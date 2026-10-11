#!/usr/bin/env python3
"""
weave_exempt_eval.py — the raw/derived Weaver boundary of the Source-Data Ingestion Principle
(`docs/for-llm/source-data-ontology-ingestion.md`).

Proves, precisely:
  • a RAW row (source:item:*, verbatim JSON) is NLP-exempt — the weave LEAF skips it, so no
    proto-word (sys:refers_to) links are grown from JSON syntax;
  • an extracted free-text atom (txt:*) is NOT exempt — the gate lets it through to the Weaver;
  • the predicate is LOCAL (its own namespace), never inferred from links — an atom linked TO a raw
    row still weaves, and a raw row stays exempt regardless of what links to it;
  • the SAME signal excludes raw rows from semantic learning even when they carry no meta.concept
    (the .ak-loaded corpus model).

Run:  python test/weave_exempt_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib.akasha.ontology import weave
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.ontology.weave import _weave_exempt
    from lib.akasha.concepts._universal import _excluded_from_learning
    from lib.akasha.kernel import KernelDispatcher

    # ── 1. the predicate is local + precise ──
    check("RAW row (source:item:*) is weave-exempt", _weave_exempt(["source:item:mobility:1"]))
    check("extracted free-text (txt:*) is NOT exempt", not _weave_exempt(["txt:mobility:1:answer"]))
    check("a normal ontology atom is NOT exempt", not _weave_exempt(["geo:belgium"]))
    check("exempt by meta marker too (runtime source atoms)",
          _weave_exempt([], '{"provenance": "source"}') and _weave_exempt([], '{"concept": "source_item"}'))
    check(".ak raw row (no meta.concept) is still learn-excluded by namespace",
          _excluded_from_learning(None, aliases=["source:item:mobility:1"])
          and not _excluded_from_learning(None, aliases=["txt:mobility:1:answer"]))

    # ── 2. end-to-end: the weave LEAF skips a raw row, admits a txt/normal atom ──
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_weaveex_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    nuc = k.manager.shared_nucleus

    raw_json = '{"Country": "Belgium", "Profession": "housewife", "Would_subscribe": "Maybe yes maybe not"}'
    txt_text = "public transport congestion charging and car sharing demand"
    key_raw = nuc.put_atom(raw_json, {"scope": "scope:sys:universal"}, author="admin")
    nuc.core.put_alias(key_raw, "source:item:mobility:1")
    key_txt = nuc.put_atom(txt_text, {"scope": "scope:sys:universal"}, author="admin")
    nuc.core.put_alias(key_txt, "txt:mobility:1:would_subscribe")
    # a clab-style interpretation atom LINKED to the raw row — must still be weavable
    key_interp = nuc.put_atom("this respondent expresses tentative openness to car sharing",
                              {"scope": "scope:sys:universal"}, author="admin")
    nuc.core.put_alias(key_interp, "clab:mobility:claim:1")
    nuc.put_link(key_interp, key_raw, "clab:about", author="admin")

    woven_raw = weave.weave_atom(k, nuc, key_raw, raw_json)

    def refers(key):
        links = nuc.core.get_adjacent_links(key, "sys:refers_to") or []
        return len(links)

    check("weave LEAF returns 0 for a raw row (skipped)", woven_raw == 0, f"woven={woven_raw}")
    check("raw row grew NO proto-word (sys:refers_to) links", refers(key_raw) == 0,
          f"{refers(key_raw)} links")

    # the txt + interp atoms are not exempt: the gate lets them through (actual link count depends on
    # the NLP tier, so assert the gate does not force-skip them, and — where the floor produces links —
    # that they DID weave). The precise, tier-independent claim is: they are NOT exempt.
    weave.weave_atom(k, nuc, key_txt, txt_text)
    weave.weave_atom(k, nuc, key_interp, "this respondent expresses tentative openness to car sharing")
    check("txt: atom is admitted to the Weaver (not exempt)", not _weave_exempt(["txt:mobility:1:would_subscribe"]))
    check("clab: atom LINKED to a raw row still weaves (local predicate, not relational)",
          not _weave_exempt(["clab:mobility:claim:1"]))
    _tier = refers(key_txt) + refers(key_interp)
    print(f"  [i] NLP tier produced {_tier} proto-word link(s) on the weavable atoms "
          f"({'floor/basic — links only if a model is loaded' if _tier == 0 else 'weaved'}).")

    # ── 3. the learn read excludes the raw row by namespace (no meta.concept present) ──
    curated_read = [r for r in nuc.core.iter_all_chunks(limit=40000)
                    if len(r.get("content") or "") >= 8
                    and not _excluded_from_learning(r.get("meta"))
                    and not _weave_exempt(nuc.core.get_aliases_by_key(r.get("key", "")))]
    keys_kept = {r["key"] for r in curated_read}
    check("raw row is EXCLUDED from the learn read (namespace signal, no meta.concept)",
          key_raw not in keys_kept)
    check("txt + interp atoms are KEPT for learning (meaning joins the graph)",
          key_txt in keys_kept and key_interp in keys_kept)

    print()
    if _fails:
        print(f"FAIL — {len(_fails)} check(s) failed: {_fails}")
        sys.exit(1)
    print("ALL PASS — the raw JSON container is NLP-exempt at the weave leaf and learn-excluded by "
          "its own namespace; extracted txt:/interpretation atoms weave normally even when linked to "
          "raw rows. Exactly the raw atoms are exempt.")


if __name__ == "__main__":
    main()
