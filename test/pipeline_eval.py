#!/usr/bin/env python3
"""
Pipeline eval — the I/O interface layer (Unix-pipe of the data plane).

Every data endpoint is a Source (produces a Stream) or a Sink (consumes one), and
`run_pipeline(source, sink)` connects any pair. This proves the interface is uniform and
composable, and that a non-file source (a future web upload) plugs in unchanged:

  PL1 file→file    — FileSource(csv) → FileSink(md): pure endpoint composition, no graph.
  PL2 upload→file  — InlineSource(in-memory csv) → FileSink(json): the web-upload path, no disk source.
  PL3 upload→model→file — io.import text= (InlineSource → TableSink), then io.export
                    (TableSource → FileSink); the exported rows equal the uploaded ones
                    (concept-model round-trip in both directions over one interface).
  PL4 file→model   — io.import path=csv → the `table` model (the reverse of export).

Run:  python test/pipeline_eval.py
"""
import os
import sys
import json
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def main():
    print("\n  pipeline eval — I/O interface (Source | Sink)\n")
    from lib.harmonia.fileio import FileIO
    from lib.harmonia.pipeline import (run_pipeline, FileSource, FileSink, InlineSource)
    work = tempfile.mkdtemp(prefix="akasha_pipe_")
    fio = FileIO(extra_roots=[work])

    # PL1 — pure endpoint composition: a CSV file piped to a Markdown file, no graph at all.
    src_csv = os.path.join(work, "in.csv")
    open(src_csv, "w").write("id,name\n1,Henri\n2,Alice\n")
    out_md = os.path.join(work, "out.md")
    run_pipeline(FileSource(fio, src_csv), FileSink(fio, out_md))
    md = open(out_md).read()
    record("PL1 file→file", "| id | name |" in md and "Henri" in md,
           f"csv→md rendered a table ({os.path.basename(out_md)})")

    # PL2 — a non-file Source: an in-memory upload payload piped straight to a JSON file.
    upload = "sku,qty\nA1,5\nB2,9\n"
    out_json = os.path.join(work, "up.json")
    run_pipeline(InlineSource(upload, "csv", name="upload.csv"), FileSink(fio, out_json))
    rows = json.load(open(out_json))
    record("PL2 upload→file", isinstance(rows, list) and len(rows) == 2 and rows[0]["sku"] == "A1",
           f"in-memory upload → json file rows={len(rows)}")

    # Kernel for the graph endpoints (PL3, PL4).
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_pipe_k_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    # The kernel's FileIO is a different instance — permit our work dir on it.
    k.fileio.add_root(work)

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    # PL3 — upload → concept model → file, both directions over the one interface.
    up_csv = "city,pop\nTokyo,37\nOsaka,19\n"
    imp = d("io.import", {"text": up_csv, "format": "csv", "table": "cities", "name": "cities.csv"})
    back = os.path.join(work, "cities_out.json")
    exp = d("io.export", {"path": back, "table": "cities"})
    got = {r["city"]: r["pop"] for r in json.load(open(back))} if os.path.exists(back) else {}
    pl3 = (imp.get("imported") == 2 and exp.get("rows") == 2
           and got.get("Tokyo") == "37" and got.get("Osaka") == "19")
    record("PL3 upload→model→file", pl3,
           f"imported={imp.get('imported')}, exported rows={exp.get('rows')}, values match={got.get('Tokyo')=='37'}")

    # PL4 — the reverse route: a CSV FILE → the concept model (table).
    f_csv = os.path.join(work, "users.csv")
    open(f_csv, "w").write("id,name\n1,Henri\n2,Alice\n3,Bob\n")
    imp2 = d("io.import", {"path": f_csv, "table": "users"})
    cortex = k.manager.get_session("admin").local_cortex
    pl4 = imp2.get("imported") == 3 and bool(cortex.resolve_alias("tbl:users"))
    record("PL4 file→model", pl4,
           f"file→table rows={imp2.get('imported')}, tbl:users resolves={bool(cortex.resolve_alias('tbl:users'))}")

    # PL5 — in-graph source → concept model through lens (io.project = LensScanSource →
    # ConceptCastSink). Base of the "project into any model" path; table is the working target.
    setname = "set:rec:cities"
    for city, pop in [("Tokyo", "37"), ("Osaka", "19"), ("Nagoya", "9")]:
        a = (d("w", {"content": f"record {city}"}) or {}).get("key")
        cc = (d("w", {"content": city}) or {}).get("key")
        cp = (d("w", {"content": pop}) or {}).get("key")
        d("ln", {"src": a, "dst": cc, "rel": "rec:city"})
        d("ln", {"src": a, "dst": cp, "rel": "rec:pop"})
        d("set.add", {"name": setname, "id": a})
    proj = d("io.project", {"src": setname, "model": "table", "into": "cities_tbl"})
    pl5 = (proj.get("kind") == "cast" and proj.get("into") == "cities_tbl"
           and bool(cortex.resolve_alias("tbl:cities_tbl")))
    record("PL5 set→model(lens)", pl5,
           f"lens cast into table={proj.get('into')}, "
           f"rows={((proj.get('cast') or {}).get('result') or {}).get('rows_inserted')}")

    # PL6 — client 'receive': io.export inline=true returns the serialised content in the
    # result (no file). The mirror of the InlineSource upload path.
    rcv = d("io.export", {"table": "cities_tbl", "format": "json", "inline": "true"})
    got = json.loads(rcv.get("content") or "[]") if rcv.get("content") else []
    pl6 = (rcv.get("kind") == "table" and "content" in rcv and rcv.get("rows") == 3
           and isinstance(got, list) and len(got) == 3)
    record("PL6 model→client", pl6,
           f"inline content bytes={rcv.get('bytes')}, rows={rcv.get('rows')}, parsed={len(got)}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the I/O pipeline interface regressed.")
        return 1
    print("\nRESULT: PASS — one Source|Sink interface connects files, in-memory uploads, and "
          "the concept model in any direction (Unix-pipe of the data plane).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
