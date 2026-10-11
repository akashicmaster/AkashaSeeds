#!/usr/bin/env python3
"""
A lab's bench has ONE author, and the gate is asked about the lab's own places.

Frontend note 2026-09-26d, "needs platform" 1 and 3:

  1. `workload.status` answered `gate.run = out_of_scope` for the lab. It asked the gate about the
     WORKLOAD KEY (`plants-vision/plants_vision`), and a key is not a place: the client's lines
     name its space and its bench. A station's key happens to spell its space
     (`studio_ai/news_show`), which is why this never showed before.
  3. On thesaurus, the legacy bench SCAFFOLD (`workloads/bench_plants_vision.json`, written by the
     crystallizer from `deploy.json`, create-if-absent) and the workload both described the lab's
     bench. Measured on a fresh cell, this is worse than a display question. The scaffold makes a
     PUBLIC bench (`wb:plants_vision`, no group), the workload's client holds its line on
     `plants-lab/wb:plants_vision`, and so every bench step the lab runs as its client is refused
     `out_of_scope`.

This eval holds the fix on a fresh cell, through the real provisioning code and the real
declaration (`app/config/workbench/workloads/plants_vision.json`):

  A. `workload.status` asks REACH on the workload's space and the FACTS on its key. The lab reads a
     fact term, never `out_of_scope`, and reads `ok` once the four run facts hold. An identity
     with no line on the lab still reads `out_of_scope`, and a station reads as it did.
  B. `bench_public: true` puts the bench in the nucleus. The client's line follows it to
     `wb:<slug>`, a real bench step as the client is admitted, and `bench_kind` / `space.kind` /
     `space.identity` reach the bench and the society.
  C. On a cell where the scaffold's public bench already exists, a declaration that places the
     bench in its group is REPORTED by field id (`bench_public: …`), not silently mis-gated, and
     declaring `bench_public: true` converges with no problem.
  D. Flipping `bench_public` moves the client's line; the line on the bench place it left is removed.
  E. Malformed `bench_kind` / `bench_public` / `space.kind` / `space.identity` are refused by id.
  F. The crystallizer no longer writes the scaffold.

Run:  python app/test/workload_bench_place_eval.py     (exit 0 = all pass)
"""
import copy
import hashlib
import json
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


def _decl(name):
    with open(os.path.join(ROOT, "app", "config", "workbench", "workloads", name), encoding="utf-8") as f:
        return json.load(f)


def _cell():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.api.trust import TRUST_INTERNAL
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="wl_place_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {
                    "user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(client, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": client, "data": data}, "id": "p"},
                          TRUST_INTERNAL)
    return k, d


def _res(r):
    return (r or {}).get("result") or {}


def _refused(r):
    err = (r or {}).get("error") or {}
    return err.get("code") == -32001 or "out_of_scope" in str(err.get("message"))



def _group_placed(decl):
    """The lab as it was declared BEFORE 26d: no `bench_public` / `bench_kind`, no `space.kind` /
    `space.identity` — the group-placed shape these cases are about. The shipped file now declares
    the public learning bench (frontend, 2026-09-27), so the baseline is derived, not read."""
    import copy as _copy
    out = _copy.deepcopy(decl)
    for f in ("bench_public", "bench_kind", "_bench"):
        out.pop(f, None)
    for f in ("kind", "identity"):
        (out.get("space") or {}).pop(f, None)
    return out

