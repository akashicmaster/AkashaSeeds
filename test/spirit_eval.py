#!/usr/bin/env python3
"""
SpiritConcept eval — the unified spirits dictionary (drinks_c: whiskey / rum / tequila).

Spirits arrive in three sibling namespaces (whiskey:/rum:/tequila:) that share one schema:
a flat entity, a `<type>:<type>` hub, an origin-country membership SET `<type>:from:<country>`,
and a sparse `<type>:made_by` producer link. SpiritConcept folds all three into one dictionary
with a `type` axis (DictionaryConcept's multi-namespace mode). This eval loads a small slice
into the shared nucleus and drives the operators as an authed user AND a guest.

  SP1 search    — spirit.search finds a spirit by name across namespaces.
  SP2 ls type   — spirit.ls type=whiskey returns whiskies, not the rum (the type=namespace axis).
  SP3 ls country— spirit.ls country=scotland returns the Scottish spirit (SET axis, unioned).
  SP4 intersect — type=whiskey country=scotland returns just the Scotch.
  SP5 get       — spirit.get resolves spirit_type + producer.
  SP6 exclude   — the namespace hubs (whiskey:whiskey/…) are not listed as spirits.
  SP7 guest     — READ-level: a guest (no login) can browse.

Run:  python test/spirit_eval.py
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


# Real entities are <type>:<form>:<slug> (form = distillery | brand).
_DEFS = {
    "whiskey:whiskey": "Whisky — grain spirit, cask-aged.",
    "rum:rum": "Rum — spirit distilled from sugarcane.",
    "tequila:tequila": "Tequila — agave spirit from Mexico.",
    "whiskey:brand:lagavulin_16": "Lagavulin 16 — an Islay single malt Scotch whisky.",
    "whiskey:brand:yamazaki_12": "Yamazaki 12 — a Japanese single malt whisky.",
    "rum:brand:appleton_estate": "Appleton Estate — a Jamaican rum.",
    "producer:diageo": "Diageo — a drinks producer.",
}
_ISA = [
    ("whiskey:brand:lagavulin_16", "whiskey:whiskey"),
    ("whiskey:brand:yamazaki_12", "whiskey:whiskey"),
    ("rum:brand:appleton_estate", "rum:rum"),
]
_MADEBY = [("whiskey:brand:lagavulin_16", "producer:diageo", "whiskey:made_by")]
_SETS = [
    ("whiskey:from:scotland", "whiskey:brand:lagavulin_16"),
    ("whiskey:from:japan", "whiskey:brand:yamazaki_12"),
    ("rum:from:jamaica", "rum:brand:appleton_estate"),
]


def main():
    print("\n  SpiritConcept eval — unified whiskey/rum/tequila dictionary\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_spirit_"))
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
    for s, d, rel in _MADEBY:
        loc("ln", src=s, dst=d, rel=rel, scope="universal")
    for setname, member in _SETS:
        loc("set.add", name=setname, id=member, scope="universal")

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # SP1 — search across namespaces.
    r = net("spirit.search", atok, q="appleton").get("result") or {}
    names = [x["name"] for x in r.get("results", [])]
    record("SP1 search", any("appleton" in n.lower() for n in names), f"results={names}")

    # SP2 — browse by type (the namespace).
    r = net("spirit.ls", atok, type="whiskey").get("result") or {}
    wh = {x["name"] for x in r.get("results", [])}
    record("SP2 ls type", wh == {"lagavulin 16", "yamazaki 12"}, f"whiskey={sorted(wh)}")

    # SP3 — browse by country (SET axis, unioned across namespaces).
    r = net("spirit.ls", atok, country="scotland").get("result") or {}
    sc = {x["name"] for x in r.get("results", [])}
    record("SP3 ls country", sc == {"lagavulin 16"}, f"scotland={sorted(sc)}")

    # SP4 — intersect type and country.
    r = net("spirit.ls", atok, type="whiskey", country="japan").get("result") or {}
    jp = {x["name"] for x in r.get("results", [])}
    record("SP4 intersect", jp == {"yamazaki 12"}, f"whiskey∩japan={sorted(jp)}")

    # SP5 — profile with type + producer.
    r = net("spirit.get", atok, id="whiskey:brand:lagavulin_16").get("result") or {}
    record("SP5 get", r.get("spirit_type") == "whiskey" and r.get("form") == "brand"
           and r.get("producer") == ["diageo"],
           f"spirit_type={r.get('spirit_type')} form={r.get('form')} producer={r.get('producer')}")

    # SP6 — the namespace hubs are not entities.
    r = net("spirit.search", atok, q="").get("result") or {}
    allnames = {x["name"] for x in r.get("results", [])}
    record("SP6 exclude", allnames == {"lagavulin 16", "yamazaki 12", "appleton estate"},
           f"entities={sorted(allnames)}")

    # SP7 — guest READ.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("spirit.get", gtok, id="rum:brand:appleton_estate")
    record("SP7 guest", "result" in rg and rg["result"].get("spirit_type") == "rum",
           f"guest_type={(rg.get('result') or {}).get('spirit_type') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
