#!/usr/bin/env python3
"""
The platform knows what a WORKLOAD is and how to run one. It does not know what a station, a studio,
a programme, a dataset or a site is (step 2 §7).

Two properties, both of which can only be demonstrated by NOT finding something — which is why they
are a static eval rather than a run:

  1. IMPORTS — a platform module imports only platform modules. A Concept Model is reached by
     `api.concept_class(kernel, prefix)`, by a manifest hook, or by dispatching its op. The rule
     exists because the import graph has one direction (heart ← ontology ← source ← concepts ←
     workbench ← archives) and a rightward import is how an 18,310-line kernel came to import thirty
     application modules.

  2. TOKENS — the platform tree names no application. The allow-list is HERE, in the eval, never in
     the code: a residue that is allowed is allowed by a line someone had to write and can read,
     with the reason and the seed it is owed in. Step 2's targets (§8) leave §3 rows 5–7 and §4 for
     seed B, so the list below is that debt, written down.

     Two lists, same discipline: the platform MODULES, and `scripts/*.py`, which the order's grep
     includes and the module scan does not reach. Both fail on a STALE entry, because an exemption
     for something already clean is a claim that is no longer true.

A hit that is a COMMENT explaining history is not a hit — a file may say what it used to be. The
scan reads code only.

Run:  python test/platform_vocabulary_eval.py     (exit 0 = all pass)
"""
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


# ── the platform tree, as the order names it ─────────────────────────────────────────────────────
PLATFORM_DIRS = ("lib/akasha/api", "lib/akasha/workbench", "lib/akasha/source",
                 "lib/akasha/ontology", "lib/akasha/jcl", "lib/akasha/backends", "api", "services")
PLATFORM_FILES = ("akasha.py",)


def _platform_py():
    out = list(PLATFORM_FILES)
    for f in sorted(os.listdir("lib/akasha")):
        if f.endswith(".py"):
            out.append("lib/akasha/" + f)
    for d in PLATFORM_DIRS:
        for base, _dirs, files in os.walk(d):
            if "__pycache__" in base:
                continue
            out.extend(os.path.join(base, f) for f in sorted(files) if f.endswith(".py"))
    # every Concept Model module under lib/ is the platform's: the application's live under its root
    for base, _dirs, files in os.walk("lib/akasha/concepts"):
        if "__pycache__" not in base:
            out.extend(os.path.join(base, f) for f in sorted(files) if f.endswith(".py"))
    return sorted(set(out))


# ── `scripts/*.py`, which the order's grep includes and the file scan above does not ─────────────
#
# The ownership map calls `scripts/` platform and `scripts/user/` user, so the top level is in the
# order's §7 grep. It was 74 lines across 19 files, reported and ratcheted while the question was
# "whose tree is this?"; the frontend moved sixteen dataset and application tools to `scripts/user/`
# and handed back three, which are now each ANSWERED below rather than counted.
#
# So this is the module allow-list's discipline applied to the script tree: an exemption is a line
# someone wrote and can read, a STALE one fails, and the residue that is merely tolerated is ZERO.
SCRIPTS_RATCHET = 0           # hits in scripts/*.py that are NOT allow-listed below; never rises

# (path, what the hits are, why that is not the platform naming an application, owed-in)
SCRIPTS_ALLOWED = [
    ("scripts/gen_pack_manifest.py", "the word \"Thesaurus\" in generated prose",
     "the RELEASE TIER, in a table comparing what each tier loads — the series constant the order's "
     "§4 last row keeps by name. A regex hit, not an application", "never — not debt"),
    ("scripts/gen_lexicon.py", "`station`, `thesaurus` and `gen` as CORE_NS entries",
     "lexicon DATA, not a code branch. `station` is core exactly BECAUSE the code compares against "
     "`station:state:*` / `station:reason:*`, which is what `verify_lexicon --all` checks — it moves "
     "with those ids when §3 row 1 re-keys them to `wl:*`. `thesaurus` defines the ontology RELATION "
     "namespace (`thesaurus:related`), which never moves", "seed B, with the re-key"),
]


def _scripts_py():
    import glob as _glob
    return sorted(_glob.glob("scripts/*.py"))


def _code_lines(path):
    """(lineno, code) with comments and docstrings stripped — a comment may name what a file used
    to be while explaining why it no longer does."""
    src = open(path, encoding="utf-8", errors="replace").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    blanked = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            blanked.update(range(n.value.lineno, (n.value.end_lineno or n.value.lineno) + 1))
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        if i in blanked:
            continue
        code = line.split("#", 1)[0]
        if code.strip():
            out.append((i, code))
    return out


