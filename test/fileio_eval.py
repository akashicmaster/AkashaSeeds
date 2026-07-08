#!/usr/bin/env python3
"""
File I/O eval — the general Harmonia import/export route (CSV / JSON / MD / TXT).

Before this, real disk I/O was scattered and domain-specific (ontology-only loader; CSV as
in-memory strings; dead Harmonia transport scaffolds). `lib/harmonia/fileio.py` is now the
single disk-I/O layer, and the kernel `io.*` methods project through it into the graph:
tabular files → the `table` model (reusing the table operators — one route), documents →
indexed atoms tagged provenance=file. Reads/writes are confined to an allow-list of roots.

  F1 parse     — FileIO reads CSV/JSON-array → table, JSON-object/MD/TXT → doc (with title).
  F2 import    — io.import: CSV/JSON → table rows (via the table model); MD → provenance=file
                 atom (single route, no bespoke table code).
  F3 export    — io.export a table to CSV/JSON/MD files; the CSV round-trips back to rows.
  F4 index     — io.index a permitted directory → docs + tables; the index set is populated.
  F5 safety    — a path outside the permitted roots is rejected (no host-filesystem escape).

Run:  python test/fileio_eval.py
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
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:10} {detail}")


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    print("\n  file I/O eval — general import/export route (CSV/JSON/MD/TXT)\n")
    from lib.harmonia.fileio import FileIO
    work = tempfile.mkdtemp(prefix="akasha_fio_")

    # F1 — pure FileIO parse (no graph).
    fio = FileIO(extra_roots=[work])
    _write(os.path.join(work, "u.csv"), "id,name\n1,Henri\n2,Alice\n")
    _write(os.path.join(work, "arr.json"), '[{"a":1,"b":"x"},{"a":2,"b":"y"}]')
    _write(os.path.join(work, "obj.json"), '{"name":"akasha","v":2}')
    _write(os.path.join(work, "n.md"), "# Migration\n\nswallows migrate north in spring")
    _write(os.path.join(work, "p.txt"), "plain notes about the ocean and tides")
    k1, p1 = fio.read(os.path.join(work, "u.csv"))
    k2, p2 = fio.read(os.path.join(work, "arr.json"))
    k3, p3 = fio.read(os.path.join(work, "obj.json"))
    k4, p4 = fio.read(os.path.join(work, "n.md"))
    k5, _ = fio.read(os.path.join(work, "p.txt"))
    f1 = (k1 == "table" and p1["columns"] == ["id", "name"] and len(p1["rows"]) == 2
          and k2 == "table" and len(p2["rows"]) == 2
          and k3 == "doc" and k4 == "doc" and p4["title"] == "Migration" and k5 == "doc")
    record("F1 parse", f1,
           f"csv→{k1}, json-arr→{k2}, json-obj→{k3}, md→{k4}(title={p4.get('title')!r}), txt→{k5}")

    # Kernel for F2–F5.
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_fio_k_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    cortex = k.manager.get_session("admin").local_cortex
    d("io.allow", {"dir": work})

    # F2 — import through the graph (table model + provenance doc).
    imp_csv = d("io.import", {"path": os.path.join(work, "u.csv"), "table": "users"})
    imp_md = d("io.import", {"path": os.path.join(work, "n.md")})
    imp_json = d("io.import", {"path": os.path.join(work, "arr.json"), "table": "arr"})
    tbl_key = cortex.resolve_alias("tbl:users")        # went through the table model
    md_meta = cortex.get_meta(imp_md.get("atom_key")) if imp_md.get("atom_key") else {}
    f2 = (imp_csv.get("imported") == 2 and imp_json.get("imported") == 2
          and bool(tbl_key) and isinstance(md_meta, dict)
          and md_meta.get("provenance") == "file")
    record("F2 import", f2,
           f"csv→table rows={imp_csv.get('imported')}, tbl:users resolves={bool(tbl_key)}, "
           f"md provenance={md_meta.get('provenance')}")

    # F3 — export the table to files and round-trip the CSV.
    out_csv = os.path.join(work, "users_out.csv")
    out_json = os.path.join(work, "users_out.json")
    out_md = os.path.join(work, "users_out.md")
    e_csv = d("io.export", {"path": out_csv, "table": "users"})
    e_json = d("io.export", {"path": out_json, "table": "users"})
    e_md = d("io.export", {"path": out_md, "table": "users"})
    rt_kind, rt = fio.read(out_csv)                    # read the exported CSV back
    f3 = (os.path.exists(out_csv) and os.path.exists(out_json) and os.path.exists(out_md)
          and rt_kind == "table" and len(rt["rows"]) == 2
          and isinstance(json.load(open(out_json)), list))
    record("F3 export", f3,
           f"csv/json/md written={all(os.path.exists(p) for p in (out_csv,out_json,out_md))}, "
           f"csv round-trip rows={len(rt['rows'])}")

    # F4 — index a directory (local-directory indexing).
    idx = d("io.index", {"dir": work, "exts": ".md .txt"})
    members = cortex.list_set(idx.get("set", "")) if idx.get("set") else []
    f4 = idx.get("indexed_docs", 0) >= 2 and len(members) >= 2
    record("F4 index", f4,
           f"indexed_docs={idx.get('indexed_docs')}, tables={idx.get('tables')}, "
           f"set members={len(members)}")

    # F5 — path safety: escape attempts are rejected, in and out.
    bad_in = d("io.import", {"path": "/etc/passwd"})
    bad_out = d("io.export", {"path": "/tmp/akasha_escape.csv", "table": "users"})
    f5 = (isinstance(bad_in, dict) and bad_in.get("code") == -32001
          and isinstance(bad_out, dict) and bad_out.get("code") == -32001)
    record("F5 safety", f5,
           f"read-escape rejected={bad_in.get('code')==-32001}, "
           f"write-escape rejected={bad_out.get('code')==-32001}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the general file I/O route regressed.")
        return 1
    print("\nRESULT: PASS — one disk-I/O route imports CSV/JSON/MD/TXT (tabular→table model, "
          "docs→provenance-tagged atoms), exports to files, indexes directories, and stays "
          "confined to permitted roots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
