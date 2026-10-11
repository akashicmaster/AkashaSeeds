"""
The one door to an elevated session (the purge order, 3 October §4.1: authority_eval 6 → 0).

Privilege that can be taken anywhere is privilege nobody can audit. Outside provisioning
(`workbench/provision.py`, the authority), no module calls `get_session("admin")` or enters
`system_context()`; a module that must act as the cell's operator asks HERE, naming a PURPOSE this
table declares. The table is the whole list of reasons the platform elevates — one row each, with the
identity it acts as — so "who runs as admin, and why?" is answered by reading one dict, and a new
reason is a reviewed row, never a quiet call. An undeclared purpose raises.

One `[authority] elevated purpose=<p> identity=<id>` line per purpose per process (the first time).
"""
import logging
from typing import Dict, Tuple

logger = logging.getLogger("akasha.kernel")

# purpose → (identity, why)
PURPOSES: Dict[str, Tuple[str, str]] = {
    "ontology.load": ("admin", "the boot loader writes the declared packs into the universal scope"),
    "driver": ("admin", "the workbench driver reads and records its societies' autorun state, "
                        "their sweeps and their leaderboards, in every group it drives"),
    "retention.expiry": ("admin", "validity expiry evicts expired membranes from the horizon"),
}

_logged = set()


class UndeclaredPurpose(PermissionError):
    """An elevation asked for a purpose the table does not declare."""


def elevated(kernel, purpose: str):
    """The session a declared `purpose` acts as."""
    row = PURPOSES.get(str(purpose or ""))
    if row is None:
        raise UndeclaredPurpose("no elevation is declared for purpose %r (lib/akasha/api/authority.py)"
                                % purpose)
    ident = row[0]
    if purpose not in _logged:
        _logged.add(purpose)
        logger.info("[authority] elevated purpose=%s identity=%s", purpose, ident)
    return kernel.manager.get_session(ident)
