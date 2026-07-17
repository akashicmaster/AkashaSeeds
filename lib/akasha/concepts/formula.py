"""
Formula Concept Model — the BASE for "materials + operations + ordered process".

A formula is a small structural universe: a root, a set of **materials** (with
quantities), the **operations** applied to them, an ordered **process** of steps,
plus notes, presentation, and **specs** (constraints / targets). Two capabilities
make it more than a list: a **property rollup** (accumulate any per-material
property, weighted by quantity — cost, mass, calories, VOC, CO₂ …) and **axis-driven
suggestion** (dimensional tags are cross-formula membership sets, retrieved by
weighted intersection — the composite `cross_query` idea applied to a catalogue).

The same structure serves many domains — cooking (`recipe`, which extends this),
pigment/dye mixing, perfume, cosmetics, and process-industry / manufacturing
(materials + procedure = ISA-88's "recipe"), including cost/BOM rollup and
procurement. A domain model subclasses `FormulaConcept`, sets a few class
attributes (prefix, axes, the material-source namespace), and skins the operator
names; the graph machinery is inherited.

Operators (generic surface):
  formula.new       create a formula root (+ dimensional axis tags)
  formula.material  add a material (name, qty/unit, direct props like cost=)
  formula.op        add an operation / technique
  formula.step      append an ordered process step, crossing material × operation
  formula.source    define a material's per-basis properties (cost, density, …)
  formula.rollup    accumulate material properties (× quantity) → totals + table
  formula.spec      add a spec: a categorical hard filter OR a numeric target
  formula.view      assemble the full sheet (GUI-ready)
  formula.ls        list formulas, optionally filtered by axis
  formula.suggest   rank formulas by axis intersection; avoid= / constraints subtract

Design invariants (shared by every extension):
  • Operand-first. Materials/operations/steps are plain atoms; the operators are
    external. A new domain is a new subclass, nothing else changes.
  • Constraints are a HARD, fail-closed filter (subtract), targets are numeric
    bounds checked against the rollup — never conflated.
  • Formulas reference materials by slug/name and never stub the source namespace,
    so a later authoritative source load (e.g. USDA foods) always wins.

Topology (sets), parametrised by the subclass prefix P:
  set:P:index                       — all roots
  set:P:{id}:materials|operations|steps|notes|presentation|specs|targets
  set:P:group:{axis}:{value}        — cross-formula discrete-axis membership
  set:P:mat:{slug} / :op:{slug} / :spec:{slug}   — cross-formula component index
"""

import re
import time
import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.concepts.base import BaseConcept

# An item atom's display text is stored as "<text>⁣<lid>" — the U+2063
# INVISIBLE SEPARATOR fences a stable per-item logical id (lid) into the
# content so that two items sharing the same display text across different
# formulas never collapse into one shared, meta-clobbered atom (keys are a
# content hash). Readers strip everything from the marker on (see `_disp`).
_LID_MARK = "⁣"

logger = logging.getLogger("Harmonia.Concept.Formula")


# ── module helpers (shared by every formula-family model) ───────────────────────

def _as_list(v) -> List[str]:
    """Accept a Python list, or a comma/space/newline-separated string (CSL-friendly)."""
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    parts = str(v).replace("\n", ",").replace(" ", ",").split(",")
    return [p.strip() for p in parts if p.strip()]


def _slug(name: str) -> str:
    """Stable lower-slug used in axis set names and role aliases."""
    return re.sub(r"[^a-z0-9]+", "_", str(name or "").lower()).strip("_")


# Mass units → grams. A per-basis property rollup accumulates only over
# mass-measured materials; a count/portion unit is reported "unmeasured" until a
# source carries a per-portion weight (a future extension).
_MASS_TO_G = {"g": 1.0, "gram": 1.0, "grams": 1.0, "kg": 1000.0, "mg": 0.001,
              "oz": 28.3495, "lb": 453.592, "lbs": 453.592}


def _to_basis(qty, unit) -> Optional[float]:
    """Convert a quantity to grams using mass units only; None if not mass-measured."""
    try:
        q = float(qty)
    except (TypeError, ValueError):
        return None
    u = str(unit or "").strip().lower()
    return q * _MASS_TO_G[u] if u in _MASS_TO_G else None


# Time units → minutes (the canonical unit for step durations / critical path).
_DUR_MIN = {"min": 1.0, "m": 1.0, "minute": 1.0, "minutes": 1.0,
            "hr": 60.0, "h": 60.0, "hour": 60.0, "hours": 60.0,
            "s": 1 / 60.0, "sec": 1 / 60.0, "second": 1 / 60.0, "seconds": 1 / 60.0,
            "day": 1440.0, "d": 1440.0}


def _dur_min(amount, unit) -> Optional[float]:
    """Convert a duration to minutes; None if not numeric."""
    a = _num(amount)
    if a is None:
        return None
    return a * _DUR_MIN.get(str(unit or "min").strip().lower(), 1.0)


def _paginate(items: List[Any], limit: Any, offset: Any) -> Tuple[List[Any], Optional[str], bool]:
    """Slice a result list. `limit`=0/None → no limit (whole list). The `cursor` is an
    opaque offset; `next_cursor` is the offset to pass next, `has_more` whether more
    remain. v1-compatible: callers that omit limit/offset get the full list."""
    try:
        off = max(0, int(offset or 0))
    except (TypeError, ValueError):
        off = 0
    try:
        lim = int(limit or 0)
    except (TypeError, ValueError):
        lim = 0
    if lim <= 0:
        page = items[off:]
        return page, None, False
    page = items[off:off + lim]
    nxt = off + lim
    more = nxt < len(items)
    return page, (str(nxt) if more else None), more


def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _spec_met(actual: float, op: str, value: float) -> bool:
    if op == "<=":
        return actual <= value
    if op == ">=":
        return actual >= value
    if op == "<":
        return actual < value
    if op == ">":
        return actual > value
    return abs(actual - value) < 1e-9


# A numeric spec / target written as `<key><op><number>` — e.g. kcal<=600, cost<=5.
_SPEC_RE = re.compile(r"^\s*([a-z_][a-z0-9_]*)\s*(<=|>=|<|>|=)\s*([0-9]+(?:\.[0-9]+)?)\s*$", re.I)


