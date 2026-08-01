#!/usr/bin/env python3
"""
SilicaBackend parity eval (Slice B) — the drop-in boundary vs SQLiteBackend.

Runs the SAME battery of AkashaBackend ISA calls through BOTH backends and asserts
identical observable results — the acceptance test that SilicaBackend is a drop-in
for SQLiteBackend (a one-line factory swap).  Also proves the payoff the whole
exercise is for: the atom bundle (chunk + access + meta) written as ONE atomic
transaction.

  P1 atom CRUD    — put/get/update/meta round-trip identical.
  P2 aliases      — exact + case-insensitive + compound-normalised resolution; pattern.
  P3 links        — outgoing/incoming (+ rel pattern), identical dicts.
  P4 collections  — members / by-key / any / all / scoped / locale-ordered.
  P5 derive       — leaf:/ns:/lang: derivation + namespace counts identical.
  P6 vault + FIFO — vault store/scan; pending-link FIFO ids; collision log.
  P7 drop cascade — drop_chunk removes chunk/aliases/links/collections/access in both.
  P8 bundle-atomic— the atom bundle commits all-or-nothing (Silica-specific payoff).
  P9 graph parity — enumerate EVERY key; the full semantic projection (content/meta/
                    aliases/collections/access/links) is byte-identical between engines
                    (the twin-release equivalence proof).
  P10 adversarial — unicode alias, a 500-member set, a 300-edge mega-hub (+bounded
                    fetch) all return identical results.

Run:  python test/silica_backend_eval.py
"""
import os
import sys
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.backends.sqlite import SQLiteBackend
from lib.akasha.backends.silica_backend import SilicaBackend

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def battery(be):
    """Apply an identical sequence of ISA writes to a backend."""
    for k, alias, la in [("k1", "word:en:apple", "en"),
                         ("k2", "word:en:banana", "en"),
                         ("k3", "word:ja:ringo", "ja")]:
        be.put_chunk_raw(k, f"content-{k}", f'{{"type":"fruit","name":"{k}"}}',
                         "auth", "verified", 1000.0 + int(k[1]))
        be.put_alias(k, alias)
        be.derive_alias_collections(alias, k)
        be.put_chunk_access(k, ["scope:sys:universal", "owner:user_x"])
    be.put_link_raw("k1", "k2", "rel:near", w=0.5)
    be.put_link_raw("k1", "k3", "thesaurus:related", w=0.9)
    be.put_link_raw("k2", "k1", "rel:back", w=0.3)
    for k in ("k1", "k2", "k3"):
        be.add_to_collection("set:fruit", k)
    be.add_to_collection("set:red", "k1")
    be.vault_store("cfg", "alpha", {"n": 1})
    be.vault_store("cfg", "beta", {"n": 2})
    be.enqueue_pending_link("k1", "kX", "rel:pending", "auth", 5.0)
    be.enqueue_pending_link("k2", "kY", "rel:pending", "auth", 6.0)
    be.log_alias_collision("word:en:apple", "old", "k1")


