"""
dont.* ops, moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

Every function takes the kernel (the heart) as its first argument: it is the object the
dispatcher / timer registry hands in, never imported. Bodies are the kernel's own, moved
verbatim except `self.` → `kernel.` and intra-family calls.
"""
import os
import re
import sys
import time
import json
import uuid
import logging
import hashlib
import functools
from typing import Dict, Any, Optional, List, Callable
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.concepts import _universal

logger = logging.getLogger("Akasha.Kernel")


def handle_dont_create(kernel, rid, data, session) -> dict:
    """Create or update a named delegation set with provenance metadata."""
    ctx = session.local_cortex
    client_id = session.client_id
    name = (data.get("name") or "").strip()
    if not name:
        return _err(rid, -32602, "dont.create requires 'name'")
    set_name = f"dont:{name}" if not name.startswith("dont:") else name
    description = (data.get("description") or data.get("desc") or "").strip()
    import time as _time
    meta = {
        "type": "donation_set",
        "created_by": client_id,
        "created_at": _time.time(),
        "description": description,
        "donations": []
    }
    ctx.create_donation_set(set_name, meta)
    return _ok(rid, {"set": set_name, "status": "created", "meta": meta})


def handle_dont_add(kernel, rid, data, session) -> dict:
    """Add atoms to a delegation set."""
    ctx = session.local_cortex
    scopes = session.active_scopes
    name = (data.get("name") or "").strip()
    targets = data.get("targets") or data.get("target") or []
    if not name:
        return _err(rid, -32602, "dont.add requires 'name'")
    set_name = f"dont:{name}" if not name.startswith("dont:") else name

    if isinstance(targets, str):
        targets = [t.strip() for t in targets.split() if t.strip()]

    history = ctx.stream(10)
    added = []
    for t in targets:
        resolved = _universal.resolve_target(kernel, t, session, history)
        if not resolved or isinstance(resolved, list):
            resolved = t
        if ctx.get_chunk(resolved):
            ctx.core.add_to_collection(set_name, resolved)
            added.append(resolved)

    return _ok(rid, {"set": set_name, "added": len(added), "keys": added})


def handle_dont_send(kernel, rid, data, session) -> dict:
    """
    Donate all atoms in a delegation set to a shared space.
    'to': "universal" | "group:<id>"
    'open': bool (default False) — if True, extend original scope instead of copying
    """
    ctx = session.local_cortex
    scopes = session.active_scopes
    client_id = session.client_id
    name = (data.get("name") or "").strip()
    destination = (data.get("to") or "").strip()
    do_open = bool(data.get("open", False))

    if not name or not destination:
        return _err(rid, -32602, "dont.send requires 'name' and 'to'")
    set_name = f"dont:{name}" if not name.startswith("dont:") else name

    # Resolve target engine
    if destination == "universal":
        if "role:librarian" not in scopes:
            return _err(rid, -32003, "Universal donation requires librarian role")
        target_engine = session.nucleus
        target_scope = "scope:sys:universal"
        target_label = "nucleus"
    elif destination.startswith("group:"):
        gid = destination[6:]
        if f"scope:group_{gid}" not in scopes:
            return _err(rid, -32003, f"Not a member of group '{gid}'")
        target_engine = session.group_engines.get(gid)
        if not target_engine:
            return _err(rid, -32002, f"Group space '{gid}' not loaded in this session")
        target_scope = f"scope:group_{gid}"
        target_label = f"group:{gid}"
    else:
        return _err(rid, -32602, f"Unknown destination '{destination}'. Use 'universal' or 'group:<id>'")

    # List set members
    member_keys = ctx.core.get_collection_members(set_name)
    if not member_keys:
        return _err(rid, -32002, f"Delegation set '{set_name}' is empty or not found")

    import time as _time
    import json as _json
    donated = []
    skipped = []

    for key in member_keys:
        row = ctx.core.get_chunk_raw(key)
        if not row:
            skipped.append(key)
            continue
        content = row["content"] or ""
        try:
            meta = _json.loads(row.get("meta") or "{}")
        except Exception:
            meta = {}

        if do_open:
            # "Open" mode: extend original atom's scope (no copy)
            ctx.core.put_chunk_access(key, [target_scope])
        else:
            # Copy mode: write atom to target engine
            target_engine.put_atom(content, meta, author=client_id)
            # Copy all aliases for this key to target
            for alias in ctx.get_aliases_by_key(key):
                target_engine.core.put_alias(key, alias)
        # Mirror set membership in target
        target_engine.add_to_set(set_name, key)
        donated.append(key)

    # Record donation in origin set metadata
    origin_meta = ctx.get_donation_set_meta(set_name) or {}
    donations = origin_meta.get("donations", [])
    donation_record = {
        "target": target_label,
        "donated_at": _time.time(),
        "atom_count": len(donated),
        "mode": "open" if do_open else "copy",
    }
    donations.append(donation_record)
    origin_meta["donations"] = donations
    ctx.update_donation_set_meta(set_name, origin_meta)

    # Record receipt in target set metadata
    receipt_meta = {
        "type": "donation_receipt",
        "source_cell": client_id,
        "source_set": set_name,
        "donated_at": donation_record["donated_at"],
        "atom_count": len(donated),
        "mode": donation_record["mode"],
    }
    target_engine.upsert_set_meta(set_name, receipt_meta)

    return _ok(rid, {
        "status": "donated",
        "set": set_name,
        "to": target_label,
        "mode": donation_record["mode"],
        "donated": len(donated),
        "skipped": len(skipped),
        "donated_at": donation_record["donated_at"],
    })


def handle_dont_ls(kernel, rid, data, session) -> dict:
    """List delegation sets and their donation history."""
    ctx = session.local_cortex
    name = (data.get("name") or "").strip()
    if name:
        set_name = f"dont:{name}" if not name.startswith("dont:") else name
        meta = ctx.get_donation_set_meta(set_name)
        if meta is None:
            return _err(rid, -32002, f"Delegation set '{set_name}' not found")
        members = ctx.core.get_collection_members(set_name)
        return _ok(rid, {"set": set_name, "atom_count": len(members), "meta": meta})
    else:
        sets = ctx.list_donation_sets()
        for s in sets:
            s["atom_count"] = len(ctx.core.get_collection_members(s["name"]))
        return _ok(rid, {"donation_sets": sets})


def handle_dont_open(kernel, rid, data, session) -> dict:
    """Convenience: dont.send with open=True (extend original scope, no copy)."""
    return handle_dont_send(kernel, rid, {**data, "open": True}, session)
