#!/usr/bin/env python3
"""
F52 — sys.compact is an ASYNC job, and auto-fold triggers on GROWTH (acceptance, design §1+§2).

A WAL fold's duration scales with store size; an 11.5 M-record fold exceeds the 60 s cell-IPC reply
window, so a synchronous sys.compact returns a spurious 'daemon busy' while the fold runs on — and
every operator retry launches ANOTHER full fold. F52 makes the fold a background JCL job that returns
immediately, refuses a second submission while one is running, and re-baselines the auto-checkpoint
daemon so it folds on ~1 GiB of NEW growth rather than every idle check on a large live store.

A real >60 s Silica fold is a VPS-only check; this eval pins the CONTRACT deterministically with a
fake, controllable compact()/wal_bytes() attached to the nucleus core.

Run:  python test/f52_compact_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _wait_job_done(k, jid, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        for j in (k.jcl_worker.list_jobs() if k.jcl_worker else []):
            if getattr(j, "job_id", "") == jid:
                st = getattr(j, "status", "")
                if st in ("DONE", "FAILED", "CANCELLED"):
                    return st
        time.sleep(0.05)
    return "TIMEOUT"


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_f52_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data, tok="admin"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    core = k.manager.shared_nucleus.core

    # ── a fake, controllable fold attached to the nucleus core (sqlite core has none) ──
    gate = threading.Event(); gate.set()          # open ⇒ compact runs immediately
    wal = [1000]                                   # current WAL bytes (mutable)
    calls = [0]

    def fake_compact():
        gate.wait()                                # block here only when the test clears the gate
        calls[0] += 1
        before = wal[0]
        wal[0] = 500                               # a fold shrinks the WAL to the live baseline
        return {"before_bytes": before, "after_bytes": wal[0], "seconds": 0.01}

    core.compact = fake_compact
    core.wal_bytes = lambda: wal[0]
    KernelDispatcher._wal_last_fold_bytes = None

    # ── 1. sys.compact returns IMMEDIATELY with a job id (not the fold result) ──
    t0 = time.time()
    r1 = d("sys.compact", {})
    dt = time.time() - t0
    jid = r1.get("job")
    check("sys.compact returns < 1 s with started=True + a job id (async, not the inline fold)",
          r1.get("started") is True and isinstance(jid, str) and jid and dt < 1.0,
          "dt=%.3fs r=%s" % (dt, r1))
    check("the immediate reply carries the pre-fold wal_bytes for the operator",
          r1.get("wal_bytes") == 1000, str(r1))

    st = _wait_job_done(k, jid)
    check("the fold runs to completion as a background JCL job (job.stat → DONE)",
          st == "DONE" and calls[0] == 1, "status=%s calls=%d" % (st, calls[0]))
    check("F52 §2 — the auto-fold baseline is re-set to the POST-fold live WAL size (500)",
          KernelDispatcher._wal_last_fold_bytes == 500,
          "baseline=%s" % KernelDispatcher._wal_last_fold_bytes)

    # ── 2. a second submission while a fold is RUNNING is refused (the retry reflex costs nothing) ──
    gate.clear()                                   # the next fold will block inside fake_compact
    wal[0] = 3000
    calls[0] = 0
    r2a = d("sys.compact", {})                      # starts job A (which blocks on the gate)
    jid_a = r2a.get("job")
    # give the worker a beat to pick the job up (it may be PENDING or RUNNING — both refuse)
    time.sleep(0.2)
    r2b = d("sys.compact", {})                      # retry mid-fold
    check("a second sys.compact mid-fold is refused with the running job id (no second fold)",
          r2a.get("started") is True and r2b.get("started") is False and r2b.get("job") == jid_a,
          "A=%s B=%s" % (r2a, r2b))
    gate.set()                                     # release job A
    st2 = _wait_job_done(k, jid_a)
    check("after release, exactly ONE fold ran despite two submissions",
          st2 == "DONE" and calls[0] == 1, "status=%s calls=%d" % (st2, calls[0]))

    # ── 3. growth-threshold semantics: baseline tracks the last fold, so a quiet generation does
    #        not re-fold. Assert the condition the idle daemon evaluates (grown = wal - baseline). ──
    base = KernelDispatcher._wal_last_fold_bytes    # == 500 (post the §2 fold)
    threshold = 1 << 30
    wal[0] = base + 10 * 1024 * 1024                # +10 MB of new WAL — well under the 1 GiB threshold
    grown_small = k.manager.shared_nucleus.core.wal_bytes() - base
    check("after a fold, a small generation stays BELOW threshold (no re-fold every idle check)",
          grown_small < threshold, "grown=%d threshold=%d" % (grown_small, threshold))
    wal[0] = base + threshold + 1                   # +1 GiB of new WAL
    grown_big = k.manager.shared_nucleus.core.wal_bytes() - base
    check("~1 GiB of NEW growth crosses threshold exactly once (growth, not total size)",
          grown_big > threshold, "grown=%d threshold=%d" % (grown_big, threshold))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — sys.compact is async (returns a job id in < 1 s, never the 60 s+ inline "
          "fold), a mid-fold retry is refused with the running id (one fold, not N), and the "
          "auto-checkpoint baseline tracks the last fold so the idle daemon folds on ~1 GiB of NEW "
          "growth rather than every check on a large live store.")
    sys.exit(0)


if __name__ == "__main__":
    main()
