#!/usr/bin/env python3
"""
The profile loader (the purge order, ruling of 4 October — P2).

A workload declaration's `profile:` names a file under the profiles root (`config/profiles/<p>.json`).
The loader applies the profile's fields as the declaration's DEFAULTS:

  1. a declaration WITHOUT `duty` takes the profile's `duty` (the order's own eval), and is then
     well-formed;
  2. a field the declaration states explicitly WINS over the profile's;
  3. a dict field merges key by key, the declaration's keys winning at every level;
  4. the profile's `_` comment keys are not copied;
  5. an unknown profile is a provisioning error BY NAME: `problems()` gives `profile`, and one
     `[bench] workload profile unknown … profile=<name>` line names it;
  6. a declaration with no `profile` is read exactly as written;
  7. on this tree, every declaration that names a profile resolves it and is well-formed.

Run:  python test/workload_profile_eval.py     (exit 0 = all pass)
"""
import json
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Grab(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, r):
        self.lines.append(r.getMessage())


BASE = {
    "bench": "wb:prof", "workflow": "prof_w", "society": "prof/main",
    "trigger": {"boot": False, "then": "every:60s"}, "effect": "record",
    "appetite": {"llm_calls_per_run": 0, "weight": 0.0}, "budget": {"per_day": 5}, "pins": {},
    "space": {"client": "prof:client", "name": "Prof"},
}
PROFILE = {"_": "a comment", "title": "A profile", "duty": "wb:duty:best_effort",
           "space": {"public": True, "open_guest": False, "name": "from-profile"},
           "budget": {"per_day": 300, "max_wall_s": 60}}


def main():
    from lib.akasha.workbench import workload as W
    real = (W.PROFILE_DIR, W.WORKLOAD_DIR)
    tmp = tempfile.mkdtemp(prefix="wlprof_")
    pdir, wdir = os.path.join(tmp, "profiles"), os.path.join(tmp, "workloads")
    os.makedirs(pdir), os.makedirs(wdir)
    with open(os.path.join(pdir, "steady.json"), "w") as fh:
        json.dump(PROFILE, fh)

    def write(name, doc):
        with open(os.path.join(wdir, name + ".json"), "w") as fh:
            json.dump(doc, fh)

    write("a_noduty", dict(BASE, profile="steady"))
    write("b_explicit", dict(BASE, profile="steady", duty="wb:duty:continuous"))
    write("c_unknown", dict(BASE, profile="no_such_profile"))
    write("d_none", dict(BASE, duty="wb:duty:continuous"))
    grab = _Grab()
    lg = logging.getLogger("Akasha.Kernel")
    lg.addHandler(grab)
    lg.setLevel(logging.INFO)
    try:
        W.PROFILE_DIR, W.WORKLOAD_DIR = pdir, wdir
        decls = {d["_file"][:-5]: d for d in W.declarations()}
    finally:
        W.PROFILE_DIR, W.WORKLOAD_DIR = real
        lg.removeHandler(grab)

    a, b, c, d = decls.get("a_noduty", {}), decls.get("b_explicit", {}), \
        decls.get("c_unknown", {}), decls.get("d_none", {})
    print("\n  ── the profile's fields are defaults ──")
    check("1. a declaration without `duty` takes the profile's duty",
          a.get("duty") == "wb:duty:best_effort", str(a.get("duty")))
    check("…and is then well-formed (no `duty` problem)", W.problems(a) == [], str(W.problems(a)))
    check("2. a field the declaration states wins (duty continuous over the profile's best_effort)",
          b.get("duty") == "wb:duty:continuous", str(b.get("duty")))
    check("3. a dict merges key by key: the profile's space.public/open_guest fill in, the "
          "declaration's space.name and space.client stay",
          a.get("space") == {"public": True, "open_guest": False, "name": "Prof",
                             "client": "prof:client"}, str(a.get("space")))
    check("…and budget.per_day is the declaration's while budget.max_wall_s comes from the profile",
          a.get("budget") == {"per_day": 5, "max_wall_s": 60}, str(a.get("budget")))
    check("4. the profile's `_` keys are not copied (its other fields are)",
          "_" not in a and a.get("title") == "A profile", str(sorted(a)))

    print("\n  ── an unknown profile is a provisioning error, by name ──")
    check("5. problems() refuses it with `profile`", "profile" in W.problems(c), str(W.problems(c)))
    named = [l for l in grab.lines if l.startswith("[bench] workload profile unknown")
             and "profile=no_such_profile" in l]
    check("…and one line names the profile and the file", len(named) == 1 and "c_unknown.json" in named[0],
          str(named))
    check("6. a declaration with no profile is read as written",
          {k: v for k, v in d.items() if k != "_file"} == dict(BASE, duty="wb:duty:continuous"),
          str(sorted(d)))

    print("\n  ── this tree ──")
    mine = [x for x in W.declarations() if x.get("profile")]
    bad = ["%s: %s" % (x["_file"], W.problems(x)) for x in mine if W.problems(x)]
    check("7. every declaration on this tree that names a profile resolves it and is well-formed "
          "(%d)" % len(mine), not bad, "; ".join(bad[:4]))

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s): %s" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a declaration's profile supplies its defaults: an unstated field (duty) is "
          "the profile's, a stated one is the declaration's, dicts merge key by key, and an unknown "
          "profile is refused by name.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
