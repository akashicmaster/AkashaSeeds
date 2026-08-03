"""
Pulse Concept Model — atom-based access analytics for the archives portal.

Design of record: `docs/for-llm/pulse-analytics-spec.md`. An access is an immutable, private
`event` atom linked (`sys:hit_of`) to the REAL concept seen — so analytics rides on the same
graph the archives serve, and concept roll-up / clickpaths / acquisition all fall out of ordinary
traversal instead of URL string-counting. Counts are DERIVED from set cardinality and a bounded
window scan; no atom is ever mutated (content-addressing + crash-stop preserved).

Two surfaces:

  • `pulse.emit`  — the single WRITER (write-gated: never a guest). The archives beacon / a
    server-side capture identity calls this once per view. LOW-priority, off the critical path.
  • the reference / aggregation / analysis READ ops — `pulse.overview`, `pulse.top`,
    `pulse.concept`, `pulse.path`, `pulse.acquisition`, `pulse.recent`, `pulse.gap`,
    `pulse.narrate`. All are **admin-only** (`action="sys.telemetry"` → Capability.TELEMETRY,
    held by admin alone): analytics is private operational data, never guest-readable.

Privacy (fixed): events carry no PII. The caller supplies only a coarse referrer class, a
country, a UA class, and a within-day `visit` id derived from a DAILY-ROTATING salted hash
(unrecoverable tomorrow — no cross-day tracking). Events live in `scope:analytics` (private) and
are `provenance="analytics"` → excluded from `semantic.learn` / `gap.scan` and never woven.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Pulse")

# Relations (defined in the lexicon — scripts/gen_lexicon.py CORE_RELS).
HIT_OF   = "sys:hit_of"      # event → the concept atom that was seen
HIT_PREV = "sys:hit_prev"    # event → the previous event in the same visit (clickpath edge)

# Set-name prefixes (reserved analytics namespaces — CORE_NS: pulse / src / visit).
S_DAY     = "pulse:day:"     # pulse:day:<YYYY-MM-DD>      — every event that day
S_CONCEPT = "pulse:concept:" # pulse:concept:<concept_key> — |set| = hits on that concept
S_SRC     = "pulse:src:"     # pulse:src:<referrer>        — acquisition bucket
S_VISIT   = "visit:"         # visit:<visit_id>            — events in one visit
S_SUMDAY  = "pulse:sumday:"  # pulse:sumday:<YYYY-MM-DD>   — a compacted day's summary atom
S_SUMSET  = "pulse:summaries" # all daily summary atoms (post-compaction index)

ANALYTICS_SCOPE = "scope:analytics"
PROVENANCE      = "analytics"
_SECS_PER_DAY   = 86400
# Roll-up walks these incoming relations to find a concept's descendants (sub-notions, members
# of a field / world). Both are traversed both ways by the graph, so this IS the mutual reference.
_ROLLUP_RELS    = ("sys:part_of", "sys:is_a")
_MAX_SCAN       = 50000      # hard cap on events scanned per read (no silent truncation — flagged)


class PulseConcept(BaseConcept):
    """Record accesses as concept-linked event atoms; aggregate and analyse them (admin-only)."""

    CONCEPT_PREFIX = "pulse"
    CONCEPT_LABEL  = "access analytics — concept-level traffic over the archives (admin/telemetry)"

    # sys.telemetry → Capability.TELEMETRY (admin only): the reads are private operational data.
    _TEL = "sys.telemetry"

    CONCEPT_METHODS = {
        "emit":        {"op": "op_emit", "action": "write",
                        "desc": ("Record one access as a concept-linked event atom (the beacon "
                                 "writer; never a guest): pulse.emit concept=<alias|key> "
                                 "[surface=] [ref=] [visit=] [prev=] [geo=] [ua=]")},
        "overview":    {"op": "op_overview", "action": _TEL, "cli": "pulse.overview", "args": [],
                        "desc": "Traffic summary over a window: pulse.overview [window=7d]"},
        "top":         {"op": "op_top", "action": _TEL, "cli": "pulse.top", "args": [],
                        "desc": ("Top concepts by hits: pulse.top [window=7d] [limit=20] [ns=] "
                                 "— the concept-level demand ranking")},
        "concept":     {"op": "op_concept", "action": _TEL, "cli": "pulse.concept", "args": ["id"],
                        "desc": ("Hits for one concept, ROLLED UP through its sub-tree: "
                                 "pulse.concept id=<alias|key> [window=7d]")},
        "path":        {"op": "op_path", "action": _TEL, "cli": "pulse.path", "args": [],
                        "desc": ("Most-walked semantic clickpaths (visit sequences): "
                                 "pulse.path [window=7d] [limit=15]")},
        "acquisition": {"op": "op_acquisition", "action": _TEL, "cli": "pulse.acquisition", "args": [],
                        "desc": "Referrer breakdown (how visitors arrive): pulse.acquisition [window=7d]"},
        "recent":      {"op": "op_recent", "action": _TEL, "cli": "pulse.recent", "args": [],
                        "desc": "Most recent access events (inspection): pulse.recent [limit=25]"},
        "gap":         {"op": "op_gap", "action": _TEL, "cli": "pulse.gap", "args": [],
                        "desc": ("High-traffic ∩ thin concepts — the enrich-next queue: "
                                 "pulse.gap [window=30d] [limit=20]")},
        "narrate":     {"op": "op_narrate", "action": _TEL, "cli": "pulse.narrate", "args": [],
                        "desc": "Plain-language summary of the window's attention: pulse.narrate [window=7d]"},
        "compact":     {"op": "op_compact", "action": "write", "cli": "pulse.compact", "args": [],
                        "desc": ("Roll day-old raw events into per-day summary atoms and soft-evict "
                                 "the raw events (bounds growth; keeps daily counts forever): "
                                 "pulse.compact [keep=2]")},
    }

    # ── time / window helpers ────────────────────────────────────────────────────
    @staticmethod
    def _now() -> float:
        return time.time()

    def _day_str(self, ts: float) -> str:
        return time.strftime("%Y-%m-%d", time.gmtime(ts))

    def _parse_window(self, window: Any) -> int:
        """A window like '7d' / '24h' / '30d' / 'all' → number of DAYS to scan (>=1).
        'all' is capped to ~2 years so a read stays bounded."""
        w = str(window or "7d").strip().lower()
        if w in ("all", "*", "max"):
            return 730
        try:
            if w.endswith("h"):
                return max(1, (int(w[:-1]) + 23) // 24)
            if w.endswith("d"):
                return max(1, int(w[:-1]))
            if w.endswith("w"):
                return max(1, int(w[:-1]) * 7)
            return max(1, int(w))
        except (TypeError, ValueError):
            return 7

    def _window_days(self, window: Any) -> List[str]:
        """The list of day strings (newest first) covered by the window."""
        n = self._parse_window(window)
        now = self._now()
        return [self._day_str(now - i * _SECS_PER_DAY) for i in range(n)]

    def _intf(self, v: Any, default: int, lo: int = 1, hi: int = 500) -> int:
        try:
            return max(lo, min(int(v), hi))
        except (TypeError, ValueError):
            return default

    # ── graph helpers ────────────────────────────────────────────────────────────
    def _members(self, set_name: str) -> List[str]:
        try:
            return list(self.cortex.get_collection_members(set_name) or [])
        except Exception:
            return []

    def _meta(self, key: str) -> Dict[str, Any]:
        try:
            return self.cortex.get_meta(key) or {}
        except Exception:
            return {}

    def _alias(self, key: str) -> str:
        try:
            aliases = self.cortex.get_aliases_by_key(key) or []
        except Exception:
            aliases = []
        return next((a for a in aliases if ":" in a), aliases[0] if aliases else key)

    def _label(self, alias: str) -> str:
        return alias.split(":")[-1].replace("_", " ") if ":" in alias else alias

    def _resolve(self, ref: str) -> Optional[str]:
        ref = (ref or "").strip()
        if not ref:
            return None
        try:
            if self.cortex.get_chunk(ref) is not None:
                return ref
            return self.cortex.resolve_alias(ref)
        except Exception:
            return None

    def _scan_events(self, window: Any) -> Dict[str, Any]:
        """One bounded pass over the window's day-sets. Returns the raw event rows (meta dicts,
        newest-first-ish) plus a `truncated` flag. Every read op derives its answer from this —
        the day-set scan needs only get_collection_members, so no set-enumeration primitive is
        required. Cost is bounded by window traffic and the _MAX_SCAN cap."""
        rows: List[Dict[str, Any]] = []
        seen = set()
        truncated = False
        for day in self._window_days(window):
            for ek in self._members(S_DAY + day):
                if ek in seen:
                    continue
                seen.add(ek)
                if len(rows) >= _MAX_SCAN:
                    truncated = True
                    break
                m = self._meta(ek)
                if m.get("provenance") != PROVENANCE:
                    continue
                rows.append({
                    "key": ek,
                    "ts": float(m.get("ts", 0) or 0),
                    "concept": m.get("concept_key") or "",
                    "alias": m.get("concept_alias") or "",
                    "surface": m.get("surface") or "",
                    "ref": m.get("ref") or "direct",
                    "visit": m.get("visit") or "",
                    "ua": m.get("ua") or "",
                    "geo": m.get("geo") or "",
                })
            if truncated:
                break
        return {"rows": rows, "truncated": truncated}

    def _summaries(self, window: Any) -> Dict[str, Any]:
        """Compacted per-day summary counts inside the window (raw events already soft-evicted).
        Returns aggregated concept / src / surface counts and totals so a read spanning old,
        compacted days still reports correct concept-level numbers (paths/recent are raw-only)."""
        concept: Dict[str, int] = {}
        alias: Dict[str, str] = {}
        src: Dict[str, int] = {}
        surface: Dict[str, int] = {}
        hits = human = 0
        visits = 0
        for day in self._window_days(window):
            for sk in self._members(S_SUMDAY + day):
                m = self._meta(sk)
                if m.get("type") != "pulse:summary":
                    continue
                for k, n in (m.get("concepts") or {}).items():
                    concept[k] = concept.get(k, 0) + int(n)
                for k, a in (m.get("aliases") or {}).items():
                    alias.setdefault(k, a)
                for k, n in (m.get("srcs") or {}).items():
                    src[k] = src.get(k, 0) + int(n)
                for k, n in (m.get("surfaces") or {}).items():
                    surface[k] = surface.get(k, 0) + int(n)
                hits += int(m.get("hits", 0)); human += int(m.get("human", 0))
                visits += int(m.get("visits", 0))
        return {"concept": concept, "alias": alias, "src": src, "surface": surface,
                "hits": hits, "human": human, "visits": visits}

    @staticmethod
    def _tally(rows: List[Dict[str, Any]], field: str) -> List[tuple]:
        counts: Dict[str, int] = {}
        for r in rows:
            v = r.get(field) or ""
            if v:
                counts[v] = counts.get(v, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    def _wcore(self):
        """The backend store analytics is written to. The NUCLEUS core when present — analytics is
        a single shared record, and every authenticated session reads the nucleus via the composite
        fallback/merge (get_meta / get_collection_members), so writer and every reader agree.
        Falls back to the local core. Writes go through core primitives directly (no weave, no
        proto-words, private scope) — the same 'pure store' pattern NucleusEngine.put_atom uses."""
        nuc = getattr(self.cortex, "_nucleus", None)
        return (nuc.core if nuc is not None else self.cortex.core)

    def _put_event(self, core, content: str, meta: dict, author: str) -> str:
        key = __import__("hashlib").sha256(content.encode("utf-8")).hexdigest()
        core.put_chunk_raw(key, content, json.dumps(meta, ensure_ascii=False), author,
                           "verified", meta.get("ts") or self._now())
        try:
            core.put_chunk_access(key, [ANALYTICS_SCOPE, f"provenance:{PROVENANCE}"])
        except Exception:
            pass
        return key

    # ── WRITER ───────────────────────────────────────────────────────────────────
    def op_emit(self, concept: str = "", surface: str = "", ref: str = "",
                visit: str = "", prev: str = "", geo: str = "", ua: str = "") -> Dict[str, Any]:
        """[pulse.emit] Record ONE access as an immutable event atom linked (sys:hit_of) to the
        concept seen. The single writer — write-gated, so a guest can never call it (the archives
        capture runs under an authorized/system identity). Off the critical path by design: submit
        it LOW-priority / fire-and-forget from the portal. `concept` is an alias or key; `surface`
        is a coarse page kind (notion/word/hall/kitchen); `ref` a referrer class (google/github/
        direct); `visit` a within-day pseudonymous id; `prev` the previous concept (clickpath).
        No PII is accepted or stored."""
        ckey = self._resolve(concept)
        if not ckey:
            raise ValueError("pulse.emit: `concept` must resolve to an atom (alias or key).")
        calias = self._alias(ckey)
        ts = self._now()
        day = self._day_str(ts)
        ref = (ref or "direct").strip().lower()[:64] or "direct"
        surface = (surface or "").strip().lower()[:32]
        visit = (visit or "").strip()[:64]
        ua = (ua or "").strip().lower()[:16]
        author = getattr(self.session, "client_id", "system")
        core = self._wcore()
        # Content carries the entropy (content-addressing unifies only true duplicates); meta
        # carries the coarse, PII-free dimensions. Written straight to the store core — private
        # scope, no weave, no proto-words (provenance=analytics never enters vocabulary/learning).
        content = f"[pulse] {surface or 'page'}:{calias} via {ref} @ {ts!r} v={visit}"
        meta = {
            "role": "pulse:event", "provenance": PROVENANCE, "type": "pulse:event",
            "ts": ts, "day": day, "surface": surface, "concept_key": ckey,
            "concept_alias": calias, "ref": ref, "visit": visit, "ua": ua, "geo": (geo or "")[:8],
        }
        ekey = self._put_event(core, content, meta, author)
        try:
            core.put_link_raw(ekey, ckey, HIT_OF, 1.0, "forward", "atom", author, "verified", ts)
        except Exception:
            pass
        pkey = self._resolve(prev) if prev else ""
        if pkey and pkey != ckey:
            try:
                core.put_link_raw(ekey, pkey, HIT_PREV, 1.0, "forward", "atom", author, "verified", ts)
            except Exception:
                pass
        for s in (S_DAY + day, S_CONCEPT + ckey, S_SRC + ref) + ((S_VISIT + visit,) if visit else ()):
            try:
                core.add_to_collection(s, ekey)
            except Exception:
                pass
        return {"type": "pulse:emit", "recorded": True, "event": ekey,
                "concept": calias, "surface": surface, "day": day}

    # ── READ / AGGREGATION / ANALYSIS (admin-only) ────────────────────────────────
    def op_overview(self, window: Any = "7d") -> Dict[str, Any]:
        """[pulse.overview] A one-glance traffic summary over the window: total hits, unique
        concepts, unique visits, and the top surfaces. The natural landing command. Admin-only."""
        scan = self._scan_events(window)
        rows = scan["rows"]
        sm = self._summaries(window)
        concepts = {r["concept"] for r in rows if r["concept"]} | set(sm["concept"])
        visits = {r["visit"] for r in rows if r["visit"]}
        humans = [r for r in rows if r["ua"] != "bot"]
        surf = {s: n for s, n in self._tally(rows, "surface")}
        for s, n in sm["surface"].items():
            surf[s] = surf.get(s, 0) + n
        top_surf = sorted(surf.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
        return {
            "type": "pulse:overview", "window": str(window),
            "days_scanned": len(self._window_days(window)),
            "hits": len(rows) + sm["hits"],
            "human_hits": len(humans) + sm["human"],
            "bot_hits": (len(rows) - len(humans)) + (sm["hits"] - sm["human"]),
            "unique_concepts": len(concepts), "unique_visits": len(visits) + sm["visits"],
            "top_surfaces": [{"surface": s or "page", "hits": n} for s, n in top_surf],
            "compacted_hits": sm["hits"], "truncated": scan["truncated"],
        }

    def op_top(self, window: Any = "7d", limit: Any = 20, ns: str = "") -> Dict[str, Any]:
        """[pulse.top] The concept-level demand ranking — top concepts by hit count over the
        window. Optional `ns=` filters to one namespace (e.g. `phil:notion`). This is what GA
        cannot do: every row is a real concept, not a URL string. Admin-only."""
        lim = self._intf(limit, 20, 1, 200)
        scan = self._scan_events(window)
        rows = scan["rows"]
        sm = self._summaries(window)
        nsf = (ns or "").strip().rstrip(":")
        counts: Dict[str, Dict[str, Any]] = {}
        def _bump(key, alias, n):
            if not key:
                return
            if nsf and not (alias or "").startswith(nsf):
                return
            e = counts.setdefault(key, {"key": key, "alias": alias,
                                        "name": self._label(alias), "hits": 0})
            e["hits"] += n
        for r in rows:
            _bump(r["concept"], r["alias"], 1)
        for key, n in sm["concept"].items():
            a = sm["alias"].get(key) or self._alias(key)
            _bump(key, a, n)
        ranked = sorted(counts.values(), key=lambda e: (-e["hits"], e["alias"]))[:lim]
        return {"type": "pulse:top", "window": str(window), "ns": nsf or None,
                "count": len(ranked), "results": ranked, "truncated": scan["truncated"]}

    def _descendants(self, key: str, max_nodes: int = 2000) -> List[str]:
        """Keys of `key` and every concept beneath it via incoming sys:part_of / sys:is_a
        (bounded BFS, DAG-safe). This is how a concept's traffic rolls up its sub-tree."""
        out: List[str] = [key]
        seen = {key}
        frontier = [key]
        while frontier and len(seen) < max_nodes:
            nxt: List[str] = []
            for k in frontier:
                for rel in _ROLLUP_RELS:
                    try:
                        inc = self.cortex.get_incoming_links(k, rel) or []
                    except Exception:
                        inc = []
                    for pair in inc:
                        src = pair[0] if isinstance(pair, (list, tuple)) else pair
                        if src and src not in seen:
                            seen.add(src)
                            out.append(src)
                            nxt.append(src)
            frontier = nxt
        return out

    def op_concept(self, id: str = "", window: Any = "7d") -> Dict[str, Any]:
        """[pulse.concept] Traffic for ONE concept, rolled up through its sub-tree. Own hits plus
        the sum over every sub-concept (incoming sys:part_of / sys:is_a), with a per-child
        breakdown — e.g. the notion `bonheur` on its own, and the whole `ethics` field beneath it.
        The roll-up is free because hits attach to real concepts. Admin-only."""
        key = self._resolve(id)
        if not key:
            raise ValueError("pulse.concept: no such concept.")
        # Per-concept counts come from set cardinality (O(1) per node), filtered to the window
        # via a scan tally so `window` is honoured.
        scan = self._scan_events(window)
        per: Dict[str, int] = {}
        for r in scan["rows"]:
            if r["concept"]:
                per[r["concept"]] = per.get(r["concept"], 0) + 1
        for k, n in self._summaries(window)["concept"].items():
            per[k] = per.get(k, 0) + n
        subtree = self._descendants(key)
        own = per.get(key, 0)
        rolled = sum(per.get(k, 0) for k in subtree)
        children = []
        for k in subtree:
            if k == key:
                continue
            h = per.get(k, 0)
            if h:
                a = self._alias(k)
                children.append({"id": a, "name": self._label(a), "hits": h})
        children.sort(key=lambda e: (-e["hits"], e["id"]))
        return {"type": "pulse:concept", "window": str(window),
                "id": self._alias(key), "name": self._label(self._alias(key)),
                "own_hits": own, "rolled_up_hits": rolled,
                "subtree_size": len(subtree), "children": children[:50],
                "truncated": scan["truncated"]}

    def op_acquisition(self, window: Any = "7d") -> Dict[str, Any]:
        """[pulse.acquisition] How visitors arrive — a breakdown by referrer class over the
        window (google / github / direct / <host>). Admin-only."""
        scan = self._scan_events(window)
        sm = self._summaries(window)
        merged: Dict[str, int] = {s: n for s, n in self._tally(scan["rows"], "ref")}
        for s, n in sm["src"].items():
            merged[s] = merged.get(s, 0) + n
        grand = sum(merged.values()) or 1
        rows = [{"source": s, "hits": n, "pct": round(100.0 * n / grand, 1)}
                for s, n in sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))]
        return {"type": "pulse:acquisition", "window": str(window),
                "total": grand if merged else 0, "sources": rows, "truncated": scan["truncated"]}

    def op_path(self, window: Any = "7d", limit: Any = 15) -> Dict[str, Any]:
        """[pulse.path] The most-walked semantic clickpaths — visit sessions reconstructed from
        their events (ordered by time), rendered as concept sequences, with the most frequent
        two-step transitions. A route through MEANING, not a URL funnel. Admin-only."""
        lim = self._intf(limit, 15, 1, 100)
        scan = self._scan_events(window)
        visits: Dict[str, List[Dict[str, Any]]] = {}
        for r in scan["rows"]:
            if r["visit"]:
                visits.setdefault(r["visit"], []).append(r)
        seqs: Dict[str, int] = {}
        edges: Dict[str, int] = {}
        for evs in visits.values():
            evs.sort(key=lambda r: r["ts"])
            names = [self._label(r["alias"]) for r in evs if r["alias"]]
            # collapse immediate repeats (a refresh is not a step)
            path = [n for i, n in enumerate(names) if i == 0 or n != names[i - 1]]
            if len(path) >= 2:
                seqs[" → ".join(path)] = seqs.get(" → ".join(path), 0) + 1
                for a, b in zip(path, path[1:]):
                    edges[f"{a} → {b}"] = edges.get(f"{a} → {b}", 0) + 1
        top_paths = [{"path": p, "visits": n}
                     for p, n in sorted(seqs.items(), key=lambda kv: (-kv[1], kv[0]))[:lim]]
        top_edges = [{"edge": e, "count": n}
                     for e, n in sorted(edges.items(), key=lambda kv: (-kv[1], kv[0]))[:lim]]
        return {"type": "pulse:path", "window": str(window),
                "visits_with_path": len(top_paths and visits or {}),
                "paths": top_paths, "transitions": top_edges, "truncated": scan["truncated"]}

    def op_recent(self, limit: Any = 25, window: Any = "7d") -> Dict[str, Any]:
        """[pulse.recent] The most recent access events, newest first — for inspection. Admin-only."""
        lim = self._intf(limit, 25, 1, 200)
        scan = self._scan_events(window)
        rows = sorted(scan["rows"], key=lambda r: r["ts"], reverse=True)[:lim]
        out = [{"when": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(r["ts"])) if r["ts"] else "",
                "concept": self._label(r["alias"]) or r["concept"], "id": r["alias"],
                "surface": r["surface"] or "page", "ref": r["ref"]} for r in rows]
        return {"type": "pulse:recent", "count": len(out), "results": out}

    def op_gap(self, window: Any = "30d", limit: Any = 20) -> Dict[str, Any]:
        """[pulse.gap] The enrich-next queue: concepts that are HIGH-TRAFFIC but THIN — real
        demand meeting a sparse graph. Thinness is the concept's out-degree (how many links it
        has); a high-hits / low-degree concept is where reader interest outruns the ontology.
        Feeds the self-expanding-ontology loop with a demand signal. Admin-only."""
        lim = self._intf(limit, 20, 1, 100)
        top = self.op_top(window=window, limit=200)["results"]
        scored = []
        for e in top:
            key = e["key"]
            try:
                degree = len(self.cortex.get_adjacent_links(key) or [])
            except Exception:
                degree = 0
            # demand per unit of existing structure — high when hits are large and degree small
            need = round(e["hits"] / (1.0 + degree), 3)
            scored.append({"id": e["alias"], "name": e["name"], "hits": e["hits"],
                           "degree": degree, "need": need})
        scored.sort(key=lambda x: (-x["need"], -x["hits"], x["id"]))
        return {"type": "pulse:gap", "window": str(window),
                "results": scored[:lim], "count": min(lim, len(scored)),
                "note": "need = hits / (1 + out-degree); high = interest outruns the graph"}

    def op_narrate(self, window: Any = "7d") -> Dict[str, Any]:
        """[pulse.narrate] A plain-language summary of the window's attention — deterministic
        (no LLM required): what drew the most interest, where visitors came from, and what to
        enrich next. Admin-only."""
        ov = self.op_overview(window)
        top = self.op_top(window=window, limit=5)["results"]
        acq = self.op_acquisition(window)["sources"][:3]
        gap = self.op_gap(window=window, limit=3)["results"]
        parts = [f"Over {window}, the archives drew {ov['hits']} hits "
                 f"({ov['human_hits']} human) across {ov['unique_concepts']} concepts "
                 f"in {ov['unique_visits']} visits."]
        if top:
            lead = ", ".join(f"{t['name']} ({t['hits']})" for t in top[:3])
            parts.append(f"Attention gathered around {lead}.")
        if acq:
            arr = ", ".join(f"{a['source']} {a['pct']}%" for a in acq)
            parts.append(f"Visitors arrived via {arr}.")
        if gap:
            enr = ", ".join(g["name"] for g in gap)
            parts.append(f"Interest is outrunning the graph on {enr} — enrich these next.")
        return {"type": "pulse:narrate", "window": str(window), "narrative": " ".join(parts),
                "overview": ov, "top": top, "acquisition": acq, "enrich_next": gap}

    # ── COMPACTION (write; nightly LOW job) ───────────────────────────────────────
    def op_compact(self, keep: Any = 2) -> Dict[str, Any]:
        """[pulse.compact] Roll every raw day OLDER than `keep` days into one immutable per-day
        summary atom (concept / referrer / surface counts + human/visit totals), then soft-evict
        that day's raw events and index sets. Daily granularity is kept forever; raw-event growth
        is bounded to the `keep`-day window. Idempotent: an already-summarised day is skipped.
        Runs as a nightly LOW job (or on demand). Admin/write-gated."""
        keep = self._intf(keep, 2, 0, 60)
        core = self._wcore()
        author = getattr(self.session, "client_id", "system")
        now = self._now()
        compacted, evicted = [], 0
        # Scan a generous back-window (older than keep, up to ~1 year) for un-summarised days.
        for i in range(keep + 1, 400):
            day = self._day_str(now - i * _SECS_PER_DAY)
            raw = self._members(S_DAY + day)
            if not raw:
                continue
            if self._members(S_SUMDAY + day):   # already summarised → idempotent skip
                continue
            concepts: Dict[str, int] = {}
            aliases: Dict[str, str] = {}
            srcs: Dict[str, int] = {}
            surfaces: Dict[str, int] = {}
            visits = set()
            hits = human = 0
            for ek in raw:
                m = self._meta(ek)
                if m.get("provenance") != PROVENANCE:
                    continue
                ck = m.get("concept_key") or ""
                if ck:
                    concepts[ck] = concepts.get(ck, 0) + 1
                    aliases.setdefault(ck, m.get("concept_alias") or ck)
                r = m.get("ref") or "direct"; srcs[r] = srcs.get(r, 0) + 1
                s = m.get("surface") or ""; surfaces[s] = surfaces.get(s, 0) + 1
                if m.get("visit"):
                    visits.add(m.get("visit"))
                hits += 1
                if m.get("ua") != "bot":
                    human += 1
            summary = {
                "role": "pulse:summary", "provenance": PROVENANCE, "type": "pulse:summary",
                "day": day, "hits": hits, "human": human, "visits": len(visits),
                "concepts": concepts, "aliases": aliases, "srcs": srcs, "surfaces": surfaces,
            }
            content = f"[pulse:summary] {day} hits={hits} concepts={len(concepts)}"
            sk = self._put_event(core, content, summary, author)
            for s in (S_SUMSET, S_SUMDAY + day):
                try:
                    core.add_to_collection(s, sk)
                except Exception:
                    pass
            # Soft-evict the raw layer: clear the day-set + drop the raw event atoms.
            for ek in raw:
                try:
                    core.remove_from_collection(S_DAY + day, ek)
                    core.drop_chunk(ek)
                    evicted += 1
                except Exception:
                    pass
            compacted.append({"day": day, "hits": hits, "concepts": len(concepts)})
        return {"type": "pulse:compact", "keep_days": keep,
                "days_compacted": len(compacted), "events_evicted": evicted,
                "summaries": compacted}
