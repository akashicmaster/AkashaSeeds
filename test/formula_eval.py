#!/usr/bin/env python3
"""
Formula eval — the generic base model (materials + operations + process + rollup).

`formula` is the domain-neutral base that `recipe` extends. It handles materials
with quantities, operations, an ordered process, a schema-agnostic property rollup
(cost / mass / any numeric property, weighted by quantity), and axis-driven
suggestion. This eval drives it directly (a dye-mixing formula) to prove the base
works standalone — the same machinery recipe inherits.

  F1 universe    — new + material + op + step build the graph; view assembles it.
  F2 cost rollup — rollup sums BOTH per-source props (× qty) AND a direct line cost;
                   a mass material with no source but a direct cost is still measured.
  F3 target      — spec value=cost<=3 is a numeric target checked against the rollup.
  F4 constraint  — a categorical spec is a hard filter: suggest avoid=<tag> subtracts.
  F5 ls / axis   — formula.ls filters by discrete axis (intersection).
  F6 status      — non-mass unit → unmeasured; mass + no source + no direct → no_data.
  F7 critical    — steps form a dependency DAG (after=); formula.critical returns the
                   makespan with parallel branches < the sequential total, and the
                   zero-slack critical path (a parallel branch carries slack).
  F8 control     — a control spec (param bound, optional ccp) is checked against a
                   recorded measurement: pass → fail when a later measurement violates
                   the bound; `safe` and `ccp_all_pass` track the CCP subset.

Run:  python test/formula_eval.py
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
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def main():
    print("\n  formula eval — generic materials + operations + process + rollup\n")
    from lib.akasha.kernel import KernelDispatcher
    from api.router import CommandRouter as R
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_form_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def run(cli):
        p = R.build_rpc_request(cli, "admin")
        if p is None:
            return {"error": {"message": "UNKNOWN_COMMAND", "cli": cli}}
        return k.dispatch(p, "local")

    def res(cli):
        r = run(cli)
        assert "error" not in r, f"{cli} -> {r.get('error')}"
        return r["result"]

    # F1 — build a dye-mixing formula.
    a = res('formula.new "Crimson Dye" kind=dye line=textile')["formula_id"]
    res(f'formula.source name=madder cost=0.8 basis=100')          # per-100g cost
    res(f'formula.material {a} name=madder qty=200 unit=g')         # 2.0 × 0.8 = 1.6
    res(f'formula.material {a} name=mordant qty=50 unit=g cost=0.5')  # direct line cost
    res(f'formula.op {a} name=simmer')
    res(f'formula.step {a} text="heat the bath to 80C" uses=madder by=simmer')
    view = res(f"formula.view {a}")
    f1 = (view["title"] == "Crimson Dye"
          and view["counts"] == {"materials": 2, "operations": 1, "steps": 1}
          and view["steps"][0]["uses"] and view["steps"][0]["by"])
    record("F1 universe", f1, f"counts={view['counts']}")

    # F2 — cost rollup: 1.6 (source-scaled) + 0.5 (direct) = 2.1; both materials measured.
    roll = res(f"formula.rollup {a}")
    f2 = (abs(roll["totals"].get("cost", 0) - 2.1) < 0.001 and roll["measured"] == 2)
    record("F2 cost rollup", f2, f"cost={roll['totals'].get('cost')} measured={roll['measured']}")

    # F3 — numeric target checked against the rollup.
    res(f'formula.spec {a} value=cost<=3')     # met (2.1)
    res(f'formula.spec {a} value=cost<=1')     # NOT met
    roll2 = res(f"formula.rollup {a}")
    tgt = {(t["key"], t["value"]): t["met"] for t in roll2["targets"]}
    f3 = (tgt.get(("cost", 3.0)) is True and tgt.get(("cost", 1.0)) is False)
    record("F3 target", f3, f"targets={[(t['key'],t['value'],t['met']) for t in roll2['targets']]}")

    # F4 — categorical constraint is a hard filter for suggestion.
    res(f'formula.spec {a} value=azo')                      # a categorical constraint tag
    b = res('formula.new "Blue Dye" kind=dye line=textile')["formula_id"]
    res(f'formula.material {b} name=madder qty=10 unit=g')  # shares the madder axis
    sug = res("formula.suggest kind=dye have=madder")
    ids = [s["formula_id"] for s in sug["suggestions"]]
    sug2 = res("formula.suggest kind=dye have=madder avoid=azo")
    ids2 = [s["formula_id"] for s in sug2["suggestions"]]
    f4 = (a in ids and b in ids and a not in ids2 and b in ids2 and sug2["blocked_count"] >= 1)
    record("F4 constraint", f4, f"a_dropped={a not in ids2} b_kept={b in ids2} blocked={sug2['blocked_count']}")

    # F5 — ls axis filter.
    dye = {r["formula_id"] for r in res("formula.ls kind=dye")["formulas"]}
    f5 = (a in dye and b in dye)
    record("F5 ls / axis", f5, f"dye={len(dye)}")

    # F6 — status: non-mass unit → unmeasured; mass + no source + no direct → no_data.
    c = res('formula.new "Status Probe" kind=test')["formula_id"]
    res(f'formula.source name=known cost=1 basis=100')
    res(f'formula.material {c} name=known qty=100 unit=g')      # measured (source)
    res(f'formula.material {c} name=counted qty=2 unit=pc')     # unmeasured (non-mass, no direct)
    res(f'formula.material {c} name=bare qty=100 unit=g')       # no_data (mass, no source, no direct)
    rc = res(f"formula.rollup {c}")
    f6 = ("counted" in rc["unmeasured"] and "bare" in rc["no_data"] and rc["measured"] == 1)
    record("F6 status", f6, f"unmeasured={rc['unmeasured']} no_data={rc['no_data']} measured={rc['measured']}")

    # F7 — PERT: prep(10) → {stew(20 after prep), garnish(5 after prep)} → plate(3 after 1,2).
    d = res('formula.new "Timed Process" kind=proc')["formula_id"]
    res(f'formula.step {d} text="prep" dur=10 label=prep')
    res(f'formula.step {d} text="stew" dur=20 after=prep')       # order 1
    res(f'formula.step {d} text="garnish" dur=5 after=prep')     # order 2 (parallel)
    res(f'formula.step {d} text="plate" dur=3 after=1,2')        # order 3
    cp = res(f"formula.critical {d}")
    crit_orders = sorted(r["order"] for r in cp["steps"] if r["critical"])
    garnish = next(r for r in cp["steps"] if r["order"] == 2)
    f7 = (abs(cp["makespan_min"] - 33.0) < 0.01 and abs(cp["sequential_min"] - 38.0) < 0.01
          and crit_orders == [0, 1, 3] and abs(garnish["slack"] - 15.0) < 0.01)
    record("F7 critical", f7,
           f"makespan={cp['makespan_min']} seq={cp['sequential_min']} "
           f"critical={crit_orders} garnish_slack={garnish['slack']}")

    # F8 — control point checked against a measurement; violation flips safe.
    e = res('formula.new "Controlled Process" kind=proc')["formula_id"]
    res(f'formula.step {e} text="react" dur=10 label=react')
    res(f'formula.control {e} param=temp op=">=" value=75 unit=C step=react ccp=yes')
    h_pre = res(f"formula.checkpoints {e}")                  # no measurement → pending
    res(f'formula.measure {e} param=temp value=78 step=react')
    h_ok = res(f"formula.checkpoints {e}")                   # 78 >= 75 → pass
    res(f'formula.measure {e} param=temp value=70 step=react')  # re-measured low → violation
    h_bad = res(f"formula.checkpoints {e}")
    f8 = (len(h_pre["pending"]) == 1 and h_pre["safe"] is False
          and h_ok["safe"] is True and h_ok["ccp_all_pass"] is True
          and h_bad["safe"] is False and len(h_bad["violations"]) == 1
          and h_bad["violations"][0]["actual"] == 70.0)
    record("F8 control", f8,
           f"pending→{h_pre['safe']} ok→{h_ok['safe']} violated→{h_bad['safe']} "
           f"viol={[(v['key'],v['actual']) for v in h_bad['violations']]}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
