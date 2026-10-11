#!/usr/bin/env python3
"""
THE FOUR ENTRANCES — every way an account comes into being, and its assignment line with it.

Ruling `6671f332-ruling-id-sets-one-gate-2026-09-22.md` §4 step 1: an identity with NO line is a
GUEST. That is the right default for an unknown caller and a trap for a known one — an account
that exists in IAM but is named by no line is not "not yet configured", it is *demoted*, silently,
with no error anywhere. So every door an account can come through has to write the line in the
same act, and there are exactly three:

  1. FRESH GENESIS      — `kernel.genesis_rite` makes the operator. It registered the account
                          ADMIN in IAM and wrote no line, so an operator whose id is not the
                          literal `admin` (only `admin admin` is in the bootstrap file) came up
                          ADMIN and was refused everything:
                              [gate] refused identity=henri action=admin target=grp.new
                                     reason=not_allowed
                          Every eval that named its operator `admin` passed while this was broken.
  2. `user.add`         — pairs the account with its line already.
  2b. `auth.register`   — the door the CONSUMER APPS come through, and the one the eighth row
                          exists for. A self-registered account is a `resident`: sovereign in
                          its own cell, reaching nothing outside it. Before the row it resolved
                          to `member` (read + say) and could create nothing of its own — 564 of
                          864 registered methods are `record`, `recipe.new` among them.
There is no third, "existing cell", entrance: a cell starts at Genesis (the purge order), so the
one-time IAM → lines migration is deleted, and this eval holds that it is gone.

Run:  python test/gate_entrances_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.api import gate as G                                   # noqa: E402

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _cell(operator="henri"):
    """A cell whose Genesis operator is NOT the literal `admin` — the deployed shape."""
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="gate_ent_"))
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
    print("the four entrances — an account and its assignment line are one act")
    print("=" * 78)

    # ── 1. FRESH GENESIS ────────────────────────────────────────────────────────────────────
    print("\n  ── 1. fresh Genesis: the operator gets the `admin` row ──")
    k = _cell("henri")
    lines = G.lines_for("henri")
    check("the Genesis operator holds a line at all — without one it is a GUEST",
          bool(lines), str(lines))
    check("…and it is the `admin` row, on everything",
          any(l["idset"] == "admin" and not str(l.get("on") or "") for l in lines), str(lines))
    check("…so the gate admits the operator, under a name that is not the literal `admin`",
          G.gate("henri", G.ADMIN)[0] is True and G.gate("henri", G.PROVISION)[0] is True)
    r = _d(k, "henri", "grp.new", {"group_id": "plants_lab", "admin_id": "henri"})
    check("…and a real operator call goes through (this is the one that was refused)",
          "__error__" not in r, str(r)[:110])

    # ── 2. user.add ─────────────────────────────────────────────────────────────────────────
    print("\n  ── 2. user.add: the account and the line, together ──")
    _d(k, "henri", "user.add", {"client_id": "bob", "role": "user",
                                "passphrase_hash": hashlib.sha256(b"b").hexdigest()})
    check("a new account holds a line before its first request",
          bool(G.lines_for("bob")), str(G.lines_for("bob")))
    _d(k, "henri", "grp.add", {"group_id": "plants_lab", "member_id": "bob"})
    check("…and joining a group is another line, naming that group",
          any(l["idset"] == "member" and str(l.get("on") or "").startswith("plants_lab")
              for l in G.lines_for("bob")), str(G.lines_for("bob")))

    # ── 2b. auth.register — the consumer app's door ─────────────────────────────────────────
    print("\n  ── 2b. auth.register: a self-registered account is a RESIDENT ──")
    os.environ["AKASHA_ALLOW_SELF_REGISTER"] = "1"
    _d(k, "", "auth.register", {"user_id": "dora", "passphrase": "hunter2secret"})
    check("a self-registered account holds a line",
          bool(G.lines_for("dora")), str(G.lines_for("dora")))
    check("…and it is `resident` — the row for a person in their OWN CELL",
          any(l["idset"] == "resident" for l in G.lines_for("dora")), str(G.lines_for("dora")))
    check("…so it may create things of its own, which `member` could not (564 of 864 methods "
          "are `record`)", G.gate("dora", G.RECORD)[0] is True)
    check("…and reaches nothing outside that cell",
          G.gate("dora", G.RECORD, "someone_elses_lab") == (False, G.R_TARGET),
          str(G.gate("dora", G.RECORD, "someone_elses_lab")))

    # ── there is no fourth entrance ─────────────────────────────────────────────────────────
    # A cell starts at Genesis (the purge order: past data is discarded once, at the purge deploy),
    # so every account came through (1), (2) or (2b) and got its line there. The one-time IAM →
    # lines migration, its sentinel and its `# migrated` header defence are deleted (§2).
    print("\n  ── no migration: a cell starts at Genesis ──")
    man = json.load(open(os.path.join(ROOT, "lib", "akasha", "MANIFEST.json"), encoding="utf-8"))
    check("no boot schedule migrates IAM into lines (`gate_migrate` is gone)",
          "gate_migrate" not in (man.get("schedules") or {}))
    check("…and the gate carries no migration code (`migrate`, `install_migration`, `MIGRATED_MARK`)",
          not any(hasattr(G, n) for n in ("migrate", "install_migration", "MIGRATED_MARK",
                                           "SENTINEL_NAME")))

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — every entrance writes the line with the account: a fresh Genesis operator, "
          "an added user, a self-registered resident; and there is no migration — a cell starts at "
          "Genesis, so no account exists without its line.")
    sys.exit(0)


if __name__ == "__main__":
    main()
