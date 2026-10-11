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

  B. The non-judgmental facilitator round logic (pure functions from app/scripts/society_gateway.py,
     no daemon) — direction-only, never rejects.
       R1 open  — the facilitator states the theme and invites all ideas (no criticism).
       R2 synth — the wrap-up collects EVERY idea additively; it ranks/rejects nothing.

Run:  python app/test/society_gateway_eval.py     (exit 0 = all pass)

Developer verification test (not a user-facing .ak example).
"""
import os
import sys
import hashlib
import tempfile
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

# THE RESEARCHER LINE (one-gate ruling §1). `grp.add` makes a person a MEMBER of a group,
# which is read + say — it joins and it speaks. The people this eval models do more than
# that: they mint casts, open spaces and run things, which is the `researcher` row, and the
# ruling is explicit that a member is never it. A researcher line is written by a person,
# so the eval writes it rather than expecting group membership to imply it.
from lib.akasha.api import gate as _G                                   # noqa: E402


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
    """Load app/scripts/society_gateway.py, or None if it isn't bundled in this build.
    The gateway is an optional experimental component; a stripped seed (e.g. the public
    seeds tier) may not ship it, and the eval must SKIP rather than crash there."""
    path = os.path.join(ROOT, "app/scripts", "society_gateway.py")
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
        _G.assign(c, "researcher", "salon")

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
    # JOIN puts the cast on the space's roster, which is what makes it one of the space's declared
    # roles — `society.say` no longer admits an undeclared cast by auto-registering it on the first
    # utterance (step 4 is the ruling's: a declared role, or the speaker itself).
    d("alice", "society.join", {"group": "salon", "space": "jam", "cast": g})
    d("alice", "society.say", {"group": "salon", "space": "jam", "cast": g,
                               "text": "reflective roofs everywhere", "agent": "ai",
                               "provider": "openrouter", "model": "meta-llama/llama-3.1-8b:free"})
    # THE MIRROR IS WHAT THE PUBLIC READS, AND THE RELAY IS WHAT FILLS IT. `society.broadcast` is
    # an alias of the one public read (`feed.read`, ruling 2026-09-23 §3), so it serves the public
    # copy rather than re-deriving the group feed under a second rule — which means a space that
    # has said something has still broadcast nothing until a relay pass carries it across the
    # consent boundary. That pass is the step this check used to get for free.
    d("alice", "society.broadcast.relay", {"group": "salon", "space": "jam"})
    bc = d("alice", "society.broadcast", {"group": "salon", "space": "jam"}).get("result") or {}
    # `ai` (the mirror's own field, set when an external provider was in the loop) rather than the
    # group feed's `agent` string: the public copy carries the fact, not the caller's label.
    ai_msg = next((m for m in bc.get("messages", []) if m.get("ai")), {})
    check("P broadcast marks the AI utterance", ai_msg.get("provider") == "openrouter")
    check("P broadcast attributes the model licence (Built with Llama)",
          "Built with Llama" in ai_msg.get("ai_notice", ""), ai_msg.get("ai_notice", ""))
    check("P broadcast bundles attribution + a disclosure banner",
          any("Built with Llama" in a for a in bc.get("attribution", [])) and bool(bc.get("disclosure")))


def part_b():
    gw = load_gateway()
    if gw is None:
        print("  SKIP  app/scripts/society_gateway.py not bundled in this build "
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


def part_c():
    """Tweet mode (talk show): host frames a ネタ, panel reacts / ツッコミ retorts; burst cadence +
    daily budget; news dedup. Pure functions, no daemon."""
    import tempfile, json as _json
    gw = load_gateway()      # ROOT-relative + skip if the optional gateway isn't bundled (F23)
    if gw is None:
        print("  SKIP  app/scripts/society_gateway.py not bundled in this build "
              "(optional experimental component) — tweet-mode checks skipped")
        return

    host = gw.mock_reply("-", gw.sys_host("Anchor", "AI technology news", "a new open model drops"), "(empty)")
    check("T1 host frames the ネタ (says what it is, invites the panel)",
          "model" in host.lower() and "?" in host, host[:60])
    tw = gw.mock_reply("-", gw.sys_tweet("Panelist", "AI news", 240), "Anchor: model X drops")
    check("T2 panelist posts a short first-person take", bool(tw.strip()) and len(tw) <= 260, tw[:60])
    tsu = gw.mock_reply("-", gw.sys_tsukkomi("Skeptic", 240), "Anchor: model X beats every benchmark")
    check("T3 ツッコミ pushes back (does not just agree)",
          any(w in tsu.lower() for w in ("hold on", "hype", "until", "?")), tsu[:60])

    # burst schedule: a daily budget caps posts across ceil(B/K) bursts
    n, budget = gw.tweet_plan(12, 4, 2)
    check("T4 burst plan: per-day 12 / burst 4 → 3 bursts, budget 12", n == 3 and budget == 12, f"{n},{budget}")
    n0, b0 = gw.tweet_plan(0, 4, 2)
    check("T4 no budget → run --rounds bursts unbounded", n0 == 2 and b0 == 0, f"{n0},{b0}")
    rest = gw.spread_rest(24, 6, 10)
    check("T5 --spread spaces bursts across the day (≈hourly for 24 bursts)", 3000 < rest < 3600, f"{rest:.0f}s")

    # news dedup: each burst gets the newest UNSEEN item
    p = tempfile.mktemp(suffix=".json")
    open(p, "w").write(_json.dumps([{"title": "Item A", "url": "http://a"}, {"title": "Item B", "url": "http://b"}]))
    seen = set()
    a = gw.fetch_news("file://" + p, seen); b = gw.fetch_news("file://" + p, seen); c = gw.fetch_news("file://" + p, seen)
    check("T6 news source yields newest-unseen items then dedups to None",
          a and a["title"] == "Item A" and b and b["title"] == "Item B" and c is None, str((a, b, c)))

    # ── role-fidelity (news caster): 演出=解釈=curation. The ネタ帖 is a set of 演出 curations, each a
    #    thesis(切り口) over 台本 atoms; the driver builds the play queue from them. ──
    # 演出 curations as read back from curation.narrate/ls (thesis=角度, steps=台本 content), out of order:
    items = [
        {"id": "cur:2", "title": "show seg-002", "angle": "Angle: tease 'end of the GPU monopoly?', leave it open.",
         "scripts": ["A cloud vendor ships its own inference chip; volume next year."]},
        {"id": "cur:1", "title": "show seg-001", "angle": "Angle: push 'small but mighty'; one number; end on a question.",
         "scripts": ["A 7B open model matches last-gen 70B; weights fully public."]},
        {"id": "cur:x", "title": "show seg-000-nodir", "angle": "", "scripts": ["orphan script, no interpretation"]},
    ]
    q = gw.neta_queue_from_curations(items)
    check("T7 ネタ帖 = 演出 curations → queue ordered by title, thesis(演出)+台本(script) paired",
          len(q) == 2 and q[0]["id"] == "cur:1" and q[1]["id"] == "cur:2"
          and "7B" in q[0]["script"] and "small but mighty" in q[0]["direction"], str([e["id"] for e in q]))
    check("T7 an interpretation-less entry (no thesis) is dropped — 演出 is required, it IS the point",
          all(e["id"] != "cur:x" for e in q))

    # the caster prompt hands over BOTH the 台本 and the 演出, tagged as take i/n (the role handoff)
    sysp = gw.sys_caster("Anchor", q[0]["script"], q[0]["direction"], 240, 3, 6)
    check("T8 caster is handed 台本 + 演出 + take number, told to PERFORM not read verbatim",
          "SCRIPT:" in sysp and "ANGLE:" in sysp and "take 3 of 6" in sysp
          and "verbatim" in sysp.lower() and "encouraged" in sysp.lower(), sysp[:70])
    line = gw.mock_reply("-", sysp, "(empty)")
    check("T8 caster performs a line that carries the 演出 (ad-lib welcome within it)",
          bool(line.strip()) and "mighty" in line, line[:60])

    # ── continuous public run: ネタ切れ→過去を繰り返す + --forever pacing ──
    n, g = gw.burst_schedule(15, 0, 6, 4, True, 10, 0, False, False, 2)
    check("T9 bounded run: 15 ネタ, no budget → one pass of 15 bursts", n == 15 and g == 0, f"{n},{g}")
    n, g = gw.burst_schedule(15, 300, 6, 4, True, 10, 0, False, False, 2)
    check("T9 budget > ネタ数 → n_bursts wraps past 15 (repeats past news, not capped at 15)", n == 30, str(n))
    n, g = gw.burst_schedule(15, 120, 6, 4, True, 10, 0, False, True, 2)
    check("T9 --forever → endless loop (n_bursts None), gap spreads the daily budget across the day",
          n is None and 6900 < g < 7200, f"{n},{g:.0f}s")
    n, g = gw.burst_schedule(15, 120, 6, 4, True, 10, 300, True, True, 2)
    check("T9 explicit --rest overrides the spread", g == 300, f"{g}")

    # ── T10: fetch_netas reads AS a given identity → an admin-owned auto-loaded ネタ帖 is recoverable ──
    # A mock dispatch that scope-filters: only `admin` sees the curations (as boot app/curations/ would own them).
    _CUR = {"c1": {"title": "news_show seg-001", "thesis": "Angle: small but mighty."}}
    _ATOM = {"a1": "[neta:studio_ai:news_show:001]\nA 7B open model matches 70B."}
    def _mock_d(tok, method, data):
        if method == "curation.ls":
            return {"curations": [dict(curation_id=k2, **v) for k2, v in _CUR.items()]} if tok == "admin" else {"curations": []}
        if method == "curation.narrate":
            return {"steps": [{"key": "a1"}]} if data.get("curation_id") in _CUR else {"steps": []}
        if method == "read":
            return {"content": _ATOM.get(data.get("id"), "")}
        return {}
    as_host = gw.fetch_netas(_mock_d, "llm:host:studio_ai", "news_show seg-")
    as_admin = gw.fetch_netas(_mock_d, "admin", "news_show seg-")
    check("T10 fetch_netas as the host sees nothing when the ネタ帖 is admin-owned (the auto-load trap)",
          as_host == [], str(len(as_host)))
    check("T10 fetch_netas as admin recovers it — script (hub header stripped) + 演出 paired",
          len(as_admin) == 1 and "7B" in as_admin[0]["script"] and "[neta:" not in as_admin[0]["script"]
          and "mighty" in as_admin[0]["direction"], str(as_admin))


def main():
    print("A. open_guest gate (kernel dispatch)")
    part_a()
    print("\nB. non-judgmental facilitator rounds (pure functions)")
    part_b()
    print("\nC. tweet mode / talk show (pure functions)")
    part_c()
    print()
    if _fails:
        print(f"FAIL — {len(_fails)} check(s): {', '.join(_fails)}")
        sys.exit(1)
    print("PASS — society guest-gateway (open_guest gate + non-judgmental brainstorm) verified.")
    sys.exit(0)


if __name__ == "__main__":
    main()
