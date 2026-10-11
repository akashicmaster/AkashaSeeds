"""
gutenberg_import.py — Project Gutenberg catalog → app/ontology/literature/lit_NN.ak

Converts the Project Gutenberg catalog CSV to Akasha .ak atoms for the optional
'literature' ontology pack.

Full texts are NOT stored — only title, author, genre, date, and a URL
pointing back to gutenberg.org. Summaries are optionally fetched from
DBpedia (Wikipedia first paragraph) via SPARQL, cached locally.

Atom IDs:    lit:work:{normalized_title}      e.g. lit:work:the_iliad
             lit:author:{normalized_name}     e.g. lit:author:homer
Aliases:     lit:gutenberg:{id}              (→ gutenberg.org/ebooks/{id})
             lit:title:{normalized_title}    (on work atom, for title-based lookup)
Links:       sys:part_of → lit:author:{name}
             sys:part_of → lit:genre:{genre}
             sys:part_of → {era_atom}         (era:classical_greek, era:medieval, etc.)

Attribution:
    Project Gutenberg — https://www.gutenberg.org/ — Public domain
    DBpedia — https://dbpedia.org/ — CC BY-SA 4.0 (if --enrich-dbpedia used)

Usage:
    python app/scripts/gutenberg_import.py

    python app/scripts/gutenberg_import.py --csv /path/to/pg_catalog.csv.gz

    python app/scripts/gutenberg_import.py --enrich-dbpedia --dry-run

    python app/scripts/gutenberg_import.py --subjects "epic,mythology,classical" --languages "en,la,grc"

    python app/scripts/gutenberg_import.py --all   # include all text types (large)

Options:
    --csv FILE          Pre-downloaded pg_catalog.csv or .gz
    --out DIR           Output directory (default: app/ontology/literature/)
    --chunk-size N      Works per .ak file (default: 2000)
    --languages LIST    Comma-separated language codes (default: major classical languages)
    --subjects LIST     Subject keywords (comma-separated) for filtering
    --all               Skip subject/bookshelf filter — include all texts in given languages
    --enrich-dbpedia    Fetch Wikipedia abstracts via DBpedia SPARQL (requires network)
    --dry-run           Print stats only, write no files

Source:
    https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz  (~10 MB)
"""

import argparse
import csv
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT  = os.path.dirname(SCRIPT_DIR)
DEFAULT_OUT   = os.path.join(PROJECT_ROOT, "app", "ontology", "literature")
CACHE_DIR     = os.path.join(PROJECT_ROOT, "out", "gutenberg_cache")
DBPEDIA_CACHE = os.path.join(PROJECT_ROOT, "out", "dbpedia_lit_cache")

CATALOG_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz"
DBPEDIA_SPARQL = "https://dbpedia.org/sparql"

DEFAULT_LANGUAGES = frozenset(
    'en,grc,la,ja,zh,fr,de,it,es,pt,ru,ar,sa,ang,enm,fro,gmh,goh'.split(',')
)

DEFAULT_SUBJECT_KEYWORDS = frozenset({
    'epic', 'mythology', 'classical literature', 'ancient',
    'medieval', 'tragedy', 'comedies', 'drama', 'poetry', 'poems',
    'philosophy', 'ethics', 'allegory', 'satire', 'fable',
    'greek literature', 'latin literature', 'roman literature',
    'japanese literature', 'chinese literature', 'arabic literature',
    'sanskrit literature', 'norse mythology', 'arthurian',
})

DEFAULT_BOOKSHELVES = frozenset({
    'harvard classics', 'ancient texts', 'classical mythology',
    'best books ever listings', 'opera',
    'du bois, w.e.b., 1868-1963',  # keep a few major authors
})

