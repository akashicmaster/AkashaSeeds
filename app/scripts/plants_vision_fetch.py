#!/usr/bin/env python3
"""
plants_vision_fetch.py — B1 (species selection) + B2 (image-REFERENCE acquisition) for the
PLANTS vision-learning experiment (docs/for-llm/plants-vision-learning-plan.md).

B1 declared rule (recorded in the manifest): take iNaturalist's Plantae species ranked by count of
research-grade observations carrying CC0/CC-BY photos, intersect with the USDA PLANTS checklist
accepted names (binomial match), and keep the TOP N_SPECIES present in both. Hypothesis-free:
popularity of photographic evidence only.

B2: for each selected species, up to N_PER research-grade observations (order_by=votes — a declared
quality proxy), ONE photo per observation (observer diversity), license restricted to CC0/CC-BY,
emitting URL REFERENCES ONLY (medium size) + verbatim license/attribution. NO image binary is
downloaded here or ever stored (the standing image law).

Usage:
  python app/scripts/plants_vision_fetch.py [--checklist plants_data/checklist.jsonl]
      [--species 20] [--per 50] [--out-dir plants_data/vision]
"""
import argparse
import gzip
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.inaturalist.org/v1"
PLANTAE = 47126
BUNDLE_DIR = os.path.join(ROOT, "app", "assets", "plants_vision")


def _get(path, **params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checklist", default="plants_data/checklist.jsonl")
    ap.add_argument("--species", type=int, default=20)
    ap.add_argument("--per", type=int, default=50)
    ap.add_argument("--out-dir", default="plants_data/vision")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    # binomial → PLANTS symbol (unique binomials only — an ambiguous binomial cannot label)
    binom = {}
    dupes = set()
    for line in open(args.checklist, encoding="utf-8"):
        r = json.loads(line)
        parts = r["scientific_name"].split()
        if len(parts) < 2 or not parts[1][0].islower():
            continue                      # genus-level or hybrid formats — not a clean binomial
        b = f"{parts[0]} {parts[1]}"
        if b in binom and binom[b]["symbol"] != r["symbol"]:
            dupes.add(b)
        binom[b] = r
    for b in dupes:
        binom.pop(b, None)

    print(f"  checklist binomials: {len(binom):,} (ambiguous dropped: {len(dupes)})")
    print("  [B1] ranking Plantae by research-grade CC0/CC-BY-photo observations…")
    ranked = _get("observations/species_counts", taxon_id=PLANTAE, quality_grade="research",
                  photo_license="cc0,cc-by", per_page=200).get("results", [])
    chosen = []
    for row in ranked:
        t = row["taxon"]
        rec = binom.get(t["name"])
        if not rec:
            continue
        chosen.append({"symbol": rec["symbol"], "binomial": t["name"], "taxon_id": t["id"],
                       "common_name": rec["common_name"] or t.get("preferred_common_name") or "",
                       "family": rec["family"], "inat_cc_research_count": row["count"]})
        if len(chosen) >= args.species:
            break
    if len(chosen) < args.species:
        print(f"[!] only matched {len(chosen)} species — extend per_page", file=sys.stderr)
        sys.exit(3)
    for c in chosen:
        print(f"      {c['symbol']:8s} {c['binomial']:32s} {c['inat_cc_research_count']:6d} obs")

    print(f"  [B2] fetching up to {args.per} photo references per species…")
    records = []
    per_species = {}
    for c in chosen:
        got = 0
        page = 1
        while got < args.per and page <= 4:
            obs = _get("observations", taxon_id=c["taxon_id"], quality_grade="research",
                       photo_license="cc0,cc-by", per_page=100, page=page,
                       order_by="votes").get("results", [])
            if not obs:
                break
            for o in obs:
                if got >= args.per:
                    break
                photo = next((p["photo"] for p in (o.get("observation_photos") or [])
                              if (p.get("photo") or {}).get("license_code") in ("cc0", "cc-by")
                              and (p.get("photo") or {}).get("url")), None)
                if not photo:
                    continue
                records.append({
                    "id": f"{o['id']}_{photo['id']}",
                    "species_symbol": c["symbol"], "binomial": c["binomial"],
                    "family": c["family"], "taxon_id": c["taxon_id"],
                    "image_url": photo["url"].replace("square", "medium"),
                    "license_code": photo.get("license_code"),
                    "attribution": photo.get("attribution") or "",
                    "observer": ((o.get("user") or {}).get("login")) or "",
                    "observed_on": o.get("observed_on") or "",
                    "observation_url": f"https://www.inaturalist.org/observations/{o['id']}",
                })
                got += 1
            page += 1
            time.sleep(1.0)               # polite paging
        per_species[c["symbol"]] = got
        print(f"      {c['symbol']:8s} {got} photo refs")

    out = os.path.join(args.out_dir, "records.jsonl")
    with open(out, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    manifest = {
        "provider": "iNaturalist (research-grade community observations)",
        "collection": "PLANTS vision-learning corpus — CC0/CC-BY photo references",
        "api": API, "snapshot_date": date.today().isoformat(),
        "selection_rule": ("B1: top-N Plantae species by count of research-grade observations with "
                           "CC0/CC-BY photos on iNaturalist, intersected with USDA PLANTS accepted "
                           "binomials (ambiguous binomials excluded); B2: per species up to N_PER "
                           "observations ordered by votes, ONE CC0/CC-BY photo each (observer "
                           "diversity), medium-size URL reference only — no binary."),
        "n_species": args.species, "n_per_species": args.per,
        "species": chosen, "per_species_counts": per_species, "total_records": len(records),
        "rights": "per-record CC0 or CC-BY (license_code + attribution kept verbatim)",
    }
    with open(os.path.join(args.out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    os.makedirs(BUNDLE_DIR, exist_ok=True)
    with gzip.open(os.path.join(BUNDLE_DIR, "records.jsonl.gz"), "wt", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(BUNDLE_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(f"  wrote {len(records)} records → {out}")
    print(f"  DEPLOY BUNDLE → {BUNDLE_DIR}/")
    print(f"\n  next: python app/scripts/plants_vision_import.py --as <admin_id>")


if __name__ == "__main__":
    main()
