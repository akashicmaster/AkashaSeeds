#!/usr/bin/env python3
"""
Society guest-gateway eval — the free-LLM brainstorm mechanism.

Two halves:

  A. The open_guest gate (in-process kernel, real dispatch) — the outbound consent that external
     LLM guests may join and this feed may leave to a free external tier.
       G1 society.new open_guest=yes sets it; society.info reports it.
       G2 society.guest toggles it (yes→no→read-only query).
       G3 creator-only — a non-creator member cannot change the guest policy.
       G4 a plain space is closed by default (open_guest=false) → the gateway would refuse it.

  B. The non-judgmental facilitator round logic (pure functions from scripts/society_gateway.py,
     no daemon) — direction-only, never rejects.
       R1 open  — the facilitator states the theme and invites all ideas (no criticism).
       R2 synth — the wrap-up collects EVERY idea additively; it ranks/rejects nothing.

Run:  python test/society_gateway_eval.py     (exit 0 = all pass)

Developer verification test (not a user-facing .ak example).
"""
import os
import sys
import hashlib
import tempfile
import importlib.util

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
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_guestgw_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def load_gateway():
    """Load scripts/society_gateway.py, or None if it isn't bundled in this build.
    The gateway is an optional experimental component; a stripped seed (e.g. the public
    seeds tier) may not ship it, and the eval must SKIP rather than crash there."""
    path = os.path.join(ROOT, "scripts", "society_gateway.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("society_gateway", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)     # top-level imports are stdlib only (cell_ipc is inside main)
    return mod


def part_a():
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

    # G1 — open at creation + info reports it
    new = d("alice", "society.new", {"group": "salon", "name": "jam", "topic": "cooling a city",
                                     "open_guest": "yes"}).get("result") or {}
    check("G1 society.new open_guest=yes", new.get("open_guest") is True and new.get("status") == "created")
    info = d("bob", "society.info", {"group": "salon", "space": "jam"}).get("result") or {}
    check("G1 society.info reports open_guest", info.get("open_guest") is True)

    # G3 — creator-only (bob is a member but not the creator)
    denied = d("bob", "society.guest", {"group": "salon", "space": "jam", "open": "no"})
    check("G3 non-creator cannot change guest policy", "error" in denied)
    still = d("alice", "society.info", {"group": "salon", "space": "jam"}).get("result") or {}
    check("G3 policy unchanged after denied toggle", still.get("open_guest") is True)

    # G2 — creator toggles off, then read-only query
    off = d("alice", "society.guest", {"group": "salon", "space": "jam", "open": "no"}).get("result") or {}
    check("G2 society.guest open=no closes it", off.get("open_guest") is False)
    q = d("alice", "society.guest", {"group": "salon", "space": "jam"}).get("result") or {}
    check("G2 society.guest (no arg) is a read-only query", q.get("open_guest") is False)
    back = d("alice", "society.guest", {"group": "salon", "space": "jam", "open": "yes"}).get("result") or {}
    check("G2 society.guest open=yes re-opens it", back.get("open_guest") is True)

    # G4 — a plain space is closed by default → gateway refuses
    d("alice", "society.new", {"group": "salon", "name": "private", "topic": "secret"})
    pinfo = d("alice", "society.info", {"group": "salon", "space": "private"}).get("result") or {}
    check("G4 plain space is open_guest=false by default", pinfo.get("open_guest") is False)
    check("G4 plain space is public=false by default", pinfo.get("public") is False)

    # P — public-broadcast gate (independent of open_guest) + AI disclosure/attribution
    d("alice", "society.public", {"group": "salon", "space": "jam", "open": "yes"})
    jinfo = d("alice", "society.info", {"group": "salon", "space": "jam"}).get("result") or {}
    check("P society.public open=yes sets public (independent of open_guest)",
          jinfo.get("public") is True and jinfo.get("open_guest") is True)
    denied_pub = d("bob", "society.public", {"group": "salon", "space": "jam", "open": "no"})
    check("P non-creator cannot change public policy", "error" in denied_pub)
    # broadcast refuses a non-public space
    refuse = d("alice", "society.broadcast", {"group": "salon", "space": "private"})
    check("P broadcast refuses a non-public space", "error" in refuse)
    # an AI utterance carries its provider/model; broadcast renders the disclosure + attribution
    g = (d("alice", "cast.new", {"name": "Gem", "identity": "guest"}).get("result") or {}).get("cast_id")
    d("alice", "society.say", {"group": "salon", "space": "jam", "cast": g,
                               "text": "reflective roofs everywhere", "agent": "ai",
                               "provider": "openrouter", "model": "meta-llama/llama-3.1-8b:free"})
    bc = d("alice", "society.broadcast", {"group": "salon", "space": "jam"}).get("result") or {}
    ai_msg = next((m for m in bc.get("messages", []) if m.get("agent") == "ai"), {})
    check("P broadcast marks the AI utterance", ai_msg.get("provider") == "openrouter")
    check("P broadcast attributes the model licence (Built with Llama)",
          "Built with Llama" in ai_msg.get("ai_notice", ""), ai_msg.get("ai_notice", ""))
    check("P broadcast bundles attribution + a disclosure banner",
          any("Built with Llama" in a for a in bc.get("attribution", [])) and bool(bc.get("disclosure")))


def part_b():
    gw = load_gateway()
    if gw is None:
        print("  SKIP  scripts/society_gateway.py not bundled in this build "
              "(optional experimental component) — facilitator-round checks skipped")
        return
    persona = "Facil"
    topic = "cooling a city without air conditioning"
    transcript = ("Facil: welcome, all ideas go\n"
                  "Gemini: paint every roof reflective white\n"
                  "Echo: plant vertical forests on towers\n"
                  "Gemini: pump cool seawater through street pipes")

    # R1 — open: states theme, invites, no criticism
    opening = gw.mock_reply("-", gw.sys_open(topic, persona), "(empty)")
    ok_open = (topic.split()[0] in opening) and any(w in opening.lower() for w in ("welcome", "no criticism", "wild"))
    check("R1 facilitator opening states theme + invites (no criticism)", ok_open, opening[:60])

    # R2 — synth: additive, collects multiple ideas, ranks/rejects nothing
    synth = gw.mock_reply("-", gw.sys_synth(persona), transcript)
    collected = sum(1 for kw in ("roof", "forest", "seawater") if kw in synth.lower())
    no_reject = not any(w in synth.lower() for w in ("worst", "reject", "eliminate", "bad idea", "winner", "best idea"))
    check("R2 synth collects multiple ideas additively", collected >= 2, f"{collected}/3 kept")
    check("R2 synth ranks/rejects nothing (non-judgmental)", no_reject, synth[:70])

    # diverge yields a non-empty creative line
    line = gw.mock_reply("-", gw.sys_diverge("Gemini"), transcript)
    check("R2 diverge yields a line", bool(line.strip()), line[:50])


def main():
    print("A. open_guest gate (kernel dispatch)")
    part_a()
    print("\nB. non-judgmental facilitator rounds (pure functions)")
    part_b()
    print()
    if _fails:
        print(f"FAIL — {len(_fails)} check(s): {', '.join(_fails)}")
        sys.exit(1)
    print("PASS — society guest-gateway (open_guest gate + non-judgmental brainstorm) verified.")
    sys.exit(0)


if __name__ == "__main__":
    main()
