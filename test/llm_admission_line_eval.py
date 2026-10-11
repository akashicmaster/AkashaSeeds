#!/usr/bin/env python3
"""
One admission line per scheduled run, at the point that decided it (step 0 §4, item 2).

The pool logs its own arithmetic when it is asked for calls, and once per hour when it refuses. It
hears nothing at all about a run that asked for NOTHING — and that silence is the one worth breaking.
A scheduled run whose appetite was lost between its declaration and admission arrives looking exactly
like an ordinary batch job, so the log of a run that went out unmetered and the log of a run that
never happened are the same log. That is what cost two days on the live cell.

So admission emits one line for every scheduled run, carrying the outcome as a vocabulary id:

    [llm] admission reserved  program=… provider=… calls=5 declared=true  free=…
    [llm] admission refused   program=… provider=… calls=5 declared=true  free=0
    [llm] admission unmetered program=… provider=-  calls=0 declared=true free=-

and nothing for an ordinary batch job, which is not a scheduled run and must not add a line per
submission.

Run:  python test/llm_admission_line_eval.py     (exit 0 = all pass)
"""
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)

from lib.akasha.api import gate as _gate                               # noqa: E402
from lib.akasha.workbench import admission, llm_pool                   # noqa: E402

_fails = []
PROVIDER = "evalprov"
OWNER = "eval-owner"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())

    def admission_lines(self):
        return [ln for ln in self.lines if ln.startswith("[llm] admission ")]


# ── the smallest kernel/session job.submit will accept ───────────────────────────────────────────
class _Session:
    client_id = OWNER
    active_scopes = ["scope:sys:admin"]


class _Jcl:
    def get_job(self, _id):
        return None


class _Harmonia:
    def __init__(self):
        self.jobs = []

    def submit_job(self, job, job_class=None):
        self.jobs.append(job)
        return job


class _Kernel:
    def __init__(self):
        self.jcl_worker = _Jcl()
        self.harmonia = _Harmonia()


def _fresh_pool(cap=3000):
    llm_pool._MEM.clear()
    llm_pool._REFUSE_LOG_AT.clear()
    llm_pool.caps = lambda provider: (cap, 0)
    llm_pool._spent_of = lambda provider: {"calls_today": 0, "tokens_month": 0}


def _submit(cap_handler, **extra):
    data = {"steps": [{"method": "ping", "params": {}}], "label": "eval job"}
    data.update(extra)
    cap_handler.lines.clear()
    return admission.handle_job_submit(_Kernel(), "eval", data, _Session())


