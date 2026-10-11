#!/usr/bin/env python3
"""
S1-a §1.2/§1.3 — the hydrate registry names every accelerator and regenerates it from canonical inputs.

The S1 invariant: *a materialized semantic horizon is an accelerator, never the source of semantic
truth.* This eval proves it for the coordinate-layer accelerator on BOTH cell shapes:

  • `hydrate.ls` enumerates the accelerators (vlab_layer / semcache_plan /
    boot_index) with inputs, regen op, layer_v, boot policy;
  • `hydrate.verify name=vlab_layer` on an already-hydrated cell regenerates with assigned=0 (the cheap
    "the accelerator still equals its regeneration" probe);
  • REGENERATION EQUALITY: capture the derived coordinate Sets, DROP them (+ strip the layer_v stamp),
    `hydrate.run name=vlab_layer`, and the Sets come back byte-for-byte equal — the test that makes the
    invariant true rather than asserted.

Run:  python app/test/hydrate_registry_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
sys.path.insert(0, os.path.join(ROOT, "test"))
_fails = []
_CLASSES = ["OAK", "MAPLE", "BIRCH", "PINE", "ELM", "ASH"]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_hydrate_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    core = k.manager.shared_nucleus.core

    def members(s):
        try:
            return set(core.get_collection_members(s) or [])
        except Exception:
            return set()

    d("world.genesis", {})
    d("bench.new", {"name": "leaf", "kind": "learning"})
    d("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = [{"id": f"img_{i}", "image": f"mock://leaf/{i}.jpg", "species_symbol": _CLASSES[i % 6]}
            for i in range(18)]
    d("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock", "label_field": "species_symbol"})
    d("source.acquire", {"source": "source:src:leafsrc", "rule": "mock", "records": recs,
                         "pool": "source:pool:leafimg:v1", "id_field": "id", "label_field": "species_symbol"})
    d("source.pool.freeze", {"pool": "source:pool:leafimg:v1"})
    tg = d("source.pool.sample", {"pool": "source:pool:leafimg:v1", "name": "target", "n": "12",
                                  "seed": "s1", "strata": "species_symbol"})
    d("learning.dataset.bind", {"name": "leaf", "pool": tg.get("sample"), "role": "target"})
    d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "color", "run": "o1",
                        "branch": "plants_t6"})

    # ── hydrate.ls enumerates the accelerators ──
    ls = d("hydrate.ls", {})
    names = {r.get("name") for r in (ls.get("accelerators") or [])}
    check(f"[{shape}] hydrate.ls enumerates the accelerators",
          {"vlab_layer", "semcache_plan", "boot_index", "leaderboard"} <= names
          and not ({"cronon", "retention"} & names),
          str(names))
    _vl = next((r for r in ls.get("accelerators") or [] if r["name"] == "vlab_layer"), {})
    check(f"[{shape}] the vlab_layer entry carries inputs / regen op / layer_v",
          _vl.get("layer_v") == 2 and _vl.get("regenerate") == "vlab.layer.backfill" and _vl.get("inputs"),
          str(_vl))

    # ── S2-m — plant a sweep_def atom that is NOT in set:wb:sweeps:all (a sweep defined before the
    #    index existed). The leaderboard hydrate must enumerate from the CANONICAL sweep_def atoms
    #    (not only the new-writes index), repair its missing board, and backfill the index. ──
    from lib.akasha.concepts._universal import UniversalConcept as _UC
    from lib.akasha.jcl.workspace_context import system_context as _sysctx
    _u = _UC(k.manager.get_session("admin")); _u._space = ""
    with _sysctx():
        _defkey = _u._mk("wb:leaf:sweep:hydro", "[stale sweep def — not indexed]",
                         {"concept": "sweep_def", "bench": "wb:leaf", "sweep": "hydro",
                          "grid": {"head": ["logreg"]}, "template": "learn_observe"})
    check(f"[{shape}] S2-m the planted sweep_def is NOT in set:wb:sweeps:all yet",
          _defkey not in members("set:wb:sweeps:all")
          and not core.get_key_by_alias("wb:leaf:leaderboard:hydro"),
          f"key={_defkey[:8]}")

    # ── H1: the boot pass EXECUTES the policy (no entry left with last_run_epoch=null) ──
    check(f"[{shape}] before the boot pass, last_run_epoch is null",
          all(r.get("last_run_epoch") is None for r in (ls.get("accelerators") or [])))
    bp1 = d("hydrate.boot_pass", {})
    ls2 = d("hydrate.ls", {})
    check(f"[{shape}] H1 after the boot pass, NO entry reads last_run_epoch=null",
          all(r.get("last_run_epoch") is not None for r in (ls2.get("accelerators") or [])),
          str([(r["name"], r.get("last_run_epoch")) for r in ls2.get("accelerators") or []]))
    # ── S2-m — the boot pass repaired the orphan sweep's missing board AND backfilled the index from
    #    the canonical sweep_def atom (assigned>=1) ──
    _lb = next((x for x in (bp1.get("boot_pass") or []) if x.get("name") == "leaderboard"), {})
    check(f"[{shape}] S2-m the boot pass rebuilt the orphan board (leaderboard assigned>=1)",
          int(_lb.get("assigned") or 0) >= 1, str(_lb))
    check(f"[{shape}] S2-m the missing board was repaired (wb:leaf:leaderboard:hydro exists)",
          bool(core.get_key_by_alias("wb:leaf:leaderboard:hydro")))
    check(f"[{shape}] S2-m the canonical enumeration backfilled set:wb:sweeps:all",
          _defkey in members("set:wb:sweeps:all"))
    # a second boot pass regenerates NO NEW work for vlab_layer (its `assigned` counts NEW backfills;
    # cronon's `members` is a mapped-count, idempotent but not a new-work signal, so it is not asserted 0)
    bp2 = d("hydrate.boot_pass", {})
    _vl2 = next((x for x in (bp2.get("boot_pass") or []) if x.get("name") == "vlab_layer"), {})
    check(f"[{shape}] H1 a second boot pass assigns 0 new work for vlab_layer (idempotent)",
          _vl2.get("assigned") in (0, None), str(_vl2))

    # ── hydrate.verify on an already-hydrated cell → assigned=0 ──
    ver = d("hydrate.verify", {"name": "vlab_layer"})
    _v0 = (ver.get("verified") or [{}])[0]
    check(f"[{shape}] hydrate.verify vlab_layer → assigned=0 (accelerator == regeneration)",
          _v0.get("assigned") in (0, None) and _v0.get("verified") is True, str(_v0))

    # ── regeneration equality: capture, DROP, regenerate, compare ──
    fam_set = "set:vlab:purpose:bench"
    obs_set = "set:wb:leaf:observations"
    pre_fam, pre_obs = members(fam_set), members(obs_set)
    check(f"[{shape}] the coordinate Sets are populated before the drop",
          len(pre_fam) > 0 and len(pre_obs) > 0, f"fam={len(pre_fam)} obs={len(pre_obs)}")
    # DROP the accelerator: strip the layer_v stamp on the run's observations + clear the derived Sets
    for okey in list(core.get_collection_members("set:vlab:run:o1:observations") or []):
        row = core.get_chunk_raw(okey)
        if not row:
            continue
        m = json.loads(row["meta"]) if row["meta"] else {}
        for kk in ("layer_v", "bench", "wf_branch", "purpose", "family"):
            m.pop(kk, None)
        core.update_meta(okey, m)
    for s in (fam_set, obs_set):
        try:
            core.clear_collection(s)
        except Exception:
            pass
    check(f"[{shape}] the accelerator is dropped (Sets cleared)",
          len(members(fam_set)) == 0 and len(members(obs_set)) == 0)
    # REGENERATE from canonical (the observations + run atoms are canonical; the Sets are derived)
    rr = d("hydrate.run", {"name": "vlab_layer"})
    check(f"[{shape}] hydrate.run vlab_layer regenerates (assigned>0)",
          int(rr.get("assigned") or 0) > 0 and rr.get("status") in ("ok", None), str(rr)[:160])
    post_fam, post_obs = members(fam_set), members(obs_set)
    check(f"[{shape}] §1.3 the regenerated Sets EQUAL the pre-drop Sets (regeneration equality)",
          post_fam == pre_fam and post_obs == pre_obs,
          f"fam {len(pre_fam)}→{len(post_fam)} obs {len(pre_obs)}→{len(post_obs)}")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — hydrate.* names every accelerator and regenerates it from canonical inputs: "
          "hydrate.ls enumerates them, hydrate.verify proves an already-hydrated accelerator equals its "
          "regeneration (assigned=0), and dropping the coordinate Sets then hydrate.run restores them "
          "byte-for-byte equal — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
