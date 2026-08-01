#!/usr/bin/env python3
"""
CheeseConcept eval — the pairing-side cheese dictionary (Step 3, the wine mirror).

Cheese is a reference dictionary over the ontology's `cheese:*` entities, read live from the
graph: milk via cheese:made_from, texture via sys:part_of → cheese:type:*, country via
cheese:origin_country → geo:country:*, and wine pairings via the wine↔cheese pairing:* edges
(seen from the cheese side, i.e. incoming). This eval loads a small cheese/wine slice into the
shared nucleus and drives the operators as an authed user AND a guest.

  CH1 search    — cheese.search finds a cheese by name.
  CH2 ls milk   — cheese.ls milk=sheep returns the sheep's-milk cheese, not the cow's.
  CH3 ls type   — cheese.ls type=blue returns the blue, not the hard.
  CH4 ls country— cheese.ls country=france returns the French cheeses.
  CH5 get       — cheese.get resolves milk + texture + country + note + wine pairing.
  CH6 pairs     — cheese.pairs defaults to target=wine → the paired wine (the app's standpoint).
  CH7 guest     — READ-level: a guest (no login) can browse.

Run:  python test/cheese_eval.py
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
    "cheese:milk:cow": "Cow's-milk classification.",
    "cheese:milk:sheep": "Sheep's-milk classification.",
    "cheese:type:blue": "Blue cheese texture family.",
    "cheese:type:hard": "Hard cheese texture family.",
    "geo:country:france": "France.",
    "cheese:roquefort": ("AOC blue cheese from Combalou caves, Aveyron. Sheep's milk. "
                         "Penicillium roqueforti veining, creamy, sharp, salty."),
    "cheese:comte": ("AOC hard cow's-milk cheese from Franche-Comte. Fruity, nutty, "
                     "complex; aged 4-24+ months."),
    "wine:region:sauternes": "Sauternes — sweet botrytised white, Bordeaux.",
}
_LINKS = [
    ("cheese:roquefort", "cheese:milk:sheep", "cheese:made_from"),
    ("cheese:comte",     "cheese:milk:cow",   "cheese:made_from"),
    ("cheese:roquefort", "cheese:type:blue",  "sys:part_of"),
    ("cheese:comte",     "cheese:type:hard",  "sys:part_of"),
    ("cheese:roquefort", "geo:country:france", "cheese:origin_country"),
    ("cheese:comte",     "geo:country:france", "cheese:origin_country"),
    # the pairing edge is authored wine -> cheese; cheese sees it incoming.
    ("wine:region:sauternes", "cheese:roquefort", "pairing:sweetness_with_saltiness"),
]


def main():
    print("\n  CheeseConcept eval — pairing-side cheese dictionary\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cheese_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for alias, desc in _DEFS.items():
        loc("def", name=alias, description=desc, scope="universal")
    for s, d, rel in _LINKS:
        loc("ln", src=s, dst=d, rel=rel, scope="universal")

    def net(method, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": method, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # CH1 — search.
    r = net("cheese.search", atok, q="roquefort").get("result") or {}
    names = [x["name"] for x in r.get("results", [])]
    record("CH1 search", any("roquefort" in n.lower() for n in names), f"results={names}")

    # CH2 — browse by milk.
    r = net("cheese.ls", atok, milk="sheep").get("result") or {}
    sheep = {x["name"] for x in r.get("results", [])}
    record("CH2 ls milk", "roquefort" in sheep and "comte" not in sheep, f"sheep={sorted(sheep)}")

    # CH3 — browse by texture.
    r = net("cheese.ls", atok, texture="blue").get("result") or {}
    blue = {x["name"] for x in r.get("results", [])}
    record("CH3 ls texture", blue == {"roquefort"}, f"blue={sorted(blue)}")

    # CH4 — browse by country.
    r = net("cheese.ls", atok, country="france").get("result") or {}
    fr = {x["name"] for x in r.get("results", [])}
    record("CH4 ls country", fr == {"roquefort", "comte"}, f"france={sorted(fr)}")

    # CH5 — profile with milk/texture/country/note + wine pairing.
    r = net("cheese.get", atok, id="cheese:roquefort").get("result") or {}
    pair_names = {p["name"] for p in r.get("pairings", [])}
    ch5 = (r.get("milk") == "sheep" and r.get("texture") == "blue" and r.get("country") == "france"
           and bool(r.get("note")) and "wine:region:sauternes" in pair_names)
    record("CH5 get", ch5,
           f"milk={r.get('milk')} texture={r.get('texture')} country={r.get('country')} "
           f"pairings={sorted(pair_names)}")

    # CH6 — pairs defaults to wine (the app's standpoint).
    r = net("cheese.pairs", atok, id="cheese:roquefort").get("result") or {}
    pnames = {p["name"] for p in r.get("pairings", [])}
    record("CH6 pairs", r.get("target") == "wine" and pnames == {"wine:region:sauternes"},
           f"target={r.get('target')} pairs={sorted(pnames)}")

    # CH7 — guest READ access.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("cheese.get", gtok, id="cheese:roquefort")
    ch7 = ("result" in rg and rg["result"].get("milk") == "sheep")
    record("CH7 guest", ch7,
           f"guest_milk={(rg.get('result') or {}).get('milk') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
