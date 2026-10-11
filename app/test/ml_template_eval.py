#!/usr/bin/env python3
"""
Part D — the ML bench TEMPLATE (PLANTS v0.2), stages T1–T6 + the Source-Viewer trace.

The template is: read datasets from a source → observe the TARGET learning-free (T2) → train from a
SEPARATE training set (T3–T5) → observe the SAME target with the learned model (T6) → follow the
change per item (T7, deferred to land with E's macro facility). This eval drives T1–T6 with MOCK
observers (no network, no heavy ML dep) on BOTH cell shapes and asserts the Stage-1 exit criterion:

  • T1 makes DISJOINT train/target samples from ONE frozen pool (stratified; complement exact).
  • dataset.bind role= lets later blocks address the pools as role:train / role:target.
  • learning.observe reads the whole target as ONE observation (resumable), sealed, membership recorded.
  • train/evaluate/promote produce a learned observer.
  • learning.observe with the promoted head re-reads the SAME target.
  • source.trace on a target item lists exactly TWO observations (o0 learning-free, o1 learned), each
    with its run/observer/at_seq — the before/after the Source Viewer renders.
  • a second full pass adds NO new observations (per-(source,observer,run) sentinels).

Run:  python app/test/ml_template_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["OAK", "MAPLE", "BIRCH", "PINE", "ELM", "ASH"]     # 6 classes
_POOL = "source:pool:leafimg:v1"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_mlt_")
    k = KernelDispatcher(series=series, base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus.core

    def members(setname):
        # read a nucleus set directly (source samples + vlab observation membranes live in the nucleus,
        # which the session's scoped s.ls does not surface here)
        try:
            return list(nuc.get_collection_members(setname) or [])
        except Exception:
            return []

    d("world.genesis", {})
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("bench.new", {"name": "leaf", "kind": "learning", "group": "lab"})
    d("society.new", {"group": "lab", "name": "leafsoc", "world": "default", "bench": "leaf",
                      "kind": "cowork"})

    # ── a FROZEN source pool of 60 refs across 6 classes (image locator + species_symbol) ──
    d("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = []
    for i in range(60):
        cls = _CLASSES[i % 6]
        recs.append({"id": f"img_{i}", "image": f"mock://leaf/{cls.lower()}/{i}.jpg",
                     "species_symbol": cls, "title": f"{cls} {i}"})
    d("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock leaf refs", "label_field": "species_symbol"})
    d("source.acquire", {"source": "source:src:leafsrc", "rule": "mock leaf refs", "records": recs,
                         "pool": _POOL, "id_field": "id", "label_field": "species_symbol"})
    fr = d("source.pool.freeze", {"pool": _POOL})
    check(f"[{shape}] the source pool freezes (60 refs)",
          fr.get("status") == "FROZEN", str(fr)[:120])

    # ── T1 — disjoint train/target samples from the ONE frozen pool (complement exact) ──
    tr = d("source.pool.sample", {"pool": _POOL, "name": "train", "n": "40", "seed": "plants1",
                                  "strata": "species_symbol"})
    tg = d("source.pool.sample", {"pool": _POOL, "name": "target", "n": "20", "seed": "plants1",
                                  "strata": "species_symbol", "rule": "complement:train"})
    s_train, s_target = tr.get("sample"), tg.get("sample")
    check(f"[{shape}] T1 train sample is 40 refs", tr.get("member_count") == 40, str(tr)[:120])
    check(f"[{shape}] T1 target is the 20-ref complement of train",
          tg.get("member_count") == 20 and tg.get("complement_of") == s_train, str(tg)[:140])
    train_m = set(members(f"{s_train}:members"))
    target_m = set(members(f"{s_target}:members"))
    check(f"[{shape}] train ∩ target = ∅ (disjoint by construction)",
          bool(train_m) and bool(target_m) and not (train_m & target_m),
          f"|train|={len(train_m)} |target|={len(target_m)} |∩|={len(train_m & target_m)}")

    # ── T1 bind — role= addresses the two pools by function ──
    d("learning.dataset.bind", {"name": "leaf", "pool": s_train, "role": "train"})
    d("learning.dataset.bind", {"name": "leaf", "pool": s_target, "role": "target"})

    # ── T2 — the learning-free reading of the target (mock classifier) ──
    o0 = d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "mock", "run": "o0",
                             "branch": "plants_t2"})
    check(f"[{shape}] T2 observes the whole target once, sealed",
          o0.get("observed") == 20 and o0.get("complete") and o0.get("sealed")
          and o0.get("items") == 20, str(o0)[:160])
    obs0 = set(members("set:vlab:run:o0:observations"))
    check(f"[{shape}] run o0 observation-membership set has 20 members (§4.1)", len(obs0) == 20,
          f"n={len(obs0)}")

    # ── T3/T4/T5 — features on the TRAINING set, train, evaluate, promote ──
    d("learning.feature.run", {"name": "leaf", "pool": "role:train", "observers": "color", "run": "f1"})
    d("learning.feature.execute", {"name": "leaf", "run": "f1"})
    d("learning.feature.seal", {"name": "leaf", "run": "f1"})
    trn = d("learning.train", {"name": "leaf", "run": "f1", "space": "color", "head": "logreg",
                            "split": "0.8", "seed": "plants1", "label_key": "species_symbol"})
    model = trn.get("model")
    check(f"[{shape}] T4 trains a head on the training set (never sees the target)",
          bool(model) and set(trn.get("classes") or []) == set(_CLASSES), str(trn)[:160])
    d("learning.evaluate", {"name": "leaf", "model": model, "sample": "test"})
    pr = d("learning.promote", {"name": "leaf", "model": model, "observer": "plants_head_f1"})
    check(f"[{shape}] T5 promotes the head as an observer", pr.get("observer") == "plants_head_f1",
          str(pr)[:140])

    # ── T6 — the learned reading of the SAME target ──
    o1 = d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "plants_head_f1",
                             "run": "o1", "branch": "plants_t6"})
    check(f"[{shape}] T6 re-observes the whole target with the promoted head",
          o1.get("observed") == 20 and o1.get("complete"), str(o1)[:160])

    # ── D2-M §6 #1 — a target item's vlab.item carries the two coordinate-layered rows; a train item
    #    has sample_roles=[train] and no o1 ──
    ti = sorted(target_m)[0]
    ti_alias = nuc.get_aliases_by_key(ti)
    ti_alias = ti_alias[0] if ti_alias else ti
    it = d("vlab.item", {"source": ti_alias})
    _rows = it.get("observations") or []
    _by_run = {r.get("run"): r for r in _rows}
    _sense = _by_run.get("o0") or {}
    _learned = _by_run.get("o1") or {}
    # (the o0 observer is `mock` here for a no-network run — its family is `mock`; the real deploy
    #  reads with `litert` → `sense`. The family taxonomy itself is unit-tested in observation_layers_eval.)
    check(f"[{shape}] §6.1 target item has an o0/plants_t2 row + a learned/o1/plants_t6 row",
          _sense.get("family") in ("sense", "mock") and _sense.get("purpose") == "bench"
          and _sense.get("bench") == "wb:leaf" and _sense.get("wf_branch") == "plants_t2"
          and _learned.get("family") == "learned" and _learned.get("wf_branch") == "plants_t6"
          and bool(_learned.get("model_sha8")) and _learned.get("model_sha8") != "nomodel",
          f"o0={_sense} o1={_learned}")
    check(f"[{shape}] §6.1 the target item's sample_roles = [target]",
          [s.get("role") for s in (it.get("sample_roles") or [])] == ["target"],
          str(it.get("sample_roles")))
    _tri = sorted(train_m)[0]
    _tri_alias = nuc.get_aliases_by_key(_tri)
    _tri_alias = _tri_alias[0] if _tri_alias else _tri
    itr = d("vlab.item", {"source": _tri_alias})
    check(f"[{shape}] §6.1 a train item has sample_roles=[train] and no o1 reading",
          [s.get("role") for s in (itr.get("sample_roles") or [])] == ["train"]
          and not any(r.get("run") == "o1" for r in (itr.get("observations") or [])),
          str(itr.get("sample_roles")))
    # §6.6 — the filters are intersections (family=learned returns only the o1 row)
    itf = d("vlab.item", {"source": ti_alias, "family": "learned"})
    check(f"[{shape}] §6.6 vlab.item family=learned returns only the learned row (intersection)",
          len(itf.get("observations") or []) == 1
          and (itf.get("observations") or [{}])[0].get("run") == "o1", str(itf.get("count")))
    # §4.2 — the version stack lists the learned head's version
    vv = d("vlab.item.versions", {"source": ti_alias, "observer": "plants_head_f1"})
    check(f"[{shape}] §4.2 vlab.item.versions lists the head's version (engine + sha)",
          len(vv.get("versions") or []) == 1 and bool((vv.get("versions") or [{}])[0].get("model_sha8"))
          and (vv.get("versions") or [{}])[0].get("engine"), str(vv.get("versions"))[:140])
    # §4.3 — learning.runs lists o0 (execution) and the diff; §5 the run coordinates
    br = d("learning.runs", {"name": "leaf"})
    _bruns = {r.get("run"): r for r in (br.get("runs") or [])}
    check(f"[{shape}] §4.3 learning.runs lists o0 + o1 with branch coordinates",
          _bruns.get("o0", {}).get("wf_branch") == "plants_t2"
          and _bruns.get("o1", {}).get("wf_branch") == "plants_t6", str(list(_bruns)))

    # ── source.trace — a target item shows exactly the two readings (before/after) ──
    one = nuc.get_aliases_by_key(sorted(target_m)[0])
    one = (one[0] if one else sorted(target_m)[0])
    tr_out = d("source.trace", {"id": one})
    observations = tr_out.get("observations") or []
    runs = sorted({o.get("run") for o in observations})
    observers = sorted({o.get("observer") for o in observations})
    check(f"[{shape}] source.trace on a target item lists exactly two observations",
          len(observations) == 2 and runs == ["o0", "o1"], f"runs={runs} observers={observers}")
    check(f"[{shape}] the two readings name o0=mock (learning-free) and o1=plants_head_f1 (learned)",
          "mock" in observers and "plants_head_f1" in observers, str(observers))

    # ── T7 — observe.diff (the pure macro over lens.compare): the change per item + in sum ──
    mtext = open(os.path.join(ROOT, "app", "config", "macros", "observe.diff.csl"), encoding="utf-8").read()
    mparams, mbody = "", []
    for ln in mtext.splitlines():
        st = ln.strip()
        if st.startswith("#!params"):
            mparams = st[len("#!params"):].strip(); continue
        if st.startswith("#"):
            continue
        mbody.append(ln)
    d("macro.def", {"name": "observe.diff", "params": mparams, "script": "\n".join(mbody).strip()})
    diff = d("macro.run", {"name": "observe.diff", "bench": "leaf", "before": "o0", "after": "o1",
                           "truth": "species_symbol", "as": "inline"})
    # the macro's steps: lens.compare (the summary), then the two set.add lines that file its aggregate
    _cmp = next((r for r in (diff.get("results") or []) if isinstance(r, dict)
                 and isinstance(r.get("result"), dict) and "summary" in r["result"]), {})
    summ = ((_cmp.get("result") or {}).get("summary")) or {}
    check(f"[{shape}] T7 observe.diff summarizes the whole target (20 items, all changed)",
          summ.get("items") == 20 and summ.get("changed") == 20, str(summ))
    check(f"[{shape}] agree_after ≥ agree_before, agree_before==0 (ImageNet has no species symbols)",
          summ.get("agree_a") == 0 and summ.get("agree_b", -1) >= 0, str(summ))
    check(f"[{shape}] observe.diff stored ONE aggregate atom wb:leaf:diff:o0:o1 (bench:compares)",
          ((_cmp.get("result") or {}).get("result")) == "wb:leaf:diff:o0:o1",
          str(_cmp.get("result", {}))[:80])
    _summ1 = dict(summ)

    # ── M2 — the stored diff is indexed under the bench, so learning.runs lists it (the run atoms carry
    #    bench=wb:leaf via M1, so the diffs set is populated) ──
    _brd = d("learning.runs", {"name": "leaf"})
    _diffs = _brd.get("diffs") or []
    check(f"[{shape}] M2 learning.runs.diffs lists the stored o0↔o1 compare (indexed by bench)",
          any(dd.get("a") == "set:vlab:run:o0:observations"
              and dd.get("b") == "set:vlab:run:o1:observations" for dd in _diffs), str(_diffs)[:200])

    # ── M4 — source.trace's learned (o1) reading carries observer_version = its model_sha8 (not null) ──
    _it_o1 = d("vlab.item", {"source": one, "run": "o1"})
    _o1_sha = (_it_o1.get("observations") or [{}])[0].get("model_sha8")
    _o1_trace = [o for o in observations if o.get("run") == "o1"]
    check(f"[{shape}] M4 source.trace's learned reading has observer_version == its model_sha8 (not null)",
          bool(_o1_sha) and _o1_trace and _o1_trace[0].get("observer_version") == _o1_sha,
          f"sha={_o1_sha} trace={[o.get('observer_version') for o in _o1_trace]}")
    # ── R3-c — the interpretations[] BRIDGE rows (what the page renders) also carry observer_version,
    #    joined from observations[] (not null for the o1 learned reading) ──
    _interp_o1 = [r for r in (tr_out.get("interpretations") or []) if r.get("run") == "o1"]
    check(f"[{shape}] R3-c source.trace interpretations[] rows carry observer_version (joined)",
          _interp_o1 and _interp_o1[0].get("observer_version") == _o1_sha,
          f"interp={[r.get('observer_version') for r in _interp_o1]}")

    # ── M5 — the version stack's accuracy is the held-out evaluate figure (a number, not null) ──
    _vacc = (vv.get("versions") or [{}])[0].get("accuracy")
    check(f"[{shape}] M5 vlab.item.versions.accuracy is the held-out figure (a number, not null)",
          isinstance(_vacc, (int, float)), f"accuracy={_vacc!r}")

    # ── a second full pass adds NO new observations (per-(source,observer,run) sentinels) ──
    o0b = d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "mock", "run": "o0",
                              "branch": "plants_t2"})
    o1b = d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "plants_head_f1",
                              "run": "o1", "branch": "plants_t6"})
    obs0b = set(members("set:vlab:run:o0:observations"))
    check(f"[{shape}] a second pass re-observes nothing (sentinels) and grows no membership",
          o0b.get("observed") == 0 and o1b.get("observed") == 0 and len(obs0b) == 20,
          f"o0.observed={o0b.get('observed')} o1.observed={o1b.get('observed')} obs0={len(obs0b)}")
    diff2 = d("macro.run", {"name": "observe.diff", "bench": "leaf", "before": "o0", "after": "o1",
                            "truth": "species_symbol", "as": "inline"})
    _cmp2 = next((r for r in (diff2.get("results") or []) if isinstance(r, dict)
                  and isinstance(r.get("result"), dict) and "summary" in r["result"]), {})
    summ2 = ((_cmp2.get("result") or {}).get("summary")) or {}
    check(f"[{shape}] re-running observe.diff yields the SAME summary (deterministic)",
          summ2 == _summ1, f"{summ2} vs {_summ1}")

    # ── D2-M §6.3 — a RETRAIN (a new seed → new weights sha) mints a SECOND learned version;
    #    vlab.item.versions lists both newest-first; the OLD model's Set keeps its members ──
    sha1 = _learned.get("model_sha8")
    d("learning.feature.run", {"name": "leaf", "pool": "role:train", "observers": "color", "run": "f2"})
    d("learning.feature.execute", {"name": "leaf", "run": "f2"})
    d("learning.feature.seal", {"name": "leaf", "run": "f2"})
    trn2 = d("learning.train", {"name": "leaf", "run": "f2", "space": "color", "head": "logreg",
                             "split": "0.8", "seed": "plants2", "label_key": "species_symbol"})
    d("learning.promote", {"name": "leaf", "model": trn2.get("model"), "observer": "plants_head_f1"})
    o2 = d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "plants_head_f1",
                             "run": "o2", "branch": "plants_t6b"})
    vv2 = d("vlab.item.versions", {"source": ti_alias, "observer": "plants_head_f1"})
    _shas = [r.get("model_sha8") for r in (vv2.get("versions") or [])]
    check(f"[{shape}] §6.3 a retrain mints a 2nd version; vlab.item.versions lists both newest-first",
          o2.get("observed") == 20 and len(_shas) == 2 and _shas[0] != _shas[1]
          and sha1 in _shas, f"shas={_shas} sha1={sha1}")
    check(f"[{shape}] §6.3 the OLD model's Set keeps its members (history preserved)",
          len(members("set:vlab:model:%s:observations" % sha1)) >= 20,
          f"old_model_set={len(members('set:vlab:model:%s:observations' % sha1))}")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the ML template runs observe→learn→observe-again: T1 splits one frozen pool "
          "into disjoint stratified train/target samples (complement exact); role= addresses them; "
          "learning.observe reads the target once (learning-free, then learned), records run membership, "
          "and source.trace shows the two readings per item — both cell shapes, no network, no sklearn.")
    sys.exit(0)


if __name__ == "__main__":
    main()
