"""
Deliberation Concept Model — the public-consultation → concept-labo → society bridge.

`delib` is a pure OPERATOR layer (no operands of its own): it reads an existing Survey of collected
public feedback, aggregates it by STANCE through the Aggregation model, projects that aggregation
into a Concept-Laboratory field (clusters → theoretical families → a first-class conclusion), and
posts the result into a Society for deliberation. It writes NO new domain schema — it composes the
survey / aggregation / clab / society operators that already exist, so the same pipeline runs on any
opinion corpus (the EU mobility public-consultation experiment is the first public use).

  survey (feedback)  ──delib.aggregate──▶  aggregation (stance groups + measures)
                     ──delib.to_labo────▶  clab field (clusters · families · conclusion)
                     ──delib.to_society─▶  society feed (proposals + conclusion for deliberation)

Provenance is one directed edge per stage (Akasha traverses both ways):
  survey  --sys:has_aggregation-->  aggregation      (laid by agg.new)
  aggregation  --delib:projects-->  clab field
  clab field   --delib:deliberates-->  society

`delib.pipeline` runs all three in order. First cut: CLI-runnable, degradation-first stance
classification (a keyword lexicon — no LLM required); a connected LLM later sharpens the SAME surface.
"""

import re
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.api.concepts import BaseConcept
from lib.akasha.api.concepts import ImportableMixin

logger = logging.getLogger("Harmonia.Concept.Delib")

_W, _R = "record", "read"

# Degradation-first stance lexicon. Deterministic, stdlib-only; a connected LLM can replace
# `_classify` without touching the pipeline. Order of resolution: count support vs oppose cues,
# then let conditional markers downgrade a lean to "conditional"; ties / no cues → neutral.
_SUPPORT = ("support", "agree", "favour", "favor", "in favour", "welcome", "beneficial", "benefit",
            "encourage", "positive", "back this", "endorse", "good idea", "should be", "yes to")
_OPPOSE = ("oppose", "against", "disagree", "reject", "harmful", "burden", "concern", "worried",
           "worry", "problem", "negative", "no to", "too costly", "unfair", "risk", "damage")
_CONDITIONAL = ("if ", "provided", "as long as", "conditional", "depends", "however", "but ",
                "except", "only when", "unless", "with safeguards", "subject to")

_STANCES = ("support", "oppose", "conditional", "neutral")
# non-English feedback with NO translation is kept HONESTLY as its own state — never forced into
# English, and never asserted to be `neutral` (a stance we did not actually read). It is collected
# input we simply have not read; it forms no conclusion. Kept separate from _STANCES on purpose.
_UNTRANSLATED = "untranslated"
# a coded answer whose declared mapping rule marks it unreadable ("Don't know", "No preferences") is
# kept HONESTLY as its own state — never lexicon-read (the lexicon would fabricate `neutral` from a
# label that contains no cues), never given a stance the mapping did not declare. Like `untranslated`,
# it is counted and visible but forms no cluster and no conclusion.
_NO_READING = "no_reading"
_POLARITY = {"support": "affirm", "oppose": "negate", "conditional": "mixed", "neutral": "undetermined",
             _UNTRANSLATED: "undetermined", _NO_READING: "undetermined"}

# word-boundary matchers so a cue never fires inside another word (e.g. "agree" ⊄ "disagree").
_RE_SUPPORT = re.compile(r"\b(" + "|".join(re.escape(w.strip()) for w in _SUPPORT) + r")\b")
_RE_OPPOSE = re.compile(r"\b(" + "|".join(re.escape(w.strip()) for w in _OPPOSE) + r")\b")
_RE_CONDITIONAL = re.compile(r"\b(" + "|".join(re.escape(w.strip()) for w in _CONDITIONAL) + r")\b")


