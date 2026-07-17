"""
Presentation Concept Model.

Models an abstract presentation structure suitable for slide decks, research talks,
or any hierarchical content assembly. Decoupled from any specific source format.

Topology:
  PresentationRoot (concept="presentation", role="root")
    ├── Decks       — ordered slide sets (pres:deck links)
    ├── Frames      — individual slides / pages within a deck (pres:frame links)
    ├── Regions     — layout zones within a frame (pres:region links)
    └── Nodes       — atomic content references within a region or frame (pres:node links)

Namespace contract (two-namespace rule):
  - Content atoms  → set:pres:{concept_id}  AND  set:pres:{concept_id}:{subset}
  - Concept-word atom → set:concept:{concept_id}  (concept catalog scope)

Cross-concept patterns:
  - Survey + Aggregation → Presentation: attach measure atoms as frame nodes
  - FieldNote + Contexa  → Presentation: embed annotated field observations as deck frames
"""

import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Presentation")

INDEX_SET = "set:pres:index"
CONTEXT_KEY_ACTIVE = "active_presentation_root"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"


class PresentationConcept(BaseConcept):
    """Deck → Frame → Region → Node presentation model."""

    CONCEPT_PREFIX = "pres"
    CONCEPT_METHODS = {
        "new":        {"op": "op_new"},
        "open":       {"op": "op_open",
                       "coerce": lambda d: {
                           "pres_id": d.get("pres_id") or d.get("presentation_id", ""),
                       }},
        "ls":         {"op": "op_list_all"},
        "deck.add":   {"op": "op_add_deck"},
        "frame.add":  {"op": "op_add_frame"},
        "region.add": {"op": "op_add_region"},
        "node.add":   {"op": "op_add_node"},
        "list":       {"op": "op_list"},
        "rm":         {"op": "op_delete"},
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ── Private helpers ───────────────────────────────────────────────────────

    def _pres_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:pres:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _get_or_create_concept_word(self, word: str) -> str:
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        author_id, scopes = self._author_and_scopes()
        key = self.cortex.put_chunk(
            content=word,
            meta={
                "type":          "concept_word",
                "word":          word,
                "concept_model": "presentation",
                "created_at":    time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.set_alias(key, alias)
        return key

    def _register_to_package(self, key: str, subset_suffix: Optional[str], concept_word: str) -> None:
        """Dual-namespace: content atom → pres-scope (main + sub), concept-word → concept catalog."""
        author_id, _ = self._author_and_scopes()
        self.cortex.add_to_set(self._pres_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._pres_set(subset_suffix), key)
        cw_key = self._get_or_create_concept_word(concept_word)
        self.register_concept_node(cw_key)
        self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        """Guard: raises RuntimeError if atom_id is not accessible in current session."""
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    # ── Operators ─────────────────────────────────────────────────────────────

    def op_new(self, title: str, context_universes: Optional[List[str]] = None) -> Dict[str, Any]:
        """[pres.new] Create a PresentationRoot with a title and optional context universe list."""
        author_id, scopes = self._author_and_scopes()

        pres_id = self.cortex.put_chunk(
            content=f"[Presentation: {title}]",
            meta={
                "type":               "concept",
                "concept":            "presentation",
                "role":               "root",
                "title":              title,
                "context_universes":  context_universes or [],
                "created_at":         time.time(),
            },
            author=author_id,
            scopes=scopes,
        )

        self.concept_id = pres_id
        self.set_name   = f"set:concept:{self.concept_id}"

        self.ensure_concept_set()
        self._register_to_package(pres_id, subset_suffix=None, concept_word="presentation")

        for suffix in (None, "decks", "frames", "regions", "nodes"):
            self.cortex.create_set(self._pres_set(suffix))

        self.cortex.create_set(INDEX_SET)
        self.cortex.add_to_set(INDEX_SET, pres_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, pres_id)

        logger.info("[PresentationConcept] Created presentation '%s' (%s)", title, pres_id[:8])
        return {
            "status":           "created",
            "presentation_id":  pres_id,
            "title":            title,
            "context_universes": context_universes or [],
        }

    def op_open(self, pres_id: str) -> Dict[str, Any]:
        """[pres.open] Mount an existing presentation as the session's active presentation."""
        meta = self.cortex.get_meta(pres_id)
        if not meta or meta.get("concept") != "presentation":
            raise RuntimeError(f"Atom '{pres_id[:12]}' is not a presentation root.")

        self.concept_id = pres_id
        self.set_name   = f"set:concept:{self.concept_id}"

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, pres_id)

        return {
            "status":            "opened",
            "presentation_id":   pres_id,
            "title":             meta.get("title", ""),
            "context_universes": meta.get("context_universes", []),
        }

    def op_list_all(self) -> Dict[str, Any]:
        """[pres.ls] List all presentation roots accessible to this session."""
        members = self.cortex.get_collection_members(INDEX_SET)
        items: List[Dict[str, Any]] = []
        for key in members:
            if not self.cortex.check_access(key, self.allowed_scopes):
                continue
            meta = self.cortex.get_meta(key) or {}
            if meta.get("concept") != "presentation":
                continue
            items.append({
                "presentation_id":   key,
                "title":             meta.get("title", ""),
                "context_universes": meta.get("context_universes", []),
                "created_at":        meta.get("created_at", 0),
            })
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"presentations": items, "count": len(items)}

    def op_add_deck(self, title: str, order: float = 0.0) -> Dict[str, Any]:
        """[pres.deck.add] Add an ordered slide-deck section to the active presentation."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        deck_id = self.cortex.put_chunk(
            content=f"[Deck: {title}]",
            meta={
                "type":       "pres_deck",
                "title":      title,
                "order":      order,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(self._pres_set(), deck_id)
        self.cortex.add_to_set(self._pres_set("decks"), deck_id)
        self.cortex.put_link(self.concept_id, deck_id, "pres:deck", author=author_id)

        return {"status": "deck_added", "deck_id": deck_id}

    def op_add_frame(
        self,
        title: str,
        deck_id: Optional[str] = None,
        order: float = 0.0,
        ref_universe: Optional[str] = None,
        ref_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """[pres.frame.add] Add a frame (slide/page) to a deck, optionally referencing an external atom."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        if deck_id:
            self._require_access(deck_id, "Deck atom")

        # Validate ref_universe against presentation's context_universes if set
        if ref_universe:
            root_meta = self.cortex.get_meta(self.concept_id) or {}
            allowed_universes = root_meta.get("context_universes", [])
            if allowed_universes and ref_universe not in allowed_universes:
                raise RuntimeError(
                    f"ref_universe '{ref_universe}' not in presentation's context_universes: {allowed_universes}"
                )

        frame_id = self.cortex.put_chunk(
            content=f"[Frame: {title}]",
            meta={
                "type":          "pres_frame",
                "title":         title,
                "order":         order,
                "ref_universe":  ref_universe,
                "ref_id":        ref_id,
                "created_at":    time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(self._pres_set(), frame_id)
        self.cortex.add_to_set(self._pres_set("frames"), frame_id)

        parent = deck_id if deck_id else self.concept_id
        self.cortex.put_link(parent, frame_id, "pres:frame", author=author_id)

        return {"status": "frame_added", "frame_id": frame_id}

    def op_add_region(self, frame_id: str, label: str, order: float = 0.0) -> Dict[str, Any]:
        """[pres.region.add] Add a layout region within a frame."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        self._require_access(frame_id, "Frame atom")

        region_id = self.cortex.put_chunk(
            content=f"[Region: {label}]",
            meta={
                "type":       "pres_region",
                "label":      label,
                "order":      order,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(self._pres_set(), region_id)
        self.cortex.add_to_set(self._pres_set("regions"), region_id)
        self.cortex.put_link(frame_id, region_id, "pres:region", author=author_id)

        return {"status": "region_added", "region_id": region_id}

    def op_add_node(
        self,
        parent_id: str,
        ref_universe: str,
        ref_id: str,
        role: str = "item",
        style: Optional[str] = None,
    ) -> Dict[str, Any]:
        """[pres.node.add] Attach a content reference node to a region or frame."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        self._require_access(parent_id, "Parent atom")

        node_id = self.cortex.put_chunk(
            content=f"[Node: {ref_universe}/{ref_id[:8]}]",
            meta={
                "type":         "pres_node",
                "ref_universe": ref_universe,
                "ref_id":       ref_id,
                "role":         role,
                "style":        style,
                "created_at":   time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(self._pres_set(), node_id)
        self.cortex.add_to_set(self._pres_set("nodes"), node_id)
        self.cortex.put_link(parent_id, node_id, "pres:node", author=author_id)

        return {"status": "node_added", "node_id": node_id}

    def op_list(self) -> Dict[str, Any]:
        """[pres.list] Return the structural inventory of the active presentation."""
        self._require_concept()
        allowed = self.allowed_scopes

        def safe_members(suffix: str) -> List[str]:
            return [
                k for k in self.cortex.get_collection_members(self._pres_set(suffix))
                if self.cortex.check_access(k, allowed)
            ]

        return {
            "presentation_id": self.concept_id,
            "decks":           safe_members("decks"),
            "frames":          safe_members("frames"),
            "regions":         safe_members("regions"),
            "nodes":           safe_members("nodes"),
        }

    def op_delete(self) -> Dict[str, Any]:
        """[pres.rm] Delete the active presentation root and clear session context."""
        self._require_concept()
        pres_id = self.concept_id
        self.cortex.drop_chunk(pres_id, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "presentation_id": pres_id}
