"""
The web fetch into the graph (contexa.fetch / gap.fetch) — moved out of the kernel (backend layout order 2026-09-20).

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

from lib.akasha.api.heart import _NucleusWriteCtx

from lib.akasha.ontology import weave
logger = logging.getLogger("Akasha.Kernel")


def do_fetch(kernel, session, ctx, scopes, client_id, query,
              link_to=None, link_rel="calc:enriches") -> dict:
    """Fetch external content for `query` and integrate it as atoms (the write half
    of contexa.fetch, shared with gap.fetch). Returns the provider result dict with
    atom_key/written on success, or the raw provider result (error/no-text) otherwise.
    Every written atom carries the provenance=external guardrail (trust score +
    provenance scopes) so unvetted web text stays distinguishable from curation.
    `link_to`, when given, is linked FROM the fetched atom via `link_rel` so the graph
    records which concept the fetch enriched. Callers run under a write workspace."""
    result = kernel.contexa.fetch(query)
    if "error" in result:
        return result

    text = result.get("text", "")
    if not text:
        return result

    source_type = result.get("source_type", "web")
    evidence    = result.get("evidence", {})
    url         = result.get("url", "")
    title       = result.get("title", "")
    alias       = result.get("alias")

    # ── Provenance guardrail (curation trust has an explicit, inspectable basis) ──
    # External content is an attack surface (ASI06 memory poisoning) and must never
    # be indistinguishable from curated ontology. Every fetched atom is:
    #   - tagged provenance=external + source, with a computed `trust` score, and
    #   - placed in the computational scopes provenance:external / provenance:<source>
    #     so curated-only reads/learning can exclude it and curators can review it.
    # trust is grounded in the fetch evidence, not asserted flat.
    trust = _external_trust(evidence, source_type)
    write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}",
                    "provenance:external", f"provenance:{source_type}"]

    # Write the content Atom
    atom_key = ctx.put_chunk(
        content=text,
        meta={"type": f"fetch:{source_type}", "evidence": evidence,
              "url": url, "title": title,
              "provenance": "external", "source": source_type, "trust": trust},
        author=client_id,
        scopes=write_scopes,
    )
    session.last_written_id = atom_key
    session.set_context("last_written_id", atom_key)
    if alias:
        try:
            ctx.set_alias(atom_key, alias)
        except Exception:
            pass

    # URL exit-point Atom + ref:source link
    url_key = None
    if url:
        url_key = find_or_create_url_atom(kernel, ctx, url, title,
                                                 client_id, write_scopes)
        if url_key:
            try:
                ctx.put_link(atom_key, url_key, "ref:source", author=client_id)
            except Exception:
                pass

    # Query Atom + ctx:topic link (find or create)
    query_key = None
    if query and not query.startswith("http"):
        q_alias = f"query:{query[:60]}"
        try:
            query_key = ctx.resolve_alias(q_alias)
        except Exception:
            pass
        if not query_key:
            try:
                query_key = ctx.put_chunk(
                    content=query,
                    meta={"type": "query"},
                    author=client_id,
                    scopes=write_scopes,
                )
                ctx.set_alias(query_key, q_alias)
            except Exception:
                pass

    # Macro context binding (ctx:topic + fetch set)
    session_id = getattr(session, "session_id", client_id)
    if kernel.contexa:
        kernel.contexa.bind_context(
            ctx, atom_key,
            topic_key=query_key,
            set_names=[f"fetch:{session_id}:refs"],
            author=client_id,
        )

    # Enrichment link: fetched atom → the concept it was fetched to enrich, so the
    # self-expanding loop is recorded in the graph (gap.fetch sets link_to).
    if link_to and link_to != atom_key:
        try:
            ctx.put_link(atom_key, link_to, link_rel, author=client_id)
        except Exception:
            pass

    # Trigger Weaver + NLP — same pipeline as w command
    weave.post_write(kernel, session, isinstance(ctx, _NucleusWriteCtx), atom_key, text)

    result["atom_key"] = atom_key
    result["written"]  = True
    return result


@staticmethod
def _external_trust(evidence: dict, source_type: str) -> float:
    """Ground a fetched atom's curation trust in its evidence rather than asserting a
    flat value: trust = 0.5·authority + 0.3·reach + 0.2·nature. Wikipedia (authority
    0.9, reach 1.0, factual) → ~0.95; a scraped URL (authority 0.5) → lower. The score
    is stored on the atom so any downstream curation decision is inspectable."""
    try:
        authority = float(evidence.get("authority", 0.3))
        reach = float(evidence.get("reach", 0.3))
    except (TypeError, ValueError):
        authority, reach = 0.3, 0.3
    nature = str(evidence.get("nature", "unknown")).lower()
    nature_f = {"factual": 1.0, "reference": 0.9, "opinion": 0.5,
                "unknown": 0.3}.get(nature, 0.3)
    return round(max(0.0, min(1.0, 0.5 * authority + 0.3 * reach + 0.2 * nature_f)), 3)


def find_or_create_url_atom(kernel, ctx, url: str, title: str,
                              client_id: str, scopes: list):
    """
    Find an existing URL Atom (by alias url:{url}) or create one.
    URL Atoms are the exit points — their content IS the URL, allowing
    navigation from Akasha to the external source.
    """
    alias = f"url:{url}"
    try:
        existing = ctx.resolve_alias(alias)
        if existing:
            return existing
    except Exception:
        pass
    try:
        key = ctx.put_chunk(
            content=url,
            meta={"type": "ref:url", "url": url, "title": title},
            author=client_id,
            scopes=scopes,
        )
        ctx.set_alias(key, alias)
        return key
    except Exception as exc:
        logger.debug("[Fetch] create URL atom '%s': %s", url, exc)
        return None
