"""
The semantic layer's ops + boot schedules (semantic.search/learn, node.sim/learn, gap.scan/fetch), moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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
    from lib.contexa.engine import ContexaEngine
except ImportError:
    ContexaEngine = None  # type: ignore
from lib.akasha.api.heart import _rss_mb, _search_partial_incr, _SEARCH_PARTIAL, _MAINT_LOCK, _MAINT_LAST_DONE, _MAINT_GAP_S, _MAINT_GATE_AVAIL_MB, _MAINT_GATE_MAX_WAIT_S, _MAINT_GATE_RETRY_S, _maint_gate_ok, _run_gated_maint, _with_rss_delta, _mem_available_mb, _smaps_rollup, _thread_count, _open_fd_count, _fd_soft_limit, _autolearn_disabled_reason
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.pagination import paginate as _paginate, resolve_limit as _rlimit, resolve_offset as _roffset
from lib.akasha.source import bootstrap as _src_bootstrap, fetch as _src_fetch   # transitional (S3→S4/S5)
from lib.akasha import lexicon

# ── constants moved from the kernel class (backend layout order 2026-09-20) ──
# Abstract / definitional vocabulary that crowds CONTENT similarity once loaded — its
# glosses are lexically dense, so it dominates sim/search though it is not a real
# content neighbour. Two populations:
#   • the lexicon layer  — reldef:/nsdef: atoms (members of the `rels`/`namespaces` sets)
#   • abstract hub atoms — the DNA/structural/logical vocabulary whose whole job is to
#     DEFINE (emotions, system relations, set operations, logic, frames, …), detected
#     by their namespace prefix.
# Both are excluded from sim / semantic.search / node.sim by default; opt back in with
# meta=1 / all=1 (vocabulary exploration). Content namespaces (word:, concept:, ingred:,
# dish:, geo:, …) are never excluded.
_META_NAMESPACES = frozenset({
    "sys", "set_op", "log", "frame", "emo", "calc", "dna", "meta", "scope", "tmp",
})


from lib.akasha.concepts._universal import _excluded_from_learning, _readable

logger = logging.getLogger("Akasha.Kernel")


def handle_gap_scan(kernel, rid, data, session, ctx, scopes) -> dict:
    """gap.scan [limit=] [scan=] — surface the self-expanding-ontology-loop entry
    points: concepts that are USED a lot (distributional importance) but UNDER-CURATED
    (few semantic links). The mismatch between how much a node is referenced and how
    richly it is linked is the signal for what to enrich next (via fetch / weaver /
    an LLM). Structural maturity is the ShelfScore idea, generalised to any atom;
    importance is inbound weave references (sys:refers_to). Scope-filtered."""
    limit = max(1, min(int(data.get("limit", 20)), 200))
    scan = max(1, min(int(data.get("scan", 3000)), 30000))
    gaps = scan_gaps(kernel, ctx, scopes, scan, limit)
    out = [{"key": g["key"], "gap_score": g["gap_score"], "importance": g["importance"],
            "curated_links": g["curated_links"], "preview": g["content"][:80]}
           for g in gaps]
    return _ok(rid, {"gaps": out, "count": len(out)})


def scan_gaps(kernel, ctx, scopes, scan, limit) -> list:
    """Rank atoms by the self-expanding-loop gap signal: importance (inbound
    references) × (1 − structural maturity of curated outbound links). Scope-filtered,
    external atoms excluded. Shared by gap.scan (report) and gap.fetch (act)."""
    results = []
    for row in (ctx.stream(limit=scan) or []):
        key = row.get("key")
        if not key or (scopes and not ctx.check_access(key, scopes)):
            continue
        # Externally-fetched atoms are not enrichment targets — they ARE the
        # enrichment material. Curating them would loop fetch→gap→fetch. Raw Source Data
        # is likewise not a curation gap (verbatim acquired data). Excluded by meta
        # (concept=source_* / provenance) — no per-row alias store read on the scan path.
        if _excluded_from_learning(row.get("meta")):
            continue
        # Importance: read the atom's incrementally-maintained meaning-density
        # (meta['salience']) — bumped on every link, so no per-atom link scan here. Falls
        # back to counting inbound links for atoms written before salience existed.
        _m = row.get("meta")
        if isinstance(_m, str):
            try:
                _m = json.loads(_m)
            except Exception:
                _m = {}
        importance = (_m or {}).get("salience")
        if importance is None:
            importance = len(ctx.get_incoming_links(key) or [])
        if not importance or importance < 0.5:
            continue
        # Structural maturity: curated semantic links out (exclude sys:/weave scaffolding).
        adj = ctx.get_adjacent_links(key) or []
        curated = sum(1 for pair in adj
                      if len(pair) > 1 and not str(pair[1]).startswith("sys:"))
        struct = min(1.0, curated / 6.0)
        imp = min(1.0, importance / 8.0)
        gap = imp * (1.0 - struct)          # important but thin → high
        if gap > 0.0:
            results.append({"gap_score": round(gap, 4), "key": key,
                            "importance": importance, "curated_links": curated,
                            "content": row.get("content") or ""})
    results.sort(key=lambda r: r["gap_score"], reverse=True)
    return results[:limit]


def handle_gap_fetch(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    """gap.fetch [limit=] [scan=] — close the self-expanding-ontology loop: find the
    important-but-thin concepts (gap.scan), then AUTO-FETCH external context to enrich
    each, weaving it into the graph so the next semantic.learn sees a richer corpus.
    This is the avatar-delegate step (#31): whichever agent/avatar session invokes it
    performs the fetch under its own identity, and every fetched atom carries the
    provenance=external guardrail (trust score + provenance scopes) so unvetted web
    text can neither poison the learned model nor masquerade as curation. Bounded and
    degrades gracefully offline (no network → fetched=false, no error). Admin/librarian
    only (external network writes). Runs inside the caller's write workspace."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    if not kernel.contexa:
        return _err(rid, -32001, "ContexaEngine not available in this environment.")
    limit = max(1, min(int(data.get("limit", 3)), 10))
    scan = max(1, min(int(data.get("scan", 3000)), 30000))
    gaps = scan_gaps(kernel, ctx, scopes, scan, limit)

    enriched = []
    for g in gaps:
        key = g["key"]
        query = gap_query(kernel, ctx, key, g["content"])
        if not query:
            enriched.append({"gap_key": key, "query": None, "fetched": False,
                             "reason": "no query term"})
            continue
        try:
            res = _src_fetch.do_fetch(kernel, session, ctx, scopes, client_id, query,
                                 link_to=key, link_rel="calc:enriches")
        except Exception as exc:                       # network / provider failure
            enriched.append({"gap_key": key, "query": query, "fetched": False,
                             "reason": str(exc)[:120]})
            continue
        if res.get("written"):
            enriched.append({"gap_key": key, "query": query, "fetched": True,
                             "atom_key": res.get("atom_key"),
                             "trust": res.get("evidence", {}).get("authority")})
        else:
            enriched.append({"gap_key": key, "query": query, "fetched": False,
                             "reason": res.get("error", "no content")})
    n_ok = sum(1 for e in enriched if e["fetched"])
    return _ok(rid, {"enriched": enriched, "gaps_scanned": len(gaps),
                     "fetched": n_ok})


def gap_query(kernel, ctx, key, content) -> str:
    """Derive a fetch query for a gap atom: prefer a human-readable alias (the concept
    name), else the leading words of its content. Namespace prefixes are stripped so
    'concept:icarus' queries 'icarus'."""
    try:
        aliases = ctx.get_aliases_by_key(key) if hasattr(ctx, "get_aliases_by_key") else None
    except Exception:
        aliases = None
    if aliases:
        term = str(aliases[0]).split(":")[-1].replace("_", " ").strip()
        if len(term) >= 2:
            return term[:80]
    text = (content or "").strip()
    if len(text) >= 2:
        return " ".join(text.split()[:6])[:80]
    return ""


def handle_semantic_learn(kernel, rid, data, session, ctx, scopes) -> dict:
    """semantic.learn [limit=] [dim=] [max_vocab=] — learn a distributional embedding
    model (PPMI + SVD, numpy) from the FULL corpus (nucleus ontology + this cortex)
    and persist it to the nucleus vault so every session's semantic.search uses it.
    Admin/librarian only (a heavy, shared, one-shot compute)."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    from lib.akasha.semantic_learn import OntologyLearner, tokens, store_model
    nucleus = getattr(session, "nucleus", None)
    if nucleus is None:
        return _err(rid, -32002, "Nucleus unavailable")
    if not OntologyLearner.available():
        return _err(rid, -32002,
                    "numpy unavailable — learner needs numpy (search degrades to the "
                    "feature-hashing floor)")
    limit = max(10, min(int(data.get("limit", 40000)), 200000))
    min_len = int(data.get("min_len", 8))
    dim = max(8, min(int(data.get("dim", 64)), 256))
    max_vocab = max(50, min(int(data.get("max_vocab", 2000)), 8000))

    docs, n = [], 0
    for src in (nucleus.core, ctx.core):
        # Bounded bulk read that RELEASES the store immediately (not a lazy scan held across the
        # loop — that starves interactive requests on the Silica store). Cap it (never the whole
        # store) and skip raw source / external rows by meta so neither bloats the read nor teaches
        # the model (ASI06). Raw Source carries concept=source_* / provenance, so no per-row alias
        # read is needed on the hot store.
        try:
            chunks = src.get_all_chunks(limit=limit) or []
        except Exception:
            chunks = []
        for row in chunks:
            content = row.get("content") or ""
            if len(content) >= min_len and not _excluded_from_learning(row.get("meta")):
                docs.append(tokens(content))
                n += 1
                if n >= limit:
                    break
        if n >= limit:
            break

    learner = OntologyLearner(dim=dim, max_vocab=max_vocab)
    if not learner.learn(docs):
        return _err(rid, -32002,
                    f"learn failed (docs={len(docs)} — need >=3 with a shared vocab)")
    store_model(nucleus, learner)
    return _ok(rid, {"status": "learned", "docs": len(docs),
                     "vocab": len(learner.vocab), "dim": dim})


def handle_node_learn(kernel, rid, data, session, ctx, scopes) -> dict:
    """node.learn [dim=] [walks=] [length=] — learn STRUCTURAL node embeddings from the
    typed-link graph (random walks → PPMI+SVD, the NodeWalkLearner). Complementary to the
    content model: it captures "connected the same way" rather than "means the same".
    Persisted to the nucleus vault. Admin/librarian only, numpy-gated."""
    err = kernel._assert_admin(session)
    if err:
        return _err(rid, -32003, err)
    from lib.akasha.semantic_learn import NodeWalkLearner, store_node_model
    nucleus = getattr(session, "nucleus", None)
    if nucleus is None:
        return _err(rid, -32002, "Nucleus unavailable")
    if not NodeWalkLearner.available():
        return _err(rid, -32002, "numpy unavailable — node embeddings need numpy")
    dim = max(8, min(int(data.get("dim", 32)), 256))
    walks = max(1, min(int(data.get("walks", 10)), 40))
    length = max(2, min(int(data.get("length", 8)), 20))
    links = []
    for src in (nucleus.core, ctx.core):
        try:
            links.extend(src.get_all_links(limit=200000) or [])
        except Exception:
            pass
    nwl = NodeWalkLearner(dim=dim, walks_per_node=walks, length=length, seed=7)
    if not nwl.learn(links):
        return _err(rid, -32002,
                    f"node.learn failed (links={len(links)} — need a connected graph)")
    store_node_model(nucleus, nwl)
    return _ok(rid, {"status": "learned", "links": len(links),
                     "nodes": len(nwl.vocab), "dim": dim})


def meta_scope_flag(kernel, data) -> bool:
    return str(data.get("meta") or data.get("all") or "").strip().lower() in ("1", "yes", "true", "all", "y")


def meta_scope_keys(kernel, ctx) -> set:
    # Lexicon layer via set membership (synchronous); abstract hubs via an INDEXED
    # alias-prefix scan (`alias LIKE 'emo:%'` — a prefix range, index-backed), which is
    # synchronous and does not depend on the async ns:/leaf: derivation queue having
    # drained. Built once per call; unioned local cell + nucleus.
    keys: set = set()
    nucleus = getattr(ctx, "_nucleus", None)
    try:
        keys |= set(ctx.get_collection_members("rels") or [])          # reldef: layer
        keys |= set(ctx.get_collection_members("namespaces") or [])    # nsdef: layer
        for ns in _META_NAMESPACES:                              # abstract hubs
            for r in (ctx.core.get_aliases_by_pattern(f"{ns}:%") or []):
                keys.add(r["key"])
            if nucleus:
                for r in (nucleus.core.get_aliases_by_pattern(f"{ns}:%") or []):
                    keys.add(r["key"])
    except Exception:
        pass
    return keys


def handle_node_sim(kernel, rid, data, session, ctx, scopes) -> dict:
    """node.sim id= [limit=] — atoms STRUCTURALLY similar to an atom (nearest node-walk
    embeddings): "connected the same way". Requires a learned model (node.learn) and that
    the anchor is a linked node. Scope-filtered. Complements semantic.search (content)."""
    from lib.akasha.semantic_learn import get_node_model, cosine as _lcos
    nucleus = getattr(session, "nucleus", None)
    model = get_node_model(nucleus) if nucleus is not None else None
    if model is None:
        return _err(rid, -32002, "no structural model — run node.learn first (or numpy absent)")
    target = (data.get("id") or data.get("key") or session.last_written_id or "").strip()
    if not target:
        return _err(rid, -32602, "node.sim requires 'id'")
    anchor = ctx.resolve_alias(target) or target
    avec = model.node_vector(anchor)
    if not avec:
        # Proto-word hub (e.g. 'rome'): the real links hang off its senses, each of
        # which --specializes--> the proto-word. Anchor on the sense that IS in the
        # structural model, so `node.sim rome` behaves like node.sim on
        # geo:capital:rome — parity with how `r`/the explorer resolve a bare word.
        for _src, _rel in (ctx.get_incoming_links(anchor, "specializes") or []):
            _sv = model.node_vector(_src)
            if _sv:
                anchor, avec = _src, _sv
                break
    if not avec:
        return _err(rid, -32002,
                    f"atom '{anchor}' is not in the structural model (no links, or re-run node.learn)")
    _meta = set() if meta_scope_flag(kernel, data) else meta_scope_keys(kernel, ctx)
    scored = []
    for key in list(model.vocab.keys()):
        if key == anchor:
            continue
        if key in _meta:                       # lexicon definition atom — not a content neighbour
            continue
        if scopes and not ctx.check_access(key, scopes):
            continue
        v = model.node_vector(key)
        if not v:
            continue
        s = _lcos(avec, v)
        if s > 0.0:
            scored.append((s, key))
    scored.sort(key=lambda t: t[0], reverse=True)
    window, page = _paginate(scored, data.get("limit"), data.get("cursor"),
                             default=10, max_limit=100)
    results = [{"key": k, "name": _readable(ctx, k), "score": round(s, 4),
                "preview": (ctx.get_chunk(k) or "")[:80]} for s, k in window]
    return _ok(rid, {"anchor": anchor, "results": results, "count": len(results),
                     "mode": "structural", "page": page})


def handle_semantic_search(kernel, rid, data, session, ctx, scopes) -> dict:
    """semantic.search query=|id= [limit=] [scan=] — rank atoms by cosine similarity.
    `query=` is free text; `id=`/`like=` anchors on an EXISTING atom ("find atoms like
    THIS one") — its own content is re-embedded as the query and the anchor is excluded
    from the results. Scope-filtered (fail-closed). Uses the learned model when one has
    been built (re-embedding candidates into one space) else the stored feature-hashing
    vectors. `tier` says which; `anchor` echoes the atom key when id-anchored."""
    query = (data.get("query") or data.get("q") or "").strip()
    anchor_ref = (data.get("id") or data.get("like") or "").strip()
    anchor_key = None
    if anchor_ref and not query:
        # Atom-anchored: resolve to an existing atom and search by its own meaning.
        resolved = ctx.resolve_alias(anchor_ref) or anchor_ref
        content = ctx.get_scoped_chunk(resolved, scopes) if scopes else ctx.get_chunk(resolved)
        if content is None:
            query = anchor_ref                       # not an atom → treat as free text
        else:
            query, anchor_key = content, resolved
    if not query:
        return _err(rid, -32602, "semantic.search requires 'query' or 'id'")
    limit = max(1, min(int(data.get("limit", 10)), 100))
    scan = max(1, min(int(data.get("scan", 2000)), 20000))
    _t0 = time.time()      # A56 §5 — a single slow call is logged, attributable to THIS query
    # A57 (R6) — a semantic.search must not become the writer's bottleneck. TWO bounds:
    #   • a TIME budget (AKASHA_SEARCH_BUDGET_S, default 10 s): past it, return the best candidates
    #     ranked SO FAR with partial=true + one INFO — never a 50 s stall;
    #   • a CANDIDATE cap (AKASHA_SEARCH_CANDIDATES, default 500): score at most this many, taking the
    #     semcache-plan (hot) atoms FIRST so the cap keeps the most-relevant corpus.
    try:
        _budget_s = float(os.environ.get("AKASHA_SEARCH_BUDGET_S", "10") or 10)
    except (TypeError, ValueError):
        _budget_s = 10.0
    try:
        _cand_cap = int(os.environ.get("AKASHA_SEARCH_CANDIDATES", "500") or 500)
    except (TypeError, ValueError):
        _cand_cap = 500
    _cand_cap = max(1, _cand_cap)

    from lib.akasha.semantic_learn import get_shared_model, cosine as _lcos
    nucleus = getattr(session, "nucleus", None)
    model = get_shared_model(nucleus) if nucleus is not None else None
    tensor = getattr(ctx, "tensor", None)

    if model is not None and model.embed_text(query):
        tier = "learned"
        qvec = model.embed_text(query)
    elif tensor is not None and tensor.embed("", query, {}):
        tier = "floor"
        qvec = tensor.embed("", query, {})
    else:
        return _ok(rid, {"query": query, "results": [], "count": 0, "tier": "none"})

    _meta = set() if meta_scope_flag(kernel, data) else meta_scope_keys(kernel, ctx)
    import json as _json
    # The searchable corpus is the SHARED ONTOLOGY, which lives in the nucleus — not
    # in the session's private cell. Streaming only ctx.stream() searched an isolated
    # guest cell (near-empty) and returned a handful of stray atoms; the ingredients /
    # concepts a guest MCP "read-first" client wants were invisible. Union the nucleus
    # candidates (deduped), exactly like discover_atoms/explore. Every candidate still
    # passes ctx.check_access(key, scopes), so isolation is unchanged — the nucleus holds
    # shared ground-truth only, never another user's private cell atoms.
    _rows = list(ctx.stream(limit=scan) or [])
    if nucleus is not None and nucleus is not ctx:
        # NucleusEngine has no stream() wrapper — go straight to the backend primitive.
        # F50 §3 (altitude check): `scan` is capped above (≤20000), and fetch_stream is now
        # O(scan) — a bounded newest-`scan` index walk + `scan` decodes, never the whole store.
        # A guest/MCP search can never request an uncapped stream, so this call is not lethal.
        _rows += list(nucleus.core.fetch_stream(scan) or [])
    # A57 — score the semcache-plan (hot) atoms FIRST, so a budget/cap cut keeps the most relevant.
    _plan_keys: set = set()
    try:
        if nucleus is not None:
            _plan_keys = set(nucleus.core.get_collection_members("set:stage:cache_plan") or [])
    except Exception:
        _plan_keys = set()
    if _plan_keys:
        _rows.sort(key=lambda r: 0 if r.get("key") in _plan_keys else 1)
    _seen_keys: set = set()
    scored = []
    _n_cand = 0
    partial = False
    _partial_reason = None
    for row in _rows:
        key = row.get("key")
        if not key or key in _seen_keys:
            continue
        _seen_keys.add(key)
        if key == anchor_key or key in _meta or (scopes and not ctx.check_access(key, scopes)):
            continue
        content = row.get("content") or ""
        if tier == "learned":
            vec = model.embed_text(content)             # re-embed → same space as qvec
        else:
            meta = row.get("meta")
            if isinstance(meta, str):
                try:
                    meta = _json.loads(meta)
                except Exception:
                    meta = {}
            vec = meta.get("semantic_vector") if isinstance(meta, dict) else None
        if not vec:
            continue
        s = _lcos(qvec, vec)
        if s > 0.0:
            scored.append((s, key, content))
        # A57 — a scored candidate counts toward the cap; check the cap + time budget together so a
        # huge corpus (2,043 candidates) degrades to the best-ranked-so-far, not a multi-second stall.
        _n_cand += 1
        if (time.time() - _t0) > _budget_s:
            partial = True; _partial_reason = "budget"; break
        if _n_cand >= _cand_cap:
            partial = True; _partial_reason = "cap"; break
    scored.sort(key=lambda t: t[0], reverse=True)
    window, page = _paginate(scored, data.get("limit"), data.get("cursor"),
                             default=10, max_limit=100)
    results = [{"key": k, "name": _readable(ctx, k), "score": round(s, 4), "preview": c[:80]}
               for s, k, c in window]
    out = {"results": results, "count": len(results), "tier": tier, "page": page,
           "partial": partial, "candidates": _n_cand}
    if partial:
        out["partial_reason"] = _partial_reason
    if anchor_key:
        out["anchor"] = anchor_key
    else:
        out["query"] = query
    # A57-b — the candidate cap is hit by EVERY large query (1,191 INFO lines in 11 h — pure noise),
    # so do NOT log it; the client still sees partial=true. Log ONE INFO only on a TIME-budget cut
    # (the rare, interesting case — the corpus is genuinely slow). Both reasons feed a Health counter
    # so the RATE of truncation is visible as an aggregate, not per-call spam.
    if partial:
        _search_partial_incr(_partial_reason)
        if _partial_reason == "budget":
            import hashlib as _hl2
            logger.info("[semantic.search] partial q=%s reason=budget candidates=%d t=%.1fs "
                        "(budget=%.0fs)",
                        _hl2.sha1((anchor_key or query).encode("utf-8", "replace")).hexdigest()[:8],
                        _n_cand, time.time() - _t0, _budget_s)
    # A56 §5 — one WARNING when a single call exceeds 30 s, so a 100 s wait is attributable to
    # the query (candidates walked) rather than only visible downstream as `slowest=`.
    _elapsed = time.time() - _t0
    if _elapsed > 30.0:
        import hashlib as _hl
        _qh = _hl.sha1((anchor_key or query).encode("utf-8", "replace")).hexdigest()[:8]
        _ipc_q = 0
        try:
            import api.portals.cell_ipc as _ipc_mod
            _ipc_q = int((_ipc_mod.server_stats() or {}).get("queued") or 0)
        except Exception:
            pass
        logger.warning("[semantic.search] slow q=%s t=%.1fs candidates=%d ipc_q=%d",
                       _qh, _elapsed, len(_rows), _ipc_q)
    return _ok(rid, out)


def schedule_semantic_learn(kernel) -> None:
    """After the ontology is loaded, learn the distributional embedding model in the
    background so semantic.search / dream are smart from (shortly after) startup —
    with no external model. Non-blocking (a daemon thread), numpy-gated; whether it runs
    is decided by declared facts (`_autolearn_disabled_reason`). Gates on the relations-complete sentinel so it
    learns on the WHOLE corpus (not the few atoms present at boot-submit time), and
    self-heals a previously-persisted stunted model by re-learning when the corpus has
    grown far beyond what that model was trained on. This is the 'startup makes Akasha
    an order smarter' hook: the graph learns from itself."""
    _skip = _autolearn_disabled_reason(kernel.series)
    if _skip:
        logger.info("[Kernel] Auto semantic.learn skipped — %s", _skip)
        return
    try:
        from lib.akasha.semantic_learn import OntologyLearner, tokens, get_shared_model, store_model
    except Exception:
        return
    if not OntologyLearner.available():          # numpy absent → floor tier, no learn
        return
    nucleus = getattr(kernel.manager, "shared_nucleus", None)
    if nucleus is None:
        return

    def _run():
        try:
            # Gate on the relations-complete sentinel, exactly like node.learn. The
            # "Ontology boot load complete" log fires when jobs are SUBMITTED, not
            # when the atoms are written (the JCL writes them async), so reading the
            # corpus immediately would learn a stunted model on the few hundred atoms
            # present at that instant and persist it forever. Wait for the whole atom
            # set to exist first.
            from lib.akasha import lifecycle
            import glob as _glob
            sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
            deadline = time.time() + 7200
            while time.time() < deadline:
                if lifecycle.is_shutting_down():
                    return
                if kernel._relations_ready():
                    break
                time.sleep(5)
            if lifecycle.is_shutting_down():
                return                     # don't start a numpy learn during teardown

            import json as _json
            # BOUND the read AND the working set. The old `get_all_chunks(limit=_cap)`
            # materialized _cap rows at once; once a large Source corpus (e.g. 26k survey
            # rows, each carrying its full verbatim payload in `source_metadata`) dominates
            # the store, that capped page is ITSELF a corpus-sized RAM spike — the boot-time
            # OOM that silently kills the daemon during the background learn (it coincides
            # with the still-running Source ingest). Stream instead: read row-by-row and
            # DISCARD raw-source / external rows immediately (they must never teach the model
            # — ASI06), holding only the curated rows we actually learn+bake. Peak RAM =
            # curated rows, not _cap raw rows. Scanning stays capped at _cap (bounded I/O).
            # Capacity tuned by AKASHA_AUTOLEARN_MAX (a deployment fact: the host's budget).
            try:
                _cap = max(0, int(os.environ.get("AKASHA_AUTOLEARN_MAX", "40000")))
            except (TypeError, ValueError):
                _cap = 40000
            if _cap == 0:
                return
            # INTERACTIVE PRIORITY (Harmonia principle): this background learn must never hold the
            # store in a way that starves an interactive request (a login's identity read). Read
            # the capped set in ONE bulk fetch that RELEASES the store immediately, then process
            # the in-memory list — do NOT hold a lazy scan across the whole loop (a streaming
            # `iter_all_chunks` here starved login on the Silica store: the long-held read blocked
            # the vault lookup → auth.status raced not-initialized → premature Genesis on redeploy).
            # Raw Source rows are excluded by meta (`concept=source_*` / `provenance=source`), which
            # the batched bootstrap stamps — no per-row alias read needed on the hot store.
            curated, docs = [], []
            for row in (nucleus.core.get_all_chunks(limit=_cap) or []):
                content = row.get("content") or ""
                if len(content) < 8 or _excluded_from_learning(row.get("meta")):
                    continue                      # raw source / external → never learned/baked
                curated.append(row)
                docs.append(tokens(content))

            # Self-heal: keep an existing model only if it was trained on a corpus
            # comparable to what exists now. A model persisted from an early-boot race
            # (tiny n_docs) is discarded and re-learned — so installs already carrying
            # a stunted model heal on the next boot. Legacy models without n_docs fall
            # back to vocab size as the proxy.
            existing = get_shared_model(nucleus)
            if existing is not None:
                prev = getattr(existing, "n_docs", 0) or 0
                if prev <= 0:
                    prev = len(getattr(existing, "vocab", {}) or {})
                if len(docs) < max(500, prev * 3):
                    return                                   # adequate — keep it
                logger.info("[Kernel] semantic model stunted (trained~%d docs, now %d) "
                            "— relearning", prev, len(docs))

            learner = OntologyLearner(dim=64, max_vocab=2000)
            if not learner.learn(docs):
                return
            store_model(nucleus, learner)
            logger.info("[Kernel] Auto semantic.learn complete (docs=%d, vocab=%d)",
                        len(docs), len(learner.vocab))

            # Per-atom bake-in: write the learned vector onto each atom's meta so the
            # cosine paths (dream, stored-vector reads) use the learned tier without
            # re-embedding. Bounded; nucleus writes are commit-forward (no guard).
            #
            # PACED (resilience law: background growth is never urgent — it must not starve
            # the serving path). On the C-tier line this loop re-embeds+re-writes tens of
            # thousands of atoms, a sustained CPU+disk burst on the writer daemon. Unthrottled
            # it pegs a small VPS so the serve-only portal (uvicorn) can't finish its
            # attach-to-writer handshake and never starts listening ("couldn't connect" for
            # minutes). A brief yield every _pace_every atoms hands the OS scheduler room to
            # service the portal; total added wall-time is negligible for a background bake.
            # Tunable: AKASHA_AUTOLEARN_PACE (atoms/yield, 0 = no pacing).
            try:
                _pace_every = max(0, int(os.environ.get("AKASHA_AUTOLEARN_PACE", "100")))
            except (TypeError, ValueError):
                _pace_every = 100
            baked = 0
            for row in curated:                    # already filtered (curated content only)
                content = row.get("content") or ""
                vec = learner.embed_text(content)
                if not vec:
                    continue
                try:
                    m = _json.loads(row.get("meta") or "{}")
                except Exception:
                    m = {}
                m["semantic_vector"] = vec
                # Preserve created_at (the chunks column is 'created_at', not 'ts')
                # so re-writing meta does not reset the atom's timestamp.
                nucleus.core.put_chunk_raw(
                    row["key"], content, _json.dumps(m, ensure_ascii=False),
                    row.get("author", "system"), row.get("status", "verified"),
                    row.get("created_at") or time.time())
                baked += 1
                if _pace_every and baked % _pace_every == 0:
                    if lifecycle.is_shutting_down():
                        return
                    time.sleep(0.05)          # yield CPU/disk to the serving portal
                if baked >= _cap:
                    break
            if baked:
                logger.info("[Kernel] Learned vectors baked into %d atoms", baked)
        except Exception as exc:                          # never break boot
            logger.warning("[Kernel] Auto semantic.learn failed (non-fatal): %s", exc)

    import threading
    threading.Thread(target=_run, name="semantic-autolearn", daemon=True).start()


def schedule_node_learn(kernel) -> None:
    """Structural sibling of _schedule_semantic_learn: after the ontology loads,
    learn the STRUCTURAL node embeddings (NodeWalkLearner: random walks over the
    typed-link graph → PPMI+SVD) in the background so `node.sim` works from
    startup with no operator step. Non-blocking daemon thread, numpy-gated, and
    skipped if a model already persists (idempotent across restarts); whether it runs
    is decided by declared facts (`_autolearn_disabled_reason`). Unlike the content model it needs the LINK
    graph — the deferred GLOBAL relations phase — so it waits for that phase's
    completion sentinel (`_relations`) before learning, never a fixed timeout, so
    a slow host does not learn on a half-built graph."""
    _skip = _autolearn_disabled_reason(kernel.series)
    if _skip:
        logger.info("[Kernel] Auto node.learn skipped — %s", _skip)
        return
    try:
        from lib.akasha.semantic_learn import (NodeWalkLearner, get_node_model,
                                               store_node_model)
    except Exception:
        return
    if not NodeWalkLearner.available():          # numpy absent → no structural model
        return
    nucleus = getattr(kernel.manager, "shared_nucleus", None)
    if nucleus is None:
        return

    def _run():
        try:
            if get_node_model(nucleus) is not None:      # already learned/persisted
                return
            # The structural model needs the LINK graph, produced by the deferred
            # GLOBAL relations phase (all al/ln/set.add run as one job AFTER every
            # pack's atoms). A fixed wait / link-count heuristic is wrong on a slow
            # host: the relations job can still be running (links trickling in), so
            # we would learn on a half-built graph and most atoms would be absent
            # from the model. Gate on the authoritative completion signal instead —
            # the `_relations` filesystem sentinel that _boot_load_ontology writes
            # when the relations phase finishes. Only then is the graph whole.
            from lib.akasha import lifecycle
            import glob as _glob
            sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
            gated = False
            deadline = time.time() + 7200               # generous ceiling (slow hosts)
            while time.time() < deadline:
                if lifecycle.is_shutting_down():
                    return
                if kernel._relations_ready():
                    gated = True
                    break
                time.sleep(5)
            if lifecycle.is_shutting_down():
                return                     # don't start a numpy learn during teardown
            if not gated:
                logger.info("[Kernel] Auto node.learn: relations-complete sentinel not "
                            "seen within ceiling — learning best-effort on current links")
            # Bound the link read (env-tunable), same rationale as the content learn:
            # never materialize an unbounded link set into RAM at boot on a tight host.
            try:
                _lcap = max(0, int(os.environ.get("AKASHA_AUTOLEARN_LINK_MAX", "200000")))
            except (TypeError, ValueError):
                _lcap = 200000
            if _lcap == 0:
                return
            try:
                links = nucleus.core.get_all_links(limit=_lcap) or []
            except Exception:
                links = []
            if len(links) < 50:
                logger.info("[Kernel] Auto node.learn skipped (graph too sparse: "
                            "links=%d)", len(links))
                return
            nwl = NodeWalkLearner(dim=32, walks_per_node=10, length=8, seed=7)
            if not nwl.learn(links):
                return
            store_node_model(nucleus, nwl)
            logger.info("[Kernel] Auto node.learn complete (links=%d, nodes=%d)",
                        len(links), len(nwl.vocab))
        except Exception as exc:                          # never break boot
            logger.warning("[Kernel] Auto node.learn failed (non-fatal): %s", exc)

    import threading
    threading.Thread(target=_run, name="node-autolearn", daemon=True).start()
