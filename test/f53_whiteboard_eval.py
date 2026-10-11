#!/usr/bin/env python3
"""
F53 Phase 0 Stage 2 — whiteboard as the naming layer over the horizon (E6 round-trip).

A whiteboard is now a NAMED bundle of the ONE session horizon: wb.pin = a soft horizon entry;
wb.focus saves the outgoing board's (horizon, focus) and restores the incoming one; recreating an
existing board is FOCUS (never erases — the old pins-wipe bug); a legacy `wb:<name>:pinned` board
migrates its pins to soft horizon entries ONCE on first focus. wb.* and the kernel horizon.* ops read
and write the SAME session horizon — that shared state is the normalization.

Run:  python test/f53_whiteboard_eval.py     (exit 0 = all pass)
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
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_wb_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def call(method, data=None):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data or {}}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    def hz_sets():
        return [e["set"] for e in call("horizon.ls", {}).get("horizon", [])]

    # ── 1. wb.pin writes the SAME session horizon the kernel horizon.* ops read ──
    call("wb.new", {"name": "board_a"})
    call("wb.pin", {"concept": "set:x"})
    call("wb.pin", {"concept": "set:y"})
    check("wb.pin adds soft horizon entries visible to the kernel horizon.ls (shared state)",
          set(hz_sets()) == {"set:x", "set:y"}, str(hz_sets()))

    # ── 2. switching boards saves + restores each board's horizon ──
    call("wb.new", {"name": "board_b"})
    check("a new board starts with an empty horizon (board_a's pins were saved, not carried over)",
          hz_sets() == [], str(hz_sets()))
    call("wb.pin", {"concept": "set:z"})
    fa = call("wb.focus", {"name": "board_a"})
    check("wb.focus board_a restores its (set:x, set:y) horizon; board_b's set:z is not present",
          set(hz_sets()) == {"set:x", "set:y"}, "focus=%s hz=%s" % (fa.get("status"), hz_sets()))

    # ── 3. recreation must never erase (the pins-wipe bug fix) ──
    rn = call("wb.new", {"name": "board_a"})
    check("wb.new on an EXISTING board is focus semantics — horizon is NOT wiped",
          set(hz_sets()) == {"set:x", "set:y"} and rn.get("status") in ("focused", "created"),
          "status=%s hz=%s" % (rn.get("status"), hz_sets()))
    fb = call("wb.focus", {"name": "board_b"})
    check("wb.focus board_b restores set:z (round-trip intact both ways)",
          set(hz_sets()) == {"set:z"}, str(hz_sets()))

    # ── 4. legacy wb:<name>:pinned migrates to soft horizon entries ONCE ──
    sess = k.manager.get_session("admin")
    names = sess.get_context("wb_names") or []
    sess.set_context("wb_names", names + ["legacy"])
    sess.set_context("wb:legacy:pinned", ["set:old1", "set:old2"])   # pre-F53 board, no :state
    fl = call("wb.focus", {"name": "legacy"})
    check("focusing a legacy board migrates its pins → soft horizon entries once (migrated=True)",
          fl.get("migrated") is True and set(hz_sets()) == {"set:old1", "set:old2"},
          "migrated=%s hz=%s" % (fl.get("migrated"), hz_sets()))
    # re-focus: no second migration (state now authoritative)
    call("wb.focus", {"name": "board_b"})
    fl2 = call("wb.focus", {"name": "legacy"})
    check("re-focusing the migrated board does NOT migrate again (state is authoritative)",
          fl2.get("migrated") is False and set(hz_sets()) == {"set:old1", "set:old2"}, str(fl2))

    # ── 5. wb.ls reports per-board horizon size O(1); wb.rm clears the active horizon ──
    ls = call("wb.ls", {})
    boards = {b["name"]: b for b in ls.get("whiteboards", [])}
    check("wb.ls lists boards with per-board horizon counts and the active marker",
          boards.get("board_a", {}).get("horizon") == 2 and boards.get("legacy", {}).get("active") is True,
          str(ls))
    call("wb.rm", {"name": "legacy"})
    check("wb.rm of the active board clears the live horizon",
          hz_sets() == [] and call("horizon.ls", {}).get("count") == 0, str(hz_sets()))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the whiteboard is a naming layer over the ONE session horizon: pins are soft "
          "horizon entries (shared with horizon.*), focus saves/restores each board's horizon, "
          "recreation never erases, and a legacy pinned board migrates once.")
    sys.exit(0)


if __name__ == "__main__":
    main()
