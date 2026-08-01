"""
DictionaryConcept — the base for reference-DICTIONARY domains (wine, cheese, ingredient …).

A dictionary domain is not a *formula*: its entities ALREADY exist as ontology atoms (loaded
universal in the thesaurus tier), each carrying a note, some axis links, and curated pairing
edges. There are no per-user instances and no bake — the concept reads the live graph. Every
such domain shares the SAME mechanism:

  • enumerate the entity atoms of a namespace
  • browse them by axis, reading the axis straight from typed links (not a duplicated set)
  • show one entity's profile (note + axis values + pairings)
  • follow curated `pairing:*` edges to a partner domain (the "sommelier" stance)

That mechanism lives here, once. A domain subclass declares a handful of class attributes and
skins the four operators with clear, domain-named methods (wine.pairs, cheese.pairs, …) — the
surface stays each concept's own; only the mechanism is shared. This is the dictionary analogue
of FormulaConcept (which is the base for *instance* domains like recipe / cocktail).

A subclass sets:
  NS            entity namespace, e.g. "wine" / "cheese"
  ENTITY_SET    OPTIONAL — a collection name whose members ARE the entities, used when the
                entities live in a SHARED namespace and are singled out by a set rather than
                owning a private one (small plates are `dish:*` atoms collected into
                `smallplate:all`, alongside every other base dish). When set, entity
                enumeration is that set's membership (scope-filtered); NS is still used to
                alias/resolve. When empty (the default), entities are a namespace scan.
  ENTITY_KINDS  sub-namespaces that are entities, e.g. ("varietal","region"); () = flat NS:<slug>
  AXIS_SPEC     {axis_name: (alias_template_with_{v}, rel)} — how each browse axis is read.
                The template may instead be a list of templates when one axis resolves over
                several namespaces (e.g. a cocktail base is spirit: / liqueur: / beverage:).
                axis_name becomes both the ls= parameter and the profile field, so it must
                avoid the reserved profile keys: id, key, name, note, kind, type, pairings
                (e.g. cheese's texture axis maps to the cheese:type:* namespace but is named
                `texture`, not `type`, which is the result envelope key).
  PAIR_RELS     the pairing relation names to follow
  PAIR_TARGET   default partner namespace for pairings ("" = any), e.g. cheese → "wine"

and calls the generic `_dict_search / _dict_ls / _dict_get / _dict_pairs` from thin op_* wrappers.
DictionaryConcept itself is abstract (no CONCEPT_PREFIX) so the registry never registers it.
"""
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.concepts.formula import FormulaConcept, _paginate, _slug


def _as_templates(template) -> Tuple[str, ...]:
    """An AXIS_SPEC template is one `alias_template_with_{v}`, OR a list/tuple of them when a
    single axis can resolve over several namespaces (e.g. a cocktail base is spirit: / liqueur: /
    beverage: / ing:). Normalise to a tuple."""
    return tuple(template) if isinstance(template, (list, tuple)) else (template,)


def _as_rels(rel) -> Tuple[str, ...]:
    """An AXIS_SPEC / group rel is one relation, OR a list/tuple of them when two datasets use
    different relations for the same axis (e.g. cocktail method is `cocktail:mixed` in the wine
    pack but `cocktail:method` in the TheCocktailDB pack). Normalise to a tuple."""
    return tuple(rel) if isinstance(rel, (list, tuple)) else (rel,)


# Cross-reference alias infixes — Wikidata unification aliases (dish:wd:Q…, whiskey:wd:Q…,
# cheese:wd:Q…) added by the importers alongside the human slug. They are alternate IDENTIFIERS,
# never an entity's display identity: a `<ns>:wd:<QID>` alias sits at the same colon-depth as a
# real entity slug, so without this guard the namespace scan lists the atom a SECOND time under
# its QID and a raw hash-like "Q1518444" surfaces as the name (a Display-principle violation). The
# alias itself is kept for lookup (spirit.get id=whiskey:wd:Q…) — only enumeration/display skip it.
_XREF_SEGMENTS = frozenset({"wd"})


def _is_xref_alias(alias: str) -> bool:
    parts = alias.split(":")
    return len(parts) >= 3 and parts[1] in _XREF_SEGMENTS