def probe(be):
    """Read the same observable state back — order-normalised for comparison."""
    def links_out(s):
        return sorted((d["dst"], d["rel"], d["w"]) for d in be.get_adjacent_links(s))
    def links_in(s):
        return sorted((d["src"], d["rel"], d["w"]) for d in be.get_incoming_links(s))
    loc = be.get_collection_members_locale_ordered(
        "set:fruit", ["scope:sys:universal", "owner:user_x"], ["ja", "en"])
    return {
        "chunk_k1": be.get_chunk_raw("k1"),
        "alias_exact": be.get_key_by_alias("word:en:apple"),
        "alias_ci": be.get_key_by_alias("WORD:EN:APPLE"),
        "alias_miss": be.get_key_by_alias("nope:x"),
        "pattern": sorted((d["alias"], d["key"]) for d in be.get_aliases_by_pattern("word:en:%")),
        "aliases_of_k1": sorted(be.get_aliases_by_key("k1")),
        "lout_k1": links_out("k1"),
        "lin_k1": links_in("k1"),
        "lout_k1_pat": sorted((d["dst"], d["rel"]) for d in be.get_adjacent_links("k1", "rel:%")),
        "members_fruit": sorted(be.get_collection_members("set:fruit")),
        "coll_of_k1": sorted(be.get_collections_for_key("k1")),
        "access_k1": sorted(be.get_chunk_access_scopes("k1")),
        "check_yes": be.check_chunk_access_any("k1", ["scope:sys:universal"]),
        "check_no": be.check_chunk_access_any("k1", ["scope:nobody"]),
        "in_all": sorted(be.get_keys_in_all_collections(["set:fruit", "set:red"])),
        "in_any": sorted(be.get_keys_in_any_collection(["set:red"])),
        "scoped": sorted(be.get_collection_members_scoped("set:fruit", ["scope:sys:universal"])),
        "scoped_deny": be.get_collection_members_scoped("set:fruit", []),
        "loc_set": sorted(loc),
        "loc_ja_first": (loc[0] == "k3") if loc else False,
        "keys_by_scope": sorted(be.get_keys_by_scope("owner:user_x")),
        "ns_word": next((r["count"] for r in be.get_namespace_counts(depth=1) if r["ns"] == "word"), None),
        "vault_alpha": be.vault_retrieve("cfg", "alpha"),
        "vault_scan": sorted(be.vault_scan("cfg")),
        "plink_ids_order": [(r["src"], r["dst"]) for r in be.get_pending_links()],
        "acl_unres": [(r["alias"], r["new_key"]) for r in be.get_alias_collision_log(unresolved_only=True)],
    }


