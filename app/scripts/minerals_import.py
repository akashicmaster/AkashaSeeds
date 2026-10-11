"""
minerals_import.py — RRUFF/IMA mineral database → app/ontology/geology/minerals_NN.ak

Converts the RRUFF Project / IMA mineral list to Akasha .ak ontology files
for app/ontology/geology/.

Filters applied:
    - IMA Status = 'Approved' only (~5,800 species as of 2024)

Atom IDs:    mineral:{normalized_name}         e.g. mineral:quartz
RRUFF alias: mineral:rruff:{normalized_name}   (canonical RRUFF reference)
Links:
    sys:part_of → mineral                       (parent namespace anchor)
    sys:part_of → mineral:crystal:{system}      (crystal system)
    sys:part_of → mineral:class:{class}         (chemical class by formula)

Attribution:
    RRUFF Project / IMA mineral database — https://rruff.info/
    IMA (International Mineralogical Association) — https://ima-mineralogy.org/
    Data released under CC BY — https://creativecommons.org/licenses/by/4.0/

Manual download instructions (if auto-download fails):
    The RRUFF master CSV files may require acceptance of a terms-of-use page
    or may move URLs. If the script cannot download automatically:

    Option A — RRUFF master list (preferred):
        1. Visit https://rruff.info/ima/ima_minerals.csv
           or   https://rruff.info/rruff_master_2021_01.csv
        2. Save the file locally
        3. Re-run: python app/scripts/minerals_import.py --minerals-csv /path/to/file.csv

    Option B — IMA master list spreadsheet:
        1. Visit https://ima-mineralogy.org/Minlist/
        2. Download the "List of Minerals" Excel or CSV
        3. Convert to CSV if needed; ensure columns include Name, Status, Formula, Crystal System
        4. Re-run with --minerals-csv

Usage:
    # Auto-download and convert:
    python app/scripts/minerals_import.py

    # Use pre-downloaded file:
    python app/scripts/minerals_import.py --minerals-csv /path/to/ima_minerals.csv

    # Dry run (stats only, no files written):
    python app/scripts/minerals_import.py --minerals-csv /path/to/ima_minerals.csv --dry-run

    # Custom output directory:
    python app/scripts/minerals_import.py --out /path/to/output/

Options:
    --minerals-csv FILE    Pre-downloaded RRUFF/IMA CSV
    --out DIR              Output directory (default: app/ontology/geology/)
    --chunk-size N         Minerals per .ak file (default: 2000)
    --dry-run              Print stats only, write no files

Source URLs tried in order:
    https://rruff.info/ima/ima_minerals.csv
    https://rruff.info/rruff_master_2021_01.csv
"""

import argparse
import csv
import os
import re
import sys
import urllib.request

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_OUT  = os.path.join(PROJECT_ROOT, "app", "ontology", "geology")
CACHE_DIR    = os.path.join(PROJECT_ROOT, "out", "minerals_cache")

PRIMARY_URL = "https://rruff.info/ima/ima_minerals.csv"
ALT_URL     = "https://rruff.info/rruff_master_2021_01.csv"

# ── Crystal system namespace anchors ──────────────────────────────────────────

CRYSTAL_SYSTEMS = {
    "cubic":        "Isometric (cubic) crystal system — three equal axes at 90°; symmetry forms include cube, octahedron, tetrahedron, dodecahedron",
    "tetragonal":   "Tetragonal crystal system — two equal horizontal axes, one distinct vertical axis, all at 90°",
    "orthorhombic": "Orthorhombic crystal system — three unequal axes all at 90°",
    "hexagonal":    "Hexagonal crystal system — three equal coplanar axes at 120° plus one vertical axis",
    "trigonal":     "Trigonal (rhombohedral) crystal system — three-fold rotational symmetry; sometimes classed within hexagonal",
    "monoclinic":   "Monoclinic crystal system — three unequal axes, one oblique angle; most common crystal system among minerals",
    "triclinic":    "Triclinic crystal system — three unequal axes with no right angles; lowest symmetry system",
    "amorphous":    "Amorphous (non-crystalline) — no long-range atomic order; includes mineraloids such as opal and obsidian",
}

# ── Chemical class namespace anchors ─────────────────────────────────────────

