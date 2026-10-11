#!/usr/bin/env python3
"""
The token-signing secret is resolved ONCE, at boot — not by whichever request arrives first.

`GuestBindingStore` signs every `gbk:` (guest) and `akt:` (authenticated) token with one HMAC
secret, and used to mint it lazily on the request path. That mint is not concurrency-safe and
cannot cheaply be made so: two threads both find no cached secret and no stored key, both mint,
both write the vault, and whichever assignment lands last wins the attribute. Every token already
signed with a loser is then permanently invalid — the holder gets `-32001 Guest binding: signature
mismatch` on every call, forever, with no recovery but a new token.

That is not a thought experiment. A fresh cell hit it whenever its first traffic was concurrent —
a crawler reaching the portal before any serial guest create — and `collapse_eval`'s 24-client
burst hit it EVERY run: 353,083 instant refusals against 207 real renders. The storm eval was
therefore green on "the writer survives the burst" while measuring a spin on a dead token instead
of the render path it exists to bound. A broken token is fast; that is exactly why it hid.

The fix is placement, not locking: `IdentityManager.__init__` calls `ensure_secret()` while the
process is still single-threaded, so the request path only ever READS a resolved secret. This eval
holds that placement down.

Checked here, on BOTH cell shapes:
  1. the secret is resolved by the time the cell is built — before any request exists
  2. 24 threads create a guest token concurrently and use it: every token verifies, none is
     signature-mismatched (the regression, driven the way the burst drove it)
  3. every thread's token verifies under the SAME secret — one secret per cell, not one per minter
  4. the source is a vocabulary id: a fresh cell reads `minted`, a second IAM over the same
     nucleus reads `vault`, and AKASHA_SECRET reads `env` — the boot line an operator uses to
     answer "did the env secret actually reach this process?" (Security Model, priority #1)
  5. the boot line is written once, at INFO, and never carries the key itself

Run:  python test/guest_secret_boot_eval.py     (exit 0 = all pass)
"""
import hashlib
import logging
import os
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

_SOURCES = ("env", "vault", "minted", "ephemeral")


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


class _SlowVault:
    """The cold first read, slowed down so the mint window is wide enough to lose a race in.

    A real nucleus answers the first `vault_retrieve` off disk; here it takes 50 ms, which is what
    turns "two threads could both miss" from a theoretical interleaving into one that happens on
    every run. `vault_store` is last-write-wins, exactly as the real one is.
    """

    def __init__(self, counter):
        self._kv = {}
        self._counter = counter
        self._counter.setdefault("stored", [])

    def vault_retrieve(self, ns, key):
        import time
        self._counter["reads"] += 1
        val = self._kv.get((ns, key))    # what was committed when the read STARTED…
        time.sleep(0.05)                 # …and it takes 50 ms to come back, as a cold disk read does
        return val

    def vault_store(self, ns, key, value):
        self._counter["stored"].append(value)
        self._kv[(ns, key)] = value


