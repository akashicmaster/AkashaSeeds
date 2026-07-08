#!/usr/bin/env python3
"""
Concurrent-login test — the per-instance client cap under simultaneous login.

Each Cell caps concurrent sessions at `manager.max_sessions` (the seeds family-use
default is 5, set via AKASHA_MAX_LEAVES; it is a single `if` gate in
manager.get_session and trivially changed). The cap must behave correctly when
several clients log in *at the same instant* — the interesting property is not the
number but that the check-then-create cannot overshoot under a race. Session
create/update is serialised through the manager's `_session_wq`, so this test
proves that guarantee holds.

  P1 all-seats     — fill exactly `cap` seats via a simultaneous login barrier;
                     every client gets a distinct, isolated session.
  P2 cap-enforced  — one more login on a full Cell is refused ("Limit Reached").
  P3 no-overshoot  — race far more logins than seats at one barrier; exactly `cap`
                     win and the live session count never exceeds `cap`.
  P4 seat-recycle  — closing a session frees a seat for a waiting client.

Run:  python test/loadtest_login.py

Developer verification test (not a user-facing .ak example). It drives the real
AkashaManager — the component that enforces the cap — directly.
"""
import os
import sys
import hashlib
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

import tempfile

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def new_manager(cap):
    """A fresh AkashaManager with max_sessions=cap (read from env at init)."""
    os.environ["AKASHA_MAX_LEAVES"] = str(cap)
    from lib.akasha.manager import AkashaManager
    return AkashaManager(series_name="seeds",
                         base_dir=tempfile.mkdtemp(prefix="akasha_login_"))


def register(mgr, client_ids):
    from lib.akasha.identity import Role
    for cid in client_ids:
        ph = hashlib.sha256(f"pw-{cid}".encode()).hexdigest()
        mgr.iam.register_client(cid, Role.USER, passphrase_hash=ph,
                                created_by="admin", display_name=cid)


def simultaneous_login(mgr, client_ids):
    """Fire get_session for every client at one barrier; return {cid: (status, info)}."""
    out = {}
    lock = threading.Lock()
    barrier = threading.Barrier(len(client_ids))

    def login(cid):
        barrier.wait()  # release all threads at the same instant → maximise the race
        try:
            s = mgr.get_session(cid)
            with lock:
                out[cid] = ("ok", s)
        except PermissionError as e:
            with lock:
                out[cid] = ("denied", str(e))
        except Exception as e:  # noqa: BLE001
            with lock:
                out[cid] = ("error", repr(e))

    ts = [threading.Thread(target=login, args=(c,)) for c in client_ids]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=30)
    return out


# ── P1: fill exactly `cap` seats via simultaneous login ──────────────────────

def phase1_all_seats(cap=5):
    mgr = new_manager(cap)
    cids = [f"fam{i}" for i in range(cap)]
    register(mgr, cids)
    out = simultaneous_login(mgr, cids)

    oks = [c for c, (st, _) in out.items() if st == "ok"]
    # Isolation by construction: each session is a distinct object with its own cortex.
    sessions = [info for (st, info) in out.values() if st == "ok"]
    distinct_cortex = len({id(s.local_cortex) for s in sessions})
    ok = (len(oks) == cap and len(mgr.sessions) == cap and distinct_cortex == cap)
    record("P1 all-seats", ok,
           f"{len(oks)}/{cap} logged in simultaneously, "
           f"{distinct_cortex} distinct cortexes, live={len(mgr.sessions)}")
    return mgr


# ── P2: one more login on a full Cell is refused ─────────────────────────────

def phase2_cap_enforced(mgr, cap=5):
    register(mgr, ["intruder"])
    try:
        mgr.get_session("intruder")
        record("P2 cap-enforced", False, "6th login SUCCEEDED — cap not enforced")
    except PermissionError as e:
        msg = str(e)
        ok = "Limit Reached" in msg and len(mgr.sessions) == cap
        record("P2 cap-enforced", ok,
               f"over-cap login refused ('{msg[:38]}...'), live still {len(mgr.sessions)}")


# ── P3: race far more logins than seats — no overshoot ───────────────────────

def phase3_no_overshoot(cap=5, contenders=20):
    mgr = new_manager(cap)
    cids = [f"race{i}" for i in range(contenders)]
    register(mgr, cids)
    out = simultaneous_login(mgr, cids)

    oks = sum(1 for st, _ in out.values() if st == "ok")
    denied = sum(1 for st, _ in out.values() if st == "denied")
    errors = [i for st, i in out.values() if st == "error"]
    # The core guarantee: the serialised check-then-create never lets the live count
    # exceed the cap, no matter how many race the barrier.
    ok = (oks == cap and len(mgr.sessions) == cap and not errors)
    record("P3 no-overshoot", ok,
           f"{contenders} raced → {oks} won / {denied} refused, "
           f"live={len(mgr.sessions)} (cap {cap}), errors={len(errors)}")


# ── P4: closing a session frees a seat ───────────────────────────────────────

def phase4_seat_recycle(cap=3):
    mgr = new_manager(cap)
    cids = [f"seat{i}" for i in range(cap)]
    register(mgr, cids)
    simultaneous_login(mgr, cids)
    full = len(mgr.sessions)

    # A waiting client is refused while full...
    register(mgr, ["waiter"])
    refused_when_full = False
    try:
        mgr.get_session("waiter")
    except PermissionError:
        refused_when_full = True

    # ...then a seat is freed and the waiter gets in.
    mgr.close_session(cids[0])
    got_in = False
    try:
        mgr.get_session("waiter")
        got_in = True
    except PermissionError:
        got_in = False

    ok = (full == cap and refused_when_full and got_in and len(mgr.sessions) == cap)
    record("P4 seat-recycle", ok,
           f"full={full}, refused-when-full={refused_when_full}, "
           f"admitted-after-close={got_in}, live={len(mgr.sessions)}")


def main():
    print("\n  concurrent-login / client-cap test "
          "(cap is a family-use default behind one `if`)\n")
    cap = 5
    mgr = phase1_all_seats(cap)
    phase2_cap_enforced(mgr, cap)
    phase3_no_overshoot(cap=5, contenders=20)
    phase4_seat_recycle(cap=3)

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the client cap misbehaved under concurrent login.")
        return 1
    print("\nRESULT: PASS — cap holds exactly under simultaneous login, no overshoot, "
          "seats recycle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
