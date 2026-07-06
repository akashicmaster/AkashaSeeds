"""
ref: Cognitive Primitives — Akasha's innate reference vocabulary.

These atoms are seeded into the nucleus before any .ak ontology loading.
They form the minimum reference/relational vocabulary that Akasha knows
innately — equivalent in status to pure logic (and, or, not) and emotions.

Unlike user-defined link relations, ref: primitives carry fixed directional
semantics that are part of Akasha's DNA: they are never overridable by .ak
files, and because they are official system atoms, any mis-linking of them
is auditable.

The three tiers:
  1. Interrogative / relational axes (ref:who, ref:where, ref:why, ...)
       → typed context slot dimensions; back the $who/$where/$why session vars
  2. Deictic pointers (ref:this, ref:that, ref:here, ref:there, ref:now, ref:then)
       → proximity axes; context-relative pointing
  3. Causal / logical connectives (ref:because, ref:therefore, ref:if, ...)
       → FIXED directional semantics (see below); foundational causal logic

Extension into CSL job graphs and control flow:
  The same ref: primitives that structure semantic knowledge also provide the
  control-flow vocabulary for CSL jobs and Harmonia workflows — without any
  additional DSL.  Execution conditions, dependency ordering, and branching
  are all expressible as Atom links:

    ref:if        → gate: job executes only when condition Atom is true
    ref:because   → dependency: this job requires that predecessor
    ref:therefore → trigger: this job fires that successor
    ref:and / ref:or / ref:not → compose conditions

  This is homoiconicity at the graph level — analogous to Lisp's "code is
  data".  A set of Atoms carrying ref: links is simultaneously:
    - a knowledge representation (semantic ontology)
    - a job definition (when granted scope:job:executable by Harmonia)
    - a simulation model / control loop (when leaf Atoms are bound to
      sensor/actuator hardware via get_chunk_raw / put_chunk_raw overrides)

  The distinction between "this is knowledge" and "this is runnable code"
  is entirely in the permission layer — the graph structure is unchanged.
  See base.py (AkashaBackend) for the sensor/actuator binding contract.

Causal direction is FIXED and never user-redefinable:
  ref:because   A  ←──  B    "A because B"   (B is the cause, A is the effect)
  ref:therefore A  ──→  B    "A therefore B" (A causes or entails B)

Session variables $who / $where / $why / $when / $how / $what / $which
are typed anaphoric slots backed by these primitives; see resolver.py.
To set a slot explicitly: ref.set dim=who target=<atom>

The four tiers (expanded):
  1. Interrogative / relational axes — $who/$where/$why/$when/$how/$what/$which
  2. Deictic pointers — ref:this/that/here/there/now/then (proximity axes)
  3. Causal / logical connectives — ref:because/therefore/if/but/and/or/not
  4. Quantifiers + ordering — ref:all/some/none (∀/∃/¬∃); ref:before/after/during/simultaneous; ref:equal
"""

import time
import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.akasha.composite import NucleusEngine

# ---------------------------------------------------------------------------
# Atom definitions
# ---------------------------------------------------------------------------

