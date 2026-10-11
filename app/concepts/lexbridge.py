"""
Lexical cross-language bridge (`lex.*`) — build the ONE interlingual link per proto-word.

Akasha's ontology is built around ENGLISH proto-words (祖語). Non-English text yields its own,
ISOLATED proto-words. This model builds the single `foreign_proto --lex:bridge--> english_proto`
link that lets a non-English atom REUSE the whole English graph (the explorer folds the English
neighbourhood + set-bearing senses across the bridge — see ConsciousnessEngine.generate_view). Bridge
the proto-words only; nothing is copied.

The English target comes from an on-demand translation PROVIDER (决定: Wikipedia/Wikidata first, OMW
offline later). Providers are pluggable via AKASHA_BRIDGE_PROVIDER (wikidata | wikipedia):
  • wikidata  — wbsearchentities(word, lang) → Q-id → its English label (language-neutral Q-id = the
    natural cross-language pivot; the same mechanism the wikidata_*_import scripts already use).
  • wikipedia — the article for `word` in `lang` → its `en` interlanguage link title.
A manual `english=`/`to=` overrides the provider (also how a curated list is loaded). Network is done
ONLY in these explicit enrichment ops (never in the write critical path); any failure → no bridge,
returned honestly (never a fabricated translation).
"""
import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from lib.akasha.api.concepts import BaseConcept

logger = logging.getLogger("Harmonia.Concept.LexBridge")

_W, _R = "record", "read"
_BRIDGE_REL = "lex:bridge"
_UA = "AkashaLexBridge/0.1 (https://github.com/henrigrohmann/AkashicTree)"


# ── translation providers (on-demand; return an English word/label or None) ──────────────
def _http_json(url: str, timeout: float = 12.0) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:   # honours HTTPS_PROXY env
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        logger.info("[lex.bridge] fetch failed (%s): %s", url[:60], exc)
        return None


def _wikidata_translate(word: str, lang: str) -> Optional[str]:
    """word@lang → its Wikidata item → the item's English label (Q-id is the language-neutral pivot)."""
    lang = lang or "en"
    q = urllib.parse.quote(word)
    s = _http_json(f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={q}"
                   f"&language={lang}&uselang={lang}&format=json&limit=1&type=item")
    hits = (s or {}).get("search") or []
    if not hits:
        return None
    qid = hits[0].get("id")
    if not qid:
        return None
    e = _http_json(f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={qid}"
                   f"&props=labels&languages=en&format=json")
    return (((e or {}).get("entities") or {}).get(qid, {}).get("labels") or {}).get("en", {}).get("value")


def _wikipedia_translate(word: str, lang: str) -> Optional[str]:
    """The `lang`-Wikipedia article for `word` → its English interlanguage-link title."""
    lang = lang or "en"
    q = urllib.parse.quote(word)
    d = _http_json(f"https://{lang}.wikipedia.org/w/api.php?action=query&titles={q}"
                   f"&prop=langlinks&lllang=en&format=json&redirects=1")
    for page in ((d or {}).get("query", {}).get("pages") or {}).values():
        for ll in page.get("langlinks") or []:
            if ll.get("lang") == "en" and ll.get("*"):
                return ll["*"]
    return None


def _translate(word: str, lang: str) -> Optional[str]:
    prov = (os.environ.get("AKASHA_BRIDGE_PROVIDER") or "wikidata").strip().lower()
    fn = {"wikidata": _wikidata_translate, "wikipedia": _wikipedia_translate}.get(prov, _wikidata_translate)
    try:
        en = fn(word, lang)
        return en.strip() if isinstance(en, str) and en.strip() else None
    except Exception as exc:
        logger.info("[lex.bridge] provider '%s' error: %s", prov, exc)
        return None


