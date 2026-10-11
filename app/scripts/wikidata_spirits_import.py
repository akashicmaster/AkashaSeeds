#!/usr/bin/env python3
"""
wikidata_spirits_import.py — Wikidata whisky / rum / tequila → spirits_wikidata.ak (C-tier).

Queries Wikidata (CC0) for the world's whisky, rum and tequila **brands** and
**distilleries**, and emits an Akasha `.ak` catalogue for the drinks_c C-tier pack:
one atom per brand/distillery, linked to its spirit type (sys:is_a), producer, and
grouped by country. Complements the A-tier whiskey/spirits vocabulary in app/ontology/wine/.

Atom IDs (ns ∈ whiskey / rum / tequila):
    <ns>:<ns>                     root concept (whiskey:whiskey exists; rum/tequila defined here)
    <ns>:brand:{slug}            a brand/product  → sys:is_a <ns>:<ns>
    <ns>:distillery:{slug}       a distillery/producer → sys:is_a <ns>:<ns>
    <ns>:wd:{QID}                Wikidata alias for either
Links / sets:
    <ns>:brand:{b} <ns>:distillery:{d} <ns>:made_by     (when the producer is known)
    set <ns>:brands · <ns>:distilleries · <ns>:from:{country_slug}

Source & license:
    Wikidata — https://www.wikidata.org/  ·  CC0 1.0 (public domain). Attribution retained.

Network note: the Wikidata SPARQL endpoint must be reachable (it is blocked in some CI
sandboxes). Run this where outbound HTTPS works. For offline transform testing, pass a
local JSON via --input (a dict {spirit: [sparql-binding, …]}).

Usage:
    python app/scripts/wikidata_spirits_import.py                    # query + write
    python app/scripts/wikidata_spirits_import.py --out app/ontology/drinks_c
    python app/scripts/wikidata_spirits_import.py --only whiskey,rum
    python app/scripts/wikidata_spirits_import.py --input bindings.json --dry-run
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "AkashaSpiritsImport/1.0 (https://akashicarchives.net; ontology import)"

# ns → (root gloss, spirit-type QID, distillery-type QID or None)
# QIDs verified: whisky=Q281, rum=Q83376, tequila=Q122195, whisky distillery=Q10373548.
# (The first cut used Q4593/Q13094 — those are Rajiv Gandhi and the mineral diaboleite,
# which is why rum/tequila returned 0 rows.)
SPIRITS = {
    "whiskey":  ("Whisky — grain spirit, cask-aged.", "Q281",    "Q10373548"),
    "rum":      ("Rum — spirit distilled from sugarcane.", "Q83376",  None),
    "tequila":  ("Tequila — agave spirit from Mexico.", "Q122195", None),
}

# Brands: a UNION rather than an unbounded `P31/P279*` (which times out on Wikidata
# for broad drink classes — it returned 0 rum/tequila on the first run). Catch three
# ways: a direct instance of the spirit, an instance of a one-level subtype, and a
# brand/product whose product (P1056) is the spirit. With optional country of origin
# (P495) and manufacturer (P176). The label service asks for {lang} — a priority list
# of the languages within SpaCy's coverage for this food/drink data (Romance family +
# German + English, default below). Many spirits are labelled only in their native
# language; en-only labels drop them (the label returns as a bare QID and we skip it),
# and the native spelling is worth keeping (kept verbatim in the description).
_BRAND_Q = """SELECT DISTINCT ?item ?itemLabel ?countryLabel ?makerLabel WHERE {{
  {{ ?item wdt:P31 wd:{type_qid}. }}
  UNION {{ ?item wdt:P31 ?sub. ?sub wdt:P279 wd:{type_qid}. }}
  UNION {{ ?item wdt:P1056 wd:{type_qid}. }}
  OPTIONAL {{ ?item wdt:P495 ?country. }}
  OPTIONAL {{ ?item wdt:P176 ?maker. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}". }}
}} LIMIT 6000"""

# Distilleries: instance of the distillery type, with optional country (P17).
_DISTILLERY_Q = """SELECT ?item ?itemLabel ?countryLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:{dist_qid} .
  OPTIONAL {{ ?item wdt:P17 ?country. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}". }}
}} LIMIT 5000"""


def slug(s):
    s = (s or "").lower()
    s = re.sub(r"[&/]", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "x"


def esc(s):
    return re.sub(r"\s+", " ", (s or "").replace('"', "'")).strip()


def _qid(binding_val):
    """'.../entity/Q123' → 'Q123'."""
    v = binding_val or ""
    return v.rsplit("/", 1)[-1] if v else ""


def sparql(query, label):
    url = f"{SPARQL_ENDPOINT}?{urllib.parse.urlencode({'query': query, 'format': 'json'})}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/sparql-results+json"})
    print(f"  Querying Wikidata: {label} …", file=sys.stderr)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    b = data["results"]["bindings"]
    print(f"  → {len(b)} rows", file=sys.stderr)
    time.sleep(1)
    return b


def _val(row, key):
    return (row.get(key) or {}).get("value", "")


def build(ns, gloss, brand_rows, dist_rows):
    """Return (concept_lines, body_lines, n_brands, n_dist, countries)."""
    concept = [f'def "{ns}:{ns}" "{esc(gloss)}"']
    body, seen, countries = [], set(), set()
    dist_slugs = set()

    # distilleries first (so brands can link to them)
    n_dist = 0
    for row in dist_rows:
        qid = _qid(_val(row, "item"))
        label = _val(row, "itemLabel").strip()
        if not label or label == qid:
            continue
        sl = slug(label)
        aid = f"{ns}:distillery:{sl}"
        if aid in seen:
            continue
        seen.add(aid); dist_slugs.add(sl)
        country = _val(row, "countryLabel").strip()
        desc = f"{label} — a {ns} distillery" + (f" in {country}" if country else "") + "."
        body.append(f'def "{aid}" "{esc(desc)}"')
        if qid:
            body.append(f"al {aid} {ns}:wd:{qid}")
        body.append(f"ln {aid} {ns}:{ns} sys:is_a")
        body.append(f'set.add name="{ns}:distilleries" id="{aid}"')
        if country:
            cs = slug(country); countries.add((cs, country))
            body.append(f'set.add name="{ns}:from:{cs}" id="{aid}"')
        n_dist += 1

    n_brands = 0
    for row in brand_rows:
        qid = _qid(_val(row, "item"))
        label = _val(row, "itemLabel").strip()
        if not label or label == qid:
            continue
        sl = slug(label)
        aid = f"{ns}:brand:{sl}"
        if aid in seen:
            continue
        seen.add(aid)
        country = _val(row, "countryLabel").strip()
        maker = _val(row, "makerLabel").strip()
        desc = (f"{label} — a {ns} brand" + (f" from {country}" if country else "")
                + (f", made by {maker}" if maker else "") + ".")
        body.append(f'def "{aid}" "{esc(desc)}"')
        if qid:
            body.append(f"al {aid} {ns}:wd:{qid}")
        body.append(f"ln {aid} {ns}:{ns} sys:is_a")
        body.append(f'set.add name="{ns}:brands" id="{aid}"')
        if country:
            cs = slug(country); countries.add((cs, country))
            body.append(f'set.add name="{ns}:from:{cs}" id="{aid}"')
        if maker and slug(maker) in dist_slugs:
            body.append(f"ln {aid} {ns}:distillery:{slug(maker)} {ns}:made_by")
        n_brands += 1

    return concept, body, n_brands, n_dist, sorted(countries)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="app/ontology/drinks_c")
    ap.add_argument("--only", default="", help="comma list: whiskey,rum,tequila (default all)")
    ap.add_argument("--lang", default="en,es,fr,it,pt,ro,ca,de",
                    help="Wikidata label languages, priority order. Default is the SpaCy-"
                         "covered set for food/drink data — Romance family (es/fr/it/pt/ro/"
                         "ca) + German + English — so native-language-only labels are kept "
                         "(recorded in their original spelling) instead of dropped.")
    ap.add_argument("--input", help="local JSON {spirit:{brands:[...],distilleries:[...]}} (offline)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv[1:])

    wanted = [s.strip() for s in args.only.split(",") if s.strip()] or list(SPIRITS)
    offline = json.load(open(args.input, encoding="utf-8")) if args.input else None

    concepts, bodies, stats = [], [], []
    for ns in wanted:
        gloss, type_qid, dist_qid = SPIRITS[ns]
        if offline is not None:
            brands = offline.get(ns, {}).get("brands", [])
            dists = offline.get(ns, {}).get("distilleries", [])
        else:
            brands = sparql(_BRAND_Q.format(type_qid=type_qid, lang=args.lang), f"{ns} brands")
            dists = sparql(_DISTILLERY_Q.format(dist_qid=dist_qid, lang=args.lang),
                           f"{ns} distilleries") if dist_qid else []
        c, b, nb, nd, countries = build(ns, gloss, brands, dists)
        concepts += c; bodies += ["", f"# ── {ns} ──"] + b
        stats.append((ns, nb, nd, len(countries)))

    lines = [
        "# Wikidata — whisky / rum / tequila brands & distilleries (C-tier). Generated by",
        "# wikidata_spirits_import.  Source: Wikidata — CC0 1.0 (public domain).",
        "",
    ] + concepts + bodies
    for ns, nb, nd, nc in stats:
        print(f"{ns}: brands={nb}  distilleries={nd}  countries={nc}")
    if args.dry_run:
        print("\n".join(lines[:22]))
        return 0
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "spirits_wikidata.ak")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {path}  ({os.path.getsize(path)//1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
