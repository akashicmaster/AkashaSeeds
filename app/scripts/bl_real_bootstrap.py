#!/usr/bin/env python3
"""
bl_real_bootstrap.py — the BL-REAL-1000 installation-time Source Data bootstrap.

Implements docs/for-llm/… "Akasha Source Viewer — Real Data Bootstrap Directive v0.1": load a
small but REAL external corpus (British Library book images) into the Source Data Layer so a fresh
install is immediately useful and the Source Viewer shows real, uninvented material.

HARD RULES (from the directive):
  • RAW data only — no hand-written, curated, semantically-preselected, or synthetic image records.
  • Selection is DETERMINISTIC + hypothesis-independent: SHA256("akasha-bl-bootstrap-v1\\0"+fname),
    sorted ascending, first N per config (embellishments 386 / plates 356 / medium 201 / covers 57
    = exactly 1000). No topic/date/score/keyword/semantic filtering.
  • Machine predictions (crop-mask, image-type, embedding) are SEPARATE observation atoms, never
    flattened into source facts. Covers deliberately carry NO crop-mask observation.
  • Failure is visible (UNRESOLVED / FAILED / unresolved joins stay queryable), never guessed.
  • bootstrap_v1 is FROZEN after load; a later research question needs a NEW declared pool.

The atoms are written THROUGH the Source Data Layer (source.* ops) so they are universal-scope and
guest-readable, and the Source Viewer renders them with no bespoke wiring. Entities map onto the
existing ops:
  provider/dataset/model/process → source.register   (external sources / upstream agents)
  image row                      → source.acquire     (Source Atom, into the pool)
  crop-mask / embedding / book   → source.acquire (from their own upstream dataset) + source.bridge
                                   observed_from / interprets the image (a traceable machine reading)

Run — LIVE on a cell that can reach Hugging Face (the VPS):
    python akasha.py --serve                       # a daemon must be running
    python app/scripts/bl_real_bootstrap.py --as <admin_id>            # full 1000-row live acquisition
    python app/scripts/bl_real_bootstrap.py --as <admin_id> --limit 40 # smaller sample for a first run
Run — OFFLINE (no HF; feed pre-fetched real rows / masks / books as JSONL):
    python app/scripts/bl_real_bootstrap.py --as <admin_id> \
        --images-jsonl rows.jsonl --masks-jsonl masks.jsonl --books-jsonl books.jsonl
The `--as` id MUST be this cell's admin/librarian (see blvh_mock_image.py) — the universal writes run
as that identity. In-process auto-load (VPS boot phase) uses the boot admin_session instead.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

# ── Directive constants ──────────────────────────────────────────────────────
DATASET   = "biglam/british-library-book-images"
OCR_DS    = "biglam/blbooks-parquet"
MASKS_CFG = "crop_masks"          # upstream machine observation dataset (config of DATASET)
EMB_CFG   = "siglip2_embeddings"  # upstream retrieval index observation (config of DATASET)
SPLIT     = "train"
# `crop_masks` is NOT split `train`: it carries one split per image type, named after the
# image config. `covers` has no crop_masks split at all — the upstream shape itself encodes
# the directive that covers carry no mask.
MASK_SPLITS = ("embellishments", "plates", "medium")
# Share of join lookups allowed to FAIL OUTRIGHT before the run counts as degraded and the pool is
# left unfrozen. A stray 5xx in ~950 lookups is tolerable; a dead /filter index is not.
MAX_JOIN_ERROR_RATE = 0.02
NS        = b"akasha-bl-bootstrap-v1\0"        # deterministic-selection salt (§3.2) — DO NOT change
# §3.1 config allocation (proportional to the real corpus; covers kept to test a config with no masks)
ALLOC = {"embellishments": 386, "plates": 356, "medium": 201, "covers": 57}   # Σ = 1000
POOL_VERSION = "bootstrap_v1"
POOL      = "source:pool:bl_book_images:bootstrap_v1"
POOL_NAME = "bl_book_images"      # source.pool.create name → id `source:pool:<name>:v1`; we alias v1→bootstrap
LAB       = "blvh"

# registry entities (§4) — created via source.register (external sources / upstream agents)
PROVIDER  = {"provider": "British Library", "collection": "book images (BigLAM)",
             "uri": "https://www.bl.uk/", "rights": "Public Domain Mark / CC0-1.0 dataset tag",
             "name": "british_library"}
UPSTREAM  = [
    {"provider": "British Library / Microsoft", "collection": "digitisation programme",
     "uri": "https://data.bl.uk/", "name": "bl_microsoft_digitisation",
     "rights": "Public Domain Mark", "note": "process:digitisation"},
    {"provider": "davanstrien", "collection": "RF-DETR crop-tighten segmentation (crop_masks)",
     "uri": "https://huggingface.co/davanstrien/bl-crop-tighten-rfdetrseg-clip10",
     "name": "rfdetr_crop_tighten", "rights": "model", "note": "model:segmentation"},
    {"provider": "Google", "collection": "SigLIP2 so400m embeddings",
     "uri": "https://huggingface.co/google/siglip2-so400m-patch16-256",
     "name": "siglip2_so400m", "rights": "model", "note": "model:embedding"},
    {"provider": "British Library", "collection": "blbooks-parquet (OCR/book metadata companion)",
     "uri": "https://huggingface.co/datasets/biglam/blbooks-parquet",
     "name": "blbooks_parquet", "rights": "CC0-1.0 dataset tag", "note": "dataset:ocr_companion"},
]


# ── Deterministic selection (§3.2) — pure, hypothesis-independent ─────────────
def sel_key(fname):
    return hashlib.sha256(NS + str(fname).encode("utf-8")).hexdigest()

def select_deterministic(rows, n):
    """`rows` = iterable of dicts each carrying at least 'fname'. Sort ascending by SHA256(ns+fname),
    take the first n. Order-independent + reproducible from fname alone (no research signal)."""
    keyed = sorted(((sel_key(r["fname"]), r) for r in rows if r.get("fname")), key=lambda t: t[0])
    return [dict(r, selection_hash=k) for k, r in keyed[:n]]

def record_id_of(fname):
    """The leading British Library system number parsed from the filename (§5/§7). Book-level id.

    Kept VERBATIM, leading zeros included: `blbooks-parquet.record_id` is a zero-padded string
    (e.g. '002263919'), so stripping the padding makes the §7 join unmatchable."""
    m = re.match(r"\s*([0-9]{3,})", str(fname or ""))
    return m.group(1) if m else None

def safe_id(config, row_index, fname):
    """Stable per-image id, already in the Source layer's id alphabet (lowercase [a-z0-9_]).

    `source.acquire` slugs the id_field value the same way (source.py `_slug`: lowercase,
    non-alnum → `_`, edges stripped) when minting `source:item:<src>:<id>`. Emitting the id
    pre-slugged keeps the ids this loader builds bridge endpoints from IDENTICAL to the stored
    item ids — mixed case or a trailing `_` here makes every `source.bridge` dst miss."""
    base = re.sub(r"[^a-z0-9]+", "_", str(fname or "").lower()).strip("_")[:48]
    base = base.strip("_") or str(row_index)
    return f"{config}_{row_index}_{base}"


# ── HF acquisition (LIVE — runs on the VPS; efficient parquet stream, /rows fallback) ─
def _have(mod):
    import importlib.util
    return importlib.util.find_spec(mod) is not None

def stream_config_rows(config, split, log):
    """Yield source-metadata dicts for EVERY row in a config (fname + coordinates + verbatim fields).
    The deterministic selection (§3.2) needs the full fname population, so this streams metadata only.
    Prefers a columnar parquet read (huggingface_hub + pyarrow) — cheap over ~1M rows — and falls back
    to the HF Dataset Viewer /rows API (heavy: 100/page). Never downloads image binaries."""
    # 1) efficient: parquet column scan via huggingface_hub + pyarrow (metadata columns only)
    if _have("huggingface_hub") and _have("pyarrow"):
        try:
            yield from _stream_parquet(config, split, log); return
        except Exception as exc:
            log(f"  parquet stream failed ({exc}); falling back to /rows API")
    # 2) fallback: /rows pagination (stdlib) — bounded by --limit in practice
    yield from _stream_rows_api(config, split, log)

# HF's parquet mirror branch: every dataset is auto-converted to parquet under this revision and
# served from huggingface.co /resolve (CDN) — a path fully independent of the datasets-server
# /filter (DuckDB) index layer, which can be down while the data itself is perfectly healthy.
_PQ_REV = "refs%2Fconvert%2Fparquet"

def _pq_dataset(dataset, config, split):
    """A pyarrow dataset over the parquet mirror, read via HfFileSystem HTTP range requests —
    only the columns a scan asks for are ever transferred."""
    from huggingface_hub import HfFileSystem
    import pyarrow.dataset as pds
    fs = HfFileSystem()
    paths = sorted(fs.glob("datasets/%s@%s/%s/%s/*.parquet" % (dataset, _PQ_REV, config, split)))
    if not paths:
        raise RuntimeError("no parquet mirror files for %s %s/%s" % (dataset, config, split))
    return pds.dataset(paths, filesystem=fs, format="parquet")

def _json_safe(row):
    """Parquet rows can carry timestamps/bytes; source atoms travel as JSON."""
    o = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            v = v.isoformat()
        elif isinstance(v, bytes):
            v = v.hex()
        o[k] = v
    return o

def _stream_parquet(config, split, log):
    """Column-pruned scan of the parquet mirror. Only the metadata columns are transferred — the
    image binary column never moves, so a config whose mirror weighs tens of GB streams in tens of
    MB. (The previous approach hf_hub_download'ed whole image-bearing shards: 46.9 GB for
    embellishments alone, hundreds for plates — no seed host survives that.)"""
    dset = _pq_dataset(DATASET, config, split)
    want = [c for c in ("fname", "date", "image_type") if c in dset.schema.names]
    n = 0
    for batch in dset.to_batches(columns=want):
        for r in batch.to_pylist():
            yield {"fname": r.get("fname"), "config": config, "split": split, "row_index": n,
                   "date_raw": r.get("date"), "image_type_raw": r.get("image_type")}
            n += 1
    log(f"  streamed {n} rows for config '{config}' via the parquet mirror")

def _rows_url(config, split, offset, length):
    return ("https://datasets-server.huggingface.co/rows"
            f"?dataset={DATASET.replace('/', '%2F')}&config={config}&split={split}"
            f"&offset={offset}&length={length}")

def _stream_rows_api(config, split, log, page=100, cap=None):
    import urllib.request
    off = 0
    while True:
        try:
            with urllib.request.urlopen(_rows_url(config, split, off, page), timeout=30) as r:
                data = json.load(r)
        except Exception as exc:
            log(f"  /rows fetch failed at offset {off}: {exc}"); return
        rows = data.get("rows") or []
        if not rows:
            return
        for rr in rows:
            row = rr.get("row", {}); idx = rr.get("row_idx", off)
            yield {"fname": row.get("fname") or row.get("source_filename"),
                   "config": config, "split": split, "row_index": idx,
                   "date_raw": row.get("date"), "image_type_raw": row.get("image_type")}
        off += len(rows)
        if cap and off >= cap:
            return
        total = data.get("num_rows_total")
        if total and off >= total:
            return

class JoinResult(dict):
    """Resolved rows, with the keys whose LOOKUP FAILED kept SEPARATE.

    "the row does not exist" and "the query could not be run" are different facts. Conflating them
    records an upstream outage as the assertion "this image has no mask" — a guess, which §6.2/§7
    forbid. Callers must consult `.errors` before treating an absence as data."""

    def __init__(self, *a, **kw):
        dict.__init__(self, *a, **kw)
        self.errors = {}        # key -> the error that stopped the lookup
        self.attempted = 0      # keys we tried to resolve

    @property
    def error_rate(self):
        return (len(self.errors) / float(self.attempted)) if self.attempted else 0.0


def join_stats(res):
    """(attempted, errors, rate) for a join result — tolerant of a plain dict (jsonl side-load)."""
    att = getattr(res, "attempted", len(res or {}))
    errs = len(getattr(res, "errors", {}) or {})
    return att, errs, ((errs / float(att)) if att else 0.0)


def _filter_rows(url):
    """One /filter call. Raises on anything that is not a parseable row list — an error body served
    with HTTP 200 (`{"error": "the dataset index is loading"}`) is a failed lookup, not zero rows."""
    import urllib.request
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    if not isinstance(data, dict) or "rows" not in data:
        raise RuntimeError(str((data or {}).get("error") or data)[:200])
    return data.get("rows") or []


def _filter_url(config, split, where, length=100, offset=0):
    import urllib.parse
    return ("https://datasets-server.huggingface.co/filter"
            f"?dataset={DATASET.replace('/', '%2F')}&config={config}&split={split}"
            f"&where={urllib.parse.quote(where)}&offset={offset}&length={length}")

def _parquet_mask_join(items, log):
    """/filter-free crop_masks join over the parquet mirror. Returns (hits, answered): `answered`
    is every fname whose split scan COMPLETED — for those, absence is the genuine fact "no mask",
    not an error.

    Hand-rolled, one row group at a time: per group only the fname column is fetched, and a group
    with hits is materialised alone, take()n down to the hit rows before any Python conversion.
    Peak memory stays ~one decompressed row group (≤ ~1.4 GB for plates). A pyarrow dataset scan
    with an isin filter prefetches several mask-bearing fragments at once and OOMs a 15 GB cgroup —
    do not put one back here."""
    from huggingface_hub import HfFileSystem
    import pyarrow.parquet as pq
    fs = HfFileSystem()
    by_split = {}
    for it in items:
        fn = it.get("fname") if isinstance(it, dict) else it
        cfg = it.get("config") if isinstance(it, dict) else None
        if not fn:
            continue
        for sp in ((cfg,) if cfg in MASK_SPLITS else MASK_SPLITS):
            by_split.setdefault(sp, set()).add(fn)
    hits, answered = {}, set()
    for sp, want in sorted(by_split.items()):
        pending = set(want) - set(hits)
        if not pending:
            answered |= want
            continue
        paths = sorted(fs.glob("datasets/%s@%s/%s/%s/*.parquet" % (DATASET, _PQ_REV, MASKS_CFG, sp)))
        if not paths:
            raise RuntimeError("no parquet mirror files for crop_masks/" + sp)
        n = 0
        for path in paths:
            if not pending:
                break
            with fs.open(path, "rb") as f:
                pf = pq.ParquetFile(f)
                for rg in range(pf.metadata.num_row_groups):
                    if not pending:
                        break
                    names = pf.read_row_group(rg, columns=["fname"]).column(0).to_pylist()
                    idx = [i for i, nm in enumerate(names) if nm in pending]
                    if not idx:
                        continue
                    tbl = pf.read_row_group(rg).take(idx)
                    for row in tbl.to_pylist():
                        fn = row.get("fname")
                        if fn in pending:
                            hits[fn] = _json_safe(row); pending.discard(fn); n += 1
                    del tbl
        answered |= want
        log("  parquet mirror crop_masks/%s: %d of %d resolved" % (sp, n, len(want)))
    return hits, answered


def _parquet_book_join(record_ids, log):
    """/filter-free blbooks join over the parquet mirror, by record_id. Book-level: the per-page
    `text` column (the bulk of the 16 GB mirror) is never transferred.

    Hand-rolled instead of a dataset-filter scan: 61 files × many row groups × ~20 columns as
    sequential HTTP range reads is tens of minutes. Per row group this reads (1) nothing when the
    footer's record_id min/max statistics exclude every wanted id, else (2) just the record_id
    column, else (3) the row group minus `text`. Files are scanned on a small thread pool."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem
    from concurrent.futures import ThreadPoolExecutor
    import threading
    fs = HfFileSystem()
    paths = sorted(fs.glob("datasets/%s@%s/default/train/*.parquet" % (OCR_DS, _PQ_REV)))
    if not paths:
        raise RuntimeError("no parquet mirror files for %s" % OCR_DS)
    remaining = set(record_ids); hits = {}; lock = threading.Lock()

    def _s(v):
        return v.decode("utf-8", "replace") if isinstance(v, bytes) else v

    def scan(path):
        with fs.open(path, "rb") as f:
            pf = pq.ParquetFile(f)
            names = pf.schema_arrow.names
            if "record_id" not in names:
                raise RuntimeError("record_id column missing in " + path)
            ci = names.index("record_id")
            cols = [c for c in names if c != "text"]
            for rg in range(pf.metadata.num_row_groups):
                with lock:
                    want = set(remaining)
                if not want:
                    return
                st = pf.metadata.row_group(rg).column(ci).statistics
                if st is not None and st.has_min_max:
                    lo, hi = _s(st.min), _s(st.max)
                    if not any(lo <= r <= hi for r in want):
                        continue
                rids = pf.read_row_group(rg, columns=["record_id"]).column(0).to_pylist()
                found = set(rids) & want
                if not found:
                    continue
                rows = pf.read_row_group(rg, columns=cols).to_pylist()
                with lock:
                    for row in rows:
                        rid = row.get("record_id")
                        if rid in remaining:
                            hits[rid] = _json_safe(row); remaining.discard(rid)

    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(scan, paths))
    log("  parquet mirror blbooks: %d of %d resolved" % (len(hits), len(record_ids)))
    return hits, set(record_ids)


