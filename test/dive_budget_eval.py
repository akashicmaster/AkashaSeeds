#!/usr/bin/env python3
"""
Dive time-budget eval (F19b) — the wall-clock bound on generate_view enrichment.

Deterministic: inject a per-signpost delay into _build_signpost, then dive a hub with many links
under a small AKASHA_DIVE_BUDGET and assert the view returns partial (never hangs, never raises)
with the truncated contract + exactly one WARNING; a disabled budget (0) is identical to today; and
the slow-signpost INFO instrument fires and names the edge.

Run:  python test/dive_budget_eval.py     (exit 0 = all pass)
"""
import hashlib
import logging
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.records = []
    def emit(self, r):
        self.records.append(r.getMessage())


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.consciousness import ConsciousnessEngine
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_dive_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # ── build a hub with 30 links ──────────────────────────────────────────────────
    hub = (d("w", {"text": "the dive hub"}) or {}).get("key")
    for i in range(30):
        nk = (d("w", {"text": f"neighbour number {i}"}) or {}).get("key")
        d("ln", {"src": hub, "dst": nk, "rel": "calc:associated_with"})

    sess = k.manager.get_session("admin")
    cons = sess.consciousness
    cap = _Capture()
    _clog = logging.getLogger("Harmonia.Consciousness")     # the consciousness.py logger
    _clog.addHandler(cap)
    _clog.setLevel(logging.INFO)

    _orig_build = ConsciousnessEngine._build_signpost

    # ── (2) trip test — 0.5 s/signpost, budget 2 s → partial view, one WARNING ───────
    def _slow05(self, *a, **kw):
        time.sleep(0.5)
        return _orig_build(self, *a, **kw)
    ConsciousnessEngine._build_signpost = _slow05
    cap.records.clear()
    t0 = time.monotonic()
    view = cons.generate_view(hub, budget_s=2.0)
    elapsed = time.monotonic() - t0
    warns = [m for m in cap.records if "budget exceeded" in m]
    check("(2) tripped dive returns in < 3 s (never hangs)", elapsed < 3.0, f"{elapsed:.1f}s")
    check("(2) partial view: truncated=True + truncated_phase=signpost-build + budget_s",
          view.get("truncated") is True and view.get("truncated_phase") == "signpost-build"
          and view.get("budget_s") == 2.0, str({x: view.get(x) for x in ("truncated", "truncated_phase", "budget_s")}))
    check("(2) keeps what is built (≥ 1 signpost present)", len(view.get("signposts", [])) >= 1,
          str(len(view.get("signposts", []))))
    check("(2) exactly ONE WARNING in the [dive] budget-exceeded format",
          len(warns) == 1 and "phase=signpost-build" in warns[0] and "focus=" in warns[0], str(warns))

    # ── (3) budget 0 → no deadline, no truncated field (identical to today) ──────────
    cap.records.clear()
    view0 = cons.generate_view(hub, budget_s=0)
    check("(3) budget_s=0 disables the deadline — no 'truncated' field",
          "truncated" not in view0 and view0.get("type") == "atom", str(view0.get("truncated")))
    check("(3) budget_s=0 emits no budget WARNING", not any("budget exceeded" in m for m in cap.records))

    # ── (6) slow-signpost INFO fires and names the edge (delay > 1 s) ────────────────
    def _slow12(self, *a, **kw):
        time.sleep(1.2)
        return _orig_build(self, *a, **kw)
    ConsciousnessEngine._build_signpost = _slow12
    cap.records.clear()
    # a small hub so 1.2 s builds don't run long; budget high so it doesn't trip first
    small = (d("w", {"text": "small dive hub"}) or {}).get("key")
    for i in range(2):
        nk = (d("w", {"text": f"small nbr {i}"}) or {}).get("key")
        d("ln", {"src": small, "dst": nk, "rel": "calc:associated_with"})
    cons.generate_view(small, budget_s=30.0)
    slow_lines = [m for m in cap.records if "slow signpost" in m]
    check("(6) slow-signpost INFO fires (build > 1 s) and names the link + rel",
          len(slow_lines) >= 1 and "link=" in slow_lines[0] and "rel=" in slow_lines[0], str(slow_lines[:1]))

    ConsciousnessEngine._build_signpost = _orig_build

    # ── (5) collection view — a mega-set is budgeted (member loop stops, does not enumerate all) ──
    from lib.akasha.consciousness import CosmosMapper
    _orig_nd = CosmosMapper.calculate_nd.__func__
    for i in range(30):
        mk = (d("w", {"text": f"set member {i}"}) or {}).get("key")
        d("set.add", {"name": "bigset", "id": mk})
    def _slow_nd(cls, *a, **kw):
        time.sleep(0.1)
        return _orig_nd(cls, *a, **kw)
    CosmosMapper.calculate_nd = classmethod(_slow_nd)
    cap.records.clear()
    cview = cons.generate_view("bigset", budget_s=1.0)
    CosmosMapper.calculate_nd = classmethod(_orig_nd)
    cwarn = [m for m in cap.records if "budget exceeded" in m]
    check("(5) mega-set collection view is budgeted (truncated, does not enumerate all members)",
          cview.get("type") == "collection" and cview.get("truncated") is True
          and cview.get("truncated_phase") == "collection-members"
          and len(cview.get("signposts", [])) < 30 and len(cwarn) == 1,
          f"members_shown={len(cview.get('signposts', []))}, warns={len(cwarn)}")

    # ── (1) default behaviour unchanged — a normal dive has no truncated field ───────
    cap.records.clear()
    normal = cons.generate_view(small)      # env default budget (10 s), fast build → no trip
    check("(1) normal dive returns with no 'truncated' field (default behaviour unchanged)",
          "truncated" not in normal and normal.get("type") == "atom")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — dive budget: a pathological dive returns a partial view (truncated contract + one "
          "WARNING) instead of hanging; budget=0 is a no-op; the slow-signpost instrument names the edge.")
    sys.exit(0)


if __name__ == "__main__":
    main()
