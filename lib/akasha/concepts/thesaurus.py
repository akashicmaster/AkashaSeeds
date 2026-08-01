"""
Thesaurus Concept Model — a simple, glossary-oriented READ surface over the graph.

Three operators, all read, deliberately minimal (this is the preparation layer for
projecting concepts onto web concept pages):

  thesaurus.reference   Browse the concept catalogue as a glossary (alphabetical;
                        the ordering axis is extensible → language collation, era,
                        associative index — see `order=`).
  thesaurus.explore     Search for a target concept. Delegates to the SAME filter
                        core as the `explore` command (lib/akasha/discovery.py) —
                        no duplicated search logic.
  thesaurus.concept     Detail + related links for one concept. Built ON TOP of the
                        dive basic view (`consciousness.generate_view`, the same
                        core `dive`/`view` use) and extended with the thesaurus
                        responsibility: a writer's view — synonyms / antonyms /
                        broader / narrower / related, usage examples, and
                        external references — for investigating a word before using
                        it in prose.

No write operators, no ShelfScore, no curation/series machinery (all removed). The
`thesaurus:*` relations themselves live in ontology/thesaurus/a_thesaurus_core.csl
and are written by ontology load / Weaver; this model only reads them.
"""

import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept
from lib.akasha.discovery import discover_atoms

logger = logging.getLogger("Harmonia.Concept.Thesaurus")

# thesaurus:* relation strings (mirror ontology/thesaurus/a_thesaurus_core.csl).
# Read-only here — used to categorise a concept's links for the writer's view.
_REL_SYNONYM   = "thesaurus:synonym"
_REL_NEAR_SYN  = "thesaurus:near_synonym"
_REL_ANTONYM   = "thesaurus:antonym"
_REL_HYPERNYM  = "thesaurus:hypernym"     # broader
_REL_HYPONYM   = "thesaurus:hyponym"      # narrower
_REL_EXAMPLE   = "thesaurus:example_usage"
_REL_AFFECTIVE = "thesaurus:affective"
_REL_EXTERNAL  = "thesaurus:external_ref"

# Cross-ref aliases the importers attach to atoms (external-refs-derivation-spec):
#   <ns>:wd:Q<id>  Wikidata QID    <ns>:wc:<id>  Wikimedia Commons id (→ media:img:wc_<id>)
#   <ns>:wp:<title> Wikipedia title.  A `wd:` alias whose tail is NOT a QID (e.g.
# `cheese:wd:camembert`, an atom id) is ignored — only real Q-numbers become links.
_WD_ALIAS = re.compile(r"(?:^|:)wd:(Q\d+)$")
_WC_ALIAS = re.compile(r"(?:^|:)wc:(\w+)$")
_WP_ALIAS = re.compile(r"(?:^|:)wp:(.+)$")

# sys:* / calc:* fallbacks so a concept enriched only at the system level (common
# right after ontology load, before thesaurus:* curation) still shows related terms.
_SYN_RELS     = (_REL_SYNONYM, "sys:synonym", "sys:synonym_of")
_ANT_RELS     = (_REL_ANTONYM, "sys:antonym", "sys:antonym_of", "sys:opposite_of")
_BROADER_RELS = (_REL_HYPERNYM, "sys:is_a", "sys:type_of")
_NARROWER_RELS = (_REL_HYPONYM, "sys:has_type", "sys:includes")

_SYS_PREFIXES = ("sys:", "scope:", "leaf:", "ns:", "lang:", "temp:",
                 "ws:", "wf:", "set:", "thesaurus:ext:",
                 # value / machinery namespaces — not glossary concepts
                 "score:", "admin_scale:")

_ORDERS_IMPLEMENTED = ("alpha", "salience")   # order= values with a real comparator; others fall back to alpha

# Default cap on how many candidates the un-namespaced glossary scan visits per request.
# The full-graph "%" alias scan can surface tens of thousands of atoms; running the per-atom
# work (check_access / salience / description) over all of them is the O(N) stall the shelf hit.
# alpha fills the page from the alphabetically-sorted head, so it rarely approaches this; salience
# ranks the first `scan` candidates ("top-N over the first scan" — a visual shelf, per the spec).
_REFERENCE_SCAN_DEFAULT = 4000


def _term_of(alias: Optional[str]) -> Optional[str]:
    """The glossary headword of a qualified alias: its last colon-segment.
    "word:en:memory" → "memory"; "geo:country:jp" → "jp"; bare → itself."""
    if not alias:
        return None
    return alias.split(":")[-1] if ":" in alias else alias


