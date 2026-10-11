#!/usr/bin/env python3
"""
The public doors the station concept needs, so it can stop reaching into platform privates.

The frontend reported `bench_station.py` calling three private members of `SocietyConcept` —
`_group_engine`, `_society_key`, `_declared_casts` — and fixed none of them, correctly: the fix is a
PUBLIC read the platform has to expose. This eval proves the doors exist and answer what the
private calls answered, on a cell provisioned from the real declarations, as the real programme
clients — so the application can switch without changing behaviour.

It also settles the fourth site the report did not list. `_seal` (bench_station ~939) reaches
further: `ChrononConcept._chronons_set` and `._mint`, plus the society's frontier read straight
off the group engine's core. A public door ALREADY exists for that — `chronon.seal` — and the
question is whether the programme client may use it, because `_mint` skips the seal gate
(scribe / chairman / admin) that `chronon.seal` enforces. Measured: every programme client is its
society's CHAIRMAN, so the public op admits it and nothing the station does today is refused.

Run:  python test/workbench_public_reads_eval.py     (exit 0 = all pass)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "test"))
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap:
    lines = []


def main():
    print("=" * 78)
    print("Public reads for the station: society_key, declared_casts, and chronon.seal")
    print("=" * 78)
    import workload_conformance_eval as C                 # its fresh-cell builder, reused
    from lib.akasha.workbench import provision, workload as W
    from lib.akasha.concepts.society import SocietyConcept
    from lib.akasha.concepts.chronon import ChrononConcept

    k = C._cell(_Cap())
    provision.provision_workloads(k)
    decls = list(W.declarations(k) or [])
    check("the cell carries the real declarations", len(decls) >= 4, str([W.key(d) for d in decls]))

    for decl in decls:
        key = W.key(decl)
        gid, space = W.society_of(decl)
        sess = k.manager.get_session(W.client_of(decl))
        soc = SocietyConcept(sess)
        print("\n  ── %s  (as %s) ──" % (key, W.client_of(decl)))
        # what the PRIVATE path answered, today
        priv_key = soc._society_key(soc._group_engine(gid), gid, space)
        priv_casts = soc._declared_casts(gid, space)
        check("[%s] `society_key(gid, space)` answers what `_group_engine`+`_society_key` did" % key,
              soc.society_key(gid, space) == priv_key and bool(priv_key), str(priv_key)[:16])
        check("[%s] `declared_casts(gid, space)` answers what `_declared_casts` did" % key,
              soc.declared_casts(gid, space) == priv_casts and bool(priv_casts), str(priv_casts)[:80])
        check("[%s] a space that does not exist reads \"\" — never raises" % key,
              soc.society_key(gid, "no_such_space") == "")
        # the fourth site: may the programme client use the PUBLIC seal?
        ch = ChrononConcept(sess)
        ge = ch._group_engine(gid)
        try:
            role = ch._gate_seal(ge, ge.resolve_alias(ch._society_alias(gid, space)))
        except Exception as exc:                   # noqa: BLE001 — the refusal IS the finding
            role = "REFUSED: %s" % exc
        check("[%s] the programme client passes the PUBLIC `chronon.seal` gate (as %s), so "
              "replacing the private `_mint` changes no authority" % (key, role),
              role in ("chairman", "scribe", "admin"), role)

    print("\n  ── fail-closed for a caller outside the group ──")
    k.dispatch({"jsonrpc": "2.0", "method": "user.add",
                "params": {"session_token": "admin",
                           "data": {"client_id": "outsider", "role": "user",
                                    "passphrase_hash": "0" * 64}}, "id": "u"}, "local")
    outsider = k.manager.get_session("outsider")
    gid, space = W.society_of(decls[0])
    if outsider is not None:
        o = SocietyConcept(outsider)
        check("a session that is not a member reads \"\" and [] — the same fail-closed answer the "
              "private path gave by raising, without the exception",
              o.society_key(gid, space) == "" and o.declared_casts(gid, space) == [])
    else:
        check("an outsider session could be made for the fail-closed check", False, "no session")

    print("\n  ── they are READS, not new operations ──")
    for name in ("society_key", "declared_casts"):
        check("`society.%s` is not registered as an RPC op (a Python read for another Concept "
              "Model, like the private it replaces)" % name.replace("_", "."),
              name not in (SocietyConcept.CONCEPT_METHODS or {})
              and not any((v or {}).get("op") == name
                          for v in (SocietyConcept.CONCEPT_METHODS or {}).values()))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — `SocietyConcept.society_key` and `.declared_casts` answer exactly what the "
          "private calls answered, fail closed for an outsider, and every programme client passes "
          "the public `chronon.seal` gate, so the station can drop all seven private reaches "
          "without changing what it may do.")
    sys.exit(0)


if __name__ == "__main__":
    main()
