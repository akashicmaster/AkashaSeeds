#!/usr/bin/env python3
"""
The status door decides what is an item by MEMBERSHIP, not by concept (the purge order, §1.5; the
10-03 §6 ruling).

`source.item.status pool= item= status=` is the source engine's one door for an item's status. An atom
that is a member of `pool=` is an item of that pool, whatever its concept — the same fact
`source.status` counts in `total`. On a real cell, both cell shapes:

  1. a member of a concept that is not `source_item` — here a plain atom with no concept at all —
     and with NO prior status, given one: the tally moves +1 into that bucket and nowhere else, the
     door returns `changed: true`, and `sum(by_status) == total` (the path `vlab.source.add` uses);
  2. the same status again is `changed: false` and moves nothing;
  3. a NON-member is refused `not a member of <pool>` (-32602), and so is the pool atom itself and an
     id that resolves to nothing;
  4. the door's code names no item concept (no `source_item`, no application concept — only its
     own engine's reserved `source_pool`, to know a pool) and carries no repair path.

Run:  python test/status_door_eval.py     (exit 0 = all pass)
"""
import hashlib
import inspect
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="door_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def raw(method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "internal")

    def d(method, data):
        r = raw(method, data)
        return r if "error" in r else (r.get("result") or {})

    def tally(p):
        st = d("source.status", {"pool": p})
        return {kk: int(v) for kk, v in (st.get("by_status") or {}).items()}, int(st.get("total") or 0)

    src = d("source.register", {"provider": "ev", "name": "door", "rights": "CC0"}).get("source")
    pool = d("source.pool.create", {"name": "door_p", "source": src, "rule": "all",
                                    "version": "v1"}).get("pool")
    plain = (d("w", {"content": "a pool member with no concept and no status (%s)" % shape,
                     "scope": "universal"}) or {}).get("key")
    d("source.pool.add", {"pool": pool, "id": plain})
    from lib.akasha import api as _api
    sc = _api.concept_class(k, "source")(k.manager.get_session("admin"))
    pm = sc.cortex.get_meta(plain) or {}
    check(f"[{shape}] (a member of the pool with no concept and no status)",
          not pm.get("concept") and not pm.get("status"), str(pm)[:120])

    b0, t0 = tally(pool)
    r = raw("source.item.status", {"pool": pool, "item": plain, "status": "ACQUIRED"})
    b1, t1 = tally(pool)
    moved = {kk: b1.get(kk, 0) - b0.get(kk, 0) for kk in b1}
    check(f"[{shape}] 1. its status is written: +1 into ACQUIRED and nowhere else, `changed: true`, "
          f"sum(by_status) == total",
          "error" not in r and (r.get("result") or {}).get("changed") is True
          and moved == {**{kk: 0 for kk in b1}, "ACQUIRED": 1} and sum(b1.values()) == t1 == 1,
          "%s; moved=%s total=%d" % (str(r.get("result") or r.get("error"))[:80], moved, t1))

    r2 = raw("source.item.status", {"pool": pool, "item": plain, "status": "ACQUIRED"})
    check(f"[{shape}] 2. the same status again: `changed: false`, nothing moves",
          (r2.get("result") or {}).get("changed") is False and tally(pool)[0] == b1, str(r2)[:120])

    other = (d("w", {"content": "an atom that is in no pool (%s)" % shape, "scope": "universal"})
             or {}).get("key")
    for what, item in (("a non-member", other), ("the pool atom itself", pool),
                       ("an id that resolves to nothing", "nothing:here")):
        rn = raw("source.item.status", {"pool": pool, "item": item, "status": "ACQUIRED"})
        check(f"[{shape}] 3. {what} is refused, and the reason is membership",
              (rn.get("error") or {}).get("code") == -32602 and "not a member of" in str(rn["error"]),
              str(rn.get("error"))[:140])


def main():
    print("=" * 78)
    print("The status door: membership, not concept")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    from lib.akasha.concepts import source as _SRC
    from lib.akasha.api.reserved import RESERVED_CONCEPTS
    door = inspect.getsource(_SRC.SourceDataLayer.op_item_status).split('"""')[-1]
    # it may name the POOL's reserved concept (that is how it knows `pool=` is a pool — rule 4); it
    # names no ITEM concept, reserved or the application's, because membership decides what an item is
    named = [c for c in list(RESERVED_CONCEPTS) + ["source_artwork"]
             if c in door and c != "source_pool"]
    check("4. the door's code names no item concept (only its own pool's reserved concept) and "
          "carries no repair path (no `check_drift`)",
          not named and "check_drift" not in door, str(named))
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — any member of the pool is an item, whatever its concept; a member with no "
          "status gets +1 and `changed: true`; the same status is `changed: false`; a non-member is "
          "refused with the membership reason; the door names no concept — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
