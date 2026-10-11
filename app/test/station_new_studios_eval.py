#!/usr/bin/env python3
"""
The Art Explorer and The Plant Geek, switched ON — and the arithmetic that makes that safe.

Both were declared on 2026-09-17 and never ran: they had a studio row and no programme, so nothing
provisioned them, nothing armed them, and the guide carried no state for either. They are now DRIVEN
like the Thinker's Shelf. The maintainer's reason for doing it rather than waiting is worth writing
down, because it is the judgement this eval serves: *deploying something you cannot verify
immediately costs more than the model calls do.* A programme nobody can watch is not cheap.

So this holds the four things that decide whether switching them on was right:

  §1  they are DRIVEN — the projected row carries `programme`, which is the exact predicate the
      boot pass uses to decide a studio is its to provision
  §2  provisioning stands each one up with NO operator: society, casts, grants, bench, the cycle on
      that bench, the moderator armed from the declaration
  §3  The Art Explorer reads a PLAIN-TEXT ontology Set and AIRS. This is the new thing: the reading
      room's passages are JSON with a bibliographic anchor, and an ordinary ontology atom is not —
      its description IS the record, and its alias IS the anchor. Without that branch the art
      programme resolves no source and stands by for ever, which is the difference between a studio
      that works on the VPS and one that only looks declared
  §4  The Plant Geek, whose Set is empty on every current cell, stands by with a REASON and does not
      invent a species to have something to say

and one guard that is the point of the whole file:

  §5  the day's DECLARED spend — Σ(appetite × per_day) over every programme — fits the provider's
      daily call ceiling. Switching a programme on can no longer silently overrun the cap: the
      arithmetic is done here, in the repo, before a deploy discovers it at 04:00Z.

Run:  python app/test/station_new_studios_eval.py      (exit 0 = all pass)
"""
import glob
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WORKLOADS = os.path.join(ROOT, "app", "config", "workbench", "workloads")
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def load(name):
    with open(os.path.join(WORKLOADS, name), encoding="utf-8") as fh:
        return json.load(fh)


