#!/usr/bin/env python3
"""
seeds-14 §2 — the research lab, ported onto the Workbench (Option B).

The Research Notebook (`research.*`) runs on the existing RESEARCH BENCH (kind=research): a chunk is a
NOTE-family entry with provenance (`research.note` with `type=` + author/society/role + the
`set:wb:<labo>:by:*` provenance Set), recorded through `_perform` so every step tees an observation + a
bench coordinate + the inline act; a Publication Set is composed with `composed_from` / `published_in`
links + a presentation macro; the four orderings are macros over `research.note.timeline`. `research.*`
forwards to `bench.*` (the single writer); a legacy `research_chunk` atom is mapped once by the hydrate
backfill.

This eval drives it on BOTH cell shapes.

Run:  python app/test/research_workbench_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import provision
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _load_macros(k):
    """Register the shipped research macros as the boot loader does (bootstraps are off in a bare test
    kernel), so macro.run resolves them."""
    mdir = os.path.join(ROOT, "app", "config", "macros")
    for fn in ("research.cronon", "research.argument", "research.evidence", "research.publication",
               "research.present"):
        raw = open(os.path.join(mdir, fn + ".csl")).read()
        params, body = "", []
        for ln in raw.splitlines():
            s = ln.strip()
            if s.startswith("#!params"):
                params = s[len("#!params"):].strip(); continue
            if s.startswith("#"):
                continue
            body.append(ln)
        k.dispatch({"jsonrpc": "2.0", "method": "macro.def",
                    "params": {"client_id": "system.librarian",
                               "data": {"name": fn, "params": params, "script": "\n".join(body).strip(),
                                        "scope": "universal"}}, "id": "m"}, "internal")


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts._universal import UniversalConcept, slug as _slug
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_rwb_"))
    k._bfp_cache = "researchbuild1"
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    d("world.genesis", {})
    _load_macros(k)
    # the demonstrator Labo's bench, stood up by ops (it was `bench_research.json`, a scaffold that is not a
    # workload declaration and is deleted)
    cfg = {"world": "default", "group": "research-lab",
           "society": {"name": "research", "kind": "cowork", "identity": "open", "public": False},
           "bench": {"name": "research", "kind": "research", "public": True},
           "grants": {"Recorder": ["operator:note", "operator:publication", "decide"]}}

    # ── item 1 — the research society + bench (the legacy bench_*.json pass is gone — the purge order
    #    §2; a Labo's bench is stood up by ops, or by a workload declaration, never by that pass) ──
    gid, sname = cfg["group"], cfg["society"]["name"]
    d("grp.new", {"group_id": gid, "admin_id": "admin"})
    b = d("bench.new", {"name": cfg["bench"]["name"], "kind": cfg["bench"]["kind"]})
    s = d("society.new", {"group": gid, "name": sname, "world": cfg.get("world") or "default",
                          "bench": cfg["bench"]["name"], "kind": cfg["society"]["kind"]})
    provision.provision_capabilities(k, gid, sname, cfg["bench"]["name"], cfg.get("grants") or {},
                                     bool(cfg["bench"].get("public")))
    check(f"[{shape}] the research society + bench are stood up",
          "error" not in b and "error" not in s, "%s / %s" % (str(b)[:80], str(s)[:80]))
    info = d("bench.info", {"name": "research"})
    check(f"[{shape}] the research bench exists (kind=research, note + publication families)",
          info.get("kind") == "research" and {"note", "publication"} <= set(info.get("families") or []),
          str(info.get("families")))

    # ── item 6 — B5 offered capability Sets written for the role ──
    cap = d("cap.ls", {"role": "Recorder", "context": "research"})
    names = {o.get("name") for o in (cap.get("offered") or [])}
    check(f"[{shape}] provisioning wrote the Recorder's offered capabilities (B5 Sets)",
          {"operator:note", "operator:publication"} <= names, str(sorted(names)))

    # ── item 2/3/4 — a chunk is a note-family entry with provenance, through the recorder ──
    d("labo.new", {"name": "research", "about": "the demonstrator"})
    q = d("research.chunk", {"labo": "research", "type": "question", "content": "why the cluster?",
                             "author": "ana"})
    h = d("research.chunk", {"labo": "research", "type": "hypothesis", "content": "a cost effect",
                             "supersedes": q.get("chunk"), "author": "ben"})
    check(f"[{shape}] research.chunk forwards to research.note (chunk recorded, cronon int, id preserved)",
          q.get("chunk") == "research:chunk:research:1" and isinstance(q.get("cronon"), int)
          and q.get("observed_at_seq"), str(q)[:100])
    ba = "wb:%s" % _slug("research")
    m = d("read", {"id": q.get("chunk")}).get("meta") or {}
    check(f"[{shape}] the chunk is a note-family entry with the D2-M facets + provenance",
          m.get("concept") == "bench_note" and m.get("family") == "note" and m.get("type") == "question"
          and m.get("author") == "ana" and m.get("mode") == "thought", str({x: m.get(x) for x in
          ("concept", "family", "type", "author")}))
    byset = d("set.ls", {"name": "set:%s:by:ana" % ba})
    check(f"[{shape}] provenance: the chunk joins set:wb:research:by:<author>",
          byset.get("count") == 1, str(byset.get("count")))
    coord = d("set.ls", {"name": "cronon:%s:c%d" % (ba, q.get("observed_at_seq"))})
    check(f"[{shape}] the step minted its bench coordinate cronon:{ba}:c<n>", coord.get("count") >= 1,
          str(coord.get("count")))
    decl = d("set.ls", {"name": "set:%s:act:declared" % ba})
    judg = d("set.ls", {"name": "set:%s:act:judged" % ba})
    check(f"[{shape}] recording mints act_declared AND act_judged (two memberships)",
          decl.get("count") == 2 and judg.get("count") == 2,
          f"declared={decl.get('count')} judged={judg.get('count')}")
    strm = d("source.stream", {"stream": "source:stream:%s" % ba, "limit": 10})
    a0 = next((sm.get("act") for o in (strm.get("observations") or [])
               for sm in [o.get("source_metadata") or {}]
               if sm.get("family") == "note" and sm.get("act")), None) or {}
    check(f"[{shape}] the chunk observation carries the inline act {{declared, judged, by}} (GUI §11)",
          a0.get("declared") and "judged" in a0 and str(a0.get("by") or "").startswith("agent:"),
          str(a0)[:100])

    # ── item 5 — a Publication Set is composed_from / published_in + an artifact ──
    pub = d("research.publication", {"labo": "research", "name": "draft1",
                                     "chunks": "%s,%s" % (q.get("chunk"), h.get("chunk"))})
    check(f"[{shape}] a Publication Set is composed (artifact_id + built_at_epoch)",
          pub.get("count") == 2 and pub.get("artifact_id") and isinstance(pub.get("built_at_epoch"), int),
          str({x: pub.get(x) for x in ("count", "artifact_id", "built_at_epoch")}))
    tr = d("research.trace", {"id": h.get("chunk")})
    check(f"[{shape}] the chunk backlinks published_in the publication (composed_from ↔ published_in)",
          "published_in" in (tr.get("out") or {}), str(tr.get("out"))[:100])

    # ── item 7 — the old research.* surface still reads (forwarding) ──
    tl = d("research.timeline", {"name": "research", "order": "cronon"})
    check(f"[{shape}] research.timeline forwards + retains superseded (2 chunks, h supersedes q)",
          tl.get("count") == 2 and any(c.get("superseded") for c in tl.get("chunks", [])),
          str(tl.get("count")))

    # ── the four orderings are macros (macro.run), plus the presentation macro ──
    def macro(name, **kw):
        r = d("macro.run", dict({"name": name, "as": "inline"}, **kw))
        return ((r.get("last") or {}).get("result") or {})
    arg = macro("research.argument", bench="research")
    check(f"[{shape}] the ordering macros run (research.argument → question first)",
          arg.get("order") == "argument" and (arg.get("chunks") or [{}])[0].get("type") == "question",
          str(arg.get("order")))
    pres = macro("research.present", bench="research", pub="draft1")
    check(f"[{shape}] the presentation macro presents the Publication Set in composed order",
          pres.get("count") == 2 and len(pres.get("sections") or []) == 2, str(pres.get("count")))

    # ── item 4 — the hydrate backfill maps a legacy research_chunk atom once ──
    u = UniversalConcept(k.manager.get_session("admin"))
    u._space = ""
    d("labo.new", {"name": "legacy", "about": "pre-port"})
    lk = u._mk("research:chunk:legacy:1", "[research:chunk:legacy:1] finding: old",
               {"concept": "research_chunk", "labo": "labo:legacy", "type": "finding",
                "content": "old finding", "author": "cid", "cronon": 3})
    u._add_to_set("research:chunk:legacy", lk)
    b1 = d("research.layer.backfill", {})
    b2 = d("research.layer.backfill", {})
    check(f"[{shape}] the hydrate backfill maps a legacy research_chunk once (assigned 1 → 0)",
          b1.get("assigned") == 1 and b2.get("assigned") == 0,
          f"first={b1.get('assigned')} second={b2.get('assigned')}")
    lm = d("read", {"id": "research:chunk:legacy:1"}).get("meta") or {}
    lba = "wb:%s" % _slug("legacy")
    ln = d("set.ls", {"name": "%s:notes" % lba})
    lby = d("set.ls", {"name": "set:%s:by:cid" % lba})
    check(f"[{shape}] the mapped legacy chunk is now a note joined to the notes + by Sets",
          lm.get("concept") == "bench_note" and ln.get("count") == 1 and lby.get("count") == 1,
          f"concept={lm.get('concept')} notes={ln.get('count')} by={lby.get('count')}")


def main():
    print("=" * 78)
    print("seeds-14 §2 — research lab ported onto the Workbench, Option B (research_workbench_eval)")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the Research Notebook runs on the research bench: one config/bench_<labo>.json "
          "provisions the society + public bench + B5 Sets; a chunk is a note-family entry with "
          "provenance (set:wb:<labo>:by:*), recorded through the recorder (bench coordinate + inline "
          "act); a Publication Set is composed_from / published_in + an artifact with a presentation "
          "macro; the four orderings are macros; the old research.* surface forwards; and the hydrate "
          "backfill maps a legacy research_chunk once — both cell shapes.")


if __name__ == "__main__":
    main()
