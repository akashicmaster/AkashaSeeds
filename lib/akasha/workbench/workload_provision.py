"""
workload_provision — a DECLARED workload provisions itself, from its declaration, with no operator.

Seed A slice 1 §2. The plan is DATA and the execution is a loop over it: every step is an ordinary
kernel call, in the order an operator would issue them, so there is no second write path and a
`--dry-run` is a print. Replaces `station_provision.py`, which read the legacy studio pair
(`station_studios.json` + `studio_*.json`) and could only describe a broadcast studio.

Three rules this file exists to hold:

**A declaration is a DESIRED STATE; a boot RECONCILES to it.** Every step is an ensure, so a pass
over a live cell changes only what does not match. There is no "provisioned already?" predicate and
no second path for the fresh case — the two-path version is what kept the Thinker's Shelf off the
air for two days, because its society existed and was armed (so the boot skipped the plan) while
the WORKFLOW ENTRIES its runs needed had never been written. *Armed is not provisioned.*

**A failure names ITSELF, in vocabulary, where it was decided.** A declaration missing a field is
`[bench] provision failed workload=<key> reason=<field>` — the field id, so the frontend knows
which line to look at. A missing template is `reason=template`. Neither is fatal to the boot and
neither is silent.

**Nothing here knows what a workload is ABOUT.** The group, the space, the bench, the casts and the
roles all come from the declaration. The bench's KIND is not even derived — it IS the declared
`effect`, so there is no table here translating one vocabulary into another.
"""
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Tuple

from lib.akasha.workbench import workload as W
from lib.akasha.api import gate as _gate

# `client_of` and `publishes_to_room` live in `workload.py` — they are questions about the
# DECLARATION, and this module is the provisioner, not their home. NOT re-exported here: a
# re-export for one and not the other is how a caller came to import the missing one and break.
logger = logging.getLogger("Akasha.Kernel")

ROOT = W.ROOT
# The templates are read from the declaration ROOT the API defines (`templates`, per bench) — the
# platform reads no file because of an application's name for it (the purge order, §1.3). The
# bench-less second directory this used to search existed on no tree and is gone.
from lib.akasha.api import reserved as _roots


def bench_kind(decl: Dict[str, Any]) -> str:
    """The `kind` the bench this workload runs on carries — the declared `bench_kind`, else the
    declared EFFECT id itself.

    There was a table here mapping `publish` → `station` and `record` → `learning`: two vocabularies
    for one fact, and one of them named a programme. The platform still maps nothing (order §3);
    what changed (26d) is that a declaration may STATE its bench's kind, because the lab's bench
    scaffold did and it is going. `bench.ls` shows it, and a reader of a bench row learns the same
    word the declaration used."""
    return W.bench_kind(decl)


def template_path(decl: Dict[str, Any]) -> str:
    """The workflow template for this workload — `config/workbench/<bench>/templates/<slug>.ak`.

    Derived from `bench` + `workflow`, never declared separately: two names for one file is two
    things to keep in step. Returns "" when the file is absent, which the caller reports as
    `reason=template` rather than provisioning a society whose runs can only fail."""
    slug = str(decl.get("workflow") or "").strip()
    return _template_named(decl, slug) if slug else ""


def templates_of(decl: Dict[str, Any]) -> List[Tuple[str, str]]:
    """(branch, template path or "") for every branch this workload runs: one per declared
    `workflows` name, or the one branch of the workflow slug."""
    if isinstance(decl.get("workflows"), list) and decl.get("workflows"):
        return [(name, _template_named(decl, name)) for name in W.workflows_of(decl)]
    return [(W.branch_of(decl), template_path(decl))]


def _template_named(decl: Dict[str, Any], name: str) -> str:
    """The template for one declared workflow NAME, searched like `template_path`."""
    p = os.path.join(_roots.root("templates", W.bench_slug(decl)), "%s.ak" % name)
    return p if os.path.exists(p) else ""


