#!/usr/bin/env python3
"""
The console's `svc` gate asks about the console's IDENTITY, not its token (seeds 13 findings F2).

`svc start|stop|restart` on the local console answered `Permission denied: … requires admin` for the
Genesis admin while `user.ls` (also admin) worked. The console asked the gate about its SESSION TOKEN
— a credential (`akt:…`, or empty on an attached console) for which the gate holds no line — where
`user.ls` is decided by the kernel for the identity the token resolves to. The console now asks
about the identity the kernel returned at login.

On a fixture cell (no application): the console logs in exactly as it does at the prompt
(`kernel.auth.local` through the console's own local gateway), then runs the REAL console handler:

  1. the Genesis admin runs `svc start`, `svc restart` and `svc stop` on a unit, and each is
     permitted and done (the unit's process is alive after start/restart, gone after stop);
  2. a resident (no admin line) is refused by the same handler, each verb;
  3. the console's session token is not an identity the gate knows — the reason the old
     pre-check refused the admin.

Run:  python test/console_svc_admin_eval.py     (exit 0 = all pass)
"""
import contextlib
import hashlib
import io
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
CELL = tempfile.mkdtemp(prefix="console_svc_")
os.environ["AKASHA_DATA_DIR"] = CELL           # the console's run-dir is the cell's
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    print("=" * 78)
    print("The console's svc gate — identity, not token")
    print("=" * 78)
    from lib.akasha.api.client import embedded
    from lib.akasha.api import gate
    from lib.harmonia import supervisor as sv
    from api.portals import stdio

    gw = embedded(CELL, "seeds", load_ontology=False)
    local = stdio._LocalGateway(gw)
    r = local.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                        "params": {"session_token": "admin",
                                   "data": {"user_name": "admin",
                                            "passphrase": hashlib.sha256(b"pw-123456").hexdigest()}},
                        "id": "g"})
    check("Genesis binds", (r.get("result") or {}).get("status") == "bound", str(r)[:120])
    auth = stdio._auth_local(local)
    check("the console logs in as it does at the prompt (kernel.auth.local)", bool(auth), str(auth))
    user_id, token, _role = auth

    # A harmless unit with a respawn recipe in the cell's run-dir (the shape allow-list is the
    # supervisor eval's subject; here a bare sleeper stands in for a portal).
    sv._validate_argv = lambda argv: None
    sleeper = [sys.executable, "-c", "import time; time.sleep(60)"]
    spec = sv.build_process_spec(sleeper, cwd=ROOT, env_add={}, base_dir=CELL)
    import subprocess
    p0 = subprocess.Popen(sleeper)
    sv.Supervisor(CELL).record_running("svc:fx", p0.pid, engine="test", spec=spec, trust="local")
    p0.terminate(); p0.wait(timeout=5)

    def run(args, identity):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            stdio._handle_svc(args, "admin", None, gw=local, session_token=token, identity=identity)
        return out.getvalue()

    def gone(p):
        """Stopped: no process, or a zombie of this process (the cell spawned it in-process here)."""
        try:
            with open("/proc/%d/stat" % p) as fh:
                return fh.read().rsplit(")", 1)[1].split()[0] == "Z"
        except OSError:
            return True

    def pid():
        u = sv.read_unit(CELL, "svc:fx") or {}
        return u.get("pid")

    print("\n  ── 1. the Genesis admin ──")
    o = run("start fx", user_id)
    time.sleep(0.3)
    check("`svc start` is permitted and starts the unit", "denied" not in o and "✓" in o
          and pid() and sv._pid_alive(pid()), o.strip())
    first = pid()
    o = run("restart fx", user_id)
    time.sleep(0.3)
    check("`svc restart` is permitted and restarts it (a new process)", "denied" not in o and "✓" in o
          and pid() and sv._pid_alive(pid()) and pid() != first, o.strip())
    last = pid()
    o = run("stop fx", user_id)
    time.sleep(0.5)
    check("`svc stop` is permitted and stops it", "denied" not in o and "✓" in o
          and gone(last), o.strip())

    print("\n  ── 2. a resident ──")
    local.dispatch({"jsonrpc": "2.0", "method": "user.add",
                    "params": {"session_token": token,
                               "data": {"client_id": "rita", "role": "user",
                                        "passphrase_hash": hashlib.sha256(b"rita-pass").hexdigest()}},
                    "id": "u"})
    for verb in ("start", "restart", "stop"):
        o = run("%s fx" % verb, "rita")
        check("`svc %s` is refused for a resident" % verb, "Permission denied" in o, o.strip())

    print("\n  ── 3. why the admin was refused ──")
    check("the gate admits the admin's identity", gate.gate(user_id, gate.ADMIN)[0])
    check("…and holds no line for the session token or for an empty one (the old question)",
          not gate.gate(token, gate.ADMIN)[0] and not gate.gate("", gate.ADMIN)[0],
          "token=%s…" % str(token)[:12])

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the console decides svc for the identity the kernel resolved at login: the "
          "Genesis admin starts, restarts and stops a unit; a resident is refused by the same gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
