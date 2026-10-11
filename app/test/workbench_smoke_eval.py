#!/usr/bin/env python3
"""
G3.5 — the workbench smoke test: the whole world-model foundation on one small "sandbox" bench,
the sequence of test/test_10_workbench.ak. Drives it on a fresh cell AND a re-run (idempotent), and
asserts the negative paths: a person with no line on the bench cannot write to it; a guest
cannot resolve scope:wb:sandbox.

Run:  python app/test/workbench_smoke_eval.py     (exit 0 = all pass)
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


def _seq(d, expect_exists=False):
    """Run the test_10 sequence via dispatch. `expect_exists` asserts the second run is idempotent."""
    G = "bench-sandbox"
    d("admin", "world.genesis", {})
    d("admin", "grp.new", {"group_id": G, "admin_id": "admin"})
    b = d("admin", "bench.new", {"name": "sandbox", "kind": "research", "group": G})
    s = d("admin", "society.new", {"group": G, "name": "sandbox", "world": "default",
                                   "bench": "sandbox", "kind": "cowork", "identity": "locked"})
    if expect_exists:
        # a second run must not re-create (idempotent) — bench.new returns exists
        check("[re-run] the bench is idempotent on a second run", b.get("status") == "exists", str(b)[:100])
    chair = d("admin", "cast.new", {"name": "Chair"}).get("cast_id")
    d("admin", "society.admit", {"group": G, "name": "sandbox", "cast": chair})
    d("admin", "society.moderator", {"group": G, "name": "sandbox", "cast": chair})
    scribe = d("admin", "cast.new", {"name": "Scribe"}).get("cast_id")
    d("admin", "society.admit", {"group": G, "name": "sandbox", "cast": scribe})
    d("admin", "society.responsible", {"group": G, "name": "sandbox", "cast": scribe, "kind": "scribe"})
    for fam in ("source", "hypothesis", "evidence", "note"):
        d("admin", "society.responsible", {"group": G, "name": "sandbox", "cast": chair,
                                           "kind": f"operator:{fam}"})
    d("admin", "society.responsible", {"group": G, "name": "sandbox", "cast": chair, "kind": "decide"})
    d("admin", "source.register", {"provider": "sandbox", "name": "sample-1", "uri": "sample:1",
                                   "rights": "CC0", "space": f"group:{G}"})
    d("admin", "source.acquire", {"source": "sample-1", "rule": "inline",
                                  "text": "Paragraph one. Paragraph two restates it.", "space": f"group:{G}"})
    d("admin", "source.pool.create", {"name": "sandbox-pool", "source": "sample-1", "space": f"group:{G}"})
    d("admin", "research.source.bind", {"name": "sandbox", "pool": "sandbox-pool"})
    d("admin", "research.hyp.new", {"name": "sandbox", "text": "paragraph 2 restates paragraph 1"})
    d("admin", "research.note", {"name": "sandbox", "text": "first pass"})
    d("admin", "wf.new", {"bench": "sandbox"})
    d("admin", "wf.write", {"bench": "sandbox", "pos": 1, "entry": "read sample-1"})
    d("admin", "wf.write", {"bench": "sandbox", "pos": 2, "entry": "state hypothesis 1"})
    d("admin", "wf.advance", {"bench": "sandbox", "n": 2})
    d("admin", "wf.rewind", {"bench": "sandbox", "pos": 1})
    d("admin", "wf.branch", {"bench": "sandbox", "from": 1, "name": "alt"})
    d("admin", "wf.dispatch", {"bench": "sandbox", "branch": "main", "from": 1, "to": 2})
    return G


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_smoke_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    d0 = {"guest": None}

    def d(tok, method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    G = _seq(d)

    # ── the world axis: formed + connected + created + ONE sync, each wall-stamped ──
    ax = d("admin", "world.axis", {})
    kinds = [r.get("kind") for r in ax.get("axis", [])]
    syncs = [r for r in ax.get("axis", []) if r.get("type") == "sync"]
    check(f"[{shape}] world.axis lists formed + connected + bench.created and ONE sync",
          all(x in kinds for x in ("society.formed", "society.connected", "bench.created"))
          and len(syncs) == 1 and syncs[0].get("wall"), str(kinds))

    # ── the bench stream shows every op incl. the rewind (an observation, not an erasure) ──
    st = d("admin", "source.stream", {"stream": "wb:sandbox", "space": f"group:{G}"})
    ops = [(o.get("source_metadata") or {}).get("op") for o in st.get("observations", [])]
    fams = [(o.get("source_metadata") or {}).get("family") for o in st.get("observations", [])]
    check(f"[{shape}] the bench stream recorded the hypothesis, note, and workflow ops (rewind kept)",
          "new" in ops and "rewind" in ops and "hypothesis" in fams and "note" in fams, str(ops)[:160])

    # ── the five grants + decide ──
    grants = d("admin", "bench.grants", {"name": "sandbox", "group": G})
    fams2 = {g.get("family") for g in grants.get("grants", [])}
    check(f"[{shape}] bench.grants lists the operator families",
          {"source", "hypothesis", "evidence", "note"} <= fams2, str(fams2))

    # ── negative: WHAT THE TABLE REFUSES, now that G2.3's grant table is gone ──
    #
    # This asked for the `operator:hypothesis` text: a person admitted to the society but holding
    # no `responsible:operator:<family>` link was refused by the bench door. That table is deleted
    # (ruling §5) — it was a permission store in the graph that the one gate could not see and no
    # eval could enumerate. What refuses a bench op now is the table: `carol` holds NO line on this
    # bench, so step 3 refuses her `record` `out_of_scope`, and she is refused BEFORE the op runs
    # rather than inside it.
    d("admin", "user.add", {"client_id": "carol", "role": "user",
                            "passphrase_hash": hashlib.sha256(b"carol").hexdigest()})
    refused = d("carol", "research.hyp.new", {"name": "sandbox", "text": "no line"})
    check(f"[{shape}] a person with no line on this bench cannot write to it",
          "error" in str(refused) or refused.get("status") == "refused", str(refused)[:140])

    # ── a second run is idempotent (no duplicate axis records, bench exists) ──
    _seq(d, expect_exists=True)
    ax2 = d("admin", "world.axis", {})
    created2 = [r for r in ax2.get("axis", []) if r.get("kind") == "bench.created"]
    check(f"[{shape}] a second run does not duplicate the bench.created axis record",
          len(created2) == 1, f"{len(created2)} bench.created records")

    # ── a guest cannot resolve the closed bench's scope ──
    gr = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                     "params": {"data": {}}, "id": "gg"}, "network")
    tok = (gr.get("result") or {}).get("session_token") if isinstance(gr, dict) else None
    seen = False
    if tok:
        gg = k.dispatch({"jsonrpc": "2.0", "method": "research.hyp.ls",
                         "params": {"session_token": tok, "data": {"name": "sandbox"}}, "id": "gq"},
                        "network")
        res = gg.get("result") if isinstance(gg, dict) else None
        # a guest is not a group member, so the closed bench is invisible: an error, or an empty/no
        # hypotheses result — never the member-only data.
        seen = bool(res and res.get("hypotheses"))
    check(f"[{shape}] a guest cannot read the closed bench (scope:wb:sandbox is member-only)",
          not seen, "guest saw hypotheses" if seen else "")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the workbench smoke path runs end-to-end (world axis shows formed/connected/"
          "created + one sync, the bench stream records every op including the rewind, the grant table "
          "lists the families), a person with no line on the bench is refused, a second run is idempotent, and a "
          "guest cannot read the closed bench — on both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
