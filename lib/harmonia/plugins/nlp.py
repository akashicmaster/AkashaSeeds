"""
NLP Analysis Plugin — Multi-Locale, Mixed-Script.

Uses SpaCy when available (auto-installed via Symbiosis.ensure at boot).
Applies script-based segmentation so mixed Japanese/English text routes each
segment to the appropriate language model instead of running both models on
the full string.

Degradation tiers:
  T3  SpaCy + language model loaded          → POS/NER-based trait extraction
  T1  SpaCy absent or model unavailable      → regex tokenizer (_tokenize_basic)
  T0  CJK script detected, no model          → character bigram extraction
"""
import re
import os
import sys
import importlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("Harmonia.NLP")

# ---------------------------------------------------------------------------
# Symbiosis import — use the active api version (has ensure() with auto-pip).
# lib.akasha.symbiosis is the legacy stub used only by legacy code.
# ---------------------------------------------------------------------------
try:
    from api.env_detector import Symbiosis
except ImportError:
    # Fallback if running nlp.py in an isolated context (tests, etc.)
    from lib.akasha.symbiosis import Symbiosis  # type: ignore


# ---------------------------------------------------------------------------
# Script detection — zero dependencies
# ---------------------------------------------------------------------------

# Unicode ranges covering CJK (Chinese/Japanese Kanji), Hiragana, Katakana,
# Hangul (Korean), and CJK Extension blocks.
_CJK_RE = re.compile(
    r'[぀-ヿ'    # Hiragana + Katakana
    r'㐀-䶿'    # CJK Extension A
    r'一-鿿'    # CJK Unified Ideographs
    r'豈-﫿'    # CJK Compatibility Ideographs
    r'가-힯]+'  # Hangul Syllables
)

# Languages whose models are suited for CJK script segments
_CJK_LANGS = frozenset({"ja", "zh", "ko"})

_BASIC_STOP = frozenset({
    "is", "it", "the", "a", "an", "be", "to", "of", "in", "at",
    "what", "he", "she", "this", "that", "your", "my", "but", "and",
    "or", "not", "are", "was", "were", "has", "have", "had", "do",
    "did", "does", "with", "for", "on", "by", "from", "as", "into",
    "we", "you", "they", "i", "me", "its", "our", "his", "her",
})


def _split_by_script(text: str) -> List[tuple]:
    """
    Split *text* into (segment, script_type) pairs where script_type is
    'cjk' or 'latin'.  Consecutive characters of the same script stay
    together; whitespace is treated as part of the preceding segment.

    Example:
        "Icarus flew — イカロス 太陽に近づきすぎた"
        # (Japanese: "Icarus — Icarus approached the sun too closely")
        → [("Icarus flew — ", "latin"), ("イカロス 太陽に近づきすぎた", "cjk")]
    """
    segments: List[tuple] = []
    last_end = 0
    for m in _CJK_RE.finditer(text):
        latin_chunk = text[last_end:m.start()]
        if latin_chunk.strip():
            segments.append((latin_chunk.strip(), "latin"))
        segments.append((m.group(), "cjk"))
        last_end = m.end()
    trailing = text[last_end:].strip()
    if trailing:
        segments.append((trailing, "latin"))
    return segments


def _tokenize_basic(text: str) -> List[str]:
    """Regex tokenizer — always available; handles Latin scripts adequately."""
    seen: set = set()
    result: List[str] = []
    for tok in re.split(r"[\W_]+", text.lower()):
        if len(tok) < 3 or tok.isdigit() or tok in _BASIC_STOP:
            continue
        if tok not in seen:
            seen.add(tok)
            result.append(tok)
    return result


def _tokenize_cjk_basic(text: str) -> List[str]:
    """
    Character bigram extraction for CJK text when no morphological model
    is available.  Single-character CJK ideographs are also kept.
    """
    chars = [c for c in text if _CJK_RE.match(c)]
    bigrams = [chars[i] + chars[i + 1] for i in range(len(chars) - 1)]
    seen: set = set()
    result: List[str] = []
    for tok in bigrams + chars:
        if tok not in seen:
            seen.add(tok)
            result.append(tok)
    return result


# ---------------------------------------------------------------------------
# Main NLP manager class
# ---------------------------------------------------------------------------

