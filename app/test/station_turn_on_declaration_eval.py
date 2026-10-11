#!/usr/bin/env python3
"""
A turn airs into the society its WORKLOAD declares — and never claims to when it did not.

Closes `needs user: A5` from `backend-delivery-2026-09-21-seedA-slice1.md`. Seed A provisions from
the four workload declarations; the turn op (`concepts/bench_station.py`, the user's) still resolved
its society and its roles from the legacy `studio_*.json` pair. On a cell provisioned the new way,
that pre-convergence society does not exist — so the feed write failed, `_say` swallowed the
exception, and the turn was recorded `aired=1` anyway.

Two defects, and the second is the worse one:

  · the feed and the bench record disagreed about what was broadcast — and the RECORD is what the
    guide, the room's airing panel and the day's count all believe, so a programme could report a
    day of airings with an empty transcript;
  · the news show could not air at all: its row declares `content`, not `programme`, so the legacy
    lookup found no roles and every beat refused with `declares no role 'Anchor'`.

The backend's `station_air_turn_eval` stopped asserting the feed side when it handed this over, and
says so in its own code. This is the eval that asserts it again, from the other side of the boundary.

Run:  python app/test/station_turn_on_declaration_eval.py       (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


import hashlib as _hashlib
from lib.akasha.api import gate as _G


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.workbench import llm_provider, provision, workload

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_turn_"))
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

    # The PLATFORM's provisioning path — the one a real boot takes since seed A.
    provision.provision_workloads(k)
    # A workload with ROLES speaks; one without republishes what another already said. This eval is
    # about the turn, so it drives the speakers — the channel workload has its own
    # (`station_publish_channel_eval`).
    # …and a workload that PUBLISHES: a lab (`effect: record`, e.g. plants_vision) declares roles
    # for its grants, but it has no turn to air.
    decls = [w for w in workload.declarations(k)
             if (w.get("roles") or {}) and w.get("effect") == "publish"]
    check("the platform provisioned from the workload declarations", len(decls) == 4,
          str(sorted(workload.key(w) for w in decls)))

    # A DISTINCT line per call. An utterance is content-addressed, so a stub that returns the same
    # string every time collapses every turn onto one atom and the feed stops growing — which reads
    # exactly like a turn that did not air. The counter keeps the two apart.
    _n = [0]

    def _gen(p, m, s, u, timeout=60.0):
        _n[0] += 1
        return "A line the model produced, number %d." % _n[0]

    llm_provider.generate = _gen

    print("\n  ── every programme airs into the society ITS declaration names ──")
    for wl in sorted(decls, key=workload.key):
        key = workload.key(wl)
        gid, space = workload.society_of(wl)
        pins = wl.get("pins") or {}
        eset = pins.get("episode_set") or pins.get("item_set")
        # one entry in the declared episode Set, so the turn has something to read. The packs are
        # not loaded here (this eval is about the TURN, not the corpus), so it is written in.
        aid = "probe:entry:" + key.split("/")[1]
        d("admin", "kernel.memory.define",
          {"name": aid, "description": "A recorded entry.", "scope": "universal"})
        d("admin", "set.add", {"name": eset, "id": aid})

        role = next(iter(r for r in (wl.get("roles") or {}) if not r.startswith("_")), "")
        client = (wl.get("space") or {}).get("client") or "admin"
        r = res(d(client, "society.air", {"program": key, "role": role, "source": "next"}))
        check("%s (%s) airs" % (key, role), r.get("status") == "aired",
              r.get("status") or str(r.get("reason"))[:90])

        feed = res(d("admin", "society.feed", {"group": gid, "space": space, "limit": "5"}))
        msgs = feed.get("messages") or []
        check("… into %s/%s, the society it DECLARES" % (gid, space), len(msgs) == 1,
              "messages=%d" % len(msgs))
        check("… and what the feed carries is the line the model produced",
              bool(msgs) and "A line the model produced" in (msgs[-1].get("text") or ""),
              repr((msgs[-1].get("text") if msgs else ""))[:60])

        # The record and the feed must agree — this is the pair that came apart. All four
        # workloads share ONE bench (`wb:studio_ai`), so the record is filtered to the entry THIS
        # programme read; the shared-bench total is four programmes' work and means nothing here.
        bench = str(wl.get("bench") or "").replace("wb:", "")
        rec = [a for a in (res(d("admin", "station.air.ls", {"name": bench})).get("aired") or [])
               if str(a.get("aired")) in ("1", "True", "true") and a.get("source") == aid]
        check("… and the bench record agrees with the feed (one aired turn, one message)",
              len(rec) == len(msgs) == 1, "record=%d feed=%d" % (len(rec), len(msgs)))

    print("\n  ── the DEPLOYED directory's shape, which the repo's does not have ──")
    # A deploy writes files into `app/config/workbench/workloads/` that no development tree carries:
    # the crystallizer generates `auto_exec.json` there, and its top level is a LIST. The reader
    # took `json.load(...) or {}` for a mapping, so `.get` raised on it and `society.air` failed
    # with an unhandled error — the whole station silent on every thesaurus cell, while every eval
    # here was green. The shape is part of the test now, not something only an extracted seed
    # reveals.
    wl_dir = os.path.join(ROOT, "app", "config", "workbench", "workloads")
    probe = os.path.join(wl_dir, "_deployed_shape_probe.json")
    try:
        with open(probe, "w", encoding="utf-8") as fh:
            json.dump([{"society": "x/y", "workflow": "z"}], fh)   # a LIST, like auto_exec.json
        shelf0 = workload.by_key(k, "studio_ai/thinkers_shelf")
        g0, s0 = workload.society_of(shelf0)
        before = len(res(d("admin", "society.feed",
                           {"group": g0, "space": s0, "limit": "20"})).get("messages") or [])
        r = res(d((shelf0.get("space") or {}).get("client") or "admin", "society.air",
                  {"program": "studio_ai/thinkers_shelf", "role": "Listener",
                   "source": "current", "last": "feed:last"}))
        check("a non-mapping file in the workloads directory does not break the turn",
              r.get("status") in ("aired", "standby"), "status=%s" % r.get("status"))
        after = len(res(d("admin", "society.feed",
                          {"group": g0, "space": s0, "limit": "20"})).get("messages") or [])
        check("… and the turn still airs into its declared society", after == before + 1,
              "before=%d after=%d" % (before, after))
    finally:
        if os.path.exists(probe):
            os.remove(probe)

    print("\n  ── the news show, which could not air AT ALL before ──")
    # Its studio row declares `content`, not `programme`, so the legacy lookup found no roles and
    # every beat refused. Its roles are in its workload declaration like everyone else's.
    news = workload.by_key(k, "studio_ai/news_show")
    check("the news show declares its three beats", sorted(
        r for r in (news.get("roles") or {}) if not r.startswith("_")) ==
        ["Anchor", "Anchor.wrap", "Commentator"], str(sorted(news.get("roles") or {})))
    gid, space = workload.society_of(news)
    client = (news.get("space") or {}).get("client") or "admin"
    r = res(d(client, "society.air", {"program": "studio_ai/news_show", "role": "Anchor.wrap",
                                      "source": "current", "last": "feed:last"}))
    check("a beat that is the same cast speaking again resolves and airs",
          r.get("status") == "aired", r.get("status") or str(r.get("reason"))[:90])
    check("… as the Anchor's cast, not a cast of its own",
          r.get("cast") == "Anchor", str(r.get("cast")))

    print("\n  ── a turn the FEED would not take is a standby, never an airing ──")
    # WHAT THIS CHECK NOW HOLDS, and why it changed. It used to name `Listener` and rely on the
    # caller not OWNING that cast. Two things make that case unreachable since the one-gate
    # ruling, and neither is a loss:
    #
    #   1. `Listener` is one of the shelf's three DECLARED roles, and step 4 admits a declared
    #      role for anyone the table lets speak there. Ownership is not the question any more —
    #      the casts belong to the workload, which is the whole of `_owned_cast`'s deletion.
    #   2. A speaker the table refuses HERE (tried: `member on other_lab`) never reaches the say
    #      at all: it cannot read the programme's own feed, so the turn is refused earlier, for
    #      the scope, with a different and more accurate reason.
    #
    # The guarantee worth keeping is the BUDGET one: a turn that cannot be said costs no model
    # call and never reads as aired. A role the declaration does not carry is the case that still
    # reaches it, so that is what this asserts — refused by name, nothing aired, nothing spent.
    sgid, sspace = gid, space
    before = len(res(d("admin", "society.feed",
                       {"group": sgid, "space": sspace, "limit": "20"})).get("messages") or [])
    # A SPEAKER the table does not let speak HERE. `bystander` holds `member on other_lab`, so it
    # may `say` (step 2 passes, and the RPC is admitted) but not into this space (step 3 refuses).
    # The line is never produced and the turn stands by — which is the guarantee: a turn the feed
    # would not take must not read as aired.
    r = res(d("admin", "society.air", {"program": "studio_ai/news_show", "role": "Heckler",
                                       "source": "current", "last": "feed:last"}))
    check("it does NOT report an airing", r.get("status") != "aired",
          "status=%s" % r.get("status"))
    # IT STANDS BY, IT DOES NOT VANISH. A bare refusal used to come back from the declaration
    # check, which left no trace at all — so the run read as never having happened and the
    # operator got the driver's `not_provisioned` instead of the reason. The reason is the same
    # `not_said` an unsayable cast gets, because it is the same fact (step 4's `roles`) reached
    # from the declaration's side, and the gate's own term plus the role are in `detail`. This
    # file's own closing sentence already said a refused turn is "recorded as a standby with its
    # reason"; the check was the part that had not caught up.
    check("… it stands by, and what it stands by ON names the role nobody declared",
          r.get("status") == "standby" and "Heckler" in str(r.get("detail") or "")
          and "roles" in str(r.get("detail") or "").lower(),
          "%s / %s" % (r.get("status"), str(r.get("detail"))[:90]))
    after = len(res(d("admin", "society.feed",
                      {"group": sgid, "space": sspace, "limit": "20"})).get("messages") or [])
    check("… and the feed is unchanged, so record and feed still agree",
          after == before, "before=%d after=%d" % (before, after))
    rec = res(d("admin", "station.air.ls", {"name": "studio_ai"})).get("aired") or []
    _h = [a for a in rec if a.get("turn") == "heckler"]
    check("… and its record says UNAIRED, so record and feed still agree",
          len(_h) == 1 and str(_h[0].get("aired")) in ("0", "False"), str(_h[:1])[:140])
    check("… with the reason on it, because a silent gap and a refused turn must not look alike",
          bool(_h) and _h[0].get("reason") == "station:reason:not_said",
          str(_h[0].get("reason")) if _h else "no record at all")

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — every programme's turn resolves its society, its roles and its episode "
          "from the workload declaration the driver also reads, and airs into the society that "
          "declaration names; the news show, which the legacy lookup could not serve at all, airs; "
          "and a turn the feed refuses is recorded as a standby with its reason instead of being "
          "published as an airing nobody heard.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
