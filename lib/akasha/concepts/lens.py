"""
LensConcept — source scanner and concept-model projection engine.

  Operator : lens.scan / lens.cast
  Agent    : any AkashaSession client

[Three-layer architecture]

  Layer 1  SourceScanner  (lens.scan)
    Enumerates nodes from a set or graph traversal, collects attribute
    profiles, infers type hints, computes coverage.  Completely model-agnostic.
    Result stored in session context for follow-up lens.cast.

  Layer 2  ImportableMixin registry  (queried by lens.scan)
    Each concept model that implements ImportableMixin.match_projection()
    is scored against the ProjectionProfile.  Score + auto-mapping are
    returned as numbered candidates.

  Layer 3  lens.cast
    Reads the stored candidates, instantiates the chosen model class with
    the current session, and calls import_projection(nodes, mapping, into).

[Session context keys]

  "lens_profile"    ProjectionProfile (summary, no node list)
  "lens_nodes"      List[(key, attrs, depth, meta)] — full node list
  "lens_candidates" Ordered list of match results

[Interactive shell]

  In lens mode, bare digits navigate the candidate list.
  The shell intercepts them and builds lens.cast signpost=N [into=name].
"""

import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.concepts.base import BaseConcept
from lib.akasha.api.concepts import ImportableMixin, ExportableMixin   # the contracts, through the API
from lib.akasha.concepts._universal import UniversalConcept

logger = logging.getLogger("Harmonia.Lens")


from lib.akasha.artifact_epoch import artifact_id as _artifact_id, is_stale as _is_stale


