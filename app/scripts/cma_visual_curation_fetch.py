#!/usr/bin/env python3
"""
cma_visual_curation_fetch.py — OFF-LINE acquisition adapter for the Visual Curation Laboratory
(Phase 1), path A (public library). Run this in a context that can reach the Cleveland Museum of Art
Open Access API; it selects the fixed 100-artwork heterogeneous stress corpus DETERMINISTICALLY and
writes a records file + provenance manifest that `app/scripts/cma_visual_curation_import.py` loads into a
running Cell. It NEVER runs on the deploy host and NEVER downloads an image binary — only references.

Target domain (the one place this talks to):
    https://openaccess-api.clevelandart.org/api/artworks/     (CMA Open Access REST API)
    Docs: https://openaccess-api.clevelandart.org/   ·   Data dump: github.com/ClevelandMuseumArt/openaccess
    License: the museum marks CC0 works with share_license_status == "CC0". We keep ONLY CC0 works
    that carry a usable public image reference. The museum is the source authority for the record;
    rights text is preserved verbatim, never paraphrased (spec §3.2).

What it does (stdlib only, polite):
  1. Page the API for CC0 works that HAVE an image (has_image=1), collecting candidates with the
     minimum metadata: a stable id, a title, a type/medium, and a public image url.
  2. Classify each candidate into a material family from its `type` (spec §4 target composition).
  3. Select DETERMINISTICALLY within each family by a stable hash of (corpus_seed, object_id) — the
     selection is INDEPENDENT of any later model result and reproducible from the seed (spec §4/§6).
  4. Emit records.jsonl (one artwork per line, verbatim kept fields + the chosen image url) and
     manifest.json (api snapshot date, filter, seed, family targets, the 100 chosen object ids).
  5. Print the ready-to-run import command.

Usage:
    python app/scripts/cma_visual_curation_fetch.py --out-dir cma_vcl [--seed vcl-v1] [--total 100]
    #   then, against a running Cell:
    python app/scripts/cma_visual_curation_import.py --as <admin_id> \
        --records cma_vcl/records.jsonl --manifest cma_vcl/manifest.json
"""
import argparse
import datetime
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://openaccess-api.clevelandart.org/api/artworks/"
OBJECT_URL = "https://www.clevelandart.org/art/"     # canonical object page prefix (+ accession or id)

# Material families → target counts (spec §4). "type" strings from CMA are matched case-insensitively
# by substring; a record that matches none falls to "other" (the boundary family).
FAMILIES = [
    ("painting",       ["painting"],                                   25),
    ("prints_drawings",["print", "drawing", "woodcut", "etching", "engraving", "lithograph"], 20),
    ("sculpture",      ["sculpture", "relief", "bronze", "statue"],    15),
    ("decorative_arts",["decorative", "ceramic", "porcelain", "glass", "metalwork", "jewelry",
                        "furniture", "lacquer", "enamel"],             15),
    ("manuscript",     ["manuscript", "miniature", "folio", "leaf"],   10),
    ("textile",        ["textile", "tapestry", "carpet", "embroidery", "costume"], 10),
    ("other",          [],                                              5),
]

# Fields kept verbatim from the CMA record (museum is the authority; do not "clean").
KEEP = ("id", "accession_number", "title", "creation_date", "culture", "type", "department",
        "technique", "measurements")


def _req(url):
    return urllib.request.Request(url, headers={"User-Agent": "akasha-vcl-cma-fetch/0.1"})


def _family_of(type_str):
    t = (type_str or "").lower()
    for name, needles, _ in FAMILIES[:-1]:
        if any(n in t for n in needles):
            return name
    return "other"


def _image_url(rec):
    imgs = rec.get("images") or {}
    for k in ("web", "print", "full"):
        u = (imgs.get(k) or {}).get("url")
        if u:
            return u
    return None


def _stable_rank(seed, object_id):
    return hashlib.sha256(("%s|%s" % (seed, object_id)).encode()).hexdigest()


