"""
Cronon Concept Model — cronon.*

Cronon is a PRIMITIVE OPERAND: a discrete unit/position in Akasha Time (Labo World-Model Directive
§1.1). It is **not** a scheduler, event, workflow phase, execution instruction, timer, or control
loop.

    "Cronon is a unit of Akasha Time, not a unit of execution.
     Execution may synchronize on Akasha Time; Akasha Time executes nothing."

A Cronon MUST NOT execute a job, decide whether time may advance, call a Society/role, contain
Harmonia scheduling logic, define its own wall-clock duration, or encode domain transition
semantics. Those belong to Harmonia (execution), Workflow (transition semantics) and Society
(interpretation). This model only ALLOCATES coordinates and records EXTERNAL temporal mappings —
temporal relativity is a projection property (§1.2): the same cronon may map, per observing system,
to milliseconds, hours, years, a historical interval, or a logical simulation interval; the mapping
is external to the Cronon.

Ops: `cronon.now` (read the current position), `cronon.mint` (allocate the next coordinate as an
addressable operand), `cronon.map` (attach an external-time mapping), `cronon.at` (read a coordinate
+ its mappings). The monotonic clock is shared with the whole Labo layer (see `_universal`).
"""
import logging
from typing import Any, Dict

from lib.akasha.concepts._universal import UniversalConcept, slug as _uslug

logger = logging.getLogger("Harmonia.Concept.Cronon")

R_FOLLOWS  = "cronon:follows"    # cronon τ → τ-1 (the Akasha-Time order; a coordinate relation, not execution)
R_MAPS_TO  = "cronon:maps_to"    # cronon → an external temporal frame/value (mapping is external to Cronon)
R_AT       = "cronon:at"         # an event atom → the cronon it is located at (used by the Labo layer)


