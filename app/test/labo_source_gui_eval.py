#!/usr/bin/env python3
"""
The Source Viewer's residues — held at the page, in a real browser.

`directive-gui-2026-09-18.md` §1. Each case drives `app/archives/labo/source/index.html` with the
backend MOCKED, so what is tested is the page's own rendering:

  §9  a capability that exists in TWO builds renders TWICE — the stale one muted and badged,
      never merged into the fresh one, never hidden, never sorted away
  §5  the day's shared model pool on the System card: `llm pool <provider> <spent>/<cap>
      reserved <n> refused <n>`, counts as served, with the per-programme breakdown
  §2  the programme table on the station bench: one row per programme, the state AS THE SERVER
      SENDS IT, and a registered programme with NO state reported as the backend defect it is
      (never filled in by the page)
  §1  an empty research bench (`wb:blvh`, `wb:mobility` — no observations) renders its live
      sections only: the probe line (`not on this server yet`) belongs to a read that is ABSENT,
      and must never appear for a read that answers empty
  §6  an empty claims Set renders three ZERO counts, not the probe

`directive-frontend-2026-09-21.md` §1.4 adds one more: a bench's `status` is RENDERED AS SERVED.
`bench.retire` deletes nothing — the bench and its observations stand and the read comes back with
`status=retired` — but the page knew only `active` and dressed every other status in the badge for
`metadata_only`, while a read carrying no status rendered no badge at all. A retired bench and a
healthy one therefore looked the same.

Run:  python app/test/labo_source_gui_eval.py       (exit 0 = all pass)
"""
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGE = "file://" + os.path.join(ROOT, "app", "archives", "labo", "source", "index.html")

VOCAB = {
    "station:state:warming_up": "warming up \u2014 registered, and its boot airing is queued.",
    "station:state:on_air": "on air \u2014 a turn aired inside the live window.",
    "station:state:rebroadcast": "rebroadcast \u2014 the last airing is repeated until the next lands.",
    "station:state:standing_by": "standing by \u2014 registered and not playing. Always carries a REASON.",
    "station:reason:provider_429": "provider 429 \u2014 the model provider rate-limited the call.",
    "station:reason:llm_pool": "llm_pool \u2014 admission could not hold the reservation.",
    "station:reason:waiting_source":
        "waiting on a source \u2014 the programme declares a source it reads from and that source is "
        "not present-and-frozen yet, so the airing is held.",
    "station:reason:not_provisioned":
        "not provisioned \u2014 a runtime precondition of the programme is missing.",
    "station:reason:not_declared":
        "not declared \u2014 this cell's build carries no declaration for the workload.",
}

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _empty_bench_answers(now):
    """A research bench that exists and has been read — and has nothing yet. Every read ANSWERS;
    none is missing. So no section may show the probe line."""
    return {
        "session.guest.create": {"binding_key": "gbk:test", "expires_at": now + 3600},
        "bench.ls": {"benches": [{"bench": "wb:blvh", "kind": "research", "status": "active"},
                                 {"bench": "wb:mobility", "kind": "research", "status": "active"}]},
        "bench.info": {"bench": "wb:blvh", "kind": "research", "status": "active",
                       "world": "public", "families": [], "observations": 0, "roles": ["Botanist"]},
        "learning.runs": {"runs": [], "diffs": []},
        "set.ls": {"count": 0, "members": []},
        "lens.rank": {"groups": []},
        "cap.ls": {"role": "Botanist", "offered": [], "granted": []},
        "store.status": {"backend": "silica", "role": "read-only", "capabilities": {}},
        "hydrate.ls": {"accelerators": [], "universe_epoch": 41},
        "r": {"meta": {}},
        "source.ls": {"sources": []},
        "source.pools": {"pools": []},
        "registry.ls": {"models": []},
    }


def _bench_status_answers(now, status):
    """A bench read that carries a given `status` — or, when `status` is None, none at all. A bench
    is never deleted (`bench.retire` records the retirement and leaves everything standing), so
    `retired` is a value a page WILL be served and must render as served."""
    a = _empty_bench_answers(now)
    a["bench.info"] = {"bench": "wb:studio_shelf", "kind": "station", "world": "default",
                       "families": [], "observations": 0, "roles": ["Reader"]}
    if status is not None:
        a["bench.info"]["status"] = status
    return a


