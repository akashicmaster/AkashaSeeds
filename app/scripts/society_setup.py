#!/usr/bin/env python3
"""
society_setup.py — provision a group + avatars for the avatar-mediated chat experiment.

Sets up, against a RUNNING Cell daemon (over the local TRUST_LOCAL socket), everything the
Ollama society-chat needs so the driver has nothing to configure but "speak / read":

  • a group (default `salon`),
  • one Akasha client + one published avatar per participant,
  • prints each avatar's cast_id and a ready-to-paste driver command.

Each avatar is created AS its owning client (only the owner may speak as it), then published
into the group so the others see it. Idempotent: re-running reuses existing users/avatars.

Start the daemon first:   python akasha.py --serve        (or it will be attached to if up)
Then:                     python app/scripts/society_setup.py
Two-bot salon:            python app/scripts/society_setup.py --participant "mcp:sage|Sage|a thoughtful host" \
                                                          --participant "mcp:echo|Echo|a curious visitor"

Default (no --participant): one human-driven avatar (client `human`, avatar `Sage`) and one
bot avatar (client from $AKASHA_MCP_CLIENT or `mcp:local`, avatar `Echo`).
"""
import argparse
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)


def _parse_neta_ak(path):
    """台本 (.ak): return (defs=[(name, description)], sets=[(setname, atom_id)]) in file order.
    Reads only def / set.add; ignores comments + blanks; skips a malformed line rather than raising."""
    import re
    import shlex
    defs, sets = [], []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("def "):
                try:
                    parts = shlex.split(line)
                except ValueError:
                    continue
                if len(parts) >= 3:
                    defs.append((parts[1], parts[2]))
            elif line.startswith("set.add"):
                nm = re.search(r'name="([^"]+)"', line) or re.search(r"name=(\S+)", line)
                idm = re.search(r'id="([^"]+)"', line) or re.search(r"id=(\S+)", line)
                if nm and idm:
                    sets.append((nm.group(1), idm.group(1)))
    return defs, sets


def _parse_neta_csl(path):
    """演出 (.csl): return the curation.new blocks as [{title, thesis, mode, ids, alias, …}] in order.
    A block begins at a line mentioning `curation.new` and collects the indented `key = "value"` lines
    until the next block. Only curation.new keys are kept; the unused `$var =` capture is ignored."""
    keys = {"title", "thesis", "mode", "ids", "alias", "set", "rels", "op"}
    blocks, cur = [], None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            if "curation.new" in s:
                if cur:
                    blocks.append(cur)
                cur = {}
                continue
            if cur is not None and "=" in s:
                key, _, val = s.partition("=")
                key = key.strip()
                if key in keys:
                    cur[key] = val.strip().strip('"')
    if cur:
        blocks.append(cur)
    return [b for b in blocks if b.get("title") or b.get("alias")]


def _load_neta(d, client, ak_path, csl_path):
    """Load a ネタ帖 into the graph AS `client` (the host) so its caster can read it: 台本 first (define
    + set.add), then 演出 curations (curation.new, which resolves ids= against the just-loaded 台本).
    Returns (n_scripts, n_curations_made). Idempotent — content-addressed defs and aliased curations."""
    defs, sets = _parse_neta_ak(ak_path)
    for name, desc in defs:
        d(client, "define", {"name": name, "description": desc})
    for setname, atom in sets:
        d(client, "set.add", {"name": setname, "id": atom})
    made = 0
    for b in _parse_neta_csl(csl_path):
        r = d(client, "curation.new", b).get("result") or {}
        if r.get("status") in ("created", "exists"):
            made += 1
    return len(defs), made


