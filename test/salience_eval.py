#!/usr/bin/env python3
"""
Salience eval — the incremental per-atom meaning-density score.

Every atom carries meta['salience']: a running, weighted degree bumped on the write path
(put_link) and decremented on remove_link — never scanned or recomputed. "The denser the
meaning, the bigger the number." Readers (thesaurus shelf.list / view.atom, gap.scan) just
read it. A link credits BOTH endpoints (inbound to dst, half-weight outbound to src), scaled
by relation type (semantic = 1.0, weave mention = 0.5, structural sys: = 0.15).

  S1 inbound>outbound — a link bumps dst (referenced) more than src (referencing).
  S2 accumulates      — a hub referenced N times outscores a leaf referenced once.
  S3 rel weighting    — a semantic link contributes more density than a structural sys: link.
  S4 decrements       — remove_link lowers the score (kept current, not stale).
  S5 gap.scan reuse   — gap.scan reads meta['salience'] as importance (no per-atom link scan).

Run:  python test/salience_eval.py
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def main():
    print("\n  salience eval — incremental meaning-density score (bump on write, read-only after)\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_sal_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    cortex = k.manager.get_session("admin").local_cortex

    def sal(key):
        return float((cortex.get_meta(key) or {}).get("salience", 0.0) or 0.0)

    def mk(name, desc):
        return (d("def", {"name": name, "description": desc}) or {}).get("key")

    # A hub referenced by three atoms via a semantic relation.
    hub  = mk("concept:hub",  "a central idea many things point at")
    leaf = mk("concept:leaf", "a peripheral idea pointed at once")
    refs = [mk(f"concept:ref{i}", f"referrer number {i} of the hub concept") for i in range(3)]
    for r in refs:
        d("ln", {"src": r, "dst": hub, "rel": "calc:associated_with"})       # semantic → weight 1.0
    d("ln", {"src": refs[0], "dst": leaf, "rel": "calc:associated_with"})

    # S1 — the dst (hub, inbound) gains more than a src (referrer, outbound) per link.
    ref_out = sal(refs[1])          # only outbound: one link to hub (+ any weave)
    record("S1 in>out", sal(hub) > ref_out and sal(hub) > 0,
           f"hub(inbound)={sal(hub):.2f} > ref(outbound)={ref_out:.2f}")

    # S2 — accumulation: hub (3 inbound) outscores leaf (1 inbound).
    record("S2 accumulates", sal(hub) > sal(leaf) > 0,
           f"hub={sal(hub):.2f} > leaf={sal(leaf):.2f}")

    # S3 — relation weighting: a semantic link out-densifies a structural sys: link.
    sem  = mk("concept:sem",  "target reached by a semantic link")
    stru = mk("concept:stru", "target reached by a structural link")
    d("ln", {"src": refs[0], "dst": sem,  "rel": "thesaurus:related"})       # semantic 1.0
    d("ln", {"src": refs[0], "dst": stru, "rel": "sys:contains"})            # structural 0.15
    record("S3 rel weight", sal(sem) > sal(stru),
           f"semantic={sal(sem):.2f} > structural={sal(stru):.2f}")

    # S4 — remove_link decrements (the score stays current, not stale-high).
    before = sal(hub)
    d("ln.rm", {"src": refs[0], "dst": hub, "rel": "calc:associated_with"})
    after = sal(hub)
    record("S4 decrements", after < before,
           f"salience {before:.2f} → {after:.2f} after unlink")

    # S5 — gap.scan reads salience as its importance signal (referenced-but-thin hub surfaces).
    gs = d("gap.scan", {"limit": 20}) or {}
    rows = gs.get("gaps", gs.get("results", [])) if isinstance(gs, dict) else []
    hub_row = next((g for g in rows if g.get("key") == hub), None)
    record("S5 gap.scan", hub_row is not None and hub_row.get("importance", 0) > 0,
           f"hub in gap.scan={hub_row is not None}, importance={hub_row.get('importance') if hub_row else None}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the salience score is not tracking meaning-density correctly.")
        return 1
    print("\nRESULT: PASS — salience grows with density on the write path (inbound>outbound, "
          "accumulates, semantic>structural), decrements on unlink, and gap.scan reads it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
