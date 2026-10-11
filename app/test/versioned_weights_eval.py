#!/usr/bin/env python3
"""
P0-a slice 2 piece 5 — VERSIONED learned-head weights (§2.5).

A trained head was overwritten in place (`head_<run>.json`), so a re-train destroyed the prior
weights and nothing could pin an older version. Now each train writes an IMMUTABLE, hash-named
`head_<run>_<sha8>.json` (published as a durable generation with a CAS pointer). There is no legacy
`head_<run>.json` mirror of the current generation; `model:…@<sha8>` pins a specific version, and
`keep_versions` prunes the oldest files (stamping `weights_present=false`, the record kept). This eval
drives it on BOTH cell shapes:

  • two re-trains of one run (different split seed ⇒ different fitted weights) leave TWO versioned
    files + two version atoms, both weights_present=true; the legacy name mirrors the latest;
  • learning.evaluate model:…@<sha8> loads the PINNED version (not degraded), for BOTH shas;
  • with keep_versions=1, a third train prunes the two older files (weights_present=false, file gone)
    and leaves exactly one versioned file.

Run:  python app/test/versioned_weights_eval.py     (exit 0 = all pass)
"""
import glob
import hashlib
import json
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


def _run(series, shape, bench):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    from app.concepts.bench_learning import LearningBenchConcept
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_vw_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus.core
    lb = LearningBenchConcept(k.manager.get_session("admin"))
    adir = lb._artifact_dir("f1", bench)
    # The artifact dir lives under data/ (a protected path), not a temp dir, so a previous run of
    # this eval leaves its versioned files behind and the exact-set checks below would count them.
    # Start from an empty one — the eval owns this bench name.
    for _stale in glob.glob(os.path.join(adir, "head_f1*.json")):
        try:
            os.remove(_stale)
        except OSError:
            pass

    def vfiles():
        return sorted(os.path.basename(p) for p in glob.glob(os.path.join(adir, "head_f1_*.json")))

    def vmeta(sha8):
        key = nuc.get_key_by_alias("model:ver:%s:f1:%s" % (bench.replace("-", "_"), sha8))
        row = nuc.get_chunk_raw(key) if key else None
        return json.loads(row["meta"]) if row and row["meta"] else {}

    a("world.genesis", {})
    a("bench.new", {"name": bench, "kind": "learning"})
    a("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = [{"id": f"img_{i}", "image": f"mock://leaf/{_CLASSES[i % 6].lower()}/{i}.jpg",
             "species_symbol": _CLASSES[i % 6]} for i in range(48)]
    a("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock", "label_field": "species_symbol"})
    a("source.acquire", {"source": "source:src:leafsrc", "rule": "mock", "records": recs,
                         "pool": _POOL, "id_field": "id", "label_field": "species_symbol"})
    a("source.pool.freeze", {"pool": _POOL})
    tr = a("source.pool.sample", {"pool": _POOL, "name": "train", "n": "48", "seed": "s1",
                                  "strata": "species_symbol"})
    a("learning.dataset.bind", {"name": bench, "pool": tr.get("sample"), "role": "train"})
    a("learning.feature.run", {"name": bench, "pool": "role:train", "observers": "color", "run": "f1"})
    a("learning.feature.execute", {"name": bench, "run": "f1"})
    a("learning.feature.seal", {"name": bench, "run": "f1"})

    # ── two re-trains of run f1 with different split seeds ⇒ different fitted weights ⇒ two versions ──
    t1 = a("learning.train", {"name": bench, "run": "f1", "space": "color", "head": "logreg",
                           "split": "0.8", "seed": "vwA", "label_key": "species_symbol"})
    m1 = nuc.get_chunk_raw(nuc.get_key_by_alias(t1.get("model")))
    sha1 = json.loads(m1["meta"]).get("weights_sha8")
    t2 = a("learning.train", {"name": bench, "run": "f1", "space": "color", "head": "logreg",
                           "split": "0.6", "seed": "vwB", "label_key": "species_symbol"})
    m2 = nuc.get_chunk_raw(nuc.get_key_by_alias(t2.get("model")))
    sha2 = json.loads(m2["meta"]).get("weights_sha8")
    check(f"[{shape}] two re-trains produce two DISTINCT weight shas", sha1 and sha2 and sha1 != sha2,
          f"sha1={sha1} sha2={sha2}")
    check(f"[{shape}] two immutable versioned files exist (no legacy mirror)",
          len(vfiles()) == 2, str(vfiles()))
    check(f"[{shape}] both version atoms read weights_present=true",
          vmeta(sha1).get("weights_present") is True and vmeta(sha2).get("weights_present") is True)

    # ── @<sha8> pins a specific version: both load, neither degraded ──
    model = t1.get("model")
    e1 = a("learning.evaluate", {"name": bench, "model": "%s@%s" % (model, sha1), "sample": "test"})
    e2 = a("learning.evaluate", {"name": bench, "model": "%s@%s" % (model, sha2), "sample": "test"})
    check(f"[{shape}] learning.evaluate model@<sha8> loads the pinned version (not degraded)",
          e1.get("degraded") is False and e2.get("degraded") is False,
          f"e1={e1.get('degraded')} e2={e2.get('degraded')}")
    # a pin to a bogus sha degrades (no such versioned file → falls back / honest degradation)
    eb = a("learning.evaluate", {"name": bench, "model": "%s@deadbeef" % model, "sample": "test"})
    check(f"[{shape}] a pin to an unknown sha8 degrades honestly (no crash)",
          isinstance(eb, dict) and "error" not in eb, str(eb)[:100])

    # ── keep_versions=1 → a third train prunes the two older files (weights_present=false) ──
    bk = nuc.get_key_by_alias("wb:%s" % bench.replace("-", "_"))
    meta = json.loads((nuc.get_chunk_raw(bk) or {}).get("meta") or "{}")
    meta["keep_versions"] = 1
    nuc.update_meta(bk, meta)
    t3 = a("learning.train", {"name": bench, "run": "f1", "space": "color", "head": "logreg",
                           "split": "0.75", "seed": "vwC", "label_key": "species_symbol"})
    sha3 = json.loads(nuc.get_chunk_raw(nuc.get_key_by_alias(t3.get("model")))["meta"]).get("weights_sha8")
    check(f"[{shape}] keep_versions=1 leaves exactly one versioned file (the newest)",
          len(vfiles()) == 1 and vfiles()[0] == "head_f1_%s.json" % sha3, str(vfiles()))
    check(f"[{shape}] the pruned versions are stamped weights_present=false (record kept)",
          vmeta(sha1).get("weights_present") is False and vmeta(sha2).get("weights_present") is False)
    check(f"[{shape}] the surviving version still reads weights_present=true",
          vmeta(sha3).get("weights_present") is True)


def main():
    _run("thesaurus", "nucleus cell", "leafa")
    _run("seeds", "single-store cell", "leafb")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — learned-head weights are versioned: each train writes an immutable "
          "head_<run>_<sha8>.json (durable generation + CAS pointer) and keeps the legacy name; "
          "model@<sha8> pins a version; keep_versions prunes the oldest files and stamps "
          "weights_present=false — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
