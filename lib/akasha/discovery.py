"""
Atom discovery — the shared filter-search core.

Factored out of kernel `_handle_explore` so the `explore` command AND the
`thesaurus.explore` concept operator call ONE implementation (no double code).

Dependency-injected: it takes the engine(s), the caller's group engines, and the
active scopes explicitly. It imports nothing kernel-specific, so a concept model
(which only holds a session + cortex) can call it exactly as the kernel does.
"""

from typing import Any, Dict, List, Optional

from lib.akasha.consciousness import CosmosMapper


def collect_candidates(ctx, nucleus, group_engines, *, ns: str = "", set_filt: str = "",
                       atom_type: str = "", pat: str = "",
                       limit: int = 50) -> Dict[str, Optional[str]]:
    """Collect candidate `{key: alias_or_None}` by ANDing the given filters.

    Matches are merged from the local cortex, the nucleus, and any shared group
    engines. This is pure collection — no scope gating; the caller filters by
    access. Mirrors the candidate-collection half of the old `_handle_explore`.
    """
    candidate_keys: Optional[Dict[str, Optional[str]]] = None

    # Pattern / namespace → alias search
    if pat or ns:
        pattern = pat if pat else f"{ns}:%"
        if "%" not in pattern and "_" not in pattern:
            pattern = f"{pattern}%"

        rows = ctx.get_aliases_by_pattern(pattern)
        seen_k = {r["key"] for r in rows}
        if nucleus:
            for r in nucleus.core.get_aliases_by_pattern(pattern) or []:
                if r["key"] not in seen_k:
                    rows.append(r)
                    seen_k.add(r["key"])
        for _gid, _ge in group_engines:
            for r in (_ge.core.get_aliases_by_pattern(pattern) or []):
                if r["key"] not in seen_k:
                    rows.append(r)
                    seen_k.add(r["key"])

        pat_keys: Dict[str, Optional[str]] = {}
        for r in rows:
            if r["key"] not in pat_keys:
                pat_keys[r["key"]] = r.get("alias")

        candidate_keys = pat_keys if candidate_keys is None else {
            k: v for k, v in pat_keys.items() if k in candidate_keys
        }

    # Set membership filter
    if set_filt:
        normalized = set_filt if set_filt.startswith("set:") else f"set:{set_filt}"
        set_members = set(ctx.get_collection_members(normalized))
        for _gid, _ge in group_engines:
            set_members |= set(_ge.core.get_collection_members(normalized))

        if candidate_keys is None:
            candidate_keys = {k: None for k in set_members}
        else:
            candidate_keys = {k: v for k, v in candidate_keys.items() if k in set_members}

    if candidate_keys is None:
        candidate_keys = {}

    # Meta-type filter (checked against raw chunk meta)
    if atom_type:
        import json as _json
        filtered: Dict[str, Optional[str]] = {}
        for k, alias in list(candidate_keys.items())[: limit * 4]:
            raw = None
            try:
                raw = ctx.core.get_chunk_raw(k)
            except Exception:
                pass
            if not raw and nucleus:
                try:
                    raw = nucleus.core.get_chunk_raw(k)
                except Exception:
                    pass
            if not raw:
                for _gid, _ge in group_engines:
                    try:
                        raw = _ge.core.get_chunk_raw(k)
                    except Exception:
                        raw = None
                    if raw:
                        break
            if raw:
                try:
                    meta = _json.loads(raw.get("meta", "{}") or "{}")
                except Exception:
                    meta = {}
                if meta.get("type") == atom_type or meta.get("rec_type") == atom_type:
                    filtered[k] = alias
        candidate_keys = filtered

    return candidate_keys


def discover_atoms(ctx, nucleus, group_engines, scopes, *, ns: str = "", set_filt: str = "",
                   atom_type: str = "", pat: str = "", limit: int = 50) -> List[Dict[str, Any]]:
    """Filter-search for atoms; return scope-gated rows `[{key, alias, preview, color}]`.

    Shared by the `explore` command and `thesaurus.explore`. Fail-closed: an atom
    denied by `check_access` is only surfaced if a shared group engine grants it.
    """
    candidate_keys = collect_candidates(
        ctx, nucleus, group_engines,
        ns=ns, set_filt=set_filt, atom_type=atom_type, pat=pat, limit=limit)

    results: List[Dict[str, Any]] = []
    for k, alias in list(candidate_keys.items())[:limit]:
        src = ctx
        if not ctx.check_access(k, scopes):
            src = next((ge for _gid, ge in group_engines if ge.check_access(k)), None)
            if src is None:
                continue
        if alias is None:
            als = src.get_aliases_by_key(k)
            alias = als[0] if als else None
        content = src.get_chunk(k) or ""
        results.append({
            "key":     k,
            "alias":   alias,
            "preview": content[:60],
            "color":   CosmosMapper.get_aura_color(ctx, k),
        })
    return results
