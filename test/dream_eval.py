#!/usr/bin/env python3
"""
Dream eval — the asynchronous incubation / bridge-proposer.

dream is deliberately unlike the other explorers: assoc fills 1-hop high-confidence gaps;
sim/node.sim rank what is already near; dream finds atoms NEAR in meaning but FAR in the
explicit graph (the "affinity gap" — connections the graph is missing) and stages them as
tentative (tent:) links for a HUMAN to confirm. It runs as a LOW-priority background JCL job
("sleep on it"): the first call returns "dreaming…", a later call returns the candidates.

  D1 submit   — dream id= returns status="dreaming" with a background job_id.
  D2 ready    — after the job completes, dream id= returns status="ready" with candidates
                (near-in-meaning atoms), each staged as a tent: link.
  D3 human    — the job NEVER links on its own: while ready-but-unconfirmed the focus has
                tent: links and ZERO real calc:hidden_affinity links. Approval is mandatory.
  D4 confirm  — dream.confirm promotes one tent: link to a real calc:hidden_affinity edge.
  D5 gap      — an atom semantically similar to the focus but ALREADY linked is NOT proposed
                (dream proposes only NEW connections — the gap).
  D6 forget   — dream.forget drops the remaining staged candidates.

Run:  python test/dream_eval.py
"""
import os
import sys
import time
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:10} {detail}")


def main():
    print("\n  dream eval — async incubation + affinity-gap + human confirm\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_dream_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    def key(r):
        return (r or {}).get("key")

    cortex = k.manager.get_session("admin").local_cortex
    focus = key(d("w", {"content": "The swallow migrates north as spring arrives and warms the air"}))
    related = key(d("w", {"content": "Warblers fly back to northern nests when the migrating season warms"}))
    d("w", {"content": "Migrating birds return north again each spring to breed and to nest"})
    # A semantically-similar atom that is ALREADY linked to the focus (should be excluded).
    linked = key(d("w", {"content": "Swallows and swifts migrate north together as the warm spring returns"}))
    d("ln", {"src": focus, "dst": linked, "rel": "calc:associated_with"})

    # D1 — submit.
    sub = d("dream", {"id": focus})
    record("D1 submit", sub.get("status") == "dreaming" and bool(sub.get("job_id")),
           f"status={sub.get('status')}, job={sub.get('job_id')}")

    # D2 — poll to ready.
    ready = None
    for _ in range(60):
        time.sleep(0.25)
        r = d("dream", {"id": focus})
        if r.get("status") == "ready":
            ready = r
            break
        if r.get("status") == "failed":
            break
    cands = (ready or {}).get("candidates", [])
    cand_keys = [c["dst"] for c in cands]
    record("D2 ready", bool(ready) and len(cands) >= 1 and related in cand_keys,
           f"status={ready.get('status') if ready else 'timeout'}, "
           f"candidates={len(cands)}, related-proposed={related in cand_keys}")

    # D3 — human mandatory: staged as tent:, NO real affinity link yet.
    links = cortex.get_adjacent_links(focus) or []
    has_tent = any(l[1].startswith("tent:") for l in links)
    no_real = not any(l[1] == "calc:hidden_affinity" for l in links)
    record("D3 human", has_tent and no_real,
           f"tent staged={has_tent}, no auto-link={no_real}")

    # D4 — confirm one.
    conf = d("dream.confirm", {"src": focus, "dst": related})
    links2 = cortex.get_adjacent_links(focus) or []
    real_now = any(l[0] == related and l[1] == "calc:hidden_affinity" for l in links2)
    tent_gone = not any(l[0] == related and l[1].startswith("tent:") for l in links2)
    record("D4 confirm", conf.get("status") == "confirmed" and real_now and tent_gone,
           f"confirmed={conf.get('status')}, real-link={real_now}, tent-gone={tent_gone}")

    # D5 — the gap: the already-linked similar atom was never proposed.
    record("D5 gap", linked not in cand_keys,
           f"already-linked atom excluded from candidates={linked not in cand_keys}")

    # D6 — forget the rest.
    forget = d("dream.forget", {"src": focus, "all": "yes"})
    links3 = cortex.get_adjacent_links(focus) or []
    record("D6 forget", forget.get("status") == "forgotten"
           and not any(l[1].startswith("tent:") for l in links3),
           f"dropped={forget.get('dropped')}, tent-links-remaining="
           f"{sum(1 for l in links3 if l[1].startswith('tent:'))}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the dream incubation flow regressed.")
        return 1
    print("\nRESULT: PASS — dream incubates asynchronously (JCL background), proposes "
          "near-in-meaning / far-in-graph bridges, links only after human confirmation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
