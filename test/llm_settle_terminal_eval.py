#!/usr/bin/env python3
"""
A prepaid job releases its LLM reservation at EVERY terminal transition (step 0 §4, item 1).

The reservation is a prepayment. `llm_pool.reserve()` holds a run's calls out of today's pool at
admission so a run can never exhaust the cap halfway; `llm_pool.settle()` gives back whatever the
run did not spend. Between those two the calls are `reserved` — committed, unspendable by anyone
else, and counted against the next admission.

So a terminal transition that does not settle is not a cosmetic gap: the pool shrinks by one run's
worth, permanently, until the UTC day rolls over. Repeat it a few times and admission refuses under
a cap that looks nearly empty — the `refused=88 with spent=219 ≪ cap 3000` shape.

Before this the worker settled on DONE and on FAILED-from-the-run-loop. Four other paths assign a
terminal status and did not:

    cancel()                       a job cancelled while still PENDING
    _wake_dependents  → CANCEL     a job cancelled because a dependency failed
    _run_loop         → CANCEL     the same, found at the gate instead of at the wake
    _acquire()        → FAILED     a job whose owner session could not be acquired

The last one is a FAILED job that never reached `_finish_failed` at all — the named symptom.

Acceptance (the order's): `reserved=0` in the Health segment after a failed job. Checked here for
every terminal path, plus the two halves of the guarantee: `settle` releases ONCE (a second call
must not subtract another job's calls), and the worker settles ALWAYS.

Run:  python test/llm_settle_terminal_eval.py     (exit 0 = all pass)
"""
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)

from lib.akasha.workbench import llm_pool                              # noqa: E402
from lib.akasha.jcl.worker import JCLWorker                            # noqa: E402
from lib.akasha.jcl.job import JCLJob, JCLStep, PENDING, FAILED, CANCELLED  # noqa: E402

_fails = []
PROVIDER = "evalprov"
CALLS = 7


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


# ── a pool with a cap, held in process memory (no store injected → llm_pool._MEM) ────────────────
def _fresh_pool():
    """Reset the in-process pool and give the eval provider a cap of its own."""
    llm_pool._MEM.clear()
    llm_pool._REFUSE_LOG_AT.clear()
    llm_pool.caps = lambda provider: (3000, 0)          # cap_calls, cap_tokens
    llm_pool._spent_of = lambda provider: {"calls_today": 0, "tokens_month": 0}


def reserved_now():
    """What Health would print: the `reserved=` field of the provider's segment."""
    seg = llm_pool.health_segment(PROVIDER)
    m = re.search(r"reserved=(\d+)", seg)
    return (int(m.group(1)) if m else None), seg


# ── a worker with no threads: __init__ starts two, and this eval drives the paths by hand ────────
class _Hooks:
    """The heart's hook table (`kernel.api.hooks`), with the one entry this eval needs — the same
    late-bound name the workbench manifest declares."""
    hooks = {"llm_settle": llm_pool.settle}


class _Kernel:
    harmonia = None
    api = _Hooks()


def _worker():
    w = JCLWorker.__new__(JCLWorker)
    w._kernel = _Kernel()
    w._jobs, w._order, w._blocked = {}, [], {}
    import threading
    w._lock = threading.Lock()
    return w


def _api_hook_reachable(worker) -> bool:
    """Ask the worker's own B10 release path whether it found the hook, by driving one job through
    it and seeing the pool move. Any AttributeError on the way is a dead call site."""
    probe = JCLJob(owner="probe", label="probe", steps=[JCLStep(method="ping", params={})])
    probe.llm_reservation = llm_pool.reserve(PROVIDER, "probe-program", 1)
    before, _ = reserved_now()
    worker._settle_llm(probe)
    after, _ = reserved_now()
    return before == 1 and after == 0


def _job(worker, owner="eval-owner"):
    j = JCLJob(owner=owner, label="eval", steps=[JCLStep(method="ping", params={})])
    j.llm_reservation = llm_pool.reserve(PROVIDER, "eval-program", CALLS)
    j.started_at = time.time()
    worker._jobs[j.job_id] = j
    worker._order.append(j.job_id)
    return j


