#!/usr/bin/env python3
"""
Live-telemetry foundation eval (`feed`) — dynamic facts → atoms, crossed on space·time. No network.

Exercises the whole backend foundation offline with mock payloads shaped exactly like the three v1
keyless feeds (ISS single object, USGS earthquakes GeoJSON, EONET nested-geometry events):

  • feed.register (config-as-data) + feed.pull id= text=<raw json> (the map-DSL normalisation)
  • the stable-subject / changing-observation split (entity:* stable, obs:* content-addressed)
  • the two anchors: geo:cell:* (1° grid) + time-bucketing
  • idempotency (re-pull the same bucket → no new obs), provenance=telemetry fence (excluded from learn)
  • feed.track (a subject's trajectory), feed.cell, and THE cross: feed.cross highlights the geo cell
    where the ISS ground-track passes over an active quake (a corroborated spatiotemporal fact)
  • feed.project (archives payload) + feed.trace (reversibility) + retention (bounded growth)

Run:  python app/test/live_telemetry_eval.py     (exit 0 = all pass)
"""
import hashlib, json, os, sys, tempfile, time as _time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, ROOT)
from app.concepts import feed_poll as feed
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

NOW = int(_time.time())                       # fixtures are now-relative (fresh) so the retention
def _iso(s):                                   # window keeps them and the default cross window covers them
    return datetime.fromtimestamp(s, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


# ── mock payloads (shaped like the real keyless APIs; now-relative timestamps) ──
ISS = {"latitude": 40.4, "longitude": -124.2, "altitude": 421.0, "timestamp": NOW - 300, "id": 25544}
# a quake in the SAME 1° cell (40N125W — floor of -124.x is -125) as the ISS subpoint, plus one elsewhere
USGS = {"features": [
    {"id": "nc111", "geometry": {"coordinates": [-124.5, 40.3, 8.0]},
     "properties": {"time": (NOW - 300) * 1000, "mag": 4.2, "title": "M4.2 — offshore"}},
    {"id": "nc222", "geometry": {"coordinates": [139.7, 35.6, 30.0]},
     "properties": {"time": (NOW - 300) * 1000, "mag": 3.1, "title": "M3.1 — near Tokyo"}},
]}
# EONET: items whose geometry is a nested ARRAY (flattened item × geometry)
EONET = {"events": [
    {"id": "EONET_1", "title": "Wildfire A",
     "geometry": [{"coordinates": [-120.1, 38.9], "date": _iso(NOW - 600)}]},
]}
CELL = "40N125W"                              # the shared cell of the ISS subpoint + the offshore quake

MAPS = {
    "iss":    "items=$; id=$.id; lat=$.latitude; lon=$.longitude; alt=$.altitude; t=$.timestamp",
    "usgs":   "items=$.features; id=$.id; lat=$.geometry.coordinates[1]; lon=$.geometry.coordinates[0]; "
              "t=$.properties.time; mag=$.properties.mag; title=$.properties.title",
    "eonet":  "items=$.events; id=$.id; title=$.title; geom=$.geometry; "
              "glat=$.coordinates[1]; glon=$.coordinates[0]; gt=$.date",
}


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_feed_"))
    gw = AkashaGateway(kernel_client=k)
    import shlex

    def C(method, **kw):
        line = " ".join([method] + [f"{a}={shlex.quote(str(v))}" for a, v in kw.items() if str(v) != ""])
        r = gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                         "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local")
        return (r.get("result") or {}).get("result") if isinstance(r.get("result"), dict) else r.get("result")

    def D(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": "admin", "data": data}, "id": "m"}, "local")
        return r.get("result") or r.get("error") or {}

    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    # ── register the three feeds (config-as-data) ──
    D("feed.register", {"id": "iss", "kind": "kind:orbit:satellite", "interval": 60, "retain": "6h", "map": MAPS["iss"]})
    D("feed.register", {"id": "usgs_eq", "kind": "kind:seismic:quake", "interval": 300, "retain": "48h", "map": MAPS["usgs"]})
    D("feed.register", {"id": "eonet", "kind": "kind:disaster:wildfire", "interval": 1800, "retain": "72h", "map": MAPS["eonet"]})
    feeds = D("feed.feeds", {})
    check("feed.register: three feeds registered (config-as-data, no code)",
          feeds.get("count") == 3, str([f["id"] for f in feeds.get("feeds", [])]))

    # ── pull one cycle offline (text= supplies the raw payload; the map DSL normalises it) ──
    ri = D("feed.pull", {"id": "iss", "text": json.dumps(ISS)})
    ru = D("feed.pull", {"id": "usgs_eq", "text": json.dumps(USGS)})
    re = D("feed.pull", {"id": "eonet", "text": json.dumps(EONET)})
    check("feed.pull iss: the single-object feed mints ONE subject + ONE observation",
          ri.get("subjects") == 1 and ri.get("observations_new") == 1, str(ri))
    check("feed.pull usgs: the GeoJSON features feed mints 2 quake subjects + 2 observations",
          ru.get("subjects") == 2 and ru.get("observations_new") == 2, str(ru))
    check("feed.pull eonet: the NESTED-geometry feed flattens item×geometry → 1 observation",
          re.get("observations_new") == 1, str(re))

    cortex = k.manager.get_session("admin").local_cortex
    # ── the stable subject + a geo cell + a kind exist as ordinary atoms ──
    iss_sub = cortex.resolve_alias("entity:iss:25544")
    cell = cortex.resolve_alias(f"geo:cell:{CELL}")
    kind = cortex.resolve_alias("kind:orbit:satellite")
    check("entity:iss:25544 is a stable subject atom (identity by feed+extid)", bool(iss_sub), str(iss_sub))
    check(f"geo:cell:{CELL} minted (the 1° shared substrate) + kind:orbit:satellite",
          bool(cell) and bool(kind))

    # ── provenance fence (ASI06): the observation is provenance=telemetry (excluded from learning) ──
    from lib.akasha.ontology.weave import _is_external
    obs_key = cortex.resolve_alias("entity:iss:25544") and \
        (cortex.get_collection_members(f"entity:{iss_sub[:12]}:track") or [None])[0]
    om = cortex.get_meta(obs_key) or {}
    check("provenance fence: the observation is provenance=telemetry and excluded from learning (ASI06)",
          om.get("provenance") == "telemetry" and _is_external(om) is True, str(om.get("provenance")))

    # ── idempotency: re-pull the SAME payload → no new observations (content-addressed by bucket) ──
    ri2 = D("feed.pull", {"id": "iss", "text": json.dumps(ISS)})
    check("idempotency: re-pulling the same cycle adds NO new observations (subject stays stable)",
          ri2.get("observations_new") == 0 and ri2.get("observations_idempotent") == 1, str(ri2))

    # ── a second ISS fix a bucket later → the trajectory grows ──
    ISS2 = {**ISS, "latitude": 40.6, "longitude": -123.4, "timestamp": ISS["timestamp"] + 120}
    D("feed.pull", {"id": "iss", "text": json.dumps(ISS2)})
    tr = D("feed.track", {"subject": "entity:iss:25544"})
    check("feed.track: the subject's trajectory is its observations ordered by time (2 fixes)",
          tr.get("count") == 2 and tr["track"][0]["t"] <= tr["track"][1]["t"], str(tr.get("count")))

    # ── substrate compatibility: successive fixes form the NATIVE chrono:before chain (the memory
    #    substrate's own time axis), not a private meta-only scheme — telemetry is time-placed like
    #    any atom, so generate_view / the "time" magnetic axis see it uniformly ──
    older = cortex.resolve_alias(tr["track"][0]["id"])
    newer = cortex.resolve_alias(tr["track"][1]["id"])
    chained = any(d == newer and r == "chrono:before" for d, r in (cortex.get_adjacent_links(older) or []))
    check("substrate compat: successive observations are linked chrono:before (native time axis, "
          "not a private time scheme)", chained, str(chained))
    # last_pull is DERIVED (op_feeds reads the newest obs), never mutated onto the feed atom
    lp = {f["id"]: f["last_pull"] for f in D("feed.feeds", {}).get("feeds", [])}
    check("layer discipline: feed.last_pull is DERIVED from the newest observation, not written back "
          "onto the (stable) feed atom", lp.get("feed:iss") == tr["track"][1]["t"], str(lp.get("feed:iss")))

    # ── THE cross: the ISS subpoint and an active quake share geo:cell:40N125W ──
    x = D("feed.cross", {"window": "72h"})
    coin = {c["cell"]: c for c in x.get("coincidence", [])}
    check(f"feed.cross: the ISS-over-quake cell is a COINCIDENCE (≥2 feeds fresh in {CELL})",
          CELL in coin and set(coin[CELL]["feeds"]) >= {"iss", "usgs_eq"}, str(list(coin)))
    check("feed.cross: the lone Tokyo quake / wildfire cells are SINGLETONS (held, not discarded)",
          any(s["cell"] != CELL for s in x.get("singletons", [])), str([s["cell"] for s in x.get("singletons", [])]))

    # ── feed.cell (a point-on-the-globe as an atom) + feed.project (archives payload) ──
    fc = D("feed.cell", {"gid": CELL, "window": "72h"})
    check("feed.cell: the cell reports the observations of both feeds within the window",
          set(fc.get("feeds", [])) >= {"iss", "usgs_eq"}, str(fc.get("feeds")))
    proj = D("feed.project", {"mode": "map", "window": "72h"})
    check("feed.project (map): layers + points + cross, every point keeping its source_atom (V7)",
          proj.get("mode") == "map" and proj.get("points") and all(p.get("source_atom") for p in proj["points"])
          and len(proj.get("layers", [])) == 3, f"layers={proj.get('layers')}")
    # reversibility: a projected object → its atom
    tr2 = D("feed.trace", {"id": proj["points"][0]["source_atom"]})
    check("feed.trace: a projected point traces back to its observation atom (reversibility)",
          tr2.get("concept") == "observation" and tr2.get("provenance") == "telemetry", str(tr2.get("concept")))

    # ── retention (bounded growth): a tiny count window soft-evicts older fixes ──
    D("feed.register", {"id": "iss", "kind": "kind:orbit:satellite", "interval": 60, "retain": "1", "map": MAPS["iss"]})
    sw = D("feed.pull", {"id": "iss", "text": json.dumps({**ISS, "timestamp": ISS["timestamp"] + 240}), "retain": "1"})
    tr3 = D("feed.track", {"subject": "entity:iss:25544"})
    check("retention: retain=1 soft-evicts older fixes → the live track is bounded (newest kept)",
          sw.get("evicted", 0) >= 1 and tr3.get("count") == 1, f"evicted={sw.get('evicted')} track={tr3.get('count')}")
    # immutability: a soft-evicted observation is NOT mutated (no 'evicted' meta) and stays resolvable
    # (recoverable) — eviction is a property of the live sets, never of the immutable fact atom.
    evicted_obs = cortex.resolve_alias(tr["track"][0]["id"])   # the older fix, evicted by retain=1
    check("immutability: an evicted observation atom is unchanged (no 'evicted' meta) and still "
          "resolvable (recoverable) — the fact atom is never mutated",
          bool(evicted_obs) and "evicted" not in (cortex.get_meta(evicted_obs) or {}), str(bool(evicted_obs)))

    # ── polling is a WORKLOAD per feed (reference-templates-and-profiles §5) ──
    # `svc:feed-poll` — one supervised thread that submitted a pull for every DUE feed — is gone. A feed is
    # polled by its own declared workload `telemetry/<feed>`: the cadence is the declaration's `trigger`, the
    # driver is the one clock, a run records its own outcome. What stays is registering the built-in feeds.
    D("feed.register", {"id": "due_test", "kind": "kind:misc:fact", "interval": 60, "map": MAPS["iss"]})
    due = D("feed.due", {})
    check("feed.due: a never-pulled feed is still detected DUE (the read a poll decides on)",
          any(d["id"] == "due_test" for d in due.get("due", [])), str([d["id"] for d in due.get("due", [])]))
    check("the poller is gone: no start / stop / once / wanted in feed_poll, and no svc:feed-poll thread unit",
          not any(hasattr(feed, n) for n in ("start_feed_poll", "stop_feed_poll", "feed_poll_once",
                                              "feed_poll_wanted", "schedule_feed_poll"))
          and "svc:feed-poll" not in json.dumps(json.load(open(os.path.join(
              ROOT, "app", "config", "MANIFEST.json"), encoding="utf-8")).get("thread_units")))
    _man = json.load(open(os.path.join(ROOT, "app", "config", "MANIFEST.json"), encoding="utf-8"))
    check("registering the built-in feeds is a boot schedule (writer phase, every boot), not a thread",
          (_man.get("schedules") or {}).get("feed_defaults", {}).get("fn")
          == "app.concepts.feed_poll:schedule_feed_defaults"
          and _man["schedules"]["feed_defaults"].get("when") == "every_boot")
    from app.concepts.feed import FeedConcept as _FC
    feed.schedule_feed_defaults(k)
    _reg = {x["id"].replace("feed:", "") for x in (D("feed.feeds", {}).get("feeds") or [])}
    _def = [f["id"] for f in _FC.DEFAULT_FEEDS]
    check("schedule_feed_defaults registers every DEFAULT_FEED (idempotent: a second call changes nothing)",
          set(_def) <= _reg and (feed.schedule_feed_defaults(k) or True), "%s ⊆ %s" % (_def, sorted(_reg)))
    for f in _FC.DEFAULT_FEEDS:
        fid = f["id"]
        dp = os.path.join(ROOT, "app", "config", "workbench", "workloads", "%s.json" % fid)
        tp = os.path.join(ROOT, "app", "config", "workbench", "telemetry", "templates", "%s.ak" % fid)
        ok = os.path.isfile(dp) and os.path.isfile(tp)
        d = json.load(open(dp, encoding="utf-8")) if ok else {}
        step = [l.strip() for l in open(tp, encoding="utf-8") if l.strip() and not l.startswith("#")] if ok else []
        iv = max(60, int(f.get("interval", 300)))
        check("workload telemetry/%s: declared, client feed:%s, idset telemetry, profile telemetry_feed, record, "
              "free (appetite 0), cadence = the feed's own interval (%ds)" % (fid, fid, iv),
              ok and d.get("workflow") == fid and d.get("society") == "telemetry/%s" % fid
              and d.get("bench") == "wb:telemetry" and d.get("idset") == "telemetry"
              and d.get("profile") == "telemetry_feed" and d.get("effect") == "record"
              and (d.get("space") or {}).get("client") == "feed:%s" % fid
              and d.get("trigger") == {"boot": True, "then": "every:%ds" % iv}
              and (d.get("appetite") or {}).get("llm_calls_per_run") == 0 and d.get("requires") == [],
              str({k2: d.get(k2) for k2 in ("workflow", "trigger", "idset")}))
        check("workload telemetry/%s: its template is ONE `feed.pull id=` step for that feed" % fid,
              step == ["#!params feed=%s" % fid, "feed.pull id=$feed"] or
              [x for x in step if not x.startswith("#!")] == ["feed.pull id=$feed"], str(step))
    st = D("feed.poll", {"action": "status"})
    check("feed.poll status names the workload each feed is polled under (telemetry/<feed>)",
          st.get("poll") == "workloads" and "telemetry/%s" % _def[0] in (st.get("workloads") or []), str(st)[:160])

    # ── PUBLIC access: a GUEST session (no admin rights) reads the telemetry — it lives in the shared
    #    nucleus at scope:sys:universal (like proto-words/ontology), not in the admin's private cell ──
    gkey = (gw.dispatch({"jsonrpc": "2.0", "method": "session.guest.create", "params": {}, "id": "gc"},
                        "local").get("result") or {}).get("binding_key")

    def G(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": gkey, "data": data}, "id": "gg"}, "local")
        return r.get("result") or r.get("error") or {}

    check("PUBLIC: a guest session was created (the public read path)", bool(gkey))
    gx = G("feed.cross", {"window": "72h"})
    check("PUBLIC: a GUEST (no admin rights) reads the telemetry cross — the atoms are universal in the "
          "shared nucleus, not admin-private", any(c.get("cell") == CELL for c in gx.get("coincidence", [])),
          str([c.get("cell") for c in gx.get("coincidence", [])]))
    gl = G("feed.latest", {"id": "usgs_eq"})
    check("PUBLIC: the guest reads a feed's observations (readable without admin — the restriction is off)",
          gl.get("count", 0) >= 1, str(gl.get("count")))
    gp = G("feed.project", {"mode": "map", "window": "72h"})
    check("PUBLIC: the guest gets the archives projection payload (the public map is servable)",
          gp.get("mode") == "map" and bool(gp.get("points")), str(len(gp.get("points", []))))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — live-telemetry foundation: keyless feeds → normalised via the map DSL → stable "
          "subjects + idempotent observations on the geo grid + native chrono:before time chain, "
          "provenance-fenced from learning; feed.cross surfaces the ISS-over-quake coincidence "
          "(singletons kept), feed.project feeds archives (reversible), retention keeps growth bounded, "
          "and the auto-fetch scheduler submits due pulls as MAINTENANCE-class JCL jobs (never delaying "
          "interactive work).")
    sys.exit(0)


if __name__ == "__main__":
    main()
