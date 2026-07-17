"""
Curation Concept Model — interpretation as a narrative path over relationships.

Curation is NOT about a single Atom (that is what `fact` / `thesaurus` do — deep-dive
one atom). Curation interprets a SET of Atoms through the RELATIONSHIPS among them,
and its output is a NARRATIVE PATH: an ordered walk Atom→Atom, produced as the
result of an operation over chosen relations, or authored by a human/LLM.

Two invariants:
  • Relationship-centred. The operand is the relation structure, not the atom.
  • No burden of proof. A curation is an interpretation from a standpoint; it shows
    its GROUNDS (which relations / operation produced the path) but does not prove
    them. Its output is provenance:interpretation — cross-check with `fact` atoms if
    verification is actually needed.

Construction (two modes):
  • derived  — intersect (default) the adjacency of the chosen relation axes within
               the target set; the surviving edges chain into the narrative path
               (e.g. time-axis ∩ bloodline → a lineage-through-time). Other
               operators (union / compose / prefer) are reserved and fall back to
               intersect for now (op_applied reports which ran).
  • authored — a human/LLM supplies the ordered path (`ids=`); the model writes the
               curation:next edges, intentionally strengthening the narrative
               network — narrative-order-first.

Operators (3, the default — extensible):
  curation.new      create a curation (derive from relations, or author a path)
  curation.narrate  read the narrative path back (ordered atoms + grounds)
  curation.ls       list curations
"""

import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Curation")

INDEX_SET = "set:curation:index"
_REL_NEXT = "curation:next"                 # the derived interpretation edge (path step)
_REL_OVER = "curation:over"                 # curation root → each atom it interprets
_ORDERS_IMPLEMENTED = ("intersect",)        # relation operators with a real comparator


def _as_list(v) -> List[str]:
    """Accept a Python list, or a comma/space/newline-separated string (CSL-friendly)."""
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    parts = str(v).replace("\n", ",").replace(" ", ",").split(",")
    return [p.strip() for p in parts if p.strip()]


