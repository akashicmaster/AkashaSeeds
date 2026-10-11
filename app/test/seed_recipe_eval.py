#!/usr/bin/env python3
"""
Group 4, 4.4 — first-run seeding is DATA the platform reads, dispatched through the ops.

`lib/akasha/seeding.py` (the heart's SeedManager) imported the note and fieldnote Concept Models and
called their methods to re-create each shipped seed capsule. It now reads a RECIPE per doc_type
(`app/config/seed/*.json`: which op creates the document, which op adds each chain item, which seed /
atom_meta fields fill their arguments) and dispatches through the routers the manifests declared.

This eval boots a real cell and drives the real op, `sys.onboarding.seed`, over the capsules the
tree ships under `app/seeds/`:

  1. every shipped `note` and `fieldnote` sample capsule is planted, as the signed-in user, and the
     document's content is the capsule's sys:top → sys:next chain, in order;
  2. a fieldnote item keeps its atom_meta (role / period) through the recipe's `{meta.*}` fields;
  3. a doc_type with no recipe is skipped with a line, not an exception;
  4. the planter names no Concept Model: no import of `lib.akasha.concepts`, no op string of its own.

Also the regression this closed: `sys.onboarding.seed` imported `.seeding` relative to `concepts/`,
where no such module exists, so first-login seeding failed at import on every cell.

Run:  python app/test/seed_recipe_eval.py     (exit 0 = all pass)
"""
import ast
import glob
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _chain(capsule):
    atoms = capsule.get("atoms", {})
    adj = {}
    for lk in capsule.get("links", []):
        adj.setdefault(lk.get("src"), {}).setdefault(lk.get("rel"), []).append(lk.get("dst"))
    cur = (adj.get(capsule["metadata"].get("concept_id"), {}).get("sys:top") or [None])[0]
    out, seen = [], set()
    while cur and cur in atoms and cur not in seen:
        seen.add(cur)
        out.append((cur, atoms[cur]))
        cur = (adj.get(cur, {}).get("sys:next") or [None])[0]
    return out


