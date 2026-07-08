#!/usr/bin/env python3
"""
Benchmark & evaluation harness — turn Akasha's headline claims into measured numbers.

"70% of RAG systems ship with no evaluation." This harness makes the claims
Akasha actually rests on repeatable and checkable:

  crash-stop     — the marquee one, proven for real: a subprocess writes atoms to the
                   FULL-synchronous nucleus, gets SIGKILL'd mid-write, and on reopen
                   EVERY atom whose commit returned is intact (last-write-only: only
                   the in-flight write is lost, nothing committed).
  throughput     — writes/sec and p50/p99 latency through the real kernel path.
  dedup          — content-addressed unification ratio (identical content → one atom).
  isolation      — cross-user read is refused (fail-closed), scored as a pass rate.

Emits a human-readable summary and, with --json, a machine-readable report for CI.

    python test/benchmark.py
    python test/benchmark.py --json
"""
import os
import sys
import time
import json
import signal
import hashlib
import tempfile
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"


# ── crash-stop driver (this file re-invokes itself in this mode) ─────────────

def run_crash_driver(base_dir, sentinel):
    """Write atoms to the FULL-synchronous nucleus forever, recording each atom's
    key to `sentinel` (fsync'd) only AFTER its commit returned — i.e. only durable
    atoms are recorded. The parent SIGKILLs us mid-loop."""
    from lib.akasha.composite import NucleusEngine
    ne = NucleusEngine(os.path.join(base_dir, "nucleus.db"))
    f = open(sentinel, "a", buffering=1)
    i = 0
    while True:
        content = f"crash-atom-{i}"
        ne.put_atom(content, {"i": i}, author="crash")   # FULL sync → on disk on return
        key = hashlib.sha256(content.encode("utf-8")).hexdigest()
        f.write(key + "\n")
        f.flush()
        os.fsync(f.fileno())
        i += 1


def bench_crash_stop():
    base = tempfile.mkdtemp(prefix="akasha_crash_")
    sentinel = os.path.join(base, "committed.log")
    open(sentinel, "w").close()
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__),
                             "--crash-driver", base, sentinel],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)                       # let it commit a few hundred atoms
    os.kill(proc.pid, signal.SIGKILL)     # hard crash, no cleanup
    proc.wait()
    time.sleep(0.3)

    # Reopen the same nucleus and verify every RECORDED (committed) atom survived.
    from lib.akasha.composite import NucleusEngine
    committed = [ln.strip() for ln in open(sentinel) if ln.strip()]
    ne = NucleusEngine(os.path.join(base, "nucleus.db"))
    survived = sum(1 for key in committed if ne.core.get_chunk_raw(key))
    lost = len(committed) - survived
    ok = len(committed) > 0 and lost == 0
    return {
        "metric": "crash-stop",
        "ok": ok,
        "committed": len(committed),
        "survived": survived,
        "lost": lost,
        "note": "SIGKILL mid-write; every committed atom intact on reopen (last-write-only)"
                if ok else "committed atoms lost after SIGKILL — durability regressed",
    }


# ── shared in-process kernel for the other metrics ───────────────────────────

def boot():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_bench_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    # warm the weave/NLP path so the one-time spacy probe is out of the timed section
    for i in range(3):
        k.dispatch({"jsonrpc": "2.0", "method": "w",
                    "params": {"session_token": "admin", "data": {"content": f"warm {i}"}},
                    "id": "w"}, "local")
    time.sleep(3.0)
    return k


def pct(xs, p):
    if not xs:
        return 0.0
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1))))] * 1000.0


def bench_throughput(k, n=400):
    lat = []
    t0 = time.time()
    for i in range(n):
        s = time.time()
        k.dispatch({"jsonrpc": "2.0", "method": "w",
                    "params": {"session_token": "admin", "data": {"content": f"bench atom {i}"}},
                    "id": "b"}, "local")
        lat.append(time.time() - s)
    elapsed = time.time() - t0
    return {"metric": "throughput", "ok": True, "writes": n,
            "writes_per_sec": round(n / elapsed, 1),
            "p50_ms": round(pct(lat, 50), 2), "p99_ms": round(pct(lat, 99), 2)}


def bench_dedup(k, n=50):
    content = "DEDUP-CONSTANT-CONTENT-for-benchmark"
    keys = set()
    for _ in range(n):
        r = k.dispatch({"jsonrpc": "2.0", "method": "w",
                        "params": {"session_token": "admin", "data": {"content": content}},
                        "id": "d"}, "local")
        keys.add((r.get("result") or {}).get("key"))
    return {"metric": "dedup", "ok": len(keys) == 1,
            "writes": n, "distinct_atoms": len(keys),
            "ratio": f"{n}:1" if len(keys) == 1 else f"{n}:{len(keys)}"}


def bench_isolation(k):
    d = lambda tok, m, data: k.dispatch(
        {"jsonrpc": "2.0", "method": m, "params": {"session_token": tok, "data": data}, "id": "i"},
        "local")
    checks, passed = 0, 0
    for a, b in (("u1", "u2"), ("u2", "u1")):
        for cid in (a, b):
            d("admin", "user.add", {"client_id": cid, "role": "user",
                                    "passphrase_hash": hashlib.sha256(cid.encode()).hexdigest()})
        secret = f"{a} private {time.time()}"
        key = (d(a, "w", {"content": secret}).get("result") or {}).get("key")
        r = d(b, "r", {"id": key})
        checks += 1
        if "error" in r or (r.get("result") or {}).get("content") != secret:
            passed += 1
    return {"metric": "isolation", "ok": passed == checks,
            "checks": checks, "refused": passed,
            "pass_rate": f"{passed}/{checks}"}


def main():
    as_json = "--json" in sys.argv
    print("\n  Akasha benchmark & evaluation\n")

    results = []
    crash = bench_crash_stop()
    results.append(crash)
    print(f"  {'OK ' if crash['ok'] else '!! '} crash-stop   "
          f"committed={crash['committed']} survived={crash['survived']} lost={crash['lost']}  "
          f"({crash['note']})")

    k = boot()
    for fn in (bench_throughput, bench_dedup, bench_isolation):
        r = fn(k)
        results.append(r)
        if r["metric"] == "throughput":
            print(f"  {'OK ' if r['ok'] else '!! '} throughput   "
                  f"{r['writes_per_sec']} w/s (p50={r['p50_ms']}ms p99={r['p99_ms']}ms, {r['writes']} writes)")
        elif r["metric"] == "dedup":
            print(f"  {'OK ' if r['ok'] else '!! '} dedup        "
                  f"{r['ratio']} ({r['writes']} identical writes → {r['distinct_atoms']} atom)")
        elif r["metric"] == "isolation":
            print(f"  {'OK ' if r['ok'] else '!! '} isolation    "
                  f"cross-user read refused {r['pass_rate']}")

    ok = all(r["ok"] for r in results)
    print()
    if as_json:
        print(json.dumps({"ok": ok, "results": results}, indent=2))
    print(f"  RESULT: {'PASS' if ok else 'FAIL'} — "
          + ("all measured claims hold." if ok else "a measured claim regressed."))
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--crash-driver":
        run_crash_driver(sys.argv[2], sys.argv[3])
    else:
        sys.exit(main())
