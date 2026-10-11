"""
P0-a slice 2 — hyperparameter SWEEPS on a bench (§2.3/§2.4, the sweep engine's operator layer).

A sweep is a fan of workflow BRANCHES, each a parameterized instance of ONE template (P0-a slice 1
`wf.branch from=<template> params=`), each producing an evaluation ROW; the leaderboard ranks them.
This concept is the operator layer over that:

  • `sweep.def bench= name= grid= [max=18] [template=] [fixed=]` — expand the grid into condition
    tuples (cartesian product, bounded by `max`) and record them; 0 branches yet.
  • `sweep.materialise bench= name= [n=1]` — turn up to `n` un-materialised conditions into branches
    (`wf.branch from=<template> params=<cond>`); each branch marker is stamped with the sweep name so
    `learning.evaluate` files its evaluation under the sweep. Never runs a branch (the driver / a manual
    `society.run` does — P0-b hands the picking to the driver).
  • `sweep.status bench= name=` — the fan: conds, branches, pending / done / failed (guest-readable).
  • `sweep.leaderboard bench= name= [key=accuracy] [select_by=dev] [report=test]` — rank the sweep's
    evaluations through `lens.rank` and store the ranking as an epoch-keyed artifact.

CSL has no loops, so the grid expansion and the per-condition branch loop live HERE (a concept), not
in a `.csl` macro; the thin `config/macros/sweep.*.csl` + `leaderboard.csl` forward to these ops so
`macro.ls` / `macro.run` list and drive them (the acceptance surface). Every op is equally
CLI-invokable (the CLI-first convention). Subclasses WorkflowConcept for `op_branch` + the
participant grant + the bench-scoped storage helpers.

Sets (under the bench; universal/nucleus for a public bench, the group engine for a closed one):
  set:wb:<b>:sweep:<name>:conds        — the condition atoms (one per grid point)
  set:wb:<b>:sweep:<name>:branches     — the materialised branch markers (wf:sweep:<b>:<branch>)
  set:wb:<b>:sweep:<name>:evaluations  — the evaluations of this sweep's branches (learning.evaluate joins)
A condition atom `wb:<b>:sweep:<name>:cond:<grid8>` carries {bindings, grid8, branch, cond8, status}.
"""
import hashlib
import itertools
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.concepts._universal import slug as _uslug
from lib.akasha.concepts.workflow import WorkflowConcept
from lib.akasha.artifact_epoch import artifact_id as _artifact_id

logger = logging.getLogger("Harmonia.Concept.Sweep")


