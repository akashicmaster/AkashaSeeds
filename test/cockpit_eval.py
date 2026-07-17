#!/usr/bin/env python3
"""
Cockpit eval — human readability of the vessel (the concept model's first priority).

Warping to a concept lands the focus on a hash-keyed catalog set (set:concept:<hash>) whose
only name is the hash, so the Cosmos FOCAL LOCK / wake / node labels read as gibberish unless
the front-end guesses from content. Two backend fixes make the cockpit readable at the source:

  K1 set alias   — a new/opened cockpit gives its catalog set a human-readable alias
                   (concept:<slug(name)>), so the set key resolves to a real name, not the hash.
  K2 collision   — first-wins: if that alias is already bound to another atom, the cockpit set
                   does NOT steal it (readability must never corrupt an existing binding).
  K3 beacon LOC  — a dropped beacon persists focal_preview (the focal atom's content head), and
                   cockpit.wake returns it — so the Trace Deck shows "LOC: Rome", not a hash.

Run:  python test/cockpit_eval.py
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


def _hashlike(s):
    s = (s or "").split(":")[-1]
    return len(s) >= 12 and all(ch in "0123456789abcdef" for ch in s.lower())


def main():
    print("\n  cockpit eval — readable set alias + beacon focal preview\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cp_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data=None):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data or {}}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    cortex = k.manager.get_session("admin").local_cortex

    # K1 — cockpit.new registers a readable alias on its catalog set.
    r = d("cockpit.new", {"name": "Apple Deck"})
    cid = (r or {}).get("cockpit_id")
    setk = f"set:concept:{cid}"
    aliases = cortex.get_aliases_by_key(setk) or []
    readable = [a for a in aliases if not _hashlike(a)]
    record("K1 set alias", "concept:apple_deck" in aliases and bool(readable),
           f"set aliases={aliases}")

    # K2 — collision-safe: an alias already owned by an atom is not stolen by a cockpit set.
    atom = (d("def", {"name": "concept:rome", "description": "Rome, the eternal city"}) or {}).get("key")
    d("cockpit.new", {"name": "Rome"})                      # would want concept:rome
    still_atom = cortex.resolve_alias("concept:rome")
    record("K2 collision", still_atom == atom and atom is not None,
           f"concept:rome still → atom={still_atom == atom}")

    # K3 — beacon persists a readable focal preview; wake returns it.
    d("cockpit.new", {"name": "Voyage"})
    focus = (d("w", {"content": "Rome is the capital of Italy and the heart of the empire"}) or {}).get("key")
    d("cockpit.lock", {"target": focus})
    d("cockpit.beacon", {"note": "noted the eternal city here"})
    wake = d("cockpit.wake", {}) or {}
    items = wake.get("wake", [])
    prev = items[0].get("focal_preview") if items else None
    record("K3 beacon LOC", bool(prev) and prev.startswith("Rome") and not _hashlike(prev),
           f"wake={len(items)}, focal_preview={prev!r}")

    # K4 — the alias is applied uniformly: other concept models get readable catalog-set
    # aliases too (ensure_concept_set is wired into every model's op_new via BaseConcept).
    checks = [
        ("survey.new", {"title": "Fruit Basket"}, "survey_id",   "concept:fruit_basket"),
        ("note.new",   {"title": "Travel Log"},   "note_id",     "concept:travel_log"),
        ("human.new",  {"name": "Ada Lovelace"},  "human_id",    "concept:ada_lovelace"),
    ]
    ok_all, detail = True, []
    for method, data, id_field, want in checks:
        res = d(method, data) or {}
        cid_m = res.get(id_field)
        al = cortex.get_aliases_by_key(f"set:concept:{cid_m}") or [] if cid_m else []
        hit = want in al
        ok_all = ok_all and hit
        detail.append(f"{method.split('.')[0]}={'ok' if hit else al}")
    record("K4 all models", ok_all, ", ".join(detail))

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the cockpit is not human-readable at the source.")
        return 1
    print("\nRESULT: PASS — the cockpit reads as names, not hashes: catalog sets carry a "
          "collision-safe readable alias, and beacons persist a readable focal preview.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
