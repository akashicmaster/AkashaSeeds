#!/usr/bin/env python3
"""
F53 Phase 0 Stage 1 — the normalized semantic session (E1 uniformity + horizon round-trip).

Every connected client holds ONE session shaped as three parts — identity / granted / self_directed —
IDENTICALLY shaped for admin / resident / guest / LLM. The self-directed horizon is client-writable,
world-ignorable, dies with the session, and can NEVER widen granted (an unreadable entry is retained
but reported `ungranted`). Storage rides the existing context mechanics: in-memory for a read-only
guest, session-atom meta for an owning admin — SAME shape both kinds (that IS the normalization).

Stage 1 is pure addition: no existing method changes meaning. This eval pins the new surface.

Run:  python test/f53_semantic_session_eval.py     (exit 0 = all pass)
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
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_f53_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def call(method, data=None, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data or {}}, "id": "t"}, trust)
        return r if "error" in r else (r.get("result") or {})

    # a fresh guest (read-only session — in-memory context)
    g = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create", "params": {}, "id": "gg"}, "network")
    gtok = ((g or {}).get("result") or {}).get("session_token")

    def gcall(method, data=None):
        return call(method, data, tok=gtok, trust="network")

    STATE_KEYS = {"identity", "granted", "self_directed"}
    SELF_KEYS = {"horizon", "focus", "radius", "axis"}
    GRANT_KEYS = {"read_scopes", "write", "class"}

    # ── E1a. sys.session.state shape — ADMIN (owning session, session-atom meta storage) ──
    sa = call("sys.session.state", {})
    check("admin sys.session.state has the triple {identity, granted, self_directed}",
          set(sa) == STATE_KEYS, str(sorted(sa)))
    check("admin identity.kind=admin; granted.write=True; grant/self shapes exact",
          sa.get("identity", {}).get("kind") == "admin" and sa["granted"].get("write") is True
          and set(sa["granted"]) == GRANT_KEYS and set(sa["self_directed"]) == SELF_KEYS,
          str(sa.get("identity")))
    check("admin granted.read_scopes carries the IAM scopes (admin sees sys:admin)",
          "scope:sys:admin" in (sa["granted"].get("read_scopes") or []), "")

    # ── E1b. sys.session.state shape — GUEST (read-only session, in-memory context) ──
    sg = gcall("sys.session.state")
    check("guest sys.session.state has the SAME top-level shape as admin (E1 uniformity)",
          set(sg) == STATE_KEYS and set(sg.get("granted", {})) == GRANT_KEYS
          and set(sg.get("self_directed", {})) == SELF_KEYS, str(sorted(sg)))
    check("guest identity.kind=guest, carries expires_at (TTL is part of the grant), write=False",
          sg["identity"].get("kind") == "guest" and "expires_at" in sg["identity"]
          and sg["granted"].get("write") is False, str(sg.get("identity")))

    # ── E1c. horizon round-trip works IDENTICALLY on both storage kinds ──
    for label, fn in (("admin(meta)", call), ("guest(memory)", gcall)):
        r = fn("horizon.add", {"set": "set:demo:one", "mode": "lens"})
        ls = fn("horizon.ls", {})
        got = {e["set"]: e for e in (ls.get("horizon") or [])}
        ok = (r.get("status") == "horizon_added" and "set:demo:one" in got
              and got["set:demo:one"]["mode"] == "lens" and got["set:demo:one"]["granted"] is True)
        check("horizon round-trip on %s — add(lens) → ls shows {set,mode,granted}" % label, ok, str(ls))
        m = fn("horizon.mode", {"set": "set:demo:one", "mode": "soft"})
        check("horizon.mode flips mode on %s" % label,
              {e["set"]: e for e in m.get("horizon", [])}.get("set:demo:one", {}).get("mode") == "soft", "")
        rm = fn("horizon.rm", {"set": "set:demo:one"})
        check("horizon.rm removes on %s (removed=1, now empty)" % label,
              rm.get("removed") == 1 and rm.get("horizon") == [], str(rm))

    # ── E1d. ungranted: an unresolvable concept is RETAINED but flagged ungranted (never dropped) ──
    call("horizon.clear", {})
    ru = call("horizon.add", {"set": "no_such_concept_xyz", "mode": "soft"})
    lsu = call("horizon.ls", {})
    ent = {e["set"]: e for e in lsu.get("horizon", [])}.get("no_such_concept_xyz")
    check("an ungranted horizon entry is retained + flagged ungranted (visible, not silently dropped)",
          ru.get("ungranted") is True and ent is not None and ent.get("granted") is False, str(lsu))

    # ── E1e. cap 8 — refuse LOUDLY, never trim ──
    call("horizon.clear", {})
    for i in range(8):
        call("horizon.add", {"set": "set:cap:%d" % i})
    over = call("horizon.add", {"set": "set:cap:8"})
    lsc = call("horizon.ls", {})
    check("horizon cap=8 refuses the 9th LOUDLY and never trims (count stays 8)",
          "error" in over and lsc.get("count") == 8, str(over.get("error") or over)[:120])

    # ── E1f. radius aliases active_scope: writes BOTH, reads prefer radius, active_scope kept ──
    call("sys.scope.set", {"radius": 3})
    st1 = call("sys.session.state", {})
    sc1 = call("sys.scope.get", {})
    check("sys.scope.set radius=3 writes BOTH keys (active_scope=3 kept; session.state radius=3)",
          sc1.get("active_scope") == 3 and st1["self_directed"].get("radius") == 3, str(sc1))
    call("sys.scope.set", {"scope": 5})
    st2 = call("sys.session.state", {})
    sc2 = call("sys.scope.get", {})
    check("sys.scope.set scope=5 still updates radius (both track; reads prefer radius)",
          sc2.get("active_scope") == 5 and st2["self_directed"].get("radius") == 5, str(sc2))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the semantic session is normalized: identity/granted/self_directed is one "
          "shape for every client kind; the horizon round-trips identically on in-memory (guest) and "
          "session-meta (admin) storage; self-directed never widens granted (ungranted entries are "
          "retained + flagged, the cap refuses loudly); and radius aliases active_scope without "
          "removing it.")
    sys.exit(0)


if __name__ == "__main__":
    main()
