#!/usr/bin/env python3
"""
WineConcept eval — the tasting-side wine dictionary (Step 2).

Wine is a reference dictionary over the ontology's `wine:*` entities (loaded universal in
the thesaurus tier), not a formula: WineConcept reads the live graph — colour via
sys:part_of, origin via wine:originated_in, cheese pairings via pairing:* — and exposes
clear read operators. This eval loads a small wine/cheese slice into the shared nucleus
(as the thesaurus wine pack does) and drives the operators as an authed user AND a guest.

  WN1 search    — wine.search finds a varietal by name.
  WN2 ls color  — wine.ls color=red returns the reds, not the white.
  WN3 ls region — wine.ls region=piedmont returns the wine originated there.
  WN4 get       — wine.get resolves colour + origin + tasting note + cheese pairing.
  WN5 pairs     — wine.pairs returns the paired cheese (tasting-side stance).
  WN6 guest     — every wine.* op is READ-level: a guest (no login) can browse.

Run:  python test/wine_eval.py
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


# A tiny slice mirroring ontology/wine/: colours, regions, two varietals, a cheese, a pairing.
_DEFS = {
    "wine:color:red":   "Red wine colour classification.",
    "wine:color:white": "White wine colour classification.",
    "wine:region:piedmont": "Piedmont — NW Italy; Barolo & Barbaresco.",
    "wine:region:burgundy": "Burgundy — France; Pinot Noir & Chardonnay.",
    "wine:varietal:nebbiolo": ("Noble red grape of Piedmont. Barolo and Barbaresco. High "
                               "tannin, high acid. Cherry, rose, tar, truffle."),
    "wine:varietal:chardonnay": ("The great white grape of Burgundy. Apple, citrus, "
                                 "hazelnut; oak-friendly."),
    "cheese:castelmagno": "Castelmagno — a Piedmontese cow's-milk cheese, semi-hard, tangy.",
}
_LINKS = [
    ("wine:varietal:nebbiolo",   "wine:color:red",       "sys:part_of"),
    ("wine:varietal:chardonnay", "wine:color:white",     "sys:part_of"),
    ("wine:varietal:nebbiolo",   "wine:region:piedmont", "wine:originated_in"),
    ("wine:varietal:chardonnay", "wine:region:burgundy", "wine:originated_in"),
    ("wine:varietal:nebbiolo",   "cheese:castelmagno",   "pairing:regional_pairing"),
]


def main():
    print("\n  WineConcept eval — tasting-side wine dictionary\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_wine_"))
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

    # WN1 — search by name.
    r = net("wine.search", atok, q="nebbiolo").get("result") or {}
    names = [x["name"] for x in r.get("results", [])]
    record("WN1 search", any("nebbiolo" in n.lower() for n in names), f"results={names}")

    # WN2 — browse reds.
    r = net("wine.ls", atok, color="red").get("result") or {}
    reds = {x["name"] for x in r.get("results", [])}
    record("WN2 ls color", "nebbiolo" in reds and "chardonnay" not in reds, f"reds={sorted(reds)}")

    # WN3 — browse by origin.
    r = net("wine.ls", atok, region="piedmont").get("result") or {}
    pied = {x["name"] for x in r.get("results", [])}
    record("WN3 ls region", pied == {"nebbiolo"}, f"piedmont={sorted(pied)}")

    # WN4 — profile with colour/origin/note + pairing.
    r = net("wine.get", atok, id="wine:varietal:nebbiolo").get("result") or {}
    pair_names = {p["name"] for p in r.get("pairings", [])}
    wn4 = (r.get("color") == "red" and r.get("region") == "piedmont"
           and bool(r.get("note")) and "cheese:castelmagno" in pair_names)
    record("WN4 get", wn4,
           f"color={r.get('color')} region={r.get('region')} pairings={sorted(pair_names)}")

    # WN5 — pairs (tasting-side stance) → the cheese.
    r = net("wine.pairs", atok, id="wine:varietal:nebbiolo", target="cheese").get("result") or {}
    pnames = {p["name"] for p in r.get("pairings", [])}
    record("WN5 pairs", pnames == {"cheese:castelmagno"}, f"pairs={sorted(pnames)}")

    # WN6 — guest READ access.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("wine.get", gtok, id="wine:varietal:nebbiolo")
    wn6 = ("result" in rg and rg["result"].get("color") == "red")
    record("WN6 guest", wn6,
           f"guest_color={(rg.get('result') or {}).get('color') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
