#!/usr/bin/env python3
"""
Source Data Layer eval — the acceptance criteria of Akasha Source Data Layer Spec v0.3 §16.

Drives the `source.*` concept model through an in-process kernel and asserts the non-negotiable
invariants: source atoms carry NO interpretation, a frozen pool is immutable, bridges are additive
(the raw atom is never mutated), failure stays visible in counts, an earlier frozen pool remains
enumerable for a rerun, the same source item can hold incompatible interpretations, Akasha Time
proves the pool was frozen BEFORE a later bridge, and a lab audit distinguishes grounded from
ungrounded evidence.

Run:  python test/source_layer_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_source_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # ── 1. register an external source ──
    reg = d("source.register", {"provider": "British Library", "collection": "book images",
                                "uri": "https://data.bl.uk/", "rights": "Public Domain Mark",
                                "name": "bl"})
    check("register: external source recorded with provider/rights",
          reg.get("status") == "registered" and reg.get("source", "").startswith("source:src:"), str(reg))
    src = reg["source"]

    # ── 2. acquire — 4 records: 3 with a locator, 1 malformed (failure is evidence) ──
    recs = [{"id": "037", "title": "Plate 37", "url": "https://img/037.jpg"},
            {"id": "051", "title": "Plate 51", "url": "https://img/051.jpg"},
            {"id": "099", "title": "Plate 99 (no image)"}]           # METADATA_ONLY (no locator)
    acq = d("source.acquire", {"source": src, "rule": "first 4 plates of shelfmark X",
                               "records": recs})
    # a malformed JSONL line via text= (kept as UNRESOLVED failure, not dropped)
    acq2 = d("source.acquire", {"source": src, "rule": "one broken line",
                                "text": "{bad json line"})
    check("acquire: 3 records became source items (2 ACQUIRED + 1 METADATA_ONLY)",
          acq.get("acquired") == 3 and acq.get("total") == 3, str(acq))
    check("acquire: a malformed line is RETAINED as UNRESOLVED, not silently dropped",
          acq2.get("unresolved") == 1, str(acq2))
    item037 = "source:item:bl:037"

    # ── 2b. the Source Atom is physically in the SHARED nucleus, so a GUEST session (the real
    #        Source Viewer) can read it — the whole point of the layer being human-inspectable ──
    g = d("session.guest.create", {})
    gt = (g or {}).get("binding_key") or (g or {}).get("session_token")
    guest_read = d("source.read", {"id": item037}, tok=gt, trust="network") if gt else {"__error__": "no guest"}
    check("guest-readable: a GUEST session can read the source atom (universal → nucleus, not a private cortex)",
          isinstance(guest_read, dict) and guest_read.get("item") == item037
          and guest_read.get("source_metadata"), str(guest_read)[:120])

    # ── 3. §16 — the Source Atom has NO experiment-derived claim as a source fact ──
    rd = d("source.read", {"id": item037})
    keys = set((rd.get("source_metadata") or {}).keys())
    check("read: source atom carries source + acquisition metadata, and NO interpretation fields",
          rd.get("status") in ("ACQUIRED", "METADATA_ONLY")
          and "title" in keys
          and not (keys & {"subject", "hypothesis", "relevance", "label", "classification", "reading"}),
          str(sorted(keys)))

    # ── 4. status — the failed/unresolved item stays visible in the counts ──
    st = d("source.status", {"source": src})
    check("status: unresolved/failed items remain counted (never disappear)",
          st.get("by_status", {}).get("UNRESOLVED", 0) >= 1
          and st.get("unresolved_or_failed", 0) >= 1, str(st.get("by_status")))

    # ── 5. build a pool, add the acquired items, freeze it ──
    pc = d("source.pool.create", {"name": "bl_visual_raw", "source": src,
                                  "rule": "all acquired BL plates", "version": "v1"})
    pool = pc["pool"]
    for it in ("source:item:bl:037", "source:item:bl:051", "source:item:bl:099"):
        d("source.pool.add", {"pool": pool, "id": it})
    lsp = d("source.pool.ls", {"pool": pool})
    check("pool.ls: the COMPLETE pool is enumerable (every eligible member)",
          lsp.get("count") == 3, str(lsp.get("count")))
    fr = d("source.pool.freeze", {"pool": pool})
    check("pool.freeze: pool becomes FROZEN with an Akasha-Time marker",
          fr.get("status") == "FROZEN" and isinstance(fr.get("at_seq"), int) and fr.get("member_count") == 3,
          str(fr))
    pool_at = fr["at_seq"]

    # ── 6. §16 — a frozen pool cannot gain members (immutability) ──
    add_after = d("source.pool.add", {"pool": pool, "id": "source:item:bl:037"})
    check("pool immutability: adding to a FROZEN pool is refused (a change needs a new version)",
          isinstance(add_after, dict) and "__error__" in add_after
          and "FROZEN" in json.dumps(add_after), str(add_after)[:120])

    # ── 7. bridge — an interpreted atom (a mock lab slot) SELECTS a source item ──
    #     additive: the source atom is not mutated; the bridge records the operation + Akasha Time
    before = d("source.read", {"id": item037})
    br = d("source.bridge", {"src": "lab:blvh:slot:051", "dst": item037, "rel": "selected_from",
                             "by": "blvh:model:siglip2_so400m", "run": "v0.3", "params": "rank=1"})
    after = d("source.read", {"id": item037})
    check("bridge: is additive — the source atom is byte-for-byte unchanged after being interpreted",
          before.get("source_metadata") == after.get("source_metadata")
          and before.get("status") == after.get("status"), str(br)[:100])
    check("Akasha Time: the pool was frozen BEFORE the bridge (at_seq ordering proves it)",
          isinstance(br.get("at_seq"), int) and br["at_seq"] > pool_at,
          f"pool_at={pool_at} bridge_at={br.get('at_seq')}")

    # ── 8. §16 — the SAME source item holds a second, incompatible interpretation, no mutation ──
    d("source.bridge", {"src": "lab:other:reject_099", "dst": item037, "rel": "rejects",
                        "by": "human:reviewer"})
    tr = d("source.trace", {"id": item037})
    interps = {(i.get("interpreted"), i.get("relation")) for i in tr.get("interpretations", [])}
    check("trace (source → interpretations): the same raw item carries BOTH selected_from and rejects",
          ("lab:blvh:slot:051", "selected_from") in interps
          and ("lab:other:reject_099", "rejects") in interps, str(sorted(interps)))

    # ── 9. trace the reverse direction (interpreted atom → its source items) ──
    tr2 = d("source.trace", {"id": "lab:blvh:slot:051"})
    srcs = {s.get("source_item") for s in tr2.get("sources", [])}
    check("trace (interpretation → source): the lab slot resolves back to source:item:bl:037",
          item037 in srcs, str(sorted(srcs)))

    # ── 10. §16 — a later model version can be rerun against the EARLIER frozen pool ──
    lsp2 = d("source.pool.ls", {"pool": pool})
    check("rerun: the earlier frozen pool is still fully enumerable for a v0.3 rerun",
          lsp2.get("status") == "FROZEN" and lsp2.get("count") == 3, str(lsp2.get("count")))

    # ── 11. lab audit — undeclared lab is UNGROUNDED; a declared CORPUS lab on a frozen pool + bridge is GROUNDED ──
    au0 = d("source.audit", {"lab": "lab:blvh"})
    check("audit: an undeclared laboratory is UNGROUNDED (no evidence profile)",
          au0.get("evidence_status") == "UNGROUNDED" and au0.get("grounded") is False, str(au0.get("findings")))
    decl = d("source.lab.declare", {"lab": "lab:blvh", "klass": "CORPUS", "pool": pool,
                                    "primary_source": src})
    check("lab.declare: a CORPUS lab pointing at a FROZEN pool is GROUNDED",
          decl.get("evidence_status") == "GROUNDED", str(decl))
    au1 = d("source.audit", {"lab": "lab:blvh"})
    check("audit: the declared, frozen-pool-backed, bridged lab is grounded",
          au1.get("acquisition_class") == "CORPUS" and au1.get("evidence_status") == "GROUNDED", str(au1))

    # ── 12. observational path — stream + reproducible snapshot ──
    d("source.stream.create", {"id": "quakes", "source": src, "rule": "USGS M>=4", "polling": "5m"})
    d("source.stream.append", {"stream": "source:stream:quakes",
                               "records": [{"id": "q1", "mag": 4.2}, {"id": "q2", "mag": 5.1}]})
    snap = d("source.snapshot.create", {"stream": "source:stream:quakes", "name": "t1"})
    check("stream+snapshot: a reproducible frozen window pins the observations for replay",
          snap.get("status") == "FROZEN" and snap.get("member_count") == 2, str(snap))

    # ── 13. CLI-first convention — the same operators must FLOW through the shlex parser + router ──
    try:
        from api.gateway import AkashaGateway
        from api.portals.stdio import run_single_shot
        gw = AkashaGateway(kernel_client=k)
        out = run_single_shot("source.register provider=CLI collection=smoke name=clitest", gw)
        cli_ok = isinstance(out, str) and '"source:src:clitest"' in out
        out2 = run_single_shot("source.pools", gw)
        cli_ok = cli_ok and isinstance(out2, str) and '"pools"' in out2
    except Exception as exc:
        cli_ok, out = False, str(exc)
    check("CLI-first: source.* flows through the real CLI (shlex parser + router), not RPC-only",
          cli_ok, str(out)[:100])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — Source Data Layer: external material is acquired before interpretation, frozen "
          "into an immutable versioned pool, kept human-inspectable with failures visible, and bridged "
          "additively so the same raw atom carries multiple interpretations without mutation; Akasha "
          "Time proves the pool preceded the interpretation; a lab audit separates grounded from "
          "ungrounded evidence.")
    sys.exit(0)


if __name__ == "__main__":
    main()
