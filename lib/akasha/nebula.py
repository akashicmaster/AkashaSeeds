"""
Nebula — the cartographer: inductive schema discovery over accumulated atoms.

The third explorer. Where `assoc` fills a local 1-hop gap and `dream` proposes a
serendipitous pair, **nebula surveys the whole meaning-universe and asks which REGION is
becoming a concept model** — a dense clump of atoms that independently grew the SAME schema
(shared relation signature). It is the inverse of Phase-2 salient-rels: Phase 2 (deductive)
*gives* a category its important relations; nebula (inductive) *finds* atoms that already
grew those relations in common and proposes the shared relations as a salient-rel profile.

Machine PROPOSES only — like `dream`, the human (environment designer) confirms and names,
which then plants the cluster set + `sys:is_a` spine + `rel:salient` profile (kernel
`nebula.confirm`). No concept-model Python class is written automatically.

Degradation-first — every signal is optional and the floor is pure stdlib:
  • schema repetition  (relation-signature Jaccard)          — stdlib, the decisive signal
  • structural density (shared-neighbour Jaccard)            — stdlib
  • content cohesion   (tensor `semantic_vector` cosine)     — numpy tier, optional
  • structural cohesion(node-walk vector cosine)             — numpy tier, optional
  • salience mass      (sum of `meta["salience"]`)           — stdlib
Content vs structural cohesion AGREE → a category core; DISAGREE (structurally dense but
semantically diverse) → a relation/hub bud, surfaced separately.

This module is pure algorithm over a ctx-like engine (the injected graph endpoints), so it
is unit-testable with a mock. The kernel wires survey→vault and confirm→plant around it.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

# Namespaces/relations that are scaffolding, not conceptual members — excluded from
# clustering (a proto-word hub or a sys: anchor is not an emerging category).
_SKIP_NS = ("word:", "proto:", "sys:", "reldef:", "nsdef:", "ws:", "wf:", "tent:",
            "leaf:", "ns:", "lang:", "scope:", "owner:", "view:", "gbk:", "akt:")
# Weave / scaffolding relations that every namespaced atom carries — not domain schema, so
# they must not pollute a proposed salient-rel profile (a cluster sharing `specializes` only
# means its members are namespaced, not that they form a category).
_SKIP_REL = ("sys:refers_to", "sys:member_of", "sys:contains", "sys:part_of",
             "specializes", "sys:derived_from", "calc:associated_with")

# Default tuning (all overridable via params; clamped in survey()).
_DEFAULTS = {
    "scan":        4000,    # corpus window scanned (cheap meta reads)
    "cluster_cap": 600,     # top-salience atoms actually clustered (O(n^2) pairwise)
    "min_size":    4,       # a candidate must have at least this many members
    "limit":       8,       # top-N candidate regions returned
    "threshold":   0.34,    # similarity edge threshold for the cluster graph
    "salience":    0.0,     # minimum salience to enter the clustering set
}


# ── vector helpers (numpy-free cosine; mirrors semantic_learn.cosine) ────────────

def cosine(a: Optional[List[float]], b: Optional[List[float]]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = s1 = s2 = 0.0
    for i in range(n):
        x, y = a[i], b[i]
        dot += x * y
        s1 += x * x
        s2 += y * y
    if s1 <= 0.0 or s2 <= 0.0:
        return 0.0
    return dot / math.sqrt(s1 * s2)


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def _namespace(alias: str) -> str:
    """The leading namespace of a namespaced alias (`dish:kabsa` → `dish`), else ''."""
    if not alias or ":" not in alias:
        return ""
    return alias.split(":", 1)[0]


def _skippable(alias: str) -> bool:
    return (not alias) or (":" not in alias) or alias.startswith(_SKIP_NS)


# ── union-find (connected components of the similarity graph) ─────────────────────

class _UF:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


class NebulaCartographer:
    """Surveys a graph engine and returns ranked concept-model-candidate regions.

    Inject the engine (ctx). Required ctx surface (all read-only):
      stream(limit) -> iterable of row dicts ({"key","alias"/"meta"} best-effort)
      get_meta(key) -> dict (reads "salience", "semantic_vector")
      get_aliases_by_key(key) -> list[str]
      get_adjacent_links(key, rel=None) -> list[[dst, rel]]
      check_access(key, scopes) -> bool        (optional; unrestricted if absent)
    Optional structural lens: node_vec(key) -> list[float] | None.
    """

    def __init__(self, ctx: Any, node_vec: Optional[Any] = None):
        self.ctx = ctx
        self._node_vec = node_vec        # callable(key)->vec|None, or None

    # -- public entry --
    def survey(self, scopes: Optional[List[str]] = None,
               params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        p = dict(_DEFAULTS)
        for k, v in (params or {}).items():
            if k in p and v is not None:
                try:
                    p[k] = type(p[k])(v)
                except (TypeError, ValueError):
                    pass
        p["scan"] = max(50, min(int(p["scan"]), 20000))
        p["cluster_cap"] = max(20, min(int(p["cluster_cap"]), 2000))
        p["min_size"] = max(2, min(int(p["min_size"]), 100))
        p["limit"] = max(1, min(int(p["limit"]), 30))
        p["threshold"] = max(0.05, min(float(p["threshold"]), 0.95))

        atoms = self._gather(scopes, p)
        if len(atoms) < p["min_size"]:
            return []
        clusters = self._cluster(atoms, p)
        cands = []
        for members in clusters:
            if len(members) < p["min_size"]:
                continue
            prof = self._profile([atoms[i] for i in members], atoms, p)
            if prof:
                cands.append(prof)
        cands.sort(key=lambda c: c["score"], reverse=True)
        return cands[:p["limit"]]

    # -- 1. gather clustering candidates from the corpus window --
    def _gather(self, scopes, p) -> List[Dict[str, Any]]:
        rows = list(self.ctx.stream(p["scan"]) or [])
        out: List[Dict[str, Any]] = []
        for row in rows:
            key = row.get("key") if isinstance(row, dict) else None
            if not key:
                continue
            if scopes is not None and hasattr(self.ctx, "check_access"):
                try:
                    if not self.ctx.check_access(key, scopes):
                        continue
                except Exception:
                    pass
            aliases = []
            try:
                aliases = self.ctx.get_aliases_by_key(key) or []
            except Exception:
                pass
            alias = next((a for a in aliases if not _skippable(a)), "")
            if not alias:               # unnamed / scaffolding atom — not a member
                continue
            meta = {}
            try:
                meta = self.ctx.get_meta(key) or {}
            except Exception:
                pass
            salience = float(meta.get("salience", 0.0) or 0.0)
            if salience < p["salience"]:
                continue
            vec = meta.get("semantic_vector") or None
            sig, nbrs = self._signature(key)
            out.append({
                "key": key, "alias": alias, "ns": _namespace(alias),
                "salience": salience, "vec": vec, "sig": sig, "nbrs": nbrs,
            })
        # cluster only the top-salience slice (bounds the O(n^2) pass).
        out.sort(key=lambda a: a["salience"], reverse=True)
        return out[:p["cluster_cap"]]

    def _signature(self, key: str) -> Tuple[set, set]:
        """(relation-signature, neighbour-set) for an atom — the schema fingerprint."""
        sig: set = set()
        nbrs: set = set()
        try:
            for dst, rel in (self.ctx.get_adjacent_links(key) or []):
                if rel and rel not in _SKIP_REL:
                    sig.add(rel)
                if dst:
                    nbrs.add(dst)
        except Exception:
            pass
        return sig, nbrs

    # -- 2. cluster: connected components of a thresholded similarity graph --
    def _cluster(self, atoms: List[Dict[str, Any]], p) -> List[List[int]]:
        n = len(atoms)
        uf = _UF(n)
        thr = p["threshold"]
        for i in range(n):
            ai = atoms[i]
            for j in range(i + 1, n):
                if self._similarity(ai, atoms[j]) >= thr:
                    uf.union(i, j)
        groups: Dict[int, List[int]] = {}
        for i in range(n):
            groups.setdefault(uf.find(i), []).append(i)
        return list(groups.values())

    def _similarity(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        """Blended, DEGRADATION-FIRST similarity. Schema (rel-signature) + structural
        (shared neighbours) are always present (stdlib); content cosine joins when both
        atoms carry a semantic_vector. Weights renormalise over the signals present."""
        parts: List[Tuple[float, float]] = []          # (weight, value)
        parts.append((0.45, _jaccard(a["sig"], b["sig"])))            # schema repetition
        parts.append((0.20, _jaccard(a["nbrs"], b["nbrs"])))         # structural density
        if a["vec"] and b["vec"]:
            parts.append((0.35, max(0.0, cosine(a["vec"], b["vec"]))))  # content cohesion
        wsum = sum(w for w, _ in parts)
        if wsum <= 0:
            return 0.0
        # A schema match is necessary — two atoms with zero rel overlap are not the same
        # emerging category however close their text. Gate the blend on some schema overlap.
        if _jaccard(a["sig"], b["sig"]) <= 0.0 and a["ns"] != b["ns"]:
            return 0.0
        return sum(w * v for w, v in parts) / wsum

    # -- 3. profile: score + schema extraction + name --
    def _profile(self, members: List[Dict[str, Any]], all_atoms, p) -> Optional[Dict[str, Any]]:
        keys = [m["key"] for m in members]
        size = len(members)

        # salience mass (meaning-density of the region).
        sal_mass = sum(m["salience"] for m in members)

        # schema repetition — relations most members share (the proposed salient-rels).
        rel_count: Dict[str, int] = {}
        for m in members:
            for r in m["sig"]:
                rel_count[r] = rel_count.get(r, 0) + 1
        schema = sorted(
            ({"rel": r, "coverage": round(c / size, 3), "count": c}
             for r, c in rel_count.items() if c >= 2),
            key=lambda x: (x["coverage"], x["count"]), reverse=True)
        # schema strength = how strongly the top relations recur across members.
        schema_strength = (sum(s["coverage"] for s in schema[:4]) / 4.0) if schema else 0.0

        # cohesion (content lens) + structural cohesion (node lens) via a sampled centroid.
        cohesion = self._cohesion(members, "vec")
        struct_cohesion = self._struct_cohesion(members)
        # agreement of the two lenses — category core vs relation bud.
        if cohesion > 0 and struct_cohesion > 0:
            agreement = 1.0 - abs(cohesion - struct_cohesion)
        else:
            agreement = 0.0
        kind = ("category" if (struct_cohesion <= 0 or cohesion <= 0
                               or abs(cohesion - struct_cohesion) < 0.25)
                else "relation-bud")

        # boundary penalty — how much the region leaks into non-members (looser = worse).
        boundary = self._boundary(members, set(keys))

        # instance multiplicity, log-damped (worth abstracting, but not size-dominated).
        scale = math.log(1 + size) / math.log(1 + 40)

        # namespace mix (for naming + a homogeneity nudge).
        ns_count: Dict[str, int] = {}
        for m in members:
            ns_count[m["ns"]] = ns_count.get(m["ns"], 0) + 1
        dom_ns, dom_n = max(ns_count.items(), key=lambda kv: kv[1])
        homogeneity = dom_n / size

        density = _jaccard_density(members)

        # Overall concept-model-worthiness (all terms in [0,1]-ish; boundary subtracts).
        score = (
            0.34 * schema_strength +
            0.20 * _clip(cohesion) +
            0.16 * _clip(min(1.0, sal_mass / (size * 1.5 + 1e-9))) +
            0.14 * density +
            0.10 * scale +
            0.06 * homogeneity
        ) * (1.0 - 0.4 * boundary)

        name = self._propose_name(members, dom_ns, homogeneity)
        return {
            "id": _cluster_id(keys),
            "name": name,
            "kind": kind,
            "size": size,
            "members": keys,
            "member_aliases": [m["alias"] for m in members][:24],
            "salience_mass": round(sal_mass, 3),
            "cohesion": round(cohesion, 3),
            "struct_cohesion": round(struct_cohesion, 3),
            "agreement": round(agreement, 3),
            "density": round(density, 3),
            "boundary": round(boundary, 3),
            "namespaces": ns_count,
            "dominant_ns": dom_ns,
            "schema": schema[:8],
            "salient_rels": [s["rel"] for s in schema[:6]],
            "score": round(score, 4),
            "score_parts": {
                "schema_strength": round(schema_strength, 3),
                "cohesion": round(cohesion, 3),
                "salience": round(min(1.0, sal_mass / (size * 1.5 + 1e-9)), 3),
                "density": round(density, 3),
                "scale": round(scale, 3),
                "homogeneity": round(homogeneity, 3),
                "boundary_penalty": round(0.4 * boundary, 3),
            },
        }

    def _cohesion(self, members, field: str) -> float:
        vecs = [m[field] for m in members if m.get(field)]
        if len(vecs) < 2:
            return 0.0
        cen = _centroid(vecs)
        if not cen:
            return 0.0
        return sum(max(0.0, cosine(v, cen)) for v in vecs) / len(vecs)

    def _struct_cohesion(self, members) -> float:
        if not self._node_vec:
            return 0.0
        vecs = []
        for m in members:
            try:
                nv = self._node_vec(m["key"])
            except Exception:
                nv = None
            if nv:
                vecs.append(nv)
        if len(vecs) < 2:
            return 0.0
        cen = _centroid(vecs)
        return sum(max(0.0, cosine(v, cen)) for v in vecs) / len(vecs) if cen else 0.0

    def _boundary(self, members, member_keys: set) -> float:
        """Fraction of member out-edges that leave the cluster (conductance-like)."""
        inside = outside = 0
        for m in members:
            for dst in m["nbrs"]:
                if dst in member_keys:
                    inside += 1
                else:
                    outside += 1
        tot = inside + outside
        return (outside / tot) if tot else 1.0

    def _propose_name(self, members, dom_ns: str, homogeneity: float) -> str:
        # A homogeneous namespace names itself; otherwise the highest-salience member's
        # local term is the working label for the human to rename.
        if dom_ns and homogeneity >= 0.6:
            return dom_ns
        top = max(members, key=lambda m: m["salience"])
        term = top["alias"].rsplit(":", 1)[-1]
        return re.sub(r"[^a-z0-9_]+", "_", term.lower()).strip("_") or "region"


# ── module helpers ───────────────────────────────────────────────────────────────

def _clip(x: float) -> float:
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def _centroid(vecs: List[List[float]]) -> List[float]:
    if not vecs:
        return []
    n = min(len(v) for v in vecs)
    if n == 0:
        return []
    cen = [0.0] * n
    for v in vecs:
        for i in range(n):
            cen[i] += v[i]
    return [c / len(vecs) for c in cen]


def _jaccard_density(members) -> float:
    """Average pairwise neighbour-set Jaccard — how interwoven the members are."""
    m = len(members)
    if m < 2:
        return 0.0
    tot = 0.0
    cnt = 0
    cap = 40                       # sample pairs to stay cheap on big clusters
    for i in range(min(m, cap)):
        for j in range(i + 1, min(m, cap)):
            tot += _jaccard(members[i]["nbrs"], members[j]["nbrs"])
            cnt += 1
    return (tot / cnt) if cnt else 0.0


def _cluster_id(keys: List[str]) -> str:
    import hashlib
    h = hashlib.sha1(("|".join(sorted(keys))).encode("utf-8")).hexdigest()
    return "neb:" + h[:16]
