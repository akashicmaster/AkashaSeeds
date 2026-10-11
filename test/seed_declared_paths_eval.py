#!/usr/bin/env python3
"""
What a seed carries: the platform's declared paths, and the application root as a whole minus what
its series declaration withholds (platform-spec v1, "Series declaration").

  1. The generic declared-path pass (the platform's `code_paths` / `data_paths` no other rule packs)
     selects `config/`, never an entry under the application root (that root ships through its own
     pass), never a tree a platform rule governs (`docs/`, `ontology/`, the code directories, the
     runtime `dirs`), and never a dot-file (`.env` is a secret). Every directory under the platform's
     `config/` is claimed by a declared path, so none ships — or fails to — by omission.
  2. The application pass, on a FIXTURE application built here: a series ships every file of the
     root by its code extension, EXCEPT a group it does not select, a private path, a pack it does not
     select (and the registry lists only the packs that ship), a corpus it does not carry (the
     declaration and its bundle); a selected `whole` group and a carried corpus's bundle ship
     whatever their extension. An unknown key, an unknown group, an unknown pack and an undeclared
     corpus are refused, naming the series.
  3. `.akasha` is a code extension, so a shipped first-run capsule is replaced and pruned like code.

Run:  python test/seed_declared_paths_eval.py     (exit 0 = all pass)
"""
import glob
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


