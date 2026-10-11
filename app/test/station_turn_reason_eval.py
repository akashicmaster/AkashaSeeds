#!/usr/bin/env python3
"""
EVERY TURN THAT DOES NOT AIR NAMES ITS REASON — the application half of the 09-25 incident.

On 2026-09-25 13:36–17:00 JST the news show ran ~160 PAID airings that aired nothing — pool 498/500,
the station dark until the pool's day turned — and every run record read `reason=''`. Two sides
lost the reason. The platform dropped what the op returned before the run record (D10, theirs).
And this side had turns that never returned a vocabulary id in the first place:

  · four exits returned a SENTENCE as the reason, wrote no record, and logged nothing;
  · every turn that RAISED returned nothing at all — and a turn that raised AFTER the model call
    was a paid failure whose only trace was the bill.

Both are closed by routing every non-aired exit through ONE function, which logs one line, records
the stand-by on the bench, and returns a vocabulary id. This eval holds that, on a real dispatcher,
by driving each exit — including the ones that only exist when something throws:

  A  no declaration                 not_declared   refused   no bench, so no record
  B  a role nobody declared         not_said
  C  the model answers nothing      no_text        called=yes
  D  raises BEFORE the model call   turn_error     called=no    (with a traceback in the log)
  E  raises AFTER the model call    turn_error     called=YES   — the incident's shape
  F  raises AFTER the line is said  status aired, NOT a stand-by — the record must match the feed
  G  the feed refuses the line      not_said       called=yes, the feed's own error in `detail`
  H  a republish that raises        turn_error     on `station.publish`

and, for every one of them: the reason is a `station:reason:*` id that EXISTS in the station pack,
`detail` is not empty, and exactly one `[station] standby` (or `[station.publish] standby`) line
carries it. A static half checks no bare stand-by dict survives anywhere in the four functions.

Run:  python app/test/station_turn_reason_eval.py     (exit 0 = all pass)
"""
import ast
import hashlib
import json
import logging
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

SRC = os.path.join(ROOT, "app", "concepts", "bench_station.py")
VOCAB_PACK = os.path.join(ROOT, "app", "ontology", "station", "programme_state.ak")

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _defined_reasons():
    ids = set()
    for line in open(VOCAB_PACK, encoding="utf-8"):
        m = re.match(r'\s*def\s+"(station:reason:[a-z0-9_]+)"', line)
        if m:
            ids.add(m.group(1))
    return ids


class _Lines(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def standby(self):
        return [r for r in self.records
                if "] standby " in r.getMessage() and ("[station]" in r.getMessage()
                                                     or "[station.publish]" in r.getMessage())]


def static_half():
    print("\n  ── static: no bare stand-by survives ──")
    src = open(SRC, encoding="utf-8").read()
    tree = ast.parse(src)
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    bare, literal_reasons = [], []
    for name in ("op_air_turn", "_air_turn", "op_publish", "_publish"):
        fn = fns.get(name)
        check("`%s` exists" % name, fn is not None)
        if not fn:
            continue
        for n in ast.walk(fn):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
                for k, v in zip(n.value.keys, n.value.values):
                    if (isinstance(k, ast.Constant) and k.value == "status"
                            and isinstance(v, ast.Constant) and v.value in ("standby", "refused")):
                        bare.append("%s:%d" % (name, n.lineno))
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr in ("_stood_by", "_pub_standby")):
                reason = next((kw.value for kw in n.keywords if kw.arg == "reason"), None)
                if reason is None and n.func.attr == "_pub_standby" and len(n.args) >= 4:
                    reason = n.args[3]
                if isinstance(reason, ast.Constant):
                    literal_reasons.append("%s:%d" % (name, n.lineno))
    check("no function returns a bare {'status': 'standby'|'refused'} dict — every exit goes "
          "through the one stand-by function", not bare, str(bare))
    check("… and no stand-by is given a string literal for its reason — only a REASON_* id",
          not literal_reasons, str(literal_reasons))


