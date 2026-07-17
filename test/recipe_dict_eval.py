#!/usr/bin/env python3
"""
Recipe food-app eval — the reference/dictionary surface the iOS client depends on.

Covers the app's food-information features and the client-facing contract additions:

  D1 method.list  — the cooking-method catalogue {methods:[{name,label}]} (name=save key).
  D2 tool.list    — the cooking-tool catalogue; a tool created by a step surfaces here.
  D3 food.lookup  — dictionary read of one food (nutrition + linked allergens/season);
                    an ambiguous name returns {found:false, candidates:[…]}.
  B2 food pin     — the dictionary id is accepted on recipe.add via food= AND via fdc=
                    (client compat: fdc=food:<slug>) — nutrition then resolves exactly.
  B1 step tools   — recipe.step tools=/temp= are stored and recipe.view steps[] return
                    tools/temp/dur_min.
  A4 publish      — free plan → {locked, upgrade_required}; paid → published + public feed.
  C1 mine         — ls/view carry mine:true for the owner, false for another user's.
  C2 hint_items   — view.hint_items carry item ids for per-memo delete.
  DD contract     — suggest.matched uses axis=value/have=food; a locked read returns
                    {locked:true} not an error; unknown method → -32601.

Run:  python test/recipe_dict_eval.py
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


def _seed_catalogue(session):
    """Load the method vocab + a couple of real foods (with a linked allergen) into the
    shared nucleus, the way a `scope=universal` ontology load does."""
    from lib.akasha.jcl.workspace_context import system_context
    nuc = session.nucleus
    with system_context():
        # cooking methods: a couple curated method:<slug> + the ontology's technique:<slug>.
        for slug, desc in [("simmer", "Cook gently in liquid.")]:
            mk = nuc.put_atom(desc, {"type": "atom"}, author="system.librarian")
            nuc.set_alias(mk, f"method:{slug}"); nuc.set_alias(mk, slug)
        for slug, desc in [("baking", "baking"), ("steaming", "steaming"), ("al_dente", "al dente")]:
            tk = nuc.put_atom(desc, {"type": "atom"}, author="system.librarian")
            nuc.set_alias(tk, f"technique:{slug}")
        # allergen namespace (the real ontology shape) + the ingredient concept it hangs on.
        peanut_alg = nuc.put_atom("Peanut allergen.", {"type": "atom"}, author="system.librarian")
        nuc.set_alias(peanut_alg, "allergen:peanut")
        peanut_ing = nuc.put_atom("peanut", {"type": "atom"}, author="system.librarian")
        nuc.set_alias(peanut_ing, "ingred:legume:peanut")
        nuc.put_link(peanut_ing, peanut_alg, "bio:allergen")       # ingred → allergen (real shape)
        # two real-shaped foods (content string carries per-100g nutrition)
        dk = nuc.put_atom("Radish, daikon, raw — per 100g: 18 kcal, Protein 0.6g, Carbohydrate 4.1g",
                          {"type": "atom", "role": "food"}, author="system.librarian")
        nuc.set_alias(dk, "food:vegetable:radish_daikon_raw")
        nuc.set_alias(dk, "food:daikon")
        nuc.set_alias(dk, "food:fdc:11429")
        pb = nuc.put_atom("Peanut butter, smooth — per 100g: 588 kcal, Protein 25.1g, Fat 50.4g",
                          {"type": "atom", "role": "food"}, author="system.librarian")
        nuc.set_alias(pb, "food:legume:peanut_butter_smooth")
        nuc.set_alias(pb, "food:peanut_butter")
        # food → ingredient concept (bridge); allergen is reached food → ingred → allergen.
        nuc.put_link(pb, peanut_ing, "thesaurus:related")


def main():
    print("\n  recipe food-app eval — dictionary + catalogues + client contract\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_dict_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")
    _seed_catalogue(k.manager.get_session("admin"))

    def net(method, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": method, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]
    net("user.add", atok, data={"client_id": "bob", "passphrase_hash": hashlib.sha256(b"x").hexdigest()})
    btok = net("auth.verify", user_id="bob", passphrase="x")["result"]["session_token"]

    # D1 — method catalogue unions curated method:* with the ontology technique:* vocab.
    ml = net("recipe.method.list", atok)["result"]
    names = {m["name"] for m in ml["methods"]}
    d1 = ({"simmer", "baking", "steaming", "al_dente"} <= names
          and all("label" in m for m in ml["methods"]))
    record("D1 method.list", d1, f"methods={sorted(names)}")

    # B1 + D2 — a step with tools=/temp=; the tool then appears in tool.list; view returns them.
    rid = net("recipe.new", atok, title="Roast Veg")["result"]["recipe_id"]
    net("recipe.step", atok, recipe=rid, text="roast the daikon", tools="oven,tray",
        temp="200", dur="40")
    card = net("recipe.view", atok, recipe=rid)["result"]
    s0 = card["steps"][0]
    b1 = (s0.get("temp") == 200.0 and s0.get("dur_min") == 40.0
          and set(s0.get("tools", [])) == {"oven", "tray"})
    record("B1 step tools/temp", b1, f"temp={s0.get('temp')} dur={s0.get('dur_min')} tools={s0.get('tools')}")
    tl = net("recipe.tool.list", atok)["result"]
    d2 = {t["name"] for t in tl["tools"]} >= {"oven", "tray"}
    record("D2 tool.list", d2, f"tools={sorted(t['name'] for t in tl['tools'])}")

    # D3 — dictionary lookup (exact + allergen link) and the ambiguous → candidates path.
    lk = net("recipe.food.lookup", atok, name="peanut butter")["result"]
    d3a = (lk.get("found") and abs(lk["nutrition"].get("kcal", 0) - 588.0) < 0.5
           and "peanut" in lk.get("allergens", []))
    amb = net("recipe.food.lookup", atok, name="radish")["result"]   # no exact food:radish
    d3b = (amb.get("found") is False and isinstance(amb.get("candidates"), list))
    record("D3 food.lookup", d3a and d3b,
           f"pb_kcal={lk.get('nutrition',{}).get('kcal')} allergens={lk.get('allergens')} "
           f"ambiguous_candidates={len(amb.get('candidates', []))}")

    # B2 — pin the dictionary id: via food= AND via the legacy fdc=food:<slug> (client compat).
    net("recipe.add", atok, recipe=rid, ingredient="daikon", qty="200", unit="g", food="food:daikon")
    r2 = net("recipe.new", atok, title="Compat Test")["result"]["recipe_id"]
    net("recipe.add", atok, recipe=r2, ingredient="daikon", qty="100", unit="g", fdc="food:daikon")
    n1 = net("recipe.nutrition", atok, recipe=rid)["result"]["totals"].get("kcal", 0)   # 18×2
    n2 = net("recipe.nutrition", atok, recipe=r2)["result"]["totals"].get("kcal", 0)    # 18×1
    b2 = (abs(n1 - 36.0) < 0.5 and abs(n2 - 18.0) < 0.5)
    record("B2 food pin (food=/fdc=)", b2, f"food=→{n1}kcal fdc=food:daikon→{n2}kcal")

    # C1 — mine flag (owner vs other).
    v_mine = net("recipe.view", atok, recipe=rid)["result"]["mine"]
    v_other = net("recipe.view", btok, recipe=rid)          # bob viewing admin's recipe
    # bob may not see admin's private recipe at all; if he can, mine must be False
    c1 = (v_mine is True and ("error" in v_other or v_other.get("result", {}).get("mine") is False))
    record("C1 mine flag", c1,
           f"owner_mine={v_mine} other={'denied' if 'error' in v_other else v_other.get('result',{}).get('mine')}")

    # C2 — hint_items carry ids for per-memo delete.
    net("recipe.add", atok, recipe=rid, hint="don't over-salt")
    hi = net("recipe.view", atok, recipe=rid)["result"]["hint_items"]
    c2 = (len(hi) == 1 and hi[0].get("item_id") and hi[0]["text"] == "don't over-salt")
    record("C2 hint_items", c2, f"hint_items={hi}")

    # A4 — publish: free (bob, tiering on) locked; admin/paid publishes to the feed.
    os.environ["AKASHA_RECIPE_TIERING"] = "1"
    brid = net("recipe.new", btok, title="Bob Dish")["result"]["recipe_id"]
    bfree = net("recipe.publish", btok, recipe=brid)["result"]
    os.environ["AKASHA_RECIPE_TIERING"] = "0"          # admin path unmetered
    pub = net("recipe.publish", atok, recipe=rid)["result"]
    published_flag = net("recipe.view", atok, recipe=rid)["result"]["published"]
    a4 = (bfree.get("locked") is True and bfree.get("reason") == "upgrade_required"
          and pub.get("status") == "published" and published_flag is True)
    record("A4 publish", a4, f"free_locked={bfree.get('locked')} published={pub.get('status')}")

    # DD — client-contract invariants (D-1/D-2/D-4 from the brief).
    sug = net("recipe.suggest", atok, season="winter", have="daikon")["result"]
    matched_ok = all(re.match(r"^(have=|[a-z]+=)", m)
                     for s in sug["suggestions"] for m in s.get("matched", [])) \
        if sug["suggestions"] else True
    os.environ["AKASHA_RECIPE_TIERING"] = "1"
    locked_read = net("recipe.nutrition", btok, recipe=brid)["result"]
    os.environ["AKASHA_RECIPE_TIERING"] = "0"
    locked_ok = (locked_read.get("locked") is True)          # a lock is a result, not an error
    unknown = net("recipe.does_not_exist", atok)
    unknown_ok = (unknown.get("error", {}).get("code") == -32601)
    dd = matched_ok and locked_ok and unknown_ok
    record("DD contract", dd,
           f"matched_fmt={matched_ok} locked_is_result={locked_ok} unknown={unknown.get('error',{}).get('code')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
