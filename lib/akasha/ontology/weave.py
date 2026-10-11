"""
The Weaver (micro layer) — proto-word decomposition + the post-write hooks (sys.weaver.* ops), moved out of the kernel (backend layout order 2026-09-20). Bodies are verbatim except `self.` → `kernel.` and intra-family calls.

Every function takes the kernel (the heart) as its first argument: it is the object the
dispatcher / timer registry hands in, never imported. Bodies are the kernel's own, moved
verbatim except `self.` → `kernel.` and intra-family calls.
"""
import os
import re
import sys
import time
import json
import uuid
import logging
import hashlib
import functools
from typing import Dict, Any, Optional, List, Callable
try:
    from lib.akasha.jcl import JCLWorker, JCLJob, JCLStep
    from lib.akasha.jcl.job import CLASS_BATCH_ATOM, CLASS_LINK, CLASS_MAINTENANCE
except ImportError:
    JCLWorker = None  # type: ignore
    JCLJob    = None  # type: ignore
    JCLStep   = None  # type: ignore
    CLASS_BATCH_ATOM = "batch_atom"  # type: ignore
    CLASS_LINK       = "link"        # type: ignore
    CLASS_MAINTENANCE = "maintenance"  # type: ignore
from lib.akasha.api.rpc import ok as _ok, err as _err

logger = logging.getLogger("Akasha.Kernel")


def weave_atom(kernel, nucleus, chunk_key: str, text: str) -> int:
    """
    Lemmatize text, link chunk_key to each lemma's nucleus protoword via
    sys:refers_to, and add chunk_key to the per-lemma set set:word:{lemma}.

    Lemma-First principle: if the protoword atom for a lemma does not yet
    exist in nucleus, _ensure_lemma_protoword auto-creates it so that
    SpaCy-lemmatized input always finds an anchor — for any language whose
    model is loaded.

    Both link and set operations are idempotent.
    Returns the number of links created.
    """
    # Weave LEAF gate — a raw Source Data row (source:item:*) is NLP-exempt: decomposing its
    # verbatim JSON would pollute the proto-word space. Local signal only (its own alias/meta).
    try:
        if _weave_exempt(nucleus.core.get_aliases_by_key(chunk_key)):
            return 0
    except Exception:
        pass
    woven = 0
    for (surface, lemma, lang, morph) in _lemmatize_for_weave(text):
        if len(lemma) < 2 or lemma in _WEAVE_STOPWORDS or lemma.isdigit():
            continue
        try:
            proto_key = nucleus._ensure_lemma_protoword(lemma, lang)
            if proto_key and proto_key != chunk_key:
                nucleus.put_link(chunk_key, proto_key, "sys:refers_to",
                                 author="sys:weaver", status="inferred")
                nucleus.add_to_set(f"set:word:{lemma}", chunk_key)
                woven += 1

                # If the surface form differs from the lemma and already has
                # its own nucleus atom (e.g. word:en:asked from WordNet),
                # link it to the lemma with a typed morph: relation.
                if surface != lemma:
                    surf_key = (nucleus.core.get_key_by_alias(surface) or
                                nucleus.core.get_key_by_alias(f"word:{lang}:{surface}"))
                    if surf_key and surf_key != proto_key:
                        rel = _morph_to_rel(morph)
                        nucleus.put_link(surf_key, proto_key, rel,
                                         author="sys:weaver", status="inferred")
        except Exception as _we:
            logger.debug("[Weaver] '%s'→lemma:'%s': %s", surface, lemma, _we)
    return woven


def weaver_denied(kernel, session, data, nucleus_write: bool):
    """Authorization gate for sys.weaver.* handlers.

    Weaving into the shared nucleus, or on behalf of another client, is a
    privileged/system operation — not something a plain USER may drive
    directly.  Legitimate weave jobs run under a librarian-tier owner
    (system.weaver for guests, the librarian/admin writer for nucleus
    writes, "admin" for boot pack loads), all of which carry role:librarian.
    Returns an error string if denied, else None.
    """
    from lib.akasha.api import gate as _gate
    # system.weaver / librarian / admin — the rows that reach the universal store.
    is_priv = _gate.gate(getattr(session, "client_id", ""), _gate.RECORD, _gate.UNIVERSAL)[0]
    for_client = data.get("_for_client")
    if for_client and for_client != session.client_id and not is_priv:
        return "weaver: '_for_client' override requires a librarian/system role"
    if nucleus_write and not is_priv:
        return "weaver: nucleus weaving requires a librarian/collective-write role"
    return None


