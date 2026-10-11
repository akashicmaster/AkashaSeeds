#!/usr/bin/env python3
"""
A SHADOW LABO NEVER OUTRANKS A REGISTERED ONE — `labo.bind origin=`, `labo.of`, registered-first (10-03, decision 2).

The workbench mints a SHADOW labo for a frozen pool no lab holds (`labo: {name: "src_{pool}", when: "unbound"}`),
and asks the application which labs already hold a pool through the read point `workload.labo.of`. The
application's side, held here on a real dispatcher:

  · `labo.bind` records an `origin` (registered | shadow); the default, and every binding made before the
    parameter existed, is registered; anything else is refused
  · `labo.of pool=` lists the Labos holding the pool, REGISTERED FIRST, each with its origin — even when the
    shadow was created first (a shadow left over from an earlier run)
  · the Labos the OLD boot schedule minted (`src_<slug>`, about "Auto — text analysis of …") count as shadow
    although they carry no mark
  · a pool no labo holds answers an empty list
  · the three ops declare the workbench's extension points in the manifest
  · the Source Viewer asks `labo.of` (one read), not a labo.ls × labo.source walk

Run:  python app/test/labo_origin_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_lab_"))

    def raw(method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local") or {}

    def d(method, data):
        return raw(method, data).get("result") or {}

    raw("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})
    POOL = "source:pool:eval:p1"
    OTHER = "source:pool:eval:p2"
    for p in (POOL, OTHER):
        d("kernel.memory.define", {"name": p, "description": "pool %s" % p, "scope": "universal"})

    # the shadow is created FIRST — a leftover from an earlier run
    d("labo.new", {"name": "src_p1", "about": "Auto — text analysis of %s" % POOL})
    d("labo.bind", {"name": "src_p1", "pool": POOL, "origin": "shadow"})
    d("labo.new", {"name": "reg1", "about": "a registered lab"})
    r = d("labo.bind", {"name": "reg1", "pool": POOL})
    check("labo.bind defaults to origin=registered and says so", r.get("origin") == "registered", str(r))
    of = d("labo.of", {"pool": POOL})
    labs = [(x["labo"], x["origin"]) for x in of.get("labos", [])]
    check("labo.of lists the registered lab FIRST although the shadow was created first",
          labs == [("labo:reg1", "registered"), ("labo:src_p1", "shadow")], str(labs))

    # an unmarked binding counts as registered
    d("labo.new", {"name": "old_lab", "about": "bound before origin existed"})
    d("labo.bind", {"name": "old_lab", "pool": OTHER})
    of2 = d("labo.of", {"pool": OTHER})
    check("a binding with no mark is registered", [(x["labo"], x["origin"]) for x in of2["labos"]]
          == [("labo:old_lab", "registered")], str(of2))

    # the old boot schedule's labos are shadows although unmarked
    d("labo.new", {"name": "src_p2", "about": "Auto — text analysis of %s" % OTHER})
    d("labo.bind", {"name": "src_p2", "pool": OTHER})            # bound WITHOUT an origin, as the schedule did
    of3 = d("labo.of", {"pool": OTHER})
    check("a labo the old boot schedule minted (src_<slug>, 'Auto — text analysis of …') counts as shadow, "
          "and ranks after the registered one",
          [(x["labo"], x["origin"]) for x in of3["labos"]]
          == [("labo:old_lab", "registered"), ("labo:src_p2", "shadow")], str(of3))

    check("a pool no labo holds answers an empty list",
          d("labo.of", {"pool": "source:pool:eval:none"}).get("labos") == [])
    bad = raw("labo.bind", {"name": "reg1", "pool": OTHER, "origin": "bogus"})
    check("an unknown origin is refused", "error" in bad, str(bad)[:120])

    man = json.load(open(os.path.join(ROOT, "app", "config", "MANIFEST.json"), encoding="utf-8"))["ops"]
    check("the workbench's three extension points are implemented by labo.new / labo.bind / labo.of",
          man.get("labo.new", {}).get("implements") == "workload.labo.new"
          and man.get("labo.bind", {}).get("implements") == "workload.labo.bind"
          and man.get("labo.of", {}).get("implements") == "workload.labo.of")
    html = open(os.path.join(ROOT, "app", "archives", "labo", "source", "index.html"), encoding="utf-8").read()
    i = html.index("function findLabo")
    body = html[i:html.index("// ── G1 · BENCH view", i)]
    check("the Source Viewer resolves a pool's lab with ONE `labo.of` read (registered first), not a walk",
          "call('labo.of'" in body and "labo.ls" not in body.replace("labo.ls × labo.source", ""), body[:80])
    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a binding carries its origin, labo.of answers registered first (legacy shadows "
          "included), and the Source Viewer asks it once.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
