#!/usr/bin/env python3
"""
A source corpus is imported because a DECLARATION says so — not because the heart knows the dataset.

Step 1 §1.7 of `directive-step1-frontend-port-2026-09-21.md`. Four datasets used to be four bodies
inside `lib/akasha/source/bootstrap.py`, each of which knew its own corpus directory, its own pool
id, its own labo, its own reset rule, its own observer roster and its own library preferences. That
is a thousand lines of application knowledge living in the platform, and it is why adding a fifth
dataset meant editing the heart.

After the port there is one declaration per dataset in `app/config/source/<id>.json` and one entry point
per importer in `app/scripts/`, and what remains platform is only the managed unit around the call
— the heartbeat, the hard cap, the run-once sentinel, the resume cursor.

This eval asserts the CONTRACT between those two halves, because the contract is the whole point:

  · every declaration resolves to a real, callable entry — a declaration naming a function nobody
    wrote is a boot-time error, and it should be found here rather than on a cell;
  · a declared importer RUNS against a real kernel, with a real corpus, and imports it;
  · it does not run twice — a second call with the bundle unchanged opens no file and reports why;
  · a CHANGED bundle is re-imported, which is what makes a correction reach a deployed cell;
  · every returned status says whether the caller earned the right to stop asking (`sentinel`), so
    an interrupted or degraded run is retried instead of being recorded as finished;
  · an ABSENT corpus is not a failure. Most cells ship no corpus at all, and a boot that treats
    that as an error spends every boot reporting it.

Run:  python app/test/declared_source_import_eval.py        (exit 0 = all pass)
"""
import hashlib
import importlib
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

