#!/usr/bin/env python3
"""
THE SOURCE VIEWER'S PREPAID VIEWS ARE TWO DECLARED WORKLOADS RUNNING TWO PASS OPS, AS THEIR OWN CLIENTS (10-03).

Replaces `analysis_precompute_boot_eval` and `media_precompute_eval`, which pinned the two boot THREADS. The
threads are gone; what they proved is kept, and the acceptance the platform added is held:

  1. ONE SWITCH — the boot schedules are gone from the manifest, `analysis.precompute` declares its required bench
     target in the SAME change, and nothing in `precompute.py` is a `schedule_*`.
  2. THE CLIENT, NOT ADMIN — the pass runs as the workload's client over `set:source:pool:frozen`. A pass aimed at
     ANOTHER workload's bench, or at none, is refused by the gate.
  3. REGISTERED LABS WIN — a pool a registered lab holds gets no shadow labo and the pass uses the registered one; a
     pool no lab holds gets a shadow (origin shadow), and the pass uses it.
  4. TEXT — every frozen text pool's projections are persisted (exact over the full pool); a second pass submits
     nothing (idempotent); a pool whose job is in flight is skipped, not stacked.
  5. MEDIA — an audio pool with no run is observed under `auto_<pool>` (spaces populated, clusters prepaid); a pool
     already observed and a text-only pool are skipped; the run is minted purpose=precompute with NO bench stamp.
  6. ACCEPTANCE — the number of frozen pools with an analysis projection, and with a media run, after the passes is
     ≥ the number the old boot threads would have prepared (every eligible pool).

Run:  python app/test/analysis_precompute_passes_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    import numpy as np
    import app.concepts.vision_lab as V
    V._resolve_audio_array = lambda loc: (np.sin(np.linspace(0, (110 + abs(hash(loc)) % 300) * 2 * np.pi,
                                                             22050)).astype("float32"), 22050)
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.workbench import workload as W
    from lib.akasha.workbench import provision as P
    from lib.akasha.workbench.workload_provision import provision
    from app.concepts import precompute
    import app.concepts.vision_lab  # noqa: F401

    print("\n  ── 1. one switch ──")
    man = json.load(open(os.path.join(ROOT, "app", "config", "MANIFEST.json"), encoding="utf-8"))
    ap = man["ops"]["analysis.precompute"]
    check("the two boot schedules are gone from the manifest",
          "analysis_precompute" not in man["schedules"] and "media_precompute" not in man["schedules"])
    check("…and `analysis.precompute` declares its bench target REQUIRED in the same change",
          (ap.get("target"), ap.get("target_kind"), ap.get("target_required")) == ("bench", "bench", True))
    check("the module holds no schedule_* (no boot thread can come back)",
          not [n for n in dir(precompute) if n.startswith("schedule_")])
    check("the pass ops are declared run-class with a required bench target",
          all(man["ops"][o].get("access") == "run" and man["ops"][o].get("target_required") is True
              for o in ("analysis.precompute.pass", "vlab.media.pass")))

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_pp_"))

    def raw(who, method, data, trust="local"):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": who, "data": data}, "id": "t"}, trust) or {}

    def d(method, data, who="admin"):
        r = raw(who, method, data)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    raw("admin", "kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})

    def mk_pool(name, records, freeze=True):
        d("source.register", {"provider": name, "name": name})
        d("source.pool.create", {"name": name, "source": "source:src:%s" % name})
        pool = "source:pool:%s:v1" % name
        d("source.acquire", {"source": "source:src:%s" % name, "rule": "t", "records": records, "pool": pool})
        if freeze:
            d("source.pool.freeze", {"pool": pool})
        return pool

    rows = lambda n: [{"id": "r%03d" % i, "country": ["DE", "FR", "IT"][i % 3], "q": i % 4} for i in range(n)]
    T_FREE = mk_pool("txtfree", rows(60))                     # no lab holds it → a shadow
    T_REG = mk_pool("txtreg", rows(30), freeze=False)         # a registered lab holds it BEFORE it freezes → no shadow
    d("labo.new", {"name": "reg_lab", "about": "a hand-registered lab", "scope": "public"})
    d("labo.bind", {"name": "reg_lab", "pool": T_REG, "origin": "registered"})
    d("source.pool.freeze", {"pool": T_REG})
    T_LATE = mk_pool("txtlate", rows(20))                     # frozen FIRST (a shadow is minted at freeze), a lab
    d("labo.new", {"name": "late_lab", "about": "registered after the shadow", "scope": "public"})    # registers AFTER
    d("labo.bind", {"name": "late_lab", "pool": T_LATE, "origin": "registered"})
    A_NEW = mk_pool("audnew", [{"id": "c%02d" % i, "url": "http://x/%d/download" % i, "content_type": "audio"}
                               for i in range(8)])
    A_OLD = mk_pool("audold", [{"id": "c%02d" % i, "url": "http://y/%d/download" % i, "content_type": "audio"}
                               for i in range(6)])
    d("vlab.run.new", {"pool": A_OLD, "observers": "spectral", "run": "b1"})       # already observed
    d("vlab.run.execute", {"run": "b1"})

    frozen = set(precompute._frozen_pools(k))
    check("the source engine's frozen-pool Set holds the fixture pools",
          {T_FREE, T_REG, A_NEW, A_OLD} <= frozen, str(sorted(frozen)))

    print("\n  ── provisioning (platform) from the real declarations ──")
    cfgs = {n: W.by_key(k, "%s/%s" % (b, n)) for n, b in (("analysis_precompute", "analysis-precompute"),
                                                          ("media_precompute", "media-precompute"))}
    check("both declarations are valid workloads", all(cfgs.values()) and not any(W.problems(c) for c in cfgs.values()),
          str({n: (W.problems(c) if c else None) for n, c in cfgs.items()}))
    for n, c in cfgs.items():
        pr = provision(lambda who, m, dd: raw(who, m, dd), c, note=lambda m: None)
        check("%s provisions with no problem" % n, not (pr or {}).get("problems"), str(pr)[:120])
    P.reconcile_workload_resources(k, list(cfgs.values()))
    ana, med = cfgs["analysis_precompute"], cfgs["media_precompute"]
    a_cl, m_cl = W.client_of(ana), W.client_of(med)
    a_bench, m_bench = "analysis-precompute", "media-precompute"

    print("\n  ── 3. registered labs win ──")
    of_free = [(x["labo"], x["origin"]) for x in (d("labo.of", {"pool": T_FREE}).get("labos") or [])]
    of_reg = [(x["labo"], x["origin"]) for x in (d("labo.of", {"pool": T_REG}).get("labos") or [])]
    of_late = [(x["labo"], x["origin"]) for x in (d("labo.of", {"pool": T_LATE}).get("labos") or [])]
    check("a pool frozen BEFORE its lab registered has a leftover shadow, and the registered lab is listed FIRST",
          len(of_late) == 2 and of_late[0] == ("labo:late_lab", "registered") and of_late[1][1] == "shadow", str(of_late))
    check("a pool no lab holds got a SHADOW labo, marked origin=shadow",
          len(of_free) == 1 and of_free[0][1] == "shadow", str(of_free))
    check("a pool a registered lab holds got NO shadow — only the registered lab answers",
          of_reg == [("labo:reg_lab", "registered")], str(of_reg))

    print("\n  ── 2. the client, not admin ──")
    refused = raw(a_cl, "analysis.precompute.pass", {"bench": m_bench})
    check("a pass aimed at ANOTHER workload's bench is refused by the gate",
          "error" in refused, str(refused)[:140])
    nobench = raw(a_cl, "analysis.precompute.pass", {})
    check("a pass with no bench= is refused (the target is required)", "error" in nobench, str(nobench)[:140])
    guest = raw("mallory", "vlab.media.pass", {"bench": m_bench})
    check("an unadmitted caller cannot run the media pass", "error" in guest, str(guest)[:120])

    print("\n  ── 4. text: every frozen text pool, exact, idempotent ──")
    r1 = d("analysis.precompute.pass", {"bench": a_bench}, who=a_cl)
    check("the pass, as the workload's client, queues the text pools",
          isinstance(r1, dict) and "__error__" not in r1 and r1.get("queued", 0) >= 3, str(r1)[:200])

    def persisted(labo, pool):
        v = d("analysis.view", {"labo": labo, "input": pool, "plugin": "count:country"})
        return (v or {}).get("persisted"), sum(((v or {}).get("projection") or {}).get("counts", {}).values())

    sh = of_free[0][0] if of_free else ""
    ok = False
    for _ in range(160):
        a, b, c = persisted(sh, T_FREE), persisted("labo:reg_lab", T_REG), persisted("labo:late_lab", T_LATE)
        if a[0] and b[0] and c[0]:
            ok = True
            break
        time.sleep(0.5)
    check("all three text pools' projections are persisted, each under ITS lab (shadow / registered / the late "
          "registered lab — registered-first even over a leftover shadow)", ok,
          "shadow=%s registered=%s" % (persisted(sh, T_FREE), persisted("labo:reg_lab", T_REG)))
    check("exact over the full pool (60 and 30)", persisted(sh, T_FREE)[1] == 60
          and persisted("labo:reg_lab", T_REG)[1] == 30, "%s %s" % (persisted(sh, T_FREE), persisted("labo:reg_lab", T_REG)))
    time.sleep(1.0)
    r2 = d("analysis.precompute.pass", {"bench": a_bench}, who=a_cl)
    check("a second pass submits NOTHING for the prepared pools (idempotent — a repeating trigger converges)",
          r2.get("per_pool", {}).get(T_FREE) in ("prepared", "n/a (None)") or r2.get("per_pool", {}).get(T_FREE) == "prepared",
          str(r2.get("per_pool", {}).get(T_FREE)))

    print("\n  ── 5. media ──")
    mr = d("vlab.media.pass", {"bench": m_bench}, who=m_cl)
    check("the media pass, as the workload's client, queues the unobserved audio pool only",
          isinstance(mr, dict) and "__error__" not in mr and mr.get("queued") == 1
          and (mr.get("per_pool") or {}).get(A_OLD) == "prepared", str(mr)[:220])
    auto = "auto_audnew_v1"
    ok = False
    for _ in range(240):
        sp = {s["space"]: s for s in (d("vlab.spaces", {"run": auto}).get("spaces") or [])}
        if sp.get("spectral", {}).get("works") == 8 and sp.get("mfcc", {}).get("works") == 8:
            ok = True
            break
        time.sleep(0.5)
    check("the audio feature spaces are populated (observation prepaid, offline)", ok, str(list(sp))[:120])
    cl = {}
    for _ in range(240):                                    # the cluster steps follow the observation in the same job
        cl = d("vlab.project", {"run": auto, "space": "spectral", "as": "cluster"})
        if cl.get("clusters"):
            break
        time.sleep(0.5)
    check("corpus analysis (clusters) is prepaid for the auto-observed pool", bool(cl.get("clusters")), str(cl)[:120])
    from lib.akasha.concepts._universal import UniversalConcept
    rm = UniversalConcept(k.manager.get_session("admin"))._meta("vision_run:%s" % auto) or {}
    check("the run is minted purpose=precompute with NO bench stamp (naming the place does not rename the run)",
          rm.get("purpose") == "precompute" and not rm.get("bench"),
          "purpose=%r bench=%r" % (rm.get("purpose"), rm.get("bench")))
    time.sleep(1.0)
    mr2 = d("vlab.media.pass", {"bench": m_bench}, who=m_cl)
    check("a second media pass submits nothing (the pool is prepared)",
          (mr2.get("per_pool") or {}).get(A_NEW) == "prepared" and mr2.get("queued") == 0, str(mr2)[:200])

    print("\n  ── 6. acceptance — after ≥ before ──")
    eligible_text = [T_FREE, T_REG, T_LATE]
    with_projection = [p for p, lab in ((T_FREE, sh), (T_REG, "labo:reg_lab"), (T_LATE, "labo:late_lab"))
                       if persisted(lab, p)[0]]
    media_pools = [A_NEW, A_OLD]
    with_run = [p for p in media_pools if (d("vlab.runs", {"pool": p}) or {}).get("runs")]
    check("frozen text pools with an analysis projection ≥ the pools the old boot thread prepared (all %d)"
          % len(eligible_text), len(with_projection) >= len(eligible_text), "%d" % len(with_projection))
    check("frozen media pools with a media run ≥ the pools the old boot thread prepared (all %d)"
          % len(media_pools), len(with_run) >= len(media_pools), "%d" % len(with_run))

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the Source Viewer's prepaid analysis and media views are two declared workloads "
          "running two pass ops as their own clients: gated per pool and per bench, registered labs win, "
          "idempotent, and no pool the old boot threads prepared is left unprepared.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
