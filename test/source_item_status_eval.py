#!/usr/bin/env python3
"""
Directive 2026-10-03 item 5 — the public op for an item's status: `source.item.status pool= item= status=`.

The source engine is the single writer of an item's status, its `source:status:<s>` Set and the
`by_status` tallies (the source's and every pool's). Until now the only door was internal
(`_set_item_status`), so code outside the engine (`vlab.source.add`) wrote `status` straight into the
item's meta, and the pool tally drifted — caught and recounted at freeze, but drifted. This op is the
public form of the one door, gated `record` ON THE POOL. On a real cell, through the CLI and RPC:

  1. a status change moves, in one write: the item's meta, its status Set membership (old out, new in),
     the source tally and the pool's live tally — and the freeze's drift check finds nothing to fix.
     (The old-Set removal was broken in the internal door too — it removed from a different store than
     `_add_to_set` wrote, silently — so an item stayed in its old status Set; fixed with this op.)
  2. the same status twice changes nothing (`changed: false`);
  3. shape errors are refused (-32602): a status outside the vocabulary, an item not in the pool, an
     unknown pool; a call WITHOUT `pool=` is refused `out_of_scope` by the gate (the declared target);
  4. the gate: an identity holding `consumer` on the pool (read · run) is refused (`not_allowed` — the row
     may not record at all); one holding a row with `record` on that pool is admitted; on ANOTHER pool
     it is refused `out_of_scope`;
  5. it is a CLI command (`sys.cli_exec`), per the CLI-first convention;
  (The membership rule — what is an item — is `test/status_door_eval.py`; that only the engine
   writes an item's status is `test/owned_fields_eval.py`, which replaced this file's §6c.)

Run:  python test/source_item_status_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import shlex
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


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.lines = []

    def emit(self, r):
        self.lines.append(r.getMessage())


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.api import gate as G
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="srcst_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def raw(who, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": who, "data": data}, "id": "t"}, "internal")

    def d(method, data):
        r = raw("admin", method, data)
        return r if "error" in r else (r.get("result") or {})

    src = d("source.register", {"provider": "ev", "name": "evst", "rights": "CC0"}).get("source")
    d("source.acquire", {"source": src, "rule": "x", "id_field": "id",
                         "records": [{"id": "a1", "locator": "https://x/1.jpg"},
                                     {"id": "a2", "locator": "https://x/2.jpg"}]})
    pool = d("source.pool.create", {"name": "evst_p", "source": src, "rule": "all",
                                    "version": "v1"}).get("pool")
    other = d("source.pool.create", {"name": "evst_q", "source": src, "rule": "all",
                                     "version": "v1"}).get("pool")
    item = "source:item:evst:a1"
    for it in (item, "source:item:evst:a2"):
        d("source.pool.add", {"pool": pool, "id": it})
    d("source.pool.add", {"pool": other, "id": "source:item:evst:a2"})
    st0 = d("source.status", {"pool": pool})

    print("    1. one write moves every count")
    r = d("source.item.status", {"pool": pool, "item": item, "status": "missing"})
    check(f"[{shape}] the status changes (ACQUIRED → MISSING) and says what it was",
          r.get("status") == "MISSING" and r.get("was") == "ACQUIRED" and r.get("changed") is True, str(r))
    from lib.akasha import api as _api
    sc = _api.concept_class(k, "source")(k.manager.get_session("admin"))
    ik = sc._key(item)
    check(f"[{shape}] the item's meta says MISSING", (sc.cortex.get_meta(ik) or {}).get("status") == "MISSING")
    mem_new = ik in set(sc._members("source:status:missing"))
    mem_old = ik in set(sc._members("source:status:acquired"))
    check(f"[{shape}] its status Set moved: in source:status:missing, out of source:status:acquired",
          mem_new and not mem_old, "new=%s old=%s" % (mem_new, mem_old))
    st1 = d("source.status", {"pool": pool})
    b0, b1 = st0.get("by_status") or {}, st1.get("by_status") or {}
    check(f"[{shape}] the pool's tally moved one count (ACQUIRED {b0.get('ACQUIRED')}→{b1.get('ACQUIRED')}, "
          f"MISSING {b0.get('MISSING')}→{b1.get('MISSING')})",
          b1.get("ACQUIRED") == b0.get("ACQUIRED", 0) - 1 and b1.get("MISSING") == b0.get("MISSING", 0) + 1,
          "%s → %s" % (b0, b1))
    stS = d("source.status", {"source": src})
    check(f"[{shape}] the source's tally moved too (MISSING=1)",
          (stS.get("by_status") or {}).get("MISSING") == 1, str(stS.get("by_status")))
    root = logging.getLogger()
    cap = _Cap()
    root.addHandler(cap)
    _lvl = root.level
    root.setLevel(logging.INFO)
    try:
        fz = d("source.pool.freeze", {"pool": pool})
    finally:
        root.removeHandler(cap)
        root.setLevel(_lvl)
    check(f"[{shape}] the freeze's drift check finds nothing to recount (no `pool tally drift` line)",
          fz.get("status") == "FROZEN" and not any("pool tally drift" in ln for ln in cap.lines),
          str([ln for ln in cap.lines if "drift" in ln]))

    print("    2. idempotent")
    r2 = d("source.item.status", {"pool": pool, "item": item, "status": "MISSING"})
    check(f"[{shape}] the same status twice changes nothing", r2.get("changed") is False, str(r2))

    print("    3. shape errors, and the declared target")
    e1 = raw("admin", "source.item.status", {"pool": pool, "item": item, "status": "LOST"})
    e2 = raw("admin", "source.item.status", {"pool": other, "item": item, "status": "ACQUIRED"})
    e3 = raw("admin", "source.item.status", {"pool": "source:pool:nope:v1", "item": item,
                                             "status": "ACQUIRED"})
    e4 = raw("admin", "source.item.status", {"item": item, "status": "ACQUIRED"})
    check(f"[{shape}] a status outside the vocabulary is refused (-32602)",
          (e1.get("error") or {}).get("code") == -32602, str(e1)[:160])
    check(f"[{shape}] an item that is not a member of the pool is refused (-32602)",
          (e2.get("error") or {}).get("code") == -32602 and "not a member" in str(e2), str(e2)[:160])
    check(f"[{shape}] an unknown pool is refused (-32602)",
          (e3.get("error") or {}).get("code") == -32602, str(e3)[:160])
    check(f"[{shape}] a call with NO pool= is refused out_of_scope by the gate, naming the param",
          "error" in e4 and G.R_TARGET in str(e4["error"]) and "no pool=" in str(e4["error"]), str(e4)[:160])

    print("    4. the gate asks `record` on the pool")
    rows = G.idsets()
    rec_row = next((n for n, r in rows.items() if "record" in r.get("may", ()) and r.get("on") == "assigned"
                    and r.get("facts") is not False), "")
    for who in ("evst_consumer", "evst_writer"):
        d("user.add", {"user_id": who, "role": "user",
                       "passphrase": hashlib.sha256(b"pw-" + who.encode()).hexdigest()})
    G.assign("evst_consumer", "consumer", other)
    G.assign("evst_writer", rec_row, other)
    rc = raw("evst_consumer", "source.item.status", {"pool": other, "item": "source:item:evst:a2",
                                                     "status": "UNRESOLVED"})
    check(f"[{shape}] a `consumer` on the pool (read · run) is refused — it may not `record` anywhere "
          f"(`{G.R_ACTION}` at the boundary)",
          "error" in rc and G.R_ACTION in str(rc["error"]), str(rc)[:160])
    rw = raw("evst_writer", "source.item.status", {"pool": other, "item": "source:item:evst:a2",
                                                   "status": "UNRESOLVED"})
    check(f"[{shape}] `{rec_row}` on the pool (record) is admitted",
          "error" not in rw and (rw.get("result") or {}).get("status") == "UNRESOLVED", str(rw)[:200])
    rw2 = raw("evst_writer", "source.item.status", {"pool": pool, "item": item, "status": "ACQUIRED"})
    check(f"[{shape}] …and on ANOTHER pool it is refused out_of_scope",
          "error" in rw2 and G.R_TARGET in str(rw2["error"]), str(rw2)[:160])

    print("    5. a CLI command")
    cmd = "source.item.status pool=%s item=%s status=ACQUIRED" % (shlex.quote(pool), shlex.quote(item))
    from api.gateway import AkashaGateway
    gw = AkashaGateway(kernel_client=k)
    rcli = gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                        "params": {"session_token": "admin", "data": {"command": cmd}}, "id": "c"},
                       "local")
    rcli = rcli.get("result") if "error" not in rcli else rcli
    check(f"[{shape}] `{cmd.split()[0]} pool= item= status=` runs through the CLI parser",
          "error" not in rcli and "ACQUIRED" in json.dumps(rcli), str(rcli)[:200])


def main():
    print("=" * 78)
    print("source.item.status — the source engine's one door for an item's status, made public")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — `source.item.status pool= item= status=` moves the item's meta, its status "
          "Set and every tally in one write (no drift to recount), is idempotent, refuses bad shapes, "
          "is gated `record` on the pool (consumer refused, a record row admitted only on its own "
          "pool), and is a CLI command — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
