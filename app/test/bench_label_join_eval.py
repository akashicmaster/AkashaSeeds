#!/usr/bin/env python3
"""
A34 — the class label reaches the learner through the SOURCE-PACK path.

The v20 box symptom: b4 failed `need ≥2 labeled feature vectors … (got 0 vectors, 0 classes)` — the
1024-d vectors existed but every one was UNLABELED. `app/assets/plants_vision/pack.json` declares
`label_field: species_symbol`, but the importer passed only `id_field` to `source.acquire`, and
`learning.train` looked for `label`/`symbol` — never `species_symbol`. The evals could not see it because
they wrote `label=` straight onto synthetic sources, never through a pack. This eval goes through the
PACK path and passes ONLY if the label join works from `label_field`. Both cell shapes.

Run:  python app/test/bench_label_join_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.source import bootstrap
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["AAA", "BBB", "CCC"]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _write_pack(pack_dir, pool, n, label_field="species_symbol"):
    dd = os.path.join(pack_dir, "mini")
    os.makedirs(dd, exist_ok=True)
    json.dump({"pool": pool, "provider": "mini", "name": "mini", "rights": "CC0", "format": "jsonl",
               "data": "d.jsonl", "id_field": "id", "label_field": label_field, "freeze": True,
               "rule": "mini image refs"}, open(os.path.join(dd, "pack.json"), "w"))
    with open(os.path.join(dd, "d.jsonl"), "w") as f:
        for i in range(n):
            f.write(json.dumps({"id": f"img{i}", "species_symbol": _CLASSES[i % 3],
                                "binomial": f"Genus {_CLASSES[i % 3]}",
                                "image_url": f"mock://leaf/{i}.jpg"}) + "\n")


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    base = tempfile.mkdtemp(prefix="akasha_lbl_")
    pack_dir = tempfile.mkdtemp(prefix="akasha_lblpk_")
    os.environ["AKASHA_SOURCE_PACK_DIR"] = pack_dir
    POOL = "source:pool:mini_images:v1"
    _write_pack(pack_dir, POOL, 18)

    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"client_id": "admin", "data": data}, "id": "t"}, "internal")
        return r if "error" in r else (r.get("result") or {})

    d("world.genesis", {})
    bootstrap.source_packs_once(k)

    # ── the importer stamped the pool's label_field AND wrote a top-level label on each item ──
    stt = d("source.status", {"pool": POOL})
    check(f"[{shape}] the pack imported + froze the image pool", stt.get("frozen") is True, str(stt)[:100])
    from lib.akasha.concepts.source import SourceDataLayer
    s = SourceDataLayer(k.manager.get_session("admin"))
    pm = s.cortex.get_meta(s._key(POOL)) or {}
    check(f"[{shape}] the pool records label_field from the pack", pm.get("label_field") == "species_symbol",
          str(pm.get("label_field")))
    itemk = s._key("source:item:mini:img0")
    im = s.cortex.get_meta(itemk) or {}
    check(f"[{shape}] each item carries a top-level `label` hoisted from label_field",
          im.get("label") == "AAA", str(im.get("label")))

    # ── bench binds the pool, extracts features (mock observer), and TRAINS — the join must work ──
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("bench.new", {"name": "mini", "kind": "learning"})          # public bench
    d("society.new", {"group": "lab", "name": "minisoc", "world": "default", "bench": "mini", "kind": "cowork"})
    d("learning.dataset.bind", {"name": "mini", "pool": POOL})
    fe = d("learning.feature.extract", {"name": "mini", "pool": POOL, "observers": "color", "run": "r1"})
    check(f"[{shape}] feature.extract observed the pool", fe.get("observed", 0) >= 1, str(fe)[:120])
    tr = d("learning.train", {"name": "mini", "run": "r1", "space": "color", "head": "logreg", "seed": "s1"})
    check(f"[{shape}] learning.train JOINS the labels through the pack path (no 'got 0 vectors')",
          tr.get("model", "").startswith("model:learned:mini_head")
          and tr.get("n_labeled", 0) >= 6 and set(tr.get("classes") or []) == set(_CLASSES),
          str(tr)[:200])

    # ── A34(c): the LIVE-VPS case — a pool imported WITHOUT label_field (no top-level `label` on its
    #    items), then re-scanned so the pool gets its label_field stamped (frozen members untouched); the
    #    resolver must then read the class from source_metadata via the declared join, no re-import. ──
    from app.concepts.bench_learning import LearningBenchConcept
    lb = LearningBenchConcept(k.manager.get_session("admin"))
    reg = d("source.register", {"provider": "legacy", "name": "legacy2", "rights": "CC0"})
    src2 = reg.get("source")
    P2 = "source:pool:legacy_images:v1"
    d("source.pool.create", {"name": P2, "rule": "legacy", "source": src2})   # NO label_field yet
    d("source.acquire", {"source": src2, "rule": "legacy", "pool": P2, "id_field": "id",   # NO label_field
                         "records": [{"id": "L0", "species_symbol": "AAA", "image_url": "mock://l/0.jpg"},
                                     {"id": "L1", "species_symbol": "BBB", "image_url": "mock://l/1.jpg"}]})
    d("source.pool.freeze", {"pool": P2})
    l0 = s.cortex.get_meta(s._key("source:item:legacy2:L0")) or {}
    check(f"[{shape}] a pool imported without label_field leaves items with NO top-level label",
          l0.get("label") is None and (l0.get("source_metadata") or {}).get("species_symbol") == "AAA",
          str(l0.get("label")))
    # now stamp the pool's label_field on the FROZEN pool (the A34c non-clobbering repair)
    d("source.pool.create", {"name": P2, "label_field": "species_symbol"})
    d("bench.new", {"name": "legbench", "kind": "learning"})
    d("learning.dataset.bind", {"name": "legbench", "pool": P2})
    lab = lb._source_label("source:item:legacy2:L0", lb._pool_label_fields("legbench"))
    check(f"[{shape}] the resolver reads the class from source_metadata via the pool's label_field",
          lab == "AAA", f"resolved={lab}")

    # ── A40: the LIVE-VPS shape via the PACK LOADER. A pool imported by an OLD build WITHOUT
    #    label_field (its import sentinel already on disk), then the NEW build's pack NAMES label_field
    #    with the SAME data (same sha ⇒ same sentinel). The pre-sentinel re-stamp (A40a) must teach the
    #    frozen pool its label_field on the next boot despite the sentinel, and evaluate (A40b) must then
    #    score a NON-EMPTY frame using the label_key the model recorded at train. ──
    VPOOL = "source:pool:vps_images:v1"
    vdir = os.path.join(pack_dir, "vps")
    os.makedirs(vdir, exist_ok=True)

    def _vps_pack(with_label):
        pk = {"pool": VPOOL, "provider": "vps", "name": "vps", "rights": "CC0", "format": "jsonl",
              "data": "d.jsonl", "id_field": "id", "freeze": True, "rule": "vps images"}
        if with_label:
            pk["label_field"] = "species_symbol"
        json.dump(pk, open(os.path.join(vdir, "pack.json"), "w"))
        with open(os.path.join(vdir, "d.jsonl"), "w") as f:
            for i in range(18):
                f.write(json.dumps({"id": f"v{i}", "species_symbol": _CLASSES[i % 3],
                                    "image_url": f"mock://vps/{i}.jpg"}) + "\n")

    _vps_pack(with_label=False)                       # OLD build: no label_field
    bootstrap.source_packs_once(k)
    vm = s.cortex.get_meta(s._key(VPOOL)) or {}
    check(f"[{shape}] the old-build import froze the pool WITHOUT a label_field",
          vm.get("label_field") is None and (s.cortex.get_meta(s._key("source:item:vps:v0")) or {}).get("label") is None,
          str(vm.get("label_field")))
    _vps_pack(with_label=True)                        # NEW build: names label_field, SAME data ⇒ SAME sentinel
    bootstrap.source_packs_once(k)
    vm2 = s.cortex.get_meta(s._key(VPOOL)) or {}
    check(f"[{shape}] the frozen pool LEARNS label_field on the next boot despite the import sentinel",
          vm2.get("label_field") == "species_symbol", str(vm2.get("label_field")))
    d("bench.new", {"name": "vbench", "kind": "learning"})
    d("society.new", {"group": "lab", "name": "vsoc", "world": "default", "bench": "vbench", "kind": "cowork"})
    d("learning.dataset.bind", {"name": "vbench", "pool": VPOOL})
    d("learning.feature.extract", {"name": "vbench", "pool": VPOOL, "observers": "color", "run": "vr1"})
    vtr = d("learning.train", {"name": "vbench", "run": "vr1", "space": "color", "head": "logreg", "seed": "vs"})
    vmodel = vtr.get("model")
    vmm = s.cortex.get_meta(s._key(vmodel)) or {} if vmodel else {}
    check(f"[{shape}] train records the resolved label_key on the model meta (A40b)",
          vmm.get("label_key") == "species_symbol", str(vmm.get("label_key")))
    vev = d("learning.evaluate", {"name": "vbench", "model": vmodel, "sample": "test"})
    check(f"[{shape}] evaluate scores a NON-EMPTY frame (n>0) — b5 no longer scores an empty frame",
          vev.get("n", 0) > 0, str(vev)[:160])

    os.environ.pop("AKASHA_SOURCE_PACK_DIR", None)


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        os.environ.pop("AKASHA_SOURCE_PACK_DIR", None)
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a source pack's label_field reaches the learner: the importer hoists a "
          "top-level `label` onto each item AND records label_field on the pool, and learning.train/evaluate "
          "resolve the class through the declared join (source_metadata) with no label_key — on both "
          "cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
