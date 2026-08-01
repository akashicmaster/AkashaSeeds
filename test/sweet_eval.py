#!/usr/bin/env python3
"""
SweetConcept eval — the confectionery / お菓子 dictionary (sweets_bread_c, Wikidata).

Same family shape as small plates: dish:* items singled out by sweet:all, each sys:is_a one or
more sub-types (dish:cake / dish:cookie … sys:is_a dish:sweet), per-type set sweet:<type>, P495
country, P2012 cuisine, P186 ingredient. Loads a small slice into the shared nucleus and drives
the operators as an authed user AND a guest.

  SW1 search    — sweet.search finds a sweet by name.
  SW2 ls type   — sweet.ls type=cake returns the cakes, not the cookie (the sweet:<type> set axis).
  SW3 ls country— sweet.ls country=france returns the French sweets (dish:from set axis).
  SW4 intersect — type=cake cuisine=french intersects the axes.
  SW5 get       — sweet.get resolves sub-type(s) + cuisines + ingredients.
  SW6 exclude   — the umbrella (dish:sweet) and sub-type concepts are not items; breads are not.
  SW7 guest     — READ-level: a guest can browse.

Run:  python test/sweet_eval.py
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
    "dish:sweet": "Sweet — the confectionery umbrella (お菓子).",
    "dish:cake": "Cake — a baked sweet.", "dish:cookie": "Cookie — a small baked sweet.",
    "cuisine:french": "French cuisine.", "cuisine:italian": "Italian cuisine.",
    "ingred:dairy:butter": "Butter — a dairy fat.",
    "dish:opera_cake": "Opéra — a French almond sponge cake with coffee and chocolate.",
    "dish:madeleine": "Madeleine — a small French shell-shaped cake.",
    "dish:amaretti": "Amaretti — an Italian almond cookie.",
    "dish:baguette": "Baguette — a French bread (NOT a sweet).",
}
_ISA = [
    ("dish:cake", "dish:sweet"), ("dish:cookie", "dish:sweet"),
    ("dish:opera_cake", "dish:cake"), ("dish:madeleine", "dish:cake"),
    ("dish:amaretti", "dish:cookie"),
]
_REL = [
    ("dish:opera_cake", "cuisine:french", "thesaurus:related"),
    ("dish:opera_cake", "ingred:dairy:butter", "thesaurus:related"),
    ("dish:madeleine", "cuisine:french", "thesaurus:related"),
    ("dish:amaretti", "cuisine:italian", "thesaurus:related"),
]
_SETS = [
    ("sweet:all", "dish:opera_cake"), ("sweet:all", "dish:madeleine"), ("sweet:all", "dish:amaretti"),
    ("sweet:cake", "dish:opera_cake"), ("sweet:cake", "dish:madeleine"),
    ("sweet:cookie", "dish:amaretti"),
    ("dish:from:france", "dish:opera_cake"), ("dish:from:france", "dish:madeleine"),
    ("dish:from:italy", "dish:amaretti"),
]


def main():
    print("\n  SweetConcept eval — confectionery / お菓子 dictionary\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_sweet_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for a, d in _DEFS.items():
        loc("def", name=a, description=d, scope="universal")
    for s, d in _ISA:
        loc("ln", src=s, dst=d, rel="sys:is_a", scope="universal")
    for s, d, rel in _REL:
        loc("ln", src=s, dst=d, rel=rel, scope="universal")
    for setname, member in _SETS:
        loc("set.add", name=setname, id=member, scope="universal")

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    r = net("sweet.search", atok, q="madeleine").get("result") or {}
    record("SW1 search", any("madeleine" in x["name"].lower() for x in r.get("results", [])),
           f"n={r.get('count')}")

    cakes = {x["name"] for x in (net("sweet.ls", atok, type="cake").get("result") or {}).get("results", [])}
    record("SW2 ls type", cakes == {"opera cake", "madeleine"}, f"cakes={sorted(cakes)}")

    fr = {x["name"] for x in (net("sweet.ls", atok, country="france").get("result") or {}).get("results", [])}
    record("SW3 ls country", fr == {"opera cake", "madeleine"}, f"france={sorted(fr)}")

    both = {x["name"] for x in (net("sweet.ls", atok, type="cake", cuisine="french").get("result") or {}).get("results", [])}
    record("SW4 intersect", both == {"opera cake", "madeleine"}, f"cake∩french={sorted(both)}")

    r = net("sweet.get", atok, id="dish:opera_cake").get("result") or {}
    record("SW5 get", r.get("types") == ["cake"] and r.get("cuisines") == ["french"]
           and r.get("ingredients") == ["dairy:butter"],
           f"types={r.get('types')} cuisines={r.get('cuisines')} ingredients={r.get('ingredients')}")

    alln = {x["name"] for x in (net("sweet.search", atok, q="").get("result") or {}).get("results", [])}
    record("SW6 exclude", alln == {"opera cake", "madeleine", "amaretti"}, f"items={sorted(alln)}")

    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("sweet.get", gtok, id="dish:amaretti")
    record("SW7 guest", "result" in rg and rg["result"].get("types") == ["cookie"],
           f"guest_types={(rg.get('result') or {}).get('types') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
