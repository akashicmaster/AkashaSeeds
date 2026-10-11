#!/usr/bin/env python3
"""
THE PRECOMPUTE SOCIETIES RESOLVE THEIR GROUP once provisioned (VPS order A1, 11 Oct).

The VPS logged `[bench.auto] skipped reason=tripped_derive detail=Not a member of group 'precompute'.`
Provisioning is what makes `lab:analysis_precompute` / `lab:media_precompute` members of group `precompute`
(`grp.add` as admin, `workload_provision.provision`). This eval pins that: after `provision_workloads`,
  1. neither precompute workload reports a provisioning problem,
  2. both lab clients are members of group `precompute`,
  3. the driver's tripped-society derive reads both societies with no `tripped_derive` skip.
What it does NOT cover: the derive running BEFORE provisioning on a cold boot — that ordering is the
platform's (see the note of 11 Oct), not a membership the application can declare.

Run:  python app/test/precompute_group_eval.py     (exit 0 = all pass)
"""
import hashlib
import logging
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


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus09", base_dir=tempfile.mkdtemp(prefix="akasha_pg_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    from lib.akasha.workbench import autorun, provision
    rep = provision.provision_workloads(k) or []
    mine = {str(r.get("workload")): r for r in rep if "precompute" in str(r.get("workload"))}
    print("\n  ── precompute provisioning ──")
    check("both precompute workloads were provisioned", len(mine) == 2, sorted(mine))
    check("no provisioning problem on either", all(not r.get("problems") for r in mine.values()),
          str({n: r.get("problems") for n, r in mine.items()}))
    members = set()
    try:
        members = set(k.manager.iam.get_group_members("precompute") or [])
    except Exception:
        members = set(getattr(k.manager.iam, "_group_members", {}).get("precompute") or [])
    check("lab:analysis_precompute and lab:media_precompute are members of group precompute",
          {"lab:analysis_precompute", "lab:media_precompute"} <= members, sorted(members))
    root = logging.getLogger()
    cap = _Cap()
    root.addHandler(cap)
    try:
        autorun.derive_bench_tripped(k)
    finally:
        root.removeHandler(cap)
    check("the tripped-society derive skips nothing once provisioned",
          not any("tripped_derive" in ln for ln in cap.lines), str(cap.lines[:2]))
    print("\n" + ("ALL PASS" if not _fails else "FAILED: " + ", ".join(_fails)))
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
