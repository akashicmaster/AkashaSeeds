"""
Thesaurus Concept Model.

Manages semantic enrichment of atoms via typed relation links and computes
a per-atom ShelfScore that reflects the richness of its semantic neighborhood.

ShelfScore components (all clamped [0, 1]):
  link_total           raw thesaurus link count / 8              w=0.05
  synonym_coverage     (synonym + near_synonym) / 3             w=0.20
  antonym_presence     min(antonym count, 1)                    w=0.05
  chain_balance        hypernym and hyponym presence, balanced   w=0.05
  example_density      example_usage count / 2                  w=0.20
  affective_score      affective link count / 3                  w=0.20
  namespace_bridges    namespace_bridge count / 2               w=0.15
  external_refs        external reference count / 4             w=0.10
  specialization_depth log10(1 + inbound specializes count)     w=0.03

specialization_depth rewards proto-words that multiple ontology sessions
independently defined — high-frequency concepts surface naturally.
Max shelf_score is 1.03 when all components saturate.

Relation types are registered in ontology/thesaurus/a_thesaurus_core.csl.
Operators use those relation strings directly (e.g. "thesaurus:synonym").

Index sets:
  set:thesaurus:index       atoms that carry any thesaurus link
  set:thesaurus:curations   CurationCollection roots and CuratedAtoms
  set:thesaurus:series      ExhibitionSeries roots
"""

import math
import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Thesaurus")

_INDEX_SET      = "set:thesaurus:index"
_CURATION_SET   = "set:thesaurus:curations"
_SERIES_SET     = "set:thesaurus:series"

# Relation type strings (mirrors ontology/thesaurus/a_thesaurus_core.csl)
_REL_SYNONYM   = "thesaurus:synonym"
_REL_NEAR_SYN  = "thesaurus:near_synonym"
_REL_ANTONYM   = "thesaurus:antonym"
_REL_HYPERNYM  = "thesaurus:hypernym"
_REL_HYPONYM   = "thesaurus:hyponym"
_REL_EXAMPLE   = "thesaurus:example_usage"
_REL_AFFECTIVE = "thesaurus:affective"
_REL_NS_BRIDGE = "thesaurus:namespace_bridge"
_REL_EXTERNAL  = "thesaurus:external_ref"
_REL_INTERPRETS  = "thesaurus:interprets"
_REL_IN_CURATION = "thesaurus:in_curation"
_REL_SEQ_NEXT    = "thesaurus:seq_next"
_REL_IN_SERIES   = "thesaurus:in_series"

_SCORE_WEIGHTS: Dict[str, float] = {
    "link_total":           0.05,
    "synonym_coverage":     0.20,
    "antonym_presence":     0.05,
    "chain_balance":        0.05,
    "example_density":      0.20,
    "affective_score":      0.20,
    "namespace_bridges":    0.15,
    "external_refs":        0.10,
    "specialization_depth": 0.03,
}


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _url_slug(alias: Optional[str]) -> Optional[str]:
    """Derive URL slug from a qualified alias by taking the last colon-segment.

    "word:en:memory"              → "memory"
    "curations:sky-dreamers-vol1" → "sky-dreamers-vol1"
    "series:dreams-genealogy"     → "dreams-genealogy"
    """
    if not alias:
        return None
    return alias.split(":")[-1] if ":" in alias else alias


