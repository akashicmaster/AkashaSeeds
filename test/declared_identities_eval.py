#!/usr/bin/env python3
"""
Declared identities (platform-spec v1 §5.8), on a FIXTURE application root built here.

  1. At Genesis each declared identity is created WITHOUT a credential, with its declared lines.
  2. A second reconcile (what every later writer boot does) creates nothing and adds no line.
  3. The owner sets the passphrase with `user.passwd <name>` and it verifies; nothing was ever
     stored for it before.
  4. Refused, naming the entry: a system or reserved name, a name declared twice, an unknown
     id-set, a malformed line.
  5. With no declaration there is nothing to do.

Run:  python test/declared_identities_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
FIX = tempfile.mkdtemp(prefix="ident_app_")
os.environ["AKASHA_APP_DIR"] = os.path.join(FIX, "fxapp")      # before the platform reads its root
logging.disable(logging.WARNING)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def declare(doc):
    p = os.path.join(os.environ["AKASHA_APP_DIR"], "config", "identities.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(doc, f)


def main():
    print("=" * 78)
    print("Declared identities (fixture application root)")
    print("=" * 78)
    from lib.akasha import identities as I
    from lib.akasha.api import gate

    check("5. no declaration → nothing declared", I.load() == [])
    declare({"identities": [{"name": "reader", "idsets": ["resident"]},
                            {"name": "fellow", "idsets": ["member on fxg"]}]})

    from lib.akasha.api.client import embedded
    gw = embedded(tempfile.mkdtemp(prefix="ident_cell_"), "seeds", load_ontology=False)
    k = gw.kernel_client

    def call(m, data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": "x"}, "local")
    g = call("kernel.genesis_rite", {"user_name": "admin", "passphrase": "pw-123456"})
    check("Genesis binds", (g.get("result") or {}).get("status") == "bound", str(g)[:120])

    rec = k.iam.get_client("reader") or {}
    check("1. the declared identity exists after Genesis, with NO credential",
          bool(rec) and not rec.get("passphrase_hash") and rec.get("created_by") == "declaration", str(rec)[:120])
    check("…with its declared lines (`resident`; `member on fxg`)",
          [l["idset"] for l in gate.lines_for("reader")] == ["resident"]
          and [(l["idset"], l["on"]) for l in gate.lines_for("fellow")] == [("member", "fxg")],
          "%s %s" % (gate.lines_for("reader"), gate.lines_for("fellow")))
    check("…and it cannot sign in yet", not k.iam.verify_passphrase("reader", hashlib.sha256(b"x").hexdigest()))

    created, added = I.reconcile(k)
    check("2. a second reconcile creates nothing and adds no line", (created, added) == (0, 0),
          str((created, added)))

    pw = hashlib.sha256(b"reader-secret").hexdigest()
    r = call("user.passwd", {"client_id": "reader", "passphrase_hash": pw})
    check("3. `user.passwd <name>` sets the passphrase, and it verifies",
          "result" in r and k.iam.verify_passphrase("reader", pw), str(r)[:120])

    print("\n  ── refusals ──")
    for doc, needle, what in (
            ({"identities": [{"name": "admin", "idsets": ["resident"]}]}, "platform's own", "admin"),
            ({"identities": [{"name": "system.x", "idsets": []}]}, "platform's own", "a system.* name"),
            ({"identities": [{"name": "a", "idsets": []}, {"name": "a", "idsets": []}]}, "twice", "a duplicate"),
            ({"identities": [{"name": "a", "idsets": ["nope"]}]}, "not a row", "an unknown id-set"),
            ({"identities": [{"name": "a", "idsets": ["member at x"]}]}, "is not", "a malformed line"),
            ({"identities": [{"name": "a b", "idsets": []}]}, "without spaces", "a spaced name")):
        declare(doc)
        try:
            I.load()
            msg = ""
        except ValueError as exc:
            msg = str(exc)
        check("4. %s is refused, naming the entry" % what, needle in msg and "identities[" in msg, msg)

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a declared identity is made once, without a credential, with its lines; its "
          "owner sets the passphrase at the prompt; a declaration the platform cannot honour stops "
          "the boot by name.")
    sys.exit(0)


if __name__ == "__main__":
    main()
