#!/usr/bin/env python3
"""
F51 — pulse closeout: the 76% rejection had two named causes; this locks the fixes.

Cause A — pulse.emit_bulk was NOT on the socket elevation allowlist, so every hourly bot flush was
clamped to local and rejected (bulk=0 in production). Cause B — a view of a NONEXISTENT concept was
routed through the ERROR path, so junk crawler slugs inflated `rej` and destroyed its alarm value.

After the fix: `rej` means STRUCTURAL failure only; a miss is a counted FACT (curation signal), not a
reject; the hourly bot flush is allowed; and a one-off pulse.repair clears dangling index memberships
left by pre-C2 compaction. This eval drives the kernel-side behaviour.

Run:  python test/pulse_closeout_eval.py     (exit 0 = all pass)
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
    # ── 2.1 (Cause A) — pulse.emit_bulk is on the socket elevation allowlist ──
    import api.portals.cell_ipc as _ipc
    check("Cause A: pulse.emit_bulk is on the internal elevation allowlist",
          "pulse.emit_bulk" in _ipc._INTERNAL_ELEVATION_METHODS, str(sorted(_ipc._INTERNAL_ELEVATION_METHODS)))

    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts import pulse as _pulse
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_pulse_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data, tok="admin"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    # a REAL concept to emit against
    nuc = k.manager.shared_nucleus
    key = nuc.put_atom("[concept] test pulse target", {"role": "concept"}, author="admin")
    nuc.core.put_alias(key, "concept:testpulse")

    _pulse._EMIT_COUNTERS.update({"emits": 0, "bulk": 0, "seen": 0, "rejected": 0, "miss": 0})
    _pulse._MISS_RING.clear()

    # ── a real emit is recorded ──
    r_ok = d("pulse.emit", {"concept": "concept:testpulse", "surface": "word"})
    check("a real concept emit is recorded", r_ok.get("recorded") is True and not r_ok.get("miss"),
          str(r_ok))

    # ── 2.2 (Cause B) — a miss is a FACT, not an error ──
    r_miss = d("pulse.emit", {"concept": "nonexistent-junk-slug", "surface": "word"})
    check("Cause B: a miss returns a NON-error result (recorded=False, miss=True), never raises",
          "error" not in r_miss and r_miss.get("recorded") is False and r_miss.get("miss") is True,
          str(r_miss))
    check("Cause B: a miss increments `miss`, NOT `rejected`",
          _pulse._EMIT_COUNTERS["miss"] == 1 and _pulse._EMIT_COUNTERS["rejected"] == 0,
          str(_pulse.emit_counters()))

    # ── 2.2 — pulse.stats exposes the counters + the miss ring ──
    st = d("pulse.stats", {})
    check("pulse.stats reports counters (seen/emit/bulk/miss/rejected) + the recent miss ring",
          st.get("miss") == 1 and st.get("rejected") == 0
          and "nonexistent-junk-slug" in (st.get("recent_misses") or []), str(st)[:200])

    # ── emit_bulk stores a summary; bulk counter moves ──
    r_bulk = d("pulse.emit_bulk", {"records": [
        {"day": "2026-09-01", "concept": "botjunk-a", "surface": "word", "ref": "bot", "count": 5},
        {"day": "2026-09-01", "concept": "concept:testpulse", "surface": "word", "ref": "bot", "count": 3},
        {"day": "2026-09-01", "concept": "botjunk-b", "surface": "hall", "ref": "bot", "count": 2}]})
    check("pulse.emit_bulk records a bot summary (bulk counter moves, no Cause-B interaction)",
          _pulse._EMIT_COUNTERS["bulk"] >= 1 and "error" not in r_bulk, str(r_bulk)[:160])

    # ── 2.5 — pulse.repair removes dangling index memberships; idempotent ──
    core = nuc.core
    core.add_to_collection(_pulse.S_CONCEPT + "ghostA", "deadkey_aaaa")   # atom never existed → dangling
    core.add_to_collection(_pulse.S_SRC + "ghostB", "deadkey_bbbb")
    core.add_to_collection(_pulse.S_VISIT + "ghostC", "deadkey_cccc")
    core.add_to_collection(_pulse.S_CONCEPT + "live", key)               # a LIVE member (must survive)
    rep = d("pulse.repair", {})
    check("pulse.repair removes dangling memberships (pre-C2 residue)",
          rep.get("dangling_removed", 0) >= 3, str(rep))
    check("pulse.repair keeps a LIVE membership (only dangling removed)",
          key in (core.get_collection_members(_pulse.S_CONCEPT + "live") or []), "live member survived")
    rep2 = d("pulse.repair", {})
    check("pulse.repair is idempotent (a second run removes 0)",
          rep2.get("dangling_removed", 0) == 0, str(rep2))

    # ── 2.4 — the Health pulse segment carries `miss` ──
    import inspect
    ksrc = inspect.getsource(KernelDispatcher._schedule_health_heartbeat) \
        if hasattr(KernelDispatcher, "_schedule_health_heartbeat") else ""
    src_ok = "miss=%s" in open(os.path.join(ROOT, "lib/akasha/kernel.py"), encoding="utf-8").read()
    check("Health pulse segment carries a `miss` field (pulse(seen= emit= bulk= miss= rej=))", src_ok)

    # ── 2.3.2 — the word shell beacons only a FOUND atom (no `|| NAME` fallback) ──
    wsh = open(os.path.join(ROOT, "services/static/word/index.html"), encoding="utf-8").read()
    check("Cause B (client): the /a/ shell beacons only a found atom (no NAME fallback)",
          "c.atom.alias || c.atom.key)) || NAME" not in wsh
          and "if (navigator.sendBeacon && _pk)" in wsh, "beacon gated on found atom")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — pulse closeout holds: emit_bulk can elevate (Cause A); a miss is a counted "
          "fact not a reject, exposed via pulse.stats (Cause B); the Health line carries `miss`; the "
          "shell beacons only a found atom; and pulse.repair clears dangling index memberships "
          "idempotently. `rej` now means structural failure only.")
    sys.exit(0)


if __name__ == "__main__":
    main()
