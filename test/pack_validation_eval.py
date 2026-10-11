#!/usr/bin/env python3
"""
The ontology is loaded AS WRITTEN or refused — never repaired (the purge order, 3 October §3).

The rules are the application's, declared in `ontology/<pack>/canon.json` under `"rules"`. The REAL
loader runs over a small ontology of this eval's own (`AKASHA_PROJECT_DIR`), on a real cell:

  §1  a pack that keeps every rule loads; a pack that breaks one is REFUSED whole — one
      `[onto] pack refused pack=… rule=… entry=… at=<file>:<line> need=…` line naming the rule and the
      FIRST offending entry, none of its atoms written, no sentinel, `refused=1` on the atoms line.
  §2  nothing missing is written in its place: the refused pack's required link does not appear
      anywhere, and no canon pass runs (`[onto] canon` is never logged).
  §3  the author fixes the pack (adds the link) → the next boot loads it, unasked.
  §4  `in_set` rules hold the same way; `depth` and `except` narrow the subjects.
  §5  a malformed rule is reported once (`[onto] rule ignored … reason=…`) and not applied.
  §6  `validate_pack` alone (no kernel): the first breach is the first in file / line order.

Run:  python test/pack_validation_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Log(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, rec):
        self.lines.append(rec.getMessage())


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


RULES = [
    {"id": "method-binds-a-product", "every": "evm:", "depth": 1, "link": "sys:method_of",
     "to": "evp:"},
    {"id": "product-in-the-superset", "every": "evp:", "depth": 1, "except": ["evp:hub"],
     "in_set": "evp:all"},
    {"id": "", "every": "x:", "link": "r"},                       # malformed: no id
]


def _project(root):
    ont = os.path.join(root, "ontology")
    _write(os.path.join(ont, "p_law", "canon.json"), [json.dumps({"rules": RULES})])
    _write(os.path.join(ont, "p_law", "law.ak"), ['def "evp:hub" "the product hub"'])
    _write(os.path.join(ont, "p_good", "g.ak"), [
        'def "evp:alpha" "Alpha"',
        'set.add name="evp:all" id="evp:alpha"',
        'def "evm:alpha" "how alpha is made"',
        "ln evm:alpha evp:alpha sys:method_of",
        'def "evp:alpha:note" "deeper than depth 1 — not a subject"',
    ])
    _write(os.path.join(ont, "p_bad", "a.ak"), [
        'def "evp:beta" "Beta"',
        'set.add name="evp:all" id="evp:beta"',
    ])
    _write(os.path.join(ont, "p_bad", "b.ak"), [
        'def "evm:beta" "how beta is made — bound to nothing"',
        'def "evm:gamma" "also unbound, but later"',
    ])
    for pn in ("p_law", "p_good", "p_bad"):
        _write(os.path.join(ont, pn, "PACK.json"), [json.dumps({"label": pn})])
    _write(os.path.join(ont, "REGISTRY.json"), [json.dumps({"version": 2, "packages": [
        {"name": "p_law", "autoload": True}, {"name": "p_good", "autoload": True},
        {"name": "p_bad", "autoload": True}]})])
    _write(os.path.join(root, "config", "ontology", "packs.json"), [json.dumps({"load_all": True})])
    return ont


def _line(log, prefix):
    got = [l for l in log.lines if l.startswith(prefix)]
    return got[-1] if got else ""


def main():
    from lib.akasha.ontology import validate as V

    print("\n  ── §6 validate_pack alone ──")
    tmp = tempfile.mkdtemp(prefix="packval_unit_")
    _project(tmp)
    rules = V.declared_rules(os.path.join(tmp, "ontology"))
    bad = sorted(os.path.join(tmp, "ontology", "p_bad", f) for f in ("a.ak", "b.ak"))
    br = V.validate_pack(bad, rules)
    check("§6 the first breach is the first in file / line order (evm:beta, b.ak line 1)",
          br and br["entry"] == "evm:beta" and br["file"] == "b.ak" and br["line"] == 1
          and br["rule"] == "method-binds-a-product", str(br))
    good = [os.path.join(tmp, "ontology", "p_good", "g.ak")]
    check("§6 a keeping pack has no breach", V.validate_pack(good, rules) is None)
    check("§4 `depth` narrows the subjects (evp:alpha:note needs nothing)",
          V.validate_pack(good, rules) is None)
    nos = os.path.join(tmp, "nos.ak")
    _write(nos, ['def "evp:delta" "not in the superset"', 'def "evp:hub" "excepted"'])
    br2 = V.validate_pack([nos], rules)
    check("§4 an `in_set` rule refuses a product left out of its set; `except` spares the hub",
          br2 and br2["rule"] == "product-in-the-superset" and br2["entry"] == "evp:delta", str(br2))
    check("§5 the malformed rule is not among the rules applied", len(rules) == 2, str(len(rules)))
    shutil.rmtree(tmp, ignore_errors=True)

    print("\n  ── the real loader on a real cell ──")
    root = tempfile.mkdtemp(prefix="packval_eval_")
    ont = _project(root)
    os.environ["AKASHA_PROJECT_DIR"] = root
    # the fixture project is the whole project: its application root is its own (empty) `app/`,
    # so the loader reads this ontology only, not the repository's application packs
    os.environ["AKASHA_APP_DIR"] = os.path.join(root, "app")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology import loader as L
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=os.path.join(root, "cell"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    time.sleep(1.0)
    k._boot_daemons_started = True
    log = _Log()
    lg = logging.getLogger("Akasha.Kernel")
    lg.addHandler(log)
    lg.setLevel(logging.INFO)

    def boot():
        log.lines.clear()
        k._schedule_gates = None
        L.boot_load_ontology(k)

    core = k.manager.shared_nucleus.core
    sent_dir = os.path.join(k.base_dir, "central", "sentinels")

    boot()
    refused = [l for l in log.lines if l.startswith("[onto] pack refused")]
    check("§1 one refusal line, naming the pack, the rule, the first entry and where it is",
          len(refused) == 1 and "pack=p_bad" in refused[0] and "rule=method-binds-a-product" in refused[0]
          and "entry=evm:beta" in refused[0] and "at=b.ak:1" in refused[0]
          and "need=ln <entry> evp:* sys:method_of" in refused[0], str(refused))
    check("§1 the atoms line counts it (refused=1)", " refused=1 " in _line(log, "[onto] atoms"),
          _line(log, "[onto] atoms"))
    check("§1 the keeping pack loaded (evm:alpha, evp:alpha are there)",
          bool(core.get_key_by_alias("evm:alpha")) and bool(core.get_key_by_alias("evp:alpha")))
    check("§1 none of the refused pack's atoms were written (not even a.ak's, which kept the rules)",
          not core.get_key_by_alias("evm:beta") and not core.get_key_by_alias("evp:beta"))
    check("§1 the refused pack has no sentinel",
          not [f for f in os.listdir(sent_dir) if f.startswith("p_bad_")], str(os.listdir(sent_dir)))
    check("§2 no canon pass, and nothing missing was written in the pack's place",
          not _line(log, "[onto] canon") and not core.get_key_by_alias("evp:beta"))
    check("§5 the malformed rule is reported, by file and reason",
          any(l.startswith("[onto] rule ignored file=p_law/canon.json") and "reason=id" in l
              for l in log.lines), str([l for l in log.lines if "rule ignored" in l]))

    print("\n  ── §3 the author fixes the pack ──")
    with open(os.path.join(ont, "p_bad", "b.ak"), "a", encoding="utf-8") as fh:
        fh.write('def "evp:gamma" "Gamma"\nset.add name="evp:all" id="evp:gamma"\n'
                 "ln evm:beta evp:beta sys:method_of\nln evm:gamma evp:gamma sys:method_of\n")
    boot()
    check("§3 the next boot loads it, unasked: no refusal, its atoms are there",
          not [l for l in log.lines if l.startswith("[onto] pack refused")]
          and bool(core.get_key_by_alias("evm:beta")) and bool(core.get_key_by_alias("evp:gamma")),
          _line(log, "[onto] atoms"))
    kb, kp = core.get_key_by_alias("evm:beta"), core.get_key_by_alias("evp:beta")
    links = [l for l in (core.get_adjacent_links(kb) or []) if l.get("rel") == "sys:method_of"] if kb else []
    check("§3 …with the link the author wrote", any(l.get("dst") == kp for l in links), str(links)[:160])

    lg.removeHandler(log)
    shutil.rmtree(root, ignore_errors=True)
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a pack that breaks a declared rule is refused whole, by name, with the rule "
          "and its first offending entry; nothing is written in its place; fixed, it loads on the next "
          "boot; a malformed rule is reported and not applied.")
    sys.exit(0)


if __name__ == "__main__":
    main()
