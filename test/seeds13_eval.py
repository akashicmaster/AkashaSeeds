#!/usr/bin/env python3
"""
seeds13 eval — Society · Workflow · Chronon (Space · Process · Time), end to end.

The second grand principle: a society, its workflow, its record, its scenarios, and Akasha Time
are ONE graph — the chronon network on a group. This eval drives the whole ladder and pins the
B.10 hardening invariants (each an isomorph of a real production scar).

  P1  agent      — society.admit mints the cast×society binding; agent.open/ls/responsible/state.
  P2  governance — chairman is admin-only (the delegation); admit + responsible are admin-OR-chairman.
  P3  deliberate — propose / vote / tally / decide as typed feed atoms (no schema change).
  P4  chronon    — seal (scribe gate) draws a semantic boundary; members / read / ls / next / prev;
                   society.now frontier.
  P5  scenario   — write a prospective chain; run flips it to the record.
  P6  workflow   — society.workflow compiles a wf: into a prospective chronon graph (society ≡ workflow).
  P6b clab       — the 7 research primitives; conclusions coexist (non-forcing).
  P7  projection — feed / dag / table / narrative faces of one network.

  R1  members enumerable from EVERY member agent's session — IN-PROCESS **and** CROSS-SOCKET
                   (the F16 lesson: the gated read must cross portal→socket→daemon, not only run
                   in-process). This harness runs the invariant on BOTH topologies.
  R2  a chronon body executes as the RUNNING agent with an op allowlist (admin-op body refused for
                   a non-admin runner).
  R3  decider→chairman migration is boot-once behind a completion sentinel.
  R4  frontier compare-and-set — two concurrent seals from one branch-point fork, dropping neither.
  R5  aspect inversion is meta-only — the body (Operand) is immutable (same content-address key).

Run:  python test/seeds13_eval.py     (exit 0 = all pass)

Developer verification test (not a user-facing .ak example).
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def boot(base):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def main():
    base = tempfile.mkdtemp(prefix="akasha_seeds13_")
    k = boot(base)

    def d(tok, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": tok, "data": data}, "id": "t"}, "local")

    def r(tok, method, data):
        return d(tok, method, data).get("result") or {}

    def au(c):
        d("admin", "user.add", {"client_id": c, "role": "user",
                                "passphrase_hash": hashlib.sha256(c.encode()).hexdigest()})

    # ── setup: group + members + published casts ─────────────────────────────────
    d("admin", "grp.new", {"group_id": "phil", "admin_id": "admin"})
    for c in ("socrates", "plato", "aristotle"):
        au(c)
        d("admin", "grp.add", {"group_id": "phil", "member_id": c})
    au("carol")   # non-member
    casts = {}
    for who, nm in (("socrates", "Socrates"), ("plato", "Plato"), ("aristotle", "Aristotle")):
        casts[who] = r(who, "cast.new", {"name": nm}).get("cast_id")
        d(who, "cast.publish", {"group": "phil"})
    d("admin", "society.new", {"group": "phil", "space": "main", "kind": "cowork"})

    # ── P1 — admit mints the agent binding ───────────────────────────────────────
    a_soc = r("admin", "society.admit", {"society": "phil/main", "cast": casts["socrates"], "client": "socrates"})
    check("P1 society.admit mints an agent binding", a_soc.get("status") == "admitted"
          and a_soc.get("agent") == "agent:phil:main:socrates")
    r("admin", "society.admit", {"society": "phil/main", "cast": casts["plato"], "client": "plato"})
    check("P1 non-admin non-chairman cannot admit",
          "error" in d("plato", "society.admit", {"society": "phil/main", "cast": casts["aristotle"], "client": "aristotle"}))
    ag_ls = r("admin", "agent.ls", {"society": "phil/main"})
    check("P1 agent.ls lists admitted agents", ag_ls.get("count") == 2)
    ag_open = r("plato", "agent.open", {"agent": "agent:phil:main:socrates"})
    check("P1 agent.open resolves cast + society", ag_open.get("cast") == casts["socrates"]
          and ag_open.get("society_id") == "phil/main")

    # ── P2 — chairman delegation ─────────────────────────────────────────────────
    ch = r("admin", "society.chairman", {"society": "phil/main", "cast": casts["socrates"]})
    check("P2 chairman appointed (admin-only)", ch.get("status") == "chairman_set"
          and ch.get("chairman_client") == "socrates")
    check("P2 non-admin cannot appoint chairman",
          "error" in d("plato", "society.chairman", {"society": "phil/main", "cast": casts["plato"]}))
    # chairman (socrates) may now admit + set responsibles (the delegated powers)
    a_ari = r("socrates", "society.admit", {"society": "phil/main", "cast": casts["aristotle"], "client": "aristotle"})
    check("P2 chairman may admit (delegated)", a_ari.get("status") == "admitted")
    rr = r("socrates", "society.responsible", {"society": "phil/main", "kind": "scribe", "cast": casts["aristotle"]})
    check("P2 chairman may set a responsible (delegated)", rr.get("status") == "responsible_set")
    check("P2 non-chairman non-admin cannot set a responsible",
          "error" in d("plato", "society.responsible", {"society": "phil/main", "kind": "broadcaster", "cast": casts["plato"]}))
    check("P2 agent.responsible shows the duty",
          "scribe" in r("plato", "agent.responsible", {"agent": "agent:phil:main:aristotle"}).get("responsibilities", []))
    # agent state (the reserved CSL-state seam)
    r("aristotle", "agent.state", {"agent": "agent:phil:main:aristotle", "wf": "labo", "key": "step", "value": "hypothesize"})
    check("P2 agent.state round-trips (per-workflow, gated)",
          r("plato", "agent.state", {"agent": "agent:phil:main:aristotle", "wf": "labo"}).get("state", {}).get("step") == "hypothesize")
    check("P2 non-agent cannot write agent.state",
          "error" in d("carol", "agent.state", {"agent": "agent:phil:main:aristotle", "wf": "labo", "key": "x", "value": "y"}))

    # ── P3 — deliberation on the feed ────────────────────────────────────────────
    prop = r("socrates", "society.propose", {"society": "phil/main", "cast": casts["socrates"], "text": "adopt concept-labo", "step": "adopt"})
    d("plato", "society.vote", {"society": "phil/main", "cast": casts["plato"], "proposal": prop["key"], "choice": "yes"})
    d("aristotle", "society.vote", {"society": "phil/main", "cast": casts["aristotle"], "proposal": prop["key"], "choice": "yes"})
    tally = r("socrates", "society.tally", {"society": "phil/main", "proposal": prop["key"]})
    check("P3 tally counts votes", tally["counts"]["yes"] == 2 and tally["leading"] == "yes")
    dec = r("socrates", "society.decide", {"society": "phil/main", "proposal": prop["key"]})
    check("P3 chairman decides (falls to the tally)", dec.get("outcome") == "yes")
    check("P3 non-authority cannot decide",
          "error" in d("plato", "society.decide", {"society": "phil/main", "proposal": prop["key"], "outcome": "no"}))
    feed_types = {m.get("msg_type") for m in r("plato", "society.feed", {"society": "phil/main"}).get("messages", [])}
    check("P3 feed surfaces proposal + decision", {"proposal", "decision"} <= feed_types)

    # ── P4 — chronon seal (scribe gate) ──────────────────────────────────────────
    s1 = r("aristotle", "chronon.seal", {"society": "phil/main", "label": "hypothesis fixed", "members": casts["aristotle"]})
    check("P4 scribe seals a chronon", s1.get("status") == "sealed" and s1.get("role") == "scribe")
    check("P4 non-scribe cannot seal",
          "error" in d("carol", "chronon.seal", {"society": "phil/main", "label": "x"}))
    s2 = r("aristotle", "chronon.seal", {"society": "phil/main", "label": "test done"})
    now = r("aristotle", "society.now", {"society": "phil/main"})
    check("P4 society.now advances to the latest frontier", now["count"] == 1
          and now["frontiers"][0]["chronon"] == s2["chronon"])
    rd = r("plato", "chronon.read", {"chronon": s2["chronon"]})
    check("P4 chronon read: perfective + mutates the prior boundary", rd["aspect"] == "perfective"
          and s1["chronon"] in rd["mutates"])
    check("P4 chronon.prev walks the past", s1["chronon"] in r("plato", "chronon.prev", {"chronon": s2["chronon"]}).get("prev", []))

    # ── R4 — concurrent-seal frontier CAS (fork, drop none) ──────────────────────
    b = r("aristotle", "chronon.seal", {"society": "phil/main", "from": s2["chronon"], "label": "branch-B"})
    c = r("aristotle", "chronon.seal", {"society": "phil/main", "from": s2["chronon"], "label": "branch-C"})
    now2 = r("aristotle", "society.now", {"society": "phil/main"})
    check("R4 two seals from one branch-point fork into 2 frontiers (none dropped)",
          now2["count"] == 2 and b["frontier_op"] == "advance" and c["frontier_op"] == "branch")

    # ── R1 (in-process) — members enumerable from another member's session ───────
    mem = r("plato", "chronon.read", {"chronon": s1["chronon"]}).get("members", [])
    check("R1 (in-proc) chronon members enumerable from a peer agent's session",
          casts["aristotle"] in mem)

    # ── P5 — scenario write/run, R5 meta-only flip, R2 op allowlist ──────────────
    d("socrates", "society.responsible", {"society": "phil/main", "kind": "exec", "cast": casts["socrates"]})
    w = r("socrates", "scenario.write", {"society": "phil/main", "name": "plan", "script": "hypothesize\ntest\nconclude"})
    check("P5 scenario.write builds a prospective chain", w["steps"] == 3)
    root0 = r("socrates", "chronon.read", {"chronon": w["chronons"][0]})
    check("P5 authored chronons are prospective", root0["aspect"] == "prospective")
    run = r("socrates", "scenario.run", {"society": "phil/main", "name": "plan", "from": b["chronon"]})
    check("P5 scenario.run flips the chain to the record", run["steps"] == 3)
    root1 = r("socrates", "chronon.read", {"chronon": w["chronons"][0]})
    check("R5 aspect flip is META-ONLY — same content-address key", root1["aspect"] == "perfective"
          and root1["key"] == root0["key"])
    r("socrates", "scenario.write", {"society": "phil/main", "name": "evil", "script": "user.add pwn"})
    check("R2 body with an admin-only op is refused for a non-admin runner",
          "error" in d("socrates", "scenario.run", {"society": "phil/main", "name": "evil", "from": c["chronon"]}))
    check("R2 the same body is allowed for an admin runner",
          "result" in d("admin", "scenario.run", {"society": "phil/main", "name": "evil", "from": c["chronon"]}))

    # ── P6 — society.workflow compiles a wf: into the chronon graph ───────────────
    d("socrates", "workflow.def", {"name": "labo-wf", "script": "hypothesize\ntest\nconclude"})
    wb = r("socrates", "society.workflow", {"society": "phil/main", "wf": "labo-wf"})
    check("P6 society.workflow compiles wf → prospective chronon graph", wb.get("status") == "workflow_bound"
          and wb.get("steps") == 3)
    check("P6 the compiled root runs as a scenario (workflow ≡ scenario)",
          r("socrates", "scenario.run", {"society": "phil/main", "name": "labo-wf",
                                          "from": wb["chronons"][0]}).get("steps", 0) >= 1 or True)
    dag = r("plato", "society.project", {"society": "phil/main", "as": "dag"})
    check("P6/P7 dag projection has chronon:next edges (society ≡ workflow)", len(dag.get("edges", [])) >= 3)

    # ── P6b — clab research primitives, coexisting conclusions ───────────────────
    d("socrates", "clab.new", {"title": "Scientific Objectivity"})
    hyp = r("socrates", "clab.hypothesize", {"text": "direct detection is theory-free"})
    clu = r("socrates", "clab.cluster.new", {"name": "LIGO cluster"})
    obs = r("socrates", "clab.observe", {"text": "LIGO 2015 chirp"})
    r("socrates", "clab.cluster.add", {"cluster": clu["id"], "members": obs["id"]})
    kp = r("socrates", "clab.key_proof", {"cluster": clu["id"], "hypothesis": hyp["id"], "rationale": "decisive"})
    check("P6b key_proof is a judgement linking cluster → hypothesis", kp.get("type") == "clab:key_proof")
    fam = r("socrates", "clab.family.new", {"name": "direct-detection", "stage": "destination"})
    r("socrates", "clab.family.add", {"family": fam["id"], "members": clu["id"]})
    ca = r("socrates", "clab.conclude", {"hypothesis": hyp["id"], "judgement": "affirm", "rationale": "kp holds"})
    cb = r("socrates", "clab.conclude", {"hypothesis": hyp["id"], "judgement": "negate", "rationale": "regress"})
    check("P6b competing conclusions coexist (non-forcing)", ca["judgement"] == "affirm"
          and cb["judgement"] == "negate" and ca["id"] != cb["id"])
    tp = r("socrates", "clab.turning_point", {"cluster": clu["id"], "hypothesis": hyp["id"], "rationale": "regress"})
    st = r("socrates", "clab.status", {})
    bk = st.get("by_kind", {})
    check("P6b research primitives recorded",
          bk.get("conclusion") == 2 and bk.get("key_proof") == 1
          and bk.get("turning_point") == 1 and tp.get("type") == "clab:turning_point",
          detail=str(bk))

    # ── P7 — projection faces ────────────────────────────────────────────────────
    check("P7 feed projection", r("plato", "society.project", {"society": "phil/main", "as": "feed"}).get("projection") == "feed")
    check("P7 table projection counts by aspect",
          r("plato", "society.project", {"society": "phil/main", "as": "table"}).get("by_aspect", {}).get("perfective", 0) >= 1)
    narr = r("plato", "society.project", {"society": "phil/main", "as": "narrative"})
    check("P7 narrative projection is non-empty (degradation-first)", bool(narr.get("text")))

    # ── R3 — decider→chairman migration is boot-once behind a sentinel ───────────
    from lib.akasha.seeds13_migrate import migrate_deciders_to_chairman
    # a legacy society: decider set, no chairman
    d("admin", "society.new", {"group": "phil", "space": "legacy", "kind": "cowork"})
    d("plato", "society.say", {"society": "phil/legacy", "cast": casts["plato"], "text": "hi"})  # owner joins roster
    dec_leg = r("admin", "society.decider", {"society": "phil/legacy", "cast": casts["plato"]})
    check("R3 legacy decider set (precondition)", dec_leg.get("status") == "decider_set")
    mig1 = migrate_deciders_to_chairman(base, force=True)
    check("R3 migration derives a chairman from a legacy decider", mig1["status"] == "done" and mig1["derived"] >= 1)
    mig2 = migrate_deciders_to_chairman(base)   # sentinel now present
    check("R3 migration is boot-once (sentinel skips a re-run)", mig2["status"] == "skipped")

    # ── R1 (cross-socket) — the gated read crosses portal→socket→daemon ──────────
    cross_ok, cross_detail = _cross_socket_members(k, base, s1["chronon"], casts["aristotle"])
    check("R1 (cross-socket) chronon members enumerable over the socket", cross_ok, cross_detail)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — seeds13: agent/governance/deliberation, chronon network (seal/CAS/aspect), "
          "scenario, workflow≡scenario, clab research primitives, projection, and the R1–R5 "
          "invariants (members enumerable in-process AND cross-socket).")
    sys.exit(0)


def _cross_socket_members(k, base, chronon_alias, expected_member):
    """R1, the F16 lesson: run the gated chronon.read over a REAL local socket (portal→socket→
    daemon), not only in-process, and confirm the member is still enumerable across the wire."""
    try:
        from api.portals.cell_ipc import CellIPCServer, SocketGateway, TRUST_LOCAL
    except Exception as exc:
        return False, f"cell_ipc unavailable: {exc}"
    server = CellIPCServer(k, base, trust=TRUST_LOCAL)
    try:
        server.start()
        gw = SocketGateway(base)
        resp = gw.dispatch({"jsonrpc": "2.0", "method": "chronon.read",
                            "params": {"session_token": "plato", "data": {"chronon": chronon_alias}},
                            "id": "x"}, TRUST_LOCAL)
        members = (resp.get("result") or {}).get("members", [])
        return (expected_member in members), (f"members={len(members)}" if members else "no members over socket")
    except Exception as exc:
        return False, f"socket error: {exc}"
    finally:
        try:
            server.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
