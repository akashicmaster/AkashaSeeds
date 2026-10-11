#!/usr/bin/env python3
"""
Publishing to an external channel is a WORKLOAD, and it refuses in words.

Step 1 §1.3. The X poster was twenty `x_*` functions and an op in the platform, run by its own
timer, opted in by the presence of a file on disk and cursored by another file beside the process.
It is now one declaration (`news_show_x.json`), one template line, and one op — `station.publish
channel=x program=<key>` — which knows neither X nor the news show: both are pins.

What this holds:

  · the thread is FORMATTED the way X counts, not the way Python does. A URL weighs its fixed t.co
    length and a wide character weighs two, and the AI disclosure is budgeted BEFORE the body is
    clipped — otherwise a body dense in emoji or CJK passes a `len()` check, blows the cap, and what
    gets dropped is the disclosure, which is the one part that must not be;
  · three gates, each NAMING itself: nothing sealed yet, the newest turn already posted, and the
    space has not consented to be shown outside. The last is a person's decision and no boot
    supplies it, which is why it earned its own reason id rather than borrowing `not_provisioned`;
  · a FAILED post does not mark the turn posted. A cursor advanced on failure loses the turn for
    good, and the next run is the retry;
  · the posted cursor is a RECORD on the bench, not a file. A file beside the process is invisible
    to `lens`, to `as_of` and to retention, and it does not survive a cell that moves.

`channel.x.post_thread` is the platform's (step 2). It is stubbed at the hook here, which is also
how the conformance eval rehearses an effectful step: the fact that matters is what this op hands
the channel, not whether a network was reachable.

Run:  python app/test/station_publish_channel_eval.py       (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from app.concepts.bench_station import (BenchStationConcept, REASON_NO_CONSENT,
                                                   REASON_WAITING_SOURCE, REASON_FRESH,
                                                   REASON_NOT_SAID)
    from lib.akasha.workbench import llm_provider, provision, workload

    print("\n  ── the formatting, which is where the disclosure is lost or kept ──")
    C = BenchStationConcept
    check("a URL weighs its fixed t.co length, not its own",
          C._x_weight("see https://example.invalid/a/very/long/path/indeed") == len("see ") + 23,
          str(C._x_weight("see https://example.invalid/a/very/long/path/indeed")))
    check("a wide character weighs two", C._x_weight("あい") == 4 and C._x_weight("ab") == 2)
    clipped = C._x_clip("あ" * 50, 20)
    check("clipping is by WEIGHT, so a wide body cannot overflow the cap",
          C._x_weight(clipped) <= 20, "%d weighted" % C._x_weight(clipped))
    beats = [{"text": "た" * 400, "model": "mistral-small", "ai_notice": "AI-generated · m"},
             {"text": "second beat"}, {"text": "third beat"}]
    thread = C._x_format(C, beats, "https://example.invalid/station/ai-news/")
    check("one turn becomes a reply chain, one tweet per beat", len(thread) == 3, str(len(thread)))
    check("every tweet is inside X's cap even with a wide body",
          all(C._x_weight(t) <= 280 for t in thread), str([C._x_weight(t) for t in thread]))
    check("the FIRST carries the disclosure and the hashtag",
          "AI-generated" in thread[0] and "#AkashaNews" in thread[0], thread[0][-60:])
    check("the LAST carries the disclosure and the link back to the room",
          "AI-generated" in thread[-1] and "station/ai-news" in thread[-1], thread[-1][-70:])

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_pub_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"},
               "local")

    def d(client, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": client, "data": data}, "id": "t"}, "local")

    def res(r):
        return (r or {}).get("result") or {}

    provision.provision_workloads(k)
    wl = workload.by_key(k, "studio_ai/news_show_x")
    check("the channel workload is declared and provisioned", bool(wl),
          str(sorted(workload.key(x) for x in workload.declarations(k))))
    check("… it names the channel and the programme as PINS, so the op knows neither",
          (wl.get("pins") or {}).get("channel") == "x"
          and (wl.get("pins") or {}).get("program") == "studio_ai/news_show",
          json.dumps(wl.get("pins") or {}))
    check("… and it reserves NOTHING, because it calls no model",
          (wl.get("appetite") or {}).get("llm_calls_per_run") == 0,
          str((wl.get("appetite") or {}).get("llm_calls_per_run")))

    print("\n  ── nothing sealed yet ──")
    r = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show"}))
    check("it stands by on the source it is waiting for",
          r.get("status") == "standby" and r.get("reason") == REASON_WAITING_SOURCE,
          "%s / %s" % (r.get("status"), r.get("reason")))

    # one aired turn of the news show to republish
    news = workload.by_key(k, "studio_ai/news_show")
    gid, space = workload.society_of(news)
    client = (news.get("space") or {}).get("client")
    for i in (1, 2, 3):
        d("admin", "kernel.memory.define",
          {"name": "probe:item:%d" % i, "description": "A recorded item, number %d." % i,
           "scope": "universal"})
    d("admin", "set.add", {"name": (news.get("pins") or {}).get("item_set"), "id": "probe:item:1"})
    _n = [0]

    def _gen(p, m, s, u, timeout=60.0):
        _n[0] += 1
        return "A line the model produced, number %d." % _n[0]

    llm_provider.generate = _gen
    def _air_one_turn():
        """One cycle of the news show, exactly as its template runs it: three beats, then the
        mirror. The mirror matters here — the channel workload reads the guest-safe public view,
        so it can only ever post what a visitor could already read."""
        for role in ("Anchor", "Commentator", "Anchor.wrap"):
            d(client, "society.air", {"program": "studio_ai/news_show", "role": role,
                                      "source": "next" if role == "Anchor" else "current",
                                      "last": "feed:last"})
        d("admin", "society.broadcast.relay", {"group": gid, "space": space})

    _air_one_turn()

    print("\n  ── the space has not consented to leave the building ──")
    # The news show DECLARES `public: true`, so provisioning has already opened it. Consent is
    # withdrawn here to drive the gate — and that it can be withdrawn at all is the point: it is a
    # person's standing decision about their own space, not a one-way switch a deploy flips.
    # WITHDRAWN BY THE OPERATOR, not by the programme. `client` here is
    # `llm:programme:news_show` — the workload's own client — and consent is precisely the thing a
    # programme must not decide about itself: "a person's standing decision", as this file's own
    # header says. It was the creator check that refused it, and that check stays until the
    # society row of the ruling; what the case is about is the gate BELOW it.
    d("admin", "society.public", {"group": gid, "space": space, "open": "no"})
    r = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show"}))
    check("it refuses, and the refusal is its own reason id",
          r.get("status") == "standby" and r.get("reason") == REASON_NO_CONSENT,
          "%s / %s" % (r.get("status"), r.get("reason")))
    check("… which is NOT `not_provisioned` — a boot cannot supply a person's decision",
          r.get("reason") != REASON_NOT_SAID, str(r.get("reason")))

    print("\n  ── the stand-by is on the record of the workload that RAN it ──")
    # §1.1 (09-26): the refusal used to be a log line under `key=studio_ai/news_show`, and nothing
    # on the bench — so the platform, reading the X workload's own rows for the run's reason, read
    # ''. The template passes `workload=`; the row goes under that key and nowhere else.
    tpl = open(os.path.join(ROOT, "app/config/workbench/studio_ai/templates/news_show_x.ak")).read()
    check("the template passes the workload's own key",
          "workload=studio_ai/news_show_x" in tpl and "workload=$workload" in tpl)
    XW = "studio_ai/news_show_x"

    def _rows(program, since=None):
        q = {"name": "studio_ai", "program": program}
        if since is not None:
            q["since"] = since
        return res(d("admin", "station.air.ls", q)).get("aired") or []

    news_before = len(_rows("studio_ai/news_show"))
    t0 = time.time() - 0.001
    r = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show",
                                         "workload": XW}))
    xr = _rows(XW, since=t0)
    check("a refused publish is ONE row under `studio_ai/news_show_x`, carrying `no_consent`",
          r.get("reason") == REASON_NO_CONSENT and len(xr) == 1
          and xr[0].get("reason") == REASON_NO_CONSENT and not xr[0].get("aired"),
          json.dumps(xr)[:160])
    check("… and the news show's own record is untouched — a refused republish is not its airing",
          len(_rows("studio_ai/news_show")) == news_before)
    t1 = time.time() - 0.001
    res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show",
                                     "workload": XW, "dry": "yes"}))
    check("a dry run records nothing (a preview is not a run)", not _rows(XW, since=t1))

    print("\n  ── a dry run formats without posting, and needs no consent to preview ──")
    r = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show",
                                         "dry": "yes"}))
    check("the preview is the thread it would send", r.get("status") == "dry_run"
          and len(r.get("tweets") or []) >= 1, "%s count=%s" % (r.get("status"), r.get("count")))

    # consent restored, and a stubbed channel client
    d("admin", "society.public", {"group": gid, "space": space, "open": "yes"})
    sent = []

    # THE STUB CARRIES THE HOOK'S OWN SIGNATURE — `post_thread_hook(tweets, dry=False)`. It used
    # to take a leading `kernel`, which the real hook does not, so the caller's extra argument
    # never showed up here: the one path where it mattered (an actually-consented post) was
    # rehearsed against a stub that forgave it. A stub that does not match is not a test.
    def _post(tweets, dry=False):
        sent.append(list(tweets))
        return {"ids": ["111", "112", "113"][:len(tweets)], "posted": len(tweets)}

    k.api.hooks["channel.x.post_thread"] = _post

    print("\n  ── consented: it posts, once ──")
    r = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show"}))
    check("it posts", r.get("status") == "posted", "%s / %s" % (r.get("status"), r.get("reason")))
    check("… handing the channel the formatted thread", len(sent) == 1 and bool(sent[0]),
          "calls=%d tweets=%d" % (len(sent), len(sent[0]) if sent else 0))
    check("… and the ids the channel returned are on the result",
          bool(r.get("ids")) and r.get("count") == len(r["ids"]), json.dumps(r.get("ids")))
    turn = r.get("turn")

    r2 = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show"}))
    check("a second run does not post the same turn again",
          r2.get("status") == "standby" and r2.get("reason") == REASON_FRESH,
          "%s / %s" % (r2.get("status"), r2.get("reason")))
    check("… and the channel was not called a second time", len(sent) == 1, "calls=%d" % len(sent))

    print("\n  ── the cursor is a RECORD, not a file ──")
    got = res(d("admin", "r", {"id": "wb:studio_ai:x:studio_ai_news_show:%s" % turn}))
    meta = got.get("meta") or {}
    check("the posted turn is an atom on the bench, readable like anything else",
          meta.get("concept") == "station_posted", json.dumps(meta)[:110])
    check("… carrying the channel, the programme and the ids it got back",
          meta.get("channel") == "x" and meta.get("program") == "studio_ai/news_show"
          and bool(meta.get("ids")), json.dumps(meta)[:140])

    print("\n  ── a post that FAILS does not consume the turn ──")
    d("admin", "set.add", {"name": (news.get("pins") or {}).get("item_set"), "id": "probe:item:2"})
    _air_one_turn()
    k.api.hooks["channel.x.post_thread"] = lambda tweets, dry=False: {"ids": []}
    r3 = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show"}))
    check("it reports a standby rather than a post", r3.get("status") == "standby",
          "%s / %s" % (r3.get("status"), r3.get("reason")))
    k.api.hooks["channel.x.post_thread"] = _post
    t2 = time.time() - 0.001
    r4 = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show",
                                          "workload": XW}))
    check("… and the SAME turn is posted on the next run — the failure was not recorded as a send",
          r4.get("status") == "posted" and r4.get("turn") == r3.get("turn"),
          "%s turn=%s (failed on %s)" % (r4.get("status"), r4.get("turn"), r3.get("turn")))
    xr = _rows(XW, since=t2)
    check("… and a post run is an AIRED row under the workload's key — its effect is countable",
          len(xr) == 1 and xr[0].get("aired") and not xr[0].get("reason"), json.dumps(xr)[:140])

    print("\n  ── no client for the channel ──")
    k.api.hooks.pop("channel.x.post_thread", None)
    d("admin", "set.add", {"name": (news.get("pins") or {}).get("item_set"), "id": "probe:item:3"})
    _air_one_turn()
    r5 = res(d("admin", "station.publish", {"channel": "x", "program": "studio_ai/news_show"}))
    check("it stands by rather than raising — a missing client is a precondition, not a crash",
          r5.get("status") == "standby" and r5.get("reason") == REASON_NOT_SAID,
          "%s / %s" % (r5.get("status"), r5.get("reason")))

    print("\n  ── as the X workload's OWN client, not as admin (2026-09-28) ──")
    # The live cell posted nothing: the X workload ran as `llm:programme:news_show_x`, which holds no
    # line on studio_ai/news_show, so the publish gate refused `out_of_scope` — and the op reported
    # it as `no_consent`. The declaration now runs it as the news show's client, and a refusal that
    # is not about consent says what it is.
    from app.concepts.bench_station import REASON_NOT_PROVISIONED
    xcl = workload.client_of(wl)
    check("the X workload runs as the news show's own client",
          xcl == workload.client_of(news), "%s vs %s" % (xcl, workload.client_of(news)))
    k.api.hooks["channel.x.post_thread"] = _post
    d("admin", "set.add", {"name": (news.get("pins") or {}).get("item_set"), "id": "probe:item:4"})
    d("admin", "kernel.memory.define", {"name": "probe:item:4", "description": "A recorded item, number 4.",
                                        "scope": "universal"})
    _air_one_turn()
    r6 = res(d(xcl, "station.publish", {"channel": "x", "program": "studio_ai/news_show",
                                      "workload": "studio_ai/news_show_x"}))
    check("…and posts as that client", r6.get("status") == "posted",
          "%s / %s / %s" % (r6.get("status"), r6.get("reason"), r6.get("detail")))
    # A channel with no posting history (`fresh` is per channel), so the GATE is what answers.
    stranger = workload.client_of(workload.by_key(k, "studio_ai/plant_geek"))
    r7 = res(d(stranger, "station.publish", {"channel": "x2", "program": "studio_ai/news_show",
                                           "dry": "", "workload": "studio_ai/news_show_x"}))
    check("a client with no reach on the news show is refused as `not_provisioned` (gate term in "
          "the detail) — NOT as `no_consent`",
          r7.get("reason") == REASON_NOT_PROVISIONED and "out_of_scope" in str(r7.get("detail")),
          "%s / %s" % (r7.get("reason"), r7.get("detail")))

    print("\n  ── the sponsor line: its own last reply, true, labelled #ad (2026-09-28) ──")
    import re as _re
    _ak = open(os.path.join(ROOT, "app", "ontology", "station_neta", "x_sponsor.ak"), encoding="utf-8").read()
    _lines = dict(_re.findall(r'^def "([^"]+)" "(.*)"$', _ak, _re.M))
    check("the shipped sponsor lines each carry #ad and the referral URL",
          len(_lines) >= 6 and all(v.endswith("#ad") and "https://x.getstanley.ai/r/" in v
                                   for v in _lines.values()), str(len(_lines)))
    check("…and none claims stanley wrote or drafted the posts",
          not any(_re.search(r"\b(draft|drafted|written|wrote|writ)", v) for v in _lines.values()))
    _set = (wl.get("pins") or {}).get("sponsor_set")
    for a, v in _lines.items():
        d("admin", "kernel.memory.define", {"name": a, "description": v, "scope": "universal"})
        d("admin", "set.add", {"name": _set, "id": a})
    # the cadence the declaration sets (owner, 09-28): not every post — the 4th, 8th, … post
    _every = int((wl.get("pins") or {}).get("sponsor_every") or 1)
    _bs = BenchStationConcept(k.manager.get_session(xcl))
    _beats0 = _bs._latest_turn(gid, space)[1]
    _with = [n for n in range(12) if _bs._sponsor_line(wl, _beats0, 7, "studio_ai/news_show", posted=n)]
    _pc = _bs._posted_count("studio_ai", "x", "studio_ai/news_show")
    check("the posted count is read from the posted RECORDS (3 real posts so far in this eval)",
          _pc == 3, str(_pc))
    check("the declaration puts the sponsor line on every 4th posted thread, not on every one",
          _every == 4 and _with == [3, 7, 11], "every=%s with-line at posted=%s" % (_every, _with))
    # the content checks below run with the line on every post, so they test the line itself
    import copy as _copy
    _real_wl = BenchStationConcept._workload
    _wl1 = _copy.deepcopy(wl); _wl1["pins"]["sponsor_every"] = 1
    BenchStationConcept._workload = (lambda self, key="", *a, **kw:
                                     _wl1 if key == "studio_ai/news_show_x" else _real_wl(self, key, *a, **kw))
    pv1 = res(d(xcl, "station.publish", {"channel": "x", "program": "studio_ai/news_show",
                                       "workload": "studio_ai/news_show_x", "dry": "yes"}))
    tw = pv1.get("tweets") or []
    check("the thread closes with ONE sponsor reply, after the news and its AI disclosure",
          len(tw) >= 2 and tw[-1] in _lines.values() and all("#ad" not in t for t in tw[:-1]),
          (tw[-1] if tw else "")[:90])
    pv2 = res(d(xcl, "station.publish", {"channel": "x", "program": "studio_ai/news_show",
                                       "workload": "studio_ai/news_show_x", "dry": "yes"}))
    check("…the same line for the same turn (a retry keeps its wording)",
          (pv2.get("tweets") or [None])[-1] == tw[-1])
    pv3 = res(d(xcl, "station.publish", {"channel": "x", "program": "studio_ai/news_show", "dry": "yes"}))
    check("…and a publish with no running workload declaring `sponsor_set` adds none",
          not any("#ad" in t for t in (pv3.get("tweets") or [])))
    _beats = BenchStationConcept(k.manager.get_session(xcl))._latest_turn(gid, space)[1]
    _src = next((b.get("source") for b in _beats if b.get("source")), "")
    own = "this item's own sponsor line: https://x.getstanley.ai/r/pww9nh #ad"
    d("admin", "kernel.memory.define", {"name": _src + ":sponsor", "description": own,
                                        "scope": "universal"})
    pv4 = res(d(xcl, "station.publish", {"channel": "x", "program": "studio_ai/news_show",
                                       "workload": "studio_ai/news_show_x", "dry": "yes"}))
    check("an item's own `<item>:sponsor` wins over the Set",
          (pv4.get("tweets") or [None])[-1] == own, str((pv4.get("tweets") or [None])[-1])[:90])
    BenchStationConcept._workload = _real_wl

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — publishing to a channel is a workload: the channel and the programme are "
          "pins, the thread is formatted the way X counts with the disclosure budgeted before the "
          "body, each of the three gates names itself, a failed post leaves the turn to be retried, "
          "and the cursor is an atom on the bench instead of a file beside the process.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
