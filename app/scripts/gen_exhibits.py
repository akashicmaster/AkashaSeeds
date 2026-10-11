#!/usr/bin/env python3
"""Regenerate the shipped editorial exhibition exports ("A Genealogy of Dreams").

The Exhibition Room (app/archives/curation/index.html) links each installment INTO the
scroll/kamishibai viewer, which reads a self-contained JSON under
app/archives/curation/exports/. Those artifacts are normally produced at runtime by
`pres.export publish=<slug>`, but the three editorial exhibits are PRODUCT content
that must ship in the seed — so they are generated here and committed (the
.gitignore negates exactly these slugs). This reproduces them headlessly:

    curation ontology (.ak)  →  authored CSL (curation.new)
      →  curation.project (presentation)  →  pres.export publish=<slug>  ·  scroll + kamishibai

Run:  python app/scripts/gen_exhibits.py
Then: git add -f app/archives/curation/exports/{index,sky-dreamers,print-dreamers,beer-journey}.*.json
"""
import os, sys, re, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

# The three editorial exhibits of the "A Genealogy of Dreams" series:
#   (curation-ontology base name, curation alias, slug, series-listing title)
EXHIBITS = [
    ("sky_dreamers",   "curation:sky-dreamers",   "sky-dreamers",   "The Wish to Fly — Icarus's Wings"),
    ("print_dreamers", "curation:print-dreamers", "print-dreamers", "The Dream of Print"),
    ("beer_journey",   "curation:beer-journey",   "beer-journey",   "Beer — the Beverage that Heals Labor"),
]


def _load_ak(loc, name):
    """Replay a curation-ontology .ak file's def / ln / al / set.add statements."""
    n = 0
    for line in open(os.path.join(ROOT, "app", "ontology", "curation", name + ".ak"), encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r'def\s+"([^"]+)"\s+"(.*)"\s*$', s)
        if m:
            loc("def", name=m.group(1), description=m.group(2), scope="universal"); n += 1; continue
        m = re.match(r'ln\s+(\S+)\s+(\S+)\s+(\S+)\s*$', s)
        if m:
            loc("ln", src=m.group(1), dst=m.group(2), rel=m.group(3), scope="universal"); n += 1; continue
        m = re.match(r'al\s+(\S+)\s+(\S+)\s*$', s)
        if m:
            loc("al", id=m.group(1), alias=m.group(2), scope="universal"); continue
        m = re.match(r'set\.add\s+name="([^"]+)"\s+id="([^"]+)"\s*$', s)
        if m:
            loc("set.add", name=m.group(1), id=m.group(2), scope="universal"); continue
    return n


def main():
    from lib.akasha.api import client
    gw = client.embedded(tempfile.mkdtemp(prefix="akasha_exh_"), "thesaurus08", load_ontology=False)
    k = gw.kernel_client
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for base, _cid, _slug, _title in EXHIBITS:
        print(f"loaded {base}.ak: {_load_ak(loc, base)} statements")
    for base, *_ in EXHIBITS:
        src = open(os.path.join(ROOT, "app", "curations", base + ".csl"), encoding="utf-8").read()
        r = loc("csl.run", script=src)
        print(f"csl.run {base}: {'OK' if not r.get('error') else r.get('error')}")

    ok = True
    for _base, cid, slug, title in EXHIBITS:
        proj = loc("curation.project", id=cid, **{"as": "presentation"}, title=title)
        pres = proj.get("result") or proj
        pid = pres.get("id") or pres.get("presentation_id") or (pres.get("presentation") or {}).get("id")
        if not pid:
            print(f"!! {slug}: project failed: {proj.get('error') or proj}"); ok = False; continue
        for fmt in ("scroll", "kamishibai"):
            ex = loc("pres.export", id=pid, **{"as": fmt}, publish=slug)
            res = ex.get("result") or ex
            st = res.get("status")
            print(f"  {slug} {fmt}: {st}  {res.get('url') or ex.get('error') or ''}")
            ok = ok and st == "published"

    outdir = os.path.join(ROOT, "app", "archives", "curation", "exports")
    print("\nexports:")
    for f in sorted(os.listdir(outdir)) if os.path.isdir(outdir) else []:
        print("  ", f)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
