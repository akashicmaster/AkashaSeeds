#!/usr/bin/env python3
"""
wikidata_smallplates_import.py — tapas / pinchos / finger-food dishes → smallplates_wikidata.ak

A cross-cultural, **multilingual** sweep of Wikidata (CC0) for the small-plate /
finger-food family of dishes — tapas, pinchos (pintxos), antipasti, cicchetti,
meze, petiscos, amuse-bouche, canapés, hors d'œuvre, Häppchen … — emitted as an
Akasha `.ak` catalogue for a drinks_c-sibling C-tier food pack (smallplates_c).

Two things set it apart from app/scripts/wikidata_food_import.py (which pulls the
generic dish skeleton in English only):

  1. **Multilingual labels.** Like app/scripts/wikidata_spirits_import.py, the label
     service is asked for a whole SpaCy-covered priority list (Romance family +
     German + English). A tapa that is labelled only in Spanish/Basque, an
     antipasto only in Italian, a petisco only in Portuguese — all kept, with the
     native spelling recorded verbatim in the description, instead of dropped as a
     bare QID.

  2. **Concept family, resolved by NAME not by hand-typed QID.** Each small-plate
     concept is resolved to its Wikidata item at runtime from its multilingual
     names (anchored to food/dish/course, most-notable match wins), and the
     resolution is printed. A concept that does not resolve is skipped with a
     warning — so a wrong hand-guessed QID can never silently pull garbage (the
     failure mode that made an early spirits run import a politician instead of rum).

Namespaces / atoms (unifies with the base dish/cuisine/ingred vocab if loaded):
    dish:{slug}                       one atom per small-plate dish
    al dish:{slug} dish:wd:{QID}      Wikidata unification alias
    dish:{concept}                    the family concept itself (dish:tapa, dish:antipasto…)
    ln dish:{slug} dish:{concept} sys:is_a          this dish IS-A tapa / meze / …
    ln dish:{slug} cuisine:{c} thesaurus:related    P2012 cuisine (unifies with base)
    ln dish:{slug} ingred:{i} thesaurus:related     P186 made-from, matched to base ingred:*
Sets:
    smallplate:all                    the umbrella category — EVERY dish found;
                                      dish:{concept} is-a dish:smallplate for each type
    smallplate:{concept}              members of each cultural sub-type (smallplate:tapa,
                                      smallplate:finger_food, smallplate:meze, …)
    dish:from:{country_slug}          by country of origin (P495)

Source & license:
    Wikidata — https://www.wikidata.org/  ·  CC0 1.0 (public domain). Attribution retained.

Network: the Wikidata SPARQL endpoint must be reachable (blocked in some CI
sandboxes). Run where outbound HTTPS works. For offline transform tests pass a
local JSON via --input (see _bindings / --dump-cache).

Usage:
    python app/scripts/wikidata_smallplates_import.py --resolve      # just show what each name resolves to
    python app/scripts/wikidata_smallplates_import.py --dry-run      # resolve + count members, write nothing
    python app/scripts/wikidata_smallplates_import.py                # full pull → app/ontology/smallplates_c
    python app/scripts/wikidata_smallplates_import.py --only tapas,pinchos,antipasto
    python app/scripts/wikidata_smallplates_import.py --lang en,es,fr,it,pt,ca
"""
import argparse
import glob
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "AkashaSmallPlatesImport/1.0 (https://akashicarchives.net; ontology import)"

# Anchor classes for name→concept resolution. dish=Q746549 is confirmed (used by
# wikidata_food_import.py); food=Q2095 and course=Q19861951 broaden the net so a
# concept that is a subclass of any of them resolves. Override with --anchors.
DEFAULT_ANCHORS = ["Q746549", "Q2095", "Q19861951"]  # dish · food · course

