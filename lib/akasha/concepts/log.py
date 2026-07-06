"""
LogConcept — records the process of exploration.

Each Log has a root atom and a sequential timeline of Checkpoint atoms.
Unlike NoteConcept (which records written content), LogConcept records the
act of traversal itself: which atom was the focus, under what scope
conditions, and when.

Dispatch chain:
    Shell: log.new / log.checkpoint / log.replay / log.annotate / log.rm
      ↓
    kernel.dispatch("log.*", data)
      ↓
    LogConcept(session).op_*(**params)
      ↓
    cortex.put_chunk / put_link
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Log")

_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"


class LogConcept(BaseConcept):
    """
    Exploration Log Model.
    Records focal atoms, scope state, and traversal notes as a sequential timeline.
    Inherits BaseConcept directly — does NOT inherit NoteConcept.
    """

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)

        # Mount the active log from session if no explicit concept_id given
        if not self.concept_id:
            active_root = getattr(self.session, "get_context", lambda k: None)("active_log_root")
            if active_root:
                self.concept_id = active_root
                self.set_name = f"set:concept:{self.concept_id}"

    def _get_set_name(self, suffix: str = "") -> str:
        return f"set:log:{self.concept_id}:{suffix}" if suffix else f"set:log:{self.concept_id}"

    def _get_or_create_concept_word(self, word: str) -> str:
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing

        author_id = getattr(self.session, 'client_id', 'system')
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        meta = {
            "type": "concept_word",
            "word": word,
            "concept_model": "log",
            "created_at": time.time(),
        }
        key = self.cortex.put_chunk(content=word, meta=meta, author=author_id, scopes=scopes)
        self.cortex.set_alias(key, alias)
        return key

    def _register_to_package(self, key: str, subset_suffix: Optional[str] = None,
                             concept_word: Optional[str] = None):
        author_id = getattr(self.session, 'client_id', 'system')
        self.cortex.add_to_set(self._get_set_name(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._get_set_name(subset_suffix), key)

        if concept_word:
            cw_key = self._get_or_create_concept_word(concept_word)
            self.register_concept_node(cw_key)
            self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    def _append_to_timeline(self, node_id: str, author_id: str):
        """Appends a node to the Log's sequential checkpoint timeline."""
        tail_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")

        if not tail_links:
            self.cortex.put_link(self.concept_id, node_id, "sys:top", author=author_id)
        else:
            last_node_id = tail_links[0][0]
            self.cortex.put_link(last_node_id, node_id, "sys:next", author=author_id)
            self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)
            self.cortex.remove_link(self.concept_id, last_node_id, "sys:bottom")

        self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)

    def _get_checkpoints_ordered(self) -> List[str]:
        """Returns checkpoint atom keys in timeline order (top → bottom)."""
        top_links = self.cortex.get_adjacent_links(self.concept_id, "sys:top")
        if not top_links:
            return []

        ordered = []
        current = top_links[0][0]
        visited: set = set()
        while current and current not in visited:
            ordered.append(current)
            visited.add(current)
            nxt = self.cortex.get_adjacent_links(current, "sys:next")
            current = nxt[0][0] if nxt else None
        return ordered

    # =========================================================================
    # Operators
    # =========================================================================

    def op_ls(self) -> Dict[str, Any]:
        """[log.ls] List all logs for the current user."""
        author_id = getattr(self.session, 'client_id', 'system')
        rows = self.cortex.fetch_by_meta_field("concept", "log", author=author_id)
        logs = []
        for row in rows:
            try:
                meta = json.loads(row.get("meta") or "{}")
            except Exception:
                meta = {}
            if meta.get("role") == "log":
                active = self.session.get_context("active_log_root") == row["key"]
                logs.append({
                    "log_id":     row["key"],
                    "name":       meta.get("name", ""),
                    "created_at": meta.get("created_at", 0),
                    "active":     active,
                })
        logs.sort(key=lambda x: x["created_at"], reverse=True)
        return {"logs": logs, "count": len(logs)}

    def op_new(self, name: str) -> Dict[str, Any]:
        """[log.new] Create a new Log and set it as the active log."""
        author_id = getattr(self.session, 'client_id', 'system')
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

        root_meta = {
            "type":       "concept",
            "concept":    "log",
            "role":       "log",
            "name":       name,
            "created_at": time.time(),
        }
        root_id = self.cortex.put_chunk(
            content=f"[ Log: {name} ]",
            meta=root_meta,
            author=author_id,
            scopes=user_scopes,
        )

        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"

        self.cortex.create_set(self._get_set_name())
        self.cortex.create_set(self._get_set_name("checkpoints"))
        self._register_to_package(root_id, concept_word="log")

        if hasattr(self.session, 'set_context'):
            self.session.set_context("active_log_root", root_id)
            self.session.set_context("active_log_container", root_id)

        logger.info(f"[LogConcept] New log: '{name}' ({root_id[:8]})")
        return {"log_id": root_id, "name": name, "status": "created"}

    def op_checkpoint(self, note: Optional[str] = None) -> Dict[str, Any]:
        """[log.checkpoint] Record the current session state as a checkpoint."""
        self._require_concept()

        author_id = getattr(self.session, 'client_id', 'system')
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

        focal_key = self.session.get_context("focus") or getattr(self.session, 'last_written_id', None) or ""
        focal_alias = None
        if focal_key:
            aliases = self.cortex.get_aliases_by_key(focal_key)
            if aliases:
                focal_alias = aliases[0]

        # Read scope state — whiteboard-local takes priority when a board is active
        active_wb = self.session.get_context("active_whiteboard")
        if active_wb:
            active_axis  = self.session.get_context(f"wb:{active_wb}:scope_axis")
            active_scope = self.session.get_context(f"wb:{active_wb}:scope_scope")
            active_time  = self.session.get_context(f"wb:{active_wb}:scope_time")
        else:
            active_axis  = self.session.get_context("active_axis")
            active_scope = self.session.get_context("active_scope")
            active_time  = self.session.get_context("active_time")

        cp_meta = {
            "type":         "log_checkpoint",
            "role":         "checkpoint",
            "focal_key":    focal_key,
            "focal_alias":  focal_alias,
            "active_axis":  active_axis,
            "active_scope": active_scope,
            "active_time":  active_time,
            "whiteboard":   active_wb,
            "note":         note,
            "created_at":   time.time(),
        }
        cp_content = (
            f"[checkpoint] focal={focal_key[:8] if focal_key else 'none'} "
            f"axis={active_axis} scope={active_scope}"
        )
        cp_id = self.cortex.put_chunk(
            content=cp_content,
            meta=cp_meta,
            author=author_id,
            scopes=user_scopes,
        )

        self._register_to_package(cp_id, subset_suffix="checkpoints", concept_word="checkpoint")
        self._append_to_timeline(cp_id, author_id)
        self.session.set_context("active_log_container", cp_id)

        return {
            "checkpoint_id": cp_id,
            "focal":         focal_key,
            "axis":          active_axis,
            "scope":         active_scope,
            "time":          active_time,
            "note":          note,
            "status":        "recorded",
        }

    def op_annotate(self, text: str) -> Dict[str, Any]:
        """[log.annotate] Add a text annotation to the most recent checkpoint."""
        self._require_concept()

        author_id = getattr(self.session, 'client_id', 'system')
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

        bottom_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")
        if not bottom_links:
            raise RuntimeError("No checkpoints to annotate. Use log.checkpoint first.")
        last_cp_id = bottom_links[0][0]

        ann_meta = {
            "type":          "log_annotation",
            "role":          "annotation",
            "checkpoint_id": last_cp_id,
            "created_at":    time.time(),
        }
        ann_id = self.cortex.put_chunk(
            content=text,
            meta=ann_meta,
            author=author_id,
            scopes=user_scopes,
        )
        self._register_to_package(ann_id)
        self.cortex.put_link(last_cp_id, ann_id, "sys:has_annotation", author=author_id)

        return {
            "annotation_id": ann_id,
            "checkpoint_id": last_cp_id,
            "status":        "annotated",
        }

    def op_replay(self) -> Dict[str, Any]:
        """[log.replay] Restore each checkpoint's session state sequentially."""
        self._require_concept()

        checkpoints = self._get_checkpoints_ordered()
        result_list = []

        active_wb = self.session.get_context("active_whiteboard")

        for i, cp_id in enumerate(checkpoints):
            raw = self.cortex.core.get_chunk_raw(cp_id)
            if not raw:
                continue
            meta = json.loads(raw["meta"]) if raw.get("meta") else {}

            focal = meta.get("focal_key", "")
            alias = meta.get("focal_alias")
            axis  = meta.get("active_axis")
            scope = meta.get("active_scope")
            t     = meta.get("active_time")
            note  = meta.get("note")

            if focal:
                self.session.set_context("focus", focal)

            if active_wb:
                if axis  is not None: self.session.set_context(f"wb:{active_wb}:scope_axis",  axis)
                if scope is not None: self.session.set_context(f"wb:{active_wb}:scope_scope", scope)
                if t     is not None: self.session.set_context(f"wb:{active_wb}:scope_time",  t)
            else:
                if axis  is not None: self.session.set_context("active_axis",  axis)
                if scope is not None: self.session.set_context("active_scope", scope)
                if t     is not None: self.session.set_context("active_time",  t)

            result_list.append({
                "index":    i,
                "focal":    focal,
                "alias":    alias,
                "axis":     axis,
                "scope":    scope,
                "note":     note,
                "restored": True,
            })

        return {
            "checkpoints": result_list,
            "count":       len(result_list),
            "status":      "replayed",
        }

    def op_read(self) -> Dict[str, Any]:
        """[log.read] Read the Log as a sequential list of checkpoints."""
        self._require_concept()

        root_raw = self.cortex.core.get_chunk_raw(self.concept_id)
        root_meta = json.loads(root_raw["meta"]) if root_raw and root_raw.get("meta") else {}

        checkpoints = self._get_checkpoints_ordered()
        cp_list = []

        for cp_id in checkpoints:
            raw = self.cortex.core.get_chunk_raw(cp_id)
            if not raw:
                continue
            meta = json.loads(raw["meta"]) if raw.get("meta") else {}

            ann_links = self.cortex.get_adjacent_links(cp_id, "sys:has_annotation")
            annotations = []
            for ann_id, _ in ann_links:
                ann_raw = self.cortex.core.get_chunk_raw(ann_id)
                if ann_raw:
                    annotations.append({
                        "id":   ann_id,
                        "text": ann_raw.get("content", ""),
                    })

            cp_list.append({
                "id":          cp_id,
                "focal":       meta.get("focal_key"),
                "alias":       meta.get("focal_alias"),
                "axis":        meta.get("active_axis"),
                "scope":       meta.get("active_scope"),
                "time":        meta.get("active_time"),
                "note":        meta.get("note"),
                "created_at":  meta.get("created_at"),
                "annotations": annotations,
            })

        return {
            "log_id":      self.concept_id,
            "name":        root_meta.get("name", ""),
            "checkpoints": cp_list,
            "count":       len(cp_list),
        }

    def op_delete(self) -> Dict[str, Any]:
        """[log.rm] Delete the active Log."""
        self._require_concept()

        scopes = self.allowed_scopes
        self.cortex.drop_chunk(self.concept_id, requester_scopes=scopes)

        self.session.set_context("active_log_root", None)
        self.session.set_context("active_log_container", None)
        return {"status": "deleted", "log_id": self.concept_id}
