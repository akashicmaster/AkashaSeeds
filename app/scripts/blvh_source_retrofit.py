#!/usr/bin/env python3
"""
blvh_source_retrofit.py — connect the British Library Visual Hypothesis Corpus (blvh) to the
Akasha **Source Data Layer** (source.*), per Spec v0.3 §11/§24 (blvh is the first consumer).

Runs the retrofit entirely through the CLI-first `source.*` operators, against a LIVE Cell daemon
(same pattern as app/scripts/blvh_mock_image.py). It:

  1. source.register  the British Library image corpus as an external source.
  2. source.acquire   a BOUNDED raw image pool — either fetched live from the Hugging Face Dataset
                      Viewer /rows API, or read from a --records JSONL of real BL rows. Each row
                      becomes a Source Atom carrying its source metadata + a durable /rows locator
                      (never the binary; external location is not identity).
  3. source.pool.*    freeze the pool as bl_visual_raw_v1 (an immutable, versioned sampling frame,
                      stamped with an Akasha-Time marker).
  4. source.lab.declare  blvh as a CORPUS laboratory that samples_from that frozen pool.
  5. source.bridge    (optional) record each slot's selection as an ADDITIVE bridge
                      `blvh:slot:NNN --selected_from--> source:item:bl:<id>` (the raw atom is never
                      mutated). Provide selections with --select slot=item (repeatable) or
                      --selections <jsonl of {slot,item}>.
  6. source.audit     blvh, and print whether its results are now traceable to a real sampling frame.

The 100 blvh:slot:* are sampling OPERATIONS (TO_SELECT); the raw pool is acquired SEPARATELY and
does NOT consist of the selected items by definition (Spec §11). Nothing synthetic is written as
evidence — provide real rows (live HF or --records); --demo writes a clearly-labelled TINY test
pool so you can watch the flow end-to-end on a dev cell.

Start a daemon first (python akasha.py --serve), enable the blvh pack (onto.pack.enable name=blvh),
then:
    python app/scripts/blvh_source_retrofit.py --as <admin_id> --limit 300
    python app/scripts/blvh_source_retrofit.py --as <admin_id> --records bl_rows.jsonl
    python app/scripts/blvh_source_retrofit.py --as <admin_id> --demo         # tiny labelled test pool
`--as` must be THIS cell's genesis admin id (as with blvh_mock_image.py) so the universal writes
land in the nucleus the GUI's guest session reads.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

DATASET = "biglam/british-library-book-images"
SOURCE_ID = "source:src:bl"
POOL = "source:pool:bl_visual_raw:v1"
LAB = "blvh"

# A tiny, clearly-labelled bounded pool for --demo (a dev-cell walkthrough, NOT evidence). Uses the
# ONE verified row (offset 10432 → a real BL plate) plus a couple more real-shaped coordinates.
_DEMO_ROWS = [
    {"id": "plates:train:10432", "config": "plates", "split": "train", "row_index": 10432,
     "dataset_id": DATASET, "record_id": "002698018", "date": "1878", "image_type": "plates",
     "source_filename": "002698018_0_000032_1_The History of Ogle County  Illinois Illustrated_1878.jpg",
     "media_type": "image/jpeg", "attribution": "British Library",
     "rights": "Public Domain Mark / CC0-1.0 dataset tag", "demo": True},
    {"id": "plates:train:200", "config": "plates", "split": "train", "row_index": 200,
     "dataset_id": DATASET, "media_type": "image/jpeg", "attribution": "British Library", "demo": True},
    {"id": "plates:train:9001", "config": "plates", "split": "train", "row_index": 9001,
     "dataset_id": DATASET, "media_type": "image/jpeg", "attribution": "British Library", "demo": True},
]


def _rows_url(config, split, offset, length=1):
    return ("https://datasets-server.huggingface.co/rows"
            f"?dataset={DATASET.replace('/', '%2F')}&config={config}&split={split}"
            f"&offset={offset}&length={length}")


def _fetch_hf(config, split, limit):
    """Fetch `limit` rows from the HF Dataset Viewer /rows API → real BL source records. Best-effort;
    network egress uses the environment proxy. The DURABLE locator is the /rows coordinate recipe
    (the front end resolves .image.src browser-side, re-resolving when the signed URL expires)."""
    import urllib.request
    out = []
    page = 100
    fetched = 0
    while fetched < limit:
        n = min(page, limit - fetched)
        url = _rows_url(config, split, fetched, n)
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"[!] HF fetch failed at offset {fetched}: {exc}", file=sys.stderr)
            break
        rows = data.get("rows") or []
        if not rows:
            break
        for r in rows:
            idx = r.get("row_idx", fetched)
            row = r.get("row") or {}
            rec = {"id": f"{config}:{split}:{idx}", "config": config, "split": split,
                   "row_index": idx, "dataset_id": DATASET, "media_type": "image/jpeg",
                   "attribution": "British Library",
                   "rights": "Public Domain Mark / CC0-1.0 dataset tag",
                   "url": _rows_url(config, split, idx)}
            # capture scalar source-supplied columns verbatim (skip the binary image cell)
            for k, v in row.items():
                if k == "image":
                    continue
                if isinstance(v, (str, int, float, bool)) or v is None:
                    rec[k] = v
            out.append(rec)
            fetched += 1
        if len(rows) < n:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description="Retrofit blvh onto the Source Data Layer (CLI).")
    ap.add_argument("--as", dest="as_id", default="admin",
                    help="admin/librarian id to write as (your genesis admin id, e.g. --as henri)")
    ap.add_argument("--base", default=None, help="daemon data dir (default AKASHA_DATA_DIR or ./data)")
    ap.add_argument("--limit", type=int, default=300, help="raw pool size to acquire from HF (Spec §11: 300–1000)")
    ap.add_argument("--config", default="plates", help="HF dataset config (default: plates)")
    ap.add_argument("--split", default="train", help="HF dataset split (default: train)")
    ap.add_argument("--records", default=None, help="JSONL of real BL rows to acquire instead of a live fetch")
    ap.add_argument("--select", action="append", default=[], metavar="slot=item",
                    help="record a slot's selection: blvh:slot:NNN=source:item:bl:<id> (repeatable)")
    ap.add_argument("--selections", default=None, help="JSONL of {slot,item} selection bridges")
    ap.add_argument("--demo", action="store_true", help="acquire a tiny LABELLED test pool (dev-cell walkthrough)")
    ap.add_argument("--freeze", dest="freeze", action="store_true", default=True, help="freeze the pool (default on)")
    ap.add_argument("--no-freeze", dest="freeze", action="store_false", help="leave the pool OPEN")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print(f"[!] No Cell daemon at {base}. Start one:  python akasha.py --serve", file=sys.stderr)
        sys.exit(2)
    gw = client.connect(base)

    def d(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": args.as_id, "data": data}, "id": "m"}, "local")
        if isinstance(r, dict) and "result" in r:
            return r["result"]
        return {"__error__": (r or {}).get("error") if isinstance(r, dict) else r}

    # 0. sanity — is the blvh pack loaded on this cell?
    if not (d("read", {"id": "blvh:root"}) or {}).get("content"):
        print("[!] blvh pack not loaded on this cell. Enable it first:  onto.pack.enable name=blvh",
              file=sys.stderr)
        gw.close(); sys.exit(3)

    # 1. register the external source
    reg = d("source.register", {"provider": "British Library", "collection": "book images",
                                "uri": "https://data.bl.uk/", "name": "bl",
                                "rights": "Public Domain Mark / CC0-1.0 dataset tag"})
    print(f"  [1] source: {reg.get('source', SOURCE_ID)}")

    # 2. gather the raw rows
    if args.demo:
        rows = _DEMO_ROWS
        print(f"  [2] --demo: acquiring {len(rows)} LABELLED test rows (not evidence)")
    elif args.records:
        rows = [json.loads(l) for l in open(args.records, encoding="utf-8") if l.strip()]
        print(f"  [2] acquiring {len(rows)} rows from {args.records}")
    else:
        rows = _fetch_hf(args.config, args.split, args.limit)
        print(f"  [2] fetched {len(rows)} rows live from HF ({args.config}/{args.split})")
    if not rows:
        print("[!] no rows to acquire (live fetch failed?) — pass --records <jsonl> or --demo",
              file=sys.stderr)
        gw.close(); sys.exit(4)

    # acquire into source atoms + drop straight into the pool (created OPEN on first add)
    d("source.pool.create", {"name": "bl_visual_raw", "source": SOURCE_ID, "version": "v1",
                             "rule": f"bounded BL {args.config}/{args.split} raw image pool "
                                     f"(n={len(rows)}), acquired before selection"})
    acq = d("source.acquire", {"source": SOURCE_ID,
                               "rule": f"BL {args.config}/{args.split} raw images (n={len(rows)})",
                               "records": rows, "id_field": "id", "pool": POOL})
    print(f"  [3] acquired: {acq.get('acquired')} ACQUIRED / {acq.get('unresolved')} unresolved "
          f"→ pool {POOL}")

    # 3. freeze the pool (immutable, Akasha-Time stamped)
    if args.freeze:
        fr = d("source.pool.freeze", {"pool": POOL})
        print(f"  [4] pool FROZEN: {fr.get('member_count')} members, at_seq={fr.get('at_seq')}")
    else:
        print("  [4] pool left OPEN (--no-freeze)")

    # 4. declare blvh as a CORPUS lab that samples_from the frozen pool
    decl = d("source.lab.declare", {"lab": LAB, "klass": "CORPUS", "pool": POOL,
                                    "primary_source": SOURCE_ID,
                                    "fixture_policy": "mock fixtures (blvh:image:mock:*) are labelled, never evidence"})
    print(f"  [5] blvh declared CORPUS → evidence_status={decl.get('evidence_status')}")

    # 5. optional selection bridges (slot → raw item), additive
    sels = []
    for s in args.select:
        if "=" in s:
            slot, item = s.split("=", 1)
            sels.append({"slot": slot.strip(), "item": item.strip()})
    if args.selections:
        sels += [json.loads(l) for l in open(args.selections, encoding="utf-8") if l.strip()]
    bridged = 0
    for sel in sels:
        r = d("source.bridge", {"src": sel["slot"], "dst": sel["item"], "rel": "selected_from",
                                "by": "blvh:model:siglip2_so400m", "run": "blvh-0.3"})
        if not (isinstance(r, dict) and "__error__" in r):
            bridged += 1
    if sels:
        print(f"  [6] recorded {bridged}/{len(sels)} selection bridges (slot --selected_from--> raw item)")

    # 6. audit
    au = d("source.audit", {"lab": LAB})
    print(f"\n  audit blvh → status={au.get('evidence_status')} grounded={au.get('grounded')} "
          f"bridged={au.get('bridged')}")
    for f in au.get("findings", []):
        print(f"    · {f}")
    print(f"\n  Inspect:  source.pool.ls pool={POOL}   ·   source.lab.profile lab={LAB}   ·   "
          f"source.trace id=<slot|item>\n")
    gw.close()


if __name__ == "__main__":
    main()