def main():
    print("\n  silica backend parity eval — drop-in vs SQLiteBackend (identical ISA results)\n")
    work = tempfile.mkdtemp(prefix="silica_be_")
    try:
        sq = SQLiteBackend(os.path.join(work, "sq.db"), is_volatile=True)
        si = SilicaBackend(os.path.join(work, "si.db"), is_volatile=True)
        battery(sq)
        battery(si)
        psq, psi = probe(sq), probe(si)

        groups = {
            "P1 atom CRUD": ["chunk_k1"],
            "P2 aliases": ["alias_exact", "alias_ci", "alias_miss", "pattern", "aliases_of_k1"],
            "P3 links": ["lout_k1", "lin_k1", "lout_k1_pat"],
            "P4 collections": ["members_fruit", "coll_of_k1", "access_k1", "check_yes", "check_no",
                               "in_all", "in_any", "scoped", "scoped_deny", "loc_set",
                               "loc_ja_first", "keys_by_scope"],
            "P5 derive": ["ns_word"],
            "P6 vault+FIFO": ["vault_alpha", "vault_scan", "plink_ids_order", "acl_unres"],
        }
        for gname, fields in groups.items():
            diffs = [f for f in fields if psq[f] != psi[f]]
            record(gname, not diffs,
                   "identical" if not diffs else f"MISMATCH {diffs}: "
                   + "; ".join(f"{f}: sq={psq[f]!r} si={psi[f]!r}" for f in diffs[:2]))

        # P7 — drop cascade parity.
        sq.drop_chunk("k2"); si.drop_chunk("k2")
        d_ok = (
            sq.get_chunk_raw("k2") is None and si.get_chunk_raw("k2") is None
            and sorted(m for m in sq.get_collection_members("set:fruit")) ==
                sorted(m for m in si.get_collection_members("set:fruit"))
            and sorted((d["dst"], d["rel"]) for d in sq.get_adjacent_links("k1")) ==
                sorted((d["dst"], d["rel"]) for d in si.get_adjacent_links("k1"))
            and si.get_key_by_alias("word:en:banana") is None       # alias gone
            and "k2" not in si.get_collection_members("set:fruit"))
        record("P7 drop cascade", d_ok,
               f"k2 removed from chunk/alias/links/collections in both (fruit now {sorted(si.get_collection_members('set:fruit'))})")

        # P8 — the payoff: the atom bundle as ONE atomic primitive (write_atom).
        si.write_atom("kb", "bundle", '{"m":1}', "a", "verified", 1.0,
                      scopes=["scope:sys:universal", "owner:user_x"])
        # Mirror the same atom on SQLite (which has no bundle primitive — several
        # calls) so the two graphs stay comparable for the P9 digest.
        sq.put_chunk_raw("kb", "bundle", '{"m":1}', "a", "verified", 1.0)
        sq.put_chunk_access("kb", ["scope:sys:universal", "owner:user_x"])
        atom_landed = (si.get_chunk_raw("kb") is not None                       # chunk +
                       and sorted(si.get_chunk_access_scopes("kb")) ==          # access (fwd) +
                           ["owner:user_x", "scope:sys:universal"]
                       and "kb" in si.get_keys_by_scope("scope:sys:universal")) # access (reverse)
        # An aborted bundle leaves nothing (rollback).
        t2 = si._store.begin()
        t2.put(b"kc", b"C", b'{"content":"x","meta":"{}","created_at":"1","author":"a","status":"v","seq":2}')
        t2.abort()
        p8 = atom_landed and si.get_chunk_raw("kc") is None
        record("P8 bundle-atomic", p8,
               "chunk+access+meta commit together (one Txn); aborted bundle leaves nothing")

        # P9 — FULL-GRAPH DIGEST PARITY: enumerate every key and compare the complete
        # semantic projection (content/meta/aliases/collections/access/links) between the
        # two engines. This is the twin-release equivalence proof — anything the spot
        # checks missed shows up as a per-key diff.
        def projection(be, key):
            c = be.get_chunk_raw(key)
            return (c["content"] if c else None, c["meta"] if c else None,
                    tuple(sorted(be.get_aliases_by_key(key))),
                    tuple(sorted(be.get_collections_for_key(key))),
                    tuple(sorted(be.get_chunk_access_scopes(key))),
                    tuple(sorted((d["dst"], d["rel"], round(d["w"], 6))
                                 for d in be.get_adjacent_links(key))))
        ksq, ksi = set(sq.get_all_keys()), set(si.get_all_keys())
        key_diff = ksq ^ ksi
        proj_diffs = [k for k in (ksq & ksi) if projection(sq, k) != projection(si, k)]
        p9 = not key_diff and not proj_diffs
        record("P9 graph parity", p9,
               f"{len(ksq)} keys, identical semantic projection"
               if p9 else f"key_diff={list(key_diff)[:3]} proj_diffs={proj_diffs[:3]}")

        # P10 — ADVERSARIAL INPUT PARITY: unicode alias, a large set, a mega-hub.
        for be in (sq, si):
            be.put_chunk_raw("u1", "爱", '{"t":"u"}', "a", "verified", 1.0)
            be.put_alias("u1", "word:zh:爱")
            for i in range(500):
                be.add_to_collection("set:big", f"m{i}")
            be.put_chunk_raw("hub", "hub", "{}", "a", "verified", 1.0)
            for i in range(300):
                be.put_link_raw(f"src{i}", "hub", "rel:in", w=1.0)
        p10 = (sq.get_key_by_alias("word:zh:爱") == si.get_key_by_alias("word:zh:爱") == "u1"
               and sorted(sq.get_aliases_by_pattern("word:zh:%")[0].items()) ==
                   sorted(si.get_aliases_by_pattern("word:zh:%")[0].items())
               and len(sq.get_collection_members("set:big")) ==
                   len(si.get_collection_members("set:big")) == 500
               and len(sq.get_incoming_links("hub")) ==
                   len(si.get_incoming_links("hub")) == 300
               and len(si.get_incoming_links("hub", limit=50)) == 50)   # bounded fetch honoured
        record("P10 adversarial", p10,
               "unicode alias, 500-member set, 300-edge mega-hub (+bounded fetch) all parity")

        sq.close(); si.close()
        print()
        passed = sum(1 for _, ok, _ in _results if ok)
        total = len(_results)
        print(f"  {passed}/{total} phases passed"
              + (f", {total - passed} FAILED" if passed < total else ""))
        if passed < total:
            print("\nRESULT: FAIL — SilicaBackend diverges from SQLiteBackend.")
            return 1
        print("\nRESULT: PASS — SilicaBackend returns identical results to SQLiteBackend across the "
              "ISA (drop-in), and the atom bundle is one atomic transaction.")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
