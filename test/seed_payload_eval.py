#!/usr/bin/env python3
"""
A shipped eval's script ships with it (F56 v64).

`scripts/` is not a bundled tree — the crystallizer packs a NAMED list of the few scripts a shipped
eval imports or executes. `scripts/gen_kernel_methods.py` was added to the repo by the layout seed
and to nobody's list, so `manifest_eval` — which runs it with `--check` to prove the generated
access table is in sync — passed on the development tree and FAILED on every deployed one. The note
claimed a PASS the deploy could not reproduce.

The rule this holds: **if a file under `test/` names a `scripts/<x>.py`, that script is in the
payload.** Checked from both sides:

  * ALWAYS (dev tree and deployed tree alike): every `scripts/<x>.py` a shipped eval names EXISTS.
    On a deployed cell this is the check that fails loudly instead of the eval that needs it.
  * GENERATOR-SIDE (the crystallizer is present): the script is in the crystallizer's platform file
    list (`CORE_FILES`), so the next seed carries it rather than relying on the repo checkout.

What an APPLICATION's evals name ships with the application root, which a seed carries whole (see
`seed_declared_paths_eval`); which series ship which docs is the application's series declaration.

Run:  python test/seed_payload_eval.py     (exit 0 = all pass)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

# A reference inside a docstring or a comment is documentation, not a dependency. These are the
# names an eval RUNS or IMPORTS and would fail without; anything else it mentions is prose.
_REF = re.compile(r"""["']((?:\.\./)?scripts/[A-Za-z0-9_]+\.py)["']""")
# Scripts an eval names only to say they are NOT shipped (the private/gated ones).
_EXEMPT = set()


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    evals = sorted(glob.glob("test/*_eval.py"))
    wanted = {}                                   # scripts/x.py -> [evals that name it]
    for f in evals:
        try:
            src = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in _REF.finditer(src):
            p = m.group(1).replace("../", "")
            if p not in _EXEMPT:
                wanted.setdefault(p, []).append(os.path.basename(f))
    check("the evals name at least one script (the check is not vacuous)", bool(wanted),
          "%d scripts referenced by %d evals" % (len(wanted), len(evals)))

    # ── 1. every named script EXISTS (the deployed-tree check) ───────────────────────────────
    missing = sorted(p for p in wanted if not os.path.isfile(p))
    check("every scripts/*.py a shipped eval names exists in this tree — on a deployed cell this "
          "is what fails loudly instead of the eval that needs it",
          not missing, "; ".join("%s (wanted by %s)" % (p, ", ".join(wanted[p])) for p in missing))

    # ── 2. …and the crystallizer bundles it (the generator-side check) ───────────────────────
    if not os.path.isdir(os.path.join(ROOT, "reproductor")):
        print("  ----  crystallizer absent (deployed tree) — the bundling half is generator-side")
    else:
        from reproductor.engine import CORE_FILES
        bundled = set(CORE_FILES)
        unbundled = sorted(p for p in wanted if p not in bundled)
        check("every script a shipped eval names is in the crystallizer's bundled list — a script "
              "in the repo but not in the payload is a PASS the deploy cannot reproduce",
              not unbundled,
              "; ".join("%s (wanted by %s)" % (p, ", ".join(wanted[p])) for p in unbundled))
        check("the access-table generator specifically is bundled (manifest_eval runs it --check)",
              "scripts/gen_kernel_methods.py" in bundled)

    # ── 2b. the platform manual and the delivery note reach a DEPLOYED cell ──────────────────
    # `docs/for-llm/` ships in no seed (0 of the doc entries). A manual written there is a manual
    # the cell that runs the thing cannot read — which is how a deployed tree had nothing under
    # `docs/` naming a manifest, a boot phase or the deployment contract. Both live where the
    # crystallizer's `docs` dirs carry them.
    check("the platform manual is under docs/developer/, a directory the seed ships — not under "
          "docs/for-llm/, which ships in no seed",
          os.path.isfile("docs/developer/platform-manual.md")
          and not os.path.isfile("docs/for-llm/platform-manual.md"))
    check("the manual covers what the order asked: the API modules, the manifest fields, the "
          "deployment contract and the log lines",
          all(t in open("docs/developer/platform-manual.md", encoding="utf-8").read()
              for t in ("api.trust", "api.rpc", "api.ops", "api.schedule", "api.provision",
                        "api.manifest", "api.heart", "concept_class", "hook", "routers",
                        "Manifest field reference", "Deployment contract", "[boot] phase=")))
    # ── 2b. THE PERMISSION FILE THE PAYLOAD SHIPS ───────────────────────────────────────────
    #
    # This is the check that would have refused seed `69e82e8128`. `config/identity/assign.ak` is
    # the BOOTSTRAP table a fresh cell is seeded from, and the cut was taken from a development
    # tree whose copy had been written by a booting cell: it carried a `# migrated` header and
    # eleven test identities (alice / bob / carol, stale `member` lines for the five programmes).
    # On the empty VPS cell `bind()` would have copied that file in, `migrate()` would have read
    # the header, said "already", and left every real IAM identity without a line — `henri` boots
    # a GUEST on a cell that has never migrated anything.
    #
    # Two properties, and they are different failures:
    #   · NO `# migrated` header — a payload may not declare a cell migrated. The key is the
    #     cell's own sentinel now and `bind()` strips a stray header, so this is defence in depth
    #     at the place the defect is actually introduced: the cut.
    #   · ONLY BOOTSTRAP IDENTITIES — an allow-list, not a pattern. A test identity in the
    #     shipped table is a line in every cell built from it, which is the residue path the
    #     per-cell split closed at runtime and this closes at build time.
    _ASSIGN = "config/identity/assign.ak"
    _BOOTSTRAP = {"admin", "anonymous", "system.librarian", "system.weaver", "system.jataka",
                  "system.broadcaster", "system.telemetry"}
    _body = open(_ASSIGN, encoding="utf-8").read() if os.path.isfile(_ASSIGN) else ""
    check("the shipped bootstrap table exists (the check is not vacuous)", bool(_body), _ASSIGN)
    _hdr = [ln for ln in _body.splitlines() if ln.lstrip().startswith("# migrated")]
    check("the shipped assign.ak carries NO `# migrated` header — a payload may not declare a "
          "cell already migrated", not _hdr, "; ".join(_hdr)[:120])
    _named = sorted({ln.split()[0] for ln in _body.splitlines()
                     if ln.strip() and not ln.lstrip().startswith("#")})
    _extra = [i for i in _named if i not in _BOOTSTRAP]
    check("…and names ONLY the bootstrap identities — a test line here is a line in every cell "
          "built from this payload", not _extra, "extra=%s" % _extra[:6])
    check("…and it does name them all, so a fresh cell can boot and an operator can log in",
          set(_named) == _BOOTSTRAP, "missing=%s" % sorted(_BOOTSTRAP - set(_named)))
    # …and the telemetry line names its target (directive 2026-10-02 §5.1): the row is `assigned`
    # now, so a bare `system.telemetry telemetry` would reach nothing on a FRESH cell (a live cell's
    # bare line is adopted at first load, but a fresh cell is seeded from this file).
    _tel = [ln.split("#", 1)[0].split() for ln in _body.splitlines()
            if ln.split("#", 1)[0].split()[:1] == ["system.telemetry"]]
    check("…and `system.telemetry` holds `telemetry on feeds` (the row is `assigned` since §5.1)",
          _tel == [["system.telemetry", "telemetry", "on", "feeds"]], str(_tel))

    # AND THE SAME TWO PROPERTIES INSIDE THE PAYLOAD ITSELF — which is the artefact that ships.
    # The tree check above guards the NEXT cut; this one guards what is already committed, and
    # they are not the same question: a tree cleaned after a bad cut passes the first and says
    # nothing about the payload sitting beside it. `69e82e8128` is exactly that shape.
    def _payload_assign(path):
        import base64, io, zipfile
        src = open(path, encoding="utf-8", errors="replace").read()
        m = re.search(r'PAYLOAD\s*=\s*"""(.*?)"""', src, re.S)
        if not m:
            return None
        z = zipfile.ZipFile(io.BytesIO(base64.b64decode("".join(m.group(1).split()))))
        return z.read(_ASSIGN).decode("utf-8") if _ASSIGN in z.namelist() else None

    for series in ("seeds14", "seeds14n", "thesaurus09", "thesaurus09n"):
        payload = "akasha_seeds_%s.py" % series
        if not os.path.isfile(payload):
            print("  ----  %s not built in this tree — the payload half is build-side" % payload)
            continue
        pb = _payload_assign(payload)
        if pb is None:
            print("  ----  %s ships no %s (an older tier layout)" % (payload, _ASSIGN))
            continue
        p_hdr = [ln for ln in pb.splitlines() if ln.lstrip().startswith("# migrated")]
        p_named = sorted({ln.split()[0] for ln in pb.splitlines()
                          if ln.strip() and not ln.lstrip().startswith("#")})
        p_extra = [i for i in p_named if i not in _BOOTSTRAP]
        check("%s's bundled assign.ak carries NO `# migrated` header" % payload, not p_hdr,
              "; ".join(p_hdr)[:100])
        check("%s's bundled assign.ak names ONLY the bootstrap identities" % payload, not p_extra,
              "extra=%s" % p_extra[:6])
        p_tel = [ln.split("#", 1)[0].split() for ln in pb.splitlines()
                 if ln.split("#", 1)[0].split()[:1] == ["system.telemetry"]]
        if p_tel == [["system.telemetry", "telemetry"]]:
            # a cut from before §5.1: a cell seeded from it adopts the bare line at first load
            # (`gate._adopt_assign_lines`), so it boots with the same reach — named, not failed.
            print("  ----  %s predates §5.1 (bare `system.telemetry telemetry`); the gate adopts it "
                  "at first load — re-cut to ship `on feeds`" % payload)
        else:
            check("%s's bundled telemetry line is `on feeds`" % payload,
                  p_tel == [["system.telemetry", "telemetry", "on", "feeds"]], str(p_tel))

    # ── 3. the generator it names is actually runnable + honest about being in sync ──────────
    if os.path.isfile("scripts/gen_kernel_methods.py"):
        import subprocess
        r = subprocess.run([sys.executable, "scripts/gen_kernel_methods.py", "--check"],
                           capture_output=True, text=True, timeout=300)
        check("`gen_kernel_methods.py --check` runs and reports the shipped table in sync",
              r.returncode == 0, (r.stdout + r.stderr).strip().splitlines()[-1:] and
              (r.stdout + r.stderr).strip().splitlines()[-1] or "rc=%d" % r.returncode)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — every script a shipped eval names exists here and is in the payload the "
          "crystallizer builds, so an eval cannot pass on the development tree and fail on the "
          "deployed one for want of a file.")
    sys.exit(0)


if __name__ == "__main__":
    main()
