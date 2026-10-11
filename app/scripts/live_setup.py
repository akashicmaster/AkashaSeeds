#!/usr/bin/env python3
"""
live_setup.py — manually register the live-telemetry feeds on a running Akasha daemon.

USUALLY UNNECESSARY: a cell that carries the live-telemetry workloads (the `feeds` path group) AUTO-PROVISIONS the built-in public
feeds at boot (kernel `_provision_default_feeds`, from FeedConcept.DEFAULT_FEEDS) and fetches them
unattended — so real-time telemetry needs zero manual setup, and the public /live/ map (guest-read)
goes live on its own. This script stays for the rare case: a deployment NOT running the poller, or to
force an immediate registration + pull.

It signs in as an operator over the daemon's HTTP `/rpc` (auth.verify, same as the web login),
registers FeedConcept.DEFAULT_FEEDS (eonet / usgs_eq / iss — verified real-API map-DSLs), and with
`--pull` does one immediate `feed.pull` each. Feeds fetch the live public APIs directly on the daemon
(EONET / USGS / wheretheiss.at); the fetch honours HTTPS_PROXY.

  AKASHA_ADMIN_PASS=… python app/scripts/live_setup.py --rpc http://127.0.0.1:8000/rpc --user admin --pull

Then open /live/ — it is a public page (guest-read), no viewer login. DEMO mode (the fixtures) needs
no daemon at all.
"""
import argparse, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")
from app.concepts.feed import FeedConcept   # DEFAULT_FEEDS = the live-provisionable public feeds

# NOTE: a cell that carries the `feeds` workloads AUTO-PROVISIONS these same feeds at boot (kernel
# _provision_default_feeds), so this script is usually UNNECESSARY. It stays as a manual bootstrap for a
# deployment that isn't running the poller, or to force an immediate pull.


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": method}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:      # honours HTTPS_PROXY for remote daemons
        j = json.loads(r.read().decode("utf-8", errors="replace"))
    if j.get("error"):
        raise SystemExit("✗ RPC error on %s: %s" % (method, j["error"]))
    return j.get("result")


def main():
    ap = argparse.ArgumentParser(description="Register the live-telemetry feeds on a running daemon.")
    ap.add_argument("--rpc", default="http://127.0.0.1:8000/rpc",
                    help="the daemon's JSON-RPC endpoint (default %(default)s)")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--pull", action="store_true",
                    help="also do one immediate feed.pull per feed (fetches the live APIs now)")
    args = ap.parse_args()

    pw = os.environ.get("AKASHA_ADMIN_PASS")
    if not pw:
        import getpass
        pw = getpass.getpass("admin passphrase: ")

    auth = rpc(args.rpc, "auth.verify", {"user_id": args.user, "passphrase": pw}) or {}
    tok = auth.get("session_token")
    if not tok:
        raise SystemExit("✗ sign-in failed (check --user / passphrase / --rpc)")
    print("✓ signed in as %s (%s)" % (args.user, auth.get("role", "?")))

    for f in FeedConcept.DEFAULT_FEEDS:
        rpc(args.rpc, "feed.register", {"session_token": tok, "data": {
            "id": f["id"], "kind": f["kind"], "url": f["url"], "interval": f["interval"],
            "retain": f["retain"], "map": f["map"], "title": f["title"]}})
        note = "" if f["url"] else "   (no url — AIS needs a key; the poller skips it)"
        print("  ✓ registered feed:%-9s %s%s" % (f["id"], f["kind"], note))

    if args.pull:
        print("\n▸ initial pull (fetching the live APIs)…")
        for f in FeedConcept.DEFAULT_FEEDS:
            if not f["url"]:
                continue
            r = rpc(args.rpc, "feed.pull", {"session_token": tok, "data": {"id": f["id"]}}) or {}
            print("  %-9s → %s  (%s new)" % (f["id"], r.get("status", "?"), r.get("observations_new", "?")))

    print("\n▸ done. Unattended fetching is the feeds workloads' (telemetry/<feed>) cadence.")
    print("  Then open  /live/?mode=live  and sign in.")


if __name__ == "__main__":
    main()
