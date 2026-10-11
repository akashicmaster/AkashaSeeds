#!/usr/bin/env python3
"""
bl_real_dump.py — freeze the BL-REAL-1000 corpus to JSONL so it can be SHIPPED IN THE SEED.

Run ONCE in an egress-allowed context (huggingface_hub + pyarrow strongly recommended, so the
robust parquet-mirror path is used and nothing truncates). It performs the exact same deterministic
selection + crop_masks / blbooks joins as the live loader (`app/scripts/bl_real_bootstrap.py` — whose
functions it reuses, no logic duplicated) and writes three files:

    <out>/bl_images.jsonl   the 1000 selected image rows (386/356/201/57, verbatim metadata)
    <out>/bl_masks.jsonl    the resolved crop-mask observation rows (keyed by fname)
    <out>/bl_books.jsonl    the resolved blbooks metadata rows (keyed by record_id)

Commit those into the repo (default out dir: app/assets/bl_real_corpus/). The kernel's boot phase then
loads them OFFLINE — the pool is built with NO Hugging Face access and NO huggingface_hub/pyarrow on
the target cell, so a VPS extraction is deterministic and immune to HF /rows 502s and /filter outages.

    python app/scripts/bl_real_dump.py                       # → app/assets/bl_real_corpus/*.jsonl (full 1000)
    python app/scripts/bl_real_dump.py --out /tmp/bl --limit 20   # a small smoke dump

Guardrail: if the joins come back mostly FAILED (an HF outage during the dump), it reports the run
DEGRADED and exits non-zero WITHOUT writing a partial corpus — you must ship a complete one, not a
truncated snapshot that would look complete once frozen.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")

import app.scripts.bl_real_bootstrap as blb   # the live loader — its functions are reused verbatim


def _fast_stream(config, log, workers=8):
    """Read the metadata columns of a config's parquet-mirror shards IN PARALLEL.

    The deterministic selection needs every row's `fname`, so the whole population must be read — but
    the loader's sequential shard-by-shard scan is HTTP-latency-bound (hundreds of shards, one at a
    time). Reading only the metadata columns (fname/date/image_type — never the image binary) across
    a small thread pool turns tens of minutes into a couple. Yields the same row dicts the loader's
    streamer does. Raises on total failure so dump() aborts rather than selecting from a partial set."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem
    from concurrent.futures import ThreadPoolExecutor
    fs = HfFileSystem()
    paths = sorted(fs.glob("datasets/%s@%s/%s/%s/*.parquet"
                           % (blb.DATASET, blb._PQ_REV, config, blb.SPLIT)))
    if not paths:
        raise RuntimeError("no parquet mirror files for %s/%s" % (config, blb.SPLIT))

    def _scan(path):
        with fs.open(path, "rb") as f:
            pf = pq.ParquetFile(f)
            names = pf.schema_arrow.names
            want = [c for c in ("fname", "date", "image_type") if c in names]
            tbl = pf.read(columns=want)
        cols = {c: tbl.column(c).to_pylist() for c in tbl.column_names}
        fn = cols.get("fname", [])
        return [{"fname": fn[i], "config": config, "split": blb.SPLIT,
                 "date_raw": (cols.get("date") or [None] * len(fn))[i],
                 "image_type_raw": (cols.get("image_type") or [None] * len(fn))[i]}
                for i in range(len(fn))]

    out, done = [], 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for rows in ex.map(_scan, paths):
            out.extend(rows); done += 1
            if done % 100 == 0:
                log("    %s: %d/%d shards, %d rows" % (config, done, len(paths), len(out)))
    for i, r in enumerate(out):
        r["row_index"] = i
    log("  streamed %d rows for config '%s' via the parquet mirror (parallel)" % (len(out), config))
    return out


