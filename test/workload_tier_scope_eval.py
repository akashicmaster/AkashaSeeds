#!/usr/bin/env python3
"""
A workload ships with what it requires — a tier that does not carry a lab's data gets no lab.

Frontend note 2026-09-26d, "needs platform" 2. The rule (`Cryptobiosis._withheld_workloads`), read
from the declaration and never from a name: a declaration ships only when the payload it would ship
in CARRIES every `source:pool:` and `model:` it `requires`. The bench's own config directory goes
with it when no shipped workload uses that bench. A `set:` requirement never withholds, because an
ontology Set can land from a pack enabled later.

Held on a FIXTURE tree built here (platform-spec v1 — the platform's tests read no application file):
a lab requiring a pool and a model, a station requiring an ontology Set, and a workload requiring
nothing, on two benches.

  1. a payload with neither the pool nor the model: the lab is withheld naming both, with its
     bench's directory; the station and the plain workload ship, and so does their bench;
  2. a payload carrying the source pack and the model: nothing is withheld;
  3. teeth: take the model file out and the lab names exactly that model; take the pack.json out
     and it names exactly that pool; a carried source DECLARATION's pool counts like a pack's;
  4. `set:` never withholds.

Run:  python test/workload_tier_scope_eval.py     (exit 0 = all pass)
"""
import json
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


def _w(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(doc if isinstance(doc, str) else json.dumps(doc))
    return rel


def main():
    print("=" * 78)
    print("A workload ships with what it requires (fixture tree)")
    print("=" * 78)
    from reproductor.engine import Cryptobiosis as C
    from lib.akasha.api import reserved as R
    t = tempfile.mkdtemp(prefix="tier_scope_")
    wl = R.tree_path("workloads")

    def decl(slug, bench, requires):
        return {"bench": "wb:" + bench, "workflow": slug, "society": "g/" + slug, "requires": requires}
    lab = _w(t, wl + "/lab.json", decl("lab", "fx_lab", ["source:pool:fx:v1", "model:fxm", "set:fx_set"]))
    station = _w(t, wl + "/station.json", decl("station", "fx_studio", ["set:fx_words"]))
    plain = _w(t, wl + "/plain.json", decl("plain", "fx_studio", []))
    lab_tpl = _w(t, R.tree_path("templates", "fx_lab") + "/lab.ak", "w x\n")
    st_tpl = _w(t, R.tree_path("templates", "fx_studio") + "/station.ak", "w y\n")
    pack = _w(t, R.tree_path("assets") + "/fxpack/pack.json", {"pool": "source:pool:fx:v1"})
    srcd = _w(t, R.tree_path("source") + "/fxsrc.json", {"importer": "m:f", "pool": "source:pool:fx:v1"})
    model_json = _w(t, "assets/models/model.json", {"models": [{"name": "fxm", "file": "fxm.tflite"}]})
    model_bin = _w(t, "assets/models/fxm.tflite", "bin")
    lab_dir = os.path.dirname(R.tree_path("templates", "fx_lab")) + "/"
    studio_dir = os.path.dirname(R.tree_path("templates", "fx_studio")) + "/"
    base = {lab, station, plain, lab_tpl, st_tpl}

    print("\n  ── 1. neither the pool nor the model ──")
    w, dirs = C._withheld_workloads(t, base)
    check("the lab is withheld", lab in w, str(sorted(w)))
    check("…naming every pool and model it requires (never its Set)",
          sorted(w.get(lab) or []) == ["model:fxm", "source:pool:fx:v1"], str(w.get(lab)))
    check("…and its bench's directory goes with it", lab_dir in dirs, str(sorted(dirs)))
    check("the station and the plain workload ship, and their bench's directory too",
          station not in w and plain not in w and studio_dir not in dirs, "%s %s" % (w, dirs))

    print("\n  ── 2. pack and model carried ──")
    full = base | {pack, model_json, model_bin}
    w2, dirs2 = C._withheld_workloads(t, full)
    check("nothing is withheld", not w2 and not dirs2, "%s %s" % (w2, dirs2))

    print("\n  ── 3. teeth ──")
    w3, _ = C._withheld_workloads(t, full - {model_bin})
    check("the model file out → the lab names exactly `model:fxm`", w3.get(lab) == ["model:fxm"],
          str(w3.get(lab)))
    w4, _ = C._withheld_workloads(t, full - {pack})
    check("the pack.json out → the lab names exactly its pool", w4.get(lab) == ["source:pool:fx:v1"],
          str(w4.get(lab)))
    w5, _ = C._withheld_workloads(t, (full - {pack}) | {srcd})
    check("a carried source declaration's pool satisfies the requirement like a pack's", not w5,
          str(w5))

    print("\n  ── 4. `set:` never withholds ──")
    check("the station requires only an ontology Set and is never withheld",
          station not in w and station not in w3 and station not in w4)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — a declaration ships only with the pools and models it requires; its bench "
          "directory goes with it; a Set never withholds.")
    sys.exit(0)


if __name__ == "__main__":
    main()
