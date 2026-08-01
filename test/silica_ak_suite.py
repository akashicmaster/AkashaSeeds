#!/usr/bin/env python3
"""
Silica .ak regression suite — the project's canonical JCL tests on the NATIVE engine.

Runs test_00..07 (the .ak baseline: memory, links, sets, aliases, dive, notes, tree
traversal, rec/lens) through the real job.submit path with AKASHA_BACKEND=silica, so
the self-owned store is validated by the same suite CLAUDE.md uses as its regression
guard for SQLite.  All jobs are submitted, then polled until each reaches a terminal
state (the single JCL worker drains them FIFO, interleaved with background weave/
semantic jobs, so a fixed per-job window would mis-flag a job whose START is merely
delayed behind the background backlog — poll ALL to a generous TOTAL deadline instead).

Run:  python test/silica_ak_suite.py     (slow — boots core ontology + 8 JCL jobs)
"""
import os
import sys
import glob
import time
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"        # ← native engine at the factory

_TOTAL_TIMEOUT = 900.0                          # whole-suite drain budget
_TERMINAL = ("DONE", "FAILED", "ERROR", "CANCELLED")


def main():
    print("\n  silica .ak suite — canonical JCL regression on the native engine\n")
    from lib.akasha.kernel import KernelDispatcher
    from api.portals.stdio import _parse_ak_file
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="silica_ak_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def disp(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error") or {}

    # Submit every job, then poll all to a total deadline (drain, not per-job window).
    jobs = []   # (name, job_id, skipped)
    for f in sorted(glob.glob(os.path.join(ROOT, "test", "test_0[0-7]*.ak"))):
        name = os.path.basename(f)
        steps, skipped = _parse_ak_file(f)
        jid = disp("job.submit", {"steps": steps, "label": name, "fail_fast": True}).get("job_id")
        jobs.append((name, jid, skipped))

    deadline = time.time() + _TOTAL_TIMEOUT
    final = {}
    while time.time() < deadline:
        final = {jid: disp("job.stat", {"job_id": jid}) for _n, jid, _s in jobs if jid}
        if all(st.get("status") in _TERMINAL for st in final.values()):
            break
        time.sleep(1.0)

    ok_all = True
    for name, jid, skipped in jobs:
        st = final.get(jid, {}) if jid else {}
        done = st.get("status") == "DONE"
        ok_all = ok_all and done
        print(f"  {'OK  ' if done else '!! FAIL'}  {name:26} {str(st.get('status')):9} "
              f"steps={st.get('step_done')}/{st.get('step_count')} skipped={skipped}")
        if not done:
            print(f"       detail: {str(st.get('error') or st.get('last_error') or st)[:200]}")

    print()
    if not ok_all:
        print("RESULT: FAIL — a .ak regression test did not pass on the native engine.")
        return 1
    print("RESULT: PASS — test_00..07 all DONE on AKASHA_BACKEND=silica; the native engine "
          "passes the project's canonical JCL regression suite.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