def main():
    print("=" * 78)
    print("A lab's bench has one author; the gate is asked about the lab's own places")
    print("=" * 78)
    if not os.path.isfile(os.path.join(ROOT, "app", "config", "workbench", "workloads", "plants_vision.json")):
        # A tier that does not carry the lab's data does not ship its declaration (26d, needs
        # platform 2), and this eval ships everywhere: there is nothing to check here.
        print("RESULT: PASS (vacuous) — this tier withholds the lab (plants_vision.json not shipped).")
        sys.exit(0)
    from lib.akasha.api import gate as G, facts as F
    from lib.akasha.workbench import workload as W, workload_provision as P, wl_state as S
    from lib.akasha.workbench import provision as PR

    lab = _group_placed(_decl("plants_vision.json"))
    lab_key = W.key(lab)
    client = W.client_of(lab)
    check("the real lab's key is NOT its space (the case a station never exercised)",
          lab_key != "%s/%s" % W.society_of(lab), "%s vs %s/%s" % ((lab_key,) + W.society_of(lab)))

    # ── A. status: reach on the place, facts on the key ─────────────────────────────────────────
    print("\n  ── A. `workload.status` asks reach on the space, facts on the key ──")
    k, d = _cell()
    P.provision(d, lab)
    st = S.status(k, lab_key)
    check("the lab reads a FACT term, not `out_of_scope` (the 26d symptom)",
          st.get("gate", {}).get("run") in G.RUN_FACTS, str(st.get("gate")))
    for fs in (F.DECLARED, F.ARMED, F.SOURCE_READY, F.HEADROOM):
        F.state(k, fs, lab_key, True)
    st = S.status(k, lab_key)
    check("…and `ok` once the four run facts hold for its key", st.get("gate", {}).get("run") == "ok",
          str(st.get("gate")))
    station = _decl("news_show.json")
    P.provision(d, station)
    other = W.client_of(station)
    ok, why = G.gate(other, G.RUN, lab_key, place=W.client_places(lab)[0])
    check("another workload's client (it may `run`, on its own places) is still refused on the lab's "
          "place — `place` has teeth", not ok and why == G.R_TARGET, "%s: %s" % (other, why))
    ok_old, why_old = G.gate(client, G.RUN, lab_key)
    check("…and asking reach of the KEY is what refused the lab (the old question, still refused)",
          not ok_old and why_old == G.R_TARGET, why_old)
    st2 = S.status(k, W.key(station))
    check("a station reads as it did (its key spells its space, so place = key)",
          st2.get("gate", {}).get("run") in G.RUN_FACTS + ("ok",), str(st2.get("gate")))

    # ── B. a declared public bench ──────────────────────────────────────────────────────────────
    print("\n  ── B. `bench_public` / `bench_kind` / `space.kind` / `space.identity` are read ──")
    pub = copy.deepcopy(lab)
    pub.update({"bench_public": True, "bench_kind": "learning"})
    pub["space"] = dict(pub["space"], kind="cowork", identity="locked")
    check("the public-bench declaration is well-formed", W.problems(pub) == [], str(W.problems(pub)))
    k, d0 = _cell()
    calls = []

    def d(client_, method, data):
        calls.append((method, dict(data)))
        return d0(client_, method, data)
    rep = P.provision(d, pub)
    check("provisioning reports no problem", not rep.get("problems"), str(rep.get("problems")))
    info = _res(d("admin", "bench.info", {"name": W.bench_slug(pub)}))
    check("the bench is in the NUCLEUS (no group) and records the declared kind `learning`",
          not info.get("group") and info.get("kind") == "learning",
          "group=%s kind=%s" % (info.get("group"), info.get("kind")))
    lines = {(ln["idset"], str(ln.get("on") or "")) for ln in G.lines_for(client)}
    gb, pb = W.bench_places(pub)
    check("the client's line is on `wb:<slug>` and not on `<gid>/wb:<slug>`",
          ("researcher", pb) in lines and not any(o == gb for _i, o in lines), str(sorted(lines)))
    r = d(client, "learning.dataset.bind", {"name": W.bench_slug(pub), "pool": "source:pool:none:v1"})
    check("a real bench step AS THE CLIENT is admitted on the public bench", not _refused(r),
          str((r or {}).get("error") or _res(r))[:160])
    soc = _res(d("admin", "society.info", {"group": W.society_of(pub)[0],
                                           "space": W.society_of(pub)[1]}))
    sn = [a for m, a in calls if m == "society.new"]
    check("`space.kind` reaches the society (society.info kind=cowork)", soc.get("kind") == "cowork",
          "kind=%s" % soc.get("kind"))
    check("`space.kind` / `space.identity` are passed to `society.new` (cowork, locked)",
          bool(sn) and sn[0].get("kind") == "cowork" and sn[0].get("identity") == "locked",
          str(sn[:1]))

    # ── C. the scaffold's bench already exists ──────────────────────────────────────────────────
    print("\n  ── C. a cell that already has the scaffold's public bench ──")
    def _scaffold(dd):
        """The pre-existing public bench + its society, stood up by ops (the legacy bench_*.json pass
        that used to do this is gone — the purge order §2)."""
        gid_, sn_ = W.society_of(lab)
        dd("admin", "grp.new", {"group_id": gid_, "admin_id": "admin"})
        dd("admin", "bench.new", {"name": W.bench_slug(lab), "kind": "learning"})
        dd("admin", "society.new", {"group": gid_, "name": sn_, "world": "default",
                                    "bench": W.bench_slug(lab), "kind": "cowork", "identity": "locked"})
    k, d = _cell()
    _scaffold(d)
    rep = P.provision(d, lab)
    named = [p for p in rep.get("problems") or [] if p.startswith("bench_public:")]
    check("a group-placed declaration over the existing public bench is REPORTED by field id",
          bool(named), str(rep.get("problems")))
    r = d(client, "learning.dataset.bind", {"name": W.bench_slug(lab), "pool": "source:pool:none:v1"})
    check("…and that is the refusal it names: the bench step as the client is out_of_scope",
          _refused(r), str((r or {}).get("error"))[:160])
    rep2 = P.provision(d, pub)
    check("declaring `bench_public: true` (+ kind learning) converges with no problem",
          not rep2.get("problems"), str(rep2.get("problems")))
    r = d(client, "learning.dataset.bind", {"name": W.bench_slug(lab), "pool": "source:pool:none:v1"})
    check("…and the lab's bench step as its client is admitted", not _refused(r),
          str((r or {}).get("error") or _res(r))[:160])

    shipped = _decl("plants_vision.json")
    k3, d3 = _cell()
    _scaffold(d3)
    rep3 = P.provision(d3, shipped)
    r = d3(client, "learning.dataset.bind", {"name": W.bench_slug(shipped), "pool": "source:pool:none:v1"})
    check("the SHIPPED declaration, as it is, converges over the existing public bench with no "
          "problem, and its bench step as the client is admitted (review 2026-09-27)",
          not rep3.get("problems") and not _refused(r),
          "%s / %s" % (rep3.get("problems"), str((r or {}).get("error") or "")[:120]))

    # ── D. flipping bench_public moves the line ─────────────────────────────────────────────────
    print("\n  ── D. the client's line follows the bench ──")
    lines = {str(ln.get("on") or "") for ln in G.lines_for(client)}
    check("after the flip to public, no line is left on `<gid>/wb:<slug>`", gb not in lines and pb in lines,
          str(sorted(lines)))

    # ── E. validation ───────────────────────────────────────────────────────────────────────────
    print("\n  ── E. malformed bench/space fields are refused by id ──")
    for field, val, want in (("bench_kind", "a kind", "bench_kind"), ("bench_public", "yes", "bench_public"),
                             ("space", dict(lab["space"], kind="room"), "space"),
                             ("space", dict(lab["space"], identity="sealed"), "space")):
        x = copy.deepcopy(lab)
        x[field] = val
        check("%s=%r is refused as `%s`" % (field, val, want), want in W.problems(x), str(W.problems(x)))
    check("absent `bench_kind` is the declared effect (the order-§3 default is unchanged)",
          W.bench_kind(lab) == W.effect(lab), W.bench_kind(lab))

    # ── F. the scaffold is not written any more ─────────────────────────────────────────────────
    print("\n  ── F. the crystallizer writes no scaffold ──")
    src = open(os.path.join(ROOT, "reproductor", "engine.py"), encoding="utf-8").read()
    check("reproductor/engine.py no longer writes workloads/bench_plants_vision.json",
          'writestr("app/config/workbench/workloads/bench_plants_vision.json"' not in src)

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — status asks reach on the workload's place and facts on its key, the bench "
          "is placed and kinded by its one declaration, a mismatch with an existing bench is named "
          "by field id, and the client's line follows the bench.")
    sys.exit(0)


if __name__ == "__main__":
    main()
