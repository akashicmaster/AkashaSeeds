"""
Concept Laboratory Projection Model v0.1 — the READ-ONLY GUI projection of a clab research graph.

Canonical research state always lives in Akasha (the `clab.*` operands + relations + the chronon
network). This module DERIVES, deterministically, a GUI-friendly view of it — the shape Archives
(SVG / Plotly / narrative) can render — and NEVER writes back (invariant V1). It re-interprets
nothing: a node is `kind=key_proof` *because* it is a `clab:key_proof` operand, not because the GUI
guessed it is important. "Projection decides how to see, not what is true."

Path:  Akasha canonical graph → projection model (this) → SVG / Plotly / narrative.
The same canonical graph yields several projections (mode = trajectory | family | evidence | time).

The invariants held here (spec §17):
  V1 never writes canonical state (pure read — this module only reads).
  V2 competing conclusions all remain visible/queryable (every conclusion is projected).
  V3 rejected paths hidden by default but recoverable (include_rejected surfaces them).
  V4 PERFECTIVE vs PROSPECTIVE never visually indistinct (aspect is carried on every object).
  V5 chronon:next and chronon:mutates are DIFFERENT projected relations (pv:next vs pv:mutates).
  V6 Family is a semantic REGION, not just another node (families → `regions`, not `nodes`).
  V7 every projected object keeps `source_atom` → GUI → CLI → clab.trace is reversible.

The projection is computed fresh on every call (it is derived + regenerable by definition — §16),
so there is no cache to invalidate: canonical change → next clab.project rebuilds it.
"""
import time
from typing import Any, Callable, Dict, List, Optional

PROJECTION_VERSION = "0.1"

# clab_kind → (pv primitive kind, visual shape hint §9). Named primitives get their own kind;
# everything else is a generic conceptual node (still projected, still reversible — V2/V3).
_KIND_MAP = {
    "master_thesis": ("master_thesis", "banner"),
    "hypothesis":    ("hypothesis", "start_marker"),
    "family":        ("family", "region"),
    "cluster":       ("cluster", "box"),
    "concept":       ("concept", "node"),
    "key_proof":     ("key_proof", "emphasized_cluster_marker"),
    "turning_point": ("turning_point", "trajectory_bend_marker"),
    "conclusion":    ("conclusion", "terminal_marker"),
    "tension":       ("tension", "unresolved_connector"),
    "source":        ("source", "provenance_leaf"),
}
_GENERIC_SHAPE = "node"
_STAGE_DEPTH = {"initial": 0, "intermediate": 1, "destination": 2}
_MODES = ("trajectory", "family", "evidence", "time")


def _lane_name(i: int) -> str:
    """Stable lane label for the i-th (deterministically ordered) trajectory."""
    return f"trajectory_{chr(ord('A') + i)}" if i < 26 else f"trajectory_{i}"


