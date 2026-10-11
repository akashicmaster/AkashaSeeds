#!/usr/bin/env python3
"""
TRANSPORT TRUST, TESTED AS BEHAVIOUR — the invariant nothing was actually checking.

`check_invariants.py` held this one by GREPPING kernel.py for the source text of two constants.
When the kernel was cut from eighteen thousand lines to three, the constants moved to
`lib/akasha/api/trust.py` and both anchors went red with

    FAIL [A] transport trust constants:    anchor NOT found in lib/akasha/kernel.py
    FAIL [A] trusted transports frozenset: anchor NOT found in lib/akasha/kernel.py

reporting "the invariant may have regressed" when nothing had regressed at all. The anchors are
re-pointed now, but that is the smaller half of the repair: a guard that greps for a string goes
blind the day the string moves, and it can never have told you whether the GATE works — only
whether a line of source exists. Probing the deployed cell showed the gate was in fact closed the
whole time, which is exactly the gap: the thing that was true was true by luck of nobody touching
it, not by anything checking.

So the property is held here as behaviour, on a real dispatcher, in a temporary cell:

  1. over TRUST_NETWORK a bare `client_id` cannot assert a privileged identity — it is refused, or
     it resolves to an anonymous guest, and it is NEVER admin
  2. a client that SUPPLIES its own `transport_trust` in the payload is ignored: trust is a
     property of the server-side binding, and a client cannot name its own
  3. system identities (`system.*`) are unreachable over the network
  4. `kernel.genesis_rite` is local/internal only
  5. TRUST_LOCAL does accept a bare id — the OS process boundary is the gate there, and a rule
     that refused everything would pass 1–4 while making the console useless
  6. every module that keeps its OWN copy of the trust constants agrees with the contract. Three
     do (`api/portals/mcp.py`, `api/portals/cell_ipc.py`, `lib/harmonia/supervisor.py`), each
     deliberately, to avoid importing the kernel on a light path — and two of them say they are
     "kept in sync with lib/akasha/kernel.py", which has not held them since the cut. Kept in sync
     by a comment is not kept in sync.

Run:  python test/transport_trust_eval.py     (exit 0 = all pass)
"""
import ast
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.api.trust import (TRUST_NETWORK, TRUST_LOCAL,           # noqa: E402
                                  TRUST_INTERNAL, TRUSTED_TRANSPORTS)

# The modules that keep their own copy, and why they are allowed to.
_COPIES = {
    "api/portals/mcp.py": "the light MCP path must not import the kernel",
    "api/portals/cell_ipc.py": "the light IPC client path must not import the kernel",
    "lib/harmonia/supervisor.py": "the supervisor stamps trust without the kernel",
}
_NAMES = ("TRUST_NETWORK", "TRUST_LOCAL", "TRUST_INTERNAL")
_CONTRACT = {"TRUST_NETWORK": TRUST_NETWORK, "TRUST_LOCAL": TRUST_LOCAL,
             "TRUST_INTERNAL": TRUST_INTERNAL}

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _call(k, method, params, trust):
    """One dispatch, and the answer reduced to what this eval asks about: did it refuse, and if it
    did not, whose identity did it run as."""
    res = k.dispatch({"jsonrpc": "2.0", "method": method, "params": params, "id": "t"},
                     transport_trust=trust)
    err = (res or {}).get("error") or None
    return err, (res or {}).get("result")


def _identity_of(result):
    """Whatever shape the read answers in, find the identity it ran as. Deliberately generous:
    the eval must not pass merely because it looked in the wrong field."""
    if not isinstance(result, dict):
        return ""
    for k in ("client_id", "identity", "who", "user"):
        v = result.get(k)
        if isinstance(v, str) and v:
            return v
    ident = result.get("identity")
    if isinstance(ident, dict):
        for k in ("client_id", "id", "name"):
            v = ident.get(k)
            if isinstance(v, str) and v:
                return v
    return ""


