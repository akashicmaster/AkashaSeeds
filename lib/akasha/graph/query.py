"""
GraphQueryEngine.
Shared graph traversal/query runtime for Akasha concepts.

Capabilities:
    - BFS neighborhood walk
    - shortest path
    - trace traversal
    - degree summary

Expected cortex interface:
    cortex.get_adjacent_links(atom_id, rel)  → [[dst, rel], ...]
    cortex.get_incoming_links(atom_id, rel)  → [[src, rel], ...]
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

DEFAULT_MAX_VISIT = 10_000


class GraphQueryEngine:
    """Reusable graph traversal and query engine."""

    def __init__(
        self,
        cortex,
        visible_fn: Optional[Callable[[str], bool]] = None,
        meta_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
        content_fn: Optional[Callable[[str], str]] = None,
    ):
        self.cortex = cortex
        self.visible_fn = visible_fn or (lambda _: True)
        self.meta_fn = meta_fn or (lambda _: {})
        self.content_fn = content_fn or (lambda _: "")

    # =========================================================
    # Internal helpers
    # =========================================================

    def _neighbors(
        self,
        atom_id: str,
        rels: Optional[List[str]] = None,
        include_incoming: bool = False,
    ) -> List[Tuple[str, str, str]]:
        """
        Return (neighbor_id, relation, direction) tuples for *atom_id*.

        direction is ``"outgoing"`` or ``"incoming"``.
        """
        result: List[Tuple[str, str, str]] = []
        for rel in (rels or []):
            for dst, _rel in self.cortex.get_adjacent_links(atom_id, rel):
                result.append((dst, rel, "outgoing"))
            if include_incoming:
                for src, _rel in self.cortex.get_incoming_links(atom_id, rel):
                    result.append((src, rel, "incoming"))
        return result

    def _is_visible(self, atom_id: str, include_hidden: bool = False) -> bool:
        if include_hidden:
            return True
        return bool(self.visible_fn(atom_id))

    # =========================================================
    # WALK  (BFS neighborhood)
    # =========================================================

    def walk(
        self,
        start_id: str,
        rels: Optional[List[str]] = None,
        depth: int = 1,
        include_hidden: bool = False,
        include_incoming: bool = False,
        max_visit: int = DEFAULT_MAX_VISIT,
    ) -> Dict[str, Any]:
        """
        BFS neighborhood traversal up to *depth* hops.

        Returns ``{"start_id", "count", "neighbors"}``.
        Each neighbor entry includes ``id``, ``depth``, ``via``, ``direction``,
        ``content``, and ``meta``.
        """
        visited: Set[str] = {start_id}
        queue: deque = deque([(start_id, 0)])
        neighbors: List[Dict[str, Any]] = []

        while queue:
            current, current_depth = queue.popleft()
            if len(visited) >= max_visit or current_depth >= depth:
                continue
            for nxt, rel, direction in self._neighbors(
                current, rels=rels, include_incoming=include_incoming,
            ):
                if nxt in visited:
                    continue
                visited.add(nxt)
                if not self._is_visible(nxt, include_hidden):
                    continue
                neighbors.append({
                    "id":        nxt,
                    "depth":     current_depth + 1,
                    "via":       rel,
                    "direction": direction,
                    "content":   self.content_fn(nxt),
                    "meta":      self.meta_fn(nxt),
                })
                queue.append((nxt, current_depth + 1))

        return {"start_id": start_id, "count": len(neighbors), "neighbors": neighbors}

    # =========================================================
    # PATH  (shortest-path BFS)
    # =========================================================

    def path(
        self,
        src_id: str,
        dst_id: str,
        rels: Optional[List[str]] = None,
        max_depth: int = 6,
        include_hidden: bool = False,
        include_incoming: bool = False,
        max_visit: int = DEFAULT_MAX_VISIT,
    ) -> Dict[str, Any]:
        """
        BFS shortest path from *src_id* to *dst_id*.

        Returns ``{"found", "path", "relations", "length"}``.
        ``length`` is ``-1`` when no path exists.
        """
        if src_id == dst_id:
            return {"found": True, "path": [src_id], "relations": [], "length": 0}

        visited: Set[str] = {src_id}
        queue: deque = deque([(src_id, [], [])])

        while queue:
            current, path_nodes, path_rels = queue.popleft()
            if len(visited) >= max_visit or len(path_nodes) >= max_depth:
                continue
            for nxt, rel, _dir in self._neighbors(
                current, rels=rels, include_incoming=include_incoming,
            ):
                if nxt in visited:
                    continue
                visited.add(nxt)
                if not self._is_visible(nxt, include_hidden):
                    continue
                new_nodes = path_nodes + [current]
                new_rels  = path_rels  + [rel]
                if nxt == dst_id:
                    final_path = new_nodes + [nxt]
                    return {
                        "found":     True,
                        "path":      final_path,
                        "relations": new_rels,
                        "length":    len(final_path) - 1,
                    }
                queue.append((nxt, new_nodes, new_rels))

        return {"found": False, "path": [], "relations": [], "length": -1}

    # =========================================================
    # TRACE  (provenance / relationship traversal)
    # =========================================================

    def trace(
        self,
        start_id: str,
        rels: Optional[List[str]] = None,
        depth: int = 3,
        include_hidden: bool = False,
        include_incoming: bool = True,
        max_visit: int = DEFAULT_MAX_VISIT,
    ) -> Dict[str, Any]:
        """
        Provenance/relationship traversal preserving the full edge chain.

        Unlike ``walk()``, a node may appear multiple times if reached via
        different paths, making it suitable for provenance debugging.

        Returns ``{"start_id", "count", "trace"}``.
        Each trace entry includes ``target``, ``depth``, ``chain``,
        ``meta``, and ``content``.
        """
        visited: Set[str] = set()
        results: List[Dict[str, Any]] = []
        queue: deque = deque([(start_id, 0, [])])

        while queue:
            current, current_depth, chain = queue.popleft()
            if current in visited or len(visited) >= max_visit:
                continue
            visited.add(current)
            if current_depth >= depth:
                continue
            for nxt, rel, direction in self._neighbors(
                current, rels=rels, include_incoming=include_incoming,
            ):
                if not self._is_visible(nxt, include_hidden):
                    continue
                edge = {"from": current, "to": nxt, "relation": rel, "direction": direction}
                new_chain = chain + [edge]
                results.append({
                    "target":  nxt,
                    "depth":   current_depth + 1,
                    "chain":   new_chain,
                    "meta":    self.meta_fn(nxt),
                    "content": self.content_fn(nxt),
                })
                queue.append((nxt, current_depth + 1, new_chain))

        return {"start_id": start_id, "count": len(results), "trace": results}

    # =========================================================
    # DEGREE
    # =========================================================

    def degree(
        self,
        atom_id: str,
        rels: Optional[List[str]] = None,
        include_incoming: bool = True,
    ) -> Dict[str, Any]:
        """Graph degree summary for *atom_id* across the given relations."""
        outgoing = 0
        incoming = 0
        for rel in (rels or []):
            outgoing += len(self.cortex.get_adjacent_links(atom_id, rel))
            if include_incoming:
                incoming += len(self.cortex.get_incoming_links(atom_id, rel))
        return {
            "atom_id":  atom_id,
            "outgoing": outgoing,
            "incoming": incoming,
            "total":    outgoing + incoming,
        }
