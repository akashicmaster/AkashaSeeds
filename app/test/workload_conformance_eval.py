#!/usr/bin/env python3
"""
Seed A slice 1 §1.8 — a DECLARATION, end to end, on a fresh store. Run against all four real ones.

The frontend landed the four station workloads before this seed's platform existed, so there is no
fixture: **the four real declarations are the fixture**, which is a better test than one I could
write to fit my own code. The scenario is the order's:

    fresh store → boot → the provisioned line → the Sets → the armed policy → the workflow on the
    declared bench and branch → the guide row with a state → a SECOND boot that changes nothing →
    a driver decision that writes a reason id → the expected log lines present

What it does NOT do is call a model. A turn that produces text is the turn op's business (and that
op is the frontend's); everything above is the platform's, and all of it is decidable without a
provider. The one place that would have needed one — "the effectful step" — is rehearsed instead:
the eval asserts the admission path would reserve the DECLARED appetite under the DECLARED key,
which is the fact that matters and the one a provider outage would otherwise hide.

    python test/workload_conformance_eval.py                 # all four declarations
    python test/workload_conformance_eval.py news_show       # one

Exit 0 = all pass.
"""
import hashlib
import json
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def _cell(cap):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="wl_conf_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    k.dispatch({"jsonrpc": "2.0", "method": "world.genesis",
                "params": {"session_token": "admin", "data": {}}, "id": "w"}, "local")
    return k


def _d(k, method, data, who="admin"):
    r = k.dispatch({"jsonrpc": "2.0", "method": method,
                    "params": {"session_token": who, "data": data}, "id": "t"}, "local")
    return r.get("result") if "result" in r else {"__error__": r.get("error")}


def _soc_rows(k):
    """(gid, name) for every armed society."""
    from lib.akasha.concepts.society import SocietyConcept
    try:
        sc = SocietyConcept(k.manager.get_session("system.broadcaster"))
        return [((r.get("gid"), r.get("name")), r) for r in sc.list_auto_societies()]
    except Exception:
        return []


