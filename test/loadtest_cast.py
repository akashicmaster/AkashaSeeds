#!/usr/bin/env python3
"""
Cast avatar / society test — projecting real-world orgs & sessions into Akasha.

Each client can create a `cast` (avatar) — an alter-ego that helps with work and
represents them in a group (an organisation / society). Beyond static atom sharing,
this brings near-real-time SESSIONS to the akasha space: avatars converse in a
group, an absent member reads the exchange later, and a shared avatar can be
observed by others. Two deliberate properties:

  ANONYMITY (policy choice) — the avatar is an alter-ego, so what it publishes/says
    is authored by the CAST, not the human. disclose=False (SNS): the human is
    hidden. disclose=True (company/org): the avatar is matched to the real member.
  ABSENCE — the society is the persistent group space, so utterances and published
    personas remain for absent members to read on their next visit.

  P1 lifecycle      — cast.new + attributes + map/diagnose/react + ls + open.
  P2 agent-session  — two avatars converse in a group; utterances are anonymous
                      (authored by the avatar) and persistent (an absent member
                      reads them later); a member's avatar reacts to another's line.
  P3 impersonation  — a member cannot say/publish as an avatar they do not own.
  P4 shared-avatar  — cast.publish copies the full persona into the group; another
                      member opens it and reads/reacts read-only.
  P5 disclosure     — disclose=True stamps the real client_id (company); the default
                      hides it (SNS).
  P6 isolation      — a non-member sees no utterances, no shared avatar.

Run:  python test/loadtest_cast.py

Developer verification test (not a user-facing .ak example).
"""
import os
import sys
import json
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def boot():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cast_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def dispatcher(k):
    def d(tok, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": tok, "data": data},
                           "id": "t"}, "local")
    return d


def add_user(d, cid):
    d("admin", "user.add", {"client_id": cid, "role": "user",
                            "passphrase_hash": hashlib.sha256(cid.encode()).hexdigest()})


# ── P1: avatar lifecycle (single client) ─────────────────────────────────────

def phase1_lifecycle(k, d):
    add_user(d, "solo")
    r = d("solo", "cast.new", {"name": "Butler", "identity": "a loyal household butler"})
    cid = (r.get("result") or {}).get("cast_id")
    steps = {
        "trait": d("solo", "cast.trait.set", {"trait": {"response": 0.8, "process": 0.7}}),
        "emotion": d("solo", "cast.emotion.add", {"verb": "serve", "obj": "house", "intensity": 0.6}),
        "skill": d("solo", "cast.skill.add", {"name": "scheduling"}),
        "map": d("solo", "cast.map", {}),
        "diagnose": d("solo", "cast.diagnose", {}),
        "react": d("solo", "cast.react", {"event": {"intensity": 0.9, "frequency": 2}}),
    }
    ls = d("solo", "cast.ls", {})
    names = [c.get("name") for c in (ls.get("result") or {}).get("casts", [])]
    reopened = d("solo", "cast.open", {"id": cid}).get("result", {}).get("status") == "opened"
    ok = (bool(cid) and all("error" not in v for v in steps.values())
          and "Butler" in names and reopened)
    record("P1 lifecycle", ok,
           f"created+active, attrs/map/diagnose/react ok, ls={names}, reopen={reopened}")


# ── shared society setup ─────────────────────────────────────────────────────

def setup_society(k, d):
    d("admin", "grp.new", {"group_id": "house", "admin_id": "admin"})
    for c in ("alice", "bob"):
        add_user(d, c)
        d("admin", "grp.add", {"group_id": "house", "member_id": c})
    add_user(d, "carol")  # NOT a member (outsider)
    alice_cast = d("alice", "cast.new", {"name": "Butler", "identity": "loyal butler"}).get("result", {}).get("cast_id")
    d("alice", "cast.trait.set", {"trait": {"response": 0.8, "process": 0.7}})
    d("alice", "cast.emotion.add", {"verb": "serve", "obj": "house", "intensity": 0.6})
    bob_cast = d("bob", "cast.new", {"name": "Gardener", "identity": "quiet gardener"}).get("result", {}).get("cast_id")
    return alice_cast, bob_cast


# ── P2: agent-mode session — anonymous, persistent conversation ──────────────

def phase2_agent_session(k, d, alice_cast):
    d("alice", "cast.open", {"id": alice_cast})
    say = d("alice", "cast.say", {"group_id": "house", "text": "Shall we plan the garden party?"})
    ukey = (say.get("result") or {}).get("key")
    ge = k.manager._get_group_engine("house")
    row = ge.core.get_chunk_raw(ukey) if ukey else None
    meta = json.loads(row["meta"]) if row else {}
    # Anonymity: utterance authored by the avatar, human hidden.
    anon = bool(row) and row["author"] == alice_cast and meta.get("client_id") is None \
        and meta.get("cast_name") == "Butler"
    # Absence/persistence: a member reads the society timeline (later visit).
    tl = d("bob", "set.ls", {"name": "soc:house"}).get("result") or {}
    member_reads = any(m["key"] == ukey for m in tl.get("members", []))
    # A member's avatar reacts to another avatar's line (group-aware event read).
    react = d("bob", "cast.react", {"event_id": ukey})
    reacted = "error" not in react
    ok = anon and member_reads and reacted
    record("P2 agent-session", ok,
           f"anonymous={anon} (cast_name={meta.get('cast_name')!r}), "
           f"member reads timeline={member_reads}, cross-avatar react={reacted}")
    return ukey


