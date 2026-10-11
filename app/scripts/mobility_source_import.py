#!/usr/bin/env python3
"""
mobility_source_import.py — wire the REAL EU Travel Survey (2014) respondent corpus into the Akasha
**Source Data Layer** for the Mobility CORPUS laboratory (Mobility Source Data Import Directive v0.1).

This is the BACKEND WIRING. The front end collects the actual dataset (the JRC "EU Travel Survey on
demand for innovative transport systems", DOI 10.2905/JRC.KMH9E9G / Harvard Dataverse
10.7910/DVN/P82V9X v1.1) and hands this script the released respondent rows + documentation files;
the script drives the `source.*` operators, in the directive's order (§12), against a live Cell:

  1. Register the JRC dataset (logical identity = DOI; retrieval location kept distinct).
  2. Acquire the COMPLETE respondent-level corpus — one Source Atom per released row, verbatim coded
     payload, missing/refused/DK/NA codes preserved distinctly. NO semantic filtering (never by
     country / mode / age / attitude / completeness / later hypotheses).
  3. Hash the data + documentation artifacts and record retrieval provenance on the pool.
  4. Freeze source:pool:mobility:eu_travel_survey_2014:v1_1 (immutable, Akasha-Time stamped).
  5. Declare Mobility a CORPUS lab that samples_from the frozen pool.
  6. (optional) Create a deterministic experiment SNAPSHOT/subset (Source Sample) — the full
     population stays visible in the pool.
  7. (optional) Bridge traceable existing Mobility opinion/claim Atoms → source rows (based_on).
  8. Audit.

The survey/question/answer/scale/country ONTOLOGY (§6/§7) is authored SEPARATELY by the front end
(see docs/for-llm/mobility-source-import-guide.md) — individual answers stay Source Atoms; only the
instrument structure and code semantics become ontology.

Start a daemon (python akasha.py --serve), then e.g.:
    python app/scripts/mobility_source_import.py --as <admin_id> \
        --records respondents.jsonl --id-field respondent_id \
        --artifact eu_travel_survey_2014.csv --artifact codebook.pdf \
        --snapshot pilot --snapshot-n 500 --snapshot-strata country
`--records` is JSONL (one released row per line) or use `--csv <file>`. `--as` must be THIS cell's
genesis admin id (the universal writes go to the shared nucleus, guest-readable — as with the other
source-layer scripts).
"""
import argparse
import csv as _csv
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

# Logical dataset identity (§2, §12.1) — DOIs are identity; the retrieval URL is a locator.
JRC_DOI = "10.2905/JRC.KMH9E9G"
DATAVERSE_DOI = "10.7910/DVN/P82V9X"
DATASET_VERSION = "1.1"
SOURCE_ID = "source:src:mobility_eu_travel_survey_2014"
POOL = "source:pool:mobility:eu_travel_survey_2014:v1_1"
LAB = "mobility"
BATCH = 2000                      # rows per acquisition call (keeps each RPC payload bounded)


def _hash_artifact(path):
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk); size += len(chunk)
    return {"name": os.path.basename(path), "sha256": h.hexdigest(), "size": size,
            "uri": os.path.abspath(path)}


def _load_rows(records, csvfile):
    if records:
        with open(records, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]
    if csvfile:
        with open(csvfile, encoding="utf-8", newline="") as fh:
            return list(_csv.DictReader(fh))
    return []


