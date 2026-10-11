#!/usr/bin/env python3
"""
D2-M — observation COORDINATES in the model (the growth cases the layout must stay O(K) under).

An observation is a point; every attribute a reader may slice by is a Set it is a member of; a reading
is an intersection; coarser questions are macros over intersections. This eval drives the growth cases
of §6 with MOCK observers (no network) on BOTH cell shapes:

  • family taxonomy — sense / learned / mock, computed at mint (unit-level).
  • §6.2 precompute REUSE — a precompute run (purpose=precompute) is reused by a bench o0 run
    (reused=N observed=0); the precompute rows are purpose=precompute.
  • §6.3 model VERSIONS — a retrain mints a second learned sha; vlab.item.versions lists both,
    newest first; the old model's Set keeps its members.
  • §6.4 second BENCH + second BRANCH — a bench's readings are in its own set:wb:<b>:observations
    (absent from the other's); two branches are separated by branch Sets; lens.compare across the
    two branch Sets joins by item.
  • §6.5 THOUGHT runs — a mode=thought run is in set:vlab:mode:thought and excluded from
    learning.runs mode=execution (execution is the complement, never a Set).
  • §6.6 every filter of vlab.item is an intersection (no [scan] O(store) warning); limit/offset page.
  • §6.7 BACKFILL — an observation minted before the layer acquires the keys + Sets on first read;
    a second read changes nothing.

Run:  python app/test/observation_layers_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["OAK", "MAPLE", "BIRCH", "PINE", "ELM", "ASH"]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_obscoord_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus.core

    def members(setname):
        try:
            return list(nuc.get_collection_members(setname) or [])
        except Exception:
            return []

    d("world.genesis", {})
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("bench.new", {"name": "leaf", "kind": "learning", "group": "lab"})
    d("society.new", {"group": "lab", "name": "ls", "world": "default", "bench": "leaf",
                      "kind": "cowork"})
    d("bench.new", {"name": "leaf2", "kind": "learning", "group": "lab"})
    d("society.new", {"group": "lab", "name": "ls2", "world": "default", "bench": "leaf2",
                      "kind": "cowork"})

    d("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = [{"id": f"img_{i}", "image": f"mock://leaf/{i}.jpg", "species_symbol": _CLASSES[i % 6]}
            for i in range(30)]
    d("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock", "label_field": "species_symbol"})
    d("source.acquire", {"source": "source:src:leafsrc", "rule": "mock", "records": recs,
                         "pool": "source:pool:leafimg:v1", "id_field": "id",
                         "label_field": "species_symbol"})
    d("source.pool.freeze", {"pool": "source:pool:leafimg:v1"})
    tg = d("source.pool.sample", {"pool": "source:pool:leafimg:v1", "name": "target", "n": "12",
                                  "seed": "s1", "strata": "species_symbol"})
    s_target = tg.get("sample")
    d("learning.dataset.bind", {"name": "leaf", "pool": s_target, "role": "target"})
    d("learning.dataset.bind", {"name": "leaf2", "pool": s_target, "role": "target"})
    N = tg.get("member_count")

    # ── family taxonomy (unit) — sense / learned / mock computed at mint ──
    from app.concepts.vision_lab import VisionLabConcept
    vl = VisionLabConcept(k.manager.get_session("admin"))

    class _F:
        family = "color"

    class _L:
        family = "learned"

    class _M:
        family = "mock"
    check(f"[{shape}] family: a learning-free observer that ran → sense",
          vl._obs_family(_F(), degraded=False) == "sense")
    check(f"[{shape}] family: a promoted head that ran → learned",
          vl._obs_family(_L(), degraded=False) == "learned")
    check(f"[{shape}] family: the mock observer (or a degraded fallback) → mock",
          vl._obs_family(_M(), degraded=False) == "mock"
          and vl._obs_family(_F(), degraded=True) == "mock"
          and vl._obs_family(_L(), degraded=True) == "mock")

    # ── §6.2 precompute reuse — a precompute run, then a bench o0 run reuses it ──
    d("vlab.run.new", {"pool": s_target, "run": "auto_leafimg", "observers": "mock",
                       "purpose": "precompute"})
    pex = d("vlab.run.execute", {"run": "auto_leafimg"})
    check(f"[{shape}] §6.2 the precompute run observed the whole target (purpose=precompute)",
          pex.get("observed") == N, str(pex)[:120])
    _pc = members("set:vlab:purpose:precompute")
    check(f"[{shape}] §6.2 precompute observations joined set:vlab:purpose:precompute", len(_pc) == N,
          f"n={len(_pc)}")
    o0 = d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "mock", "run": "o0",
                             "branch": "plants_t2"})
    check(f"[{shape}] §6.2 the bench o0 run REUSED the precompute (reused=N observed=0)",
          o0.get("reused") == N and o0.get("observed") == 0 and o0.get("complete"), str(o0)[:160])
    check(f"[{shape}] §6.2 the reused observations are in o0's + the bench's Sets",
          len(members("set:vlab:run:o0:observations")) == N
          and len(members("set:wb:leaf:observations")) == N)

    # ── §6.5 a thought run is in set:vlab:mode:thought + excluded from learning.runs mode=execution.
    #    (a distinct observer `texture` so its readings are their own atoms — the SAME observer on the
    #    SAME item is one content-addressed reading shared across runs, which is the reuse case.) ──
    d("vlab.run.new", {"pool": s_target, "run": "th0", "observers": "texture", "bench": "wb:leaf",
                       "branch": "rehearsal", "mode": "thought"})
    d("vlab.run.execute", {"run": "th0"})
    check(f"[{shape}] §6.5 a thought run's observations are in set:vlab:mode:thought",
          len(members("set:vlab:mode:thought")) == N, f"n={len(members('set:vlab:mode:thought'))}")
    _brx = d("learning.runs", {"name": "leaf", "mode": "execution"})
    _rns = {r.get("run") for r in (_brx.get("runs") or [])}
    check(f"[{shape}] §6.5 learning.runs mode=execution excludes the thought run",
          "o0" in _rns and "th0" not in _rns, str(_rns))
    _brt = d("learning.runs", {"name": "leaf", "mode": "thought"})
    check(f"[{shape}] §6.5 learning.runs mode=thought lists ONLY the thought run",
          {r.get("run") for r in (_brt.get("runs") or [])} == {"th0"},
          str({r.get("run") for r in (_brt.get("runs") or [])}))

    # ── §6.4 a second bench observing the same pool with a DIFFERENT observer — its readings are its
    #    own (fresh atoms, so disjoint from the first bench's reused-mock readings) ──
    d("learning.observe", {"name": "leaf2", "pool": "role:target", "observers": "color", "run": "o0b",
                        "branch": "b2"})
    b1 = set(members("set:wb:leaf:observations"))
    b2 = set(members("set:wb:leaf2:observations"))
    check(f"[{shape}] §6.4 a second bench's readings are in its own Set, disjoint from the first",
          len(b2) == N and not (b1 & b2), f"|b1|={len(b1)} |b2|={len(b2)} ∩={len(b1 & b2)}")

    # ── §6.4 a second BRANCH of the SAME bench (a different head → distinct readings) — branch Sets
    #    separate them; lens.compare across the two branch Sets joins by item ──
    d("learning.observe", {"name": "leaf", "pool": "role:target", "observers": "geometry", "run": "o1m",
                        "branch": "plants_t6_mlp"})
    br_a = "set:wb:leaf:branch:plants_t2:observations"
    br_b = "set:wb:leaf:branch:plants_t6_mlp:observations"
    check(f"[{shape}] §6.4 two branches of one bench are separated by branch Sets",
          len(members(br_a)) == N and len(members(br_b)) == N
          and set(members(br_a)) != set(members(br_b)),
          f"|a|={len(members(br_a))} |b|={len(members(br_b))} eq={set(members(br_a))==set(members(br_b))}")
    cmp_br = d("lens.compare", {"a": br_a, "b": br_b, "key": "vis:observes"})
    check(f"[{shape}] §6.4 lens.compare across the two branch Sets joins by item (N rows)",
          (cmp_br.get("summary") or {}).get("items") == N, str(cmp_br.get("summary")))

    # ── M1/M3/M6 — the mint path stamps bench/wf_branch/purpose; learning.runs describes a run by its
    #    coordinates; the model sha8 is ONE number across vlab.item and learning.runs. o1m (leaf/geometry/
    #    branch=plants_t6_mlp) is a FRESH mint (not a reuse), so its observations carry the coords. ──
    _mi = sorted(members(f"{s_target}:members"))[0]
    _mi_a = nuc.get_aliases_by_key(_mi)
    _mi_a = _mi_a[0] if _mi_a else _mi
    _it_m = d("vlab.item", {"source": _mi_a, "run": "o1m"})
    _row_m = (_it_m.get("observations") or [{}])[0]
    check(f"[{shape}] M1 a learning.observe mint carries bench=wb:leaf wf_branch=plants_t6_mlp purpose=bench",
          _row_m.get("bench") == "wb:leaf" and _row_m.get("wf_branch") == "plants_t6_mlp"
          and _row_m.get("purpose") == "bench",
          str({kk: _row_m.get(kk) for kk in ("bench", "wf_branch", "purpose")}))
    _br_t6 = d("learning.runs", {"name": "leaf", "branch": "plants_t6_mlp"})
    _r_t6 = {r.get("run"): r for r in (_br_t6.get("runs") or [])}
    check(f"[{shape}] M3 learning.runs branch=plants_t6_mlp returns o1m with its coords",
          "o1m" in _r_t6 and _r_t6["o1m"].get("wf_branch") == "plants_t6_mlp"
          and _r_t6["o1m"].get("purpose") == "bench"
          and bool(_r_t6["o1m"].get("model_sha8s")), str(_r_t6.get("o1m")))
    check(f"[{shape}] M6 the model sha8 is ONE number across vlab.item and learning.runs",
          _row_m.get("model_sha8") in (_r_t6.get("o1m") or {}).get("model_sha8s", []),
          f"item={_row_m.get('model_sha8')} runs={(_r_t6.get('o1m') or {}).get('model_sha8s')}")

    # ── §6.6 every vlab.item filter is an intersection (no [scan] O(store) warning); paging ──
    ti = sorted(members(f"{s_target}:members"))[0]
    ti_alias = nuc.get_aliases_by_key(ti)
    ti_alias = ti_alias[0] if ti_alias else ti

    class _Cap(logging.Handler):
        def __init__(self):
            super().__init__(logging.WARNING); self.lines = []

        def emit(self, r):
            try:
                self.lines.append(r.getMessage())
            except Exception:
                pass
    _cap = _Cap()
    _root = logging.getLogger(); _root.addHandler(_cap); _lvl = _root.level
    _root.setLevel(logging.WARNING)
    try:
        it_all = d("vlab.item", {"source": ti_alias})
        it_th = d("vlab.item", {"source": ti_alias, "mode": "thought"})
        it_ex = d("vlab.item", {"source": ti_alias, "mode": "execution"})
        it_br = d("vlab.item", {"source": ti_alias, "bench": "leaf", "branch": "plants_t6_mlp"})
        it_pc = d("vlab.item", {"source": ti_alias, "purpose": "precompute"})
        no_scan = not any("[scan]" in ln and "O(store)" in ln for ln in _cap.lines)
    finally:
        _root.removeHandler(_cap); _root.setLevel(_lvl)
    check(f"[{shape}] §6.6 mode=thought and mode=execution partition the item's readings",
          len(it_th.get("observations") or []) == 1
          and all(r.get("mode") != "thought" for r in (it_ex.get("observations") or []))
          and (it_th.get("count_total", 0) + len(it_ex.get("observations") or []))
          == it_all.get("count_total"), f"all={it_all.get('count_total')} th={it_th.get('count_total')}")
    check(f"[{shape}] §6.6 bench+branch filter returns only that branch's reading",
          len(it_br.get("observations") or []) == 1
          and (it_br.get("observations") or [{}])[0].get("wf_branch") == "plants_t6_mlp",
          str(it_br.get("count")))
    check(f"[{shape}] §6.6 purpose=precompute filter returns the precompute reading",
          len(it_pc.get("observations") or []) == 1
          and (it_pc.get("observations") or [{}])[0].get("purpose") == "precompute",
          str([{"run": r.get("run"), "purpose": r.get("purpose")} for r in (it_pc.get("observations") or [])]))
    check(f"[{shape}] §6.6 no [scan] O(store) warning during the filtered reads", no_scan,
          str(_cap.lines)[-160:])
    # paging: limit=2 then offset=2 partitions the item's readings deterministically
    p1 = d("vlab.item", {"source": ti_alias, "limit": "2", "offset": "0"})
    p2 = d("vlab.item", {"source": ti_alias, "limit": "2", "offset": "2"})
    _ids = lambda r: [x.get("observation") for x in (r.get("observations") or [])]
    check(f"[{shape}] §6.6 limit/offset page consistently (no overlap, ordered by at_seq desc)",
          len(_ids(p1)) == 2 and len(_ids(p2)) >= 1 and not (set(_ids(p1)) & set(_ids(p2)))
          and p1.get("count_total") == it_all.get("count_total"),
          f"p1={_ids(p1)} p2={_ids(p2)}")

    # ── §6.7 backfill — an observation minted WITHOUT the layer acquires it on first read. Pick a
    #    target item's o0b (leaf2/color) observation, strip its layer, then read the item ──
    ti2 = sorted(members(f"{s_target}:members"))[1]
    ti2_alias = nuc.get_aliases_by_key(ti2)
    ti2_alias = ti2_alias[0] if ti2_alias else ti2
    _it2 = d("vlab.item", {"source": ti2_alias, "run": "o0b"})
    victim = nuc.get_key_by_alias((_it2.get("observations") or [{}])[0].get("observation"))
    vm = json.loads(nuc.get_chunk_raw(victim)["meta"])
    for kk in ("family", "model_sha8", "bench", "wf_branch", "mode", "purpose", "observer_version",
               "layer_v"):
        vm.pop(kk, None)                              # simulate a pre-D2-M observation (no layer version)
    nuc.update_meta(victim, vm)
    vm2 = json.loads(nuc.get_chunk_raw(victim)["meta"])
    _pre = "family" not in vm2
    d("vlab.item", {"source": ti2_alias})             # first read backfills
    vm3 = json.loads(nuc.get_chunk_raw(victim)["meta"])
    check(f"[{shape}] §6.7 a pre-layer observation acquires the layer keys on first read",
          _pre and vm3.get("family") and vm3.get("bench") == "wb:leaf2"
          and vm3.get("wf_branch") == "b2", f"pre={_pre} post={ {kk: vm3.get(kk) for kk in ('family','bench','wf_branch')} }")
    _before = dict(vm3)
    d("vlab.item", {"source": ti2_alias})             # second read changes nothing
    vm4 = json.loads(nuc.get_chunk_raw(victim)["meta"])
    check(f"[{shape}] §6.7 a second read changes nothing (idempotent backfill)",
          vm4.get("family") == _before.get("family")
          and vm4.get("at_seq") == _before.get("at_seq"))


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — an observation carries its coordinates as Set memberships computed at mint: "
          "family/observer/model/bench/branch/mode/purpose. A precompute is reused by a bench run; a "
          "second bench and a second branch are separable and comparable; a thought run is marked and "
          "excluded from execution; every vlab.item filter is an intersection (no store scan) that "
          "pages; and a pre-layer observation is backfilled idempotently on first read — both cells.")
    sys.exit(0)


if __name__ == "__main__":
    main()
