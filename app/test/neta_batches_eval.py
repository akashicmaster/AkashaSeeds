#!/usr/bin/env python3
"""
A NEWS BATCH MINTS ITS OWN IDS — AN ITEM ID IS NEVER REUSED FOR A DIFFERENT TEXT (D16).

Directive 2026-10-02 §0. On 09-28 the 09-27 batch REUSED the ids 001–030 of the batch before it with
new text. The platform's reconcile then retired the new atoms (fixed on its side), and the news show
aired 18 of its 48 items. Independently of that defect, reuse breaks provenance: the air rows that
named the old `…:001` resolve to a different fact. So the rule is data:

  · every batch file `news_show_<date>.ak` defines items `neta:studio_ai:news_show:<date>:NNN`
    (and their `:angle` / optional `:sponsor`) — the file's own date, never a bare number
  · no two files of the pack define the same alias
  · every `set.add` in a file names an alias that SAME file defines (a batch cannot adopt another's)
  · only fact atoms are in the item Set; the PACK.json states the rule

and, on a REAL loader and a real cell (Silica, then SQLite, each in its own process):

  · after loading the shipped pack, `neta:studio_ai:news_show:src` holds exactly the items the
    batch files define (48), each with its text and its angle bound
  · a cell that still carries the previous batch's bare-numbered ids (the live cell after 09-28)
    ends with exactly those 48 — the old ids are retired and out of the Set, so no item airs twice

Run:  python app/test/neta_batches_eval.py     (exit 0 = all pass)
"""
import glob
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

PACK = os.path.join(ROOT, "app", "ontology", "station_neta")
ITEM_SET = "neta:studio_ai:news_show:src"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _defs(path):
    return re.findall(r'^def "([^"]+)" "', open(path, encoding="utf-8").read(), re.M)


def _sets(path):
    return re.findall(r'^set\.add name="([^"]+)" id="([^"]+)"', open(path, encoding="utf-8").read(), re.M)


def static():
    print("\n  ── the batch files ──")
    batches = sorted(glob.glob(os.path.join(PACK, "news_show_*.ak")))
    check("the pack has at least one batch file", bool(batches), str([os.path.basename(b) for b in batches]))
    seen, dupes = {}, []
    for f in sorted(glob.glob(os.path.join(PACK, "*.ak"))):
        for a in _defs(f):
            if a in seen and seen[a] != f:
                dupes.append((a, os.path.basename(seen[a]), os.path.basename(f)))
            seen.setdefault(a, f)
    check("no two files of the pack define the same alias", not dupes, str(dupes[:3]))
    for b in batches:
        base = os.path.basename(b)
        date = re.match(r"news_show_(\d{4}-\d{2}-\d{2})\.ak$", base)
        check("%s is named for its date" % base, bool(date), base)
        if not date:
            continue
        pref = "neta:studio_ai:news_show:%s:" % date.group(1)
        defs = _defs(b)
        bad = [a for a in defs if not a.startswith(pref)]
        check("%s: every id it defines carries its own date (%s…)" % (base, pref), defs and not bad,
              str(bad[:3]))
        shape = [a for a in defs if not re.fullmatch(re.escape(pref) + r"\d{3}(:angle|:sponsor)?", a)]
        check("%s: ids are NNN, NNN:angle or NNN:sponsor" % base, not shape, str(shape[:3]))
        mine = set(defs)
        foreign = [(s, i) for s, i in _sets(b) if i not in mine]
        check("%s: every set.add names an alias this file defines" % base, not foreign, str(foreign[:3]))
        in_set = [i for s, i in _sets(b) if s == ITEM_SET]
        facts = [a for a in defs if re.fullmatch(re.escape(pref) + r"\d{3}", a)]
        check("%s: the item Set holds exactly the facts (no angle, no sponsor in it)" % base,
              sorted(in_set) == sorted(facts), "%d in set, %d facts" % (len(in_set), len(facts)))
        check("%s: every fact has its :angle" % base,
              all((a + ":angle") in mine for a in facts), "")
    desc = json.load(open(os.path.join(PACK, "PACK.json"), encoding="utf-8")).get("description", "")
    check("PACK.json states the rule (an id is never reused; a refresh adds a file)",
          "NEVER reused" in desc and "ADDS a batch file" in desc and "re-used NNN takes" not in desc)
    return batches


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


class _Log(logging.Handler):
    def __init__(self):
        super().__init__(); self.lines = []

    def emit(self, r):
        self.lines.append(r.getMessage())


