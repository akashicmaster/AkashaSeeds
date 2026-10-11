#!/usr/bin/env python3
"""
Radu Annotation distribution gating eval.

Policy: the generic Concept Laboratory (clab) ships in every series; the Radu Annotation MODEL and its
data do NOT go external — for now they ship on the THESAURUS line only. This eval locks that in so the
model can never accidentally leak into a public seed:

  • get_config gating — app/seeds/business/enterprise/librarian EXCLUDE the Radu files; thesaurus /
    thesaurus08 / their `n` twins INCLUDE them (cfg "radu": true).
  • the packer honours the exclusion — packing lib/ + test/ for a seeds series contains NONE of the
    Radu Annotation files; for a thesaurus series it contains the model + projection.
  • clab itself is NOT gated (the generic substrate ships everywhere).

Skips gracefully where `reproductor` is unavailable (e.g. inside a shipped seed, which strips the
mother-tree reproductive organs) — there is nothing to test there. Run:
  python app/test/radu_distribution_eval.py     (exit 0 = all pass / skipped)
"""
import io
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    try:
        from reproductor.engine import GeneticBlueprint as G, RADU_PRIVATE_FILES
        from reproductor import engine
    except Exception as exc:
        print(f"  SKIP  reproductor unavailable ({exc}) — distribution gating is not testable here "
              "(e.g. inside a shipped seed). Nothing to check.")
        print("RESULT: PASS (skipped).")
        return 0

    Cryst = next(c for _, c in vars(engine).items()
                 if isinstance(c, type) and hasattr(c, "_pack_directory"))
    inst = Cryst()

    def excludes_radu(series):
        ex = set(G.get_config(series)["exclude_paths"])
        return all(f in ex for f in RADU_PRIVATE_FILES)

    # ── get_config gating ────────────────────────────────────────────────────────────
    public = ["seeds", "seeds12", "seeds12n", "business", "enterprise", "librarian"]
    check("public/other series EXCLUDE the Radu Annotation model from get_config",
          all(excludes_radu(s) for s in public), detail=str([s for s in public if not excludes_radu(s)]))
    thesaurus = ["thesaurus", "thesaurus08", "thesaurus08n"]
    check("thesaurus line INCLUDES the Radu Annotation model (cfg 'radu': true, `n` twin inherits)",
          all(not excludes_radu(s) for s in thesaurus), detail=str([s for s in thesaurus if excludes_radu(s)]))

    # ── the packer honours it (pack lib/ + test/ into an in-memory zip) ───────────────
    def payload(series):
        buf = io.BytesIO()
        ex = G.get_config(series)["exclude_paths"]
        with zipfile.ZipFile(buf, "w") as zf:
            inst._pack_directory(ROOT, os.path.join(ROOT, "lib"), zf, exclude_paths=ex)
            inst._pack_directory(ROOT, os.path.join(ROOT, "test"), zf, exclude_paths=ex)
        return set(zipfile.ZipFile(io.BytesIO(buf.getvalue())).namelist())

    seeds_names = payload("seeds12")
    check("packed seeds payload contains NONE of the Radu Annotation model files",
          not ({"app/concepts/radu.py", "app/concepts/radu_projection.py",
                "app/test/radu_annotation_eval.py"} & seeds_names),
          detail=str(sorted(n for n in seeds_names if "radu" in n)))
    the_names = payload("thesaurus08")
    check("packed thesaurus payload SHIPS the Radu Annotation model + projection",
          {"app/concepts/radu.py", "app/concepts/radu_projection.py"} <= the_names)

    # ── clab (the generic substrate) is NOT gated — ships in seeds too ────────────────
    check("clab itself is NOT gated — the generic Concept Laboratory ships in seeds",
          "app/concepts/clab.py" in seeds_names and "app/concepts/clab_projection.py" in seeds_names)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        return 1
    print("ALL PASS — Radu Annotation model is thesaurus-line-only (never in public seeds), while the "
          "generic Concept Laboratory ships everywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
