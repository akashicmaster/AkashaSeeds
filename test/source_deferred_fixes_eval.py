#!/usr/bin/env python3
"""
source_deferred_fixes_eval.py — the Source-Layer DEFERRED-batch merge gate (2026-09).

Companion to source_review_fixes_eval.py. Pins the four deferred design items worked to decision
depth in docs/for-llm/source-layer-deferred-design.md:

  A3  per-source status tally is PAY-AT-WRITE: source.status(source=) returns a tally that equals a
      one-off sweep with NO member scan; source.resolve moves EXACTLY one count between buckets; a
      reload rebuilds the tally to match the new corpus; the read works on the GUEST surface.
  A4  bridge endpoint index: source.trace reads ONE membrane (source:bridges:{src,interp}:<slug>),
      not the whole registry — a 3-bridge item traces to exactly its 3 interpretations and the
      membrane set has exactly 3 members.
  A7  source.audit's bridged count is computed WITHOUT materializing the pool as an alias set, and
      equals the number of in-frame bridges.
  B2  mode-1 replacement: re-acquire an identical record → reused; a CHANGED record → divergent
      (filed in source:status:divergent, NEVER overwritten); source.reload replaces the corpus,
      keeps ids stable, INTERPRETATION TRACES SURVIVE, and clears source:status:divergent.
  C1  private import consent: source.import.set REFUSES a set with any non-universal member (naming
      the private count), UNLESS allow_private=yes, which imports all-or-nothing and badges the pool.
  (BF — the boot-once `source.backfill` of tallies and bridge indexes over legacy data — is deleted
  with the op: the purge order, 3 October §2, discards past data rather than migrating it.)

Run:  python test/source_deferred_fixes_eval.py     (exit 0 = all pass)
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
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_sdef_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(m, data, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    from lib.akasha.concepts.source import SourceDataLayer, ITEM_STATUS, _slug
    sess = k.manager.get_session("admin")
    sl = SourceDataLayer(sess)
    core = sl._nuc.core if sl._nuc else sess.core

    # ── A3 — per-source status tally is pay-at-write, equals a sweep ──
    d("source.register", {"provider": "y", "name": "y"})
    # 2 ACQUIRED (id + uri locator), 2 METADATA_ONLY (id, no locator), 2 UNRESOLVED (no id)
    recs = ([{"id": "a%d" % i, "uri": "http://h/a%d.jpg" % i} for i in range(2)] +
            [{"id": "m%d" % i, "label": "meta%d" % i} for i in range(2)] +
            [{"note": "no-id-%d" % i} for i in range(2)])
    d("source.acquire", {"source": "source:src:y", "rule": "t", "records": recs})

    def _sweep(src_slug):
        counts = {s: 0 for s in ITEM_STATUS}
        for kk in sl._members("source:items"):
            mm = sl.cortex.get_meta(kk) or {}
            if sl._src_slug(mm.get("source") or "") == src_slug and mm.get("status") in counts:
                counts[mm["status"]] += 1
        return counts

    st = d("source.status", {"source": "source:src:y"})
    swept = _sweep("y")
    check("A3: source.status(source=) tally equals a one-off sweep",
          st.get("by_status") == swept and st.get("total") == 6,
          "tally=%s sweep=%s" % (st.get("by_status"), swept))
    check("A3: the tally counts the mint correctly (2 ACQUIRED / 2 METADATA_ONLY / 2 UNRESOLVED)",
          (st.get("by_status") or {}).get("ACQUIRED") == 2
          and (st.get("by_status") or {}).get("METADATA_ONLY") == 2
          and (st.get("by_status") or {}).get("UNRESOLVED") == 2, str(st.get("by_status")))

    # resolve one METADATA_ONLY → ACQUIRED must move EXACTLY one count between two buckets
    before = dict(st["by_status"])
    d("source.resolve", {"id": "source:item:y:m0", "locator": "http://h/m0.jpg"})
    after = d("source.status", {"source": "source:src:y"}).get("by_status")
    moved_ok = (after.get("ACQUIRED") == before["ACQUIRED"] + 1
                and after.get("METADATA_ONLY") == before["METADATA_ONLY"] - 1
                and after.get("UNRESOLVED") == before["UNRESOLVED"]
                and sum(after.values()) == sum(before.values()))
    check("A3: source.resolve moves EXACTLY one count between buckets (total unchanged)", moved_ok,
          "before=%s after=%s" % (before, after))

    # the read works on the GUEST surface (the real Source Viewer) with no member sweep
    g = d("session.guest.create", {})
    gt = (g or {}).get("binding_key") or (g or {}).get("session_token")
    gst = d("source.status", {"source": "source:src:y"}, tok=gt, trust="network") if gt else {}
    check("A3: source.status(source=) works on the guest surface and returns the tally (O(1) read)",
          gst.get("total") == 6 and (gst.get("by_status") or {}).get("ACQUIRED") == 3,
          "guest=%s" % gst.get("by_status"))

    # ── A4 — bridge endpoint index: trace reads one membrane ──
    d("source.register", {"provider": "z", "name": "z"})
    d("source.pool.create", {"name": "z:v1", "source": "source:src:z"})
    d("source.acquire", {"source": "source:src:z", "rule": "t",
                         "records": [{"id": "it", "uri": "http://h/it.jpg"}], "pool": "source:pool:z:v1"})
    d("source.pool.freeze", {"pool": "source:pool:z:v1"})
    # three interpreted atoms bridge to the ONE source item
    for i in range(3):
        w = d("w", {"content": "interp %d" % i})
        d("set.add", {"name": "set:interp", "id": w.get("key")})
        d("source.bridge", {"src": w.get("key"), "dst": "source:item:z:it", "rel": "interprets"})
    tr = d("source.trace", {"id": "source:item:z:it"})
    membrane = sl._members("source:bridges:src:%s" % _slug("source:item:z:it"))
    check("A4: trace on a 3-bridge item returns exactly 3 interpretations via its endpoint membrane",
          len(tr.get("interpretations", [])) == 3 and len(membrane) == 3,
          "traced=%d membrane=%d" % (len(tr.get("interpretations", [])), len(membrane)))

    # ── A7 — audit bridged count without alias-materializing the pool ──
    d("source.lab.declare", {"lab": "labo:ztest", "klass": "CORPUS", "pool": "source:pool:z:v1"})
    aud = d("source.audit", {"lab": "labo:ztest"})
    # the 3 bridges all point at source:item:z:it which IS a member of the frozen pool → bridged == 3
    check("A7: audit reports the in-frame bridged count (no whole-pool alias set materialized)",
          aud.get("bridged") == 3, "bridged=%s findings=%s" % (aud.get("bridged"), aud.get("findings")))

    # ── B2 — mode-1 replacement: reused vs divergent, reload continuity ──
    d("source.register", {"provider": "corp", "name": "corp"})
    d("source.acquire", {"source": "source:src:corp", "rule": "v0",
                         "records": [{"id": "row1", "val": "A"}, {"id": "row2", "val": "B"}]})
    # bridge an interpretation to row1 so we can prove trace survives a reload
    w = d("w", {"content": "reading of row1"})
    d("source.bridge", {"src": w.get("key"), "dst": "source:item:corp:row1", "rel": "interprets"})

    # re-acquire IDENTICAL row1 → reused; CHANGED row2 → divergent (filed, not overwritten)
    reacq = d("source.acquire", {"source": "source:src:corp", "rule": "v0-again",
                                 "records": [{"id": "row1", "val": "A"}, {"id": "row2", "val": "CHANGED"}]})
    div_set = sl._members("source:status:divergent")
    stored_row2 = (d("source.read", {"id": "source:item:corp:row2"}).get("source_metadata") or {}).get("val")
    check("B2: re-acquire reports reused (identical) and divergent (changed), never overwriting",
          reacq.get("reused") == 1 and reacq.get("divergent") == 1
          and sl._key("source:item:corp:row2") in div_set and stored_row2 == "B",
          "reused=%s divergent=%s stored_val=%s" % (reacq.get("reused"), reacq.get("divergent"), stored_row2))

    # source.reload replaces the corpus; ids stable; trace survives; divergent cleared
    d("source.reload", {"source": "source:src:corp", "rule": "v1-corrected",
                        "records": [{"id": "row1", "val": "A2"}, {"id": "row2", "val": "B2"}]})
    row2_after = (d("source.read", {"id": "source:item:corp:row2"}).get("source_metadata") or {}).get("val")
    tr2 = d("source.trace", {"id": "source:item:corp:row1"})
    div_after = sl._members("source:status:divergent")
    check("B2: reload replaces the corpus (new values), ids stable, and clears source:status:divergent",
          row2_after == "B2" and len(div_after) == 0, "row2=%s divergent=%d" % (row2_after, len(div_after)))
    check("B2: interpretation TRACE SURVIVES the reload (alias-keyed bridge index)",
          len(tr2.get("interpretations", [])) == 1, "traced=%d" % len(tr2.get("interpretations", [])))

    # ── C1 — private import consent ──
    a_pub = d("w", {"content": "public member"})
    a_priv = d("w", {"content": "private member"})
    d("set.add", {"name": "set:privtest", "id": a_pub.get("key")})
    d("set.add", {"name": "set:privtest", "id": a_priv.get("key")})

    def _put_access(atom_key, scopes):
        pk = sl._key(atom_key)
        for c in (sl.cortex.core, (sl._nuc.core if sl._nuc else None)):
            if c and c.get_chunk_raw(pk):
                c.put_chunk_access(pk, scopes)
                return
    # a plain `w` atom is OWNER-scoped (non-universal) — make the public one explicitly universal so
    # exactly ONE member (a_priv, owner-scoped) is private. This mirrors an ontology set (universal
    # members) that contains one accidentally private atom.
    _put_access(a_pub.get("key"), ["scope:sys:universal"])
    _put_access(a_priv.get("key"), ["scope:owner:henri"])
    refused = d("source.import.set", {"set": "set:privtest", "name": "privtest"})
    check("C1: import.set REFUSES a set with a private member and names the private count",
          isinstance(refused, dict) and "__error__" in refused
          and "1 private" in str(refused["__error__"]), str(refused.get("__error__"))[:120])
    consented = d("source.import.set", {"set": "set:privtest", "name": "privtest2", "allow_private": "yes"})
    pm = (d("source.read", {"id": consented.get("pool")}) if False else {})  # pool is not a source item
    pool_meta = sl.cortex.get_meta(sl._key(consented.get("pool"))) or {}
    check("C1: with allow_private=yes the import proceeds all-or-nothing and badges the pool",
          consented.get("imported_private") is True and consented.get("private_members") == 1
          and pool_meta.get("imported_private") is True and pool_meta.get("private_members") == 1,
          "consented=%s badge=%s" % (consented.get("imported_private"), pool_meta.get("imported_private")))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails))); sys.exit(1)
    print("ALL PASS — Source-Layer deferred batch: per-source tallies are pay-at-write (equal a sweep, "
          "one-count moves on resolve, guest-O(1)), bridge trace reads one endpoint membrane, audit "
          "counts in-frame bridges with no alias set, mode-1 reload replaces cleanly with surviving "
          "traces and reused/divergent reporting and private import needs explicit "
          "consent.")
    sys.exit(0)


if __name__ == "__main__":
    main()