def live(batches):
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology import loader as L
    be = os.environ.get("AKASHA_BACKEND", "?")
    print("\n  ── a real load, backend=%s ──" % be)
    root = tempfile.mkdtemp(prefix="neta_batches_")
    ont = os.path.join(root, "ontology")
    shutil.copytree(PACK, os.path.join(ont, "station_neta"))
    _write(os.path.join(ont, "REGISTRY.json"), [json.dumps({"version": 2, "packages": [
        {"name": "station_neta", "autoload": True}]})])
    _write(os.path.join(root, "config", "ontology", "packs.json"), [json.dumps({"load_all": True})])
    # the live cell after 09-28: the PREVIOUS batch's bare-numbered ids are still defined. Its file
    # is not in the shipped pack any more, so it is added for the first load and removed for the next.
    legacy = os.path.join(ont, "station_neta", "news_show_2026-08-20.ak")
    old_ids = ["neta:studio_ai:news_show:%03d" % i for i in range(1, 19)]
    _write(legacy, ['def "%s" "OLD batch item %d, bare-numbered"' % (a, i + 1) for i, a in enumerate(old_ids)]
           + ['set.add name="%s" id="%s"' % (ITEM_SET, a) for a in old_ids])
    os.environ["AKASHA_APP_DIR"] = root          # the fixture IS the application root (SPEC §2)
    os.environ["AKASHA_PROJECT_DIR"] = root      # the loader reads the cell policy (config/ontology/packs.json) from here
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=os.path.join(root, "cell"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    time.sleep(1.0)
    k._boot_daemons_started = True
    log = _Log()
    for lg in ("Akasha.Kernel", "Akasha.Reconcile", ""):
        logging.getLogger(lg).addHandler(log)
    logging.getLogger("Akasha.Kernel").setLevel(logging.INFO)

    def d(method, data):
        return (k.dispatch({"jsonrpc": "2.0", "method": method,
                            "params": {"session_token": "admin", "data": data}, "id": "t"},
                           "local") or {}).get("result") or {}

    def load():
        k._schedule_gates = None
        L.boot_load_ontology(k)

    def members():
        r = d("set.ls", {"name": ITEM_SET, "limit": "500"})
        return sorted(str(m.get("alias") or m.get("id") or m) for m in (r.get("members") or r.get("items") or []))

    load()
    first = members()
    check("(the live cell's starting point) the previous batch's 18 bare ids and the 48 new ones are all in "
          "the Set after the first load", len(first) == 66, "%d members" % len(first))
    os.remove(legacy)                      # the previous batch's file is retired by REMOVING it
    load()
    final = members()
    want = []
    for b in batches:
        date = re.match(r"news_show_(\d{4}-\d{2}-\d{2})\.ak$", os.path.basename(b)).group(1)
        want += [a for a in _defs(b) if re.fullmatch(r"neta:studio_ai:news_show:%s:\d{3}" % date, a)]
    check("after the shipped pack loads, the Set holds EXACTLY the items the batch files define (%d)" % len(want),
          sorted(final) == sorted(want), "set=%d want=%d extra=%s missing=%s" % (
              len(final), len(want), sorted(set(final) - set(want))[:3], sorted(set(want) - set(final))[:3]))
    check("…and none of the previous batch's bare ids is left in it",
          not [m for m in final if re.fullmatch(r"neta:studio_ai:news_show:\d{3}", m)])
    nuc = k.manager.shared_nucleus
    unbound = [a for a in want if not nuc.core.get_key_by_alias(a) or not nuc.core.get_key_by_alias(a + ":angle")]
    check("every item has its text and its angle bound to its own name", not unbound, str(unbound[:3]))
    texts = []
    for a in want[:5]:
        c = (d("r", {"id": a}).get("content") or "")
        texts.append(c.split("\n", 1)[-1][:40])
    check("each item reads back its own text (spot check)", all(len(t) > 20 for t in texts), str(texts[:2]))
    load()
    check("a further unchanged load leaves the Set as it was", sorted(members()) == sorted(want))
    shutil.rmtree(root, ignore_errors=True)


def main():
    batches = static()
    if os.environ.get("AKASHA_BACKEND"):
        live(batches)
        print()
        if _fails:
            print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
            return 1
        print("RESULT: PASS\n")
        return 0
    import subprocess
    rc = 1 if _fails else 0
    for be in ("silica", "sqlite"):
        print("\n#### backend=%s" % be)
        rc |= subprocess.call([sys.executable, os.path.abspath(__file__)], env=dict(os.environ, AKASHA_BACKEND=be))
    print()
    if rc:
        print("RESULT: FAIL — see above\n")
        return 1
    print("RESULT: PASS — a news batch mints its own date-prefixed ids and never reuses one; no two files "
          "define an alias; every set.add names its own file's alias; and a real load on Silica and on "
          "SQLite, even over the previous batch's bare-numbered ids, leaves the item Set holding exactly "
          "the items the batch files define.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