def _roles(decl: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    r = decl.get("roles") if isinstance(decl.get("roles"), dict) else {}
    return {str(k): (v if isinstance(v, dict) else {}) for k, v in r.items() if not k.startswith("_")}


def _cast_name(role: str) -> str:
    """The cast a role speaks as. `Anchor.wrap` is the Anchor speaking a third time, so a role
    keyed on role-plus-beat declares its `cast` and this returns that, not the key."""
    return role.split(".", 1)[0]


def plan(decl: Dict[str, Any]) -> List[Tuple[str, str, dict]]:
    """The provisioning plan as DATA — `[(client, method, data), …]`, for review and for `--dry-run`.

    Derived from the declaration alone, so it reads the same on a fresh deploy and on a provisioned
    cell (where executing it is a no-op)."""
    gid, space = W.society_of(decl)
    bench = W.bench_slug(decl)
    prog = W.client_of(decl)
    sp = decl.get("space") if isinstance(decl.get("space"), dict) else {}
    mod = decl.get("moderator") if isinstance(decl.get("moderator"), dict) else {}
    steps: List[Tuple[str, str, dict]] = [
        ("admin", "grp.new", {"group_id": gid, "admin_id": "admin"}),
        ("admin", "grp.add", {"group_id": gid, "member_id": "system.broadcaster"}),
        ("admin", "user.add", {"client_id": prog, "role": "user",
                               "passphrase_hash": hashlib.sha256(prog.encode()).hexdigest()}),
        ("admin", "grp.add", {"group_id": gid, "member_id": prog}),
        (prog, "society.new", {"group": gid, "space": space,
                               "topic": str(sp.get("topic") or space),
                               "category": str(sp.get("category") or ""),
                               "daily_budget": W.budget(decl)["per_day"],
                               "open_guest": "yes" if sp.get("open_guest") else "no",
                               "public": "yes" if sp.get("public") else "no"}),
    ]
    if sp.get("open_guest"):
        steps.append((prog, "society.guest", {"group": gid, "space": space, "open": "yes"}))
    if sp.get("public"):
        steps.append((prog, "society.public", {"group": gid, "space": space, "open": "yes"}))
    for role, spec in _roles(decl).items():
        cast = str(spec.get("cast") or _cast_name(role))
        steps.append((prog, "cast.new", {"name": cast,
                                         "identity": str(spec.get("identity") or cast)}))
    for who in (mod.get("chairman"), mod.get("scribe")):
        if who:
            steps.append((prog, "cast.new", {"name": str(who),
                                             "identity": "%s — holds responsibility, never a turn" % who}))
    steps += [
        ("admin", "society.broadcast.relay", {"group": gid, "space": space}),
        ("admin", "bench.new", dict({"name": bench, "kind": bench_kind(decl)},
                                    **({} if W.bench_public(decl) else {"group": gid}))),
        ("admin", "society.connect", {"group": gid, "space": space, "bench": bench}),
        (prog, "wf.new", {"bench": bench}),
        ("admin", "society.moderator", {"group": gid, "space": space, "mode": "auto",
                                        "policy": json.dumps(W.policy(decl), ensure_ascii=False)}),
    ]
    return steps


def provision(d, decl: Dict[str, Any], note=None, kernel_session=None) -> Dict[str, Any]:
    """Run the plan through `d(client, method, data) -> response envelope`. Returns a report dict.

    Best-effort and idempotent per step. The two steps whose failure leaves a workload LOOKING
    alive while being dead are reported explicitly: the guide registration (a programme missing
    from the guide is the silence the airing ruling forbids) and the workflow load (a bench with no
    workflow fails every run with `has no workflow`, which reads as a breaker)."""
    say = note or (lambda msg: logger.info("[bench] provision %s", msg))
    kernel_session = kernel_session or (lambda: None)
    gid, space = W.society_of(decl)
    bench, prog = W.bench_slug(decl), W.client_of(decl)
    wl_key = W.key(decl)
    report = {"workload": wl_key, "gid": gid, "space": space, "client": prog, "bench": "",
              "casts": {}, "registered": False, "armed": False, "entries": 0, "problems": []}

    def res(r):
        return (r or {}).get("result") or {}

    def problem(msg):
        report["problems"].append(msg)
        logger.warning("[bench] provision workload=%s problem=%s", wl_key, msg)

    d("admin", "grp.new", {"group_id": gid, "admin_id": "admin"})
    d("admin", "grp.add", {"group_id": gid, "member_id": "system.broadcaster"})
    d("admin", "user.add", {"client_id": prog, "role": "user",
                            "passphrase_hash": hashlib.sha256(prog.encode()).hexdigest()})
    d("admin", "grp.add", {"group_id": gid, "member_id": prog})
    # THE PROGRAMME'S ASSIGNMENT LINE (ruling §2: "provisioning appends the programmes"). The
    # account `user.add` just made carries the `member` row its IAM role maps to; what this
    # client actually IS is a programme ON ITS OWN WORKLOAD, and that is the line that lets it
    # run and say. Written here because provisioning is the only party that knows the pairing.
    # THE LINE IS THE DECLARATION'S (frontend 26b/26c): the ID set the declaration names for its
    # client — `programme` unless it says otherwise, and only a row whose `on` is `assigned` —
    # on each of the workload's OWN places, its space and its bench. A lab's client RECORDS on
    # its bench, and a line on the space alone never reached `<gid>/wb:<bench>`.
    # CONVERGE, don't append: a line this client holds on these places for a different ID set is
    # removed, so changing `idset` in the file changes the grant instead of adding to it.
    _want = W.idset_of(decl)
    _places = W.client_places(decl)
    for _place in _places:
        for _ln in list(_gate.lines_for(prog)):
            if str(_ln.get("on") or "") == _place and _ln.get("idset") != _want:
                _gate.unassign(prog, _ln.get("idset"), _place)
        _gate.assign(prog, _want, _place)
    # …and the bench's OTHER spelling is not a place of this workload: `bench_public` moves the
    # bench between `<gid>/wb:…` and `wb:…`, and the line on the one it left is removed.
    for _other in W.bench_places(decl):
        if _other in _places:
            continue
        for _ln in list(_gate.lines_for(prog)):
            if str(_ln.get("on") or "") == _other:
                _gate.unassign(prog, _ln.get("idset"), _other)

    # PROVISIONING RUNS AS ADMIN, all of it. It used to dispatch the society, the casts and the
    # workflow as the programme CLIENT, which was harmless while a client's role decided nothing
    # — and is wrong now that it does: `programme` is `run · say · annotate · publish`, so it may
    # not provision the space it speaks in nor record the casts it speaks as. That is the
    # ruling's shape, not an accident of it: the client SPEAKS, the operator PREPARES. One
    # authority (§A21), one gate question — `gate(admin, provision, key)`.

    sp = decl.get("space") if isinstance(decl.get("space"), dict) else {}
    _sn = {"group": gid, "space": space, "topic": str(sp.get("topic") or space),
           "category": str(sp.get("category") or ""),
           "daily_budget": W.budget(decl)["per_day"],
           "open_guest": "yes" if sp.get("open_guest") else "no",
           "public": "yes" if sp.get("public") else "no"}
    # `space.kind` / `space.identity` — the two society facts the lab's bench scaffold carried (26d).
    for _f in ("kind", "identity"):
        if sp.get(_f):
            _sn[_f] = str(sp[_f])
    d("admin", "society.new", _sn)
    if sp.get("open_guest"):
        d("admin", "society.guest", {"group": gid, "space": space, "open": "yes"})
    if sp.get("public"):
        d("admin", "society.public", {"group": gid, "space": space, "open": "yes"})

    # ── the casts: one per declared role, reused across boots ────────────────────────────────────
    casts: Dict[str, str] = {}
    existing = {c.get("name"): c.get("cast_id") for c in (res(d("admin", "cast.ls", {})).get("casts") or [])}
    wanted = {str(spec.get("cast") or _cast_name(role)): str(spec.get("identity") or role)
              for role, spec in _roles(decl).items()}
    mod = decl.get("moderator") if isinstance(decl.get("moderator"), dict) else {}
    for who in (mod.get("chairman"), mod.get("scribe")):
        if who:
            wanted.setdefault(str(who), "%s — holds responsibility, never a turn" % who)
    for name, identity in wanted.items():
        cid = existing.get(name)
        if cid:
            d("admin", "cast.open", {"id": cid})
        else:
            _r = d("admin", "cast.new", {"name": name, "identity": identity})
            cid = res(_r).get("cast_id")
            if not cid:
                problem("cast.new %s failed: %s" % (name, str((_r or {}).get("error"))[:140]))
        if cid:
            casts[name] = cid
            d("admin", "cast.publish", {"group": gid})
            d("admin", "society.join", {"group": gid, "space": space, "cast": cid})
            d("admin", "society.admit", {"group": gid, "space": space, "cast": cid, "client": prog})
    report["casts"] = dict(casts)

    # ── the guide: a scheduled workload appears BEFORE it has ever spoken ────────────────────────
    # `effect=publish` is what says this workload's output faces the public, so it is what decides
    # whether a guide row exists — not a test for what the society is called (order §1.3).
    if W.publishes_to_room(decl):
        rr = d("admin", "society.broadcast.relay", {"group": gid, "space": space}) or {}
        if res(rr).get("sid"):
            report["registered"] = True
        else:
            problem("not in the programme guide (its room reads `unclassified` until this "
                    "succeeds): %s" % (str(rr.get("error"))[:140] or "no sid returned"))

    # The bench must EXIST before the society connects to it. A PUBLIC bench (`bench_public`) is
    # created in the nucleus — no group — and is its own place `wb:<slug>`.
    _bn = {"name": bench, "kind": bench_kind(decl)}
    if not W.bench_public(decl):
        _bn["group"] = gid
    _bnr = res(d("admin", "bench.new", _bn))
    # `bench.new` is create-if-absent, so a bench that already exists keeps ITS placement and kind.
    # A placement that differs from the declaration is not cosmetic: the client's line is on the
    # declared place and every bench step is gated on the real one, so the lab would be refused
    # `out_of_scope` on every step (26d — the scaffold's public bench did exactly this). Said here,
    # by field id, where it is known.
    if _bnr.get("status") == "exists":
        _info = res(d("admin", "bench.info", {"name": bench, "group": gid}))
        _is_public = not _info.get("group")
        if _info and _is_public != W.bench_public(decl):
            problem("bench_public: wb:%s exists as a %s bench and the declaration places it %s — "
                    "its bench steps are gated on the existing place"
                    % (bench, "public" if _is_public else "group",
                       "in the nucleus" if W.bench_public(decl) else "in %s" % gid))
        if _info and str(_info.get("kind") or "") != bench_kind(decl):
            problem("bench_kind: wb:%s exists with kind %s, declared %s"
                    % (bench, _info.get("kind"), bench_kind(decl)))
    conn = d("admin", "society.connect", {"group": gid, "space": space, "bench": bench}) or {}
    if conn.get("error"):
        problem("society.connect bench=%s failed: %s" % (bench, str(conn["error"])[:120]))
    else:
        report["bench"] = res(conn).get("bench") or ("wb:" + bench)

    # The workload must be an OPERATOR of its own bench, or a turn generates and then cannot be
    # recorded — the feed and the bench record would disagree about what aired.
    for name, cid in casts.items():
        g = d("admin", "society.responsible",
              {"group": gid, "space": space, "kind": "operator:air", "cast": cid}) or {}
        if g.get("error"):
            problem("operator:air grant for %s failed: %s" % (name, str(g["error"])[:110]))
    # …and the responsibilities the declaration names for a cast (`grants`): a lab's casts operate
    # the bench's families (`operator:dataset`, `operator:train`, …) and decide.
    for name, kinds in sorted((decl.get("grants") or {}).items()):
        if str(name).startswith("_"):
            continue
        cid = casts.get(str(name))
        if not cid:
            problem("grants name cast %s, which the declaration does not provision" % name)
            continue
        for kind in kinds:
            g = d("admin", "society.responsible",
                  {"group": gid, "space": space, "kind": str(kind), "cast": cid}) or {}
            if g.get("error"):
                problem("%s grant for %s failed: %s" % (kind, name, str(g["error"])[:110]))

    # ── the GOVERNANCE casts (ruling, 2026-09-22) ────────────────────────────────────────────────
    # A governance cast is DATA this function creates, named by the declaration. Arming does not
    # check that it exists — `society.moderator mode=auto` asked that question a second time, about
    # an admission provisioning had already performed as admin, and refused exactly what the gate
    # admits. That precondition is deleted; the check belongs HERE, at the one place that can
    # actually do something about it, and its failure is this workload's failure:
    #
    #     [bench] provision failed workload=… reason=governance:<name>
    #
    # so a missing chairman or scribe is a named, actionable line at the moment it happens rather
    # than a workload that arms and then behaves oddly later.
    for _kind, _rel in (("chairman", ""), ("scribe", "scribe")):
        who = str(mod.get(_kind) or "").strip()
        if not who:
            continue
        cid = casts.get(who)
        if not cid:
            report["failed"] = "governance:%s" % who
            logger.warning("[bench] provision failed workload=%s reason=governance:%s", wl_key, who)
            return report
        if _rel:
            d("admin", "society.responsible", {"group": gid, "space": space, "kind": _rel,
                                               "cast": cid})
        else:
            d("admin", "society.chairman", {"group": gid, "space": space, "cast": cid})

    # ── the workflow on the declared bench, from the template ────────────────────────────────────
    d("admin", "wf.new", {"bench": bench})
    # One branch per declared workflow (`workflows`), each from the template of its own name; or
    # the one branch the workflow slug names. `wf.load … params=` and not `wf.branch`: the driver
    # runs these branches by name, while `wf.branch` DERIVES a name for a sweep arm.
    for branch, tpl in templates_of(decl):
        n = 0
        if tpl:
            ld = res(d("admin", "wf.load", {"bench": bench, "file": tpl, "branch": branch,
                                         "params": json.dumps(_params(decl), ensure_ascii=False)}))
            n = len(ld.get("written") or []) or int(ld.get("count") or 0)
            report["entries"] += n
        if not n:
            problem("no workflow entries on wb:%s/%s — every run of this workload would fail "
                    "`has no workflow`" % (bench, branch))
    # The declared sweeps: each `config/workbench/<bench>/sweeps/<name>.json` becomes a `sweep.def`
    # (the grid expands into conditions); the driver picks their branches after a static run.
    report["sweeps"] = 0
    for name in W.sweeps_of(decl):
        spath = os.path.join(ROOT, "config", "workbench", W.bench_slug(decl), "sweeps", name + ".json")
        try:
            with open(spath, encoding="utf-8") as f:
                sd = json.load(f)
        except (OSError, ValueError) as exc:
            problem("sweep %s unreadable at %s: %s" % (name, os.path.relpath(spath, ROOT), exc))
            continue
        r = d("admin", "sweep.def", {"bench": bench, "name": sd.get("name") or name,
                                  "grid": json.dumps(sd.get("grid") or {}),
                                  "max": str(sd.get("max") or 18),
                                  "template": sd.get("template") or "learn_observe",
                                  "fixed": json.dumps(sd.get("fixed") or {}),
                                  "budget": json.dumps(sd.get("budget") or {})}) or {}
        if r.get("error"):
            problem("sweep.def %s failed: %s" % (name, str(r["error"])[:120]))
        else:
            report["sweeps"] += 1
    say("workload=%s society=%s/%s bench=wb:%s entries=%d casts=%d"
        % (wl_key, gid, space, bench, report["entries"], len(casts)))

    # ── the guide row carries this workload's declared COST before it has ever run ───────────────
    # A scheduled workload shows what it will spend at provisioning time, not only after its first
    # airing: `bench.info`/the guide read `llm{calls_per_run}` and the accounting key off the row,
    # and a row that answers "unknown" until something happens is the same silence as no row.
    # THE STAMP IS GONE, and so is the row it stamped. A programme's declared cost — its accounting
    # key, its room, the calls one run needs, the provider, the daily budget — is in its
    # DECLARATION, which is the file this function is reading right now. Copying it onto a
    # platform-owned guide row made the declaration and the row two answers to one question, and
    # the row was the one a page happened to read. `workload.status` reports `spent_today` against
    # the declaration; the declaration is the cost.

    # ── armed: the driver airs it, no operator ───────────────────────────────────────────────────
    arm = d("admin", "society.moderator", {"group": gid, "space": space, "mode": "auto",
                                           "policy": json.dumps(W.policy(decl), ensure_ascii=False)}) or {}
    a = res(arm)
    if arm.get("error") or a.get("status") == "refused":
        problem("auto-arming refused: %s" % (a.get("reason") or str(arm.get("error"))[:140]))
    else:
        report["armed"] = True
    return report


def _params(decl: Dict[str, Any]) -> Dict[str, str]:
    """The template's `#!params` substitutions, from the declaration.

    A template step is a fixed line of data, so everything variable in it — the programme key, the
    group, the space, the bench, and every declared pin — is substituted at branch time. `pins` is
    exactly the set of things a template may need and the declaration may name, which is why it is
    one of the nine frozen fields rather than a per-template invention."""
    gid, space = W.society_of(decl)
    out = {"program": W.key(decl), "workload": W.key(decl), "group": gid, "space": space,
           "bench": W.bench_slug(decl), "slug": str(decl.get("workflow") or ""),
           "client": W.client_of(decl)}
    pins = decl.get("pins") if isinstance(decl.get("pins"), dict) else {}
    for k, v in pins.items():
        if not k.startswith("_") and isinstance(v, (str, int, float)):
            out[str(k)] = str(v)
    return out


def install_workload_stores(kernel) -> None:
    """The DURABLE stores any LLM-using workload needs, as a declared writer-phase schedule.

    These are not one programme's: they are what must be in place BEFORE anything reserves a model
    call — the 429 back-off window, the spend meter and the reservation pool, all backed by the
    shared-nucleus vault so a restart does not forget what it already spent. They ran from a
    launcher call before the 2026-09-20 layout order, and when that call became a generic thread
    start whose declared starter was the thread alone, all of it was silently lost: no boot line,
    the pool and the meter back in process memory, the back-off no longer inherited. They are a
    SCHEDULE for that reason — the boot reports them by name, and a failure is `status=error` on
    the phase line rather than a debug-level skip.

    Nothing here is best-effort: an exception propagates to `run_phase`, which names this body.

    Provisioning is NOT here. Arming a declared workload is `provision:schedule_workload_provision`,
    its own writer-phase body gated `after: ontology.loaded` because a template resolves ontology
    atoms. This body installs stores; it provisions nothing."""
    from lib.akasha.workbench import llm
    llm.install_llm_backoff_store(kernel)
    llm.install_llm_pool_store(kernel)
