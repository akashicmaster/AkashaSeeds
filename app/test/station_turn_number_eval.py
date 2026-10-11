#!/usr/bin/env python3
"""
A TURN KEEPS ONE NUMBER ACROSS ITS BEATS — THE BUMPER NEVER PLAYS MID-TURN (D18).

Owner report 2026-10-02: the AI News room played its between-turn bumper after the Anchor and the
Commentator, before the Anchor's close. The room treats a CHANGE of the utterance's `turn` as the
turn boundary; the number was the position of the item in the programme's newest 200 rows — a sliding
window — so once the record outgrew it the three beats of ONE item got 68, 67, 66. A rebroadcast also
reused the item's first number, so numbers ran backwards.

Held on a real dispatcher over 80 items (240 beats, past the window), then a rebroadcast cycle:

  A  the three beats of every item carry ONE number
  B  the next item is exactly one higher — numbers rise monotonically through the record
  C  after the Set is exhausted (wrap) the numbers keep rising, not back to the first airing
  D  a record from before `turn_no` (no number on its rows) continues from its full count
  E  the feed utterances carry the same numbers (what the room reads)

Run:  python app/test/station_turn_number_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

PROGRAM = "studio_ai/news_show"
SET = "neta:studio_ai:news_show:src"
N_ITEMS = 80
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.workbench import llm_provider
    from lib.akasha.workbench import workload as _W
    from lib.akasha.workbench.workload_provision import provision
    from app.concepts import bench_station as BS

    KernelDispatcher._boot_load_ontology = lambda self: None
    n = [0]

    def gen(provider, model, system, user, timeout=60.0):
        n[0] += 1
        return "Line number %d." % n[0]

    real = llm_provider.generate
    llm_provider.generate = gen
    try:
        k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_d18_"))

        def raw(client, method, data):
            return k.dispatch({"jsonrpc": "2.0", "method": method,
                               "params": {"session_token": client, "data": data}, "id": "t"}, "local")

        def d(client, method, data):
            return (raw(client, method, data) or {}).get("result") or {}

        raw("admin", "kernel.genesis_rite", {"user_name": "admin",
                                             "passphrase": hashlib.sha256(b"pw").hexdigest()})
        cfg = _W.by_key(k, PROGRAM)
        provision(raw, cfg, note=lambda m: None)
        client = _W.client_of(cfg)
        for i in range(N_ITEMS):
            a = "neta:studio_ai:news_show:2026-10-02:%03d" % (i + 1)
            d("admin", "kernel.memory.define", {"name": a, "description": "Fact number %d about AI." % (i + 1),
                                                "scope": "universal"})
            d("admin", "set.add", {"name": SET, "id": a})

        def run_item(i):
            for role, src in (("Anchor", "next"), ("Commentator", "current"), ("Anchor.wrap", "current")):
                d(client, "station.air.turn", {"program": PROGRAM, "role": role, "source": src,
                                             "provider": "mistral", "turn": "d18:%d:%s" % (i, role)})

        def rows():
            return d("admin", "station.air.ls", {"name": _W.bench_slug(cfg), "program": PROGRAM,
                                               "limit": "100000"}).get("aired") or []

        def by_item(rs):
            out = {}
            for r in rs:
                if str(r.get("aired")) in ("1", "True", "true"):
                    out.setdefault(r.get("atom"), []).append(r.get("turn_no"))
            return out

        for i in range(N_ITEMS):
            run_item(i)
        rs = rows()
        groups = by_item(rs)
        order = []
        for r in rs:
            if r.get("atom") not in order and str(r.get("aired")) in ("1", "True", "true"):
                order.append(r.get("atom"))
        check("every item aired all three beats", len(groups) == N_ITEMS and all(len(v) == 3 for v in groups.values()),
              "%d items" % len(groups))
        check("A: the three beats of every item carry ONE number",
              all(len(set(v)) == 1 and v[0] for v in groups.values()),
              str([(a.split(":")[-1], v) for a, v in groups.items() if len(set(v)) != 1][:3]))
        nums = [groups[a][0] for a in order]
        check("B: item after item the number is exactly one higher (through %d beats, past the 200-row window)"
              % (3 * N_ITEMS), nums == list(range(nums[0], nums[0] + N_ITEMS)), str(nums[:4]) + "…" + str(nums[-3:]))

        for i in range(N_ITEMS, N_ITEMS + 3):          # the Set is exhausted: the rebroadcast
            run_item(i)
        rs = rows()
        last3 = [r for r in rs if str(r.get("aired")) in ("1", "True", "true")][-9:]
        got = [r.get("turn_no") for r in last3]
        check("C: a rebroadcast keeps the numbers rising (and one per item), not back to the first airing",
              len(set(got[0:3])) == 1 and len(set(got[3:6])) == 1 and len(set(got[6:9])) == 1
              and got[0] == nums[-1] + 1 and got[3] == got[0] + 1 and got[6] == got[3] + 1, str(got))

        msgs = d("admin", "society.feed", {"group": "studio_ai", "space": "news_show", "limit": "1000"}) \
            .get("messages") or []
        tn = [m.get("turn") for m in msgs]
        check("E: the feed utterances carry the same numbers the room reads (3 per number; the oldest may be cut by the feed's own window)",
              bool(tn) and all(tn.count(t) == 3 for t in set(tn) if t != tn[0]) and 0 not in tn, str(tn[-6:]))

        print("\n  ── D · a record from before `turn_no` ──")
        k2 = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_d18b_"))
        bs = BS.BenchStationConcept(k2.manager.get_session("admin"))
        # legacy rows: two items aired, no turn_no on them
        k2.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                     "params": {"session_token": "admin", "data": {
                         "user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
        bs = BS.BenchStationConcept(k2.manager.get_session("admin"))
        name = _W.bench_slug(cfg)
        for src in ("s1", "s1", "s1", "s2", "s2", "s2"):
            bs.op_air(name=name, source=src, provider="mistral", model="m", aired="1", program=PROGRAM,
                      atom="x:" + src)
        a = bs._turn_no(name, PROGRAM, "s2", "x:s2")
        b = bs._turn_no(name, PROGRAM, "s3", "x:s3")
        check("D: a legacy record counts its items once — the open item is turn 2, a new one is turn 3",
              (a, b) == (2, 3), str((a, b)))
    finally:
        llm_provider.generate = real

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a turn keeps one number across its beats however long the record grows, "
          "the next turn is exactly one higher, a rebroadcast keeps counting up, and a record from "
          "before the number was stored continues from its full count.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