class MultiLocaleNLP:
    """
    Multi-locale NLP dispatcher with script-aware segmentation.

    When SpaCy is available, text is split by Unicode script and each segment
    is processed by the model best suited for that script.  This avoids the
    quality degradation that occurs when an English model is applied to CJK
    characters or vice versa.

    Model map can be extended; entries follow {lang_code: spacy_model_name}.
    """

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_map: Dict[str, str] = {
            "en": "en_core_web_sm",
            "ja": "ja_core_news_sm",
            "de": "de_core_news_sm",
            "zh": "zh_core_web_sm",
            "fr": "fr_core_news_sm",
            "es": "es_core_news_sm",
        }
        self.spacy: Optional[Any] = None
        self._checked = False

    def _check_dependencies(self) -> None:
        """Lazy-load SpaCy via Symbiosis.ensure() on first use."""
        if self._checked:
            return
        self._checked = True
        self.spacy = Symbiosis.ensure(
            module_name="spacy",
            package_name="spacy",
            scope="[Plugin: NLP]",
            feature="Advanced Semantic & Temporal Parsing",
        )

    def _load_model(self, lang_code: str) -> Optional[Any]:
        """
        Load and cache the SpaCy model for *lang_code*.
        On OSError (model not yet downloaded) attempts a one-shot
        `python -m spacy download <model>` then retries the load.
        """
        if not self.spacy:
            return None

        if lang_code in self.models:
            return self.models[lang_code]

        model_name = self.model_map.get(lang_code)
        if not model_name:
            return None

        # First attempt
        try:
            self.models[lang_code] = self.spacy.load(model_name)
            return self.models[lang_code]
        except OSError:
            pass

        # Model not downloaded. Honour the operator's opt-out: no network fetch when
        # AKASHA_SKIP_AUTOINSTALL is set — degrade to the regex / CJK-bigram tokenizer
        # silently (T1/T0) instead of blocking on a spacy download.
        if os.environ.get("AKASHA_SKIP_AUTOINSTALL"):
            return None

        # Model not downloaded — try auto-download
        logger.info("[NLP] Model '%s' missing — attempting download…", model_name)
        try:
            import subprocess
            res = subprocess.run(
                [sys.executable, "-m", "spacy", "download", model_name,
                 "--quiet"],
                timeout=120,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if res.returncode != 0:
                err = res.stderr.decode("utf-8", errors="replace").strip()
                logger.warning("[NLP] spacy download '%s' failed: %s", model_name, err)
                return None
            importlib.invalidate_caches()
            self.models[lang_code] = self.spacy.load(model_name)
            logger.info("[NLP] Model '%s' ready.", model_name)
            return self.models[lang_code]
        except Exception as exc:
            logger.warning("[NLP] Could not auto-download '%s': %s", model_name, exc)
            return None

    # -----------------------------------------------------------------------
    # Public extraction API
    # -----------------------------------------------------------------------

    def lemmatize_tokens(self, text: str, lang: str = "en") -> List[tuple]:
        """
        Tokenize and lemmatize *text*.

        Returns [(surface, lemma, lang, morph)] for each content token where
        morph is a dict of Universal Dependencies morphological features
        (e.g. {'Tense': 'Past'}, {'Number': 'Plur'}, {'VerbForm': 'Part'}).
        - T3 (SpaCy available): token.lemma_ + token.morph.to_dict()
        - T1 fallback: (token, token, lang, {}) — surface equals lemma, no morph

        Stopword/length filtering is intentionally absent here; the caller
        (_weave_atom) applies _WEAVE_STOPWORDS against the lemma so the
        filtering policy stays in one place.
        """
        if not text:
            return []

        self._check_dependencies()

        results: List[tuple] = []
        seen: set = set()
        segments = _split_by_script(text)

        for segment, script in segments:
            seg_lang = lang if script == "latin" else "ja"
            nlp_model = self._load_model(seg_lang) if self.spacy else None

            if nlp_model:
                try:
                    doc = nlp_model(segment)
                    for token in doc:
                        if token.is_punct or token.is_space:
                            continue
                        surface = token.text.lower()
                        lemma   = token.lemma_.lower()
                        if lemma and len(lemma) >= 2 and lemma not in seen:
                            seen.add(lemma)
                            morph = token.morph.to_dict() if token.morph else {}
                            results.append((surface, lemma, seg_lang, morph))
                except Exception as exc:
                    logger.debug("[NLP] lemmatize error (lang=%s): %s", seg_lang, exc)
                    # fall through to regex fallback for this segment
                else:
                    continue

            # Regex fallback — surface = lemma, no morph data
            if script == "cjk":
                for tok in _tokenize_cjk_basic(segment):
                    if tok not in seen:
                        seen.add(tok)
                        results.append((tok, tok, seg_lang, {}))
            else:
                import re as _re
                for tok in _re.split(r"[\W_]+", segment.lower()):
                    if len(tok) >= 2 and tok not in seen:
                        seen.add(tok)
                        results.append((tok, tok, seg_lang, {}))

        return results

    def extract_traits(self, text: str, locale_context=None, **kwargs) -> List[str]:
        """
        Extract semantic traits and chronological markers from *text*.

        Processing path:
          1. Split text by Unicode script (CJK vs. Latin).
          2. For each segment, determine which language models are applicable.
          3. Apply the first successfully loaded model for that segment.
          4. Fall back to regex or bigram extraction per segment if no model loads.

        Returns a deduplicated list of trait:* and chrono:aspect:* tags.
        """
        if not text:
            return []

        self._check_dependencies()

        # Derive ordered language preference from session locale context
        if locale_context:
            target_langs = (locale_context.supported
                            if hasattr(locale_context, "supported")
                            else [str(locale_context)])
        else:
            target_langs = ["en"]

        # Normalise lang codes: "en_US" → "en", "ja_JP" → "ja"
        target_langs = [l.split("_")[0].split("-")[0].lower() for l in target_langs]

        all_traits: List[str] = []

        for segment, script in _split_by_script(text):
            traits = self._extract_segment(segment, script, target_langs)
            all_traits.extend(traits)

        return list(dict.fromkeys(all_traits))  # deduplicate, preserve order

    def _extract_segment(self, segment: str, script: str,
                         target_langs: List[str]) -> List[str]:
        """
        Extract traits from a single script-homogeneous segment.
        Tries NLP models in locale-preference order, falls back to basic.
        """
        banned = {
            "is", "it", "the", "a", "an", "be", "to", "of", "in", "at",
            "what's", "he", "she", "this", "that", "your", "my", "but", "and",
        }

        if self.spacy:
            # Build candidate lang list: prefer locale-matching models for this script
            if script == "cjk":
                candidates = [l for l in target_langs if l in _CJK_LANGS]
                if not candidates:
                    candidates = ["ja"]  # default CJK model
            else:
                candidates = [l for l in target_langs if l not in _CJK_LANGS]
                if not candidates:
                    candidates = ["en"]  # default Latin model

            for lang in candidates:
                nlp = self._load_model(lang)
                if not nlp:
                    continue
                try:
                    return self._spacy_extract(nlp, lang, segment, banned)
                except Exception as exc:
                    logger.debug("[NLP] spacy extract error (lang=%s): %s", lang, exc)

        # --- Fallback (no model loaded for this segment) ---
        if script == "cjk":
            return [f"trait:{tok}" for tok in _tokenize_cjk_basic(segment)]
        return [f"trait:{tok}" for tok in _tokenize_basic(segment)]

    @staticmethod
    def _spacy_extract(nlp, lang: str, text: str, banned: set) -> List[str]:
        """Run one SpaCy model on *text* and collect trait/chrono tags."""
        traits: List[str] = []
        doc = nlp(text)
        for token in doc:
            if token.is_stop or token.is_punct or token.is_space or token.like_num:
                continue
            surface = token.text.lower()
            if surface in banned or (len(surface) < 2 and
                                     not re.match(r'[一-鿿]', surface)):
                continue

            if token.pos_ in ("NOUN", "PROPN"):
                traits.append(f"trait:{surface}")

            if token.pos_ in ("VERB", "AUX"):
                if lang == "ja":
                    if token.lemma_ in ("いる", "ある"):
                        traits.append("chrono:aspect:stative")
                    elif token.lemma_ == "た":
                        traits.append("chrono:aspect:perfective")
                    elif token.dep_ == "advcl":
                        traits.append("chrono:aspect:progressive")
                elif lang == "en":
                    if token.tag_ == "VBN":
                        traits.append("chrono:aspect:perfective")
                    elif token.tag_ == "VBG":
                        traits.append("chrono:aspect:progressive")
        return traits


# Global instance
nlp_manager = MultiLocaleNLP()


def register(engine) -> None:
    """Register the NLP extractor with the Harmonia Engine."""
    engine.register_plugin("nlp.extract", nlp_manager.extract_traits)
    logger.info("[Plugin] Registered: nlp.extract (multi-locale, mixed-script)")