# ── P3: impersonation guard ──────────────────────────────────────────────────

def phase3_impersonation(k, d, alice_cast):
    # Publish so bob CAN open Butler (read-only), then prove he cannot act as it.
    d("alice", "cast.open", {"id": alice_cast})
    d("alice", "cast.publish", {"group_id": "house"})
    opened = d("bob", "cast.open", {"id": alice_cast}).get("result", {}).get("status") == "opened"
    say = d("bob", "cast.say", {"group_id": "house", "text": "I am Butler"})
    say_blocked = "error" in say
    pub = d("bob", "cast.publish", {"group_id": "house"})
    pub_blocked = "error" in pub
    ok = opened and say_blocked and pub_blocked
    record("P3 impersonation", ok,
           f"bob opened Butler={opened}, say-as-Butler blocked={say_blocked}, "
           f"publish-as-Butler blocked={pub_blocked}")


# ── P4: shared-avatar — publish, open, observe/react read-only ───────────────

def phase4_shared_avatar(k, d, alice_cast):
    ge = k.manager._get_group_engine("house")
    # Published by P3; confirm the full structure is in the group space.
    concept_members = ge.core.get_collection_members(f"set:concept:{alice_cast}")
    cast_members = ge.core.get_collection_members(f"set:cast:{alice_cast}")
    d("bob", "cast.open", {"id": alice_cast})
    mp = d("bob", "cast.map", {})
    map_ok = "error" not in mp and (mp.get("result") or {}).get("cast_id") == alice_cast
    rc = d("bob", "cast.react", {"event": {"intensity": 0.9}})
    react_ok = "error" not in rc and (rc.get("result") or {}).get("entity") == "Butler"
    ok = bool(cast_members) and map_ok and react_ok
    record("P4 shared-avatar", ok,
           f"published structure in group (cast_set={len(cast_members)}, "
           f"concept_set={len(concept_members)}), bob map={map_ok}, react={react_ok}")


# ── P5: disclosure — company (matched) vs SNS (anonymous) ────────────────────

def phase5_disclosure(k, d, bob_cast):
    d("bob", "cast.open", {"id": bob_cast})
    ge = k.manager._get_group_engine("house")
    u_open = d("bob", "cast.say", {"group_id": "house", "text": "company line", "disclose": True}).get("result", {})
    m_open = json.loads(ge.core.get_chunk_raw(u_open["key"])["meta"])
    u_anon = d("bob", "cast.say", {"group_id": "house", "text": "sns line"}).get("result", {})
    m_anon = json.loads(ge.core.get_chunk_raw(u_anon["key"])["meta"])
    company = m_open.get("client_id") == "bob" and u_open.get("disclosed") is True
    sns = m_anon.get("client_id") is None and u_anon.get("disclosed") is False
    ok = company and sns
    record("P5 disclosure", ok,
           f"company(disclose)={company} (client_id={m_open.get('client_id')!r}), "
           f"sns(anon)={sns} (client_id={m_anon.get('client_id')!r})")


# ── P6: outsider isolation ───────────────────────────────────────────────────

def phase6_isolation(k, d, alice_cast, ukey):
    tl = d("carol", "set.ls", {"name": "soc:house"}).get("result") or {}
    no_timeline = len(tl.get("members", [])) == 0
    r = d("carol", "r", {"id": ukey})
    utter_denied = "error" in r
    o = d("carol", "cast.open", {"id": alice_cast})
    cast_denied = "error" in o
    ok = no_timeline and utter_denied and cast_denied
    record("P6 isolation", ok,
           f"outsider: no timeline={no_timeline}, utterance denied={utter_denied}, "
           f"cast.open denied={cast_denied}")


def main():
    print("\n  cast avatar / society test "
          "(avatars converse in a group — anonymous, persistent, isolated)\n")
    k = boot()
    d = dispatcher(k)

    phase1_lifecycle(k, d)
    alice_cast, bob_cast = setup_society(k, d)
    ukey = phase2_agent_session(k, d, alice_cast)
    phase3_impersonation(k, d, alice_cast)
    phase4_shared_avatar(k, d, alice_cast)
    phase5_disclosure(k, d, bob_cast)
    phase6_isolation(k, d, alice_cast, ukey)

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — cast avatar / society flow broke somewhere.")
        return 1
    print("\nRESULT: PASS — avatars represent members in a society: converse (anonymous or "
          "matched), persist for absent members, publish for observation, and stay isolated "
          "from non-members.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