# After this many consecutive outright lookup failures with not one success, the /filter index is
# down, not flaky — stop burning a round-trip per key (a full 1000-row run wastes ~30 min on doomed
# calls) and let the remaining keys go straight to the mirror rescue.
FILTER_BREAKER_AFTER = 10

def _mirror_rescue(out, items, joiner, label, log):
    """When /filter lookups failed above the tolerated rate, retry JUST the failed keys against the
    parquet mirror. A key the mirror scan answered leaves `errors` (resolved, or genuinely absent);
    a mirror failure leaves the original error standing — never a guess."""
    att, err, rate = join_stats(out)
    if not err or rate <= MAX_JOIN_ERROR_RATE:
        return out
    if not (_have("huggingface_hub") and _have("pyarrow")):
        log("  %s: /filter degraded (%d/%d failed) and no huggingface_hub+pyarrow — cannot fall back" % (label, err, att))
        return out
    log("  %s: /filter degraded (%d/%d lookups failed) — falling back to the parquet mirror" % (label, err, att))
    try:
        hits, answered = joiner(items, log)
    except Exception as exc:
        log("  %s: parquet mirror fallback failed: %s" % (label, exc))
        return out
    for k, row in hits.items():
        out[k] = row
    for k in answered:
        out.errors.pop(k, None)
    return out


