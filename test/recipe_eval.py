#!/usr/bin/env python3
"""
Recipe eval — the cookable-structure concept model + axis-driven suggestion.

Recipe is a small structural universe (root + ingredients/methods/steps/hints/
constraints) whose dimensional axes (season/ethnic/course/scene, plus the
ingredients/methods/constraints it carries) are cross-recipe membership sets, so
`recipe.suggest` ranks recipes by weighted axis intersection — the composite
cross_query idea applied to a menu.

  R1 universe      — new + add(ingredient/method) + step build the graph; view
                     assembles the card with qty, ordered steps, and crossings.
  R2 step chain    — steps chain via sys:next and carry step×ingredient /
                     step×method crossings (uses= / by=).
  R3 suggest rank  — more matched axes ⇒ higher score; ordering is by coverage.
  R4 constraint    — avoid= is a HARD filter: a recipe that matches every other
                     axis is still removed if it uses/《constrains》an avoided term.
  R5 ls / axis     — recipe.ls filters by discrete axis (intersection).
  R6 idempotent    — recipe.new alias= re-uses the existing recipe (boot-safe).
  R7 nutrition     — recipe.food sets USDA nutrition; recipe.nutrition accumulates
                     (grams/basis)×nutrient over mass ingredients; a count-unit
                     ingredient is `unmeasured`, a food with no data is `no_data`.
  R8 kcal target   — constraint=kcal<=600 is a TARGET (not an allergen) checked
                     against the accumulated total (met / not-met), and it never
                     enters the allergen constraint list.
  R9 USDA content  — a food whose nutrition arrived as an ontology .ak CONTENT
                     string ("… — per 100g: 18 kcal, Protein 0.6g, …") — because
                     .ak def can't write meta — resolves by name alias and
                     accumulates identically to a recipe.food (structured) food.
  R10 fdc handle   — a food is reachable from EITHER alias: an ingredient pinned
                     with fdc=<id> resolves via food:fdc:<id> even when the cooking
                     name doesn't match the USDA descriptive name.
  R11 critical     — parallel cooking: steps with dur=/after= form a DAG, and
                     recipe.critical returns a makespan (parallel) below the naive
                     sequential total, with the correct zero-slack critical path.
  R12 haccp        — a cook-temperature CCP + a storage-temperature control; measuring
                     the actuals reports pass/safe, and an undercooked re-measurement
                     flips safe=False with the CCP flagged.
  R13 edit/safety  — the client-facing contract additions: idempotent add
                     (request_key), ingredient remove + update, a version/updated_at
                     on the card, the expected_updated_at optimistic-lock conflict,
                     and ls pagination (limit/cursor → next_cursor/has_more).

Run:  python test/recipe_eval.py
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def main():
    print("\n  recipe eval — cookable structure + axis-driven suggestion\n")
    from lib.akasha.kernel import KernelDispatcher
    from api.router import CommandRouter as R
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_rcp_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def run(cli):
        p = R.build_rpc_request(cli, "admin")
        if p is None:
            return {"error": {"message": "UNKNOWN_COMMAND", "cli": cli}}
        return k.dispatch(p, "local")

    def res(cli):
        r = run(cli)
        assert "error" not in r, f"{cli} -> {r.get('error')}"
        return r["result"]

    # ── Build recipe A: winter japanese daikon soup (no peanut) ────────────────
    a = res('recipe.new "Winter Daikon Soup" season=winter ethnic=japanese course=soup')["recipe_id"]
    res(f'recipe.add {a} ingredient=daikon qty=300 unit=g')
    res(f'recipe.add {a} ingredient=pork qty=150 unit=g')
    res(f'recipe.add {a} method=simmer')
    res(f'recipe.add {a} hint="skim the foam for a clear broth"')
    res(f'recipe.step {a} text="cut the daikon into rounds" uses=daikon')
    res(f'recipe.step {a} text="simmer daikon and pork 25 min" uses=daikon,pork by=simmer')

    card = res(f"recipe.view {a}")
    r1 = (card["title"] == "Winter Daikon Soup"
          and card["counts"]["ingredients"] == 2
          and card["counts"]["steps"] == 2
          and any(i["qty"] == "300" and i["unit"] == "g" for i in card["ingredients"]))
    record("R1 universe", r1,
           f"ing={card['counts']['ingredients']} steps={card['counts']['steps']}")

    # R2 — steps are ordered and carry their crossings.
    steps = card["steps"]
    r2 = (steps == sorted(steps, key=lambda s: s["order"])
          and len(steps[1]["uses"]) == 2 and len(steps[1]["by"]) == 1
          and len(steps[0]["uses"]) == 1)
    record("R2 step chain", r2,
           f"s0.uses={len(steps[0]['uses'])} s1.uses={len(steps[1]['uses'])} s1.by={len(steps[1]['by'])}")

    # ── Build recipe B: winter thai peanut curry (matches season, has peanut) ──
    b = res('recipe.new "Winter Thai Curry" season=winter ethnic=thai course=curry')["recipe_id"]
    res(f'recipe.add {b} ingredient=daikon qty=100 unit=g')
    res(f'recipe.add {b} ingredient=peanut qty=50 unit=g')
    res(f'recipe.add {b} constraint=peanut')
    # ── Recipe C: summer italian (should not surface for winter) ───────────────
    c = res('recipe.new "Summer Caprese" season=summer ethnic=italian course=salad')["recipe_id"]
    res(f'recipe.add {c} ingredient=tomato qty=2 unit=pc')

    # R3 — suggest by axes; A matches season+ethnic+course+have(daikon)=4/4,
    #      B matches season+have(daikon)=2/4 → A ranks above B.
    sug = res('recipe.suggest season=winter ethnic=japanese course=soup have=daikon')
    order = [s["recipe_id"] for s in sug["suggestions"]]
    top = sug["suggestions"][0]
    r3 = (order and order[0] == a and top["coverage"] == "4/4"
          and c not in order)
    record("R3 suggest rank", r3,
           f"top={top['title']!r} cov={top['coverage']} n_sug={len(order)}")

    # R4 — avoid=peanut is a hard filter: B is dropped entirely even though it
    #      still matches season+have(daikon); A (no peanut) survives.
    sug2 = res('recipe.suggest season=winter have=daikon avoid=peanut')
    ids2 = [s["recipe_id"] for s in sug2["suggestions"]]
    r4 = (a in ids2 and b not in ids2 and sug2["blocked_count"] >= 1)
    record("R4 constraint", r4,
           f"A_in={a in ids2} B_dropped={b not in ids2} blocked={sug2['blocked_count']}")

    # R5 — ls filters by axis intersection.
    winter = {r["recipe_id"] for r in res("recipe.ls season=winter")["recipes"]}
    summer = {r["recipe_id"] for r in res("recipe.ls season=summer")["recipes"]}
    r5 = (a in winter and b in winter and c not in winter
          and c in summer and a not in summer)
    record("R5 ls / axis", r5, f"winter={len(winter)} summer={len(summer)}")

    # R6 — idempotent alias on new.
    d1 = res('recipe.new "Aliased Dish" alias=recipe:test:aliased')["recipe_id"]
    again = res('recipe.new "Aliased Dish" alias=recipe:test:aliased')
    r6 = (again["status"] == "exists" and again["recipe_id"] == d1)
    record("R6 idempotent", r6, f"status={again['status']}")

    # ── Nutrition: USDA-style food data (per 100 g) + accumulation ─────────────
    res("recipe.food daikon kcal=18 protein_g=0.6 fat_g=0.1 carb_g=4.1")
    res("recipe.food pork kcal=242 protein_g=27 fat_g=14 carb_g=0")
    # (tomato deliberately has NO recipe.food → exercises no_data)
    n = res('recipe.new "Nutrition Test" season=winter')["recipe_id"]
    res(f"recipe.add {n} ingredient=daikon qty=300 unit=g")     # 3.0 × per-100g
    res(f"recipe.add {n} ingredient=pork qty=150 unit=g")       # 1.5 × per-100g
    res(f"recipe.add {n} ingredient=egg qty=1 unit=pc")         # count unit → unmeasured
    res(f"recipe.add {n} ingredient=tomato qty=100 unit=g")     # no recipe.food → no_data
    nut = res(f"recipe.nutrition {n}")
    t = nut["totals"]
    # 300g daikon: kcal 54, protein 1.8 ; 150g pork: kcal 363, protein 40.5
    r7 = (abs(t.get("kcal", 0) - 417.0) < 0.5
          and abs(t.get("protein_g", 0) - 42.3) < 0.1
          and nut["measured"] == 2
          and "egg" in nut["unmeasured"] and "tomato" in nut["no_data"])
    record("R7 nutrition", r7,
           f"kcal={t.get('kcal')} protein={t.get('protein_g')} "
           f"unmeasured={nut['unmeasured']} no_data={nut['no_data']}")

    # ── kcal target as a constraint (met + not-met), separate from allergens ───
    res(f"recipe.add {n} constraint=kcal<=600")     # 417 <= 600 → met
    res(f"recipe.add {n} constraint=protein_g>=50")  # 42.3 >= 50 → NOT met
    res(f"recipe.add {n} constraint=peanut")         # allergen, not a target
    nut2 = res(f"recipe.nutrition {n}")
    tgt = {x["nutrient"]: x for x in nut2["targets"]}
    card = res(f"recipe.view {n}")
    r8 = (tgt.get("kcal", {}).get("met") is True
          and tgt.get("protein_g", {}).get("met") is False
          and "constraint:peanut" in card["constraints"]
          and not any(c.startswith("constraint:kcal") for c in card["constraints"])
          and len(card["targets"]) == 2)
    record("R8 kcal target", r8,
           f"kcal_met={tgt.get('kcal',{}).get('met')} "
           f"protein_met={tgt.get('protein_g',{}).get('met')} "
           f"targets={len(card['targets'])}")

    # ── R9: a USDA .ak-imported food carries nutrition in its CONTENT string ───
    # (`.ak def` can't write meta) and is aliased by name — recipe.nutrition must
    # resolve it by slug and parse the "per 100g: …" string just like a structured
    # recipe.food. Simulate the loader's write via system_context (its exemption).
    from lib.akasha.jcl.workspace_context import system_context
    cx = k.manager.get_session("admin").local_cortex
    with system_context():                              # kabocha: only defined via content
        fk = cx.put_chunk(
            content=("Squash, winter, kabocha, raw — per 100g: 34 kcal, Protein 1.2g, "
                     "Fat 0.1g, Carbohydrate 8.0g, Fiber 2.0g, Sodium 4mg"),
            meta={"type": "atom", "role": "food"},
            author="admin", scopes=["owner:user_admin"])
        cx.set_alias(fk, "food:vegetable:squash_winter_kabocha_raw")  # USDA descriptive key
        cx.set_alias(fk, "food:kabocha")                             # plain-name alias
    u = res('recipe.new "USDA Content" season=winter')["recipe_id"]
    res(f"recipe.add {u} ingredient=kabocha qty=200 unit=g")          # 2.0 × per-100g
    un = res(f"recipe.nutrition {u}")
    ut = un["totals"]
    r9 = (abs(ut.get("kcal", 0) - 68.0) < 0.5
          and abs(ut.get("protein_g", 0) - 2.4) < 0.05
          and abs(ut.get("sodium_mg", 0) - 8.0) < 0.5
          and un["measured"] == 1 and not un["no_data"])
    record("R9 USDA content", r9,
           f"kcal={ut.get('kcal')} protein={ut.get('protein_g')} sodium={ut.get('sodium_mg')}")

    # ── R10: reach a food by its food:fdc:<id> alias (name deliberately mismatched) ──
    with system_context():
        gk = cx.put_chunk(
            content="Gourd, white-flowered (calabash), raw — per 100g: 14 kcal, Protein 0.6g",
            meta={"type": "atom", "role": "food"},
            author="admin", scopes=["owner:user_admin"])
        cx.set_alias(gk, "food:vegetable:gourd_white_flowered_raw")  # USDA descriptive key
        cx.set_alias(gk, "food:fdc:11209")                           # numeric FDC alias only
    g = res('recipe.new "FDC Handle" season=winter')["recipe_id"]
    # cooking name "yugao" won't match "gourd_white_flowered" — pin via fdc
    res(f"recipe.add {g} ingredient=yugao qty=200 unit=g fdc=11209")
    res(f"recipe.add {g} ingredient=nomatch qty=100 unit=g")   # no fdc, no name match
    gn = res(f"recipe.nutrition {g}")
    r10 = (abs(gn["totals"].get("kcal", 0) - 28.0) < 0.5   # 14 × 2.0
           and gn["measured"] == 1 and gn["no_data"] == ["nomatch"])
    record("R10 fdc handle", r10,
           f"kcal={gn['totals'].get('kcal')} measured={gn['measured']} no_data={gn['no_data']}")

    # ── R11: parallel cooking — the oven runs while the stew simmers ────────────
    p = res('recipe.new "Parallel Dinner" season=winter')["recipe_id"]
    res(f'recipe.step {p} text="prep the vegetables" dur=10 label=prep')
    res(f'recipe.step {p} text="simmer the stew" dur=20 after=prep label=stew')
    res(f'recipe.step {p} text="toast the garnish" dur=5 after=prep')   # parallel branch
    res(f'recipe.step {p} text="plate and serve" dur=3 after=stew,2')
    cr = res(f"recipe.critical {p}")
    crit = sorted(r["order"] for r in cr["steps"] if r["critical"])
    r11 = (abs(cr["makespan_min"] - 33.0) < 0.01 and cr["makespan_min"] < cr["sequential_min"]
           and crit == [0, 1, 3])
    record("R11 critical", r11,
           f"makespan={cr['makespan_min']} seq={cr['sequential_min']} critical={crit}")

    # ── R12: HACCP — cook-temp CCP + storage-temp control, measured + violated ──
    hd = res('recipe.new "Chicken Dish" season=winter')["recipe_id"]
    res(f'recipe.step {hd} text="cook the chicken through" dur=15 label=cook')
    res(f'recipe.control {hd} param=core_temp op=">=" value=75 unit=C step=cook ccp=yes')
    res(f'recipe.control {hd} param=storage_temp op="<=" value=5 unit=C')
    res(f'recipe.measure {hd} param=core_temp value=78 step=cook')   # pass
    res(f'recipe.measure {hd} param=storage_temp value=4')           # pass
    h_ok = res(f"recipe.haccp {hd}")
    res(f'recipe.measure {hd} param=core_temp value=70 step=cook')   # undercooked → violation
    h_bad = res(f"recipe.haccp {hd}")
    ccp = next((c for c in h_bad["ccps"] if c["key"] == "core_temp"), None)
    r12 = (h_ok["safe"] is True and h_ok["ccp_all_pass"] is True
           and h_bad["safe"] is False and ccp is not None and ccp["status"] == "fail"
           and any(v["key"] == "core_temp" for v in h_bad["violations"]))
    record("R12 haccp", r12,
           f"ok_safe={h_ok['safe']} bad_safe={h_bad['safe']} ccp_status={ccp and ccp['status']}")

    # ── R13: client-facing contract additions (idempotency / CRUD / version / paging) ──
    ed = res('recipe.new "Edit Me" season=winter')["recipe_id"]
    a1 = res(f"recipe.add {ed} ingredient=daikon qty=300 unit=g request_key=k1")
    a2 = res(f"recipe.add {ed} ingredient=daikon qty=300 unit=g request_key=k1")  # retry
    res(f"recipe.add {ed} ingredient=pork qty=150 unit=g")
    v0 = res(f"recipe.view {ed}")
    rm = res(f"recipe.ingredient.remove {ed} item={a1['key']}")
    v1 = res(f"recipe.view {ed}")
    pk = v1["ingredients"][0]["key"]
    res(f"recipe.ingredient.update {ed} item={pk} qty=200")
    v2 = res(f"recipe.view {ed}")
    # stale optimistic-lock guard → conflict error (not a silent overwrite)
    conflict = run(f"recipe.add {ed} ingredient=salt qty=1 unit=g expected_updated_at={v0['updated_at']}")
    for i in range(4):
        res(f'recipe.new "P{i}" season=autumn')
    pg = res("recipe.ls season=autumn limit=2")
    r13 = (a1["status"] == "added" and a2["status"] == "duplicate" and a1["key"] == a2["key"]
           and v0["counts"]["ingredients"] == 2 and v1["counts"]["ingredients"] == 1
           and v1["ingredients"][0]["name"] == "pork" and v2["ingredients"][0]["qty"] == "200"
           and "version" in v0 and "updated_at" in v0
           and "error" in conflict and "conflict" in conflict["error"]["message"]
           and len(pg["recipes"]) == 2 and pg["has_more"] is True and pg["count"] == 4)
    record("R13 edit/safety", r13,
           f"dup={a2['status']} removed→{v1['counts']['ingredients']} qty={v2['ingredients'][0]['qty']} "
           f"conflict={'error' in conflict} page={len(pg['recipes'])}/{pg['count']}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