class CurationConcept(BaseConcept):
    """Interpretation as a narrative path: new (create) · narrate (read) · ls (list)."""

    CONCEPT_PREFIX = "curation"
    CONCEPT_LABEL  = "interpretation as a narrative path over relationships"

    CONCEPT_METHODS = {
        "new": {
            "op":     "op_new",
            "action": "write",
            "cli":    "cur.new",
            "args":   ["title"],
            "desc":   ("Create a curation (narrative path). Derive from relations: "
                       "curation new <title> set=<set> rels=a,b [op=intersect] — or author an "
                       "order: curation new <title> ids=x,y,z"),
        },
        "narrate": {
            "op":     "op_narrate",
            "action": "read",
            "cli":    "cur.narrate",
            "args":   ["curation_id"],
            "desc":   "Read a curation's narrative path back: curation narrate <curation_id|alias>",
        },
        "ls": {
            "op":     "op_ls",
            "action": "read",
            "cli":    "cur.ls",
            "args":   [],
            "desc":   "List curations: cur.ls",
        },
    }

    # ── helpers ────────────────────────────────────────────────────────────────

    def _author_scopes(self):
        uid = getattr(self.session, "client_id", "system")
        return uid, [f"owner:user_{uid}", f"view:user_{uid}"]

    def _scopes(self) -> List[str]:
        return getattr(self.session, "active_scopes", []) or []

    def _visible(self, key: str) -> bool:
        scopes = self._scopes()
        return (not scopes) or self.cortex.check_access(key, scopes)

    def _resolve(self, ref: str) -> Optional[str]:
        """Resolve an atom ref: direct key, alias, or bare word (leaf fallback)."""
        if not ref:
            return None
        if self.cortex.get_chunk(ref) is not None:
            return ref                                # already a real key
        key = self.cortex.resolve_alias(ref)
        if not key and ":" not in ref:
            keys = self.cortex.list_leaf(ref)
            if keys:
                key = keys[0]
        return key

    def _name(self, key: str) -> Optional[str]:
        aliases = self.cortex.get_aliases_by_key(key) or []
        return next((a for a in aliases if ":" in a), aliases[0] if aliases else None)

    def _step(self, key: str) -> Dict[str, Any]:
        content = (self.cortex.get_chunk(key) or "").strip()
        if content.startswith("[") and "\n" in content:
            content = content.split("\n", 1)[1].strip()   # drop the "[alias]" hub header
        return {"key": key, "name": self._name(key),
                "preview": content.split("\n", 1)[0][:80]}

    # ── the relation-algebra core (auto path discovery) ─────────────────────────

    def _derive_path(self, pool: List[str], rels: List[str], op: str) -> List[str]:
        """Order `pool` into a narrative chain via a relation operation.

        One axis → follow that relation's chain. Two+ axes with `intersect` → an edge
        a→b survives only if b is adjacent to a under EVERY axis (e.g. later-in-time
        AND descends-from); the surviving edges chain into the path. `op` values other
        than 'intersect' are reserved and treated as intersect for now.
        """
        pool_set = set(pool)
        if not rels:
            return list(pool)

        def adjacency(rel: str) -> Dict[str, set]:
            edges: Dict[str, set] = {}
            for a in pool:
                for (dst, _rel) in self.cortex.get_adjacent_links(a, rel):
                    if dst in pool_set and dst != a:
                        edges.setdefault(a, set()).add(dst)
            return edges

        per_axis = [adjacency(r) for r in rels]
        base = per_axis[0]
        edges: Dict[str, set] = {}
        for a, bs in base.items():
            inter = set(bs)
            for other in per_axis[1:]:
                inter &= other.get(a, set())
            if inter:
                edges[a] = inter

        # Chain: start at a node with no incoming surviving edge; walk deterministically.
        incoming = set().union(*edges.values()) if edges else set()
        start = next((a for a in pool if a not in incoming and a in edges), None)
        if start is None:
            start = next((a for a in pool if a not in incoming), pool[0] if pool else None)

        path: List[str] = []
        seen: set = set()
        cur = start
        while cur is not None and cur not in seen:
            path.append(cur)
            seen.add(cur)
            nxts = sorted(edges.get(cur, set()))
            cur = next((n for n in nxts if n not in seen), None)
        # The narrative IS the chain the operation reveals: atoms not connected under
        # every axis (e.g. time-adjacent but off the bloodline) are not on the path.
        return path

    # ── operators ───────────────────────────────────────────────────────────────

    def op_new(self, title: str, thesis: str = "", set: str = "",
               ids: Any = None, rels: Any = None, op: str = "intersect",
               mode: str = "", alias: str = "") -> Dict[str, Any]:
        """[curation.new] Create a curation — a narrative path interpreting a set of atoms.

        Target the atoms with `set=<name>` and/or `ids=<a,b,c>`. Then either:
          • derive  — pass `rels=<a,b>` (relation axes) [op=intersect]; the path is
                      computed from the relationship structure.
          • author  — pass `ids=` as the intended ORDER (no rels, or mode=authored);
                      the path is taken as given and its curation:next edges written.

        No burden of proof: the output is provenance:interpretation and records its
        grounds (the relation axes / operation used), but does not prove them.
        """
        if not title or not title.strip():
            raise ValueError("curation.new requires a title.")
        # Idempotent when an alias is given: re-running (e.g. a boot-loaded example CSL)
        # returns the existing curation instead of piling up duplicates.
        if alias:
            existing = self.cortex.resolve_alias(alias)
            if existing and (self.cortex.get_meta(existing) or {}).get("concept") == "curation":
                em = self.cortex.get_meta(existing) or {}
                return {
                    "status": "exists", "curation_id": existing,
                    "title": em.get("title", ""), "mode": em.get("mode", ""),
                    "op_applied": (em.get("lens") or {}).get("op", ""),
                    "grounds": em.get("lens", {}),
                    "path": [self._step(k) for k in (em.get("path") or [])],
                    "length": len(em.get("path") or []),
                }
        author, scopes = self._author_scopes()
        rel_list = _as_list(rels)
        id_list = [k for k in (self._resolve(r) for r in _as_list(ids)) if k]

        # Resolve the target pool. Accept the set name as given (user-facing sets from
        # `set.add name=X` are stored literally as X) or with the `set:` prefix.
        pool: List[str] = []
        if set:
            members = (self.cortex.get_collection_members(set)
                       or self.cortex.get_collection_members(
                           set if set.startswith("set:") else f"set:{set}"))
            pool = [k for k in (members or []) if self._visible(k)]
        if id_list:
            # ids extend/define the pool; preserve their order (matters for authored).
            pool = id_list + [k for k in pool if k not in id_list] if pool else id_list

        # Decide mode.
        authored = (mode == "authored") or (bool(id_list) and not rel_list)
        if authored:
            path = [k for k in id_list if self._visible(k)] or [k for k in pool if self._visible(k)]
            op_applied = "authored"
            resolved_mode = "authored"
        else:
            if not pool:
                raise ValueError("derive mode needs a target: set=<name> or ids=<list>.")
            op_applied = op if op in _ORDERS_IMPLEMENTED else "intersect"
            path = self._derive_path([k for k in pool if self._visible(k)], rel_list, op_applied)
            resolved_mode = "derived"

        # Materialise the curation root.
        root = self.cortex.put_chunk(
            content=f"[ Curation: {title.strip()} ]",
            meta={
                "type":       "concept",
                "concept":    "curation",
                "role":       "root",
                "title":      title.strip(),
                "thesis":     thesis.strip(),
                "mode":       resolved_mode,
                "lens":       {"rels": rel_list, "op": op_applied},
                "path":       path,
                "provenance": "interpretation",       # no burden of proof (ASI06 class)
                "created_at": time.time(),
            },
            author=author, scopes=scopes)
        self.concept_id = root
        self.set_name = f"set:concept:{root}"
        self.cortex.create_set(INDEX_SET)
        self.cortex.add_to_set(INDEX_SET, root)
        self.ensure_concept_set()                     # readable alias on the catalog set
        if alias:
            self.cortex.set_alias(root, alias)

        # Write the narrative edges (the derived interpretation) + membership.
        for i, key in enumerate(path):
            self.cortex.add_to_set(self.set_name, key)
            self.cortex.put_link(root, key, _REL_OVER, w=float(i), author=author)
            if i > 0:
                self.cortex.put_link(path[i - 1], key, _REL_NEXT, w=float(i), author=author)

        if hasattr(self.session, "set_context"):
            self.session.set_context("active_curation_root", root)

        return {
            "status":      "created",
            "curation_id": root,
            "title":       title.strip(),
            "mode":        resolved_mode,
            "op_applied":  op_applied,
            "grounds":     {"rels": rel_list, "op": op_applied},
            "path":        [self._step(k) for k in path],
            "length":      len(path),
        }

    def op_narrate(self, curation_id: str = "", name: str = "") -> Dict[str, Any]:
        """[curation.narrate] Read a curation's narrative path: the ordered atoms, the
        transitions between them, and the grounds (relation axes / operation). This is
        the story STRUCTURE — hand it to Jataka (`jataka.present as=narrative`) for prose."""
        ctx_get = getattr(self.session, "get_context", None)
        ref = curation_id or name or (ctx_get("active_curation_root") if ctx_get else None)
        if not ref:
            raise ValueError("Provide 'curation_id' or 'name'.")
        root = self.cortex.resolve_alias(ref) if ":" in str(ref) else None
        root = root or ref
        meta = self.cortex.get_meta(root) or {}
        if meta.get("concept") != "curation" or meta.get("role") != "root":
            raise ValueError(f"'{str(ref)[:16]}' is not a curation.")
        if not self._visible(root):
            raise ValueError("Curation not accessible.")

        path = [k for k in (meta.get("path") or []) if self._visible(k)]
        steps = [self._step(k) for k in path]
        transitions = [{"from": path[i - 1], "to": path[i], "rel": _REL_NEXT}
                       for i in range(1, len(path))]
        return {
            "type":        "curation:narrative",
            "curation_id": root,
            "title":       meta.get("title", ""),
            "thesis":      meta.get("thesis", ""),
            "mode":        meta.get("mode", ""),
            "grounds":     meta.get("lens", {}),
            "provenance":  meta.get("provenance", "interpretation"),
            "steps":       steps,
            "transitions": transitions,
            "length":      len(steps),
        }

    def op_ls(self) -> Dict[str, Any]:
        """[curation.ls] List curations."""
        items = []
        for key in self.cortex.get_collection_members(INDEX_SET) or []:
            if not self._visible(key):
                continue
            meta = self.cortex.get_meta(key) or {}
            if meta.get("concept") != "curation" or meta.get("role") != "root":
                continue
            items.append({
                "curation_id": key,
                "title":       meta.get("title", ""),
                "thesis":      meta.get("thesis", ""),
                "mode":        meta.get("mode", ""),
                "length":      len(meta.get("path") or []),
                "created_at":  meta.get("created_at", 0),
            })
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"curations": items, "count": len(items)}
