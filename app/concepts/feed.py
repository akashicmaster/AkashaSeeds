"""
Live-Telemetry Concept Model (`feed`) — dynamic facts → atoms, crossed on space·time.

The world is full of dynamic facts with a place and a time (a wildfire now, a quake a minute ago, the
ISS overhead). This model continuously maps those live facts to ordinary atoms — auto-fetched from
public keyless feeds, placed in SPACE (a `geo:cell:` patch) and TIME (a bucketed timestamp), and
provenance-fenced (`provenance="telemetry"`) so they never teach the learned ontology. Once they are
atoms, concept models operate them like any other atom — read, track, and (the payoff) CROSS: several
feeds projected onto the SAME geo grid reveal coincidences (the ISS over an active wildfire cell) the
way `gen.cross` reveals corroborated boundaries — nothing collapsed, singletons kept.

Operand shape (§1 of the spec):
  feed:<id>              a registered source + schedule + field mapping
  entity:<feed>:<extid>  a STABLE subject (event / quake / satellite) — by (feed, external id)
  obs:<entity>:<bucket>  a CHANGING observation — content-addressed by (subject, time-bucket) = idempotent
  kind:<domain>:<type>   the telemetry taxonomy (kind:seismic:quake …)
  geo:cell:<gid>         the shared substrate every feed crosses on (default 1° grid)

Relations: obs:of (obs→subject), obs:from (obs→feed), obs:at (obs→geo cell), feed:tracks (feed→subject),
sys:is_a (obs→kind). The stable-subject / changing-observation split is the point: identity stays
stable, trajectories fall out (order a subject's obs by time), re-fetches are idempotent.

CLI-first: every op is `feed.*`; batch is `feed.ingest` (RPC) with a CLI single form `feed.pull`.
Live HTTP runs off-web; `feed.pull id= text=<raw json>` / `io.ingest model=feed` feed it offline.
Spec: docs/for-llm/live-telemetry-atoms-spec.md. Handoff: docs/handoff/live-telemetry-atoms-foundation.md.
"""

import hashlib
import json
import logging
import re
import time as _time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.api.concepts import BaseConcept
from lib.akasha.api.concepts import ImportableMixin

logger = logging.getLogger("Harmonia.Concept.Feed")

_W, _R = "record", "read"
_PROV = "telemetry"                 # the ASI06 provenance fence value (excluded from learn/gap/ontology)
_DAY_PREFIX = "telemetry:day:"      # A48.1 — per-day membership collection: evict iterates the day, not the store


def _day_of(iso: str) -> str:
    """The UTC day (YYYY-MM-DD) for a telemetry write — the observation's own ISO time when present,
    else today. Used for the write-time day-membership collection (A48.1)."""
    s = str(iso or "")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return _time.strftime("%Y-%m-%d", _time.gmtime())
_DEFAULT_GRID = 1.0                 # degrees — a coarse 1° lat/lon cell; low precision by design
_DEFAULT_TRUST = 0.6
_UA = "AkashaLiveFeed/0.1 (+https://github.com/henrigrohmann/AkashicTree)"

# ── F55 §1 — demo retention + cadence policy (memory-discipline R5) ──────────────────────────────
# Telemetry is DEMO operation for now: it need not be captured frequently, and anything from an
# earlier day may be DELETED (the maintainer's ruling — in a REAL-measurement deployment, raise the
# retention and COMPACT to daily summaries like pulse, rather than hoard raw rows). Both values are
# DEPLOYMENT policy, tunable by env, NOT experiment toggles:
#   • the cadence FLOOR bounds how often a feed is even eligible to write (demo ≈ once per hour), so
#     a 60 s ISS feed no longer appends per minute;
#   • the retention window (keep=today) is enforced by a writer-side nightly job that HARD-drops
#     (drop_chunk, full C2 eviction) every telemetry atom older than the window — soft-eviction alone
#     (removing set membership while the atom stays resident) is what let 131k rows accumulate.
_MIN_INTERVAL_ENV     = "AKASHA_FEED_MIN_INTERVAL"
_KEEP_DAYS_ENV        = "AKASHA_TELEMETRY_KEEP_DAYS"
_DEFAULT_MIN_INTERVAL = 3600        # demo cadence floor (s); AKASHA_FEED_MIN_INTERVAL=0 disables it
_DEFAULT_KEEP_DAYS    = 1           # retention window in days (1 = keep today only); AKASHA_TELEMETRY_KEEP_DAYS
_GC_DEFAULT_BUDGET    = 20000       # atoms dropped per feed.gc pass (bounded; the job re-enters until clean)

# retain= parses as a rolling time WINDOW ("72h" / "48h" / "30m" / "2d") or an integer COUNT/subject.
_DUR = re.compile(r"^\s*(\d+)\s*([smhd])\s*$", re.I)
_DUR_MULT = {"s": 1, "m": 60, "h": 3600, "d": 86400}


