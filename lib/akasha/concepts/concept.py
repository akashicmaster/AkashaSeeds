"""
Concept Concept Model — a navigator over the CONCEPT HIERARCHY (the sys:is_a up/down structure).

The ontology's concepts form a subset/superset lattice via `sys:is_a` — a lower concept `sys:is_a`
its upper concept (its instances are a subset of the upper's). This model lets you walk that
lattice SYSTEMATICALLY, from the top down, ignoring every other kind of link and every membership
set — only the concept up/down relation is followed.

  concept.roots      the top of the hierarchy — the universal roles (role:product / component /
                     method / producer) with their domain children; or one field's top with `field=`
  concept.tree       descend the sys:is_a tree from a concept (or from the roots) — depth- and
                     fan-out-bounded, with child counts and an ascii render
  concept.children   the immediate sub-concepts of one concept (paginated)

Only `sys:is_a` is traversed (never made_from / method_of / thesaurus:related / membership sets),
so the view is the pure concept skeleton. READ-level; scope-filtered. Cost is bounded: a node
fetches its children in one query and resolves aliases only for the page it shows, so an
empty/huge fan-out (e.g. every dish under `meal`) never triggers an O(N) alias/adjacency storm.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Concept")


class ConceptConcept(BaseConcept):
    """Walk the sys:is_a concept lattice: list the roots, descend the tree, list sub-concepts."""

    CONCEPT_PREFIX = "concept"
    CONCEPT_LABEL  = "concept hierarchy navigator — the sys:is_a subset/superset lattice"

    IS_A = "sys:is_a"
    # The canonical apex of the made-thing ontology (see docs/for-llm/product-component-ontology).
    ROLES = ("role:product", "role:component", "role:method", "role:producer")
    MAX_DEPTH = 6
    DEFAULT_DEPTH = 2
    DEFAULT_LIMIT = 25
    MAX_LIMIT = 100

    CONCEPT_METHODS = {
        "roots":    {"op": "op_roots", "action": "read", "cli": "concept.roots", "args": [],
                     "desc": ("Top of the concept hierarchy as a taxonomy — the universal roles + "
                              "their domains: concept.roots [field=<concept>] [depth=2] [limit=25] "
                              "[leaves=yes]")},
        "tree":     {"op": "op_tree", "action": "read", "cli": "concept.tree", "args": ["root"],
                     "desc": ("Descend the concept (sys:is_a) taxonomy: concept.tree [root=<concept>] "
                              "[depth=2] [limit=25] [leaves=yes] — concept up/down only; branches "
                              "expanded, instances folded into a count")},
        "children": {"op": "op_children", "action": "read", "cli": "concept.children", "args": ["id"],
                     "desc": "Immediate sub-concepts of a concept: concept.children id=<concept> [limit=]"},
    }

    # ── config coercion ─────────────────────────────────────────────────────────
    def _depthf(self, v: Any, default: int = None) -> int:
        try:
            d = int(v)
        except (TypeError, ValueError):
            d = self.DEFAULT_DEPTH if default is None else default
        return max(0, min(d, self.MAX_DEPTH))

    def _limitf(self, v: Any) -> int:
        try:
            n = int(v)
        except (TypeError, ValueError):
            n = self.DEFAULT_LIMIT
        return max(1, min(n, self.MAX_LIMIT))

    # ── graph helpers (sys:is_a only) ────────────────────────────────────────────
    def _scopes(self) -> List[str]:
        return getattr(self.session, "active_scopes", []) or []

    def _visible(self, key: str) -> bool:
        sc = self._scopes()
        try:
            return (not sc) or self.cortex.check_access(key, sc)
        except Exception:
            return True

    def _alias(self, key: str) -> str:
        aliases = self.cortex.get_aliases_by_key(key) or []
        return next((a for a in aliases if ":" in a), aliases[0] if aliases else key)

    def _label(self, alias: str) -> str:
        return alias.split(":")[-1].replace("_", " ") if ":" in alias else alias

    def _resolve(self, ref: str) -> Optional[str]:
        ref = (ref or "").strip()
        if not ref:
            return None
        if self.cortex.get_chunk(ref) is not None:
            return ref
        return self.cortex.resolve_alias(ref)

    def _cores(self) -> list:
        cs = []
        cc = getattr(self.cortex, "core", None)
        if cc is not None:
            cs.append(cc)
        nc = getattr(getattr(self.session, "nucleus", None), "core", None)
        if nc is not None and nc is not cc:
            cs.append(nc)
        return cs

    def _family(self) -> tuple:
        """The `sys:is_a` FAMILY the navigator follows: `sys:is_a` itself plus every relation
        declared a sub-relation of it (`reldef:<r> sys:is_a reldef:sys:is_a`) — today that adds
        `specializes` (a word-sense is a more specific sense of its lemma). Read once from the
        reldef lattice and cached; tiny. This is what lets proto-words/lemmas and their senses
        join the concept hierarchy without special-casing per field."""
        cached = getattr(self, "_family_tuple", None)
        if cached is not None:
            return cached
        fam = {self.IS_A}
        root = None
        try:
            root = self.cortex.resolve_alias(f"reldef:{self.IS_A}")   # reldef:sys:is_a
        except Exception:
            root = None
        if root:
            for (src, rel) in (self.cortex.get_incoming_links(root, self.IS_A) or []):
                if rel != self.IS_A:
                    continue
                a = self._alias(src)                                  # e.g. "reldef:specializes"
                if a.startswith("reldef:"):
                    fam.add(a.split(":", 1)[1])                       # → "specializes"
        self._family_tuple = tuple(sorted(fam))
        return self._family_tuple

    def _taxa(self) -> set:
        """The set of BRANCH concepts (taxa) — every concept that is the parent of ≥1 edge in the
        is-a FAMILY (has a sub-concept). Fetched once per request (cheap: distinct parents over the
        family, ONE query) and cached. A concept NOT in this set is a leaf/instance. If the backend
        lacks the primitive, returns empty → the navigator degrades to the flat view."""
        cached = getattr(self, "_taxa_set", None)
        if cached is not None:
            return cached
        taxa: set = set()
        fam = list(self._family())
        for core in self._cores():
            fn = getattr(core, "distinct_link_dsts", None)
            if fn:
                try:
                    taxa.update(fn(fam))
                except Exception:
                    pass
        self._taxa_set = taxa
        return taxa

    def _child_keys(self, key: str) -> List[str]:
        """The keys of a concept's immediate sub-concepts — incoming links over the is-a FAMILY
        (sys:is_a ∪ specializes …), scope-filtered, de-duped, DAG-safe (self-excluded). NO alias
        lookups here (so counting a huge fan-out is cheap)."""
        out: List[str] = []
        seen = set()
        for r in self._family():
            for (src, rel) in (self.cortex.get_incoming_links(key, r) or []):
                if rel == r and src not in seen and src != key and self._visible(src):
                    seen.add(src)
                    out.append(src)
        return out

    def _node(self, key: str, depth: int, limit: int, alias: str = None,
              taxonomic: bool = True) -> Dict[str, Any]:
        """A tree node. In the default TAXONOMIC view (like a biological classification) only the
        branch concepts (taxa — children that themselves have sub-concepts) are expanded, and the
        leaf instances are folded into `leaf_count`; with taxonomic=False every child is shown.
        Aliases are resolved only for the shown page (bounded cost)."""
        alias = alias or self._alias(key)
        ck = self._child_keys(key)
        node: Dict[str, Any] = {"id": alias, "name": self._label(alias), "child_count": len(ck)}
        if taxonomic:
            taxa = self._taxa()
            expand = [k for k in ck if k in taxa] if taxa else ck   # branches only (taxa)
            node["leaf_count"] = len(ck) - len(expand)              # instances folded into a count
        else:
            expand = ck
        if depth > 0 and expand:
            shown = sorted((self._alias(k), k) for k in expand[:limit])   # alias only the page
            node["children"] = [self._node(k, depth - 1, limit, alias=a, taxonomic=taxonomic)
                                for a, k in shown]
            if len(expand) > len(shown):
                node["truncated"] = len(expand) - len(shown)
        return node

    # ── ascii render ─────────────────────────────────────────────────────────────
    def _render(self, node: Dict[str, Any], prefix: str = "", is_root: bool = True) -> List[str]:
        lines: List[str] = []
        if is_root:
            cnt = f"  [{node['child_count']}]" if node.get("child_count") else ""
            lines.append(f"{node['name']}  ({node['id']}){cnt}")
        kids = node.get("children", [])
        trunc = node.get("truncated", 0)
        leaves = node.get("leaf_count", 0)
        for i, ch in enumerate(kids):
            last = (i == len(kids) - 1) and not trunc and not leaves
            branch = "└─ " if last else "├─ "
            cnt = f"  [{ch['child_count']}]" if ch.get("child_count") else ""
            lines.append(f"{prefix}{branch}{ch['name']}  ({ch['id']}){cnt}")
            lines += self._render(ch, prefix + ("   " if last else "│  "), is_root=False)
        if trunc:
            lines.append(f"{prefix}├─ … +{trunc} more sub-groups" if leaves
                         else f"{prefix}└─ … +{trunc} more sub-groups")
        if leaves:
            lines.append(f"{prefix}└─ · {leaves} instance(s)  (concept.children id={node['id']})")
        return lines

    # ── operators ────────────────────────────────────────────────────────────────
    @staticmethod
    def _taxo(leaves: Any) -> bool:
        """Taxonomic (branch-only) view unless leaves=yes asks to show every instance."""
        return str(leaves).strip().lower() not in ("yes", "true", "1", "y")

    def op_roots(self, field: str = "", depth: Any = "", limit: Any = "",
                 leaves: Any = "") -> Dict[str, Any]:
        """[concept.roots] The top of the concept hierarchy, as a taxonomy. With no argument: the
        universal roles (product / component / method / producer) each expanded to their domain
        children — the systematic apex. With `field=<concept>`: that concept's own sub-tree. Only
        branch concepts (taxa) are expanded and leaf instances are folded into a count; pass
        `leaves=yes` to show every instance. READ-level."""
        lim = self._limitf(limit)
        tax = self._taxo(leaves)
        if field:
            key = self._resolve(field)
            if not key:
                raise ValueError("concept.roots: no such field concept.")
            node = self._node(key, self._depthf(depth, 2), lim, taxonomic=tax)
            return {"type": "concept:roots", "field": self._alias(key),
                    "roots": [node], "ascii": "\n".join(self._render(node))}
        roots = []
        for r in self.ROLES:
            key = self._resolve(r)
            if key:
                roots.append(self._node(key, self._depthf(depth, 2), lim, alias=r, taxonomic=tax))
        ascii_ = "\n\n".join("\n".join(self._render(x)) for x in roots)
        return {"type": "concept:roots", "roots": roots, "count": len(roots), "ascii": ascii_}

    def op_tree(self, root: str = "", depth: Any = "", limit: Any = "",
                leaves: Any = "") -> Dict[str, Any]:
        """[concept.tree] Descend the concept (sys:is_a) tree from `root` (or from the roots when
        omitted), as a taxonomy — only branch concepts are expanded, leaf instances folded into a
        count (pass `leaves=yes` for the full listing). Depth- and fan-out-bounded; only the
        concept up/down relation is followed — every other link type and every set is ignored.
        READ-level."""
        ref = (root or "").strip()
        if not ref:
            return self.op_roots(field="", depth=depth, limit=limit, leaves=leaves)
        key = self._resolve(ref)
        if not key:
            raise ValueError("concept.tree: no such concept.")
        node = self._node(key, self._depthf(depth), self._limitf(limit), taxonomic=self._taxo(leaves))
        return {"type": "concept:tree", "root": self._alias(key),
                "tree": node, "ascii": "\n".join(self._render(node))}

    def op_children(self, id: str = "", name: str = "", limit: Any = "",
                    offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[concept.children] The immediate sub-concepts of one concept (incoming sys:is_a),
        paginated. Aliases resolved for the page only. READ-level."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError("concept.children: no such concept.")
        ck = self._child_keys(key)
        lim = self._limitf(limit)
        try:
            start = int(cursor or offset or 0)
        except (TypeError, ValueError):
            start = 0
        page_keys = ck[start:start + lim]
        results = [{"id": a, "name": self._label(a)}
                   for a, _k in sorted((self._alias(k), k) for k in page_keys)]
        nxt = start + lim
        return {"type": "concept:children", "id": self._alias(key),
                "results": results, "count": len(ck),
                "next_cursor": str(nxt) if nxt < len(ck) else None,
                "has_more": nxt < len(ck)}
