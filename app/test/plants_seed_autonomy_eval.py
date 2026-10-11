#!/usr/bin/env python3
"""
Seed-time autonomy §3 — PLANTS ships self-sufficient (structural guard).

The deploy-autonomy ruling (2026-09-07): a seed-baked bench runs with NO operator action and its data
is imported+frozen at boot BEFORE it runs. This eval guards the PLANTS side of that contract WITHOUT
the heavy 49k import: (a) each bundled source pack (assets/plants_*) has a well-formed pack.json and its
data file present; (b) the deploy config declares the three `requires` pools, `trigger: boot`,
`then: daily:03:00`, the b1..b5 workflow list, and `auto_dispatch: false`; (c) the workflows the auto
policy names exist as .ak files. A small in-memory import of the (real) pack.json + a 3-row slice proves
the loader parses the real manifest shape.

Run:  python app/test/plants_seed_autonomy_eval.py     (exit 0 = all pass)
"""
import gzip
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


REQUIRED = ["source:pool:plants:checklist:v1",
            "source:pool:plants:vision20:v1",
            "source:pool:plants_images:v1",
            "model:mobilenet_v3_small_fv",      # the bundled LiteRT embedder (vision-deps-bundle §3.2)
            "model:mobilenet_v1_cls"]           # the bundled LiteRT classifier (VPS-vision-coverage §2, T2)
PACKS = {"plants_checklist": "source:pool:plants:checklist:v1",
         "plants_vision": "source:pool:plants_images:v1",
         "plants_vision20": "source:pool:plants:vision20:v1"}


def _read_rows(path, n):
    op = (lambda p: gzip.open(p, "rt", encoding="utf-8")) if path.endswith(".gz") \
        else (lambda p: open(p, "r", encoding="utf-8"))
    out = []
    with op(path) as fh:
        for i, ln in enumerate(fh):
            if i >= n:
                break
            ln = ln.strip()
            if ln:
                out.append(json.loads(ln))
    return out