class ClabProjectionBuilder:
    """Builds the projection JSON for one clab nebula (research field). Pure read; takes a cortex
    (read surface: get_meta / get_chunk / get_adjacent_links / get_collection_members) plus an
    alias resolver, and — optionally — a group engine to fold in the chronon timeline."""

    def __init__(self, cortex, alias_of: Callable[[str], str], now_ts: float,
                 group_engine=None):
        self.cortex = cortex
        self._alias_of = alias_of
        self._now = now_ts
        self.ge = group_engine

    # ── read helpers ───────────────────────────────────────────────────────────────
    def _meta(self, key: str) -> Dict[str, Any]:
        return self.cortex.get_meta(key) or {}

    def _head(self, key: str) -> str:
        return (self.cortex.get_chunk(key) or "").replace("\n", " ").strip()

    def _adj(self, key: str, rel: str = None) -> List[Dict[str, Any]]:
        """Normalize both link surfaces: the composite engine returns [dst, rel] pairs; a raw
        backend returns {'dst':…, 'rel':…} dicts."""
        try:
            raw = self.cortex.get_adjacent_links(key, rel)
        except TypeError:
            raw = self.cortex.get_adjacent_links(key)
        out = []
        for item in (raw or []):
            if isinstance(item, dict):
                d, r = item.get("dst"), item.get("rel")
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                d, r = item[0], item[1]
            else:
                continue
            if rel is None or r == rel:
                out.append({"dst": d, "rel": r})
        return out

    def _dsts(self, key: str, rel: str) -> List[str]:
        return [l.get("dst") for l in self._adj(key, rel) if l.get("dst")]

    # ── the build ────────────────────────────────────────────────────────────────
    def build(self, root_key: str, members: List[str], title: str, mode: str,
              at: str = "", include_rejected: bool = False,
              source_society: str = "", source_workflow: str = "",
              source_chronon_root: str = "", source_frontier: List[str] = None) -> Dict[str, Any]:
        mode = (mode or "trajectory").strip().lower()
        if mode not in _MODES:
            mode = "trajectory"

        # 1) classify operands → projected objects (nodes) + regions (families), V6/V7.
        nodes: List[Dict[str, Any]] = []
        regions: List[Dict[str, Any]] = []
        by_source: Dict[str, Dict[str, Any]] = {}     # source_atom → projected object
        families: Dict[str, Dict[str, Any]] = {}
        for key in members:
            m = self._meta(key)
            kind = m.get("clab_kind", "")
            if kind == "nebula" or not kind:
                continue
            status = m.get("status", "")
            if not include_rejected and status == "rejected":
                continue                                  # V3: hidden by default, recoverable
            pv_kind, shape = _KIND_MAP.get(kind, ("concept", _GENERIC_SHAPE))
            obj = self._project_object(key, m, pv_kind, shape)
            by_source[key] = obj
            if pv_kind == "family":
                regions.append(obj)
                families[key] = obj
            else:
                nodes.append(obj)

        # 2) relations → typed projected edges (V5: next ≠ mutates; canonical never rewritten).
        edges: List[Dict[str, Any]] = []
        self._project_membership(by_source, families, nodes, edges)   # pv:contains (+ external concepts)
        self._project_trajectory_next(families, edges)                # pv:trajectory_next
        self._project_support_challenge(by_source, edges)             # pv:supports / pv:challenges
        self._project_leads_to_conclusion(by_source, edges)           # pv:leads_to_conclusion (derived)
        if mode == "evidence":
            self._project_provenance(by_source, nodes, edges)         # pv:derived_from + sources

        # 3) trajectories (competing theories as family_next chains).
        trajectories = self._build_trajectories(families, by_source)

        # 4) timepoints + semantic-progression depth (x-axis), chronon topology when bound (V4/V5).
        timepoints, depth_of = self._build_timepoints(families, by_source, source_chronon_root)

        # 5) layout hints (semantic placement, NOT pixels §8): lane per trajectory, depth = x.
        layout_hints = self._build_layout(families, by_source, trajectories, depth_of)

        proj_id = f"projection:clab:{root_key[:12]}"
        # §16 invalidate trigger: bake the SOURCE FRONTIER (the society's society:now at generation
        # time) into meta. A consumer detects "canonical graph changed" by comparing this against the
        # society's CURRENT frontier (society.now) — minimal + semantically exact. generated_at
        # (wall-clock) is DISPLAY-ONLY and must not be used to decide staleness.
        meta = {"projection_type": "clab", "projection_version": PROJECTION_VERSION,
                "title": title, "mode": mode, "generated_at": self._now,
                "source_society": source_society, "source_workflow": source_workflow,
                "source_chronon_root": source_chronon_root,
                "source_frontier": sorted(source_frontier or []), "at": at,
                "include_rejected": include_rejected}
        # mode-specific emphasis (all objects always retained — V2; mode changes what leads).
        return {"projection": proj_id, "mode": mode, "meta": meta,
                "nodes": nodes, "regions": regions, "edges": edges,
                "timepoints": timepoints, "trajectories": trajectories,
                "layout_hints": layout_hints}

    # ── object projection ────────────────────────────────────────────────────────
    def _project_object(self, key: str, m: Dict[str, Any], pv_kind: str, shape: str) -> Dict[str, Any]:
        alias = self._alias_of(key)
        obj = {"id": f"pv:{pv_kind}:{key[:8]}", "kind": pv_kind, "shape": shape,
               "source_atom": alias,                       # V7 — GUI → CLI → clab.trace reversible
               "label": self._label(key, m, pv_kind),
               "status": m.get("status", ""),
               "aspect": m.get("aspect", "perfective"),    # V4 — always carried
               "agent": m.get("agent", "") or m.get("created_by", ""),
               "chronon": m.get("chronon", "")}
        if pv_kind == "family":
            obj.update(stage=m.get("stage", "intermediate"), contains=[])
        elif pv_kind == "conclusion":
            obj.update(polarity=m.get("judgement", "undetermined"),
                       lifecycle=m.get("status", "proposed"), rationale=m.get("rationale", ""),
                       hypothesis=self._first_alias(self._dsts(key, "clab:concludes_about")))
        elif pv_kind == "key_proof":
            obj.update(rationale=m.get("rationale", ""),
                       cluster=self._first_alias(self._dsts(key, "clab:key_proof")),
                       hypothesis=self._first_alias(self._dsts(key, "clab:decisively_supports")))
        elif pv_kind == "turning_point":
            obj.update(rationale=m.get("rationale", ""),
                       cluster=self._first_alias(self._dsts(key, "clab:turning_point")),
                       hypothesis=self._first_alias(self._dsts(key, "clab:challenges")))
        elif pv_kind == "tension":
            obj.update(kind_of_tension=m.get("tension_kind", m.get("kind", "")))
        elif pv_kind == "source":
            obj.update(title=m.get("title", ""), authors=m.get("authors", ""),
                       year=m.get("year", ""), doi=m.get("doi", ""), url=m.get("url", ""))
        elif pv_kind == "concept":
            obj.update(concept_name=m.get("concept_name", ""), maturity=m.get("maturity", ""))
        return obj

    def _label(self, key: str, m: Dict[str, Any], pv_kind: str) -> str:
        for f in ("concept_name", "title", "label"):
            if m.get(f):
                return str(m[f])[:80]
        head = self._head(key)
        return (head[:80] or self._alias_of(key))

    def _first_alias(self, keys: List[str]) -> str:
        return self._alias_of(keys[0]) if keys else ""

    # ── edge projections ─────────────────────────────────────────────────────────
    def _ensure_node(self, key: str, by_source, nodes) -> Dict[str, Any]:
        """Return the projected object for `key`, projecting it on demand as a pv:concept if it is
        an external domain atom (a corpus concept a family/cluster references) not already a clab
        operand. Keeps the region populated with the concept nodes the GUI draws inside it."""
        if key in by_source:
            return by_source[key]
        m = self._meta(key)
        pv_kind, shape = _KIND_MAP.get(m.get("clab_kind", ""), ("concept", _GENERIC_SHAPE))
        obj = self._project_object(key, m, pv_kind, shape)
        by_source[key] = obj
        nodes.append(obj)
        return obj

    def _incoming(self, key: str, rel: str) -> List[str]:
        try:
            raw = self.cortex.get_incoming_links(key, rel)
        except Exception:
            return []
        out = []
        for item in (raw or []):
            if isinstance(item, dict):
                out.append(item.get("src"))
            elif isinstance(item, (list, tuple)) and len(item) >= 1:
                out.append(item[0])
        return [s for s in out if s]

    def _project_membership(self, by_source, families, nodes, edges) -> None:
        # a family REGION contains its members (V6: region → member). Members are found by INCOMING
        # belongs_to_family (member → family); external domain concepts are projected on demand.
        for fk, fobj in families.items():
            for member in self._incoming(fk, "clab:belongs_to_family"):
                mobj = self._ensure_node(member, by_source, nodes)
                if mobj["id"] not in fobj.setdefault("contains", []):
                    fobj["contains"].append(mobj["id"])
                    edges.append({"rel": "pv:contains", "src": fobj["id"], "dst": mobj["id"]})
        # a cluster contains its references (outgoing clab:contains)
        for key, obj in list(by_source.items()):
            if obj["kind"] != "cluster":
                continue
            for ref in self._dsts(key, "clab:contains"):
                robj = self._ensure_node(ref, by_source, nodes)
                edges.append({"rel": "pv:contains", "src": obj["id"], "dst": robj["id"]})

    def _project_trajectory_next(self, families, edges) -> None:
        for fk, fobj in families.items():
            for nxt in self._dsts(fk, "clab:family_next"):
                if nxt in families:
                    edges.append({"rel": "pv:trajectory_next", "src": fobj["id"], "dst": families[nxt]["id"]})

    def _project_support_challenge(self, by_source, edges) -> None:
        for key, obj in by_source.items():
            for rel, pv in (("clab:supports", "pv:supports"), ("clab:challenges", "pv:challenges")):
                for dst in self._dsts(key, rel):
                    if dst in by_source:
                        edges.append({"rel": pv, "src": obj["id"], "dst": by_source[dst]["id"]})

    def _project_leads_to_conclusion(self, by_source, edges) -> None:
        """Derived GUI edge (§5.6): key_proof / turning_point → the conclusion about the same
        hypothesis. Never written back to the canonical graph (V1)."""
        # conclusion → its hypothesis
        concl_by_hyp: Dict[str, List[str]] = {}
        for key, obj in by_source.items():
            if obj["kind"] == "conclusion":
                for h in self._dsts(key, "clab:concludes_about"):
                    concl_by_hyp.setdefault(h, []).append(obj["id"])
        for key, obj in by_source.items():
            if obj["kind"] not in ("key_proof", "turning_point"):
                continue
            rel = "clab:decisively_supports" if obj["kind"] == "key_proof" else "clab:challenges"
            for h in self._dsts(key, rel):
                for cid in concl_by_hyp.get(h, []):
                    edges.append({"rel": "pv:leads_to_conclusion", "src": obj["id"], "dst": cid})

    def _project_provenance(self, by_source, nodes, edges) -> None:
        """Evidence view (§5.7): follow the provenance chain operand —clab:sourced_by→ citation
        —clab:cites→ Source, project the pv:source leaf, and emit a pv:derived_from edge (the
        citation carries the locator/role). Canonical graph is never rewritten (V1)."""
        seen_src = {o["source_atom"] for o in by_source.values()}
        projected: Dict[str, Dict[str, Any]] = {}         # source key → pv object
        for key, obj in list(by_source.items()):
            for citation in self._dsts(key, "clab:sourced_by"):
                cm = self._meta(citation)
                for src in self._dsts(citation, "clab:cites"):
                    sm = self._meta(src)
                    if sm.get("clab_kind") != "source":
                        continue
                    sobj = projected.get(src)
                    if sobj is None and self._alias_of(src) not in seen_src:
                        sobj = self._project_object(src, sm, "source", "provenance_leaf")
                        nodes.append(sobj)
                        projected[src] = sobj
                        by_source[src] = sobj
                        seen_src.add(sobj["source_atom"])
                    elif sobj is None:
                        sobj = by_source.get(src)
                    if sobj:
                        edges.append({"rel": "pv:derived_from", "src": obj["id"], "dst": sobj["id"],
                                      "role": cm.get("role", ""), "locator": cm.get("locator", "")})

    # ── trajectories, timepoints, layout ────────────────────────────────────────
    def _build_trajectories(self, families, by_source) -> List[Dict[str, Any]]:
        """Competing theories as maximal family_next chains (§6). A trajectory is a DAG collapsed to
        a path for display; several trajectories may share a family."""
        incoming = {fk: 0 for fk in families}
        for fk in families:
            for nxt in self._dsts(fk, "clab:family_next"):
                if nxt in families:
                    incoming[nxt] = incoming.get(nxt, 0) + 1
        roots = [fk for fk in families if incoming.get(fk, 0) == 0] or list(families)

        # Enumerate EVERY maximal root→leaf path over family_next — competing theories often SHARE
        # the initial family (one root, several successors), so a first-successor walk would collapse
        # them into one. Each distinct path is a trajectory; shared families are allowed (§6).
        paths: List[List[str]] = []

        def _dfs(cur, path, seen):
            nxts = sorted(n for n in self._dsts(cur, "clab:family_next") if n in families and n not in seen)
            if not nxts:
                paths.append(list(path))
                return
            for n in nxts:
                _dfs(n, path + [n], seen | {n})

        for root in roots:
            _dfs(root, [root], {root})

        # §8 lane stability: order trajectories DETERMINISTICALLY by a stable key (the initial
        # family's source_atom / branch_root_chronon, then the full path), NOT by discovery order, so
        # regeneration never reshuffles lanes (critical for the regenerate→refresh experiment loop).
        def _path_key(path):
            fam = families[path[0]]
            return (fam.get("chronon") or fam.get("source_atom") or path[0],
                    tuple(families[k].get("source_atom", k) for k in path))
        paths = sorted(paths, key=_path_key)

        trajectories = []
        for i, path in enumerate(paths):
            root, dest = path[0], path[-1]
            trajectories.append({
                "id": f"pv:trajectory:{i+1}",
                "lane": _lane_name(i),
                "initial_family": families[root]["id"],
                "branch_root": families[root].get("source_atom", ""),   # the stable lane key
                "branch_root_chronon": families[root].get("chronon", ""),
                "intermediate_families": [families[k]["id"] for k in path[1:-1]],
                "destination_family": families[dest]["id"],
                "frontier_chronon": families[dest].get("chronon", ""),
                "conclusion": self._conclusion_for(dest, families, by_source),
                "status": "open",
                "families": [families[k]["id"] for k in path]})
        return trajectories

    def _conclusion_for(self, dest_family: str, families, by_source) -> str:
        """The conclusion that terminates a trajectory: one whose `concludes_about` target is a
        member of the destination family (the case that family is about). Returns its projected id,
        else ''."""
        members = set(self._incoming(dest_family, "clab:belongs_to_family"))
        for key, obj in by_source.items():
            if obj["kind"] == "conclusion":
                for h in self._dsts(key, "clab:concludes_about"):
                    if h in members:
                        return obj["id"]
        return ""

    def _build_timepoints(self, families, by_source, chronon_root):
        """x = semantic progression depth (§7): family_next topological depth; members inherit
        their family's depth; hypotheses/master_thesis at 0; conclusions one past the destination.
        (When a real chronon root is supplied, its chronon:next depth would drive this instead.)"""
        depth: Dict[str, int] = {}

        def fam_depth(fk, guard=None):
            if fk in depth:
                return depth[fk]
            guard = guard or set()
            if fk in guard:
                return 0
            guard.add(fk)
            preds = [pk for pk in families if fk in self._dsts(pk, "clab:family_next")]
            d = 0 if not preds else 1 + max(fam_depth(p, guard) for p in preds)
            depth[fk] = d
            return d

        for fk in families:
            fam_depth(fk)
        maxd = max(depth.values()) if depth else 0
        depth_of: Dict[str, int] = {}
        for key, obj in by_source.items():
            k = obj["kind"]
            if k == "family":
                depth_of[key] = depth.get(key, 0)
            elif k in ("hypothesis", "master_thesis"):
                depth_of[key] = 0
            elif k == "conclusion":
                depth_of[key] = maxd + 1
            else:
                fams = [f for f in self._dsts(key, "clab:belongs_to_family") if f in families]
                depth_of[key] = depth.get(fams[0], 0) if fams else 0
        # synthetic timepoints per depth level (the x-axis); aspect defaults perfective (a nebula
        # research state exists), preserved so PROSPECTIVE forks stay distinct (V4).
        levels = sorted(set(depth_of.values()) | {0})
        timepoints = [{"id": f"pv:timepoint:d{d}", "depth": d, "aspect": "perfective",
                       "label": f"progression {d}", "chronon": ""} for d in levels]
        return timepoints, depth_of

    def _build_layout(self, families, by_source, trajectories, depth_of) -> Dict[str, Dict[str, Any]]:
        """Semantic placement hints (§8) — lane (per trajectory), depth (x), rank (y within lane),
        group. Pixels are the frontend's job."""
        # lanes come straight from each trajectory's own deterministic lane (derived from its branch
        # root, §8) — never re-derived by discovery order here.
        pv_to_key = {obj["id"]: key for key, obj in by_source.items()}
        lane_of: Dict[str, str] = {}
        for traj in trajectories:
            for fam_pv in traj["families"]:
                key = pv_to_key.get(fam_pv)
                if key is not None:
                    lane_of[key] = traj["lane"]
        hints: Dict[str, Dict[str, Any]] = {}
        rank_at: Dict[tuple, int] = {}
        for key, obj in by_source.items():
            d = depth_of.get(key, 0)
            # a member inherits its family's lane
            lane = lane_of.get(key)
            if lane is None:
                fams = [f for f in self._dsts(key, "clab:belongs_to_family") if f in families]
                lane = lane_of.get(fams[0], "main") if fams else "main"
            rk = rank_at.get((lane, d), 0)
            rank_at[(lane, d)] = rk + 1
            hints[obj["id"]] = {"lane": lane, "depth": d, "rank": rk, "group": obj["kind"]}
        return hints
