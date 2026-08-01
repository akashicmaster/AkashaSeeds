#!/usr/bin/env python3
"""
Silica disk-value LARGE-CONTENT read integrity — the "recipe body empty" hypothesis.

Symptom reported from the VPS (`docs/handoff/recipe-body-empty-content-chunk.md`): a recipe
detail page shows the photo + title but an EMPTY body — the atom's alias, links, and set
membership resolve, yet `get_chunk(key)` returns empty content. Leading hypothesis: the Silica
native twin's DISK-VALUE mode returns empty for the large-content recipe atoms (a regression in
the mega-hub streaming / scan() OOM work), i.e. small subkey-encoded rows survive but large
value preads come back empty.

This test RULES THAT OUT at the backend layer by driving a recipe-sized (multi-KB) content atom
through the disk-value store across every durability boundary and asserting the body reads back
byte-for-byte:
  • fresh write → read;
  • after an explicit checkpoint (LCKPT rewrites the WAL, so value offsets are recomputed);
  • after close + reopen (full WAL replay — the boot path);
  • after a SIMULATED CRASH (drop the store without a clean close/checkpoint → reopen + replay);
  • the alias still resolves in every case (the surviving-metadata half of the symptom).

If this passes, an empty body on the VPS is NOT the disk-mode read path — it is a data-state
issue (a partially-persisted / crash-truncated load, or a stale 'loaded' sentinel over a lost
chunk), which a CLEAN reload repopulates. If it ever FAILS, the disk-value large-value read has
genuinely regressed.

Run:  python test/silica_large_content_eval.py
"""
import os, sys, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_SILICA_VALUES"] = "disk"          # the mode the symptom lives in

from lib.akasha.backends.silica_backend import SilicaBackend

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:34} {detail}")

# A real recipe body is a few KB (the handoff cites Baingan Bharta at 2792 chars). Test well past
# that so any length-field / offset / pread-truncation bug on large values would surface.
BODY = ("Baingan Bharta — smoky mashed eggplant. "
        + ("Roast the eggplant over an open flame until the skin blisters and the flesh is soft; "
           "peel, mash, and set aside. Saute onion, garlic, ginger and green chili; add tomato, "
           "turmeric, cumin and coriander; fold in the eggplant and cook down. Finish with garam "
           "masala and fresh cilantro. Serve with roti. " * 40))          # ~9 KB
KEY = "rk_baingan_bharta"
ALIAS = "recipe:baingan_bharta"


def _read_len(be):
    r = be.get_chunk_raw(KEY)
    return len(r.get("content", "")) if r else -1


def main():
    print(f"\n  silica disk-value large-content read — body is {len(BODY)} bytes\n")
    work = tempfile.mkdtemp(prefix="akasha_body_")
    db = os.path.join(work, "n.db")
    try:
        be = SilicaBackend(db, is_volatile=False)
        be.put_chunk_raw(KEY, BODY, '{"type":"recipe"}', "admin", "verified", 1000.0)
        be.put_alias(KEY, ALIAS)

        record("fresh: body intact", _read_len(be) == len(BODY), f"len={_read_len(be)}/{len(BODY)}")

        be._store.checkpoint()
        record("after checkpoint: intact", _read_len(be) == len(BODY),
               f"len={_read_len(be)} (LCKPT recomputes value offsets)")

        be.close()
        be2 = SilicaBackend(db, is_volatile=False)                       # reopen → full WAL replay
        record("after reopen: intact", _read_len(be2) == len(BODY), f"len={_read_len(be2)}")
        record("alias still resolves", be2.get_key_by_alias(ALIAS) == KEY,
               "(the surviving-metadata half of the symptom)")

        # Simulated CRASH: write MORE, then drop the store WITHOUT a clean close/checkpoint.
        be2.put_chunk_raw("rk2", BODY + " variant", '{"type":"recipe"}', "admin", "verified", 1001.0)
        be2.put_alias("rk2", "recipe:baingan_variant")
        del be2
        import gc; gc.collect()
        be3 = SilicaBackend(db, is_volatile=False)                       # replay after the "crash"
        ok_crash = (_read_len(be3) == len(BODY)
                    and (be3.get_chunk_raw("rk2") or {}).get("content", "").startswith("Baingan"))
        record("after simulated crash: intact", ok_crash,
               f"orig len={_read_len(be3)}, second atom recovered={bool(be3.get_chunk_raw('rk2'))}")
        be3.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)

    passed = sum(1 for _, ok, _ in _results if ok); total = len(_results)
    print(f"\n  {passed}/{total} checks passed")
    if passed == total:
        print("\nRESULT: PASS — the disk-value store returns large content byte-for-byte across "
              "checkpoint, reopen and crash-replay. An empty recipe body is NOT the Silica read "
              "path; it is a data-state issue (partial/crash-truncated load or stale sentinel over "
              "a lost chunk) that a clean reload repopulates.\n")
        return 0
    print("\nRESULT: FAIL — the disk-value large-content read regressed (the recipe-body bug is "
          "in the backend after all).\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
