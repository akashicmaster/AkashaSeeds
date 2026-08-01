#!/usr/bin/env python3
"""
Supervisor P1 eval — persistent respawn recipe + the hardened control-path gate.

Validates the premises-doc P1 implementation end to end, using a harmless allow-listed
recipe (`python -m services.<x> --sleep`) so nothing touches the nucleus:

  1  build_process_spec persists a serializable, re-executable recipe (argv/env/cwd).
  2  respawn() re-launches a dead unit from the run-dir alone — no in-memory closure.
  3  reconcile() applies the on-failure restart policy (dead pid → respawned).
  4  GATE argv    — a recipe whose argv[0] is not the interpreter / module not allow-listed is refused.
  5  GATE env     — a credential-shaped env key is refused at BUILD time (never persisted).
  6  GATE perms   — a group/other-writable descriptor is refused (tamper guard).
  7  GATE sign    — with a supervisor key set, an unsigned/forged recipe is refused; a
                    correctly-signed one passes; strict mode refuses unsigned even with no key.
  8  single-writer admission — a serve_only=False unit is refused while svc:cell is live (P5).

Run:  python test/supervisor_respawn_eval.py
"""
import os
import sys
import time
import stat
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.harmonia import supervisor as sv  # noqa: E402

_PASS = []
_FAIL = []


