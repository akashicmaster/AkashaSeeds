#!/usr/bin/env python3
"""
F54 — retire active_scope as a WRITTEN key + drop the whiteboard-local scope branch (acceptance).

F53 introduced `radius` as the preferred spelling of the traversal-depth `active_scope`, writing BOTH
keys and keeping the wb-local `wb:<name>:scope_*` branch. F54 completes the migration:
  • writers write ONLY `radius`; `active_scope` is no longer a written session key (readers keep the
    fallback one more series so pre-F54 sessions/checkpoints still resolve);
  • the whiteboard-local scope branch is retired — a board's axis/radius/time ride wb:<name>:state,
    restored into the session-global keys by wb.focus; the sys.scope.* handlers read only globals.

Run:  python test/f54_scope_retire_eval.py     (exit 0 = all pass)
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


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_f54_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def call(method, data=None):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data or {}}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    sess = k.manager.get_session("admin")

    # ── 1. sys.scope.set writes radius ONLY; active_scope session key is NOT written ──
    call("sys.scope.set", {"radius": 3, "axis": "emotion"})
    st = call("sys.session.state", {})
    check("scope.set radius=3 → session.state radius=3; the active_scope session key stays UNWRITTEN",
          st["self_directed"].get("radius") == 3 and sess.get_context("radius") == 3
          and sess.get_context("active_scope") is None, "radius=%s active_scope=%s"
          % (sess.get_context("radius"), sess.get_context("active_scope")))

    # ── 2. the `scope` alias still works but also lands in radius (not active_scope) ──
    call("sys.scope.set", {"scope": 5})
    check("scope.set scope=5 writes radius=5 (the alias is accepted; active_scope still unwritten)",
          sess.get_context("radius") == 5 and sess.get_context("active_scope") is None, "")

    # ── 3. READ fallback: a pre-F54 session (only active_scope, no radius) still resolves ──
    sess.set_context("radius", None)
    sess.set_context("active_scope", 7)                # simulate legacy state
    sg = call("sys.scope.get", {})
    check("a pre-F54 session (active_scope only) resolves via the read fallback (depth=7)",
          sg.get("active_scope") == 7 and sg.get("radius") == 7, str(sg))
    call("sys.scope.reset", {})
    check("scope.reset clears BOTH radius and the retired active_scope",
          sess.get_context("radius") is None and sess.get_context("active_scope") is None, "")

    # ── 4. whiteboard: axis/radius ride wb state and wb.focus restores them into the GLOBAL keys ──
    call("wb.new", {"name": "A"}); call("sys.scope.set", {"radius": 3, "axis": "emotion"})
    call("wb.new", {"name": "B"})
    check("a new board starts with a fresh (empty) scope in the global keys",
          sess.get_context("radius") is None and sess.get_context("active_axis") is None, "")
    call("sys.scope.set", {"radius": 7, "axis": "color"})
    fa = call("wb.focus", {"name": "A"})
    check("wb.focus A restores A's radius=3 + axis=emotion into the global keys (no wb-local branch)",
          sess.get_context("radius") == 3 and sess.get_context("active_axis") == "emotion"
          and sess.get_context("active_scope") is None, "radius=%s axis=%s"
          % (sess.get_context("radius"), sess.get_context("active_axis")))
    call("wb.focus", {"name": "B"})
    check("wb.focus B restores B's radius=7 + axis=color (per-board scope round-trips via state)",
          sess.get_context("radius") == 7 and sess.get_context("active_axis") == "color", "")
    # no wb-local scope key was ever written
    check("no whiteboard-local scope key (wb:*:scope_scope) is written anymore",
          sess.get_context("wb:A:scope_scope") is None and sess.get_context("wb:B:scope_scope") is None, "")

    # ── 5. checkpoint: save records the depth, replay restores it to `radius` (not active_scope) ──
    call("wb.focus", {"name": "A"})                    # radius=3
    call("sys.scope.set", {"radius": 4})
    call("log.new", {"name": "f54log"})
    cp = call("log.checkpoint", {"note": "f54"})
    if "error" not in cp:
        call("sys.scope.set", {"radius": 9})           # move away
        call("log.replay", {})
        check("log.replay restores the checkpoint depth into `radius` (active_scope stays unwritten)",
              sess.get_context("radius") == 4 and sess.get_context("active_scope") is None,
              "radius=%s" % sess.get_context("radius"))
    else:
        check("log.checkpoint available", False, str(cp.get("error"))[:80])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — active_scope is retired as a written key (writers write radius; the "
          "read-fallback keeps pre-F54 sessions/checkpoints resolving); the whiteboard-local scope "
          "branch is gone (a board's axis/radius/time ride wb:<name>:state, restored into the global "
          "keys by wb.focus); checkpoints save + replay through radius.")
    sys.exit(0)


if __name__ == "__main__":
    main()
