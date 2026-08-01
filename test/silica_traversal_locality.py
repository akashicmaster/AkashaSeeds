#!/usr/bin/env python3
"""
Silica cache — TRAVERSAL locality measurement (Step 3 groundwork, measurement-first).

Step 3 as planned = "semantic prefetch on traversal": when the composite layer walks the graph
(explore / generate_view) it KNOWS the neighbours it is about to read, so it could prefetch their
values by MEANING (adjacent links / set co-members) instead of paying a per-neighbour cache miss.
Before building any prefetch we must measure — same rule as Step 2: identify the target semantic
space and prove a gap the Step-1 SLRU does not already close, else DO NOT build it.

This harness replays generate_view's real read pattern (consciousness.py) against a single disk
store, so the cache counters isolate traversal locality with no boot-ontology noise:

    dive(focus):
        get_chunk_raw(focus)                        # focal value
        sps = get_adjacent_links(focus)[:15]        # 1-hop signposts (link rows on focus route)
        for dst in sps:      get_chunk_raw(dst)      # 1-hop neighbour VALUE  ← read
        for dst in sps:                              # resonance = 2-hop
            for hk in get_adjacent_links(dst)[:15]:  # a sibling's neighbours…
                get_chunk_raw(hk)                    # 2-hop neighbour VALUE  ← read (RE-reads hub/siblings)

Graph: one hub + S spokes; every spoke links back to the hub and to a few siblings, so the 2-hop
resonance pass RE-reads the hub and sibling values already touched at 1-hop — the locality a
prefetch would target. We separate two questions a prefetch cannot conflate:

  • RE-READ ratio — reads whose value was already read earlier in the session. SLRU already turns
    these into HITS after first touch; a prefetch adds nothing to their hit-rate.
  • FIRST-TOUCH misses — the unavoidable floor: each distinct value must be pread once. A prefetch
    only changes WHEN that pread happens (batched vs inline), never whether it is a miss.

If re-reads dominate and already hit, and disk read latency already ≈ SQLite, a prefetch buys
only pread batching on a floor that is already cheap → not justified. The numbers decide.

Run:  python test/silica_traversal_locality.py     (informational; exit 0 unless it errors)
"""
import os
import sys
import gc
import tempfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ.setdefault("AKASHA_SILICA_VALUES", "disk")

from lib.akasha.backends.silica_backend import SilicaBackend

META = '{"type":"note"}'


def build_backend(base):
    return SilicaBackend(os.path.join(base, "nuc"), sync_mode="NORMAL")


def build_graph(be, spokes, sibling_fanout):
    """Hub + spokes; each spoke → hub and → a few siblings (2-hop revisits hub/siblings)."""
    hub = "hub"
    be.put_chunk_raw(hub, "hub content " + "h" * 60, META, "a", "active", 1.0)
    be.put_alias(hub, "hub")
    keys = [f"spoke{i:04d}" for i in range(spokes)]
    for i, k in enumerate(keys):
        be.put_chunk_raw(k, f"spoke {i} " + "s" * 60, META, "a", "active", 2.0 + i)
        be.put_alias(k, k)
        be.put_link_raw(hub, k, "thesaurus:related")
        be.put_link_raw(k, hub, "thesaurus:related")
    for i, k in enumerate(keys):                       # cross-link siblings
        for j in range(1, sibling_fanout + 1):
            sib = keys[(i + j) % spokes]
            be.put_link_raw(k, sib, "thesaurus:related")
    return hub, keys


class _Counter:
    """Session-level first-touch vs re-read tally, independent of the cache, so we can attribute
    the cache's hit-rate to genuine re-reads (prefetch-irrelevant) vs first touches."""
    def __init__(self):
        self.seen = set()
        self.reads = 0
        self.first_touch = 0
        self.re_read = 0

    def note(self, key):
        self.reads += 1
        if key in self.seen:
            self.re_read += 1
        else:
            self.first_touch += 1
            self.seen.add(key)