class FeedConcept(BaseConcept, ImportableMixin):
    """Live-telemetry operators over the feed/entity/obs/kind operands + the geo·time anchors."""

    CONCEPT_PREFIX = "feed"

    # io.ingest model=feed into=<feed id>: NORMALISED records → subjects + observations. Each record is
    # {raw_id, lat, lon, [alt], [mag], [mag_unit], [t], [title], [kind]}. lat+lon required.
    IMPORT_SCHEMA = {
        "model": "feed", "requires": ["lat", "lon"], "prefers": ["raw_id", "t", "kind", "mag"],
        "min_nodes": 1,
        "description": "Normalised telemetry samples → observation atoms on stable subjects, placed on "
                       "the geo grid + time-bucketed. into=<feed id>.",
    }

    CONCEPT_METHODS = {
        "register": {"op": "op_register", "action": _W, "cli": "feed.register", "args": ["id"],
                     "desc": "Declare a live source + schedule + field mapping: feed.register id=<slug> "
                             "kind=kind:<domain>:<type> [interval=300] [retain=72h|200] url='…' "
                             "map='items=$.features; id=$.id; lat=$.geometry.coordinates[1]; …'"},
        "pull":     {"op": "op_pull", "action": _W, "cli": "feed.pull", "args": ["id"],
                     "desc": "Fetch ONE cycle now (the scheduler calls this): feed.pull id=<feed> "
                             "[text=<raw json, offline>] [path=<file>] [retain=]"},
        "ingest":   {"op": "op_ingest", "action": _W, "cli": "feed.ingest", "args": ["id"],
                     "desc": "Batch-ingest NORMALISED records (RPC form): feed.ingest id=<feed> records=<json>"},
        "feeds":    {"op": "op_feeds", "action": _R, "cli": "feed.feeds", "args": [],
                     "desc": "List registered feeds + last pull + counts: feed.feeds"},
        "due":      {"op": "op_due", "action": _R, "cli": "feed.due", "args": [],
                     "desc": "List feeds DUE for a pull (interval elapsed since the newest observation) "
                             "— the scheduler's policy input (feed.tick submits a LOW-priority JCL pull "
                             "per due feed): feed.due [at=<ISO>]"},
        "latest":   {"op": "op_latest", "action": _R, "cli": "feed.latest", "args": ["id"],
                     "desc": "The most recent observations from a feed: feed.latest id=<feed> [n=20]"},
        "track":    {"op": "op_track", "action": _R, "cli": "feed.track", "args": ["subject"],
                     "desc": "A subject's ordered trajectory (the moving-point path): feed.track "
                             "subject=<entity> [since=<ISO>] [n=]"},
        "cell":     {"op": "op_cell", "action": _R, "cli": "feed.cell", "args": ["gid"],
                     "desc": "Everything observed in a geo cell / time window (a point-on-the-globe as "
                             "an atom): feed.cell gid=<gid> [window=6h] [at=<ISO>]"},
        "cross":    {"op": "op_cross", "action": _R, "cli": "feed.cross", "args": [],
                     "desc": "THE cross — overlay feeds on the shared geo grid → coincidences (≥2 feeds "
                             "in a cell) vs singletons: feed.cross [window=6h] [feeds=<a,b>] [at=<ISO>]"},
        "project":  {"op": "op_project", "action": _R, "cli": "feed.project", "args": [],
                     "desc": "The read-only projection payload for archives: feed.project "
                             "[mode=map|cross|track] [window=6h] [subject=<entity>]"},
        "trace":    {"op": "op_trace", "action": _R, "cli": "feed.trace", "args": ["id"],
                     "desc": "A projection object → its source atom (reversibility): feed.trace id=<alias/key>"},
        "gc":       {"op": "op_gc", "action": _W, "cli": "feed.gc", "args": [],
                     "desc": "HARD retention sweep (F55): drop telemetry atoms older than the window "
                             "(keep=today by default), full C2 eviction, bounded per pass: "
                             "feed.gc [keep=<days>] [limit=<max drops>]. Nightly writer job + backlog drain."},
    }

    # The built-in PUBLIC feeds a live deployment auto-provisions (the kernel registers these at boot
    # on a cell that carries the feeds workloads, so real-time telemetry needs ZERO manual setup). Only feeds whose
    # map-DSL matches the REAL keyless API live here — verified against the actual responses. The
    # richer demo (aircraft / sea level / ships) is offline-only in app/scripts/live_lab.py until those
    # real-API maps are wired (OpenSky returns positional arrays; NOAA CO-OPS is per-station; AIS
    # needs a key). Single source of truth: scripts/live_lab + live_setup import this.
    DEFAULT_FEEDS = [
        {"id": "eonet", "kind": "kind:disaster:event", "interval": 1800, "retain": "72h",
         # days=30 + limit=200 keep the payload small & fast: the bare ?status=open response is
         # hundreds of KB (every open event's full geometry history) and streams so slowly it blows
         # the fetch timeout — no observation ever lands. days=30 restricts to events active in the
         # last 30 days (= current disasters, exactly what fold=latest/stamp=now want), limit caps it.
         "url": "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=30&limit=200",
         "title": "NASA EONET — natural-disaster events",
         # fold=latest → one point per open event (its most recent footprint, not every historical
         # footprint = no 3000-point flood); stamp=now → an OPEN event is a fact as of THIS pull, so
         # the live map shows active disasters in-window (and last_pull reflects fetch time, not the
         # old footprint date). Both are config-as-data tokens — no eonet special-casing in code.
         "map": ("items=$.events; id=$.id; title=$.title; geom=$.geometry; "
                 "glat=$.coordinates[1]; glon=$.coordinates[0]; gt=$.date; fold=latest; stamp=now")},
        {"id": "usgs_eq", "kind": "kind:seismic:quake", "interval": 300, "retain": "48h",
         "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
         "title": "USGS — earthquakes (past hour)",
         "map": ("items=$.features; id=$.id; lat=$.geometry.coordinates[1]; lon=$.geometry.coordinates[0]; "
                 "t=$.properties.time; mag=$.properties.mag; title=$.properties.title")},
        {"id": "iss", "kind": "kind:orbit:satellite", "interval": 60, "retain": "6h",
         "url": "https://api.wheretheiss.at/v1/satellites/25544",
         "title": "ISS (ZARYA) — live position",
         "map": "items=$; id=$.id; lat=$.latitude; lon=$.longitude; alt=$.altitude; t=$.timestamp"},
    ]

    # ── identity / minting helpers ────────────────────────────────────────────
    def _author(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _scopes(self) -> List[str]:
        a = self._author()
        return [f"owner:user_{a}", f"view:user_{a}"]

    def _pub_nucleus(self):
        """The SHARED nucleus telemetry is published to. Telemetry is PUBLIC shared data (scope:sys:universal,
        exactly like proto-words / ontology), so every session — a public GUEST included — reads it through
        the composite's nucleus merge. Who may write it is the GATE's answer to the op (`feed.pull` /
        `feed.ingest` / `feed.gc` are record-class ops on the `telemetry` id-set), asked before this handler
        runs; the handler tests no role and no scope string."""
        return getattr(self.cortex, "_nucleus", None)

    def _resolve(self, ref: str) -> Optional[str]:
        ref = (ref or "").strip()
        if not ref:
            return None
        return self.cortex.resolve_alias(ref) or (ref if self.cortex.get_chunk(ref) else None)

    def _alias_of(self, key: str) -> str:
        try:
            al = self.cortex.get_aliases_by_key(key) or []
        except Exception:
            al = []
        pref = ("feed:", "entity:", "obs:", "kind:", "geo:cell:")
        return next((a for a in al if a.startswith(pref)), (al[0] if al else key))

    def _mint(self, alias: str, content: str, meta: Dict[str, Any], sets: Tuple[str, ...] = (),
              refresh: bool = False) -> str:
        """Idempotent by alias: reuse the atom if the alias resolves, else create + alias it. PUBLIC
        telemetry writes to the shared nucleus (scope:sys:universal); a private (non-privileged) feed
        writes to the local guarded cortex. `refresh` updates config meta (observations are immutable →
        never refreshed)."""
        nuc = self._pub_nucleus()
        author = self._author()
        if nuc is not None:                               # PUBLIC — shared nucleus (like proto-words)
            core = nuc.core
            key = core.get_key_by_alias(alias)
            if not key:
                key = hashlib.sha256((content or alias).encode("utf-8")).hexdigest()
                core.put_chunk_raw(key, content, json.dumps(meta, ensure_ascii=False),
                                   author, "verified", _time.time())
                core.put_chunk_access(key, ["scope:sys:universal"])
                try:
                    core.put_alias(key, alias)
                except Exception:
                    pass
            elif refresh:
                try:
                    core.merge_meta(key, dict(meta))
                except Exception:
                    pass
            for s in sets:
                try:
                    core.add_to_collection(s, key)
                except Exception:
                    pass
            return key
        # PRIVATE — the caller's own guarded cell (owner-scoped)
        key = self.cortex.resolve_alias(alias)
        if not key:
            key = self.cortex.put_chunk(content=content, meta=meta, author=author, scopes=self._scopes())
            try:
                self.cortex.set_alias(key, alias)
            except Exception:
                pass
        elif refresh:
            for mk, mv in meta.items():
                try:
                    self.cortex.set_meta(key, mk, mv)
                except Exception:
                    pass
        for s in sets:
            try:
                self.cortex.add_to_set(s, key)
            except Exception:
                pass
        return key

    def _link(self, src: str, dst: str, rel: str) -> None:
        if not (src and dst):
            return
        nuc = self._pub_nucleus()
        try:
            if nuc is not None:                           # public link lives in the shared nucleus
                nuc.core.put_link_raw(src, dst, rel, w=1.0, author=self._author(), status="verified")
            else:
                self.cortex.put_link(src, dst, rel, author=self._author())
        except Exception:
            pass

    def _delset(self, name: str, key: str) -> None:
        """Remove a member from a live set — from the nucleus (public) or the local cell (private)."""
        nuc = self._pub_nucleus()
        try:
            if nuc is not None:
                nuc.core.remove_from_collection(name, key)
            else:
                self.cortex.remove_from_set(name, key)
        except Exception:
            pass

    # ── geo cell + time bucket (the two anchors) ────────────────────────────────
    @staticmethod
    def _cell_gid(lat: float, lon: float, grid: float = _DEFAULT_GRID) -> str:
        """Discretise a lat/lon to a grid cell id, e.g. 40N124W (SW corner of a 1° cell)."""
        la = int((lat // grid) * grid)
        lo = int((lon // grid) * grid)
        return f"{abs(la)}{'N' if la >= 0 else 'S'}{abs(lo)}{'E' if lo >= 0 else 'W'}"

    def _ensure_cell(self, lat: float, lon: float, grid: float) -> Tuple[str, str]:
        """(cell_key, gid) — mint (idempotently) the geo:cell atom the observation binds to."""
        gid = self._cell_gid(lat, lon, grid)
        la = int((lat // grid) * grid)
        lo = int((lon // grid) * grid)
        key = self._mint(f"geo:cell:{gid}", f"{grid}° cell {gid}",
                         {"concept": "geo_cell", "gid": gid, "lat0": la, "lon0": lo, "grid": grid},
                         sets=("geo:cells",))
        return key, gid

    @staticmethod
    def _iso(t_raw: Any) -> str:
        """Normalise a timestamp (unix s / unix ms / ISO string) to `YYYY-MM-DDTHH:MM:SSZ` (UTC)."""
        if t_raw is None or t_raw == "":
            dt = datetime.now(timezone.utc)
        elif isinstance(t_raw, (int, float)) or (isinstance(t_raw, str) and t_raw.strip().replace(".", "", 1).isdigit()):
            v = float(t_raw)
            if v > 1e11:                                  # milliseconds since epoch
                v /= 1000.0
            dt = datetime.fromtimestamp(v, tz=timezone.utc)
        else:
            s = str(t_raw).strip().replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                dt = datetime.now(timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _epoch(iso: str) -> float:
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
        except (ValueError, AttributeError):
            return 0.0

    def _bucket(self, iso: str, interval: int) -> str:
        """Floor a timestamp to the feed's interval so re-fetches within a bucket unify (idempotent)."""
        interval = max(1, int(interval or 60))
        e = self._epoch(iso)
        b = int(e // interval) * interval
        return datetime.fromtimestamp(b, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── the field-mapping DSL (the only per-source config) ──────────────────────
    @staticmethod
    def _parse_map(map_str: str) -> Dict[str, str]:
        """`'items=$.features; id=$.id; lat=$.geometry.coordinates[1]; …'` → {field: path}."""
        out = {}
        for part in (map_str or "").split(";"):
            if "=" in part:
                k, _, v = part.partition("=")
                if k.strip() and v.strip():
                    out[k.strip()] = v.strip()
        return out

    @staticmethod
    def _get(obj: Any, path: str) -> Any:
        """Evaluate a tiny JSONPath subset: `$`, `$.a.b`, `$.a[1].b`, over dicts/lists."""
        if not path or not path.startswith("$"):
            return None
        cur = obj
        for tok in path[1:].lstrip(".").split("."):
            if cur is None or tok == "":
                if tok == "":
                    continue
                return None
            m = re.match(r"^([^\[\]]*)((?:\[\d+\])*)$", tok)
            if not m:
                return None
            name, idxs = m.group(1), m.group(2)
            if name:
                if isinstance(cur, dict):
                    cur = cur.get(name)
                else:
                    return None
            for i in re.findall(r"\[(\d+)\]", idxs):
                if isinstance(cur, (list, tuple)) and int(i) < len(cur):
                    cur = cur[int(i)]
                else:
                    return None
        return cur

    def _normalize(self, raw: Any, mp: Dict[str, str], default_kind: str) -> List[Dict[str, Any]]:
        """Apply a feed's field mapping to a fetched payload → normalised records. Handles a single
        object (`items=$`), a list, and per-item nested geometry arrays (`geom=$.geometry`, flattened
        item × geometry — the EONET shape)."""
        items = self._get(raw, mp.get("items", "$")) if mp.get("items") else raw
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            return []
        recs = []
        for it in items:
            base = {"raw_id": self._get(it, mp["id"]) if mp.get("id") else None,
                    "title": self._get(it, mp["title"]) if mp.get("title") else None,
                    "mag": self._get(it, mp["mag"]) if mp.get("mag") else None,
                    "mag_unit": self._get(it, mp["mag_unit"]) if mp.get("mag_unit") else None,
                    "alt": self._get(it, mp["alt"]) if mp.get("alt") else None,
                    "kind": (self._get(it, mp["kind"]) if mp.get("kind") else None) or default_kind}
            if mp.get("geom"):                            # flatten item × each geometry element
                geoms = self._get(it, mp["geom"]) or []
                geoms = geoms if isinstance(geoms, list) else [geoms]
                for g in geoms:
                    recs.append({**base,
                                 "lat": self._get(g, mp.get("glat", "$.coordinates[1]")),
                                 "lon": self._get(g, mp.get("glon", "$.coordinates[0]")),
                                 "t": self._get(g, mp["gt"]) if mp.get("gt") else base.get("t")})
            else:
                recs.append({**base,
                             "lat": self._get(it, mp["lat"]) if mp.get("lat") else None,
                             "lon": self._get(it, mp["lon"]) if mp.get("lon") else None,
                             "t": self._get(it, mp["t"]) if mp.get("t") else None})
        return recs

    def _apply_map_shaping(self, recs: List[Dict[str, Any]], mp: Dict[str, str]) -> List[Dict[str, Any]]:
        """Post-normalisation record shaping driven ONLY by map tokens (config-as-data, no per-feed
        code). Two tokens, both aimed at long-lived event feeds (EONET): `fold=latest` keeps a single
        record per subject id — its most recent footprint by source date — so an open event that
        carries a long historical footprint trail lands as ONE current point, not hundreds; `stamp=now`
        rewrites each record's timestamp to fetch-time, because an OPEN event is a fact as of THIS pull
        (its old footprint date must not push it out of the live window, and last_pull should read as
        the fetch time). Feeds without the tokens are returned untouched."""
        if mp.get("fold", "").strip().lower() == "latest":
            best: Dict[str, Dict[str, Any]] = {}
            for r in recs:
                rid = str(r.get("raw_id") if r.get("raw_id") is not None else id(r))
                cur = best.get(rid)
                if cur is None or str(r.get("t") or "") >= str(cur.get("t") or ""):
                    best[rid] = r
            recs = list(best.values())
        if mp.get("stamp", "").strip().lower() == "now":
            now = self._iso(None)
            for r in recs:
                r["t"] = now
        return recs

    # ── feed registry ───────────────────────────────────────────────────────────
    @staticmethod
    def _retain_spec(retain: str) -> Tuple[str, int]:
        """Parse retain= → ('window', seconds) or ('count', n). Default: a 72h window."""
        s = (str(retain or "").strip() or "72h")
        m = _DUR.match(s)
        if m:
            return "window", int(m.group(1)) * _DUR_MULT[m.group(2).lower()]
        if s.isdigit():
            return "count", int(s)
        return "window", 72 * 3600

    def op_register(self, id: str = "", url: str = "", kind: str = "", interval: Any = 300,
                    retain: str = "72h", map: str = "", title: str = "") -> Dict[str, Any]:
        """[feed.register] Declare a live source: its url, telemetry kind, fetch interval (s), retention
        window/count, and the field-mapping DSL. Config-as-data — adding a domain is ONE register, no
        code. Idempotent by id."""
        fid = (id or "").strip()
        if not fid:
            return {"error": "feed.register needs id="}
        try:
            iv = max(5, int(interval))
        except (TypeError, ValueError):
            iv = 300
        rmode, rval = self._retain_spec(retain)
        kind = (kind or "kind:misc:fact").strip()
        self._ensure_kind(kind)
        alias = f"feed:{fid}"
        key = self._mint(alias, (title or f"live feed: {fid}"),
                         {"concept": "feed", "feed_id": fid, "url": url, "kind": kind, "interval": iv,
                          "retain": retain, "retain_mode": rmode, "retain_val": rval, "map": map,
                          "title": title or fid, "provenance": _PROV},
                         sets=("feed:all",), refresh=True)
        return {"status": "ok", "feed": alias, "key": key, "interval": iv,
                "retain": {"mode": rmode, "value": rval}}

    def _ensure_kind(self, kind: str) -> str:
        kind = (kind or "kind:misc:fact").strip()
        parts = kind.split(":")
        label = parts[-1].replace("_", " ") if parts else kind
        return self._mint(kind, f"telemetry kind — {label}",
                          {"concept": "telemetry_kind", "domain": parts[1] if len(parts) > 2 else "",
                           "type": parts[-1]}, sets=("kind:all",))

    def _feed_meta(self, fid: str) -> Tuple[Optional[str], Dict[str, Any]]:
        fk = self._resolve(fid if fid.startswith("feed:") else f"feed:{fid}")
        return fk, (self.cortex.get_meta(fk) or {} if fk else {})

    # ── the fetch → normalise → ingest cycle ────────────────────────────────────
    def op_pull(self, id: str = "", text: str = "", path: str = "", retain: str = "") -> Dict[str, Any]:
        """[feed.pull] Fetch ONE cycle now and ingest it — the CLI-native pull the scheduler calls each
        interval. Acquires the raw payload from `text=`/`path=` (offline) or an HTTP GET of the feed's
        registered url (live, off-web); normalises via the feed's map; mints subjects + observations;
        then runs retention. Degradation-first: a down/malformed feed advances nothing, never raises."""
        fk, fm = self._feed_meta(id)
        if not fk:
            return {"error": f"unknown feed '{id}' (register it first)"}
        raw = None
        try:
            if (text or "").strip():
                raw = json.loads(text)
            elif (path or "").strip():
                with open(path, encoding="utf-8") as fh:
                    raw = json.load(fh)
            elif fm.get("url"):
                raw = self._http_json(fm["url"])
        except Exception as exc:
            logger.info("[feed.pull] %s acquire failed: %s", id, exc)
            return {"status": "skipped", "feed": self._alias_of(fk), "reason": str(exc)[:80]}
        if raw is None:
            return {"status": "skipped", "feed": self._alias_of(fk), "reason": "no payload"}
        mp = self._parse_map(fm.get("map", ""))
        recs = self._normalize(raw, mp, fm.get("kind", "kind:misc:fact"))
        recs = self._apply_map_shaping(recs, mp)   # fold=latest / stamp=now (config-as-data)
        res = self.import_records(recs, into=(fm.get("feed_id") or id))
        # last_pull is per-cycle RUNTIME state, not config — it is DERIVED (op_feeds reads the newest
        # observation's time), never written back onto the feed atom. The feed atom holds only its
        # stable declaration; observations carry the moving frontier.
        swept = self._retain(fk, fm, override=retain)
        return {"status": "pulled", "feed": self._alias_of(fk), **res, "evicted": swept}

    def _http_json(self, url: str, timeout: float = 20.0) -> Optional[Any]:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:   # honours HTTPS_PROXY
            return json.loads(resp.read().decode("utf-8", errors="replace"))

    def op_ingest(self, id: str = "", records: Any = None) -> Dict[str, Any]:
        """[feed.ingest] Batch-ingest NORMALISED records (RPC form) into a feed."""
        if not isinstance(records, list):
            return {"error": "feed.ingest needs records=[{lat,lon,raw_id,t,…}]"}
        return self.import_records(records, into=(id or "").strip())

    # ── the Importable contract (io.ingest model=feed into=<feed>) ──────────────
    def import_records(self, records: List[Dict[str, Any]], into: str = "",
                       mapping: Dict[str, str] = None, **opts) -> Dict[str, Any]:
        """[Importable] Ingest NORMALISED telemetry records into the feed named by `into`. Each record
        → (mint-or-reuse the STABLE subject) + (mint the CHANGING observation, content-addressed by
        (subject, time-bucket) = idempotent) + geo-cell / feed / kind links. All writes go through the
        guarded composite path (workspace guard + WriteQueue); provenance=telemetry fences them from
        learning. A record missing lat/lon is skipped (degradation-first)."""
        fk, fm = self._feed_meta(into)
        if not fk:
            raise ValueError(f"feed import needs into=<registered feed id> (got {into!r})")
        fid = fm.get("feed_id") or into
        interval = int(fm.get("interval") or 300)
        grid = float(fm.get("grid") or _DEFAULT_GRID)
        subjects, obs_new, obs_seen, skipped = set(), 0, 0, 0
        _batch_newest = [""]                              # newest obs ISO in this batch (for last_pull)
        for i, rec in enumerate(records):
            lat, lon = self._num(self._m(rec, mapping, "lat")), self._num(self._m(rec, mapping, "lon"))
            if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                skipped += 1
                continue
            raw_id = str(self._m(rec, mapping, "raw_id", "id", default=fid) or fid)
            iso = self._iso(self._m(rec, mapping, "t"))
            bucket = self._bucket(iso, interval)
            kind = str(self._m(rec, mapping, "kind") or fm.get("kind") or "kind:misc:fact")
            # 1) the STABLE subject — by (feed, external id)
            sub_alias = f"entity:{fid}:{self._slug(raw_id)}"
            _sday = _day_of(iso)   # A48.1 — day membership at WRITE time (evict iterates the day, not the store)
            sk = self._mint(sub_alias, (self._m(rec, mapping, "title") or f"{fid}:{raw_id}"),
                            {"concept": "telemetry_subject", "feed": fid, "raw_id": raw_id,
                             "kind": kind, "provenance": _PROV},
                            sets=(f"feed:{fid}:subjects", f"telemetry:day:{_sday}"))
            self._link(fk, sk, "feed:tracks")
            subjects.add(sk)
            # 2) the CHANGING observation — content-addressed by (subject, bucket) = idempotent
            obs_alias = f"obs:{fid}:{self._slug(raw_id)}:{bucket}"
            existed = bool(self.cortex.resolve_alias(obs_alias))
            mag = self._num(self._m(rec, mapping, "mag"))
            title = self._m(rec, mapping, "title") or f"{fid} {raw_id}"
            content = f"{title} · {iso}" + (f" · M{mag}" if mag is not None else "")
            ck, gid = self._ensure_cell(lat, lon, grid)
            ok = self._mint(obs_alias, content,
                            {"concept": "observation", "provenance": _PROV, "trust": _DEFAULT_TRUST,
                             "feed": fid, "subject": sk, "raw_id": raw_id, "kind": kind,
                             "lat": lat, "lon": lon, "alt": self._num(self._m(rec, mapping, "alt")),
                             "mag": mag, "mag_unit": self._m(rec, mapping, "mag_unit") or "",
                             "t": iso, "bucket": bucket, "cell": gid},
                            sets=(f"feed:{fid}:obs", f"entity:{sk[:12]}:track", f"geo:cell:{gid}:obs",
                                  f"telemetry:day:{_day_of(iso)}"))   # A48.1 — write-time day membership
            if not existed:
                self._link(ok, sk, "obs:of")
                self._link(ok, fk, "obs:from")
                self._link(ok, ck, "obs:at")
                self._link(ok, self._ensure_kind(kind), "sys:is_a")
                self._chrono_anchor(sk, ok, iso)          # place it in the substrate's time chain
                obs_new += 1
                if iso and iso > _batch_newest[0]:
                    _batch_newest[0] = iso                # track this batch's newest obs time
            else:
                obs_seen += 1
        # F30-2/F39-P1b — PERSIST last_pull as O(1) mutable feed state (set_meta side-store, not the
        # content-addressed atom). op_due/op_feeds then read it as a dict lookup instead of scanning
        # EVERY observation and taking max(t) — the O(N_obs) due-scan behind the 300 s+ feed-poll
        # ticks and the "no reply within 60 s" incidents. Monotonic: never regress past a newer
        # persisted value (an out-of-order backfill must not move last_pull backwards).
        if _batch_newest[0]:
            self._persist_last_pull(fk, _batch_newest[0])
        return {"status": "ingested", "feed": f"feed:{fid}", "records": len(records),
                "subjects": len(subjects), "observations_new": obs_new,
                "observations_idempotent": obs_seen, "skipped": skipped}

    def _chrono_anchor(self, sk: str, new_obs: str, new_iso: str) -> None:
        """Place a new observation in the memory substrate's NATIVE temporal chain: a subject's
        successive fixes are linked `chrono:before` (the same relation paleography/psychology use to
        order atoms in time), so the live trajectory is visible to the substrate's `time` magnetic
        axis and generate_view — not a private meta-only scheme. meta.t stays for exact ordering; the
        chrono edges make telemetry uniformly time-placed, like any other atom. In-order polling lays
        one edge; an out-of-order insert stitches both neighbours."""
        prev, prev_t, nxt, nxt_t = None, "", None, None
        for o in (self.cortex.get_collection_members(f"entity:{sk[:12]}:track") or []):
            if o == new_obs:
                continue
            t = (self.cortex.get_meta(o) or {}).get("t", "")
            if not t:
                continue
            if t <= new_iso and t >= prev_t:
                prev, prev_t = o, t
            elif t > new_iso and (nxt_t is None or t < nxt_t):
                nxt, nxt_t = o, t
        if prev:
            self._link(prev, new_obs, "chrono:before")
        if nxt:
            self._link(new_obs, nxt, "chrono:before")

    @staticmethod
    def _slug(s: Any) -> str:
        return re.sub(r"[^a-zA-Z0-9]+", "_", str(s)).strip("_")[:48] or "x"

    @staticmethod
    def _num(v: Any) -> Optional[float]:
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _m(rec: Dict[str, Any], mapping: Optional[Dict[str, str]], field: str, *fallbacks: str,
           default: Any = None) -> Any:
        mapping = mapping or {}
        keys = [mapping[field]] if field in mapping else [field, *fallbacks]
        for k in keys:
            if k in rec and rec[k] is not None and str(rec[k]) != "":
                return rec[k]
        return default

    # ── retention (bounded growth — mandatory) ──────────────────────────────────
    def _retain(self, fk: str, fm: Dict[str, Any], override: str = "") -> int:
        """Soft-evict observations beyond the feed's retention window/count (recoverable — the atom
        stays, it leaves the live sets + is tagged evicted). The live layer never grows unbounded."""
        mode, val = self._retain_spec(override) if override else (fm.get("retain_mode", "window"),
                                                                  int(fm.get("retain_val") or 72 * 3600))
        fid = fm.get("feed_id") or self._alias_of(fk).split(":", 1)[-1]
        evicted = 0
        now = self._epoch(self._iso(None))
        for sk in (self.cortex.get_collection_members(f"feed:{fid}:subjects") or []):
            track = self.cortex.get_collection_members(f"entity:{sk[:12]}:track") or []
            rows = sorted(((self.cortex.get_meta(o) or {}).get("t", ""), o) for o in track)
            drop = []
            if mode == "count" and len(rows) > val:
                drop = rows[:len(rows) - val]
            elif mode == "window":
                drop = [(t, o) for t, o in rows if t and (now - self._epoch(t)) > val]
            for t, o in drop:
                self._evict(fid, sk, o)
                evicted += 1
        return evicted

    @staticmethod
    def _min_interval() -> int:
        """The DEMO cadence floor in seconds (F55 §1). Env AKASHA_FEED_MIN_INTERVAL overrides the
        default; 0 disables the floor (a real-measurement deployment honoring each feed's interval)."""
        import os as _os
        raw = _os.environ.get(_MIN_INTERVAL_ENV, "").strip()
        if raw == "":
            return _DEFAULT_MIN_INTERVAL
        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            return _DEFAULT_MIN_INTERVAL

    @staticmethod
    def _keep_days() -> int:
        """Telemetry retention window in days (F55 §1); 1 = keep today only. Env override; never < 1."""
        import os as _os
        try:
            return max(1, int(_os.environ.get(_KEEP_DAYS_ENV, "").strip() or _DEFAULT_KEEP_DAYS))
        except (TypeError, ValueError):
            return _DEFAULT_KEEP_DAYS

    @staticmethod
    def _chunk_day(row: Dict[str, Any], meta: Dict[str, Any]) -> str:
        """The UTC day (YYYY-MM-DD) an atom belongs to: an observation's own time (meta.t) when
        present, else the chunk's created_at epoch. Empty string when neither resolves (kept, never
        dropped on an unknown day — conservative)."""
        t = str((meta or {}).get("t") or "")
        if len(t) >= 10 and t[4] == "-" and t[7] == "-":
            return t[:10]
        ca = str((row or {}).get("created_at") or "")
        try:
            return _time.strftime("%Y-%m-%d", _time.gmtime(float(ca)))
        except (TypeError, ValueError):
            return ""

    def op_gc(self, keep: Any = 0, limit: Any = 0) -> Dict[str, Any]:
        """[feed.gc] HARD retention sweep (F55 §1, memory-discipline R5/C2): delete every
        `provenance=telemetry` atom whose UTC day is OLDER than the retention window (`keep` days,
        default = the deployment policy, 1 = keep today only). Unlike `_retain` (a SOFT view eviction
        that leaves the atom resident — which is what let ~131k rows accumulate), this drops the atom
        fully: removed from EVERY set it joined, then `drop_chunk` (links + alias go with it).

        Writer-side + BOUNDED: at most `limit` atoms are dropped per pass (default 20000) and the pass
        is `truncated` when it hits the budget — the nightly job re-enters until clean, so the existing
        backlog drains over a few passes without one gulp under the WriteQueue. Idempotent (a second
        run over an already-swept window drops 0). Requires the shared nucleus (public telemetry) +
        librarian/admin. **Demo policy = keep today only; a real-measurement deployment raises
        AKASHA_TELEMETRY_KEEP_DAYS and should COMPACT to daily summaries (the pulse pattern) instead.**"""
        nuc = self._pub_nucleus()
        if nuc is None:
            return {"status": "skipped", "note": "feed.gc needs the shared nucleus (librarian/admin)"}
        core = nuc.core
        kd = max(1, int(keep)) if str(keep).strip() not in ("", "0") else self._keep_days()
        try:
            budget = int(limit) if int(limit) > 0 else _GC_DEFAULT_BUDGET
        except (TypeError, ValueError):
            budget = _GC_DEFAULT_BUDGET
        cutoff = _time.strftime("%Y-%m-%d", _time.gmtime(_time.time() - (kd - 1) * 86400))
        try:
            from lib.akasha.api import process as _mt
            _rss0 = _mt.rss_mb()
        except Exception:
            _mt, _rss0 = None, None

        def _phase(nm, n, r_before, t0):
            # A58 — one `[telemetry.evict] phase=<n> n= Δrss= t=` line per phase, same shape as
            # station.compact, so the three phases sum to the summary (the +73MB was uninstrumented).
            r1 = _mt.rss_mb() if _mt is not None else None
            dr = round(r1 - r_before, 1) if (r_before is not None and r1 is not None) else "?"
            logger.info("[telemetry.evict] phase=%s n=%d Δrss=%sMB t=%ss", nm, n, dr,
                        round(_time.time() - t0, 1))
            return r1
        _pr = _rss0
        _pt = _time.time()
        # A48.1 — iterate the write-time DAY collections for days BEFORE the cutoff and drop those
        # members (O(victims)), instead of decoding every atom in the store to find ≤ a few thousand
        # victims (the F33/F50 "O(K), never O(store)" rule, broken nightly by the old iter_all_chunks
        # sweep — each pass left ~110 MB of un-returned transient allocations resident). `scanned` is now
        # victims examined, not store rows walked.
        try:
            day_colls = [c for c in (core.get_distinct_collection_names() or [])
                         if str(c).startswith(_DAY_PREFIX)]
        except Exception:
            day_colls = []
        # A telemetry SUBJECT is stable across days: `feed.ingest` re-mints the same
        # content-addressed atom on every report, so it joins the day collection of EVERY day it
        # reported. Sweeping an old day used to drop whatever it found there — including a subject
        # that reported again this morning — which left today's surviving observation pointing at a
        # dead atom (`meta.subject` unresolvable, its `obs:of` link dangling). Reproduced: one
        # subject on day −3 and today, `feed.gc keep=1` → the subject gone, today's observation
        # orphaned.
        #
        # So build the KEPT side first: every member of every day at or after the cutoff. A victim
        # is a member of an expiring day that is in NO kept day. Bounded the same way as the sweep —
        # it walks the same per-day collections, never the store (A48.1 / memory R1).
        kept: set = set()
        for cname in sorted(day_colls):
            day = cname[len(_DAY_PREFIX):]
            if day and day >= cutoff:
                kept.update(k for k in (core.get_collection_members(cname) or []) if k)
        victims: List[str] = []
        scanned = 0
        truncated = False
        drained_days: List[str] = []
        still_reporting = 0
        for cname in sorted(day_colls):
            day = cname[len(_DAY_PREFIX):]
            if not (day and day < cutoff):
                continue
            for k in (core.get_collection_members(cname) or []):
                scanned += 1
                if not k:
                    continue
                if k in kept:
                    # Still reporting on a day we keep. Its membership in THIS expiring day goes
                    # (the day is drained), but the atom stays resolvable for the observations that
                    # still point at it.
                    still_reporting += 1
                    try:
                        core.remove_from_collection(cname, k)
                    except Exception:
                        pass
                    continue
                victims.append(k)
                if len(victims) >= budget:
                    truncated = True
                    break
            if truncated:
                break
            drained_days.append(cname)
        _pr = _phase("scan", scanned, _pr, _pt); _pt = _time.time()
        # Phase 2 — DROP (C2): remove from every set it joined, then drop the atom (links + alias go).
        dropped = 0
        for k in victims:
            if not k:
                continue
            try:
                for coll in list(core.get_collections_for_key(k) or []):
                    try:
                        core.remove_from_collection(coll, k)
                    except Exception:
                        pass
                core.drop_chunk(k)
                dropped += 1
            except Exception:
                pass
        # A drained day collection is left EMPTY (there is no collection-def delete on the ISA; an empty
        # def is O(days) tiny and never re-lists members) — the members are gone, which is what matters.
        _pr = _phase("drop", dropped, _pr, _pt); _pt = _time.time()
        # A58 — phase=commit: return the sweep's transient allocations to the OS (gc + malloc_trim) so
        # they do not become the process's permanent floor, and measure what is RETAINED after (rss now
        # minus rss before the whole sweep). This is the residue the +73MB uninstrumented delta hid.
        _retdr = None
        if _mt is not None:
            _retdr, _ = _mt.gc_trim()
        _rss1 = _mt.rss_mb() if _mt is not None else None
        _phase("commit", 0, _pr, _pt)
        _retained = round(_rss1 - _rss0, 1) if (_rss0 is not None and _rss1 is not None) else "?"
        _dr = _retained
        logger.info("[telemetry.evict] keep_days=%d cutoff<%s scanned=%d dropped=%d "
                    "still_reporting=%d truncated=%s Δrss=%sMB retained=%sMB",
                    kd, cutoff, scanned, dropped, still_reporting, truncated, _dr, _retained)
        return {"status": "ok", "type": "feed:gc", "keep_days": kd, "cutoff_day": cutoff,
                "scanned": scanned, "dropped": dropped, "still_reporting": still_reporting,
                "truncated": truncated, "retained": _retained}

    def _evict(self, fid: str, sk: str, obs_key: str) -> None:
        """Soft-evict one observation: remove it from the live sets and tag it (the atom is kept)."""
        # Soft-evict = remove from the LIVE sets ONLY. An observation is an immutable, content-
        # addressed FACT: we never mutate the atom (upper layers see atoms as immutable). Eviction is
        # a property of the live VIEW (set membership), not of the atom — the atom + its alias remain
        # resolvable, so it is fully recoverable (re-add to the sets, or reach it by its alias).
        m = self.cortex.get_meta(obs_key) or {}
        gid = m.get("cell", "")
        for s in (f"feed:{fid}:obs", f"entity:{sk[:12]}:track", f"geo:cell:{gid}:obs" if gid else ""):
            if not s:
                continue
            self._delset(s, obs_key)

    # ── reads ────────────────────────────────────────────────────────────────────
    def _obs_row(self, ok: str) -> Dict[str, Any]:
        m = self.cortex.get_meta(ok) or {}
        return {"id": self._alias_of(ok), "t": m.get("t"), "lat": m.get("lat"), "lon": m.get("lon"),
                "alt": m.get("alt"), "mag": m.get("mag"), "cell": m.get("cell"), "kind": m.get("kind"),
                "feed": m.get("feed"), "subject": self._alias_of(m.get("subject")) if m.get("subject") else "",
                "source_atom": self._alias_of(ok)}

    def _persist_last_pull(self, fk: str, iso: str) -> None:
        """Persist last_pull on the feed atom's mutable meta. A PUBLIC feed lives in the shared
        nucleus (like proto-words), so its meta is updated on the nucleus core — the same routing
        _mint uses; a PRIVATE feed updates its own cortex. Never regress past a newer value."""
        if not iso:
            return
        nuc = self._pub_nucleus()
        try:
            if nuc is not None:
                core = nuc.core
                row = core.get_chunk_raw(fk)
                cur = json.loads(row["meta"]) if row and row.get("meta") else {}
                if iso > (cur.get("last_pull") or ""):
                    core.merge_meta(fk, {"last_pull": iso})
            else:
                if iso > ((self.cortex.get_meta(fk) or {}).get("last_pull") or ""):
                    self.cortex.set_meta(fk, "last_pull", iso)
        except Exception:
            pass

    def _feed_last_pull(self, fk: str, m: Dict[str, Any], fid: str) -> str:
        """O(1) last_pull for a feed: the persisted `last_pull` meta marker (F30-2). If ABSENT — a
        feed whose observations predate the marker — fall back ONCE to the O(N_obs) max(t) scan and
        PERSIST the result, so this feed is O(1) on every subsequent call (self-healing migration; no
        operator step). Returns "" when the feed has no observations yet."""
        lp = (m or {}).get("last_pull")
        if lp:
            return lp
        obs = self.cortex.get_collection_members(f"feed:{fid}:obs") or []
        last = max(((self.cortex.get_meta(o) or {}).get("t", "") for o in obs), default="") or ""
        if last:
            self._persist_last_pull(fk, last)
        return last

    def op_feeds(self) -> Dict[str, Any]:
        """[feed.feeds] Registered feeds with their schedule, last pull, and live observation count."""
        rows = []
        for fk in (self.cortex.get_collection_members("feed:all") or []):
            m = self.cortex.get_meta(fk) or {}
            fid = m.get("feed_id", "")
            # last_pull is O(1) from the persisted marker (F30-2); the observation COUNT is a keys-only
            # membrane walk (no per-obs value read), not the old max(get_meta(o) for every o).
            last_pull = self._feed_last_pull(fk, m, fid) or None
            rows.append({"id": self._alias_of(fk), "kind": m.get("kind"), "interval": m.get("interval"),
                         "retain": m.get("retain"), "last_pull": last_pull,
                         "subjects": len(self.cortex.get_collection_members(f"feed:{fid}:subjects") or []),
                         "observations": len(self.cortex.get_collection_members(f"feed:{fid}:obs") or [])})
        rows.sort(key=lambda r: r["id"])
        return {"status": "ok", "count": len(rows), "feeds": rows}

    def op_due(self, at: str = "") -> Dict[str, Any]:
        """[feed.due] The feeds DUE for a pull — the scheduler's POLICY input (pure read; the kernel
        feed.tick turns each into a LOW-priority JCL pull). A feed is due when its interval has elapsed
        since its newest observation (last_pull is derived, never stored on the atom)."""
        now = self._epoch(self._iso(at)) if at else self._epoch(self._iso(None))
        floor = self._min_interval()
        due = []
        for fk in (self.cortex.get_collection_members("feed:all") or []):
            m = self.cortex.get_meta(fk) or {}
            fid = m.get("feed_id", "")
            # DEMO cadence floor (F55 §1): a feed is eligible no more often than the floor, so a
            # 60 s ISS / 300 s quake feed captures ≈ hourly and stops flooding the store. A real
            # deployment sets AKASHA_FEED_MIN_INTERVAL=0 to honor each feed's declared interval.
            interval = max(int(m.get("interval") or 300), floor)
            # F30-2/F39-P1b — O(1) last_pull from the persisted feed-meta side-store; this is the
            # scheduler's per-tick hot path. Only a LEGACY feed (ingested before last_pull was
            # persisted) has no marker — then fall back to the O(N_obs) scan ONCE and persist the
            # result, so every subsequent tick is O(feeds), never O(observations).
            last = self._feed_last_pull(fk, m, fid)
            elapsed = (now - self._epoch(last)) if last else float("inf")
            if elapsed >= interval:
                due.append({"id": fid, "feed": self._alias_of(fk), "interval": interval,
                            "last_pull": last or None,
                            "elapsed": (None if elapsed == float("inf") else round(elapsed))})
        due.sort(key=lambda d: (d["elapsed"] is not None, -(d["elapsed"] or 0)))
        return {"status": "ok", "now": self._iso(at) if at else self._iso(None),
                "count": len(due), "due": due}

    def op_latest(self, id: str = "", n: Any = 20) -> Dict[str, Any]:
        """[feed.latest] The most recent observations from a feed (newest first)."""
        fk, fm = self._feed_meta(id)
        if not fk:
            return {"error": f"unknown feed '{id}'"}
        fid = fm.get("feed_id") or id
        try:
            lim = max(1, int(n))
        except (TypeError, ValueError):
            lim = 20
        obs = self.cortex.get_collection_members(f"feed:{fid}:obs") or []
        rows = sorted((self._obs_row(o) for o in obs), key=lambda r: r.get("t") or "", reverse=True)
        return {"status": "ok", "feed": self._alias_of(fk), "count": len(rows), "latest": rows[:lim]}

    def op_track(self, subject: str = "", since: str = "", n: Any = 0) -> Dict[str, Any]:
        """[feed.track] A subject's ordered trajectory — the moving-point path (obs by time)."""
        sk = self._resolve(subject if subject.startswith("entity:") else subject)
        if not sk:
            return {"error": f"unknown subject '{subject}'"}
        rows = sorted((self._obs_row(o) for o in
                       (self.cortex.get_collection_members(f"entity:{sk[:12]}:track") or [])),
                      key=lambda r: r.get("t") or "")
        if since:
            iso = self._iso(since)
            rows = [r for r in rows if (r.get("t") or "") >= iso]
        try:
            lim = int(n)
        except (TypeError, ValueError):
            lim = 0
        if lim > 0:
            rows = rows[-lim:]
        return {"status": "ok", "subject": self._alias_of(sk), "count": len(rows), "track": rows}

    def _window_bounds(self, window: str, at: str) -> Tuple[float, float]:
        _, secs = self._retain_spec(window or "6h")
        hi = self._epoch(self._iso(at)) if at else self._epoch(self._iso(None))
        return hi - secs, hi

    def op_cell(self, gid: str = "", window: str = "6h", at: str = "") -> Dict[str, Any]:
        """[feed.cell] Everything observed in a geo cell within a time window — a point-on-the-globe as
        an atom (its live contents across feeds)."""
        gid = (gid or "").strip().replace("geo:cell:", "")
        lo, hi = self._window_bounds(window, at)
        rows = []
        for o in (self.cortex.get_collection_members(f"geo:cell:{gid}:obs") or []):
            r = self._obs_row(o)
            e = self._epoch(r.get("t") or "")
            if lo <= e <= hi:
                rows.append(r)
        rows.sort(key=lambda r: r.get("t") or "", reverse=True)
        feeds = sorted({r["feed"] for r in rows})
        return {"status": "ok", "cell": gid, "window": window, "count": len(rows),
                "feeds": feeds, "observations": rows}

    def _fresh_by_cell(self, lo: float, hi: float, only_feeds: Optional[set]) -> Dict[str, Dict[str, Any]]:
        """{gid: {feed: [obs rows]}} for observations in the window — the cross substrate."""
        cells: Dict[str, Dict[str, Any]] = {}
        for fk in (self.cortex.get_collection_members("feed:all") or []):
            fid = (self.cortex.get_meta(fk) or {}).get("feed_id", "")
            if only_feeds and fid not in only_feeds:
                continue
            for o in (self.cortex.get_collection_members(f"feed:{fid}:obs") or []):
                r = self._obs_row(o)
                e = self._epoch(r.get("t") or "")
                if r.get("cell") and lo <= e <= hi:
                    cells.setdefault(r["cell"], {}).setdefault(fid, []).append(r)
        return cells

    def op_cross(self, window: str = "6h", feeds: str = "", at: str = "", grid: str = "") -> Dict[str, Any]:
        """[feed.cross] THE cross — the geo analog of gen.cross: loci = geo cells, lenses = feeds. For a
        time window it groups observations by cell across feeds and reports COINCIDENCE (a cell with ≥2
        feeds fresh — a corroborated spatiotemporal fact no single feed states, e.g. the ISS over an
        active quake cell) vs SINGLETONS (one feed only — held, not discarded). Nothing collapsed; the
        cross is a regenerable view, never a canonical write."""
        only = set(x.strip() for x in (feeds or "").split(",") if x.strip()) or None
        lo, hi = self._window_bounds(window, at)
        cells = self._fresh_by_cell(lo, hi, only)
        coincidence, singleton = [], []
        for gid, by_feed in cells.items():
            fids = sorted(by_feed)
            row = {"cell": gid, "feeds": fids, "count": len(fids),
                   "observations": [o for fs in by_feed.values() for o in fs]}
            (coincidence if len(fids) >= 2 else singleton).append(row)
        coincidence.sort(key=lambda r: (-r["count"], r["cell"]))
        singleton.sort(key=lambda r: r["cell"])
        return {"status": "ok", "window": window, "cells": len(cells),
                "coincidence": coincidence, "singletons": singleton,
                "feeds_present": sorted({f for c in cells.values() for f in c})}

    def op_project(self, mode: str = "map", window: str = "6h", subject: str = "",
                   at: str = "") -> Dict[str, Any]:
        """[feed.project] The read-only projection payload for the archives live map. Derived +
        regenerable, never a canonical write (V1); every object keeps its source_atom (V7). Modes:
        map (all fresh observations as points + the feed layers), cross (the coincidence cells),
        track (one subject's trajectory)."""
        mode = (mode or "map").strip()
        if mode == "track" and subject:
            return {"status": "ok", "mode": "track", **self.op_track(subject=subject)}
        if mode == "cross":
            return {"status": "ok", "mode": "cross", **self.op_cross(window=window, at=at)}
        lo, hi = self._window_bounds(window, at)
        cells = self._fresh_by_cell(lo, hi, None)
        # map = the CURRENT state: ONE marker per subject at its latest position in the window.
        # The per-bucket history (a moving subject's trail) is the `track` mode, not the map —
        # otherwise a static-but-still-active event (stamp=now re-confirms it every interval) stacks
        # one point per bucket and floods the map (an open disaster became thousands of coincident
        # points). Latest-per-subject keeps iss/quakes/disasters to one live marker each; the ISS
        # trail is still drawn from a separate mode=track call.
        latest: Dict[str, Dict[str, Any]] = {}
        for o in (p for by in cells.values() for fs in by.values() for p in fs):
            skey = o.get("subject") or o.get("id")
            cur = latest.get(skey)
            if cur is None or str(o.get("t") or "") >= str(cur.get("t") or ""):
                latest[skey] = o
        points = list(latest.values())
        layers: Dict[str, int] = {}
        for p in points:
            layers[p["feed"]] = layers.get(p["feed"], 0) + 1
        return {"status": "ok", "mode": "map", "window": window, "generated_at": self._iso(None),
                "layers": [{"feed": f, "points": n} for f, n in sorted(layers.items())],
                "points": points, "cross": self.op_cross(window=window, at=at).get("coincidence", [])}

    def op_trace(self, id: str = "") -> Dict[str, Any]:
        """[feed.trace] A projection object → its source atom (reversibility, V7)."""
        k = self._resolve(id)
        if not k:
            return {"error": f"unknown object '{id}'"}
        m = self.cortex.get_meta(k) or {}
        return {"status": "ok", "id": self._alias_of(k), "key": k, "concept": m.get("concept"),
                "provenance": m.get("provenance"), "content": self.cortex.get_chunk(k) or "", "meta": m,
                "links": [{"to": self._alias_of(d), "rel": r} for d, r in
                          (self.cortex.get_adjacent_links(k) or [])]}