class LexBridgeConcept(BaseConcept):
    """Build the one `lex:bridge` link per proto-word (祖語) from an on-demand translation provider."""

    CONCEPT_PREFIX = "lex"
    CONCEPT_METHODS = {
        "bridge":  {"op": "op_bridge", "action": _W, "cli": "lex.bridge", "args": ["word"],
                    "desc": "Bridge a foreign proto-word to its English proto-word (reuse the English "
                            "graph): lex.bridge word=<foreign> [lang=fr] [english=<override>]. "
                            "English comes from the provider (AKASHA_BRIDGE_PROVIDER) unless given."},
        "build":   {"op": "op_build", "action": _W, "cli": "lex.build", "args": ["lang"],
                    "desc": "Batch-bridge foreign proto-words of a language (or a set): "
                            "lex.build lang=fr [set=<name>] [limit=200]"},
        "ls":      {"op": "op_ls", "action": _R, "cli": "lex.ls", "args": [],
                    "desc": "List existing bridges: lex.ls [word=<foreign>]"},
    }

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _author(self):
        return getattr(self.session, "client_id", "system")

    def _proto(self, word: str, lang: str = "") -> Optional[str]:
        """Resolve (or ensure) the proto-word atom for a bare word. Prefers an existing lang-qualified
        proto (word:{lang}:{word}) or the bare alias; else mints one via the engine's proto machinery."""
        word = (word or "").strip()
        if not word:
            return None
        for alias in ([f"word:{lang}:{word}"] if lang else []) + [word]:
            k = self.cortex.resolve_alias(alias)
            if k:
                return k
        ens = getattr(self.cortex, "_ensure_protoword", None)
        return ens(word) if ens else None

    def _alias(self, key: str) -> str:
        al = self.cortex.get_aliases_by_key(key) or []
        return next((a for a in al if ":" not in a), al[0] if al else key[:12])

    def _bridge_dst(self, foreign_key: str) -> List[str]:
        out = []
        for l in (self.cortex.get_magnetic_neighborhood(foreign_key) or []):
            if l.get("rel") == _BRIDGE_REL and l.get("direction") == "out":
                out.append(l["key"])
        return out

    # ── ops ────────────────────────────────────────────────────────────────────────
    def op_bridge(self, word: str = "", lang: str = "", english: str = "", to: str = "") -> Dict[str, Any]:
        """[lex.bridge] Build foreign_proto --lex:bridge--> english_proto for one word. The English
        target is `english`/`to` if given, else the on-demand provider's translation. Idempotent; if no
        translation is found, returns honestly with no bridge (never fabricated)."""
        word = (word or "").strip()
        if not word:
            raise ValueError("lex.bridge requires word=<foreign word>.")
        fk = self._proto(word, lang)
        if not fk:
            raise RuntimeError(f"could not resolve/ensure a proto-word for '{word}'.")
        en_word = (english or to or "").strip() or _translate(word, lang)
        if not en_word:
            return {"status": "no_translation", "word": word, "lang": lang,
                    "provider": os.environ.get("AKASHA_BRIDGE_PROVIDER", "wikidata")}
        ek = self._proto(en_word, "en")
        if not ek or ek == fk:
            return {"status": "no_english_proto", "word": word, "english": en_word}
        if ek in self._bridge_dst(fk):
            return {"status": "exists", "word": word, "english": en_word,
                    "foreign": self._alias(fk), "target": self._alias(ek)}
        self.cortex.put_link(fk, ek, _BRIDGE_REL, author=self._author())
        logger.info("[lex.bridge] %s(%s) --lex:bridge--> %s", word, lang or "?", en_word)
        return {"status": "bridged", "word": word, "lang": lang, "english": en_word,
                "foreign": self._alias(fk), "target": self._alias(ek)}

    def op_build(self, lang: str = "", set: str = "", limit: Any = 200) -> Dict[str, Any]:
        """[lex.build] Batch: bridge foreign proto-words of a language (aliased word:{lang}:*) or the
        members of a set. On-demand provider translation per word; idempotent. Returns counts."""
        lang = (lang or "").strip()
        try:
            lim = max(1, min(int(limit), 5000))
        except (TypeError, ValueError):
            lim = 200
        words: List[tuple] = []       # (word, lang, proto_key)
        if set:
            for mk in (self.cortex.get_collection_members(set.strip()) or [])[:lim]:
                al = self._alias(mk)
                w = al.split(":")[-1]
                words.append((w, lang, mk))
        elif lang:
            # scan the lang-qualified proto namespace ns:word:{lang}
            for mk in (self.cortex.get_collection_members(f"ns:word:{lang}") or [])[:lim]:
                al = self.cortex.get_aliases_by_key(mk) or []
                w = next((a.split(":")[-1] for a in al if a.startswith(f"word:{lang}:")), None) \
                    or (al[0] if al else "")
                if w:
                    words.append((w, lang, mk))
        else:
            raise ValueError("lex.build requires lang= or set=.")
        bridged = exists = none = 0
        for w, lg, _mk in words:
            r = self.op_bridge(word=w, lang=lg)
            st = r.get("status")
            bridged += st == "bridged"
            exists += st == "exists"
            none += st in ("no_translation", "no_english_proto")
        return {"status": "built", "scanned": len(words), "bridged": bridged,
                "already": exists, "no_bridge": none,
                "provider": os.environ.get("AKASHA_BRIDGE_PROVIDER", "wikidata")}

    def op_ls(self, word: str = "") -> Dict[str, Any]:
        """[lex.ls] List bridges. With word=, only that foreign word's bridge(s)."""
        rows: List[Dict[str, str]] = []
        if word.strip():
            fk = self._proto(word.strip())
            for ek in (self._bridge_dst(fk) if fk else []):
                rows.append({"foreign": self._alias(fk), "english": self._alias(ek)})
        return {"status": "ok", "count": len(rows), "bridges": rows}