def station_preset(d, args):
    """Provision the 放送局 (station): studios (groups) each carrying a public talk SHOW (space).

    For each studio it: creates the group, adds `system.broadcaster` as a member (so the relay
    daemon may mirror the public feed into the nucleus), registers a host client + a ツッコミ client,
    creates the public+open_guest show (with category / daily_budget / news segments), publishes the
    host + ツッコミ casts into it, and prints the ready-to-run tweet-mode gateway command. Idempotent.
    """
    BROADCASTER = "system.broadcaster"
    studios = args.studio or ["technology|studio_ai|mail_show|AI technology news|12"]

    def au(client):
        d("admin", "user.add", {"client_id": client, "role": "user",
                                "passphrase_hash": hashlib.sha256(client.encode()).hexdigest()})

    def cast_for(client, name, identity):
        """Reuse an existing avatar of this name, else create one — AS the owning client."""
        for c in (d(client, "cast.ls", {}).get("result") or {}).get("casts", []):
            if c.get("name") == name:
                d(client, "cast.open", {"id": c.get("cast_id")})
                return c.get("cast_id")
        return (d(client, "cast.new", {"name": name, "identity": identity}).get("result") or {}).get("cast_id")

    print(f"\n  Akasha 放送局 (station) — {len(studios)} studio(s), provider={args.provider}\n  " + "=" * 66)
    driver_cmds = []
    for idx, spec in enumerate(studios):
        f = [x.strip() for x in spec.split("|")]
        if len(f) < 4 or not f[1] or not f[2]:
            print(f"[!] bad --studio '{spec}' (want category|group|space|topic[|daily_budget])", file=sys.stderr)
            sys.exit(2)
        category, gid, space, topic = f[0], f[1], f[2], f[3]
        budget = int(f[4]) if len(f) > 4 and f[4] else args.daily_budget

        d("admin", "grp.new", {"group_id": gid, "admin_id": "admin"})
        d("admin", "grp.add", {"group_id": gid, "member_id": BROADCASTER})   # the relay mirrors as this member

        host_client = f"llm:host:{gid}"
        tsu_client = f"llm:tsukkomi:{gid}"
        au(host_client)
        au(tsu_client)
        d("admin", "grp.add", {"group_id": gid, "member_id": host_client})
        d("admin", "grp.add", {"group_id": gid, "member_id": tsu_client})

        # the host client creates + owns the show; open it to guests AND to public broadcast.
        d(host_client, "society.new", {"group": gid, "space": space, "topic": topic,
                                       "category": category, "daily_budget": budget,
                                       "open_guest": "yes", "public": "yes"})
        d(host_client, "society.guest", {"group": gid, "space": space, "open": "yes"})
        d(host_client, "society.public", {"group": gid, "space": space, "open": "yes"})

        host_cast = cast_for(host_client, "Anchor", f"the host of the {category} show")
        tsu_cast = cast_for(tsu_client, "Skeptic", "a ツッコミ challenging the host from a different angle")
        d(host_client, "cast.publish", {"group": gid})
        d(tsu_client, "cast.publish", {"group": gid})
        d(host_client, "society.join", {"group": gid, "space": space, "cast": host_cast})
        d(tsu_client, "society.join", {"group": gid, "space": space, "cast": tsu_cast})

        ok = bool(host_cast) and bool(tsu_cast)
        print(f"  {category:11} {gid}/{space:10} budget={budget:<4} "
              f"host={host_cast} tsukkomi={tsu_cast}  {'ok' if ok else 'FAILED'}")

        # 一気通貫: load a ネタ帖 (台本.ak + 演出.csl) into THIS studio's host so the caster can read it.
        neta_loaded = False
        if idx == 0 and args.neta_ak and args.neta_csl:
            try:
                n_scripts, n_curs = _load_neta(d, host_client, args.neta_ak, args.neta_csl)
                neta_loaded = n_curs > 0
                print(f"    ネタ帖 loaded as {host_client}: {n_scripts} 台本(script), {n_curs} 演出(curation)"
                      f"  {'ok' if neta_loaded else 'NO 演出 — check --neta-csl'}")
            except OSError as e:
                print(f"    [!] ネタ帖 load failed: {e}", file=sys.stderr)

        cmd = ["    python app/scripts/society_gateway.py --mode tweet \\",
               f"        --group {gid} --space {space} --per-day {budget} --pace 10 \\"]
        if neta_loaded:
            # public experiment: run continuously, looping the ネタ帖 (repeats past news on ネタ切れ)
            cmd.append(f"        --neta-prefix \"{space} seg-\" --takes {args.takes} --forever \\")
        elif args.news_source:
            cmd.append(f"        --burst 4 --news-source \"{args.news_source}\" \\")
        else:
            cmd.append("        --burst 4 \\")
        cmd.append(f"        --guest \"{host_client}|{host_cast}|{args.provider}|{args.model}|host\" \\")
        cmd.append(f"        --guest \"{tsu_client}|{tsu_cast}|{args.provider}|{args.model}|tsukkomi\"")
        driver_cmds.append("\n".join(cmd))

    print("  " + "=" * 66)
    key_env = {"openrouter": "AKASHA_OPENROUTER_KEY", "gemini": "AKASHA_GEMINI_KEY"}.get(args.provider)
    if key_env:
        print(f"\n  Provider key (put it in the environment, never an atom):  export {key_env}=…")
    print("\n  Run a show (host frames a ネタ, ツッコミ retorts, in burst cadence):")
    for cmd in driver_cmds:
        print(cmd)
        print()
    if not (args.neta_ak and args.neta_csl):
        print("  Role-fidelity run (the caster PERFORMS 演出 curations — 台本 + 解釈 → ad-lib takes):")
        print("      演出=解釈=curationの構造。台本を .ak、演出を curation.new (.csl) で書き、一気通貫で流し込む:")
        print("        python app/scripts/society_setup.py --station \\")
        print("            --neta-ak app/scripts/society_neta_example.ak \\")
        print("            --neta-csl app/scripts/society_neta_example.csl")
        print("      → 第1スタジオの host client に台本+演出を読み込み、上のコマンドが --neta-prefix 付きで出ます。")
        print("        Add a ツッコミ guest (role=tsukkomi) for the 2nd stage.\n")
    print("  Restart the daemon with the relay ON so the public feed reaches the archives page:")
      python akasha.py --serve
    print("  Then the guest-safe live view + program guide (no group membership needed):")
    print("      akasha> society.station")
    print("      akasha> society.broadcast.live society=studio_ai/mail_show")
    print("  Mock (no keys) — swap each guest's provider to `mock`:  …|mock|-|host  …|mock|-|tsukkomi\n")


