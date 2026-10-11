#!/usr/bin/env python3
"""
A read during the ontology load says the ontology is still loading (seeds 13 findings F1).

`dive`/`r` on a focus that is not loaded yet answered `Focal point dissolved or locked behind scope
boundaries` — a verdict the cell could not yet give. While a load is in flight (the loader's own
in-flight record), on a fixture project (no application):

  1. `dive <not yet loaded>` and `r <not yet loaded>` say the ontology is still loading and name
     `onto.status`;
  2. an empty `s.ls <set>` and `onto.dump sets <set>` carry the same note;
  3. once the load is over, the answers are the ordinary ones again (no note, the old words);
  4. after the load the atom resolves — the message was about timing, not about the atom.

Run:  python test/load_time_focus_eval.py     (exit 0 = all pass)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "test"))
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    print("=" * 78)
    print("Reads during the ontology load")
    print("=" * 78)
    from _fixtures import pack_cell
    from lib.akasha.ontology import loader as L
    k, cli, _root = pack_cell({"a.ak": 'def "fx:late" "Arrives with the pack"\n'
                                       'set.add name="fx:lateset" id="fx:late"\n'}, load=False)

    print("\n  ── 1–2. while the load is in flight ──")
    L.publish_in_flight(k, first=True, packs=["p_fx"])
    for line in ("dive fx:late", "r fx:late"):
        e = str(cli(line).get("error") or "")
        check("`%s` says the ontology is still loading and names onto.status" % line,
              "still loading" in e and "onto.status" in e and "dissolved" not in e, e)
    for line in ("s.ls fx:lateset", "onto.dump sets fx:lateset"):
        n = str(cli(line).get("note") or "")
        check("an empty `%s` carries the note" % line, "onto.status" in n, n)
    L.publish_in_flight(k, clear=True)

    print("\n  ── 3. with no load in flight ──")
    e = str(cli("dive fx:late").get("error") or "")
    check("`dive` answers in its ordinary words", "dissolved" in e and "still loading" not in e, e)
    e = str(cli("r fx:late").get("error") or "")
    check("`r` answers in its ordinary words", "out of scope" in e and "still loading" not in e, e)
    check("an empty `s.ls` carries no note", "note" not in cli("s.ls fx:lateset"))

    print("\n  ── 4. after the load ──")
    L.boot_load_ontology(k)
    r = cli("r fx:late")
    check("the atom resolves", "error" not in r and r.get("key"), str(r)[:120])
    check("…and its set counts it", (cli("s.ls fx:lateset").get("page") or {}).get("total") == 1)

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — during the load a missing focus or an empty set says the ontology is still "
          "loading and points at onto.status; after it, the ordinary answers and the atom.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