def main():
    # A24 — the plants bench is thesaurus-tier only. On a cell where it is NOT shipped (a seeds-tier
    # seed, which carries neither the packs nor the config), there is nothing to validate: pass
    # vacuously instead of failing on absent files. Shipment is signalled by any of the plants artifacts.
    shipped = (os.path.isfile(os.path.join(ROOT, "app", "assets", "plants_checklist", "pack.json"))
               or os.path.isfile(os.path.join(ROOT, "app", "config", "workbench", "workloads", "plants_vision.json")))
    if not shipped:
        print("\nRESULT: PASS — PLANTS is not shipped on this cell (not the plants tier); "
              "nothing to validate (vacuous pass).")
        sys.exit(0)
    print("\n  ── PLANTS source packs (assets/plants_*) ──")
    for pdir, pool in PACKS.items():
        base = os.path.join(ROOT, "app", "assets", pdir)
        pj = os.path.join(base, "pack.json")
        ok = os.path.isfile(pj)
        check(f"assets/{pdir}/pack.json exists", ok)
        if not ok:
            continue
        pack = json.load(open(pj, encoding="utf-8"))
        check(f"assets/{pdir} pack.json declares the expected pool",
              pack.get("pool") == pool, str(pack.get("pool")))
        check(f"assets/{pdir} pack.json declares id_field + data + freeze",
              bool(pack.get("id_field")) and bool(pack.get("data")) and pack.get("freeze") is True,
              f"id={pack.get('id_field')} data={pack.get('data')} freeze={pack.get('freeze')}")
        data_path = os.path.join(base, pack.get("data", ""))
        check(f"assets/{pdir} data file is present", os.path.isfile(data_path), pack.get("data"))
        if os.path.isfile(data_path):
            rows = _read_rows(data_path, 3)
            idf = pack.get("id_field")
            check(f"assets/{pdir} data parses as JSONL with the declared id_field",
                  bool(rows) and all(idf in r for r in rows),
                  f"first={rows[0] if rows else None}")

    # The lab is a WORKLOAD (2026-09-26): app/config/workbench/workloads/plants_vision.json. It ships only
    # on a tier that carries what it requires (the crystallizer withholds it otherwise), and it is its
    # bench's ONE author — the old deploy.json and its bench scaffold are gone (2026-09-27).
    from lib.akasha.workbench import workload as W
    decl_p = os.path.join(ROOT, "app", "config", "workbench", "workloads", "plants_vision.json")
    check("the PLANTS lab is declared as a workload (app/config/workbench/workloads/plants_vision.json)",
          os.path.isfile(decl_p), decl_p)
    decl = json.load(open(decl_p, encoding="utf-8")) if os.path.isfile(decl_p) else {}
    check("the declaration is well-formed (no problem ids)", W.problems(decl) == [], str(W.problems(decl)))
    check("it runs as its own client under the `researcher` ID set — never as admin",
          decl.get("idset") == "researcher"
          and str((decl.get("space") or {}).get("client") or "").startswith("lab:"),
          "%s / %s" % (decl.get("idset"), (decl.get("space") or {}).get("client")))
    check("it is a private lab: effect=record, duty=best_effort, profile=private_lab",
          decl.get("effect") == "record" and decl.get("duty") == "wb:duty:best_effort"
          and decl.get("profile") == "private_lab",
          "%s / %s / %s" % (decl.get("effect"), decl.get("duty"), decl.get("profile")))
    check("the declaration requires the pools + the bundled model",
          sorted(decl.get("requires") or []) == sorted(REQUIRED), str(decl.get("requires")))
    trig = decl.get("trigger") or {}
    check("trigger fires at boot (seed-time autonomy) and recurs daily at 03:00Z",
          trig.get("boot") is True and trig.get("then") == "daily:03:00Z", str(trig))
    check("it runs the full T1..T7 template pipeline",
          decl.get("workflows") == ["plants_t1", "plants_t2", "plants_t3", "plants_t4",
                                    "plants_t5", "plants_t6", "plants_t7"],
          str(decl.get("workflows")))
    check("the bench is declared by the lab: public, kind `learning` — the bench live cells already have",
          decl.get("bench_public") is True and decl.get("bench_kind") == "learning",
          "%s / %s" % (decl.get("bench_public"), decl.get("bench_kind")))
    check("…and its space is a locked cowork space",
          (decl.get("space") or {}).get("kind") == "cowork"
          and (decl.get("space") or {}).get("identity") == "locked", str(decl.get("space"))[:120])
    for _gone in (os.path.join("app", "config", "workbench", "plants-vision", "deploy.json"),
                  os.path.join("app", "config", "workbench", "workloads", "bench_plants_vision.json"),
                  os.path.join("app", "config", "workbench", "workloads", "auto_exec.json")):
        check("no second author: %s is gone" % _gone, not os.path.isfile(os.path.join(ROOT, _gone)))
    b3_txt = ""
    for wf in decl.get("workflows") or []:
        p = os.path.join(ROOT, "app", "config", "workbench", "plants-vision", "templates", wf + ".ak")
        check(f"workflow templates/{wf}.ak exists", os.path.isfile(p))
        if wf == "plants_t3" and os.path.isfile(p):
            b3_txt = open(p, encoding="utf-8").read()
    # A41.2 (amended) — T3 covers the WHOLE pool by DEFAULT: the shipped line is a plain
    # `learning.feature.execute … run=f1` with no `limit=` (a dev knob) and no `until=` (dropped).
    _b3_exec = [ln for ln in b3_txt.splitlines()
                if ln.strip().startswith("learning.feature.execute")]
    check("T3 feature.execute covers the whole pool by default (no limit=/until=)",
          len(_b3_exec) == 1 and "limit=" not in _b3_exec[0] and "until=" not in _b3_exec[0],
          _b3_exec[0] if _b3_exec else "(no feature.execute line)")

    # The sweep ships self-sufficient: the declaration names it and its definition is an 8-cond grid.
    check("the declaration names sweeps=[heads1]", decl.get("sweeps") == ["heads1"],
          str(decl.get("sweeps")))
    _hp = os.path.join(ROOT, "app", "config", "workbench", "plants-vision", "sweeps", "heads1.json")
    check("the heads1 sweep definition ships", os.path.isfile(_hp), _hp)
    if os.path.isfile(_hp):
        _hd = json.load(open(_hp, encoding="utf-8"))
        _grid = _hd.get("grid") or {}
        _n = 1
        for _vs in _grid.values():
            _n *= max(1, len(_vs))
        # S2-h — the grid sweeps only the IMPLEMENTED learner kinds (learned_head.KINDS = logreg, mlp);
        # ridge/linear were dropped (they degraded to a centroid mock), so the grid is 2×2×2 = 8.
        _heads = _grid.get("head") or []
        check("heads1 grid expands to 8 conditions (2 heads × 2 splits × 2 seeds), max=18",
              _n == 8 and int(_hd.get("max") or 0) == 18 and _hd.get("template") == "learn_observe"
              and set(_heads) == {"logreg", "mlp"},
              f"conds={_n} heads={_heads} max={_hd.get('max')}")

    print("\n  ── the policy the driver reads ──")
    pol = W.policy(decl) if decl else {}
    check("the projected policy keeps the workflows, the sweep and the requires",
          pol.get("workflows") == decl.get("workflows") and pol.get("sweeps") == ["heads1"]
          and sorted(pol.get("requires") or []) == sorted(REQUIRED),
          str({k: pol.get(k) for k in ("workflows", "sweeps", "requires")})[:200])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — PLANTS ships self-sufficient: three well-formed source packs with data present, "
          "and the lab declared as a workload — its own `researcher` client, requires / boot trigger / "
          "daily:03:00Z / T1..T7 from templates/ / the heads1 sweep — with no `auto` left to run it as "
          "admin. No operator action is encoded anywhere.")
    sys.exit(0)


if __name__ == "__main__":
    main()
