# Cookbook — Ancient World Map Demo

## Concept

A Leaflet-based map viewer that slides between a modern basemap and an ancient
world map (Mediterranean / Near East), with Akasha atoms surfaced as place pins.

The key philosophical point: **the map image changes, the semantic network does not.**
Coordinates are just one attribute of a place atom — they are not the identity.
The slider transitions the visual projection; Akasha's graph stays invariant beneath it.

Overlay alignment uses affine transformation (ground control points) to warp the
historical map image onto the modern coordinate system, so pins stay at the same
screen position as the slider moves.

---

## Data Sources

### Place atoms — Pleiades
- Ancient world gazetteer covering Greece, Rome, Near East, Egypt, Persia
- 35,000+ places with coordinates, time period ranges, and short descriptions
- Connections between places (roads, political relationships)
- License: CC BY
- Bulk JSON download available
- Each Pleiades entry maps directly to an Akasha atom

### Ancient map tiles — AWMC (Ancient World Mapping Center, UNC Chapel Hill)
- XYZ / WMS tile service for the ancient Mediterranean world
- Includes Roman roads, ancient coastlines, period-accurate place names
- Intended to be used as a Leaflet tile layer alongside Pleiades data

### Modern basemap
- OpenStreetMap or equivalent — standard Leaflet default tile layer

---

## Affine Transform / Georeferencing

Historical map images are aligned to the modern coordinate system using ground
control points (GCPs): a small set of locations identifiable on both maps whose
modern coordinates are known.

With 3–6 GCPs an affine transform is sufficient for most ancient maps.
The warp is applied client-side (CSS transform or canvas) so no server-side
tile pre-processing is required for the demo.

Pleiades coordinates serve double duty: atom positions AND GCP candidates.

---

## Akasha Atom Structure

```
place:rome
  al: Rome, Roma, Ῥώμη
  coord: [41.8919, 12.5113]
  period_start: -753          ← founding (traditional)
  period_end: 476             ← fall of Western Empire
  ln → place:carthage   thesaurus:rival_of
  ln → place:ostia      thesaurus:gateway_of
  ln → era:roman        thesaurus:belongs_to
  ln → myth:romulus     thesaurus:founded_by

place:carthage
  al: Carthage, Kart-Hadasht
  coord: [36.8528, 10.3233]
  period_start: -814
  period_end: -146            ← destroyed by Rome
  ln → place:rome       thesaurus:rival_of
  ln → era:punic        thesaurus:belongs_to
  ln → myth:dido        thesaurus:origin_of
```

The `sky_dreamers` curation already seeds some of the mythological atoms
(Icarus, Daedalus, da Vinci, Lilienthal) that share the Mediterranean context.

---

## Demo Interaction

1. Page loads showing the ancient AWMC tile layer with Pleiades pins
2. Slider at the top: left = ancient, right = modern
3. Dragging the slider cross-fades the tile layers; pins stay fixed
4. Clicking a pin opens an Akasha panel: atom name, aliases, links to related atoms
5. Optional: time filter — enter a year and only atoms whose period spans that year appear

---

## Scope for Initial Cookbook Entry

Region: Mediterranean + Near East (Pleiades coverage)
Period: Classical antiquity (roughly -500 to 500 CE)
Initial atom count: start with a curated subset (~50 key places)
Map tile source: AWMC for ancient, OSM for modern
Slider: simple CSS opacity cross-fade, affine transform not needed for first pass

---

## Files to Create

| Path | Purpose |
|---|---|
| `archives/cookbook/index.html` | Entry page for all cookbook demos |
| `archives/cookbook/map/index.html` | The map demo itself |
| `curations/ancient_mediterranean.csl` | CSL curation loading place atoms |
| `ontology/base/place.ak` | Core place atoms (Rome, Carthage, Athens, …) |

---

## Related

- `curations/sky_dreamers.csl` — Icarus/Daedalus atoms share the Mediterranean context
- `ontology/base/sky.ak` — sky:myth:* atoms already defined
- Pleiades entry for Crete: `place:crete` → connects to existing `sky:myth:daedalus`