def handle_weave(kernel, rid, data, session) -> dict:
    """sys.weaver.weave — weave a single atom's text into protoword links."""
    denied = weaver_denied(kernel, session, data, nucleus_write=True)
    if denied:
        return _err(rid, -32003, denied)
    nucleus = getattr(session, 'nucleus', None)
    if not nucleus:
        return _ok(rid, {"status": "skipped", "reason": "no nucleus"})

    key  = data.get("key", "")
    text = data.get("text", "")
    alias = data.get("alias", "")

    if not key and alias:
        key = nucleus.core.get_key_by_alias(alias) or ""
    if not key:
        return _ok(rid, {"status": "skipped", "reason": "atom not found"})

    if not text and key:
        raw = nucleus.core.get_chunk_raw(key)
        if raw:
            content = raw.get("content", "") if isinstance(raw, dict) else str(raw)
            # Strip "[name]\n" prefix written by _handle_define
            text = content.split("\n", 1)[1] if "\n" in content else content

    if not text:
        return _ok(rid, {"status": "skipped", "reason": "no text"})

    woven = weave_atom(kernel, nucleus, key, text)
    return _ok(rid, {"status": "woven", "key": key, "links_created": woven})


def handle_weave_batch(kernel, rid, data, session) -> dict:
    """sys.weaver.weave_batch — weave a list of {alias, text} items in one step."""
    denied = weaver_denied(kernel, session, data, nucleus_write=True)
    if denied:
        return _err(rid, -32003, denied)
    nucleus = getattr(session, 'nucleus', None)
    if not nucleus:
        return _ok(rid, {"status": "skipped", "reason": "no nucleus"})

    items = data.get("items", [])
    total_woven = 0
    processed   = 0

    for item in items:
        alias = item.get("alias", "")
        text  = item.get("text", "")
        key   = item.get("key", "")

        if not key and alias:
            key = nucleus.core.get_key_by_alias(alias) or ""
        if not key or not text:
            continue

        try:
            total_woven += weave_atom(kernel, nucleus, key, text)
            processed += 1
        except Exception as _be:
            logger.debug("[Weaver] batch item '%s': %s", alias or key[:8], _be)

    logger.info("[Weaver] batch: %d atoms processed, %d links woven", processed, total_woven)
    return _ok(rid, {"status": "woven",
                      "atoms_processed": processed,
                      "links_created": total_woven})


def weave_client_atom(kernel, cortex, nucleus, chunk_key: str, text: str) -> int:
    """
    Client-space weave: link chunk_key to EXISTING nucleus protowords only,
    and add chunk_key to a per-lemma set in the client's own cortex.

    Privacy contract (black-hole boundary):
    - Lemmatizes text and looks up the lemma in nucleus (read-only access).
    - Lookup tries bare alias first, then qualified 'word:{lang}:{lemma}'.
    - Never creates new protowords in nucleus — no client data leaks outward.
    - Links and set memberships are written into the client's own cortex only.
    - Direction: client_atom → nucleus_protoword (one-way; no reverse link).
    - set:word:{lemma} in cortex = private index of client's atoms by concept.
    """
    # Weave LEAF gate — raw Source Data rows (source:item:*) are NLP-exempt (see _weave_exempt).
    try:
        if _weave_exempt(cortex.core.get_aliases_by_key(chunk_key)):
            return 0
    except Exception:
        pass
    woven = 0
    for (surface, lemma, lang, _morph) in _lemmatize_for_weave(text):
        if len(lemma) < 2 or lemma in _WEAVE_STOPWORDS or lemma.isdigit():
            continue
        try:
            proto_key = (nucleus.core.get_key_by_alias(lemma) or
                         nucleus.core.get_key_by_alias(f"word:{lang}:{lemma}"))
            if proto_key and proto_key != chunk_key:
                cortex.put_link(chunk_key, proto_key, "sys:refers_to",
                                author="sys:weaver", status="inferred")
                cortex.add_to_set(f"set:word:{lemma}", chunk_key)
                woven += 1
        except Exception as _we:
            logger.debug("[Weaver/client] '%s'→lemma:'%s': %s", surface, lemma, _we)
    return woven


