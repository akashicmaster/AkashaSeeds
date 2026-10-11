#!/usr/bin/env python3
"""
A workload's client reaches its own places and the resources it requires — and nothing else.

Directive 2026-10-02 §5 (the first two lines of C2). The application could not declare a feed or a
precompute as a workload:
  5.1  `idset: "telemetry"` was not assignable — the row said `on: feeds`, and a declaration may
       name only an `assigned` row. The row is `assigned` now; `system.telemetry` holds it
       `on feeds`, a NAMED target the gate resolves to the source feeds, and a cell's bare line is
       rewritten to that at first load.
  5.2  a client had no reach on the pools its declaration `requires`. The `consumer` row (read ·
       run, `facts: false`) and one provisioned line per `source:pool:` / `model:` requirement.

On a real cell provisioned from the real declarations plus two of the eval's own (a feed with
`idset: "telemetry"` and a private lab requiring two pools), through the real provisioning and the
real gate, this eval holds:

  1. the feed provisions; its client holds `telemetry` on exactly its two places; it RECORDS there
     through a real dispatch (`wf.new bench=…`, the target gate) and is refused on another
     workload's bench; its run reaches its own place;
  2. the lab gets one `consumer` line per required pool (two), none for its `set:` entry; `read`
     and `run` on each pool are admitted; `record` on a pool is refused `out_of_scope`; its main
     ID set stays on its own places;
  3. removing a requirement and re-provisioning removes that line, and only that one;
  4. `system.telemetry`'s reach is unchanged: the same gate answers, for a fixed list of actions
     and targets, under the table before §5 + its bare line as under the shipped table + the
     shipped `on feeds` line (no table upgrade and no line adoption: the purge order §2);
  5. a resource row is never a client's main ID set (`consumer` is not assignable) and the shipped
     table/seed say what §5.1 says.

Run:  python app/test/workload_resource_access_eval.py     (exit 0 = all pass)
"""
import copy
import json
import logging
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "test"))
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, rec):
        self.lines.append(rec.getMessage())


POOL_A, POOL_B = "source:pool:eval_res_a:v1", "source:pool:eval_res_b:v1"

FEED = {
    "_file": "eval_feed.json", "profile": "telemetry_feed",
    "bench": "wb:eval_telemetry", "bench_kind": "record",
    "workflow": "eval_feed_iss", "society": "eval_telemetry/eval_feed_iss",
    "trigger": {"boot": True, "then": "every:300s"}, "duty": "wb:duty:best_effort",
    "effect": "record", "appetite": {"llm_calls_per_run": 0, "weight": 0.1},
    "budget": {"per_day": 300, "max_wall_s": 60, "max_steps": 5}, "pins": {},
    "idset": "telemetry", "space": {"client": "feed:eval_iss"}, "requires": [],
}
LAB = {
    "_file": "eval_lab.json", "profile": "private_lab",
    "bench": "wb:eval_lab", "bench_kind": "record",
    "workflow": "eval_precompute", "society": "eval_lab/eval_precompute",
    "trigger": {"boot": True, "then": "daily:03:00Z"}, "duty": "wb:duty:best_effort",
    "effect": "record", "appetite": {"llm_calls_per_run": 0, "weight": 0.1},
    "budget": {"per_day": 4, "max_wall_s": 600, "max_steps": 20}, "pins": {},
    "idset": "researcher", "space": {"client": "lab:eval_precompute"},
    "requires": [POOL_A, POOL_B, "set:eval_res_names"],
}


