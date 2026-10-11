"""
ENGINE-OWNED FIELDS — a reserved engine declares the meta fields it alone writes, and the STORE refuses
any other writer (the purge order, 3 October, §1.4).

Why at the store. The source engine keeps an item's `status`, its status Set and every pool's
`by_status` tally in step through one door (`source.item.status`). A model that wrote `status` into an
item's meta itself moved the item and left the tally behind — the drift a freeze then had to recount.
A rule written in a docstring is held by memory; a refusal at the store is held by construction.

The declaration (data, from the owning engine — nothing here names an engine's internals):

    declare(owner, field, concept=<reserved concept>)       the field on atoms of that concept
    declare(owner, field, member_of=(<prefix>, <suffix>))   the field on any MEMBER of a Set whose name
                                                            has that prefix and suffix — membership,
                                                            not a concept name (the §6 ruling)

The owner writes inside `writing_as(owner)`. A write that CHANGES a declared field of an atom in its
scope from anything else raises `OwnedFieldRefused` (a PermissionError) naming the field, the atom and
the owner. A write that leaves the field as it was passes — owning a field is owning its CHANGES.

The check runs INSIDE the store's atomic write (the SQLite writer thread; the Silica bank lock), so
the "old" it compares against is the record being replaced, never a copy read earlier — a stale
whole-meta write that would revert a declared field is refused, not landed. The caller's context does
not cross into the writer, so the store captures it first with `context(core, key, new_meta)` (the
owner, and the atom's Set memberships when a membership-scoped field is named) and passes it in. It
costs one reverse-membership read only for a write that names a membership-scoped field.
"""
import json
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

_DECL: List[Dict[str, Any]] = []
_FIELDS: set = set()
_tls = threading.local()


class OwnedFieldRefused(PermissionError):
    """A write changed a field another engine owns."""


def declare(owner: str, field: str, concept: str = "",
            member_of: Optional[Tuple[str, str]] = None) -> None:
    """Declare that `owner` alone writes `field` — on atoms of `concept`, or on members of a Set
    named `<prefix>…<suffix>`. Idempotent."""
    d = {"owner": str(owner), "field": str(field), "concept": str(concept or ""),
         "member_of": tuple(member_of) if member_of else None}
    if d not in _DECL:
        _DECL.append(d)
        _FIELDS.add(d["field"])


def declared() -> List[Dict[str, Any]]:
    """Every declaration: [{owner, field, scope}]."""
    out = []
    for d in _DECL:
        scope = ("concept=%s" % d["concept"]) if d["concept"] else \
                ("member of %s…%s" % d["member_of"])
        out.append({"owner": d["owner"], "field": d["field"], "scope": scope})
    return out


@contextmanager
def writing_as(owner: str):
    """The owning engine's writes run inside this. Nests; restores on exit."""
    prev = getattr(_tls, "owner", "")
    _tls.owner = str(owner)
    try:
        yield
    finally:
        _tls.owner = prev


def current() -> str:
    return getattr(_tls, "owner", "") or ""


def _meta(m: Any) -> Dict[str, Any]:
    if isinstance(m, dict):
        return m
    if not m:
        return {}
    try:
        v = json.loads(m)
        return v if isinstance(v, dict) else {}
    except (TypeError, ValueError):
        return {}


_UNSET = object()


def context(core, key: str, new_meta: Any) -> Tuple[str, Optional[List[str]]]:
    """Read on the CALLER's thread what the check needs from it: the writing owner, and — only when the
    write names a field declared by membership — the atom's Set memberships (read here because the
    store's atomic section may not read another record: the Silica bank lock is not reentrant).
    `new_meta=None` = not known yet (a merge computed from the current record): any declared field."""
    who = current()
    if not _DECL:
        return who, None
    new = {f: None for f in _FIELDS} if new_meta is None else _meta(new_meta)
    if not any(f in new for f in _FIELDS):
        return who, None
    if not any(d["member_of"] and d["field"] in new for d in _DECL):
        return who, None
    try:
        return who, list(core.get_collections_for_key(key) or [])
    except Exception:
        return who, []


def check(core, key: str, new_meta: Any, old_meta: Any = _UNSET, who: Optional[str] = None,
          cols: Optional[List[str]] = None) -> None:
    """Refuse this write if it changes a field another engine owns. `core` is the backend about to
    write. A store passes the record it is replacing (`old_meta`) and the caller's `context` (`who`,
    `cols`); without them they are read here (the caller's thread, the record as it is now)."""
    if not _DECL:
        return
    new = _meta(new_meta)
    # a field can only change if the new meta names it or the old one did; the old is read only when
    # the new names one (a write that drops a declared field is caught at the next write that names it
    # — the RMW writers always carry the whole meta)
    if not any(f in new for f in _FIELDS):
        return
    if old_meta is _UNSET:
        try:
            row = core.get_chunk_raw(key)
        except Exception:
            row = None
        old_meta = (row or {}).get("meta")
    old = _meta(old_meta)
    if who is None:
        who = current()
    for d in _DECL:
        f = d["field"]
        if f not in new or new.get(f) == old.get(f) or who == d["owner"]:
            continue
        if d["concept"]:
            in_scope = d["concept"] in (new.get("concept"), old.get("concept"))
        else:
            if cols is None:
                try:
                    cols = list(core.get_collections_for_key(key) or [])
                except Exception:
                    cols = []
            pre, suf = d["member_of"]
            in_scope = any(c.startswith(pre) and c.endswith(suf) for c in cols)
        if in_scope:
            raise OwnedFieldRefused(
                "field '%s' of %s is owned by the %s engine — write it through that engine "
                "(writer: %s; %r → %r)" % (f, key, d["owner"], who or "not the owner",
                                           old.get(f), new.get(f)))
