#!/usr/bin/env python3
"""
A TURN IS GENERATED FROM ITS SOURCE, OR NOT AT ALL — D13.

From the port (2026-09-21, `d8091d1`) until 2026-09-26 the news show's three role prompts carried
neither `{source}` nor `{last}`. `station.air.turn` resolved the ネタ帖 item, never put it in the
message, and wrote it to the air row as the turn's source anyway. So the Anchor read out news the
model had invented ("Gemini 1.5 Pro", "AdaptiveMind", the same opener at 12:07 and 12:37) under a
record saying `source=neta:studio_ai:news_show:006`, and the Commentator never saw the line it was
reacting to. The other three programmes' prompts were right; nothing checked that they had to be.

Held here on a real dispatcher, for EVERY declared programme and EVERY one of its roles:

  · the user message sent to the model contains the resolved source's body VERBATIM
  · a role that answers a previous line receives that line (`{last}`)
  · statically, no declared role prompt lacks `{source}` — every template gives every role one
  · a declaration whose prompt cannot carry the source stands by with
    `station:reason:prompt_without_source`, makes NO model call, and its row does not name the
    source it was never given
  · a source that resolves to no text stands by the same way (`waiting_source`), no call

Run:  python app/test/station_turn_grounding_eval.py     (exit 0 = all pass)
"""
import copy
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    from lib.akasha.workbench import llm_provider
    from lib.akasha.workbench import workload as _W
    from lib.akasha.workbench.workload_provision import provision
    from app.concepts import bench_station as BS

    decls = [c for c in _W.declarations(None) if (c.get("roles") or {})]

    print("\n  ── static: every declared role prompt can carry its source ──")
    missing = []
    for cfg in decls:
        for role, spec in (cfg.get("roles") or {}).items():
            if role.startswith("_") or not isinstance(spec, dict):
                continue
            if "{source}" not in (spec.get("prompt") or "{source}"):
                missing.append("%s/%s" % (_W.key(cfg), role))
    check("no declared role prompt lacks `{source}` (the news show's three did, from the port "
          "until 09-26)", not missing, str(missing))

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_ground_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(client, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": client, "data": data}, "id": "t"}, "local")

    def res(r):
        return (r or {}).get("result") or {}

    sent = []

    def capture(provider, model, system, user, timeout=60.0):
        sent.append({"system": system, "user": user})
        return "A grounded line."

    real_gen = llm_provider.generate
    llm_provider.generate = capture
    LAST = "THE PREVIOUS LINE, AS IT AIRED — marker 7c1e"
    try:
        print("\n  ── every programme, every role: the item is IN the message ──")
        for cfg in decls:
            program = _W.key(cfg)
            provision(d, cfg, note=lambda m: None)
            client = _W.client_of(cfg)
            body = "THE ITEM FOR %s, AS WRITTEN — marker %s" % (
                program, hashlib.sha1(program.encode()).hexdigest()[:6])
            atom = "test:ground:%s" % program.replace("/", ":")
            d("admin", "kernel.memory.define", {"name": atom, "description": body,
                                                "scope": "universal"})
            for role, spec in (cfg.get("roles") or {}).items():
                if role.startswith("_") or not isinstance(spec, dict):
                    continue
                n0 = len(sent)
                r = res(d(client, "station.air.turn",
                          {"program": program, "role": role, "source": atom, "last": LAST,
                           "provider": "mistral", "turn": "g:%s" % role}))
                msg = sent[-1]["user"] if len(sent) > n0 else ""
                check("%s / %s: the model is sent the source body verbatim" % (program, role),
                      len(sent) == n0 + 1 and body in msg,
                      "status=%s calls=%d" % (r.get("status"), len(sent) - n0))
                if "{last}" in (spec.get("prompt") or ""):
                    check("%s / %s: … and the line it answers" % (program, role), LAST in msg)

        print("\n  ── a prompt that cannot carry the source never reaches the model ──")
        cfg = next(c for c in decls if _W.key(c) == "studio_ai/news_show")
        program, client = _W.key(cfg), _W.client_of(cfg)
        broken = copy.deepcopy(cfg)
        broken["roles"]["Anchor"]["prompt"] = "Deliver today's item to camera."   # no {source}
        real_wl = BS.BenchStationConcept._workload
        BS.BenchStationConcept._workload = lambda self, key: broken if key == program else real_wl(self, key)
        n0 = len(sent)
        r = res(d(client, "station.air.turn",
                  {"program": program, "role": "Anchor", "source": "test:ground:studio_ai:news_show",
                   "provider": "mistral", "turn": "g:broken"}))
        BS.BenchStationConcept._workload = real_wl
        check("a resolved source with no `{source}` in the prompt stands by as "
              "`prompt_without_source`",
              r.get("reason") == "station:reason:prompt_without_source", json.dumps(r)[:120])
        check("… and NO model call is made — a turn that cannot be grounded costs nothing",
              len(sent) == n0, "calls=%d" % (len(sent) - n0))
        rows = [x for x in (res(d("admin", "station.air.ls",
                                  {"name": _W.bench_slug(cfg), "program": program})).get("aired")
                            or []) if x.get("turn") == "g:broken"]
        check("… and its row does NOT name the source it was never given",
              len(rows) == 1 and "test:ground" not in str(rows[0].get("source")),
              str(rows[:1])[:120])

        print("\n  ── a source with no text is not a source ──")
        # Both shapes an empty define really takes: a bare `[alias]` header (blank description)
        # and the store's placeholder `Conceptual hub: <alias>` (empty description). Each used to
        # reach the model as "today's item".
        for tag, desc in (("blank", " "), ("empty", "")):
            atom = "test:ground:%s" % tag
            d("admin", "kernel.memory.define", {"name": atom, "description": desc,
                                                "scope": "universal"})
            n0 = len(sent)
            r = res(d(client, "station.air.turn",
                      {"program": program, "role": "Anchor", "source": atom,
                       "provider": "mistral", "turn": "g:%s" % tag}))
            check("a source with no text (%s define) stands by as `waiting_source` — no model "
                  "call, no invented item" % tag,
                  r.get("reason") == "station:reason:waiting_source" and len(sent) == n0,
                  "reason=%s calls=%d" % (r.get("reason"), len(sent) - n0))

        print("\n  ── 演出: an item's `:angle` companion reaches the caster, and only the caster ──")
        nprog = next(c for c in decls if _W.key(c) == "studio_ai/news_show")
        ncl = _W.client_of(nprog)
        ANG = "THE ANGLE TO TAKE — marker 5a1f"
        d("admin", "kernel.memory.define", {"name": "test:ground:angled", "scope": "universal",
                                            "description": "AN ITEM WITH AN ANGLE — marker 9b2c"})
        d("admin", "kernel.memory.define", {"name": "test:ground:angled:angle", "scope": "universal",
                                            "description": ANG})
        seen = {}
        for role in ("Anchor", "Commentator", "Anchor.wrap"):
            n0 = len(sent)
            res(d(ncl, "station.air.turn", {"program": "studio_ai/news_show", "role": role,
                                          "source": "test:ground:angled", "last": LAST,
                                          "provider": "mistral", "turn": "g:ang:%s" % role}))
            seen[role] = sent[-1]["user"] if len(sent) > n0 else ""
        check("the Anchor is handed the item's angle, under its heading",
              ANG in seen["Anchor"] and "The angle to take" in seen["Anchor"], seen["Anchor"][-160:])
        check("…and so is the wrap", ANG in seen["Anchor.wrap"], seen["Anchor.wrap"][-160:])
        check("…but NOT the Commentator (its job is to push back)",
              seen["Commentator"] and ANG not in seen["Commentator"], seen["Commentator"][-120:])
        n0 = len(sent)
        res(d(ncl, "station.air.turn", {"program": "studio_ai/news_show", "role": "Anchor",
                                      "source": "test:ground:studio_ai:news_show",
                                      "provider": "mistral", "turn": "g:noang"}))
        m = sent[-1]["user"] if len(sent) > n0 else ""
        check("an item with NO angle leaves no heading and no literal `{angle}` in the message",
              m and "{angle}" not in m and "The angle to take" not in m, m[-120:])
        check("no message sent in this eval carries an unexpanded `{angle}` / `{source}` / `{last}`",
              not [x for x in sent if any(t in x["user"] for t in ("{angle}", "{source}", "{last}"))])
    finally:
        llm_provider.generate = real_gen

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — every declared programme's every role is sent its source verbatim (and the "
          "line it answers, where it answers one); no declared prompt lacks `{source}`; and a turn "
          "that cannot be grounded — a prompt with nowhere to put the source, or a source with no "
          "text — stands by with a reason, makes no model call, and names no source it was not "
          "given.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
