#!/usr/bin/env python3
"""
The readiness gate's `requires` — the three kinds of requirement, and the one predicate behind them.

A declaration's `policy.requires` names what must be in place before the workload may run. There
are three kinds and they are told apart by their prefix, because they live in three different
places and only their own owner can answer for them:

    model:<name>   a binary bundled with the seed     — nothing to wait for at readiness time
    set:<name>     an ontology Set                    — ready when the Set has members
    <anything>     a source pool                      — ready when the SOURCE engine says frozen

Two defects came through this function with no eval standing in the way, which is why this file
exists at all:

  D4 (2026-09-24)  the fact `set:source:ready` held POOL NAMES while the gate asked by WORKLOAD
                   KEY, so step 4 could never pass for any workload, and `headroom` had no writer
                   whatsoever. A programme that was on air reported `gate.run=source_ready`.

  D7 (2026-09-25)  every non-`model:` entry was handed to `pool_frozen`, which asks about a POOL.
                   A declaration requiring `set:bio:plants:field_guide:ep1` therefore asked whether
                   a pool of that name was frozen, was told no by a pool that does not exist, and
                   waited for ever. The Plant Geek's declared wait was inert: it was not waiting
                   for the thing it had asked for, and no amount of loading could clear it.

  P6 (2026-09-25)  the D7 fix looked the requirement up VERBATIM — `set:bio:plants:…` — while an
                   `.ak` names its collection BARE (`set.add name="bio:plants:field_guide:ep1"`),
                   the convention by 40,880 uses to 1,587. The wait went from inert to evaluated-
                   and-never-ready. THIS EVAL PASSED OVER IT, because its fake store was keyed
                   `"set:bio:plants:field_guide:ep1"`: it compared the code to itself, so no
                   `.ak` naming could ever disagree with it. A check that cannot see the thing it
                   is checking — the same shape as the `[A]` anchors in P5.

                   So the fixture is no longer written here. It is PARSED FROM THE REAL PACK
                   (`app/ontology/biology/field_guide_ep1.ak`) and the requirement is READ FROM THE
                   REAL DECLARATION (`app/config/workbench/workloads/plant_geek.json`), and the last
                   section replays that pack through a REAL kernel's `set.add` and asks the real
                   store. If either file changes its spelling, this eval sees the change.

The deciding (`workload_source_ready`, which writes the gate's fact) and the naming
(`requires_missing`, which lists what is not ready so a room can say so) now go through ONE
predicate, `provision.requirement_ready`. Two readings of one question are two readings that can
disagree — and once a `set:` requirement existed, they did.

Run:  python app/test/workbench_requires_eval.py     (exit 0 = all pass)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

import hashlib                                                  # noqa: E402
import json                                                     # noqa: E402
import re                                                       # noqa: E402
import shlex                                                    # noqa: E402
import tempfile                                                 # noqa: E402

from lib.akasha.workbench import provision, autorun          # noqa: E402

_fails = []

PACK = os.path.join(ROOT, "app", "ontology", "biology", "field_guide_ep1.ak")
DECL = os.path.join(ROOT, "app", "config", "workbench", "workloads", "plant_geek.json")
_KW = re.compile(r"^[A-Za-z_][\w.:-]*$")          # the loader's own kwarg-key rule
_AK = {"def": ("kernel.memory.define", ["name", "description"]),
       "al": ("alias", ["id", "name"]),
       "set.add": ("set.add", ["name", "id"])}


def _pack_steps(path):
    """The pack's atom-phase steps, parsed as `ontology/loader.py` parses them: shlex-split, a
    kwarg only when its key is an identifier, positional otherwise, `def` scoped universal. Kept
    to the three commands that decide what a Set is CALLED — `ln` names no collection."""
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = shlex.split(line)
        if parts[0].lower() not in _AK:
            continue
        method, names = _AK[parts[0].lower()]
        kw, pos = {}, []
        for tok in parts[1:]:
            if "=" in tok and _KW.match(tok.split("=", 1)[0].strip()):
                a, b = tok.split("=", 1)
                kw[a] = b
                continue
            pos.append(tok)
        p = {n: kw.get(n, pos[i] if i < len(pos) else "") for i, n in enumerate(names)}
        if method == "kernel.memory.define":
            p["scope"] = "universal"
        yield method, p


def _pack_sets(path):
    """{collection name AS THE PACK WRITES IT: [member ids]} — never a name typed into this file."""
    out = {}
    for method, p in _pack_steps(path):
        if method == "set.add":
            out.setdefault(p["name"], []).append(p["id"])
    return out


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Core:
    def __init__(self, sets):
        self._sets = sets

    def get_collection_members(self, name):
        return list(self._sets.get(name) or [])


class _Kernel:
    """The two doors `requirement_ready` reaches through: the shared nucleus (for an ontology Set)
    and the RPC dispatcher (for a source pool). Nothing else is needed — which is the point."""

    def __init__(self, sets=None, frozen_pools=()):
        self.manager = type("M", (), {"shared_nucleus": type("N", (), {"core": _Core(sets or {})})()})()
        self._frozen = set(frozen_pools)
        self.calls = []

    def dispatch(self, payload, trust=None):
        pool = ((payload.get("params") or {}).get("data") or {}).get("pool")
        self.calls.append(pool)
        if pool in self._frozen:
            return {"result": {"frozen": True, "total": 42}}
        return {"result": {"frozen": False, "total": 0}}


def main():
    print("=" * 78)
    print("The readiness gate's `requires`: model: / set: / pool, and one predicate for all three")
    print("=" * 78)
    print("\n  ── the three kinds ──")

    pack_sets = _pack_sets(PACK)
    decl = json.load(open(DECL, encoding="utf-8"))
    req = [r for r in (decl.get("requires") or []) if str(r).startswith("set:")]
    check("the fixture is PARSED FROM THE PACK, and the pack names its episode Set",
          any(n.endswith("field_guide:ep1") for n in pack_sets), sorted(pack_sets))
    check("the requirement is READ FROM THE DECLARATION, and it is a `set:` requirement",
          len(req) == 1, str(decl.get("requires")))
    # The one thing the previous version of this file could never do: DISAGREE with the code. The
    # pack's spelling and the declaration's spelling are two different strings, and this check is
    # here to prove the eval is looking at both — if they were ever identical the lookup would be
    # trivially right and the rest of this file would test nothing.
    check("…and the pack's spelling and the declaration's are DIFFERENT strings (bare vs `set:`)",
          req and req[0] not in pack_sets and req[0][len("set:"):] in pack_sets,
          "decl=%s pack=%s" % (req, sorted(pack_sets)))
    # The 3.7% are real too: the platform's own fact Sets carry `set:` IN their stored name.
    k = _Kernel(sets=dict(pack_sets, **{"set:wl:declared": ["studio_ai/news_show"]}),
                frozen_pools=("source:pool:plants:v1",))
    SET_REQ = req[0] if req else "set:bio:plants:field_guide:ep1"
    ABSENT = "set:bio:plants:field_guide:ep2"

    check("a `model:` requirement is ready — the binary ships with the seed, there is no wait",
          provision.requirement_ready(k, "model:mobilenet_v3_small_fv.tflite"))
    check("…and it never asks the source engine about a pool of that name",
          "model:mobilenet_v3_small_fv.tflite" not in k.calls, str(k.calls))

    check("the Plant Geek's OWN requirement is READY against the pack's OWN spelling (P6)",
          provision.requirement_ready(k, SET_REQ), SET_REQ)
    check("…a Set the pack never filled is not ready: an empty Set and an unloaded pack are the "
          "same state", not provision.requirement_ready(k, ABSENT))
    check("…and a Set genuinely stored WITH the prefix (the platform's own fact Sets, 1,587 of "
          "them) is found too — both spellings, bare first",
          provision.requirement_ready(k, "set:wl:declared"))
    check("…and a `set:` requirement is never asked of the source engine — it was never a pool",
          not [c for c in k.calls if str(c).startswith("set:")], str(k.calls))

    check("a POOL requirement is ready when the source engine says frozen and non-empty",
          provision.requirement_ready(k, "source:pool:plants:v1"))
    check("…and not when it is absent or open",
          not provision.requirement_ready(k, "source:pool:nothing:v1"))

    print("\n  ── the fact the gate reads is written from that predicate ──")
    # The declaration's OWN shape: `requires` is a top-level field (as in
    # `app/config/workbench/workloads/plant_geek.json`), which `workload.policy` copies into the
    # policy the driver reads. Writing it under `policy` here made four checks pass on an empty
    # requirement list instead of on the requirement — the fixture has to be the real shape or the
    # eval tests nothing.
    check("THE REAL DECLARATION, against the REAL PACK's Set, is source-ready",
          provision.workload_source_ready(k, decl) is True)
    _decl_empty = dict(decl, requires=[ABSENT])
    check("…and one whose Set has not landed is not",
          provision.workload_source_ready(k, _decl_empty) is False)
    check("a workload that requires NOTHING is ready — the absence of a wait is not a wait",
          provision.workload_source_ready(k, {"workload": "w"}) is True)
    _mixed = {"workload": "w", "requires": ["model:m.tflite", SET_REQ, "source:pool:plants:v1"]}
    check("all three kinds in one declaration, each answered by its own owner",
          provision.workload_source_ready(k, _mixed) is True)
    _mixed_bad = dict(_mixed, requires=["model:m.tflite", ABSENT, "source:pool:plants:v1"])
    check("…and one unmet entry of any kind withholds the whole workload",
          provision.workload_source_ready(k, _mixed_bad) is False)

    print("\n  ── the list that NAMES the wait cannot contradict the fact that DECIDES it ──")
    # `requires_missing` with no workload key takes the no-fact path, where each entry answers for
    # itself — the same predicate the fact is written from. Before D7 this asked `pool_frozen`
    # directly and named every `set:` entry as missing whether or not its pack had landed, so the
    # room's reason and the gate's decision could disagree about the same declaration.
    _req = [SET_REQ, ABSENT, "source:pool:plants:v1", "source:pool:nothing:v1"]
    missing = autorun.requires_missing(k, _req, wl_key="")
    check("a filled Set is NOT named as missing", SET_REQ not in missing, str(missing))
    check("an unfilled Set IS named, and so is an unfrozen pool",
          ABSENT in missing and "source:pool:nothing:v1" in missing, str(missing))
    check("a frozen pool is not named", "source:pool:plants:v1" not in missing, str(missing))
    check("the namer agrees with the decider on every entry, one at a time",
          all((r in missing) != provision.requirement_ready(k, r) for r in _req), str(missing))

    print("\n  ── provisioning does not bind a non-pool as a pool ──")
    src = open(os.path.join(ROOT, "lib/akasha/workbench/provision.py"), encoding="utf-8").read()
    check("the `bench.bind_pool` implementer is handed only `source:pool:` entries (never a `model:` "
          "or a `set:`) when the declared workload's bench is grounded",
          'pools = [r for r in want if r.startswith("source:pool:")]' in src
          and "bound = _bind_bench_pools(kernel, decl, pools)" in src
          and '"data": {"name": workload.bench_slug(decl), "pool": pool}' in src)

    print("\n  ── the same question asked of a REAL kernel, with the REAL pack replayed into it ──")
    # The fake above is only as good as its idea of how a store names a collection. So the pack is
    # replayed step for step — the loader's own parse, the kernel's own `set.add` — into a real
    # cell's shared nucleus, and the predicate is asked of THAT. This is the measurement P6 made by
    # hand: the collection lands under the bare name and nothing lands under the prefixed one.
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    rk = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="requires_eval_"))

    def _d(method, data):
        return rk.dispatch({"jsonrpc": "2.0", "method": method,
                            "params": {"session_token": "henri", "data": data}, "id": "r"}, "local")
    _d("kernel.genesis_rite", {"user_name": "henri",
                               "passphrase": hashlib.sha256(b"pw").hexdigest()})
    errs = [m for m, p in _pack_steps(PACK) if "error" in _d(m, p)]
    core = rk.manager.shared_nucleus.core
    bare_n = len(core.get_collection_members(SET_REQ[len("set:"):]) or [])
    pref_n = len(core.get_collection_members(SET_REQ) or [])
    check("the real pack replays into a real cell with no step refused", not errs,
          "%d refused" % len(errs))
    check("…and the real store holds the episode under the BARE name, nothing under `set:`",
          bare_n == len(pack_sets.get(SET_REQ[len("set:"):]) or []) and bare_n > 0 and pref_n == 0,
          "bare=%d prefixed=%d" % (bare_n, pref_n))
    check("the predicate, asked of the real kernel, answers READY for the real declaration",
          provision.requirement_ready(rk, SET_REQ)
          and provision.workload_source_ready(rk, decl) is True)
    check("…and an episode the pack never wrote is still not ready on the real kernel",
          not provision.requirement_ready(rk, ABSENT))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — `requires` tells its three kinds apart by prefix; a `set:` requirement "
          "finds the Set under the name the PACK gave it (bare first, then literal), checked "
          "against the real pack and the real declaration on a real kernel; and the fact that "
          "decides and the list that explains are one predicate, so they cannot disagree.")
    sys.exit(0)


if __name__ == "__main__":
    main()
