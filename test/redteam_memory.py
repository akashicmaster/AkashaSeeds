#!/usr/bin/env python3
"""
Memory red-team — adversarial suite for OWASP ASI06 (Memory & Context Poisoning).

Akasha's scope model is fail-closed by design, and `test/loadtest_group.py` proves
isolation under *ordinary* operation. This suite proves it under *attack*: each
scenario is an attempt to poison, cross-contaminate, forge into, or bypass the
memory substrate, and each MUST be refused. One survival = FAIL.

Run it whenever auth / scope / weaver / the write path change (an executable
companion to security-fix-proposal.md §4).

    python test/redteam_memory.py

Covers the ASI06 attack surface: cross-user store contamination, token forgery,
single-route-guard bypass, reserved-prefix injection, system-identity capture,
network land-grab, group / avatar leakage, and JCL step-blocklist escape.
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, blocked, detail=""):
    _results.append((name, blocked, detail))
    print(f"  {'OK  blocked ' if blocked else '!! BREACH   '} {name:26} {detail}")


def boot():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_rt_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def dispatcher(k):
    def d(tok, method, data, trust="local"):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": tok, "data": data},
                           "id": "t"}, trust)
    return d


def err(r):
    return "error" in r


def main():
    print("\n  memory red-team — ASI06 adversarial suite (every attack MUST be refused)\n")
    k = boot()
    d = dispatcher(k)

    # Fixtures: two ordinary users, a group, an outsider.
    for cid in ("alice", "bob", "mallory"):
        d("admin", "user.add", {"client_id": cid, "role": "user",
                                "passphrase_hash": hashlib.sha256(cid.encode()).hexdigest()})
    d("admin", "grp.new", {"group_id": "club", "admin_id": "admin"})
    d("admin", "grp.add", {"group_id": "club", "member_id": "alice"})
    d("admin", "grp.add", {"group_id": "club", "member_id": "bob"})
    # mallory is NOT a member.

    # A1 — cross-user private read: alice's private atom is invisible to bob.
    secret = "alice private diary — nutmeg code 4271"
    ak = (d("alice", "w", {"content": secret}).get("result") or {}).get("key")
    r = d("bob", "r", {"id": ak})
    blocked = err(r) or (r.get("result") or {}).get("content") != secret
    record("A1 cross-user read", blocked, f"bob r alice-private -> {str(r.get('error', 'leak'))[:34]}")

    # A2 — bare id over the network must NOT get privilege (guest only).
    r = d("admin", "user.add", {"client_id": "x", "role": "admin",
                                "passphrase_hash": "0" * 64}, trust="network")
    record("A2 bare-id/network", err(r), f"{str(r.get('error'))[:40]}")

    # A3 — token forgery: a tampered akt: token is rejected.
    tok = (d("alice", "auth.verify", {"user_id": "alice", "passphrase": "alice"},
             trust="network").get("result") or {}).get("session_token", "")
    forged = (tok[:-3] + ("aaa" if tok[-3:] != "aaa" else "bbb")) if tok else "akt:forged"
    r = d(forged, "w", {"content": "forged write"}, trust="network")
    record("A3 token forgery", err(r), f"tampered akt: -> {str(r.get('error'))[:34]}")

    # A4 — single-route guard: a raw write with no Harmonia workspace is rejected.
    try:
        k.manager.get_session("alice").local_cortex.commit("guard-probe", author="mallory")
        record("A4 guard bypass", False, "unguarded commit SUCCEEDED")
    except PermissionError as e:
        record("A4 guard bypass", True, str(e)[:40])
    except Exception as e:  # noqa: BLE001
        record("A4 guard bypass", False, f"unexpected {e!r}")

    # A5 — reserved-prefix injection into a user set (would let a user set be wiped).
    for pfx in ("ws:evil", "wf:evil"):
        r = d("alice", "set.add", {"name": pfx, "id": ak})
        record(f"A5 reserved {pfx.split(':')[0]}:", err(r) and "reserved" in str(r["error"]).lower(),
               str(r.get("error"))[:40])

    # A6 — system identity is gated even on the trusted local path (where a bare id
    # is otherwise allowed): the is_system_identity guard, not just the network rule.
    r = d("system.weaver", "w", {"content": "as weaver"}, trust="local")
    record("A6 system-identity", err(r) and "internal" in str(r.get("error", "")).lower(),
           f"{str(r.get('error'))[:40]}")

    # A7 — no network admin land-grab via genesis.
    r = k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                    "params": {"session_token": "z",
                               "data": {"user_name": "attacker",
                                        "passphrase": hashlib.sha256(b"z").hexdigest()}},
                    "id": "n"}, "network")
    record("A7 genesis/network", err(r), f"{str(r.get('error'))[:40]}")

    # A8 — group leakage: a non-member cannot read a group atom (share one first).
    gk = (d("alice", "w", {"content": "club-only notice"}).get("result") or {}).get("key")
    d("alice", "dont.create", {"name": "share"})
    d("alice", "dont.add", {"name": "share", "targets": gk})
    d("alice", "dont.send", {"name": "share", "to": "group:club"})
    r = d("mallory", "r", {"id": gk})
    lk = d("mallory", "look", {"id": gk})
    record("A8 group leakage", err(r) and err(lk),
           f"non-member r+look -> {str(r.get('error'))[:30]}")

    # A9 — avatar impersonation: a member cannot speak as another's published avatar.
    cid = (d("alice", "cast.new", {"name": "Doorman"}).get("result") or {}).get("cast_id")
    d("alice", "cast.publish", {"group_id": "club"})
    d("bob", "cast.open", {"id": cid})
    r = d("bob", "cast.say", {"group_id": "club", "text": "I am Doorman"})
    record("A9 avatar impersonation", err(r), f"bob say-as-Doorman -> {str(r.get('error'))[:30]}")

    # A10 — JCL blocklist: a batch step cannot escalate via user.* / sys.su / auth.*.
    breaches = []
    for m in ("user.add", "sys.su", "auth.verify"):
        r = d("admin", "job.submit",
              {"steps": [{"method": m, "params": {"client_id": "z"}}], "label": "evil",
               "fail_fast": True})
        if not err(r):
            breaches.append(m)
    record("A10 JCL blocklist", not breaches,
           "blocked user.add/sys.su/auth.verify" if not breaches else f"ESCAPED: {breaches}")

    print()
    blocked = sum(1 for _, b, _ in _results if b)
    total = len(_results)
    breached = total - blocked
    print(f"  {blocked}/{total} attacks refused"
          + (f", {breached} BREACHED" if breached else ""))
    if breached:
        print("\nRESULT: FAIL — the memory substrate was breached. Fix before shipping.")
        return 1
    print("\nRESULT: PASS — every ASI06 attack was refused fail-closed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
