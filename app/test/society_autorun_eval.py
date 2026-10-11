#!/usr/bin/env python3
"""
G2.7 / G3.7 — autonomous execution: society.moderator mode=auto + the auto-run driver.

A society is by origin a HUMAN-moderated proceeding; auto mode lets the moderator execute the bench's
workflows automatically under a POLICY it cannot exceed. Auto mode requires a scribe (every autonomous
act needs a keeper of the record). The driver runs at most one run per society per tick as ONE PRIO_LOW
JCL job through society.run; consecutive failures trip the breaker → mode=manual + an axis record.
Anything not in the policy's workflows list is refused. A human can always take the chair back.

Run:  python app/test/society_autorun_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import autorun
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_ar_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(tok, method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    d("admin", "world.genesis", {})
    d("admin", "grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("admin", "bench.new", {"name": "sandbox", "kind": "research", "group": "lab"})
    d("admin", "society.new", {"group": "lab", "name": "sem", "world": "default",
                               "bench": "sandbox", "kind": "cowork"})
    # moderator = admin's cast; a workflow with one valid step on the main branch
    mod = d("admin", "cast.new", {"name": "Mod"}).get("cast_id")
    d("admin", "society.admit", {"group": "lab", "name": "sem", "cast": "Mod"})
    d("admin", "society.moderator", {"group": "lab", "name": "sem", "cast": mod})
    d("admin", "wf.new", {"bench": "sandbox"})
    d("admin", "wf.write", {"bench": "sandbox", "pos": 1,
                            "entry": json.dumps({"method": "research.note",
                                                 "params": {"name": "sandbox", "text": "auto pass"}})})
    policy = {"workflows": ["main"], "trigger": "boot", "auto_dispatch": False,
              "budget": {"runs_per_day": 4, "max_steps": 500, "max_wall_s": 60},
              "on_failure": {"retries": 1, "breaker": 3}, "run_once": False}

    # ── WHAT ARMING REFUSES NOW: the table, and the policy's own content ──
    #
    # This asked for "mode=auto is REFUSED without a scribe". That precondition is deleted
    # (one-gate ruling §5, and §3 of the stage-2 note): it asks about an ADMISSION, and an
    # admission is an assignment line now — provisioning performs it as admin, so the check
    # refused exactly what the gate admits. A second gate in a call site that has moved.
    #
    # Two things still refuse, and they are the two kinds a call site is allowed to have:
    # the TABLE (who may arm), and the policy's own CONTENT (arming with nothing permitted to
    # run would name no runs at all). Neither asks about a cast.
    d("admin", "user.add", {"client_id": "carol", "role": "user",
                            "passphrase_hash": hashlib.sha256(b"carol").hexdigest()})
    no_line = d("carol", "society.moderator", {"group": "lab", "name": "sem",
                                               "mode": "auto", "policy": json.dumps(policy)})
    check(f"[{shape}] a person with no line on this society cannot arm it (the table, not a cast)",
          "error" in str(no_line) or no_line.get("status") == "refused", str(no_line)[:140])
    empty = d("admin", "society.moderator", {"group": "lab", "name": "sem", "mode": "auto",
                                             "policy": json.dumps(dict(policy, workflows=[]))})
    check(f"[{shape}] …and an auto policy naming NO workflow is refused on its own content",
          empty.get("status") == "refused" and "workflows" in (empty.get("reason") or ""),
          str(empty)[:140])

    # ── a scribe is still DATA the declaration creates — it just does not gate the arming ──
    scr = d("admin", "cast.new", {"name": "Scribe"}).get("cast_id")
    d("admin", "society.admit", {"group": "lab", "name": "sem", "cast": "Scribe"})
    d("admin", "society.responsible", {"group": "lab", "name": "sem", "cast": scr, "kind": "scribe"})
    armed = d("admin", "society.moderator", {"group": "lab", "name": "sem",
                                             "mode": "auto", "policy": json.dumps(policy)})
    check(f"[{shape}] mode=auto is accepted with a scribe (policy stored)",
          armed.get("status") == "mode_set" and armed.get("mode") == "auto"
          and (armed.get("policy") or {}).get("workflows") == ["main"], str(armed)[:160])
    ax = d("admin", "world.axis", {})
    check(f"[{shape}] the mode change is recorded on the world axis",
          any(r.get("kind") == "society.moderator.mode" for r in ax.get("axis", [])),
          str([r.get("kind") for r in ax.get("axis", [])]))

    # ── society.run refuses a workflow outside the policy ──
    bad = d("admin", "society.run", {"group": "lab", "name": "sem", "workflow": "not-listed"})
    check(f"[{shape}] society.run refuses a workflow outside the policy",
          bad.get("status") == "refused" and "not in the society's policy" in (bad.get("reason") or ""),
          str(bad)[:140])

    # ── a driver tick runs the listed workflow as ONE JCL job; the step tees driver=auto ──
    acts = autorun.bench_autorun_tick(k)
    ran = [a for a in acts if a.get("society") == "lab/sem"]
    check(f"[{shape}] the driver ran the auto society once (a JCL job)",
          bool(ran) and ran[0].get("action") == "ran" and ran[0].get("ok") is True
          and ran[0].get("job_id"), str(ran)[:160])
    st = d("admin", "source.stream", {"stream": "wb:sandbox", "space": "group:lab"})
    drivers = {(o.get("source_metadata") or {}).get("driver") for o in st.get("observations", [])}
    check(f"[{shape}] the bench stream stamped driver=auto on the run", "auto" in drivers, str(drivers))

    # ── breaker: a failing workflow flips the society back to manual after N consecutive fails ──
    d("admin", "grp.new", {"group_id": "lab2", "admin_id": "admin"})
    d("admin", "bench.new", {"name": "broken", "kind": "research", "group": "lab2"})
    d("admin", "society.new", {"group": "lab2", "name": "auto2", "world": "default",
                               "bench": "broken", "kind": "cowork"})
    m2 = d("admin", "cast.new", {"name": "Mod2"}).get("cast_id")
    s2 = d("admin", "cast.new", {"name": "Scr2"}).get("cast_id")
    d("admin", "society.admit", {"group": "lab2", "name": "auto2", "cast": "Mod2"})
    d("admin", "society.admit", {"group": "lab2", "name": "auto2", "cast": "Scr2"})
    d("admin", "society.moderator", {"group": "lab2", "name": "auto2", "cast": m2})
    d("admin", "society.responsible", {"group": "lab2", "name": "auto2", "cast": s2, "kind": "scribe"})
    d("admin", "wf.new", {"bench": "broken"})
    # a structured entry that raises every run (research.hyp.new with no text=)
    d("admin", "wf.write", {"bench": "broken", "pos": 1,
                            "entry": json.dumps({"method": "research.hyp.new", "params": {"name": "broken"}})})
    bpol = dict(policy); bpol["trigger"] = "interval:0"; bpol["on_failure"] = {"retries": 0, "breaker": 3}
    d("admin", "society.moderator", {"group": "lab2", "name": "auto2",
                                     "mode": "auto", "policy": json.dumps(bpol)})
    tripped = False
    for _ in range(4):
        acts = autorun.bench_autorun_tick(k)
        a2 = [a for a in acts if a.get("society") == "lab2/auto2"]
        if a2 and a2[0].get("breaker_tripped"):
            tripped = True
            break
    check(f"[{shape}] three failing runs trip the breaker → mode=manual", tripped, str(acts)[:160])
    info = d("admin", "society.read_autorun_probe", {"group": "lab2", "name": "auto2"}) \
        if False else None
    # confirm mode is manual now (the driver flipped it) and it left the auto index
    left = "lab2/auto2" not in {f"{p['gid']}/{p['name']}"
                                for p in __import__("lib.akasha.concepts.society",
                                                    fromlist=["SocietyConcept"]).SocietyConcept(
                                    k.manager.get_session("admin")).list_auto_societies()}
    check(f"[{shape}] the broken society was dropped from the auto index (a human re-arms)", left)


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — arming is refused by the TABLE (a person with no line on the society) "
          "and by the auto policy's own content (a policy naming no workflow), and by nothing else: "
          "the scribe/moderator admission preconditions are deleted, because an admission is an "
          "assignment line now and asking again here refused what the gate admits. Auto mode stores "
          "its policy + records the mode change on the world axis; society.run refuses a workflow "
          "outside the policy; the driver runs a due auto society as one PRIO_LOW JCL job "
          "(driver=auto on the stream); and consecutive failures trip the breaker back to manual "
          "— on both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