def main():
    ap = argparse.ArgumentParser(description="Provision a group + avatars for society chat.")
    ap.add_argument("--group", default="salon")
    ap.add_argument("--space", default="main", help="dialogue space (channel) name in the group")
    ap.add_argument("--topic", default="", help="topic for the space")
    ap.add_argument("--base", default=None, help="daemon data dir (default: AKASHA_DATA_DIR or ./data)")
    ap.add_argument("--participant", action="append", default=[],
                    help="client|avatar_name|identity[|role]  (repeatable, '|'-delimited since "
                         "client ids may contain ':'). role = participant|facilitator (for the "
                         "brainstorm gateway). Overrides the defaults.")
    ap.add_argument("--open-guest", action="store_true",
                    help="open the space to external-LLM guests (society.guest open=yes) — the "
                         "outbound consent that this feed may leave to a free external tier.")
    ap.add_argument("--public", action="store_true",
                    help="open the space to PUBLIC broadcast (society.public open=yes) — consent to "
                         "show this feed on the public web (archives live view). A public curation "
                         "meeting sets both --open-guest and --public.")
    # ── station preset (放送局): provision studios + ✉️ talk shows for the tweet-mode gateway ──
    ap.add_argument("--station", action="store_true",
                    help="STATION PRESET: provision one or more studios (groups) each carrying a "
                         "public talk SHOW (space), with a host + ツッコミ cast, system.broadcaster as "
                         "a member (so the relay can mirror), and print the tweet-mode driver command.")
    ap.add_argument("--studio", action="append", default=[],
                    help="station mode: category|group|space|topic[|daily_budget]  (repeatable). "
                         "Default: technology|studio_ai|mail_show|AI technology news|12 (the ✉️ show).")
    ap.add_argument("--provider", default="openrouter",
                    help="station mode: LLM provider for the printed driver command (default openrouter).")
    ap.add_argument("--model", default="meta-llama/llama-3.3-70b-instruct:free",
                    help="station mode: model id for the printed driver command (default a :free model).")
    ap.add_argument("--daily-budget", type=int, default=12,
                    help="station mode: default daily post budget when a --studio omits it.")
    ap.add_argument("--news-source", default="",
                    help="station mode: keyless AI-news RSS/JSON URL for the ✉️ show (each burst uses "
                         "the newest unseen item as the ネタ); printed into the driver command.")
    ap.add_argument("--neta-ak", default="",
                    help="station mode: 台本 .ak to load into the FIRST studio's host client (一気通貫). "
                         "Pair with --neta-csl. Default example: app/scripts/society_neta_example.ak")
    ap.add_argument("--neta-csl", default="",
                    help="station mode: 演出 .csl (curation.new) to load into the FIRST studio's host "
                         "client. Requires --neta-ak. Default example: app/scripts/society_neta_example.csl")
    ap.add_argument("--takes", type=int, default=6,
                    help="station mode: caster ad-lib lines per ネタ (printed into the --neta-prefix cmd).")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print(f"[!] No Cell daemon at {base}. Start one:  python akasha.py --serve", file=sys.stderr)
        sys.exit(2)
    gw = client.connect(base)

    def d(tok, method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok, "data": data}, "id": "s"}, "local")
        return r

    if args.station:
        station_preset(d, args)
        gw.close()
        return

    bot_client = os.environ.get("AKASHA_MCP_CLIENT", "mcp:local")
    parts = args.participant or [
        "human|Sage|a thoughtful salon host",
        f"{bot_client}|Echo|a curious visiting mind",
    ]
    parsed = []
    for p in parts:
        fields = [f.strip() for f in p.split("|")]
        client = fields[0] if fields else ""
        name = fields[1] if len(fields) > 1 else ""
        identity = fields[2] if len(fields) > 2 else ""
        role = (fields[3] if len(fields) > 3 else "participant") or "participant"
        if not client or not name:
            print(f"[!] bad --participant '{p}' (want client|avatar_name|identity[|role])", file=sys.stderr)
            sys.exit(2)
        parsed.append((client, name, identity or name, role))

    gid = args.group
    space = args.space
    d("admin", "grp.new", {"group_id": gid, "admin_id": "admin"})   # idempotent if exists

    print(f"\n  Group: {gid}   Space: {space}"
          f"{'   (open_guest)' if args.open_guest else ''}"
          f"{'   (public)' if args.public else ''}\n  " + "-" * 60)
    results = []
    space_made = False
    for client, name, identity, role in parsed:
        # ensure the user exists (deterministic passphrase = its own id; local trust anyway)
        d("admin", "user.add", {"client_id": client, "role": "user",
                                "passphrase_hash": hashlib.sha256(client.encode()).hexdigest()})
        d("admin", "grp.add", {"group_id": gid, "member_id": client})
        # the first member creates the dialogue space (idempotent) + opens it to guests if asked
        if not space_made:
            d(client, "society.new", {"group": gid, "space": space, "topic": args.topic,
                                      "open_guest": "yes" if args.open_guest else "",
                                      "public": "yes" if args.public else ""})
            if args.open_guest:
                d(client, "society.guest", {"group": gid, "space": space, "open": "yes"})
            if args.public:
                d(client, "society.public", {"group": gid, "space": space, "open": "yes"})
            space_made = True
        # reuse an existing avatar of this name, else create one — AS the owning client
        existing = None
        for c in (d(client, "cast.ls", {}).get("result") or {}).get("casts", []):
            if c.get("name") == name:
                existing = c.get("cast_id")
                break
        if existing:
            cast_id = existing
            d(client, "cast.open", {"id": cast_id})
        else:
            cast_id = (d(client, "cast.new", {"name": name, "identity": identity})
                       .get("result") or {}).get("cast_id")
        d(client, "cast.publish", {"group": gid})               # persona copy (others can inspect)
        join = d(client, "society.join", {"group": gid, "space": space, "cast": cast_id})
        ok = bool(cast_id) and "error" not in join
        results.append((client, name, cast_id, ok, role))
        print(f"  {name:10} owner={client:14} role={role:11} cast_id={cast_id}  {'ok' if ok else 'FAILED'}")

    print("  " + "-" * 60)
    if args.open_guest:
        print("\n  Run the brainstorm gateway (mock provider — no keys needed):")
        print("    python app/scripts/society_gateway.py \\")
        pace = "  --pace 6" if args.public else ""     # readable + rate-safe cadence when broadcast
        print(f"        --group {gid} --space {space} --rounds 2{pace} \\")
        for client, name, cast_id, ok, role in results:
            if ok:
                print(f"        --guest \"{client}|{cast_id}|mock|-|{role}\" \\")
        print("    # swap a guest's provider to gemini/openrouter (with its API key in env) for a real run.")
    else:
        print("\n  Drive a bot avatar (deterministic Ollama loop):")
        for client, name, cast_id, ok, role in results:
            if not ok:
                continue
            print(f"    AKASHA_MCP_CLIENT={client} python scripts/ollama_society_chat.py \\")
            print(f"        --group {gid} --space {space} --cast {cast_id} --model llama3 \\")
            print(f"        --persona \"You are {name}. Speak in the first person.\"")
        print("    # bot↔bot with no human? add --pace 4 to each for a readable, paced tempo.")
    print("\n  A human can join from the CLI:")
    if results:
        c0, n0, id0, _, _ = results[0]
        print(f"    python akasha.py         # then, as {c0}:")
        print(f"    akasha> society.feed group={gid} space={space}")
        print(f"    akasha> society.say cast={id0} group={gid} space={space} text=\"hello\"")
    print()
    gw.close()


if __name__ == "__main__":
    main()
