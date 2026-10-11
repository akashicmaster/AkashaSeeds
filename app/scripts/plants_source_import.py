#!/usr/bin/env python3
"""
plants_source_import.py — USDA NRCS PLANTS Database (complete checklist) → the Source Data Layer.

TEXT ONLY: the checklist rows (symbol / scientific name / common name / family + synonyms). No
images, no distribution millions. Public domain (US federal work); provenance recorded anyway.

Shape (follows mobility/birdclef):
  fetch  : download the Complete PLANTS Checklist (plants.sc.egov.usda.gov/DocumentLibrary/Txt/
           plantlst.txt), fold the 93k rows into ONE record per ACCEPTED name (48,994) with its
           synonyms attached as a list — a synonym is an ALIAS of the accepted name, not its own
           source item (Akasha's alias machinery is the matching structure).
  import : register → pool → acquire (batched, resumable) → freeze → declare `plants` CORPUS →
           audit. One Source Atom per accepted name, coded fields verbatim.

Usage:
  python app/scripts/plants_source_import.py fetch  [--out-dir plants_data]
  python app/scripts/plants_source_import.py import [--as admin] [--records plants_data/checklist.jsonl]
      [--base <data dir>] [--batch 500] [--rpc-timeout 300] [--resume]

`--resume` reads the pool's current total and skips that many records (safe: acquisition order is
deterministic = file order; re-acquiring an overlap is idempotent).
"""
import argparse
import csv
import gzip
import io
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CHECKLIST_URL = "https://plants.sc.egov.usda.gov/DocumentLibrary/Txt/plantlst.txt"
SOURCE_ID = "source:src:usda_plants"
POOL = "source:pool:plants:checklist:v1"
LAB = "plants"
BUNDLE_DIR = os.path.join(ROOT, "app", "assets", "plants_checklist")


