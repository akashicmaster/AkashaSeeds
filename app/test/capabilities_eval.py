#!/usr/bin/env python3
"""
B5 §A7 — capabilities: OFFERED ≠ GRANTED.

Provisioning declares, per society + role, the capabilities a role is OFFERED from the workload
declaration's grants — `set:cap:offered:<society>:<role>`, one `cap:<name>@<fp8>` per grant (fp8 = the running seed's
content_fingerprint[:8], the P3 identity rule). `cap.ls role= context=` reports `offered` to anyone (a
guest on a public bench) and `granted` only to a holder / privileged caller. A capability whose op is
declared `effectful` reads `effectful=true`; a member minted under an older fingerprint is kept and
flagged `stale_build` (never removed).

This eval drives it on BOTH cell shapes:
  • provisioning writes the offered Set with the running fingerprint;
  • a guest reads `offered` and no `granted`; the admin reads both;
  • a capability in an effectful family reads effectful=true, an operator: capability false;
  • a re-provision on a NEW fingerprint adds new members and flags the old ones stale_build.

Run:  python app/test/capabilities_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import provision
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "test"))
_fails = []
GID = "plants-lab"
SOC = "plants-vision"
BENCH = "plants-vision"

_GRANTS = {
    "Botanist": ["operator:dataset", "operator:feature", "operator:train",
                 "operator:evaluate", "operator:promote", "decide"],
    "Broadcaster": ["society:say", "station:poll", "x_broadcast:post"],   # effectful families
}


def _decl():
    """A DECLARED workload carrying the grants — provisioning has one path (the purge order removed
    the legacy bench_*.json / auto_exec.json pass), so the offered capabilities come from a
    declaration's `grants`. Shaped on the shipped lab declaration, narrowed to what this eval needs."""
    import json as _json
    with open(os.path.join(ROOT, "app", "config", "workbench", "workloads", "plants_vision.json"),
              encoding="utf-8") as f:
        d = _json.load(f)
    d.pop("sweeps", None)
    d.update(_file="eval_capabilities.json", workflow="capev", workflows=["capev"],
             requires=[], grants=dict(_GRANTS),
             roles={"Botanist": {"identity": "the lab's operator"},
                    "Broadcaster": {"identity": "the voice"}})
    d["space"] = dict(d["space"], client="lab:eval_capabilities")
    return d