def dump(out_dir, limit, log=print, workers=4):
    os.makedirs(out_dir, exist_ok=True)
    # RESUMABLE: each config's selection + each join is checkpointed to <out>/.parts/ as soon as it
    # completes, so a run interrupted by HF rate-limiting (the full ~1.08M-row scan can throttle) is
    # re-run and skips whatever already finished. Nothing is lost across restarts.
    parts = os.path.join(out_dir, ".parts")
    os.makedirs(parts, exist_ok=True)

    def _load(name):
        p = os.path.join(parts, name)
        if os.path.exists(p):
            return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        return None

    def _save(name, records):
        p = os.path.join(parts, name); tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, p)

    # 1. deterministic selection per config (checkpointed) — gentle parallel parquet scan
    selected = []
    for cfg, alloc in blb.ALLOC.items():
        take = min(alloc, limit or alloc)
        cached = _load("sel_%s.jsonl" % cfg)
        if cached is not None:
            log("  select[%s]: %d (resumed from checkpoint)" % (cfg, len(cached)))
            selected += cached
            continue
        log("  streaming '%s' from HF…" % cfg)
        try:
            rows = _fast_stream(cfg, log, workers)
        except Exception as exc:
            log("  parallel scan failed (%s) — falling back to the loader's streamer" % exc)
            rows = list(blb.stream_config_rows(cfg, blb.SPLIT, log))
        picked = blb.select_deterministic(rows, take)
        if not picked:
            log("  [!] 0 rows for '%s' — the stream is unavailable/truncated; aborting (no checkpoint)" % cfg)
            return None
        _save("sel_%s.jsonl" % cfg, picked)
        selected += picked
        log("  select[%s]: %d of %d streamed (checkpointed)" % (cfg, len(picked), len(rows)))

    non_cover = [r for r in selected if r.get("config") != "covers"]

    # 2. crop_masks join (non-cover) — checkpointed; never checkpoint a degraded (outage) result
    mask_recs = _load("masks.jsonl")
    if mask_recs is not None:
        log("  crop_masks: %d rows (resumed from checkpoint)" % len(mask_recs))
    else:
        masks = blb.fetch_masks_for(non_cover, log)
        m_att, m_err, m_rate = blb.join_stats(masks)
        if m_rate > blb.MAX_JOIN_ERROR_RATE:
            log("  [!] crop_masks DEGRADED (%d/%d failed, > %.0f%%) — HF unhealthy; NOT checkpointing, "
                "re-run when HF is up." % (m_err, m_att, blb.MAX_JOIN_ERROR_RATE * 100))
            return None
        mask_recs = list(masks.values())
        _save("masks.jsonl", mask_recs)

    # 3. blbooks join by record_id — checkpointed
    book_recs = _load("books.jsonl")
    if book_recs is not None:
        log("  blbooks: %d rows (resumed from checkpoint)" % len(book_recs))
    else:
        rids = sorted({blb.record_id_of(r["fname"]) for r in non_cover if blb.record_id_of(r["fname"])})
        books = blb.fetch_books_for(rids, log)
        b_att, b_err, b_rate = blb.join_stats(books)
        if b_rate > blb.MAX_JOIN_ERROR_RATE:
            log("  [!] blbooks DEGRADED (%d/%d failed, > %.0f%%) — HF unhealthy; NOT checkpointing, "
                "re-run when HF is up." % (b_err, b_att, blb.MAX_JOIN_ERROR_RATE * 100))
            return None
        book_recs = list(books.values())
        _save("books.jsonl", book_recs)

    # 4. assemble the final three JSONL from the (now-complete) parts
    def _write(name, records):
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return path, len(records)

    ip, ic = _write("bl_images.jsonl", selected)
    mp, mc = _write("bl_masks.jsonl", mask_recs)
    bp, bc = _write("bl_books.jsonl", book_recs)
    log("\n  dumped: %d images → %s" % (ic, ip))
    log("          %d crop-mask rows → %s" % (mc, mp))
    log("          %d book rows → %s" % (bc, bp))
    return {"images": ic, "masks": mc, "books": bc, "out": out_dir}


def main():
    ap = argparse.ArgumentParser(description="Freeze the BL-REAL-1000 corpus to JSONL for the seed.")
    ap.add_argument("--out", default=os.path.join(ROOT, "app", "assets", "bl_real_corpus"),
                    help="output dir (default app/assets/bl_real_corpus/ — commit this)")
    ap.add_argument("--limit", type=int, default=None, help="cap rows PER CONFIG (smoke dump; omit for the full 1000)")
    ap.add_argument("--workers", type=int, default=4, help="parallel shard readers (default 4; lower = gentler on HF)")
    args = ap.parse_args()
    print("\n  BL-REAL-1000 dump → %s  (resumable; workers=%d)" % (args.out, args.workers))
    out = dump(args.out, args.limit, workers=args.workers)
    if not out:
        sys.exit(2)
    print("\n  Commit %s/{bl_images,bl_masks,bl_books}.jsonl — the kernel boot phase then loads it "
          "OFFLINE (no HF, no huggingface_hub/pyarrow on the target cell).\n" % args.out)


if __name__ == "__main__":
    main()
