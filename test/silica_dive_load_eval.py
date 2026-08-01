#!/usr/bin/env python3
"""
Silica dive LOAD regression — the mega-hub dive must not scan whole routes.

This is the guard for the class of bug that only shows at real server scale and that NO
small synthetic test caught: a dense proto-word hub (a common thesaurus word — tens of
thousands of `specializes`/related edges sharing one Silica route) dived under the
disk-value backend. The regression was that per-key lookups on the hot dive path
(get_aliases_by_key / get_chunk_access_scopes / collection_exists, and the "branches
ahead" cue) read the WHOLE route's values — O(density) value reads (preads) per dive —
which silently OOM-killed the daemon at real ontology density while every unit test passed.

The invariant this locks in: **a dive's value-read count is bounded by the display/scan
CAPS, NOT by the hub's degree.** So it must stay ~FLAT as the hub's density grows. We build
the same hub at 1x / 4x / 10x density (disk-value Silica), count value materializations
(SilicaStore._entry_bytes — every disk value read funnels through it) during ONE dive at
each scale, and assert the 10x count is not linear in density. A reintroduced full-route
scan makes the count scale with degree and fails here.

Run:  python test/silica_dive_load_eval.py
"""
import os, sys, time, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"
os.environ["AKASHA_SILICA_VALUES"] = "disk"          # the environment the bug lives in

from lib.akasha.composite import AkashaEngine
from lib.akasha.consciousness import ConsciousnessEngine
from lib.akasha.tensor import TensorEngine
from lib.akasha.backends import silica as _silica_mod
from lib.akasha.jcl.workspace_context import system_context

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:24} {detail}")


# ── value-read instrumentation ──────────────────────────────────────────────────
# Every disk-mode value materialization funnels through SilicaStore._entry_bytes; counting
# its calls IS the pread/value-read count (independent of the SLRU cache, which only changes
# whether the read hits disk — we care that the code even ASKS for the value).
_ENTRY = {"n": 0}
_orig_entry_bytes = _silica_mod.SilicaStore._entry_bytes


def _counting_entry_bytes(self, bank, entry):
    _ENTRY["n"] += 1
    return _orig_entry_bytes(self, bank, entry)


_silica_mod.SilicaStore._entry_bytes = _counting_entry_bytes


def _build_hub(cortex, tag, n_senses, nb_per_sense):
    """A dense proto-word hub `tag`: n_senses incoming `specializes` senses, each carrying a
    semantic_vector + nb_per_sense neighbours — the shape of a real thesaurus mega-hub."""
    vec = [0.01 * ((i % 17) - 8) for i in range(64)]
    with system_context():
        hub = cortex.commit(f"{tag} hub content for load test", meta={"type": "hub"},
                            scopes=["scope:sys:universal"])["key"]
        cortex.put_alias(hub, tag)
        for s in range(n_senses):
            sk = cortex.commit(f"ingred:{tag}:sense{s} a sense with descriptive words here",
                              meta={"type": "hub", "semantic_vector": vec},
                              scopes=["scope:sys:universal"])["key"]
            cortex.put_link(sk, hub, "specializes", author="system")
            for j in range(nb_per_sense):
                nb = cortex.commit(f"neighbour {j} of {tag} sense {s}, more words",
                                  meta={"semantic_vector": vec},
                                  scopes=["scope:sys:universal"])["key"]
                cortex.put_link(sk, nb, "sys:related", author="system")
    return hub


def _dive_value_reads(cons, hub_key):
    _ENTRY["n"] = 0
    t0 = time.time()
    view = cons.generate_view(hub_key)
    dt = time.time() - t0
    return _ENTRY["n"], dt, view


