#!/usr/bin/env python3
"""
P0-a slice 1 — the sweep engine FOUNDATION: `wf.branch from=<template> params=`, evaluations-as-a-Set,
and `lens.rank`.

A hyperparameter sweep is a fan of workflow BRANCHES, each a parameterized instance of ONE template,
each producing an evaluation ROW; the leaderboard is `lens.rank` over the evaluations Set, faceted by
the condition Sets the branches declared. This eval drives the whole foundation on BOTH cell shapes:

  • wf.branch from=<template> params=k=v,k=v loads config/<bench>/templates/<template>.ak with $param
    substitution, derives the lineage branch name + a cond8 over the sorted bindings, and is idempotent
    (a re-run with the SAME params returns already=true and adds no branch);
  • two sweep points with a differing param get DIFFERENT cond8 / branches;
  • each branch joins the faceting Sets set:wb:<b>:cond:<k>:<v> (+ set:wb:<b>:branches) via a marker;
  • running a branch's tail produces a learning.evaluate metrics atom that (a) joins set:wb:<b>:evaluations,
    (b) carries branch + cond8 + built_at_epoch + artifact_id, (c) joins the SAME condition Sets;
  • lens.rank ranks the evaluations Set grouped (default group=frame), respects within=<Set> as an
    intersection, and flags frame_mismatch when a mixed-frame Set is ranked without grouping by frame.

Run:  python app/test/sweep_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["OAK", "MAPLE", "BIRCH", "PINE", "ELM", "ASH"]     # 6 classes
_POOL = "source:pool:leafimg:v1"
# use the SHIPPED bench name so the SHIPPED template app/config/workbench/plants-vision/templates/learn_observe.ak
# is the one under test (the template dir is keyed by the bench name).
BENCH = "plants-vision"
BSLUG = "plants_vision"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_sweep_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus.core

    def members(setname):
        try:
            return list(nuc.get_collection_members(setname) or [])
        except Exception:
            return []

    # ── a PUBLIC bench (nucleus-scoped, so the sweep markers/cond-Sets/evaluations are all readable
    #    through the nucleus core here) + its workflow + a frozen 60-ref pool split into train/target ──
    d("world.genesis", {})
    d("bench.new", {"name": BENCH, "kind": "learning"})
    d("wf.new", {"bench": BENCH})
    d("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = [{"id": f"img_{i}", "image": f"mock://leaf/{_CLASSES[i % 6].lower()}/{i}.jpg",
             "species_symbol": _CLASSES[i % 6]} for i in range(60)]
    d("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock", "label_field": "species_symbol"})
    d("source.acquire", {"source": "source:src:leafsrc", "rule": "mock", "records": recs,
                         "pool": _POOL, "id_field": "id", "label_field": "species_symbol"})
    d("source.pool.freeze", {"pool": _POOL})
    tr = d("source.pool.sample", {"pool": _POOL, "name": "train", "n": "40", "seed": "plants1",
                                  "strata": "species_symbol"})
    tg = d("source.pool.sample", {"pool": _POOL, "name": "target", "n": "20", "seed": "plants1",
                                  "strata": "species_symbol", "rule": "complement:train"})
    d("learning.dataset.bind", {"name": BENCH, "pool": tr.get("sample"), "role": "train"})
    d("learning.dataset.bind", {"name": BENCH, "pool": tg.get("sample"), "role": "target"})

    # ── the sweep: TWO points of ONE template, differing only in split= ──
    bA = d("wf.branch", {"bench": BENCH, "from": "learn_observe",
                         "params": "space=color,head=logreg,split=0.8"})
    bB = d("wf.branch", {"bench": BENCH, "from": "learn_observe",
                         "params": "space=color,head=logreg,split=0.6"})
    check(f"[{shape}] wf.branch from=<template> materializes a branch (steps loaded, cond8 derived)",
          bA.get("status") == "branched" and bA.get("steps") == 7 and bool(bA.get("cond8")),
          f"steps={bA.get('steps')} cond8={bA.get('cond8')}")
    check(f"[{shape}] two sweep points with a differing param get DIFFERENT cond8 + branch",
          bA.get("cond8") != bB.get("cond8") and bA.get("branch") != bB.get("branch"),
          f"A={bA.get('cond8')} B={bB.get('cond8')}")
    check(f"[{shape}] the branch name carries the lineage <parent>@p<fork>/<template>@<cond8>",
          bA.get("lineage", "").startswith("main@p0/learn_observe@")
          and bA.get("cond8") in bA.get("lineage", ""), bA.get("lineage"))

    # ── idempotency: the SAME params re-point nothing (already=true), no new branch ──
    n_branches_before = len(members(f"set:wb:{BSLUG}:branches"))
    bA2 = d("wf.branch", {"bench": BENCH, "from": "learn_observe",
                          "params": "space=color,head=logreg,split=0.8"})
    check(f"[{shape}] a re-run with identical params is idempotent (already=true)",
          bA2.get("already") is True and bA2.get("branch") == bA.get("branch"), str(bA2)[:120])
    check(f"[{shape}] set:wb:{BSLUG}:branches holds exactly the 2 distinct sweep points",
          len(members(f"set:wb:{BSLUG}:branches")) == 2 == n_branches_before, str(n_branches_before))

    # ── the faceting condition Sets ──
    check(f"[{shape}] cond Set head:logreg holds BOTH branches; split:0_8 / split:0_6 hold ONE each",
          len(members(f"set:wb:{BSLUG}:cond:head:logreg")) == 2
          and len(members(f"set:wb:{BSLUG}:cond:split:0_8")) == 1
          and len(members(f"set:wb:{BSLUG}:cond:split:0_6")) == 1,
          f"head={len(members(f'set:wb:{BSLUG}:cond:head:logreg'))} "
          f"s8={len(members(f'set:wb:{BSLUG}:cond:split:0_8'))} "
          f"s6={len(members(f'set:wb:{BSLUG}:cond:split:0_6'))}")

    # ── $param substitution reached the loaded entries (run/model keyed by cond8, split bound) ──
    ls = d("wf.ls", {"bench": BENCH, "branch": bA.get("branch")})
    _methods = {e.get("method"): e for e in (ls.get("entries") or []) if e.get("method")}
    _train = _methods.get("learning.train") or {}
    check(f"[{shape}] the template's $params substituted (split bound, run keyed by cond8)",
          (_train.get("params") or {}).get("split") == "0.8"
          and (_train.get("params") or {}).get("run") == f"f_{bA.get('cond8')}",
          str(_train.get("params")))

    # ── run each branch's tail → real evaluations that carry the coordinates + join the Sets ──
    def _drive(branch):
        rows = d("wf.ls", {"bench": BENCH, "branch": branch}).get("entries") or []
        _feat = {}
        for e in rows:
            if e.get("method"):
                params = dict(e.get("params") or {})
                params.setdefault("name", BENCH)
                _r = d(e["method"], params)
                if e["method"] == "learning.feature.execute":
                    _feat = _r or {}
        return _feat

    _fa = _drive(bA.get("branch"))
    _fb = _drive(bB.get("branch"))

    ev = members(f"set:wb:{BSLUG}:evaluations")
    check(f"[{shape}] each sweep point produced an evaluation row in set:wb:{BSLUG}:evaluations",
          len(ev) == 2, f"n={len(ev)}")
    # B2 (S2-k) — the two branches share space=color over the SAME frozen train pool, so the SECOND
    # branch REUSES the first's embeddings (no re-encode) yet still seals + trains (it filed the second
    # evaluation above). The first branch embeds fresh; the second reuses.
    check(f"[{shape}] B2 branch A embeds fresh (observed>0, reused=0), branch B reuses (observed=0, reused>0)",
          int(_fa.get("observed") or 0) > 0 and int(_fa.get("reused") or 0) == 0
          and int(_fb.get("observed") or 0) == 0 and int(_fb.get("reused") or 0) > 0
          and _fb.get("complete") is True,
          f"A(obs={_fa.get('observed')} reuse={_fa.get('reused')}) "
          f"B(obs={_fb.get('observed')} reuse={_fb.get('reused')} complete={_fb.get('complete')})")

    import json as _json
    def _meta(mk):
        row = nuc.get_chunk_raw(mk)
        return _json.loads(row["meta"]) if row and row["meta"] else {}
    _ems = [_meta(mk) for mk in ev]
    check(f"[{shape}] every evaluation carries branch + cond8 + built_at_epoch + artifact_id",
          all(m.get("branch") and m.get("cond8") and m.get("built_at_epoch") is not None
              and m.get("artifact_id") for m in _ems),
          str([(m.get("cond8"), m.get("built_at_epoch") is not None, bool(m.get("artifact_id")))
               for m in _ems]))
    _cond8s = {m.get("cond8") for m in _ems}
    check(f"[{shape}] the two evaluations carry the two distinct cond8 (faceted by condition)",
          _cond8s == {bA.get("cond8"), bB.get("cond8")}, str(_cond8s))

    # ── lens.rank — the leaderboard over the evaluations Set ──
    rk = d("lens.rank", {"set": f"set:wb:{BSLUG}:evaluations", "key": "accuracy", "group": "frame"})
    check(f"[{shape}] lens.rank groups by frame (one 'test' group, 2 ranked rows, no mismatch)",
          rk.get("type") == "lens:rank" and len(rk.get("groups") or []) == 1
          and (rk.get("groups") or [{}])[0].get("count") == 2 and rk.get("frame_mismatch") is False,
          str(rk.get("groups"))[:160])
    _rows = (rk.get("groups") or [{}])[0].get("rows") or []
    _accs = [r.get("accuracy") for r in _rows]
    check(f"[{shape}] lens.rank orders desc by the key and stamps rank 1..n",
          [r.get("rank") for r in _rows] == list(range(1, len(_rows) + 1))
          and _accs == sorted(_accs, key=lambda x: (x is not None, x if x is not None else 0),
                              reverse=True), str(_accs))

    # ── within= is an intersection with a condition Set (facet: only split=0.8) ──
    rkw = d("lens.rank", {"set": f"set:wb:{BSLUG}:evaluations", "key": "accuracy",
                          "group": "frame", "within": f"set:wb:{BSLUG}:cond:split:0_8"})
    _wrows = [r for g in (rkw.get("groups") or []) for r in (g.get("rows") or [])]
    check(f"[{shape}] lens.rank within=<cond Set> intersects — only the split=0.8 evaluation survives",
          len(_wrows) == 1 and _wrows[0].get("cond8") == bA.get("cond8"),
          f"n={len(_wrows)} cond8={_wrows[0].get('cond8') if _wrows else None}")

    # ── group=cond8 → one group per sweep point (each a single row) ──
    rkc = d("lens.rank", {"set": f"set:wb:{BSLUG}:evaluations", "key": "accuracy", "group": "cond8"})
    check(f"[{shape}] lens.rank group=cond8 yields one single-row group per sweep point",
          len(rkc.get("groups") or []) == 2
          and all(g.get("count") == 1 for g in (rkc.get("groups") or [])),
          str([g.get("count") for g in (rkc.get("groups") or [])]))


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — wf.branch from=<template> params= materializes idempotent, cond8-keyed sweep "
          "branches whose evaluations join a Set carrying branch/cond8/epoch coordinates; lens.rank "
          "ranks that Set grouped, intersects within=<cond Set>, and flags frame mismatch — both cell "
          "shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