_REF_ATOMS = [
    # ── Interrogative / relational axes ──────────────────────────────────────
    # Each is a dimension of inquiry AND a typed session-variable slot ($who, …).
    ("ref:who",       "agent reference axis: the actor, person, or subject in context"),
    ("ref:what",      "entity reference axis: the thing, concept, or object in context"),
    ("ref:where",     "spatial reference axis: the location or place in context"),
    ("ref:when",      "temporal reference axis: the time point or period in context"),
    ("ref:why",       "causal interrogative axis: the reason or motive — question form of ref:because"),
    ("ref:how",       "manner and method reference axis: the way or means by which something occurs"),
    ("ref:which",     "selective reference axis: a choice among a set of alternatives"),
    # ── Deictic pointers ─────────────────────────────────────────────────────
    ("ref:this",      "proximal demonstrative: points to the contextually near or current entity"),
    ("ref:that",      "distal demonstrative: points to a contextually distant or prior entity"),
    ("ref:here",      "proximal spatial deictic: the current or near location"),
    ("ref:there",     "distal spatial deictic: a distant or referenced location"),
    ("ref:now",       "proximal temporal deictic: the present moment"),
    ("ref:then",      "distal temporal deictic: a referenced past or future moment"),
    # ── Causal / logical connectives ─────────────────────────────────────────
    # Directionality is FIXED; use in .ak links to assert causal structure
    # without ambiguity.  Auditing a mis-link is straightforward because the
    # semantics are standardised here, not in the librarian's free-form label.
    ("ref:because",   "backward causal connective: A because B means B→A (B causes A)"),
    ("ref:therefore", "forward causal connective: A therefore B means A→B (A causes or entails B)"),
    ("ref:if",        "conditional antecedent: marks the premise of a conditional relation"),
    ("ref:but",       "concessive/contrastive connective: holds despite prior expectation"),
    ("ref:and",       "additive connective: joins two propositions or entities"),
    ("ref:or",        "disjunctive connective: marks mutually exclusive or overlapping alternatives"),
    ("ref:not",       "negation operator: inverts or denies the attached proposition"),
    # ── Quantifiers (scope over a domain) ────────────────────────────────────
    # ∀ / ∃ / ¬∃ expressed as typed atoms so .ak files can assert scope.
    ("ref:all",       "universal quantifier (∀): the predicate holds for every member of the domain"),
    ("ref:some",      "existential quantifier (∃): the predicate holds for at least one member"),
    ("ref:none",      "null quantifier (¬∃): the predicate holds for no member of the domain"),
    # ── Ordering relations (temporal or logical sequence) ────────────────────
    # Finer-grained than chrono:period (which covers historical eras).
    # These primitives are usable for any ordered structure: time, step lists,
    # argument chains, causal sequences, etc.
    ("ref:before",    "precedence relation: A comes before B in an ordered sequence"),
    ("ref:after",     "succession relation: A comes after B in an ordered sequence"),
    ("ref:during",    "containment relation: A occurs within the span or scope of B"),
    ("ref:simultaneous", "co-occurrence relation: A and B occur at the same time or step"),
    # ── Identity / equality ───────────────────────────────────────────────────
    # Complement to sys:same_as (which is used for concept identity).
    # ref:equal is the logical equality predicate — two atoms carry the same value
    # or occupy the same position in a structure.
    ("ref:equal",     "equality predicate: A and B are identical in value or position"),
]

# Short-form aliases so .ak files can write `ln A B because` instead of
# `ln A B ref:because`.  Only registered if the short form is unclaimed.
_REF_ALIASES = [
    ("ref:because",     "because"),
    ("ref:therefore",   "therefore"),
    ("ref:if",          "if"),
    ("ref:but",         "but"),
    ("ref:and",         "and"),
    ("ref:or",          "or"),
    ("ref:not",         "not"),
    ("ref:all",         "all"),
    ("ref:some",        "some"),
    ("ref:none",        "none"),
    ("ref:before",      "before"),
    ("ref:after",       "after"),
    ("ref:during",      "during"),
    ("ref:simultaneous", "simultaneous"),
    ("ref:equal",       "equal"),
]

