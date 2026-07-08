#!/usr/bin/env python3
"""
Group-space sharing test — the family-group knowledge-sharing flow.

A group space is the minimal unit of *shared atoms*: several clients form a group
and donate atoms into one content-addressed space they can all read. It is the
entry point to the knowledge-exchange ecosystem (issue #26) and the substrate under
cloud offload (#27), multi-LLM collaboration, and DTN async handoff (#29) — so it
must actually work through the normal API flow (create user → add to group → share
→ read), not only in a hand-wired setup.

  P1 membership   — 5 members added to a group; each live session carries the group
                    scope AND a group engine, and each got a Human identity atom
                    (the user.add write runs under a workspace, not rejected).
  P2 share+read   — one member donates atoms to the group; every other member reads
                    them by key, by alias, and via `look`.
  P3 isolation    — a non-member cannot read the shared atoms (r and look denied).
  P4 concurrent   — all members donate into the one group space at once; the group's
                    single WriteQueue serialises them and every atom lands.
  P5 revocation   — removing a member drops the group engine + scope from their live
                    session; they can no longer read the shared atoms.

Run:  python test/loadtest_group.py

Developer verification test (not a user-facing .ak example). Drives the real kernel
dispatch path in-process.
"""
import os
import sys
import time
import hashlib
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def boot():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_grp_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def dispatcher(k):
    def d(tok, method, data, trust="local"):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": tok, "data": data},
                           "id": "t"}, trust)
    return d


def donate(d, member, atoms, set_name):
    """member writes `atoms` (list of content str), aliases them, and donates the
    whole set into group:family. Returns {content: key}."""
    keys = {}
    d(member, "dont.create", {"name": set_name})
    for i, content in enumerate(atoms):
        r = d(member, "w", {"content": content})
        key = (r.get("result") or {}).get("key")
        keys[content] = key
        d(member, "al", {"id": key, "name": f"{member}:{set_name}:{i}"})
        d(member, "dont.add", {"name": set_name, "targets": key})
    r = d(member, "dont.send", {"name": set_name, "to": "group:family"})
    return keys, r


# ── P1: membership → scope + engine + identity ───────────────────────────────

def phase1_membership(k, d, members):
    d("admin", "grp.new", {"group_id": "family", "admin_id": "admin"})
    human_ids = 0
    for cid in members:
        ph = hashlib.sha256(f"pw-{cid}".encode()).hexdigest()
        r = d("admin", "user.add", {"client_id": cid, "role": "user", "passphrase_hash": ph})
        if (r.get("result") or {}).get("human_id"):
            human_ids += 1
        d("admin", "grp.add", {"group_id": "family", "member_id": cid})

    # Each live session must now carry the group scope AND the group engine.
    scoped = 0
    engined = 0
    for cid in members:
        s = k.manager.get_session(cid)
        if "scope:group_family" in s.active_scopes:
            scoped += 1
        if "family" in s.group_engines:
            engined += 1
    ok = scoped == len(members) and engined == len(members) and human_ids == len(members)
    record("P1 membership", ok,
           f"{scoped}/{len(members)} scoped, {engined}/{len(members)} have engine, "
           f"{human_ids}/{len(members)} identity atoms")


# ── P2: donate + shared read by every member ─────────────────────────────────

def phase2_share_read(k, d, members):
    donor = members[0]
    recipe = "Grandma's apple pie recipe — secret: nutmeg"
    keys, r = donate(d, donor, [recipe], "share1")
    key = keys[recipe]
    donated_ok = (r.get("result") or {}).get("status") == "donated"

    read_by_key = 0
    read_by_alias = 0
    read_by_look = 0
    alias = f"{donor}:share1:0"
    for cid in members[1:]:
        rk = d(cid, "r", {"id": key})
        if (rk.get("result") or {}).get("content") == recipe:
            read_by_key += 1
        ra = d(cid, "r", {"id": alias})
        if (ra.get("result") or {}).get("content") == recipe:
            read_by_alias += 1
        rl = d(cid, "look", {"id": key})
        if (rl.get("result") or {}).get("type") == "atom":
            read_by_look += 1

    others = len(members) - 1
    ok = (donated_ok and read_by_key == others
          and read_by_alias == others and read_by_look == others)
    record("P2 share+read", ok,
           f"donated={donated_ok}; {read_by_key}/{others} by key, "
           f"{read_by_alias}/{others} by alias, {read_by_look}/{others} via look")
    return key, recipe


# ── P3: non-member isolation ─────────────────────────────────────────────────

def phase3_isolation(k, d, key, recipe):
    ph = hashlib.sha256(b"pw-out").hexdigest()
    d("admin", "user.add", {"client_id": "outsider", "role": "user", "passphrase_hash": ph})
    s = k.manager.get_session("outsider")
    no_scope = "scope:group_family" not in s.active_scopes
    no_engine = "family" not in s.group_engines

    rk = d("outsider", "r", {"id": key})
    rl = d("outsider", "look", {"id": key})
    r_denied = "error" in rk
    look_denied = "error" in rl
    # Belt-and-braces: even if a handler leaked, content must not equal the secret.
    leaked = (rk.get("result") or {}).get("content") == recipe
    ok = no_scope and no_engine and r_denied and look_denied and not leaked
    record("P3 isolation", ok,
           f"no-scope={no_scope} no-engine={no_engine} r-denied={r_denied} "
           f"look-denied={look_denied} leaked={leaked}")


