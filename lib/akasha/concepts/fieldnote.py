"""
FieldNote Concept Model.

[OPERAND-FIRST DESIGN]
Represents a structured field observation record — a lightweight, flat sequence
of observations anchored to a research context (project, region, season).

Unlike the Note concept (which models a hierarchical document), FieldNote is
deliberately flat: a root atom holds context metadata, and all observations are
appended to a single chronological timeline (sys:top → sys:next → sys:bottom).

Topology:
  - Root atom (concept: "fieldnote", role: "root") carries context metadata.
  - Observation atoms are linked via sys:contains and sequenced by the timeline.
  - A global index set (set:fieldnote:index) holds all root IDs for fast listing.

Namespace contract (two-namespace rule):
  - Content atoms → set:fieldnote:{concept_id}   (fieldnote-model scope)
  - All atoms registered in concept catalog → set:concept:{concept_id}
"""

import time
import logging
from typing import List, Dict, Any, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.FieldNote")

CONTEXT_KEY_ACTIVE = "active_fieldnote_root"
INDEX_SET = "set:fieldnote:index"


class FieldNoteConcept(BaseConcept):
    """Flat, context-tagged field observation record."""

    CONCEPT_PREFIX = "fieldnote"
    CONCEPT_METHODS = {
        "new": {
            "op": "op_new",
            "coerce": lambda d: {
                "title":   d.get("title") or d.get("name", ""),
                "project": d.get("project") or None,
                "region":  d.get("region")  or None,
                "season":  d.get("season")  or None,
            },
        },
        "ls":   {"op": "op_list"},
        "open": {"op": "op_open"},
        "add": {
            "op": "op_add",
            "coerce": lambda d: {"text": d.get("text") or d.get("observation", "")},
        },
        "read": {"op": "op_read"},
        "rm":   {"op": "op_delete"},
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None, namespace: Optional[str] = None):
        super().__init__(session, concept_id, namespace=namespace)
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(self._ctx_key(CONTEXT_KEY_ACTIVE))
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ── Private helpers ───────────────────────────────────────────────────────

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _content_set(self) -> str:
        return f"set:fieldnote:{self.concept_id}"

    def _append_to_timeline(self, node_id: str, author_id: str):
        tail_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")
        if not tail_links:
            self.cortex.put_link(self.concept_id, node_id, "sys:top", author=author_id)
        else:
            last_node_id = tail_links[0][0]
            self.cortex.put_link(last_node_id, node_id, "sys:next",     author=author_id)
            self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)
            self.cortex.remove_link(self.concept_id, last_node_id, "sys:bottom")
        self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)

    # ── Operators (public API) ────────────────────────────────────────────────

    def op_new(self, title: str, project: Optional[str] = None,
               region: Optional[str] = None, season: Optional[str] = None) -> Dict[str, Any]:
        """[fieldnote.new] Create a new FieldNote record."""
        author_id, scopes = self._author_and_scopes()

        root_meta = {
            "type":       "concept",
            "concept":    "fieldnote",
            "role":       "root",
            "title":      title,
            "project":    project,
            "region":     region,
            "season":     season,
            "created_at": time.time(),
        }
        root_id = self.cortex.put_chunk(
            content=f"[ FieldNote: {title} ]",
            meta=root_meta,
            author=author_id,
            scopes=scopes,
        )

        self.concept_id = root_id
        self.set_name   = f"set:concept:{self.concept_id}"

        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._content_set())
        self.register_concept_node(root_id)

        # Global index for fast listing across all fieldnotes
        self.cortex.add_to_set(INDEX_SET, root_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(self._ctx_key(CONTEXT_KEY_ACTIVE), root_id)

        logger.info(f"[FieldNoteConcept] Created: '{title}' ({root_id[:8]})")
        return {
            "status":       "created",
            "fieldnote_id": root_id,
            "title":        title,
            "project":      project,
            "region":       region,
            "season":       season,
        }

    def op_open(self, fieldnote_id: str) -> Dict[str, Any]:
        """[fieldnote.open] Mount an existing FieldNote as the session's active record."""
        meta = self.cortex.get_meta(fieldnote_id)
        if not meta or meta.get("concept") != "fieldnote":
            raise RuntimeError(f"Atom '{fieldnote_id[:12]}' is not a fieldnote root.")

        self.concept_id = fieldnote_id
        self.set_name   = f"set:concept:{self.concept_id}"

        if hasattr(self.session, "set_context"):
            self.session.set_context(self._ctx_key(CONTEXT_KEY_ACTIVE), fieldnote_id)

        return {
            "status":       "opened",
            "fieldnote_id": fieldnote_id,
            "title":        meta.get("title", ""),
            "project":      meta.get("project"),
            "region":       meta.get("region"),
            "season":       meta.get("season"),
        }

    def op_list(self) -> Dict[str, Any]:
        """[fieldnote.ls] List all accessible FieldNote records."""
        members = self.cortex.get_collection_members(INDEX_SET)
        items = []

        for key in members:
            if not self.cortex.check_access(key, self.allowed_scopes):
                continue

            meta = self.cortex.get_meta(key)
            if meta.get("concept") != "fieldnote":
                continue

            items.append({
                "fieldnote_id": key,
                "title":        meta.get("title", ""),
                "project":      meta.get("project"),
                "region":       meta.get("region"),
                "season":       meta.get("season"),
                "created_at":   meta.get("created_at", 0),
            })

        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"fieldnotes": items, "count": len(items)}

    def op_add(self, text: str, role: str = "observation",
               period: Optional[str] = None,
               confidence: Optional[float] = None) -> Dict[str, Any]:
        """[fieldnote.add] Append an observation to the active FieldNote."""
        self._require_concept()
        if not text:
            raise ValueError("Observation text is required.")

        author_id, scopes = self._author_and_scopes()

        meta: Dict[str, Any] = {
            "type":       "observation",
            "role":       role or "observation",
            "created_at": time.time(),
        }
        if period is not None:
            meta["period"] = period
        if confidence is not None:
            meta["confidence"] = float(confidence)

        obs_id = self.cortex.put_chunk(
            content=text,
            meta=meta,
            author=author_id,
            scopes=scopes,
        )

        self.cortex.add_to_set(self._content_set(), obs_id)
        self.register_concept_node(obs_id)
        self.cortex.put_link(self.concept_id, obs_id, "sys:contains", author=author_id)
        self._append_to_timeline(obs_id, author_id)

        return {"status": "added", "observation_id": obs_id, "preview": text[:60]}

    def op_read(self) -> Dict[str, Any]:
        """[fieldnote.read] Read all observations in chronological order."""
        self._require_concept()

        allowed  = self.allowed_scopes
        sequence = []

        top_links = self.cortex.get_adjacent_links(self.concept_id, "sys:top")
        if not top_links:
            return {"observations": [], "count": 0}

        seen = set()
        current_id = top_links[0][0]
        while current_id and current_id not in seen:
            seen.add(current_id)
            if self.cortex.check_access(current_id, allowed):
                content = self.cortex.get_chunk(current_id)
                meta    = self.cortex.get_meta(current_id)
                sequence.append({
                    "id":         current_id,
                    "content":    content,
                    "role":       meta.get("role", "observation"),
                    "period":     meta.get("period"),
                    "confidence": meta.get("confidence"),
                    "created_at": meta.get("created_at"),
                })
            next_links = self.cortex.get_adjacent_links(current_id, "sys:next")
            current_id = next_links[0][0] if next_links else None

        return {"observations": sequence, "count": len(sequence)}

    def op_delete(self) -> Dict[str, Any]:
        """[fieldnote.rm] Delete the active FieldNote and clear session context."""
        self._require_concept()
        fieldnote_id = self.concept_id
        self.cortex.drop_chunk(fieldnote_id, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(self._ctx_key(CONTEXT_KEY_ACTIVE), None)
        return {"status": "deleted", "fieldnote_id": fieldnote_id}