MINERAL_CLASSES = {
    "native_element":  "Native elements — minerals composed of a single element in pure or alloyed form; e.g. gold, silver, copper, diamond, sulfur",
    "sulfide":         "Sulfide minerals — compounds of sulfur with metals; e.g. pyrite (FeS₂), galena (PbS), sphalerite (ZnS), chalcopyrite (CuFeS₂)",
    "oxide":           "Oxide minerals — compounds of oxygen with metals; e.g. hematite (Fe₂O₃), magnetite (Fe₃O₄), corundum (Al₂O₃), rutile (TiO₂)",
    "hydroxide":       "Hydroxide minerals — oxides or hydroxides with OH groups; e.g. gibbsite Al(OH)₃, goethite FeO(OH)",
    "silicate":        "Silicate minerals — built from SiO₄ tetrahedra; most abundant mineral class in Earth's crust; includes feldspars, pyroxenes, amphiboles, micas, quartz",
    "carbonate":       "Carbonate minerals — contain CO₃²⁻ group; e.g. calcite (CaCO₃), dolomite (CaMg(CO₃)₂), malachite",
    "sulfate":         "Sulfate minerals — contain SO₄²⁻ group; e.g. gypsum (CaSO₄·2H₂O), barite (BaSO₄), anhydrite",
    "phosphate":       "Phosphate minerals — contain PO₄³⁻ group; e.g. apatite Ca₅(PO₄)₃(F,Cl,OH), monazite, turquoise",
    "halide":          "Halide minerals — compounds with halogen anions (F, Cl, Br, I); e.g. halite (NaCl), fluorite (CaF₂), sylvite (KCl)",
    "borate":          "Borate minerals — contain BO₃ or BO₄ groups; e.g. borax, ulexite, kernite",
    "nitrate":         "Nitrate minerals — contain NO₃⁻ group; e.g. nitratine (NaNO₃), niter (KNO₃); rare, found in arid climates",
    "tungstate":       "Tungstate and molybdate minerals — contain WO₄²⁻ or MoO₄²⁻; e.g. scheelite (CaWO₄), wolframite",
    "arsenate":        "Arsenate minerals — contain AsO₄³⁻ group; e.g. erythrite, olivenite, scorodite",
    "vanadate":        "Vanadate minerals — contain VO₄³⁻ group; e.g. vanadinite, carnotite",
    "chromate":        "Chromate minerals — contain CrO₄²⁻ group; e.g. crocoite (PbCrO₄), phoenicochroite",
    "element_alloy":   "Intermetallic alloys and metallic minerals not classed as pure native elements",
    "organic":         "Organic minerals — naturally occurring carbon compounds of biological or abiogenic origin; e.g. whewellite, amber-related minerals",
    "other":           "Minerals not fitting the main chemical classification groups; includes complex or mixed-anion species",
}

FILE_HEADER = """\
# {filename}
# RRUFF Project / IMA mineral database — https://rruff.info/
# IMA (International Mineralogical Association) — https://ima-mineralogy.org/
# CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/
# Generated by app/scripts/minerals_import.py
# IMA-approved minerals: {mineral_range}
#
"""

ANCHOR_HEADER = """\
# minerals_01.ak
# RRUFF Project / IMA mineral database — https://rruff.info/
# IMA (International Mineralogical Association) — https://ima-mineralogy.org/
# CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/
# Generated by app/scripts/minerals_import.py
# File 01 contains namespace anchors, then the first batch of minerals.
#
"""

# ── Column name aliases ───────────────────────────────────────────────────────
# RRUFF CSVs have varied column naming across versions; we try multiple names.

COL_ALIASES = {
    'name':    ['Mineral Name', 'Name', 'mineral_name', 'name'],
    'status':  ['IMA Status', 'Status', 'ima_status', 'status'],
    'formula': ['Chemical Formula', 'Formula', 'chemical_formula', 'formula', 'IMA Chemistry'],
    'crystal': ['Crystal System', 'crystal_system', 'Crystal system'],
    'class':   ['Crystal Class', 'crystal_class'],
    'hardness':['Hardness (Mohs)', 'Hardness', 'hardness', 'Mohs Hardness'],
    'color':   ['Color', 'Colour', 'color', 'colour'],
    'lustre':  ['Lustre', 'Luster', 'lustre', 'luster'],
}


def resolve_cols(header: list[str]) -> dict[str, int | None]:
    """Map logical field names → CSV column indices (None if absent)."""
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


