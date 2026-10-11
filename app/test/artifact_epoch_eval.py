#!/usr/bin/env python3
"""
S1-a §1.4/§1.5 — a derived artifact is epoch-keyed; a superseded one reads `stale`.

The S1 invariant: *a materialized semantic horizon is an accelerator, never the source of semantic
truth.* A stored `lens.compare` aggregate (the first client) therefore carries `built_at_epoch` +
`artifact_id`; when its input Sets advance past that epoch it is a stale accelerator. This eval drives
it on BOTH cell shapes:

  • unit: artifact_id is stable and access-context-sensitive; is_stale fires only when inputs advance;
  • a stored diff carries built_at_epoch + artifact_id;
  • adding a NEW observation to an input run raises the input epoch ⇒ learning.runs.diffs reports
    `stale=true`; re-running lens.compare rebuilds it at the new epoch ⇒ `stale=false`.

Run:  python app/test/artifact_epoch_eval.py     (exit 0 = all pass)
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


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _unit():
    from lib.akasha.artifact_epoch import artifact_id, is_stale
    a1 = artifact_id(10, "universal", None, ["A", "B"], "lens.compare", "label", "member")
    a2 = artifact_id(10, "universal", None, ["B", "A"], "lens.compare", "label", "member")
    a3 = artifact_id(10, "universal", None, ["A", "B"], "lens.compare", "label", "guest")
    check("[unit] artifact_id is stable + input-order-independent", a1 == a2, "")
    check("[unit] artifact_id is access-context-sensitive (guest ≠ member)", a1 != a3, "")
    check("[unit] is_stale fires only when inputs advance",
          is_stale(10, 11) is True and is_stale(10, 10) is False and is_stale(11, 10) is False
          and is_stale(None, 5) is False, "")


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_epoch_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    core = k.manager.shared_nucleus.core
    d("world.genesis", {})
    d("bench.new", {"name": "leaf", "kind": "learning"})
    d("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = [{"id": f"img_{i}", "image": f"mock://leaf/{i}.jpg", "species_symbol": _CLASSES[i % 6]}
            for i in range(24)]
    d("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock", "label_field": "species_symbol"})
    d("source.acquire", {"source": "source:src:leafsrc", "rule": "mock", "records": recs,
                         "pool": "source:pool:leafimg:v1", "id_field": "id", "label_field": "species_symbol"})
    d("source.pool.freeze", {"pool": "source:pool:leafimg:v1"})
    tg = d("source.pool.sample", {"pool": "source:pool:leafimg:v1", "name": "target", "n": "12",
                                  "seed": "s1", "strata": "species_symbol"})
    d("learning.dataset.bind", {"name": "leaf", "pool": tg.get("sample"), "role": "target"})
    d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "mock", "run": "o0",
                        "branch": "plants_t2"})
    d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "color", "run": "o1",
                        "branch": "plants_t6"})
    run_a, run_b = "set:vlab:run:o0:observations", "set:vlab:run:o1:observations"

    def _file_diff():
        # `lens.compare` returns the stored key and files it nowhere; the observe.diff macro files it where
        # `learning.runs` reads it — so the eval files it the same way.
        for _s in ("set:vlab:compares", "set:wb:leaf:diffs"):
            d("set.add", {"name": _s, "id": "wb:leaf:diff:o0:o1"})

    # store a diff → it carries built_at_epoch + artifact_id
    cmp = d("lens.compare", {"a": run_a, "b": run_b, "key": "vis:observes",
                             "result": "wb:leaf:diff:o0:o1"})
    _file_diff()
    dm = core.get_chunk_raw(core.get_key_by_alias("wb:leaf:diff:o0:o1"))
    import json as _json
    meta = _json.loads(dm["meta"]) if dm and dm["meta"] else {}
    check(f"[{shape}] a stored diff carries built_at_epoch + artifact_id",
          meta.get("built_at_epoch") is not None and bool(meta.get("artifact_id")), str(meta.get("built_at_epoch")))
    _e0 = meta.get("built_at_epoch")
    _aid0 = meta.get("artifact_id")

    br = d("learning.runs", {"name": "leaf"})
    _diff = (br.get("diffs") or [{}])[0]
    check(f"[{shape}] a fresh diff reads stale=false", _diff.get("stale") is False, str(_diff.get("stale")))

    # advance an input Set: a NEW observation joins run o1 at a LATER coordinate (a fresh reading added
    # after the diff was built) → the inputs epoch rises above built_at_epoch
    nuc = k.manager.shared_nucleus
    _late = int(_e0) + 100
    nk = nuc.put_atom("[obs:vision:x:late:geometry:o1] later reading",
                      {"concept": "vision_observation", "observer": "geometry", "run": "o1",
                       "status": "success", "cronon": _late, "at_seq": _late},
                      author="admin", alias="obs:vision:x:late:geometry:o1")
    core.add_to_collection(run_b, nk)
    br2 = d("learning.runs", {"name": "leaf"})
    _diff2 = (br2.get("diffs") or [{}])[0]
    check(f"[{shape}] after an input advances, the stored diff reads stale=true",
          _diff2.get("stale") is True, f"stale={_diff2.get('stale')} built={_diff2.get('built_at_epoch')}")

    # rebuild the diff at the new epoch → stale clears, epoch advanced
    d("lens.compare", {"a": run_a, "b": run_b, "key": "vis:observes", "result": "wb:leaf:diff:o0:o1"})
    _file_diff()
    dm2 = core.get_chunk_raw(core.get_key_by_alias("wb:leaf:diff:o0:o1"))
    meta2 = _json.loads(dm2["meta"]) if dm2 and dm2["meta"] else {}
    br3 = d("learning.runs", {"name": "leaf"})
    _diff3 = (br3.get("diffs") or [{}])[0]
    check(f"[{shape}] rebuilding lens.compare advances built_at_epoch and clears stale",
          meta2.get("built_at_epoch") is not None and meta2.get("built_at_epoch") >= _e0
          and _diff3.get("stale") is False, f"e0={_e0} e1={meta2.get('built_at_epoch')} stale={_diff3.get('stale')}")

    # ── M2-b — an OLD (pre-epoch) twin diff for the same (a,b) is collapsed: learning.runs.diffs returns
    #    ONE row per pair (the newest), the older alias travels as `superseded` ──
    old_alias = "wb:plants-vision:diff:o0:o1"   # a hyphen-aliased pre-epoch twin, same (a,b)
    ok_old = nuc.put_atom("[%s] legacy diff" % old_alias,
                          {"concept": "lens_compare", "a": run_a, "b": run_b,
                           "items": 12, "changed": 12}, author="admin", alias=old_alias)
    core.add_to_collection("set:wb:leaf:diffs", ok_old)   # both twins now in the bench diffs Set
    br4 = d("learning.runs", {"name": "leaf"})
    _pair = [dd for dd in (br4.get("diffs") or [])
             if dd.get("a") == run_a and dd.get("b") == run_b]
    check(f"[{shape}] M2-b learning.runs.diffs returns ONE row per pair (newest), old as superseded",
          len(_pair) == 1 and (_pair[0].get("built_at_epoch") is not None)
          and old_alias in (_pair[0].get("superseded") or []),
          f"rows={len(_pair)} superseded={(_pair[0].get('superseded') if _pair else None)}")


def main():
    _unit()
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a stored lens.compare aggregate is epoch-keyed (built_at_epoch + artifact_id, "
          "access-context-sensitive); when an input Set advances past its epoch learning.runs.diffs reads "
          "stale=true, and rebuilding it clears stale at the new epoch — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
