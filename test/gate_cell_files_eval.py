#!/usr/bin/env python3
"""
THE PERMISSION FILES BELONG TO THE CELL — and an existing society's consent survives the deploy.

Two platform items the frontend found in stage 2, held together because they are the same shape:
something that was correct while it lived only in this repository becomes wrong the moment
`config/` ships in a seed.

1. `gate.ASSIGN_PATH` / `IDSETS_PATH` were REPOSITORY-relative. Every eval that boots a cell —
   and every `identity.assign`, and the IAM migration — therefore appended to the actual shipped
   permission file: `python test/gate_eval.py` left `config/identity/assign.ak` DIRTY. With
   `config/identity/` in the seed payload, a `t0`/`eval-owner` line left behind by a test run was
   one `spawn.py` away from being a line in a deployed cell's gate. The files are now
   `<base_dir>/central/identity/`, beside `nucleus.db` and the sentinels, under gitignored
   `data/`; `config/identity/` is a read-only SEED, copied once into a cell that has none.

   (The stage-2 note claimed "full suite, git status clean". It was — because my suite runner ran
   `git checkout config/identity/assign.ak` after every single eval. The tree was scrubbed, not
   untouched, and the scrubbing is what hid this. The runner no longer needs to, and this file is
   what would have caught it.)

2. `set:society:public` is written by `society.public` and by `society.new public=yes` — and
   NEITHER runs for a society that already exists. `society.new` returns `exists` and states
   nothing; the every-boot reconciliation writes only the five DECLARED programmes. So the
   hand-made public spaces (`hall`, `akashapolis`, `plants-lab`) are written by nobody, and their
   guest reads and `publish` are refused `reason=public` on the first boot after the gate lands.
   A one-time migration projects each group's own `soc:public:<gid>` Set into the fact.

Run:  python test/gate_cell_files_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.api import gate as G                                   # noqa: E402
from lib.akasha.api import facts as F                                  # noqa: E402

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _cell(base, operator="henri"):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": operator,
                           "data": {"user_name": operator,
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def _d(k, who, method, data):
    r = k.dispatch({"jsonrpc": "2.0", "method": method,
                    "params": {"session_token": who, "data": data}, "id": "t"}, "local")
    return r.get("result") if "result" in r else {"__error__": r.get("error")}


def main():
    print("=" * 78)
    print("the permission files are the cell's; an existing society's consent survives")
    print("=" * 78)

    # ── 1. THE FILES ARE THE CELL'S ─────────────────────────────────────────────────────────
    print("\n  ── 1. a cell writes its own identity files, never the shipped seed ──")
    seed_before = open(G.SEED_ASSIGN_PATH, encoding="utf-8").read()
    _dirty_before = subprocess.run(["git", "status", "--porcelain", "config/identity/"],
                                   capture_output=True, text=True).stdout.strip()
    base = tempfile.mkdtemp(prefix="gate_cell_")
    k = _cell(base)

    live = os.path.join(base, "central", "identity", "assign.ak")
    check("the cell got its OWN assign.ak, under its base_dir", os.path.exists(live), live)
    check("…and NO idsets.json copy beside it: the table is the shipped one, read as is (the purge "
          "order §2 — no copy, no upgrade)",
          not os.path.exists(os.path.join(base, "central", "identity", "idsets.json"))
          and os.path.abspath(G.IDSETS_PATH) == os.path.abspath(G.SEED_IDSETS_PATH), G.IDSETS_PATH)
    check("…seeded from the shipped config, so a fresh cell boots with the bootstrap rows",
          "anonymous guest" in open(live, encoding="utf-8").read())
    check("…owner-only at rest (0600) — the permission table is not world-readable",
          (os.stat(live).st_mode & 0o777) == 0o600, oct(os.stat(live).st_mode & 0o777))
    check("the gate is reading THAT file, not the repository's",
          os.path.abspath(G.ASSIGN_PATH) == os.path.abspath(live), G.ASSIGN_PATH)

    # The write that used to land in the repository.
    _d(k, "henri", "user.add", {"client_id": "eval_resident", "role": "user",
                                "passphrase_hash": hashlib.sha256(b"x").hexdigest()})
    check("an account added on this cell writes ITS line into the cell's file",
          "eval_resident" in open(live, encoding="utf-8").read())
    check("…and the SHIPPED SEED is byte-identical — this is the leak that could reach a deploy",
          open(G.SEED_ASSIGN_PATH, encoding="utf-8").read() == seed_before)

    # ── 2. AN EXISTING SOCIETY'S CONSENT ────────────────────────────────────────────────────
    #
    # The shape that matters: the society EXISTS and its consent is in the group-local Set, and
    # the fact Set does not know. That is every hand-made public space on the box, because the
    # only writers of the fact are the two ops that do not run for a society that already exists.
    print("\n  ── 2. an existing public society still reads public after the deploy ──")
    _d(k, "henri", "grp.new", {"group_id": "hall", "admin_id": "henri"})
    _d(k, "henri", "society.new", {"group": "hall", "name": "akashapolis", "public": "yes"})
    sid = "hall/akashapolis"

    from lib.akasha.concepts.society import SocietyConcept
    soc = SocietyConcept(k.manager.get_session("henri"))
    ge = soc._group_engine("hall")
    skey = soc._society_key(ge, "hall", "akashapolis")

    # Put the cell back in the pre-migration state: the group Set remembers, the fact does not.
    F.public(k, sid, False)
    check("PRE: the group's own consent Set still holds the space",
          skey in (ge.core.get_collection_members(soc._public_set("hall")) or []))
    check("PRE: …but the FACT does not, so the gate refuses the public read",
          not F.has(k, F.PUBLIC, sid)
          and G.gate("anonymous", G.READ, sid) == (False, G.R_PUBLIC),
          str(G.gate("anonymous", G.READ, sid)))
    bc = _d(k, "henri", "society.broadcast", {"group": "hall", "name": "akashapolis"})
    check("PRE: …and society.broadcast refuses it — this is the deploy-day symptom",
          "__error__" in bc, str(bc)[:110])

    from lib.akasha.concepts import schedules as _sched
    stated, _guest, groups, keys = _sched.migrate_society_consent(k)
    check("the migration ran and reports what it stated",
          stated >= 1 and groups >= 1, "public=%d groups=%d" % (stated, groups))
    # IT NAMES THE KEYS (D3). `public=5` is equally consistent with five OTHER spaces having been
    # migrated, and that ambiguity is what left a live cell unable to tell "the space is called
    # something else" from "the fact was written and then lost". A count is not an answer about a
    # named thing.
    check("…and it NAMES the keys it stated, so a reader can tell WHICH space it meant",
          sid in keys, "keys=%s" % keys)
    check("POST: the fact now holds the space", F.has(k, F.PUBLIC, sid))
    check("POST: …so the gate admits the public read", G.gate("anonymous", G.READ, sid)[0] is True)
    bc2 = _d(k, "henri", "society.broadcast", {"group": "hall", "name": "akashapolis"})
    check("POST: …and society.broadcast serves it", "__error__" not in bc2, str(bc2)[:110])

    # AND A REAL GUEST READS IT, OVER THE NETWORK (D3). The two checks above ask the gate directly
    # and read as the cell's operator; neither is the thing a visitor does. A guest holds no group
    # membership and arrives over TRUST_NETWORK, which is the whole of what "public" is for — so
    # that is the read the migration has to earn, and the one the deploy-day symptom was about.
    _gtok = (_d(k, "henri", "session.guest.create", {}) or {}).get("binding_key") or ""
    _gr = k.dispatch({"jsonrpc": "2.0", "method": "society.broadcast",
                      "params": {"session_token": _gtok,
                                 "data": {"group": "hall", "name": "akashapolis"}}, "id": "g"},
                     "network")
    check("POST: a GUEST, over the network, with no membership, reads the migrated space",
          "result" in _gr and (_gr["result"] or {}).get("sid") == sid,
          str(_gr.get("error") or (_gr.get("result") or {}).get("sid"))[:110])
    _gp = k.dispatch({"jsonrpc": "2.0", "method": "society.broadcast",
                      "params": {"session_token": _gtok,
                                 "data": {"group": "hall", "name": "no_such_space"}}, "id": "g2"},
                     "network")
    check("…while a space the migration never named stays refused to that same guest",
          "result" not in _gp, str(_gp.get("error"))[:110])

    # IT OPENS NOTHING. A projection of a consent that exists, never a decision to grant one.
    _d(k, "henri", "society.new", {"group": "hall", "name": "private_room"})
    _stated2, _g2, _gr2, keys2 = _sched.migrate_society_consent(k)
    check("a space nobody consented to is STILL not public — the migration projects, never grants",
          not F.has(k, F.PUBLIC, "hall/private_room")
          and G.gate("anonymous", G.READ, "hall/private_room") == (False, G.R_PUBLIC)
          and "hall/private_room" not in keys2, "keys=%s" % keys2)

    # ONCE, and keyed where a reader can find it.
    print("\n  ── run once, keyed where a reader can find it ──")
    _sched.schedule_society_consent_migrate(k)
    sdir = os.path.join(base, "central", "sentinels")
    sent = os.path.join(sdir, "society_consent_%s.done" % _sched._CONSENT_MIGRATION_VERSION)
    check("…and it keys itself with its own dated sentinel, so a second boot is a no-op",
          os.path.exists(sent), sent)
    check("the sentinel RECORDS WHICH SPACES it migrated — the log rotates, this does not",
          "keys=" in open(sent, encoding="utf-8").read(),
          open(sent, encoding="utf-8").read().strip())

    # ── D3 — A FIXED MIGRATION IS A DIFFERENT MIGRATION, AND ITS SENTINEL SAYS SO ─────────────
    # The v1 run landed its sentinel on the live cell and the hand-made spaces were STILL not
    # public to a guest. The corrected migration could then never run there: the v1 file said a
    # migration had happened, and a sentinel cannot say WHICH one. So the version is part of the
    # name, and a cell carrying only the old file runs the new migration once, on its own account.
    check("the migration carries a version, and it is past v1",
          _sched._CONSENT_MIGRATION_VERSION != "v1", _sched._CONSENT_MIGRATION_VERSION)
    k3 = _cell(tempfile.mkdtemp(prefix="gate_cell3_"), operator="henri")
    s3 = os.path.join(k3.base_dir, "central", "sentinels")
    os.makedirs(s3, exist_ok=True)
    with open(os.path.join(s3, "society_consent_v1.done"), "w", encoding="utf-8") as fh:
        fh.write("2026-09-24 public=5 open_guest=0 groups=9\n")      # the live cell's own state
    _sched.schedule_society_consent_migrate(k3)
    check("a cell already carrying the v1 sentinel STILL runs the fixed migration",
          os.path.exists(os.path.join(s3, "society_consent_%s.done"
                                      % _sched._CONSENT_MIGRATION_VERSION)),
          str(sorted(os.listdir(s3))))
    check("…and the v1 file is left alone — it is the record that v1 ran, and the only evidence "
          "of the thing being investigated",
          os.path.exists(os.path.join(s3, "society_consent_v1.done")))

    # ── 3. THE FRONTEND'S REPRODUCTION, run LAST ──────────────────────────────────────────
    # The frontend's reproduction, as a reproduction: boot a second cell, then ask git.
    k2 = _cell(tempfile.mkdtemp(prefix="gate_cell2_"), operator="other")
    _d(k2, "other", "user.add", {"client_id": "second_cell_user", "role": "user",
                                 "passphrase_hash": hashlib.sha256(b"y").hexdigest()})
    # A DELTA, not an absolute. What this must hold is that BOOTING CELLS changed nothing under
    # `config/identity/` — not that the operator has no edit of their own pending there, which is
    # a different (and legitimate) state. Comparing the porcelain before and after says exactly
    # the first thing, and it is what the frontend's reproduction actually measured.
    dirty = subprocess.run(["git", "status", "--porcelain", "config/identity/"],
                           capture_output=True, text=True).stdout.strip()
    check("…and `git status config/identity/` is UNCHANGED across two cells being booted and "
          "written to (the reproduction that started this)", dirty == _dirty_before,
          "before=%r after=%r" % (_dirty_before[:60], dirty[:60]))
    check("two cells do not share a table — the second's account is absent from the first's file",
          "second_cell_user" not in open(live, encoding="utf-8").read())

    # ONE CELL PER PROCESS is the model, and this is where it becomes visible: the gate's tables
    # are process-level (`_IDSETS` / `_ASSIGN` / `_LOADED` always were), so `bind` points the ONE
    # gate at the ONE cell and the last kernel constructed wins. A deployment runs a single
    # KernelDispatcher per process, so that is exactly right there — but an eval that builds two
    # has to say which one it is talking about, or it reads cell 1's session against cell 2's
    # table and every identity comes back a guest.
    G.bind(base)
    check("re-binding returns the gate to the first cell's table",
          "eval_resident" in open(G.ASSIGN_PATH, encoding="utf-8").read()
          and os.path.abspath(G.ASSIGN_PATH) == os.path.abspath(live))

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — a cell writes its identity files under its own base_dir (0600, seeded "
          "once from the shipped config), two cells booted and written to leave `config/identity/` "
          "byte-identical and `git status` clean, and an existing society's consent — which no "
          "writer of the fact Set reaches, because neither `society.new` nor the declaration "
          "reconciliation runs for a society that already exists — is projected from the group's "
          "own Set into the fact, once, opening nothing that was not already open.")
    sys.exit(0)


if __name__ == "__main__":
    main()