class CrononConcept(UniversalConcept):
    """The Akasha-Time coordinate primitive. Passive: it locates time, it never advances execution."""

    CONCEPT_PREFIX = "cronon"
    CONCEPT_LABEL = "Cronon — a position in Akasha Time (a coordinate, NOT a scheduler)"

    CONCEPT_METHODS: Dict[str, Any] = {
        "now":  {"op": "op_now", "action": "read",
                 "desc": "The current Akasha-Time position (a coordinate; nothing is executed). [clock=]"},
        "mint": {"op": "op_mint", "action": "record",
                 "desc": "Allocate the next Akasha-Time coordinate as an addressable operand "
                         "(cronon:c<n>, or cronon:<clock>:c<n> for a named clock). [clock=]"},
        "map":  {"op": "op_map", "action": "record",
                 "desc": "Attach an EXTERNAL temporal mapping to a cronon (1 cronon → ms/hours/years/interval)."},
        "at":   {"op": "op_at", "action": "read",
                 "desc": "Read one cronon: its position, external-time mappings, and what is located at it."},
        "ls":   {"op": "op_ls", "action": "read",
                 "desc": "List minted cronons in Akasha-Time order. [clock=]"},
        # G4 §2.2 — the generic ordered renderer (rows by coordinate position) + the two reverse-link
        # readers the shipped macros wrap. Coordinate = Set, so these are pure Set/link reads.
        "timeline": {"op": "op_timeline", "action": "read",
                     "desc": "A clock's coordinates in order, each with its members (the generic ordered "
                             "renderer): cronon.timeline clock=<world:default|wb:<bench>|wf:<bench>:<branch>> "
                             "[from=] [to=]"},
        "executions": {"op": "op_executions", "action": "read",
                       "desc": "The bench coordinates that executed/rehearsed a plan position: "
                               "cronon.executions bench=<b> branch=<w> [pos=] [mode=execution|thought|all]"},
        "sync.between": {"op": "op_sync_between", "action": "read",
                         "desc": "world ↔ bench coordinate pairs joined by cronon:sync: "
                                 "cronon.sync.between [world=default] [bench=]"},
        # B3 §A8 — effectivity: what holds at a chronon coordinate under a set of conditions (and a
        # role's visible scope). Pure Set intersection; stores nothing. The `effective.at` macro wraps it.
        "effective_at": {"op": "op_effective_at", "action": "read",
                         "desc": "What is in effect at a chronon coordinate (or range) under conditions: "
                                 "cronon.effective_at bench=<b> chronon=<c|a..b> [cond=k=v,k=v] [role=] "
                                 "[society=<gid>/<name>]"},
        # B3 §A8 — validity: an atom that EXPIRES joins set:valid:until:<clock>:<pos> at write time (the
        # nightly retention sweep evicts it from the horizon once the clock passes <pos>; the store is
        # never touched). This is the ONE writer that also indexes the validity Set (set:valid:until:all).
        "valid_until": {"op": "op_valid_until", "action": "record",
                        "desc": "Mark an atom valid until a clock position (joins the validity membrane): "
                                "cronon.valid_until id=<atom> clock=<clock> pos=<n>"},
    }

    # ── B3 §A8 — validity membrane ────────────────────────────────────────────────
    @staticmethod
    def _valid_set(clock: str, pos: Any) -> str:
        return "set:valid:until:%s:%s" % (_uslug(clock), int(pos))

    @staticmethod
    def _valid_index_alias(clock: str, pos: Any) -> str:
        return "valid:until:%s:%s" % (_uslug(clock), int(pos))

    # ── clock-aware id helpers (G0.1) ────────────────────────────────────────────
    @staticmethod
    def _cid(seq: int, clock: str = "") -> str:
        """A cronon coordinate id: `cronon:c<n>` on the default clock, `cronon:<clock>:c<n>` on a
        named clock (so the shared `world:default` axis coordinates never collide with the default)."""
        return f"cronon:c{seq}" if not clock else f"cronon:{clock}:c{seq}"

    @staticmethod
    def _all_set(clock: str = "") -> str:
        return "cronon:all" if not clock else f"cronon:{clock}:all"

    def op_now(self, clock: str = "") -> Dict[str, Any]:
        """The current Akasha-Time position — a read of a monotonic coordinate (it does not advance
        time; time advances only when an event allocates the next coordinate). `clock=` reads a named
        clock (default: the shared clock)."""
        clk = self._key(self._clock_alias(clock))
        seq = int((self.cortex.get_meta(clk) or {}).get("at_seq", 0)) if clk else 0
        return {"cronon": seq, "clock": clock or "default",
                "note": "a position in Akasha Time — a coordinate, not an execution step"}

    def op_mint(self, label: str = "", clock: str = "") -> Dict[str, Any]:
        """Allocate the NEXT Akasha-Time coordinate as an addressable operand — `cronon:c<n>` on the
        default clock, `cronon:<clock>:c<n>` on a named clock (G0.1). Minting allocates a coordinate;
        it triggers no execution and calls no Society (§1.1, §1.3). `cronon:follows` chains per clock."""
        seq = self._akasha_now(clock)
        cid = self._cid(seq, clock)
        meta = {"concept": "cronon", "position": seq, "label": label, "clock": clock or "default",
                "minted_wall": self._now_wall(), "mappings": []}
        self._mk(cid, f"[{cid}] Akasha-Time position {seq}" + (f" — {label}" if label else ""), meta)
        self._add_to_set(self._all_set(clock), self._key(cid))
        prev = self._cid(seq - 1, clock)
        if seq > 1 and self._key(prev):
            self._link(cid, prev, R_FOLLOWS)
        return {"cronon": cid, "position": seq, "clock": clock or "default", "label": label or None}

    def op_map(self, cronon: str, frame: str, value: str) -> Dict[str, Any]:
        """Record an EXTERNAL temporal mapping for a cronon: `frame` (the observing system, e.g.
        'wall_clock' / 'historical' / 'simulation_step' / 'geological') → `value`. The mapping lives
        OUTSIDE the Cronon's meaning — the same coordinate may carry many mappings at different
        resolutions (temporal relativity, §1.2)."""
        k = self._key(cronon)
        if not k:
            raise ValueError(f"unknown cronon '{cronon}' — cronon.mint it first")
        m = self.cortex.get_meta(k) or {}
        if m.get("concept") != "cronon":
            raise ValueError(f"'{cronon}' is not a cronon")
        mappings = list(m.get("mappings") or [])
        mappings.append({"frame": frame, "value": value})
        self._set_meta(k, "mappings", mappings)
        # record the mapping as a link too, so the frame is diveable
        self._link(cronon, f"timeframe:{frame}", R_MAPS_TO)
        return {"cronon": self._alias(k), "frame": frame, "value": value, "mappings": mappings}

    def op_at(self, cronon: str) -> Dict[str, Any]:
        """Read one cronon: its Akasha-Time position, external-time mappings, and the event atoms
        located at it. H2 — location IS membership of the coordinate Set (`_cronon_locate`); the legacy
        incoming `cronon:at` links are unioned in only for pre-G4 stores whose coordinate has not been
        migrated yet, so the read is correct whether or not the migration window is closed."""
        cid = self._alias(self._key(cronon)) or cronon
        k = self._key(cronon)
        if not k:
            raise ValueError(f"unknown cronon '{cronon}'")
        m = self.cortex.get_meta(k) or {}
        located = [self._alias(mk) or mk for mk in self._members(cid)]   # coordinate = Set (§1.7)
        _seen = set(located)
        for a, r in self._links_incoming(k):     # legacy pre-G4 links (migration window not yet closed)
            if r == R_AT and a not in _seen:
                located.append(a); _seen.add(a)
        return {"cronon": self._alias(k), "position": m.get("position"),
                "mappings": m.get("mappings") or [], "label": m.get("label") or None,
                "located_here": located}

    def op_ls(self, limit: int = 100, clock: str = "") -> Dict[str, Any]:
        """List minted cronons (addressable coordinates) in Akasha-Time order, on the given clock
        (default: the shared clock)."""
        rows = []
        for k in self._members(self._all_set(clock)):
            m = self.cortex.get_meta(k) or {}
            rows.append({"cronon": self._alias(k), "position": m.get("position"),
                         "label": m.get("label") or None, "mappings": len(m.get("mappings") or [])})
        rows.sort(key=lambda r: r.get("position") or 0)
        return {"cronons": rows[:max(1, int(limit))], "count": len(rows), "clock": clock or "default"}

    def _bind_group(self, group: str) -> None:
        """G4 — cronon COORDINATE atoms + membership are UNIVERSAL (nucleus) timing/structure metadata
        even for a closed bench (a coordinate Set holds opaque keys; the private content stays in the
        bench's group engine), so a clock read never needs to bind to a group. `group=` is accepted for
        forward-compatibility but ignored — reads span the nucleus like any universal read."""
        return

    def op_timeline(self, clock: str = "", from_: Any = None, to: Any = None, group: str = "",
                    **kw) -> Dict[str, Any]:
        """[cronon.timeline] G4 §2.2 — a clock's coordinates in order (by position), each row
        `{pos, id, when, members:[{id, kind, ref, note, mode}]}`; a tick-only coordinate is a row with
        no members (the gaps the old world.axis dropped). `when` is the coordinate's wall_clock mapping
        (a plan/branch coordinate has none → `—`). Pure Set reads — a coordinate is a Set. `group=` reads
        a closed bench's clock from its group engine."""
        clock = str(clock or "").strip()
        self._bind_group(group)
        lo = self._pos(kw.get("from") if kw.get("from") is not None else from_)
        hi = self._pos(to)
        rows = []
        for ck in self._members(self._all_set(clock)):
            cm = self._meta(self._alias(ck)) or {}
            pos = int(cm.get("position") or 0)
            if (lo is not None and pos < lo) or (hi is not None and pos > hi):
                continue
            cid = self._alias(ck)
            when = "—"
            for mp in (cm.get("mappings") or []):
                if mp.get("frame") == "wall_clock":
                    when = mp.get("value"); break
            members = []
            for mk in self._members(cid):
                mm = self._meta(self._alias(mk) or mk) or {}
                members.append({"id": self._alias(mk), "kind": mm.get("kind") or mm.get("concept"),
                                "ref": mm.get("ref") or mm.get("exec"),
                                "note": mm.get("note"),
                                "mode": (mm.get("source_metadata") or {}).get("mode") or mm.get("mode")})
            rows.append({"pos": pos, "id": cid, "when": when, "mode": cm.get("mode"),
                         "members": members, "count": len(members)})
        rows.sort(key=lambda r: r.get("pos") or 0)
        return {"clock": clock or "default", "timeline": rows, "count": len(rows)}

    @staticmethod
    def _pos(x: Any) -> Any:
        if x is None or str(x).strip() == "":
            return None
        s = str(x).strip()
        if s.isdigit():
            return int(s)
        if ":c" in s and s.rsplit(":c", 1)[-1].isdigit():
            return int(s.rsplit(":c", 1)[-1])
        return None

    def op_executions(self, bench: str = "", branch: str = "", pos: Any = None,
                      mode: str = "execution", group: str = "") -> Dict[str, Any]:
        """[cronon.executions] G4 §3.3 — the bench coordinates that `cronon:executes` (mode=execution),
        `cronon:rehearses` (mode=thought) or either (mode=all) a plan position (or the whole branch),
        ordered by bench position — "how many times, and when, was this rehearsed / carried out". The
        links point bench-coordinate → plan position, so this reads the plan position's INCOMING links."""
        if not bench:
            raise ValueError("cronon.executions requires bench=")
        self._bind_group(group)
        # S2-i — the bench/wf coordinate namespace is keyed by the SLUGGED bench name (`_write_entry`
        # and `_locate_observation` both use `_uslug(name)`), so slug here too: a caller passing the raw
        # bench name (`plants-vision`) must resolve to the same clock as the stored `plants_vision`
        # coordinates, else the plan coordinates read empty and every execution reads count=0.
        name = _uslug(bench[3:] if str(bench).startswith("wb:") else bench)   # the wf clock (slugged)
        branch = branch or "main"
        rels = {"execution": ("cronon:executes",), "thought": ("cronon:rehearses",),
                "all": ("cronon:executes", "cronon:rehearses")}.get(mode, ("cronon:executes",))
        p = self._pos(pos)
        # gather plan-entry keys: one plan coordinate cronon:wf:<name>:<branch>:p<pos>, or every one on
        # the branch (its `…:all` set). Each coordinate's members are the entry + its revisions.
        plan_coords = ["cronon:wf:%s:%s:p%d" % (name, branch, p)] if p is not None else \
            [self._alias(ck) for ck in self._members("cronon:wf:%s:%s:all" % (name, branch))]
        entry_keys = set()
        for coord in plan_coords:
            for mk in self._members(coord):
                entry_keys.add(mk)
        rows, seen = [], set()
        for pk in entry_keys:
            for src, rel in self._incoming(pk):
                if rel in rels and src not in seen:
                    seen.add(src)
                    sm = self._meta(self._alias(src) or src) or {}
                    rows.append({"coordinate": self._alias(src), "pos": int(sm.get("position") or 0),
                                 "mode": "thought" if rel == "cronon:rehearses" else "execution"})
        rows.sort(key=lambda r: r.get("pos") or 0)
        return {"bench": "wb:%s" % name, "branch": branch, "mode": mode,
                "executions": rows, "count": len(rows), "considered": len(rows)}

    def op_sync_between(self, world: str = "default", bench: str = "",
                        group: str = "") -> Dict[str, Any]:
        """[cronon.sync.between] G4 §3.3 — world ↔ bench coordinate pairs joined by `cronon:sync`,
        ordered by world position. The link points world-coordinate → bench-coordinate. `group=` also
        reads a closed bench's engine (a dispatch stores its sync link there)."""
        want = ("wb:%s" % bench) if (bench and not str(bench).startswith("wb:")) else bench
        rows, seen = [], set()
        # coordinates + sync links are UNIVERSAL (nucleus); the composite spans them. The link points
        # world-coordinate → bench-coordinate.
        for ck in self._members(self._all_set("world:%s" % world)):
            cid = self._alias(ck)
            wm = self.cortex.get_meta(ck) or {}
            for dst, rel in self.cortex.get_adjacent_links(ck, "cronon:sync"):
                bc = self._alias(dst) or dst
                if want and want not in str(bc):
                    continue
                key = (cid, bc)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"world": cid, "world_pos": int(wm.get("position") or 0), "bench": bc})
        rows.sort(key=lambda r: r.get("world_pos") or 0)
        return {"world": world, "bench": bench or None, "pairs": rows, "count": len(rows)}

    @staticmethod
    def _crange(chronon: Any) -> "tuple":
        """Parse a chronon= into (lo, hi) positions. Accepts a coordinate alias
        (`cronon:wb:<b>:c88`), a bare position (`88`), or a range `88..90` (either end a coord or int).
        A single value → (n, n); an open range keeps the missing end None."""
        s = str(chronon or "").strip()
        if ".." in s:
            a, b = s.split("..", 1)
            return CrononConcept._pos(a), CrononConcept._pos(b)
        p = CrononConcept._pos(s)
        return p, p

    def op_effective_at(self, bench: str = "", chronon: str = "", cond: str = "",
                        role: str = "", society: str = "", group: str = "") -> Dict[str, Any]:
        """[cronon.effective_at] B3 §A8 — what is IN EFFECT at a chronon coordinate (or range) on a
        bench, narrowed by conditions and (optionally) a role's visible scope. A pure Set intersection —
        stores nothing, returns `{set, members[{alias}], count}` like a lens read:

          (1) the chronon coordinate's range Set — the records located at `cronon:wb:<bench>:c<n>`
              (a range `a..b` unions the coordinates in it, as `timeline` does);
          (2) ∩ each `cond:` Set named in `cond=` (`k=v,k=v` → `set:wb:<b>:cond:<k>:<v>`);
          (3) ∩ the role's visible Set (`set:cap:visible:<society>:<role>`, the Set B5 writes) when
              `role=` is given and the society resolves; absent → no restriction.

        Guest-readable on a public bench."""
        if not bench:
            raise ValueError("effective.at requires bench=")
        if not str(chronon).strip():
            raise ValueError("effective.at requires chronon=")
        self._bind_group(group)
        b = _uslug(bench[3:] if str(bench).startswith("wb:") else bench)
        clock = "wb:%s" % b
        lo, hi = self._crange(chronon)
        # (1) the coordinate range → union of member keys
        result = None
        coords_used: list = []
        for ck in self._members(self._all_set(clock)):
            cm = self._meta(self._alias(ck)) or {}
            pos = int(cm.get("position") or 0)
            if (lo is not None and pos < lo) or (hi is not None and pos > hi):
                continue
            cid = self._alias(ck)
            coords_used.append(cid)
            result = (result or set()) | set(self._members(cid))
        if result is None:
            result = set()
        constraints = ["chronon"]
        # (2) each cond: facet Set narrows the set
        for tok in str(cond or "").replace(";", ",").split(","):
            tok = tok.strip()
            if "=" not in tok:
                continue
            k, v = tok.split("=", 1)
            result &= set(self._members("set:wb:%s:cond:%s:%s" % (b, _uslug(k.strip()), _uslug(v.strip()))))
            constraints.append("cond:%s=%s" % (k.strip(), v.strip()))
        # (3) the role's visible Set (B5); absent → no restriction
        role_applied = False
        if role:
            vis = self._visible_set(bench, role, society, b)
            if vis and self._members(vis):
                result &= set(self._members(vis))
                role_applied = True
                constraints.append("role:%s" % role)
        members = sorted({self._alias(mk) or mk for mk in result})
        return {"bench": "wb:%s" % b, "chronon": chronon, "coordinates": coords_used,
                "cond": cond or None, "role": (role or None) if role_applied else None,
                "constraints": constraints, "members": [{"alias": a} for a in members],
                "count": len(members)}

    def op_valid_until(self, id: str = "", clock: str = "", pos: Any = None,
                       group: str = "") -> Dict[str, Any]:
        """[cronon.valid_until] B3 §A8 — mark an atom as valid until position `pos` on `clock`: join it to
        the validity membrane `set:valid:until:<clock>:<pos>` and register that membrane in the index
        `set:valid:until:all` (one atom `valid:until:<clock>:<pos>` carrying {clock, pos}) so the nightly
        retention sweep can enumerate the membranes without a store scan. Nothing else changes at write;
        the atom stays fully in the store — expiry only evicts it from the horizon later."""
        self._bind_group(group)
        k = self._key(id)
        if not k:
            raise ValueError("cronon.valid_until: unknown atom '%s'" % id)
        try:
            p = int(pos)
        except (TypeError, ValueError):
            raise ValueError("cronon.valid_until requires an integer pos=")
        if not str(clock).strip():
            raise ValueError("cronon.valid_until requires clock=")
        self._add_to_set(self._valid_set(clock, p), k)
        ialias = self._valid_index_alias(clock, p)
        ikey = self._mk(ialias, "[%s] validity membrane" % ialias,
                        {"concept": "validity_membrane", "clock": clock, "pos": p})
        self._add_to_set("set:valid:until:all", ikey)
        return {"status": "valid_until", "id": id, "clock": clock, "pos": p,
                "set": self._valid_set(clock, p)}

    def _visible_set(self, bench: str, role: str, society: str, bslug: str) -> str:
        """B3/B5 — resolve the role's visible-Set name `set:cap:visible:<gid>:<sname>:<role>`. `society`
        may be given explicitly (`gid/name` or `gid:name`); otherwise it is read from the bench atom's
        `society_sid` (stamped at provisioning). No society resolvable → '' (no restriction)."""
        sid = str(society or "").strip()
        if not sid:
            sid = str((self._meta("wb:%s" % bslug) or {}).get("society_sid") or "")
        if not sid:
            return ""
        parts = sid.replace("/", ":").split(":")
        key = ":".join(_uslug(p) for p in parts if p)
        return "set:cap:visible:%s:%s" % (key, _uslug(role))

    def _meta_from(core, key: str) -> Dict[str, Any]:
        """Meta for `key` read from a SPECIFIC backend core (used when a coordinate lives in the
        nucleus but the reading concept is bound elsewhere). Never raises."""
        import json as _json
        try:
            row = core.get_chunk_raw(key)
            return (_json.loads(row["meta"]) if row and row.get("meta") else {}) or {}
        except Exception:
            return {}

    def _incoming(self, key: str):
        """(src_key, rel) pairs pointing AT this atom — across both backend cores (link adjacency does
        not span the nucleus through the composite for incoming edges)."""
        out = []
        cores = []
        for c in (self._read_core(), getattr(self.cortex, "core", None),
                  (self._nuc.core if self._nuc else None)):
            if c is not None and c not in cores:
                cores.append(c)
        for core in cores:
            try:
                for link in core.get_incoming_links(key):
                    src = link.get("src") if isinstance(link, dict) else None
                    rel = link.get("rel") if isinstance(link, dict) else None
                    if src:
                        out.append((src, rel))
            except Exception:
                pass
        return out

    def _links_incoming(self, key: str):
        """(src_alias, rel) pairs pointing AT this atom — scanned via the bridge of adjacency both
        ways (get_adjacent_links unions in/out for a nucleus atom)."""
        out = []
        for dst, r in self.cortex.get_adjacent_links(key):
            out.append((self._alias(dst), r))
        return out
