#!/usr/bin/env python3
"""
labo_register.py — reorganize the existing thought-experiment laboratories into the canonical Labo
world-model structure (Labo / Hyper Labo Implementation Directive §2, §15 Phase 1).

Each lab in the archives hall becomes a `labo:` bounded research namespace that BINDS (references)
its already-shipped resources — Source Pools, concept fields, societies. Nothing is rewritten or
merged; the labs keep their own provenance and may be observed by multiple Societies (§10). Run it
against a live Cell (like the other source-layer scripts); it is idempotent and binds a resource
only if that resource is actually present on this cell (a lab whose Source Pool has not been imported
yet is still registered, just with an empty SOURCE projection until its data lands).

    python app/scripts/labo_register.py --as <admin_id>

`--as` must be THIS cell's genesis admin id (the universal writes go to the shared nucleus, so a
public lab's shell is guest-readable — as with the source-layer scripts).
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

# Each existing lab → its canonical Labo binding. `pool`/`concept`/`society` are bound only if the
# referenced atom exists on this cell (so a not-yet-imported corpus never blocks registration).
LABS = [
    {"name": "blvh", "about": "British Library Visual Hypothesis Corpus (image evidence, CORPUS)",
     "scope": "public", "pool": "source:pool:bl_book_images:bootstrap_v1", "concept": "blvh:root"},
    {"name": "mobility", "about": "EU mobility public-opinion research (CORPUS)",
     "scope": "public", "pool": "source:pool:mobility:eu_travel_survey_2014:v1_1", "concept": "mob:root"},
    {"name": "stylometry", "about": "Stylometry — one text's composition seams (single-lens genealogy)",
     "scope": "public", "concept": "sty:root"},
    {"name": "genealogy", "about": "Genealogy — where traditions come from (multi-lens)",
     "scope": "public", "concept": "gen:root"},
    {"name": "consensus", "about": "Form-a-Consensus deliberation (public feedback)",
     "scope": "public", "concept": "delib:root"},
    {"name": "concept", "about": "Concept Laboratory — thought experiments about concept formation (AUTHORED)",
     "scope": "public", "concept": "clab:root"},
    {"name": "visual_curation", "about": "Visual Curation Laboratory — machine observation of museum artworks (CORPUS)",
     "scope": "public", "pool": "source:pool:cma:visual_curation:v1"},
]


def main():
    ap = argparse.ArgumentParser(description="Register the existing labs as canonical Labos.")
    ap.add_argument("--as", dest="as_id", default="admin", help="THIS cell's genesis admin id")
    ap.add_argument("--base", default=None, help="daemon data dir (default AKASHA_DATA_DIR or ./data)")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print(f"[!] No Cell daemon at {base}. Start one:  python akasha.py --serve", file=sys.stderr)
        sys.exit(2)
    gw = client.connect(base)

    def d(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": args.as_id, "data": data}, "id": "m"}, "local")
        return r["result"] if isinstance(r, dict) and "result" in r else \
            {"__error__": (r or {}).get("error") if isinstance(r, dict) else r}

    def exists(atom_id):
        return bool((d("read", {"id": atom_id}) or {}).get("content"))

    for lab in LABS:
        d("labo.new", {"name": lab["name"], "about": lab["about"], "scope": lab["scope"]})
        bind = {"name": lab["name"]}
        bound = []
        for kind in ("pool", "concept", "society"):
            ref = lab.get(kind)
            if ref and exists(ref):
                bind[kind] = ref
                bound.append(f"{kind}={ref}")
        if len(bind) > 1:
            d("labo.bind", dict(bind, origin="registered"))
        print(f"  labo:{lab['name']:<12} registered" + (f"  ⟵ {'  '.join(bound)}" if bound else "  (no resources on this cell yet)"))

    print(f"\n  {len(LABS)} labs registered as canonical Labos. Open one:  labo.info name=<lab>")
    print(f"  Compose a Hyper Labo:  labo.hyper.new name=<h> labos=<a>,<b>\n")
    gw.close()


if __name__ == "__main__":
    main()
