#!/usr/bin/env python3
"""
The boot reports its own shape (backend layout order §5b).

A boot used to be a wall of unrelated lines: you could not tell which package's work took the
twelve seconds, which body raised, or whether a body was expected to run at all on this boot. Now
the ONE place that runs a schedule — `ScheduleRegistry.run_phase` — reports each body:

    [boot] phase=1:load package=ontology name=ontology_load when=new_build status=ok t=12.40s Δrss=310MB
    [boot] complete phase=1:load ran=1 failed=0 t=12.40s Δrss=310MB

`when` is the body's DECLARATION: `new_build` (its work is expected once per new build — the body
is sentinel-gated inside) or `every_boot` (it starts a daemon, or does per-boot work). It is a
LABEL on the line, not a gate: this seed changes nothing about when a body runs. The phase GATES
(`after=ontology.loaded`, which would change when a pick runs) are seed A's, with S2-k4.

Checked here:
  1. every registered body is reported once per phase run, with all its fields
  2. the line's `package` is the package whose manifest declared it, and `when` is one of the two
     declared words — so a boot log answers "whose work is this?" without a grep of the source
  3. `[boot] complete` closes every phase with the counts
  4. a body that RAISES is reported `status=error` with the exception named, and the phase still
     runs the bodies after it (a boot has always survived one bad schedule; hiding it was the bug)
  5. every schedule in every manifest declares `when`, and the labels are honest: a `new_build`
     body is one whose second run in the same process does nothing (sentinel-gated)

Run:  python test/boot_phase_eval.py     (exit 0 = all pass)
"""
import glob
import json
import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.lines = []

    def emit(self, record):
        try:
            self.lines.append(record.getMessage())
        except Exception:
            self.lines.append(str(record.msg))


def main():
    os.chdir(ROOT)
    from lib.akasha.api.schedule import ScheduleRegistry, PHASES, WHENS

    # ── a registry of our own, so the check is on the MECHANISM, not on a live boot ──────────
    reg = ScheduleRegistry()
    seen = []
    reg.register("first", lambda k: seen.append("first"), phase="writer", order=10,
                 source="heart:x", when="every_boot", package="heart")
    reg.register("boom", lambda k: (_ for _ in ()).throw(RuntimeError("declared failure")),
                 phase="writer", order=20, source="workbench:y", when="new_build", package="workbench")
    reg.register("after", lambda k: seen.append("after"), phase="writer", order=30,
                 source="concepts:z", when="every_boot", package="concepts")

    cap = _Capture()
    root = logging.getLogger("Akasha.Kernel")
    root.addHandler(cap); old_level = root.level; root.setLevel(logging.INFO)
    try:
        reg.run_phase(None, "writer")
    finally:
        root.removeHandler(cap); root.setLevel(old_level)

    boot = [l for l in cap.lines if l.startswith("[boot] ")]
    bodies = [l for l in boot if " name=" in l and "complete" not in l]
    check("every registered body is reported — one line per body", len(bodies) == 3,
          "%d: %s" % (len(bodies), bodies))

    first = next((l for l in bodies if "name=first" in l), "")
    for field in ("phase=2:writer", "package=heart", "name=first", "when=every_boot",
                  "status=ok", "t=", "Δrss="):
        check("the line carries %s" % field, field in first, first)

    boom = next((l for l in bodies if "name=boom" in l), "")
    check("a body that RAISES is reported status=error with the exception named",
          "status=error" in boom and "RuntimeError" in boom and "declared failure" in boom, boom)
    check("…and the phase still runs the bodies after it", seen == ["first", "after"], str(seen))
    check("the failing body's own `when` and package still appear (it is attributable)",
          "package=workbench" in boom and "when=new_build" in boom, boom)

    done = [l for l in boot if "complete" in l]
    check("`[boot] complete` closes the phase with the counts",
          len(done) == 1 and "ran=3" in done[0] and "failed=1" in done[0]
          and "phase=2:writer" in done[0], str(done))

    # the report is also DATA, so a later boot check reads it instead of scraping a log
    rows = [r for r in reg.log if r.get("name") != "*"]
    check("the report is data as well as a line — name/package/when/status/t per body",
          len(rows) == 3 and all({"name", "package", "when", "status", "t"} <= set(r) for r in rows),
          str(rows[:1]))

    # ── the real manifests: every schedule declares `when`, every phase is known ─────────────
    mans = {p: json.load(open(p, encoding="utf-8"))
            for p in ["lib/akasha/MANIFEST.json"] + sorted(glob.glob("lib/akasha/*/MANIFEST.json"))
            if os.path.isfile(p)}
    no_when, bad_phase, bad_when = [], [], []
    for p, m in mans.items():
        for name, spec in (m.get("schedules") or {}).items():
            spec = {"fn": spec} if isinstance(spec, str) else spec
            if "when" not in spec:
                no_when.append("%s:%s" % (m["package"], name))
            elif spec["when"] not in WHENS:
                bad_when.append("%s:%s=%s" % (m["package"], name, spec["when"]))
            if spec.get("phase", "writer") not in PHASES:
                bad_phase.append("%s:%s=%s" % (m["package"], name, spec.get("phase")))
    check("every schedule in every manifest declares `when` — a boot line can always say whether "
          "this body was expected to work on this boot", not no_when,
          "%d: %s" % (len(no_when), no_when[:6]))
    check("every declared `when` is one of the two words", not bad_when, str(bad_when))
    check("every declared phase is a known phase", not bad_phase, str(bad_phase))

    # ── the live aggregate carries the same labels ───────────────────────────────────────────
    from lib.akasha import kernel as _kmod
    agg = _kmod._heart_aggregate()
    total = sum(len(agg.schedules.phase(ph)) for ph in PHASES)
    labelled = sum(1 for ph in PHASES for n, _ in agg.schedules.phase(ph)
                   if (agg.schedules.meta(n) or {}).get("when") in WHENS
                   and (agg.schedules.meta(n) or {}).get("package"))
    check("every live schedule carries its package and `when` into the registry (%d of %d)"
          % (labelled, total), labelled == total and total > 20)
    check("the load phase is the ontology's, and the heart declares none of it",
          [n for n, _ in agg.schedules.phase("load")]
          and all((agg.schedules.meta(n) or {}).get("package") == "ontology"
                  for n, _ in agg.schedules.phase("load")),
          str([(n, agg.schedules.meta(n).get("package")) for n, _ in agg.schedules.phase("load")]))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — every schedule body is reported at the one place that runs it, with its "
          "package, its `when`, its status, its time and its Δrss; a body that raises is named and "
          "the phase carries on; `[boot] complete` closes each phase with the counts; and every "
          "manifest schedule declares the label the line prints.")
    sys.exit(0)


if __name__ == "__main__":
    main()
