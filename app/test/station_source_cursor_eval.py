#!/usr/bin/env python3
"""
THE NEXT ITEM IS THE NEXT ONE NOBODY HAS READ — D14.

From 02:47 on 09-27 every news-show run aired `neta:studio_ai:news_show:001` (25 runs by the time it
was seen). The notebook has thirty items. Three things in `bench_station._resolve_source` made it:

  · "seen" was read from `station.air.ls name=<bench>` at the op's default window — the newest 200
    rows of the WHOLE bench, which five workloads share — so which items counted as aired depended
    on how much the other programmes had aired lately;
  · every row counted, including the ones from before the D13 fix, which name items the model was
    never sent;
  · once everything looked seen it returned `eps[0]` — item 001 — forever.

Held here on a real dispatcher, with a thirty-item notebook:

  A  thirty `source=next` turns air items 001…030 in order, once each
  B  the news show broadcasts around the clock (project owner, 2026-09-27): the 31st turn is a
     REBROADCAST of the least recently aired item — no stand-by, no gap — and an item added later
     airs first, then joins the rotation. Every declared programme is `wrap`.
  C  `on_exhausted: stand_by`, declared explicitly, still stands by `source_exhausted` with no model
     call (the option exists; no programme uses it)
  D  an aired row without `grounded` (a pre-fix row) does not consume an item — unless the
     programme declares `unmarked_rows: count` (the reading room, whose prompts always carried it)
  E  another programme's rows on the same bench, naming the same items, do not move the cursor
  F  every aired turn's row is stamped `grounded: true`; a stood-by row is not

Run:  python app/test/station_source_cursor_eval.py     (exit 0 = all pass)
"""
import copy
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []
N = 30
PROGRAM = "studio_ai/news_show"


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
    calls = [0]

    def gen(provider, model, system, user, timeout=60.0):
        calls[0] += 1
        return "Line number %d, read from the item." % calls[0]

    real_gen, real_wl = llm_provider.generate, BS.BenchStationConcept._workload
    llm_provider.generate = gen

    def cell(overrides=None, tag="c"):
        """A fresh cell with the news show provisioned and a thirty-item notebook of its own."""
        k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_d14_"))
        k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                    "params": {"session_token": "admin",
                               "data": {"user_name": "admin",
                                        "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                    "id": "g"}, "local")

        def raw(client, method, data):
            return k.dispatch({"jsonrpc": "2.0", "method": method,
                               "params": {"session_token": client, "data": data}, "id": "t"},
                              "local")

        def d(client, method, data):
            return (raw(client, method, data) or {}).get("result") or {}

        cfg = copy.deepcopy(_W.by_key(k, PROGRAM))
        cfg.update(overrides or {})
        provision(raw, cfg, note=lambda m: None)          # provisioning reads the RPC envelope
        set_name = "test:d14:%s:notebook" % tag
        cfg["pins"] = dict(cfg.get("pins") or {}, item_set=set_name)
        items = ["test:d14:%s:item:%03d" % (tag, i) for i in range(1, N + 1)]
        for i, a in enumerate(items, 1):
            d("admin", "kernel.memory.define", {"name": a, "description": "News item %d, as written." % i,
                                                "scope": "universal"})
            d("admin", "set.add", {"name": set_name, "id": a})
        BS.BenchStationConcept._workload = lambda self, key: cfg if key == PROGRAM else real_wl(self, key)
        return k, d, cfg, items

    def anchor(d, client, n):
        return d(client, "station.air.turn", {"program": PROGRAM, "role": "Anchor", "source": "next",
                                            "provider": "mistral", "turn": "d14:%d" % n})

    def rows(d, cfg, program=PROGRAM):
        return d("admin", "station.air.ls", {"name": _W.bench_slug(cfg), "program": program,
                                           "limit": "100000"}).get("aired") or []

    try:
        print("\n  ── A/B/F · thirty items in order, then the rebroadcast — no stand-by ──")
        k, d, cfg, items = cell(tag="a")
        client = _W.client_of(cfg)
        check("the news show declares `on_exhausted: wrap` — it is on air 24 hours",
              _W.by_key(k, PROGRAM).get("on_exhausted") == "wrap",
              str(_W.by_key(k, PROGRAM).get("on_exhausted")))
        got = []
        for n in range(1, N + 1):
            r = anchor(d, client, n)
            got.append(r.get("source") if r.get("status") == "aired" else "(%s)" % r.get("reason"))
        check("A: thirty `next` turns air items 001…030, in order, once each", got == items,
              "first=%s last=%s distinct=%d" % (got[:1], got[-1:], len(set(got))))
        rs = rows(d, cfg)
        check("F: every aired row is stamped `grounded: true`",
              len(rs) == N and all(r.get("grounded") for r in rs), "%d rows" % len(rs))
        r31 = anchor(d, client, N + 1)
        r32 = anchor(d, client, N + 2)
        check("B: the 31st turn AIRS a rebroadcast of item 001 — the least recently aired",
              r31.get("status") == "aired" and r31.get("source") == items[0],
              "%s / %s / %s" % (r31.get("status"), r31.get("reason"), r31.get("source")))
        check("B: …and the 32nd rebroadcasts 002, not 001 again", r32.get("source") == items[1],
              "%s / %s" % (r32.get("status"), r32.get("source")))
        new = "test:d14:a:item:%03d" % (N + 1)
        d("admin", "kernel.memory.define", {"name": new, "description": "A new item, added later.",
                                            "scope": "universal"})
        d("admin", "set.add", {"name": "test:d14:a:notebook", "id": new})
        r33 = anchor(d, client, N + 3)
        r34 = anchor(d, client, N + 4)
        check("B: an item added to the notebook airs FIRST (it has never aired)",
              r33.get("source") == new, "%s / %s" % (r33.get("status"), r33.get("source")))
        check("B: …and then the rotation carries on where it was (003)",
              r34.get("source") == items[2], "%s / %s" % (r34.get("status"), r34.get("source")))
        check("B: no turn of the news show stood by at any point",
              not [x for x in rows(d, cfg) if not x.get("aired")],
              str([x.get("reason") for x in rows(d, cfg) if not x.get("aired")][:3]))

        print("\n  ── C · `on_exhausted: stand_by`, declared, still stands by (the option) ──")
        k, d, cfg, items = cell({"on_exhausted": "stand_by"}, tag="c")
        client = _W.client_of(cfg)
        for n in range(1, N + 1):
            anchor(d, client, n)
        c0 = calls[0]
        r = anchor(d, client, N + 1)
        check("C: the 31st turn stands by `station:reason:source_exhausted`",
              r.get("reason") == BS.REASON_SOURCE_EXHAUSTED, json.dumps(r)[:140])
        check("C: …and makes NO model call", calls[0] == c0, "calls=%d" % (calls[0] - c0))
        st = [x for x in rows(d, cfg) if x.get("turn") == "d14:%d" % (N + 1)]
        check("F: …its stand-by row carries the reason and is NOT grounded",
              len(st) == 1 and st[0].get("reason") == BS.REASON_SOURCE_EXHAUSTED
              and not st[0].get("grounded") and not st[0].get("aired"), str(st)[:140])

        print("\n  ── D · a row without `grounded` does not consume an item ──")
        k, d, cfg, items = cell(tag="d")
        client = _W.client_of(cfg)
        # a pre-fix row: aired, names item 001, carries no `grounded` — written through the op
        # itself (the recorder has no RPC of its own; the turn op is its only caller)
        def record(k, cfg, **kw):
            BS.BenchStationConcept(k.manager.get_session("admin")).op_air(
                name=_W.bench_slug(cfg), provider="mistral", model="m", aired="1", **kw)

        record(k, cfg, source=items[0], turn="legacy", program=PROGRAM)
        check("D: the pre-fix row is on the record (so the next check is not vacuous)",
              any(x.get("source") == items[0] and not x.get("grounded") for x in rows(d, cfg)))
        r = anchor(d, client, 1)
        check("D: an unmarked aired row naming 001 does not consume it — 001 airs as itself",
              r.get("source") == items[0], "%s / %s" % (r.get("status"), r.get("source")))
        k, d, cfg, items = cell({"unmarked_rows": "count"}, tag="d2")
        client = _W.client_of(cfg)
        record(k, cfg, source=items[0], turn="legacy", program=PROGRAM)
        r = anchor(d, client, 1)
        check("D: …unless the programme declares `unmarked_rows: count` — then it moves on to 002",
              r.get("source") == items[1], "%s / %s" % (r.get("status"), r.get("source")))

        print("\n  ── E · another programme's rows on the same bench do not move the cursor ──")
        k, d, cfg, items = cell(tag="e")
        client = _W.client_of(cfg)
        for i in range(0, 5):
            record(k, cfg, source=items[i], turn="other", program="studio_ai/art_explorer",
                   grounded="1")
        check("E: the other programme's five grounded rows are on the bench (not vacuous)",
              len([x for x in rows(d, cfg, "studio_ai/art_explorer") if x.get("grounded")]) == 5)
        r = anchor(d, client, 1)
        check("E: five grounded rows of ANOTHER programme naming 001–005 leave the cursor at 001",
              r.get("source") == items[0], "%s / %s" % (r.get("status"), r.get("source")))

        print("\n  ── the declarations say what they mean ──")
        decls = {_W.key(x): x for x in _W.declarations(None)}
        for key, want in (("studio_ai/news_show", "wrap"), ("studio_ai/thinkers_shelf", "wrap"),
                          ("studio_ai/art_explorer", "wrap"), ("studio_ai/plant_geek", "wrap")):
            check("%s declares on_exhausted=%s" % (key, want),
                  (decls.get(key) or {}).get("on_exhausted") == want,
                  str((decls.get(key) or {}).get("on_exhausted")))
        src = open(os.path.join(ROOT, "app/concepts/bench_station.py"), encoding="utf-8").read()
        check("no `return eps[0]` is left in the op", "return eps[0]" not in src)
    finally:
        llm_provider.generate = real_gen
        BS.BenchStationConcept._workload = real_wl

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the next item is the next one THIS programme has not read, counted from its "
          "own grounded rows only: thirty items air in order once each; then the news show keeps "
          "broadcasting — the least recently aired item comes round again, a newly added item airs "
          "first and joins the rotation, and no turn stands by; `stand_by` remains only as a declared "
          "option; a pre-fix row consumes nothing unless the programme declares its unmarked rows "
          "real; and another programme's rows never move the cursor.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
