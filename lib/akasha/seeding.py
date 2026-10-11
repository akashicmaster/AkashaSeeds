"""
SeedManager — trusted first-login document seeding.

Seeds are .akasha capsule files stored in seeds/{app_name}/ at the project root.
Each file has a "seed" block inside the metadata section that controls seeding behaviour.

Unlike the regular import flow (KnowledgeCapsule.decapsulate), SeedManager.plant()
re-creates documents via the concept API.  Atoms are therefore immediately owned by
the current user with status="verified" — no pending isolation scope.

Seed file metadata extension:
    "seed": {
        "kind":     "sample",    # "sample" | "template" (see below)
        "title":    str,         # human-readable title (used directly by plant())
        "order":    int,         # sort order within the app
        "category": str,         # grouping tag (e.g. "archaeology", "general")
        "project":  str | null,  # fieldnote-specific context
        "region":   str | null,
        "season":   str | null,
        "locale":   str          # ISO 639-1 language code, default "en"
    }

Seed kinds:
    "sample"   — loaded automatically on first login; one-time, disposable.
                 Users may freely edit or delete these documents.
    "template" — NOT auto-loaded.  Planned future feature: a sys.template.*
                 API will let users instantiate templates on demand.

atom_meta extension (for preserving per-atom metadata not carried by content):
    "atom_meta": { "<atom_id>": {"role": str, "confidence": float, "period": str} }

Planned extensions:
  template system    — sys.template.ls / sys.template.use RPC (not yet implemented)
  admin export tool  — sys.seed.export RPC: let app developers export any document
                       as a seed file directly from within the app, replacing the
                       current code-generation approach in app/scripts/generate_seeds.py
  locale-aware seeds — load seeds whose locale matches the session first; fall back
                       to "en" seeds when no locale match exists
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import logging
import os

# ── the seed recipes: APPLICATION data (config/seed/*.json), read here, dispatched through the ops ──
# The planter used to import the note and fieldnote Concept Models and call their methods (group 4,
# 4.4). A recipe names the ops instead; the platform reads it and dispatches through the routers the
# manifests declared, so it names no Concept Model and imports none.
_RECIPES: Dict[str, Dict[str, Any]] = {}


def _recipe_dir() -> str:
    from lib.akasha.api import reserved as _reserved
    return _reserved.root("seed_recipes")


def _recipe_for(doc_type: str) -> Optional[Dict[str, Any]]:
    if not _RECIPES:
        d = _recipe_dir()
        for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if not name.endswith(".json"):
                continue
            try:
                with open(os.path.join(d, name), encoding="utf-8") as f:
                    rec = json.load(f)
            except (OSError, ValueError):
                continue
            for dt in rec.get("doc_types") or []:
                _RECIPES.setdefault(str(dt), rec)
    return _RECIPES.get(str(doc_type or "note"))


def _fill(template: Any, ctx: Dict[str, Any]) -> Any:
    """`{field}` / `{meta.key}` / `{a|b|literal}` → the first non-empty value; the last alternative
    is a literal default when it names no field. None when nothing resolves (the arg is dropped)."""
    if not (isinstance(template, str) and template.startswith("{") and template.endswith("}")):
        return template
    alts = template[1:-1].split("|")
    for i, alt in enumerate(alts):
        cur: Any = ctx
        for part in alt.split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur not in (None, ""):
            return cur
        if i == len(alts) - 1 and i > 0 and "." not in alt and alt not in ctx:
            return alt
    return None


def _dispatch(session, step: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    op = str(step.get("op") or "")
    if not op:
        return False
    args = {k: v for k, v in ((k, _fill(t, ctx)) for k, t in (step.get("args") or {}).items())
            if v is not None}
    from lib.akasha import api as _api
    for router in _api.routers() or _api.discover_routers():
        try:
            r = router.dispatch_if_handled(op, session, args, "seed")
        except Exception as exc:
            logging.getLogger("Akasha.Seed").info("[seed] %s failed: %s", op, exc)
            return False
        if r is not None:
            return isinstance(r, dict) and "result" in r
    logging.getLogger("Akasha.Seed").info("[seed] %s skipped reason=no_router", op)
    return False


class SeedManager:
    def __init__(self, seeds_root: str | Path):
        self.seeds_root = Path(seeds_root)

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def seed_app(self, session, app_name: str) -> Dict[str, Any]:
        """
        Load all kind='sample' seeds for app_name into the session's cortex.
        Individual seed failures are non-fatal — the remaining seeds still load.
        Returns {"already_done": False, "seeds_loaded": int, "titles": [str]}.
        """
        seed_dir = self.seeds_root / app_name
        if not seed_dir.exists():
            return {"already_done": False, "seeds_loaded": 0, "titles": []}

        files  = sorted(seed_dir.glob("*.akasha"))
        titles: List[str] = []
        for path in files:
            try:
                with open(path, encoding="utf-8") as fp:
                    capsule = json.load(fp)
                seed_meta = capsule.get("metadata", {}).get("seed", {})
                if seed_meta.get("kind", "sample") != "sample":
                    continue  # templates are not auto-loaded
                title = self.plant(session, capsule)
                if title:
                    titles.append(title)
            except Exception:
                pass  # log or surface errors in a future debug mode

        return {"already_done": False, "seeds_loaded": len(titles), "titles": titles}

    def plant(self, session, capsule: Dict[str, Any]) -> Optional[str]:
        """
        Re-create one document from a capsule dict using the concept API.
        Returns the document title on success, None on failure.
        """
        meta       = capsule.get("metadata", {})
        doc_type   = meta.get("doc_type", "note")
        concept_id = meta.get("concept_id", "")
        seed_meta  = meta.get("seed", {})
        atoms      = capsule.get("atoms", {})
        links      = capsule.get("links", [])
        atom_meta  = capsule.get("atom_meta", {})

        # Build outgoing adjacency map: src → {rel → [dst, ...]}
        adj: Dict[str, Dict[str, List[str]]] = {}
        for lk in links:
            src = lk.get("src", "")
            rel = lk.get("rel", "")
            dst = lk.get("dst", "")
            adj.setdefault(src, {}).setdefault(rel, []).append(dst)

        recipe = _recipe_for(doc_type)
        if recipe is None:
            logging.getLogger("Akasha.Seed").info(
                "[seed] skipped doc_type=%s reason=no_recipe (config/seed/*.json)", doc_type)
            return None
        title = (seed_meta.get("title") or atoms.get(concept_id)
                 or recipe.get("default_title") or "Untitled")
        ctx = dict(seed_meta)
        ctx["title"] = title
        if not _dispatch(session, recipe.get("create") or {}, ctx):
            return None
        item = recipe.get("item") or {}
        if item.get("op"):
            for atom_id, text in self._walk_chain_items(concept_id, atoms, adj):
                if text:
                    ictx = dict(ctx)
                    ictx["text"] = text
                    ictx["meta"] = atom_meta.get(atom_id, {}) or {}
                    _dispatch(session, item, ictx)
        return title

    # ─────────────────────────────────────────────────────────────────────────
    # Chain traversal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _walk_chain(self, root_id: str, atoms: dict, adj: dict) -> List[str]:
        return [text for _, text in self._walk_chain_items(root_id, atoms, adj)]

    def _walk_chain_items(self, root_id: str, atoms: dict, adj: dict) -> List[Tuple[str, str]]:
        """Follow sys:top → sys:next chain; yield (atom_id, content) in order."""
        tops    = adj.get(root_id, {}).get("sys:top", [])
        current = tops[0] if tops else None
        seen: set = set()
        result: List[Tuple[str, str]] = []
        while current and current not in seen and current in atoms:
            seen.add(current)
            result.append((current, atoms[current]))
            nexts   = adj.get(current, {}).get("sys:next", [])
            current = nexts[0] if nexts else None
        return result


def handle_onboarding_seed(kernel, rid, data, session) -> dict:
    """[sys.onboarding.seed] Load the sample seeds for `app` on the user's first login to it."""
    from lib.akasha.api.rpc import ok as _ok, err as _err
    app_name = (data or {}).get("app", "").strip()
    if not app_name:
        return _err(rid, -32602, "sys.onboarding.seed requires 'app'")
    if app_name in kernel.iam.get_onboarded_apps(session.client_id):
        return _ok(rid, {"already_done": True, "seeds_loaded": 0, "titles": []})
    from lib.akasha.api import reserved as _reserved
    seeds_root = Path(_reserved.root("seeds"))
    result = SeedManager(seeds_root).seed_app(session, app_name)
    kernel.iam.mark_onboarded(session.client_id, app_name)
    return _ok(rid, result)