def run(dispatch, rows, opts, log=print):
    """Drive the §12 sequence through a pluggable `dispatch(method, data)` — used by the CLI (socket)
    AND by the kernel's offline boot phase (in-process TRUST_INTERNAL). Registers the JRC source,
    creates the provenance pool, acquires the COMPLETE corpus one-atom-per-row (batched, no
    filtering), freezes, declares Mobility CORPUS, optionally samples, and audits. Returns a summary.
    `rows` may be a list (CLI) or a LAZY iterator/generator (the boot streams the bundled gz); it is
    consumed once in batches and never fully materialized, so a large corpus costs one batch of RAM."""
    artifacts = opts.get("artifacts") or []
    id_field  = opts.get("id_field", "respondent_id")
    retrieval = opts.get("retrieval", "")
    batch     = int(opts.get("batch") or BATCH)

    dispatch("source.register", {"provider": "European Commission Joint Research Centre (JRC)",
                                 "collection": "EU Travel Survey on demand for innovative transport systems (2014)",
                                 "name": "mobility_eu_travel_survey_2014", "doi": JRC_DOI,
                                 "version": DATASET_VERSION, "uri": f"https://doi.org/{JRC_DOI}",
                                 "retrieval_uri": retrieval or f"https://doi.org/{DATAVERSE_DOI}",
                                 "rights": "See dataset licence (JRC Data Catalogue / Harvard Dataverse)"})
    log(f"  [1] source: {SOURCE_ID}  (DOI {JRC_DOI}; Dataverse {DATAVERSE_DOI} v{DATASET_VERSION})")

    dispatch("source.pool.create", {"name": "mobility:eu_travel_survey_2014", "version": "v1_1",
                                    "source": SOURCE_ID, "doi": JRC_DOI, "dataset_version": DATASET_VERSION,
                                    "artifacts": artifacts, "retrieval": retrieval,
                                    "rule": "COMPLETE released respondent-level corpus of the JRC EU Travel "
                                            "Survey 2014 (all 28 EU MS; 1000/country except CY,LU,MT=500); "
                                            "no acquisition-time filtering"})
    log(f"  [2] pool created: {POOL}  ({len(artifacts)} artifact hashes)")

    import itertools
    # `rows` may be a list (CLI) OR a lazy iterator/generator (the offline boot streams the gz).
    # Batch by pulling `batch` items at a time — the whole corpus is NEVER materialized here, so a
    # 26k-row corpus costs one batch of RAM, not the whole file (the boot-OOM the caller hit).
    total_acq = total_unres = 0
    seen = 0
    row_iter = iter(rows)
    first = True
    while True:
        chunk = list(itertools.islice(row_iter, batch))
        if not chunk:
            break
        lo, seen = seen, seen + len(chunk)
        r = dispatch("source.acquire", {"source": SOURCE_ID, "records": chunk, "id_field": id_field,
                                        "pool": POOL, "dataset_version": DATASET_VERSION,
                                        "artifacts": artifacts if first else None,
                                        "rule": f"complete respondent corpus (rows {lo}-{seen - 1})"})
        first = False
        if isinstance(r, dict) and "__error__" in r:
            raise RuntimeError("acquire batch @%d: %s" % (lo, r["__error__"]))
        total_acq += (r or {}).get("acquired", 0); total_unres += (r or {}).get("unresolved", 0)
        log(f"      acquired {seen} rows so far…")
    log(f"  [3] acquired {total_acq} respondent Source Atoms ({total_unres} unresolved/failed, retained)")

    members = at_seq = None
    if opts.get("freeze", True):
        fr = dispatch("source.pool.freeze", {"pool": POOL})
        members = (fr or {}).get("member_count"); at_seq = (fr or {}).get("at_seq")
        log(f"  [4] pool FROZEN: {members} members, at_seq={at_seq}")

    decl = dispatch("source.lab.declare", {"lab": LAB, "klass": "CORPUS", "pool": POOL,
                                           "primary_source": SOURCE_ID,
                                           "fixture_policy": "no synthetic respondents; existing untraceable "
                                                             "atoms remain PARTIAL/UNGROUNDED"})
    log(f"  [5] mobility declared CORPUS → evidence_status={(decl or {}).get('evidence_status')}")

    if opts.get("snapshot"):
        s = dispatch("source.pool.sample", {"pool": POOL, "name": opts["snapshot"],
                                            "rule": f"deterministic experiment subset (seed={opts.get('snapshot_seed','mobility-v0.1')}"
                                                    f"{', strata=' + opts['snapshot_strata'] if opts.get('snapshot_strata') else ''})",
                                            "n": str(opts.get("snapshot_n", 0)), "seed": opts.get("snapshot_seed", "mobility-v0.1"),
                                            "strata": opts.get("snapshot_strata", ""), "model": "mobility-v0.1"})
        log(f"  [6] snapshot: {(s or {}).get('sample')}  n={(s or {}).get('member_count')} (population still visible in the pool)")

    au = dispatch("source.audit", {"lab": LAB})
    log(f"  audit mobility → status={(au or {}).get('evidence_status')} grounded={(au or {}).get('grounded')} "
        f"bridged={(au or {}).get('bridged')}")
    return {"pool": POOL, "acquired": total_acq, "unresolved": total_unres, "members": members,
            "at_seq": at_seq, "evidence_status": (au or {}).get("evidence_status"),
            "grounded": (au or {}).get("grounded"), "bridged": (au or {}).get("bridged")}


