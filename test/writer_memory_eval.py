#!/usr/bin/env python3
"""
A48.2 / A48.3 — the writer's memory discipline is instrumented.

A48.2: a META-ONLY store iterator (`iter_chunk_meta`) lets a sweep read the two meta fields it needs
without preading + holding every atom's content; an UNCAPPED `iter_all_chunks` logs one `[scan]`
WARNING so a new O(store) read cannot appear silently. A48.3: `_with_rss_delta(tag, fn)` wraps a
writer-daemon task and logs its footprint in the `[maint] … Δrss=…` shape (INFO < 16 MB, WARNING above).

Run:  python test/writer_memory_eval.py     (exit 0 = all pass)
"""
import hashlib
import logging
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


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO); self.lines = []

    def emit(self, record):
        try:
            self.lines.append(record.getMessage())
        except Exception:
            pass

    def has(self, *subs):
        return any(all(s in ln for s in subs) for ln in self.lines)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher, _with_rss_delta
    from lib.akasha.jcl.workspace_context import system_context
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_wm_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    nuc = k.manager.shared_nucleus
    core = nuc.core

    # write a handful of atoms with distinctive content
    with system_context():
        for i in range(20):
            nuc.put_atom("CONTENT-BODY-%d-xxxxxxxxxxxxxxxx" % i, {"concept": "thing", "n": i},
                         author="admin", alias="wm:%d" % i)

    # ── A48.2 — iter_chunk_meta yields key + meta but NOT content ──
    check(f"[{shape}] the backend exposes iter_chunk_meta", hasattr(core, "iter_chunk_meta"))
    rows = list(core.iter_chunk_meta(limit=50))
    check(f"[{shape}] iter_chunk_meta returns the atoms", len(rows) >= 20, str(len(rows)))
    check(f"[{shape}] iter_chunk_meta rows carry key + meta but NO content",
          all(("key" in r and "meta" in r and "content" not in r) for r in rows),
          str(sorted(rows[0].keys())) if rows else "(none)")

    # ── A48.2 — an uncapped iter_all_chunks logs one [scan] WARNING ──
    root = logging.getLogger(); cap = _Cap(); root.addHandler(cap); _lvl = root.level; root.setLevel(logging.INFO)
    try:
        # reset the throttle so this test observes a fresh warning
        try:
            from lib.akasha.backends import sqlite as _sq
            _sq._scan_warn_seen.clear()
        except Exception:
            pass
        try:
            from lib.akasha.backends import silica_backend as _si
            _si._sb_scan_warn_seen.clear()
        except Exception:
            pass
        _ = list(core.iter_all_chunks())          # uncapped → one [scan] warning
        check(f"[{shape}] an uncapped iter_all_chunks logs a [scan] O(store) warning",
              cap.has("[scan] O(store) walk", "iter_all_chunks"),
              next((ln for ln in cap.lines if "[scan]" in ln), "(none)"))

        # ── A48.3 — _with_rss_delta wraps a task and logs the [maint] Δrss line ──
        cap.lines.clear()
        out = _with_rss_delta("unit.task", lambda: 42)
        check(f"[{shape}] _with_rss_delta returns the task result", out == 42)
        check(f"[{shape}] _with_rss_delta logs a [maint] Δrss line",
              cap.has("[maint] unit.task", "Δrss="),
              next((ln for ln in cap.lines if "[maint]" in ln), "(none)"))
        # it re-raises the task's exception (the Δrss line still prints)
        cap.lines.clear()
        raised = False
        try:
            _with_rss_delta("unit.boom", lambda: (_ for _ in ()).throw(ValueError("boom")))
        except ValueError:
            raised = True
        check(f"[{shape}] _with_rss_delta re-raises and still logs", raised and cap.has("[maint] unit.boom"))
    finally:
        root.removeHandler(cap); root.setLevel(_lvl)


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — iter_chunk_meta reads meta without content, an uncapped iter_all_chunks logs a "
          "[scan] warning, and _with_rss_delta logs the [maint] Δrss line (and re-raises) — both cell "
          "shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
