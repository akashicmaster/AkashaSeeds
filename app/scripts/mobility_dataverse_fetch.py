#!/usr/bin/env python3
"""
mobility_dataverse_fetch.py — TEST-CONTEXT acquisition helper for the EU Travel Survey (2014).

`app/scripts/mobility_source_import.py` deliberately does NOT fetch or generate data — the front supplies
the released respondent rows. This helper is the front's hand: run it in a context that can reach
Harvard Dataverse, and it downloads the REAL dataset (DOI 10.7910/DVN/P82V9X, v1.1), converts the
released tabular file to the importer's JSONL **verbatim** (every coded value, missing/refused/DK code,
and column preserved unchanged — nothing filtered, nothing synthesized), and prints the exact
`mobility_source_import.py` command (with the artifact paths to hash). It is NOT part of the backend
loader contract and never runs on the VPS; it is a convenience for the acquisition experiment.

What it does (all via the stable Dataverse REST API, stdlib only):
  1. List the dataset's files at the pinned version.
  2. Download every file into --out-dir (keeping original names): the tabular data file (the
     Dataverse-ingested `.tab` TSV, always available for tabular uploads) + the documentation
     (codebook / questionnaire / value labels / DDI) — these become the provenance artifacts.
  3. Convert the tabular file → respondents.jsonl, ONE released row per line, all columns verbatim.
     A stable id per row: an existing id column if found (or --id-col), else a synthesized row
     coordinate `<file>:<rownum>` so there is exactly one Source Atom per row and re-runs are
     idempotent. A confidently-detected country column is ALSO mirrored to a `country` key (the
     original column is kept too) so `--snapshot-strata country` and the pool rule work.
  4. Print a summary: row count, columns, id strategy, country column, artifact paths, and the
     ready-to-run import command.

Then hand its output to the importer against a running Cell:
    python akasha.py --serve
    python app/scripts/mobility_dataverse_fetch.py --out-dir mob_data
    #   (copy the printed command, e.g.:)
    python app/scripts/mobility_source_import.py --as <admin_id> \
        --records mob_data/respondents.jsonl --id-field respondent_id \
        --artifact mob_data/<data>.tab --artifact mob_data/<codebook> ...

Restricted/embargoed files need a Dataverse API token: --api-token <t> (sent as X-Dataverse-key).
No data is invented; if the tabular file cannot be located the helper reports it and exits non-zero.
"""
import argparse
import csv
import json
import os
import sys
import urllib.request
import urllib.parse

# Logical identity (mirrors app/scripts/mobility_source_import.py) — DOI is identity, server is retrieval.
DEFAULT_SERVER  = "https://dataverse.harvard.edu"
DEFAULT_DOI     = "10.7910/DVN/P82V9X"     # Harvard Dataverse mirror of the JRC EU Travel Survey 2014
DEFAULT_VERSION = "1.1"

# Column-name heuristics (case-insensitive substring) — used only to LABEL, never to drop/rename data.
_ID_HINTS      = ("respondent_id", "respondentid", "resp_id", "respid", "interview", "record_id", "uuid", "id")
_COUNTRY_HINTS  = ("country", "cntry", "ctry", "nuts0", "geo", "member_state", "isocntry")
_WEIGHT_HINTS   = ("weight", "wgt", "wt", "pond")
_DOC_EXT        = (".pdf", ".docx", ".doc", ".xml", ".json", ".txt", ".rtf", ".xlsx", ".ods", ".sps", ".do")


def _req(url, token=None, accept=None):
    headers = {"User-Agent": "akasha-mobility-fetch/0.1"}
    if token:
        headers["X-Dataverse-key"] = token
    if accept:
        headers["Accept"] = accept
    return urllib.request.Request(url, headers=headers)


def _api_json(server, path, params, token=None):
    url = server.rstrip("/") + path + ("?" + urllib.parse.urlencode(params) if params else "")
    with urllib.request.urlopen(_req(url, token, "application/json"), timeout=60) as r:
        return json.load(r)


