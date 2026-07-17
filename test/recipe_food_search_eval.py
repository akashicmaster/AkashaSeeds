#!/usr/bin/env python3
"""
Recipe food-search eval — the ingredient picker the app needs.

Food atoms carry category-namespaced keys (`food:<category>:<slug>`) and an
`food:fdc:<id>` alias, and live in the shared nucleus catalogue (loaded universal),
while a user's private foods live in their own cortex. `recipe.food.search` bridges
name → id: it scans BOTH, matches the query tokens against the food NAME aliases, and
returns each hit's `fdc` + per-basis nutrition so the client can pin the ingredient.

  FS1 catalogue   — search the shared catalogue by name → the right food + its fdc +
                    parsed per-basis nutrition (loaded the way the .ak loader does:
                    a "… — per 100g: N kcal, …" content string in the nucleus).
  FS2 pin→resolve — feeding a search result's fdc into recipe.add makes recipe.nutrition
                    resolve exactly (the name→id→nutrition round trip).
  FS3 personal    — a user's own recipe.food.personal food is found by search too,
                    marked scope=personal, merged with the shared catalogue.
  FS4 paginate    — a broad query respects limit/max and returns count/has_more.
  FS5 guest read  — search is READ-level: a guest (no login) can browse foods.

Run:  python test/recipe_food_search_eval.py
"""
import os
import sys
import re
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"
os.environ["AKASHA_ALLOW_SELF_REGISTER"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def _load_real_foods_into_nucleus(session, limit=400):
    """Emulate the .ak loader for a slice of the REAL base food ontology, writing into
    the shared nucleus (universal scope) exactly as a `scope=universal` boot load does."""
    from lib.akasha.jcl.workspace_context import system_context
    nuc = session.nucleus
    defs, als = {}, []
    path = "ontology/base1/food_foundation.ak"
    if not os.path.exists(path):
        return 0
    for line in open(path, encoding="utf-8"):
        m = re.match(r'^def "([^"]+)" "(.*)"\s*$', line)
        if m:
            defs[m.group(1)] = m.group(2)
        a = re.match(r'^al (\S+) (\S+)\s*$', line)
        if a:
            als.append((a.group(1), a.group(2)))
    picked = [k for k in defs if k.startswith("food:") and "per 100g" in defs[k]][:limit]
    keymap = {}
    with system_context():
        for kk in picked:
            key = nuc.put_atom(defs[kk], {"type": "atom", "role": "food"},
                               author="system.librarian")
            nuc.set_alias(key, kk)
            keymap[kk] = key
        for src, dst in als:
            if src in keymap and dst.startswith("food:fdc:"):
                nuc.set_alias(keymap[src], dst)
    return len(picked)


def main():
    print("\n  recipe food-search eval — the ingredient picker (name → fdc → nutrition)\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_fsearch_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    admin_session = k.manager.get_session("admin")
    n = _load_real_foods_into_nucleus(admin_session)
    print(f"  (loaded {n} real base foods into the shared nucleus)\n")

    def net(method, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": method, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # FS1 — search the shared catalogue by name.
    r = net("recipe.food.search", atok, q="hummus")["result"]
    hummus = next((x for x in r["results"] if "hummus" in x["name"].lower()), None)
    fs1 = (hummus is not None and hummus["fdc"] == "321358"
           and abs((hummus["per_basis"] or {}).get("kcal", 0) - 229.0) < 0.5
           and hummus["scope"] == "catalog")
    record("FS1 catalogue", fs1,
           f"name={hummus and hummus['name']!r} fdc={hummus and hummus['fdc']} "
           f"kcal={hummus and hummus['per_basis'].get('kcal')}")

    # FS2 — feed the picked fdc into recipe.add → nutrition resolves exactly.
    rid = net("recipe.new", atok, title="Picker Test")["result"]["recipe_id"]
    net("recipe.add", atok, recipe=rid, ingredient="hummus", qty="200", unit="g",
        fdc=(hummus or {}).get("fdc", ""))
    nut = net("recipe.nutrition", atok, recipe=rid)["result"]
    fs2 = (abs(nut["totals"].get("kcal", 0) - 458.0) < 1.0 and nut["measured"] == 1)  # 229×2
    record("FS2 pin→resolve", fs2,
           f"kcal={nut['totals'].get('kcal')} measured={nut['measured']}")

    # FS3 — a private food is found too, marked personal.
    net("recipe.food.personal", atok, name="my special granola", kcal="480", protein_g="11")
    r3 = net("recipe.food.search", atok, q="granola")["result"]
    mine = next((x for x in r3["results"] if "granola" in x["name"].lower()), None)
    fs3 = (mine is not None and mine["scope"] == "personal"
           and abs((mine["per_basis"] or {}).get("kcal", 0) - 480.0) < 0.5)
    record("FS3 personal", fs3, f"found={mine is not None} scope={mine and mine['scope']}")

    # FS4 — pagination on a broad query.
    r4 = net("recipe.food.search", atok, q="beef", limit="5")["result"]
    fs4 = (len(r4["results"]) <= 5 and r4["count"] >= 1
           and (r4["has_more"] == (r4["count"] > 5)))
    record("FS4 paginate", fs4,
           f"page={len(r4['results'])} count={r4['count']} has_more={r4['has_more']}")

    # FS5 — guest (no login) can search (READ-level).
    g = net("session.guest.create")
    gtok = (g.get("result") or {}).get("binding_key") or (g.get("result") or {}).get("session_token")
    r5 = net("recipe.food.search", gtok, q="hummus")
    fs5 = ("result" in r5 and isinstance(r5["result"].get("results"), list)
           and len(r5["result"]["results"]) >= 1)
    record("FS5 guest read", fs5,
           f"guest_results={len(r5.get('result', {}).get('results', [])) if 'result' in r5 else r5.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
