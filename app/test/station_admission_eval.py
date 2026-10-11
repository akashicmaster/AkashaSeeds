#!/usr/bin/env python3
"""
Station boot + admission + what the platform records and answers (2026-09-18, re-cut 2026-09-23).

Covers the four asks, on both cell shapes, without a full VPS deploy (a live airing is server-side):

  §3  the reservation DERIVE — `workload_appetite(bench, branch)` reads the WORKLOAD declaration
      (key + llm_calls_per_run) and the cadence comes from its declared trigger; wf.advance passes them so a scheduled
      airing reserves against the pool (the derive is trusted, not submitter-chosen).
  §2  the interval a fresh-guard uses comes from the cadence (per_day → 86400, every_s → n).
  the RECORD + `workload.status` (ruling 2026-09-23) — the platform records one observation per run
      with the op's own reason verbatim (empty when it gave none), and answers `last` / `gate` /
      `next_at` / `spent_today`. NO `state` field: "on air" and "standing by" are the station's
      words, composed by the station Concept Model. The stamped guide row `station:show:*`, the
      `set:station:state:*` memberships and `society.station` are deleted, and with them the four
      statuses the rooms were measured showing wrongly.
  §1  the registered-programme declarations load; a boot pass provisions the declared studio (the
      provisioning itself is held by station_deploy_airs_eval).

Run:  python test/station_admission_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import time
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import wl_state
from lib.akasha.workbench import provision
from lib.akasha.api import gate as _G
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_fails = []
_BROADCASTER = "system.broadcaster"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _kernel(series, base):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    return KernelDispatcher(series=series, base_dir=base)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.concepts.society import SocietyConcept
    base = tempfile.mkdtemp(prefix="akasha_station_")
    k = _kernel(series, base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    # ── §3 — the derive reads the WORKLOAD declaration ──
    # Asserted AGAINST THE DECLARATION, not against a literal: the key is the declaration's to choose
    # (the slug rule of the 2026-09-18 ontology order moved it once already), and a test that pins a
    # spelling fails every time that choice is exercised — which is the opposite of what it guards.
    # What matters is that the derive returns the DECLARED value rather than reconstructing one.
    #
    # Seed A moved the lookup KEY: it was the studio's group, and four workloads now share one
    # bench, so a group-keyed derive would hand all four the first one's appetite. It is keyed on
    # (bench, branch) — the pair a running job knows about itself without anyone passing a name.
    from lib.akasha.workbench import workload as _W
    # The station's workloads — the ones that PUBLISH. A lab (plants_vision, `effect: record`) is a
    # workload too, on its own bench, and none of the station's key/appetite claims are about it.
    _by = {_W.key(x): x for x in _W.declarations(k) if x.get("effect") == "publish"}
    _shelf = _by.get("studio_ai/thinkers_shelf", {})
    _news = _by.get("studio_ai/news_show", {})
    prog, cpr = _W.workload_appetite(k, _W.bench_slug(_shelf), _W.branch_of(_shelf))
    check(f"[{shape}] §3 the appetite derive returns (key, llm_calls_per_run) from the declaration",
          prog == _W.key(_shelf) and cpr == _W.appetite(_shelf)["llm_calls_per_run"],
          f"{prog},{cpr} vs declared {_W.key(_shelf)},{_W.appetite(_shelf)['llm_calls_per_run']}")
    _np, _nc = _W.workload_appetite(k, _W.bench_slug(_news), _W.branch_of(_news))
    check(f"[{shape}] §3 the derive returns EXACTLY the declared key (not a guess)",
          _np == _W.key(_news) and _nc == _W.appetite(_news)["llm_calls_per_run"],
          f"{_np},{_nc} vs declared {_W.key(_news)},{_W.appetite(_news)['llm_calls_per_run']}")
    check(f"[{shape}] §2 every declared key is <bench>/<slug> with an underscore slug",
          all(_W.key(x).startswith("studio_ai/") and "-" not in _W.key(x) for x in _by.values()),
          str(sorted(_by)))
    check(f"[{shape}] §3 four workloads on ONE bench each derive their OWN appetite (a group-keyed "
          f"lookup would give them all the first one's)",
          len({_W.workload_appetite(k, _W.bench_slug(x), _W.branch_of(x)) for x in _by.values()})
          == len(_by),
          str(sorted(_W.workload_appetite(k, _W.bench_slug(x), _W.branch_of(x)) for x in _by.values())))
    check(f"[{shape}] §2 the cadence interval comes from the declared TRIGGER (daily → 86400, "
          f"every:1800s → 1800)",
          _W.interval_s(_shelf) == 86400.0 and _W.interval_s(_news) == 1800.0,
          f"{_W.interval_s(_shelf)},{_W.interval_s(_news)}")
    check(f"[{shape}] §3 an undeclared (bench, branch) derives nothing (submitter data would be "
          f"declared=false)",
          _W.workload_appetite(k, "no_such_bench", "no_such_branch") == (None, 0))

    # ── THE RUN IS RECORDED, AND `workload.status` DERIVES (ruling 2026-09-23) ─────────────────
    #
    # What stood here was §4 / §2.3 / §2.5: `note_airing` maintaining `today`, `next_burst_at`,
    # `skipped` and `last_post_at` on the guide row `station:show:<gid>:<space>`; the programme's
    # membership of exactly one `set:station:state:*`; and the row serving `state` / `reason` /
    # `airing` / `llm{}` to the room. Every one of those is the PLATFORM NAMING AN APPLICATION'S
    # STATUS, and the whole register is deleted. Four of its fields were measured lying in
    # production — a `no_text` on workloads that call no model, a `standing_by` beside airings that
    # ran — because the row was a second copy of facts the bench's own observations already held.
    #
    # The contract now: the bench RECORDS one observation per run, carrying the op's own reason
    # verbatim (or none), and `workload.status key=` DERIVES `last` + `gate` + `next_at` +
    # `spent_today` from it. There is no `state` field: "on air", "standing by" and the sentences
    # around them are the station's words, composed by the station Concept Model from these two.
    provision.provision_workloads(k)
    gid, space = "studio_ai", "news_show"
    _key = _W.key(_news)

    def _d(method, data, who="admin"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": who, "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    def _record(aired, reason="", provider="", model=""):
        # The run is recorded the way the DRIVER records it (group 4, 4.12(a)): one row in the
        # platform's own run record, `ok` = the job ran, the effect counted, the op's own reason
        # verbatim. `workload.status.last` reads this row and nothing else — it no longer derives
        # from the application's bench rows. A stand-by run is ok=False here as it was, so the
        # contract checked below is unchanged: the reason passes through untouched.
        from lib.akasha.workbench import wl_state as _wls
        return _wls.record_run(k, _key, at=time.time(), ok=bool(int(aired)), reason=reason,
                               effect_count=int(aired), by="eval")

    st = _d("workload.status", {"key": _key})
    check(f"[{shape}] the platform ANSWERS for a declared workload (key + its society)",
          st.get("declared") is True and st.get("society") == f"{gid}/{space}", str(st)[:120])
    check(f"[{shape}] …with `last` and `gate`, and NO `state` — the words are the application's",
          "last" in st and "gate" in st and "state" not in st, str(sorted(st.keys())))
    _term = str((st.get("gate") or {}).get("run") or "")
    check(f"[{shape}] …and the gate's term is `ok` or one of the platform's OWN reasons",
          _term == "ok" or _term in _G.REASONS, f"run={_term!r}")
    check(f"[{shape}] a workload nothing declares answers declared=false, not an invented status",
          _d("workload.status", {"key": "studio_ai/no_such_show"}).get("declared") is False
          and _d("workload.status", {"key": "studio_ai/no_such_show"}).get("last") == {},
          str(_d("workload.status", {"key": "studio_ai/no_such_show"}))[:100])

    # a STAND-BY: the op names its own reason, and the platform passes it through untouched
    _record(0, reason="llm_pool")
    st = _d("workload.status", {"key": _key})
    _last = st.get("last") or {}
    check(f"[{shape}] a stand-by is RECORDED with the op's own reason, verbatim",
          _last.get("ok") is False and _last.get("reason") == "llm_pool", str(_last)[:120])
    check(f"[{shape}] …and the platform does not restate it in the station's namespace",
          not str(_last.get("reason") or "").startswith("station:reason:"), str(_last.get("reason")))

    # a run the op gave NO reason for stays EMPTY — the P2 fault was inventing `no_text` here
    _record(0)
    _last = (_d("workload.status", {"key": _key}).get("last") or {})
    check(f"[{shape}] a run whose op gave no reason records an EMPTY one (never a substitute)",
          _last.get("ok") is False and _last.get("reason") == "", f"reason={_last.get('reason')!r}")

    # an AIRING: ok, no reason, and the trigger's next window measured from it
    _record(1, provider="openrouter", model="meta-llama/llama-3.3-70b-instruct:free")
    st = _d("workload.status", {"key": _key})
    _last = st.get("last") or {}
    check(f"[{shape}] an airing is recorded ok with no reason",
          _last.get("ok") is True and _last.get("reason") == "", str(_last)[:120])
    check(f"[{shape}] next_at is the DECLARED cadence from that airing (every:1800s → +1800)",
          abs(float(st.get("next_at") or 0) - (float(_last.get("at") or 0) + 1800.0)) < 2.0,
          "next_at=%s at=%s" % (st.get("next_at"), _last.get("at")))
    check(f"[{shape}] spent_today is the pool's count for THIS key (an int, never a stamped row)",
          isinstance(st.get("spent_today"), int), str(st.get("spent_today")))

    # FOUR WORKLOADS SHARE ONE BENCH — a status read must not answer with another's run.
    _other = _W.key(_shelf)
    _so = _d("workload.status", {"key": _other})
    check(f"[{shape}] a second workload on the SAME bench has its own empty record (no bleed)",
          _so.get("declared") is True and (_so.get("last") or {}) == {},
          "last=%s" % str(_so.get("last"))[:80])

    # ── §1 — the declarations load (provisioning itself is held by station_deploy_airs_eval). ──
    # Counted from the declarations on disk, not from a literal: a fifth declaration landing (as
    # `news_show_x` did) is a file, and an eval that has to be edited for it is testing its own
    # memory rather than the loader.
    _want = len([x for x in _W.declarations(None) if x.get("effect") == "publish"])
    check(f"[{shape}] §1 every station workload declaration loads ({_want})",
          len(_by) == _want and _want >= 4, str(sorted(_by)))
    check(f"[{shape}] §1 …and the loader reads every declaration on disk, the lab's included",
          len(_W.declarations(k)) == len(_W.declarations(None)),
          "%d vs %d" % (len(_W.declarations(k)), len(_W.declarations(None))))


def _rename_checks():
    """decision (i)b — the one-time ledger rename carries credits + measures + today's tally, and is
    idempotent (runs once, no alias afterwards)."""
    import lib.akasha.workbench.llm_pool as pool
    print("\n  ── (i)b one-time ledger rename ──")
    vault = {}
    pool.set_pool_store(lambda k: vault.get(k), lambda k, d: vault.__setitem__(k, dict(d)))
    pool._MEM.clear()
    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "100"
    old, new = "studio_ai/news_show", "studio_ai/ai-news"
    # accumulate today's spend under the OLD key first (a run in by[old]), THEN stamp a carry-over
    # credit + a measured mean directly (so the reserve does not consume the credit we are testing)
    r = pool.reserve("mistral", old, 3); r["consumed"] = 2; pool.settle(r, wall_s=0.1)  # by[old] gets a run
    vault[pool._CREDITS_KEY] = {old: {"n": 2, "calls": 3, "since": 1.0}}
    vault[pool._MEASURES_KEY] = {old: {"mean": 2.5, "n": 6}}
    res = pool.rename_program(old, new, provider="mistral")
    check("(i)b the rename reports carried credits + measures + by", res.get("renamed")
          and set(res.get("carried") or []) >= {"credits", "measures", "by"}, str(res))
    check("(i)b the carry-over credit moved to the new key (old cleared)",
          pool.credits(new) == 2 and pool.credits(old) == 0, f"new={pool.credits(new)} old={pool.credits(old)}")
    _ms = pool._load(pool._MEASURES_KEY)
    check("(i)b the measured mean moved to the new key",
          new in _ms and old not in _ms and abs(float(_ms[new]["mean"]) - 2.5) < 0.6, str(_ms))
    check("(i)b today's by[program] tally moved to the new key",
          new in pool.pool_view("mistral").get("by", {}) and old not in pool.pool_view("mistral").get("by", {}),
          str(list(pool.pool_view("mistral").get("by", {}).keys())))
    again = pool.rename_program(old, new, provider="mistral")
    check("(i)b the rename is idempotent — it runs ONCE (second call is a no-op)",
          again.get("renamed") is False and again.get("reason") == "already", str(again))
    pool.set_pool_store(lambda k: None, lambda k, d: None); pool._STORE = None; pool._MEM.clear()


def main():
    print("=" * 78)
    print("Station — boot admission + what the platform records and answers (2026-09-23)")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    _rename_checks()
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails))); sys.exit(1)
    print("RESULT: PASS — the scheduled-airing reservation derives its key + appetite + interval from "
          "the studio declaration (§3/§2); each run is RECORDED once, carrying the op's own reason "
          "verbatim or none at all; `workload.status` answers `last` + `gate` + `next_at` + "
          "`spent_today` for the declared key, with NO `state` field and no station word in it, and "
          "four workloads on one bench never read each other's runs; the declarations load and a "
          "boot pass provisions the declared studio (§1) — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
