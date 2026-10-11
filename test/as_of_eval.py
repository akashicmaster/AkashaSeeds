#!/usr/bin/env python3
"""
B4 §A5 — as-of reads: the durable universe as it stood at an epoch.

`set.ls name= as_of=<epoch>` returns a Set's membership as it stood — the members whose first recorded
at_seq is ≤ the epoch (an append-only Set's history). `r id= as_of=<epoch>` returns the atom's META as of
the epoch (content is immutable); before the atom's first at_seq it is absent. A horizon / accelerator
read (semcache / exec / stage / coordinate / hydrate / store) refuses as_of with -32602. As-of reads are
budget-bounded (over → partial=true reason=budget), and the answer equals the recorded history across a
restart. Durable universe only — meta as-of; content immutable.

This eval drives it on BOTH cell shapes:
  • three members at three epochs; as_of at each epoch returns the membership as it stood, with
    history_from = the earliest known at_seq; an epoch before all of them is empty;
  • a meta change at epoch e is invisible at e-1 (the older version is returned);
  • a horizon Set read refuses; a budget cut returns partial=true;
  • the same as-of answer survives a restart (the durable store, not a cache).

Run:  python test/as_of_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
SET = "set:demo:evals"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _kernel(series, base):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    return KernelDispatcher(series=series, base_dir=base)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.concepts.cronon import CrononConcept
    base = tempfile.mkdtemp(prefix="akasha_asof_")
    k = _kernel(series, base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    def err(method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")

    cc = CrononConcept(k.manager.get_session("admin"))
    # three members, each stamped with its own creation epoch (at_seq)
    for i, ep in enumerate((10, 20, 30), start=1):
        kk = cc._mk("demo:m%d" % i, "[demo:m%d] row %d" % (i, i),
                    {"concept": "demo_row", "at_seq": ep, "n": i})
        cc._add_to_set(SET, kk)

    # ── set.ls as_of returns the membership as it stood ──
    for ep, want in ((5, 0), (10, 1), (20, 2), (30, 3), (99, 3)):
        r = a("set.ls", {"name": SET, "as_of": str(ep)})
        check(f"[{shape}] set.ls as_of={ep} → {want} member(s)",
              r.get("count") == want and r.get("as_of") == ep, f"count={r.get('count')}")
    r30 = a("set.ls", {"name": SET, "as_of": "30"})
    check(f"[{shape}] set.ls as_of carries history_from = the earliest at_seq",
          r30.get("history_from") == 10, str(r30.get("history_from")))
    live = a("set.ls", {"name": SET})
    check(f"[{shape}] a plain set.ls (no as_of) is unchanged (3 members, no as_of field)",
          live.get("count") == 3 and "as_of" not in live, str(live.get("count")))

    # ── r as_of: meta as of an epoch; content immutable; before first at_seq → absent ──
    km = cc._mk("demo:atom", "immutable content",
                {"concept": "demo_atom", "at_seq": 10, "v": 2,
                 "_asof_hist": [{"at_seq": 10, "meta": {"concept": "demo_atom", "at_seq": 10, "v": 1}},
                                {"at_seq": 20, "meta": {"concept": "demo_atom", "at_seq": 20, "v": 2}}]})
    r_now = a("read", {"id": "demo:atom"})
    check(f"[{shape}] a live read (no as_of) returns the current meta (v=2)",
          (r_now.get("meta") or {}).get("v") == 2, str(r_now.get("meta")))
    r_e10 = a("read", {"id": "demo:atom", "as_of": "10"})
    check(f"[{shape}] r as_of=10 returns the meta as it stood (v=1)",
          (r_e10.get("meta") or {}).get("v") == 1 and r_e10.get("as_of") == 10, str(r_e10.get("meta")))
    r_e15 = a("read", {"id": "demo:atom", "as_of": "15"})
    check(f"[{shape}] a meta change at epoch 20 is invisible at 15 (still v=1)",
          (r_e15.get("meta") or {}).get("v") == 1, str(r_e15.get("meta")))
    r_e20 = a("read", {"id": "demo:atom", "as_of": "20"})
    check(f"[{shape}] r as_of=20 sees the change (v=2)", (r_e20.get("meta") or {}).get("v") == 2,
          str(r_e20.get("meta")))
    r_before = err("read", {"id": "demo:atom", "as_of": "5"})
    check(f"[{shape}] r as_of before the atom's first at_seq → absent",
          "error" in r_before, str(r_before)[:120])
    check(f"[{shape}] content is immutable — the as-of read returns the same content",
          r_e10.get("content") == r_now.get("content"), str(r_e10.get("content"))[:60])

    # ── a horizon / accelerator read refuses as_of ──
    hz = err("set.ls", {"name": "set:stage:featured", "as_of": "10"})
    check(f"[{shape}] a horizon Set read refuses as_of with -32602",
          (hz.get("error") or {}).get("code") == -32602
          and "horizon" in ((hz.get("error") or {}).get("message") or ""), str(hz.get("error")))

    # ── a budget cut returns partial=true reason=budget ──
    from lib.akasha.kernel import KernelDispatcher
    _saved = KernelDispatcher._ASOF_MAX_WALK
    KernelDispatcher._ASOF_MAX_WALK = 2
    try:
        rb = a("set.ls", {"name": SET, "as_of": "99"})
    finally:
        KernelDispatcher._ASOF_MAX_WALK = _saved
    check(f"[{shape}] an as_of walk over the budget returns partial=true reason=budget",
          rb.get("partial") is True and rb.get("reason") == "budget", str(rb)[:140])

    # ── the same as-of answer survives a restart (durable, not a cache) ──
    k2 = _kernel(series, base)
    r2 = k2.dispatch({"jsonrpc": "2.0", "method": "set.ls",
                      "params": {"session_token": "admin", "data": {"name": SET, "as_of": "20"}},
                      "id": "t"}, "local")
    r2 = (r2.get("result") or {})
    check(f"[{shape}] as-of equals the recorded history after a restart (as_of=20 → 2)",
          r2.get("count") == 2 and r2.get("as_of") == 20, str(r2.get("count")))

    # ── B4-a — as_of filters for a GUEST too (the member meta is resolved nucleus-aware) ──
    # The SET's members are universal (nucleus) atoms. A guest's read cortex does not union the nucleus
    # for get_meta, so before the fix the as-of loop read None for every member and kept them all; after
    # the nucleus-aware resolver a guest sees the same history as the admin.
    gtok = (k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                        "params": {"data": {}}, "id": "gg"}, "network").get("result") or {}).get("binding_key")

    def gg(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": gtok, "data": data}, "id": "gq"}, "network")
        return r if "error" in r else (r.get("result") or {})

    for ep, want in ((5, 0), (20, 2), (99, 3)):
        rg = gg("set.ls", {"name": SET, "as_of": str(ep)})
        check(f"[{shape}] B4-a: a GUEST as_of={ep} read filters nucleus-aware → {want}",
              rg.get("count") == want and rg.get("as_of") == ep, f"count={rg.get('count')}")

    # ── B4-b — a horizon / accelerator read (hydrate.ls / store.status) refuses as_of ──
    for meth in ("hydrate.ls", "store.status"):
        hz = k.dispatch({"jsonrpc": "2.0", "method": meth,
                         "params": {"session_token": "admin", "data": {"as_of": "10"}}, "id": "h"}, "local")
        check(f"[{shape}] B4-b: {meth} refuses as_of with -32602",
              (hz.get("error") or {}).get("code") == -32602
              and "horizon" in ((hz.get("error") or {}).get("message") or ""), str(hz.get("error")))


def main():
    print("=" * 78)
    print("B4 §A5 — as-of reads (durable universe only)")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — set.ls / r read the durable universe as of an epoch (membership as it stood, "
          "meta as of, content immutable, absent before the first at_seq), a horizon read refuses, a "
          "budget cut returns partial, and the answer survives a restart — both cell shapes.")


if __name__ == "__main__":
    main()
