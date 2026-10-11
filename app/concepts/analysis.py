"""
Analysis Concept Model — analysis.*

The standard **Analysis View** over the Source Window (Labo World-Model Directive §3). This model is
a lightweight PROJECTION/CONTROL + PROVENANCE surface over analysis/transform plugins — it does NOT
build a statistics engine (§14 anti-pattern). Vectorization, PCA/UMAP, clustering, affine transforms
and numerical analysis remain replaceable plugins.

Non-negotiables (§3, §3.1):
- Clustering output is materialized as **Sets, never as the one true classification**.
- Switching clustering/projection methods = switching RESULT SETS, not rebuilding state.
- One Source Atom may belong to **multiple** statistical + semantic Sets simultaneously.
- Multiple result Sets overlay on the same population; union/intersection/difference are supported.
- Method disagreement is made VISIBLE: a method-invariant/**core** Set (stable across methods) and
  method-sensitive **boundary** cases are materialized separately.
- Numerical similarity and semantic interpretation stay distinguishable — a geometric cluster may
  receive zero, one or many semantic labels (those live in labo.interpret, not here).

Every run persists provenance: input Set, plugin/version, parameters, cronon, output projection and
output Sets. Two dependency-free built-in analyses ship (`groupby:<field>`, `count:<field>`) so the
CLI is useful out of the box; any other plugin name records provenance and accepts declared outputs.

Boundary with the two neighbouring models (kept strictly non-overlapping — one responsibility each):

  • Aggregation (`agg:*`, concepts/aggregation.py — Unit → Group → Measure → Analysis → Hierarchy).
    ⚠️ THIS AND AGGREGATION GENUINELY OVERLAP — they are not cleanly complementary. Both model the
    SAME statistical core three times over:
        agg.group.add (labelled partition, manual members)   ≈  analysis groupby (partition, auto by field)
        agg.measure.add (count/share per group)              ≈  analysis count  (per-group counts)
        agg.analysis.add (scored relation between 2 groups)  ≈  analysis.overlay (computed Jaccard)   ← agg even NAMES this sub-part "analysis"
    The only real differences today are authoring + storage + reach: aggregation is HAND-authored,
    durable Group/Measure/Hierarchy ATOMS, owner-scoped (survey / delib use it); analysis is the
    AUTOMATIC, plugin-provenanced, Labo-bound, guest-readable layer whose partitions are result
    **Sets** carrying set-algebra (union / intersect / diff / core / boundary) — the parts agg lacks.
    ► RECOMMENDED TARGET DIVISION (agreed; not a merge but a clean re-split along Operand/Operator):
        aggregation → a GENERAL-PURPOSE, STATELESS statistical TOOLBOX (the Operator layer): pure
                      operations — grouping, count / mean / distribution, correlation, inter-group
                      scores — computed over whatever atoms/values it is handed. Owns no session state.
        analysis    → the MANAGEMENT of statistical-analysis TARGETS and RESULTS (the Operand/record
                      layer): owns the input population (Set) selection, the result Sets + projections,
                      provenance (plugin / params / cronon), set-algebra (union / intersect / core /
                      boundary / overlay), Labo binding and recompute-free re-fetch. It CALLS the
                      aggregation toolbox to compute; it stores and manages what goes in and comes out.
    Then the overlap dissolves: agg COMPUTES (operator), analysis MANAGES target+result (operand).
    DO NOT grow either twin further in isolation — realize this split at the NEXT implementation
    addition that touches statistical grouping/measures. Migration note: aggregation is TODAY a
    stateful structure-builder, so the work is factoring pure operators OUT of it — but DO A FULL
    DEPENDENCY SWEEP FIRST (hidden consumers may exist; do not touch it before that). Known today:
    `delib` is the only programmatic consumer (imports AggregationConcept, drives
    `agg.new`/`group`/`measure`/`analysis`); plus the CLI `ag.*` aliases (api/router.py) and a bare
    concept-name entry in intelligence.py's catalog. Doc-only until then.

  • The present PRIMITIVE (the pipeline PresentTableSink / ScatterSink / NarrativeSink,
    lib/harmonia/pipeline.py) is a peer render unit — ONE drawable frame, `{"kind": "present",
    "format": "table" | "scatter" | "distribution", ...}`. To avoid a second, rival render format,
    every projection this model emits IS that primitive, tagged `"source": "statistical"`. The ONE
    difference from the semantic ScatterSink (which positions by the Consciousness cosmos_nd vector)
    is the positioning source: here points are placed by RAW metadata fields. Statistical reading
    (this model) and semantic reading (cosmos / labo.interpret) stay distinct axes that may cross,
    never merged — and the GUI has ONE renderer for both.

  • The Presentation MODEL (`pres:*`, concepts/presentation.py — Deck → Frame → Region → Node) is
    NOT a peer of this model and does not overlap it: it is the UPPER layer — a slide-deck /
    kamishibai that COMPOSES rendered frames into an ordered narrative. An analysis projection (or a
    semantic present frame) is content it can mount as a `pres.node`/`pres.frame`; analysis sits
    BENEATH it as a producer, presentation arranges above. One is a chart, the other is the deck.
"""
import itertools
import logging
import os
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List


def _pace(members):
    """Iterate the member walk POLITELY so the background precompute never starves an interactive
    read. The full-member `get_meta` walk runs inside a Harmonia batch (analysis.run), but on the
    native store a tight 26k-member loop can hold the store long enough that a concurrent
    `source.pool.ls` / `source.status` from a visitor times out ('計算中' for a full minute). Sleeping
    briefly every N members yields the store/GIL so those reads slip through. Backgrounds are meant to
    be slow-but-polite; the added time is trivial. Tunable: AKASHA_PRECOMPUTE_YIELD_EVERY (default
    1000), AKASHA_PRECOMPUTE_YIELD_MS (default 20). Set EVERY or MS to 0 to disable."""
    try:
        every = int(os.environ.get("AKASHA_PRECOMPUTE_YIELD_EVERY", "1000") or 1000)
        ms = float(os.environ.get("AKASHA_PRECOMPUTE_YIELD_MS", "20") or 20) / 1000.0
    except (TypeError, ValueError):
        every, ms = 1000, 0.02
    if every <= 0 or ms <= 0:
        for x in members:
            yield x
        return
    i = 0
    for x in members:
        yield x
        i += 1
        if i % every == 0:
            time.sleep(ms)


def _analysis_topn() -> int:
    """Cap on the number of rows a PERSISTED projection stores (a distribution's tail is long; a
    per-value dict of tens of thousands of entries is a fat atom). 0 = uncapped. Default 500."""
    try:
        return max(0, int(os.environ.get("AKASHA_ANALYSIS_TOPN", "500")))
    except (TypeError, ValueError):
        return 500


def _groupby_max_sets() -> int:
    """Cap on how many result Sets a `groupby` MATERIALIZES. A groupby on a high-cardinality field
    (e.g. a respondent id) would otherwise create one Set per value — tens of thousands of writes
    flooding the WriteQueue (blocking reads). Above this, the projection is kept but NO Sets are
    materialized (a 26k-way "clustering" is meaningless anyway). Default 200."""
    try:
        return max(1, int(os.environ.get("AKASHA_GROUPBY_MAX_SETS", "200")))
    except (TypeError, ValueError):
        return 200


