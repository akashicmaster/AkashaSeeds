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

# sys:* / calc:* fallbacks so a concept enriched only at the system level (common
# right after ontology load, before thesaurus:* curation) still shows related terms.
_SYN_RELS     = (_REL_SYNONYM, "sys:synonym", "sys:synonym_of")
_ANT_RELS     = (_REL_ANTONYM, "sys:antonym", "sys:antonym_of", "sys:opposite_of")
_BROADER_RELS = (_REL_HYPERNYM, "sys:is_a", "sys:type_of")
_NARROWER_RELS = (_REL_HYPONYM, "sys:has_type", "sys:includes")

_SYS_PREFIXES = ("sys:", "scope:", "leaf:", "ns:", "lang:", "temp:",
                 "ws:", "wf:", "set:", "thesaurus:ext:")

_ORDERS_IMPLEMENTED = ("alpha",)   # order= values with a real comparator; others fall back to alpha


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
            "desc":   ("Glossary index of concepts, alphabetical: "
                       "thesaurus reference [order=alpha] [ns=<prefix>] [initial=<letter>] [limit=N]"),
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
                     initial: str = "", limit: int = 200) -> Dict[str, Any]:
        """[thesaurus.reference] Glossary index of concepts.

        Enumerates named concepts (qualified aliases, system prefixes excluded) and
        orders them for browsing. `order='alpha'` (default) sorts by headword. The
        ordering axis is intentionally open — `lang:<code>` (locale collation),
        `era` (chronological), and `assoc` (associative index) are recognised and
        reserved; until each has a real comparator they fall back to alphabetical
        (`order_applied` says which ran). `ns=` scopes to one namespace; `initial=`
        keeps only headwords starting with that letter (glossary letter-jump).
        """
        limit = max(1, min(int(limit), 1000))
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
        by_key: Dict[str, Dict[str, Any]] = {}
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
            if initial_lc and not term.lower().startswith(initial_lc):
                continue
            if scopes and not self.cortex.check_access(key, scopes):
                continue
            # First qualified alias per atom wins as its headword.
            if key not in by_key or (":" in alias and ":" not in (by_key[key]["name"] or "")):
                by_key[key] = {
                    "key":         key,
                    "name":        alias,
                    "term":        term,
                    "initial":     term[:1].upper(),
                    "description": self._clean_description(key),
                    "salience":    self._salience(key),
                }

        concepts = list(by_key.values())
        order_applied = order if order in _ORDERS_IMPLEMENTED else "alpha"
        # alpha (and, for now, every reserved axis) sorts by casefolded headword.
        concepts.sort(key=lambda c: (c["term"].casefold(), c["term"]))
        page = concepts[:limit]

        return {
            "order":         order,
            "order_applied": order_applied,
            "concepts":      page,
            # `entries` mirrors `concepts` for the archives projection normaliser.
            "entries":       page,
            "total":         len(concepts),
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

        external_refs = []
        for (dst, _w) in self.cortex.get_adjacent_links(key, _REL_EXTERNAL):
            m = self.cortex.get_meta(dst) or {}
            if m.get("type") == "thesaurus:ExternalRef":
                external_refs.append({"label": m.get("label", ""),
                                      "url": m.get("url") or self.cortex.get_chunk(dst)})

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
