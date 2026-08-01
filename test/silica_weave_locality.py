#!/usr/bin/env python3
"""
Silica cache — WEAVE WORKING-SET measurement (Step 2 groundwork, measurement-first).

Before adding any working-set *pin* to the disk-value cache, we must first identify the weave
working set empirically and measure whether Step 1's SLRU already captures its locality. Per the
design rule: *identify the target semantic space with a measurement algorithm, THEN decide whether
a priority mechanism is warranted — never an arbitrary pin.*

The weave working set = the proto-word / hub atoms shared across a batch's words. The real access
pattern (grounded in composite._ensure_protoword → backend.get_key_by_alias, and set_alias →
put_link_raw) is:

    for each word in a batch:
        for each bare component (Zipf-popular hubs recur):
            key = get_key_by_alias(bare)          # SHARED read  → store.get(_R_ALIAS, bare)
            if key is None:                        # first sighting of this hub
                put_chunk_raw(hub); put_alias(hub) # WRITE → invalidates (_R_ALIAS, bare)
            put_link_raw(word, hub, "specializes")
        put_chunk_raw(word); put_alias(word)

Two regimes are measured separately because they stress the cache differently:

  W1  WARM weave  — hubs already exist (large ontology already loaded): every hub lookup is a pure
                    read. Tests whether SLRU protects the recurrent hub reads (the steady state on
                    a running cell — the common case).
  W2  COLD weave  — hubs are minted during the batch (fresh corpus): each new hub is written then
                    re-read, so the write invalidates its cache entry and it re-enters probationary.
                    Tests the write-then-read penalty on the working set.

For each regime we report the cache hit-rate overall AND on the hub-alias reads alone (the working
set), plus evictions, so Step 2 is decided on data, not intuition.

Run:  python test/silica_weave_locality.py     (informational; exit 0 always unless it errors)
"""
import os
import sys
import gc
import hashlib
import tempfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ.setdefault("AKASHA_SILICA_VALUES", "disk")   # this whole study is the disk-value path

from lib.akasha.backends.silica_backend import SilicaBackend


# ── deterministic pseudo-random (no Math.random equivalent needed; reproducible) ──
class _LCG:
    """A tiny deterministic PRNG so the study is reproducible run-to-run."""
    def __init__(self, seed=0x9E3779B1):
        self._s = seed & 0xFFFFFFFF

    def _next(self):
        self._s = (1103515245 * self._s + 12345) & 0x7FFFFFFF
        return self._s

    def rand(self):
        return self._next() / 0x7FFFFFFF

    def zipf_index(self, n, s=1.2):
        """Return an index in [0,n) skewed toward 0 (popular hubs recur). Cheap rank-power draw."""
        # inverse-transform on a truncated power law over ranks
        u = self.rand()
        # rank r ∝ r^-s ; approximate the CDF inversion with a power curve
        return min(n - 1, int(n * (u ** (s + 1.0))))


def _kd(*parts):
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _reset_cache_counters(store):
    c = store._cache
    c.hits = c.misses = c.evictions = c.inserts = 0


def build_backend(base):
    return SilicaBackend(os.path.join(base, "nuc"), sync_mode="NORMAL")


META = '{"type":"note"}'


def mint_hub(be, bare):
    """First sighting of a proto-word hub: write chunk + alias (the write-invalidation source)."""
    k = _kd("word", bare)
    be.put_chunk_raw(k, f"proto:{bare}", META, "weaver", "active", 1.0)
    be.put_alias(k, bare)
    return k


def run_weave(be, hubs, n_words, comps_per_word, rng, pre_minted):
    """Drive the weave access pattern. Returns per-class read counters resolved from the store cache
    deltas around the hub-alias reads so we can separate working-set hits from the rest."""
    store = be._store
    cache = store._cache
    minted = set(pre_minted)
    hub_hits0 = cache.hits
    hub_miss0 = cache.misses
    # We want the hub-alias-read hit-rate in isolation. Snapshot around ONLY the get_key_by_alias
    # calls by diffing the counters immediately before/after each such call.
    hub_hits = hub_miss = 0
    n = len(hubs)
    for wi in range(n_words):
        word_alias = f"w{wi:06d}"
        word_key = _kd("word", word_alias)
        # decompose into Zipf-popular components (popular hubs recur across words = the locality)
        picks = {hubs[rng.zipf_index(n)] for _ in range(comps_per_word)}
        for bare in picks:
            h0, m0 = cache.hits, cache.misses
            key = be.get_key_by_alias(bare)        # SHARED working-set read
            hub_hits += cache.hits - h0
            hub_miss += cache.misses - m0
            if key is None:
                key = mint_hub(be, bare)           # write → invalidates (_R_ALIAS, bare)
                minted.add(bare)
            be.put_link_raw(word_key, key, "specializes")
        be.put_chunk_raw(word_key, f"word body {word_alias}", META, "weaver", "active", 2.0 + wi)
        be.put_alias(word_key, word_alias)
    total_hits = cache.hits - hub_hits0
    total_miss = cache.misses - hub_miss0
    return {
        "hub_reads": hub_hits + hub_miss,
        "hub_hit_rate": (hub_hits / (hub_hits + hub_miss)) if (hub_hits + hub_miss) else 0.0,
        "overall_hits": total_hits, "overall_miss": total_miss,
        "overall_hit_rate": (total_hits / (total_hits + total_miss)) if (total_hits + total_miss) else 0.0,
    }


