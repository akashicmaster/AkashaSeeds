#!/usr/bin/env python3
"""
`station.air.ls` returns the NEWEST rows, newest last — which its docstring always claimed.

It returned STORE order: the rows came out in whatever order the aired Set yields its members, and
`limit` sliced the tail of that. So `limit=40` was forty arbitrary turns, and every reader that took
the last row as "the latest" was reading a row chosen by hash order. The platform's run outcome did
exactly that and read a run's reason back as `''` eleven times in twelve (P7 / D10, 2026-09-26); the
platform stopped depending on it, and asked (`needs user:`) that the op itself be fixed for the
rooms and pages that still read it directly, and that it accept `since=`.

Held here on a real dispatcher, with enough rows that store order and time order cannot agree:

  · rows come back in ascending wall-clock order, so the LAST row is the newest
  · `limit=N` is the NEWEST N — not N arbitrary rows
  · `since=<epoch>` keeps exactly the rows after that moment (one run's rows)
  · `program=` still narrows to one workload, and composes with `since` and `limit`
  · `count` / `bench_count` still say how far the read was narrowed

Run:  python app/test/bench_air_ls_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from app.concepts.bench_station import BenchStationConcept

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_airls_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "x"}, "local")
        return (r or {}).get("result") or {}

    d("bench.new", {"name": "airls", "kind": "publish"})
    bs = BenchStationConcept(k.manager.get_session("admin"))
    A, B = "studio_ai/a", "studio_ai/b"

    # 24 turns of A and 8 of B, interleaved, each at a distinct later moment. `mid` falls between
    # the 12th and 13th of A — the start of "a later run".
    mid = 0.0
    for i in range(32):
        prog = B if i % 4 == 3 else A
        bs.op_air(name="airls", program=prog, source="s", turn="t%02d" % i,
                  aired="1" if i % 3 else "0", reason="" if i % 3 else "station:reason:no_text")
        time.sleep(0.004)
        if i == 15:
            time.sleep(0.02); mid = time.time(); time.sleep(0.02)

    print("\n  ── ordering ──")
    allrows = d("station.air.ls", {"name": "airls", "limit": "500"}).get("aired") or []
    ats = [float(r.get("at") or 0) for r in allrows]
    check("every row comes back (32)", len(allrows) == 32, "n=%d" % len(allrows))
    check("rows are in ascending wall-clock order — newest LAST, as the op has always claimed",
          ats == sorted(ats), "first 5 at=%s" % [round(a % 1000, 3) for a in ats[:5]])
    check("… so the last row IS the newest", bool(ats) and ats[-1] == max(ats))

    print("\n  ── limit is the NEWEST N ──")
    five = d("station.air.ls", {"name": "airls", "limit": "5"}).get("aired") or []
    want5 = sorted(ats)[-5:]
    got5 = [float(r.get("at") or 0) for r in five]
    check("`limit=5` returns exactly the five newest rows", got5 == want5,
          "got=%s want=%s" % ([round(a % 1000, 3) for a in got5],
                              [round(a % 1000, 3) for a in want5]))

    print("\n  ── since= is one run's rows ──")
    late = d("station.air.ls", {"name": "airls", "since": str(mid), "limit": "500"})
    lr = late.get("aired") or []
    check("`since=` keeps only rows strictly after that moment",
          bool(lr) and all(float(r.get("at") or 0) > mid for r in lr),
          "n=%d" % len(lr))
    check("… and keeps ALL of them", len(lr) == sum(1 for a in ats if a > mid),
          "got=%d want=%d" % (len(lr), sum(1 for a in ats if a > mid)))
    check("… echoing the cut-off it applied", late.get("since") == mid, str(late.get("since")))

    print("\n  ── program= composes with both ──")
    ar = d("station.air.ls", {"name": "airls", "program": A, "since": str(mid), "limit": "3"})
    arows = ar.get("aired") or []
    a_after = sorted(float(r.get("at") or 0) for r in allrows
                     if r.get("program") == A and float(r.get("at") or 0) > mid)
    check("program + since + limit → the newest 3 of THAT workload after the cut-off",
          [float(r.get("at") or 0) for r in arows] == a_after[-3:]
          and all(r.get("program") == A for r in arows), "n=%d" % len(arows))
    check("`count` is what came back, `bench_count` is the bench's total",
          ar.get("count") == len(arows) and ar.get("bench_count") == 32,
          "count=%s bench_count=%s" % (ar.get("count"), ar.get("bench_count")))

    print("\n  ── the reader that went wrong: \"the latest stand-by\" ──")
    # What the platform's run outcome did, and what a room does when it shows the last airing:
    # take the last non-aired row with a reason. It must be the newest such row.
    stood = [r for r in allrows if str(r.get("aired")) in ("0", "False") and r.get("reason")]
    newest_stood = max(stood, key=lambda r: float(r.get("at") or 0)) if stood else {}
    last_seen = next((r for r in reversed(allrows)
                      if str(r.get("aired")) in ("0", "False") and r.get("reason")), {})
    check("walking newest-first finds the NEWEST stand-by, not one chosen by hash order",
          bool(stood) and last_seen.get("obs") == newest_stood.get("obs"),
          "found=%s newest=%s" % (last_seen.get("turn"), newest_stood.get("turn")))

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — `station.air.ls` orders by wall clock before `limit`, so the last row is the "
          "newest and `limit=N` is the newest N; `since=` returns exactly one run's rows; and "
          "`program=` composes with both. A reader walking newest-first now finds the newest "
          "stand-by rather than one picked by hash order.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
