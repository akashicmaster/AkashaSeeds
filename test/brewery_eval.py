#!/usr/bin/env python3
"""
BreweryConcept eval — the Open Brewery DB dictionary (drinks_c, C-tier).

Breweries are `brewery:<slug>` atoms with a type (a typed link: sys:is_a → brewery:type:*) and a
country (a MEMBERSHIP SET: brewery:in:<country>). BreweryConcept is a dictionary that reads both —
exercising DictionaryConcept's new SET_AXIS support for the set-based country axis. This eval
loads a small slice into the shared nucleus and drives the operators as an authed user AND a guest.

  BR1 search    — brewery.search finds a brewery by name.
  BR2 ls type   — brewery.ls type=micro returns the micros, not the brewpub (typed-link axis).
  BR3 ls country— brewery.ls country=japan returns the Japanese brewery (SET axis).
  BR4 intersect — type=micro country=germany returns just the German micro.
  BR5 get       — brewery.get resolves brewery_type + description.
  BR6 exclude   — the namespace hub (brewery:brewery) is not listed as a brewery.
  BR7 guest     — READ-level: a guest (no login) can browse.

Run:  python test/brewery_eval.py
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


_DEFS = {
    "brewery:brewery": "A brewery — a facility that makes beer.",
    "brewery:type:micro": "Micro — a small craft brewery.",
    "brewery:type:brewpub": "Brewpub — a pub that brews on-site.",
    "brewery:testa": "Testa — micro brewery in Munich, Bayern, Germany. http://testa.example",
    "brewery:testb": "Testb — brewpub in Portland, Oregon, United States.",
    "brewery:testc": "Testc — micro brewery in Kyoto, Japan.",
}
_ISA = [
    ("brewery:type:micro", "brewery:brewery"), ("brewery:type:brewpub", "brewery:brewery"),
    ("brewery:testa", "brewery:type:micro"), ("brewery:testb", "brewery:type:brewpub"),
    ("brewery:testc", "brewery:type:micro"),
]
_SETS = [
    ("breweries", "brewery:testa"), ("breweries", "brewery:testb"), ("breweries", "brewery:testc"),
    ("brewery:in:germany", "brewery:testa"),
    ("brewery:in:united_states", "brewery:testb"),
    ("brewery:in:japan", "brewery:testc"),
]


def main():
    print("\n  BreweryConcept eval — Open Brewery DB dictionary\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_brew_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for alias, desc in _DEFS.items():
        loc("def", name=alias, description=desc, scope="universal")
    for s, d in _ISA:
        loc("ln", src=s, dst=d, rel="sys:is_a", scope="universal")
    for setname, member in _SETS:
        loc("set.add", name=setname, id=member, scope="universal")

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # BR1 — search.
    r = net("brewery.search", atok, q="testa").get("result") or {}
    names = [x["name"] for x in r.get("results", [])]
    record("BR1 search", any("testa" in n.lower() for n in names), f"results={names}")

    # BR2 — browse by type (typed link).
    r = net("brewery.ls", atok, type="micro").get("result") or {}
    micro = {x["name"] for x in r.get("results", [])}
    record("BR2 ls type", micro == {"testa", "testc"}, f"micro={sorted(micro)}")

    # BR3 — browse by country (SET axis).
    r = net("brewery.ls", atok, country="japan").get("result") or {}
    jp = {x["name"] for x in r.get("results", [])}
    record("BR3 ls country", jp == {"testc"}, f"japan={sorted(jp)}")

    # BR4 — intersect a link axis and a set axis.
    r = net("brewery.ls", atok, type="micro", country="germany").get("result") or {}
    de = {x["name"] for x in r.get("results", [])}
    record("BR4 intersect", de == {"testa"}, f"micro∩germany={sorted(de)}")

    # BR5 — profile.
    r = net("brewery.get", atok, id="brewery:testa").get("result") or {}
    record("BR5 get", r.get("brewery_type") == "micro" and bool(r.get("note")),
           f"brewery_type={r.get('brewery_type')} note?={bool(r.get('note'))}")

    # BR6 — the namespace hub is not an entity.
    r = net("brewery.search", atok, q="").get("result") or {}
    allnames = {x["name"] for x in r.get("results", [])}
    record("BR6 exclude", allnames == {"testa", "testb", "testc"}, f"entities={sorted(allnames)}")

    # BR7 — guest READ.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("brewery.get", gtok, id="brewery:testc")
    record("BR7 guest", "result" in rg and rg["result"].get("brewery_type") == "micro",
           f"guest_type={(rg.get('result') or {}).get('brewery_type') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
