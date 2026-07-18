#!/usr/bin/env python3
"""
Mode eval — the ONE subcommand-mode mechanism (dive + every concept model).

The interactive shell used to have two parallel, half-real notions of "mode":
`dive`/`explore` only relabelled the prompt (cosmetic — "fake"), while concept
models had a separate ad-hoc block. Both were unified onto one pure controller
(`api/shell/modes.py:ModeController`) so `dive` and a concept model enter and
resolve by the SAME rule — and dropping a new concept model in makes it an
enterable mode with no shell edit.

  M1 command mode    — dive enters by being DISPATCHED (command_enter), not by a
                       bare name (bare_enter is False); look/d alias to dive.
  M2 nav numeric     — inside [dive] a bare number → `dive.look signpost=N`.
  M3 nav word        — inside [dive] a non-number → `dive <word>` then global.
  M4 concept mode    — a booted concept model (thesaurus/curation) is a bare-enter
                       namespace mode; its operators come from the live registry.
  M5 concept resolve — inside [thesaurus] a bare operator → `thesaurus.<op>`, and
                       an unrelated global (status) still falls through.
  M6 candidates real — every candidate string M2/M3/M5 emits actually resolves
                       through CommandRouter.build_rpc_request (not a dead label).
  M7 one path        — there is a single interactive REPL (run_cli); the dead
                       AkashaShell/run_shell path is gone from api.portals.

Run:  python test/mode_eval.py
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def main():
    print("\n  mode eval — one subcommand-mode mechanism (dive + concept models)\n")

    # ── Pure controller (no boot needed for the dive command-mode rules) ──────
    from api.shell.modes import ModeController
    m = ModeController()

    # M1 — dive is a command mode: it enters by being dispatched, not by a name.
    ok = (not m.bare_enter("dive")
          and m.command_enter("dive") == "dive"
          and m.command_enter("look") == "dive"
          and m.command_enter("d") == "dive"
          and m.command_enter("thesaurus") is None)
    record("M1 command mode", ok,
           f"bare_enter(dive)={m.bare_enter('dive')} command_enter(look)={m.command_enter('look')}")

    # M2 — inside [dive] a bare number selects the nav operator (signpost).
    c = m.candidates("dive", "5")
    record("M2 nav numeric", c == ["dive.look signpost=5"], str(c))

    # M3 — inside [dive] a non-number tries the scoped form, then the global.
    c = m.candidates("dive", "love")
    record("M3 nav word", c == ["dive love", "love"], str(c))

    # ── Booted registry: concept models must auto-register as modes ───────────
    from api.gateway import create_gateway
    create_gateway(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_mode_"))
    from api.router import CommandRouter as R
    m.refresh()  # pick up the now-live concept registry

    # M4 — a concept model is a bare-enter namespace mode with live operators.
    ops = m.operators("thesaurus")
    ok = (m.bare_enter("thesaurus") and m.bare_enter("curation")
          and "concept" in ops and "reference" in ops and "explore" in ops)
    record("M4 concept mode", ok, f"thesaurus ops={ops}")

    # M5 — inside [thesaurus] a bare operator scopes to thesaurus.<op>; a global
    #      command (status) still resolves via the fallback candidate.
    c_op = m.candidates("thesaurus", "reference ns=word")
    c_gl = m.candidates("thesaurus", "status")
    ok = (c_op == ["thesaurus reference ns=word", "reference ns=word"]
          and c_gl == ["thesaurus status", "status"])
    record("M5 concept resolve", ok, f"{c_op} / {c_gl}")

    # M6 — every candidate the controller emits must really resolve in the router
    #      (the first that resolves wins — exactly what run_cli._build does, passing
    #      is_command so a command mode lets real commands pass through).
    def resolves(mode, raw):
        for cand in m.candidates(mode, raw, is_command=R.is_command):
            if R.build_rpc_request(cand, "akt:tok") is not None:
                return cand
        return None
    checks = {
        ("dive", "5"): "dive.look signpost=5",
        ("dive", "love"): "dive love",                 # bare word → navigate
        ("dive", "tree Spain"): "tree Spain",          # real command → pass through (regression)
        ("dive", "s.ls set:x"): "s.ls set:x",          # single-token command → pass through
        ("dive", "lens src=set:x"): "lens src=set:x",  # not swallowed into a dive on "lens"
        ("dive", "sim rome"): "sim rome",
        ("thesaurus", "reference"): "thesaurus reference",
        ("thesaurus", "concept id=word:love"): "thesaurus concept id=word:love",
        ("thesaurus", "status"): "status",
        ("curation", "ls"): "curation ls",
    }
    bad = {k: (resolves(*k), want) for k, want in checks.items()
           if resolves(*k) != want}
    record("M6 candidates real", not bad, "all resolve" if not bad else str(bad))

    # M7 — one interactive path only: the dead shell must be gone.
    import api.portals as P
    dead_gone = ("run_shell" not in getattr(P, "__all__", [])
                 and not hasattr(P, "AkashaShell"))
    try:
        import api.portals.shell  # noqa: F401
        file_gone = False
    except ImportError:
        file_gone = True
    has_repl = hasattr(P, "run_cli")
    record("M7 one path", dead_gone and file_gone and has_repl,
           f"dead_gone={dead_gone} file_gone={file_gone} run_cli={has_repl}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