def main():
    print("\n  ── the constants, and the copies of them ──")
    check("the contract names the three levels and the trusted pair",
          TRUST_NETWORK == "network" and TRUST_LOCAL == "local"
          and TRUST_INTERNAL == "internal"
          and TRUSTED_TRANSPORTS == frozenset({TRUST_LOCAL, TRUST_INTERNAL}),
          "network is NOT trusted: %s" % (TRUST_NETWORK not in TRUSTED_TRANSPORTS))
    check("… and the network is not in it — the safe default is the untrusted one",
          TRUST_NETWORK not in TRUSTED_TRANSPORTS)

    for rel, why in _COPIES.items():
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            check("%s is where the map says it is" % rel, False, "missing")
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        got = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in _NAMES:
                        got[t.id] = node.value.value
        bad = {n: (v, _CONTRACT[n]) for n, v in got.items() if v != _CONTRACT[n]}
        check("%s's own copy agrees with the contract (%s)" % (rel, why),
              bool(got) and not bad, "copies=%s bad=%s" % (sorted(got), bad or "none"))

    print("\n  ── the gate, on a real dispatcher ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_trust_")
    k = KernelDispatcher(series="seeds", base_dir=base)
    # The operator has to EXIST before "can a bare admin id be asserted" means anything: on a
    # fresh cell every answer is "identity unknown", which would let checks 1-4 pass for the wrong
    # reason. The rite is performed over TRUST_LOCAL, which is also the positive half of check 4 —
    # it is refused over the network and accepted from the console.
    g = k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                    "params": {"session_token": "admin",
                               "data": {"user_name": "admin",
                                        "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                    "id": "g"}, TRUST_LOCAL)
    check("the genesis rite IS accepted from the local console",
          not (g or {}).get("error"), str(((g or {}).get("error") or {}).get("message"))[:60])

    # 1 — a bare privileged id over the network is never that identity
    err, res = _call(k, "sys.session.state", {"client_id": "admin"}, TRUST_NETWORK)
    who = _identity_of(res)
    check("a bare `admin` over the NETWORK is refused, or is anyone but admin",
          bool(err) or who != "admin", "err=%s who=%r" % (bool(err), who))

    # 2 — the client cannot name its own trust
    err2, res2 = _call(k, "sys.session.state",
                       {"client_id": "admin", "transport_trust": "local"}, TRUST_NETWORK)
    who2 = _identity_of(res2)
    check("a client-supplied `transport_trust: local` is IGNORED — trust is the server's",
          bool(err2) or who2 != "admin", "err=%s who=%r" % (bool(err2), who2))
    check("… and it answers exactly as the same call without it",
          bool(err) == bool(err2) and who == who2,
          "with=%r without=%r" % ((bool(err2), who2), (bool(err), who)))

    # 3 — system identities are internal-only
    for sysid in ("system.librarian", "system.weaver"):
        e, r = _call(k, "sys.session.state", {"client_id": sysid}, TRUST_NETWORK)
        check("`%s` is unreachable over the network" % sysid,
              bool(e) or _identity_of(r) != sysid, "err=%s who=%r" % (bool(e), _identity_of(r)))

    # 4 — the land-grab is local/internal only
    e, _ = _call(k, "kernel.genesis_rite", {"client_id": "admin"}, TRUST_NETWORK)
    check("`kernel.genesis_rite` is refused over the network",
          bool(e), str((e or {}).get("message"))[:60])

    # 5 — and the console still works, or 1-4 pass by refusing everything
    e, r = _call(k, "sys.session.state", {"client_id": "admin"}, TRUST_LOCAL)
    check("a bare `admin` on the LOCAL console is accepted — the rule is not 'refuse everything'",
          not e, str((e or {}).get("message"))[:60])
    # and the SAME id, now that it exists, is still refused over the network: the refusal above
    # was the trust gate, not an account that happened to be missing
    e2, r2 = _call(k, "sys.session.state", {"client_id": "admin"}, TRUST_NETWORK)
    check("… while the same existing id is STILL refused over the network",
          bool(e2) or _identity_of(r2) != "admin",
          "err=%s who=%r" % (bool(e2), _identity_of(r2)))

    # 6 — a write is a write: the network default must not let one through unsigned
    e, _ = _call(k, "w", {"client_id": "admin", "content": "trust probe"}, TRUST_NETWORK)
    check("an unsigned WRITE over the network is refused", bool(e),
          str((e or {}).get("message"))[:60])

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — transport trust is held as BEHAVIOUR, not as a string in a file: over "
          "the network a bare client_id is never a privileged identity, a client-supplied trust "
          "level is ignored, system identities and the genesis rite are unreachable and an "
          "unsigned write is refused — while the local console still works, so none of it passes "
          "by refusing everything. Every module keeping its own copy of the constants is checked "
          "against the contract rather than against a comment.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
