"""
volcanoes_import.py — Smithsonian GVP Holocene volcanoes → app/ontology/geology/volcanoes.ak

Converts the Global Volcanism Program (GVP) Holocene volcano list to a single
Akasha .ak ontology file at app/ontology/geology/volcanoes.ak.

Atom IDs:    geo:volcano:{normalized_name}          e.g. geo:volcano:vesuvius
GVP alias:   geo:volcano:gvp:{VolcanoNumber}        (e.g. geo:volcano:gvp:211060)
Links:
    sys:part_of → geo:volcano                        (parent namespace anchor)
    sys:part_of → geo:country:{iso3}                 (ISO3 country code)
    sys:part_of → geo:volcano:type:{normalized_type} (volcano morphology)

Attribution:
    Smithsonian Institution Global Volcanism Program
    https://volcano.si.edu/
    CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/

Usage:
    # Auto-download from GVP WFS and convert:
    python app/scripts/volcanoes_import.py

    # Use pre-downloaded CSV:
    python app/scripts/volcanoes_import.py --csv /path/to/gvp_holocene.csv

    # Dry run (stats only, no files written):
    python app/scripts/volcanoes_import.py --dry-run

    # Custom output directory:
    python app/scripts/volcanoes_import.py --out /path/to/output/

Options:
    --csv FILE    Pre-downloaded GVP CSV
    --out DIR     Output directory (default: app/ontology/geology/)
    --dry-run     Print stats only, write no files

Source URLs tried in order:
    https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=GVP-VOTW:E3WebApp_Volcanoes_Holocene&outputFormat=csv
    https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes&outputFormat=csv

If both URLs fail, download from https://volcano.si.edu/search_volcano.cfm
(search for Holocene, export to Excel/CSV) and use --csv.
"""

import argparse
import csv
import os
import re
import sys
import urllib.request

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DEFAULT_OUT  = os.path.join(PROJECT_ROOT, "app", "ontology", "geology")
CACHE_DIR    = os.path.join(PROJECT_ROOT, "out", "volcanoes_cache")
CACHE_FILE   = os.path.join(CACHE_DIR, "gvp_holocene.csv")

PRIMARY_URL = (
    "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeName=GVP-VOTW:E3WebApp_Volcanoes_Holocene&outputFormat=csv"
)
ALT_URL = (
    "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeName=GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes&outputFormat=csv"
)

# ── Volcano type namespace anchors ────────────────────────────────────────────

VOLCANO_TYPES = {
    "stratovolcano": "Stratovolcano (composite volcano) — steep conical form built from alternating layers of lava and pyroclastic material; most common type of large volcano",
    "shield":        "Shield volcano — broad, gently sloping dome built from fluid basaltic lava flows; e.g. Mauna Loa, Kilauea",
    "caldera":       "Caldera — large volcanic depression formed by collapse of a magma chamber after eruption; may contain resurgent domes or lakes",
    "cinder_cone":   "Cinder cone / pyroclastic cone — steep conical hill of loose volcanic fragments; typically monogenetic, often short-lived",
    "submarine":     "Submarine volcano — erupts on the ocean floor; forms seamounts and some islands; may be undiscovered until acoustic or seafloor surveys",
    "lava_dome":     "Lava dome — mound of viscous lava extruded slowly over a vent; often forms inside calderas or on flanks of stratovolcanoes",
    "complex":       "Volcanic complex — cluster of related vents, craters, or domes that share a common magmatic system; may include multiple types",
    "maar":          "Maar / tuff cone — low-relief volcanic crater formed by phreatomagmatic explosions; often water-filled; e.g. Eifel maars",
    "fissure_vent":  "Fissure vent — elongated fracture in the crust from which lava erupts; produces lava fields and curtains of fire; e.g. Laki (Iceland)",
    "other":         "Volcanic feature not classified under the primary GVP morphological types",
}

# ── Primary volcano type normalisation ───────────────────────────────────────