def fetch_masks_for(items, log):
    """Join crop_masks on fname for the SELECTED (non-cover) images (§6.2). Bounded lookup, never a
    full scan. Best-effort per fname; a missing join stays a queryable 'no mask' state, not a guess.

    `items` are the selected image records (dicts carrying `fname` + `config`); the mask split is the
    image's own config, since crop_masks is split per image type. A bare fname string is still
    accepted and then probes each mask split in turn."""
    out = JoinResult()
    streak = 0
    for it in items:
        fn = it.get("fname") if isinstance(it, dict) else it
        cfg = it.get("config") if isinstance(it, dict) else None
        if not fn:
            continue
        out.attempted += 1
        if streak >= FILTER_BREAKER_AFTER and not out:
            out.errors[fn] = "skipped: /filter circuit open (%d consecutive failures)" % streak
            continue
        answered = False; last = None
        for sp in ((cfg,) if cfg in MASK_SPLITS else MASK_SPLITS):
            try:
                rows = _filter_rows(_filter_url(MASKS_CFG, sp, "\"fname\" = '%s'" % str(fn).replace("'", "''"), length=1))
                answered = True                     # the index answered: 0 rows here IS "no mask"
                if rows:
                    out[fn] = rows[0].get("row", {})
                    break
            except Exception as exc:
                last = exc
                log(f"  crop_masks lookup FAILED for {fn} [{sp}]: {exc}")
        if fn not in out and not answered:
            out.errors[fn] = "%s: %s" % (type(last).__name__, last)
            streak += 1
            if streak == FILTER_BREAKER_AFTER and not out:
                log("  crop_masks: %d consecutive /filter failures, none succeeded — skipping the rest" % streak)
        else:
            streak = 0
    failed = [it for it in items
              if ((it.get("fname") if isinstance(it, dict) else it) in out.errors)]
    return _mirror_rescue(out, failed, _parquet_mask_join, "crop_masks", log)

