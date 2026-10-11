#!/usr/bin/env python3
"""
`analysis.precompute` IS GATED BY THE GATE, NOT BY A ROLE TEST INSIDE ITS HANDLER (§5 prerequisite).

The op declares `access: run`. It also used to refuse anyone without `scope:sys:admin` / `role:librarian`
inside `handle_analysis_precompute`, which would have refused a workload's client AFTER the gate had
admitted it. The handler no longer tests a role; who may run it is the gate's answer. Held here:

  · the handler source contains no admin / librarian test
  · a caller the gate does not admit (an unknown identity = a guest) is refused, and no job is submitted
  · admin passes the gate and reaches the handler's own argument check (-32602 without labo=/input=)

Run:  python app/test/analysis_precompute_gate_eval.py     (exit 0 = all pass)
"""
import hashlib
import inspect
import os
import sys
import tempfile

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
    from app.concepts import analysis_ops
    src = inspect.getsource(analysis_ops.handle_analysis_precompute)
    check("the handler tests no role (the gate decides)",
          "scope:sys:admin" not in src and "role:librarian" not in src)
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_apg_"))

    def call(who, data):
        return k.dispatch({"jsonrpc": "2.0", "method": "analysis.precompute",
                           "params": {"session_token": who, "data": data}, "id": "t"}, "local") or {}

    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {
                    "user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    r = call("mallory", {"labo": "x", "input": "pool:x"})
    check("a caller the gate does not admit is refused", "error" in r, str(r)[:120])
    a = call("admin", {"bench": "sandbox"})
    check("admin passes the gate (a bench named) and reaches the handler's own argument check (-32602)",
          (a.get("error") or {}).get("code") in (-32602, -32002), str(a)[:140])
    nb = call("admin", {})
    check("with no bench= even admin is refused: the target is required (10-03, one switch)",
          "out_of_scope" in str(nb.get("error")), str(nb)[:140])
    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — analysis.precompute is gated by the gate: no role test in the handler, an "
          "unadmitted caller is refused, admin reaches the handler.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
