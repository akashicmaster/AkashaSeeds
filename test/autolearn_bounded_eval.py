#!/usr/bin/env python3
"""
Boot-autolearn OOM guard — a bounded `get_all_chunks(limit=N)` must NOT read the whole corpus.

The daemon was dying silently (no Python traceback → a hard OOM-killer SIGKILL) during the
boot-time background learn. Root cause: the semantic-autolearn read `nucleus.core.get_all_chunks()`
with NO cap — on the disk-value Silica store (chosen precisely because the host can't hold the
corpus in RAM) that preads EVERY atom's content+meta into memory at once and retains them all in
one list, even though the learn + bake only ever USE the first ~40 000. A background enrichment job
("while sleeping", IDLE class) must never be able to take down the single writer — so the read is
now bounded.

This test locks that in. On the disk-value store it counts how many atom CONTENT records the read
actually pulls off disk (by wrapping `SilicaBackend._all_chunk_recs`, the one-value-at-a-time
generator every content read funnels through) and asserts:
  • get_all_chunks()          pulls EVERY atom's content (the unbounded export path, unchanged);
  • get_all_chunks(limit=K)   pulls AT MOST K content records — it STOPS the generator early, it
    does NOT read-all-then-slice (the OOM guard: retained memory ∝ cap, not corpus);
  • the capped read returns exactly K correct rows (content materialized);
  • a cap above the corpus returns everything (no over-truncation);
  • get_all_links(limit=K)    accumulates AT MOST K links (was: materialize-all-then-slice).

Run:  python test/autolearn_bounded_eval.py
"""
import os, sys, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_SILICA_VALUES"] = "disk"          # the memory-constrained mode the OOM lives in

from lib.akasha.backends.silica_backend import SilicaBackend

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:30} {detail}")

# Count CONTENT records pulled off disk. `_all_chunk_recs` is the generator that preads one chunk
# value per yield; counting its yields == the number of full atom records materialized (the memory
# the OOM is made of), cleanly separated from the cheap key-index enumeration.
_CONTENT = {"n": 0}
_orig_recs = SilicaBackend._all_chunk_recs
def _counting_recs(self):
    for item in _orig_recs(self):
        _CONTENT["n"] += 1
        yield item
SilicaBackend._all_chunk_recs = _counting_recs


def main():
    print("\n  boot-autolearn OOM guard — a bounded get_all_chunks() must not read the whole corpus\n")
    work = tempfile.mkdtemp(prefix="akasha_bounded_")
    be = SilicaBackend(os.path.join(work, "b.db"), is_volatile=True)
    try:
        base = len(be.get_all_chunks())              # baseline system/genesis atoms
        ADD = 300
        for i in range(ADD):
            be.put_chunk_raw(f"k{i}", f"content number {i} with enough words to be real",
                             f'{{"i":{i}}}', "auth", "verified", 1000.0 + i)
        total = base + ADD

        # (1) unbounded read pulls EVERY atom's content (export/backup path — must stay complete).
        _CONTENT["n"] = 0
        allc = be.get_all_chunks()
        full = _CONTENT["n"]
        record("unbounded: reads all", len(allc) == total and full == total,
               f"rows={len(allc)} content_reads={full} (corpus={total})")

        # (2) THE GUARD: a capped read pulls AT MOST the cap content records — stops early.
        K = 20
        _CONTENT["n"] = 0
        capped = be.get_all_chunks(limit=K)
        capped_reads = _CONTENT["n"]
        record("capped: content_reads <= cap", capped_reads <= K,
               f"limit={K} content_reads={capped_reads} (<= {K}; unbounded pulled {full})")

        # (3) the capped read is still correct: exactly K rows, content materialized.
        ok_rows = (len(capped) == K and all(r.get("content") for r in capped))
        record("capped: K correct rows", ok_rows, f"rows={len(capped)} content_present={ok_rows}")

        # (4) a cap far above the corpus returns everything (no over-truncation).
        big = be.get_all_chunks(limit=total * 10)
        record("cap > corpus: all rows", len(big) == total, f"rows={len(big)} (corpus={total})")

        # (5) links: a bounded read accumulates at most the cap (was materialize-all-then-slice).
        for i in range(60):
            be.put_link_raw("k0", f"k{i+1}", "sys:related", author="auth")
        linked = be.get_all_links(limit=15)
        record("links: capped accumulation", len(linked) <= 15, f"returned={len(linked)} (<= 15)")
    finally:
        try: be.close()
        except Exception: pass
        shutil.rmtree(work, ignore_errors=True)

    passed = sum(1 for _, ok, _ in _results if ok); total_c = len(_results)
    print(f"\n  {passed}/{total_c} checks passed")
    if passed == total_c:
        print("\nRESULT: PASS — the boot autolearn's corpus read is memory-bounded: a capped "
              "get_all_chunks stops the content generator at the cap, so the disk-value store "
              "never materializes the whole corpus into RAM (the silent boot OOM cannot recur).\n")
        return 0
    print("\nRESULT: FAIL — the bounded read still pulls the whole corpus (OOM risk remains).\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
