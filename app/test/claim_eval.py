#!/usr/bin/env python3
"""
B1 §A6 — CLAIMS: a stated assertion about a bench, with a DERIVED status.

A claim is a first-class atom (`claim:<sha8>`) written UNIVERSAL so a public bench's claims are
guest-readable. Its STATUS is never stored — it is DERIVED at read time from whether its `evidenced_by`
evidence resolves and holds:

    unattached    no evidence
    attached      ≥ 1 evidence resolves and does NOT negate
    contradicted  every evidence's OWN status negates it (a superseded evaluation, a retired condition,
                  an unsealed observation, or an execution coordinate whose block ended failed)

There is no `false`. A guest reads only the counts (never the claim texts); a member reads the rows.
The status surfaces through `lens.rank group=status` (the claims Set), which asks the claim concept for
each row's derived status and strips the text for a guest.

This eval drives it on BOTH cell shapes:
  • claim.make with no evidence ⇒ unattached;
  • attach a DONE evaluation ⇒ attached;
  • a claim whose only evidence is a FAILED execution coordinate ⇒ contradicted;
  • claim.status: a guest gets counts only (no rows/text), a member gets the rows with text;
  • lens.rank group=status faces the claims Set (guest: no text; member: text).

Run:  python app/test/claim_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["OAK", "MAPLE", "BIRCH", "PINE", "ELM", "ASH"]
_POOL = "source:pool:leafimg:v1"
BENCH = "plants-vision"
BSLUG = "plants_vision"
SWEEP = "grid1"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_claim_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    gr = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                     "params": {"data": {}}, "id": "gg"}, "network")
    gtok = (gr.get("result") or {}).get("binding_key")

    def g(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": gtok, "data": data}, "id": "gq"}, "network")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus.core

    def members(setname):
        try:
            return list(nuc.get_collection_members(setname) or [])
        except Exception:
            return []

    # ── a PUBLIC learning bench + a materialised sweep branch, run to a DONE evaluation ──
    a("world.genesis", {})
    a("bench.new", {"name": BENCH, "kind": "learning"})
    a("wf.new", {"bench": BENCH})
    a("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = [{"id": f"img_{i}", "image": f"mock://leaf/{_CLASSES[i % 6].lower()}/{i}.jpg",
             "species_symbol": _CLASSES[i % 6]} for i in range(60)]
    a("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock", "label_field": "species_symbol"})
    a("source.acquire", {"source": "source:src:leafsrc", "rule": "mock", "records": recs,
                         "pool": _POOL, "id_field": "id", "label_field": "species_symbol"})
    a("source.pool.freeze", {"pool": _POOL})
    tr = a("source.pool.sample", {"pool": _POOL, "name": "train", "n": "40", "seed": "plants1",
                                  "strata": "species_symbol"})
    tg = a("source.pool.sample", {"pool": _POOL, "name": "target", "n": "20", "seed": "plants1",
                                  "strata": "species_symbol", "rule": "complement:train"})
    a("learning.dataset.bind", {"name": BENCH, "pool": tr.get("sample"), "role": "train"})
    a("learning.dataset.bind", {"name": BENCH, "pool": tg.get("sample"), "role": "target"})
    a("sweep.def", {"bench": BENCH, "name": SWEEP,
                    "grid": '{"head":["logreg"],"split":["0.8"],"seed":["1"]}',
                    "template": "learn_observe", "fixed": "space=color"})
    branch = (a("sweep.materialise", {"bench": BENCH, "name": SWEEP, "n": "1"}).get("made") or [{}])[0].get("branch")
    rows = a("wf.ls", {"bench": BENCH, "branch": branch}).get("entries") or []
    for e in rows:
        if e.get("method"):
            params = dict(e.get("params") or {}); params.setdefault("name", BENCH)
            a(e["method"], params)
    ev = members("set:wb:%s:evaluations" % BSLUG)
    done_ev = (nuc.get_aliases_by_key(ev[0]) or [ev[0]])[0] if ev else ""

    # ── claim.make with NO evidence ⇒ unattached ──
    cm = a("claim.make", {"bench": BENCH, "text": "logreg is the right head for leaves"})
    check(f"[{shape}] claim.make with no evidence derives unattached",
          cm.get("status") == "made" and cm.get("derived_status") == "unattached", str(cm)[:120])
    claim_a = cm.get("claim")

    # ── attach a DONE evaluation ⇒ attached ──
    at = a("claim.attach", {"bench": BENCH, "claim": claim_a, "evidence": done_ev})
    check(f"[{shape}] attaching a DONE evaluation makes the claim attached",
          at.get("status") == "attached" and at.get("derived_status") == "attached", str(at)[:140])

    # ── a claim whose ONLY evidence is a FAILED execution coordinate ⇒ contradicted ──
    if k.jcl_worker:
        fb = (a("sweep.materialise", {"bench": BENCH, "name": SWEEP, "n": "1"}).get("made") or [{}])
        # SWEEP has one condition (already materialised above), so make a hand branch that fails
        hb = a("wf.branch", {"bench": BENCH, **{"from": "learn_observe", "params": "seed=7,space=color",
                                                "parent": "main"}}).get("branch")
        a("wf.write", {"bench": BENCH, "branch": hb, "pos": "8",
                       "entry": {"method": "learning.evaluate",
                                 "params": {"name": BENCH, "model": "model:learned:never_trained",
                                            "sample": "test"}}})
        a("wf.advance", {"bench": BENCH, "branch": hb, "n": "1000", "as": "job"})
        # the failed coordinate is the step_failed deviation's `observed_in` coordinate
        devset = members("set:wb:%s:deviation:kind:step_failed" % BSLUG)
        coord = ""
        for d in devset:
            dm = json.loads((nuc.get_chunk_raw(d) or {}).get("meta") or "{}")
            if dm.get("branch_slug") == hb:
                coord = dm.get("coordinate"); break
        cc = a("claim.make", {"bench": BENCH, "text": "this run proved mlp wins", "evidence": coord})
        check(f"[{shape}] a claim whose only evidence is a FAILED coordinate is contradicted",
              cc.get("derived_status") == "contradicted", f"coord={coord} → {cc.get('derived_status')}")

    # ── claim.status: a guest gets counts only (no rows/text); a member gets rows with text ──
    gs = g("claim.status", {"bench": BENCH})
    check(f"[{shape}] a guest reads claim.status counts only (no claims rows, no text)",
          not gs.get("error") and isinstance(gs.get("counts"), dict) and "claims" not in gs,
          str(gs)[:140])
    ms = a("claim.status", {"bench": BENCH})
    check(f"[{shape}] a member reads claim.status rows WITH text",
          isinstance(ms.get("claims"), list) and ms["claims"]
          and all("text" in r for r in ms["claims"]), str(ms.get("counts")))
    check(f"[{shape}] the counts reflect attached≥1 (and contradicted≥1 under JCL)",
          ms["counts"].get("attached", 0) >= 1
          and (ms["counts"].get("contradicted", 0) >= 1 if k.jcl_worker else True),
          str(ms.get("counts")))

    # ── lens.rank group=status faces the claims Set: a guest gets grouped counts with NO text; a
    #    member gets the text on each row ──
    lg = g("lens.rank", {"set": "set:wb:%s:claims" % BSLUG, "group": "status"})
    guest_rows = [r for grp in (lg.get("groups") or []) for r in (grp.get("rows") or [])]
    check(f"[{shape}] guest lens.rank group=status returns grouped rows with the derived status, NO text",
          bool(guest_rows) and all(r.get("status") in ("attached", "unattached", "contradicted")
                                   for r in guest_rows) and all("text" not in r for r in guest_rows),
          str([grp.get("group") for grp in (lg.get("groups") or [])]))
    lm = a("lens.rank", {"set": "set:wb:%s:claims" % BSLUG, "group": "status"})
    member_rows = [r for grp in (lm.get("groups") or []) for r in (grp.get("rows") or [])]
    check(f"[{shape}] member lens.rank group=status keeps the text on each row",
          bool(member_rows) and all("text" in r for r in member_rows), f"rows={len(member_rows)}")


def main():
    print("=" * 78)
    print("B1 §A6 — claims: a bench assertion with a DERIVED status (guest counts only)")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — a claim's status is DERIVED from its evidence (unattached / attached / "
          "contradicted), a guest reads only counts while a member reads the rows, and lens.rank "
          "group=status faces the claims Set with the text hidden from a guest — both cell shapes.")


if __name__ == "__main__":
    main()
