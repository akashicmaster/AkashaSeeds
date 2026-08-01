#!/usr/bin/env python3
"""
thesaurus external-ref consolidation eval — op_concept must surface a URL for BOTH reference
systems, so Wikipedia/web auto-fetch results become clickable on the concept page.

Historically op_concept collected external references only from `thesaurus:external_ref` links
whose target meta.type == "thesaurus:ExternalRef". A Wikipedia auto-fetch instead writes the
enriching atom with meta.type="fetch:<source>" (+ url/title, provenance=external) and a `ref:web`
URL exit-atom — a separate reference system that never surfaced. `_collect_external_refs` unifies
both from the concept's 1-hop neighbourhood, deduped by URL.

This is a pure unit test of that helper against a fake cortex (the two get_adjacent_links return
shapes replicated): curated + fetched(fetch:wikipedia) + url-atom(ref:web), a duplicate URL, and a
plain non-ref neighbour that must be excluded.

  XR1 curated   — a thesaurus:ExternalRef is surfaced with its url + source="curated".
  XR2 fetched   — a fetch:wikipedia atom (incoming, any relation) is surfaced with url + source.
  XR3 ref:web   — a ref:web URL exit-atom is surfaced.
  XR4 dedupe    — the same URL from two systems appears once (curated wins).
  XR5 exclude   — a neighbour with no url is not a reference.

Run:  python test/thesaurus_extref_eval.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:11} {detail}")


class FakeCortex:
    """Replicates the two get_adjacent_links return shapes used by op_concept:
    with a rel filter → [(dst, weight)]; without → [(dst, rel)]. Incoming → [(dst, rel)]."""
    def __init__(self, out, inc, meta, chunks=None):
        self.out, self.inc, self.meta, self.chunks = out, inc, meta, (chunks or {})

    def get_adjacent_links(self, key, rel_pattern=None):
        if rel_pattern is not None:
            return [(d, 1.0) for (d, r) in self.out if r == rel_pattern]
        return list(self.out)

    def get_incoming_links(self, key, rel_pattern=None):
        if rel_pattern is not None:
            return [(d, 1.0) for (d, r) in self.inc if r == rel_pattern]
        return list(self.inc)

    def get_meta(self, key):
        return self.meta.get(key, {})

    def get_chunk(self, key):
        return self.chunks.get(key, "")

    def get_aliases_by_key(self, key):
        # op_concept resolves an atom's display aliases; this eval doesn't exercise the
        # alias layer, so a namespaced key stands in for itself and bare keys have none.
        return [key] if isinstance(key, str) and ":" in key else []


def main():
    print("\n  thesaurus external-ref consolidation eval\n")
    from lib.akasha.concepts.thesaurus import ThesaurusConcept

    ICARUS = "https://en.wikipedia.org/wiki/Icarus"
    DAEDALUS = "https://en.wikipedia.org/wiki/Daedalus"
    BRIT = "https://www.britannica.com/topic/Icarus"

    out = [
        ("ref_cur", "thesaurus:external_ref"),   # curated
        ("url_web", "ref:source"),               # a ref:web URL exit-atom
        ("dup",     "thesaurus:related"),        # fetched, SAME url as curated → deduped
        ("plain",   "thesaurus:related"),        # a normal neighbour, no url → excluded
    ]
    inc = [
        ("fetched", "ctx:topic"),                # a fetch:wikipedia atom, incoming
    ]
    meta = {
        "ref_cur": {"type": "thesaurus:ExternalRef", "label": "Britannica: Icarus", "url": BRIT},
        "url_web": {"type": "ref:web", "url": DAEDALUS, "title": "Daedalus"},
        "fetched": {"type": "fetch:wikipedia", "url": ICARUS, "title": "Icarus",
                    "provenance": "external", "source": "wikipedia"},
        "dup":     {"type": "fetch:web", "url": BRIT, "title": "dup", "provenance": "external"},
        "plain":   {"type": "word"},             # no url
    }

    obj = type("O", (), {})()
    obj.cortex = FakeCortex(out, inc, meta)
    refs = ThesaurusConcept._collect_external_refs(obj, "C")
    by_url = {r["url"]: r for r in refs}

    record("XR1 curated", by_url.get(BRIT, {}).get("source") == "curated"
           and by_url.get(BRIT, {}).get("label") == "Britannica: Icarus", f"brit={by_url.get(BRIT)}")
    record("XR2 fetched", by_url.get(ICARUS, {}).get("source") == "wikipedia"
           and by_url.get(ICARUS, {}).get("label") == "Icarus", f"icarus={by_url.get(ICARUS)}")
    record("XR3 ref:web", DAEDALUS in by_url and by_url[DAEDALUS]["source"] == "web",
           f"daedalus={by_url.get(DAEDALUS)}")
    record("XR4 dedupe", len(refs) == 3 and list(by_url).count(BRIT) == 1,
           f"count={len(refs)} urls={sorted(by_url)}")
    record("XR5 exclude", all("plain" not in (r.get("label", "") + r.get("url", "")) for r in refs)
           and len(refs) == 3, f"n={len(refs)}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
