#!/usr/bin/env python3
"""
Seed transfer-robustness — the base64 payload is WRAPPED, never one monster line.

A 16.9 MB single physical line (the old `PAYLOAD = "..."`) is silently truncated by mobile SSH
pastes, editors, and clipboard limits — the operator then hits "SyntaxError: unterminated string
literal (detected at line 22)" on the VPS because the closing quote was lost mid-transfer. The
crystallizer now wraps the payload at 120 cols inside a triple-quoted string and the seed strips
whitespace before decoding. This eval drives _generate_sprout_script with a tiny payload and proves:
the emitted script has NO monster line, is valid Python, and its wrapped payload decodes back to the
EXACT original bytes.

Run:  python test/seed_payload_wrap_eval.py   (exit 0 = all pass)
"""
import base64
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    # The crystallizer is GENERATOR-SIDE — a seed carries no `reproductor/`, so this import used to
    # raise on every deployed tree. This eval drives the emitted extractor, which only exists where
    # the generator does. A skip says so by name and never counts as a pass (deploy_eval, 09-21).
    if not os.path.isdir(os.path.join(ROOT, "reproductor")):
        print("SKIP generator-only — reproductor/ (the crystallizer) ships in no seed; the payload "
              "wrap is a property of the generator's own output")
        sys.exit(0)
    from reproductor.engine import Cryptobiosis
    eng = Cryptobiosis.__new__(Cryptobiosis)      # no __init__ needed for _generate_sprout_script

    # a payload long enough to require many wrapped lines (simulate a real multi-MB blob, small)
    original = os.urandom(50000)
    b64 = base64.b64encode(original).decode("ascii")
    check("test payload is a long single base64 string", len(b64) > 60000, "len=%d" % len(b64))

    script = eng._generate_sprout_script("testseries", {"max_leaves": 50, "tier": "alpha"}, b64,
                                         [], "silica", "disk", {"series": "testseries"})

    longest = max((len(l) for l in script.split("\n")), default=0)
    check("the emitted seed has NO monster physical line (wrapped)", longest <= 4096,
          "longest line=%d" % longest)

    # valid Python
    ok_compile = True
    try:
        compile(script, "seed", "exec")
    except SyntaxError as exc:
        ok_compile = False
        print("      compile error:", exc)
    check("the emitted seed is valid Python (compiles)", ok_compile)

    # the wrapped payload, whitespace-stripped, decodes back to the EXACT original bytes
    m = re.search(r'PAYLOAD = """\n(.*?)\n"""', script, re.S)
    check("PAYLOAD is a triple-quoted wrapped block", bool(m))
    if m:
        payload = m.group(1)
        maxpl = max((len(l) for l in payload.split("\n")), default=0)
        check("payload lines are wrapped at 120 cols", maxpl <= 120, "max payload line=%d" % maxpl)
        decoded = base64.b64decode("".join(payload.split()))
        check("the wrapped payload round-trips to the EXACT original bytes", decoded == original,
              "len %d vs %d" % (len(decoded), len(original)))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — the seed payload is wrapped (no monster line), the script compiles, and the "
          "wrapped base64 decodes back to the exact original bytes: transfer-robust on any terminal.")
    sys.exit(0)


if __name__ == "__main__":
    main()
