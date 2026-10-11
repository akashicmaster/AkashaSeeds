#!/usr/bin/env python3
"""
blvh_import.py — generate app/ontology/blvh/blvh_sampling.ak from the sampling manifest CSV.

The v0.2 manifest is a SAMPLING PLAN (100 slots, status TO_SELECT — no images selected yet). Per the
spec "selection itself is an observation and must be traceable", each slot is ingested as a
sampling_operation atom carrying its plan fields, linked into its candidate-set + the operation that
would perform the selection (SigLIP2 retrieval for historical; the RF-DETR mask rule for
ambiguity/control), and added to the operational sets. Re-run after editing the manifest; the .ak is
content-addressed so a re-load is idempotent.

    python app/scripts/blvh_import.py
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "app", "ontology", "blvh", "SAMPLING_MANIFEST_v0_2.csv")
OUT = os.path.join(ROOT, "app", "ontology", "blvh", "blvh_sampling.ak")


def _clean(s):
    return (s or "").replace('"', "'").replace("\n", " ").strip()


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    lines = [
        "# British Library Visual Hypothesis Corpus v0.2 — sampling operations (GENERATED).",
        "# Source: app/ontology/blvh/SAMPLING_MANIFEST_v0_2.csv via app/scripts/blvh_import.py — do not edit by hand.",
        "# Each slot is a sampling_operation observation (selection is traceable, spec §10). v0.2 status is",
        "# TO_SELECT for every slot — no image is selected yet; when one is, an image atom links to its",
        "# slot with blvh:selected_by and the slot's status advances.",
        "",
    ]
    # model that each candidate set's selection method leans on (provenance of the operation)
    gen_by = {"historical": "blvh:model:siglip2_so400m",
              "ambiguity": "blvh:model:rfdetr_crop_tighten",
              "control": "blvh:model:rfdetr_crop_tighten"}
    for r in rows:
        slot = _clean(r["slot"])
        cset = _clean(r["candidate_set"])
        sid = f"blvh:slot:{slot}"
        desc = (f"sampling_operation; slot={slot}; candidate_set={cset}; subgroup={_clean(r['subgroup'])}; "
                f"target_period={_clean(r['target_period'])}; query_pool={_clean(r['semantic_query_pool'])}; "
                f"mask_rule={_clean(r['mask_rule'])}; book_cap={_clean(r['book_cap'])}; "
                f"selection_method={_clean(r['selection_method'])}; required_provenance={_clean(r['required_provenance'])}; "
                f"status={_clean(r['status'])}; sampling_version=blvh-0.2. "
                f"observation_status=machine_selection_plan; NEVER promote the semantic query to a factual subject label.")
        lines.append(f'def "{sid}" "{desc}"')
        lines.append(f'ln {sid} blvh:sample:{cset} sys:part_of')
        model = gen_by.get(cset)
        if model:
            lines.append(f'ln {sid} {model} blvh:generated_by')
        lines.append(f'set.add name="blvh:sampling_operations" id="{sid}"')
        lines.append(f'set.add name="blvh:sample:{cset}" id="{sid}"')
        lines.append(f'set.add name="blvh:sample:v0_2" id="{sid}"')
        lines.append(f'set.add name="blvh:status:{_clean(r["status"]).lower()}" id="{sid}"')
        lines.append(f'set.add name="blvh:all" id="{sid}"')
        lines.append("")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {OUT}: {len(rows)} sampling operations")


if __name__ == "__main__":
    main()