def _station_answers(now):
    """The two reads that replaced `society.station`. The platform records and answers and no
    longer names: `set.ls wl:effect:publish` says WHICH programmes are declared, and one
    `workload.status key=` each answers `last {at,ok,reason,by}`, `gate {run}`, `next_at` and
    `spent_today` \u2014 and no `state`. Five cases, so every branch of the page's own composer is
    exercised: a fresh run, a stale one, a run the op stood by WITH its reason, a run it stood by
    with NONE, and a GATE refusal (the platform's own term, which the page must read through the
    station's vocabulary). A sixth key answers nothing at all \u2014 the defect marker."""
    a = _empty_bench_answers(now)
    a["bench.info"] = {"bench": "wb:studio_ai", "kind": "station", "status": "active",
                       "observations": 12, "roles": ["broadcaster"]}
    a["station.air.ls"] = {"bench": "wb:studio_ai", "count": 0, "aired": []}
    a["_wl_keys"] = ["studio_ai/news_show", "studio_ai/thinkers_shelf", "studio_ai/art_explorer",
                     "studio_ai/plant_geek", "studio_ai/news_show_x", "studio_ai/weather_desk"]
    a["_wl_status"] = {
        "studio_ai/news_show": {
            "key": "studio_ai/news_show", "declared": True, "society": "studio_ai/news_show",
            "last": {"at": now - 120, "ok": True, "reason": "", "by": "station.air.turn"},
            "gate": {"run": "ok"}, "next_at": now + 1800, "spent_today": 18},
        "studio_ai/art_explorer": {
            "key": "studio_ai/art_explorer", "declared": True, "society": "studio_ai/art_explorer",
            "last": {"at": now - 5400, "ok": True, "reason": "", "by": "station.air.turn"},
            "gate": {"run": "ok"}, "next_at": now + 5400, "spent_today": 6},
        "studio_ai/thinkers_shelf": {
            "key": "studio_ai/thinkers_shelf", "declared": True,
            "society": "studio_ai/thinkers_shelf",
            "last": {"at": now - 9000, "ok": False,
                     "reason": "station:reason:provider_429", "by": "station.air.turn"},
            "gate": {"run": "ok"}, "next_at": now + 3600, "spent_today": 30},
        "studio_ai/plant_geek": {
            "key": "studio_ai/plant_geek", "declared": True, "society": "studio_ai/plant_geek",
            "last": None, "gate": {"run": "source_ready"}, "next_at": now + 600, "spent_today": 0},
        # a run the OP stood by and gave NO reason for. The platform stopped substituting one, so
        # the page must leave it empty rather than supply a word on the platform's behalf.
        "studio_ai/news_show_x": {
            "key": "studio_ai/news_show_x", "declared": True, "society": "studio_ai/news_show_x",
            "last": {"at": now - 1200, "ok": False, "reason": "", "by": "station.publish"},
            "gate": {"run": "ok"}, "next_at": now + 14400, "spent_today": 0},
    }
    return a


def _pool_answers(now):
    a = _empty_bench_answers(now)
    a["_pool_day"] = time.strftime("%Y-%m-%d", time.gmtime())
    a["cap.ls"] = {"role": "Botanist", "granted": [], "offered": [
        {"name": "bench.read", "fingerprint": "23f40c3c00", "effectful": False, "stale_build": True},
        {"name": "bench.read", "fingerprint": "157f4eec00", "effectful": False, "stale_build": False},
        {"name": "runs.read", "fingerprint": "157f4eec00", "effectful": False, "stale_build": False}]}
    return a


def _handler(answers):
    def serve(route, request):
        try:
            body = json.loads(request.post_data or "{}")
        except (TypeError, ValueError):
            body = {}
        m = body.get("method") or ""
        data = ((body.get("params") or {}).get("data")) or {}
        rid = str(data.get("id", ""))
        if m == "r" and (rid.startswith("station:state:") or rid.startswith("station:reason:")):
            res = {"id": rid, "content": VOCAB.get(rid, ""), "meta": {}}
        elif m == "r" and rid.startswith("llm:pool:ollama:"):
            res = {"id": rid, "meta": {"concept": "llm_pool", "provider": "ollama",
                                       "day": answers.get("_pool_day", ""), "capacity_calls": 0,
                                       "spent_calls": 12, "reserved": 0, "refused": 0,
                                       "by": {"studio_ai/plant_geek": {"spent": 12, "reserved": 0}}}}
        elif m == "r" and rid.startswith("llm:pool:mistral:"):
            res = {"id": rid, "meta": {
                "concept": "llm_pool", "provider": "mistral", "day": answers.get("_pool_day", ""),
                "capacity_calls": 3000, "spent_calls": 41, "reserved": 2, "refused": 1,
                "by": {"studio_ai/news_show": {"spent": 27, "reserved": 0},
                       "studio_ai/thinkers_shelf": {"spent": 14, "reserved": 2}}}}
        elif m == "set.ls" and str(data.get("name") or "") == "wl:effect:publish":
            res = {"members": [{"alias": "wl:" + k.replace("/", ":")}
                               for k in answers.get("_wl_keys", [])]}
        elif m == "workload.status":
            # a key the platform does not answer is an ERROR, not an empty object: the page has to
            # be able to tell "no value exists" from "the value is blank"
            res = (answers.get("_wl_status") or {}).get(str(data.get("key") or ""))
            if res is None:
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps({"jsonrpc": "2.0", "id": body.get("id"),
                                               "error": {"code": -32602, "message": "unknown key"}}))
                return
        else:
            res = answers.get(m, {})
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"jsonrpc": "2.0", "result": res, "id": body.get("id")}))
    return serve


