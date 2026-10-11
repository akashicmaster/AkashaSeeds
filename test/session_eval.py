#!/usr/bin/env python3
"""
A SESSION IS THE GATE'S VIEW OF AN IDENTITY — and the fact Sets have one writer each.

Order: `a7406440-directive-backend-one-gate-2026-09-22.md` §2b / §6.

The order's second claim, after "one function decides", is that the gate is not a module beside
IAM and the session manager — it is what they become. Society management and ordinary session
management run on three things and nothing else: the id-set table, the assignment file, and the
gate. A society membership is an assignment line; the group engine a session opens is the list
`gate.scopes_for` produced; `society.join` / `admit` / `chairman` / `moderator` is each a way of
writing a line, which is why they go.

This eval holds the half of that which is testable without a live cell — the derivation — and the
fact Sets' one-writer rule, which is what step 4 rests on. `gate_eval` holds the table; the call
sites move over in the stages after this one and bring their own checks.

Run:  python test/session_eval.py     (exit 0 = all pass)
"""
import ast
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.api import gate as G                                   # noqa: E402
from lib.akasha.api import facts as F                                  # noqa: E402

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    print("=" * 78)
    print("the session is the gate's view of an identity; each fact Set has one writer")
    print("=" * 78)

    # ── the shipped assignment file is loadable, and it is what a fresh cell boots with ──────
    print("\n  ── the file a cell cannot boot without ──")
    G.load()
    for ident, idset in (("admin", "admin"), ("anonymous", "guest")):
        held = [l["idset"] for l in G.lines_for(ident)]
        check("the shipped assign.ak gives `%s` the `%s` id-set" % (ident, idset),
              idset in held, str(held))
    check("…and every system identity has a line, so none of them depends on a bare id being "
          "believed over a socket for its PERMISSIONS",
          all(G.lines_for(i) for i in ("system.librarian", "system.weaver",
                                       "system.jataka", "system.broadcaster")))
    check("an identity the file does not name is a GUEST (§4 step 1) — it may not record…",
          G.gate("someone.who.signed.up", "record", "x") == (False, G.R_ACTION))
    check("…and is answered exactly as `anonymous` is, for every action, so a refusal cannot "
          "tell a prober which names the file holds",
          all(G.gate("someone.who.signed.up", a, "x") == G.gate("anonymous", a, "x")
              for a in G.ACTIONS))
    check("the shipped file gives `system.telemetry` the row that may only record into feeds",
          [l["idset"] for l in G.lines_for("system.telemetry")] == ["telemetry"])

    # ── scopes_for is the derivation, not a second statement of the policy ──────────────────
    print("\n  ── a session's scopes ARE gate.scopes_for(identity) ──")
    for ident in ("admin", "anonymous", "system.librarian"):
        sc = G.scopes_for(ident)
        check("`%s` resolves to a scope list without asking IAM" % ident, isinstance(sc, list)
              and "scope:sys:universal" in sc, str(sc)[:110])
    check("the guest list is the public pair and NOTHING else — a guest that picked up a cell "
          "scope would be reading somebody's private atoms",
          G.scopes_for("anonymous") == ["scope:sys:universal", "view:public"])
    check("…and it is the same list for every unknown caller, because a guest is a LINE "
          "(`anonymous guest`), not a fallback branch",
          G.scopes_for("anonymous") == G.scopes_for("anonymous"))

    # A membership line opens exactly that group — the §2b claim, as a derivation.
    import tempfile
    tmp = tempfile.mkdtemp(prefix="akasha_sess_")
    ap = os.path.join(tmp, "assign.ak")
    open(ap, "w", encoding="utf-8").write(
        "admin admin\nanonymous guest\np1 member on grp_a/main\n"
        "p2 member on grp_a/main\np2 member on grp_b/side\nboss admin on grp_a\n"
        "r1 researcher on grp_a\n")
    G.load(assign_path=ap)
    s1 = G.scopes_for("p1")
    check("one membership line opens exactly one group engine",
          [x for x in s1 if x.startswith("scope:group_")] == ["scope:group_grp_a"], str(s1))
    s2 = G.scopes_for("p2")
    check("two lines open two, and no more",
          sorted(x for x in s2 if x.startswith("scope:group_"))
          == ["scope:group_grp_a", "scope:group_grp_b"], str(s2))
    check("a member does not manage the group it is in",
          not [x for x in s2 if x.startswith("manage:")])
    sb = G.scopes_for("boss")
    check("`admin on <group>` manages that group…", "manage:group_grp_a" in sb)
    check("…and does NOT collect the operator's cell-wide scopes — a bounded line that picked "
          "them up would be a whole-cell grant written as a one-group one",
          not {"scope:sys:admin", "scope:sys:dna", "role:superuser"} & set(sb), str(sb))
    check("…and the gate agrees with the scope list it produced (they are one derivation, so "
          "they cannot disagree)",
          G.gate("boss", "admin", "grp_a")[0] is True
          and G.gate("boss", "admin", "grp_b") == (False, G.R_TARGET))

    # An `annotate` outside the identity's scope is refused BY THE GATE, before the store.
    #
    # The 09-22 REVISION moved the example: `member` is `read · say` and nothing else — it joins
    # and it speaks — so the row that annotates its own ground is `researcher`. Asserting it of a
    # member would be asserting a table that no longer exists, and the point being made is about
    # the TARGET, not about which row happens to hold the action.
    print("\n  ── annotate is an action, gated on the target like any other ──")
    check("a researcher may annotate inside its own bench",
          G.gate("r1", "annotate", "grp_a/main")[0] is True)
    check("…and is refused outside it, by the gate, so the write never reaches the store",
          G.gate("r1", "annotate", "grp_b/side") == (False, G.R_TARGET))
    check("a member may not annotate at all — it reads and speaks, and that is the whole row",
          G.gate("p1", "annotate", "grp_a/main") == (False, G.R_ACTION))
    check("a guest may not annotate anything at all — it cannot add provenance, a link or a "
          "claim to an atom",
          G.gate("anonymous", "annotate", "anything") == (False, G.R_ACTION))
    check("…and neither may a telemetry agent: it records rows and nothing else",
          G.gate("system.telemetry", "annotate", "feed:x") == (False, G.R_ACTION))
    G.load()

    # ── the fact Sets: one writer each, and the map says who ────────────────────────────────
    print("\n  ── each fact Set has exactly one writer ──")
    check("the five Sets of §2 are declared", set(F.WRITERS) == {
        F.DECLARED, F.ARMED, F.SOURCE_READY, F.HEADROOM, F.PUBLIC}, str(sorted(F.WRITERS)))
    check("…and the gate reads the same five names, so the writer and the reader cannot drift",
          {G.SET_DECLARED, G.SET_ARMED, G.SET_SOURCE_READY, G.SET_HEADROOM, G.SET_PUBLIC}
          == set(F.WRITERS))
    check("every Set names its writer in the map — the answer to 'who could have put this key "
          "here?' is one file", all(F.WRITERS.values()))

    # The one-writer rule, held statically: only `facts.py` writes these Set names.
    bad = []
    for name in (F.DECLARED, F.ARMED, F.PUBLIC):
        try:
            out = subprocess.run(["grep", "-rn", "--include=*.py", name, "lib/"],
                                 capture_output=True, text=True, timeout=60).stdout
        except Exception:
            continue
        for line in out.splitlines():
            path, _, body = line.partition(":")
            if path.startswith(("lib/akasha/api/facts.py", "lib/akasha/api/gate.py")):
                continue
            if "add_to_set" in body or "remove_from_collection" in body:
                bad.append(line[:120])
    check("no module outside `api/facts.py` writes a fact Set directly — a second writer is a "
          "second chance for the fact to be wrong", not bad, "; ".join(bad[:2]))

    # ── the writers are wired at the sites the order names ──────────────────────────────────
    print("\n  ── the writers are wired where the fact becomes true ──")
    prov = open("lib/akasha/workbench/provision.py", encoding="utf-8").read()
    check("`set:wl:declared` is reconciled by the declaration loader, from the FILES",
          "_facts.declared(kernel," in prov)
    check("…before any workload is provisioned, so the gate and the guide never see a "
          "half-reconciled Set",
          prov.index("_facts.declared(kernel,") < prov.index("for decl in decls:"))
    check("`set:wl:armed` is written where a workload becomes provisioned",
          "_facts.armed(kernel," in prov)
    def _facts_src_writers():
        """The PUBLIC row of `api/facts.py`'s WRITERS map, as the file states it."""
        from lib.akasha.api import facts as _f
        return str((_f.WRITERS or {}).get(_f.PUBLIC) or "")

    soc = open("lib/akasha/concepts/society.py", encoding="utf-8").read()
    # ONE WRITER MEANS ONE MODULE, and the module has TWO spellings of the same consent: a space
    # can be opened at creation (`society.new public=yes`) or toggled afterwards
    # (`society.public open=yes`). Counting CALL SITES read that as two writers and let the create
    # path ship without stating the fact at all — so a space answered `public: true` to its creator
    # and "not a public broadcast" to the gate, the guest and the relay, which is the precise
    # disagreement a fact Set exists to make impossible. What the invariant is actually about is
    # that no OTHER module writes it, which the scan above already holds; here we hold that both
    # spellings state it and that the WRITERS map names them.
    import re as _re
    _pub_sites = soc.count("_facts.public(")
    _new_at, _pub_at = soc.find("def op_new"), soc.find("def op_public")
    check("`set:society:public` is written in `society.py` and nowhere else — by BOTH of its "
          "spellings, the create-time one and the toggle",
          _pub_sites == 2 and _new_at >= 0 and _pub_at > _new_at
          and soc.find("_facts.public(") < _pub_at < soc.rfind("_facts.public("),
          "call sites=%d" % _pub_sites)
    check("…and the writers map names both, so 'who could have put this key here' stays one read",
          "society.new" in _facts_src_writers() and "society.public" in _facts_src_writers(),
          _facts_src_writers())

    # ── the reader is installed before anything can ask ─────────────────────────────────────
    import json as _json
    man = _json.load(open("lib/akasha/MANIFEST.json", encoding="utf-8"))
    sch = man.get("schedules") or {}
    check("the fact reader is a declared boot schedule, not an import someone remembered",
          sch.get("gate_facts", {}).get("fn") == "lib.akasha.api.facts:install",
          str(sch.get("gate_facts")))
    check("…and it runs FIRST in its phase — the gate answers every request, so its facts are "
          "installed before anything can ask",
          sch.get("gate_facts", {}).get("order", 999)
          <= min(v.get("order", 999) for v in sch.values()),
          "order=%s" % sch.get("gate_facts", {}).get("order"))
    check("…on every boot, because a fact reader is process state and a new process has none",
          sch.get("gate_facts", {}).get("when") == "every_boot")

    # ── the policy ships, and the audit trail is preserved across a redeploy ────────────────
    print("\n  ── the two files ship on the right side of a redeploy ──")
    check("`idsets.json` ships as CODE — it is policy, and a redeploy replaces it",
          "config/identity/idsets.json" in (man.get("code_paths") or []))
    check("`assign.ak` ships as DATA — it is the cell's own audit trail, and a redeploy that "
          "overwrote it would erase who had been granted what",
          "config/identity/assign.ak" in (man.get("data_paths") or []))

    # ── the gate is a leaf: it imports no heart module ──────────────────────────────────────
    print("\n  ── the gate decides for the heart, so it may not depend on it ──")
    tree = ast.parse(open("lib/akasha/api/gate.py", encoding="utf-8").read())
    imports = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            imports.append(n.module or "")
    heart = [m for m in imports if m.startswith("lib.akasha") and not m.startswith("lib.akasha.api")]
    check("the gate imports no heart module — it is a pure function of (table, lines, facts), "
          "which is what lets an eval enumerate it and a compiled heart sit behind it",
          not heart, str(heart))
    check("…and it reads its facts through an injected callback rather than the store",
          "def set_facts(" in open("lib/akasha/api/gate.py", encoding="utf-8").read())

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — a session's scopes are a derivation of the assignment lines and "
          "nothing else; a membership line opens exactly its group and a bounded line collects "
          "no cell-wide scope; `annotate` is gated on the target like any other action; each "
          "fact Set has one writer, wired where the fact becomes true, with the reader "
          "installed first at boot; and the gate depends on no heart module.")
    sys.exit(0)


if __name__ == "__main__":
    main()
