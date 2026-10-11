#!/usr/bin/env python3
"""
The four station workloads, held to the frozen declaration shape — and to ONE source.

Frontend order 2026-09-21 §2. The station's four programmes are declared as WORKLOADS in the shape
its §5 freezes, and each has a template on `wb:studio_ai`. Seed A brings the platform half — the
provisioning that reads this shape, the driver that reads its five fields, and
`workload_conformance_eval`, which is where the two roles meet. None of that exists yet, so this
eval holds the USER half on its own: that what seed A will read is there, well-formed, complete, and
written exactly once.

The last clause used to need machinery. While the old driver still read the pair
(`station_studios.json` + `studio_*.json`), those files were kept as a mechanical PROJECTION of
these four so that no value was written twice. Step 1 deleted the pair and its generator, so §6
now holds the thing the projection was protecting: the declaration is the only place a programme is
written down, and every role a template plays carries its own prompt and identity there.

What is checked:

  §1  the frozen shape — every required field, of the right kind, with vocabulary where the code
      will compare (duty is a `wb:duty:*` id that the lexicon defines, effect is publish|execute)
  §2  the key `<bench>/<workflow>` is the file's own name, so a key can never disagree with the
      declaration it is read from
  §3  the room is DERIVED from the slug — or declares an override and says why
  §4  the template exists, carries `#!params`, calls only ops that exist, names only roles the
      workload declares, and spells no state or reason as a literal
  §5  every role that speaks is offered the capabilities its turn needs, and an effectful offer
      appears only under `effect: publish`
  §6  ONE declaration — no projected pair survives, and every role a template plays
      carries its own prompt and identity there (the platform's copies die in step 2)

Run:  python app/test/station_workload_decl_eval.py        (exit 0 = all pass)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
WORKLOADS = os.path.join(ROOT, "app", "config", "workbench", "workloads")
TEMPLATES = os.path.join(ROOT, "app", "config", "workbench", "studio_ai", "templates")
# The four programmes, and the one workload that republishes one of them to an external channel.
# `news_show_x` is here to prove the shape holds for a workload that speaks into no society, calls
# no model and renders no room — if it needed an exception, `publish` would be two things.
SLUGS = ["news_show", "thinkers_shelf", "art_explorer", "plant_geek", "news_show_x"]
# A workload with roles SPEAKS: it has a society, a room and an appetite. One without roles
# republishes what another already said. The difference is declared, not guessed from a name.
SPEAKING = ["news_show", "thinkers_shelf", "art_explorer", "plant_geek"]

# The fields §5 freezes. A workload the driver can read is one that carries all of them.
REQUIRED = ["bench", "workflow", "society", "trigger", "duty", "effect", "appetite", "budget", "pins"]
DUTIES = {"wb:duty:continuous", "wb:duty:best_effort"}
EFFECTS = {"publish", "execute"}
# An offer whose family leaves the world. `cap.py` holds the same two families as the kernel-level
# effectful set; a workload that offers one without declaring `effect: publish` is asking a role to
# do something its own declaration says it will not do.
EFFECTFUL_FAMILIES = {"station", "x_broadcast", "society"}

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def load(slug):
    with open(os.path.join(WORKLOADS, slug + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


def template_steps(slug):
    """(params, steps) of a template — the `#!params` header and the non-comment lines."""
    with open(os.path.join(TEMPLATES, slug + ".ak"), encoding="utf-8") as fh:
        raw = fh.read().splitlines()
    params, steps = {}, []
    for ln in raw:
        s = ln.strip()
        if s.startswith("#!params"):
            params.update(dict(t.split("=", 1) for t in s[len("#!params"):].split() if "=" in t))
        elif s and not s.startswith("#"):
            steps.append(s)
    return params, steps


def known_methods():
    """Every method a concept model declares, as `<prefix>.<suffix>`, plus the generated access
    table. A template step that names anything else would never run — and the failure would arrive
    hours later, at the first airing, instead of at the load."""
    names = set()
    try:
        from lib.akasha.kernel_methods import METHOD_TO_ACTION
        names |= set(METHOD_TO_ACTION)
    except Exception:
        pass
    import importlib
    import pkgutil
    import app.concepts as _app_pkg                  # the application's Concept Models (app/concepts) ...
    import lib.akasha.concepts as _plat_pkg          # ... and the platform's (society, chronon, …)
    for pkg, base in ((_app_pkg, "app.concepts."), (_plat_pkg, "lib.akasha.concepts.")):
        for mod in pkgutil.iter_modules(pkg.__path__):
            if mod.name.startswith("_"):
                continue
            try:
                m = importlib.import_module(base + mod.name)
            except Exception:
                continue
            for obj in vars(m).values():
                pref = getattr(obj, "CONCEPT_PREFIX", None)
                meths = getattr(obj, "CONCEPT_METHODS", None)
                if isinstance(pref, str) and isinstance(meths, dict):
                    names |= {"%s.%s" % (pref, s_) for s_ in meths}
    return names


def main():
    ws = {}
    print("\n  ── §1 · the frozen declaration shape ──")
    for slug in SLUGS:
        try:
            w = ws[slug] = load(slug)
        except (OSError, ValueError) as exc:
            check("%s is a readable declaration" % slug, False, str(exc)[:70])
            continue
        missing = [f for f in REQUIRED if f not in w]
        check("%s carries every field §5 freezes" % slug, not missing, "missing=%s" % missing)
        check("%s is on the station bench" % slug, w.get("bench") == "wb:studio_ai", str(w.get("bench")))
        check("%s declares a DUTY from the vocabulary, not a word" % slug,
              w.get("duty") in DUTIES, str(w.get("duty")))
        check("%s declares an effect the driver knows" % slug,
              w.get("effect") in EFFECTS, str(w.get("effect")))
        tr = w.get("trigger") or {}
        # `boot` is not "does a deploy fire it?" — it is "is it SCHEDULED at all?". The platform
        # projects a declaration without it to `trigger: manual`, and a manual workload never runs
        # on its `then` cadence. So every workload meant to run declares it true; a deploy opening
        # on a blank room is the other half of the same rule.
        check("%s is scheduled — `boot` is what arms it, not merely what fires it once" % slug,
              tr.get("boot") is True, json.dumps(tr))
        check("%s says what happens after the boot run" % slug,
              bool(re.match(r"^(daily:\d\d:\d\d Z?|daily:\d\d:\d\dZ|every:\d+s)$",
                            str(tr.get("then") or ""))), str(tr.get("then")))
        app, b = w.get("appetite") or {}, w.get("budget") or {}
        # ZERO is a real appetite, not a missing one: a workload that republishes what another
        # already generated makes no model call, and reserving for it would hold calls nobody
        # spends. What must never be absent is the declaration of how much it wants.
        _want = app.get("llm_calls_per_run")
        check("%s declares its appetite in model calls per run" % slug,
              isinstance(_want, int) and _want >= 0 and (_want > 0) == (slug in SPEAKING),
              "%s (speaks=%s)" % (_want, slug in SPEAKING))
        check("%s bounds its day and its wall clock" % slug,
              isinstance(b.get("per_day"), int) and b["per_day"] > 0
              and isinstance(b.get("max_wall_s"), int) and b["max_wall_s"] > 0, json.dumps(b))
        check("%s declares pins (may be empty, never absent)" % slug,
              isinstance(w.get("pins"), dict))

    print("\n  ── the duty vocabulary is DEFINED, not spelled ──")
    duty_pack = open(os.path.join(ROOT, "ontology", "workbench", "duty.ak"), encoding="utf-8").read()
    for d in sorted({w.get("duty") for w in ws.values() if w.get("duty")}):
        check("%s is defined in the lexicon" % d, ('def "%s"' % d) in duty_pack)

    print("\n  ── §2 · the key is the file, and the file is the key ──")
    for slug, w in ws.items():
        key = "%s/%s" % (str(w.get("bench", "")).replace("wb:", ""), w.get("workflow", ""))
        check("%s's key is %s" % (slug, key), w.get("workflow") == slug and key.endswith("/" + slug), key)
        check("%s's society is one per programme under one group" % slug,
              str(w.get("society") or "").split("/")[0] == "studio_ai", str(w.get("society")))

    print("\n  ── §3 · the room is derived from the slug, or says why not ──")
    for slug, w in ((s_, w_) for s_, w_ in ws.items() if s_ in SPEAKING):
        derived = "/station/%s/" % slug.replace("_", "-")
        if w.get("room"):
            check("%s declares a room AND the reason it does not derive" % slug,
                  bool(w.get("_room_override_reason")), str(w.get("room")))
        else:
            check("%s derives its room (%s)" % (slug, derived),
                  os.path.isdir(os.path.join(ROOT, "app", "archives", "station", slug.replace("_", "-"))),
                  derived)
        room = w.get("room") or derived
        check("%s's room is a public path, not a repo path" % slug,
              room.startswith("/") and "app/archives/" not in room, room)

    print("\n  ── §4 · the template: real ops, declared roles, no literal state ──")
    known = known_methods()
    for slug, w in ws.items():
        path = os.path.join(TEMPLATES, slug + ".ak")
        if not os.path.exists(path):
            check("%s has a template" % slug, False, path)
            continue
        params, steps = template_steps(slug)
        check("%s's template declares #!params" % slug, bool(params), json.dumps(params))
        _key = "%s/%s" % (w["bench"].replace("wb:", ""), w["workflow"])
        _want_prog = _key if slug in SPEAKING else (w.get("pins") or {}).get("program")
        check("… whose program default is the key it acts on",
              params.get("program") == _want_prog,
              "%s: %s (wanted %s)" % (slug, params.get("program"), _want_prog))
        check("%s's template has steps" % slug, bool(steps), "steps=%d" % len(steps))
        methods = {s.split()[0] for s in steps}
        unknown = sorted(m for m in methods if m not in known)
        check("%s's steps all name ops that exist" % slug, not unknown, "unknown=%s" % unknown)
        roles = {s.split("role=", 1)[1].split()[0] for s in steps if "role=" in s}
        undeclared = sorted(r for r in roles if r not in (w.get("roles") or {}))
        check("%s's steps only play roles the workload declares" % slug,
              not undeclared, "undeclared=%s" % undeclared)
        src = open(path, encoding="utf-8").read()
        check("%s's template spells no state or reason as a literal" % slug,
              "station:state:" not in "\n".join(steps) and "station:reason:" not in "\n".join(steps),
              "(prose in comments is fine; a STEP must not compare a literal)")
        check("%s's template carries no repo path" % slug,
              "config/" not in "\n".join(steps) and "app/archives/" not in "\n".join(steps))
        if slug in SPEAKING:
            # The mirror is the LAST step, in the same job as the turns: a room's liveness used to
            # depend on a platform thread nobody could see from the programme, and a programme that
            # did not air must not mirror.
            check("%s mirrors what it aired, as its last step" % slug,
                  steps[-1].startswith("society.broadcast.relay society="), steps[-1][:60])

    print("\n  ── §5 · every speaking role is offered what its turn needs ──")
    for slug, w in ((s_, w_) for s_, w_ in ws.items() if s_ in SPEAKING):
        roles = {k: v for k, v in (w.get("roles") or {}).items() if not k.startswith("_")}
        offers = {k: v for k, v in (w.get("offers") or {}).items() if not k.startswith("_")}
        mod = w.get("moderator") or {}
        # A capability is offered to the CAST that speaks, not to the beat. `Anchor.wrap` is the
        # news anchor speaking a third time — a separate beat, not a separate voice — so it holds
        # the Anchor's offer and must not be given one of its own.
        speaking = [(r, spec.get("cast") or r) for r, spec in roles.items() if spec.get("aired")]
        check("%s offers a capability set to every speaking role" % slug,
              all(c in offers for _r, c in speaking),
              "unoffered=%s" % sorted({c for _r, c in speaking if c not in offers}))
        for r, cast in speaking:
            fams = {str(c).split(":")[0] for c in (offers.get(cast) or [])}
            check("%s/%s may speak and may air" % (slug, r),
                  {"society", "station"} <= fams, str(sorted(offers.get(cast) or [])))
        voices = {c for _r, c in speaking} | {mod.get("chairman"), mod.get("scribe")} - {None, ""}
        check("%s offers nothing to a voice that does not exist" % slug,
              not (set(offers) - voices), "orphan=%s" % sorted(set(offers) - voices))
        eff = sorted({c for cs in offers.values() for c in cs
                      if str(c).split(":")[0] in EFFECTFUL_FAMILIES})
        check("%s offers an effectful capability only under effect=publish" % slug,
              (not eff) or w.get("effect") == "publish", "%s effect=%s" % (eff[:3], w.get("effect")))
        check("%s names a chairman AND a scribe (an autonomous act needs a keeper of the record)"
              % slug, bool(mod.get("chairman") and mod.get("scribe")), json.dumps(mod)[:70])
        for who in (mod.get("chairman"), mod.get("scribe")):
            check("%s's %s holds responsibility and never a turn" % (slug, who),
                  who not in roles, who)

    print("\n  ── §6 · ONE declaration, and the prompts still live in it ──")
    # The projection is gone (step 1 §1.2): the pair the old driver read — `station_studios.json`
    # and the `studio_*.json` / `studio_*_cycle.ak` files generated from these four — is deleted
    # along with its generator. This section used to prove the projection was in sync with its
    # source. There is no projection now, so it proves the thing that mattered underneath: the
    # declaration is the ONLY place a programme is written down.
    leftovers = sorted(os.path.basename(p) for p in
                       glob.glob(os.path.join(WORKLOADS, "station_studios.json"))
                       + glob.glob(os.path.join(WORKLOADS, "studio_*.json"))
                       + glob.glob(os.path.join(WORKLOADS, "studio_*_cycle.ak")))
    check("no projected pair survives beside the declarations", not leftovers, str(leftovers))
    # Spelled as a GLOB rather than a literal path, and deliberately. The crystallizer scans a
    # bundled eval for `os.path.join("scripts", "<name>.py")` to learn which tools that eval needs
    # shipped beside it — a good check, and one that cannot tell "this eval runs that script" from
    # "this eval asserts that script is gone". Writing the name as a pattern says the second.
    check("… and its generator is gone with it",
          not glob.glob(os.path.join(ROOT, "scripts", "station_legacy_*.py")))
    # §1.5 — the platform's `station_prompt` / `station_identity` / `station_content` are the
    # daemon's copies and die in step 2. Nothing may rely on them, so every role a template plays
    # carries its own prompt and identity HERE.
    for slug, w in ((s_, w_) for s_, w_ in ws.items() if s_ in SPEAKING):
        played = {ln.split("role=", 1)[1].split()[0]
                  for ln in template_steps(slug)[1] if "role=" in ln}
        for role in sorted(played):
            spec = (w.get("roles") or {}).get(role) or {}
            check("%s/%s carries its own prompt and identity in the declaration" % (slug, role),
                  bool(spec.get("prompt")) and bool(spec.get("identity")),
                  "prompt=%s identity=%s" % (bool(spec.get("prompt")), bool(spec.get("identity"))))

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the station's four programmes are declared as workloads in the frozen "
          "shape, each with a template whose steps name real ops and declared roles; every key, "
          "room, duty and effect comes from the declaration; and the projected pair is gone, so a "
          "programme is written down in exactly one place, prompts and all.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