def main():
    want = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    from lib.akasha.api import gate as G
    from lib.akasha.workbench import workload as W
    from lib.akasha.workbench import wl_state, provision, workload_provision
    from lib.akasha.workbench import workload_provision as _wp
    from lib.akasha.workbench import autorun as _autorun

    decls = [d for d in W.declarations(None) if not want or str(d.get("workflow")) == want]
    print("=" * 78)
    print("Workload conformance — %d declaration(s), fresh store, no model call" % len(decls))
    print("=" * 78)
    if not decls:
        print("no declaration matches %r" % want); sys.exit(2)

    # ── one cell, all four: provisioning is per-workload and the bench is shared, which is itself
    #    part of what is under test (four workloads must not overwrite each other's branch).
    cap = _Capture()
    kl = logging.getLogger("Akasha.Kernel")
    old = kl.level
    kl.addHandler(cap); kl.setLevel(logging.INFO)
    try:
        k = _cell(cap)
        first = provision.provision_workloads(k)
        k._workload_decl_cache = None                 # a second boot re-reads the files, as it would
        second = provision.provision_workloads(k)
    finally:
        kl.removeHandler(cap); kl.setLevel(old)

    by_key = {r.get("workload"): r for r in first}
    by_key2 = {r.get("workload"): r for r in second}

    for decl in decls:
        key = W.key(decl)
        gid, space = W.society_of(decl)
        bench, branch = W.bench_slug(decl), W.branch_of(decl)
        print("\n  ── %s (%s) ──" % (key, decl.get("_file")))
        rep, rep2 = by_key.get(key) or {}, by_key2.get(key) or {}

        # 1. the declaration is well-formed against the frozen shape
        check("[%s] the declaration carries the nine frozen fields" % key,
              W.problems(decl) == [], str(W.problems(decl)))

        # 2. it provisioned, and said so in one line carrying the five fields
        check("[%s] provisioned from a fresh store" % key, rep.get("status") == "provisioned",
              str(rep.get("reason") or rep)[:90])
        line = [l for l in cap.lines if "provisioned workload=%s " % key in l]
        check("[%s] one `[bench] provisioned` line naming society, workflow, trigger, duty, effect"
              % key,
              len(line) >= 1 and all(t in line[0] for t in
                                     ("society=%s/%s" % (gid, space), "workflow=%s" % decl.get("workflow"),
                                      "trigger=", "duty=%s" % W.duty(decl), "effect=%s" % W.effect(decl))),
              (line[0][:150] if line else "no line"))

        # 3. every field is a membership on the workload atom — the declaration, as data
        sets = _d(k, "set.ls", {"name": "set:wl:effect:%s" % W.effect(decl)})
        names = W.field_sets(decl)
        missing = []
        for nm in names:
            got = _d(k, "set.ls", {"name": nm})
            if not (got or {}).get("members"):
                missing.append(nm)
        check("[%s] every declared field is a `set:wl:*` membership (%d Sets)" % (key, len(names)),
              not missing, "missing=%s" % missing[:3])

        # 4. armed, with the policy the declaration projects — the five fields, verbatim
        from lib.akasha.concepts.society import SocietyConcept
        sc = SocietyConcept(k.manager.get_session("admin"))
        info = sc.read_autorun(gid, space) or {}
        pol = info.get("policy") or {}
        check("[%s] armed mode=auto with the declared policy" % key,
              info.get("mode") == "auto" and pol.get("workload") == key, str(info)[:110])
        check("[%s] the policy carries duty, effect, trigger, appetite and budget" % key,
              wl_state.continuous(pol) == W.is_continuous(decl)
              # NOT `effect == publish` (P4, ruling 2026-09-23). That is a different question and
              # this line asserted the conflation: `news_show_x` declares `effect: publish` and a
              # channel pin, so it publishes and has NO room. `publishes_to_room` is the one
              # predicate, the policy carries its answer, and the two must agree with each other
              # rather than with the effect.
              and wl_state.publishes(pol) == W.publishes_to_room(decl)
              and wl_state.interval_of(pol) == W.interval_s(decl)
              and pol.get("trigger") == ("boot" if W.trigger(decl)["boot"] else "manual")
              and (pol.get("appetite") or {}).get("llm_calls_per_run")
                  == W.appetite(decl)["llm_calls_per_run"]
              and (pol.get("budget") or {}).get("runs_per_day") == W.budget(decl)["per_day"],
              "duty=%s iv=%s appetite=%s" % (pol.get("duty"), wl_state.interval_of(pol),
                                             pol.get("appetite")))

        # 5. the cycle is on the DECLARED bench and its own branch — four on one bench, no overwrite.
        # A LAB declares `workflows` (a list, backend-needs-platform-2026-09-26c §2): each listed
        # name is its own branch, and the provisioning report's `entries` is their sum.
        branches = list(decl.get("workflows") or [branch])
        wfs = [(b, _d(k, "wf.ls", {"bench": bench, "branch": b}) or {}) for b in branches]
        counts = {b: len(w.get("entries") or []) for b, w in wfs}
        n_entries = sum(counts.values())
        check("[%s] the template is loaded on wb:%s branch %s (%d entries)"
              % (key, bench, ",".join(branches), n_entries),
              all(counts.values()) and rep.get("entries") == n_entries,
              "wf.ls=%s report=%s" % (counts, rep.get("entries")))
        check("[%s] the policy runs THAT branch (the driver and the loader cannot drift)" % key,
              list(pol.get("workflows") or [])[:len(branches)] == branches, str(pol.get("workflows")))
        body = " ".join(str(e.get("body") or "") for _b, w in wfs for e in (w.get("entries") or []))
        check("[%s] the template's `$params` were substituted, not written literally" % key,
              "$" not in body, body[:110])

        # 6. THE STATUS THE PLATFORM ANSWERS — and no state word in it.
        #
        # This asked `society.station` for a guide ROW and asserted its `state` ended in
        # `warming_up` / `on_air` / `standing_by` / `rebroadcast`. That register is deleted and
        # those four words are the STATION's, for the station's own surface (ruling 2026-09-23):
        # a platform that stamps them is deciding what an application's status MEANS. What the
        # platform owes is what it RECORDED and what the GATE answers; the sentence is composed by
        # the station Concept Model and the room pages from exactly these fields.
        st = _d(k, "workload.status", {"key": key}) or {}
        check("[%s] workload.status answers for the declared key" % key,
              st.get("declared") is True and st.get("key") == key, str(st)[:140])
        check("[%s] …with `last` (what was recorded) and `gate` (what the gate answers), and NO "
              "`state` field — the words are the application's" % key,
              "last" in st and "gate" in st and "state" not in st, sorted(st.keys()))
        _term = str((st.get("gate") or {}).get("run") or "")
        check("[%s] …and the gate's answer is `ok` or one of ITS OWN terms, never a station word"
              % key,
              _term == "ok" or _term in G.REASONS,
              "run=%r (vocabulary: ok | %s)" % (_term, "|".join(G.REASONS[:4])))
        _reason = str((st.get("last") or {}).get("reason") or "")
        check("[%s] …and `last.reason` is the op's own string or EMPTY — the platform never "
              "substitutes one (P2: `no_text` was stamped on runs that called no model)" % key,
              _reason == "" or not _reason.startswith("station:reason:"),
              "reason=%r" % _reason)

        # 6b. the CASTS work: the client the declaration names speaks as a cast the declaration
        # names, into the space the declaration names — one turn, from an empty store, right after
        # provisioning (step 2 §1). This is what "provisioned" has to mean: a programme that cannot
        # say its own turn is armed and mute, and the log looks identical either way. No model is
        # involved — the point is that the TURN lands, not the words.
        #
        # What this asked before the one-gate ruling, and why it changed: it asked whether the
        # programme OWNED the cast (`cast.ls who=<programme>`). It does not, and must not —
        # provisioning runs as `admin` from one authority, so the casts belong to the WORKLOAD, and
        # the right to speak as one is ruling §1 step 4 (a cast the target declares, or the
        # speaker's own identity), not ownership. The check that matters is therefore the one below:
        # the declared cast is ON THE ROSTER of the declared space, and the declared client's turn
        # as that cast is ADMITTED and reaches the feed stamped with it.
        _roles = decl.get("roles") if isinstance(decl.get("roles"), dict) else {}
        if _roles:
            _prog = W.client_of(decl)
            _role0, _spec0 = sorted(_roles.items())[0]
            _cast0 = str((_spec0 or {}).get("cast") or _role0.split(".", 1)[0])
            _members = ((_d(k, "society.roster", {"group": gid, "space": space}, who=_prog) or {})
                        .get("casts") or [])
            _cid = next((m.get("cast_id") for m in _members
                         if str(m.get("name") or "") == _cast0), "")
            check("[%s] the declaration's cast is on the roster of its own space (%s)" % (key, _cast0),
                  bool(_cid), "roster=%s" % [m.get("name") for m in _members])
            _said = _d(k, "society.say", {"group": gid, "space": space, "cast": _cid,
                                          "text": "conformance: one turn."}, who=_prog) or {}
            check("[%s] …and it says one turn into its own space" % key,
                  bool(_said.get("key")) and not _said.get("error"), str(_said)[:120])
            _feed = _d(k, "society.feed", {"group": gid, "space": space, "limit": 5},
                       who=_prog) or {}
            _msgs = _feed.get("messages") or []
            check("[%s] …and the feed carries it, stamped with that cast" % key,
                  any("conformance: one turn." in str(m.get("text") or "") for m in _msgs)
                  and any(m.get("from_cast") == _cid for m in _msgs),
                  "%d message(s)" % len(_msgs))

        # 7. a SECOND boot changes nothing — a declaration is a desired state, reconciled.
        #
        # The row count is gone from this check because the ROW is gone: provisioning wrote a
        # `station:show:*` register and a second pass had to be shown not to double it. Nothing is
        # stamped now, so what has to hold is that the reconciled state is identical — the same
        # entries on the same branch, still armed, and one answer from `workload.status`.
        n2 = sum(len((_d(k, "wf.ls", {"bench": bench, "branch": b}) or {}).get("entries") or [])
                 for b in branches)
        st2 = _d(k, "workload.status", {"key": key}) or {}
        check("[%s] a second boot is a no-op: same entries, same status, still armed" % key,
              rep2.get("status") == "provisioned"
              and n2 == n_entries
              and st2.get("declared") is True and st2.get("society") == st.get("society")
              and rep2.get("armed"),
              "entries %d→%d society=%s" % (n_entries, n2, st2.get("society")))

        # 8. a gate that stops a run does NOT name the application's status.
        #
        # This used to assert that `wl_state.gate` wrote `station:reason:runs_per_day` onto the
        # guide row "a listener reads" — the platform writing an application word into an
        # application namespace, which is the fault this ruling names. The gate records; the
        # station composes. What must hold is that after a stop, `workload.status` still answers in
        # the platform's own vocabulary and still carries no `state`, and that the recorded reason
        # is the op's own string, never one the platform put there.
        wl_state.gate(k, gid, space, wl_state.REASON_RUNS_PER_DAY, pol=pol)
        st4 = _d(k, "workload.status", {"key": key}) or {}
        _term4 = str((st4.get("gate") or {}).get("run") or "")
        _reason4 = str((st4.get("last") or {}).get("reason") or "")
        check("[%s] a gate's stop leaves the status in the platform's OWN vocabulary — no `state`, "
              "no station word" % key,
              "state" not in st4 and (_term4 == "ok" or _term4 in G.REASONS)
              and (_reason4 == "" or not _reason4.startswith("station:reason:")),
              "run=%r reason=%r keys=%s" % (_term4, _reason4, sorted(st4.keys())))

        # 9. the effectful step, REHEARSED: admission would reserve the declared appetite under the
        #    declared key. No provider is called; what is checked is the derivation, which is the
        #    part a provider outage would hide.
        prog, cpr = W.workload_appetite(k, bench, branch)
        check("[%s] admission derives the DECLARED key and appetite from (bench, branch) — not "
              "from whoever submits the job" % key,
              prog == key and cpr == W.appetite(decl)["llm_calls_per_run"],
              "%s calls=%s" % (prog, cpr))

    # ── the shared bench: four workloads, four branches, one count ────────────────────────────
    # ── §1: the driver acts as the workload's declared client ──────────────────────────────────
    # AFTER the per-declaration loop, and deliberately: the negative case ticks the DRIVER, which
    # runs every armed society on the cell, so inside the loop it changed the state of workloads
    # the loop had not reached yet (news_show_x grew a guide row from a sibling's tick). A test
    # whose result depends on which declaration ran first is not testing what it says it is.
    print("\n  ── the driver's identity (§1) ──")
    _pub = [d for d in decls if W.publishes_to_room(d) and (d.get("roles") or {})]
    if _pub:
        decl = _pub[0]
        _dk = W.key(decl)
        gid, space = W.society_of(decl)
        _prog = W.client_of(decl)
    # 6c. THROUGH THE DRIVER. 6b proves the client OWNS its cast; this proves the DRIVER acts
    # as that client — the run is produced by dispatching `society.run` exactly as
    # `autorun.py` does, not by calling `society.say`. The two are not the same claim: the
    # driver ran every workload as `admin` until 2026-09-22 §1, so a workload whose casts
    # belonged to its declared client was armed, provisioned, guide-listed — and mute.
    #
    # What is asserted is the IDENTITY the run carries, not the words. On a fresh store the
    # turn refuses at `source=next` (no episode pack), so no line is produced and no model is
    # called — which is correct, and is why the say itself is 6b's. What this adds is that the
    # run is ADMITTED and EXECUTES: before the companion fix in `admission.handle_job_submit`,
    # running as the declared client was refused `-32003 job.submit requires admin or
    # librarian` and every programme died with `no job id`. The job's OWNER is the identity
    # every step re-authenticates as — so it is the identity a say WOULD carry.
    if True:
        _rr = _d(k, "society.run", {"group": gid, "name": space,
                                    "workflow": W.branch_of(decl)}, who=_prog) or {}
        check("[%s] the DRIVER's dispatch is ADMITTED for the declared client (%s)" % (_dk, _prog),
              not _rr.get("__error__") and bool(_rr.get("job_id")),
              str(_rr.get("__error__") or _rr)[:140])
        check("[%s] …and the run EXECUTED its steps (not refused at submission)" % _dk,
              _rr.get("job_status") == "DONE" and int(_rr.get("minted") or 0) > 0,
              "job_status=%s minted=%s" % (_rr.get("job_status"), _rr.get("minted")))
        _job = (_d(k, "job.stat", {"job_id": _rr.get("job_id")}) or {})
        check("[%s] …owned by the declared client, which is the identity every step ran as" % _dk,
              str(_job.get("owner") or "") == _prog,
              "owner=%s" % _job.get("owner"))

        # …and the negative. Re-point the declaration's client at somebody else: the casts
        # belong to the original client, so this one owns none of them. The run must not reach
        # the model — a turn that cannot be said must not be paid for first. The fresh-interval
        # gate is cleared first, or the tick would skip for `fresh` and the check would pass
        # while proving nothing.
        import lib.akasha.workbench.llm_provider as _lp
        _gen_calls = []
        _real_gen = _lp.generate
        _lp.generate = lambda *a, **kw: (_gen_calls.append(a[:2]) or "never produced")
        _alien = dict(decl)
        _sp = dict(_alien.get("space") or {})
        _sp["client"] = "llm:programme:not_the_owner"
        _alien["space"] = _sp
        _real_for_society = W.for_society
        W.for_society = lambda _k, _g, _s: (_alien if (_g, _s) == (gid, space)
                                            else _real_for_society(_k, _g, _s))
        from lib.akasha.concepts.society import SocietyConcept as _SC
        _sc = _SC(k.manager.get_session("system.broadcaster"))
        _stn = dict((_sc.read_autorun(gid, space) or {}).get("state") or {})
        _stn.pop("last_run", None); _stn.pop("retry_at", None)
        _stn["boot_pending"] = True
        _sc.write_autorun_state(gid, space, _stn)
        # …and the FRESH gate is stood down for this one tick. 6b and the gate checks above
        # stamped an airing minutes ago, so the driver would skip `fresh` before it ever looked
        # at the casts — and the "model not called" check would then pass while proving
        # nothing. The gate under test is the ownership one; this is the only way to reach it.
        _real_last = wl_state.last_effect_at
        wl_state.last_effect_at = lambda *_a, **_kw: 0.0   # the fresh clock, stood down
        try:
            _acts = _autorun.bench_autorun_tick(k)
            _mine = [a for a in _acts if a.get("society") == "%s/%s" % (gid, space)]
            check("[%s] a client that owns none of the declared casts attempted and did not air"
                  % _dk,
                  bool(_mine) and all(a.get("reason") != "fresh" for a in _mine)
                  and not any(a.get("action") == "ran" and a.get("ok") for a in _mine),
                  str(_mine)[:180])
            check("[%s] …and the model was NOT called for a turn that cannot be said" % _dk,
                  not _gen_calls, "%d call(s)" % len(_gen_calls))
        finally:
            wl_state.last_effect_at = _real_last
            W.for_society = _real_for_society
            _lp.generate = _real_gen

    print("\n  ── the bench they share ──")
    bench = W.bench_slug(decls[0])
    binfo = _d(k, "bench.info", {"name": bench}) or {}
    n_pub = sum(1 for d in W.declarations(None)
                if W.bench_slug(d) == bench and W.effect(d) == W.EFFECT_PUBLISH)
    check("bench.info programmes counts `effect=publish` workloads on the bench, with no kind test",
          binfo.get("programmes") == n_pub, "%s (expected %d)" % (binfo.get("programmes"), n_pub))
    branches = {W.branch_of(d) for d in W.declarations(None) if W.bench_slug(d) == bench}
    check("each workload has its OWN branch on the shared bench (none overwrote another)",
          len(branches) == len([d for d in W.declarations(None) if W.bench_slug(d) == bench]),
          str(sorted(branches)))

    # ── a broken declaration is refused BY FIELD, and provisions nothing ──────────────────────
    print("\n  ── a declaration that is not well-formed ──")
    bad = dict(decls[0]); bad.pop("trigger", None); bad["_file"] = "broken.json"
    # ── an UNDECLARED workload cannot run: the declaration Set is reconciled to the files ──────
    # (the purge order §2: `retire_undeclared` and its retired rows are gone). A declaration that
    # disappears drops its key from `set:wl:declared` on the next pass, and the gate's step 4 refuses
    # its run `declared` — the society, its feed and its bench stand untouched; nothing is retired.
    from lib.akasha.api import gate as _G
    _k = _cell(None)
    provision.provision_workloads(_k)              # the real pass, so the workload is declared + armed
    _d0 = decls[0]
    _key0 = W.key(_d0)

    def _run_gate():
        return _G.gate(W.client_of(_d0), _G.RUN, _key0, place=W.client_places(_d0)[0])
    _ok0, _why0 = _run_gate()
    check("…(setup) while declared, the gate does not refuse the run as undeclared",
          _why0 != _G.R_DECLARED, "%s %s" % (_ok0, _why0))
    _real = W.declarations
    W.declarations = lambda *_a, **_kw: []
    try:
        provision.provision_workloads(_k)
    finally:
        W.declarations = _real
    _ok1, _why1 = _run_gate()
    check("a workload whose declaration is gone is refused `declared` by the gate on the next pass",
          not _ok1 and _why1 == _G.R_DECLARED, "%s %s" % (_ok1, _why1))
    _gid0, _space0 = W.society_of(_d0)
    _info = (_d(_k, "society.info", {"group": _gid0, "space": _space0}) or {})
    check("…and nothing is retired or deleted: its society stands",
          bool(_info.get("society_id")) and not _info.get("__error__"), str(_info)[:120])
    check("…and the retire functions are gone (one mechanism: the declaration Set)",
          not hasattr(provision, "retire_undeclared") and not hasattr(provision, "retire_undeclared_benches"))

    check("a missing field is reported as its own id, not as `invalid`",
          W.problems(bad) == ["trigger"], str(W.problems(bad)))
    noclient = json.loads(json.dumps(decls[0])); (noclient.get("space") or {}).pop("client", None)
    check("a declaration without `space.client` is refused (`space`) — the platform invents no client "
          "id (the purge order §2: no legacy `llm:programme:<workflow>` default)",
          "space" in W.problems(noclient) and W.client_of(noclient) == "", str(W.problems(noclient)))
    no_tpl = dict(decls[0]); no_tpl["workflow"] = "no_such_template"
    check("a workload with no template resolves to no path (it is refused rather than armed with "
          "a bench that has no workflow)", workload_provision.template_path(no_tpl) == "")

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — each declaration provisions itself from a fresh store, says so in one "
          "line carrying its five fields, becomes Sets and an armed policy and a cycle on its own "
          "branch of the shared bench, shows a state to a listener, reconciles to a no-op on the "
          "next boot, writes a reason id when a gate stops it, and derives its own accounting key "
          "and appetite at admission.")
    sys.exit(0)


if __name__ == "__main__":
    main()
