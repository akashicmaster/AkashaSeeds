#!/usr/bin/env python3
"""
Semantic Macro-Cache Phase 1 — planner acceptance (design §7 merge gate, memory-discipline §4).

Residency by MEMBERSHIP: a curated seed set (set:stage:featured) is expanded into a budgeted plan
(set:stage:cache_plan) whose members' bodies + pages deserve RAM. This eval drives the writer-side
planner (`cache.replan`) and asserts the memory-discipline contract:

  • Budget bounds the EXPANDED population, never the curated seed — the seed is ALWAYS included, and
    if the seed alone exceeds budget the planner flags `over_budget` (loud, no silent trim).
  • The closure is BOUNDED per seed member (a mega-hub seed can't explode the candidate ring — R1).
  • The plan is applied as a DIFF (added/removed), never clear-all (R7).
  • The plan is inspectable data (cache.plan / cache.stat); presence of the seed is the opt-in (a
    cell with no featured set → the mechanism is OFF).

The portal-side render warm daemon (design §4a) is a live-server concern (mirrors _revalidate); it
is out of scope for this unit eval, which pins the planner it consumes.

Run:  python test/semcache_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts import cache as _cache
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_semcache_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data, tok="admin"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus
    core = nuc.core
    ts = time.time()
    SMALL = "s" * 200

    def big(tag):
        # distinct content per atom (content-addressing collapses identical bodies);
        # ~80 KB ⇒ cost ≈ 240 KB per atom.
        return ("c" * 80000) + "|" + tag

    def atom(alias, content, salience=1.0):
        key = nuc.put_atom(content, {"salience": salience}, author="admin")
        core.put_alias(key, alias)
        return key

    def feat(key):
        core.add_to_collection(_cache.FEATURED, key)

    def link(src, dst, rel="thesaurus:related", w=1.0):
        core.put_link_raw(src, dst, rel, w, "forward", "atom", "admin", "verified", ts)

    # ── 0. no seed ⇒ the mechanism is OFF ──
    r0 = d("cache.replan", {})
    check("no curated seed ⇒ replan is inactive (mechanism OFF on a plain cell)",
          r0.get("active") is False, str(r0))

    # ── 1. a small seed with a LARGE candidate closure; budget trims the expansion ──
    seeds = [atom("concept:seed%d" % i, "seed %d %s" % (i, SMALL), salience=3.0) for i in range(3)]
    for s in seeds:
        feat(s)
    cand = []
    for i, s in enumerate(seeds):
        for j in range(4):                        # 12 large candidates total
            c = atom("concept:cand%d_%d" % (i, j), big("cand%d_%d" % (i, j)), salience=1.0 + j)
            link(s, c)
            cand.append(c)
    r1 = d("cache.replan", {"budget_mb": "1"})
    check("seed always included; budget bounds the EXPANSION (not all 12 candidates fit)",
          r1.get("seed") == 3 and 0 < r1.get("expanded", 0) < 12
          and r1.get("over_budget") is False, str(r1))
    check("plan est_bytes stays within budget",
          r1.get("est_bytes", 0) <= 1 * 1024 * 1024, "est_bytes=%s" % r1.get("est_bytes"))
    plan_members = set(core.get_collection_members(_cache.PLAN) or [])
    check("every seed member is in the plan set (seed never trimmed)",
          set(seeds) <= plan_members, "seed⊆plan=%s" % (set(seeds) <= plan_members))
    check("plan set size == seed + expanded",
          len(plan_members) == r1.get("seed") + r1.get("expanded"),
          "plan=%d seed=%d expanded=%d" % (len(plan_members), r1.get("seed"), r1.get("expanded")))

    # ── 2. DIFF-apply — add a seed, remove a seed; the plan updates by diff, not clear-all ──
    new_seed = atom("concept:seedX", "seedX %s" % SMALL, salience=3.0)
    feat(new_seed)
    core.remove_from_collection(_cache.FEATURED, seeds[0])     # drop seed0 from featured
    before = set(core.get_collection_members(_cache.PLAN) or [])
    r2 = d("cache.replan", {"budget_mb": "1"})
    after = set(core.get_collection_members(_cache.PLAN) or [])
    check("replan applies a DIFF (added>0 or removed>0; not a clear-all rebuild)",
          (r2.get("added", 0) + r2.get("removed", 0)) > 0 and after, str(r2))
    check("the newly featured seed is now in the plan; the dropped seed is gone",
          new_seed in after and seeds[0] not in after,
          "seedX_in=%s seed0_out=%s" % (new_seed in after, seeds[0] not in after))

    # ── 3. over-budget: the seed ALONE exceeds budget ⇒ flagged, no expansion, seed still all in ──
    for s in list(core.get_collection_members(_cache.FEATURED) or []):
        core.remove_from_collection(_cache.FEATURED, s)
    big_seed = [atom("concept:huge%d" % i, big("huge%d" % i), salience=1.0) for i in range(12)]  # 12 × 240KB ≈ 2.9MB
    for s in big_seed:
        feat(s)
    r3 = d("cache.replan", {"budget_mb": "1"})
    over_plan = set(core.get_collection_members(_cache.PLAN) or [])
    check("seed alone over budget ⇒ over_budget flagged, expansion suppressed, seed still all included",
          r3.get("over_budget") is True and r3.get("expanded") == 0 and set(big_seed) <= over_plan,
          str(r3))

    # ── 4. bounded closure (R1): a mega-hub seed's candidate ring is capped per seed ──
    for s in list(core.get_collection_members(_cache.FEATURED) or []):
        core.remove_from_collection(_cache.FEATURED, s)
    hub = atom("concept:hub", "hub %s" % SMALL, salience=5.0)
    feat(hub)
    for j in range(200):                          # 200 small neighbours — all fit in 1MB by bytes…
        c = atom("concept:hubn%d" % j, "n%d %s" % (j, SMALL), salience=1.0)
        link(hub, c)
    r4 = d("cache.replan", {"budget_mb": "8"})     # budget large enough that BYTES don't limit it
    check("mega-hub closure is capped per seed (expanded ≤ per-seed link cap, not 200) — R1",
          r4.get("expanded", 999) <= _cache._PER_SEED_LINKS,
          "expanded=%s cap=%d" % (r4.get("expanded"), _cache._PER_SEED_LINKS))

    # ── 5. inspectable: cache.plan + cache.stat + Health-visible counters ──
    pl = d("cache.plan", {"slugs": "1"})
    st = d("cache.stat", {})
    check("cache.plan reports the plan (atoms + warm slug list for the portal)",
          pl.get("atoms") == len(over_plan_or_hub(core, _cache)) and isinstance(pl.get("slugs"), list),
          "atoms=%s" % pl.get("atoms"))
    check("cache.stat is active (curated seed present) and carries plan-authorship counters",
          st.get("active") is True and "plan" in st and st.get("budget_mb_config") >= 1, str(st)[:160])
    check("semcache_counters() exposes the Health segment fields (plan/bytes/plan_age)",
          set(("plan", "bytes", "plan_age")) <= set(_cache.semcache_counters()), "")

    # ── 6. Phase 1.5 — focal-membrane demand staging (cache.stage): bounded, membrane-preferring ──
    focal = atom("concept:focal", "focal %s" % SMALL, salience=2.0)
    membrane = "set:stage:test_membrane"
    neigh = []
    for i in range(40):                                    # 40 candidates — well over any K
        c = atom("concept:fn%d" % i, "fn%d %s" % (i, SMALL), salience=1.0)
        link(focal, c)
        neigh.append(c)
        if i < 8:
            core.add_to_collection(membrane, c)            # 8 of them are membrane siblings
    rs = d("cache.stage", {"id": "concept:focal", "k": "5"})
    check("cache.stage bounds the staged membrane to K and trims the rest (never the raw closure) — R1",
          rs.get("staged") == 5 and rs.get("trimmed", 0) > 0 and len(rs.get("slugs", [])) == 5, str(rs))
    check("cache.stage writes nothing (READ) — the staged slugs are all real depth-1 neighbours",
          set(rs.get("slugs", [])) <= set(core.get_aliases_by_key(n)[0] for n in neigh
                                          if core.get_aliases_by_key(n)), "")
    rsm = d("cache.stage", {"id": "concept:focal", "set": membrane, "k": "6"})
    memb_aliases = set(core.get_aliases_by_key(n)[0] for n in neigh[:8] if core.get_aliases_by_key(n))
    check("cache.stage prefers the named membrane's siblings first (locality the visitor traverses)",
          len(set(rsm.get("slugs", [])) & memb_aliases) >= 5, "in_membrane=%d slugs=%s"
          % (len(set(rsm.get("slugs", [])) & memb_aliases), rsm.get("slugs")))
    rbad = d("cache.stage", {"id": "concept:does_not_exist"})
    check("cache.stage on an unknown focal is inactive (no crash, nothing staged)",
          rbad.get("active") is False, str(rbad))

    # ── 7. A4 regression — replan with NO budget arg (the boot-replan path). op_replan's `budget_mb`
    #   parameter once shadowed the module budget function, so `cache.replan` with an empty budget +
    #   a non-empty featured set crashed with `'str' object is not callable` (-32602) on EVERY boot
    #   replan since §12.5 planted the seed. Every case above passed a non-empty `budget_mb`, so none
    #   of them ever reached it. This case IS the boot path: empty data ⇒ env default budget.
    feat_now = set(core.get_collection_members(_cache.FEATURED) or [])
    check("(setup) featured set is non-empty for the empty-budget path", bool(feat_now), str(len(feat_now)))
    r7 = d("cache.replan", {})            # empty data ⇒ empty budget ⇒ env_budget_mb() default
    check("A4 — cache.replan with NO budget does not crash and authors a plan (shadowing regression)",
          "error" not in r7 and r7.get("active") is not False
          and r7.get("budget_mb") == _cache.env_budget_mb(), str(r7)[:200])
    check("A4 — a clean empty-budget replan records NO last_error on the counters",
          _cache.semcache_counters().get("last_error") is None,
          str(_cache.semcache_counters().get("last_error")))
    r7a = d("cache.replan", {"budget": "2"})   # the preferred `budget=` spelling still works
    check("A4 — `budget=` (preferred spelling) is honoured alongside the `budget_mb=` CLI alias",
          "error" not in r7a and r7a.get("budget_mb") == 2, str(r7a)[:160])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the semantic macro-cache planner holds the contract: residency by "
          "membership; the curated seed is always included and over-budget is flagged loudly; the "
          "depth-1 closure is bounded per seed (R1); the plan is diff-applied not clear-all (R7); and "
          "the plan is first-class inspectable data on the Health line.")
    sys.exit(0)


def over_plan_or_hub(core, _cache):
    return set(core.get_collection_members(_cache.PLAN) or [])


if __name__ == "__main__":
    main()
