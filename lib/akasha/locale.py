"""
Cognitive Multi-Locale Management.
Akasha operates on a 'Global Mixed-Locale' basis, allowing simultaneous 
processing of multiple languages while respecting user-defined priorities.

[MULTIDIMENSIONAL SCOPE UPDATE]
Languages are now treated as Semantic Scopes (e.g., 'lang:ja', 'lang:en').
This allows the Core database layer to perform ultra-fast hardware-level 
filtering to return only concepts the client can understand, seamlessly 
integrating with the IAM (Identity & Access) scope model.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class LocaleContext:
    """
    Manages the active language stack, fallback chains, and semantic model bindings.
    Now acts as the generator for Language Scopes during graph traversal and weaving.
    """
    primary: str = "en"  # The leading language for UI and initial NLP
    supported: List[str] = field(default_factory=lambda: ["en", "ja"])
    
    # Fallback chains: If a concept isn't clear in 'ja', look it up in 'en'
    fallbacks: Dict[str, str] = field(default_factory=lambda: {"ja": "en", "en": "ja"})
    
    # NLP Model Mapping: Connects ISO codes to physical Spacy/NLP model names.
    model_map: Dict[str, str] = field(default_factory=lambda: {
        "en": "en_core_web_sm",
        "ja": "ja_core_news_sm",
        "de": "de_core_news_sm"
    })

    def set_primary(self, lang_code: str):
        """Sets the primary locale and ensures it is active in the stack."""
        self.primary = lang_code
        if lang_code not in self.supported:
            self.supported.insert(0, lang_code)

    def add_supported(self, lang_code: str):
        """Activates a new language for semantic processing."""
        if lang_code not in self.supported:
            self.supported.append(lang_code)

    def get_model_for(self, lang_code: Optional[str] = None) -> str:
        """Returns the appropriate NLP model name for the given or primary locale."""
        target = lang_code or self.primary
        return self.model_map.get(target, self.model_map.get("en"))

    def get_priority_list(self) -> List[str]:
        """
        Returns an ordered list of locales for sequential lookup/analysis.
        Always starts with the primary locale.
        """
        others = [l for l in self.supported if l != self.primary]
        return [self.primary] + others

    # --- [NEW] Multidimensional Scope Integration ---
    
    def get_language_scopes(self) -> List[str]:
        """
        Generates the Set prefixes (Scopes) for all languages the client understands.
        Can be appended to IdentityManager scopes to filter graph results by language.
        e.g., Returns ['lang:en', 'lang:ja']
        """
        return [f"lang:{code}" for code in self.supported]

    def get_primary_scope(self) -> str:
        """Returns the Scope prefix for the client's preferred language."""
        return f"lang:{self.primary}"

    def extract_language_scope(self, text: str) -> str:
        """
        Detect the language of text from Unicode character ranges (no external deps).
        Non-Latin scripts (CJK, Arabic, Cyrillic, …) are identified by codepoint ranges.
        Latin text falls back to the session's primary locale (the user writes in their
        own language, which is the dominant case).
        Returns a lang: scope tag, e.g. 'lang:ja'.
        """
        if text:
            total = sum(1 for c in text if not c.isspace())
            if total > 0:
                kana     = sum(1 for c in text if '぀' <= c <= 'ヿ')
                cjk      = sum(1 for c in text if '一' <= c <= '鿿')
                hangul   = sum(1 for c in text if '가' <= c <= '힯')
                arabic   = sum(1 for c in text if '؀' <= c <= 'ۿ')
                cyrillic = sum(1 for c in text if 'Ѐ' <= c <= 'ӿ')
                thai     = sum(1 for c in text if '฀' <= c <= '๿')
                devan    = sum(1 for c in text if 'ऀ' <= c <= 'ॿ')

                # Hiragana/Katakana presence is definitive for Japanese
                if kana / total > 0.05 or (kana > 0 and cjk / total > 0.05):
                    return "lang:ja"
                if cjk / total > 0.15:
                    return "lang:zh"
                if hangul / total > 0.1:
                    return "lang:ko"
                if arabic / total > 0.1:
                    return "lang:ar"
                if cyrillic / total > 0.1:
                    return "lang:ru"
                if thai / total > 0.1:
                    return "lang:th"
                if devan / total > 0.1:
                    return "lang:hi"
        # Latin scripts and unknown — use session's primary locale
        return self.get_primary_scope()

    # ------------------------------------------------
    
    def resolve_fallback(self, lang_code: str) -> str:
        """
        Determines which language to use if the current one fails.
        Useful for cross-linguistic semantic weaving.
        """
        return self.fallbacks.get(lang_code, "en")

    def get_context(self) -> dict:
        """Serializes the locale state for Vault storage or RPC transmission."""
        return {
            "primary": self.primary,
            "supported": self.supported,
            "priority_stack": self.get_priority_list(),
            "active_model": self.get_model_for(),
            "language_scopes": self.get_language_scopes()
        }

    def __post_init__(self):
        """Validation to ensure primary is always in supported list."""
        if self.primary not in self.supported:
            self.supported.insert(0, self.primary)
