#!/usr/bin/env python3
"""
onto-reconcile eval — pack re-import retires atoms the pack no longer contributes, WITHOUT a
data wipe, and NEVER touches user knowledge. Spec: docs/for-llm/ontology-reconciliation-spec.md.

  R1 removal retires   — pack P (a,b,c) → reload (a,b): c evicted, alias gone, its sys:is_a +
                         meal:all membership gone; a,b untouched.
  R2 edit orphan       — a's description edited → new key a'; old a retired; alias resolves to a'.
  R3 user-data fence   — an owner:user_x atom linking to c: c soft-evicted (not dropped); the
                         user atom is intact; the dry-run warned about the reference.
  R4 cross-pack refcnt — P and Q both def k. Reload P without k → k live (Q owns). Reload Q
                         without k → retired.
  R5 idempotent        — reconcile an unchanged pack → nothing retired.
  R6 normalizer-coherent— retiring a food removes its derived sys:is_a (no evicted taxon).
  R7 dry-run == apply  — the dry-run retire list equals what apply retires.

Run:  python test/onto_reconcile_eval.py
"""
import os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:20} {detail}")


def main():
    print("\n  onto-reconcile eval — pack removal retires, user knowledge fenced\n")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology_reconcile import OntologyReconciler
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_recon_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **d):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": d}, "id": 1}, "local")

    sess = k.manager.get_session("admin")
    store = sess.nucleus                      # write-capable engine over the universal layer
    core = store.core
    R = OntologyReconciler(store)

    def kof(alias): return sess.local_cortex.resolve_alias(alias)
    def status(key):
        row = core.get_chunk_raw(key); return row["status"] if row else "GONE"
    def in_set(name, key): return key in (core.get_collection_members(name) or [])

    # ── R1 removal retires ────────────────────────────────────────────────────
    for a, d in [("food:a", "Alpha dish."), ("food:b", "Beta dish."), ("food:c", "Gamma dish.")]:
        loc("def", name=a, description=d, scope="universal")
    loc("ln", src="food:c", dst="ingredient", rel="sys:is_a", scope="universal")
    loc("set.add", name="meal:all", id="food:c", scope="universal")
    ka, kb, kc = kof("food:a"), kof("food:b"), kof("food:c")
    R.stamp_provenance("P", [ka, kb, kc])
    R.reconcile("P", {ka, kb, kc}, dry_run=False)         # establish ledger (nothing gone yet)
    # reload P': c removed
    R.reconcile("P", {ka, kb}, dry_run=False)
    ok = (status(kc) == "evicted" and kof("food:c") is None
          and not in_set("meal:all", kc)
          and status(ka) == "verified" and status(kb) == "verified"
          and kof("food:a") == ka)
    record("R1 removal retires",
           ok, f"c={status(kc)} alias={kof('food:c')} in_meal={in_set('meal:all', kc)} a={status(ka)}")

    # ── R2 rename orphan ──────────────────────────────────────────────────────
    # A `def` is a NAME-keyed hub, so editing a description is in-place (same key). The orphan
    # case is a RENAME: the old name is dropped from the pack and a new one added. The old
    # concept's key is then no longer contributed → retired; the stale alias must not linger.
    loc("def", name="dish:oldname", description="A dish, first name.", scope="universal")
    kold = kof("dish:oldname")
    R.stamp_provenance("P", [ka, kb, kold]); R.reconcile("P", {ka, kb, kold}, dry_run=False)
    loc("def", name="dish:newname", description="A dish, renamed.", scope="universal")
    knew = kof("dish:newname")
    R.stamp_provenance("P", [ka, kb, knew])
    R.reconcile("P", {ka, kb, knew}, dry_run=False)       # oldname dropped → kold retired
    record("R2 rename orphan",
           knew != kold and status(kold) == "evicted" and kof("dish:oldname") is None
           and status(knew) == "verified" and kof("dish:newname") == knew,
           f"kold={status(kold)} old_alias={kof('dish:oldname')} knew={status(knew)}")

    # ── R3 user-data fence ────────────────────────────────────────────────────
    loc("def", name="food:e", description="Epsilon dish.", scope="universal")
    ke = kof("food:e")
    R.stamp_provenance("P", [ka, kb, ke]); R.reconcile("P", {ka, kb, ke}, dry_run=False)
    # a USER atom (owner:user_x) that links TO food:e
    import hashlib
    uk = hashlib.sha256(b"user note about epsilon").hexdigest()
    core.put_chunk_raw(uk, "My note referencing epsilon.", "{}", "user_x", "verified", 0.0)
    core.put_alias(uk, "note:user_x:epsilon")
    core.put_chunk_access(uk, ["owner:user_x", "view:user_x"])
    core.put_link_raw(uk, ke, "calc:associated_with")
    dry = R.reconcile("P", {ka, kb}, dry_run=True)         # e removed from pack
    warned = any(w["key"] == ke for w in dry["user_ref_warnings"])
    R.reconcile("P", {ka, kb}, dry_run=False)
    user_intact = (status(uk) == "verified" and kof("note:user_x:epsilon") == uk)
    record("R3 user-data fence",
           status(ke) == "evicted" and status(uk) != "GONE" and user_intact and warned,
           f"e={status(ke)} user={status(uk)} user_alias_ok={kof('note:user_x:epsilon')==uk} warned={warned}")

    # ── R4 cross-pack ref-count ───────────────────────────────────────────────
    loc("def", name="shared:k", description="A shared concept.", scope="universal")
    kk = kof("shared:k")
    R.stamp_provenance("P", [kk]); R.stamp_provenance("Q", [kk])
    R.reconcile("P", {kk}, dry_run=False); R.reconcile("Q", {kk}, dry_run=False)
    R.reconcile("P", set(), dry_run=False)                 # P drops k → Q still owns it
    live_after_P = status(kk) == "verified"
    owners_after_P = (R._meta(kk) or {}).get("pack")
    R.reconcile("Q", set(), dry_run=False)                 # Q drops k → now retired
    retired_after_Q = status(kk) == "evicted"
    record("R4 cross-pack refcnt",
           live_after_P and owners_after_P == ["Q"] and retired_after_Q,
           f"after_P live={live_after_P} owners={owners_after_P} | after_Q evicted={retired_after_Q}")

    # ── R5 idempotent ─────────────────────────────────────────────────────────
    loc("def", name="food:f", description="Zeta dish.", scope="universal")
    kf = kof("food:f")
    R.stamp_provenance("P2", [kf]); R.reconcile("P2", {kf}, dry_run=False)
    rep = R.reconcile("P2", {kf}, dry_run=False)           # unchanged
    record("R5 idempotent", rep["gone_count"] == 0 and not rep["retired"] and status(kf) == "verified",
           f"gone={rep['gone_count']} retired={len(rep['retired'])}")

    # ── R6 normalizer-coherent: the derived sys:is_a from a retired food is gone ──
    loc("def", name="food:g", description="Eta dish.", scope="universal")
    loc("ln", src="food:g", dst="ingredient", rel="sys:is_a", scope="universal")
    kg = kof("food:g"); king = kof("ingredient")
    R.stamp_provenance("P3", [kg]); R.reconcile("P3", {kg}, dry_run=False)
    R.reconcile("P3", set(), dry_run=False)
    # no outgoing sys:is_a remains from the retired atom (it can't re-inflate a mega-hub / mis-bind)
    still = [l for l in (core.get_adjacent_links(kg) or []) if l.get("rel") == "sys:is_a"]
    record("R6 normalizer-coherent", status(kg) == "evicted" and not still,
           f"g={status(kg)} dangling_sys_is_a={len(still)}")

    # ── R7 dry-run == apply ───────────────────────────────────────────────────
    for a, d in [("food:h", "Theta."), ("food:i", "Iota."), ("food:j", "Kappa.")]:
        loc("def", name=a, description=d, scope="universal")
    kh, ki, kj = kof("food:h"), kof("food:i"), kof("food:j")
    R.stamp_provenance("P4", [kh, ki, kj]); R.reconcile("P4", {kh, ki, kj}, dry_run=False)
    dry = R.reconcile("P4", {kh}, dry_run=True)            # would retire i, j
    dry_set = set(dry["retired"])
    apply = R.reconcile("P4", {kh}, dry_run=False)
    apply_set = set(apply["retired"])
    record("R7 dry-run == apply",
           dry_set == apply_set == {ki, kj} and status(kh) == "verified",
           f"dry={sorted(dry_set)==sorted([ki,kj])} apply==dry={dry_set==apply_set}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
