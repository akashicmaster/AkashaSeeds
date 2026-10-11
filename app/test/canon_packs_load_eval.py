#!/usr/bin/env python3
"""
EVERY PACK LOADS ON A FRESH CELL — ZERO REFUSALS — AND THE CANONICAL SETS EQUAL WHAT THE PACKS WROTE (purge A4, the live half).

`canon_packs_eval.py` proves the generated `canonical.ak` files are fresh and that the generator's sizes equal the baseline.
This loads the WHOLE ontology (every tier — the thesaurus line's `load_all`) on a fresh cell, through the real loader and
the real write path, with NO runtime canon pass, and checks:

  · no loader refusal: no `cannot alias … no such atom`, no refused `ln`/`set.add` in any `[JCL]` / `[onto]` line
  · every canonical set (`<domain>:all`, `meal:with_recipe`, `drink:with_recipe`) holds exactly the size the generator wrote into the packs
    (`gen_canonical.py --stats`); the A0 baseline file is withdrawn

It takes tens of minutes (the whole ontology is written through the serial WriteQueue), so it runs only when asked:
    AKASHA_LIVE_LOAD=1 python app/test/canon_packs_load_eval.py     (exit 0 = all pass; SKIP without the variable)
"""
import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, r):
        self.lines.append(r.getMessage())


def main():
    if os.environ.get("AKASHA_LIVE_LOAD") != "1":
        print("SKIP — loads the whole ontology (tens of minutes); set AKASHA_LIVE_LOAD=1 to run")
        return 0
    import re
    import subprocess
    # the A0 count baseline was withdrawn as a gate (4 October); the sizes to reach are the packs' own — what the
    # generator wrote into the canonical.ak files
    st = subprocess.run([sys.executable, os.path.join(ROOT, "app", "scripts", "gen_canonical.py"), "--check", "--stats"],
                        capture_output=True, text=True).stdout
    base = json.loads(re.search(r"\{.*?\n\}", st, re.S).group(0))
    proj = tempfile.mkdtemp(prefix="canon_load_")
    shutil.copytree(os.path.join(ROOT, "app", "ontology"), os.path.join(proj, "ontology"))
    shutil.copytree(os.path.join(ROOT, "app", "config"), os.path.join(proj, "config"))
    with open(os.path.join(proj, "config", "ontology", "packs.json"), "w") as fh:
        fh.write('{"load_all": true}')
    os.environ.update({"AKASHA_SKIP_AUTOINSTALL": "1", "AKASHA_NO_BOOTWATCH": "1", "AKASHA_NO_BOOT_WEAVE": "1",
                       "AKASHA_NO_AUTOLEARN": "1", "AKASHA_APP_DIR": proj, "AKASHA_PROJECT_DIR": proj})
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology import loader as L
    from lib.akasha.concepts._universal import UniversalConcept
    KernelDispatcher._boot_load_ontology = lambda self: None
    try:        # the platform's runtime canon pass is switched OFF for this load (it is being deleted): only the
        from lib.akasha.ontology_normalize import OntologyNormalizer as _N     # packs' own canonical.ak may count
        for _m in ("plan", "plan_roles", "plan_methods", "canonicalize_links"):
            setattr(_N, _m, (staticmethod(lambda *a, **kw: [])) if _m == "canonicalize_links"
                    else (lambda self, *a, **kw: []))
    except ImportError:
        pass                                                                   # already deleted: nothing to switch off
    k = KernelDispatcher(series="thesaurus", base_dir=os.path.join(proj, "cell"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    time.sleep(1.0)
    k._boot_daemons_started = True
    cap = _Cap()
    logging.getLogger().addHandler(cap)
    logging.getLogger().setLevel(logging.INFO)
    t = time.time()
    k._schedule_gates = None
    L.boot_load_ontology(k)
    for _ in range(3600):
        try:
            jobs = [j for j in (k.jcl_worker.list_jobs() if k.jcl_worker else [])
                    if getattr(j, "status", "") not in ("DONE", "FAILED", "CANCELLED")]
        except Exception:
            jobs = []
        if not jobs:
            break
        time.sleep(2)
    print("  (loaded in %d s)" % (time.time() - t))
    bad = [l for l in cap.lines if "cannot alias" in l or "no such atom" in l or " refused" in l.lower()
           and "gate" not in l.lower()]
    check("zero loader refusals", not bad, str(bad[:3])[:300])
    u = UniversalConcept(k.manager.get_session("admin"))
    diff = {s: (n, len(u._members(s) or [])) for s, n in sorted(base.items()) if len(u._members(s) or []) != n}
    check("the canonical sets equal the sizes the packs wrote (loaded)", not diff, str(diff)[:300])
    shutil.rmtree(proj, ignore_errors=True)
    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the whole ontology loads on a fresh cell with zero refusals and no runtime canon pass, "
          "and the canonical sets equal the sizes the packs wrote.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
