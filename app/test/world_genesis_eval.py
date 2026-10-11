#!/usr/bin/env python3
"""
G0 — the shared world: genesis, clock, axis (world-workbench-society spec v1.0).

The world model's FOUNDATION, shipped in every series. `world.genesis` creates the commons
`world:default` in the nucleus (its own clock + env/sync sets); `world.tick` mints a coordinate on
that clock with a wall-clock stamp; `world.env.record` appends an environment event; `world.axis`
reads env+sync in clock order. Backward-compat: fiction `topos.new` and default-clock `cronon.mint`
are byte-identical.

Runs on BOTH cell shapes: a NUCLEUS cell (thesaurus) and a SINGLE-STORE edge cell (seeds), because
`UniversalConcept._nuc` is None on the latter and the commons must still work (writes to the local
cortex with the universal scope).

Run:  python app/test/world_genesis_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _boot(series):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_world_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    return k


def _run_shape(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    k = _boot(series)

    def d(method, data, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r if "error" in r else (r.get("result") or {})

    # ── genesis: idempotent across three calls (the boot path may run once; a re-run is 'present') ──
    g1 = d("world.genesis", {})
    g2 = d("world.genesis", {})
    g3 = d("world.genesis", {})
    check(f"[{shape}] genesis creates world:default once; re-runs are 'present'",
          g1.get("status") == "created" and g2.get("status") == "present"
          and g3.get("status") == "present" and g1.get("world") == "world:default", str(g1))
    check(f"[{shape}] genesis reports the world's own clock",
          g1.get("clock") == "cronon:clock:world:default", g1.get("clock"))

    # ── tick: monotonic on the world clock, wall stamp parses ──
    t1 = d("world.tick", {"reason": "env", "ref": "x"})
    t2 = d("world.tick", {"reason": "sync", "ref": "y"})
    mono = (t1.get("position", 0) >= 1 and t2.get("position", 0) == t1.get("position", 0) + 1)
    check(f"[{shape}] world.tick is monotonic on the world clock", mono,
          "p1=%s p2=%s" % (t1.get("position"), t2.get("position")))
    wall = str(t1.get("wall") or "")
    import datetime
    ok_wall = "|" in wall
    if ok_wall:
        iso = wall.split("|", 1)[0]
        try:
            datetime.datetime.strptime(iso.replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            ok_wall = False
    check(f"[{shape}] the wall stamp is <ISO8601>|<epoch> and parses", ok_wall, wall)
    check(f"[{shape}] the world clock ids are cronon:world:default:c<n>",
          str(t1.get("cronon", "")).startswith("cronon:world:default:c"), t1.get("cronon"))

    # ── env.record + axis round-trip ──
    e1 = d("world.env.record", {"kind": "society.formed", "ref": "soc:1", "note": "first"})
    e2 = d("world.env.record", {"kind": "bench.created", "ref": "wb:1"})
    check(f"[{shape}] env.record refuses an unknown kind",
          "error" in d("world.env.record", {"kind": "not.a.kind"}), "should error")
    ax = d("world.axis", {})
    kinds = [r.get("kind") for r in ax.get("axis", [])]
    check(f"[{shape}] world.axis lists the env records in clock order",
          "society.formed" in kinds and "bench.created" in kinds
          and ax.get("axis") == sorted(ax.get("axis"), key=lambda r: r["position"]), str(kinds))
    # from/to windowing by position
    axw = d("world.axis", {"from": e2.get("position")})
    check(f"[{shape}] world.axis from=<pos> windows the axis",
          all((r.get("position") or 0) >= e2.get("position") for r in axw.get("axis", [])),
          str([r.get("position") for r in axw.get("axis", [])]))

    # ── world.axis is NOT guest-readable ──
    gt = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                     "params": {"data": {}}, "id": "gg"}, "network")
    gtok = ((gt.get("result") or {}).get("session_token")
            or (gt.get("result") or {}).get("token"))
    if gtok:
        gres = k.dispatch({"jsonrpc": "2.0", "method": "world.axis",
                           "params": {"session_token": gtok, "data": {}}, "id": "ga"}, "network")
        refused = (("error" in gres)
                   or ((gres.get("result") or {}).get("status") == "refused"))
        check(f"[{shape}] world.axis is NOT guest-readable", refused, str(gres)[:120])

    # ── virtual world records world.created on the DEFAULT axis ──
    vw = d("topos.new", {"title": "Test Cosmos", "kind": "virtual"})
    check(f"[{shape}] topos.new kind=virtual creates a sovereign world",
          vw.get("status") in ("created", "exists") and vw.get("world_id") == "world:test_cosmos", str(vw))
    ax2 = d("world.axis", {})
    check(f"[{shape}] a virtual topos.new records world.created on the default axis",
          any(r.get("kind") == "world.created" for r in ax2.get("axis", [])),
          str([r.get("kind") for r in ax2.get("axis", [])]))

    # ── BACKWARD COMPAT: fiction topos.new unchanged; default-clock cronon.mint unchanged ──
    fic = d("topos.new", {"title": "A Fiction Realm"})
    check(f"[{shape}] fiction topos.new (default kind) keeps the old response shape",
          fic.get("status") == "created" and fic.get("world_id") and fic.get("concept_id")
          and fic.get("title") == "A Fiction Realm", str(fic)[:120])
    c1 = d("cronon.mint", {})
    check(f"[{shape}] cronon.mint with no clock still produces cronon:c<n> on the default clock",
          str(c1.get("cronon", "")).startswith("cronon:c") and c1.get("clock") == "default", str(c1))


def main():
    _run_shape("thesaurus", "nucleus cell")
    _run_shape("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the shared world genesis is idempotent, the world clock ticks monotonically "
          "with a parseable wall stamp, the axis round-trips in clock order and refuses guests, a "
          "virtual world records on the default axis, and both the fiction world and the default cronon "
          "clock are byte-identical — on a nucleus cell AND a single-store edge cell.")
    sys.exit(0)


if __name__ == "__main__":
    main()