# ── 2. the tokens, and the debt that is still owed ───────────────────────────────────────────────
# `cosmos` IS NOT ON THIS LIST, and that is a classification, not an exemption (group 4). In
# platform code the word names the HEART'S semantic field — Consciousness's `cosmos_nd`, the
# `CosmosMapper`, the field view (`view`/`cosmos`), the field projection a dive returns and the
# field-graph ops — exactly as the CLAUDE.md layer map describes it. The GUI that VIEWS the field is
# named after it and is archives' business; its one foothold in the platform, the `/cosmos` URL
# mount (launcher + portal), is now archives' own `static` declaration. So the token that names
# the APPLICATION is the mount path, and that one is on the list.
TOKENS = ("station", "studio", "news", "thesaurus", "kitchen", "/cosmos", "mobility", "birdclef",
          "cma_", "bl_real", "akashic", "reading_room", "gallery", "field_guide", "_legacy_sid",
          # ── ruling 2026-09-23 §3.5: the words the platform must not be able to say ──
          # `station:state:*` / `station:reason:*` are the STATION's vocabulary for the STATION's
          # surface. A platform module that names one is deciding what "on air" or "standing by"
          # means for an application, which is the fault the ruling is about; `workload.status`
          # returns `last` + `gate` and the application composes the sentence.
          "station:state", "station:reason",
          # `no_text` is a MODEL-PROVIDER outcome: it means a model was called and returned
          # nothing. Outside the LLM gateway it is a word about something the module did not do —
          # the driver stamped it on workloads that never called a model at all, and the rooms
          # showed a provider failure where no provider was involved.
          "no_text")
_TOKEN_RX = re.compile("|".join(re.escape(t) for t in TOKENS), re.I)

# A token that is NOT an application name. Each is a substring the scan must not count, with the
# reason it is not one — the same discipline as the allow-list, applied to the match rather than to
# the file, because these are not debt and will never be paid off.
NOT_AN_APPLICATION = (
    ("thesaurus:", "an ontology RELATION namespace (`thesaurus:related`), not the series"),
    ("_news_sm", "a spaCy model id (`ja_core_news_sm`), not a programme"),
    ("thesaurus.", "a Concept Model's declared op prefix, routed as data — not the series"),
    ("_thesaurus_", "the renderer for that op family's result"),
    ("llm_provider.py", "the LLM GATEWAY is where a model outcome is named — `no_text` there is "
                        "a true statement about a call this module made (ruling §2)"),
    ("llm_pool.py", "the same gateway's admission half"),
    ("TRANSIENT_REASONS", "the retry ladder keys on the gateway's own outcomes, which the ruling "
                          "keeps as the platform's (§2: 'retry policy stays the platform's, keyed "
                          "on the platform's own terms'). It READS the ids; it never writes one "
                          "onto a run that did not report it"),
)


def _is_application_hit(code, match):
    """Does this match name an APPLICATION, or is it one of the words that merely looks like one?"""
    for needle, _why in NOT_AN_APPLICATION:
        if needle.lower() in code.lower():
            return False
    return True

# Every entry is (path, token, why, owed-in). An entry that stops matching FAILS the eval too: a
# stale exemption is a claim about the code that is no longer true, and it would hide the next one.
ALLOWED = [
    # GROUP 4 PAID THIS LIST OFF (42 lines across 22 files on 2026-09-26 → 0). Every residue is now
    # either data the application declares (op attributes, hooks, `site.json`, `static`, `canon.json`,
    # `effectful_families`), a generated table (exempt by construction, below), or a classification
    # with its reason (NOT_AN_APPLICATION). An entry added here is debt with a reason and a seed —
    # and a STALE one fails.
]
_ALLOWED_BY_FILE = {}
for _p, _t, _w, _s in ALLOWED:
    _ALLOWED_BY_FILE.setdefault(_p, []).append((_t, _w, _s))


