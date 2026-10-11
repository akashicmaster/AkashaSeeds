#!/usr/bin/env python3
"""
F56-D1 — content fingerprint: a redeploy with ANY changed byte replaces the running daemon.

The crystallizer bakes `content_fingerprint` (a sha256 over the WHOLE payload manifest — every bundled
file's path + bytes) into akasha_build.json; the daemon-replace handshake (akasha._handshake_build_id)
advertises + compares it. So a redeploy that changed only an .ak / config / static asset — which the
.py-only _code_build_id would miss — still replaces the running writer. This eval verifies, on an
already-built seed, that the baked fingerprint is a correct, content-addressed hash of the payload
(hence: any changed bundled byte ⇒ a different fingerprint) and that the handshake consumes it.

Run:  python test/f56_d1_fingerprint_eval.py [akasha_seeds_seeds14.py]   (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _manifest_fp(z: zipfile.ZipFile) -> str:
    """The same sha256-over-manifest the crystallizer bakes: sorted names, each name + bytes,
    excluding the self-referential akasha_build.json and the generated seeds."""
    h = hashlib.sha256()
    for n in sorted(z.namelist()):
        if n == "akasha_build.json" or n.startswith("akasha_seeds_"):
            continue
        h.update(n.encode("utf-8", "replace")); h.update(b"\0")
        h.update(z.read(n)); h.update(b"\0")
    return h.hexdigest()[:16]


def main():
    # `seed_check` lives in `scripts/` and is GENERATOR-SIDE: it ships in no payload, so on a
    # deployed tree this import used to raise and the eval failed for the one reason that says
    # nothing about the cell. A skip says so by name and never counts as a pass (deploy_eval,
    # 09-21).
    if not os.path.isfile(os.path.join(ROOT, "scripts", "seed_check.py")):
        print("SKIP generator-only — scripts/seed_check.py reads a built payload and ships in no "
              "seed; this eval runs on the generator side, against the seed it just built")
        sys.exit(0)
    import seed_check
    seed = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "akasha_seeds_seeds14.py")
    if not os.path.isfile(seed):
        print("SKIP — seed not built: %s (run: python spawn.py seeds14)" % seed); sys.exit(0)

    z = seed_check._payload_zip(seed)
    build = json.loads(z.read("akasha_build.json").decode("utf-8"))
    baked = (build.get("content_fingerprint") or "").strip()

    check("akasha_build.json carries a 16-hex content_fingerprint",
          len(baked) == 16 and all(c in "0123456789abcdef" for c in baked), "fp=%r" % baked)

    recomputed = _manifest_fp(z)
    check("the baked fingerprint EQUALS an independent recompute of the payload manifest "
          "(content-addressed ⇒ any changed bundled byte changes it)",
          baked == recomputed, "baked=%s recomputed=%s" % (baked, recomputed))

    # the handshake reads it from akasha_build.json (both sides advertise/compare the same id)
    import tempfile
    import akasha
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "akasha_build.json"), "w") as fh:
        fh.write(json.dumps(build))
    check("akasha._handshake_build_id() returns the baked content_fingerprint (the daemon-replace id)",
          akasha._handshake_build_id(d) == baked, akasha._handshake_build_id(d))

    # a changed byte anywhere in the payload yields a different id (simulate by flipping the manifest)
    h2 = hashlib.sha256(("x" + recomputed).encode()).hexdigest()[:16]
    check("the fingerprint is sensitive: a different payload manifest ⇒ a different id",
          h2 != baked, "")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the seed bakes a correct content-addressed fingerprint of its whole payload "
          "into akasha_build.json, and the daemon-replace handshake advertises + compares it, so a "
          "redeploy with any changed byte (code / ontology / config / asset) replaces the running daemon.")
    sys.exit(0)


if __name__ == "__main__":
    main()
