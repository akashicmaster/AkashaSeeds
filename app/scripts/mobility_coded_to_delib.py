#!/usr/bin/env python3
"""
mobility_coded_to_delib.py — the coded-field → stance MAPPING LAYER (converter half).

Projects coded attitude items of the EU Travel Survey 2014 respondent corpus into delib-ingestable
records, under a DECLARED mapping spec (app/config/mobility_stance_map.json). This is the "different
design" flagged in docs/for-llm/consensus-mobility-regen-instructions.md — coded survey answers
treated as opinions — kept honest by construction:

  • the mapping is DATA (the spec), never code: every code→stance reading is inspectable, versioned,
    and disputable; the converter only applies it;
  • the record's `text` is the VERBATIM coded answer (label or code) — no opinion sentence is ever
    synthesized; the survey item's proposition is the survey question, not record text;
  • every record carries `stance` + `stance_basis` (= "map:<spec>@<version>:<field>"), which delib
    stores as first-class delib:mapped_stance / delib:mapped_by links — a mapped voice is ALWAYS
    distinguishable from a read free-text voice (delib.aggregate reports via_mapping; delib.voices
    carries via_mapping + mapping_rule per voice);
  • codes the spec declares unreadable ("Don't know", "No preferences") become stance=no_reading:
    counted and visible in their own group, but no cluster, no trajectory, no conclusion;
  • an answer VALUE the spec has no reading for is reported (unmapped) and NOT emitted with a stance
    guess — the converter refuses to invent a reading (they are listed in the summary).

One survey item = one proposition = ONE output JSONL (a delib survey aggregates one question).

Usage:
  python app/scripts/mobility_coded_to_delib.py \
      --records mob_data/respondents.jsonl \
      --map app/config/mobility_stance_map.json \
      --item Preference_tolls_or_traffic_limitation \
      --out mobility_tolls_stance.jsonl [--limit N]

Then (throwaway-cell pipeline + projection files, same as free-text):
  python app/scripts/mobility_lab.py --feedback mobility_tolls_stance.jsonl --emit-projection <dir>
"""
import argparse
import json
import sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True, help="respondents JSONL (verbatim fetch output)")
    ap.add_argument("--map", dest="mapfile", default="app/config/mobility_stance_map.json",
                    help="the declared mapping spec (default app/config/mobility_stance_map.json)")
    ap.add_argument("--item", required=True, help="the survey field to project (one item = one run)")
    ap.add_argument("--out", required=True, help="output JSONL of delib records")
    ap.add_argument("--limit", type=int, default=0, help="cap respondents (0 = all)")
    args = ap.parse_args()

    with open(args.mapfile, encoding="utf-8") as fh:
        spec = json.load(fh)
    item = next((i for i in spec.get("items", []) if i.get("field") == args.item), None)
    if not item:
        print(f"[!] item '{args.item}' is not declared in {args.mapfile} — "
              f"declared: {[i.get('field') for i in spec.get('items', [])]}", file=sys.stderr)
        sys.exit(3)
    readings = item.get("readings") or {}
    basis = f"map:{spec.get('spec')}@{spec.get('version')}:{args.item}"

    emitted = 0
    counts = {}
    unmapped = {}
    with open(args.records, encoding="utf-8") as fin, open(args.out, "w", encoding="utf-8") as fout:
        for n, line in enumerate(fin):
            if args.limit and emitted >= args.limit:
                break
            if not line.strip():
                continue
            row = json.loads(line)
            raw = str(row.get(args.item, "")).strip()
            if not raw:
                continue
            stance = readings.get(raw)
            if stance is None:
                unmapped[raw] = unmapped.get(raw, 0) + 1     # refused: no reading invented
                continue
            rid = str(row.get("respondent_id") or row.get("ID") or f"row{n}")
            rec = {
                "respondent_id": f"{rid}:{args.item}",
                # the OPERAND is the verbatim coded answer — never a synthesized opinion sentence
                "text": raw,
                "language": "en",
                "stance": stance,
                "stance_basis": basis,
                # provenance passthrough (country mirrors the Source-layer stratification key)
                "country": row.get("country") or row.get("Country") or "",
                "source_row": row.get("row_coordinate", ""),
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            emitted += 1
            counts[stance] = counts.get(stance, 0) + 1

    print(f"  spec       : {basis}")
    print(f"  proposition: {item.get('proposition')}")
    print(f"  emitted    : {emitted} records → {args.out}")
    print(f"  by stance  : {counts}")
    if unmapped:
        print(f"  UNMAPPED (no declared reading — NOT emitted, extend the spec if these should read):")
        for v, c in sorted(unmapped.items(), key=lambda kv: -kv[1]):
            print(f"    {c:6d} × {v!r}")
    print(f"\n  next: python app/scripts/mobility_lab.py --feedback {args.out} --emit-projection <dir>")
    print(f"        (survey question = the proposition above; delib stores the mapped stance +")
    print(f"         rule as delib:mapped_stance / delib:mapped_by — never lexicon-read)")

if __name__ == "__main__":
    main()
