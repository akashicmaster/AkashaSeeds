#!/usr/bin/env python3
"""
BirdCLEF × Source Data Layer import eval — a FOCUSED audio corpus, audio-by-reference.

Drives app/scripts/birdclef_source_import.py's selection + the same `source.*` wiring it runs against a
live cell, in-process over real-SHAPED BirdCLEF `train.csv` rows, and asserts the non-negotiables:

  · CONCENTRATION — the auto-selector picks the FEWEST species (richest `type` variety first) to
    reach N, not a scatter across the whole dataset;
  · WITHIN-SPECIES VARIETY — the slice is type-balanced (song / call / courtship … all present), so
    the audio analysis has different vocalizations to cross;
  · AUDIO-BINARY PRINCIPLE — every record is a REFERENCE URL (xeno-canto id → …/download) with
    content_type=audio; the .ogg binary is NEVER carried;
  · one Source Atom per clip, acquired into a frozen pool, declared a CORPUS lab, audited grounded;
  · the pool advertises the AUDIO modality (via content_type, since a /download URL has no extension).

Run:  python app/test/birdclef_source_import_eval.py     (exit 0 = all pass)
"""
import hashlib
import importlib.util
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.source import bootstrap
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _synthetic_rows():
    """train.csv-shaped rows: 3 species with different `type` richness + xeno-canto filenames."""
    species = {
        "comsan": ["song", "call", "courtship", "alarm", "flight call"],   # 5 types (richest)
        "wlwwar": ["song", "call", "courtship", "alarm"],                  # 4 types
        "grtdro": ["song", "call"],                                        # 2 types (sparse)
    }
    rows, xc = [], 100000
    for sp, types in species.items():
        for _rep in range(8):
            for t in types:
                xc += 1
                rows.append({"primary_label": sp, "secondary_labels": "['xxx']", "type": t,
                             "latitude": "12.34", "longitude": "56.78", "author": "Recordist",
                             "rating": "4.5", "filename": "%s/XC%d.ogg" % (sp, xc),
                             "common_name": sp.upper(), "scientific_name": "Genus %s" % sp})
    return rows