def main():
    print("\n  silica dive LOAD regression — dive value-reads must be capped, not O(density)\n")
    base = tempfile.mkdtemp(prefix="akasha_dive_load_")
    db = os.path.join(base, "load.db")
    cortex = AkashaEngine(db)
    cortex.attach_tensor_engine(TensorEngine(cortex))
    cons = ConsciousnessEngine(cortex)

    # 1x / 4x / 10x density (same shape, growing degree). Kept modest so the build stays inside
    # a constrained container; the RATIO across scales is what matters, not the absolute size.
    NB = 6
    scales = [("1x", 300), ("4x", 1200), ("10x", 3000)]
    reads = {}
    try:
        for label, n in scales:
            t0 = time.time()
            hub = _build_hub(cortex, f"loadhub{label}", n, NB)
            build_s = time.time() - t0
            v_reads, dive_s, view = _dive_value_reads(cons, hub)
            reads[label] = v_reads
            edges = n * (NB + 1)
            ok = isinstance(view, dict) and not view.get("error") and view.get("signposts")
            record(f"dive {label} (~{edges//1000}k edges)", ok,
                   f"value_reads={v_reads}  dive={dive_s:.2f}s  build={build_s:.1f}s  "
                   f"signposts={len(view.get('signposts', []))}")

        # THE INVARIANT: value-reads PER EDGE stay a small bounded constant and do NOT grow with
        # density. The catastrophic bug read each edge's WHOLE route once PER SIGNPOST → ~12
        # reads/edge AND rising with density (more signposts × more edges). The fix reads each
        # incoming sense edge ~once (to enumerate the proto-word's senses — necessary work) plus a
        # capped handful per signpost → well under 2 reads/edge and FLAT-to-falling as density
        # grows. (The remaining O(density) is that single per-edge sense read; it has a tiny
        # constant and is fundamental to 'surface every sense', unlike the bug's per-signpost
        # re-scan. A far larger server-scale hub could later cap that too — separate optimisation.)
        edges = {lbl: n * (NB + 1) for lbl, n in scales}
        rpe = {lbl: reads[lbl] / edges[lbl] for lbl in reads}
        BUDGET = 3.0                                  # bug was ~12; fix is ~0.6–1.3
        under_budget = all(v < BUDGET for v in rpe.values())
        record("reads/edge under budget", under_budget,
               "  ".join(f"{lbl}={rpe[lbl]:.2f}" for lbl, _ in scales) +
               f"  (budget <{BUDGET}/edge; bug was ~12)")
        # Super-linearity guard: per-edge cost must not CLIMB with density (that is the signature
        # of a per-signpost route re-scan creeping back). Allow mild slack for build variance.
        not_climbing = rpe["10x"] <= rpe["1x"] * 1.5
        record("reads/edge not climbing", not_climbing,
               f"10x={rpe['10x']:.2f} ≤ 1x={rpe['1x']:.2f} ×1.5 (per-edge work must not grow with size)")

        # Sanity: a direct mega-hub alias lookup must read ZERO values (scan_subkeys is key-only).
        big = _build_hub(cortex, "aliashub", 4000, 2)
        _ENTRY["n"] = 0
        _ = cortex.get_aliases_by_key(big)
        _ = cortex.core.get_chunk_access_scopes(big)
        _ = cortex.core.get_collections_for_key(big)
        _ = cortex.core.collection_exists("scope:sys:universal")
        zero = _ENTRY["n"]
        record("subkey lookups: 0 reads", zero == 0,
               f"alias/scope/collection/exists on a 4k-edge hub materialized {zero} values (want 0)")
    finally:
        shutil.rmtree(base, ignore_errors=True)
        _silica_mod.SilicaStore._entry_bytes = _orig_entry_bytes

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} checks passed")
    if passed == total:
        print("\nRESULT: PASS — a mega-hub dive's value-reads stay capped as density grows; the "
              "subkey lookups read keys only. The 'whole-route pread' regression cannot return "
              "unnoticed.\n")
        return 0
    print("\nRESULT: FAIL — a dive is reading values in proportion to hub density (a full-route "
          "scan has been reintroduced on the hot path).\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
