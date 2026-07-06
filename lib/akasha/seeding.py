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
                       current code-generation approach in scripts/generate_seeds.py
  locale-aware seeds — load seeds whose locale matches the session first; fall back
                       to "en" seeds when no locale match exists
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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

        if doc_type in ("note", "loom:note"):
            return self._plant_note(session, concept_id, seed_meta, atoms, adj, doc_type)
        if doc_type == "fieldnote":
            return self._plant_fieldnote(session, concept_id, seed_meta, atoms, adj, atom_meta)
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Per-type planters
    # ─────────────────────────────────────────────────────────────────────────

    def _plant_note(self, session, concept_id, seed_meta, atoms, adj, doc_type) -> Optional[str]:
        from .concepts.note import NoteConcept
        title     = seed_meta.get("title") or atoms.get(concept_id, "Untitled")
        namespace = "loom" if doc_type == "loom:note" else None
        concept   = NoteConcept(session, namespace=namespace)
        concept.op_new(title=title)
        for text in self._walk_chain(concept_id, atoms, adj):
            if text:
                concept.op_add_chunk(text=text)
        return title

    def _plant_fieldnote(self, session, concept_id, seed_meta, atoms, adj, atom_meta) -> Optional[str]:
        from .concepts.fieldnote import FieldNoteConcept
        title   = seed_meta.get("title") or atoms.get(concept_id, "Sample FieldNote")
        project = seed_meta.get("project")
        region  = seed_meta.get("region")
        season  = seed_meta.get("season")
        concept = FieldNoteConcept(session)
        concept.op_new(title=title, project=project, region=region, season=season)
        for atom_id, text in self._walk_chain_items(concept_id, atoms, adj):
            if text:
                am   = atom_meta.get(atom_id, {})
                concept.op_add(
                    text       = text,
                    role       = am.get("role", "observation"),
                    confidence = am.get("confidence"),
                    period     = am.get("period"),
                )
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
