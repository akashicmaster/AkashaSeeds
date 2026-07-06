"""
TemporalMixin.
Shared temporal linked-list utilities for Akasha Concept Models.

Provides:
    - ISO-like time normalization
    - event-sourced temporal linked list (insert-sorted)
    - rebuild support (re-sort from subset atoms)
    - chronological walk

Expected host class attributes:
    self.cortex
    self.concept_id
    self.allowed_scopes
    self._meta(key)
    self._visible(key)
    self._summary(key)
    self._members(subset)
    self._content(key)
    self._require_concept()
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

TIME_TOP = "sys:time_top"
TIME_BOTTOM = "sys:time_bottom"
TIME_NEXT = "sys:time_next"
TIME_PREVIOUS = "sys:time_previous"
UNDATED_SORT_KEY = "9999-12-31T23:59:59"


class TemporalMixin:
    """Reusable temporal index for concept models."""

    TEMPORAL_TYPES: Sequence[str] = ()
    TEMPORAL_SUBSETS: Sequence[str] = ()

    # ------------------------------------------------------------------
    # Time normalization
    # ------------------------------------------------------------------

    def _normalize_time_sort(self, value: str = "") -> str:
        """
        Normalize a caller-supplied time string into a lexicographically
        sortable ``YYYY-MM-DDTHH:MM:SS`` key.

        Accepted input formats (partial ISO 8601):
            YYYY
            YYYY-MM
            YYYY-MM-DD
            YYYY-MM-DDTHH:MM:SS  (or longer)

        Anything unparseable or empty sorts last (``9999-12-31T23:59:59``).
        """
        if not value:
            return UNDATED_SORT_KEY
        raw = str(value).strip()
        if not raw:
            return UNDATED_SORT_KEY
        try:
            if len(raw) == 4 and raw.isdigit():
                return f"{raw}-01-01T00:00:00"
            if len(raw) == 7:
                datetime.strptime(raw, "%Y-%m")
                return f"{raw}-01T00:00:00"
            if len(raw) == 10:
                datetime.strptime(raw, "%Y-%m-%d")
                return f"{raw}T00:00:00"
            if len(raw) >= 19:
                datetime.fromisoformat(raw[:19])
                return raw[:19]
        except Exception:
            pass
        return UNDATED_SORT_KEY

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_time_sort(self, node_id: str) -> str:
        """Return the effective sort key for a temporal node."""
        meta = self._meta(node_id)
        if meta.get("time_sort"):
            return meta["time_sort"]
        raw = (
            meta.get("occurred_at")
            or meta.get("event_time")
            or meta.get("observed_at")
            or meta.get("captured_at")
            or ""
        )
        return self._normalize_time_sort(raw)

    def _collect_temporal_nodes(self) -> List[str]:
        """Gather temporal atoms from all declared TEMPORAL_SUBSETS."""
        nodes: List[str] = []
        seen: set = set()
        for subset in self.TEMPORAL_SUBSETS:
            for key in self._members(subset):
                if key in seen:
                    continue
                if self.TEMPORAL_TYPES:
                    atom_type = self._meta(key).get("type", "")
                    if atom_type not in self.TEMPORAL_TYPES:
                        continue
                seen.add(key)
                nodes.append(key)
        return nodes

    def _clear_time_index(self) -> None:
        """Remove all temporal index links from the active concept root."""
        self._require_concept()
        temporal_nodes = self._collect_temporal_nodes()
        for rel in (TIME_TOP, TIME_BOTTOM):
            for dst, _ in list(self.cortex.get_adjacent_links(self.concept_id, rel)):
                self.cortex.remove_link(self.concept_id, dst, rel)
        for node_id in temporal_nodes:
            for rel in (TIME_NEXT, TIME_PREVIOUS):
                for dst, _ in list(self.cortex.get_adjacent_links(node_id, rel)):
                    self.cortex.remove_link(node_id, dst, rel)

    # ------------------------------------------------------------------
    # Temporal index — insert
    # ------------------------------------------------------------------

    def _append_to_time_index(
        self,
        node_id: str,
        author_id: str,
        time_sort: Optional[str] = None,
    ) -> None:
        """
        Insert *node_id* into the root-level temporal linked list.

        Maintains:
            root  ──sys:time_top──▶   oldest atom
            root  ──sys:time_bottom──▶ newest atom
            atom  ──sys:time_next──▶  next newer atom
            atom  ──sys:time_previous──▶ next older atom

        Insertion is O(n); acceptable for the typical hundreds-of-events
        range per concept root.
        """
        self._require_concept()
        sort_key = time_sort if time_sort is not None else self._get_time_sort(node_id)

        top_links = self.cortex.get_adjacent_links(self.concept_id, TIME_TOP)
        if not top_links:
            # Empty index — node is both top and bottom
            self.cortex.put_link(self.concept_id, node_id, TIME_TOP, author=author_id)
            self.cortex.put_link(self.concept_id, node_id, TIME_BOTTOM, author=author_id)
            return

        current = top_links[0][0]
        previous = ""
        while current:
            current_sort = self._get_time_sort(current)
            if sort_key < current_sort:
                # Insert before current
                if previous:
                    self.cortex.remove_link(previous, current, TIME_NEXT)
                    self.cortex.put_link(previous, node_id, TIME_NEXT, author=author_id)
                    self.cortex.put_link(node_id, previous, TIME_PREVIOUS, author=author_id)
                else:
                    self.cortex.remove_link(self.concept_id, current, TIME_TOP)
                    self.cortex.put_link(self.concept_id, node_id, TIME_TOP, author=author_id)
                self.cortex.put_link(node_id, current, TIME_NEXT, author=author_id)
                self.cortex.put_link(current, node_id, TIME_PREVIOUS, author=author_id)
                return
            next_links = self.cortex.get_adjacent_links(current, TIME_NEXT)
            if not next_links:
                break
            previous = current
            current = next_links[0][0]

        # Append after the last node
        self.cortex.put_link(current, node_id, TIME_NEXT, author=author_id)
        self.cortex.put_link(node_id, current, TIME_PREVIOUS, author=author_id)
        for dst, _ in list(self.cortex.get_adjacent_links(self.concept_id, TIME_BOTTOM)):
            self.cortex.remove_link(self.concept_id, dst, TIME_BOTTOM)
        self.cortex.put_link(self.concept_id, node_id, TIME_BOTTOM, author=author_id)

    # ------------------------------------------------------------------
    # Temporal index — read
    # ------------------------------------------------------------------

    def _walk_time_index(
        self,
        limit: int = 100,
        atom_types: Optional[List[str]] = None,
        include_hidden: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Walk the temporal index oldest → newest, returning up to *limit*
        visible entries.

        *atom_types* filters by ``meta["type"]``; pass ``None`` for all types.
        """
        self._require_concept()
        result: List[Dict[str, Any]] = []
        top_links = self.cortex.get_adjacent_links(self.concept_id, TIME_TOP)
        if not top_links:
            return result

        current = top_links[0][0]
        seen: set = set()
        cap = max(1, int(limit))

        while current and current not in seen and len(result) < cap:
            seen.add(current)
            if self._visible(current):
                meta = self._meta(current)
                atom_type = meta.get("type", "")
                if not atom_types or atom_type in atom_types:
                    if include_hidden or not meta.get("hidden", False):
                        result.append({
                            "id": current,
                            "content": self._content(current),
                            "type": atom_type,
                            "occurred_at": (
                                meta.get("occurred_at")
                                or meta.get("event_time")
                                or meta.get("observed_at")
                                or meta.get("captured_at")
                                or ""
                            ),
                            "time_sort": self._get_time_sort(current),
                            "meta": meta,
                        })
            next_links = self.cortex.get_adjacent_links(current, TIME_NEXT)
            current = next_links[0][0] if next_links else ""

        return result

    # ------------------------------------------------------------------
    # Temporal index — rebuild
    # ------------------------------------------------------------------

    def _rebuild_time_index(self, author_id: str) -> Dict[str, Any]:
        """
        Rebuild the temporal linked list from scratch using all atoms
        declared in TEMPORAL_SUBSETS.

        Run once after bulk import of pre-dated data or after deploying
        the temporal index for the first time.
        """
        self._require_concept()
        nodes = self._collect_temporal_nodes()
        self._clear_time_index()
        nodes.sort(key=self._get_time_sort)
        for node_id in nodes:
            self._append_to_time_index(
                node_id=node_id,
                author_id=author_id,
                time_sort=self._get_time_sort(node_id),
            )
        return {
            "status": "time_index_rebuilt",
            "concept_id": self.concept_id,
            "count": len(nodes),
        }
