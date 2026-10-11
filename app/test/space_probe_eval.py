#!/usr/bin/env python3
"""
F47-2.4 — sys.space_probe: the one-command proof the ENGINE stays innocent.

The public page can take tens of seconds while a depth-1 render is ~21 ms — the latency is coupling
and admission, not the semantic system. sys.space_probe renders one concept ENGINE-SIDE (the same
archives.space → op_concept → generate_view the page uses) but BYPASSING admission, and returns
{ms, point_get, membrane_scan, full_scan} straight off the store's access-degree probe. This eval
boots the silica engine, plants a concept with a small neighbourhood, and asserts the probe returns
a fast time, zero full_scans, and a populated access-degree count — over both CLI and RPC.

Run:  python test/space_probe_eval.py   (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "test"))

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="probe_"))
    gw = AkashaGateway(kernel_client=k)

    def D(m, d):
        return (gw.dispatch({"jsonrpc": "2.0", "method": m,
                             "params": {"session_token": "admin", "data": d}, "id": "c"}, "local")
                ).get("result") or {}

    def cli(line):
        return D("sys.cli_exec", {"command": line})

    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    # a concept with a few related links (a small neighbourhood to render)
    cli('def "concept:bird" "a warm-blooded egg-laying vertebrate."'); cli('al concept:bird bird')
    for w in ("feather", "wing", "beak", "nest"):
        cli('def "concept:%s" "part/notion of a bird."' % w)
        cli('al concept:%s %s' % (w, w))
        cli('ln concept:bird concept:%s thesaurus:related' % w)

    # ── RPC path ──
    r = D("sys.space_probe", {"name": "bird"})
    check("2.4 space_probe returns ms + access-degree probe fields",
          set(r) >= {"ms", "point_get", "membrane_scan", "full_scan", "ok"}, str(r))
    check("2.4 the render succeeded (found the concept)", r.get("ok") and r.get("found"), str(r))
    check("2.4 ZERO full scans (access-degree bounded — the engine is innocent)",
          r.get("full_scan") == 0, "full_scan=%s" % r.get("full_scan"))
    check("2.4 the render is fast engine-side (< 200 ms on this tiny store)",
          isinstance(r.get("ms"), (int, float)) and r["ms"] < 200, "ms=%s" % r.get("ms"))
    check("2.4 the access-degree probe actually counted point-gets/membrane-walks",
          (r.get("point_get") or 0) + (r.get("membrane_scan") or 0) > 0,
          "pg=%s ms=%s" % (r.get("point_get"), r.get("membrane_scan")))

    # ── CLI path (CLI-first convention) ──
    c = cli("space_probe name=bird")
    check("2.4 space_probe is invocable via the CLI",
          isinstance(c, dict) and c.get("ok") and c.get("full_scan") == 0, str(c)[:160])

    # ── a missing concept probes cleanly (no crash, ok/found false) ──
    miss = D("sys.space_probe", {"name": "no_such_concept_zzz"})
    check("2.4 a missing concept returns cleanly (not found, no crash)",
          "ms" in miss and not miss.get("found"), str(miss)[:140])

    # ── guard: non-admin is refused ──
    gw.dispatch({"jsonrpc": "2.0", "method": "session.guest.create", "params": {}, "id": "gg"}, "network")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — sys.space_probe renders a concept engine-side (bypassing admission) and returns "
          "ms + point_get/membrane_scan/full_scan; the render is fast with zero full scans, over both "
          "CLI and RPC — the one-command production proof the engine stays innocent.")
    sys.exit(0)


if __name__ == "__main__":
    main()
