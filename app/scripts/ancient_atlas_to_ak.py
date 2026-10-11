#!/usr/bin/env python3
"""
ancient_atlas_to_ak.py — derive the `ancient` ONTOLOGY PACK from the Ancient Civilizations atlas.

The atlas page (`app/archives/ancient/`) is the curated authoring source: `index.html` carries the 14
regions and ~77 civilizations (name / endonym / era / note / atom id) in its REGIONS table, and its
sidecar `atlas.json` carries the geography (modern-country membership, schematic extent, and SOURCED
excavation sites with coordinates + source links) — itself generated from scripts/civ_atlas_data.py.
This generator reads BOTH and emits `app/ontology/ancient/civilizations.ak` so the civilizations, their
HEADWORDS (name + endonym), their SOURCE LINKS, their excavation sites, AND their modern-country
membership + schematic extent are first-class ontology atoms — queryable, linked, provenance-bearing
— exactly the `ancient:<…>` ids the GUI references (GUI → CLI → ontology is reversible). Regenerable:
re-run whenever the atlas grows. (atlas.json is read as JSON, so unicode / apostrophes in site names
and notes survive intact — unlike regex-scraping inline JS.)

  Regions      → `ancient:region:<id>`  (sys:is_a ancient:region), in set:ancient:regions
  Civilizations→ `ancient:<slug>`       (sys:is_a ancient:civilization, ancient:in_region <region>),
                 headword name aliased, endonym/era/note in the description, in set:ancient:all
  Source links → `ancient:src:<civ>:<label>`   (civ ancient:source →), URL in the description
  Excavation   → `ancient:site:<civ>:<name>`   (civ ancient:site →), lat/lon/note in the description
  Country      → geo:country:<ISO3>            (civ ancient:spans_country →), modern land of the core
  Extent       → `ancient:extent:<civ>`        (civ ancient:has_extent →), schematic polygon in desc
  Old map      → `ancient:oldmap:<civ>:<t>`    (civ ancient:has_oldmap →), title/date/attribution/url
  Region pin   → `ancient:region:<id>:pin`     (region geo:has_coordinate →), the atlas map marker

Run:  python scripts/gen_civ_atlas.py         (writes app/archives/ancient/atlas.json)
Then: python app/scripts/ancient_atlas_to_ak.py   (writes app/ontology/ancient/civilizations.ak)
Then: python scripts/gen_lexicon.py && python test/verify_lexicon.py --all
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "app", "archives", "ancient", "index.html")
ATLAS_JSON = os.path.join(ROOT, "app", "archives", "ancient", "atlas.json")
OUT_DIR = os.path.join(ROOT, "app", "ontology", "ancient")
OUT = os.path.join(OUT_DIR, "civilizations.ak")


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def _clean(s):
    """Make a value safe as an .ak description: no double-quotes, single line, collapsed spaces."""
    s = (s or "").replace('"', "'").replace("\\", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _block(text, start_re, open_ch, close_ch):
    """Return the substring of one balanced open/close block that begins at `start_re`."""
    m = re.search(start_re, text)
    if not m:
        return ""
    i = text.index(open_ch, m.start())
    depth, j = 0, i
    while j < len(text):
        if text[j] == open_ch:
            depth += 1
        elif text[j] == close_ch:
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
        j += 1
    return text[i:]


def _load_geo():
    """Per-civ geography from app/scripts/civ_atlas_data.py — the DEV authoring source of the atlas.

    This is the UPSTREAM source: civ_atlas_data.py → (this generator) → the ontology pack →
    (app/scripts/ancient_atlas_project.py) → app/archives/ancient/atlas.json. The GUI reads the projection,
    so the GUI is a projection of the ONTOLOGY (not a sibling of it).
    """
    import importlib.util
    data_py = os.path.join(ROOT, "app", "scripts", "civ_atlas_data.py")
    spec = importlib.util.spec_from_file_location("civ_atlas_data", data_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    atlas = {}
    for atom, e in mod.ATLAS.items():
        atlas[atom] = {
            "sources": [{"label": s[1], "url": s[5]} for s in (e.get("sites") or [])],
            "sites": [{"name": s[1], "lat": s[2], "lon": s[3], "note": s[4]} for s in (e.get("sites") or [])],
            "countries": e.get("c") or [],
            "hull": e.get("hull") or [],
            "note": e.get("note", ""),
            "maps": [{"title": m[0], "date": m[1], "attribution": m[2], "url": m[3]} for m in (e.get("maps") or [])],
        }
    return atlas


def parse(html):
    regions_txt = _block(html, r"var\s+REGIONS\s*=\s*", "[", "]")

    # ── ATLAS geography: from civ_atlas_data.py (the authoring source; ontology is derived from it) ──
    atlas = _load_geo()

    # ── REGIONS: each header, then the civs between it and the next header ──
    hdr = re.compile(r"\{\s*no\s*:\s*(\d+)\s*,\s*id\s*:\s*'([^']+)'\s*,\s*name\s*:\s*'([^']*)'\s*,"
                     r"\s*sub\s*:\s*'([^']*)'\s*,\s*lon\s*:\s*([-\d.]+)\s*,\s*lat\s*:\s*([-\d.]+)\s*,"
                     r"\s*lead\s*:\s*'([^']*)'")
    civ = re.compile(r"\{\s*name\s*:\s*'([^']*)'\s*,\s*nat\s*:\s*'([^']*)'\s*,\s*era\s*:\s*'([^']*)'\s*,"
                     r"\s*note\s*:\s*'([^']*)'\s*,\s*atom\s*:\s*'(ancient:[^']+)'\s*\}")
    heads = list(hdr.finditer(regions_txt))
    regions = []
    for idx, h in enumerate(heads):
        seg = regions_txt[h.end():(heads[idx + 1].start() if idx + 1 < len(heads) else len(regions_txt))]
        civs = [{"name": n, "nat": na, "era": e, "note": nt, "atom": a}
                for n, na, e, nt, a in civ.findall(seg)]
        regions.append({"no": int(h.group(1)), "id": h.group(2), "name": h.group(3),
                        "sub": h.group(4), "lon": h.group(5), "lat": h.group(6),
                        "lead": h.group(7), "civs": civs})
    return regions, atlas


def emit(regions, atlas):
    L = []
    L.append("# Ancient Civilizations — GENERATED from app/archives/ancient/ (index.html REGIONS +")
    L.append("# atlas.json geography) by scripts/ancient_atlas_to_ak.py. Do not edit by hand; re-run it.")
    L.append("# Every civilization, region, source link, excavation site, modern-country membership and")
    L.append("# schematic extent the atlas carries, as first-class ancient:<…> atoms the GUI references.")
    L.append("")
    L.append('def "ancient:civilization" "An ancient civilization — a culture, kingdom or empire of '
             'the old world, gathered by region in the Ancient Civilizations atlas."')
    L.append('al ancient:civilization ancient_civilization')
    L.append('def "ancient:region" "A region of the ancient world — a sphere of related ancient '
             'cultures on the atlas (the fertile crescent, the Andes, Oceania, and so on)."')
    L.append('al ancient:region ancient_region')
    L.append("")

    n_civ = n_src = n_site = n_country = n_ext = n_map = n_pin = 0
    seen_alias = set()

    def alias(atom, want):
        w = _slug(want)
        if w and w not in seen_alias:
            seen_alias.add(w)
            L.append("al %s %s" % (atom, w))

    for r in regions:
        ratom = "ancient:region:%s" % r["id"]
        desc = "%s — %s. %s" % (_clean(r["name"]), _clean(r["sub"]), _clean(r["lead"]))
        L.append('def "%s" "%s"' % (ratom, desc))
        alias(ratom, r["id"])
        L.append("ln %s ancient:region sys:is_a" % ratom)
        L.append('set.add name="set:ancient:regions" id="%s"' % ratom)
        # the region's atlas pin (the map marker lon/lat) — so nothing the GUI shows is ontology-absent
        if r.get("lon") and r.get("lat"):
            patom = "ancient:region:%s:pin" % r["id"]
            L.append('def "%s" "%s, %s (WGS84) — atlas map pin of %s"' % (patom, r["lat"], r["lon"], _clean(r["name"])))
            L.append("ln %s %s geo:has_coordinate" % (ratom, patom))
            n_pin += 1
        for c in r["civs"]:
            catom = c["atom"]
            parts = [_clean(c["name"])]
            meta = []
            if c["nat"]:
                meta.append("endonym %s" % _clean(c["nat"]))
            if c["era"]:
                meta.append(_clean(c["era"]))
            head = "%s (%s)" % (parts[0], ", ".join(meta)) if meta else parts[0]
            desc = "%s — %s" % (head, _clean(c["note"])) if c["note"] else head
            L.append('def "%s" "%s"' % (catom, desc))
            alias(catom, c["name"])
            L.append("ln %s ancient:civilization sys:is_a" % catom)
            L.append("ln %s %s ancient:in_region" % (catom, ratom))
            L.append('set.add name="set:ancient:all" id="%s"' % catom)
            L.append('set.add name="set:ancient:region:%s:members" id="%s"' % (r["id"], catom))
            n_civ += 1
            det = atlas.get(catom) or {}
            cslug = _slug(catom.replace("ancient:", ""))
            for s in det.get("sources", []):
                satom = "ancient:src:%s:%s" % (cslug, _slug(s["label"]))
                L.append('def "%s" "%s — %s"' % (satom, _clean(s["label"]), s["url"]))
                L.append("ln %s %s ancient:source" % (catom, satom))
                L.append('set.add name="set:ancient:sources" id="%s"' % satom)
                n_src += 1
            for st in det.get("sites", []):
                statom = "ancient:site:%s:%s" % (cslug, _slug(st["name"]))
                L.append('def "%s" "%s (%s, %s) — %s"' % (
                    statom, _clean(st["name"]), st["lat"], st["lon"], _clean(st["note"])))
                L.append("ln %s %s ancient:site" % (catom, statom))
                L.append('set.add name="set:ancient:sites" id="%s"' % statom)
                n_site += 1
            # modern-country membership (the CORE, approximate) → the existing geo:country:<ISO3> atoms
            for iso in det.get("countries", []):
                L.append("ln %s geo:country:%s ancient:spans_country" % (catom, iso))
                n_country += 1
            # schematic territorial extent (optional) — the polygon rides the description, never a border
            hull = det.get("hull") or []
            if hull:
                eatom = "ancient:extent:%s" % cslug
                poly = "; ".join("%s,%s" % (round(p[0], 4), round(p[1], 4)) for p in hull)
                note = _clean(det.get("note", ""))
                L.append('def "%s" "%s Schematic core outline (approximate, not a surveyed border). '
                         'polygon lon,lat: %s"' % (eatom, note, poly))
                L.append("ln %s %s ancient:has_extent" % (catom, eatom))
                L.append('set.add name="set:ancient:extents" id="%s"' % eatom)
                n_ext += 1
            # historical maps from (or depicting) the era the civilization flourished — link + provenance
            for m in det.get("maps", []):
                matom = "ancient:oldmap:%s:%s" % (cslug, _slug(m["title"]))
                L.append('def "%s" "%s (%s) — %s | %s"' % (
                    matom, _clean(m["title"]), _clean(m["date"]), _clean(m["attribution"]), m["url"]))
                L.append("ln %s %s ancient:has_oldmap" % (catom, matom))
                L.append('set.add name="set:ancient:oldmaps" id="%s"' % matom)
                n_map += 1
        L.append("")
    return "\n".join(L) + "\n", n_civ, n_src, n_site, n_country, n_ext, n_map, n_pin


def main():
    with open(SRC, "r", encoding="utf-8") as f:
        html = f.read()
    regions, atlas = parse(html)
    if not regions:
        print("[ancient] no regions parsed — aborting", file=sys.stderr)
        sys.exit(1)
    text, n_civ, n_src, n_site, n_country, n_ext, n_map, n_pin = emit(regions, atlas)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("[ancient] wrote %s — %d regions, %d civilizations, %d source links, %d sites, "
          "%d country links, %d extents, %d old-maps, %d region pins"
          % (os.path.relpath(OUT, ROOT), len(regions), n_civ, n_src, n_site, n_country, n_ext, n_map, n_pin))


if __name__ == "__main__":
    main()