def list_files(server, doi, version, token):
    """The dataset's files at the pinned version, via the persistentId API."""
    data = _api_json(server, "/api/datasets/:persistentId/versions/" + urllib.parse.quote(version),
                     {"persistentId": "doi:" + doi}, token)
    files = ((data or {}).get("data") or {}).get("files") or []
    out = []
    for f in files:
        df = f.get("dataFile") or {}
        out.append({
            "id": df.get("id"),
            "filename": df.get("filename") or f.get("label") or ("datafile_%s" % df.get("id")),
            "content_type": df.get("contentType") or "",
            "original_format": df.get("originalFileFormat") or "",
            "tabular": bool(df.get("tabularData") or (df.get("contentType") == "text/tab-separated-values")),
            "size": df.get("filesize") or 0,
            "directory": f.get("directoryLabel") or "",
        })
    return out


def download(server, file_id, dest, token, original=False):
    url = server.rstrip("/") + "/api/access/datafile/%s" % file_id + ("?format=original" if original else "")
    with urllib.request.urlopen(_req(url, token), timeout=300) as r, open(dest, "wb") as fh:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    return dest


def download_ddi(server, doi, dest, token):
    """Dataset-level DDI codebook (variable + value-label semantics) — a provenance artifact."""
    url = server.rstrip("/") + "/api/datasets/export?" + urllib.parse.urlencode(
        {"exporter": "ddi", "persistentId": "doi:" + doi})
    try:
        with urllib.request.urlopen(_req(url, token, "application/xml"), timeout=120) as r, open(dest, "wb") as fh:
            fh.write(r.read())
        return dest
    except Exception as exc:
        print("  [ddi] codebook export unavailable (%s) — continuing without it" % exc, file=sys.stderr)
        return None


def _read_text(path):
    """Decode a downloaded tabular file WITHOUT silent corruption. The prior code used
    encoding='utf-8', errors='replace', which turned every non-UTF-8 byte into U+FFFD — for this
    dataset (Windows-1252 European survey text: õ/ö/ä/é/ñ/î…) that permanently mangled Region and
    Destination. Try codecs STRICTLY in order and keep the first that decodes cleanly: utf-8 (the
    common case), then cp1252 (this dataset's original CSV), then latin-1 (byte-preserving last
    resort). Never errors='replace'."""
    b = open(path, "rb").read()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("latin-1", "replace")   # unreachable (latin-1 never raises), belt-and-suspenders


def _sniff(path):
    head = _read_text(path).split("\n", 1)[0]
    return "\t" if head.count("\t") >= head.count(",") else ","


def _pick(cols, hints):
    low = {c.lower(): c for c in cols}
    # exact-ish first (a column named exactly like a hint), then substring
    for h in hints:
        for lc, orig in low.items():
            if lc == h:
                return orig
    for h in hints:
        for lc, orig in low.items():
            if h in lc:
                return orig
    return None


def tab_to_jsonl(path, out_jsonl, id_col=None, country_col=None, coerce_numeric=False):
    """Convert a released tabular file (Dataverse `.tab` TSV, or a .csv) → JSONL, VERBATIM.

    Every column is preserved unchanged. Values are kept as their exact strings (truly "unchanged" —
    a coded -9 / 997 stays as written) unless --coerce-numeric is asked. A stable `respondent_id` is
    an existing id column, else a synthesized `<file>:<rownum>` coordinate. A detected country column
    is MIRRORED to `country` (original column kept), so stratified sampling + the pool rule work."""
    import io as _io
    delim = _sniff(path)
    base = os.path.basename(path)
    with _io.StringIO(_read_text(path)) as fh:
        reader = csv.DictReader(fh, delimiter=delim)
        cols = reader.fieldnames or []
        id_pick = id_col or _pick(cols, _ID_HINTS)
        ctry_pick = country_col or _pick(cols, _COUNTRY_HINTS)
        wt_pick = _pick(cols, _WEIGHT_HINTS)
        n = 0
        with open(out_jsonl, "w", encoding="utf-8") as out:
            for i, raw in enumerate(reader):
                rec = {}
                for k, v in raw.items():
                    if k is None:
                        continue
                    if coerce_numeric and v is not None and v != "" and _is_number(v):
                        rec[k] = _num(v)
                    else:
                        rec[k] = v
                # stable id: existing column value, else a synthesized row coordinate
                rid = (str(raw.get(id_pick)).strip() if id_pick and raw.get(id_pick) not in (None, "") else None)
                rec["respondent_id"] = rid or ("%s:%d" % (base, i + 2))   # +2: header is row 1, data starts at 2
                rec["row_coordinate"] = "%s:%d" % (base, i + 2)
                if ctry_pick and "country" not in rec and raw.get(ctry_pick) not in (None, ""):
                    rec["country"] = raw.get(ctry_pick)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    return {"rows": n, "columns": cols, "id_col": id_pick, "country_col": ctry_pick,
            "weight_col": wt_pick, "synthesized_id": not id_pick, "delimiter": "TAB" if delim == "\t" else "COMMA"}