def normalize(name: str) -> str:
    """Convert mineral name to atom name component."""
    s = name.lower()
    s = re.sub(r"[\s\-,.'()\[\]/]+", '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return s[:60]


def escape_ak(s: str) -> str:
    """Escape double-quotes and backslashes for .ak def strings."""
    return s.replace('\\', '\\\\').replace('"', '\\"')


# ── Chemical class detection ──────────────────────────────────────────────────

# Patterns checked in priority order.
# Each entry: (class_key, compiled_pattern_on_formula)
def _has_S_not_SO4_not_Si(formula: str) -> bool:
    """
    Return True if formula contains sulfur (S), selenium (Se), or tellurium (Te)
    acting as an anion (sulfide/selenide/telluride), i.e. not part of SO4 (sulfate),
    not Si (silicon), not Sn/Sb/Sr/Sc/Sm/Sg.
    Strategy: strip oxyanion and two-letter element groups, then check for remaining S/Se/Te.
    """
    f = formula
    # Remove SO4, SO3, SO2, SO — sulfate/sulfite groups
    f = re.sub(r'SO\d*', '', f)
    # Remove two-letter S-elements that are NOT sulfur-as-anion
    f = re.sub(r'S(?:i|n|b|r|c|m|g)\d*', '', f)
    # Se and Te: these ARE sulfide-class (selenide/telluride) — keep them for the check
    # Now check if a bare S, Se, or Te remains
    return bool(re.search(r'(?:Se|Te|S)\d*', f))


def _build_class_patterns():
    # Checked in priority order. Each entry: (class_key, compiled_regex | None).
    # When regex is None the classify_formula function uses a custom check instead.
    rules = [
        # Native elements: single element symbol (possibly with subscript), no other elements
        ("native_element",  re.compile(r'^[A-Z][a-z]?\d*$')),
        # Silicates: contain Si and O — high priority (SiS2 is a sulfide; Si+O wins silicate)
        ("silicate",        re.compile(r'Si[^·]*O')),
        # Carbonates: CO3
        ("carbonate",       re.compile(r'CO3')),
        # Sulfates: SO4 — must be before sulfide (SO4 also has an S)
        ("sulfate",         re.compile(r'SO4')),
        # Phosphates: PO4
        ("phosphate",       re.compile(r'PO4')),
        # Arsenates: AsO4
        ("arsenate",        re.compile(r'AsO4')),
        # Vanadates: VO4
        ("vanadate",        re.compile(r'VO4')),
        # Chromates: CrO4
        ("chromate",        re.compile(r'CrO4')),
        # Tungstates / molybdates
        ("tungstate",       re.compile(r'WO4|MoO4')),
        # Nitrates: NO3
        ("nitrate",         re.compile(r'NO3')),
        # Borates: BO3, BO4, B2O3 patterns
        ("borate",          re.compile(r'B\d*O\d|BO\d*')),
        # Sulfides / selenides / tellurides — None means use _has_sulfide_S helper
        ("sulfide",         None),
        # Hydroxides: OH group
        ("hydroxide",       re.compile(r'OH')),
        # Oxides: O present (not matched as anything above)
        ("oxide",           re.compile(r'O')),
        # Halides: Cl, Br, F, I as anions.
        # Cl and Br are unambiguous two-letter tokens (no other element starts Cl/Br).
        # F: not Fe (iron); I: not In (indium) or Ir (iridium).
        ("halide",          re.compile(r'Cl\d*|Br\d*|F(?!e)\d*|(?<![A-Za-z])I(?!n|r)\d*')),
        # Organic: carbon bonded to hydrogen
        ("organic",         re.compile(r'C\d*H|H\d*C')),
    ]
    return rules

CLASS_PATTERNS = _build_class_patterns()


def classify_formula(formula: str) -> str:
    """Return chemical class key for a mineral formula string."""
    if not formula or not formula.strip():
        return "other"
    f = formula.strip()
    for cls, pat in CLASS_PATTERNS:
        if pat is None:
            # Sulfide: use helper that strips SO4/Si/Se etc. before checking for S
            if _has_S_not_SO4_not_Si(f):
                return cls
        elif pat.search(f):
            return cls
    return "other"


# ── Crystal system normalisation ─────────────────────────────────────────────

CRYSTAL_NORM: dict[str, str] = {
    'isometric':     'cubic',
    'cubic':         'cubic',
    'tetragonal':    'tetragonal',
    'orthorhombic':  'orthorhombic',
    'hexagonal':     'hexagonal',
    'trigonal':      'trigonal',
    'rhombohedral':  'trigonal',
    'monoclinic':    'monoclinic',
    'triclinic':     'triclinic',
    'amorphous':     'amorphous',
    'none':          'amorphous',
    'unknown':       'amorphous',
    '':              'amorphous',
}


def norm_crystal(raw: str) -> str:
    key = raw.strip().lower().split('/')[0].split(',')[0].strip()
    return CRYSTAL_NORM.get(key, 'amorphous')


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_minerals(path: str) -> list[dict]:
    """Parse RRUFF/IMA CSV → list of mineral dicts (IMA-approved only, sorted)."""
    minerals: list[dict] = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            print("ERROR: CSV file appears to be empty.", file=sys.stderr)
            sys.exit(1)

        cols = resolve_cols(raw_header)

        if cols['name'] is None:
            print(f"ERROR: Cannot find mineral name column in CSV header:", file=sys.stderr)
            print(f"  {raw_header}", file=sys.stderr)
            print("  Known column names: Mineral Name, Name, mineral_name", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            if not row:
                continue
            def _get(field: str) -> str:
                idx = cols.get(field)
                if idx is None or idx >= len(row):
                    return ''
                return row[idx].strip()

            name   = _get('name')
            status = _get('status')

            if not name:
                continue
            # Accept 'Approved', 'approved', or blank status (some CSVs omit it)
            if status and status.lower() not in ('approved', 'ima-approved', 'ima approved', ''):
                continue

            formula  = _get('formula')
            crystal  = _get('crystal')
            hardness = _get('hardness')
            color    = _get('color')
            lustre   = _get('lustre')

            minerals.append({
                'name':     name,
                'formula':  formula,
                'crystal':  crystal,
                'hardness': hardness,
                'color':    color,
                'lustre':   lustre,
            })

    # Sort alphabetically by name
    minerals.sort(key=lambda m: m['name'].lower())
    print(f"  Parsed {len(minerals)} IMA-approved minerals")
    return minerals


# ── .ak emission ──────────────────────────────────────────────────────────────

def build_desc(m: dict) -> str:
    parts = [m['name']]
    if m['formula']:
        parts.append(m['formula'])
    tokens = []
    crystal_norm = norm_crystal(m['crystal'])
    if crystal_norm and crystal_norm != 'amorphous':
        tokens.append(f"crystal system: {crystal_norm}")
    elif m['crystal'] and m['crystal'].strip().lower() not in ('', 'none', 'unknown'):
        tokens.append(f"crystal system: {m['crystal'].strip()}")
    if m['hardness']:
        tokens.append(f"hardness: {m['hardness']} Mohs")
    if m['color'] and m['color'].lower() not in ('', 'variable', 'various', 'none'):
        tokens.append(f"color: {m['color']}")
    if m['lustre'] and m['lustre'].lower() not in ('', 'none'):
        tokens.append(f"lustre: {m['lustre']}")
    desc = ' — '.join(parts)
    if tokens:
        desc += '; ' + '; '.join(tokens)
    return desc


def emit_mineral(fh, m: dict) -> None:
    norm    = normalize(m['name'])
    atom    = f"mineral:{norm}"
    alias   = f"mineral:rruff:{norm}"
    crystal = norm_crystal(m['crystal'])
    cls     = classify_formula(m['formula'])
    desc    = build_desc(m)

    fh.write(f'def "{atom}" "{escape_ak(desc)}"\n')
    fh.write(f'al {atom} {alias}\n')
    fh.write(f'ln {atom} mineral sys:part_of\n')
    fh.write(f'ln {atom} mineral:crystal:{crystal} sys:part_of\n')
    fh.write(f'ln {atom} mineral:class:{cls} sys:part_of\n')
    fh.write('\n')


def write_anchors(fh) -> None:
    """Write the top-level mineral anchor, crystal system anchors, and class anchors."""
    fh.write('def "mineral" "Naturally occurring inorganic solid with a characteristic chemical composition and crystalline structure. ~5,800 IMA-approved species."\n\n')

    fh.write('# Crystal system anchors\n')
    for sys_key, desc in CRYSTAL_SYSTEMS.items():
        atom = f"mineral:crystal:{sys_key}"
        fh.write(f'def "{atom}" "{escape_ak(desc)}"\n')
        fh.write(f'ln {atom} mineral sys:part_of\n')
    fh.write('\n')

    fh.write('# Chemical class anchors\n')
    for cls_key, desc in MINERAL_CLASSES.items():
        atom = f"mineral:class:{cls_key}"
        fh.write(f'def "{atom}" "{escape_ak(desc)}"\n')
        fh.write(f'ln {atom} mineral sys:part_of\n')
    fh.write('\n')


def generate(minerals: list[dict], out_dir: str, chunk_size: int, dry_run: bool):
    total     = len(minerals)
    num_files = (total + chunk_size - 1) // chunk_size

    # Class distribution
    class_counts: dict[str, int] = {}
    crystal_counts: dict[str, int] = {}
    for m in minerals:
        cls = classify_formula(m['formula'])
        crystal = norm_crystal(m['crystal'])
        class_counts[cls]       = class_counts.get(cls, 0) + 1
        crystal_counts[crystal] = crystal_counts.get(crystal, 0) + 1

    print(f"\n  Minerals: {total}")
    print(f"  Files:    {num_files} × {chunk_size} → minerals_{{NN}}.ak")
    print(f"\n  Crystal systems:")
    for k, v in sorted(crystal_counts.items(), key=lambda x: -x[1]):
        print(f"    {k:15s} {v:5d}")
    print(f"\n  Chemical classes:")
    for k, v in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"    {k:18s} {v:5d}")

    if dry_run:
        return

    os.makedirs(out_dir, exist_ok=True)

    for i in range(num_files):
        chunk = minerals[i * chunk_size:(i + 1) * chunk_size]
        fname = f"minerals_{i + 1:02d}.ak"
        fpath = os.path.join(out_dir, fname)
        start = i * chunk_size + 1
        end   = start + len(chunk) - 1

        with open(fpath, 'w', encoding='utf-8') as fh:
            if i == 0:
                fh.write(ANCHOR_HEADER)
                write_anchors(fh)
            else:
                fh.write(FILE_HEADER.format(filename=fname, mineral_range=f"{start}–{end}"))
            for m in chunk:
                emit_mineral(fh, m)
        print(f"  {fname}  {len(chunk):5d} minerals", flush=True)

    print(f"\n  Total: {total} minerals in {num_files} files → {out_dir}/")
    print("\nNext: git add app/ontology/geology/minerals_*.ak && git commit")


# ── Download helpers ──────────────────────────────────────────────────────────

def _download(url: str, dest: str, label: str) -> bool:
    """Try to download url → dest. Returns True on success."""
    print(f"Downloading {label} …")
    print(f"  URL: {url}")

    def _prog(b, bs, ts):
        if ts > 0:
            pct = min(100, b * bs * 100 // ts)
            print(f"\r  {pct}%", end='', flush=True)

    try:
        urllib.request.urlretrieve(url, dest, _prog)
        print()
        return True
    except Exception as e:
        print(f"\n  Failed: {e}")
        return False


def ensure_minerals_csv(arg: str | None) -> str:
    if arg:
        if not os.path.exists(arg):
            print(f"ERROR: --minerals-csv file not found: {arg}", file=sys.stderr)
            sys.exit(1)
        return arg

    os.makedirs(CACHE_DIR, exist_ok=True)

    # Try primary location
    dest = os.path.join(CACHE_DIR, 'ima_minerals.csv')
    if os.path.exists(dest):
        print(f"Using cached: {dest}")
        return dest

    # Try primary URL
    if _download(PRIMARY_URL, dest, "ima_minerals.csv"):
        return dest

    # Try alternative URL
    dest2 = os.path.join(CACHE_DIR, 'rruff_master.csv')
    if os.path.exists(dest2):
        print(f"Using cached: {dest2}")
        return dest2

    if _download(ALT_URL, dest2, "rruff_master_2021_01.csv"):
        return dest2

    # Both failed — print manual instructions
    print("\n" + "="*60, file=sys.stderr)
    print("AUTO-DOWNLOAD FAILED", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(__doc__.split("Manual download instructions")[1].split("Usage:")[0].strip(), file=sys.stderr)
    print("="*60, file=sys.stderr)
    sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('--minerals-csv', metavar='FILE',
                    help='Pre-downloaded RRUFF/IMA CSV file')
    ap.add_argument('--out', default=DEFAULT_OUT,
                    help=f'Output directory (default: {DEFAULT_OUT})')
    ap.add_argument('--chunk-size', type=int, default=2000,
                    help='Minerals per .ak file (default: 2000)')
    ap.add_argument('--dry-run', action='store_true',
                    help='Print stats only, write no files')
    args = ap.parse_args()

    print('[minerals_import] Locating source file …')
    csv_path = ensure_minerals_csv(args.minerals_csv)

    print(f'[minerals_import] Parsing {csv_path} …')
    minerals = parse_minerals(csv_path)

    if not minerals:
        print("ERROR: No IMA-approved minerals found. Check CSV format.", file=sys.stderr)
        print("  Expected column: 'IMA Status' with value 'Approved'", file=sys.stderr)
        print("  Or a 'Mineral Name' / 'Name' column with all rows treated as approved.", file=sys.stderr)
        sys.exit(1)

    generate(minerals, args.out, args.chunk_size, args.dry_run)


if __name__ == '__main__':
    main()
