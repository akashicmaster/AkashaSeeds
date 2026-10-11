#!/usr/bin/env python3
"""
society_gateway.py — invite free external LLMs into an Akasha society as brainstorm guests.

A **multi-session gateway**: it holds N guest sessions at once, ONE Akasha client per guest
(1 guest = 1 client; more guests = more clients, never one client for all). Each guest is a pure
chat participant — it only reads the feed and says a line; it has NO Akasha responsibility.

The brainstorm is run by a **non-judgmental facilitator** (NOT a decider): it keeps only the
*direction* and never rejects an idea. Round model — divergence-first, judgment deferred:

    open        facilitator posts the 前提 (topic) + "all ideas welcome, no criticism"
    diverge×N   each participant reads the feed and adds ONE idea (no critique of others)
    synth       facilitator bundles EVERY idea additively (no ranking, no culling)

Judgment happens OUTSIDE the session — a human later reads the feed and confirms the good ideas
into ontology (`.ak`). Nothing is rejected in-room, so the feed captures the whole divergent space.

Gate: the gateway REFUSES to join a space that is not `open_guest` (the outbound consent that this
feed may leave to a free external tier that may train on it). Set it with
`society.new … open_guest=yes` or `society.guest open=yes` (see app/scripts/society_setup.py --open-guest).

Transport: the local Cell IPC (per-client sessions via local trust) — run a daemon first
(`python akasha.py --serve`) and provision with `app/scripts/society_setup.py --open-guest`. Providers
are plain stdlib HTTP (honor HTTPS_PROXY); keys come from the environment, never an atom.

  # Provision (one facilitator + two guests), open to guests:
  python app/scripts/society_setup.py --group salon --space jam --open-guest \
      --participant "llm:facil|Facil|the host|facilitator" \
      --participant "llm:gemini|Gemini|a free external guest|participant" \
      --participant "mcp:local|Echo|a local model|participant"

  # No keys? Prove the whole loop with the mock provider:
  python app/scripts/society_gateway.py --group salon --space jam --rounds 2 \
      --guest "llm:facil|<facil_cast>|mock|-|facilitator" \
      --guest "llm:gemini|<gemini_cast>|mock|-|participant" \
      --guest "mcp:local|<echo_cast>|mock|-|participant"

  # Real free-tier guest (needs AKASHA_GEMINI_KEY):
  #   ... --guest "llm:gemini|<cast>|gemini|gemini-2.0-flash|participant"
"""
import argparse
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)


# ── provider adapters (persona/前提 = system, transcript = user → one line) ──────────
def _http_json(url, body, headers, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def gemini_reply(model, system, transcript):
    """Google AI Studio free tier — generativelanguage REST (key in the query)."""
    key = os.environ.get("AKASHA_GEMINI_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("gemini provider needs AKASHA_GEMINI_KEY (or GEMINI_API_KEY).")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model or 'gemini-2.0-flash'}:generateContent?key={key}")
    body = {"system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": transcript}]}]}
    data = _http_json(url, body, {})
    return "".join(p.get("text", "")
                   for p in (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])).strip()


