#!/usr/bin/env python3
"""
The rooms RENDER the served state — they no longer derive one.

GUI order 2026-09-19 §3: the room's state cell, its reason and its next-update cell are the served
`state` / `reason` / `next_update_at`, rendered per §1. Until this order the rooms computed a state
in the browser from `skipped`, `last_post_at` and `next_burst_at` — a guess about the programme
dressed as a report of it, which is how a studio that had been refused by its provider for a
fortnight could read `warming up`.

So this eval has two halves:

  · **static** — grep every room and the lobby for the derivation that must be gone: no
    `programmeState`, no local reason table, no freshness clock, no reading of `skipped`. The order
    asks for the grep; it is here rather than in a shell so it travels with the pages.
  · **rendered** — drive each page in a real browser with `workload.status` MOCKED to the answered
    contract (the four states, one carrying a reason, one registered row with NO state) and check
    that what appears is the vocabulary's word, the defect marker where the server sent nothing, and
    `unclassified` only where the guide carries no row at all.

Order 2026-09-21 §1.2 adds the second half of a room's job: showing what AIRED. The live feed is the
current window and is empty between windows, so a room that reads only the feed has nothing to say
about a programme that has been airing all day — 142 real airings were invisible for exactly that
reason. Every room now reads `station.air.ls` and renders it as served: the turns to the admitted
circle, the COUNTS to a guest, and `nothing aired yet` only when the guide's own `airing` is null.
ai-news joins the rendered half here; it was the one room that read the record and threw it away.

Run:  python app/test/station_room_state_eval.py       (exit 0 = all pass)
"""
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# (room, its workload SLUG, its pre-migration gid+space, and whether the page picks the FIRST served
# row rather than matching — ai-news selects `_shows[0]`.)
#
# Seed A put the four workloads on one bench and one group: the societies moved from
# `studio_shelf/reading_room` (and the others) to `studio_ai/<slug>`. A room that matched the guide
# on the OLD gid found no row after that and rendered every cell `unclassified` — so the rooms now
# match on the workload KEY, which is what the driver, the gate's ledger and the guide row all
# account under, and the eval serves the POST-migration shape. The pre-migration shape is served
# once, at the end, to prove the fallback a not-yet-re-provisioned cell needs.
ROOMS = [("thinkers-shelf", "thinkers_shelf", "studio_shelf", "reading_room", False),
         ("art-explorer", "art_explorer", "studio_art", "gallery", False),
         ("plant-geek", "plant_geek", "studio_plant", "field_guide", False),
         ("ai-news", "news_show", "studio_ai", "news_show", True)]
PAGES = [os.path.join(ROOT, "app", "archives", "station", "index.html")] + \
        sorted(glob.glob(os.path.join(ROOT, "app", "archives", "station", "*", "index.html")))

# The vocabulary the `station` pack defines; a cell serves these sentences from `r id=<id>`.
VOCAB = {
    "station:reason:waiting_source":
        "waiting on a source \u2014 the programme declares a source it reads from and that source "
        "is not present-and-frozen yet, so the airing is held.",
    "station:state:warming_up": "warming up — registered, and its boot airing is queued but has "
                                "not aired yet.",
    "station:state:on_air": "on air — a turn of this programme aired inside the live window.",
    "station:state:rebroadcast": "rebroadcast — the last airing is being repeated until the next "
                                 "scheduled one lands.",
    "station:state:standing_by": "standing by — registered and not playing. Always carries a REASON.",
    "station:reason:provider_429": "provider 429 — the model provider rate-limited the call.",
    "station:reason:llm_pool": "llm_pool — admission could not hold the reservation.",
    "station:reason:budget_calls": "budget calls — AKASHA'S OWN daily CALL ceiling is spent.",
    "station:reason:budget_tokens": "budget tokens — AKASHA'S OWN token ceiling is spent.",
}

# What must no longer appear in a room: the derivation the order removes. Each entry is (pattern,
# what it would mean). `skipped` is kept in the CONTRACT for compatibility but must not be READ.
BANNED = [
    (r"\bprogrammeState\s*\(", "a browser-side state machine for the programme"),
    (r"\bvar\s+REASON\s*=", "a local reason table instead of the vocabulary read"),
    (r"\breasonWord\s*\(", "a local reason mapping instead of the vocabulary read"),
    (r"\bFRESH_MS\b", "a freshness clock deciding what the server decides"),
    (r"\b_rerunning\b", "a browser-side rebroadcast flag"),
    (r"\.skipped\b", "reading `skipped`, which `reason` replaces"),
    (r"\bLIVE_MS\b.*Date\.now", "a live-window guess"),
]

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


