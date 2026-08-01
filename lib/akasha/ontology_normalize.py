"""
OntologyNormalizer — derives the canonical Product·Component·Method structure automatically
at every ontology ingestion, so no local per-pack rules accumulate and no user ever runs a
migration command by hand.

Given a read handle over the current graph (a list of backend `core`s — local cortex + nucleus),
it PLANS the canonical steps that are missing and returns them as ordinary loader step dicts
(`kernel.memory.define` / `kernel.memory.link` / `set.add`). The caller submits them through the
normal guarded write path (a JCL job at boot, or in-workspace at runtime). Every step is
idempotent (content-addressed atoms, first-wins alias, dedup links/sets), so re-running is safe.

What it derives (see lib/akasha/canon.py — the law):
  1. Role taxonomy + superset sets: every product/component/method entry `sys:is_a <domain>`
     and joins `<domain>:all`; each domain `sys:is_a role:{product,component,method}`.
  2. Method binding + mint-up: every recipe binds `sys:method_of` a product; the product entry
     is MINTED if absent (recipe ⊆ meal:all always), and joins `meal:all` + `meal:with_recipe`.
  3. Material canonicalization: product→component material links (thesaurus:related to a
     component, cocktail:base/uses) also get a canonical `sys:made_from` edge.

Steps 1–2 are derived from the alias table (cheap enumeration). Step 3 is a pure transform over
the link steps being ingested (available at boot from the global-relations scan, and at runtime
from the import's parsed links) — no per-atom graph reads.
"""
from typing import Any, Dict, List, Optional

from lib.akasha import canon


# Canonical normalization always writes to the shared ontology layer (universal), so minted
# products, role links, and superset sets are visible to every reader (incl. guests) — the same
# scope the ontology packs themselves load into.
def _def(alias: str, text: str) -> dict:
    return {"method": "kernel.memory.define",
            "params": {"name": alias, "description": text, "scope": "universal"}}


def _ln(src: str, dst: str, rel: str) -> dict:
    return {"method": "kernel.memory.link",
            "params": {"src": src, "dst": dst, "rel": rel, "scope": "universal"}}


def _setadd(name: str, atom: str) -> dict:
    return {"method": "set.add", "params": {"name": name, "id": atom, "scope": "universal"}}


