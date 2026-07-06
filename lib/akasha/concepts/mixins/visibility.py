"""
VisibilityMixin.
Shared visibility helpers for Akasha Concept Models.

Provides:
    - hidden / revealed / archived / tombstoned checks
    - transition-link based visibility
    - concept-neutral visibility vocabulary

Expected host class attributes:
    self.cortex
    self.allowed_scopes
    self._meta(key)
"""
from __future__ import annotations

from typing import Any, Dict


class VisibilityMixin:
    """Reusable semantic visibility checks for concept models."""

    REL_REVEALED_BY   = "sys:revealed_by"
    REL_HIDDEN_BY     = "sys:hidden_by"
    REL_ARCHIVED_BY   = "sys:archived_by"
    REL_TOMBSTONED_BY = "sys:tombstoned_by"

    # ------------------------------------------------------------------
    # Link probe
    # ------------------------------------------------------------------

    def _has_out_link(self, atom_id: str, rel: str) -> bool:
        try:
            return bool(self.cortex.get_adjacent_links(atom_id, rel))
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Access-control layer (IAM only — no semantic state)
    # ------------------------------------------------------------------

    def _base_access_visible(self, atom_id: str) -> bool:
        if not atom_id:
            return False
        return bool(self.cortex.check_access(atom_id, self.allowed_scopes))

    # ------------------------------------------------------------------
    # Semantic state checks
    # ------------------------------------------------------------------

    def _is_revealed(self, atom_id: str) -> bool:
        return self._has_out_link(atom_id, self.REL_REVEALED_BY)

    def _is_hidden(self, atom_id: str) -> bool:
        meta = self._meta(atom_id) or {}
        return bool(meta.get("hidden")) or self._has_out_link(atom_id, self.REL_HIDDEN_BY)

    def _is_archived(self, atom_id: str) -> bool:
        meta = self._meta(atom_id) or {}
        return bool(meta.get("archived")) or self._has_out_link(atom_id, self.REL_ARCHIVED_BY)

    def _is_tombstoned(self, atom_id: str) -> bool:
        meta = self._meta(atom_id) or {}
        return bool(meta.get("tombstoned")) or self._has_out_link(atom_id, self.REL_TOMBSTONED_BY)

    # ------------------------------------------------------------------
    # Composite visibility
    # ------------------------------------------------------------------

    def _visible_semantic(
        self,
        atom_id: str,
        include_hidden: bool = False,
        include_archived: bool = True,
        include_tombstoned: bool = False,
    ) -> bool:
        """
        IAM + semantic visibility.

        Hidden atoms become visible if:
            - ``include_hidden=True``
            - OR the atom has a ``sys:revealed_by`` link

        Tombstoned atoms are excluded by default.
        Archived atoms are included by default.
        """
        if not self._base_access_visible(atom_id):
            return False
        if self._is_tombstoned(atom_id) and not include_tombstoned:
            return False
        if self._is_archived(atom_id) and not include_archived:
            return False
        if self._is_hidden(atom_id):
            return include_hidden or self._is_revealed(atom_id)
        return True

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def _visibility_state(self, atom_id: str) -> Dict[str, Any]:
        """Return a full visibility audit dict for *atom_id*."""
        return {
            "atom_id":        atom_id,
            "access_visible": self._base_access_visible(atom_id),
            "hidden":         self._is_hidden(atom_id),
            "revealed":       self._is_revealed(atom_id),
            "archived":       self._is_archived(atom_id),
            "tombstoned":     self._is_tombstoned(atom_id),
        }
