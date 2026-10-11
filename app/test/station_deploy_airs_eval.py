#!/usr/bin/env python3
"""
A deploy AIRS — a declared studio provisions itself, with no operator.

`ruling-station-airing-2026-09-18.md` §1/§4: when a bench boots, every registered programme is
submitted for an airing, and a registered programme is never silent. Arming alone could not deliver
that: the boot arm SKIPPED a society that did not exist yet ("setup's job"), so a fresh deploy
carried the room, the bench, the corpus and the cycle but no society — the programme guide had no
show, and the room read `warming up` with `unclassified` cells forever. That is what the live cell
showed on 2026-09-19, and it is what this eval holds shut.

The boot pass now provisions a DECLARED society that is absent, from the same declaration, through
the same plan the operator tool runs (`lib/akasha/workbench/workload_provision.py` — one code path, every step
an ordinary kernel call). This eval boots a throwaway cell and checks:

  · a fresh cell provisions the declared studio and makes it ANSWERABLE, so `workload.status` —
    what the room and the lobby derive their words from — knows it (the stamped `station:show:*`
    guide row it used to register is deleted; ruling 2026-09-23);
  · the DECLARED daily budget is what the room counts `spent_today` against, read once from the
    declaration rather than copied onto a row that can disagree with it;
  · the society is armed `mode=auto` with the declared policy, so the driver airs it;
  · the studio's bench exists and the society is connected to it;
  · a SECOND pass changes nothing (idempotent — no duplicate group, cast or show);
  · a studio that declares no automation (the in-kernel news programme) is not provisioned this way.

Run:  python app/test/station_deploy_airs_eval.py      (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import wl_state
from lib.akasha.workbench import provision
from lib.akasha.workbench import autorun
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.workbench import workload as _W
    from lib.akasha.workbench import wl_state

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_deploy_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(client, method, data, trust="internal"):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": client, "data": data}, "id": "t"}, trust)

    from lib.akasha.workbench import workload_provision as _wp
    decls = _W.declarations(k)
    declared = [x for x in decls if not _W.problems(x) and _wp.template_path(x)
                and _W.effect(x) == "publish"]            # the STATION programmes (the record workloads have no airing)
    check("the declaration set carries at least one well-formed workload with a template",
          bool(declared), "of %d declarations, %d are provisionable" % (len(decls), len(declared)))
    if not declared:
        return 1
    st = declared[0]
    gid, space = _W.society_of(st)
    print("\n  ── a fresh cell, and the declared workload %s ──" % _W.key(st))

    from lib.akasha.concepts.society import SocietyConcept
    sc = SocietyConcept(k.manager.get_session("admin"))
    # On a fresh cell there is no group, and `read_autorun` RAISES rather than answering `mode=""`.
    # That is exactly the fresh-deploy state, and it is why the arm pass must treat a raise as absent.
    def mode_of():
        try:
            return sc.read_autorun(gid, space)
        except Exception as exc:
            return {"mode": "", "raised": str(exc)[:60]}

    before_boot = mode_of()
    check("before boot the society does not exist (this is the fresh-deploy state)",
          before_boot.get("mode") == "", before_boot.get("raised") or before_boot.get("mode"))

    print("\n  ── the boot pass ──")
    provision.provision_workloads(k)

    info = mode_of()
    check("the society now exists", info.get("mode") != "", "mode=%s" % info.get("mode"))
    check("… and is armed `auto` from the declared policy (the driver airs it, no operator)",
          info.get("mode") == "auto", "mode=%s" % info.get("mode"))
    pol = info.get("policy") or {}
    check("… with the declared trigger and budget",
          bool(pol.get("trigger")) and bool(pol.get("budget")),
          "trigger=%s budget=%s" % (pol.get("trigger"), pol.get("budget")))
    check("the society is connected to its station bench",
          bool(info.get("bench")), "bench=%s" % info.get("bench"))

    print("\n  ── what the platform answers about it ──")
    # The room and the lobby rendered `society.station` — a platform-owned register of stamped
    # `station:show:*` rows. It is deleted (ruling 2026-09-23): the platform records what happened
    # and answers the gate's terms, and the words a room shows are the station's, composed from
    # `workload.status`. So "provisioned" is checked as ANSWERABLE, and the budget the room counts
    # against is read from the ONE declaration rather than from a second copy that can disagree.
    guest = (d("admin", "session.guest.create", {}) or {}).get("result") or {}
    tok = guest.get("binding_key") or "admin"
    _key = _W.key(st)
    res = ((d(tok, "workload.status", {"key": _key}, trust="network") or {}).get("result")) or {}
    check("the provisioned workload is ANSWERABLE (what the room reads)",
          res.get("declared") is True and res.get("society") == "%s/%s" % (gid, space),
          json.dumps(res, ensure_ascii=False)[:140])
    check("… with `last` and `gate`, and NO `state` — the words are the application's",
          "last" in res and "gate" in res and "state" not in res, str(sorted(res.keys())))
    check("… and the declared daily budget is what the room counts `spent_today` against",
          (pol.get("budget") or {}).get("runs_per_day") == _W.budget(st)["per_day"]
          and isinstance(res.get("spent_today"), int),
          "budget=%s spent=%s" % (pol.get("budget"), res.get("spent_today")))

    print("\n  ── a second boot changes nothing ──")
    before = json.dumps(res, sort_keys=True)
    provision.provision_workloads(k)
    res2 = ((d(tok, "workload.status", {"key": _key}, trust="network") or {}).get("result")) or {}
    check("the status is unchanged by the second pass (a reconcile, not a re-create)",
          json.dumps(res2, sort_keys=True) == before, json.dumps(res2, ensure_ascii=False)[:140])
    casts = (((d(st.get("client") or ("llm:programme:%s" % gid), "cast.ls", {}) or {})
              .get("result")) or {}).get("casts") or []
    names = [c.get("name") for c in casts]
    # The live 2026-09-20 failure: the society existed and was armed, so the boot pass skipped the
    # plan — including the wf.new/wf.load that puts the cycle on the bench. The bench never had a
    # workflow, every run failed `has no workflow`, and the driver blamed a breaker and a fresh skip.
    # ARMED IS NOT PROVISIONED: a boot reconciles an armed programme to its declaration.
    from lib.akasha.concepts.workflow import WorkflowConcept

    def _has_workflow():
        w = WorkflowConcept(k.manager.get_session("admin"))
        w._bind(w._bench_gid(gid))
        return bool(w._key(w._wf_head(gid)))

    check("the programme's cycle is on its bench after provisioning", _has_workflow())
    check("… and still there after a SECOND boot of an ALREADY-ARMED programme", _has_workflow())
    check("the casts were REUSED, not minted again (one avatar per role)",
          len(names) == len(set(names)), str(sorted(names)))

    print("\n  ── the STATION rules the generic driver now applies (owner's decision A) ──")
    sc2 = SocietyConcept(k.manager.get_session("admin"))
    # The question the driver asks is the DUTY, not the domain: a workbench runs research, broadcast
    # AND operational processes, and only the workload knows which guarantee it needs.
    check("a workload that DECLARES `duty: continuous` gets the continuity rules",
          wl_state.continuous({"duty": "wb:duty:continuous"}))
    check("a workload that declares nothing does not (best effort, the default)",
          not wl_state.continuous({}))
    check("an operational workload claims the duty with no station anywhere in the question — the "
          "driver reads the DUTY, never the domain",
          wl_state.continuous({"duty": "wb:duty:continuous", "effect": "record"}))

    # A GATE THAT STOPS A PROGRAMME MUST SAY SO — silence without a reason is the defect §4 names,
    # and a stop names ITSELF, in vocabulary, at the place that decided it (workbench doctrine 3).
    # It used to say so by STAMPING `station:reason:<id>` onto the guide row: the platform writing
    # an application word into an application namespace, which is the fault the 2026-09-23 ruling
    # is about. The stop is REPORTED, with the platform's own id and untranslated, and the station
    # composes whatever sentence it shows from `workload.status`.
    import logging as _logging

    class _Cap(_logging.Handler):
        def __init__(self):
            _logging.Handler.__init__(self)
            self.lines = []

        def emit(self, rec):
            try:
                self.lines.append(rec.getMessage())
            except Exception:
                pass

    _cap = _Cap()
    _lg = _logging.getLogger("Akasha.Kernel")
    _lg.addHandler(_cap)
    _lg.setLevel(_logging.INFO)
    try:
        for reason in ("waiting_source", "runs_per_day", "breaker"):
            _cap.lines = []
            wl_state.gate(k, gid, space, reason, pol=_W.policy(st))
            check("a %s gate REPORTS itself, with its id untranslated" % reason,
                  any("stood by" in l and "reason=%s" % reason in l
                      and "%s/%s" % (gid, space) in l for l in _cap.lines),
                  str(_cap.lines)[:120])
        _st_g = ((d(tok, "workload.status", {"key": _key}, trust="network") or {})
                 .get("result")) or {}
        check("… and it stamps NO application status: the answer still carries no `state`, and no "
              "reason in the station's namespace",
              "state" not in _st_g
              and not str((_st_g.get("last") or {}).get("reason") or "").startswith("station:reason:"),
              str(sorted(_st_g.keys())))
    finally:
        _lg.removeHandler(_cap)

    # the breaker must not unschedule a broadcaster
    st4 = sc2.read_autorun(gid, space) or {}
    check("the programme is still armed after a breaker report", st4.get("mode") == "auto",
          "mode=%s" % st4.get("mode"))

    # §1 — a boot run that aired nothing, for a reason a RETRY CAN FIX, leaves the deploy still
    # owing an airing. The reason comes from the run's own record — the LLM gateway's outcome on
    # its own observation of a model call — and the retry ladder is keyed on the platform's own
    # transient terms. It used to be keyed on a reason the DRIVER supplied when the op gave none
    # (`no_text`), which is the P2 substitution: every empty run, including on workloads that call
    # no model at all, was retried as though a model had answered with nothing.
    # The OUTCOME is stubbed at `run_effect`, which is the one seam the ladder reads. Recording a
    # bench row instead would not reach it: a run's outcome is read from the rows of THAT RUN
    # (`since=`), and a row written before the tick belongs to the run before it — which is the
    # point of the window and not something to work around here. What is under test is the
    # ladder's KEYING, and this drives it with the two outcomes that decide it.
    _real_outcome = wl_state.run_effect

    def _boot_tick(reason):
        stB = dict((sc2.read_autorun(gid, space) or {}).get("state") or {})
        stB["boot_pending"] = True
        stB.pop("boot_tries", None)
        stB.pop("retry_at", None)
        sc2.write_autorun_state(gid, space, stB)
        wl_state.run_effect = lambda *a, **kw: (0, reason)
        try:
            autorun.bench_autorun_tick(k)
        finally:
            wl_state.run_effect = _real_outcome
        return (sc2.read_autorun(gid, space) or {}).get("state") or {}

    stC = _boot_tick(wl_state.REASON_LLM_POOL)
    check("a boot run that aired nothing for a TRANSIENT reason RE-OPENS the boot gate (the deploy "
          "still owes one)",
          bool(stC.get("boot_pending")) and int(stC.get("boot_tries", 0)) >= 1,
          "boot_pending=%s tries=%s" % (stC.get("boot_pending"), stC.get("boot_tries")))
    check("… bounded, so a provider that is down cannot make it a loop",
          wl_state.BOOT_AIRING_TRIES and int(stC.get("boot_tries", 0)) <= wl_state.BOOT_AIRING_TRIES,
          "tries=%s cap=%s" % (stC.get("boot_tries"), wl_state.BOOT_AIRING_TRIES))
    # …and a run whose op named NO reason is NOT retried: no clock fixes a reason the platform was
    # never given, so it waits for the next trigger (ruling 2026-09-23 §2, retry policy).
    stD = _boot_tick("")
    check("a run whose op gave NO reason is not retried — it waits for the next trigger, rather "
          "than being retried under a reason the platform invented",
          not stD.get("boot_tries"), "tries=%s" % stD.get("boot_tries"))

    print("\n  ── §1 beats §2: a programme that has NEVER AIRED airs at boot ──")
    # The 2026-09-20 regression, held shut. The driver skipped the boot airing as `fresh` because
    # `last_run` was 81,208 s old against an 86,400 s interval — but the programme had never AIRED
    # once (today=0, airing=null, state=warming_up). A run that aired nothing is not an airing, and
    # the ruling measures `fresh` against the AIRING. So: a stamped `last_run` with no airing must
    # NOT close the boot gate, and a real recent airing must.
    st2 = sc2.read_autorun(gid, space).get("state") or {}
    check("the programme under test has never produced its effect",
          wl_state.last_effect_at(k, _key) == 0.0, "last_effect_at=%s" % wl_state.last_effect_at(k, _key))
    st2["last_run"] = time.time() - 60          # ran a minute ago, aired nothing
    st2["boot_pending"] = True
    sc2.write_autorun_state(gid, space, st2)
    acts = autorun.bench_autorun_tick(k)
    mine = [a for a in acts if a.get("society") == "%s/%s" % (gid, space)]
    check("a recent RUN that aired nothing does not skip the boot airing as `fresh`",
          not any(a.get("reason") == "fresh" for a in mine), str(mine)[:120])

    # …and the idempotence rule still holds where it is meant to: a REAL effect minutes ago does
    # skip. `fresh` is measured against the PLATFORM'S OWN RUN RECORD (group 4, 4.12(a)) — the
    # newest run that produced its effect — so the record is written the way the driver writes it.
    wl_state.record_run(k, _key, at=time.time() - 60, ok=True, effect_count=1, by="eval")
    st3 = sc2.read_autorun(gid, space).get("state") or {}
    st3.pop("retry_at", None)                  # due now: the boot gate is what is under test
    st3["boot_pending"] = True
    sc2.write_autorun_state(gid, space, st3)
    acts = autorun.bench_autorun_tick(k)
    mine = [a for a in acts if a.get("society") == "%s/%s" % (gid, space)]
    check("a REAL effect minutes ago still skips the boot run as `fresh` (§2 intact)",
          any(a.get("reason") == "fresh" for a in mine),
          "last_effect_at=%.0f acts=%s" % (wl_state.last_effect_at(k, _key), str(mine)[:80]))

    print("\n  ── a run that produced NOTHING is not counted as its effect ──")
    # The shelf's five turns each stand by on their own when the model is refused, and the JOB still
    # succeeds. The driver used to assert one airing for any successful job. The effect is now read
    # through the op the DECLARATION names (4.12(b)) — here the application's own row reader, named
    # by this fixture exactly as a publishing declaration names it.
    from app.concepts.bench_station import BenchStationConcept as _BS
    bs = _BS(k.manager.get_session("admin"))
    bench = (sc2.read_autorun(gid, space) or {}).get("bench") or gid
    _bn = bench[3:] if str(bench).startswith("wb:") else bench
    _pol = {"workload": _key, "effect_read": {
        "op": "station.air.ls", "args": {"name": _bn, "limit": "1000"},
        "rows": "aired", "effect": "aired", "reason": "reason", "at": "at"}}
    check("the declared effect read reaches the bench's record", wl_state.effect_rows(k, _pol) is not None)
    t0 = time.time(); time.sleep(0.01)
    bs.op_air(name=bench, source="a passage", provider="mistral", model="m", turn="reader",
              aired="0", reason="budget_calls")
    n, why = wl_state.run_effect(k, _pol, since=t0)
    check("a run whose turns all stood by reports ZERO effect", n == 0, "n=%s" % n)
    check("… and carries the reason its turns recorded VERBATIM, not a guess and not a restatement",
          why == "budget_calls", why)
    t1 = time.time(); time.sleep(0.01)
    bs.op_air(name=bench, source="a passage", provider="mistral", model="m", turn="reader", aired="1")
    n2, why2 = wl_state.run_effect(k, _pol, since=t1)
    check("a run that DID produce it reports its effect", n2 == 1 and not why2, "n=%s why=%r" % (n2, why2))
    check("a workload that declares no effect read keeps one-run-one-effect",
          wl_state.run_effect(k, {"workload": _key}, time.time()) == (1, ""))

    print("\n  ── EVERY declared workload, not just the first ──")
    # The station carries four driven programmes since 2026-09-21. A boot that provisions one of
    # them and quietly skips the rest is a deploy that looks fine and is three quarters silent —
    # exactly the failure the airing ruling is about — so the pass is asserted over the whole
    # declaration set rather than over `declared[0]`. (Merged from the frontend's version of this
    # check; the loop is the same question asked of the new shape, where a "studio" is a workload
    # and its row is found by SID because all four now share one group.)
    check("the declaration set carries every driven programme", len(declared) >= 4,
          "driven=%s" % [_W.key(x) for x in declared])
    for x in declared:
        g, sp_ = _W.society_of(x)
        try:
            m = sc.read_autorun(g, sp_)
        except Exception as exc:
            m = {"mode": "", "raised": str(exc)[:70]}
        check("%s is armed after ONE boot pass" % _W.key(x), m.get("mode") == "auto",
              m.get("raised") or ("mode=%s" % m.get("mode")))
        # EVERY workload ANSWERS, and whether it has a ROOM is a DECLARATION field, not a row.
        # This used to look for a stamped guide row and to treat its presence as the answer to
        # "does this workload have a room" — two predicates for one question, which is P4. The
        # register is deleted; `workload.status` answers for all of them alike, and
        # `publishes_to_room` is the one predicate for the room.
        _stx = ((d(tok, "workload.status", {"key": _W.key(x)}, trust="network") or {})
                .get("result")) or {}
        check("… and the platform answers for it (no `state`, the gate's own term)",
              _stx.get("declared") is True and "state" not in _stx and "gate" in _stx,
              "%s keys=%s" % (_W.key(x), sorted(_stx.keys())))
        check("… and whether it has a ROOM is read from its declaration, once",
              _W.publishes_to_room(x) == (x.get("effect") == "publish" and not (x.get("pins") or {}).get("channel")),
              "%s room=%s channel=%s" % (_W.key(x), _W.publishes_to_room(x),
                                         (x.get("pins") or {}).get("channel")))
        _br = _W.branch_of(x)
        _e = ((d("admin", "wf.ls", {"bench": _W.bench_slug(x), "branch": _br}) or {})
              .get("result") or {}).get("entries") or []
        check("… and its cycle is on its OWN branch of the shared bench (none overwrote another)",
              len(_e) > 0, "%s/%s entries=%d" % (_W.bench_slug(x), _br, len(_e)))

    print("\n  ── a declaration that is not provisionable is refused, by name ──")
    check("a workload whose template is missing resolves to no path — it is refused rather than "
          "armed onto a bench with no workflow",
          _wp.template_path(dict(st, workflow="no_such_template")) == "")
    check("a workload missing a frozen field is reported as that field's id",
          _W.problems({x2: v for x2, v in st.items() if x2 != "budget"}) == ["budget"],
          str(_W.problems({x2: v for x2, v in st.items() if x2 != "budget"})))

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a fresh cell provisions EVERY declared workload at boot and makes each "
          "ANSWERABLE through `workload.status`, armed from its declaration, connected to the bench "
          "and on its own branch of it, with no operator; a gate that stops one reports itself in "
          "the vocabulary and stamps no application status; a second boot changes nothing; a "
          "declaration that is not provisionable is refused by field name rather than "
          "half-applied.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