def fetch_books_for(record_ids, log):
    """Join blbooks-parquet on record_id for the distinct SELECTED records (§7). Book-level only —
    never asserts page alignment."""
    out = JoinResult()
    streak = 0
    for rid in record_ids:
        out.attempted += 1
        if streak >= FILTER_BREAKER_AFTER and not out:
            out.errors[rid] = "skipped: /filter circuit open (%d consecutive failures)" % streak
            continue
        try:
            url = ("https://datasets-server.huggingface.co/filter"
                   "?dataset=" + OCR_DS.replace("/", "%2F") + "&config=default&split=train"
                   "&where=" + __import__("urllib.parse", fromlist=["quote"]).quote("\"record_id\" = '%s'" % rid)
                   + "&offset=0&length=1")
            rows = _filter_rows(url)
            if rows:
                out[rid] = rows[0].get("row", {})
            streak = 0
        except Exception as exc:
            out.errors[rid] = "%s: %s" % (type(exc).__name__, exc)
            log(f"  blbooks lookup FAILED for {rid}: {exc}")
            streak += 1
            if streak == FILTER_BREAKER_AFTER and not out:
                log("  blbooks: %d consecutive /filter failures, none succeeded — skipping the rest" % streak)
    return _mirror_rescue(out, sorted(out.errors), _parquet_book_join, "blbooks", log)


