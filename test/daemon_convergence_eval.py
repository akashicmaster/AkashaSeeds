#!/usr/bin/env python3
"""
Daemon convergence eval — the process-lifecycle fixes from
`docs/for-llm/daemon-convergence-spec.md` (R1–R5). Every entry path must converge to "exactly one
healthy daemon, one healthy portal" from any state, without operator intervention.

  C1 wedge probe (R3)   — a SIGSTOPped worker still passes a bare TCP connect (the old probe was
                          blind) but FAILS the new JSON-RPC probe, because the worker never runs
                          code to answer → probe_health detects the wedge. (real SIGSTOP)
  C2 heartbeat (R4)     — the boot-progress heartbeat is fresh while touched, not-fresh once
                          cleared or stale — the signal that tells a slow BOOT from a wedge.
  C3 converge (R1)      — the ONE shared routine: answers→attach, none→spawn, wedged→reap+spawn,
                          and a FRESH-heartbeat boot is waited on, never reaped (acceptance #3).
  C4 recipe env (B1)    — AKASHA_DAEMON_ARGV is in the respawn env allow-list, so the portal recipe
                          records a valid spec (not None) and the health tick can respawn it.
  C5 no self-kill (B2)  — _stop_recorded_portal refuses to signal its OWN pid, so the portal
                          watchdog's revive can't suicide mid-recovery.
  C6 entry pick (B3)    — _spawn_cell_daemon re-execs akasha.py, NOT the portal module hosting
                          the watchdog (sys.argv[0]=http_portal.py) — else `python http_portal.py
                          --daemon` dies on argparse and the revive spawns nothing.

Skips cleanly where /proc or SIGSTOP is unavailable (non-POSIX).

Run:  python test/daemon_convergence_eval.py
"""
import os
import sys
import time
import signal
import socket
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _wait_port(port, up=True, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        s = socket.socket()
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            if up:
                return True
        except OSError:
            if not up:
                return True
        finally:
            try: s.close()
            except OSError: pass
        time.sleep(0.1)
    return up is False


def c1_wedge_probe():
    """R3 — the new health probe detects a wedged (SIGSTOPped) worker; a TCP connect does not."""
    from lib.harmonia import supervisor as sv
    port = _free_port()
    # A trivial HTTP responder in its own process (so we can SIGSTOP it). It answers any request
    # (POST /api/rpc → 501), which the RPC probe treats as ALIVE (the worker RAN). SIGSTOP freezes
    # it: TCP still accepts into the backlog, but no HTTP response ever comes → the probe times out.
    code = ("import http.server,socketserver;"
            "socketserver.TCPServer.allow_reuse_address=True;"
            f"socketserver.TCPServer(('127.0.0.1',{port}),"
            "http.server.SimpleHTTPRequestHandler).serve_forever()")
    proc = subprocess.Popen([sys.executable, "-c", code],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not _wait_port(port, up=True, timeout=5.0):
            record("C1 wedge probe", False, "responder never bound")
            return
        unit = {"pid": proc.pid, "host": "127.0.0.1", "port": port,
                "health": {"kind": "http", "method": "sys.ping",
                           "target": f"http://127.0.0.1:{port}/api/rpc", "timeout": 2.0}}
        healthy_before = sv.probe_health(unit)
        tcp_before = sv._tcp_ok(f"127.0.0.1:{port}")

        os.kill(proc.pid, signal.SIGSTOP)                 # wedge it
        time.sleep(0.3)
        healthy_wedged = sv.probe_health(unit)            # RPC probe → should be False (times out)
        tcp_wedged = sv._tcp_ok(f"127.0.0.1:{port}")      # bare TCP → still True (the old blindness)
        os.kill(proc.pid, signal.SIGCONT)

        ok = healthy_before and not healthy_wedged and tcp_wedged
        record("C1 wedge probe", ok,
               f"alive_probe={healthy_before} wedged_probe={healthy_wedged} "
               f"tcp_still_passes={tcp_wedged}")
    finally:
        try: os.kill(proc.pid, signal.SIGCONT)
        except OSError: pass
        proc.terminate()
        try: proc.wait(timeout=3)
        except Exception: proc.kill()


def c2_heartbeat(base):
    """R4 — heartbeat fresh while touched; not-fresh once cleared or stale."""
    import akasha
    akasha._boot_heartbeat_clear(base)
    absent = akasha._boot_heartbeat_fresh(base)
    akasha._boot_heartbeat_touch(base)
    fresh = akasha._boot_heartbeat_fresh(base)
    # Force a stale mtime (older than the stale window).
    p = akasha._boot_heartbeat_path(base)
    old = time.time() - (akasha._BOOT_HEARTBEAT_STALE_S + 30)
    os.utime(p, (old, old))
    stale = akasha._boot_heartbeat_fresh(base)
    akasha._boot_heartbeat_clear(base)
    cleared = akasha._boot_heartbeat_fresh(base)
    ok = (not absent) and fresh and (not stale) and (not cleared)
    record("C2 heartbeat", ok,
           f"absent={absent} fresh={fresh} stale={stale} cleared={cleared}")


def c3_converge(base):
    """R1 — the shared convergence state machine (monkeypatched I/O, no real processes)."""
    import akasha
    from api.portals import cell_ipc
    calls = {"spawn": 0, "reap": 0}

    orig = {
        "ping": cell_ipc.ping,
        "alive": akasha._daemon_process_alive,
        "spawn": akasha._spawn_cell_daemon,
        "reap": akasha._reap_stale_daemon,
        "reapp": akasha._reap_leaked_portals,
        "fresh": akasha._boot_heartbeat_fresh,
    }
    try:
        def _spawn(*a, **k):
            calls["spawn"] += 1
            return True
        def _reap(*a, **k):
            calls["reap"] += 1
            return 4321
        akasha._spawn_cell_daemon = _spawn
        akasha._reap_stale_daemon = _reap
        akasha._reap_leaked_portals = lambda *a, **k: []

        # (a) a daemon ANSWERS → attach.
        cell_ipc.ping = lambda *a, **k: True
        a_state = akasha._converge_daemon(ROOT, base, None, spawn=False)

        # (b) no live daemon, spawn=True → spawned.
        cell_ipc.ping = lambda *a, **k: False
        akasha._daemon_process_alive = lambda *a, **k: None
        calls["spawn"] = 0
        b_state = akasha._converge_daemon(ROOT, base, None, spawn=True)
        b_spawned = calls["spawn"] == 1

        # (c) no live daemon, spawn=False → gone (no spawn).
        calls["spawn"] = 0
        c_state = akasha._converge_daemon(ROOT, base, None, spawn=False)
        c_no_spawn = calls["spawn"] == 0

        # (d) alive + WEDGED (stale heartbeat, never answers) → reap + spawn.
        cell_ipc.ping = lambda *a, **k: False
        akasha._daemon_process_alive = lambda *a, **k: 1234
        akasha._boot_heartbeat_fresh = lambda *a, **k: False
        calls["spawn"] = calls["reap"] = 0
        d_state = akasha._converge_daemon(ROOT, base, None, spawn=True, wait_ceiling=0)
        d_reaped = calls["reap"] >= 1 and calls["spawn"] == 1

        # (e) alive + BOOTING (heartbeat fresh) → waited on, NEVER reaped (acceptance #3).
        _seq = {"n": 0}
        def _ping_booting(*a, **k):
            _seq["n"] += 1
            return _seq["n"] >= 3           # silent twice, then the boot binds its socket
        cell_ipc.ping = _ping_booting
        akasha._daemon_process_alive = lambda *a, **k: 1234
        akasha._boot_heartbeat_fresh = lambda *a, **k: True
        calls["spawn"] = calls["reap"] = 0
        e_state = akasha._converge_daemon(ROOT, base, None, spawn=True)
        e_no_reap = e_state == "answering" and calls["reap"] == 0 and calls["spawn"] == 0

        ok = (a_state == "answering" and b_state == "spawned" and b_spawned
              and c_state == "gone" and c_no_spawn
              and d_state == "spawned" and d_reaped and e_no_reap)
        record("C3 converge", ok,
               f"answer={a_state} spawn={b_state} gone={c_state} "
               f"wedge_reap={d_reaped} booting_kept={e_no_reap}")
    finally:
        cell_ipc.ping = orig["ping"]
        akasha._daemon_process_alive = orig["alive"]
        akasha._spawn_cell_daemon = orig["spawn"]
        akasha._reap_stale_daemon = orig["reap"]
        akasha._reap_leaked_portals = orig["reapp"]
        akasha._boot_heartbeat_fresh = orig["fresh"]


def c4_recipe_env():
    """B1 — the watchdog env key must be in the respawn allow-list, or build_process_spec raises,
    the portal recipe stores spec=None, and the health tick can NEVER respawn the portal."""
    from lib.harmonia import supervisor as sv
    in_allow = "AKASHA_DAEMON_ARGV" in sv._ALLOWED_ENV_KEYS
    spec = None
    try:
        spec = sv.build_process_spec(
            argv=["python", "-m", "api.portals.web_worker"], cwd=".",
            env_add={"AKASHA_SERVE_ONLY": "1", "AKASHA_DAEMON_ARGV": '["--daemon"]'},
            base_dir="data")
    except Exception:
        spec = None
    kept = bool(spec) and "AKASHA_DAEMON_ARGV" in (spec.get("env_add") or {})
    record("C4 recipe env", in_allow and kept,
           f"in_allow_list={in_allow} spec_valid={bool(spec)} argv_env_kept={kept}")


def c5_no_self_kill():
    """B2 — _stop_recorded_portal must skip its OWN pid (the watchdog's revive path passes
    web-portal.pid, which names the watchdog itself → signalling it is self-suicide)."""
    import tempfile
    import akasha
    d = tempfile.mkdtemp(prefix="akasha_selfkill_")
    p = os.path.join(d, "web-portal.pid")
    with open(p, "w") as fh:
        fh.write(str(os.getpid()))
    r = akasha._stop_recorded_portal(p)
    # We are obviously still running; the guard must have returned None WITHOUT signalling.
    record("C5 no self-kill", r is None, f"self_skip_returned={r!r} (still alive)")


def c6_entry_pick(base):
    """B3 — the watchdog's spawn must re-exec akasha.py even when sys.argv[0] is the portal module
    it runs inside. Simulate that context and capture the argv _spawn_cell_daemon would exec."""
    import akasha
    import subprocess
    captured = {}
    orig_popen = subprocess.Popen
    orig_argv0 = sys.argv[0]
    orig_reap = akasha._reap_stale_local
    try:
        akasha._reap_stale_local = lambda *a, **k: 0          # skip pid-file cleanup noise
        def _fake_popen(cmd, *a, **k):
            captured["cmd"] = list(cmd)
            raise OSError("stub: do not actually spawn")       # → _spawn_cell_daemon returns False
        subprocess.Popen = _fake_popen
        sys.argv[0] = "/opt/app/services/http_portal.py"       # the portal-watchdog context (B3)
        akasha._spawn_cell_daemon(ROOT, base, None, quiet=True)
    finally:
        subprocess.Popen = orig_popen
        sys.argv[0] = orig_argv0
        akasha._reap_stale_local = orig_reap
    cmd = captured.get("cmd") or []
    entry = cmd[1] if len(cmd) > 1 else ""
    ok = entry.endswith("akasha.py") and "http_portal" not in entry
    record("C6 entry pick", ok, f"entry={os.path.basename(entry) or entry!r}")


class _FakeProc:
    """A spawned-daemon stand-in: stays 'alive' (poll None) so the wait loop exercises the
    heartbeat/ceiling logic rather than the proc-exit grace."""
    def poll(self):
        return None
    def terminate(self):
        pass


def c7_spawn_wait(base):
    """B4 — the spawn wait must be heartbeat-gated (F1) and must reap a wedged spawn before
    returning False (F2). Exercises the REAL _spawn_cell_daemon loop with monkeypatched I/O
    (no slow real daemon boot)."""
    import akasha
    import subprocess
    from api.portals import cell_ipc

    orig = {
        "popen": subprocess.Popen, "ping": cell_ipc.ping,
        "fresh": akasha._boot_heartbeat_fresh, "reaplocal": akasha._reap_stale_local,
        "alive": akasha._daemon_process_alive, "reap": akasha._reap_stale_daemon,
        "reapp": akasha._reap_leaked_portals, "bootwait": os.environ.get("AKASHA_BOOT_WAIT"),
    }
    try:
        subprocess.Popen = lambda *a, **k: _FakeProc()
        akasha._reap_stale_local = lambda *a, **k: 0

        # F1 — heartbeat FRESH → the (short) fallback ceiling must NOT fire; wait until the socket
        # answers even though that is well past the ceiling.
        os.environ["AKASHA_BOOT_WAIT"] = "1"                 # 1 s fallback ceiling
        akasha._boot_heartbeat_fresh = lambda *a, **k: True
        _t0 = time.time()
        cell_ipc.ping = lambda *a, **k: (time.time() - _t0) >= 3.0   # binds the socket at ~3 s
        res_f1 = akasha._spawn_cell_daemon(ROOT, base, None, quiet=True)
        elapsed = time.time() - _t0
        f1_ok = res_f1 is True and elapsed > 1.5              # survived past the 1 s ceiling
        record("C7a F1 gate", f1_ok, f"attached={res_f1} waited={elapsed:.1f}s (>ceiling 1s)")

        # F2 — heartbeat STALE + never answers → give up, but REAP the still-alive wedged spawn
        # before returning False (a False return must mean no live daemon process).
        reaped = {"n": 0}
        os.environ["AKASHA_BOOT_WAIT"] = "1"
        akasha._boot_heartbeat_fresh = lambda *a, **k: False
        cell_ipc.ping = lambda *a, **k: False
        akasha._daemon_process_alive = lambda *a, **k: 99999    # a wedged daemon is "alive"
        akasha._reap_stale_daemon = lambda *a, **k: reaped.__setitem__("n", reaped["n"] + 1) or 99999
        akasha._reap_leaked_portals = lambda *a, **k: []
        res_f2 = akasha._spawn_cell_daemon(ROOT, base, None, quiet=True)
        f2_ok = res_f2 is False and reaped["n"] >= 1
        record("C7b F2 reap", f2_ok, f"gave_up={res_f2 is False} reaped_before_false={reaped['n']>=1}")
    finally:
        subprocess.Popen = orig["popen"]
        cell_ipc.ping = orig["ping"]
        akasha._boot_heartbeat_fresh = orig["fresh"]
        akasha._reap_stale_local = orig["reaplocal"]
        akasha._daemon_process_alive = orig["alive"]
        akasha._reap_stale_daemon = orig["reap"]
        akasha._reap_leaked_portals = orig["reapp"]
        if orig["bootwait"] is None:
            os.environ.pop("AKASHA_BOOT_WAIT", None)
        else:
            os.environ["AKASHA_BOOT_WAIT"] = orig["bootwait"]


def c8_sentinel_alias():
    """F6 — aliasing an explicit 64-hex atom key must be allowed (the global-relations completion
    sentinel is a write→alias of the just-written key; rejecting it made the sentinel never land →
    relations REPLAYED every boot → RSS climbed into the OOM ceiling). A NON-hex dangling target is
    still rejected (B2 preserved)."""
    import hashlib
    import tempfile as _tf
    from lib.akasha.kernel import KernelDispatcher
    from api.router import CommandRouter
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=_tf.mkdtemp(prefix="akasha_f6_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def run(cli):
        p = CommandRouter.build_rpc_request(cli, "admin")
        return k.dispatch(p, "local") if p else {"error": {"code": -1}}

    fakekey = hashlib.sha256(b"sentinel-nonexistent").hexdigest()      # a 64-hex key with no body
    r_hex = run(f"al {fakekey} ont:ak:relations:all:testsentinel")
    hex_ok = r_hex.get("error", {}).get("code") != -32602              # F6: created, not rejected
    r_raw = run("al place:nowhere nowherenick")
    raw_rejected = r_raw.get("error", {}).get("code") == -32602        # B2: still rejected
    record("C8 F6 sentinel", hex_ok and raw_rejected,
           f"hexkey_aliased={hex_ok} nonhex_rejected={raw_rejected}")


def c9_recorded_portal(base):
    """F7 — the watchdog guard must accept the Supervisor run-dir pid (a health-tick respawn
    updates the run-dir unit pid but NOT web-portal.pid), else the watchdog is muted after the
    first respawn."""
    from api.portals import daemon_watchdog as dw
    from lib.harmonia import supervisor as sv
    os.makedirs(sv.run_dir(base), exist_ok=True)
    with open(os.path.join(base, "web-portal.pid"), "w") as fh:
        fh.write("999999")                                            # legacy file names ANOTHER pid
    sv.write_unit(base, {"id": "svc:web-portal", "kind": sv.KIND_SERVICE, "pid": os.getpid()})
    ok = dw._is_recorded_portal(base)                                 # run-dir pid is authoritative
    record("C9 F7 recorded", ok, f"run-dir pid honoured={ok} (legacy file stale)")


def c10_health_update(base):
    """F8 — a portal that flips to HTTPS after registration must be able to correct its own probe
    (health-only update, no re-sign) so the daemon stops respawning a healthy TLS portal."""
    from lib.harmonia import supervisor as sv
    os.makedirs(sv.run_dir(base), exist_ok=True)
    sv.write_unit(base, {"id": "svc:web-portal", "kind": sv.KIND_SERVICE, "pid": os.getpid(),
                         "health": {"kind": "http", "target": "http://127.0.0.1:80/api/rpc",
                                    "method": "sys.ping"},
                         "spec": {"substrate": "process", "sig": "abc"}})
    sv.update_unit_health(base, "svc:web-portal",
                          {"kind": "http", "target": "https://127.0.0.1:443/api/rpc",
                           "method": "sys.ping", "timeout": 3.0})
    u = sv.read_unit(base, "svc:web-portal")
    ok = (u["health"]["target"] == "https://127.0.0.1:443/api/rpc"
          and u["spec"]["sig"] == "abc" and u["pid"] == os.getpid())
    record("C10 F8 health", ok, f"target={u['health']['target']} sig_intact={u['spec']['sig']=='abc'}")


def c11_readiness_gate(base):
    """F9 — the health tick must NOT respawn a portal that is still BOOTING (alive, not yet ready,
    within boot_grace_s) even though its probe fails; once it signals readiness OR the grace
    expires, the normal probe/debounce resumes. Uses a live child pid + a non-respawnable spec so
    the assertion never triggers a real stop/respawn."""
    import subprocess
    from lib.harmonia import supervisor as sv
    os.makedirs(sv.run_dir(base), exist_ok=True)
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        sup = sv.Supervisor(base)
        H = {"kind": "http", "target": "http://127.0.0.1:59999/api/rpc",
             "method": "sys.ping", "timeout": 1.0}                    # always fails (dead port)
        # (a) BOOTING — alive, no ready_at, within grace, failing probe → skipped (no debounce count)
        sup.record_running("svc:web-portal", child.pid, restart="on-failure", serve_only=True,
                           spec={"substrate": "thread"}, boot_grace_s=300, health=H)
        sup.maintain()
        booting_skipped = sup._health_fails.get("svc:web-portal", 0) == 0
        # (b) grace EXPIRED — start far in the past → gate no longer skips → probe path runs
        u = sv.read_unit(base, "svc:web-portal"); u["started_at"] = time.time() - 10000
        sv.write_unit(base, u)
        sup.maintain()
        expired_probed = sup._health_fails.get("svc:web-portal", 0) >= 1
        # (c) READY — fresh start but ready_at set → probe path runs immediately
        sup._health_fails.clear()
        u = sv.read_unit(base, "svc:web-portal"); u["started_at"] = time.time()
        u.pop("ready_at", None); sv.write_unit(base, u)
        sv.mark_unit_ready(base, "svc:web-portal")
        sup.maintain()
        ready_probed = sup._health_fails.get("svc:web-portal", 0) >= 1
        ok = booting_skipped and expired_probed and ready_probed
        record("C11 F9 readiness", ok,
               f"booting_skipped={booting_skipped} expired_probed={expired_probed} "
               f"ready_probed={ready_probed}")
    finally:
        child.terminate()
        try: child.wait(timeout=3)
        except Exception: child.kill()


def main():
    print("\n  daemon convergence eval — R1 shared convergence · R3 wedge probe · R4 heartbeat\n")
    if not sys.platform.startswith("linux") or not os.path.isdir("/proc"):
        print("  SKIP  requires Linux + /proc + SIGSTOP (non-POSIX host).")
        print("\nRESULT: SKIP")
        return 0

    import tempfile
    base = tempfile.mkdtemp(prefix="akasha_converge_")
    os.makedirs(os.path.join(base, "central"), exist_ok=True)

    c1_wedge_probe()
    c2_heartbeat(base)
    c3_converge(base)
    c4_recipe_env()
    c5_no_self_kill()
    c6_entry_pick(base)
    c7_spawn_wait(base)
    c8_sentinel_alias()
    c9_recorded_portal(base)
    c10_health_update(base)
    c11_readiness_gate(base)

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — a daemon-convergence invariant regressed.")
        return 1
    print("\nRESULT: PASS — the shared convergence routine, the wedge-detecting health probe, and "
          "the boot heartbeat behave per the daemon-convergence spec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
