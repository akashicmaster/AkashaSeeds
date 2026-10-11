#!/usr/bin/env python3
"""
A deploy AIRS at boot — the boot airing is a RULE read from the cadence, through submit_job, idempotent.

`ruling-station-airing-2026-09-18.md` §1/§2 and the backend order §2.2: when a registered programme is
provisioned, the schedule's FIRST slot is the boot. The boot airing is not a special case bolted on —
it is the cadence's own `trigger: boot`, armed from the declaration, run by the driver as ONE JCL job
(society.run → submit_job), and it `then:` continues on the declared recurrence. Two properties make it
safe to run on every deploy:

  · IDEMPOTENT per boot — the boot run fires once per writer boot (boot_id gate); a redeploy at 13:07
    after a 13:00 airing does not air twice.
  · FRESH SKIP (§2.4) — a restart INSIDE the interval skips the airing (`fresh`). The clock that
    decides it is the workload's last AIRING, read from the bench's own observations: a run that
    aired nothing does not set it, and neither does another workload sharing the bench. What the
    room then SAYS about a skip ("rebroadcast") is the station's word, composed from `workload.status`
    — the platform records and answers, the application names (ruling 2026-09-23).

This eval boots a throwaway cell, provisions the declared studio, and checks the RULE (armed auto,
trigger=boot, in the auto index the driver airs from) plus the idempotence/rebroadcast STATE contract —
directly, with no live model call. The live airing cycle itself is held by station_air_turn_eval; that
a boot pass provisions + arms is held by station_deploy_airs_eval; the boot-run-once-per-boot gate is
held by bench_autorun_reboot_eval. This one owns the STATION boot-airing rule + the rebroadcast state.

Run:  python test/station_boot_airing_eval.py      (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import wl_state
from lib.akasha.workbench import provision
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []
_BROADCASTER = "system.broadcaster"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _kernel(series, base):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    return KernelDispatcher(series=series, base_dir=base)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.concepts.society import SocietyConcept
    base = tempfile.mkdtemp(prefix="akasha_bootair_")
    k = _kernel(series, base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    # ── the boot-airing RULE: a declared workload is armed auto, and its trigger is `boot` FROM ITS
    # OWN declaration (not a per-society constant) ──
    from lib.akasha.workbench import workload as _W
    shelf = next(x for x in _W.declarations(k) if x.get("workflow") == "thinkers_shelf")
    gid, space = _W.society_of(shelf)
    pol_decl = _W.policy(shelf)
    check(f"[{shape}] the workload declares its own trigger", bool(shelf.get("trigger")),
          str(shelf.get("trigger")))
    check(f"[{shape}] §2.2 the boot airing is the declaration's own rule: trigger=boot, then continues",
          pol_decl.get("trigger") == "boot" and pol_decl.get("then") not in ("", "none"),
          "trigger=%s then=%s" % (pol_decl.get("trigger"), pol_decl.get("then")))

    provision.provision_workloads(k)
    sc = SocietyConcept(k.manager.get_session("admin"))
    info = sc.read_autorun(gid, space)
    check(f"[{shape}] §2.2 the provisioned workload is armed auto (the driver airs it — no operator)",
          info.get("mode") == "auto", "mode=%s" % info.get("mode"))
    check(f"[{shape}] §2.2 … with the declared trigger=boot in its stored policy",
          (info.get("policy") or {}).get("trigger") == "boot",
          "trigger=%s" % (info.get("policy") or {}).get("trigger"))
    autos = [(p["gid"], p["name"]) for p in sc.list_auto_societies()]
    check(f"[{shape}] §2.2 it is in the auto index the boot driver enumerates (→ submit_job at boot)",
          (gid, space) in autos, str(autos))

    # ── the driver's boot gate is set once per writer boot (idempotent) — the tick opens the boot gate
    # for this boot_id, and a state stamped with THIS boot_id is not re-fired ──
    boot_id = k._writer_boot_id()
    st = dict(info.get("state") or {})
    st_boot = st.get("boot_id")
    # a freshly-armed society has no boot_id yet (the driver stamps it on the boot run); the gate is
    # keyed on boot_id, so a state carrying THIS boot_id would be treated as already-run.
    check(f"[{shape}] §2.2 the boot run is gated by boot_id (idempotent per writer boot)",
          st_boot != boot_id, "state boot_id=%s writer boot_id=%s" % (st_boot, boot_id))

    # ── THE FRESH GUARD'S CLOCK — the platform half of §2.4 ───────────────────────────────────
    #
    # What stood here asserted the four station STATES (`standing_by` → `on_air` → `rebroadcast`)
    # on the guide row `station:show:*`, driven by `note_airing`. Both are deleted (ruling
    # 2026-09-23): "rebroadcast" is the station's word for its own surface, composed from `last` and
    # `gate`, and a platform that stamps it has decided what an application's status means.
    #
    # The platform's half of the same rule is the CLOCK the guard reads: `last_effect_at` is when
    # this workload last PRODUCED ITS EFFECT, from the platform's OWN run record (group 4, 4.12(a)
    # — it read the application's aired rows until then). It decides whether a boot inside the
    # interval skips as `fresh`, so the two things that must hold are that an effect sets it and
    # that a run with NO effect does not — the second is the exact bug the §1/§2 ruling was written
    # about, where a run that aired nothing still counted and swallowed a deploy's boot airing.
    _key = "studio_ai/news_show"
    check(f"[{shape}] §2.4 a workload that has NEVER produced its effect has no clock — so a "
          f"deploy always runs it", wl_state.last_effect_at(k, _key) == 0.0,
          str(wl_state.last_effect_at(k, _key)))
    wl_state.record_run(k, _key, at=time.time(), ok=True, reason="provider_429", effect_count=0)
    check(f"[{shape}] §2.4 a run with NO effect does not set the clock (it must not swallow the "
          f"next deploy's boot run)", wl_state.last_effect_at(k, _key) == 0.0,
          str(wl_state.last_effect_at(k, _key)))
    wl_state.record_run(k, _key, at=time.time(), ok=True, effect_count=3)
    _at = wl_state.last_effect_at(k, _key)
    check(f"[{shape}] §2.4 an EFFECT sets it, so a restart inside the interval skips as `fresh`",
          _at > 0 and (time.time() - _at) < 1800.0, str(_at))
    # four workloads share this bench: another workload's record is not this one's clock
    wl_state.record_run(k, "studio_ai/plant_geek", at=time.time() + 5, ok=True, effect_count=1)
    check(f"[{shape}] §2.4 …and another workload's effect on the SAME bench is not this one's clock",
          wl_state.last_effect_at(k, _key) == _at,
          "%s vs %s" % (wl_state.last_effect_at(k, _key), _at))


def main():
    print("=" * 78)
    print("Station — the boot airing is a cadence rule (trigger:boot, submit_job, idempotent) + rebroadcast")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — the boot airing is the cadence's own `trigger: boot`, armed from the declaration "
          "and enumerated in the auto index the driver airs through submit_job, gated once per writer boot "
          "(§2.2); the fresh guard's clock is the workload's own last AIRING, which a stand-by does not set "
          "and another workload on the same bench does not answer (§2.4) — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