def dive(be, focus, ctr):
    """Faithful generate_view read pattern (focus → 1-hop signposts → 2-hop resonance)."""
    be.get_chunk_raw(focus); ctr.note(focus)
    sps = [l["dst"] for l in be.get_adjacent_links(focus)][:15]
    for dst in sps:
        be.get_chunk_raw(dst); ctr.note(dst)
    for dst in sps:                                    # resonance: 2-hop
        hops = [l["dst"] for l in be.get_adjacent_links(dst)][:15]
        for hk in hops:
            be.get_chunk_raw(hk); ctr.note(hk)


def _reset_cache(be):
    c = be._store._cache
    c.hits = c.misses = c.evictions = c.inserts = 0


def run(spokes, sibling_fanout, rounds, cache_mb, label):
    os.environ["AKASHA_SILICA_CACHE_MB"] = str(cache_mb)
    base = tempfile.mkdtemp(prefix="trav_")
    be = build_backend(base)
    hub, keys = build_graph(be, spokes, sibling_fanout)

    # ── cold single dive on the hub (fresh cache) — the first-touch floor ──
    _reset_cache(be)
    ctr_cold = _Counter()
    dive(be, hub, ctr_cold)
    cold = be._store.stats()["cache"]
    cold_hits, cold_miss = cold["hits"], cold["misses"]

    # ── warm session: repeated dives over hub + every spoke, several rounds ──
    _reset_cache(be)
    ctr = _Counter()
    for _r in range(rounds):
        dive(be, hub, ctr)
        for k in keys:
            dive(be, k, ctr)
    st = be._store.stats()["cache"]
    be.close(); shutil.rmtree(base, ignore_errors=True); gc.collect()

    print(f"\n  {label}  (spokes={spokes}, sibling_fanout={sibling_fanout}, rounds={rounds}, "
          f"cache={cache_mb}MB)")
    print(f"    COLD single hub dive : reads={ctr_cold.reads:>6}  "
          f"first-touch={ctr_cold.first_touch}  re-read={ctr_cold.re_read}  "
          f"cache hit-rate={100*cold_hits/max(1,cold_hits+cold_miss):4.1f}%")
    print(f"       → even within ONE cold dive, {100*ctr_cold.re_read/max(1,ctr_cold.reads):.0f}% "
          f"of reads are re-reads (2-hop revisiting 1-hop) — SLRU already serves these.")
    print(f"    WARM session         : reads={ctr.reads:>6}  "
          f"first-touch={ctr.first_touch}  re-read={ctr.re_read}  "
          f"({100*ctr.re_read/max(1,ctr.reads):.0f}% re-read)")
    print(f"       cache hit-rate={100*st['hits']/max(1,st['hits']+st['misses']):4.1f}%  "
          f"evictions={st['evictions']}  bytes={st['bytes']/1e6:.2f}MB")
    # The prefetch ceiling: a perfect meaning-prefetch could at best convert the session's
    # FIRST-TOUCH reads into pre-warmed hits. It cannot beat the first-touch floor on hit-rate;
    # it only batches those preads. Report that floor explicitly.
    floor = 100 * ctr.first_touch / max(1, ctr.reads)
    print(f"       first-touch floor = {floor:.1f}% of reads (the ONLY reads a prefetch could "
          f"pre-warm; the rest already hit). Prefetch changes pread batching, not hit-rate.")


def main():
    print("Silica traversal-locality study  (generate_view read pattern; value_store=disk)")
    run(300, 4, 3, 64, "T1 dense hub-spoke, roomy cache")
    run(300, 4, 3, 1,  "T2 dense hub-spoke, tight cache (eviction pressure)")
    run(2000, 6, 2, 64, "T3 large graph, roomy cache")

    print("\n  Interpretation:")
    print("   • High re-read % with high WARM hit-rate + low evictions → the Step-1 SLRU already")
    print("     captures traversal locality; the 2-hop resonance re-reads hit after first touch.")
    print("   • A meaning-prefetch cannot lower the first-touch floor (each value is pread once);")
    print("     it only batches those preads. With disk read p50 already ≈ SQLite, that is not a")
    print("     measured win → do NOT build the prefetch on hit-rate grounds. Revisit only if a")
    print("     workload shows a large first-touch floor AND pread latency becomes the bottleneck.")
    sys.exit(0)


if __name__ == "__main__":
    main()