def handle_weave_client(kernel, rid, data, session) -> dict:
    """sys.weaver.weave_client — weave a client atom into existing nucleus protowords."""
    # weave_client only READS nucleus protowords and writes into the target
    # cortex, so it is safe on one's own cortex; the _for_client override
    # (writing into another client's cortex) is the privileged part.
    denied = weaver_denied(kernel, session, data, nucleus_write=False)
    if denied:
        return _err(rid, -32003, denied)
    # When running as system.weaver on behalf of a guest, _for_client names
    # the original session so we access the correct cortex.
    for_client = data.get("_for_client")
    if for_client:
        _target = kernel.manager.get_session(for_client)
        nucleus = getattr(_target, 'nucleus', None)
        cortex  = _target.local_cortex
    else:
        nucleus = getattr(session, 'nucleus', None)
        cortex  = session.local_cortex
    if not nucleus:
        return _ok(rid, {"status": "skipped", "reason": "no nucleus"})

    key   = data.get("key", "")
    text  = data.get("text", "")
    alias = data.get("alias", "")

    if not key and alias:
        key = cortex.resolve_alias(alias) or ""
    if not key:
        return _ok(rid, {"status": "skipped", "reason": "atom not found"})

    if not text and key:
        raw = cortex.get_chunk_raw(key) if hasattr(cortex, 'get_chunk_raw') else None
        if raw:
            content = raw.get("content", "") if isinstance(raw, dict) else str(raw)
            text = content.split("\n", 1)[1] if "\n" in content else content

    if not text:
        return _ok(rid, {"status": "skipped", "reason": "no text"})

    woven = weave_client_atom(kernel, cortex, nucleus, key, text)
    return _ok(rid, {"status": "woven", "key": key, "links_created": woven})


def enqueue_weave(kernel, session, is_nucleus: bool, key: str, text: str, label: str) -> None:
    """
    Fire-and-forget weave job.  Skipped inside JCL worker threads (pack loading
    uses the batch weaver; per-atom jobs would double-weave and flood the queue).

    Guest sessions lack WRITE capability so the job runs under system.weaver
    (LIBRARIAN role) with _for_client carrying the original session owner so
    the Weaver handler can access the right cortex.
    """
    import threading as _thr
    if _thr.current_thread().name.startswith("JCLWorker"):
        return
    if not (text and kernel.jcl_worker and JCLJob and JCLStep):
        return
    method = "sys.weaver.weave" if is_nucleus else "sys.weaver.weave_client"
    cid = getattr(session, 'client_id', 'system')
    role = getattr(session, 'role', None)
    is_guest = (role is not None and str(getattr(role, 'value', role)) == "guest")
    jcl_owner = "system.weaver" if is_guest else cid
    params = {"key": key, "text": text}
    if is_guest:
        params["_for_client"] = cid
    kernel.harmonia.submit_job(JCLJob(
        owner=jcl_owner,
        label=label[:60],
        steps=[JCLStep(method=method, params=params)],
        fail_fast=False,
    ))


def post_write(kernel, session, is_nucleus: bool, atom_id: str, text: str,
                label: str = None) -> None:
    """
    Single entry point called after every Atom write.
    Queues both protoword linking and NLP word decomposition so all paths
    (w / def / al / s.add / onto load / fetch) go through the same pipeline.
    """
    if not text:
        return
    lbl = label or f"sys.weaver:{atom_id[:8]}"
    enqueue_weave(kernel, session, is_nucleus, atom_id, text, lbl)
    enqueue_decompose(kernel, session, is_nucleus, atom_id, text)


def enqueue_decompose(kernel, session, is_nucleus: bool, atom_id: str,
                       text: str, label: str = None) -> None:
    """
    Queue a word-decomposition job. Skipped inside JCL worker threads
    and for single-word texts (already atomic — nothing to decompose).

    Guest sessions lack WRITE capability so the job runs under system.weaver
    (LIBRARIAN role) with _for_client carrying the original session owner.
    """
    import threading as _thr
    if _thr.current_thread().name.startswith("JCLWorker"):
        return
    if not (text and kernel.jcl_worker and JCLJob and JCLStep):
        return
    if len(_tokenize_for_weave(text)) < 2:
        return
    cid    = getattr(session, 'client_id', 'system')
    role   = getattr(session, 'role', None)
    is_guest = (role is not None and str(getattr(role, 'value', role)) == "guest")
    jcl_owner = "system.weaver" if is_guest else cid
    locale = getattr(getattr(session, 'locale', None), 'primary', 'en')
    lbl    = (label or f"decompose:{atom_id[:8]}")[:60]
    params = {"key": atom_id, "text": text, "is_nucleus": is_nucleus, "locale": locale}
    if is_guest:
        params["_for_client"] = cid
    kernel.harmonia.submit_job(JCLJob(
        owner=jcl_owner,
        label=lbl,
        steps=[JCLStep(method="sys.weaver.decompose", params=params)],
        fail_fast=False,
    ))


