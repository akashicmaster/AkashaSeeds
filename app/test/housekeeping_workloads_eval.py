#!/usr/bin/env python3
"""
THE TWO APPLICATION BOOT BODIES THAT CALLED PLATFORM INTERNALS ARE DECLARED WORKLOADS (purge order, A2; ruling of 4 Oct).

`schedule_labo_register` (waited on a kernel-private readiness predicate, dispatched as admin) and
`schedule_telemetry_gc` (called `kernel._schedule_backlog_gc`) were boot threads. Now:

  1. the manifest declares neither schedule, and `concepts/app_boot.py` is gone; `log_vision_roster` (a
     diagnostic line the on-demand `vlab.roster` op already gives) is deleted with it
  2. `labo_register` and `telemetry_gc` are valid declared workloads with templates
  3. as its OWN client (never admin) `labo.register.pass` registers the canonical labs (idempotent); a pass aimed at
     another bench, or none, is refused
  4. as its OWN client `feed.gc` is admitted and runs (a clean window drops 0)

Run:  python app/test/housekeeping_workloads_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

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
    man = json.load(open(os.path.join(ROOT, "app", "config", "MANIFEST.json"), encoding="utf-8"))
    print("\n  ── 1. no boot body ──")
    check("labo_register / telemetry_gc / log_vision_roster are not schedules",
          not {"labo_register", "telemetry_gc", "log_vision_roster"} & set(man["schedules"]))
    check("concepts/app_boot.py is gone", not os.path.exists(os.path.join(ROOT, "lib/akasha/concepts/app_boot.py")))
    check("no application schedule names a kernel-private (`kernel._…`) job runner",
          "_schedule_backlog_gc" not in open(os.path.join(ROOT, "app/concepts/feed_poll.py")).read())

    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.workbench import workload as W
    from lib.akasha.workbench import provision as P
    from lib.akasha.workbench.workload_provision import provision
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_hk_"))

    def raw(who, method, data, trust="local"):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": who, "data": data}, "id": "t"}, trust) or {}

    def d(method, data, who="admin"):
        r = raw(who, method, data)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    raw("admin", "kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})
    print("\n  ── 2. declared ──")
    cfgs = {n: W.by_key(k, "%s/%s" % (b, n)) for n, b in (("labo_register", "labo-register"),
                                                         ("telemetry_gc", "telemetry"))}
    check("both are valid declared workloads", all(cfgs.values()) and not any(W.problems(c) for c in cfgs.values()),
          str({n: (W.problems(c) if c else None) for n, c in cfgs.items()}))
    for n, c in cfgs.items():
        pr = provision(lambda who, m, dd: raw(who, m, dd), c, note=lambda m: None)
        check("%s provisions with no problem" % n, not (pr or {}).get("problems"), str(pr)[:160])
    P.reconcile_workload_resources(k, list(cfgs.values()))
    l_cl, g_cl = W.client_of(cfgs["labo_register"]), W.client_of(cfgs["telemetry_gc"])

    print("\n  ── 3. labo.register.pass, as its own client ──")
    check("a pass aimed at another bench is refused", "error" in raw(l_cl, "labo.register.pass", {"bench": "telemetry"}))
    check("a pass with no bench= is refused", "error" in raw(l_cl, "labo.register.pass", {}))
    from app.scripts import labo_register as LR
    d("source.register", {"provider": "hk", "name": "hk"})
    d("source.pool.create", {"name": "hk", "source": "source:src:hk"})
    LR.LABS.append({"name": "hk_lab", "about": "a lab whose pool is present", "scope": "public",
                    "pool": "source:pool:hk:v1"})                         # a resource present on this cell
    r = d("labo.register.pass", {"bench": "labo-register"}, who=l_cl)
    check("every canonical lab is registered, none refused",
          isinstance(r, dict) and r.get("labs") == len(LR.LABS) and not r.get("refused"), str(r)[:240])
    r2 = d("labo.register.pass", {"bench": "labo-register"}, who=l_cl)
    check("a resource present on the cell is bound (a lab whose pool is present)", r.get("bindings", 0) >= 1, str(r)[:160])
    check("a second pass is idempotent", r2.get("labs") == len(LR.LABS) and not r2.get("refused"), str(r2)[:160])
    ls = d("labo.ls", {}, who="mallory")
    check("a guest reads the registered labs (universal)", isinstance(ls, dict) and "blvh" in json.dumps(ls), str(ls)[:160])

    print("\n  ── 4. telemetry as the feed workload's client: public, retained ──")
    f_cl = "feed:iss"
    fc = W.by_key(k, "telemetry/iss")
    provision(lambda who, m, dd: raw(who, m, dd), fc, note=lambda m: None)
    P.reconcile_workload_resources(k, [fc])
    f_cl = W.client_of(fc)
    ing = d("feed.ingest", {"id": "iss", "records": [
        {"subject": "iss", "t": "2020-01-01T00:00:00Z", "lat": 1, "lon": 2},
        {"subject": "iss", "t": "2099-01-01T00:00:00Z", "lat": 1, "lon": 2}]}, who=f_cl)
    check("the feed's own client records observations", ing.get("observations_new") == 2, str(ing)[:160])
    seen = d("feed.latest", {"id": "iss"}, who="mallory")
    check("a GUEST reads them (published to the shared nucleus; the workload's client holds no librarian role)",
          seen.get("count") == 2, str(seen)[:160])
    check("an identity the gate does not admit cannot record telemetry",
          "error" in raw("mallory", "feed.ingest", {"id": "iss", "records": [{"subject": "x", "t": "2099-01-01T00:00:00Z"}]}))
    g = d("feed.gc", {}, who=g_cl)
    check("feed.gc, as the retention workload's client, drops the expired observation and keeps today's",
          g.get("status") == "ok" and g.get("dropped") == 1, str(g)[:200])
    check("…and the guest still reads the rest", d("feed.latest", {"id": "iss"}, who="mallory").get("count") == 1)
    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — lab registration and telemetry retention are declared workloads run as their own clients; "
          "no application boot body calls a platform internal.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