# Subject keyword → genre atom slug
GENRE_RULES: list[tuple[list[str], str]] = [
    (['epic poetry', 'heroic poetry', 'epic'],                    'epic'),
    (['tragedy', 'tragedies'],                                     'tragedy'),
    (['comedy', 'comedies'],                                       'comedy'),
    (['poem', 'poetry', 'verse', 'ode', 'sonnet', 'hymn', 'elegy', 'lyric'], 'poetry'),
    (['philosophy', 'philosophical dialogues', 'ethics'],         'philosophy'),
    (['mythology', 'myths', 'legend'],                            'mythology'),
    (['drama', 'plays', 'theatrical'],                            'drama'),
    (['novel', 'fiction', 'short stories', 'romance'],            'fiction'),
    (['history', 'memoir', 'autobiography', 'annals'],            'history'),
    (['essay', 'essays', 'meditations'],                          'essay'),
    (['satire', 'satirical'],                                      'satire'),
    (['fable', 'fables'],                                          'fable'),
    (['letter', 'letters', 'epistolary'],                         'letters'),
    (['scripture', 'religious text', 'sacred text'],              'sacred_text'),
]

# Subject/title keywords → era atom
ERA_RULES: list[tuple[list[str], str]] = [
    (['ancient greek', 'greek literature', 'greek poetry', 'homer', 'plato',
      'aristotle', 'sophocles', 'aeschylus', 'euripides', 'herodotus',
      'thucydides', 'aristophanes', 'hesiod', 'sappho'],     'era:classical_greek'),
    (['roman literature', 'latin literature', 'virgil', 'ovid', 'cicero',
      'livy', 'tacitus', 'horace', 'catullus', 'lucretius',
      'seneca', 'juvenal', 'martial'],                        'era:roman'),
    (['medieval', 'middle ages', 'arthurian', 'troubadour',
      'dante', 'chaucer', 'boccaccio', 'byzantine'],         'era:medieval'),
    (['renaissance', 'shakespeare', 'cervantes', 'montaigne',
      'early modern', 'reformation'],                         'era:renaissance'),
    (['enlightenment', '18th century', 'voltaire', 'swift',
      'defoe', 'fielding', 'richardson'],                     'era:enlightenment'),
    (['19th century', 'victorian', 'romantic period',
      'dickens', 'tolstoy', 'dostoevsky'],                    'era:nineteenth_century'),
    (['norse', 'old norse', 'viking', 'icelandic sagas',
      'eddas', 'saga'],                                        'era:viking_age'),
    (['ancient', 'classical antiquity'],                       'era:classical_greek'),
]

FILE_HEADER = """\
# {filename}
# Project Gutenberg — https://www.gutenberg.org/ — Public domain
# DBpedia abstracts (where present) — CC BY-SA 4.0
# Generated by app/scripts/gutenberg_import.py
# Works: {work_range}
#
"""