def nlp_extract_tags(kernel, text: str, locale: str = "en") -> dict:
    """
    Extract semantic tags from text with graceful multi-tier degradation.

    Tier 3 (NLP): Harmonia nlp.extract plugin (SpaCy-based MultiLocaleNLP).
                  Returns trait:*, chrono:*, and geo:* tags.
    Tier 1 (Basic): _tokenize_for_weave — regex split, stopwords, len≥3.
                    Always available for Latin-script text.
    Tier 0 (CJK):  Character bigrams for CJK text when no model is available.

    Returns dict with keys:
      words   — word tokens to materialise as Atoms in components set
      chrono  — chrono: tags (for chrono:period links)
      geo     — geo: tags (for geo:at links)
      quality — 'nlp' | 'basic'
    """
    import re as _re

    is_cjk = bool(_re.search(r'[぀-鿿가-힯一-鿿]', text))

    # T3 — try registered NLP plugin
    if kernel.harmonia:
        _plugins = getattr(kernel.harmonia, '_plugins', {})
        nlp_fn   = _plugins.get("nlp.extract")
        if nlp_fn:
            try:
                raw    = nlp_fn(text)
                words  = []
                chrono = []
                geo    = []
                for tag in (raw or []):
                    if tag.startswith("trait:"):
                        words.append(tag[6:])
                    elif tag.startswith("chrono:"):
                        chrono.append(tag)
                    elif tag.startswith("geo:"):
                        geo.append(tag)
                    elif not tag.startswith("sys:"):
                        words.append(tag)
                if words or chrono or geo:
                    return {"words": words, "chrono": chrono,
                            "geo": geo, "quality": "nlp"}
            except Exception as _e:
                logger.debug("[Weaver/decompose] NLP plugin failed: %s", _e)

    # T0 — CJK character bigrams when no morphological model
    if is_cjk:
        chars   = [c for c in text
                   if _re.match(r'[぀-鿿가-힯一-鿿]', c)]
        bigrams = [chars[i] + chars[i + 1] for i in range(len(chars) - 1)]
        tokens  = list(dict.fromkeys(bigrams + chars))
        return {"words": tokens, "chrono": [], "geo": [], "quality": "basic"}

    # T1 — basic Latin tokenizer (always available)
    tokens = _tokenize_for_weave(text)
    return {"words": tokens, "chrono": [], "geo": [], "quality": "basic"}


def find_or_create_word_atom(kernel, write_ctx, nucleus, client_id: str,
                               token: str, is_nucleus: bool):
    """
    Locate an existing Atom for a word token, or create one.
    For nucleus Atoms the protoword (word:{token}) is the canonical word Atom.
    For client Atoms we prefer an existing cortex alias, then nucleus protoword,
    and finally create a new private cortex Atom.
    """
    if is_nucleus and nucleus:
        existing = (nucleus.core.get_key_by_alias(f"word:{token}") or
                    nucleus.core.get_key_by_alias(token))
        if existing:
            return existing

    if hasattr(write_ctx, 'resolve_alias'):
        existing = write_ctx.resolve_alias(token)
        if existing:
            return existing

    if nucleus:
        proto = nucleus.core.get_key_by_alias(f"word:{token}")
        if proto:
            return proto

    try:
        scopes = [] if is_nucleus else [
            f"owner:user_{client_id}",
            f"view:user_{client_id}",
        ]
        word_key = write_ctx.put_chunk(
            content=token,
            meta={"type": "word", "source": "weave_decompose"},
            author=client_id,
            scopes=scopes,
        )
        write_ctx.set_alias(word_key, token)
        return word_key
    except Exception as _e:
        logger.debug("[Decompose] create word atom '%s': %s", token, _e)
        return None


