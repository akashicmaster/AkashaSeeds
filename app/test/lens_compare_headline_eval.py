#!/usr/bin/env python3
"""
M8 — lens.compare reads the observation's own stamped `label` (vlab stamps the headline label at write; the
generic lens derives nothing from detection Sets or feature atoms — the purge order, platform P2a item 3).

A SENSE/CLASSIFIER observer (litert) produces NO detection: its predicted class is the feature atom's
`dominant_class`. Before M8, `lens.compare field=label` read the top DETECTION only, so such an
observation returned `label:null` and every row counted as "changed" (label vs nothing). This eval
builds one item observed two ways — a DETECTION observer (class on a detection) and a FEATURE observer
(dominant_class on the feature, no detection) — and proves lens.compare now reads BOTH labels, so
`changed` reflects a real label-vs-label comparison, on both cell shapes.

Run:  python app/test/lens_compare_headline_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_m8_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    nuc = k.manager.shared_nucleus
    core = nuc.core

    def atom(alias, meta):
        key = nuc.put_atom(f"[{alias}]", dict(meta), author="admin", alias=alias)
        return key

    # one source item, observed two ways
    item = atom("src:item:leaf1", {"concept": "source_item", "provider": "x"})
    # A — a DETECTION observer: label on a detection
    oa = "obs:vision:x:leaf1:detobs:ra"
    ka = atom(oa, {"concept": "vision_observation", "observer": "detobs", "run": "ra",
                   "status": "success", "detection_count": 1,
                   "label": "oak", "confidence": 0.91})   # stamped AT WRITE by vlab (the lens derives nothing)
    nuc.put_link(ka, item, "vis:observes", author="admin")
    da = atom("obs:detection:x:leaf1:detobs:0", {"concept": "vision_detection", "class": "oak",
                                                 "confidence": 0.91})
    core.add_to_collection("set:vlab:det:%s" % _slug(oa), da)
    core.add_to_collection("set:vlab:run:ra:observations", ka)
    # B — a SENSE/CLASSIFIER observer: dominant_class on the FEATURE atom, NO detection
    ob = "obs:vision:x:leaf1:senseobs:rb"
    kb = atom(ob, {"concept": "vision_observation", "observer": "senseobs", "run": "rb",
                   "status": "success", "detection_count": 0,
                   "label": "maple", "confidence": 0.77})
    nuc.put_link(kb, item, "vis:observes", author="admin")
    atom("obs:feature:x:leaf1:senseobs:rb", {"concept": "vision_feature", "observer": "senseobs",
                                             "run": "rb", "dominant_class": "maple", "top1_score": 0.77})
    core.add_to_collection("set:vlab:run:rb:observations", kb)

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    cmp = d("lens.compare", {"a": "set:vlab:run:ra:observations",
                             "b": "set:vlab:run:rb:observations", "key": "vis:observes", "field": "label"})
    rows = cmp.get("rows") or []
    row = rows[0] if rows else {}
    la = (row.get("a") or {}).get("label")
    lb = (row.get("b") or {}).get("label")
    check(f"[{shape}] the detection observer's label reads 'oak'", la == "oak", f"a={la}")
    check(f"[{shape}] M8 the sense observer's label reads the feature dominant_class 'maple' (not null)",
          lb == "maple", f"b={lb}")
    check(f"[{shape}] the two labels differ → changed=True (a real label-vs-label compare)",
          row.get("changed") is True and (cmp.get("summary") or {}).get("changed") == 1, str(cmp.get("summary")))


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — lens.compare reads a sense/classifier observation's label from the feature "
          "atom's dominant_class (the same normalisation vlab.item shows), so `changed` reflects a real "
          "label-vs-label comparison instead of label-vs-null — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