# ── The bootstrap flow (§10), driven through a pluggable `dispatch(method, data)` ─
class Bootstrap:
    def __init__(self, dispatch, log=print):
        self.d = dispatch          # dispatch(method:str, data:dict) -> result dict (raises on error)
        self.log = log

    def _src_id(self, name):
        return "source:src:" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

    def register_all(self):
        self.d("source.register", dict(provider=PROVIDER["provider"], collection=PROVIDER["collection"],
                                       uri=PROVIDER["uri"], rights=PROVIDER["rights"], name=PROVIDER["name"]))
        for u in UPSTREAM:
            self.d("source.register", dict(provider=u["provider"], collection=u["collection"],
                                           uri=u["uri"], rights=u.get("rights", ""), name=u["name"]))
        self.log("  [1] registered provider + %d upstream sources/models/processes" % len(UPSTREAM))

    def acquire_images(self, selected):
        """One Source Atom per selected image row, dropped into the (open) pool."""
        src = self._src_id(PROVIDER["name"])
        recs = []
        for r in selected:
            fn = r["fname"]; rid = record_id_of(fn)
            recs.append({
                "id": safe_id(r["config"], r["row_index"], fn),
                "concept": "source_image",
                "dataset_id": DATASET, "config": r["config"], "split": r["split"], "row_index": r["row_index"],
                "fname": fn, "date_raw": r.get("date_raw"), "image_type_raw": r.get("image_type_raw"),
                "record_id": rid, "media_type": "image/jpeg", "display_mode": "external_resolved_image",
                "selection_hash": r["selection_hash"], "attribution": "British Library",
                "rights": PROVIDER["rights"],
            })
        # ensure the pool exists (open) before acquiring into it
        self.d("source.pool.create", {"name": POOL_NAME, "source": src, "version": POOL_VERSION,
                                      "rule": "BL-REAL-1000 deterministic bootstrap (SHA256(fname), config-proportional 386/356/201/57); infrastructure verification, not historically representative"})
        pool_id = _pool_v1(POOL_NAME)
        res = self.d("source.acquire", {"source": src, "rule": "BL-REAL-1000 real image rows (deterministic, hypothesis-independent)",
                                        "records": recs, "id_field": "id", "pool": pool_id})
        if res is None:
            raise RuntimeError("source.acquire refused %d records into %s — see the preceding "
                               "[import] refused line" % (len(recs), pool_id))
        self.log("  [2] acquired %s image Source Atoms into %s" % (res.get("acquired_count", len(recs)), pool_id))
        return pool_id, recs

    def acquire_masks(self, images, masks_by_fname):
        """crop_masks predictions as SEPARATE observation atoms, bridged observed_from the image (§6.2).
        Covers get none (they carry no upstream mask). Scores < 0.3 are retained (0.3 is a viewer
        default, not an ingestion rule)."""
        src = self._src_id("rfdetr_crop_tighten"); recs = []; bridges = []
        for im in images:
            if im["config"] == "covers":
                continue                                  # deliberately no mask observation for covers
            m = masks_by_fname.get(im["fname"])
            if not m:
                continue                                  # unresolved join stays a 'no mask' state
            oid = "obs_mask_" + im["id"]
            recs.append(dict(m, id=oid, concept="source_obs_mask", observation_of="source:item:%s:%s" % (src_slug(src), im["id"]),
                             interpretation_status="MACHINE_PREDICTION", model_id="davanstrien/bl-crop-tighten-rfdetrseg-clip10",
                             source_threshold=0.10))
            bridges.append((oid, im["id"]))
        if recs:
            self.d("source.acquire", {"source": src, "rule": "RF-DETR crop-mask predictions (machine observation; all instances retained)",
                                      "records": recs, "id_field": "id"})
            for oid, iid in bridges:
                self.d("source.bridge", {"src": "source:item:%s:%s" % (src_slug(src), oid),
                                         "dst": "source:item:%s:%s" % (src_slug(self._src_id(PROVIDER["name"])), iid),
                                         "rel": "observed_from", "by": "source:src:rfdetr_crop_tighten"})
        self.log("  [3] crop-mask observations: %d (covers intentionally none)" % len(recs))

    def acquire_books(self, images, books_by_rid):
        """Distinct record_id → one book Source Atom from blbooks-parquet (§7). Book-level; no page
        alignment asserted. A record with no match stays unresolved."""
        src = self._src_id("blbooks_parquet"); recs = []
        seen = set()
        for im in images:
            rid = im.get("record_id")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            b = books_by_rid.get(rid)
            if not b:
                continue
            recs.append(dict(b, id="book_" + rid, concept="source_book", record_id=rid,
                             metadata_source=OCR_DS, join_status="BOOK_VERIFIED"))
        if recs:
            self.d("source.acquire", {"source": src, "rule": "BL book metadata by record_id (book-level; page alignment not asserted)",
                                      "records": recs, "id_field": "id"})
        self.log("  [4] book metadata atoms: %d (distinct verified record_ids)" % len(recs))

    def freeze_and_declare(self, pool_id):
        self.d("source.pool.freeze", {"pool": pool_id})
        self.d("source.lab.declare", {"lab": LAB, "klass": "CORPUS", "pool": pool_id,
                                      "primary_source": self._src_id(PROVIDER["name"]),
                                      "fixture_policy": "no synthetic fixtures in this pool; blvh:image:mock:* are labelled fixtures only"})
        self.log("  [5] pool FROZEN + blvh declared CORPUS on %s" % pool_id)


