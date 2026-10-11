"""
wikidata_food_import.py — Wikidata (CC0) → food-domain skeleton .ak

Cross-fetches five food-domain gaps from Wikidata and writes one .ak per
category, ranked by notability (sitelink count) so a bounded pull gives the
most-notable "skeleton" of each area:

    category   root class (P31/P279*)     namespace     bridges
    ─────────  ─────────────────────────  ────────────  ─────────────────────
    dish       dish            (Q746549)  dish:*        → cuisine:*  → ingred:*
    cuisine    cuisine        (Q1778821)  cuisine:*     (merges with existing)
    technique  cooking technique (Q1039303) technique:* → dish:* (optional)
    beverage   drink           (Q40050)   beverage:*    → beverage parent
    nutrient   nutrient       (Q181394)   nutrient:*    → nutrient class

Atom IDs:   <ns>:<normalized_label>     e.g. dish:paella, cuisine:italian
Aliases:    <ns>:wd:<QID>               e.g. dish:wd:Q4685
Sets:       <ns>:wikidata               (all atoms of the category)
Links:      dish  --thesaurus:related-->  cuisine:<c>       (P2012 cuisine)
            dish  --thesaurus:related-->  ingred:<i>        (P186, matched)
            cuisine --sys:part_of-->      cuisine:<parent>  (P361)
            beverage --sys:part_of-->     beverage:<parent> (P279)
            nutrient --sys:part_of-->     nutrient:<class>  (vitamin/mineral/…)

The dish→ingred bridge reuses the existing culinary ingredient concepts
(ingred:*, 261 atoms in base): a dish's Wikidata "made from material" (P186)
is matched to an ingredient alias, so browsing an ingredient reaches the
dishes that use it. cuisine:* labels are stripped of the trailing "cuisine"/
"food" so they unify with the hand-authored cuisine:* atoms already in base.

License:  Wikidata — CC0 1.0 (public domain). Safe to bundle.
          Attribution: https://www.wikidata.org/

Usage:
    python app/scripts/wikidata_food_import.py                 # all categories → ontology/base
    python app/scripts/wikidata_food_import.py --dry-run       # counts only, no files
    python app/scripts/wikidata_food_import.py --only dish,cuisine
    python app/scripts/wikidata_food_import.py --cap dish=1500 --out ontology/base

Options:
    --only LIST     Comma list of categories (default: all five)
    --out DIR       Output directory (default: ontology/base)
    --cap C=N       Per-category notability cap (repeatable); defaults below
    --cache-dir DIR SPARQL result cache (default: out/wikidata_food_cache)
    --dry-run       Print stats only, write no files

Note: run this on a host that can reach https://query.wikidata.org/ .
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
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)            # the application root (app/)
DEFAULT_OUT  = os.path.join(PROJECT_ROOT, "ontology", "base")
DEFAULT_CACHE = os.path.join(PROJECT_ROOT, "out", "wikidata_food_cache")

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "AkashaOntologyBuilder/1.0 (contact: ontology@akasha.local)"

# ── Category definitions ─────────────────────────────────────────────────────
# root  : Wikidata class; members are P31/P279* of it.
# ns    : atom namespace.
# cap   : default notability cap (most-sitelinked first).
# rel   : extra property fetched for the primary link (None = none).
#         P2012 cuisine · P361 part-of · P279 subclass-of.
# If a QID looks wrong for your Wikidata snapshot, adjust it here — a bad root
# simply yields 0 rows (visible under --dry-run).
CATEGORIES = {
    "cuisine":   {"root": "Q1778821", "ns": "cuisine",   "cap": 400, "rel": "P361", "rel_ns": "cuisine"},
    "dish":      {"root": "Q746549",  "ns": "dish",      "cap": 1500, "rel": "P2012", "rel_ns": "cuisine"},
    "technique": {"root": "Q1039303", "ns": "technique", "cap": 300, "rel": None,   "rel_ns": None},
    "beverage":  {"root": "Q40050",   "ns": "beverage",  "cap": 800,  "rel": "P279", "rel_ns": "beverage"},
    "nutrient":  {"root": "Q181394",  "ns": "nutrient",  "cap": 250,  "rel": "P279", "rel_ns": "nutrient"},
}


# ── helpers ──────────────────────────────────────────────────────────────────
def normalize(name: str) -> str:
    """Label → atom name component: lowercase, NFD→ASCII, underscores."""
    s = unicodedata.normalize('NFD', name)
    s = s.encode('ascii', 'ignore').decode('ascii').lower()
    s = re.sub(r'[\s\-/,.()\[\]\'\"]+', '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return s[:60]


def cuisine_slug(label: str) -> str:
    """Cuisine label → slug that unifies with the hand-authored cuisine:* atoms
    (drop a trailing 'cuisine'/'food'): 'Italian cuisine' → 'italian'."""
    s = normalize(label)
    s = re.sub(r'_(cuisine|food|gastronomy)$', '', s)
    return s or normalize(label)


def escape_ak(s: str) -> str:
    return (s or "").replace('\\', ' ').replace('"', "'").replace('\n', ' ').strip()


def qid_of(binding_uri: str) -> str:
    return binding_uri.rsplit('/', 1)[-1]


# ── ingred bridge map (from the existing ontology) ───────────────────────────
def load_ingred_terms(root_path: str) -> dict:
    """term → ingred atom id, from every ingred def/alias already in ontology."""
    import glob
    term2id = {}
    for fp in glob.glob(os.path.join(root_path, "ontology", "**", "*.ak"), recursive=True):
        try:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for atom in re.findall(r'^def\s+"(ingred:[^"]+)"', txt, re.M):
            term2id.setdefault(atom.split(":")[-1].lower(), atom)
        for atom, alias in re.findall(r'^al\s+(ingred:\S+)\s+(\S+)', txt, re.M):
            term2id.setdefault(alias.split(":")[-1].lower(), atom)
    return term2id


def _singular(w: str) -> str:
    w = w.lower()
    if len(w) > 4 and w.endswith("ies"): return w[:-3] + "y"
    if len(w) > 4 and w.endswith("oes"): return w[:-2]
    if len(w) > 4 and w.endswith(("ses", "ches", "shes", "xes")): return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"): return w[:-1]
    return w


def ingred_for(label: str, ingred_terms: dict):
    """Match an ingredient label (e.g. 'chicken', 'olive oil') to an ingred atom."""
    for tok in [_singular(t) for t in normalize(label).split("_")[:3]]:
        if tok in ingred_terms:
            return ingred_terms[tok]
    return None


# ── SPARQL ───────────────────────────────────────────────────────────────────
def sparql(query: str, label: str, retries: int = 3) -> list:
    params = urllib.parse.urlencode({'query': query, 'format': 'json'})
    req = urllib.request.Request(
        f"{SPARQL_ENDPOINT}?{params}",
        headers={'User-Agent': USER_AGENT, 'Accept': 'application/sparql-results+json'})
    for attempt in range(1, retries + 1):
        try:
            print(f"  Querying Wikidata: {label} (try {attempt}) …", file=sys.stderr)
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            rows = data['results']['bindings']
            print(f"  → {len(rows)} rows", file=sys.stderr)
            return rows
        except Exception as e:
            msg = str(e)
            if attempt < retries and any(k in msg.lower() for k in ('timed out', '429', '500', '503')):
                time.sleep(2 ** attempt)
                continue
            raise


def build_query(root: str, rel: str, cap: int) -> str:
    """Notability-ranked members of a class, with one optional relation value."""
    rel_line = f"OPTIONAL {{ ?item wdt:{rel} ?rel . }}" if rel else ""
    rel_sel  = "?rel ?relLabel" if rel else ""
    return f"""SELECT ?item ?itemLabel ?sl {rel_sel} WHERE {{
  ?item wdt:P31/wdt:P279* wd:{root} .
  ?item wikibase:sitelinks ?sl .
  {rel_line}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} ORDER BY DESC(?sl) LIMIT {cap}"""


DISH_INGREDIENTS_QUERY = """SELECT ?item ?ingLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q746549 .
  ?item wikibase:sitelinks ?sl .
  ?item wdt:P186 ?ing .
  ?ing rdfs:label ?ingLabel . FILTER(lang(?ingLabel)="en")
}} ORDER BY DESC(?sl) LIMIT {cap}"""


# ── parse + emit ─────────────────────────────────────────────────────────────
def parse_rows(rows: list, cat: dict) -> dict:
    """QID → {label, slug, rel_slug}."""
    out = {}
    slugger = cuisine_slug if cat["ns"] == "cuisine" else normalize
    for r in rows:
        if 'item' not in r or 'itemLabel' not in r:
            continue
        label = r['itemLabel']['value']
        if not label or label.startswith('Q') and label[1:].isdigit():
            continue  # unlabeled item — skip (Q-id came back as label)
        qid = qid_of(r['item']['value'])
        slug = slugger(label)
        if not slug:
            continue
        rec = out.setdefault(qid, {"label": label, "slug": slug, "rels": set()})
        if cat["rel"] and 'relLabel' in r:
            rlabel = r['relLabel']['value']
            if rlabel and not (rlabel.startswith('Q') and rlabel[1:].isdigit()):
                rslug = (cuisine_slug if cat["rel_ns"] == "cuisine" else normalize)(rlabel)
                if rslug:
                    rec["rels"].add(rslug)
    return out


def emit_category(name: str, cat: dict, items: dict,
                  dish_ings: dict, ingred_terms: dict) -> str:
    ns = cat["ns"]
    lines = [
        f"# Akasha ontology — namespace: {ns} (Wikidata skeleton, CC0)",
        f"# {len(items)} most-notable {name} concepts fetched from Wikidata.",
        f"# Source: https://www.wikidata.org/  ·  CC0 1.0 (public domain)",
        "# atoms: def + wd alias + set membership; links to related concepts.",
        "",
    ]
    for qid, rec in sorted(items.items(), key=lambda kv: kv[1]["slug"]):
        atom = f"{ns}:{rec['slug']}"
        lines.append(f'def "{atom}" "{escape_ak(rec["label"])}"')
        lines.append(f'al {atom} {ns}:wd:{qid}')
        lines.append(f'set.add name="{ns}:wikidata" id="{atom}"')
        # primary relation (cuisine / part-of / subclass)
        for rslug in sorted(rec["rels"]):
            if cat["rel_ns"] == "cuisine":
                lines.append(f'ln {atom} cuisine:{rslug} thesaurus:related')
            else:
                lines.append(f'ln {atom} {cat["rel_ns"]}:{rslug} sys:part_of')
        # dish → ingred bridges
        if ns == "dish":
            for ing_label in sorted(dish_ings.get(qid, [])):
                tgt = ingred_for(ing_label, ingred_terms)
                if tgt:
                    lines.append(f'ln {atom} {tgt} thesaurus:related')
        lines.append("")
    return "\n".join(lines) + "\n"


# ── driver ───────────────────────────────────────────────────────────────────
def _bindings(obj):
    """Normalise SPARQL results from any of the shapes a query.wikidata.org
    download can take, so a JSON dropped into --cache-dir works as-is:
      • full response  {"head":…, "results":{"bindings":[{var:{"value":…}}]}}
      • bare bindings   [{var:{"value":…}}]
      • "Simplified"    [{var: "plain string"}]   ← WDQS "Simplified" download
    Plain-string values are wrapped to {"value": …} so parse_rows is uniform."""
    rows = (obj.get("results") or {}).get("bindings", []) if isinstance(obj, dict) else (obj or [])
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out.append({k: (v if isinstance(v, dict) else {"value": str(v)})
                    for k, v in r.items() if v is not None})
    return out


def fetch_category(name: str, cat: dict, cache_dir: str) -> list:
    cache = os.path.join(cache_dir, f"{name}.json")
    if os.path.exists(cache):
        print(f"[{name}] cached: {cache}", file=sys.stderr)
        return _bindings(json.load(open(cache, encoding="utf-8")))
    rows = sparql(build_query(cat["root"], cat["rel"], cat["cap"]), name)
    os.makedirs(cache_dir, exist_ok=True)
    json.dump(rows, open(cache, "w", encoding="utf-8"))
    return rows


def fetch_dish_ingredients(cap: int, cache_dir: str) -> dict:
    cache = os.path.join(cache_dir, "dish_ingredients.json")
    if os.path.exists(cache):
        rows = _bindings(json.load(open(cache, encoding="utf-8")))
    else:
        rows = sparql(DISH_INGREDIENTS_QUERY.format(cap=cap * 6), "dish ingredients")
        os.makedirs(cache_dir, exist_ok=True)
        json.dump(rows, open(cache, "w", encoding="utf-8"))
    by_dish = {}
    for r in rows:
        if 'item' in r and 'ingLabel' in r:
            by_dish.setdefault(qid_of(r['item']['value']), set()).add(r['ingLabel']['value'])
    return by_dish


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', default="")
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--cap', action='append', default=[])
    ap.add_argument('--cache-dir', default=DEFAULT_CACHE)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    for c in args.cap:
        if '=' in c:
            k, v = c.split('=', 1)
            if k in CATEGORIES:
                CATEGORIES[k]["cap"] = int(v)

    wanted = [c.strip() for c in args.only.split(',') if c.strip()] or list(CATEGORIES)
    ingred_terms = load_ingred_terms(PROJECT_ROOT)
    print(f"[wikidata_food] ingred bridge targets: {len(ingred_terms)}", file=sys.stderr)

    dish_ings = {}
    if 'dish' in wanted:
        dish_ings = fetch_dish_ingredients(CATEGORIES['dish']['cap'], args.cache_dir)
        print(f"[wikidata_food] dishes with ingredient data: {len(dish_ings)}", file=sys.stderr)

    total = 0
    for name in wanted:
        if name not in CATEGORIES:
            print(f"  [!] unknown category: {name}", file=sys.stderr); continue
        cat = CATEGORIES[name]
        rows = fetch_category(name, cat, args.cache_dir)
        items = parse_rows(rows, cat)
        bridged = 0
        if name == "dish":
            for qid in items:
                if any(ingred_for(l, ingred_terms) for l in dish_ings.get(qid, [])):
                    bridged += 1
        print(f"  {name:10s}: {len(items)} atoms"
              + (f", {bridged} bridged to ingred" if name == "dish" else ""))
        total += len(items)
        if not args.dry_run:
            os.makedirs(args.out, exist_ok=True)
            path = os.path.join(args.out, f"food_wd_{name}.ak")
            open(path, "w", encoding="utf-8").write(
                emit_category(name, cat, items, dish_ings, ingred_terms))
            print(f"    → {path}")
    print(f"\n  Total: {total} atoms across {len(wanted)} categories")
    if args.dry_run:
        print("  (dry run — no files written)")


if __name__ == "__main__":
    main()