def openrouter_reply(model, system, transcript):
    """OpenRouter — OpenAI-compatible; many `:free` models under one key."""
    key = os.environ.get("AKASHA_OPENROUTER_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("openrouter provider needs AKASHA_OPENROUTER_KEY (or OPENROUTER_API_KEY).")
    data = _http_json("https://openrouter.ai/api/v1/chat/completions",
                      {"model": model or "meta-llama/llama-3.1-8b-instruct:free",
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": transcript}]},
                      {"Authorization": f"Bearer {key}"})
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()


def ollama_reply(model, system, transcript):
    """Local Ollama — the low-idea baseline the external guests lift."""
    url = os.environ.get("AKASHA_OLLAMA_URL", "http://localhost:11434")
    data = _http_json(url.rstrip("/") + "/api/chat",
                      {"model": model or "llama3", "stream": False,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": transcript}]}, {})
    return (data.get("message", {}).get("content", "") or "").strip()


def mock_reply(model, system, transcript):
    """Canned generator — verifies the whole loop with no key. Phase is inferred from the
    system prompt so open/diverge/synth each yield something sensible."""
    who = ""
    for tag in ("[FACIL-OPEN]", "[FACIL-SYNTH]", "[DIVERGE]", "[HOST]", "[TWEET]", "[TSUKKOMI]", "[CASTER]"):
        if tag in system:
            who = tag
    last = [l for l in transcript.strip().splitlines() if l.strip()]
    if who == "[CASTER]":
        script = system.split("SCRIPT:", 1)[-1].split("ANGLE:", 1)[0].strip() if "SCRIPT:" in system else "the story"
        angle = system.split("ANGLE:", 1)[-1].strip().splitlines()[0] if "ANGLE:" in system else ""
        return f"On air — {script[:44]}… and honestly? {(angle[:44] or 'you did not see this coming')}"
    if who == "[HOST]":
        seg = system.split("SEGMENT:", 1)[-1].strip().splitlines()[0] if "SEGMENT:" in system else \
              (system.split("TOPIC:", 1)[-1].strip().splitlines()[0] if "TOPIC:" in system else "today's item")
        return f"Today's item: {seg[:60]}. Here's what it means — panel, your take?"
    if who == "[TWEET]":
        seed = (last[-1].split(":", 1)[-1].strip() if last else "the news")
        return f"My take: {seed[:40]} is bigger than it looks — watch the second-order effects."
    if who == "[TSUKKOMI]":
        seed = (last[-1].split(":", 1)[-1].strip() if last else "that")
        return f"Hold on — '{seed[:32]}'? That's hype until someone ships it."
    if who == "[FACIL-OPEN]":
        topic = system.split("TOPIC:", 1)[-1].strip().splitlines()[0] if "TOPIC:" in system else "our theme"
        return f"Welcome — let's brainstorm on: {topic}. Every idea is welcome, no criticism. Go wild!"
    if who == "[FACIL-SYNTH]":
        ideas = [l.split(":", 1)[-1].strip() for l in last if ":" in l][-6:]
        bullet = "; ".join(i[:50] for i in ideas) or "(none yet)"
        return f"Ideas gathered (all kept, unranked): {bullet}."
    seed = (last[-1].split(":", 1)[-1].strip() if last else "the theme")
    persona = system.split("You are", 1)[-1].split(".", 1)[0].strip() if "You are" in system else "A guest"
    return f"Building on '{seed[:40]}': what if we {persona.lower()}-style flipped it entirely?"


PROVIDERS = {"gemini": gemini_reply, "openrouter": openrouter_reply,
             "ollama": ollama_reply, "mock": mock_reply}


# ── system prompts (direction only; no constraint on idea content/length) ────────────
def sys_open(topic, persona):
    return (f"[FACIL-OPEN] You are the facilitator of a brainstorm. You are {persona}. "
            f"Post ONE short, warm opening that states the theme and invites all ideas — "
            f"emphasize: no criticism, wild ideas welcome, build on each other.\nTOPIC: {topic}")


def sys_diverge(persona):
    return (f"[DIVERGE] You are {persona}, a participant in a brainstorm. This is divergence: "
            f"offer ONE fresh, creative idea that keeps the theme's direction and builds on what "
            f"others said. Do NOT critique or rank anyone's idea. Write only your line, no name prefix.")


def sys_synth(persona):
    return (f"[FACIL-SYNTH] You are {persona}, the facilitator wrapping up. Read the transcript and "
            f"list EVERY idea raised, additively, WITHOUT judging, ranking, or dropping any. "
            f"A short collected digest — the human will pick from it later.")


def transcript_of(messages, n=12):
    return "\n".join(f"{m.get('cast_name', '?')}: {m.get('text', '')}" for m in messages[-n:]) or "(empty)"


# ── talk-show prompts (mode=tweet): a host frames the ネタ, guests react in short takes ──
def sys_host(persona, topic, segment):
    seg = f"\nSEGMENT: {segment}" if segment else ""
    return (f"[HOST] You are {persona}, the host of a short AI-news talk show. In ONE or two lines, "
            f"frame today's item for the panel — say what it is and why it matters, then invite a "
            f"reaction. Warm, concise, no preamble.\nTOPIC: {topic}{seg}")


def sys_tweet(persona, topic, char_limit):
    return (f"[TWEET] You are {persona}, a panelist on a short AI-news show. In ≤{char_limit} "
            f"characters, post ONE first-person take on the topic — react to it and, if useful, to "
            f"what others just said. No preamble, no meta, no name prefix.\nTOPIC: {topic}")


def sys_tsukkomi(persona, char_limit):
    return (f"[TSUKKOMI] You are {persona}, the critical foil (ツッコミ) on a short AI-news show — a "
            f"DIFFERENT context from the host. In ≤{char_limit} characters, react to the host's "
            f"latest point: challenge it, question it, or quip — do NOT just agree. One line, no "
            f"name prefix.")


def sys_caster(persona, script, direction, char_limit, i, n):
    """The role-fidelity experiment: hand the LLM a SCRIPT (facts) + an ANGLE (direction) and have it
    PLAY the news-caster role — not read the script verbatim, not summarize, but perform. Ad-libbing
    is WELCOME as long as it stays within the angle; that improvisation IS what we're testing."""
    return (f"[CASTER] You are {persona}, a live news caster on air. You are handed today's SCRIPT "
            f"(what happened) and the director's ANGLE (how to play it). Do NOT read the script "
            f"verbatim and do NOT merely summarize — PERFORM. Deliver take {i} of {n}: ONE punchy "
            f"on-air line (≤{char_limit} chars) that lands the angle and moves the segment forward "
            f"(don't repeat earlier takes). Improvise freely to make it vivid and entertaining — "
            f"ad-libbing is encouraged AS LONG AS you stay within the angle. No name prefix, no meta.\n"
            f"SCRIPT: {script}\nANGLE: {direction}")


def fetch_netas(d, reader, prefix):
    """Read the ネタ帖 (演出 curations whose title starts with `prefix`) from the graph AS `reader`, and
    return the play queue. `d(client, method, data)` is the driver's dispatch closure (returns the RPC
    result). Reading is scope-filtered by `reader`: pass the host client normally, or the identity that
    OWNS the curations (e.g. `admin` for an auto-loaded ネタ帖) — reading the script never lets a cast
    speak as that identity. Returns [] when nothing is visible to `reader` (the caller can then retry)."""
    items = []
    for c in ((d(reader, "curation.ls", {}) or {}).get("curations") or []):
        if not str(c.get("title", "")).startswith(prefix):
            continue
        narr = d(reader, "curation.narrate", {"curation_id": c.get("curation_id")}) or {}
        scripts = []
        for st in narr.get("steps", []):
            r = d(reader, "read", {"id": st.get("key")}) or {}
            body = (r.get("content") or "").strip()
            if body.startswith("[") and "\n" in body:
                body = body.split("\n", 1)[1].strip()          # drop the "[alias]" hub header
            scripts.append(body or (st.get("preview") or "").strip())
        items.append({"id": c.get("curation_id"), "title": c.get("title", ""),
                      "angle": c.get("thesis", ""), "scripts": scripts})
    return neta_queue_from_curations(items)


def neta_queue_from_curations(items):
    """Build the show's ネタ queue from 演出 curations (pure, testable). Each `item` is one curation
    read back from the graph — {id, title, angle(=thesis), scripts:[台本 content …]}. 演出 IS the
    interpretation (curation.thesis); the台本 are the atoms on its path. The queue is ordered by title
    (so `<space> seg-001, seg-002, …` play in sequence) and drops any entry missing a script or angle.
    The caster is then handed (script, angle) per ネタ and ad-libs within the angle."""
    out = []
    for it in sorted(items, key=lambda x: (x.get("title", ""), x.get("id", ""))):
        script = " / ".join(s.strip() for s in (it.get("scripts") or []) if s and s.strip())
        angle = (it.get("angle") or "").strip()
        if script and angle:
            out.append({"id": it.get("id", ""), "title": it.get("title", ""),
                        "script": script, "direction": angle})
    return out


def fetch_news(url, seen):
    """Best-effort AI-news fetch (v1, driver-side): return the newest item {title, summary, url} not in
    `seen`, or None. Supports a JSON list of items or a minimal RSS/Atom feed. Keyless; honours
    HTTPS_PROXY via urllib. Never raises — a failure returns None and the burst reuses the topic."""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Akasha-Broadcast/0.1"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
    except Exception:
        return None
    items = []
    try:
        data = json.loads(raw)
        rows = data if isinstance(data, list) else (data.get("items") or data.get("entries") or [])
        for it in rows:
            t = (it.get("title") or "").strip()
            if t:
                items.append({"title": t, "summary": (it.get("summary") or it.get("description") or "").strip(),
                              "url": (it.get("url") or it.get("link") or "").strip(),
                              "id": (it.get("id") or it.get("url") or it.get("link") or t)})
    except Exception:
        import re as _re                              # minimal RSS/Atom: pull <title>/<link>
        for m in _re.finditer(r"<(?:item|entry)\b.*?</(?:item|entry)>", raw, _re.S | _re.I):
            blk = m.group(0)
            tm = _re.search(r"<title[^>]*>(.*?)</title>", blk, _re.S | _re.I)
            lm = _re.search(r"<link[^>]*>(.*?)</link>|<link[^>]*href=\"(.*?)\"", blk, _re.S | _re.I)
            t = _re.sub(r"<.*?>", "", (tm.group(1) if tm else "")).strip()
            link = ((lm.group(1) or lm.group(2)) if lm else "").strip() if lm else ""
            if t:
                items.append({"title": t, "summary": "", "url": link, "id": link or t})
    for it in items:
        if it["id"] not in seen:
            seen.add(it["id"])
            return it
    return None


def tweet_plan(per_day, burst, rounds):
    """The burst schedule (pure, testable): how many BURSTS to run and the post BUDGET. With a
    per-day budget B and K turns/burst, run ceil(B/K) bursts capped at B posts; with no budget, run
    `rounds` bursts unbounded. Returns (n_bursts, budget) where budget<=0 means unbounded."""
    import math
    K = max(1, int(burst or 1))
    B = max(0, int(per_day or 0))
    if B > 0:
        return max(1, math.ceil(B / K)), B
    return max(1, int(rounds or 1)), 0


def spread_rest(n_bursts, burst, pace, day_seconds=86400):
    """The gap between bursts when --spread is set: space the bursts EVENLY across the day so the feed
    is catchable live at many times (pure, testable). Returns seconds of rest between bursts."""
    burst_seconds = max(0, int(burst)) * max(0.0, float(pace))
    return max(0.0, (day_seconds - n_bursts * burst_seconds) / max(1, n_bursts))


def burst_schedule(n_netas, budget, takes, burst, has_panel, pace, rest, spread, forever, rounds,
                   day_seconds=86400):
    """Resolve (n_bursts, gap) for a tweet-mode run (pure, testable). Central to the public experiment:

      • posts_per_burst — a ネタ run posts `takes` caster lines (+ a panel burst if present); a news run
        posts 1 host line + a panel burst.
      • n_bursts — None = run FOREVER (loop the ネタ帖, repeating past news on ネタ切れ); else derived
        from the daily budget (ceil(budget/posts_per_burst)), which may EXCEED n_netas so the burst
        index wraps and past news repeats; else one pass of the ネタ帖 (or `rounds` for a news run).
      • gap — seconds between bursts: an explicit --rest wins; else --spread/--forever spread the
        day's budget across `day_seconds` (so the daily post count ≈ budget and the feed is catchable
        live all day); else 0 (pace-only, as fast as the per-utterance --pace allows).
    """
    import math
    panel_posts = max(1, int(burst)) if has_panel else 0
    posts_per_burst = (max(1, int(takes)) + panel_posts) if n_netas else (1 + max(1, int(burst)))
    if forever:
        n_bursts = None
    elif budget:
        n_bursts = max(1, math.ceil(budget / posts_per_burst))
    elif n_netas:
        n_bursts = n_netas
    else:
        n_bursts = max(1, int(rounds or 1))
    if rest and float(rest) > 0:
        gap = float(rest)
    elif (spread or forever) and budget:
        bursts_per_day = max(1.0, budget / posts_per_burst)
        gap = spread_rest(bursts_per_day, posts_per_burst, pace, day_seconds)
    else:
        gap = 0.0
    return n_bursts, gap


def main():
    ap = argparse.ArgumentParser(description="Multi-session society gateway (free-LLM guests) — "
                                             "brainstorm OR talk-show (tweet) mode.")
    ap.add_argument("--group", required=True)
    ap.add_argument("--space", default="main")
    ap.add_argument("--topic", default="", help="the 前提 / theme (falls back to the space's topic)")
    ap.add_argument("--mode", choices=["brainstorm", "tweet"], default="brainstorm",
                    help="brainstorm (default) or tweet (a talk show: host frames a ネタ, panel reacts)")
    ap.add_argument("--per-day", type=int, default=0, help="tweet mode: daily post BUDGET (hard cap); "
                    "0 = run --rounds bursts unbounded")
    ap.add_argument("--burst", type=int, default=4, help="tweet mode: turns per burst")
    ap.add_argument("--rest", type=float, default=0.0, help="tweet mode: seconds between bursts")
    ap.add_argument("--spread", action="store_true", help="tweet mode: auto-space bursts evenly across "
                    "the day (overrides --rest) so the feed is catchable live at many times")
    ap.add_argument("--char-limit", type=int, default=240, help="tweet mode: max chars per post")
    ap.add_argument("--news-source", default="", help="tweet mode: a keyless AI-news RSS/JSON URL; each "
                    "burst uses the newest unseen item as the ネタ (the ✉️ show)")
    ap.add_argument("--neta-prefix", default="", help="tweet mode: play 演出 curations whose title "
                    "starts with this prefix (default: the space name) as the ネタ帖 — each curation is a "
                    "segment (thesis=演出 over 台本 atoms). One ネタ per burst; the caster ad-libs --takes "
                    "lines from (台本+演出). Authored as .ak(台本)+.csl(curation.new) — see "
                    "app/scripts/society_neta_example.ak / .csl. Takes precedence over --news-source.")
    ap.add_argument("--takes", type=int, default=6, help="tweet mode + --neta-prefix: how many short "
                    "caster lines (5–10) the host ad-libs per ネタ")
    ap.add_argument("--neta-reader", default="", help="tweet mode: the identity to READ the ネタ帖 as "
                    "(default: the host client; falls back to admin automatically). Set it to whatever "
                    "OWNS an auto-loaded ネタ帖 — reading the script never lets a cast speak as it.")
    ap.add_argument("--forever", action="store_true", help="tweet mode: run CONTINUOUSLY (the public "
                    "experiment) — loop the ネタ帖 endlessly, repeating past news on ネタ切れ, pacing bursts "
                    "to --per-day across the day. Ctrl-C to stop. (Without it: one bounded run.)")
    ap.add_argument("--gemini-paid", action="store_true", help="assert Gemini guests are the PAID tier "
                    "(free Gemini is refused for a PUBLIC space — EEA/CH/UK geo policy)")
    ap.add_argument("--rounds", type=int, default=2, help="diverge rounds (brainstorm) / bursts when "
                    "tweet mode has no --per-day")
    ap.add_argument("--pace", type=float, default=0.0,
                    help="seconds between utterances (bot-only rooms): a readable public cadence "
                         "that also spaces provider calls to respect free-tier rate limits. 0 = as "
                         "fast as possible.")
    ap.add_argument("--guest", action="append", default=[],
                    help="client|cast_id|provider|model|role  (repeatable; role=participant|facilitator)")
    ap.add_argument("--base", default=None, help="daemon data dir (default AKASHA_DATA_DIR or ./data)")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print(f"[!] No Cell daemon at {base}. Start one:  python akasha.py --serve", file=sys.stderr)
        sys.exit(2)
    gw = client.connect(base)

    def d(tok, method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok, "data": data}, "id": "g"}, "local")
        return r.get("result") if isinstance(r, dict) else None

    guests = []
    for g in args.guest:
        f = [x.strip() for x in g.split("|")]
        if len(f) < 3 or not f[0] or not f[1]:
            print(f"[!] bad --guest '{g}' (want client|cast_id|provider|model|role)", file=sys.stderr)
            sys.exit(2)
        guests.append({"client": f[0], "cast": f[1], "provider": f[2] if len(f) > 2 else "mock",
                       "model": (f[3] if len(f) > 3 else "") or "",
                       "role": (f[4] if len(f) > 4 else "participant") or "participant",
                       "persona": ""})
    if not guests:
        print("[!] no --guest given.", file=sys.stderr)
        sys.exit(2)
    for g in guests:
        if g["provider"] not in PROVIDERS:
            print(f"[!] unknown provider '{g['provider']}' (have {', '.join(PROVIDERS)})", file=sys.stderr)
            sys.exit(2)

    # ── the outbound gate: refuse a space that is not open_guest ──
    info = d(guests[0]["client"], "society.info", {"group": args.group, "space": args.space}) or {}
    if not info.get("open_guest"):
        print(f"[!] REFUSED: '{args.group}/{args.space}' is not open_guest. External-LLM guests may "
              f"only join a space explicitly opened (society.new open_guest=yes / society.guest "
              f"open=yes). This gate stops a private feed leaving to a free external tier.",
              file=sys.stderr)
        sys.exit(3)
    topic = args.topic or info.get("topic") or args.space

    # ── PUBLIC geo policy: free Gemini may not serve EEA/CH/UK; a public page is global → refuse ──
    if info.get("public"):
        bad = [g for g in guests if g["provider"] == "gemini" and not args.gemini_paid]
        if bad:
            print(f"[!] REFUSED: '{args.group}/{args.space}' is PUBLIC and a guest uses FREE Gemini "
                  f"({', '.join(b['cast'] for b in bad)}). Google's free tier may not serve EEA/CH/UK, "
                  f"but a public archives page is global. Use OpenRouter :free, local Ollama, or paid "
                  f"Gemini (--gemini-paid).", file=sys.stderr)
            sys.exit(4)

    facil = next((g for g in guests if g["role"] == "facilitator"), None)
    parts = [g for g in guests if g["role"] != "facilitator"]
    if not parts:
        print("[!] need at least one participant guest.", file=sys.stderr)
        sys.exit(2)

    # join each guest's avatar; resolve its display persona from the OWNER's own cast list
    # (the roster resolves names from feed history, which is empty at the start of a session).
    for g in guests:
        d(g["client"], "society.join", {"group": args.group, "space": args.space, "cast": g["cast"]})
        my_casts = (d(g["client"], "cast.ls", {}) or {}).get("casts", [])
        g["persona"] = next((c.get("name") for c in my_casts if c.get("cast_id") == g["cast"]), g["client"])

    def gen(g, system):
        return PROVIDERS[g["provider"]](g["model"], system, transcript_of(feed()))

    def feed():
        return (d(guests[0]["client"], "society.feed",
                  {"group": args.group, "space": args.space, "limit": 50}) or {}).get("messages", [])

    def say(g, text):
        if not text:
            return
        # stamp AI provenance so a public broadcast can show the required disclosure + attribution
        d(g["client"], "society.say", {"group": args.group, "space": args.space, "cast": g["cast"],
                                       "text": text, "agent": "ai", "provider": g["provider"],
                                       "model": g["model"]})
        print(f"  {g['persona']:14} │ {text}")

    turn_no = [0]

    def turn(g, system):
        # pace between utterances (bot-only rooms): readable public cadence + rate-limit spacing.
        if turn_no[0] and args.pace > 0:
            time.sleep(args.pace)
        turn_no[0] += 1
        # degradation-first: a provider error (missing key, rate limit, network) skips that guest's
        # turn and the brainstorm continues — one voice failing never aborts the room.
        try:
            say(g, gen(g, system))
        except Exception as e:
            print(f"  [skip] {g['persona']} ({g['provider']}): {e}", file=sys.stderr)

    # ── tweet mode: a talk show — a caster performs a ネタ (script+angle), a ツッコミ reacts ──
    if args.mode == "tweet":
        host = next((g for g in guests if g["role"] in ("host", "facilitator")), None)
        real_panel = [g for g in guests if g is not host]      # a distinct panel (e.g. the ツッコミ)
        panel = real_panel or [host]                            # one-man show: the host is the only voice
        # ネタ帖 = 演出 curations (interpretation over 台本), read from the graph.
        netas = []
        if args.neta_prefix:
            prefix = args.neta_prefix
            primary = args.neta_reader or (host or guests[0])["client"]
            netas = fetch_netas(d, primary, prefix)
            # Fallback: an AUTO-LOADED ネタ帖 is often owned by `admin` (the boot app/curations/ phase runs
            # CSL as admin → its curations are scope-filtered OUT of the host client's curation.ls). The
            # caster then sees zero ネタ. Over local trust the driver may READ the ネタ帖 as admin while
            # the casts still SPEAK as themselves — reading ≠ speaking, no privilege is granted to a cast.
            if not netas and not args.neta_reader and primary != "admin":
                alt = fetch_netas(d, "admin", prefix)
                if alt:
                    print("  (ネタ帖 read as admin — auto-loaded curations are admin-owned; casters "
                          "still speak as themselves)")
                    netas = alt
            if not netas:
                print(f"[!] --neta-prefix '{prefix}': no 演出 curations visible for {args.group}/{args.space} "
                      f"(read as {primary}). If the ネタ帖 was auto-loaded under another identity, pass "
                      f"--neta-reader <that client>. See app/scripts/society_neta_example.ak / .csl.", file=sys.stderr)
                sys.exit(2)
        segments = info.get("segments") or ([topic] if topic else ["the news"])
        _, budget = tweet_plan(args.per_day, args.burst, args.rounds)   # budget = daily post cap (0 = none)
        n_bursts, gap = burst_schedule(len(netas), budget, args.takes, args.burst,
                                       bool(real_panel), args.pace, args.rest,
                                       args.spread, args.forever, args.rounds)
        hard_budget = 0 if args.forever else budget    # forever paces by gap; it never stops on budget
        seen = set()
        posted = 0
        loop_note = "∞ loop (ネタ切れ→過去を繰り返す)" if args.forever else f"{n_bursts} burst(s)"
        mode_tag = f"ネタ帖 {len(netas)} 本 × {args.takes} takes" if netas else f"panel={len(panel)}"
        print(f"\n  ✉️  {topic}   ({args.group}/{args.space}, host={host['persona'] if host else '—'}, "
              f"{mode_tag}, budget={budget or '∞'}/day, {loop_note}, gap={gap:.0f}s)\n  " + "-" * 68)
        b = 0
        try:
            while n_bursts is None or b < n_bursts:
                if hard_budget and posted >= hard_budget:
                    break
                if netas:
                    # role-fidelity run: the caster is handed (script, angle) and ad-libs --takes lines.
                    neta = netas[b % len(netas)]
                    if b and netas and b % len(netas) == 0:
                        print(f"  ↻ ネタ一巡 — 過去ニュースを繰り返します (loop {b // len(netas) + 1})")
                    print(f"  ── ネタ {neta['id']}: {neta['script'][:56]}")
                    if neta["direction"]:
                        print(f"     演出: {neta['direction'][:56]}")
                    for t in range(max(1, args.takes)):
                        if hard_budget and posted >= hard_budget:
                            break
                        turn(host, sys_caster(host["persona"], neta["script"], neta["direction"],
                                              args.char_limit, t + 1, args.takes)); posted += 1
                    # 2nd stage: a distinct ツッコミ/panel reacts to the caster (skipped in a one-man show)
                    for i in range(len(real_panel) and max(1, args.burst)):
                        if hard_budget and posted >= hard_budget:
                            break
                        g = real_panel[i % len(real_panel)]
                        system = (sys_tsukkomi(g["persona"], args.char_limit) if g["role"] == "tsukkomi"
                                  else sys_tweet(g["persona"], topic, args.char_limit))
                        turn(g, system); posted += 1
                else:
                    # news / segment run: the host frames a ネタ, the panel reacts in short takes.
                    item = fetch_news(args.news_source, seen) if args.news_source else None
                    segment = item["title"] if item else segments[b % len(segments)]
                    if item and item.get("url"):
                        print(f"  ── news: {segment[:64]}  <{item['url']}>")
                    if host and not (hard_budget and posted >= hard_budget):
                        turn(host, sys_host(host["persona"], topic, segment)); posted += 1
                    for i in range(max(1, args.burst)):
                        if hard_budget and posted >= hard_budget:
                            break
                        g = panel[i % len(panel)]
                        system = (sys_tsukkomi(g["persona"], args.char_limit) if g["role"] == "tsukkomi"
                                  else sys_tweet(g["persona"], topic, args.char_limit))
                        turn(g, system); posted += 1
                b += 1
                more = (n_bursts is None or b < n_bursts) and not (hard_budget and posted >= hard_budget)
                if gap > 0 and more:
                    print(f"  … rest {gap:.0f}s")
                    time.sleep(gap)
        except KeyboardInterrupt:
            print("\n  (interrupted)")
        print("  " + "-" * 68)
        print(f"  {'Stopped' if args.forever else 'Done'}. {posted} post(s). "
              f"Live: society.broadcast.live / the archives station.\n")
        gw.close()
        return

    print(f"\n  Brainstorm on: {topic}   ({args.group}/{args.space}, {len(parts)} participant(s)"
          f"{', facilitated' if facil else ''})\n  " + "-" * 68)

    # open
    if facil:
        turn(facil, sys_open(topic, facil["persona"]))
    # diverge × N
    for _ in range(max(1, args.rounds)):
        for g in parts:
            turn(g, sys_diverge(g["persona"]))
    # additive synth (facilitator, or the first participant if none)
    turn(facil or parts[0], sys_synth((facil or parts[0])["persona"]))

    print("  " + "-" * 68)
    print(f"  Done. Harvest: read the feed (society.feed group={args.group} space={args.space}) "
          f"and confirm the ideas worth keeping into ontology (.ak).\n")
    gw.close()


if __name__ == "__main__":
    main()
