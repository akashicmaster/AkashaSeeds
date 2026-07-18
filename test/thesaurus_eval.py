#!/usr/bin/env python3
"""
Thesaurus eval — the simplified glossary read model (reference / explore / concept).

The thesaurus was reduced to three read operators, a glossary surface prepping
concepts for web concept pages:

  T1 reference alpha   — browse the concept catalogue alphabetically (glossary).
  T2 reference axis    — order= is extensible: a reserved axis (era/assoc/lang)
                         falls back to alpha, reported via order_applied.
  T3 explore delegates — search reuses the SAME core as the `explore` command
                         (lib/akasha/discovery.py) — no double code.
  T4 concept = dive+   — concept builds on the dive basic view (generate_view:
                         signposts/resonance/cosmos_nd) and extends it with the
                         writer's view: synonyms/antonyms/broader/narrower/examples.
  T5 explore regression — refactoring explore's core did not change the command.
  T6 old ops removed   — shelf.*/curation.*/series.* no longer served.

Run:  python test/thesaurus_eval.py
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def main():
    print("\n  thesaurus eval — glossary read model (reference / explore / concept)\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_thes_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else r.get("error")

    def mk(name, desc):
        return (d("def", {"name": name, "description": desc}) or {}).get("key")

    # A tiny glossary: four words + typed relations.
    memory   = mk("word:en:memory",   "the faculty of retaining and recalling information")
    recall   = mk("word:en:recall",   "to bring a past event back to mind")
    oblivion = mk("word:en:oblivion", "the state of being forgotten")
    amnesia  = mk("word:en:amnesia",  "loss of memory")
    d("ln", {"src": memory,  "dst": recall,   "rel": "thesaurus:synonym"})
    d("ln", {"src": memory,  "dst": oblivion, "rel": "thesaurus:antonym"})
    d("ln", {"src": amnesia, "dst": memory,   "rel": "thesaurus:hypernym"})   # memory is broader than amnesia
    # A usage example attached to memory.
    ex = mk("word:en:memory:ex1", "Her memory of that summer never faded.")
    d("ln", {"src": memory, "dst": ex, "rel": "thesaurus:example_usage"})

    # T1 — reference: alphabetical glossary.
    ref = d("thesaurus.reference", {"ns": "word", "limit": 50})
    terms = [c["term"] for c in ref.get("concepts", [])]
    alpha_ok = terms == sorted(terms, key=lambda t: (t.casefold(), t)) and "memory" in terms
    record("T1 reference alpha", alpha_ok and ref.get("order_applied") == "alpha",
           f"order={terms}")

    # initial= letter-jump + grouping headers.
    ref_m = d("thesaurus.reference", {"ns": "word", "initial": "m"})
    only_m = all(c["term"].lower().startswith("m") for c in ref_m.get("concepts", []))
    record("T1b initial jump", only_m and any(c["initial"] == "M" for c in ref_m.get("concepts", [])),
           f"initial=m → {[c['term'] for c in ref_m.get('concepts', [])]}")

    # T2 — reserved ordering axis falls back to alpha, reported honestly.
    ref_era = d("thesaurus.reference", {"ns": "word", "order": "era"})
    record("T2 reference axis", ref_era.get("order") == "era"
           and ref_era.get("order_applied") == "alpha",
           f"order=era → applied={ref_era.get('order_applied')}")

    # T3 — explore search (delegates to the shared discovery core).
    exq = d("thesaurus.explore", {"query": "word:en:mem"})
    hit = {m["term"] for m in exq.get("matches", [])}
    record("T3 explore search", "memory" in hit and exq.get("count", 0) >= 1
           and all("salience" in m for m in exq.get("matches", [])),
           f"query 'mem' → {hit}")

    # T4 — concept: dive basic view + writer's related links.
    cn = d("thesaurus.concept", {"name": "word:en:memory"})
    syn = {s["term"] for s in cn.get("synonyms", [])}
    ant = {s["term"] for s in cn.get("antonyms", [])}
    dive_base = "signposts" in cn and cn.get("cosmos_nd") is not None
    examples_ok = any("faded" in (e.get("text") or "") for e in cn.get("examples", []))
    record("T4 concept dive+", "recall" in syn and "oblivion" in ant and dive_base and examples_ok,
           f"syn={syn} ant={ant} dive_base={dive_base} examples={len(cn.get('examples', []))}")

    # bare-word resolution (leaf fallback) still resolves to the concept.
    cn2 = d("thesaurus.concept", {"name": "memory"})
    record("T4b bare word", isinstance(cn2, dict) and cn2.get("atom", {}).get("term") == "memory",
           f"'memory' → {cn2.get('atom', {}).get('term') if isinstance(cn2, dict) else cn2}")

    # T5 — the explore COMMAND is unchanged by the core refactor.
    exc = d("explore", {"ns": "word"})
    record("T5 explore cmd", isinstance(exc, dict) and exc.get("count", 0) >= 4
           and "atoms" in exc and "filters" in exc,
           f"explore ns=word → count={exc.get('count') if isinstance(exc, dict) else exc}")

    # T6 — the removed operators are no longer served.
    removed = ["thesaurus.shelf.list", "thesaurus.curation.ls", "thesaurus.series.ls",
               "thesaurus.view.atom"]
    gone = all(isinstance(d(m, {}), dict) and "code" in d(m, {}) for m in removed)
    record("T6 old ops gone", gone, f"{removed} all error out")

    # T7 — archives-projection seam: the compat keys the archives model's normaliser
    # reads (results/entries + concept.semantic_links) are present, so archives.*
    # projects the thesaurus without touching its own file.
    ax = d("archives.explore", {"query": "word:en:mem"})
    ar = d("archives.reference", {"limit": 10})
    sp = d("archives.space", {"name": "word:en:memory"})
    seam = (isinstance(ax, dict) and ax.get("entries") is not None
            and isinstance(ar, dict) and ar.get("entries") is not None
            and isinstance(sp, dict)
            and any(r.get("ref") == "word:en:recall" for r in (sp.get("related") or [])))
    record("T7 archives seam", seam,
           f"archives.explore/reference normalise + space related has synonym")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the simplified thesaurus model is not behaving as specified.")
        return 1
    print("\nRESULT: PASS — thesaurus is a 3-op glossary: reference (alpha, extensible), "
          "explore (shared core), concept (dive + writer's view); explore command intact; "
          "old ops removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
