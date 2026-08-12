"""
Concept Laboratory — Rubik Projection Model v0.1 (read-only, PRECOMPUTED spatial projection).

"A theory can be treated as a path through theoretical families; the Rubik Projection shows how those
families TRANSFORM while the path is being constructed." Where the Trajectory view answers *where did
the research go?*, the Rubik view answers *how did its conceptual structure change?*

Architectural boundary (same as Semantic Cosmos): **Akasha computes everything spatial** — which
families participate, their transformation deltas, page coordinates, page depth/orientation, per-page
concept coordinates, and visual classification. Plotly/JS receives the finished projection and only
renders / pans / zooms / selects / animates. **No semantic inference or graph layout runs in JS.**

The projection NEVER creates or modifies research meaning (canonical = clab + the chronon network);
it is derived + regenerable, and carries no canonical state.

Three axes are kept SEPARATE (do not encode time as z):
  • (x, y) — semantic position of a family in the projected plane.
  • z      — transformation depth (separation between family states; family_next depth). NOT time.
  • t      — Akasha-Time (research progression / chronon topology), independent of z.

Objects (spec §5–§8):
  • pv:page:<id>       — one per clab:family (a rectangular plane holding its concepts).
  • pv:node:<id>       — a member concept/cluster, positioned PAGE-LOCALLY in normalized (u,v).
  • pv:transform:<id>  — the transformation between two pages, carrying an ALREADY-COMPUTED visual
                         delta (added / removed / retained / changed) so JS only animates the result.
"""
import hashlib
import math
from typing import Any, Callable, Dict, List, Optional

RUBIK_VERSION = "0.1"

# page geometry + cabinet-projection depth offsets (per unit of z) — the pseudo-3D recede.
_PAGE_W = 220.0
_PAGE_H = 300.0
_LANE_GAP = 320.0        # horizontal gap between competing trajectories (semantic x)
_DEPTH_DX = 74.0         # screen shift right per depth unit
_DEPTH_DY = 96.0         # screen shift up per depth unit

# transformation kinds derived from the member-set delta (spec §7 minimal set).
_KIND_INTRODUCE = "introduce"
_KIND_REMOVE = "remove"
_KIND_REDEFINE = "redefine"
_KIND_BRIDGE = "bridge"
_KIND_OTHER = "other"


