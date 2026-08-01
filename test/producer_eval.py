#!/usr/bin/env python3
"""
ProducerConcept eval — the drinks-producer dictionary (distilleries + breweries), the far side of
sys:made_by. Producers are NOT drinks: they live in producer:all, never in drink:all.

Seeds a slice (a spirit brand + its distillery via whiskey:made_by, a brewery), runs the canonical
normalizer as the ingestion hook does, then drives the operators.

  PR1 search   — producer.search finds a producer by name.
  PR2 ls kind  — producer.ls kind=distillery / brewery selects by kind.
  PR3 get makes— producer.get shows kind + the drinks it makes (incoming made_by).
  PR4 not drink— a producer is in producer:all, NOT drink:all; a drink brand is not a producer.
  PR5 guest    — READ-level: a guest can browse.

Run:  python test/producer_eval.py
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


def main():
    print("\n  ProducerConcept eval — distilleries + breweries (the made_by far side)\n")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology_normalize import OntologyNormalizer
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_producer_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for a, d in [("role:product", "product."), ("role:component", "component."),
                 ("role:method", "method."), ("role:producer", "producer."),
                 ("drink", "Drink."), ("spirit", "Spirit."), ("producer", "Producer."),
                 ("meal", "Meal."), ("ingredient", "Ingredient."), ("recipe", "Recipe."),
                 ("cocktail", "Cocktail."), ("wine", "Wine.")]:
        loc("def", name=a, description=d, scope="universal")
    for a, d in [("whiskey:brand:lagavulin_16", "Lagavulin 16 — an Islay single malt."),
                 ("whiskey:distillery:lagavulin", "Lagavulin distillery — an Islay distillery."),
                 ("brewery:guinness", "Guinness — a Dublin brewery.")]:
        loc("def", name=a, description=d, scope="universal")
    ln = [{"method": "kernel.memory.link",
           "params": {"src": "whiskey:brand:lagavulin_16", "dst": "whiskey:distillery:lagavulin",
                      "rel": "whiskey:made_by"}}]
    for s in ln:
        loc(s["method"], **s["params"])

    sess = k.manager.get_session("admin")
    cores = [getattr(sess.local_cortex, "core", None),
             getattr(getattr(sess, "nucleus", None), "core", None)]
    for s in OntologyNormalizer(cores).plan(link_steps=ln):
        loc(s["method"], **s["params"])
    cortex = sess.local_cortex

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # PR1 — search.
    r = net("producer.search", atok, q="lagavulin").get("result") or {}
    record("PR1 search", any("lagavulin" in x["name"].lower() for x in r.get("results", [])),
           f"n={r.get('count')}")

    # PR2 — browse by kind.
    di = {x["name"] for x in (net("producer.ls", atok, kind="distillery").get("result") or {}).get("results", [])}
    br = {x["name"] for x in (net("producer.ls", atok, kind="brewery").get("result") or {}).get("results", [])}
    record("PR2 ls kind", di == {"lagavulin"} and br == {"guinness"},
           f"distillery={sorted(di)} brewery={sorted(br)}")

    # PR3 — profile with kind + the drinks it makes.
    r = net("producer.get", atok, id="whiskey:distillery:lagavulin").get("result") or {}
    record("PR3 get makes", r.get("kind") == "distillery"
           and any("lagavulin_16" in x or "16" in x for x in (r.get("makes") or [])),
           f"kind={r.get('kind')} makes={r.get('makes')}")

    # PR4 — a producer is NOT a drink; a drink brand is NOT a producer.
    prod_all = set(cortex.get_collection_members("producer:all") or [])
    drink_all = set(cortex.get_collection_members("drink:all") or [])
    dist = cortex.resolve_alias("whiskey:distillery:lagavulin")
    brand = cortex.resolve_alias("whiskey:brand:lagavulin_16")
    record("PR4 not drink", dist in prod_all and dist not in drink_all
           and brand in drink_all and brand not in prod_all,
           f"distillery∈producer={dist in prod_all} distillery∈drink={dist in drink_all}")

    # PR5 — guest READ.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("producer.get", gtok, id="brewery:guinness")
    record("PR5 guest", "result" in rg and rg["result"].get("kind") == "brewery",
           f"guest_kind={(rg.get('result') or {}).get('kind') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
