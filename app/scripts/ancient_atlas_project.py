# -*- coding: utf-8 -*-
"""Project the `ancient` ONTOLOGY PACK into the GUI's read-only atlas.json.

    python app/scripts/ancient_atlas_project.py     (writes app/archives/ancient/atlas.json)

This is the PROJECTION step that makes the Ancient Civilizations GUI a projection OF the ontology:
it PARSES app/ontology/ancient/civilizations.ak (the source of truth) and emits app/archives/ancient/
atlas.json — the exact data the /ancient/ overlay renders. EVERY datum carries `source_atom`, the
`ancient:*` (or `geo:country:*`) id it came from, so GUI → atom is reversible; nothing on the GUI
exists that is not an atom/link in the ontology (Wikipedia links and historical-map links included).

Pipeline:  app/scripts/civ_atlas_data.py  →  [ancient_atlas_to_ak.py]  →  app/ontology/ancient/civilizations.ak
           →  [THIS]  →  app/archives/ancient/atlas.json  →  the GUI.

Output shape:
  { "civs": { "<atom>": { region, name, nat, era, note, source_atom,
                          countries:[{iso, source_atom}], hull:[[lon,lat]…], extent_atom,
                          sites:[{name,lat,lon,note, source_atom}],
                          sources:[{label,url, source_atom}],
                          oldmaps:[{title,date,attribution,url, source_atom}] } },
    "regions": { "<id>": { no, name, sub, lead, lat, lon, pin_atom, source_atom, civs:[atom…] } } }
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AK = os.path.join(ROOT, "app", "ontology", "ancient", "civilizations.ak")
OUT_JSON = os.path.join(ROOT, "app", "archives", "ancient", "atlas.json")

DASH = " — "  # the em-dash separator the generator uses in every description


def _parse_ak(text):
    defs, aliases, links = {}, {}, []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r'def\s+"([^"]+)"\s+"(.*)"\s*$', s)
        if m:
            defs[m.group(1)] = m.group(2)
            continue
        m = re.match(r'al\s+(\S+)\s+(\S+)\s*$', s)
        if m:
            aliases.setdefault(m.group(1), m.group(2))
            continue
        m = re.match(r'ln\s+(\S+)\s+(\S+)\s+(\S+)\s*$', s)
        if m:
            links.append((m.group(1), m.group(2), m.group(3)))
    return defs, aliases, links


def _civ_meta(desc):
    """'Name (endonym X, ERA) — note' → (name, nat, era, note)."""
    head, _, note = desc.partition(DASH)
    head, note = head.strip(), note.strip()
    name, nat, era = head, "", ""
    mm = re.match(r"^(.*)\(([^()]*)\)\s*$", head)  # the LAST parenthetical is the (endonym…, era) meta
    if mm:
        name = mm.group(1).strip()
        for part in mm.group(2).split(", "):
            part = part.strip()
            if part.lower().startswith("endonym "):
                nat = part[len("endonym "):].strip()
            elif part:
                era = part
    return name, nat, era, note


def _site_meta(desc):
    """'Name (lat, lon) — note' → (name, lat, lon, note)."""
    head, _, note = desc.partition(DASH)
    head, note = head.strip(), note.strip()
    name, lat, lon = head, None, None
    mm = re.match(r"^(.*?)\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)\s*$", head)
    if mm:
        name = mm.group(1).strip()
        lat, lon = float(mm.group(2)), float(mm.group(3))
    return name, lat, lon, note


def _oldmap_meta(desc):
    """'Title (date) — attribution | url' → (title, date, attribution, url)."""
    head, _, rest = desc.partition(DASH)
    head, rest = head.strip(), rest.strip()
    title, date = head, ""
    mm = re.match(r"^(.*)\(([^()]*)\)\s*$", head)  # the LAST parenthetical is the date
    if mm:
        title, date = mm.group(1).strip(), mm.group(2).strip()
    attribution, _, url = rest.rpartition(" | ")
    return title, date, attribution.strip(), url.strip()


def _hull(desc):
    m = re.search(r"polygon lon,lat:\s*(.+)$", desc)
    if not m:
        return []
    pts = []
    for pair in m.group(1).split(";"):
        pair = pair.strip()
        if not pair:
            continue
        try:
            lon, lat = (float(x) for x in pair.split(","))
            pts.append([lon, lat])
        except ValueError:
            pass
    return pts


def _pin(desc):
    """'lat, lon (WGS84) — …' → (lat, lon)."""
    mm = re.match(r"^\s*([-\d.]+)\s*,\s*([-\d.]+)", desc)
    return (float(mm.group(1)), float(mm.group(2))) if mm else (None, None)


def project(text):
    defs, aliases, links = _parse_ak(text)
    civ_atoms = [s for (s, d, r) in links if d == "ancient:civilization" and r == "sys:is_a"]
    region_atoms = [s for (s, d, r) in links if d == "ancient:region" and r == "sys:is_a"]

    # index links by (rel) for the source atom
    by_src = {}
    for s, d, r in links:
        by_src.setdefault((s, r), []).append(d)

    civs = {}
    for atom in civ_atoms:
        name, nat, era, note = _civ_meta(defs.get(atom, aliases.get(atom, atom)))
        region = next((d.split(":")[-1] for d in by_src.get((atom, "ancient:in_region"), [])), "")
        countries = [{"iso": d.split(":")[-1], "source_atom": d}
                     for d in by_src.get((atom, "ancient:spans_country"), [])]
        sites = []
        for d in by_src.get((atom, "ancient:site"), []):
            sn, la, lo, nt = _site_meta(defs.get(d, ""))
            sites.append({"name": sn, "lat": la, "lon": lo, "note": nt, "source_atom": d})
        sources = []
        for d in by_src.get((atom, "ancient:source"), []):
            lbl, _, url = defs.get(d, "").partition(DASH)
            sources.append({"label": lbl.strip(), "url": url.strip(), "source_atom": d})
        oldmaps = []
        for d in by_src.get((atom, "ancient:has_oldmap"), []):
            t, dt, attr, url = _oldmap_meta(defs.get(d, ""))
            oldmaps.append({"title": t, "date": dt, "attribution": attr, "url": url, "source_atom": d})
        hull, extent_atom = [], ""
        for d in by_src.get((atom, "ancient:has_extent"), []):
            hull, extent_atom = _hull(defs.get(d, "")), d
        civs[atom] = {
            "region": region, "name": name, "nat": nat, "era": era, "note": note,
            "source_atom": atom, "countries": countries, "hull": hull, "extent_atom": extent_atom,
            "sites": sites, "sources": sources, "oldmaps": oldmaps,
        }

    # regions (nav chrome — also fully ontology-backed): name/sub/lead + pin, in declaration order
    regions = {}
    for i, ratom in enumerate(region_atoms, 1):
        rid = ratom.split(":")[-1]
        rdesc = defs.get(ratom, "")
        rname, _, rest = rdesc.partition(DASH)
        sub, _, lead = rest.partition(". ")
        lat = lon = None
        pin_atom = ""
        for d in by_src.get((ratom, "geo:has_coordinate"), []):
            lat, lon = _pin(defs.get(d, ""))
            pin_atom = d
        regions[rid] = {
            "no": i, "name": rname.strip(), "sub": sub.strip(), "lead": lead.strip(),
            "lat": lat, "lon": lon, "pin_atom": pin_atom, "source_atom": ratom,
            "civs": [a for a in civ_atoms if civs[a]["region"] == rid],
        }

    return {"civs": civs, "regions": regions}


def main():
    with open(AK, "r", encoding="utf-8") as f:
        out = project(f.read())
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    civs = out["civs"]
    print("projected %d civilizations, %d regions → %s" % (len(civs), len(out["regions"]),
          os.path.relpath(OUT_JSON, ROOT)))
    print("  sites %d, sources %d, country links %d, old-maps %d, extents %d" % (
        sum(len(c["sites"]) for c in civs.values()),
        sum(len(c["sources"]) for c in civs.values()),
        sum(len(c["countries"]) for c in civs.values()),
        sum(len(c["oldmaps"]) for c in civs.values()),
        sum(1 for c in civs.values() if c["hull"])))


if __name__ == "__main__":
    main()
