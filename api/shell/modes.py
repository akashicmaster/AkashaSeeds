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

    # ── in-mode resolution (the one rule) ──────────────────────────────────────
    def candidates(self, mode: str, raw: str) -> List[str]:
        """Ordered command strings the REPL should try for input `raw` inside `[mode]`:

          1. nav_hint + a bare number → `<mode>.<navop> signpost=N`  (dive signposts)
          2. otherwise → `<mode> <raw>` (namespace-scoped, i.e. <mode>.<op>) …
          3. … then `raw` itself (global fallback — help / status / w / r still work).

        The REPL builds each in order and uses the first that resolves.
        """
        parts = raw.split(None, 1)
        head = parts[0] if parts else ""
        nav = self._nav_hint.get(mode)
        if nav and head.isdigit():
            return [f"{mode}.{nav} signpost={head}"]
        return [f"{mode} {raw}", raw]