def handle_weave_decompose(kernel, rid, data, session) -> dict:
    """
    sys.weaver.decompose — NLP word decomposition and component set population.

    For each meaningful token extracted from the source Atom's text:
      1. Finds or creates a word Atom in the appropriate context.
      2. Adds the word Atom to components:{key} set of the source Atom.
      3. Weaves protoword links for the word Atom directly (already in JCL
         context, so no secondary JCL job is needed).

    When NLP quality is 'basic', the source Atom is queued in
    weave:pending:{locale} for reprocessing when a full model loads.
    """
    key        = data.get("key", "")
    text       = data.get("text", "")
    is_nucleus = data.get("is_nucleus", False)
    locale     = data.get("locale", "en")

    if not key or not text:
        return _err(rid, -32602, "decompose requires key and text")

    denied = weaver_denied(kernel, session, data, nucleus_write=bool(is_nucleus))
    if denied:
        return _err(rid, -32003, denied)

    # When running as system.weaver on behalf of a guest, _for_client names
    # the original session so we write to the correct cortex.
    for_client = data.get("_for_client")
    if for_client:
        _target = kernel.manager.get_session(for_client)
        nucleus = getattr(_target, 'nucleus', None)
        cortex  = getattr(_target, 'local_cortex',
                          getattr(_target, 'cortex', None))
        cid     = for_client
    else:
        nucleus = getattr(session, 'nucleus', None)
        cortex  = getattr(session, 'local_cortex',
                          getattr(session, 'cortex', None))
        cid     = getattr(session, 'client_id', 'system')
    write_ctx = nucleus if is_nucleus else cortex
    if not write_ctx:
        return _ok(rid, {"status": "skipped", "reason": "no write context"})

    # Weave LEAF gate — a raw Source Data row (source:item:*) is NLP-exempt (see _weave_exempt):
    # do not decompose its verbatim JSON into proto-words. Extracted txt:* atoms are not exempt.
    try:
        if _weave_exempt(write_ctx.core.get_aliases_by_key(key)):
            return _ok(rid, {"status": "skipped", "reason": "raw source (NLP-exempt)"})
    except Exception:
        pass

    result  = nlp_extract_tags(kernel, text, locale)
    words   = result["words"]
    chrono  = result["chrono"]
    geo     = result["geo"]
    quality = result["quality"]

    if not (words or chrono or geo):
        return _ok(rid, {"status": "skipped", "reason": "no tokens extracted"})

    component_set = f"components:{key}"
    created = 0

    for token in words:
        word_key = find_or_create_word_atom(kernel, 
            write_ctx, nucleus, cid, token, is_nucleus)
        if not word_key or word_key == key:
            continue
        try:
            write_ctx.add_to_set(component_set, word_key)
        except Exception as _e:
            logger.debug("[Decompose] add_to_set '%s': %s", token, _e)
            continue
        # Weave protoword links for the word Atom directly — we are already
        # inside a JCL worker thread, so _enqueue_weave would no-op here.
        try:
            if is_nucleus and nucleus:
                weave_atom(kernel, nucleus, word_key, token)
            elif cortex and nucleus:
                weave_client_atom(kernel, cortex, nucleus, word_key, token)
        except Exception as _e:
            logger.debug("[Decompose] weave word atom '%s': %s", token, _e)
        created += 1

    # Create chrono:period and geo:at links for semantic tags produced by NLP
    tag_links = (
        [(t, "chrono:period") for t in chrono] +
        [(t, "geo:at") for t in geo]
    )
    for tag, rel in tag_links:
        try:
            tag_key = write_ctx.resolve_alias(tag) if hasattr(write_ctx, 'resolve_alias') else None
            if not tag_key:
                tag_key = write_ctx.put_chunk(
                    content=tag,
                    meta={"type": "tag", "role": rel},
                    author=cid,
                )
                if hasattr(write_ctx, 'set_alias'):
                    write_ctx.set_alias(tag_key, tag)
            write_ctx.put_link(key, tag_key, rel, author=cid)
            created += 1
        except Exception as _e:
            logger.debug("[Decompose] tag link '%s' → '%s': %s", tag, rel, _e)

    pending_set = f"weave:pending:{locale}"
    if quality == "basic":
        try:
            write_ctx.add_to_set(pending_set, key)
        except Exception:
            pass
    else:
        try:
            write_ctx.remove_from_set(pending_set, key)
        except Exception:
            pass

    return _ok(rid, {"status": "ok", "key": key,
                     "components": created, "quality": quality})