def src_slug(src_id):
    return src_id.split(":")[-1]

def _pool_v1(name):
    return "source:pool:%s:%s" % (name, POOL_VERSION)


# ── entry points ─────────────────────────────────────────────────────────────
def run_declared(kernel, decl, ctl=None):
    """The DECLARED entry — what a boot calls for `app/config/source/bl_real.json`.

    Everything below used to sit inside the platform's `schedule_source_bootstrap`, which meant the
    heart knew this corpus's directory, its three file names, which libraries its live path wants
    and what "degraded" means for it. None of that is boot machinery; all of it is British Library
    knowledge, so it lives here, next to the acquisition it belongs to.

    What the caller still owns is the managed unit around this call — the run-once sentinel, the
    heartbeat, the hard cap — and it learns from the returned `sentinel` whether this run earned the
    right to not happen again."""
    try:
        from app.scripts import _declared_import as di
    except ImportError:                       # run directly: the script's own directory is sys.path[0]
        import _declared_import as di

    ctl = ctl or di.Ctl()
    corpus = di.corpus_dir(decl)
    img = os.path.join(corpus, "bl_images.jsonl") if corpus else ""
    offline = bool(img) and os.path.exists(img)

    state, digest = di.decide(kernel, decl)
    if state == "skip":
        return {"status": "skipped", "detail": "corpus unchanged", "sentinel": True}

    # A FROZEN pool is never acquired into (`source.acquire` refuses it by law). Asked first, in O(1): a frozen,
    # populated pool whose bundle this cell has no record of is left exactly as it is — nothing is acquired and
    # nothing is adopted (a cell starts from Genesis; a changed corpus is a new seed).
    pst = di.dispatcher(kernel)("source.status", {"pool": decl.get("pool") or POOL}) or {}
    if pst.get("frozen") and pst.get("total"):
        return {"status": "frozen", "sentinel": False,
                "detail": "%s is frozen with %s atoms and this cell holds no matching import record — "
                          "nothing acquired" % (decl.get("pool") or POOL, pst.get("total"))}

    opts = {"freeze": True, "limit": None}

    if offline:
        # PREFER the bundle the seed carries. It loads with no Hugging Face access and no
        # huggingface_hub/pyarrow on the target, so an extraction is deterministic and immune to the
        # /rows 502s and /filter outages that make the live path unreliable.
        opts["images_jsonl"] = img
        for key, fn in (("masks_jsonl", "bl_masks.jsonl"), ("books_jsonl", "bl_books.jsonl")):
            p = os.path.join(corpus, fn)
            if os.path.exists(p):
                opts[key] = p
        ctl.say("loading the bundled corpus offline from %s (no Hugging Face)" % corpus)
    else:
        # The live fallback's ROBUST path — the parquet mirror plus the /filter-outage join
        # fallback — needs these two. Without them the loader drops to the /rows API, which a 502
        # storm silently truncates into an under-filled pool that reads as a complete one.
        ctl.say("no bundled corpus — ensuring huggingface_hub + pyarrow for the live path")
        try:
            from lib.akasha.api.client import Environment as Symbiosis
            for mod in ("huggingface_hub", "pyarrow"):
                Symbiosis.ensure(mod, mod, scope="[SrcBootstrap]",
                                 feature="BL parquet stream + join fallback", timeout=300)
        except Exception as exc:
            ctl.say("parquet deps not ensured (%s) — falling back to the /rows path" % exc)
        ctl.say("starting the live acquisition")

    out = run(di.dispatcher(kernel), opts, log=ctl.say) or {}

    if not out.get("images"):
        return {"status": "no_data", "detail": "0 images acquired", "sentinel": False}
    if out.get("degraded"):
        # A PARTIAL failure, and the one that must not be latched: the images come from /rows and
        # the mask/book joins from /filter, so a dead /filter yields a full-looking image pool with
        # no observations on it. The loader withholds the freeze; sentinelling here would make that
        # silently-degraded corpus permanent.
        return {"status": "degraded", "sentinel": False,
                "detail": "join lookups failed (crop_masks %s/%s, blbooks %s/%s) — pool left unfrozen"
                          % (out.get("mask_errors"), out.get("mask_lookups"),
                             out.get("book_errors"), out.get("book_lookups")),
                "mask_errors": out.get("mask_errors"), "book_errors": out.get("book_errors")}

    di.record_hash(kernel, decl, digest, {"images": out.get("images")})
    return {"status": "complete", "sentinel": True,
            "detail": "%s image atoms in %s (%s records)"
                      % (out.get("images"), out.get("pool"), out.get("record_ids")),
            "images": out.get("images"), "pool": out.get("pool")}



