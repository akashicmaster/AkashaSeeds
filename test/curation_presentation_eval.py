#!/usr/bin/env python3
"""
curation → presentation → export eval. Spec: docs/for-llm/curation-presentation-scroll-spec.md.

  CP1 project        — cur.project builds one frame per curation atom, in order (private deck).
  CP2 scroll scenes  — pr.export as=scroll → N ordered atom-card scenes (headword/description/
                       href/links present; blocks absent for scroll).
  CP3 kamishibai     — as=kamishibai carries blocks[] for an enriched frame, [] for a plain one;
                       same scene spine (content identical, only layout richness differs).
  CP4 degradation    — a frame whose ref is missing → headword-only scene, image null, no drop.
  CP5 idempotent     — re-projecting the same curation returns the same presentation.
  CP6 publish        — publish=<slug> writes a self-contained JSON readable with NO graph access.
  CP7 cli text       — inline export carries a plain-text rendering for the CLI.

Run:  python test/curation_presentation_eval.py
"""
import os, sys, json, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def main():
    print("\n  curation → presentation → export eval\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cp_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or {"__error__": r.get("error")}

    # concepts (with an external ref on icarus so refs[] is exercised)
    for a, desc in [("concept:icarus", "Icarus — son of Daedalus who flew on wings of wax and fell."),
                    ("concept:daedalus", "Daedalus — the master craftsman who built the labyrinth."),
                    ("concept:flight", "Flight — movement through the air.")]:
        d("def", {"name": a, "description": desc, "scope": "universal"})
    d("ln", {"src": "concept:icarus", "dst": "concept:daedalus", "rel": "thesaurus:related", "scope": "universal"})
    # an external ref atom on icarus (curated ExternalRef)
    d("def", {"name": "ref:icarus_wiki", "description": "https://en.wikipedia.org/wiki/Icarus", "scope": "universal"})
    core = k.manager.get_session("admin").nucleus.core
    rk = k.manager.get_session("admin").local_cortex.resolve_alias("ref:icarus_wiki")
    if rk:
        core.update_meta(rk, {"type": "thesaurus:ExternalRef", "label": "Icarus",
                              "url": "https://en.wikipedia.org/wiki/Icarus"})
    d("ln", {"src": "concept:icarus", "dst": "ref:icarus_wiki", "rel": "thesaurus:external_ref", "scope": "universal"})

    cur = d("curation.new", {"title": "A Genealogy of Dreams",
                             "ids": "concept:icarus,concept:daedalus,concept:flight", "mode": "authored"})
    cid = cur.get("curation_id")

    # CP1 project
    proj = d("curation.project", {"id": cid, "as": "presentation", "title": "A Genealogy of Dreams"})
    pid = proj.get("presentation_id")
    record("CP1 project", proj.get("status") == "projected" and proj.get("frames") == 3 and bool(pid),
           f"status={proj.get('status')} frames={proj.get('frames')}")

    # CP2 scroll scenes
    exp = d("pres.export", {"id": pid, "as": "scroll", "inline": "true"})
    ex = exp.get("export") or {}
    scenes = ex.get("scenes") or []
    ok2 = (ex.get("format") == "scroll" and ex.get("count") == 3
           and [s["headword"] for s in scenes] == ["Icarus", "Daedalus", "Flight"]
           and all(s.get("description") for s in scenes)
           and scenes[0].get("href") == "/a/concept:icarus"
           and any(r.get("url") for r in scenes[0].get("refs", []))
           and "blocks" not in scenes[0])
    record("CP2 scroll scenes", ok2,
           f"headwords={[s['headword'] for s in scenes]} refs0={len(scenes[0].get('refs',[]))} "
           f"links0={len(scenes[0].get('links',[]))}")

    # CP3 kamishibai — enrich frame 0 with a region + node, expect blocks there, [] elsewhere
    d("pres.open", {"pres_id": pid})
    frames = sorted(((k.manager.get_session("admin").local_cortex.get_meta(fk) or {}).get("order", 0), fk)
                    for fk in (d("pres.list", {}).get("frames") or []))
    f0 = frames[0][1]
    reg = d("pres.region.add", {"frame_id": f0, "label": "figure"})
    d("pres.node.add", {"parent_id": reg.get("region_id"), "ref_universe": "local",
                        "ref_id": k.manager.get_session("admin").local_cortex.resolve_alias("concept:daedalus"),
                        "role": "quote"})
    kam = d("pres.export", {"id": pid, "as": "kamishibai", "inline": "true"})
    kx = kam.get("export") or {}
    ks = kx.get("scenes") or []
    blocks0 = ks[0].get("blocks") if ks else None
    blocks1 = ks[1].get("blocks") if len(ks) > 1 else None
    record("CP3 kamishibai",
           kx.get("format") == "kamishibai" and bool(blocks0) and blocks1 == []
           and [s["headword"] for s in ks] == ["Icarus", "Daedalus", "Flight"],
           f"blocks0={len(blocks0 or [])} blocks1={blocks1} spine_same={[s['headword'] for s in ks]}")

    # CP4 degradation — a frame whose ref is a non-existent atom → headword-only, image null
    d("pres.open", {"pres_id": pid})
    d("pres.frame.add", {"deck_id": proj.get("deck_id"), "title": "Ghost", "order": 99,
                         "ref_universe": "local", "ref_id": "deadbeef" * 8})
    exp2 = d("pres.export", {"id": pid, "as": "scroll", "inline": "true"})
    ghost = [s for s in (exp2.get("export") or {}).get("scenes", []) if s.get("headword") == "Ghost"]
    record("CP4 degradation",
           len(ghost) == 1 and ghost[0].get("image") is None and not ghost[0].get("description"),
           f"ghost_scene={bool(ghost)} image={ghost[0].get('image') if ghost else '?'}")

    # CP5 idempotent
    proj2 = d("curation.project", {"id": cid, "as": "presentation"})
    record("CP5 idempotent", proj2.get("reused") is True and proj2.get("presentation_id") == pid,
           f"reused={proj2.get('reused')}")

    # CP6 publish — writes a self-contained JSON readable with NO graph access
    pub = d("pres.export", {"id": pid, "as": "scroll", "publish": "genealogy-of-dreams"})
    url = pub.get("url")
    path = os.path.join(ROOT, "archives", "curation", "exports", "genealogy-of-dreams.scroll.json")
    file_ok, self_contained = False, False
    if os.path.exists(path):
        file_ok = True
        with open(path, encoding="utf-8") as f:
            art = json.load(f)                        # pure JSON read — NO graph access
        self_contained = (art.get("format") == "scroll" and art.get("count") >= 3
                          and all(s.get("headword") for s in art.get("scenes", [])))
        os.remove(path)                               # cleanup
    record("CP6 publish", pub.get("status") == "published" and url and file_ok and self_contained,
           f"url={url} file={file_ok} self_contained={self_contained}")

    # CP7 cli text
    txt = exp.get("text") or ""
    record("CP7 cli text",
           "A Genealogy of Dreams" in txt and "Icarus" in txt and "scene(s)" in txt,
           f"text_lines={len(txt.splitlines())}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