def handle_weave_drain_pending(kernel, rid, data, session) -> dict:
    """
    sys.weaver.drain_pending — reprocess atoms in weave:pending:{locale}
    after a full NLP model has become available.
    """
    locale  = data.get("locale", "en")
    nucleus = getattr(session, 'nucleus', None)
    cortex  = getattr(session, 'local_cortex',
                      getattr(session, 'cortex', None))
    pending_set = f"weave:pending:{locale}"
    processed = 0
    remaining = 0

    for ctx_label, ctx_obj in [("nucleus", nucleus), ("cortex", cortex)]:
        if not ctx_obj:
            continue
        try:
            members = ctx_obj.list_set(pending_set) or []
        except Exception:
            continue
        for member in members:
            atom_key = member.get("key", "")
            if not atom_key:
                continue
            try:
                raw = (ctx_obj.get_chunk_raw(atom_key)
                       if hasattr(ctx_obj, 'get_chunk_raw') else None)
                if not raw:
                    continue
                text = (raw.get("content", "")
                        if isinstance(raw, dict) else str(raw))
                _result = nlp_extract_tags(kernel, text, locale)
                if _result["quality"] == "nlp":
                    is_nucleus = (ctx_label == "nucleus")
                    handle_weave_decompose(kernel, rid, {
                        "key": atom_key, "text": text,
                        "is_nucleus": is_nucleus, "locale": locale,
                    }, session)
                    processed += 1
                else:
                    remaining += 1
            except Exception as _e:
                logger.debug("[DrainPending] %s: %s", atom_key, _e)

    return _ok(rid, {"locale": locale,
                     "processed": processed, "remaining": remaining})


# ── Weaver — constituent-word tokenizer ──────────────────────────────────────
# Words extracted from atom descriptions are linked to their nucleus protowords
# via sys:refers_to (relation: "this atom refers to this concept").
# Stopwords are filtered so only semantically meaningful tokens are woven.
_WEAVE_STOPWORDS = frozenset({
    # English function words
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "not", "and", "or", "but",
    "for", "yet", "so", "nor", "to", "of", "in", "on", "at", "by", "as",
    "with", "this", "that", "these", "those", "it", "its", "i", "you",
    "he", "she", "we", "they", "them", "their", "our", "your", "his", "her",
    "who", "what", "which", "when", "where", "why", "how", "all", "each",
    "both", "few", "more", "most", "other", "some", "such", "no", "only",
    "own", "same", "than", "too", "very", "just", "about", "after",
    "before", "between", "into", "through", "during", "also", "then", "now",
    "if", "from", "up", "out", "over", "under", "again", "here", "there",
    "ever", "never", "often", "while", "although", "because", "since",
    "until", "has", "had", "its", "one", "two", "new", "old", "any",
    # Common abbreviation noise in descriptions
    "etc", "eg", "ie", "vs",
    # French/Spanish/German particles that appear in ontology descriptions
    "de", "la", "le", "et", "du", "les", "des", "en", "el", "und", "der",
})


def _tokenize_for_weave(text: str) -> List[str]:
    """Return deduplicated candidate concept tokens from a description string."""
    import re as _re
    seen: set = set()
    result: List[str] = []
    for tok in _re.split(r"[\W_]+", text.lower()):
        if len(tok) < 3:
            continue
        if tok in _WEAVE_STOPWORDS:
            continue
        if tok.isdigit():
            continue
        if tok not in seen:
            seen.add(tok)
            result.append(tok)
    return result


def _morph_to_rel(morph: dict) -> str:
    """
    Map Universal Dependencies morphological features (from SpaCy token.morph)
    to a morph: link relation string.

    Falls back to sys:inflection_of when no specific category is recognised,
    preserving the generic derivation link while allowing callers to distinguish
    typed relations (morph:plural, morph:past_tense, …) from untyped ones.
    """
    tense     = morph.get("Tense")
    verb_form = morph.get("VerbForm")
    number    = morph.get("Number")
    degree    = morph.get("Degree")
    case      = morph.get("Case")
    aspect    = morph.get("Aspect")
    polarity  = morph.get("Polarity")

    if verb_form == "Part":
        return "morph:past_participle" if tense == "Past" else "morph:progressive"
    if tense == "Past":
        return "morph:past_tense"
    if tense == "Pres" and verb_form == "Fin":
        return "morph:present"
    if verb_form == "Inf":
        return "morph:infinitive"
    if number == "Plur":
        return "morph:plural"
    if degree == "Comp":
        return "morph:comparative"
    if degree == "Sup":
        return "morph:superlative"
    if polarity == "Neg":
        return "morph:negative"
    if case:
        return f"morph:{case.lower()}"
    return "sys:inflection_of"


