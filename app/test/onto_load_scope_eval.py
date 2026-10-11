#!/usr/bin/env python3
"""
An ontology load holds only the workloads it touches.

Frontend note 2026-09-28, "needs platform" 1. While the ontology load ran, the driver answered
`pick deferred reason=onto_load` for EVERY workload, so one 400-atom pack stopped all five
programmes for 17 minutes, including those that read nothing from it.

The load now states what it is doing (`ontology.loader.in_flight`: `first`, and the packs found
CHANGED so far). The driver holds a workload only when one of those packs DECLARES a name the
workload declares it reads — a `pins` value or a `requires` Set (`W.ontology_names`). On a cell's
first load every workload is still held, because the graph is not there yet.

This eval drives the REAL driver tick, on a cell provisioned from the REAL declarations, against
the REAL packs that declare those names. It holds:

  1. a load in flight that is rewriting `station_neta` (the news show's ネタ帖) holds the news show,
     naming the pack and the Set, and holds NOTHING else — each other programme is picked;
  2. rewriting `shelf_dibdin` holds the Thinker's Shelf, and not the news show;
  3. a load rewriting a pack that declares none of the workloads' names holds nobody;
  4. a cell's FIRST load holds every workload (the tick returns before any pick), as before;
  5. with no load in flight nothing is held;
  6. each loading pack is scanned ONCE per load, and the answer is kept on the in-flight record;
  7. `pack_declares` reads `def`, `al` and `set.add name=` lines, and nothing else.

Run:  python test/onto_load_scope_eval.py     (exit 0 = all pass)
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "test"))
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap:
    lines = []


def main():
    print("=" * 78)
    print("An ontology load holds only the workloads it touches")
    print("=" * 78)
    import workload_conformance_eval as C
    from lib.akasha.api import schedule as S
    from lib.akasha.ontology import loader as L
    from lib.akasha.workbench import provision, workload as W, wl_state, autorun, llm_pool, llm_provider as lp
    from lib.akasha.concepts.society import SocietyConcept

    # Every pick is REFUSED by the pool (it cannot fit one run), so a picked workload shows up as a
    # `ran` action with a refusal and costs nothing — the eval is about who is PICKED, not a run.
    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "1"
    lp._METER.clear(); lp._METER_LOADED = True; lp._NEXT_OK.clear()
    vault = {}
    llm_pool.set_pool_store(lambda kk: vault.get(kk), lambda kk, d: vault.__setitem__(kk, dict(d)))
    llm_pool._MEM.clear()
    wl_state.last_effect_at = lambda *_a, **_kw: 0.0

    # The cell runs its OWN driver thread (the writer phase starts it), which ticks the moment
    # provisioning finishes and every 60 s after — concurrently with this eval's ticks. A pick it
    # made between `_arm_all` and `_tick` spent the boot gate, and the eval's tick then skipped that
    # programme silently (not due): the news show, the shelf and the ISS feed vanished from runs at
    # random. The cell's thread is parked (it calls the module's tick by name); the eval calls the
    # real one.
    _real_tick = autorun.bench_autorun_tick
    autorun.bench_autorun_tick = lambda *_a, **_kw: []
    k = C._cell(_Cap())
    provision.provision_workloads(k)
    sc = SocietyConcept(k.manager.get_session("system.broadcaster"))
    decls = {W.key(d): d for d in W.declarations(k) if not W.problems(d)}
    socs = {"%s/%s" % W.society_of(d): key for key, d in decls.items()}

    def _arm_all():
        # Every pick here is REFUSED by the pool on purpose, and a refused run is a failed run: the
        # driver's breaker drops a best-effort workload to manual on it, out of the auto index, so
        # which programmes the NEXT tick even sees depended on the order the pool refused them in
        # (the shelf and the ISS feed vanished from some runs). Re-arm through provisioning — the
        # one thing that re-arms a tripped workload — so every tick asks about holds and nothing else.
        provision.provision_workloads(k)
        for ptr in sc.list_auto_societies():
            st = dict((sc.read_autorun(ptr["gid"], ptr["name"]) or {}).get("state") or {})
            # runs_today/day too: a pick in the previous tick counts toward a workload's daily cap,
            # and a cap of 1 (the shelf, the ISS feed) then reads as `budget_skip`, not as a hold —
            # which made this eval depend on the declarations' budgets rather than on the load.
            for kk in ("last_run", "retry_at", "retry_count", "breaker", "runs_today", "day",
                       "spent_no_effect", "spent_no_effect_calls"):
                st.pop(kk, None)
            st["boot_pending"] = True
            sc.write_autorun_state(ptr["gid"], ptr["name"], st)

    def _tick():
        _arm_all()
        acts = _real_tick(k, now=time.time())
        held = {socs.get(a["society"], a["society"]): a for a in acts if a.get("action") == "held"}
        picked = {socs.get(a["society"], a["society"]) for a in acts if a.get("action") == "ran"}
        return held, picked, acts

    def _load(first, packs):
        S.mark_running(k, "ontology.loaded")
        L.publish_in_flight(k, first=first, packs=list(packs))

    def _done():
        S.open_gate(k, "ontology.loaded")
        L.publish_in_flight(k, clear=True)

    news, shelf = "studio_ai/news_show", "studio_ai/thinkers_shelf"
    check("the real declarations provision (the news show and the shelf are among them)",
          news in decls and shelf in decls, str(sorted(decls)))

    print("\n  ── 5. no load in flight ──")
    _done()
    held, picked, _a = _tick()
    check("nothing is held, and the armed workloads are picked", not held and news in picked,
          "held=%s picked=%s" % (sorted(held), sorted(picked)))
    all_picked = set(picked)

    print("\n  ── 1. a load rewriting the news show's ネタ帖 pack ──")
    _load(False, ["station_neta"])
    held, picked, _a = _tick()
    check("the news show is held, reason onto_load, naming the pack and its item Set",
          news in held and held[news].get("reason") == wl_state.REASON_ONTO_LOAD
          and held[news].get("packs") == ["station_neta"]
          and "neta:studio_ai:news_show:src" in (held[news].get("names") or []), str(held.get(news)))
    # The X channel reads a Set of this pack too since 2026-09-28 (its sponsor lines,
    # `pins.sponsor_set` → x_sponsor.ak), so it is held WITH the news show — for the same reason.
    # Reviewed 2026-10-02 (platform §3): the adaptation is right, but `set(held) <= _touch` also
    # passed with the X channel PICKED during the load. The hold is asserted, and its cause named
    # by the declaration's own pin, so a sponsor Set that moves out of the pack moves the answer.
    xch = "studio_ai/news_show_x"
    x_set = str(((decls.get(xch) or {}).get("pins") or {}).get("sponsor_set") or "")
    check("the X channel (it reads %s from that pack) is held too, for the same reason" % x_set,
          xch in all_picked and x_set and xch in held
          and held[xch].get("reason") == wl_state.REASON_ONTO_LOAD
          and held[xch].get("packs") == ["station_neta"]
          and x_set in (held[xch].get("names") or []), str(held.get(xch)))
    _touch = {news, xch}
    check("…and NOTHING else is held: every other armed programme is picked",
          set(held) == _touch and (all_picked - _touch) <= picked,
          "held=%s picked=%s" % (sorted(held), sorted(picked)))
    decl_before = dict(L.in_flight(k).get("declares") or {})
    _tick()
    check("6. the loading pack was scanned ONCE — the second tick reused the kept answer",
          set(decl_before) == {"station_neta"} and L.in_flight(k).get("declares") == decl_before,
          str(decl_before))
    _done()

    print("\n  ── 2. a load rewriting the shelf's pack ──")
    _load(False, ["shelf_dibdin"])
    held, picked, _a = _tick()
    check("the Thinker's Shelf is held (its passages Set and its work atom)",
          shelf in held and {"shelf:dibdin:passages:ep1"} <= set(held[shelf].get("names") or []),
          str(held.get(shelf)))
    check("…and the news show is picked", news not in held and news in picked,
          "held=%s" % sorted(held))
    _done()

    print("\n  ── 3. a load rewriting a pack no workload reads ──")
    _load(False, ["vocab"])
    held, picked, _a = _tick()
    check("nobody is held", not held, str(sorted(held)))
    _done()

    print("\n  ── 4. the cell's FIRST load ──")
    _load(True, [])
    held, picked, acts = _tick()
    check("every workload is held: the tick returns before any pick (the graph is not there yet)",
          not acts, str(acts)[:160])
    _done()

    print("\n  ── 7. what `pack_declares` reads ──")
    import tempfile
    tmp = tempfile.mkdtemp(prefix="onto_decl_")
    pd = os.path.join(tmp, "ontology", "evalpack")
    os.makedirs(pd)
    with open(os.path.join(pd, "a.ak"), "w", encoding="utf-8") as f:
        f.write('# name:in_a_comment\n'
                'def "x:defined" "text that mentions x:only_in_text"\n'
                'al x:defined x:alias_name\n'
                'set.add name="x:a_set" id="x:defined"\n'
                'ln x:defined x:only_linked thesaurus:related\n')
    _pd = L.project_dir
    L.project_dir = lambda: tmp
    try:
        got = L.pack_declares("evalpack", ["x:defined", "x:alias_name", "x:a_set", "x:only_linked",
                                           "x:only_in_text", "name:in_a_comment"])
    finally:
        L.project_dir = _pd
    check("a def id, an al alias and a set.add Set are declared; a link target, a word in a "
          "description and a comment are not",
          got == {"x:defined", "x:alias_name", "x:a_set"}, str(sorted(got)))

    print("\n  ── 4b. what counts as a FIRST load ──")
    sd = tempfile.mkdtemp(prefix="onto_sent_")
    od = os.path.join(ROOT, "ontology")
    open(os.path.join(sd, "bench_provision_news_show_ab12cd34.done"), "w").close()
    open(os.path.join(sd, "wb_boot_x.done"), "w").close()
    check("a cell whose sentinels are all other boot bodies' has never loaded a pack → first",
          L._any_pack_sentinel(sd, od) is False)
    open(os.path.join(sd, "station_neta_0123abcd.done"), "w").close()
    check("one pack sentinel (`<pack>_<hash>.done`) → not first", L._any_pack_sentinel(sd, od) is True)

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a load in flight holds only the workloads whose declared names a changing "
          "pack declares; the rest are picked; a first load holds everything; each pack is scanned "
          "once per load.")
    sys.exit(0)


if __name__ == "__main__":
    main()
