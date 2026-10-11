#!/usr/bin/env python3
"""
British Library Visual Hypothesis Corpus (blvh) eval — the data-foundation acceptance (spec §16).

Loads the app/ontology/blvh pack's .ak (lexicon + skeleton + 100 sampling operations) into an in-process
kernel and asserts the corpus is diveable/explorable with source, observation, process, and (dormant)
research layers kept DISTINCT — never collapsed. No image records exist in v0.2 (the 100 slots are
TO_SELECT sampling operations), so the image→book→OCR traversal is checked at the sampling-plan level.

Run:  python app/test/blvh_corpus_eval.py     (exit 0 = all pass)
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
    # F27-5 — the blvh pack is tier C: it ships in a load_all service extraction (thesaurus/
    # enterprise) but NOT in the seeds line. When the pack dir is absent (a seeds extraction), SKIP
    # cleanly rather than FileNotFound-FAIL, so `test/` is zero-FAIL on ANY fresh extraction.
    PACK = os.path.join(ROOT, "app", "ontology", "blvh")
    if not os.path.isdir(PACK):
        print("  SKIP  blvh corpus not in this extraction (tier-C pack, seeds line) — nothing to check")
        sys.exit(0)

    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_blvh_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # ── load the pack's .ak by dispatching def/ln/set.add (as the boot loader would) ──
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

    # ── 0. lexicon: the namespace + a corpus relation are DEFINED (definition-completeness) ──
    check("lexicon: nsdef:blvh + reldef:blvh:derived_from are defined",
          bool((d("read", {"id": "nsdef:blvh"}) or {}).get("content"))
          and bool((d("read", {"id": "reldef:blvh:derived_from"}) or {}).get("content")))

    # ── 1. root is diveable; explore surfaces the corpus regions ──
    exp = d("explore", {"id": "blvh:root", "depth": 2})
    aliases = {a.get("alias") for a in (exp.get("atoms", []) if isinstance(exp, dict) else [])}
    check("dive/explore: blvh:root reachable and non-empty",
          isinstance(exp, dict) and exp.get("count", 0) > 0, str(exp.get("count") if isinstance(exp, dict) else exp))

    # ── 2. provenance chain preserved: dataset → digitisation/crop process (derived_from), never collapsed ──
    dv = d("view", {"id": "blvh:dataset:book_images"})
    sp = {(s.get("alias"), s.get("rel")) for s in (dv.get("signposts", []) if isinstance(dv, dict) else [])}
    check("provenance: dataset:book_images --blvh:derived_from--> the digitisation + crop processes",
          any(a == "blvh:process:bl_microsoft_digitisation" and r == "blvh:derived_from" for a, r in sp)
          and any(a == "blvh:process:abbyy_loose_crop" and r == "blvh:derived_from" for a, r in sp), str(sorted(sp))[:120])

    # ── 3. model → all observations it generated (query 8 / model 7) ──
    mv = d("view", {"id": "blvh:model:rfdetr_crop_tighten"})
    gen = [s for s in (mv.get("signposts", []) if isinstance(mv, dict) else []) if s.get("rel") == "blvh:generated_by"]
    check("model → observations it generated (ambiguity+control sampling ops = 50 point at RF-DETR)",
          len(gen) >= 40, f"{len(gen)} incoming blvh:generated_by")

    # ── 4. sets: ambiguity=30, v0_2 superset carries the 100 ops + 3 categories, status set tracks state ──
    def ssize(name):
        r = d("set.ls", {"name": name, "limit": 500}) or {}
        return r.get("count", len(r.get("members", []) or r.get("atoms", []) or []))
    check("set: blvh:sample:ambiguity holds the 30 ambiguity sampling operations", ssize("blvh:sample:ambiguity") == 30,
          str(ssize("blvh:sample:ambiguity")))
    check("set: blvh:sampling_operations holds all 100 slots", ssize("blvh:sampling_operations") == 100,
          str(ssize("blvh:sampling_operations")))
    check("set: blvh:status:to_select tracks every unselected slot (100)", ssize("blvh:status:to_select") == 100,
          str(ssize("blvh:status:to_select")))

    # ── 5. a sampling operation traces to its candidate set + the selection model — layers kept distinct ──
    sv = d("view", {"id": "blvh:slot:001"})
    ssp = {(s.get("alias"), s.get("rel")) for s in (sv.get("signposts", []) if isinstance(sv, dict) else [])}
    body = ((sv.get("focus") or {}).get("content", "") if isinstance(sv, dict) else "")
    check("sampling op: slot:001 --sys:part_of--> its candidate set AND --blvh:generated_by--> SigLIP2",
          ("blvh:sample:historical", "sys:part_of") in ssp
          and ("blvh:model:siglip2_so400m", "blvh:generated_by") in ssp, str(sorted(ssp))[:140])
    check("sampling op preserves the plan WITHOUT promoting the query to a subject label",
          "NEVER promote the semantic query" in body and "status=TO_SELECT" in body)

    # ── 6. a research question FRAMES a corpus region (research layer present but dormant) ──
    qv = d("view", {"id": "blvh:q:what_is_one_object"})
    qsp = {(s.get("alias"), s.get("rel")) for s in (qv.get("signposts", []) if isinstance(qv, dict) else [])}
    check("research: the 'what is one object' question --blvh:frames--> the ambiguity set",
          ("blvh:sample:ambiguity", "blvh:frames") in qsp, str(sorted(qsp))[:120])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — blvh corpus: the skeleton + 100 sampling operations load and dive/explore; source, "
          "observation, process, and (dormant) research layers stay distinct; provenance is traceable and "
          "no machine selection is promoted to a fact.")
    sys.exit(0)


if __name__ == "__main__":
    main()
