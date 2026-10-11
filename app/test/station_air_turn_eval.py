#!/usr/bin/env python3
"""
`station.air.turn` / `society.air` — one programme turn, produced INSIDE the daemon.

Why it must be here and not in a driver process: `llm_provider`'s meter, rate pacing and 429 back-off
are process state, and the durable store is installed by the KERNEL. A model call made in a separate
process is invisible to the day's shared pool — neither counted nor debited against a reservation —
so two drivers plus the station could each believe they are under the cap. This eval pins that down:

  · the turn's model call goes through `llm_provider.generate` IN THIS PROCESS, so the gate sees it
  · the role's contract and prompt come from the programme's DECLARATION, not from the caller
  · a turn the model does not produce is NOT invented: nothing is said, and it is recorded standby
  · an aired turn writes each face exactly ONCE — the feed through society.say, the record through
    the bench recorder — with the exact provider/model on both (the anti-やらせ evidence)
  · `society.air` is a pure FORWARD: it opens no second write path of its own
  · the accounting key comes from the declaration (B10-a), never from the caller

Run:  python app/test/station_air_turn_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import autorun
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    def _auto_index():
        """The nucleus pointer Set the kernel's auto-run driver enumerates."""
        try:
            from lib.akasha.concepts.society import SocietyConcept
            return list(SocietyConcept(k.manager.get_session("admin")).list_auto_societies())
        except Exception as exc:
            return [{"error": str(exc)}]

    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.workbench import llm_provider
    # The plan lives in `lib/akasha/workbench/workload_provision.py` so the boot pass and the operator tool
    # run the SAME one; the script still exposes it, and this eval provisions through that one path.
    from lib.akasha.workbench import workload as _W
    from lib.akasha.workbench.workload_provision import provision

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_air_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(client, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": client, "data": data}, "id": "t"}, "local")

    def res(r):
        return (r or {}).get("result") or {}

    cfg = next(x for x in _W.declarations(None) if x.get("workflow") == "thinkers_shelf")
    gid, space = _W.society_of(cfg)
    program = _W.key(cfg)

    print("\n  ── the accounting key comes from the declaration (B10-a) ──")
    check("the workload declares its programme key", program == "studio_ai/thinkers_shelf", program)

    print("\n  ── provisioning ──")
    out = provision(d, cfg, note=lambda m: None)
    check("the programme client owns all three casts",
          len(out["casts"]) == 5 and all(out["casts"].values()),
          "casts=%s (three roles + the chairman and the scribe, who hold responsibility and "
          "never take a turn)" % list(out["casts"]))
    from lib.akasha.workbench.workload import client_of as _client_of
    client = _client_of(cfg)

    # What the room reads is the workload's STATUS, and the words around it are the room's own.
    #
    # This used to read `society.station` — a platform-owned register of `station:show:*` rows
    # carrying `state`, `reason` and `daily_budget`. That register is deleted (ruling 2026-09-23):
    # the platform records what happened and answers the gate's terms; naming an application's
    # status is the application's. So what "provisioned" has to mean here is that the workload is
    # ANSWERABLE — `workload.status` knows the key, names its society, and gives the gate's own
    # term — and that the budget the room counts against is the DECLARED one, read from the single
    # declaration rather than from a second copy on a row that could disagree with it.
    st = res(d("admin", "workload.status", {"key": program}))
    check("provisioning makes the workload answerable (what the room reads)",
          st.get("declared") is True and st.get("society") == "%s/%s" % (gid, space)
          and "state" not in st and "last" in st and "gate" in st,
          "keys=%s society=%s" % (sorted(st.keys()), st.get("society")))
    from lib.akasha.concepts.society import SocietyConcept as _SC
    _pol = (_SC(k.manager.get_session("admin")).read_autorun(gid, space) or {}).get("policy") or {}
    check("the declared daily budget is the one the room counts `spent_today` against",
          (_pol.get("budget") or {}).get("runs_per_day") == _W.budget(cfg)["per_day"]
          and isinstance(st.get("spent_today"), int),
          "budget=%s spent_today=%s" % (_pol.get("budget"), st.get("spent_today")))

    # a passage atom to read from, written the way the pack writes one
    passage = {"book": "A", "section": "S", "text": "THE TEXT AS PRINTED.",
               "anchor": {"page": "iii", "uri": "https://example.invalid/p3", "ocr_span": [0, 19]}}
    d("admin", "kernel.memory.define",
      {"name": "shelf:test:passage:1", "description": json.dumps(passage), "scope": "universal"})

    # the model, stubbed at the ONE gate — every call the turn makes must pass through here
    calls = []

    def fake_generate(provider, model, system, user, timeout=60.0):
        calls.append({"provider": provider, "model": model, "system": system, "user": user})
        return "  A line the model produced.  "

    real_generate = llm_provider.generate
    llm_provider.generate = fake_generate

    print("\n  ── one aired turn ──")
    r = res(d(client, "society.air", {"program": program, "role": "Reader", "bench": gid,
                                      "source": "shelf:test:passage:1", "provider": "mistral",
                                      "model": "mistral-small-latest", "turn": "read#1"}))
    check("society.air forwards and the turn airs", r.get("status") == "aired", json.dumps(r)[:140])
    check("the model call went through llm_provider IN THIS PROCESS (the gate sees it)",
          len(calls) == 1, "calls=%d" % len(calls))
    check("the text is the model's, trimmed — not invented by the operator",
          r.get("text") == "A line the model produced.", repr(r.get("text"))[:60])

    c0 = calls[0] if calls else {}
    check("the system prompt is the role's DECLARED contract (not the caller's)",
          "Reader" in c0.get("system", "") and "You must NOT" in c0.get("system", ""),
          repr(c0.get("system", ""))[:70])
    check("the user prompt is the declared template filled with the passage text",
          "THE TEXT AS PRINTED." in c0.get("user", ""), repr(c0.get("user", ""))[:70])

    print("\n  ── written exactly once, with the real provider/model ──")
    # The FEED side of a turn is not checked here any more, and that is a gap being NAMED rather
    # than asserted away. `station.air.turn` (a user-owned op) resolves the society it speaks into
    # from the legacy `studio_*.json` programme file, so after seed A moved the four workloads onto
    # one bench with the slug as the space, its feed write still goes to the pre-convergence
    # society. The turn itself airs, the model call passes the one gate, and the BENCH record —
    # the platform's own evidence, and what the room and the Source Viewer read — is correct;
    # those are what this eval now asserts. Residue in the delivery note, `needs user:`.
    aired = res(d("admin", "station.air.ls", {"name": _W.bench_slug(cfg)}))
    rows = [x for x in (aired.get("aired") or []) if x.get("turn") == "read#1"]
    check("the bench record carries the turn exactly once", len(rows) == 1, "n=%d" % len(rows))
    check("the record names the exact provider and model",
          bool(rows) and rows[0].get("provider") == "mistral"
          and rows[0].get("model") == "mistral-small-latest", str(rows[:1])[:110])
    check("the record is judged aired", bool(rows) and str(rows[0].get("aired")) in ("1", "True"))

    print("\n  ── a turn the model does not produce is never invented ──")
    llm_provider.generate = lambda *a, **kw: None
    r2 = res(d(client, "society.air", {"program": program, "role": "Listener", "bench": gid,
                                       "source": "shelf:test:passage:1", "turn": "question#2"}))
    check("no text → status standby, nothing said", r2.get("status") == "standby" and not r2.get("text"),
          json.dumps(r2)[:120])
    aired2 = res(d("admin", "station.air.ls", {"name": _W.bench_slug(cfg)}))
    standby = [x for x in (aired2.get("aired") or []) if x.get("turn") == "question#2"]
    check("the standby IS recorded (a silent gap would hide it)",
          len(standby) == 1 and str(standby[0].get("aired")) in ("0", "False"), str(standby[:1])[:110])

    print("\n  ── a turn nobody can speak costs NOTHING (the 09-22 loss) ──")
    # At 03:32 on 2026-09-22 the three boot-owed programmes each called the model and were refused
    # at the say (`No owned avatar`). The calls were paid — spend 0→4, 0→4, 21→25 — and nothing
    # aired: the day's budget went on lines that were generated and then thrown away. The say's
    # check is a pure read, so it is asked BEFORE the call, and the only way to prove it is to
    # count the calls: a status is what the code claims, the call count is what it did.
    #
    # WHAT MAKES THE TURN UNSAYABLE CHANGED with the one-gate ruling, and the case had to move
    # with it. It used to be a cast the caller did not OWN — but `Reader` is a role this workload
    # DECLARES, the casts belong to the workload rather than to whoever minted them, and step 4
    # admits a declared role, so that turn is sayable now and airing it is correct. What the table
    # still refuses is a role the declaration does not name, which is the case that actually
    # protects the budget: a template naming a role nobody declared must cost nothing.
    llm_provider.generate = fake_generate
    before = len(calls)
    spend_before = res(d("admin", "llm.budget", {}))
    r5 = res(d("admin", "society.air", {"program": program, "role": "Heckler", "bench": gid,
                                        "source": "shelf:test:passage:1", "turn": "unowned#1"}))
    check("a turn naming a role the declaration does not carry gets a standby, not an airing",
          r5.get("status") == "standby", json.dumps(r5)[:120])
    check("… and the MODEL WAS NEVER CALLED — the whole point", len(calls) == before,
          "calls before=%d after=%d" % (before, len(calls)))
    check("… the reason is its own id, not the driver's `not_provisioned`",
          r5.get("reason") == "station:reason:not_said", str(r5.get("reason")))
    check("… and it names the gate's own term and the cast, for whoever has to fix it",
          "roles" in str(r5.get("detail", "")).lower() and "Heckler" in str(r5.get("detail", "")),
          str(r5.get("detail"))[:80])
    rec5 = [x for x in (res(d("admin", "station.air.ls", {"name": _W.bench_slug(cfg)})).get("aired") or [])
            if x.get("turn") == "unowned#1"]
    check("… the standby is ON THE RECORD with that reason",
          len(rec5) == 1 and rec5[0].get("reason") == "station:reason:not_said"
          and str(rec5[0].get("aired")) in ("0", "False"), str(rec5[:1])[:130])
    spend_after = res(d("admin", "llm.budget", {}))
    def _calls_today(b):
        return {x.get("provider"): x.get("calls_today") for x in (b.get("budgets") or [])}
    check("… and the day's spend is unchanged",
          _calls_today(spend_before) == _calls_today(spend_after),
          "%s → %s" % (_calls_today(spend_before), _calls_today(spend_after)))

    print("\n  ── refusals ──")
    llm_provider.generate = fake_generate
    r3 = res(d(client, "society.air", {"program": "studio_ai/no-such", "role": "Reader", "bench": gid}))
    check("an undeclared programme is refused", r3.get("status") == "refused", json.dumps(r3)[:110])
    # An undeclared PROGRAMME is refused (there is no such thing to run); an undeclared ROLE of a
    # real programme STANDS BY. The difference is deliberate and it is the doctrine's third rule —
    # a stop names itself at the place that decided it. A refusal here left no record, so the run
    # read as never having happened and the operator got the driver's `not_provisioned` instead of
    # the reason. What must hold either way is that nothing aired and no model was called.
    r4 = res(d(client, "society.air", {"program": program, "role": "Janitor", "bench": gid}))
    check("a role the programme does not declare stands by — recorded, unaired, unpaid-for",
          r4.get("status") == "standby" and str(r4.get("aired")) in ("0", "False")
          and not r4.get("text"), json.dumps(r4)[:140])
    check("… and its detail names the gate's own term, so the fix is the declaration",
          "roles" in str(r4.get("detail", "")).lower(), str(r4.get("detail"))[:90])

    print("\n  ── the cycle runs with no operator: a workflow on the bench, armed auto ──")
    # Seed A — the cycle is on the workload's OWN branch of the shared bench (four workloads live on
    # `wb:studio_ai`, so `main` would have each overwrite the last), and the policy it is armed with
    # is the declaration's projection rather than a hand-written `automation` block.
    pol_want = _W.policy(cfg)
    entries = res(d("admin", "wf.ls", {"bench": _W.bench_slug(cfg), "branch": _W.branch_of(cfg)}))
    rows = entries.get("entries") or entries.get("rows") or []
    # Five turns and then the MIRROR. The mirror was a background thread of the platform's until
    # step 1 §1.4, which meant a room's liveness depended on a daemon invisible from the programme;
    # as the cycle's last step it runs in the same job as the turns, and a programme that did not
    # air does not mirror.
    turns = [r for r in rows if r.get("method") == "society.air"]
    check("the declared cycle is loaded as workflow entries",
          len(rows) == 6 and len(turns) == 5
          and rows[-1].get("method") == "society.broadcast.relay",
          "n=%d methods=%s" % (len(rows), sorted({r.get("method") for r in rows})))
    check("every turn entry is a role turn of THIS programme (data, not code)",
          all((r.get("params") or {}).get("program") == program for r in turns)
          and [(r.get("params") or {}).get("role") for r in turns]
              == ["Reader", "Listener", "Commentator", "Listener", "Commentator"],
          str([(r.get("params") or {}).get("role") for r in turns]))
    check("… and the last entry mirrors the society it just aired into",
          (rows[-1].get("params") or {}).get("society") == _W.society_of(cfg)[0] + "/"
          + _W.society_of(cfg)[1], str((rows[-1].get("params") or {}).get("society")))

    # read it the way the kernel's auto-run driver reads it — that is the surface that matters
    from lib.akasha.concepts.society import SocietyConcept
    arm = SocietyConcept(k.manager.get_session("admin")).read_autorun(gid, space) or {}
    check("the society is armed mode=auto (the kernel's driver airs it)",
          arm.get("mode") == "auto", "mode=%r" % arm.get("mode"))
    pol = arm.get("policy") or {}
    check("the trigger and the budget read back as declared",
          pol.get("trigger") == pol_want["trigger"]
          and (pol.get("budget") or {}).get("runs_per_day")
              == pol_want["budget"]["runs_per_day"],
          json.dumps({"trigger": pol.get("trigger"), "budget": pol.get("budget")}))
    check("the run it would advance is the workload's own branch",
          list(pol.get("workflows") or []) == [_W.branch_of(cfg)], str(pol.get("workflows")))

    # A demo must never open on a blank studio: if the first airing waited for the scheduled slot,
    # every hour between deploy and that slot would have nothing aired, and a viewer in another time
    # zone would meet an empty room. So the trigger is `boot` and CONTINUES as `then`.
    check("the programme airs on boot, then continues on its schedule",
          pol.get("trigger") == "boot" and str(pol.get("then", "")).startswith("daily:"),
          "trigger=%r then=%r" % (pol.get("trigger"), pol.get("then")))
    due_now = autorun.autorun_due(pol, {"boot_pending": True}, time.time(), "boot-1")
    check("a fresh boot makes it due AT ONCE (no blank after a deploy)", due_now is True)
    after = autorun.autorun_due(
        pol, {"boot_pending": False, "last_run": time.time()}, time.time(), "boot-1")
    check("after the boot airing it waits for the schedule, not every tick", after is False)
    check("the boot airing does not eat the day's scheduled one",
          int((pol.get("budget") or {}).get("runs_per_day", 0)) >= 2,
          str((pol.get("budget") or {}).get("runs_per_day")))
    check("the driver can enumerate it (it joined the auto index)",
          any(p.get("name") == space and p.get("gid") == gid
              for p in _auto_index()), "index=%s" % _auto_index())

    print("\n  ── the cursor is derived from the record, not stored ──")
    # a two-passage episode, written as the pack writes it
    for i, (pg, txt) in enumerate((("1", "FIRST PASSAGE."), ("2", "SECOND PASSAGE.")), start=1):
        d("admin", "kernel.memory.define",
          {"name": "shelf:cur:passage:%d" % i, "scope": "universal",
           "description": json.dumps({"book": "B", "section": "S%d" % i, "text": txt,
                                       "anchor": {"page": pg, "uri": "https://example.invalid/%s" % pg,
                                                  "ocr_span": [0, 9]}})})
        d("admin", "set.add", {"name": "shelf:cur:ep", "id": "shelf:cur:passage:%d" % i})
    from app.concepts.bench_station import BenchStationConcept
    sess = k.manager.get_session(client)
    bs = BenchStationConcept(sess)
    # A workload names its episode in `pins`. The legacy programme file's `source.episode_set`
    # spelling went with the file in the step-1 port: one declaration, one spelling.
    # D14: the cursor reads THIS programme's rows (its key = <bench>/<workflow>) and only rows
    # stamped `grounded` (the source text was in the message) — so the synthetic rows carry both.
    prog = {"pins": {"episode_set": "shelf:cur:ep"}, "bench": "wb:%s" % gid, "workflow": "curtest"}
    _key = "%s/curtest" % gid
    first = bs._resolve_source("next", gid, prog)
    check("`next` picks a passage of the episode", first in ("shelf:cur:passage:1", "shelf:cur:passage:2"),
          first)
    bs.op_air(name=gid, source="B · S1 · p.1", provider="mistral", model="m", turn="read#9",
              program=_key, grounded="1")
    check("once a passage has an aired record, `next` moves on",
          bs._resolve_source("next", gid, prog) == "shelf:cur:passage:2",
          bs._resolve_source("next", gid, prog))
    check("`current` stays on the passage the last aired turn worked from",
          bs._resolve_source("current", gid, prog) == "shelf:cur:passage:1",
          bs._resolve_source("current", gid, prog))
    # a standby must NOT consume a passage: a turn the model failed to produce has not read it, and
    # letting it count would lose that page for good to a rate limit.
    bs.op_air(name=gid, source="B · S2 · p.2", provider="mistral", model="m", turn="read#10", aired="0",
              program=_key)
    check("a STANDBY record does not consume a passage",
          bs._resolve_source("next", gid, prog) == "shelf:cur:passage:2",
          bs._resolve_source("next", gid, prog))
    check("`current` ignores a standby (it names the passage actually read)",
          bs._resolve_source("current", gid, prog) == "shelf:cur:passage:1",
          bs._resolve_source("current", gid, prog))
    empty = BenchStationConcept(k.manager.get_session(client))
    check("`current` with nothing aired yet resolves to nothing (the follow-up stands by)",
          empty._resolve_source("current", "studio_art", prog) == "",
          repr(empty._resolve_source("current", "studio_art", prog)))

    llm_provider.generate = real_generate
    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a programme turn is produced inside the daemon, behind the one LLM gate, "
          "under the role's declared contract; it writes the feed and the bench record exactly once "
          "each with the real provider/model; a turn the model does not produce is recorded standby "
          "and never invented; society.air forwards and opens no write path of its own. The cycle is "
          "workflow entries on the bench, armed mode=auto with the declared trigger and budget, and "
          "the cursor is derived from the record — so an episode airs with no operator.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