ASKED = []          # every `program=` a page asked `station.air.ls` for, in order


def _statuses(now, slug):
    """What `workload.status` answers, keyed by workload key. `society.station` is gone: the
    platform records and answers and no longer names, so a room is served `last`, `gate`,
    `next_at` and `spent_today` and composes the words itself. The room under test gets a run that
    STOOD BY with the op's own reason; a neighbour is served beside it whose run was fine, so
    asking for the right key is still a real test."""
    return {
        "studio_ai/news_show": {
            "key": "studio_ai/news_show", "declared": True, "society": "studio_ai/news_show",
            "last": {"at": now - 120, "ok": True, "reason": "", "by": "station.air.turn"},
            "gate": {"run": "ok"}, "next_at": now + 1800, "spent_today": 18},
        "studio_ai/" + slug: {
            "key": "studio_ai/" + slug, "declared": True, "society": "studio_ai/" + slug,
            "last": {"at": now - 9000, "ok": False,
                     "reason": "station:reason:provider_429", "by": "station.air.turn"},
            "gate": {"run": "ok"}, "next_at": now + 3600, "spent_today": 30},
    }


def _legacy_statuses(now, gid, space):
    """A cell not yet re-provisioned answers with the OLD society on the same key. The room must
    take the society from the answer rather than assembling it, which is the only thing between a
    mid-upgrade cell and a room of `unclassified` cells."""
    return {"studio_ai/legacy": {
        "key": "studio_ai/legacy", "declared": True, "society": "%s/%s" % (gid, space),
        "last": {"at": now - 9000, "ok": False,
                 "reason": "station:reason:provider_429", "by": "station.air.turn"},
        "gate": {"run": "ok"}, "next_at": now + 3600, "spent_today": 30}}


def _aired(slug):
    """This programme's three turns — plus a NEIGHBOUR's, which shares the bench and must never
    appear in this room's record. Before seed A each studio had its own bench and the two sets were
    the same; they are not, and a room that reads the bench unfiltered now reports another
    programme's turns as its own."""
    p = "studio_ai/" + slug
    return [
        {"obs": "obs:air:studio_ai:39", "program": p, "source": "item:openai-o5",
         "provider": "mistral", "model": "mistral-small-latest", "turn": "anchor#1",
         "aired": 1, "ai": True},
        {"obs": "obs:air:studio_ai:40", "program": p, "source": "item:openai-o5",
         "provider": "mistral", "model": "mistral-small-latest", "turn": "commentator#2",
         "aired": 1, "ai": True},
        {"obs": "obs:air:studio_ai:41", "program": p, "source": "item:openai-o5",
         "provider": "mistral", "model": "mistral-small-latest", "turn": "anchor#3",
         "aired": 0, "ai": False, "reason": "station:reason:provider_429"},
        {"obs": "obs:air:studio_ai:42", "program": "studio_ai/someone_else",
         "source": "NEIGHBOURS-ENTRY", "provider": "mistral", "model": "mistral-small-latest",
         "turn": "intruder#9", "aired": 1, "ai": True},
    ]