# The small-plate family. key = concept slug (→ dish:{key} + smallplate:{key} set);
# names = multilingual labels used to RESOLVE the Wikidata concept (no hand QIDs);
# gloss = the atom description for the family concept itself.
SEEDS = {
    "tapa":         (["tapa", "tapas"],
                     "Tapa — a small Spanish savoury dish served as a snack or appetiser."),
    "pincho":       (["pincho", "pinchos", "pintxo", "pintxos"],
                     "Pincho (pintxo) — a Basque/northern-Spanish small snack, often on bread with a skewer."),
    "finger_food":  (["finger food", "fingerfood"],
                     "Finger food — food eaten directly with the hands, in small portions."),
    "hors_doeuvre": ["hors d'oeuvre", "hors d'œuvre", "hors-d'oeuvre", "amuse-gueule"],
    "amuse_bouche": (["amuse-bouche", "amuse bouche"],
                     "Amuse-bouche — a single bite-size hors d'œuvre offered by the kitchen."),
    "canape":       (["canapé", "canape", "canapés", "canapes"],
                     "Canapé — a small decorative finger food on a bread/pastry base."),
    "antipasto":    (["antipasto", "antipasti"],
                     "Antipasto — the traditional first course of an Italian meal, small savoury bites."),
    "cicchetti":    (["cicchetti", "cicchetto", "cichetti"],
                     "Cicchetti — small Venetian snacks or side dishes, the Venetian answer to tapas."),
    "meze":         (["meze", "mezze", "mezes", "mezédes"],
                     "Meze — a selection of small dishes served across the Mediterranean and Near East."),
    "petisco":      (["petiscos", "petisco"],
                     "Petisco — a Portuguese small savoury dish/snack, the Portuguese tapa."),
    "appetizer":    (["appetizer", "appetiser", "starter", "entrée", "entrada", "aperitivo"],
                     "Appetiser — a small first dish that opens a meal."),
    "haeppchen":    (["häppchen", "haeppchen", "fingerfood"],
                     "Häppchen — German bite-size finger food / canapés."),
}
# a couple of entries above are (names, gloss); hors_doeuvre is names-only → default gloss.

# The umbrella category. Every dish found — whatever its cultural type — is collected
# into the smallplate:all set, and each cultural concept (tapa, pincho, finger_food,
# antipasto, meze, …) is linked sys:is_a under dish:smallplate. finger_food is just one
# of the member sub-types (its own smallplate:finger_food set), not the parent — a meze
# or starter is a small plate without necessarily being eaten with the hands. The
# umbrella concept + set are always defined so the top-level grouping exists.
UMBRELLA = "smallplate"
UMBRELLA_GLOSS = (
    "Small plate — a small savoury dish or portion served as a snack, appetiser or shared "
    "bite; the umbrella for tapas, pinchos, finger food, antipasti, meze, canapés and the rest."
)
UMBRELLA_SET = "smallplate:all"


def _seed(v):
    """Normalise a SEEDS value to (names, gloss)."""
    if isinstance(v, tuple):
        return v[0], v[1]
    return v, None