def _max_pairs() -> int:
    """Cap on how many field PAIRS the auto-precompute prepares scatter projections for. The viewer can
    pick ANY field×field pair, and — because guests must never trigger a compute and there is no operator
    step — EVERY selectable pair has to be prepared in advance, or it shows "Computing" forever. A survey
    pool has many coded fields (mobility ≈ 46 → C(46,2)=1035 pairs), so the cap must cover them; the pairs
    are all built in ONE bounded pass (not a walk each), so the only cost is stored atoms, which the
    smaller point-cap below keeps light. ⚠️ INVARIANT: this must be ≥ C(MAX_FIELDS, 2) so that EVERY pair
    of prepared fields is prepared — the viewer offers only prepared fields, so a shortfall here would
    leave a selectable pair showing "Computing" forever. Default 3160 ≥ C(80,2)=3160 (the field ceiling). A
    pathological ultra-wide pool is still bounded. 0 = uncapped."""
    try:
        return max(0, int(os.environ.get("AKASHA_PRECOMPUTE_MAX_PAIRS", "3160")))
    except (TypeError, ValueError):
        return 3160


def _scatter_pcap() -> int:
    """Cap on the number of member POINTS a precomputed scatter atom stores. Because ALL field pairs are
    prepared (up to C(60,2)=1770 on a wide survey pool) and the store keeps atom values in RAM, this is
    kept small — a categorical survey scatter reads its shape from a few hundred points; 2000 would just
    overplot and multiply the resident size by pairs. Default 400 (× 1770 pairs ≈ 0.17 GB worst case, the
    one widest frozen corpus). Also bounds the single build pass (O(pcap))."""
    try:
        return max(1, int(os.environ.get("AKASHA_PRECOMPUTE_SCATTER_PCAP", "400")))
    except (TypeError, ValueError):
        return 400


def _max_distinct() -> int:
    """The distinct-value ceiling that separates a MEANINGFUL CATEGORY from a categorically-meaningless
    field (a date, a serial/sequence number, a unique id, free text). A field whose value set stays
    under this ceiling is a category and is ALWAYS prepared; a field that reaches it has too many
    distinct values to be a category (its distribution is unreadable and its scatter is just a diagonal)
    and is excluded — the policy: exclude dates/serials, always compute anything with categorical
    meaning. It ALSO bounds the count accumulator's per-field height (memory: ≤ this many entries per
    field during the walk), so a unique id never balloons the accumulator. Default 500."""
    try:
        return max(2, int(os.environ.get("AKASHA_ANALYSIS_MAX_DISTINCT", "500")))
    except (TypeError, ValueError):
        return 500


def _is_categorical(distinct: int, hit_cap: bool, n_total: int) -> bool:
    """True if a field is a MEANINGFUL category (→ always computed), False if categorically meaningless
    (date / serial / unique id / free text → excluded). Two signals, both from the count tally (no extra
    walk): (1) it reached the distinct ceiling → too many values to be a category; (2) it is near-unique
    — distinct ≈ member count — the shape of a serial/id/date even on a small pool. A field with a small,
    repeating value set passes both and is kept, however many fields the pool has."""
    if hit_cap:
        return False
    if n_total >= 20 and distinct > max(1, int(0.7 * n_total)):
        return False
    return True

from lib.akasha.api.concepts import UniversalConcept, slug

logger = logging.getLogger("Harmonia.Concept.Analysis")

R_IN_LABO      = "analysis:in_labo"
R_INPUT        = "analysis:input"        # run → input set
R_USES_PLUGIN  = "analysis:uses_plugin"  # run → plugin
R_PRODUCES     = "analysis:produces"     # run → output set / projection
R_DERIVED_FROM = "analysis:derived_from" # a core/algebra set → its source sets