def _lslug(s: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


class _LensNucIO(UniversalConcept):
    """A NON-registered UniversalConcept (no CONCEPT_METHODS ⇒ the registry never discovers it): lens
    borrows its nucleus-spanning helpers (_members / _meta / _alias / _key / _mk / _link / _add_to_set)
    to read Set members that live in the shared nucleus and to write the ONE compare aggregate into
    universal scope — the same helpers the source engine uses. Its `core` handles link adjacency in the
    nucleus (which the session cortex does not span)."""
    CONCEPT_PREFIX = "lens_nucio"

# Module-level registry reference — injected by kernel.py at startup.
_registry_ref = None

_SAMPLE_SIZE = 30   # nodes sampled for type inference
_MAX_NODES   = 5000 # hard cap for scan


def set_registry(registry) -> None:
    """Inject the ConceptRegistry so lens.scan can find ImportableMixin classes."""
    global _registry_ref
    _registry_ref = registry


# ── Type inference ─────────────────────────────────────────────────────────────

def _infer_type(values: List[str]) -> str:
    """Guess the most specific type for a list of string samples."""
    if not values:
        return "text"
    sample = [v for v in values if v and v.strip()][:_SAMPLE_SIZE]
    if not sample:
        return "text"

    bool_words = {"true", "false", "yes", "no", "1", "0"}
    counts = {"date": 0, "int": 0, "float": 0, "bool": 0}

    for v in sample:
        sv = v.strip()
        # Strip [key]\n header written by the def command before type-probing
        if sv.startswith("[") and "\n" in sv:
            sv = sv.split("\n", 1)[1].strip()
        if sv.lower() in bool_words:
            counts["bool"] += 1
            continue
        # Date: YYYY, YYYY-MM, YYYY-MM-DD, or ISO 8601
        if len(sv) >= 4 and sv[:4].isdigit():
            if len(sv) == 4:
                counts["date"] += 1; continue
            if len(sv) in (7, 10) and sv[4] == "-":
                counts["date"] += 1; continue
            if len(sv) > 10 and "T" in sv:
                counts["date"] += 1; continue
        try:
            int(sv.replace(",", "").replace("_", ""))
            counts["int"] += 1; continue
        except ValueError:
            pass
        try:
            float(sv.replace(",", "").replace("_", ""))
            counts["float"] += 1; continue
        except ValueError:
            pass

    n = len(sample)
    for typ in ("date", "bool", "float", "int"):
        if counts[typ] / n >= 0.70:
            return typ
    return "text"


def _bar(coverage: float, width: int = 10) -> str:
    filled = round(coverage * width)
    return "█" * filled + "░" * (width - filled)


# ── SourceScanner ──────────────────────────────────────────────────────────────

class SourceScanner:
    """
    Enumerates nodes from a set or graph traversal and builds a ProjectionProfile.

    set mode   : src is a set name (e.g. "set:rec:expense").
    tree mode  : src is an atom key/alias and follow= specifies the rel to traverse.
    """

    def __init__(self, cortex, session=None):
        self.cortex  = cortex
        self.session = session

    # ── public entry point ─────────────────────────────────────────────────────

    def scan(
        self,
        src:    str,
        follow: str = "",
        depth:  int = 2,
    ) -> Tuple[Dict[str, Any], List[Tuple]]:
        """
        Scan the source and return (ProjectionProfile, nodes).

        nodes : list of (atom_key, attrs_dict, traversal_depth, meta_dict)
          attrs_dict includes rec: link values AND "content" key for atom content.

        Resolution order (non-tree mode):
          1. ExportableMixin — if src resolves to a concept model instance atom
          2. Set scan — if src names a collection
          3. (tree mode overrides all with BFS traversal)
        """
        if not follow:
            exported = self._collect_export(src)
            if exported is not None:
                profile = self._build_profile(src, follow, depth, exported)
                profile["scope"] = "model_export"
                return profile, exported

        if follow:
            nodes = self._collect_tree(src, follow, depth)
        else:
            nodes = self._collect_set(src)

        profile = self._build_profile(src, follow, depth, nodes)
        return profile, nodes

    # ── ExportableMixin detection ──────────────────────────────────────────────

    def _collect_export(self, src: str) -> Optional[List[Tuple]]:
        """
        Try to collect nodes via an ExportableMixin class.

        Resolves src → atom key → checks meta["type"] against every registered
        ExportableMixin's EXPORT_SCHEMA["meta_type"].  Returns None if no match
        (caller falls through to set/tree scan).
        """
        if _registry_ref is None or self.session is None:
            return None

        atom_key = self.cortex.resolve_alias(src) or src
        meta      = self.cortex.get_meta(atom_key) or {}
        meta_type = meta.get("type", "")
        if not meta_type:
            return None

        seen: set = set()
        for entry in _registry_ref._handlers.values():
            cls = entry[0]                        # (cls, op_name, coerce, namespace)
            if cls in seen:
                continue
            seen.add(cls)
            if not (isinstance(cls, type) and issubclass(cls, ExportableMixin)):
                continue
            schema = cls.EXPORT_SCHEMA
            if schema.get("meta_type") != meta_type:
                continue
            # Optional refinement: every key in meta_match must equal the atom's meta.
            # Lets several models share a generic meta_type (e.g. "concept") while
            # still being disambiguated (survey roots are type="concept" + concept="survey").
            meta_match = schema.get("meta_match") or {}
            if any(meta.get(mk) != mv for mk, mv in meta_match.items()):
                continue
            try:
                instance = cls(self.session)
                nodes = instance.export_projection(atom_key)
                if nodes is not None:
                    return nodes
            except Exception:
                return None
            return None

        return None

    # ── node collection ────────────────────────────────────────────────────────

    def _collect_set(self, src: str) -> List[Tuple]:
        """Collect members of a named set."""
        # Try the src as-is, then with "set:" prefix
        members = self.cortex.get_collection_members(src)
        if not members and not src.startswith("set:"):
            members = self.cortex.get_collection_members(f"set:{src}")
        return [self._node_tuple(k, 0) for k in members[:_MAX_NODES] if k]

    def _collect_tree(self, src: str, follow: str, max_depth: int) -> List[Tuple]:
        """BFS from a root atom following links of type `follow`."""
        root = self.cortex.resolve_alias(src) or src
        if not self.cortex.get_chunk(root):
            return []

        visited: Dict[str, int] = {root: 0}
        queue   = [root]
        result  = [self._node_tuple(root, 0)]

        while queue and len(result) < _MAX_NODES:
            current = queue.pop(0)
            cur_depth = visited[current]
            if cur_depth >= max_depth:
                continue
            links = self.cortex.get_adjacent_links(current, follow)
            for dst, _ in links:
                if dst not in visited:
                    visited[dst] = cur_depth + 1
                    queue.append(dst)
                    result.append(self._node_tuple(dst, cur_depth + 1))
                    if len(result) >= _MAX_NODES:
                        break

        return result

    def _node_tuple(self, key: str, depth: int) -> Tuple:
        """Build a single node tuple (key, attrs, depth, meta)."""
        content = self.cortex.get_chunk(key) or ""
        meta    = self.cortex.get_meta(key) or {}
        links   = self.cortex.get_adjacent_links(key)

        attrs: Dict[str, str] = {"content": content}
        for dst, rel in links:
            if rel.startswith("rec:") or rel.startswith("tbl:") or rel.startswith("ctx:"):
                val = self.cortex.get_chunk(dst) or ""
                if val:
                    attrs[rel] = val

        return (key, attrs, depth, meta)

    # ── profile construction ───────────────────────────────────────────────────

    def _build_profile(
        self,
        src:   str,
        follow: str,
        depth:  int,
        nodes:  List[Tuple],
    ) -> Dict[str, Any]:
        node_count = len(nodes)
        if not nodes:
            return {
                "src": src, "scope": "tree" if follow else "flat_set",
                "node_count": 0, "attrs": {}, "meta_attrs": {},
                "content_available": False, "content_sample": "",
                "link_types_out": [], "link_types_in": [],
                "tree_depth_max": depth if follow else None,
            }

        # Aggregate attribute coverage + samples
        attr_values:   Dict[str, List[str]] = defaultdict(list)
        attr_counts:   Dict[str, int]       = defaultdict(int)
        link_types_out = set()

        for key, attrs, nd, meta in nodes:
            for attr, val in attrs.items():
                attr_counts[attr] += 1
                if len(attr_values[attr]) < _SAMPLE_SIZE:
                    attr_values[attr].append(val)
            links = self.cortex.get_adjacent_links(key)
            for _, rel in links:
                link_types_out.add(rel)

        # Compute per-attr profile
        attrs_profile: Dict[str, Any] = {}
        for attr, count in attr_counts.items():
            if attr == "content":
                continue
            coverage = count / node_count
            samples  = attr_values.get(attr, [])
            attrs_profile[attr] = {
                "type_hint": _infer_type(samples),
                "coverage":  round(coverage, 3),
                "sample":    samples[0] if samples else "",
            }

        content_samples = attr_values.get("content", [])
        content_sample  = content_samples[0] if content_samples else ""
        content_avail   = bool(content_samples) and any(s.strip() for s in content_samples)

        return {
            "src":              src,
            "scope":            "tree" if follow else "flat_set",
            "node_count":       node_count,
            "attrs":            attrs_profile,
            "meta_attrs":       {},
            "content_available": content_avail,
            "content_sample":   content_sample[:80],
            "link_types_out":   sorted(link_types_out),
            "link_types_in":    [],
            "tree_depth_max":   depth if follow else None,
        }


# ── Coerce helpers ─────────────────────────────────────────────────────────────

def _coerce_scan(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "src":    data.get("src", "").strip().strip('"\''),
        "follow": data.get("follow", "").strip().strip('"\''),
        "depth":  int(data.get("depth", 2)),
        "within": data.get("within", "").strip().strip('"\''),
    }


def _coerce_cast(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "signpost": int(data["signpost"]) if data.get("signpost") else None,
        "into":     data.get("into", "").strip().strip('"\''),
        "model":    data.get("model", "").strip(),
    }


def _coerce_flatten(data: Dict[str, Any]) -> Dict[str, Any]:
    return {"into": data.get("into", "").strip().strip('"\'')}


# ── LensConcept ───────────────────────────────────────────────────────────────

class LensConcept(BaseConcept):
    """
    Lens — source scanner and concept-model projection engine.

    lens.scan    : scan a set/tree, score compatible models, store candidates.
    lens.cast    : project the scanned nodes into the chosen concept model.
    lens.flatten : persist scan nodes as new rec atoms in a named set (snapshot).
    """

    CONCEPT_PREFIX = "lens"
    CONCEPT_LABEL  = "Source scanner and concept-model projection engine"
    CONCEPT_METHODS = {
        "scan": {"op": "op_scan", "coerce": _coerce_scan},
        "cast": {"op": "op_cast", "coerce": _coerce_cast},
        "flatten": {
            "op":     "op_flatten",
            "coerce": _coerce_flatten,
            "action": "record",
            "args":   ["into"],
            "desc":   "Persist scan nodes as rec atoms in a named set: lens.flatten into=<name>",
        },
        "compare": {
            "op":     "op_compare",
            "action": "read",
            "args":   ["a", "b", "key", "field", "truth", "result", "item"],
            "desc":   "Join two Sets member-by-member (key=<relation to the join key>, empty = the "
                      "member) and compare one meta field: lens.compare a=<set> b=<set> [key=<rel>] "
                      "[field=label] [truth=<item field>] [result=<atom>] [item=<id>]",
        },
        "rank": {
            "op":     "op_rank",
            "action": "read",
            "args":   ["set", "key", "order", "within", "group", "top"],
            "desc":   "Rank a Set's atoms by a meta field, grouped (default group=frame): lens.rank "
                      "set=<Set> key=<field> [order=desc|asc] [within=<Set>] [group=<f[,f]>] [top=<n>]",
        },
    }

    # ── nucleus IO helper (observations live in the shared nucleus) ─────────────
    def _nucio(self) -> "_LensNucIO":
        io = getattr(self, "_nucio_cache", None)
        if io is None:
            io = self._nucio_cache = _LensNucIO(self.session)
        return io

    # ── helpers ───────────────────────────────────────────────────────────────

    def _scanner(self) -> SourceScanner:
        return SourceScanner(self.cortex, self.session)

    def _importable_classes(self) -> List[type]:
        """Return all registered concept model classes that implement ImportableMixin."""
        if _registry_ref is None:
            return []
        seen: set = set()
        result: List[type] = []
        for entry in _registry_ref._handlers.values():
            cls = entry[0]                        # (cls, op_name, coerce, namespace)
            if cls not in seen and isinstance(cls, type) and issubclass(cls, ImportableMixin):
                seen.add(cls)
                result.append(cls)
        return result

    def _auto_into(self, src: str, model: str) -> str:
        """Generate a default target name from src + model."""
        base = src.replace("set:rec:", "").replace("set:", "").split(":")[0]
        base = base or "lens"
        candidate = f"{base}_{model}"
        # Avoid alias collision
        if not self.cortex.resolve_alias(f"tbl:{candidate}"):
            return candidate
        for i in range(2, 20):
            alt = f"{candidate}_{i}"
            if not self.cortex.resolve_alias(f"tbl:{alt}"):
                return alt
        return f"{candidate}_{int(time.time())}"

    # ── operators ─────────────────────────────────────────────────────────────

    def op_scan(
        self,
        src:    str,
        follow: str = "",
        depth:  int = 2,
        within: str = "",
    ) -> Dict[str, Any]:
        """[lens.scan] Scan a source and list compatible concept model targets.

        src    — set name (e.g. "set:rec:expense") or atom key/alias (tree root)
        follow — link relation to traverse for tree mode (e.g. "ref:therefore")
        depth  — max traversal depth in tree mode (default 2)
        within — a Set to INTERSECT the scanned nodes with (G4): keep only nodes that are members of
                 `within`, so a lens is confined to a membrane (e.g. the observations of one run). A
                 coordinate/run membership Set is exactly such a membrane — this is Set algebra, no new
                 traversal.

        Stores results in session context for follow-up lens.cast.
        Returns a lens:scan result for the renderer.

        Example:
          lens src="set:rec:expense"
          lens src=<atom_key> follow="ref:therefore" depth=3
        """
        if not src:
            raise ValueError("'src' is required.")

        # Invalidate any prior scan's stored result UP FRONT: a fresh scan supersedes it,
        # and — crucially — a scan that then FAILS (no nodes / scanner error) must not leave
        # the previous scan's nodes behind for lens.flatten/cast to silently pick up.
        self.session.set_context("lens_profile",    None)
        self.session.set_context("lens_nodes",      None)
        self.session.set_context("lens_candidates", None)

        scanner = self._scanner()
        profile, nodes = scanner.scan(src, follow=follow, depth=depth)

        if within:
            keep = set(self._nucio()._members(within))
            nodes = [n for n in nodes if n[0] in keep]
            profile["within"] = within
            profile["node_count"] = len(nodes)

        if not nodes:
            raise ValueError(f"No nodes found at '{src}'{f' within {within}' if within else ''}.")

        # Score all importable models
        importable = self._importable_classes()
        candidates: List[Dict[str, Any]] = []
        for cls in importable:
            match = cls.match_projection(profile)
            if match.get("score", 0) > 0.05:
                candidates.append({
                    "model":        cls.CONCEPT_PREFIX,
                    "cls_name":     cls.__name__,
                    "score":        match["score"],
                    "auto_mapping": match.get("auto_mapping", {}),
                    "auto_opts":    match.get("auto_opts", {}),
                    "notes":        match.get("notes", []),
                    "missing":      match.get("missing", []),
                })
        candidates.sort(key=lambda c: -c["score"])

        # Store in session context
        self.session.set_context("lens_profile",    profile)
        self.session.set_context("lens_nodes",      nodes)
        self.session.set_context("lens_candidates", candidates)

        # Build a row-preview for the renderer (first 15 nodes, attrs only)
        _PREVIEW_MAX = 15
        attr_keys     = sorted(profile.get("attrs", {}).keys())
        preview_rows: List[Dict[str, Any]] = []
        for _atom_key, _attrs, _depth, _meta in nodes[:_PREVIEW_MAX]:
            preview_rows.append({k: str(_attrs.get(k) or "") for k in attr_keys})

        return {
            "type":         "lens:scan",
            "src":          src,
            "profile":      profile,
            "candidates":   candidates,
            "preview_cols": attr_keys,
            "preview_rows": preview_rows,
        }

    # ── observation join (G4 / Part D T7 substrate) ─────────────────────────────
    def _inputs_epoch(self, io: "_LensNucIO", sets: Tuple[str, ...]) -> Optional[int]:
        """S1-a §1.4/§1.5 — the epoch of a set of observation Sets: the MAX member coordinate
        (`cronon`/`at_seq`) across them. A later observation added to either Set raises this, so a diff
        built at the old epoch reads as stale. O(members) — a bounded membrane read, never a scan."""
        hi = None
        for s in sets:
            for okey in io._members(s):
                m = io._meta(io._alias(okey) or okey) or {}
                e = m.get("cronon")
                if e is None:
                    e = m.get("at_seq")
                try:
                    e = int(e) if e is not None else None
                except (TypeError, ValueError):
                    e = None
                if e is not None and (hi is None or e > hi):
                    hi = e
        return hi

    @staticmethod
    def _member_row(io: "_LensNucIO", core, okey: str, key: str, field: str) -> Tuple[Optional[str], Any, float]:
        """For one member of a compared Set: (its join key, its `field` value, its `confidence`). The
        join key is the target of the member's first `key` link (`key` names a RELATION), or the member
        itself when `key` is empty. The value is the member's own meta `field` (else its
        `source_metadata[field]`). The lens reads what the member's writer stated — it derives no label
        from any model's atoms (the purge order §2: the platform names no application relation)."""
        oalias = io._alias(okey) or okey
        item = oalias
        if key:
            item = None
            try:
                for l in core.get_adjacent_links(okey, key):
                    dst = l.get("dst")
                    if dst:
                        item = io._alias(dst) or dst
                        break
            except Exception:
                item = None
        m = io._meta(oalias) or {}
        val = m.get(field)
        if val is None:
            val = (m.get("source_metadata") or {}).get(field)
        try:
            conf = float(m.get("confidence") or 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        return item, val, conf

    def op_compare(self, a: str = "", b: str = "", key: str = "", field: str = "label",
                   truth: str = "", result: str = "", item: str = "") -> Dict[str, Any]:
        """[lens.compare] Join two Sets member-by-member and compare one meta field — a per-item
        before/after. `key` names the RELATION whose target is each member's join key (empty: the member
        itself); `field` is the member meta field compared (default `label`; falls back to the member's
        `source_metadata`). Optional `truth=<field>` scores agreement with the joined item's own field
        (never read from a member); optional `item=<id>` returns just that item's row. With `result=`,
        stores ONE aggregate atom (concept `lens_compare`, epoch-stamped) under that alias and returns its
        key as `stored`; indexing it anywhere else is the caller's. Pure Set algebra over two membranes."""
        if not a or not b:
            raise ValueError("lens.compare requires a= and b= (two observation Sets)")
        # F3 — a GUEST reads the comparison read-only: the answer key (`truth=`) NEVER leaves the
        # admitted circle (rows carry truth=null, truth_known=0), and no aggregate atom is stored (a
        # guest holds no write capability — `result=` is ignored rather than refused, so the read still
        # returns the rows the public page shows).
        _guest = self._is_guest()
        if _guest:
            truth = ""
            result = ""
        io = self._nucio()
        core = io._nuc.core if io._nuc else None
        if core is None:
            raise RuntimeError("lens.compare needs the nucleus (observations live there)")

        def _index(setname):
            out = {}
            for okey in io._members(setname):
                item, label, conf = self._member_row(io, core, okey, key, field)
                if item is not None:
                    out[item] = {"observation": io._alias(okey) or okey, "label": label,
                                 "confidence": round(conf, 4)}
            return out

        A, B = _index(a), _index(b)
        items = sorted(set(A) | set(B))
        rows, changed, agree_a, agree_b, truths = [], 0, 0, 0, 0
        for it in items:
            ra, rb = A.get(it), B.get(it)
            la = ra["label"] if ra else None
            lb = rb["label"] if rb else None
            ch = (la != lb)
            if ch:
                changed += 1
            tv = None
            if truth:
                tm = io._meta(it) or {}
                tv = tm.get(truth) or (tm.get("source_metadata") or {}).get(truth)
                if tv is not None:
                    truths += 1
                    if la is not None and str(la) == str(tv):
                        agree_a += 1
                    if lb is not None and str(lb) == str(tv):
                        agree_b += 1
            rows.append({"item": it, "a": ra, "b": rb, "changed": ch, "truth": tv})
        summary = {"items": len(items), "changed": changed,
                   "agree_a": agree_a, "agree_b": agree_b, "truth_known": truths}
        # D2-M §4.5 — an item= filter returns just that item's row (the GUI's single-item compare).
        if item:
            rows = [r for r in rows if str(r.get("item")) == str(item)
                    or str(r.get("item")) == str(io._alias(io._key(item)) or item)]

        stored = None
        if result:
            # A `wb:<bench>:…` result alias is a bench's: slug its bench segment so it matches the bench
            # alias (`wb:` + slug(name)) whatever spelling of the bench the caller passed.
            if result.startswith("wb:"):
                _parts = result.split(":")
                if len(_parts) >= 2 and _parts[1]:
                    _parts[1] = _lslug(_parts[1])
                    result = ":".join(_parts)
            content = "[lens.compare] %s vs %s: %d items, %d changed" % (a, b, len(items), changed)
            # S1-a §1.4 — this stored aggregate is a DERIVED accelerator. Stamp its epoch identity so a
            # reader can tell a fresh diff from a stale one (inputs advanced) and regenerate it: the
            # inputs are the two observation Sets, the epoch is their max member coordinate, and the
            # access_context distinguishes a guest's diff from an admitted member's (F3/R5).
            _epoch = self._inputs_epoch(io, (a, b))
            _aid = _artifact_id(_epoch, "universal", None, (a, b), "lens.compare", field,
                                "guest" if self._is_guest() else "member")
            meta = {"concept": "lens_compare", "a": a, "b": b, "key": key, "field": field,
                    "truth": truth or None, "built_at_epoch": _epoch, "artifact_id": _aid,
                    "access_context": "guest" if self._is_guest() else "member", **summary}
            # S1-a §1.4 — REPLACE-on-change keyed on the artifact_id: a rebuild at a NEW epoch (inputs
            # advanced) mints a fresh generation and re-points the alias; an identical rebuild is a no-op.
            # (The old atom stays — history — per _mk_replace.)
            stored, _achg, _aold = io._mk_replace(result, content, meta, compare_meta=("artifact_id",))
        logger.info("[lens.compare] a=%s b=%s items=%d changed=%d agree_a=%d agree_b=%d",
                    a, b, len(items), changed, agree_a, agree_b)
        return {"type": "lens:compare", "a": a, "b": b, "key": key, "field": field,
                "rows": rows, "summary": summary, "result": result or None, "stored": stored}

    def op_rank(self, set: str = "", key: str = "accuracy", order: str = "desc",
                within: str = "", group: str = "frame", top: str = "") -> Dict[str, Any]:
        """[lens.rank] P0-a §2.4 — rank a Set's atoms by a meta `key`, GROUPED (default `group=frame`
        so evaluations on different held-out frames never rank against each other — `frame_mismatch=true`
        when a group spans frames), optionally intersected `within=<Set>`, `top=<n>` per group. Pure Set
        algebra over the members' meta — no scan, guest-readable (F3). The leaderboard macro is built on
        this."""
        if not set:
            raise ValueError("lens.rank requires set=")
        io = self._nucio()
        within_keys = {x for x in io._members(within)} if within else None
        group_fields = [g.strip() for g in str(group or "").split(",") if g.strip()]
        desc = str(order or "desc").lower() != "asc"
        rows = []
        for mk in io._members(set):
            if within_keys is not None and mk not in within_keys:
                continue
            m = io._meta(io._alias(mk) or mk) or {}
            if not m:
                continue
            row = dict(m)
            row["atom"] = io._alias(mk) or mk
            # B1 §A6 — a claim's `status` is DERIVED (never stored): when ranking the claims Set, ask the
            # claim concept for each row's status (so `group=status` works) and HIDE the text from a guest.
            if m.get("concept") == "claim":
                try:
                    from lib.akasha.concepts.claim import ClaimConcept
                    row["status"] = ClaimConcept(self.session)._derive_status(mk)
                except Exception:
                    row.setdefault("status", "unattached")
                if self._is_guest():
                    row.pop("text", None)
            rows.append(row)

        def _num(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        def _gkey(r):
            return tuple(str(r.get(g)) for g in group_fields) if group_fields else ("_all",)

        groups: Dict[tuple, list] = {}
        for r in rows:
            groups.setdefault(_gkey(r), []).append(r)
        try:
            _top = int(top) if str(top).strip() else None
        except (TypeError, ValueError):
            _top = None
        out_groups = []
        for gk, grows in groups.items():
            # sort by the numeric key when possible (None sinks to the bottom), else lexicographically
            grows.sort(key=lambda r: (_num(r.get(key)) is not None, _num(r.get(key))
                                      if _num(r.get(key)) is not None else 0, str(r.get(key) or "")),
                       reverse=desc)
            ranked = grows[:_top] if _top else grows
            for i, r in enumerate(ranked):
                r["rank"] = i + 1
            out_groups.append({"group": dict(zip(group_fields, gk)) if group_fields else {},
                               "rows": ranked, "count": len(ranked)})
        # a request that mixes frames when the caller did NOT group by frame is flagged (P0-a)
        _frames = {str(r.get("frame")) for r in rows if r.get("frame") is not None}
        frame_mismatch = (len(_frames) > 1) and ("frame" not in group_fields)
        logger.debug("[lens.rank] set=%s key=%s groups=%d frame_mismatch=%s", set, key,
                     len(out_groups), frame_mismatch)
        return {"type": "lens:rank", "set": set, "key": key, "order": "desc" if desc else "asc",
                "group": group_fields, "groups": out_groups, "count": len(rows),
                "frame_mismatch": frame_mismatch}

    def op_cast(
        self,
        signpost: Optional[int] = None,
        into:     str = "",
        model:    str = "",
    ) -> Dict[str, Any]:
        """[lens.cast] Project stored scan nodes into a concept model.

        signpost — candidate number from lens.scan output (1-indexed)
        into     — target name (auto-generated from src+model if omitted)
        model    — model prefix override (used when signpost is absent)

        After lens.scan, use this via the interactive lens mode:
          1            — project into candidate #1 with auto-generated name
          1 my_table   — project into candidate #1 named "my_table"

        Or directly:
          lens.cast signpost=1 into=expenses_2025
          lens.cast model=table into=expenses_2025
        """
        profile    = self.session.get_context("lens_profile")
        nodes      = self.session.get_context("lens_nodes")
        candidates = self.session.get_context("lens_candidates")

        if not profile or nodes is None:
            raise RuntimeError("No scan result found. Run 'lens src=<x>' first.")

        if signpost is not None:
            idx = int(signpost) - 1
            if not candidates or idx < 0 or idx >= len(candidates):
                raise ValueError(
                    f"Signpost {signpost} out of range. "
                    f"Valid: 1–{len(candidates or [])}."
                )
            candidate = candidates[idx]
            model     = candidate["model"]
        elif model:
            candidate = next(
                (c for c in (candidates or []) if c["model"] == model), None
            )
            if candidate is None:
                # Not in cached candidates — run match now
                if _registry_ref is None:
                    raise RuntimeError("Lens registry not initialised.")
                cls = _registry_ref.get_class(model)
                if cls is None:
                    raise ValueError(f"Model '{model}' not found in registry.")
                match     = cls.match_projection(profile)
                candidate = {
                    "model":        model,
                    "cls_name":     cls.__name__,
                    "auto_mapping": match.get("auto_mapping", {}),
                    "auto_opts":    match.get("auto_opts", {}),
                }
        else:
            raise ValueError("Provide signpost= or model= to lens.cast.")

        if not into:
            into = self._auto_into(profile.get("src", "lens"), candidate["model"])

        if _registry_ref is None:
            raise RuntimeError("Lens registry not initialised.")
        target_cls = _registry_ref.get_class(candidate["model"])
        if target_cls is None or not issubclass(target_cls, ImportableMixin):
            raise ValueError(
                f"Model '{candidate['model']}' is not importable."
            )

        target_instance = target_cls(self.session)
        result = target_instance.import_projection(
            nodes   = nodes,
            mapping = candidate["auto_mapping"],
            into    = into,
            **candidate["auto_opts"],
        )

        return {
            "type":       "lens:cast",
            "model":      candidate["model"],
            "into":       into,
            "node_count": len(nodes),
            "result":     result,
        }

    def op_flatten(self, into: str) -> Dict[str, Any]:
        """[lens.flatten] Persist current scan nodes as rec atoms in a named set.

        Creates a persistent snapshot — each scanned node becomes a new rec atom
        carrying the same attributes as the source.  Source atoms are never
        modified.  A ctx:source link preserves the reference to the original atom.

        into — target set name (auto-prefixed with "set:" if not already prefixed)

        The snapshot set can be used in downstream operations:
          s.op union / isect / diff   — set algebra with other sets
          lens src=set:<into>          — re-scan the snapshot
          rec.ls in_set=<into>         — browse as records
          cross / tensor projection    — multi-model intersection

        Example:
          lens src="set:rec:expense"
          lens.flatten into=expense_snap
          → atoms in set:expense_snap; rec.ls in_set=expense_snap works immediately
        """
        nodes = self.session.get_context("lens_nodes")
        if not nodes:
            raise RuntimeError("No scan result found. Run 'lens src=<x>' first.")
        if not into:
            raise ValueError("'into' is required.")

        set_name = into if into.startswith("set:") else f"set:{into}"
        aid    = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{aid}", f"view:user_{aid}"]

        written = 0
        for atom_key, attrs, depth, meta in nodes:
            # Content is unique per source atom — ensures idempotent snapshots
            snap_content = f"[ flat:{atom_key[:24]} in:{into} ]"
            snap_key = self.cortex.put_chunk(
                content=snap_content,
                meta={
                    "type":       "rec",
                    "rec_type":   "lens_flat",
                    "source_key": atom_key,
                    "created_at": time.time(),
                },
                author=aid,
                scopes=scopes,
            )

            # Write source atom's text content as rec:content (if meaningful)
            src_content = attrs.get("content", "").strip()
            if src_content:
                val_key = self.cortex.put_chunk(
                    content=src_content,
                    meta={"type": "rec_value"},
                    author=aid,
                    scopes=scopes,
                )
                self.cortex.put_link(snap_key, val_key, "rec:content",
                                     w=1.0, author=aid)

            # Write each typed attribute (rec:, tbl:, ctx:, …) as a rec: link
            for attr, val in attrs.items():
                if attr == "content" or not val:
                    continue
                attr_key = attr if attr.startswith("rec:") else f"rec:{attr}"
                val_key = self.cortex.put_chunk(
                    content=val,
                    meta={"type": "rec_value"},
                    author=aid,
                    scopes=scopes,
                )
                self.cortex.put_link(snap_key, val_key, attr_key,
                                     w=1.0, author=aid)

            # Trace link back to original atom — source is never touched
            self.cortex.put_link(snap_key, atom_key, "ctx:source",
                                 w=1.0, author=aid)

            self.cortex.add_to_set(set_name, snap_key)
            written += 1

        return {
            "type":    "lens:flatten",
            "into":    set_name,
            "written": written,
        }