def _is_number(s):
    try:
        float(s); return True
    except (TypeError, ValueError):
        return False


def _num(s):
    f = float(s)
    return int(f) if f.is_integer() and "." not in str(s) and "e" not in str(s).lower() else f


def main():
    ap = argparse.ArgumentParser(description="Fetch the EU Travel Survey 2014 from Dataverse → importer JSONL.")
    ap.add_argument("--server", default=DEFAULT_SERVER, help="Dataverse server (default Harvard)")
    ap.add_argument("--doi", default=DEFAULT_DOI, help="dataset DOI (default 10.7910/DVN/P82V9X)")
    ap.add_argument("--version", default=DEFAULT_VERSION, help="dataset version (default 1.1)")
    ap.add_argument("--out-dir", default="mob_data", help="download + output directory")
    ap.add_argument("--api-token", default=os.environ.get("DATAVERSE_API_TOKEN"), help="X-Dataverse-key for restricted files")
    ap.add_argument("--data-file-id", type=int, default=None, help="force which file id is the respondent table")
    ap.add_argument("--id-col", default=None, help="force the respondent-id column (else auto/synthesized)")
    ap.add_argument("--country-col", default=None, help="force the country column (else auto-detected)")
    ap.add_argument("--coerce-numeric", action="store_true", help="convert numeric-looking cells to int/float (default: keep verbatim strings)")
    ap.add_argument("--also-original", action="store_true", help="also download each tabular file's ORIGINAL upload (e.g. .sav) as an artifact")
    ap.add_argument("--list-only", action="store_true", help="list the dataset files and exit (no download)")
    args = ap.parse_args()

    print("\n  Mobility acquisition — %s  doi:%s  v%s" % (args.server, args.doi, args.version))
    try:
        files = list_files(args.server, args.doi, args.version, args.api_token)
    except Exception as exc:
        print("  [!] could not list the dataset (%s: %s)." % (type(exc).__name__, exc), file=sys.stderr)
        print("      Confirm the server/DOI/version and (for restricted files) --api-token; the context "
              "must be able to reach %s." % args.server, file=sys.stderr)
        sys.exit(2)
    if not files:
        print("  [!] the dataset version lists no files — check the DOI/version.", file=sys.stderr); sys.exit(2)

    print("  files (%d):" % len(files))
    for f in files:
        print("    - id=%s  %-40s  %-28s %s%s"
              % (f["id"], f["filename"], f["content_type"], "TABULAR " if f["tabular"] else "",
                 "orig=%s" % f["original_format"] if f["original_format"] else ""))
    if args.list_only:
        return

    os.makedirs(args.out_dir, exist_ok=True)

    # choose the respondent table: forced id, else the (largest) tabular file
    tabulars = [f for f in files if f["tabular"]]
    if args.data_file_id:
        data_f = next((f for f in files if f["id"] == args.data_file_id), None)
    else:
        data_f = max(tabulars, key=lambda f: f.get("size") or 0) if tabulars else None
    if not data_f:
        print("  [!] no tabular respondent file found. Pass --data-file-id <id> from the list above "
              "(the released respondent table).", file=sys.stderr)
        sys.exit(3)

    artifacts = []
    # 1) the respondent table — Dataverse serves tabular files as ingested `.tab` (TSV) by default
    tab_name = data_f["filename"]
    if not tab_name.lower().endswith((".tab", ".tsv", ".csv")):
        tab_name += ".tab"
    tab_path = os.path.join(args.out_dir, tab_name)
    print("\n  downloading respondent table id=%s → %s" % (data_f["id"], tab_path))
    download(args.server, data_f["id"], tab_path, args.api_token, original=False)
    artifacts.append(tab_path)
    # PREFER the depositor's ORIGINAL upload for CONVERSION whenever it exists: Dataverse's ingested
    # `.tab` for this dataset baked U+FFFD into every non-UTF-8 cell (Region / Destination), so the
    # .tab is lossily corrupted at the source. The original upload keeps the real bytes; `_read_text`
    # decodes it faithfully (utf-8→cp1252→latin-1). The .tab stays as a provenance artifact.
    convert_path = tab_path
    if data_f.get("original_format"):
        orig_path = os.path.join(args.out_dir, "original_" + data_f["filename"])
        print("  downloading ORIGINAL upload id=%s → %s (encoding-faithful source for conversion)"
              % (data_f["id"], orig_path))
        download(args.server, data_f["id"], orig_path, args.api_token, original=True)
        artifacts.append(orig_path)
        convert_path = orig_path

    # 2) documentation files (codebook / questionnaire / value labels) — provenance artifacts
    for f in files:
        if f is data_f:
            continue
        if f["tabular"] or f["filename"].lower().endswith(_DOC_EXT):
            dest = os.path.join(args.out_dir, f["filename"])
            try:
                print("  downloading doc/aux id=%s → %s" % (f["id"], dest))
                download(args.server, f["id"], dest, args.api_token, original=bool(f["original_format"]) and not f["tabular"])
                artifacts.append(dest)
            except Exception as exc:
                print("    [skip] %s (%s)" % (f["filename"], exc), file=sys.stderr)

    # 3) dataset-level DDI codebook (variable + value-label semantics)
    ddi = download_ddi(args.server, args.doi, os.path.join(args.out_dir, "codebook_ddi.xml"), args.api_token)
    if ddi:
        artifacts.append(ddi)

    # 4) convert the respondent table → importer JSONL (verbatim)
    out_jsonl = os.path.join(args.out_dir, "respondents.jsonl")
    print("\n  converting %s → %s (verbatim)…" % (convert_path, out_jsonl))
    info = tab_to_jsonl(convert_path, out_jsonl, id_col=args.id_col, country_col=args.country_col,
                        coerce_numeric=args.coerce_numeric)
    artifacts.insert(0, out_jsonl)  # keep respondents.jsonl first for readability; hash the source table too

    print("\n  ── acquisition summary ──")
    print("    rows (Source Atoms to be):  %d   (delimiter=%s)" % (info["rows"], info["delimiter"]))
    print("    columns (%d):               %s%s" % (len(info["columns"]), ", ".join(info["columns"][:12]),
                                                    " …" if len(info["columns"]) > 12 else ""))
    print("    respondent id:              %s" % ("column '%s'" % info["id_col"] if info["id_col"]
                                                  else "SYNTHESIZED row coordinate (<file>:<rownum>)"))
    print("    country column:             %s" % (info["country_col"] or "(not detected — set --country-col if needed)"))
    print("    weight column:              %s" % (info["weight_col"] or "(none detected)"))

    tab_artifacts = [a for a in artifacts if a != out_jsonl]
    art_flags = " ".join("--artifact %s" % a for a in tab_artifacts)
    print("\n  ── next: import into a running Cell (verbatim, no filtering) ──")
    print("  python akasha.py --serve")
    print("  python app/scripts/mobility_source_import.py --as <admin_id> \\")
    print("      --records %s --id-field respondent_id \\" % out_jsonl)
    print("      %s \\" % art_flags)
    print("      --retrieval %s/dataset.xhtml?persistentId=doi:%s \\" % (args.server.rstrip('/'), args.doi))
    print("      --snapshot pilot --snapshot-n 500 --snapshot-strata %s" % (info["country_col"] and "country" or "country"))
    print("\n  then verify:  source.pool.ls pool=source:pool:mobility:eu_travel_survey_2014:v1_1  ·  source.audit lab=mobility")
    print("  Source Viewer: /labo/source/#src=pool/source:pool:mobility:eu_travel_survey_2014:v1_1\n")


if __name__ == "__main__":
    main()
