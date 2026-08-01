"""
Shell subcommand modes — one mechanism for every mode.

A **namespace mode** scopes bare input to `<mode>.<operator>`; a `nav_hint` maps a
bare number to a navigation operator (e.g. dive signposts). Concept-model modes are
auto-registered from the ConceptRegistry (drop a concept model in → it becomes an
enterable mode, no shell edit); the hardcoded navigator `dive` is registered the same
way. There is one resolution rule for all of them, so `dive` and a concept model are
the *same* real mechanism, not parallel special-cases.

Pure and I/O-free: the REPL owns the prompt, input, and dispatch. This module only
answers "is this token a mode?", "what does a dispatched command enter?", and "given
input inside mode X, what command(s) should the REPL try?" — so it is unit-testable
without the interactive loop.

Selection modes (assoc / dream / lens — numeric pick of a staged candidate) are a
*different* kind of mode and stay in the REPL; this controller covers the namespace
modes (dive + concept models).
"""

from typing import Dict, List, Optional

from api.router import CommandRouter


class ModeController:
    # Namespace modes entered by DISPATCHING a command (not by a bare name), mapped to
    # the operator a bare number selects inside the mode. dive: `dive X` → [dive]; a
    # number → dive.look signpost=N. The entering command aliases resolve via ROUTER.
    _COMMAND_MODES: Dict[str, str] = {"dive": "look"}
    _COMMAND_ALIASES: Dict[str, str] = {"dive": "dive", "look": "dive", "d": "dive"}

    def __init__(self) -> None:
        self._nav_hint: Dict[str, Optional[str]] = {}
        self.refresh()

    def refresh(self) -> None:
        """(Re)build the mode table from the live concept registry + command modes."""
        hint: Dict[str, Optional[str]] = {}
        try:
            for ns in CommandRouter.concept_namespaces():
                hint[ns] = None                      # concept models: no numeric nav
        except Exception:
            pass
        hint.update(self._COMMAND_MODES)             # dive etc.
        self._nav_hint = hint

    # ── enter ────────────────────────────────────────────────────────────────
    def is_mode(self, token: str) -> bool:
        return token in self._nav_hint

    def bare_enter(self, token: str) -> bool:
        """True if a bare `token` (no args) should enter a mode on its own — concept
        models. Command modes (dive) enter by being dispatched, not by a bare name."""
        return token in self._nav_hint and token not in self._COMMAND_MODES

    def command_enter(self, cmd: str) -> Optional[str]:
        """The namespace mode a just-dispatched command enters (dive/look/d → dive)."""
        return self._COMMAND_ALIASES.get(cmd)

    def operators(self, mode: str) -> List[str]:
        """The bare operators available inside `[mode]` (for the enter hint / help)."""
        try:
            return CommandRouter.concept_namespaces().get(mode, [])
        except Exception:
            return []

    def is_command_mode(self, mode: str) -> bool:
        """A command mode (dive) is entered by dispatching a target-accepting command, so
        `<mode> <anything>` always builds — it must let real commands pass through rather
        than swallow them (unlike a concept namespace, where `<mode> <non-op>` fails to
        build and falls through on its own)."""
        return mode in self._COMMAND_MODES

    # ── in-mode resolution (the one rule) ──────────────────────────────────────
    def candidates(self, mode: str, raw: str, is_command=None) -> List[str]:
        """Ordered command strings the REPL should try for input `raw` inside `[mode]`:

          1. nav_hint + a bare number → `<mode>.<navop> signpost=N`  (dive signposts)
          2. otherwise → ONLY the `<mode>`-scoped form (`<mode> <raw>` → `<mode>.<op>`, and
             for a command mode like dive, `dive <raw>` navigates).

        Mode PURITY: there is NO global passthrough. Inside `[mode]`, only that mode's
        operators (and, for dive, bare navigation) resolve — a stray shell command is NOT
        silently executed (that added noise and blurred whether you were in the mode). The
        REPL still handles meta (help / out / exit / more / next / prev) BEFORE this call, so
        leaving and getting help always work; everything else must be a mode command or it is
        rejected with a clear "not a <mode> command" (the REPL prints it when nothing builds).

        `is_command` is accepted for signature compatibility but no longer consulted.
        """
        parts = raw.split(None, 1)
        head = parts[0] if parts else ""
        # Forgive a redundant leading mode verb. Inside [dive] a user habitually types the
        # WHOLE command — `dive town` — not just the target `town`. Without this, purity turns
        # that into `dive dive town`, so the focus id becomes the literal string "dive town"
        # and the dive fails with "Focal point dissolved". Strip ONE leading token when it is
        # this mode's own name or an alias that ENTERS this mode (dive/look/d → dive), so
        # `town` and `dive town` are identical. A non-verb head (`tree Spain`) is untouched —
        # purity still rejects stray shell commands.
        if head and (head == mode or self._COMMAND_ALIASES.get(head) == mode):
            raw = parts[1] if len(parts) > 1 else ""
            parts = raw.split(None, 1)
            head = parts[0] if parts else ""
        nav = self._nav_hint.get(mode)
        if nav and head.isdigit():
            return [f"{mode}.{nav} signpost={head}"]
        return [f"{mode} {raw}"]