def main():
    static_half()

    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.workbench import llm_provider
    from lib.akasha.workbench import workload as _W
    from lib.akasha.workbench.workload_provision import provision
    from lib.akasha.workbench.workload import client_of
    from app.concepts import bench_station as BS

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_reason_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(client, method, data):
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": client, "data": data}, "id": "t"}, "local")

    def res(r):
        return (r or {}).get("result") or {}

    cfg = next(x for x in _W.declarations(None) if x.get("workflow") == "thinkers_shelf")
    program = _W.key(cfg)
    gid, _ = _W.society_of(cfg)
    provision(d, cfg, note=lambda m: None)
    client = client_of(cfg)
    bench = _W.bench_slug(cfg)
    d("admin", "kernel.memory.define",
      {"name": "shelf:test:passage:reason", "scope": "universal",
       "description": json.dumps({"book": "B", "section": "S", "text": "PRINTED.",
                                  "anchor": {"page": "i"}})})

    defined = _defined_reasons()

    def R(name):
        # the id by NAME, not by attribute: the eval must run against an op that predates these
        # constants and fail on what the turn DID, not crash on a missing name
        return getattr(BS, "REASON_" + name, "station:reason:" + name.lower())
    lines = _Lines()
    lg = logging.getLogger("Harmonia.Concept.BenchStation")
    lg.addHandler(lines)
    lg.setLevel(logging.DEBUG)

    calls = []

    def gen_ok(provider, model, system, user, timeout=60.0):
        calls.append(1)
        return "A line."

    real_gen = llm_provider.generate
    llm_provider.generate = gen_ok

    def turn(role, tag, program_=None):
        before = len(lines.standby())
        r = res(d(client, "station.air.turn", {"program": program_ or program, "role": role,
                                             "source": "shelf:test:passage:reason",
                                             "provider": "mistral", "turn": tag}))
        return r, lines.standby()[before:]

    def recorded(tag):
        rows = res(d("admin", "station.air.ls", {"name": bench})).get("aired") or []
        return [x for x in rows if x.get("turn") == tag]

    def holds(case, r, new, want_reason, want_called, want_record, tag):
        reason = r.get("reason", "")
        check("%s: the turn stands by with the id `%s`" % (case, want_reason),
              reason == want_reason, "got %r status=%s" % (reason, r.get("status")))
        check("%s: … an id the station vocabulary DEFINES" % case, reason in defined, reason)
        check("%s: … with a non-empty `detail` saying what happened" % case,
              bool(str(r.get("detail") or "").strip()), repr(r.get("detail"))[:90])
        check("%s: … and says whether a model call had gone out (called=%s)"
              % (case, "yes" if want_called else "no"),
              bool(r.get("called")) is want_called, str(r.get("called")))
        mine = [x for x in new if ("reason=%s " % reason) in x.getMessage()]
        check("%s: exactly ONE standby line carries that id" % case, len(mine) == 1,
              " | ".join(x.getMessage()[:100] for x in new) or "no line")
        if want_record:
            rec = recorded(tag)
            check("%s: … and it is RECORDED on the bench with the reason on the observation" % case,
                  len(rec) == 1 and str(rec[0].get("aired")) in ("0", "False")
                  and rec[0].get("reason") == reason, str(rec)[:120])
        return mine

    try:
        print("\n  ── A · no declaration ──")
        r, new = turn("Reader", "a#1", program_="studio_ai/does_not_exist")
        holds("A", r, new, R("NOT_DECLARED"), False, False, "a#1")
        check("A: status stays `refused` — the platform branches on nothing new",
              r.get("status") == "refused", r.get("status"))

        print("\n  ── B · a role nobody declared ──")
        r, new = turn("Nobody", "b#1")
        holds("B", r, new, R("NOT_SAID"), False, True, "b#1")

        print("\n  ── C · the model answers nothing ──")
        llm_provider.generate = lambda *a, **kw: ""
        r, new = turn("Listener", "c#1")
        check("C: the turn stands by with a provider-side id (no_text / 429 / a ceiling)",
              r.get("reason") in (R("NO_TEXT"), R("PROVIDER_429"),
                                  R("BUDGET_CALLS"), R("BUDGET_TOKENS")),
              r.get("reason"))
        holds("C", r, new, r.get("reason"), True, True, "c#1")
        llm_provider.generate = gen_ok

        print("\n  ── D · raises BEFORE the model call ──")
        # Saved from the class DICT: read through the class, a staticmethod comes back as a plain
        # function, and putting THAT back makes it an instance method that is handed `self` — every
        # later turn then dies of a TypeError. (It did, the first time; the wrapper turned each of
        # those into a recorded `turn_error` with the TypeError in `detail`, which is the feature
        # demonstrating itself on the eval's own mistake.)
        real_contract = BS.BenchStationConcept.__dict__["_contract"]
        BS.BenchStationConcept._contract = staticmethod(
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("contract unreadable")))
        n0 = len(calls)
        r, new = turn("Listener", "d#1")
        BS.BenchStationConcept._contract = real_contract
        mine = holds("D", r, new, R("TURN_ERROR"), False, True, "d#1")
        check("D: no model call was made", len(calls) == n0, "calls=%d" % (len(calls) - n0))
        check("D: the exception's class and message are in `detail`",
              "RuntimeError" in str(r.get("detail")) and "contract unreadable" in str(r.get("detail")),
              str(r.get("detail"))[:80])
        check("D: the log line carries the TRACEBACK, so the cause is found from the log alone",
              bool(mine) and mine[0].exc_info is not None, str(bool(mine and mine[0].exc_info)))

        print("\n  ── E · raises AFTER the model call — the incident's shape ──")
        real_turn_no = BS.BenchStationConcept._turn_no
        BS.BenchStationConcept._turn_no = lambda self, *a, **kw: (_ for _ in ()).throw(
            KeyError("turn counter"))
        n0 = len(calls)
        r, new = turn("Commentator", "e#1")
        BS.BenchStationConcept._turn_no = real_turn_no
        holds("E", r, new, R("TURN_ERROR"), True, True, "e#1")
        check("E: the model call DID go out — this is the paid failure that used to leave no trace",
              len(calls) == n0 + 1, "calls=%d" % (len(calls) - n0))
        check("E: … and its line is a WARNING, not an INFO a busy log would bury",
              bool(new) and new[-1].levelno >= logging.WARNING, logging.getLevelName(new[-1].levelno)
              if new else "-")

        print("\n  ── F · raises AFTER the line is on the feed ──")
        real_seal = BS.BenchStationConcept._seal
        BS.BenchStationConcept._seal = lambda self, *a, **kw: (_ for _ in ()).throw(
            OSError("seal store"))
        r, new = turn("Reader", "f#1")
        BS.BenchStationConcept._seal = real_seal
        check("F: it is reported AIRED — the line is on the feed, and saying otherwise would make "
              "the record and the feed disagree", r.get("status") == "aired", json.dumps(r)[:120])
        check("F: … with the failure beside it", "OSError" in str(r.get("detail")),
              str(r.get("detail"))[:80])
        check("F: … and NO stand-by is recorded for a turn that aired",
              not [x for x in recorded("f#1") if str(x.get("aired")) in ("0", "False")],
              str(recorded("f#1"))[:100])
        check("F: … nor logged as one", not new, " | ".join(x.getMessage()[:80] for x in new))

        print("\n  ── G · the feed refuses the line ──")
        real_say = BS.BenchStationConcept._say
        BS.BenchStationConcept._say = lambda self, *a, **kw: {"error": "ValueError: space closed"}
        r, new = turn("Listener", "g#1")
        BS.BenchStationConcept._say = real_say
        holds("G", r, new, R("NOT_SAID"), True, True, "g#1")
        check("G: the feed's OWN error is in `detail`, on the same line as the reason",
              "space closed" in str(r.get("detail")) and bool(new)
              and "space closed" in new[-1].getMessage(), str(r.get("detail"))[:80])

        print("\n  ── H · a republish that raises ──")
        real_latest = BS.BenchStationConcept._latest_turn
        BS.BenchStationConcept._latest_turn = lambda self, *a, **kw: (_ for _ in ()).throw(
            LookupError("feed unreadable"))
        before = len(lines.standby())
        r = res(d("admin", "station.publish", {"channel": "x", "program": program, "dry": "yes"}))
        new = lines.standby()[before:]
        BS.BenchStationConcept._latest_turn = real_latest
        check("H: a publish that raised stands by with `turn_error`",
              r.get("reason") == R("TURN_ERROR") and r.get("reason") in defined,
              json.dumps(r)[:120])
        check("H: … the exception in `detail`", "LookupError" in str(r.get("detail")),
              str(r.get("detail"))[:80])
        check("H: … and one `[station.publish] standby` line with its traceback",
              len(new) == 1 and "[station.publish]" in new[0].getMessage()
              and new[0].exc_info is not None, " | ".join(x.getMessage()[:80] for x in new))
    finally:
        llm_provider.generate = real_gen
        lg.removeHandler(lines)

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — every turn that does not air names its reason: a vocabulary id the "
          "station pack defines, a `detail` saying what happened, whether a model call had gone "
          "out, ONE log line at the place that decided it, and a record on the bench where there "
          "is one. That holds for the exits that only exist when something THROWS — before the "
          "model call, after it, and in a republish — and a turn whose line is already on the feed "
          "is reported aired rather than recorded as a stand-by it was not.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
