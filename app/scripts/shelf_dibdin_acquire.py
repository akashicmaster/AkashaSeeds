#!/usr/bin/env python3
"""
shelf_dibdin_acquire.py — acquire The Library Companion (Dibdin, 1824) for The Thinker's Shelf.

Implements `docs/for-llm/thinkers-shelf-data-acquisition.md`: A (searchable OCR text) / B (page
images, BY REFERENCE — never downloaded as corpus) / C (bibliographic record, acquired
independently, never derived from A) with the anchoring rule

    fragment → edition → printed page → source URI → OCR span → scan reference

Nothing is hard-coded to an identifier: `locate` searches, `probe` reads the host metadata,
`titlepage` fetches ONE leaf image for human/visual verification of the printing, and only then
does `fetch` pull the OCR text + leaf↔printed-page map. `emit` joins a hand-curated SELECTION
file against the fetched surfaces and generates the passage JSON + the `.ak` pack — the passage
`text` is sliced verbatim out of the page's OCR text (span located by quoted start/end snippets),
so `text` == OCR at `ocr_span` BY CONSTRUCTION (no silent repair possible).

    python app/scripts/shelf_dibdin_acquire.py locate
    python app/scripts/shelf_dibdin_acquire.py probe --id <identifier>
    python app/scripts/shelf_dibdin_acquire.py titlepage --id <identifier> --leaf 5
    python app/scripts/shelf_dibdin_acquire.py fetch --id <identifier>
    python app/scripts/shelf_dibdin_acquire.py pagemap --id <identifier>
    python app/scripts/shelf_dibdin_acquire.py pagetext --id <identifier> --leaf 12
    python app/scripts/shelf_dibdin_acquire.py emit --id <identifier> --selection shelf_data/ep1_selection.json

Staging: shelf_data/<identifier>/ (gitignored). Output: app/ontology/shelf_dibdin/ (the pack).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = os.path.join(ROOT, "shelf_data")
PACK_DIR = os.path.join(ROOT, "app", "ontology", "shelf_dibdin")

IA_SEARCH = ("https://archive.org/advancedsearch.php?q="
             + urllib.parse.quote('title:"library companion" AND creator:"Dibdin"')
             + "&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=year&fl%5B%5D=creator"
               "&fl%5B%5D=publicdate&rows=50&output=json")
OL_SEARCH = "https://openlibrary.org/search.json?q=library+companion+dibdin&limit=20"


def get(url, timeout=120, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "akasha-shelf-acquire/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", errors="replace")


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode, **({} if isinstance(data, bytes) else {"encoding": "utf-8"})) as f:
        f.write(data)
    return path


def sha1_of(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ── locate / probe — find the edition, do not guess it ───────────────────────────────────────────
def cmd_locate(_args):
    print("[IA] " + IA_SEARCH)
    docs = json.loads(get(IA_SEARCH)).get("response", {}).get("docs", [])
    for d in sorted(docs, key=lambda x: str(x.get("year", ""))):
        print("  %-45s year=%-6s %s" % (d.get("identifier"), d.get("year"),
                                        str(d.get("title"))[:70]))
    print("\n[OL] " + OL_SEARCH)
    ol = json.loads(get(OL_SEARCH))
    for d in ol.get("docs", []):
        print("  %-25s %-9s eds=%-3s %s" % (d.get("key"), d.get("first_publish_year"),
                                            d.get("edition_count"), str(d.get("title"))[:60]))
    print("\nNext: probe each 1824 candidate, then verify the TITLE PAGE (titlepage --leaf N).")


def cmd_probe(args):
    url = "https://archive.org/metadata/" + args.id
    meta = json.loads(get(url))
    save(os.path.join(STAGE, args.id, "ia_metadata.json"), json.dumps(meta, indent=2))
    m = meta.get("metadata", {})
    print("identifier : %s" % m.get("identifier"))
    for k in ("title", "creator", "date", "year", "publisher", "volume", "language",
              "possible-copyright-status", "licenseurl", "rights", "scanner", "sponsor",
              "contributor", "source", "external-identifier"):
        if m.get(k):
            print("%-11s: %s" % (k[:11], m[k]))
    print("server     : https://%s%s" % (meta.get("server"), meta.get("dir")))
    print("\nfiles of interest (name · sha1 · size):")
    for f in meta.get("files", []):
        n = f.get("name", "")
        if re.search(r"(_djvu\.txt|_djvu\.xml|_scandata\.xml|_meta\.xml|_jp2\.zip|_page_numbers\.json)$", n):
            print("  %-55s %s  %s" % (n, f.get("sha1", "-")[:12], f.get("size", "-")))
    print("\ntitle-page check: usually leaf 3–9 —")
    print("  python app/scripts/shelf_dibdin_acquire.py titlepage --id %s --leaf 5" % args.id)


def cmd_titlepage(args):
    # ONE leaf image, fetched only to verify the printing against the title page (§2.1).
    url = "https://archive.org/download/%s/page/n%d.jpg" % (args.id, args.leaf)
    out = os.path.join(STAGE, args.id, "titlepage_n%d.jpg" % args.leaf)
    save(out, get(url, binary=True))
    print("saved %s  (open/Read it and verify title · publisher · year against the catalogue)" % out)


# ── fetch — A + the leaf↔page map; B stays a reference ───────────────────────────────────────────
def _pick(meta, suffix):
    for f in meta.get("files", []):
        if f.get("name", "").endswith(suffix):
            return f
    return None


def cmd_fetch(args):
    meta = json.loads(open(os.path.join(STAGE, args.id, "ia_metadata.json"), encoding="utf-8").read())
    # archive.org/download/ 302s to a rotating datanode (sometimes *.eu.archive.org, outside the
    # egress allowlist) — fetch from the item's primary server directly; record the stable
    # /download/ URL as the reference.
    servers = [s for s in (meta.get("server"), meta.get("d1"), meta.get("d2")) if s]
    artifacts = []
    for suffix in ("_djvu.txt", "_djvu.xml", "_scandata.xml", "_meta.xml", "_page_numbers.json"):
        f = _pick(meta, suffix)
        if not f:
            print("  [!] no %s in item" % suffix)
            continue
        url = "https://%s%s/%s" % (servers[0], meta.get("dir", ""), urllib.parse.quote(f["name"]))
        out = os.path.join(STAGE, args.id, f["name"])
        print("  fetch %s (%s bytes)" % (f["name"], f.get("size", "?")))
        save(out, get(url, binary=True))
        got = sha1_of(out)
        ok = (got == f.get("sha1"))
        print("    sha1 host=%s local=%s %s" % (f.get("sha1", "-")[:12], got[:12],
                                                "OK" if ok else "MISMATCH"))
        artifacts.append({"file": f["name"], "sha1_host": f.get("sha1"), "sha1_local": got,
                          "md5_host": f.get("md5"), "size": f.get("size"), "verified": ok,
                          "url": "https://archive.org/download/%s/%s"
                                 % (args.id, urllib.parse.quote(f["name"]))})
    jp2 = _pick(meta, "_jp2.zip")
    if jp2:
        print("  images: REFERENCED, not fetched → %s (sha1 %s)" % (jp2["name"], jp2.get("sha1", "-")[:12]))
        artifacts.append({"file": jp2["name"], "sha1_host": jp2.get("sha1"),
                          "size": jp2.get("size"), "referenced_only": True})
    save(os.path.join(STAGE, args.id, "artifacts.json"),
         json.dumps({"retrieved": date.today().isoformat(), "artifacts": artifacts}, indent=2))
    print("  artifact hashes recorded → shelf_data/%s/artifacts.json" % args.id)


# ── page surfaces — leaf↔printed-page map + per-page OCR text ────────────────────────────────────
def load_pagemap(item_dir):
    """leaf → printed page number, from scandata.xml or page_numbers.json (printed page wins;
    the leaf is kept beside it)."""
    pj = next((os.path.join(item_dir, n) for n in os.listdir(item_dir)
               if n.endswith("_page_numbers.json")), None)
    path = next((os.path.join(item_dir, n) for n in os.listdir(item_dir)
                 if n.endswith("_scandata.xml")), None)
    if pj and not path:
        d = json.load(open(pj, encoding="utf-8"))
        return {int(p["leafNum"]): (p.get("pageNumber") or None) for p in d.get("pages", [])}
    if not path:
        raise SystemExit("no _scandata.xml / _page_numbers.json fetched")
    root = ET.parse(path).getroot()
    ns = {"s": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else None
    pages = root.iter("{%s}page" % ns["s"]) if ns else root.iter("page")
    out = {}
    for p in pages:
        leaf = p.get("leafNum")
        num = None
        for child in p.iter():
            tag = child.tag.split("}")[-1]
            if tag == "pageNumber" and (child.text or "").strip():
                num = child.text.strip()
        if leaf is not None:
            out[int(leaf)] = num
    return out


def render_djvu_xml_pages(path):
    """Per-leaf OCR text derived from *_djvu.xml by ONE deterministic rule (recorded in the
    anchor as `ocr_render`): WORDs of a LINE joined by a single space, LINEs joined by '\\n'.
    Streamed with iterparse — the 30 MB XML is never held whole."""
    pages, lines, words = [], [], []
    for ev, el in ET.iterparse(path, events=("start", "end")):
        tag = el.tag.split("}")[-1].upper()
        if ev == "end" and tag == "WORD":
            words.append(el.text or "")
        elif ev == "end" and tag == "LINE":
            lines.append(" ".join(words))
            words = []
        elif ev == "end" and tag == "OBJECT":
            pages.append("\n".join(lines))
            lines, words = [], []
            el.clear()
    return pages


OCR_RENDER_RULE = "djvu-xml: WORDs joined by ' ', LINEs by '\\n', per OBJECT (leaf order)"


def load_pagetexts(item_dir):
    """Per-leaf OCR text. Older IA items separate *_djvu.txt leaves with form-feed; current
    derivations carry no separator, so the per-page surface comes from *_djvu.xml instead."""
    path = next((os.path.join(item_dir, n) for n in os.listdir(item_dir)
                 if n.endswith("_djvu.txt")), None)
    if path:
        raw = open(path, encoding="utf-8", errors="replace").read()
        if "\f" in raw:
            return raw.split("\f"), os.path.basename(path), "djvu-txt form-feed split"
    xml = next((os.path.join(item_dir, n) for n in os.listdir(item_dir)
                if n.endswith("_djvu.xml")), None)
    if not xml:
        raise SystemExit("no page-separable OCR surface (_djvu.txt with form-feeds, or _djvu.xml)")
    return render_djvu_xml_pages(xml), os.path.basename(xml), OCR_RENDER_RULE


def cmd_pagemap(args):
    pm = load_pagemap(os.path.join(STAGE, args.id))
    for leaf in sorted(pm):
        if pm[leaf] or args.all:
            print("  leaf %-5d printed page %s" % (leaf, pm[leaf] or "—"))


def cmd_pagetext(args):
    texts, _, _ = load_pagetexts(os.path.join(STAGE, args.id))
    if args.leaf >= len(texts):
        raise SystemExit("leaf %d out of range (%d pages)" % (args.leaf, len(texts)))
    t = texts[args.leaf]
    print("--- leaf %d · %d chars ---" % (args.leaf, len(t)))
    print(t)


# ── emit — passages JSON + the .ak pack, generated (never hand-written) ──────────────────────────
def ak_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def id_slug(s):
    """An atom id is a BARE token on every `ln` / `set.add` line, so it may carry no whitespace:
    a printed page like `[t.p. verso]` would re-split the line and bind the wrong src/dst/rel.
    The printed page is kept verbatim INSIDE the atom (and in every anchor); the id is its slug."""
    out = re.sub(r"[^a-z0-9]+", "_", s.strip().lower()).strip("_")
    return out or "unnumbered"


def ak_def(aid, content):
    if aid.split() != [aid]:
        raise SystemExit("atom id %r contains whitespace — it is a bare token on every ln / "
                         "set.add line and would re-split it (use id_slug)" % aid)
    return 'def "%s" "%s"' % (ak_escape(aid), ak_escape(content))


def resolve_span(page_text, spec, pid):
    """Locate the passage inside the page's OCR text. Explicit ocr_span wins; else quoted
    start/end snippets are searched — verbatim, so a typo here fails loudly, never silently."""
    if spec.get("ocr_span"):
        s, e = spec["ocr_span"]
        return int(s), int(e)
    q = spec.get("span_query") or {}
    s = page_text.find(q.get("start_text", ""))
    if s < 0 or not q.get("start_text"):
        raise SystemExit("[%s] start_text not found on the page (OCR differs? fix the selection)" % pid)
    if q.get("end_text"):
        e = page_text.find(q["end_text"], s)
        if e < 0:
            raise SystemExit("[%s] end_text not found after start on the page" % pid)
        e += len(q["end_text"])
    else:
        e = len(page_text.rstrip())
    return s, e


def cmd_emit(args):
    item_dir = os.path.join(STAGE, args.id)
    sel = json.load(open(args.selection, encoding="utf-8"))
    meta = json.load(open(os.path.join(item_dir, "ia_metadata.json"), encoding="utf-8"))
    arts = json.load(open(os.path.join(item_dir, "artifacts.json"), encoding="utf-8"))
    pagemap = load_pagemap(item_dir)
    texts, txt_name, render_rule = load_pagetexts(item_dir)
    jp2 = _pick(meta, "_jp2.zip")
    jp2_prefix = jp2["name"][:-len("_jp2.zip")] if jp2 else args.id

    ed = sel["edition"]
    book_atom = sel["book"]["atom"]
    ed_atom = ed["atom"]

    # 1 · the passage file (§6.1) — text sliced verbatim from the page's OCR
    passages = []
    for p in sel["passages"]:
        leaf = int(p["leaf"])
        page_text = texts[leaf]
        printed = pagemap.get(leaf) or p.get("page")
        if not printed:
            raise SystemExit("[%s] leaf %d has no printed page number and none supplied — "
                             "an unanchorable fragment may not ship (§3)" % (p["pid"], leaf))
        s, e = resolve_span(page_text, p, p["pid"])
        scan = ("https://archive.org/download/%s/%s_jp2.zip/%s_jp2%%2F%s_%04d.jp2"
                % (args.id, jp2_prefix, jp2_prefix, jp2_prefix, leaf))
        passages.append({
            "book": sel["book"]["statement"],
            "section": p["section_label"],
            "atom": "shelf:dibdin:passage:%s" % p["pid"],   # §13 — what a kept question links to
            "text": page_text[s:e],
            "anchor": {"edition": ed["statement"], "page": printed, "leaf": leaf,
                       "uri": "https://archive.org/details/%s/page/n%d" % (args.id, leaf),
                       "ocr_source": txt_name, "ocr_render": render_rule,
                       "ocr_span": [s, e], "scan": scan},
            "bridges": (p.get("bridges") or [])[:2],
            # No "level"/"stratum" text tag: the classification is a Set MEMBERSHIP minted below
            # (`shelf:level:source`, `shelf:stratum:original`). A value the code compares against is
            # vocabulary — a free string in the record would be a second, driftable source of truth.
        })
    os.makedirs(PACK_DIR, exist_ok=True)
    save(os.path.join(PACK_DIR, "passages_ep1.json"),
         json.dumps({"passages": passages}, indent=2, ensure_ascii=False))

    # 2 · the bibliographic record (§1C + §6.3) — its OWN record, never derived from A
    bib = dict(sel["bibliographic"])
    bib["digital_source"] = {"host": "Internet Archive", "identifier": args.id,
                             "item": "https://archive.org/details/" + args.id}
    bib["rights_verbatim"] = sel["rights_verbatim"]
    bib["retrieval_date"] = arts["retrieved"]
    bib["artifacts"] = arts["artifacts"]
    bib["title_page_verified"] = sel["title_page_verified"]
    save(os.path.join(PACK_DIR, "bibliographic_record.json"),
         json.dumps(bib, indent=2, ensure_ascii=False))

    # 3 · the .ak pack — decomposition + STRUCTURAL relations only (§4, §5)
    L = []
    L.append("# shelf_dibdin — The Library Companion (Dibdin, 1824), episode-1 slice.")
    L.append("# GENERATED by app/scripts/shelf_dibdin_acquire.py — do not hand-edit; re-run emit.")
    L.append("# Strata: original (passages, verbatim JSON w/ anchor) + structural (entities,")
    L.append("# relations the text itself states). NO analytical relation lives here (§5).")
    L.append("")
    L.append(ak_def(book_atom, sel["book"]["desc"]))
    L.append('al %s %s' % (book_atom, sel["book"]["alias"]))
    L.append("ln %s shelf:book sys:is_a" % book_atom)
    L.append(ak_def(ed_atom, ed["desc"]))
    L.append("ln %s shelf:edition sys:is_a" % ed_atom)
    L.append("ln %s %s shelf:has_edition" % (book_atom, ed_atom))
    L.append("")
    for group, klass in (("persons", "shelf:person"), ("works", "shelf:work"),
                         ("places", "shelf:place"), ("printers", "shelf:printer"),
                         ("languages", "shelf:language"),
                         ("historical_references", "shelf:historical_reference")):
        for ent in sel.get("entities", {}).get(group, []):
            L.append(ak_def(ent["atom"], ent["desc"]))
            if ent.get("alias"):
                L.append("al %s %s" % (ent["atom"], ent["alias"]))
            L.append("ln %s %s sys:is_a" % (ent["atom"], klass))
            L.append('set.add name="shelf:dibdin:entities" id="%s"' % ent["atom"])
    L.append("")
    for src, dst, rel in sel.get("relations", []):
        L.append("ln %s %s %s" % (src, dst, rel))
    L.append("")
    seen_sections, seen_pages = set(), {}
    for p, rec in zip(sel["passages"], passages):
        sec_atom = p["section_atom"]
        if sec_atom not in seen_sections:
            seen_sections.add(sec_atom)
            L.append(ak_def(sec_atom, "%s — %s" % (rec["section"], sel["book"]["statement"])))
            L.append("ln %s shelf:section sys:is_a" % sec_atom)
            L.append("ln %s %s sys:part_of" % (sec_atom, book_atom))
        leaf = rec["anchor"]["leaf"]
        page_atom = "shelf:dibdin:page:%s" % id_slug(str(rec["anchor"]["page"]))
        if seen_pages.get(page_atom, rec["anchor"]["page"]) != rec["anchor"]["page"]:
            raise SystemExit("two printed pages slug to the same atom id (%s): %r and %r — "
                             "disambiguate in the selection" % (page_atom,
                                                                seen_pages[page_atom],
                                                                rec["anchor"]["page"]))
        if page_atom not in seen_pages:
            seen_pages[page_atom] = rec["anchor"]["page"]
            L.append(ak_def(page_atom, json.dumps(
                {"edition": rec["anchor"]["edition"], "page": rec["anchor"]["page"],
                 "leaf": leaf, "uri": rec["anchor"]["uri"], "scan": rec["anchor"]["scan"]},
                ensure_ascii=False, sort_keys=True)))
            L.append("ln %s shelf:page sys:is_a" % page_atom)
        pa = "shelf:dibdin:passage:%s" % p["pid"]
        L.append(ak_def(pa, json.dumps(rec, ensure_ascii=False, sort_keys=True)))
        L.append("ln %s shelf:passage sys:is_a" % pa)
        L.append("ln %s %s shelf:part_of_section" % (pa, sec_atom))
        L.append("ln %s %s shelf:anchored_in" % (pa, page_atom))
        L.append("ln %s shelf:stratum:original shelf:in_stratum" % pa)
        L.append("ln %s shelf:level:source shelf:at_level" % pa)
        # The classification AT MINT: a passage joins its stratum and its level Set the moment it is
        # defined, so "what stratum is this?" is answered by membership, never by reading a tag.
        L.append('set.add name="shelf:stratum:original" id="%s"' % pa)
        L.append('set.add name="shelf:level:source" id="%s"' % pa)
        L.append('set.add name="shelf:dibdin:passages:ep1" id="%s"' % pa)
    L.append("")
    # commentary stratum — corrections/observations live BESIDE the original, never inside it
    for c in sel.get("commentary", []):
        ca = "shelf:dibdin:commentary:%s" % c["id"]
        L.append(ak_def(ca, c["text"]))
        L.append("ln %s shelf:stratum:commentary shelf:in_stratum" % ca)
        L.append('set.add name="shelf:stratum:commentary" id="%s"' % ca)
        for pid in c.get("about_pids", []):
            L.append("ln %s shelf:dibdin:passage:%s sys:refers_to" % (ca, pid))
    L.append("")
    L.append(ak_def("shelf:dibdin:bib_record", json.dumps(bib, ensure_ascii=False, sort_keys=True)))
    L.append("ln shelf:dibdin:bib_record %s sys:part_of" % ed_atom)
    save(os.path.join(PACK_DIR, "dibdin_library_companion.ak"), "\n".join(L) + "\n")
    print("emitted: %d passages · %d entities · pack app/ontology/shelf_dibdin/ (ak + passages_ep1.json"
          " + bibliographic_record.json)" % (len(passages),
                                             sum(len(v) for v in sel.get("entities", {}).values())))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("locate")
    for name in ("probe", "fetch", "pagemap"):
        p = sub.add_parser(name)
        p.add_argument("--id", required=True)
        if name == "pagemap":
            p.add_argument("--all", action="store_true")
    p = sub.add_parser("titlepage")
    p.add_argument("--id", required=True)
    p.add_argument("--leaf", type=int, default=5)
    p = sub.add_parser("pagetext")
    p.add_argument("--id", required=True)
    p.add_argument("--leaf", type=int, required=True)
    p = sub.add_parser("emit")
    p.add_argument("--id", required=True)
    p.add_argument("--selection", required=True)
    args = ap.parse_args()
    {"locate": cmd_locate, "probe": cmd_probe, "titlepage": cmd_titlepage, "fetch": cmd_fetch,
     "pagemap": cmd_pagemap, "pagetext": cmd_pagetext, "emit": cmd_emit}[args.cmd](args)


if __name__ == "__main__":
    main()