def fetch_candidates(limit_pages, page_size, sleep_s):
    """Stream CC0, has-image works. Bounded: one page in memory at a time (memory discipline)."""
    seen, skip, page = {}, 0, 0
    while page < limit_pages:
        q = urllib.parse.urlencode({"cc0": 1, "has_image": 1, "limit": page_size, "skip": skip})
        try:
            with urllib.request.urlopen(_req(API + "?" + q), timeout=60) as r:
                data = json.load(r)
        except Exception as exc:
            print("  [!] page %d fetch failed: %s" % (page, exc), file=sys.stderr)
            break
        rows = data.get("data") or []
        if not rows:
            break
        for rec in rows:
            if (rec.get("share_license_status") or "").upper() != "CC0":
                continue
            img = _image_url(rec)
            oid = str(rec.get("id") or "")
            if not img or not oid or not (rec.get("title") or "").strip():
                continue
            if oid in seen:
                continue
            kept = {k: rec.get(k) for k in KEEP}
            kept["creators"] = "; ".join(c.get("description", "") for c in (rec.get("creators") or []))
            kept["rights"] = rec.get("share_license_status")
            kept["open_access_status"] = True
            kept["canonical_url"] = rec.get("url") or (OBJECT_URL + str(rec.get("accession_number") or oid))
            kept["image_url"] = img
            kept["family"] = _family_of(rec.get("type"))
            seen[oid] = kept
        skip += page_size
        page += 1
        print("  page %d: %d CC0+image candidates so far…" % (page, len(seen)))
        time.sleep(sleep_s)
    return list(seen.values())


def select(candidates, seed, total):
    """Deterministic per-family selection by a stable hash rank; independent of any model result."""
    by_fam = {name: [] for name, _, _ in FAMILIES}
    for c in candidates:
        by_fam.setdefault(c["family"], []).append(c)
    chosen, leftovers = [], []
    for name, _, target in FAMILIES:
        pool = sorted(by_fam.get(name, []), key=lambda c: _stable_rank(seed, str(c["id"])))
        chosen += pool[:target]
        leftovers += pool[target:]
    # Backfill to `total` from the global leftover pool (still deterministic by rank).
    if len(chosen) < total:
        leftovers.sort(key=lambda c: _stable_rank(seed, str(c["id"])))
        chosen += leftovers[: total - len(chosen)]
    return chosen[:total]


def main():
    ap = argparse.ArgumentParser(description="CMA Open Access → VCL Phase-1 100-work corpus (deterministic).")
    ap.add_argument("--out-dir", default="cma_vcl")
    ap.add_argument("--seed", default="vcl-v1", help="corpus_seed — the reproducibility anchor")
    ap.add_argument("--total", type=int, default=100)
    ap.add_argument("--pages", type=int, default=40, help="max API pages to scan for candidates")
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--sleep", type=float, default=0.5, help="politeness delay between pages (s)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    print("  [1] fetching CC0 + has-image candidates from %s" % API)
    cands = fetch_candidates(args.pages, args.page_size, args.sleep)
    if len(cands) < args.total:
        print("  [!] only %d candidates found (< %d) — widen --pages or check the API." % (len(cands), args.total),
              file=sys.stderr)
    chosen = select(cands, args.seed, args.total)
    fam_counts = {}
    for c in chosen:
        fam_counts[c["family"]] = fam_counts.get(c["family"], 0) + 1
    print("  [2] selected %d works — %s" % (len(chosen), fam_counts))

    rec_path = os.path.join(args.out_dir, "records.jsonl")
    with open(rec_path, "w", encoding="utf-8") as fh:
        for c in chosen:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    manifest = {
        "provider": "cma", "api": API, "license_filter": "CC0 + has_image",
        "snapshot_date": datetime.date.today().isoformat(),
        "corpus_seed": args.seed, "selection_rule": "deterministic: per-family, stable sha256(seed|object_id)",
        "family_targets": {name: t for name, _, t in FAMILIES},
        "selected_family_counts": fam_counts, "total": len(chosen),
        "object_ids": [str(c["id"]) for c in chosen],
        "pool_id": "source:pool:cma:visual_curation:v1",
    }
    with open(os.path.join(args.out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    # DEPLOY BUNDLE (dev-side prep, per the Grand Principle): also emit the gzipped records + manifest
    # into app/assets/cma_visual_curation/ — commit those two files ONCE and every deploy auto-loads the
    # corpus at boot (_schedule_cma_bootstrap), no museum API and no operator step on the target cell.
    import gzip as _gzip
    _bundle = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "app", "assets", "cma_visual_curation")
    os.makedirs(_bundle, exist_ok=True)
    with _gzip.open(os.path.join(_bundle, "records.jsonl.gz"), "wt", encoding="utf-8") as fh:
        for c in chosen:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    with open(os.path.join(_bundle, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print("\n  [3] wrote %s (%d records) + manifest.json" % (rec_path, len(chosen)))
    print("      DEPLOY BUNDLE written to app/assets/cma_visual_curation/ (records.jsonl.gz + manifest.json).")
    print("      Commit those two files ONCE → every deploy auto-loads the corpus at boot (no operator step).")
    print("      (Manual one-off import into a running Cell is still possible:)")
    print("      python app/scripts/cma_visual_curation_import.py --as <admin_id> \\")
    print("          --records %s --manifest %s" % (rec_path, os.path.join(args.out_dir, "manifest.json")))


if __name__ == "__main__":
    main()