DECLS = os.path.join(ROOT, "app", "config", "source")
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def declarations():
    out = {}
    for fn in sorted(os.listdir(DECLS)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(DECLS, fn), "r", encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and d.get("importer"):
            out[d.get("id") or fn[:-5]] = d
    return out


def entry(decl):
    """Resolve `importer: "module:function"` exactly as a boot would."""
    mod, _, fn = str(decl.get("importer") or "").partition(":")
    return getattr(importlib.import_module(mod), fn)


def main():
    from lib.akasha.kernel import KernelDispatcher

    decls = declarations()
    print("\n  ── every declaration resolves to an entry that exists ──")
    check("four datasets are declared", len(decls) == 4, ", ".join(sorted(decls)))
    for name in sorted(decls):
        try:
            fn = entry(decls[name])
            ok = callable(fn)
            detail = decls[name]["importer"]
        except Exception as exc:
            ok, detail = False, "%s: %s" % (decls[name].get("importer"), exc)
        check("%s → %s" % (name, decls[name].get("importer")), ok, detail if not ok else "")

    print("\n  ── and declares the four things the platform used to hard-code ──")
    for name in sorted(decls):
        d = decls[name]
        check("%s declares corpus / pool / labo / reset_key" % name,
              all(d.get(k) for k in ("corpus", "pool", "reset_key")) and bool(d.get("labo")),
              ", ".join(k for k in ("corpus", "pool", "labo", "reset_key") if not d.get(k)))

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_decl_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"},
               "local")

    from app.scripts import _declared_import as di

    print("\n  ── a corpus this cell does not carry is SKIPPED, not failed ──")
    # The common case by a wide margin: a declaration ships in every seed, a corpus does not.
    absent = dict(decls["mobility_eu_2014"], corpus="assets/_not_on_this_cell")
    r = entry(decls["mobility_eu_2014"])(k, absent, di.Ctl(log=lambda _m: None)) or {}
    check("status is `skipped`, not an error", r.get("status") == "skipped", str(r.get("status")))
    check("… and it does NOT claim the right to stop asking", r.get("sentinel") is False,
          "sentinel=%s" % r.get("sentinel"))
    check("… and says plainly WHICH corpus was missing",
          "absent" in str(r.get("detail")) and "_not_on_this_cell" in str(r.get("detail")),
          str(r.get("detail"))[:80])

    print("\n  ── a declared importer RUNS: the real entry, a real kernel, a real corpus ──")
    # A small stand-in bundle in the shape the mobility importer reads. Real rows would make this a
    # thirty-second eval; the contract under test is the declaration→entry→import path, which three
    # rows exercise exactly as well as 26,605 do.
    import gzip
    tmp = tempfile.mkdtemp(prefix="akasha_corpus_")
    rel = os.path.relpath(tmp, ROOT) if tmp.startswith(ROOT) else ""
    if not rel:                       # the scratch dir is outside the tree — mirror it inside
        tmp = os.path.join(ROOT, "assets", "_eval_mobility_corpus")
        os.makedirs(tmp, exist_ok=True)
        rel = os.path.relpath(tmp, ROOT)
    try:
        rows = [{"respondent_id": "r%d" % i, "country": "IT", "q1": str(i)} for i in (1, 2, 3)]
        with gzip.open(os.path.join(tmp, "respondents.jsonl.gz"), "wt", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        with open(os.path.join(tmp, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump({"id_field": "respondent_id", "artifacts": [], "retrieval": ""}, fh)

        decl = dict(decls["mobility_eu_2014"], corpus=rel,
                    reset_key=[os.path.join(rel, "respondents.jsonl.gz")])
        run = entry(decl)
        lines = []
        r1 = run(k, decl, di.Ctl(log=lines.append)) or {}
        check("it imports, and reports what it imported", r1.get("status") == "complete",
              "%s / %s" % (r1.get("status"), str(r1.get("detail"))[:70]))
        check("… all three rows", str(r1.get("members")) == "3", str(r1.get("members")))
        check("… and NOW it has earned the run-once sentinel", r1.get("sentinel") is True,
              "sentinel=%s" % r1.get("sentinel"))
        check("… having said out loud what it was doing", any("stream" in l for l in lines),
              "%d phases" % len(lines))

        print("\n  ── the same bundle a second time opens nothing ──")
        # R4: a boot is O(what changed). The marker is read before a corpus file is touched, so the
        # second call costs one graph read whatever the corpus weighs.
        lines2 = []
        r2 = run(k, decl, di.Ctl(log=lines2.append)) or {}
        check("it skips", r2.get("status") == "skipped", str(r2.get("status")))
        check("… saying the corpus is unchanged", "unchanged" in str(r2.get("detail")),
              str(r2.get("detail")))
        check("… still holding the sentinel, so the caller does not retry", r2.get("sentinel") is True,
              "sentinel=%s" % r2.get("sentinel"))
        check("… and it did NOT walk the corpus to find that out", not lines2,
              "%d phases: %s" % (len(lines2), lines2[:2]))

        print("\n  ── a CORRECTED bundle is re-imported, which is the whole reason for the hash ──")
        rows[0]["country"] = "FR"          # the same row, corrected — same id, different content
        with gzip.open(os.path.join(tmp, "respondents.jsonl.gz"), "wt", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        lines3 = []
        r3 = run(k, decl, di.Ctl(log=lines3.append)) or {}
        check("it imports again", r3.get("status") == "complete",
              "%s / %s" % (r3.get("status"), str(r3.get("detail"))[:70]))
        check("… and resets nothing — no reset, no adoption, no repair (the purge order rule 1; the "
              "application's importer, 9bbbee5)", not any("reset" in l for l in lines3),
              "; ".join(lines3[:2])[:90])

        print("\n  ── the declared content hash is what decides all of that ──")
        h_a = di.content_hash(decl)
        check("hashing the same bundle twice gives the same answer", h_a == di.content_hash(decl))
        check("… and the cell remembers it", di.recorded_hash(k, decl) == h_a,
              "%s vs %s" % (di.recorded_hash(k, decl)[:12], h_a[:12]))
        check("… as an ATOM, so it survives a move and is visible to a reader",
              bool((k.dispatch({"jsonrpc": "2.0", "method": "r",
                                "params": {"session_token": "admin",
                                           "data": {"id": "source:import:%s:content" % decl["id"]}},
                                "id": "m"}, "local") or {}).get("result")))
        check("… and a key naming a file that is gone hashes DIFFERENTLY",
              di.content_hash(dict(decl, reset_key=[os.path.join(rel, "gone.gz")])) != h_a)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n  ── a FROZEN pool is never re-acquired into (bl_real, 09-26) ──")
    # Every boot of the live cell raised `'NoneType' object has no attribute 'get'` at
    # bl_real_bootstrap.py:494: its pool was frozen by an import from before the content marker
    # existed, so with no marker every boot decided `import`, `source.acquire` refused the frozen
    # frame, and the refusal arrived as None. Replayed here on the real bundled corpus, two rows
    # per config.
    bl = decls.get("bl_real")
    if bl and os.path.isdir(os.path.join(ROOT, bl.get("corpus") or "-")):
        os.environ["AKASHA_SOURCE_BOOTSTRAP_LIMIT"] = "2"
        try:
            run = entry(bl)
            r1 = run(k, bl, di.Ctl(log=lambda _m: None)) or {}
            check("the bundled BL corpus imports and freezes", r1.get("status") == "complete",
                  "%s / %s" % (r1.get("status"), str(r1.get("detail"))[:70]))
            _decide = di.decide
            try:
                # the live cell's state: a frozen, populated pool and no marker
                di.decide = lambda kernel, decl, populated=False: ("import", di.content_hash(decl))
                r2 = run(k, bl, di.Ctl(log=lambda _m: None)) or {}
                check("with no marker, a frozen frame is neither acquired into nor ADOPTED: the import "
                      "names itself `frozen`, keeps no sentinel, raises nothing (rule 1)",
                      r2.get("status") == "frozen" and r2.get("sentinel") is False,
                      "%s / %s" % (r2.get("status"), str(r2.get("detail"))[:80]))
            finally:
                di.decide = _decide
        finally:
            os.environ.pop("AKASHA_SOURCE_BOOTSTRAP_LIMIT", None)
    else:
        check("the bl_real bundle is present to replay against", False, str(bl and bl.get("corpus")))

    print("\n  ── the resume cursor: what lets a capped run converge instead of restarting ──")
    cur = os.path.join(tempfile.mkdtemp(prefix="akasha_cur_"), "progress")
    ctl = di.Ctl(log=lambda _m: None, progress_path=cur)
    check("a fresh cursor reads 0, which is also the honest answer for a first run",
          ctl.progress() == 0, str(ctl.progress()))
    ctl.advance(500)
    check("… and a NEW unit reads back what the last one wrote",
          di.Ctl(progress_path=cur).progress() == 500,
          str(di.Ctl(progress_path=cur).progress()))
    check("a unit with nowhere to write still works (the stand-alone case)",
          di.Ctl().progress() == 0)

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — every source corpus is named by a declaration that resolves to an entry "
          "the user side owns; a declared importer runs against a real cell, imports its corpus, "
          "declines to do it twice, re-imports a corrected one, and tells the caller in every case "
          "whether this run earned the right to not happen again. The heart knows none of the four "
          "datasets by name.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