class SweepConcept(WorkflowConcept):
    """`sweep.*` — hyperparameter sweeps on a bench (define a grid → materialise branches → rank).
    Not a bench kind (no KIND); registers on its own `sweep.*` prefix."""

    CONCEPT_PREFIX = "sweep"
    CONCEPT_LABEL = "Sweep — a fan of parameterized workflow branches over a hyperparameter grid"

    CONCEPT_METHODS: Dict[str, Any] = {
        "def": {"op": "op_def", "action": "record",
                "args": ["bench", "name", "grid", "max", "template", "fixed", "budget"],
                "desc": "Define a sweep — expand a grid into conditions (cartesian, bounded by max): "
                        "sweep.def bench= name= grid=head=logreg,linear;split=0.8,0.7 [max=18] "
                        "[template=learn_observe] [fixed=space=mobilenet] "
                        "[budget=per_day=1;total=12;drift_per_day=0]"},
        "materialise": {"op": "op_materialise", "action": "record",
                        "args": ["bench", "name", "n"],
                        "desc": "Turn up to n un-materialised conditions into branches (wf.branch "
                                "from=<template>): sweep.materialise bench= name= [n=1]"},
        "status": {"op": "op_status", "action": "read",
                   "args": ["bench", "name"],
                   "desc": "The sweep fan — conds / branches / pending / done / failed (guest): "
                           "sweep.status bench= name="},
        "leaderboard": {"op": "op_leaderboard", "action": "record",
                        "args": ["bench", "name", "key", "select_by", "report"],
                        "desc": "Rank the sweep's evaluations (lens.rank) and store the ranking as an "
                                "epoch-keyed artifact: sweep.leaderboard bench= name= [key=accuracy] "
                                "[select_by=dev] [report=test]"},
        "mark": {"op": "op_mark", "action": "record",
                 "args": ["bench", "branch", "status"],
                 "desc": "Stamp a sweep condition's status from its branch run (pending→done|failed) — "
                         "the driver calls this at its block-status site: sweep.mark bench= branch= status="},
        "release": {"op": "op_release", "action": "record",
                    "args": ["bench", "name", "branch"],
                    "desc": "Release a QUARANTINED branch — stamp released_at on its condition so the "
                            "step_failed deviations before now stop counting and the driver may retry it: "
                            "sweep.release bench= name= branch=<lineage|slug>"},
    }

    # `_refuse` is GONE with the participant gate it reported (ruling §5). A sweep op that is not
    # allowed is refused at the dispatcher, by `gate`, with the ruling's reason and the ONE
    # `[gate] refused …` line — not here, in a second vocabulary, under a second rule.

    # ── aliases / sets ───────────────────────────────────────────────────────────
    def _sweep_head(self, name: str, sweep: str) -> str:
        return "wb:%s:sweep:%s" % (_uslug(name), _uslug(sweep))

    def _conds_set(self, name: str, sweep: str) -> str:
        return "set:wb:%s:sweep:%s:conds" % (_uslug(name), _uslug(sweep))

    def _branches_set(self, name: str, sweep: str) -> str:
        return "set:wb:%s:sweep:%s:branches" % (_uslug(name), _uslug(sweep))

    def _sweep_evals_set(self, name: str, sweep: str) -> str:
        return "set:wb:%s:sweep:%s:evaluations" % (_uslug(name), _uslug(sweep))

    def _cond_alias(self, name: str, sweep: str, grid8: str) -> str:
        return "wb:%s:sweep:%s:cond:%s" % (_uslug(name), _uslug(sweep), grid8)

    # ── grid parsing / expansion ─────────────────────────────────────────────────
    @staticmethod
    def _parse_grid(grid: Any) -> "Dict[str, List[str]]":
        """`grid` → {axis: [values]}. Accepts a JSON object {axis: [..]} (how the config ships it) or a
        compact string `axis=v1,v2;axis2=v3,v4` (axes by ';', values by ','). Order is preserved."""
        if isinstance(grid, dict):
            return {str(k): [str(v) for v in (vs if isinstance(vs, list) else [vs])]
                    for k, vs in grid.items()}
        s = str(grid or "").strip()
        if not s:
            return {}
        if s.startswith("{"):
            try:
                return SweepConcept._parse_grid(json.loads(s))
            except Exception:
                pass
        out: Dict[str, List[str]] = {}
        for axis in s.split(";"):
            axis = axis.strip()
            if not axis or "=" not in axis:
                continue
            k, vs = axis.split("=", 1)
            vals = [v.strip() for v in vs.split(",") if v.strip()]
            if k.strip() and vals:
                out[k.strip()] = vals
        return out

    @staticmethod
    def _parse_fixed(fixed: Any) -> "Dict[str, str]":
        if isinstance(fixed, dict):
            return {str(k): str(v) for k, v in fixed.items()}
        s = str(fixed or "").strip()
        if not s:
            return {}
        if s.startswith("{"):
            try:
                return {str(k): str(v) for k, v in json.loads(s).items()}
            except Exception:
                pass
        out: Dict[str, str] = {}
        for tok in s.replace(";", ",").split(","):
            if "=" in tok:
                k, v = tok.split("=", 1)
                if k.strip():
                    out[k.strip()] = v.strip()
        return out

    @staticmethod
    def _grid8(bindings: Dict[str, str]) -> str:
        canon = ",".join("%s=%s" % (k, bindings[k]) for k in sorted(bindings))
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:8]

    @staticmethod
    def _parse_budget(budget: Any) -> "Dict[str, int]":
        """B1-c — the sweep's budget block {per_day, total, drift_per_day} → ints. Accepts a JSON object
        (how `config/<bench>/sweeps/<name>.json` ships it) or a compact `per_day=1;total=12` string. An
        empty budget means the driver never auto-picks this sweep (auto-driving is opt-in per sweep)."""
        if isinstance(budget, dict):
            src: Dict[str, Any] = dict(budget)
        else:
            s = str(budget or "").strip()
            if not s:
                return {}
            if s.startswith("{"):
                try:
                    src = json.loads(s)
                except Exception:
                    src = {}
            else:
                src = {}
                for tok in s.replace(";", ",").split(","):
                    if "=" in tok:
                        k, v = tok.split("=", 1)
                        if k.strip():
                            src[k.strip()] = v.strip()
        out: Dict[str, int] = {}
        for k in ("per_day", "total", "drift_per_day"):
            if k in src:
                try:
                    out[k] = int(src[k])
                except (TypeError, ValueError):
                    pass
        return out

    @staticmethod
    def _bench_day() -> str:
        """The bench day — the UTC date, matching the auto-run driver's daily-budget rollover key."""
        return time.strftime("%Y-%m-%d", time.gmtime())

    def _deviation_slug(self, bench: str) -> str:
        balias = self._bench_alias(bench)
        return _uslug(balias[3:] if balias.startswith("wb:") else balias)

    def _quarantine_count(self, bench: str, branch_slug: str, since: int,
                          kind_members: "Optional[set]" = None) -> int:
        """B1-c — how many `step_failed` deviations a branch has accrued SINCE the coordinate `since`
        (a condition's `released_at`; 0 = count all). ≥2 ⇒ the branch is QUARANTINED and the driver skips
        it (a branch that failed twice is not retried until a `sweep.release` advances `since` past its
        failures). O(branch deviations) — the intersection of the step_failed kind Set (read ONCE by the
        caller and passed in) with the per-branch Set, both bounded populations."""
        if not branch_slug:
            return 0
        slug_b = self._deviation_slug(bench)
        if kind_members is None:
            kind_members = set(self._members("set:wb:%s:deviation:kind:step_failed" % slug_b))
        n = 0
        for dk in self._members("set:wb:%s:deviation:branch:%s" % (slug_b, branch_slug)):
            if dk not in kind_members:
                continue
            dm = self._meta(self._alias(dk) or dk) or {}
            if since and int(dm.get("at_seq", 0) or 0) <= int(since):
                continue
            n += 1
        return n

    def _expand(self, grid: Dict[str, List[str]], fixed: Dict[str, str],
                cap: int) -> "Tuple[List[Dict[str, str]], int, bool]":
        """The cartesian product of the grid axes → a list of condition bindings (each ⊕ fixed),
        BOUNDED by `cap` (R3 — a sweep is a population with a budget). Returns (conds, full_count,
        capped)."""
        axes = list(grid.keys())
        if not axes:
            return [], 0, False
        value_lists = [grid[a] for a in axes]
        full = 1
        for vs in value_lists:
            full *= max(1, len(vs))
        conds: List[Dict[str, str]] = []
        for combo in itertools.product(*value_lists):
            b = dict(fixed)
            for a, v in zip(axes, combo):
                b[a] = v
            conds.append(b)
            if len(conds) >= cap:
                break
        return conds, full, full > cap

    # ── sweep.def ────────────────────────────────────────────────────────────────
    def op_def(self, bench: str = "", name: str = "", grid: Any = "", max: Any = 18,
               template: str = "learn_observe", fixed: Any = "", budget: Any = "") -> Dict[str, Any]:
        """[sweep.def] Expand a grid into condition tuples (cartesian, bounded by `max`) and record
        them under the sweep. Idempotent + additive: a re-def with the same grid changes nothing; a
        grid EXTENSION adds only the new conditions. `budget` (per_day / total / drift_per_day) gates the
        auto-run driver's branch picking (B1-c) — Set-free counters (spent_today / spent_total / day) on
        this sweep_def atom, carried across a re-def (a budget edit never resets the spend)."""
        gid = self._bench_gid(bench); self._bind(gid)
        if not name:
            raise ValueError("sweep.def requires name=")
        if not self._key(self._bench_alias(bench)):
            raise ValueError("unknown bench '%s' — bench.new it first" % bench)
        try:
            cap = max if isinstance(max, int) else int(str(max).strip() or 18)
        except (TypeError, ValueError):
            cap = 18
        if cap <= 0:
            cap = 18
        g = self._parse_grid(grid)
        fx = self._parse_fixed(fixed)
        # S2-h — validate a `head` axis (or fixed head) against the real learner KINDS at DEFINITION
        # time, so a sweep can never materialise conditions that would silently train a centroid mock.
        import lib.akasha.concepts.learned_head as _lh
        _heads = list(g.get("head") or []) + ([fx["head"]] if fx.get("head") else [])
        _bad = [h for h in _heads if h not in _lh.KINDS]
        if _bad:
            logger.info("[sweep] def bench=%s name=%s refused head=%s (kinds: %s)",
                        self._bench_alias(bench), name, ",".join(_bad), ",".join(_lh.KINDS))
            return {"status": "refused", "bench": self._bench_alias(bench), "sweep": name,
                    "reason": "unknown head=%s — learner kinds are %s" % (",".join(_bad), ", ".join(_lh.KINDS))}
        conds, full, capped = self._expand(g, fx, cap)
        head = self._sweep_head(bench, name)
        _added = 0
        for b in conds:
            grid8 = self._grid8(b)
            calias = self._cond_alias(bench, name, grid8)
            if not self._key(calias):
                _added += 1
            k = self._mk(calias, "[%s] %s" % (calias, ",".join("%s=%s" % (x, b[x]) for x in sorted(b))),
                         {"concept": "sweep_cond", "bench": self._bench_alias(bench), "sweep": name,
                          "bindings": b, "grid8": grid8, "template": template, "status": "unmaterialised",
                          "branch": None, "cond8": None, "author": self._client()})
            self._add_to_set(self._conds_set(bench, name), k)
        # S2-h2 — a stale condition from an older grid (e.g. the ridge/linear points left when the grid
        # was narrowed to logreg,mlp) whose head is not a real learner KIND is dropped from the grid.
        # S2-m2 — but ONLY a BRANCHLESS (unmaterialised) one is stamped `retired` (materialise skips it,
        # status counts it), so `materialise n=1` can never pick it and fail at learning.train. A condition
        # that already MATERIALISED — it has a branch, an evaluation, maybe the leaderboard's only row —
        # keeps its real status (done/failed/pending) and is only FLAGGED `retired_grid=true` (visible,
        # not counted as retired), so the fan does not claim nothing ran while the board ranks that run.
        _retired = 0
        for ck in self._members(self._conds_set(bench, name)):
            cm = self._meta(self._alias(ck) or ck) or {}
            _h = (cm.get("bindings") or {}).get("head")
            if _h is None or _h in _lh.KINDS:
                continue
            _ck = self._key(self._alias(ck) or ck)
            if cm.get("branch"):
                if not cm.get("retired_grid"):
                    self._set_meta(_ck, "retired_grid", True)   # dropped from the grid, but it ran
                # S2-m3 — an earlier build wrongly stamped `retired` on this EXECUTED condition; clear it
                # to `pending` so status re-derives its real done/failed/pending (it never was retired).
                if cm.get("status") == "retired":
                    self._set_meta(_ck, "status", "pending")
            elif cm.get("status") != "retired":
                self._set_meta(_ck, "status", "retired")
                _retired += 1
        # B1-c — the budget block, and the live spend counters carried forward from the current head
        # atom so a re-def (idempotent, or a budget edit) never resets what the driver has already spent.
        bud = self._parse_budget(budget)
        _hm_prev = self._meta(head) or {}
        _spent_today = int(_hm_prev.get("spent_today", 0) or 0)
        _spent_total = int(_hm_prev.get("spent_total", 0) or 0)
        _day = _hm_prev.get("day") or ""
        # the sweep-def atom (grid + template + max + budget), replace-on-change so a grid/budget edit is
        # legible. The spend counters are NOT compared (they move on every driver pick, not a definition).
        hk, _chg, _old = self._mk_replace(
            head, "[%s] grid over %s (%d conds, max %d)" % (head, ",".join(g.keys()) or "-", len(conds), cap),
            {"concept": "sweep_def", "bench": self._bench_alias(bench), "sweep": name, "grid": g,
             "fixed": fx, "template": template, "max": cap, "conds": len(conds), "full": full,
             "capped": capped, "budget": bud, "spent_today": _spent_today, "spent_total": _spent_total,
             "day": _day, "author": self._client()},
            compare_meta=("grid", "fixed", "template", "max", "budget"))
        # S2-l — index the sweep-def atom in a bench-global Set so the leaderboard hydrate (boot verify)
        # can enumerate every (bench, sweep) and rebuild each board from its evaluations — no operator
        # command, no per-bench hand-list.
        self._add_to_set("set:wb:sweeps:all", hk)
        n_conds = len(self._members(self._conds_set(bench, name)))
        logger.info("[sweep] def bench=%s name=%s conds=%d max=%d%s%s%s", self._bench_alias(bench), name,
                    n_conds, cap, " (new)" if _added else "", (" retired=%d" % _retired) if _retired else "",
                    " CAPPED full=%d" % full if capped else "")
        return {"status": "defined", "bench": self._bench_alias(bench), "sweep": name,
                "template": template, "conds": n_conds, "added": _added, "retired": _retired,
                "max": cap, "full": full, "capped": capped, "grid": g, "fixed": fx, "budget": bud}

    # ── sweep.materialise ────────────────────────────────────────────────────────
    def op_materialise(self, bench: str = "", name: str = "", n: Any = 1) -> Dict[str, Any]:
        """[sweep.materialise] Turn up to `n` un-materialised conditions into workflow branches via
        `wf.branch from=<template> params=<cond>`. Each branch marker is stamped with the sweep name so
        learning.evaluate files its evaluation under this sweep. Idempotent (a cond already materialised is
        skipped; wf.branch itself is idempotent by cond8)."""
        gid = self._bench_gid(bench); self._bind(gid)
        if not name:
            raise ValueError("sweep.materialise requires name=")
        try:
            want = max(1, int(str(n).strip() or 1))
        except (TypeError, ValueError):
            want = 1
        # pending = conds without a branch yet, in a stable order (by grid8).
        # S2-h2 — a RETIRED condition (a stale invalid-head cond from an older grid) is never
        # materialised: it would fail at learning.train (its head is not a real learner KIND).
        pending = []
        for ck in self._members(self._conds_set(bench, name)):
            cm = self._meta(self._alias(ck) or ck) or {}
            if not cm.get("branch") and cm.get("status") != "retired":
                pending.append((self._alias(ck) or ck, cm))
        pending.sort(key=lambda cm: cm[1].get("grid8") or "")
        made = []
        for calias, cm in pending:
            if len(made) >= want:
                break
            b = cm.get("bindings") or {}
            template = cm.get("template") or "learn_observe"
            params = ",".join("%s=%s" % (k, b[k]) for k in sorted(b))
            # `_sweep_bound` — these params ARE the condition's bindings (the sweep dimensions), not a
            # hand override, so op_branch must NOT mint a param_override deviation for them (B1 §A3).
            r = self.op_branch(bench=bench, **{"from": template, "params": params, "parent": "main",
                                               "_sweep_bound": True})
            if r.get("status") != "branched":
                logger.warning("[sweep] materialise bench=%s name=%s cond=%s branch refused: %s",
                               self._bench_alias(bench), name, cm.get("grid8"), r.get("reason"))
                continue
            branch, cond8 = r.get("branch"), r.get("cond8")
            # record the branch on the cond, mark it pending (materialised, not yet run)
            ck = self._key(calias)
            self._set_meta(ck, "branch", branch)
            self._set_meta(ck, "cond8", cond8)
            self._set_meta(ck, "status", "pending")
            # stamp the sweep name on the branch marker so learning.evaluate files under this sweep
            marker = self._sweep_marker(bench, branch)
            mk = self._key(marker)
            if mk:
                self._set_meta(mk, "sweep", name)
                self._add_to_set(self._branches_set(bench, name), mk)
            made.append({"cond": cm.get("grid8"), "branch": branch, "cond8": cond8,
                         "already": bool(r.get("already"))})
        logger.info("[sweep] materialise bench=%s name=%s branches=+%d pending_left=%d",
                    self._bench_alias(bench), name, len(made), len(pending) - len(made))
        return {"status": "materialised", "bench": self._bench_alias(bench), "sweep": name,
                "branches": len(made), "made": made, "pending_left": len(pending) - len(made)}

    # ── sweep.status ─────────────────────────────────────────────────────────────
    def op_status(self, bench: str = "", name: str = "") -> Dict[str, Any]:
        """[sweep.status] The sweep fan: conds, materialised branches, and pending / done / failed —
        `done` is DERIVED (the branch has an evaluation in the sweep evaluations Set); `failed` is a
        stamped status. Guest-readable pure Set read."""
        gid = self._bench_gid(bench); self._bind(gid)
        if not name:
            raise ValueError("sweep.status requires name=")
        head = self._meta(self._sweep_head(bench, name)) or {}
        # branches that already carry an evaluation (done), from the sweep evaluations Set's meta
        done_branches = set()
        for ek in self._members(self._sweep_evals_set(bench, name)):
            em = self._meta(self._alias(ek) or ek) or {}
            if em.get("branch"):
                done_branches.add(em.get("branch"))
        # B1-c — the step_failed deviation kind Set, read ONCE (bounded population), so quarantine is
        # derived per-condition without re-scanning it (R1 — pay the Set read once, not per cond).
        _kind_members = set(self._members(
            "set:wb:%s:deviation:kind:step_failed" % self._deviation_slug(bench)))
        conds = []
        n_pending = n_done = n_failed = n_unmat = n_retired = n_quar = 0
        for ck in self._members(self._conds_set(bench, name)):
            cm = self._meta(self._alias(ck) or ck) or {}
            branch = cm.get("branch")
            # S2-m3 — the BRANCH decides first: a branch-bearing condition RAN, so it is derived
            # done/failed/pending and NEVER reads `retired` (a stale stored `retired` written by an
            # earlier build is ignored here and cleared at the next re-apply, op_def). Only a BRANCHLESS
            # condition is `retired` (stale invalid-head grid drop) or `unmaterialised`.
            if not branch:
                if cm.get("status") == "retired":
                    st = "retired"; n_retired += 1
                else:
                    st = "unmaterialised"; n_unmat += 1
            elif cm.get("status") == "failed":
                st = "failed"; n_failed += 1
            elif branch in done_branches:
                st = "done"; n_done += 1
            else:
                st = "pending"; n_pending += 1
            # B1-c — quarantine is an OVERLAY over the five buckets (typically over failed): a branch with
            # ≥2 step_failed deviations SINCE its `released_at` coordinate is quarantined, and the driver
            # skips it. Counted separately (`quarantined`) so the five status buckets still sum to conds.
            _quar = (branch and self._quarantine_count(
                bench, _uslug(branch), int(cm.get("released_at", 0) or 0), _kind_members) >= 2)
            if _quar:
                n_quar += 1
            conds.append({"grid8": cm.get("grid8"), "bindings": cm.get("bindings") or {},
                          "branch": branch, "cond8": cm.get("cond8"), "status": st,
                          "quarantined": bool(_quar), "released_at": cm.get("released_at"),
                          # S2-m2 — a materialised condition dropped from the grid keeps its real status
                          # and carries this flag so the fan shows it ran yet is no longer in the grid.
                          "retired_grid": bool(cm.get("retired_grid"))})
        conds.sort(key=lambda c: c.get("grid8") or "")
        return {"bench": self._bench_alias(bench), "sweep": name, "template": head.get("template"),
                "grid": head.get("grid") or {}, "max": head.get("max"), "capped": head.get("capped", False),
                "budget": head.get("budget") or {}, "spent_today": int(head.get("spent_today", 0) or 0),
                "spent_total": int(head.get("spent_total", 0) or 0), "day": head.get("day") or "",
                "conds": len(conds), "branches": n_pending + n_done + n_failed,
                "pending": n_pending, "done": n_done, "failed": n_failed, "unmaterialised": n_unmat,
                "retired": n_retired, "quarantined": n_quar, "conditions": conds}

    # ── sweep.mark (internal — the pending→done|failed status move) ───────────────
    def op_mark(self, bench: str = "", branch: str = "", status: str = "",
                by: str = "") -> Dict[str, Any]:
        """[sweep.mark] (internal) Stamp a sweep condition's status when its branch's run finishes —
        the pending→done|failed move the driver / a manual society.run makes. `done` is normally
        DERIVED by sweep.status from the evaluation; this op records `failed` (or forces `done`) for a
        branch. No-op for a branch not owned by any sweep condition.

        `by=` is WHOSE run this bookkeeping belongs to. The write itself is the RECORDER's — a
        workload's own client has no scope over the bench it airs on, and dispatching this as that
        client put a `[gate] refused … out_of_scope` line after every run of every programme (D2).
        Provenance is a field on the record; it is never a reason to borrow an authority."""
        gid = self._bench_gid(bench); self._bind(gid)
        if not branch or status not in ("done", "failed", "pending"):
            return {"status": "noop"}
        marker = self._meta(self._sweep_marker(bench, branch)) or {}
        sweep = marker.get("sweep")
        if not sweep:
            return {"status": "noop", "reason": "branch not owned by a sweep"}
        for ck in self._members(self._conds_set(bench, sweep)):
            cm = self._meta(self._alias(ck) or ck) or {}
            if cm.get("branch") == branch:
                _k = self._key(self._alias(ck) or ck)
                self._set_meta(_k, "status", status)
                if str(by or "").strip():
                    self._set_meta(_k, "status_by", str(by).strip())
                return {"status": "marked", "sweep": sweep, "branch": branch,
                        "cond_status": status, "by": str(by or "") or None}
        return {"status": "noop", "reason": "no condition for branch"}

    # ── sweep.release (lift a branch's quarantine) ────────────────────────────────
    def op_release(self, bench: str = "", name: str = "", branch: str = "") -> Dict[str, Any]:
        """[sweep.release] Lift a QUARANTINED branch's quarantine — stamp `released_at=<coordinate>` on
        its condition so the step_failed deviations before now stop counting (sweep.status re-derives it
        below the ≥2 threshold, the driver may pick it again). `branch` is the lineage or the slug (both
        uslug to the branch slug). Participant write; a no-op for a branch not owned by a condition."""
        gid = self._bench_gid(bench); self._bind(gid)
        if not name or not branch:
            raise ValueError("sweep.release requires name= and branch=")
        bslug = _uslug(branch)
        at = self._akasha_now()
        for ck in self._members(self._conds_set(bench, name)):
            cm = self._meta(self._alias(ck) or ck) or {}
            if cm.get("branch") and _uslug(cm.get("branch")) == bslug:
                self._set_meta(self._key(self._alias(ck) or ck), "released_at", at)
                logger.info("[sweep] release bench=%s name=%s branch=%s released_at=%s",
                            self._bench_alias(bench), name, cm.get("branch"), at)
                return {"status": "released", "bench": self._bench_alias(bench), "sweep": name,
                        "branch": cm.get("branch"), "released_at": at}
        return {"status": "noop", "bench": self._bench_alias(bench), "sweep": name,
                "reason": "no condition for branch %s" % branch}

    # ── driver_pick (B1-c — the auto-run driver's branch picker, called from the kernel tick) ──────
    def driver_pick(self, bench: str = "", name: str = "") -> Dict[str, Any]:
        """B1-c — the auto-run driver's branch picker (called from `_bench_autorun_tick` after the static
        workflows of a run end ok). It is the ONLY spender of the sweep's budget:

          1. reset `spent_today` when the bench day (UTC date) rolls;
          2. refuse when `budget.per_day` or `budget.total` is exhausted (no auto-driving without a
             budget — a sweep with no budget block is opt-OUT of the driver);
          3. `sweep.materialise n=1` when nothing is pending;
          4. pick the oldest PENDING non-quarantined condition (by grid8);
          5. SPEND one unit at pick START (spent_today/spent_total +1, day=today) on the sweep_def atom.

        Returns `{status:"picked", branch:<lineage>, branch_slug, cond8, budget_left, …}` — the caller
        runs that branch as `society.run` does. When nothing is pending but `drift_per_day>0` and the
        drift budget is unspent today, returns a `drift` pick (the oldest DONE branch to re-run, so a
        result_drift deviation is minted if its artifact_id moves). Pure counters, no Sets (R3)."""
        gid = self._bench_gid(bench); self._bind(gid)
        head_alias = self._sweep_head(bench, name)
        hm = self._meta(head_alias) or {}
        if not hm:
            return {"status": "no_sweep", "sweep": name}
        bud = hm.get("budget") or {}
        per_day_set = "per_day" in bud                    # an ABSENT per_day = no daily cap (total only)
        per_day = int(bud.get("per_day", 0) or 0)         # an EXPLICIT per_day=0 = zero picks a day
        total = int(bud.get("total", 0) or 0)
        drift_per_day = int(bud.get("drift_per_day", 0) or 0)
        if not per_day_set and total <= 0:
            return {"status": "no_budget", "sweep": name}   # no budget at all → the driver is opt-OUT
        today = self._bench_day()
        spent_today = int(hm.get("spent_today", 0) or 0)
        spent_total = int(hm.get("spent_total", 0) or 0)
        drift_today = int(hm.get("drift_today", 0) or 0)
        if hm.get("day") != today:          # a new bench day rolls the daily counters
            spent_today = 0
            drift_today = 0
        if per_day_set and spent_today >= per_day:          # per_day=0 blocks immediately (0 >= 0)
            return {"status": "budget_exhausted", "scope": "per_day", "sweep": name,
                    "spent_today": spent_today, "per_day": per_day}
        if total > 0 and spent_total >= total:
            return {"status": "budget_exhausted", "scope": "total", "sweep": name,
                    "spent_total": spent_total, "total": total}
        st = self.op_status(bench=bench, name=name)

        def _pending(status_obj):
            return sorted([c for c in (status_obj.get("conditions") or [])
                           if c.get("status") == "pending" and not c.get("quarantined")],
                          key=lambda c: c.get("grid8") or "")

        pend = _pending(st)
        if not pend:
            # nothing pending — turn one un-materialised condition into a branch, then re-read the fan.
            m = self.op_materialise(bench=bench, name=name, n=1)
            if m.get("branches", 0) > 0:
                st = self.op_status(bench=bench, name=name)
                pend = _pending(st)
        hk = self._key(head_alias)
        if pend:
            pick = pend[0]
            branch_slug = pick.get("branch")
            cond8 = pick.get("cond8")
            marker = self._meta(self._sweep_marker(bench, branch_slug)) or {}
            lineage = marker.get("lineage") or branch_slug
            # SPEND one unit at pick START (a started pick counts against the budget even if its run later
            # fails — the budget bounds attempts, not successes).
            self._set_meta(hk, "spent_today", spent_today + 1)
            self._set_meta(hk, "spent_total", spent_total + 1)
            self._set_meta(hk, "day", today)
            budget_left = (total - (spent_total + 1)) if total > 0 else None
            logger.info("[sweep] pick bench=%s name=%s branch=%s cond8=%s spent=%d/%s",
                        self._bench_alias(bench), name, lineage, cond8, spent_total + 1,
                        total if total > 0 else "-")
            return {"status": "picked", "kind": "pending", "bench": self._bench_alias(bench),
                    "sweep": name, "branch": lineage, "branch_slug": branch_slug, "cond8": cond8,
                    "budget_left": budget_left, "total": total, "per_day": per_day,
                    "spent_today": spent_today + 1, "spent_total": spent_total + 1}
        # nothing left to run for the first time — a drift re-run (re-execute a DONE branch to detect
        # result_drift), gated by its own daily counter so it never eats the whole per_day/total budget.
        if drift_per_day > 0 and drift_today < drift_per_day:
            done = sorted([c for c in (st.get("conditions") or [])
                           if c.get("status") == "done" and not c.get("quarantined")],
                          key=lambda c: c.get("grid8") or "")
            if done:
                pick = done[0]
                branch_slug = pick.get("branch")
                marker = self._meta(self._sweep_marker(bench, branch_slug)) or {}
                lineage = marker.get("lineage") or branch_slug
                self._set_meta(hk, "drift_today", drift_today + 1)
                self._set_meta(hk, "day", today)
                logger.info("[sweep] drift bench=%s name=%s branch=%s cond8=%s drift=%d/%d",
                            self._bench_alias(bench), name, lineage, pick.get("cond8"),
                            drift_today + 1, drift_per_day)
                return {"status": "picked", "kind": "drift", "bench": self._bench_alias(bench),
                        "sweep": name, "branch": lineage, "branch_slug": branch_slug,
                        "cond8": pick.get("cond8"), "fork_pos": marker.get("fork_pos"),
                        "drift_today": drift_today + 1, "drift_per_day": drift_per_day}
        return {"status": "no_pending", "sweep": name}

    # ── sweep.leaderboard ────────────────────────────────────────────────────────
    def op_leaderboard(self, bench: str = "", name: str = "", key: str = "accuracy",
                       select_by: str = "dev", report: str = "test") -> Dict[str, Any]:
        """[sweep.leaderboard] Rank the sweep's evaluations by `key` (grouped on frame) through
        `lens.rank` over `set:wb:<b>:sweep:<name>:evaluations`, and store the ranking as an epoch-keyed
        artifact `wb:<b>:leaderboard:<name>` (artifact_id + built_at_epoch, replace-on-change, old kept
        + linked). `select_by=dev report=<frame>` — today both are the held-out `test` frame (§2.4)."""
        gid = self._bench_gid(bench); self._bind(gid)
        if not name:
            raise ValueError("sweep.leaderboard requires name=")
        return self.build_leaderboard(bench, name, key=key, select_by=select_by, report=report)

    def build_leaderboard(self, bench: str = "", name: str = "", key: str = "accuracy",
                          select_by: str = "dev", report: str = "test") -> Dict[str, Any]:
        """S2-l — the leaderboard BUILDER, no participant gate: the board is DERIVED state (R0), so it
        is rebuilt automatically when a sweep evaluation lands (learning.evaluate) and verified at boot
        (hydrate), never only on an operator command. `sweep.leaderboard` is this builder behind the
        participant check (the manual re-mint). One `lens.rank` over the sweep's evaluations Set + one
        `_mk_replace`; the artifact_id makes a no-change rebuild a no-op (`unchanged`)."""
        gid = self._bench_gid(bench); self._bind(gid)
        evset = self._sweep_evals_set(bench, name)
        # S2-b — COMPOSE lens.rank over the sweep's evaluations Set (grouped on frame), don't
        # re-implement the sort: one ranking algebra, guest-inspectable, frame_mismatch-aware.
        from lib.akasha.concepts.lens import LensConcept
        rk = LensConcept(self.session).op_rank(set=evset, key=key, group="frame")
        board = []
        for grp in (rk.get("groups") or []):
            for r in (grp.get("rows") or []):
                br = r.get("branch")               # the branch SLUG (main_p0_learn_observe_<cond8>)
                # JOIN this branch's sweep marker for its bindings (head/split/seed) AND its lineage.
                _mk = (self._meta(self._sweep_marker(bench, br)) or {}) if br else {}
                binds = _mk.get("bindings") or {}
                # row naming — surface the readable LINEAGE (main@p0/learn_observe@<cond8>) as `branch`,
                # matching learning.runs and the evaluation row (§2.8); keep the slug as `branch_slug` for a
                # GUI key. Fall back to the slug when a marker has no lineage.
                lineage = _mk.get("lineage") or br
                board.append({"rank": r.get("rank"), "branch": lineage, "branch_slug": br,
                              "cond8": r.get("cond8"),
                              "frame": r.get("frame"), key: r.get(key), "macro_f1": r.get("macro_f1"),
                              "model": r.get("model"), "engine": r.get("engine"), "bindings": binds,
                              # leak? — today select_by=dev and report= are the SAME held-out `test`
                              # frame, so there is no dev/report separation to leak across (§2.4). Real
                              # leak detection (train∩test overlap) is P0-b; for now this is False.
                              "leak": False})
        epoch = self._akasha_now()
        aid = _artifact_id(epoch, "universal", name, [evset], "sweep.leaderboard", report, "member")
        alias = "wb:%s:leaderboard:%s" % (_uslug(bench), _uslug(name))
        k, changed, old = self._mk_replace(
            alias, "[%s] %d rows by %s (select_by=%s report=%s)" % (alias, len(board), key, select_by, report),
            {"concept": "sweep_leaderboard", "bench": self._bench_alias(bench), "sweep": name,
             "key": key, "select_by": select_by, "report": report, "rows": board, "count": len(board),
             "frame_mismatch": rk.get("frame_mismatch", False),
             "built_at_epoch": epoch, "artifact_id": aid, "author": self._client()},
            compare_meta=("rows",))
        if old:
            self._link(alias, old, "bench:superseded_by")   # history reachable
            # S2-b — keep every prior generation in the per-sweep :history Set (regenerable trail)
            self._add_to_set("set:wb:%s:leaderboard:%s:history" % (_uslug(bench), _uslug(name)), old)
        self._add_to_set("set:wb:%s:leaderboard:%s:history" % (_uslug(bench), _uslug(name)), k)
        self._add_to_set("set:wb:%s:leaderboards" % _uslug(bench), k)
        logger.info("[sweep] leaderboard bench=%s name=%s rows=%d epoch=%s%s", self._bench_alias(bench),
                    name, len(board), epoch, " (rebuilt)" if changed else " (unchanged)")
        return {"status": "ranked", "bench": self._bench_alias(bench), "sweep": name, "leaderboard": alias,
                "key": key, "select_by": select_by, "report": report, "rows": board, "count": len(board),
                "frame_mismatch": rk.get("frame_mismatch", False),
                "built_at_epoch": epoch, "artifact_id": aid, "changed": changed}
