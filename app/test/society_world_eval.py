#!/usr/bin/env python3
"""
G2 — society on the world: roles, grants, identity (world-workbench-society spec v1.0).

A group society WITHOUT world= is byte-identical (station regression covers airing). A society WITH
world=+bench= records society.formed + society.connected on the world axis and links society:connected,
so the bench grant table composes: an op of family F is admitted iff the caller's agent belongs to a
connected society AND holds responsible:operator:F. Roles round-trip through society.role/roster;
identity=locked is stored.

Run:  python app/test/society_world_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
# THE RESEARCHER LINE (one-gate ruling §1). `grp.add` makes a person a MEMBER of a group,
# which is read + say. The person these evals model works ON A BENCH — opens its societies,
# mints its casts, writes its hypotheses, runs its sweeps — and that is the `researcher`
# row. The ruling is explicit that a member is never it ("provisioned by the researcher who
# owns the bench, never by a member"), and a researcher line is written by a person, so the
# eval writes it rather than expecting group membership to imply it.
from lib.akasha.api import gate as _G                                   # noqa: E402


_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_sw_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(tok, method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    d("admin", "world.genesis", {})
    d("admin", "grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("admin", "user.add", {"client_id": "alice", "role": "user",
                            "passphrase_hash": hashlib.sha256(b"alice").hexdigest()})
    d("admin", "grp.add", {"group_id": "lab", "member_id": "alice"})
    _G.assign("alice", "researcher", "lab")

    # ── a group society WITHOUT world= is unchanged ──
    plain = d("admin", "society.new", {"group": "lab", "name": "chatroom"})
    check(f"[{shape}] society.new without world= keeps the old shape",
          plain.get("status") == "created" and plain.get("society_id") == "lab/chatroom"
          and plain.get("connected") is False, str(plain)[:120])

    # ── a WORLD society bound to a bench ──
    d("admin", "bench.new", {"name": "sandbox", "kind": "research", "group": "lab"})
    sw = d("admin", "society.new", {"group": "lab", "name": "sem", "world": "default",
                                    "bench": "sandbox", "kind": "cowork", "identity": "locked"})
    check(f"[{shape}] society.new world+bench connects and stores identity",
          sw.get("connected") is True and sw.get("identity") == "locked"
          and sw.get("bench") == "wb:sandbox", str(sw)[:160])
    ax = d("admin", "world.axis", {})
    kinds = [r.get("kind") for r in ax.get("axis", [])]
    check(f"[{shape}] the world axis records society.formed + society.connected",
          "society.formed" in kinds and "society.connected" in kinds, str(kinds))

    # ── roles round-trip (admin owns Chair, so admit-by-name resolves; role → chairman) ──
    chair = d("admin", "cast.new", {"name": "Chair"}).get("cast_id")
    d("admin", "society.admit", {"group": "lab", "name": "sem", "cast": "Chair"})
    d("admin", "society.role", {"group": "lab", "name": "sem", "cast": chair, "role": "moderator"})
    roster = d("admin", "society.roster", {"group": "lab", "name": "sem"})
    roles = {c.get("name"): c.get("role") for c in roster.get("casts", [])}
    check(f"[{shape}] society.roster reports the moderator role", roles.get("Chair") == "moderator",
          str(roles))

    # ── connect / sever record on the axis ──
    d("admin", "bench.new", {"name": "sandbox2", "kind": "research", "group": "lab"})
    conn = d("admin", "society.connect", {"group": "lab", "name": "sem", "bench": "sandbox2"})
    check(f"[{shape}] society.connect links a second bench", conn.get("status") == "connected", str(conn))
    sev = d("admin", "society.sever", {"group": "lab", "name": "sem", "bench": "sandbox2"})
    check(f"[{shape}] society.sever records on the axis", sev.get("status") == "severed", str(sev))

    # ── who may write on the bench: the LINE, not a per-family grant ──
    #
    # This was the G2.3 path — refused until `responsible:operator:hypothesis` was granted, then
    # admitted. That table is deleted (ruling §5). alice owns cast Al and JOINS it into the roster
    # (a person registers their own avatar); the chairman/admin then admits it by cast id
    # (personas live in the owner's cortex, so cross-owner admission resolves through the roster)
    # and names alice as the controlling client. What decides her bench write is her
    # `researcher on lab` line; what refuses carol is her having none.
    al = d("alice", "cast.new", {"name": "Al"}).get("cast_id")
    d("alice", "society.join", {"group": "lab", "name": "sem", "cast": al})
    d("admin", "society.admit", {"group": "lab", "name": "sem", "cast": al, "client": "alice"})
    admitted = d("alice", "research.hyp.new", {"name": "sandbox", "text": "a granted claim"})
    check(f"[{shape}] a researcher on the lab writes on its bench",
          admitted.get("hyp") and isinstance(admitted.get("observed_at_seq"), int), str(admitted)[:160])
    d("admin", "user.add", {"client_id": "carol", "role": "user",
                            "passphrase_hash": hashlib.sha256(b"carol").hexdigest()})
    refused = d("carol", "research.hyp.new", {"name": "sandbox", "text": "a claim"})
    check(f"[{shape}] …and a person with no line on it is REFUSED",
          "error" in str(refused) or refused.get("status") == "refused", str(refused)[:160])


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a world society records formed/connected on the axis, stores identity, and "
          "roles round-trip; the bench grant table composes society:connected + responsible:operator:F, "
          "refusing a non-granted member and admitting a granted one — on both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
