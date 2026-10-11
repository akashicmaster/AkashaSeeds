#!/usr/bin/env python3
"""
mobility_lab.py — the public mobility-consultation deliberation experiment, end-to-end on the CLI.

Runs the whole flow with ONE command, in an isolated throwaway Cell (no daemon, no config):

  survey (mobility feedback)
     └─ delib.aggregate ─▶ stance groups (support / oppose / conditional / neutral)
        └─ delib.to_labo ─▶ concept-labo field (clusters · families · a first-class conclusion)
           └─ delib.to_society ─▶ a society feed (framing + one proposal per stance + the conclusion)

The feedback below is a stand-in for the EU Public Consultations mobility subset (Angst, Zenodo
v0.2.0). Once the `mobility` ontology pack lands, real feedback is projected into a survey the SAME
way (see docs/for-llm/mobility-consultation-ontology-guide.md) and this driver runs unchanged.

  python app/scripts/mobility_lab.py                 # run it, print each stage + the society feed
  python app/scripts/mobility_lab.py --feedback my.jsonl   # {"text": "...", "respondent_id": "..."} per line
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

# A small, realistic MULTI-LOCALE mobility sample — the original language is the primary source
# (一次資料); the English is a secondary translation-projection. {respondent_id, text, text_en, language}.
SAMPLE = [
    {"respondent_id": "r01", "text": "I strongly support expanding the cycling network, it is beneficial for the city.", "language": "en"},
    {"respondent_id": "r02", "text": "Yes, I welcome the low-emission zone. Cleaner air is a good idea.", "language": "en"},
    {"respondent_id": "r03", "text": "A positive step. I endorse the plan to expand bike lanes.", "language": "en"},
    {"respondent_id": "r04", "text": "I oppose the low-emission zone, it is an unfair burden on drivers.", "language": "en"},
    {"respondent_id": "r05", "text": "Against this plan. It is too costly and a real problem for small businesses.", "language": "en"},
    {"respondent_id": "r06", "text": "This could work, but the fees must be phased in with safeguards.", "language": "en"},
    {"respondent_id": "r07", "text": "Ich unterstütze den Ausbau des Radwegenetzes voll und ganz.",
     "text_en": "I fully support expanding the cycling network.", "language": "de"},
    {"respondent_id": "r08", "text": "Je suis contre la zone à faibles émissions, c'est un fardeau injuste.",
     "text_en": "I am against the low-emission zone, it is an unfair burden.", "language": "fr"},
    {"respondent_id": "r09", "text": "Das Fahrrad ist mein tägliches Verkehrsmittel in der Stadt.", "language": "de"},
]

QUESTION = "Should the city expand the low-emission zone and cycling network?"


def load_feedback(path):
    """Read EU-consultation JSONL → records keeping the ORIGINAL as primary + the translation aside.
    {feedback_id|respondent_id, text (original), text_en (optional), language (optional)}."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            original = (o.get("text") or o.get("text_en") or "").strip()
            if not original:
                continue
            rows.append({"respondent_id": str(o.get("respondent_id") or o.get("feedback_id") or f"r{i:04d}"),
                         "text": original, "text_en": (o.get("text_en") or "").strip(),
                         "language": (o.get("language") or "").strip(),
                         # 原票: the complete submission, when the acquisition supplied it
                         "full_text": (o.get("full_text") or o.get("source_text") or o.get("document") or "").strip()})
    return rows


