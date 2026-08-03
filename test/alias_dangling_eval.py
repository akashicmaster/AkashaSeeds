#!/usr/bin/env python3
"""
Alias / define integrity eval — three silent-failure bugs in the basic authoring
flow that the cookbook's green chapter and quick-start teach (v1.2 regression).

Discovered on the v1.2 release build: the CLI `def "name" "description"` swallowed
the SECOND quoted string into the name (router declared only ["name"], and the
parser's "last declared arg absorbs all remaining tokens" rule joined the whole
sentence). The alias became the entire sentence, the intended id was never
registered, and the follow-up `r <id>` returned not-found — with NO error. Two
linked bugs shared the root cause:

  D1 def 2-arg    — `def "id" "desc"` binds the alias to `id` ONLY (not the sentence),
                    and the description lands in the atom body. `r id` then resolves.
  D2 al rejects   — `al <src> <name>` with an UNRESOLVED src is refused (-32602), not
                    silently bound to a dangling raw-string key. `.ak` loading is
                    unaffected (it aliases resolved atoms).
  D3 no shadow    — a pre-existing DANGLING local alias (a non-hash key with no atom
                    body, from a v1.2 cell) no longer shadows the real nucleus atom of
                    the same name: resolve_alias self-heals (drops the dangling alias)
                    and falls through to the nucleus, so `r <name>` reaches the shared
                    atom again. A GENUINE cross-store local alias (local→nucleus hash)
                    is preserved untouched.

Run:  python test/alias_dangling_eval.py
"""
import os
import sys
import hashlib
import tempfile
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


def part_a_dispatch():
    """D1 + D2 through the full shell path: CommandRouter → kernel dispatch."""
    from lib.akasha.kernel import KernelDispatcher
    from api.router import CommandRouter
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_alias_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def run(cli):
        p = CommandRouter.build_rpc_request(cli, "admin")
        if p is None:
            return {"error": {"code": -1, "message": "UNKNOWN_COMMAND"}}
        return k.dispatch(p, "local")

    # D1 — def splits name / description; the alias is the id ALONE, and r finds it.
    d = run('def "wptest:alpha" "A short two-argument definition test."')
    alias = (d.get("result") or {}).get("alias")
    rr = run("r wptest:alpha")
    res = rr.get("result") or {}
    body = res.get("content") or ""
    d1 = (alias == "wptest:alpha"
          and "error" not in rr
          and "wptest:alpha" in (res.get("aliases") or [])
          and "two-argument" in body)
    record("D1 def 2-arg", d1,
           f"alias={alias!r} read_ok={'error' not in rr} desc_in_body={'two-argument' in body}")

    # D2 — al on an UNRESOLVED src is refused, and no dangling alias is created.
    a = run("al place:france france")
    refused = a.get("error", {}).get("code") == -32602
    # the name must not have become resolvable (no silent dangling bind)
    still_absent = run("r france").get("error", {}).get("code") in (-32002, -32602)
    record("D2 al rejects", refused and still_absent,
           f"refused={refused} france_absent={still_absent}")

    # D2b — al on a RESOLVED src still works (regression guard: we didn't over-reject).
    run('def "wptest:beta" "Second definition."')
    ab = run("al wptest:beta beta_nick")
    ok_alias = "error" not in ab and run("r beta_nick").get("result", {}).get("aliases")
    record("D2b al resolves", bool(ok_alias),
           f"nick_bound={'error' not in ab}")


def part_b_shadow():
    """D3 — dangling local alias must not shadow the nucleus; cross-store alias survives."""
    from lib.akasha.composite import NucleusEngine, AkashaEngine
    from lib.akasha.resolver import ContextResolver

    tmp = tempfile.mkdtemp(prefix="akasha_shadow_")
    nuc = NucleusEngine(os.path.join(tmp, "nucleus.db"))
    cortex = AkashaEngine(os.path.join(tmp, "cortex.db"), is_volatile=False)
    cortex.attach_nucleus(nuc)

    # Real shared atom in the nucleus, aliased `france`.
    fk = nuc.put_atom("[france]\nFrance — a country in Western Europe.",
                      {"type": "hub"}, author="admin", alias="france")

    # Inject a v1.2-style DANGLING local alias: france → "place:france" (non-hash, no body).
    cortex.core.put_alias("place:france", "france")
    pre = cortex.core.get_key_by_alias("france")            # local sees the dangling key

    resolved = cortex.resolve_alias("france")               # NEW: self-heal → nucleus
    healed = cortex.core.get_key_by_alias("france") is None  # dangling alias dropped
    d3 = (pre == "place:france" and resolved == fk and healed)
    record("D3 no shadow", d3,
           f"was_dangling={pre=='place:france'} now_resolves_nucleus={resolved==fk} healed={healed}")

    # The real read path (ContextResolver → _handle_read) now reaches the nucleus atom.
    sess = SimpleNamespace(cortex=cortex, nucleus=nuc, last_written_id=None,
                           allowed_scopes=None, active_scopes=None,
                           group_engines={}, locale=None, symbols={})
    via_resolver = ContextResolver.resolve(sess, "france", [])
    record("D3b read path", via_resolver == fk,
           f"resolver→{'nucleus' if via_resolver == fk else via_resolver}")

    # A GENUINE cross-store local alias (local→nucleus hash) must be preserved, not healed.
    cortex.core.put_alias(fk, "myfr")
    r2 = cortex.resolve_alias("myfr")
    preserved = (r2 == fk and cortex.core.get_key_by_alias("myfr") == fk)
    record("D3c cross-store", preserved,
           f"resolves={r2 == fk} alias_kept={cortex.core.get_key_by_alias('myfr') == fk}")


def main():
    print("\n  alias / define integrity eval — v1.2 silent-failure fixes (def / al / shadow)\n")
    part_a_dispatch()
    part_b_shadow()

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — a basic-authoring silent failure has returned.")
        return 1
    print("\nRESULT: PASS — def splits name/description, al refuses unresolved targets, "
          "and a dangling alias no longer shadows the shared nucleus atom.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
