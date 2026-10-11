#!/usr/bin/env python3
"""
Set enumeration counts the members the nucleus holds (seeds 13 findings P1).

A pack's `set.add` records membership in the shared NUCLEUS. On a fixture project whose pack the
REAL loader loads (no application), every read of a set counts those members:

  1. `s.ls <set>` counts them — for the admin's console token and for a resident's;
  2. `onto.dump sets <set>` counts them (and the console renders the no-name listing as names), with the set as the word after `sets` (the console's
     positional slot, which used to be read as a namespace filter and fell back to one fixed
     collection, reporting 0) and as `collection=`; a bare name finds a `set:`-prefixed set, as
     `s.ls` does; with no set named, the sets themselves are listed (local + nucleus);
  3. `r <atom>` lists the sets of BOTH stores: an atom with one local membership used to hide every
     set the nucleus held for it;
  4. `lens <set>` scans the same members.

Run:  python test/set_enumeration_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "test"))
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


PACK = "\n".join([
    'def "fx:apple" "Apple fruit"',
    'def "fx:pear" "Pear fruit"',
    'def "fx:plum" "Plum fruit"',
    'set.add name="fx:fruits" id="fx:apple"',
    'set.add name="fx:fruits" id="fx:pear"',
    'set.add name="fx:fruits" id="fx:plum"',
    'set.add name="set:fx:stone" id="fx:plum"',
]) + "\n"


def main():
    print("=" * 78)
    print("Set enumeration counts the nucleus's members")
    print("=" * 78)
    from _fixtures import pack_cell
    k, cli, _root = pack_cell({"a.ak": PACK})
    nuc = k.manager.shared_nucleus
    check("the pack's memberships are in the NUCLEUS (3)",
          len(nuc.core.get_collection_members("fx:fruits") or []) == 3)
    admin = k.dispatch({"jsonrpc": "2.0", "method": "kernel.auth.local", "params": {"data": {}},
                        "id": "a"}, "local")["result"]["session_token"]
    k.dispatch({"jsonrpc": "2.0", "method": "user.add",
                "params": {"session_token": admin,
                           "data": {"client_id": "rita", "role": "user",
                                    "passphrase_hash": hashlib.sha256(b"rita-pass").hexdigest()}},
                "id": "u"}, "local")
    rita = (k.dispatch({"jsonrpc": "2.0", "method": "kernel.auth.verify",
                        "params": {"data": {"user_id": "rita",
                                            "passphrase": hashlib.sha256(b"rita-pass").hexdigest()}},
                        "id": "v"}, "local").get("result") or {}).get("session_token") or "rita"

    print("\n  ── 1. s.ls ──")
    for who, tok in (("admin", admin), ("a resident", rita)):
        r = cli("s.ls fx:fruits", tok)
        check("s.ls counts the 3 nucleus members (%s)" % who,
              (r.get("page") or {}).get("total") == 3 and len(r.get("members") or []) == 3, str(r)[:160])

    print("\n  ── 2. onto.dump sets ──")
    r = cli("onto.dump sets fx:fruits", admin)
    check("`onto.dump sets <set>` (the word after `sets`) counts 3", r.get("count") == 3
          and r.get("collection") == "fx:fruits", str(r)[:160])
    r = cli("onto.dump sets collection=fx:fruits", admin)
    check("`onto.dump sets collection=<set>` counts 3", r.get("count") == 3, str(r)[:160])
    r = cli("onto.dump sets fx:stone", admin)
    check("a bare name finds the `set:`-prefixed set", r.get("count") == 1
          and r.get("collection") == "set:fx:stone", str(r)[:160])
    r = cli("onto.dump sets", admin)
    names = [i.get("collection") for i in (r.get("items") or [])]
    check("with no set named, the sets are listed (fx:fruits, set:fx:stone among them)",
          "fx:fruits" in names and "set:fx:stone" in names, str(names)[:160])
    import contextlib, io, re
    from api.shell import renderer as _R
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _R._render_onto_dump(r)
    shown = [ln.strip() for ln in re.sub(r"\x1b\[[0-9;]*m", "", buf.getvalue()).splitlines()]
    check("…and the console prints those names, no blank rows (seeds 13 request 6)",
          "fx:fruits" in shown and "set:fx:stone" in shown
          and not any(ln == "" for ln in shown[3:3 + len(names)]), str(shown[:8]))

    print("\n  ── 3. r ──")
    key = nuc.core.get_key_by_alias("fx:plum")
    from lib.akasha.jcl.workspace_context import system_context
    with system_context():                     # a fixture membership in the admin's own cortex
        k.manager.get_session("admin").local_cortex.add_to_set("fx:local_pick", key)
    r = cli("r fx:plum", admin)
    sets = r.get("sets") or []
    check("`r` lists the local set AND the nucleus's sets", "fx:local_pick" in sets
          and "fx:fruits" in sets and "set:fx:stone" in sets, str(sets))

    print("\n  ── 4. lens ──")
    r = cli("lens fx:fruits", admin)
    n = (r.get("profile") or {}).get("node_count")
    check("`lens <set>` scans the 3 members", n == 3, str(r)[:200])

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — members a pack records in the nucleus are counted by s.ls (admin and resident), "
          "onto.dump sets (either spelling), r and lens.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
