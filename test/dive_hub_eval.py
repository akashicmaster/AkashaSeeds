#!/usr/bin/env python3
"""
dive-hub eval — a proto-word hub must reveal the semantic field of its senses.

When two qualified atoms share a leaf (word:en:apple + ingred:fruit:apple), the
alias engine auto-creates a bare proto-word `apple` and links each sense to it via
`specializes`. All the real edges (→ sweet, → red, dishes → apple) attach to the
SENSES, not the bare hub. Diving the common word `apple` lands on the hub, whose
only 1-hop links are the `specializes` scaffolding — so the rich neighbourhood is
one hop away, untraversed. This eval reproduces that and asserts the fix: diving a
proto-word hub surfaces the union of its senses' neighbours.

  H1 hub is thin        — raw link.list on `apple` = only incoming `specializes`.
  H2 senses are rich    — link.list on each sense carries the real edges.
  H3 hub view expands   — generate_view(`apple`) signposts include the senses'
                          neighbours (sweet/red/crisp/dish…), not just specializes.
  H4 love hub expands    — same for love (concept:love + word:en:love → emo:*).
  H5 sense view intact   — diving a sense directly is unchanged (no double-count).
  H6 nav keys valid      — every expanded signpost has a resolvable key.

Run:  python test/dive_hub_eval.py
"""
import os, sys, hashlib, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def main():
    print("\n  dive-hub eval — proto-word hub reveals its senses' field\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_hub_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    # ── Build the two apple senses + one love, exactly as the ontology does ──────
    # Link targets first.
    for nm, desc in [("dna:taste:sweet", "sweet"), ("dna:color:red", "red"),
                     ("dna:texture:crisp", "crisp"), ("verb:cook:core", "cook"),
                     ("emo:joy", "joy"), ("emo:trust", "trust"), ("emo:tenderness", "tenderness")]:
        d("def", {"name": nm, "description": desc})

    # Sense 1: culinary ingredient.
    d("def", {"name": "ingred:fruit:apple",
              "description": "A round fruit with red or green skin. Used fresh, baked, or juiced."})
    d("ln", {"src": "ingred:fruit:apple", "dst": "dna:taste:sweet",  "rel": "calc:associated_with"})
    d("ln", {"src": "ingred:fruit:apple", "dst": "dna:color:red",    "rel": "calc:associated_with"})
    d("ln", {"src": "ingred:fruit:apple", "dst": "dna:texture:crisp","rel": "calc:associated_with"})
    d("ln", {"src": "ingred:fruit:apple", "dst": "verb:cook:core",   "rel": "sys:refers_to"})
    # Sense 2: the dictionary word.
    d("def", {"name": "word:en:apple",
              "description": "Fruit with red or yellow or green skin and sweet crisp whitish flesh."})
    d("ln", {"src": "word:en:apple", "dst": "dna:color:red", "rel": "calc:associated_with"})
    # Incoming edges from dishes onto the culinary sense.
    d("def", {"name": "dish:apple_pie", "description": "A baked pie filled with spiced apples."})
    d("ln", {"src": "dish:apple_pie", "dst": "ingred:fruit:apple", "rel": "thesaurus:related"})
    d("def", {"name": "dish:cider", "description": "A drink pressed from apples."})
    d("ln", {"src": "dish:cider", "dst": "ingred:fruit:apple", "rel": "thesaurus:related"})

    # love: two senses onto emotions.
    d("def", {"name": "concept:love", "description": "Love — deep affection and attachment."})
    d("ln", {"src": "concept:love", "dst": "emo:tenderness", "rel": "calc:associated_with"})
    d("ln", {"src": "concept:love", "dst": "emo:trust",      "rel": "calc:associated_with"})
    d("def", {"name": "word:en:love", "description": "An intense feeling of deep affection."})
    d("ln", {"src": "word:en:love", "dst": "emo:joy", "rel": "calc:associated_with"})

    def links(alias):
        r = d("link.list", {"id": alias})
        return r.get("links", []) if isinstance(r, dict) else []

    def sp_of(alias):
        v = d("view", {"id": alias})
        if not isinstance(v, dict) or "signposts" not in v:
            return None, v
        return v["signposts"], v

    # H1 — the hub is thin: raw direct links are only incoming `specializes`.
    hub = links("apple")
    only_spec = bool(hub) and all(l["rel"] == "specializes" and l["direction"] == "in" for l in hub)
    record("H1 hub is thin", only_spec, f"apple raw links: {[(l['direction'],l['rel']) for l in hub]}")

    # H2 — the senses carry the real edges.
    ing = links("ingred:fruit:apple")
    ing_real = sum(1 for l in ing if l["rel"] != "specializes")
    record("H2 senses are rich", ing_real >= 5,
           f"ingred:fruit:apple real links={ing_real} (total {len(ing)})")

    # H3 — diving the hub surfaces the senses' neighbours, not just specializes.
    sps, v = sp_of("apple")
    if sps is None:
        record("H3 hub view expands", False, f"view error: {v}")
    else:
        rels = [sp.get("rel") for sp in sps]
        aliases = [str(sp.get("alias")) for sp in sps]
        semantic = [sp for sp in sps if sp.get("rel") != "specializes"]
        touches = " ".join(aliases)
        want = any(t in touches for t in ("sweet", "red", "crisp", "cook", "pie", "cider"))
        record("H3 hub view expands", len(semantic) >= 5 and want,
               f"signposts={len(sps)} semantic={len(semantic)} rels={set(rels)}")

    # H4 — love hub likewise reaches the emotion field.
    sps_l, vl = sp_of("love")
    if sps_l is None:
        record("H4 love hub expands", False, f"view error: {vl}")
    else:
        al = " ".join(str(sp.get("alias")) for sp in sps_l)
        emo_hits = sum(t in al for t in ("joy", "trust", "tenderness"))
        record("H4 love hub expands", emo_hits >= 2,
               f"signposts={len(sps_l)} emo_hits={emo_hits} aliases={[str(sp.get('alias')) for sp in sps_l]}")

    # H5 — diving a sense directly is still correct (rich, no self/dup explosion).
    sps_s, vs = sp_of("ingred:fruit:apple")
    if sps_s is None:
        record("H5 sense view intact", False, f"view error: {vs}")
    else:
        keys = [sp["key"] for sp in sps_s]
        no_dup = len(keys) == len(set(keys))
        record("H5 sense view intact", len(sps_s) >= 5 and no_dup,
               f"signposts={len(sps_s)} unique={no_dup}")

    # H6 — every expanded signpost key resolves to a readable atom.
    sps2, _ = sp_of("apple")
    allkeys = [sp["key"] for sp in (sps2 or [])]
    resolvable = all(k and (d("r", {"id": k}) or {}).get("content") is not None for k in allkeys[:12])
    record("H6 nav keys valid", bool(allkeys) and resolvable, f"checked {min(len(allkeys),12)} keys")

    # H7 — the DIVE path (associations + 3D cosmos, fed by associate()/_traverse) is
    #      also rich on the hub: _traverse_associations seeds through the senses, so the
    #      cosmos graph is no longer a lone node. (dive overrides generate_view's
    #      associations with associate(); this asserts that override is now non-empty.)
    dv = d("dive.look", {"id": "love"})
    if not isinstance(dv, dict):
        record("H7 dive assoc rich", False, f"dive error: {dv}")
    else:
        assoc = dv.get("associations", [])
        cosmos_nodes = (dv.get("cosmos", {}) or {}).get("nodes", [])
        record("H7 dive assoc rich", len(assoc) >= 2 and len(cosmos_nodes) >= 3,
               f"associations={len(assoc)} cosmos_nodes={len(cosmos_nodes)}")

    # ── 語感-first: emotion/sensation nodes are NEVER capped; the rest overflow ──
    # Build a `berry` hub: one sense with 3 affect neighbours (taste/colour/emotion)
    # and 6 non-affect dishes pointing in. Force the display bound low so the
    # non-affect neighbours MUST overflow, and assert every affect node still shows.
    for nm, desc in [("dna:taste:tart", "tart"), ("dna:color:purple", "purple"), ("emo:delight", "delight")]:
        d("def", {"name": nm, "description": desc})
    d("def", {"name": "ingred:fruit:berry", "description": "A small juicy fruit."})
    d("ln", {"src": "ingred:fruit:berry", "dst": "dna:taste:tart",   "rel": "calc:associated_with"})
    d("ln", {"src": "ingred:fruit:berry", "dst": "dna:color:purple", "rel": "calc:associated_with"})
    d("ln", {"src": "ingred:fruit:berry", "dst": "emo:delight",      "rel": "calc:associated_with"})
    d("def", {"name": "word:en:berry", "description": "An edible small fruit."})
    for i in range(6):
        d("def", {"name": f"dish:berry_{i}", "description": f"Berry dish {i}."})
        d("ln", {"src": f"dish:berry_{i}", "dst": "ingred:fruit:berry", "rel": "thesaurus:related"})

    from lib.akasha.consciousness import ConsciousnessEngine
    saved = ConsciousnessEngine._HUB_SIGNPOST_DISPLAY
    ConsciousnessEngine._HUB_SIGNPOST_DISPLAY = 4   # force overflow of the 6 dishes
    try:
        v = d("view", {"id": "berry"})
    finally:
        ConsciousnessEngine._HUB_SIGNPOST_DISPLAY = saved

    if not isinstance(v, dict) or "signposts" not in v:
        record("H8 affect never capped", False, f"view error: {v}")
        record("H9 explicit overflow", False, "n/a")
    else:
        al = " ".join(str(sp.get("alias")) for sp in v["signposts"])
        affect_hits = sum(t in al for t in ("dna:taste:tart", "dna:color:purple", "emo:delight"))
        # All 3 affect present despite the low display bound (they bypass the cap).
        record("H8 affect never capped", affect_hits == 3,
               f"affect_hits={affect_hits}/3 signposts={len(v['signposts'])}")
        # The dishes overflow, and it is reported explicitly (never silently dropped).
        ov = v.get("hub_overflow", 0)
        record("H9 explicit overflow", ov >= 1,
               f"hub_overflow={ov} (6 dishes vs display bound 4)")

    # H10 — r (primitive) contract: one-hop, literal links, but ALL same-leaf senses
    #       to the proto-word are shown (fruit-apple + word-apple both reachable). r
    #       does NOT expand through the hub (that is the explorer's job) — it stays
    #       one level, just complete about the same-leaf senses.
    rr = d("r", {"id": "apple"})
    if not isinstance(rr, dict) or "in_links" not in rr:
        record("H10 r same-leaf senses", False, f"r error: {rr}")
    else:
        in_al = " ".join(a for l in rr["in_links"] for a in (l.get("aliases") or []))
        both = ("word:en:apple" in in_al) and ("ingred:fruit:apple" in in_al)
        # one-hop: r must NOT have pulled the senses' neighbours (no dna:*/sweet here)
        one_hop = "dna:" not in in_al and "dna:" not in \
            " ".join(a for l in rr.get("out_links", []) for a in (l.get("aliases") or []))
        record("H10 r same-leaf senses", both and one_hop,
               f"both_senses={both} one_hop={one_hop}")

    # H11 — first-class relation surfacing: define reldef:<rel>, and the explorer view
    #       attaches the full-spelling so a cryptic edge reads plainly.
    d("def", {"name": "reldef:calc:associated_with",
              "description": "associated with — a soft conceptual association."})
    v2 = d("view", {"id": "apple"})
    sps11 = v2.get("signposts", []) if isinstance(v2, dict) else []
    has_reldesc = any(sp.get("rel") == "calc:associated_with" and sp.get("rel_desc")
                      for sp in sps11)
    record("H11 rel surfacing", has_reldesc,
           f"a signpost carries rel_desc={has_reldesc}")

    # H12 — first-class namespace surfacing: define nsdef:<ns>, and r on a namespaced
    #       atom returns the namespace gloss.
    d("def", {"name": "nsdef:ingred", "description": "ingred — culinary ingredient namespace."})
    rr2 = d("r", {"id": "ingred:fruit:apple"})
    nsd = rr2.get("namespace_desc") if isinstance(rr2, dict) else None
    record("H12 namespace surfacing", bool(nsd) and nsd.startswith("ingred —"), f"namespace_desc={nsd!r}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
