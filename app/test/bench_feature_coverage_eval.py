#!/usr/bin/env python3
"""
A41/A42 — the feature corpus covers the WHOLE pool, train needs a complete run, promote is visible.

The v-directive symptom: `[vlab] run.execute … sources=100 observed=0 skipped=100` — a resumed run
never advanced past the first 100 sources (the cap was spent on already-observed skips), and b3 ran a
single `limit=100` chunk then sealed, so the corpus never grew past one chunk. And b5's promote left
no log line and no axis record.

This eval proves the fixes on both cell shapes (a synthetic 3-class × 10 pool, mock-observable refs):
  A41.1  `execute limit=4` twice → the second observes 4 NEW sources (skipped≥4), `remaining` drops by 4.
  A41.2  `execute` with no limit (chunk=4 tuning knob) on a FRESH 30-source run → chunks=8, remaining=0,
         complete=true (whole pool is the DEFAULT — amended 2026-09-08).
  A41.3  `seal` on remaining>0 → sealed=false reason=incomplete; on a complete run → sealed=true; a
         second seal → already=true.
  A41.5  `train` on an incomplete run raises "not sealed (remaining=…)"; on a complete run it trains,
         seeing all 3 classes.
  A42    train/evaluate/promote each write a world-axis record (bench.trained/evaluated/promoted), a
         promote log line, and promote is idempotent (`already=true`) the second time.

Run:  python app/test/bench_feature_coverage_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CL = ["AAA", "BBB", "CCC"]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_cov_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"client_id": "admin", "data": data}, "id": "t"}, "internal")
        return r if "error" in r else (r.get("result") or {})

    def derr(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"client_id": "admin", "data": data}, "id": "t"}, "internal")
        return r.get("error") if isinstance(r, dict) else None

    d("world.genesis", {})
    reg = d("source.register", {"provider": "syn", "name": "syn", "rights": "CC0"})
    src = reg.get("source")

    # B2 (S2-k) — feature.execute now REUSES an identical earlier embedding (same item, observer,
    # model_sha8) across runs. This eval tests the FRESH-embedding coverage / seal / train gating, so
    # each coverage run gets its OWN pool of DISTINCT items (no cross-run reuse to short-circuit it);
    # the reuse path itself is proven in sweep_eval. `_pool(tag, prefix)` builds a frozen 30-item pool.
    def _pool(tag, prefix):
        pid = "source:pool:%s:v1" % tag
        d("source.pool.create", {"name": pid, "rule": "syn", "source": src, "label_field": "species_symbol"})
        recs = [{"id": f"{prefix}{i}", "species_symbol": _CL[i % 3], "image_url": f"mock://{tag}/{i}.jpg"}
                for i in range(30)]
        d("source.acquire", {"source": src, "rule": "syn", "pool": pid, "id_field": "id",
                             "label_field": "species_symbol", "records": recs})
        d("source.pool.freeze", {"pool": pid})
        return pid

    P = _pool("syn", "s")          # A41.1 resumption
    P2 = _pool("syn2", "t")        # A41.2 full coverage + the train corpus
    P3 = _pool("syn3", "u")        # A41.3 / A41.5 seal + train gating
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("bench.new", {"name": "cov", "kind": "learning"})
    d("society.new", {"group": "lab", "name": "cs", "world": "default", "bench": "cov", "kind": "cowork"})
    d("learning.dataset.bind", {"name": "cov", "pool": P})
    d("learning.dataset.bind", {"name": "cov", "pool": P2})
    d("learning.dataset.bind", {"name": "cov", "pool": P3})

    # ── A41.1 — the cap counts NEW work; a resumed execute advances ──
    d("learning.feature.run", {"name": "cov", "pool": P, "observers": "color", "run": "r1"})
    e1 = d("learning.feature.execute", {"name": "cov", "run": "r1", "limit": "4"})
    e2 = d("learning.feature.execute", {"name": "cov", "run": "r1", "limit": "4"})
    check(f"[{shape}] a resumed execute observes NEW sources (not spent on skips)",
          e2.get("observed") == 4 and int(e2.get("skipped") or 0) >= 4, str(e2))
    check(f"[{shape}] remaining decreases by the chunk each call",
          int(e1.get("remaining")) - int(e2.get("remaining")) == 4,
          f"{e1.get('remaining')}→{e2.get('remaining')}")

    # ── A41.2 — the DEFAULT (no limit) covers the WHOLE pool in chunks (fresh 30-source run) ──
    d("learning.feature.run", {"name": "cov", "pool": P2, "observers": "color", "run": "r2"})
    ec = d("learning.feature.execute", {"name": "cov", "run": "r2", "chunk": "4"})
    check(f"[{shape}] the default (no limit) covers the pool: chunks=8, remaining=0, complete=true",
          ec.get("chunks") == 8 and ec.get("remaining") == 0 and ec.get("complete") is True, str(ec))

    # ── A41.3 / A41.5 — seal + train gate on a complete corpus ──
    d("learning.feature.run", {"name": "cov", "pool": P3, "observers": "color", "run": "r3"})
    d("learning.feature.execute", {"name": "cov", "run": "r3", "limit": "4"})     # partial
    sl_inc = d("learning.feature.seal", {"name": "cov", "run": "r3"})
    check(f"[{shape}] seal on an incomplete run refuses (sealed=false reason=incomplete)",
          sl_inc.get("sealed") is False and sl_inc.get("reason") == "incomplete"
          and int(sl_inc.get("remaining") or 0) > 0, str(sl_inc))
    err = derr("learning.train", {"name": "cov", "run": "r3", "space": "color", "head": "logreg", "seed": "s"})
    check(f"[{shape}] train on an incomplete run raises 'not sealed'",
          bool(err) and "not sealed" in ((err or {}).get("message", "")), str(err)[:120])
    d("learning.feature.execute", {"name": "cov", "run": "r3", "chunk": "4"})
    sl = d("learning.feature.seal", {"name": "cov", "run": "r3"})
    check(f"[{shape}] seal on a complete run seals it", sl.get("sealed") is True, str(sl))
    sl2 = d("learning.feature.seal", {"name": "cov", "run": "r3"})
    check(f"[{shape}] a second seal is a no-op (already=true)",
          sl2.get("sealed") is True and sl2.get("already") is True, str(sl2))

    # ── A41.5(iv) — train on the complete run sees all 3 classes ──
    tr = d("learning.train", {"name": "cov", "run": "r2", "space": "color", "head": "logreg", "seed": "s"})
    check(f"[{shape}] train on a complete run sees all 3 classes",
          tr.get("n_labeled") == 30 and set(tr.get("classes") or []) == set(_CL), str(tr)[:160])
    model = tr.get("model")

    # ── A42 — evaluate + promote write axis records; promote is idempotent + logs ──
    d("learning.evaluate", {"name": "cov", "model": model, "sample": "test"})
    pr = d("learning.promote", {"name": "cov", "model": model, "observer": "cov_head"})
    check(f"[{shape}] promote returns the observer (first promotion is not `already`)",
          pr.get("observer") == "cov_head" and not pr.get("already"), str(pr)[:120])
    pr2 = d("learning.promote", {"name": "cov", "model": model, "observer": "cov_head"})
    check(f"[{shape}] promote is idempotent (second time already=true)", pr2.get("already") is True, str(pr2))
    axis = d("world.axis", {"world": "default"})
    kinds = {r.get("kind") for r in (axis.get("axis") or [])}
    check(f"[{shape}] the world axis carries bench.trained / bench.evaluated / bench.promoted",
          {"bench.trained", "bench.evaluated", "bench.promoted"} <= kinds,
          str(sorted(k for k in kinds if str(k).startswith("bench."))))


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the feature corpus covers the whole pool (the cap counts NEW work; "
          "until=complete chunks to remaining=0), seal + train gate on a complete run, and "
          "train/evaluate/promote each leave a world-axis record with promote idempotent — both cell "
          "shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