def _provision(k):
    from lib.akasha.workbench import workload_provision as WP, workload as W
    tpl = os.path.join(tempfile.mkdtemp(prefix="capev_tpl_"), "capev.ak")
    with open(tpl, "w", encoding="utf-8") as f:
        f.write("# eval\nw content=capev\n")
    real = WP.templates_of
    WP.templates_of = lambda dc: ([(W.branch_of(dc), tpl)] if dc.get("_file") == "eval_capabilities.json"
                                  else real(dc))
    try:
        k._workload_decl_cache = [_decl()]
        reps = provision.provision_workloads(k)
    finally:
        WP.templates_of = real
    return reps


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_cap_"))
    k._bfp_cache = "aaaa1111buildfp"          # pin the fingerprint so fp8 is deterministic
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    gr = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                     "params": {"data": {}}, "id": "gg"}, "network")
    gtok = (gr.get("result") or {}).get("binding_key")

    def g(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": gtok, "data": data}, "id": "gq"}, "network")
        return r if "error" in r else (r.get("result") or {})

    a("world.genesis", {})
    reps = _provision(k)
    check(f"[{shape}] (the declared workload provisioned)",
          any(r.get("status") == "provisioned" for r in reps), str(reps)[:160])

    # ── provisioning wrote the offered Set with the running fingerprint (6 for Botanist) ──
    am = a("cap.ls", {"role": "Botanist", "context": BENCH})
    _off = am.get("offered") or []
    check(f"[{shape}] cap.ls offers the Botanist's six capabilities at the running fingerprint",
          len(_off) == 6 and all(o.get("fingerprint") == "aaaa1111" for o in _off),
          f"n={len(_off)} fps={sorted({o.get('fingerprint') for o in _off})}")
    check(f"[{shape}] none of the fresh-build capabilities is stale",
          all(not o.get("stale_build") for o in _off), str([o.get('stale_build') for o in _off]))

    # ── guest reads offered, NOT granted; admin reads both ──
    gm = g("cap.ls", {"role": "Botanist", "context": BENCH})
    check(f"[{shape}] a guest reads offered and NO granted",
          (not gm.get("error")) and isinstance(gm.get("offered"), list) and "granted" not in gm,
          str(gm)[:140])
    check(f"[{shape}] the admin (privileged) reads granted alongside offered",
          isinstance(am.get("granted"), list) and len(am["granted"]) == 6, str(am.get("granted"))[:120])

    # ── effectful: society:say is effectful; operator:feature is not ──
    bm = a("cap.ls", {"role": "Broadcaster", "context": BENCH})
    _bo = {o.get("name"): o for o in (bm.get("offered") or [])}
    _say = _bo.get("society:say", {})
    check(f"[{shape}] an effectful-family capability (society:say) reads effectful=true",
          _say.get("effectful") is True, str(_say))
    _feat = next((o for o in _off if o.get("name") == "operator:feature"), {})
    check(f"[{shape}] an operator: capability is not effectful",
          _feat.get("effectful") is False, str(_feat))
    # §3 — the broadcast station's publishing ops (station.* / x_broadcast.*) are effectful
    check(f"[{shape}] a station publishing capability (station:poll) reads effectful=true",
          _bo.get("station:poll", {}).get("effectful") is True, str(_bo.get("station:poll")))
    check(f"[{shape}] an x_broadcast publishing capability (x_broadcast:post) reads effectful=true",
          _bo.get("x_broadcast:post", {}).get("effectful") is True, str(_bo.get("x_broadcast:post")))

    # ── a re-provision on a NEW fingerprint adds new members + flags the old ones stale ──
    k._bfp_cache = "bbbb2222buildfp"
    _provision(k)
    am2 = a("cap.ls", {"role": "Botanist", "context": BENCH})
    _off2 = am2.get("offered") or []
    _fps = {o.get("fingerprint") for o in _off2}
    _stale = {o.get("fingerprint") for o in _off2 if o.get("stale_build")}
    check(f"[{shape}] a new build adds new-fingerprint members (both fps present, old flagged stale)",
          _fps == {"aaaa1111", "bbbb2222"} and _stale == {"aaaa1111"} and len(_off2) == 12,
          f"fps={sorted(_fps)} stale={sorted(_stale)} n={len(_off2)}")

    # ── B5-b — the offered Set keeps at most ONE stale generation, however many builds pass ──
    # Each build used to add a generation and retire none: `cap.ls` on the VPS carried EIGHT
    # fingerprints per capability by 09-21, seven of them dead. The previous generation stays (a
    # read taken mid-deploy still resolves it); everything older leaves the offered Set and joins a
    # validity membrane already in the past, which the nightly retention phase evicts. The atoms
    # are never deleted — they simply stop being offered.
    for _fp in ("cccc3333buildfp", "dddd4444buildfp", "eeee5555buildfp"):
        k._bfp_cache = _fp
        _provision(k)
    am3 = a("cap.ls", {"role": "Botanist", "context": BENCH})
    _off3 = am3.get("offered") or []
    _fps3 = {o.get("fingerprint") for o in _off3}
    _stale3 = {o.get("fingerprint") for o in _off3 if o.get("stale_build")}
    check(f"[{shape}] after five builds the offered Set still shows ONE current + ONE stale "
          f"generation — not one per build",
          _fps3 == {"eeee5555", "dddd4444"} and _stale3 == {"dddd4444"},
          f"fps={sorted(_fps3)} stale={sorted(_stale3)} n={len(_off3)}")
    check(f"[{shape}] …and the count stays flat across builds (no unbounded pile)",
          len(_off3) == len(_off2), f"{len(_off2)} -> {len(_off3)}")
    # the retired atoms are still READABLE — retirement is not deletion
    _gone = a("r", {"id": "cap:society:say@aaaa1111"})
    check(f"[{shape}] a retired capability atom is still readable (retired ≠ deleted)",
          bool(_gone) and "__error__" not in _gone, str(_gone)[:90])


def main():
    print("=" * 78)
    print("B5 §A7 — capabilities: offered ≠ granted, effectful, stale_build")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — provisioning declares a role's OFFERED capabilities at the running fingerprint, "
          "cap.ls reports offered to a guest and granted only to a holder, marks effectful capabilities, "
          "and flags an older build's members stale without removing them — both cell shapes.")


if __name__ == "__main__":
    main()
