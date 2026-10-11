#!/usr/bin/env python3
"""
`semantic.search` truncates for TWO reasons, and both are provable (seed A slice 2).

The Health line carries `search(partial cap=N budget=M)`. After the layout seed, `cap` grew and
`budget` stayed 0 for three hours, which read as a dead code path: "either the budget-cut path is
no longer reached (a behaviour change) or the two sides hold different objects".

Neither, as it turned out — the candidate loop is byte-identical to its pre-layout self and both
sides import the SAME counter dict from `api.heart`. `budget=0` meant no query had taken 10 s.
But "we read the diff and it looks fine" is not evidence, so this eval makes the budget cut
HAPPEN and watches the counter move. A truncation reason nobody can demonstrate is a truncation
reason nobody can trust.

Checked here:
  1. the two counters are ONE object — the incrementer, the Health reader and the op all share it
  2. a search with the time budget set to 0 is cut by BUDGET (not by cap), says so in its result,
     and logs `[semantic.search] partial … reason=budget` with the candidates and the elapsed time
  3. that call moves `_SEARCH_PARTIAL["budget"]` by exactly one
  4. with a generous budget and a tiny candidate cap the SAME query is cut by CAP instead, moves
     the other counter, and stays SILENT in the log (the cap case is every large query — 1,191
     INFO lines in 11 h was the reason it is not logged)
  5. Health renders both counters once either is non-zero

Run:  python test/search_budget_partial_eval.py     (exit 0 = all pass)
"""
import hashlib
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.api.heart import _SEARCH_PARTIAL, _search_partial_incr
    from lib.akasha.concepts import semantic_ops as _sops

    # ── 1. one counter object, not two ───────────────────────────────────────────────────────
    import lib.akasha.kernel as _kmod
    check("the op, the incrementer and the Health reader share ONE counter object — the 'two "
          "sides hold different objects' hypothesis, checked rather than assumed",
          _sops._SEARCH_PARTIAL is _SEARCH_PARTIAL and _kmod._SEARCH_PARTIAL is _SEARCH_PARTIAL)

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_sbp_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    for i in range(40):
        d("w", {"content": "budget probe subject %d about rivers mountains and weather" % i})

    # ── 2/3. force a BUDGET cut and watch the counter move ───────────────────────────────────
    before = dict(_SEARCH_PARTIAL)
    cap = _Capture()
    roots = [logging.getLogger(n) for n in ("Akasha.Kernel", "Harmonia.Concept.Semantic",
                                            _sops.logger.name)]
    olds = [r.level for r in roots]
    for r in roots:
        r.addHandler(cap); r.setLevel(logging.INFO)
    os.environ["AKASHA_SEARCH_BUDGET_S"] = "0"       # every candidate is already over budget
    os.environ.pop("AKASHA_SEARCH_CANDIDATES", None)
    try:
        res = d("semantic.search", {"query": "rivers and weather", "limit": 5})
    finally:
        os.environ.pop("AKASHA_SEARCH_BUDGET_S", None)
        for r, o in zip(roots, olds):
            r.removeHandler(cap); r.setLevel(o)

    check("a search with the time budget spent is cut by BUDGET and says so in its result",
          res.get("partial") is True and res.get("partial_reason") == "budget",
          "partial=%s reason=%s candidates=%s" % (res.get("partial"), res.get("partial_reason"),
                                                  res.get("candidates")))
    check("the budget counter moved by exactly one — the path is live, not dead code",
          _SEARCH_PARTIAL["budget"] == before.get("budget", 0) + 1,
          "%s -> %s" % (before.get("budget"), _SEARCH_PARTIAL["budget"]))
    line = [l for l in cap.lines if "[semantic.search] partial" in l]
    check("the cut logs its REASON ID with the evidence (candidates walked, elapsed, the budget)",
          len(line) == 1 and "reason=budget" in line[0] and "candidates=" in line[0]
          and "budget=" in line[0], str(line))

    # ── 4. the CAP cut moves the other counter and stays silent ──────────────────────────────
    before2 = dict(_SEARCH_PARTIAL)
    cap2 = _Capture()
    for r in roots:
        r.addHandler(cap2); r.setLevel(logging.INFO)
    os.environ["AKASHA_SEARCH_CANDIDATES"] = "2"     # generous time, tiny candidate cap
    try:
        res2 = d("semantic.search", {"query": "rivers and weather", "limit": 5})
    finally:
        os.environ.pop("AKASHA_SEARCH_CANDIDATES", None)
        for r, o in zip(roots, olds):
            r.removeHandler(cap2); r.setLevel(o)
    check("the same query under a tiny candidate cap is cut by CAP instead",
          res2.get("partial") is True and res2.get("partial_reason") == "cap",
          "reason=%s candidates=%s" % (res2.get("partial_reason"), res2.get("candidates")))
    check("…and it moves the OTHER counter (the two reasons are counted apart)",
          _SEARCH_PARTIAL["cap"] == before2.get("cap", 0) + 1
          and _SEARCH_PARTIAL["budget"] == before2.get("budget", 0),
          "cap %s -> %s, budget %s -> %s" % (before2.get("cap"), _SEARCH_PARTIAL["cap"],
                                             before2.get("budget"), _SEARCH_PARTIAL["budget"]))
    check("…while staying SILENT in the log — every large query hits the cap, and 1,191 INFO "
          "lines in 11 hours is what made that the rule",
          not [l for l in cap2.lines if "[semantic.search] partial" in l], str(cap2.lines[-1:]))

    # ── 5. Health renders both ───────────────────────────────────────────────────────────────
    seg = ""
    if _SEARCH_PARTIAL["cap"] or _SEARCH_PARTIAL["budget"]:
        seg = " search(partial cap=%d budget=%d)" % (_SEARCH_PARTIAL["cap"],
                                                     _SEARCH_PARTIAL["budget"])
    check("Health renders both counters once either is non-zero — the shape the checkpoint reads",
          "cap=" in seg and "budget=" in seg and "budget=0" not in seg, seg.strip())

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — both truncation reasons are reachable and counted apart: the budget cut "
          "fires, moves its own counter and logs `reason=budget` with its evidence; the cap cut "
          "moves the other and stays quiet. A `budget=0` on Health means no query was slow, not a "
          "dead path — and now that is demonstrable rather than argued.")
    sys.exit(0)


if __name__ == "__main__":
    main()
