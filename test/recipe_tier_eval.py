#!/usr/bin/env python3
"""
Recipe tiering eval — server-side entitlement enforcement (the akashickitchen model).

Tiering is OFF by default (OSS = no limits). With AKASHA_RECIPE_TIERING=1 a free plan
is capped at AKASHA_RECIPE_FREE_QUOTA own recipes and the analytics features
(nutrition / critical / haccp) require a paid plan. A user's plan lives in the shared
nucleus vault (server-side, cross-session), set only by an admin/server role —
the billing hook. Enforcement is server-side because a client can't be trusted to
honour a quota or a paywall.

  T1 quota      — a free user hits `quota_reached` on the (N+1)th recipe.
  T2 gate       — nutrition / critical / haccp return a `locked` result for free.
  T3 upgrade    — admin recipe.plan.set tier=paid lifts the quota AND unlocks the
                  features, visible in the *user's own* session (cross-session vault).
  T4 downgrade  — tier=free re-locks; free users cannot self-upgrade.
  T5 off        — with tiering OFF everyone is 'paid' (no limits) — the OSS default.
  T6 register   — general auth.register (bounded, config-gated) self-signs a user on
                  the free plan, role forced to 'user', duplicate id rejected; the
                  general auth.plan.set (admin) upgrades them, reflected in recipe gates.

Run:  python test/recipe_tier_eval.py
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"
os.environ["AKASHA_RECIPE_TIERING"] = "1"
os.environ["AKASHA_RECIPE_FREE_QUOTA"] = "2"
os.environ["AKASHA_ALLOW_SELF_REGISTER"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


def main():
    print("\n  recipe tiering eval — server-side entitlement (quota + feature gates)\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_tier_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def call(tok, method, **fields):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": tok, **fields}, "id": 9}, "network")

    atok = call(None, "auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]
    call(atok, "user.add", data={"client_id": "bob",
                                 "passphrase_hash": hashlib.sha256(b"x").hexdigest()})
    btok = call(None, "auth.verify", user_id="bob", passphrase="x")["result"]["session_token"]

    def bob(m, **f):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": btok, **f}, "id": 9}, "network")
    def adm(m, **f):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": atok, **f}, "id": 9}, "network")

    # T1 — quota (free = 2)
    bob("recipe.new", title="R1"); bob("recipe.new", title="R2")
    over = bob("recipe.new", title="R3")
    t1 = ("error" in over and "quota_reached" in over["error"]["message"])
    record("T1 quota", t1, over.get("error", {}).get("message", "")[:38])

    rid = bob("recipe.ls")["result"]["recipes"][0]["recipe_id"]
    # T2 — feature gates (free)
    nut = bob("recipe.nutrition", recipe=rid)["result"]
    cri = bob("recipe.critical", recipe=rid)["result"]
    hac = bob("recipe.haccp", recipe=rid)["result"]
    t2 = (nut.get("locked") and cri.get("locked") and hac.get("locked")
          and nut.get("reason") == "upgrade_required")
    record("T2 gate", t2, f"nutrition/critical/haccp locked={nut.get('locked'),cri.get('locked'),hac.get('locked')}")

    # T3 — admin upgrade, visible in bob's own session (cross-session vault)
    adm("recipe.plan.set", user="bob", tier="paid")
    plan = bob("recipe.plan")["result"]
    made = bob("recipe.new", title="R3").get("result", {})
    unlocked = "totals" in bob("recipe.nutrition", recipe=rid)["result"]
    t3 = (plan["tier"] == "paid" and made.get("status") == "created" and unlocked)
    record("T3 upgrade", t3, f"tier={plan['tier']} 3rd={made.get('status')} nutrition_unlocked={unlocked}")

    # T4 — downgrade re-locks; a free user cannot self-upgrade
    adm("recipe.plan.set", user="bob", tier="free")
    relocked = bob("recipe.nutrition", recipe=rid)["result"].get("locked")
    self_up = bob("recipe.plan.set", user="bob", tier="paid")
    t4 = (relocked and "error" in self_up and "upgrade_denied" in self_up["error"]["message"])
    record("T4 downgrade", t4, f"relocked={relocked} self_upgrade_denied={'error' in self_up}")

    # T5 — tiering OFF ⇒ everyone unlimited/paid (OSS default)
    os.environ["AKASHA_RECIPE_TIERING"] = "0"
    off_plan = bob("recipe.plan")["result"]
    off_made = bob("recipe.new", title="R4").get("result", {})
    off_nut = "totals" in bob("recipe.nutrition", recipe=rid)["result"]
    os.environ["AKASHA_RECIPE_TIERING"] = "1"
    t5 = (off_plan["tier"] == "paid" and off_made.get("status") == "created" and off_nut)
    record("T5 off", t5, f"tier={off_plan['tier']} create={off_made.get('status')} nutrition={off_nut}")

    # T6 — general self-registration + general auth.plan.set (billing hook)
    def net(m, tok=None, **f):
        p = {"session_token": tok} if tok else {}
        p.update(f)
        return k.dispatch({"jsonrpc": "2.0", "method": m, "params": p, "id": 9}, "network")
    reg = net("auth.register", user_id="carol", passphrase="hunter2secret")
    ctok = reg.get("result", {}).get("session_token")
    dup = net("auth.register", user_id="carol", passphrase="hunter2secret")
    free_tier = net("auth.plan", ctok)["result"]["tier"] if ctok else "?"
    net("recipe.new", ctok, title="C1"); net("recipe.new", ctok, title="C2")
    c_quota = "quota_reached" in net("recipe.new", ctok, title="C3").get("error", {}).get("message", "")
    adm("auth.plan.set", user="carol", tier="paid")          # general billing hook
    paid_tier = net("auth.plan", ctok)["result"]["tier"]
    c_lifted = net("recipe.new", ctok, title="C3").get("result", {}).get("status") == "created"
    t6 = (reg.get("result", {}).get("status") == "registered"
          and reg["result"]["role"] == "user" and free_tier == "free"
          and "error" in dup and c_quota and paid_tier == "paid" and c_lifted)
    record("T6 register", t6,
           f"reg={reg.get('result',{}).get('status')} role={reg.get('result',{}).get('role')} "
           f"dup_rejected={'error' in dup} free→paid={free_tier}→{paid_tier} quota_then_lifted={c_quota and c_lifted}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
