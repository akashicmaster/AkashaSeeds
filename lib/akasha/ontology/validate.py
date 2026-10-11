"""
Pack validation — a pack is loaded AS WRITTEN or refused; the loader never repairs it (the purge order,
3 October §3).

The rules are the application's, declared as data in `ontology/<pack>/canon.json` under `"rules"`
(every pack's lists are unioned). The platform names no domain, no namespace and no relation here: it
evaluates the rule shapes below against the statements a pack itself contains, BEFORE anything of that
pack is written. A pack that breaks a rule is refused whole, by name, with the rule id and the first
offending entry (`[onto] pack refused pack=… rule=… entry=… at=<file>:<line> need=…`), writes nothing
and gets no sentinel, so the next boot asks again. Nothing missing is ever written in its place.

A rule:

    {"id": "<rule id>",                  required — what the refusal line names
     "every": "<name prefix>",           required — the subjects: every name the pack DEFINES (`def`)
                                         that starts with this prefix …
     "depth": <n>,                       … optionally with exactly n `:` separators in the name
     "except": ["<name>", …],            … optionally less these names
     and ONE requirement:
     "link": "<relation>", "to": "<target prefix>"   the pack links the subject `ln <subject> <dst>
                                                      <relation>` (to a dst starting with `to`, if given)
     "in_set": "<set name>"                          the pack adds the subject: `set.add name=<set>
                                                      id=<subject>`}

A rule that is not of this shape is reported once (`[onto] rule ignored file=… rule=… reason=…`) and
not applied — a declaration error is the declarer's, and refusing every pack for it would be worse.
Validation streams each file once and keeps only what the rules can ask about.
"""
import glob
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("Akasha.Kernel")

RULES_FILE = "canon.json"


def _rule_problem(r: Any) -> str:
    if not isinstance(r, dict):
        return "not an object"
    if not str(r.get("id") or "").strip():
        return "id"
    if not isinstance(r.get("every"), str) or not r.get("every"):
        return "every"
    if "depth" in r and not isinstance(r.get("depth"), int):
        return "depth"
    if "except" in r and not isinstance(r.get("except"), list):
        return "except"
    has_link, has_set = bool(r.get("link")), bool(r.get("in_set"))
    if has_link == has_set:
        return "requirement (exactly one of link / in_set)"
    if has_link and not isinstance(r.get("link"), str):
        return "link"
    if "to" in r and not isinstance(r.get("to"), str):
        return "to"
    if has_set and not isinstance(r.get("in_set"), str):
        return "in_set"
    return ""


def declared_rules(ontology_dir: str) -> List[Dict[str, Any]]:
    """Every well-formed rule in `<ontology_dir>/*/canon.json`, in file order."""
    out: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(ontology_dir, "*", RULES_FILE))):
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, ValueError) as exc:
            logger.warning("[onto] rule ignored file=%s rule=- reason=unreadable detail=%s",
                           os.path.relpath(path, ontology_dir), exc)
            continue
        for r in (doc.get("rules") or []) if isinstance(doc, dict) else []:
            bad = _rule_problem(r)
            if bad:
                logger.warning("[onto] rule ignored file=%s rule=%s reason=%s",
                               os.path.relpath(path, ontology_dir),
                               (r.get("id") if isinstance(r, dict) else "-") or "-", bad)
                continue
            out.append(dict(r, _file=os.path.relpath(path, ontology_dir)))
    return out


def _subject_of(rule: Dict[str, Any], name: str) -> bool:
    if not name.startswith(rule["every"]):
        return False
    if "depth" in rule and name.count(":") != rule["depth"]:
        return False
    return name not in (rule.get("except") or [])


def _need(rule: Dict[str, Any]) -> str:
    if rule.get("link"):
        return "ln <entry> %s* %s" % (rule.get("to") or "", rule["link"])
    return "set.add name=%s id=<entry>" % rule["in_set"]


def validate_pack(ak_files: List[str], rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """None when the pack keeps every rule, else the FIRST breach: {rule, entry, file, line, need}.

    "First" is in file order, then line order — the entry an author reads first. One streamed read
    per file; held: the subjects (name → where it was defined) and the satisfied (rule, subject) pairs."""
    if not rules:
        return None
    from lib.akasha.ontology.loader import parse_ak_line
    subjects: Dict[str, tuple] = {}            # name → (file, line), first definition
    order: List[str] = []
    met: set = set()                           # (rule index, subject name)
    for path in sorted(ak_files):
        try:
            fh = open(path, encoding="utf-8", errors="ignore")
        except OSError:
            continue
        with fh:
            for n, raw in enumerate(fh, 1):
                st = parse_ak_line(raw)
                if not st:
                    continue
                m, p = st["method"], st["params"]
                if m == "kernel.memory.define":
                    nm = str(p.get("name") or "").strip()
                    if nm and nm not in subjects and any(_subject_of(r, nm) for r in rules):
                        subjects[nm] = (os.path.basename(path), n)
                        order.append(nm)
                elif m == "kernel.memory.link":
                    src, dst, rel = (str(p.get(k) or "").strip() for k in ("src", "dst", "rel"))
                    for i, r in enumerate(rules):
                        if (r.get("link") == rel and _subject_of(r, src)
                                and dst.startswith(r.get("to") or "")):
                            met.add((i, src))
                elif m == "set.add":
                    sname, sid = str(p.get("name") or "").strip(), str(p.get("id") or "").strip()
                    for i, r in enumerate(rules):
                        if r.get("in_set") == sname and _subject_of(r, sid):
                            met.add((i, sid))
    for nm in order:
        for i, r in enumerate(rules):
            if _subject_of(r, nm) and (i, nm) not in met:
                f, line = subjects[nm]
                return {"rule": r["id"], "entry": nm, "file": f, "line": line, "need": _need(r),
                        "declared_in": r.get("_file")}
    return None
