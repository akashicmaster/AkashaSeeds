#!/usr/bin/env python3
"""
Society eval — the virtual dialogue space as a first-class, LLM-agnostic feature.

`society` is the SPACE (roster + timeline + turn ordering); `cast` is the PERSONA. You speak
into a society AS an avatar you own. Nothing here involves an LLM — an LLM is connected later as
just another avatar.

  S1 space object   — society.new creates a named space in a group (idempotent); society.ls
                      discovers it with its topic.
  S2 avatar say     — society.say posts AS an owned cast (by id and by name); text is authored
                      by the avatar (pseudonymous by default).
  S3 resolved feed  — society.feed returns {cast_name, text, created_at, reply_to} oldest→newest.
  S4 threading      — reply=<key> records a reply; feed thread=<key> filters to a message + its
                      direct replies (flat + optional reply).
  S5 multi-space    — two named spaces in one group keep separate timelines.
  S6 turn ordering  — society.turn (defined by the space, not the client) reports last speaker +
                      a suggested next avatar; roster names resolve from the feed.
  S7 main interop   — the default space "main" maps onto soc:<gid>, so cast.say and
                      society.feed(main) share ONE timeline (back-compat with cast.*).
  S8 world cross    — society.world links the space into a world (sys:in_world).
  S9 security       — a non-member cannot say/feed; a member cannot speak as an avatar it does
                      not own (impersonation blocked).

Run:  python test/society_eval.py     (exit 0 = all pass)

Developer verification test (not a user-facing .ak example).
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def boot():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_society_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def main():
    k = boot()

    def d(tok, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": tok, "data": data}, "id": "t"}, "local")

    def au(c):
        d("admin", "user.add", {"client_id": c, "role": "user",
                                "passphrase_hash": hashlib.sha256(c.encode()).hexdigest()})

    d("admin", "grp.new", {"group_id": "salon", "admin_id": "admin"})
    for c in ("alice", "bob"):
        au(c)
        d("admin", "grp.add", {"group_id": "salon", "member_id": c})
    au("carol")  # non-member
    sage = (d("alice", "cast.new", {"name": "Sage", "identity": "host"}).get("result") or {}).get("cast_id")
    echo = (d("bob", "cast.new", {"name": "Echo", "identity": "guest"}).get("result") or {}).get("cast_id")

    # S1 — space object + discovery
    new = d("alice", "society.new", {"group": "salon", "name": "debate", "topic": "free will"}).get("result") or {}
    check("S1 society.new creates a named space", new.get("status") == "created" and new.get("society_id") == "salon/debate")
    dup = d("bob", "society.new", {"society": "salon/debate"}).get("result") or {}
    check("S1 society.new idempotent", dup.get("status") == "exists")
    ls = (d("alice", "society.ls", {"group": "salon"}).get("result") or {}).get("societies", [])
    check("S1 society.ls discovers it + topic", any(s["name"] == "debate" and s["topic"] == "free will" for s in ls))

    # S2 — avatar say (by id and by name)
    r1 = d("alice", "society.say", {"society": "salon/debate", "cast": sage, "text": "Do we choose, or discover our choices?"})
    k1 = (r1.get("result") or {}).get("key")
    r2 = d("bob", "society.say", {"group": "salon", "name": "debate", "cast": "Echo", "text": "We discover, then call it choice.", "reply": k1})
    check("S2 say as owned cast (by id)", (r1.get("result") or {}).get("status") == "said")
    check("S2 say as owned cast (by name)", (r2.get("result") or {}).get("status") == "said")

    # S3 — resolved feed
    feed = d("bob", "society.feed", {"society": "salon/debate"}).get("result") or {}
    msgs = feed.get("messages", [])
    check("S3 feed resolved + ordered", len(msgs) == 2 and msgs[0]["cast_name"] == "Sage" and msgs[1]["cast_name"] == "Echo")
    check("S3 feed pseudonymous (no client_id)", all(not m["disclosed"] for m in msgs))

    # S4 — threading
    check("S4 reply recorded", msgs[1]["reply_to"] == k1)
    thread = d("alice", "society.feed", {"society": "salon/debate", "thread": k1}).get("result") or {}
    check("S4 thread filter (root + direct replies)", thread.get("count") == 2)

    # S5 — multi-space isolation
    d("alice", "society.new", {"group": "salon", "name": "lounge", "topic": "small talk"})
    d("alice", "society.say", {"society": "salon/lounge", "cast": sage, "text": "nice weather"})
    lounge = d("alice", "society.feed", {"society": "salon/lounge"}).get("result") or {}
    debate = d("alice", "society.feed", {"society": "salon/debate"}).get("result") or {}
    check("S5 two spaces keep separate timelines", lounge.get("count") == 1 and debate.get("count") == 2)

    # S6 — turn ordering + roster
    turn = d("alice", "society.turn", {"society": "salon/debate"}).get("result") or {}
    check("S6 turn reports last + suggested next", turn.get("last_cast_name") == "Echo" and turn.get("suggested_next_name") == "Sage")
    roster = {c["name"] for c in (d("alice", "society.roster", {"society": "salon/debate"}).get("result") or {}).get("casts", [])}
    check("S6 roster names resolve from feed", roster == {"Sage", "Echo"})

    # S7 — main-space interop with cast.*
    d("alice", "cast.publish", {"group": "salon"})   # active cast = Sage
    d("alice", "cast.say", {"group": "salon", "text": "(main) hello via cast.say"})
    main_feed = d("bob", "society.feed", {"group": "salon"}).get("result") or {}   # name defaults to main
    check("S7 society.feed(main) sees cast.say", any("hello via cast.say" in m["text"] for m in main_feed.get("messages", [])))
    d("bob", "society.say", {"group": "salon", "cast": echo, "text": "(main) reply via society.say"})
    cast_feed = d("alice", "cast.feed", {"group": "salon"}).get("result") or {}
    check("S7 cast.feed sees society.say(main)", any("reply via society.say" in m["text"] for m in cast_feed.get("messages", [])))

    # S8 — world cross
    w = (d("alice", "world.new", {"title": "Atlantis"}).get("result") or {}).get("world_id")
    crossed = d("alice", "society.world", {"society": "salon/debate", "world": w}).get("result") or {}
    check("S8 society.world crosses into a world", crossed.get("status") == "crossed" and crossed.get("world") == w)

    # S9 — security
    check("S9 non-member say denied", "error" in d("carol", "society.say", {"society": "salon/debate", "cast": sage, "text": "x"}))
    check("S9 non-member feed denied", "error" in d("carol", "society.feed", {"society": "salon/debate"}))
    check("S9 impersonation blocked", "error" in d("bob", "society.say", {"society": "salon/debate", "cast": sage, "text": "x"}))

    # S10 — coworking governance anchors (reserved-space seam): kind + responsible decider + info
    cw = d("alice", "society.new", {"group": "salon", "space": "board", "kind": "cowork", "topic": "decisions"}).get("result") or {}
    check("S10 society.new kind=cowork recorded", cw.get("kind") == "cowork")
    d("alice", "society.say", {"society": "salon/board", "cast": sage, "text": "proposal"})
    d("bob", "society.say", {"society": "salon/board", "cast": echo, "text": "seconded"})
    dec = d("alice", "society.decider", {"society": "salon/board", "cast": "Sage"}).get("result") or {}
    check("S10 creator designates a decider (by name)", dec.get("status") == "decider_set" and dec.get("decider_name") == "Sage")
    check("S10 non-creator cannot set decider", "error" in d("bob", "society.decider", {"society": "salon/board", "cast": echo}))
    d("alice", "society.decider", {"society": "salon/board", "cast": echo})   # replace
    info = d("bob", "society.info", {"society": "salon/board"}).get("result") or {}
    check("S10 society.info surfaces kind/topic/decider", info.get("kind") == "cowork" and info.get("topic") == "decisions" and info.get("decider_name") == "Echo")
    check("S10 decider replace is single (not accumulated)", info.get("decider") == echo)
    check("S10 default space kind is chat", (d("alice", "society.info", {"group": "salon"}).get("result") or {}).get("kind") == "chat")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — society: space object, avatar say, resolved feed, threading, multi-space, "
          "turn ordering, cast.* interop, world cross, security.")
    sys.exit(0)


if __name__ == "__main__":
    main()
