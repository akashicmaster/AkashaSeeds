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


def make_prompt(user_id: str, in_multiline: bool,
                su_context: dict = None, nav_mode: dict = None) -> str:
    """Generate a context-aware shell prompt string."""
    if in_multiline:
        return _c(Colors.DIM, "...> ")

    mode_tag = ""
    if nav_mode and nav_mode.get("active"):
        name    = nav_mode["name"]
        col     = _NAV_MODE_COLOR.get(name, Colors.CYAN)
        mode_tag = _c(col, f"[{name}]") + " "

    if su_context and su_context.get("active"):
        target = su_context.get("target")
        if target == "root":
            return f"\n{mode_tag}{_c(Colors.FAIL, '[root@akasha]')} {_c(Colors.FAIL, '#')} "
        return f"\n{mode_tag}{_c(Colors.WARNING, f'akasha/{user_id}(su:{target})')} $ "

    return f"\n{mode_tag}{_c(Colors.CYAN, f'akasha/{user_id}')} $ "
