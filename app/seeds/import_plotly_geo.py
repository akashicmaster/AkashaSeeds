#!/usr/bin/env python3
"""
Import plotly geographic reference datasets into the Akasha nucleus.

Three datasets:
  world_gdp_2014    → 2014_world_gdp_with_codes.csv  → geo:country:* atoms
  us_cities_2014    → 2014_us_cities.csv              → geo:city:us:* atoms
  us_airports_2011  → 2011_february_us_airport_traffic.csv → geo:airport:* atoms

Each CSV is also stored as a full-JSON raw dataset atom with alias
plotly:dataset:{id} and added to set:plotly:datasets.

Country atoms → set:geo:countries, set:geo:index
City atoms    → set:geo:cities:us, set:geo:country:USA:cities
Airport atoms → set:geo:airports:us, set:geo:country:USA:airports

Bridge links:
  geo:is_in      (city → country, airport → country, airport → city)
  geo:from_dataset (entity → dataset raw atom)

Run from project root:
  python app/seeds/import_plotly_geo.py
"""

import sys
import os
import json
import csv
import re
import io
from urllib.request import urlopen

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from lib.akasha.composite import NucleusEngine

BASE_DIR = os.path.join(_ROOT, "data")
NUCLEUS_DB = os.path.join(BASE_DIR, "central", "nucleus.db")
AUTHOR = "system:import:plotly_geo"

