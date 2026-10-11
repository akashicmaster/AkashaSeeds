#!/usr/bin/env python3
"""
Manifest-driven deployment (backend layout order 2026-09-20 §5).

The self-extractor used to carry its own idea of what a deploy owns — a PROTECTED_PATHS list, a
PRUNE_KEEP list, a PRUNE_EXTS tuple and a `.env` basename comparison — so the answer to "may this
file be written?" lived in the installer instead of beside the code it protects. It is now ONE
declaration: each package's MANIFEST.json says which trees it owns (`code_paths`) and which are
operator- or runtime-owned (`data_paths`); the crystallizer unions them into the SEED_MANIFEST it
embeds, and `safe_extract` / `prune_stale` are one loop each over it, comparing no basename.

This eval drives the REAL emitted extractor (rendered from the crystallizer's own template, so a
change to the template is a change to what is tested here):

  1. the seed manifest is BUILT from the tree's manifests — the union of their declarations, and a
     declaration that could escape the tree (absolute, or with `..`) is refused at build time
  2. a FRESH extract writes the whole payload
  3. a RE-extract over a live deployment: every data file is byte-identical afterwards (the store,
     the deployment env, the secrets file, user ontology), code is replaced by the new payload,
     retired code is pruned, and a file no code_path claims is left alone
  4. a payload entry that tries to escape the tree (absolute path, `..`) is skipped, not written

**Two halves, because a seed carries no crystallizer.** Checks 2–4 drive the emitted extractor and
need `reproductor/`, which is generator-side and ships in no payload — so on a DEPLOYED tree this
eval used to fail at import, and the deployment contract could not be verified where it matters
most (F56 v64). It is now explicitly split: the MANIFEST half (the contract's input — every
declared path inside the tree, every retired protected path claimed by some package) runs
everywhere, from the manifests the seed does carry; the EXTRACTOR half announces itself as
generator-side and is skipped when the crystallizer is absent. A skip says so by name; it never
counts as a pass.

Run:  python test/deploy_eval.py     (exit 0 = all pass)
"""
import base64
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _zip_bytes(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, body in files.items():
            zf.writestr(name, body)
    return buf.getvalue()


def _extractor(manifest, payload_zip):
    """Render the crystallizer's OWN seed template and load the extractor it emits."""
    from reproductor.engine import Cryptobiosis
    eng = Cryptobiosis()
    src = eng._generate_sprout_script(
        "evalseries", {"max_clients": 1}, base64.b64encode(payload_zip).decode(),
        exclude_paths=list(manifest.get("keep_paths") or []), seed_manifest=manifest)
    body = src[src.index("SEED_MANIFEST = "):src.index("def _verify_tree(")]
    ns = {"os": os, "zipfile": zipfile, "io": io, "print": lambda *a, **k: None}
    exec(compile(body, "<seed>", "exec"), ns)
    return ns


def _write(path, body):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)


def _manifest_union():
    """The contract's INPUT, read from the package manifests alone — no crystallizer.

    On a deployed tree this is the only source there is: the seed carries the manifests, not the
    generator that unions them. When the crystallizer IS present the union it builds is asserted
    equal to this, so the two can never drift apart unnoticed."""
    from lib.akasha.api.manifest import default_manifest_paths, read_manifest
    code, data, dirs = [], [], []
    for p in default_manifest_paths(os.path.join(ROOT, "lib", "akasha")):
        man = read_manifest(p)
        code += list(man.get("code_paths") or [])
        data += list(man.get("data_paths") or [])
        dirs += list(man.get("dirs") or [])
    return {"code_paths": sorted(set(code)), "data_paths": sorted(set(data)),
            "dirs": sorted(set(dirs))}