def norm_type(raw: str) -> str:
    """Normalise GVP PrimaryVolcanoType string → short key."""
    s = raw.strip().lower()
    # Remove parenthetical qualifiers like "(s)"
    s = re.sub(r'\(.*?\)', '', s).strip()
    if not s:
        return 'other'
    if 'strato' in s:
        return 'stratovolcano'
    if 'shield' in s:
        return 'shield'
    if 'caldera' in s:
        return 'caldera'
    if 'cinder' in s or 'pyroclastic cone' in s:
        return 'cinder_cone'
    if 'submarine' in s:
        return 'submarine'
    if 'lava dome' in s:
        return 'lava_dome'
    if 'complex' in s:
        return 'complex'
    if 'maar' in s or 'tuff cone' in s or 'tuff ring' in s:
        return 'maar'
    if 'fissure' in s:
        return 'fissure_vent'
    return 'other'

# ── Country name → ISO3 mapping ───────────────────────────────────────────────
# Covers the countries most commonly represented in the GVP Holocene list.

COUNTRY_TO_ISO3: dict[str, str] = {
    "Afghanistan":               "afg",
    "Albania":                   "alb",
    "Algeria":                   "dza",
    "Antarctica":                "ata",
    "Argentina":                 "arg",
    "Armenia":                   "arm",
    "Australia":                 "aus",
    "Azerbaijan":                "aze",
    "Bolivia":                   "bol",
    "Cameroon":                  "cmr",
    "Canada":                    "can",
    "Cape Verde":                "cpv",
    "Cabo Verde":                "cpv",
    "Chad":                      "tcd",
    "Chile":                     "chl",
    "China":                     "chn",
    "Colombia":                  "col",
    "Comoros":                   "com",
    "Congo, DRC":                "cod",
    "Congo":                     "cog",
    "Democratic Republic of Congo": "cod",
    "Costa Rica":                "cri",
    "Croatia":                   "hrv",
    "Cuba":                      "cub",
    "Djibouti":                  "dji",
    "Ecuador":                   "ecu",
    "El Salvador":               "slv",
    "Eritrea":                   "eri",
    "Ethiopia":                  "eth",
    "Fiji":                      "fji",
    "France":                    "fra",
    "Germany":                   "deu",
    "Greece":                    "grc",
    "Greenland":                 "grl",
    "Guatemala":                 "gtm",
    "Guinea":                    "gin",
    "Honduras":                  "hnd",
    "Iceland":                   "isl",
    "India":                     "ind",
    "Indonesia":                 "idn",
    "Iran":                      "irn",
    "Italy":                     "ita",
    "Japan":                     "jpn",
    "Jordan":                    "jor",
    "Kazakhstan":                "kaz",
    "Kenya":                     "ken",
    "Kyrgyzstan":                "kgz",
    "Laos":                      "lao",
    "Libya":                     "lby",
    "Madagascar":                "mdg",
    "Mali":                      "mli",
    "Martinique":                "mtq",
    "Mexico":                    "mex",
    "Mongolia":                  "mng",
    "Morocco":                   "mar",
    "Mozambique":                "moz",
    "Myanmar":                   "mmr",
    "New Zealand":               "nzl",
    "Nicaragua":                 "nic",
    "Niger":                     "ner",
    "Nigeria":                   "nga",
    "North Korea":               "prk",
    "Norway":                    "nor",
    "Pakistan":                  "pak",
    "Panama":                    "pan",
    "Papua New Guinea":          "png",
    "Peru":                      "per",
    "Philippines":               "phl",
    "Portugal":                  "prt",
    "Russia":                    "rus",
    "Rwanda":                    "rwa",
    "Saint Kitts and Nevis":     "kna",
    "Saint Lucia":               "lca",
    "Saint Vincent and the Grenadines": "vct",
    "Saudi Arabia":              "sau",
    "Solomon Islands":           "slb",
    "South Korea":               "kor",
    "Spain":                     "esp",
    "Sudan":                     "sdn",
    "Svalbard":                  "sjm",
    "Syria":                     "syr",
    "Tanzania":                  "tza",
    "Tajikistan":                "tjk",
    "Tonga":                     "ton",
    "Trinidad and Tobago":       "tto",
    "Turkey":                    "tur",
    "Turkmenistan":              "tkm",
    "Uganda":                    "uga",
    "Ukraine":                   "ukr",
    "United Kingdom":            "gbr",
    "United States":             "usa",
    "USA":                       "usa",
    "Uzbekistan":                "uzb",
    "Vanuatu":                   "vut",
    "Venezuela":                 "ven",
    "Vietnam":                   "vnm",
    "Yemen":                     "yem",
    "Zambia":                    "zmb",
    "Zimbabwe":                  "zwe",
    # Ocean / sea regions (no country code; use a synthetic anchor)
    "Atlantic Ocean":            "oce",
    "Pacific Ocean":             "oce",
    "Indian Ocean":              "oce",
    "Arctic Ocean":              "oce",
    "Mediterranean Sea":         "oce",
    "Red Sea":                   "oce",
    "Indian Ocean-S":            "oce",
}


