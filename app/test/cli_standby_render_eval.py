#!/usr/bin/env python3
"""
The CLI shows why something did not happen.

Directive 2026-10-02 §2 (frontend 09-28 item 4). An op that stands by returns
`{status, reason, detail}`. The operator's shell printed `✓ standby` and dropped both, so on the VPS
the reason for an X publish that did not post (09-28 09:17) was only in the log. And a
`station.air.ls` row showed its first two fields cut to 20 characters, so the `reason` column never
appeared.

Through the REAL command path — `sys.cli_exec` (the shlex parser and the router) on a cell
provisioned from the real declarations, rendered by the shell's own renderer — this eval holds:

  1. a stood-by `station.publish … dry=yes` on a cell without consent prints ONE line
     `standby · <reason id> · <detail>`: no `✓`, the reason id and the detail both shown;
  2. an ok result still renders as before (`✓ <status>`) and a status-only stop word renders its
     line too;
  3. a `station.air.ls` row prints its `reason` — first among its fields — and every row line fits
     the terminal width (it wraps, or drops trailing fields with a `+N more` marker; nothing is cut
     to 20 characters).

Run:  python app/test/cli_standby_render_eval.py     (exit 0 = all pass)
"""
import contextlib
import io
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "test"))
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["COLUMNS"] = "80"

_fails = []
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap:
    lines = []


def _rendered(resp):
    from api.shell import renderer
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        renderer.render(resp)
    return _ANSI.sub("", buf.getvalue())