class ThesaurusConcept(BaseConcept):
    """Semantic enrichment, ShelfScore computation, and curation management."""

    CONCEPT_PREFIX = "thesaurus"

    CONCEPT_METHODS = {
        "shelf.score":    "op_shelf_score",
        "shelf.list":     "op_shelf_list",
        "shelf.link":     "op_shelf_link",
        "shelf.link_ext": "op_shelf_link_ext",
        "curation.new":   "op_curation_new",
        "curation.ls":    "op_curation_list",
        "curation.atom":  "op_curation_atom",
        "series.new":     "op_series_new",
        "series.ls":      "op_series_list",
        "series.add":     "op_series_add",
        "view.atom":      "op_view_atom",
        "view.curation":  "op_view_curation",
        "view.series":    "op_view_series",
    }

    def __init__(self, session: Any):
        super().__init__(session)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _author(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _scopes(self) -> List[str]:
        uid = self._author()
        return [f"owner:user_{uid}", f"view:user_{uid}"]

    def _resolve_atom(self, atom_id: Optional[str], name: Optional[str],
                      required: bool = True) -> Optional[str]:
        """Return the internal key for atom_id (direct) or alias name (lookup).

        When required=False, returns None instead of raising on missing alias.
        """
        if atom_id:
            return atom_id
        if name:
            key = self.cortex.resolve_alias(name)
            if not key and ":" not in name:
                # Bare word fallback: "memory" → leaf:memory collection
                keys = self.cortex.list_leaf(name)
                if keys:
                    key = keys[0]
            if not key:
                if required:
                    raise ValueError(f"Atom not found for alias '{name}'.")
                return None
            return key
        raise ValueError("Provide 'atom_id' or 'name'.")

    def _count_links(self, atom_id: str, rel: str) -> int:
        return len(self.cortex.get_adjacent_links(atom_id, rel))

    def _count_inbound_links(self, atom_id: str, rel: str) -> int:
        return len(self.cortex.get_incoming_links(atom_id, rel))

    def _count_links_with_fallback(self, atom_id: str, primary: str, *fallbacks: str) -> int:
        """Count links by primary rel type; if zero, sum the fallback rel types."""
        n = self._count_links(atom_id, primary)
        if n:
            return n
        return sum(self._count_links(atom_id, fb) for fb in fallbacks)

    def _atom_stub(self, key: str) -> Dict[str, Any]:
        """Return minimal public-facing atom data: key, primary alias, description."""
        aliases = self.cortex.get_aliases_by_key(key) or []
        name = next((a for a in aliases if ":" in a), aliases[0] if aliases else None)
        return {
            "key":         key,
            "name":        name,
            "url_slug":    _url_slug(name),
            "description": self.cortex.get_chunk(key),
        }

    def _atom_full(self, key: str) -> Dict[str, Any]:
        """Return full atom data: all aliases, meta, and cleaned description."""
        aliases = self.cortex.get_aliases_by_key(key) or []
        name = next((a for a in aliases if ":" in a), aliases[0] if aliases else None)
        raw_content = self.cortex.get_chunk(key) or ""
        # Strip the "[alias]\n" hub prefix so description is clean for display
        desc = raw_content
        if desc.startswith("[") and "\n" in desc:
            desc = desc.split("\n", 1)[1].strip()
        meta = self.cortex.get_meta(key) or {}
        return {
            "key":         key,
            "name":        name,
            "url_slug":    _url_slug(name),
            "description": desc,
            "aliases":     aliases,
            "meta":        meta,
        }

    def _external_refs_for(self, key: str) -> List[Dict[str, Any]]:
        """Return ordered list of external reference dicts for an atom."""
        links = self.cortex.get_adjacent_links(key, _REL_EXTERNAL)
        refs = []
        for (ref_key, _) in links:
            meta = self.cortex.get_meta(ref_key) or {}
            if meta.get("type") == "thesaurus:ExternalRef":
                refs.append({
                    "label": meta.get("label", ""),
                    "url":   meta.get("url") or self.cortex.get_chunk(ref_key),
                })
        return refs

    def _waypoint_count(self, col_key: str) -> int:
        """Count CuratedAtoms in a CurationCollection by walking seq_next chain."""
        count = 0
        visited = {col_key}
        cursor = col_key
        while True:
            nxt = self.cortex.get_adjacent_links(cursor, _REL_SEQ_NEXT)
            if not nxt:
                break
            nk = nxt[0][0]
            if nk in visited:
                break
            visited.add(nk)
            cursor = nk
            count += 1
        return count

    def _col_summary(self, col_key: str, position: int) -> Dict[str, Any]:
        """Return lightweight metadata for a CurationCollection (no waypoint bodies)."""
        m = self.cortex.get_meta(col_key) or {}
        aliases = self.cortex.get_aliases_by_key(col_key) or []
        alias = next((a for a in aliases if ":" in a), aliases[0] if aliases else None)
        return {
            "id":             col_key,
            "alias":          alias,
            "url_slug":       _url_slug(alias),
            "title":          m.get("title"),
            "concept":        m.get("concept"),
            "curator":        m.get("curator"),
            "created_at":     m.get("created_at"),
            "waypoint_count": self._waypoint_count(col_key),
            "position":       position,
        }

    def _compute_score(self, atom_id: str) -> Dict[str, Any]:
        """Compute ShelfScore components for a single atom.

        Falls back to sys:* link types when thesaurus:* links are absent so that
        atoms enriched at the system level still receive a meaningful score.
        """
        n_syn    = self._count_links_with_fallback(atom_id, _REL_SYNONYM,   "sys:synonym",   "sys:synonym_of")
        n_nsyn   = self._count_links(atom_id, _REL_NEAR_SYN)
        n_ant    = self._count_links_with_fallback(atom_id, _REL_ANTONYM,   "sys:antonym",   "sys:antonym_of", "sys:opposite_of")
        n_hyper  = self._count_links_with_fallback(atom_id, _REL_HYPERNYM,  "sys:is_a",      "sys:type_of")
        n_hypo   = self._count_links_with_fallback(atom_id, _REL_HYPONYM,   "sys:has_type",  "sys:includes")
        n_ex     = self._count_links(atom_id, _REL_EXAMPLE)
        n_aff    = self._count_links_with_fallback(atom_id, _REL_AFFECTIVE, "calc:associated_with", "calc:has_emotion")
        n_bridge = self._count_links_with_fallback(atom_id, _REL_NS_BRIDGE, "sys:mapped_to")
        n_ext    = self._count_links(atom_id, _REL_EXTERNAL)
        n_spec   = self._count_inbound_links(atom_id, "specializes")

        total_thesaurus = n_syn + n_nsyn + n_ant + n_hyper + n_hypo + n_ex + n_aff + n_bridge

        link_total           = _clamp(total_thesaurus / 8.0)
        synonym_coverage     = _clamp((n_syn + n_nsyn) / 3.0)
        antonym_presence     = _clamp(float(n_ant))
        example_density      = _clamp(n_ex / 2.0)
        affective_score      = _clamp(n_aff / 3.0)
        namespace_bridges    = _clamp(n_bridge / 2.0)
        external_refs        = _clamp(n_ext / 4.0)
        specialization_depth = _clamp(math.log10(1 + n_spec))

        chain_presence = _clamp((n_hyper + n_hypo) / 4.0)
        chain_total = n_hyper + n_hypo
        if chain_total == 0:
            balance_ratio = 0.0
        else:
            balance_ratio = 1.0 - abs(n_hyper - n_hypo) / chain_total
        chain_balance = chain_presence * (0.4 + 0.6 * balance_ratio)

        components = {
            "link_total":           link_total,
            "synonym_coverage":     synonym_coverage,
            "antonym_presence":     antonym_presence,
            "chain_balance":        chain_balance,
            "example_density":      example_density,
            "affective_score":      affective_score,
            "namespace_bridges":    namespace_bridges,
            "external_refs":        external_refs,
            "specialization_depth": specialization_depth,
        }

        shelf_score = sum(_SCORE_WEIGHTS[k] * v for k, v in components.items())

        return {
            "atom_id":     atom_id,
            "shelf_score": round(shelf_score, 4),
            "components":  {k: round(v, 4) for k, v in components.items()},
            "link_counts": {
                "synonym":              n_syn,
                "near_synonym":         n_nsyn,
                "antonym":              n_ant,
                "hypernym":             n_hyper,
                "hyponym":              n_hypo,
                "example_usage":        n_ex,
                "affective":            n_aff,
                "namespace_bridge":     n_bridge,
                "external_ref":         n_ext,
                "specializes_inbound":  n_spec,
            },
        }

    # ── Operators ─────────────────────────────────────────────────────────────

    def op_shelf_score(self, atom_id: Optional[str] = None,
                       name: Optional[str] = None) -> Dict[str, Any]:
        """[thesaurus.shelf.score] Compute ShelfScore for a single atom."""
        key = self._resolve_atom(atom_id, name)
        return self._compute_score(key)

    def op_shelf_list(self, limit: int = 20,
                      min_score: float = 0.0) -> Dict[str, Any]:
        """[thesaurus.shelf.list] List atoms ranked by ShelfScore."""
        limit = max(1, min(int(limit), 200))
        members = self.cortex.get_collection_members(_INDEX_SET) or []
        results = []
        allowed = getattr(self.session, "active_scopes", [])

        for key in members:
            if allowed and not self.cortex.check_access(key, allowed):
                continue
            scored = self._compute_score(key)
            if scored["shelf_score"] >= min_score:
                meta    = self.cortex.get_meta(key) or {}
                aliases = self.cortex.get_aliases_by_key(key) or []
                alias   = next((a for a in aliases if ":" in a),
                               aliases[0] if aliases else None)
                results.append({
                    **scored,
                    "content":  self.cortex.get_chunk(key),
                    "name":     meta.get("name") or meta.get("title"),
                    "alias":    alias,
                    "url_slug": _url_slug(alias),
                })

        results.sort(key=lambda r: r["shelf_score"], reverse=True)
        return {"atoms": results[:limit], "total_indexed": len(members)}

    def op_shelf_link(self, atom_id: Optional[str] = None,
                      name: Optional[str] = None,
                      target_id: Optional[str] = None,
                      target_name: Optional[str] = None,
                      rel: str = "",
                      weight: float = 1.0) -> Dict[str, Any]:
        """[thesaurus.shelf.link] Add a typed thesaurus link between two atoms.

        If either atom is not found (e.g. its ontology pack is not loaded),
        the link is silently skipped and the caller receives status='skipped'.
        """
        if not rel.startswith("thesaurus:"):
            raise ValueError(
                f"rel must start with 'thesaurus:'; got '{rel}'. "
                "See ontology/thesaurus/a_thesaurus_core.csl for valid types."
            )
        src = self._resolve_atom(atom_id, name, required=False)
        dst = self._resolve_atom(target_id, target_name, required=False)
        if src is None or dst is None:
            missing = (name or atom_id) if src is None else (target_name or target_id)
            return {"status": "skipped", "reason": f"atom not found: '{missing}'"}
        author = self._author()

        self.cortex.put_link(src, dst, rel, w=float(weight), author=author)

        self.cortex.create_set(_INDEX_SET)
        self.cortex.add_to_set(_INDEX_SET, src)
        self.cortex.add_to_set(_INDEX_SET, dst)

        return {"src": src, "dst": dst, "rel": rel, "weight": float(weight), "indexed": True}

    def op_shelf_link_ext(self, name: Optional[str] = None,
                          atom_id: Optional[str] = None,
                          url: str = "",
                          label: str = "") -> Dict[str, Any]:
        """[thesaurus.shelf.link_ext] Attach an external reference URL to an atom."""
        if not url:
            raise ValueError("'url' is required.")
        if not label:
            raise ValueError("'label' is required.")
        src = self._resolve_atom(atom_id, name)
        author = self._author()
        scopes = self._scopes()

        src_aliases = self.cortex.get_aliases_by_key(src) or []
        src_name = next((a for a in src_aliases if ":" in a), src)
        source_slug = src_name.replace(":", "-").replace(" ", "-").lower()
        label_slug  = label.lower().replace(" ", "-").replace("/", "-")
        ref_alias   = f"thesaurus:ext:{source_slug}:{label_slug}"

        existing_key = self.cortex.resolve_alias(ref_alias)
        if existing_key:
            ref_key = existing_key
        else:
            ref_key = self.cortex.put_chunk(
                content=url,
                meta={"type": "thesaurus:ExternalRef", "label": label, "url": url, "source": src_name},
                author=author,
                scopes=scopes,
            )
            self.cortex.set_alias(ref_key, ref_alias)

        self.cortex.put_link(src, ref_key, _REL_EXTERNAL, w=1.0, author=author)

        self.cortex.create_set(_INDEX_SET)
        self.cortex.add_to_set(_INDEX_SET, src)

        return {"src": src, "ref_alias": ref_alias, "label": label, "url": url}

    def op_curation_new(self, title: str,
                        concept: Optional[str] = None,
                        alias: Optional[str] = None) -> Dict[str, Any]:
        """[thesaurus.curation.new] Create a new CurationCollection atom."""
        if not title or not title.strip():
            raise ValueError("'title' is required.")
        author = self._author()
        scopes = self._scopes()

        meta: Dict[str, Any] = {
            "type":       "thesaurus:CurationCollection",
            "title":      title.strip(),
            "created_at": time.time(),
            "curator":    author,
        }
        if concept:
            meta["concept"] = concept

        collection_id = self.cortex.put_chunk(content=title.strip(), meta=meta,
                                              author=author, scopes=scopes)

        self.cortex.create_set(_CURATION_SET)
        self.cortex.add_to_set(_CURATION_SET, collection_id)

        if alias:
            self.cortex.set_alias(collection_id, alias)

        if concept:
            concept_alias = f"concept:word:{concept}"
            cw_key = self.cortex.resolve_alias(concept_alias)
            if not cw_key:
                cw_key = self.cortex.put_chunk(
                    content=concept,
                    meta={"type": "concept_word", "word": concept,
                          "concept_model": "thesaurus", "created_at": time.time()},
                    author=author, scopes=scopes,
                )
                self.cortex.set_alias(cw_key, concept_alias)
            self.cortex.put_link(collection_id, cw_key, "sys:derived_from", author=author)

        return {"collection_id": collection_id, "title": title.strip(),
                "alias": alias, "concept": concept}

    def op_curation_list(self) -> Dict[str, Any]:
        """[thesaurus.curation.ls] List all CurationCollections."""
        members = self.cortex.get_collection_members(_CURATION_SET) or []
        allowed = getattr(self.session, "active_scopes", [])
        results = []
        for key in members:
            if allowed and not self.cortex.check_access(key, allowed):
                continue
            meta = self.cortex.get_meta(key) or {}
            if meta.get("type") != "thesaurus:CurationCollection":
                continue
            content = self.cortex.get_chunk(key)
            results.append({
                "id":         key,
                "title":      meta.get("title") or content,
                "concept":    meta.get("concept"),
                "curator":    meta.get("curator"),
                "created_at": meta.get("created_at"),
            })
        results.sort(key=lambda r: r.get("created_at") or 0, reverse=True)
        return {"collections": results, "count": len(results)}

    def op_curation_atom(self, collection_id: str,
                         original_id: Optional[str] = None,
                         original_name: Optional[str] = None,
                         interpretation: str = "",
                         position: Optional[int] = None) -> Dict[str, Any]:
        """[thesaurus.curation.atom] Add a CuratedAtom to a CurationCollection."""
        if not collection_id:
            raise ValueError("'collection_id' is required.")
        resolved_col = self.cortex.resolve_alias(collection_id)
        col_key = resolved_col if resolved_col else collection_id

        original_key = self._resolve_atom(original_id, original_name)
        if not interpretation.strip():
            raise ValueError("'interpretation' must not be empty.")

        author = self._author()
        scopes = self._scopes()

        original_meta = self.cortex.get_meta(original_key) or {}
        curated_meta: Dict[str, Any] = {
            "type":          "thesaurus:CuratedAtom",
            "collection_id": col_key,
            "original_id":   original_key,
            "curator":       author,
            "created_at":    time.time(),
        }
        if position is not None:
            curated_meta["position"] = int(position)
        if original_meta.get("name"):
            curated_meta["original_name"] = original_meta["name"]

        curated_id = self.cortex.put_chunk(content=interpretation.strip(),
                                           meta=curated_meta, author=author, scopes=scopes)

        self.cortex.put_link(curated_id, original_key, _REL_INTERPRETS, author=author)
        self.cortex.put_link(curated_id, col_key, _REL_IN_CURATION, author=author)
        self.cortex.add_to_set(_CURATION_SET, curated_id)

        existing_seq = self.cortex.get_adjacent_links(col_key, _REL_SEQ_NEXT)
        if not existing_seq:
            self.cortex.put_link(col_key, curated_id, _REL_SEQ_NEXT, author=author)
        else:
            tail_id = col_key
            visited = {col_key}
            while True:
                next_links = self.cortex.get_adjacent_links(tail_id, _REL_SEQ_NEXT)
                if not next_links:
                    break
                candidate = next_links[0][0]
                if candidate in visited:
                    break
                visited.add(candidate)
                tail_id = candidate
            self.cortex.put_link(tail_id, curated_id, _REL_SEQ_NEXT, author=author)

        self.cortex.create_set(_INDEX_SET)
        self.cortex.add_to_set(_INDEX_SET, original_key)

        return {"curated_id": curated_id, "original_id": original_key,
                "collection_id": col_key, "interpretation": interpretation.strip()}

    # ── Exhibition Series ─────────────────────────────────────────────────────

    def op_series_new(self, title: str,
                      slug: Optional[str] = None,
                      alias: Optional[str] = None) -> Dict[str, Any]:
        """[thesaurus.series.new] Create a new ExhibitionSeries.

        Groups multiple CurationCollections under a themed series. The series
        maintains an ordered list of exhibitions; the last-added is the current
        (front-page) exhibition. Earlier entries are the archive.

        title — series display title (e.g. "Genealogy of the Dreamers")
        slug  — URL slug (e.g. "dreams-genealogy"); auto-derived from alias if omitted
        alias — canonical alias (e.g. "series:dreams-genealogy"); auto-built from slug

        Idempotent: if the alias already resolves to an ExhibitionSeries, returns it.
        """
        if not title or not title.strip():
            raise ValueError("'title' is required.")
        author = self._author()
        scopes = self._scopes()

        if not slug and alias:
            slug = alias.split(":", 1)[-1] if ":" in alias else alias
        if not slug:
            slug = title.lower().replace(" ", "-").replace("　", "-")[:40]
        canonical_alias = alias or f"series:{slug}"

        # Idempotency: return existing series if alias already registered
        existing_key = self.cortex.resolve_alias(canonical_alias)
        if existing_key:
            existing_meta = self.cortex.get_meta(existing_key) or {}
            if existing_meta.get("type") == "thesaurus:ExhibitionSeries":
                return {
                    "series_id":   existing_key,
                    "title":       existing_meta.get("title"),
                    "alias":       canonical_alias,
                    "slug":        existing_meta.get("slug"),
                    "url_slug":    existing_meta.get("slug"),
                    "exhibitions": existing_meta.get("exhibitions", []),
                    "existed":     True,
                }

        meta: Dict[str, Any] = {
            "type":        "thesaurus:ExhibitionSeries",
            "title":       title.strip(),
            "slug":        slug,
            "exhibitions": [],        # ordered list of CurationCollection keys
            "created_at":  time.time(),
            "curator":     author,
        }

        series_id = self.cortex.put_chunk(content=title.strip(), meta=meta,
                                          author=author, scopes=scopes)
        self.cortex.set_alias(series_id, canonical_alias)
        self.cortex.create_set(_SERIES_SET)
        self.cortex.add_to_set(_SERIES_SET, series_id)

        return {
            "series_id":   series_id,
            "title":       title.strip(),
            "alias":       canonical_alias,
            "slug":        slug,
            "url_slug":    slug,
            "exhibitions": [],
        }

    def op_series_list(self) -> Dict[str, Any]:
        """[thesaurus.series.ls] List all ExhibitionSeries."""
        members = self.cortex.get_collection_members(_SERIES_SET) or []
        allowed = getattr(self.session, "active_scopes", [])
        results = []
        for key in members:
            if allowed and not self.cortex.check_access(key, allowed):
                continue
            meta = self.cortex.get_meta(key) or {}
            if meta.get("type") != "thesaurus:ExhibitionSeries":
                continue
            exhibitions = meta.get("exhibitions") or []
            results.append({
                "id":               key,
                "title":            meta.get("title"),
                "slug":             meta.get("slug"),
                "url_slug":         meta.get("slug"),
                "curator":          meta.get("curator"),
                "created_at":       meta.get("created_at"),
                "exhibition_count": len(exhibitions),
            })
        results.sort(key=lambda r: r.get("created_at") or 0, reverse=True)
        return {"series": results, "count": len(results)}

    def op_series_add(self, series_id: Optional[str] = None,
                      alias: Optional[str] = None,
                      collection: Optional[str] = None,
                      collection_id: Optional[str] = None) -> Dict[str, Any]:
        """[thesaurus.series.add] Add a CurationCollection to an ExhibitionSeries.

        The new collection becomes the current (front-page) exhibition; all
        previously added collections become the archive. Appending the same
        collection twice is idempotent.

        series_id / alias      — ExhibitionSeries key or alias
        collection / collection_id — CurationCollection key or alias
        """
        id_str = alias or series_id
        if not id_str:
            raise ValueError("Provide 'series_id' or 'alias'.")
        resolved_series = self.cortex.resolve_alias(id_str)
        s_key = resolved_series if resolved_series else id_str

        s_meta = self.cortex.get_meta(s_key) or {}
        if s_meta.get("type") != "thesaurus:ExhibitionSeries":
            raise ValueError(f"'{id_str}' is not an ExhibitionSeries.")

        col_str = collection or collection_id
        if not col_str:
            raise ValueError("Provide 'collection' or 'collection_id'.")
        resolved_col = self.cortex.resolve_alias(col_str)
        c_key = resolved_col if resolved_col else col_str

        c_meta = self.cortex.get_meta(c_key) or {}
        if c_meta.get("type") != "thesaurus:CurationCollection":
            raise ValueError(f"'{col_str}' is not a CurationCollection.")

        author = self._author()

        # Idempotency: skip if already in exhibitions list
        exhibitions = s_meta.get("exhibitions") or []
        if c_key not in exhibitions:
            # add_meta appends to the list in the series atom's meta
            self.cortex.add_meta(s_key, "exhibitions", c_key)
            exhibitions = exhibitions + [c_key]

        # Ensure graph link exists (idempotent via UNIQUE constraint)
        self.cortex.put_link(c_key, s_key, _REL_IN_SERIES, w=1.0, author=author)

        position = exhibitions.index(c_key) + 1
        is_current = (exhibitions[-1] == c_key)

        col_aliases = self.cortex.get_aliases_by_key(c_key) or []
        col_alias = next((a for a in col_aliases if ":" in a), None)

        return {
            "series_id":       s_key,
            "collection_id":   c_key,
            "collection_alias": col_alias,
            "url_slug":        _url_slug(col_alias),
            "position":        position,
            "is_current":      is_current,
        }

    # ── View projections ──────────────────────────────────────────────────────

    def op_view_atom(self, name: Optional[str] = None,
                     atom_id: Optional[str] = None) -> Dict[str, Any]:
        """[thesaurus.view.atom] Full UI projection for a single atom."""
        key = self._resolve_atom(atom_id, name)
        score_data = self._compute_score(key)

        def linked_stubs(rel: str) -> List[Dict[str, Any]]:
            return [self._atom_stub(k)
                    for (k, _) in self.cortex.get_adjacent_links(key, rel)[:10]]

        def linked_stubs_multi(*rels) -> List[Dict[str, Any]]:
            seen: set = set()
            result: List[Dict[str, Any]] = []
            for rel in rels:
                for (k, _) in self.cortex.get_adjacent_links(key, rel)[:10]:
                    if k not in seen and k != key:
                        seen.add(k)
                        result.append(self._atom_stub(k))
                        if len(result) >= 10:
                            return result
            return result

        # Merge sys:* and thesaurus:* relations for richer sphere when thesaurus
        # links haven't been curated yet (common during initial ontology load).
        synonyms      = linked_stubs_multi(_REL_SYNONYM,   "sys:synonym",  "sys:synonym_of")
        antonyms      = linked_stubs_multi(_REL_ANTONYM,   "sys:antonym",  "sys:antonym_of", "sys:opposite_of")
        hypernyms     = linked_stubs_multi(_REL_HYPERNYM,  "sys:is_a",     "sys:type_of")
        hyponyms      = linked_stubs_multi(_REL_HYPONYM,   "sys:has_type", "sys:includes")
        ns_bridges    = linked_stubs_multi(_REL_NS_BRIDGE, "sys:mapped_to")

        # General associated atoms: outgoing + incoming links not already categorised
        all_linked_keys = {s["key"] for cat in (synonyms, antonyms, hypernyms, hyponyms, ns_bridges)
                           for s in cat}
        all_linked_keys.add(key)
        associated: List[Dict[str, Any]] = []
        for (k, _) in self.cortex.get_adjacent_links(key)[:30]:
            if k not in all_linked_keys:
                all_linked_keys.add(k)
                associated.append(self._atom_stub(k))
                if len(associated) >= 15:
                    break
        for (k, _) in self.cortex.get_incoming_links(key)[:20]:
            if k not in all_linked_keys:
                all_linked_keys.add(k)
                associated.append(self._atom_stub(k))
                if len(associated) >= 15:
                    break

        curation_entries: List[Dict[str, Any]] = []
        for (curated_id, _) in self.cortex.get_incoming_links(key, _REL_INTERPRETS):
            c_meta = self.cortex.get_meta(curated_id) or {}
            col_id = c_meta.get("collection_id")
            col_title = None
            if col_id:
                col_meta = self.cortex.get_meta(col_id) or {}
                col_title = col_meta.get("title")
            curation_entries.append({
                "curated_id":       curated_id,
                "collection_id":    col_id,
                "collection_title": col_title,
                "interpretation":   self.cortex.get_chunk(curated_id),
                "position":         c_meta.get("position"),
            })

        # All outgoing/incoming links for full atom view (graph neighbourhood).
        # Intentionally lightweight — alias only, no content fetch.
        def _link_stub(k: str, rel: str) -> Dict[str, Any]:
            aliases = self.cortex.get_aliases_by_key(k) or []
            name = next((a for a in aliases if ":" in a), aliases[0] if aliases else None)
            return {"key": k, "rel": rel, "name": name, "url_slug": _url_slug(name)}

        all_out = [_link_stub(k, rel) for k, rel in self.cortex.get_adjacent_links(key)[:15]]
        all_in  = [_link_stub(k, rel) for k, rel in self.cortex.get_incoming_links(key)[:15]]

        return {
            "type": "thesaurus:AtomView",
            "atom": self._atom_full(key),
            "shelf_score": score_data,
            "semantic_links": {
                "synonyms":          synonyms,
                "near_synonyms":     linked_stubs_multi(_REL_NEAR_SYN),
                "antonyms":          antonyms,
                "hypernyms":         hypernyms,
                "hyponyms":          hyponyms,
                "example_usage":     linked_stubs(_REL_EXAMPLE),
                "affective":         linked_stubs_multi(_REL_AFFECTIVE, "calc:associated_with", "calc:has_emotion"),
                "namespace_bridges": ns_bridges,
                "associated":        associated,
            },
            "all_links": {
                "outgoing": all_out,
                "incoming": all_in,
            },
            "external_refs": self._external_refs_for(key),
            "curations":     curation_entries,
        }

    def op_view_curation(self, collection_id: Optional[str] = None,
                         alias: Optional[str] = None) -> Dict[str, Any]:
        """[thesaurus.view.curation] Full UI projection for a CurationCollection."""
        id_str = alias or collection_id
        if not id_str:
            raise ValueError("Provide 'collection_id' or 'alias'.")
        resolved = self.cortex.resolve_alias(id_str)
        col_key = resolved if resolved else id_str

        col_meta = self.cortex.get_meta(col_key) or {}
        if col_meta.get("type") != "thesaurus:CurationCollection":
            raise ValueError(f"'{id_str}' is not a CurationCollection.")

        waypoints: List[Dict[str, Any]] = []
        visited = {col_key}
        cursor = col_key
        while True:
            next_links = self.cortex.get_adjacent_links(cursor, _REL_SEQ_NEXT)
            if not next_links:
                break
            next_key = next_links[0][0]
            if next_key in visited:
                break
            visited.add(next_key)
            cursor = next_key

            c_meta = self.cortex.get_meta(cursor) or {}
            original_key = c_meta.get("original_id")
            original_data: Dict[str, Any] = {}
            if original_key:
                original_data = {
                    **self._atom_stub(original_key),
                    "shelf_score":   self._compute_score(original_key)["shelf_score"],
                    "external_refs": self._external_refs_for(original_key),
                }

            waypoints.append({
                "position":       c_meta.get("position"),
                "curated_id":     cursor,
                "interpretation": self.cortex.get_chunk(cursor),
                "original":       original_data,
            })

        col_aliases = self.cortex.get_aliases_by_key(col_key) or []
        col_alias = next((a for a in col_aliases if ":" in a),
                         col_aliases[0] if col_aliases else None)

        return {
            "type": "thesaurus:CurationView",
            "collection": {
                "id":             col_key,
                "alias":          col_alias,
                "url_slug":       _url_slug(col_alias),
                "title":          col_meta.get("title"),
                "concept":        col_meta.get("concept"),
                "curator":        col_meta.get("curator"),
                "created_at":     col_meta.get("created_at"),
                "waypoint_count": len(waypoints),
            },
            "waypoints": waypoints,
        }

    def op_view_series(self, series_id: Optional[str] = None,
                       alias: Optional[str] = None) -> Dict[str, Any]:
        """[thesaurus.view.series] Full UI projection for an ExhibitionSeries.

        Returns series metadata, the current (latest) exhibition summary, and
        the archive list in reverse chronological order (most recently archived
        first). Each entry includes a url_slug for permanent URL construction.

        URL convention (frontend):
          current / series top: /series/{series.url_slug}
          individual permanent: /exhibition/{col.url_slug}

        series_id / alias — ExhibitionSeries key or alias
        """
        id_str = alias or series_id
        if not id_str:
            raise ValueError("Provide 'series_id' or 'alias'.")
        resolved = self.cortex.resolve_alias(id_str)
        s_key = resolved if resolved else id_str

        s_meta = self.cortex.get_meta(s_key) or {}
        if s_meta.get("type") != "thesaurus:ExhibitionSeries":
            raise ValueError(f"'{id_str}' is not an ExhibitionSeries.")

        exhibitions = s_meta.get("exhibitions") or []  # ordered, last = current

        s_aliases = self.cortex.get_aliases_by_key(s_key) or []
        s_alias = next((a for a in s_aliases if ":" in a),
                       s_aliases[0] if s_aliases else None)

        if not exhibitions:
            current_data = None
            archive_data = []
        else:
            current_data = self._col_summary(exhibitions[-1], len(exhibitions))
            archive_data = [
                self._col_summary(exhibitions[i], i + 1)
                for i in range(len(exhibitions) - 2, -1, -1)
            ]

        return {
            "type": "thesaurus:SeriesView",
            "series": {
                "id":               s_key,
                "alias":            s_alias,
                "url_slug":         s_meta.get("slug"),
                "title":            s_meta.get("title"),
                "curator":          s_meta.get("curator"),
                "created_at":       s_meta.get("created_at"),
                "exhibition_count": len(exhibitions),
            },
            "current": current_data,
            "archive": archive_data,
        }

