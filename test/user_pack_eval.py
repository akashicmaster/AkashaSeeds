#!/usr/bin/env python3
"""
A pack the cell operator drops in `ontology/user/` loads (seeds 13 findings P2).

`ontology/user/` survives updates, but the loader read only each root's REGISTRY.json, so a pack
there was never discovered — while the data-format refusal and the specification told the operator
to put one there. A directory under `ontology/user/` holding a `PACK.json` is now a pack, with no
REGISTRY.json edit. On a fixture project (no application), with the REAL loader:

  1. `ontology/user/mine/` (PACK.json + .ak) loads on the next boot and its atom resolves with `r`;
     its set counts its member;
  2. it is listed by `onto.pack.list`;
  3. a directory with no PACK.json is not a pack (nothing of it loads);
  4. a user pack whose PACK.json says `"autoload": false` waits for `onto.pack.enable`, then loads
     (on a cell without `load_all` — a `load_all` tier loads every pack, as it does registered ones);
  5. a user pack named like a registered one does not shadow it (the registered pack wins).

Run:  python test/user_pack_eval.py     (exit 0 = all pass)
"""
import json
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


def _pack(root, name, ak, meta=None):
    d = os.path.join(root, "ontology", "user", name)
    os.makedirs(d, exist_ok=True)
    if meta is not None:
        with open(os.path.join(d, "PACK.json"), "w") as fh:
            json.dump(meta, fh)
    with open(os.path.join(d, "a.ak"), "w", encoding="utf-8") as fh:
        fh.write(ak)


def main():
    print("=" * 78)
    print("ontology/user/ — the operator's own packs")
    print("=" * 78)
    from _fixtures import pack_cell
    k, cli, root = pack_cell({"a.ak": 'def "fx:registered" "From the registered pack"\n'}, load=False)
    _pack(root, "mine", 'def "u:mine" "The operator\'s own atom"\nset.add name="u:mineset" id="u:mine"\n',
          {"label": "mine"})
    _pack(root, "bare", 'def "u:bare" "No PACK.json here"\n', None)
    _pack(root, "later", 'def "u:later" "Waits to be enabled"\n', {"label": "later", "autoload": False})
    _pack(root, "p_fx", 'def "u:shadow" "Would shadow the registered p_fx"\n', {"label": "p_fx"})

    with open(os.path.join(root, "config", "ontology", "packs.json"), "w") as fh:
        json.dump({"load_all": False}, fh)             # a seeds-like cell: opt-in packs wait
    from lib.akasha.ontology import loader as L
    L.boot_load_ontology(k)

    print("\n  ── 1–2. a self-describing pack ──")
    r = cli("r u:mine")
    check("ontology/user/mine/ loaded on boot and `r u:mine` resolves", "error" not in r and r.get("key"),
          str(r)[:120])
    check("…its set counts it", (cli("s.ls u:mineset").get("page") or {}).get("total") == 1)
    lst = cli("onto.pack.list")
    names = json.dumps(lst)
    check("`onto.pack.list` lists it", '"mine"' in names, names[:200])

    print("\n  ── 3. no PACK.json ──")
    check("a directory with no PACK.json is not a pack", "error" in cli("r u:bare"))

    print("\n  ── 4. autoload: false ──")
    check("`\"autoload\": false` does not load on boot", "error" in cli("r u:later"))
    e = cli("onto.pack.enable later")
    L.boot_load_ontology(k)
    r = cli("r u:later")
    check("…`onto.pack.enable later` turns it on and it loads", "error" not in r and r.get("key"),
          "%s | %s" % (str(e)[:100], str(r)[:100]))

    print("\n  ── 5. a name already registered ──")
    check("the registered pack wins; the user copy is ignored",
          "error" not in cli("r fx:registered") and "error" in cli("r u:shadow"))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a PACK.json in ontology/user/<name>/ is a pack: it loads on the next boot "
          "(or on onto.pack.enable when it says autoload false), with no REGISTRY.json edit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