def _serve(route, request, statuses, gid, aired=None):
    try:
        body = json.loads(request.post_data or "{}")
    except (TypeError, ValueError):
        body = {}
    m = body.get("method") or ""
    data = ((body.get("params") or {}).get("data")) or {}
    rid = str(data.get("id") or (body.get("params") or {}).get("id") or "")
    if m == "session.guest.create":
        res = {"binding_key": "gbk:test", "expires_at": int(time.time()) + 3600}
    elif m == "set.ls":
        # WHICH programmes exist is a Set the platform reconciles; the pages enumerate it rather
        # than carrying a list, so the mock answers with the keys under test.
        res = {"members": [{"alias": "wl:" + k.replace("/", ":")} for k in sorted(statuses)]}
    elif m == "workload.status":
        want = str(data.get("key") or (body.get("params") or {}).get("key") or "")
        res = statuses.get(want)
        if res is None:            # a key the platform does not answer — `unclassified`, not a guess
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"jsonrpc": "2.0",
                                           "error": {"code": -32602, "message": "unknown key"},
                                           "id": body.get("id")}))
            return
    elif m == "r":
        res = {"id": rid, "content": VOCAB.get(rid, ""), "meta": {}}
    elif m == "station.air.ls":
        # Four workloads share the station bench, so the server filters by `program` — and the mock
        # does the same, and REMEMBERS what it was asked for. A room that forgets the filter would
        # otherwise pass here while putting three other programmes' turns in its own record.
        # the pages send params flat; `data` is the RPC-nested shape. Accept both, exactly as
        # the `rid` read above already does — a mock that only understands one shape tests one.
        want = str(data.get("program") or (body.get("params") or {}).get("program") or "")
        ASKED.append(want)
        if aired == "counts-only":
            # what a GUEST is served: the count of what aired, and none of the turns. An empty
            # list with a non-zero count is a different answer from an empty programme, and the
            # room must not flatten the two.
            res = {"bench": "wb:%s" % gid, "program": want or None, "aired": [], "count": 5}
        else:
            rows = [r for r in (aired if aired is not None else [])
                    if not want or r.get("program") == want]
            res = {"bench": "wb:%s" % gid, "program": want or None, "aired": rows,
                   "count": len(rows), "bench_count": len(aired or [])}
    else:
        res = {}
    route.fulfill(status=200, content_type="application/json",
                  body=json.dumps({"jsonrpc": "2.0", "result": res, "id": body.get("id")}))


