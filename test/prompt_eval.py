#!/usr/bin/env python3
"""
Prompt eval — the interactive prompt must be safe for minimal line editors.

On iOS a-Shell / Pyto the `input()` line editor measures the prompt's visible
column width from the raw string. A prompt that (a) embeds a newline or (b)
carries un-bracketed ANSI colour escapes makes it miscount — the left margin
drifts, the prompt is hidden, and the session locks up. GNU readline (Unix/SSH)
tolerates both, which is why it only showed on the minimal targets.

  P1 no newline   — no prompt variant embeds '\\n' (spacing is printed separately).
  P2 plain clean  — color=False yields pure ASCII: no ESC, no \\001/\\002 markers.
  P3 rl bracketed — readline_active wraps every escape in \\001…\\002 (zero-width).
  P4 balanced     — \\001 and \\002 are balanced and properly nested in the rl form.
  P5 modes/su     — nav-mode tag and su/root prompts follow the same three rules.

Run:  python test/prompt_eval.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from api.shell.input import make_prompt  # noqa: E402

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def _balanced(s):
    depth = 0
    for ch in s:
        if ch == "\001":
            depth += 1
            if depth > 1:
                return False          # no nesting of start markers
        elif ch == "\002":
            depth -= 1
            if depth < 0:
                return False          # end before start
    return depth == 0


def main():
    print("\n  prompt eval — line-editor safety (a-Shell / Pyto)\n")

    nav  = {"active": True, "name": "dive", "kind": "ns"}
    su   = {"active": True, "target": "alice"}
    root = {"active": True, "target": "root"}

    # Every reachable variant, across the three rendering policies.
    variants = []
    for ctx in (
        dict(nav_mode=None, su_context=None),
        dict(nav_mode=nav, su_context=None),
        dict(nav_mode=None, su_context=su),
        dict(nav_mode=nav,  su_context=root),
    ):
        for policy in (
            dict(color=False, readline_active=False),   # plain
            dict(color=True,  readline_active=True),     # readline TTY
            dict(color=True,  readline_active=False),    # color, no readline
        ):
            variants.append(make_prompt("henri", False, ctx["su_context"],
                                        ctx["nav_mode"], **policy))
    variants.append(make_prompt("henri", True, None, None, color=True,
                                readline_active=True))  # multiline

    # P1 — no embedded newline anywhere.
    bad = [repr(v) for v in variants if "\n" in v]
    record("P1 no newline", not bad, "clean" if not bad else str(bad[:2]))

    # P2 — plain policy is pure ASCII (no escapes, no readline markers).
    plains = [make_prompt("henri", False, c.get("su"), c.get("nav"),
                          color=False, readline_active=False)
              for c in ({}, {"nav": nav}, {"su": su}, {"nav": nav, "su": root})]
    bad = [repr(p) for p in plains if "\033" in p or "\001" in p or "\002" in p]
    record("P2 plain clean", not bad, "no escapes" if not bad else str(bad[:2]))

    # P3 — readline policy brackets escapes; a bare ESC outside \001..\002 fails.
    def unbracketed_esc(s):
        depth, seen = 0, False
        for ch in s:
            if ch == "\001":
                depth += 1
            elif ch == "\002":
                depth -= 1
            elif ch == "\033" and depth == 0:
                seen = True
        return seen
    rls = [make_prompt("henri", False, None, nav, color=True, readline_active=True),
           make_prompt("henri", False, su, None, color=True, readline_active=True),
           make_prompt("henri", False, root, nav, color=True, readline_active=True)]
    bad = [repr(p) for p in rls if unbracketed_esc(p)]
    has_markers = all("\001" in p and "\002" in p for p in rls)
    record("P3 rl bracketed", not bad and has_markers,
           "all escapes zero-width" if (not bad and has_markers) else str(bad[:2]))

    # P4 — markers balance and don't nest.
    bad = [repr(p) for p in rls if not _balanced(p)]
    record("P4 balanced", not bad, "balanced" if not bad else str(bad[:2]))

    # P5 — su/root prompts obey the same rules (spot-check root plain + rl).
    rp = make_prompt("henri", False, root, None, color=False, readline_active=False)
    rr = make_prompt("henri", False, root, None, color=True, readline_active=True)
    ok = ("\n" not in rp and "\033" not in rp
          and "\n" not in rr and _balanced(rr) and "[root@akasha]" in rp)
    record("P5 modes/su", ok, repr(rp))

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
