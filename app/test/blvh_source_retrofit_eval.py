#!/usr/bin/env python3
"""
blvh × Source Data Layer retrofit eval — Spec v0.3 §11/§24 (blvh is the first consumer of the layer).

Loads the app/ontology/blvh pack in-process, then runs the retrofit FLOW through the CLI-first `source.*`
operators (the same ops app/scripts/blvh_source_retrofit.py drives against a live cell) with a bounded
set of BL-shaped test rows, and asserts the corpus is now evidence-grounded:

  - a SEPARATE raw image pool is acquired and frozen (the 100 blvh:slot:* do NOT constitute the raw
    corpus by definition — the pool is source:item:*, not the sampling operations);
  - blvh is declared a CORPUS lab that samples_from the frozen pool;
  - a slot's selection is an ADDITIVE bridge to a raw item (the raw atom is never mutated);
  - the bridge traces both ways (slot → raw item, raw item → slot);
  - the audit reports blvh grounded, with the selection traceable to the frame.

Run:  python app/test/blvh_source_retrofit_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import re
import shlex
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    PACK = os.path.join(ROOT, "app", "ontology", "blvh")
    if not os.path.isdir(PACK):
        print("  SKIP  blvh pack not in this extraction (tier-C, seeds line) — nothing to retrofit")
        sys.exit(0)

    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_blvhsrc_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # ── load the blvh pack's .ak (so the 100 sampling operations exist to bridge) ──
    for fn in ("_lexicon.ak", "blvh_skeleton.ak", "blvh_sampling.ak"):
        for raw in open(os.path.join(PACK, fn), encoding="utf-8"):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("def "):
                p = shlex.split(line)
                if len(p) >= 3:
                    d("define", {"name": p[1], "description": p[2]})
            elif line.startswith("ln "):
                p = line.split()
                if len(p) >= 4:
                    d("ln", {"src": p[1], "dst": p[2], "rel": p[3]})
            elif line.startswith("set.add"):
                nm = re.search(r'name="([^"]+)"', line)
                idm = re.search(r'id="([^"]+)"', line)
                if nm and idm:
                    d("set.add", {"name": nm.group(1), "id": idm.group(1)})

    check("pre: the blvh sampling operations loaded (slot:001 exists to bridge)",
          bool((d("read", {"id": "blvh:slot:001"}) or {}).get("content")))

    # ── 1. register the BL source + acquire a bounded raw image pool (SEPARATE from the 100 slots) ──
    d("source.register", {"provider": "British Library", "collection": "book images", "name": "bl",
                          "rights": "Public Domain Mark / CC0-1.0 dataset tag"})
    rows = [{"id": f"plates:train:{100 + i}", "config": "plates", "split": "train",
             "row_index": 100 + i, "dataset_id": "biglam/british-library-book-images",
             "media_type": "image/jpeg", "url": f"https://datasets-server.huggingface.co/rows?offset={100 + i}"}
            for i in range(12)]
    d("source.pool.create", {"name": "bl_visual_raw", "source": "source:src:bl", "version": "v1",
                             "rule": "bounded BL plates/train raw image pool, acquired before selection"})
    acq = d("source.acquire", {"source": "source:src:bl", "rule": "BL plates raw images (n=12)",
                               "records": rows, "id_field": "id", "pool": "source:pool:bl_visual_raw:v1"})
    check("acquire: a SEPARATE raw image pool is acquired (12 raw items, distinct from the 100 slots)",
          acq.get("acquired") == 12, str(acq.get("acquired")))

    # ── 2. §11 — the raw pool is NOT the 100 sampling operations (source:item:* vs blvh:slot:*) ──
    lsp = d("source.pool.ls", {"pool": "source:pool:bl_visual_raw:v1"})
    members = [m.get("item") for m in (lsp.get("members") or [])]
    check("separation: the raw pool holds source:item:* raw atoms, NOT blvh:slot:* sampling operations",
          all((m or "").startswith("source:item:") for m in members) and lsp.get("count") == 12,
          str(lsp.get("count")))

    # ── 3. freeze → immutable versioned sampling frame ──
    fr = d("source.pool.freeze", {"pool": "source:pool:bl_visual_raw:v1"})
    check("freeze: bl_visual_raw_v1 is FROZEN with an Akasha-Time marker",
          fr.get("status") == "FROZEN" and isinstance(fr.get("at_seq"), int), str(fr))
    pool_at = fr["at_seq"]

    # ── 4. declare blvh CORPUS + the sampling-frame link (lab samples_from pool) ──
    decl = d("source.lab.declare", {"lab": "blvh", "klass": "CORPUS",
                                    "pool": "source:pool:bl_visual_raw:v1", "primary_source": "source:src:bl"})
    check("declare: blvh is a CORPUS lab GROUNDED on the frozen pool (samples_from the frame)",
          decl.get("acquisition_class") == "CORPUS" and decl.get("evidence_status") == "GROUNDED", str(decl))

    # ── 5. a slot's selection is an ADDITIVE bridge to a raw item (raw atom unchanged) ──
    raw_item = "source:item:bl:plates_train_105"
    before = d("source.read", {"id": raw_item})
    br = d("source.bridge", {"src": "blvh:slot:001", "dst": raw_item, "rel": "selected_from",
                             "by": "blvh:model:siglip2_so400m", "run": "blvh-0.3"})
    after = d("source.read", {"id": raw_item})
    check("bridge: slot:001 --selected_from--> a raw item, additively (the raw atom is unchanged)",
          isinstance(br, dict) and "__error__" not in br
          and before.get("source_metadata") == after.get("source_metadata"), str(br)[:100])
    check("Akasha Time: the pool was frozen BEFORE the selection bridge",
          isinstance(br.get("at_seq"), int) and br["at_seq"] > pool_at,
          f"pool_at={pool_at} bridge_at={br.get('at_seq')}")

    # ── 6. the bridge traces BOTH ways without collapsing the reading into the source ──
    t_slot = d("source.trace", {"id": "blvh:slot:001"})
    t_item = d("source.trace", {"id": raw_item})
    check("trace (slot → source): slot:001 resolves to its selected raw item",
          raw_item in {s.get("source_item") for s in t_slot.get("sources", [])}, str(t_slot.get("sources")))
    check("trace (source → interpretations): the raw item lists blvh:slot:001 as selected_from",
          ("blvh:slot:001", "selected_from") in
          {(i.get("interpreted"), i.get("relation")) for i in t_item.get("interpretations", [])},
          str(t_item.get("interpretations")))

    # ── 7. audit — blvh is now evidence-grounded with results traceable to the frame ──
    au = d("source.audit", {"lab": "blvh"})
    check("audit: blvh is grounded — frozen frame + at least one selection bridged into it",
          au.get("grounded") is True and au.get("bridged", 0) >= 1, str(au))

    # ── 8. the retrofit script is importable/parseable (the CLI entry the operator runs) ──
    import importlib.util
    spec = importlib.util.spec_from_file_location("blvh_source_retrofit",
                                                  os.path.join(ROOT, "app/scripts", "blvh_source_retrofit.py"))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        script_ok = hasattr(mod, "main") and mod.POOL == "source:pool:bl_visual_raw:v1"
    except Exception as exc:
        script_ok = False
        print("   script import error:", exc)
    check("script: app/scripts/blvh_source_retrofit.py loads and targets the same pool/ops", script_ok)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — blvh retrofit: a separate bounded raw image pool is acquired and frozen as "
          "bl_visual_raw_v1, blvh is declared a CORPUS lab that samples_from it, a slot's selection "
          "bridges additively to a raw item (traceable both ways, raw atom unmutated, pool frozen "
          "before the selection), and the audit reports blvh grounded.")
    sys.exit(0)


if __name__ == "__main__":
    main()
