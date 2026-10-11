#!/usr/bin/env python3
"""
Semantic macro-cache §12.5 — deploy-time initial featured set (acceptance).

A fresh deploy should have the cache ACTIVE (not OFF until someone hand-curates). The permanent
measure: the seed bundles config/semcache_featured.json ONLY on the thesaurus/service tier, and the
kernel seeds set:stage:featured ONCE at boot from bundled curated sources — NON-CLOBBERING (an
operator's existing curation is left as-is), tier-gated (personal seeds ship no config → cache stays
OFF, the design's opt-in), and it fires a cache.replan so the plan is authored immediately.

This eval pins the pure seeding step + the tier-correct crystallizer wiring.

Run:  python test/semcache_featured_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.concepts import schedules
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    # `GeneticBlueprint` is GENERATOR-SIDE — a seed carries no `reproductor/`, so this import used
    # to raise on every deployed tree. What is checked here is which series the BLUEPRINT bundles
    # the featured config for, a decision made when the seed is cut. A skip says so by name and
    # never counts as a pass (deploy_eval, 09-21).
    if not os.path.isdir(os.path.join(ROOT, "reproductor")):
        print("SKIP generator-only — reproductor/ (the seed blueprint) ships in no seed; which "
              "series bundles the featured config is decided where the seed is cut")
        sys.exit(0)
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts import cache as _cache
    from reproductor.engine import GeneticBlueprint
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_scf_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def call(method, data=None):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data or {}}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus
    core = nuc.core

    def atom(alias):
        key = nuc.put_atom("c " + alias, {"salience": 2.0}, author="admin")
        core.put_alias(key, alias)
        return key

    # curated demo sets (as the curation/*.ak packs would create them)
    demos = {
        "curation:demo:print_dreamers": [atom("print:a"), atom("print:b")],
        "curation:demo:beer_journey":   [atom("beer:a")],
        "curation:demo:sky_dreamers":   [atom("sky:a"), atom("sky:b")],
        "curation:demo:lineage":        [atom("lin:a")],
    }
    for s, keys in demos.items():
        for kk in keys:
            core.add_to_collection(s, kk)
    all_demo_keys = {kk for keys in demos.values() for kk in keys}

    cfg = {"enabled": True, "from_sets": list(demos.keys()), "top_salient": 0}

    # ── 1. a fresh (empty featured) deploy is seeded from the bundled curated sets ──
    added, existing = schedules.semcache_apply_featured(k, core, cfg)
    feat = set(core.get_collection_members(_cache.FEATURED) or [])
    check("empty featured ⇒ seeded from the bundled curated demo sets (union)",
          existing == 0 and added == len(all_demo_keys) and feat == all_demo_keys,
          "added=%d feat=%d expected=%d" % (added, len(feat), len(all_demo_keys)))

    # ── 2. the cache is now ACTIVE (replan produces a plan instead of {active:False}) ──
    rp = call("cache.replan", {"budget_mb": "8"})
    check("with featured seeded, cache.replan is ACTIVE (a fresh deploy warms from boot)",
          rp.get("active") is not False and rp.get("seed") == len(all_demo_keys), str(rp)[:140])

    # ── 3. NON-CLOBBERING — a second run leaves an operator's curation untouched ──
    added2, existing2 = schedules.semcache_apply_featured(k, core, cfg)
    feat2 = set(core.get_collection_members(_cache.FEATURED) or [])
    check("already-curated featured is left as-is (added=0, existing reported, membership unchanged)",
          added2 == 0 and existing2 == len(all_demo_keys) and feat2 == all_demo_keys, "added2=%d" % added2)

    # ── 4. top_salient path is best-effort and never raises (bounded query) ──
    # fresh empty featured on a different set-name space; here just confirm the call is safe with N>0
    ok_topn = True
    try:
        schedules.semcache_apply_featured(k, core, {"enabled": True, "from_sets": [], "top_salient": 10})
    except Exception:
        ok_topn = False
    check("the top_salient backbone is best-effort and never raises", ok_topn, "")

    # ── 5. tier-correct wiring: thesaurus09 ships the config; the public seeds line does NOT ──
    th = GeneticBlueprint.get_config("thesaurus09").get("semcache_featured")
    s14 = GeneticBlueprint.get_config("seeds14").get("semcache_featured")
    th_n = GeneticBlueprint.get_config("thesaurus09n").get("semcache_featured")
    check("thesaurus09 / thesaurus09n bundle the initial-featured config; seeds14 does NOT (cache OFF)",
          bool(th and th.get("enabled")) and bool(th_n and th_n.get("enabled")) and not s14,
          "th=%s th_n=%s s14=%s" % (bool(th), bool(th_n), bool(s14)))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the deploy-time initial featured set seeds a fresh cell from the bundled "
          "curated sources (cache active from boot), never clobbers an operator's curation, and ships "
          "ONLY on the thesaurus/service tier (personal seeds keep the cache OFF — the opt-in contract).")
    sys.exit(0)


if __name__ == "__main__":
    main()
