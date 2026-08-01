"""
Producer Concept Model — the DICTIONARY over the drinks producers (生産者).

`producer` is the PRODUCER role in the canonical Product·Component·Method·Producer upper ontology
(lib/akasha/canon.py). A producer makes a drink but is NOT itself a drink — a distillery is not
drunk — so producers live in their own dictionary (`producer:all`), never in `drink:all`. The two
kinds share one shape (an entity, the incoming `sys:made_by` from the products it makes):

  whiskey:distillery:<slug> / rum:distillery:<slug> / tequila:distillery:<slug>   (a distillery)
  brewery:<slug>                                                                  (a brewery)

Three READ operators (producers have no components/method of their own — they are the far side of
`made_by`, so there is no pairs/nutrition operator):

  producer.search   name/keyword lookup across distilleries + breweries
  producer.ls       browse by kind — distillery | brewery
  producer.get      a producer's profile — its kind and the drinks it makes (incoming made_by)

`spirit.*` / `brewery.*` remain the per-namespace surfaces; `producer.*` is the union, and the
counterpart of `drink.*` on the other side of `sys:made_by`.
"""
import logging
from typing import Any, Dict, List

from lib.akasha.concepts.dictionary import DictionaryConcept
from lib.akasha import canon

logger = logging.getLogger("Harmonia.Concept.Producer")


class ProducerConcept(DictionaryConcept):
    """Dictionary over the drinks producers — distilleries and breweries — browsable by kind,
    each showing the drinks it makes."""

    CONCEPT_PREFIX = "producer"
    CONCEPT_LABEL  = "producer dictionary — distilleries and breweries, and the drinks they make"
    NOUN   = "producer"
    ID_KEY = "producer_id"
    AXES   = ()

    NS         = ("brewery", "whiskey", "rum", "tequila")   # namespaces producers live in
    ENTITY_SET = "producer:all"        # the canonical producer superset (built by the normalizer)
    AXIS_SPEC = {
        # kind value → its sub-superset (distillery → producer:distillery, brewery → brewery:all)
        # both are membership sets the normalizer/packs maintain; see _kind for the mapping.
    }

    # namespace → producer kind.
    _KIND = {"brewery": "brewery", "whiskey": "distillery",
             "rum": "distillery", "tequila": "distillery"}

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "producer.search", "args": ["q"],
                   "desc": "Search producers by name/keyword: producer search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "producer.ls", "args": [],
                   "desc": "Browse producers by kind: producer ls [kind=distillery|brewery]"},
        "get":    {"op": "op_get", "action": "read", "cli": "producer.get", "args": ["id"],
                   "desc": ("Producer profile — kind and the drinks it makes: "
                            "producer get id=whiskey:distillery:<slug>")},
    }

    def _kind(self, alias: str) -> str:
        return self._KIND.get(alias.split(":", 1)[0], "producer")

    def _makes(self, key: str) -> List[str]:
        """The drinks this producer makes — the incoming `sys:made_by` edges (scope-filtered)."""
        out = set()
        for src, rel in (self.cortex.get_incoming_links(key, canon.MADE_BY) or []):
            if rel == canon.MADE_BY and self._visible(src):
                nm = self._name(src) or ""
                out.add(nm.split(":", 1)[1] if ":" in nm else nm)
        return sorted(out)

    def _profile(self, key: str, alias: str) -> Dict[str, Any]:
        prof = super()._profile(key, alias)
        prof["kind"] = self._kind(alias)
        return prof

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[producer.search] Find producers whose name or description contains every query token.
        READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, kind: str = "", limit: Any = "", offset: Any = 0,
              cursor: Any = "") -> Dict[str, Any]:
        """[producer.ls] Browse producers by `kind` — distillery | brewery. READ-level;
        paginated (default 20, max 100)."""
        ents = self._entity_aliases()
        want = (kind or "").strip().lower()
        # Filter + sort on the CHEAP alias (kind is derived from the namespace prefix — no graph
        # read); profile ONLY the page. Profiling every match before paginating is O(N) graph
        # reads (see dictionary._dict_ls) and stalls the cell on a large producer:all.
        matches = sorted((a.split(":")[-1].replace("_", " ").lower(), a, k)
                         for a, k in ents if not want or self._kind(a) == want)
        from lib.akasha.concepts.formula import _paginate
        page, nxt, more = _paginate(matches, self._page_limit(limit), cursor or offset)
        results = [self._profile(k, a) for _, a, k in page]
        return {"type": "producer:ls", "filters": {"kind": want} if want else {},
                "results": results, "count": len(matches), "next_cursor": nxt, "has_more": more}

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[producer.get] A producer's profile — its kind (distillery/brewery) and the drinks it
        makes (the incoming made_by). READ-level."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError("producer.get: no such producer.")
        prof = self._profile(key, self._alias_of(key, ref))
        prof["type"] = "producer:profile"
        prof["makes"] = self._makes(key)
        return prof