def _slow_vault_store():
    """A GuestBindingStore over ONE cold, slow vault; returns it with the vault's read counter."""
    from lib.akasha.identity import GuestBindingStore
    counter = {"reads": 0}
    vault = _SlowVault(counter)
    return GuestBindingStore(nucleus_fn=lambda: vault), counter


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None

    cap = _Capture()
    iam_log = logging.getLogger("Harmonia.IAM")
    old = iam_log.level
    iam_log.addHandler(cap); iam_log.setLevel(logging.INFO)
    base = tempfile.mkdtemp(prefix="akasha_gsec_")
    os.environ.pop("AKASHA_SECRET", None)
    try:
        k = KernelDispatcher(series=series, base_dir=base)
    finally:
        iam_log.removeHandler(cap); iam_log.setLevel(old)

    store = k.iam.guest_bindings

    # ── 1. resolved at construction, before a single request ─────────────────────────────────
    check(f"[{shape}] the signing secret is resolved by the time the cell is built — the request "
          f"path only ever reads it",
          store._secret_bytes is not None and store._secret_source in _SOURCES,
          "source=%s" % store._secret_source)

    # ── 4/5. the boot line names a vocabulary source id and never the key ────────────────────
    lines = [l for l in cap.lines if "token signing secret" in l]
    check(f"[{shape}] one boot line names the source, at INFO",
          len(lines) == 1 and any(("source=" + s) in lines[0] for s in _SOURCES), str(lines))
    check(f"[{shape}] a fresh cell with no AKASHA_SECRET mints its own — source=minted",
          store._secret_source == "minted", store._secret_source)
    check(f"[{shape}] …and the line never carries the key itself",
          lines and store._secret_bytes.hex() not in lines[0], str(lines)[:80])

    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    # ── 2/3. THE REGRESSION — concurrent first touch, driven at the store ─────────────────────
    # Driven where the race actually lives, with the window held OPEN: a vault whose retrieve
    # sleeps is exactly the slow first read a cold cell does, and every thread would otherwise
    # walk through it and mint. A cell whose boot resolved the secret has nothing left to race
    # on — that is the claim, and this is the shape that can refute it.
    N = 24
    out = {"mismatch": 0, "ok": 0, "other": []}
    lock = threading.Lock()
    started = threading.Barrier(N)

    def _worker(st):
        started.wait(30.0)                       # all N arrive at the store together
        try:
            key = st.create()["binding_key"]
            sid = st.resolve(key)
        except Exception as e:                   # noqa: BLE001 — counted, never hidden
            with lock:
                if "signature mismatch" in str(e):
                    out["mismatch"] += 1
                else:
                    out["other"].append(str(e)[:80])
            return
        with lock:
            if sid and sid.startswith("guest:"):
                out["ok"] += 1
            else:
                out["other"].append("resolved to %r" % sid)

    resolved, vault_reads = _slow_vault_store()
    resolved.ensure_secret()                     # what IdentityManager.__init__ does, at boot
    ts = [threading.Thread(target=_worker, args=(resolved,), daemon=True) for _ in range(N)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(60.0)

    check(f"[{shape}] {N} tokens minted at once against a cold, slow vault: NOT ONE is "
          f"signature-mismatched",
          out["mismatch"] == 0, "mismatch=%d ok=%d other=%s" % (out["mismatch"], out["ok"],
                                                               out["other"][:2]))
    check(f"[{shape}] …and every one of them resolves (one secret per cell, not one per minter)",
          out["ok"] == N, "ok=%d/%d other=%s" % (out["ok"], N, out["other"][:2]))
    check(f"[{shape}] the boot resolve took the ONLY vault read — the request path never mints",
          vault_reads["reads"] == 1, "vault reads=%d" % vault_reads["reads"])

    # …and the same N threads against a store NOT resolved at boot show the window is real: they
    # walk into the mint together and come out holding different secrets. This is the shape the
    # placement removes — asserted as "more than one secret was minted", the defect itself, so
    # nothing here can pass by claiming the gap is harmless.
    raced, raced_v = _slow_vault_store()
    started2 = threading.Barrier(N)

    def _mint(_st):
        started2.wait(30.0)
        _st.ensure_secret()

    ts2 = [threading.Thread(target=_mint, args=(raced,), daemon=True) for _ in range(N)]
    for t in ts2:
        t.start()
    for t in ts2:
        t.join(60.0)
    _distinct = len(set(raced_v["stored"]))
    check(f"[{shape}] the window is real: entered concurrently, the mint runs again and again and "
          f"writes a DIFFERENT key each time — last one wins, every earlier token dies",
          _distinct > 1, "vault reads=%d distinct keys written=%d (one survives)"
          % (raced_v["reads"], _distinct))

    # ── 4b. a second IAM over the same nucleus adopts the stored key — source=vault ───────────
    from lib.akasha.identity import IdentityManager
    iam2 = IdentityManager(series, nucleus=k.manager.shared_nucleus)
    check(f"[{shape}] a second IAM over the same nucleus adopts the stored key — source=vault",
          iam2.guest_bindings._secret_source == "vault"
          and iam2.guest_bindings._secret_bytes == store._secret_bytes,
          iam2.guest_bindings._secret_source)

    # …and a token minted by one verifies in the other — which is the whole point of the vault
    gk = (k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                      "params": {"data": {}}, "id": "x"}, "network").get("result") or {}
          ).get("binding_key")
    try:
        sid = iam2.guest_bindings.resolve(gk)
    except Exception as e:                                   # noqa: BLE001 — reported, not hidden
        sid = "RAISED: %s" % e
    check(f"[{shape}] a token minted by one process verifies in another that read the same vault",
          isinstance(sid, str) and sid.startswith("guest:"), str(sid)[:90])

    # ── 4c. AKASHA_SECRET wins and is reported as such ───────────────────────────────────────
    os.environ["AKASHA_SECRET"] = "ab" * 32
    try:
        iam3 = IdentityManager(series, nucleus=k.manager.shared_nucleus)
        check(f"[{shape}] AKASHA_SECRET wins over the vault and reports source=env — the answer to "
              f"'did the env secret reach this process?'",
              iam3.guest_bindings._secret_source == "env"
              and iam3.guest_bindings._secret_bytes == bytes.fromhex("ab" * 32),
              iam3.guest_bindings._secret_source)
    finally:
        os.environ.pop("AKASHA_SECRET", None)


def main():
    print("=" * 78)
    print("Token-signing secret — resolved once at boot, never raced on the request path")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the signing secret is resolved while the cell is still single-threaded, "
          "so 24 guests arriving at once all hold tokens that verify; the source is reported as a "
          "vocabulary id (minted / vault / env) on one INFO line that never carries the key.")
    sys.exit(0)


if __name__ == "__main__":
    main()
