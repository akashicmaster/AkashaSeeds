#!/usr/bin/env python3
"""
live_lab.py — build the live-telemetry demo on a throwaway Cell and emit the archives fixtures.

Registers the three v1 keyless feeds (EONET disasters, USGS earthquakes, ISS position) and drives
them OFFLINE with sample payloads shaped exactly like the real APIs (via `feed.pull id= text=<raw>`,
so the real map-DSL normalisation runs), builds an ISS ground-track of several fixes, and arranges
two spatiotemporal COINCIDENCES (the ISS passing over an active wildfire + quake off N California;
a volcano over a quake in Indonesia). Then emits the read-only projection fixtures the /archives/live/
map renders: feed_map / feed_cross / feed_track / feed_feeds + index.

  python app/scripts/live_lab.py --emit-projection app/archives/live
  python app/scripts/live_lab.py --trace

FLOW via the CLI (`sys.cli_exec`), VISUALISE via RPC — same convention as app/scripts/stylometry_lab.py.
Timestamps are now-relative so the freshly-generated fixtures fall inside the default cross window.
"""
import argparse, hashlib, json, math, os, sys, tempfile, shlex, time as _time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")

NOW = int(_time.time())
def iso(sec):
    return datetime.fromtimestamp(sec, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# The live-provisionable public feeds are the single source of truth on the model
# (FeedConcept.DEFAULT_FEEDS = eonet / usgs_eq / iss — real-API map-DSLs, auto-registered at boot).
# The demo adds three OFFLINE-only feeds (aircraft / sea level / ships) whose real-API wiring isn't
# done yet, so the showcase map is richer while the live map provisions only what actually fetches.
from app.concepts.feed import FeedConcept
_DEMO_ONLY = [
    {"id": "aircraft", "kind": "kind:air:aircraft", "interval": 30, "retain": "3h",
     "url": "https://opensky-network.org/api/states/all",     # anonymous; real response is positional arrays
     "title": "OpenSky — aircraft state vectors",
     "map": "items=$.states; id=$.icao24; lat=$.lat; lon=$.lon; alt=$.alt; title=$.callsign"},
    {"id": "sea_level", "kind": "kind:ocean:tide", "interval": 900, "retain": "48h",
     "url": "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",   # keyless CO-OPS (per-station)
     "title": "NOAA CO-OPS — coastal water level",
     "map": "items=$.stations; id=$.id; lat=$.lat; lon=$.lon; mag=$.level; title=$.name"},
    {"id": "ships", "kind": "kind:marine:vessel", "interval": 120, "retain": "12h",
     "url": "",                                               # AIS (e.g. aisstream.io) needs a key when live
     "title": "AIS — vessel positions (key required when live)",
     "map": "items=$.vessels; id=$.mmsi; lat=$.lat; lon=$.lon; title=$.name"},
]
FEEDS = list(FeedConcept.DEFAULT_FEEDS) + _DEMO_ONLY

# aircraft over the W-Pacific storm cell (≈16N,131E) → cross with the EONET typhoon
AIRCRAFT = {"states": [
    {"icao24": "a1b2c3", "callsign": "UAL823", "lat": 16.8, "lon": 131.4, "alt": 10600},
    {"icao24": "d4e5f6", "callsign": "ANA211", "lat": 37.2, "lon": 140.9, "alt": 11200},
    {"icao24": "778899", "callsign": "BAW177", "lat": 51.0, "lon": -30.0, "alt": 10900},
    {"icao24": "0a1b2c", "callsign": "QFA009", "lat": -25.0, "lon": 133.0, "alt": 11500},
    {"icao24": "3d4e5f", "callsign": "AAL120", "lat": 40.1, "lon": -100.0, "alt": 10700},
    {"icao24": "6f7a8b", "callsign": "AFR066", "lat": 24.0, "lon": 8.0, "alt": 11000},
]}
# a vessel off the Chilean coast in the same cell as the M6.0 quake (≈-30,-71) → cross with USGS
SHIPS = {"vessels": [
    {"mmsi": "224100001", "name": "MV Atacama", "lat": -30.3, "lon": -71.5},
    {"mmsi": "636014444", "name": "Ever Pacific", "lat": 30.0, "lon": 32.5},
    {"mmsi": "431000222", "name": "Nippon Maru", "lat": 34.6, "lon": 139.9},
    {"mmsi": "563099888", "name": "Pacific Star", "lat": 8.0, "lon": -140.0},
]}
# a tide station offshore Honshu in the same cell as the M5.1 quake (≈38N,142E) → cross with USGS
SEALEVEL = {"stations": [
    {"id": "9414290", "name": "San Francisco", "lat": 37.8, "lon": -122.5, "level": 1.3},
    {"id": "coops_honshu", "name": "Off Honshu", "lat": 38.3, "lon": 142.0, "level": 0.9},
    {"id": "1615680", "name": "Kahului", "lat": 20.9, "lon": -156.5, "level": 0.6},
    {"id": "coops_valpo", "name": "Valparaíso", "lat": -33.0, "lon": -71.6, "level": 0.8},
]}

# EONET events (one nested-geometry payload). A wildfire sits in the N-California cell (≈40N,124W).
EONET = {"events": [
    {"id": "EONET_wildfire_norcal", "title": "Wildfire — Northern California",
     "geometry": [{"coordinates": [-124.3, 40.2], "date": iso(NOW - 3600)}]},
    {"id": "EONET_typhoon_wpac", "title": "Severe Storm — Western Pacific",
     "geometry": [{"coordinates": [131.0, 16.5], "date": iso(NOW - 5400)}]},
    {"id": "EONET_volcano_java", "title": "Volcano — Java, Indonesia",
     "geometry": [{"coordinates": [112.5, -8.2], "date": iso(NOW - 7200)}]},
    {"id": "EONET_wildfire_nsw", "title": "Wildfire — New South Wales",
     "geometry": [{"coordinates": [150.4, -33.4], "date": iso(NOW - 4800)}]},
]}

# USGS quakes (one GeoJSON payload). Two co-locate with disasters/the ISS to make coincidences.
USGS = {"features": [
    {"id": "us_norcal", "geometry": {"coordinates": [-124.5, 40.3, 8.0]},
     "properties": {"time": (NOW - 1500) * 1000, "mag": 4.2, "title": "M4.2 — offshore N California"}},
    {"id": "us_java", "geometry": {"coordinates": [112.4, -8.4, 35.0]},
     "properties": {"time": (NOW - 2400) * 1000, "mag": 4.8, "title": "M4.8 — Java, Indonesia"}},
    {"id": "us_japan", "geometry": {"coordinates": [142.1, 38.2, 30.0]},
     "properties": {"time": (NOW - 900) * 1000, "mag": 5.1, "title": "M5.1 — off Honshu"}},
    {"id": "us_chile", "geometry": {"coordinates": [-71.3, -30.1, 55.0]},
     "properties": {"time": (NOW - 1200) * 1000, "mag": 6.0, "title": "M6.0 — Coquimbo, Chile"}},
    {"id": "us_alaska", "geometry": {"coordinates": [-150.2, 61.1, 40.0]},
     "properties": {"time": (NOW - 600) * 1000, "mag": 3.5, "title": "M3.5 — Anchorage"}},
    {"id": "us_greece", "geometry": {"coordinates": [23.7, 38.1, 12.0]},
     "properties": {"time": (NOW - 3000) * 1000, "mag": 4.0, "title": "M4.0 — Aegean Sea"}},
]}

# the ISS ground-track: 10 fixes over ~90 min (one orbit), inclination-51.6° sinusoid, sweeping east.
# One fix is forced over the N-California cell so the track crosses the wildfire + the M4.2 quake.
def iss_track():
    # a clean eastward ground-track (monotonic lon so the polyline reads as one orbit sweep);
    # index 2 is forced over the N-California cell so the track crosses the wildfire + the M4.2 quake.
    lons = [-176, -150, -124.4, -92, -52, -8, 40, 88, 132, 168]
    pts = []
    for i, lon in enumerate(lons):
        t = NOW - (len(lons) - i) * 540                               # 9-min steps, all within the window
        lat = 40.3 if i == 2 else round(50 * math.sin((i / (len(lons) - 1)) * math.pi * 1.9 - 0.3), 1)
        pts.append({"id": 25544, "latitude": lat, "longitude": lon,
                    "altitude": 419 + (i % 3), "timestamp": t})
    return pts


def main():
    ap = argparse.ArgumentParser(description="Build the live-telemetry demo and emit archives fixtures.")
    ap.add_argument("--emit-projection", metavar="DIR", help="write feed_map/cross/track/feeds + index")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = tempfile.mkdtemp(prefix="livelab_")
    gw = client.embedded(base, "seeds", load_ontology=False)
    k = gw.kernel_client

    step = [0]
    def _trace(kind, line):
        if args.trace:
            step[0] += 1
            print("%3d ┃ [%s] %s" % (step[0], kind, line))

    def D(method, data, tok="admin"):
        _trace("rpc", method + " " + json.dumps(data, ensure_ascii=False)[:80])
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok, "data": data}, "id": "m"}, "local")
        return r.get("result") if isinstance(r, dict) else r

    def C(method, **kw):
        line = " ".join([method] + ["%s=%s" % (kk, shlex.quote(str(vv))) for kk, vv in kw.items()])
        _trace("cli", line)
        return gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                            "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local")

    D("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})

    # ── [cli] register the feeds (config-as-data) ──
    for f in FEEDS:
        C("feed.register", id=f["id"], kind=f["kind"], interval=f["interval"],
          retain=f["retain"], url=f["url"], title=f["title"], map=f["map"])

    # ── [cli] drive them offline with sample payloads (the real map-DSL normalisation runs) ──
    C("feed.pull", id="eonet", text=json.dumps(EONET))
    C("feed.pull", id="usgs_eq", text=json.dumps(USGS))
    for fix in iss_track():                          # each pull = one ISS fix → the trajectory
        C("feed.pull", id="iss", text=json.dumps(fix))
    C("feed.pull", id="aircraft", text=json.dumps(AIRCRAFT))
    C("feed.pull", id="sea_level", text=json.dumps(SEALEVEL))
    C("feed.pull", id="ships", text=json.dumps(SHIPS))

    # ── report ──
    cross = D("feed.cross", {"window": "6h"}) or {}
    print("▸ feeds: %d · coincidence cells: %d · singletons: %d" % (
        len(FEEDS), len(cross.get("coincidence", [])), len(cross.get("singletons", []))))
    for c in cross.get("coincidence", []):
        print("    ⊕ cell %-10s  feeds=%s  (×%d)" % (c["cell"], ",".join(c["feeds"]), c["count"]))

    if args.emit_projection:
        outdir = os.path.abspath(args.emit_projection)
        os.makedirs(outdir, exist_ok=True)
        fixtures = {
            "feed_map.json":   D("feed.project", {"mode": "map", "window": "6h"}),
            "feed_cross.json": D("feed.project", {"mode": "cross", "window": "6h"}),
            "feed_track.json": D("feed.project", {"mode": "track", "subject": "entity:iss:25544"}),
            "feed_feeds.json": D("feed.feeds", {}),
        }
        for fn, payload in fixtures.items():
            with open(os.path.join(outdir, fn), "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        index = {"generated_at": iso(NOW), "window": "6h", "note": "illustrative snapshot",
                 "feeds": [{"id": f["id"], "kind": f["kind"], "title": f["title"]} for f in FEEDS]}
        with open(os.path.join(outdir, "index.json"), "w", encoding="utf-8") as fh:
            json.dump(index, fh, ensure_ascii=False, indent=2)
        print("\n▸ wrote %d fixtures + index to %s" % (len(fixtures), outdir))

    if not args.keep:
        import shutil
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
