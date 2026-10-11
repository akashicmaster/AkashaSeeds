#!/usr/bin/env python3
"""
The seed's own evals pass ON THE SEED — extracted, not on the tree that built it.

`seed_payload_eval` holds that a file an eval names is IN the payload. This holds the next thing:
that the payload, once extracted, actually WORKS. The two are not the same question, and the gap
between them cost a shipped seed.

What it caught the first time it was run. A deployed cell has files in
`app/config/workbench/workloads/` that no development tree carries — the crystallizer generates
`auto_exec.json`, whose top level is a LIST. The turn op took `json.load(...) or {}` for a mapping
and raised `AttributeError` on it, so `society.air` failed with an unhandled error and the whole
station was silent. Every eval in the repo was green. The seed had already been cut and sent.

That class of defect is invisible to any check that runs where the code was written, because the
difference IS the deployment. So the check runs the evals from the extracted payload, in a temporary
directory, exactly as a cell would.

It is deliberately a SMOKE test — a handful of evals that exercise the declaration readers and the
turn, not the whole suite, which would take as long as the suite. If one of them fails here while
passing in the repo, the difference is the deploy and that is the thing worth knowing before a seed
leaves the building.

Run:  python app/test/seed_extract_smoke_eval.py        (exit 0 = all pass; skips if no payload is built)
"""
import base64
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The tier whose payload carries the station: the rooms, the four workloads and the corpus packs.
SEED = os.path.join(ROOT, "akasha_seeds_thesaurus09.py")

# The evals that read a DECLARATION or run a TURN — the surfaces where the deployed directory's
# shape differs from the repo's. Cheap enough to run from a cold extract.
SMOKE = ["station_workload_decl_eval.py",
         "station_new_studios_eval.py",
         "station_turn_on_declaration_eval.py",
         "workload_conformance_eval.py",
         # The CORPUS declarations, added after they shipped in no seed at all. The platform globs
         # `app/config/source/*.json`, the crystallizer packs `config/` file by file, and nobody had put
         # the four declarations on a list — so a thesaurus cell carried four corpora's assets and
         # four importers and imported nothing, while every eval on the tree stayed green because
         # every eval on the tree reads `app/config/source/` from the repo. This is the one surface
         # where "it is in the tree" and "it is in the seed" differ by an entire feature.
         "declared_source_import_eval.py",
         # D13 (09-26): the news show aired invented items under a recorded source. The grounding
         # eval runs on the ARTEFACT so a note can state its result there, not on the tree.
         "station_turn_grounding_eval.py",
         "station_publish_channel_eval.py",
         "station_seal_eval.py",
         # D14 (09-27): the news show aired item 001 on every run. Its cursor eval runs on the artefact.
         "station_source_cursor_eval.py",
         # D16 (10-02): an item id is never reused. The batch rule + a real load on both backends.
         "neta_batches_eval.py", "station_reading_order_eval.py",
         # D18 (10-02): a turn keeps one number across its beats (the bumper never plays mid-turn).
         "station_turn_number_eval.py", "station_bumper_boundary_eval.py",
         # C6 (10-02): the five operation profiles are well-formed and the declarations agree with them.
         "profile_files_eval.py",
         # 10-03: the precompute passes, run as their own clients, and the registered-first lab resolution.
         "analysis_precompute_passes_eval.py", "labo_origin_eval.py",
         # 10-03 item 1 (platform): the driver waits for the declared-workload pass — a method renamed
         # between boots runs under its new name. The directive asks for its output ON the artefact.
         "bench_provision_order_eval.py",
         # 10-03 item 1 (application): the BirdCLEF import skips a frozen, unchanged pool — no source.acquire into it.
         "birdclef_source_import_eval.py",
         # 10-03 item 5 (platform): the ownership bounds at 0 (c, d, e), checked on the artefact.
         "ownership_eval.py",
         # 10-03 item 3: a vlab artwork is counted by the source engine's door (total and one bucket), repaired by one pass.
         "vlab_artwork_status_eval.py"]

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    if not os.path.isfile(SEED):
        print("\n  SKIP — %s is not built in this tree; this check runs against a cut payload.\n"
              % os.path.basename(SEED))
        return 0

    src = open(SEED, encoding="utf-8", errors="replace").read()
    m = re.search(r'PAYLOAD\s*=\s*"""(.*?)"""', src, re.S)
    if not m:
        check("the seed carries a readable payload", False, os.path.basename(SEED))
        return 1
    zf = zipfile.ZipFile(io.BytesIO(base64.b64decode("".join(m.group(1).split()))))

    tmp = tempfile.mkdtemp(prefix="akasha_extract_")
    try:
        zf.extractall(tmp)
        print("\n  extracted %d entries from %s" % (len(zf.namelist()), os.path.basename(SEED)))

        # The deployed directory's shape is the point of the whole file, so it is named rather than
        # left implicit: these are the files that exist THERE and not here.
        here = set(os.listdir(os.path.join(ROOT, "app", "config", "workbench", "workloads")))
        there = set(os.listdir(os.path.join(tmp, "app", "config", "workbench", "workloads")))
        extra = sorted(there - here)
        # Until 2026-09-27 the crystallizer WROTE declarations the repo does not carry (the plants
        # scaffold `bench_plants_vision.json`, `auto_exec.json`) — a second author for one bench.
        # Now every workload is its bench's one author, so the deployed directory holds only what
        # the repo holds (minus what a tier withholds for lack of its requires).
        check("the extracted tree has NO deploy-only declaration file (no second author)", not extra,
              "deploy-only: %s" % ", ".join(extra) if extra else "none")

        print("\n  ── the evals, run FROM the extracted tree ──")
        env = dict(os.environ, AKASHA_SKIP_AUTOINSTALL="1", PYTHONPATH=tmp)
        for name in SMOKE:
            # an application eval ships under app/test, a platform eval under test/
            rel = next((os.path.join(d, name) for d in ("app/test", "test")
                        if os.path.isfile(os.path.join(tmp, d, name))), "")
            if not rel:
                check("%s is in the payload" % name, False, os.path.join(tmp, "app/test", name))
                continue
            r = subprocess.run([sys.executable, rel], cwd=tmp, env=env,
                               capture_output=True, text=True, timeout=1800)
            tail = [l for l in (r.stdout or "").splitlines() if l.strip()][-1:] or \
                   [(r.stderr or "").strip().splitlines()[-1:] or [""]][0]
            fails = [l.strip() for l in (r.stdout or "").splitlines() if l.startswith("  FAIL")]
            check("%s passes on the extracted seed" % name, r.returncode == 0,
                  "; ".join(fails[:2]) or str(tail)[:110])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the seed's own declaration readers and its turn work on the tree the seed "
          "EXTRACTS, not only on the tree that built it. The difference between those two is the "
          "deployment, and it is the only place this class of defect is visible.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
