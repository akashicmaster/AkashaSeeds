"""
wikidata_people_import.py — Wikidata SPARQL → out/people/wikidata_people_NN.ak

Queries the Wikidata SPARQL endpoint for historically notable humans (born before
1900) with ≥10 Wikipedia sitelinks, and emits Akasha .ak ontology atoms.

To avoid SPARQL timeout, queries are batched by century birth range. Each batch
is cached separately. If a batch times out, it is automatically re-tried as two
50-year sub-ranges.

Filters applied:
    - Instance of human (Q5)
    - ≥ 10 sitelinks (10+ Wikipedia language editions)
    - Born before 1900 CE
    - Has at least one occupation (P106)
    - Has date of birth (P569)
    - Has English label

Atom IDs:    person:{normalized_label}   e.g. person:aristotle
Aliases:     person:wd:{qid}             e.g. person:wd:Q868
Links:       sys:part_of → person:field:{mapped_field}
Sets:        person:wikidata

Attribution:
    Wikidata — https://www.wikidata.org/ — CC0 1.0
    SPARQL endpoint — https://query.wikidata.org/

Usage:
    # Auto-query SPARQL (batched by century, cached):
    python app/scripts/wikidata_people_import.py

    # Use a specific cache directory:
    python app/scripts/wikidata_people_import.py --cache-dir /tmp/wd_cache

    # Dry run (stats only, no files written):
    python app/scripts/wikidata_people_import.py --dry-run

    # Custom output:
    python app/scripts/wikidata_people_import.py --out out/people

Options:
    --out DIR         Output directory (default: out/people)
    --chunk-size N    Atoms per .ak file (default: 500)
    --cache-dir DIR   Cache directory for SPARQL JSON results
    --dry-run         Print stats only, write no files

Source:
    https://query.wikidata.org/sparql
    User-Agent: AkashaOntologyBuilder/1.0
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_OUT  = os.path.join(PROJECT_ROOT, "out", "people")
DEFAULT_CACHE_DIR = os.path.join(PROJECT_ROOT, "out", "wikidata_people_cache")

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_BASE   = "https://www.wikidata.org/wiki/"
USER_AGENT      = "AkashaOntologyBuilder/1.0 (contact: ontology@akasha.local)"

# ── Century-based birth ranges (start_year_inclusive, end_year_exclusive) ──
# Each is queried and cached separately. Name used in cache filename.
CENTURY_RANGES = [
    ("ancient",  None,  500),   # before 500 CE (and BCE)
    ("c06_10",   500,  1000),
    ("c11_13",  1000,  1300),
    ("c14_15",  1300,  1500),
    ("c16",     1500,  1600),
    ("c17",     1600,  1700),
    ("c18",     1700,  1800),
    ("c19",     1800,  1900),
]

# If a century batch times out, split into these 50-year sub-ranges
def sub_ranges(start: int | None, end: int) -> list[tuple[str, int | None, int]]:
    """Produce 50-year sub-ranges for a century range."""
    if start is None:
        return [
            ("ancient_a", None, 0),
            ("ancient_b", 0, 250),
            ("ancient_c", 250, 500),
        ]
    mid = start + (end - start) // 2
    return [
        (f"sub_{start}_{mid}", start, mid),
        (f"sub_{mid}_{end}", mid, end),
    ]


# ── Occupation → person:field: mapping ──
OCCUPATION_FIELD_MAP: dict[str, str] = {
    # Philosophy
    "philosopher":                  "philosophy",
    "epistemologist":               "philosophy",
    "metaphysician":                "philosophy",
    "logician":                     "philosophy",
    "ethicist":                     "philosophy",
    "stoic philosopher":            "philosophy",
    # Science
    "physicist":                    "science",
    "chemist":                      "science",
    "biologist":                    "science",
    "naturalist":                   "science",
    "astronomer":                   "science",
    "botanist":                     "science",
    "zoologist":                    "science",
    "geologist":                    "science",
    "scientist":                    "science",
    "alchemist":                    "science",
    "geographer":                   "science",
    # Mathematics
    "mathematician":                "mathematics",
    "statistician":                 "mathematics",
    "cryptographer":                "mathematics",
    # Medicine
    "physician":                    "medicine",
    "surgeon":                      "medicine",
    "anatomist":                    "medicine",
    "pharmacologist":               "medicine",
    "medical researcher":           "medicine",
    "psychiatrist":                 "medicine",
    # Literature
    "poet":                         "literature",
    "novelist":                     "literature",
    "playwright":                   "literature",
    "writer":                       "literature",
    "author":                       "literature",
    "essayist":                     "literature",
    "historian":                    "literature",
    "biographer":                   "literature",
    "scholar":                      "linguistics_scholarship",
    # Music
    "composer":                     "music",
    "musician":                     "music",
    "singer":                       "music",
    "conductor":                    "music",
    "lutenist":                     "music",
    "organist":                     "music",
    "violinist":                    "music",
    "cellist":                      "music",
    # Visual Arts
    "painter":                      "visual_arts",
    "sculptor":                     "visual_arts",
    "engraver":                     "visual_arts",
    "illustrator":                  "visual_arts",
    "printmaker":                   "visual_arts",
    "draughtsman":                  "visual_arts",
    "goldsmith":                    "visual_arts",
    "ceramicist":                   "visual_arts",
    # Architecture
    "architect":                    "architecture",
    "urban planner":                "architecture",
    # Religion
    "theologian":                   "religion",
    "bishop":                       "religion",
    "pope":                         "religion",
    "cardinal":                     "religion",
    "abbot":                        "religion",
    "priest":                       "religion",
    "rabbi":                        "religion",
    "monk":                         "religion",
    "mystic":                       "religion",
    "imam":                         "religion",
    "saint":                        "religion",
    "prophet":                      "religion",
    # Politics & statecraft
    "statesman":                    "politics_statecraft",
    "politician":                   "politics_statecraft",
    "emperor":                      "politics_statecraft",
    "king":                         "politics_statecraft",
    "queen":                        "politics_statecraft",
    "pharaoh":                      "politics_statecraft",
    "sultan":                       "politics_statecraft",
    "caliph":                       "politics_statecraft",
    "monarch":                      "politics_statecraft",
    "president":                    "politics_statecraft",
    "prime minister":               "politics_statecraft",
    "chancellor":                   "politics_statecraft",
    "diplomat":                     "politics_statecraft",
    "duke":                         "politics_statecraft",
    "count":                        "politics_statecraft",
    "prince":                       "politics_statecraft",
    # Military
    "general":                      "military",
    "admiral":                      "military",
    "military commander":           "military",
    "military officer":             "military",
    "soldier":                      "military",
    "field marshal":                "military",
    "condottiere":                  "military",
    # Exploration & navigation
    "explorer":                     "exploration_navigation",
    "navigator":                    "exploration_navigation",
    "cartographer":                 "exploration_navigation",
    "sailor":                       "exploration_navigation",
    # Law
    "jurist":                       "law",
    "judge":                        "law",
    "lawyer":                       "law",
    "legal scholar":                "law",
    # Economics
    "economist":                    "economics",
    "merchant":                     "economics",
    "banker":                       "economics",
    # Engineering & invention
    "engineer":                     "engineering_invention",
    "inventor":                     "engineering_invention",
    "mechanical engineer":          "engineering_invention",
    "civil engineer":               "engineering_invention",
    # Theater & performing arts
    "actor":                        "theater_performing_arts",
    "actress":                      "theater_performing_arts",
    "comedian":                     "theater_performing_arts",
    "theatrical director":          "theater_performing_arts",
    # Linguistics & scholarship
    "linguist":                     "linguistics_scholarship",
    "philologist":                  "linguistics_scholarship",
    "grammarian":                   "linguistics_scholarship",
    "lexicographer":                "linguistics_scholarship",
    "translator":                   "linguistics_scholarship",
    "antiquarian":                  "linguistics_scholarship",
    "encyclopedist":                "linguistics_scholarship",
}

# Valid person:field: atom IDs
KNOWN_FIELDS = frozenset({
    "philosophy", "science", "mathematics", "medicine", "literature",
    "music", "visual_arts", "architecture", "religion", "politics_statecraft",
    "military", "exploration_navigation", "law", "economics",
    "engineering_invention", "theater_performing_arts", "linguistics_scholarship",
})

FILE_HEADER = """\
# {filename}
# Wikidata — https://www.wikidata.org/ — CC0 1.0
# Historical humans (born < 1900, ≥10 Wikipedia editions)
# Generated by app/scripts/wikidata_people_import.py — chunk {chunk_num}
# People: {person_range}
#
"""


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def escape_ak(s: str) -> str:
    """Escape double-quotes and backslashes for .ak def strings."""
    return s.replace('\\', '\\\\').replace('"', '\\"')


def truncate(s: str, n: int = 320) -> str:
    if len(s) <= n:
        return s
    return s[:n - 1].rsplit(' ', 1)[0].rstrip(' ,;') + '…'


def normalize_label(name: str) -> str:
    """Convert a person name to a safe atom ID component (≤50 chars)."""
    s = unicodedata.normalize('NFD', name)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[\s\-,.'()/\\&]+", '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return s[:50]


def extract_qid(uri: str) -> str:
    """Extract Q-number from a Wikidata entity URI."""
    m = re.search(r'(Q\d+)$', uri)
    return m.group(1) if m else uri.strip()


def val(row: dict, field: str) -> str | None:
    """Safely extract string value from a SPARQL result binding row."""
    entry = row.get(field)
    if not entry:
        return None
    v = entry.get('value', '').strip()
    return v if v else None


def map_occupation_to_field(occupation_label: str) -> str | None:
    """Map a Wikidata occupation label to a person:field: atom ID, or None."""
    if not occupation_label:
        return None
    key = occupation_label.strip().lower()
    field = OCCUPATION_FIELD_MAP.get(key)
    if field and field in KNOWN_FIELDS:
        return field
    # Partial match: check if any known key is a substring of the occupation
    for occ_key, field_val in OCCUPATION_FIELD_MAP.items():
        if occ_key in key or key in occ_key:
            if field_val in KNOWN_FIELDS:
                return field_val
    return None


def build_sparql_query(birth_start: int | None, birth_end: int,
                       min_sitelinks: int = 10) -> str:
    """Build a SPARQL query for the given birth year range."""
    if birth_start is None:
        birth_filter = f"FILTER(YEAR(?dob) < {birth_end})"
    else:
        birth_filter = (
            f"FILTER(YEAR(?dob) >= {birth_start} && YEAR(?dob) < {birth_end})"
        )

    return f"""\
