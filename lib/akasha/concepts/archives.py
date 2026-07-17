"""
Archives Concept Model — the concept warehouse's projection & navigation layer.

Not a digital archive of *things* but a warehouse of *concepts*: it stores the
whole atom space and gives it structure and traversal. This model is GUI-FREE —
every operator returns plain JSON describing what to show and where each element
leads (`target`); a web GUI projects that and does nothing but render. All page
composition and transitions live here, not in the HTML.

Element concepts (each an operator):

  index      — the index of portals: the whole portal structure, hierarchically
               organised. Transitions to each portal.
  portal     — a category entry point (a "room" / "page"): basically a list of
               links, but its STYLE is set by what concept model it projects —
               `links` (bare list), `map` (a map as the doorway), `curation` (a
               narrative doorway). The projection changes the look; the portal's
               role — a doorway into concept spaces — does not.
  space      — a concept space: the detail of a single concept (an "exhibit" /
               "card" / "page"). Projects ONE thesaurus concept. Reached from a
               portal, from explore, or from reference.
  explore    — the search portal: keyword + filters. Projects the thesaurus
               model's explore; its results transition to concept spaces.
  reference  — projects the thesaurus model's reference (the organised list);
               its entries transition to concept spaces.

Projection seam: `space`/`explore`/`reference` delegate to the thesaurus model.
They prefer the redefined API (`thesaurus.concept` / `.explore` / `.reference`)
and fall back to today's methods (`view.atom` / a local scan / `shelf.list`) so
this model works before the backend redefinition lands and swaps automatically
after. `portal` with projection `map`/`curation` delegates to those models.

Data model:
  Portal atom   meta.type = "archives:portal"
                meta: {title, slug, category, projection, projection_ref,
                       parent, order, description}
                alias  "archives:portal:<slug>"
                scope  scope:sys:universal  (public — guests browse the archive)
  Portal entry  portal --archives:entry--> concept atom   (weight = order)
  Index set     set:archives:portals
"""
import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Archives")

_PORTAL_SET   = "set:archives:portals"
_REL_ENTRY    = "archives:entry"
_PORTAL_TYPE  = "archives:portal"
_PUBLIC_SCOPE = "scope:sys:universal"

_PROJECTIONS = ("links", "map", "curation")


def _slugify(text: str) -> str:
    out = []
    for ch in (text or "").strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "　"):
            out.append("-")
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:64] or "portal"