class OntologyNormalizer:
    """Plan the canonical links/sets missing from the current graph. Read-only over `cores`;
    emits loader steps the caller writes."""

    def __init__(self, cores: List[Any]):
        # cores: backend objects exposing get_aliases_by_pattern / get_chunk (local + nucleus).
        self.cores = [c for c in cores if c is not None]

    # ── reads ────────────────────────────────────────────────────────────────────
    def _aliases(self, prefix: str, depth: int) -> Dict[str, str]:
        """alias → key for every atom whose alias starts with `prefix` at exactly `depth` colons,
        across all cores (de-duped, first core wins)."""
        out: Dict[str, str] = {}
        for core in self.cores:
            try:
                rows = core.get_aliases_by_pattern(f"{prefix}%") or []
            except Exception:
                rows = []
            for row in rows:
                a, k = row.get("alias", ""), row.get("key", "")
                if k and a.startswith(prefix) and a.count(":") == depth:
                    out.setdefault(a, k)
        return out

    def _chunk(self, key: str) -> str:
        for core in self.cores:
            try:
                c = core.get_chunk(key)
            except Exception:
                c = None
            if c:
                return c
        return ""

    def _name_head(self, key: str, fallback: str) -> str:
        """A short display name for a minted product, taken from the method atom's description
        head (before ' — ' / ' (' / '. '), else the slug humanised."""
        c = self._chunk(key).strip()
        for sep in (" — ", " (", ". "):
            if sep in c:
                c = c.split(sep, 1)[0].strip()
                break
        c = c.strip()
        return c[:80] if c else fallback

    def _members_of(self, cfg: dict) -> Dict[str, str]:
        """alias → key for every entity of a domain, across its member_ns (each a (prefix, depth)
        pair), minus the domain hubs."""
        out: Dict[str, str] = {}
        for prefix, depth in cfg.get("member_ns", ()):
            for alias, key in self._aliases(f"{prefix}:", depth).items():
                if alias not in canon.HUB_EXCLUDE:
                    out.setdefault(alias, key)
        return out

    # ── planning ───────────────────────────────────────────────────────────────
    def plan_roles(self) -> List[dict]:
        """Role taxonomy + superset membership. Every domain `sys:is_a` its role (and its parent
        super-product, if any); every entry `sys:is_a` its domain and joins the domain superset
        (and the parent's rollup + any method marker)."""
        steps: List[dict] = []
        for dom, cfg in canon.DOMAINS.items():
            steps.append(_ln(dom, cfg["role"], canon.IS_A))            # meal sys:is_a role:product
            if cfg.get("parent"):
                steps.append(_ln(dom, cfg["parent"], canon.IS_A))     # cocktail sys:is_a drink
            for alias in self._members_of(cfg):
                steps.append(_ln(alias, dom, canon.IS_A))
                steps.append(_setadd(cfg["all_set"], alias))
                if cfg.get("rollup_set"):
                    steps.append(_setadd(cfg["rollup_set"], alias))   # … also into drink:all
                if cfg.get("method_marker"):
                    steps.append(_setadd(cfg["method_marker"], alias))  # carries an inline method
        return steps

    def plan_methods(self) -> List[dict]:
        """Bind every method to a product (mint the product if missing → method ⊆ product),
        and mark the product as method-carrying."""
        steps: List[dict] = []
        for dom, cfg in canon.DOMAINS.items():
            if cfg["role"] != canon.ROLE_METHOD:
                continue
            pdom = cfg["method_of"]
            pcfg = canon.DOMAINS[pdom]
            pns = cfg["product_ns"]
            known = set(self._members_of(pcfg))                # existing product entries
            for malias, mkey in sorted(self._members_of(cfg).items()):
                slug = malias.split(":", 1)[1]
                palias = f"{pns}:{slug}"
                if palias not in known:
                    name = self._name_head(mkey, slug.replace("_", " "))
                    steps.append(_def(palias, name))            # mint the product entry
                    known.add(palias)
                steps.append(_ln(palias, pdom, canon.IS_A))
                steps.append(_setadd(pcfg["all_set"], palias))
                steps.append(_setadd(cfg["subset_set"], palias))
                steps.append(_ln(malias, palias, canon.METHOD_OF))
        return steps

    @staticmethod
    def canonicalize_links(link_steps: List[dict]) -> List[dict]:
        """Pure transform: for every product→component material link emit a canonical
        `sys:made_from` edge, and for every product→producer link a `sys:made_by` edge. No graph
        reads (works off the links being ingested)."""
        out: List[dict] = []
        for s in link_steps or []:
            p = s.get("params", {})
            src, dst, rel = p.get("src", ""), p.get("dst", ""), p.get("rel", "")
            if not src or not dst or rel in (canon.MADE_FROM, canon.MADE_BY):
                continue
            # made_from — cocktail/dish/recipe → component
            tgts = canon.MATERIAL_RELS.get(rel)
            if tgts and any(src.startswith(f"{ns}:") for ns in canon.PRODUCT_NS):
                if "*" in tgts or any(dst.startswith(f"{t}:") for t in tgts):
                    out.append(_ln(src, dst, canon.MADE_FROM))
            # made_by — product → producer
            ptgts = canon.PRODUCER_RELS.get(rel)
            if ptgts and ("*" in ptgts or any(dst.startswith(f"{t}:") for t in ptgts)):
                out.append(_ln(src, dst, canon.MADE_BY))
        return out

    def plan_lexeme(self) -> List[dict]:
        """Root the vocabulary: every proto-word that carries a sense (a target of `specializes`)
        is rolled up `sys:is_a lexeme`, so lemmas + their senses become a navigable field. This
        BACK-FILLS existing proto-words idempotently on load (new proto-words are rooted at
        creation in composite._ensure_protoword). No-op if the `lexeme` apex isn't present."""
        protos: set = set()
        for core in self.cores:
            fn = getattr(core, "distinct_link_dsts", None)
            if fn:
                try:
                    protos.update(fn("specializes"))
                except Exception:
                    pass
        return [_ln(pk, "lexeme", canon.IS_A) for pk in sorted(protos)]

    def plan(self, link_steps: Optional[List[dict]] = None) -> List[dict]:
        """The full canonical plan. Order matters: role/superset first (so products exist),
        then method binding (mint-up), material canonicalization, then vocabulary rooting."""
        return (self.plan_roles() + self.plan_methods()
                + self.canonicalize_links(link_steps or []) + self.plan_lexeme())