def main():
    print("=" * 78)
    print("A prepaid job releases its reservation at every terminal transition")
    print("=" * 78)

    # ── the worker can actually REACH the pool ───────────────────────────────────────────────────
    # First, because until this seed it could not: all four B10 call sites read `self.kernel`, an
    # attribute JCLWorker does not have (it holds `self._kernel`). `_api.hook(self.kernel, …)`
    # therefore raised AttributeError before the lookup, and every site swallowed it — so settle,
    # begin_run, end_run and the cost axis were dead code, and a reservation was NEVER released by
    # anything. A local stub for `kernel` in this eval would have hidden exactly that, so the eval
    # uses the real attribute and checks the reach before it checks the behaviour.
    _fresh_pool()
    w = _worker()
    check("the worker reaches the heart's hook table through an attribute it really has",
          _api_hook_reachable(w), "llm_settle")

    # ── the prepayment is real: reserving moves the pool ─────────────────────────────────────────
    j = _job(w)
    n, seg = reserved_now()
    check("a reservation shows in Health as calls held out of today's pool", n == CALLS,
          "reserved=%s in %r" % (n, seg.strip()))
    check("the job carries the reservation into the run", bool(j.llm_reservation))

    # ── the named symptom: a FAILED job leaves reserved=0 ────────────────────────────────────────
    w._finish_failed(j, RuntimeError("step blew up"), None, None, rollback=False)
    n, seg = reserved_now()
    check("after a failed job, reserved=0 in Health", n == 0 and j.status == FAILED,
          "reserved=%s status=%s" % (n, j.status))

    # ── every other terminal path ────────────────────────────────────────────────────────────────
    paths = []

    def _path(name, drive, expect_status):
        _fresh_pool()
        wk = _worker()
        job = _job(wk)
        before, _ = reserved_now()
        drive(wk, job)
        after, segment = reserved_now()
        paths.append((name, before, after, job.status))
        check("%s → reserved returns to 0" % name,
              before == CALLS and after == 0 and job.status == expect_status,
              "%s → %s, status=%s" % (before, after, job.status))

    def _cancel_pending(wk, job):
        job.status = PENDING
        wk.cancel(job.job_id, requester=job.owner)

    def _cascade(wk, job):
        dep = JCLJob(owner=job.owner, label="dep", steps=[JCLStep(method="ping", params={})])
        dep.status = FAILED
        job.depends_on = [dep.job_id]
        wk._jobs[dep.job_id] = dep
        wk._blocked[job.job_id] = job
        wk._wake_dependents(dep)

    def _session_gone(wk, job):
        class _NoManager:
            def get_session(self, _owner):
                raise RuntimeError("session unavailable")
        wk._kernel.manager = _NoManager()
        wk._acquire(job)

    def _done(wk, job):
        job.step_done = job.step_count
        wk._finish_done(job)

    _path("a job cancelled while PENDING", _cancel_pending, CANCELLED)
    _path("a job cancelled by a failed dependency", _cascade, CANCELLED)
    _path("a job whose session could not be acquired", _session_gone, FAILED)
    _path("a job that finished normally", _done, "DONE")

    # ── settle releases ONCE: a second call must not eat another job's calls ─────────────────────
    _fresh_pool()
    w2 = _worker()
    a = _job(w2)
    b = _job(w2)                       # a second prepaid job, still outstanding
    res_a = a.llm_reservation
    w2._finish_failed(a, RuntimeError("x"), None, None, rollback=False)
    mid, _ = reserved_now()
    again = llm_pool.settle(res_a)     # the same dict, a second time
    after, seg = reserved_now()
    check("settling the same reservation twice leaves the OTHER job's calls intact",
          mid == CALLS and after == CALLS and again.get("repeat") is True,
          "mid=%s after=%s repeat=%s" % (mid, after, again.get("repeat")))

    # ── a settle that cannot run does not silently drop the handle ───────────────────────────────
    _fresh_pool()
    w3 = _worker()
    c = _job(w3)
    w3._kernel.api = type("api", (), {"hooks": {}})()
    w3._finish_failed(c, RuntimeError("y"), None, None, rollback=False)
    check("with no settle hook reachable, the reservation is KEPT for a later release "
          "(never dropped into the pool's blind spot)", c.llm_reservation is not None)

    print()
    print("  path                                                  before  after  status")
    for name, before, after, status in paths:
        print("   %-52s %5s  %5s  %s" % (name[:52], before, after, status))
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — DONE, FAILED and CANCELLED all release the prepayment, the two paths "
          "that never enter the run loop release it too, and a repeat release is a no-op.")
    sys.exit(0)


if __name__ == "__main__":
    main()
