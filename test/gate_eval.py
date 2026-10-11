#!/usr/bin/env python3
"""
THE GATE — one function decides, and the grep of §0 proves nothing else does.

Order: `a7406440-directive-backend-one-gate-2026-09-22.md` §6.

Two halves, and the second is the one that keeps the first true:

  1. The TABLE half enumerates every id-set × every one of the eight actions × the fact
     combinations that matter, and asserts the answer AND the reason term. A permission table
     that is only tested where it says yes is a table nobody has read.

  2. The GREP half is §0: the permission decision terms — `role ==`, `_owned_cast`,
     `_pub_nucleus`, `_is_public(`, `"role:librarian" in`, `in allowed_scopes`, `mode ==
     "auto"` and the rest — appear in NO platform code outside the gate itself, the session
     manager that asks it, and the store that enforces the list it produced. An ASSERTION at 0
     (the purge order §4.1); application modules that still decide are listed, not counted.

Run:  python test/gate_eval.py     (exit 0 = all pass)
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.api import gate as G                                   # noqa: E402

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


# ── a world whose facts the eval states, so every branch of step 4 is reachable ─────────────
FACTS = set()


def _has(set_name, member):
    return (set_name, member) in FACTS


ASSIGN = """\
admin admin
anonymous guest
res1 resident
lib1 librarian
rsr1 researcher on plants_lab
llm:programme:news programme on studio_ai/news_show
mem1 member on grp_a/main
system.telemetry telemetry on feeds
chair1 admin on grp_a
cons1 consumer on source:pool:x:v1
"""


def _write_world(tmp):
    ap = os.path.join(tmp, "assign.ak")
    with open(ap, "w", encoding="utf-8") as fh:
        fh.write(ASSIGN)
    G.load(assign_path=ap)
    G.set_facts(_has)
    return ap


def main():
    import tempfile
    tmp = tempfile.mkdtemp(prefix="akasha_gate_")
    ap = _write_world(tmp)

    print("=" * 78)
    print("the gate — one function, four steps, eight actions, seven id-sets")
    print("=" * 78)

    # ── the table loaded, and it is the shipped one ─────────────────────────────────────────
    doc = json.load(open(G.IDSETS_PATH, encoding="utf-8"))
    rows = G.idsets()
    # Nine since 2026-10-02 §5.2: `consumer` (read · run on a resource a workload requires). It is
    # a RESOURCE row — never a client's main ID set — and the eight below are still the ruling's.
    check("the shipped table has the ruling's eight rows plus `consumer` (§5.2)", len(rows) == 9,
          "%d: %s" % (len(rows), sorted(rows)))
    check("…and declares exactly the eight actions",
          tuple(doc.get("actions") or ()) == G.ACTIONS, str(doc.get("actions")))
    check("…and no row grants an action outside the eight",
          all(set(r["may"]) <= set(G.ACTIONS) for r in rows.values()))
    check("the rows are the ruling's eight and `consumer`, by name",
          sorted(rows) == ["admin", "consumer", "guest", "librarian", "member", "programme",
                           "researcher", "resident", "telemetry"], str(sorted(rows)))
    # The `may` column of every row, from the ruling §1 + the `annotate` column of the platform
    # order's §2b. Written out here so a change to the shipped table has to be made twice, on
    # purpose — a permission table that only its own file describes is a table nobody reviews.
    RULING = {   # ruling §1, revision 09-22
        "admin":      {"read", "say", "run", "record", "annotate", "publish", "provision", "admin"},
        "librarian":  {"read", "run", "record", "annotate", "publish", "provision"},
        "programme":  {"read", "run", "say", "annotate", "publish"},
        "researcher": {"read", "run", "say", "record", "annotate", "provision"},
        # The eighth row (revision 09-22, second). A person in their OWN CELL is sovereign
        # there — everything but `admin` — and reaches nothing outside it.
        "resident":   {"read", "say", "run", "record", "annotate", "publish", "provision"},
        "member":     {"read", "say"},
        "guest":      {"read"},
        "telemetry":  {"read", "run", "record"},
        # §5.2 (directive 2026-10-02): a workload's client on a resource its declaration requires
        "consumer":   {"read", "run"},
    }
    wrong = ["%s: %s != ruling %s" % (k, sorted(rows[k]["may"]), sorted(v))
             for k, v in RULING.items() if set(rows[k]["may"]) != v]
    check("…and every row's `may` is the ruling's, action for action", not wrong,
          "; ".join(wrong))
    check("`guest` may only read — it cannot annotate, so it may not add provenance, a link or "
          "a claim to anything", rows["guest"]["may"] == ("read",), str(rows["guest"]["may"]))
    check("`librarian` does NOT `say` — a curation sweep is a job, and it RUNS one, but it "
          "speaks as nobody",
          "say" not in rows["librarian"]["may"] and "run" in rows["librarian"]["may"])
    check("…and may not `admin`, which is the one thing that would let it widen itself",
          "admin" not in rows["librarian"]["may"])
    # §5.1 (directive 2026-10-02): the row is `assigned` — it reaches what its LINE names. The
    # bootstrap line names `feeds`, a NAMED target the gate resolves to the source feeds, so
    # `system.telemetry` reaches exactly what the old `on: feeds` did (asserted below by gate).
    check("`telemetry` reads, runs its pulls and records — on what its line names (`assigned`); "
          "`system.telemetry`'s line is `on feeds`, so a compromised sensor still writes rows "
          "nobody acted on",
          set(rows["telemetry"]["may"]) == {"read", "run", "record"}
          and rows["telemetry"]["on"] == "assigned"
          and [l["on"] for l in G.lines_for("system.telemetry")] == ["feeds"])
    check("`consumer` reads and runs, never records, and says `facts: false`",
          set(rows["consumer"]["may"]) == {"read", "run"} and rows["consumer"]["on"] == "assigned"
          and rows["consumer"]["facts"] is False)
    check("`researcher` provisions its OWN bench — a laboratory's societies and casts are the "
          "researcher's, never a member's", "provision" in rows["researcher"]["may"])
    check("…and does not publish: putting a result in front of the public is a separate consent",
          "publish" not in rows["researcher"]["may"])
    check("`member` is two actions — it joins (a line) and speaks",
          set(rows["member"]["may"]) == {"read", "say"})
    check("`resident` is sovereign in its own cell — everything but `admin`",
          set(rows["resident"]["may"]) == set(G.ACTIONS) - {"admin"}
          and rows["resident"]["on"] == "own", str(rows["resident"]))
    check("…and a member is NOT thereby given a cell: participating is not owning one",
          set(rows["member"]["may"]) < set(rows["resident"]["may"])
          and rows["member"]["on"] != "own")
    check("only `admin` may admin", sorted(k for k, r in rows.items() if "admin" in r["may"])
          == ["admin"])

    # ── step 1 — an absent identity IS A GUEST (§4 step 1) ──────────────────────────────────
    print("\n  ── step 1: which id-set does this identity hold?  (absent → guest) ──")
    FACTS.clear()
    FACTS.add((G.SET_PUBLIC, "pub_key"))
    check("an identity with no line reads what is public — it is a GUEST, not an error",
          G.gate("nobody", "read", "pub_key")[0] is True)
    check("…and is refused everything a guest is refused, by the SAME term, so a refusal "
          "cannot tell a prober which names exist",
          all(G.gate("nobody", a, "pub_key") == G.gate("anonymous", a, "pub_key")
              for a in G.ACTIONS))
    check("…and cannot read what is NOT public",
          G.gate("nobody", "read", "private_key") == (False, G.R_PUBLIC))
    check("the empty identity is a guest too", G.gate("", "read", "pub_key")[0] is True)

    # ── step 2 — the action column, enumerated for every row ────────────────────────────────
    print("\n  ── step 2: may they perform this action? ──")
    WHO = {"admin": "admin", "librarian": "lib1", "researcher": "rsr1", "resident": "res1",
           "programme": "llm:programme:news", "member": "mem1",
           "telemetry": "system.telemetry", "guest": "anonymous", "consumer": "cons1"}
    # A target each row's `on` reaches, so step 3 never masks step 2's answer.
    TARGET = {"admin": "anything", "librarian": "anything", "researcher": "plants_lab",
              "resident": "owner:user_res1",
              "programme": "studio_ai/news_show", "member": "grp_a/main",
              "telemetry": "feed:sensor1", "guest": "pub_key", "consumer": "source:pool:x:v1"}
    # Every fact true, so step 4 never masks step 2's answer either.
    FACTS.clear()
    for k in TARGET.values():
        for st in (G.SET_DECLARED, G.SET_ARMED, G.SET_SOURCE_READY, G.SET_HEADROOM,
                   G.SET_PUBLIC):
            FACTS.add((st, k))
    bad = []
    for role, row in sorted(rows.items()):
        for act in G.ACTIONS:
            ok, why = G.gate(WHO[role], act, TARGET[role])
            want = act in row["may"]
            if ok != want:
                bad.append("%s/%s: got %s (%s), table says %s" % (role, act, ok, why, want))
            if not ok and want is False and why not in (G.R_ACTION, G.R_TARGET):
                bad.append("%s/%s: refused as %s, expected action_not_granted" % (role, act, why))
    check("every id-set × every action answers exactly what the table says (%d × 8 = %d)"
          % (len(rows), 8 * len(rows)),
          not bad, "; ".join(bad[:3]))

    # ── step 3 — the target column ──────────────────────────────────────────────────────────
    print("\n  ── step 3: on this target? ──")
    check("`on: assigned` reaches the target its own line names",
          G.gate("rsr1", "run", "plants_lab")[0] is True)
    check("…and anything beneath it (asked with `record`, which no fact Set gates — `run` "
          "would be answered by step 4's declared/armed, not by the reach rule under test)",
          G.gate("rsr1", "record", "plants_lab/exp1")[0] is True)
    check("…and NOT a sibling bench", G.gate("rsr1", "run", "other_lab") == (False, G.R_TARGET))
    check("…and not a bench whose name merely starts the same way",
          G.gate("rsr1", "run", "plants_lab_two") == (False, G.R_TARGET))
    check("a programme reaches its own workload", G.gate("llm:programme:news", "say",
                                                         "studio_ai/news_show")[0] is True)
    check("…and not the studio's other programme",
          G.gate("llm:programme:news", "say", "studio_ai/art_explorer") == (False, G.R_TARGET))
    check("`on: *` reaches anywhere", G.gate("lib1", "record", "anyone/anything")[0] is True)
    check("`on: feeds` reaches a feed…", G.gate("system.telemetry", "record",
                                                "feed:sensor1")[0] is True)
    check("…and nothing else: a compromised sensor cannot reach the graph",
          G.gate("system.telemetry", "record", "grp_a/main") == (False, G.R_TARGET))

    # ── step 4 — the facts, each Set proved to be the thing that decides ────────────────────
    print("\n  ── step 4: do the facts allow it? ──")
    # `run` needs ALL FOUR, and the reason is the name of the FIRST one missing — so the term
    # is the thing to fix, not whichever Set a reader happened to look at first.
    T = "studio_ai/news_show"
    FACTS.clear()
    WANT = [(G.SET_DECLARED, G.R_DECLARED), (G.SET_ARMED, G.R_ARMED),
            (G.SET_SOURCE_READY, G.R_SOURCE_READY), (G.SET_HEADROOM, G.R_HEADROOM)]
    for st, term in WANT:
        check("`run` missing `%s` is refused with that fact's own name" % term,
              G.gate("llm:programme:news", "run", T) == (False, term))
        FACTS.add((st, T))
    check("…and with declared ∩ armed ∩ source_ready ∩ headroom it runs",
          G.gate("llm:programme:news", "run", T)[0] is True)
    # …and the order is the ruling's, not the order a reader guesses.
    FACTS.clear(); FACTS.add((G.SET_ARMED, T)); FACTS.add((G.SET_HEADROOM, T))
    check("a workload missing two facts names the FIRST one the ruling lists",
          G.gate("llm:programme:news", "run", T) == (False, G.R_DECLARED))

    FACTS.clear()
    check("a publish the public Set does not hold is refused as `public`",
          G.gate("llm:programme:news", "publish", T) == (False, G.R_PUBLIC))
    FACTS.add((G.SET_PUBLIC, T))
    check("…and once the consent op writes the Set, it publishes",
          G.gate("llm:programme:news", "publish", T)[0] is True)

    check("say-as a cast the workload declares is admitted",
          G.gate("llm:programme:news", "say", T, cast="Anchor",
                 declared_casts=["Anchor", "Scribe"])[0] is True)
    check("SAY AS ONESELF: a speaker needs no cast of its own — its own identity is admitted, "
          "which is why `member` needs neither a cast nor `provision`",
          G.gate("mem1", "say", "grp_a/main", cast="mem1",
                 declared_casts=["Anchor"])[0] is True)
    check("…and a cast it does not declare is refused as `roles` — this is `_owned_cast` "
          "asking the DECLARATION instead of an avatar atom, which is the check that burned "
          "two days of model calls",
          G.gate("llm:programme:news", "say", T, cast="Interloper",
                 declared_casts=["Anchor", "Scribe"]) == (False, G.R_ROLES))

    # `read` needs public ONLY when the public row was the way in.
    check("a guest reading something not public is refused as `public`",
          G.gate("anonymous", "read", "private_key") == (False, G.R_PUBLIC))
    FACTS.add((G.SET_PUBLIC, "private_key"))
    check("…and reads it once it is public", G.gate("anonymous", "read", "private_key")[0] is True)
    FACTS.clear()
    check("…while a reader whose own scope covers the target does NOT need the public Set "
          "(`unless idset.on covers it`)",
          G.gate("lib1", "read", "anything_at_all")[0] is True)
    check("…and a member reads inside its group without it being public",
          G.gate("mem1", "read", "grp_a/main")[0] is True)

    check("a fact Set that cannot be read is not a grant",
          (lambda: (G.set_facts(lambda s, m: (_ for _ in ()).throw(RuntimeError("store down"))),
                    G.gate("llm:programme:news", "run", T))[1])() == (False, G.R_DECLARED))
    G.set_facts(_has)

    # ── an action that is not one of the eight ──────────────────────────────────────────────
    check("an action outside the eight is refused, not quietly admitted",
          G.gate("admin", "write", "x") == (False, G.R_UNKNOWN_ACTION))
    check("…even for the operator", G.gate("admin", "", "x") == (False, G.R_UNKNOWN_ACTION))

    # ── the gate never raises ───────────────────────────────────────────────────────────────
    raised = []
    for args in (("admin", "read", None), (None, None, None), ("admin", "read", ""),
                 ("x" * 500, "read", "y"), ("admin", "READ", "x")):
        try:
            G.gate(*args)
        except Exception as exc:
            raised.append("%s -> %r" % (args, exc))
    check("the gate never raises — a caller that must wrap it in `except` has written a "
          "second decision", not raised, "; ".join(raised))

    # ── group_admin is `admin on <group>`, not an eighth row ────────────────────────────────
    print("\n  ── the row the table deliberately does not have ──")
    check("`admin on <group>` may admin that group",
          G.gate("chair1", "admin", "grp_a")[0] is True)
    check("…and may NOT admin another group",
          G.gate("chair1", "admin", "grp_b") == (False, G.R_TARGET))
    check("…and may not admin the cell", G.gate("chair1", "admin", "scope:sys:admin")
          == (False, G.R_TARGET))
    check("…while the operator can", G.gate("admin", "admin", "grp_b")[0] is True)

    # ── provenance: `admitted` names a line that exists ─────────────────────────────────────
    print("\n  ── provenance: the admitted effect says which line allowed it ──")
    a = G.admitted("rsr1", "record", "plants_lab")
    check("an admitted effect records identity, action, target, id-set AND the file line",
          a["identity"] == "rsr1" and a["action"] == "record" and a["idset"] == "researcher"
          and isinstance(a["line"], int), str(a))
    body = [l for l in open(ap, encoding="utf-8").read().splitlines()]
    check("…and that line number is a real line of the assignment file naming the same id-set",
          1 <= a["line"] <= len(body) and "researcher" in body[a["line"] - 1], body[a["line"] - 1])
    check("an identity with no line is admitted AS A GUEST, and says so — the provenance of a "
          "public read names the row that allowed it, not a blank",
          G.admitted("nobody", "read", "x")["idset"] == "guest")
    check("…and an action no row of its allows names no id-set, so nothing can be stamped "
          "with one", G.admitted("nobody", "run", "x")["idset"] is None)

    # ── scopes_for: the session IS the gate's view of an identity ───────────────────────────
    print("\n  ── the session is the gate's view of an identity ──")
    gs = G.scopes_for("anonymous")
    check("a guest's scopes are the public pair and nothing else",
          gs == ["scope:sys:universal", "view:public"], str(gs))
    ts = G.scopes_for("system.telemetry")
    check("a telemetry agent gets its own cell and no collective scope", 
          "owner:user_system.telemetry" in ts and "scope:sys:collective" not in ts, str(ts))
    ls = G.scopes_for("lib1")
    check("an id-set that may record anywhere gets the collective scope — the scope follows "
          "the ACTION, not the role's name",
          "scope:sys:collective" in ls and "role:librarian" in ls)
    check("…and not the operator's", "scope:sys:admin" not in ls and "scope:sys:dna" not in ls)
    as_ = G.scopes_for("admin")
    check("the operator gets the admin scopes", {"scope:sys:admin", "scope:sys:dna",
                                                 "view:admin_override", "role:superuser"} <= set(as_))
    ms = G.scopes_for("mem1")
    check("a society membership line opens exactly that group",
          "scope:group_grp_a" in ms and "view:group_grp_a" in ms and
          not [s for s in ms if s.startswith("manage:")], str(ms))
    cs = G.scopes_for("chair1")
    check("…and `admin on <group>` also manages it",
          "manage:group_grp_a" in cs and "scope:group_grp_a" in cs, str(cs))

    # ── the files are the truth ─────────────────────────────────────────────────────────────
    print("\n  ── the assignment file is the audit trail ──")
    n0 = len(G.lines_for("newcomer"))
    G.assign("newcomer", "member", "grp_z/main", path=ap)
    check("a new line is appended and read back", len(G.lines_for("newcomer")) == n0 + 1)
    check("…and it grants what it says", G.gate("newcomer", "say", "grp_z/main")[0] is True)
    G.assign("newcomer", "member", "grp_z/main", path=ap)
    check("…and assigning the same line twice does not duplicate it",
          len(G.lines_for("newcomer")) == n0 + 1)
    check("the line is IN THE FILE, not only in memory",
          "newcomer member on grp_z/main" in open(ap, encoding="utf-8").read())
    G.unassign("newcomer", "member", "grp_z/main", path=ap)
    check("removing it takes the permission with it — and drops the identity back to `guest`, "
          "which may not say at all",
          G.gate("newcomer", "say", "grp_z/main") == (False, G.R_ACTION))
    check("…and the file's comments survive the rewrite — an audit trail that loses its "
          "commentary every time it is written is a worse one",
          open(ap, encoding="utf-8").read().count("#") >= ASSIGN.count("#"))

    # ── a permission file that half-loads is worse than one that does not load ──────────────
    print("\n  ── a malformed file is a boot error naming the line ──")
    for body, what in ((ASSIGN + "ghost no_such_idset\n", "an id-set that is not a row"),
                       (ASSIGN + "only_one_word\n", "a line that is not the three fields")):
        bp = os.path.join(tmp, "bad.ak")
        open(bp, "w", encoding="utf-8").write(body)
        try:
            G.load(assign_path=bp)
            check("%s is refused at load" % what, False, "loaded silently")
        except ValueError as exc:
            check("%s is refused at load, and the error names the line" % what,
                  "bad.ak:" in str(exc) or "assign.ak:" in str(exc) or "idsets" in str(exc),
                  str(exc)[:90])
    G.load(assign_path=ap)

    # ── §0: the grep ────────────────────────────────────────────────────────────────────────
    # ── every REGISTERED method's action is one of the eight ────────────────────────────────
    #
    # The manifests were remapped and `manifest_eval` checks them, but a concept model may
    # declare its action inline in `CONCEPT_METHODS`, and seven of them held the OLD tokens as
    # local constants (`_W = "write"`, `_TEL = "sys.telemetry"`). Those never went through the
    # remap, so nine concepts' write ops reached the gate as `unknown_action` — fail-closed,
    # but refused with a term that names nothing an operator can act on, which is exactly the
    # failure mode `_derive_action`'s own comment warns about. A manifest-only check could not
    # see it. This asks the LIVE registry, which is what the dispatcher actually consults.
    print("\n  ── every method the registry serves carries one of the eight ──")
    try:
        from lib.akasha.concepts.registry import build_active
        _acts = dict(getattr(build_active(), "_method_actions", {}) or {})
    except Exception as _exc:                              # noqa: BLE001 — reported, never silent
        _acts = {}
        check("the concept registry is loadable", False, "%s: %s" % (type(_exc).__name__, _exc))
    _off = sorted((m, a) for m, a in _acts.items() if a not in G.ACTIONS)
    check("no registered method carries an action outside the eight (%d methods)" % len(_acts),
          len(_acts) > 0 and not _off,
          "%d off-vocabulary: %s" % (len(_off), _off[:6]) if _off else "")

    print("\n  ── §0: one function decides, and nothing else does ──")
    _grep()

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the gate answers from the table, the lines and the facts; every "
          "id-set × action pair is the table's own answer; each of the four steps refuses in "
          "its own term; an admitted effect names the line that allowed it; and a session's "
          "scopes are a read of the same lines.")
    sys.exit(0)


# ── the §0 grep, as an ASSERTION (the purge order §4.1: 39 → 0) ─────────────────────────────
# A permission DECISION made anywhere but the gate is a second decision. The terms below are the
# ones that made such decisions: comparing a role, reading a role scope out of a session, deciding
# "may publish" by a helper of one's own. Each is now 0 in the platform's code.
#
# What changed from the ratchet, said plainly so it can be checked:
#   * CODE only. A comment or a docstring that NAMES a term is not a decision; the scan reads the
#     tokens (comments dropped, docstrings dropped), so prose explaining why a term is gone no longer
#     counts as the term.
#   * `manager.py` is allowed — the order's own wording is "outside the gate, the SESSION MANAGER and
#     the store", which the ratchet's allow-list omitted (its comment said so; the number stood at
#     +3 rather than absorb it — now the order settles it).
#   * `state ==`, `reason ==` and `boot_pending` are not in the list. They matched the stamped
#     programme state of the guide row (deleted 09-23) and the driver's run gate (now the gate's
#     step-4 facts, held by workload_conformance_eval). What they still match is execution state —
#     a JCL step's PERT state, a semantic search's partial reason, a workflow rewind's reason, the
#     driver's own "a boot airing is owed" trigger record — none of which decides who may do what.
#   * The PLATFORM's files are asserted. An application module that still decides by itself is
#     listed (its owner's to move — the note names them), not counted.
TERMS = [
    r"role ==", r"_owned_cast", r"_pub_nucleus", r"_is_public\(", r'"role:librarian" in',
    r'"role:superuser" in', r"in self\.allowed_scopes", r"in active_scopes", r'mode == "auto"',
]
ALLOWED_PREFIXES = ("lib/akasha/api/gate.py", "lib/akasha/manager.py", "test/",
                    "lib/akasha/composite.py", "lib/akasha/backends/")


def _code_lines(path):
    """{lineno: code text} with comments and docstrings removed — what a decision can be."""
    import ast as _ast
    import io as _io
    import tokenize as _tok
    try:
        src = open(path, encoding="utf-8").read()
        tree = _ast.parse(src)
    except Exception:
        return {}
    doc = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Expr) and isinstance(getattr(node, "value", None), _ast.Constant) \
                and isinstance(node.value.value, str):
            doc.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    out = {}
    try:
        for t in _tok.generate_tokens(_io.StringIO(src).readline):
            if t.type in (_tok.COMMENT, _tok.NL, _tok.NEWLINE, _tok.INDENT, _tok.DEDENT,
                          _tok.ENDMARKER):
                continue
            if t.start[0] in doc:
                continue
            out.setdefault(t.start[0], []).append(t.string)
    except Exception:
        return {}
    return {n: " ".join(v) for n, v in out.items()}


def _platform_file(path):
    import json as _json
    if not path.startswith("lib/akasha/concepts/"):
        return not path.startswith("archives/")
    if os.path.dirname(path) != "lib/akasha/concepts":
        return False
    pm = set(_json.load(open(os.path.join(ROOT, "lib/akasha/concepts/MANIFEST.json"),
                             encoding="utf-8")).get("platform_modules") or [])
    return os.path.splitext(os.path.basename(path))[0] in pm


def _grep():
    import glob as _glob
    os.chdir(ROOT)
    files = [f for d in ("lib", "api", "archives") for f in _glob.glob(d + "/**/*.py", recursive=True)
             if "__pycache__" not in f and not f.startswith(ALLOWED_PREFIXES)]
    pats = [(t, re.compile(t.replace(" ", r"\s*"))) for t in TERMS]
    plat, app = [], []
    for f in sorted(files):
        for n, code in _code_lines(f).items():
            for t, rx in pats:
                if rx.search(code):
                    (plat if _platform_file(f) else app).append("%s:%d %s" % (f, n, t))
    check("ASSERTION — permission decision terms in PLATFORM code outside the gate, the session "
          "manager and the store: %d (must be 0)" % len(plat), not plat, "; ".join(plat[:6]))
    if app:
        print("        application modules still deciding by themselves (theirs to move): "
              + "; ".join(app[:8]) + (" …" if len(app) > 8 else ""))


if __name__ == "__main__":
    main()
