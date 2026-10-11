"""
Semantic Macro-Cache — the third residency tier: residency by MEMBERSHIP (concept model `cache`).

F33 gives two residency tiers: the set-algebra INDEX is always RAM (the paid-for invariant); atom
VALUES are disk-by-default. This is the third: a curated SET declares which atom bodies + rendered
pages deserve RAM regardless of the disk default. The pinning judgment moves from route-granularity
(F32) to SET-granularity — Akasha's own idiom: the concept group is enclosed in a set at write time,
and residency is one more property the membrane confers. It is NOT the caching F33 banned (an opaque
byte-LRU that put set-algebra STRUCTURE on disk): here structure stays in RAM untouched, and the
policy is a first-class SET — inspectable with `s.ls`, editable with `set.add`, reported in Health.
Eviction by MEANING (membership), declared as data, bounded by contract (design doc §10).

The contract (design §2):
  • `set:stage:featured` — the human-curated SEED (the demo vocabulary, cosmos hubs, station anchors).
    Its presence is the OPT-IN: a general-purpose cell has no featured set, so the mechanism is OFF
    (§6). Ordinary set semantics; nothing special stored in the members.
  • `set:stage:cache_plan` — the DERIVED plan (this planner's output): the seed plus a budgeted,
    scored depth-1 expansion. Inspectable data — `s.ls set:stage:cache_plan` answers "what is hot and
    why is it this size".
  • budget — one number, `AKASHA_SEMCACHE_BUDGET_MB` (default 512 on the 8 GB box). Bounds the
    EXPANDED population, never the curated seed: if the seed alone exceeds budget, the planner says so
    LOUDLY rather than trimming silently.

Memory discipline: the planner is WRITER-SIDE, bounded, run nightly + on demand (`cache.replan`).
The depth-1 closure is capped per seed member (a mega-hub seed can't explode the candidate ring — R1).
The plan is applied as a DIFF (warm the added, release the removed) — never clear-all (R7). The plan
population is on the Health line (§3). Value pinning (Phase 2) and the render warm daemon (Phase 1,
portal-side) consume this plan set; this module only AUTHORS it.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts._universal import UniversalConcept

logger = logging.getLogger("Harmonia.Concept.Cache")

FEATURED = "set:stage:featured"      # curated seed (deployment-owned; presence = opt-in)
PLAN = "set:stage:cache_plan"        # derived plan (this planner's output)

_MB = 1024 * 1024
_DEFAULT_BUDGET_MB = 512
_PER_SEED_LINKS = 50                 # depth-1 cap per seed member — bounds the candidate ring (R1)
_MIN_RENDER_BYTES = 2048             # floor for a rendered page's projected cost

# ── Phase 1.5 — focal-membrane demand staging (design §11) ──────────────────────────────────
# On a HUMAN dive the portal calls cache.stage id=<focal>; a visitor is likely to keep moving
# through the semantically connected space around the focal point, so we pre-warm that neighbourhood.
# The staged unit is BOUNDED, never the raw set (a big membrane like a hub's would be O(set) per dive
# — R1): the focal's depth-1 render closure, optionally ∩ a named membrane's siblings, top-K by
# link_weight × salience, capped by a share of the one budget. cache.stage is a READ (it computes +
# returns slugs, writes nothing); the portal warms them into L1/snapshot, whose own TTL+LRU is the
# dynamic population's death (≈ a visitor session). Bot dives never call it (portal gates on class).
_STAGE_K = 30                        # top-K neighbours per dive (design §11.2 start K≈30)
_STAGE_BUDGET_FRAC = 0.25            # dynamic staging shares ONE budget: its byte share (design §11.1)

# Relation → residency weight (thesaurus relations favored over incidental/structural links, §3.3).
_REL_WEIGHT = {
    "thesaurus:related": 1.0, "sys:synonym": 1.0, "sys:antonym": 0.9, "sys:is_a": 0.8,
    "sys:part_of": 0.7, "sys:associated_with": 0.6, "calc:associated_with": 0.5,
    "sys:refers_to": 0.3,
}

# Health/telemetry counters — process-lifetime, set by the writer daemon that runs cache.replan; the
# Health heartbeat (same process) snapshots them. Warm/hit/miss are portal-side (see the warm daemon).
# `plan`/`bytes`/`plan_at` reflect the last SUCCESSFUL replan; `last_error`/`last_error_at` carry the
# most recent REFUSED replan (A4(d) — honesty: a silent crash must be readable via cache.plan/Health).
_SEMCACHE = {"plan": 0, "bytes": 0, "seed": 0, "expanded": 0, "budget_mb": 0,
             "over_budget": False, "plan_at": 0.0, "last_error": None, "last_error_at": 0.0}


def semcache_counters() -> dict:
    """Snapshot of the plan-authorship counters (for the Health heartbeat). Mirrors pulse's
    emit_counters(): a module-level dict read by the same-process heartbeat."""
    c = dict(_SEMCACHE)
    c["plan_age"] = round(time.time() - c["plan_at"], 0) if c["plan_at"] else None
    return c


def record_replan_error(msg: str) -> None:
    """Record a REFUSED replan so Health/`cache.plan` can surface it (A4(d)). Called by the boot-replan
    daemon when the internal `cache.replan` dispatch returns an error — the failure is no longer silent."""
    _SEMCACHE["last_error"] = str(msg)[:300]
    _SEMCACHE["last_error_at"] = time.time()


def env_budget_mb() -> int:
    """The configured budget (AKASHA_SEMCACHE_BUDGET_MB, default 512). Named `env_budget_mb` — NOT
    `budget_mb` — so an op with a `budget_mb=` parameter can call it without the parameter shadowing
    the function (the A4 boot-replan crash: `op_replan(budget_mb="")` then `budget_mb()` called "")."""
    try:
        return max(1, int(os.environ.get("AKASHA_SEMCACHE_BUDGET_MB", str(_DEFAULT_BUDGET_MB))
                          or _DEFAULT_BUDGET_MB))
    except (TypeError, ValueError):
        return _DEFAULT_BUDGET_MB


class CacheConcept(UniversalConcept):
    """`cache.*` — the semantic macro-cache planner (see module docstring + design doc)."""

    CONCEPT_PREFIX = "cache"
    CONCEPT_LABEL = "semantic macro-cache — residency by set membership (planner; admin/telemetry)"
    _TEL = "read"

    CONCEPT_METHODS = {
        "replan": {"op": "op_replan", "action": "record", "cli": "cache.replan", "args": [],
                   "desc": ("Recompute the semantic-cache plan from set:stage:featured (budgeted "
                            "depth-1 expansion) → set:stage:cache_plan (diff-applied): "
                            "cache.replan [budget_mb=] [window=30d]")},
        "plan":   {"op": "op_plan", "action": "read", "cli": "cache.plan", "args": [],
                   "desc": ("Inspect the current cache plan (atoms, est bytes, seed vs expanded; "
                            "slugs=1 for the warm target list): cache.plan [slugs=1]")},
        "stage":  {"op": "op_stage", "action": "read", "cli": "cache.stage", "args": [],
                   "desc": ("Phase 1.5 focal-membrane demand staging — compute the bounded warm set "
                            "for a dive (focal depth-1 closure ∩ membrane, top-K); returns slugs the "
                            "portal pre-warms. READ, writes nothing: cache.stage id=<atom> [set=] [k=30]")},
        "stat":   {"op": "op_stat", "action": _TEL, "cli": "cache.stat", "args": [],
                   "desc": "Plan-authorship counters (plan size, bytes, age): cache.stat"},
    }

    # ── store helpers (nucleus core when present; reads union it) ──────────────────
    def _lcore(self):
        nuc = self._nuc
        return nuc.core if nuc is not None else self.cortex.core

    def _raw(self, key: str):
        """The raw row {content, meta} for a key, tried in nucleus then local (or vice versa)."""
        for core in (self._lcore(), self.cortex.core):
            try:
                row = core.get_chunk_raw(key)
            except Exception:
                row = None
            if row is not None:
                return row
        return None

    def _rm_from_set(self, name: str, key: str) -> None:
        nuc = self._nuc
        core = nuc.core if nuc is not None else self.cortex.core
        try:
            core.remove_from_collection(name, key)
        except Exception:
            pass

    def _core_links(self, key: str, cap: int) -> List[dict]:
        """Depth-1 outgoing links WITH weight + relation (the composite drops weight, so go to the
        core), top-`cap` by weight — this bounds a mega-hub seed's fan-out (R1)."""
        try:
            return list(self._lcore().get_adjacent_links(key, order_by_weight=True, limit=cap) or [])
        except Exception:
            return []

    # ── cost / demand / weight ────────────────────────────────────────────────────
    def _cost(self, key: str) -> int:
        """Estimated residency cost of a plan member = value bytes + a projected page-render estimate
        (a rendered page is a few× the content). Bounded, one point-get."""
        row = self._raw(key)
        if row is None:
            return 0
        vb = len(row.get("content") or "") + len(row.get("meta") or "")
        return vb + max(_MIN_RENDER_BYTES, 2 * (len(row.get("content") or "")))

    def _salience(self, key: str) -> float:
        m = self._meta(key)
        try:
            return float(m.get("salience", 0.0)) or 0.1
        except (TypeError, ValueError):
            return 0.1

    @staticmethod
    def _link_weight(rel: str, w: Any) -> float:
        base = _REL_WEIGHT.get(rel, 0.2)
        try:
            return base * (0.5 + min(1.0, float(w)))
        except (TypeError, ValueError):
            return base

    def _window_days(self, window: Any) -> List[str]:
        n = 30
        w = str(window or "30d").strip().lower()
        if w.endswith("d") and w[:-1].isdigit():
            n = int(w[:-1])
        now = time.time()
        return [time.strftime("%Y-%m-%d", time.gmtime(now - i * 86400)) for i in range(max(1, n))]

    def _demand(self, window: Any) -> Dict[str, int]:
        """{concept_key: hits} over the window, from pulse's compacted daily summaries (the concepts
        real visitors actually hit). Best-effort — no pulse data ⇒ empty demand (every candidate then
        scores on link_weight × salience alone)."""
        days = set(self._window_days(window))
        out: Dict[str, int] = {}
        try:
            for sk in self._members("pulse:summaries"):
                m = self._meta(sk)
                if m.get("day") in days:
                    for ck, n in (m.get("concepts") or {}).items():
                        out[ck] = out.get(ck, 0) + int(n)
        except Exception:
            pass
        return out

    # ── the planner ───────────────────────────────────────────────────────────────
    def op_replan(self, budget: Any = "", budget_mb: Any = "", window: Any = "30d") -> Dict[str, Any]:
        """[cache.replan] Recompute the plan: seed = set:stage:featured; candidate ring = the seed's
        depth-1 render closure (capped per seed); score `w = link_weight × salience × demand`; greedy
        fill by `w/cost` until the budget; write set:stage:cache_plan as a DIFF (never clear-all).
        The seed is ALWAYS included; if the seed alone exceeds budget the planner says so loudly and
        does not expand. Writer-side, bounded. Nightly (boot daemon) + on demand. Budget: `budget=`
        (preferred) or the `budget_mb=` CLI alias; empty ⇒ AKASHA_SEMCACHE_BUDGET_MB (env_budget_mb())."""
        seed = list(self._members(FEATURED))
        if not seed:
            return {"active": False,
                    "reason": "no curated seed (set:stage:featured is empty) — semantic cache is OFF"}
        _b = budget if str(budget).strip() != "" else budget_mb    # accept either spelling
        bmb = env_budget_mb() if str(_b).strip() == "" else max(1, int(_b))
        budget_bytes = bmb * _MB

        # seed always included; its cost is paid first.
        plan_cost: Dict[str, int] = {}
        seed_bytes = 0
        for k in seed:
            c = self._cost(k)
            plan_cost[k] = c
            seed_bytes += c
        over = seed_bytes > budget_bytes
        if over:
            logger.warning("[semcache.replan] the CURATED SEED alone (%d atoms, ≈%d bytes) exceeds "
                           "the budget (%d MB); including the seed, NO expansion — raise "
                           "AKASHA_SEMCACHE_BUDGET_MB or trim set:stage:featured",
                           len(seed), seed_bytes, bmb)

        # candidate ring: depth-1 closure of the seed, scored.
        demand = self._demand(window)
        seed_set = set(seed)
        candidates: Dict[str, tuple] = {}      # dst -> (score, cost)
        if not over:
            for k in seed:
                for link in self._core_links(k, _PER_SEED_LINKS):
                    dst = link.get("dst")
                    if not dst or dst in seed_set:
                        continue
                    score = (self._link_weight(link.get("rel", ""), link.get("w", 1.0))
                             * self._salience(dst) * (1.0 + float(demand.get(dst, 0))))
                    cur = candidates.get(dst)
                    if cur is None:
                        candidates[dst] = (score, self._cost(dst))
                    elif score > cur[0]:
                        candidates[dst] = (score, cur[1])

        # greedy fill by value density (w/cost) until the budget; skip (don't stop) so smaller
        # high-value candidates still pack in after a large one is passed.
        ranked = sorted(candidates.items(), key=lambda kv: kv[1][0] / max(1, kv[1][1]), reverse=True)
        used = seed_bytes
        expanded: List[str] = []
        for dst, (score, cost) in ranked:
            if used + cost > budget_bytes:
                continue
            plan_cost[dst] = cost
            used += cost
            expanded.append(dst)

        # diff-apply to set:stage:cache_plan (R7 — warm the added, release the removed, never clear-all).
        new_plan = set(plan_cost)
        old_plan = set(self._members(PLAN))
        added = new_plan - old_plan
        removed = old_plan - new_plan
        for k in added:
            self._add_to_set(PLAN, k)
        for k in removed:
            self._rm_from_set(PLAN, k)

        _SEMCACHE.update({"plan": len(new_plan), "bytes": used, "seed": len(seed),
                          "expanded": len(expanded), "budget_mb": bmb, "over_budget": over,
                          "plan_at": time.time(), "last_error": None})
        logger.info("[semcache.replan] plan atoms=%d est_bytes=%d seed=%d expanded=%d "
                    "budget_used=%.1f%% added=%d removed=%d over_budget=%s",
                    len(new_plan), used, len(seed), len(expanded),
                    100.0 * used / max(1, budget_bytes), len(added), len(removed), over)
        return {"type": "cache:replan", "plan_set": PLAN, "atoms": len(new_plan),
                "seed": len(seed), "expanded": len(expanded), "est_bytes": used,
                "budget_mb": bmb, "budget_used_pct": round(100.0 * used / max(1, budget_bytes), 1),
                "over_budget": over, "added": len(added), "removed": len(removed)}

    def op_plan(self, slugs: Any = "") -> Dict[str, Any]:
        """[cache.plan] Inspect the current plan: its size, estimated bytes, seed vs expanded, and
        (for the portal warm daemon) the member SLUGS to pre-render. `s.ls set:stage:cache_plan`
        gives the raw membership; this adds the accounting + the warm target list."""
        members = list(self._members(PLAN))
        seed = set(self._members(FEATURED))
        want_slugs = str(slugs).strip().lower() in ("1", "yes", "true", "slugs")
        out = {"type": "cache:plan", "plan_set": PLAN, "atoms": len(members),
               "seed": len(seed & set(members)), "expanded": len(set(members) - seed),
               "est_bytes": _SEMCACHE.get("bytes"), "budget_mb": _SEMCACHE.get("budget_mb"),
               "over_budget": _SEMCACHE.get("over_budget"),
               "plan_age": semcache_counters().get("plan_age"),
               "last_error": _SEMCACHE.get("last_error")}
        if want_slugs:
            out["slugs"] = [self._alias(k) for k in members]
        return out

    def op_stage(self, id: Any = "", set: Any = "", k: Any = "") -> Dict[str, Any]:
        """[cache.stage] Phase 1.5 — compute the bounded demand-staging membrane for a dive to `id`:
        the focal's depth-1 render closure (capped per R1), scored by link_weight × salience, with a
        named membrane's siblings (`set=`) preferred, top-K, bounded by a share of the budget. Returns
        the member SLUGS for the portal to pre-warm — this op WRITES NOTHING (the dynamic population is
        the portal's short-TTL warm cache, not a nucleus set). Guest-safe read; the portal calls it on
        HUMAN dives only and warms at LOW priority, so a bot storm never spends staging budget."""
        key = self._key(str(id or "").strip())
        if not key:
            return {"active": False, "reason": "cache.stage requires a known id=<focal atom>"}
        try:
            kk = _STAGE_K if str(k).strip() == "" else max(1, int(k))
        except (TypeError, ValueError):
            kk = _STAGE_K

        # candidate ring: the focal's depth-1 closure, scored — bounded per R1 (never O(hub-degree)).
        scored: Dict[str, float] = {}
        for link in self._core_links(key, _PER_SEED_LINKS):
            dst = link.get("dst")
            if not dst or dst == key:
                continue
            s = self._link_weight(link.get("rel", ""), link.get("w", 1.0)) * self._salience(dst)
            if s > scored.get(dst, 0.0):
                scored[dst] = s

        # membrane ∩ : when a set is named, its siblings rank FIRST (the focal's own membrane is the
        # locality the visitor is likely to traverse), then fill with the rest of the closure to K.
        # NB: the `set` PARAM shadows the builtin — use a comprehension, never set(), below.
        membrane = str(set or "").strip()
        siblings = {m for m in self._members(membrane)} if membrane else frozenset()
        ranked = sorted(scored.items(),
                        key=lambda kv: (kv[0] in siblings, kv[1]), reverse=True)

        # bounded by K AND a share of the one budget (design §11.1 — two populations, one budget).
        stage_budget = int(env_budget_mb() * _MB * _STAGE_BUDGET_FRAC)
        used, staged, trimmed = 0, [], 0
        for dst, _s in ranked:
            if len(staged) >= kk:
                trimmed += 1
                continue
            cost = self._cost(dst)
            if used + cost > stage_budget:
                trimmed += 1
                continue
            used += cost
            staged.append(dst)
        return {"type": "cache:stage", "focal": self._alias(key), "membrane": membrane or None,
                "k": kk, "staged": len(staged), "trimmed": trimmed, "est_bytes": used,
                "slugs": [self._alias(d) for d in staged]}

    def op_stat(self) -> Dict[str, Any]:
        """[cache.stat] The plan-authorship counters that ride the Health `semcache(...)` segment."""
        return {"type": "cache:stat", **semcache_counters(), "budget_mb_config": env_budget_mb(),
                "active": bool(self._members(FEATURED))}