class ArchivesConcept(BaseConcept):
    """The concept warehouse: portals, concept spaces, explore, reference, index."""

    CONCEPT_PREFIX = "archives"
    CONCEPT_LABEL  = "concept warehouse: portals, spaces, explore, reference, index"

    CONCEPT_METHODS = {
        "index":       {"op": "op_index",       "action": "read"},
        "portal":      {"op": "op_portal",      "action": "read"},
        "space":       {"op": "op_space",       "action": "read"},
        "explore":     {"op": "op_explore",     "action": "read"},
        "reference":   {"op": "op_reference",   "action": "read"},
        "portal.new":  {"op": "op_portal_new",  "action": "write"},
        "portal.set":  {"op": "op_portal_set",  "action": "write"},
        "portal.add":  {"op": "op_portal_add",  "action": "write"},
    }

    # ── helpers ────────────────────────────────────────────────────────────────

    def _author(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _portal_scopes(self) -> List[str]:
        # Public-readable structure + an owner marker for provenance.
        return [_PUBLIC_SCOPE, f"owner:user_{self._author()}"]

    @staticmethod
    def _target(kind: str, ref: Optional[str]) -> Dict[str, Any]:
        """Where an element leads. The GUI maps kind→route (space→/a/<ref>,
        portal→/portal/<ref>, explore→/explore, reference→/reference)."""
        return {"kind": kind, "ref": ref}

    def _visible(self, key: str) -> bool:
        allowed = getattr(self.session, "active_scopes", [])
        if not allowed:
            return True                      # internal / unscoped context
        return self.cortex.check_access(key, allowed)

    def _primary_alias(self, key: str) -> Optional[str]:
        aliases = self.cortex.get_aliases_by_key(key) or []
        return next((a for a in aliases if ":" in a), aliases[0] if aliases else None)

    def _slug_of(self, alias: Optional[str]) -> Optional[str]:
        if not alias:
            return None
        return alias.split(":")[-1] if ":" in alias else alias

    def _resolve_portal(self, slug: Optional[str], portal_id: Optional[str]) -> Optional[str]:
        if portal_id:
            return portal_id
        if not slug:
            return None
        # accept a bare slug or a full alias
        alias = slug if slug.startswith("archives:portal:") else f"archives:portal:{slug}"
        return self.cortex.resolve_alias(alias) or self.cortex.resolve_alias(slug)

    def _portal_meta(self, key: str) -> Dict[str, Any]:
        m = self.cortex.get_meta(key) or {}
        return m

    def _portal_public(self, key: str, m: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id":            key,
            "slug":          m.get("slug"),
            "title":         m.get("title"),
            "category":      m.get("category"),
            "projection":    m.get("projection", "links"),
            "projection_ref": m.get("projection_ref") or "",
            "parent":        m.get("parent") or "",
            "order":         m.get("order", 0),
            "description":   m.get("description") or self.cortex.get_chunk(key),
        }

    # ── thesaurus projection seam (forward-compatible) ─────────────────────────

    def _thesaurus(self):
        from lib.akasha.concepts.thesaurus import ThesaurusConcept
        return ThesaurusConcept(self.session)

    def _project_concept(self, name: Optional[str], atom_id: Optional[str]) -> Dict[str, Any]:
        t = self._thesaurus()
        if hasattr(t, "op_concept"):
            return t.op_concept(name=name, atom_id=atom_id)   # redefined API
        return t.op_view_atom(name=name, atom_id=atom_id)     # today

    def _project_reference(self, limit: int) -> Dict[str, Any]:
        t = self._thesaurus()
        if hasattr(t, "op_reference"):
            return t.op_reference(limit=limit)
        return t.op_shelf_list(limit=limit)

    def _project_explore(self, query: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        t = self._thesaurus()
        if hasattr(t, "op_explore"):
            return t.op_explore(query=query, **(filters or {}))
        return self._explore_fallback(query, int((filters or {}).get("limit", 30)))

    def _explore_fallback(self, query: str, limit: int, scan: int = 500) -> Dict[str, Any]:
        """Minimal keyword match over the thesaurus index until thesaurus.explore
        lands: substring over aliases (bounded scan — no full graph walk)."""
        q = (query or "").strip().lower()
        members = self.cortex.get_collection_members("set:thesaurus:index") or []
        results = []
        for key in members[:scan]:
            if not self._visible(key):
                continue
            alias = self._primary_alias(key)
            hay = (alias or "") + " " + (self.cortex.get_chunk(key) or "")
            if q and q not in hay.lower():
                continue
            results.append({"atom_id": key, "alias": alias, "url_slug": self._slug_of(alias)})
            if len(results) >= limit:
                break
        return {"type": "thesaurus:explore", "query": query, "results": results,
                "backing": "archives.fallback"}

    def _to_space_entries(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalise whatever a thesaurus list-shaped payload returns into
        space-targeted entries, tolerant of both the current and redefined APIs."""
        rows = (payload.get("atoms") or payload.get("results")
                or payload.get("entries") or [])
        entries = []
        for r in rows:
            alias = r.get("alias") or r.get("name")
            slug  = r.get("url_slug") or self._slug_of(alias) or alias
            entries.append({
                "ref":     alias or r.get("atom_id"),
                "title":   r.get("name") or r.get("title") or slug,
                "slug":    slug,
                "salience": r.get("salience"),
                "target":  self._target("space", alias or r.get("atom_id")),
            })
        return entries

    # ── read operators ─────────────────────────────────────────────────────────

    def op_index(self) -> Dict[str, Any]:
        """[archives.index] The portal index: the whole portal structure,
        hierarchically organised. Each node transitions to a portal."""
        members = self.cortex.get_collection_members(_PORTAL_SET) or []
        nodes: Dict[str, Dict[str, Any]] = {}
        for key in members:
            if not self._visible(key):
                continue
            m = self._portal_meta(key)
            if m.get("type") != _PORTAL_TYPE:
                continue
            slug = m.get("slug")
            if not slug:
                continue
            nodes[slug] = {
                "slug":     slug,
                "title":    m.get("title"),
                "category": m.get("category"),
                "projection": m.get("projection", "links"),
                "order":    m.get("order", 0),
                "parent":   m.get("parent") or "",
                "target":   self._target("portal", slug),
                "children": [],
            }
        roots: List[Dict[str, Any]] = []
        for slug, node in nodes.items():
            parent = node["parent"]
            if parent and parent in nodes:
                nodes[parent]["children"].append(node)
            else:
                roots.append(node)
        _sort = lambda lst: lst.sort(key=lambda n: (n.get("order", 0), n.get("title") or ""))
        _sort(roots)
        for node in nodes.values():
            _sort(node["children"])
        return {"type": "archives:index", "portals": roots, "count": len(nodes)}

    def op_portal(self, slug: Optional[str] = None,
                  portal_id: Optional[str] = None,
                  limit: int = 60) -> Dict[str, Any]:
        """[archives.portal] A portal (category doorway). Returns its projection
        style and entries (each transitions to a concept space), plus any child
        portals. `links` lists the atoms added to it; `map`/`curation` delegate to
        those models for a spatial / narrative doorway — same doorway concept,
        different style."""
        key = self._resolve_portal(slug, portal_id)
        if not key or self._portal_meta(key).get("type") != _PORTAL_TYPE:
            raise ValueError(f"Portal not found: {slug or portal_id}")
        if not self._visible(key):
            raise ValueError("Portal not accessible.")
        m = self._portal_meta(key)
        projection = m.get("projection", "links")
        entries = self._portal_entries(key, m, projection, limit)

        # Child portals (sub-rooms), from the index hierarchy.
        my_slug = m.get("slug")
        subportals = []
        for pk in self.cortex.get_collection_members(_PORTAL_SET) or []:
            pm = self._portal_meta(pk)
            if pm.get("type") == _PORTAL_TYPE and pm.get("parent") == my_slug and self._visible(pk):
                subportals.append({
                    "slug": pm.get("slug"), "title": pm.get("title"),
                    "order": pm.get("order", 0),
                    "target": self._target("portal", pm.get("slug")),
                })
        subportals.sort(key=lambda n: (n.get("order", 0), n.get("title") or ""))

        return {
            "type":       "archives:portal",
            "portal":     self._portal_public(key, m),
            "projection": projection,
            "entries":    entries,
            "subportals": subportals,
        }

    def _portal_entries(self, key: str, m: Dict[str, Any],
                        projection: str, limit: int) -> List[Dict[str, Any]]:
        if projection == "map":
            projected = self._project_portal_map(m.get("projection_ref"))
            if projected is not None:
                return projected
        elif projection == "curation":
            projected = self._project_portal_curation(m.get("projection_ref"))
            if projected is not None:
                return projected
        # links (default) — and the graceful fallback for map/curation.
        entries = []
        links = self.cortex.get_adjacent_links(key, _REL_ENTRY) or []
        # order by link weight when available (list rows are [dst, rel] or [dst, rel, w])
        rows = []
        for row in links:
            dst = row[0]
            w = row[2] if len(row) > 2 else 0
            rows.append((dst, w))
        rows.sort(key=lambda t: t[1])
        for dst, _w in rows[:limit]:
            if not self._visible(dst):
                continue
            alias = self._primary_alias(dst)
            slug = self._slug_of(alias)
            entries.append({
                "ref":    alias or dst,
                "title":  slug or alias or dst,
                "slug":   slug,
                "target": self._target("space", alias or dst),
            })
        return entries

    def _project_portal_map(self, ref: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        """Project a `map` model instance as the doorway (spatial entries)."""
        if not ref:
            return None
        try:
            from lib.akasha.concepts.map import MapConcept
        except Exception:
            return None
        try:
            mc = MapConcept(self.session)
            for opname in ("op_view", "op_render", "op_get", "op_map"):
                if hasattr(mc, opname):
                    data = getattr(mc, opname)(**self._ref_kwargs(mc, ref))
                    return self._map_to_entries(data)
        except Exception as exc:
            logger.debug("[archives] map projection failed: %s", exc)
        return None

    def _project_portal_curation(self, ref: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        """Project a curation (exhibition) as the doorway (narrative entries)."""
        if not ref:
            return None
        try:
            t = self._thesaurus()
            if hasattr(t, "op_view_curation"):
                data = t.op_view_curation(alias=ref)
                entries = []
                for wp in data.get("waypoints", []):
                    orig = wp.get("original") or {}
                    alias = orig.get("name") or orig.get("url_slug")
                    entries.append({
                        "ref":            alias,
                        "title":          orig.get("url_slug") or alias,
                        "slug":           orig.get("url_slug") or self._slug_of(alias),
                        "interpretation": wp.get("interpretation"),
                        "position":       wp.get("position"),
                        "target":         self._target("space", alias),
                    })
                return entries
        except Exception as exc:
            logger.debug("[archives] curation projection failed: %s", exc)
        return None

    @staticmethod
    def _ref_kwargs(model, ref: str) -> Dict[str, Any]:
        # Best-effort: pass the ref under the arg names map ops commonly accept.
        return {"alias": ref} if ref and ":" in ref else {"map_id": ref}

    def _map_to_entries(self, data: Any) -> List[Dict[str, Any]]:
        nodes = []
        if isinstance(data, dict):
            nodes = data.get("nodes") or data.get("points") or data.get("atoms") or []
        entries = []
        for n in nodes:
            alias = n.get("alias") or n.get("name")
            entries.append({
                "ref":   alias or n.get("key"),
                "title": n.get("label") or self._slug_of(alias) or alias,
                "slug":  n.get("url_slug") or self._slug_of(alias),
                "x":     n.get("x"), "y": n.get("y"),
                "target": self._target("space", alias or n.get("key")),
            })
        return entries

    def op_space(self, name: Optional[str] = None,
                 atom_id: Optional[str] = None) -> Dict[str, Any]:
        """[archives.space] A concept space: the detail of one concept, projected
        from the thesaurus model, with related links (each transitions to another
        space) and back-navigation to the portals that contain it."""
        if not name and not atom_id:
            raise ValueError("Provide 'name' or 'atom_id'.")
        concept = self._project_concept(name, atom_id)

        # Related links → space targets (tolerant of both API shapes).
        related: List[Dict[str, Any]] = []
        seen = set()
        if isinstance(concept, dict):
            own = (concept.get("atom") or {}).get("name")
            if own:
                seen.add(own)                     # never link a concept to itself
        sem = (concept.get("semantic_links") or {}) if isinstance(concept, dict) else {}
        all_links = (concept.get("all_links") or {}) if isinstance(concept, dict) else {}
        buckets = list(sem.values()) + [all_links.get("outgoing", []), all_links.get("incoming", [])]
        _skip_prefix = ("set:", "scope:", "archives:portal:", "ws:", "wf:")
        for bucket in buckets:
            for stub in (bucket or []):
                alias = stub.get("name")
                if not alias or alias in seen:
                    continue
                if alias.startswith(_skip_prefix):
                    continue          # sets / scopes / portals are not concept spaces
                seen.add(alias)
                related.append({
                    "ref":    alias,
                    "title":  stub.get("url_slug") or self._slug_of(alias),
                    "slug":   stub.get("url_slug") or self._slug_of(alias),
                    "rel":    stub.get("rel"),
                    "target": self._target("space", alias),
                })

        # Back-nav: portals that list this concept.
        atom_key = None
        if isinstance(concept, dict):
            atom_key = (concept.get("atom") or {}).get("key")
        portals = []
        if atom_key:
            for (src, _rel) in self.cortex.get_incoming_links(atom_key, _REL_ENTRY) or []:
                pm = self._portal_meta(src)
                if pm.get("type") == _PORTAL_TYPE and self._visible(src):
                    portals.append({"slug": pm.get("slug"), "title": pm.get("title"),
                                    "target": self._target("portal", pm.get("slug"))})

        return {
            "type":    "archives:space",
            "concept": concept,
            "related": related,
            "portals": portals,
        }

    def op_explore(self, query: str = "", limit: int = 30,
                   ns: str = "", type: str = "") -> Dict[str, Any]:
        """[archives.explore] The search portal: projects the thesaurus explore.
        Results transition to concept spaces. (Explicit filter params — the
        thesaurus-side filter set will grow as its explore API is defined.)"""
        filters = {"limit": limit}
        if ns:
            filters["ns"] = ns
        if type:
            filters["type"] = type
        raw = self._project_explore(query, filters)
        return {
            "type":    "archives:explore",
            "query":   query,
            "filters": {k: v for k, v in filters.items() if k != "limit"},
            "entries": self._to_space_entries(raw),
            "backing": raw.get("backing", "thesaurus"),
        }

    def op_reference(self, limit: int = 100) -> Dict[str, Any]:
        """[archives.reference] Projects the thesaurus reference (organised list).
        Entries transition to concept spaces."""
        raw = self._project_reference(limit)
        return {
            "type":     "archives:reference",
            "entries":  self._to_space_entries(raw),
            "total":    raw.get("total_indexed") or raw.get("total"),
        }

    # ── write operators (build the warehouse structure) ────────────────────────

    def op_portal_new(self, title: str,
                      slug: Optional[str] = None,
                      category: str = "",
                      projection: str = "links",
                      projection_ref: str = "",
                      parent: str = "",
                      order: int = 0,
                      description: str = "") -> Dict[str, Any]:
        """[archives.portal.new] Create (or return) a portal. Idempotent by slug."""
        if not title or not title.strip():
            raise ValueError("'title' is required.")
        if projection not in _PROJECTIONS:
            raise ValueError(f"projection must be one of {_PROJECTIONS}.")
        slug = _slugify(slug or title)
        alias = f"archives:portal:{slug}"

        existing = self.cortex.resolve_alias(alias)
        if existing:
            m = self._portal_meta(existing)
            if m.get("type") == _PORTAL_TYPE:
                return {"portal_id": existing, "slug": slug, "alias": alias, "existed": True}

        meta = {
            "type":        _PORTAL_TYPE,
            "title":       title.strip(),
            "slug":        slug,
            "category":    category,
            "projection":  projection,
            "projection_ref": projection_ref,
            "parent":      parent,
            "order":       int(order),
            "description": description,
            "created_at":  time.time(),
            "curator":     self._author(),
        }
        key = self.cortex.put_chunk(content=description or title.strip(), meta=meta,
                                    author=self._author(), scopes=self._portal_scopes())
        self.cortex.set_alias(key, alias)
        self.cortex.create_set(_PORTAL_SET)
        self.cortex.add_to_set(_PORTAL_SET, key)
        return {"portal_id": key, "slug": slug, "alias": alias,
                "projection": projection, "existed": False}

    def op_portal_set(self, slug: Optional[str] = None,
                      portal_id: Optional[str] = None,
                      projection: Optional[str] = None,
                      projection_ref: Optional[str] = None,
                      parent: Optional[str] = None,
                      order: Optional[int] = None,
                      title: Optional[str] = None,
                      category: Optional[str] = None,
                      description: Optional[str] = None) -> Dict[str, Any]:
        """[archives.portal.set] Update a portal's projection / parent / order /
        title / category / projection_ref / description (only the fields given).

        Explicit params (not **kwargs): the kernel's concept dispatch passes only
        params that match the op's declared signature."""
        key = self._resolve_portal(slug, portal_id)
        if not key or self._portal_meta(key).get("type") != _PORTAL_TYPE:
            raise ValueError(f"Portal not found: {slug or portal_id}")
        if projection is not None and projection not in _PROJECTIONS:
            raise ValueError(f"projection must be one of {_PROJECTIONS}.")
        fields = {
            "projection": projection, "projection_ref": projection_ref,
            "parent": parent, "order": order, "title": title,
            "category": category, "description": description,
        }
        updated = {}
        for k, v in fields.items():
            if v is None:
                continue
            if k == "order":
                v = int(v)
            self.cortex.set_meta(key, k, v)
            updated[k] = v
        return {"portal_id": key, "updated": updated}

    def op_portal_add(self, slug: Optional[str] = None,
                      portal_id: Optional[str] = None,
                      concept: Optional[str] = None,
                      concept_id: Optional[str] = None,
                      order: int = 0) -> Dict[str, Any]:
        """[archives.portal.add] Add a concept as an entry of a portal (links
        projection). `order` becomes the link weight so entries can be sequenced."""
        key = self._resolve_portal(slug, portal_id)
        if not key or self._portal_meta(key).get("type") != _PORTAL_TYPE:
            raise ValueError(f"Portal not found: {slug or portal_id}")
        target = concept_id or (self.cortex.resolve_alias(concept) if concept else None)
        if not target:
            return {"status": "skipped", "reason": f"concept not found: {concept or concept_id}"}
        self.cortex.put_link(key, target, _REL_ENTRY, w=float(order), author=self._author())
        return {"portal_id": key, "concept_id": target, "order": order, "linked": True}
