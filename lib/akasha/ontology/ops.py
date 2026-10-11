"""
The onto.* RPC ops — moved out of the kernel (backend layout order 2026-09-20).

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
from lib.akasha.pagination import paginate as _paginate, resolve_limit as _rlimit, resolve_offset as _roffset
from lib.akasha.ontology import loader

logger = logging.getLogger("Akasha.Kernel")


def handle_onto_dump(kernel, rid, data, ctx) -> dict:
    """
    Flexible ontology dump.
    mode: atoms (default) | links | antonyms | aliases | sets | namespaces
    sort: alpha (default) | count | recent
    ns:         namespace prefix filter, e.g. "word:en"
    rel:        relation type filter for links mode, e.g. "sys:antonym"
    collection: collection name for sets mode
    limit:      max items returned (default 500, max 5000)
    pattern:    alias LIKE pattern for aliases mode
    """
    mode    = (data.get("mode") or "atoms").lower()
    sort    = (data.get("sort") or "alpha").lower()
    ns      = (data.get("ns") or "").rstrip(":")
    rel_f   = (data.get("rel") or "")
    coll    = (data.get("collection") or "")
    pattern = (data.get("pattern") or "")
    cursor  = data.get("cursor")
    # Cursor pagination over the FULL sorted result — so pages are consistent, the
    # list must be built and sorted whole before slicing. For the unbounded modes
    # (links, atoms) `scan` bounds that universe (admin may raise it); the page
    # envelope's `total` is the size within the scanned universe.
    scan    = min(int(data.get("scan") or 20000), 100000)

    def _page(items):
        window, page = _paginate(items, data.get("limit"), cursor,
                                 default=500, max_limit=5000)
        return window, page

    def _best_alias(key: str) -> str:
        als = ctx.core.get_aliases_by_key(key)
        if not als:
            _nuc = getattr(ctx, '_nucleus', None)
            if _nuc:
                als = _nuc.core.get_aliases_by_key(key)
        if not als:
            return key[:16]
        return min(als, key=lambda a: (a.count(":"), len(a)))

    if mode == "namespaces":
        depth = int(data.get("depth") or 1)
        items = ctx.core.get_namespace_counts(depth=depth)
        _nuc = getattr(ctx, '_nucleus', None)
        if _nuc:
            nuc_items = _nuc.core.get_namespace_counts(depth=depth)
            local_ns = {i["ns"]: i for i in items}
            for ni in nuc_items:
                ns_key = ni["ns"]
                if ns_key in local_ns:
                    local_ns[ns_key]["count"] += ni["count"]
                else:
                    items.append(ni)
                    local_ns[ns_key] = ni
        if sort == "alpha":
            items.sort(key=lambda x: x["ns"])
        window, page = _page(items)
        return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})

    if mode in ("links", "antonyms"):
        effective_rel = "sys:antonym" if mode == "antonyms" else rel_f
        rows = ctx.core.get_all_links(rel_filter=effective_rel or None, limit=scan)
        items = []
        for r in rows:
            src_a = _best_alias(r["src"])
            dst_a = _best_alias(r["dst"])
            items.append({"src": src_a, "dst": dst_a, "rel": r["rel"], "w": r["w"]})
        if sort == "alpha":
            items.sort(key=lambda x: (x["rel"], x["src"]))
        window, page = _page(items)
        return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})

    if mode == "sets":
        # The set is `collection=`, or the word after `sets` — the CLI's positional slot after the
        # mode is `ns`, so `onto.dump sets <set>` arrives there (seeds 13 findings P1: it was read
        # as a namespace filter and the dump fell back to one fixed collection, reporting 0).
        # No set named → the sets themselves (local + nucleus), as `s.ls` with no name lists them.
        name = coll or str(data.get("ns") or "").strip()
        if not name:
            names = ctx.list_set_names()
            window, page = _page([{"collection": n} for n in names])
            return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})
        keys = ctx.get_collection_members(name)
        if not keys and not name.startswith("set:"):         # as `s.ls` does
            keys = ctx.get_collection_members("set:" + name)
            if keys:
                name = "set:" + name
        items = []
        for k in keys:
            main = _best_alias(k)
            items.append({"alias": main, "key": k[:12]})
        if sort == "alpha":
            items.sort(key=lambda x: x["alias"])
        elif sort == "count":
            pass  # no count available per-member
        window, page = _page(items)
        out = {"mode": mode, "collection": name, "count": len(window), "items": window, "page": page}
        if not items:
            from lib.akasha.ontology.loader import loading_note
            if loading_note(kernel):
                out["note"] = loading_note(kernel)
        return _ok(rid, out)

    if mode == "aliases":
        pat = pattern or (f"{ns}:%" if ns else "%")
        rows = ctx.core.get_aliases_by_pattern(pat)
        items = [{"alias": r["alias"], "key": r["key"][:12]} for r in rows]
        if sort == "alpha":
            items.sort(key=lambda x: x["alias"])
        window, page = _page(items)
        return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})

    # default: atoms — one row per distinct atom key, primary alias + content preview.
    # Composed from ISA primitives (alias pattern match + per-key content) rather
    # than a relational JOIN, so it holds on non-SQL backends too.
    pat = f"{ns}:%" if ns else "%:%"
    alias_rows = list(ctx.core.get_aliases_by_pattern(pat))
    _nucleus = getattr(ctx, '_nucleus', None)
    if _nucleus:
        alias_rows += list(_nucleus.core.get_aliases_by_pattern(pat))
    seen: set = set()
    items = []
    for r in alias_rows[:scan]:
        key = r["key"]
        if key in seen:
            continue
        seen.add(key)
        row = ctx.core.get_chunk_raw(key)
        if row is None and _nucleus:
            row = _nucleus.core.get_chunk_raw(key)
        preview = ((row["content"] if row else "") or "")[:100].replace("\n", " ")
        items.append({"alias": r["alias"], "key": key[:12], "preview": preview})
    items.sort(key=lambda x: x["alias"])
    window, page = _page(items)
    return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})


def handle_onto_export(kernel, rid, data, ctx) -> dict:
    """
    Export ontology atoms to .ak files in out/ (or a specified directory).

    Params
    ------
    ns         : namespace prefix, e.g. "myth" — exports all myth:* atoms.
                 May be a comma-separated list: "myth,deity,era".
                 Omit (or "*") to export everything.
    collection : set name filter, e.g. "ontology.narrative_genres".
                 When given, only atoms that belong to this collection
                 are exported (AND-ed with ns if both are supplied).
    era        : era alias filter, e.g. "ancient".  Only atoms that carry
                 the link  ln X era:<era> sys:part_of  are included.
    out        : output directory, relative to project root (default: out/).
    split      : "ns" (one file per namespace, default)
               | "single" (one file, filename = ns or "export")
               | "set"    (one file per collection the atoms belong to)
    """
    import os, re, textwrap

    core = ctx.core

    # ── resolve project root ──────────────────────────────────────
    _kdir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # lib/akasha/
    _ldir  = os.path.dirname(_kdir)                       # lib/
    _proot = os.path.dirname(_ldir)                       # project root

    out_base = os.path.join(_proot, (data.get("out") or "out").strip("/"))
    os.makedirs(out_base, exist_ok=True)

    split = (data.get("split") or "ns").lower()

    # ── build namespace list ──────────────────────────────────────
    ns_raw = (data.get("ns") or "").strip()
    if ns_raw in ("", "*"):
        ns_list = []            # no ns filter
    else:
        ns_list = [n.strip().rstrip(":") for n in ns_raw.split(",") if n.strip()]

    coll_filter = (data.get("collection") or "").strip()
    era_filter  = (data.get("era") or "").strip().lstrip("era:")

    # ── collect candidate keys ────────────────────────────────────
    def _primary_alias(key: str) -> str:
        als = core.get_aliases_by_key(key)
        if not als:
            return ""
        return min(als, key=lambda a: (a.count(":"), len(a)))

    def _aliases_for_ns(ns: str):
        """Return {key: primary_alias} for all atoms in namespace ns."""
        rows = core.get_aliases_by_pattern(f"{ns}:%")
        seen = {}
        for r in rows:
            k = r["key"]
            if k in seen:
                continue
            a = r["alias"]
            # keep the primary (shortest / fewest colons)
            if k not in seen or (a.count(":"), len(a)) < (seen[k].count(":"), len(seen[k])):
                seen[k] = a
        return seen  # {key: alias}

    # gather all candidate keys → {key: primary_alias}
    if ns_list:
        candidates = {}
        for ns in ns_list:
            candidates.update(_aliases_for_ns(ns))
    else:
        # all aliases in DB
        rows = core.get_aliases_by_pattern("%:%")
        candidates = {}
        for r in rows:
            k = r["key"]
            a = r["alias"]
            if k not in candidates or (a.count(":"), len(a)) < \
                    (candidates[k].count(":"), len(candidates[k])):
                candidates[k] = a

    # ── apply collection filter ───────────────────────────────────
    if coll_filter:
        coll_keys = set(core.get_collection_members(coll_filter))
        candidates = {k: v for k, v in candidates.items() if k in coll_keys}

    # ── apply era filter ─────────────────────────────────────────
    if era_filter:
        era_alias = f"era:{era_filter}"
        era_key   = core.get_key_by_alias(era_alias)
        if era_key:
            era_keys = {
                lk["src"]
                for lk in core.get_incoming_links(era_key, rel_pattern="sys:part_of")
            }
            candidates = {k: v for k, v in candidates.items() if k in era_keys}

    if not candidates:
        return _ok(rid, {"exported": 0, "files": [], "note": "no atoms matched filters"})

    # ── build atom blocks ─────────────────────────────────────────
    def _escape(s: str) -> str:
        return s.replace('\\', '\\\\').replace('"', '\\"')

    def _atom_block(key: str, alias: str) -> str:
        """Return the .ak text block for one atom."""
        raw = core.get_chunk_raw(key)
        content = (raw.get("content") or "") if raw else ""
        lines = [f'def "{alias}" "{_escape(content)}"']

        # outgoing links
        for lk in core.get_adjacent_links(key):
            dst_alias = _primary_alias(lk["dst"])
            if not dst_alias:
                continue
            rel = lk["rel"]
            lines.append(f"ln {alias} {dst_alias} {rel}")

        # collection memberships
        for cname in sorted(core.get_collections_for_key(key)):
            lines.append(f'set.add name="{cname}" id="{alias}"')

        return "\n".join(lines)

    # ── group by split mode ───────────────────────────────────────
    # groups: {filename_stem: [(key, alias), ...]}
    groups: dict = {}

    if split == "set":
        # group by the first ontology.* collection the atom belongs to
        for key, alias in candidates.items():
            colls = [c for c in core.get_collections_for_key(key)
                     if c.startswith("ontology.")]
            stem = colls[0] if colls else "misc"
            groups.setdefault(stem, []).append((key, alias))
    elif split == "single":
        stem = (coll_filter or (ns_list[0] if ns_list else "export"))
        stem = re.sub(r"[^\w.\-]", "_", stem)
        groups[stem] = list(candidates.items())
    else:  # "ns" (default)
        for key, alias in candidates.items():
            stem = alias.split(":")[0] if ":" in alias else "misc"
            groups.setdefault(stem, []).append((key, alias))

    # ── write files ───────────────────────────────────────────────
    written_files = []
    total_atoms   = 0

    for stem, pairs in sorted(groups.items()):
        pairs.sort(key=lambda p: p[1])          # alpha by alias
        filename = re.sub(r"[^\w.\-]", "_", stem) + ".ak"
        filepath = os.path.join(out_base, filename)

        header = (
            f"# Akasha ontology export — {stem}\n"
            f"# atoms: {len(pairs)}"
            + (f"  ns: {ns_raw}" if ns_raw else "")
            + (f"  collection: {coll_filter}" if coll_filter else "")
            + (f"  era: {era_filter}" if era_filter else "")
            + "\n#\n"
        )

        blocks = [header]
        for key, alias in pairs:
            blocks.append(_atom_block(key, alias))
            blocks.append("")   # blank line separator

        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(blocks))

        written_files.append({"file": os.path.relpath(filepath, _proot),
                               "atoms": len(pairs)})
        total_atoms += len(pairs)

    return _ok(rid, {
        "exported": total_atoms,
        "files":    written_files,
        "out_dir":  os.path.relpath(out_base, _proot),
    })


def handle_onto_reload(kernel, rid, data, session, scopes) -> dict:
    """
    Remove ontology sentinels and re-trigger _boot_load_ontology.
    Existing atoms are idempotent (re-written but unchanged). New or
    modified .ak/.csl/curation files will be picked up.
    Requires role:librarian.
    """
    if "role:librarian" not in scopes:
        return _err(rid, -32601, "onto.reload requires role:librarian")

    confirm = (data.get("confirm") or "").strip()
    if confirm != "RELOAD":
        return _err(rid, -32602,
            "⚠️  This will clear all ontology load sentinels and re-trigger a full boot load.\n"
            "Modified .ak / .csl / curation files will be picked up on next scan.\n"
            "Existing atoms are re-written idempotently (no data loss).\n\n"
            "To proceed: onto.reload confirm=\"RELOAD\"")

    nucleus = getattr(session, 'nucleus', None)
    if not nucleus:
        return _err(rid, -32001, "No nucleus available for this session")

    _PREFIXES = [
        "ont:ak:f:",            # ⚠️ per-file atom sentinel — MUST be cleared or the re-load is
                                # a silent no-op. Phase 1 skips any file whose ont:ak:f:* alias
                                # is still present (kernel.py ~1052), so leaving these behind
                                # means the pack re-enters but re-writes NO atoms — the exact
                                # failure that left recipe-content chunks empty and un-healable
                                # by onto.reload (docs/handoff/recipe-body-empty-content-chunk.md).
        "ont:ak:atoms:loaded:",
        "ont:ak:loaded:",
        "ont:csl:loaded:",
        "ont:curation:loaded:",
        # S2-k4 — clear the relations-phase completion marker too, so `_relations_ready()` reads
        # False WHILE this reload re-runs (the relations phase re-writes it at the end). Without
        # this the gate stays open during a reload and a sweep pick could run against a graph that
        # is being re-imported. The `.done` FS markers below cover the first-boot form of the same.
        "ont:ak:relations:all:",
    ]
    removed = []
    for prefix in _PREFIXES:
        rows = nucleus.core.get_aliases_by_pattern(prefix) or []
        for row in rows:
            alias = row["alias"] if isinstance(row, dict) else row
            nucleus.core.delete_alias(alias)
            removed.append(alias)

    # Also remove filesystem sentinel files so _boot_load_ontology re-runs fully.
    import glob as _glob
    _sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
    _removed_files = 0
    for _sf in _glob.glob(os.path.join(_sent_dir, "*.done")):
        try:
            os.remove(_sf)
            _removed_files += 1
        except OSError:
            pass

    import threading as _thr
    _thr.Thread(target=kernel._boot_load_ontology, daemon=True,
                name="ontology-reload").start()

    return _ok(rid, {
        "status": "reload_triggered",
        "sentinels_cleared": removed,
        "sentinel_files_removed": _removed_files,
        "message": "Ontology reload started in background.",
    })


def handle_onto_reconcile(kernel, rid, data, session, scopes) -> dict:
    """[onto.reconcile] Retire ontology atoms a pack no longer contributes — the data-side
    analog of the seed code prune. Fenced to provenance=ontology + no user scope + cross-pack
    ref-count; soft-evict (recoverable) by default. `dry=yes` (default) reports without
    mutating; `apply=yes` retires; `compact=yes` (superuser) hard-drops evicted orphans.
    Requires role:librarian. Spec: docs/for-llm/ontology-reconciliation-spec.md."""
    if "role:librarian" not in scopes:
        return _err(rid, -32601, "onto.reconcile requires role:librarian")
    nucleus = getattr(session, "nucleus", None)
    if not nucleus:
        return _err(rid, -32001, "No nucleus available for this session")
    from lib.akasha.ontology_reconcile import OntologyReconciler
    R = OntologyReconciler(nucleus)

    def _truthy(v):
        return str(v).strip().lower() in ("yes", "true", "1", "on")

    if _truthy(data.get("compact")):
        if "role:superuser" not in scopes and "scope:sys:admin" not in scopes:
            return _err(rid, -32601, "onto.reconcile compact=yes requires role:superuser")
        res = R.compact(scopes)
        return _ok(rid, {"status": "compacted", "dropped_count": len(res.get("dropped", [])),
                         "dropped": res.get("dropped", [])[:50]})

    apply = _truthy(data.get("apply"))
    dry = not apply
    pack = (data.get("pack") or "").strip()
    packs = loader.active_reconcile_packs(kernel, session, pack)
    reports = []
    for pn in packs:
        keys, names = loader.pack_def_keys(kernel, session, pn)
        if not names:
            continue                         # pack absent / not loaded → nothing to diff
        R.stamp_provenance(pn, list(keys))
        rep = R.reconcile(pn, keys, dry_run=dry)
        reports.append(rep)
    total_retired = sum(len(r["retired"]) for r in reports)
    total_warn = sum(len(r["user_ref_warnings"]) for r in reports)
    return _ok(rid, {
        "status": "dry_run" if dry else "applied",
        "packs": [r["pack"] for r in reports],
        "retired_total": total_retired,
        "user_ref_warning_total": total_warn,
        "reports": reports,
        "hint": ("Preview only — re-run with apply=yes to retire (soft-evict, recoverable)."
                 if dry else "Retired via soft-evict; re-add the pack to restore."),
    })


def handle_onto_reset(kernel, rid, data, session, scopes) -> dict:
    """
    ⚠️  DANGEROUS ZONE ⚠️

    Hard-reset nucleus: deletes ALL atoms, links, and aliases except the
    35 DNA primal atoms, then re-triggers _boot_load_ontology.
    This CANNOT be undone.

    Required: confirm="RESET"
    Requires role:librarian.
    """
    if "role:librarian" not in scopes:
        return _err(rid, -32601, "onto.reset requires role:librarian")

    confirm = (data.get("confirm") or "").strip()
    if confirm != "RESET":
        return _err(rid, -32602,
            "⚠️  DANGEROUS ZONE ⚠️\n"
            "onto.reset will delete ALL ontology data from nucleus.\n"
            "Only the 35 DNA primal atoms will be preserved.\n"
            "All atoms, links, aliases, namespace_counts, and collections will be erased.\n"
            "This CANNOT be undone.\n\n"
            "To proceed: onto.reset confirm=\"RESET\"")

    nucleus = getattr(session, 'nucleus', None)
    if not nucleus:
        return _err(rid, -32001, "No nucleus available for this session")

    from lib.akasha.dna import get_primal_sequence
    import hashlib as _hl
    dna = get_primal_sequence()
    dna_keys = [_hl.sha256(t.encode("utf-8")).hexdigest() for t in dna.values()]

    nucleus.core.clear_ontology_data(dna_keys)
    nucleus.core._unfold_dna()

    # Remove filesystem sentinel files so the reload starts clean.
    import glob as _glob
    _sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
    for _sf in _glob.glob(os.path.join(_sent_dir, "*.done")):
        try:
            os.remove(_sf)
        except OSError:
            pass

    import threading as _thr
    _thr.Thread(target=kernel._boot_load_ontology, daemon=True,
                name="ontology-reset-reload").start()

    return _ok(rid, {
        "status": "reset_complete",
        "dna_atoms_preserved": len(dna_keys),
        "message": "Nucleus cleared. DNA atoms restored. Ontology reload started.",
    })


def handle_onto_pack_list(kernel, rid, data, session, scopes) -> dict:
    """
    List all ontology packages defined in ontology/REGISTRY.json.

    Each package entry includes:
      autoload  — true for base (always loaded), false for opt-in packs
      enabled   — true when listed in config/ontology/packs.json["enabled"]
      loaded    — true when a filesystem sentinel file exists for this pack
      ak_files  — number of .ak files in the package directory
    """
    import json as _json
    import glob as _glob

    _kernel_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _project_dir = os.path.dirname(os.path.dirname(_kernel_dir))
    ont_dir      = os.path.join(_project_dir, "ontology")
    cfg_path     = os.path.join(_project_dir, "config", "ontology", "packs.json")
    _sent_dir    = os.path.join(kernel.base_dir, "central", "sentinels")

    try:
        with open(cfg_path) as f:
            _cfg = _json.load(f)
            enabled  = set(_cfg.get("enabled", []))
            load_all = bool(_cfg.get("load_all", False))
    except Exception:
        enabled, load_all = set(), False

    def _sentinel_loaded(pack_name: str) -> bool:
        return bool(os.path.isdir(_sent_dir) and
                    _glob.glob(os.path.join(_sent_dir, f"{pack_name}_*.done")))

    def _pack_meta(pack_dir: str) -> dict:
        fpath = os.path.join(pack_dir, "PACK.json")
        if os.path.isfile(fpath):
            try:
                with open(fpath) as f:
                    return _json.load(f)
            except Exception:
                pass
        return {}

    def _ak_count(pack_dir: str) -> int:
        if not os.path.isdir(pack_dir):
            return 0
        return sum(1 for fn in os.listdir(pack_dir) if fn.endswith(".ak"))

    # every pack root's REGISTRY.json, platform first, for the ordered package list
    from lib.akasha.ontology.loader import (reserved_dirs as _reserved_dirs,
                                            registry_packages as _registry_packages,
                                            ontology_roots as _ontology_roots)
    registry: list = _registry_packages()
    RESERVED = _reserved_dirs()                         # the registries' own (group 4, 4.9)
    registry_names = set()
    packages = []
    for pkg in registry:
        pname    = pkg.get("name", "")
        autoload = pkg.get("autoload", False)
        if not pname or pname in RESERVED:
            continue
        registry_names.add(pname)
        pack_dir = pkg.get("_dir") or os.path.join(ont_dir, pname)
        pmeta    = _pack_meta(pack_dir)
        packages.append({
            "name":        pname,
            "label":       pmeta.get("label", pname),
            "description": pmeta.get("description", ""),
            "autoload":    autoload,
            "enabled":     autoload or load_all or pname in enabled,
            "loaded":      _sentinel_loaded(pname),
            "ak_files":    _ak_count(pack_dir),
            "license":     pmeta.get("license", ""),
        })

    # Packs enabled in config but absent from REGISTRY (user-added externals)
    for pname in sorted(enabled - registry_names):
        if pname in RESERVED:
            continue
        from lib.akasha.ontology.loader import pack_dir as _pack_dir_of
        pack_dir = _pack_dir_of(pname)
        pmeta    = _pack_meta(pack_dir)
        packages.append({
            "name":        pname,
            "label":       pmeta.get("label", pname),
            "description": pmeta.get("description", ""),
            "autoload":    False,
            "enabled":     True,
            "loaded":      _sentinel_loaded(pname),
            "ak_files":    _ak_count(pack_dir),
            "license":     pmeta.get("license", ""),
            "unregistered": True,
        })

    return _ok(rid, {
        "packages": packages,
        "enabled":  sorted(enabled),
        "load_all": load_all,
    })


def handle_onto_pack_enable(kernel, rid, data, session, scopes) -> dict:
    """
    Enable an optional pack and trigger its load in the background.
    All packages live at ontology/{name}/.  Requires role:librarian.
    """
    import json as _json
    if "role:librarian" not in scopes:
        return _err(rid, -32601, "onto.pack.enable requires role:librarian")

    pack_name = data.get("name", "").strip()
    if not pack_name:
        return _err(rid, -32602, "Missing param: name")
    from lib.akasha.ontology.loader import (registry_packages as _registry_packages,
                                            pack_dir as _pack_dir_of, project_dir as _proj)
    if any(p.get("name") == pack_name and p.get("autoload") for p in _registry_packages()):
        return _err(rid, -32602, f"Pack '{pack_name}' has autoload:true — no enable needed.")

    # the opt-in list the loader reads: the same project directory (`loader.project_dir`)
    _project_dir = _proj()
    cfg_path     = os.path.join(_project_dir, "config", "ontology", "packs.json")

    pack_dir = _pack_dir_of(pack_name)
    if not os.path.isdir(pack_dir):
        return _err(rid, -32602, f"Pack '{pack_name}' is in no pack root")

    os.makedirs(os.path.join(_project_dir, "config", "ontology"), exist_ok=True)
    try:
        with open(cfg_path) as f:
            cfg = _json.load(f)
    except Exception:
        cfg = {"enabled": []}
    cfg.setdefault("enabled", [])

    if pack_name not in cfg["enabled"]:
        cfg["enabled"].append(pack_name)
        with open(cfg_path, "w") as f:
            _json.dump(cfg, f, indent=2)

    import threading as _thr
    _thr.Thread(target=kernel._boot_load_ontology, daemon=True,
                name=f"ontology-pack-{pack_name}").start()

    return _ok(rid, {
        "status":   "enabled",
        "pack":     pack_name,
        "location": os.path.relpath(pack_dir, _project_dir) + "/",
        "message":  f"Pack '{pack_name}' enabled. Load running in background.",
    })


def handle_onto_pack_disable(kernel, rid, data, session, scopes) -> dict:
    """Disable an optional pack (does not remove already-loaded atoms)."""
    import json as _json
    if "role:librarian" not in scopes:
        return _err(rid, -32601, "onto.pack.disable requires role:librarian")

    pack_name = data.get("name", "").strip()
    if not pack_name:
        return _err(rid, -32602, "Missing param: name")
    if pack_name in ("base1", "base2", "base3"):
        return _err(rid, -32602, f"Pack '{pack_name}' is built-in and cannot be disabled.")

    from lib.akasha.ontology.loader import project_dir as _proj
    cfg_path = os.path.join(_proj(), "config", "ontology", "packs.json")

    try:
        with open(cfg_path) as f:
            cfg = _json.load(f)
    except Exception:
        cfg = {"enabled": []}
    cfg.setdefault("enabled", [])

    if pack_name in cfg["enabled"]:
        cfg["enabled"].remove(pack_name)
        with open(cfg_path, "w") as f:
            _json.dump(cfg, f, indent=2)

    return _ok(rid, {
        "status": "disabled",
        "pack": pack_name,
        "message": f"Pack '{pack_name}' disabled. Atoms remain in nucleus until onto.reset.",
    })


def handle_onto_report(kernel, rid, data, ctx) -> dict:
    """Alias collision report — reads alias_collision_log from nucleus."""
    nucleus = getattr(ctx, '_nucleus', None)
    src = nucleus if nucleus else ctx
    since = float(data.get("since", 0.0) or 0.0)
    limit = int(data.get("limit", 200) or 200)
    entries_raw = src.get_alias_collision_log(since=since, limit=limit, unresolved_only=False)
    should_clear = str(data.get("clear", "")).lower() in ("true", "1", "yes")
    if should_clear and entries_raw:
        nucleus_core = getattr(src, 'core', None)
        if nucleus_core:
            try:
                nucleus_core.clear_alias_collision_log()
            except Exception:
                pass
    overwrites = sum(1 for e in entries_raw if e.get("event") == "overwrite")
    leaf_skips = sum(1 for e in entries_raw if e.get("event") == "leaf_skip")
    entries = [
        {"alias": e["alias"], "winner": e.get("new_key", ""), "loser": e.get("old_key", ""),
         "event": e.get("event", ""), "ts": e.get("ts", 0)}
        for e in entries_raw
    ]
    return _ok(rid, {"overwrites": overwrites, "leaf_skips": leaf_skips, "entries": entries})


def handle_onto_status(kernel, rid, data, session, scopes) -> dict:
    """Ontology status: nucleus counts, REGISTRY packages, and sentinel files."""
    import json as _json
    import glob as _glob

    _kernel_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _project_dir = os.path.dirname(os.path.dirname(_kernel_dir))
    ont_dir      = os.path.join(_project_dir, "ontology")
    cfg_path     = os.path.join(_project_dir, "config", "ontology", "packs.json")
    _sent_dir    = os.path.join(kernel.base_dir, "central", "sentinels")

    nucleus = getattr(session, "nucleus", None)
    atom_count = link_count = alias_count = 0
    if nucleus:
        try:
            _t = nucleus.core.get_store_totals()
            atom_count, link_count, alias_count = _t["chunks"], _t["links"], _t["aliases"]
        except Exception:
            pass

    sent_names = []
    if os.path.isdir(_sent_dir):
        sent_names = sorted(os.path.basename(f) for f in _glob.glob(os.path.join(_sent_dir, "*.done")))

    # A pack's atom-load is complete when its phase-2 sentinel file exists
    # ({pack}_{hash}.done). Present-on-disk packs without one are still loading
    # (or not yet reached). Use the sentinel basenames already globbed above.
    def _pack_loaded(pname: str) -> bool:
        return any(s.startswith(pname + "_") and s.endswith(".done") for s in sent_names)

    # REGISTRY summary (every pack root, platform first)
    from lib.akasha.ontology.loader import registry_packages as _registry_packages
    registry_packages = []
    try:
        for pkg in _registry_packages():
                pname = pkg.get("name", "")
                pdir  = pkg.get("_dir") or ""
                fcount = sum(1 for fn in os.listdir(pdir) if fn.endswith(".ak")) if os.path.isdir(pdir) else 0
                registry_packages.append({
                    "name":       pname,
                    "autoload":   pkg.get("autoload", False),
                    "file_count": fcount,
                    "exists":     os.path.isdir(pdir),
                    "loaded":     _pack_loaded(pname),
                })
    except Exception:
        pass

    # ── Load-progress summary — one-glance "still loading / done" ──────────────
    # The boot load is a background daemon; a fresh seed re-extract re-imports
    # everything on the next boot (mtime-changed manifest hash). This tells the
    # operator whether that pass is still running, without having to eyeball the
    # sentinel list. Phase markers: _relations_*.done = all atoms+links loaded (the
    # definitive core-complete signal the portal/learn daemons gate on); curations
    # complete is a DB alias (ont:curation:loaded:*), CSL likewise.
    def _phase_done(prefix: str) -> bool:
        return any(s.startswith(prefix) and s.endswith(".done") for s in sent_names)

    def _alias_phase_done(pattern: str) -> bool:
        try:
            return bool(nucleus and nucleus.core.get_aliases_by_pattern(pattern))
        except Exception:
            return False

    # A pack that exists but ships 0 .ak files has nothing to load — it never gets a
    # sentinel, so counting it as "present" would pin the summary at IN PROGRESS
    # forever (the archaeology/biology/literature/medicine placeholders do this).
    _present = [p for p in registry_packages if p["exists"] and p.get("file_count", 0) > 0]
    _present_loaded = [p for p in _present if p["loaded"]]
    _pending = [p["name"] for p in _present if not p["loaded"]]
    _relations_done = _phase_done("_relations_")
    _has_curations = os.path.isdir(os.path.join(_project_dir, "curations"))
    _curations_done = (not _has_curations) or _alias_phase_done("ont:curation:loaded:")
    # "complete" = the CORE graph is loaded (all atoms + links = _relations_done, and no
    # present pack still pending). Curations and reconcile are OPTIONAL layers that do NOT
    # gate core completeness: curations are example ENRICHMENTS (not every tier runs them —
    # the seeds tier would otherwise pin complete=False forever), and reconcile only runs on
    # load_all tiers. Both are reported separately below. The portal/learn daemons already
    # gate on _relations_done, not on these, so this matches what the system treats as ready.
    _complete = bool(_relations_done and not _pending)
    load_summary = {
        "complete":        _complete,
        "in_progress":     not _complete,
        "packs_present":   len(_present),
        "packs_loaded":    len(_present_loaded),
        "packs_pending":   _pending,
        "relations_done":  _relations_done,     # atoms + all links loaded
        "canon_done":      _phase_done("_canon_"),
        "reconcile_done":  _phase_done("_reconcile_"),   # load_all tiers only; informational
        "curations_done":  _curations_done,              # optional enrichment; does not gate 'complete'
        # atoms count keeps climbing while loading — poll onto.status to watch it move.
        "atoms":           atom_count,
        "hint": (("ontology core load complete."
                  + ("" if _curations_done else " (curation enrichments still loading in the background.)"))
                 if _complete else
                 "ontology still loading — safe to exit; unfinished packs re-load on the "
                 "next boot (content-addressed, no data loss). Re-run onto.status to watch."),
    }

    enabled_packs = []
    try:
        with open(cfg_path) as f:
            enabled_packs = _json.load(f).get("enabled", [])
    except Exception:
        pass

    return _ok(rid, {
        "load": load_summary,
        "nucleus": {
            "atoms":   atom_count,
            "links":   link_count,
            "aliases": alias_count,
        },
        "registry": {
            "packages": registry_packages,
        },
        "enabled_packs": enabled_packs,
        "sentinels": {
            "count": len(sent_names),
            "files": sent_names,
        },
    })


def handle_onto_genesis_redo(kernel, rid, data, session, scopes) -> dict:
    """
    ⚠️  DANGEROUS ZONE ⚠️

    Remove the genesis anchor atoms so genesis_rite can be re-run.
    Ontology data, users, and atoms are NOT affected — only the
    two genesis markers (sys:genesis:anchor / sys:genesis:complete)
    are deleted.  The admin can then run genesis again to rename
    the Akasha instance or correct the initial setup.

    Required: confirm="GENESIS"
    Requires scope:sys:admin.
    """
    if "scope:sys:admin" not in scopes:
        return _err(rid, -32601, "onto.genesis.redo requires admin")

    confirm = (data.get("confirm") or "").strip()
    if confirm != "GENESIS":
        return _err(rid, -32602,
            "⚠️  DANGEROUS ZONE ⚠️\n"
            "onto.genesis.redo will delete the genesis anchor atoms, allowing\n"
            "a fresh genesis_rite to be performed.\n"
            "Ontology data, users, and all other atoms are NOT deleted.\n"
            "The system will be in an uninitialized state until genesis is re-run.\n\n"
            "To proceed: onto.genesis.redo confirm=\"GENESIS\"")

    nucleus = getattr(session, 'nucleus', None)
    if not nucleus:
        return _err(rid, -32001, "No nucleus available for this session")

    removed = []
    for alias in ("sys:genesis:complete", "sys:genesis:anchor"):
        key = nucleus.resolve_alias(alias)
        if key:
            nucleus.core.drop_chunk(key)
            removed.append(alias)

    return _ok(rid, {
        "status": "genesis_reset",
        "removed_anchors": removed,
        "message": "Genesis anchors removed. Run genesis_rite to re-initialize.",
    })


def handle_onto_scope_drop(kernel, rid, data, session, scopes) -> dict:
    """
    ⚠️  DANGEROUS ZONE ⚠️

    Delete all atoms that carry a specific access scope from the nucleus.
    Useful for purging a decommissioned user's contributed atoms, or
    removing all atoms donated under a particular scope.

    Required: confirm="DROP:<scope>"  (scope name embedded in confirm string)
    Requires role:librarian.
    Operates on nucleus only.  Personal cortex atoms are not affected.
    """
    if "role:librarian" not in scopes:
        return _err(rid, -32601, "onto.scope.drop requires role:librarian")

    target_scope = (data.get("scope") or "").strip()
    if not target_scope:
        return _err(rid, -32602, "onto.scope.drop requires 'scope'")

    confirm = (data.get("confirm") or "").strip()
    expected = f"DROP:{target_scope}"
    if confirm != expected:
        return _err(rid, -32602,
            f"⚠️  DANGEROUS ZONE ⚠️\n"
            f"onto.scope.drop will permanently delete ALL nucleus atoms\n"
            f"that carry the scope '{target_scope}'.\n"
            f"This CANNOT be undone.\n\n"
            f"To proceed: onto.scope.drop scope=\"{target_scope}\" confirm=\"{expected}\"")

    nucleus = getattr(session, 'nucleus', None)
    if not nucleus:
        return _err(rid, -32001, "No nucleus available for this session")

    keys = nucleus.core.get_keys_by_scope(target_scope)
    dropped = 0
    for key in keys:
        try:
            nucleus.core.drop_chunk(key)
            dropped += 1
        except Exception:
            pass

    return _ok(rid, {
        "status": "scope_dropped",
        "scope":   target_scope,
        "dropped": dropped,
        "message": f"Deleted {dropped} atoms carrying scope '{target_scope}'.",
    })
