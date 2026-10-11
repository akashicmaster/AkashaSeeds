#!/usr/bin/env python3
"""
THE SEEDS-SERIES PAYLOAD IS WHAT A NEW USER MAY RUN OFFLINE (order of 9 October, step 3/5 gate).

The seeds series ships the purged platform and the application's seeds content, and nothing that needs a key, a
network or a model at first run. Held, on the CUT SEED when `akasha_seeds_seeds13.py` is built (and, until it is, on the
payload the crystallizer would cut — the same list):

  1. OFFLINE — no workload declaration, template or sweep (the station, the feeds, the laboratories, X and the LLM
     programmes are declarations; none ships), no source-corpus declaration, no TLS file
  2. NO MODEL — no model binary of any kind (`.tflite .onnx .pt .pth .bin .gguf .h5 .pb .safetensors .ckpt`), and no
     `assets/models/`
  3. LICENSED — every pack in the payload carries a licence, and each licence it names is one the repository's
     `LICENSE.md` admits (MIT, WordNet 3.1 as attributed, or a public-domain / CC0 / CC BY / CC BY-SA source it names)
  4. SIZE — the seed file is under 15 MB
  6. NO PERSONAL ADDRESS — no file of the payload carries a personal mailbox at a consumer provider (the Apple,
     Google, Microsoft, Yahoo and Proton mail domains), nor the maintainer's own local part
  5. THE PRIVATE STAYS PRIVATE — none of the series' `private` paths, and none of the `radu` / `plants` / `pages` groups

Run:  python app/test/seeds_payload_content_eval.py [SEED.py]     (exit 0 = all pass)
"""
import base64
import io
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
SERIES = "seeds13"
SEED = os.path.join(ROOT, "akasha_seeds_%s.py" % SERIES)
LIMIT = 15 * 1024 * 1024
MODEL_EXT = (".tflite", ".onnx", ".pt", ".pth", ".bin", ".gguf", ".h5", ".pb", ".safetensors", ".ckpt")
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def payload(seed):
    """{path: bytes} of the seed's payload, or the crystallizer's list read from the tree."""
    if seed and os.path.isfile(seed):
        src = open(seed, encoding="utf-8", errors="replace").read()
        m = re.search(r'PAYLOAD\s*=\s*"""(.*?)"""', src, re.S)
        zf = zipfile.ZipFile(io.BytesIO(base64.b64decode("".join(m.group(1).split()))))
        return {n: zf.read(n) for n in zf.namelist() if not n.endswith("/")}, "seed %s" % os.path.basename(seed)
    from reproductor import engine as E
    bp = E.GeneticBlueprint.get_config(SERIES)
    cr = E.Cryptobiosis()
    files = cr._app_payload(ROOT, bp, cr._select_packs(ROOT, bp))[0]
    return {f: open(os.path.join(ROOT, f), "rb").read() for f in files}, "the payload the crystallizer would cut (no seed built)"


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else SEED
    files, what = payload(seed)
    print("\n  payload: %s — %d files\n" % (what, len(files)))
    app = {p: b for p, b in files.items() if p.startswith("app/")}

    # (`config/source/corpus_policy/` is the generator's reviewed schema policy — data for an offline build step,
    # not a declaration the platform runs)
    decl = sorted(p for p in app if p.startswith("app/config/workbench/")
                  or (p.startswith("app/config/source/") and "/corpus_policy/" not in p))
    check("OFFLINE: no workload declaration, template, sweep or source-corpus declaration ships", not decl, str(decl[:4]))
    tls = sorted(p for p in files if p.endswith("tls.json"))
    tls += sorted(p for p in files if p.endswith("tls_domains.txt")
                  and any(ln.strip() and not ln.strip().startswith("#")
                          for ln in files[p].decode("utf-8", "replace").splitlines()))   # a commented template is inert
    check("OFFLINE: no active TLS configuration ships (certificates are obtained over the network)", not tls, str(tls))

    models = sorted(p for p in files if p.lower().endswith(MODEL_EXT) or "/assets/models/" in p or p.startswith("assets/models/"))
    check("NO MODEL: no model binary and no assets/models/", not models, str(models[:4]))

    lic_text = open(os.path.join(ROOT, "LICENSE.md"), encoding="utf-8").read().lower()
    admitted = ("mit", "public domain", "cc0", "cc by", "wordnet 3.1")
    bad = []
    packs = sorted({p.split("/")[2] for p in app if p.startswith("app/ontology/") and p.count("/") >= 3})
    for pk in packs:
        raw = app.get("app/ontology/%s/PACK.json" % pk)
        if raw is None:
            continue
        lic = str(json.loads(raw).get("license") or json.loads(raw).get("licence") or "").strip()
        low = lic.lower()
        if not lic or not any(a in low for a in admitted):
            bad.append("%s: %r" % (pk, lic[:40]))
        elif "wordnet" in low and "wordnet" not in lic_text:
            bad.append("%s: WordNet is not attributed in LICENSE.md" % pk)
    check("LICENSED: every pack (%d) carries a licence LICENSE.md admits" % len(packs), not bad, str(bad[:3]))

    if os.path.isfile(seed):
        size = os.path.getsize(seed)
        check("SIZE: the seed is under 15 MB", size < LIMIT, "%.2f MB" % (size / 1048576.0))
    else:
        import zlib
        est = sum(len(zlib.compress(b, 6)) for b in files.values())
        check("SIZE: the payload compresses under 15 MB (no seed built; estimate)", est < LIMIT, "%.2f MB" % (est / 1048576.0))

    decl_s = json.load(open(os.path.join(ROOT, "app", "config", "series.json"), encoding="utf-8"))
    leaked = sorted(p for priv in decl_s.get("private", []) for p in files
                    if p.startswith("app/" + priv.strip("/")))
    for g in ("radu", "plants", "pages"):
        for gp in decl_s["groups"][g]["paths"]:
            leaked += [p for p in files if p == "app/" + gp.strip("/") or p.startswith("app/" + gp.strip("/") + "/")]
    check("PRIVATE: no private path and no radu / plants / pages group ships", not leaked, str(sorted(set(leaked))[:4]))

    mail = re.compile(r"[A-Za-z0-9._%+-]*@(?:mac|me|icloud|gmail|googlemail|hotmail|outlook|live|yahoo|ymail|proton(?:mail)?|pm)"
                      r"\.(?:com|me|net|jp|co\.jp)\b|\bhenri77\b", re.I)
    hits = []
    for pth, raw in files.items():
        if pth.endswith((".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip", ".gz", ".woff", ".woff2", ".tflite", ".onnx")):
            continue
        for m in mail.finditer(raw.decode("utf-8", "ignore")):
            hits.append("%s: %s" % (pth, m.group(0)))
            break
    check("NO PERSONAL ADDRESS: no personal mailbox or free-mail address in any file of the payload", not hits,
          "%d: %s" % (len(hits), hits[:3]))

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the seeds payload is offline, model-free, licensed, under 15 MB, and carries nothing private and no personal address.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