# ── P4: concurrent donation into the one group space ─────────────────────────

def phase4_concurrent(k, d, members):
    per = 4
    errs = []
    lock = threading.Lock()

    def worker(cid):
        try:
            atoms = [f"{cid} shared note {j} :: {cid}-{j}" for j in range(per)]
            _, r = donate(d, cid, atoms, "bulk")
            if "error" in r:
                with lock:
                    errs.append(f"{cid}: {r['error']}")
        except Exception as e:  # noqa: BLE001
            with lock:
                errs.append(f"{cid}: {e!r}")

    ts = [threading.Thread(target=worker, args=(c,)) for c in members]
    t0 = time.time()
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)
    elapsed = time.time() - t0

    # Every donated atom must have landed in the one shared group space.
    ge = k.manager._get_group_engine("family")
    expected = len(members) * per
    landed = 0
    for cid in members:
        for j in range(per):
            content = f"{cid} shared note {j} :: {cid}-{j}"
            key = hashlib.sha256(content.encode("utf-8")).hexdigest()
            row = ge.core.get_chunk_raw(key)
            if row and row["content"] == content:
                landed += 1
    ok = not errs and landed == expected
    record("P4 concurrent", ok,
           f"{len(members)} donors x {per} = {expected} atoms → {landed} landed "
           f"in shared space, {len(errs)} errors, {elapsed:.1f}s")


# ── P5: membership revocation drops access ───────────────────────────────────

def phase5_revocation(k, d, members, key, recipe):
    victim = members[-1]
    # Confirm the victim can currently read the shared atom.
    before = (d(victim, "r", {"id": key}).get("result") or {}).get("content") == recipe

    d("admin", "grp.rm", {"group_id": "family", "member_id": victim})

    # Next dispatch refreshes the live session: scope + engine must be gone.
    s = k.manager.get_session(victim)
    scope_gone = "scope:group_family" not in s.active_scopes
    engine_gone = "family" not in s.group_engines
    after = d(victim, "r", {"id": key})
    now_denied = "error" in after and (after.get("result") or {}).get("content") != recipe

    ok = before and scope_gone and engine_gone and now_denied
    record("P5 revocation", ok,
           f"could-read-before={before}, scope-gone={scope_gone}, "
           f"engine-gone={engine_gone}, now-denied={now_denied}")


# ── P6: navigation within group scope, private atoms black-holed ─────────────

def phase6_navigation(k, d, members):
    donor, navigator = members[0], members[1]
    # donor shares one aliased atom into the group and keeps one PRIVATE (undonated)
    shared = f"NAV shared secret from {donor}"
    private = f"NAV private diary of {donor}"
    sk = (d(donor, "w", {"content": shared}).get("result") or {}).get("key")
    d(donor, "al", {"id": sk, "name": "nav:shared"})
    pk = (d(donor, "w", {"content": private}).get("result") or {}).get("key")
    d(donor, "al", {"id": pk, "name": "nav:private"})
    d(donor, "dont.create", {"name": "navset"})
    d(donor, "dont.add", {"name": "navset", "targets": sk})
    d(donor, "dont.send", {"name": "navset", "to": "group:family"})

    def visible(tok):
        ex = {a["key"] for a in (d(tok, "explore", {"ns": "nav"}).get("result") or {}).get("atoms", [])}
        al = {a["key"] for a in (d(tok, "alias.find", {"pattern": "nav:%"}).get("result") or {}).get("aliases", [])}
        sl = {m["key"] for m in (d(tok, "set.ls", {"name": "dont:navset"}).get("result") or {}).get("members", [])}
        return ex, al, sl

    m_ex, m_al, m_sl = visible(navigator)
    # A member navigates shared content via every path...
    member_sees_shared = sk in m_ex and sk in m_al and sk in m_sl
    # ...but another member's private atom is black-holed (never in the group space).
    member_blackholes_private = pk not in m_ex and pk not in m_al and pk not in m_sl
    # A non-member sees nothing at all.
    o_ex, o_al, o_sl = visible("outsider")
    outsider_sees_nothing = not (o_ex | o_al | o_sl) or (
        sk not in o_ex and sk not in o_al and sk not in o_sl
        and pk not in o_ex and pk not in o_al and pk not in o_sl)

    ok = member_sees_shared and member_blackholes_private and outsider_sees_nothing
    record("P6 navigation", ok,
           f"member sees shared (explore/alias/set.ls)={member_sees_shared}, "
           f"member-private black-holed={member_blackholes_private}, "
           f"outsider sees nothing={outsider_sees_nothing}")


def main():
    print("\n  group-space sharing test (5-family: donate → share → read → navigate → isolate)\n")
    members = [f"fam{i}" for i in range(5)]
    k = boot()
    d = dispatcher(k)

    phase1_membership(k, d, members)
    key, recipe = phase2_share_read(k, d, members)
    phase3_isolation(k, d, key, recipe)
    phase4_concurrent(k, d, members)
    phase6_navigation(k, d, members)
    phase5_revocation(k, d, members, key, recipe)

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — group-space sharing broke somewhere in the flow.")
        return 1
    print("\nRESULT: PASS — group sharing works end-to-end: members share and read, "
          "non-members are excluded, concurrent donations serialise, revocation cuts access.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
