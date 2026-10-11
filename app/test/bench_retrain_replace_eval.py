#!/usr/bin/env python3
"""
A46 — a re-train REPLACES its run-scoped results; it does not keep yesterday's identity/frame/promotion.

The v26 symptom: b5 read `evaluate … model=…head:p1 frame=test n=20 classes=2` — a 20-class model scored
on a 20-item 2-class frame frozen the day before, because train's identity atom, the frozen frames, the
metrics atoms and the promotion record were all created-if-absent by alias (the A43 pattern one level
up). This eval proves the replace semantics on both cell shapes:

  A46(1) `_identity_atom` on the same alias with a DIFFERENT sha/size → a NEW identity atom, alias
         re-pointed, old kept + linked `bench:superseded_by`; identical sha → no-op.
  A46(2) `_freeze_sample` re-freezes when members differ (replace, old kept); identical → no-op.
  A46(3) `evaluate` refuses a frame whose corpus_sha disagrees with the model's.
  A46(4) `promote` compares the model KEY: a superseded model is a NEW promotion (not `already`), the
         learned-observer record is updated to the new model_key; the SAME key is `already=True`.
  end-to-end: an identical re-train mints no new atoms and promote returns `already=True`.

Run:  python app/test/bench_retrain_replace_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CL = ["A", "B", "C"]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    from app.concepts.bench_learning import LearningBenchConcept
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_rtr_"))
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
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("bench.new", {"name": "cov", "kind": "learning"})
    d("society.new", {"group": "lab", "name": "cs", "world": "default", "bench": "cov", "kind": "cowork"})
    lb = LearningBenchConcept(k.manager.get_session("admin")); lb._bind("")
    st = lb._store(); core = st.core if st is not None else lb.cortex.core

    def linked(sk, dk, rel):
        return any(l.get("dst") == dk and l.get("rel") == rel for l in (core.get_adjacent_links(sk) or []))

    # ── A46(1) _identity_atom replace-on-sha-change ──
    al = "model:learned:cov_head:r"
    k1 = lb._identity_atom(al, {"weights_sha256": "AAA", "weights_size": 10, "classes": ["A", "B"]})
    k2 = lb._identity_atom(al, {"weights_sha256": "BBB", "weights_size": 20, "classes": _CL})
    check(f"[{shape}] identity replaced on a sha/size change (new key)", k2 != k1, f"{k1[:8]}→{k2[:8]}")
    check(f"[{shape}] the old identity is kept and linked bench:superseded_by",
          core.get_chunk_raw(k1) is not None and linked(k2, k1, "bench:superseded_by"))
    k3 = lb._identity_atom(al, {"weights_sha256": "BBB", "weights_size": 20, "classes": _CL})
    check(f"[{shape}] an unchanged sha is a no-op (same key)", k3 == k2)

    # ── A46(2) _freeze_sample replace-on-members-change ──
    _, f1 = lb._freeze_sample("cov", "r", "test", ["x1", "x2"], "s", 0.8, "CORP1")
    _, f2 = lb._freeze_sample("cov", "r", "test", ["x1", "x2", "x3"], "s", 0.8, "CORP2")
    _, f3 = lb._freeze_sample("cov", "r", "test", ["x1", "x2", "x3"], "s", 0.8, "CORP2")
    check(f"[{shape}] a frame re-freezes when its members change, and is a no-op when identical",
          f1 is True and f2 is True and f3 is False, f"{f1},{f2},{f3}")

    # ── an end-to-end train on a real (mock) corpus, then the idempotent + guard + promote paths ──
    reg = d("source.register", {"provider": "syn", "name": "syn", "rights": "CC0"})
    src = reg.get("source")
    P = "source:pool:p:v1"
    d("source.pool.create", {"name": P, "rule": "syn", "source": src, "label_field": "sp"})
    d("source.acquire", {"source": src, "rule": "syn", "pool": P, "id_field": "id", "label_field": "sp",
                         "records": [{"id": f"s{i}", "sp": _CL[i % 3], "image_url": f"mock://x/{i}.jpg"}
                                     for i in range(30)]})
    d("source.pool.freeze", {"pool": P})
    d("learning.dataset.bind", {"name": "cov", "pool": P})
    d("learning.feature.extract", {"name": "cov", "pool": P, "observers": "color", "run": "p1"})
    tr = d("learning.train", {"name": "cov", "run": "p1", "space": "color", "head": "logreg", "seed": "s"})
    model = tr.get("model"); mkey1 = lb._key(model)
    pr = d("learning.promote", {"name": "cov", "model": model, "observer": "cov_head"})
    check(f"[{shape}] the first promotion is not `already`", not pr.get("already"), str(pr)[:100])

    # A46(6) — an identical re-train mints no new atoms; promote is `already=True`
    tr2 = d("learning.train", {"name": "cov", "run": "p1", "space": "color", "head": "logreg", "seed": "s"})
    check(f"[{shape}] an identical re-train keeps the same model identity", lb._key(tr2.get("model")) == mkey1)
    pr2 = d("learning.promote", {"name": "cov", "model": model, "observer": "cov_head"})
    check(f"[{shape}] promoting the same model KEY again is `already=True`", pr2.get("already") is True, str(pr2)[:100])

    # A46(3) — evaluate refuses a frame whose corpus_sha disagrees with the model's
    lb._freeze_sample("cov", "p1", "stale", ["z1", "z2"], "s", 0.8, "DIFFERENT_CORPUS")
    err = derr("learning.evaluate", {"name": "cov", "model": model, "sample": "stale"})
    check(f"[{shape}] evaluate refuses a stale frame (corpus_sha mismatch)",
          bool(err) and "corpus_sha" in ((err or {}).get("message", "")), str(err)[:120])

    # A46(4) — a SUPERSEDED model (new key, same alias) is a NEW promotion, observer updated
    mkey_new = lb._identity_atom(model, {**(lb._meta(model) or {}), "weights_sha256": "ZZZ", "weights_size": 999})
    check(f"[{shape}] superseding the model changes its key", mkey_new != mkey1)
    pr3 = d("learning.promote", {"name": "cov", "model": model, "observer": "cov_head"})
    check(f"[{shape}] promoting a superseded model is NOT `already` (a new promotion)", not pr3.get("already"), str(pr3)[:100])
    obs_meta = lb._meta("vlab:learned:cov_head") or {}
    check(f"[{shape}] the learned-observer record now points at the new model_key",
          obs_meta.get("model_key") == mkey_new, str(obs_meta.get("model_key", ""))[:12])


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a re-train replaces its run-scoped results: the identity atom, frozen frames, "
          "metrics and promotion follow the model KEY (new content-addressed atoms, alias re-pointed, "
          "old kept + linked), evaluate refuses a stale frame, an identical re-train is a no-op, and a "
          "superseded model is a fresh promotion — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
