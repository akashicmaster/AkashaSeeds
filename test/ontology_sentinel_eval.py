#!/usr/bin/env python3
"""
Group 1 — the ontology engine does only the work a CONTENT change asks for.

The 09-26 deploy: two changed packs (35 atoms) cost nine minutes; the relations phase read 489 files
"changed" for 22 links + 32 `set.add`; one pack's phase-1 wait (287 s for 13 atoms) sat behind
another pack's weave; 15 min 28 s dark. Three different keys answered "has this file changed?"
(size, mtime+size, raw bytes), so a comment re-parsed a pack and a fresh extraction re-read every
file; the canon plan covered the whole ontology on any change; one gate covered everything.

This eval runs the REAL loader (`ontology/loader.py`) over a small ontology of its own
(`AKASHA_PROJECT_DIR`), on a real cell, and counts what it actually does — the jobs it submits, the
steps in them, the `[onto]` phase lines it writes. The loader's older evals mirrored its logic in a
copy; a copy cannot see the code it is checking.

  (a) a comment-only edit → no atom job, no relation step; both gates open fast
  (b) one def edit → that file's atoms only, and no canon pass (the loader repairs nothing, §3)
  (c) a fresh extraction of the same files (all mtimes new) → nothing re-parsed
  (d) the reconcile of the largest pack stays under a stated memory bound, and says its Δrss

Run:  python test/ontology_sentinel_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import time
import tracemalloc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []
BIG_DEFS = 4000          # the "largest pack" of (d) — sized so the eval stays in minutes
RECONCILE_BOUND_MB = 16  # (d) peak Python allocation of one pack's reconcile, at BIG_DEFS defs


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Log(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, rec):
        self.lines.append(rec.getMessage())


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _project(root):
    """A two-pack ontology plus one big pack, laid out as the real one is."""
    ont = os.path.join(root, "ontology")
    _write(os.path.join(ont, "p_one", "f1.ak"), [
        "# p_one / f1 — dishes and a recipe",
        'def "dish:alpha" "Alpha — a test dish"',
        'def "dish:beta" "Beta — a test dish"',
        'def "recipe:alpha" "Alpha recipe — how alpha is made"',
        "al dish:alpha alphadish",
        "ln dish:alpha dish:beta thesaurus:related",
        'set.add name="demo:dishes" id="dish:alpha"',
    ])
    _write(os.path.join(ont, "p_one", "f2.ak"), [
        'def "dish:gamma" "Gamma — a test dish"',
        'set.add name="demo:dishes" id="dish:gamma"',
    ])
    _write(os.path.join(ont, "p_two", "g1.ak"), [
        'def "dish:delta" "Delta — a test dish"',
        'def "recipe:delta" "Delta recipe"',
        "ln dish:delta dish:alpha thesaurus:related",
    ])
    big = ['def "bigpack:item%05d" "Big item %d"' % (i, i) for i in range(BIG_DEFS)]
    _write(os.path.join(ont, "p_big", "big.ak"), big)
    for pn in ("p_one", "p_two", "p_big"):
        _write(os.path.join(ont, pn, "PACK.json"), [json.dumps({"label": pn})])
    _write(os.path.join(ont, "REGISTRY.json"), [json.dumps({"version": 2, "packages": [
        {"name": "p_one", "autoload": True}, {"name": "p_two", "autoload": True},
        {"name": "p_big", "autoload": True}]})])
    _write(os.path.join(root, "config", "ontology", "packs.json"), [json.dumps({"load_all": True})])
    return ont


class _Spy:
    """What the loader SUBMITS — label and step count of every JCL job — for one run."""
    def __init__(self, k):
        self.k, self.jobs = k, []
        self._orig = k.harmonia.submit_job

        def _submit(job, job_class=None, _o=self._orig):
            self.jobs.append((str(getattr(job, "label", "")), len(getattr(job, "steps", []) or [])))
            return _o(job, job_class=job_class) if job_class is not None else _o(job)
        k.harmonia.submit_job = _submit

    def reset(self):
        self.jobs = []

    def atom_jobs(self):
        return [l for l, _n in self.jobs if l.startswith("ont.ak.") and ":" in l
                and not l.startswith(("ont.ak.relations", "ont.ak.canon", "ont.ak.links",
                                      "ont.ak.sentinel", "ont.ak.atoms_sentinel",
                                      "ont.ak.corrections"))]

    def steps(self, prefix):
        return sum(n for l, n in self.jobs if l.startswith(prefix))


def _line(log, prefix):
    got = [l for l in log.lines if l.startswith(prefix)]
    return got[-1] if got else ""


def _num(line, key):
    for tok in line.split():
        if tok.startswith(key + "="):
            try:
                return int(tok.split("=", 1)[1])
            except ValueError:
                return -1
    return -1


def main():
    print("=" * 78)
    print("Group 1 — the ontology engine does only what a CONTENT change asks for")
    print("=" * 78)
    root = tempfile.mkdtemp(prefix="onto_sentinel_eval_")
    ont = _project(root)
    os.environ["AKASHA_PROJECT_DIR"] = root
    # the fixture project is the whole project: its application root is its own (empty) `app/`,
    # so the loader reads this ontology only, not the repository's application packs
    os.environ["AKASHA_APP_DIR"] = os.path.join(root, "app")

    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology import loader as L
    from lib.akasha.api import schedule as _sched
    _real_boot = KernelDispatcher._boot_load_ontology
    KernelDispatcher._boot_load_ontology = lambda self: None          # we drive the loader ourselves
    k = KernelDispatcher(series="thesaurus", base_dir=os.path.join(root, "cell"))
    # genesis re-triggers the boot load on a thread of its own; kept patched through it, or a second
    # concurrent load races the one under test (the first version of this eval counted every atom
    # job twice for exactly that reason).
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    time.sleep(1.0)
    k._boot_daemons_started = True        # the post-load daemons (corpus bootstraps) are not under test
    log = _Log()
    logging.getLogger("Akasha.Kernel").addHandler(log)
    logging.getLogger("Akasha.Kernel").setLevel(logging.INFO)
    spy = _Spy(k)

    def run(label):
        log.lines.clear()
        spy.reset()
        k._schedule_gates = None          # a fresh process's gates
        t0 = time.time()
        L.boot_load_ontology(k)
        return time.time() - t0

    print("\n  ── first load of a fresh cell ──")
    t_first = run("first")
    check("the first load submits atom jobs for every pack", len(spy.atom_jobs()) >= 4,
          str(spy.atom_jobs()))
    rel = _line(log, "[onto] relations")
    check("…says what the relations phase did in one line", bool(rel), rel or "no [onto] relations line")
    check("…and `ontology.loaded` and `ontology.normalized` are both open when it returns",
          _sched.gate_open(k, "ontology.loaded") and _sched.gate_open(k, "ontology.normalized"))

    print("\n  ── an UNCHANGED restart ──")
    t_same = run("same")
    rel = _line(log, "[onto] relations")
    check("no atom job", not spy.atom_jobs(), str(spy.atom_jobs()))
    check("no relation step, nothing re-parsed", spy.steps("ont.ak.relations") == 0
          and _num(rel, "reparsed") == 0, rel)
    check("…in seconds (%.1fs)" % t_same, t_same < 15)

    print("\n  ── (a) a comment-only edit ──")
    f1 = os.path.join(ont, "p_one", "f1.ak")
    with open(f1, "a", encoding="utf-8") as fh:
        fh.write("# a new header line, as a generator's path change adds one\n\n")
    t_a = run("comment")
    rel = _line(log, "[onto] relations")
    check("(a) no atom job", not spy.atom_jobs(), str(spy.atom_jobs()))
    check("(a) no relation step and nothing re-parsed", spy.steps("ont.ak.relations") == 0
          and _num(rel, "reparsed") == 0, rel)
    check("(a) both gates open, in seconds (%.1fs)" % t_a,
          t_a < 15 and _sched.gate_open(k, "ontology.loaded")
          and _sched.gate_open(k, "ontology.normalized"))

    print("\n  ── (c) a fresh extraction of the same files (every mtime new) ──")
    time.sleep(1.1)
    for d, _s, names in os.walk(ont):
        for n in names:
            p = os.path.join(d, n)
            data = open(p, "rb").read()
            os.remove(p)
            open(p, "wb").write(data)          # a new inode, a new mtime, the same bytes
    t_c = run("extract")
    rel = _line(log, "[onto] relations")
    check("(c) nothing re-parsed (%s)" % rel.split(" t=")[0], _num(rel, "reparsed") == 0, rel)
    check("(c) no atom job, no relation step",
          not spy.atom_jobs() and spy.steps("ont.ak.relations") == 0, str(spy.jobs))

    print("\n  ── (b) one def edited ──")
    with open(f1, "r", encoding="utf-8") as fh:
        body = fh.read()
    with open(f1, "w", encoding="utf-8") as fh:
        fh.write(body.replace('"Beta — a test dish"', '"Beta — a test dish, revised"'))
    t_b = run("def-edit")
    rel = _line(log, "[onto] relations")
    check("(b) exactly ONE atom job, for that file", spy.atom_jobs() == ["ont.ak.p_one:f1.ak"],
          str(spy.atom_jobs()))
    check("(b) only that file's relations re-parsed", _num(rel, "reparsed") == 1, rel)
    check("(b) no canon pass and no canon job — the loader writes what the pack says (§3)",
          not _line(log, "[onto] canon") and spy.steps("ont.ak.canon") == 0, str(spy.jobs))

    print("\n  ── (d) the reconcile of the largest pack, bounded ──")
    from lib.akasha.ontology_reconcile import OntologyReconciler
    admin = k.manager.get_session("admin")
    tracemalloc.start()
    keys = L.pack_def_key_set(k, admin, "p_big")
    OntologyReconciler(admin.nucleus).reconcile("p_big", keys, dry_run=True)
    _cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    check("(d) the reconcile of a %d-def pack peaks under %d MB of Python allocation (%.1f MB)"
          % (BIG_DEFS, RECONCILE_BOUND_MB, peak / 1e6), peak / 1e6 < RECONCILE_BOUND_MB)
    rec = [l for l in log.lines if l.startswith("[onto] reconcile")]
    check("(d) the reconcile phase line carries Δrss", any("Δrss=" in l for l in rec),
          str(rec[-1:]))

    print("\n  ── every phase says what it did, with t= and Δrss= ──")
    for ph in ("[onto] atoms", "[onto] relations", "[onto] reconcile"):
        ln = _line(log, ph)
        check("`%s …` carries t= and Δrss=" % ph, "t=" in ln and "Δrss=" in ln, ln or "absent")

    shutil.rmtree(root, ignore_errors=True)
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — one content key per file: a comment or a fresh extraction re-parses "
          "nothing, a def edit re-loads that file only, the two gates open, reconcile is bounded, and "
          "every phase names its time and its memory.")
    sys.exit(0)


if __name__ == "__main__":
    main()
