#!/usr/bin/env python3
"""
Cell-daemon replacement decision eval — the recurring "reinstall did not replace the stale daemon" bug.

Root cause (fixed): the build handshake used `running_build and disk_build and running_build != disk`,
so a daemon that ANSWERS the socket but reports NO build (running_build falsy) was LEFT ALONE. Such a
daemon is, by construction, running code that PREDATES the build handshake (a current daemon always
advertises AKASHA_HANDSHAKE_BUILD) — i.e. strictly OLDER — yet it could never be superseded by any
git pull / reinstall, because every replace path was gated on it reporting a build it cannot report.
That made a pre-handshake writer a PERMANENT ZOMBIE that had to be killed by hand.

`_should_replace_daemon(running, disk)` is the one authoritative decision now shared by the client
(_run_cell_client) and server (--serve/--daemon) attach paths. This pins its contract.

Run:  python test/daemon_replace_eval.py     (exit 0 = all pass)
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _ping_build_returns_tuple():
    """ping_build's contract is a (status, build) tuple (F60 §4.1) — verified by source, since a live
    daemon socket is not available in this unit eval."""
    import inspect
    from api.portals import cell_ipc
    src = inspect.getsource(cell_ipc.ping_build)
    return '("silent", None)' in src and '("no-build", None)' in src and '("ok", b)' in src


def main():
    import akasha
    f = akasha._should_replace_daemon

    # THE BUG: a no-build (pre-handshake) answering daemon must now be REPLACED, not left alone.
    check("no-build daemon (None) is REPLACED when we know our disk build (the fixed trap)",
          f(None, "abc123") is True)
    check("no-build daemon ('') is REPLACED too", f("", "abc123") is True)

    # A genuinely older build is replaced (this always worked).
    check("an OLDER-build daemon is replaced", f("oldbuild", "newbuild") is True)

    # An identical build is NEVER replaced — no needless ontology reload, no thrash/respawn loop
    # (after one replacement the fresh daemon reports a build and matches on the next launch).
    check("a SAME-build daemon is NOT replaced (no thrash, no reload)",
          f("abc123", "abc123") is False)

    # Safety: a launcher that cannot fingerprint its OWN tree must NOT evict anyone (no false takeover).
    check("unknown disk build → do NOT replace (no false takeover), even vs a reporting daemon",
          f("abc123", "") is False)
    check("unknown disk build → do NOT replace even a no-build daemon", f(None, "") is False)

    # F60 §4.1 — the tri-state tuple from cell_ipc.ping_build. A SILENT daemon (timeout/refused) is
    # NOT replaced (a busy/slow writer must not be evicted on a missed ping — the watchdog decides);
    # no-build is replaced (strictly older); ok replaces only on a different build.
    check("silent daemon (('silent', None)) is NOT replaced — busy ≠ stale",
          f(("silent", None), "abc123") is False)
    check("no-build tuple (('no-build', None)) IS replaced (pre-handshake ⇒ older)",
          f(("no-build", None), "abc123") is True)
    check("ok tuple with a DIFFERENT build is replaced", f(("ok", "old"), "new") is True)
    check("ok tuple with the SAME build is NOT replaced", f(("ok", "abc"), "abc") is False)
    check("unknown disk build → never replace, even a silent daemon", f(("silent", None), "") is False)
    check("cell_ipc.ping_build now returns a (status, build) tuple",
          _ping_build_returns_tuple())

    # _code_build_id covers the whole served tree so a new endpoint anywhere bumps the fingerprint
    # (the secondary latent gap: a method added under services/ or remote/ must still force a replace).
    import inspect
    src = inspect.getsource(akasha._code_build_id)
    for d in ("lib", "api", "services", "remote"):
        check(f"_code_build_id fingerprints the '{d}/' tree", f'"{d}"' in src or f"'{d}'" in src)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("All daemon-replacement decision checks passed."); sys.exit(0)


if __name__ == "__main__":
    main()
