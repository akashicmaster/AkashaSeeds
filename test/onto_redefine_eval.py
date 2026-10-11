#!/usr/bin/env python3
"""
D16 — a REDEFINED def name binds to its new text, and the reconcile retires only the old one.

Directive 2026-10-02 §1. At the 09-28 deploy the reconcile of `station_neta` logged
`keys=59 retired=45` while the pack's files defined 104 atoms: the 45 it retired were the NEW texts
of the item ids the 09-27 batch had REDEFINED. The keep-set resolved those names to their stale
keys, so it kept the old atoms and retired the ones the files define; before that reload the
programme had aired the new texts under bare content keys, because no alias mapped back from them.
The Set held 18 of 48 items afterwards.

This eval runs the REAL loader over a small project (`AKASHA_PROJECT_DIR`, as
`ontology_sentinel_eval` does), on a real cell:

  1. pack P, file A: `def X "old"`, `set.add name=S id=X`; load;
  2. remove A, add file B: `def X "new"`, `set.add name=S id=X`; load;
  3. reload P once more with an unrelated change (a new def in another file).

After steps 2 and 3:
  * `X` resolves to the key of "new";
  * the reverse lookup from that key gives `X`, and the old key no longer answers `X`;
  * `S` contains the new key and not the old;
  * the reconcile retires the old key only;
  * the reconcile line's `keys` equals the number of atoms the files define.

And two the incident adds:
  4. a cell the old reconcile DAMAGED (the name unbound, the new atom evicted and out of its Set,
     the file's sentinel still present) heals on the next load of the pack: the file is named and
     re-run, the name binds to the new text again, the atom is live and back in S;
  5. the reconcile removes only a name that still points at the key it retires.

Both backends run, each in its own process: Silica (the thesaurus line's store, whose alias rebind
left the old key's reverse entry behind) and SQLite.

Run:  python test/onto_redefine_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Log(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, rec):
        self.lines.append(rec.getMessage())


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _num(line, key):
    for tok in line.replace(":", " ").split():
        if tok.startswith(key + "="):
            try:
                return int(tok.split("=", 1)[1])
            except ValueError:
                return -1
    return -1


X, S = "rd:item:001", "rd:items"


def main():
    print("=" * 78)
    print("D16 — a redefined def binds to its new text; the reconcile retires only the old one")
    print("=" * 78)
    root = tempfile.mkdtemp(prefix="onto_redefine_")
    ont = os.path.join(root, "ontology")
    pdir = os.path.join(ont, "p_rd")
    _write(os.path.join(pdir, "PACK.json"), [json.dumps({"label": "p_rd"})])
    _write(os.path.join(ont, "REGISTRY.json"), [json.dumps({"version": 2, "packages": [
        {"name": "p_rd", "autoload": True}]})])
    _write(os.path.join(root, "config", "ontology", "packs.json"), [json.dumps({"load_all": True})])
    # step 1 — file A: X "old", in S; plus a sibling that never changes
    _write(os.path.join(pdir, "a.ak"), [
        'def "%s" "Item one — the OLD text"' % X,
        'set.add name="%s" id="%s"' % (S, X),
    ])
    _write(os.path.join(pdir, "keep.ak"), [
        'def "rd:item:002" "Item two — unchanged"',
        'set.add name="%s" id="rd:item:002"' % S,
    ])
    os.environ["AKASHA_PROJECT_DIR"] = root
    # the fixture project is the whole project: its application root is its own (empty) `app/`,
    # so the loader reads this ontology only, not the repository's application packs
    os.environ["AKASHA_APP_DIR"] = os.path.join(root, "app")

    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology import loader as L
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=os.path.join(root, "cell"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    time.sleep(1.0)
    k._boot_daemons_started = True
    log = _Log()
    for lg in ("Akasha.Kernel", "Akasha.Reconcile", ""):
        logging.getLogger(lg).addHandler(log)
    logging.getLogger("Akasha.Kernel").setLevel(logging.INFO)
    nuc = k.manager.shared_nucleus

    def load():
        log.lines.clear()
        k._schedule_gates = None
        L.boot_load_ontology(k)

    def key_of(name):
        return nuc.core.get_key_by_alias(name)

    def text(key):
        row = nuc.core.get_chunk_raw(key) if key else None
        if row and str(row.get("status") or "") == "evicted":
            return "(evicted) " + str(row.get("content") or "")
        return (row or {}).get("content") or ""

    def members():
        return set(nuc.core.get_collection_members(S) or [])

    def recon_line():
        got = [l for l in log.lines if "Reconcile 'p_rd'" in l]
        return got[-1] if got else ""

    print("\n  ── step 1: X is defined OLD ──")
    load()
    old = key_of(X)
    check("X resolves to the OLD text, and S holds it", "OLD text" in text(old) and old in members(),
          "key=%s members=%d" % ((old or "")[:12], len(members())))

    print("\n  ── step 2: A removed, B defines X NEW ──")
    os.remove(os.path.join(pdir, "a.ak"))
    _write(os.path.join(pdir, "b.ak"), [
        'def "%s" "Item one — the NEW text"' % X,
        'set.add name="%s" id="%s"' % (S, X),
    ])
    load()

    def after(step):
        new = key_of(X)
        check("[%s] X resolves to the key of the NEW text" % step, "NEW text" in text(new),
              "key=%s text=%r" % ((new or "")[:12], text(new)[:40]))
        rev_new = nuc.core.get_aliases_by_key(new) if new else []
        check("[%s] the reverse lookup from the new key gives X" % step, X in (rev_new or []),
              str(rev_new))
        check("[%s] …and the old key no longer answers X" % step,
              X not in (nuc.core.get_aliases_by_key(old) or []), str(nuc.core.get_aliases_by_key(old)))
        m = members()
        check("[%s] S contains the new key and not the old" % step, bool(new) and new in m and old not in m,
              "new_in=%s old_in=%s n=%d" % (new in m, old in m, len(m)))
        return new

    new = after("step 2")
    rl = recon_line()
    check("[step 2] the reconcile retires the old key ONLY (retired=1)", _num(rl, "retired") == 1, rl)
    check("[step 2] the reconcile's keys = the atoms the files define (2)", _num(rl, "keys") == 2, rl)
    try:
        evicted = (nuc.core.get_meta(old) or {}) if hasattr(nuc.core, "get_meta") else {}
    except Exception:
        evicted = {}

    print("\n  ── step 3: an unrelated change reloads P ──")
    _write(os.path.join(pdir, "c.ak"), ['def "rd:item:003" "Item three — new"'])
    load()
    after("step 3")
    rl = recon_line()
    check("[step 3] the reconcile retires nothing more (retired=0)", _num(rl, "retired") == 0, rl)
    check("[step 3] the reconcile's keys = the atoms the files define (3)", _num(rl, "keys") == 3, rl)

    print("\n  ── step 4: a cell the old reconcile DAMAGED heals on the next load of the pack ──")
    # The 09-28 state, made by hand: the redefined name deleted from under its new text, the new
    # atom retired (evicted) and dropped from its Set — while b.ak's per-file sentinel says it ran.
    cur_new = key_of(X)
    nuc.core.delete_alias(X)
    nuc.core.remove_from_collection(S, cur_new)
    nuc.core.update_chunk_status(cur_new, "evicted", None)
    check("(the damage is in place: X unbound, the new atom evicted, S without it)",
          not key_of(X) and cur_new not in members() and "(evicted)" in text(cur_new),
          "X=%s" % key_of(X))
    ks = L.pack_def_key_set(k, k.manager.get_session("admin"), "p_rd")
    check("the reconcile's keep-set is computed from the FILES: it holds the new text's key even "
          "while the store has X unbound (the 09-28 keep-set asked the store and lost 45 keys)",
          cur_new in ks and old not in ks and len(ks) == 3, "n=%d new_in=%s" % (len(ks), cur_new in ks))
    _write(os.path.join(pdir, "d.ak"), ['def "rd:item:004" "Item four — new"'])
    load()
    healed = [l for l in log.lines if "not bound to this file's text" in l]
    check("[step 4] the load names the damaged file and reloads it (b.ak)",
          any("'b.ak'" in l for l in healed), str(healed[:1]))
    after("step 4")
    check("[step 4] the new atom is live again", "(evicted)" not in text(key_of(X)) and
          "NEW text" in text(key_of(X)), text(key_of(X))[:40])
    rl = recon_line()
    check("[step 4] the reconcile keeps it: retired=0, keys = the 4 atoms the files define",
          _num(rl, "retired") == 0 and _num(rl, "keys") == 4, rl)

    print("\n  ── the reconcile removes only a name that still points at the key it retires ──")
    from lib.akasha.ontology_reconcile import OntologyReconciler

    class _Core:
        deleted = []

        def get_aliases_by_key(self, k):
            return [X, "rd:only_old"]

        def get_key_by_alias(self, a):
            return "NEWKEY" if a == X else "OLDKEY"

        def delete_alias(self, a):
            self.deleted.append(a)

        def get_adjacent_links(self, k):
            return []

        def get_collections_for_key(self, k):
            return []

        def update_chunk_status(self, *a):
            pass

    class _Store:
        core = _Core()
    OntologyReconciler(_Store()).retire("OLDKEY")
    check("retiring OLDKEY deletes the name that points at it and NOT the redefined X (which "
          "points at NEWKEY) — even when a stale reverse entry lists X under OLDKEY",
          _Core.deleted == ["rd:only_old"], str(_Core.deleted))

    shutil.rmtree(root, ignore_errors=True)
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a redefined def name binds to its new text both ways, its Set follows it, "
          "and the reconcile retires the old text only and counts what the files define.")
    sys.exit(0)


if __name__ == "__main__":
    if os.environ.get("AKASHA_BACKEND"):
        main()
    # Both backends, each in its own process (the store is chosen at import). Silica is the one the
    # thesaurus line runs, and the one whose alias rebind left the old key's reverse entry behind.
    import subprocess
    rc = 0
    for be in ("silica", "sqlite"):
        print("\n#### backend=%s" % be)
        rc |= subprocess.call([sys.executable, os.path.abspath(__file__)],
                              env=dict(os.environ, AKASHA_BACKEND=be))
    print("\nRESULT: %s on both backends" % ("PASS" if rc == 0 else "FAIL"))
    sys.exit(rc)
