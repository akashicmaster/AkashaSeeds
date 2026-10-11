#!/usr/bin/env python3
"""
Cross-language proto-word bridge eval — the `lex:bridge` traversal fix.

Design: Akasha's ontology is built around ENGLISH proto-words (祖語). Non-English text yields its OWN
proto-words, isolated from the English graph. The fix bridges the PROTO-WORDS ONLY
(foreign_proto --lex:bridge--> english_proto), and `generate_view` folds the English proto's
neighbourhood + set-bearing senses into the foreign atom's view — so a non-English atom instantly
reuses the English links and sets, WITHOUT copying anything.

This eval builds a tiny English concept (apple + a sense with a real edge + a set membership), a French
proto (pomme), bridges them, and asserts:
  • BEFORE the bridge: a dive on `pomme` is isolated — no English neighbours.
  • AFTER the bridge: a dive on `pomme` surfaces the English edge (tagged `bridged`), and the
    set-bearing English sense is reachable → the French atom can reuse the English set.

Run:  python app/test/lex_bridge_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_bridge_"))
    gw = AkashaGateway(kernel_client=k)

    def cli(line):
        return gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                            "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local")

    def view(alias):
        r = gw.dispatch({"jsonrpc": "2.0", "method": "view",
                         "params": {"session_token": "admin", "data": {"id": alias}}, "id": "v"}, "local")
        return r.get("result") or {}

    def settle(alias, rel="sys:refers_to", timeout=15.0):
        """Wait for the FRESHLY-CREATED English concept's background weave to land its
        `sys:refers_to` proto link + `set:word:*` membership before we dive across the bridge.
        In a real deployment the English graph pre-exists (weaved long ago), so the bridge folds
        immediately; this eval builds the English concept milliseconds before diving, so its weave
        is still a queued `sys.weaver.weave_batch` job. That is test-setup latency, NOT the bridge
        behaviour under test — settle it deterministically instead of racing the async weave (the
        race surfaced once dives got faster; the fold-in logic is unchanged)."""
        cortex = k.manager.get_session("admin").local_cortex
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            key = cortex.resolve_alias(alias)
            if key and any(l.get("rel") == rel
                           for l in (cortex.get_magnetic_neighborhood(key) or [])):
                return True
            time.sleep(0.1)
        return False

    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    # ── English concept: a sense atom (bare alias "apple" → proto), a real edge, a set membership ──
    cli('def "color:red" "the colour red."')
    cli('al color:red red')
    cli('def "ingred:fruit:apple" "An apple — a common pomaceous fruit."')
    cli('al ingred:fruit:apple apple')                 # bare alias → mints proto(apple) + specializes
    cli('ln ingred:fruit:apple color:red thesaurus:related')   # an English edge on the sense
    cli('set.add name="fruit:all" id="ingred:fruit:apple"')    # an English set on the sense

    # ── French proto-word (its own atom, isolated from the English graph) ──
    cli('def "word:fr:pomme" "pomme — French for apple."')
    cli('al word:fr:pomme pomme')

    def neighbours(v):
        return {s.get("alias") or s.get("label") or s.get("key", "")[:8]: s for s in v.get("signposts", [])}

    # ── BEFORE the bridge: pomme is isolated (no English `red`, no bridged nodes) ──
    before = view("pomme")
    nb = neighbours(before)
    check("before bridge: a dive on `pomme` does NOT reach the English neighbour `red`",
          not any("red" in a for a in nb) and not any(s.get("bridged") for s in before.get("signposts", [])),
          f"{list(nb)[:6]}")

    # ── bridge the proto-words only ──
    r = cli('ln pomme apple lex:bridge')
    check("bridge: pomme --lex:bridge--> apple created", "error" not in r)

    # ── AFTER the bridge: the English edge folds into pomme's view, tagged `bridged` ──
    settle("ingred:fruit:apple")           # let the English sense's weave land before diving across
    after = view("pomme")
    sp = after.get("signposts", [])
    bridged = [s for s in sp if s.get("bridged")]
    red = next((s for s in sp if "red" in (s.get("alias") or s.get("label") or "")), None)
    check("after bridge: pomme's view now surfaces the English edge → `red` (folded across the bridge)",
          red is not None, f"{[s.get('alias') or s.get('label') for s in sp][:8]}")
    check("after bridge: the folded English neighbours are tagged `bridged` (provenance via the English proto)",
          bool(bridged) and all(s.get("via") for s in bridged), f"{len(bridged)} bridged")

    # ── the set-bearing English sense + its set are reachable → the French atom reuses the English set ──
    cortex = k.manager.get_session("admin").local_cortex
    apple_sense = cortex.resolve_alias("ingred:fruit:apple")
    sets_on_sense = set(cortex.core.get_collections_for_key(apple_sense) or [])
    reachable = {s.get("alias") or s.get("label") or "" for s in sp}
    check("set reuse: the English set `fruit:all` is folded into pomme's view (the sense carries it)",
          "fruit:all" in sets_on_sense and any("fruit:all" in a for a in reachable),
          f"sets={sorted(sets_on_sense)}")

    # ── nothing copied: the surfaced English sense is the SAME atom, shared (reuse, not duplication) ──
    sense_sp = next((s for s in sp if (s.get("alias") or s.get("label")) == "ingred:fruit:apple"), None)
    check("nothing copied: the folded English sense IS the canonical atom (same key — reuse, not a copy)",
          sense_sp is not None and sense_sp.get("key") == apple_sense, f"key match={bool(sense_sp)}")

    # ── the on-demand builder op (lex.bridge) + pluggable provider ───────────────
    def D(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": "admin", "data": data}, "id": "b"}, "local")
        return r.get("result") or r.get("error") or {}

    cli('def "animal:cat" "a cat — a small carnivorous mammal."')
    cli('al animal:cat cat')
    cli('def "word:fr:chat" "chat — French for cat."')
    cli('al word:fr:chat chat')
    # MOCK provider (network is blocked here; the live wikidata/wikipedia providers run off-web)
    import app.concepts.lexbridge as _lb
    _lb._wikidata_translate = lambda word, lang: {"chat": "cat"}.get(word)
    rb = D("lex.bridge", {"word": "chat", "lang": "fr"})
    check("lex.bridge op: the mock provider bridges chat(fr) → cat (on-demand translation → bridge)",
          rb.get("status") == "bridged" and rb.get("english") == "cat", str(rb))
    # the bridge is real: chat's view now reaches the English `cat` proto
    settle("animal:cat")                   # let the English sense's weave land before diving across
    chat_view = view("chat")
    check("lex.bridge op: after building, a dive on `chat` reaches the English graph (bridged)",
          any(s.get("bridged") for s in chat_view.get("signposts", [])))
    # no translation → honest, NO bridge fabricated
    rn = D("lex.bridge", {"word": "zzqqx", "lang": "fr"})
    check("lex.bridge op: no translation → honest no-bridge (never fabricated)",
          rn.get("status") == "no_translation", str(rn))
    # manual english= override (also how a curated OMW list would load)
    cli('def "word:fr:matou" "matou — French (familiar) for cat."')
    cli('al word:fr:matou matou')
    ro = D("lex.bridge", {"word": "matou", "lang": "fr", "english": "cat"})
    check("lex.bridge op: manual english= override bridges (curated-list path)",
          ro.get("status") == "bridged" and ro.get("target") == "cat", str(ro))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — lex:bridge: bridging the proto-words only lets a non-English atom instantly reuse "
          "the English graph — the folded English edges are tagged `bridged`, and the set-bearing English "
          "sense is reachable, with nothing copied.")
    sys.exit(0)


if __name__ == "__main__":
    main()