def main():
    print("=" * 78)
    print("The platform names no application")
    print("=" * 78)

    files = _platform_py()
    from lib.akasha.api import reserved as _RES
    app_pkg = _RES.app_package()
    check("the platform tree is found and is not trivially small", len(files) > 40, "%d files" % len(files))

    # ── 1. imports ───────────────────────────────────────────────────────────────────────────────
    rightward = []
    for path in files:
        src = open(path, encoding="utf-8", errors="replace").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            mod = ""
            if isinstance(n, ast.ImportFrom) and n.module:
                mod = n.module
            elif isinstance(n, ast.Import):
                mod = ",".join(a.name for a in n.names)
            for part in mod.split(","):
                part = part.strip()
                if part == app_pkg or part.startswith(app_pkg + "."):
                    rightward.append("%s:%d imports %s" % (path, n.lineno, part))
    check("no platform module imports anything of the application — it asks the registry, a hook "
          "or the dispatcher", not rightward, "%d: %s" % (len(rightward), rightward[:4]))
    check("…and no application module lives in the platform's concepts package (the registry "
          "classifies every class there as the platform's)",
          not [f for f in os.listdir("lib/akasha/concepts") if f.endswith(".py")
               and _RES.is_app_path(os.path.join("lib/akasha/concepts", f))])

    # ── 2. tokens ────────────────────────────────────────────────────────────────────────────────
    hits, by_file = [], {}
    for path in files:
        # A GENERATED table (a `GENERATED FILE` header) follows the manifests it is generated from;
        # it names what they declare and is never edited, so it is exempt by construction.
        if "GENERATED FILE" in open(path, encoding="utf-8", errors="replace").read(800):
            continue
        for lineno, code in _code_lines(path):
            m = _TOKEN_RX.search(code)
            if m and _is_application_hit(code, m):
                hits.append("%s:%d  %s" % (path, lineno, code.strip()[:96]))
                by_file.setdefault(path, 0)
                by_file[path] += 1
    unexpected = sorted(f for f in by_file if f not in _ALLOWED_BY_FILE)
    check("every file that still names an application is on the allow-list, with a reason",
          not unexpected, "%d: %s" % (len(unexpected), unexpected[:6]))
    stale = sorted(f for f in _ALLOWED_BY_FILE if f not in by_file)
    check("…and no allow-list entry is stale — an exemption for something already clean is a "
          "claim that is no longer true", not stale, "%d: %s" % (len(stale), stale))

    print("\n  the debt, as the allow-list records it")
    print("  " + "-" * 74)
    for path in sorted(_ALLOWED_BY_FILE):
        for tok, why, owed in _ALLOWED_BY_FILE[path]:
            print("   %-38s %-3s  %s" % (path.replace("lib/akasha/", "…/")[:38], owed[-1], why[:74]))
    print("   %d line(s) across %d file(s) still name an application."
          % (len(hits), len(by_file)))

    # ── scripts/*.py — in the order's grep, out of the module scan; each hit answered ───────────
    s_files = {}
    for p in _scripts_py():
        n = sum(1 for _l, c in _code_lines(p)
                if _TOKEN_RX.search(c) and _is_application_hit(c, _TOKEN_RX.search(c)))
        if n:
            s_files[p] = n
    s_allowed = {row[0] for row in SCRIPTS_ALLOWED}
    print("\n  scripts/*.py — the three the frontend handed back, each answered")
    print("  " + "-" * 74)
    for path, what, why, owed in SCRIPTS_ALLOWED:
        print("   %-26s %-4d %s" % (os.path.basename(path), s_files.get(path, 0), what))
        print("   %-26s      %s" % ("", why[:78]))
        print("   %-26s      → %s" % ("", owed))
    unexplained = {p: n for p, n in s_files.items() if p not in s_allowed}
    check("every scripts/*.py hit is ANSWERED — allow-listed with what it is and why it is not the "
          "platform naming an application", not unexplained,
          "%d file(s): %s" % (len(unexplained), sorted(unexplained)[:4]))
    check("RATCHET — scripts/*.py hits that are merely TOLERATED: %d (bound %d; never rises)"
          % (sum(unexplained.values()), SCRIPTS_RATCHET),
          sum(unexplained.values()) <= SCRIPTS_RATCHET)
    # A path that is NOT IN THIS TREE is not stale — a deployed cell bundles a subset of `scripts/`,
    # and an allow-list entry for a file that was never extracted there says nothing false. Only a
    # file that is PRESENT and clean is a claim that has expired.
    s_stale = sorted(p for p in s_allowed if os.path.exists(p) and p not in s_files)
    check("…and no scripts allow-list entry is stale — an exemption for a file that is already "
          "clean is a claim that is no longer true", not s_stale, str(s_stale))

    # ── the files this delivery cleared, asserted by name ───────────────────────────────────────
    for gone in ("lib/akasha/workbench/station.py",):
        check("`%s` is gone" % gone, not os.path.exists(gone))
    for clean, what in (("lib/akasha/workbench/autorun.py", "the driver"),
                        ("lib/akasha/workbench/provision.py", "the provisioning authority"),
                        ("lib/akasha/workbench/workload_provision.py", "provisioning"),
                        ("lib/akasha/workbench/llm.py", "the LLM stores"),
                        ("lib/akasha/workbench/admission.py", "admission"),
                        ("lib/akasha/source/bootstrap.py", "the corpus bootstraps"),
                        ("lib/akasha/workbench/x_broadcast.py", "the channel client")):
        n = sum(1 for _l, c in _code_lines(clean)
                if _TOKEN_RX.search(c) and _is_application_hit(c, _TOKEN_RX.search(c)))
        check("%s names no application (%s)" % (what, os.path.basename(clean)), n == 0, "%d line(s)" % n)

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the platform imports no user concept; every application name left in its "
          "modules is on a written allow-list with the seed it is owed in; and every hit in the "
          "dev-side script tree is answered, with nothing merely tolerated.")
    sys.exit(0)


if __name__ == "__main__":
    main()
