#!/usr/bin/env python3
"""
shelf_verify_pack.py — hold an acquired work to the quality gates of the acquisition order.

Checks an emitted pack (`app/ontology/shelf_dibdin/` by default) against §8 of
`docs/for-llm/thinkers-shelf-data-acquisition.md`, so a corpus can be proven sound BEFORE it is
committed, registered and bundled into a seed. Exit 0 = every gate passed.

    python app/scripts/shelf_verify_pack.py
    python app/scripts/shelf_verify_pack.py --pack app/ontology/shelf_dibdin --id <ia identifier>

The strongest gate needs the staging directory (`shelf_data/<id>/`, gitignored): with it, every
passage's `text` is RE-SLICED out of the fetched OCR at its recorded `ocr_span` and compared byte for
byte — proving `text == OCR[ocr_span]` rather than trusting it. Without staging that gate reports
SKIP (it cannot be faked into a PASS).
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# The vocabulary the `shelf` pack defines (`shelf:level:<x>` / `shelf:stratum:<x>`); an acquired
# pack mints a fragment INTO one of these Sets rather than writing the word into its record.
LEVELS = ("source", "derived", "interpretive", "speculative")
STRATA = ("original", "structural", "analytical", "commentary")
# §5 — acquisition extracts what the page STATES. These are readings ACROSS sources and must not
# appear in an acquired pack; they are the programme's to make, later, as analytical fragments.
ANALYTICAL_RELS = ("shelf:evidences_construct", "shelf:supported_by", "shelf:related_construct",
                   "shelf:intersects", "shelf:shares_sources_with", "shelf:shares_method_with",
                   "shelf:later_fragmented_into", "shelf:contrasts_with", "shelf:historically_precedes",
                   "shelf:derived_from", "shelf:opens_construct")
BIB_REQUIRED = ("title", "author", "edition", "publication_year", "publisher", "volume")

_fail, _warn = [], []


def gate(name, ok, detail="", skip=False):
    tag = "SKIP" if skip else ("PASS" if ok else "FAIL")
    print("  %-5s %s%s" % (tag, name, ("   (%s)" % detail) if detail else ""))
    if skip:
        _warn.append(name)
    elif not ok:
        _fail.append(name)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def page_texts(item_dir):
    """The per-page OCR surfaces the emit step sliced from, if staging is present."""
    if not item_dir or not os.path.isdir(item_dir):
        return None, None
    cand = glob.glob(os.path.join(item_dir, "*_djvu.txt"))
    if cand:
        raw = open(cand[0], encoding="utf-8", errors="replace").read()
        # older IA djvu.txt separates leaves with a form feed; leaf N == chunk N (0-based)
        if "\f" in raw:
            return raw.split("\f"), os.path.basename(cand[0])
    # current IA derivations carry no separator in _djvu.txt — re-render per leaf from _djvu.xml
    # by the SAME deterministic rule the acquisition tool records in the anchor (`ocr_render`):
    # WORDs of a LINE joined by ' ', LINEs joined by '\n', one page per OBJECT.
    xml = glob.glob(os.path.join(item_dir, "*_djvu.xml"))
    if not xml:
        return None, None
    import xml.etree.ElementTree as ET
    pages, lines, words = [], [], []
    for ev, el in ET.iterparse(xml[0], events=("start", "end")):
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
    return pages, os.path.basename(xml[0])


def main():
    ap = argparse.ArgumentParser(description="Verify an acquired Thinker's Shelf pack (§8 gates).")
    ap.add_argument("--pack", default=os.path.join(ROOT, "app", "ontology", "shelf_dibdin"))
    ap.add_argument("--id", default="", help="IA identifier, to re-slice from shelf_data/<id>/")
    args = ap.parse_args()
    pack = args.pack

    print("\n  Thinker's Shelf — acquisition gates · %s\n  %s" % (os.path.relpath(pack, ROOT), "=" * 62))
    if not os.path.isdir(pack):
        print("  FAIL  the pack directory does not exist — nothing to verify.")
        print("\n  The acquisition tool writes it with `emit`; it is NOT gitignored and must be committed.\n")
        return 2

    # ── files ────────────────────────────────────────────────────────────────────────────────────
    aks = glob.glob(os.path.join(pack, "*.ak"))
    pjs = glob.glob(os.path.join(pack, "passages*.json"))
    bibp = os.path.join(pack, "bibliographic_record.json")
    gate("the pack carries a .ak, a passage file and a bibliographic record",
         bool(aks) and bool(pjs) and os.path.exists(bibp),
         "ak=%d passages=%d bib=%s" % (len(aks), len(pjs), os.path.exists(bibp)))
    if not (aks and pjs and os.path.exists(bibp)):
        print("\n  RESULT: FAIL (incomplete pack)\n")
        return 1
    gate("PACK.json present (the pack is loadable as an ontology package)",
         os.path.exists(os.path.join(pack, "PACK.json")))

    passages = []
    for p in pjs:
        passages += (load_json(p).get("passages") or [])
    bib = load_json(bibp)
    ak = "\n".join(open(a, encoding="utf-8").read() for a in aks)
    # The generated reldef layer (`_lexicon.ak`) repeats a definition for every relation the pack
    # USES, by design — it is the pack's self-contained definition layer, not content. The content
    # gates below read the corpus files only.
    corpus_ak = "\n".join(open(a, encoding="utf-8").read() for a in aks
                          if os.path.basename(a) != "_lexicon.ak")

    # ── §3 anchoring ─────────────────────────────────────────────────────────────────────────────
    unanchored = [i for i, p in enumerate(passages)
                  if not ((p.get("anchor") or {}).get("page") is not None
                          and ((p.get("anchor") or {}).get("uri") or (p.get("anchor") or {}).get("scan")))]
    gate("every passage resolves: printed page + (uri | scan)", not unanchored,
         "n=%d bad=%s" % (len(passages), unanchored[:3]))
    nospan = [i for i, p in enumerate(passages)
              if not isinstance((p.get("anchor") or {}).get("ocr_span"), (list, tuple))]
    gate("every passage carries an ocr_span (re-readable at the source)", not nospan, "bad=%s" % nospan[:3])
    empty = [i for i, p in enumerate(passages) if not (p.get("text") or "").strip()]
    gate("no empty passage text", not empty, "bad=%s" % empty[:3])

    # ── §6.1 the contract the reading cycle consumes ─────────────────────────────────────────────
    # Stratum and level are Set MEMBERSHIPS minted with the passage, never a text tag: a value the
    # code compares against is vocabulary, and a tag beside the membership would be a second,
    # driftable source of truth. So the gate reads the pack's memberships, and separately refuses a
    # record that re-states them as free strings.
    members = {}
    for nm, aid in re.findall(r'^set\.add\s+name="([^"]+)"\s+id="([^"]+)"', ak, re.M):
        members.setdefault(nm, set()).add(aid)
    unclassified = [p.get("atom") for p in passages
                    if p.get("atom") not in members.get("shelf:stratum:original", set())
                    or p.get("atom") not in members.get("shelf:level:source", set())]
    gate("every passage is minted into its stratum and level Set (shelf:stratum:original + "
         "shelf:level:source), not tagged", not unclassified, "bad=%s" % unclassified[:3])
    tagged = [p.get("atom") for p in passages if "level" in p or "stratum" in p]
    gate("no passage record re-states its classification as a free string (one source of truth)",
         not tagged, "tagged=%s" % tagged[:3])
    stray = sorted(n for n in members
                   if (n.startswith("shelf:level:") and n[len("shelf:level:"):] not in LEVELS)
                   or (n.startswith("shelf:stratum:") and n[len("shelf:stratum:"):] not in STRATA))
    gate("the pack mints into DEFINED level / stratum Sets only", not stray, "stray=%s" % stray[:3])
    toomany = [i for i, p in enumerate(passages) if len(p.get("bridges") or []) > 2]
    gate("no passage opens more than two doors (§10)", not toomany, "bad=%s" % toomany[:3])

    # ── the strongest gate: text == OCR[ocr_span], re-sliced ─────────────────────────────────────
    item_dir = os.path.join(ROOT, "shelf_data", args.id) if args.id else ""
    leaves, txt_name = page_texts(item_dir)
    if not leaves:
        gate("passage text re-slices byte-for-byte from the fetched OCR", False,
             "staging shelf_data/<id>/ not present — run with --id on the acquiring machine", skip=True)
    else:
        bad = []
        for i, p in enumerate(passages):
            a = p.get("anchor") or {}
            leaf, span = a.get("leaf"), a.get("ocr_span")
            if leaf is None or not span:
                bad.append((i, "no leaf/span"))
                continue
            if leaf >= len(leaves):
                bad.append((i, "leaf %s beyond OCR" % leaf))
                continue
            if leaves[leaf][int(span[0]):int(span[1])] != p.get("text"):
                bad.append((i, "text != OCR[span]"))
        gate("passage text re-slices byte-for-byte from the fetched OCR (no silent repair)",
             not bad, "source=%s bad=%s" % (txt_name, bad[:3]))

    # ── §1C / §2.2 the bibliographic record ──────────────────────────────────────────────────────
    missing = [k for k in BIB_REQUIRED if not bib.get(k)]
    gate("bibliographic record carries the required fields", not missing, "missing=%s" % missing)
    gate("rights statement captured verbatim", bool((bib.get("rights_verbatim") or "").strip()))
    gate("the edition was verified against the title page, not the catalogue",
         bool(bib.get("title_page_verified")))
    gate("retrieval date recorded", bool(bib.get("retrieval_date")))
    arts = bib.get("artifacts") or []
    unver = [a.get("file") for a in arts if not (a.get("verified") or a.get("referenced_only"))]
    gate("every fetched artifact hash-verified against the host (images referenced only)",
         bool(arts) and not unver, "n=%d unverified=%s" % (len(arts), unver[:3]))

    # ── the .ak pack ─────────────────────────────────────────────────────────────────────────────
    bad_vocab = [l.strip() for l in ak.splitlines() if l.strip() and not l.strip().startswith("#")
                 and not re.match(r"^(def\s|ln\s|al\s|set\.add\s)", l.strip())]
    gate("the pack uses only the release .ak vocabulary (def/ln/al/set.add/#)",
         not bad_vocab, "offending=%s" % bad_vocab[:2])
    used = set(re.findall(r"^ln\s+\S+\s+\S+\s+(\S+)\s*$", ak, re.M))
    leaked = sorted(used & set(ANALYTICAL_RELS))
    gate("no ANALYTICAL relation in an acquired pack (§5 — acquisition states, it does not read)",
         not leaked, "leaked=%s" % leaked)
    defs = set(re.findall(r'^def\s+"([^"]+)"', ak, re.M))
    # An atom id is a BARE token on every `ln` / `set.add` line, so whitespace inside one silently
    # re-splits the line: the loader binds the wrong src/dst/rel and the lexicon mints a relation
    # out of the second half. (This is how `reldef:verso]` was minted from a page id `[t.p. verso]`.)
    spaced = sorted(a for a in defs if a.split() != [a])
    gate("no defined atom id contains whitespace (a bare token on every ln / set.add line)",
         not spaced, "bad=%s" % spaced[:3])
    # §5.2 — the source decomposition (book / edition / page / … / historical reference) is defined
    # ONCE, in the `shelf` pack; an acquired pack only INSTANTIATES it. So every atom this pack
    # defines is corpus-namespaced, and the classes it links to come from `shelf`.
    vocab = ""
    for fp in sorted(glob.glob(os.path.join(ROOT, "app", "ontology", "shelf", "*.ak"))):
        vocab += open(fp, encoding="utf-8", errors="ignore").read()
    vocab_defs = set(re.findall(r'^def\s+"([^"]+)"', vocab, re.M))
    corpus_defs = set(re.findall(r'^def\s+"([^"]+)"', corpus_ak, re.M))
    redefined = sorted(corpus_defs & vocab_defs)
    gate("the pack re-defines no vocabulary of the `shelf` pack (it instantiates, §5.2)",
         not redefined, "redefined=%s" % redefined[:3])
    corpus = os.path.basename(pack.rstrip("/")).split("shelf_")[-1]
    offnamespace = sorted(a for a in corpus_defs if not a.startswith("shelf:%s:" % corpus))
    gate("every atom the pack defines is corpus-namespaced (shelf:%s:…)" % corpus,
         not offnamespace, "stray=%s" % offnamespace[:3])
    targets = set()
    for s, d in re.findall(r"^ln\s+(\S+)\s+(\S+)\s+\S+\s*$", ak, re.M):
        targets |= {s, d}
    ext = targets - defs
    allak = ""
    for fp in glob.glob(os.path.join(ROOT, "ontology", "**", "*.ak"), recursive=True):
        allak += open(fp, encoding="utf-8", errors="ignore").read()
    dangling = sorted(a for a in ext if ('def "%s"' % a) not in allak)
    gate("no dangling link target (every atom the pack links is defined somewhere)",
         not dangling, "dangling=%s" % dangling[:3])

    # ── registration + downstream ────────────────────────────────────────────────────────────────
    reg = load_json(os.path.join(ROOT, "ontology", "REGISTRY.json"))
    name = os.path.basename(pack.rstrip("/"))
    entry = next((x for x in reg.get("packages", []) if x.get("name") == name), None)
    gate("the pack is registered in ontology/REGISTRY.json as tier C",
         bool(entry) and entry.get("tier") == "C",
         "entry=%s" % json.dumps(entry) if entry else "not registered")

    print("  %s" % ("=" * 62))
    print("  passages=%d  entities(defs)=%d  artifacts=%d" % (len(passages), len(defs), len(arts)))
    if _fail:
        print("\n  RESULT: FAIL (%d gate(s)): %s\n" % (len(_fail), "; ".join(_fail)))
        return 1
    if _warn:
        print("\n  RESULT: PASS with %d skipped gate(s) — re-run on the acquiring machine with --id "
              "to close them.\n" % len(_warn))
        return 0
    print("\n  RESULT: PASS — the acquisition satisfies every gate of the order.")
    print("  Next:  python scripts/gen_lexicon.py && python test/verify_lexicon.py --all")
    print("         python app/scripts/shelf_reading_cycle.py --passages %s --cycles 3\n"
          % os.path.relpath(pjs[0], ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
