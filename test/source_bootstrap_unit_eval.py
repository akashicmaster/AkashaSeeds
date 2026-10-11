#!/usr/bin/env python3
"""
The managed unit around a declared import, written ONCE (step 2 §1, frontend note §1.1).

Four datasets used to be four near-identical bodies in `lib/akasha/source/bootstrap.py`, ~250 lines
each. What differed between them was four things — a corpus directory, a pool, a labo and a reset
rule — and those are declared in `config/source/<id>.json` now. Everything else was the same code
written four times: a run-once sentinel, a supervised unit, a hard cap, a serve-first gate, a resume
cursor. That is what stays platform, and this eval is about THAT, not about any dataset.

The frontend's `declared_source_import_eval` drives real corpora through real importers. This one
drives a SYNTHETIC declaration through the unit, so every branch the unit owns is reachable without
a corpus on disk:

  · the unit calls what the declaration names, and nothing it knows by name;
  · `sentinel: True` stops the next boot; `no_data` / `degraded` / `failed` do not;
  · the sentinel is keyed on the declared `reset_key`, so a CHANGED bundle re-imports and an
    unchanged one returns before the importer is called at all (memory discipline R4);
  · an importer that raises is one skipped import with a reason id, not a broken boot;
  · the cap and the shutdown check are raised THROUGH `ctl.say`, which is why the contract says an
    importer must let them propagate;
  · the cursor survives the unit that wrote it, and is cleared when the import completes.

Run:  python test/source_bootstrap_unit_eval.py     (exit 0 = all pass)
"""
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)

from lib.akasha.source import bootstrap as B                          # noqa: E402

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Kernel:
    """The two things the unit asks of the heart: a data dir and a supervised phase unit."""

    def __init__(self, base):
        self.base_dir = base
        self.units = []

    def _bg_phase_unit(self, name):
        rec = {"name": name, "phases": []}
        self.units.append(rec)

        def update(status, detail="", **kw):
            rec["phases"].append((status, detail))

        def close():
            rec["closed"] = True
        return update, close


# The importer under test is installed on THIS module and named by the declaration, so the unit
# resolves it exactly as it resolves a user script's — through `module:function`, late-bound.
_CALLS = []
_REPORT = {"status": "complete", "detail": "ok", "sentinel": True}


def fake_importer(kernel, decl, ctl=None):
    _CALLS.append(dict(decl))
    if callable(_REPORT):
        return _REPORT(kernel, decl, ctl)
    return dict(_REPORT)


def _decl(tmp, **kw):
    d = {"id": "eval_corpus", "importer": "%s:fake_importer" % __name__,
         "corpus": os.path.relpath(tmp, ROOT), "reset_key": []}
    d.update(kw)
    return d


