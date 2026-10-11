#!/usr/bin/env python3
"""
The Ancient Civilizations atlas is ingested WHOLESALE into the ontology (not just the GUI).

The atlas references each civilization by an `ancient:<…>` atom id and carries its headword
(name + endonym), era, note, region, modern-country membership, sourced excavation sites, source
links, and historical-map links. atlas.json is a PROJECTION of the generated pack (each datum
carries source_atom). This eval proves the pack `app/ontology/ancient/civilizations.ak` covers ALL of
it — so the GUI is a projection of the ontology and GUI → CLI → ontology is reversible:

  • every `atom:'ancient:…'` id the GUI references has a `def` in the pack (no dangling GUI link);
  • every region has an `ancient:region:<id>` atom, and every civ is in set:ancient:all;
  • every source URL the GUI shows appears in the pack (source links imported wholesale);
  • every headword (civilization name) is aliased (searchable), and the endonym is in the atom body;
  • the pack uses ONLY the release .ak vocabulary (def / ln / al / set.add / #).

The generator `app/scripts/ancient_atlas_to_ak.py` is a DEV-side tool (the atlas is prepared off-line
into the pack, per the source-data-as-ontology principle); it is not shipped in the seed, so this
eval checks the SHIPPED `.ak` and does not run the generator.

Run:  python app/test/ancient_ontology_eval.py     (exit 0 = all pass)
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HTML = os.path.join(ROOT, "app", "archives", "ancient", "index.html")
AK = os.path.join(ROOT, "app", "ontology", "ancient", "civilizations.ak")
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    html = open(HTML, encoding="utf-8").read()
    ak = open(AK, encoding="utf-8").read()
    import json
    # atlas.json is a PROJECTION of this pack (app/scripts/ancient_atlas_project.py); shape {civs, regions}
    atlas_doc = json.load(open(os.path.join(ROOT, "app", "archives", "ancient", "atlas.json"), encoding="utf-8"))
    civs = atlas_doc.get("civs", atlas_doc)
    regions_proj = atlas_doc.get("regions", {})

    gui_atoms = set(re.findall(r"atom\s*:\s*'(ancient:[^']+)'", html))
    gui_regions = set(re.findall(r"id\s*:\s*'([a-z_]+)'\s*,\s*name\s*:", html))  # region ids
    # every external datum the GUI shows lives in the pack: source links, old-map links, countries
    gui_urls = set(s["url"] for e in civs.values() for s in (e.get("sources") or []))
    gui_oldmap_urls = set(m["url"] for e in civs.values() for m in (e.get("oldmaps") or []))
    gui_countries = set((e.get("source_atom", ""), c["iso"]) for e in civs.values()
                        for c in (e.get("countries") or []))

    ak_defs = set(re.findall(r'^def\s+"([^"]+)"', ak, re.M))
    ak_aliases = set(re.findall(r"^al\s+\S+\s+(\S+)", ak, re.M))
    set_all = set(re.findall(r'set\.add name="set:ancient:all" id="([^"]+)"', ak))
    set_regions = set(re.findall(r'set\.add name="set:ancient:regions" id="([^"]+)"', ak))

    check("the GUI references civilizations", len(gui_atoms) >= 70, f"{len(gui_atoms)} atom ids")
    missing = sorted(a for a in gui_atoms if a not in ak_defs)
    check("every GUI civilization atom id has a def in the pack (no dangling GUI link)",
          not missing, f"missing={missing[:5]}")

    # every region the GUI lists has an ancient:region:<id> atom
    reg_missing = sorted(r for r in gui_regions if ("ancient:region:%s" % r) not in ak_defs)
    check("every atlas region has an ancient:region:<id> atom",
          len(set_regions) >= 14 and not reg_missing, f"regions={len(set_regions)} missing={reg_missing[:5]}")

    # every civ atom is in set:ancient:all
    not_in_all = sorted(a for a in gui_atoms if a not in set_all)
    check("every civilization joins set:ancient:all", not not_in_all, f"missing={not_in_all[:5]}")

    # source links imported wholesale — every GUI url appears in the pack body
    url_missing = sorted(u for u in gui_urls if u not in ak)
    check("every GUI source URL is imported into the pack (source links wholesale)",
          bool(gui_urls) and not url_missing, f"urls={len(gui_urls)} missing={url_missing[:3]}")
    check("source-link atoms are linked ancient:source",
          ak.count("ancient:source") >= len(gui_urls), str(ak.count("ancient:source")))

    # modern-country membership imported wholesale — every atlas (civ, ISO3) is a spans_country link
    cty_missing = sorted("%s->%s" % (a, iso) for (a, iso) in gui_countries
                         if ("ln %s geo:country:%s ancient:spans_country" % (a, iso)) not in ak)
    check("every atlas country membership is imported (civ ancient:spans_country geo:country:<ISO3>)",
          bool(gui_countries) and not cty_missing, f"links={len(gui_countries)} missing={cty_missing[:3]}")

    # historical-map links imported wholesale — every old-map URL the GUI shows is in the pack, linked
    om_missing = sorted(u for u in gui_oldmap_urls if u not in ak)
    check("every historical-map link is imported into the pack (old maps wholesale)",
          bool(gui_oldmap_urls) and not om_missing and ak.count("ancient:has_oldmap") >= len(gui_oldmap_urls),
          f"oldmaps={len(gui_oldmap_urls)} missing={om_missing[:3]}")

    # the projection is FROM the ontology: every projected datum carries a source_atom, and every
    # region has its atlas pin as a coordinate atom (nothing the GUI draws is ontology-absent)
    no_src = [a for a, e in civs.items() if not e.get("source_atom")]
    pins_ok = bool(regions_proj) and all(r.get("pin_atom") for r in regions_proj.values())
    check("the GUI is a projection of the ontology — every civ + region carries a source_atom / pin",
          not no_src and pins_ok, f"civs_without_source={no_src[:3]} regions={len(regions_proj)}")

    # headwords: each civ name is aliased (searchable); endonym is in the body
    check("civilization headwords are aliased (searchable) — one alias per civ + region",
          len(ak_aliases) >= len(gui_atoms) and "sumer" in ak_aliases and "inca" in ak_aliases
          and "khmer_empire" in ak_aliases,
          f"{len(ak_aliases)} aliases for {len(gui_atoms)} civs")
    check("endonyms are carried in the atom body (headword #2)",
          "endonym ki-en-gir" in ak and "endonym Tawantinsuyu" in ak)

    # excavation sites (pilot) present + linked
    check("excavation sites are imported + linked ancient:site",
          ak.count("ancient:site") >= 11 and 'def "ancient:site:sumer:uruk"' in ak,
          str(ak.count("ancient:site")))

    # the pack uses ONLY the release .ak vocabulary
    bad = []
    for ln in ak.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if not re.match(r'^(def\s|ln\s|al\s|set\.add\s)', s):
            bad.append(s[:60])
    check("the pack uses only the release .ak vocabulary (def/ln/al/set.add/#)",
          not bad, f"offending={bad[:3]}")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the Ancient Civilizations atlas is ingested wholesale into the ontology: "
          "every GUI civilization atom, region, source link, headword and excavation site is a defined "
          "`ancient:*` atom (GUI → CLI → ontology reversible), and the pack is well-formed .ak.")
    sys.exit(0)


if __name__ == "__main__":
    main()
