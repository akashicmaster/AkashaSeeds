#!/usr/bin/env python3
"""
source_import_set_eval.py — an ontology SET becomes a browsable, analysable Source Pool.

The Source Viewer is being promoted to the central data hub every lab connects to. `source.import.set`
turns any existing in-graph set (a `set.add`-defined ontology collection) into a frozen Source Pool:
one Source Atom per member (member alias → id, scalar meta → source_metadata fields, content → text),
reusing the acquisition minting/filing, then freeze. So the existing ontology becomes viewable +
analysable through the same Source Viewer with no bespoke importer.

Pins:
  1. import mints one source_item per member; the pool freezes; source.status tallies them;
  2. the members' meta scalars AND content are projected into source_metadata — source.pool.scan
     surfaces them as fields (so analysis.count/scatter/cluster can run over them);
  3. idempotent — re-import unifies (content-addressed by alias), no duplicate items.

Run:  python test/source_import_set_eval.py     (exit 0 = pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_setimp_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # Real ontology atoms live UNIVERSAL (shared nucleus) — mint a few + a set membership, as a boot
    # ontology pack would (a user-scope `w` atom is deliberately invisible to the universal source layer).
    nuc = k.manager.shared_nucleus
    fixtures = [("concept:apple", "A red pome fruit", {"concept": "fruit", "color": "red", "family": "rosaceae"}),
                ("concept:pear", "A green pome fruit", {"concept": "fruit", "color": "green", "family": "rosaceae"}),
                ("concept:fig", "A purple fruit", {"concept": "fruit", "color": "purple", "family": "moraceae"})]
    for aid, desc, meta in fixtures:
        key = nuc.put_atom(desc, meta, author="system")
        nuc.core.put_alias(key, aid)
        nuc.add_to_set("demo:fruits", key)

    r = d("source.import.set", {"set": "demo:fruits", "name": "demo_fruits", "freeze": "yes"})
    POOL = r.get("pool")
    check("import mints one source item per member + freezes the pool",
          r.get("imported") == 3 and r.get("frozen") is True and bool(POOL), str(r))

    st = d("source.status", {"pool": POOL})
    check("source.status tallies the imported pool (3, frozen)",
          st.get("total") == 3 and st.get("frozen") is True, str(st.get("by_status")))

    fields = set(d("source.pool.scan", {"pool": POOL}).get("fields") or [])
    check("member meta scalars + content are projected as source_metadata fields",
          {"color", "family", "content"} <= fields, str(sorted(fields)))

    rows = d("source.pool.scan", {"pool": POOL, "fields": "color,family,content"}).get("rows") or []
    colors = {row.get("color") for row in rows}
    check("scan surfaces the actual values (a categorical field analysis can cross)",
          colors == {"red", "green", "purple"} and all(row.get("content") for row in rows),
          str(colors))

    # the imported (metadata-only) pool advertises the TEXT modality only — no image/audio media —
    # which is what the Source Viewer uses to decide the pool's tab switcher.
    mods = d("source.modalities", {"pool": POOL}).get("modalities") or {}
    check("source.modalities marks the imported pool text-only (no image/audio)",
          mods.get("text") is True and mods.get("image") is False and mods.get("audio") is False, str(mods))

    # idempotent: re-import unifies (no duplicate source items)
    r2 = d("source.import.set", {"set": "demo:fruits", "name": "demo_fruits", "freeze": "no"})
    st2 = d("source.status", {"pool": POOL})
    check("re-import is idempotent (still 3 items, no duplicates)", st2.get("total") == 3, str(st2.get("total")))

    print("\nRESULT:", "PASS" if not _fails else "FAIL — " + ", ".join(_fails))
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
