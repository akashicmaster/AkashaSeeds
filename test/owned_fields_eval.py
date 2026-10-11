#!/usr/bin/env python3
"""
Engine-owned fields — the store refuses any writer but the owning engine (the purge order, §1.4).

The source engine alone writes an item's `status` (an item = any member of a pool's member Set,
whatever its concept) and a pool's `by_status`. It declares both (`owned_fields.declare`); every
backend checks a meta write against the declarations on the caller's thread. This replaces
`source_item_status_eval` §6c: drift written around the door is no longer something to correct —
it cannot be written.

  1. AT THE STORE, both backends (SQLite, Silica), through every meta-writing primitive
     (`put_chunk_raw`, `update_meta`, and Silica's `write_atom`):
     a. a non-engine write that changes a member's `status` is refused — the reason names the field,
        the atom and the owning engine;
     b. the same write inside `writing_as("source")` passes;
     c. a pool's `by_status` is owned the same way (scope: the reserved concept `source_pool`);
     d. scope holds: `status` on an atom that is in no pool member Set is anyone's; a write that
        leaves an owned field as it was passes (owning a field is owning its changes);
  2. ON A CELL, both cell shapes:
     a. the door's write passes;
     b. a write by another model (a plain `UniversalConcept.set_meta`, the path a model took when it
        wrote `status` itself) is refused, and the item is unchanged;
     c. after a random sequence of door writes over several members, `sum(by_status) == total`
        after every one;
  3. the API publishes the declarations (`lib.akasha.api.fields.owned()`).

Run:  python test/owned_fields_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import random
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


def _refused(fn):
    from lib.akasha.owned_fields import OwnedFieldRefused
    try:
        fn()
    except OwnedFieldRefused as exc:
        return str(exc)
    return ""


def store_level(name, core):
    print(f"\n  ── 1. at the store: {name} ──")
    import lib.akasha.concepts.source  # noqa: F401 — the engine's declarations
    from lib.akasha.owned_fields import writing_as
    item = "evof_item_" + name
    plain = "evof_plain_" + name
    pool = "evof_pool_" + name
    core.put_chunk_raw(item, "an item", json.dumps({"concept": "eval_artwork", "status": "METADATA_ONLY"}),
                       "admin", "verified", 1.0)
    core.put_chunk_raw(plain, "not an item", json.dumps({"concept": "eval_run", "status": "RUNNING"}),
                       "admin", "verified", 1.0)
    with writing_as("source"):
        core.put_chunk_raw(pool, "a pool", json.dumps({"concept": "source_pool", "by_status": {}}),
                           "admin", "verified", 1.0)
    core.add_to_collection("source:pool:evof:v1:members", item)

    why = _refused(lambda: core.put_chunk_raw(
        item, "an item", json.dumps({"concept": "eval_artwork", "status": "ACQUIRED"}),
        "admin", "verified", 1.0))
    check(f"[{name}] put_chunk_raw: a non-engine change of a MEMBER's status is refused, naming the "
          f"field, the atom and the owner",
          "'status'" in why and item in why and "source engine" in why, why[:150])
    why2 = _refused(lambda: core.update_meta(item, {"concept": "eval_artwork", "status": "MISSING"}))
    check(f"[{name}] update_meta: refused the same way", "'status'" in why2, why2[:100])
    if hasattr(core, "write_atom"):
        why3 = _refused(lambda: core.write_atom(
            item, "an item", json.dumps({"concept": "eval_artwork", "status": "WITHDRAWN"}),
            "admin", "verified", 1.0))
        check(f"[{name}] write_atom: refused the same way", "'status'" in why3, why3[:100])
    check(f"[{name}] …and the member is unchanged",
          json.loads(core.get_chunk_raw(item)["meta"]).get("status") == "METADATA_ONLY")

    with writing_as("source"):
        core.update_meta(item, {"concept": "eval_artwork", "status": "ACQUIRED"})
    check(f"[{name}] inside writing_as(\"source\") the same change passes",
          json.loads(core.get_chunk_raw(item)["meta"]).get("status") == "ACQUIRED")

    whyp = _refused(lambda: core.update_meta(pool, {"concept": "source_pool",
                                                    "by_status": {"ACQUIRED": 9}}))
    check(f"[{name}] a pool's by_status (concept source_pool) is owned: a non-engine change is refused",
          "'by_status'" in whyp, whyp[:100])

    ok_plain = not _refused(lambda: core.update_meta(plain, {"concept": "eval_run", "status": "DONE"}))
    check(f"[{name}] scope: `status` on an atom in no pool member Set is anyone's",
          ok_plain and json.loads(core.get_chunk_raw(plain)["meta"]).get("status") == "DONE")
    same = not _refused(lambda: core.update_meta(item, {"concept": "eval_artwork", "status": "ACQUIRED",
                                                       "title": "renamed"}))
    check(f"[{name}] a write that leaves the owned field as it was passes (other fields are the "
          f"writer's)", same and json.loads(core.get_chunk_raw(item)["meta"]).get("title") == "renamed")


def cell_level(series, shape):
    print(f"\n  ── 2. on a cell: {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="evof_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def raw(method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "internal")

    def d(method, data):
        r = raw(method, data)
        return r if "error" in r else (r.get("result") or {})

    src = d("source.register", {"provider": "ev", "name": "evof", "rights": "CC0"}).get("source")
    pool = d("source.pool.create", {"name": "evof_p", "source": src, "rule": "all",
                                    "version": "v1"}).get("pool")
    members = []
    for i in range(4):
        key = (d("w", {"content": "owned-fields eval member %d (%s)" % (i, shape),
                       "scope": "universal"}) or {}).get("key")
        d("source.pool.add", {"pool": pool, "id": key})
        members.append(key)

    r0 = raw("source.item.status", {"pool": pool, "item": members[0], "status": "ACQUIRED"})
    check(f"[{shape}] the door's write passes", "error" not in r0, str(r0)[:150])

    from lib.akasha import api as _api
    from lib.akasha.concepts._universal import UniversalConcept
    other = UniversalConcept(k.manager.get_session("admin"))
    sc = _api.concept_class(k, "source")(k.manager.get_session("admin"))
    why = _refused(lambda: other.set_meta(members[0], "status", "MISSING"))
    check(f"[{shape}] another model writing the member's status itself is refused (the path that "
          f"drifted the tally)", "'status'" in why and "source engine" in why, why[:150])
    check(f"[{shape}] …and the item is unchanged",
          (sc.cortex.get_meta(members[0]) or {}).get("status") == "ACQUIRED")

    rng = random.Random(1003)
    ok_all, seen = True, []
    from lib.akasha.concepts.source import ITEM_STATUS
    for step in range(30):
        m = rng.choice(members)
        s = rng.choice(ITEM_STATUS)
        r = raw("source.item.status", {"pool": pool, "item": m, "status": s})
        st = d("source.status", {"pool": pool})
        tot = int(st.get("total") or 0)
        sm = sum(int(v) for v in (st.get("by_status") or {}).values())
        seen.append((sm, tot))
        if "error" in r:
            ok_all = False
            break
    # every member has a status once each was written at least once; until then the unwritten ones
    # are members with no status, which no bucket counts — the sum equals the members that have one
    written = {members[0]}
    rng = random.Random(1003)
    expect_ok = True
    for step, (sm, tot) in enumerate(seen):
        written.add(rng.choice(members))
        rng.choice(ITEM_STATUS)
        if sm != len(written):
            expect_ok = False
    for m in members:
        raw("source.item.status", {"pool": pool, "item": m, "status": "ACQUIRED"})
    st = d("source.status", {"pool": pool})
    check(f"[{shape}] after every one of 30 random door writes the tally counts exactly the members "
          f"that have a status, and once all have one, sum(by_status) == total",
          ok_all and expect_ok and sum(int(v) for v in (st.get("by_status") or {}).values())
          == int(st.get("total") or 0) == len(members),
          "steps=%d last=%s final=%s" % (len(seen), seen[-1:], st.get("by_status")))


def main():
    print("=" * 78)
    print("Engine-owned fields: the store refuses any writer but the owning engine")
    print("=" * 78)
    from lib.akasha.backends.sqlite import SQLiteBackend
    from lib.akasha.backends.silica_backend import SilicaBackend
    store_level("sqlite", SQLiteBackend(os.path.join(tempfile.mkdtemp(prefix="evof_sq_"), "t.db")))
    store_level("silica", SilicaBackend(os.path.join(tempfile.mkdtemp(prefix="evof_si_"), "t.db")))
    cell_level("thesaurus", "nucleus cell")
    cell_level("seeds", "single-store cell")

    print("\n  ── 3. the API publishes it ──")
    from lib.akasha.api import fields as F
    decl = F.owned()
    check("lib.akasha.api.fields.owned() lists the source engine's two fields with their scopes",
          {(x["owner"], x["field"]) for x in decl} >= {("source", "status"), ("source", "by_status")},
          str(decl))
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — the source engine's `status` (on any pool member) and `by_status` (on a pool) "
          "are refused to every other writer at the store, on both backends and through every "
          "meta-writing primitive, with the field and its owner in the reason; the door's writes pass "
          "and keep sum(by_status) == total; the API lists the declarations.")
    sys.exit(0)


if __name__ == "__main__":
    main()
