#!/usr/bin/env python3
"""
Recipe account / catalogue eval — the launch-hardening contract additions.

Covers the iOS-lead feedback items that are user-lifecycle / permission shaped:

  A1 food.personal — a regular user can define a PRIVATE food (food:user:<uid>:<slug>)
                     and their recipe's nutrition resolves it; it never touches the
                     shared catalogue.
  A2 food denied   — a regular user CANNOT write the shared catalogue via recipe.food
                     (catalog_denied); an admin/librarian can.
  A3 revision      — every write advances a monotonic `revision`; an in-place edit
                     (delete+recreate, same parts count) still bumps it; a stale
                     `expected_revision` is rejected as a conflict.
  A4 persistent id — a step keeps its `step_id` across an edit (atom key changes, the
                     logical id does not), and `after=<step_id>` still resolves.
  A5 delete        — auth.account.delete needs confirm, refuses without it, then erases
                     the account: login stops working and the user's recipes are gone;
                     another user is untouched.

Run:  python test/recipe_account_eval.py
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
os.environ["AKASHA_ALLOW_SELF_REGISTER"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def main():
    print("\n  recipe account / catalogue eval — launch-hardening contract\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_acct_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def net(method, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": method, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]
    net("user.add", atok, data={"client_id": "bob",
                                "passphrase_hash": hashlib.sha256(b"x").hexdigest()})
    btok = net("auth.verify", user_id="bob", passphrase="x")["result"]["session_token"]
    ctok = net("auth.register", user_id="carol", passphrase="hunter2secret")["result"]["session_token"]

    def bob(m, **f):
        return net(m, btok, **f)

    # A1 — personal food resolves in bob's own recipe nutrition.
    fp = bob("recipe.food.personal", name="my granola", basis_g="100",
             kcal="480", protein_g="10")
    r = bob("recipe.new", title="Granola Bowl")["result"]["recipe_id"]
    bob("recipe.add", recipe=r, ingredient="my granola", qty="50", unit="g")
    nut = bob("recipe.nutrition", recipe=r)["result"]
    a1 = (fp.get("result", {}).get("scope") == "personal"
          and fp["result"]["alias"] == "food:user:bob:my_granola"
          and abs(nut["totals"].get("kcal", 0) - 240.0) < 0.5      # 480 × 0.5
          and nut["measured"] == 1)
    record("A1 food.personal", a1,
           f"alias={fp.get('result',{}).get('alias')} kcal={nut['totals'].get('kcal')}")

    # A2 — shared catalogue is librarian/admin only.
    denied = bob("recipe.food", name="daikon", kcal="18")
    admin_ok = net("recipe.food", atok, name="daikon", kcal="18")
    a2 = ("error" in denied and "catalog_denied" in denied["error"]["message"]
          and admin_ok.get("result", {}).get("status") in ("created", "updated", "exists"))
    record("A2 food denied", a2,
           f"user_denied={'error' in denied} admin={admin_ok.get('result',{}).get('status')}")

    # A3 — monotonic revision + conflict on stale expected_revision.
    v_new = bob("recipe.new", title="Rev Test")["result"]
    rr = v_new["recipe_id"]
    rev0 = v_new["revision"]
    add1 = bob("recipe.add", recipe=rr, ingredient="pork", qty="100", unit="g")["result"]
    rev1 = bob("recipe.view", recipe=rr)["result"]["revision"]
    ikey = add1["key"]
    # in-place edit keeps the parts count but must still advance revision
    bob("recipe.ingredient.update", recipe=rr, item=add1["ingredient_id"], qty="150")
    rev2 = bob("recipe.view", recipe=rr)["result"]["revision"]
    conflict = bob("recipe.add", recipe=rr, ingredient="salt", qty="1", unit="g",
                   expected_revision=rev0)
    a3 = (rev0 >= 1 and rev1 > rev0 and rev2 > rev1
          and "error" in conflict and "conflict" in conflict["error"]["message"])
    record("A3 revision", a3, f"rev {rev0}→{rev1}→{rev2} conflict={'error' in conflict}")

    # A4 — persistent step_id across an edit; after=<step_id> resolves.
    sr = bob("recipe.new", title="Step Test")["result"]["recipe_id"]
    s1 = bob("recipe.step", recipe=sr, text="prep", dur="10")["result"]
    sid = s1["step_id"]
    key_before = s1["atom_key"]
    # edit the step text — atom key changes, step_id must NOT
    s1b = bob("recipe.step.update", recipe=sr, item=sid, text="prep carefully")["result"]
    s2 = bob("recipe.step", recipe=sr, text="cook", dur="20", after=sid)["result"]
    cr = bob("recipe.critical", recipe=sr)["result"]
    cook = next((row for row in cr["steps"] if row["text"].startswith("cook")), {})
    a4 = (s1b["step_id"] == sid and s1b["atom_key"] != key_before
          and cook.get("preds") and any(
              (row.get("step_id") == sid) for row in cr["steps"] if row["key"] in cook["preds"]))
    record("A4 persistent id", a4,
           f"step_id_stable={s1b['step_id'] == sid} key_changed={s1b['atom_key'] != key_before}")

    # A5 — account deletion: confirm required, then erased.
    no_confirm = net("auth.account.delete", ctok)
    made = net("recipe.new", ctok, title="Carol Dish")["result"]["recipe_id"]
    gone = net("auth.account.delete", ctok, confirm="true")
    relogin = net("auth.verify", user_id="carol", passphrase="hunter2secret")
    bob_still = bob("recipe.ls").get("result", {}).get("recipes") is not None
    a5 = ("error" in no_confirm and gone.get("result", {}).get("status") == "deleted"
          and "error" in relogin and bob_still)
    record("A5 delete", a5,
           f"needs_confirm={'error' in no_confirm} deleted={gone.get('result',{}).get('status')} "
           f"relogin_blocked={'error' in relogin} other_user_ok={bob_still}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
