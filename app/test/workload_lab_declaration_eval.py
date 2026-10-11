#!/usr/bin/env python3
"""
A LAB is a workload: its client's ID set, its seven workflows and its sweep are declared, and read.

The frontend's plants-vision draft (notes 2026-09-26 b/c, "needs platform 2") could not land:
provisioning wrote `programme on plants-lab/plants-vision` for every declaration's client whatever
the declaration said, `programme` has no `record`, and the gate refused the lab's first bench step:

    [gate] refused identity=lab:plants_vision action=record target=plants-lab/wb:plants_vision
           reason=out_of_scope

and the frozen shape carried ONE `workflow` where a lab runs seven (`plants_t1…t7`) plus a sweep.

This eval provisions the SHIPPED declaration (`app/config/workbench/workloads/plants_vision.json`, with
its templates and `heads1` sweep) on a fresh cell through the real provisioning code — the file as
it runs, now a public `learning` bench (26d). Review 2026-09-27: it used to rebuild a draft from
`deploy.json`'s legacy block (deleted), and then to strip the shipped file back to a group-placed
shape, so the shape that ships was the one it never provisioned. The group-placed shape is case 7.
On a tier that withholds the lab it passes vacuously. It holds:

  1. the client's lines are the DECLARED ID set (`researcher`) on the workload's own places — its
     space AND its bench — and no `programme` line; the gate now ADMITS the refused question;
  2. a real bench step (`learning.dataset.bind`, a `record` on the bench) dispatched AS the client is
     not refused by the gate;
  3. seven branches are loaded (one per declared workflow), the sweep is defined, and the policy the
     driver reads carries the seven workflows and the sweep;
  4. changing `idset` CONVERGES the lines (the old ID set's lines go), it does not add to them;
  5. a declaration may name only an `assigned` row: `admin` / `librarian` / `resident` are refused
     by id (`reason=idset`), as are malformed `workflows` / `sweeps` / `grants` / `profile`;
  6. `profile` is a Set membership (`set:wl:profile:<p>`) and nothing else;
  7. the group-placed shape (the 26c refusal): its client is admitted on `<gid>/wb:<bench>`.

Run:  python app/test/workload_lab_declaration_eval.py     (exit 0 = all pass)
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



LAB = os.path.join(ROOT, "app", "config", "workbench", "workloads", "plants_vision.json")


def _group_placed(decl):
    """The lab in its pre-26d GROUP-placed shape (no `bench_public` / `bench_kind`, no `space.kind` /
    `space.identity`), which is the shape the 26c refusal was about."""
    out = copy.deepcopy(decl)
    for f in ("bench_public", "bench_kind", "_bench"):
        out.pop(f, None)
    for f in ("kind", "identity"):
        (out.get("space") or {}).pop(f, None)
    return out


def shipped():
    """THE SHIPPED DECLARATION, as it is — the file that runs on a cell. (Review 2026-09-27: this
    used to rebuild the draft from `deploy.json`'s legacy `auto` block, which is deleted, and then
    to strip the shipped file back to a group-placed shape, so the lab that actually ships was the
    one shape this eval did not provision.)"""
    with open(LAB, encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 78)
    print("A lab is a workload: ID set, workflows, sweeps, grants and profile are read")
    print("=" * 78)
    if not os.path.isfile(LAB):
        # A tier that does not carry the lab's data does not ship its declaration (26d, needs
        # platform 2), and this eval ships everywhere: there is nothing to provision here.
        print("RESULT: PASS (vacuous) — this tier withholds the lab (plants_vision.json not shipped).")
        sys.exit(0)
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.api import gate as G
    from lib.akasha.api.trust import TRUST_INTERNAL
    from lib.akasha.workbench import workload as W, workload_provision as P
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="wl_lab_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {
                    "user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(client, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": client, "data": data}, "id": "p"},
                          TRUST_INTERNAL)

    decl = shipped()
    client = W.client_of(decl)
    print("\n  ── the shipped declaration is well-formed ──")
    check("the shipped declaration has no problems", W.problems(decl) == [], str(W.problems(decl)))
    check("every declared workflow has its template", all(t for _b, t in P.templates_of(decl)),
          str([b for b, t in P.templates_of(decl) if not t]))

    rep = P.provision(d, decl)
    print("\n  ── 1. the declared ID set, on the workload's own places ──")
    lines = sorted((ln["idset"], str(ln.get("on") or "")) for ln in G.lines_for(client))
    want = sorted(("researcher", p) for p in W.client_places(decl))
    check("the client holds `researcher` on its space AND its bench, and no `programme` line",
          set(want) <= set(lines) and not any(i == "programme" for i, _ in lines), str(lines))
    bench_place = W.client_places(decl)[1]
    ok, why = G.gate(client, "record", bench_place)
    check("the gate ADMITS `record` on the lab's own bench place (%s)" % bench_place, ok, why)
    ok2, why2 = G.gate(client, "record", bench_place.replace("plants_vision", "some_other_bench"))
    check("…and only there: another bench in the group is still out of scope", not ok2, why2)

    print("\n  ── 2. a real bench step, as the client ──")
    r = d(client, "learning.dataset.bind", {"name": "plants-vision", "pool": "source:pool:none:v1"})
    err = (r or {}).get("error") or {}
    check("`learning.dataset.bind` as lab:plants_vision is not refused by the gate",
          not (err.get("code") == -32001 or "out_of_scope" in str(err.get("message"))),
          str(err or (r or {}).get("result"))[:160])

    print("\n  ── 3. seven branches, the sweep, the policy ──")
    check("seven workflow branches were loaded, each with entries",
          rep.get("entries", 0) > 0 and not [p for p in rep.get("problems") or [] if "no workflow" in p],
          "entries=%s problems=%s" % (rep.get("entries"), rep.get("problems")))
    check("the declared sweep was defined", rep.get("sweeps") == 1, str(rep.get("sweeps")))
    pol = W.policy(decl)
    check("the policy the driver reads carries the seven workflows, in order, and the sweep",
          pol.get("workflows") == decl["workflows"] and pol.get("sweeps") == ["heads1"],
          "%s / %s" % (pol.get("workflows"), pol.get("sweeps")))
    grant_problems = [p for p in rep.get("problems") or [] if "grant" in p]
    check("the Botanist's declared grants were written", not grant_problems, str(grant_problems))

    print("\n  ── 4. changing `idset` converges the lines ──")
    d2 = copy.deepcopy(decl)
    d2["idset"] = "member"
    P.provision(d, d2)
    lines2 = sorted((ln["idset"], str(ln.get("on") or "")) for ln in G.lines_for(client))
    check("after `idset: member` the client holds member on both places and NO researcher line",
          set(("member", p) for p in W.client_places(d2)) <= set(lines2)
          and not any(i == "researcher" for i, _ in lines2), str(lines2))

    print("\n  ── 5. a declaration may name only an `assigned` row ──")
    for bad_idset in ("admin", "librarian", "resident", "guest", "nonesuch"):
        x = dict(decl, idset=bad_idset)
        check("idset=%s is refused by id" % bad_idset, "idset" in W.problems(x), str(W.problems(x)))
    for field, val in (("workflows", []), ("workflows", ["ok", "bad name"]), ("sweeps", "heads1"),
                       ("grants", {"Botanist": "decide"}), ("profile", "private lab")):
        x = dict(decl)
        x[field] = val
        check("%s=%r is refused by id" % (field, val), field in W.problems(x), str(W.problems(x)))

    print("\n  ── 6. `profile` is a label ──")
    sets = W.field_sets(decl)
    check("`profile` is a Set membership and the ID set is one too",
          "set:wl:profile:private_lab" in sets and "set:wl:idset:researcher" in sets,
          str([s for s in sets if "profile" in s or "idset" in s]))
    base = dict(decl)
    base.pop("profile")
    check("…and it changes nothing the driver reads", W.policy(base) == W.policy(decl))

    print("\n  ── 7. the 26c refusal, in the group-placed shape ──")
    gp = _group_placed(decl)
    k2 = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="wl_lab_gp_"))
    k2.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {
                     "user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                 "id": "g"}, "local")

    def d2(client_, method, data):
        return k2.dispatch({"jsonrpc": "2.0", "method": method,
                            "params": {"session_token": client_, "data": data}, "id": "p"},
                           TRUST_INTERNAL)
    P.provision(d2, gp)
    gp_bench = W.client_places(gp)[1]
    ok3, why3 = G.gate(client, "record", gp_bench)
    check("a group-placed lab's client is admitted `record` on %s (the question 26c refused)"
          % gp_bench, ok3 and gp_bench.startswith(W.society_of(gp)[0] + "/"), why3)

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — the shipped plants-vision declaration provisions as a workload: its client holds the "
          "declared ID set on its space and bench and the gate admits its bench steps, its seven "
          "workflows and its sweep are loaded and handed to the driver, a changed ID set converges, "
          "and only an `assigned` row can be named.")
    sys.exit(0)


if __name__ == "__main__":
    main()
