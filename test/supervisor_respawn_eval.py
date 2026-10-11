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
                    correctly-signed one passes; with no key the OS boundary is the gate.
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

    # Busy-vs-hung guard (health tick): a unit that MISSES its probe but is ADVANCING (CPU / major-
    # faults — a portal working through an access burst) must NOT be respawned; a frozen/hung one
    # (no CPU) still is. This is what stops the "portal flew back to 'warming up' under load" churn.
    if sys.platform.startswith("linux") and os.path.isdir("/proc"):
        import subprocess as _sp, signal as _sig
        _busy = _sp.Popen([sys.executable, "-c", "x=0\nwhile True:\n x+=1"])
        _frozen = _sp.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            time.sleep(0.3); os.kill(_frozen.pid, _sig.SIGSTOP)
            _ba = sv._proc_advancing(_busy.pid, window=0.6)
            _fa = sv._proc_advancing(_frozen.pid, window=0.6)
            check("0 busy unit spared, frozen unit reapable", _ba is True and _fa is False,
                  f"busy_adv={_ba} frozen_adv={_fa}")
        finally:
            try: os.kill(_frozen.pid, _sig.SIGCONT)
            except OSError: pass
            for _p in (_busy, _frozen):
                _p.kill(); _p.wait()

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

    # no key: the OS boundary is the gate, so an unsigned recipe passes (the strict-signing
    # switch is deleted — the purge order §4.5; a key's presence is the one deciding fact)
    sv.write_unit(base, {"id": "svc:nokey", "kind": sv.KIND_SERVICE, "pid": 1, "spec": s_ok})
    ok_nk, why_nk = sv.authorize_recipe(base, "svc:nokey", s_ok)
    check("7e with no key an unsigned recipe passes (one deciding fact: key present)",
          ok_nk, why_nk)
    sv.remove_unit(base, "svc:nokey")

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

    # ── 10. THREAD-substrate stop safety: a host-bound unit's pid is the HOST interpreter's, so
    #    stop() must NEVER signal it (else stopping an in-process poller would take down the whole
    #    Cell daemon and every unit it carries — the collateral this guards against). ──
    sup4 = sv.Supervisor(base)
    host = _sp.Popen(real_sleeper, cwd=ROOT)      # stand-in for the host daemon interpreter
    sup4.record_running("svc:inproc", host.pid, engine="thread-unit",
                        substrate=sv.SUBSTRATE_THREAD,
                        health={"kind": "heartbeat", "stale_s": 90})
    r10 = sup4.stop("svc:inproc")
    time.sleep(0.2)
    check("10 stop() of a live THREAD unit does NOT kill the host pid (no daemon collateral)",
          sv._pid_alive(host.pid) and r10.get("status") == "host-managed", str(r10))
    check("10b stop() leaves the THREAD descriptor while the host lives (no orphaned live thread)",
          sv.read_unit(base, "svc:inproc") is not None)
    # once the host is gone, the thread died with it → stop() scrubs the now-safe stale descriptor
    host.terminate(); host.wait(timeout=3)
    r10c = sup4.stop("svc:inproc")
    check("10c stop() of a THREAD unit whose host already exited scrubs the stale descriptor",
          r10c.get("status") == "stopped" and sv.read_unit(base, "svc:inproc") is None, str(r10c))

    # ── R7. the uvicorn portal shuts down GRACEFULLY inside the reaper grace. Its default graceful
    #    shutdown waits on idle keep-alive connections with no bound, so on `stop` the supervisor's
    #    SIGTERM grace expired and the portal was SIGKILL'd (a WARNING reserved for a WEDGED portal).
    #    The portal launch now bounds uvicorn's timeout_graceful_shutdown BELOW the 5.0s reaper grace,
    #    so a `stop` with an idle keep-alive drains and exits status=-15. Assert the Config carries it
    #    (a fake uvicorn module captures the kwargs — no real socket, no uvicorn dependency). ──
    _REAP_GRACE_S = 5.0                                   # svc:web-portal SIGTERM grace (akasha.py reaper)

    class _FakeCfg:
        def __init__(self, app, **kw):
            self.kw = kw; self.install_signal_handlers = True
            for k, v in kw.items():
                setattr(self, k, v)

    class _FakeServer:
        def __init__(self, cfg):
            self.cfg = cfg

    class _FakeUvicorn:
        Config = _FakeCfg
        Server = _FakeServer

    from api.portals.asgi import _run_uvicorn
    os.environ.pop("AKASHA_PORTAL_GRACEFUL_S", None)      # default path
    _cfg, _srv = _run_uvicorn(_FakeUvicorn, object(), "127.0.0.1", 8080, None, None, True)
    _g = _cfg.kw.get("timeout_graceful_shutdown")
    check("R7 the portal Config bounds uvicorn's graceful shutdown", _g is not None, str(_cfg.kw))
    check("R7 the graceful shutdown is BELOW the reaper grace (no SIGKILL on a normal stop)",
          _g is not None and _g < _REAP_GRACE_S, f"graceful={_g} grace={_REAP_GRACE_S}")
    check("R7 signal handlers stay off the background portal thread",
          _cfg.install_signal_handlers is False)
    os.environ["AKASHA_PORTAL_GRACEFUL_S"] = "2"          # operator override, still under the grace
    _cfg2, _ = _run_uvicorn(_FakeUvicorn, object(), "127.0.0.1", 8080, None, None, True)
    check("R7 AKASHA_PORTAL_GRACEFUL_S overrides the graceful timeout",
          _cfg2.kw.get("timeout_graceful_shutdown") == 2, str(_cfg2.kw))
    os.environ.pop("AKASHA_PORTAL_GRACEFUL_S", None)

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