# Innate semantic links between ref: atoms.
# (src_alias, dst_alias, rel_label)
# rel_label is stored as a string in the links table — no atom required.
_REF_LINKS = [
    # Proximity axis: near-pole ↔ far-pole
    ("ref:this",        "ref:that",         "thesaurus:antonym"),
    ("ref:here",        "ref:there",        "thesaurus:antonym"),
    ("ref:now",         "ref:then",         "thesaurus:antonym"),
    # Interrogative shares axis with its deictic counterparts
    ("ref:where",       "ref:here",         "ref:same_axis"),
    ("ref:where",       "ref:there",        "ref:same_axis"),
    ("ref:when",        "ref:now",          "ref:same_axis"),
    ("ref:when",        "ref:then",         "ref:same_axis"),
    # Causal axis: why (interrogative) ↔ because (backward) ↔ therefore (forward)
    ("ref:why",         "ref:because",      "ref:same_axis"),
    ("ref:because",     "ref:therefore",    "ref:inverse"),     # direction flipped
    # Quantifier axis: all ↔ none are antonyms; some lies between them
    ("ref:all",         "ref:none",         "thesaurus:antonym"),
    ("ref:some",        "ref:all",          "ref:weaker_than"),  # ∃ is weaker claim than ∀
    ("ref:some",        "ref:none",         "ref:weaker_than"),
    # Ordering axis: before ↔ after are inverses; during is a sub-relation of when
    ("ref:before",      "ref:after",        "ref:inverse"),
    ("ref:when",        "ref:before",       "ref:same_axis"),
    ("ref:when",        "ref:after",        "ref:same_axis"),
    ("ref:when",        "ref:during",       "ref:same_axis"),
    ("ref:when",        "ref:simultaneous", "ref:same_axis"),
    # Equality relates to sameness
    ("ref:equal",       "ref:not",          "ref:inverse"),
    # ── Cross-links: ref: connectives ↔ DNA log: fuzzy logic ─────────────────
    # ref: atoms are the natural-language surface; log: atoms are the formal
    # fuzzy-logic equivalents.  Both exist; the link records their equivalence.
    ("ref:and",         "log:and",          "calc:associated_with"),
    ("ref:or",          "log:or",           "calc:associated_with"),
    ("ref:not",         "log:not",          "calc:associated_with"),
    ("ref:if",          "log:implies",      "calc:associated_with"),
    # Cross-links: causal connectives ↔ sys: topology
    ("ref:therefore",   "sys:causes",       "calc:associated_with"),
    ("ref:because",     "sys:causes",       "calc:associated_with"),
    # Cross-links: set operations ↔ propositional logic
    # The logical equivalence: union=OR, intersection=AND, complement=NOT
    ("set_op:union",        "log:or",       "calc:associated_with"),
    ("set_op:intersection", "log:and",      "calc:associated_with"),
    ("set_op:complement",   "log:not",      "calc:associated_with"),
    # De Morgan's laws (structural, not asserted as inferential rules here)
    ("set_op:union",        "set_op:intersection", "ref:inverse"),
    # Quantifiers ↔ set operations
    ("ref:all",         "set_op:intersection", "calc:associated_with"),  # ∀ = AND over all members
    ("ref:some",        "set_op:union",        "calc:associated_with"),  # ∃ = OR over members
    ("ref:none",        "set_op:complement",   "calc:associated_with"),  # ¬∃ = complement of ∃
    # Quantifiers ↔ fuzzy logic
    ("ref:all",         "log:and",          "calc:associated_with"),
    ("ref:some",        "log:or",           "calc:associated_with"),
    ("ref:none",        "log:not",          "calc:associated_with"),
]

# ---------------------------------------------------------------------------
# Set memberships for ref: primitives.
# Grouped so `exp ns=ref` or `s ls ref:interrogative` reveals them.
# (alias, set_name) — added AFTER atoms are seeded.
# ---------------------------------------------------------------------------
_REF_SET_MEMBERSHIPS = [
    # Interrogative axes
    ("ref:who",         "ref:interrogative"),
    ("ref:what",        "ref:interrogative"),
    ("ref:where",       "ref:interrogative"),
    ("ref:when",        "ref:interrogative"),
    ("ref:why",         "ref:interrogative"),
    ("ref:how",         "ref:interrogative"),
    ("ref:which",       "ref:interrogative"),
    # Deictic pointers
    ("ref:this",        "ref:deictic"),
    ("ref:that",        "ref:deictic"),
    ("ref:here",        "ref:deictic"),
    ("ref:there",       "ref:deictic"),
    ("ref:now",         "ref:deictic"),
    ("ref:then",        "ref:deictic"),
    # Logical / causal connectives
    ("ref:because",     "ref:connective"),
    ("ref:therefore",   "ref:connective"),
    ("ref:if",          "ref:connective"),
    ("ref:but",         "ref:connective"),
    ("ref:and",         "ref:connective"),
    ("ref:or",          "ref:connective"),
    ("ref:not",         "ref:connective"),
    # Quantifiers
    ("ref:all",         "ref:quantifier"),
    ("ref:some",        "ref:quantifier"),
    ("ref:none",        "ref:quantifier"),
    # Ordering relations
    ("ref:before",      "ref:ordering"),
    ("ref:after",       "ref:ordering"),
    ("ref:during",      "ref:ordering"),
    ("ref:simultaneous","ref:ordering"),
    # Identity
    ("ref:equal",       "ref:identity"),
    # All ref: atoms also go into a master set
    *[
        (alias, "leaf:ref")
        for alias, _ in [
            ("ref:who", ""), ("ref:what", ""), ("ref:where", ""), ("ref:when", ""),
            ("ref:why", ""), ("ref:how", ""), ("ref:which", ""),
            ("ref:this", ""), ("ref:that", ""), ("ref:here", ""), ("ref:there", ""),
            ("ref:now", ""), ("ref:then", ""),
            ("ref:because", ""), ("ref:therefore", ""), ("ref:if", ""),
            ("ref:but", ""), ("ref:and", ""), ("ref:or", ""), ("ref:not", ""),
            ("ref:all", ""), ("ref:some", ""), ("ref:none", ""),
            ("ref:before", ""), ("ref:after", ""), ("ref:during", ""),
            ("ref:simultaneous", ""), ("ref:equal", ""),
        ]
    ],
    # set_op: atoms (from DNA) into their own set
    ("set_op:union",        "leaf:set_op"),
    ("set_op:intersection", "leaf:set_op"),
    ("set_op:difference",   "leaf:set_op"),
    ("set_op:complement",   "leaf:set_op"),
    ("set_op:membership",   "leaf:set_op"),
    ("set_op:subset",       "leaf:set_op"),
    ("set_op:empty",        "leaf:set_op"),
    ("set_op:universal",    "leaf:set_op"),
]