def main():
    spec = importlib.util.spec_from_file_location(
        "birdclef_source_import", os.path.join(ROOT, "app/scripts", "birdclef_source_import.py"))
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)

    rows = _synthetic_rows()

    # ── 1. auto-concentration: fewest species (richest type variety first) to reach N ──
    recs, chosen, per_type = B.select_records(rows, n=40)
    check("select: auto-concentrates on the FEWEST species (richest `type` variety) to reach N",
          len(recs) == 40 and 1 <= len(chosen) <= 2 and chosen[0] == "comsan", str(chosen))

    # ── 2. within-species variety: type-balanced (not 40 songs) ──
    check("select: the slice is type-balanced — song/call/courtship all represented, no monoculture",
          len(per_type) >= 3 and max(per_type.values()) - min(per_type.values()) <= 2, str(per_type))

    # ── 3. audio-binary principle: reference URL + content_type=audio, never a binary ──
    check("select: every clip is a REFERENCE URL (xeno-canto id → …/download), content_type=audio",
          all(r["url"].startswith("https://xeno-canto.org/") and r["url"].endswith("/download")
              and r["content_type"] == "audio" and r["format"] == "ogg" for r in recs)
          and not any("binary" in r or "data" in r or "bytes" in r for r in recs), recs[0]["url"])

    # ── 4. explicit --species + --audio-base override the xeno-canto derivation ──
    recs2, chosen2, pt2 = B.select_records(rows, n=12, species="wlwwar",
                                           audio_base="https://mirror.example/train_audio")
    check("select: explicit species concentrates on exactly it; --audio-base builds base/<filename>",
          chosen2 == ["wlwwar"] and all(r["primary_label"] == "wlwwar" for r in recs2)
          and all(r["url"].startswith("https://mirror.example/train_audio/wlwwar/") for r in recs2),
          str(chosen2))

    # ── 5. end-to-end over the Source Data Layer (the same ops the script runs on a live cell) ──
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_bird_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    out = B.run(d, recs, {"freeze": True, "species": chosen})
    check("run: the focused slice is acquired one Source Atom per clip into the frozen pool",
          out.get("acquired") == 40 and out.get("members") == 40 and isinstance(out.get("at_seq"), int),
          str({kk: out.get(kk) for kk in ("acquired", "members", "at_seq")}))
    check("run: birdsong is declared a CORPUS lab grounded on the frozen audio pool",
          out.get("evidence_status") == "GROUNDED", str(out.get("evidence_status")))

    # ── 6. the acquired atom keeps the reference + verbatim metadata; the pool advertises AUDIO ──
    one = d("source.read", {"id": "source:item:birdclef:%s" % recs[0]["id"].lower()})
    sm = one.get("source_metadata") or {}
    check("acquire: the clip atom keeps the reference URL + coded metadata (primary_label, type) verbatim",
          sm.get("content_type") == "audio" and sm.get("primary_label") == recs[0]["primary_label"]
          and sm.get("type") == recs[0]["type"] and sm.get("url", "").endswith("/download"), str(sm)[:120])
    mods = out.get("modalities") or {}
    check("modalities: the extension-less audio pool advertises AUDIO (via content_type), not image",
          mods.get("audio") is True and mods.get("image") is False and mods.get("text") is True, str(mods))

    # ── the Source Viewer's Laboratories panel lists a source-declared lab (birdsong grounds itself via
    #    source.lab.declare, never a labo: — so source.labs must surface it, not just labo.ls) ──
    slabs = {L.get("lab"): L for L in d("source.labs", {}).get("labs") or []}
    check("source.labs lists the source-declared CORPUS lab (birdsong) so the hub panel shows it",
          "birdsong" in slabs and slabs["birdsong"].get("evidence_status") == "GROUNDED"
          and slabs["birdsong"].get("pool") == B.POOL, str(sorted(slabs)))

    # ── 7. the script targets the documented source/pool/lab identities ──
    check("script: birdclef_source_import targets the birdclef source/pool and the birdsong CORPUS lab",
          B.SOURCE_ID == "source:src:birdclef" and B.POOL == "source:pool:birdclef:focus:v1"
          and B.LAB == "birdsong", "%s / %s / %s" % (B.SOURCE_ID, B.POOL, B.LAB))

    # ── 8. AUTO-BOOTSTRAP: the dev-side --emit-bundle asset + the boot phase's bundle→load→observe payload
    #    (what makes deploy automatic — no operator step). Emit a bundle, read it back, load + OBSERVE it
    #    exactly as _schedule_birdclef_bootstrap does, offline (a synthetic waveform resolver). ──
    import gzip as _gzip
    import json as _json
    import numpy as np
    import app.concepts.vision_lab as _V
    _V._resolve_audio_array = lambda loc: (np.sin(np.linspace(0, (110 + abs(hash(loc)) % 300) * 2 * np.pi,
                                                              22050)).astype("float32"), 22050)
    bdir = tempfile.mkdtemp(prefix="bird_bundle_")
    recs_gz, man = B.emit_bundle(recs, chosen, per_type, bdir)
    back = [_json.loads(x) for x in _gzip.open(recs_gz, "rt", encoding="utf-8").read().splitlines() if x.strip()]
    check("emit-bundle: records.jsonl.gz + manifest round-trip (references only, no binary)",
          len(back) == len(recs) and man.get("pool") == B.POOL and man.get("audio_by_reference") is True
          and all("url" in r and not any(k in r for k in ("binary", "bytes", "data")) for r in back),
          "%d recs, species=%s" % (len(back), man.get("species")))

    # fresh cell → run the boot phase's payload (bc.run corpus-load, then the observation the JCL job does)
    k2 = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_bird2_"))
    k2.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d2(m, data):
        r = k2.dispatch({"jsonrpc": "2.0", "method": m,
                         "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    bout = B.run(d2, back, {"freeze": True, "species": man.get("species") or []})
    d2("vlab.run.new", {"pool": B.POOL, "run": "b1", "observers": "spectral,mfcc"})
    bex = d2("vlab.run.execute", {"run": "b1"})
    bsp = {s["space"]: s for s in d2("vlab.spaces", {"run": "b1"}).get("spaces", [])}
    check("boot payload: the bundle auto-loads a GROUNDED corpus and the observation run populates offline",
          bout.get("evidence_status") == "GROUNDED" and bex.get("observed") == len(back) * 2  # 2 observers
          and bsp.get("spectral", {}).get("works") == len(back), "obs=%s spectral=%s"
          % (bex.get("observed"), bsp.get("spectral", {}).get("works")))

    # ── 8b. (10-03) a FROZEN, unchanged pool is skipped — a boot never acquires into it again ──
    #    The first boot pass after every deploy logged "[import] refused method=source.acquire code=-32002 — pool
    #    … is FROZEN": the import called source.acquire straight after source.pool.create. It now reads the pool.
    calls = []

    def d3(m, data):
        calls.append(m)
        return d2(m, data)

    second = B.run(d3, back, {"freeze": True, "species": man.get("species") or []})
    check("second run on the frozen, unchanged pool reports `skipped` (corpus unchanged)",
          second.get("status") == "skipped" and second.get("detail") == "corpus unchanged"
          and second.get("pool") == B.POOL and second.get("members") == len(back), str(second)[:160])
    check("…and issues NO source.acquire (nor pool.create / freeze) — nothing is attempted on a frozen pool",
          "source.acquire" not in calls and "source.pool.create" not in calls
          and "source.pool.freeze" not in calls, str(calls))
    check("…and still reports the lab's audit (the boot's status line stays honest)",
          second.get("evidence_status") == "GROUNDED", str(second.get("evidence_status")))
    calls.clear()
    third = B.run(d3, back[:-3], {"freeze": True, "species": man.get("species") or []})
    check("a frozen pool is skipped even when the corpus differs — nothing else is attempted (no derived version, "
          "no repair; a changed corpus is a new seed on a new cell)",
          third.get("status") == "skipped" and third.get("pool") == B.POOL
          and not [c for c in calls if c in ("source.acquire", "source.pool.create", "source.pool.freeze")], str(third)[:140])

    # ── 9. the boot phase is WIRED: the kernel defines the method AND calls it in _boot_load_ontology.
    #    (The eval stubs _boot_load_ontology, so read the kernel source file, not the live method.) ──
    #    (Post-layout: the source package's MANIFEST declares the post_load schedule; the heart runs
    #    the manifests' post_load phase in order.)
    # Step 2: there is no per-dataset boot body any more. ONE `source_bootstrap` schedule runs the
    # managed unit over every `app/config/source/*.json` that declares an importer — so what this checks
    # is that THIS corpus is among the declarations that schedule will pick up, and that its
    # declared entry resolves. A dataset is wired by being declared, not by being named in the boot.
    from lib.akasha import kernel as _kmod
    _agg = _kmod._heart_aggregate()
    _post = [n for n, _ in _agg.schedules.phase("post_load")]
    _ids = [str(d.get("id")) for d in bootstrap.source_declarations(None)]
    _decl = next((d for d in bootstrap.source_declarations(None) if d.get("id") == "birdclef"), None)
    check("the boot runs ONE declared-source unit, and this corpus is one of its declarations",
          "source_bootstrap" in _post
          and _agg.schedules.get("source_bootstrap") is bootstrap.schedule_source_bootstrap
          and _decl is not None, "declared: %s" % ", ".join(_ids))
    check("its declared importer resolves to a callable",
          _decl is not None and callable(bootstrap.declared_importer(_decl)),
          str((_decl or {}).get("importer")))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — BirdCLEF import: a CONCENTRATED, type-balanced audio slice (few species, many "
          "vocalization types) is acquired one-atom-per-clip into a frozen pool, audio-by-reference only "
          "(xeno-canto URL, content_type=audio, no binary ever), declared a CORPUS lab audited grounded, "
          "with the pool advertising the AUDIO modality for the Source Viewer.")
    sys.exit(0)


if __name__ == "__main__":
    main()