DATASETS = {
    "world_gdp_2014": (
        "https://raw.githubusercontent.com/plotly/datasets/master/"
        "2014_world_gdp_with_codes.csv"
    ),
    "us_cities_2014": (
        "https://raw.githubusercontent.com/plotly/datasets/master/"
        "2014_us_cities.csv"
    ),
    "us_airports_2011": (
        "https://raw.githubusercontent.com/plotly/datasets/master/"
        "2011_february_us_airport_traffic.csv"
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _fetch_csv(url: str) -> list:
    print(f"  Fetching: {url}")
    with urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def _put_dataset_atom(nucleus, dataset_id: str, url: str, rows: list) -> str:
    """Store the full CSV as a JSON atom. Returns nucleus key."""
    alias = f"plotly:dataset:{dataset_id}"
    existing = nucleus.resolve_alias(alias)
    if existing:
        print(f"  Dataset atom exists: {alias}")
        return existing

    payload = json.dumps(
        {"source": "plotly/datasets", "url": url, "license": "MIT", "rows": rows},
        ensure_ascii=False,
    )
    meta = {
        "type": "plotly_dataset",
        "dataset_id": dataset_id,
        "source": "plotly/datasets",
        "url": url,
        "license": "MIT",
        "row_count": len(rows),
    }
    key = nucleus.put_atom(payload, meta, AUTHOR, alias=alias)
    nucleus.add_to_set("set:plotly:datasets", key)
    print(f"  Dataset atom created: {alias}  rows={len(rows)}")
    return key


# ---------------------------------------------------------------------------
# World GDP → geo:country:* atoms
# ---------------------------------------------------------------------------

def _import_countries(nucleus, rows: list, dataset_key: str) -> None:
    created = skipped = 0
    for row in rows:
        name = row.get("COUNTRY", "").strip()
        iso3 = row.get("CODE", "").strip()
        gdp_s = row.get("GDP (BILLIONS)", "").strip()

        if not name or not iso3:
            continue

        alias = f"geo:country:{iso3}"
        if nucleus.resolve_alias(alias):
            skipped += 1
            continue

        try:
            gdp = float(gdp_s)
        except (ValueError, TypeError):
            gdp = None

        meta = {
            "type": "geo_country",
            "name": name,
            "iso3": iso3,
            "gdp_billions": gdp,
            "coordinate_system": "wgs84",
        }
        key = nucleus.put_atom(name, meta, AUTHOR, alias=alias)
        nucleus.add_to_set("set:geo:countries", key)
        nucleus.add_to_set("set:geo:index", key)
        nucleus.put_link(key, dataset_key, "geo:from_dataset")
        # Also register the country name slug as a navigable bare alias
        # so `look france`, `look germany`, `look china` etc. resolve directly.
        name_slug = _slug(name)
        if name_slug and not nucleus.resolve_alias(name_slug):
            nucleus.core.put_alias(key, name_slug)
        created += 1

    print(f"  Countries: {created} created, {skipped} skipped (already exist)")


# ---------------------------------------------------------------------------
# US Cities → geo:city:us:* atoms
# ---------------------------------------------------------------------------

def _import_us_cities(nucleus, rows: list, dataset_key: str) -> None:
    # Sort by population descending so the largest city wins the plain slug
    def _pop(r):
        try:
            return int(r.get("pop", 0))
        except (ValueError, TypeError):
            return 0

    rows_sorted = sorted(rows, key=_pop, reverse=True)
    usa_key = nucleus.resolve_alias("geo:country:USA")
    created = skipped = 0

    for row in rows_sorted:
        name = row.get("name", "").strip()
        lat_s = row.get("lat", "").strip()
        lon_s = row.get("lon", "").strip()
        pop_s = row.get("pop", "").strip()

        if not name:
            continue

        alias = f"geo:city:us:{_slug(name)}"
        if nucleus.resolve_alias(alias):
            skipped += 1
            continue

        try:
            lat = float(lat_s)
        except (ValueError, TypeError):
            lat = None
        try:
            lon = float(lon_s)
        except (ValueError, TypeError):
            lon = None
        try:
            pop = int(pop_s)
        except (ValueError, TypeError):
            pop = None

        meta = {
            "type": "geo_city",
            "name": name,
            "country_iso3": "USA",
            "lat": lat,
            "lon": lon,
            "pop": pop,
            "coordinate_system": "wgs84",
        }
        key = nucleus.put_atom(name, meta, AUTHOR, alias=alias)
        nucleus.add_to_set("set:geo:cities:us", key)
        nucleus.add_to_set("set:geo:country:USA:cities", key)

        if usa_key:
            nucleus.put_link(key, usa_key, "geo:is_in")
        nucleus.put_link(key, dataset_key, "geo:from_dataset")
        created += 1

    print(f"  US cities: {created} created, {skipped} skipped (duplicate slug, lower-pop variant)")


# ---------------------------------------------------------------------------
# US Airports → geo:airport:* atoms
# ---------------------------------------------------------------------------

def _import_us_airports(nucleus, rows: list, dataset_key: str) -> None:
    usa_key = nucleus.resolve_alias("geo:country:USA")
    created = skipped = 0

    for row in rows:
        iata = row.get("iata", "").strip()
        name = row.get("airport", "").strip()
        city = row.get("city", "").strip()
        state = row.get("state", "").strip()
        lat_s = row.get("lat", "").strip()
        lon_s = row.get("long", "").strip()
        cnt_s = row.get("cnt", "").strip()

        if not iata or not name:
            continue

        alias = f"geo:airport:{iata}"
        if nucleus.resolve_alias(alias):
            skipped += 1
            continue

        try:
            lat = float(lat_s)
        except (ValueError, TypeError):
            lat = None
        try:
            lon = float(lon_s)
        except (ValueError, TypeError):
            lon = None
        try:
            cnt = int(cnt_s)
        except (ValueError, TypeError):
            cnt = 0

        meta = {
            "type": "geo_airport",
            "iata": iata,
            "name": name,
            "city": city,
            "state": state,
            "country_iso3": "USA",
            "lat": lat,
            "lon": lon,
            "traffic_count": cnt,
            "coordinate_system": "wgs84",
        }
        key = nucleus.put_atom(name, meta, AUTHOR, alias=alias)
        nucleus.add_to_set("set:geo:airports:us", key)
        nucleus.add_to_set("set:geo:country:USA:airports", key)

        if usa_key:
            nucleus.put_link(key, usa_key, "geo:is_in")

        # Link airport → nearest city atom if slug resolves
        city_key = nucleus.resolve_alias(f"geo:city:us:{_slug(city)}")
        if city_key:
            nucleus.put_link(key, city_key, "geo:is_in")

        nucleus.put_link(key, dataset_key, "geo:from_dataset")
        created += 1

    print(f"  US airports: {created} created, {skipped} skipped (already exist)")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _print_summary(nucleus):
    import sqlite3
    con = sqlite3.connect(NUCLEUS_DB)
    sets_to_check = [
        "set:plotly:datasets",
        "set:geo:countries",
        "set:geo:index",
        "set:geo:cities:us",
        "set:geo:airports:us",
        "set:geo:country:USA:cities",
        "set:geo:country:USA:airports",
    ]
    print("\nCollection sizes after import:")
    for s in sets_to_check:
        n = con.execute(
            "SELECT COUNT(*) FROM collections WHERE name=?", (s,)
        ).fetchone()[0]
        print(f"  {s}: {n}")
    con.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Akasha — Plotly Geographic Reference Import")
    print(f"Nucleus: {NUCLEUS_DB}\n")

    if not os.path.exists(NUCLEUS_DB):
        print(f"[!] Nucleus DB not found: {NUCLEUS_DB}")
        print("    Start akasha.py at least once to initialize the database.")
        sys.exit(1)

    nucleus = NucleusEngine(NUCLEUS_DB)

    # --- World GDP 2014 ---
    print("=== World GDP 2014 ===")
    world_rows = _fetch_csv(DATASETS["world_gdp_2014"])
    world_key = _put_dataset_atom(nucleus, "world_gdp_2014", DATASETS["world_gdp_2014"], world_rows)
    _import_countries(nucleus, world_rows, world_key)

    # --- US Cities 2014 ---
    print("\n=== US Cities 2014 ===")
    cities_rows = _fetch_csv(DATASETS["us_cities_2014"])
    cities_key = _put_dataset_atom(nucleus, "us_cities_2014", DATASETS["us_cities_2014"], cities_rows)
    _import_us_cities(nucleus, cities_rows, cities_key)

    # --- US Airport Traffic 2011 ---
    print("\n=== US Airport Traffic 2011 ===")
    airport_rows = _fetch_csv(DATASETS["us_airports_2011"])
    airports_key = _put_dataset_atom(nucleus, "us_airports_2011", DATASETS["us_airports_2011"], airport_rows)
    _import_us_airports(nucleus, airport_rows, airports_key)

    _print_summary(nucleus)
    print("\nDone.")


if __name__ == "__main__":
    main()
