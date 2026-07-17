"""
Multiline input buffer and prompt helpers for Akasha shell portals.
Shared by stdio and remote portals.
"""

from typing import List
from api.env_detector import Colors


def _c(color: str, text: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


class InputBuffer:
    """
    Accumulates input lines until a complete command is ready.
    Detects unclosed triple-quote blocks (\"\"\" / ''') and keeps
    buffering until the block is closed.
    """

    def __init__(self):
        self._lines: List[str] = []

    def push(self, line: str) -> bool:
        """
        Add a line to the buffer.
        Returns True when the buffer is ready to flush (block closed).
        """
        self._lines.append(line)
        return not self.in_multiline

    @property
    def in_multiline(self) -> bool:
        joined = "\n".join(self._lines)
        return joined.count('"""') % 2 != 0 or joined.count("'''") % 2 != 0

    def flush(self) -> str:
        """Return the accumulated text and reset the buffer."""
        text = "\n".join(self._lines).strip()
        self._lines = []
        return text

    def reset(self):
        self._lines = []


_NAV_MODE_COLOR = {
    "dive":    Colors.CYAN,
    "explore": Colors.GREEN,
    "assoc":   "\033[35m",   # magenta — gap analysis
    "dream":   "\033[36m",   # cyan dim — hypothetical linking
    "lens":    "\033[33m",   # yellow — projection engine
}

# Readline "non-printing" brackets: \001 (RL_PROMPT_START_IGNORE) / \002
# (RL_PROMPT_END_IGNORE). They tell a readline-compatible line editor that the
# bytes between them occupy ZERO display columns, so colour escapes don't inflate
# the prompt's measured width. Only emit them when readline actually backs
# input(): raw \001/\002 printed by an editor that ignores them shows as garbage.
_RL_START = "\001"
_RL_END   = "\002"


def _prompt_span(color: str, text: str, *, color_on: bool, bracket: bool) -> str:
    """Colour `text`, honouring the terminal's capabilities.

    color_on=False → plain text (no escapes at all — safe on any dumb console).
    bracket=True   → wrap the escapes in readline's \001/\002 so the editor
                     excludes them from the visible column count.
    """
    if not color_on or not color:
        return text
    if bracket:
        return f"{_RL_START}{color}{_RL_END}{text}{_RL_START}{Colors.ENDC}{_RL_END}"
    return f"{color}{text}{Colors.ENDC}"


def make_prompt(user_id: str, in_multiline: bool,
                su_context: dict = None, nav_mode: dict = None,
                *, color: bool = True, readline_active: bool = False) -> str:
    """Generate a context-aware shell prompt — line-editor safe.

    Two properties keep minimal line editors (iOS a-Shell / Pyto) from drifting
    the cursor column, hiding the prompt, and locking the session:

    * **No embedded newline.** A multi-line prompt string makes such editors
      miscount the column; the caller prints blank-line spacing separately.
    * **Escapes are bracketed or absent.** With `readline_active` the colour
      escapes are wrapped in \001/\002 (zero-width to readline); with
      `color=False` (restricted console / NO_COLOR / dumb TERM) the prompt is
      plain ASCII, which is unbreakable everywhere.
    """
    def sp(col: str, text: str) -> str:
        return _prompt_span(col, text, color_on=color, bracket=readline_active)

    if in_multiline:
        return sp(Colors.DIM, "...> ")

    mode_tag = ""
    if nav_mode and nav_mode.get("active"):
        name    = nav_mode["name"]
        col     = _NAV_MODE_COLOR.get(name, Colors.CYAN)
        mode_tag = sp(col, f"[{name}]") + " "

    if su_context and su_context.get("active"):
        target = su_context.get("target")
        if target == "root":
            return f"{mode_tag}{sp(Colors.FAIL, '[root@akasha]')} {sp(Colors.FAIL, '#')} "
        return f"{mode_tag}{sp(Colors.WARNING, f'akasha/{user_id}(su:{target})')} $ "

    return f"{mode_tag}{sp(Colors.CYAN, f'akasha/{user_id}')} $ "