class RubikProjectionBuilder:
    """Builds the Rubik payload for one clab field (optionally one trajectory). Pure read."""

    def __init__(self, cortex, alias_of: Callable[[str], str], now_ts: float):
        self.cortex = cortex
        self._alias_of = alias_of
        self._now = now_ts

    # ── read helpers (normalize the composite [dst,rel] vs backend dict surfaces) ──
    def _meta(self, key: str) -> Dict[str, Any]:
        return self.cortex.get_meta(key) or {}

    def _content(self, key: str) -> str:
        return (self.cortex.get_chunk(key) or "").replace("\n", " ").strip()

    def _adj(self, key: str, rel: str = None) -> List[Dict[str, Any]]:
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
        return [l["dst"] for l in self._adj(key, rel) if l.get("dst")]

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

    def _label(self, key: str) -> str:
        m = self._meta(key)
        for f in ("concept_name", "title", "clab_name"):
            if m.get(f):
                return str(m[f])[:80]
        return (self._content(key)[:80] or self._alias_of(key))

    # ── the build ────────────────────────────────────────────────────────────────
    def build(self, root_key: str, members: List[str], restrict_families: Optional[List[str]],
              title: str, society: str = "", workflow: str = "concept-labo") -> Dict[str, Any]:
        # 1) which families participate.
        families = []
        for key in members:
            m = self._meta(key)
            if m.get("clab_kind") == "family":
                if restrict_families is None or key in restrict_families:
                    families.append(key)
        fam_set = set(families)

        # 2) transformation depth = family_next topological depth (NOT time).
        depth = self._depths(families, fam_set)

        # 3) trajectory membership (which trajectories cross each family) + lanes for x.
        traj_of = self._trajectory_membership(families, fam_set)
        lane_index = self._lane_index(families, traj_of)

        # 4) members of each family (external domain concepts, page-local).
        fam_members = {fk: self._family_members(fk) for fk in families}

        # 5) pages + nodes.
        pages: List[Dict[str, Any]] = []
        nodes: List[Dict[str, Any]] = []
        page_id_of: Dict[str, str] = {}
        node_id_of: Dict[tuple, str] = {}          # (page_id, atom_key) → node id
        for fk in families:
            m = self._meta(fk)
            d = depth.get(fk, 0)
            lane = lane_index.get(fk, 0)
            page = self._page(fk, m, d, lane, traj_of.get(fk, []))
            pages.append(page)
            page_id_of[fk] = page["id"]
            for node in self._page_nodes(page["id"], fam_members[fk]):
                nodes.append(node)
                node_id_of[(page["id"], node["source_key"])] = node["id"]

        # draw order: far (high z) first so near pages overlay (spec §9).
        order = sorted(pages, key=lambda p: (-p["z"], p["x"]))
        for i, p in enumerate(order):
            p["draw_order"] = i

        # 6) transforms between family_next-adjacent pages, with precomputed deltas (§8).
        transforms = self._transforms(families, fam_set, fam_members, page_id_of, node_id_of, depth)

        # strip internal keys the payload doesn't need.
        for n in nodes:
            n.pop("source_key", None)

        proj_id = f"projection:clab_rubik:{root_key[:12]}"
        return {
            "projection": proj_id, "version": RUBIK_VERSION,
            "meta": {"type": "projection:clab_rubik", "version": RUBIK_VERSION,
                     "society": society, "workflow": workflow, "source": self._alias_of(root_key),
                     "title": title, "generated": self._now, "read_only": True,
                     "trajectory_filter": (restrict_families is not None)},
            "pages": pages, "nodes": nodes, "transforms": transforms,
        }

    # ── families / depth / trajectories ────────────────────────────────────────
    def _depths(self, families, fam_set) -> Dict[str, int]:
        depth: Dict[str, int] = {}

        def d_of(fk, guard=None):
            if fk in depth:
                return depth[fk]
            guard = guard or set()
            if fk in guard:
                return 0
            guard.add(fk)
            preds = [pk for pk in fam_set if fk in self._dsts(pk, "clab:family_next")]
            val = 0 if not preds else 1 + max(d_of(p, guard) for p in preds)
            depth[fk] = val
            return val

        for fk in families:
            d_of(fk)
        return depth

    def _trajectory_membership(self, families, fam_set) -> Dict[str, List[str]]:
        """Which trajectories cross each family — from explicit clab:theory contains, else the
        family_next chain the family sits on."""
        out: Dict[str, List[str]] = {fk: [] for fk in families}
        # explicit theories (clab.theory.new/path) that contain these families
        theories = set()
        for fk in families:
            for th in self._incoming(fk, "clab:contains"):
                if self._meta(th).get("clab_kind") == "theory":
                    theories.add(th)
        for th in theories:
            tid = self._alias_of(th)
            for fk in self._dsts(th, "clab:contains"):
                if fk in out:
                    out[fk].append(tid)
        return out

    def _lane_index(self, families, traj_of) -> Dict[str, int]:
        """Assign a stable lane per family for the semantic x — by its first trajectory (or 0)."""
        lanes: Dict[str, int] = {}
        order = sorted({t for ts in traj_of.values() for t in ts})
        lane_of_traj = {t: i for i, t in enumerate(order)}
        for fk in families:
            ts = traj_of.get(fk, [])
            lanes[fk] = lane_of_traj.get(ts[0], 0) if ts else 0
        return lanes

    def _family_members(self, fk: str) -> List[str]:
        """The concepts/clusters that belong to a family (incoming clab:belongs_to_family)."""
        return sorted(set(self._incoming(fk, "clab:belongs_to_family")), key=lambda k: self._alias_of(k))

    # ── page + node projection ─────────────────────────────────────────────────
    def _page(self, fk: str, m: Dict[str, Any], d: int, lane: int, trajectories: List[str]) -> Dict[str, Any]:
        # (x,y) = semantic position; z = transformation depth (kept separate, spec §3).
        x = lane * _LANE_GAP
        y = 0.0
        z = float(d)
        # cabinet-projected corners so Plotly gets DRAWABLE coordinates (spec §9).
        ox, oy = z * _DEPTH_DX, z * _DEPTH_DY
        corners = [[x + ox, y - oy], [x + _PAGE_W + ox, y - oy],
                   [x + _PAGE_W + ox, y + _PAGE_H - oy], [x + ox, y + _PAGE_H - oy]]
        slug = self._alias_of(fk)
        return {
            "id": f"pv:page:{fk[:8]}", "source_atom": slug,
            "stage": m.get("stage", "intermediate"),
            "x": round(x, 2), "y": round(y, 2), "z": z,
            "width": _PAGE_W, "height": _PAGE_H, "rotation": 0.0,
            "t_start": d, "t_end": None, "trajectory": trajectories,
            "label": self._label(fk),
            "corners": [[round(cx, 2), round(cy, 2)] for cx, cy in corners],
            "depth": z, "opacity": round(max(0.45, 1.0 - 0.15 * z), 3),
        }

    def _page_nodes(self, page_id: str, member_keys: List[str]) -> List[Dict[str, Any]]:
        """Position members in normalized page-local (u,v) on a deterministic grid — so a whole page
        can move / rotate / change depth without recomputing its internal layout (spec §6)."""
        out = []
        n = len(member_keys)
        cols = max(1, math.ceil(math.sqrt(n))) if n else 1
        rows = max(1, math.ceil(n / cols)) if n else 1
        for i, key in enumerate(member_keys):
            col, row = i % cols, i // cols
            u = (col + 0.5) / cols
            v = (row + 0.5) / rows
            m = self._meta(key)
            kind = m.get("clab_kind")
            pv_kind = "cluster" if kind == "cluster" else ("tension" if kind == "tension" else "concept")
            out.append({"id": f"pv:node:{page_id[8:]}:{i}", "source_atom": self._alias_of(key),
                        "source_key": key, "page": page_id, "u": round(u, 4), "v": round(v, 4),
                        "kind": pv_kind, "label": self._label(key)})
        return out

    # ── transforms + precomputed delta ──────────────────────────────────────────
    def _transforms(self, families, fam_set, fam_members, page_id_of, node_id_of, depth) -> List[Dict[str, Any]]:
        transforms = []
        for a in families:
            for b in self._dsts(a, "clab:family_next"):
                if b not in fam_set:
                    continue
                a_set, b_set = set(fam_members[a]), set(fam_members.get(b, []))
                added = sorted(b_set - a_set, key=self._alias_of)
                removed = sorted(a_set - b_set, key=self._alias_of)
                retained = sorted(a_set & b_set, key=self._alias_of)
                kind = self._delta_kind(added, removed)
                pa, pb = page_id_of[a], page_id_of[b]
                # map atoms → the node ids the GUI will animate: added/retained/changed on the TO
                # page (appear / stay), removed on the FROM page (fade).
                tid = "pv:transform:" + hashlib.sha256((a + "\x1f" + b).encode()).hexdigest()[:8]
                transforms.append({
                    "id": tid, "from": pa, "to": pb, "from_page": pa, "to_page": pb,
                    "kind": kind, "source_chronon": "", "t": depth.get(b, 0),
                    "added": [node_id_of.get((pb, k)) for k in added if node_id_of.get((pb, k))],
                    "removed": [node_id_of.get((pa, k)) for k in removed if node_id_of.get((pa, k))],
                    "retained": [node_id_of.get((pb, k)) for k in retained if node_id_of.get((pb, k))],
                    "changed": [],
                    "added_atoms": [self._alias_of(k) for k in added],
                    "removed_atoms": [self._alias_of(k) for k in removed],
                    "retained_atoms": [self._alias_of(k) for k in retained],
                })
        return transforms

    @staticmethod
    def _delta_kind(added, removed) -> str:
        if added and removed:
            return _KIND_REDEFINE
        if added:
            return _KIND_INTRODUCE
        if removed:
            return _KIND_REMOVE
        return _KIND_BRIDGE      # a family_next with no member change is a pure connection
