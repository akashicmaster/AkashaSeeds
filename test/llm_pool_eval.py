#!/usr/bin/env python3
"""
B10 — shared LLM resource ALLOCATION: the reservation/pool layer on top of the A53 free-tier floor.

The defect this closes: a run that exhausts the day's provider cap halfway. Every LLM call passes the
one gate (`llm_provider.generate`), where A53 enforces the hard floor (calls/UTC-day + tokens/UTC-month,
durable, trips even for a bypassed call). B10 adds the ALLOCATION: a programme RESERVES its per-run calls
at admission and runs prepaid; a reservation that would cross the ceiling is refused before anything is
called; the gate debits the reservation and settles the unused at the end. Capacity = A53's caps; spend
= A53's meter — B10 never re-counts either.

Stage-1 acceptance (§1.6): reservation refused before it starts (nothing called); a run that ends early
returns its unused calls; two programmes never exceed the cap together; reserved survives a restart; the
floor (A53) still trips if a reservation is bypassed. Stage 2 (§2.3): carry-over protects a once-a-day
programme. Stage 3: the measured mean overrides the declaration. §4: llm.route resolves the provider.

Run:  python test/llm_pool_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import llm
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _reset(pool, lp, cap_calls, tokens_month=0):
    """A fresh, deterministic world: A53 meter cleared + capped via env; B10 pool store on a fresh dict;
    pacing disabled so the eval never sleeps."""
    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = str(cap_calls)
    os.environ["AKASHA_LLM_MISTRAL_TOKENS_PER_MONTH"] = str(tokens_month)
    lp._METER.clear(); lp._METER_LOADED = True; lp._NEXT_OK.clear()
    lp._FREE_TIER["mistral"]["min_interval"] = 0.0        # no pacing sleeps in the eval
    vault = {}
    pool.set_pool_store(lambda k: vault.get(k), lambda k, d: vault.__setitem__(k, dict(d)))
    pool._MEM.clear()
    return vault


def _module_checks():
    import lib.akasha.workbench.llm_pool as pool
    import lib.akasha.workbench.llm_provider as lp
    print("\n  ── module: reserve / settle / floor ──")
    _reset(pool, lp, cap_calls=5)

    # ── a reservation that fits is granted ──
    r1 = pool.reserve("mistral", "studio_ai/news_show", 3)
    check("a reservation within the cap is granted", r1 is not None and r1["calls"] == 3)
    check("the granted reservation is reserved on the pool (reserved=3, spent=0)",
          pool.pool_view("mistral")["reserved"] == 3 and pool.pool_view("mistral")["spent_calls"] == 0)

    # ── two programmes never exceed the cap together (5): B reserving 3 more is refused ──
    r2 = pool.reserve("mistral", "reading/daily", 3)
    check("a second reservation that would cross the cap is REFUSED (nothing called)", r2 is None)
    check("the refusal is counted", pool.pool_view("mistral")["refused"] == 1)
    r2b = pool.reserve("mistral", "reading/daily", 2)
    check("a reservation that fits the remaining budget is granted (3+2 == cap)",
          r2b is not None and pool.pool_view("mistral")["reserved"] == 5)

    # ── the gate (A53) counts spend + debits the reservation; a run that ends early returns unused ──
    os.environ["AKASHA_MISTRAL_KEY"] = "test-key-never-logged"
    calls = {"n": 0}
    def ok_turn(url, body, headers, timeout=60):
        calls["n"] += 1
        return {"choices": [{"message": {"content": "aired words from the model"}}]}
    lp._http_json = ok_turn
    pool.begin_run(r1)
    lp.generate("mistral", "", "sys", "user")          # 1 real call of the 3 reserved
    pool.end_run()
    st = pool.settle(r1, wall_s=0.4)
    check("the gate counted the real call in A53's meter (spent_calls=1)",
          pool.pool_view("mistral")["spent_calls"] == 1, str(pool.pool_view("mistral")["spent_calls"]))
    check("a run that ends early spends only what it used (spent=1) and returns the rest (returned=2)",
          st["spent"] == 1 and st["returned"] == 2, str(st))
    check("after settle the pool releases the reservation (reserved back to 2 = B's)",
          pool.pool_view("mistral")["reserved"] == 2)
    check("by[program] records the run's spend and one run",
          pool.pool_view("mistral")["by"]["studio_ai/news_show"]["spent"] == 1
          and pool.pool_view("mistral")["by"]["studio_ai/news_show"]["runs"] == 1)

    # ── D5 — the same reservation, SETTLED TWICE, spends once ────────────────────────────────────
    # The `settled` flag was stamped on the passed dict and nowhere else, so it answered only for
    # one object in one process's memory. A reservation read back from the durable vault, or copied
    # across a hand-off, arrives WITHOUT it and settles again: `by[program].spent` gains another
    # `consumed` that no model call produced. That is how a workload came to report 240 calls
    # charged on a day the provider's own meter counted 21 — a tenfold spend that was never spent.
    # The ledger itself has to remember, because the ledger is what survives the process.
    _before = dict(pool.pool_view("mistral")["by"]["studio_ai/news_show"])
    _reread = dict(r1)                                  # what a durable re-read hands back…
    _reread.pop("settled", None)                        # …with no in-memory flag on it
    st2 = pool.settle(_reread, wall_s=0.4)
    _after = pool.pool_view("mistral")["by"]["studio_ai/news_show"]
    check("a reservation re-read from the store and settled a SECOND time moves nothing",
          st2.get("repeat") is True and st2["spent"] == 0
          and _after["spent"] == _before["spent"] and _after["runs"] == _before["runs"],
          "before=%s after=%s st2=%s" % (_before, dict(_after), st2))
    check("…and the pool's own tally never exceeds A53's meter, which counts every call ATTEMPTED "
          "while the pool counts only the ones that answered",
          pool.pool_view("mistral")["pool_spent_calls"] <= pool.pool_view("mistral")["spent_calls"],
          "pool=%d metered=%d" % (pool.pool_view("mistral")["pool_spent_calls"],
                                  pool.pool_view("mistral")["spent_calls"]))
    check("the guard is on the DURABLE record, not only the dict — the id is remembered there",
          r1["id"] in (pool._get_own("mistral", pool.day()).get("settled_ids") or []))

    # ── a reservation would cross the cap → refused before it starts, nothing called ──
    calls["n"] = 0
    # committed = spent(1) + reserved(2) = 3; cap 5 → 2 free; a 3-call reservation is refused
    r3 = pool.reserve("mistral", "late/show", 3)
    check("a reservation is refused before it starts when it would cross the cap (nothing called)",
          r3 is None and calls["n"] == 0)

    # ── the hard floor (A53) still trips if a reservation is BYPASSED ──
    _reset(pool, lp, cap_calls=2)
    calls["n"] = 0
    lp._http_json = ok_turn
    o1 = lp.generate("mistral", "", "s", "u")          # bypasses reserve — A53 meters it
    o2 = lp.generate("mistral", "", "s", "u")
    o3 = lp.generate("mistral", "", "s", "u")          # cap reached → A53 suppresses, no HTTP
    check("the floor allows calls up to the cap (2 HTTP calls made)",
          o1 and o2 and calls["n"] == 2, str(calls["n"]))
    check("the A53 floor trips on a bypassed call once the cap is reached (3rd None, no HTTP)",
          o3 is None and calls["n"] == 2, str(calls["n"]))
    os.environ.pop("AKASHA_MISTRAL_KEY", None)

    # ── restart: reserved (B10) + spent (A53) both persist through their vault stores ──
    print("\n  ── module: restart persistence ──")
    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "5"
    os.environ["AKASHA_LLM_MISTRAL_TOKENS_PER_MONTH"] = "0"
    lp._FREE_TIER["mistral"]["min_interval"] = 0.0
    pvault = {}
    mvault = {"d": {}}
    lp._METER.clear(); lp._METER_LOADED = False
    lp.set_meter_store(lambda: dict(mvault["d"]), lambda x: mvault.__setitem__("d", dict(x)))
    pool.set_pool_store(lambda k: pvault.get(k), lambda k, d: pvault.__setitem__(k, dict(d)))
    pool._MEM.clear()
    r = pool.reserve("mistral", "svc/persist", 2)       # reserved 2 (persisted to pvault)
    lp._meter_record("mistral", 40)                     # spend 1 (persisted to mvault)
    # simulate RESTART: wipe process memory, reinstall stores over the SAME vaults, reload
    lp._METER.clear(); lp._METER_LOADED = False
    lp.set_meter_store(lambda: dict(mvault["d"]), lambda x: mvault.__setitem__("d", dict(x)))
    pool.set_pool_store(lambda k: pvault.get(k), lambda k, d: pvault.__setitem__(k, dict(d)))
    pool._MEM.clear()
    pv = pool.pool_view("mistral")
    check("the vault carries both across the restart — nothing was lost with the process "
          "(reserved=2, spent=1)",
          pv["reserved"] == 2 and pv["spent_calls"] == 1, str({k: pv[k] for k in ("reserved", "spent_calls")}))

    # §4 — …and then the two are told apart. The SPEND happened and must survive; the RESERVATION
    # was a claim held open by a job of a process that is gone, and nothing will ever settle it. A
    # boot that inherits it answers every request for the rest of the day against a ceiling that
    # much lower — the live cell booted with `reserved=65` from jobs that no longer existed. The
    # release runs at pool-store install, which is what is exercised here, log line and all.
    import logging as _lg

    class _Grab0(_lg.Handler):
        def __init__(self):
            super().__init__(); self.lines = []

        def emit(self, r):
            self.lines.append(r.getMessage())

    class _Nuc:
        def vault_retrieve(self, cat, k):
            return pvault.get(k) if cat == "llm_pool" else None

        def vault_store(self, cat, k, d):
            if cat == "llm_pool":
                pvault[k] = dict(d)

    class _Mgr:
        shared_nucleus = _Nuc()

    class _K:
        manager = _Mgr()

    _g0 = _Grab0()
    _lgr = _lg.getLogger("Akasha.Kernel")
    _lgr.addHandler(_g0); _lgr.setLevel(_lg.INFO)
    try:
        llm.install_llm_pool_store(_K())
    finally:
        _lgr.removeHandler(_g0)
    pv2 = pool.pool_view("mistral")
    check("a reservation does not survive the process that made it — the boot releases it",
          pv2["reserved"] == 0, "reserved=%s" % pv2["reserved"])
    check("…and the spend it was stored beside is untouched (that one DID happen)",
          pv2["spent_calls"] == 1, "spent_calls=%s" % pv2["spent_calls"])
    _rel = [ln for ln in _g0.lines if "released stale reservations" in ln]
    check("…and the boot says so, once, with the provider and the number it released",
          len(_rel) == 1 and "provider=mistral" in _rel[0] and "n=2" in _rel[0],
          _rel[0] if _rel else "%d line(s)" % len(_rel))
    _g0.lines.clear()
    _lgr.addHandler(_g0)
    try:
        llm.install_llm_pool_store(_K())
    finally:
        _lgr.removeHandler(_g0)
    check("…and a boot with nothing to release is silent about it (no line for reserved=0)",
          not [ln for ln in _g0.lines if "released stale reservations" in ln])
    check("a reservation made AFTER the boot is a live claim and is not released by it",
          (pool.reserve("mistral", "svc/live", 1) or {}).get("calls") == 1
          and pool.pool_view("mistral")["reserved"] == 1)

    pool.set_pool_store(lambda k: None, lambda k, d: None); pool._STORE = None; pool._MEM.clear()
    lp.set_meter_store(lambda: {}, lambda x: None); lp._METER.clear(); lp._METER_LOADED = True

    # ── B10-b — the pool's OWN aggregate (pool_spent_calls/tokens = Σ by[*].spent) + per-program spend ──
    bvault = {}
    pool.set_pool_store(lambda k: bvault.get(k), lambda k, d: bvault.__setitem__(k, dict(d)))
    pool._MEM.clear()
    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "100"
    import logging as _logging
    _cap = []
    class _Grab(_logging.Handler):
        def emit(self, r): _cap.append(r.getMessage())
    _lg = _logging.getLogger("Akasha.LLM"); _lg.setLevel(_logging.INFO)
    _h = _Grab(); _h.setLevel(_logging.INFO); _lg.addHandler(_h)
    rA = pool.reserve("mistral", "studio_ai/news_show", 3)
    rA["consumed"] = 2; rA["tokens_spent"] = 800; pool.settle(rA)
    rB = pool.reserve("mistral", "studio_ai/reading_room", 4)
    rB["consumed"] = 4; rB["tokens_spent"] = 1600; pool.settle(rB)
    _lg.removeHandler(_h)
    pv = pool.pool_view("mistral")
    check("B10-b pool_spent_calls = Σ by[*].spent (2+4=6)", pv["pool_spent_calls"] == 6, str(pv["pool_spent_calls"]))
    check("B10-b pool_spent_tokens = Σ by[*].tokens (800+1600=2400)", pv["pool_spent_tokens"] == 2400,
          str(pv["pool_spent_tokens"]))
    check("B10-b program_spent attributes one programme's spend (calls=2, tokens=800)",
          pool.program_spent("studio_ai/news_show", "mistral") == {"calls": 2, "tokens": 800, "runs": 1},
          str(pool.program_spent("studio_ai/news_show", "mistral")))
    # B10-c's admission line moved OUT of the pool in step 2 §6: it was emitted here only because a
    # second caller reserved outside admission and had no other trace, and that caller went with
    # station.py. The line is now `[llm] admission reserved … free= cap=`, logged once at the one
    # admission point — `test/llm_admission_line_eval.py` owns it. What the pool must NOT do is log
    # a second one: two layers naming one reservation is how a reader counts it twice.
    check("B10-c the pool logs no reservation line of its own (admission logs the one)",
          sum(1 for m in _cap if m.startswith("[llm] reserved")) == 0,
          str([m for m in _cap if m.startswith("[llm] reserved")]))
    pool.set_pool_store(lambda k: None, lambda k, d: None); pool._STORE = None; pool._MEM.clear()


def _stage23_checks():
    import lib.akasha.workbench.llm_pool as pool
    import lib.akasha.workbench.llm_provider as lp
    print("\n  ── Stage 2/3/4 (carry-over + measured estimate + routing) ──")
    _reset(pool, lp, cap_calls=2)

    _days = {"d": "2026-01-01"}
    _real_day = pool.day
    pool.day = lambda: _days["d"]
    # meter rolls over by UTC day too; freeze the meter's "today" to match by clearing it each day
    try:
        # Day 1 — the continuous programme C fills the cap; the once-a-day D is refused → gains a credit.
        pool.reserve("mistral", "cont/C", 2)            # reserved 2/2
        d1 = pool.reserve("mistral", "daily/D", 1)      # no room → refused
        check("Stage2: the once-a-day programme is refused when the pool is full", d1 is None)
        check("Stage2: a refused programme gains a carry-over credit", pool.credits("daily/D") == 1)

        # Day 2 — fresh pool (new day → own state resets; meter has 0 spent). D's owed call is headroom,
        # so the hog C cannot take the whole pool; D (credited) is admitted and consumes its credit.
        _days["d"] = "2026-01-02"
        c1 = pool.reserve("mistral", "cont/C", 1)       # ok (1/2)
        c2 = pool.reserve("mistral", "cont/C", 1)       # refused — 2nd slot is headroom for D
        check("Stage2: a hog cannot take the slot held for a credited programme", c1 is not None and c2 is None)
        d2 = pool.reserve("mistral", "daily/D", 1)      # credited → admitted
        check("Stage2: the credited once-a-day programme runs the next day (not starved)", d2 is not None)
        check("Stage2: the successful admission consumed the carry-over credit", pool.credits("daily/D") == 0)

        # Stage 3 — a programme that consistently uses fewer calls than declared: after ≥5 settles whose
        # mean diverges >25 % from the declaration, the reservation uses the MEASURED mean.
        _days["d"] = "2026-01-03"
        _reset(pool, lp, cap_calls=100)
        for _ in range(6):
            r = pool.reserve("mistral", "svc/lean", 3)
            r["consumed"] = 1
            pool.settle(r, wall_s=0.1)
        rn = pool.reserve("mistral", "svc/lean", 3)
        check("Stage3: after ≥5 settles the reservation uses the measured mean, not the declaration",
              rn is not None and rn["calls"] == 1 and rn["declared"] == 3, str(rn)[:90])
    finally:
        pool.day = _real_day
        pool.set_pool_store(lambda k: None, lambda k, d: None); pool._STORE = None; pool._MEM.clear()
    check("Stage4: llm.route resolves shared/dedicated/local to distinct pool providers",
          pool.route_provider("mistral", "shared") == "mistral"
          and pool.route_provider("mistral", "dedicated") == "mistral#2"
          and pool.route_provider("mistral", "local") == "ollama")


def _kernel(series, base):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    return KernelDispatcher(series=series, base_dir=base)


def _kernel_checks(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    import lib.akasha.workbench.llm_pool as pool
    import lib.akasha.workbench.llm_provider as lp
    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "4"
    os.environ["AKASHA_LLM_MISTRAL_TOKENS_PER_MONTH"] = "0"
    lp._FREE_TIER["mistral"]["min_interval"] = 0.0
    base = tempfile.mkdtemp(prefix="akasha_llmpool_")
    k = _kernel(series, base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    llm.install_llm_backoff_store(k)                      # installs A53's meter store (vault-backed)
    llm.install_llm_pool_store(k)                         # installs B10's pool store
    lp._METER.clear(); lp._METER_LOADED = False; pool._MEM.clear()
    day = pool.day()

    def disp(method, data, trust="local", token="admin"):
        p = {"data": data}
        if token is not None:
            p["session_token"] = token
        return k.dispatch({"jsonrpc": "2.0", "method": method, "params": p, "id": "t"}, trust)

    # reserve a run, count 2 real calls through A53's meter, settle, reflect the atom
    res = pool.reserve("mistral", "studio_ai/news_show", 3)
    check(f"[{shape}] a reservation is granted against the vault-backed pool", res is not None)
    pool.begin_run(res)
    lp._meter_record("mistral", 40); pool.note_consumed("mistral", 40)
    lp._meter_record("mistral", 40); pool.note_consumed("mistral", 40)
    pool.end_run()
    pool.settle(res, wall_s=0.5)
    llm.llm_pool_reflect(k, "mistral")

    nuc = k.manager.shared_nucleus
    akey = nuc.core.get_key_by_alias("llm:pool:mistral:%s" % day)
    scopes = (nuc.core.get_chunk_access_scopes(akey) or []) if akey else []
    check(f"[{shape}] the pool atom is at scope:sys:universal (guest-readable)",
          "scope:sys:universal" in scopes, str(scopes)[:80])
    ar = disp("r", {"id": "llm:pool:mistral:%s" % day})
    body = (ar.get("result") or {}) if isinstance(ar, dict) else {}
    meta = body.get("meta") or body.get("metadata") or {}
    check(f"[{shape}] the pool atom reports counts (spent_calls=2, reserved back to 0)",
          int(meta.get("spent_calls", -1)) == 2 and int(meta.get("reserved", -1)) == 0, str(meta)[:140])
    check(f"[{shape}] the pool atom carries counts, never a key or prompt",
          "capacity_calls" in meta and "prompt" not in meta and "key" not in meta, str(meta)[:110])

    # submit_job reserves at admission; cap=4, spent 2 + reserved 0 → 2 free. need 2 admitted, need 3 refused
    ok_job = disp("job.submit", {"label": "llm-run-A", "llm_calls_per_run": 2, "program": "svc/A",
                                 "steps": [{"method": "ping", "params": {}}]})
    check(f"[{shape}] a job declaring llm_calls_per_run that fits is admitted (reserved at admission)",
          "result" in ok_job and ok_job["result"].get("job_id"), str(ok_job)[:120])
    over_job = disp("job.submit", {"label": "llm-run-B", "llm_calls_per_run": 3, "program": "svc/B",
                                   "steps": [{"method": "ping", "params": {}}]})
    check(f"[{shape}] a job whose reservation would cross the cap is REFUSED (not queued, -32005)",
          "error" in over_job and over_job["error"].get("code") == -32005, str(over_job)[:150])

    seg = pool.health_segment("mistral")
    check(f"[{shape}] the Health segment reports the pool (spent/cap reserved refused)",
          "llm(pool=mistral" in seg and "spent=" in seg, seg)
    pool.set_pool_store(lambda kk: None, lambda kk, d: None); pool._STORE = None; pool._MEM.clear()
    lp.set_meter_store(lambda: {}, lambda x: None); lp._METER.clear(); lp._METER_LOADED = True


def main():
    print("=" * 78)
    print("B10 — shared LLM resource allocation on the A53 floor: pool, reserve/settle")
    print("=" * 78)
    _module_checks()
    _stage23_checks()
    _kernel_checks("thesaurus", "nucleus cell")
    _kernel_checks("seeds", "single-store cell")
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails))); sys.exit(1)
    print("RESULT: PASS — a programme reserves its per-run calls at admission and runs prepaid on the A53 "
          "floor; a reservation that would cross the ceiling is refused before anything is called "
          "(job.submit -32005); a run that ends early returns its unused calls; two programmes never "
          "exceed the cap together; reserved (B10) and spent (A53) survive a restart; the A53 floor trips "
          "on a bypassed call; carry-over protects a once-a-day programme; the measured mean overrides "
          "the declaration; llm.route resolves the provider — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
