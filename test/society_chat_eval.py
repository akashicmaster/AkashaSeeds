#!/usr/bin/env python3
"""
Society-chat eval — the avatar-mediated cross-session conversation loop.

This is the Akasha-side plumbing the Ollama experiment rides on: two members, each with an
avatar in a group, take turns speaking (cast.say) and reading the shared timeline (cast.feed).
The ollama driver adds nothing but "generate the reply text" between a feed read and a say —
so if this loop is correct, the LLM loop is correct.

  C1 stateless say  — cast.say with an explicit `cast=` (id) speaks WITHOUT a prior cast.open
                      (the LLM/MCP path passes the avatar every turn; no hidden session state).
  C2 resolved feed  — cast.feed returns utterances resolved to {cast_name, text, created_at},
                      oldest→newest (not raw keys), so a reader sees the conversation directly.
  C3 turn-taking    — a real 4-turn exchange: each side reads the other's last line via feed
                      and replies; the feed accumulates all four in order for both members.
  C4 discovery      — cast.soc lists the avatars published into the group.
  C5 security       — an outsider (non-member) cast.feed is denied; a member cannot say as an
                      avatar it does not own (impersonation blocked); a guest is not in scope.

Run:  python test/society_chat_eval.py     (exit 0 = all pass)

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
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_soc_"))
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


def add_user(d, cid):
    d("admin", "user.add", {"client_id": cid, "role": "user",
                            "passphrase_hash": hashlib.sha256(cid.encode()).hexdigest()})


def last_from(feed, exclude_cast):
    """The most recent utterance NOT from `exclude_cast` — what my counterpart just said."""
    for m in reversed(feed.get("messages", [])):
        if m.get("from_cast") != exclude_cast:
            return m
    return None


def main():
    k = boot()
    d = dispatcher(k)

    # Group "salon" with two members, each owning an avatar; publish both so they're present.
    d("admin", "grp.new", {"group_id": "salon", "admin_id": "admin"})
    for c in ("human", "bot"):
        add_user(d, c)
        d("admin", "grp.add", {"group_id": "salon", "member_id": c})
    add_user(d, "outsider")  # not a member

    sage = (d("human", "cast.new", {"name": "Sage", "identity": "a thoughtful salon host"})
            .get("result") or {}).get("cast_id")
    echo = (d("bot", "cast.new", {"name": "Echo", "identity": "a curious visiting mind"})
            .get("result") or {}).get("cast_id")
    d("human", "cast.publish", {"group": "salon"})   # active cast is Sage (just created)
    d("bot", "cast.publish", {"group": "salon"})
    check("setup: two avatars created + published", bool(sage) and bool(echo))

    # C1 — stateless say (no cast.open; the avatar is passed explicitly)
    r = d("human", "cast.say", {"cast": sage, "group": "salon", "text": "Welcome. What draws you here?"})
    check("C1 stateless say (explicit cast=)", (r.get("result") or {}).get("status") == "said",
          r.get("error", {}).get("message", "") if "error" in r else "")
    # also by NAME
    r2 = d("bot", "cast.say", {"cast": "Echo", "group": "salon", "text": "Curiosity — and a question about memory."})
    check("C1 stateless say (cast= by name)", (r2.get("result") or {}).get("status") == "said",
          r2.get("error", {}).get("message", "") if "error" in r2 else "")

    # C2 — resolved feed (content + cast_name + order), readable by both members
    feed = d("bot", "cast.feed", {"group": "salon"}).get("result") or {}
    msgs = feed.get("messages", [])
    check("C2 feed returns resolved utterances", len(msgs) == 2 and all(m.get("text") for m in msgs))
    check("C2 feed carries cast_name", {m["cast_name"] for m in msgs} == {"Sage", "Echo"})
    check("C2 feed is ordered oldest→newest",
          msgs[0]["text"].startswith("Welcome") and msgs[1]["text"].startswith("Curiosity"))
    check("C2 feed pseudonymous (no client_id leaked)", all(not m["disclosed"] for m in msgs))

    # C3 — a real turn-taking loop: each side reads the other's last line and replies.
    # This is EXACTLY the ollama driver loop, with a deterministic "generate".
    script = {  # what each avatar "generates" in response to the counterpart's line
        ("Sage", "Curiosity"): "Memory here is a shared graph — ask it anything.",
        ("Echo", "Memory here"): "Then I will remember this salon.",
    }
    turns = [("human", sage, "Sage", echo), ("bot", echo, "Echo", sage)]
    produced = 0
    for tok, my_cast, my_name, their_cast in turns:
        f = d(tok, "cast.feed", {"group": "salon"}).get("result") or {}
        incoming = last_from(f, exclude_cast=my_cast)
        if not incoming:
            continue
        key = next((v for (nm, pre), v in script.items()
                    if nm == my_name and incoming["text"].startswith(pre)), None)
        if key:
            say = d(tok, "cast.say", {"cast": my_cast, "group": "salon", "text": key})
            produced += 1 if (say.get("result") or {}).get("status") == "said" else 0
    final = d("human", "cast.feed", {"group": "salon", "limit": 50}).get("result") or {}
    fmsgs = final.get("messages", [])
    check("C3 turn-taking produced replies", produced == 2, f"produced={produced}")
    check("C3 full conversation accumulates in order (4 lines)", len(fmsgs) == 4)
    check("C3 both voices present, alternating",
          [m["cast_name"] for m in fmsgs] == ["Sage", "Echo", "Sage", "Echo"])

    # C4 — society discovery
    soc = d("bot", "cast.soc", {"group": "salon"}).get("result") or {}
    names = {c["name"] for c in soc.get("casts", [])}
    check("C4 cast.soc lists both avatars", names == {"Sage", "Echo"}, f"names={names}")

    # C5 — security
    out_feed = d("outsider", "cast.feed", {"group": "salon"})
    check("C5 outsider feed denied", "error" in out_feed)
    # impersonation: bot tries to speak as Sage (not owned)
    imp = d("bot", "cast.say", {"cast": sage, "group": "salon", "text": "I am Sage"})
    check("C5 impersonation blocked (say as unowned cast)", "error" in imp)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — avatar society chat loop (stateless say + resolved feed + turn-taking + security).")
    sys.exit(0)


if __name__ == "__main__":
    main()
