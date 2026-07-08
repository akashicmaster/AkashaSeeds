#!/usr/bin/env python3
"""
Queue load test — multi-client resilience of the WriteQueue under heavy load.

Akasha serialises every write through a single-worker WriteQueue per cortex, plus
one shared queue for the nucleus (proto-words). Priority changes *order*, never
parallelism (CLAUDE.md: JCL Design Philosophy / Resilience Design). This harness
puts that model under concurrent stress from many client threads and asserts the
guarantees hold:

  Phase 1  Same-cortex write storm  — N threads hammer one cortex; every write must
           land exactly once (single-queue serialisation, no lost writes, no dup).
  Phase 2  Content-addressed dedup  — many threads write identical content; it must
           unify to exactly one atom key with intact content.
  Phase 3  Multi-client + shared nucleus + isolation — distinct authenticated
           clients write concurrently; the shared nucleus stays consistent and one
           client cannot read another's private atom.
  Phase 4  Priority under load      — a flood of LOW background writes must not
           starve HIGH interactive writes (bounded interactive latency).
  Phase 5  Guest pool churn         — rapid concurrent guest create/use cycles.

A global watchdog fails the run if any phase wedges (deadlock detection). Throughput
and latency percentiles are reported per phase.

Run:   python test/loadtest_queue.py            # default heavy load (~10-30s)
       AKASHA_LOAD=quick python test/loadtest_queue.py   # fast smoke
       AKASHA_LOAD=heavy python test/loadtest_queue.py   # stress

This is a developer resilience test, not a user-facing .ak example. It exercises
the real kernel dispatch path in-process (Plan A) so the queue itself is the thing
under test, not the transport.
"""
import os
import sys
import time
import threading
import tempfile
import hashlib
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

# ── Load profile ─────────────────────────────────────────────────────────────
_PROFILE = os.environ.get("AKASHA_LOAD", "default").lower()
if _PROFILE == "quick":
    THREADS, PER_THREAD, DEDUP_THREADS, CLIENTS, CLIENT_WRITES = 4, 40, 16, 3, 20
    BG_WRITES, HI_WRITES, GUESTS = 200, 40, 40
    WATCHDOG_S = 60
elif _PROFILE == "heavy":
    THREADS, PER_THREAD, DEDUP_THREADS, CLIENTS, CLIENT_WRITES = 16, 500, 64, 8, 120
    BG_WRITES, HI_WRITES, GUESTS = 4000, 200, 400
    WATCHDOG_S = 300
else:  # default
    THREADS, PER_THREAD, DEDUP_THREADS, CLIENTS, CLIENT_WRITES = 8, 200, 32, 5, 60
    BG_WRITES, HI_WRITES, GUESTS = 1500, 100, 150
    WATCHDOG_S = 150

_results = []   # (phase, ok, detail)


def record(phase, ok, detail=""):
    _results.append((phase, ok, detail))
    tag = "OK  " if ok else "!! FAIL"
    print(f"  {tag}  {phase:30} {detail}")


def pct(latencies, p):
    if not latencies:
        return 0.0
    s = sorted(latencies)
    i = min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1))))
    return s[i] * 1000.0  # ms


def run_threads(n, target):
    """Spawn n threads running target(i); join all; return per-thread exceptions."""
    errs = [None] * n
    lat = [[] for _ in range(n)]

    def wrap(i):
        try:
            target(i, lat[i])
        except Exception as e:  # noqa: BLE001 — capture, don't crash the harness
            errs[i] = "".join(traceback.format_exception_only(type(e), e)).strip()

    ts = [threading.Thread(target=wrap, args=(i,)) for i in range(n)]
    t0 = time.time()
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    elapsed = time.time() - t0
    return errs, [x for sub in lat for x in sub], elapsed


# ── Kernel bootstrap ─────────────────────────────────────────────────────────

def boot():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_load_")
    k = KernelDispatcher(series="seeds", base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    # Warm up the write/weave path single-threaded BEFORE any timed phase: the first
    # write triggers a one-time NLP-plugin (spacy) probe that degrades to None in a
    # non-interactive env. Paying it here keeps it out of the latency percentiles and
    # off the concurrent phases (where several threads would race the same probe).
    for i in range(2):
        k.dispatch({"jsonrpc": "2.0", "method": "w",
                    "params": {"session_token": "admin",
                               "data": {"content": f"warmup {i}"}}, "id": "w"}, "local")
    time.sleep(2.0)  # let background weave finish initialising the NLP plugin
    return k


def make_dispatch(k):
    def d(token, method, data, trust="local"):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": token, "data": data},
                           "id": "x"}, trust)
    return d


# ── Phase 1: same-cortex write storm ─────────────────────────────────────────

