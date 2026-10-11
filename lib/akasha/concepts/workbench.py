"""
Workbench — a research bench on the shared world (world-workbench-society spec v1.0, G1).

A bench is a bounded workspace with an OBSERVATION TIME: every operation on it tees ONE observation
onto the bench's own Source Stream, so the bench's history is a replayable, append-only record (the
at_seq IS the bench's observation chronon). A CLOSED bench (created with `group=<gid>`) and its scope
+ stream live in that society's GROUP ENGINE — private to members (F53: only a member's session
resolves `scope:wb:<name>`); a public bench (no group) lives in the nucleus (not used by this track).

This module is the BASE (`WorkbenchConcept`, no CONCEPT_PREFIX → not itself registered): the bench
lifecycle ops (new/ls/info/retire/grants), the `_perform` dispatcher (grant-check → run → observe →
return), and the grant model. `bench_research.py` subclasses it as the concrete `bench` concept
(kind=research).
"""
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts._universal import UniversalConcept, slug as _uslug
from lib.akasha.concepts.source import SourceDataLayer

logger = logging.getLogger("Harmonia.Concept.Workbench")

# KIND → concrete bench subclass, populated by __init_subclass__. The registered `bench` concept
# dispatches a family op to the subclass whose KIND matches the bench atom's stored kind, so a bench
# designer plugs a new kind in without touching this file (interface contract v1).
_BENCH_KINDS: Dict[str, type] = {}

# Artifacts live OUTSIDE the store, under a protected directory (never an atom body).
_ARTIFACT_ROOT = os.path.join("data", "bench")

R_CONNECTED = "society:connected"                 # society → bench (G2.1)
R_RESP = "responsible:operator:"                  # society → agent, per operation family (G2.3)


# The bench lifecycle methods — inherited by the concrete bench concept (bench_research), which merges
# them with its family ops. Kept here so every bench kind shares one lifecycle surface.
BENCH_BASE_METHODS: Dict[str, Any] = {
    # `target: ""` opts OUT of the gate's second question (see ConceptRegistry._gate_target): this
    # op MINTS the bench the question would be about, so asking it is the resolution-vs-decision
    # mistake — it refuses every first act and admits nothing that was not already admitted. Who
    # may create a bench is step 2 on `record`, which the boundary has already asked.
    "new":    {"op": "op_new", "action": "record", "target": "",
               "desc": "Create a bench: bench.new name= kind=research [world=default] group=<gid>"},
    "ls":     {"op": "op_ls", "action": "read", "desc": "List benches: bench.ls [world=]"},
    "info":   {"op": "op_info", "action": "read",
               "desc": "Bench detail (families, clock, stream head): bench.info name="},
    "retire": {"op": "op_retire", "action": "record",
               "desc": "Retire a bench (records bench.retired; nothing deleted): bench.retire name="},
    "grants": {"op": "op_grants", "action": "read",
               "desc": "The composed grant table {agent, family}: bench.grants name="},
}


