"""
Synthesis Concept Model.

Models the qualitative thinking process between raw source material and
presentation-ready claims.

Flow:
    Source -> Code -> Theme -> Interpretation -> Claim -> Thread

Namespace contract (two-namespace rule):
  - Content atoms  → set:synth:{concept_id}  AND  set:synth:{concept_id}:{subset}
  - Concept-word atom → set:concept:{concept_id}  (concept catalog scope)
"""

import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Synthesis")

CONTEXT_KEY_ACTIVE = "active_synthesis_root"
INDEX_SET = "set:synth:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"


class SynthesisConcept(BaseConcept):
    """Qualitative synthesis model: evidence -> meaning -> argument."""

    CONCEPT_PREFIX = "synth"

    CONCEPT_METHODS = {
        "new":        {"op": "op_new"},
        # Accept both "synth_id" and "synthesis_id" since the API returns the latter
        "open":       {"op": "op_open",
                       "coerce": lambda d: {
                           "synth_id": d.get("synth_id") or d.get("synthesis_id", ""),
                       }},
        "ls":         {"op": "op_list"},
        "source.add": {"op": "op_add_source"},
        "code.add":   {"op": "op_add_code"},
        "theme.add":  {"op": "op_add_theme"},
        "interp.add": {"op": "op_add_interpretation"},
        "claim.add":  {"op": "op_add_claim"},
        "thread.new": {"op": "op_new_thread"},
        "thread.add": {"op": "op_add_thread_step"},
        "map":        {"op": "op_map"},
        "trace":      {"op": "op_trace"},
        "rm":         {"op": "op_delete"},
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        if not self.concept_id:
            active = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if active:
                self.concept_id = active
                self.set_name = f"set:concept:{self.concept_id}"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _get_set_name(self, suffix: str = "") -> str:
        if suffix:
            return f"set:synth:{self.concept_id}:{suffix}"
        return f"set:synth:{self.concept_id}"

    def _create_sets(self):
        self.cortex.create_set(INDEX_SET)
        self.cortex.create_set(self._get_set_name())
        self.cortex.create_set(self._get_set_name("sources"))
        self.cortex.create_set(self._get_set_name("codes"))
        self.cortex.create_set(self._get_set_name("themes"))
        self.cortex.create_set(self._get_set_name("interpretations"))
        self.cortex.create_set(self._get_set_name("claims"))
        self.cortex.create_set(self._get_set_name("threads"))

    def _get_or_create_concept_word(self, word: str) -> str:
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        author_id, scopes = self._author_and_scopes()
        key = self.cortex.put_chunk(
            content=word,
            meta={
                "type": "concept_word",
                "word": word,
                "concept_model": "synthesis",
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.set_alias(key, alias)
        return key

    def _register(
        self,
        key: str,
        subset_suffix: Optional[str] = None,
        concept_word: Optional[str] = None,
    ):
        author_id = getattr(self.session, "client_id", "system")
        self.cortex.add_to_set(self._get_set_name(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._get_set_name(subset_suffix), key)
        if concept_word:
            cw_key = self._get_or_create_concept_word(concept_word)
            self.register_concept_node(cw_key)
            self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    def _append_to_thread(self, thread_id: str, node_id: str, author_id: str):
        tail_links = self.cortex.get_adjacent_links(thread_id, "sys:bottom")
        if not tail_links:
            self.cortex.put_link(thread_id, node_id, "sys:top", author=author_id)
        else:
            last_node_id = tail_links[0][0]
            self.cortex.put_link(last_node_id, node_id, "sys:next", author=author_id)
            self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)
            self.cortex.remove_link(thread_id, last_node_id, "sys:bottom")
        self.cortex.put_link(thread_id, node_id, "sys:bottom", author=author_id)

    def _visible(self, key: str) -> bool:
        return self.cortex.check_access(key, self.allowed_scopes)

    def _atom_summary(self, key: str) -> Dict[str, Any]:
        return {
            "id": key,
            "content": self.cortex.get_chunk(key),
            "meta": self.cortex.get_meta(key),
        }

    def _members(self, suffix: str) -> List[str]:
        # [FIX] Filter by access — original returned all members without checking visibility
        return [
            k for k in self.cortex.get_collection_members(self._get_set_name(suffix))
            if self._visible(k)
        ]

    # ── Root lifecycle ────────────────────────────────────────────────────────

    def op_new(
        self,
        title: str,
        source_universes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """[synth.new] Create a SynthesisRoot."""
        if not title:
            raise ValueError("title is required")

        author_id, scopes = self._author_and_scopes()
        source_universes = source_universes or []

        root_id = self.cortex.put_chunk(
            content=f"[ Synthesis: {title} ]",
            meta={
                "type": "concept",
                "concept": "synthesis",
                "role": "root",
                "title": title,
                "source_universes": source_universes,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )

        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"

        # [FIX] Create concept catalog set before any registration that writes to it
        self.ensure_concept_set()
        self._create_sets()

        # [FIX] Ensure INDEX_SET exists before adding root (also created inside _create_sets,
        # kept explicit here for clarity of intent)
        self.cortex.create_set(INDEX_SET)
        self.cortex.add_to_set(INDEX_SET, root_id)

        # [FIX] Register only after all target sets are guaranteed to exist
        self._register(root_id, concept_word="synthesis")

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)

        logger.info("[SynthesisConcept] Created '%s' (%s)", title, root_id[:8])
        return {
            "status": "created",
            "synthesis_id": root_id,
            "title": title,
            "source_universes": source_universes,
        }

    def op_open(self, synth_id: str) -> Dict[str, Any]:
        """[synth.open] Mount an existing synthesis as the session's active synthesis."""
        if not synth_id:
            raise ValueError("synthesis_id is required")
        if not self._visible(synth_id):
            raise RuntimeError("synthesis not found or access denied")

        meta = self.cortex.get_meta(synth_id)
        if not meta or meta.get("concept") != "synthesis":
            raise RuntimeError("atom is not a synthesis root")

        self.concept_id = synth_id
        self.set_name = f"set:concept:{self.concept_id}"

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, synth_id)

        return {
            "status": "opened",
            "synthesis_id": synth_id,
            "title": meta.get("title", ""),
            "source_universes": meta.get("source_universes", []),
        }

    def op_list(self) -> Dict[str, Any]:
        """[synth.ls] List all synthesis roots accessible to this session."""
        members = self.cortex.get_collection_members(INDEX_SET)
        items = []
        for key in members:
            if not self._visible(key):
                continue
            meta = self.cortex.get_meta(key) or {}
            if meta.get("concept") != "synthesis":
                continue
            items.append({
                "synthesis_id": key,
                "title": meta.get("title", ""),
                "source_universes": meta.get("source_universes", []),
                "created_at": meta.get("created_at", 0),
            })
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"syntheses": items, "count": len(items)}

    # ── Source / Code / Theme / Interpretation / Claim ────────────────────────

    def op_add_source(
        self,
        ref_id: str,
        ref_universe: str = "",
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """[synth.source.add] Index an existing Cortex atom as a source; optionally annotate it."""
        self._require_concept()
        if not ref_id:
            raise ValueError("ref_id is required")
        if not self._visible(ref_id):
            raise RuntimeError("source atom not found or access denied")

        author_id, scopes = self._author_and_scopes()

        root_meta = self.cortex.get_meta(self.concept_id) or {}
        allowed = root_meta.get("source_universes") or []
        if allowed and ref_universe and ref_universe not in allowed:
            raise ValueError(f"ref_universe '{ref_universe}' is not allowed")

        # Index the original atom directly (no copy)
        self.cortex.add_to_set(self._get_set_name("sources"), ref_id)
        self.cortex.add_to_set(self._get_set_name(), ref_id)
        self.cortex.put_link(self.concept_id, ref_id, "synth:source", author=author_id)

        source_ref_id = None
        if note:
            source_ref_id = self.cortex.put_chunk(
                content=note,
                meta={
                    "type": "synth_source_ref",
                    "role": "source_ref",
                    "ref_id": ref_id,
                    "ref_universe": ref_universe,
                    "created_at": time.time(),
                },
                author=author_id,
                scopes=scopes,
            )
            self._register(source_ref_id, subset_suffix="sources", concept_word="source")
            self.cortex.put_link(source_ref_id, ref_id, "synth:refers_to", author=author_id)

        return {
            "status": "source_added",
            "source_id": ref_id,
            "source_ref_id": source_ref_id,
            "ref_universe": ref_universe,
        }

    def op_add_code(
        self,
        label: str,
        source_id: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """[synth.code.add] Create a qualitative code, optionally linked to a source atom."""
        self._require_concept()
        if not label:
            raise ValueError("label is required")
        if source_id and not self._visible(source_id):
            raise RuntimeError("source atom not found or access denied")

        author_id, scopes = self._author_and_scopes()

        code_id = self.cortex.put_chunk(
            content=label,
            meta={
                "type": "synth_code",
                "role": "code",
                "label": label,
                "confidence": confidence,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register(code_id, subset_suffix="codes", concept_word="code")
        self.cortex.put_link(self.concept_id, code_id, "synth:code", author=author_id)

        if source_id:
            self.cortex.put_link(code_id, source_id, "synth:applies_to", author=author_id)

        return {
            "status": "code_added",
            "code_id": code_id,
            "label": label,
            "source_id": source_id,
        }

    def op_add_theme(
        self,
        title: str,
        codes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """[synth.theme.add] Create a theme grouping one or more codes."""
        self._require_concept()
        if not title:
            raise ValueError("title is required")

        author_id, scopes = self._author_and_scopes()
        codes = codes or []

        theme_id = self.cortex.put_chunk(
            content=title,
            meta={
                "type": "synth_theme",
                "role": "theme",
                "title": title,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register(theme_id, subset_suffix="themes", concept_word="theme")
        self.cortex.put_link(self.concept_id, theme_id, "synth:theme", author=author_id)

        for code_id in codes:
            if self._visible(code_id):
                self.cortex.put_link(theme_id, code_id, "synth:contains", author=author_id)

        return {
            "status": "theme_added",
            "theme_id": theme_id,
            "title": title,
            "codes": codes,
        }

    def op_add_interpretation(
        self,
        text: str,
        theme_id: Optional[str] = None,
        support: Optional[List[str]] = None,
        stance: str = "hypothesis",
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """[synth.interp.add] Record an interpretation, optionally grounded in a theme and evidence atoms."""
        self._require_concept()
        if not text:
            raise ValueError("text is required")
        if theme_id and not self._visible(theme_id):
            raise RuntimeError("theme not found or access denied")

        author_id, scopes = self._author_and_scopes()
        support = support or []

        interp_id = self.cortex.put_chunk(
            content=text,
            meta={
                "type": "synth_interpretation",
                "role": "interpretation",
                "stance": stance,
                "confidence": confidence,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register(interp_id, subset_suffix="interpretations", concept_word="interpretation")
        self.cortex.put_link(self.concept_id, interp_id, "synth:interp", author=author_id)

        if theme_id:
            self.cortex.put_link(interp_id, theme_id, "synth:interprets", author=author_id)

        for evidence_id in support:
            if self._visible(evidence_id):
                self.cortex.put_link(interp_id, evidence_id, "synth:supported_by", author=author_id)

        return {
            "status": "interpretation_added",
            "interpretation_id": interp_id,
            "theme_id": theme_id,
            "support": support,
        }

    def op_add_claim(
        self,
        text: str,
        interpretations: Optional[List[str]] = None,
        evidence: Optional[List[str]] = None,
        status: str = "draft",
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """[synth.claim.add] Assert a claim backed by interpretations and/or direct evidence."""
        self._require_concept()
        if not text:
            raise ValueError("text is required")

        author_id, scopes = self._author_and_scopes()
        interpretations = interpretations or []
        evidence = evidence or []

        claim_id = self.cortex.put_chunk(
            content=text,
            meta={
                "type": "synth_claim",
                "role": "claim",
                "status": status,
                "confidence": confidence,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register(claim_id, subset_suffix="claims", concept_word="claim")
        self.cortex.put_link(self.concept_id, claim_id, "synth:claim", author=author_id)

        for interp_id in interpretations:
            if self._visible(interp_id):
                self.cortex.put_link(claim_id, interp_id, "synth:argues", author=author_id)

        for evidence_id in evidence:
            if self._visible(evidence_id):
                self.cortex.put_link(claim_id, evidence_id, "synth:evidence", author=author_id)

        return {
            "status": "claim_added",
            "claim_id": claim_id,
            "interpretations": interpretations,
            "evidence": evidence,
        }

    # ── Threads ───────────────────────────────────────────────────────────────

    def op_new_thread(self, title: str) -> Dict[str, Any]:
        """[synth.thread.new] Create a named reasoning thread within the active synthesis."""
        self._require_concept()
        if not title:
            raise ValueError("title is required")

        author_id, scopes = self._author_and_scopes()

        thread_id = self.cortex.put_chunk(
            content=title,
            meta={
                "type": "synth_thread",
                "role": "thread",
                "title": title,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register(thread_id, subset_suffix="threads", concept_word="thread")
        self.cortex.put_link(self.concept_id, thread_id, "synth:thread", author=author_id)

        return {"status": "thread_created", "thread_id": thread_id, "title": title}

    def op_add_thread_step(self, thread_id: str, node_id: str) -> Dict[str, Any]:
        """[synth.thread.add] Append an existing atom as the next step in a reasoning thread."""
        self._require_concept()
        if not thread_id or not node_id:
            raise ValueError("thread_id and node_id are required")
        if not self._visible(thread_id):
            raise RuntimeError("thread not found or access denied")
        if not self._visible(node_id):
            raise RuntimeError("node not found or access denied")

        author_id = getattr(self.session, "client_id", "system")

        self.cortex.put_link(thread_id, node_id, "synth:step", author=author_id)
        self._append_to_thread(thread_id, node_id, author_id)

        return {
            "status": "thread_step_added",
            "thread_id": thread_id,
            "node_id": node_id,
        }

    # ── Projections ───────────────────────────────────────────────────────────

    def op_map(self) -> Dict[str, Any]:
        """[synth.map] Return the full structural inventory of the active synthesis."""
        self._require_concept()
        return {
            "synthesis_id": self.concept_id,
            "sources":         self._members("sources"),
            "codes":           self._members("codes"),
            "themes":          self._members("themes"),
            "interpretations": self._members("interpretations"),
            "claims":          self._members("claims"),
            "threads":         self._members("threads"),
        }

    def op_trace(self, claim_id: str) -> Dict[str, Any]:
        """[synth.trace] Walk the evidence chain from a claim back to raw sources."""
        self._require_concept()
        if not claim_id:
            raise ValueError("claim_id is required")
        if not self._visible(claim_id):
            raise RuntimeError("claim not found or access denied")

        claim = self._atom_summary(claim_id)
        interpretations = []
        themes = []
        codes = []
        sources = []
        evidence = []

        for dst, rel in self.cortex.get_adjacent_links(claim_id):
            if rel == "synth:argues" and self._visible(dst):
                interpretations.append(self._atom_summary(dst))
            elif rel == "synth:evidence" and self._visible(dst):
                evidence.append(self._atom_summary(dst))

        for interp in interpretations:
            for dst, rel in self.cortex.get_adjacent_links(interp["id"]):
                if not self._visible(dst):
                    continue
                if rel == "synth:interprets":
                    themes.append(self._atom_summary(dst))
                elif rel == "synth:supported_by":
                    evidence.append(self._atom_summary(dst))

        seen_theme_ids = {t["id"] for t in themes}
        for theme_id in seen_theme_ids:
            for dst, rel in self.cortex.get_adjacent_links(theme_id):
                if rel == "synth:contains" and self._visible(dst):
                    codes.append(self._atom_summary(dst))

        seen_code_ids = {c["id"] for c in codes}
        for code_id in seen_code_ids:
            for dst, rel in self.cortex.get_adjacent_links(code_id):
                if rel == "synth:applies_to" and self._visible(dst):
                    sources.append(self._atom_summary(dst))

        for ev in evidence:
            ev_meta = ev.get("meta") or {}
            if ev_meta.get("role") == "source" or ev_meta.get("type") == "observation":
                sources.append(ev)

        def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            seen: set = set()
            out = []
            for item in items:
                k = item["id"]
                if k not in seen:
                    seen.add(k)
                    out.append(item)
            return out

        return {
            "claim":           claim,
            "interpretations": dedupe(interpretations),
            "themes":          dedupe(themes),
            "codes":           dedupe(codes),
            "sources":         dedupe(sources),
            "evidence":        dedupe(evidence),
        }

    # ── Delete ────────────────────────────────────────────────────────────────

    def op_delete(self) -> Dict[str, Any]:
        """[synth.rm] Delete the active synthesis root and clear session context."""
        self._require_concept()
        target = self.concept_id
        self.cortex.drop_chunk(target, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "synthesis_id": target}
