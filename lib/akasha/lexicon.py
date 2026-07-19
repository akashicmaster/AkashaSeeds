"""
Lexicon — first-class relations and namespaces (read-side mechanism).

Relations and namespaces in Akasha are short, cryptic strings (`thesaurus:related`,
`bio:allergen`, `emo:`, `dna:taste:`). They are hard for humans AND for the ontology
LLM to read, which breeds naming drift and meaning confusion. The fix is to make each
one a *defined* atom the ontology carries, and to surface that definition wherever the
short form appears.

This module is the READ side. The definitions themselves are ordinary ontology data
authored in `.ak` (see docs/for-llm/rel-definition-spec.md) — no new write path:

  reldef:<rel>   an atom whose CONTENT is the relation's full-spelling description,
                 a member of the `rels` set.        e.g. reldef:thesaurus:related
  nsdef:<ns>     an atom whose CONTENT is the namespace's description,
                 a member of the `namespaces` set.  e.g. nsdef:dna:taste
  <set> --rel:salient--> reldef:<rel>   declares that <rel> is a SALIENT relation for
                 members of the set, weight = priority (higher = more important). This
                 profile inherits down the sys:is_a / sys:part_of set hierarchy.

All reads union the caller's cell with the shared nucleus (definitions are universal),
and degrade gracefully: a missing definition simply yields None (the short form still
shows), never an error.
"""

from typing import Any, Dict, List, Optional

RELDEF_PREFIX = "reldef:"
NSDEF_PREFIX = "nsdef:"
RELS_SET = "rels"
NAMESPACES_SET = "namespaces"
SALIENT_REL = "rel:salient"

# Set names that are computational/structural, not conceptual categories — never a
# source of a salient-rel profile.
_SYS_SET_PREFIXES = ("leaf:", "ns:", "lang:", "scope:", "sys:", "set:", "ws:", "wf:",
                     "temp:", "chunk:", "pending:", "dont:", "ont:")


def _body(content: Optional[str]) -> Optional[str]:
    """Strip the `[alias]\\n` header that `def`/`w` prepend to an atom's stored content,
    returning just the human description body."""
    if content and content.startswith("[") and "\n" in content:
        return content.split("\n", 1)[1].strip() or None
    return content


def _adj(engine, key: str, rel_pattern: Optional[str] = None) -> List[Dict[str, Any]]:
    """Weighted outgoing links, unioned local cell + nucleus (dedup by dst+rel, max w)."""
    out = list(engine.core.get_adjacent_links(key, rel_pattern) or [])
    nucleus = getattr(engine, "_nucleus", None)
    if nucleus:
        seen = {(l["dst"], l["rel"]) for l in out}
        for l in (nucleus.core.get_adjacent_links(key, rel_pattern) or []):
            if (l["dst"], l["rel"]) not in seen:
                out.append(l); seen.add((l["dst"], l["rel"]))
    return out


def _collections_for(engine, key: str) -> List[str]:
    names = list(engine.core.get_collections_for_key(key) or [])
    nucleus = getattr(engine, "_nucleus", None)
    if nucleus:
        for n in (nucleus.core.get_collections_for_key(key) or []):
            if n not in names:
                names.append(n)
    return names


def _rel_of_reldef(engine, key: str) -> Optional[str]:
    """The relation string a `reldef:<rel>` atom stands for (from its alias), or its
    bare alias if the target is the rel proto-word itself."""
    aliases = engine.get_aliases_by_key(key) or []
    for a in aliases:
        if a.startswith(RELDEF_PREFIX):
            return a[len(RELDEF_PREFIX):]
    return aliases[0] if aliases else None


def rel_description(engine, rel: str) -> Optional[str]:
    """Full-spelling description registered for a relation, or None. Looks up the
    `reldef:<rel>` atom's content. `rel` is the exact relation string on the edge."""
    if not rel:
        return None
    key = engine.resolve_alias(f"{RELDEF_PREFIX}{rel}")
    if not key:
        return None
    return _body(engine.get_chunk(key)) or None


def namespace_description(engine, ns: str) -> Optional[str]:
    """Description registered for a namespace prefix, or None. `ns` is the namespace
    without the trailing colon (e.g. 'dna:taste', 'emo'). Tries progressively shorter
    prefixes so `dna:taste:sweet` resolves to `nsdef:dna:taste` then `nsdef:dna`."""
    if not ns:
        return None
    parts = ns.split(":")
    for i in range(len(parts), 0, -1):
        cand = ":".join(parts[:i])
        key = engine.resolve_alias(f"{NSDEF_PREFIX}{cand}")
        if key:
            desc = _body(engine.get_chunk(key))
            if desc:
                return desc
    return None


def namespace_of_alias(alias: Optional[str]) -> Optional[str]:
    """The namespace of a qualified alias ('dna:taste:sweet' -> 'dna:taste'); None for
    a bare word."""
    if not alias or ":" not in alias:
        return None
    return alias.rsplit(":", 1)[0]


def resolve_salient_rels(engine, atom_key: str, max_depth: int = 3) -> List[str]:
    """Ordered list of relations that are SALIENT for `atom_key` — the rels a reader
    most wants to see / a gap-finder most wants present. Sources, nearest-first:

      1. pinpoint `rel:salient` links on the atom (or its proto-word) itself,
      2. the `rel:salient` profile of every conceptual set the atom belongs to,
      3. inherited up the sys:is_a / sys:part_of hierarchy of those sets
         (ingredient's `varieties` flows down to fruit / herb / meat).

    Ordered by (hierarchy depth asc, edge weight desc); first occurrence of each rel
    wins. Returns the relation strings (e.g. ['varieties', 'rec:sweetness'])."""
    if not atom_key:
        return []

    # Seed nodes: the atom itself + the proto-word atom of every conceptual set it is in.
    seeds: List[str] = [atom_key]
    for name in _collections_for(engine, atom_key):
        if any(name.startswith(p) for p in _SYS_SET_PREFIXES):
            continue
        sk = engine.resolve_alias(name)
        if sk and sk not in seeds:
            seeds.append(sk)

    scored: List[tuple] = []          # (depth, -weight, rel)
    seen_rel: set = set()
    visited: set = set()
    frontier = [(s, 0) for s in seeds]
    while frontier:
        node, depth = frontier.pop(0)
        if node in visited or depth > max_depth:
            continue
        visited.add(node)
        # Collect this node's salient-rel declarations.
        for link in _adj(engine, node, SALIENT_REL):
            rel = _rel_of_reldef(engine, link["dst"])
            if rel and rel not in seen_rel:
                seen_rel.add(rel)
                scored.append((depth, -float(link.get("w", 1.0) or 1.0), rel))
        # Climb the set hierarchy (is_a / part_of) for inheritance.
        if depth < max_depth:
            for rel_pat in ("sys:is_a", "sys:part_of"):
                for link in _adj(engine, node, rel_pat):
                    if link["dst"] not in visited:
                        frontier.append((link["dst"], depth + 1))

    scored.sort(key=lambda t: (t[0], t[1]))
    return [rel for _, _, rel in scored]
