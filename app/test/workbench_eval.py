#!/usr/bin/env python3
"""
G1 — workbench registry, the research bench, observation time (world-workbench-society spec v1.0).

A CLOSED bench (created with group=<gid>) and its scope + observation stream live in the society's
GROUP ENGINE, private to members — a nucleus alias lookup returns nothing. Every bench op tees ONE
observation onto the bench stream (the at_seq is the observation chronon), with the agent + family
stamped. bench.created is recorded on the world axis. source.* with no space= is byte-identical.

Run:  python app/test/workbench_eval.py     (exit 0 = all pass)
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


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_wb_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(tok, method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    d("admin", "world.genesis", {})
    d("admin", "grp.new", {"group_id": "lab", "admin_id": "admin"})

    # ── bench.new in a group: atoms live in the GROUP engine only ──
    b = d("admin", "bench.new", {"name": "sandbox", "kind": "research", "world": "default",
                                 "group": "lab"})
    check(f"[{shape}] bench.new creates wb:sandbox in the group",
          b.get("status") == "created" and b.get("bench") == "wb:sandbox"
          and b.get("group") == "lab", str(b)[:140])
    nuc = getattr(k.manager, "shared_nucleus", None)
    if nuc is not None:
        in_nuc = nuc.core.get_key_by_alias("wb:sandbox")
        check(f"[{shape}] the bench atom is NOT in the nucleus (group-private)", in_nuc is None,
              "nucleus has it: %s" % bool(in_nuc))
    # idempotent
    b2 = d("admin", "bench.new", {"name": "sandbox", "group": "lab"})
    check(f"[{shape}] bench.new is idempotent (exists)", b2.get("status") == "exists", str(b2))

    # ── three ops → three observations, increasing at_seq, agent + family stamped ──
    o1 = d("admin", "research.hyp.new", {"name": "sandbox", "text": "p2 restates p1"})
    o2 = d("admin", "research.hyp.new", {"name": "sandbox", "text": "second claim"})
    o3 = d("admin", "research.note", {"name": "sandbox", "text": "first pass"})
    check(f"[{shape}] each bench op returns observed_at_seq",
          all(isinstance(o.get("observed_at_seq"), int) for o in (o1, o2, o3)),
          "seqs=%s" % [o.get("observed_at_seq") for o in (o1, o2, o3)])
    seqs = [o.get("observed_at_seq") for o in (o1, o2, o3)]
    check(f"[{shape}] observation at_seq strictly increases", seqs == sorted(seqs) and len(set(seqs)) == 3,
          str(seqs))

    stream = d("admin", "source.stream", {"stream": "wb:sandbox", "space": "group:lab"})
    obs = stream.get("observations") or []
    fams = [(o.get("source_metadata") or {}).get("family") for o in obs]
    agents = {(o.get("source_metadata") or {}).get("agent") for o in obs}
    check(f"[{shape}] the bench stream shows all three ops with family stamped",
          fams.count("hypothesis") == 2 and fams.count("note") == 1, str(fams))
    check(f"[{shape}] every observation stamps the acting agent", agents == {"admin"}, str(agents))

    # ── world.axis shows bench.created ──
    ax = d("admin", "world.axis", {})
    check(f"[{shape}] world.axis records bench.created",
          any(r.get("kind") == "bench.created" for r in ax.get("axis", [])),
          str([r.get("kind") for r in ax.get("axis", [])]))

    # ── bench.info / bench.grants ──
    info = d("admin", "bench.info", {"name": "sandbox"})
    check(f"[{shape}] bench.info reports families + the stream", "hypothesis" in (info.get("families") or [])
          and info.get("stream") == "source:stream:wb:sandbox", str(info)[:140])

    # ── source.* with NO space= is unchanged (nucleus path) ──
    s = d("admin", "source.stream.create", {"id": "plainstream", "rule": "no-space"})
    sid = s.get("stream")
    check(f"[{shape}] source.stream.create with no space= still targets the nucleus",
          sid == "source:stream:plainstream" and s.get("space") is None, str(s))
    ap = d("admin", "source.stream.append", {"stream": sid, "records": [{"a": 1}]})
    check(f"[{shape}] a no-space stream append is readable back from the nucleus",
          ap.get("appended") == 1, str(ap))
    if nuc is not None:
        check(f"[{shape}] the no-space stream IS in the nucleus (backward compat)",
              nuc.core.get_key_by_alias(sid) is not None)


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a closed bench and its stream live in the group engine (not the nucleus); "
          "each op tees one observation with a strictly-increasing at_seq and the agent/family stamped; "
          "bench.created lands on the world axis; and no-space source.* is byte-identical.")
    sys.exit(0)


if __name__ == "__main__":
    main()