def country_to_iso3(country: str) -> str:
    """Map country name → ISO3 lower code, fallback to normalized name."""
    stripped = country.strip()
    if stripped in COUNTRY_TO_ISO3:
        return COUNTRY_TO_ISO3[stripped]
    # Try partial match
    for k, v in COUNTRY_TO_ISO3.items():
        if k.lower() in stripped.lower() or stripped.lower() in k.lower():
            return v
    # Fallback: generate a safe key from the country name
    return re.sub(r'[^a-z0-9]', '', stripped.lower())[:6] or 'unk'


# ── Column name aliases ───────────────────────────────────────────────────────

COL_ALIASES = {
    'name':     ['VolcanoName', 'Volcano_Name', 'Name', 'name', 'volcano_name'],
    'country':  ['Country', 'country'],
    'type':     ['PrimaryVolcanoType', 'Primary_Volcano_Type', 'VolcanoType', 'type'],
    'evidence': ['ActivityEvidence', 'Activity_Evidence', 'evidence'],
    'eruption': ['LastKnownEruption', 'Last_Known_Eruption', 'eruption', 'last_eruption'],
    'region':   ['Region', 'region'],
    'subregion':['Subregion', 'subregion', 'Sub_Region'],
    'lat':      ['Latitude', 'latitude', 'lat'],
    'lon':      ['Longitude', 'longitude', 'lon'],
    'elev':     ['Elevation', 'elevation', 'Elev', 'elev'],
    'number':   ['VolcanoNumber', 'Volcano_Number', 'Number', 'number', 'GVP_Number'],
}


