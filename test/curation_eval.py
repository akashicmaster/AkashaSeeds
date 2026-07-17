#!/usr/bin/env python3
"""
Curation eval — interpretation as a narrative path over relationships.

The curation model was redefined from a 6-layer reconciliation engine to a simple
narrative-path interpreter. Curation's object is the RELATIONSHIP among atoms (not a
single atom), its output is an ordered narrative path, and it bears NO burden of
proof (provenance:interpretation — cross-check with `fact` if verification is needed).

  C1 derived intersect — time-axis ∩ bloodline reveals the succession chain; an atom
                         adjacent on ONE axis only (time, not blood) is left off.
  C2 single axis       — one relation → follow its chain.
  C3 authored          — a human/LLM-supplied order is taken as the path verbatim.
  C4 narrate           — reads the path back with grounds + provenance:interpretation.
  C5 no burden of proof— the curation + its narrative are provenance:interpretation.
  C6 idempotent alias  — re-running with the same alias returns the same curation.
  C7 ls / removed      — curations list; the old ops (premise/fold/view/…) are gone.

Run:  python test/curation_eval.py
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:20} {detail}")


def main():
    print("\n  curation eval — interpretation as a narrative path over relationships\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cur_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else r.get("error")

    def mk(n, de):
        return (d("def", {"name": n, "description": de}) or {}).get("key")

    # A patriline: both a time axis (chrono:before) and a bloodline (lineage:begat).
    ou = mk("myth:ouranos", "primordial sky, head of the line")
    kr = mk("myth:kronos",  "titan, son of Ouranos")
    ze = mk("myth:zeus",    "olympian, son of Kronos")
    ga = mk("myth:gaia",    "primordial earth — time-early but off this patriline")
    for a in (ou, kr, ze, ga):
        d("set.add", {"name": "demo:pantheon", "id": a})
    d("ln", {"src": ou, "dst": kr, "rel": "chrono:before"})
    d("ln", {"src": kr, "dst": ze, "rel": "chrono:before"})
    d("ln", {"src": ga, "dst": ou, "rel": "chrono:before"})       # gaia earlier in time…
    d("ln", {"src": ou, "dst": kr, "rel": "lineage:begat"})
    d("ln", {"src": kr, "dst": ze, "rel": "lineage:begat"})       # …but not on the bloodline

    # C1 — derived intersection.
    c1 = d("curation.new", {"title": "Succession", "thesis": "father to son through time",
                            "set": "demo:pantheon", "rels": "chrono:before,lineage:begat",
                            "op": "intersect"})
    path1 = [s["name"] for s in c1.get("path", [])]
    record("C1 derived intersect",
           path1 == ["myth:ouranos", "myth:kronos", "myth:zeus"] and c1.get("mode") == "derived",
           f"path={path1} (gaia off-bloodline excluded)")

    # C2 — single axis follows that relation's chain.
    c2 = d("curation.new", {"title": "Just Time", "set": "demo:pantheon", "rels": "chrono:before"})
    path2 = [s["name"] for s in c2.get("path", [])]
    record("C2 single axis", path2 and path2[0] == "myth:gaia" and "myth:zeus" in path2,
           f"chrono chain head={path2[0] if path2 else None}, len={len(path2)}")

    # C3 — authored order taken verbatim.
    c3 = d("curation.new", {"title": "A Reading", "mode": "authored",
                            "ids": "myth:zeus, myth:gaia, myth:ouranos"})
    path3 = [s["name"] for s in c3.get("path", [])]
    record("C3 authored", path3 == ["myth:zeus", "myth:gaia", "myth:ouranos"]
           and c3.get("mode") == "authored", f"path={path3}")

    # C4 — narrate reads the path back with grounds + transitions.
    nr = d("curation.narrate", {"curation_id": c1.get("curation_id")})
    record("C4 narrate", isinstance(nr, dict) and len(nr.get("steps", [])) == 3
           and len(nr.get("transitions", [])) == 2 and nr.get("grounds", {}).get("op") == "intersect",
           f"steps={len(nr.get('steps', []))} transitions={len(nr.get('transitions', []))}")

    # C5 — no burden of proof: the output is provenance:interpretation.
    root_meta = k.manager.get_session("admin").local_cortex.get_meta(c1.get("curation_id")) or {}
    record("C5 no proof", root_meta.get("provenance") == "interpretation"
           and nr.get("provenance") == "interpretation",
           f"provenance={root_meta.get('provenance')}")

    # C6 — idempotent by alias.
    a1 = d("curation.new", {"title": "Aliased", "set": "demo:pantheon",
                            "rels": "chrono:before,lineage:begat", "alias": "curation:demo:x"})
    a2 = d("curation.new", {"title": "Aliased again", "set": "demo:pantheon",
                            "rels": "chrono:before,lineage:begat", "alias": "curation:demo:x"})
    record("C6 idempotent alias", a2.get("status") == "exists"
           and a1.get("curation_id") == a2.get("curation_id"),
           f"re-run status={a2.get('status')}")

    # C7 — ls works; the old reconciliation ops are gone.
    ls = d("curation.ls", {})
    removed = ["curation.premise.add", "curation.view.run", "curation.fold.add",
               "curation.conclusion.add", "curation.trace", "curation.diagnose"]
    gone = all(isinstance(d(m, {}), dict) and "code" in d(m, {}) for m in removed)
    record("C7 ls / removed", isinstance(ls, dict) and ls.get("count", 0) >= 4 and gone,
           f"ls count={ls.get('count')}, old ops gone={gone}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the narrative-path curation model is not behaving as specified.")
        return 1
    print("\nRESULT: PASS — curation is a narrative-path interpreter: derived (relation "
          "intersection) + authored orders, read via narrate, provenance:interpretation "
          "(no burden of proof); the old 6-layer reconciliation ops are removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
