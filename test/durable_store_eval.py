#!/usr/bin/env python3
"""
S1-b §2 / §4 — the storage abstraction: local backend proves the writer capabilities; a bucket-only
backend is admitted for archives and refused as a writer.

The S1 storage evals (plan §4):
  • immutable generations + range read round-trip (content-addressed, idempotent);
  • local backend CAS race: two publishers, one pointer, exactly ONE wins, the loser's generation is
    still listed (GC-able) — the HydraDB manifest-GC lesson;
  • lease fencing: a writer whose lease expired cannot renew (fenced out) and a new acquire bumps the
    epoch monotonically;
  • capability refusal: a backend without CAS/leases (the S3 archives mirror) is REFUSED as a writer
    (check_backend(WRITER_REQUIRED)) but ADMITTED as an archives mirror (check_backend(ARCHIVES_REQUIRED));
  • SemanticArtifactStore: put(kind, artifact_id, bytes) → get returns the same bytes.

Pure-stdlib (local filesystem backend); the S3 backend is checked by its DECLARED capabilities only
(no live bucket, no boto3 needed).

Run:  python test/durable_store_eval.py     (exit 0 = all pass)
"""
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.storage import (LocalDurableStore, SemanticArtifactStore, check_backend,
                                    WRITER_REQUIRED, ARCHIVES_REQUIRED)
    from lib.akasha.storage.s3 import S3DurableStore

    root = tempfile.mkdtemp(prefix="akasha_store_")
    s = LocalDurableStore(root)

    # ── capabilities: the local backend proves the full writer set ──
    ok_w, miss_w = check_backend(s.capabilities(), WRITER_REQUIRED)
    check("local backend is admitted as a WRITER (cas + versioning + leases)", ok_w and not miss_w,
          repr(s.capabilities()))

    # ── immutable generations + range read ──
    data = b"the quick brown fox jumps over the lazy dog"
    g1 = s.put_immutable("archives:demo", data)
    g1b = s.put_immutable("archives:demo", data)
    check("put_immutable is content-addressed + idempotent (same bytes → same id, written once)",
          g1 == g1b and len(s.list_generations("archives:demo")) == 1, g1[:12])
    check("read returns the exact bytes", s.read("archives:demo", g1) == data)
    check("read_range returns a byte slice", s.read_range("archives:demo", g1, 4, 5) == b"quick",
          s.read_range("archives:demo", g1, 4, 5))

    # ── CAS race: two publishers, one pointer, exactly one wins ──
    g2 = s.put_immutable("archives:demo", b"generation two")
    r1 = s.cas_pointer("archives:demo", None, g1)     # first publish: expect no pointer
    r2 = s.cas_pointer("archives:demo", None, g2)     # racer with the SAME (stale) expectation
    check("CAS: exactly one of two racers on the same expectation wins", (r1 != r2) and (r1 or r2),
          f"r1={r1} r2={r2}")
    winner = g1 if r1 else g2
    loser = g2 if r1 else g1
    check("CAS: the pointer resolves to the winner", s.resolve_generation("archives:demo")["generation"] == winner)
    check("CAS: the loser's generation is still listed (GC-able, not lost)",
          loser in s.list_generations("archives:demo"))
    # a correct CAS with the current expectation succeeds and bumps the version
    v0 = s.resolve_generation("archives:demo")["version"]
    check("CAS: swapping with the current expectation succeeds + bumps version",
          s.cas_pointer("archives:demo", winner, loser) is True
          and s.resolve_generation("archives:demo")["version"] == v0 + 1)

    # ── lease fencing ──
    l1 = s.acquire_lease("writerA", ttl_s=0.5)
    check("acquire_lease grants a token + epoch", bool(l1 and l1.get("token")) and l1.get("epoch") >= 1)
    check("a second holder cannot acquire a LIVE lease", s.acquire_lease("writerB", ttl_s=0.5) is None)
    time.sleep(0.6)                                   # let writerA's lease expire
    check("the expired holder cannot renew (fenced out)", s.renew(l1["token"], ttl_s=0.5) is False)
    l2 = s.acquire_lease("writerB", ttl_s=0.5)
    check("a new holder steals the EXPIRED lease with a HIGHER epoch (the fence)",
          bool(l2) and l2["epoch"] > l1["epoch"], f"{l1.get('epoch')}→{l2.get('epoch') if l2 else None}")

    # ── capability refusal: the S3 archives mirror ──
    s3 = S3DurableStore(bucket="demo")
    ok_a, miss_a = check_backend(s3.capabilities(), ARCHIVES_REQUIRED)
    ok_sw, miss_sw = check_backend(s3.capabilities(), WRITER_REQUIRED)
    check("the S3 backend is ADMITTED as an archives mirror", ok_a and not miss_a, repr(s3.capabilities()))
    check("the S3 backend is REFUSED as a writer (missing cas + leases)",
          (not ok_sw) and "supports_cas" in miss_sw and "supports_leases" in miss_sw, str(miss_sw))

    # ── SemanticArtifactStore round-trip ──
    art = SemanticArtifactStore(s)
    art.put("leaderboard", "artifact_abc", b"rows...")
    check("SemanticArtifactStore.put→get round-trips by artifact_id",
          art.get("leaderboard", "artifact_abc") == b"rows...")

    # ── B4 §A5 — as-of equals the recorded history AFTER A RESTART (durable, not a cache) ──
    import hashlib as _hl
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts.cronon import CrononConcept
    KernelDispatcher._boot_load_ontology = lambda self: None
    kbase = tempfile.mkdtemp(prefix="akasha_asof_dur_")
    k1 = KernelDispatcher(series="seeds", base_dir=kbase)
    k1.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": _hl.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    _cc = CrononConcept(k1.manager.get_session("admin"))
    for _i, _ep in enumerate((10, 20, 30), start=1):
        _cc._add_to_set("set:demo:asof", _cc._mk("dur:m%d" % _i, "row %d" % _i,
                        {"concept": "demo_row", "at_seq": _ep, "n": _i}))
    k2 = KernelDispatcher(series="seeds", base_dir=kbase)      # restart on the same durable store
    _r = (k2.dispatch({"jsonrpc": "2.0", "method": "set.ls",
                       "params": {"session_token": "admin", "data": {"name": "set:demo:asof", "as_of": "20"}},
                       "id": "t"}, "local").get("result") or {})
    check("B4 as-of equals the recorded history after a restart (as_of=20 → 2 members)",
          _r.get("count") == 2 and _r.get("as_of") == 20, str(_r.get("count")))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the local DurableSemanticStore proves the writer capability set (immutable "
          "generations, range read, CAS with exactly-one-winner races, fenced leases); the S3 archives "
          "mirror is admitted for archives and refused as a writer by capability negotiation; the "
          "SemanticArtifactStore round-trips an artifact by id.")
    sys.exit(0)


if __name__ == "__main__":
    main()
