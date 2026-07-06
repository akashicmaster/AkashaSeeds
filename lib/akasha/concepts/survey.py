"""
Survey Concept Model (v1.2).

Pure structural Survey Universe:

- Survey (root)
- Questions
- Options
- Respondents
- Responses (tri-linked: survey ← question ← respondent)

Topology (sets):

  set:survey:index            — global index of all survey roots
  set:survey:{id}             — all content atoms for this survey
  set:survey:{id}:questions
  set:survey:{id}:options
  set:survey:{id}:respondents
  set:survey:{id}:responses

Namespace contract (two-namespace rule):

  - Content atoms    → set:survey:{concept_id}  (survey-model scope)
  - Concept-word atoms → set:concept:{concept_id}  (concept catalog scope)

The concept catalog (set:concept:{id}) contains ONLY concept-word atoms
("survey", "question", "option", "respondent", "response").  The root atom
itself is NOT added to the catalog — it lives in the survey-scope sets and
the global index.  Each content atom links to its concept-word via
sys:derived_from.
"""

import time
import logging
from typing import Dict, List, Any, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Survey")

CONTEXT_KEY_ACTIVE = "active_survey_root"
INDEX_SET = "set:survey:index"

_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"


class SurveyConcept(BaseConcept):
    """Pure structural Survey Universe."""

    CONCEPT_PREFIX = "survey"
    CONCEPT_METHODS = {
        "new":     {"op": "op_new"},
        "open":    {"op": "op_open"},
        "ls":      {"op": "op_surveys"},
        "q.add":   {"op": "op_add_question"},
        "opt.add": {"op": "op_add_option"},
        "res.add": {"op": "op_add_respondent"},
        "ans":     {"op": "op_add_response"},
        "list":    {"op": "op_list"},
        "rm":      {"op": "op_delete"},
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)

        # Auto-mount: if kernel didn't pass a concept_id, try the session context
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ── Private helpers ───────────────────────────────────────────────────────

    def _author_and_scopes(self):
        """Returns (author_id, user_scopes) from the current session."""
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _survey_set(self, suffix: Optional[str] = None) -> str:
        """Survey content namespace root."""
        base = f"set:survey:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _get_or_create_concept_word(self, word: str, model: str = "survey") -> str:
        """
        Return (or create) the concept-word atom for a structural role name
        ("survey", "question", "option", "respondent", "response", …).
        Idempotent: re-uses the existing atom if the alias already exists.
        """
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing

        author_id, scopes = self._author_and_scopes()
        key = self.cortex.put_chunk(
            content=word,
            meta={
                "type":          "concept_word",
                "word":          word,
                "concept_model": model,
                "created_at":    time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.set_alias(key, alias)
        return key

    def _register_to_package(
        self,
        key: str,
        subset_suffix: Optional[str] = None,
        concept_word: Optional[str] = None,
    ) -> None:
        """
        Dual-namespace registration for a content atom.

        1. Content atom → survey-scope sets (set:survey:{id}  and  set:survey:{id}:{suffix})
        2. Concept-word atom → concept catalog (set:concept:{id}) via sys:derived_from link

        The concept catalog holds ONLY concept-word atoms, never content atoms directly.
        """
        author_id, _ = self._author_and_scopes()

        # 1. Content atom → survey-scope
        self.cortex.add_to_set(self._survey_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._survey_set(subset_suffix), key)

        # 2. Concept-word atom → concept catalog + one-directional derivation link
        if concept_word:
            cw_key = self._get_or_create_concept_word(concept_word, model="survey")
            self.register_concept_node(cw_key)
            self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    # ── Operators (public API) ────────────────────────────────────────────────

    def op_new(self, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        """[survey.new] Create a new Survey root."""
        author_id, scopes = self._author_and_scopes()

        root_id = self.cortex.put_chunk(
            content=f"[ Survey: {title} ]",
            meta={
                "type":        "concept",
                "concept":     "survey",
                "role":        "root",
                "title":       title,
                "description": description or "",
                "created_at":  time.time(),
            },
            author=author_id,
            scopes=scopes,
        )

        # Mount session context
        self.concept_id = root_id
        self.set_name   = f"set:concept:{self.concept_id}"

        # Concept catalog set — root is NOT added here; only concept-word atoms go in
        self.cortex.create_set(self.set_name)

        # Root → survey-scope + derive from concept-word "survey"
        self._register_to_package(root_id, subset_suffix=None, concept_word="survey")

        # Survey content sets
        for suffix in (None, "questions", "options", "respondents", "responses"):
            self.cortex.create_set(self._survey_set(suffix))

        # Global index (idempotent create)
        self.cortex.create_set(INDEX_SET)
        self.cortex.add_to_set(INDEX_SET, root_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)

        logger.info(f"[SurveyConcept] Created survey '{title}' ({root_id[:8]})")
        return {"status": "created", "survey_id": root_id, "title": title}

    def op_open(self, survey_id: str) -> Dict[str, Any]:
        """[survey.open] Mount an existing survey as the session's active survey."""
        meta = self.cortex.get_meta(survey_id)
        if not meta or meta.get("concept") != "survey":
            raise RuntimeError(f"Atom '{survey_id[:12]}' is not a survey root.")

        self.concept_id = survey_id
        self.set_name   = f"set:concept:{self.concept_id}"

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, survey_id)

        return {
            "status":      "opened",
            "survey_id":   survey_id,
            "title":       meta.get("title", ""),
            "description": meta.get("description", ""),
        }

    def op_add_question(
        self,
        text: str,
        qtype: str = "free_text",
        order: Optional[int] = None,
    ) -> Dict[str, Any]:
        """[survey.q.add] Add a question to the active survey."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        q_id = self.cortex.put_chunk(
            content=text,
            meta={
                "type":          "survey_question",
                "question_type": qtype,
                "order":         order,
                "created_at":    time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register_to_package(q_id, subset_suffix="questions", concept_word="question")
        self.cortex.put_link(self.concept_id, q_id, "sys:contains", author=author_id)
        self.cortex.put_link(q_id, self.concept_id, "sys:part_of",  author=author_id)

        return {"status": "question_added", "question_id": q_id, "text": text}

    def op_add_option(
        self,
        question_id: str,
        label: str,
        value: Optional[str] = None,
    ) -> Dict[str, Any]:
        """[survey.opt.add] Add an answer option to a question."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        opt_id = self.cortex.put_chunk(
            content=label,
            meta={
                "type":       "survey_option",
                "label":      label,
                "value":      value or label,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register_to_package(opt_id, subset_suffix="options", concept_word="option")
        self.cortex.put_link(question_id, opt_id, "sys:contains", author=author_id)
        self.cortex.put_link(opt_id, question_id, "sys:part_of",  author=author_id)

        return {"status": "option_added", "option_id": opt_id}

    def op_add_respondent(
        self,
        respondent_id: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """[survey.res.add] Register a respondent in the active survey."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        r_atom = self.cortex.put_chunk(
            content=f"[Respondent {respondent_id}]",
            meta={
                "type":          "survey_respondent",
                "respondent_id": respondent_id,
                "attributes":    attributes or {},
                "created_at":    time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register_to_package(r_atom, subset_suffix="respondents", concept_word="respondent")
        self.cortex.put_link(self.concept_id, r_atom, "sys:contains", author=author_id)
        self.cortex.put_link(r_atom, self.concept_id, "sys:part_of",  author=author_id)

        return {"status": "respondent_added", "respondent_atom": r_atom}

    def op_add_response(
        self,
        question_id: str,
        respondent_atom: str,
        answer: Any,
    ) -> Dict[str, Any]:
        """[survey.ans] Record a tri-linked response (survey ↔ question ↔ respondent)."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        resp_id = self.cortex.put_chunk(
            content=str(answer),
            meta={
                "type":            "survey_response",
                "question_id":     question_id,
                "respondent_atom": respondent_atom,
                "answer":          answer,
                "timestamp":       time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self._register_to_package(resp_id, subset_suffix="responses", concept_word="response")

        # Tri-links: survey root, question, respondent all point to response
        for src in (self.concept_id, question_id, respondent_atom):
            self.cortex.put_link(src,     resp_id, "sys:contains", author=author_id)
            self.cortex.put_link(resp_id, src,     "sys:part_of",  author=author_id)

        return {"status": "response_added", "response_id": resp_id}

    def op_list(self) -> Dict[str, Any]:
        """[survey.list] Return the structural inventory of the active survey."""
        self._require_concept()
        allowed = self.allowed_scopes

        def safe_members(suffix: str) -> List[str]:
            return [
                k for k in self.cortex.get_collection_members(self._survey_set(suffix))
                if self.cortex.check_access(k, allowed)
            ]

        return {
            "survey_id":   self.concept_id,
            "questions":   safe_members("questions"),
            "options":     safe_members("options"),
            "respondents": safe_members("respondents"),
            "responses":   safe_members("responses"),
        }

    def op_surveys(self) -> Dict[str, Any]:
        """[survey.ls] List all surveys accessible to this session."""
        members = self.cortex.get_collection_members(INDEX_SET)
        items: List[Dict[str, Any]] = []
        for key in members:
            if not self.cortex.check_access(key, self.allowed_scopes):
                continue
            meta = self.cortex.get_meta(key) or {}
            if meta.get("concept") != "survey":
                continue
            items.append({
                "survey_id":   key,
                "title":       meta.get("title", ""),
                "description": meta.get("description", ""),
                "created_at":  meta.get("created_at", 0),
            })
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"surveys": items, "count": len(items)}

    def op_delete(self) -> Dict[str, Any]:
        """[survey.rm] Delete the active survey and clear session context."""
        self._require_concept()
        survey_id = self.concept_id
        self.cortex.drop_chunk(survey_id, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "survey_id": survey_id}