class FormulaConcept(BaseConcept):
    """Materials + operations + ordered process, with property rollup and axis suggestion."""

    CONCEPT_PREFIX = "formula"
    CONCEPT_LABEL  = ("materials + operations + ordered process, with property rollup, "
                      "specs, and axis-driven suggestion")
    CONTEXT_KEY_ACTIVE = "active_formula_root"

    # ── subclass knobs ──────────────────────────────────────────────────────────
    ID_KEY    = "formula_id"                     # the id field name in results
    NOUN      = "formula"                        # human word for messages
    AXES      = ("kind", "line", "grade")        # dimensional axes (recipe overrides)
    SOURCE_NS = "material"                        # canonical component atoms: material:{slug}
    STUB_NS   = "rmaterial"                       # last-resort step-cross stub namespace
    # sub-group set suffixes
    SUF = {"material": "materials", "operation": "operations", "step": "steps",
           "note": "notes", "present": "presentation", "spec": "specs", "target": "targets",
           "measurement": "measurements"}
    # cross-formula component index tokens
    IDX = {"material": "mat", "operation": "op", "spec": "spec"}

    CONCEPT_METHODS = {
        "new":      {"op": "op_new",      "action": "write", "cli": "form.new",
                     "args": ["title"],
                     "desc": "Create a formula: formula new <title> [kind= line= grade=]"},
        "material": {"op": "op_material", "action": "write", "cli": "form.material",
                     "args": ["formula"],
                     "desc": ("Add a material: formula material <formula> name=flour "
                              "[qty=200 unit=g] [cost=0.3] [source=<id>]")},
        "op":       {"op": "op_operation", "action": "write", "cli": "form.op",
                     "args": ["formula"],
                     "desc": "Add an operation: formula op <formula> name=mix"},
        "step":     {"op": "op_step",     "action": "write", "cli": "form.step",
                     "args": ["formula"],
                     "desc": ("Append a process step: formula step <formula> text='…' "
                              "[uses=a,b] [by=mix] [dur=20 dur_unit=min] [after=0,1] [label=x]")},
        "critical": {"op": "op_critical", "action": "read", "cli": "form.critical",
                     "args": ["formula"],
                     "desc": ("Critical path over the step DAG (ES/EF/LS/LF, slack, "
                              "makespan): formula critical <formula>")},
        "source":   {"op": "op_source",   "action": "write", "cli": "form.source",
                     "args": ["name"],
                     "desc": ("Define a material's per-basis properties: formula source "
                              "name=flour cost=0.3 [basis=1]")},
        "source.search": {"op": "op_source_search", "action": "read", "cli": "form.source.search",
                          "args": [],
                          "desc": ("Search the source catalogue by name → pickable atoms: "
                                   "formula source.search q=<text> [limit=20]")},
        "rollup":   {"op": "op_rollup",   "action": "read", "cli": "form.rollup",
                     "args": ["formula"],
                     "desc": "Accumulate material properties → totals + table: formula rollup <formula>"},
        "spec":     {"op": "op_spec",     "action": "write", "cli": "form.spec",
                     "args": ["formula"],
                     "desc": ("Add a spec: formula spec <formula> value=cost<=5 (a target) | "
                              "value=<tag> (a categorical constraint)")},
        "control":  {"op": "op_control",  "action": "write", "cli": "form.control",
                     "args": ["formula"],
                     "desc": ("Add a control point: formula control <formula> param=temp "
                              "op='>=' value=75 [unit=C step=<ref> ccp=yes]")},
        "measure":  {"op": "op_measure",  "action": "write", "cli": "form.measure",
                     "args": ["formula"],
                     "desc": ("Record a measured value: formula measure <formula> param=temp "
                              "value=78 [step=<ref>]")},
        "checkpoints": {"op": "op_checkpoints", "action": "read", "cli": "form.checkpoints",
                        "args": ["formula"],
                        "desc": ("Check control specs vs measurements (CCPs, violations, "
                                 "safe): formula checkpoints <formula>")},
        "view":     {"op": "op_view",     "action": "read", "cli": "form.view",
                     "args": ["formula"],
                     "desc": "Assemble the full sheet: formula view <formula|alias>"},
        "ls":       {"op": "op_ls",       "action": "read", "cli": "form.ls",
                     "args": [],
                     "desc": "List formulas, optionally by axis: formula ls [kind= line=]"},
        "suggest":  {"op": "op_suggest",  "action": "read", "cli": "form.suggest",
                     "args": [],
                     "desc": ("Suggest by axes (intersection ranking): formula suggest "
                              "kind=x have=a,b avoid=c — avoid/constraints are a hard filter")},
    }

    # ── session / scope helpers ─────────────────────────────────────────────────

    def _author_scopes(self) -> Tuple[str, List[str]]:
        uid = getattr(self.session, "client_id", "system")
        return uid, [f"owner:user_{uid}", f"view:user_{uid}"]

    def _scopes(self) -> List[str]:
        return getattr(self.session, "active_scopes", []) or []

    def _visible(self, key: str) -> bool:
        scopes = self._scopes()
        return (not scopes) or self.cortex.check_access(key, scopes)

    def _members(self, set_name: str) -> List[str]:
        return [k for k in (self.cortex.get_collection_members(set_name) or []) if self._visible(k)]

    def _name(self, key: str) -> Optional[str]:
        aliases = self.cortex.get_aliases_by_key(key) or []
        return next((a for a in aliases if ":" in a), aliases[0] if aliases else None)

    # ── name-parametrised graph addressing ──────────────────────────────────────

    def _P(self) -> str:
        return self.CONCEPT_PREFIX

    def _index_set(self) -> str:
        return f"set:{self._P()}:index"

    def _rset(self, root: str, key: str) -> str:
        return f"set:{self._P()}:{root}:{self.SUF.get(key, key)}"

    def _axis_set(self, axis: str, value: str) -> str:
        return f"set:{self._P()}:group:{axis}:{_slug(value)}"

    def _idx_set(self, kind: str, slug: str) -> str:
        return f"set:{self._P()}:{self.IDX.get(kind, kind)}:{slug}"

    def _rel(self, verb: str) -> str:
        return f"{self._P()}:{verb}"

    # ── resolution ──────────────────────────────────────────────────────────────

    def _resolve(self, ref: str) -> Optional[str]:
        """Resolve an atom ref to a key: direct key, alias, or bare word (leaf fallback)."""
        if not ref:
            return None
        if self.cortex.get_chunk(ref) is not None:
            return ref
        key = self.cortex.resolve_alias(ref)
        if not key and ":" not in ref:
            keys = self.cortex.list_leaf(ref)
            if keys:
                key = keys[0]
        return key

    def _resolve_or_create(self, name: str, kind: str, author: str, scopes: List[str]) -> str:
        """Resolve an existing atom by alias `<kind>:<slug>`, or create a lightweight one.
        Idempotent (first-wins alias) so an ontology-provided atom is reused."""
        slug = _slug(name)
        alias = f"{kind}:{slug}"
        existing = self.cortex.resolve_alias(alias) or self._resolve(name)
        if existing:
            return existing
        key = self.cortex.put_chunk(
            content=str(name).strip(),
            meta={"type": "atom", "role": kind, "concept": self._P(), "slug": slug,
                  "created_at": time.time()},
            author=author, scopes=scopes)
        self.cortex.set_alias(key, alias)
        return key

    def _client(self) -> str:
        return getattr(self.session, "client_id", "anon")

    def _is_admin(self) -> bool:
        """True for an admin/superuser session (used for full-list pagination + gates)."""
        scopes = getattr(self.session, "active_scopes", []) or []
        return "role:superuser" in scopes or "scope:sys:admin" in scopes

    # ── idempotency (safe write retries over mobile networks) ────────────────────
    # A request_key is scoped to (client, rpc-method, key) so the SAME key on two
    # different methods can't cross-collide, and only retained for a bounded window
    # (a mobile retry storm is seconds-to-minutes; a "retry" a day later is a genuinely
    # new request, so the record is treated as expired and the write runs again).
    _IDEM_RETENTION_S = 24 * 3600

    def _idem_alias(self, method: str, request_key: str) -> str:
        return f"idem:{self._client()}:{_slug(method)}:{_slug(request_key)}"

    def _idem_hit(self, method: str, request_key: str) -> Optional[str]:
        """If this (client, method, request_key) already produced an atom WITHIN the
        retention window, return its key; else None (expired/absent → re-execute)."""
        if not request_key:
            return None
        key = self.cortex.resolve_alias(self._idem_alias(method, request_key))
        if not key:
            return None
        ts = float((self.cortex.get_meta(key) or {}).get("created_at", 0) or 0)
        if ts and (time.time() - ts) > self._IDEM_RETENTION_S:
            return None
        return key

    def _idem_record(self, method: str, request_key: str, key: str) -> None:
        if request_key and key:
            self.cortex.set_alias(key, self._idem_alias(method, request_key))

    # ── stable per-item logical id (lid) + unique item atoms ─────────────────────

    def _mint_item(self, display: str, meta: Dict[str, Any], author: str,
                   scopes: List[str], lid: str = "") -> Tuple[str, str]:
        """Create a per-formula item atom carrying a stable logical id. The lid is stored
        in meta AND fenced into the content (`display⁣lid`) so the atom is unique per item
        even when its display text repeats across formulas — and so an edit (detach +
        recreate) can carry the SAME lid forward onto a new atom key. Returns (key, lid)."""
        lid = lid or uuid.uuid4().hex[:12]
        m = dict(meta)
        m["lid"] = lid
        key = self.cortex.put_chunk(content=f"{display}{_LID_MARK}{lid}", meta=m,
                                    author=author, scopes=scopes)
        return key, lid

    @staticmethod
    def _disp(content: str) -> str:
        """The human-facing text of an item atom — everything before the lid marker
        (a shared/unfenced atom with no marker returns its whole content, stripped)."""
        return (content or "").split(_LID_MARK)[0].strip()

    def _line(self, key: str) -> str:
        return self._disp(self.cortex.get_chunk(key) or "")

    def _lid_of(self, key: str) -> str:
        return (self.cortex.get_meta(key) or {}).get("lid", "") or ""

    def _resolve_item(self, root: str, ref: str) -> Optional[str]:
        """Resolve an item handle to its current atom key: a direct atom key, or a stable
        lid matched against the formula's members (so a client that stored an id survives
        the atom-key churn of an edit)."""
        if not ref:
            return None
        # A real atom key resolves to content; a lid does not (get_meta returns {} for a
        # missing key, so test the chunk, not the meta).
        if self.cortex.get_chunk(ref) is not None:
            return ref
        for k in self._members_all(root):
            if (self.cortex.get_meta(k) or {}).get("lid") == ref:
                return k
        return ref

    # ── revision / freshness (append-only monotonic counter) ─────────────────────

    def _revlog_set(self, root: str) -> str:
        return f"set:{self._P()}:{root}:revlog"

    def _bump(self, root: str) -> int:
        """Append a monotonic revision marker. The marker set is APPEND-ONLY — markers are
        never removed, even when an edit is a detach+recreate that leaves the atom count
        unchanged — so `revision` strictly increases on every write. Each marker embeds a
        uuid, so concurrent bumps produce distinct atoms (no lost update) and revision
        advances by one per bump. This is the correct optimistic-concurrency token; the
        old parts-count `version` did not change across an in-place edit."""
        author, scopes = self._author_scopes()
        rl = self._revlog_set(root)
        mk = self.cortex.put_chunk(
            content=f"{_LID_MARK}rev:{root}:{uuid.uuid4().hex}",
            meta={"type": "atom", "role": "rev", "concept": self._P(),
                  "root": root, "created_at": time.time()},
            author=author, scopes=scopes)
        self.cortex.add_to_set(rl, mk)
        return len(self.cortex.get_collection_members(rl) or [])

    # ── version / freshness (revision + updated_at) ───────────────────────────────

    def _members_all(self, root: str) -> List[str]:
        return self._members(self._rset(root, "all"))

    def _version(self, root: str) -> Dict[str, Any]:
        """The concurrency + display token. `revision` is the monotonic write counter
        (append-only revlog — changes on EVERY write, the field to lock on). `updated_at`
        is the most recent write timestamp (for display / last-modified sync). `version`
        is the legacy parts count, kept for backward compatibility only — do NOT lock on
        it (an in-place edit leaves it unchanged)."""
        ts = 0.0
        markers = self.cortex.get_collection_members(self._revlog_set(root)) or []
        revision = len(markers)
        for k in markers:
            ts = max(ts, float((self.cortex.get_meta(k) or {}).get("created_at", 0) or 0))
        n = 0
        for k in self._members_all(root):
            n += 1
            ts = max(ts, float((self.cortex.get_meta(k) or {}).get("created_at", 0) or 0))
        return {"revision": revision, "version": n, "updated_at": round(ts, 4)}

    def _guard_version(self, root: str, expected_updated_at: Any = "",
                       expected_revision: Any = "") -> None:
        """Optimistic lock. Preferred: `expected_revision` — the monotonic counter, robust
        across in-place edits. Legacy: `expected_updated_at` — still honoured for older
        clients. If the formula has advanced past what the caller last saw, reject rather
        than silently overwrite a concurrent edit."""
        exp_rev = _num(expected_revision)
        if exp_rev is not None:
            cur = self._version(root)["revision"]
            if cur > exp_rev + 1e-9:
                raise RuntimeError(
                    f"conflict: {self.NOUN} changed since you loaded it "
                    f"(revision {cur} > expected {int(exp_rev)}). Reload and retry.")
            return
        exp = _num(expected_updated_at)
        if exp is None:
            return
        cur = self._version(root)["updated_at"]
        if cur > exp + 1e-6:
            raise RuntimeError(
                f"conflict: {self.NOUN} changed since you loaded it "
                f"(updated_at {cur} > expected {exp}). Reload and retry.")

    # ── pagination policy (v1: default 20, max 100, full list admin-only) ─────────

    def _page_limit(self, limit: Any) -> int:
        """Resolve the effective page size. Unspecified → 20; capped at 100; only an
        admin may request the whole list (limit=0)."""
        n = _num(limit)
        if n is None or str(limit).strip() == "":
            return 20
        n = int(n)
        if n <= 0:
            return 0 if self._is_admin() else 20   # full list is admin-only
        return min(n, 100)

    # ── removal / replacement (detach — orphan the immutable atom) ───────────────

    _ROLE_SUF = {"material": "material", "operation": "operation", "step": "step",
                 "hints": "hints", "presentation": "presentation",
                 "constraint": "spec", "target": "target", "measurement": "measurement"}
    _ROLE_IDX = {"material": "material", "operation": "operation", "constraint": "spec"}

    def _forget(self, root: str, key: str) -> None:
        """Detach an item from a formula: remove it from every membership set and drop the
        links to/from the root. The content-addressed atom itself is left orphaned
        (invisible everywhere); hard deletion is a separate admin/GC concern."""
        m = self.cortex.get_meta(key) or {}
        role, slug = m.get("role", ""), m.get("slug", "")
        for suf in set(self.SUF.values()):
            self.cortex.remove_from_set(f"set:{self._P()}:{root}:{suf}", key)
        self.cortex.remove_from_set(self._rset(root, "all"), key)
        for verb in ("uses", "by", "step", "hint", "plating", "spec", "target",
                     "measure", "after", "step_uses", "step_by"):
            self.cortex.remove_link(root, key, self._rel(verb))
        # Cross-index holds the ROOT; only drop it when no sibling shares this slug.
        idx = self._ROLE_IDX.get(role)
        if idx and slug:
            suf = self.SUF[self._ROLE_SUF[role]]
            siblings = [k for k in self._members(f"set:{self._P()}:{root}:{suf}")
                        if (self.cortex.get_meta(k) or {}).get("slug") == slug]
            if not siblings:
                self.cortex.remove_from_set(self._idx_set(idx, slug), root)

    def _remove_root(self, root: str) -> Dict[str, Any]:
        """Remove a formula from every index (it disappears from ls/suggest). Members are
        detached; the atoms orphan (soft delete — content-addressed store, no hard drop)."""
        for k in list(self._members_all(root)):
            if k != root:
                self._forget(root, k)
        rmeta = self.cortex.get_meta(root) or {}
        self.cortex.remove_from_set(self._index_set(), root)
        self.cortex.remove_from_set(self._rset(root, "all"), root)
        owner = rmeta.get("owner")
        if owner:
            self.cortex.remove_from_set(f"set:{self._P()}:owner:{owner}", root)
        for ax, values in (rmeta.get("axes", {}) or {}).items():
            for v in values:
                self.cortex.remove_from_set(self._axis_set(ax, v), root)
        return {"status": "removed", self.ID_KEY: root}

    def _root(self, ref: str) -> str:
        """Resolve a formula reference (id / alias / active-context) to a validated root."""
        ctx_get = getattr(self.session, "get_context", None)
        ref = ref or (ctx_get(self.CONTEXT_KEY_ACTIVE) if ctx_get else None)
        if not ref:
            raise ValueError(f"Provide a {self.NOUN} id or alias (or create/open one first).")
        root = (self.cortex.resolve_alias(ref) if ":" in str(ref) else None) or ref
        meta = self.cortex.get_meta(root) or {}
        if meta.get("concept") != self._P() or meta.get("role") != "root":
            raise ValueError(f"'{str(ref)[:24]}' is not a {self.NOUN}.")
        if not self._visible(root):
            raise ValueError(f"{self.NOUN.capitalize()} not accessible.")
        return root

    # ── source properties (the rollup hook — subclasses override) ────────────────

    def _source_props(self, line_meta: Dict[str, Any]) -> Optional[Tuple[Dict[str, float], float]]:
        """Return (per-basis property dict, basis) for a material line's source atom,
        or None. Base: resolve `{SOURCE_NS}:{slug}` (or the plain name) and read its
        `meta.props` (with `basis`, default 1). Recipe overrides this to resolve a food
        atom and read USDA nutrition (structured meta OR a "per 100g: …" content string)."""
        slug = line_meta.get("slug", "")
        src = (self.cortex.resolve_alias(f"{self.SOURCE_NS}:{slug}") if slug else None) \
            or self._resolve(line_meta.get("name", ""))
        if not src:
            return None
        sm = self.cortex.get_meta(src) or {}
        props = sm.get("props")
        if not isinstance(props, dict) or not props:
            return None
        basis = _num(props.get("basis")) or 1.0
        return ({k: v for k, v in props.items() if k != "basis"}, basis or 1.0)

    # ── property rollup (the generalisation of nutrition accumulation) ───────────

    def _rollup(self, root: str) -> Dict[str, Any]:
        """Accumulate material properties into totals + a per-material table.

        Two contributions per material:
          • direct line properties (e.g. `cost=` entered on the material line) —
            summed as-is (the cost of that line);
          • source-scaled properties — (amount / basis) × each per-basis property
            from the material's source atom (mass-measured only; degradation-first).

        Schema-agnostic: sums every numeric property present, so new fields total
        automatically. Materials with a non-mass unit are `unmeasured` (for the
        scaled part), a material with no source props `no_data`; both are reported.
        """
        totals: Dict[str, float] = {}
        per: List[Dict[str, Any]] = []
        unmeasured: List[str] = []
        no_data: List[str] = []

        for k in self._members(self._rset(root, "material")):
            m = self.cortex.get_meta(k) or {}
            name, qty, unit = m.get("name", ""), m.get("qty", ""), m.get("unit", "")
            entry: Dict[str, Any] = {"name": name, "qty": qty, "unit": unit}
            contrib: Dict[str, float] = {}

            # (1) direct line properties (e.g. cost= entered on the line) — always count.
            for pk, pv in (m.get("props") or {}).items():
                fv = _num(pv)
                if fv is None:
                    continue
                totals[pk] = round(totals.get(pk, 0.0) + fv, 4)
                contrib[pk] = round(contrib.get(pk, 0.0) + fv, 4)

            # (2) source-scaled properties (nutrition, per-basis cost, …).
            amount = _to_basis(qty, unit)
            sp = self._source_props(m)
            if amount is not None and sp:
                props, basis = sp
                factor = amount / (basis or 1.0)
                for pk, pv in props.items():
                    fv = _num(pv)
                    if fv is None:
                        continue
                    totals[pk] = round(totals.get(pk, 0.0) + fv * factor, 4)
                    contrib[pk] = round(contrib.get(pk, 0.0) + fv * factor, 4)

            # Status reflects whether the material's properties could be accounted for.
            # A material that contributed anything (scaled OR a direct prop like cost)
            # is `measured`; otherwise a non-mass unit → `unmeasured`, a mass material
            # with no source props → `no_data` (both reported, never silently dropped).
            if (amount is not None and sp) or contrib:
                entry["status"] = "measured"
            elif amount is None:
                entry["status"] = "unmeasured"
                unmeasured.append(name)
            else:
                entry["status"] = "no_data"
                no_data.append(name)

            entry["props"] = contrib
            per.append(entry)

        measured = sum(1 for e in per if e.get("status") == "measured")
        return {"totals": totals, "per_material": per, "measured": measured,
                "unmeasured": unmeasured, "no_data": no_data}

    def _specs(self, root: str, totals: Dict[str, float]) -> List[Dict[str, Any]]:
        """Read numeric targets (specs with a bound) and check each against `totals`."""
        out = []
        for k in self._members(self._rset(root, "target")):
            m = self.cortex.get_meta(k) or {}
            key, op, value = m.get("key") or m.get("nutrient"), m.get("op"), m.get("value")
            if not key:
                continue
            actual = float(totals.get(key, 0.0))
            out.append({"key": key, "op": op, "value": value, "actual": round(actual, 4),
                        "met": _spec_met(actual, op, float(value)),
                        "measurable": key in totals,
                        "ccp": bool(m.get("ccp")), "step": m.get("step") or ""})
        return out

    def _constraints(self, root: str) -> List[str]:
        return [self._name(k) or self._line(k)
                for k in self._members(self._rset(root, "spec"))]

    # ── PERT / critical path (design-time process planning) ──────────────────────

    def _critical(self, root: str) -> Dict[str, Any]:
        """Critical Path Method over the step dependency DAG.

        Forward pass gives each step its earliest start/finish (ES/EF); the backward
        pass gives latest start/finish (LS/LF); slack = LS − ES. The **critical path**
        is the zero-slack chain; **makespan** is the total duration accounting for
        parallel branches (steps with no mutual dependency overlap). Distinct from the
        JCL/Harmonia runtime `depends_on` PERT — this is design-time planning on the
        formula's own steps."""
        steps = sorted(self._members(self._rset(root, "step")),
                       key=lambda k: (self.cortex.get_meta(k) or {}).get("order", 0))
        info: Dict[str, Dict[str, Any]] = {}
        for k in steps:
            m = self.cortex.get_meta(k) or {}
            info[k] = {"key": k, "step_id": m.get("lid", ""),
                       "order": m.get("order", 0), "label": m.get("label", ""),
                       "text": self._line(k)[:80],
                       "dur": float(m.get("dur_min") or 0.0),
                       "preds": [p for p in (m.get("after") or []) if p in dict.fromkeys(steps)]}
        # Forward pass (steps are in topological order — `after` only names earlier steps).
        es: Dict[str, float] = {}
        ef: Dict[str, float] = {}
        for k in steps:
            s = info[k]
            s_es = max((ef[p] for p in s["preds"] if p in ef), default=0.0)
            es[k] = s_es
            ef[k] = s_es + s["dur"]
        makespan = max(ef.values(), default=0.0)
        # Successors + backward pass.
        succ: Dict[str, List[str]] = {k: [] for k in steps}
        for k in steps:
            for p in info[k]["preds"]:
                succ.setdefault(p, []).append(k)
        ls: Dict[str, float] = {}
        lf: Dict[str, float] = {}
        for k in reversed(steps):
            outs = succ.get(k, [])
            k_lf = min((ls[c] for c in outs if c in ls), default=makespan)
            lf[k] = k_lf
            ls[k] = k_lf - info[k]["dur"]
        rows = []
        for k in steps:
            slack = round(ls[k] - es[k], 4)
            rows.append({**{kk: info[k][kk] for kk in ("key", "step_id", "order", "label", "text", "dur", "preds")},
                         "es": round(es[k], 4), "ef": round(ef[k], 4),
                         "ls": round(ls[k], 4), "lf": round(lf[k], 4),
                         "slack": slack, "critical": abs(slack) < 1e-6})
        critical_path = [r["key"] for r in rows if r["critical"]]
        return {"steps": rows, "makespan_min": round(makespan, 4),
                "critical_path": critical_path,
                "sequential_min": round(sum(info[k]["dur"] for k in steps), 4)}

    # ── control points / HACCP (process-parameter specs + measurements) ──────────

    def _add_measurement(self, root: str, param: str, value: str,
                         step: str = "") -> Dict[str, Any]:
        """Record an observed value for a process parameter (temperature, time, pH, …),
        optionally scoped to a step. Checked against control specs by `_checkpoints`."""
        author, scopes = self._author_scopes()
        v = _num(value)
        if not param or v is None:
            raise ValueError(f"{self.NOUN}.measure requires param= and a numeric value=.")
        skey = ""
        if step:
            by_order, by_label, by_lid = self._step_indexes(root)
            skey = self._resolve_step(step, by_order, by_label, by_lid) or ""
        mkey, _lid = self._mint_item(
            f"{param}={v:g}",
            {"type": "atom", "role": "measurement", "concept": self._P(),
             "param": _slug(param), "value": v, "step": skey, "created_at": time.time()},
            author, scopes)
        self.cortex.put_link(root, mkey, self._rel("measure"), author=author)
        self.cortex.add_to_set(self._rset(root, "measurement"), mkey)
        self.cortex.add_to_set(self._rset(root, "all"), mkey)
        self._bump(root)
        return {"status": "recorded", self.ID_KEY: root, "key": mkey,
                "param": _slug(param), "value": v, "step": skey}

    def _checkpoints(self, root: str) -> Dict[str, Any]:
        """Check every target against the best available actual — a recorded measurement
        for its parameter (preferring one at the same step) if present, otherwise the
        material rollup. Targets flagged `ccp` are HACCP critical control points. A target
        with no actual is `pending`, one that violates its bound is `fail`."""
        totals = self._rollup(root)["totals"]
        # Latest measurement per (param, step) wins — order by created_at, not by the
        # set's member order, so a re-measurement (an audit trail) supersedes correctly.
        metas = sorted(((self.cortex.get_meta(mk) or {})
                        for mk in self._members(self._rset(root, "measurement"))),
                       key=lambda mm: mm.get("created_at", 0))
        meas: Dict[Tuple[str, str], float] = {}
        for mm in metas:
            p, st, v = mm.get("param", ""), mm.get("step", ""), _num(mm.get("value"))
            if v is None:
                continue
            meas[(p, st)] = v          # (param, step) — latest wins
            meas[(p, "")] = v          # param-level fallback

        rows = []
        for tk in self._members(self._rset(root, "target")):
            tm = self.cortex.get_meta(tk) or {}
            key, op, value = tm.get("key"), tm.get("op"), tm.get("value")
            if not key:
                continue
            step, ccp = tm.get("step", ""), bool(tm.get("ccp"))
            actual, source = None, "pending"
            if step and (key, step) in meas:
                actual, source = meas[(key, step)], "measured"
            elif (key, "") in meas:
                actual, source = meas[(key, "")], "measured"
            elif key in totals:
                actual, source = totals[key], "rollup"
            met = _spec_met(float(actual), op, float(value)) if actual is not None else None
            rows.append({"key": key, "op": op, "value": value, "unit": tm.get("unit", ""),
                         "step": step, "ccp": ccp, "actual": actual, "source": source,
                         "met": met,
                         "status": "pending" if met is None else ("pass" if met else "fail")})
        ccps = [r for r in rows if r["ccp"]]
        violations = [r for r in rows if r["status"] == "fail"]
        pending = [r for r in rows if r["status"] == "pending"]
        return {"checkpoints": rows, "ccps": ccps,
                "ccp_all_pass": all(r["status"] == "pass" for r in ccps) if ccps else None,
                "violations": violations, "pending": pending,
                "safe": (not violations) and all(r["status"] == "pass" for r in ccps)}

    # ── shared write helpers (used by both generic ops and subclass skins) ───────

    def _mk_root(self, title: str, axes: Dict[str, List[str]], alias: str = "") -> Dict[str, Any]:
        """Create a formula root, index it, and register its axis memberships. Idempotent
        by alias. Returns the standard created/exists result (id field = self.ID_KEY)."""
        if not title or not title.strip():
            raise ValueError(f"{self.NOUN}.new requires a title.")
        if alias:
            existing = self.cortex.resolve_alias(alias)
            if existing and (self.cortex.get_meta(existing) or {}).get("concept") == self._P():
                em = self.cortex.get_meta(existing) or {}
                return {"status": "exists", self.ID_KEY: existing,
                        "title": em.get("title", ""), "axes": em.get("axes", {})}
        author, scopes = self._author_scopes()
        root = self.cortex.put_chunk(
            content=f"[ {self.NOUN.capitalize()}: {title.strip()} ]",
            meta={"type": "concept", "concept": self._P(), "role": "root",
                  "title": title.strip(), "axes": axes, "owner": author,
                  "created_at": time.time()},
            author=author, scopes=scopes)
        self.concept_id = root
        self.set_name = f"set:concept:{root}"
        self.cortex.create_set(self._index_set())
        self.cortex.add_to_set(self._index_set(), root)
        self.cortex.add_to_set(f"set:{self._P()}:owner:{author}", root)   # per-user index (quota)
        self.cortex.add_to_set(self._rset(root, "all"), root)
        self.ensure_concept_set()
        if alias:
            self.cortex.set_alias(root, alias)
        for ax, values in axes.items():
            for v in values:
                self.cortex.add_to_set(self._axis_set(ax, v), root)
        self._bump(root)
        if hasattr(self.session, "set_context"):
            self.session.set_context(self.CONTEXT_KEY_ACTIVE, root)
        return {"status": "created", self.ID_KEY: root, "title": title.strip(),
                "axes": axes, **self._version(root)}

    def _add_material(self, root: str, name: str, qty: str = "", unit: str = "",
                      props: Optional[Dict[str, Any]] = None,
                      extra_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a material line (qty-carrying atom) + index it for suggestion."""
        author, scopes = self._author_scopes()
        slug = _slug(name)
        line = f"{name} {qty}{(' ' + unit) if unit and not qty else unit}".strip()
        meta = {"type": "atom", "role": "material", "concept": self._P(),
                "name": name, "slug": slug, "qty": str(qty), "unit": str(unit),
                "props": {k: v for k, v in (props or {}).items() if _num(v) is not None},
                "created_at": time.time()}
        meta.update(extra_meta or {})
        key, lid = self._mint_item(line or name, meta, author, scopes,
                                   lid=(extra_meta or {}).get("lid", ""))
        order = float(len(self._members(self._rset(root, "material"))))
        self.cortex.put_link(root, key, self._rel("uses"), w=order, author=author)
        self.cortex.add_to_set(self._rset(root, "material"), key)
        self.cortex.add_to_set(self._rset(root, "all"), key)
        self.cortex.add_to_set(self._idx_set("material", slug), root)
        self._bump(root)
        return {"status": "added", self.ID_KEY: root, "kind": "material",
                "key": key, "atom_key": key, "item_id": lid, "lid": lid,
                "name": name, "slug": slug}

    def _add_operation(self, root: str, name: str) -> Dict[str, Any]:
        author, scopes = self._author_scopes()
        okey = self._resolve_or_create(name, "operation", author, scopes)
        self.cortex.put_link(root, okey, self._rel("by"), author=author)
        self.cortex.add_to_set(self._rset(root, "operation"), okey)
        self.cortex.add_to_set(self._rset(root, "all"), okey)
        self.cortex.add_to_set(self._idx_set("operation", _slug(name)), root)
        self._bump(root)
        return {"status": "added", self.ID_KEY: root, "kind": "operation",
                "key": okey, "atom_key": okey, "name": name, "slug": _slug(name)}

    def _add_note(self, root: str, text: str, suffix: str, verb: str) -> Dict[str, Any]:
        author, scopes = self._author_scopes()
        key, lid = self._mint_item(
            text,
            {"type": "atom", "role": suffix, "concept": self._P(), "created_at": time.time()},
            author, scopes)
        self.cortex.put_link(root, key, verb, author=author)
        self.cortex.add_to_set(self._rset(root, suffix), key)
        self.cortex.add_to_set(self._rset(root, "all"), key)
        self._bump(root)
        return {"status": "added", self.ID_KEY: root, "kind": suffix,
                "key": key, "atom_key": key, "item_id": lid, "lid": lid}

    def _add_spec(self, root: str, value: str, step: str = "", unit: str = "",
                  ccp: bool = False) -> Dict[str, Any]:
        """A numeric bound (`cost<=5`) → a target (checked against the rollup); anything
        else → a categorical constraint (a hard, fail-closed filter for suggestion).
        `step=`/`ccp=` scope a target to a process step (used by HACCP control points)."""
        author, scopes = self._author_scopes()
        m = _SPEC_RE.match(value)
        if m:
            key, op, val = m.group(1).lower(), m.group(2), float(m.group(3))
            # Minted (per-formula) so a target with a step scope / ccp flag is never
            # clobbered by an identically-worded target in another formula.
            tkey, lid = self._mint_item(
                f"{key}{op}{val:g}{(' ' + unit) if unit else ''}",
                {"type": "atom", "role": "target", "concept": self._P(),
                 "key": key, "op": op, "value": val, "unit": str(unit),
                 "step": str(step), "ccp": bool(ccp), "created_at": time.time()},
                author, scopes)
            self.cortex.put_link(root, tkey, self._rel("target"), author=author)
            self.cortex.add_to_set(self._rset(root, "target"), tkey)
            self.cortex.add_to_set(self._rset(root, "all"), tkey)
            self._bump(root)
            return {"status": "added", self.ID_KEY: root, "kind": "target",
                    "key": tkey, "atom_key": tkey, "item_id": lid, "lid": lid,
                    "spec_key": key, "op": op, "value": val, "ccp": bool(ccp)}
        ckey = self._resolve_or_create(value, "constraint", author, scopes)
        self.cortex.put_link(root, ckey, self._rel("spec"), author=author)
        self.cortex.add_to_set(self._rset(root, "spec"), ckey)
        self.cortex.add_to_set(self._rset(root, "all"), ckey)
        self.cortex.add_to_set(self._idx_set("spec", _slug(value)), root)
        self._bump(root)
        return {"status": "added", self.ID_KEY: root, "kind": "constraint",
                "key": ckey, "name": value, "slug": _slug(value)}

    def _step_indexes(self, root: str) -> Tuple[Dict[int, str], Dict[str, str], Dict[str, str]]:
        """Build (order→key, label→key, lid→key) maps over a formula's current steps."""
        by_order: Dict[int, str] = {}
        by_label: Dict[str, str] = {}
        by_lid: Dict[str, str] = {}
        for sk in self._members(self._rset(root, "step")):
            sm = self.cortex.get_meta(sk) or {}
            by_order[sm.get("order")] = sk
            if sm.get("label"):
                by_label[sm.get("label")] = sk
            if sm.get("lid"):
                by_lid[sm.get("lid")] = sk
        return by_order, by_label, by_lid

    def _resolve_step(self, ref: str, by_order: Dict[int, str],
                      by_label: Dict[str, str],
                      by_lid: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Resolve a step reference within a formula: a stable step_id (lid), an order
        index, a step label, or a direct atom key/alias. The lid is preferred so a client
        that stored a step_id keeps a valid `after=` reference across edits."""
        ref = str(ref).strip()
        if by_lid and ref in by_lid:
            return by_lid[ref]
        if ref.isdigit() and int(ref) in by_order:
            return by_order[int(ref)]
        return by_label.get(ref) or self._resolve(ref)

    def _mk_step(self, root: str, text: str, uses: Any = None, by: Any = None,
                 dur: str = "", dur_unit: str = "min", after: Any = None, label: str = "",
                 tools: Any = None, temp: str = "", lid: str = "",
                 extra_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Append one process step and cross it with the materials/operations it touches.

        Steps form a **dependency DAG**, not just a chain: `after=` names predecessor
        steps (by stable step_id, order index, `label=`, or key); with no `after`, a step
        depends on the immediately preceding one (the linear default). Steps with no mutual
        dependency run in **parallel**. `dur=`/`dur_unit=` give the estimated duration
        (→ minutes) that `formula.critical` uses for the critical path. Never stubs the
        source namespace (a later authoritative source load wins). Returns a stable
        `step_id` (lid) that survives an edit, alongside the immutable `atom_key`."""
        if not text or not text.strip():
            raise ValueError(f"{self.NOUN}.step requires text=.")
        author, scopes = self._author_scopes()
        prior = self._members(self._rset(root, "step"))
        order = len(prior)

        # Resolve the dependency predecessors among already-created steps.
        by_order, by_label, by_lid = self._step_indexes(root)
        after_list = _as_list(after)
        preds: List[str] = []
        for ref in after_list:
            tgt = self._resolve_step(ref, by_order, by_label, by_lid)
            if tgt and tgt not in preds:
                preds.append(tgt)
        if not preds and prior:
            preds = [prior[-1]]                      # linear default: after the previous step

        tool_names = _as_list(tools)
        temp_c = _num(temp)
        meta = {"type": "atom", "role": "step", "concept": self._P(),
                "order": order, "label": str(label or ""),
                "dur_min": _dur_min(dur, dur_unit), "dur_unit": str(dur_unit or "min"),
                "tools": tool_names, "temp": temp_c,
                "after": preds, "created_at": time.time()}
        meta.update(extra_meta or {})
        step, step_lid = self._mint_item(text.strip(), meta, author, scopes, lid=lid)
        self.cortex.put_link(root, step, self._rel("step"), w=float(order), author=author)
        self.cortex.add_to_set(self._rset(root, "step"), step)
        self.cortex.add_to_set(self._rset(root, "all"), step)
        if prior:
            self.cortex.put_link(prior[-1], step, "sys:next", w=float(order), author=author)
        for p in preds:
            self.cortex.put_link(step, p, self._rel("after"), author=author)

        mat_lines = {(self.cortex.get_meta(k) or {}).get("slug"): k
                     for k in self._members(self._rset(root, "material"))}
        crossed_uses: List[str] = []
        for u in _as_list(uses):
            tgt = (mat_lines.get(_slug(u))
                   or self.cortex.resolve_alias(f"{self.SOURCE_NS}:{_slug(u)}")
                   or self._resolve_or_create(u, self.STUB_NS, author, scopes))
            self.cortex.put_link(step, tgt, self._rel("step_uses"), author=author)
            crossed_uses.append(u)
        crossed_by: List[str] = []
        for o in _as_list(by):
            okey = self._resolve_or_create(o, "operation", author, scopes)
            self.cortex.put_link(step, okey, self._rel("step_by"), author=author)
            crossed_by.append(o)
        for t in tool_names:                          # cooking tools the step uses
            tkey = self._resolve_or_create(t, "tool", author, scopes)
            self.cortex.put_link(step, tkey, self._rel("step_tool"), author=author)
        self._bump(root)
        return {"status": "added", self.ID_KEY: root, "step_id": step_lid, "lid": step_lid,
                "atom_key": step, "key": step, "order": order,
                "label": str(label or ""), "dur_min": _dur_min(dur, dur_unit),
                "temp": temp_c, "tools": tool_names,
                "after": preds, "uses": crossed_uses, "by": crossed_by}

    def _def_source(self, name: str, basis: str = "1", **props) -> Dict[str, Any]:
        """Define/refresh a material source's per-basis properties (cost, density, …).
        Stored in `{SOURCE_NS}:{slug}` meta.props; fresh values re-point the alias."""
        if not name or not name.strip():
            raise ValueError(f"{self.NOUN}.source requires a name.")
        author, scopes = self._author_scopes()
        slug = _slug(name)
        p: Dict[str, float] = {"basis": _num(basis) or 1.0}
        for pk, pv in (props or {}).items():
            fv = _num(pv)
            if fv is not None:
                p[pk] = fv
        existing = self.cortex.resolve_alias(f"{self.SOURCE_NS}:{slug}")
        if existing and len(p) <= 1:
            return {"status": "exists", "source_id": existing, "name": name.strip(),
                    "slug": slug, "props": (self.cortex.get_meta(existing) or {}).get("props")}
        key = self.cortex.put_chunk(
            content=name.strip(),
            meta={"type": "atom", "role": self.SOURCE_NS, "concept": self._P(),
                  "slug": slug, "name": name.strip(), "props": p,
                  "source": f"{self.NOUN}.source", "created_at": time.time()},
            author=author, scopes=scopes)
        self.cortex.set_alias(key, f"{self.SOURCE_NS}:{slug}", force=bool(existing))
        return {"status": "updated" if existing else "created", "source_id": key,
                "name": name.strip(), "slug": slug, "props": p}

    # ── source catalogue search (name → pickable source atoms) ───────────────────

    def _source_scan(self, query: str, cap: int = 400) -> List[Tuple[str, str]]:
        """Find source atoms (`{SOURCE_NS}:…`) whose name-alias contains every token of
        `query`, across BOTH the caller's own cortex (personal entries) AND the shared
        nucleus catalogue (the bulk, loaded universal). Returns de-duplicated
        (key, name_alias) pairs. Category / index / fdc aliases are skipped — only the
        per-item name aliases are matched, so a search resolves to a real source atom the
        caller can pin. This is the name→id bridge a client needs (users type a name; the
        rollup resolves nutrition/props by the id they then pin)."""
        tokens = [t for t in _slug(query).split("_") if t]
        if not tokens:
            return []
        pattern = f"{self.SOURCE_NS}:%" + "%".join(tokens) + "%"
        cores = []
        cortex_core = getattr(self.cortex, "core", None)
        if cortex_core is not None:
            cores.append(cortex_core)
        nuc = getattr(self.session, "nucleus", None)
        nuc_core = getattr(nuc, "core", None)
        if nuc_core is not None and nuc_core is not cortex_core:
            cores.append(nuc_core)
        seen: Dict[str, str] = {}
        skip = (f"{self.SOURCE_NS}:category:", f"{self.SOURCE_NS}:fdc:",
                f"{self.SOURCE_NS}:index:")
        for core in cores:
            for row in (core.get_aliases_by_pattern(pattern) or []):
                alias, key = row.get("alias", ""), row.get("key", "")
                if not key or alias.startswith(skip):
                    continue
                if key not in seen:
                    seen[key] = alias
                if len(seen) >= cap:
                    break
        return list(seen.items())

    def _source_name(self, key: str, alias: str) -> str:
        """A display name for a source atom: the descriptive text before a ' — …' details
        clause, else meta.name, else the alias' trailing slug humanised."""
        m = self.cortex.get_meta(key) or {}
        content = (self.cortex.get_chunk(key) or "").strip()
        head = re.split(r"\s[—–-]\s", content, 1)[0].strip() if content else ""
        return head or m.get("name") or alias.split(":")[-1].replace("_", " ")

    def _fdc_of(self, key: str) -> str:
        for a in (self.cortex.get_aliases_by_key(key) or []):
            m = re.match(rf"^{re.escape(self.SOURCE_NS)}:fdc:(\d+)$", a)
            if m:
                return m.group(1)
        return ""

    def op_source_search(self, name: str = "", q: str = "", limit: Any = "",
                         offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[formula.source.search] Search the source catalogue by name (substring, all
        tokens) → pickable source atoms with their per-basis props. `q`/`name` is the
        query; paginated (default 20, max 100). READ-level (guests may browse)."""
        query = q or name
        hits = self._source_scan(query)
        items = []
        for key, alias in hits:
            m = self.cortex.get_meta(key) or {}
            props = m.get("props") if isinstance(m.get("props"), dict) else {}
            items.append({"key": key, "name": self._source_name(key, alias),
                          "slug": m.get("slug", ""), "props": props or {}})
        items.sort(key=lambda x: x["name"].lower())
        page, nxt, more = _paginate(items, self._page_limit(limit), cursor or offset)
        return {"type": f"{self._P()}:source_search", "query": query,
                "results": page, "count": len(items),
                "next_cursor": nxt, "has_more": more}

    def _catalog_scan(self, prefix: str, cap: int = 4000) -> List[Tuple[str, str]]:
        """List catalogue atoms directly under a namespace (`<prefix>:<slug>`) across the
        caller's cortex AND the shared nucleus, de-duped. Skips deeper sub-namespaces
        (e.g. `method:category:*`) so only leaf catalogue entries come back."""
        pattern = f"{prefix}:%"
        cores = []
        cortex_core = getattr(self.cortex, "core", None)
        if cortex_core is not None:
            cores.append(cortex_core)
        nuc_core = getattr(getattr(self.session, "nucleus", None), "core", None)
        if nuc_core is not None and nuc_core is not cortex_core:
            cores.append(nuc_core)
        depth = prefix.count(":") + 1
        seen: Dict[str, str] = {}
        for core in cores:
            for row in (core.get_aliases_by_pattern(pattern) or []):
                alias, key = row.get("alias", ""), row.get("key", "")
                if not key or alias.count(":") != depth:
                    continue
                if key not in seen:
                    seen[key] = alias
                if len(seen) >= cap:
                    break
        return list(seen.items())

    # ── publication (mark a root public / official) ──────────────────────────────

    def _published_set(self) -> str:
        return f"set:{self._P()}:published"

    def _is_published(self, root: str) -> bool:
        return root in (self.cortex.get_collection_members(self._published_set()) or [])

    def _suggest(self, axis_terms: List[Tuple[str, str]], have: Any, avoid: Any,
                 mode: str, limit: int, offset: Any = 0) -> Dict[str, Any]:
        """Rank roots by weighted axis intersection; avoid= / constraints subtract (hard)."""
        positive: List[Tuple[str, str]] = []
        for ax, val in axis_terms:
            positive.append((f"{ax}={val}", self._axis_set(ax, val)))
        for h in _as_list(have):
            positive.append((f"have={h}", self._idx_set("material", _slug(h))))
        if not positive:
            raise ValueError(f"{self.NOUN}.suggest needs at least one axis or have=.")

        blocked: set = set()
        avoided = _as_list(avoid)
        for a in avoided:
            s = _slug(a)
            blocked |= set(self._members(self._idx_set("material", s)))
            blocked |= set(self._members(self._idx_set("spec", s)))

        coverage: Dict[str, List[str]] = {}
        for label, sname in positive:
            for root in self._members(sname):
                if root in blocked:
                    continue
                coverage.setdefault(root, []).append(label)

        n = len(positive)
        results = []
        for root, matched in coverage.items():
            meta = self.cortex.get_meta(root) or {}
            if meta.get("concept") != self._P() or meta.get("role") != "root":
                continue
            results.append({self.ID_KEY: root, "title": meta.get("title", ""),
                            "matched": matched, "score": round(len(matched) / n, 4),
                            "coverage": f"{len(matched)}/{n}"})
        results.sort(key=lambda x: (x["score"], x["title"]), reverse=True)
        page, nxt, more = _paginate(results, limit, offset)
        return {"type": f"{self._P()}:suggestions", "mode_applied": "retrieval",
                "axes_requested": [lbl for lbl, _ in positive], "avoided": avoided,
                "blocked_count": len(blocked), "suggestions": page,
                "count": len(results), "next_cursor": nxt, "has_more": more}

    def _ls(self, filters: List[Tuple[str, str]], limit: Any = 0,
            offset: Any = 0) -> Dict[str, Any]:
        if filters:
            sets = [set(self._members(self._axis_set(ax, v))) for ax, v in filters]
            roots = set.intersection(*sets) if sets else set()
        else:
            roots = set(self._members(self._index_set()))
        pub = set(self.cortex.get_collection_members(self._published_set()) or [])
        uid = self._client()
        items = []
        for k in roots:
            meta = self.cortex.get_meta(k) or {}
            if meta.get("concept") != self._P() or meta.get("role") != "root":
                continue
            items.append({self.ID_KEY: k, "title": meta.get("title", ""),
                          "axes": meta.get("axes", {}), "created_at": meta.get("created_at", 0),
                          "mine": meta.get("owner") == uid,
                          "published": k in pub})
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        page, nxt, more = _paginate(items, limit, offset)
        return {f"{self._P()}s": page, "count": len(items), "filters": dict(filters),
                "next_cursor": nxt, "has_more": more}

    # ── generic operators (the `formula.*` surface) ──────────────────────────────

    def op_new(self, title: str = "", alias: str = "", **axis_kwargs) -> Dict[str, Any]:
        """[formula.new] Create a formula root and tag its dimensional axes."""
        axes = {ax: _as_list(axis_kwargs.get(ax)) for ax in self.AXES}
        return self._mk_root(title, axes, alias)

    def op_material(self, formula: str = "", name: str = "", qty: str = "", unit: str = "",
                    source: str = "", **props) -> Dict[str, Any]:
        """[formula.material] Add a material (qty-carrying line). Extra numeric keyword
        args (e.g. cost=0.3) are stored as direct line properties for the rollup."""
        root = self._root(formula)
        if not name or not name.strip():
            raise ValueError("formula.material requires name=.")
        extra = {"source": source} if source else None
        return self._add_material(root, name.strip(), qty, unit,
                                  props={k: v for k, v in props.items() if _num(v) is not None},
                                  extra_meta=extra)

    def op_operation(self, formula: str = "", name: str = "") -> Dict[str, Any]:
        """[formula.op] Add an operation / technique."""
        root = self._root(formula)
        if not name or not name.strip():
            raise ValueError("formula.op requires name=.")
        return self._add_operation(root, name.strip())

    def op_step(self, formula: str = "", text: str = "", uses: Any = None, by: Any = None,
                dur: str = "", dur_unit: str = "min", after: Any = None,
                label: str = "", tools: Any = None, temp: str = "") -> Dict[str, Any]:
        """[formula.step] Append a process step, crossing material × operation. `dur=`/
        `dur_unit=` estimate its duration; `after=` names predecessor steps (order index,
        label, or key) forming the dependency DAG — omit for the linear default, use it
        for parallel branches. `tools=` names equipment the step uses; `temp=` a target
        temperature (°C). See formula.critical."""
        root = self._root(formula)
        return self._mk_step(root, text, uses, by, dur=dur, dur_unit=dur_unit,
                             after=after, label=label, tools=tools, temp=temp)

    def op_critical(self, formula: str = "", name: str = "") -> Dict[str, Any]:
        """[formula.critical] Critical Path Method over the step DAG: per-step ES/EF/LS/LF
        + slack, the zero-slack critical path, the makespan (accounting for parallel
        branches), and the naive sequential total for comparison."""
        root = self._root(formula or name)
        meta = self.cortex.get_meta(root) or {}
        c = self._critical(root)
        return {"type": f"{self._P()}:critical", self.ID_KEY: root,
                "title": meta.get("title", ""), **c}

    def op_source(self, name: str = "", basis: str = "1", **props) -> Dict[str, Any]:
        """[formula.source] Define a material's per-basis properties (cost, density, …)."""
        return self._def_source(name, basis, **props)

    def op_spec(self, formula: str = "", value: str = "", step: str = "",
                unit: str = "", ccp: str = "") -> Dict[str, Any]:
        """[formula.spec] Add a spec: a numeric bound (target) or a categorical constraint."""
        root = self._root(formula)
        if not value or not str(value).strip():
            raise ValueError("formula.spec requires value=.")
        return self._add_spec(root, str(value).strip(), step=step, unit=unit,
                              ccp=str(ccp).lower() in ("1", "yes", "true", "y"))

    def op_control(self, formula: str = "", param: str = "", op: str = ">=",
                   value: str = "", unit: str = "", step: str = "",
                   ccp: str = "") -> Dict[str, Any]:
        """[formula.control] Add a process-parameter control spec — a bound on a parameter
        (temperature, time, pH, …), optionally scoped to a step and flagged a critical
        control point: formula control <formula> param=temp op='>=' value=75 unit=C
        step=<ref> ccp=yes. Checked against measurements by formula.checkpoints."""
        root = self._root(formula)
        v = _num(value)
        if not param or v is None or op not in ("<=", ">=", "<", ">", "="):
            raise ValueError("formula.control requires param=, op= (<= >= < > =), numeric value=.")
        return self._add_spec(root, f"{_slug(param)}{op}{v:g}", step=step, unit=unit,
                             ccp=str(ccp).lower() in ("1", "yes", "true", "y"))

    def op_measure(self, formula: str = "", param: str = "", value: str = "",
                   step: str = "") -> Dict[str, Any]:
        """[formula.measure] Record an observed value for a process parameter (optionally
        at a step): formula measure <formula> param=temp value=78 [step=<ref>]."""
        return self._add_measurement(self._root(formula), param, value, step)

    def op_checkpoints(self, formula: str = "", name: str = "") -> Dict[str, Any]:
        """[formula.checkpoints] Check control specs against recorded measurements (and the
        rollup): per-target pass/fail/pending, the CCP subset, violations, and an overall
        `safe` flag."""
        root = self._root(formula or name)
        meta = self.cortex.get_meta(root) or {}
        return {"type": f"{self._P()}:checkpoints", self.ID_KEY: root,
                "title": meta.get("title", ""), **self._checkpoints(root)}

    def op_rollup(self, formula: str = "") -> Dict[str, Any]:
        """[formula.rollup] Accumulate material properties → totals + per-material table +
        target compliance."""
        root = self._root(formula)
        meta = self.cortex.get_meta(root) or {}
        acc = self._rollup(root)
        return {"type": f"{self._P()}:rollup", self.ID_KEY: root,
                "title": meta.get("title", ""), "totals": acc["totals"],
                "per_material": acc["per_material"], "measured": acc["measured"],
                "unmeasured": acc["unmeasured"], "no_data": acc["no_data"],
                "targets": self._specs(root, acc["totals"])}

    def op_view(self, formula: str = "", name: str = "") -> Dict[str, Any]:
        """[formula.view] Assemble the full sheet: materials, operations, ordered steps,
        notes, presentation, axes, constraints, a rollup summary, and targets."""
        root = self._root(formula or name)
        meta = self.cortex.get_meta(root) or {}
        materials = [{"key": k, "item_id": self._lid_of(k),
                      **{kk: (self.cortex.get_meta(k) or {}).get(kk, "")
                         for kk in ("name", "qty", "unit")},
                      "line": self._line(k)}
                     for k in self._members(self._rset(root, "material"))]
        steps = sorted(
            ({"key": k, "step_id": self._lid_of(k),
              "order": (self.cortex.get_meta(k) or {}).get("order", 0),
              "text": self._line(k),
              "uses": [d for d, _ in self.cortex.get_adjacent_links(k, self._rel("step_uses"))],
              "by":   [d for d, _ in self.cortex.get_adjacent_links(k, self._rel("step_by"))]}
             for k in self._members(self._rset(root, "step"))),
            key=lambda s: s["order"])
        operations = [{"key": k, "name": self._name(k) or self._line(k)}
                      for k in self._members(self._rset(root, "operation"))]
        notes = [self._line(k) for k in self._members(self._rset(root, "note"))]
        acc = self._rollup(root)
        return {"type": f"{self._P()}:sheet", self.ID_KEY: root, "title": meta.get("title", ""),
                "axes": meta.get("axes", {}), "materials": materials, "operations": operations,
                "steps": steps, "notes": notes, "constraints": self._constraints(root),
                "rollup": {"totals": acc["totals"], "measured": acc["measured"],
                           "unmeasured": acc["unmeasured"], "no_data": acc["no_data"]},
                "targets": self._specs(root, acc["totals"]),
                **self._version(root),
                "counts": {"materials": len(materials), "operations": len(operations),
                           "steps": len(steps)}}

    def op_ls(self, limit: Any = "", offset: Any = 0, cursor: Any = "",
              **axis_kwargs) -> Dict[str, Any]:
        """[formula.ls] List formulas, optionally filtered by discrete axis. `limit`/
        `cursor` (opaque offset) paginate; `next_cursor`/`has_more` come back. Default
        page 20, max 100; the whole list (limit=0) is admin-only."""
        filters = [(ax, axis_kwargs[ax]) for ax in self.AXES if axis_kwargs.get(ax)]
        return self._ls(filters, limit=self._page_limit(limit), offset=cursor or offset)

    def op_suggest(self, have: Any = None, avoid: Any = None, mode: str = "retrieval",
                   limit: Any = "", offset: Any = 0, cursor: Any = "",
                   **axis_kwargs) -> Dict[str, Any]:
        """[formula.suggest] Rank formulas by dimensional-axis intersection (paginated:
        default 20, max 100, full list admin-only)."""
        terms = [(ax, val) for ax in self.AXES for val in _as_list(axis_kwargs.get(ax))]
        return self._suggest(terms, have, avoid, mode, self._page_limit(limit),
                             offset=cursor or offset)

    # ── remove / update (generic) ────────────────────────────────────────────────

    def op_remove(self, formula: str = "", item: str = "",
                  expected_updated_at: Any = "", expected_revision: Any = "") -> Dict[str, Any]:
        """[formula.remove] Remove the whole formula (item omitted) or a single item
        (`item=<step_id|key>`). Detaches from every index; the immutable atom orphans."""
        root = self._root(formula)
        self._guard_version(root, expected_updated_at, expected_revision)
        if item:
            self._forget(root, self._resolve_item(root, item))
            self._bump(root)
            return {"status": "removed", self.ID_KEY: root, "item": item, **self._version(root)}
        return {**self._remove_root(root), **self._version(root)}

    def op_material_update(self, formula: str = "", item: str = "", name: str = "",
                           qty: str = "", unit: str = "", source: str = "",
                           expected_updated_at: Any = "", expected_revision: Any = "",
                           **props) -> Dict[str, Any]:
        """[formula.material.update] Replace a material line (atoms are immutable, so this
        detaches the old line and adds a new one at the end): pass the fields to change;
        omitted fields inherit the old line's values. The stable item_id is carried
        forward onto the new atom."""
        root = self._root(formula)
        self._guard_version(root, expected_updated_at, expected_revision)
        item = self._resolve_item(root, item)
        old = self.cortex.get_meta(item) or {}
        if old.get("role") != "material":
            raise ValueError("formula.material.update: item is not a material line.")
        merged_props = dict(old.get("props") or {})
        merged_props.update({k: v for k, v in props.items() if _num(v) is not None})
        lid = old.get("lid", "")
        self._forget(root, item)
        extra = {"lid": lid} if lid else {}
        if source:
            extra["source"] = source
        return self._add_material(root, name or old.get("name", ""),
                                  qty or old.get("qty", ""), unit or old.get("unit", ""),
                                  props=merged_props, extra_meta=extra or None)