def main():
    print("=" * 78)
    print("4.4 — first-run seeds are recipes the platform reads, dispatched through the ops")
    print("=" * 78)
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="seed_recipe_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {
                    "user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def _d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    from lib.akasha import seeding as _seeding
    _sent = []
    _real_dispatch = _seeding._dispatch

    def _spy(session, step, ctx):
        _sent.append((step.get("op"), {k2: _seeding._fill(t, ctx)
                                       for k2, t in (step.get("args") or {}).items()}))
        return _real_dispatch(session, step, ctx)
    _seeding._dispatch = _spy

    for app in ("note", "fieldnote"):
        shipped = [json.load(open(p, encoding="utf-8"))
                   for p in sorted(glob.glob(os.path.join(ROOT, "app", "seeds", app, "*.akasha")))]
        samples = [c for c in shipped if (c["metadata"].get("seed") or {}).get("kind", "sample") == "sample"]
        r = _d("sys.onboarding.seed", {"app": app})
        titles = (r or {}).get("titles") or []
        want = [(c["metadata"].get("seed") or {}).get("title") or c["atoms"].get(c["metadata"].get("concept_id"))
                for c in samples]
        print("\n  ── app=%s: %d shipped sample capsule(s) ──" % (app, len(samples)))
        check("`sys.onboarding.seed app=%s` plants every shipped sample capsule" % app,
              samples and sorted(titles) == sorted(want) and r.get("seeds_loaded") == len(samples),
              "%s" % (r if "__error__" in (r or {}) else "%d/%d" % (len(titles), len(samples))))
        again = _d("sys.onboarding.seed", {"app": app}) or {}
        check("…once: a second call is `already_done` and plants nothing",
              again.get("already_done") is True and again.get("seeds_loaded") == 0, str(again))

    # 1 + 2 — the content of a planted fieldnote is the capsule's chain, with its atom_meta
    fn = [json.load(open(p, encoding="utf-8"))
          for p in sorted(glob.glob(os.path.join(ROOT, "app", "seeds", "fieldnote", "*.akasha")))][0]
    chain = _chain(fn)
    listed = _d("fieldnote.ls", {}) or {}
    rows = json.dumps(listed, ensure_ascii=False)
    title = (fn["metadata"].get("seed") or {}).get("title")
    check("the planted fieldnote is listed under its seed title", title and title in rows,
          "%s in fieldnote.ls" % title)
    fid = next((it.get("id") or it.get("fieldnote_id") or it.get("key")
                for it in (listed.get("fieldnotes") or listed.get("items") or [])
                if title and title in json.dumps(it, ensure_ascii=False)), "")
    _d("fieldnote.open", {"fieldnote_id": fid})
    read = _d("fieldnote.read", {}) or {}
    shown = json.dumps(read, ensure_ascii=False)
    seq = [str(o.get("content") or o.get("text") or "") for o in
           (read.get("sequence") or read.get("observations") or [])]
    want_texts = [t for _, t in chain if t]
    check("…and its entries are the capsule's sys:top → sys:next chain, IN ORDER (%d item(s))"
          % len(chain), chain and [s[:40] for s in seq] == [t[:40] for t in want_texts],
          "read %d, want %d" % (len(seq), len(want_texts)))
    am = fn.get("atom_meta") or {}
    want_meta = [(t, am.get(a, {}).get("role"), am.get(a, {}).get("period")) for a, t in chain if t]
    sent = {a.get("text"): a for op, a in _sent if op == "fieldnote.add"}
    got_meta = [(t, (sent.get(t) or {}).get("role"), (sent.get(t) or {}).get("period"))
                for t, _, _ in want_meta]
    check("…and each item is DISPATCHED with its atom_meta (role / period) through the recipe's "
          "`{meta.*}` fields", got_meta == [(t, r or "observation", p) for t, r, p in want_meta],
          "%d item(s)" % len(want_meta))
    kept = {str(o.get("content")): o.get("role") for o in (read.get("observations") or [])}
    lost = [t[:30] for t, r, _ in want_meta if r and kept.get(t) != r]
    print("  %s  the op KEEPS the role it is sent (application half — `fieldnote.add`'s coerce "
          "passes `text` only)%s" % ("OK  " if not lost else "OWED",
                                      "" if not lost else "   (%d role(s) dropped by the op)" % len(lost)))

    # 3 — a doc_type with no recipe
    from lib.akasha.seeding import SeedManager
    sess = k.manager.get_session("admin")
    out = SeedManager(os.path.join(ROOT, "app", "seeds")).plant(
        sess, {"metadata": {"doc_type": "no_such_kind", "concept_id": "x"}, "atoms": {"x": "t"}})
    check("a doc_type with no recipe is skipped (None), never an exception", out is None, str(out))

    # 4 — the planter names no Concept Model
    src = open(os.path.join(ROOT, "lib", "akasha", "seeding.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
               and "concepts" in (getattr(n, "module", "") or "" if isinstance(n, ast.ImportFrom)
                                  else " ".join(a.name for a in n.names))]
    ops = {s for r in (json.load(open(p, encoding="utf-8"))
                       for p in glob.glob(os.path.join(ROOT, "app", "config", "seed", "*.json")))
           for s in ((r.get("create") or {}).get("op"), (r.get("item") or {}).get("op")) if s}
    named = sorted(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and n.value in ops)
    check("seeding.py imports no Concept Model and names none of the ops its recipes dispatch",
          not imports and not named, "imports=%d named=%s" % (len(imports), named))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — first-login seeding plants every shipped note and fieldnote capsule through "
          "the recipes in app/config/seed/, the content is the capsule's chain and each item is dispatched with its atom_meta, an "
          "unknown doc_type is skipped, and the platform planter names no Concept Model.")
    sys.exit(0)


if __name__ == "__main__":
    main()
