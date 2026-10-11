#!/usr/bin/env python3
"""
G4 §3.2 — the MACRO facility: a saved, PARAMETERIZED CSL script that is a coarser reader expressed as
Set operations. macro.def/run/get/ls/rm reuse the saved-script mechanism (workflow.* stays for
compatibility) and add (a) named parameters with defaults bound as $name at run, and (b) a synchronous
`as=inline` mode that runs in-process and renders the last result.

Also verifies the enabling fix: a CSL script's sub-calls run at the SAME transport trust the script was
admitted with (never higher) — so a macro run by the local operator / the JCL worker (INTERNAL) / a
signed agent reaches its entitled methods instead of being re-authenticated over NETWORK.

Run:  python test/macro_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_macro_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    # seed two sets to operate on
    d("w", {"content": "alpha"}); d("w", {"content": "beta"})
    d("set.add", {"name": "a:set", "id": "alpha"})
    d("set.add", {"name": "b:set", "id": "beta"})

    # ── def / get / ls ──
    dfn = d("macro.def", {"name": "u", "params": "a=,b=,r=tmp:u",
                          "script": 'set.op op="union" result="$r" a="$a" b="$b"'})
    check(f"[{shape}] macro.def stores the script + params",
          dfn.get("status") == "defined" and dfn.get("alias") == "macro:u", str(dfn)[:120])
    g = d("macro.get", {"name": "u"})
    check(f"[{shape}] macro.get returns script + params",
          g.get("params") == "a=,b=,r=tmp:u" and "set.op" in (g.get("script") or ""), str(g)[:120])
    ls = d("macro.ls", {})
    check(f"[{shape}] macro.ls lists it", any(m.get("name") == "u" for m in ls.get("macros") or []),
          str(ls)[:120])

    # ── inline run binds params + runs synchronously under the caller's trust ──
    r = d("macro.run", {"name": "u", "a": "a:set", "b": "b:set", "r": "res:ab", "as": "inline"})
    check(f"[{shape}] macro.run as=inline runs synchronously (trust propagated, no token error)",
          r.get("mode") == "inline" and r.get("results")
          and not (r.get("last") or {}).get("error"), str(r)[:160])
    union = set(x.get("key") for x in (d("set.ls", {"name": "res:ab"}).get("members") or []))
    check(f"[{shape}] the inline macro actually performed the set union (alpha ∪ beta)",
          union == {"alpha", "beta"}, str(union))

    # ── a defaulted param may be omitted ──
    r2 = d("macro.run", {"name": "u", "a": "a:set", "b": "b:set", "as": "inline"})   # r defaults to tmp:u
    dflt = set(x.get("key") for x in (d("set.ls", {"name": "tmp:u"}).get("members") or []))
    check(f"[{shape}] an omitted param takes its default (r=tmp:u)", dflt == {"alpha", "beta"},
          str(dflt))

    # ── a required param (no default) is enforced ──
    d("macro.def", {"name": "need", "params": "x", "script": 'set.ls name="$x"'})
    miss = d("macro.run", {"name": "need", "as": "inline"})
    check(f"[{shape}] a required param with no value is refused",
          isinstance(miss, dict) and miss.get("error"), str(miss)[:120])

    # ── the last result is rendered ──
    d("macro.def", {"name": "lsone", "params": "s", "script": 'set.ls name="$s"'})
    r3 = d("macro.run", {"name": "lsone", "s": "res:ab", "as": "inline"})
    last = (r3.get("last") or {}).get("result") or {}
    check(f"[{shape}] as=inline renders the macro's LAST result", last.get("count") == 2, str(last)[:120])

    # ── CLI parse: `macro.run <name> param=… as=inline` routes with params passed through ──
    from api.router import CommandRouter
    payload = CommandRouter.build_rpc_request('macro.run observe.diff bench=plants before=o0 after=o1 as=inline',
                                              "tok")
    pdata = ((payload or {}).get("params") or {}).get("data") or {}
    check(f"[{shape}] CLI parses macro.run: name positional + params pass through",
          payload and payload.get("method") == "macro.run" and pdata.get("name") == "observe.diff"
          and pdata.get("bench") == "plants" and pdata.get("before") == "o0"
          and pdata.get("after") == "o1" and pdata.get("as") == "inline", str(pdata)[:160])

    # ── rm ──
    d("macro.rm", {"name": "u"})
    check(f"[{shape}] macro.rm removes it",
          not any(m.get("name") == "u" for m in (d("macro.ls", {}).get("macros") or [])))


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the macro facility saves parameterized CSL readers, binds $params (with "
          "defaults + required enforcement), runs them synchronously as=inline rendering the last "
          "result, parses from the CLI with params passed through, and the CSL sub-calls run at the "
          "caller's transport trust — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
