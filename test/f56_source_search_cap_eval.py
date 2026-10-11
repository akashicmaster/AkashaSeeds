#!/usr/bin/env python3
"""
F56-A2 — source.search hard ≤5000 examined-per-call (guest-surface cap).

The rest of Source-Layer batch 1 (at_seq stream ids; pool.ls 500/1000; op_pools stored member_count;
text_truncated; the `src` URI-shape guard; pool.scan 5000 cap) is already covered by
test/source_review_fixes_eval.py + test/source_deferred_fixes_eval.py. This pins the ONE tightening
F56-A2 requires beyond that: source.search must never examine more than 5000 entries in a single call,
even when a (guest) caller passes a larger budget — a caller pages the rest with the returned offset.

Run:  python test/f56_source_search_cap_eval.py     (exit 0 = all pass)
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
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_f56cap_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    nuc = k.manager.shared_nucleus
    core = nuc.core
    N = 5005                                          # just over the 5000 ceiling
    for i in range(N):
        key = nuc.put_atom("srcitem %d" % i,
                           {"concept": "source_item", "source": "source:src:z",
                            "source_record_id": "r%d" % i}, author="admin")
        core.add_to_collection("source:items", key)

    g = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create", "params": {}, "id": "gg"}, "network")
    gt = ((g or {}).get("result") or {}).get("session_token")

    def gsearch(data):
        r = k.dispatch({"jsonrpc": "2.0", "method": "source.search",
                        "params": {"session_token": gt, "data": data}, "id": "s"}, "network")
        return r if "error" in r else (r.get("result") or {})

    # ── a guest passing a huge budget examines AT MOST 5000, and gets a continuation ──
    r = gsearch({"q": "zzz_nomatch", "budget": 99999})
    check("source.search caps examined entries at 5000 even for budget=99999 (guest CPU bounded)",
          r.get("scanned") == 5000 and r.get("truncated") is True and r.get("next_offset") == 5000
          and r.get("total_candidates") == N, str({kk: r.get(kk) for kk in
          ("scanned", "truncated", "next_offset", "total_candidates")}))

    # ── the caller pages the remainder from the returned offset (no lost rows) ──
    r2 = gsearch({"q": "zzz_nomatch", "budget": 99999, "offset": r.get("next_offset")})
    check("the continuation offset pages the rest (remaining 5 examined, scan complete, not truncated)",
          r2.get("scanned") == (N - 5000) and r2.get("truncated") is False, str(r2.get("scanned")))

    # ── a small explicit budget is still honored below the cap (mechanism unchanged) ──
    r3 = gsearch({"q": "zzz_nomatch", "budget": 100})
    check("a below-cap budget is honored exactly (examines 100, pages on)",
          r3.get("scanned") == 100 and r3.get("truncated") is True and r3.get("next_offset") == 100,
          str(r3.get("scanned")))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — source.search examines at most 5000 entries per call regardless of the "
          "requested budget; a caller pages the rest with the returned offset. The guest CPU surface "
          "is bounded (F56-A2).")
    sys.exit(0)


if __name__ == "__main__":
    main()