class DictionaryConcept(FormulaConcept):
    """Read-only multi-axis browse + pairing over pre-existing ontology entities."""

    SET_AXIS = "@set"          # AXIS_SPEC rel sentinel: the axis is a set, not a typed link

    NS: str = ""
    ENTITY_SET: str = ""                      # members ARE the entities (shared-namespace mode)
    ENTITY_KINDS: Tuple[str, ...] = ()
    ENTITY_DEPTH: Optional[int] = None        # colon count of an entity alias; None = derive
    KIND_FIELD: str = "kind"                  # profile field name for the 2nd segment
    ENTITY_EXCLUDE: frozenset = frozenset()   # NS:<slug> aliases that are vocab, not entities
    AXIS_SPEC: Dict[str, Tuple[str, str]] = {}
    PAIR_RELS: Tuple[str, ...] = ()
    PAIR_TARGET: str = ""

    # ── entity enumeration + axis reading (straight from the graph) ──────────────
    def _entities_from_set(self) -> List[Tuple[str, str]]:
        """Entities defined by membership of ENTITY_SET rather than a namespace scan — for a
        dictionary whose members live in a SHARED namespace (small plates are `dish:*` atoms
        singled out by the `smallplate:all` set, not a private namespace). Scope-filtered,
        aliased to this concept's namespace, de-duped and sorted.

        Bounded reads: the member keys come scope-filtered in one query (`member_keys_scoped`)
        and every member's aliases in one batched query (`get_aliases_for_keys`) — NOT a
        `_visible` + `_alias_of` pair per member, which is O(N) separate queries and, on a large
        superset (meal:all ≈ 2.3k, producer:all), stalls the cell under concurrent write load."""
        scopes = self._scopes()
        keys = self.cortex.member_keys_scoped(self.ENTITY_SET, scopes or None)
        amap = self.cortex.get_aliases_for_keys(keys)
        nss = self._ns_list()
        seen: Dict[str, str] = {}
        for mkey in keys:
            if mkey in seen:
                continue
            # pick the alias in this concept's namespace(s) — same selection as _alias_of,
            # skipping <ns>:wd:<QID> cross-refs so a raw QID never becomes the display name.
            alias = next((a for a in (amap.get(mkey) or [])
                          if any(a.startswith(f"{ns}:") for ns in nss)
                          and not _is_xref_alias(a)), "")
            if alias and alias not in self.ENTITY_EXCLUDE:
                seen[mkey] = alias
        return sorted((alias, key) for key, alias in seen.items())

    def _entity_aliases(self) -> List[Tuple[str, str]]:
        """Every entity atom of this dictionary as (alias, key), across cortex + nucleus,
        de-duped and sorted. When ENTITY_SET is declared, entities are that set's members
        (shared-namespace mode). Otherwise: kinded domains enumerate `NS:<kind>:<slug>` for
        each declared kind; flat domains enumerate `NS:<slug>`. Axis vocab (a deeper
        `NS:milk:*` etc.) is never an entity and is excluded by the exact colon-depth match."""
        if self.ENTITY_SET:
            return self._entities_from_set()
        prefixes = []
        for ns in self._ns_list():                       # a concept may span sibling namespaces
            prefixes += ([f"{ns}:{k}:" for k in self.ENTITY_KINDS]
                         if self.ENTITY_KINDS else [f"{ns}:"])
        cores = []
        cc = getattr(self.cortex, "core", None)
        if cc is not None:
            cores.append(cc)
        nc = getattr(getattr(self.session, "nucleus", None), "core", None)
        if nc is not None and nc is not cc:
            cores.append(nc)
        seen: Dict[str, str] = {}
        for prefix in prefixes:
            # exact depth of an entity alias: an explicit override (e.g. ingred:*:* with an
            # unlisted category) else the prefix's own colon count.
            want = self.ENTITY_DEPTH if self.ENTITY_DEPTH is not None else prefix.count(":")
            for core in cores:
                for row in (core.get_aliases_by_pattern(f"{prefix}%") or []):
                    alias, key = row.get("alias", ""), row.get("key", "")
                    if (key and alias.startswith(prefix) and alias.count(":") == want
                            and alias not in self.ENTITY_EXCLUDE
                            and not _is_xref_alias(alias)):     # skip <ns>:wd:<QID> cross-refs
                        seen.setdefault(alias, key)
        return sorted(seen.items())

    def _axis_members(self, axis_alias: str, rel: str) -> set:
        """The entity keys on the far side of an axis value. A LINK axis returns the entities
        linked INTO `axis_alias` by `rel` (e.g. cheeses `cheese:made_from cheese:milk:cow`); a
        SET axis (rel == SET_AXIS) returns the members of the collection named `axis_alias`
        (e.g. breweries in `brewery:in:germany`). Scope-filtered either way."""
        if rel == self.SET_AXIS:
            return set(self._members(axis_alias))
        key = self._resolve(axis_alias)
        if not key:
            return set()
        return {src for src, r in (self.cortex.get_incoming_links(key, rel) or [])
                if r == rel and self._visible(src)}

    def _ns_list(self) -> Tuple[str, ...]:
        """This concept's entity namespace(s). Usually one (`wine`), but a concept may span
        sibling namespaces (spirits = whiskey / rum / tequila) — the `type` axis then names the
        namespace an entity belongs to."""
        return tuple(self.NS) if isinstance(self.NS, (list, tuple)) else (self.NS,)

    def _multi_ns(self) -> bool:
        return len(self._ns_list()) > 1

    def _display(self) -> str:
        """Prefix for the result `type:` field and error messages: the single namespace as
        before, or the concept prefix for a multi-namespace concept (spirit vs whiskey/rum/…)."""
        if self._multi_ns():
            return getattr(self, "CONCEPT_PREFIX", "") or self._ns_list()[0]
        return self.NS

    def _alias_of(self, key: str, fallback: str = "") -> str:
        nss = self._ns_list()
        aliases = self.cortex.get_aliases_by_key(key) or []
        # prefer a canonical namespace alias; a <ns>:wd:<QID> cross-ref is only a last resort
        # (so `.get` shows "vat 69", never "Q1518444"), and even then only if nothing else fits.
        for a in aliases:
            if any(a.startswith(f"{ns}:") for ns in nss) and not _is_xref_alias(a):
                return a
        for a in aliases:
            if any(a.startswith(f"{ns}:") for ns in nss):
                return a
        return fallback

    def _profile(self, key: str, alias: str) -> Dict[str, Any]:
        """An entity's display profile: its note (chunk), its `kind` (for kinded domains), and
        each declared axis value resolved from the matching outgoing link."""
        prof: Dict[str, Any] = {
            "id": alias, "key": key,
            "name": alias.split(":")[-1].replace("_", " "),
            "note": (self.cortex.get_chunk(key) or "").strip(),
        }
        if self._multi_ns():
            prof[self.KIND_FIELD] = alias.split(":")[0]   # the namespace is the type
        elif (self.ENTITY_KINDS or self.ENTITY_DEPTH) and alias.count(":") >= 2:
            prof[self.KIND_FIELD] = alias.split(":")[1]
        adj = self.cortex.get_adjacent_links(key) or []
        for axis, (template, rel) in self.AXIS_SPEC.items():
            rels = _as_rels(rel)
            if self.SET_AXIS in rels:
                continue                                 # set axes aren't readable from links
            prefixes = [t.split("{v}")[0] for t in _as_templates(template)]
            value = ""
            for dst, r in adj:
                if r not in rels:
                    continue
                name = self._name(dst) or ""
                hit = next((p for p in prefixes if name.startswith(p)), None)
                if hit is not None:
                    value = name[len(hit):]
                    break
            prof[axis] = value
        return prof

    def _link_groups(self, key: str, groups: Tuple[Tuple[str, str, bool], ...]) -> Dict[str, Any]:
        """Collect an entity's outgoing links into named groups for a rich `get` card. `groups`
        is a tuple of (field, rel, is_list): a multi-valued field becomes a sorted, de-duped
        list of the targets' last path segment; a single-valued field becomes that segment (or
        ''). Used where an entity's payload is grouped relations (cocktail recipe, ingredient
        allergens/season) rather than one value per axis."""
        by_rel: Dict[str, List[str]] = {}
        for dst, rel in (self.cortex.get_adjacent_links(key) or []):
            name = self._name(dst) or ""
            by_rel.setdefault(rel, []).append(name.split(":")[-1] if name else dst)
        out: Dict[str, Any] = {}
        for field, rel, is_list in groups:
            vals = sorted({v for rr in _as_rels(rel) for v in by_rel.get(rr, [])})
            out[field] = vals if is_list else (vals[0] if vals else "")
        return out

    # ── generic operators (skinned by each subclass's op_* wrappers) ─────────────
    def _dict_search(self, query: str, limit: Any = "", offset: Any = 0,
                     cursor: Any = "") -> Dict[str, Any]:
        # Match on cheap fields, then profile ONLY the requested page. Profiling every match
        # (get_adjacent_links per atom) before paginating is O(N) graph reads — an empty-query
        # scan over a large dictionary (e.g. meal:all) would read the whole graph on one request
        # thread and can stall the cell under concurrent write load. With no query tokens we skip
        # the per-atom content read as well, so an empty scan is enumerate + sort + profile-a-page.
        toks = [t for t in _slug(query or "").split("_") if t]
        matches: List[Tuple[str, str, str]] = []          # (sort_name, alias, key)
        for alias, key in self._entity_aliases():
            name = alias.split(":")[-1]
            if toks:
                hay = name + " " + (self.cortex.get_chunk(key) or "").lower()
                if not all(t in hay for t in toks):
                    continue
            matches.append((name.replace("_", " ").lower(), alias, key))
        matches.sort(key=lambda m: m[0])
        page, nxt, more = _paginate(matches, self._page_limit(limit), cursor or offset)
        results = [self._profile(key, alias) for _, alias, key in page]
        return {"type": f"{self._display()}:search", "query": query, "results": results,
                "count": len(matches), "next_cursor": nxt, "has_more": more}

    def _dict_ls(self, filters: Dict[str, str], limit: Any = "", offset: Any = 0,
                 cursor: Any = "") -> Dict[str, Any]:
        ents = self._entity_aliases()
        alias_by_key = {key: alias for alias, key in ents}
        keyset = set(alias_by_key)
        kind = (filters.get("kind") or "").strip()
        if kind:
            if self._multi_ns():                          # the kind filter selects a namespace
                keyset = {k for a, k in ents if a.split(":")[0] == _slug(kind)}
            elif self.ENTITY_KINDS or self.ENTITY_DEPTH:
                keyset = {k for a, k in ents if a.startswith(f"{self.NS}:{_slug(kind)}:")}
        for axis, (template, rel) in self.AXIS_SPEC.items():
            v = (filters.get(axis) or "").strip()
            if v:
                members = set()
                for t in _as_templates(template):        # an axis may span >1 namespace …
                    for rr in _as_rels(rel):             # … and >1 relation (two datasets)
                        members |= self._axis_members(t.format(v=_slug(v)), rr)
                keyset &= members
        # profile ONLY the page, not every filtered key (see _dict_search — bounds read cost).
        matches = sorted((alias_by_key[k].split(":")[-1].replace("_", " ").lower(), k)
                         for k in keyset if k in alias_by_key)
        page, nxt, more = _paginate(matches, self._page_limit(limit), cursor or offset)
        results = [self._profile(k, alias_by_key[k]) for _, k in page]
        return {"type": f"{self._display()}:ls", "filters": {k: v for k, v in filters.items() if v},
                "results": results, "count": len(matches), "next_cursor": nxt, "has_more": more}

    def _dict_get(self, ref: str) -> Dict[str, Any]:
        ref = (ref or "").strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError(f"{self._display()}.get: no such {self._display()}.")
        prof = self._profile(key, self._alias_of(key, ref))
        prof["type"] = f"{self._display()}:profile"
        prof["pairings"] = self._pairings(key, self.PAIR_RELS,
                                          target_ns=self.PAIR_TARGET, limit=30)
        return prof

    def _dict_pairs(self, ref: str, target: str = "") -> Dict[str, Any]:
        ref = (ref or "").strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError(f"{self._display()}.pairs: no such {self._display()}.")
        tgt = (target or self.PAIR_TARGET or "").strip()
        pairs = self._pairings(key, self.PAIR_RELS, target_ns=tgt, limit=50)
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for p in pairs:
            ns = (p["name"] or "").split(":")[0] if ":" in (p["name"] or "") else "other"
            groups.setdefault(ns, []).append(p)
        return {"type": f"{self._display()}:pairs", "id": self._alias_of(key, ref), "target": tgt,
                "pairings": pairs, "by_namespace": groups, "count": len(pairs)}
