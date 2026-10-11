#!/usr/bin/env python3
"""
F47-6.4 / F35 — a guest/bot storm can NEVER occupy the last session slot: a structural reserve keeps
authenticated (non-guest) slots open so the operator is never locked out of their own Cell.

With AKASHA_MAX_LEAVES=5 and a reserve of 2, guests may take at most 3 slots; the 4th guest is
refused while the operator can still sign in and take a reserved slot. This eval drives the manager's
get_session cap directly (no network) and asserts the reserve holds.

Run:  python test/admin_reserve_eval.py   (exit 0 = all pass)
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_MAX_LEAVES"] = "5"
os.environ["AKASHA_ADMIN_SESSION_RESERVE"] = "2"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.manager import AkashaManager
    mgr = AkashaManager(series_name="seeds", base_dir=tempfile.mkdtemp(prefix="reserve_"))
    check("reserve is set from env (2), clamped below the cap",
          mgr._admin_session_reserve == 2 and mgr.max_sessions == 5,
          "reserve=%s cap=%s" % (mgr._admin_session_reserve, mgr.max_sessions))

    # Guests take slots as role=GUEST (unauthenticated ids fall back to the requested role).
    made = 0
    refused = None
    for i in range(6):
        try:
            mgr.get_session("guest:pool:%d" % i, requested_role="leaf")
            made += 1
        except PermissionError as exc:
            refused = str(exc)
            break
    check("guests are capped at max_sessions - reserve (5-2=3)", made == 3,
          "guests_made=%d refused=%s" % (made, refused))
    check("the refusal names the reserved-for-sign-in reason",
          refused and "reserved" in refused.lower(), refused)

    # With 3 guest slots used, an AUTHENTICATED operator can still take a reserved slot. The
    # operator is a REGISTERED identity, as admin is once genesis runs. (This used to lean on the
    # manager's fallback mapping an unknown id's requested_role='admin' → Role.ADMIN; since group 4,
    # 4.1, an identity with no record is answered by the `anonymous` assignment line — a guest — in
    # every series, so an unregistered "operator" is exactly the guest the reserve keeps out.)
    from lib.akasha.identity import Role
    mgr.iam.register_client("operator_one", Role.ADMIN)
    got_admin = False
    try:
        s = mgr.get_session("operator_one", requested_role="admin")
        got_admin = s is not None
    except PermissionError as exc:
        got_admin = False
        print("      (admin refused: %s)" % exc)
    check("an operator (non-guest) still gets a reserved slot while guests are full", got_admin)
    # …and an UNREGISTERED id asking for admin is a guest (4.1): refused at the guest boundary.
    try:
        mgr.get_session("not_registered", requested_role="admin")
        unknown_refused = False
    except PermissionError:
        unknown_refused = True
    check("an unregistered id is answered as `anonymous` (a guest), whatever role it asks for — "
          "refused at the guest boundary", unknown_refused)

    # A further GUEST is now refused (4 sessions, cap-reserve=3 reached for guests).
    guest_refused = False
    try:
        mgr.get_session("guest:pool:99", requested_role="leaf")
    except PermissionError:
        guest_refused = True
    check("a guest is still refused once the reserve boundary is crossed", guest_refused)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — guests are capped below the hard limit so authenticated slots stay reserved; "
          "an operator can always sign in even while guests are at capacity (F35).")
    sys.exit(0)


if __name__ == "__main__":
    main()
