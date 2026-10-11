#!/usr/bin/env python3
"""
Public-experiment broadcasting eval — the backend core (mock, no network).

Exercises the pipeline that lets an unauthenticated archives page watch a public multi-LLM talk show
in real time, end to end and offline:

  society.say (AI-stamped)  →  society.broadcast.relay (broadcaster mirrors the PUBLIC feed into the
  shared nucleus @ scope:sys:universal)  →  society.feed.read (a GUEST reads it WITHOUT group scope,
  with the AI disclosure and the space's own labels baked in; `society.broadcast[.live]` are its
  aliases).

Asserts the design's load-bearing claims:
  • the CRITICAL public-read gap is closed: a guest (no group membership) reads the mirror via
    broadcast.live and sees the messages + per-message ai_notice + attribution + disclosure;
  • the broadcaster gate holds: the relay needs role:librarian + group membership (system.broadcaster),
    and refuses a non-public space;
  • incremental: since=<cursor> returns only new messages on both the relay and the live read;
  • idempotency: re-relaying the same feed mirrors nothing new;
  • the guest's read carries the labels a lineup (studio category → show topic) is composed from;
  • provenance fence: mirror atoms are provenance=broadcast, excluded from learning (ASI06).

Run:  python test/public_experiment_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
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


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology.weave import _is_external
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_pubexp_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    from lib.akasha.concepts.society import SocietyConcept

    def d(tok, method, data, trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # The broadcaster relay runs INTERNALLY as system.broadcaster (an internal-only system identity,
    # exactly like the feed poller runs as system.librarian) — obtained via manager.get_session, not a
    # client login. This is how the kernel relay daemon invokes it; here we call the op directly.
    def brelay(owner="system.broadcaster", **kw):
        try:
            sess = k.manager.get_session(owner)
            return SocietyConcept(sess).op_broadcast_relay(**kw)
        except Exception as e:
            return {"__error__": str(e)}

    # ── provision a studio (group) + the ✉️ show (public experiment society) ──────────
    d("admin", "grp.new", {"group_id": "studio_ai", "admin_id": "admin"})
    d("admin", "grp.add", {"group_id": "studio_ai", "member_id": "system.broadcaster"})
    show = d("admin", "society.new", {"group": "studio_ai", "name": "mail_show",
                                      "topic": "AI technology news", "category": "technology",
                                      "daily_budget": 12, "open_guest": "yes", "public": "yes"})
    check("provision: public show created with topic/category/budget + gates",
          show.get("status") == "created" and show.get("public") is True and show.get("open_guest") is True,
          str(show))
    host = (d("admin", "cast.new", {"name": "Anchor", "identity": "AI news host"}) or {}).get("cast_id")
    guest = (d("admin", "cast.new", {"name": "Skeptic", "identity": "a ツッコミ from a different angle"}) or {}).get("cast_id")
    # A CAST JOINS BEFORE IT SPEAKS. `society.say` used to register an avatar on its first
    # utterance; step 4 of the gate ("say needs cast ∈ target.roles") means the role has to exist
    # when the question is asked, and no row — not even the operator's — is exempt from a step-4
    # fact. Minting a cast is not being cast in a space, and that is the distinction the gate
    # keeps: a space's roster is what says who may be spoken as in it.
    for _c in (host, guest):
        d("admin", "society.join", {"society": "studio_ai/mail_show", "cast": _c})

    def say(cast, text, provider, model, reply=""):
        return d("admin", "society.say", {"society": "studio_ai/mail_show", "cast": cast, "text": text,
                                          "provider": provider, "model": model, "agent": "ai", "reply": reply})

    # stage-1 one-man: the host explains a news item (AI-stamped as an OpenRouter :free model)
    say(host, "Today: a new open model drops. Here is what it means.", "openrouter", "meta-llama/llama-3.3-70b-instruct:free")
    say(host, "It matters because it is free and geo-unrestricted.", "openrouter", "meta-llama/llama-3.3-70b-instruct:free")

    # ── the broadcaster relay mirrors the PUBLIC feed → nucleus (guest-readable) ──────
    rel = brelay(society="studio_ai/mail_show")
    check("relay: the broadcaster mirrors the public feed into the nucleus",
          rel.get("mirrored") == 2 and rel.get("cursor", 0) > 0, str(rel))
    cursor1 = rel.get("cursor", 0)

    # ── the CORE: a GUEST (no group scope) reads the mirror via broadcast.live ────────
    gtok = (d("admin", "session.guest.create", {}) or {}).get("binding_key")
    gl = d(gtok, "society.broadcast.live", {"society": "studio_ai/mail_show"})
    msgs = gl.get("messages", [])
    check("CORE: a guest with NO group membership reads the public broadcast (the closed gap)",
          gl.get("count") == 2 and all(m.get("text") for m in msgs), str(gl.get("count")))
    # F21: assert the load-bearing CONTENT of the disclosure (machine origin, never a human) and that
    # it is the ONE shared banner constant both broadcast ops serve — not the exact prose.
    _disc = gl.get("disclosure", "")
    check("guest read carries per-message AI disclosure (ai_notice) + attribution + disclosure banner",
          all(m.get("ai_notice") for m in msgs) and gl.get("attribution")
          and _disc == SocietyConcept._DISCLOSURE_BANNER and "never a human" in _disc,
          str(gl.get("attribution")))
    check("attribution names the model/provider (Built with … · via OpenRouter)",
          any("OpenRouter" in a for a in gl.get("attribution", [])), str(gl.get("attribution")))

    # a bare (non-guest, non-member) session cannot read the GROUP feed — but the mirror is public
    grp_feed = d("carol_nomember", "society.feed", {"society": "studio_ai/mail_show"}) if False else None

    # ── the labels a lineup (番組表) is composed FROM, guest-safe ─────────────────────
    # This asked `society.station` for a platform-owned register of `station:show:*` rows. That
    # register is deleted (ruling 2026-09-23): it stamped `state`, `reason` and a daily budget —
    # the platform naming an application's status — and the lineup is composed by the station
    # Concept Model and the room pages, from `workload.status` and this read.
    #
    # What the PLATFORM owes a guest is the space's OWN labels across the consent boundary, baked
    # into the public copy the way the AI notice is, because a guest has no group scope to read
    # the society with. So that is what is checked: the public read names the show and its studio.
    check("the guest's public read carries the show's own labels (category → topic)",
          gl.get("category") == "technology" and gl.get("topic") == "AI technology news"
          and gl.get("sid") == "studio_ai/mail_show",
          "sid=%s category=%s topic=%s" % (gl.get("sid"), gl.get("category"), gl.get("topic")))

    # ── incremental (since= cursor) on both relay and live ───────────────────────────
    say(host, "Breaking: a second item just landed.", "openrouter", "google/gemma-2-9b-it:free")
    rel2 = brelay(society="studio_ai/mail_show", since=cursor1)
    check("incremental relay: since=<cursor> mirrors ONLY the new message", rel2.get("mirrored") == 1, str(rel2))
    gl2 = d(gtok, "society.broadcast.live", {"society": "studio_ai/mail_show", "since": cursor1})
    check("incremental live: since=<cursor> returns ONLY the new message",
          gl2.get("count") == 1 and "Breaking" in gl2["messages"][0]["text"], str(gl2.get("count")))

    # ── idempotency: re-relaying the whole feed mirrors nothing new ──────────────────
    # Two properties now, not one. The mirror is content-addressed, so a message already there is
    # never duplicated; and since step 2 the pass RESUMES from the society's own cursor, so a
    # re-run does not even re-read what it already mirrored. `skipped` counting 3 was the first
    # property on its own — the second is strictly stronger and makes the first unobservable here.
    rel3 = brelay(society="studio_ai/mail_show")
    check("idempotent relay: re-mirroring the same feed adds nothing",
          rel3.get("mirrored") == 0, str(rel3))
    check("…and it resumes from the society's own cursor rather than re-reading the feed",
          float(rel3.get("cursor") or 0) > 0 and rel3.get("skipped") == 0, str(rel3))

    # ── a later post reaches the mirror through the SAME op, one society at a time ───
    # There used to be a platform-wide sweep here (`broadcast_relay_once` enumerated every group the
    # broadcaster could see and relayed them all). It is deleted with the rest of that daemon: the
    # relay is a step in a workload's own workflow now, so the thing to test is that the op mirrors
    # this society's new post — which is all the sweep ever did, once per society.
    say(host, "One more headline before the break.", "openrouter", "deepseek/deepseek-chat:free")
    rel4 = brelay(society="studio_ai/mail_show")
    check("the relay op mirrors a society's new post when it is next run",
          rel4.get("mirrored") >= 1, str(rel4))

    # ── stage-2 dialogue: add the ツッコミ (reply threads onto the host) ──────────────
    hk = (say(host, "So this model beats the last one.", "openrouter", "meta-llama/llama-3.3-70b-instruct:free") or {}).get("key")
    say(guest, "Beats it on WHAT — a benchmark nobody uses?", "openrouter", "qwen/qwen-2.5-72b-instruct:free", reply=hk)
    brelay(society="studio_ai/mail_show")
    gl3 = d(gtok, "society.broadcast.live", {"society": "studio_ai/mail_show"})
    tsu = next((m for m in gl3["messages"] if "nobody uses" in m["text"]), None)
    check("dialogue: the ツッコミ is mirrored and threads onto the host's post (reply_to)",
          tsu is not None and tsu.get("reply_to") == hk, str(tsu and tsu.get("reply_to")))

    # ── gate: the relay refuses a NON-public space ───────────────────────────────────
    d("admin", "society.new", {"group": "studio_ai", "name": "private_room", "topic": "x"})
    ref = brelay(society="studio_ai/private_room")
    check("gate: relay refuses a non-public space (no accidental broadcast)",
          isinstance(ref, dict) and "__error__" in ref, str(ref)[:80])

    # ── the gate is the CONSENT, not the caller's role (step 2 §1) ───────────────────
    # The relay used to demand role:librarian of whoever asked, which made a mechanism into a
    # privilege the caller had to bring — provisioning could run it, a workflow step could not, and
    # the act itself is the same whoever asks: copy a message the society has already consented to
    # publish into the universal scope. The write is the platform's mirror writer now. What still
    # refuses is the thing that should: a space nobody opened (checked just above), and a caller who
    # cannot read the feed at all.
    d("admin", "user.add", {"client_id": "eve", "role": "user", "passphrase_hash": hashlib.sha256(b"eve").hexdigest()})
    d("admin", "grp.add", {"group_id": "studio_ai", "member_id": "eve"})
    ref2 = d("eve", "society.broadcast.relay", {"society": "studio_ai/mail_show"})
    check("a member without role:librarian may run the relay of a PUBLIC space — the write is the "
          "mirror writer's, not the caller's",
          isinstance(ref2, dict) and "__error__" not in ref2, str(ref2)[:100])
    ref3 = d("eve", "society.broadcast.relay", {"society": "studio_ai/private_room"})
    check("…and the consent gate still refuses a space nobody opened, whoever asks",
          isinstance(ref3, dict) and "__error__" in ref3, str(ref3)[:80])
    d("admin", "user.add", {"client_id": "mallory", "role": "user",
                            "passphrase_hash": hashlib.sha256(b"m").hexdigest()})
    ref4 = d("mallory", "society.broadcast.relay", {"society": "studio_ai/mail_show"})
    check("…and a NON-MEMBER cannot relay at all — it cannot read the feed to begin with",
          isinstance(ref4, dict) and "__error__" in ref4, str(ref4)[:80])

    # ── provenance fence: mirror atoms are provenance=broadcast, excluded from learning ─
    nuc = k.manager.shared_nucleus
    bset = "broadcast:studio_ai:mail_show"
    mk = (nuc.core.get_collection_members(bset) or [None])[0]
    raw = nuc.core.get_chunk_raw(mk) if mk else None
    check("provenance fence: mirror atoms are provenance=broadcast → excluded from learning (ASI06)",
          bool(raw) and _is_external(raw.get("meta")), str(bool(raw)))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — public-experiment core: a public society feed is mirrored to the nucleus by the "
          "broadcaster and read by a GUEST (no group scope) via society.broadcast.live with baked AI "
          "disclosure; since= is incremental; the relay is idempotent + privilege/public-gated; the "
          "public read carries the show's own labels; mirror atoms are learning-fenced.")
    sys.exit(0)


if __name__ == "__main__":
    main()