def run(dispatch, opts, log=print):
    """The full §10 sequence. `dispatch(method,data)` writes through source.* (socket or in-process)."""
    bs = Bootstrap(dispatch, log)
    bs.register_all()

    # 4. stream metadata + 5. deterministic select per config
    selected = []
    if opts.get("images_jsonl"):
        rows = [json.loads(l) for l in open(opts["images_jsonl"], encoding="utf-8") if l.strip()]
        by_cfg = {}
        for r in rows:
            by_cfg.setdefault(r.get("config", "plates"), []).append(r)
        for cfg, n in ALLOC.items():
            picked = select_deterministic(by_cfg.get(cfg, []), min(n, opts.get("limit") or n))
            selected += picked
            log("  select[%s]: %d of %d candidates" % (cfg, len(picked), len(by_cfg.get(cfg, []))))
    else:
        for cfg, n in ALLOC.items():
            take = min(n, opts.get("limit") or n)
            log("  streaming '%s' from HF for deterministic selection…" % cfg)
            rows = list(stream_config_rows(cfg, SPLIT, log))
            picked = select_deterministic(rows, take)
            selected += picked
            log("  select[%s]: %d of %d streamed" % (cfg, len(picked), len(rows)))

    pool_id, images = bs.acquire_images(selected)

    # 6. crop-mask observations (non-cover), 7. book metadata
    non_cover = [im for im in images if im["config"] != "covers"]
    if opts.get("masks_jsonl"):
        masks = {}
        for l in open(opts["masks_jsonl"], encoding="utf-8"):
            if l.strip():
                m = json.loads(l); masks[m.get("fname")] = m
    else:
        masks = fetch_masks_for(non_cover, log)
    bs.acquire_masks(images, masks)

    rids = sorted({im.get("record_id") for im in images if im.get("record_id")})
    if opts.get("books_jsonl"):
        books = {}
        for l in open(opts["books_jsonl"], encoding="utf-8"):
            if l.strip():
                b = json.loads(l); books[str(b.get("record_id"))] = b
    else:
        books = fetch_books_for(rids, log)
    bs.acquire_books(images, books)

    # 10. freeze + declare — but ONLY on a corpus whose joins actually ran.
    # A lookup that FAILED is an infrastructure outage, not the fact "no mask / no book". Freezing
    # on top of it would latch a silently-degraded corpus that reads exactly like a complete one, so
    # the freeze is withheld and the caller is told the run is degraded (kernel: no run-once
    # sentinel → retried next boot) instead of guessing (§6.2/§7).
    m_att, m_err, m_rate = join_stats(masks)
    b_att, b_err, b_rate = join_stats(books)
    max_rate = float(opts.get("max_join_error_rate", MAX_JOIN_ERROR_RATE))
    degraded = max(m_rate, b_rate) > max_rate
    frozen = False
    if degraded:
        log("  [5] FREEZE WITHHELD — join lookups FAILED: crop_masks %d/%d, blbooks %d/%d "
            "(> %.0f%% tolerated). These are outages, NOT 'no mask'/'no book'; the pool stays OPEN "
            "so the bootstrap is retried rather than latching a degraded corpus."
            % (m_err, m_att, b_err, b_att, max_rate * 100))
    elif opts.get("freeze", True):
        bs.freeze_and_declare(pool_id)
        frozen = True
    return {"pool": pool_id, "images": len(images), "record_ids": len(rids),
            "mask_lookups": m_att, "mask_errors": m_err,
            "book_lookups": b_att, "book_errors": b_err,
            "degraded": degraded, "frozen": frozen}


