#!/usr/bin/env python3
"""
F53 Phase 0 Stage 3 — the horizon consumer behind the empty-horizon guard (E2 / E3 / E4 + safety).

The ONLY stage that edits a function the enrichment path executes. Discipline: `_apply_horizon` first
short-circuits when the session has no horizon, returning the associations UNCHANGED (the archives /
no-horizon path is bit-identical). Below the guard: SOFT entries re-rank (a nudge, never a filter,
count unchanged); LENS entries clip to the UNION of lens sets and annotate; an ungranted entry is inert
(self-directed can never widen granted). Also: cross.query defaults to the horizon when `concepts` is
omitted, and adds mode=coverage|strict.

Run:  python test/f53_horizon_apply_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

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
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_hz_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def call(method, data=None):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data or {}}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus
    core = nuc.core
    ts = time.time()

    def atom(alias, content):
        key = nuc.put_atom(content, {"salience": 1.0}, author="admin")
        core.put_alias(key, alias)
        return key

    SET_A, SET_B = "set:demo:A", "set:demo:B"
    focal = atom("concept:focal_hz", "focal hz node")
    neigh = {}
    for i in range(6):
        n = atom("concept:nb%d" % i, "neighbour %d" % i)
        core.put_link_raw(focal, n, "calc:associated_with", 1.0, "forward", "atom", "admin", "verified", ts)
        neigh["concept:nb%d" % i] = n
    for i in (0, 1, 2):
        core.add_to_collection(SET_A, neigh["concept:nb%d" % i])
    for i in (3, 4):
        core.add_to_collection(SET_B, neigh["concept:nb%d" % i])

    def dive_assoc_slugs():
        r = call("dive.look", {"id": "concept:focal_hz"})
        out = []
        for a in r.get("associations", []):
            al = core.get_aliases_by_key(a.get("key"))
            out.append((al[0] if al else a.get("key")))
        return out, r

    # ── baseline (no horizon) ──
    base_slugs, base_r = dive_assoc_slugs()
    members = {"concept:nb0", "concept:nb1", "concept:nb2"}
    base_has_members = members & set(base_slugs)
    check("baseline dive surfaces the neighbour associations (no horizon set yet)",
          len(base_has_members) >= 2 and "lens" not in base_r,
          "assoc=%s lens_in_result=%s" % (base_slugs, "lens" in base_r))

    # ── E2 soft: members of set:demo:A rank HIGHER; COUNT unchanged; clearing reverts ──
    call("horizon.add", {"set": SET_A, "mode": "soft"})
    soft_slugs, soft_r = dive_assoc_slugs()
    top3 = set(soft_slugs[:3])
    check("E2 soft — set:demo:A members are nudged to the top; result COUNT unchanged; no clip",
          len(top3 & members) >= min(3, len(base_has_members)) and len(soft_slugs) == len(base_slugs)
          and "lens" not in soft_r,
          "top3=%s count(%d==%d)" % (top3, len(soft_slugs), len(base_slugs)))
    call("horizon.clear", {})
    rev_slugs, _ = dive_assoc_slugs()
    check("E2 soft — clearing the horizon reverts the ordering to baseline",
          rev_slugs == base_slugs, "rev==base=%s" % (rev_slugs == base_slugs))

    # ── E3 lens: clip to the UNION of lens sets; annotate; non-members drop ──
    call("horizon.add", {"set": SET_A, "mode": "lens"})
    lens_slugs, lens_r = dive_assoc_slugs()
    check("E3 lens — associations are CLIPPED to set:demo:A members and the result is annotated lens:[A]",
          set(lens_slugs) <= members and len(lens_slugs) >= 1 and lens_r.get("lens") == [SET_A],
          "assoc=%s lens=%s" % (lens_slugs, lens_r.get("lens")))
    check("E3 lens — each surviving association carries its own lens annotation",
          all("lens" in a for a in lens_r.get("associations", [])), "")

    # empty clip = empty list + annotation, not an error
    call("horizon.clear", {})
    call("horizon.add", {"set": "set:demo:EMPTY", "mode": "lens"})   # a real set name, no assoc members
    empty_slugs, empty_r = dive_assoc_slugs()
    check("E3 lens — a clip that matches nothing is an EMPTY list + annotation, never an error",
          empty_slugs == [] and empty_r.get("lens") == ["set:demo:EMPTY"], str(empty_r.get("lens")))

    # ── E4 grant invariant: an ungranted (unresolvable) lens entry is inert — result == baseline ──
    call("horizon.clear", {})
    call("horizon.add", {"set": "no_such_root_zzz", "mode": "lens"})
    ung_slugs, ung_r = dive_assoc_slugs()
    check("E4 grant — an ungranted horizon entry clips NOTHING, reveals NOTHING (== no-horizon baseline)",
          ung_slugs == base_slugs and "lens" not in ung_r, "ung==base=%s" % (ung_slugs == base_slugs))
    call("horizon.clear", {})

    # ── cross.query — defaults to the horizon when concepts omitted; mode=coverage|strict ──
    cq_empty = call("sys.cross.query", {})
    check("cross.query with no concepts AND empty horizon errors as before (message mentions horizon)",
          "error" in cq_empty and "horizon" in str(cq_empty.get("error", {})).lower(), str(cq_empty)[:120])
    call("horizon.add", {"set": SET_A})
    call("horizon.add", {"set": SET_B})
    cq_hz = call("sys.cross.query", {})
    check("cross.query defaults to the horizon (source=horizon) when concepts omitted",
          cq_hz.get("source") == "horizon" and cq_hz.get("mode") == "coverage", str(cq_hz)[:140])
    cq_strict = call("sys.cross.query", {"concepts": "%s %s" % (SET_A, SET_B), "mode": "strict"})
    check("cross.query mode=strict keeps only atoms present in EVERY concept (true intersection)",
          cq_strict.get("mode") == "strict"
          and all(len(r.get("present_in", [])) == 2 for r in cq_strict.get("intersection", [])),
          "count=%s" % cq_strict.get("count"))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the horizon consumer is guarded (no horizon ⇒ associations unchanged); soft "
          "re-ranks without filtering (count stable, revertible); lens clips to the union + annotates "
          "(empty clip is an empty list, not an error); an ungranted entry is inert (never widens "
          "granted); and cross.query defaults to the horizon with mode=coverage|strict.")
    sys.exit(0)


if __name__ == "__main__":
    main()
