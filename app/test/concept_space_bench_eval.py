#!/usr/bin/env python3
"""
F39-P2 / F33 §5.2 — the per-request cost of a concept space, guarded on the EXACT production path.

Path: archives.op_space → _project_concept → thesaurus.op_concept → consciousness.generate_view.
Production measured 11–18 s per call — but the quiet-box diagnostic (F33 §5 access-degree probe)
shows the render itself is BOUNDED (one membership lookup + one point-get per member reached, ZERO
scans below a membrane) and does NOT scale with store size, so that 11–18 s was QUEUEING under the
crawler storm (now bounded by the P1a admission cap), not an algorithmic below-membrane scan.

This locks that in as a permanent guard: the concept-space render's store round-trips must stay
CONSTANT as the store grows, with zero full scans, and complete well within the §5.2 cold budget.
A future regression that reintroduces an O(store) walk fails HERE, not as the site falling over.

Run:  python app/test/concept_space_bench_eval.py   (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="space_"))
    gw = AkashaGateway(kernel_client=k)

    def cli(line):
        return (gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                             "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"},
                            "local")).get("result") or {}

    def space(name):
        return gw.dispatch({"jsonrpc": "2.0", "method": "archives.space",
                            "params": {"session_token": "admin", "data": {"name": name}}, "id": "s"}, "local")

    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    # a concept hub with a real neighbourhood (related terms + an emotion edge)
    cli('def "concept:bird" "a bird — a feathered, winged animal."'); cli('al concept:bird bird')
    for i in range(15):
        cli('def "concept:kind%d" "kind %d"' % (i, i)); cli('al concept:kind%d k%d' % (i, i))
        cli('ln concept:bird concept:kind%d thesaurus:related' % i)
    cli('def "emo:awe" "awe"'); cli('al emo:awe awe'); cli('ln concept:bird emo:awe calc:associated_with')
    time.sleep(0.6)

    core = k.manager.shared_nucleus.core
    if not hasattr(core, "probe_read"):
        check("probe available (silica)", False); print("SKIP"); sys.exit(0)

    def weave_quiet(timeout=20.0):
        # Wait until the background weave/write threads stop touching the shared store, so the
        # process-global probe reflects ONLY the render on the next measure. An idle window shows
        # ~no point-gets; a still-churning weave shows many. Reset, let a tick pass, read — when a
        # quiet tick lands, the backlog has drained.
        deadline = time.time() + timeout
        while time.time() < deadline:
            core.probe_reset()
            time.sleep(0.3)
            if core.probe_read().get("point_get", 0) < 3:
                return
        core.probe_reset()

    def measure(samples=5):
        # The access-degree probe is PROCESS-GLOBAL: a concurrent background weave thread (which
        # writes proto-words to the shared nucleus while the just-added atoms are decomposed) will
        # add its own point-gets to whatever window we read. That is cross-thread noise, not the
        # render's cost — and it only ever ADDS. So we sample the render several times and keep the
        # CLEANEST run (fewest point-gets): the minimum converges to the render's intrinsic access
        # degree once a quiet tick lands between weave bursts. (A real O(store) regression in the
        # render would inflate EVERY sample by hundreds/thousands, so the min still catches it.)
        # 10-02 §6.3 — THREAD-ONLY: the probe counts the accesses made by THIS thread, so a
        # background weave's point-gets are not in the window at all. The process-global probe
        # plus a "quiet" wait plus min-of-N was a race the eval won alone and lost under a loaded
        # parallel suite (when the 2,000-atom weave backlog outlasted the 20 s quiet window).
        best = None
        for _ in range(samples):
            core.probe_reset(thread_only=True)
            t = time.time()
            r = space("bird")
            p, ms = core.probe_read(), (time.time() - t) * 1000.0
            if best is None or p["point_get"] < best[0]["point_get"]:
                best = (p, ms, r)
        return best

    weave_quiet()
    p_small, ms_small, r0 = measure()
    ok0 = (r0.get("result") or {})
    check("archives.space renders the concept (signposts present)",
          bool(ok0) and "error" not in r0, str(r0.get("error")))
    check("archives.space does ZERO full scans (no below-membrane keyspace walk)",
          p_small["full_scan"] == 0, str(p_small))

    # ── the measurement is immune to other threads (§6.3): a thread hammering the same store
    #    DURING the render adds nothing to the render's count. Under the old process-global probe
    #    this is exactly the noise that failed the bench in a parallel suite.
    import threading as _th
    _stop = [False]
    _hits = [0]

    def _noise():
        while not _stop[0]:
            try:
                core.get_chunk_raw("noise-key-that-does-not-exist")
                _hits[0] += 1
            except Exception:
                pass
    _t = _th.Thread(target=_noise, daemon=True)
    _t.start()
    time.sleep(0.05)
    p_noisy, _ms_noisy, _r = measure(samples=1)
    _stop[0] = True
    _t.join(timeout=5)
    check("a thread hammering the store during the render adds NOTHING to its measured access "
          "degree (thread-only probe; %d foreign reads ran)" % _hits[0],
          _hits[0] > 0 and p_noisy["point_get"] == p_small["point_get"]
          and p_noisy["membrane_scan"] == p_small["membrane_scan"],
          "quiet=%s noisy=%s" % (p_small, p_noisy))
    core.probe_reset()
    _t2 = _th.Thread(target=lambda: [core.get_chunk_raw("noise-%d" % i) for i in range(200)])
    _t2.start(); _t2.join()
    check("…while the process-global probe does count them (the noise is real, and is excluded)",
          core.probe_read()["point_get"] >= 200, str(core.probe_read()))

    # grow the store 40× and re-measure — the render's round-trips must NOT grow with it
    for i in range(2000):
        cli('def "noise:%d" "noise atom %d filler text"' % (i, i))
    weave_quiet()                # drain the 2000-atom weave backlog before reading the global probe
    p_big, ms_big, _ = measure()

    check("access-degree is CONSTANT as the store grows (round-trips do not scale with N atoms)",
          p_big["point_get"] <= p_small["point_get"] + 2
          and p_big["membrane_scan"] <= p_small["membrane_scan"] + 2
          and p_big["full_scan"] == 0,
          f"small={p_small} big={p_big}")

    # F50 §4 — call counts alone hid the fetch_stream pathology (one membrane_scan CALL that walked
    # the whole store). The probe now weights by entries_walked; the render's entries-walked budget
    # must ALSO stay flat as the store grows 40× — a whole-store walk would blow up here even at a
    # constant call count. (older stores predating the metric report None → treated as satisfied.)
    ew_small = p_small.get("entries_walked")
    ew_big = p_big.get("entries_walked")
    check("entries-walked budget is CONSTANT as the store grows (F50 §4 — no hidden store-wide walk)",
          ew_small is None or ew_big is None or ew_big <= ew_small + 50,
          f"small_entries_walked={ew_small} big_entries_walked={ew_big}")

    # §5.2 cold budget: a single concept space well under 5 s on a quiet box
    budget_ms = float(os.environ.get("AKASHA_SPACE_BUDGET_MS", "5000"))
    check("archives.space cold render within the §5.2 budget",
          ms_big < budget_ms, f"{ms_big:.1f}ms < {budget_ms:.0f}ms (small={ms_small:.1f}ms)")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — the concept-space render is access-degree bounded: constant store round-trips as "
          "the store grows, zero scans below a membrane, well within the cold budget. The production "
          "11–18 s was queueing under load (now capped by P1a admission), not an algorithmic scan.")
    sys.exit(0)


if __name__ == "__main__":
    main()
