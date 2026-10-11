#!/usr/bin/env python3
"""
Mapped-stance layer eval — coded survey answers as DECLARED opinions, honest by construction.

The coded-field → stance mapping layer (app/config/mobility_stance_map.json +
app/scripts/mobility_coded_to_delib.py + the delib mapped-voice contract) lets coded attitude items
(e.g. EU Travel Survey 2014 `Preference_tolls_or_traffic_limitation`) feed the Consensus lab —
WITHOUT pretending they are read free-text opinions:

  • a mapped stance is DECLARED by an inspectable rule (delib:mapped_by → first-class rule atom),
    never read by the stance lexicon (which would fabricate `neutral` from "No preferences");
  • the verbatim coded answer stays the operand — no synthesized opinion text;
  • unreadable codes ("Don't know", "No preferences") are `no_reading`: counted, visible, their own
    group — but no stance, no cluster, no conclusion, excluded from dominant/net;
  • mapped and free-text voices stay distinguishable end-to-end (aggregate.via_mapping,
    voices[].via_mapping + mapping_rule).

Run:  python app/test/delib_mapped_stance_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


BASIS = "map:mobility_stance_map@v1:Preference_tolls_or_traffic_limitation"

RECORDS = [
    # mapped voices — stance DECLARED by the rule, operand = the verbatim coded answer
    {"respondent_id": "1:tolls", "text": "Definitely more acceptable to limit road traffic",
     "language": "en", "stance": "support", "stance_basis": BASIS},
    {"respondent_id": "2:tolls", "text": "Definitely more acceptable to pay for less congestion",
     "language": "en", "stance": "support", "stance_basis": BASIS},
    {"respondent_id": "3:tolls", "text": "Probably more acceptable to limit road traffic",
     "language": "en", "stance": "conditional", "stance_basis": BASIS},
    # a declared oppose (synthetic here; the rule id still traces it)
    {"respondent_id": "4:tolls", "text": "Certainly not", "language": "en",
     "stance": "oppose", "stance_basis": BASIS},
    # unreadable codes → no_reading (the lexicon would have fabricated `neutral` from these)
    {"respondent_id": "5:tolls", "text": "No preferences", "language": "en",
     "stance": "no_reading", "stance_basis": BASIS},
    {"respondent_id": "6:tolls", "text": "Don't know", "language": "en",
     "stance": "no_reading", "stance_basis": BASIS},
    # one READ free-text voice alongside — must stay distinguishable from the mapped ones
    {"respondent_id": "7:free", "text": "I support congestion charges, they are beneficial.",
     "language": "en"},
]


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_mapstance_"))
    gw = AkashaGateway(kernel_client=k)

    def D(method, data, tok="admin"):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok, "data": data}, "id": "t"}, "local")
        if "error" in r:
            return {"__error__": r["error"].get("message", "")}
        return r.get("result") or {}

    D("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})
    cortex = k.manager.get_session("admin").local_cortex

    sid = D("survey.new", {"title": "Demand management acceptance (mapped)"}).get("survey_id")
    D("survey.q.add", {"text": "Demand-management measures (congestion charges or road-traffic "
                               "limitation) are acceptable to reduce congestion.",
                       "qtype": "free_text"})

    # ── guard: a mapped stance WITHOUT a declared basis is refused ────────────────
    bad = D("delib.ingest", {"survey": sid, "records": [
        {"respondent_id": "x", "text": "No preferences", "stance": "no_reading"}]})
    check("guard: stance without stance_basis is refused (an undeclared mapping is a fabricated reading)",
          "__error__" in bad and "stance_basis" in bad["__error__"], str(bad)[:90])

    ing = D("delib.ingest", {"survey": sid, "records": RECORDS})
    check("ingest: 7 records (6 mapped + 1 free-text) accepted", ing.get("count") == 7, str(ing))

    agg = D("delib.aggregate", {"survey": sid})
    br = agg.get("breakdown", {})
    check("aggregate: declared stances only — support 3 (2 mapped + 1 read), oppose 1, conditional 1",
          br.get("support") == 3 and br.get("oppose") == 1 and br.get("conditional") == 1, str(br))
    check("aggregate: 'No preferences'/'Don't know' are no_reading — NEVER lexicon-fabricated neutral",
          br.get("no_reading") == 2 and "neutral" not in br, str(br))
    check("aggregate: via_mapping counts exactly the 6 mapped voices", agg.get("via_mapping") == 6,
          str(agg.get("via_mapping")))
    check("aggregate: dominant/net exclude no_reading (dominant=support, net=(3-1)/7)",
          agg.get("dominant") == "support" and abs(agg.get("net_score", 0) - round(2 / 7, 4)) < 1e-9,
          f"dominant={agg.get('dominant')} net={agg.get('net_score')}")

    # ── graph: the declared reading is first-class + traceable ───────────────────
    resp_keys = cortex.get_collection_members(f"set:survey:{sid}:responses") or []
    mapped_resp = next((rk for rk in resp_keys
                        if (cortex.get_meta(rk) or {}).get("answer") ==
                        "Definitely more acceptable to limit road traffic"), None)
    st_links = cortex.get_adjacent_links(mapped_resp, "delib:mapped_stance") if mapped_resp else []
    st_dst = (st_links[0].get("dst") if isinstance(st_links[0], dict) else st_links[0][0]) if st_links else None
    check("graph: response --delib:mapped_stance--> delib:stance:support",
          bool(st_dst) and "delib:stance:support" in (cortex.get_aliases_by_key(st_dst) or []))
    rl_links = cortex.get_adjacent_links(mapped_resp, "delib:mapped_by") if mapped_resp else []
    rl_dst = (rl_links[0].get("dst") if isinstance(rl_links[0], dict) else rl_links[0][0]) if rl_links else None
    check("graph: response --delib:mapped_by--> the first-class rule atom carrying the spec id",
          bool(rl_dst) and BASIS == (cortex.get_chunk(rl_dst) or "").strip())

    # ── voices: mapped vs read voices stay distinguishable ───────────────────────
    voices = D("delib.voices", {"agg": agg.get("aggregation_id")}).get("voices", [])
    v_mapped = [v for v in voices if v.get("via_mapping")]
    v_read = [v for v in voices if not v.get("via_mapping")]
    check("voices: 6 via_mapping (each carrying the rule id) + 1 read free-text voice",
          len(v_mapped) == 6 and len(v_read) == 1 and
          all(v.get("mapping_rule") == BASIS for v in v_mapped),
          f"mapped={len(v_mapped)} read={len(v_read)}")
    check("voices: the mapped operand is the VERBATIM coded answer (no synthesized opinion text)",
          any(v.get("original") == "No preferences" for v in v_mapped))

    # ── labo projection: no_reading joins the initial family but forms nothing ───
    labo = D("delib.to_labo", {"agg": agg.get("aggregation_id"), "title": "tolls (mapped)"})
    concl = [c.get("judgement") for c in labo.get("conclusions", [])]
    check("to_labo: conclusions only from declared stances (affirm/negate/mixed — nothing from no_reading)",
          set(concl) == {"affirm", "negate", "mixed"}, str(concl))
    check("to_labo: no cluster is labelled no_reading",
          all("no_reading" not in str(c) for c in (labo.get("clusters") or {})), str(labo.get("clusters")))

    # ── converter: applies the spec verbatim + refuses unmapped values ───────────
    with tempfile.TemporaryDirectory() as td:
        rows = [
            {"respondent_id": "1", "Preference_tolls_or_traffic_limitation":
                "Definitely more acceptable to limit road traffic", "country": "BE",
             "row_coordinate": "t.tab:2"},
            {"respondent_id": "2", "Preference_tolls_or_traffic_limitation": "No preferences",
             "country": "DE", "row_coordinate": "t.tab:3"},
            {"respondent_id": "3", "Preference_tolls_or_traffic_limitation":
                "SOME VALUE THE SPEC NEVER DECLARED", "country": "FR", "row_coordinate": "t.tab:4"},
        ]
        src = os.path.join(td, "r.jsonl")
        out = os.path.join(td, "o.jsonl")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write("\n".join(json.dumps(r) for r in rows))
        p = subprocess.run([sys.executable, "app/scripts/mobility_coded_to_delib.py",
                            "--records", src, "--map", "app/config/mobility_stance_map.json",
                            "--item", "Preference_tolls_or_traffic_limitation", "--out", out],
                           capture_output=True, text=True)
        emitted = [json.loads(l) for l in open(out, encoding="utf-8") if l.strip()]
        check("converter: declared readings applied (support + no_reading), stance_basis stamped",
              len(emitted) == 2 and emitted[0]["stance"] == "support" and
              emitted[1]["stance"] == "no_reading" and
              all(e["stance_basis"] == BASIS for e in emitted), str([e.get("stance") for e in emitted]))
        check("converter: an undeclared value is REFUSED (reported UNMAPPED, never guessed)",
              "UNMAPPED" in p.stdout and "SOME VALUE THE SPEC NEVER DECLARED" in p.stdout)

    print()
    if _fails:
        print(f"{len(_fails)} FAILED: {_fails}")
        sys.exit(1)
    print("ALL PASS — mapped voices are declared, traceable, distinguishable; unreadable codes stay "
          "no_reading (counted, never given a stance they did not earn).")


if __name__ == "__main__":
    main()