_nav = [0]


def _open(page, answers, hash_):
    # A goto that changes ONLY the hash is a same-document navigation — the page would keep the
    # previous case's state and its (now unrouted) requests would fail. A unique query forces a
    # real load, so each case boots the page fresh.
    page.route("**/rpc", _handler(answers))
    _nav[0] += 1
    page.goto("%s?case=%d#%s" % (PAGE, _nav[0], hash_))
    page.wait_for_timeout(1400)


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n  SKIP — playwright is not installed; this eval drives the real page.\n")
        return 0

    now = int(time.time())
    exe = next(iter(sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))), "")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**({"executable_path": exe} if exe else {}))
        page = browser.new_page()

        print("\n  ── §2 · the programme table, from the served contract ──")
        _open(page, _station_answers(now), "src=bench/studio_ai")
        body = page.eval_on_selector("#focus", "e => e.innerText")
        for label, want in (("a fresh run", "on air"), ("a stale one", "rebroadcast"),
                            ("a gate refusal", "waiting on a source")):
            check("%s is COMPOSED into the station's word, read from the vocabulary" % label,
                  want in body, want)
        check("a run the op stood by names the OP'S OWN reason, from the vocabulary",
              "standing by \u00b7 provider 429" in body,
              [l for l in body.split("\n") if "provider 429" in l][:1])
        check("a run with an EMPTY reason is still a standby, with no word invented for it",
              body.count("standing by") >= 3, "standing by \u00d7%d" % body.count("standing by"))
        check("the raw ids never reach the page",
              "station:state:" not in body and "station:reason:" not in body)
        check("every programme is named by its `<bench>/<slug>` key",
              body.count("studio_ai/") >= 5, "occurrences=%d" % body.count("studio_ai/"))
        check("a key the platform does not answer shows the defect marker, not `unclassified`",
              "state missing (server)" in body)
        check("\u2026 and the table says it is a backend defect",
              "backend defect" in body and "did not answer" in body)
        check("the last-run cell says the outcome, when, and which op",
              "stood by" in body and "station.air.turn" in body,
              [l for l in body.split("\n") if "station.air.turn" in l][:1])
        check("the model-call cell is `spent_today`, as the platform accounts it",
              "18" in body and "30" in body)
        check("a programme that has never run says so rather than showing an empty time",
              "no run recorded" in body)
        page.unroute("**/rpc")

        print("\n  ── §1 · an empty research bench shows no probe line ──")
        _open(page, _empty_bench_answers(now), "src=bench/blvh")
        n_probe = page.eval_on_selector_all(".notyet", "els => els.length")
        body = page.eval_on_selector("#focus", "e => e.innerText")
        check("no `not on this server yet` anywhere on an empty bench (every read ANSWERED)",
              n_probe == 0, "probe lines=%d" % n_probe)
        check("the empty run list is said plainly, as a live read",
              "No run on this bench" in body, body[:60].replace("\n", " "))
        print("\n  ── §6 · an empty claims Set is three zero counts ──")
        check("claims: attached 0 · unattached 0 · contradicted 0",
              "claims: attached 0 · unattached 0 · contradicted 0" in body,
              [l for l in body.split("\n") if "claims" in l][:1])
        page.unroute("**/rpc")

        print("\n  ── §1.4 · a bench's STATUS is rendered as served ──")
        # `bench.retire` deletes nothing — the bench and its observations stand, and the read comes
        # back with `status=retired`. A page that only knew `active` rendered every other status in
        # the same badge as `metadata_only`, and a read with no status at all rendered no badge, so
        # a retired bench and a healthy one looked alike.
        _open(page, _bench_status_answers(now, "retired"), "src=bench/studio_shelf")
        badges = page.eval_on_selector_all(
            "#focus .sbadge", "els => els.map(e => [e.className, e.textContent])")
        check("a retired bench says `retired`, in its own badge",
              any(t.strip() == "retired" and "st-retired" in c for c, t in badges), str(badges)[:90])
        check("… and it is not dressed as another status",
              not any("acquired" in c or "metadata_only" in c for c, _t in badges), str(badges)[:90])
        body = page.eval_on_selector("#focus", "e => e.innerText")
        check("… while the bench itself still renders (nothing is deleted on retirement)",
              "wb:studio_shelf" in body, body[:60].replace("\n", " "))
        check("no probe line on a retired bench either",
              page.eval_on_selector_all(".notyet", "els => els.length") == 0)
        page.unroute("**/rpc")

        _open(page, _bench_status_answers(now, None), "src=bench/studio_shelf")
        badges = page.eval_on_selector_all(
            "#focus .sbadge", "els => els.map(e => [e.className, e.textContent])")
        check("a read that carries NO status says `unclassified`, rather than showing nothing",
              any("unclassified" in t for _c, t in badges), str(badges)[:90])
        page.unroute("**/rpc")

        print("\n  ── §9 / §5 · two builds of one capability, and the model pool ──")
        _open(page, _pool_answers(now), "src=bench/blvh")
        chips = page.eval_on_selector_all(
            ".ochip", "els => els.map(e => [e.className, e.textContent])")
        reads = [c for c in chips if "bench.read@" in c[1]]
        check("the capability appears TWICE — once per build (never merged)",
              len(reads) == 2, "rendered=%d" % len(reads))
        check("the stale build is muted and badged `stale`",
              any("stale" in c[0] and "STALE" in c[1].upper() for c in reads),
              str(reads)[:90])
        check("the fresh build carries no stale badge",
              any("stale" not in c[0] and "157f4eec" in c[1] for c in reads), str(reads)[:90])
        check("the stale one is kept in the order served (stale first here, not sorted away)",
              reads and "23f40c3c" in reads[0][1], str(reads[:1])[:70])
        sysbody = page.eval_on_selector("#rail-system", "e => e.innerText")
        check("the System card shows `llm pool <provider>`", "llm pool mistral" in sysbody)
        check("… <spent>/<cap>, reserved and refused, as served",
              "41/3000" in sysbody and "reserved 2" in sysbody and "refused 1" in sysbody,
              sysbody.replace("\n", " ")[:110])
        check("a SECOND provider gets its own pool line (§2.2 — one per provider, never merged)",
              "llm pool ollama" in sysbody and "12/unmetered" in sysbody,
              [l for l in sysbody.split("\n") if "ollama" in l][:2])
        check("… and the per-programme breakdown the pool carries",
              "studio_ai/news_show" in sysbody and "spent 27" in sysbody,
              sysbody.replace("\n", " ")[-110:])
        print("\n  ── §10 · the epistemic stamp on an observation row (fixture) ──")
        page.goto(PAGE + "?fixture=1#src=item/source:item:plants:1")
        page.wait_for_timeout(1500)
        # the record opens on Source (the raw material); the readings live on the Observation tab
        page.eval_on_selector_all(
            ".vtab", "els => { const t = els.find(e => e.getAttribute('data-k') === 'obs');"
                     " if (t) t.click(); }")
        page.wait_for_timeout(1200)
        btns = page.eval_on_selector_all(
            ".orow .linkbtn", "els => els.map(e => e.textContent)")
        check("a row that carries its coordinate offers the epistemic stamp",
              "epistemic" in btns, str(btns[:4]))
        page.eval_on_selector_all(
            ".orow .linkbtn",
            "els => { const b = els.find(e => e.textContent === 'epistemic'); if (b) b.click(); }")
        page.wait_for_timeout(900)
        stamp = page.eval_on_selector("#focus", "e => e.innerText")
        check("… role / scopes / horizon / budget, as the coordinate records them",
              "role Botanist" in stamp and "horizon h3" in stamp and "budget 1000" in stamp)
        check("… and the two horizon counts from lens.compare (the page computes neither)",
              "shown, not read 12" in stamp and "hidden by horizon 5" in stamp,
              [l for l in stamp.split("\n") if "hidden by horizon" in l][:1])
        check("a coordinate that was planned AND happened shows BOTH aspect memberships",
              "prospective" in stamp and "perfective" in stamp,
              [l for l in stamp.split("\n") if "prospective" in l][:1])

        browser.close()

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the programme table reports the served state and names the missing one as "
          "a defect; an empty research bench shows no probe line and an empty claims Set shows zeros; "
          "two builds of a capability both render, the stale one muted; a bench's status is rendered "
          "as served, retirement included, and said to be unclassified when the read carries none; "
          "and the day's model pool is on the System card as counts.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
