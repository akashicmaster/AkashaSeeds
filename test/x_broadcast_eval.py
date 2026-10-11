#!/usr/bin/env python3
"""
x_broadcast — the channel client that survives the port, and the two seams it exposes.

Step 1 moved everything ABOUT posting into the application: what a thread says, when it goes out and
whether it goes at all are a workload's (`config/workbench/workloads/news_show_x.json` → the
declaration's cadence, and `station.publish` → the beats). What stays platform is this file — an HTTP
client that holds four credentials, the same kind of thing as a disk or a socket — plus:

  · the `x.key` op, because storing a provider credential in a chmod-0600 file on the host is
    platform, and it never was anything else;
  · the `channel.x.post_thread` hook, which is how the application asks for a thread to go out.

This eval covers THOSE, and nothing about a programme. The gates that decide whether a thread goes
(opt-in, consent, cursor) are the workload's and are held by `station_publish_channel_eval`. The
network is never touched: `post_tweet` is mocked, and the dry path must not call it at all.

Run:  python test/x_broadcast_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.workbench import x_broadcast as X                      # noqa: E402

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _clear_creds():
    for var in X.KEY_ALIASES.values():
        os.environ.pop(var, None)


def _set_creds():
    for i, var in enumerate(X.KEY_ALIASES.values()):
        os.environ[var] = "cred-%d-never-logged" % i


def main():
    print("=" * 78)
    print("The channel client, the credential op and the post hook")
    print("=" * 78)

    posted = []

    def fake_post(text, reply_to="", timeout=20.0):
        posted.append((text, reply_to))
        return {"id": "t%d" % len(posted)}
    X.post_tweet = fake_post

    # ── no credentials: the module reports it, and NOTHING goes out ──────────────────────────────
    _clear_creds()
    posted[:] = []
    check("with no credentials the client reports itself unavailable", X.available() is False)
    check("…and a thread is refused rather than half-sent",
          X.post_thread(["a", "b"]) is None and not posted, str(posted))
    check("…the hook answers the same way", X.post_thread_hook(["a", "b"]) is None)

    # ── the DRY path posts nothing, with or without credentials ──────────────────────────────────
    # It belongs here rather than at the caller: a dry run that still posted would be a silent,
    # irreversible, public mistake, and the one place that can guarantee it did not is the place
    # that would have made the call.
    _set_creds()
    posted[:] = []
    dry = X.post_thread_hook(["beat one", "beat two", "AI-generated · via Akasha"], dry=True) or {}
    check("a dry run returns the thread it WOULD send", dry.get("would_post") == 3
          and dry.get("tweets") and len(dry["tweets"]) == 3, str(dry.get("would_post")))
    check("…marks itself dry, so a caller cannot mistake it for a post", dry.get("dry") is True)
    check("…and calls the network ZERO times", not posted, str(posted))
    _clear_creds()
    posted[:] = []
    dry2 = X.post_thread_hook(["only beat"], dry=True) or {}
    check("a dry run works without credentials too — it is a preview, not an attempt",
          dry2.get("would_post") == 1 and dry2.get("creds") is False and not posted)

    # ── a real thread is a REPLY CHAIN ───────────────────────────────────────────────────────────
    _set_creds()
    posted[:] = []
    out = X.post_thread_hook(["one", "two", "three"]) or {}
    check("a thread posts each beat", out.get("posted") == 3, str(out))
    check("…as a reply chain: the first is a root, each next replies to the previous",
          [r for _t, r in posted] == ["", "t1", "t2"], str([r for _t, r in posted]))
    check("…and the ids come back in order", out.get("ids") == ["t1", "t2", "t3"], str(out.get("ids")))

    # ── a mid-thread failure stops the chain and reports what DID go ─────────────────────────────
    posted[:] = []

    def flaky(text, reply_to="", timeout=20.0):
        posted.append((text, reply_to))
        return {"id": "t1"} if len(posted) == 1 else None
    X.post_tweet = flaky
    part = X.post_thread_hook(["one", "two", "three"]) or {}
    check("a mid-thread failure stops the chain rather than retrying blindly",
          part.get("posted") == 1 and len(posted) == 2, "posted=%s calls=%d" % (part.get("posted"), len(posted)))
    posted[:] = []

    def always_fails(text, reply_to="", timeout=20.0):
        posted.append((text, reply_to))
        return None
    X.post_tweet = always_fails
    check("…and a FIRST post that fails reports None — nothing went out",
          X.post_thread_hook(["x"]) is None and len(posted) == 1, str(posted))
    X.post_tweet = fake_post

    # ── an empty thread is not an attempt ────────────────────────────────────────────────────────
    posted[:] = []
    check("an empty or blank thread is refused without a call",
          X.post_thread_hook([]) is None and X.post_thread_hook(["", "  "]) is None and not posted)

    # ── the hook is what the manifest declares ───────────────────────────────────────────────────
    import json
    man = json.load(open("lib/akasha/workbench/MANIFEST.json", encoding="utf-8"))
    check("the manifest declares the post hook the application calls",
          man["hooks"].get("channel.x.post_thread") ==
          "lib.akasha.workbench.x_broadcast:post_thread_hook",
          str(man["hooks"].get("channel.x.post_thread")))
    check("…and `x.key` is an op of this file now, not of a deleted programme",
          man["ops"]["x.key"]["fn"] == "lib.akasha.workbench.x_broadcast:handle_x_key",
          man["ops"]["x.key"]["fn"])

    # ── x.key: stores, masks, removes; librarian/admin only ──────────────────────────────────────
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_xkey_"))
    gw = AkashaGateway(kernel_client=k)
    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin",
                            "data": {"user_name": "admin",
                                     "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"},
                "local")

    def D(method, data, trust="local"):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": "admin", "data": data}, "id": "m"}, trust)
        return r.get("result") or r.get("error") or {}

    _clear_creds()
    st = D("x.key", {"action": "set", "consumer_key": "CK-secret", "consumer_secret": "CS-secret",
                     "access_token": "AT-secret", "access_secret": "AS-secret"})
    check("x.key set stores all four and reports complete",
          sorted(st.get("stored") or []) == sorted(X.KEY_ALIASES) and st.get("complete") is True,
          str(st.get("stored")))
    ls = D("x.key", {"action": "ls"})
    creds = ls.get("credentials") or {}
    check("x.key ls MASKS every value — a credential never comes back out",
          creds and all("secret" not in str(v).lower() or str(v).startswith("CK") is False
                        for v in creds.values())
          and not any(v in ("CK-secret", "CS-secret", "AT-secret", "AS-secret")
                      for v in creds.values()), str(creds))
    rm = D("x.key", {"action": "rm"})
    check("x.key rm removes them", "removed" in rm and X.available() is False, str(rm))
    bad = D("x.key", {"action": "set"})
    check("x.key set with no values is a parameter error, not a silent no-op",
          bad.get("code") == -32602, str(bad))
    _clear_creds()

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the client posts a thread as a reply chain, refuses without credentials, "
          "sends nothing on a dry run, and the credential op stores and masks. Nothing here knows "
          "what is being posted or when.")
    sys.exit(0)


if __name__ == "__main__":
    main()
