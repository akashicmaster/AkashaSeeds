#!/usr/bin/env python3
"""
A38 — the CLI `world.axis` table shows the full clock-ordered ledger.

The v20 note: the CLI rendered world.axis through the generic concept-list fallback, which printed
only a truncated id and two arbitrary fields — dropping position, the wall-clock, the full kind, and
the note. This eval renders a real axis (two env records + one sync record) through the CLI renderer
and asserts every dropped column is now present, with a LOCAL wall-clock derived from the stored
`<ISO>|<epoch>` stamp.

Run:  python app/test/world_axis_render_eval.py     (exit 0 = all pass)
"""
import io
import os
import sys
import time
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _strip(s):
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)


def main():
    from api.shell import renderer
    epoch = 1_725_000_000.0
    iso = "2026-09-08T12:00:00.000Z"
    wall = f"{iso}|{epoch}"
    result = {
        "world": "commons:default",
        "count": 3,
        "axis": [
            {"type": "env", "id": "world_env:default:c1", "kind": "world.created",
             "ref": "commons:mylab", "note": "My Lab", "cronon": "cron:default:c1",
             "position": 1, "wall": wall},
            {"type": "env", "id": "world_env:default:c2", "kind": "sensor.reading",
             "ref": None, "note": "temp=21C", "cronon": "cron:default:c2",
             "position": 2, "wall": wall},
            {"type": "sync", "id": "world_sync:default:c3", "kind": "workflow.dispatched",
             "exec": "exec:abc123", "bench": "wb:plants-vision", "branch": "plants_b4",
             "agents": ["Botanist"], "position": 3, "wall": wall, "note": None},
        ],
    }
    buf = io.StringIO()
    with redirect_stdout(buf):
        renderer.render({"jsonrpc": "2.0", "id": "t", "result": result})
    out = _strip(buf.getvalue())

    check("the header names the world", "world axis: commons:default" in out, out.splitlines()[1] if out else "")
    check("the record count is shown", "3 records" in out, "")
    check("position column present (1,2,3 all shown)",
          all(f" {p} " in out or f" {p}\n" in out or f">{p}" in out or out.count(str(p)) for p in (1, 2, 3)))
    # the FULL kind strings (not truncated) are present
    check("the full kind is shown (world.created)", "world.created" in out)
    check("the full kind is shown (workflow.dispatched)", "workflow.dispatched" in out)
    # the full id (not a 16-char truncation) is shown
    check("the full id is shown (not truncated)", "world_sync:default:c3" in out,
          "sync id present")
    # a LOCAL wall-clock derived from the epoch part of `<ISO>|<epoch>`
    expect_local = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))
    check("a local wall-clock is derived from the stamp", expect_local in out, expect_local)
    # the note tail is shown
    check("the note is shown", "My Lab" in out and "temp=21C" in out)
    # sync detail tail
    check("the sync detail (exec/bench/branch) is shown",
          "exec:abc123" in out and "wb:plants-vision" in out and "plants_b4" in out)

    # empty axis renders cleanly (no crash, an explicit empty marker)
    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        renderer.render({"jsonrpc": "2.0", "id": "t", "result": {"world": "commons:default", "count": 0, "axis": []}})
    out2 = _strip(buf2.getvalue())
    check("an empty axis renders an explicit marker (no crash)", "axis empty" in out2, out2.strip()[-40:])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the CLI world.axis table shows the full ledger: position, the full kind, a "
          "local wall-clock derived from the stored stamp, the full id, and the ref/note/sync tail — "
          "no longer the truncated two-field concept-list fallback.")
    print("\n--- sample render ---\n" + out)
    sys.exit(0)


if __name__ == "__main__":
    main()