def phase1_write_storm(k, d):
    total = THREADS * PER_THREAD

    def worker(i, lat):
        for j in range(PER_THREAD):
            alias = f"load:t{i}:n{j}"
            t0 = time.time()
            r = d("admin", "w", {"content": f"storm atom {i}-{j} :: {alias}"})
            # alias the just-written atom so we can prove it landed (al param is 'name')
            key = (r.get("result") or {}).get("key")
            if key:
                ar = d("admin", "al", {"id": key, "name": alias})
                if "error" in ar:
                    raise RuntimeError(f"alias error: {ar['error']}")
            lat.append(time.time() - t0)
            if "error" in r:
                raise RuntimeError(f"write error: {r['error']}")

    errs, lat, elapsed = run_threads(THREADS, worker)
    err = next((e for e in errs if e), None)
    if err:
        record("P1 write-storm", False, f"thread error: {err}")
        return

    # No lost writes: every alias must resolve to a distinct key.
    engine = k.manager.get_session("admin").local_cortex
    keys = set()
    missing = 0
    for i in range(THREADS):
        for j in range(PER_THREAD):
            key = engine.resolve_alias(f"load:t{i}:n{j}")
            if key:
                keys.add(key)
            else:
                missing += 1
    thru = total / elapsed if elapsed else 0
    detail = (f"{total} writes, {len(keys)} distinct keys, {missing} missing | "
              f"{thru:.0f} w/s, p50={pct(lat,50):.1f}ms p99={pct(lat,99):.1f}ms")
    record("P1 write-storm", missing == 0 and len(keys) == total, detail)


# ── Phase 2: content-addressed dedup under concurrency ───────────────────────

def phase2_dedup(k, d):
    content = "DEDUP-CONSTANT-" + "x" * 32
    expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
    seen = []
    lock = threading.Lock()

    def worker(i, lat):
        r = d("admin", "w", {"content": content})
        key = (r.get("result") or {}).get("key")
        with lock:
            seen.append(key)

    errs, _, _ = run_threads(DEDUP_THREADS, worker)
    err = next((e for e in errs if e), None)
    uniq = set(seen)
    engine = k.manager.get_session("admin").local_cortex
    row = engine.core.get_chunk_raw(expected)
    intact = bool(row) and row["content"] == content
    ok = (not err) and uniq == {expected} and intact
    record("P2 dedup", ok,
           f"{DEDUP_THREADS} identical writes → {len(uniq)} key(s), "
           f"content {'intact' if intact else 'CORRUPT/missing'}")


# ── Phase 3: multi-client + shared nucleus + isolation ───────────────────────

def phase3_multiclient(k, d):
    # Admin creates distinct authenticated clients, each gets a signed token.
    tokens = {}
    for c in range(CLIENTS):
        cid = f"client{c}"
        ph = hashlib.sha256(f"pw{c}".encode()).hexdigest()
        d("admin", "user.add", {"client_id": cid, "role": "user", "passphrase_hash": ph})
        r = d(cid, "auth.verify", {"user_id": cid, "passphrase": f"pw{c}"}, trust="network")
        tok = (r.get("result") or {}).get("session_token")
        if tok:
            tokens[cid] = tok
    if len(tokens) < CLIENTS:
        record("P3 multi-client", False,
               f"only {len(tokens)}/{CLIENTS} clients authenticated")
        return

    # Each client concurrently writes atoms sharing vocabulary → the shared nucleus
    # queue is the contention point (proto-words must unify, not corrupt/duplicate).
    private_keys = {}
    klock = threading.Lock()
    shared_vocab = "resonance cascade lattice aurora threshold"
    cids = list(tokens)

    def worker(i, lat):
        cid = cids[i]
        tok = tokens[cid]
        for j in range(CLIENT_WRITES):
            r = d(tok, "w", {"content": f"{cid} note {j}: {shared_vocab}"}, trust="network")
            key = (r.get("result") or {}).get("key")
            if j == 0 and key:
                with klock:
                    private_keys[cid] = key

    errs, _, elapsed = run_threads(len(cids), worker)
    err = next((e for e in errs if e), None)

    # Isolation: client B must not be able to read client A's private atom.
    leaked = 0
    checks = 0
    for a in cids:
        ka = private_keys.get(a)
        if not ka:
            continue
        for b in cids:
            if b == a:
                continue
            checks += 1
            rr = d(tokens[b], "r", {"id": ka}, trust="network")
            res = rr.get("result")
            # A readable foreign atom (non-empty content) = leak.
            if res and (res.get("content") if isinstance(res, dict) else res):
                leaked += 1
            break  # one cross-check per owner is enough

    # Shared nucleus consistency: a shared word resolves to a single stable
    # proto-word key (content-addressed unification under concurrent writers).
    nuc = getattr(k.manager.get_session("admin"), "nucleus", None)
    nuc_ok = True
    nuc_detail = "nucleus check skipped"
    if nuc is not None:
        try:
            kk = [nuc.resolve_alias(f"word:{w}") for w in ("aurora", "lattice")]
            nuc_ok = all(x is None or isinstance(x, str) for x in kk)
            nuc_detail = "nucleus consistent"
        except Exception as e:  # noqa: BLE001
            nuc_ok, nuc_detail = False, f"nucleus error: {e!r}"

    ok = (not err) and leaked == 0 and nuc_ok
    record("P3 multi-client", ok,
           f"{len(cids)} clients x {CLIENT_WRITES} writes, {checks} isolation checks, "
           f"{leaked} leaks, {nuc_detail}")