def fetch(out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    raw_path = os.path.join(out_dir, "plantlst.txt")
    print(f"  downloading {CHECKLIST_URL} …")
    with urllib.request.urlopen(CHECKLIST_URL, timeout=120) as r:
        data = r.read()
    with open(raw_path, "wb") as fh:
        fh.write(data)
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8", "replace"))))
    accepted = {}
    order = []
    for row in rows:
        sym = (row.get("Symbol") or "").strip()
        if not sym:
            continue
        syn = (row.get("Synonym Symbol") or "").strip()
        if not syn:
            accepted[sym] = {
                "symbol": sym,
                "scientific_name": (row.get("Scientific Name with Author") or "").strip(),
                "common_name": (row.get("Common Name") or "").strip(),
                "family": (row.get("Family") or "").strip(),
                "synonyms": [],
            }
            order.append(sym)
    orphan_syn = 0
    for row in rows:
        syn = (row.get("Synonym Symbol") or "").strip()
        if not syn:
            continue
        sym = (row.get("Symbol") or "").strip()
        if sym in accepted:
            accepted[sym]["synonyms"].append(
                {"symbol": syn,
                 "scientific_name": (row.get("Scientific Name with Author") or "").strip()})
        else:
            orphan_syn += 1
    out_path = os.path.join(out_dir, "checklist.jsonl")
    with open(out_path, "w", encoding="utf-8") as fh:
        for sym in order:
            fh.write(json.dumps(accepted[sym], ensure_ascii=False) + "\n")
    manifest = {
        "provider": "USDA Natural Resources Conservation Service",
        "collection": "PLANTS Database — Complete PLANTS Checklist",
        "retrieval": CHECKLIST_URL,
        "rights": "Public domain (US federal government work)",
        "rows_raw": len(rows), "accepted": len(order),
        "synonyms_folded": len(rows) - len(order) - orphan_syn, "orphan_synonyms": orphan_syn,
        "rule": "COMPLETE checklist — one record per accepted name, synonyms folded as aliases; "
                "no selection, no filtering. Text only (no images, no distribution rows).",
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    # deploy bundle (mobility/CMA pattern): commit ONCE → deploys can auto-load
    os.makedirs(BUNDLE_DIR, exist_ok=True)
    with gzip.open(os.path.join(BUNDLE_DIR, "checklist.jsonl.gz"), "wt", encoding="utf-8") as fh:
        for sym in order:
            fh.write(json.dumps(accepted[sym], ensure_ascii=False) + "\n")
    with open(os.path.join(BUNDLE_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(f"  accepted {len(order):,} · synonyms folded {manifest['synonyms_folded']:,} "
          f"(orphan {orphan_syn}) → {out_path}")
    print(f"  DEPLOY BUNDLE → {BUNDLE_DIR}/ (checklist.jsonl.gz + manifest.json)")
    print(f"\n  next: python app/scripts/plants_source_import.py import --as <admin_id>")


def run_import(args):
    from api.portals import cell_ipc
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not cell_ipc.ping(base):
        print(f"[!] No Cell daemon at {base}. Start one: python akasha.py --serve", file=sys.stderr)
        sys.exit(2)
    gw = cell_ipc.SocketGateway(base, timeout=args.rpc_timeout)

    def d(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": args.as_id, "data": data}, "id": "p"}, "local")
        if isinstance(r, dict) and "error" in r:
            raise RuntimeError(f"{method}: {r['error'].get('message')}")
        return (r or {}).get("result") or {}

    manifest = {}
    mpath = os.path.join(os.path.dirname(args.records), "manifest.json")
    if os.path.exists(mpath):
        manifest = json.load(open(mpath, encoding="utf-8"))

    d("source.register", {"provider": manifest.get("provider", "USDA NRCS"),
                          "collection": manifest.get("collection", "PLANTS Complete Checklist"),
                          "name": "usda_plants", "uri": "https://plants.usda.gov/",
                          "retrieval_uri": CHECKLIST_URL,
                          "rights": manifest.get("rights", "Public domain")})
    print(f"  [1] source: {SOURCE_ID}")
    d("source.pool.create", {"name": "plants:checklist", "version": "v1", "source": SOURCE_ID,
                             "dataset_version": manifest.get("snapshot_date", ""),
                             "retrieval": CHECKLIST_URL, "rule": manifest.get("rule", "")})
    print(f"  [2] pool: {POOL}")

    records = [json.loads(l) for l in open(args.records, encoding="utf-8") if l.strip()]
    start = 0
    if args.resume:
        st = d("source.status", {"pool": POOL})
        start = int(st.get("total") or 0)
        print(f"  [resume] pool already holds {start} — continuing from there")
    total_acq = 0
    for i in range(start, len(records), args.batch):
        chunk = records[i:i + args.batch]
        r = d("source.acquire", {"source": SOURCE_ID, "records": chunk, "id_field": "symbol",
                                 "pool": POOL, "content_type": "text",
                                 "rule": f"complete checklist rows {i}-{i + len(chunk) - 1}"})
        total_acq += r.get("acquired", 0)
        print(f"      acquired {i + len(chunk)}/{len(records)}…", flush=True)
    print(f"  [3] acquired {total_acq} accepted-name Source Atoms this run")

    fr = d("source.pool.freeze", {"pool": POOL})
    print(f"  [4] pool FROZEN: {fr.get('member_count')} members, at_seq={fr.get('at_seq')}")
    decl = d("source.lab.declare", {"lab": LAB, "klass": "CORPUS", "pool": POOL,
                                    "primary_source": SOURCE_ID,
                                    "fixture_policy": "no invented taxa; USDA PLANTS checklist "
                                                      "verbatim, synonyms as aliases"})
    print(f"  [5] {LAB} declared CORPUS → {decl.get('evidence_status')}")
    au = d("source.audit", {"lab": LAB})
    mo = d("source.modalities", {"pool": POOL})
    print(f"  done → status={au.get('evidence_status')} modalities={mo.get('modalities')}")
    gw.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["fetch", "import"])
    ap.add_argument("--out-dir", default="plants_data")
    ap.add_argument("--records", default="plants_data/checklist.jsonl")
    ap.add_argument("--as", dest="as_id", default="admin")
    ap.add_argument("--base", default=None)
    ap.add_argument("--batch", type=int, default=500)
    ap.add_argument("--rpc-timeout", type=float, default=300.0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    if args.mode == "fetch":
        fetch(args.out_dir)
    else:
        run_import(args)


if __name__ == "__main__":
    main()