class WorkbenchConcept(UniversalConcept):
    """The workbench base — lifecycle + the observing dispatcher, and the OWNER of the `bench`
    prefix (group 4, 4.17).

    The base ops (`bench.new/ls/info/retire/grants`) are the platform's, so the platform class
    registers them under the platform prefix. They used to be registered three times — once by each
    APPLICATION bench kind (research, station, learning) that spread `BENCH_BASE_METHODS` into its
    own table — and served by whichever registered LAST by filename, which was the station. A kind
    takes its own prefix for its own family ops (the application's order); until it does, the
    registry refuses it the platform prefix and the platform's methods, and says so at boot."""

    CONCEPT_PREFIX = "bench"
    CONCEPT_METHODS: Dict[str, Any] = dict(BENCH_BASE_METHODS)

    CONCEPT_LABEL = "Workbench — a research bench on the shared world (observation time)"

    KIND: Optional[str] = None    # concrete subclass declares its kind (e.g. "research")
    _FAMILIES: tuple = ()         # the operation families a subclass exposes (for the grant table)
    # A53 item 6c — (family, op) pairs whose fn() can block for a long time (a train, a whole-pool
    # feature extract / observe run). These get a `status=running` observation BEFORE the work so
    # the bench stream shows progress, not a silent gap. Fast ops are omitted (no double record).
    _LONG_OPS: frozenset = frozenset({
        ("feature", "extract"), ("feature", "run"), ("learned", "train"),
        ("observe", "run"), ("run", "execute"),
    })

    def __init_subclass__(cls, **kwargs):
        """Register a concrete bench subclass by its KIND, so `bench.new kind=<k>` routes there and a
        family op can be delegated to the right subclass (interface contract v1)."""
        super().__init_subclass__(**kwargs)
        k = cls.__dict__.get("KIND")
        if k:
            _BENCH_KINDS[k] = cls

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _client(self) -> str:
        return getattr(self.session, "client_id", "system") or "system"

    # `_is_privileged` is GONE (ruling §5). It read the literal client id and then
    # `scope:sys:admin` / `role:librarian` out of `active_scopes` — a permission decision taken from
    # a derived scope list, in a concept model, beside the one the dispatcher had already taken. Any
    # op that reaches here has passed `gate(identity, <its declared action>)`; asking again with a
    # different rule is the second gate the ruling forbids.

    # THE GATE'S TARGET, declared rather than branched on. A `bench.*` op acts on the bench its
    # `name=` names, so that param is what step 3 of the gate is about; `wf.*` / `sweep.*` /
    # `claim.*` subclass this and spell the same thing `bench=`, so they re-declare it.
    # `ConceptRegistry._gate_target` reads the declaration at the ONE dispatch site and asks the
    # same gate a second question with it. Reads are exempt by ACTION, not by name — a bench's
    # status and its published work are guest-readable by design.
    CONCEPT_TARGET_ARG = "name"

    def gate_target(self, value: str) -> str:
        """The bench this op names, spelled the way an assignment line spells a place.

        A bench in a GROUP is `<gid>/wb:<slug>`, so the line a person already holds —
        `henri researcher on plants_lab` — reaches every bench of that lab through `_under`,
        the same way `programme on studio_ai/news_show` reaches its space. A PUBLIC bench has no
        group: it is `wb:<slug>`, its own place, reached only by a row that reaches everything
        (`admin`, `librarian`) or by a line naming it. That asymmetry is the point — a public
        bench is nucleus-resident and readable by every identity, so it is the one a stray
        `record` could otherwise reach.

        The two spellings a caller may type (`sandbox`, `wb:sandbox`) have to collapse to one
        string here, or the same person is admitted or refused by how they typed it."""
        v = str(value or "").strip()
        alias = v if v.startswith("wb:") else self._bench_alias(v)
        try:
            gid = self._bench_gid(v[3:] if v.startswith("wb:") else v)
        except Exception:                       # a bench that does not resolve is its own place
            gid = ""
        return ("%s/%s" % (gid, alias)) if gid else alias

    def _source(self) -> SourceDataLayer:
        s = getattr(self, "_source_cache", None)
        if s is None:
            s = self._source_cache = SourceDataLayer(self.session)
        return s

    def _world(self):
        """The world's AXIS — the platform's minimal world container (group 4, 4.14), not the
        application's world model, so a platform model no longer depends on an application one.
        The callers below still handle None."""
        w = getattr(self, "_world_cache", None)
        if w is None:
            from lib.akasha.concepts.world_axis import axis as _axis
            w = self._world_cache = _axis(self.session)
        return w

    @staticmethod
    def _bench_alias(name: str) -> str:
        return f"wb:{_uslug(name)}"

    @staticmethod
    def _scope_set(name: str) -> str:
        return f"scope:wb:{_uslug(name)}"

    @staticmethod
    def _stream_id(name: str) -> str:
        return f"source:stream:wb:{_uslug(name)}"

    def _bind(self, gid: str) -> None:
        """Route this concept's universal writes/reads to the bench's group engine (closed bench) or
        the nucleus (public bench). Set at the start of every op that touches a bench's atoms."""
        self._space = f"group:{gid}" if gid else ""

    def _bench_meta(self, name: str) -> Dict[str, Any]:
        return self._meta(self._bench_alias(name))

    # ── lifecycle ops ────────────────────────────────────────────────────────────
    def op_new(self, name: str, kind: str = "research", world: str = "default",
               group: str = "") -> Dict[str, Any]:
        """[bench.new] Create a bench `wb:<name>` in the society's GROUP ENGINE (closed bench, when
        group= is given) or the nucleus (public). Creates the F53 scope set `scope:wb:<name>` and the
        observation stream, and records `bench.created` on the world axis. Idempotent by alias."""
        if not name:
            raise ValueError("bench.new requires name=")
        self._bind(group)
        alias = self._bench_alias(name)
        if self._key(alias):
            return {"bench": alias, "status": "exists", "world": f"world:{world}",
                    "group": group or None}
        # The families are the KIND's, resolved from the registered subclass — NOT self._FAMILIES.
        # The registry serves `bench.new` from whichever bench concept won registration (last by
        # filename), which may not be the kind being created; a learning bench created through the
        # research handler must still record the LEARNING families. `_BENCH_KINDS[kind]` is that map.
        kind = kind or self.KIND or "bench"
        subclass = _BENCH_KINDS.get(kind, type(self))
        families = list(getattr(subclass, "_FAMILIES", ()) or self._FAMILIES)
        _w = self._world()
        tick = _w.op_tick(reason="env", ref=alias, world=world) if _w else {}   # a world coordinate
        key = self._mk(alias, f"[{alias}] {kind} bench",
                       {"concept": "bench", "kind": kind, "name": name,
                        "families": families, "world": world, "group": group or None,
                        "owner": self._client(),
                        "created_cronon": tick.get("cronon"), "created_wall": tick.get("wall"),
                        "status": "active"})
        self._add_to_set(self._scope_set(name), key)          # the F53 scope root (member-resolvable)
        self._add_to_set("set:bench:index", key)              # per-space bench registry (bench.ls)
        # the observation stream lives in the SAME space (member-only for a closed bench). Pass the
        # FULL stream id so it is kept verbatim (a bare id would be slugged, dropping the colon).
        self._source().op_stream_create(id=self._stream_id(name), source=alias,
                                        rule="bench observation stream",
                                        space=(f"group:{group}" if group else ""))
        # record on the world axis (env), outside the bench's own space (the axis is world-level)
        if _w:
            _w.op_env_record(kind="bench.created", ref=alias, note=name, world=world)
        return {"bench": alias, "status": "created", "kind": kind or self.KIND or "bench",
                "world": f"world:{world}", "group": group or None,
                "scope": self._scope_set(name), "stream": self._stream_id(name),
                "created_cronon": tick.get("cronon")}

    def op_ls(self, world: str = "") -> Dict[str, Any]:
        """[bench.ls] List benches (public + any the caller's group memberships expose). A bench that
        is not for the public lives in its group, so a caller outside it never resolves it."""
        rows = []
        seen = set()

        def _collect():
            for k in self._members("set:bench:index"):
                m = self._meta(k)
                a = self._alias(k)
                if a and a not in seen and (not world or m.get("world") == world):
                    seen.add(a)
                    rows.append({"bench": a, "kind": m.get("kind"), "world": m.get("world"),
                                 "group": m.get("group"), "status": m.get("status")})
        # PUBLIC benches (nucleus, guest-readable) FIRST, then group benches whose scope the caller
        # resolves. The nucleus pass is what lets a guest (no groups) see the public benches at all.
        self._bind("")
        _collect()
        for gid in list(getattr(self.session, "group_engines", {}) or {}):
            self._bind(gid)
            _collect()
        self._bind("")
        return {"benches": rows, "count": len(rows)}

    def op_info(self, name: str, group: str = "") -> Dict[str, Any]:
        """[bench.info] A bench's families, clock, group, stream head and grant summary."""
        gid = group or self._bench_gid(name)
        self._bind(gid)
        m = self._bench_meta(name)
        if not m:
            raise ValueError(f"unknown bench '{name}'")
        stream = self._stream_id(name)
        obs = self._source().op_stream(stream=stream, limit=1,
                                       space=(f"group:{gid}" if gid else ""))
        head = obs.get("count")
        out = {"bench": self._bench_alias(name), "kind": m.get("kind"), "world": m.get("world"),
               "group": m.get("group"), "families": m.get("families") or [],
               "status": m.get("status"), "created_cronon": m.get("created_cronon"),
               "stream": stream, "observations": head,
               # The last summary this bench stamped, if it stamps any. It is here because the
               # DRIVER wants it for its run-end line and the driver is platform: reading it used
               # to mean importing a user concept module by name, which is the import direction
               # step 2 §5 closes. A bench that stamps nothing answers {} — no caller branches on
               # what kind of bench it is.
               "last_metrics": m.get("last_metrics") or {}}
        # Seed A §1.3 (L5) — `programmes` is how many workloads on THIS bench declare `effect:
        # publish`: the intersection of two `set:wl:*` memberships, which provisioning derives from
        # the declarations. It replaced `if m["kind"] == "station"` walking a station registry —
        # a test for what the bench is CALLED standing in for a fact the declaration states, so a
        # research bench that published could never report one and a station that stopped
        # publishing would still report four. Every bench answers now, from the same two Sets.
        try:
            # Read the Sets in the UNIVERSAL space where provisioning writes them: this concept is
            # bound to the bench's GROUP while answering, and a group-bound read does not see them.
            _sp, self._space = getattr(self, "_space", ""), ""
            try:
                _pub = set(self._members("set:wl:effect:publish") or [])
                _mine = set(self._members("set:wl:bench:%s" % _uslug(name)) or [])
            finally:
                self._space = _sp
            out["programmes"] = len(_pub & _mine)
        except Exception as exc:                   # noqa: BLE001 — reported, never silent
            logger.warning("[bench] info programmes FAILED bench=%s reason=%s: %s",
                           name, type(exc).__name__, exc)
            out["programmes"] = 0
        return out

    def op_retire(self, name: str, group: str = "") -> Dict[str, Any]:
        """[bench.retire] Mark a bench retired (records `bench.retired` on the world axis). Nothing is
        deleted — the record of the bench and its observations stands."""
        gid = group or self._bench_gid(name)
        self._bind(gid)
        m = self._bench_meta(name)
        if not m:
            raise ValueError(f"unknown bench '{name}'")
        self._set_meta(self._key(self._bench_alias(name)), "status", "retired")
        _w = self._world()
        _w and _w.op_env_record(kind="bench.retired", ref=self._bench_alias(name),
                                    note=name, world=m.get("world") or "default")
        return {"bench": self._bench_alias(name), "status": "retired"}

    def op_grants(self, name: str, group: str = "") -> Dict[str, Any]:
        """[bench.grants] The composed grant table {agent, family} — the agents holding
        `responsible:operator:<family>` in a society that is `society:connected` to this bench (G2.3)."""
        gid = group or self._bench_gid(name)
        self._bind(gid)
        bench = self._bench_alias(name)
        if not self._key(bench):
            raise ValueError(f"unknown bench '{name}'")
        grants = self._composed_grants(name, gid)
        return {"bench": bench, "grants": grants, "count": len(grants)}

    # ── the grant model (G2.3) ─────────────────────────────────────────────────────
    def _bench_gid(self, name: str) -> str:
        """The bench's TRUE home group, read from the bench atom's declared `group` meta — '' for a
        PUBLIC bench (ruling D: it lives in the nucleus). We must NOT infer this from "which engine
        resolves the alias": a group engine's reads UNION the nucleus, so a public bench would look
        closed in every group and its ops would wrongly write member-only. Resolve the bench atom
        (from any accessible engine) and trust its stored group."""
        alias = self._bench_alias(name)
        # A pure QUERY: probing engines rebinds _space, so restore the caller's binding before
        # returning — otherwise `_perform` (which calls this to get the gid) would leave fn() writing
        # to the last-probed group engine instead of the space the op bound (member-only writes on a
        # public bench, invisible on read).
        saved = getattr(self, "_space", "")
        try:
            for gid in list(getattr(self.session, "group_engines", {}) or {}):
                self._bind(gid)
                if self._key(alias):
                    return self._meta(alias).get("group") or ""
            self._bind("")
            return (self._meta(alias).get("group") or "") if self._key(alias) else ""
        finally:
            self._space = saved

    @staticmethod
    def _link_dst_rel(l):
        """A group-engine core returns adjacency as dicts {dst, rel} (society.py convention); some
        engines return (dst, rel) tuples. Normalise to (dst, rel)."""
        if isinstance(l, dict):
            return l.get("dst"), l.get("rel")
        if isinstance(l, (list, tuple)) and len(l) >= 2:
            return l[0], l[1]
        return None, None

    @staticmethod
    def _conn_index(name: str) -> str:
        """The nucleus reverse-index of societies connected to a PUBLIC bench (society.connect writes
        it). A public bench lives in the nucleus while its governing society lives in a group, so the
        society→bench link cannot be found from the bench side without this index."""
        return f"set:bench:{_uslug(name)}:societies"

    def _society_core(self, sgid: str):
        """The core a society's links/agents live in — its group engine (a society is always on a
        group). None when the caller is not a member of that group."""
        if not sgid:
            return self._read_core() or getattr(self.cortex, "core", None)
        try:
            return self._group_engine(sgid).core
        except Exception:
            return None

    def _society_connections(self, name: str, gid: str, bench_key: str) -> List[tuple]:
        """(society_key, society_gid) pairs `society:connected` to this bench. A CLOSED bench (gid set)
        reads its own group's `societies:<gid>` and keeps those with the outgoing link; a PUBLIC bench
        (gid '') reads the nucleus reverse-index, since its societies live in their own groups."""
        out: List[tuple] = []
        if not bench_key:
            return out
        if gid:
            rc = self._society_core(gid)
            try:
                for sk in (rc.get_collection_members(f"societies:{gid}") or []) if rc else []:
                    for l in rc.get_adjacent_links(sk) or []:
                        dst, rel = self._link_dst_rel(l)
                        if rel == R_CONNECTED and dst == bench_key:
                            out.append((sk, gid)); break
            except Exception:
                pass
            return out
        saved = getattr(self, "_space", "")
        self._space = ""
        try:
            for pk in self._members(self._conn_index(name)):
                m = self._meta(self._alias(pk) or pk)
                if m.get("concept") == "bench_conn" and m.get("society_key") and m.get("gid"):
                    out.append((m["society_key"], m["gid"]))
        except Exception:
            pass
        finally:
            self._space = saved
        return out

    def _composed_grants(self, name: str, gid: str) -> List[Dict[str, Any]]:
        """{agent, agent_key, family, gid} for every `responsible:operator:<family>` link from a
        connected society — read from EACH society's own group engine (closed and public alike)."""
        bench_key = self._key(self._bench_alias(name))
        grants: List[Dict[str, Any]] = []
        for skey, sgid in self._society_connections(name, gid, bench_key):
            core = self._society_core(sgid)
            if core is None:
                continue
            try:
                for l in core.get_adjacent_links(skey) or []:
                    dst, rel = self._link_dst_rel(l)
                    if rel and rel.startswith(R_RESP):
                        al = (core.get_aliases_by_key(dst) or [None])[0]
                        grants.append({"agent": al, "agent_key": dst, "family": rel[len(R_RESP):],
                                       "gid": sgid})
            except Exception:
                pass
        return grants

    # kept as a thin alias — some callers (workflow provenance) only need the society keys
    def _connected_societies(self, gid: str, bench_key: str) -> List[str]:
        name = getattr(self, "_grant_name", "")
        return [s for s, _ in self._society_connections(name, gid, bench_key)]

    # `_grant_ok` (G2.3) is GONE (ruling §5). `responsible:operator:<family>` was a permission
    # table of its own, kept in the graph, consulted by the bench door and by nothing the gate could
    # see. `_composed_grants` survives BELOW as what it always really was — a READ, the answer
    # `bench.grants` prints — and decides nothing.

    # `_is_own_agent` is GONE with `_grant_ok` above — it is the cast-ownership check wearing a
    # bench's clothes. Provisioning runs as `admin` (one authority, order §1), so every cast belongs
    # to admin and this test refused the programme's own bench ops: two gates disagreeing.

    # ── the observing dispatcher (G1.1) ────────────────────────────────────────────
    @staticmethod
    def _digest(args: Dict[str, Any]) -> str:
        try:
            return hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()[:16]
        except Exception:
            return ""

    def _perform(self, name: str, family: str, op: str, args: Dict[str, Any], fn):
        """The ONLY door onto a bench (interface contract v1): (1) run `fn`; (2) tee ONE
        observation to the bench stream {agent, cast, family, op, args_digest, result_ref, sim_pos,
        branch, driver, run}; (3) return `fn`'s result + {observed_at_seq}. An exception in `fn` is
        recorded as a FAILED observation and re-raised as the op's error (never an unlogged path).

        The grant check that stood at (1) is GONE (ruling §5). Every op that reaches this door came
        through `gate(identity, <the op's declared action>)` at the dispatcher; `family` is now what
        it reads as — the STREAM this observation belongs to, not a permission."""
        gid = self._bench_gid(name)
        # A53 item 6c — for a LONG op (a train / feature-extract / whole-pool observe run), tee a
        # `status=running` observation BEFORE the blocking work, so the bench stream (and the driver
        # reading it) shows work-in-progress instead of a silent multi-minute gap that reads as a
        # wedge. The finalise observation (ok / failed) is written after, as before. Fast ops are not
        # marked (it would double every record) — only the known-long families.
        if (family, op) in self._LONG_OPS:
            self._observe(name, gid, family, op, args, {"status": "running"})
        try:
            result = fn()
        except Exception as exc:
            self._observe(name, gid, family, op, args, {"status": "failed", "error": str(exc)},
                          failed=True)
            raise
        obs_seq = self._observe(name, gid, family, op, args, result)
        out = dict(result) if isinstance(result, dict) else {"result": result}
        out["observed_at_seq"] = obs_seq
        return out

    def _observe(self, name: str, gid: str, family: str, op: str, args: Dict[str, Any],
                 result: Any, failed: bool = False) -> Optional[int]:
        """Append ONE observation to the bench stream — source_metadata {agent, cast, family, op,
        args_digest, result_ref, sim_pos, branch, driver, run, status}. The at_seq (nucleus
        source:clock) IS the chronon. `driver`/`run` come from the acting context (auto-run stamps
        them via args); a failed op is recorded as an observation too (never a gap)."""
        rid = None
        if isinstance(result, dict):
            for k in ("id", "hyp", "evidence", "proof", "note", "bound", "atom", "key"):
                if result.get(k):
                    rid = result.get(k)
                    break
        # A53 item 6c — honour an explicit `status=running` marker (the pre-op tee); otherwise the
        # usual ok/failed. A running marker carries no result_ref (nothing produced yet).
        _status = "failed" if failed else "ok"
        if not failed and isinstance(result, dict) and result.get("status") == "running":
            _status = "running"
        # G4 §1.5b — `mode` (execution|thought) on every bench observation; default execution for every
        # existing/normal op. A thought act (wf.advance mode=thought, rewind, branch, plan revision)
        # passes mode=thought.
        mode = args.get("mode") or "execution"
        rec = {"agent": self._client(), "cast": args.get("cast"), "family": family, "op": op,
               "args_digest": self._digest(args), "result_ref": rid,
               "sim_pos": args.get("sim_pos"), "branch": args.get("branch"),
               "driver": args.get("driver") or getattr(self, "_driver", None),
               "run": args.get("run") or getattr(self, "_run", None),
               "mode": mode, "status": _status}
        # §2 item 3 / GUI §11 — a thought-lab act carries an `act` on its observation: {declared, judged}
        # rendered as TWO chips (the missing one is `unclassified`), `by` the acting agent. The page reads
        # this inline shape; the two clock Sets (set:<bench>:act:{declared,judged}) are the queryable side.
        _act = args.get("act")
        if isinstance(_act, dict):
            rec["act"] = {"declared": _act.get("declared"), "judged": _act.get("judged"),
                          "by": _act.get("by") or ("agent:%s" % self._client())}
        try:
            r = self._source().op_stream_append(stream=self._stream_id(name), records=[rec],
                                                space=(f"group:{gid}" if gid else ""))
            at_seq = r.get("at_seq")
            self._locate_observation(name, gid, at_seq, mode, args)
            return at_seq
        except Exception as exc:
            logger.debug("[bench] observation tee skipped for %s.%s: %s", family, op, exc)
            return None

    def _locate_observation(self, name: str, gid: str, at_seq: Optional[int], mode: str,
                            args: Dict[str, Any]) -> None:
        """G4 §1.7 — the observation atom is a MEMBER of (a) the bench coordinate it mints
        (`cronon:wb:<bench>:c<at_seq>` — one coordinate per record, today's at_seq) AND (b) the CURRENT
        world coordinate (no tick), so "what did every bench do while the world stood at c12" is a Set
        intersection. When the op is a plan step, the bench coordinate points back to the plan with ONE
        `cronon:executes` (mode=execution) or `cronon:rehearses` (mode=thought) link to the entry KEY
        (§1.5/§1.5b — the KEY, so a later entry replacement never rewrites history). Best-effort."""
        if not at_seq:
            return
        try:
            self._bind(gid)
            balias = self._bench_alias(name)                   # wb:<bench> — the bench clock name
            okey = self._key("%s:obs:%s" % (self._stream_id(name), at_seq))
            if not okey:
                return
            # The coordinate ATOMS + membership + plan links are UNIVERSAL (nucleus) timing/structure
            # metadata — a coordinate Set holds opaque KEYS (the private observation content stays in
            # the bench's group engine). Writing them in the nucleus keeps every clock readable from one
            # space with no cross-engine link, and the coordinate leaks only "something happened here".
            _prev_space = getattr(self, "_space", "")
            self._space = ""
            try:
                _cid = self._cronon_locate(balias, int(at_seq), okey)   # (a) bench coordinate
                # §1.5b — one bench coordinate has exactly one MODE; stamp it on the coordinate so the
                # ordered timeline distinguishes rehearsal from execution without reading the (private)
                # member content.
                if self._key(_cid):
                    self._set_meta(self._key(_cid), "mode", mode)
                try:                                               # (b) the CURRENT world coordinate
                    wseq = self._akasha_peek("world:default")
                    if wseq:
                        self._add_to_set("cronon:world:default:c%d" % int(wseq), okey)
                except Exception:
                    pass
                ek = args.get("plan_entry_key")                    # (c) executes / rehearses → entry KEY
                if ek:
                    rel = "cronon:rehearses" if mode == "thought" else "cronon:executes"
                    self._link("cronon:%s:c%d" % (balias, int(at_seq)), ek, rel)
            finally:
                self._space = _prev_space
        except Exception as exc:
            logger.debug("[bench] observation locate skipped for %s: %s", name, exc)

    # ── acts (seeds-14 §2 item 3 — shared across every lab port) ───────────────────
    def _act(self, name: str, gid: str, obs_seq: Optional[int], kind: str = "") -> Optional[str]:
        """Record an ACT on the bench clock: where a person or an LLM acts (reads, annotates, submits,
        compares, revises, decides), the act is TWO memberships that never overwrite each other. The
        OBSERVATION at `obs_seq` carries the inline `act {declared, judged, by}` the page reads (§11); this
        joins that observation to `set:<bench>:act:declared` AND `set:<bench>:act:judged` — the two clock
        memberships (declared = the claim was made; judged = it has a verdict slot, `null` until judged).
        Both persist; neither overwrites the other. Best-effort; never fails the op."""
        if not obs_seq:
            return None
        try:
            self._bind(gid)
            balias = self._bench_alias(name)
            okey = self._key("%s:obs:%s" % (self._stream_id(name), obs_seq))   # the observation atom
            if not okey:
                return None
            self._add_to_set("set:%s:act:declared" % balias, okey)   # membership 1 — declared (the claim)
            self._add_to_set("set:%s:act:judged" % balias, okey)     # membership 2 — judged (the verdict slot)
            return self._alias(okey) or okey
        except Exception as exc:
            logger.debug("[bench] act record skipped for %s.%s: %s", name, kind, exc)
            return None

    def ensure_public_bench(self, name: str, kind: str, world: str = "default",
                            by: str = "") -> str:
        """PUBLIC (group 4, 4.16; `_ensure_public_bench` kept one seed). Ensure a PUBLIC bench (nucleus) named `name` of `kind` exists, creating it idempotently. A
        thought-lab notebook lives in the nucleus so the lab stays guest-readable exactly as before the
        port (no group = no member-only visibility). Returns the bench alias.

        **A creation LOGS ITSELF, naming the hook that asked** (`by=`). This is the single place a
        public bench comes into existence, and it used to come into existence silently: two benches
        (`wb:plants_lab`, `wb:studio_shelf`) appeared between two deploys with no line in either log
        saying which path made them, so the checkpoint could not tell a provisioning hook from an
        operator step. A bench is a durable, guest-visible object; it does not appear anonymously.
        An idempotent no-op stays silent — only the transition is news."""
        alias = self._bench_alias(name)
        saved = getattr(self, "_space", "")
        self._bind("")
        try:
            if not self._key(alias):
                self.op_new(name=name, kind=kind, world=world, group="")
                logger.info("[bench] new %s kind=%s world=%s by=%s", alias, kind, world,
                            by or "unnamed_caller")
            return alias
        finally:
            self._space = saved

    # ── artifacts + identity atoms (interface contract v1) ─────────────────────────

    _ensure_public_bench = ensure_public_bench     # the old spelling, kept ONE seed (4.16)

    def _artifact_dir(self, run: str, name: str = "") -> str:
        """A per-run artifact directory under data/bench/<name>/artifacts/<run>/ (PROTECTED_PATHS —
        NEVER an atom body). Created on demand. `name` defaults to the last bench this concept touched."""
        bench = _uslug(name or getattr(self, "_bench_name", "") or "bench")
        path = os.path.join(_ARTIFACT_ROOT, bench, "artifacts", _uslug(str(run)) or "run")
        try:
            os.makedirs(path, exist_ok=True)
        except OSError:
            pass
        return path

    def _identity_atom(self, alias: str, meta: Dict[str, Any]) -> str:
        """Mint an identity atom (sha256 / size / path / provenance). A46(1) — an identity atom is
        immutable PER FILE: it must always describe the exact artifact it names. When the alias already
        exists with a DIFFERENT sha256/size (the weights file was overwritten by a re-train), a plain
        idempotent-by-alias mint would leave the OLD identity pointing at a file that no longer matches.
        So this REPLACES on a sha/size change — a new content-addressed identity atom, the alias
        re-pointed, the old kept and linked `bench:superseded_by` (history reachable) — and is a no-op
        when the sha/size is unchanged. Lives in the active space (the bench's engine for a closed
        bench)."""
        m = dict(meta or {})
        m.setdefault("concept", "bench_identity")
        m.setdefault("immutable", True)
        # The MINTED content folds in the file fingerprint (sha/size) so a changed file yields a NEW
        # content-addressed key — content addressing is what makes the identity immutable PER FILE.
        _fp = "%s:%s" % (m.get("weights_sha256") or m.get("sha256") or "",
                         m.get("weights_size") or m.get("size") or "")
        content = "%s\n#identity %s" % (m.get("content") or f"[{alias}] identity", _fp)
        old_meta = self._meta(alias) if self._key(alias) else {}
        key, changed, old_key = self._mk_replace(
            alias, content, m,
            compare_meta=("weights_sha256", "weights_size", "sha256", "size"))
        if old_key:
            self._link(alias, old_key, "bench:superseded_by")
            def _sh(d):
                return str(d.get("weights_sha256") or d.get("sha256") or "")[:8] or "?"
            logger.info("[bench] identity superseded alias=%s old=%s new=%s",
                        alias, _sh(old_meta), _sh(m))
        return key
