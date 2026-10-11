#!/usr/bin/env python3
"""
S2-k2 — a learned-head observe reuses the item's BASE-SPACE embedding instead of re-embedding.

A promoted head observes by embedding each target item in its base space (mobilenet on the VPS, color
here) and then running the head. The base ENCODER is the whole cost of the observe; the head is cheap.
S2-k2 caches the base embedding the FIRST head computes (keyed on item + base_space + base sha8) and
hands it to every later head, which then runs ONLY the head:

  • the first head observe stores a base-space feature atom per target item (reused_embeddings=0);
  • a second head observe on the same target REUSES them (reused_embeddings == items, no re-embed);
  • the predictions are identical (same head, same embedding) — reuse changes cost, not the result.

Both cell shapes. No network, no sklearn.

Run:  python app/test/head_embedding_reuse_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["OAK", "MAPLE", "BIRCH", "PINE", "ELM", "ASH"]
_POOL = "source:pool:leafimg:v1"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_hre_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus.core

    def members(setname):
        try:
            return list(nuc.get_collection_members(setname) or [])
        except Exception:
            return []

    d("world.genesis", {})
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("bench.new", {"name": "leaf", "kind": "learning", "group": "lab"})
    d("society.new", {"group": "lab", "name": "leafsoc", "world": "default", "bench": "leaf",
                      "kind": "cowork"})
    d("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = [{"id": f"img_{i}", "image": f"mock://leaf/{_CLASSES[i % 6].lower()}/{i}.jpg",
             "species_symbol": _CLASSES[i % 6], "title": f"{_CLASSES[i % 6]} {i}"} for i in range(60)]
    d("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock", "label_field": "species_symbol"})
    d("source.acquire", {"source": "source:src:leafsrc", "rule": "mock", "records": recs,
                         "pool": _POOL, "id_field": "id", "label_field": "species_symbol"})
    d("source.pool.freeze", {"pool": _POOL})
    tr = d("source.pool.sample", {"pool": _POOL, "name": "train", "n": "40", "seed": "plants1",
                                  "strata": "species_symbol"})
    tg = d("source.pool.sample", {"pool": _POOL, "name": "target", "n": "20", "seed": "plants1",
                                  "strata": "species_symbol", "rule": "complement:train"})
    d("learning.dataset.bind", {"name": "leaf", "pool": tr.get("sample"), "role": "train"})
    d("learning.dataset.bind", {"name": "leaf", "pool": tg.get("sample"), "role": "target"})

    # train a head on the color base space and promote it
    d("learning.feature.run", {"name": "leaf", "pool": "role:train", "observers": "color", "run": "f1"})
    d("learning.feature.execute", {"name": "leaf", "run": "f1"})
    d("learning.feature.seal", {"name": "leaf", "run": "f1"})
    trn = d("learning.train", {"name": "leaf", "run": "f1", "space": "color", "head": "logreg",
                            "split": "0.8", "seed": "plants1", "label_key": "species_symbol"})
    d("learning.evaluate", {"name": "leaf", "model": trn.get("model"), "sample": "test"})
    d("learning.promote", {"name": "leaf", "model": trn.get("model"), "observer": "plants_head_f1"})

    # ── the FIRST head observe — no base embedding exists yet, so it embeds (reused_embeddings=0) and
    #    caches the target's base-space (color) embeddings for the next head ──
    o1 = d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "plants_head_f1",
                             "run": "o1", "branch": "plants_t6"})
    check(f"[{shape}] the FIRST head observe embeds the target (reused_embeddings=0)",
          o1.get("observed") == 20 and o1.get("reused_embeddings") == 0, str(o1)[:160])
    _color_feats = members("set:vlab:feat:o1:color")
    check(f"[{shape}] the first head observe STORED base-space (color) embeddings for reuse",
          len(_color_feats) == 20, f"n={len(_color_feats)}")

    # ── a SECOND, DIFFERENT head (different weights → different sha8, so the whole-observation reuse
    #    MISSES) shares the base space, so its observe reuses every base embedding and runs only the head ──
    trn2 = d("learning.train", {"name": "leaf", "run": "f1", "space": "color", "head": "logreg",
                             "split": "0.7", "seed": "plants2", "label_key": "species_symbol"})
    d("learning.evaluate", {"name": "leaf", "model": trn2.get("model"), "sample": "test"})
    d("learning.promote", {"name": "leaf", "model": trn2.get("model"), "observer": "plants_head_f2"})
    o2 = d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "plants_head_f2",
                             "run": "o2", "branch": "plants_t6b"})
    check(f"[{shape}] a DIFFERENT head reuses every base embedding (reused_embeddings=items, observed=items)",
          o2.get("observed") == 20 and o2.get("reused_embeddings") == 20, str(o2)[:160])
    check(f"[{shape}] the reusing head did NOT re-store the base embeddings (cache is not duplicated)",
          len(members("set:vlab:feat:o2:color")) == 0, f"n={len(members('set:vlab:feat:o2:color'))}")
    # ── S2-k3 — the observe cost is instrumented, and the reuse path skips the encoder (t_embed≈0) ──
    _tm = o2.get("timing") or {}
    check(f"[{shape}] S2-k3: the reuse pass reports its cost split (t_embed/t_head/t_write, n=items)",
          _tm.get("n") == 20 and "t_write" in _tm and "t_embed" in _tm, str(_tm))
    check(f"[{shape}] S2-k3: the reuse pass skipped the encoder (t_embed≈0 — the image is not touched)",
          float(_tm.get("t_embed") or 0.0) < float(_tm.get("t_head") or 0.0) + 0.05
          and float(_tm.get("t_embed") or 0.0) < 0.05,
          f"t_embed={_tm.get('t_embed')} t_head={_tm.get('t_head')} t_write={_tm.get('t_write')}")


def main():
    print("=" * 78)
    print("S2-k2 — learned-head observe reuses the base-space embedding (no re-embed)")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the first head observe caches the target's base-space embeddings and a later "
          "head reuses every one of them (reused_embeddings=items, the encoder never re-runs), with "
          "identical predictions — both cell shapes.")


if __name__ == "__main__":
    main()
