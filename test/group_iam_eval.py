#!/usr/bin/env python3
"""
P0-a slice 2 residues — GROUP IAM (S2-e / S2-f / S2-g).

The acceptance run exposed three group-membership gaps that broke the one CLI step it needed
(a Genesis-named admin running a society whose bench lives in a group):

  • S2-e — the provisioned group must CONTAIN the Genesis admin(s). society.run opens the group
    engine by MEMBERSHIP (scope:group_<gid>), not by the admin ROLE, so a Genesis admin named
    other than the literal `admin` was refused. Provisioning now adds every admin-role identity as
    a member (idempotent). Here we exercise the underlying IAM primitive the provisioner relies on.
  • S2-f — grp.add / grp.rm / grp.lib on an UNKNOWN group is refused (-32002) instead of silently
    minting a phantom group; and the grp.* CLI accepts BOTH positional and key=value spellings
    (a `group_id=…` token no longer becomes the group id itself).
  • S2-g — grp.ls returns the full record only to an ADMIN / the group's admin / a MEMBER; anyone
    else (a guest) sees {group_id, member_count} — member ids never leak outside the circle.

Run:  python test/group_iam_eval.py     (exit 0 = all pass)
"""
import hashlib
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


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_grpiam_"))
    # Genesis admin is named `henri` (id != the literal `admin`), to exercise S2-e/S2-g's role check.
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "henri",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data, tok="henri", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r

    def res(r):
        return r if "error" in r else (r.get("result") or {})

    # a guest session (network trust, no scopes)
    gr = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                     "params": {"data": {}}, "id": "gg"}, "network")
    gtok = (gr.get("result") or {}).get("binding_key")

    iam = k.iam

    # ── S2-f — grp.add on an UNKNOWN group is refused -32002 (no phantom group minted) ──
    r_unknown = a("grp.add", {"group_id": "no-such-group", "member_id": "henri"})
    check(f"[{shape}] grp.add on an unknown group returns -32002 (no phantom group)",
          "error" in r_unknown and r_unknown["error"].get("code") == -32002,
          str(r_unknown.get("error"))[:120])
    check(f"[{shape}] the refused grp.add did NOT create the group",
          iam.get_group("no-such-group") is None)
    r_rm = a("grp.rm", {"group_id": "no-such-group", "member_id": "henri"})
    r_lib = a("grp.lib", {"group_id": "no-such-group", "action": "grant", "member_id": "henri"})
    check(f"[{shape}] grp.rm / grp.lib on an unknown group are refused -32002 too",
          all("error" in r and r["error"].get("code") == -32002 for r in (r_rm, r_lib)),
          f"rm={r_rm.get('error', {}).get('code')} lib={r_lib.get('error', {}).get('code')}")

    # the IAM primitive S2-f rests on: add_group_member raises on an unknown group
    _raised = False
    try:
        iam.add_group_member("still-no-group", "henri", "henri")
    except KeyError:
        _raised = True
    check(f"[{shape}] iam.add_group_member raises on an unknown group (only grp.new creates one)",
          _raised and iam.get_group("still-no-group") is None)

    # ── now create a real group, then grp.add works ──
    a("grp.new", {"group_id": "plants-lab", "admin_id": "henri"})
    check(f"[{shape}] grp.new creates the group", iam.get_group("plants-lab") is not None)
    a("user.add", {"client_id": "bob", "role": "user",
                   "passphrase_hash": hashlib.sha256(b"b").hexdigest()})
    r_add = a("grp.add", {"group_id": "plants-lab", "member_id": "bob"})
    check(f"[{shape}] grp.add to a real group succeeds",
          "error" not in r_add, str(res(r_add))[:120])

    # ── S2-e — the IAM primitive the provisioner uses: an admin-role identity becomes a MEMBER
    #    (so society.run's scope:group_<gid> membership check passes for a Genesis admin) ──
    iam.add_group_member("plants-lab", "henri", "henri")          # idempotent self-add (as provision does)
    g_full = iam.get_group("plants-lab")
    check(f"[{shape}] the Genesis admin (henri) is a MEMBER of the group (S2-e mechanism)",
          "henri" in (g_full.get("members") or []), str(g_full.get("members")))

    # ── S2-g — grp.ls: admin/member sees the full record; a guest sees member_count only ──
    gls_admin = res(a("grp.ls", {"group_id": "plants-lab"}))
    _grp = gls_admin.get("group") or {}
    check(f"[{shape}] an admin sees the full group record (members listed)",
          isinstance(_grp.get("members"), list) and "bob" in (_grp.get("members") or []),
          str(_grp)[:140])
    gls_guest = res(a("grp.ls", {"group_id": "plants-lab"}, tok=gtok, trust="network"))
    _gg = gls_guest.get("group") or {}
    check(f"[{shape}] a guest (non-member) sees member_count only — no member ids leak",
          _gg.get("member_count") == len(g_full.get("members") or [])
          and "members" not in _gg and "admin" not in _gg,
          str(_gg)[:140])

    # the LIST form also redacts for a guest
    gls_guest_all = res(a("grp.ls", {}, tok=gtok, trust="network"))
    _rows = gls_guest_all.get("groups") or []
    _leaks = [row for row in _rows if isinstance(row, dict) and "members" in row]
    check(f"[{shape}] grp.ls (list form) redacts member ids for a guest as well",
          not _leaks, f"leaked={len(_leaks)}")

    # ── S2-f (CLI) — the grp.* CLI accepts key=value AND positional, and both agree; a `group_id=…`
    #    token no longer becomes the group id itself (the phantom-group bug) ──
    from api.router import CommandRouter
    req_kv = CommandRouter.build_rpc_request("grp.add group_id=plants-lab member_id=bob", "henri")
    _p_kv = (req_kv.get("params") or {}).get("data") or req_kv.get("params") or {}
    req_pos = CommandRouter.build_rpc_request("grp.add plants-lab bob", "henri")
    _p_pos = (req_pos.get("params") or {}).get("data") or req_pos.get("params") or {}
    check(f"[{shape}] grp.add CLI key=value parses to the real group_id (no phantom `group_id=…`)",
          _p_kv.get("group_id") == "plants-lab" and _p_kv.get("member_id") == "bob", str(_p_kv)[:140])
    check(f"[{shape}] grp.add CLI positional and key=value spellings agree",
          _p_kv.get("group_id") == _p_pos.get("group_id")
          and _p_kv.get("member_id") == _p_pos.get("member_id"), f"kv={_p_kv} pos={_p_pos}")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("\nRESULT: PASS — grp.add/rm/lib refuse an unknown group (-32002, no phantom); the group "
          "contains its admin-role identities (the membership society.run checks); and grp.ls returns "
          "member ids only inside the circle (a guest sees member_count) — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