def check(name, cond, detail=""):
    (_PASS if cond else _FAIL).append(name)
    print(f"  {'OK  ' if cond else '!! FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def _harmless_argv(seconds=30):
    # An allow-listed module launch that just sleeps — never opens the nucleus.
    # We use `-c` is NOT allowed (must be -m <allow-listed>), so we point at a bundled
    # services module that accepts being imported; the process exits fast on ImportError,
    # which is fine — we only assert the PID was spawned + gated, not that it serves.
    return [sys.executable, "-m", "services.static_noop_probe", "--sleep", str(seconds)]


def main():
    print("\n  Supervisor P1 eval — respawn recipe + hardened gate\n")
    base = tempfile.mkdtemp(prefix="sup_p1_")
    os.makedirs(os.path.join(base, "central"), exist_ok=True)
    sv._ensure_run_dir(base)

    # Use a genuinely spawnable, harmless recipe: python -c is disallowed, so run a tiny
    # sleeper via an allow-listed *services.* module path that we know exists as a probe.
    # To keep the eval self-contained and not depend on a real services module, we spawn a
    # trivial sleeper through the interpreter with an allow-listed module name by monkey-adding
    # it to the allow-list for the duration (the GATE tests below use the REAL allow-list).
    real_sleeper = [sys.executable, "-c", "import time,sys; time.sleep(30)"]

    # ── 1. build_process_spec persists a serializable recipe ──────────────────
    # Temporarily allow a bare interpreter recipe for the spawn/respawn/reconcile mechanics,
    # so those tests exercise a process we can actually launch and kill.
    orig_validate = sv._validate_argv
    sv._validate_argv = lambda argv: None          # mechanics tests: bypass shape allow-list
    try:
        spec = sv.build_process_spec(real_sleeper, cwd=ROOT,
                                     env_add={"PYTHONUNBUFFERED": "1"}, base_dir=base)
        check("1 recipe is serializable (argv/cwd/env_add present)",
              spec.get("argv") == real_sleeper and spec.get("cwd") == ROOT
              and spec.get("env_add") == {"PYTHONUNBUFFERED": "1"})

        sup = sv.Supervisor(base)
        # Record a unit as if launched, carrying the recipe, then kill it and respawn from disk.
        import subprocess
        p0 = subprocess.Popen(real_sleeper, cwd=ROOT)
        sup.record_running("svc:sleeper", p0.pid, engine="test", spec=spec,
                           restart=sv.RESTART_ON_FAILURE, serve_only=True, trust="local")
        p0.terminate(); p0.wait(timeout=5)
        check("pre-respawn: recorded unit's pid is dead", not sv._pid_alive(p0.pid))

        # ── 2. respawn from the run-dir alone (fresh Supervisor, no in-memory closure) ──
        fresh = sv.Supervisor(base)                # a DIFFERENT instance — no blueprint in memory
        unit = sv.read_unit(base, "svc:sleeper")
        proc = sv.respawn(base, unit)
        time.sleep(0.3)
        check("2 respawn() re-launched from the persisted recipe (no closure)",
              proc and sv._pid_alive(proc.pid) and proc.pid != p0.pid)
        proc.terminate(); proc.wait(timeout=5)

        # ── 3. reconcile applies on-failure policy (dead → respawned) ──────────
        # svc:sleeper descriptor still points at the now-dead respawn pid.
        sv.write_unit(base, {**sv.read_unit(base, "svc:sleeper"), "pid": proc.pid})
        fresh.reconcile()
        u_after = sv.read_unit(base, "svc:sleeper")
        alive = u_after and sv._pid_alive(u_after.get("pid"))
        check("3 reconcile() respawned the dead on-failure unit", bool(alive),
              f"unit={u_after}")
        if alive:
            try:
                os.kill(u_after["pid"], 15)
            except OSError:
                pass
        sv.remove_unit(base, "svc:sleeper")
    finally:
        sv._validate_argv = orig_validate          # restore the REAL gate for the tests below

    # ── 4. GATE argv — non-interpreter / non-allow-listed module refused ──────
    try:
        sv.build_process_spec(["/bin/sh", "-c", "rm -rf /"], cwd=ROOT, base_dir=base)
        check("4 argv gate refuses a shell recipe", False, "no ValueError raised")
    except ValueError:
        check("4 argv gate refuses a shell recipe", True)
    try:
        sv.build_process_spec([sys.executable, "-m", "os", "-c", "x"], cwd=ROOT, base_dir=base)
        check("4b argv gate refuses a non-allow-listed module", False)
    except ValueError:
        check("4b argv gate refuses a non-allow-listed module", True)
    # …and the allow-listed module passes.
    ok_argv = [sys.executable, "-m", "api.portals.web_worker", "--port", "9"]
    try:
        s_ok = sv.build_process_spec(ok_argv, cwd=ROOT, base_dir=base)
        check("4c argv gate ADMITS the allow-listed web_worker module", bool(s_ok.get("argv")))
    except ValueError as e:
        check("4c argv gate ADMITS the allow-listed web_worker module", False, str(e))

    # ── 5. GATE env — credential-shaped key refused at build time ─────────────
    try:
        sv.build_process_spec(ok_argv, cwd=ROOT,
                              env_add={"AKASHA_SECRET": "hunter2"}, base_dir=base)
        check("5 env gate refuses a secret-shaped key", False)
    except ValueError:
        check("5 env gate refuses a secret-shaped key", True)
    try:
        sv.build_process_spec(ok_argv, cwd=ROOT,
                              env_add={"RANDOM_UNLISTED": "x"}, base_dir=base)
        check("5b env gate refuses a non-allow-listed key", False)
    except ValueError:
        check("5b env gate refuses a non-allow-listed key", True)

    # ── 6. GATE perms — group/other-writable descriptor refused ───────────────
    sv.write_unit(base, {"id": "svc:permtest", "kind": sv.KIND_SERVICE, "pid": 1,
                         "spec": {**s_ok}})
    desc_path = sv._unit_path(base, "svc:permtest")
    os.chmod(desc_path, 0o666)                      # world-writable → tamperable
    ok, why = sv.authorize_recipe(base, "svc:permtest", s_ok)
    check("6 perms gate refuses a world-writable descriptor", not ok, why)
    os.chmod(desc_path, 0o600)
    ok2, _ = sv.authorize_recipe(base, "svc:permtest", s_ok)
    check("6b perms gate ADMITS an owner-only descriptor (no key set)", ok2)
    sv.remove_unit(base, "svc:permtest")

    # ── 7. GATE signature — key present ⇒ recipe must be validly signed ────────
    os.environ["AKASHA_SECRET"] = "test-supervisor-key-777"
    try:
        signed = sv.build_process_spec(ok_argv, cwd=ROOT, base_dir=base)
        check("7 signed recipe carries a sig", bool(signed.get("sig")))
        sv.write_unit(base, {"id": "svc:sig", "kind": sv.KIND_SERVICE, "pid": 1, "spec": signed})
        ok_s, _ = sv.authorize_recipe(base, "svc:sig", signed)
        check("7b correctly-signed recipe is admitted", ok_s)
        forged = {**signed, "argv": [sys.executable, "-m", "api.portals.web_worker", "--port", "666"]}
        ok_f, why_f = sv.authorize_recipe(base, "svc:sig", forged)
        check("7c tampered recipe (sig no longer matches) is refused", not ok_f, why_f)
        unsigned = {k: v for k, v in signed.items() if k != "sig"}
        ok_u, _ = sv.authorize_recipe(base, "svc:sig", unsigned)
        check("7d unsigned recipe refused while a key is present", not ok_u)
        sv.remove_unit(base, "svc:sig")
    finally:
        del os.environ["AKASHA_SECRET"]

    # strict mode: refuse unsigned even with NO key available (enterprise lever)
    os.environ["AKASHA_SUPERVISOR_STRICT"] = "1"
    try:
        sv.write_unit(base, {"id": "svc:strict", "kind": sv.KIND_SERVICE, "pid": 1, "spec": s_ok})
        ok_st, why_st = sv.authorize_recipe(base, "svc:strict", s_ok)
        check("7e strict mode refuses unsigned recipe with no key", not ok_st, why_st)
        sv.remove_unit(base, "svc:strict")
    finally:
        del os.environ["AKASHA_SUPERVISOR_STRICT"]

    # ── 8. single-writer admission (P5) ───────────────────────────────────────
    sup2 = sv.Supervisor(base)
    sv.write_unit(base, {"id": "svc:cell", "kind": sv.KIND_SERVICE, "pid": os.getpid(),
                         "serve_only": False})     # the live writer (this process)
    admit_ok, admit_why = sup2._admit({"id": "svc:secondwriter", "serve_only": False})
    check("8 admission refuses a 2nd writer while svc:cell is live", not admit_ok, admit_why)
    admit_ro, _ = sup2._admit({"id": "svc:reader", "serve_only": True})
    check("8b admission ADMITS a serve_only front", admit_ro)
    sv.remove_unit(base, "svc:cell")

    # ── 9. this-process handles: get_proc / release / stop_local (ServiceManager's job) ──
    import subprocess as _sp
    sup3 = sv.Supervisor(base)
    p1 = _sp.Popen(real_sleeper, cwd=ROOT)
    sup3.record_running("svc:held", p1.pid, engine="test", proc=p1)
    check("9 get_proc returns the tracked handle", sup3.get_proc("svc:held") is p1)
    # release() untracks (survives stop_local) but LEAVES the run-dir descriptor
    sup3.release("svc:held")
    check("9b release untracks the proc", sup3.get_proc("svc:held") is None)
    check("9c release leaves the run-dir descriptor", sv.read_unit(base, "svc:held") is not None)
    sup3.stop_local()                          # must NOT stop the released proc
    time.sleep(0.2)
    check("9d stop_local spares a released unit", sv._pid_alive(p1.pid))
    # a still-tracked unit IS stopped by stop_local
    p2 = _sp.Popen(real_sleeper, cwd=ROOT)
    sup3.record_running("svc:tracked", p2.pid, engine="test", proc=p2)
    sup3.stop_local()
    time.sleep(0.2)
    check("9e stop_local stops a tracked unit", not sv._pid_alive(p2.pid))
    check("9f stop_local removes the tracked descriptor", sv.read_unit(base, "svc:tracked") is None)
    for _p in (p1, p2):
        try:
            _p.terminate(); _p.wait(timeout=3)
        except Exception:
            pass
    sv.remove_unit(base, "svc:held")

    print()
    total = len(_PASS) + len(_FAIL)
    if _FAIL:
        print(f"RESULT: FAIL — {len(_FAIL)}/{total} checks failed: {_FAIL}")
        return 1
    print(f"RESULT: PASS — all {total} checks green. P1 respawn recipe + the layered gate "
          f"(perms → argv → env → signature) + single-writer admission hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
