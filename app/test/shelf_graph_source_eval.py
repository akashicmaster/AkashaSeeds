#!/usr/bin/env python3
"""
The Thinker's Shelf — the reading data comes OUT OF THE GRAPH.

A read work enters as an ontology pack (the source-data law: the deploy target does `onto` load
ONLY, no data file read at runtime). So on a running cell the passages are ATOMS — each one's
content is the verbatim JSON the acquisition emitted — and the episode is the Set that holds them.
This eval loads the Dibdin pack's passage atoms into a throwaway cell and checks that the driver
reads the episode back out of the graph, byte for byte, with nothing repaired:

  · every passage of the pack comes back, in a stable order
  · each one's text is IDENTICAL to the acquired file's text (no silent normalisation)
  · the anchor survives the round trip (page + uri/scan + ocr_span), so a fragment can return to
    its page — the §3 rule the programme refuses to air without
  · a passage with no anchor is dropped by the graph path exactly as by the file path
  · a Set that does not exist yields [] (so the driver falls back and SAYS it fell back), never a
    crash and never a silent fixture

Run:  python app/test/shelf_graph_source_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

PACK = os.path.join(ROOT, "app", "ontology", "shelf_dibdin")
AK = os.path.join(PACK, "dibdin_library_companion.ak")
PASSAGES = os.path.join(PACK, "passages_ep1.json")
EPISODE_SET = "shelf:dibdin:passages:ep1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


# The boot loader's own `.ak` line shape (kernel `_parse_ak_line`): shlex tokens, a bare-identifier
# `key=value` is a kwarg, everything else positional, and a def/write is written at universal scope.
_AK_MAP = {"def": ("kernel.memory.define", ["name", "description"]),
           "al": ("alias", ["id", "name"]),
           "ln": ("kernel.memory.link", ["src", "dst", "rel"]),
           "set.add": ("set.add", ["name", "id"])}
_KWARG = re.compile(r"^[A-Za-z_][\w.:-]*$")


def load_pack(d):
    """Load the pack the way the boot loader does — same tokenizer, same methods, same universal
    scope — so what this eval reads back is what a deployed cell would hold. Dispatched line by line
    so no ontology boot is needed (that would load every pack)."""
    import shlex
    n = {"def": 0, "al": 0, "ln": 0, "set.add": 0}
    for raw in open(AK, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line)
        except ValueError:
            continue
        if not parts or parts[0].lower() not in _AK_MAP:
            continue
        cmd = parts[0].lower()
        method, names = _AK_MAP[cmd]
        kw, pos = {}, []
        for tok in parts[1:]:
            if "=" in tok:
                k, v = tok.split("=", 1)
                if _KWARG.match(k.strip()):
                    kw[k] = v
                    continue
            pos.append(tok)
        params = {a: (kw[a] if a in kw else (pos[i] if i < len(pos) else ""))
                  for i, a in enumerate(names)}
        if method == "kernel.memory.define":
            params["scope"] = "universal"
        d(method, params)
        n[cmd] += 1
    return n


def main():
    from lib.akasha.kernel import KernelDispatcher
    from app.scripts.shelf_reading_cycle import load_passages_from_graph, load_passages

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_shelf_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")

    # the driver's dispatcher shape: d(client, method, data) -> the whole envelope
    def dd(_client, method, data):
        return d(method, data)

    print("\n  ── loading the acquired pack into a throwaway cell ──")
    n = load_pack(d)
    check("the pack's atoms, aliases, links and set memberships loaded",
          n["def"] >= 29 and n["set.add"] > 0 and n["ln"] > 0,
          "def=%d al=%d ln=%d set.add=%d" % (n["def"], n["al"], n["ln"], n["set.add"]))

    print("\n  ── the episode read back OUT OF THE GRAPH ──")
    from_file = json.load(open(PASSAGES, encoding="utf-8"))["passages"]
    from_graph = load_passages_from_graph(dd, "admin", EPISODE_SET)
    check("every acquired passage comes back from the graph",
          len(from_graph) == len(from_file),
          "graph=%d file=%d" % (len(from_graph), len(from_file)))

    by_atom = {p.get("atom"): p for p in from_graph}
    missing = [p.get("atom") for p in from_file if p.get("atom") not in by_atom]
    check("each passage is found by its own atom id", not missing, "missing=%s" % missing[:3])

    differ = []
    for p in from_file:
        g = by_atom.get(p.get("atom"))
        if g is not None and g.get("text") != p.get("text"):
            differ.append(p.get("atom"))
    check("the text is IDENTICAL to the acquired text (nothing repaired on the way out)",
          not differ, "differ=%s" % differ[:3])

    unanchored = [p.get("atom") for p in from_graph
                  if not ((p.get("anchor") or {}).get("page")
                          and ((p.get("anchor") or {}).get("uri") or (p.get("anchor") or {}).get("scan")))]
    check("every passage returns anchored (page + uri/scan) — §3", not unanchored,
          "bad=%s" % unanchored[:3])
    spans = [p.get("atom") for p in from_graph
             if not isinstance((p.get("anchor") or {}).get("ocr_span"), (list, tuple))]
    check("the ocr_span survives the round trip (re-readable at the source)", not spans,
          "bad=%s" % spans[:3])

    check("the order is stable (by atom id), so an episode reads the same way twice",
          [p.get("atom") for p in from_graph] == sorted(p.get("atom") for p in from_graph))

    # The classification is a MEMBERSHIP, not a tag in the record: so it is read the way anything
    # else in the graph is read — by listing the Set the passage was minted into.
    def _members(name):
        r = (d("set.ls", {"name": name, "limit": 200}) or {}).get("result") or {}
        return {m.get("alias") or m.get("key") for m in (r.get("members") or [])}

    in_level = _members("shelf:level:source")
    in_stratum = _members("shelf:stratum:original")
    atoms = {p.get("atom") for p in from_graph}
    check("a passage read from a page carries level=SOURCE as a Set membership",
          atoms and atoms <= in_level, "missing=%s" % sorted(atoms - in_level)[:3])
    check("…and stratum=original likewise — what is read on air is the text, not an analysis",
          atoms and atoms <= in_stratum, "missing=%s" % sorted(atoms - in_stratum)[:3])
    check("the record itself states neither (one source of truth, §5.1)",
          not [p for p in from_graph if "level" in p or "stratum" in p],
          "tagged=%s" % [p.get("atom") for p in from_graph if "level" in p][:3])

    print("\n  ── the fallback is honest ──")
    none_set = load_passages_from_graph(dd, "admin", "shelf:dibdin:passages:no_such_episode")
    check("an episode Set that is not loaded yields [] (the driver falls back and says so)",
          none_set == [], str(none_set)[:60])
    check("the file path drops an unanchored passage exactly as the graph path does",
          len(load_passages(PASSAGES)) == len(from_graph))

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the episode is read out of the graph: every acquired passage returns, its "
          "text byte-identical, its anchor and ocr_span intact, in a stable order; an unloaded "
          "episode yields [] rather than a silent fixture.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
