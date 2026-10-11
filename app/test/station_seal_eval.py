#!/usr/bin/env python3
"""
AN AIRED TURN IS SEALED THROUGH THE PUBLIC DOOR — `chronon.seal`, not the chronon layer's privates.

Until 09-26 `bench_station._seal` reached into `ChrononConcept._chronons_set` / `._mint` and read
the society's frontier straight off the group engine. That skipped the seal gate, recorded no
scribe, and silently extended `frontier[0]` of a forked timeline. It now calls `chronon.seal`
(the platform's published op) with the society resolved by `SocietyConcept.society_key`.

Held here on a real dispatcher, as the programme's OWN client:

  · every aired turn seals exactly one PERFECTIVE chronon, labelled with the turn's source
  · the chain stays linear — one frontier, the newest chronon
  · a turn that stands by seals nothing (the timeline records what was said, not what was not)

Run:  python app/test/station_seal_eval.py     (exit 0 = all pass)
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

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_seal_"))

    def d(client, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": client, "data": data}, "id": "t"}, "local")

    def res(r):
        return (r or {}).get("result") or {}

    d("admin", "kernel.genesis_rite", {"user_name": "admin",
                                       "passphrase": hashlib.sha256(b"pw").hexdigest()})
    real_gen = llm_provider.generate
    llm_provider.generate = lambda p, m, s, u, timeout=60.0: "A grounded line."
    try:
        cfg = _W.by_key(k, "studio_ai/news_show")
        provision(d, cfg, note=lambda m: None)
        client = _W.client_of(cfg)
        gid, space = _W.society_of(cfg)
        d("admin", "kernel.memory.define", {"name": "test:seal:item",
                                            "description": "An item to air.", "scope": "universal"})

        def chronons():
            return res(d(client, "chronon.ls", {"group": gid, "space": space}))

        for i in range(3):
            r = res(d(client, "station.air.turn",
                      {"program": "studio_ai/news_show", "role": "Anchor",
                       "source": "test:seal:item", "provider": "mistral", "turn": "s%d" % i}))
            check("turn %d airs" % (i + 1), r.get("status") == "aired", json.dumps(r)[:120])
        ls = chronons()
        seq = ls.get("chronons") or []
        check("three aired turns seal three chronons", len(seq) == 3, "count=%d" % len(seq))
        check("… each PERFECTIVE and labelled with the turn's source",
              all(c.get("aspect") == "perfective" and c.get("label") == "test:seal:item"
                  for c in seq), json.dumps(seq)[:160])
        check("… and the chain is linear: one frontier, the newest chronon",
              ls.get("frontiers") == [seq[-1].get("chronon")] if seq else False,
              str(ls.get("frontiers")))

        llm_provider.generate = lambda p, m, s, u, timeout=60.0: ""
        r = res(d(client, "station.air.turn",
                  {"program": "studio_ai/news_show", "role": "Anchor",
                   "source": "test:seal:item", "provider": "mistral", "turn": "s-none"}))
        check("a turn the model does not produce stands by", r.get("status") != "aired",
              str(r.get("reason")))
        check("… and seals nothing", len(chronons().get("chronons") or []) == 3)
    finally:
        llm_provider.generate = real_gen

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — an aired turn is sealed through `chronon.seal` as the programme's own "
          "client: one perfective chronon per aired turn, labelled with its source, on a linear "
          "chain; a stood-by turn seals nothing.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
