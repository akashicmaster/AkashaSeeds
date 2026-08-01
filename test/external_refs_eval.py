"""
External-refs derivation eval (external-refs-derivation-spec).

Guards the backend half of the archives external-navigation fix: the atom's external
identity (Wikidata QID, Wikimedia Commons image) must surface as {label,url,source} refs
so the frontend's External References renderer has 動線 to click. Derivation is read-only,
offline, deterministic — reads existing wd:/wc:/wp: cross-ref aliases + the linked media
atom; curated thesaurus:external_ref refs still win on a URL collision.

Run:  python test/external_refs_eval.py      (exit 0 = all pass)
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from lib.akasha.concepts.thesaurus import ThesaurusConcept

_fails = []


def check(name, cond):
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond:
        _fails.append(name)


class MockCortex:
    """Mirrors ontology/nutrition/worldcuisines.ak's shape for one dish + one media atom,
    plus an optional curated ExternalRef atom to test dedupe/precedence."""
    def __init__(self, aliases, content, links, alias_to_key, meta=None):
        self.aliases = aliases
        self.content = content
        self.links = links
        self.alias_to_key = alias_to_key
        self.meta = meta or {}

    def get_adjacent_links(self, key, rel=None):
        return list(self.links.get(key, []))

    def get_incoming_links(self, key, rel=None):
        return []

    def get_meta(self, key):
        return dict(self.meta.get(key, {}))

    def get_chunk(self, key):
        return self.content.get(key)

    def get_aliases_by_key(self, key):
        return list(self.aliases.get(key, []))

    def resolve_alias(self, a):
        return self.alias_to_key.get(a)


def _thes(cortex):
    t = ThesaurusConcept.__new__(ThesaurusConcept)
    t.cortex = cortex
    return t


def test_wikidata_and_commons_via_link():
    print("[1] wikidata (wd: alias) + commons (media:depicts link → content URL)")
    mc = MockCortex(
        aliases={"dish": ["dish:kabsa", "dish:wc:100", "dish:wd:Q2902532"],
                 "media": ["media:img:wc_100"]},
        content={"media": "https://upload.wikimedia.org/wikipedia/commons/kabsa.jpg?download"},
        links={"dish": [["media", "media:depicts"]]},
        alias_to_key={"media:img:wc_100": "media"},
    )
    refs = _thes(mc)._collect_external_refs("dish")
    by = {r["source"]: r for r in refs}
    check("wikidata ref derived from wd: alias",
          by.get("wikidata", {}).get("url") == "https://www.wikidata.org/wiki/Q2902532")
    check("commons ref from the media:depicts atom's content URL",
          by.get("commons", {}).get("url", "").endswith("kabsa.jpg?download"))
    check("no duplicate URLs", len({r["url"] for r in refs}) == len(refs))


def test_commons_via_wc_alias_fallback():
    print("[2] commons fallback: no media link → resolve <ns>:wc:<id> → media:img:wc_<id>")
    mc = MockCortex(
        aliases={"dish": ["dish:arepa", "dish:wc:1001"], "media": ["media:img:wc_1001"]},
        content={"media": "https://upload.wikimedia.org/wikipedia/commons/arepa.jpg"},
        links={"dish": []},                                   # no media:depicts link
        alias_to_key={"media:img:wc_1001": "media"},
    )
    refs = _thes(mc)._collect_external_refs("dish")
    check("commons ref recovered via wc: alias resolution",
          any(r["source"] == "commons" and r["url"].endswith("arepa.jpg") for r in refs))


def test_media_atom_self_ref():
    print("[3] a media:img:* atom surfaces its OWN URL as a commons source badge")
    mc = MockCortex(
        aliases={"media": ["media:img:wc_100"]},
        content={"media": "https://upload.wikimedia.org/wikipedia/commons/kabsa.jpg"},
        links={"media": []},
        alias_to_key={},
    )
    refs = _thes(mc)._collect_external_refs("media")
    check("media atom page gets its own commons ref",
          any(r["source"] == "commons" for r in refs))


def test_curated_wins_on_collision():
    print("[4] curated thesaurus:external_ref wins a URL collision with a derived ref")
    URL = "https://www.wikidata.org/wiki/Q2902532"
    mc = MockCortex(
        aliases={"dish": ["dish:kabsa", "dish:wd:Q2902532"], "cur": []},
        content={},
        links={"dish": [["cur", "thesaurus:external_ref"]]},
        alias_to_key={},
        meta={"cur": {"type": "thesaurus:ExternalRef", "label": "Curated Wikidata", "url": URL}},
    )
    refs = _thes(mc)._collect_external_refs("dish")
    same = [r for r in refs if r["url"] == URL]
    check("exactly one badge for the shared URL (deduped)", len(same) == 1)
    check("the curated ref wins (source=curated, its label kept)",
          same and same[0]["source"] == "curated" and same[0]["label"] == "Curated Wikidata")


def test_non_qid_wd_alias_ignored():
    print("[5] a wd: alias whose tail is NOT a QID (an atom id) does not become a link")
    mc = MockCortex(
        aliases={"cheese": ["cheese:wd:camembert", "cheese:wd:Q182527"]},  # id + real QID
        content={}, links={"cheese": []}, alias_to_key={},
    )
    refs = _thes(mc)._collect_external_refs("cheese")
    wd = [r for r in refs if r["source"] == "wikidata"]
    check("only the real QID becomes a wikidata link (id-form ignored)",
          len(wd) == 1 and wd[0]["url"].endswith("Q182527"))


def main():
    test_wikidata_and_commons_via_link()
    test_commons_via_wc_alias_fallback()
    test_media_atom_self_ref()
    test_curated_wins_on_collision()
    test_non_qid_wd_alias_ignored()
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — external identity (wikidata/commons) is derived into external_refs; curated wins.")
    sys.exit(0)


if __name__ == "__main__":
    main()