def run_declared(kernel, decl, ctl=None):
    """The DECLARED entry — what a boot calls for `app/config/source/mobility_eu_2014.json`.

    26,605 respondent rows, shipped gzipped in the seed and loaded with no Dataverse and no Hugging
    Face access. Three things make that survivable on one small host and all three are this corpus's
    business rather than the boot's:

      · the rows are STREAMED — a generator, one batch resident at a time, never 26k rows in RAM;
      · a run that ran out of cap RESUMES, because each acquired batch advances a cursor the caller
        persists; without it a slow host restarts from row 0 every boot and the pool never converges;
      · a corrected bundle RESETS the corpus first, since a row keeps its declared id and so cannot
        be corrected in place.
    """
    import gzip

    try:
        from app.scripts import _declared_import as di
    except ImportError:
        import _declared_import as di

    ctl = ctl or di.Ctl()
    corpus = di.corpus_dir(decl)
    recs_gz = os.path.join(corpus, "respondents.jsonl.gz") if corpus else ""
    if not recs_gz or not os.path.exists(recs_gz):
        return {"status": "skipped", "sentinel": False,
                "detail": "corpus bundle absent (%s)" % (recs_gz or decl.get("corpus"))}

    members_now = 0
    d = di.dispatcher(kernel)
    try:
        members_now = int(((d("source.status", {"pool": decl.get("pool")}) or {})
                           .get("members")) or 0)
    except Exception:
        members_now = 0
    state, digest = di.decide(kernel, decl, populated=bool(members_now))
    if state == "skip":
        return {"status": "skipped", "detail": "corpus unchanged", "sentinel": True}

    try:
        with open(os.path.join(corpus, "manifest.json"), "r", encoding="utf-8") as fh:
            man = json.load(fh)
    except (OSError, ValueError):
        man = {}

    done = [ctl.progress()]
    if done[0]:
        ctl.say("resuming from row %d (checkpoint)" % done[0])

    def _rows():
        skip = done[0]
        with gzip.open(recs_gz, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                if skip > 0:               # read + discard: no parse, no dispatch, no RAM
                    skip -= 1
                    continue
                yield json.loads(line)

    def _dispatch(method, data):
        r = d(method, data)
        # Advance the cursor only after a batch is acquired — the write is what a resume must not
        # repeat, so the cursor follows the write and never leads it.
        if method == "source.acquire" and isinstance(r, dict):
            done[0] += len(data.get("records") or [])
            ctl.advance(done[0])
        return r

    opts = {"artifacts": man.get("artifacts") or [], "id_field": man.get("id_field", "respondent_id"),
            "retrieval": man.get("retrieval", ""), "batch": 500, "freeze": True,
            "snapshot": "pilot", "snapshot_n": 500, "snapshot_strata": "country"}
    ctl.say("streaming the bundled corpus offline (from row %d)" % done[0])
    try:
        out = run(_dispatch, _rows(), opts, log=ctl.say) or {}
    except TimeoutError as exc:
        # The cap is the platform's ceiling for one run, and `ctl.say` raises it. The cursor already
        # follows every acquired batch, so a run that hits it has LOST NOTHING: report the stop as
        # a resumable partial (no sentinel, so the next start continues from the checkpoint)
        # instead of a failure with a traceback.
        return {"status": "degraded", "sentinel": False,
                "detail": "%s after %d of the corpus rows; the checkpoint is kept and the next start resumes"
                          % (exc, done[0])}

    if not out.get("members"):
        return {"status": "no_data", "sentinel": False, "detail": "0 members"}
    di.record_hash(kernel, decl, digest, {"members": out.get("members")})
    return {"status": "complete", "sentinel": True,
            "detail": "%s members in %s" % (out.get("members"), out.get("pool")),
            "members": out.get("members"), "pool": out.get("pool")}


def main():
    ap = argparse.ArgumentParser(description="Import the EU Travel Survey 2014 into the Source Data Layer.")
    ap.add_argument("--as", dest="as_id", default="admin", help="THIS cell's genesis admin id")
    ap.add_argument("--base", default=None, help="daemon data dir (default AKASHA_DATA_DIR or ./data)")
    ap.add_argument("--records", default=None, help="JSONL of released respondent rows")
    ap.add_argument("--csv", dest="csvfile", default=None, help="CSV of released respondent rows")
    ap.add_argument("--id-field", default="respondent_id",
                    help="the stable per-row id field (respondent id / row coordinate). "
                         "Guarantees exactly one Source Atom per released row.")
    ap.add_argument("--artifact", action="append", default=[], metavar="PATH",
                    help="a data/documentation file to hash + register as retrieval provenance (repeatable)")
    ap.add_argument("--retrieval", default="", help="retrieval locator/mirror (kept distinct from the DOI identity)")
    ap.add_argument("--snapshot", default="", help="also create a deterministic experiment subset with this name (§9)")
    ap.add_argument("--snapshot-n", type=int, default=0, help="subset size (0 = whole pool)")
    ap.add_argument("--snapshot-strata", default="", help="source_metadata field to balance the subset across (e.g. country)")
    ap.add_argument("--snapshot-seed", default="mobility-v0.1", help="deterministic sampling seed")
    ap.add_argument("--bridge", action="append", default=[], metavar="mob_atom=source_item",
                    help="bridge an existing Mobility atom to a source row: based_on (repeatable)")
    ap.add_argument("--no-freeze", dest="freeze", action="store_false", default=True, help="leave the pool OPEN")
    ap.add_argument("--batch", type=int, default=BATCH,
                    help=f"rows per source.acquire call (default {BATCH}; lower it if the daemon "
                         "cannot finish a batch inside --rpc-timeout on slow hosts)")
    ap.add_argument("--rpc-timeout", type=float, default=300.0,
                    help="seconds to wait for each daemon reply (default 300; a batched corpus "
                         "acquire legitimately exceeds the gateway's 60s default on slow hosts)")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print(f"[!] No Cell daemon at {base}. Start one:  python akasha.py --serve", file=sys.stderr)
        sys.exit(2)
    gw = client.connect(base, timeout=args.rpc_timeout)

    def d(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": args.as_id, "data": data}, "id": "m"}, "local")
        return r["result"] if isinstance(r, dict) and "result" in r else \
            {"__error__": (r or {}).get("error") if isinstance(r, dict) else r}

    rows = _load_rows(args.records, args.csvfile)
    if not rows:
        print("[!] no respondent rows — pass --records <jsonl> or --csv <file>", file=sys.stderr)
        gw.close(); sys.exit(3)
    opts = {"artifacts": [_hash_artifact(p) for p in args.artifact], "id_field": args.id_field,
            "retrieval": args.retrieval, "batch": args.batch, "freeze": args.freeze,
            "snapshot": args.snapshot, "snapshot_n": args.snapshot_n,
            "snapshot_strata": args.snapshot_strata, "snapshot_seed": args.snapshot_seed}
    try:
        run(d, rows, opts)
    except Exception as exc:
        print(f"[!] import failed: {exc}", file=sys.stderr); gw.close(); sys.exit(4)

    # optional bridges from existing Mobility atoms to source rows (CLI-only; only where provenance holds)
    bridged = 0
    for b in args.bridge:
        if "=" in b:
            mob, item = b.split("=", 1)
            r = d("source.bridge", {"src": mob.strip(), "dst": item.strip(), "rel": "based_on",
                                    "by": "mobility-lab", "run": "mobility-v0.1"})
            if not (isinstance(r, dict) and "__error__" in r):
                bridged += 1
    if args.bridge:
        print(f"  [7] bridged {bridged}/{len(args.bridge)} existing Mobility atoms (based_on) to source rows")

    print(f"  Inspect:  source.pool.ls pool={POOL}  ·  source.status pool={POOL}  ·  "
          f"source.samples  ·  source.lab.profile lab={LAB}\n")
    gw.close()


if __name__ == "__main__":
    main()
