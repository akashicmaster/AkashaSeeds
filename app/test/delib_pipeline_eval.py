#!/usr/bin/env python3
"""
Deliberation bridge eval — multi-locale survey → aggregation → concept-labo → society, on the CLI.

`delib` flows a Survey of collected public feedback through the Aggregation model (stance groups),
projects it into a Concept-Laboratory field, and posts the outcome into a Society. This eval is also
the MULTI-LOCALE + DISAGREEMENT-AS-DATA validation of the public mobility-consultation experiment:

  • Multi-locale: the ORIGINAL language is the primary-source atom (一次資料); the English machine-
    translation is a linked, secondary provenance=inferred PROJECTION. A non-English response is
    classified via its translation; one with no translation is kept HONESTLY as `untranslated` — not
    forced into English, and NOT asserted to be neutral (a reading we did not make). It forms no
    conclusion. (A German "Ich unterstütze…" with no English keywords would misfire if read directly;
    via its translation it lands as support — the whole point of keeping the original as the operand.)
  • Disagreement-as-data: every substantial stance becomes a COMPETING TRAJECTORY that shares the
    initial family and closes in its OWN first-class conclusion; a first-class TENSION holds between
    support and oppose. Conclusions COEXIST (the non-forcing principle), never collapsed to one verdict.

Deterministic sample (9 responses): support 4 (3 en + 1 de-via-translation) · oppose 3 (2 en +
1 fr-via-translation) · conditional 1 (en) · untranslated 1 (de, no translation — kept honestly, not neutral).

Run:  python app/test/delib_pipeline_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []

# (respondent_id, original_text, english_translation|"", language) — the original is the operand.
RECORDS = [
    ("r01", "I strongly support expanding the cycling network, it is beneficial for the city.", "", "en"),
    ("r02", "Yes, I welcome the low-emission zone. Cleaner air is a good idea.", "", "en"),
    ("r03", "A positive step. I endorse the plan to expand bike lanes.", "", "en"),
    ("r04", "I oppose the low-emission zone, it is an unfair burden on drivers.", "", "en"),
    ("r05", "Against this plan. It is too costly and a real problem for small businesses.", "", "en"),
    ("r06", "This could work, but the fees must be phased in with safeguards.", "", "en"),
    # non-English WITH translation → classified via the translation (original stays primary source)
    ("r07", "Ich unterstütze den Ausbau des Radwegenetzes voll und ganz.",
     "I fully support expanding the cycling network.", "de"),
    ("r08", "Je suis contre la zone à faibles émissions, c'est un fardeau injuste.",
     "I am against the low-emission zone, it is an unfair burden.", "fr"),
    # non-English WITHOUT translation → kept honestly as `untranslated` (not forced to English, not neutral)
    ("r09", "Das Fahrrad ist mein tägliches Verkehrsmittel in der Stadt.", "", "de"),
]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_delib_"))
    gw = AkashaGateway(kernel_client=k)

    def D(method, data, tok="admin"):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        if "error" in r:
            print("   [err]", method, r["error"].get("message"))
        return r.get("result") or {}

    D("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})
    cortex = k.manager.get_session("admin").local_cortex

    GID, SPACE = "civic", "hearing"
    D("grp.new", {"group_id": GID, "admin_id": "admin"})
    D("grp.add", {"group_id": GID, "member_id": "admin"})
    D("society.new", {"group": GID, "space": SPACE, "topic": "urban mobility", "kind": "cowork"})
    cast_id = D("cast.new", {"name": "Moderator", "identity": "the consultation moderator"}).get("cast_id")
    D("cast.publish", {"group": GID})
    D("society.join", {"group": GID, "space": SPACE, "cast": cast_id})
    check("provisioned group + society + owned cast", bool(cast_id))

    # ── multi-locale ingestion (original = operand, translation = projection) ────
    sid = D("survey.new", {"title": "Mobility usage in the city"}).get("survey_id")
    D("survey.q.add", {"text": "Should the city expand the low-emission zone and cycling network?",
                       "qtype": "free_text"})
    recs = [{"respondent_id": r, "text": t, "text_en": en, "language": lg} for (r, t, en, lg) in RECORDS]
    ing = D("delib.ingest", {"survey": sid, "records": recs})
    check("ingest: 9 responses across 3 locales (en/de/fr)",
          ing.get("count") == 9 and set(ing.get("languages", [])) == {"en", "de", "fr"}, str(ing.get("by_language")))
    check("ingest: 2 English translation-projections minted (de + fr, not the untranslated de)",
          ing.get("translated") == 2, str(ing.get("translated")))

    # primary source: the original German is the response atom of record (一次資料), tagged de
    resp_keys = cortex.get_collection_members(f"set:survey:{sid}:responses") or []
    de_floor = next((rk for rk in resp_keys if "Das Fahrrad" in (cortex.get_meta(rk) or {}).get("answer", "")), None)
    check("primary source: the untranslated German original is kept verbatim as the response atom",
          bool(de_floor) and "Das Fahrrad" in (cortex.get_chunk(de_floor) or ""))
    lang_links = cortex.get_adjacent_links(de_floor, "delib:in_language") if de_floor else []
    lang_ok = any("language:de" in (cortex.get_aliases_by_key(
        (l.get("dst") if isinstance(l, dict) else l[0])) or []) for l in (lang_links or []))
    check("primary source: response carries delib:in_language → language:de", lang_ok)

    # translation projection: the de-support response links an English, provenance=inferred atom
    de_sup = next((rk for rk in resp_keys if "unterstütze" in (cortex.get_meta(rk) or {}).get("answer", "")), None)
    tr = cortex.get_incoming_links(de_sup, "delib:translates") if de_sup else []
    tr_src = (tr[0].get("src") if isinstance(tr[0], dict) else tr[0][0]) if tr else None
    tmeta = cortex.get_meta(tr_src) or {} if tr_src else {}
    check("translation is a secondary provenance=inferred PROJECTION of the original",
          tmeta.get("provenance") == "inferred" and "support" in (cortex.get_chunk(tr_src) or "").lower())

    # ── aggregate (language-aware) ──────────────────────────────────────────────
    agg = D("delib.aggregate", {"survey": sid})
    bd = agg.get("breakdown", {})
    check("aggregate: breakdown support4 / oppose3 / conditional1 / untranslated1 (de, no translation — NOT neutral)",
          bd.get("support") == 4 and bd.get("oppose") == 3 and bd.get("conditional") == 1
          and bd.get("untranslated") == 1 and "neutral" not in bd,
          str(bd))
    check("aggregate: by_language en6 / de2 / fr1", agg.get("by_language") == {"en": 6, "de": 2, "fr": 1},
          str(agg.get("by_language")))
    check("aggregate: 2 classified via translation, 1 floored (de, no translation)",
          agg.get("via_translation") == 2 and agg.get("floored") == 1,
          f"via={agg.get('via_translation')} floored={agg.get('floored')}")
    agg_id = agg.get("aggregation_id")
    D("agg.open", {"agg_id": agg_id})
    inv = D("agg.list", {})
    check("aggregate: 4 groups recorded (support/oppose/conditional + untranslated held aside)",
          len(inv.get("groups", [])) == 4)

    # ── locales: per-stance translation-reliance feed (the visualization quantity) ──
    loc = D("delib.locales", {"agg": agg_id}).get("by_stance", {})
    check("locales: support stance shows its locale mix incl. the de-via-translation member",
          loc.get("support", {}).get("languages", {}).get("de") == 1
          and loc.get("support", {}).get("via_translation") == 1, str(loc.get("support")))
    check("locales: the de with no translation is kept 'untranslated' (floored, not via_translation, NOT neutral)",
          loc.get("untranslated", {}).get("floored") == 1 and loc.get("untranslated", {}).get("via_translation") == 0
          and "neutral" not in loc,
          str(loc.get("untranslated")))

    # ── to_labo: competing trajectories + coexisting conclusions + tension ───────
    labo = D("delib.to_labo", {"agg": agg_id})
    conclset = {c["judgement"] for c in labo.get("conclusions", [])}
    check("to_labo: 3 COEXISTING conclusions — affirm + negate + mixed (non-forcing)",
          conclset == {"affirm", "negate", "mixed"}, str(sorted(conclset)))
    check("to_labo: 3 competing trajectories (one per substantial stance)",
          len(labo.get("trajectories", [])) == 3, str(len(labo.get("trajectories", []))))
    check("to_labo: a first-class tension between support and oppose", bool(labo.get("tension")))
    labo_key = labo.get("labo_key")
    kinds = D("delib.show", {"labo": labo_key}).get("field", {}).get("by_kind", {})
    check("to_labo: field = shared initial + 3 destination families, 3 clusters, 3 conclusions, ≥1 tension "
          "(untranslated forms NO cluster/conclusion — kept in the initial family as unread input)",
          kinds.get("family") == 4 and kinds.get("cluster") == 3 and kinds.get("conclusion") == 3
          and kinds.get("theory") == 3 and kinds.get("tension", 0) >= 1, str(kinds))
    cc = D("delib.show", {"labo": labo_key}).get("conclusions", {})
    check("to_labo: conclusions provably coexist (compare shows >1 polarity)", cc.get("coexist") is True)

    # ── to_society: post competing readings, kept side by side ───────────────────
    soc = D("delib.to_society", {"labo": labo_key, "society": SPACE, "group": GID, "cast": cast_id, "space": SPACE})
    check("to_society: 3 stance proposals + 3 coexisting readings posted (untranslated is not a stance)",
          soc.get("proposals") == 3 and set(soc.get("conclusions", [])) == {"affirm", "negate", "mixed"},
          str(soc.get("conclusions")))
    feed = D("society.feed", {"group": GID, "space": SPACE, "limit": 50}).get("messages", [])
    readings = [m for m in feed if m.get("text", "").startswith("[Reading ·")]
    coexist_note = [m for m in feed if m.get("text", "").startswith("[Note]")]
    check("to_society: feed shows the competing readings + a coexistence note",
          len(readings) == 3 and len(coexist_note) == 1, f"readings={len(readings)} note={len(coexist_note)}")

    # ── provenance chain ────────────────────────────────────────────────────────
    proj = cortex.get_adjacent_links(agg_id, "delib:projects") or []
    check("provenance: aggregation --delib:projects--> the labo field",
          any((l.get("dst") if isinstance(l, dict) else l[0]) == labo_key for l in proj))

    # ── CLI compatibility (the standing convention: flow via CLI) ───────────────
    # delib.feed must be invokable as a real CLI command string (not RPC-only), incl. a unicode
    # original + a quoted translation carried intact through the shlex tokenizer.
    def CLI(line):
        return gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                            "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local").get("result") or {}
    sid2 = CLI('survey.new title="CLI compat"').get("survey_id")
    CLI(f'survey.q.add survey={sid2} text="expand cycling?" qtype=free_text')
    fed = CLI(f'delib.feed survey={sid2} text="Ich unterstütze den Ausbau voll und ganz." '
              f'text_en="I fully support the expansion." language=de respondent=x1')
    check("CLI compat: delib.feed runs as a CLI command (unicode original + quoted translation)",
          fed.get("status") == "fed" and fed.get("language") == "de" and fed.get("translated") is True, str(fed))

    # ── general import pipeline: io.ingest model=delib (records= + inline text=) ─
    sid3 = CLI('survey.new title="io.ingest"').get("survey_id")
    CLI(f'survey.q.add survey={sid3} text="expand?" qtype=free_text')
    gi = D("io.ingest", {"model": "delib", "into": sid3, "records": [
        {"text": "Je suis contre, c'est injuste.", "text_en": "I am against, it is unfair.", "language": "fr", "respondent_id": "g1"},
        {"text": "I support this fully.", "language": "en", "respondent_id": "g2"}]})
    check("io.ingest: the GENERAL route ingests raw records into delib (any-model import contract)",
          gi.get("count") == 2 and gi.get("by_language") == {"fr": 1, "en": 1} and gi.get("translated") == 1, str(gi))
    gi2 = D("io.ingest", {"model": "delib", "into": sid3, "format": "jsonl",
                          "text": '{"text":"Cleaner air is a good idea.","language":"en","respondent_id":"g3"}'})
    check("io.ingest: inline text= (JSONL upload path) also lands via the same route",
          gi2.get("count") == 1, str(gi2))

    # ── 原票: original FULL TEXT as a first-class atom + the analysis target ─────
    sid4 = CLI('survey.new title="full text"').get("survey_id")
    CLI(f'survey.q.add survey={sid4} text="expand?" qtype=free_text')
    # f1: short feed comment is NEUTRAL, but the full submission is clearly OPPOSE → analysis must
    #     read the FULL text. f2: non-English full text, no authority translation → untranslated.
    ftrec = D("io.ingest", {"model": "delib", "into": sid4, "records": [
        {"text": "See attached submission.", "language": "en", "respondent_id": "f1",
         "full_text": "I strongly oppose this plan; it is an unfair burden and too costly for families."},
        {"text": "Siehe Anhang.", "language": "de", "respondent_id": "f2",
         "full_text": "Ich bin entschieden dagegen. Der Zeitplan ist zu ehrgeizig."}]})
    check("full text: both records import a first-class 原票 atom (with_full_text=2)",
          ftrec.get("with_full_text") == 2, str(ftrec))
    # the short comment alone would be neutral — proves the classifier used the full text, not the snippet
    from app.concepts.delib import DelibConcept as _DC
    check("full text is the analysis target: short comment 'See attached.' is neutral on its own",
          _DC._classify("See attached submission.") == "neutral")
    ftagg = D("delib.aggregate", {"survey": sid4})
    check("full text is the analysis target: f1 lands in OPPOSE (read from the full submission, not the snippet)",
          ftagg.get("breakdown", {}).get("oppose") == 1, str(ftagg.get("breakdown")))
    check("full text: the non-English f2 (no authority translation) stays untranslated (no auto-MT)",
          ftagg.get("breakdown", {}).get("untranslated") == 1 and ftagg.get("floored") == 1, str(ftagg.get("breakdown")))
    # the 原票 is a first-class, traceable atom: aliased text:orig:, provenance=external, delib:source link
    rk_f1 = next((rk for rk in (cortex.get_collection_members(f"set:survey:{sid4}:responses") or [])
                  if (cortex.get_meta(rk) or {}).get("answer") == "See attached submission."), None)
    src = cortex.get_adjacent_links(rk_f1, "delib:source") if rk_f1 else []
    src_dst = (src[0].get("dst") if isinstance(src[0], dict) else src[0][0]) if src else None
    smeta = cortex.get_meta(src_dst) or {} if src_dst else {}
    check("原票 is first-class: response --delib:source--> a provenance=external full-text atom (text:orig:)",
          smeta.get("provenance") == "external" and "oppose" in (cortex.get_chunk(src_dst) or "").lower()
          and any(a.startswith("text:orig:") for a in (cortex.get_aliases_by_key(src_dst) or [])))
    # delib.voices surfaces the full text + its traceable atom
    fv = next((v for v in D("delib.voices", {"agg": ftagg.get("aggregation_id")}).get("voices", [])
               if v.get("respondent") and "unfair burden" in v.get("full_text", "")), None)
    check("原票 reaches the record-level views: delib.voices carries full_text + full_text_atom",
          bool(fv) and fv.get("full_text_atom", "").startswith("text:orig:"))

    # ── one-shot pipeline ───────────────────────────────────────────────────────
    full = D("delib.pipeline", {"survey": sid, "society": SPACE, "group": GID, "cast": cast_id, "space": SPACE})
    check("pipeline: one call runs aggregate→to_labo→to_society with coexisting conclusions",
          len(full.get("posted", [])) >= 8 and full.get("dominant") == "support", str(len(full.get("posted", []))))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — delib bridge: multi-locale ingestion (original=operand, translation=projection), "
          "language-aware stance aggregation (untranslated non-English kept honestly, not neutral), disagreement-as-data "
          "projection (competing trajectories + coexisting conclusions + first-class tension), and "
          "society deliberation — end-to-end on the CLI path.")
    sys.exit(0)


if __name__ == "__main__":
    main()
