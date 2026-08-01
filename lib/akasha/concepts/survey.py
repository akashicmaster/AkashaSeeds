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
from typing import Dict, List, Any, Optional, Tuple

from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts.mixins.exportable import ExportableMixin

logger = logging.getLogger("Harmonia.Concept.Survey")

CONTEXT_KEY_ACTIVE = "active_survey_root"
INDEX_SET = "set:survey:index"

_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"
_MAX_EXPORT_RESPONSES = 5000   # hard cap for export_projection (mirrors lens _MAX_NODES)


class SurveyConcept(BaseConcept, ExportableMixin):
    """Pure structural Survey Universe."""

    CONCEPT_PREFIX = "survey"
    CONCEPT_METHODS = {
        "new":     {"op": "op_new", "action": "write", "args": ["title"],
                    "desc": "Create a survey: survey.new <title> [description=]"},
        "open":    {"op": "op_open", "action": "read", "args": ["survey_id"],
                    "desc": "Mount a survey as the active one: survey.open <survey_id>"},
        "ls":      {"op": "op_surveys", "action": "read", "args": [],
                    "desc": "List surveys: survey.ls"},
        "q.add":   {"op": "op_add_question", "action": "write", "args": ["text", "qtype"],
                    "desc": "Add a question: survey.q.add <text> [qtype=free_text|choice] [order=]"},
        "opt.add": {"op": "op_add_option", "action": "write", "args": ["question_id", "label"],
                    "desc": "Add a choice option to a question: survey.opt.add <question_id> <label> [value=]"},
        "res.add": {"op": "op_add_respondent", "action": "write", "args": ["respondent_id"],
                    "desc": "Register a respondent: survey.res.add <respondent_id> [attributes=]"},
        "ans":     {"op": "op_add_response", "action": "write",
                    "args": ["question_id", "respondent_atom", "answer"],
                    "desc": "Record an answer: survey.ans <question_id> <respondent_atom> <answer>"},
        "list":    {"op": "op_list", "action": "read", "args": [],
                    "desc": "Structural inventory of the active survey: survey.list"},
        "rm":      {"op": "op_delete", "action": "drop", "args": [],
                    "desc": "Delete the active survey: survey.rm"},
    }

    # ── ExportableMixin — lens export adapter ────────────────────────────────
    #
    # A survey root is exported as its RESPONSES, one node per response, carrying
    # the answer + question text + respondent id as rec: attributes so the stream
    # can be re-projected into any Importable target (table, rec, …) — the survey
    # OUT side of the pipe, complementing contexa.ingest (the IN side).
    #
    # Survey roots carry meta type="concept"; that value is shared by other concept
    # models, so `meta_match` refines detection to concept="survey" only.

    EXPORT_SCHEMA = {
        "model":       "survey",
        "meta_type":   "concept",                 # survey root atoms carry type="concept"
        "meta_match":  {"concept": "survey"},      # …refined to survey roots only
        "description": "Survey responses as records (answer / question / respondent).",
        "produces":    ["rec:"],
    }

    def export_projection(self, src_key: str, **opts) -> Optional[List[Tuple]]:
        """Return the survey's responses as SourceScanner-format nodes.

        src_key — atom key of the survey root (resolved from alias by the scanner)
        Each node: (response_key, attrs, 0, response_meta)
          attrs = {"content", "rec:answer", "rec:question", "rec:respondent"}

        Returns None if src_key is not a survey root (scanner falls through to a
        plain set/tree scan).  Scope-filtered against the session's allowed scopes.
        """
        meta = self.cortex.get_meta(src_key) or {}
        if meta.get("concept") != "survey":
            return None

        allowed  = self.allowed_scopes
        resp_set = f"set:survey:{src_key}:responses"
        resp_keys = self.cortex.get_collection_members(resp_set) or []

        q_cache: Dict[str, str] = {}
        r_cache: Dict[str, str] = {}
        nodes: List[Tuple] = []

        for rk in resp_keys[:_MAX_EXPORT_RESPONSES]:
            if allowed and not self.cortex.check_access(rk, allowed):
                continue
            rmeta = self.cortex.get_meta(rk) or {}
            if rmeta.get("type") != "survey_response":
                continue

            attrs: Dict[str, str] = {"content": self.cortex.get_chunk(rk) or ""}

            ans = rmeta.get("answer")
            if ans is not None and str(ans).strip():
                attrs["rec:answer"] = str(ans)

            qid = rmeta.get("question_id")
            if qid:
                if qid not in q_cache:
                    q_cache[qid] = self.cortex.get_chunk(qid) or ""
                if q_cache[qid]:
                    attrs["rec:question"] = q_cache[qid]

            ratom = rmeta.get("respondent_atom")
            if ratom:
                if ratom not in r_cache:
                    rm = self.cortex.get_meta(ratom) or {}
                    r_cache[ratom] = rm.get("respondent_id") or (self.cortex.get_chunk(ratom) or "")
                if r_cache[ratom]:
                    attrs["rec:respondent"] = r_cache[ratom]

            nodes.append((rk, attrs, 0, rmeta))

        return nodes

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
        self.ensure_concept_set()

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

        # Atoms are content-addressed, but a response is inherently tied to its (respondent,
        # question): two respondents giving the SAME answer are DISTINCT responses and must not
        # collapse to one atom. So the content encodes respondent+question; the raw answer lives
        # in meta['answer'] for aggregation. (Without this, identical answers silently dedupe and
        # a single shared response atom accumulates every respondent's ctx:from — corrupt data.)
        resp_id = self.cortex.put_chunk(
            content=f"[response {respondent_atom[:8]}→{question_id[:8]}] {answer}",
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