def regime_warm(n_hubs, n_words, comps, cache_mb):
    os.environ["AKASHA_SILICA_CACHE_MB"] = str(cache_mb)
    base = tempfile.mkdtemp(prefix="weave_warm_")
    rng = _LCG(0xA11CE)
    be = build_backend(base)
    hubs = [f"bare{h:05d}" for h in range(n_hubs)]
    for bare in hubs:                              # pre-load the ontology (hubs already exist)
        mint_hub(be, bare)
    _reset_cache_counters(be._store)               # measure only the weave, not the preload
    res = run_weave(be, hubs, n_words, comps, rng, pre_minted=hubs)
    st = be._store.stats()["cache"]
    be.close(); shutil.rmtree(base, ignore_errors=True); gc.collect()
    return res, st


def regime_cold(n_hubs, n_words, comps, cache_mb):
    os.environ["AKASHA_SILICA_CACHE_MB"] = str(cache_mb)
    base = tempfile.mkdtemp(prefix="weave_cold_")
    rng = _LCG(0xC01D)
    be = build_backend(base)
    hubs = [f"bare{h:05d}" for h in range(n_hubs)]  # NOT pre-minted → minted during the weave
    _reset_cache_counters(be._store)
    res = run_weave(be, hubs, n_words, comps, rng, pre_minted=set())
    st = be._store.stats()["cache"]
    be.close(); shutil.rmtree(base, ignore_errors=True); gc.collect()
    return res, st


def _report(title, res, st):
    print(f"\n  {title}")
    print(f"    hub-alias reads (working set) : {res['hub_reads']:>8}   "
          f"hit-rate {100*res['hub_hit_rate']:5.1f}%")
    print(f"    overall cache reads           : {res['overall_hits']+res['overall_miss']:>8}   "
          f"hit-rate {100*res['overall_hit_rate']:5.1f}%")
    print(f"    cache: entries={st['entries']} protected={st['protected']} "
          f"prob={st['probationary']} evictions={st['evictions']} "
          f"bytes={st['bytes']/1e6:.2f}MB / budget={st['budget']/1e6:.1f}MB")


def main():
    N_HUBS, N_WORDS, COMPS = 3000, 8000, 6
    print(f"Silica weave-locality study  (hubs={N_HUBS}, words={N_WORDS}, comps/word={COMPS}, "
          f"Zipf-shared)\n  value_store=disk")

    # Big cache: working set fits — establishes the ceiling.
    wr, ws = regime_warm(N_HUBS, N_WORDS, COMPS, cache_mb=64)
    _report("W1 WARM weave, 64 MB cache (working set fits)", wr, ws)
    cr, cs = regime_cold(N_HUBS, N_WORDS, COMPS, cache_mb=64)
    _report("W2 COLD weave, 64 MB cache (hubs minted during batch)", cr, cs)

    # Tight cache: does the hub working set survive eviction pressure, or does Step 1's scan-
    # resistance already keep it protected? This is the measurement that decides Step 2.
    wr2, ws2 = regime_warm(N_HUBS, N_WORDS, COMPS, cache_mb=1)
    _report("W1 WARM weave, 1 MB cache (eviction pressure)", wr2, ws2)

    print("\n  Interpretation guide:")
    print("   • If WARM hub hit-rate stays high under the tight cache → SLRU already captures the")
    print("     weave working set; a Step-2 pin adds little (do NOT add an unmeasured pin).")
    print("   • If COLD hub hit-rate is much lower than WARM → the write-then-read invalidation is")
    print("     the real gap; the right Step-2 lever is a write-warm (populate cache on commit),")
    print("     NOT a semantic-priority pin.")
    print("   • Evictions climbing on WARM/tight while hit-rate falls → the working set exceeds the")
    print("     protected budget; only THEN is a size-targeted pin justified.")
    sys.exit(0)


if __name__ == "__main__":
    main()