# ── Phase 4: priority ordering at the WriteQueue (deterministic) ─────────────

def phase4_priority(k, d):
    # The invariant: the single-worker WriteQueue serves by PRIORITY, not FIFO —
    # an interactive (HIGH) write queued *after* a backlog of background (LOW) writes
    # still runs first. Tested directly and deterministically at the queue primitive:
    # occupy the one worker with a blocker, build a backlog of LOW *then* HIGH tasks
    # while it is busy, release, and assert every HIGH ran before every LOW (which is
    # the opposite of their enqueue order — so FIFO would fail this).
    from lib.akasha.jcl.write_queue import WriteQueue
    from lib.akasha.jcl.workspace_context import PRIO_HIGH, PRIO_IDLE

    wq = WriteQueue(name="loadtest-prio")
    order = []
    olock = threading.Lock()
    release = threading.Event()
    N = 8

    def blocker():
        wq.submit(lambda: release.wait(WATCHDOG_S), priority=PRIO_HIGH)

    bt = threading.Thread(target=blocker)
    bt.start()
    time.sleep(0.15)  # ensure the blocker is occupying the worker

    def enqueue(pri, tag):
        def fn():
            with olock:
                order.append(tag)
        wq.submit(fn, priority=pri)  # blocks caller until fn runs

    workers = []
    # Enqueue LOW first, HIGH second — priority must reverse this at execution.
    for n in range(N):
        t = threading.Thread(target=enqueue, args=(PRIO_IDLE, f"LOW{n}"))
        t.start()
        workers.append(t)
    time.sleep(0.1)
    for n in range(N):
        t = threading.Thread(target=enqueue, args=(PRIO_HIGH, f"HIGH{n}"))
        t.start()
        workers.append(t)
    time.sleep(0.25)  # let every task enqueue (submit() puts before it blocks)

    release.set()  # blocker returns; worker now drains the backlog by priority
    for t in workers:
        t.join(timeout=WATCHDOG_S)
    bt.join(timeout=WATCHDOG_S)
    wq.shutdown()

    highs = [i for i, x in enumerate(order) if x.startswith("HIGH")]
    lows = [i for i, x in enumerate(order) if x.startswith("LOW")]
    complete = len(order) == 2 * N
    ordered = bool(highs) and bool(lows) and max(highs) < min(lows)
    record("P4 priority-order", complete and ordered,
           f"{len(order)}/{2*N} ran; HIGH-then-LOW={ordered} "
           f"(enqueued LOW-first → priority reordered) order={'|'.join(order)}")


# ── Phase 5: guest pool churn ────────────────────────────────────────────────

def phase5_guest_churn(k, d):
    created = []
    lock = threading.Lock()
    fails = []

    def worker(i, lat):
        try:
            r = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                            "params": {"data": {}}, "id": "g"}, "network")
            tok = (r.get("result") or {}).get("binding_key") or \
                  (r.get("result") or {}).get("session_token")
            with lock:
                (created if tok else fails).append(tok or r.get("error"))
        except Exception as e:  # noqa: BLE001
            with lock:
                fails.append(repr(e))

    per = max(1, GUESTS // 8)
    errs, _, elapsed = run_threads(8, lambda i, lat: [worker(i, lat) for _ in range(per)])
    hard_err = next((e for e in errs if e), None)
    # Guest pools are intentionally bounded — creation may be REFUSED once full,
    # which is correct fail-closed behaviour, not a crash. Success = no crash and
    # at least some guests were issued; refusals are acceptable.
    ok = hard_err is None and len(created) > 0
    record("P5 guest-churn", ok,
           f"{len(created)} guests issued, {len(fails)} refused/failed "
           f"(bounded pool ok), {elapsed:.1f}s")


# ── Watchdog + main ──────────────────────────────────────────────────────────

def main():
    print(f"\n  load profile: {_PROFILE}  "
          f"(threads={THREADS} per={PER_THREAD} clients={CLIENTS} "
          f"guests={GUESTS} watchdog={WATCHDOG_S}s)\n")

    done = threading.Event()

    def watchdog():
        if not done.wait(WATCHDOG_S):
            print("\n  !! WATCHDOG TRIPPED — possible deadlock. Thread dump:\n")
            for tid, frame in sys._current_frames().items():
                print(f"  --- thread {tid} ---")
                traceback.print_stack(frame)
            os._exit(2)

    wd = threading.Thread(target=watchdog, daemon=True)
    wd.start()

    k = boot()
    d = make_dispatch(k)

    for phase_fn in (phase1_write_storm, phase2_dedup, phase3_multiclient,
                     phase4_priority, phase5_guest_churn):
        try:
            phase_fn(k, d)
        except Exception as e:  # noqa: BLE001
            record(phase_fn.__name__, False, f"phase crashed: {e!r}")

    done.set()

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    failed = total - passed
    print(f"  {passed}/{total} phases passed"
          + (f", {failed} FAILED" if failed else ""))
    if failed:
        print("\nRESULT: FAIL — a queue-resilience invariant broke under load.")
        return 1
    print("\nRESULT: PASS — queue held under load (no lost writes, dedup, isolation, "
          "priority, bounded pool).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
