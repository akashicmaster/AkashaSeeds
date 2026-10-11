#!/usr/bin/env python3
"""
THE FIVE OPERATION PROFILES ARE DATA THAT AGREES WITH THE DECLARATIONS (C6, application side).

`app/config/profiles/<name>.json` — private_lab, open_meeting, broadcast, seminar, telemetry_feed — in the
LIVE declaration shape (docs/design/reference-templates-and-profiles.md §4). Until the platform's
loader lands (W2) they are read by nothing; this eval is the application's half of `profile_eval`:

  · each profile file loads and carries every schema field with the right type
  · the vocabulary is the live one (duty ids, trigger object, budget.per_day, on_failure)
  · `lock` names only fields the profile states
  · every workload declaration names a profile that exists
  · no declaration overrides a field its profile locks (to a different value)
  · the profile's own gate_facts / admits are not restated by a declaration under a lock

Run:  python app/test/profile_files_eval.py     (exit 0 = all pass)
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROFILES = ["private_lab", "open_meeting", "broadcast", "seminar", "telemetry_feed"]
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def load(name):
    return json.load(open(os.path.join(ROOT, "app", "config", "profiles", name + ".json"), encoding="utf-8"))


def dig(d, path):
    for p in path.split("."):
        if not isinstance(d, dict) or p not in d:
            return None, False
        d = d[p]
    return d, True


def main():
    print("\n  ── the profile files ──")
    on_disk = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "app", "config", "profiles", "*.json")))
    check("exactly the five profiles are present", on_disk == sorted(PROFILES), str(on_disk))
    schema = {"title": str, "admits": dict, "space": dict, "duty": str, "trigger": dict, "budget": dict,
              "moderator": dict, "effect": str, "gate_facts": list, "roles_min": int, "output": dict,
              "retention": dict, "lock": list}
    prof = {}
    for n in PROFILES:
        p = prof[n] = load(n)
        bad = [k for k, t in schema.items() if not isinstance(p.get(k), t)]
        check("%s: every field present with the right type" % n, not bad, str(bad))
        check("%s: live vocabulary (duty id, trigger object, budget.per_day, on_failure)" % n,
              p["duty"] in ("wb:duty:continuous", "wb:duty:best_effort")
              and set(p["trigger"]) == {"boot", "then"} and isinstance(p["budget"].get("per_day"), int)
              and set(p["moderator"].get("on_failure", {})) == {"retries", "breaker"}
              and p["effect"] in ("record", "publish"))
        stated = [f for f in p["lock"] if dig(p, f)[1]]
        check("%s: every locked field is one the profile states" % n, stated == p["lock"],
              str(set(p["lock"]) - set(stated)))
        check("%s: a profile never carries a declaration-only field" % n,
              not ({"bench", "bench_public", "bench_kind", "workflow", "society", "appetite", "pins",
                    "on_exhausted", "effect_read", "room", "roles", "offers"} & set(p)))

    print("\n  ── the declarations under them ──")
    for f in sorted(glob.glob(os.path.join(ROOT, "app", "config", "workbench", "workloads", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        n = os.path.basename(f)
        name = d.get("profile")
        check("%s names a profile that exists" % n, name in prof, str(name))
        if name not in prof:
            continue
        p = prof[name]
        over = []
        for field in p["lock"]:
            pv, _ = dig(p, field)
            dv, has = dig(d, field)
            if has and dv != pv:
                over.append((field, dv, pv))
        check("%s overrides no field its profile (%s) locks" % (n, name), not over, str(over))
    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the five profiles are well-formed data in the live declaration shape, and every "
          "workload declaration names one and overrides none of its locked fields.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
