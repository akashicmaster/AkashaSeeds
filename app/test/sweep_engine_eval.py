#!/usr/bin/env python3
"""
P0-a slice 2 — the SWEEP ENGINE: sweep.def / materialise / status / leaderboard + branch admission.

A sweep is a fan of workflow branches over a hyperparameter grid (slice 1's `wf.branch from=<template>`),
each producing an evaluation ROW; the leaderboard ranks them. This eval drives the whole slice on BOTH
cell shapes, exercising the SHIPPED template app/config/workbench/plants-vision/templates/learn_observe.ak:

  • sweep.def of a 2×2×2 grid ⇒ 8 conditions, 0 branches (idempotent; a grid EXTENSION adds only new);
  • sweep.materialise n=3 ⇒ 3 branches, 3 pending, 5 unmaterialised (each a wf.branch from the template);
  • running one branch's tail ⇒ that condition reads `done` (derived from its evaluation) and the
    evaluation carries cond8 + branch and joins set:wb:<b>:sweep:<name>:evaluations;
  • sweep.leaderboard ranks the sweep's evaluations and stores an epoch-keyed artifact
    (wb:<b>:leaderboard:<name>, built_at_epoch + artifact_id, rebuilt only on change);
  • sweep.status is guest-readable;
  • a materialised branch lineage is ADMITTED (society.run would run it); a random name is not.

Run:  python app/test/sweep_engine_eval.py     (exit 0 = all pass)
"""
import hashlib
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
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_sweng_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    def as_(tok, method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
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

    # ── a PUBLIC bench (nucleus-scoped, readable here) + workflow + frozen pool + role samples ──
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

    # ── sweep.def — a 2×2×2 grid ⇒ 8 conditions, 0 branches (space fixed to `color` for a mock run) ──
    sd = a("sweep.def", {"bench": BENCH, "name": SWEEP,
                         "grid": '{"head":["logreg","mlp"],"split":["0.8","0.7"],"seed":["1","2"]}',
                         "max": "18", "template": "learn_observe", "fixed": "space=color"})
    check(f"[{shape}] sweep.def expands the grid to 8 conditions, 0 branches",
          sd.get("conds") == 8 and len(members(f"set:wb:{BSLUG}:sweep:{SWEEP}:branches")) == 0,
          f"conds={sd.get('conds')}")
    st0 = a("sweep.status", {"bench": BENCH, "name": SWEEP})
    check(f"[{shape}] sweep.status: 8 conds, all unmaterialised",
          st0.get("conds") == 8 and st0.get("unmaterialised") == 8 and st0.get("branches") == 0,
          str({kk: st0.get(kk) for kk in ("conds", "unmaterialised", "branches")}))

    # ── sweep.def is idempotent (a re-def adds nothing) ──
    sd2 = a("sweep.def", {"bench": BENCH, "name": SWEEP,
                          "grid": '{"head":["logreg","mlp"],"split":["0.8","0.7"],"seed":["1","2"]}',
                          "max": "18", "template": "learn_observe", "fixed": "space=color"})
    check(f"[{shape}] a re-def with the same grid adds nothing (idempotent)",
          sd2.get("conds") == 8 and sd2.get("added") == 0, f"added={sd2.get('added')}")

    # ── sweep.materialise n=3 ⇒ 3 branches, 3 pending, 5 unmaterialised ──
    ms = a("sweep.materialise", {"bench": BENCH, "name": SWEEP, "n": "3"})
    check(f"[{shape}] sweep.materialise n=3 creates 3 branches",
          ms.get("branches") == 3 and len(ms.get("made") or []) == 3, str(ms.get("branches")))
    st1 = a("sweep.status", {"bench": BENCH, "name": SWEEP})
    check(f"[{shape}] status after materialise: 3 pending, 5 unmaterialised, 0 done",
          st1.get("pending") == 3 and st1.get("unmaterialised") == 5 and st1.get("done") == 0,
          str({kk: st1.get(kk) for kk in ("pending", "unmaterialised", "done")}))

    # ── run ONE materialised branch's tail → its condition reads `done`; the evaluation carries cond8 ──
    branch = (ms.get("made") or [{}])[0].get("branch")
    rows = a("wf.ls", {"bench": BENCH, "branch": branch}).get("entries") or []
    for e in rows:
        if e.get("method"):
            params = dict(e.get("params") or {}); params.setdefault("name", BENCH)
            a(e["method"], params)
    ev = members(f"set:wb:{BSLUG}:sweep:{SWEEP}:evaluations")
    check(f"[{shape}] the run filed one evaluation under the sweep", len(ev) == 1, f"n={len(ev)}")
    import json as _json
    em = _json.loads((nuc.get_chunk_raw(ev[0]) or {}).get("meta") or "{}") if ev else {}
    check(f"[{shape}] the sweep evaluation carries branch + cond8 + built_at_epoch",
          em.get("branch") == branch and bool(em.get("cond8")) and em.get("built_at_epoch") is not None,
          str({kk: em.get(kk) for kk in ("cond8", "built_at_epoch")}))
    st2 = a("sweep.status", {"bench": BENCH, "name": SWEEP})
    check(f"[{shape}] status now derives done=1, pending=2 (the run's condition is done)",
          st2.get("done") == 1 and st2.get("pending") == 2,
          str({kk: st2.get(kk) for kk in ("done", "pending")}))

    # ── S2-l — the leaderboard is DERIVED state (R0): the inline run's learning.evaluate rebuilt it in the
    #    SAME write path, with NO explicit sweep.leaderboard call. It exists, has one row + artifact_id;
    #    a second identical evaluate is a no-op rebuild (artifact_id unchanged). ──
    def _lb_meta():
        return _json.loads((nuc.get_chunk_raw(nuc.get_key_by_alias(
            "wb:%s:leaderboard:%s" % (BSLUG, SWEEP))) or {}).get("meta") or "{}")
    lb_auto = _lb_meta()
    check(f"[{shape}] S2-l learning.evaluate auto-built the leaderboard (no command) with one row",
          lb_auto.get("concept") == "sweep_leaderboard" and lb_auto.get("count") == 1
          and bool(lb_auto.get("artifact_id")),
          str({kk: lb_auto.get(kk) for kk in ("count", "artifact_id")}))
    _aid0 = lb_auto.get("artifact_id")
    for e in rows:                                   # re-run the branch tail — a second identical evaluate
        if e.get("method") == "learning.evaluate":
            params = dict(e.get("params") or {}); params.setdefault("name", BENCH)
            a(e["method"], params)
    check(f"[{shape}] S2-l a second identical evaluate leaves the leaderboard artifact_id unchanged",
          _lb_meta().get("artifact_id") == _aid0, f"{_aid0} → {_lb_meta().get('artifact_id')}")

    # ── sweep.leaderboard — the MANUAL re-mint (participant) stays, unchanged ──
    lb = a("sweep.leaderboard", {"bench": BENCH, "name": SWEEP, "key": "accuracy"})
    check(f"[{shape}] sweep.leaderboard ranks the sweep (1 row) with built_at_epoch + artifact_id",
          lb.get("count") == 1 and lb.get("built_at_epoch") is not None and bool(lb.get("artifact_id"))
          and (lb.get("rows") or [{}])[0].get("rank") == 1, str(lb.get("rows"))[:160])
    # row naming — the row's `branch` is the readable LINEAGE (main@p0/…@cond8), matching learning.runs +
    # the evaluation row (§2.8); the slug is kept as `branch_slug` for a GUI key.
    _row0 = (lb.get("rows") or [{}])[0]
    check(f"[{shape}] the leaderboard row's branch is the lineage; branch_slug keeps the slug",
          str(_row0.get("branch", "")).startswith("main@p0/")
          and str(_row0.get("branch_slug", "")).startswith("main_p0_"),
          f"branch={_row0.get('branch')} slug={_row0.get('branch_slug')}")
    lm = _json.loads((nuc.get_chunk_raw(nuc.get_key_by_alias("wb:%s:leaderboard:%s" % (BSLUG, SWEEP)))
                      or {}).get("meta") or "{}")
    check(f"[{shape}] the leaderboard is stored as an epoch-keyed artifact atom",
          lm.get("concept") == "sweep_leaderboard" and bool(lm.get("artifact_id")), str(lm.get("count")))
    # rebuilt only when the input changed: an immediate re-run is unchanged
    lb2 = a("sweep.leaderboard", {"bench": BENCH, "name": SWEEP, "key": "accuracy"})
    check(f"[{shape}] a re-run with no new evaluation does not re-mint the leaderboard",
          lb2.get("changed") is False, str(lb2.get("changed")))

    # ── grid EXTENSION adds conditions only (a new seed value) ──
    sd3 = a("sweep.def", {"bench": BENCH, "name": SWEEP,
                          "grid": '{"head":["logreg","mlp"],"split":["0.8","0.7"],"seed":["1","2","3"]}',
                          "max": "18", "template": "learn_observe", "fixed": "space=color"})
    check(f"[{shape}] a grid extension adds conditions only (8 → 12, +4 new)",
          sd3.get("conds") == 12 and sd3.get("added") == 4, f"conds={sd3.get('conds')} added={sd3.get('added')}")

    # ── sweep.status is guest-readable ──
    gs = g("sweep.status", {"bench": BENCH, "name": SWEEP})
    check(f"[{shape}] a guest can read sweep.status",
          not gs.get("error") and gs.get("conds") == 12, str(gs)[:120])

    # ── admission — a materialised branch lineage is admitted; a random name is not ──
    from lib.akasha.concepts.society import SocietyConcept
    scpt = SocietyConcept(k.manager.get_session("admin"))
    check(f"[{shape}] a materialised sweep branch lineage is admitted for society.run",
          scpt._is_admitted_sweep_branch(BENCH, [SWEEP], branch) is True
          and scpt._is_admitted_sweep_branch(BENCH, [SWEEP], "not-a-branch") is False)

    # ── S2-d — privilege is the ROLE, not the literal id: a Genesis-named admin (id != 'admin',
    #    session carries scope:sys:admin) can materialise; a plain user is refused with a log line ──
    a("user.add", {"client_id": "henri", "role": "admin",
                   "passphrase_hash": hashlib.sha256(b"h").hexdigest()})
    a("user.add", {"client_id": "bob", "role": "user",
                   "passphrase_hash": hashlib.sha256(b"b").hexdigest()})
    check(f"[{shape}] a Genesis-named admin (id=henri, scope:sys:admin) holds admin scope",
          "scope:sys:admin" in (k.manager.get_session("henri").active_scopes or []),
          str(k.manager.get_session("henri").active_scopes)[:120])
    mh = as_("henri", "sweep.materialise", {"bench": BENCH, "name": SWEEP, "n": "1"})
    check(f"[{shape}] a Genesis-named admin can materialise (privileged by role, not by id 'admin')",
          mh.get("status") == "materialised" and (mh.get("branches") or 0) >= 1, str(mh)[:140])

    # WHAT REFUSES BOB, and in whose words. S2-d's `_is_privileged` + `sweep._refuse` are deleted
    # (one-gate ruling §5) — a second rule, in a second vocabulary, beside the one the dispatcher
    # had already applied. The refusal is the GATE's now, and it comes from step 3: this bench is
    # PUBLIC (nucleus-resident, readable by every identity), so bob's own row reaches it or
    # nothing does. The reason id is `out_of_scope` and the log line is the one `[gate] refused`.
    #
    # That the target reaches the gate at all is the fix this check is really guarding: the
    # boundary asks `gate(identity, record)` and cannot know which bench, so without the op's own
    # second question bob's `record` on somebody else's public bench and his `record` in his own
    # cell were the same question — and the eighth row (`resident`) answers that one yes.
    import logging, io as _io
    _buf = _io.StringIO(); _h = logging.StreamHandler(_buf)
    _lg = logging.getLogger("Akasha.Kernel"); _lg.addHandler(_h); _lvl = _lg.level
    _lg.setLevel(logging.INFO)
    try:
        rb = as_("bob", "sweep.materialise", {"bench": BENCH, "name": SWEEP, "n": "1"})
    finally:
        _lg.removeHandler(_h); _lg.setLevel(_lvl)
    _e = str((rb.get("error") or {}).get("message") or "") if isinstance(rb, dict) else ""
    check(f"[{shape}] a plain user (bob) is refused sweep.materialise",
          "bob" in _e and "out_of_scope" in _e, str(rb)[:160])
    check(f"[{shape}] …and the refusal is the gate's ONE line, naming identity/action/target/reason",
          "[gate] refused" in _buf.getvalue() and "identity=bob" in _buf.getvalue()
          and "target=wb:plants_vision" in _buf.getvalue()
          and "reason=out_of_scope" in _buf.getvalue(), _buf.getvalue().strip()[:160])

    # S2-d(3) — a refused step must FAIL the job, not end DONE 1/1: csl.run fail_on_refused (the flag
    # macro.run's background job sets) turns a refused sub-command into a JSON-RPC error.
    rc = k.dispatch({"jsonrpc": "2.0", "method": "csl.run", "params": {"session_token": "bob", "data": {
        "script": 'sweep.materialise bench="%s" name="%s" n="1"' % (BENCH, SWEEP),
        "fail_on_refused": True}}, "id": "fr"}, "local")
    check(f"[{shape}] csl.run fail_on_refused surfaces a refused command as an error (job FAILS)",
          isinstance(rc, dict) and "error" in rc and "bob" in str(rc["error"]), str(rc)[:160])
    # …and WITHOUT the flag, the same refused command does not error (back-compat)
    rc2 = k.dispatch({"jsonrpc": "2.0", "method": "csl.run", "params": {"session_token": "bob", "data": {
        "script": 'sweep.materialise bench="%s" name="%s" n="1"' % (BENCH, SWEEP)}}, "id": "fr2"}, "local")
    check(f"[{shape}] without fail_on_refused a refused command still returns ok (back-compat)",
          isinstance(rc2, dict) and "error" not in rc2)

    # ── S2-c — a list-shaped `data` (malformed client / scanner probe) is answered -32602, not a
    #    -32000 traceback ──
    lp = k.dispatch({"jsonrpc": "2.0", "method": "sweep.status",
                     "params": {"session_token": "admin", "data": [1, 2, 3]}, "id": "lp"}, "local")
    check(f"[{shape}] a list-shaped `data` returns -32602 (no traceback / -32000)",
          isinstance(lp, dict) and (lp.get("error") or {}).get("code") == -32602, str(lp)[:120])

    # ── S2-a — sweep.mark stamps a branch's condition failed (the pending→failed move the driver
    #    makes at its block-status site); a branch that fails no longer stays `pending` forever ──
    _pend = [m.get("branch") for m in (ms.get("made") or []) if m.get("branch") != branch]
    fb = a("sweep.mark", {"bench": BENCH, "branch": _pend[0], "status": "failed"})
    check(f"[{shape}] sweep.mark stamps a materialised branch's condition failed",
          fb.get("status") == "marked" and fb.get("cond_status") == "failed", str(fb)[:120])
    st_f = a("sweep.status", {"bench": BENCH, "name": SWEEP})
    check(f"[{shape}] sweep.status reflects the failed condition (failed>=1)",
          (st_f.get("failed") or 0) >= 1, str({kk: st_f.get(kk) for kk in ("done", "pending", "failed")}))
    nm = a("sweep.mark", {"bench": BENCH, "branch": "not-a-sweep-branch", "status": "failed"})
    check(f"[{shape}] sweep.mark is a no-op for a non-sweep workflow",
          nm.get("status") == "noop", str(nm)[:80])

    # ── S2-b — the leaderboard joined the bindings, carries leak?, and keeps a :history Set ──
    lb3 = a("sweep.leaderboard", {"bench": BENCH, "name": SWEEP, "key": "accuracy"})
    _r0 = (lb3.get("rows") or [{}])[0]
    check(f"[{shape}] leaderboard rows join the sweep bindings + carry leak?",
          isinstance(_r0.get("bindings"), dict) and _r0.get("bindings") and ("leak" in _r0),
          str(_r0.get("bindings")))
    hist = members(f"set:wb:{BSLUG}:leaderboard:{SWEEP}:history")
    check(f"[{shape}] the leaderboard keeps a :history Set (>=1 generation)", len(hist) >= 1, str(len(hist)))

    # ── S2-h — only the IMPLEMENTED learner kinds (learned_head.KINDS = logreg, mlp) are accepted:
    #    sweep.def REFUSES a grid with an unknown head at definition time, and learning.train refuses one at
    #    run time — neither silently degrades to the centroid/majority mock (which read as a real model) ──
    import lib.akasha.concepts.learned_head as _lh
    check(f"[{shape}] learned_head.KINDS is exactly the implemented learners (logreg, mlp)",
          tuple(_lh.KINDS) == ("logreg", "mlp"), str(_lh.KINDS))
    sdr = a("sweep.def", {"bench": BENCH, "name": "badhead",
                          "grid": '{"head":["logreg","ridge"]}', "max": "8",
                          "template": "learn_observe", "fixed": "space=color"})
    check(f"[{shape}] sweep.def refuses a grid naming an unimplemented head (ridge)",
          sdr.get("status") == "refused" and "ridge" in str(sdr.get("reason", "")), str(sdr)[:160])
    # (run is non-empty so the head check — which fires right after the run check — is what refuses)
    tr_bad = a("learning.train", {"name": BENCH, "run": "f_x", "head": "ridge"})
    check(f"[{shape}] learning.train refuses an unimplemented head (ridge) instead of degrading",
          isinstance(tr_bad, dict) and "error" in tr_bad and "ridge" in str(tr_bad["error"]),
          str(tr_bad)[:160])

    # ── §2.8 — a learning.runs row for a materialised sweep branch carries the sweep COORDINATE (the full
    #    lineage + cond8), read from the branch's marker — not only the `wf_branch` slug ──
    br_runs = a("learning.runs", {"name": BENCH})
    _swrows = [r for r in (br_runs.get("runs") or []) if r.get("wf_branch") == branch]
    check(f"[{shape}] §2.8 learning.runs fills branch (lineage) + cond8 from the sweep marker",
          bool(_swrows) and all(r.get("cond8") and r.get("branch") for r in _swrows),
          f"rows={[(r.get('wf_branch'), r.get('cond8'), r.get('branch')) for r in _swrows][:2]}")
    # ── B1-b — a run row carries its cost (reused / wall_s), stamped on the run atom by vlab.run.execute
    #    (GUI §7 renders them). The branch ran its feature + observe runs above, so at least one row of
    #    this bench has a numeric wall_s and a reused count (>=0). ──
    _cost_rows = [r for r in (br_runs.get("runs") or [])
                  if isinstance(r.get("wall_s"), (int, float)) and isinstance(r.get("reused"), int)]
    check(f"[{shape}] B1-b learning.runs rows carry numeric reused + wall_s (the run's cost)",
          bool(_cost_rows) and any((r.get("wall_s") or 0) >= 0 for r in _cost_rows),
          f"cost_rows={[(r.get('run'), r.get('reused'), r.get('wall_s')) for r in _cost_rows][:2]}")

    # ── S2-i — `wf.advance as=job` records the EXECUTION TRACE (one cronon:executes coordinate per step)
    #    exactly like the inline path, and stamps the sweep condition from the job's terminal state, so a
    #    manual run and a driver run leave the SAME trace. The learn_observe template is 7 structured ops.
    if k.jcl_worker:
        # (a) success: advance the branch as ONE JCL job → 7 steps run → 7 execution coordinates. The
        #     coordinate is minted for every step that RAN (fail_fast=False), so count=7 is robust.
        rj = a("wf.advance", {"bench": BENCH, "branch": branch, "n": "1000", "as": "job"})
        ce = a("cronon.executions", {"bench": BENCH, "branch": branch})
        check(f"[{shape}] wf.advance as=job mints 7 execution coordinates (cronon:executes)",
              ce.get("count") == 7,
              f"count={ce.get('count')} job_status={rj.get('job_status')} minted={rj.get('minted')}")
        # (b) a planted failure: a fresh branch with a bad tail step → the job does not succeed and its
        #     sweep condition is stamped `failed` by the shared recorder (never left pending forever).
        _fresh = (a("sweep.materialise", {"bench": BENCH, "name": SWEEP, "n": "1"}).get("made") or [{}])
        fail_b = _fresh[0].get("branch")
        # plant a STRUCTURED step that runs but errors — a real learning.evaluate on a model that was never
        # trained → "unknown model" at dispatch, so the job ends with a step error (ok=False) and the
        # shared recorder stamps the sweep condition failed. (A plain-string wf.write entry is stored as
        # text; a structured step needs a {method, params} entry.)
        a("wf.write", {"bench": BENCH, "branch": fail_b, "pos": "8",
                       "entry": {"method": "learning.evaluate",
                                 "params": {"name": BENCH, "model": "model:learned:never_trained",
                                            "sample": "test"}}})
        rjf = a("wf.advance", {"bench": BENCH, "branch": fail_b, "n": "1000", "as": "job"})
        stf = a("sweep.status", {"bench": BENCH, "name": SWEEP})
        _cond = next((c for c in (stf.get("conditions") or []) if c.get("branch") == fail_b), {})
        check(f"[{shape}] a planted-fail branch run as=job stamps its sweep condition failed",
              rjf.get("job_status") in ("DONE", "FAILED") and _cond.get("status") == "failed",
              f"job_status={rjf.get('job_status')} minted={rjf.get('minted')} cond={_cond.get('status')}")

    # ── S2-h2 — a stale INVALID-head condition (from an older grid, e.g. ridge) is RETIRED by the next
    #    sweep.def: it stays in the fan (history) but materialise never picks it (it would fail at
    #    learning.train) and sweep.status counts it. sweep.def refuses a ridge GRID (S2-h), so the stale
    #    condition is injected directly to model a cell that carried an older, wider grid. ──
    from lib.akasha.concepts.sweep import SweepConcept
    _sw = SweepConcept(k.manager.get_session("admin"))
    _sw._bind(_sw._bench_gid(BENCH))
    _ck = _sw._mk(_sw._cond_alias(BENCH, SWEEP, "ridgexx"), "[stale] head=ridge",
                  {"concept": "sweep_cond", "bench": _sw._bench_alias(BENCH), "sweep": SWEEP,
                   "bindings": {"head": "ridge", "split": "0.8", "seed": "1"}, "grid8": "ridgexx",
                   "template": "learn_observe", "status": "unmaterialised", "branch": None, "cond8": None})
    _sw._add_to_set(_sw._conds_set(BENCH, SWEEP), _ck)
    # S2-m2/S2-m3 — a MATERIALISED invalid-head condition (it has a branch, it ran) must NOT read
    # `retired`. Seed it with a STALE stored status=retired (as an earlier build wrongly wrote): the
    # re-apply must CLEAR that (S2-m3) and status must DERIVE it non-retired, with retired_grid=true, so
    # the fan does not claim nothing ran while the board ranks that run.
    _ckb = _sw._mk(_sw._cond_alias(BENCH, SWEEP, "ridgeyy"), "[stale-but-ran] head=ridge",
                   {"concept": "sweep_cond", "bench": _sw._bench_alias(BENCH), "sweep": SWEEP,
                    "bindings": {"head": "ridge", "split": "0.7", "seed": "1"}, "grid8": "ridgeyy",
                    "template": "learn_observe", "status": "retired",
                    "branch": "main_p0_learn_observe_ranridge", "cond8": "ranridge"})
    _sw._add_to_set(_sw._conds_set(BENCH, SWEEP), _ckb)
    sd_ret = a("sweep.def", {"bench": BENCH, "name": SWEEP,
                             "grid": '{"head":["logreg","mlp"],"split":["0.8","0.7"],"seed":["1","2","3"]}',
                             "max": "18", "template": "learn_observe", "fixed": "space=color"})
    check(f"[{shape}] S2-h2 sweep.def retires the BRANCHLESS stale invalid-head (ridge) condition only",
          (sd_ret.get("retired") or 0) >= 1, f"retired={sd_ret.get('retired')}")
    st_ret = a("sweep.status", {"bench": BENCH, "name": SWEEP})

    def _by_grid8(status, g8):
        return next((c for c in (status.get("conditions") or []) if c.get("grid8") == g8), {})
    _rx = _by_grid8(st_ret, "ridgexx")
    _ry = _by_grid8(st_ret, "ridgeyy")
    check(f"[{shape}] S2-h2 the branchless ridge cond is retired (status=retired, counted)",
          (st_ret.get("retired") or 0) >= 1 and _rx.get("status") == "retired", str(_rx)[:120])
    check(f"[{shape}] S2-m3 the MATERIALISED ridge cond reads non-retired (stale retired cleared, "
          f"retired_grid=true, not counted)",
          _ry.get("status") not in ("retired", None) and _ry.get("retired_grid") is True
          and _ry.get("status") == "pending", str(_ry)[:140])
    ma = a("sweep.materialise", {"bench": BENCH, "name": SWEEP, "n": "50"})
    st_ma = a("sweep.status", {"bench": BENCH, "name": SWEEP})
    _rx2 = _by_grid8(st_ma, "ridgexx")
    check(f"[{shape}] S2-h2 materialise never picks the retired branchless condition",
          _rx2.get("branch") is None and _rx2.get("status") == "retired", str(_rx2)[:120])

    # ── B1-c — the auto-run DRIVER picks branches, budget-gated; quarantine + release; drift ──
    from lib.akasha.concepts.sweep import SweepConcept
    swd = SweepConcept(k.manager.get_session("admin"))
    DRV = "drv1"
    a("sweep.def", {"bench": BENCH, "name": DRV,
                    "grid": '{"head":["logreg","mlp"],"split":["0.8"],"seed":["1"]}',
                    "template": "learn_observe", "fixed": "space=color",
                    "budget": '{"per_day":1,"total":12,"drift_per_day":0}'})
    # per_day=1 → the driver materialises one condition, picks it, and spends one unit
    p1 = swd.driver_pick(bench=BENCH, name=DRV)
    check(f"[{shape}] B1-c driver_pick (per_day=1) picks one branch and spends one unit",
          p1.get("status") == "picked" and p1.get("kind") == "pending"
          and p1.get("spent_total") == 1 and p1.get("budget_left") == 11, str(p1)[:160])
    p2 = swd.driver_pick(bench=BENCH, name=DRV)
    check(f"[{shape}] B1-c a second pick the same day is budget_exhausted (per_day=1)",
          p2.get("status") == "budget_exhausted" and p2.get("scope") == "per_day", str(p2)[:120])
    # per_day=0 → the driver picks none
    a("sweep.def", {"bench": BENCH, "name": "drv0",
                    "grid": '{"head":["logreg"],"split":["0.8"],"seed":["1"]}',
                    "template": "learn_observe", "fixed": "space=color",
                    "budget": '{"per_day":0,"total":12}'})
    pz = swd.driver_pick(bench=BENCH, name="drv0")
    check(f"[{shape}] B1-c per_day=0 → the driver picks none (budget_exhausted per_day)",
          pz.get("status") == "budget_exhausted" and pz.get("scope") == "per_day", str(pz)[:120])
    # a sweep with no budget block is opt-OUT of the driver
    a("sweep.def", {"bench": BENCH, "name": "drvnob",
                    "grid": '{"head":["logreg"],"split":["0.8"],"seed":["1"]}',
                    "template": "learn_observe", "fixed": "space=color"})
    check(f"[{shape}] B1-c a sweep with no budget is not auto-driven (no_budget)",
          swd.driver_pick(bench=BENCH, name="drvnob").get("status") == "no_budget")

    if k.jcl_worker:
        # ── quarantine — two step_failed deviations on the picked branch quarantine it; release lifts it ──
        fbranch = p1.get("branch_slug")
        a("wf.write", {"bench": BENCH, "branch": fbranch, "pos": "8",
                       "entry": {"method": "learning.evaluate",
                                 "params": {"name": BENCH, "model": "model:learned:never_trained",
                                            "sample": "test"}}})
        a("wf.advance", {"bench": BENCH, "branch": fbranch, "n": "1000", "as": "job"})
        a("wf.rewind", {"bench": BENCH, "branch": fbranch, "pos": "7", "by": "driver"})
        a("wf.advance", {"bench": BENCH, "branch": fbranch, "n": "1000", "as": "job"})
        st_q = a("sweep.status", {"bench": BENCH, "name": DRV})
        cq = next((c for c in (st_q.get("conditions") or []) if c.get("branch") == fbranch), {})
        check(f"[{shape}] B1-c two step_failed deviations quarantine the branch (status.quarantined)",
              cq.get("quarantined") is True and (st_q.get("quarantined") or 0) >= 1,
              f"quarantined={cq.get('quarantined')} n={st_q.get('quarantined')}")
        rel = a("sweep.release", {"bench": BENCH, "name": DRV, "branch": fbranch})
        check(f"[{shape}] B1-c sweep.release stamps released_at",
              rel.get("status") == "released" and rel.get("released_at") is not None, str(rel)[:120])
        st_r = a("sweep.status", {"bench": BENCH, "name": DRV})
        cr = next((c for c in (st_r.get("conditions") or []) if c.get("branch") == fbranch), {})
        check(f"[{shape}] B1-c after release the branch is no longer quarantined",
              cr.get("quarantined") is False, str(cr)[:120])

    # ── drift — a sweep with drift_per_day>0 whose one condition is DONE returns a `drift` pick. Its
    #    binding is UNIQUE (seed=9) so its branch never collides with an earlier quarantined branch. ──
    DRF = "drvdrift"
    a("sweep.def", {"bench": BENCH, "name": DRF,
                    "grid": '{"head":["logreg"],"split":["0.8"],"seed":["9"]}',
                    "template": "learn_observe", "fixed": "space=color",
                    "budget": '{"per_day":1,"total":12,"drift_per_day":1}'})
    dm = (a("sweep.materialise", {"bench": BENCH, "name": DRF, "n": "1"}).get("made") or [{}])[0]
    drf_branch = dm.get("branch")
    for e in (a("wf.ls", {"bench": BENCH, "branch": drf_branch}).get("entries") or []):
        if e.get("method"):
            params = dict(e.get("params") or {}); params.setdefault("name", BENCH)
            a(e["method"], params)
    st_drf = a("sweep.status", {"bench": BENCH, "name": DRF})
    _cdone = next((c for c in (st_drf.get("conditions") or []) if c.get("branch") == drf_branch), {})
    check(f"[{shape}] B1-c the drift sweep's one condition is done (its branch ran)",
          _cdone.get("status") == "done", str(_cdone)[:120])
    pd = swd.driver_pick(bench=BENCH, name=DRF)
    check(f"[{shape}] B1-c with nothing pending + drift_per_day>0 the driver returns a drift pick",
          pd.get("status") == "picked" and pd.get("kind") == "drift"
          and pd.get("drift_today") == 1, str(pd)[:160])


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the sweep engine defines a grid into conditions, materialises them into "
          "wf branches, derives done from each branch's evaluation, ranks the sweep into an epoch-keyed "
          "leaderboard, extends a grid additively, reads guest-side, and admits its branches for "
          "society.run — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
