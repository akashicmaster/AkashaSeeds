#!/usr/bin/env python3
"""
THE READING ROOM READS THE BOOK IN ITS OWN ORDER, EVERY PASSAGE ONCE — D17.

Directive 2026-10-02 §1. Two defects, both in how `bench_station` keeps its place in an episode:

  · THE CURSOR KEYED BY ANCHOR. The Dibdin preface's first two passages share the anchor
    `The Preface · p.[i]`, so airing one marked BOTH as read and the other never aired on its own.
  · THE ORDER WAS THE STORE'S ACCIDENT. The episode was sorted by `alias(k)` — the FIRST alias of the
    key. An atom with several aliases answers whichever the store lists first, so since 09-27 the room
    read p.[i], dedication, imprint, title page, p.ii, p.iv instead of the book.

Held here on a real dispatcher, with the REAL passages of `shelf_dibdin` (passages_ep1.json), the store forced to answer a
different first alias for each — the live condition — and the precondition checked, so the eval cannot pass by never having the problem:

  A  the seven passages air in BOOK order, title page first, each exactly once per cycle
  B  the two passages that share an anchor BOTH air
  C  the 8th turn wraps to the least recently aired — the title page again
  D  a row from before `atom` existed (anchor only) consumes its passage when the anchor is unique,
     and consumes NOTHING when it is shared
  E  a passage that declares `seq` goes by it, whatever its name; natural order for numbers
  F  every aired row names its atom

Run:  python app/test/station_reading_order_eval.py     (exit 0 = all pass)
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

PROGRAM = "studio_ai/thinkers_shelf"
SET = "shelf:dibdin:passages:ep1"
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

    passages = json.load(open(os.path.join(ROOT, "app", "ontology", "shelf_dibdin", "passages_ep1.json"),
                              encoding="utf-8"))["passages"]
    want = [p["atom"] for p in passages]                      # the pack's own order
    KernelDispatcher._boot_load_ontology = lambda self: None
    calls = [0]

    def gen(provider, model, system, user, timeout=60.0):
        calls[0] += 1
        return "A line about the passage, number %d." % calls[0]

    real_gen = llm_provider.generate
    llm_provider.generate = gen

    def cell(extra_aliases=True):
        k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_d17_"))

        def raw(client, method, data):
            return k.dispatch({"jsonrpc": "2.0", "method": method,
                               "params": {"session_token": client, "data": data}, "id": "t"}, "local")

        def d(client, method, data):
            return (raw(client, method, data) or {}).get("result") or {}

        raw("admin", "kernel.genesis_rite", {"user_name": "admin",
                                             "passphrase": hashlib.sha256(b"pw").hexdigest()})
        cfg = _W.by_key(k, PROGRAM)
        provision(raw, cfg, note=lambda m: None)
        for p in passages:
            d("admin", "kernel.memory.define", {"name": p["atom"], "description": json.dumps(p),
                                                "scope": "universal"})
            d("admin", "set.add", {"name": SET, "id": p["atom"]})
        return k, d, cfg

    def read(d, cfg, client, n):
        return d(client, "station.air.turn", {"program": PROGRAM, "role": "Reader", "source": "next",
                                            "provider": "mistral", "turn": "d17:%d" % n})

    def rows(d, cfg):
        return d("admin", "station.air.ls", {"name": _W.bench_slug(cfg), "program": PROGRAM,
                                           "limit": "100000"}).get("aired") or []

    def record(k, cfg, **kw):
        BS.BenchStationConcept(k.manager.get_session("admin")).op_air(
            name=_W.bench_slug(cfg), provider="mistral", model="m", aired="1", program=PROGRAM, **kw)

    try:
        print("\n  ── the live condition ──")
        k, d, cfg = cell()
        client = _W.client_of(cfg)
        bs = BS.BenchStationConcept(k.manager.get_session(client))
        # The live condition, made deterministic: the store answers a DIFFERENT first alias for each
        # passage, in an order that is not the book's (adding aliases is not enough on either store —
        # both list the earliest-registered first here — so the answer itself is forced).
        hostile = {a: "zz:%02d" % (len(want) - i) for i, a in enumerate(want)}
        key_to_atom = {bs._key(a): a for a in want}
        real_alias = BS.BenchStationConcept._alias

        def forced_alias(self, key):
            return hostile.get(key_to_atom.get(key), real_alias(self, key))

        for a, n in hostile.items():           # real aliases: they RESOLVE to the atom, as live ones do
            reg = d("admin", "kernel.identity.alias", {"id": a, "name": n})
        check("PRECONDITION: the hostile aliases are registered and resolve to their atoms",
              all(bs._key(n) == bs._key(a) for a, n in hostile.items()), str(reg)[:80])
        BS.BenchStationConcept._alias = forced_alias
        firsts = [bs._alias(bs._key(a)) for a in want]
        check("PRECONDITION: the store's FIRST alias of every passage is not its declared name, and sorted "
              "by it the passages would be in REVERSE book order",
              all(f != a for f, a in zip(firsts, want)) and sorted(firsts) == firsts[::-1], str(firsts[:3]))
        anchors = {}
        for p in passages:
            a = p["anchor"]
            anchors.setdefault(" · ".join(str(x) for x in [p.get("book"), p.get("section"),
                                                           ("p.%s" % a["page"]) if a.get("page") else None] if x),
                               []).append(p["atom"])
        shared = [v for v in anchors.values() if len(v) > 1]
        check("PRECONDITION: two passages of the real pack share an anchor", bool(shared), str(shared[:1]))
        eps = bs._episode(_W.by_key(k, PROGRAM))
        check("the episode IS the pack's order, by declared atom, whatever the store's aliases say",
              [e["atom"] for e in eps] == want, str([e["atom"].split(":")[-1] for e in eps]))

        print("\n  ── A/B/C/F · the book, once each, then round again ──")
        got, atoms = [], []
        for n in range(1, len(want) + 1):
            r = read(d, cfg, client, n)
            got.append(r.get("status"))
        rs = rows(d, cfg)
        atoms = [x.get("atom") for x in rs if x.get("aired")]
        check("A: the seven passages air in BOOK order, title page first", atoms == want,
              str([a.split(":")[-1] for a in atoms]))
        check("A: each exactly once in the cycle", len(set(atoms)) == len(want) and all(g == "aired" for g in got),
              str(got))
        check("B: the two passages that share an anchor BOTH aired",
              all(a in atoms for a in shared[0]), str(shared[0]))
        check("F: every aired row names its atom", all(x.get("atom") for x in rs if x.get("aired")))
        r8 = read(d, cfg, client, 8)
        rs = rows(d, cfg)
        check("C: the 8th turn wraps to the least recently aired — the title page again",
              [x.get("atom") for x in rs if x.get("aired")][-1] == want[0],
              str([x.get("atom") for x in rs if x.get("aired")][-1]))

        print("\n  ── D · a row from before `atom` existed ──")
        k, d, cfg = cell()
        client = _W.client_of(cfg)
        for a, n in hostile.items():
            d("admin", "kernel.identity.alias", {"id": a, "name": n})
        key_to_atom.clear()
        _bs2 = BS.BenchStationConcept(k.manager.get_session(client))
        key_to_atom.update({_bs2._key(a): a for a in want})
        first_anchor = " · ".join(str(x) for x in [passages[0].get("book"), passages[0].get("section"),
                                                    "p.%s" % passages[0]["anchor"]["page"]])
        shared_anchor = [a for a, v in anchors.items() if len(v) > 1][0]
        record(k, cfg, source=first_anchor, turn="legacy-1")             # unique anchor, no atom
        record(k, cfg, source=shared_anchor, turn="legacy-2")            # shared anchor, no atom
        r = read(d, cfg, client, 1)
        check("D: the unique-anchor legacy row consumed its passage (the title page) and the shared-anchor "
              "legacy row consumed NOTHING — the next passage is the imprint",
              (r.get("source") or "").endswith("t.p. verso]") or "Imprint" in str(r.get("source")),
              str(r.get("source")))
        rest = [x.get("atom") for x in rows(d, cfg) if x.get("aired") and x.get("atom")]
        for n in range(2, 8):
            read(d, cfg, client, n)
        rest = [x.get("atom") for x in rows(d, cfg) if x.get("aired") and x.get("atom")]
        check("D: and both shared-anchor passages still air", all(a in rest for a in shared[0]),
              str([a.split(":")[-1] for a in rest]))

        print("\n  ── E · `seq` and natural order ──")
        order = BS.BenchStationConcept._episode_order
        mk = lambda atom, seq=None: {"atom": atom, "seq": seq, "_json": True}
        check("a passage that declares `seq` goes by it, whatever its name",
              sorted([mk("x:b", 1), mk("x:a", 2), mk("x:c", 3)], key=order)[0]["atom"] == "x:b")
        check("without `seq`, numbers sort NATURALLY (ep1-2 before ep1-10)",
              [e["atom"] for e in sorted([mk("ep1-10"), mk("ep1-2"), mk("ep1-1")], key=order)]
              == ["ep1-1", "ep1-2", "ep1-10"])
        check("a plain-text item (news, gallery) keeps its alias order",
              [e["atom"] for e in sorted([{"atom": "n:2026-09-27:010"}, {"atom": "n:2026-09-27:002"}],
                                         key=order)] == ["n:2026-09-27:002", "n:2026-09-27:010"])
    finally:
        llm_provider.generate = real_gen
        try:
            BS.BenchStationConcept._alias = real_alias
        except NameError:
            pass

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the reading room reads the pack's own order whatever aliases the store lists "
          "first, keeps its place by ATOM so two passages that share an anchor both air, wraps to the "
          "least recently read, counts a legacy anchor-only row only when it names one passage, and "
          "honours a declared `seq`.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
