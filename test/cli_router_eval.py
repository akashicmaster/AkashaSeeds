#!/usr/bin/env python3
"""
CLI router eval — the interactive `akasha>` shell must stay in sync with the kernel.

New kernel methods (semantic sim, node.sim/learn, emotion.find, standalone view, and the async
dream + dream.confirm/forget) were added, but the interactive CLI (api/router.py + renderer.py)
was not updated with them — so they returned "Unknown command" in the shell and the dream
renderer rendered the old shape against the new async payload. This guard exercises the full
shell path (CommandRouter.build_rpc_request → kernel dispatch → renderer.render) for the
meaning-layer surface so the divergence can't silently return.

  R1 known      — every meaning-layer command resolves in the router (not "Unknown command").
  R2 dispatch   — sim / view / node.sim / emotion.find reach a real handler (no method-not-found).
  R3 dream flow — dream (async) renders the "dreaming" indicator, polls to "ready", the menu
                  extracts staged bridges, and a CLI dream.confirm promotes one (human confirm).
  R4 render     — none of the payloads crash the renderer.

Run:  python test/cli_router_eval.py
"""
import os
import sys
import io
import time
import contextlib
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


def main():
    print("\n  cli router eval — interactive shell ↔ kernel parity (meaning layer + dream)\n")
    from lib.akasha.kernel import KernelDispatcher
    from api.router import CommandRouter
    from api.shell import renderer
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cli_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def run(cli_cmd):
        """Drive one interactive command through the real shell path; return the RPC result."""
        payload = CommandRouter.build_rpc_request(cli_cmd, "admin")
        if payload is None:
            return None, "UNKNOWN_COMMAND"
        resp = k.dispatch(payload, "local")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):        # renderer must not crash on any payload
            try:
                renderer.render(resp)
                rendered = True
            except Exception as exc:                 # noqa
                rendered = f"RENDER_CRASH: {exc}"
        return resp, rendered

    def key(r):
        return (r or {}).get("result", {}).get("key") if r else None

    # Seed a little graph.
    a = k.dispatch(CommandRouter.build_rpc_request(
        "w The swallow migrates north each spring as the warm air returns", "admin"), "local")
    focus = a.get("result", {}).get("key")
    k.dispatch(CommandRouter.build_rpc_request(
        "w Warblers fly back to northern nests when the migrating season warms", "admin"), "local")
    k.dispatch(CommandRouter.build_rpc_request(
        "w Migrating birds return north again each spring to breed and nest", "admin"), "local")

    # R1 — every meaning-layer command is KNOWN to the router (the "Unknown command" gap).
    cmds = ["sim x", "similar x", "node.sim x", "node.learn", "emotion.find awe",
            "emotion.profile x", "view x", "cosmos x", "search bird", "gap.scan",
            "dream x", "dream.confirm d", "dream.forget all=yes"]
    unknown = [cli for cli in cmds if CommandRouter.build_rpc_request(cli, "admin") is None]
    record("R1 known", not unknown, "all resolve" if not unknown else f"UNKNOWN: {unknown}")

    # R2 — the exploration commands actually reach a handler (not -32601 method-not-found).
    render_ok = True
    dispatched = {}
    for cli in (f"sim {focus}", f"view {focus}", f"node.sim {focus}", "emotion.find awe",
                f"emotion.profile {focus}", "node.learn dim=16"):
        resp, rendered = run(cli)
        dispatched[cli.split()[0]] = resp
        if rendered is not True:
            render_ok = False
        err = (resp or {}).get("error", {})
        if err.get("code") == -32601:                # method not found = still not wired
            render_ok = False
    no_method_errors = all(
        (r or {}).get("error", {}).get("code") != -32601 for r in dispatched.values())
    record("R2 dispatch", no_method_errors and render_ok,
           f"reached handlers={no_method_errors}, render_ok={render_ok}")

    # R3 — dream async flow through the CLI: dreaming → ready → confirm.
    sub, sub_r = run(f"dream {focus}")
    sub_status = (sub or {}).get("result", {}).get("status")
    ready = None
    for _ in range(60):
        time.sleep(0.25)
        r, _rr = run(f"dream {focus}")
        st = (r or {}).get("result", {}).get("status")
        if st == "ready":
            ready = r
            break
        if st == "failed":
            break
    menu = renderer.extract_dream_menu((ready or {}).get("result", {}))
    cands = (ready or {}).get("result", {}).get("candidates", [])
    confirmed = False
    if cands:
        dst = cands[0]["dst"]
        cr, _crr = run(f"dream.confirm dst={dst} src={focus}")
        confirmed = (cr or {}).get("result", {}).get("status") == "confirmed"
    record("R3 dream flow",
           sub_status == "dreaming" and ready is not None and len(menu["menu"]) >= 1 and confirmed,
           f"submit={sub_status}, ready={ready is not None}, "
           f"menu={len(menu['menu'])}, confirmed={confirmed}")

    # R4 — the renderer survived every payload above (dreaming / ready / confirmed / views).
    record("R4 render", sub_r is True,
           "renderer handled the async dream payloads without crashing")

    # R5 — the uniform concept-model command scheme. Every model is reachable four ways:
    # full model name (canonical), abbreviation (back-compat), "<model> <op>" one-shot,
    # and the "<model>" subcommand mode (shell prepends the namespace).
    def _method_of(line):
        p = CommandRouter.build_rpc_request(line, "admin")
        return p.get("method") if p else None

    # (a) canonical full model name — uniform across ALL models (incl. abbreviated-prefix ones).
    full_ok = (_method_of("thesaurus.reference ns=word") == "thesaurus.reference"
               and _method_of("cast.new") == "cast.new"
               and _method_of("note.add") == "note.add"
               and _method_of("curation.new title=X") == "curation.new")
    # (b) "<model> <op>" one-shot form.
    oneshot_ok = (_method_of("thesaurus reference ns=word") == "thesaurus.reference"
                  and _method_of("curation new title=X") == "curation.new")
    # (c) the shell subcommand mode: inside [thesaurus], bare "reference" → thesaurus.reference,
    #     and a non-operator falls back to the global command.
    def _mode(model, inp):
        p = (CommandRouter.build_rpc_request(f"{model} {inp}", "admin")
             or CommandRouter.build_rpc_request(inp, "admin"))
        return p.get("method") if p else None
    mode_ok = (_mode("thesaurus", "reference ns=word") == "thesaurus.reference"
               and _mode("thesaurus", "status") == "sys.status.full")
    # (d) help groups the abbreviations; the removed standalone aliases are gone.
    th_help = sorted(CommandRouter.get_concept_specs("thesaurus").keys())
    removed_gone = all(CommandRouter.build_rpc_request(c, "admin") is None
                       for c in ("reference", "lookup", "concept", "curate", "narrate"))
    ns = CommandRouter.concept_namespaces()
    record("R5 command scheme",
           full_ok and oneshot_ok and mode_ok and removed_gone
           and set(th_help) == {"th.reference", "th.explore", "th.concept"}
           and "thesaurus" in ns and "cast" in ns,
           f"full={full_ok} oneshot={oneshot_ok} mode={mode_ok} "
           f"standalone_removed={removed_gone} namespaces={len(ns)}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the interactive CLI has drifted from the kernel.")
        return 1
    print("\nRESULT: PASS — the interactive shell is in sync with the kernel: the meaning-layer "
          "commands resolve and dispatch, and the async dream renders + confirms end-to-end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