def normalize(name):
    """Label → atom-name component: lowercase, NFD→ASCII, underscores (matches
    wikidata_food_import.normalize so atoms unify with the base dish/ingred vocab)."""
    s = unicodedata.normalize("NFD", name)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[\s\-/,.()\[\]'\"]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:60]


def cuisine_slug(label):
    s = normalize(label)
    return re.sub(r"_(cuisine|food|gastronomy)$", "", s) or normalize(label)


def escape_ak(s):
    return re.sub(r"\s+", " ", (s or "").replace("\\", " ").replace('"', "'")).strip()


def qid_of(uri):
    return (uri or "").rsplit("/", 1)[-1]


def _val(row, key):
    return (row.get(key) or {}).get("value", "")


def _is_qid_label(label):
    return bool(label) and label[0] == "Q" and label[1:].isdigit()


# ── ingred bridge (reuse the ingredient vocab already in ontology/) ───────────
def load_ingred_terms(root_path):
    term2id = {}
    for fp in glob.glob(os.path.join(root_path, "ontology", "**", "*.ak"), recursive=True):
        try:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for atom in re.findall(r'^def\s+"(ingred:[^"]+)"', txt, re.M):
            term2id.setdefault(atom.split(":")[-1].lower(), atom)
        for atom, alias in re.findall(r"^al\s+(ingred:\S+)\s+(\S+)", txt, re.M):
            term2id.setdefault(alias.split(":")[-1].lower(), atom)
    return term2id


def _singular(w):
    w = w.lower()
    if len(w) > 4 and w.endswith("ies"): return w[:-3] + "y"
    if len(w) > 4 and w.endswith("oes"): return w[:-2]
    if len(w) > 4 and w.endswith(("ses", "ches", "shes", "xes")): return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"): return w[:-1]
    return w


def ingred_for(label, ingred_terms):
    for tok in [_singular(t) for t in normalize(label).split("_")[:3]]:
        if tok in ingred_terms:
            return ingred_terms[tok]
    return None


# ── SPARQL ────────────────────────────────────────────────────────────────────
def sparql(query, label, retries=3):
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    req = urllib.request.Request(
        f"{SPARQL_ENDPOINT}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
    for attempt in range(1, retries + 1):
        try:
            print(f"  Querying Wikidata: {label} (try {attempt}) …", file=sys.stderr)
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            rows = data["results"]["bindings"]
            print(f"  → {len(rows)} rows", file=sys.stderr)
            time.sleep(1)
            return rows
        except Exception as e:
            if attempt < retries and any(k in str(e).lower()
                                         for k in ("timed out", "429", "500", "503")):
                time.sleep(2 ** attempt)
                continue
            raise


def _values_terms(names):
    """SPARQL VALUES body for a list of literal terms (accent + lowercase forms)."""
    forms = set()
    for n in names:
        forms.add(n.lower())
        forms.add(unicodedata.normalize("NFD", n).encode("ascii", "ignore").decode().lower())
    return " ".join(f'"{f}"' for f in sorted(forms) if f)


def resolve_concept(names, anchors, langs):
    """Resolve a concept's Wikidata QID from its multilingual names. Returns
    (qid, label) of the most-notable food/dish/course whose label matches, or
    (None, None). Prints the top candidates for transparency."""
    lang_list = ", ".join(f'"{l}"' for l in langs.split(","))
    anchor_vals = " ".join(f"wd:{a}" for a in anchors)
    q = f"""SELECT ?c ?cLabel (MAX(?sl) AS ?n) WHERE {{
  VALUES ?term {{ {_values_terms(names)} }}
  ?c rdfs:label ?l . FILTER( LANG(?l) IN ({lang_list}) && LCASE(STR(?l)) = ?term )
  ?c wdt:P279* ?anc . VALUES ?anc {{ {anchor_vals} }}
  OPTIONAL {{ ?c wikibase:sitelinks ?sl }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{langs}". }}
}} GROUP BY ?c ?cLabel ORDER BY DESC(?n) LIMIT 3"""
    rows = sparql(q, f"resolve {names[0]!r}")
    best = None
    for r in rows:
        qid = qid_of(_val(r, "c"))
        lbl = _val(r, "cLabel")
        n = _val(r, "n") or "0"
        tag = "  ←" if best is None else ""
        print(f"      {qid:>10}  n={n:>4}  {lbl}{tag}", file=sys.stderr)
        if best is None and qid and not _is_qid_label(lbl):
            best = (qid, lbl)
    return best or (None, None)


def _members_query(qid, langs, cap):
    return f"""SELECT DISTINCT ?item ?itemLabel ?countryLabel ?cuisineLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:{qid} .
  OPTIONAL {{ ?item wdt:P495 ?country. }}
  OPTIONAL {{ ?item wdt:P2012 ?cuisine. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{langs}". }}
}} LIMIT {cap}"""


def _ingredients_query(qid, cap):
    return f"""SELECT ?item ?ingLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:{qid} .
  ?item wdt:P186 ?ing .
  ?ing rdfs:label ?ingLabel . FILTER(LANG(?ingLabel)="en")
}} LIMIT {cap}"""


# ── accumulate + emit ─────────────────────────────────────────────────────────
def accumulate(concept, rows, ing_rows, ingred_terms, dishes):
    """Fold a concept's member rows into the shared dish table `dishes`."""
    ings_by_qid = {}
    for r in ing_rows:
        q = qid_of(_val(r, "item"))
        lbl = _val(r, "ingLabel")
        if q and lbl:
            ings_by_qid.setdefault(q, set()).add(lbl)

    n = 0
    for r in rows:
        qid = qid_of(_val(r, "item"))
        label = _val(r, "itemLabel").strip()
        if not label or _is_qid_label(label):
            continue                       # no label in any requested language → skip
        slug = normalize(label)
        if not slug:
            continue
        d = dishes.setdefault(slug, {
            "label": label, "qid": qid, "concepts": set(),
            "country": "", "cuisines": set(), "ingreds": set(),
        })
        d["concepts"].add(concept)
        if not d["qid"]:
            d["qid"] = qid
        country = _val(r, "countryLabel").strip()
        if country and not _is_qid_label(country):
            d["country"] = country
        cuisine = _val(r, "cuisineLabel").strip()
        if cuisine and not _is_qid_label(cuisine):
            d["cuisines"].add(cuisine_slug(cuisine))
        for ing_label in ings_by_qid.get(qid, ()):
            tgt = ingred_for(ing_label, ingred_terms)
            if tgt:
                d["ingreds"].add(tgt)
        n += 1
    return n


def emit(dishes, concept_meta):
    lines = [
        "# Wikidata — tapas / pinchos / finger-food dishes (C-tier). Generated by",
        "# wikidata_smallplates_import.  Source: Wikidata — CC0 1.0 (public domain).",
        "",
        "# ── the small-plate family concepts (smallplate is the umbrella) ──",
    ]
    # the umbrella concept is always defined (it is not a Wikidata seed, so no alias).
    lines.append(f'def "dish:{UMBRELLA}" "{escape_ak(UMBRELLA_GLOSS)}"')
    for key in sorted(concept_meta):
        qid, gloss = concept_meta[key]
        lines.append(f'def "dish:{key}" "{escape_ak(gloss)}"')
        if qid:
            lines.append(f"al dish:{key} dish:wd:{qid}")
        lines.append(f"ln dish:{key} dish:{UMBRELLA} sys:is_a")   # tapa is-a small plate
    lines.append("")
    lines.append("# ── dishes ──")
    for slug in sorted(dishes):
        d = dishes[slug]
        aid = f"dish:{slug}"
        concepts = sorted(d["concepts"])
        desc = (d["label"] + " — a small-plate dish ("
                + "/".join(concepts) + ")"
                + (f" from {d['country']}" if d["country"] else "") + ".")
        lines.append(f'def "{aid}" "{escape_ak(desc)}"')
        if d["qid"]:
            lines.append(f"al {aid} dish:wd:{d['qid']}")
        lines.append(f'set.add name="{UMBRELLA_SET}" id="{aid}"')   # umbrella small-plate set
        for c in concepts:
            lines.append(f"ln {aid} dish:{c} sys:is_a")
            lines.append(f'set.add name="smallplate:{c}" id="{aid}"')   # per-type sub-set
        if d["country"]:
            cs = normalize(d["country"])
            lines.append(f'set.add name="dish:from:{cs}" id="{aid}"')
        for c in sorted(d["cuisines"]):
            lines.append(f"ln {aid} cuisine:{c} thesaurus:related")
        for tgt in sorted(d["ingreds"]):
            lines.append(f"ln {aid} {tgt} thesaurus:related")
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="app/ontology/smallplates_c")
    ap.add_argument("--only", default="", help="comma list of concept slugs (default: all)")
    ap.add_argument("--lang", default="en,es,fr,it,pt,ro,ca,de",
                    help="Wikidata label languages, priority order (SpaCy-covered set)")
    ap.add_argument("--anchors", default=",".join(DEFAULT_ANCHORS),
                    help="comma list of anchor QIDs for name resolution (dish,food,course)")
    ap.add_argument("--cap", type=int, default=800, help="max members per concept")
    ap.add_argument("--resolve", action="store_true", help="only resolve concept names, then exit")
    ap.add_argument("--dry-run", action="store_true", help="resolve + count, write no file")
    args = ap.parse_args(argv[1:])

    wanted = [s.strip() for s in args.only.split(",") if s.strip()] or list(SEEDS)
    anchors = [a.strip() for a in args.anchors.split(",") if a.strip()]
    unknown = [w for w in wanted if w not in SEEDS]
    if unknown:
        print(f"  [!] unknown concept(s): {', '.join(unknown)}", file=sys.stderr)
        wanted = [w for w in wanted if w in SEEDS]

    # 1) resolve each concept name → QID
    resolved = {}
    for key in wanted:
        names, _ = _seed(SEEDS[key])
        qid, lbl = resolve_concept(names, anchors, args.lang)
        if qid:
            resolved[key] = (qid, lbl)
            print(f"  {key:14s} → {qid}  ({lbl})")
        else:
            print(f"  {key:14s} → [!] unresolved — skipped")
    if args.resolve:
        return 0
    if not resolved:
        print("  no concepts resolved; nothing to do.", file=sys.stderr)
        return 1

    ingred_terms = load_ingred_terms(PROJECT_ROOT)
    print(f"[smallplates] ingred bridge targets: {len(ingred_terms)}", file=sys.stderr)

    # 2) pull members + ingredients per concept, fold into one dish table
    dishes, concept_meta = {}, {}
    for key, (qid, lbl) in resolved.items():
        _, gloss = _seed(SEEDS[key])
        concept_meta[key] = (qid, gloss or f"{lbl or key} — a small-plate / finger-food category.")
        rows = sparql(_members_query(qid, args.lang, args.cap), f"{key} members")
        ings = sparql(_ingredients_query(qid, args.cap * 4), f"{key} ingredients")
        n = accumulate(key, rows, ings, ingred_terms, dishes)
        print(f"  {key:14s}: {n} members")

    print(f"\n  distinct small-plate dishes: {len(dishes)}  "
          f"across {len(resolved)} concepts")
    if args.dry_run:
        print("  (dry run — no file written)")
        return 0

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "smallplates_wikidata.ak")
    with open(path, "w", encoding="utf-8") as f:
        f.write(emit(dishes, concept_meta))
    print(f"wrote {path}  ({os.path.getsize(path) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