def load_manifest_units():
    """The workbench's declared thread units — seed A retired `svc:news-broadcast` from them."""
    with open(os.path.join(ROOT, "lib", "akasha", "workbench", "MANIFEST.json"), encoding="utf-8") as f:
        return [u.get("name") for u in (json.load(f).get("thread_units") or [])]


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.workbench import llm_provider
    from lib.akasha.workbench import llm_pool
    from lib.akasha.workbench import workload as _W
    from lib.akasha.workbench import workload_provision as _wp

    rows = {_W.key(x): x for x in _W.declarations(None)}

    print("\n  ── §1 · driven, not merely declared ──")
    # Seed A moved the predicate. A workload is the boot pass's to provision when its DECLARATION is
    # well-formed and its template exists — not when a projected studio row happens to carry a
    # `programme` file. That is the same question ("will the boot stand this up?") asked of the file
    # that now answers it, and it is answered for all four rather than for the two that had a row.
    for key in ("studio_ai/art_explorer", "studio_ai/plant_geek"):
        row = rows.get(key) or {}
        check("%s is a well-formed declaration — the boot pass will provision it" % key,
              bool(row) and _W.problems(row) == [], str(_W.problems(row) or "missing"))
        check("… and its template exists, so it is armed onto a bench that has a workflow",
              bool(_wp.template_path(row)), "%s: %s" % (key, bool(_wp.template_path(row))))
    news = rows.get("studio_ai/news_show") or {}
    check("the news show is driven by the same one driver (its cadence is its own trigger, and the "
          "`svc:news-broadcast` timer that was the second driver is retired)",
          bool(news) and _W.trigger(news)["every_s"] == 1800.0
          and "svc:news-broadcast" not in json.dumps(
              load_manifest_units()), str(_W.trigger(news)))

    print("\n  ── §5 · the day's declared spend fits the ceiling ──")
    # Σ(appetite × per_day) across every workload, against the provider's daily call ceiling. An
    # appetite is what ADMISSION reserves before a run, so this is the demand the pool sees, not an
    # optimistic estimate of what gets spent.
    per = []
    for p in sorted(glob.glob(os.path.join(WORKLOADS, "*.json"))):
        w = json.load(open(p, encoding="utf-8"))
        # Skipped by SHAPE. A DEPLOYED cell has files here that no development tree carries — the
        # crystallizer writes `auto_exec.json`, whose top level is a LIST — and a reader that takes
        # every `*.json` for a mapping raises on it. That is how this eval crashed on an extracted
        # seed while passing here.
        if not isinstance(w, dict):
            continue
        if not (w.get("workflow") and w.get("appetite")):
            continue
        n = int(w["appetite"]["llm_calls_per_run"]) * int((w.get("budget") or {}).get("per_day") or 0)
        per.append((w["workflow"], n))
    total = sum(n for _s, n in per)
    # The ceiling is read through `llm_pool.caps()` — the number ADMISSION reserves against — not
    # through a constant here and not through a second read that could drift from it. Both it and
    # `llm_provider.quota()` resolve `llm_provider._budget()`, and that is asserted rather than
    # assumed: a repo-time bound that disagrees with the runtime's is worse than no bound.
    cap, _tokens_cap = llm_pool.caps("mistral")
    quota = (llm_provider.quota("mistral") or {})
    check("the eval's ceiling IS the one admission reserves against",
          cap == int(quota.get("calls_per_day") or 0),
          "llm_pool.caps=%s quota.calls_per_day=%s" % (cap, quota.get("calls_per_day")))
    # …and say WHERE it came from, because the deployed host may raise it. `_FREE_TIER` is the
    # built-in; `AKASHA_LLM_[MISTRAL_]CALLS_PER_DAY` overrides it per host. The VPS runs at 500
    # while this repo's built-in is 220, and the two are the same ceiling read in two processes —
    # not two ceilings. This check therefore bounds the declared demand against the ceiling IN
    # FORCE WHERE IT RUNS, which is the only bound worth having.
    _builtin = int((llm_provider._FREE_TIER.get("mistral") or {}).get("calls_per_day") or 0)
    _src = "env override" if cap != _builtin else "built-in default"
    # Every declaration with a workflow — stations, the X channel AND the plants lab (appetite 0, but
    # admission still reads it). Counted against the declarations, not a hard-coded number, so a new
    # workload is checked the day it lands instead of breaking the count.
    _declared = [x for x in _W.declarations(None) if x.get("workflow")]
    check("every workload declares an appetite and a per-day budget",
          len(per) == len(_declared) and len(per) >= 5, str(per))
    check("the declared day fits the provider's call ceiling (%d of %d)" % (total, cap),
          cap > 0 and total <= cap,
          "%s; ceiling from the %s" % ("; ".join("%s=%d" % (s, n) for s, n in per), _src))
    check("… with headroom left for a retry and an operator's own calls",
          cap > 0 and total <= cap * 0.9, "%d of %d (%.0f%%)" % (total, cap, 100.0 * total / (cap or 1)))
    for slug, _n in per:
        w = load(slug + ".json")
        # Each workload's templates live under ITS bench (`wb:studio_ai` → studio_ai/, the lab's
        # `wb:plants-vision` → plants-vision/), one per listed workflow (a lab lists seven).
        _bdir = str(w.get("bench") or "").replace("wb:", "")
        # Only the steps that CALL A MODEL count towards an appetite: `society.air` produces a
        # turn, while the mirror and the channel post move words that already exist. Counting them
        # would reserve calls nobody makes, which is the over-reservation that starves the pool.
        steps = []
        for _wf in (w.get("workflows") or [w["workflow"]]):
            tpl = os.path.join(ROOT, "app", "config", "workbench", _bdir, "templates", _wf + ".ak")
            steps += [l.strip() for l in open(tpl, encoding="utf-8")
                      if l.strip().startswith("society.air ")]
        # One `society.air` step is at most one model call, so with the cycle declared as data the
        # appetite is COUNTABLE. Declaring more than the template can spend is what makes admission
        # hold calls nobody uses, and a programme refused while the cap looks empty.
        check("%s's appetite is its template's step count, not an estimate" % slug,
              w["appetite"]["llm_calls_per_run"] == len(steps),
              "declared=%s steps=%d" % (w["appetite"]["llm_calls_per_run"], len(steps)))

    KernelDispatcher._boot_load_ontology = lambda self: None
    # `thesaurus` is the tier the station runs on — the one with the rooms. On `seeds` the boot
    # pass's provisioning calls are refused by the series gate and the log fills with
    # `[iam] refused … series=seeds`, which is correct behaviour and the wrong tier to test on.
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_studios_"))
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

    calls = []

    def fake_generate(provider, model, system, user, timeout=60.0):
        calls.append({"provider": provider, "model": model, "system": system, "user": user})
        return "  A line the model produced.  "

    llm_provider.generate = fake_generate

    print("\n  ── §2 · each one provisions itself, with no operator ──")
    provisioned = {}
    for key in ("studio_ai/art_explorer", "studio_ai/plant_geek"):
        cfg = rows[key]
        out = _wp.provision(lambda c, m, data: d(c, m, data), cfg, note=lambda m: None,
                            kernel_session=lambda: k.manager.get_session("system.broadcaster"))
        provisioned[key] = (cfg, out)
        # The casts are the declared ROLES plus the two who hold responsibility and never take a
        # turn (the chairman and the scribe), which provisioning admits from `moderator`.
        _want = {str((v or {}).get("cast") or rk.split(".", 1)[0])
                 for rk, v in (cfg.get("roles") or {}).items() if not rk.startswith("_")}
        _want |= {str((cfg.get("moderator") or {}).get(x))
                  for x in ("chairman", "scribe") if (cfg.get("moderator") or {}).get(x)}
        check("%s: every declared role has a cast" % key,
              set(out["casts"]) == _want and all(out["casts"].values()),
              "casts=%s want=%s" % (sorted(out["casts"]), sorted(_want)))
        check("%s: registered in the programme guide (what its room reads)" % key,
              out["registered"], "; ".join(out["problems"])[:110] or "ok")
        check("%s: connected to its bench" % key, bool(out["bench"]), str(out["bench"]))
        check("%s: armed from the declaration, not by hand" % key, out["armed"],
              "; ".join(out["problems"])[:110] or "ok")

    print("\n  ── §3 · The Art Explorer reads a PLAIN-TEXT ontology Set of WORKS, and airs ──")
    art_cfg = provisioned["studio_ai/art_explorer"][0]
    gid, space = _W.society_of(art_cfg)
    # Since 2026-09-27 the episode is the CMA open-access WORKS pack (`art_cma`, tier C): one work
    # per turn, its image beside it (`<work>:image`) for the gallery room. Two works are read from
    # the SHIPPED pack file, so the eval exercises the pack as it is, not a copy of it.
    eset = (art_cfg.get("pins") or {}).get("episode_set")
    check("the art programme reads the works Set of the `art_cma` pack",
          eset == "art:cma:broadcast" and (art_cfg.get("source") or {}).get("pack") == "art_cma",
          str(eset))
    import re as _re
    _pack = open(os.path.join(ROOT, "app", "ontology", "art_cma", "cma_works.ak"), encoding="utf-8").read()
    _works = [(m.group(1), m.group(2).replace('\\"', '"'))
              for m in _re.finditer(r'^def "(art:work:cma:[0-9_]+)" "(.*)"$', _pack, _re.M)][:2]
    check("the shipped pack carries works with their image + credit companions",
          len(_works) == 2 and all(('def "%s:image"' % a) in _pack and ('def "%s:credit"' % a) in _pack
                                   for a, _t in _works), str([a for a, _ in _works]))
    for aid, text in _works:
        d("admin", "kernel.memory.define", {"name": aid, "description": text, "scope": "universal"})
        d("admin", "set.add", {"name": eset, "id": aid})

    client = _W.client_of(art_cfg)
    r = res(d(client, "society.air", {"program": "studio_ai/art_explorer", "role": "Curator",
                                      "bench": gid, "source": "next", "provider": "mistral",
                                      "model": "mistral-small-latest", "turn": "present#1"}))
    check("`source=next` resolves a plain-text atom and the turn AIRS",
          r.get("status") == "aired", json.dumps(r)[:150])
    c0 = calls[-1] if calls else {}
    check("… and the atom's DESCRIPTION is what the role was handed to present",
          any(t[:40] in c0.get("user", "") for _a, t in _works),
          repr(c0.get("user", ""))[:80])
    check("… under the Curator's declared contract, not the caller's",
          "Curator" in c0.get("system", "") and "must NOT" in c0.get("system", "").replace("You ", ""),
          repr(c0.get("system", ""))[:70])
    aired = res(d("admin", "station.air.ls", {"name": gid, "limit": "10"})).get("aired") or []
    check("the record names the atom it read, so a listener can go back to it",
          bool(aired) and str(aired[-1].get("source", "")).startswith("art:work:cma:"),
          str(aired[-1].get("source")) if aired else "no record")

    r2 = res(d(client, "society.air", {"program": "studio_ai/art_explorer", "role": "Curator",
                                       "bench": gid, "source": "next", "provider": "mistral",
                                       "model": "mistral-small-latest", "turn": "present#2"}))
    aired2 = res(d("admin", "station.air.ls", {"name": gid, "limit": "10"})).get("aired") or []
    srcs = [a.get("source") for a in aired2 if str(a.get("aired")) in ("1", "True", "true")]
    check("a second `next` moves on — an aired entry is not read twice",
          len(set(srcs)) == 2, str(srcs))

    print("\n  ── §4 · The Plant Geek has no source, and says so rather than inventing one ──")
    plant_cfg = provisioned["studio_ai/plant_geek"][0]
    pgid = _W.bench_slug(plant_cfg)   # the bench all four share; a turn is recorded on it
    before = len(calls)
    r3 = res(d(_W.client_of(plant_cfg),
               "society.air", {"program": "studio_ai/plant_geek", "role": "Keyer", "bench": pgid,
                               "source": "next", "provider": "mistral",
                               "model": "mistral-small-latest", "turn": "key_out#1"}))
    check("it does not air", r3.get("status") != "aired", json.dumps(r3)[:120])
    # The REASON is a vocabulary id and the sentence is `detail` (2026-09-26). It used to be the
    # sentence itself, in the `reason` field — which resolved to nothing through the station
    # vocabulary, reached a reader as a raw token, and wrote no record. The same fact, now in the
    # two places a reader and a surface each look for it.
    check("… it stands by as `waiting_source`, an id the station vocabulary defines",
          r3.get("reason") == "station:reason:waiting_source", str(r3.get("reason"))[:80])
    check("… and its `detail` says the episode Set is empty on this cell, naming the Set",
          "empty" in str(r3.get("detail", "")).lower()
          and str((plant_cfg.get("pins") or {}).get("episode_set")) in str(r3.get("detail", "")),
          str(r3.get("detail"))[:130])
    check("… and it spends NOTHING — no model call is made for a turn with nothing to read",
          len(calls) == before, "calls before=%d after=%d" % (before, len(calls)))

    print("\n  ── the reading room's JSON passages still work (no regression) ──")
    shelf = rows["studio_ai/thinkers_shelf"]
    _wp.provision(lambda c, m, data: d(c, m, data), shelf, note=lambda m: None,
                  kernel_session=lambda: k.manager.get_session("system.broadcaster"))
    passage = {"book": "Dibdin", "section": "I", "text": "THE TEXT AS PRINTED.",
               "anchor": {"page": "iii"}}
    eset_s = (shelf.get("pins") or {}).get("episode_set")
    d("admin", "kernel.memory.define",
      {"name": "shelf:test:passage:1", "description": json.dumps(passage), "scope": "universal"})
    d("admin", "set.add", {"name": eset_s, "id": "shelf:test:passage:1"})
    r4 = res(d(_W.client_of(shelf),
               "society.air", {"program": "studio_ai/thinkers_shelf", "role": "Reader",
                               "bench": _W.bench_slug(shelf), "source": "next",
                               "provider": "mistral", "model": "mistral-small-latest",
                               "turn": "read#1"}))
    check("a JSON passage still resolves and airs", r4.get("status") == "aired",
          json.dumps(r4)[:130])
    check("… and its anchor is still the bibliographic one, not the atom id",
          "Dibdin" in str(r4.get("source", "")), str(r4.get("source"))[:60])

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — both studios are driven and provision themselves with no operator; the "
          "Art Explorer reads the graph's own art atoms and airs, naming the atom it read; the "
          "Plant Geek stands by with a reason and spends nothing; the reading room's JSON passages "
          "are unaffected; and the four programmes' declared day fits the provider's call ceiling "
          "with headroom, checked here rather than discovered on the air.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
