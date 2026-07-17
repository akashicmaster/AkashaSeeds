"""
Contexa — Context-Reading Engine.

Pipeline position:
  external source → Contexa.read_*() → kernel write → Weaver (micro) → Contexa.bind_context() (macro)

The Weaver handles micro-level decomposition: word Atoms, protoword links, component sets.
Contexa handles macro-level contextual binding: connecting chunks to the larger structure
they belong to — dialogue threads, survey questions, fetch sessions — using Akasha links
and sets.

Responsibilities:

  1. Web / Wikipedia fetch (fetch, search)
     Bring external content into Akasha as chunks.

  2. Interactive dialogue reading
     When a client answers a question, the answer Atom must be linked to the question Atom
     and to any preconditions (topic, session, earlier turns).  Contexa knows this context
     because it owns the dialogue session — the Weaver does not.

  3. Batch data reading (surveys, CSV, pre-collected datasets)
     Each row/response is read as a contextualised chunk linked back to its question Atom
     and respondent Atom, and added to the appropriate survey collection.
     (Live via the kernel `contexa.ingest` → `ResponseIngestSink`, which calls bind_context
     per response. See docs/for-llm/io-pipeline.md.)

Division of labour:
  Weaver   — micro: word decomposition, protoword links, component: set
  Contexa  — macro: ctx:answers, ctx:topic, ctx:thread links; dialogue: and survey: sets

Pipe position: Contexa is the client session's INPUT side on the I/O pipe (fetch = Source,
ingest = Sink); Jataka is the OUTPUT side; Consciousness is the substrate both flow through.
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("Harmonia.Contexa")


class ContexaEngine:
    """
    Context-reading engine.

    Reads chunks from external sources and, after the Weaver handles word-level
    decomposition, creates the macro-level links and set memberships that situate
    each chunk in its larger context (dialogue thread, survey, topic, etc.).
    """

    def __init__(self, manager: Any = None, harmonia: Any = None):
        self.manager = manager
        self.harmonia = harmonia

    def on_trigger(self, event_data: Dict[str, Any]):
        """Event sink for autonomic cognitive triggers (chat webhooks, batch signals)."""
        trigger_type = event_data.get("trigger", "unknown")
        logger.debug("[Contexa] Trigger: %s", trigger_type)

    # ------------------------------------------------------------------
    # Macro-level contextual binding
    # ------------------------------------------------------------------

    def bind_context(self, ctx, chunk_key: str,
                     question_key: Optional[str] = None,
                     topic_key: Optional[str] = None,
                     respondent_key: Optional[str] = None,
                     set_names: Optional[List[str]] = None,
                     author: str = "contexa") -> Dict[str, Any]:
        """
        Create macro-level contextual links and set memberships for a chunk.

        Called after the chunk has been written (Weaver fires automatically on
        write; this method handles the higher-level structure on top of that).

        Links created:
          chunk → question_key   via  ctx:answers      (dialogue / survey)
          chunk → topic_key      via  ctx:topic        (thread / subject)
          chunk → respondent_key via  ctx:from         (survey respondent)

        Sets updated:
          Each name in set_names receives the chunk as a member.
          Conventional names: dialogue:{session_id}, survey:{id}:q:{qid},
          fetch:{session_id}:refs

        Returns a summary dict: {"links": n, "sets": n}.
        """
        if not ctx or not chunk_key:
            return {"links": 0, "sets": 0}

        links = 0
        sets  = 0

        link_targets = [
            (question_key,   "ctx:answers"),
            (topic_key,      "ctx:topic"),
            (respondent_key, "ctx:from"),
        ]
        for target_key, rel in link_targets:
            if not target_key:
                continue
            try:
                ctx.put_link(chunk_key, target_key, rel, author=author)
                links += 1
            except Exception as exc:
                logger.debug("[Contexa] bind link %s → %s: %s", rel, target_key, exc)

        for set_name in (set_names or []):
            try:
                ctx.add_to_set(set_name, chunk_key)
                sets += 1
            except Exception as exc:
                logger.debug("[Contexa] bind set %s: %s", set_name, exc)

        return {"links": links, "sets": sets}

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search Wikipedia for query terms and return a ranked list of results."""
        safe_query = urllib.parse.quote(query)
        url = (
            f"https://en.wikipedia.org/w/api.php"
            f"?action=opensearch&search={safe_query}&limit={limit}&format=json&redirects=resolve"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AkashaCognitiveFetch/2.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                titles   = data[1] if len(data) > 1 else []
                snippets = data[2] if len(data) > 2 else []
                urls     = data[3] if len(data) > 3 else []
                results = [
                    {"title": titles[i], "snippet": snippets[i], "url": urls[i]}
                    for i in range(len(titles))
                ]
                return {"results": results, "count": len(results)}
        except urllib.error.URLError as e:
            logger.warning(f"[Contexa] web.search network error: {e}")
            return {"error": f"web.search failed (Network): {str(e)}"}
        except Exception as e:
            logger.error(f"[Contexa] web.search critical error: {e}", exc_info=True)
            return {"error": f"web.search failed: {str(e)}"}

    def fetch(self, query: str) -> Dict[str, Any]:
        """External Context Gateway. Fetches intelligence from the global web."""
        query = query.strip()
        is_url = query.startswith("http://") or query.startswith("https://")
        if is_url: 
            return self._fetch_url(query)
        else: 
            return self._fetch_wikipedia(query)

    def _fetch_wikipedia(self, keyword: str) -> Dict[str, Any]:
        safe_keyword = urllib.parse.quote(keyword)
        api_url = (f"https://en.wikipedia.org/w/api.php"
                   f"?action=query&prop=extracts&exintro"
                   f"&titles={safe_keyword}&format=json&explaintext=1")
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "AkashaCognitiveFetch/2.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    if page_id == "-1":
                        return {"error": f"Concept '{keyword}' not found in Wikipedia."}
                    title   = page_info.get("title", keyword)
                    extract = page_info.get("extract", "").strip()
                    if not extract:
                        return {"error": "Found the page, but extract was empty."}
                    article_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    content = f"[{title}]\n{extract}"
                    return {
                        "source_type": "wikipedia",
                        "text":        content,
                        "title":       title,
                        "url":         article_url,
                        "alias":       f"wiki:{title.replace(' ', '_')}",
                        "evidence":    {"authority": 0.9, "reach": 1.0, "nature": "factual"},
                    }
            return {"error": "Failed to parse Wikipedia response."}
        except urllib.error.URLError as e:
            logger.warning("[Contexa] Wikipedia fetch network error: %s", e)
            return {"error": f"Wikipedia fetch failed (Network): {e}"}
        except Exception as e:
            logger.error("[Contexa] Wikipedia fetch critical error: %s", e, exc_info=True)
            return {"error": f"Wikipedia fetch failed: {e}"}

    def _fetch_url(self, url: str) -> Dict[str, Any]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AkashaCognitiveFetch/2.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode("utf-8", errors="ignore")
                title_m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
                title   = title_m.group(1).strip() if title_m else "Extracted Webpage"
                html    = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
                html    = re.sub(r"<style.*?>.*?</style>",  "", html, flags=re.IGNORECASE | re.DOTALL)
                text    = re.sub(r"<[^>]+>", " ", html)
                text    = re.sub(r"\s+", " ", text).strip()
                snippet = text[:1500] + "..." if len(text) > 1500 else text
                content = f"[{title}]\nSource: {url}\n\n{snippet}"
                return {
                    "source_type": "web",
                    "text":        content,
                    "title":       title,
                    "url":         url,
                    "evidence":    {"authority": 0.5, "reach": 0.5, "nature": "web_scrape"},
                }
        except urllib.error.URLError as e:
            logger.warning("[Contexa] URL fetch network error: %s", e)
            return {"error": f"URL fetch failed (Network): {e}"}
        except Exception as e:
            logger.error("[Contexa] URL fetch critical error: %s", e, exc_info=True)
            return {"error": f"URL fetch failed: {e}"}
