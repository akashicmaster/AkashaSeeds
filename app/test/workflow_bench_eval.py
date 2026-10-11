#!/usr/bin/env python3
"""
G3 — workflow on the bench + the sync event (world-workbench-society spec v1.0).

A workflow is a bench's script-and-log in one structure: entries ahead of the cursor are the plan,
behind it the record; a rewind is itself an observation (never an erasure). wf.dispatch is the SYNC
EVENT — it mints an immutable exec:<bench>:<n> membrane over a run of entries and records ONE world
chronon on the shared axis (governed by responsible:decide). Entry atoms are aliased
workflow:<bench>:<branch>:<pos> (NOT the old CSL wf: space).

Run:  python app/test/workflow_bench_eval.py     (exit 0 = all pass)
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
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_wf_"))
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
    _G.assign("alice", "researcher", "lab")
    d("admin", "bench.new", {"name": "sandbox", "kind": "research", "group": "lab"})
    d("admin", "society.new", {"group": "lab", "name": "sem", "world": "default",
                               "bench": "sandbox", "kind": "cowork"})

    # ── wf.new is 1:1 ──
    w1 = d("admin", "wf.new", {"bench": "sandbox"})
    w2 = d("admin", "wf.new", {"bench": "sandbox"})
    check(f"[{shape}] wf.new creates then is idempotent (1:1)",
          w1.get("status") == "created" and w2.get("status") == "exists"
          and w1.get("workflow") == "workflow:sandbox", f"{w1.get('status')}/{w2.get('status')}")

    # ── write / advance / rewind / branch ──
    d("admin", "wf.write", {"bench": "sandbox", "pos": 1, "entry": "read sample-1"})
    d("admin", "wf.write", {"bench": "sandbox", "pos": 2, "entry": "state hypothesis 1"})
    adv = d("admin", "wf.advance", {"bench": "sandbox", "n": 2})
    check(f"[{shape}] wf.advance moves the cursor over both entries",
          adv.get("cursor") == 2 and adv.get("advanced") == [1, 2], str(adv)[:120])
    cur = d("admin", "wf.cursor", {"bench": "sandbox", "branch": "main"})
    check(f"[{shape}] wf.cursor reports the advanced cursor", cur.get("cursor") == 2, str(cur))
    rw = d("admin", "wf.rewind", {"bench": "sandbox", "pos": 1})
    check(f"[{shape}] wf.rewind moves the cursor back (entries stay)", rw.get("cursor") == 1, str(rw))
    ls = d("admin", "wf.ls", {"bench": "sandbox", "branch": "main"})
    phases = {r["pos"]: r["phase"] for r in ls.get("entries", [])}
    check(f"[{shape}] wf.ls splits log (≤cursor) from script (>cursor)",
          phases.get(1) == "log" and phases.get(2) == "script", str(phases))
    br = d("admin", "wf.branch", {"bench": "sandbox", "from": 1, "name": "alt"})
    check(f"[{shape}] wf.branch forks a branch sharing the prefix",
          br.get("status") == "branched" and br.get("branch") == "alt" and br.get("copied") == 1,
          str(br)[:120])

    # ── observation at_seq strictly increases across the rewind (the record of rewinding is kept) ──
    st = d("admin", "source.stream", {"stream": "wb:sandbox", "space": "group:lab"})
    wf_obs = [o for o in st.get("observations", [])
              if (o.get("source_metadata") or {}).get("family") in ("workflow",)]
    seqs = [o.get("at_seq") for o in wf_obs]
    ops = [(o.get("source_metadata") or {}).get("op") for o in wf_obs]
    check(f"[{shape}] every wf.* call teed an observation with a strictly increasing at_seq",
          len(seqs) >= 6 and seqs == sorted(seqs) and len(set(seqs)) == len(seqs), str(seqs))
    check(f"[{shape}] the rewind is itself an observation (never erased)", "rewind" in ops, str(ops))

    # ── dispatch = the sync event: one exec membrane + one world chronon ──
    dp = d("admin", "wf.dispatch", {"bench": "sandbox", "branch": "main", "from": 1, "to": 2})
    check(f"[{shape}] wf.dispatch mints exec:sandbox:1 with a wall stamp",
          dp.get("status") == "dispatched" and dp.get("exec") == "exec:sandbox:1"
          and dp.get("wall") and dp.get("members") == 2, str(dp)[:160])
    ax = d("admin", "world.axis", {})
    sync_rows = [r for r in ax.get("axis", []) if r.get("type") == "sync"]
    check(f"[{shape}] the world axis gains ONE sync record naming the exec + a wall stamp",
          len(sync_rows) == 1 and sync_rows[0].get("exec") == "exec:sandbox:1"
          and sync_rows[0].get("wall"), str(sync_rows)[:160])
    er = d("admin", "exec.read", {"id": "exec:sandbox:1", "group": "lab"})
    check(f"[{shape}] exec.read returns the run's provenance",
          er.get("bench") == "wb:sandbox" and er.get("from") == 1 and er.get("to") == 2
          and len(er.get("members") or []) == 2, str(er)[:160])

    # ── a second dispatch makes a NEW record; the first is untouched (copy-and-fix) ──
    dp2 = d("admin", "wf.dispatch", {"bench": "sandbox", "branch": "main", "from": 1, "to": 1})
    ax2 = d("admin", "world.axis", {})
    sync2 = [r for r in ax2.get("axis", []) if r.get("type") == "sync"]
    check(f"[{shape}] a corrected dispatch is a NEW exec, the first record unchanged",
          dp2.get("exec") == "exec:sandbox:2" and len(sync2) == 2
          and {s.get("exec") for s in sync2} == {"exec:sandbox:1", "exec:sandbox:2"}, str(dp2)[:120])

    # ── who may DISPATCH to the world ──
    #
    # This asked for `responsible:decide`: alice was refused until that link was written, then
    # admitted. The `responsible:*` table is deleted as a permission (ruling §5) — `decide` is one
    # of the names §2 collapses into the assignment line. Dispatch is a `record` on the bench, so
    # what decides it is the line: alice holds `researcher on lab` and dispatches; carol holds
    # none and does not. The responsibility link is still written above, and still readable
    # through `bench.grants` — as provenance, which is what it always was.
    al = d("alice", "cast.new", {"name": "Al"}).get("cast_id")
    d("alice", "society.join", {"group": "lab", "name": "sem", "cast": al})
    d("admin", "society.admit", {"group": "lab", "name": "sem", "cast": al, "client": "alice"})
    d("admin", "society.responsible", {"group": "lab", "name": "sem", "cast": al,
                                       "kind": "operator:hypothesis"})
    d("admin", "user.add", {"client_id": "carol", "role": "user",
                            "passphrase_hash": hashlib.sha256(b"carol").hexdigest()})
    refused = d("carol", "wf.dispatch", {"bench": "sandbox", "branch": "main", "from": 1, "to": 1})
    check(f"[{shape}] wf.dispatch is REFUSED for a person with no line on this bench",
          "error" in str(refused) or refused.get("status") == "refused", str(refused)[:160])
    ok = d("alice", "wf.dispatch", {"bench": "sandbox", "branch": "main", "from": 1, "to": 1})
    check(f"[{shape}] …and a researcher on the lab dispatches",
          ok.get("status") == "dispatched" and ok.get("exec") == "exec:sandbox:3", str(ok)[:120])

    # ── A52 — a macro.run line with a POSITIONAL token is text-suspect (not silently swallowed) ──
    import logging as _lg
    import tempfile as _tf
    from lib.akasha.concepts.workflow import WorkflowConcept
    good = WorkflowConcept._parse_ak_line('macro.run name=observe.diff bench=x before=o0')
    bad = WorkflowConcept._parse_ak_line('macro.run observe.diff bench=x before=o0')
    check(f"[{shape}] a name= macro.run line parses as a structured command",
          isinstance(good, dict) and good.get("method") == "macro.run"
          and good.get("params", {}).get("name") == "observe.diff", str(good)[:120])
    check(f"[{shape}] a positional-token macro.run line is text_suspect",
          isinstance(bad, dict) and bad.get("kind") == "text_suspect"
          and bad.get("bad_token") == "observe.diff", str(bad)[:120])

    class _Cap(_lg.Handler):
        def __init__(self):
            super().__init__(_lg.WARNING); self.lines = []

        def emit(self, r):
            try:
                self.lines.append(r.getMessage())
            except Exception:
                pass

        def has(self, *subs):
            return any(all(x in ln for x in subs) for ln in self.lines)

    _root = _lg.getLogger(); _cap = _Cap(); _root.addHandler(_cap); _lvl = _root.level
    _root.setLevel(_lg.WARNING)
    try:
        _pbad = os.path.join(_tf.mkdtemp(), "t7bad.ak")
        open(_pbad, "w").write("macro.run observe.diff bench=sandbox before=o0\n")
        d("admin", "wf.load", {"bench": "sandbox", "file": _pbad, "branch": "t7bad"})
        check(f"[{shape}] wf.load WARNS on the text-suspect line",
              _cap.has("[wf] load", "parsed as TEXT", "observe.diff"))
        aj = d("admin", "wf.advance", {"bench": "sandbox", "branch": "t7bad", "n": 9, "as": "job"})
        check(f"[{shape}] wf.advance as=job on a text-only branch → text_only, no job id (not 'dispatched')",
              aj.get("status") == "text_only" and aj.get("job_id") is None and aj.get("steps") == 0,
              str(aj)[:120])
        _pok = os.path.join(_tf.mkdtemp(), "t7ok.ak")
        open(_pok, "w").write("macro.run name=observe.diff bench=sandbox before=o0 after=o1 as=inline\n")
        d("admin", "wf.load", {"bench": "sandbox", "file": _pok, "branch": "t7ok"})
        aj2 = d("admin", "wf.advance", {"bench": "sandbox", "branch": "t7ok", "n": 9, "as": "job"})
        check(f"[{shape}] wf.advance as=job on the name= line submits a JOB (job id present, 1 step)",
              aj2.get("status") == "dispatched" and aj2.get("job_id") and aj2.get("steps") == 1,
              str(aj2)[:120])
    finally:
        _root.removeHandler(_cap); _root.setLevel(_lvl)


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a bench workflow is a script-and-log in one structure "
          "(write/advance/rewind/branch, every call an observation with a strictly increasing at_seq, "
          "the rewind kept); wf.dispatch mints an immutable exec membrane + ONE world chronon per "
          "dispatch, a corrected dispatch is a new record, and dispatch to the world needs "
          "responsible:decide — on both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