class AnalysisConcept(UniversalConcept):
    """Plugin-provenance + result-Set surface over the Source Window. Results are traceable Sets,
    never ontological truths."""

    CONCEPT_PREFIX = "analysis"
    CONCEPT_LABEL = "Analysis View — plugin runs → traceable result Sets (never the one true classification)"

    CONCEPT_METHODS: Dict[str, Any] = {
        "run":   {"op": "op_run", "action": "record",
                  "desc": "Run an analysis plugin over an input Set → output result Sets + a persisted provenance record."},
        "precompute_counts": {"op": "op_precompute_counts", "action": "record",
                  "desc": "Batch-precompute the count distributions of MANY fields in ONE member pass (boot precompute path; reads then re-fetch O(1))."},
        "count_chunk": {"op": "op_count_chunk", "action": "record",
                  "desc": "One slice of the chunked precompute (job-visible progress): fold members[offset:offset+chunk] into the shared accumulator. Resumable."},
        "count_finalize": {"op": "op_count_finalize", "action": "record",
                  "desc": "Persist each field's count run from the completed accumulator, then drop it."},
        "view":  {"op": "op_view", "action": "read",
                  "desc": "Compute a projection (distribution/count/scatter/groupby counts) and RETURN it WITHOUT persisting — a read-only statistical view any visitor can render (no operator write)."},
        "runs":  {"op": "op_runs", "action": "read", "desc": "List a Labo's analysis runs with their provenance."},
        "get":   {"op": "op_get", "action": "read", "desc": "Read one analysis run (input, plugin, params, outputs, cronon)."},
        "set":   {"op": "op_set", "action": "record",
                  "desc": "Set algebra over two result Sets: union / intersect / diff → a new persisted Set."},
        "core":  {"op": "op_core", "action": "record",
                  "desc": "Materialize the method-invariant CORE Set (members in ALL given Sets) + the boundary Set (method-sensitive)."},
        "overlay": {"op": "op_overlay", "action": "read",
                    "desc": "Compare two result Sets: overlap / Jaccard — makes method disagreement visible without hiding it."},
        "ls":    {"op": "op_sets", "action": "read", "desc": "List a Labo's result Sets (analysis outputs)."},
        "reset": {"op": "op_reset", "action": "record",
                  "desc": "Drop a Labo's persisted analysis runs/Sets so a following analysis.precompute rebuilds them uniformly (e.g. after a pair/point-cap change). Fenced to the Labo; never touches the source pool. Admin/librarian."},
    }

    # ── input / set helpers ──────────────────────────────────────────────────────
    def _members_set_of(self, ref: str) -> str:
        """A pool/snapshot/sample/analysis-set atom stores its members in `<id>:members`; a plain set
        name is used directly."""
        k = self._key(ref)
        if k:
            concept = (self.cortex.get_meta(k) or {}).get("concept", "")
            if concept in ("source_pool", "source_snapshot", "source_sample", "analysis_set"):
                return f"{self._alias(k)}:members"
        return ref

    def _input_members(self, ref: str) -> List[str]:
        return self._members(self._members_set_of(ref))

    def _make_set(self, labo: str, name: str, member_keys: List[str], meta_extra: Dict[str, Any]) -> str:
        nm = labo.replace("labo:", "")
        sid = f"analysis:set:{slug(nm)}:{slug(name)}"
        meta = {"concept": "analysis_set", "labo": f"labo:{slug(nm)}", "name": name,
                "cronon": self._akasha_now(), "size": len(member_keys), **meta_extra}
        self._mk(sid, f"[{sid}] Analysis result Set — {name} (n={len(member_keys)})", meta)
        for mk in member_keys:
            self._add_to_set(f"{sid}:members", mk)
        self._add_to_set(f"analysis:set:{slug(nm)}", self._key(sid))
        return sid

    # ── pure compute (no writes) — the BATCH cost, run only inside analysis.run ────────
    def _compute_projection(self, members: List[str], plugin: str, params: str = ""):
        """PURE READ: compute the presentation-primitive projection over the input members' raw
        `source_metadata`. No writes. Returns (projection, buckets); `buckets` is present only for
        groupby so a caller (op_run) can optionally materialize result Sets — op_view ignores it.

        ⚠️ This walks EVERY member (`get_meta` per member) — a full Atom sweep. It is therefore the
        BATCH cost and is ONLY ever invoked from `op_run`, which is meant to be submitted as a Harmonia
        background job (`analysis.precompute`), never on the interactive/read path. `op_view` NEVER
        calls this — it re-fetches the persisted result. `input_size` records the full population."""
        n_total = len(members)
        topn = _analysis_topn()
        buckets = None
        projection = None
        if plugin.startswith("groupby:"):
            field = plugin.split(":", 1)[1]
            buckets = defaultdict(list)
            for mk in _pace(members):
                v = str(((self.cortex.get_meta(mk) or {}).get("source_metadata") or {}).get(field, "?"))
                buckets[v].append(mk)
            # Bound the PERSISTED projection to the top-N groups (a distribution's tail is long and a
            # per-value dict of 26k entries is a fat atom). `distinct` keeps the true group count.
            _ordered = sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            _top = _ordered[:topn] if topn > 0 else _ordered
            rows = [{field: v, "count": len(ks)} for v, ks in _top]
            projection = {"kind": "present", "format": "table", "source": "statistical",
                          "field": field, "columns": [field, "count"], "rows": rows,
                          "row_count": len(rows), "groups": {v: len(ks) for v, ks in _top},
                          "distinct": len(buckets), "truncated": topn > 0 and len(buckets) > topn,
                          "as_sets": True, "input_size": n_total}
        elif plugin.startswith("count:"):
            field = plugin.split(":", 1)[1]
            dist = Counter(str(((self.cortex.get_meta(mk) or {}).get("source_metadata") or {}).get(field, "?"))
                           for mk in _pace(members))
            most = dist.most_common(topn if topn > 0 else None)
            rows = [{field: v, "count": n} for v, n in most]
            projection = {"kind": "present", "format": "distribution", "source": "statistical",
                          "field": field, "columns": [field, "count"], "rows": rows,
                          "row_count": len(rows), "counts": dict(most), "distinct": len(dist),
                          "truncated": topn > 0 and len(dist) > topn, "input_size": n_total}
        elif plugin.startswith("scatter:"):
            spec = plugin.split(":", 1)[1]
            fx, _, fy = spec.partition(",")
            fx, fy = fx.strip(), fy.strip()
            try:
                pcap = max(1, min(int(params) if str(params).isdigit() else 8000, 30000))
            except (TypeError, ValueError):
                pcap = 8000
            pts_members = members[:pcap]

            def _vals(field):
                raw = [((self.cortex.get_meta(mk) or {}).get("source_metadata") or {}).get(field) for mk in _pace(pts_members)]
                nums, ok = [], True
                for v in raw:
                    try:
                        nums.append(float(v))
                    except (TypeError, ValueError):
                        ok = False
                        break
                if ok:
                    return raw, nums, False, None
                cats = sorted({("∅" if v in (None, "") else str(v)) for v in raw})
                idx = {c: i for i, c in enumerate(cats)}
                return raw, [idx["∅" if v in (None, "") else str(v)] for v in raw], True, cats

            _rx, xs, x_cat, x_cats = _vals(fx)
            _ry, ys, y_cat, y_cats = _vals(fy)
            pts = [{"key": self._alias(pts_members[i]), "label": self._alias(pts_members[i]),
                    "x": xs[i], "y": ys[i]} for i in range(len(pts_members))]
            projection = {"kind": "present", "format": "scatter", "source": "statistical",
                          "x": fx, "y": fy, "x_categorical": x_cat, "y_categorical": y_cat,
                          "x_cats": x_cats, "y_cats": y_cats, "n": n_total, "points": pts,
                          "count": len(pts), "truncated": n_total > len(pts_members), "input_size": n_total}
        return projection, buckets

    def _persisted_projection(self, labo: str, input: str, plugin: str, params: str = ""):
        """Return a PREVIOUSLY-PERSISTED projection for exactly this (input, plugin, params), or None.
        A pool is FROZEN (immutable) and an `analysis.run` is immutable, so a persisted projection is
        always still valid — this is the "re-fetched, never recomputed" contract. The scan is over the
        Labo's run atoms (a handful), not the pool's members, so it is cheap regardless of pool size."""
        nm = labo.replace("labo:", "")
        _ikey = self._key(input) or input          # resolve so an alias and its raw key both match
        for k in self._members(f"analysis:run:{slug(nm)}"):
            m = self.cortex.get_meta(k) or {}
            if not (m.get("plugin") == plugin and (m.get("params") or "") == (params or "") and m.get("projection")):
                continue
            _si = m.get("input")
            if _si == input or (self._key(_si) or _si) == _ikey:
                return m.get("projection"), self._alias(k), m.get("cronon")
        return None

    def _persisted_plugin_set(self, labo: str, input: str, params: str = "") -> set:
        """The SET of plugin strings already persisted for this (input, params) — one scan of the Labo's
        run atoms, so checking "is this pair prepared?" for hundreds of pairs is O(runs) once, not
        O(pairs×runs). Used by derived_pending / _precompute_derived where the pair count is large."""
        nm = labo.replace("labo:", "")
        _ikey = self._key(input) or input
        out = set()
        for k in self._members(f"analysis:run:{slug(nm)}"):
            m = self.cortex.get_meta(k) or {}
            if not (m.get("projection") and (m.get("params") or "") == (params or "")):
                continue
            _si = m.get("input")
            if _si == input or (self._key(_si) or _si) == _ikey:
                p = m.get("plugin")
                if p:
                    out.add(p)
        return out

    def _persist_projection(self, nm: str, lid: str, input: str, plugin: str, params: str,
                            projection: Dict[str, Any], out_sets=None) -> str:
        """Persist ONE analysis run atom for an ALREADY-COMPUTED projection (no member walk here). The
        write side shared by op_run and the combined op_precompute_counts."""
        at = self._akasha_now()
        seq = len(self._members(f"analysis:run:{slug(nm)}")) + 1
        run_id = f"analysis:run:{slug(nm)}:{seq}"
        meta = {"concept": "analysis_run", "labo": self._alias(self._key(lid)), "input": input,
                "input_size": (projection or {}).get("input_size"), "plugin": plugin, "params": params,
                "cronon": at, "projection": projection, "outputs": out_sets or []}
        self._mk(run_id, f"[{run_id}] {plugin} over {input}", meta)
        self._link(run_id, lid, R_IN_LABO)
        self._link(run_id, self._members_set_of(input), R_INPUT)
        self._link(run_id, f"plugin:{slug(plugin)}", R_USES_PLUGIN)
        self._add_to_set(f"analysis:run:{slug(nm)}", self._key(run_id))
        return run_id

    # ── derived projections (groupby + scatter) — prepared IN THE SAME background build ──────────
    # The Source Viewer offers three views per pool: distribution (count), cluster (groupby) and
    # scatter (field×field). ALL THREE must be prepared IN ADVANCE via Harmonia — a viewer NEVER
    # triggers a compute and NO operator "prepare" step exists (the absolute rule). count is the walk;
    # groupby is DERIVED FROM the same count tally for free (identical group sizes, no extra walk); and
    # scatter is built from a SINGLE BOUNDED pass over members[:pcap] (O(pcap), not O(store)) that
    # yields every field pair at once. So adding cluster + every scatter costs one cheap bounded pass,
    # never the O(store)-per-view fan-out that made counts "never finish".
    def _groupby_projection(self, field: str, count_map: Dict[str, int], n_total: int) -> Dict[str, Any]:
        topn = _analysis_topn()
        ordered = sorted((count_map or {}).items(), key=lambda kv: (-kv[1], kv[0]))
        top = ordered[:topn] if topn > 0 else ordered
        return {"kind": "present", "format": "table", "source": "statistical", "field": field,
                "columns": [field, "count"], "rows": [{field: v, "count": n} for v, n in top],
                "row_count": len(top), "groups": {v: n for v, n in top}, "distinct": len(count_map or {}),
                "truncated": topn > 0 and len(count_map or {}) > topn, "as_sets": True,
                "input_size": n_total}

    def _scatter_projection(self, fx: str, fy: str, raw_x: List[Any], raw_y: List[Any],
                            n_total: int, n_walked: int) -> Dict[str, Any]:
        def _axis(raw):
            nums, ok = [], True
            for v in raw:
                try:
                    nums.append(float(v))
                except (TypeError, ValueError):
                    ok = False
                    break
            if ok:
                return nums, False, None
            cats = sorted({("∅" if v in (None, "") else str(v)) for v in raw})
            idx = {c: i for i, c in enumerate(cats)}
            return [idx["∅" if v in (None, "") else str(v)] for v in raw], True, cats
        xs, x_cat, x_cats = _axis(raw_x)
        ys, y_cat, y_cats = _axis(raw_y)
        # COMPACT points: {x,y} only. The renderer reads solely x/y (a density cloud, no per-point
        # tooltip), and EVERY field pair is stored — carrying the member id twice per point (key+label)
        # would multiply the resident size of hundreds of scatter atoms for data nothing reads.
        pts = [{"x": xs[i], "y": ys[i]} for i in range(len(xs))]
        return {"kind": "present", "format": "scatter", "source": "statistical", "x": fx, "y": fy,
                "x_categorical": x_cat, "y_categorical": y_cat, "x_cats": x_cats, "y_cats": y_cats,
                "n": n_total, "points": pts, "count": len(pts), "truncated": n_total > n_walked,
                "input_size": n_total}

    @staticmethod
    def _transpose_scatter(projection: Dict[str, Any]) -> Dict[str, Any]:
        """Return a scatter projection with its X and Y axes swapped — so a pair stored as (b,a) can
        answer a request for (a,b) without recompute. Pure re-labelling of the persisted result."""
        p = dict(projection or {})
        p["x"], p["y"] = p.get("y"), p.get("x")
        p["x_categorical"], p["y_categorical"] = p.get("y_categorical"), p.get("x_categorical")
        p["x_cats"], p["y_cats"] = p.get("y_cats"), p.get("x_cats")
        p["points"] = [dict(pt, x=pt.get("y"), y=pt.get("x")) for pt in (p.get("points") or [])]
        return p

    def _count_projection(self, f: str, dist: Dict[str, int], hit_cap: bool,
                          n_total: int, topn: int) -> Dict[str, Any]:
        """Build the persisted `count:<field>` projection AND stamp whether the field is a MEANINGFUL
        CATEGORY (`categorical`). A non-categorical field (date / serial / unique id / free text) is
        still recorded — so the precompute CONVERGES (its count run exists → it is not re-walked every
        boot) — but as a light marker with no distribution rows, and it is excluded from the cluster /
        scatter views and from the viewer's field menus (the policy: exclude dates/serials, always
        compute anything with categorical meaning)."""
        distinct = len(dist)
        categorical = _is_categorical(distinct, hit_cap, n_total)
        if not categorical:
            return {"kind": "present", "format": "distribution", "source": "statistical", "field": f,
                    "categorical": False, "columns": [f, "count"], "rows": [], "row_count": 0,
                    "counts": {}, "distinct": distinct, "distinct_capped": hit_cap, "input_size": n_total,
                    "note": "not a category (too many distinct values — a date, serial, id or free text) "
                            "— excluded from the statistical views"}
        most = sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))[:topn] if topn > 0 \
            else sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))
        return {"kind": "present", "format": "distribution", "source": "statistical", "field": f,
                "categorical": True, "columns": [f, "count"], "row_count": len(most),
                "rows": [{f: v, "count": n} for v, n in most], "counts": dict(most),
                "distinct": distinct, "truncated": topn > 0 and distinct > topn, "input_size": n_total}

    def _categorical_fields(self, labo: str, input: str, fields: List[str]) -> List[str]:
        """The subset of `fields` whose persisted `count:<field>` run is a MEANINGFUL CATEGORY (i.e. not
        stamped `categorical:false`). Used so the cluster/scatter prep + the pending check only ever
        consider category fields — a date/serial column is prepared as a count MARKER but drives no
        groupby/scatter and never keeps the precompute 'pending'. A field with no count run yet is
        treated as still-to-decide (kept), so it gets counted + classified on this pass."""
        lid = "labo:%s" % slug(labo.replace("labo:", ""))
        out = []
        for f in fields:
            pv = self._persisted_projection(lid, input, "count:%s" % f, "")
            if pv is None:
                out.append(f)                                  # not yet counted — classify it this pass
            elif (pv[0] or {}).get("categorical") is not False:
                out.append(f)                                  # counted AND a category
        return out

    def _precompute_derived(self, nm: str, lid: str, input: str, fields: List[str],
                            counts: Dict[str, Dict[str, int]], n_total: int,
                            members: List[str] = None) -> Dict[str, Any]:
        """Persist the cluster (groupby) + scatter projections that go with an already-computed set of
        field counts, so the viewer's every view is prepared in advance. groupby is derived from
        `counts` with NO walk; scatter needs one BOUNDED pass over members[:pcap] (built once for all
        pairs). Idempotent: skips any projection already persisted."""
        made_gb, made_sc = [], []
        # One scan of the run atoms → the set of plugins already prepared. Checking hundreds of pairs
        # against this set is O(runs) once, NOT O(pairs×runs).
        have = self._persisted_plugin_set(lid, input)
        # (a) cluster = groupby projection, DERIVED from the count tally (no walk).
        for f in fields:
            if ("groupby:%s" % f) in have:
                continue
            self._persist_projection(nm, lid, input, "groupby:%s" % f, "",
                                     self._groupby_projection(f, counts.get(f) or {}, n_total), [])
            made_gb.append(f)
        # (b) scatter = one bounded pass over members[:pcap], every missing pair built from it. EVERY
        # selectable pair is prepared (the viewer may pick any two fields; a guest can never trigger a
        # compute and there is no operator step), bounded by _max_pairs.
        max_pairs = _max_pairs()
        pairs = list(itertools.combinations(fields, 2))
        if max_pairs:
            pairs = pairs[:max_pairs]
        missing = [(fx, fy) for fx, fy in pairs if ("scatter:%s,%s" % (fx, fy)) not in have]
        if missing:
            if members is None:
                members = self._input_members(input)
            pcap = _scatter_pcap()
            pts_members = members[:pcap]
            need_fields = sorted({f for pr in missing for f in pr})
            cols = {f: [] for f in need_fields}
            for mk in _pace(pts_members):                       # ONE bounded pass for ALL pairs
                sm = (self.cortex.get_meta(mk) or {}).get("source_metadata") or {}
                for f in need_fields:
                    cols[f].append(sm.get(f))
            for fx, fy in missing:
                self._persist_projection(nm, lid, input, "scatter:%s,%s" % (fx, fy), "",
                                         self._scatter_projection(fx, fy, cols[fx], cols[fy],
                                                                  n_total, len(pts_members)), [])
                made_sc.append("%s,%s" % (fx, fy))
        return {"groupby": made_gb, "scatter": made_sc}

    def derived_pending(self, labo: str, input: str, fields: List[str]) -> bool:
        """True if ANY cluster (groupby) or scatter projection for the CATEGORY fields is NOT yet
        persisted — a cheap run-atom scan (never a member walk). Lets the boot precompute self-heal a
        pool whose counts were prepared by older code (counts present, cluster/scatter still missing).
        Only category fields are considered: a date/serial field is prepared as a count marker but drives
        no groupby/scatter, so it must never keep this 'pending' (which would resubmit every boot). A
        field not yet counted counts as pending — it still needs its first classification pass."""
        lid = "labo:%s" % slug(labo.replace("labo:", ""))
        have = self._persisted_plugin_set(lid, input)     # one scan; membership checks are O(1)
        cat = self._categorical_fields(lid, input, fields)
        # a not-yet-counted field → its count run (which also classifies it) is still to come → pending
        for f in fields:
            if ("count:%s" % f) not in have:
                return True
        for f in cat:
            if ("groupby:%s" % f) not in have:
                return True
        max_pairs = _max_pairs()
        pairs = list(itertools.combinations(cat, 2))
        if max_pairs:
            pairs = pairs[:max_pairs]
        for fx, fy in pairs:
            if ("scatter:%s,%s" % (fx, fy)) not in have:
                return True
        return False

    def op_precompute_counts(self, labo: str, input: str, fields=None) -> Dict[str, Any]:
        """R1/R4-safe batch precompute: compute the count distribution of MANY fields in a SINGLE member
        pass (one `get_meta` per member for ALL fields — NOT one O(store) pass per field, which never
        finished under the disk-resident index), persisting each as a `count:<field>` run so reads stay
        O(1) re-fetches. Gated/idempotent (skips already-persisted fields), streamed + PACED, and the
        accumulator is bounded (fields × distinct values), so it is a one-time background build, never a
        per-read walk. Then the cluster (groupby) + scatter projections are prepared from the SAME tally
        + ONE bounded pass, so every viewer view is ready in advance (no operator step, no per-read walk)."""
        nm = labo.replace("labo:", "")
        lid = f"labo:{slug(nm)}"
        if not self._key(lid):
            raise ValueError(f"unknown labo '{labo}' — labo.new it first")
        if isinstance(fields, str):
            fields = [f.strip() for f in fields.split(",") if f.strip()]
        fields = list(fields or [])
        todo = [f for f in fields
                if self._persisted_projection(labo, input, "count:%s" % f, "") is None]
        members = self._input_members(input)               # indexed keys (O(K)), needed for scatter too
        n_total = len(members)
        topn = _analysis_topn()
        made = []
        counts_map: Dict[str, Dict[str, int]] = {}
        if todo:
            # Per-field distinct-value CAP — bounds the accumulator height (memory) AND is the signal
            # that a field is not a category (a serial/id/date reaches the cap; a category never does).
            cap = _max_distinct()
            dists = {f: {} for f in todo}
            over = {f: False for f in todo}
            for mk in _pace(members):                      # ONE walk for ALL not-yet-counted fields
                sm = (self.cortex.get_meta(mk) or {}).get("source_metadata") or {}
                for f in todo:
                    v = str(sm.get(f, "?"))
                    d = dists[f]
                    if v in d:
                        d[v] += 1
                    elif len(d) < cap:
                        d[v] = 1
                    else:
                        over[f] = True                      # hit the distinct ceiling → not a category
            for f in todo:
                projection = self._count_projection(f, dists[f], over[f], n_total, topn)
                self._persist_projection(nm, lid, input, "count:%s" % f, "", projection, [])
                if projection.get("categorical") is not False:
                    counts_map[f] = dict(dists[f])
                made.append(f)
        # Assemble the FULL per-field count tally (fresh + already-persisted) for the CATEGORY fields only,
        # so cluster (groupby) can be derived for every category even when its count was persisted on an
        # earlier boot — self-healing. Non-category (date/serial) fields are skipped here and below.
        cat_fields = self._categorical_fields(lid, input, fields)
        for f in cat_fields:
            if f in counts_map:
                continue
            pv = self._persisted_projection(input=input, labo=lid, plugin="count:%s" % f)
            if pv:
                counts_map[f] = (pv[0] or {}).get("counts") or {}
        derived = self._precompute_derived(nm, lid, input, cat_fields, counts_map, n_total, members)
        logger.info("[analysis.precompute_counts] %s/%s → count=%d groupby=%d scatter=%d (n=%d)",
                    labo, input, len(made), len(derived["groupby"]), len(derived["scatter"]), n_total)
        return {"labo": labo, "input": input, "computed": len(made), "fields": made,
                "groupby": derived["groupby"], "scatter": derived["scatter"], "input_size": n_total}

    # ── CHUNKED precompute (job-visible progress) ──────────────────────────────────
    # The combined pass is one JCL step, so `job` shows only 0/1 — no "how far". For a large pool the
    # precompute is instead a MULTI-STEP job: one count_chunk per member slice (job.stat shows
    # chunk k/K = the fraction of the corpus walked) + a final count_finalize. Still ONE walk overall
    # (each member's get_meta happens in exactly one chunk), bounded per step, and RESUMABLE — a
    # running accumulator atom holds the partial counts + how many members are done.
    def _accum_alias(self, nm: str, input: str, fields: List[str]) -> str:
        import hashlib
        h = hashlib.sha1(("%s|%s" % (input, ",".join(sorted(fields)))).encode()).hexdigest()[:10]
        return "analysis:accum:%s:%s" % (slug(nm), h)

    def op_count_chunk(self, labo: str, input: str, fields=None, offset: str = "0",
                       chunk: str = "2000") -> Dict[str, Any]:
        """One slice of the chunked precompute: walk members[offset:offset+chunk] once, fold their
        field values into the shared accumulator atom, advance its `done` cursor. Idempotent/resumable
        (a re-run of an already-done offset is skipped). This is what makes progress visible in `job`."""
        nm = labo.replace("labo:", "")
        lid = "labo:%s" % slug(nm)
        if not self._key(lid):
            raise ValueError("unknown labo '%s'" % labo)
        if isinstance(fields, str):
            fields = [f.strip() for f in fields.split(",") if f.strip()]
        fields = list(fields or [])
        off = int(offset) if str(offset).strip().lstrip("-").isdigit() else 0
        ch = int(chunk) if str(chunk).strip().isdigit() else 2000
        acc_alias = self._accum_alias(nm, input, fields)
        acc_key = self._key(acc_alias)
        acc = (self.cortex.get_meta(acc_key) or {}) if acc_key else {}
        done = int(acc.get("done") or 0)
        counts = acc.get("counts") or {f: {} for f in fields}
        over = acc.get("over") or {}                   # fields that hit the distinct ceiling (not a category)
        cap = _max_distinct()
        members = self._input_members(input)          # indexed read (keys); the walk below is O(chunk)
        n_total = len(members)
        if off < done:                                # this slice already folded — resumable skip
            return {"labo": labo, "input": input, "done": done, "total": n_total, "skipped": True}
        for mk in _pace(members[off:off + ch]):
            sm = (self.cortex.get_meta(mk) or {}).get("source_metadata") or {}
            for f in fields:
                v = str(sm.get(f, "?"))
                d = counts.setdefault(f, {})
                if v in d:
                    d[v] += 1
                elif len(d) < cap:                    # bounded accumulator height (memory)
                    d[v] = 1
                else:
                    over[f] = True                    # too many distinct → date/serial/id, not a category
        new_done = min(off + ch, n_total)
        if not acc_key:
            self._mk(acc_alias, "[%s] precompute accumulator" % acc_alias,
                     {"concept": "analysis_accum", "input": input, "fields": fields,
                      "counts": counts, "over": over, "done": new_done, "total": n_total})
        else:
            self._set_meta(acc_key, "counts", counts)
            self._set_meta(acc_key, "over", over)
            self._set_meta(acc_key, "done", new_done)
            self._set_meta(acc_key, "total", n_total)
        return {"labo": labo, "input": input, "done": new_done, "total": n_total,
                "processed": max(0, new_done - off)}

    def op_count_finalize(self, labo: str, input: str, fields=None) -> Dict[str, Any]:
        """Persist each field's count run from the completed accumulator (no walk here), prepare the
        cluster (groupby, derived from the tally) + scatter (one bounded pass) so every viewer view is
        ready in advance, then drop the accumulator atom. Skips projections already persisted (idempotent)."""
        nm = labo.replace("labo:", "")
        lid = "labo:%s" % slug(nm)
        if not self._key(lid):
            raise ValueError("unknown labo '%s'" % labo)
        if isinstance(fields, str):
            fields = [f.strip() for f in fields.split(",") if f.strip()]
        fields = list(fields or [])
        acc_alias = self._accum_alias(nm, input, fields)
        acc_key = self._key(acc_alias)
        acc = (self.cortex.get_meta(acc_key) or {}) if acc_key else {}
        counts = acc.get("counts") or {}
        over = acc.get("over") or {}                   # fields that hit the distinct ceiling
        n_total = int(acc.get("total") or acc.get("done") or 0)
        topn = _analysis_topn()
        made = []
        for f in fields:
            if self._persisted_projection(labo, input, "count:%s" % f, "") is not None:
                continue
            # classify: a category gets a full distribution; a date/serial/id gets a light marker (so the
            # precompute converges) and is excluded from the cluster/scatter views + the field menus.
            projection = self._count_projection(f, counts.get(f) or {}, bool(over.get(f)), n_total, topn)
            self._persist_projection(nm, lid, input, "count:%s" % f, "", projection, [])
            made.append(f)
        # cluster (groupby, from the full accumulator tally) + scatter (one bounded pass) for the CATEGORY
        # fields only — prepared here so the viewer never asks and no operator step exists.
        cat_fields = self._categorical_fields(lid, input, fields)
        cat_counts = {f: counts.get(f) or {} for f in cat_fields}
        derived = self._precompute_derived(nm, lid, input, cat_fields, cat_counts, n_total)
        if acc_key and self._nuc:                     # drop the accumulator
            core = self._nuc.core
            try:
                for coll in list(core.get_collections_for_key(acc_key) or []):
                    core.remove_from_collection(coll, acc_key)
                for al in list(core.get_aliases_by_key(acc_key) or []):
                    core.delete_alias(al)
                core.drop_chunk(acc_key)
            except Exception:
                pass
        return {"labo": labo, "input": input, "computed": len(made), "fields": made,
                "groupby": derived["groupby"], "scatter": derived["scatter"], "input_size": n_total}

    def op_reset(self, labo: str) -> Dict[str, Any]:
        """[analysis.reset] Drop a Labo's persisted analysis runs + result Sets so a following
        `analysis.precompute` rebuilds them UNIFORMLY under the current settings (e.g. after a
        pair-cap / point-cap change, to replace a mix of old and new scatter atoms). Fenced to this
        Labo's own `analysis:run:<nm>` / `analysis:set:<nm>` registries — it never touches the source
        pool or any other Labo. Admin/librarian only (a nucleus write). Recompute-free runs are
        re-fetched forever otherwise, so this is the sanctioned way to force a clean recompute."""
        return self.reset_labo(labo)

    def reset_labo(self, labo: str) -> Dict[str, Any]:
        """INTERNAL helper (also the public op_reset): drop a Labo's persisted analysis runs + result
        Sets, so that after its source pool is RE-IMPORTED with corrected data OR a settings change the
        auto-precompute recomputes (the runs are recompute-free/idempotent, so a stale run would
        otherwise be re-fetched forever). Fenced to this Labo's `analysis:run:<nm>` /
        `analysis:set:<nm>` registries; nothing else."""
        nuc = self._nuc
        core = nuc.core if nuc else None
        if not core:
            return {"labo": labo, "note": "no nucleus"}
        nm = labo.replace("labo:", "")
        dropped = {"runs": 0, "sets": 0}

        def _drop(key):
            for coll in list(core.get_collections_for_key(key) or []):
                try:
                    core.remove_from_collection(coll, key)
                except Exception:
                    pass
            for al in list(core.get_aliases_by_key(key) or []):
                try:
                    core.delete_alias(al)
                except Exception:
                    pass
            try:
                core.drop_chunk(key)
            except Exception:
                pass

        for k in list(self._members(f"analysis:set:{slug(nm)}")):
            try:
                core.clear_collection("%s:members" % (self._alias(k) or ""))
            except Exception:
                pass
            _drop(k); dropped["sets"] += 1
        for k in list(self._members(f"analysis:run:{slug(nm)}")):
            _drop(k); dropped["runs"] += 1
        try:
            core.clear_collection(f"analysis:run:{slug(nm)}")
            core.clear_collection(f"analysis:set:{slug(nm)}")
        except Exception:
            pass
        logger.info("[analysis.reset_labo] %s → dropped %s", labo, dropped)
        return {"labo": labo, "dropped": dropped}

    def op_view(self, labo: str = "", input: str = "", plugin: str = "", params: str = "") -> Dict[str, Any]:
        """[analysis.view] READ — RE-FETCH ONLY. Return a PREVIOUSLY-PERSISTED projection for exactly
        this (input, plugin, params); NEVER compute one in the request.

        ⚠️ ABSOLUTE PRINCIPLE (no real-time Atom sweep): a projection over a pool's members is a
        per-member `get_meta` walk — on a 26k-row pool that is a read-storm that starves the cell's
        liveness. That cost is FORBIDDEN on the interactive/read path. It is paid AHEAD OF TIME, in a
        Harmonia BATCH job (`analysis.precompute` → `analysis.run` steps at background priority), which
        persists the projection. The pool is FROZEN (immutable) and a run is immutable, so the persisted
        result is always valid — the "re-fetched, never recomputed" contract. `analysis.view` only reads
        that result (a cheap scan of the few run atoms, not the pool). A miss returns `pending`, never a
        scan — an operator precomputes it and every guest then re-fetches the exact chart for free."""
        # Required args must be present — a missing one is a caller error, not a silent empty result.
        # (A bare `analysis.view labo=… plugin=…` without input= previously returned a confusing None.)
        missing = [n for n, v in (("labo", labo), ("input", input), ("plugin", plugin)) if not (v or "").strip()]
        if missing:
            raise ValueError("analysis.view requires %s — e.g. analysis.view labo=<labo> "
                             "input=<pool> plugin=<count:F|scatter:Fx,Fy|groupby:F>"
                             % ", ".join("%s=" % m for m in missing))
        hit = self._persisted_projection(labo, input, plugin, params)
        if hit is None and plugin.startswith("scatter:"):
            # Scatter is prepared for ONE field ordering per pair (fx,fy from combinations); the viewer
            # may pick the two axes in the OTHER order. Re-fetch the stored pair and TRANSPOSE it so the
            # axes match what was asked — no recompute, still a re-fetch of the persisted result.
            spec = plugin.split(":", 1)[1]
            a, _, b = spec.partition(",")
            a, b = a.strip(), b.strip()
            if a and b and a != b:
                alt = self._persisted_projection(labo, input, "scatter:%s,%s" % (b, a), params)
                if alt is not None:
                    projection, run_id, cronon = alt
                    projection = self._transpose_scatter(projection)
                    return {"labo": labo, "plugin": plugin, "input": input,
                            "input_size": projection.get("input_size") or projection.get("n"),
                            "projection": projection, "cronon": cronon, "persisted": True, "run": run_id}
        if hit is not None:
            projection, run_id, cronon = hit
            members_n = projection.get("input_size")
            if members_n is None:
                members_n = projection.get("n")
            return {"labo": labo, "plugin": plugin, "input": input, "input_size": members_n,
                    "projection": projection, "cronon": cronon, "persisted": True, "run": run_id}
        return {"labo": labo, "plugin": plugin, "input": input, "projection": None,
                "persisted": False, "pending": True,
                "note": "not computed yet — a projection is precomputed in a Harmonia batch "
                        "(analysis.precompute), never swept in the read path. Ask an operator to "
                        "precompute this field; it then re-fetches instantly for everyone."}

    # ── run ──────────────────────────────────────────────────────────────────────
    def op_run(self, labo: str, input: str, plugin: str, params: str = "", name: str = "",
               outputs: str = "") -> Dict[str, Any]:
        """Run an analysis over an input Set and persist the provenance (input, plugin/version,
        params, cronon, outputs). Built-ins: `groupby:<field>` (one result Set per value of a
        source_metadata field — clustering AS Sets) and `count:<field>` (a distribution projection).
        Any other `plugin` records the run and adopts caller-declared `outputs` (comma-separated set
        names already produced by an external/installed plugin)."""
        nm = labo.replace("labo:", "")
        lid = f"labo:{slug(nm)}"
        if not self._key(lid):
            raise ValueError(f"unknown labo '{labo}' — labo.new it first")
        # IDEMPOTENT / recompute-free (see reset_labo): if this exact (input, plugin, params) is already
        # persisted, RE-FETCH it — never recompute. This is what lets the auto-precompute boot phase
        # RE-FETCH it — never recompute. This is what lets the auto-precompute boot phase re-submit
        # every boot with no duplicate runs and, crucially, NO repeat member sweep.
        _existing = self._persisted_projection(labo, input, plugin, params)
        if _existing is not None:
            _proj, _run_id, _cronon = _existing
            _m = self.cortex.get_meta(self._key(_run_id)) or {}
            return {"run": _run_id, "labo": self._alias(self._key(lid)), "plugin": plugin,
                    "input": input, "input_size": _m.get("input_size"),
                    "output_sets": _m.get("outputs") or [], "projection": _proj,
                    "cronon": _cronon, "reused": True,
                    "note": "already persisted — re-fetched, not recomputed (no member sweep)"}
        members = self._input_members(input)
        at = self._akasha_now()
        seq = len(self._members(f"analysis:run:{slug(nm)}")) + 1
        run_id = f"analysis:run:{slug(nm)}:{seq}"
        out_sets: List[str] = []
        # Compute the projection with the SAME pure helper analysis.view uses (one source of truth).
        projection, buckets = self._compute_projection(members, plugin, params)
        if buckets is not None:
            # groupby → ALSO materialize one result Set per value (the persisted, set-algebra face).
            # CAP the materialization: a high-cardinality field would otherwise create tens of
            # thousands of Sets (a WriteQueue flood that blocks reads). Above the cap keep the
            # projection (top-N group counts) but materialize NO Sets — a 26k-way clustering is not a
            # meaningful result set anyway.
            field = plugin.split(":", 1)[1]
            _max_sets = _groupby_max_sets()
            if len(buckets) <= _max_sets:
                for v, keys in sorted(buckets.items()):
                    out_sets.append(self._make_set(nm, f"{name or field}_{v}", keys,
                                                   {"method": plugin, "cluster_value": v, "run": run_id}))
            elif projection is not None:
                projection["sets_skipped"] = True
                projection["sets_skipped_reason"] = "%d groups > cap %d (no Set materialization)" % (
                    len(buckets), _max_sets)
        elif projection is None:
            # external/installed plugin — record provenance + adopt declared output sets
            for onm in [x.strip() for x in outputs.split(",") if x.strip()]:
                keys = self._members(self._members_set_of(onm))
                out_sets.append(self._make_set(nm, onm, keys, {"method": plugin, "run": run_id, "declared": True}))

        meta = {"concept": "analysis_run", "labo": self._alias(self._key(lid)), "input": input,
                "input_size": len(members), "plugin": plugin, "params": params, "cronon": at,
                "projection": projection, "outputs": out_sets}
        self._mk(run_id, f"[{run_id}] {plugin} over {input} (n={len(members)})", meta)
        self._link(run_id, lid, R_IN_LABO)
        self._link(run_id, self._members_set_of(input), R_INPUT)
        self._link(run_id, f"plugin:{slug(plugin)}", R_USES_PLUGIN)
        for s in out_sets:
            self._link(run_id, s, R_PRODUCES)
        self._add_to_set(f"analysis:run:{slug(nm)}", self._key(run_id))
        return {"run": run_id, "labo": self._alias(self._key(lid)), "plugin": plugin, "input": input,
                "input_size": len(members), "output_sets": out_sets, "projection": projection, "cronon": at,
                "note": "result Sets are analysis outputs, not ontological truths; overlay/switch them freely"}

    def op_runs(self, labo: str) -> Dict[str, Any]:
        """List a Labo's analysis runs with input/plugin/output provenance."""
        nm = labo.replace("labo:", "")
        out = []
        for k in self._members(f"analysis:run:{slug(nm)}"):
            m = self.cortex.get_meta(k) or {}
            # `categorical` (from the projection) lets the viewer offer only category fields — a
            # date/serial count is recorded but marked categorical:false and not shown as a summary.
            _cat = (m.get("projection") or {}).get("categorical")
            out.append({"run": self._alias(k), "plugin": m.get("plugin"), "input": m.get("input"),
                        "input_size": m.get("input_size"), "outputs": len(m.get("outputs") or []),
                        "categorical": _cat, "cronon": m.get("cronon")})
        out.sort(key=lambda r: r.get("cronon") or 0)
        return {"labo": f"labo:{slug(nm)}", "runs": out, "count": len(out)}

    def op_get(self, id: str) -> Dict[str, Any]:
        """Read one analysis run: input Set, plugin/params, output Sets, projection, cronon."""
        k = self._key(id)
        if not k:
            raise ValueError(f"unknown analysis run '{id}'")
        m = self.cortex.get_meta(k) or {}
        return {"run": self._alias(k), "labo": m.get("labo"), "input": m.get("input"),
                "input_size": m.get("input_size"), "plugin": m.get("plugin"), "params": m.get("params"),
                "projection": m.get("projection"), "outputs": m.get("outputs") or [], "cronon": m.get("cronon")}

    def op_sets(self, labo: str) -> Dict[str, Any]:
        """List a Labo's result Sets (analysis outputs) — each openable in Source/Concept/Society."""
        nm = labo.replace("labo:", "")
        out = []
        for k in self._members(f"analysis:set:{slug(nm)}"):
            m = self.cortex.get_meta(k) or {}
            out.append({"set": self._alias(k), "name": m.get("name"), "method": m.get("method"),
                        "size": m.get("size"), "cronon": m.get("cronon")})
        return {"labo": f"labo:{slug(nm)}", "sets": out, "count": len(out)}

    # ── set algebra (§3) ─────────────────────────────────────────────────────────
    def op_set(self, labo: str, op: str, a: str, b: str, name: str = "") -> Dict[str, Any]:
        """Set algebra over two Sets → a new persisted result Set. `op` ∈ union / intersect / diff.
        A Source Atom may belong to many Sets at once, so these compose freely."""
        if op not in ("union", "intersect", "diff"):
            raise ValueError("op must be union / intersect / diff")
        nm = labo.replace("labo:", "")
        A = {self._alias(k): k for k in self._input_members(a)}
        B = {self._alias(k): k for k in self._input_members(b)}
        if op == "union":
            keys = list({**A, **B}.values())
        elif op == "intersect":
            keys = [A[x] for x in A if x in B]
        else:
            keys = [A[x] for x in A if x not in B]
        sid = self._make_set(nm, name or f"{op}_result", keys,
                             {"method": f"algebra:{op}", "operands": [a, b]})
        self._link(sid, self._members_set_of(a), R_DERIVED_FROM)
        self._link(sid, self._members_set_of(b), R_DERIVED_FROM)
        return {"set": sid, "op": op, "a": a, "b": b, "size": len(keys)}

    def op_core(self, labo: str, sets: str, name: str = "") -> Dict[str, Any]:
        """Materialize the method-invariant CORE Set (members present in ALL the given result Sets)
        and the BOUNDARY Set (members in some but not all) — so method disagreement is explicit, not
        hidden (§3.1). These are analysis results, not ontological truths."""
        nm = labo.replace("labo:", "")
        names = [x.strip() for x in sets.split(",") if x.strip()]
        if len(names) < 2:
            raise ValueError("pass sets= with at least two comma-separated result Sets")
        member_maps = [{self._alias(k): k for k in self._input_members(s)} for s in names]
        all_keys = {}
        for mm in member_maps:
            all_keys.update(mm)
        core = [all_keys[x] for x in all_keys if all(x in mm for mm in member_maps)]
        boundary = [all_keys[x] for x in all_keys if not all(x in mm for mm in member_maps)]
        core_id = self._make_set(nm, (name or "core") + "_core", core,
                                 {"method": "method_invariant_core", "over": names})
        bnd_id = self._make_set(nm, (name or "core") + "_boundary", boundary,
                                {"method": "method_sensitive_boundary", "over": names})
        for s in names:
            self._link(core_id, self._members_set_of(s), R_DERIVED_FROM)
            self._link(bnd_id, self._members_set_of(s), R_DERIVED_FROM)
        return {"core_set": core_id, "boundary_set": bnd_id, "over": names,
                "core_size": len(core), "boundary_size": len(boundary),
                "note": "stable-across-methods vs method-sensitive — results, not truths"}

    def op_overlay(self, a: str, b: str) -> Dict[str, Any]:
        """Compare two result Sets: their overlap + Jaccard similarity — makes disagreement between
        methods visible rather than hiding it (§3.1)."""
        A = {self._alias(k) for k in self._input_members(a)}
        B = {self._alias(k) for k in self._input_members(b)}
        inter = A & B
        union = A | B
        return {"a": a, "b": b, "a_size": len(A), "b_size": len(B), "shared": len(inter),
                "only_a": len(A - B), "only_b": len(B - A),
                "jaccard": round(len(inter) / len(union), 3) if union else 0.0,
                "note": "numerical similarity ≠ semantic agreement; label semantics via labo.interpret"}
