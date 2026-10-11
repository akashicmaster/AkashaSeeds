#!/usr/bin/env python3
"""
B1 §A3 — DEVIATION ATOMS: the one writer, the six kinds, the faceting Sets, the links.

A deviation is a FACT recorded the moment an execution's ACTUAL diverges from its PLAN. There is exactly
ONE writer — `WorkflowConcept._mint_deviation` — called from six triggers (step_failed, rewound,
param_override, admission_refused, budget_chunked, result_drift). Each mint is an immutable atom
(content-addressed, never replaced) joined to three Sets — the bench's `:deviations`, the kind facet
`:deviation:kind:<kind>`, and the branch facet `:deviation:branch:<slug>` — and linked `deviates_from`
→ the plan entry it diverged from and `observed_in` → the execution coordinate it happened at. Written
UNIVERSAL (nucleus) so the fan is guest-readable like the coordinates it references.

This eval drives it on BOTH cell shapes:
  • the ORGANIC triggers — a planted-fail branch run as=job (step_failed), a driver rewind (rewound),
    a hand wf.branch overriding a template default (param_override) — each mints exactly one atom, in
    the three Sets, and step_failed carries its deviates_from + observed_in links + coordinate;
  • the writer for the three kinds harder to force here (admission_refused / budget_chunked /
    result_drift) minted once each through the same `_mint_deviation`;
  • `lens.rank group=kind` faces the deviations Set into one group per kind, each count 1.

Run:  python app/test/deviation_eval.py     (exit 0 = all pass)
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
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_dev_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus.core

    def members(setname):
        try:
            return list(nuc.get_collection_members(setname) or [])
        except Exception:
            return []

    def dmeta(key):
        return json.loads((nuc.get_chunk_raw(key) or {}).get("meta") or "{}")

    # ── a PUBLIC learning bench + workflow + frozen pool + role samples + a sweep (mock space) ──
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
                    "grid": '{"head":["logreg","mlp"],"split":["0.8"],"seed":["1"]}',
                    "template": "learn_observe", "fixed": "space=color"})

    if not k.jcl_worker:
        check(f"[{shape}] JCL worker available (deviation triggers need as=job)", False)
        return

    # ── ORGANIC step_failed — a planted-fail branch run as=job mints exactly one step_failed deviation
    #    in the three Sets, with deviates_from + observed_in links + a coordinate. ──
    fb = (a("sweep.materialise", {"bench": BENCH, "name": SWEEP, "n": "1"}).get("made") or [{}])[0].get("branch")
    a("wf.write", {"bench": BENCH, "branch": fb, "pos": "8",
                   "entry": {"method": "learning.evaluate",
                             "params": {"name": BENCH, "model": "model:learned:never_trained",
                                        "sample": "test"}}})
    a("wf.advance", {"bench": BENCH, "branch": fb, "n": "1000", "as": "job"})
    sf = members("set:wb:%s:deviation:kind:step_failed" % BSLUG)
    check(f"[{shape}] a planted-fail run mints exactly ONE step_failed deviation", len(sf) == 1,
          f"n={len(sf)}")
    in_all = set(members("set:wb:%s:deviations" % BSLUG))
    in_branch = set(members("set:wb:%s:deviation:branch:%s" % (BSLUG, fb)))
    check(f"[{shape}] the step_failed deviation is a member of all three Sets (deviations/kind/branch)",
          bool(sf) and sf[0] in in_all and sf[0] in in_branch,
          f"all={sf[0] in in_all} branch={sf[0] in in_branch}")
    if sf:
        dm = dmeta(sf[0])
        rels = {l.get("rel") for l in (nuc.get_adjacent_links(sf[0]) or [])}
        check(f"[{shape}] the step_failed deviation links deviates_from + observed_in",
              "deviates_from" in rels and "observed_in" in rels, str(sorted(rels)))
        check(f"[{shape}] the step_failed deviation carries kind + branch_slug + a coordinate + actual",
              dm.get("kind") == "step_failed" and dm.get("branch_slug") == fb
              and str(dm.get("coordinate") or "").startswith("cronon:wb:%s:c" % BSLUG)
              and bool(dm.get("actual")),
              str({kk: dm.get(kk) for kk in ("kind", "coordinate")}))

    # ── ORGANIC rewound — a DRIVER rewind mints exactly one rewound deviation (an agent rewind does not) ──
    # an IN-RUN driver rewind (to a non-zero position) IS a divergence → one rewound
    a("wf.rewind", {"bench": BENCH, "branch": fb, "pos": "3", "by": "driver"})
    rw = members("set:wb:%s:deviation:kind:rewound" % BSLUG)
    check(f"[{shape}] an in-run driver rewind (pos!=0) mints exactly ONE rewound deviation",
          len(rw) == 1, f"n={len(rw)}")
    # B1-a — the scheduled reset-to-0 before a rerun (reason=rerun) is the run's precondition, NOT a
    #        divergence → it mints NO deviation (else the daily reruns add eight rewound atoms a day).
    a("wf.rewind", {"bench": BENCH, "branch": fb, "pos": "0", "by": "driver", "reason": "rerun"})
    check(f"[{shape}] B1-a the scheduled rerun reset to 0 mints NO rewound (run precondition)",
          len(members("set:wb:%s:deviation:kind:rewound" % BSLUG)) == 1,
          f"n={len(members('set:wb:%s:deviation:kind:rewound' % BSLUG))}")
    # a retry rewind IS an in-run divergence even at pos 0 → one more rewound
    a("wf.rewind", {"bench": BENCH, "branch": fb, "pos": "0", "by": "driver", "reason": "retry"})
    check(f"[{shape}] B1-a an in-run retry rewind (reason=retry) mints a rewound even at pos 0",
          len(members("set:wb:%s:deviation:kind:rewound" % BSLUG)) == 2,
          f"n={len(members('set:wb:%s:deviation:kind:rewound' % BSLUG))}")
    # an AGENT rewind is a thought act — it mints nothing here
    a("wf.rewind", {"bench": BENCH, "branch": fb, "pos": "2", "by": "agent"})
    check(f"[{shape}] an agent rewind mints NO deviation (a thought act, not a divergence)",
          len(members("set:wb:%s:deviation:kind:rewound" % BSLUG)) == 2)

    # ── ORGANIC param_override — a HAND wf.branch overriding one template default (seed) mints exactly
    #    one param_override; a sweep materialise (bindings ARE the dimensions, _sweep_bound) mints none. ──
    a("wf.branch", {"bench": BENCH, **{"from": "learn_observe", "params": "seed=99", "parent": "main"}})
    po = members("set:wb:%s:deviation:kind:param_override" % BSLUG)
    check(f"[{shape}] a hand wf.branch overriding one default mints exactly ONE param_override", len(po) == 1,
          f"n={len(po)}")
    if po:
        pm = dmeta(po[0])
        check(f"[{shape}] param_override records the default→passed change (seed plants1→99)",
              pm.get("planned", {}).get("seed") == "plants1" and pm.get("actual", {}).get("seed") == "99",
              str({"planned": pm.get("planned"), "actual": pm.get("actual")}))

    # ── the writer for the three kinds not easily forced here (same one writer, distinct exec_id) ──
    from lib.akasha.concepts.workflow import WorkflowConcept
    wc = WorkflowConcept(k.manager.get_session("admin"))
    gid = wc._bench_gid(BENCH)
    for kind in ("admission_refused", "budget_chunked", "result_drift"):
        wc._mint_deviation(BENCH, gid, "main@p0/learn_observe@zz", 0, kind,
                           {"plan": kind}, {"actual": kind}, exec_id="ex_%s" % kind)
    for kind in ("admission_refused", "budget_chunked", "result_drift"):
        check(f"[{shape}] the writer mints exactly one {kind} deviation",
              len(members("set:wb:%s:deviation:kind:%s" % (BSLUG, kind))) == 1)

    # ── all six kinds present; lens.rank group=kind faces the deviations Set into one group per kind ──
    all_dev = members("set:wb:%s:deviations" % BSLUG)
    kinds = sorted({dmeta(d).get("kind") for d in all_dev})
    # seven atoms: one of each kind, plus the second `rewound` from the retry rewind above.
    check(f"[{shape}] the deviations Set holds all six kinds (rewound twice: in-run + retry)",
          kinds == ["admission_refused", "budget_chunked", "param_override", "result_drift",
                    "rewound", "step_failed"] and len(all_dev) == 7, f"kinds={kinds} n={len(all_dev)}")
    lr = a("lens.rank", {"set": "set:wb:%s:deviations" % BSLUG, "group": "kind"})
    per_kind = {g.get("group", {}).get("kind"): len(g.get("rows") or []) for g in (lr.get("groups") or [])}
    check(f"[{shape}] lens.rank group=kind returns one group per kind (rewound=2, the rest 1)",
          len(per_kind) == 6 and per_kind.get("rewound") == 2
          and all(v == 1 for kk, v in per_kind.items() if kk != "rewound"), str(per_kind))

    # ── a deviation is a FACT — never replaced: re-minting the identical divergence is idempotent ──
    _before = len(members("set:wb:%s:deviations" % BSLUG))
    wc._mint_deviation(BENCH, gid, "main@p0/learn_observe@zz", 0, "budget_chunked",
                       {"plan": "budget_chunked"}, {"actual": "budget_chunked"}, exec_id="ex_budget_chunked")
    check(f"[{shape}] re-minting the identical deviation is idempotent (content-addressed)",
          len(members("set:wb:%s:deviations" % BSLUG)) == _before, f"{_before} → after")


def main():
    print("=" * 78)
    print("B1 §A3 — deviation atoms: one writer, six kinds, faceting Sets + links")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — deviations are minted by the ONE writer at their six triggers, joined to the "
          "deviations/kind/branch Sets, linked deviates_from + observed_in, faced by lens.rank group=kind, "
          "and content-addressed (a re-mint is idempotent) — both cell shapes.")


if __name__ == "__main__":
    main()