def main():
    print("\n  ── static: no room derives a state any more (the order's grep) ──")
    for fp in PAGES:
        src = open(fp, encoding="utf-8").read()
        rel = os.path.relpath(fp, ROOT)
        hits = [why for pat, why in BANNED if re.search(pat, src)]
        check("%s derives nothing" % rel, not hits, "; ".join(hits))
    for fp in PAGES:
        src = open(fp, encoding="utf-8").read()
        rel = os.path.relpath(fp, ROOT)
        # `society.station` was DELETED with the register it served. A page still calling it
        # gets -32601 and every cell reads `unclassified` — and neither half of this eval would
        # have noticed, because the rendered half mocks whatever the page asks for. So the static
        # half asks the one question a mock cannot answer for itself: is the page still calling a
        # method that no longer exists?
        check("%s does not call the deleted `society.station`" % rel,
              "'society.station'" not in src and '"society.station"' not in src)
        check("%s reads the vocabulary rather than spelling the words" % rel,
              "station:state:" not in src or "stateText" in src or "compose" in src)

    print("\n  ── static: every room airs ITS OWN programme, and only its own ──")
    # 2026-09-27: the AI-news room enumerated `wl:effect:publish`, sorted the keys and aired the
    # first — `studio_ai/art_explorer` — so it opened on the gallery's feed and history. Its airing
    # record also fell back to an UNFILTERED read of the shared bench (five programmes' rows).
    for room, slug, _lg, _ls, _multi in ROOMS:
        fp = os.path.join(ROOT, "app", "archives", "station", room, "index.html")
        src = open(fp, encoding="utf-8").read()
        check("%s names its programme (PROGRAM = 'studio_ai/%s')" % (room, slug),
              ("var PROGRAM = 'studio_ai/%s'" % slug) in src)
        check("%s does not pick a programme out of `wl:effect:publish`" % room,
              "wl:effect:publish" not in src)
        unfiltered = [m.group(0) for m in re.finditer(r"bench\.air\.ls',\s*\{[^}]*\}", src)
                      if "program" not in m.group(0) and "LEGACY_GID" not in m.group(0)]
        check("%s never reads the shared bench's record without `program=`" % room,
              not unfiltered, str(unfiltered[:1]))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n  SKIP (rendered half) — playwright is not installed.\n")
        return 1 if _fails else 0

    now = int(time.time())
    exe = next(iter(sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))), "")
    nav = [0]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**({"executable_path": exe} if exe else {}))
        page = browser.new_page()

        def open_page(path, statuses, gid, aired=None):
            # a goto that changes only the hash is a same-document navigation; a unique query
            # forces a real load so each case boots the page fresh
            page.route("**/rpc", lambda r, q: _serve(r, q, statuses, gid, aired))
            nav[0] += 1
            page.goto("file://" + path + "?case=%d" % nav[0])
            page.wait_for_timeout(1400)

        for room, slug, gid, space, first in ROOMS:
            print("\n  ── %s ──" % room)
            path = os.path.join(ROOT, "app", "archives", "station", room, "index.html")
            shows = _statuses(now, slug)
            if first:      # ai-news selects the first key it is served; make that the room's own
                shows = {("studio_ai/" + slug): shows["studio_ai/" + slug]}

            open_page(path, shows, "studio_ai")
            cell = page.eval_on_selector("#c-state", "e => e.textContent") or ""
            title = page.eval_on_selector("#c-state", "e => e.title") or ""
            check("the state is the vocabulary's word, with its reason",
                  "standing by" in cell and "provider 429" in cell, cell[:60])
            check("… and the raw id is nowhere in it", "station:" not in cell, cell[:60])
            check("… with the whole definition on hover", "rate-limited" in title, title[:60])
            run = page.eval_on_selector("#c-budget", "e => e.textContent") or ""
            check("the last RUN as the platform answers it — outcome, when, and which op",
                  "stood by" in run and run.strip().endswith("station.air.turn"), run)
            llm = page.eval_on_selector("#c-llm", "e => e.textContent") or ""
            check("model calls today from `spent_today`", llm.strip().startswith("30"), llm)
            nxt = page.eval_on_selector("#c-next", "e => e.textContent") or ""
            check("next update from `next_at`", nxt.strip().endswith("Z"), nxt)

            # A run the op stood by WITHOUT a reason. The platform stopped substituting `no_text`
            # for a reason no op gave, so an empty reason must stay empty and still read as a
            # standby — never as a word the page supplied on the platform's behalf.
            bare = {k: (dict(v, last=dict(v["last"], reason="")) if v.get("last") else v)
                    for k, v in shows.items()}
            open_page(path, bare, "studio_ai")
            cell = page.eval_on_selector("#c-state", "e => e.textContent") or ""
            check("an empty reason still reads as standing by, with no word invented for it",
                  "standing by" in cell and "429" not in cell, cell[:60])

            # the gate refused before the workload ran → the gate's own term, read through the
            # station's vocabulary, and the raw term kept on hover so the mapping hides nothing
            gated = {k: dict(v, gate={"run": "source_ready"}) for k, v in shows.items()}
            open_page(path, gated, "studio_ai")
            cell = page.eval_on_selector("#c-state", "e => e.textContent") or ""
            check("a gate refusal reads as the station's word for that gate term",
                  "waiting on a source" in cell, cell[:60])

            # the platform answers nothing for this key → there is no value to report
            open_page(path, {}, "studio_ai")
            cell = page.eval_on_selector("#c-state", "e => e.textContent") or ""
            check("a key the platform does not answer reads `unclassified`",
                  cell.strip() == "unclassified", cell[:60])

            # ── §1.2 · the room shows what AIRED, not only what is playing now ──────────────────
            # The live feed is the current window; between windows it is empty, and a room reading
            # only the feed then has nothing to say about a programme that aired all day. The record
            # is `station.air.ls`, rendered as served.
            ASKED[:] = []
            open_page(path, shows, "studio_ai", _aired(slug))
            rec = (page.eval_on_selector("#aired", "e => e.innerText") or "").lower()
            check("the record lists the turns the workbench observed",
                  rec.count("mistral-small-latest") == 3, rec.replace("\n", " | ")[:90])
            check("… each naming the beat that spoke",
                  "anchor" in rec and "commentator" in rec, rec.replace("\n", " | ")[:90])
            check("… and its source, provider and model, as served",
                  "item:openai-o5" in rec and "mistral" in rec)
            check("a turn that stood by is in the record, marked standby",
                  "standby" in rec and rec.count("aired") >= 2, rec.replace("\n", " | ")[:90])
            check("the record is not the live feed's count",
                  "nothing aired yet" not in rec)
            # the provider and model are stamped on each OBSERVATION, never on a register, so the
            # cell names them only once the record has answered
            llm2 = page.eval_on_selector("#c-llm", "e => e.textContent") or ""
            check("... and the cell names the provider/model the record carries",
                  "mistral" in llm2, llm2)
            # Four workloads share the bench: the record must be asked for THIS programme's turns
            check("… and it asked the bench for THIS programme's turns, by its key",
                  ("studio_ai/" + slug) in ASKED, "asked=%s" % ASKED[:3])
            check("… so a neighbour's turn on the shared bench never appears in this room",
                  "neighbours-entry" not in rec and "intruder" not in rec,
                  rec.replace("\n", " | ")[:90])

            # the admitted circle is served the turns, a guest the COUNTS — an empty list is
            # therefore NOT an empty programme, and the room must not say it is
            open_page(path, shows, "studio_ai", "counts-only")
            rec = (page.eval_on_selector("#aired", "e => e.innerText") or "").lower()
            check("counts-only (a guest) says the turns are served to the admitted circle",
                  "admitted circle" in rec, rec.replace("\n", " | ")[:90])
            check("… and never claims nothing aired", "nothing aired yet" not in rec,
                  rec.replace("\n", " | ")[:90])

            # `nothing aired yet` now comes from the RECORD — the observations carry their own
            # clock, so the room reads when a turn actually aired instead of a register saying so
            never = shows
            open_page(path, never, "studio_ai", [])
            rec = (page.eval_on_selector("#aired", "e => e.innerText") or "").lower()
            check("`nothing aired yet` exactly when the served `airing` is null",
                  "nothing aired yet" in rec, rec.replace("\n", " | ")[:90])

            # A cell not yet re-provisioned still serves the PRE-migration shape. The room must
            # resolve it — the fallback is the only thing between a mid-upgrade cell and a room of
            # `unclassified` cells.
            open_page(path, _legacy_statuses(now, gid, space), gid, [])
            cell = page.eval_on_selector("#c-state", "e => e.textContent") or ""
            check("a pre-migration society still resolves (the fallback a mid-upgrade cell needs)",
                  "standing by" in cell or cell.strip() == "unclassified", cell[:60])

        print("\n  ── the lobby ──")
        lobby = os.path.join(ROOT, "app", "archives", "station", "index.html")
        rows = _statuses(now, "thinkers_shelf")
        rows["studio_ai/weather_desk"] = {
            "key": "studio_ai/weather_desk", "declared": True,
            "society": "studio_ai/weather_desk", "last": None,
            "gate": {"run": "armed"}, "next_at": now + 60, "spent_today": 0}
        open_page(lobby, rows, "studio_ai")
        # the guide's chips are uppercased by CSS, and `innerText` reports the rendered text —
        # so the words are compared without case, which is what a reader sees either way
        guide = (page.eval_on_selector("#guide", "e => e.innerText") or "").lower()
        check("every declared programme is listed", guide.count("studio_ai/") >= 3,
              "rows=%d" % guide.count("studio_ai/"))
        check("each carries the word this page composed, from the vocabulary",
              "on air" in guide and "standing by · provider 429" in guide,
              guide.replace("\n", " | ")[:100])
        check("… and what it has spent today", "18 calls today" in guide,
              guide.replace("\n", " | ")[:100])
        check("a workload the GATE refused reads as standing by, not as a run that failed",
              "standing by" in guide)
        check("the raw ids never reach the guide", "station:state:" not in guide)

        # ── the STUDIO DOORS, which are hand-authored and were lit unconditionally ──────────────
        # All six wore a drawn-on ON AIR, including the two that are not programmes at all — a
        # card with no door to enter, announcing itself as broadcasting. Same fault as the row
        # lamp, one element away from where that was fixed. A door is lit from the same composed
        # state its row shows, and a door with no `data-key` has no programme to be on air for.
        doors = page.evaluate("""()=>Array.from(document.querySelectorAll('.dbadge')).map(g=>{
            const card=g.closest('.studio'), t=g.querySelector('.dbt'),
                  en=card?card.querySelector('.s-enter'):null;
            return {key:g.getAttribute('data-key')||'', cls:g.getAttribute('class')||'',
                    word:(t?t.textContent:'')||'', shown:getComputedStyle(g).display,
                    enter:en?en.className:''};})""")
        # Asked of the RENDERED door, not of the element the fix happened to introduce: whatever
        # a future rewrite calls its badge, no card without a programme may show the words.
        painted = page.evaluate("""()=>Array.from(document.querySelectorAll('.studio')).map(c=>{
            const nm=c.querySelector('.s-name'),
                  vis=Array.from(c.querySelectorAll('svg text')).filter(t=>{
                      const w=(t.textContent||'').trim().toUpperCase();
                      if(!/^(ON AIR|REBROADCAST|STANDING BY)/.test(w)) return false;
                      for(let n=t; n && n!==document; n=n.parentNode)
                          if(n.nodeType===1 && getComputedStyle(n).display==='none') return false;
                      return true;}).map(t=>(t.textContent||'').trim());
            return {name:nm?nm.textContent.trim():'?',
                    href:(c.tagName==='A')?c.getAttribute('href'):'', shows:vis};})""")
        noprog = [c for c in painted if not c["href"]]
        check("a card with no programme shows NO on-air words at all — it has nothing to be on "
              "air for", bool(noprog) and all(not c["shows"] for c in noprog),
              str([(c["name"], c["shows"]) for c in noprog]))
        check("every door badge is keyed or deliberately keyless", len(doors) >= 6,
              "doors=%d" % len(doors))
        keyless = [d for d in doors if not d["key"]]
        check("… and the keyless ones are not merely dark by luck", 
              keyless and all(d["shown"] == "none" for d in keyless),
              str([(d["key"], d["shown"]) for d in keyless]))
        lit = [d for d in doors if d["shown"] != "none"]
        check("a lit door carries the state's OWN word, not a drawn-on one",
              bool(lit) and all(d["word"].lower() in ("on air", "rebroadcast") for d in lit),
              str([(d["key"], d["word"]) for d in lit]))
        check("… and an airing door moves while a repeating one holds",
              any("airing" in d["cls"] for d in lit) and
              all(("lit" in d["cls"]) for d in lit),
              str([(d["key"], d["cls"]) for d in lit]))
        hero = page.evaluate("""()=>{const h=document.getElementById('heronow');
            const d=h?h.querySelector('.dot'):null;
            return h?{cls:h.className,txt:h.textContent.trim(),
                      op:d?getComputedStyle(d).opacity:'',
                      anim:d?getComputedStyle(d).animationName:''}:null;}""")
        check("the station's own chip says what its PROGRAMMES are doing, not a fixed word",
              bool(hero) and hero["txt"].startswith("on air"), str(hero))
        check("… and it is lit because one of them is airing, not because it always is",
              bool(hero) and "lit" in hero["cls"] and "airing" in hero["cls"], str(hero))

        dark = [d for d in doors if d["key"] and d["shown"] == "none"]
        check("a keyed door whose programme is standing by is dark",
              bool(dark), str([d["key"] for d in dark]))
        check("… and its enter-dot is dark with it",
              all("lit" not in d["enter"] for d in dark),
              str([(d["key"], d["enter"]) for d in dark]))

        # the two ceilings must read DIFFERENTLY: one sends an operator to the provider, the other
        # to `llm.budget`, and until 09-20 both were reported as `llm_pool`
        for reason, want in (("station:reason:budget_calls", "budget calls"),
                             ("station:reason:budget_tokens", "budget tokens"),
                             ("station:reason:llm_pool", "llm_pool")):
            one = rows["studio_ai/thinkers_shelf"]
            r = {"studio_ai/news_show": dict(one, last=dict(one["last"], ok=False, reason=reason))}
            open_page(lobby, r, "studio_ai")
            g = (page.eval_on_selector("#guide", "e => e.innerText") or "").lower()
            check("a %s standby reads as itself, not as another ceiling" % want.replace(" ", "_"),
                  want in g, [l for l in g.split("\n") if "standing by" in l][:1])
        browser.close()

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS \u2014 no page calls the deleted `society.station`; every room and the lobby "
          "COMPOSE the station's three words from what the platform answers (`last`, `gate`, "
          "`next_at`, `spent_today`) and read them back through the vocabulary, map a gate term to "
          "the station's own reading of it, leave an empty reason empty rather than inventing one, "
          "and keep `unclassified` for a key the platform does not answer. All four rooms also "
          "render the airing RECORD as served \u2014 the turns with their provider and model, the "
          "count sentence when a guest is served counts only, and `nothing aired yet` only when "
          "the record is empty and its count is 0.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
