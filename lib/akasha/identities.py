"""
Declared identities (platform-spec v1, "Identities declaration").

An application names the accounts it needs — a reader a restricted page is declared for, a researcher
a bench admits — in ONE file under its root (`config/identities.json`), and the platform makes them:

    {"identities": [{"name": "<id>", "idsets": ["<idset>", "<idset> on <target>", …]}]}

- **At Genesis, and at every later writer boot**, each declared identity that does not exist is
  created WITHOUT A CREDENTIAL, and its declared assignment lines are written (the gate's `assign`,
  idempotent). A declaration is a desired state and a boot converges to it; nothing is created twice.
- **The owner sets the passphrase at the `akasha>` prompt**: `user.passwd <name>` (admin, local
  console). Until then the account exists and cannot sign in — no passphrase is ever baked, shipped
  or read from an environment variable.
- **An invalid declaration stops the boot**, naming the entry: a name that is a system identity or
  `admin` / `anonymous`, a duplicate name, an id-set that is not a row of the platform's table, or a
  malformed line. A permission file that half-applies is worse than one that does not apply.

No declaration (or no application) means no declared identities; the platform's own lines (`admin`,
`anonymous`, the internal identities) come from its own seed, never from here.
"""
import json
import logging
import os
from typing import Dict, List, Tuple

from lib.akasha.api import reserved as _reserved

logger = logging.getLogger(__name__)

_RESERVED_NAMES = ("admin", "anonymous")


def load(path: str = "") -> List[Dict]:
    """The declared identities, validated: `[{"name", "lines": [(idset, target), …]}]`. Raises
    ValueError naming the entry for anything the platform refuses."""
    from lib.akasha.api import gate as _gate
    from lib.akasha.identity import _system_role
    p = path or _reserved.root("identities")
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8") as f:
        doc = json.load(f)
    rows = _gate.idsets()
    out, seen = [], set()
    for i, ent in enumerate(doc.get("identities") or []):
        name = str((ent or {}).get("name") or "").strip()
        where = "identities[%d]" % i
        if not name or any(c.isspace() for c in name):
            raise ValueError("%s: `name` must be a non-empty identifier without spaces" % where)
        if name in _RESERVED_NAMES or name.startswith("system.") or _system_role(name) is not None:
            raise ValueError("%s: %r is the platform's own identity — an application may not "
                             "declare it" % (where, name))
        if name in seen:
            raise ValueError("%s: %r is declared twice" % (where, name))
        seen.add(name)
        lines = []
        for raw in ent.get("idsets") or []:
            parts = str(raw).split()
            if len(parts) not in (1, 3) or (len(parts) == 3 and parts[1] != "on"):
                raise ValueError("%s (%s): %r is not `<idset>` or `<idset> on <target>`"
                                 % (where, name, raw))
            if parts[0] not in rows:
                raise ValueError("%s (%s): id-set %r is not a row of the platform's table"
                                 % (where, name, parts[0]))
            lines.append((parts[0], parts[2] if len(parts) == 3 else ""))
        out.append({"name": name, "lines": lines})
    return out


def reconcile(kernel, declared: List[Dict] = None) -> Tuple[int, int]:
    """Create each declared identity that is missing (no credential) and write its declared lines.
    Returns (identities created, lines added). One `[identity]` line per identity."""
    from lib.akasha.api import gate as _gate
    from lib.akasha.identity import Role
    created = added = 0
    for ent in (load() if declared is None else declared):
        name = ent["name"]
        made = False
        if not kernel.iam.get_client(name):
            kernel.iam.register_client(name, Role.USER, passphrase_hash=None,
                                       created_by="declaration", display_name=name)
            created += 1
            made = True
        n = sum(1 for idset, target in ent["lines"]
                if _gate.assign(name, idset, target).get("added"))
        added += n
        rec = kernel.iam.get_client(name) or {}
        logger.info("[identity] declared name=%s created=%s lines_added=%d credential=%s",
                    name, "yes" if made else "no", n,
                    "set" if rec.get("passphrase_hash") else "none (user.passwd %s)" % name)
    return created, added
