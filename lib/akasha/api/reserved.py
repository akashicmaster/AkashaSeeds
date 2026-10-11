"""
Reserved concept names and declaration roots — the two lists the platform decides by (the purge
order, 3 October, §1.2–§1.3; rule 4: decide by declared facts, never by an application's names).

RESERVED_CONCEPTS maps each concept name a platform engine mints to that engine. These are the ONLY
concept names platform code may test (`meta["concept"] == …`); an application never mints one.
DECLARATION_ROOTS are the directories the platform reads declarations from. It never reads a file
because of an application's name for it: it reads a ROOT, and what is in it is the application's.

THE APPLICATION ROOT (platform-spec v1, the purge order P5). The application lives under ONE
directory, `app/` beside the platform; every declaration root is relative to it, and this module is
the only place the platform names it. Everything under it is the application's; everything outside
it is the platform's (`owner_of`). The root is a deployment fact (`AKASHA_APP_DIR`, a path), so a
platform test can stand a fixture application in its place.
"""
import os
from typing import Dict

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
APP_DIR = "app"


def app_root() -> str:
    """The application root's absolute path: `AKASHA_APP_DIR`, else `<project>/app`."""
    return os.path.abspath(os.environ.get("AKASHA_APP_DIR") or os.path.join(_ROOT, APP_DIR))


def app_package() -> str:
    """The import package of the application root (its directory name; `app`), with its parent made
    importable — the application's modules are `<package>.concepts.<stem>`, `<package>.scripts.…`."""
    import sys as _sys
    parent = os.path.dirname(app_root())
    if parent not in _sys.path:
        _sys.path.insert(0, parent)
    return os.path.basename(app_root())


def is_app_path(path: str) -> bool:
    """Is a project-relative (or absolute) path under the application root?"""
    p = os.path.abspath(path if os.path.isabs(path) else os.path.join(_ROOT, path))
    r = app_root()
    return p == r or p.startswith(r + os.sep)

RESERVED_CONCEPTS: Dict[str, str] = {
    # the source engine
    **{c: "source" for c in ("source_item", "source_pool", "source_sample", "source_tally",
                             "source_acquisition", "source_bridge", "source_clock",
                             "source_evidence_profile", "source_external", "source_observation",
                             "source_snapshot", "source_stream")},
    # society, casts and agents
    **{c: "society" for c in ("society", "society_auto", "broadcast_msg", "bench_conn", "agent",
                              "cast")},
    "agent_state": "agent",
    # the workflow engine and sweeps
    **{c: "workflow" for c in ("workflow", "wf_entry", "wf_sweep_branch", "exec", "deviation")},
    **{c: "sweep" for c in ("sweep_def", "sweep_cond", "sweep_leaderboard")},
    # time: chronon (semantic) and cronon (the passive coordinate)
    "chronon": "chronon",
    **{c: "cronon" for c in ("cronon", "cronon_clock", "validity_membrane")},
    # the world axis
    **{c: "world" for c in ("world", "world_env", "world_sync")},
    # the workbench, provisioning and the gate's facts
    "bench": "workbench", "workload": "workbench", "capability": "workbench", "cap_build": "workbench",
    "fact": "gate",
    # heart services that mint atoms
    "llm_pool": "llm", "log": "log", "proj": "proj", "space": "space", "claim": "claim",
    "lens_compare": "lens",
}

# kind → path relative to the APPLICATION root. `templates` holds `%s` for the bench slug.
DECLARATION_ROOTS: Dict[str, str] = {
    "manifest":   "config/MANIFEST.json",
    "workloads":  "config/workbench/workloads",
    "templates":  "config/workbench/%s/templates",
    "sweeps":     "config/workbench/%s/sweeps",
    "profiles":   "config/profiles",
    "macros":     "config/macros",
    "source":     "config/source",
    "assign":     "config/assign.ak",
    "identities": "config/identities.json",
    "tier_policy": "config/tier_policy.json",
    "seed_recipes": "config/seed",
    "seeds":      "seeds",
    "exports":    "archives/exports",
    "curations":  "curations",
    "assets":     "assets",
    "concepts":   "concepts",
    "packs":      "ontology",
    "pages":      "archives",
    "series":     "config/series.json",
    "lexicon":    "config/lexicon.json",
    "tests":      "test",
}


def root(kind: str, bench: str = "") -> str:
    """The absolute path of a declaration root under the application root. `templates` and `sweeps`
    take the bench slug."""
    rel = DECLARATION_ROOTS[kind]
    if "%s" in rel:
        rel = rel % bench
    return os.path.join(app_root(), rel)


def tree_path(kind: str, bench: str = "") -> str:
    """The same root as a path relative to the project tree (`app/<root>`, '/'-separated) — for the
    generator side, which reads and packs the tree rather than a deployed application root."""
    rel = DECLARATION_ROOTS[kind]
    if "%s" in rel:
        rel = rel % bench
    return APP_DIR + "/" + rel


def owner_engine(concept: str) -> str:
    """The engine that reserves `concept`, or "" when it is not reserved (an application's)."""
    return RESERVED_CONCEPTS.get(str(concept or ""), "")