def main():
    print("=" * 78)
    print("The CLI shows why something did not happen")
    print("=" * 78)
    import workload_conformance_eval as C
    from api.gateway import AkashaGateway
    from lib.akasha.workbench import (provision, workload as W, autorun, llm_pool,
                                      llm_provider as lp, wl_state)
    from lib.akasha.concepts.society import SocietyConcept

    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "500"
    lp._METER.clear(); lp._METER_LOADED = True; lp._NEXT_OK.clear()
    lp._FREE_TIER["mistral"]["min_interval"] = 0.0
    vault = {}
    llm_pool.set_pool_store(lambda kk: vault.get(kk), lambda kk, d: vault.__setitem__(kk, dict(d)))
    llm_pool._MEM.clear()

    k = C._cell(_Cap())
    provision.provision_workloads(k)
    gw = AkashaGateway(kernel_client=k)

    def cli(cmd):
        return gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                            "params": {"session_token": "admin", "data": {"command": cmd}},
                            "id": "c"}, "local")

    PUB = "station.publish channel=x program=studio_ai/news_show workload=studio_ai/news_show_x"

    def one_line(resp, want_reason):
        res = (resp or {}).get("result") or {}
        out = _rendered(resp)
        check("the publish stood by, with a reason id and a detail",
              res.get("status") == "standby" and res.get("reason") and res.get("detail"),
              "status=%s reason=%s detail=%r" % (res.get("status"), res.get("reason"),
                                                 str(res.get("detail"))[:60]))
        check("…the gate that stopped it is %s" % want_reason, want_reason in str(res.get("reason")),
              str(res.get("reason")))
        lines = [l for l in out.splitlines() if l.strip()]
        check("it renders ONE line `standby · <reason> · <detail>`, with no ✓",
              len(lines) == 1 and lines[0].strip().startswith("standby · ") and "✓" not in out,
              repr(out[:160]))
        check("…carrying the reason id verbatim", str(res.get("reason")) in out, repr(out[:160]))
        check("…and the detail", " ".join(str(res.get("detail")).split())[:40] in out, repr(out[:200]))

    print("\n  ── 1a. a stood-by `station.publish … dry=yes`, through sys.cli_exec ──")
    one_line(cli(PUB + " dry=yes"), "waiting_source")

    # Seal one news-show turn, so the publish passes its first gate (something to post) and stops
    # at a later gate.
    _gen = lp.generate
    lp.generate = lambda *a, **kw: "Here is the news, in my own words."
    wl_state.last_effect_at = lambda *_a, **_kw: 0.0
    news = W.by_key(k, "studio_ai/news_show")
    gid, space = W.society_of(news)
    for _i in (1, 2):
        for m, d in (("kernel.memory.define",
                      {"name": "neta:item:cs%d" % _i, "scope": "universal",
                       "description": "A lab published open model number %d today." % _i}),
                     ("set.add", {"name": (news.get("pins") or {}).get("item_set"),
                                  "id": "neta:item:cs%d" % _i})):
            k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": d}, "id": "s"}, "local")
    sc = SocietyConcept(k.manager.get_session("system.broadcaster"))
    st = dict((sc.read_autorun(gid, space) or {}).get("state") or {})
    for kk in ("last_run", "retry_at", "retry_count", "breaker"):
        st.pop(kk, None)
    st["boot_pending"] = True
    sc.write_autorun_state(gid, space, st)
    autorun.bench_autorun_tick(k, now=time.time())
    lp.generate = _gen

    print("\n  ── 1b. the same publish on a cell WITHOUT consent, once a turn is sealed ──")
    # `dry=yes` returns the preview BEFORE the consent gate (the station's docstring: the preview
    # an operator wants before consenting), so the consent stop is reached without it. On a cell
    # with no consent the gate refuses first: nothing is posted.
    dry = (cli(PUB + " dry=yes") or {}).get("result") or {}
    check("(a turn is sealed: the dry run now previews a thread)",
          dry.get("status") == "dry_run" and dry.get("count"), str(dry)[:120])
    # The provisioned cell consented; withdraw it, as its creator would, through the same shell.
    wd = (cli("society.public group=%s space=%s open=no" % (gid, space)) or {})
    from lib.akasha.api import gate as _gate
    check("(consent withdrawn: the public Set no longer holds %s/%s)" % (gid, space),
          not _gate._FACTS.has(_gate.SET_PUBLIC, "%s/%s" % (gid, space)), str(wd)[:160])
    resp = cli(PUB)
    one_line(resp, "no_consent")

    print("\n  ── 2. an ok result is unchanged; a status-only stop still says so ──")
    check("`{status: ok}` still renders `✓ ok`",
          _rendered({"result": {"status": "ok"}}).strip() == "✓ ok")
    check("`{status: refused}` with no reason renders `refused · - · -`, not a tick",
          _rendered({"result": {"status": "refused"}}).strip() == "refused · - · -")

    print("\n  ── 3. `station.air.ls` rows show their reason and fit the terminal ──")
    rows_resp = cli("station.air.ls name=studio_ai limit=20")
    rows = ((rows_resp or {}).get("result") or {}).get("aired") or []
    check("the bench has rows to show", bool(rows), str(rows_resp)[:120])
    # a row the way the X workload's stand-by writes it: aired=0 with a reason
    rows_resp = {"result": {"aired": [dict(rows[0] if rows else {}, aired=0,
                                           reason="station:reason:no_consent",
                                           obs="wb:studio_ai:aired:999")] + rows[:3],
                            "count": 1 + len(rows[:3])}}
    out = _rendered(rows_resp)
    width = int(os.environ["COLUMNS"])
    body = [l for l in out.splitlines() if l.strip() and not l.startswith("───")]
    check("the stood-by row's reason is printed", "reason=station:reason:no_consent" in out,
          repr(out[:300]))
    check("…as the FIRST field after the row's head (why before what)",
          any(re.search(r"^\s+\S.*?\s{2}reason=station:reason:no_consent", l) for l in body)
          or any(l.strip().startswith("reason=station:reason:no_consent") for l in body),
          repr([l for l in body if "no_consent" in l][:1]))
    check("every row line fits the %d-column terminal (wrapped, not truncated)" % width,
          all(len(l) <= width for l in body), str(max((len(l) for l in body), default=0)))
    check("no field is cut to 20 characters any more (a full `program=` value is shown)",
          "program=" + str((rows[0] if rows else {}).get("program") or "") in out or not rows,
          repr(out[:300]))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a stand-by renders `status · reason · detail` on one line through the real "
          "command path, ok results are unchanged, and a run row shows its reason within the "
          "terminal width.")
    sys.exit(0)


if __name__ == "__main__":
    main()