def _old_table_answers(G, probes):
    """The gate's answers for `system.telemetry` under the table as it was before §5.1: the row
    `on: feeds` with a BARE line. Built in a temp dir from the shipped files, edited back."""
    tmp = tempfile.mkdtemp(prefix="res_old_")
    try:
        doc = json.load(open(G.SEED_IDSETS_PATH, encoding="utf-8"))
        for r in doc["idsets"]:
            if r["role"] == "telemetry":
                r["on"], r["groups"] = "feeds", "source"
        ip = os.path.join(tmp, "idsets.json")
        json.dump(doc, open(ip, "w", encoding="utf-8"))
        ap = os.path.join(tmp, "assign.ak")
        open(ap, "w", encoding="utf-8").write("admin admin\nanonymous guest\n"
                                              "system.telemetry telemetry\n")
        # the old gate read `on: feeds` as the row's own word; that branch is the NAMED target
        # now, which `_reaches` consults for a row word too — so this is the old semantics.
        G.load(ip, ap)
        return [G.gate("system.telemetry", a, t) for a, t in probes], \
            sorted(G.scopes_for("system.telemetry"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 78)
    print("A workload's client reaches its own places and its required resources — nothing else")
    print("=" * 78)
    import workload_conformance_eval as C
    from lib.akasha.api import gate as G
    from lib.akasha.workbench import provision, workload as W, workload_provision as WP

    # ── 4 first, on files of its own, before the cell binds the gate ─────────────────────────
    print("\n  ── 4. `system.telemetry` keeps exactly today's reach ──")
    probes = [(a, t) for a in ("read", "run", "record", "annotate", "say", "publish", "admin")
              for t in (None, "feed:iss", "feed", "set:source:iss", "source:pool:x:v1",
                        "source:item:x:1", "grp_a/main", "wb:studio_ai", "universal",
                        "feeds_other", "set:wl:declared")]
    old_ans, old_scopes = _old_table_answers(G, probes)
    # the shipped table and the shipped line (a fresh cell's — there is no adoption of an older
    # bare line, and no table upgrade: the purge order §2)
    tmp = tempfile.mkdtemp(prefix="res_new_")
    ap = os.path.join(tmp, "assign.ak")
    shutil.copyfile(G.SEED_ASSIGN_PATH, ap)
    G.load(G.SEED_IDSETS_PATH, ap)
    check("the shipped line is `system.telemetry telemetry on feeds`",
          "\nsystem.telemetry telemetry on feeds" in open(ap, encoding="utf-8").read())
    new_ans = [G.gate("system.telemetry", a, t) for a, t in probes]
    diff = [(probes[i], old_ans[i], new_ans[i]) for i in range(len(probes)) if old_ans[i] != new_ans[i]]
    check("the same gate answers for %d (action, target) probes, the table before §5 + its bare "
          "line vs the shipped table + the shipped line" % len(probes), not diff, str(diff[:4]))
    check("…and it still records into a feed and is refused a group (the probe is not vacuous)",
          G.gate("system.telemetry", "record", "feed:iss")[0]
          and G.gate("system.telemetry", "record", "grp_a/main") == (False, G.R_TARGET))
    check("…and the same session scopes (a named target opens no group engine)",
          sorted(G.scopes_for("system.telemetry")) == old_scopes,
          str(sorted(set(G.scopes_for("system.telemetry")) ^ set(old_scopes))))
    shutil.rmtree(tmp, ignore_errors=True)

    # ── the cell ──────────────────────────────────────────────────────────────────────────────
    cap = _Cap()
    logging.getLogger("Akasha.Kernel").addHandler(cap)
    k = C._cell(cap)
    real = W.declarations(k)
    tpl = next(p for _b, p in (t for d in real for t in WP.templates_of(d)) if p)
    _real_tpls = WP.templates_of
    WP.templates_of = lambda decl: ([(W.branch_of(decl), tpl)] if decl.get("_file", "").startswith("eval_")
                                    else _real_tpls(decl))
    feed, lab = copy.deepcopy(FEED), copy.deepcopy(LAB)
    for dd in (feed, lab):
        check("(the eval's %s declaration is valid: %s)" % (dd["_file"], W.problems(dd) or "ok"),
              not W.problems(dd))
    k._workload_decl_cache = list(real) + [feed, lab]
    reps = {r.get("workload"): r for r in provision.provision_workloads(k)}
    # the boot's two fact reconciles, which the driver's `run` question reads (step 4)
    provision.reconcile_source_ready(k)
    provision.reconcile_headroom(k)

    def d(who, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": who, "data": data}, "id": "x"}, "internal")

    print("\n  ── 1. a declared feed with `idset: \"telemetry\"` ──")
    fkey, fcli = W.key(feed), W.client_of(feed)
    frep = reps.get(fkey) or {}
    check("it provisions (status provisioned, no problem)",
          frep.get("status") == "provisioned" and not frep.get("problems"),
          "%s %s" % (frep.get("status"), (frep.get("problems") or frep.get("reason"))))
    fplaces = W.client_places(feed)
    held = sorted((l["idset"], l["on"]) for l in G.lines_for(fcli))
    # (its account's IAM lines — `member` on its group, `resident` — come with every client
    # `user.add` creates, programmes included; what the declaration grants is the `telemetry` one)
    tel = sorted(on for i, on in held if i == "telemetry")
    check("its client holds `telemetry` on exactly its two places, and no `consumer` line",
          tel == sorted(fplaces) and not [1 for i, _ in held if i == "consumer"], str(held))
    ok_rec = [G.gate(fcli, "record", p) for p in fplaces]
    check("it may record on both of its places", all(o for o, _ in ok_rec), str(ok_rec))
    r_own = d(fcli, "wf.new", {"bench": W.bench_slug(feed)})
    check("…through a real dispatch: `wf.new bench=<its bench>` as its client is admitted",
          "error" not in r_own, str(r_own.get("error"))[:140])
    r_other = d(fcli, "wf.new", {"bench": "studio_ai"})
    check("…and `wf.new bench=studio_ai` (another workload's bench) is refused out_of_scope",
          "error" in r_other and G.R_TARGET in str(r_other["error"]), str(r_other)[:160])
    check("the gate says the same of the other bench",
          G.gate(fcli, "record", "wb:studio_ai") == (False, G.R_TARGET))
    check("its run reaches its own place (the driver's question: run on the key, at its place)",
          G.gate(fcli, "run", fkey, place=fplaces[0]) == (True, G.OK),
          str(G.gate(fcli, "run", fkey, place=fplaces[0])))
    check("…and it does not reach a feed it was not given (a line is not a class)",
          G.gate(fcli, "record", "feed:somebody_else") == (False, G.R_TARGET))

    print("\n  ── 2. a private lab requiring two pools ──")
    lcli = W.client_of(lab)
    lrep = reps.get(W.key(lab)) or {}
    check("it provisions", lrep.get("status") == "provisioned", str(lrep.get("problems"))[:120])
    cons = sorted(l["on"] for l in G.lines_for(lcli) if l["idset"] == "consumer")
    check("two `consumer` lines, one per required pool — none for its `set:` entry",
          cons == sorted([POOL_A, POOL_B]), str(cons))
    for pool in (POOL_A, POOL_B):
        check("read on %s is admitted" % pool, G.gate(lcli, "read", pool) == (True, G.OK),
              str(G.gate(lcli, "read", pool)))
        check("run on %s is admitted (a job over an input: no workload facts asked)" % pool,
              G.gate(lcli, "run", pool) == (True, G.OK), str(G.gate(lcli, "run", pool)))
        check("record on %s is refused out_of_scope" % pool,
              G.gate(lcli, "record", pool) == (False, G.R_TARGET), str(G.gate(lcli, "record", pool)))
    main_lines = sorted(l["on"] for l in G.lines_for(lcli) if l["idset"] == "researcher")
    check("its main ID set (`researcher`) stays on its own two places only",
          main_lines == sorted(W.client_places(lab)), str(main_lines))
    check("a pool it does not require is out of reach", G.gate(lcli, "read", "source:pool:other:v1")
          == (False, G.R_TARGET))

    print("\n  ── 3. removing a requirement removes its line ──")
    lab2 = copy.deepcopy(lab)
    lab2["requires"] = [POOL_A, "set:eval_res_names"]
    k._workload_decl_cache = list(real) + [feed, lab2]
    provision.provision_workloads(k)
    cons2 = sorted(l["on"] for l in G.lines_for(lcli) if l["idset"] == "consumer")
    check("re-provisioned without %s: one line left, for %s" % (POOL_B, POOL_A),
          cons2 == [POOL_A], str(cons2))
    check("…and run on the dropped pool is refused now",
          G.gate(lcli, "run", POOL_B) == (False, G.R_TARGET))
    check("…and the client's other lines are untouched",
          sorted(l["on"] for l in G.lines_for(lcli) if l["idset"] == "researcher") == main_lines)

    print("\n  ── 6. (§6.1) a workload may require EVERY frozen pool ──")
    from lib.akasha.source import bootstrap as SB

    def dd(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "s"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}
    src = (dd("source.register", {"provider": "Eval", "collection": "res", "name": "evres"}) or {}).get("source")
    dd("source.acquire", {"source": src, "rule": "two plates",
                          "records": [{"id": "r1", "title": "one", "url": "https://x/1.jpg"},
                                      {"id": "r2", "title": "two", "url": "https://x/2.jpg"}]})
    pools = []
    for nm in ("evres_a", "evres_b"):
        pc = dd("source.pool.create", {"name": nm, "source": src, "rule": "all", "version": "v1"})
        pools.append(pc.get("pool"))
        for it in ("source:item:evres:r1", "source:item:evres:r2"):
            dd("source.pool.add", {"pool": pc.get("pool"), "id": it})
    fa = dd("source.pool.freeze", {"pool": pools[0]})
    check("(two pools exist; the first is frozen through the real op)",
          all(pools) and fa.get("status") == "FROZEN", "%s %s" % (pools, str(fa)[:80]))
    check("the source engine states the freeze in `set:source:pool:frozen`",
          pools[0] in SB.frozen_pools(k) and pools[1] not in SB.frozen_pools(k), str(SB.frozen_pools(k)))
    pre = dict(copy.deepcopy(LAB), _file="eval_pre.json", workflow="eval_pre",
               society="eval_lab/eval_pre", space={"client": "lab:eval_pre"},
               requires=["set:source:pool:frozen"])
    check("(the declaration requiring the Set is valid: %s)" % (W.problems(pre) or "ok"), not W.problems(pre))
    k._workload_decl_cache = list(real) + [feed, lab2, pre]
    provision.provision_workloads(k)
    pcli = W.client_of(pre)

    def plines():
        return sorted(l["on"] for l in G.lines_for(pcli) if l["idset"] == "consumer")
    check("one `consumer` line per frozen pool — exactly the Set's members",
          plines() == sorted(SB.frozen_pools(k)) and pools[0] in plines() and pools[1] not in plines(),
          "lines=%s set=%s" % (plines(), SB.frozen_pools(k)))
    fb = dd("source.pool.freeze", {"pool": pools[1]})
    check("freezing a new pool adds its line — at the freeze, with no reboot and no reprovision",
          fb.get("status") == "FROZEN" and pools[1] in plines(), str(plines()))
    for pl in pools:
        check("run on %s is admitted; record on it is refused out_of_scope" % pl,
              G.gate(pcli, "run", pl) == (True, G.OK)
              and G.gate(pcli, "record", pl) == (False, G.R_TARGET),
              "%s %s" % (G.gate(pcli, "run", pl), G.gate(pcli, "record", pl)))
    check("the lab requiring two NAMED pools gained nothing from the Set (it names its own)",
          sorted(l["on"] for l in G.lines_for(lcli) if l["idset"] == "consumer") == [POOL_A])
    SB.state_pool_frozen(k, pools[1], False)          # a pool that leaves the Set (re-opened/deleted)
    provision.reconcile_workload_resources(k, [pre])
    check("a pool that leaves the Set loses its line at the next reconcile",
          pools[1] not in plines() and pools[0] in plines(), str(plines()))
    SB.state_pool_frozen(k, pools[1], True)
    SB.reconcile_pool_frozen(k)
    check("the boot reconcile states the Set from the pools as they are",
          set(pools) <= set(SB.frozen_pools(k)), str(SB.frozen_pools(k)))

    print("\n  ── 7. (§6.4) the precompute's writes, each in its proper place ──")
    # THE APPLICATION'S DECLARATIONS, applied in memory (the eval's own; the note names the lines):
    #   labo.new / labo.bind  implements workload.labo.new / workload.labo.bind
    #   vlab.run.new          target=bench, target_kind=bench, target_required
    #   analysis.precompute   target=bench, target_kind=bench, target_required (a manifest op)
    from lib.akasha.concepts import registry as RG
    _attrs = k.api.op_attrs
    _saved_attrs = {m: dict(_attrs.get(m) or {}) for m in ("labo.new", "labo.bind", "analysis.precompute")}
    _attrs.setdefault("labo.new", {})["implements"] = W.LABO_NEW_POINT
    _attrs.setdefault("labo.bind", {})["implements"] = W.LABO_BIND_POINT
    _attrs.setdefault("analysis.precompute", {}).update(
        {"target": "bench", "target_kind": "bench", "target_required": True})
    _reg = RG.get_active()
    _reg._method_targets["vlab.run.new"] = "bench"
    _reg._method_target_attrs["vlab.run.new"] = {"target": "bench", "target_kind": "bench",
                                                 "target_required": True}

    pc_decl = dict(copy.deepcopy(pre), _file="eval_pc.json", workflow="eval_pc", society="eval_pc/eval_pc",
                   bench="wb:eval_pc", bench_public=True, space={"client": "lab:eval_pc"},
                   labo={"name": "src_{pool}", "about": "auto — text analysis", "scope": "public"})
    check("(the precompute declaration with `labo` is valid: %s)" % (W.problems(pc_decl) or "ok"),
          not W.problems(pc_decl))
    bad_lab = dict(copy.deepcopy(pc_decl), labo={"name": "one_for_all"})
    check("a `labo.name` without `{pool}` on a multi-pool workload is refused (`problems: labo`)",
          "labo" in W.problems(bad_lab), str(W.problems(bad_lab)))
    k._workload_decl_cache = list(real) + [feed, lab2, pre, pc_decl]
    provision.provision_workloads(k)

    def lab_bound(pool):
        info = dd("labo.info", {"name": W.labo_name(pc_decl, pool)}) or {}
        return "__error__" not in info and pool in json.dumps(info)
    frozen_now = SB.frozen_pools(k)
    check("provisioning ensured one labo per frozen pool and bound the pool (no op of its own did)",
          frozen_now and all(lab_bound(p) for p in frozen_now),
          str({p: lab_bound(p) for p in frozen_now}))
    pc_new = (dd("source.pool.create", {"name": "evres_c", "source": src, "rule": "all",
                                        "version": "v1"}) or {}).get("pool")
    dd("source.pool.add", {"pool": pc_new, "id": "source:item:evres:r1"})
    check("(a third pool, not yet frozen, has no labo)", not lab_bound(pc_new))
    dd("source.pool.freeze", {"pool": pc_new})
    check("freezing a new pool adds its labo and binding — at the freeze",
          lab_bound(pc_new), W.labo_name(pc_decl, pc_new))

    # the by-status tally, maintained by the writes that change it — no freeze call
    dd("source.acquire", {"source": src, "rule": "one with no locator",
                          "records": [{"id": "r3", "title": "three"}]})        # METADATA_ONLY
    tp = (dd("source.pool.create", {"name": "evres_tally", "source": src, "rule": "all",
                                    "version": "v1"}) or {}).get("pool")
    for it in ("source:item:evres:r1", "source:item:evres:r3"):
        dd("source.pool.add", {"pool": tp, "id": it})
    st0 = dd("source.status", {"pool": tp}) or {}
    check("an OPEN pool's tally is live as members are added (no freeze): ACQUIRED=1 METADATA_ONLY=1",
          (st0.get("by_status") or {}).get("ACQUIRED") == 1
          and (st0.get("by_status") or {}).get("METADATA_ONLY") == 1 and not st0.get("frozen"),
          str(st0.get("by_status")))
    dd("source.resolve", {"id": "source:item:evres:r3", "locator": "https://x/3.jpg"})
    st1 = dd("source.status", {"pool": tp}) or {}
    check("a status change moves the count in the same write (ACQUIRED=2, METADATA_ONLY=0), still OPEN",
          (st1.get("by_status") or {}).get("ACQUIRED") == 2
          and (st1.get("by_status") or {}).get("METADATA_ONLY") == 0 and not st1.get("frozen"),
          str(st1.get("by_status")))
    fz = dd("source.pool.freeze", {"pool": tp}) or {}
    check("freezing reads the live tally (no recount; the same counts)",
          (fz.get("by_status") or {}).get("ACQUIRED") == 2, str(fz.get("by_status")))

    # the writes land on the workload's own (public) bench; aimed anywhere else they are refused
    pcli = W.client_of(pc_decl)

    def dc(who, method, data, trust="internal"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": who, "data": data}, "id": "c"}, trust)
        return r
    own = W.bench_slug(pc_decl)
    run_ok = dc(pcli, "vlab.run.new", {"pool": frozen_now[0], "observers": "color", "run": "eval_pc_run",
                                       "bench": own, "purpose": "precompute"})
    check("vlab.run.new bench=<its own public bench> as its client is admitted",
          "error" not in run_ok, str(run_ok.get("error"))[:160])
    g = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                    "params": {"data": {}}, "id": "g"}, "network")
    gt = ((g or {}).get("result") or {}).get("binding_key") or ((g or {}).get("result") or {}).get("session_token")
    gr = k.dispatch({"jsonrpc": "2.0", "method": "vlab.run.info",
                     "params": {"session_token": gt, "data": {"run": "eval_pc_run"}}, "id": "gr"}, "network")
    check("…and a GUEST reads the run it wrote (a public bench is the nucleus)",
          gt and "error" not in gr and "eval_pc_run" in json.dumps(gr.get("result") or {}),
          str(gr)[:160])
    run_bad = dc(pcli, "vlab.run.new", {"pool": frozen_now[0], "observers": "color", "run": "eval_pc_bad",
                                        "bench": "studio_ai", "purpose": "precompute"})
    check("vlab.run.new aimed at another bench is refused out_of_scope",
          "error" in run_bad and G.R_TARGET in str(run_bad["error"]), str(run_bad)[:160])
    run_none = dc(pcli, "vlab.run.new", {"pool": frozen_now[0], "observers": "color", "run": "eval_pc_none",
                                         "purpose": "precompute"})
    check("…and with NO bench (the old fixed-namespace write) it is refused, naming the param",
          "error" in run_none and "no bench=" in str(run_none["error"]), str(run_none)[:160])
    pj_ok = dc(pcli, "analysis.precompute", {"bench": own})
    check("the projection writer (a MANIFEST op) passes the gate on its own bench — it reaches the "
          "op's own argument check (-32602), never a gate refusal (-32001)",
          "error" in pj_ok and pj_ok["error"].get("code") == -32602, str(pj_ok)[:160])
    pj_bad = dc(pcli, "analysis.precompute", {"bench": "studio_ai", "labo": "x", "input": frozen_now[0]})
    check("…and aimed at another bench it is refused out_of_scope before it runs",
          "error" in pj_bad and G.R_TARGET in str(pj_bad["error"]), str(pj_bad)[:160])

    print("\n  ── 7b. (3 October, decision 2) registered labs win — a SHADOW labo only for an unbound pool ──")
    # The application's half, written here as the eval's own implementers (the note names the lines):
    #   `workload.labo.bind` accepts `origin` and records it on the binding;
    #   `workload.labo.of`   {pool} → {"labos": [{"labo", "origin"}]}, read from the pool's links.
    from lib.akasha import api as _api
    from lib.akasha import kernel_methods as _KM
    from app.concepts import labo as _LB
    _origin = {}                                   # (labo id, pool) → origin, as the binding recorded it

    def _ev_bind(kernel, rid, data):
        d = dict(data or {})
        origin = str(d.pop("origin", "") or "registered")
        r = kernel.dispatch({"jsonrpc": "2.0", "method": "labo.bind",
                             "params": {"session_token": "admin", "data": d}, "id": rid}, "internal")
        if "error" not in r:
            _origin[((r.get("result") or {}).get("labo"), d.get("pool"))] = origin
        return r

    def _ev_of(kernel, rid, data, session):
        pool = str((data or {}).get("pool") or "")
        lb = _api.concept_class(kernel, "labo")(session)
        out = [{"labo": a, "origin": _origin.get((a, pool), "")}
               for a, r in lb._links(pool, _LB.R_IN_LABO)]
        return {"jsonrpc": "2.0", "id": rid, "result": {"labos": out}}
    k.api.ops.register("eval.labo.bind", _ev_bind, stage="pre", access="record", source="eval")
    k.api.ops.register("eval.labo.of", _ev_of, stage="pre", access="read", source="eval")
    _KM.METHOD_TO_ACTION["eval.labo.bind"] = "record"
    _KM.METHOD_TO_ACTION["eval.labo.of"] = "read"
    _attrs["labo.bind"].pop("implements", None)
    _attrs["eval.labo.bind"] = {"implements": W.LABO_BIND_POINT}
    # the application implements `workload.labo.of` now; take its declaration off for 7b (whichever
    # op holds it — the eval names the point, not the method) so "no implementer" can be reproduced,
    # and put it back after
    _of_held = {m: dict(a) for m, a in _attrs.items() if a.get("implements") == W.LABO_OF_POINT}
    for m in _of_held:
        _attrs[m].pop("implements", None)

    def mkpool(nm):
        p = (dd("source.pool.create", {"name": nm, "source": src, "rule": "all", "version": "v1"})
             or {}).get("pool")
        dd("source.pool.add", {"pool": p, "id": "source:item:evres:r1"})
        return p
    p_reg, p_free = mkpool("evres_reg"), mkpool("evres_free")
    dd("labo.new", {"name": "eval_registered", "about": "a hand-registered lab", "scope": "public"})
    rb = k.dispatch({"jsonrpc": "2.0", "method": "eval.labo.bind", "params": {"session_token": "admin",
                     "data": {"name": "eval_registered", "pool": p_reg, "origin": "registered"}},
                     "id": "rb"}, "internal")
    check("(the registered lab is bound to its pool through the bind point, origin registered)",
          "error" not in rb and _origin.get(("labo:eval_registered", p_reg)) == "registered", str(rb)[:160])
    sh_decl = dict(copy.deepcopy(pre), _file="eval_sh.json", workflow="eval_sh", society="eval_sh/eval_sh",
                   bench="wb:eval_sh", bench_public=True, space={"client": "lab:eval_sh"},
                   requires=[p_reg, p_free],
                   labo={"name": "sh_{pool}", "about": "auto — shadow", "when": "unbound"})
    check("(`labo.when: unbound` is a valid declaration: %s)" % (W.problems(sh_decl) or "ok"),
          not W.problems(sh_decl))
    bad_when = dict(copy.deepcopy(sh_decl), labo={"name": "sh_{pool}", "when": "sometimes"})
    check("an unknown `labo.when` is refused (`problems: labo`)", "labo" in W.problems(bad_when),
          str(W.problems(bad_when)))

    def shadow_of(pool):
        info = dd("labo.info", {"name": W.labo_name(sh_decl, pool)}) or {}
        return "__error__" not in info and pool in json.dumps(info)
    k._workload_decl_cache = list(real) + [feed, lab2, pre, pc_decl, sh_decl]
    provision.provision_workloads(k)
    check("with NO implementer of `workload.labo.of` no shadow is made — nobody can say the pool is "
          "unbound, so the safe answer is none", not shadow_of(p_reg) and not shadow_of(p_free))
    _attrs["eval.labo.of"] = {"implements": W.LABO_OF_POINT}
    provision.provision_workloads(k)
    check("a pool bound to a REGISTERED lab gets no shadow labo",
          not shadow_of(p_reg), W.labo_name(sh_decl, p_reg))
    check("an UNBOUND pool gets its shadow labo, bound",
          shadow_of(p_free), W.labo_name(sh_decl, p_free))
    sh_free = "labo:%s" % W.labo_name(sh_decl, p_free)
    check("…and the binding records `origin: shadow` (the platform passes it through the bind point)",
          _origin.get((sh_free, p_free)) == "shadow", str(_origin))
    provision.provision_workloads(k)
    held = [h["labo"] for h in ((_ev_of(k, "x", {"pool": p_free}, k.manager.get_session("admin"))
                                 .get("result") or {}).get("labos") or [])]
    check("a re-provision keeps the pool's own shadow (its own shadow is not a registered lab) and "
          "adds nothing", held == [sh_free], str(held))
    check("the registered pool is still held by its registered lab alone",
          [h["labo"] for h in ((_ev_of(k, "x", {"pool": p_reg}, k.manager.get_session("admin"))
                                .get("result") or {}).get("labos") or [])] == ["labo:eval_registered"])
    for m in ("eval.labo.bind", "eval.labo.of"):
        _attrs.pop(m, None)
        _KM.METHOD_TO_ACTION.pop(m, None)
    for m, a in _of_held.items():
        _attrs[m] = a

    print("\n  ── 7c. (purge §2) the declared pass grounds the bench through `bench.bind_pool` ──")
    _bp_calls = []

    def _bp(kernel, rid, data):
        _bp_calls.append((data.get("name"), data.get("pool")))
        return {"jsonrpc": "2.0", "id": rid, "result": {"bound": True}}
    _bp_held = {m: dict(a) for m, a in _attrs.items() if a.get("implements") == provision.BIND_POOL_POINT}
    for m in _bp_held:
        _attrs[m].pop("implements", None)
    k.api.ops.register("eval.bench.bind_pool", _bp, stage="pre", access="record", source="eval")
    _KM.METHOD_TO_ACTION["eval.bench.bind_pool"] = "record"
    _attrs["eval.bench.bind_pool"] = {"implements": provision.BIND_POOL_POINT}
    bp_decl = dict(copy.deepcopy(pc_decl), _file="eval_bp.json", workflow="eval_bp",
                   society="eval_bp/eval_bp", bench="wb:eval_bp", space={"client": "lab:eval_bp"},
                   requires=list(frozen_now[:1]) + ["model:eval_bp_model", "set:eval_bp_set"])
    bp_decl.pop("labo", None)
    provision.reconcile_workload_resources(k, [bp_decl])
    check("the implementer is called once per required SOURCE POOL, with the bench's slug",
          _bp_calls == [(W.bench_slug(bp_decl), frozen_now[0])], str(_bp_calls))
    check("…and never with a `model:` or a `set:` requirement",
          not [c for c in _bp_calls if not str(c[1]).startswith("source:pool:")], str(_bp_calls))
    _attrs.pop("eval.bench.bind_pool", None)
    k.api.ops._entries.pop("eval.bench.bind_pool", None)
    _KM.METHOD_TO_ACTION.pop("eval.bench.bind_pool", None)
    _bp_calls.clear()
    provision.reconcile_workload_resources(k, [bp_decl])
    check("with no implementer nothing is bound (one `pools_unbound` line instead)", not _bp_calls)
    for m, a in _bp_held.items():
        _attrs[m] = a

    for m, a in _saved_attrs.items():
        _attrs[m] = a
    _reg._method_targets.pop("vlab.run.new", None)
    _reg._method_target_attrs.pop("vlab.run.new", None)

    print("\n  ── 5. the table says it ──")
    check("`telemetry` is assignable now; `consumer` is not (a resource row is never a main ID set)",
          "telemetry" in W.assignable_idsets() and "consumer" not in W.assignable_idsets(),
          str(W.assignable_idsets()))
    lab_bad = dict(copy.deepcopy(LAB), idset="consumer")
    check("…so a declaration naming `idset: consumer` is refused (`problems: idset`)",
          "idset" in W.problems(lab_bad), str(W.problems(lab_bad)))
    seed = open(G.SEED_ASSIGN_PATH, encoding="utf-8").read()
    check("the shipped bootstrap line is `system.telemetry telemetry on feeds`",
          "\nsystem.telemetry telemetry on feeds" in seed)
    rows = G.idsets()
    check("the `consumer` row: read · run, on assigned, groups none, facts false",
          rows.get("consumer", {}).get("may") == ("read", "run")
          and rows["consumer"]["on"] == "assigned" and rows["consumer"]["groups"] == "none"
          and rows["consumer"]["facts"] is False, str(rows.get("consumer")))

    WP.templates_of = _real_tpls
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a feed declares `idset: telemetry` and reaches only its own places; a lab "
          "reads and runs on the pools it requires and never records on them; a dropped "
          "requirement drops its line; system.telemetry's reach is unchanged.")
    sys.exit(0)


if __name__ == "__main__":
    main()