def escape_ak(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"')


def normalize(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[\s\-',.()\[\]\"!?:;/\\]+", '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return s[:70]


def strip_dates(author: str) -> str:
    """'Shakespeare, William, 1564-1616' → 'Shakespeare, William'"""
    return re.sub(r',?\s*\d{4}[\-–]\d{0,4}\.?\s*$', '', author).strip()


def primary_author(authors_field: str) -> str:
    """First author from '; '-separated list."""
    return strip_dates(authors_field.split(';')[0].strip())


def normalize_author_name(raw: str) -> str:
    """'Shakespeare, William' → 'william_shakespeare'"""
    # Swap "Last, First" to "First Last"
    name = strip_dates(raw.strip())
    if ',' in name:
        parts = [p.strip() for p in name.split(',', 1)]
        name = f"{parts[1]} {parts[0]}" if len(parts) == 2 else parts[0]
    return normalize(name)[:60]


def classify_genre(subjects: list[str]) -> str | None:
    text = ' '.join(s.lower() for s in subjects)
    for keywords, genre in GENRE_RULES:
        if any(kw in text for kw in keywords):
            return genre
    return None


def classify_era(subjects: list[str], title: str = '', authors_raw: str = '') -> str | None:
    text = ' '.join([s.lower() for s in subjects] + [title.lower(), authors_raw.lower()])
    for keywords, era in ERA_RULES:
        if any(kw in text for kw in keywords):
            return era
    return None


def load_catalog(path: str) -> list[dict]:
    """Parse Gutenberg catalog CSV (.gz or plain)."""
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        return list(reader)


def filter_works(rows: list[dict], languages: set[str],
                 subject_keywords: set[str] | None,
                 bookshelves_filter: set[str] | None,
                 include_all: bool) -> list[dict]:
    """Apply language, type, and subject/bookshelf filters."""
    works = []
    for row in rows:
        typ = row.get('Type', row.get('type', '')).strip()
        if typ.lower() != 'text':
            continue

        lang_raw = row.get('Language', row.get('language', '')).strip().lower()
        # Language field may have multiple codes: "en; fr"
        langs = set(l.strip() for l in re.split(r'[;,]', lang_raw) if l.strip())
        if not langs.intersection(languages):
            continue

        subjects_raw  = row.get('Subjects',    row.get('subjects', '')).strip()
        shelves_raw   = row.get('Bookshelves', row.get('bookshelves', '')).strip()
        title         = row.get('Title',       row.get('title', '')).strip()
        authors_field = row.get('Authors',     row.get('authors', '')).strip()

        subjects  = [s.strip() for s in subjects_raw.split(';')  if s.strip()]
        bookshelves = [b.strip() for b in shelves_raw.split(';') if b.strip()]

        if not include_all:
            text = ' '.join(subjects + bookshelves + [title, authors_field]).lower()
            subject_match   = subject_keywords  and any(kw in text for kw in subject_keywords)
            bookshelf_match = bookshelves_filter and any(
                b.lower() in [s.lower() for s in bookshelves]
                for b in bookshelves_filter
            )
            if not subject_match and not bookshelf_match:
                continue

        gid = row.get('Text#', row.get('text_id', row.get('id', ''))).strip()
        if not gid or not title:
            continue

        works.append({
            'id':         gid,
            'title':      title,
            'authors':    authors_field,
            'languages':  langs,
            'subjects':   subjects,
            'bookshelves': bookshelves,
            'issued':     row.get('Issued', row.get('issued', '')).strip(),
            'locc':       row.get('LoCC',   row.get('locc', '')).strip(),
        })
    return works


def query_dbpedia_abstract(title: str) -> str | None:
    """Fetch English Wikipedia abstract for a work title via DBpedia SPARQL."""
    os.makedirs(DBPEDIA_CACHE, exist_ok=True)
    cache_key = normalize(title) + '.json'
    cache_path = os.path.join(DBPEDIA_CACHE, cache_key)

    if os.path.exists(cache_path):
        with open(cache_path, encoding='utf-8') as f:
            d = json.load(f)
            return d.get('abstract')

    # Escape title for SPARQL
    safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
    sparql = f"""
SELECT ?abstract WHERE {{
  ?work <http://www.w3.org/2000/01/rdf-schema#label> "{safe_title}"@en ;
        <http://dbpedia.org/ontology/abstract> ?abstract .
  FILTER(lang(?abstract) = 'en')
}} LIMIT 1"""

    url = (DBPEDIA_SPARQL + '?' +
           urllib.parse.urlencode({'query': sparql, 'format': 'application/sparql-results+json'}))
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/sparql-results+json'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        bindings = data.get('results', {}).get('bindings', [])
        abstract = bindings[0]['abstract']['value'].strip() if bindings else None
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({'abstract': abstract}, f)
        return abstract
    except Exception:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({'abstract': None}, f)
        return None


def truncate(s: str, n: int = 260) -> str:
    if len(s) <= n:
        return s
    return s[:n].rsplit(' ', 1)[0].rstrip('.,;') + '…'


def build_work_atom(work: dict, author_atoms: dict[str, str],
                    abstract: str | None) -> dict:
    """Compute all fields for one work atom."""
    title      = work['title']
    norm_title = normalize(title)
    gid        = work['id']

    # Primary author
    primary    = primary_author(work['authors']) if work['authors'] else ''
    auth_norm  = normalize_author_name(primary) if primary else ''
    auth_atom  = author_atoms.get(auth_norm, '')

    genre = classify_genre(work['subjects'])
    era   = classify_era(work['subjects'], title, work['authors'])

    # Description: prefer DBpedia abstract; fall back to subjects + URL
    url   = f"gutenberg.org/ebooks/{gid}"
    if abstract:
        desc = truncate(abstract, 250) + f" [{url}]"
    else:
        subj_str = '; '.join(work['subjects'][:3]) if work['subjects'] else ''
        desc = title
        if primary:
            desc += f" — {primary}"
        if subj_str:
            desc += f". {subj_str}"
        desc += f" [{url}]"

    return {
        'atom':       f"lit:work:{norm_title}",
        'alias_gut':  f"lit:gutenberg:{gid}",
        'alias_title': f"lit:title:{norm_title}",
        'desc':       desc,
        'auth_atom':  auth_atom,
        'genre':      genre,
        'era':        era,
    }


def emit_work(fh, wa: dict) -> None:
    fh.write(f'def "{wa["atom"]}" "{escape_ak(wa["desc"][:280])}"\n')
    fh.write(f'al {wa["atom"]} {wa["alias_gut"]}\n')
    if wa['auth_atom']:
        fh.write(f'ln {wa["atom"]} {wa["auth_atom"]} sys:part_of\n')
    if wa['genre']:
        fh.write(f'ln {wa["atom"]} lit:genre:{wa["genre"]} sys:part_of\n')
    if wa['era']:
        fh.write(f'ln {wa["atom"]} {wa["era"]} sys:part_of\n')
    fh.write('\n')


def emit_author(fh, auth_norm: str, display: str) -> None:
    atom = f"lit:author:{auth_norm}"
    fh.write(f'def "{atom}" "{escape_ak(display)}"\n')
    fh.write(f'ln {atom} lit:author sys:part_of\n')
    fh.write('\n')


def emit_anchors(fh, genres: set[str]) -> None:
    fh.write('def "lit:work" "A literary work in the Akasha literature ontology."\n\n')
    fh.write('def "lit:author" "An author of a literary work."\n\n')
    fh.write('def "lit:genre" "Literary genre or form classification."\n\n')
    for g in sorted(genres):
        label = g.replace('_', ' ').title()
        fh.write(f'def "lit:genre:{g}" "{label} (literary genre)"\n')
        fh.write(f'ln lit:genre:{g} lit:genre sys:part_of\n\n')


def generate(works: list[dict], out_dir: str, chunk_size: int,
             dry_run: bool, enrich: bool) -> None:
    # Deduplicate authors
    author_map: dict[str, str] = {}   # norm_name → display_name
    for w in works:
        if w['authors']:
            primary = primary_author(w['authors'])
            an = normalize_author_name(primary)
            if an and an not in author_map:
                author_map[an] = strip_dates(primary)

    author_atoms = {an: f"lit:author:{an}" for an in author_map}

    # Optionally enrich with DBpedia
    abstracts: dict[str, str | None] = {}
    if enrich:
        print(f"  Fetching DBpedia abstracts (cached in {DBPEDIA_CACHE}) …")
        for i, w in enumerate(works):
            abstracts[w['id']] = query_dbpedia_abstract(w['title'])
            if (i + 1) % 50 == 0:
                print(f"    {i + 1}/{len(works)} …", flush=True)
            time.sleep(0.5)   # rate-limit

    # Build work atom dicts
    work_atoms = []
    seen_atoms: set[str] = set()
    for w in works:
        wa = build_work_atom(w, author_atoms, abstracts.get(w['id']))
        # Collision resolution
        base = wa['atom']
        if base in seen_atoms:
            langs = ','.join(sorted(w['languages']))
            wa['atom'] = f"{base}_{langs}"
        seen_atoms.add(wa['atom'])
        work_atoms.append(wa)

    # Collect all genres
    genres = {wa['genre'] for wa in work_atoms if wa['genre']}

    # Stats
    total   = len(work_atoms)
    n_auth  = len(author_map)
    n_files = (total + chunk_size - 1) // chunk_size
    enriched = sum(1 for v in abstracts.values() if v) if abstracts else 0

    print(f"\n  Works filtered: {total}")
    print(f"  Authors:        {n_auth}")
    print(f"  Genres:         {', '.join(sorted(genres))}")
    if enrich:
        print(f"  DBpedia abstracts found: {enriched}/{len(abstracts)}")
    print(f"  Files: {n_files} × {chunk_size} → lit_{{NN}}.ak")

    if dry_run:
        return

    os.makedirs(out_dir, exist_ok=True)

    # File 01: anchors + authors + first chunk of works
    for i in range(n_files):
        chunk  = work_atoms[i * chunk_size:(i + 1) * chunk_size]
        fname  = f"lit_{i + 1:02d}.ak"
        fpath  = os.path.join(out_dir, fname)
        start  = i * chunk_size + 1
        end    = start + len(chunk) - 1
        with open(fpath, 'w', encoding='utf-8') as fh:
            fh.write(FILE_HEADER.format(filename=fname, work_range=f"{start}–{end}"))
            if i == 0:
                emit_anchors(fh, genres)
                for an, display in sorted(author_map.items()):
                    emit_author(fh, an, display)
            for wa in chunk:
                emit_work(fh, wa)
        print(f"  {fname}  {len(chunk):5d} works", flush=True)

    print(f"\n  Total: {total} works + {n_auth} authors in {n_files} files → {out_dir}/")
    print("\nNext:")
    print("  git add app/ontology/literature/ && git commit")
    print("  onto.pack.enable literature")


def _download(url: str, dest: str, label: str) -> None:
    print(f"Downloading {label} …")

    def _prog(b, bs, ts):
        if ts > 0:
            print(f"\r  {min(100, b * bs * 100 // ts)}%", end='', flush=True)

    urllib.request.urlretrieve(url, dest, _prog)
    print()


def ensure_catalog(arg: str | None) -> str:
    if arg:
        return arg
    os.makedirs(CACHE_DIR, exist_ok=True)
    dest = os.path.join(CACHE_DIR, 'pg_catalog.csv.gz')
    if os.path.exists(dest):
        print(f"Using cached: {dest}")
        return dest
    _download(CATALOG_URL, dest, "pg_catalog.csv.gz (~10 MB)")
    return dest


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('--csv',            help='Pre-downloaded pg_catalog.csv or .gz')
    ap.add_argument('--out',            default=DEFAULT_OUT,
                    help=f'Output directory (default: {DEFAULT_OUT})')
    ap.add_argument('--chunk-size',     type=int, default=2000,
                    help='Works per .ak file (default: 2000)')
    ap.add_argument('--languages',      default=','.join(sorted(DEFAULT_LANGUAGES)),
                    help='Comma-separated language codes')
    ap.add_argument('--subjects',       default=None,
                    help='Comma-separated subject keywords (overrides default)')
    ap.add_argument('--all',            action='store_true',
                    help='Skip subject/bookshelf filter (all texts in given languages)')
    ap.add_argument('--enrich-dbpedia', action='store_true',
                    help='Fetch Wikipedia abstracts via DBpedia SPARQL (slow)')
    ap.add_argument('--dry-run',        action='store_true',
                    help='Print stats only, write no files')
    args = ap.parse_args()

    languages = set(c.strip().lower() for c in args.languages.split(',') if c.strip())

    if args.subjects:
        subject_kws: set[str] | None = set(
            s.strip().lower() for s in args.subjects.split(',') if s.strip()
        )
    else:
        subject_kws = DEFAULT_SUBJECT_KEYWORDS

    print('[gutenberg_import] Locating catalog …')
    try:
        csv_path = ensure_catalog(args.csv)
    except Exception as e:
        print(f'\nError: {e}')
        print(f'\nManual download: {CATALOG_URL}')
        print('Re-run with: --csv /path/to/pg_catalog.csv.gz')
        sys.exit(1)

    print(f'[gutenberg_import] Parsing {os.path.basename(csv_path)} …')
    rows = load_catalog(csv_path)
    print(f'  Total rows: {len(rows)}')

    print(f'[gutenberg_import] Filtering (languages={",".join(sorted(languages))}) …')
    works = filter_works(
        rows, languages,
        subject_kws if not args.all else None,
        DEFAULT_BOOKSHELVES if not args.all else None,
        args.all,
    )
    print(f'  Works after filter: {len(works)}')

    generate(works, args.out, args.chunk_size, args.dry_run, args.enrich_dbpedia)


if __name__ == '__main__':
    main()