def main():
    print("=" * 78)
    print("One admission line per scheduled run")
    print("=" * 78)

    # A CELL OF ITS OWN. This eval has no kernel — it drives `admission.handle_job_submit`
    # directly — so nothing binds the gate for it, and the line it writes below would land in the
    # DEFAULT cell's table and still be there on the next run. The second run would then find
    # `eval-owner` already a librarian and the "no line" case would quietly stop being tested.
    # Binding a throwaway cell is what a kernel does at construction; a kernel-less eval does it
    # itself. (Before the paths were split this wrote into the repository's `config/identity/`,
    # which is the leak `gate_cell_files_eval` now holds shut.)
    _gate.bind(tempfile.mkdtemp(prefix="llm_adm_"))

    cap = _Capture()
    lg = logging.getLogger("Akasha.Kernel")
    lg.addHandler(cap)
    lg.setLevel(logging.INFO)
    # The pool logs on its own logger; capture that too, so "this is the only reservation line"
    # is a claim about what a reader actually sees and not about one logger's share of it.
    lg_pool = logging.getLogger("Akasha.LLM")
    lg_pool.addHandler(cap)
    lg_pool.setLevel(logging.INFO)

    # ── WHO MAY SUBMIT AT ALL: a job is a `run`, and a `run` needs a line ────────────────────────
    #
    # The ruling is explicit that `job.submit` is not an action of its own ("a `run` is a job;
    # whoever may `run` may submit the job that runs it and nothing else"), so admission asks
    # `gate(owner, run)` and an identity named by no line is a GUEST, which may only read. This
    # eval's owner is a bare fake identity, so it has to hold a line like any other submitter —
    # and asserting the refusal first is what keeps the rest of the file honest: without it, every
    # "no admission line" check below would pass on a submit that never got as far as admission.
    _fresh_pool()
    _r0 = _submit(cap)
    check("an identity named by NO line cannot submit a job at all (a run needs a line)",
          "error" in _r0 and _gate.R_ACTION in str(_r0["error"].get("message", "")),
          str(_r0)[:140])
    check("…and it produced no admission line, because it never reached admission",
          cap.admission_lines() == [], str(cap.admission_lines()))
    _gate.assign(OWNER, "librarian")

    # ── an ordinary batch job is not a scheduled run: no line ────────────────────────────────────
    _fresh_pool()
    _submit(cap)
    check("an ordinary batch job adds no admission line", cap.admission_lines() == [],
          str(cap.admission_lines()))

    # ── a scheduled run that reserves ────────────────────────────────────────────────────────────
    _fresh_pool()
    r = _submit(cap, program="eval/one", llm_provider=PROVIDER,
                llm_calls_per_run=5, llm_declared=True)
    lines = cap.admission_lines()
    check("a scheduled run with an appetite logs exactly one line",
          len(lines) == 1, str(lines))
    check("…and it says reserved, with the programme, the appetite and the derived key",
          bool(lines) and lines[0].startswith("[llm] admission reserved ")
          and "program=eval/one" in lines[0] and "calls=5" in lines[0]
          and "declared=true" in lines[0], lines[0] if lines else "")
    # Step 2 §6 — the pool used to log `[llm] reserved` as well, because a second caller reserved
    # outside admission and had no other trace. That caller went with station.py, so this is the ONE
    # reservation line and it carries the pool arithmetic the other one had: committed = cap − free.
    check("…and it carries the day's pool, so nothing the pool's own line said is lost",
          bool(lines) and "free=" in lines[0] and "cap=" in lines[0], lines[0] if lines else "")
    check("…and it is the ONLY line logged for the reservation (the pool no longer logs its own)",
          len([ln for ln in cap.lines if ln.startswith("[llm] reserved")]) == 0,
          str([ln for ln in cap.lines if ln.startswith("[llm] reserved")]))
    check("…and the job was admitted with its reservation",
          "error" not in r and r.get("result", {}).get("job_id"))

    # ── a scheduled run with NO appetite — the case no other line can carry ──────────────────────
    _fresh_pool()
    _submit(cap, program="eval/two", llm_calls_per_run=0, llm_declared=True)
    lines = cap.admission_lines()
    check("a scheduled run that asked for nothing is still one line, marked unmetered",
          len(lines) == 1 and lines[0].startswith("[llm] admission unmetered ")
          and "program=eval/two" in lines[0] and "calls=0" in lines[0], str(lines))

    # ── a scheduled run the pool refuses ─────────────────────────────────────────────────────────
    _fresh_pool(cap=4)
    r = _submit(cap, program="eval/three", llm_provider=PROVIDER,
                llm_calls_per_run=5, llm_declared=True)
    lines = cap.admission_lines()
    check("a refused run logs one line too, and is not admitted",
          len(lines) == 1 and lines[0].startswith("[llm] admission refused ")
          and "free=" in lines[0] and r.get("error", {}).get("code") == -32005, str(lines))

    # ── the outcomes are vocabulary ids ──────────────────────────────────────────────────────────
    ids = (admission.ADMIT_RESERVED, admission.ADMIT_REFUSED, admission.ADMIT_UNMETERED)
    check("the three outcomes are declared ids, not strings written at the call site",
          len(set(ids)) == 3 and all(i.islower() and i.isalpha() for i in ids), str(ids))

    # ── the driver path carries the zero appetite that makes `unmetered` reachable ───────────────
    src = open("lib/akasha/concepts/workflow.py", encoding="utf-8").read()
    i = src.find('_appetite(_ACTIVE_KERNEL, name, branch)')
    win = src[i:i + 1400] if i >= 0 else ""
    check("wf.advance passes the appetite to admission even when it is zero",
          i >= 0 and 'int(_cpr or 0)' in win and '_data["llm_declared"]' in win,
          "no guard on _cpr > 0 around the carried fields")

    lg.removeHandler(cap)
    lg_pool.removeHandler(cap)
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — every scheduled run leaves exactly one admission line naming its outcome; "
          "an ordinary batch job leaves none.")
    sys.exit(0)


if __name__ == "__main__":
    main()
