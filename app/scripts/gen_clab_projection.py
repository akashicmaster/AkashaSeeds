#!/usr/bin/env python3
"""
Regenerate the Concept Laboratory demo projection asset for the Archives page.

The Archives Concept Lab page (`app/archives/labo/concept/`) is display-only (P1): it reads a static
projection JSON and renders the Trajectory+Family view (spec: docs/for-llm/clab-projection-gui-spec.md).
This script produces that JSON by running the Radu "Primary Examples" fixture through the REAL CLI
path and calling `clab.project` — the same flow as app/test/clab_radu_fixture_eval.py — then writing the
trajectory (and evidence) modes into app/archives/labo/concept/.

Missing corpus atoms the fixture references are stubbed with a HUMANIZED label (so the demo reads
cleanly). When the page is later switched to a live `clab.project` RPC (P3), this asset becomes just
a fallback.

Run:  python app/scripts/gen_clab_projection.py
"""
import glob
import hashlib
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

OUT_DIR = os.path.join(ROOT, "app", "archives", "labo", "concept")
FIXTURE = os.path.join(ROOT, "app", "test", "fixtures", "radu_primary_examples.clab")


def humanize(alias: str) -> str:
    seg = [s for s in alias.split(":") if s not in ("pe", "pe04", "example")]
    tail = seg[-2:] if len(seg) >= 2 else seg
    w = " ".join(tail).replace("_", " ").strip()
    return (w[:1].upper() + w[1:]) if w else alias


def main():
    from lib.akasha.api import client
    gw = client.embedded(tempfile.mkdtemp(prefix="clab_gen_"), "seeds", load_ontology=False)
    k = gw.kernel_client
    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def cli(line):
        return gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                            "params": {"session_token": "admin", "data": {"command": line}}, "id": "t"}, "local")

    def R(line):
        return cli(line).get("result") or {}

    # load the primary_examples tier-C corpus
    for ak in sorted(glob.glob(os.path.join(ROOT, "app", "ontology", "primary_examples", "*.ak"))):
        if os.path.basename(ak) == "_lexicon.ak":
            continue
        for ln in open(ak, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                cli(ln)

    lines = [l.rstrip("\n") for l in open(FIXTURE, encoding="utf-8")
             if l.strip() and not l.strip().startswith("#")]

    # stub referenced-but-undefined corpus atoms with a readable label
    cortex = k.manager.get_session("admin").local_cortex
    for a in sorted(set(re.findall(r'(pe0?4?:[A-Za-z0-9_:]+)', " ".join(lines)))):
        if not cortex.resolve_alias(a):
            cli(f'def "{a}" "{humanize(a)}"')

    # run the 104-command research session
    src_id = None
    for line in lines:
        res = cli(line.replace("__SRC__", src_id or "clab:source:x"))
        if line.startswith("clab.source.add"):
            src_id = res.get("result", {}).get("id")

    os.makedirs(OUT_DIR, exist_ok=True)
    for mode, fname in (("trajectory", "projection.trajectory.json"),
                        ("evidence", "projection.evidence.json")):
        proj = R(f'clab.project target="active" mode="{mode}"')
        json.dump(proj, open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"wrote {fname}: nodes={len(proj.get('nodes', []))} "
              f"regions={len(proj.get('regions', []))} trajectories={len(proj.get('trajectories', []))}")

    # Rubik (Concept Formation) projection — depth-stacked family pages (docs/for-llm/
    # clab-rubik-projection-gui-spec.md). The §16 acceptance branch + the full unfiltered stack.
    LIGO_THEORY = "Theory A — Theoretically Pertinent Detection"
    for cmd, fname in ((f'clab.rubik trajectory="{LIGO_THEORY}"', "rubik.json"),
                       ('clab.rubik', "rubik.full.json")):
        rub = R(cmd)
        json.dump(rub, open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"wrote {fname}: pages={len(rub.get('pages', []))} "
              f"transforms={len(rub.get('transforms', []))} nodes={len(rub.get('nodes', []))}")


if __name__ == "__main__":
    main()
