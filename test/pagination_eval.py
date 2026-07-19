#!/usr/bin/env python3
"""
pagination eval — the shared cursor page envelope.

One `paginate()` gives every list surface the same envelope so all clients page
identically (offset cursor → next_cursor / prev_cursor / has_more / total).

  PG1 envelope shape   — window + page dict with the documented keys.
  PG2 walk forward     — following next_cursor visits every item exactly once.
  PG3 has_more/total   — has_more true until the last window; total constant.
  PG4 prev_cursor      — set on later pages, None on the first.
  PG5 unbounded        — limit<=0 returns the whole remaining list, no next_cursor.
  PG6 defaults/clamp   — unspecified → default; positive over max clamps.

Run:  python test/pagination_eval.py
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def main():
    print("\n  pagination eval — shared cursor page envelope\n")
    from lib.akasha.pagination import paginate

    items = list(range(137))

    # PG1 — envelope shape.
    win, page = paginate(items, limit=20, cursor=None)
    keys = {"limit", "offset", "total", "count", "has_more", "next_cursor", "prev_cursor"}
    record("PG1 envelope shape",
           win == list(range(20)) and keys <= set(page) and page["total"] == 137
           and page["count"] == 20 and page["offset"] == 0,
           f"page={page}")

    # PG2 — walk forward via next_cursor visits each item once.
    seen, cursor, pages = [], None, 0
    while True:
        w, p = paginate(items, limit=20, cursor=cursor)
        seen.extend(w); pages += 1
        if not p["has_more"]:
            break
        cursor = p["next_cursor"]
        if pages > 100:
            break
    record("PG2 walk forward", seen == items and pages == 7,
           f"visited={len(seen)} pages={pages}")

    # PG3 — has_more true until last; total constant.
    _, p0 = paginate(items, 20, "0")
    _, pLast = paginate(items, 20, "120")   # 120..136 = 17 items, last page
    record("PG3 has_more/total",
           p0["has_more"] and not pLast["has_more"]
           and p0["total"] == pLast["total"] == 137 and pLast["count"] == 17,
           f"first.has_more={p0['has_more']} last.has_more={pLast['has_more']} last.count={pLast['count']}")

    # PG4 — prev_cursor None on first page, set later.
    _, pf = paginate(items, 20, "0")
    _, pm = paginate(items, 20, "40")
    record("PG4 prev_cursor", pf["prev_cursor"] is None and pm["prev_cursor"] == "20",
           f"first.prev={pf['prev_cursor']} mid.prev={pm['prev_cursor']}")

    # PG5 — unbounded (limit<=0) returns the whole remaining list, no next.
    w5, p5 = paginate(items, limit=0, cursor="100")
    record("PG5 unbounded", w5 == list(range(100, 137)) and p5["next_cursor"] is None and not p5["has_more"],
           f"count={p5['count']} next={p5['next_cursor']}")

    # PG6 — defaults + clamp.
    _, pd = paginate(items, limit=None)                 # default 20
    _, pc = paginate(items, limit=500, max_limit=100)   # clamp to 100
    record("PG6 defaults/clamp", pd["limit"] == 20 and pc["limit"] == 100,
           f"default={pd['limit']} clamped={pc['limit']}")

    # ── Kernel integration: a general list command carries the page envelope ─────
    import tempfile, hashlib
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_pg_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    # 25 atoms into one set.
    for i in range(25):
        a = d("w", {"content": f"member number {i:02d}"})
        d("set.add", {"name": "bigset", "id": a["key"]})

    p1 = d("set.ls", {"name": "bigset", "limit": 10})
    pg1 = p1.get("page", {}) if isinstance(p1, dict) else {}
    record("PG7 kernel envelope",
           len(p1.get("members", [])) == 10 and pg1.get("total") == 25
           and pg1.get("has_more") is True and pg1.get("next_cursor") == "10",
           f"count={len(p1.get('members', []))} total={pg1.get('total')} next={pg1.get('next_cursor')}")

    # Walk with the cursor: page 2 (10–19), page 3 (20–24, last).
    p2 = d("set.ls", {"name": "bigset", "limit": 10, "cursor": pg1.get("next_cursor")})
    pg2 = p2.get("page", {})
    p3 = d("set.ls", {"name": "bigset", "limit": 10, "cursor": pg2.get("next_cursor")})
    pg3 = p3.get("page", {})
    record("PG8 cursor walk",
           len(p2.get("members", [])) == 10 and pg2.get("prev_cursor") == "0"
           and len(p3.get("members", [])) == 5 and pg3.get("has_more") is False,
           f"p2={len(p2.get('members', []))} p3={len(p3.get('members', []))} p3.has_more={pg3.get('has_more')}")

    # PG9 — onto.dump (admin) modes now carry the envelope over a consistent sorted list.
    for i in range(15):
        d("def", {"name": f"pgns:item:{i:02d}", "description": f"item {i}"})
    od = d("onto.dump", {"mode": "aliases", "pattern": "pgns:item:%", "limit": 10})
    odp = od.get("page", {}) if isinstance(od, dict) else {}
    od2 = d("onto.dump", {"mode": "aliases", "pattern": "pgns:item:%", "limit": 10,
                          "cursor": odp.get("next_cursor")})
    aliases_pg1 = [it["alias"] for it in od.get("items", [])]
    aliases_pg2 = [it["alias"] for it in od2.get("items", [])]
    # 15 total, page1=10 (sorted), page2=5, no overlap (consistent global sort).
    record("PG9 onto.dump paged",
           odp.get("total") == 15 and len(aliases_pg1) == 10 and len(aliases_pg2) == 5
           and not (set(aliases_pg1) & set(aliases_pg2)),
           f"total={odp.get('total')} p1={len(aliases_pg1)} p2={len(aliases_pg2)} overlap={bool(set(aliases_pg1)&set(aliases_pg2))}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