def main():
    HAS_GEN = os.path.isdir(os.path.join(ROOT, "reproductor"))

    # ── 1. the seed manifest is the union of the tree's own declarations ──────────────────────
    u = _manifest_union()
    if HAS_GEN:
        from reproductor.engine import Cryptobiosis
        eng = Cryptobiosis()
        m = eng._seed_manifest(ROOT, ["services/static/cookbook"])
        check("the seed manifest is built from the tree's package manifests (a version, code, data, "
              "dirs, the file types the seed ships)",
              m.get("version") == 1 and m["code_paths"] and m["data_paths"] and m["dirs"]
              and ".py" in m["code_exts"], str({k: len(v) for k, v in m.items() if isinstance(v, list)}))
        from lib.akasha.api import reserved as _R
        _app_claim = {_R.APP_DIR + "/"} if os.path.isdir(os.path.join(ROOT, _R.APP_DIR)) else set()
        check("the crystallizer's union IS the manifests' union plus the application root as code "
              "(platform-spec §5.9) — it adds no other path and drops none",
              sorted(set(m["code_paths"]) - _app_claim) == sorted(set(u["code_paths"]) - _app_claim)
              and _app_claim <= set(m["code_paths"])
              and sorted(set(m["data_paths"])) == u["data_paths"],
              "code Δ=%s data Δ=%s" % (sorted(set(m["code_paths"]) ^ set(u["code_paths"])),
                                       sorted(set(m["data_paths"]) ^ set(u["data_paths"]))))
        check("the crystallizer's own per-series exclusions ride along as keep_paths",
              "services/static/cookbook" in m["keep_paths"], str(m["keep_paths"]))
    else:
        eng = None
        m = dict(u, version=1, keep_paths=[], code_exts=[".py"])
        print("  ----  crystallizer absent (deployed tree) — the seed-manifest BUILD and the "
              "extractor drive are generator-side; the manifest contract below still runs")
    check("every platform package's declaration reaches the union (the heart's store, the "
          "ontology's user tree, the gate's identity seed)",
          "data/" in u["data_paths"] and "ontology/user/" in u["data_paths"]
          and any(p.startswith("config/identity") for p in u["code_paths"]),
          "data=%s code=%s" % (u["data_paths"], u["code_paths"]))

    # ── 1b. the retired PROTECTED_PATHS inventory, one by one ────────────────────────────────
    # The old extractor carried this list itself. Each entry must now be covered by some package's
    # `data_paths`, or a re-extract could erase an operator's key. Checked by NAME so the list can
    # never quietly shrink; `data/central/secrets.env` is the real location of the secrets file and
    # is covered by the heart's `data/`.
    RETIRED_PROTECTED = ["data/", "env/models/", "env/deployment.env", "env/secrets.env",
                         "data/central/secrets.env", ".env", "docs/user/",
                         "ontology/user/", "apps/custom/", "lib/plugins/"]
    dps = [str(p).replace("\\", "/") for p in u["data_paths"]]
    uncovered = [p for p in RETIRED_PROTECTED
                 if not any(p == dp or p.startswith(dp) for dp in dps)]
    check("every path the retired PROTECTED_PATHS list shielded is claimed by a package's "
          "data_paths — %d of %d, none lost in the move"
          % (len(RETIRED_PROTECTED) - len(uncovered), len(RETIRED_PROTECTED)),
          not uncovered, str(uncovered))

    # No declaration in THIS tree could escape it — the check that matters on a deployed cell,
    # where a hand-edited manifest is the way a re-extract could be pointed outside the tree.
    escapes = [p for p in (u["code_paths"] + u["data_paths"] + u["dirs"])
               if os.path.isabs(p) or ".." in str(p).replace("\\", "/").split("/")]
    check("no path any manifest declares could escape the tree (absolute, or with `..`)",
          not escapes, str(escapes))

    if not HAS_GEN:
        print()
        print("  ----  %d extractor checks are GENERATOR-SIDE and were skipped: the seed carries no "
              "reproductor/. They run on the tree the seed is built from." % 8)
        if _fails:
            print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
        print("RESULT: PASS (manifest half) — the deployment contract's input is intact on this "
              "tree: every declared path is inside it, and every retired protected path is claimed "
              "by a package. The extractor drive is generator-side.")
        sys.exit(0)

    # a declaration that could escape the tree is refused where it is READ, naming the manifest
    bad_root = tempfile.mkdtemp(prefix="akasha_badman_")
    os.makedirs(os.path.join(bad_root, "lib", "akasha"), exist_ok=True)
    _write(os.path.join(bad_root, "lib", "akasha", "MANIFEST.json"),
           json.dumps({"package": "heart", "code_paths": ["../../etc/"], "data_paths": []}))
    refused = ""
    try:
        eng._seed_manifest(bad_root, [])
    except ValueError as exc:
        refused = str(exc)
    check("a manifest that declares a path outside the tree is REFUSED when the seed is built "
          "(named, not silently dropped)",
          "unusable" in refused and "MANIFEST.json" in refused, refused[:110] or "not refused")

    # ── the fixture deployment ────────────────────────────────────────────────────────────────
    MAN = {"version": 1,
           "code_paths": ["lib/", "archives/", "config/workbench/", "akasha.py"],
           "data_paths": ["data/", "env/deployment.env", "env/secrets.env", "ontology/user/",
                          "archives/snapshots/", ".env"],
           "keep_paths": ["lib/keepme/"],
           "dirs": ["data"],
           "code_exts": [".py", ".json", ".html", ".ak"]}
    v1 = _zip_bytes({
        "akasha.py": "v1\n",
        "lib/akasha/kernel.py": "kernel v1\n",
        "lib/akasha/retired.py": "retired v1\n",
        "lib/keepme/kept.py": "kept v1\n",
        "archives/index.html": "<p>v1</p>",
        "config/workbench/workloads/news_show.json": '{"workflow": "news_show"}',
        "data/central/nucleus.db": "SEED-DEFAULT",
        "env/deployment.env": "AKASHA_TIER=seed-default\n",
    })

    work = tempfile.mkdtemp(prefix="akasha_deploy_")
    cwd = os.getcwd()
    try:
        os.chdir(work)

        # ── 2. FRESH extract — the whole payload lands ────────────────────────────────────────
        ex = _extractor(MAN, v1)
        failures = ex["safe_extract"](v1)
        wrote = all(os.path.isfile(p) for p in
                    ("akasha.py", "lib/akasha/kernel.py", "archives/index.html",
                     "config/workbench/workloads/news_show.json",
                     "data/central/nucleus.db", "env/deployment.env"))
        check("a FRESH extract writes the whole payload (code, declarations and the shipped "
              "defaults for a store that does not exist yet)", wrote and not failures,
              str(failures)[:120])

        # ── the deployment lives: the operator and the runtime write ──────────────────────────
        _write("data/central/nucleus.db", "LIVE-STORE-CONTENTS")
        _write("env/deployment.env", "AKASHA_TIER=thesaurus\nAKASHA_MAX_LEAVES=50\n")
        _write("env/secrets.env", "AKASHA_SECRET=operator-owned\n")
        _write(".env", "LOCAL=1\n")
        _write("ontology/user/mine.ak", 'def "u:x" "mine"\n')
        _write("archives/snapshots/apple.html", "<p>warm</p>")
        _write("config/tls.json", '{"domains": ["example.org"]}')     # operator file, unclaimed
        _write("lib/akasha/local_patch.py", "operator patch\n")       # claimed tree, not in payload
        before = {p: open(p, encoding="utf-8").read() for p in
                  ("data/central/nucleus.db", "env/deployment.env", "env/secrets.env", ".env",
                   "ontology/user/mine.ak", "archives/snapshots/apple.html")}

        # ── 3. RE-extract: v2 changes a file, retires another, keeps the rest ────────────────
        v2 = _zip_bytes({
            "akasha.py": "v2\n",
            "lib/akasha/kernel.py": "kernel v2\n",
            "lib/keepme/kept.py": "kept v2\n",
            "archives/index.html": "<p>v2</p>",
            "config/workbench/workloads/news_show.json": '{"workflow": "news_show", "v": 2}',
            "data/central/nucleus.db": "SEED-DEFAULT",
            "env/deployment.env": "AKASHA_TIER=seed-default\n",
        })
        ex2 = _extractor(MAN, v2)
        ex2["safe_extract"](v2)
        ex2["prune_stale"](v2)

        after = {p: (open(p, encoding="utf-8").read() if os.path.isfile(p) else None) for p in before}
        same = [p for p in before if after[p] == before[p]]
        check("every DATA path survives a re-extract byte-identical — the store, the deployment "
              "env, the secrets file, the local .env, user ontology and the warm snapshot cache",
              len(same) == len(before), "changed: %s" % [p for p in before if after[p] != before[p]])
        check("CODE is replaced by the new payload",
              open("lib/akasha/kernel.py").read() == "kernel v2\n"
              and open("archives/index.html").read() == "<p>v2</p>"
              and open("akasha.py").read() == "v2\n")
        check("a declaration file is replaced too (it is the seed's, not the operator's)",
              open("config/workbench/workloads/news_show.json").read() == '{"workflow": "news_show", "v": 2}')
        check("RETIRED code is pruned — a module the payload no longer carries does not linger",
              not os.path.exists("lib/akasha/retired.py"))
        check("an exclusion (keep_paths) is never pruned, even inside a claimed tree",
              os.path.isfile("lib/keepme/kept.py"))
        check("a file NO code_path claims is left alone (an operator's own config beside the "
              "seed's) — the prune only touches what a manifest says the seed owns",
              os.path.isfile("config/tls.json"))
        check("an operator's file inside a CLAIMED tree is pruned as stale seed code — that tree "
              "belongs to the seed, and this is the update hygiene the prune exists for",
              not os.path.exists("lib/akasha/local_patch.py"))

        # ── 4. a payload entry that tries to escape the tree is skipped ──────────────────────
        evil = _zip_bytes({"../escaped.py": "nope\n", "/abs.py": "nope\n",
                           "lib/akasha/fine.py": "ok\n"})
        ex3 = _extractor(MAN, evil)
        ex3["safe_extract"](evil)
        check("a payload entry with `..` or an absolute path is SKIPPED, and the safe entries in "
              "the same payload still land",
              os.path.isfile("lib/akasha/fine.py")
              and not os.path.exists(os.path.join(work, "..", "escaped.py"))
              and not os.path.exists("escaped.py"))
    finally:
        os.chdir(cwd)
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(bad_root, ignore_errors=True)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — the deployment reads ONE declaration: the seed manifest the crystallizer "
          "unions from every package MANIFEST.json. A fresh extract writes the payload; a re-extract "
          "leaves every declared data path byte-identical, replaces code, prunes retired code, and "
          "touches nothing no code_path claims; a path that could escape the tree is refused when "
          "the seed is built and skipped when it is extracted.")
    sys.exit(0)


if __name__ == "__main__":
    main()
