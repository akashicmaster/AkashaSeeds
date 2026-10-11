#!/usr/bin/env python3
"""
A VLAB ARTWORK IS COUNTED BY THE SOURCE ENGINE'S DOOR, NOT BY A STATUS WRITTEN AROUND IT (directive 2026-10-03, item 3, rev 3).

`vlab.source.add` used to put `status: METADATA_ONLY` into the artwork's meta and add it to `source:status:metadata_only`
itself. The engine's tally counts only a status change made through its one door (`source.item.status`), so a pool of vlab
artworks read `total: N` with every `by_status` bucket 0. The order now (rev 3): create the artwork with NO status, add it
to the pool, and call `source.item.status … status=METADATA_ONLY`; the door's error is returned, never swallowed. Held on a
real dispatcher:

  1. add an artwork to a pool whose tally is LIVE: the door answered `changed: true`, `source.status` has it in `total`
     and in exactly one `by_status` bucket
  2. `source.pool.freeze` logs NO drift line
  3. the mint writes no status and nothing to `source:status:metadata_only`; a LOCAL artwork (no Source-layer citizen)
     keeps its own mark
  4. the door's refusal is RETURNED by `vlab.source.add` (not swallowed, not replaced by a status written some other way)
  5. NO backfill of vlab's own: an artwork that was counted around the door (the old drift) is corrected by the engine's
     drift check — the freeze recounts it, logs the drift line once, and the sums add up

Run:  python app/test/vlab_artwork_status_eval.py     (exit 0 = all pass)
"""
import hashlib
import inspect
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, r):
        self.lines.append(r.getMessage())


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts._universal import UniversalConcept
    from app.concepts.vision_lab import VisionLabConcept
    from lib.akasha.concepts.source import SourceDataLayer
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_art_"))
    cap = _Cap()
    logging.getLogger().addHandler(cap)
    logging.getLogger().setLevel(logging.INFO)

    def raw(m, d):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": d}, "id": "t"}, "local") or {}

    def d(m, data):
        r = raw(m, data)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    raw("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})
    POOL = "source:pool:art:v1"
    d("source.pool.create", {"name": "art", "source": "", "rule": "t"})

    def tally(pool=POOL):
        st = d("source.status", {"pool": pool})
        return st.get("total"), dict(st.get("by_status") or {})

    print("\n  ── 1. an added artwork is counted, once, through the door ──")
    first = d("vlab.source.add", {"pool": POOL, "object_id": "o1", "image": "http://x/1.jpg", "title": "one"})
    # the tally of POOL is live now (the door adopted it); this second add is to a pool whose tally is LIVE
    second = d("vlab.source.add", {"pool": POOL, "object_id": "o2", "image": "http://x/2.jpg", "title": "two"})
    check("the add returns the door's answer, and it CHANGED the status (changed: true)",
          (second.get("status") or {}).get("changed") is True and (second.get("status") or {}).get("was") is None,
          str(second.get("status")))
    total, by = tally()
    check("`source.status` counts both in `total`", total == 2, str(total))
    check("…and each in EXACTLY ONE `by_status` bucket (METADATA_ONLY)",
          sum(by.values()) == 2 and by.get("METADATA_ONLY") == 2, str(by))
    for i in range(3, 6):
        d("vlab.source.add", {"pool": POOL, "object_id": "o%d" % i, "image": "http://x/%d.jpg" % i})
    total, by = tally()
    check("sum(by_status) == total after five adds", total == 5 and sum(by.values()) == 5, str((total, by)))

    print("\n  ── 2. the freeze finds no drift ──")
    cap.lines.clear()
    d("source.pool.freeze", {"pool": POOL})
    drift = [l for l in cap.lines if "pool tally drift" in l]
    total, by = tally()
    check("`source.pool.freeze` logs NO drift line", not drift, str(drift)[:160])
    check("…and the frozen tally still adds up", total == 5 and sum(by.values()) == 5, str((total, by)))

    print("\n  ── 3. the mint writes no status; a local artwork keeps its mark ──")
    src = inspect.getsource(VisionLabConcept.op_source_add)
    check("the status write is reached ONLY for a pool the engine does not know (`not engine_pool`): ad hoc vlab-private "
          "pools and local artworks, whose tally the door cannot move",
          'engine_pool = visibility == "public" and str(pool).startswith("source:pool:")' in src
          and 'if not engine_pool:' in src and src.count('meta["status"]') == 1, "")
    u = UniversalConcept(k.manager.get_session("admin"))
    adhoc = d("vlab.source.add", {"pool": "vc:scratch:v1", "object_id": "s1", "image": "http://x/s.jpg"})
    check("an ad hoc vlab-private pool (not `source:pool:…`) keeps its own mark and returns no door answer",
          (u._meta("source:artwork:cma:s1") or {}).get("status") == "METADATA_ONLY" and "status" not in adhoc, str(adhoc)[:120])
    d("vlab.source.add", {"pool": "source:pool:local_art:v1", "object_id": "L1", "image": "/tmp/x.png", "scheme": "local"})
    check("a LOCAL artwork (no Source-layer citizen) keeps its own status mark",
          (u._meta("source:artwork:local:l1") or {}).get("status") == "METADATA_ONLY")

    print("\n  ── 4. the door's refusal is returned ──")
    real = SourceDataLayer.op_item_status

    def refuse(self, pool, item, status):
        raise ValueError("the door refused (eval)")
    SourceDataLayer.op_item_status = refuse
    try:
        r = raw("vlab.source.add", {"pool": POOL.replace("v1", "v9"), "object_id": "x1", "image": "http://x/9.jpg"})
    finally:
        SourceDataLayer.op_item_status = real
    check("`vlab.source.add` returns the door's error (it does not swallow it or write the status another way)",
          "error" in r and "the door refused" in str(r), str(r)[:160])

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a vlab artwork is counted by the source engine's door (changed: true, total and exactly one "
          "bucket, no drift at the freeze), and the door's refusal is returned.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
