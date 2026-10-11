#!/usr/bin/env python3
"""
Restricted URL prefixes are DECLARED by a package; the platform names no account and no path.

Until the purge order (3 October §2) the portal kept `/labo/concept` to one hard-coded client id, the
launcher created that client at boot with a baked default passphrase, and four Concept Models asked a
module named after that account whether a bench was "his" before answering a guest. Now:

  §1  a manifest's `restricted` map ({"/prefix": ["client", …]}) is aggregated by
      `manifest.declared_restricted()`; several packages' lists for one prefix are unioned; a key that
      is not a "/"-path or a value that is not a list is ignored.
  §2  the portal's decision is `restricted_rule(path, rules)` (the LONGEST declared prefix the path
      falls under) and `restricted_allows(client, role, clients)` (a declared client, or an admin).
  §3  nothing declared → nothing gated.
  §4  the portal, the launcher and the platform Concept Models name no account: no `radu`, no
      `/labo/concept`, no `akasha_labo` cookie, no `_radu_gate` import.

Run:  python test/restricted_prefix_eval.py     (exit 0 = all pass)
"""
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.api import manifest as M
    from api.portals.asgi import restricted_rule, restricted_allows

    # §1 — aggregation over a tree of manifests (a scratch root; the real cache is left alone)
    root = tempfile.mkdtemp(prefix="akasha_restr_")
    la = os.path.join(root, "lib", "akasha")
    for pkg, body in (("concepts", {"package": "concepts", "restricted": {"/a/": ["c1"], "bad": ["x"]}}),
                      ("workbench", {"package": "workbench", "restricted": {"/a/": ["c2", "c1"],
                                                                            "/b/": "notalist"}})):
        os.makedirs(os.path.join(la, pkg), exist_ok=True)
        with open(os.path.join(la, pkg, "MANIFEST.json"), "w", encoding="utf-8") as f:
            json.dump(body, f)
    saved_root, saved = M._root_dir, dict(M._DECLARED)
    saved_app = os.environ.get("AKASHA_APP_DIR")
    try:
        M._root_dir = lambda: root
        os.environ["AKASHA_APP_DIR"] = os.path.join(root, "app")    # the scratch tree's (empty) root
        M._DECLARED.clear()
        got = M.declared_restricted()
    finally:
        if saved_app is None:
            os.environ.pop("AKASHA_APP_DIR", None)
        else:
            os.environ["AKASHA_APP_DIR"] = saved_app
        M._root_dir = saved_root
        M._DECLARED.clear()
        M._DECLARED.update(saved)
    check("§1 two packages' lists for one prefix are unioned; a non-path key and a non-list are ignored",
          got == {"/a/": ["c1", "c2"]}, str(got))

    # §2 — the decision
    rules = {"/lab/": ["alice"], "/lab/inner/": ["bob"]}
    check("§2 the longest declared prefix wins",
          restricted_rule("/lab/inner/x.json", rules) == ("/lab/inner/", ["bob"])
          and restricted_rule("/lab/y", rules) == ("/lab/", ["alice"]))
    check("§2 a path under no prefix is not gated", restricted_rule("/public/z", rules) is None)
    check("§2 a declared client passes, another client does not, an admin always does",
          restricted_allows("bob", "user", ["bob"]) and not restricted_allows("eve", "user", ["bob"])
          and restricted_allows("eve", "admin", ["bob"]))

    # §3 — nothing declared
    check("§3 nothing declared → nothing gated", restricted_rule("/anything", {}) is None)

    # §4 — no account named by the platform
    plat = [os.path.join(ROOT, "akasha.py"), os.path.join(ROOT, "api", "portals", "asgi.py"),
            os.path.join(ROOT, "api", "portals", "cell_ipc.py")]
    man = json.load(open(os.path.join(ROOT, "lib", "akasha", "concepts", "MANIFEST.json"), encoding="utf-8"))
    for mod in man.get("platform_modules") or []:
        if mod != "_radu_gate":                      # the file itself goes once the application drops it
            p = os.path.join(ROOT, "lib", "akasha", "concepts", mod + ".py")
            if os.path.exists(p):
                plat.append(p)
    for pkg in ("workbench", "source", "ontology", "api"):
        d = os.path.join(ROOT, "lib", "akasha", pkg)
        plat += [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".py")]
    pat = re.compile(r"\bradu\b|/labo/concept|akasha_labo|_radu_gate", re.I)
    hits = []
    for p in plat:
        for i, ln in enumerate(open(p, encoding="utf-8"), 1):
            if pat.search(ln) and "deleted (§2)" not in ln:
                hits.append("%s:%d" % (os.path.relpath(p, ROOT), i))
    check("§4 the portal, the launcher and the platform modules name no account, path or cookie of one",
          not hits, ", ".join(hits[:8]))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("RESULT: PASS — restricted prefixes are what the packages declare (longest prefix, declared "
          "clients or an admin); nothing declared gates nothing; the platform names no account.")
    sys.exit(0)


if __name__ == "__main__":
    main()
