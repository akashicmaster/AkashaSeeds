#!/usr/bin/env python3
"""
`lens.compare` is generic — the caller names the join relation and the field; the lens names none.

Until the purge order (3 October §2) the lens joined two Sets by the vision lab's `vis:observes` link,
derived a label from the lab's detection Sets and feature atoms, filed its aggregate in `set:vlab:compares`
and linked it to `vision_run:` atoms — application law inside a platform op. Now:

  §1  key=<relation>: each member joins by the target of its first `key` link; `field` is the member's
      own meta field; `changed` / `agree_*` / `truth_known` are counted per joined item.
  §2  key empty: each member joins by itself.
  §3  `field` falls back to the member's `source_metadata[field]`.
  §4  result=: ONE aggregate atom (concept `lens_compare`, epoch-stamped) under that alias, returned as
      `stored`; the lens files it in no other Set and links it to nothing.
  §5  item=: just that item's row.
  §6  the lens source names no application relation, Set, prefix or concept.

Run:  python test/lens_compare_generic_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import re
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


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.api.client import embedded
    gw = embedded(tempfile.mkdtemp(prefix="akasha_lcmp_"), series, load_ontology=False)
    k = gw.kernel_client
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    nuc = k.manager.shared_nucleus
    core = nuc.core

    def atom(alias, meta):
        return nuc.put_atom("[%s]" % alias, dict(meta), author="admin", alias=alias)

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    items = {n: atom("evcmp:item:%s" % n, {"kind": "thing", "answer": ans})
             for n, ans in (("i1", "oak"), ("i2", "elm"), ("i3", "ash"))}
    # Set A reads i1 oak, i2 elm; Set B reads i1 oak, i2 pine, i3 ash (i3 absent from A)
    for side, reads in (("a", {"i1": "oak", "i2": "elm"}), ("b", {"i1": "oak", "i2": "pine", "i3": "ash"})):
        for n, lab in reads.items():
            mk = atom("evcmp:reading:%s:%s" % (side, n), {"label": lab, "confidence": 0.5})
            nuc.put_link(mk, items[n], "evcmp:reads", author="admin")
            core.add_to_collection("set:evcmp:%s" % side, mk)

    r = d("lens.compare", {"a": "set:evcmp:a", "b": "set:evcmp:b", "key": "evcmp:reads",
                           "field": "label", "truth": "answer"})
    rows = {row["item"]: row for row in (r.get("rows") or [])}
    sm = r.get("summary") or {}
    check(f"[{shape}] §1 three items joined by the named relation",
          sorted(rows) == ["evcmp:item:i1", "evcmp:item:i2", "evcmp:item:i3"], str(sorted(rows)))
    check(f"[{shape}] §1 changed counts i2 (elm→pine) and i3 (absent→ash)",
          sm.get("changed") == 2 and rows.get("evcmp:item:i1", {}).get("changed") is False, str(sm))
    check(f"[{shape}] §1 truth read from the joined item's own field: agree_a=2, agree_b=2, known=3",
          sm.get("agree_a") == 2 and sm.get("agree_b") == 2 and sm.get("truth_known") == 3, str(sm))

    for side, n in (("a", "x1"), ("b", "x1")):
        core.add_to_collection("set:evcmp:self%s" % side,
                               atom("evcmp:self:%s:%s" % (side, n), {"label": side}))
    r2 = d("lens.compare", {"a": "set:evcmp:selfa", "b": "set:evcmp:selfb", "field": "label"})
    check(f"[{shape}] §2 key empty: each member joins by itself (two distinct atoms → two rows)",
          (r2.get("summary") or {}).get("items") == 2, str(r2.get("summary")))

    k1 = atom("evcmp:sm:a", {"source_metadata": {"label": "deep"}})
    core.add_to_collection("set:evcmp:sma", k1)
    r3 = d("lens.compare", {"a": "set:evcmp:sma", "b": "set:evcmp:sma", "field": "label"})
    row3 = (r3.get("rows") or [{}])[0]
    check(f"[{shape}] §3 field falls back to source_metadata",
          (row3.get("a") or {}).get("label") == "deep", str(row3)[:120])

    r4 = d("lens.compare", {"a": "set:evcmp:a", "b": "set:evcmp:b", "key": "evcmp:reads",
                            "field": "label", "result": "evcmp:cmp:ab"})
    st = r4.get("stored")
    _row = core.get_chunk_raw(st) if st else None
    sm4 = json.loads(_row["meta"]) if _row and _row.get("meta") else {}
    check(f"[{shape}] §4 one aggregate atom under result=, concept lens_compare, epoch-stamped",
          bool(st) and sm4.get("concept") == "lens_compare" and "built_at_epoch" in sm4
          and "artifact_id" in sm4, str(sm4)[:160])
    cols = sorted(core.get_collections_for_key(st) or []) if st else []
    links = list(core.get_adjacent_links(st) or []) if st else []
    check(f"[{shape}] §4 the lens files it in no Set and links it to nothing",
          not [c for c in cols if not c.startswith(("leaf:", "ns:", "lang:", "ws:"))] and not links,
          "cols=%s links=%s" % (cols, links[:3]))

    r5 = d("lens.compare", {"a": "set:evcmp:a", "b": "set:evcmp:b", "key": "evcmp:reads",
                            "field": "label", "item": "evcmp:item:i2"})
    check(f"[{shape}] §5 item= returns just that row",
          [x["item"] for x in (r5.get("rows") or [])] == ["evcmp:item:i2"], str(r5.get("rows"))[:120])


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    src = open(os.path.join(ROOT, "lib", "akasha", "concepts", "lens.py"), encoding="utf-8").read()
    named = sorted(set(re.findall(r"vis:\w+|set:vlab:\w*|vision_\w+|obs:(?:vision|feature|detection):|"
                                  r"dominant_class|learning\.runs", src)))
    print()
    check("§6 the lens names no application relation, Set, prefix or concept", not named, str(named))
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("RESULT: PASS — lens.compare joins by the relation the caller names and compares the field the "
          "caller names; it stores one aggregate and files it nowhere else; it names no application law.")
    sys.exit(0)


if __name__ == "__main__":
    main()