# ---------------------------------------------------------------------------
# Typed session-variable dimensions
# ---------------------------------------------------------------------------

# Maps $-variable suffix → ref: atom alias (used by ContextResolver).
# $who → looks up session context "ref_slot:who" → returns the stored atom key.
REF_SLOT_DIMENSIONS: dict = {
    "who":   "ref:who",
    "what":  "ref:what",
    "where": "ref:where",
    "when":  "ref:when",
    "why":   "ref:why",
    "how":   "ref:how",
    "which": "ref:which",
    # Deictic slots — explicitly settable via ref.set
    "this":  "ref:this",
    "that":  "ref:that",
    "here":  "ref:here",
    "there": "ref:there",
    "now":   "ref:now",
    "then":  "ref:then",
}

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

_SENTINEL_CAT = "system"
_SENTINEL_KEY = "ref_primitives_seeded_v2"  # bumped: added quantifiers, ordering, set_op cross-links


def bootstrap_ref_primitives(nucleus: "NucleusEngine") -> None:
    """
    Seed ref: primitives into the nucleus (idempotent — no-op if already done).

    Called by AkashaManager right after shared_nucleus is created, before any
    .ak ontology loading.  Writes directly to nucleus.core (bypassing WriteQueue)
    because this executes synchronously at startup before any user sessions exist.

    Content-addressing guarantees idempotency: re-running on an existing DB
    produces the same SHA-256 keys and `INSERT OR REPLACE` is a no-op.
    """
    if nucleus.vault_retrieve(_SENTINEL_CAT, _SENTINEL_KEY):
        return  # already seeded on a prior boot

    ts = time.time()

    for alias, description in _REF_ATOMS:
        content = f"[{alias}]\n{description}"
        key = hashlib.sha256(content.encode("utf-8")).hexdigest()
        nucleus.core.put_chunk_raw(
            key, content,
            '{"type":"ref_primitive","canonical":true}',
            "system", "verified", ts,
        )
        nucleus.core.put_chunk_access(key, ["scope:sys:universal"])
        if not nucleus.core.get_key_by_alias(alias):
            nucleus.core.put_alias(key, alias)

    for alias, short in _REF_ALIASES:
        key = nucleus.resolve_alias(alias)
        if key and not nucleus.resolve_alias(short):
            nucleus.core.put_alias(key, short)

    for src_alias, dst_alias, rel in _REF_LINKS:
        src = nucleus.resolve_alias(src_alias)
        dst = nucleus.resolve_alias(dst_alias)
        if src and dst:
            nucleus.core.put_link_raw(src, dst, rel, w=1.0, author="system", ts=ts)

    for alias, set_name in _REF_SET_MEMBERSHIPS:
        key = nucleus.resolve_alias(alias)
        if key:
            nucleus.add_to_set(set_name, key)

    nucleus.vault_store(_SENTINEL_CAT, _SENTINEL_KEY, True)
