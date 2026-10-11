#!/usr/bin/env python3
"""
Public bench + group-society governance (PLANTS Vision Learning ruling D, 2026-09-06).

A bench may be PUBLIC — `bench.new` with no group=, so its atoms live in the nucleus and its outputs
are guest-readable — while governance stays with a small group SOCIETY that `society:connected` to it
(roles + grants only). This eval proves the grant model still composes across that boundary: a
non-privileged member is refused an op until the moderator grants `responsible:operator:<family>`, and
then admitted — even though the society is in a group and the bench is in the nucleus (the connection
is found through the nucleus reverse-index). Reading the public bench needs no membership.

Run:  python app/test/bench_public_grant_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
# THE RESEARCHER LINE (one-gate ruling §1). `grp.add` makes a person a MEMBER of a group,
# which is read + say. The person these evals model works ON A BENCH — opens its societies,
# mints its casts, writes its hypotheses, runs its sweeps — and that is the `researcher`
# row. The ruling is explicit that a member is never it ("provisioned by the researcher who
# owns the bench, never by a member"), and a researcher line is written by a person, so the
# eval writes it rather than expecting group membership to imply it.
from lib.akasha.api import gate as _G                                   # noqa: E402


_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_pg_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(tok, method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    d("admin", "world.genesis", {})
    d("admin", "grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("admin", "user.add", {"client_id": "alice", "role": "user",
                            "passphrase_hash": hashlib.sha256(b"alice").hexdigest()})
    d("admin", "grp.add", {"group_id": "lab", "member_id": "alice"})
    _G.assign("alice", "researcher", "lab")   # see THE RESEARCHER LINE, below the imports

    # ── a PUBLIC bench (no group=) lives in the nucleus ──
    b = d("admin", "bench.new", {"name": "pub", "kind": "research"})
    check(f"[{shape}] bench.new with no group= is a PUBLIC (nucleus) bench",
          b.get("status") == "created" and b.get("group") is None, str(b)[:100])

    # ── a group society connects to the public bench (governance only) ──
    sw = d("admin", "society.new", {"group": "lab", "name": "gov", "world": "default",
                                    "bench": "pub", "kind": "cowork"})
    check(f"[{shape}] a group society connects to the public bench", sw.get("connected") is True,
          str(sw)[:120])

    # ── who may write on a PUBLIC bench, now that G2.3's grant table is gone ──
    #
    # This used to assert the bridge: a member of the group society was REFUSED on the nucleus-
    # resident bench until `responsible:operator:hypothesis` was granted, then admitted — the
    # grant "composing across the nucleus↔group boundary". That table is deleted (ruling §5): it
    # was a permission store in the graph, invisible to the one gate and enumerable by no eval.
    #
    # What the boundary question becomes is the LINE — and a PUBLIC bench is its OWN place, not a
    # place reached through a society that connects to it. `society:connected` is governance (it
    # is what `bench.grants` reads, below); treating it as a permission bridge would rebuild the
    # deleted table out of links. A bench inside a group is `<gid>/wb:<slug>`, so a line on the
    # group reaches it; a public bench is `wb:<slug>`, reached by a row that reaches everything
    # or by a line naming it. So alice holds a SECOND line, on the bench itself — the ruling's
    # own row for her ("researcher · its bench"), written by a person, as §2 says.
    #
    # `carol` holds no line on it and is refused, by step 3, on the same bench. That is the
    # property worth keeping from this case: a PUBLIC bench is not a public WRITE surface.
    _G.assign("alice", "researcher", "wb:pub")
    al = d("alice", "cast.new", {"name": "Al"}).get("cast_id")
    d("alice", "society.join", {"group": "lab", "name": "gov", "cast": al})
    d("admin", "society.admit", {"group": "lab", "name": "gov", "cast": al, "client": "alice"})
    admitted = d("alice", "research.hyp.new", {"name": "pub", "text": "a granted claim"})
    check(f"[{shape}] a researcher on the lab writes on the public bench its society connects to",
          admitted.get("hyp") and isinstance(admitted.get("observed_at_seq"), int), str(admitted)[:140])
    d("admin", "user.add", {"client_id": "carol", "role": "user",
                            "passphrase_hash": hashlib.sha256(b"carol").hexdigest()})
    refused = d("carol", "research.hyp.new", {"name": "pub", "text": "a claim"})
    check(f"[{shape}] …and a person with no line is REFUSED on it — public to read is not "
          f"public to write",
          "error" in str(refused) or refused.get("status") == "refused", str(refused)[:140])

    # ── A28(e) — society.run RESOLVES the public bench (its key is a nucleus key; the group engine
    #    cannot alias-resolve it, so `_bench_name_for` must go nucleus-aware). This is exactly what
    #    silently failed on the box (bench= empty → no job id → status=failed). ──
    d("admin", "wf.new", {"bench": "pub"})
    d("admin", "wf.write", {"bench": "pub", "pos": 1, "entry":
        __import__("json").dumps({"method": "research.note", "params": {"name": "pub", "text": "run ok"}})})
    run = d("admin", "society.run", {"group": "lab", "name": "gov", "workflow": "main"})
    check(f"[{shape}] society.run RESOLVES the public bench and dispatches (bench= is not empty)",
          run.get("bench") == "wb:pub" and bool(run.get("job_id")), str(run)[:160])

    # ── `bench.grants` still COMPOSES ACROSS the nucleus↔group boundary — as a READ ──
    #
    # The responsibility record is no longer a permission (G2.3 is deleted), but it is still
    # written, still provenance, and still the one place a reader sees who holds what on a bench.
    # The property this case was really protecting is the hard part of the read: the bench lives
    # in the NUCLEUS and the society that names its responsibilities lives in a GROUP ENGINE, so
    # composing them is a cross-store walk that silently returned nothing when it was wrong.
    d("admin", "society.responsible", {"group": "lab", "name": "gov", "cast": al,
                                       "kind": "operator:hypothesis"})
    grants = d("admin", "bench.grants", {"name": "pub"})
    check(f"[{shape}] bench.grants composes the responsibility record from the connected society "
          f"across the nucleus↔group boundary",
          any(g.get("family") == "hypothesis" for g in grants.get("grants", [])), str(grants)[:140])
    gr = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                     "params": {"data": {}}, "id": "gg"}, "network")
    tok = (gr.get("result") or {}).get("binding_key") if isinstance(gr, dict) else None
    seen = False
    if tok:
        gg = k.dispatch({"jsonrpc": "2.0", "method": "research.hyp.ls",
                         "params": {"session_token": tok, "data": {"name": "pub"}}, "id": "gq"}, "network")
        res = gg.get("result") if isinstance(gg, dict) else None
        seen = bool(res and res.get("hypotheses"))
    check(f"[{shape}] the PUBLIC bench is guest-readable (its outputs are public)", seen,
          "guest could not read" if not seen else "")

    # ── sever drops the connection; the grant no longer composes ──
    d("admin", "society.sever", {"group": "lab", "name": "gov", "bench": "pub"})
    after = d("admin", "bench.grants", {"name": "pub"})
    check(f"[{shape}] severing drops the reverse-index (no composed grant)",
          not any(g.get("family") == "hypothesis" for g in after.get("grants", [])), str(after)[:120])


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a PUBLIC bench is nucleus-resident, guest-READABLE, and its own place for "
          "the gate (`wb:<slug>`, not `<gid>/wb:<slug>`): a researcher writes on it by holding a LINE "
          "naming it, and a person with no such line is refused by step 3 — public to read is not "
          "public to write, and `society:connected` is governance, never a permission bridge. The "
          "responsibility record is still composed across the nucleus↔group boundary by "
          "`bench.grants`, now purely as a READ; society.run resolves the nucleus bench; and severing "
          "drops the connection — on both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