SELECT DISTINCT ?person ?personLabel ?dob ?dod ?occupationLabel ?nationalityLabel WHERE {{
  ?person wdt:P31 wd:Q5 .
  ?person wdt:P569 ?dob .
  ?person wdt:P106 ?occupation .
  ?person wikibase:sitelinks ?links .
  FILTER(?links >= {min_sitelinks})
  {birth_filter}
  OPTIONAL {{ ?person wdt:P570 ?dod }}
  OPTIONAL {{ ?person wdt:P27 ?nationality }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY YEAR(?dob) ?personLabel
LIMIT 10000"""


def sparql_get(query: str, timeout: int = 120) -> dict:
    """Execute a SPARQL query against Wikidata; return parsed JSON."""
    params = urllib.parse.urlencode({
        'query':  query,
        'format': 'application/sparql-results+json',
    })
    url = SPARQL_ENDPOINT + '?' + params
    req = urllib.request.Request(url, headers={
        'Accept':     'application/sparql-results+json',
        'User-Agent': USER_AGENT,
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fetch_batch(label: str, birth_start: int | None, birth_end: int,
                cache_dir: str) -> list[dict]:
    """
    Fetch one century batch from cache or SPARQL.
    On timeout, automatically splits into 50-year sub-ranges.
    Returns a list of SPARQL result binding rows.
    """
    cache_file = os.path.join(cache_dir, f"people_{label}.json")

    if os.path.exists(cache_file):
        eprint(f"  [cache] {label}: {cache_file}")
        with open(cache_file, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('results', {}).get('bindings', [])

    eprint(f"  [sparql] Querying batch: {label} "
           f"(birth {birth_start or '<'}…{birth_end}) …")
    query = build_sparql_query(birth_start, birth_end)

    try:
        data = sparql_get(query, timeout=120)
        bindings = data.get('results', {}).get('bindings', [])
        eprint(f"    → {len(bindings):,} rows")

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        eprint(f"    Cached to: {cache_file}")
        return bindings

    except (urllib.error.URLError, TimeoutError, OSError) as e:
        eprint(f"  Timeout/error on batch '{label}': {e}")
        eprint(f"  Splitting into 50-year sub-ranges …")

        all_bindings: list[dict] = []
        for sub_label, sub_start, sub_end in sub_ranges(birth_start, birth_end):
            eprint(f"    Sub-range: {sub_label} ({sub_start}–{sub_end}) …")
            sub_cache = os.path.join(cache_dir, f"people_{sub_label}.json")

            if os.path.exists(sub_cache):
                eprint(f"      [cache] {sub_cache}")
                with open(sub_cache, encoding='utf-8') as f:
                    sub_data = json.load(f)
                sub_bindings = sub_data.get('results', {}).get('bindings', [])
            else:
                sub_query = build_sparql_query(sub_start, sub_end)
                try:
                    eprint(f"      Querying …")
                    sub_data = sparql_get(sub_query, timeout=90)
                    sub_bindings = sub_data.get('results', {}).get('bindings', [])
                    eprint(f"      → {len(sub_bindings):,} rows")
                    with open(sub_cache, 'w', encoding='utf-8') as f:
                        json.dump(sub_data, f, ensure_ascii=False)
                except Exception as sub_e:
                    eprint(f"      Sub-range failed: {sub_e} — skipping")
                    sub_bindings = []
                time.sleep(2)  # polite delay between sub-range queries

            all_bindings.extend(sub_bindings)

        # Cache combined result for this century so we don't re-split next time
        combined = {'results': {'bindings': all_bindings}}
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False)
        eprint(f"  Combined {len(all_bindings):,} rows → cached to {cache_file}")
        return all_bindings


def parse_bindings(all_bindings: list[dict]) -> list[dict]:
    """
    Collapse multi-row SPARQL results (multiple occupations per person) into
    one record per QID. Keep first occupation; deduplicate by QID.
    Returns list of person dicts, sorted by birth year then name.
    """
    by_qid: dict[str, dict] = {}

    for row in all_bindings:
        person_uri = val(row, 'person')
        if not person_uri:
            continue
        qid   = extract_qid(person_uri)
        label = val(row, 'personLabel') or ''

        # Skip rows where label is just the QID (Wikidata fallback)
        if not label or label == qid:
            continue

        dob_raw = val(row, 'dob') or ''
        dod_raw = val(row, 'dod') or ''
        occ     = val(row, 'occupationLabel') or ''
        nat     = val(row, 'nationalityLabel') or ''

        # Extract year from ISO date string like "1724-01-01T00:00:00Z"
        birth_year = ''
        if dob_raw:
            m = re.match(r'^(-?\d+)', dob_raw)
            if m:
                birth_year = m.group(1)

        death_year = ''
        if dod_raw:
            m = re.match(r'^(-?\d+)', dod_raw)
            if m:
                death_year = m.group(1)

        if qid in by_qid:
            rec = by_qid[qid]
            # Prefer first non-empty occupation; supplement nationality
            if occ and not rec['occupation']:
                rec['occupation'] = occ
            if nat and not rec['nationality']:
                rec['nationality'] = nat
        else:
            by_qid[qid] = {
                'qid':         qid,
                'label':       label,
                'birth_year':  birth_year,
                'death_year':  death_year,
                'occupation':  occ,
                'nationality': nat,
            }

    records = list(by_qid.values())

    # Sort by birth year ascending, then label alphabetically
    def sort_key(r: dict):
        try:
            yr = int(r['birth_year']) if r['birth_year'] else 9999
        except ValueError:
            yr = 9999
        return (yr, r['label'].lower())

    records.sort(key=sort_key)
    return records


def assign_slugs(records: list[dict]) -> None:
    """
    Assign a unique atom slug to each record in-place.
    Collisions resolved by appending _b, _c, _d, …
    """
    seen: dict[str, int] = {}
    suffixes = ['_b', '_c', '_d', '_e', '_f', '_g', '_h', '_i', '_j']

    for rec in records:
        base = normalize_label(rec['label'])
        if base not in seen:
            seen[base] = 0
            rec['slug'] = base
        else:
            seen[base] += 1
            idx = seen[base] - 1
            if idx < len(suffixes):
                rec['slug'] = base + suffixes[idx]
            else:
                rec['slug'] = f"{base}_{seen[base] + 1}"


def build_description(rec: dict) -> str:
    """Build atom description string."""
    label       = rec['label']
    birth_year  = rec['birth_year']
    death_year  = rec['death_year']
    occupation  = rec['occupation']
    nationality = rec['nationality']
    qid         = rec['qid']

    # Date range
    if birth_year and death_year:
        dates = f"({birth_year}–{death_year})"
    elif birth_year:
        dates = f"(b.{birth_year})"
    else:
        dates = ''

    url = f"{WIKIDATA_BASE}{qid}"

    parts: list[str] = []
    name_part = f"{label} {dates}".strip() if dates else label
    parts.append(name_part)
    if occupation:
        parts.append(occupation)
    if nationality:
        parts.append(nationality)
    parts.append(url)

    desc = ', '.join(parts[:-1])
    if desc:
        desc = f"{desc}. {url}"
    else:
        desc = url

    return truncate(desc, 320)


def emit_person(fh, rec: dict) -> None:
    """Write one person atom block to fh."""
    slug  = rec['slug']
    qid   = rec['qid']
    atom  = f"person:{slug}"
    alias = f"person:wd:{qid}"
    desc  = build_description(rec)

    occ_field = map_occupation_to_field(rec.get('occupation', ''))

    fh.write(f'def "{atom}" "{escape_ak(desc)}"\n')
    fh.write(f'al {atom} {alias}\n')
    if occ_field:
        fh.write(f'ln {atom} person:field:{occ_field} sys:part_of\n')
    fh.write(f'set.add name="person:wikidata" id="{atom}"\n')
    fh.write('\n')


def fetch_all_batches(cache_dir: str) -> list[dict]:
    """Fetch all century batches and return combined list of SPARQL binding rows."""
    os.makedirs(cache_dir, exist_ok=True)
    all_bindings: list[dict] = []

    for label, birth_start, birth_end in CENTURY_RANGES:
        try:
            bindings = fetch_batch(label, birth_start, birth_end, cache_dir)
            all_bindings.extend(bindings)
            eprint(f"  Batch '{label}': {len(bindings):,} rows "
                   f"(running total: {len(all_bindings):,})")
        except Exception as e:
            eprint(f"  Batch '{label}' failed completely: {e} — skipping")
        # Polite delay between century-level queries
        time.sleep(1)

    return all_bindings


def generate(records: list[dict], out_dir: str, chunk_size: int, dry_run: bool) -> None:
    total     = len(records)
    num_files = (total + chunk_size - 1) // chunk_size if total else 0

    # Field coverage stats
    field_counts: dict[str, int] = {}
    for r in records:
        f = map_occupation_to_field(r.get('occupation', ''))
        key = f if f else '(unmapped)'
        field_counts[key] = field_counts.get(key, 0) + 1

    with_birth = sum(1 for r in records if r.get('birth_year'))
    with_death = sum(1 for r in records if r.get('death_year'))

    eprint(f"\n  People:      {total:,}")
    eprint(f"  With birth:  {with_birth:,}")
    eprint(f"  With death:  {with_death:,}")
    eprint(f"  Files:       {num_files} × {chunk_size} → wikidata_people_{{NN}}.ak")
    eprint(f"  Top fields:")
    for fld, cnt in sorted(field_counts.items(), key=lambda x: -x[1])[:10]:
        eprint(f"    {fld:45s} {cnt:6d}")

    if dry_run:
        eprint('\n--- dry-run: first 20 output lines ---')
        import io as _io
        buf = _io.StringIO()
        for r in records[:5]:
            emit_person(buf, r)
        lines = buf.getvalue().splitlines()
        for line in lines[:20]:
            print(line)
        return

    if total == 0:
        eprint('[wikidata_people_import] No records to write.')
        return

    os.makedirs(out_dir, exist_ok=True)

    for i in range(num_files):
        chunk  = records[i * chunk_size:(i + 1) * chunk_size]
        fname  = f"wikidata_people_{i + 1:02d}.ak"
        fpath  = os.path.join(out_dir, fname)
        start  = i * chunk_size + 1
        end    = start + len(chunk) - 1
        with open(fpath, 'w', encoding='utf-8') as fh:
            fh.write(FILE_HEADER.format(
                filename=fname,
                chunk_num=i + 1,
                person_range=f"{start}–{end}",
            ))
            for r in chunk:
                emit_person(fh, r)
        eprint(f"  {fname}  {len(chunk):5d} people", flush=True)

    eprint(f"\n  Total: {total:,} people in {num_files} files → {out_dir}/")
    eprint("\nNext: git add out/people/wikidata_people_*.ak && git commit")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('--out',        default=DEFAULT_OUT,
                    help=f'Output directory (default: {DEFAULT_OUT})')
    ap.add_argument('--chunk-size', type=int, default=500,
                    help='Atoms per .ak file (default: 500)')
    ap.add_argument('--cache-dir',  default=DEFAULT_CACHE_DIR,
                    help=f'Cache directory for SPARQL results (default: {DEFAULT_CACHE_DIR})')
    ap.add_argument('--dry-run',    action='store_true',
                    help='Print stats only, write no files')
    args = ap.parse_args()

    eprint('[wikidata_people_import] Fetching data from Wikidata SPARQL (batched by century) …')
    eprint(f'  Cache dir: {args.cache_dir}')
    eprint(f'  Endpoint:  {SPARQL_ENDPOINT}')

    try:
        all_bindings = fetch_all_batches(args.cache_dir)
    except Exception as e:
        eprint(f'\nError: {e}')
        eprint('\nManual download instructions:')
        eprint('  Visit https://query.wikidata.org/')
        eprint('  Run the SPARQL query from build_sparql_query() for each century range')
        eprint('  Save each result as JSON to your --cache-dir as people_{label}.json')
        eprint('  Then re-run this script (it will use the cached files)')
        sys.exit(1)

    if not all_bindings:
        eprint('No SPARQL results returned. Check network or use cached files.')
        sys.exit(1)

    eprint(f'[wikidata_people_import] Total rows from all batches: {len(all_bindings):,}')
    eprint('[wikidata_people_import] Parsing and deduplicating …')

    records = parse_bindings(all_bindings)
    eprint(f'  {len(records):,} unique people after dedup')

    eprint('[wikidata_people_import] Assigning slugs …')
    assign_slugs(records)

    generate(records, args.out, args.chunk_size, args.dry_run)


if __name__ == '__main__':
    main()
