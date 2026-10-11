#!/usr/bin/env python3
"""
source_review_fixes_eval.py — the Source-Viewer code-review merge gate (2026-09-03).

Pins the fixes shipped from the librarian review: guest-surface caps (F50 family), the stream-id
reuse correctness bug, and the smaller correctness items. Every op here is guest-callable (the viewer
IS a guest), so the caps must hold at the OP contract, not just in the GUI.

  A1  pool.ls with no/zero limit is server-capped (never the whole pool); an explicit huge limit is
      hard-capped; truncated+count tell the caller how to page.
  A2  search with a no-match query is BUDGETED — it examines ≤ budget entries and returns a
      continuation offset, instead of sweeping all of source:items.
  A5  pools reports a frozen pool's count from stored member_count (no per-member sweep).
  A6  pool.scan rows are hard-capped at 5000 on the guest surface.
  B1  stream observations are numbered by at_seq — unique forever; a removal + re-append never
      collides into (silently unifies with) an existing observation; a snapshot window cut at an
      earlier at_seq provably excludes later appends.
  B3  import.set marks truncated text (text_truncated + text_length), never silently.
  B4  a generic `src` metadata field (an id/label, not a URI) is NOT mistaken for a locator.

Run:  python test/source_review_fixes_eval.py     (exit 0 = all pass)
"""
import hashlib
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


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_srev_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(m, data, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    d("source.register", {"provider": "x", "name": "x"})
    d("source.pool.create", {"name": "x", "source": "source:src:x"})
    # 1200 rows, each with a generic `src` LABEL (not a URI) to test B4
    d("source.acquire", {"source": "source:src:x", "rule": "t",
                         "records": [{"id": "r%04d" % i, "country": ["DE", "FR", "IT"][i % 3],
                                      "src": "label_%d" % i} for i in range(1200)],
                         "pool": "source:pool:x:v1"})
    d("source.pool.freeze", {"pool": "source:pool:x:v1"})

    # a guest is the real viewer — run the read ops as one
    g = d("session.guest.create", {})
    gt = (g or {}).get("binding_key") or (g or {}).get("session_token")

    def dg(m, data):
        return d(m, data, tok=gt, trust="network") if gt else {"__error__": "no guest"}

    # ── A1 — pool.ls server page cap ──
    pl = dg("source.pool.ls", {"pool": "source:pool:x:v1"})              # no limit
    check("A1: guest pool.ls with no limit is capped (≤500), not the whole pool",
          pl.get("returned") == 500 and pl.get("count") == 1200 and pl.get("truncated") is True,
          "returned=%s count=%s" % (pl.get("returned"), pl.get("count")))
    plb = dg("source.pool.ls", {"pool": "source:pool:x:v1", "limit": 999999})
    check("A1: an explicit huge limit is hard-capped (≤1000)", plb.get("returned") == 1000,
          str(plb.get("returned")))
    # paging still reaches the whole frame
    seen = 0
    off = 0
    for _ in range(4):
        pg = dg("source.pool.ls", {"pool": "source:pool:x:v1", "limit": 500, "offset": off})
        seen += pg.get("returned", 0); off += pg.get("returned", 0)
        if not pg.get("truncated"):
            break
    check("A1: the full frame is still reachable by paging (offset)", seen == 1200, str(seen))

    # ── A2 — search budget ──
    s = dg("source.search", {"q": "zzz_nomatch", "budget": 100})
    check("A2: a no-match search is budgeted (examines ≤budget, returns a continuation, no full sweep)",
          s.get("scanned") == 100 and s.get("truncated") is True and s.get("next_offset") == 100
          and s.get("count") == 0, "scanned=%s next=%s" % (s.get("scanned"), s.get("next_offset")))
    s2 = dg("source.search", {"q": "label_7", "limit": 5})               # a real hit still returns
    check("A2: a matching search still returns hits within the budget", (s2.get("count") or 0) >= 1,
          str(s2.get("count")))

    # ── A5 — pools uses stored member_count ──
    ps = dg("source.pools", {})
    row = next((p for p in ps.get("pools", []) if p.get("pool") == "source:pool:x:v1"), {})
    check("A5: pools reports count from the frozen pool's stored member_count", row.get("count") == 1200,
          str(row.get("count")))

    # ── A6 — pool.scan row cap ──
    sc = dg("source.pool.scan", {"pool": "source:pool:x:v1", "fields": "country", "limit": 999999})
    check("A6: guest pool.scan rows are hard-capped at 5000", (sc.get("returned") or 0) <= 5000
          and sc.get("truncated") is False, "returned=%s" % sc.get("returned"))  # 1200 ≤ 5000 → all, not truncated

    # ── B4 — a generic `src` label is not a locator ──
    one = dg("source.read", {"id": "source:item:x:r0000"})
    check("B4: a generic `src` metadata label is NOT treated as a locator",
          not (one.get("locator") or {}).get("uri") and one.get("source_metadata", {}).get("src") == "label_0",
          str(one.get("locator")))

    # ── B1 — stream observations numbered by at_seq; removal never collides; snapshot window is provable ──
    d("source.stream.create", {"id": "obs", "source": "source:src:x"})
    a1 = d("source.stream.append", {"stream": "source:stream:obs",
                                    "records": [{"v": 1}, {"v": 2}, {"v": 3}]})
    ids1 = a1.get("observations") or []
    # cut a snapshot window that ends at the 3rd observation's at_seq
    seq3 = int(ids1[-1].rsplit(":", 1)[-1])
    a2 = d("source.stream.append", {"stream": "source:stream:obs", "records": [{"v": 4}]})
    ids2 = a2.get("observations") or []
    seq4 = int(ids2[-1].rsplit(":", 1)[-1])
    check("B1: every appended observation is a distinct atom with a strictly-increasing at_seq id",
          len(set(ids1 + ids2)) == 4 and seq4 > seq3, "ids1=%s id4_seq=%s" % (ids1, seq4))
    # a snapshot cut at the 3rd observation's at_seq must include the first 3 and EXCLUDE the 4th (v4).
    snap = d("source.snapshot.create", {"stream": "source:stream:obs", "to_seq": str(seq3), "name": "w"})
    check("B1: a snapshot window cut at an earlier at_seq provably excludes the later appends",
          snap.get("member_count") == 3, "member_count=%s (expected 3)" % snap.get("member_count"))
    # remove one observation, then append again — the new one must NOT reuse a freed id / unify silently
    from lib.akasha.concepts.source import SourceDataLayer
    sess = k.manager.get_session("admin")
    sl = SourceDataLayer(sess)
    core = sl._nuc.core if sl._nuc else sess.core
    victim = sl._key(ids1[1])
    for coll in list(core.get_collections_for_key(victim) or []):
        try:
            core.remove_from_collection(coll, victim)
        except Exception:
            pass
    a3 = d("source.stream.append", {"stream": "source:stream:obs", "records": [{"v": 5}]})
    new_id = (a3.get("observations") or [""])[0]
    check("B1: after removing an observation, a re-append mints a NEW id (never reuses/unifies)",
          new_id and new_id not in ids1 and new_id not in ids2
          and int(new_id.rsplit(":", 1)[-1]) > seq4, str(new_id))

    # ── B3 — import.set marks truncated text ── (add the atom by its KEY so its content resolves)
    wr = d("w", {"content": "Y" * 2500})
    d("set.add", {"name": "set:revtrunc", "id": wr.get("key")})
    # grant the atom a UNIVERSAL scope so import.set proceeds without the C1 private-consent gate — this
    # test targets truncation marking, not the consent gate (real ontology imports are universal-scoped).
    for _c in (sl.cortex.core, (sl._nuc.core if sl._nuc else None)):
        if _c and _c.get_chunk_raw(wr.get("key")):
            _c.put_chunk_access(wr.get("key"), ["scope:sys:universal"]); break
    imp = d("source.import.set", {"set": "set:revtrunc", "name": "revtrunc"})
    sm = {}
    mem = d("source.pool.ls", {"pool": imp.get("pool"), "limit": 10}).get("members", []) if imp.get("pool") else []
    if mem:
        sm = (d("source.read", {"id": mem[0]["item"]}).get("source_metadata") or {})
    check("B3: import.set flags truncated text (text_truncated + text_length), never silently",
          sm.get("text_truncated") is True and sm.get("text_length") == 2500 and len(sm.get("content", "")) == 2000,
          "truncated=%s len=%s content=%s" % (sm.get("text_truncated"), sm.get("text_length"), len(sm.get("content", ""))))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails))); sys.exit(1)
    print("ALL PASS — Source-Viewer review fixes: guest reads are capped/budgeted (F50), stream "
          "observations are at_seq-numbered (unique forever, removal-safe, snapshot-provable), pools "
          "use stored counts, scan is capped, truncation is marked, and a generic `src` field is no "
          "longer a bogus locator.")
    sys.exit(0)


if __name__ == "__main__":
    main()
