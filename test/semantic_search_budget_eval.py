#!/usr/bin/env python3
"""
A57 (R6) — semantic.search is bounded, so it can never become the writer's 50 s bottleneck.

Two bounds, on BOTH cell shapes:
  • a CANDIDATE cap (AKASHA_SEARCH_CANDIDATES, default 500): a 2,100-candidate corpus is scored down to
    the cap — semcache-plan (hot) atoms first — and returns `partial=true` with the best ranked so far,
    fast (< 1.5 s);
  • a TIME budget (AKASHA_SEARCH_BUDGET_S, default 10 s): a 0 s budget cuts after the first candidate,
    `partial=true`;
  • with both bounds lifted, a full pass returns `partial=false` (nothing is truncated when it fits).

Run:  python test/semantic_search_budget_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import sys
import tempfile
import time

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
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_ssbudget_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    sess = k.manager.get_session("admin")
    ctx = sess.local_cortex
    tensor = getattr(ctx, "tensor", None)
    nuc = k.manager.shared_nucleus
    # ~2,100 floor-tier candidates sharing tokens with the query so cosine > 0 (real ranked results).
    N = 2100
    for i in range(N):
        content = f"leaf specimen sample number {i}"
        vec = tensor.embed("", content, {}) if tensor else None
        key = hashlib.sha256(content.encode("utf-8")).hexdigest()
        nuc.core.put_chunk_raw(key, content, json.dumps({"semantic_vector": vec}),
                               "admin", "verified", time.time())
        nuc.core.put_chunk_access(key, ["scope:sys:universal"])

    def search(data, env=None):
        _saved = {}
        for kk, vv in (env or {}).items():
            _saved[kk] = os.environ.get(kk)
            os.environ[kk] = vv
        try:
            t0 = time.time()
            r = k.dispatch({"jsonrpc": "2.0", "method": "semantic.search",
                            "params": {"session_token": "admin", "data": data}, "id": "s"}, "local")
            return (r.get("result") or {}), time.time() - t0
        finally:
            for kk, vv in _saved.items():
                if vv is None:
                    os.environ.pop(kk, None)
                else:
                    os.environ[kk] = vv

    # A57-b — capture WARNING+INFO to prove the cap path is SILENT (no per-call spam) and the budget
    # path logs exactly one line.
    class _Cap(logging.Handler):
        def __init__(self):
            super().__init__(logging.INFO); self.lines = []

        def emit(self, r):
            try:
                self.lines.append(r.getMessage())
            except Exception:
                pass
    _root = logging.getLogger(); _cap = _Cap(); _root.addHandler(_cap); _lvl = _root.level
    _root.setLevel(logging.INFO)

    # 1. the candidate cap (default 500) truncates a 2,100-candidate query, fast, with ranked results
    res, dt = search({"query": "leaf specimen sample", "scan": "20000"})
    check(f"[{shape}] a 2,100-candidate query returns partial=true (candidate cap hit)",
          res.get("partial") is True, f"partial={res.get('partial')} candidates={res.get('candidates')}")
    check(f"[{shape}] A57-b the cap truncation is reason=cap and is NOT logged (no per-call spam)",
          res.get("partial_reason") == "cap"
          and not any("[semantic.search] partial" in ln for ln in _cap.lines),
          f"reason={res.get('partial_reason')} lines={[l for l in _cap.lines if 'partial' in l]}")
    check(f"[{shape}] the cap bounds the candidates scored (≈500, not 2,100)",
          0 < int(res.get("candidates", 0)) <= 520, f"candidates={res.get('candidates')}")
    check(f"[{shape}] it completes fast (< 1.5 s)", dt < 1.5, f"t={dt:.2f}s")
    check(f"[{shape}] it still returns the best-ranked results", len(res.get("results") or []) > 0,
          str(res.get("count")))

    # 2. the time budget: a 0 s budget cuts after the first candidate → partial=true, reason=budget,
    #    and it IS logged (one INFO — the rare, interesting case)
    _cap.lines.clear()
    res2, dt2 = search({"query": "leaf specimen sample", "scan": "20000"},
                       env={"AKASHA_SEARCH_BUDGET_S": "0", "AKASHA_SEARCH_CANDIDATES": "999999"})
    check(f"[{shape}] a 0 s budget returns partial=true reason=budget (time budget hit)",
          res2.get("partial") is True and res2.get("partial_reason") == "budget" and dt2 < 1.5,
          f"partial={res2.get('partial')} reason={res2.get('partial_reason')} t={dt2:.2f}s")
    check(f"[{shape}] A57-b a budget truncation IS logged (one INFO)",
          any("[semantic.search] partial" in ln and "reason=budget" in ln for ln in _cap.lines),
          str([l for l in _cap.lines if 'partial' in l])[:160])
    _root.removeHandler(_cap); _root.setLevel(_lvl)
    # A57-b — both truncations fed the Health counter (cap ≥ 1 from test 1, budget ≥ 1 from test 2)
    from lib.akasha.kernel import _SEARCH_PARTIAL
    check(f"[{shape}] A57-b the Health counter aggregates both reasons",
          _SEARCH_PARTIAL["cap"] >= 1 and _SEARCH_PARTIAL["budget"] >= 1, str(dict(_SEARCH_PARTIAL)))

    # 3. both bounds lifted → a full pass is NOT partial
    res3, _ = search({"query": "leaf specimen sample", "scan": "20000"},
                     env={"AKASHA_SEARCH_BUDGET_S": "600", "AKASHA_SEARCH_CANDIDATES": "999999"})
    check(f"[{shape}] with both bounds lifted the full pass is partial=false",
          res3.get("partial") is False and int(res3.get("candidates", 0)) >= N - 5,
          f"partial={res3.get('partial')} candidates={res3.get('candidates')}")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — semantic.search is bounded by a candidate cap and a time budget: a "
          "2,100-candidate query truncates to the best ranked so far with partial=true in under 1.5 s, "
          "a 0 s budget cuts immediately, and lifting both bounds restores the full non-partial pass — "
          "both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