def resolve_cols(header: list[str]) -> dict[str, int | None]:
    result: dict[str, int | None] = {}
    lower_header = [h.strip().lower() for h in header]
    for field, candidates in COL_ALIASES.items():
        idx = None
        for cand in candidates:
            try:
                idx = lower_header.index(cand.lower())
                break
            except ValueError:
                pass
        result[field] = idx
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[\s\-,.'()\[\]/]+", '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return s[:60]


def escape_ak(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"')


def fmt_coord(lat: float, lon: float) -> str:
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    return f"{abs(lat):.4f}°{ns} {abs(lon):.4f}°{ew}"


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_volcanoes(path: str) -> list[dict]:
    """Parse GVP CSV → list of volcano dicts, sorted by Region then Latitude."""
    volcanoes: list[dict] = []

    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            print("ERROR: CSV file appears to be empty.", file=sys.stderr)
            sys.exit(1)

        cols = resolve_cols(raw_header)

        if cols['name'] is None:
            print("ERROR: Cannot find volcano name column in CSV header:", file=sys.stderr)
            print(f"  {raw_header}", file=sys.stderr)
            print("  Known names: VolcanoName, Volcano_Name, Name", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            if not row:
                continue
            def _get(field: str) -> str:
                idx = cols.get(field)
                if idx is None or idx >= len(row):
                    return ''
                return row[idx].strip()

            name = _get('name')
            if not name:
                continue

            try:
                lat = float(_get('lat')) if _get('lat') else 0.0
            except ValueError:
                lat = 0.0
            try:
                lon = float(_get('lon')) if _get('lon') else 0.0
            except ValueError:
                lon = 0.0
            try:
                elev = int(float(_get('elev'))) if _get('elev') else None
            except ValueError:
                elev = None

            volcanoes.append({
                'name':     name,
                'country':  _get('country'),
                'type':     _get('type'),
                'evidence': _get('evidence'),
                'eruption': _get('eruption'),
                'region':   _get('region'),
                'subregion':_get('subregion'),
                'lat':      lat,
                'lon':      lon,
                'elev':     elev,
                'number':   _get('number'),
            })

    # Sort: Region alphabetically, then Latitude descending (north first)
    volcanoes.sort(key=lambda v: (v['region'].lower(), -v['lat']))
    print(f"  Parsed {len(volcanoes)} volcanoes")
    return volcanoes


# ── .ak emission ──────────────────────────────────────────────────────────────

def build_desc(v: dict) -> str:
    parts = []
    loc = v['country'] if v['country'] else 'location unknown'
    vtype = v['type'] if v['type'] else 'volcanic feature'
    parts.append(f"{v['name']}, {loc} — {vtype}")
    if v['elev'] is not None:
        parts.append(f"elevation {v['elev']} m")
    if v['eruption']:
        parts.append(f"last eruption: {v['eruption']}")
    if v['lat'] or v['lon']:
        parts.append(fmt_coord(v['lat'], v['lon']))
    if v['region']:
        parts.append(f"region: {v['region']}")
    return '; '.join(parts)


def emit_volcano(fh, v: dict) -> None:
    norm    = normalize(v['name'])
    atom    = f"geo:volcano:{norm}"
    iso3    = country_to_iso3(v['country']) if v['country'] else 'unk'
    vtype   = norm_type(v['type'])

    desc = build_desc(v)
    fh.write(f'def "{atom}" "{escape_ak(desc)}"\n')
    if v['number']:
        alias = f"geo:volcano:gvp:{v['number']}"
        fh.write(f'al {atom} {alias}\n')
    fh.write(f'ln {atom} geo:volcano sys:part_of\n')
    fh.write(f'ln {atom} geo:country:{iso3} sys:part_of\n')
    fh.write(f'ln {atom} geo:volcano:type:{vtype} sys:part_of\n')
    fh.write('\n')


def write_anchors(fh) -> None:
    fh.write('def "geo:volcano" "Volcano — geological vent or fissure in the Earth\'s crust through which magma, ash, and gases are expelled; includes ~1,400 Holocene-active volcanoes in the Smithsonian GVP database"\n\n')

    fh.write('# Volcano type anchors\n')
    for type_key, desc in VOLCANO_TYPES.items():
        atom = f"geo:volcano:type:{type_key}"
        fh.write(f'def "{atom}" "{escape_ak(desc)}"\n')
        fh.write(f'ln {atom} geo:volcano sys:part_of\n')
    fh.write('\n')


FILE_HEADER = """\
# volcanoes.ak
# Smithsonian Institution Global Volcanism Program (GVP)
# https://volcano.si.edu/
# CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/
# Generated by volcanoes_import
# Holocene volcanoes: {count}
# Sorted by: Region, then Latitude (north first)
#
"""


def generate(volcanoes: list[dict], out_dir: str, dry_run: bool):
    total = len(volcanoes)

    # Type distribution
    type_counts: dict[str, int] = {}
    region_counts: dict[str, int] = {}
    for v in volcanoes:
        t = norm_type(v['type'])
        type_counts[t]                 = type_counts.get(t, 0) + 1
        region_counts[v['region']]     = region_counts.get(v['region'], 0) + 1

    print(f"\n  Volcanoes: {total}")
    print(f"  Output:    volcanoes.ak (single file)")
    print(f"\n  Volcano types:")
    for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {k:18s} {v:5d}")
    print(f"\n  Regions:")
    for k, v in sorted(region_counts.items(), key=lambda x: -x[1]):
        print(f"    {k:35s} {v:5d}")

    if dry_run:
        return

    os.makedirs(out_dir, exist_ok=True)
    fpath = os.path.join(out_dir, "volcanoes.ak")

    with open(fpath, 'w', encoding='utf-8') as fh:
        fh.write(FILE_HEADER.format(count=total))
        write_anchors(fh)
        current_region = None
        for v in volcanoes:
            if v['region'] != current_region:
                current_region = v['region']
                fh.write(f'# Region: {current_region}\n')
            emit_volcano(fh, v)

    print(f"\n  volcanoes.ak  {total} volcanoes → {fpath}")
    print("\nNext: git add app/ontology/geology/volcanoes.ak && git commit")


# ── Download helpers ──────────────────────────────────────────────────────────

def _download(url: str, dest: str, label: str) -> bool:
    print(f"Downloading {label} …")
    print(f"  URL: {url[:80]}{'…' if len(url) > 80 else ''}")

    def _prog(b, bs, ts):
        if ts > 0:
            pct = min(100, b * bs * 100 // ts)
            print(f"\r  {pct}%", end='', flush=True)
        else:
            kb = b * bs // 1024
            print(f"\r  {kb} KB", end='', flush=True)

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'AkashaOntologyBuilder/1.0 (contact: ontology@akasha.local)'
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(dest, 'wb') as f:
            f.write(data)
        print(f"\r  {len(data) // 1024} KB downloaded")
        return True
    except Exception as e:
        print(f"\n  Failed: {e}")
        return False


def ensure_csv(arg: str | None) -> str:
    if arg:
        if not os.path.exists(arg):
            print(f"ERROR: --csv file not found: {arg}", file=sys.stderr)
            sys.exit(1)
        return arg

    os.makedirs(CACHE_DIR, exist_ok=True)

    if os.path.exists(CACHE_FILE):
        print(f"Using cached: {CACHE_FILE}")
        return CACHE_FILE

    if _download(PRIMARY_URL, CACHE_FILE, "GVP Holocene volcanoes (primary WFS)"):
        # Verify it looks like CSV (not an XML error response)
        with open(CACHE_FILE, 'r', encoding='utf-8-sig', errors='replace') as f:
            head = f.read(200)
        if head.strip().startswith('<'):
            print("  Response was XML (possibly an error); trying alternative URL …")
            os.remove(CACHE_FILE)
        else:
            return CACHE_FILE

    alt_file = CACHE_FILE.replace('.csv', '_alt.csv')
    if _download(ALT_URL, alt_file, "GVP Holocene volcanoes (alternative WFS)"):
        with open(alt_file, 'r', encoding='utf-8-sig', errors='replace') as f:
            head = f.read(200)
        if not head.strip().startswith('<'):
            os.rename(alt_file, CACHE_FILE)
            return CACHE_FILE

    print("\n" + "="*60, file=sys.stderr)
    print("AUTO-DOWNLOAD FAILED", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print("Manual download steps:", file=sys.stderr)
    print("  1. Visit https://volcano.si.edu/search_volcano.cfm", file=sys.stderr)
    print("     Select: Holocene activity, all types, all regions", file=sys.stderr)
    print("     Export to CSV / Excel", file=sys.stderr)
    print("  2. Or try the WFS URLs directly in a browser:", file=sys.stderr)
    print(f"     {PRIMARY_URL}", file=sys.stderr)
    print("  3. Re-run with: --csv /path/to/downloaded.csv", file=sys.stderr)
    print("="*60, file=sys.stderr)
    sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('--csv', metavar='FILE',
                    help='Pre-downloaded GVP Holocene CSV file')
    ap.add_argument('--out', default=DEFAULT_OUT,
                    help=f'Output directory (default: {DEFAULT_OUT})')
    ap.add_argument('--dry-run', action='store_true',
                    help='Print stats only, write no files')
    args = ap.parse_args()

    print('[volcanoes_import] Locating source file …')
    csv_path = ensure_csv(args.csv)

    print(f'[volcanoes_import] Parsing {csv_path} …')
    volcanoes = parse_volcanoes(csv_path)

    if not volcanoes:
        print("ERROR: No volcanoes found. Check CSV format.", file=sys.stderr)
        print("  Expected column: VolcanoName (or Volcano_Name, Name)", file=sys.stderr)
        sys.exit(1)

    generate(volcanoes, args.out, args.dry_run)


if __name__ == '__main__':
    main()