class ThesaurusConcept(BaseConcept):
    """Glossary-oriented read model: reference (browse) · explore (search) · concept (detail)."""

    CONCEPT_PREFIX = "thesaurus"
    CONCEPT_LABEL  = "Glossary of concepts — browse, search, and read concept pages"

    CONCEPT_METHODS = {
        "reference": {
            "op":     "op_reference",
            "action": "read",
            "cli":    "th.reference",
            "args":   ["order"],
            "desc":   ("Glossary index of concepts: thesaurus reference "
                       "[order=alpha|salience] [ns=<prefix>] [initial=<letter>] [limit=N] [scan=N]"),
        },
        "explore": {
            "op":     "op_explore",
            "action": "read",
            "cli":    "th.explore",
            "args":   ["query"],
            "desc":   ("Look up concepts by name/namespace/type (glossary search): "
                       "thesaurus explore <query> [ns=<prefix>] [type=<t>] [limit=N]"),
        },
        "concept": {
            "op":     "op_concept",
            "action": "read",
            "cli":    "th.concept",
            "args":   ["name"],
            "desc":   ("Concept page — detail + writer's related links (synonyms, "
                       "broader/narrower, examples): thesaurus concept <name|id>"),
        },
    }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _scopes(self) -> List[str]:
        return getattr(self.session, "active_scopes", []) or []

    def _resolve_atom(self, atom_id: Optional[str], name: Optional[str]) -> str:
        """Return the internal key for atom_id (direct) or alias/word name (lookup)."""
        if atom_id:
            return atom_id
        if name:
            key = self.cortex.resolve_alias(name)
            if not key and ":" not in name:
                keys = self.cortex.list_leaf(name)      # bare word → leaf:<word>
                if keys:
                    key = keys[0]
            if not key:
                raise ValueError(f"Concept not found for '{name}'.")
            return key
        raise ValueError("Provide 'name' or 'atom_id'.")

    def _primary_alias(self, key: str) -> Optional[str]:
        aliases = self.cortex.get_aliases_by_key(key) or []
        return next((a for a in aliases if ":" in a), aliases[0] if aliases else None)

    def _salience(self, key: str) -> float:
        return round(float((self.cortex.get_meta(key) or {}).get("salience", 0.0) or 0.0), 4)

    def _clean_description(self, key: str) -> str:
        raw = self.cortex.get_chunk(key) or ""
        # Strip the "[alias]\n" hub prefix so the description reads cleanly.
        if raw.startswith("[") and "\n" in raw:
            raw = raw.split("\n", 1)[1]
        return raw.strip()

    def _stub(self, key: str) -> Dict[str, Any]:
        alias = self._primary_alias(key)
        return {"key": key, "name": alias, "term": _term_of(alias),
                "salience": self._salience(key)}

    def _related_by(self, key: str, rels) -> List[Dict[str, Any]]:
        """Stubs for the first-matching relation family (primary, then fallbacks)."""
        seen: set = set()
        out: List[Dict[str, Any]] = []
        for rel in rels:
            for (dst, _w) in self.cortex.get_adjacent_links(key, rel)[:12]:
                if dst != key and dst not in seen:
                    seen.add(dst)
                    out.append(self._stub(dst))
            if out:                                     # first family that yields anything wins
                break
        return out

    # ── Operators ─────────────────────────────────────────────────────────────

    def op_reference(self, order: str = "alpha", ns: str = "",
                     initial: str = "", limit: int = 200, scan: Any = "") -> Dict[str, Any]:
        """[thesaurus.reference] Glossary index of concepts.

        Enumerates named concepts (qualified aliases, system prefixes excluded) and
        orders them for browsing. `order='alpha'` (default) sorts by headword;
        `order='salience'` ranks by salience (descending) — the "top concepts by score"
        shelf feed. Other axes (`era`, `assoc`, `lang:<code>`) are reserved and fall back
        to alpha (`order_applied` says which ran). `ns=` scopes to one namespace; `initial=`
        keeps only headwords starting with that letter (glossary letter-jump); `scan=`
        caps how many candidates the full-graph scan visits (default 4000).

        Bounded reads: the enumerate + filter + sort is done on the cheap headword string
        with NO per-atom graph reads; the expensive per-atom work (check_access, salience,
        description) runs ONLY while filling the returned page — so an un-namespaced "%"
        scan over the whole graph stays sub-second (same principle as the F1 dictionary fix).
        """
        limit = max(1, min(int(limit), 1000))
        try:
            scan_cap = int(scan) if str(scan).strip() else _REFERENCE_SCAN_DEFAULT
        except (TypeError, ValueError):
            scan_cap = _REFERENCE_SCAN_DEFAULT
        scan_cap = max(limit, min(scan_cap, 50000))

        pattern = f"{ns}:%" if ns else "%"
        rows = self.cortex.get_aliases_by_pattern(pattern) or []
        nucleus = getattr(self.session, "nucleus", None)
        if nucleus:
            seen_alias = {(r["key"], r.get("alias")) for r in rows}
            for r in (nucleus.core.get_aliases_by_pattern(pattern) or []):
                if (r["key"], r.get("alias")) not in seen_alias:
                    rows.append(r)

        scopes = self._scopes()
        initial_lc = initial.lower() if initial else ""
        # ── Phase 1: CHEAP candidate build — headword string ops only, NO graph reads.
        # Enumerate, apply the glossary filters, and keep the best (first qualified) alias
        # per atom. Deferring check_access / salience / description to the page (Phase 2) is
        # what bounds the full-graph scan; doing them here would be O(N) reads (the shelf stall).
        cand: Dict[str, str] = {}                       # key -> best headword alias
        for r in rows:
            alias = r.get("alias") or ""
            key = r.get("key")
            if not key or not alias:
                continue
            if not ns and alias.startswith(_SYS_PREFIXES):
                continue                                # glossary excludes machinery aliases
            term = _term_of(alias) or ""
            if not term:
                continue
            # A glossary of concepts is a word list: keep headwords that begin with a
            # letter (any script — Latin, CJK, accented), and drop the proto-word noise
            # that otherwise floods the '#' bucket — bare numbers ("0.05", "1,220"),
            # scores, and punctuation fragments ("'s", "+1", "/cbt", "--jonathan").
            # Only in the default (unscoped) browse; an explicit ns= stays unfiltered
            # so a power user can still enumerate a numeric/symbol namespace.
            if not ns and not term[:1].isalpha():
                continue
            if initial_lc and not term.lower().startswith(initial_lc):
                continue
            # First qualified (colon) alias per atom wins as its headword.
            prev = cand.get(key)
            if prev is None or (":" in alias and ":" not in prev):
                cand[key] = alias
        candidates = [((_term_of(a) or ""), a, k) for k, a in cand.items()]

        order_applied = order if order in _ORDERS_IMPLEMENTED else "alpha"

        def _visible(key: str) -> bool:
            return (not scopes) or self.cortex.check_access(key, scopes)

        def _row(term: str, alias: str, key: str, salience: float = None) -> Dict[str, Any]:
            return {
                "key":         key,
                "name":        alias,
                "term":        term,
                "initial":     term[:1].upper(),
                "description": self._clean_description(key),
                "salience":    self._salience(key) if salience is None else salience,
            }

        # ── Phase 2: order + fill the page (per-atom reads bounded here).
        if order_applied == "salience":
            # Rank by salience descending over the first `scan_cap` visible candidates —
            # "top-N over the first scan candidates", acceptable for a visual shelf.
            scored = []
            for term, alias, key in candidates[:scan_cap]:
                if not _visible(key):
                    continue
                scored.append((self._salience(key), term, alias, key))
            scored.sort(key=lambda t: (-t[0], t[1].casefold(), t[1]))
            page = [_row(term, alias, key, salience=s) for s, term, alias, key in scored[:limit]]
        else:
            # alpha: true alphabetical head. Sort cheaply, then walk in order filling the
            # page with visible atoms only — check_access + profile run for ~limit atoms
            # (plus any denied ones skipped), never the whole candidate set.
            candidates.sort(key=lambda c: (c[0].casefold(), c[0]))
            page = []
            walked = 0
            for term, alias, key in candidates:
                walked += 1
                if not _visible(key):
                    if walked >= scan_cap and not page:
                        break                           # pathological deny-all guard
                    continue
                page.append(_row(term, alias, key))
                if len(page) >= limit:
                    break

        return {
            "order":         order,
            "order_applied": order_applied,
            "concepts":      page,
            # `entries` mirrors `concepts` for the archives projection normaliser.
            "entries":       page,
            # candidate count after the cheap glossary filters (pre-visibility); for the
            # public glossary this equals the visible concept count.
            "total":         len(candidates),
        }

    def op_explore(self, query: str = "", ns: str = "",
                   type: str = "", limit: int = 20) -> Dict[str, Any]:
        """[thesaurus.explore] Search for a target concept.

        Delegates to the shared filter-search core (lib/akasha/discovery.py) — the
        very same code behind the `explore` command — so there is one search
        implementation. `query` is a name/alias pattern (`%`/`_` wildcards allowed);
        `ns=` restricts by namespace, `type=` by meta type. Each match carries its
        meaning-density `salience` for ranking on the glossary side.
        """
        query = (query or "").strip()
        if not (query or ns or type):
            raise ValueError("thesaurus.explore requires 'query' (or ns= / type=).")
        limit = max(1, min(int(limit), 100))
        nucleus = getattr(self.session, "nucleus", None)
        # Public glossary: no group-private merge (group_engines=[]).
        rows = discover_atoms(self.cortex, nucleus, [], self._scopes(),
                              ns=ns, atom_type=type, pat=query, limit=limit)
        matches = [{
            "key":      r["key"],
            "name":     r["alias"],
            "term":     _term_of(r["alias"]),
            "preview":  r["preview"],
            "color":    r["color"],
            "salience": self._salience(r["key"]),
        } for r in rows]
        matches.sort(key=lambda m: m["salience"], reverse=True)
        # `results` mirrors `matches` for the archives projection layer, whose
        # list normaliser reads atoms/results/entries (archives.py:_to_space_entries).
        return {"query": query, "matches": matches, "results": matches,
                "count": len(matches)}

    def _collect_external_refs(self, key: str) -> List[Dict[str, Any]]:
        """Every external reference reachable from a concept — the SINGLE surface that unifies
        the two historically-separate reference systems so a URL is always present:

          • curated refs      `thesaurus:external_ref` → atom(meta.type="thesaurus:ExternalRef",
                              meta.url)
          • fetched web refs  a Wikipedia/web auto-fetch writes the enriching atom with
                              meta.type="fetch:<source>" (+ meta.url/title, provenance=external)
                              and a `ref:web` URL exit-atom; either shape is recognised here.

        Any atom in the concept's 1-hop neighbourhood (out or in, any relation) that carries a
        URL as a web reference is included, normalised to {label, url, source}, deduped by URL.
        Read-only and migration-free — it surfaces already-fetched references without touching
        the write path. `source` lets the client distinguish a curated ref from a fetched one."""
        refs: Dict[str, Dict[str, Any]] = {}      # url → ref (first-wins, dedupe by url)

        def add(label: str, url: str, source: str) -> None:
            url = (url or "").strip()
            if url and url not in refs:
                refs[url] = {"label": (label or url).strip(), "url": url, "source": source}

        # 1) curated external references (the original op_concept behaviour).
        for (dst, _w) in self.cortex.get_adjacent_links(key, _REL_EXTERNAL):
            m = self.cortex.get_meta(dst) or {}
            if m.get("type") == "thesaurus:ExternalRef":
                add(m.get("label", ""), m.get("url") or self.cortex.get_chunk(dst), "curated")

        # 2) fetched web references anywhere in the 1-hop neighbourhood (any relation).
        for getter in (self.cortex.get_adjacent_links, self.cortex.get_incoming_links):
            for (nbr, _rel) in (getter(key) or [])[:40]:
                m = self.cortex.get_meta(nbr) or {}
                t = str(m.get("type", ""))
                url = m.get("url")
                if not url:
                    continue
                if t == "ref:web":
                    add(m.get("title", ""), url, "web")
                elif t.startswith("fetch:") or m.get("provenance") == "external":
                    add(m.get("title", ""), url, m.get("source") or "web")

        # 3) DERIVED refs (external-refs-derivation-spec): read the importers' cross-ref
        #    aliases + the linked media atom, so an atom's external identity always has a
        #    URL. Deterministic, offline, read-only — writes nothing; add() dedupes by URL
        #    so the curated refs above already win. No new namespace/relation is introduced.
        aliases = self.cortex.get_aliases_by_key(key) or []

        def _emit_media(media_key: str) -> None:
            # media:img:* atoms store the image URL as their CONTENT (not meta.url), so
            # step 2 misses them — resolve the atom and read its content directly.
            content = (self.cortex.get_chunk(media_key) or "").strip()
            if not content.startswith("http"):
                return
            malias = next((a for a in (self.cortex.get_aliases_by_key(media_key) or [])
                           if a.startswith("media:img:")), "")
            label = (malias.rsplit(":", 1)[-1] if malias
                     else urllib.parse.unquote(content.rsplit("/", 1)[-1])) or "image"
            add(label, content, "commons")

        for al in aliases:
            m_wd = _WD_ALIAS.search(al)
            if m_wd:
                qid = m_wd.group(1)
                add(qid, f"https://www.wikidata.org/wiki/{qid}", "wikidata")
                continue
            m_wp = _WP_ALIAS.search(al)
            if m_wp:
                title = m_wp.group(1)
                add(title.replace("_", " "),
                    "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title, safe=""),
                    "wikipedia")

        # Image: prefer the explicit media link (`media:*` relation → media:img:* atom);
        # fall back to resolving the `<ns>:wc:<id>` cross-ref to `media:img:wc_<id>`.
        media_seen = False
        for (nbr, rel) in (self.cortex.get_adjacent_links(key) or []):
            if str(rel).startswith("media:"):
                _emit_media(nbr)
                media_seen = True
        if not media_seen:
            for al in aliases:
                m_wc = _WC_ALIAS.search(al)
                if m_wc:
                    mk = self.cortex.resolve_alias(f"media:img:wc_{m_wc.group(1)}")
                    if mk:
                        _emit_media(mk)

        # If THIS atom is itself a media:img:* image, surface its own URL as a source badge.
        if any(a.startswith("media:img:") for a in aliases):
            _emit_media(key)

        return list(refs.values())

    def op_concept(self, name: Optional[str] = None,
                   atom_id: Optional[str] = None) -> Dict[str, Any]:
        """[thesaurus.concept] Concept page: dive basic view + writer's related links.

        The base is the SAME dive view the `dive`/`view` commands produce
        (`consciousness.generate_view`: focus, signposts, resonance, cosmos_nd) —
        reused, not reimplemented. On top of it this adds the thesaurus
        responsibility, aimed at writing: the word's synonyms / antonyms /
        broader / narrower terms, usage examples, and external references —
        everything needed to investigate a concept word before putting it in prose.
        """
        key = self._resolve_atom(atom_id, name)
        scopes = self._scopes()

        consciousness = getattr(self.session, "consciousness", None)
        base: Dict[str, Any] = {}
        if consciousness is not None:
            view = consciousness.generate_view(key, allowed_scopes=scopes)
            if isinstance(view, dict) and "error" in view:
                raise ValueError(view["error"])
            focus = view.get("focus", {}) if isinstance(view, dict) else {}
            base = {
                "signposts": view.get("signposts", []),
                "resonance": view.get("resonance", []),
                "cosmos_nd": focus.get("cosmos_nd"),
            }

        # Writer's view — categorise the concept's links.
        examples = [{"text": self.cortex.get_chunk(dst) or "", "key": dst}
                    for (dst, _w) in self.cortex.get_adjacent_links(key, _REL_EXAMPLE)[:12]]

        external_refs = self._collect_external_refs(key)

        # Everything else linked (out + in), flat, for the "related" cloud —
        # deduped against the categorised buckets above.
        categorised = {_REL_EXAMPLE, _REL_EXTERNAL, *_SYN_RELS, *_ANT_RELS,
                       *_BROADER_RELS, *_NARROWER_RELS}
        related: List[Dict[str, Any]] = []
        seen = {key}
        for dir_, getter in (("out", self.cortex.get_adjacent_links),
                             ("in", self.cortex.get_incoming_links)):
            for (dst, rel) in getter(key)[:30]:
                if dst in seen or rel in categorised:
                    continue
                seen.add(dst)
                stub = self._stub(dst)
                stub["rel"] = rel
                stub["dir"] = dir_
                related.append(stub)
                if len(related) >= 20:
                    break

        alias = self._primary_alias(key)
        synonyms = self._related_by(key, _SYN_RELS)
        antonyms = self._related_by(key, _ANT_RELS)
        broader  = self._related_by(key, _BROADER_RELS)
        narrower = self._related_by(key, _NARROWER_RELS)
        return {
            "type": "thesaurus:concept",
            "atom": {
                "key":         key,
                "name":        alias,
                "term":        _term_of(alias),
                "description": self._clean_description(key),
                "aliases":     self.cortex.get_aliases_by_key(key) or [],
                "meta":        self.cortex.get_meta(key) or {},
            },
            "salience": self._salience(key),
            # Writer's thesaurus view
            "synonyms": synonyms,
            "antonyms": antonyms,
            "broader":  broader,
            "narrower": narrower,
            "related":  related,
            "examples": examples,
            "external_refs": external_refs,
            # Archives-projection compatibility: the same related stubs, grouped
            # under the containers archives.op_space reads (semantic_links / all_links)
            # to build its "related → space" transitions.
            "semantic_links": {
                "synonyms": synonyms, "antonyms": antonyms,
                "broader":  broader,  "narrower": narrower,
            },
            "all_links": {
                "outgoing": [r for r in related if r.get("dir") == "out"],
                "incoming": [r for r in related if r.get("dir") == "in"],
            },
            # Dive basic view (reused from generate_view)
            **base,
        }
