#!/usr/bin/env python3
"""
wikidata_bakery_import.py — お菓子 (sweets) & パン (bread) dishes → sweets_bread_wikidata.ak

The confectionery/bread sibling of app/scripts/wikidata_smallplates_import.py: a
cross-cultural, **multilingual** Wikidata (CC0) sweep of two food families —

    sweet  (お菓子)  desserts, cakes, cookies, pastries, chocolate, pudding,
                     ice cream, candy, tarts …
    bread  (パン)    breads: flatbread, buns/rolls, sweet bread/viennoiserie,
                     sourdough, rye, quick bread …

emitted as an Akasha `.ak` catalogue for a C-tier food pack. Same design as the
smallplates importer:

  1. **Multilingual labels** (SpaCy-covered Romance family + German + English) —
     a Kuchen labelled only in German, a bolo only in Portuguese, a gâteau only
     in French are all kept, native spelling verbatim in the description.
  2. **Concepts resolved by NAME, not hand-typed QID.** Each family umbrella and
     each sub-type is resolved to its Wikidata item at runtime from its
     multilingual names (anchored to food/dish/course), printed, and skipped if
     it does not resolve — a wrong QID can never silently pull garbage.

Namespaces / atoms (unify with the base dish/cuisine/ingred vocab if loaded):
    dish:{slug}                       one atom per sweet / bread
    al dish:{slug} dish:wd:{QID}      Wikidata unification alias
    dish:sweet · dish:bread           the two family umbrellas
    dish:{type}                       each sub-type (dish:cake, dish:flatbread…)
    ln dish:{type} dish:{family} sys:is_a           cake is-a sweet, flatbread is-a bread
    ln dish:{slug} dish:{type}  sys:is_a            this item IS-A cake / sourdough / …
    ln dish:{slug} cuisine:{c}  thesaurus:related   P2012 cuisine (unifies with base)
    ln dish:{slug} ingred:{i}   thesaurus:related   P186 made-from, matched to base ingred:*
Sets (one namespace per family):
    sweet:all · bread:all             the umbrella category — EVERY item of the family
    sweet:{type} · bread:{type}       each sub-type (sweet:cake, bread:sourdough…)
    dish:from:{country_slug}          by country of origin (P495)

Source & license:
    Wikidata — https://www.wikidata.org/  ·  CC0 1.0 (public domain). Attribution retained.

Network: the Wikidata SPARQL endpoint must be reachable (blocked in some CI
sandboxes). Run where outbound HTTPS works.

Usage:
    python app/scripts/wikidata_bakery_import.py --resolve        # show what each name resolves to
    python app/scripts/wikidata_bakery_import.py --dry-run        # resolve + count, write nothing
    python app/scripts/wikidata_bakery_import.py                  # full pull → app/ontology/sweets_bread_c
    python app/scripts/wikidata_bakery_import.py --only bread      # one whole family
    python app/scripts/wikidata_bakery_import.py --only cake,cookie,flatbread
    python app/scripts/wikidata_bakery_import.py --lang en,es,fr,it,pt,de
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
USER_AGENT = "AkashaBakeryImport/1.0 (https://akashicarchives.net; ontology import)"

# Anchor classes for name→concept resolution. dish=Q746549 is confirmed (used by
# wikidata_food_import.py); food=Q2095 and course=Q19861951 broaden the net. Override
# with --anchors. A concept that resolves to nothing is skipped (visible under --resolve).
DEFAULT_ANCHORS = ["Q746549", "Q2095", "Q19861951"]  # dish · food · course

# Two families. Each: gloss for the umbrella concept (dish:{family}); `names` to
# RESOLVE the umbrella's own Wikidata concept (so its generic members are pulled too);
# and `seeds` = the sub-types (slug → (multilingual names, gloss)). Sets live in the
# family's own namespace (sweet:* / bread:*).
FAMILIES = {
    "sweet": {
        "gloss": "Confectionery / sweets (お菓子) — sweet foods: desserts, cakes, "
                 "cookies, pastries, chocolate and other treats.",
        "names": ["confectionery", "confection", "sweets", "sweet", "süßware", "süßwaren",
                  "süßigkeit", "dulce", "dulces", "golosina", "dolciumi", "dolciume",
                  "confiserie", "confeitaria", "doçaria"],
        "seeds": {
            "dessert":   (["dessert", "postre", "dolce", "sobremesa", "nachtisch"],
                          "Dessert — a sweet course served at the end of a meal."),
            "cake":      (["cake", "gâteau", "gateau", "torta", "tarta", "bolo", "kuchen", "torte"],
                          "Cake — a sweet baked dessert of flour, sugar and eggs."),
            "cookie":    (["cookie", "biscuit", "galleta", "biscotto", "keks", "plätzchen", "bolacha"],
                          "Cookie / biscuit — a small sweet baked treat."),
            "pastry":    (["pastry", "pâtisserie", "patisserie", "gebäck", "pasticceria",
                           "repostería", "pastel"],
                          "Pastry — a sweet baked good of enriched dough."),
            "chocolate": (["chocolate", "cioccolato", "schokolade", "chocolat"],
                          "Chocolate — a confection made from cacao."),
            "pudding":   (["pudding", "budino", "flan"],
                          "Pudding — a soft sweet dessert."),
            "ice_cream": (["ice cream", "gelato", "helado", "eiscreme", "glace", "sorvete",
                           "speiseeis"],
                          "Ice cream — a frozen sweet dessert."),
            "candy":     (["candy", "caramelo", "bonbon", "caramella", "rebuçado"],
                          "Candy / sweet — a small sugar confection."),
            "tart":      (["tart", "tarte", "crostata", "törtchen"],
                          "Tart — an open sweet pastry with a filling."),
        },
    },
    "bread": {
        "gloss": "Bread (パン) — a staple baked food of flour and water; the umbrella "
                 "for its many types.",
        "names": ["bread", "pan", "pane", "pão", "brot", "pain"],
        "seeds": {
            "flatbread":   (["flatbread", "pane piatto", "fladenbrot", "pain plat"],
                            "Flatbread — a thin bread, often unleavened."),
            "bun":         (["bun", "bread roll", "roll", "panecillo", "brötchen",
                             "petit pain", "panino", "bollo"],
                            "Bun / roll — a small individual bread."),
            "sweet_bread": (["sweet bread", "sweet roll", "viennoiserie", "brioche",
                             "hefegebäck"],
                            "Sweet bread / viennoiserie — enriched sweet bread (brioche, etc.)."),
            "sourdough":   (["sourdough", "sauerteigbrot", "pan de masa madre"],
                            "Sourdough — bread leavened by natural fermentation."),
            "rye_bread":   (["rye bread", "roggenbrot", "pane di segale", "pan de centeno"],
                            "Rye bread — bread made with rye flour."),
            "quick_bread": (["quick bread"],
                            "Quick bread — bread leavened chemically rather than with yeast."),
        },
    },
}


def build_concept_index():
    """Return (concept_meta_specs, concept2family). concept_meta_specs maps a concept
    slug → (names, gloss, is_umbrella). concept2family maps slug → family key."""
    specs, c2f = {}, {}
    for fam, meta in FAMILIES.items():
        specs[fam] = (meta["names"], meta["gloss"], True)   # the umbrella itself
        c2f[fam] = fam
        for slug, (names, gloss) in meta["seeds"].items():
            specs[slug] = (names, gloss, False)
            c2f[slug] = fam
    return specs, c2f


# ── helpers (shared with the food/smallplates importers) ─────────────────────
def normalize(name):
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
    forms = set()
    for n in names:
        forms.add(n.lower())
        forms.add(unicodedata.normalize("NFD", n).encode("ascii", "ignore").decode().lower())
    return " ".join(f'"{f}"' for f in sorted(forms) if f)


def resolve_concept(names, anchors, langs):
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
            continue
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


def emit(dishes, concept_meta, concept2family):
    lines = [
        "# Wikidata — お菓子 (sweets) & パン (bread) dishes (C-tier). Generated by",
        "# wikidata_bakery_import.  Source: Wikidata — CC0 1.0 (public domain).",
        "",
        "# ── the two family umbrellas and their sub-types ──",
    ]
    for fam in sorted(FAMILIES):
        # umbrella concept — always defined; keeps its Wikidata alias if it resolved.
        um_qid = concept_meta.get(fam, (None, None))[0]
        lines.append(f'def "dish:{fam}" "{escape_ak(FAMILIES[fam]["gloss"])}"')
        if um_qid:
            lines.append(f"al dish:{fam} dish:wd:{um_qid}")
        for slug in sorted(FAMILIES[fam]["seeds"]):
            if slug not in concept_meta:
                continue
            qid, gloss = concept_meta[slug]
            lines.append(f'def "dish:{slug}" "{escape_ak(gloss)}"')
            if qid:
                lines.append(f"al dish:{slug} dish:wd:{qid}")
            lines.append(f"ln dish:{slug} dish:{fam} sys:is_a")   # cake is-a sweet
        lines.append("")

    lines.append("# ── items ──")
    for slug in sorted(dishes):
        d = dishes[slug]
        aid = f"dish:{slug}"
        concepts = sorted(d["concepts"])
        desc = (d["label"] + " — " + "/".join(concepts)
                + (f" from {d['country']}" if d["country"] else "") + ".")
        lines.append(f'def "{aid}" "{escape_ak(desc)}"')
        if d["qid"]:
            lines.append(f"al {aid} dish:wd:{d['qid']}")
        fam_seen = set()
        for c in concepts:
            fam = concept2family.get(c)
            if fam and fam not in fam_seen:                 # umbrella :all set, once per family
                lines.append(f'set.add name="{fam}:all" id="{aid}"')
                fam_seen.add(fam)
            lines.append(f"ln {aid} dish:{c} sys:is_a")
            if fam and c != fam:                            # per-type sub-set
                lines.append(f'set.add name="{fam}:{c}" id="{aid}"')
        if d["country"]:
            cs = normalize(d["country"])
            lines.append(f'set.add name="dish:from:{cs}" id="{aid}"')
        for c in sorted(d["cuisines"]):
            lines.append(f"ln {aid} cuisine:{c} thesaurus:related")
        for tgt in sorted(d["ingreds"]):
            lines.append(f"ln {aid} {tgt} thesaurus:related")
    return "\n".join(lines) + "\n"


def _expand_only(tokens, specs):
    """--only tokens may be family keys (expand to umbrella + all its seeds) or
    individual concept slugs."""
    wanted = []
    for t in tokens:
        if t in FAMILIES:
            wanted.append(t)
            wanted += list(FAMILIES[t]["seeds"])
        elif t in specs:
            wanted.append(t)
        else:
            print(f"  [!] unknown family/concept: {t}", file=sys.stderr)
    return wanted


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="app/ontology/sweets_bread_c")
    ap.add_argument("--only", default="", help="comma list of families (sweet,bread) or concept slugs")
    ap.add_argument("--lang", default="en,es,fr,it,pt,ro,ca,de",
                    help="Wikidata label languages, priority order (SpaCy-covered set)")
    ap.add_argument("--anchors", default=",".join(DEFAULT_ANCHORS),
                    help="comma list of anchor QIDs for name resolution (dish,food,course)")
    ap.add_argument("--cap", type=int, default=800, help="max members per concept")
    ap.add_argument("--resolve", action="store_true", help="only resolve concept names, then exit")
    ap.add_argument("--dry-run", action="store_true", help="resolve + count, write no file")
    args = ap.parse_args(argv[1:])

    specs, concept2family = build_concept_index()
    anchors = [a.strip() for a in args.anchors.split(",") if a.strip()]
    tokens = [s.strip() for s in args.only.split(",") if s.strip()]
    wanted = _expand_only(tokens, specs) if tokens else list(specs)
    # keep declaration order (umbrellas first per family) and dedup
    seen = set()
    wanted = [w for w in wanted if not (w in seen or seen.add(w))]

    # 1) resolve each concept name → QID
    resolved = {}
    for key in wanted:
        names, _gloss, _is_um = specs[key]
        qid, lbl = resolve_concept(names, anchors, args.lang)
        fam = concept2family[key]
        kind = "umbrella" if key == fam else f"→{fam}"
        if qid:
            resolved[key] = (qid, lbl)
            print(f"  {key:14s} [{kind:9s}] → {qid}  ({lbl})")
        else:
            print(f"  {key:14s} [{kind:9s}] → [!] unresolved — skipped")
    if args.resolve:
        return 0
    if not resolved:
        print("  no concepts resolved; nothing to do.", file=sys.stderr)
        return 1

    ingred_terms = load_ingred_terms(PROJECT_ROOT)
    print(f"[bakery] ingred bridge targets: {len(ingred_terms)}", file=sys.stderr)

    # 2) pull members + ingredients per concept, fold into one dish table
    dishes, concept_meta = {}, {}
    for key, (qid, lbl) in resolved.items():
        _names, gloss, _is_um = specs[key]
        concept_meta[key] = (qid, gloss)
        rows = sparql(_members_query(qid, args.lang, args.cap), f"{key} members")
        ings = sparql(_ingredients_query(qid, args.cap * 4), f"{key} ingredients")
        n = accumulate(key, rows, ings, ingred_terms, dishes)
        print(f"  {key:14s}: {n} members")

    # per-family tally
    fam_counts = {}
    for d in dishes.values():
        for c in d["concepts"]:
            fam_counts.setdefault(concept2family[c], set()).add(d["label"])
    for fam in sorted(fam_counts):
        print(f"  {fam}: {len(fam_counts[fam])} distinct items")
    print(f"\n  distinct items total: {len(dishes)}")
    if args.dry_run:
        print("  (dry run — no file written)")
        return 0

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "sweets_bread_wikidata.ak")
    with open(path, "w", encoding="utf-8") as f:
        f.write(emit(dishes, concept_meta, concept2family))
    print(f"wrote {path}  ({os.path.getsize(path) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