def main():
    ap = argparse.ArgumentParser(description="Run the mobility consultation deliberation pipeline.")
    ap.add_argument("--feedback", help="JSONL of {text|text_en, respondent_id|feedback_id} (default: built-in sample)")
    ap.add_argument("--group", default="civic")
    ap.add_argument("--space", default="hearing")
    ap.add_argument("--question", default=QUESTION)
    ap.add_argument("--consultation", help="alias of a real consultation in the mobility ontology pack "
                    "(e.g. co2cv_2021_public) — loads the pack and uses its framing question")
    ap.add_argument("--pack-dir", default=os.path.join(ROOT, "app", "ontology", "mobility"),
                    help="ontology pack dir to load when --consultation is given")
    ap.add_argument("--emit-projection", metavar="DIR", help="write the visualization payloads "
                    "(clab.project trajectory + clab.rubik + delib.locales JSON) to DIR for the lab / Archives")
    ap.add_argument("--trace", action="store_true",
                    help="echo every operation as a CLI command line (the run's sequence)")
    ap.add_argument("--keep", action="store_true", help="keep the throwaway Cell dir (default: temp)")
    args = ap.parse_args()

    os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
    from lib.akasha.api import client
    base = tempfile.mkdtemp(prefix="akasha_mobility_")
    gw = client.embedded(base, "seeds", load_ontology=False)
    k = gw.kernel_client

    # Convention: FLOW via the CLI (sys.cli_exec — exercises the CLI parser every run),
    # VISUALIZE via RPC (direct method dispatch for the projection payloads). See --trace.
    import shlex as _shlex
    _seq = [0]

    def _trace(kind, line):
        if not args.trace:
            return
        _seq[0] += 1
        disp = line if len(line) <= 116 else line[:113] + "…"
        print(f"  {_seq[0]:>3} ┃ [{kind}] {disp}")

    def _cmd(method, **kw):
        """Build a CLI command line; shlex.quote keeps arbitrary verbatim text (spaces, quotes,
        unicode) intact — the original stays byte-for-byte the primary source."""
        toks = [method] + [f"{k}={_shlex.quote(str(v))}" for k, v in kw.items() if str(v) != ""]
        return " ".join(toks)

    def C(method, **kw):
        """FLOW step — run as a CLI command via sys.cli_exec."""
        line = _cmd(method, **kw)
        _trace("cli", line)
        r = gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                         "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local")
        if "error" in r:
            print(f"  [!] {method}: {r['error'].get('message')}", file=sys.stderr)
        return r.get("result") or {}

    def D(method, data, tok="admin"):
        """VISUALIZE / bootstrap step — direct RPC method dispatch."""
        redacted = {k: ("***" if k == "passphrase" else v) for k, v in (data or {}).items()}
        _trace("rpc", method + " " + " ".join(f"{k}={str(v)[:32]}" for k, v in redacted.items()))
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok, "data": data}, "id": "m"}, "local")
        if "error" in r:
            print(f"  [!] {method}: {r['error'].get('message')}", file=sys.stderr)
        return r.get("result") or {}

    def cli(line, tok="admin"):      # raw CLI line (ontology pack load; summarized in trace)
        return gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                            "params": {"session_token": tok, "data": {"command": line}}, "id": "c"}, "local")

    feedback = None if args.feedback else SAMPLE     # a --feedback file streams via io.ingest (§below)
    GID, SPACE = args.group, args.space

    # 0) genesis + provision a coworking society with an owned moderator cast
    D("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})
    cortex = k.manager.get_session("admin").local_cortex

    # 0b) optionally load the real mobility ontology pack and target a real consultation
    question = args.question
    lineage = ""
    if args.consultation:
        import glob as _glob
        atoms, links = [], []          # two-pass: create all atoms/sets before any cross-file link
        for ak in sorted(_glob.glob(os.path.join(args.pack_dir, "*.ak"))):
            if os.path.basename(ak) == "_lexicon.ak":
                continue
            for ln in open(ak, encoding="utf-8"):
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                (links if ln.startswith("ln ") else atoms).append(ln)
        for ln in atoms + links:
            cli(ln)
        if args.trace:
            from collections import Counter
            verbs = Counter(l.split(" ", 1)[0] for l in atoms + links)
            print(f"  {'—':>3} ┃ [pack load] app/ontology/mobility → "
                  + ", ".join(f"{v}×{n}" for v, n in sorted(verbs.items())))
        ckey = cortex.resolve_alias(f"consultation:{args.consultation}") or cortex.resolve_alias(args.consultation)
        if not ckey:
            print(f"  [!] consultation '{args.consultation}' not found in {args.pack_dir}", file=sys.stderr)
            sys.exit(2)
        desc = (cortex.get_chunk(ckey) or "").strip()
        question = desc.split(": ", 1)[1] if ": " in desc else desc      # the ASK after the framing prefix

        # lineage (traceability): consultation → initiative → topic, resolved from the loaded catalog
        def _alias(key):
            al = (cortex.get_aliases_by_key(key) or []) if key else []
            return next((a for a in al if ":" in a), al[0] if al else "")
        def _first_dst(key, rel):
            for l in (cortex.get_adjacent_links(key, rel) or []):
                if isinstance(l, dict):
                    return l.get("dst")
                if isinstance(l, (list, tuple)) and l:
                    return l[0]
            return ""
        init = _first_dst(ckey, "sys:part_of")
        topic = _first_dst(init, "ctx:topic") if init else ""
        lineage = " → ".join(a for a in (_alias(topic), _alias(init), f"consultation:{args.consultation}") if a)

    _src = f"file:{os.path.basename(args.feedback)}" if args.feedback else f"{len(SAMPLE)} sample responses"
    print(f"\n  Mobility consultation · group={GID} space={SPACE} · {_src}")
    if args.consultation:
        print(f"  consultation: {args.consultation}"
              f"{('   (' + lineage + ')') if lineage else ''}")
        print(f"  question    : {question}")
    print("  " + "-" * 66)

    # ── BOOTSTRAP (via RPC) — group provisioning (grp.* are core positional CLI commands) ──
    D("grp.new", {"group_id": GID, "admin_id": "admin"})
    D("grp.add", {"group_id": GID, "member_id": "admin"})

    # ── FLOW (via CLI) — the deliberation pipeline as CLI commands (concept ops, key=value) ──
    C("society.new", group=GID, space=SPACE, topic="urban mobility", kind="cowork")
    cast_id = C("cast.new", name="Moderator", identity="the consultation moderator").get("cast_id")
    C("cast.publish", group=GID)
    C("society.join", group=GID, space=SPACE, cast=cast_id)

    # 1) survey + multi-locale ingest
    sid = C("survey.new", title=f"Consultation — {args.consultation or 'city mobility'}").get("survey_id")
    C("survey.q.add", text=question, qtype="free_text")
    if args.feedback:
        # real data → the GENERAL import pipeline: io.ingest routes the JSONL into delib's import
        # contract (CLI-native, path-based, model-agnostic). One command, any size.
        fpath = os.path.abspath(args.feedback)
        C("io.allow", dir=os.path.dirname(fpath))
        fed = C("io.ingest", model="delib", into=sid, path=fpath)
    else:
        # built-in sample → one delib.feed CLI command per record (the per-record flow demo)
        fed = {"count": 0, "by_language": {}, "translated": 0}
        _CAP = 6                       # cap the feed lines shown in --trace (still runs all)
        for i, rec in enumerate(feedback):
            if args.trace and i == _CAP and len(feedback) > _CAP:
                print(f"  {'…':>3} ┃ [cli] delib.feed × {len(feedback) - _CAP} more")
            _save, args.trace = args.trace, (args.trace and i < _CAP)
            r = C("delib.feed", survey=sid, text=rec["text"], text_en=rec.get("text_en", ""),
                  language=rec.get("language", ""), respondent=rec.get("respondent_id", f"r{i:04d}"),
                  full_text=rec.get("full_text", ""))
            args.trace = _save
            lang = r.get("language", "und")
            fed["count"] += 1
            fed["by_language"][lang] = fed["by_language"].get(lang, 0) + 1
            fed["translated"] += 1 if r.get("translated") else 0
    print(f"  survey    : {sid[:12]}…  ({fed.get('count')} responses · locales {fed.get('by_language')} · "
          f"{fed.get('translated')} translation-projections)")

    # 2) aggregate (language-aware) → project (competing trajectories) → deliberate
    agg = C("delib.aggregate", survey=sid)
    print(f"  aggregate : {agg.get('breakdown')}  net={agg.get('net_score'):+.2f}  "
          f"(via translation: {agg.get('via_translation')}, floored: {agg.get('floored')})")
    labo = C("delib.to_labo", agg=agg.get("aggregation_id"))
    verdicts = [c["judgement"] for c in labo.get("conclusions", [])]
    print(f"  to_labo   : field {labo.get('labo_id')}")
    print(f"              {len(labo.get('trajectories', []))} competing trajectories · "
          f"conclusions {verdicts} coexist · tension={bool(labo.get('tension'))}")
    out = C("delib.to_society", labo=labo.get("labo_key"), society=SPACE, group=GID,
            cast=cast_id, space=SPACE)
    print(f"  to_society: {len(out.get('posted', []))} atoms posted into {GID}/{SPACE}")
    out["labo_key"] = labo.get("labo_key")

    # 2b) emit the visualization payloads for the lab / Archives (topology + locale quantities)
    if args.emit_projection:
        import json as _json
        os.makedirs(args.emit_projection, exist_ok=True)
        labo_key = labo.get("labo_key")
        payloads = {
            "clab_project_trajectory.json": D("clab.project", {"target": labo_key, "mode": "trajectory"}),
            "clab_rubik.json":              D("clab.rubik", {"target": labo_key}),
            "delib_locales.json":           D("delib.locales", {"agg": agg.get("aggregation_id")}),
            "delib_voices.json":            D("delib.voices",  {"agg": agg.get("aggregation_id")}),
        }
        for fn, payload in payloads.items():
            with open(os.path.join(args.emit_projection, fn), "w", encoding="utf-8") as fh:
                _json.dump(payload, fh, ensure_ascii=False, indent=2)
        pr = payloads["clab_project_trajectory.json"]
        print(f"  emit      : {args.emit_projection}/  "
              f"(trajectory: {len(pr.get('trajectories', []))} lanes / {len(pr.get('nodes', []))} nodes · "
              f"rubik: {len(payloads['clab_rubik.json'].get('pages', []))} pages · locales · "
              f"voices: {payloads['delib_voices.json'].get('count', 0)})")

    # 3) show the society feed as a moderator/citizen would read it (CLI read)
    print("\n  Society feed (civic/hearing):")
    print("  " + "-" * 66)
    for m in C("society.feed", group=GID, space=SPACE, limit=50).get("messages", []):
        who = (m.get("cast_name") or "?")[:10]
        print(f"    {who:>10} │ {m.get('text', '')}")

    # 4) show the conclusion(s) side by side (non-forcing — all polarities kept) (CLI read)
    cc = C("delib.show", labo=out.get("labo_key")).get("conclusions", {})
    print("\n  Concept-labo conclusion(s):")
    for c in cc.get("conclusions", []):
        print(f"    · [{c.get('polarity')}] {c.get('rationale')}")

    print(f"\n  Done. Cell: {base if args.keep else '(temp — discarded)'}\n")
    if not args.keep:
        import shutil
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