def main():
    global _REPORT
    print("=" * 78)
    print("One managed unit, any declared corpus")
    print("=" * 78)

    base = tempfile.mkdtemp(prefix="akasha_srcunit_")
    corpus = tempfile.mkdtemp(prefix="akasha_srccorpus_")
    bundle = os.path.join(corpus, "rows.jsonl")
    with open(bundle, "w", encoding="utf-8") as fh:
        fh.write('{"a":1}\n')
    key = [os.path.relpath(bundle, ROOT)]

    # ── the unit calls what the declaration names ────────────────────────────────────────────────
    k = _Kernel(base)
    d = _decl(corpus, reset_key=key)
    _CALLS[:] = []
    rep = B.run_declared_import(k, d)
    check("the unit runs the importer the declaration names", len(_CALLS) == 1 and rep.get("status") == "complete")
    check("…inside a supervised unit named for the declaration, and closes it",
          k.units and k.units[0]["name"] == "svc:source-bootstrap:eval_corpus"
          and k.units[0].get("closed"), str(k.units and k.units[0]["name"]))
    check("…and the platform learned nothing about the corpus but its id",
          set(_CALLS[0]) >= {"id", "importer"} and "eval_corpus" not in open(
              "lib/akasha/source/bootstrap.py", encoding="utf-8").read())

    # ── sentinel: True stops the next boot, before anything is opened ────────────────────────────
    _CALLS[:] = []
    rep2 = B.run_declared_import(_Kernel(base), d)
    check("a completed import is not run again", not _CALLS and rep2.get("sentinel") is True,
          "%s / calls=%d" % (rep2.get("status"), len(_CALLS)))
    check("…and the short-circuit says so without pretending it did work",
          rep2.get("opened") is False and "sentinel" in str(rep2.get("detail")), str(rep2.get("detail")))

    # ── a CHANGED bundle re-imports ──────────────────────────────────────────────────────────────
    with open(bundle, "a", encoding="utf-8") as fh:
        fh.write('{"a":2}\n')
    _CALLS[:] = []
    B.run_declared_import(_Kernel(base), d)
    check("a changed bundle re-imports — the sentinel is keyed on the declared reset_key",
          len(_CALLS) == 1)
    check("…and a reset_key naming a file that is gone hashes differently",
          B.reset_key_digest(d) != B.reset_key_digest(_decl(corpus, reset_key=key + ["nope/gone.jsonl"])))

    # ── the three statuses that must NOT latch ───────────────────────────────────────────────────
    for status in ("no_data", "degraded", "failed"):
        base2 = tempfile.mkdtemp(prefix="akasha_srcunit_")
        _REPORT = {"status": status, "detail": status, "sentinel": False}
        _CALLS[:] = []
        B.run_declared_import(_Kernel(base2), d)
        n_first = len(_CALLS)
        B.run_declared_import(_Kernel(base2), d)
        check("a `%s` run is retried on the next boot, never recorded as finished" % status,
              n_first == 1 and len(_CALLS) == 2, "calls=%d" % len(_CALLS))
    _REPORT = {"status": "complete", "detail": "ok", "sentinel": True}

    # ── an importer that raises is ONE skipped import, with a reason id ──────────────────────────
    base3 = tempfile.mkdtemp(prefix="akasha_srcunit_")

    def _boom(kernel, decl, ctl=None):
        raise RuntimeError("the corpus host is down")
    _REPORT = _boom
    k3 = _Kernel(base3)
    rep3 = B.run_declared_import(k3, d)
    _REPORT = {"status": "complete", "detail": "ok", "sentinel": True}
    check("an importer that raises returns failed rather than breaking the boot",
          rep3.get("status") == "failed" and "down" in str(rep3.get("detail")))
    check("…the unit is still closed, and the reason is a declared id",
          k3.units[0].get("closed") and B.SKIP_IMPORT_FAILED in B.SKIP_REASONS)
    check("…and nothing was latched", not os.path.exists(B._sentinel_path(k3, d)))

    # ── a declaration naming something that is not there fails at the declaration ────────────────
    try:
        B.declared_importer({"importer": "no.such.module:nope"})
        ok = False
    except Exception as exc:
        ok = "no.such.module" in str(exc) or "nope" in str(exc) or isinstance(exc, ImportError)
    check("a declaration naming a missing entry fails loudly, naming it", ok)
    try:
        B.declared_importer({"importer": "bare_name"})
        ok2 = False
    except ValueError:
        ok2 = True
    check("…and one that is not `module:function` is refused as malformed", ok2)

    # ── the cap and the shutdown check are raised THROUGH ctl.say ────────────────────────────────
    ctl = B._UnitCtl(d, lambda *a, **kw: None, os.path.join(base, "p"), cap_s=1, t0=time.time() - 5)
    try:
        ctl.say("a phase")
        capped = False
    except TimeoutError:
        capped = True
    check("`ctl.say` raises once the run has outlived its cap — the importer must let it through",
          capped)

    # ── the cursor survives the unit that wrote it, and the sentinel clears it ───────────────────
    ppath = B._progress_path(_Kernel(base), d)
    c1 = B._UnitCtl(d, lambda *a, **kw: None, ppath, cap_s=0, t0=time.time())
    check("a fresh cursor reads 0", c1.progress() == 0)
    c1.advance(500)
    c2 = B._UnitCtl(d, lambda *a, **kw: None, ppath, cap_s=0, t0=time.time())
    check("…and a new unit reads back what the last one wrote", c2.progress() == 500)
    base4 = tempfile.mkdtemp(prefix="akasha_srcunit_")
    k4 = _Kernel(base4)
    B._UnitCtl(d, lambda *a, **kw: None, B._progress_path(k4, d), 0, time.time()).advance(7)
    B.run_declared_import(k4, d)
    check("a completed import clears the cursor — it has nothing left to resume",
          not os.path.exists(B._progress_path(k4, d)))

    # ── a declaration switches ITSELF off; no environment switch does (the purge order §4.5) ─────
    check("a declaration can switch itself off", B._bootstrap_skipped({"id": "x", "enabled": False}))
    check("…and an enabled declaration is not skipped", not B._bootstrap_skipped(d))

    # ── the real declarations still resolve through it ───────────────────────────────────────────
    real = B.source_declarations(None)
    check("every real declaration carries an id and an importer (%d on this tree)" % len(real),
          all(d0.get("id") and ":" in str(d0.get("importer")) for d0 in real),
          ", ".join(str(d0.get("id")) for d0 in real))
    bad = []
    for d0 in real:
        try:
            B.declared_importer(d0)
        except Exception as exc:
            bad.append("%s: %s" % (d0.get("id"), exc))
    check("…and every one of them resolves to a callable", not bad, "; ".join(bad))

    # ── the schedule SAYS what it found, so "no corpus" and "corpus dropped in packaging" differ ──
    # Four seeds shipped with no `config/source/*.json` at all and imported nothing, and nothing in
    # any log said so: a cell that carries no corpus and a cell whose declarations were lost look
    # identical from inside this schedule. `found=` is the tree, `runnable=` what survives the skip
    # switches — `found=0` on a tier meant to carry a corpus is a packaging defect, stated at boot.
    import logging as _lg
    _seen = []

    class _Grab(_lg.Handler):
        def emit(self, r):
            _seen.append(r.getMessage())

    _log = _lg.getLogger("Akasha.Kernel")
    _h = _Grab(); _h.setLevel(_lg.INFO); _log.addHandler(_h); _log.setLevel(_lg.INFO)
    _real_decls = B.source_declarations
    try:
        B.source_declarations = lambda _k=None: [dict(_decl(corpus), enabled=False)]
        B.schedule_source_bootstrap(_Kernel(tempfile.mkdtemp(prefix="akasha_srcsched_")))
        line = next((m for m in _seen if m.startswith("[source.bootstrap] declarations ")), "")
        check("the schedule logs what it found and what is runnable, every boot",
              "found=1" in line and "runnable=0" in line, line or "(no line)")
        _seen[:] = []
        B.source_declarations = lambda _k=None: []
        B.schedule_source_bootstrap(_Kernel(tempfile.mkdtemp(prefix="akasha_srcsched_")))
        line0 = next((m for m in _seen if m.startswith("[source.bootstrap] declarations ")), "")
        check("…and a cell with NO declaration says found=0 rather than saying nothing",
              "found=0" in line0 and "runnable=0" in line0, line0 or "(no line)")
    finally:
        B.source_declarations = _real_decls
        _log.removeHandler(_h)

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — one unit imports any declared corpus: run-once on the declared bundle, "
          "supervised, capped, resumable, and it never latches a run that did not earn it.")
    sys.exit(0)


if __name__ == "__main__":
    main()
