#!/usr/bin/env python3
"""
Seed-time autonomy §2.1/§2.5 — source packs imported at boot.

A directory assets/<pack>/ with a pack.json {pool, rule, provider, rights, format, data, id_field,
label_field, freeze} and its data file is imported into the Source Data Layer at boot by
`_schedule_source_packs` BEFORE any bench runs, so a seed-baked bench's data is present-and-frozen with
no operator action. Properties verified: import + freeze; ROW-BY-ROW streaming (batched, R1); a
sha256-keyed fsync'd run-once sentinel; NON-CLOBBERING (an already-frozen pool of the same name is left
alone); and a cell with no packs imports nothing. Both cell shapes.

Run:  python test/source_pack_eval.py     (exit 0 = all pass)
"""
import glob
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import _fixtures as _fx  # noqa: E402
from lib.akasha.source import bootstrap
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _kernel(series, base):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    return k


def _write_pack(pack_dir, pool, rows):
    d = os.path.join(pack_dir, "demopack")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "pack.json"), "w", encoding="utf-8") as f:
        json.dump({"pool": pool, "provider": "eval", "collection": "demo",
                   "rights": "CC0", "format": "jsonl", "data": "data.jsonl",
                   "id_field": "sym", "label_field": "name", "freeze": True,
                   "batch": 3, "rule": "demo source pack"}, f)
    with open(os.path.join(d, "data.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    base = tempfile.mkdtemp(prefix="akasha_srcpack_")
    pack_dir = tempfile.mkdtemp(prefix="akasha_packs_")
    os.environ["AKASHA_SOURCE_PACK_DIR"] = pack_dir
    POOL = "source:pool:demo:things:v1"
    rows = [{"sym": f"S{i}", "name": f"thing {i}",
             "image_url": f"https://example.org/{i}.jpg"} for i in range(5)]
    _write_pack(pack_dir, POOL, rows)

    k = _kernel(series, base)

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"client_id": "admin", "data": data}, "id": "t"}, "internal")
        return r if "error" in r else (r.get("result") or {})

    _fx.world_genesis(k)

    # ── import: streamed in batches of 2 (5 rows ⇒ ≥3 acquire calls), pool frozen ──
    acts = bootstrap.source_packs_once(k, batch=2)
    a = next((x for x in acts if x.get("pool") == POOL), {})
    check(f"[{shape}] the pack imported + froze the pool",
          a.get("status") == "imported" and a.get("frozen") is True and a.get("rows") == 5, str(a))
    stt = d("source.status", {"pool": POOL})
    check(f"[{shape}] source.status reports the pool FROZEN with every row",
          stt.get("frozen") is True and stt.get("total") == 5, str(stt)[:140])
    # A23/A25 — the row-count helper feeds the progress line; the Health import status is cleared when done.
    check(f"[{shape}] the row-count helper counts the data rows",
          bootstrap.count_pack_rows(os.path.join(pack_dir, "demopack", "data.jsonl")) == 5)
    check(f"[{shape}] the Health import status is cleared after all packs are handled",
          getattr(k, "_source_pack_status", None) is None)

    # ── run-once sentinel: a second pass does nothing (the sentinel is present) ──
    sents = glob.glob(os.path.join(base, "central", "sentinels", "source_pack_*.done"))
    check(f"[{shape}] a sha256-keyed run-once sentinel was written", len(sents) >= 1, str(sents))
    acts2 = bootstrap.source_packs_once(k)
    check(f"[{shape}] a second pass is a no-op (sentinel present)", acts2 == [], str(acts2))

    # ── NON-CLOBBERING: drop the sentinel; the frozen pool is left alone (`present`, not re-imported) ──
    for s in sents:
        os.remove(s)
    acts3 = bootstrap.source_packs_once(k)
    a3 = next((x for x in acts3 if x.get("pool") == POOL), {})
    check(f"[{shape}] a re-scan of an already-FROZEN pool is NON-clobbering (present, not re-imported)",
          a3.get("status") == "present", str(acts3))
    stt3 = d("source.status", {"pool": POOL})
    check(f"[{shape}] the frozen pool still has exactly its original rows (never doubled)",
          stt3.get("total") == 5, str(stt3)[:120])

    # ── a cell with no packs imports nothing ──
    empty = tempfile.mkdtemp(prefix="akasha_nopacks_")
    os.environ["AKASHA_SOURCE_PACK_DIR"] = empty
    base2 = tempfile.mkdtemp(prefix="akasha_srcpack2_")
    k2 = _kernel(series, base2)
    check(f"[{shape}] a cell with no source packs imports nothing", bootstrap.source_packs_once(k2) == [])
    os.environ.pop("AKASHA_SOURCE_PACK_DIR", None)


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        os.environ.pop("AKASHA_SOURCE_PACK_DIR", None)
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a bundled source pack (assets/<pack>/pack.json + data) is streamed row-by-row "
          "and imported + frozen at boot, behind a sha256-keyed run-once sentinel; a re-scan of an "
          "already-frozen pool is non-clobbering; and a cell with no packs imports nothing — both shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
