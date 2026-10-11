#!/usr/bin/env python3
"""
F33 §5.1 — access-degree instrumentation: the permanent guard for the paid-for invariant.

Akasha pays its cost UP FRONT: every needed concept group is enclosed in sets at write time. So as
long as the set-algebra structure (collection membership, scope indexes, @ALIAS) is memory-resident
— which it now is, ALWAYS (F33: the index is RAM, one implementation) — any atom is reachable in
effectively ONE level: one membership lookup (RAM membrane walk) + one point-get (disk is fine for
the per-atom body). The pathology this guards against is a SCAN below a membrane: the cached-index
experiment put the membranes on disk and every nested render became scan × depth × fan-out under
held bank locks — a lock convoy that went to 5-min-plus. The access DEGREE, not raw speed, broke.

This eval instruments the store's reads — point_get (one member resolved), membrane_scan (one
route's keys walked), full_scan (the whole keyspace) — and asserts a set-mediated access satisfies
round-trips ≤ (atoms reached + sets touched) with ZERO full_scans. A regression that reintroduces a
below-membrane scan fails HERE, at eval time, never as a slow page in production.

Run:  python test/access_degree_eval.py   (exit 0 = all pass)
"""
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def run(value_store):
    os.environ["AKASHA_SILICA_VALUES"] = value_store
    from lib.akasha.backends.silica_backend import SilicaBackend
    b = SilicaBackend(os.path.join(tempfile.mkdtemp(prefix="accdeg_"), "s"), banks=4, sync_mode="NORMAL")

    # ── build two collections; the second shares no members with the first ──
    a_members = []
    for i in range(20):
        k = "a:atom%d" % i
        b.put_chunk_raw(k, "body a %d" % i + "x" * 80, "{}", "admin", "verified", time.time())
        b.add_to_collection("set:a", k)
        a_members.append(k)
    for i in range(12):
        k = "b:atom%d" % i
        b.put_chunk_raw(k, "body b %d" % i + "y" * 80, "{}", "admin", "verified", time.time())
        b.add_to_collection("set:b", k)

    # ── (1) single set-mediated access: one membrane + one point-get per member, zero full scans ──
    b.probe_reset()
    members = b.get_collection_members("set:a")
    for m in members:
        b.get_chunk_raw(m)
    p = b.probe_read()
    n, sets = len(members), 1
    rt = p["point_get"] + p["membrane_scan"]
    check("[%s] one set-mediated access: ZERO full scans" % value_store, p["full_scan"] == 0, str(p))
    check("[%s] round-trips ≤ atoms reached + sets touched" % value_store, rt <= n + sets,
          f"round-trips={rt} ≤ {n}+{sets}={n+sets}")
    check("[%s] exactly one point-get per member reached" % value_store, p["point_get"] == n,
          f"point_get={p['point_get']} members={n}")
    check("[%s] exactly one membrane walk per set touched" % value_store, p["membrane_scan"] == sets,
          f"membrane_scan={p['membrane_scan']} sets={sets}")

    # ── (2) a NESTED render (two membranes deep): still bounded, still zero full scans ──
    b.probe_reset()
    reached = 0
    for setname in ("set:a", "set:b"):
        for m in b.get_collection_members(setname):
            b.get_chunk_raw(m)
            reached += 1
    p2 = b.probe_read()
    rt2 = p2["point_get"] + p2["membrane_scan"]
    check("[%s] nested render: ZERO full scans below the membranes" % value_store, p2["full_scan"] == 0, str(p2))
    check("[%s] nested round-trips ≤ atoms reached + sets touched" % value_store, rt2 <= reached + 2,
          f"round-trips={rt2} ≤ {reached}+2")

    # ── (3) the detector is armed: a genuine whole-keyspace scan DOES register as a full_scan ──
    b.probe_reset()
    _ = list(b._store.scan_all())
    p3 = b.probe_read()
    check("[%s] the guard is armed — a whole-keyspace scan_all is counted as a full_scan" % value_store,
          p3["full_scan"] >= 1, str(p3))


def main():
    # Both value residencies: RAM (fast) and disk (memory-frugal). The invariant holds in BOTH —
    # the index (membranes) is RAM either way; only per-atom bodies differ.
    run("ram")
    for mod in list(sys.modules):
        if mod.startswith("lib.akasha.backends"):
            pass  # keep modules; env re-read happens in SilicaStore.__init__ per instance
    run("disk")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — the paid-for invariant is instrumented and holds: a set-mediated access is one "
          "membrane walk (RAM) + one point-get per member, ZERO scans below a membrane, in both value "
          "modes. The lock-convoy pathology cannot return unnoticed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