class DelibConcept(BaseConcept, ImportableMixin):
    """Opinion-aggregation → concept-labo → society deliberation bridge (stateless operators)."""

    CONCEPT_PREFIX = "delib"

    # the general import contract (io.ingest model=delib into=<survey>): raw feedback records →
    # multi-locale survey responses. `text` is required; text_en / language / respondent are preferred.
    IMPORT_SCHEMA = {
        "model": "delib", "requires": ["text"], "prefers": ["text_en", "language", "respondent_id"],
        "min_nodes": 1,
        "description": "Multi-locale public feedback → survey responses (original=primary source, "
                       "text_en=translation-projection). into=<survey id>.",
    }
    CONCEPT_METHODS = {
        "feed":       {"op": "op_feed_one", "action": _W, "cli": "delib.feed", "args": ["survey", "text"],
                       "desc": "Ingest ONE feedback (CLI-native, like survey.ans): the ORIGINAL text is the "
                               "primary-source atom; full_text (原票, optional) is minted as a first-class "
                               "atom + the analysis target; text_en a linked authority translation-projection. "
                               "delib.feed survey=<id> text=\"…\" [full_text=\"…complete…\"] [text_en=\"…\"] [language=de] [respondent=<id>]"},
        "ingest":     {"op": "op_ingest", "action": _W, "cli": "delib.ingest", "args": ["survey"],
                       "desc": "Batch-ingest multi-locale feedback (RPC form) — a list of "
                               "{text,text_en,language,respondent_id}: delib.ingest survey=<id> records=<json>"},
        "aggregate":  {"op": "op_aggregate", "action": _W, "cli": "delib.aggregate", "args": ["survey"],
                       "desc": "Aggregate a survey's feedback by stance: delib.aggregate survey=<id> [by=stance]"},
        "to_labo":    {"op": "op_to_labo", "action": _W, "cli": "delib.to_labo", "args": ["agg"],
                       "desc": "Project an aggregation into a concept-labo field: delib.to_labo agg=<id> [title=]"},
        "to_society": {"op": "op_to_society", "action": _W, "cli": "delib.to_society", "args": ["labo"],
                       "desc": "Post a labo field's conclusion into a society: "
                               "delib.to_society labo=<id> society=<name> group=<gid> [cast=] [space=]"},
        "pipeline":   {"op": "op_pipeline", "action": _W, "cli": "delib.pipeline", "args": ["survey"],
                       "desc": "Run the whole flow survey→agg→labo→society: "
                               "delib.pipeline survey=<id> society=<name> group=<gid> [cast=] [space=] [title=]"},
        "locales":    {"op": "op_locales", "action": _R, "cli": "delib.locales", "args": ["agg"],
                       "desc": "Per-stance locale composition + translation reliance (the "
                               "translation-artifact check feed): delib.locales agg=<id>"},
        "voices":     {"op": "op_voices", "action": _R, "cli": "delib.voices", "args": ["agg"],
                       "desc": "Per-RESPONSE record behind an aggregation (original=operand, "
                               "translation=projection, stance, locale, reliance flags) — the feed "
                               "for parallel-reading / tension / locale-lens / provenance: "
                               "delib.voices agg=<id>"},
        "show":       {"op": "op_show", "action": _R, "cli": "delib.show", "args": ["labo"],
                       "desc": "Summarise a deliberation: delib.show labo=<id>"},
    }

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _author(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _scopes(self) -> List[str]:
        a = self._author()
        return [f"owner:user_{a}", f"view:user_{a}"]

    def _alias_of(self, key: str) -> str:
        try:
            al = self.cortex.get_aliases_by_key(key) or []
        except Exception:
            al = []
        return next((a for a in al if ":" in a), al[0] if al else key)

    @staticmethod
    def _detect_lang(text: str) -> str:
        """Cheapest possible language floor: ASCII-only → assume 'en', else 'und' (undetermined).
        A real per-segment language-ID (the multi-locale NLP roadmap) replaces this without changing
        the pipeline — the original stays the operand; detection only routes classification."""
        t = (text or "").strip()
        if not t:
            return "und"
        try:
            t.encode("ascii")
            return "en"
        except UnicodeEncodeError:
            return "und"

    def _lang_atom(self, code: str) -> str:
        """(Idempotent) the atom for a language code, aliased language:<code>."""
        code = (code or "und").strip().lower()
        alias = f"language:{code}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        key = self.cortex.put_chunk(content=code, meta={"type": "language", "code": code},
                                    author=self._author(), scopes=self._scopes())
        try:
            self.cortex.set_alias(key, alias)
        except Exception:
            pass
        return key

    def _stance_atom(self, stance: str) -> str:
        """(Idempotent) the atom for a declared stance token, aliased delib:stance:<stance>."""
        stance = (stance or "").strip().lower()
        alias = f"delib:stance:{stance}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        key = self.cortex.put_chunk(content=stance, meta={"type": "delib_stance", "stance": stance},
                                    author=self._author(), scopes=self._scopes())
        try:
            self.cortex.set_alias(key, alias)
        except Exception:
            pass
        return key

    def _maprule_atom(self, basis: str) -> str:
        """(Idempotent) the atom for a DECLARED coded-answer→stance mapping rule. `basis` is the rule
        id the converter stamped (e.g. 'map:mobility_stance_map@v1:Preference_tolls...'). The rule is a
        first-class, inspectable atom — the reading is declared and disputable, never implicit."""
        basis = (basis or "").strip()
        alias = "delib:maprule:" + re.sub(r"[^A-Za-z0-9_.@:-]+", "_", basis)[:160]
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        key = self.cortex.put_chunk(
            content=basis,
            meta={"type": "delib_maprule", "provenance": "mapping", "rule": basis,
                  "created_at": time.time()},
            author=self._author(), scopes=self._scopes())
        try:
            self.cortex.set_alias(key, alias)
        except Exception:
            pass
        return key

    def _mapped_stance(self, response_key: str) -> Tuple[str, str]:
        """The DECLARED stance of a mapped (coded-answer) response, or ('','') for a free-text one.
        Reads the delib:mapped_stance / delib:mapped_by links written at ingest — never re-derives."""
        stance = ""
        rule = ""
        for l in (self.cortex.get_adjacent_links(response_key, "delib:mapped_stance") or []):
            dst = l.get("dst") if isinstance(l, dict) else (l[0] if isinstance(l, (list, tuple)) else None)
            if dst:
                stance = str((self.cortex.get_meta(dst) or {}).get("stance") or
                             self.cortex.get_chunk(dst) or "").strip()
                break
        if stance:
            for l in (self.cortex.get_adjacent_links(response_key, "delib:mapped_by") or []):
                dst = l.get("dst") if isinstance(l, dict) else (l[0] if isinstance(l, (list, tuple)) else None)
                if dst:
                    rule = str((self.cortex.get_meta(dst) or {}).get("rule") or
                               self.cortex.get_chunk(dst) or "").strip()
                    break
        return stance, rule

    def _translation_atom(self, text_en: str, response_key: str) -> str:
        """Mint the English translation as a SECONDARY, provenance=inferred atom that PROJECTS the
        original (the operand). Linked text_en --delib:translates--> the original response, so a later
        check can ask whether an apparent disagreement is real or a translation artifact."""
        key = self.cortex.put_chunk(
            content=text_en,
            meta={"type": "translation", "provenance": "inferred", "kind": "projection:translation",
                  "language": "en", "translation_of": response_key, "created_at": time.time()},
            author=self._author(), scopes=self._scopes())
        try:
            self.cortex.set_alias(key, f"text:en:{response_key[:8]}")
        except Exception:
            pass
        self.cortex.put_link(key, response_key, "delib:translates", author=self._author())
        return key

    def _response_lang(self, response_key: str, primary: str) -> str:
        """The declared language of a response (delib:in_language link), else a detected floor."""
        for l in (self.cortex.get_adjacent_links(response_key, "delib:in_language") or []):
            dst = l.get("dst") if isinstance(l, dict) else (l[0] if isinstance(l, (list, tuple)) else None)
            if dst:
                al = self._alias_of(dst)
                if al.startswith("language:"):
                    return al.split(":", 1)[1]
        return self._detect_lang(primary)

    def _translation_pair(self, response_key: str) -> Tuple[str, str]:
        """(English translation text, translation atom key) for a response, if one was ingested
        (incoming delib:translates). ('', '') when the original has no translation-projection."""
        try:
            for item in (self.cortex.get_incoming_links(response_key, "delib:translates") or []):
                src = item.get("src") if isinstance(item, dict) else (item[0] if isinstance(item, (list, tuple)) else None)
                if src:
                    return (self.cortex.get_chunk(src) or ""), src
        except Exception:
            pass
        return "", ""

    # ── 原票 — the original FULL TEXT as a first-class atom (the analysis target) ──
    def _source_atom(self, full_text: str, response_key: str, language: str, rid: str) -> str:
        """Mint the original FULL TEXT (原票 — the complete submission, longer than the feed comment)
        as a FIRST-CLASS atom: verbatim, provenance=external (raw primary source, NOT inferred), locale
        tagged, aliased `text:orig:<resp>`. Linked `response --delib:source--> 原票`, so the full text is
        the analysis target and the provenance chain reaches the actual source record. No auto-
        translation is ever performed here — the original is kept as-is."""
        key = self.cortex.put_chunk(
            content=full_text,
            meta={"type": "original_source", "provenance": "external", "kind": "primary_record",
                  "language": (language or "und"), "source_of": response_key, "respondent": rid,
                  "created_at": time.time()},
            author=self._author(), scopes=self._scopes())
        try:
            self.cortex.set_alias(key, f"text:orig:{response_key[:8]}")
        except Exception:
            pass
        self.cortex.put_link(response_key, key, "delib:source", author=self._author())
        return key

    def _source_pair(self, response_key: str) -> Tuple[str, str]:
        """(full original text, 原票 atom key) for a response, if a full-text source was ingested
        (outgoing delib:source). ('', '') when only the short feed comment exists."""
        for l in (self.cortex.get_adjacent_links(response_key, "delib:source") or []):
            dst = l.get("dst") if isinstance(l, dict) else (l[0] if isinstance(l, (list, tuple)) else None)
            if dst:
                return (self.cortex.get_chunk(dst) or ""), dst
        return "", ""

    def _analysis_text(self, response_key: str, primary: str) -> str:
        """The text stance analysis reads: the FULL original (原票) when one was imported, else the
        response's own operand. Deeper analysis works on the complete submission, not a snippet."""
        full, _ = self._source_pair(response_key)
        return full.strip() or primary

    def _response_translation(self, response_key: str) -> str:
        """The English translation text of a response, if one was ingested (incoming delib:translates)."""
        return self._translation_pair(response_key)[0]

    def _survey_responses(self, survey_id: str) -> List[Dict[str, Any]]:
        """Read a survey's responses as [{key, answer, question_id, respondent}] (scope-filtered)."""
        allowed = self.allowed_scopes
        members = self.cortex.get_collection_members(f"set:survey:{survey_id}:responses") or []
        out: List[Dict[str, Any]] = []
        for rk in members:
            if allowed and not self.cortex.check_access(rk, allowed):
                continue
            m = self.cortex.get_meta(rk) or {}
            if m.get("type") != "survey_response":
                continue
            answer = m.get("answer")
            text = str(answer) if answer is not None and str(answer).strip() else (self.cortex.get_chunk(rk) or "")
            out.append({"key": rk, "answer": text, "question_id": m.get("question_id", ""),
                        "respondent": m.get("respondent_atom", "")})
        return out

    def _survey_frame(self, survey_id: str) -> Tuple[str, str]:
        """(title, first-question text) — the deliberation subject."""
        sm = self.cortex.get_meta(survey_id) or {}
        title = sm.get("title") or "public consultation"
        q = ""
        qs = self.cortex.get_collection_members(f"set:survey:{survey_id}:questions") or []
        if qs:
            q = (self.cortex.get_chunk(qs[0]) or "").strip()
        return title, q

    @staticmethod
    def _classify(text: str) -> str:
        t = (text or "").lower()
        sup = len(_RE_SUPPORT.findall(t))
        opp = len(_RE_OPPOSE.findall(t))
        cond = bool(_RE_CONDITIONAL.search(t))
        if sup == 0 and opp == 0:
            return "conditional" if cond else "neutral"
        if sup > 0 and opp > 0:
            return "conditional"          # genuinely two-sided
        lean = "support" if sup > opp else "oppose"
        return "conditional" if cond else lean

    def _classify_response(self, response_key: str, primary: str) -> Tuple[str, str, bool]:
        """Language-aware stance of a response, read from the FULL original (原票) when one was imported
        — deeper analysis works on the complete submission, not a snippet. When the text is non-English
        the classifier reads the authority's English translation-projection instead (never an
        auto-translation), so a later check can ask whether an apparent disagreement is real or a
        translation artifact. Non-English with NO translation is kept HONESTLY as `untranslated` — NOT
        forced into English, and NOT asserted to be `neutral` (a reading we did not make). It forms no
        conclusion. Returns (stance, language, floored)."""
        text = self._analysis_text(response_key, primary)     # the 原票 full text when present
        lang = self._response_lang(response_key, text)
        # a MAPPED voice carries its DECLARED stance — the lexicon never reads a coded answer label
        # (it would fabricate `neutral` from "No preferences"). no_reading stays its own honest state.
        mapped, _rule = self._mapped_stance(response_key)
        if mapped:
            return mapped, lang, False
        if lang == "en":
            return self._classify(text), lang, False
        trans = self._response_translation(response_key)       # authority translation only — no auto-MT
        if trans:
            return self._classify(trans), lang, False
        return _UNTRANSLATED, lang, True

    # ── stage 0 — multi-locale ingestion (original = operand, translation = projection) ──
    def _open_survey_q(self, survey: str) -> Tuple[Any, str]:
        """Resolve a survey → (opened SurveyConcept, first-question key). Shared by feed + ingest."""
        sm = self.cortex.get_meta(survey) or {}
        if sm.get("concept") != "survey":
            raise RuntimeError(f"'{survey[:12]}' is not a survey root.")
        qs = self.cortex.get_collection_members(f"set:survey:{survey}:questions") or []
        if not qs:
            raise RuntimeError("survey has no question — add one (survey.q.add) before ingesting.")
        from app.concepts.survey import SurveyConcept
        sv = SurveyConcept(self.session)
        sv.op_open(survey_id=survey)
        return sv, qs[0]

    def _ingest_one(self, sv, qkey: str, original: str, text_en: str, language: str,
                    rid: str, full_text: str = "", stance: str = "",
                    stance_basis: str = "", attachment_url: str = "") -> Tuple[str, str, bool, bool]:
        """Ingest ONE feedback: original = primary-source response atom; text_en = linked translation-
        projection; language tagged. When `full_text` (the 原票 — the complete submission) is supplied,
        it is minted as a FIRST-CLASS atom linked `delib:source` and becomes the analysis target. No
        auto-translation ever happens here. Returns (response_key, language, translated?, has_full?).
        The single shared primitive behind delib.feed (CLI, one record) and delib.ingest (RPC, batch)."""
        original = (original or "").strip()
        ratom = sv.op_add_respondent(respondent_id=rid)["respondent_atom"]
        resp = sv.op_add_response(question_id=qkey, respondent_atom=ratom, answer=original)["response_id"]
        lang = str(language or self._detect_lang(original)).lower()
        self.cortex.put_link(resp, self._lang_atom(lang), "delib:in_language", author=self._author())
        # 原票 REFERENCE (not ingest): a locator to the complete submission (an attachment/PDF) hosted at
        # the source. Provenance metadata only — the document text is never fetched or stored. The record
        # view links to it so a reader can see it exists and open it.
        attachment_url = (attachment_url or "").strip()
        if attachment_url:
            self.cortex.set_meta(resp, "attachment_url", attachment_url)
        has_full = False
        full_text = (full_text or "").strip()
        if full_text:
            self._source_atom(full_text, resp, lang, rid)     # the 原票 as a first-class atom
            has_full = True
        translated = False
        text_en = (text_en or "").strip()
        if text_en and text_en != original:
            self._translation_atom(text_en, resp)
            translated = True
        # A MAPPED voice: the stance is DECLARED by a coded-answer→stance mapping rule, never read
        # from the text (the lexicon would fabricate a reading from an answer label). The rule itself
        # is a first-class atom, so every mapped stance is traceable to the exact declared reading.
        stance = (stance or "").strip().lower()
        if stance:
            if stance not in _STANCES + (_NO_READING,):
                raise ValueError(f"mapped stance '{stance}' not in {_STANCES + (_NO_READING,)}")
            if not (stance_basis or "").strip():
                raise ValueError("a mapped stance requires stance_basis=<declared rule id> — "
                                 "an undeclared mapping is a fabricated reading.")
            self.cortex.put_link(resp, self._stance_atom(stance), "delib:mapped_stance",
                                 author=self._author())
            self.cortex.put_link(resp, self._maprule_atom(stance_basis), "delib:mapped_by",
                                 author=self._author())
        return resp, lang, translated, has_full

    def op_feed_one(self, survey: str = "", text: str = "", text_en: str = "",
                    language: str = "", respondent: str = "", full_text: str = "",
                    stance: str = "", stance_basis: str = "", attachment_url: str = "") -> Dict[str, Any]:
        """[delib.feed] Ingest ONE feedback from the CLI (the CLI-native ingest, like survey.ans): the
        ORIGINAL `text` is the primary-source atom (一次資料); `full_text` (optional) is the complete
        submission (原票) minted as a first-class atom + the analysis target; `text_en` is the
        authority's linked translation-projection (never auto-translation); `language` is the ISO
        locale. Keeps the whole flow runnable as a CLI command sequence."""
        survey = (survey or "").strip()
        if not (text or "").strip():
            raise ValueError('delib.feed requires text="…original…".')
        sv, qkey = self._open_survey_q(survey)
        rid = str(respondent or "").strip() or f"r_{self._author()}_{int(time.time()*1000)}"
        resp, lang, translated, has_full = self._ingest_one(sv, qkey, text, text_en, language, rid,
                                                            full_text, stance=stance,
                                                            stance_basis=stance_basis,
                                                            attachment_url=attachment_url)
        return {"status": "fed", "survey_id": survey, "response_id": resp,
                "language": lang, "translated": translated, "full_text": has_full}

    def op_ingest(self, survey: str = "", records: Any = None, question: str = "") -> Dict[str, Any]:
        """[delib.ingest] Ingest feedback into a survey with the ORIGINAL-language text as the
        PRIMARY-SOURCE atom (一次資料) and the English machine-translation as a linked, secondary
        `provenance=inferred` projection. Each record: {respondent_id|feedback_id, text (original),
        text_en (optional), language (optional, ISO 639-1)}. This is the multi-locale entry point: the
        original is the operand kept for the record; translation only routes classification."""
        recs = records if isinstance(records, list) else []
        if not recs:
            raise ValueError("delib.ingest requires records=[{text, respondent_id, [text_en], [language]}].")
        return self.import_records(recs, into=(survey or "").strip())

    # ── the model-agnostic import contract (kernel io.ingest calls this) ──────────
    def import_records(self, records: List[Dict[str, Any]], into: str = "",
                       mapping: Dict[str, str] = None, **opts) -> Dict[str, Any]:
        """[Importable] Ingest raw feedback records into the survey named by `into`, keeping each
        ORIGINAL text as the primary-source atom (一次資料) and text_en as a linked translation-
        projection. Field remap via `mapping` (e.g. text:body, language:lang). This is what
        `io.ingest model=delib into=<survey> (path=|text=|records=)` routes to — so multi-locale
        feedback flows in through the GENERAL import pipeline, no delib-specific transport needed."""
        into = (into or "").strip()
        if not into:
            raise ValueError("delib import needs into=<survey id> (the survey the feedback answers).")
        sv, qkey = self._open_survey_q(into)
        by_lang: Dict[str, int] = {}
        translated = 0
        with_full = 0
        for i, rec in enumerate(records):
            original = self._mapped(rec, mapping, "text", "text_en", "body")
            if not original.strip():
                continue
            rid = self._mapped(rec, mapping, "respondent_id", "feedback_id", "respondent",
                               default=f"r{i:04d}")
            # 原票: the complete original submission, when the acquisition supplied it
            full = self._mapped(rec, mapping, "full_text", "source_text", "document", "attachment_text")
            _, lang, tr, hf = self._ingest_one(sv, qkey, original,
                                               self._mapped(rec, mapping, "text_en", "translation"),
                                               self._mapped(rec, mapping, "language", "lang"), rid, full,
                                               stance=self._mapped(rec, mapping, "stance", "stance_mapped"),
                                               stance_basis=self._mapped(rec, mapping, "stance_basis",
                                                                         "mapping_rule"),
                                               attachment_url=self._mapped(rec, mapping, "attachment_url",
                                                                           "attachment", "source_url"))
            by_lang[lang] = by_lang.get(lang, 0) + 1
            translated += 1 if tr else 0
            with_full += 1 if hf else 0
        return {"status": "ingested", "survey_id": into, "count": sum(by_lang.values()),
                "by_language": by_lang, "translated": translated, "with_full_text": with_full,
                "languages": sorted(by_lang)}

    # ── stage 1 — aggregate a survey by stance ───────────────────────────────────
    def op_aggregate(self, survey: str = "", by: str = "stance") -> Dict[str, Any]:
        """[delib.aggregate] Group a survey's feedback into stance groups (support / oppose /
        conditional / neutral) via the Aggregation model, with count + share measures and a
        net-stance analysis edge. Returns the aggregation id and the breakdown."""
        survey = (survey or "").strip()
        if not survey:
            raise ValueError("delib.aggregate requires survey=<id>.")
        sm = self.cortex.get_meta(survey) or {}
        if sm.get("concept") != "survey":
            raise RuntimeError(f"'{survey[:12]}' is not a survey root.")

        responses = self._survey_responses(survey)
        if not responses:
            raise RuntimeError("survey has no accessible responses to aggregate.")

        buckets: Dict[str, List[str]] = {s: [] for s in _STANCES}
        untranslated: List[str] = []          # non-English, no translation — kept honestly, not read
        no_reading: List[str] = []            # coded answers the mapping declares unreadable
        by_language: Dict[str, int] = {}
        via_translation = 0
        via_mapping = 0
        floored = 0
        for r in responses:
            stance, lang, floor = self._classify_response(r["key"], r["answer"])
            if self._mapped_stance(r["key"])[0]:
                via_mapping += 1              # stance declared by a mapping rule, not read from text
            if stance == _UNTRANSLATED:
                untranslated.append(r["key"])   # held aside — forms no stance, no conclusion
            elif stance == _NO_READING:
                no_reading.append(r["key"])     # held aside — the mapping made no reading
            else:
                buckets[stance].append(r["key"])
            by_language[lang] = by_language.get(lang, 0) + 1
            if floor:
                floored += 1
            elif lang != "en" and not self._mapped_stance(r["key"])[0]:
                via_translation += 1

        from app.concepts.aggregation import AggregationConcept
        agg = AggregationConcept(self.session)
        agg_id = agg.op_new(source_id=survey)["aggregation_id"]

        total = len(responses)
        for r in responses:
            agg.op_add_unit(unit_id=r["key"])

        group_of: Dict[str, str] = {}
        breakdown: Dict[str, int] = {}
        for stance in _STANCES:
            keys = buckets[stance]
            if not keys:
                continue
            gid = agg.op_add_group(label=stance, members=keys)["group_id"]
            group_of[stance] = gid
            breakdown[stance] = len(keys)
            agg.op_add_measure(group_id=gid, key="count", value=len(keys))
            agg.op_add_measure(group_id=gid, key="share", value=round(len(keys) / total, 4))

        # untranslated = collected input we did not read (no translation) — kept as its OWN honest
        # group so the record-level views can show the original, but it forms NO stance/conclusion
        # and is excluded from the dominant/net computation below.
        if untranslated:
            gid = agg.op_add_group(label=_UNTRANSLATED, members=untranslated)["group_id"]
            group_of[_UNTRANSLATED] = gid
            breakdown[_UNTRANSLATED] = len(untranslated)
            agg.op_add_measure(group_id=gid, key="count", value=len(untranslated))
            agg.op_add_measure(group_id=gid, key="share", value=round(len(untranslated) / total, 4))

        # no_reading = coded answers whose DECLARED mapping makes no reading ("Don't know",
        # "No preferences") — same honesty contract as untranslated: counted, visible, its own group,
        # but NO stance, NO cluster, NO conclusion, excluded from dominant/net.
        if no_reading:
            gid = agg.op_add_group(label=_NO_READING, members=no_reading)["group_id"]
            group_of[_NO_READING] = gid
            breakdown[_NO_READING] = len(no_reading)
            agg.op_add_measure(group_id=gid, key="count", value=len(no_reading))
            agg.op_add_measure(group_id=gid, key="share", value=round(len(no_reading) / total, 4))

        # net-stance analysis: support ↔ oppose, score = (support − oppose) / total
        if "support" in group_of and "oppose" in group_of:
            net = round((breakdown.get("support", 0) - breakdown.get("oppose", 0)) / total, 4)
            agg.op_add_analysis(src_group=group_of["support"], dst_group=group_of["oppose"],
                                relation="net_stance", score=net)

        stance_breakdown = {s: n for s, n in breakdown.items() if s not in (_UNTRANSLATED, _NO_READING)}
        dominant = max(stance_breakdown, key=stance_breakdown.get) if stance_breakdown else "neutral"
        net_score = round((breakdown.get("support", 0) - breakdown.get("oppose", 0)) / total, 4)
        logger.info("[delib] aggregated survey %s → %s (%d responses, langs=%s)",
                    survey[:8], breakdown, total, by_language)
        return {"status": "aggregated", "aggregation_id": agg_id, "survey_id": survey,
                "total": total, "breakdown": breakdown, "dominant": dominant, "net_score": net_score,
                "groups": group_of, "by_language": by_language, "via_translation": via_translation,
                "via_mapping": via_mapping, "floored": floored}

    # ── stage 2 — project the aggregation into a concept-labo field ──────────────
    def op_to_labo(self, agg: str = "", title: str = "") -> Dict[str, Any]:
        """[delib.to_labo] Project a stance aggregation into a Concept-Laboratory field as
        DISAGREEMENT-AS-DATA: a master thesis + hypothesis (the consultation question), one cluster per
        stance (feedback as references — never copies), and — for every substantial stance — a
        COMPETING TRAJECTORY that shares the initial family, transitions to its own destination family,
        and closes in its OWN first-class conclusion (support→affirm, oppose→negate, conditional→mixed).
        A first-class TENSION holds between support and oppose. Multiple conclusions COEXIST (the
        non-forcing principle) — the projection reads them as parallel chronon trajectories. Returns
        the field id, the clusters, the coexisting conclusions, and the trajectories."""
        agg = (agg or "").strip()
        am = self.cortex.get_meta(agg) or {}
        if am.get("concept") != "aggregation":
            raise RuntimeError(f"'{agg[:12]}' is not an aggregation root.")
        survey_id = am.get("source_id", "")
        s_title, question = self._survey_frame(survey_id) if survey_id else ("public consultation", "")

        groups = self._agg_groups(agg)                 # [{group_id, label, members:[...]}]
        if not groups:
            raise RuntimeError("aggregation has no groups — run delib.aggregate first.")
        counts = {g["label"]: len(g["members"]) for g in groups}
        members_of = {g["label"]: g["members"] for g in groups}
        total = sum(counts.values()) or 1

        from app.concepts.clab import ClabConcept
        clab = ClabConcept(self.session)
        field_title = (title or "").strip() or f"Public consultation — {s_title}"
        field = clab.op_new(title=field_title)
        field_key = field["key"]

        subject = question or s_title
        clab.op_master_thesis(text=f"Aggregate the public's stance on: {subject}")
        hyp_id = clab.op_hypothesize(text=f"The public supports: {subject}")["id"]

        # the shared initial family = all collected public input (the fork point for competing lanes)
        fam_in = clab.op_family_new(name=f"Collected public input — {s_title}", stage="initial")["id"]

        # each substantial stance becomes a cluster + a competing trajectory + its own conclusion.
        clusters: Dict[str, str] = {}
        conclusions: List[Dict[str, str]] = []
        trajectories: List[str] = []
        for stance in _STANCES:
            members = members_of.get(stance, [])
            if not members:
                continue
            share = round(100 * len(members) / total)
            cl = clab.op_cluster_new(name=f"{stance} · {len(members)} ({share}%)")["id"]
            clusters[stance] = cl
            clab.op_cluster_add(cluster=cl, members=",".join(members))
            clab.op_family_add(family=fam_in, members=",".join(members))   # raw input in the initial family

            if stance == "neutral":
                continue        # non-committal (incl. the multi-locale floor) — no trajectory/conclusion

            # a competing trajectory: initial family → this stance's destination family
            fam_out = clab.op_family_new(name=f"{stance} reading — {s_title}", stage="destination")["id"]
            clab.op_family_add(family=fam_out, member=cl)
            clab.op_family_next(**{"from": fam_in, "to": fam_out})
            traj = clab.op_theory_new(name=f"{stance} trajectory")["id"]
            clab.op_theory_path(theory=traj, family=fam_in)
            clab.op_theory_path(theory=traj, family=fam_out)
            trajectories.append(traj)

            # the stance is decisive for its own reading (proof if pro-hypothesis, turning if against)
            rationale = f"{stance}: {len(members)}/{total} of collected feedback"
            if stance == "support":
                clab.op_key_proof(cluster=cl, hypothesis=hyp_id, rationale=rationale)
            else:
                clab.op_turning_point(cluster=cl, hypothesis=hyp_id, rationale=rationale)

            concl = clab.op_conclude(hypothesis=hyp_id, judgement=_POLARITY[stance], rationale=rationale)
            conclusions.append({"stance": stance, "id": concl["id"], "judgement": _POLARITY[stance]})

        # untranslated feedback IS collected input — keep it in the initial family as raw input, but
        # give it NO reading (no cluster/trajectory/conclusion). Honest: collected, not read.
        untranslated_members = members_of.get(_UNTRANSLATED, [])
        if untranslated_members:
            clab.op_family_add(family=fam_in, members=",".join(untranslated_members))
        # no_reading (mapped coded answers the rule declares unreadable) — same contract:
        # collected input in the initial family, no cluster, no trajectory, no conclusion.
        no_reading_members = members_of.get(_NO_READING, [])
        if no_reading_members:
            clab.op_family_add(family=fam_in, members=",".join(no_reading_members))

        # first-class tension between support and oppose — disagreement is DATA, not noise to resolve.
        tension_id = ""
        if "support" in clusters and "oppose" in clusters:
            tension_id = clab.op_tension(left=clusters["support"], right=clusters["oppose"],
                                         kind="stance_conflict")["id"]

        stance_counts = {s: n for s, n in counts.items() if s not in (_UNTRANSLATED, _NO_READING)}
        dominant = max(stance_counts, key=stance_counts.get) if stance_counts else "neutral"
        net = round((counts.get("support", 0) - counts.get("oppose", 0)) / total, 4)

        # provenance: aggregation --delib:projects--> clab field
        try:
            self.cortex.put_link(agg, field_key, "delib:projects", author=self._author())
        except Exception:
            pass

        return {"status": "projected", "labo_id": field["id"], "labo_key": field_key,
                "field_title": field_title, "clusters": clusters, "conclusions": conclusions,
                "trajectories": trajectories, "tension": tension_id,
                # the dominant stance is a HEADLINE, not the answer — conclusions coexist (non-forcing)
                "judgement": _POLARITY.get(dominant, "undetermined"), "dominant": dominant,
                "net_score": net, "counts": counts}

    # ── stage 3 — post the conclusion into a society for deliberation ────────────
    def op_to_society(self, labo: str = "", society: str = "", group: str = "", cast: str = "",
                      space: str = "", name: str = "") -> Dict[str, Any]:
        """[delib.to_society] Post a labo field's outcome into a society: a framing utterance, one
        PROPOSAL per stance (for the society to deliberate / vote / decide), and the aggregated
        conclusion. Links the field --delib:deliberates--> the society. Requires an owned cast."""
        from app.concepts.clab import ClabConcept
        from lib.akasha.api.concepts import model as _model

        clab = ClabConcept(self.session)
        clab.op_open(id=labo)                          # mount the field (by alias or key)
        summary = clab.op_status()
        field_title = summary.get("title", "public consultation")
        # pull ALL coexisting conclusions + clusters back out of the field (disagreement-as-data:
        # every competing verdict is posted, never collapsed to a single "answer").
        conclusions = clab.op_conclusion_compare().get("conclusions", [])
        clusters = [r for r in clab._rows(kind="cluster")]

        soc = _model(self.session, "society")
        # a "society" IS a (group, space); the user's society=<name> is the space/channel name. Forward
        # only group + space to the society ops (their `society=` param means a "gid/name" id — passing
        # a bare space name there would be mis-read as the group).
        channel = (space or society or name or "").strip()
        common = {"cast": cast, "group": group, "space": channel}
        posted: List[str] = []

        framing = soc.op_say(text=f"[Public consultation] {field_title} — collected feedback, "
                                  f"competing views kept side by side.", **common)
        posted.append(framing["key"])

        for c in clusters:
            head = (c.get("text") or c.get("id", "")).strip()
            p = soc.op_propose(text=f"Stance cluster: {head}", step="deliberate", **common)
            posted.append(p["key"])

        # post EACH coexisting conclusion (support→affirm, oppose→negate, conditional→mixed) as its own
        # utterance — the non-forcing principle made visible in the society feed.
        for c in conclusions:
            verdict = c.get("polarity", "undetermined")
            u = soc.op_say(text=f"[Reading · {verdict}] {c.get('rationale', '')}", **common)
            posted.append(u["key"])
        if len(conclusions) > 1:
            posted.append(soc.op_say(
                text=f"[Note] {len(conclusions)} competing readings coexist — this consultation is not "
                     f"reduced to one verdict.", **common)["key"])

        # provenance: clab field --delib:deliberates--> society
        gid, sname = soc.resolve_society(group, channel)
        society_key = soc.society_key(gid, sname)
        try:
            if society_key:
                self.cortex.put_link(summary.get("id") or labo, society_key,
                                     "delib:deliberates", author=self._author())
        except Exception:
            pass

        return {"status": "deliberating", "society_id": soc.society_id(gid, sname), "posted": posted,
                "proposals": len(clusters), "conclusions": [c.get("polarity") for c in conclusions]}

    # ── one-shot workflow ────────────────────────────────────────────────────────
    def op_pipeline(self, survey: str = "", society: str = "", group: str = "", cast: str = "",
                    space: str = "", name: str = "", title: str = "") -> Dict[str, Any]:
        """[delib.pipeline] Run the whole flow: aggregate → to_labo → to_society. The CLI entrypoint
        for the public deliberation experiment."""
        a = self.op_aggregate(survey=survey)
        b = self.op_to_labo(agg=a["aggregation_id"], title=title)
        c = {}
        if (society or group):
            c = self.op_to_society(labo=b["labo_key"], society=society, group=group, cast=cast,
                                   space=space, name=name)
        return {"status": "done", "survey_id": survey, "aggregation_id": a["aggregation_id"],
                "breakdown": a["breakdown"], "labo_id": b["labo_id"], "labo_key": b["labo_key"],
                "judgement": b["judgement"], "dominant": b["dominant"], "net_score": b["net_score"],
                "society": c.get("society_id", ""), "posted": c.get("posted", [])}

    def op_show(self, labo: str = "") -> Dict[str, Any]:
        """[delib.show] Summarise a deliberation field: status + conclusion(s)."""
        from app.concepts.clab import ClabConcept
        clab = ClabConcept(self.session)
        clab.op_open(id=labo)
        return {"status": "ok", "field": clab.op_status(),
                "conclusions": clab.op_conclusion_compare()}

    def op_locales(self, agg: str = "") -> Dict[str, Any]:
        """[delib.locales] Per-stance locale composition + translation reliance — the quantitative feed
        for the TRANSLATION-ARTIFACT check ("is this stance real disagreement, or does it rest on
        translated text?"). For each stance group: the language histogram, how many members were
        classified via an English translation (non-English originals), and how many floored (non-English
        with no translation). A stance that is mostly `via_translation` is a flag to inspect before
        trusting the disagreement. Read-only — the input for the visualization's locale panels."""
        agg = (agg or "").strip()
        if (self.cortex.get_meta(agg) or {}).get("concept") != "aggregation":
            raise RuntimeError(f"'{agg[:12]}' is not an aggregation root.")
        by_stance: Dict[str, Any] = {}
        overall_lang: Dict[str, int] = {}
        overall_via = 0
        for g in self._agg_groups(agg):
            langs: Dict[str, int] = {}
            via = 0
            floored = 0
            for rk in g["members"]:
                primary = str((self.cortex.get_meta(rk) or {}).get("answer") or self.cortex.get_chunk(rk) or "")
                lang = self._response_lang(rk, primary)
                langs[lang] = langs.get(lang, 0) + 1
                overall_lang[lang] = overall_lang.get(lang, 0) + 1
                if lang != "en":
                    if self._response_translation(rk):
                        via += 1
                        overall_via += 1
                    else:
                        floored += 1
            total = len(g["members"])
            by_stance[g["label"]] = {
                "total": total, "languages": langs, "via_translation": via, "floored": floored,
                # a headline the panel can badge: share of this stance resting on translated text
                "translation_reliance": round(via / total, 4) if total else 0.0}
        return {"status": "ok", "aggregation_id": agg, "by_stance": by_stance,
                "overall": {"languages": overall_lang, "via_translation": overall_via}}

    def op_voices(self, agg: str = "") -> Dict[str, Any]:
        """[delib.voices] The per-RESPONSE record behind an aggregation — the record-level feed that
        `delib.locales` only counts. For each stance group, every member response as
        {id, respondent, language, original, translation, translation_atom, via_translation, floored,
        stance, polarity, source_atom}. The ORIGINAL text is the operand of record (一次資料);
        `translation` is the linked English projection, kept DISTINCT so a reader can audit whether an
        interpretation rests on translated text (the Original↔Translation parallel reading, the Tension
        view, the Locale lens, the Provenance view all read this). Read-only — it re-reads what the CLI
        already decided; it never re-classifies, re-detects language, or re-translates."""
        agg = (agg or "").strip()
        if (self.cortex.get_meta(agg) or {}).get("concept") != "aggregation":
            raise RuntimeError(f"'{agg[:12]}' is not an aggregation root.")
        voices: List[Dict[str, Any]] = []
        langs_seen: Dict[str, int] = {}
        for g in self._agg_groups(agg):
            stance = g["label"]
            polarity = _POLARITY.get(stance, "undetermined")
            for rk in g["members"]:
                m = self.cortex.get_meta(rk) or {}
                original = str(m.get("answer") or self.cortex.get_chunk(rk) or "")
                full, full_atom = self._source_pair(rk)          # the 原票 full text, if imported
                lang = self._response_lang(rk, full or original)
                trans, trans_atom = self._translation_pair(rk)
                via = bool(lang != "en" and trans)
                floored = bool(lang != "en" and not trans)
                mstance, mrule = self._mapped_stance(rk)
                langs_seen[lang] = langs_seen.get(lang, 0) + 1
                voices.append({
                    "id": rk, "respondent": m.get("respondent_atom", ""),
                    "via_mapping": bool(mstance), "mapping_rule": mrule,
                    "language": lang, "original": original,
                    # the full original submission (原票) is the analysis target when present; the short
                    # `original` above is the feed comment. full_atom is traceable via clab.trace.
                    "full_text": full, "full_text_atom": self._alias_of(full_atom) if full_atom else "",
                    # 原票 REFERENCE — a locator to the complete submission (attachment/PDF) at the source,
                    # shown as a link in the record view. Provenance only; the document is not ingested.
                    "attachment_url": m.get("attachment_url") or "",
                    "translation": trans,
                    "translation_atom": self._alias_of(trans_atom) if trans_atom else "",
                    "via_translation": via, "floored": floored,
                    "stance": stance, "polarity": polarity,
                    "source_atom": self._alias_of(rk)})
        return {"status": "ok", "aggregation_id": agg, "count": len(voices),
                "languages": langs_seen, "voices": voices}

    # ── aggregation read-back ─────────────────────────────────────────────────────
    def _agg_groups(self, agg_id: str) -> List[Dict[str, Any]]:
        """Read an aggregation's groups back as [{group_id, label, members}] (members via agg:member)."""
        allowed = self.allowed_scopes
        out: List[Dict[str, Any]] = []
        for gk in self.cortex.get_collection_members(f"set:agg:{agg_id}:groups") or []:
            if allowed and not self.cortex.check_access(gk, allowed):
                continue
            gm = self.cortex.get_meta(gk) or {}
            members = []
            for l in (self.cortex.get_adjacent_links(gk, "agg:member") or []):
                dst = l.get("dst") if isinstance(l, dict) else (l[0] if isinstance(l, (list, tuple)) else None)
                if dst:
                    members.append(dst)
            out.append({"group_id": gk, "label": gm.get("label", "?"), "members": members})
        # stable stance order
        out.sort(key=lambda g: _STANCES.index(g["label"]) if g["label"] in _STANCES else 99)
        return out