def _lemmatize_for_weave(text: str) -> List[tuple]:
    """
    Tokenize and lemmatize *text* for the Weaver pipeline.

    Returns [(surface, lemma, lang, morph)] tuples where morph is a dict of
    Universal Dependencies features (e.g. {'Tense': 'Past', 'VerbForm': 'Fin'}).
    Emits (token, token, 'en', {}) — the regex floor.

    Stopword/length/digit filtering is applied by the caller (_weave_atom).

    Why the regex floor and nothing else: the boot
    weave runs UNATTENDED inside the single-writer daemon, and SpaCy's native pipeline
    (thinc/blis/numpy C-extensions) can HARD-CRASH the process — a segfault is not a Python
    exception, so no `try/except` can catch it, and it takes the whole daemon down (the
    silent, deterministic boot death seen on Python 3.14 while weaving the `lexicon` pack). The
    weave is OPTIONAL background enrichment (the graph is fully usable without it), so it must not
    be able to kill the writer. Therefore:
      • The stdlib regex floor, always — dependency-free, and it CANNOT crash the process. It
        produces valid `word:` links (surface forms), without lemma normalization. (The SpaCy
        opt-in and its regex-only override are deleted with their switches — the purge order §4.5.)
    """
    import re as _re
    seen: set = set()
    result = []
    for tok in _re.split(r"[\W_]+", text.lower()):
        if tok and tok not in seen:
            seen.add(tok)
            result.append((tok, tok, "en", {}))
    return result


def _weave_exempt(aliases, raw_meta=None) -> bool:
    """True if an atom must NOT be weaved (NLP-decomposed) — a RAW Source Data row. The signal is
    LOCAL to the atom: its own alias namespace (`source:item:*`) or a raw meta marker
    (`provenance=source` / `content_type=json`). It is NEVER inferred from what the atom links to,
    so an index / analysis / clab / `txt:` atom linked to a raw row still weaves, and a raw row is
    exempt regardless of what links to it — exactly the raw atoms are exempt, no more. Placed at the
    weave LEAF so every path (boot batch, _post_write→decompose, direct sys.weaver.*) is covered."""
    for a in (aliases or []):
        if str(a).startswith(_RAW_SOURCE_NS):
            return True
    return _is_raw_source(raw_meta)


def _is_external(raw_meta) -> bool:
    """True if an atom's meta marks it as NON-curated content excluded from learning (ASI06):
    provenance=external (unvetted fetched web text), telemetry (dynamic live facts), or broadcast
    (AI-generated public-broadcast mirror chatter). Such atoms are excluded from semantic learning and
    from gap.scan so neither unvetted web text, live facts, nor machine talk-show output poisons the
    learned model or is mistaken for a curation gap — they are operable by concept models but never
    teach the graph its structure."""
    if not raw_meta:
        return False
    try:
        meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
        return str(meta.get("provenance", "")) in ("external", "telemetry", "broadcast")
    except (json.JSONDecodeError, AttributeError):
        return False


def _is_raw_source(raw_meta) -> bool:
    """True for a Source Data Layer atom — a Source item/pool/acquisition/sample/snapshot/stream/
    bridge (`concept` = `source_*`, or a `provenance="source"` marker). These are RAW acquired
    data, verbatim and explicitly un-interpreted: a Source item's `content` is boilerplate
    ("Source item — ACQUIRED …") and its real payload rides in `source_metadata`, so learning from
    it teaches the model boilerplate noise while a large corpus (e.g. 26k survey rows) both bloats
    the learn READ and consumes the bounded learn budget meant for curated ontology. Excluded from
    semantic learning and gap.scan for the same reason as external content (ASI06): raw data is
    operable by concept models but must never teach the graph its structure."""
    if not raw_meta:
        return False
    try:
        meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
        if str(meta.get("provenance", "")) == "source":
            return True
        return str(meta.get("concept", "")).startswith("source_")
    except (json.JSONDecodeError, AttributeError):
        return False


_RAW_SOURCE_NS = "source:item:"