def _w(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def _fixture(series):
    """A tiny project tree whose application root declares `series`."""
    from lib.akasha.api import reserved as RES
    t = tempfile.mkdtemp(prefix="seed_fixture_")
    A = RES.APP_DIR
    _w(t, A + "/config/series.json", json.dumps({
        "default": "small",
        "groups": {"pages": {"paths": ["pages/"]}, "data": {"paths": ["assets/big/"], "whole": True}},
        "private": ["notes/private.md"],
        "series": series}))
    _w(t, A + "/concepts/model.py", "X = 1\n")
    _w(t, A + "/pages/index.html", "<p>room</p>\n")
    _w(t, A + "/assets/big/data.jsonl.gz", "binary-ish\n")
    _w(t, A + "/notes/private.md", "secret\n")
    _w(t, A + "/notes/public.md", "open\n")
    _w(t, A + "/ontology/REGISTRY.json", json.dumps({"version": "2", "packages": [
        {"name": "core", "autoload": True, "tier": "A"},
        {"name": "extra", "autoload": False, "tier": "B"},
        {"name": "deep", "autoload": False, "tier": "C"}]}))
    for pk in ("core", "extra", "deep"):
        _w(t, A + "/ontology/%s/PACK.json" % pk, "{}")
        _w(t, A + "/ontology/%s/%s.ak" % (pk, pk), 'def "%s:x" "x"\n' % pk)
    _w(t, A + "/scripts/imp.py", "def run_declared(*a):\n    pass\n")
    for cid in ("one", "two"):
        _w(t, A + "/config/source/%s.json" % cid, json.dumps({
            "importer": "%s.scripts.imp:run_declared" % A, "corpus": "%s/assets/%s" % (A, cid),
            "pool": "source:pool:%s" % cid}))
        _w(t, A + "/assets/%s/rows.jsonl" % cid, "{}\n")
    return t


def main():
    print("=" * 78)
    print("What a seed carries — declared platform paths, and the application root")
    print("=" * 78)
    from reproductor.engine import Cryptobiosis as C, GeneticBlueprint as B, SeriesError
    from lib.akasha.api import reserved as RES

    print("\n  ── 1. the generic declared-path pass ──")
    manifest = C()._seed_manifest(ROOT, [])
    bp = {"core_dirs": ["api", "lib", "remote", "env", "services", "assets", "test"],
          "core_files": ["akasha.py", "scripts/gen_lexicon.py"]}
    entries = C._generic_declared_entries(manifest, bp)
    tops = {e.split("/")[0] for e in entries}
    check("`config/` is selected (the pass's own domain)", "config" in tops, str(sorted(tops)))
    check("no entry under the application root (it ships through its own pass)",
          not any(RES.is_app_path(e) for e in entries), str([e for e in entries if RES.is_app_path(e)]))
    governed = {"docs", "ontology", "lib", "api", "test", "scripts", "data", "logs"}
    check("nothing a platform rule governs is selected (%s)" % ", ".join(sorted(governed)),
          not (tops & governed), str(sorted(tops & governed)))
    check("no dot-file is ever selected (`.env` is a declared data path — a secret)",
          not any(e.startswith(".") for e in entries))
    cfg_dirs = sorted({os.path.relpath(os.path.dirname(f), ROOT).replace(os.sep, "/") + "/"
                       for f in glob.glob(os.path.join(ROOT, "config", "*", "**", "*"), recursive=True)
                       if os.path.isfile(f)})
    orphan = [d for d in cfg_dirs if not any(d.startswith(e) or e.startswith(d) for e in entries)]
    check("every directory under the platform's config/ is claimed by a declared path",
          bool(cfg_dirs) and not orphan, str(orphan[:6]))

    print("\n  ── 2. the application pass, on a fixture application ──")
    A = RES.APP_DIR
    t = _fixture({"small": {"tier": "t", "max_leaves": 5, "packs": "*", "corpora": ["one"]},
                  "big": {"tier": "t", "max_leaves": 5, "load_all": True, "packs": "*",
                          "groups": ["pages", "data"]}})
    eng = C()
    small = B.get_config("small", t)
    packs = eng._select_packs(t, small)
    by_ext, whole = eng._app_payload(t, small, packs)
    ship = set(by_ext) | set(whole)
    check("an ordinary file ships by its extension", A + "/concepts/model.py" in by_ext)
    check("a group the series does not select is withheld (pages, data)",
          A + "/pages/index.html" not in ship and A + "/assets/big/data.jsonl.gz" not in ship)
    check("a private path never ships; its sibling does",
          A + "/notes/private.md" not in ship and A + "/notes/public.md" in ship)
    check("`*` without load_all is every pack but tier C; autoload packs always ship",
          packs == ["core", "extra"], str(packs))
    check("…an unselected pack's directory is withheld, and the registry is written, not copied",
          not any(p.startswith(A + "/ontology/deep/") for p in ship)
          and A + "/ontology/REGISTRY.json" not in ship)
    check("a carried corpus ships its declaration and its WHOLE bundle; another is withheld, both",
          A + "/config/source/one.json" in ship and A + "/assets/one/rows.jsonl" in whole
          and A + "/config/source/two.json" not in ship
          and not any(p.startswith(A + "/assets/two/") for p in ship), str(sorted(whole)))
    big = B.get_config("big", t)
    bpacks = eng._select_packs(t, big)
    b_ext, b_whole = eng._app_payload(t, big, bpacks)
    check("a selected group ships; a `whole` group ships whatever its extension; load_all takes tier C",
          A + "/pages/index.html" in b_ext and A + "/assets/big/data.jsonl.gz" in b_whole
          and "deep" in bpacks, "packs=%s" % bpacks)
    check("…and a corpus the series does not carry is withheld there too",
          A + "/config/source/one.json" not in set(b_ext) | set(b_whole))

    def refused(series, name):
        tt = _fixture(series)
        try:
            cfg = B.get_config(name, tt)
            eng._app_payload(tt, cfg, eng._select_packs(tt, cfg))
            return ""
        except SeriesError as e:
            return str(e)
    r = refused({"s": {"tier": "t", "max_leaves": 1, "colour": "red"}}, "s")
    check("an unknown series key is refused, naming the series and the key", "'colour'" in r, r)
    r = refused({"s": {"tier": "t", "max_leaves": 1, "groups": ["nope"]}}, "s")
    check("an unknown group is refused", "nope" in r, r)
    r = refused({"s": {"tier": "t", "max_leaves": 1, "packs": ["ghost"]}}, "s")
    check("a pack the registry does not list is refused", "ghost" in r, r)
    r = refused({"s": {"tier": "t", "max_leaves": 1, "corpora": ["three"]}}, "s")
    check("a corpus the application does not declare is refused", "three" in r, r)
    r = refused({"s": {"tier": "t"}}, "s")
    check("a series without max_leaves is refused", "max_leaves" in r, r)
    check("`<name>n` is the Silica twin only for a series that declares `twin`",
          B.get_config("smalln", _fixture({"small": {"tier": "t", "max_leaves": 1, "twin": True}}))
          .get("backend") == "silica" and refused({"small": {"tier": "t", "max_leaves": 1}}, "smalln"))

    print("\n  ── 3. code extensions ──")
    check("`.akasha` is a CODE extension", ".akasha" in C.SEED_CODE_EXTS)

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — the platform's declared paths ship by declaration, and the application root "
          "ships whole, minus exactly what its series declaration withholds.")
    sys.exit(0)


if __name__ == "__main__":
    main()