def main():
    ap = argparse.ArgumentParser(description="BL-REAL-1000 real-data Source bootstrap (directive v0.1).")
    ap.add_argument("--as", dest="as_id", default="admin", help="admin/librarian user id to write as (e.g. --as henri)")
    ap.add_argument("--base", default=None, help="daemon data dir (default AKASHA_DATA_DIR or ./data)")
    ap.add_argument("--limit", type=int, default=None, help="cap rows PER CONFIG (smoke run; omit for the full 1000)")
    ap.add_argument("--images-jsonl", default=None, help="offline: JSONL of real image rows (skip HF stream)")
    ap.add_argument("--masks-jsonl", default=None, help="offline: JSONL of crop_mask rows keyed by fname")
    ap.add_argument("--books-jsonl", default=None, help="offline: JSONL of book rows keyed by record_id")
    ap.add_argument("--no-freeze", dest="freeze", action="store_false", default=True, help="leave the pool OPEN")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print("[!] No Cell daemon at %s. Start one: python akasha.py --serve" % base, file=sys.stderr); sys.exit(2)
    gw = client.connect(base)

    def dispatch(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method, "params": {"session_token": args.as_id, "data": data}, "id": "b"}, "local")
        if isinstance(r, dict) and "error" in r:
            raise RuntimeError("%s: %s" % (method, r["error"].get("message")))
        return r.get("result") if isinstance(r, dict) and "result" in r else r

    opts = {"limit": args.limit, "images_jsonl": args.images_jsonl, "masks_jsonl": args.masks_jsonl,
            "books_jsonl": args.books_jsonl, "freeze": args.freeze}
    print("\n  BL-REAL-1000 bootstrap → %s" % POOL)
    out = run(dispatch, opts)
    print("\n  done: %d image atoms in %s (%d distinct records)" % (out["images"], out["pool"], out["record_ids"]))
    print("  verify (guest):  source.pool.ls pool=%s  ·  source.status pool=%s  ·  source.audit lab=%s" % (out["pool"], out["pool"], LAB))
    print("  Source Viewer:   /labo/source/#src=pool/%s\n" % out["pool"])
    gw.close()


if __name__ == "__main__":
    main()
