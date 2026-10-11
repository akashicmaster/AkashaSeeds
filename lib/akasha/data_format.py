"""
The cell's data-format id (the purge order, 3 October §4.4).

A cell's store is written in ONE data format. The first boot of a fresh directory stamps the format
this build writes (`central/DATA_FORMAT`); every later boot reads the stamp BEFORE anything opens the
store, and a directory stamped with another id — or a store with no stamp at all, written before
stamps existed — stops the boot with one line, writing nothing. There is no migration and no adoption
(rule 1): past data is discarded once. Atoms worth keeping are dumped with the build that wrote them
and described again as a pack.
"""
import logging
import os

logger = logging.getLogger("akasha.kernel")

# The format this build writes. Change it only with a change to what is ON DISK — never for a code
# change that reads the same store the same way.
DATA_FORMAT_ID = "akasha-cell-2026-10-03"

STAMP_REL = os.path.join("central", "DATA_FORMAT")
_STORE_RELS = (os.path.join("central", "nucleus.db"), os.path.join("central", "nucleus.db.silica"))


class DataFormatMismatch(RuntimeError):
    """The directory holds a store in a format this build does not write."""


def stamp_path(base_dir: str) -> str:
    return os.path.join(base_dir, STAMP_REL)


def found_id(base_dir: str) -> str:
    """The id stamped in this directory; "none" for a store with no stamp; "" for a fresh one."""
    try:
        with open(stamp_path(base_dir), encoding="utf-8") as f:
            return f.read().strip() or "none"
    except OSError:
        pass
    if any(os.path.exists(os.path.join(base_dir, r)) for r in _STORE_RELS):
        return "none"
    return ""


def check(base_dir: str) -> None:
    """Stop before the store is opened when this directory's format is not this build's."""
    found = found_id(base_dir)
    if found in ("", DATA_FORMAT_ID):
        return
    msg = ("[cell] data format found=%s expected=%s dir=%s — this build does not read it. Move this "
           "directory aside and start fresh. To keep atoms, dump them with the old build and "
           "describe them again as a pack: a directory ontology/user/<name>/ holding a PACK.json and "
           "its .ak files loads on the next boot (no REGISTRY.json edit)."
           % (found, DATA_FORMAT_ID, os.path.abspath(base_dir)))
    logger.error(msg)
    raise DataFormatMismatch(msg)


def stamp(base_dir: str) -> bool:
    """Write this build's id into a directory that has none (its genesis). Never overwrites.
    Returns True when it wrote."""
    p = stamp_path(base_dir)
    if os.path.exists(p):
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(DATA_FORMAT_ID + "\n")
        f.flush()
        os.fsync(f.fileno())
    return True
