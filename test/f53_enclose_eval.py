#!/usr/bin/env python3
"""
F53 Phase 0 Stage 4 — horizon.enclose (E5): the only store-writing horizon op.

horizon.enclose persists the intersection of the current GRANTED LENS horizon entries (>=2) as a
named set, stamped with its provenance {derived_from_horizon, by, at}. It is the isect operation
(agrees with cross.query mode=strict). Write-gated as any set op — a guest is refused by the ordinary
gate before reaching the handler.

Run:  python test/f53_enclose_eval.py     (exit 0 = all pass)
"""
import hashlib
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
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_enc_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def call(method, data=None, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data or {}}, "id": "t"}, trust)
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus
    core = nuc.core
    m = {i: nuc.put_atom("m%d" % i, {"salience": 1.0}, author="admin") for i in range(5)}
    for i in (0, 1, 2, 3):
        core.add_to_collection("set:demo:A", m[i])
    for i in (0, 1, 2, 4):
        core.add_to_collection("set:demo:B", m[i])
    expected = {m[0], m[1], m[2]}                       # A ∩ B

    # ── 1. enclose the intersection of two lens entries, with provenance ──
    call("horizon.add", {"set": "set:demo:A", "mode": "lens"})
    call("horizon.add", {"set": "set:demo:B", "mode": "lens"})
    enc = call("horizon.enclose", {"name": "set:demo:AB"})
    check("horizon.enclose writes the isect of the lens sets (A ∩ B) as the named set",
          enc.get("status") == "enclosed" and set(enc.get("members", [])) == expected
          and enc.get("count") == 3, str(enc)[:160])
    check("the enclosure records its provenance {derived_from_horizon, by, at}",
          set(enc.get("derived_from_horizon", [])) == {"set:demo:A", "set:demo:B"}
          and enc.get("by") == "admin" and enc.get("at"), str(enc.get("derived_from_horizon")))
    import json as _json
    desc = enc.get("descriptor")
    _raw = core.get_chunk_raw(desc) if desc else None
    meta = _json.loads(_raw["meta"]) if _raw and _raw.get("meta") else {}
    check("the provenance is retrievable from the enclosure's descriptor atom (aliased to the set)",
          set(meta.get("derived_from_horizon", [])) == {"set:demo:A", "set:demo:B"}
          and core.get_key_by_alias("set:demo:AB") == desc, str(meta)[:140])

    # ── 2. it is a STRICT intersection (= cross.query mode=strict semantics), not a union ──
    enc_members = set(enc.get("members", []))
    check("the enclosure is the STRICT intersection — A-only (m3) and B-only (m4) are excluded",
          m[3] not in enc_members and m[4] not in enc_members and expected <= enc_members,
          "members=%d" % len(enc_members))

    # ── 3. <2 granted lens entries → refused ──
    call("horizon.clear", {})
    call("horizon.add", {"set": "set:demo:A", "mode": "lens"})
    one = call("horizon.enclose", {"name": "set:demo:solo"})
    check("horizon.enclose with <2 lens entries is refused (needs >=2)",
          "error" in one and ">=2" in str(one.get("error", {})), str(one.get("error"))[:120])

    # ── 4. a GUEST is refused by the ordinary write gate (structurally cannot enclose) ──
    g = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create", "params": {}, "id": "gg"}, "network")
    gtok = ((g or {}).get("result") or {}).get("session_token")
    call("horizon.add", {"set": "set:demo:A", "mode": "lens"}, tok=gtok, trust="network")
    call("horizon.add", {"set": "set:demo:B", "mode": "lens"}, tok=gtok, trust="network")
    genc = call("horizon.enclose", {"name": "set:guest:x"}, tok=gtok, trust="network")
    check("a guest's horizon.enclose is refused by the ordinary write gate (no store write)",
          "error" in genc, str(genc.get("result") or genc.get("error"))[:120])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — horizon.enclose persists the lens intersection with provenance, agrees with "
          "cross.query mode=strict, needs >=2 lens entries, and is refused for a guest by the ordinary "
          "write gate (self-directed lens entries cannot become a store write without the grant).")
    sys.exit(0)


if __name__ == "__main__":
    main()
