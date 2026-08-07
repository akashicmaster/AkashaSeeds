"""
Akasha Kernel Dispatcher.
The single authoritative boundary between the Shell (api/, remote/) and the
cognitive engine (lib/). All JSON-RPC 2.0 requests enter through `dispatch()`.

[RESPONSIBILITIES]
- Bootstrap all kernel subsystems: HarmoniaEngine, AkashaManager, ContexaEngine
- Authenticate every request via IAM before touching a session
- Route method calls to the appropriate cognitive engine
- Return well-formed JSON-RPC 2.0 response dicts (never raise to the caller)

[WHAT DOES NOT LIVE HERE]
- CLI rendering, ANSI colors, multi-line input, pipe/redirect handling
- HTTP server startup, ASGI lifecycle
- Any import of api.*, remote.*, or services.*
"""

import os
import re
import sys
import time
import json
import uuid
import logging
import hashlib
from typing import Dict, Any, Optional, List, Callable

from lib.akasha.manager import AkashaManager
from lib.akasha.identity import Role, Capability
from lib.akasha.resolver import ContextResolver
from lib.akasha.kernel_methods import METHOD_TO_ACTION as _METHOD_TO_ACTION
from lib.akasha.consciousness import CosmosMapper
from lib.akasha import lexicon
from lib.akasha.pagination import paginate as _paginate, resolve_limit as _rlimit, resolve_offset as _roffset

try:
    from lib.akasha import __version__ as _AKASHA_VERSION
except ImportError:
    _AKASHA_VERSION = "dev"

logger = logging.getLogger("Akasha.Kernel")

# ── Transport trust levels ──────────────────────────────────────────────────
# Trust is a property of the *server-side transport binding*, set by the portal
# that received the request — never a value the client can supply.  It governs
# whether a bare client_id may assert an identity:
#
#   TRUST_NETWORK  (default) — untrusted remote (HTTP/ASGI, web worker, CGI).
#                              A privileged identity must prove itself with a
#                              signed akt: session token; a bare client_id is
#                              only ever accepted as an anonymous GUEST.
#   TRUST_LOCAL              — the local operator's stdio console.  The OS
#                              process boundary is the real gate, so a bare
#                              client_id (incl. the admin) is accepted.
#   TRUST_INTERNAL           — kernel-originated in-process dispatch (JCL worker,
#                              boot loader, self-dispatch).  Bare client_id and
#                              system.* process identities are accepted.
TRUST_NETWORK  = "network"
TRUST_LOCAL    = "local"
TRUST_INTERNAL = "internal"
_TRUSTED_TRANSPORTS = frozenset({TRUST_LOCAL, TRUST_INTERNAL})

# IAM actions whose handlers write graph atoms/links synchronously in the dispatch
# thread. Every graph-writing verb — memory write, alias, set.add, all concept-model
# op_new/op_set writes — maps to "write"; the link/meta verbs map to their own
# tokens; sync.pull writes atoms pulled from a peer. These are the methods the
# per-turn workspace seam wraps (single-route guard). Reads, status, drop (physical
# delete, never a commit()/put_link()) and job.submit (enqueues an async JCL job
# that writes under its OWN workspace) are intentionally absent — they never trip
# the guard, so wrapping them would only add empty-workspace overhead.
_WRITE_ACTIONS = frozenset({
    "write", "link.create", "link.reinforce", "meta.set", "sync.pull",
})

# Optional engines — degrade gracefully if missing
try:
    from lib.harmonia.engine import HarmoniaEngine
except ImportError:
    HarmoniaEngine = None  # type: ignore

try:
    from lib.contexa.engine import ContexaEngine
except ImportError:
    ContexaEngine = None  # type: ignore

try:
    from lib.jataka.engine import JatakaEngine
except ImportError:
    JatakaEngine = None  # type: ignore

try:
    from lib.akasha.vision import VisionEngine
except ImportError:
    VisionEngine = None  # type: ignore

try:
    from lib.harmonia.fileio import FileIO
    from lib.harmonia.infra import HarmoniaInfra
    from lib.harmonia.pipeline import (
        run_pipeline, FileSource, FileSink, InlineSource,
        TableSource, TableSink, DocSink, SetSource,
        LensScanSource, ConceptCastSink, ResponseSink,
        ContexaWebSource, ResponseIngestSink,
        SurveyAggregateSource, InterpretationSource,
        PresentTableSink, ScatterSink, NarrativeSink,
        CurationPathSource, PresentationSink, PresentationSceneSource, ExportSink,
    )
except ImportError:
    FileIO = None  # type: ignore
    HarmoniaInfra = None  # type: ignore

try:
    from lib.akasha.concepts.note import NoteConcept
except ImportError:
    NoteConcept = None  # type: ignore

try:
    from lib.akasha.concepts.log import LogConcept
except ImportError:
    LogConcept = None  # type: ignore

try:
    from lib.akasha.concepts.whiteboard import WhiteboardConcept
except ImportError:
    WhiteboardConcept = None  # type: ignore

try:
    from lib.akasha.concepts.fieldnote import FieldNoteConcept
except ImportError:
    FieldNoteConcept = None  # type: ignore

try:
    from lib.akasha.concepts.survey import SurveyConcept
except ImportError:
    SurveyConcept = None  # type: ignore

from lib.akasha.jcl.workspace_context import (
    active as _workspace_active,
    _in_workspace,
)
from lib.akasha.jcl import workflow_vocab as _wf

try:
    from lib.akasha.jcl import JCLWorker, JCLJob, JCLStep
    from lib.akasha.jcl.job import CLASS_BATCH_ATOM, CLASS_LINK, CLASS_MAINTENANCE
except ImportError:
    JCLWorker = None  # type: ignore
    JCLJob    = None  # type: ignore
    JCLStep   = None  # type: ignore
    CLASS_BATCH_ATOM = "batch_atom"  # type: ignore
    CLASS_LINK       = "link"        # type: ignore
    CLASS_MAINTENANCE = "maintenance"  # type: ignore

try:
    from lib.akasha.concepts.human import HumanConcept as _HumanConcept
except ImportError:
    _HumanConcept = None  # type: ignore

try:
    from lib.akasha.concepts.correspondence import CorrespondenceConcept as _CorrespondenceConcept
except ImportError:
    _CorrespondenceConcept = None  # type: ignore

try:
    from lib.akasha.concepts.map import MapConcept as _MapConcept
except ImportError:
    _MapConcept = None  # type: ignore

try:
    from lib.akasha.concepts.country import CountryConcept as _CountryConcept
except ImportError:
    _CountryConcept = None  # type: ignore

ScriptConcept = None  # ScriptConcept removed; kept as None for backward-compat guards

# ── Concept Model Registry ────────────────────────────────────────────────────
# Auto-discovers concept model plugins from concepts/ (Layer 2) and the
# session/ instance layer (Layer 3).  Commands in both layers are
# intentionally hidden from the main help system — see docs/concept-model-spec.md.
try:
    from lib.akasha.concepts.registry import ConceptRegistry as _ConceptRegistry
    _concept_registry = _ConceptRegistry()
    _here = os.path.dirname(__file__)
    _concept_registry.discover(
        os.path.join(_here, "concepts"),
        module_prefix="lib.akasha.concepts",
    )
    _concept_registry.discover(
        os.path.join(_here, "session"),
        module_prefix="lib.akasha.session",
    )
    # Inject registry into SpaceConcept so it can resolve model plugins
    # without circular imports.
    from lib.akasha.session import space as _space_mod
    _space_mod.set_registry(_concept_registry)
    import lib.akasha.concepts.lens as _lens_mod
    _lens_mod.set_registry(_concept_registry)
    # Activate module-level reference so router.py can augment itself lazily
    from lib.akasha.concepts import registry as _registry_module
    _registry_module.set_active(_concept_registry)
    # Merge auto-derived method→action entries into the live METHOD_TO_ACTION dict.
    # Existing hand-written entries are never overwritten (they take precedence).
    for _dyn_method, _dyn_action in _concept_registry.get_method_actions().items():
        if _dyn_method not in _METHOD_TO_ACTION:
            _METHOD_TO_ACTION[_dyn_method] = _dyn_action
except Exception as _reg_exc:
    logger.error("ConceptRegistry init failed: %s", _reg_exc)
    _concept_registry = None  # type: ignore

# ── Weaver — constituent-word tokenizer ──────────────────────────────────────
# Words extracted from atom descriptions are linked to their nucleus protowords
# via sys:refers_to (relation: "this atom refers to this concept").
# Stopwords are filtered so only semantically meaningful tokens are woven.
_WEAVE_STOPWORDS = frozenset({
    # English function words
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "not", "and", "or", "but",
    "for", "yet", "so", "nor", "to", "of", "in", "on", "at", "by", "as",
    "with", "this", "that", "these", "those", "it", "its", "i", "you",
    "he", "she", "we", "they", "them", "their", "our", "your", "his", "her",
    "who", "what", "which", "when", "where", "why", "how", "all", "each",
    "both", "few", "more", "most", "other", "some", "such", "no", "only",
    "own", "same", "than", "too", "very", "just", "about", "after",
    "before", "between", "into", "through", "during", "also", "then", "now",
    "if", "from", "up", "out", "over", "under", "again", "here", "there",
    "ever", "never", "often", "while", "although", "because", "since",
    "until", "has", "had", "its", "one", "two", "new", "old", "any",
    # Common abbreviation noise in descriptions
    "etc", "eg", "ie", "vs",
    # French/Spanish/German particles that appear in ontology descriptions
    "de", "la", "le", "et", "du", "les", "des", "en", "el", "und", "der",
})


def _tokenize_for_weave(text: str) -> List[str]:
    """Return deduplicated candidate concept tokens from a description string."""
    import re as _re
    seen: set = set()
    result: List[str] = []
    for tok in _re.split(r"[\W_]+", text.lower()):
        if len(tok) < 3:
            continue
        if tok in _WEAVE_STOPWORDS:
            continue
        if tok.isdigit():
            continue
        if tok not in seen:
            seen.add(tok)
            result.append(tok)
    return result


def _morph_to_rel(morph: dict) -> str:
    """
    Map Universal Dependencies morphological features (from SpaCy token.morph)
    to a morph: link relation string.

    Falls back to sys:inflection_of when no specific category is recognised,
    preserving the generic derivation link while allowing callers to distinguish
    typed relations (morph:plural, morph:past_tense, …) from untyped ones.
    """
    tense     = morph.get("Tense")
    verb_form = morph.get("VerbForm")
    number    = morph.get("Number")
    degree    = morph.get("Degree")
    case      = morph.get("Case")
    aspect    = morph.get("Aspect")
    polarity  = morph.get("Polarity")

    if verb_form == "Part":
        return "morph:past_participle" if tense == "Past" else "morph:progressive"
    if tense == "Past":
        return "morph:past_tense"
    if tense == "Pres" and verb_form == "Fin":
        return "morph:present"
    if verb_form == "Inf":
        return "morph:infinitive"
    if number == "Plur":
        return "morph:plural"
    if degree == "Comp":
        return "morph:comparative"
    if degree == "Sup":
        return "morph:superlative"
    if polarity == "Neg":
        return "morph:negative"
    if case:
        return f"morph:{case.lower()}"
    return "sys:inflection_of"


def _lemmatize_for_weave(text: str) -> List[tuple]:
    """
    Tokenize and lemmatize *text* for the Weaver pipeline.

    Returns [(surface, lemma, lang, morph)] tuples where morph is a dict of
    Universal Dependencies features (e.g. {'Tense': 'Past', 'VerbForm': 'Fin'}).
    Delegates to nlp_manager.lemmatize_tokens() when SpaCy is available.
    Falls back to (token, token, 'en', {}) when unavailable.

    Stopword/length/digit filtering is applied by the caller (_weave_atom).

    Robustness gate — SpaCy is OPT-IN, regex is the DEFAULT (why the default flipped): the boot
    weave runs UNATTENDED inside the single-writer daemon, and SpaCy's native pipeline
    (thinc/blis/numpy C-extensions) can HARD-CRASH the process — a segfault is not a Python
    exception, so the `try/except` below cannot catch it, and it takes the whole daemon down (the
    silent, deterministic boot death seen on Python 3.14 while weaving the `lexicon` pack). The
    weave is OPTIONAL background enrichment (the graph is fully usable without it), so it must not
    be able to kill the writer. Therefore:
      • Default: the stdlib regex floor — dependency-free, and it CANNOT crash the process. It
        still produces valid `word:` links (surface forms), just without lemma normalization.
      • `AKASHA_WEAVE_SPACY=1` opts INTO SpaCy lemmatization, for a deployment that has verified
        its SpaCy/thinc/numpy stack is stable on its interpreter.
      • Even with SpaCy enabled, MIXED / NON-LATIN text still bypasses it: the loaded model is
        monolingual English, so CJK/mixed-script input (e.g. a `nsdef:` description carrying
        `成果物`) yields garbage lemmas at best and is the crash trigger at worst — per CLAUDE.md's
        multi-locale-NLP note (mixed zh+ja+en is unsupported), it degrades to the regex floor.
      • `AKASHA_WEAVE_REGEX_ONLY=1` forces the floor even if the SpaCy opt-in is set.
    """
    import re as _re
    _use_spacy = os.environ.get("AKASHA_WEAVE_SPACY", "").strip().lower() in (
        "1", "yes", "true", "on")
    _regex_only = os.environ.get("AKASHA_WEAVE_REGEX_ONLY", "").strip().lower() not in (
        "", "0", "no", "false", "off")
    _non_latin = any(ord(c) > 0x2FF for c in text)          # beyond Latin-1+combining → not English
    if _use_spacy and not _regex_only and not _non_latin:
        try:
            from lib.harmonia.plugins.nlp import nlp_manager as _nlp
            pairs = _nlp.lemmatize_tokens(text)
            if pairs:
                return pairs
        except Exception:
            pass
    seen: set = set()
    result = []
    for tok in _re.split(r"[\W_]+", text.lower()):
        if tok and tok not in seen:
            seen.add(tok)
            result.append((tok, tok, "en", {}))
    return result


def _rss_mb():
    """This process's resident memory in MB (Linux /proc, stdlib only), or None off-Linux.
    Used by the boot memory heartbeat so a SILENT daemon death (OOM-killer SIGKILL / C-ext
    segfault — no Python traceback) still leaves a self-diagnosis in the log: the RSS trajectory
    right up to the last line tells OOM (RSS climbing to the host ceiling) apart from a hard
    crash at flat RSS. Akasha owns its own diagnosis — the operator is never asked to run dmesg."""
    try:
        with open("/proc/self/status") as _f:
            for _line in _f:
                if _line.startswith("VmRSS:"):
                    return int(_line.split()[1]) // 1024      # kB → MB
    except (OSError, ValueError, IndexError):
        pass
    return None


def _autolearn_disabled_reason() -> Optional[str]:
    """Decide whether the boot-time numpy autolearn (semantic + node embeddings) may run.
    Returns a human-readable reason string when it must be SKIPPED, or None when allowed.

    Same class of failure as the SpaCy weave gate in `_lemmatize_for_weave` — and the last
    native code left on the boot path once weave defaults to the regex floor: the two autolearn
    threads run numpy (PPMI+SVD, random-walk matrices) UNATTENDED inside the single-writer
    daemon shortly after boot. A numpy/BLAS C-extension segfault is NOT a Python exception, so
    the `try/except` in each `_run()` cannot catch it — it takes the whole writer down (the
    silent, deterministic boot death reproduced on Python 3.14 *after* SpaCy weave was already
    ruled out, and confirmed non-OOM: flat RSS, no dmesg OOM record). Autolearn is OPTIONAL
    enrichment: without it, atoms still carry the stdlib feature-hashing FLOOR vector
    (tensor.py), so semantic.search / dream / gap.scan degrade gracefully and never break.

      • `AKASHA_NO_AUTOLEARN`      → always skip (explicit; unchanged).
      • `AKASHA_FORCE_AUTOLEARN=1` → always run, overriding the interpreter gate below — for a
        deployment that has VERIFIED its numpy/BLAS stack is stable on its interpreter.
      • Default: RUN on Python < 3.14 (numpy wheels are mature there); SKIP on Python >= 3.14,
        where the numpy/BLAS wheels are still immature and have hard-crashed the boot daemon.
        The floor tier keeps the meaning layer usable until the stack is verified + forced on.

    This mirrors the weave decision exactly: never let optional native ML kill the writer.
    """
    _env = os.environ.get("AKASHA_NO_AUTOLEARN", "").strip().lower()
    if _env not in ("", "0", "no", "false", "off"):
        return "AKASHA_NO_AUTOLEARN set"
    _forced = os.environ.get("AKASHA_FORCE_AUTOLEARN", "").strip().lower() in (
        "1", "yes", "true", "on")
    if _forced:
        return None
    if sys.version_info >= (3, 14):
        return ("Python %d.%d — numpy/BLAS boot autolearn is default-off here (a native segfault "
                "in the learn thread would crash the writer); set AKASHA_FORCE_AUTOLEARN=1 once "
                "the numpy stack is verified stable on this interpreter" % sys.version_info[:2])
    return None


# Axis filter map shared between _handle_associate and _handle_associate_unwritten
_AXIS_PREFIXES: Dict[str, List[str]] = {
    "emotion": ["emo:"],
    "color":   ["word:color:", "calc:color"],
    "sense":   ["word:sense:", "calc:sense"],
    "time":    ["chrono:", "calc:time"],
    "context": ["calc:context", "calc:associated_with"],
    "story":   ["polti:", "story:"],
}


# Method → IAM action mapping imported from lib/akasha/kernel_methods.py


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ok(rid, data: Any) -> dict:
    return {"jsonrpc": "2.0", "result": data, "id": rid}

def _err(rid, code: int, message: str, data: Any = None) -> dict:
    e: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "error": e, "id": rid or str(uuid.uuid4())}


def _csl_calls_to_ak(calls) -> str:
    """Convert a list of CompiledCall objects to .ak format text."""
    lines = []
    for call in calls:
        if getattr(call, 'comment', None):
            lines.append(f"# {call.comment}")
        m = call.method
        p = call.params
        if m in ("define", "kernel.memory.define", "def"):
            name = p.get("name", "")
            desc = p.get("description", "")
            lines.append(f'def "{name}" "{desc}"')
        elif m in ("ln", "link.create", "kernel.memory.link"):
            src = p.get("src", "")
            dst = p.get("dst", "")
            rel = p.get("rel", "thesaurus:related")
            lines.append(f"ln {src} {dst} {rel}")
        elif m in ("al", "alias", "kernel.identity.alias"):
            atom_id = p.get("id", "")
            name    = p.get("name", "")
            lines.append(f"al {atom_id} {name}")
        elif m == "set.add":
            name    = p.get("name", "")
            atom_id = p.get("id", "")
            lines.append(f'set.add name="{name}" id="{atom_id}"')
        else:
            lines.append(f"# [method: {m}] {json.dumps(p, ensure_ascii=False)}")
    return "\n".join(lines)


def _is_sys_atom(item: dict) -> bool:
    """Return True for internally-managed system atoms (session anchors, etc.)."""
    raw_meta = item.get("meta")
    if not raw_meta:
        return False
    try:
        meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
        return str(meta.get("type", "")).startswith("sys:")
    except (json.JSONDecodeError, AttributeError):
        return False


def _is_external(raw_meta) -> bool:
    """True if an atom's meta marks it as external (fetched) content — provenance=external.
    Such atoms are excluded from semantic learning and from gap.scan so unvetted web text
    neither poisons the learned model nor is mistaken for a curation gap (ASI06)."""
    if not raw_meta:
        return False
    try:
        meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
        return str(meta.get("provenance", "")) == "external"
    except (json.JSONDecodeError, AttributeError):
        return False


def _readable(ctx, key: str) -> str:
    """A human-facing label for an atom key: its namespaced alias (`geo:athens`) if any,
    else a bareword alias, else a short key prefix. Result rows (sim/search/emotion.find)
    carry this as `name` so the shell shows names, not raw hashes."""
    try:
        aliases = ctx.get_aliases_by_key(key) or []
    except Exception:
        aliases = []
    named = [a for a in aliases if ":" in a]
    if named:
        return named[0]
    if aliases:
        return aliases[0]
    return str(key)[:12]


def _fmt_ts(ts) -> Optional[str]:
    """Unix timestamp → 'HH:MM:SS' (today) or 'YYYY-MM-DD HH:MM:SS' (older)."""
    if ts is None:
        return None
    import datetime as _dt
    try:
        dt  = _dt.datetime.fromtimestamp(ts)
        now = _dt.datetime.now()
        return (dt.strftime("%H:%M:%S") if dt.date() == now.date()
                else dt.strftime("%Y-%m-%d %H:%M:%S"))
    except (ValueError, OSError):
        return None


def _job_to_dict(job, brief: bool = False) -> dict:
    pct      = int(100 * job.step_done / job.step_count) if job.step_count else 0
    progress = f"{job.step_done}/{job.step_count}"
    if job.status == "RUNNING":
        progress += f" ({pct}%)"

    d: dict = {
        "job_id":     job.job_id,
        "owner":      job.owner,
        "label":      job.label,
        "status":     job.status,
        "progress":   progress,
        "step_done":  job.step_done,
        "step_count": job.step_count,
        "submitted":  _fmt_ts(job.submitted_at),
    }
    if job.completed_at:
        d["completed"] = _fmt_ts(job.completed_at)
        if job.submitted_at:
            d["elapsed_s"] = round(job.completed_at - job.submitted_at, 1)
    if job.error:
        d["error"] = job.error
    errs = getattr(job, "step_errors", [])
    if brief:
        if errs:
            d["step_errors"] = len(errs)   # count only in list view
    else:
        # Full detail for job.stat
        d["step_errors"]  = errs
        d["fail_fast"]    = getattr(job, "fail_fast", True)
        d["tx_id"]        = job.tx_id
        d["submitted_at"] = job.submitted_at
        d["completed_at"] = job.completed_at
    return d


# ---------------------------------------------------------------------------
# _NucleusWriteCtx — transparent write-routing proxy
# ---------------------------------------------------------------------------

class _NucleusWriteCtx:
    """
    A lightweight proxy that routes all put_* operations to the nucleus engine
    while delegating read operations (and everything else) to the local cortex.

    Constructed by _route() when scope=universal and the caller has librarian
    rights.  Handlers receive this object as `ctx` and do not need to know
    which store they are writing to.
    """

    def __init__(self, local, nucleus):
        self._loc = local
        self._nuc = nucleus

    # --- write surface -------------------------------------------------------

    def put_chunk(self, content, meta=None, author="system", scopes=None):
        """Write atom to nucleus; return content-addressed key."""
        return self._nuc.put_atom(content, meta or {}, author=author)

    def put_link(self, src, dst, rel, w=1.0, author="system"):
        """Write link to nucleus."""
        return self._nuc.put_link(src, dst, rel, w=w, author=author)

    def set_alias(self, key, name, force=False):
        """Register alias in nucleus with proto-word auto-creation. force=True bypasses
        first-wins (authoritative ontology re-import superseding a prior nucleus atom)."""
        return self._nuc.set_alias(key, name, force=force)

    def add_to_set(self, name, key):
        """Add key to a named set in nucleus."""
        return self._nuc.add_to_set(name, key)

    # --- alias resolution ----------------------------------------------------

    def resolve_alias(self, alias):
        """Prefer nucleus alias resolution; fall back to local cortex."""
        return (self._nuc.core.get_key_by_alias(alias)
                or self._loc.core.get_key_by_alias(alias))

    # --- delegate all other attributes to local cortex -----------------------

    def __getattr__(self, name):
        # All read operations (get_chunk, stream, get_adjacent_links, etc.)
        # use the local cortex which already has nucleus fallback built in.
        return getattr(self._loc, name)


# ---------------------------------------------------------------------------
# KernelDispatcher
# ---------------------------------------------------------------------------

class KernelDispatcher:
    """
    The cognitive engine gateway.
    Instantiated once at boot; shared across all portal types (stdio, ASGI, MCP…).
    """

    def __init__(self, series: str = "seeds", base_dir: str = "data"):
        self.series = series
        self.base_dir = base_dir

        self.harmonia = HarmoniaEngine() if HarmoniaEngine else None
        self.manager = AkashaManager(series_name=series, base_dir=base_dir)
        self.iam = self.manager.iam
        self.contexa = ContexaEngine(self.manager, self.harmonia) if ContexaEngine else None
        # Vision inference (image → labels). Lazy: no model/runtime touched until the
        # first image.profile call, so boot never installs or loads anything for it.
        self.vision = VisionEngine() if VisionEngine else None
        # General file import/export — the single Harmonia-owned disk I/O route (CSV/JSON/
        # MD/TXT). Confined to an allow-list of roots (data/import, data/export, data);
        # admins permit more via io.allow. Graph writes still go through the guarded path.
        self.fileio = FileIO(HarmoniaInfra()) if (FileIO and HarmoniaInfra) else None

        if self.harmonia:
            self._register_harmonia_plugins()

        # JCL worker — started after all other subsystems are ready so that
        # worker threads can safely call self.dispatch() and self.manager.
        # max_workers=1: the phase-1 atoms sentinel is appended to the LAST file's
        # JCL job.  With a single worker, every earlier atom job has already
        # completed by the time the sentinel is written — giving a sound guarantee
        # that all atoms are in nucleus before phase-2 links run.
        # With max_workers>1 the sentinel can fire while large earlier files are
        # still being processed, causing intermittent "not found" on recent atoms.
        # This matches the JCL design principle: serial writes over parallelism.
        #
        # Ownership: the JCL executor is Harmonia's initiator, not a kernel sibling.
        # The kernel builds it (it needs the dispatch ref) and hands ownership to
        # Harmonia; from here the kernel submits jobs via `harmonia.submit_job(...)`,
        # and `self.jcl_worker` is a read-only view onto Harmonia's executor.
        _jcl = JCLWorker(self, max_workers=1) if JCLWorker else None
        if self.harmonia and _jcl:
            self.harmonia.attach_jcl(_jcl)

        logger.info(
            f"[Kernel] Dispatcher online — series={series}, "
            f"harmonia={'on' if self.harmonia else 'off'}, "
            f"contexa={'on' if self.contexa else 'off'}, "
            f"jcl={'on' if self.jcl_worker else 'off'}"
        )

        # Boot-time ontology load — queue CSL files as JCL jobs if sentinel absent.
        # Runs in a daemon thread so boot is never blocked.
        if self.jcl_worker:
            import threading as _t
            _t.Thread(target=self._boot_load_ontology, daemon=True,
                      name="ont-boot-loader").start()

    @property
    def jcl_worker(self):
        """Read-only view onto Harmonia's JCL executor (job submission goes through
        `self.harmonia.submit_job`, not this)."""
        return self.harmonia.jcl if self.harmonia else None

    # ------------------------------------------------------------------
    # Boot-time ontology loader
    # ------------------------------------------------------------------

    def _boot_load_ontology(self) -> None:
        """
        Queue all ontology files (.ak and .csl) as JCL jobs on kernel boot if
        sentinels are absent.  Runs in a daemon thread — never blocks boot.

        Requires an admin user in IAM (created via genesis_rite).  If no admin
        exists yet (first boot before genesis), this is a no-op.
        """
        import time as _time
        import hashlib as _hl
        import shlex as _shlex
        from lib.akasha import lifecycle

        if not JCLJob or not JCLStep:
            return  # JCL imports failed at module load

        # Serve-only worker (spawned by akasha.py alongside the loader main process):
        # the MAIN process is the SOLE nucleus writer (it runs this boot-load + the
        # learn daemons). The uvicorn worker boots its own gateway against the SAME
        # nucleus; if it ALSO ran the boot-load, two processes would import the ontology
        # into the one store at once — a single-writer violation that kills the worker
        # on first boot ("Dead (Check logs)"), which is exactly what a slow full re-import
        # (bigger than the launcher's sentinel wait) triggered. Skip it here; the worker
        # only serves reads while main loads (WAL → concurrent readers are safe).
        if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
            logger.info("[Kernel] AKASHA_SERVE_ONLY — skipping ontology boot load (serve-only worker)")
            return

        # Boot memory heartbeat — self-diagnosis for a SILENT daemon death during the load
        # (OOM-killer SIGKILL / C-ext segfault leave NO Python traceback, so the process just
        # stops logging). This logs RSS every few seconds until the load finishes or shutdown,
        # so the LAST line before a silent death shows whether RSS was climbing to the host
        # ceiling (→ OOM) or flat (→ a hard crash, e.g. a C-extension on a bleeding-edge
        # interpreter). No operator dmesg needed — Akasha reports its own memory. Off with
        # AKASHA_NO_BOOTWATCH=1.
        if (os.environ.get("AKASHA_NO_BOOTWATCH", "").strip().lower() in ("", "0", "no", "false", "off")
                and not getattr(self, "_bootwatch_running", False)):
            self._bootwatch_running = True            # one heartbeat per process, not per reload
            def _bootwatch():
                _t0 = _time.time(); _peak = 0; _idle = 0
                _CAP = 900.0                                    # bounded to the boot window (~15min)
                while not lifecycle.is_shutting_down() and _time.time() - _t0 < _CAP:
                    rss = _rss_mb()
                    if rss is not None:
                        _peak = max(_peak, rss)
                        # name the JCL job in flight, if any — ties an RSS spike to a phase.
                        _cur = ""
                        try:
                            _jobs = self.jcl_worker.list_jobs() if self.jcl_worker else []
                            _run = [j for j in _jobs if getattr(j, "status", "") == "RUNNING"]
                            if _run:
                                _cur = getattr(_run[0], "label", "") or ""
                        except Exception:
                            _cur = ""
                        logger.info("[BootWatch] rss=%dMB peak=%dMB t=%.0fs job=%s",
                                    rss, _peak, _time.time() - _t0, _cur or "-")
                        # Once the load has been quiet (no running job) for a while, stop — the
                        # boot window is over; no need to heartbeat steady-state forever.
                        _idle = _idle + 1 if not _cur else 0
                        if _idle >= 10:                         # ~30s idle after the load settled
                            logger.info("[BootWatch] load settled — heartbeat off (peak=%dMB)", _peak)
                            self._bootwatch_running = False
                            return
                    for _ in range(6):                          # ~3s, but wake promptly on shutdown
                        if lifecycle.is_shutting_down():
                            return
                        _time.sleep(0.5)
                self._bootwatch_running = False
            import threading as _thr_bw
            _thr_bw.Thread(target=_bootwatch, name="boot-memwatch", daemon=True).start()

        # Wait briefly so the JCL worker threads are fully started
        _time.sleep(0.5)

        try:
            # Verify admin exists and has librarian privileges
            from lib.akasha.identity import Role
            try:
                admin_role = self.iam.authenticate("admin")
            except PermissionError:
                return  # no admin yet — genesis_rite not done

            if admin_role not in (Role.ADMIN, Role.LIBRARIAN):
                return

            admin_session = self.manager.get_session("admin")

            # Locate ontology directory relative to project root
            _kernel_dir  = os.path.dirname(os.path.abspath(__file__))  # lib/akasha/
            _lib_dir     = os.path.dirname(_kernel_dir)                  # lib/
            _project_dir = os.path.dirname(_lib_dir)                     # project root
            ont_dir = os.path.join(_project_dir, "ontology")
            if not os.path.exists(ont_dir):
                logger.info("[Kernel] No ontology/ directory found — skipping boot load")
                return

            def _collect(ext: str) -> List[str]:
                files: List[str] = []
                for root_d, _, names in os.walk(ont_dir):
                    for n in sorted(names):
                        if n.endswith(ext):
                            files.append(os.path.join(root_d, n))
                return files

            def _submit_file_job(fpath: str, steps_raw: List[dict], label: str) -> None:
                steps = [JCLStep(method=s["method"], params=s.get("params", {}))
                         for s in steps_raw]
                job = JCLJob(owner="admin", label=label, steps=steps, fail_fast=False)
                # Ontology atom phase — Class 2 (consistent as a set, not real-time).
                self.harmonia.submit_job(job, job_class=CLASS_BATCH_ATOM)

            # ── .ak files (vocab / thesaurus links) ───────────────────────────
            _AK_WRITE = frozenset({"w", "write", "kernel.memory.write",
                                   "def", "define", "kernel.memory.define"})
            _AK_MAP = {
                "w":   ("kernel.memory.write",  ["text"]),
                "write": ("kernel.memory.write", ["text"]),
                "def": ("kernel.memory.define",  ["name", "description"]),
                "define": ("kernel.memory.define", ["name", "description"]),
                "al":  ("alias",                 ["id", "name"]),
                "alias": ("alias",               ["id", "name"]),
                "ln":  ("kernel.memory.link",    ["src", "dst", "rel"]),
                "set.add": ("set.add",           ["name", "id"]),
            }

            def _parse_ak_line(raw: str):
                line = raw.strip()
                if not line or line.startswith("#"):
                    return None
                try:
                    parts = _shlex.split(line)
                except ValueError:
                    # Defensive strip: remove surrounding quotes left by plain split
                    parts = [p.strip('"\'') for p in line.split()]
                if not parts:
                    return None
                cmd = parts[0].lower()
                if cmd not in _AK_MAP:
                    return None
                method, arg_names = _AK_MAP[cmd]
                args = parts[1:]
                params: dict = {}
                # Separate keyword args (key=value) from positional args so that
                # `set.add name="set:foo" id="bar"` maps correctly.
                kw: dict = {}
                pos: list = []
                for token in args:
                    if "=" in token:
                        k, v = token.split("=", 1)
                        kw[k] = v
                    else:
                        pos.append(token)
                for i, aname in enumerate(arg_names):
                    if aname in kw:
                        params[aname] = kw[aname]
                    elif i < len(pos):
                        params[aname] = pos[i]
                    else:
                        params[aname] = ""
                # Mark write/define as universal so they go to nucleus
                if method in _AK_WRITE or method in ("kernel.memory.write", "kernel.memory.define"):
                    params["scope"] = "universal"
                return {"method": method, "params": params}

            # ── .ak files — two-phase load to eliminate ordering races ──────────
            # Phase 1: atom-only jobs (write/define/alias/set.add — NO links).
            #          The last atom job gets an "atoms:loaded" sentinel appended.
            # Phase 2: boot-load thread polls for the sentinel, then submits ONE
            #          link job containing ALL ln steps from ALL files.  By the
            #          time the link job runs every atom is guaranteed to be in
            #          nucleus, so alias resolution cannot fail on ordering.

            # Manifest hash: sha256 of (basename:size) for all files. Stat-only (no file
            # reads), so it is fast even for large ontologies, and it gates the PACK-LEVEL
            # phases (load / reconcile / csl / curations) — "did this pack's content change?"
            #
            # ⚠️ mtime is DELIBERATELY EXCLUDED. The seed self-extractor (python akasha_seeds_*.py)
            # is the supported deploy/recovery path, and unzip stamps EVERY extracted file with a
            # fresh mtime (it does not restore the source time). An mtime-inclusive manifest
            # therefore flipped every pack's hash on every re-extraction → every one of the ~25
            # packs re-entered load AND re-materialised its def-keys for reconcile (the heavy pass
            # that OOM-killed the Cell daemon; see the per-pack reconcile fix). That made the
            # per-pack incremental gating a no-op for the ONE path users actually deploy through.
            # Keying on (basename:size) is stable across re-extraction, so a deploy reloads ONLY
            # the packs whose content genuinely changed (different file list or byte size).
            #
            # A size-preserving edit (same byte count, changed bytes) is invisible to THIS gate,
            # but it is still caught downstream: the global-relations phase gates each file by a
            # full CONTENT hash and re-applies changed al/ln/set; the per-file atom sentinel is
            # likewise size-keyed, so mtime never bought an atom re-import here in the first place.
            # NOTE: re-import is ADDITIVE (content-addressed) — it applies additions and edits but
            # does not purge atoms deleted from the ontology; wipe <data>/central for a clean slate.
            def _manifest_hash(files: List[str]) -> str:
                parts = []
                for f in sorted(files):
                    try:
                        parts.append(f"{os.path.basename(f)}:{os.path.getsize(f)}")
                    except OSError:
                        parts.append(os.path.basename(f))
                return _hl.sha256("\n".join(parts).encode()).hexdigest()[:16]

            # ── Pack loading — flat ontology/{name}/ structure ─────────────
            # Packages are defined in ontology/REGISTRY.json.
            # autoload:true  → always loaded (base)
            # autoload:false → loaded only when listed in config/ontology_packs.json["enabled"]
            # Each pack has its own two-phase sentinel:
            #   ont:ak:atoms:loaded:{pack}:{hash}  — phase-1 complete
            #   ont:ak:loaded:{pack}:{hash}         — phase-2 complete

            RESERVED_DIRS = {"seeds", "thesaurus"}

            def _collect_from_dir(d, ext):
                files = []
                if os.path.isdir(d):
                    for root_d, _, names in os.walk(d):
                        for n in sorted(names):
                            if n.endswith(ext):
                                files.append(os.path.join(root_d, n))
                return sorted(files)

            def _read_registry():
                import json as _json
                reg_path = os.path.join(ont_dir, "REGISTRY.json")
                try:
                    with open(reg_path) as _f:
                        return _json.load(_f).get("packages", [])
                except Exception:
                    return []

            def _read_enabled_packs():
                import json as _json
                cfg = os.path.join(_project_dir, "config", "ontology_packs.json")
                try:
                    with open(cfg, "r") as _f:
                        return set(_json.load(_f).get("enabled", []))
                except Exception:
                    return set()

            def _read_load_all():
                # Service tiers (thesaurus/enterprise) ship config/ontology_packs.json
                # with "load_all": true — the standing instruction to auto-load EVERY
                # registered pack sequentially (in REGISTRY order), including specialist
                # B/C packs added after the seed was built. The seeds tier omits the
                # flag, so its optional packs stay opt-in (onto.pack.enable).
                import json as _json
                cfg = os.path.join(_project_dir, "config", "ontology_packs.json")
                try:
                    with open(cfg, "r") as _f:
                        return bool(_json.load(_f).get("load_all", False))
                except Exception:
                    return False

            # ── Filesystem-based pack sentinel helpers ─────────────────────────
            # These files are the authoritative "was pack X fully loaded?" record.
            # Independent of SQLite WAL behaviour — a plain file on disk survives
            # any backend swap, sync-mode change, or WAL corruption scenario.
            # DB sentinels (ont:ak:atoms:loaded:* / ont:ak:loaded:*) continue to
            # serve as within-session phase-coordination signals only.
            _sent_dir = os.path.join(self.base_dir, "central", "sentinels")
            os.makedirs(_sent_dir, exist_ok=True)

            def _sent_file(pack_name, phash):
                return os.path.join(_sent_dir, f"{pack_name}_{phash}.done")

            def _sent_exists(pack_name, phash):
                return os.path.exists(_sent_file(pack_name, phash))

            def _write_sent(pack_name, phash):
                path = _sent_file(pack_name, phash)
                with open(path, "w") as _fp:
                    _fp.write(str(_time.time()))
                    _fp.flush()
                    os.fsync(_fp.fileno())
                logger.info("[Kernel] Pack '%s': sentinel file written", pack_name)

            def _load_ak_pack(pack_name, ak_files):
                """
                Three-phase .ak load for one pack.

                Phase 1: atom-only JCL jobs → DB signal ont:ak:atoms:loaded:*
                Phase 2: link JCL job       → DB signal ont:ak:loaded:*
                         → filesystem sentinel {base_dir}/central/sentinels/{pack}_{hash}.done
                Phase 3: weave JCL job      → sys:refers_to + set:word:* links (background)

                The filesystem sentinel is the authoritative restart-skip signal.
                """
                if not ak_files:
                    logger.info("[Kernel] Pack '%s': no .ak files — skipping", pack_name)
                    return
                pmhash = _manifest_hash(ak_files)

                # Primary restart-skip check: filesystem sentinel.
                if _sent_exists(pack_name, pmhash):
                    logger.info("[Kernel] Pack '%s' already loaded (sentinel file) — skipping", pack_name)
                    return

                _pack_start = _time.time()

                # ── growth narration ──────────────────────────────────────────
                # Announce the theme now being woven so the progressive base1→
                # base2→base3 load reads as the world tree *growing*, whatever the
                # host speed.  The PACK.json "theme"/"label" is the human line.
                try:
                    import json as _pj
                    _pmeta = _pj.load(open(os.path.join(ont_dir, pack_name, "PACK.json")))
                    _theme = _pmeta.get("theme") or _pmeta.get("label") or pack_name
                except Exception:
                    _theme = pack_name
                logger.info("[Kernel] 🌱 growing — %s  (%s, %d files)",
                            _theme, pack_name, len(ak_files))

                atoms_text  = f"[ont:ak] Pack '{pack_name}' atoms written"
                atoms_key   = _hl.sha256(atoms_text.encode()).hexdigest()
                atoms_alias = f"ont:ak:atoms:loaded:{pack_name}:{pmhash}"
                done_text   = f"[ont:ak] Pack '{pack_name}' fully loaded"
                done_key    = _hl.sha256(done_text.encode()).hexdigest()
                done_alias  = f"ont:ak:loaded:{pack_name}:{pmhash}"

                pack_max_wait = max(1800, len(ak_files) * 60)
                atoms_done = admin_session.local_cortex.get_aliases_by_pattern(atoms_alias)
                all_link_steps: List[dict] = []
                all_atom_defs: List[dict] = []   # [{alias, text}] for weave phase

                if atoms_done:
                    # Atoms already written. Links/aliases/sets are handled by the single
                    # global relations phase after ALL packs (not per-pack) — so here we
                    # only re-collect atom defs for the (idempotent) weave phase.
                    logger.info("[Kernel] Pack '%s': atoms sentinel found — collecting defs for weave…", pack_name)
                    for fpath in ak_files:
                        try:
                            with open(fpath, "r", encoding="utf-8") as _f:
                                for raw in _f:
                                    s = _parse_ak_line(raw)
                                    if s is None:
                                        continue
                                    if s["method"] == "kernel.memory.define":
                                        _p = s["params"]
                                        _desc = _p.get("description", "")
                                        if _desc and not _desc.startswith("Conceptual hub:"):
                                            all_atom_defs.append({
                                                "alias": _p.get("name", ""),
                                                "text": _desc,
                                            })
                        except Exception as exc:
                            logger.warning("[Kernel] Pack '%s' defs (recovery) %s: %s",
                                           pack_name, os.path.basename(fpath), exc)
                else:
                    logger.info("[Kernel] Pack '%s': scanning %d files (phase 1)…",
                                pack_name, len(ak_files))
                    files_to_queue: List[tuple] = []
                    for fpath in ak_files:
                        basename = os.path.basename(fpath)
                        try:
                            atom_steps: List[dict] = []
                            with open(fpath, "r", encoding="utf-8") as _f:
                                for raw in _f:
                                    s = _parse_ak_line(raw)
                                    if s is None:
                                        continue
                                    if s["method"] in ("kernel.memory.link", "alias", "set.add"):
                                        # Deferred: ln / al / set.add all resolve a target to a
                                        # nucleus key, so they MUST run after EVERY pack's atoms
                                        # exist. Run per-pack (before a cross-pack target is
                                        # defined) they bind to the bare proto-word instead of the
                                        # real body atom (e.g. base1 linking base2's ingred:fruit:apple
                                        # attaches to the proto-word "apple"). Collected and run once,
                                        # in order alias→link→set, in the global relations phase below.
                                        continue
                                    else:
                                        if s["method"] == "kernel.memory.define":
                                            _p = s["params"]
                                            _desc = _p.get("description", "")
                                            if _desc and not _desc.startswith("Conceptual hub:"):
                                                all_atom_defs.append({
                                                    "alias": _p.get("name", ""),
                                                    "text": _desc,
                                                })
                                        atom_steps.append(s)
                        except Exception as exc:
                            logger.warning("[Kernel] Pack '%s' atoms %s: %s",
                                           pack_name, basename, exc)
                            continue

                        if not atom_steps:
                            continue

                        # Per-file restart-skip sentinel.
                        # Key includes file size so edits invalidate it automatically.
                        try:
                            _fsize = os.path.getsize(fpath)
                        except OSError:
                            _fsize = 0
                        f_alias = f"ont:ak:f:{pack_name}:{basename}:{_fsize:x}"
                        if admin_session.local_cortex.get_aliases_by_pattern(f_alias):
                            logger.debug("[Kernel] Pack '%s' '%s': file sentinel present — skip",
                                         pack_name, basename)
                            continue

                        # Append per-file sentinel at end of this file's atom job.
                        f_text = f"[ont:ak] Pack '{pack_name}' file '{basename}' atoms loaded"
                        f_key  = _hl.sha256(f_text.encode()).hexdigest()
                        atom_steps.append({"method": "write",
                                           "params": {"text": f_text, "scope": "universal"}})
                        atom_steps.append({"method": "alias",
                                           "params": {"id": f_key, "name": f_alias}})

                        files_to_queue.append((fpath, atom_steps, basename))

                    if files_to_queue:
                        # Pack-level atoms sentinel goes on the LAST file still being queued.
                        _lf, _ls, _lb = files_to_queue[-1]
                        _ls.append({"method": "write",
                                    "params": {"text": atoms_text, "scope": "universal"}})
                        _ls.append({"method": "alias",
                                    "params": {"id": atoms_key, "name": atoms_alias}})
                        logger.info("[Kernel] Pack '%s': queuing %d/%d atom jobs (phase 1)…",
                                    pack_name, len(files_to_queue), len(ak_files))
                        for _fp, _steps, _bn in files_to_queue:
                            _submit_file_job(_fp, _steps, f"ont.ak.{pack_name}:{_bn}")
                    else:
                        # All per-file sentinels present but pack sentinel absent.
                        # Write it now as a lightweight standalone job.
                        logger.info("[Kernel] Pack '%s': all file sentinels present — writing pack sentinel",
                                    pack_name)
                        self.harmonia.submit_job(JCLJob(
                            owner="admin",
                            label=f"ont.ak.atoms_sentinel:{pack_name}",
                            steps=[
                                JCLStep(method="write",
                                        params={"text": atoms_text, "scope": "universal"}),
                                JCLStep(method="alias",
                                        params={"id": atoms_key, "name": atoms_alias}),
                            ],
                            fail_fast=False,
                        ), job_class=CLASS_BATCH_ATOM)

                    logger.info("[Kernel] Pack '%s': waiting for phase-1 sentinel (max %ds)…",
                                pack_name, pack_max_wait)
                    _p1_start = _time.time()
                    while _time.time() - _p1_start < pack_max_wait:
                        _time.sleep(5)
                        if lifecycle.is_shutting_down(): return
                        if admin_session.local_cortex.get_aliases_by_pattern(atoms_alias):
                            logger.info("[Kernel] Pack '%s': phase-1 done in %.1fs",
                                        pack_name, _time.time() - _p1_start)
                            break
                    else:
                        logger.warning("[Kernel] Pack '%s': phase-1 timeout after %.1fs — skipping link phase",
                                       pack_name, _time.time() - _p1_start)
                        return

                if all_link_steps:
                    logger.info("[Kernel] Pack '%s': submitting %d link steps (phase 2)…",
                                pack_name, len(all_link_steps))
                    all_link_steps.append({"method": "write",
                                           "params": {"text": done_text, "scope": "universal"}})
                    all_link_steps.append({"method": "alias",
                                           "params": {"id": done_key, "name": done_alias}})
                    self.harmonia.submit_job(JCLJob(
                        owner="admin",
                        label=f"ont.ak.links:{pack_name}",
                        steps=[JCLStep(method=s["method"], params=s.get("params", {}))
                               for s in all_link_steps],
                        fail_fast=False,
                    ))
                else:
                    self.harmonia.submit_job(JCLJob(
                        owner="admin", label=f"ont.ak.sentinel:{pack_name}", steps=[
                            JCLStep(method="write",
                                    params={"text": done_text, "scope": "universal"}),
                            JCLStep(method="alias",
                                    params={"id": done_key, "name": done_alias}),
                        ], fail_fast=False))

                # Wait for phase-2 DB sentinel (written by link/sentinel job above),
                # then write the filesystem sentinel so restart-skip is durable.
                logger.info("[Kernel] Pack '%s': waiting for phase-2 completion (max %ds)…",
                            pack_name, pack_max_wait)
                _p2_start = _time.time()
                while _time.time() - _p2_start < pack_max_wait:
                    _time.sleep(5)
                    if lifecycle.is_shutting_down(): return
                    if admin_session.local_cortex.get_aliases_by_pattern(done_alias):
                        _write_sent(pack_name, pmhash)
                        logger.info("[Kernel] Pack '%s': phase-2 done in %.1fs",
                                    pack_name, _time.time() - _p2_start)
                        break
                else:
                    logger.warning("[Kernel] Pack '%s': phase-2 timeout after %.1fs — sentinel not written",
                                   pack_name, _time.time() - _p2_start)

                # Phase 3 — Weave: link each atom's description tokens to nucleus protowords.
                # Runs as a single LOW-priority JCL job after phases 1 and 2 are done.
                # Idempotent: duplicate put_link calls are silently ignored by the backend.
                # Resilience valve: the weave is OPTIONAL background enrichment ("while
                # sleeping") — the graph is fully usable without it (dive/explore/read work off
                # the atoms + relations already loaded). If a weave is ever the thing taking the
                # daemon down (e.g. a fragile NLP C-extension on a bleeding-edge interpreter, or
                # memory pressure), AKASHA_NO_BOOT_WEAVE=1 keeps the writer alive by skipping it.
                # The word-level links can be (re)built later with `onto.reload`.
                _skip_weave = os.environ.get("AKASHA_NO_BOOT_WEAVE", "").strip().lower() not in (
                    "", "0", "no", "false", "off")
                _p3_queued = False
                if _skip_weave and all_atom_defs:
                    logger.info("[Kernel] Pack '%s': AKASHA_NO_BOOT_WEAVE — skipping the weave "
                                "(%d atoms); graph is usable, word-links deferred.",
                                pack_name, len(all_atom_defs))
                if not _skip_weave and all_atom_defs and self.jcl_worker and JCLJob and JCLStep:
                    # Chunk the weave into many steps (not one monolithic step): the job then
                    # reports visible progress (k/M) and the single JCL worker can YIELD to
                    # higher-priority ready jobs (e.g. canon normalization) at every chunk
                    # boundary. Weave is background enrichment ("while sleeping"), so it runs at
                    # the IDLE (maintenance) class — the structural canon pass, which populates
                    # the reading surfaces, is NORMAL class and therefore runs ahead of it.
                    _WEAVE_CHUNK = 400
                    _weave_steps = [
                        JCLStep(method="sys.weaver.weave_batch",
                                params={"items": all_atom_defs[_wi:_wi + _WEAVE_CHUNK]})
                        for _wi in range(0, len(all_atom_defs), _WEAVE_CHUNK)
                    ]
                    self.harmonia.submit_job(JCLJob(
                        owner="admin",
                        label=f"sys.weaver.batch:{pack_name}",
                        steps=_weave_steps,
                        fail_fast=False,
                    ), job_class=CLASS_MAINTENANCE)
                    _p3_queued = True

                _total = _time.time() - _pack_start
                logger.info(
                    "[Kernel] Pack '%s': load complete — total %.1fs | "
                    "files=%d atoms=%d links=%d weave=%s",
                    pack_name, _total, len(ak_files), len(all_atom_defs),
                    len(all_link_steps),
                    f"queued({len(all_atom_defs)} atoms)" if _p3_queued else "skipped",
                )

            # ── Load packs in REGISTRY.json order ─────────────────────────────
            # autoload:true  → always load (base)
            # load_all:true  → load EVERY registered pack (thesaurus/service tiers)
            # autoload:false → otherwise, load only if the pack name is in
            #                  config/ontology_packs.json["enabled"] (seeds opt-in)
            _enabled  = _read_enabled_packs()
            _load_all = _read_load_all()
            if _load_all:
                logger.info("[Kernel] load_all is set — auto-loading every registered pack sequentially")
            for _pkg in _read_registry():
                _pname     = _pkg.get("name", "")
                _autoload  = _pkg.get("autoload", False)
                if not _pname or _pname in RESERVED_DIRS:
                    continue
                if not _autoload and not _load_all and _pname not in _enabled:
                    continue
                _pack_dir = os.path.join(ont_dir, _pname)
                if not os.path.isdir(_pack_dir):
                    logger.warning("[Kernel] Pack '%s': directory not found — skipping", _pname)
                    continue
                _load_ak_pack(_pname, _collect_from_dir(_pack_dir, ".ak"))

            # Packs enabled in config but absent from REGISTRY (user-added externals)
            _registry_names = {p.get("name") for p in _read_registry()}
            for _pname in sorted(_enabled - _registry_names):
                if _pname in RESERVED_DIRS:
                    continue
                _pack_dir = os.path.join(ont_dir, _pname)
                if os.path.isdir(_pack_dir):
                    logger.info("[Kernel] Pack '%s': enabled but not in REGISTRY — loading", _pname)
                    _load_ak_pack(_pname, _collect_from_dir(_pack_dir, ".ak"))
                else:
                    logger.warning("[Kernel] Enabled pack '%s': not found in ontology/", _pname)

            # ── Global relations phase — run ALL al / ln / set.add AFTER every pack's
            # atoms exist. Every one of these resolves a target to a nucleus key, so run
            # per-pack (before a cross-pack target is defined) it binds to the bare
            # proto-word instead of the real body atom — e.g. base1's
            #   al ingred:fruit:apple apple   /   ln ingred:fruit:apple score:0.25 rec:acidity
            # attaches to the proto-word "apple" because base2 defines ingred:fruit:apple.
            # v1.0 ran links as one all-packs job; v1.1's per-pack split reintroduced the
            # ordering bug. Fix: collect al/ln/set across the active packs and run them as
            # ONE deferred job in order alias→link→set (so links/sets can resolve by alias),
            # gated by a content-hash sentinel. All three are idempotent, so a re-run after a
            # new pack is enabled is safe.
            try:
                _active_dirs: List[str] = []
                for _pkg in _read_registry():
                    _pn = _pkg.get("name", "")
                    if not _pn or _pn in RESERVED_DIRS:
                        continue
                    if not _pkg.get("autoload", False) and not _load_all and _pn not in _enabled:
                        continue
                    _d = os.path.join(ont_dir, _pn)
                    if os.path.isdir(_d):
                        _active_dirs.append(_d)
                _reg_names = {p.get("name") for p in _read_registry()}
                for _pn in sorted(_enabled - _reg_names):
                    if _pn in RESERVED_DIRS:
                        continue
                    _d = os.path.join(ont_dir, _pn)
                    if os.path.isdir(_d):
                        _active_dirs.append(_d)

                # FILE-LEVEL incremental (was: re-read EVERY file and re-apply EVERY al/ln/set
                # whenever one GLOBAL relations hash changed — so adding one small .ak file to a
                # big pack re-applied the entire ontology's relations). Now each .ak file carries
                # its own CONTENT-HASH sentinel: a file whose content is unchanged is skipped
                # entirely (not read, its relations not re-applied), and only NEW/CHANGED files'
                # relations are collected + applied. Adding one file touches only that file.
                # Correctness holds: targets in unchanged files were aliased on a prior boot (their
                # aliases already resolve), and within this batch the ordered al→ln→set guarantees
                # a changed file's links/sets resolve names defined in the same batch.
                _al_steps: List[dict] = []
                _ln_steps: List[dict] = []
                _set_steps: List[dict] = []
                _relfile_sentinels: List[tuple] = []      # (sentinel_name, filehash) to write on success

                def _setadd_in_nucleus(_content_bytes) -> bool:
                    """True if this file has NO set.add, or a representative set.add member is
                    present in its target set IN THE NUCLEUS. False when it carries set.add whose
                    sampled members are NOT in the nucleus set — the guest-invisible bug where a
                    prior boot routed the membership into the writer's private cortex (a local
                    'Conceptual hub' shadowed the nucleus atom). Nucleus-only on purpose: local
                    membership is exactly what we must re-route. Lets the relations phase RE-APPLY
                    such a file even though its content hash is unchanged, self-healing stuck
                    cuisine/pairing sets on the next boot (the routing fix then lands them in the
                    nucleus)."""
                    _nuc = getattr(admin_session, "nucleus", None)
                    if _nuc is None:
                        return True
                    _sampled = 0
                    try:
                        for _rw in _content_bytes.decode("utf-8", "replace").splitlines():
                            _ss = _parse_ak_line(_rw)
                            if not _ss or _ss["method"] != "set.add":
                                continue
                            _nm = _ss["params"].get("name", ""); _idv = _ss["params"].get("id", "")
                            if not _nm or not _idv:
                                continue
                            _k = _nuc.core.get_key_by_alias(_idv) or _idv
                            _mem = set(_nuc.core.get_collection_members(_nm) or [])
                            if _k in _mem or _idv in _mem:
                                return True                # a member is in the nucleus set → trust it
                            _sampled += 1
                            if _sampled >= 5:
                                return False
                    except Exception:
                        return True                        # never force churn on a read/parse error
                    return _sampled == 0                   # no set.add → OK; had some, none in nucleus → re-apply

                for _d in _active_dirs:
                    _pn_r = os.path.basename(_d)
                    for _fp in _collect_from_dir(_d, ".ak"):
                        _bn_r = os.path.basename(_fp)
                        try:
                            _content_r = open(_fp, "rb").read()
                        except OSError as _exc:
                            logger.warning("[Kernel] Global relations read %s: %s", _fp, _exc)
                            continue
                        _fh_r = _hl.sha256(_content_r).hexdigest()[:16]
                        _sname_r = "_relfile_" + (_pn_r + "__" + _bn_r).replace(
                            os.sep, "_").replace(".", "_").replace(":", "_")
                        if _sent_exists(_sname_r, _fh_r):
                            # Unchanged file → its relations are normally already applied. But if it
                            # carries set.add whose members are NOT in the nucleus set (routed to a
                            # private cortex on a prior boot → guest-invisible), re-apply so the
                            # nucleus-first routing in _handle_set_add lands them where guests read.
                            if _setadd_in_nucleus(_content_r):
                                continue
                            logger.info("[Kernel] Global relations: '%s' is sentinel'd but its set.add "
                                        "members are not in the nucleus — re-applying (self-heal).", _bn_r)
                        try:
                            for _raw in _content_r.decode("utf-8", "replace").splitlines():
                                _s = _parse_ak_line(_raw)
                                if not _s:
                                    continue
                                if _s["method"] == "alias":
                                    _al_steps.append(_s)
                                elif _s["method"] == "kernel.memory.link":
                                    _ln_steps.append(_s)
                                elif _s["method"] == "set.add":
                                    _set_steps.append(_s)
                        except Exception as _exc:
                            logger.warning("[Kernel] Global relations scan %s: %s", _fp, _exc)
                            continue                       # do NOT sentinel a file we failed to parse
                        _relfile_sentinels.append((_sname_r, _fh_r))

                # Ordered: aliases first (so ln/set can resolve short names), then links,
                # then set memberships. Single FIFO job guarantees the order.
                _rel_steps = _al_steps + _ln_steps + _set_steps
                if not _rel_steps and not _relfile_sentinels:
                    logger.info("[Kernel] Global relations: no changed .ak files — skipping")
                if _rel_steps:
                    _sig = "\n".join(
                        f"{_s['method']}|{_s['params'].get('id','')}|"
                        f"{_s['params'].get('name','')}|{_s['params'].get('src','')}|"
                        f"{_s['params'].get('dst','')}|{_s['params'].get('rel','')}"
                        for _s in _rel_steps)
                    _rhash = _hl.sha256(_sig.encode()).hexdigest()[:16]
                    if True:
                        _rel_text  = "[ont:ak] Global relations (al/ln/set) applied"
                        _rel_key   = _hl.sha256((_rel_text + _rhash).encode()).hexdigest()
                        _rel_alias = f"ont:ak:relations:all:{_rhash}"
                        logger.info("[Kernel] Global relations phase: %d aliases + %d links + "
                                    "%d set.add across %d CHANGED file(s)…",
                                    len(_al_steps), len(_ln_steps), len(_set_steps),
                                    len(_relfile_sentinels))
                        _job_steps = [JCLStep(method=_s["method"], params=_s.get("params", {}))
                                      for _s in _rel_steps]
                        _job_steps.append(JCLStep(method="write",
                                                  params={"text": _rel_text, "scope": "universal"}))
                        _job_steps.append(JCLStep(method="alias",
                                                  params={"id": _rel_key, "name": _rel_alias}))
                        self.harmonia.submit_job(JCLJob(
                            owner="admin", label="ont.ak.relations:all",
                            steps=_job_steps, fail_fast=False,
                        ))
                        _rel_wait = max(3600, len(_rel_steps))
                        _r_start = _time.time()
                        while _time.time() - _r_start < _rel_wait:
                            _time.sleep(5)
                            if lifecycle.is_shutting_down(): return
                            if admin_session.local_cortex.get_aliases_by_pattern(_rel_alias):
                                # Job applied every changed file's relations → gate each changed
                                # file at its content hash, so an unchanged next boot skips it.
                                for _sn, _fh in _relfile_sentinels:
                                    _write_sent(_sn, _fh)
                                logger.info("[Kernel] Global relations phase done in %.1fs",
                                            _time.time() - _r_start)
                                break
                        else:
                            logger.warning("[Kernel] Global relations phase timeout after %.1fs",
                                           _time.time() - _r_start)
                elif _relfile_sentinels:
                    # Changed files that carried NO al/ln/set (def-only) — nothing to apply, but
                    # they must still be gated so they are not re-scanned every boot.
                    for _sn, _fh in _relfile_sentinels:
                        _write_sent(_sn, _fh)
                    logger.info("[Kernel] Global relations: %d changed def-only file(s) gated",
                                len(_relfile_sentinels))
            except Exception as _exc:
                logger.warning("[Kernel] Global relations phase error: %s", _exc)

            # ── Canonical normalization phase — derive the Product·Component·Method
            # structure (sys:is_a role, :all / :with_recipe sets, sys:method_of + product
            # mint-up, sys:made_from) AUTOMATICALLY from what every pack just loaded. Runs
            # after all atoms + relations exist, once per content change (sentinel-gated),
            # as a background JCL job. No pack authors these links by hand and no user ever
            # runs a migration command — the law lives in lib/akasha/canon.py and is applied
            # at every ingestion (this boot path also fires on onto.reload / onto.pack.enable).
            try:
                # Gate on "did any .ak file change this boot?" — the normalizer's role/method/
                # lexeme plan is GRAPH-derived (stable), but its link canonicalization reads the
                # links ingested this boot (`_ln_steps`, now file-incremental). On an UNCHANGED
                # restart that link set is empty, which would shift the plan hash and re-run canon
                # every boot; gating on a real change keeps the unchanged restart a true no-op,
                # while an incremental add still (re)derives roles for the new atoms + canonicalises
                # the new links.
                _files_changed_this_boot = bool(locals().get("_relfile_sentinels"))
                from lib.akasha.ontology_normalize import OntologyNormalizer as _Norm
                _cores = [getattr(admin_session.local_cortex, "core", None),
                          getattr(getattr(admin_session, "nucleus", None), "core", None)]
                _canon_steps = (_Norm(_cores).plan(link_steps=locals().get("_ln_steps", []))
                                if _files_changed_this_boot else [])
                if not _files_changed_this_boot:
                    logger.info("[Kernel] Canonical normalization: no changed .ak files — skipping")
                if _canon_steps:
                    _csig = "\n".join(
                        f"{_s['method']}|{_s['params'].get('name','')}|{_s['params'].get('src','')}|"
                        f"{_s['params'].get('dst','')}|{_s['params'].get('rel','')}|"
                        f"{_s['params'].get('id','')}" for _s in _canon_steps)
                    _chash = _hl.sha256(_csig.encode()).hexdigest()[:16]
                    if _sent_exists("_canon", _chash):
                        logger.info("[Kernel] Canonical normalization already applied (sentinel) — skipping")
                    else:
                        _ctext  = "[ont:ak] Canonical Product/Component/Method normalization applied"
                        _ckey   = _hl.sha256(_ctext.encode()).hexdigest()
                        _calias = f"ont:ak:canon:{_chash}"
                        logger.info("[Kernel] Canonical normalization phase: %d steps…",
                                    len(_canon_steps))
                        _cjs = [JCLStep(method=_s["method"], params=_s.get("params", {}))
                                for _s in _canon_steps]
                        _cjs.append(JCLStep(method="write",
                                            params={"text": _ctext, "scope": "universal"}))
                        _cjs.append(JCLStep(method="alias", params={"id": _ckey, "name": _calias}))
                        # NORMAL class so the structural pass (which populates the reading
                        # surfaces — meal:all / drink:all / made_from / method_of) runs AHEAD of
                        # the IDLE-class background weave. Its 43k+ steps already yield between
                        # steps, so higher-priority work is never starved.
                        self.harmonia.submit_job(JCLJob(
                            owner="admin", label="ont.ak.canon:normalize",
                            steps=_cjs, fail_fast=False), job_class=CLASS_BATCH_ATOM)
                        _cwait = max(3600, len(_canon_steps))
                        _c0 = _time.time()
                        while _time.time() - _c0 < _cwait:
                            _time.sleep(5)
                            if lifecycle.is_shutting_down(): return
                            if admin_session.local_cortex.get_aliases_by_pattern(_calias):
                                _write_sent("_canon", _chash)
                                logger.info("[Kernel] Canonical normalization done in %.1fs",
                                            _time.time() - _c0)
                                break
                        else:
                            logger.warning("[Kernel] Canonical normalization phase timeout")
            except Exception as _exc:
                logger.warning("[Kernel] Canonical normalization phase error: %s", _exc)

            # ── Ontology reconciliation phase — retire atoms a pack no longer contributes
            # (the data-side analog of the seed CODE prune). Additive re-import handles adds +
            # edits; this adds the missing REMOVAL half so a retired concept doesn't linger
            # forever in an operation-mode server without a data wipe. Fenced so it can NEVER
            # touch user knowledge: provenance="ontology" + no user access scope + no still-owning
            # pack (ref-counted). Soft-evict only (recoverable); hard drop is superuser-only via
            # onto.reconcile compact=yes. Sentinel-gated (runs once per ontology content change)
            # and idempotent. Default ON for load_all/server tiers; AKASHA_ONTO_RECONCILE
            # overrides. Spec: docs/for-llm/ontology-reconciliation-spec.md.
            try:
                _recon_on = os.environ.get(
                    "AKASHA_ONTO_RECONCILE", "1" if _load_all else "0"
                ).strip().lower() not in ("0", "no", "false", "off", "")
                if _recon_on:
                    from lib.akasha.ontology_reconcile import OntologyReconciler as _Recon
                    _R = _Recon(admin_session.nucleus)
                    _recon_packs: List[str] = []
                    for _pkg in _read_registry():
                        _pn = _pkg.get("name", "")
                        if not _pn or _pn in RESERVED_DIRS:
                            continue
                        if not _pkg.get("autoload", False) and not _load_all and _pn not in _enabled:
                            continue
                        if os.path.isdir(os.path.join(ont_dir, _pn)):
                            _recon_packs.append(_pn)
                    # PER-PACK gating (was ONE GLOBAL sentinel over every pack's manifest). The
                    # global sentinel meant ANY single pack change invalidated it and re-ran the
                    # reconcile for ALL packs — re-materialising each pack's def-keys AND re-stamping
                    # them on top of the fully-resident graph. On an incremental add (one small file
                    # dropped into a big pack) that peak OOM-killed the Cell daemon mid-reload. Now
                    # each pack is gated by its OWN manifest sentinel, exactly like the load phase:
                    # only a pack whose .ak content actually changed is reconciled, so an incremental
                    # add touches ONE pack, never all 25. The reconcile itself retires only
                    # (old_ledger − new_keys), so an additive-only change (nothing dropped) retires
                    # nothing and stays bounded to that single pack.
                    _total_retired = 0
                    _reconciled_n = 0
                    for _pn in _recon_packs:
                        try:
                            _pmh = _manifest_hash(_collect_from_dir(os.path.join(ont_dir, _pn), ".ak"))
                            if _sent_exists("_reconcile_" + _pn, _pmh):
                                continue                        # unchanged since last reconcile → skip
                            _keys, _names = self._pack_def_keys(admin_session, _pn)
                            if not _names:
                                # empty / failed parse — do NOT write a sentinel (retry next boot),
                                # and never let an empty new_keys wipe the ledger via reconcile.
                                continue
                            _R.stamp_provenance(_pn, list(_keys))
                            _rep = _R.reconcile(_pn, _keys, dry_run=False)
                            if _rep["retired"]:
                                _total_retired += len(_rep["retired"])
                                logger.info("[Kernel] Reconcile '%s': retired %d atom(s): %s",
                                            _pn, len(_rep["retired"]), _rep["retired"][:10])
                            _write_sent("_reconcile_" + _pn, _pmh)   # gate THIS pack at THIS manifest
                            _reconciled_n += 1
                        except Exception as _pe:
                            # DEGRADE, never crash the daemon: a pack that fails to reconcile is left
                            # as-is (no sentinel → retried next boot); the process stays alive so the
                            # rest of the ontology still serves. (Same posture as the dive OOM fix.)
                            logger.warning("[Kernel] Reconcile '%s' degraded (skipped): %s", _pn, _pe)
                    if _reconciled_n:
                        logger.info("[Kernel] Ontology reconcile done — %d atom(s) retired across "
                                    "%d changed pack(s)", _total_retired, _reconciled_n)
            except Exception as _exc:
                logger.warning("[Kernel] Ontology reconcile phase error: %s", _exc)

            # ── .csl files (concept graph) ─────────────────────────────────────
            _csl_files_probe = _collect(".csl")
            _csl_mhash = _manifest_hash(_csl_files_probe) if _csl_files_probe else "empty"

            _SENT_TEXT  = "[ont:csl] Ontology CSL scripts loaded"
            _SENT_KEY   = _hl.sha256(_SENT_TEXT.encode()).hexdigest()
            _SENT_ALIAS = f"ont:csl:loaded:{_csl_mhash}"

            csl_loaded = admin_session.local_cortex.get_aliases_by_pattern(_SENT_ALIAS)
            if not csl_loaded:
                csl_files = _csl_files_probe
                if csl_files:
                    logger.info("[Kernel] Queuing %d .csl ontology files as JCL boot jobs…", len(csl_files))
                    for idx, fpath in enumerate(csl_files):
                        try:
                            with open(fpath, "r", encoding="utf-8") as _f:
                                source = _f.read()
                            steps_raw = [{"method": "csl.run", "params": {"script": source}}]
                            if idx == len(csl_files) - 1:
                                steps_raw.append({
                                    "method": "write",
                                    "params": {"text": _SENT_TEXT, "scope": "universal"},
                                })
                                steps_raw.append({
                                    "method": "alias",
                                    "params": {"id": _SENT_KEY, "name": _SENT_ALIAS},
                                })
                            _submit_file_job(fpath, steps_raw,
                                             f"ont.csl.boot:{os.path.basename(fpath)}")
                        except Exception as exc:
                            logger.warning("[Kernel] boot-load .csl: could not queue %s: %s",
                                           os.path.basename(fpath), exc)
                    logger.info("[Kernel] .csl boot load queued (%d files)", len(csl_files))
                else:
                    # No ontology .csl (e.g. a minimal seeds series without the thesaurus
                    # pack). The ont:csl sentinel is normally written by the last .csl job;
                    # with zero .csl jobs it would never fire, so the curations phase below
                    # would wait out its full timeout and skip. Queue a sentinel-only job —
                    # it runs AFTER the already-queued .ak atom jobs (same class, FIFO), so
                    # it still marks "atoms are loaded" and the curations phase proceeds.
                    _submit_file_job("(no ontology csl)", [
                        {"method": "write", "params": {"text": _SENT_TEXT, "scope": "universal"}},
                        {"method": "alias", "params": {"id": _SENT_KEY, "name": _SENT_ALIAS}},
                    ], "ont.csl.boot:sentinel-only")
                    logger.info("[Kernel] no ontology .csl — ont:csl sentinel queued directly")

            # ── curations/ (thesaurus enrichments) ────────────────────────────
            # Loaded automatically AFTER ontology .csl sentinel is set.
            # curations/ lives at project root alongside ontology/ — these are
            # example enrichments that ship with the system so a fresh install
            # already has curated content to explore.
            _CUR_SENT_TEXT  = "[ont:curation] Curation scripts loaded"
            _CUR_SENT_KEY   = _hl.sha256(_CUR_SENT_TEXT.encode()).hexdigest()

            cur_dir = os.path.join(_project_dir, "curations")
            _cur_files_probe: List[str] = []
            if os.path.exists(cur_dir):
                for _rd, _, _ns in os.walk(cur_dir):
                    for _n in sorted(_ns):
                        if _n.endswith(".csl"):
                            _cur_files_probe.append(os.path.join(_rd, _n))
            _cur_mhash = _manifest_hash(_cur_files_probe) if _cur_files_probe else "empty"
            _CUR_SENT_ALIAS = f"ont:curation:loaded:{_cur_mhash}"

            cur_loaded = admin_session.local_cortex.get_aliases_by_pattern(_CUR_SENT_ALIAS)
            if not cur_loaded:
                cur_files = _cur_files_probe

                if cur_files:
                    # Wait for .csl ontology sentinel before loading curations
                    logger.info("[Kernel] Waiting for ont:csl:loaded before curations…")
                    _wait_start = _time.time()
                    _max_wait = 3600  # 1 hour ceiling for curation load gate
                    while _time.time() - _wait_start < _max_wait:
                        _time.sleep(5)
                        if lifecycle.is_shutting_down(): return
                        csl_done = admin_session.local_cortex.get_aliases_by_pattern(_SENT_ALIAS)
                        if csl_done:
                            break
                    else:
                        logger.warning("[Kernel] CSL sentinel timeout — skipping curation load")
                        return

                    logger.info("[Kernel] Queuing %d curation scripts…", len(cur_files))
                    for idx, fpath in enumerate(cur_files):
                        try:
                            with open(fpath, "r", encoding="utf-8") as _f:
                                source = _f.read()
                            steps_raw = [{"method": "csl.run", "params": {"script": source}}]
                            if idx == len(cur_files) - 1:
                                steps_raw.append({
                                    "method": "write",
                                    "params": {"text": _CUR_SENT_TEXT, "scope": "universal"},
                                })
                                steps_raw.append({
                                    "method": "alias",
                                    "params": {"id": _CUR_SENT_KEY, "name": _CUR_SENT_ALIAS},
                                })
                            _submit_file_job(fpath, steps_raw,
                                             f"ont.curation:{os.path.basename(fpath)}")
                        except Exception as exc:
                            logger.warning("[Kernel] boot-load curation: %s: %s",
                                           os.path.basename(fpath), exc)
                    logger.info("[Kernel] Curation load queued (%d files)", len(cur_files))

            logger.info("[Kernel] Ontology boot load complete")
            self._schedule_semantic_learn()
            self._schedule_node_learn()

        except Exception as exc:
            logger.warning("[Kernel] Ontology boot load failed (non-fatal): %s", exc, exc_info=True)

    def _schedule_semantic_learn(self) -> None:
        """After the ontology is loaded, learn the distributional embedding model in the
        background so semantic.search / dream are smart from (shortly after) startup —
        with no external model. Non-blocking (a daemon thread), numpy-gated. Set
        AKASHA_NO_AUTOLEARN=1 to disable. Gates on the relations-complete sentinel so it
        learns on the WHOLE corpus (not the few atoms present at boot-submit time), and
        self-heals a previously-persisted stunted model by re-learning when the corpus has
        grown far beyond what that model was trained on. This is the 'startup makes Akasha
        an order smarter' hook: the graph learns from itself."""
        _skip = _autolearn_disabled_reason()
        if _skip:
            logger.info("[Kernel] Auto semantic.learn skipped — %s", _skip)
            return
        try:
            from lib.akasha.semantic_learn import OntologyLearner, tokens, get_shared_model, store_model
        except Exception:
            return
        if not OntologyLearner.available():          # numpy absent → floor tier, no learn
            return
        nucleus = getattr(self.manager, "shared_nucleus", None)
        if nucleus is None:
            return

        def _run():
            try:
                # Gate on the relations-complete sentinel, exactly like node.learn. The
                # "Ontology boot load complete" log fires when jobs are SUBMITTED, not
                # when the atoms are written (the JCL writes them async), so reading the
                # corpus immediately would learn a stunted model on the few hundred atoms
                # present at that instant and persist it forever. Wait for the whole atom
                # set to exist first.
                from lib.akasha import lifecycle
                import glob as _glob
                sent_dir = os.path.join(self.base_dir, "central", "sentinels")
                deadline = time.time() + 7200
                while time.time() < deadline:
                    if lifecycle.is_shutting_down():
                        return
                    if _glob.glob(os.path.join(sent_dir, "_relations_*.done")):
                        break
                    time.sleep(5)
                if lifecycle.is_shutting_down():
                    return                     # don't start a numpy learn during teardown

                import json as _json
                # BOUND the read. `get_all_chunks()` with no cap preads EVERY atom's value
                # into RAM — on the disk-value store (chosen precisely because the host can't
                # hold the corpus in memory) that is the boot-time OOM that silently kills the
                # daemon during the background learn. The learn + bake already only USE the
                # first `_cap` atoms, so capping the READ is behaviour-preserving and turns an
                # unbounded allocation into a bounded one. Tunable for tight hosts via
                # AKASHA_AUTOLEARN_MAX (lower it, or AKASHA_NO_AUTOLEARN=1 to skip entirely).
                try:
                    _cap = max(0, int(os.environ.get("AKASHA_AUTOLEARN_MAX", "40000")))
                except (TypeError, ValueError):
                    _cap = 40000
                if _cap == 0:
                    return
                chunks = nucleus.core.get_all_chunks(limit=_cap) or []
                # Learn only from CURATED content — external (fetched) atoms carry
                # provenance=external and are excluded so unvetted web text cannot
                # poison the learned model (ASI06).
                docs = []
                for row in chunks:
                    content = row.get("content") or ""
                    if len(content) < 8:
                        continue
                    if _is_external(row.get("meta")):
                        continue
                    docs.append(tokens(content))
                    if len(docs) >= _cap:
                        break

                # Self-heal: keep an existing model only if it was trained on a corpus
                # comparable to what exists now. A model persisted from an early-boot race
                # (tiny n_docs) is discarded and re-learned — so installs already carrying
                # a stunted model heal on the next boot. Legacy models without n_docs fall
                # back to vocab size as the proxy.
                existing = get_shared_model(nucleus)
                if existing is not None:
                    prev = getattr(existing, "n_docs", 0) or 0
                    if prev <= 0:
                        prev = len(getattr(existing, "vocab", {}) or {})
                    if len(docs) < max(500, prev * 3):
                        return                                   # adequate — keep it
                    logger.info("[Kernel] semantic model stunted (trained~%d docs, now %d) "
                                "— relearning", prev, len(docs))

                learner = OntologyLearner(dim=64, max_vocab=2000)
                if not learner.learn(docs):
                    return
                store_model(nucleus, learner)
                logger.info("[Kernel] Auto semantic.learn complete (docs=%d, vocab=%d)",
                            len(docs), len(learner.vocab))

                # Per-atom bake-in: write the learned vector onto each atom's meta so the
                # cosine paths (dream, stored-vector reads) use the learned tier without
                # re-embedding. Bounded; nucleus writes are commit-forward (no guard).
                baked = 0
                for row in chunks:
                    content = row.get("content") or ""
                    if len(content) < 8 or _is_external(row.get("meta")):
                        continue
                    vec = learner.embed_text(content)
                    if not vec:
                        continue
                    try:
                        m = _json.loads(row.get("meta") or "{}")
                    except Exception:
                        m = {}
                    m["semantic_vector"] = vec
                    # Preserve created_at (the chunks column is 'created_at', not 'ts')
                    # so re-writing meta does not reset the atom's timestamp.
                    nucleus.core.put_chunk_raw(
                        row["key"], content, _json.dumps(m, ensure_ascii=False),
                        row.get("author", "system"), row.get("status", "verified"),
                        row.get("created_at") or time.time())
                    baked += 1
                    if baked >= _cap:
                        break
                if baked:
                    logger.info("[Kernel] Learned vectors baked into %d atoms", baked)
            except Exception as exc:                          # never break boot
                logger.warning("[Kernel] Auto semantic.learn failed (non-fatal): %s", exc)

        import threading
        threading.Thread(target=_run, name="semantic-autolearn", daemon=True).start()

    def _schedule_node_learn(self) -> None:
        """Structural sibling of _schedule_semantic_learn: after the ontology loads,
        learn the STRUCTURAL node embeddings (NodeWalkLearner: random walks over the
        typed-link graph → PPMI+SVD) in the background so `node.sim` works from
        startup with no operator step. Non-blocking daemon thread, numpy-gated, and
        skipped if a model already persists (idempotent across restarts). Set
        AKASHA_NO_AUTOLEARN=1 to disable. Unlike the content model it needs the LINK
        graph — the deferred GLOBAL relations phase — so it waits for that phase's
        completion sentinel (`_relations`) before learning, never a fixed timeout, so
        a slow host does not learn on a half-built graph."""
        _skip = _autolearn_disabled_reason()
        if _skip:
            logger.info("[Kernel] Auto node.learn skipped — %s", _skip)
            return
        try:
            from lib.akasha.semantic_learn import (NodeWalkLearner, get_node_model,
                                                   store_node_model)
        except Exception:
            return
        if not NodeWalkLearner.available():          # numpy absent → no structural model
            return
        nucleus = getattr(self.manager, "shared_nucleus", None)
        if nucleus is None:
            return

        def _run():
            try:
                if get_node_model(nucleus) is not None:      # already learned/persisted
                    return
                # The structural model needs the LINK graph, produced by the deferred
                # GLOBAL relations phase (all al/ln/set.add run as one job AFTER every
                # pack's atoms). A fixed wait / link-count heuristic is wrong on a slow
                # host: the relations job can still be running (links trickling in), so
                # we would learn on a half-built graph and most atoms would be absent
                # from the model. Gate on the authoritative completion signal instead —
                # the `_relations` filesystem sentinel that _boot_load_ontology writes
                # when the relations phase finishes. Only then is the graph whole.
                from lib.akasha import lifecycle
                import glob as _glob
                sent_dir = os.path.join(self.base_dir, "central", "sentinels")
                gated = False
                deadline = time.time() + 7200               # generous ceiling (slow hosts)
                while time.time() < deadline:
                    if lifecycle.is_shutting_down():
                        return
                    if _glob.glob(os.path.join(sent_dir, "_relations_*.done")):
                        gated = True
                        break
                    time.sleep(5)
                if lifecycle.is_shutting_down():
                    return                     # don't start a numpy learn during teardown
                if not gated:
                    logger.info("[Kernel] Auto node.learn: relations-complete sentinel not "
                                "seen within ceiling — learning best-effort on current links")
                # Bound the link read (env-tunable), same rationale as the content learn:
                # never materialize an unbounded link set into RAM at boot on a tight host.
                try:
                    _lcap = max(0, int(os.environ.get("AKASHA_AUTOLEARN_LINK_MAX", "200000")))
                except (TypeError, ValueError):
                    _lcap = 200000
                if _lcap == 0:
                    return
                try:
                    links = nucleus.core.get_all_links(limit=_lcap) or []
                except Exception:
                    links = []
                if len(links) < 50:
                    logger.info("[Kernel] Auto node.learn skipped (graph too sparse: "
                                "links=%d)", len(links))
                    return
                nwl = NodeWalkLearner(dim=32, walks_per_node=10, length=8, seed=7)
                if not nwl.learn(links):
                    return
                store_node_model(nucleus, nwl)
                logger.info("[Kernel] Auto node.learn complete (links=%d, nodes=%d)",
                            len(links), len(nwl.vocab))
            except Exception as exc:                          # never break boot
                logger.warning("[Kernel] Auto node.learn failed (non-fatal): %s", exc)

        import threading
        threading.Thread(target=_run, name="node-autolearn", daemon=True).start()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def dispatch(self, payload: dict, transport_trust: str = TRUST_NETWORK) -> dict:
        """
        Unified JSON-RPC 2.0 entry point.
        Every shell portal calls this and only this.

        transport_trust is supplied by the calling portal (never by the client)
        and defaults to the safe TRUST_NETWORK.  See the trust-level constants.
        """
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0" or "method" not in payload:
            return _err(payload.get("id") if isinstance(payload, dict) else None,
                        -32600, "Invalid Request: not valid JSON-RPC 2.0")

        rid = payload.get("id", str(uuid.uuid4()))
        method: str = payload["method"]
        params: dict = payload.get("params", {})

        try:
            return self._authenticated_dispatch(method, params, rid, transport_trust)
        except PermissionError as e:
            return _err(rid, -32001, f"Permission Denied: {e}")
        except Exception as e:
            logger.error(f"[Kernel] Unhandled error in dispatch: {e}", exc_info=True)
            return _err(rid, -32000, f"Internal Kernel Error: {e}")

    # ------------------------------------------------------------------
    # Auth + session resolution
    # ------------------------------------------------------------------

    def _authenticated_dispatch(self, method: str, params: dict, rid: str,
                                transport_trust: str = TRUST_NETWORK) -> dict:
        # Raw token as supplied by the transport layer (HTTP header or RPC param).
        # Akasha does not trust the transport; this value is opaque until resolved.
        raw_token: str = params.get("session_token") or params.get("client_id") or "anonymous"
        trusted = transport_trust in _TRUSTED_TRANSPORTS
        data: dict = params.get("data", {})
        # Merge any top-level non-auth params into data so concept registry
        # handlers receive them regardless of nesting style used by the caller.
        # Nested data keys take priority over same-named top-level keys.
        _top = {k: v for k, v in params.items()
                if k not in ("session_token", "client_id", "data")}
        if _top:
            data = {**_top, **data}

        # Methods that run before a session exists
        if method == "sys.ping":
            return self._handle_ping(rid, raw_token)
        if method == "sys.status":
            return self._handle_status(rid)
        if method == "kernel.genesis_rite":
            # Genesis seizes (or creates) the admin account.  Restrict it to the
            # local console / internal boot so a network client cannot land-grab
            # admin on a Cell that is exposed before its first-boot ceremony.
            if not trusted:
                return _err(rid, -32001,
                            "genesis_rite must be performed from the local console.")
            return self._handle_genesis_rite(rid, data)
        if method in ("kernel.auth.status", "auth.status"):
            return self._handle_auth_status(rid)
        if method in ("kernel.auth.verify", "auth.verify"):
            return self._handle_auth_verify(rid, data)
        # Self-service registration — pre-auth (the registrant has no token yet),
        # bounded + config-gated (see _handle_auth_register). Open to any client only
        # when the operator enables it.
        if method in ("kernel.auth.register", "auth.register"):
            return self._handle_auth_register(rid, data)

        # Guest session management — operate on the binding directly, no Akasha
        # auth needed.  session.guest.create issues a new binding; extend renews
        # an existing one.  Both are intentionally open to any HTTP client.
        if method == "session.guest.create":
            return self._handle_guest_create(rid, data)
        if method == "session.guest.extend":
            return self._handle_guest_extend(rid, raw_token, data)

        # ── Identity resolution ──────────────────────────────────────────────
        # The identity is resolved from the token, never asserted by a bare
        # client_id over an untrusted transport.  Four cases:
        if self.iam.guest_bindings.is_guest_key(raw_token):
            # gbk: signed guest binding → an Akasha-internal "guest:" session id.
            try:
                client_id = self.iam.guest_bindings.resolve(raw_token)
                role      = self.iam.authenticate(client_id)
            except PermissionError as e:
                return _err(rid, -32001, str(e))
            # Renew the pool slot timer so the sweeper doesn't reclaim an active
            # visitor's session mid-use.
            self.manager.touch_guest_session(client_id)
        elif self.iam.guest_bindings.is_auth_key(raw_token):
            # akt: signed session token — proof of identity on ANY transport.
            try:
                client_id, role = self.iam.resolve_session_token(raw_token)
            except PermissionError as e:
                return _err(rid, -32001, str(e))
        elif trusted:
            # Trusted transport (local console / internal): a bare client_id may
            # assert an identity — the OS/process boundary is the real gate.
            client_id = raw_token
            if self.iam.is_system_identity(client_id) and transport_trust != TRUST_INTERNAL:
                return _err(rid, -32001, "System identities are internal-only.")
            try:
                role = self.iam.authenticate(client_id)
            except PermissionError as e:
                return _err(rid, -32001, str(e))
        else:
            # Untrusted network transport with a bare (unsigned) identity claim.
            # Resolve it, but accept ONLY an anonymous GUEST.  A known privileged
            # identity MUST present a signed akt: token (obtained via auth.verify)
            # — this closes the "the username is the credential" bypass.
            try:
                role = self.iam.authenticate(raw_token)
            except PermissionError as e:
                return _err(rid, -32001, str(e))
            if role != Role.GUEST:
                return _err(rid, -32001,
                            "This identity requires a signed session token over the "
                            "network. Call auth.verify to obtain one.")
            client_id = raw_token

        # Map full RPC method names to the capability action tokens IAM understands.
        # A method with no capability mapping (and not one of the capability-free built-ins
        # authorize() accepts directly) has no handler here — it is genuinely
        # unimplemented, so return -32601 (Method not found), NOT -32001 (permission), so a
        # client can tell "not built yet" apart from "not allowed". Pre-auth methods
        # (auth.*, session.guest.*, sys.ping/status) were already handled above.
        action = _METHOD_TO_ACTION.get(method)
        if action is None:
            if method not in ("echo", "help", "status", "ping"):
                return _err(rid, -32601, f"Method not found: {method}")
            action = method
        try:
            # Effective policy = base role ⊕ attached grants (capability-delegation-iam-spec).
            # Additive: with no grants this is exactly self.iam.authorize(role, action, data).
            authorized = self.iam.authorize_effective(client_id, role, action, data)
        except PermissionError as quota_err:
            return _err(rid, -32001, str(quota_err))

        if not authorized:
            return _err(rid, -32001, f"Capability denied for '{method}' with role '{role.value}'")

        session = self.manager.get_session(client_id)
        ctx = session.local_cortex
        # Build user-authored history for $0/$N context references.
        # Skip the DB fetch for internal bulk-write calls (JCL/CSL batch) where
        # history context is never needed — avoids 25k+ SELECT queries per boot load.
        if data.get("_skip_history"):
            history: list = []
        else:
            _raw = ctx.stream(50)
            history = [item for item in _raw
                       if item.get("author") == client_id and not _is_sys_atom(item)][:20]

        # Per-token su slot: elevation (su root/librarian/impersonate) is bound to
        # THIS token, not shared across every connection that presents the same
        # client_id — prevents su state bleeding between concurrent sessions.
        su_key = "su_target:" + hashlib.sha256(raw_token.encode()).hexdigest()[:16]

        # ── Single-route write turn ───────────────────────────────────────────
        # A synchronous graph-writing method runs inside ONE Harmonia workspace so
        # its atom/link bundle (proto-word + w + set + alias — the ~4-6-write critical
        # bundle) is atomic and reversible: commit on success, rollback on any error.
        # This is the seam the hard guard enforces — a composite write with no
        # workspace is rejected once ENFORCE is on. Skipped when a workspace is
        # already active on this thread: a JCL step re-enters dispatch under its
        # job's workspace and must not nest (nor steal) a second tracked context.
        if (action in _WRITE_ACTIONS and self.harmonia
                and not _workspace_active()[0] and not _in_workspace()):
            return self._write_turn(method, data, session, ctx, history, rid, su_key)
        return self._route(method, data, session, ctx, history, rid, su_key)

    def _write_turn(self, method, data, session, ctx, history, rid, su_key) -> dict:
        """Run a write-action dispatch inside one atomic, reversible workspace.

        Opened on the session's local cortex (the engine that records the tracking
        set). Universal/nucleus writes route to a different engine, so they are
        presence-guarded but not per-atom tracked — acceptable: those are idempotent
        content-addressed system writes, not the user's reversible conversation
        bundle. evidence=False keeps the per-turn workspace off the critical path."""
        # HIGH priority (0): a user turn is the perceived-immediate critical path;
        # its writes are ordered ahead of background batch/link work at the WriteQueue.
        tx_id = self.harmonia.begin_workspace(
            session.local_cortex, f"turn:{method}", tracked=True, evidence=False,
            priority=0)
        try:
            resp = self._route(method, data, session, ctx, history, rid, su_key)
        except Exception:
            self.harmonia.rollback_workspace(session.local_cortex, tx_id)
            raise
        if isinstance(resp, dict) and "error" in resp:
            # Failed op → all-or-nothing: drop anything the handler already wrote.
            self.harmonia.rollback_workspace(session.local_cortex, tx_id)
        else:
            self.harmonia.commit_workspace(session.local_cortex, tx_id)
        return resp

    # ------------------------------------------------------------------
    # Routing table
    # ------------------------------------------------------------------

    def _route(self, method: str, data: dict, session, ctx, history: list, rid: str,
               su_key: str = "su_target") -> dict:
        client_id = session.client_id
        scopes = session.active_scopes

        # ── Session context (available to all roles incl. GUEST) ─────
        if method == "session.context.set":
            return self._handle_session_ctx_set(rid, data, session)
        if method == "session.context.get":
            return self._handle_session_ctx_get(rid, data, session)

        # ── su: must run under real identity, not the overridden one ──
        if method == "sys.su":
            return self._handle_su(rid, data, session, client_id, su_key)

        # Apply su state — override client_id / scopes for all other commands.
        # su_key is per-token so elevation does not leak across connections.
        su_target = session.get_context(su_key)
        if su_target == "root":
            scopes = list(scopes) + ["scope:sys:root"]
        elif su_target == "librarian":
            scopes = list(scopes) + ["role:librarian", "scope:sys:collective"]
        elif su_target:
            try:
                target_role = self.iam.authenticate(su_target)
                scopes = self.iam.get_allowed_scopes(su_target, target_role)
            except Exception:
                pass
            client_id = su_target

        # Resolve write context once based on scope and role.
        # When scope=universal and the caller has librarian rights, all put_*
        # operations in this dispatch call route transparently to nucleus.
        nucleus = getattr(session, 'nucleus', None)
        if (data.get("scope") == "universal"
                and "role:librarian" in scopes
                and nucleus is not None):
            ctx = _NucleusWriteCtx(session.local_cortex, nucleus)

        # ── Status ────────────────────────────────────────────────────
        if method == "sys.status.full":
            return self._handle_status_full(rid, session)

        # ── Ref-slot management ───────────────────────────────────────
        if method == "ref.set":
            return self._handle_ref_set(rid, data, session)
        if method == "ref.get":
            return self._handle_ref_get(rid, data, session)

        # ── Memory ────────────────────────────────────────────────────
        if method in ("kernel.memory.write", "write", "w"):
            return self._handle_write(rid, data, session, ctx, scopes, client_id)

        if method in ("kernel.memory.define", "define", "def"):
            return self._handle_define(rid, data, session, ctx, scopes, client_id)

        if method in ("kernel.memory.read", "read", "r"):
            return self._handle_read(rid, data, session, ctx, scopes, history)

        if method in ("kernel.memory.drop", "drop", "rm"):
            return self._handle_drop(rid, data, session, ctx, scopes)

        if method in ("kernel.memory.link", "link.create", "ln"):
            return self._handle_link(rid, data, session, ctx, client_id)

        if method in ("link.list",):
            return self._handle_link_list(rid, data, ctx, scopes)

        if method in ("link.reinforce",):
            return self._handle_link_reinforce(rid, data, ctx, client_id)

        if method in ("link.rm", "ln.rm"):
            return self._handle_link_rm(rid, data, session, ctx)

        if method in ("meta.set",):
            return self._handle_meta_set(rid, data, ctx)

        # ── Aliases ───────────────────────────────────────────────────
        if method in ("kernel.identity.alias", "alias", "al"):
            return self._handle_alias(rid, data, session, ctx, history)

        if method in ("alias.rm", "al.rm"):
            return self._handle_alias_rm(rid, data, session, ctx)

        if method in ("kernel.identity.alias.list", "alias.list", "al.ls"):
            return _ok(rid, {"aliases": ctx.get_all_aliases()})

        if method in ("kernel.identity.alias.find", "alias.find", "al.find"):
            pattern = data.get("pattern") or data.get("name", "%")
            aliases = ctx.get_aliases_by_pattern(pattern)
            # Group-space aliases: a member also sees aliases of atoms shared into
            # their groups (scope-gated); other members' private aliases are not in
            # the group space, so they never surface here.
            _seen_a = {(a.get("key"), a.get("alias")) for a in aliases}
            for _gid, _ge in self._member_group_engines(session, scopes):
                for a in (_ge.core.get_aliases_by_pattern(pattern) or []):
                    _ka = (a.get("key"), a.get("alias"))
                    if _ka not in _seen_a:
                        _seen_a.add(_ka)
                        aliases.append(a)
            focus   = self._get_display_focus(session)
            nucleus = getattr(session, 'nucleus', None)
            if focus:
                ns_prefixes = focus.get("ns_prefixes", [])
                scope_list  = focus.get("scopes", [])
                def _alias_passes(entry: dict) -> bool:
                    alias_str = entry.get("alias", "")
                    key       = entry.get("key", "")
                    if ns_prefixes and not any(alias_str.startswith(p) for p in ns_prefixes):
                        return False
                    if scope_list and not self._passes_display_focus(key, {"scopes": scope_list, "ns_prefixes": []}, ctx, nucleus):
                        return False
                    return True
                aliases = [a for a in aliases if _alias_passes(a)]
            return _ok(rid, {"aliases": aliases})

        # ── Ontology ─────────────────────────────────────────────────
        if method == "onto.dump":
            return self._handle_onto_dump(rid, data, ctx)
        if method == "onto.export":
            return self._handle_onto_export(rid, data, ctx)
        if method == "onto.reload":
            return self._handle_onto_reload(rid, data, session, scopes)
        if method == "onto.reconcile":
            return self._handle_onto_reconcile(rid, data, session, scopes)
        if method == "onto.reset":
            return self._handle_onto_reset(rid, data, session, scopes)
        if method == "onto.pack.list":
            return self._handle_onto_pack_list(rid, data, session, scopes)
        if method == "onto.pack.enable":
            return self._handle_onto_pack_enable(rid, data, session, scopes)
        if method == "onto.pack.disable":
            return self._handle_onto_pack_disable(rid, data, session, scopes)
        if method == "onto.report":
            return self._handle_onto_report(rid, data, ctx)
        if method == "onto.status":
            return self._handle_onto_status(rid, data, session, scopes)

        # ── Service lifecycle (Supervisor RPC — P3: the daemon is the sole respawner) ──
        # A client's `svc start/restart` is a REQUEST delivered here; the kernel (running in
        # the Cell daemon that hosts the Supervisor) performs the spawn from the persisted
        # recipe. `svc ls`/`svc stop` also work directly on the run-dir client-side, but the
        # RPC path lets any front operate the plane uniformly and is where a delegation grant
        # check will slot in (service-extension-and-delegation-spec §3.2).
        if method in ("svc.ls", "svc.start", "svc.stop", "svc.restart"):
            return self._handle_svc_rpc(rid, method, data, session)

        # ── Capability delegation (grants compose on top of the base role) ──
        if method in ("iam.grant", "iam.revoke", "iam.grants"):
            return self._handle_iam_grant(rid, method, data, session)
        if method == "onto.genesis.redo":
            return self._handle_onto_genesis_redo(rid, data, session, scopes)
        if method == "onto.scope.drop":
            return self._handle_onto_scope_drop(rid, data, session, scopes)

        # ── Weaver ────────────────────────────────────────────────────
        if method == "sys.weaver.weave":
            return self._handle_weave(rid, data, session)
        if method == "sys.weaver.weave_batch":
            return self._handle_weave_batch(rid, data, session)
        if method == "sys.weaver.weave_client":
            return self._handle_weave_client(rid, data, session)
        if method == "sys.weaver.decompose":
            return self._handle_weave_decompose(rid, data, session)
        if method == "sys.weaver.drain_pending":
            return self._handle_weave_drain_pending(rid, data, session)

        # ── Exploration ───────────────────────────────────────────────
        if method in ("explore", "network.tree"):
            return self._handle_explore(rid, data, session, ctx, scopes, history)

        if method == "graph.tree":
            return self._handle_graph_tree(rid, data, session, ctx, scopes)

        if method in ("semantic.search", "search", "sim", "similar"):
            return self._handle_semantic_search(rid, data, session, ctx, scopes)

        if method == "semantic.learn":
            return self._handle_semantic_learn(rid, data, session, ctx, scopes)

        if method in ("gap.scan", "gaps"):
            return self._handle_gap_scan(rid, data, session, ctx, scopes)

        if method in ("gap.fetch", "gap.enrich"):
            return self._handle_gap_fetch(rid, data, session, ctx, scopes, client_id)

        if method == "node.learn":
            return self._handle_node_learn(rid, data, session, ctx, scopes)
        if method in ("node.sim", "node.similar"):
            return self._handle_node_sim(rid, data, session, ctx, scopes)

        # ── Dive / View ────────────────────────────────────────────────
        if method in ("dive.look", "look"):
            return self._handle_dive_look(rid, data, session, scopes)

        if method in ("dive.out", "out"):
            return self._handle_dive_out(rid, data, session, scopes)

        if method in ("view", "cosmos"):
            return self._handle_view(rid, data, session, scopes)

        # ── Sets ──────────────────────────────────────────────────────
        if method in ("set.add",):
            return self._handle_set_add(rid, data, session, ctx)

        if method in ("set.rm",):
            return self._handle_set_rm(rid, data, ctx)

        if method in ("set.ls",):
            return self._handle_set_ls(rid, data, ctx, scopes, session)

        if method in ("set.clear",):
            return self._handle_set_clear(rid, data, ctx)

        if method in ("set.op",):
            return self._handle_set_op(rid, data, ctx)

        # Notes (note.* / loom.note.*) now dispatch through the ONE concept registry
        # (NoteConcept + CONCEPT_NAMESPACES) below — the hand-wired handler block was
        # retired in #50 Stage 2.

        # ── JCL ───────────────────────────────────────────────────────
        if method == "job.submit": return self._handle_job_submit(rid, data, session)
        if method == "job.ls":     return self._handle_job_ls(rid, data, session)
        if method == "job.stat":   return self._handle_job_stat(rid, data, session)
        if method == "job.cancel": return self._handle_job_cancel(rid, data, session)

        # ── Workflow (stored CSL script → orchestrated JCL job) ────────
        if method == "workflow.def": return self._handle_workflow_def(rid, data, session, ctx)
        if method == "workflow.run": return self._handle_workflow_run(rid, data, session, ctx)
        if method == "workflow.ls":  return self._handle_workflow_ls(rid, data, session, ctx)
        if method == "workflow.get": return self._handle_workflow_get(rid, data, session, ctx)
        if method == "workflow.rm":  return self._handle_workflow_rm(rid, data, session, ctx)

        # ── Locale ────────────────────────────────────────────────────
        if method == "locale.get": return self._handle_locale_get(rid, session)
        if method == "locale.set": return self._handle_locale_set(rid, data, session)

        # ── CSL ─────────────────────────────────────────────────────
        if method in ("csl", "csl.check", "csl.build", "csl.run"):
            return self._handle_csl(rid, method, data, session)

        # ── Concept Models (registry-dispatched) ──────────────────────
        if _concept_registry:
            _reg_result = _concept_registry.dispatch_if_handled(method, session, data, rid)
            if _reg_result is not None:
                # Propagate the created atom key so $it/$0 resolve correctly
                _reg_payload = _reg_result.get("result", {})
                if isinstance(_reg_payload, dict) and "key" in _reg_payload:
                    session.last_written_id = _reg_payload["key"]
                return _reg_result

        # FieldNote (fieldnote.*) and Survey (survey.*) now dispatch through the ONE concept
        # registry above (FieldNoteConcept / SurveyConcept); their hand-wired handler blocks
        # were retired in #50 Stage 2 (they were already dead — the registry ran first).

        # ── Associate ─────────────────────────────────────────────────
        if method == "kernel.associate":
            return self._handle_associate(rid, data, session, ctx, scopes, history)

        if method == "associate.unwritten":
            return self._handle_associate_unwritten(rid, data, session, ctx, scopes)

        if method in ("emotion.profile", "emo.vector", "emo.profile"):
            return self._handle_emotion_profile(rid, data, session, ctx, scopes)

        if method in ("emotion.find", "emo.find"):
            return self._handle_emotion_find(rid, data, session, ctx, scopes)

        # ── Log ───────────────────────────────────────────────────────
        if LogConcept:
            if method == "log.new":        return self._handle_log_new(rid, data, session)
            if method == "log.ls":         return self._handle_log_ls(rid, session)
            if method == "log.checkpoint": return self._handle_log_checkpoint(rid, data, session)
            if method == "log.annotate":   return self._handle_log_annotate(rid, data, session)
            if method == "log.replay":     return self._handle_log_replay(rid, session)
            if method == "log.read":       return self._handle_log_read(rid, session)
            if method == "log.rm":         return self._handle_log_rm(rid, session)

        # ── Whiteboard ────────────────────────────────────────────────
        if WhiteboardConcept:
            if method == "wb.new":    return self._handle_wb_new(rid, data, session)
            if method == "wb.pin":    return self._handle_wb_pin(rid, data, session)
            if method == "wb.unpin":  return self._handle_wb_unpin(rid, data, session)
            if method == "wb.focus":  return self._handle_wb_focus(rid, data, session)
            if method == "wb.ls":     return self._handle_wb_ls(rid, session)
            if method == "wb.show":   return self._handle_wb_show(rid, session)
            if method == "wb.rm":     return self._handle_wb_rm(rid, data, session)

        # ── Cross ─────────────────────────────────────────────────────
        if method == "sys.cross.query": return self._handle_cross_query(rid, data, session, ctx, scopes)
        if method == "sys.cross.axes":  return self._handle_cross_axes(rid, data, session, ctx, scopes)
        if method == "sys.cross.atom":  return self._handle_cross_atom(rid, data, session, ctx, scopes)

        # ── Associate ─────────────────────────────────────────────────
        if method == "kernel.associate":
            return self._handle_associate(rid, data, session, ctx, scopes, history)

        if method == "associate.unwritten":
            return self._handle_associate_unwritten(rid, data, session, ctx, scopes)

        # ── Log ───────────────────────────────────────────────────────
        if LogConcept:
            if method == "log.new":        return self._handle_log_new(rid, data, session)
            if method == "log.ls":         return self._handle_log_ls(rid, session)
            if method == "log.checkpoint": return self._handle_log_checkpoint(rid, data, session)
            if method == "log.annotate":   return self._handle_log_annotate(rid, data, session)
            if method == "log.replay":     return self._handle_log_replay(rid, session)
            if method == "log.read":       return self._handle_log_read(rid, session)
            if method == "log.rm":         return self._handle_log_rm(rid, session)

        # ── Whiteboard ────────────────────────────────────────────────
        if WhiteboardConcept:
            if method == "wb.new":    return self._handle_wb_new(rid, data, session)
            if method == "wb.pin":    return self._handle_wb_pin(rid, data, session)
            if method == "wb.unpin":  return self._handle_wb_unpin(rid, data, session)
            if method == "wb.focus":  return self._handle_wb_focus(rid, data, session)
            if method == "wb.ls":     return self._handle_wb_ls(rid, session)
            if method == "wb.show":   return self._handle_wb_show(rid, session)
            if method == "wb.rm":     return self._handle_wb_rm(rid, data, session)

        # ── Cross ─────────────────────────────────────────────────────
        if method == "sys.cross.query": return self._handle_cross_query(rid, data, session, ctx, scopes)
        if method == "sys.cross.axes":  return self._handle_cross_axes(rid, data, session, ctx, scopes)
        if method == "sys.cross.atom":  return self._handle_cross_atom(rid, data, session, ctx, scopes)

        # ── Jataka — dream (async incubation) ─────────────────────────
        if method in ("jataka.dream", "dream"):
            return self._handle_dream(rid, data, session, ctx, scopes, history)
        if method == "dream.run":                       # internal background step
            return self._handle_dream_run(rid, data, session, ctx, scopes)
        if method in ("dream.confirm", "dream.approve"):
            return self._handle_dream_confirm(rid, data, session, ctx, scopes, history)
        if method in ("dream.forget", "dream.reject"):
            return self._handle_dream_forget(rid, data, session, ctx, scopes, history)
        if method == "nebula":
            return self._handle_nebula(rid, data, session, ctx, scopes, history)
        if method == "nebula.run":                      # internal background step
            return self._handle_nebula_run(rid, data, session, ctx, scopes)
        if method in ("nebula.confirm", "nebula.approve"):
            return self._handle_nebula_confirm(rid, data, session, ctx, scopes, history)
        if method in ("nebula.forget", "nebula.reject"):
            return self._handle_nebula_forget(rid, data, session, ctx, scopes, history)

        # ── Contexa — the client session's INPUT side ─────────────────
        if method in ("contexa.fetch", "fetch"):
            return self._handle_contexa_fetch(rid, data, session, ctx, scopes, client_id)
        if method in ("contexa.ingest", "survey.ingest"):
            return self._handle_contexa_ingest(rid, data, session, ctx, scopes, client_id)

        # ── Jataka — the client session's OUTPUT side ─────────────────
        if method in ("jataka.present", "present"):
            return self._handle_jataka_present(rid, data, session, ctx, scopes, client_id)
        if method in ("curation.project", "cur.project"):
            return self._handle_curation_project(rid, data, session, ctx, scopes, client_id)
        if method in ("pres.export", "presentation.export"):
            return self._handle_pres_export(rid, data, session, ctx, scopes, client_id)

        if method in ("image.profile", "img.profile", "vision.classify"):
            return self._handle_image_profile(rid, data, session, ctx, scopes, client_id)

        # ── File import/export (general disk I/O — single route) ───────
        if method in ("io.import", "file.import"):
            return self._handle_io_import(rid, data, session, ctx, scopes, client_id)
        if method in ("io.export", "file.export"):
            return self._handle_io_export(rid, data, session, ctx, scopes, client_id)
        if method in ("io.index", "dir.index"):
            return self._handle_io_index(rid, data, session, ctx, scopes, client_id)
        if method in ("io.project", "io.cast"):
            return self._handle_io_project(rid, data, session, ctx, scopes, client_id)
        if method in ("io.allow", "io.permit"):
            return self._handle_io_allow(rid, data, session)

        if method == "web.search":
            return self._handle_web_search(rid, data, session, ctx, scopes, client_id)

        # ── Display Focus ─────────────────────────────────────────────
        if method == "session.focus":
            return self._handle_focus(rid, data, session, client_id)

        # ── Scope ─────────────────────────────────────────────────────
        if method == "sys.scope.set":
            return self._handle_scope_set(rid, data, session)
        if method == "sys.scope.get":
            return self._handle_scope_get(rid, session)
        if method == "sys.scope.reset":
            return self._handle_scope_reset(rid, session)

        # ── Onboarding ────────────────────────────────────────────────
        if method == "sys.onboarding.seed":
            return self._handle_onboarding_seed(rid, data, session)

        # ── Sys ───────────────────────────────────────────────────────
        if method in ("sys.cogito", "cogito"):
            return _ok(rid, session.consciousness.cogito(session))

        if method in ("sys.history",):
            return _ok(rid, {"history": history})

        if method in ("sys.ls",):
            return self._handle_sys_ls(rid, data, ctx, scopes, client_id)

        if method in ("sys.session.close",):
            self.manager.close_session(client_id)
            return _ok(rid, {"status": "session_closed", "client_id": client_id})

        # ── Self-service passphrase change (all authenticated users) ──
        if method in ("sys.passwd", "passwd"):
            return self._handle_passwd_self(rid, data, session)

        # ── User management (admin only, hidden) ─────────────────────
        if method in ("user.ls",):
            return self._handle_user_ls(rid, session)
        if method in ("user.add",):
            return self._handle_user_add(rid, data, session)
        # Entitlement plan (general): read own tier; admin sets a user's tier (billing hook)
        if method in ("auth.plan", "kernel.auth.plan"):
            return self._handle_auth_plan(rid, session)
        if method in ("auth.plan.set", "kernel.auth.plan.set"):
            return self._handle_auth_plan_set(rid, data, session)
        # Self-service account deletion (App Store / Play Store requirement). Deletes the
        # CALLER's own account only — identity, private cell (recipes/personal foods/
        # measurements), and entitlement — never another user's.
        if method in ("auth.account.delete", "kernel.auth.account.delete"):
            return self._handle_account_delete(rid, data, session, session.role)
        if method in ("user.rm",):
            return self._handle_user_rm(rid, data, session)
        if method in ("user.mod",):
            return self._handle_user_mod(rid, data, session)
        if method in ("user.id",):
            return self._handle_user_id(rid, data, session)
        if method in ("user.passwd",):
            return self._handle_user_passwd(rid, data, session)

        # ── Group management (admin / group_admin) ────────────────────
        if method in ("grp.ls",):
            return self._handle_grp_ls(rid, data, session)
        if method in ("grp.new",):
            return self._handle_grp_new(rid, data, session)
        if method in ("grp.add",):
            return self._handle_grp_add(rid, data, session)
        if method in ("grp.rm",):
            return self._handle_grp_rm(rid, data, session)
        if method in ("grp.lib",):
            return self._handle_grp_lib(rid, data, session)
        if method in ("grp.del",):
            return self._handle_grp_del(rid, data, session)

        # ── Donation / Delegation Sets ────────────────────────────────
        if method == "dont.create":
            return self._handle_dont_create(rid, data, session)
        if method == "dont.add":
            return self._handle_dont_add(rid, data, session)
        if method == "dont.send":
            return self._handle_dont_send(rid, data, session)
        if method == "dont.ls":
            return self._handle_dont_ls(rid, data, session)
        if method == "dont.open":
            return self._handle_dont_open(rid, data, session)

        # ── Unknown ───────────────────────────────────────────────────
        return _err(rid, -32601, f"Method not found: '{method}'")

    # ------------------------------------------------------------------
    # su — privileged identity switch (admin only)
    # ------------------------------------------------------------------

    def _handle_su(self, rid: str, data: dict, session, real_client_id: str,
                   su_key: str = "su_target") -> dict:
        # Verify the caller holds admin role
        try:
            role = self.iam.authenticate(real_client_id)
        except PermissionError:
            return _err(rid, -32003, "Permission denied: su requires admin role")
        if role.value not in ("admin",):
            return _err(rid, -32003, "Permission denied: su requires admin role")

        target = data.get("target", "").strip()
        passphrase = data.get("passphrase", "")

        # Exit su (no passphrase required)
        if not target or target == "exit":
            prev = session.get_context(su_key)
            session.set_context(su_key, None)
            return _ok(rid, {"status": "su_exited", "previous": prev})

        # All other su targets require passphrase re-verification
        if not passphrase:
            return _err(rid, -32602, "su requires 'passphrase'")

        presented_hash = hashlib.sha256(passphrase.encode("utf-8")).hexdigest()
        if not self.iam.verify_passphrase(real_client_id, presented_hash):
            return _err(rid, -32001, "Authentication failed: invalid passphrase")

        # Root mode
        if target == "root":
            session.set_context(su_key, "root")
            return _ok(rid, {
                "status": "su_active",
                "target": "root",
                "warning": "All scope restrictions lifted. Full system access active.",
            })

        # Librarian mode — adds role:librarian to current admin session
        if target == "librarian":
            session.set_context(su_key, "librarian")
            return _ok(rid, {
                "status": "su_active",
                "target": "librarian",
                "warning": "Librarian mode active. Nucleus write access and ontology operations enabled.",
            })

        # Impersonate another client — verify identity exists
        try:
            self.iam.authenticate(target)
        except PermissionError:
            return _err(rid, -32002, f"su: unknown identity '{target}'")

        session.set_context(su_key, target)
        return _ok(rid, {"status": "su_active", "target": target})

    # ------------------------------------------------------------------
    # User management handlers (admin only)
    # ------------------------------------------------------------------

    def _assert_admin(self, session) -> Optional[str]:
        """Return error message string if caller is not admin, else None."""
        try:
            role = self.iam.authenticate(session.client_id)
        except PermissionError:
            return "Permission denied: admin role required"
        if role != Role.ADMIN:
            return "Permission denied: admin role required"
        return None

    def _handle_user_ls(self, rid, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        users = self.iam.list_clients()
        # Strip passphrase hash from output
        sanitized = [
            {k: v for k, v in u.items() if k != "passphrase_hash"}
            for u in users
        ]
        return _ok(rid, {"users": sanitized, "count": len(sanitized)})

    def _handle_user_add(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id   = (data.get("client_id") or data.get("id") or "").strip()
        role_str    = data.get("role", "user").strip().lower()
        phash       = data.get("passphrase_hash", "")
        display     = data.get("display_name", client_id)
        if not client_id:
            return _err(rid, -32602, "user.add requires 'client_id'")
        try:
            role = Role(role_str)
        except ValueError:
            return _err(rid, -32602, f"Unknown role '{role_str}'. Valid: user, librarian, group_admin, admin")
        try:
            record = self.iam.register_client(
                client_id, role,
                passphrase_hash=phash or None,
                created_by=session.client_id,
                display_name=display,
            )
        except ValueError as e:
            return _err(rid, -32602, str(e))

        # Create a private HumanConcept identity record for the new client.
        # Scope: owner:user_{client_id} + view:user_{client_id} — accessible only
        # by the client themselves and by admins (via view:admin_override).
        # Note: Role.GUEST clients lack owner:user_* in their active_scopes and
        # therefore cannot read back their own Human atom until the role is upgraded.
        human_id = None
        if _HumanConcept is not None:
            try:
                from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
                new_session = self.manager.get_session(client_id)
                human = _HumanConcept(new_session)
                # System-initiated identity write: it does not run under a user
                # conversation workspace, so exempt it from the single-route guard
                # (same pattern as genesis/anchor writes). Without this the
                # HumanConcept atom is rejected and the member has no identity record.
                with _sys_ctx():
                    result = human.op_new(
                        name=display,
                        description=f"Identity record for registered client '{client_id}'",
                        client_id=client_id,
                    )
                human_id = result.get("human_id")
                # Store the mapping so the user can retrieve their identity later
                new_session.set_context("identity_human_id", human_id)
            except Exception as exc:
                logger.warning("[user.add] HumanConcept creation failed for '%s': %s", client_id, exc)

        return _ok(rid, {"status": "created", "client_id": client_id, "role": role.value,
                         "human_id": human_id})

    def _handle_user_rm(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id = (data.get("client_id") or data.get("id") or "").strip()
        if not client_id:
            return _err(rid, -32602, "user.rm requires 'client_id'")
        if client_id == session.client_id:
            return _err(rid, -32602, "Cannot remove yourself")
        try:
            self.iam.deregister_client(client_id)
        except (KeyError, ValueError) as e:
            return _err(rid, -32602, str(e))
        return _ok(rid, {"status": "removed", "client_id": client_id})

    def _handle_user_mod(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id = (data.get("client_id") or data.get("id") or "").strip()
        role_str  = data.get("role", "").strip().lower()
        if not client_id or not role_str:
            return _err(rid, -32602, "user.mod requires 'client_id' and 'role'")
        try:
            role = Role(role_str)
            self.iam.set_role(client_id, role)
        except ValueError as e:
            return _err(rid, -32602, str(e))
        return _ok(rid, {"status": "updated", "client_id": client_id, "role": role_str})

    def _handle_user_id(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id = (data.get("client_id") or data.get("id") or "").strip()
        if not client_id:
            return _err(rid, -32602, "user.id requires 'client_id'")
        record = self.iam.get_client(client_id)
        if not record:
            return _err(rid, -32002, f"User '{client_id}' not found")
        groups = self.iam.get_client_groups(client_id)
        info = {k: v for k, v in record.items() if k != "passphrase_hash"}
        info.update({"client_id": client_id, "groups": groups,
                     "has_passphrase": bool(record.get("passphrase_hash"))})
        return _ok(rid, info)

    def _handle_passwd_self(self, rid, data, session) -> dict:
        """Self-service passphrase change — any authenticated user, own account only."""
        current_hash = data.get("current_hash", "").strip()
        new_hash     = data.get("new_hash", "").strip()
        if not current_hash or not new_hash:
            return _err(rid, -32602, "passwd requires 'current_hash' and 'new_hash'")
        if not self.iam.verify_passphrase(session.client_id, current_hash):
            return _err(rid, -32001, "Authentication failed: incorrect current passphrase")
        try:
            self.iam.set_passphrase(session.client_id, new_hash)
        except (KeyError, ValueError) as e:
            return _err(rid, -32602, str(e))
        return _ok(rid, {"status": "passphrase_updated", "client_id": session.client_id})

    def _handle_user_passwd(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id = (data.get("client_id") or data.get("id") or "").strip()
        phash     = data.get("passphrase_hash", "").strip()
        if not client_id or not phash:
            return _err(rid, -32602, "user.passwd requires 'client_id' and 'passphrase_hash'")
        try:
            self.iam.set_passphrase(client_id, phash)
        except (KeyError, ValueError) as e:
            return _err(rid, -32602, str(e))
        return _ok(rid, {"status": "passphrase_updated", "client_id": client_id})

    # ------------------------------------------------------------------
    # Group management handlers
    # ------------------------------------------------------------------

    def _handle_grp_ls(self, rid, data, session) -> dict:
        group_id = (data.get("group_id") or data.get("id") or "").strip()
        if group_id:
            g = self.iam.get_group(group_id)
            if not g:
                return _err(rid, -32002, f"Group '{group_id}' not found")
            return _ok(rid, {"group": g})
        return _ok(rid, {"groups": self.iam.list_groups(), "count": len(self.iam.list_groups())})

    def _handle_grp_new(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        group_id  = (data.get("group_id") or data.get("id") or "").strip()
        admin_id  = (data.get("admin_id") or data.get("admin") or "").strip()
        if not group_id or not admin_id:
            return _err(rid, -32602, "grp.new requires 'group_id' and 'admin_id'")
        self.iam.create_group(group_id, admin_id)
        return _ok(rid, {"status": "created", "group_id": group_id, "admin": admin_id})

    def _handle_grp_add(self, rid, data, session) -> dict:
        group_id  = (data.get("group_id") or "").strip()
        member_id = (data.get("member_id") or data.get("member") or "").strip()
        if not group_id or not member_id:
            return _err(rid, -32602, "grp.add requires 'group_id' and 'member_id'")
        try:
            self.iam.add_group_member(group_id, session.client_id, member_id)
        except PermissionError as e:
            return _err(rid, -32003, str(e))
        return _ok(rid, {"status": "added", "group_id": group_id, "member": member_id})

    def _handle_grp_rm(self, rid, data, session) -> dict:
        group_id  = (data.get("group_id") or "").strip()
        member_id = (data.get("member_id") or data.get("member") or "").strip()
        if not group_id or not member_id:
            return _err(rid, -32602, "grp.rm requires 'group_id' and 'member_id'")
        try:
            self.iam.remove_group_member(group_id, session.client_id, member_id)
        except PermissionError as e:
            return _err(rid, -32003, str(e))
        return _ok(rid, {"status": "removed", "group_id": group_id, "member": member_id})

    def _handle_grp_lib(self, rid, data, session) -> dict:
        group_id  = (data.get("group_id") or "").strip()
        action    = (data.get("action") or "").strip().lower()
        member_id = (data.get("member_id") or data.get("member") or "").strip()
        if not group_id or action not in ("grant", "revoke") or not member_id:
            return _err(rid, -32602, "grp.lib requires 'group_id', 'action' (grant|revoke), 'member_id'")
        try:
            if action == "grant":
                self.iam.grant_group_librarian(group_id, session.client_id, member_id)
            else:
                self.iam.revoke_group_librarian(group_id, session.client_id, member_id)
        except PermissionError as e:
            return _err(rid, -32003, str(e))
        return _ok(rid, {"status": f"librarian_{action}ed", "group_id": group_id, "member": member_id})

    def _handle_grp_del(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        group_id = (data.get("group_id") or data.get("id") or "").strip()
        if not group_id:
            return _err(rid, -32602, "grp.del requires 'group_id'")
        if not self.iam.get_group(group_id):
            return _err(rid, -32002, f"Group '{group_id}' not found")
        self.iam.delete_group(group_id)
        return _ok(rid, {"status": "deleted", "group_id": group_id})

    # ------------------------------------------------------------------
    # Donation / Delegation Sets (dont.*)
    # ------------------------------------------------------------------
    # Delegation sets are named collections used to transfer (donate) a bundle
    # of atoms to a shared space: the nucleus (universal) or a group space.
    # Metadata on the set records provenance on both origin and destination.
    # Set name convention: "dont:<user_name>" e.g. dont:love_vocab

    def _handle_dont_create(self, rid, data, session) -> dict:
        """Create or update a named delegation set with provenance metadata."""
        ctx = session.local_cortex
        client_id = session.client_id
        name = (data.get("name") or "").strip()
        if not name:
            return _err(rid, -32602, "dont.create requires 'name'")
        set_name = f"dont:{name}" if not name.startswith("dont:") else name
        description = (data.get("description") or data.get("desc") or "").strip()
        import time as _time
        meta = {
            "type": "donation_set",
            "created_by": client_id,
            "created_at": _time.time(),
            "description": description,
            "donations": []
        }
        ctx.create_donation_set(set_name, meta)
        return _ok(rid, {"set": set_name, "status": "created", "meta": meta})

    def _handle_dont_add(self, rid, data, session) -> dict:
        """Add atoms to a delegation set."""
        ctx = session.local_cortex
        scopes = session.active_scopes
        name = (data.get("name") or "").strip()
        targets = data.get("targets") or data.get("target") or []
        if not name:
            return _err(rid, -32602, "dont.add requires 'name'")
        set_name = f"dont:{name}" if not name.startswith("dont:") else name

        if isinstance(targets, str):
            targets = [t.strip() for t in targets.split() if t.strip()]

        history = ctx.stream(10)
        added = []
        for t in targets:
            resolved = self._resolve_target(t, session, history)
            if not resolved or isinstance(resolved, list):
                resolved = t
            if ctx.get_chunk(resolved):
                ctx.core.add_to_collection(set_name, resolved)
                added.append(resolved)

        return _ok(rid, {"set": set_name, "added": len(added), "keys": added})

    def _handle_dont_send(self, rid, data, session) -> dict:
        """
        Donate all atoms in a delegation set to a shared space.
        'to': "universal" | "group:<id>"
        'open': bool (default False) — if True, extend original scope instead of copying
        """
        ctx = session.local_cortex
        scopes = session.active_scopes
        client_id = session.client_id
        name = (data.get("name") or "").strip()
        destination = (data.get("to") or "").strip()
        do_open = bool(data.get("open", False))

        if not name or not destination:
            return _err(rid, -32602, "dont.send requires 'name' and 'to'")
        set_name = f"dont:{name}" if not name.startswith("dont:") else name

        # Resolve target engine
        if destination == "universal":
            if "role:librarian" not in scopes:
                return _err(rid, -32003, "Universal donation requires librarian role")
            target_engine = session.nucleus
            target_scope = "scope:sys:universal"
            target_label = "nucleus"
        elif destination.startswith("group:"):
            gid = destination[6:]
            if f"scope:group_{gid}" not in scopes:
                return _err(rid, -32003, f"Not a member of group '{gid}'")
            target_engine = session.group_engines.get(gid)
            if not target_engine:
                return _err(rid, -32002, f"Group space '{gid}' not loaded in this session")
            target_scope = f"scope:group_{gid}"
            target_label = f"group:{gid}"
        else:
            return _err(rid, -32602, f"Unknown destination '{destination}'. Use 'universal' or 'group:<id>'")

        # List set members
        member_keys = ctx.core.get_collection_members(set_name)
        if not member_keys:
            return _err(rid, -32002, f"Delegation set '{set_name}' is empty or not found")

        import time as _time
        import json as _json
        donated = []
        skipped = []

        for key in member_keys:
            row = ctx.core.get_chunk_raw(key)
            if not row:
                skipped.append(key)
                continue
            content = row["content"] or ""
            try:
                meta = _json.loads(row.get("meta") or "{}")
            except Exception:
                meta = {}

            if do_open:
                # "Open" mode: extend original atom's scope (no copy)
                ctx.core.put_chunk_access(key, [target_scope])
            else:
                # Copy mode: write atom to target engine
                target_engine.put_atom(content, meta, author=client_id)
                # Copy all aliases for this key to target
                for alias in ctx.get_aliases_by_key(key):
                    target_engine.core.put_alias(key, alias)
            # Mirror set membership in target
            target_engine.add_to_set(set_name, key)
            donated.append(key)

        # Record donation in origin set metadata
        origin_meta = ctx.get_donation_set_meta(set_name) or {}
        donations = origin_meta.get("donations", [])
        donation_record = {
            "target": target_label,
            "donated_at": _time.time(),
            "atom_count": len(donated),
            "mode": "open" if do_open else "copy",
        }
        donations.append(donation_record)
        origin_meta["donations"] = donations
        ctx.update_donation_set_meta(set_name, origin_meta)

        # Record receipt in target set metadata
        receipt_meta = {
            "type": "donation_receipt",
            "source_cell": client_id,
            "source_set": set_name,
            "donated_at": donation_record["donated_at"],
            "atom_count": len(donated),
            "mode": donation_record["mode"],
        }
        target_engine.upsert_set_meta(set_name, receipt_meta)

        return _ok(rid, {
            "status": "donated",
            "set": set_name,
            "to": target_label,
            "mode": donation_record["mode"],
            "donated": len(donated),
            "skipped": len(skipped),
            "donated_at": donation_record["donated_at"],
        })

    def _handle_dont_ls(self, rid, data, session) -> dict:
        """List delegation sets and their donation history."""
        ctx = session.local_cortex
        name = (data.get("name") or "").strip()
        if name:
            set_name = f"dont:{name}" if not name.startswith("dont:") else name
            meta = ctx.get_donation_set_meta(set_name)
            if meta is None:
                return _err(rid, -32002, f"Delegation set '{set_name}' not found")
            members = ctx.core.get_collection_members(set_name)
            return _ok(rid, {"set": set_name, "atom_count": len(members), "meta": meta})
        else:
            sets = ctx.list_donation_sets()
            for s in sets:
                s["atom_count"] = len(ctx.core.get_collection_members(s["name"]))
            return _ok(rid, {"donation_sets": sets})

    def _handle_dont_open(self, rid, data, session) -> dict:
        """Convenience: dont.send with open=True (extend original scope, no copy)."""
        return self._handle_dont_send(rid, {**data, "open": True}, session)

    # ------------------------------------------------------------------
    # Unauthenticated handlers
    # ------------------------------------------------------------------

    def _handle_ping(self, rid: str, client_id: str) -> dict:
        # CONSTANT-TIME LIVENESS ONLY. sys.ping is the reachability probe the portal /
        # CLI client (cell_ipc.ping) uses to decide "is the Cell daemon there?" — it only
        # needs "the daemon answered", nothing more. It therefore touches NO iam / manager /
        # session / consciousness / DB: those calls run on the same GIL as the writer, so a
        # heavy dive (mega-hub fan-out) or boot-time index/cache warming holding the CPU could
        # otherwise stall this probe past its timeout and be MISREAD as "writer unreachable",
        # fail-closing the write-forwarding path even though the daemon is alive but busy.
        # Keeping it O(1) means once the probe gets a GIL slice it returns instantly.
        # The rich cogito view (consciousness.ping) is served by _handle_status_full / sys.status.
        return _ok(rid, {
            "status": "kernel_online",
            "series": self.series,
            "timestamp": time.time(),
            "alive": True,
            # Running-code fingerprint (stamped by the launcher at daemon boot). A re-extracted
            # seed / pulled repo boots argument-less → attaches to THIS daemon over the socket;
            # if its on-disk code differs from what this daemon is running, the client replaces
            # the daemon instead of running new tests on stale code. Constant-time env read.
            # Prefer the CODE-CONTENT fingerprint (AKASHA_HANDSHAKE_BUILD) for the replace
            # handshake — it is identical for identical code however the daemon was launched (seed
            # vs plain `python akasha.py`). AKASHA_BUILD_ID may be a git-SHA display label the seed
            # stamped, which differs from a plain reconnect's content hash and would wrongly trigger
            # a daemon-replace (the silent no-trace daemon kill + boot loop). Fall back to it only
            # for a daemon booted before this field existed.
            "build": os.environ.get("AKASHA_HANDSHAKE_BUILD") or os.environ.get("AKASHA_BUILD_ID", ""),
        })

    def _handle_status(self, rid: str) -> dict:
        return _ok(rid, {
            "status": "online",
            "series": self.series,
            "harmonia": self.harmonia is not None,
            "contexa": self.contexa is not None,
            "active_sessions": len(self.manager.sessions),
            "timestamp": time.time()
        })

    def _handle_ref_set(self, rid: str, data: dict, session) -> dict:
        """Set a typed context slot: ref.set dim=who target=<atom>."""
        from lib.akasha.ref_primitives import REF_SLOT_DIMENSIONS
        dim    = data.get("dim", "").strip()
        target = data.get("target", "").strip()
        if not dim or not target:
            return _err(rid, -32602, "ref.set requires 'dim' and 'target'")
        if dim not in REF_SLOT_DIMENSIONS:
            return _err(rid, -32602,
                        f"Unknown ref dimension '{dim}'. "
                        f"Valid: {', '.join(sorted(REF_SLOT_DIMENSIONS))}")
        resolved = self._resolve_target(target, session, []) or target
        session.set_ref_slot(dim, resolved)
        return _ok(rid, {"dim": dim, "key": resolved, "var": f"${dim}"})

    def _handle_ref_get(self, rid: str, data: dict, session) -> dict:
        """Get all (or one) typed context slot values."""
        from lib.akasha.ref_primitives import REF_SLOT_DIMENSIONS
        dim = data.get("dim", "").strip()
        if dim:
            if dim not in REF_SLOT_DIMENSIONS:
                return _err(rid, -32602, f"Unknown ref dimension '{dim}'")
            key = session.get_ref_slot(dim)
            return _ok(rid, {"dim": dim, "key": key, "var": f"${dim}"})
        slots = {
            d: session.get_ref_slot(d)
            for d in sorted(REF_SLOT_DIMENSIONS)
        }
        return _ok(rid, {"slots": slots})

    def _handle_status_full(self, rid: str, session) -> dict:
        """Aggregate status: cogito payload + akasha_name, series, display_focus, JCL summary."""
        result = session.consciousness.ping(session)
        try:
            akasha_name = self._nucleus().vault_retrieve("system", "akasha_name") or "AKASHA"
        except Exception:
            akasha_name = "AKASHA"
        result["akasha_name"]   = akasha_name
        result["series"]        = self.series
        result["version"]       = _AKASHA_VERSION
        result["display_focus"] = session.get_context("display_focus") or {}
        if self.jcl_worker:
            from collections import Counter as _Ctr
            all_jobs = self.jcl_worker.list_jobs(owner=session.client_id)
            counts   = _Ctr(j.status for j in all_jobs)
            result["jcl"] = {
                "running":     counts.get("RUNNING", 0),
                "pending":     counts.get("PENDING", 0),
                "queue_depth": self.jcl_worker.queue_depth(),
            }
        else:
            result["jcl"] = None
        return _ok(rid, result)

    def _handle_sys_ls(self, rid: str, data: dict, ctx, scopes, client_id: str) -> dict:
        # Cursor pagination over the recent-atom stream. Fetch enough of the stream to
        # cover offset+limit AFTER filtering (×5 slack for excluded sys/other-author
        # atoms), then page the filtered list.
        lim = _rlimit(data.get("limit"), default=10, max_limit=100)
        off = _roffset(data.get("cursor"))
        need = off + (lim or 100)
        raw = ctx.stream(need * 5 + 20)
        # su root: expose all atoms including system-owned ones
        if scopes and "scope:sys:root" in scopes:
            filtered = list(raw)
        else:
            # Keep only atoms authored by this user; exclude internal sys: atoms.
            filtered = [item for item in raw
                        if item.get("author") == client_id and not _is_sys_atom(item)]
        window, page = _paginate(filtered, data.get("limit"), data.get("cursor"),
                                 default=10, max_limit=100)
        atoms = []
        for i, item in enumerate(window):
            key     = item.get("key", "")
            content = item.get("content") or ctx.get_chunk(key) or ""
            aliases = ctx.get_aliases_by_key(key)
            atoms.append({"idx": page["offset"] + i, "key": key, "preview": content[:60], "aliases": aliases})
        return _ok(rid, {"atoms": atoms, "count": len(atoms), "page": page})

    def _handle_genesis_rite(self, rid: str, data: dict) -> dict:
        akasha_name = data.get("akasha_name", "AKASHA")
        user_name = data.get("user_name", "")
        raw_passphrase = data.get("passphrase", "")

        if not user_name or not raw_passphrase:
            return _err(rid, -32602, "genesis_rite requires 'user_name' and 'passphrase'")

        passphrase_hash = hashlib.sha256(raw_passphrase.encode("utf-8")).hexdigest()

        # Bootstrap a temporary system session for the ceremony
        # Use the existing manager without strict IAM (pre-genesis state)
        try:
            session = self.manager.get_session("sys:genesis_bootstrap")
        except Exception:
            session = None

        # Perform the rite via the consciousness layer
        consciousness = session.consciousness if session else None
        if not consciousness:
            # Fallback: create bare-minimum cortex for the ceremony
            from lib.akasha.composite import AkashaEngine
            import os
            os.makedirs(f"{self.base_dir}/cells/sys_genesis", exist_ok=True)
            bare_cortex = AkashaEngine(f"{self.base_dir}/cells/sys_genesis/genesis.db")
            from lib.akasha.consciousness import ConsciousnessEngine
            consciousness = ConsciousnessEngine(bare_cortex)

        # The genesis ceremony writes the akasha-name / keeper anchor atoms outside
        # any request workspace (it runs before the first session/turn). Exempt those
        # system writes from the single-route guard.
        from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
        with _sys_ctx():
            result = consciousness.genesis_rite(akasha_name, user_name, passphrase_hash, session)

        # If rite succeeded, register the genesis admin in the persistent IAM store
        if result.get("status") == "bound":
            self.iam.register_client(user_name, Role.ADMIN,
                                     passphrase_hash=passphrase_hash,
                                     created_by="genesis",
                                     display_name=user_name)
            if user_name != "admin":
                # Also register the canonical "admin" alias used by automation
                self.iam.register_client("admin", Role.ADMIN,
                                         passphrase_hash=passphrase_hash,
                                         created_by="genesis",
                                         display_name="admin")

            # Trigger ontology boot load now that admin exists.
            # _boot_load_ontology is a no-op when called at kernel init on a
            # fresh install (no admin yet), so we re-run it after genesis_rite.
            if self.jcl_worker:
                import threading as _thr_g
                _thr_g.Thread(target=self._boot_load_ontology, daemon=True,
                              name="ont-genesis-load").start()

        return _ok(rid, result)

    def _nucleus(self):
        """Returns the process-shared NucleusEngine from the manager."""
        return self.manager.shared_nucleus

    def _handle_auth_status(self, rid: str) -> dict:
        # Pre-auth endpoint: report only whether the Cell is initialized.  The
        # admin username is NOT disclosed — under the token model the username is
        # the login identifier, so leaking it pre-auth hands an attacker half the
        # credential (and the whole of it under the old bare-id model).
        try:
            n = self._nucleus()
            admin_name = n.vault_retrieve("system", "admin_name")
            akasha_name = n.vault_retrieve("system", "akasha_name") or "AKASHA"
        except Exception:
            n, admin_name, akasha_name = None, None, "AKASHA"
        # `initialized` requires BOTH an admin name AND a usable passphrase credential — not just
        # the name. A crash mid-genesis (or the old Silica read-fd race aborting a genesis write)
        # can leave a HALF-WRITTEN genesis vault: `system/admin_name` persisted but the matching
        # credential (`iam/user:<name>` / `iam/user:admin` / legacy `system/passphrase_hash`) did
        # not. With the old `admin_name is not None` test that reads as initialized, so the console
        # shows a login prompt that can NEVER succeed (no credential to verify against) — a soft
        # brick. Treating "name present, no credential" as NOT initialized lets the local console
        # re-run the genesis ceremony and re-establish the admin, WITHOUT touching the graph
        # (genesis only overwrites the genesis vault + admin record; every ontology/user atom is
        # preserved). Safe: genesis_rite is local-console-only (TRUST_LOCAL), so this never opens a
        # network admin land-grab. Reads the durable vault directly (not the cache), so it reflects
        # ground truth, not a boot-timing gap.
        credential_present = False
        if n is not None and admin_name:
            try:
                rec = (n.vault_retrieve("iam", f"user:{admin_name}")
                       or n.vault_retrieve("iam", "user:admin"))
                if isinstance(rec, dict) and rec.get("passphrase_hash"):
                    credential_present = True
                elif n.vault_retrieve("system", "passphrase_hash"):
                    credential_present = True          # legacy single-hash genesis vault entry
            except Exception:
                credential_present = False
            if not credential_present:
                logger.warning("[IAM] auth.status: admin_name=%r present but NO usable passphrase "
                               "credential in the vault — reporting uninitialized so the local "
                               "console can re-run genesis (graph is preserved).", admin_name)
        return _ok(rid, {
            "initialized": bool(admin_name is not None and credential_present),
            "akasha_name": akasha_name,
        })

    def _handle_auth_verify(self, rid: str, data: dict) -> dict:
        user_id = data.get("user_id", "")
        passphrase = data.get("passphrase", "")
        if not user_id or not passphrase:
            return _err(rid, -32602, "auth.verify requires 'user_id' and 'passphrase'")

        # System process identities have no passphrase and are never a login.
        if self.iam.is_system_identity(user_id):
            return _err(rid, -32001, "Authentication failed: invalid credentials")

        passphrase_hash = hashlib.sha256(passphrase.encode("utf-8")).hexdigest()

        # Verify passphrase through IAM (covers per-user hashes + genesis fallback)
        if not self.iam.verify_passphrase(user_id, passphrase_hash):
            return _err(rid, -32001, "Authentication failed: invalid credentials")

        try:
            role = self.iam.authenticate(user_id)
        except PermissionError:
            return _err(rid, -32001, "Authentication failed: unknown user")

        # Mint a signed, expiring session token bound to this identity.  This —
        # not the bare username — is what the client presents on subsequent calls.
        try:
            ttl = max(60, min(int(data.get("ttl", 1800)), 86400))
        except (TypeError, ValueError):
            ttl = 1800
        try:
            minted = self.iam.issue_session_token(user_id, ttl)
        except PermissionError as e:
            return _err(rid, -32001, str(e))

        return _ok(rid, {
            "status": "authenticated",
            "user_id": user_id,
            "session_token": minted["session_token"],
            "expires_at": minted["expires_at"],
            "role": role.value,
        })

    # ------------------------------------------------------------------
    # Self-service registration + entitlement plan (general, product-neutral)
    # ------------------------------------------------------------------
    @staticmethod
    def _self_register_enabled() -> bool:
        return str(os.environ.get("AKASHA_ALLOW_SELF_REGISTER", "")).strip().lower() \
            in ("1", "yes", "true", "on")

    def _get_plan(self, uid: str) -> str:
        """A user's entitlement tier from the shared nucleus vault ('entitlement' KV).
        Product-neutral; 'paid' only if explicitly set, else 'free'."""
        try:
            v = self._nucleus().vault_retrieve("entitlement", uid)
        except Exception:
            v = None
        return "paid" if str(v or "").strip().lower() == "paid" else "free"

    def _set_plan(self, uid: str, tier: str) -> None:
        self._nucleus().vault_store("entitlement", uid, tier)

    def _handle_auth_register(self, rid, data) -> dict:
        """Self-service account creation. DELIBERATELY BOUNDED (a loosening of the
        admin-only user-management rule): OFF unless AKASHA_ALLOW_SELF_REGISTER is set;
        role is FORCED to 'user' (never client-supplied, no privilege escalation); an
        existing id is REJECTED (never overwritten → no account hijack); a passphrase is
        required. Abuse controls (rate limiting, email/CAPTCHA) are a deployment concern.
        On success it auto-logs-in (returns a session token) and starts on the free plan."""
        if not self._self_register_enabled():
            return _err(rid, -32601, "Self-registration is not enabled on this server.")
        client_id  = (data.get("user_id") or data.get("client_id") or "").strip()
        passphrase = data.get("passphrase", "")
        display    = (data.get("display_name") or client_id).strip()
        if not client_id or not passphrase:
            return _err(rid, -32602, "auth.register requires 'user_id' and 'passphrase'.")
        if not (3 <= len(client_id) <= 64) or not all(
                c.isalnum() or c in "_.-" for c in client_id):
            return _err(rid, -32602, "user_id must be 3-64 chars of [A-Za-z0-9_.-].")
        if len(passphrase) < 8:
            return _err(rid, -32602, "passphrase must be at least 8 characters.")
        if self.iam.is_system_identity(client_id):
            return _err(rid, -32001, "That identity is reserved.")
        # No overwrite: a taken id is rejected (prevents account takeover).
        try:
            taken = self.iam._cache.get(client_id) is not None
        except Exception:
            taken = False
        if taken:
            return _err(rid, -32602, "That user id is already taken.")

        presented = hashlib.sha256(passphrase.encode("utf-8")).hexdigest()
        try:
            self.iam.register_client(client_id, Role.USER,          # role FORCED to user
                                     passphrase_hash=presented,
                                     created_by="self-register", display_name=display)
        except ValueError as e:
            return _err(rid, -32602, str(e))

        # Best-effort private identity record (same as admin user.add).
        if _HumanConcept is not None:
            try:
                from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
                new_session = self.manager.get_session(client_id)
                with _sys_ctx():
                    _HumanConcept(new_session).op_new(
                        name=display, description=f"Self-registered client '{client_id}'",
                        client_id=client_id)
            except Exception as exc:
                logger.warning("[auth.register] identity record for '%s' failed: %s", client_id, exc)

        try:
            ttl = max(60, min(int(data.get("ttl", 1800)), 86400))
        except (TypeError, ValueError):
            ttl = 1800
        try:
            minted = self.iam.issue_session_token(client_id, ttl)
        except PermissionError as e:
            return _err(rid, -32001, str(e))
        return _ok(rid, {"status": "registered", "user_id": client_id,
                         "session_token": minted["session_token"],
                         "expires_at": minted["expires_at"], "role": "user", "tier": "free"})

    def _handle_account_delete(self, rid, data, session, role) -> dict:
        """Self-service account deletion — the caller erases their OWN account. Deletes:
        the identity (soft-deleted in IAM: active=False, so the login can never be used
        again but the record is retained as the legally-required audit trail), the entire
        private cell (l_cortex.db — every recipe, personal food, measurement, and private
        atom the user authored), and the entitlement/plan entry. It never targets another
        user, and it does not touch the shared nucleus/catalogue.

        Requires an explicit confirmation (`confirm=true` or `confirm=<your user_id>`) so a
        stray call can't wipe an account. Guests (no account) and admins (removed via
        user-management so the Cell can't be locked out of its last admin) are refused."""
        uid = session.client_id
        confirm = str(data.get("confirm", "")).strip().lower()
        if confirm not in ("true", "yes", "1", "delete", uid.lower()):
            return _err(rid, -32602,
                        "auth.account.delete requires confirm=true (irreversible: this "
                        "erases your account, recipes, personal foods, and measurements).")
        if role == Role.GUEST or self.iam.is_system_identity(uid):
            return _err(rid, -32001, "This session has no deletable account.")
        if role == Role.ADMIN:
            return _err(rid, -32001,
                        "Admin accounts are removed via user management, not self-deletion "
                        "(prevents locking the Cell out of its last admin).")
        # 1. Identity → soft-delete (audit retained).
        try:
            self.iam.deregister_client(uid)
        except (KeyError, ValueError) as e:
            return _err(rid, -32001, f"Account deletion failed: {e}")
        # 2. Entitlement/plan entry → purge.
        try:
            self._nucleus().vault_delete("entitlement", uid)
        except Exception as e:
            logger.warning("[account.delete] entitlement purge for '%s' failed: %s", uid, e)
        # 3. Private cell (all user-authored data) → erase.
        purged = False
        try:
            purged = bool(self.manager.purge_client_cell(uid))
        except Exception as e:
            logger.warning("[account.delete] cell purge for '%s' failed: %s", uid, e)
        # 4. Drop the live session (token can no longer resolve an active identity).
        try:
            self.manager.close_session(uid)
        except Exception:
            pass
        return _ok(rid, {"status": "deleted", "user_id": uid, "cell_purged": purged,
                         "note": "identity retained as audit (deactivated); all private "
                                 "data erased. Sign-in with this id is no longer possible."})

    def _handle_auth_plan(self, rid, session) -> dict:
        """Read the caller's entitlement tier (product-neutral)."""
        uid = session.client_id
        return _ok(rid, {"user_id": uid, "tier": self._get_plan(uid)})

    def _handle_auth_plan_set(self, rid, data, session) -> dict:
        """(admin) Set a user's entitlement tier — the server-side billing hook. An
        external billing service validates the store receipt (App Store / Play) and then
        calls this with an admin token; the client can never set its own plan."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        uid  = (data.get("user") or data.get("user_id") or "").strip()
        tier = (data.get("tier") or "").strip().lower()
        if not uid or tier not in ("free", "paid"):
            return _err(rid, -32602, "auth.plan.set requires user=<id> and tier=free|paid.")
        self._set_plan(uid, tier)
        return _ok(rid, {"status": "set", "user_id": uid, "tier": tier})

    # ------------------------------------------------------------------
    # Memory handlers
    # ------------------------------------------------------------------

    def _resolve_target(self, target: str, session, history: list) -> Optional[str]:
        """Resolves $-references, aliases, and direct keys. Returns None on failure."""
        try:
            return ContextResolver.resolve(session, target, history)
        except Exception:
            return None

    def _handle_write(self, rid, data, session, ctx, scopes, client_id) -> dict:
        text = data.get("text") or data.get("content", "")
        if not text:
            return _err(rid, -32602, "write requires 'text'")

        meta = data.get("meta", {})
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}

        # Derive write scopes: user's private scope + any explicit overrides.
        # When ctx is _NucleusWriteCtx (scope=universal + librarian), put_chunk
        # routes to nucleus automatically — no branching needed here.
        write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}"]
        if "view:public" in scopes and data.get("public"):
            write_scopes.append("view:public")
        key = ctx.put_chunk(content=text, meta=meta, author=client_id, scopes=write_scopes)

        session.set_context("last_written_id", key)
        session.last_written_id = key

        self._post_write(session, isinstance(ctx, _NucleusWriteCtx), key, text)

        return _ok(rid, {"key": key, "status": "written"})

    def _handle_define(self, rid, data, session, ctx, scopes, client_id) -> dict:
        name = data.get("name", "").strip()
        if not name:
            return _err(rid, -32602, "define requires 'name'")

        description = data.get("description") or f"Conceptual hub: {name}"
        hub_content = f"[{name.replace(' ', '_')}]\n{description}"

        # canonical=True marks this as the authoritative, explicitly-authored definition.
        # Implicit/auto-created atoms (proto-words) have auto_created=True instead.
        # Inferred links (specializes, proto-word scaffolding) carry status="inferred".
        meta = {"type": "hub", "name": name, "role": "concept", "canonical": True}
        write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}"]
        key = ctx.put_chunk(content=hub_content, meta=meta, author=client_id, scopes=write_scopes)
        # Authoritative ontology re-import (scope=universal) must UPDATE a changed def, not
        # silently keep the stale atom. Content-addressing gives edited text a NEW key, so
        # plain first-wins would leave the alias on the old atom and orphan the new content
        # (the release's fix never reaches the user). When the incumbent lives in the NUCLEUS
        # it is pack/ontology content (users can't write there) → rebind is safe and the
        # collision is logged for onto.report. A user cell atom holding the alias keeps
        # first-wins untouched. Ordinary (non-universal) user defines are unaffected.
        _force = False
        if str(data.get("scope", "")) == "universal":
            _nuc = getattr(session, "nucleus", None)
            if _nuc is not None:
                _prev = _nuc.core.get_key_by_alias(name)
                if _prev and _prev != key:
                    _force = True
        ctx.set_alias(key, name, force=_force)

        session.set_context("last_written_id", key)

        self._post_write(session, isinstance(ctx, _NucleusWriteCtx), key,
                         description, f"sys.weaver:{name[:40]}")

        return _ok(rid, {"key": key, "alias": name, "status": "defined"})

    # ------------------------------------------------------------------
    # Weaver — constituent-word → protoword links
    # ------------------------------------------------------------------

    def _weave_atom(self, nucleus, chunk_key: str, text: str) -> int:
        """
        Lemmatize text, link chunk_key to each lemma's nucleus protoword via
        sys:refers_to, and add chunk_key to the per-lemma set set:word:{lemma}.

        Lemma-First principle: if the protoword atom for a lemma does not yet
        exist in nucleus, _ensure_lemma_protoword auto-creates it so that
        SpaCy-lemmatized input always finds an anchor — for any language whose
        model is loaded.

        Both link and set operations are idempotent.
        Returns the number of links created.
        """
        woven = 0
        for (surface, lemma, lang, morph) in _lemmatize_for_weave(text):
            if len(lemma) < 2 or lemma in _WEAVE_STOPWORDS or lemma.isdigit():
                continue
            try:
                proto_key = nucleus._ensure_lemma_protoword(lemma, lang)
                if proto_key and proto_key != chunk_key:
                    nucleus.put_link(chunk_key, proto_key, "sys:refers_to",
                                     author="sys:weaver", status="inferred")
                    nucleus.add_to_set(f"set:word:{lemma}", chunk_key)
                    woven += 1

                    # If the surface form differs from the lemma and already has
                    # its own nucleus atom (e.g. word:en:asked from WordNet),
                    # link it to the lemma with a typed morph: relation.
                    if surface != lemma:
                        surf_key = (nucleus.core.get_key_by_alias(surface) or
                                    nucleus.core.get_key_by_alias(f"word:{lang}:{surface}"))
                        if surf_key and surf_key != proto_key:
                            rel = _morph_to_rel(morph)
                            nucleus.put_link(surf_key, proto_key, rel,
                                             author="sys:weaver", status="inferred")
            except Exception as _we:
                logger.debug("[Weaver] '%s'→lemma:'%s': %s", surface, lemma, _we)
        return woven

    def _weaver_denied(self, session, data, nucleus_write: bool):
        """Authorization gate for sys.weaver.* handlers.

        Weaving into the shared nucleus, or on behalf of another client, is a
        privileged/system operation — not something a plain USER may drive
        directly.  Legitimate weave jobs run under a librarian-tier owner
        (system.weaver for guests, the librarian/admin writer for nucleus
        writes, "admin" for boot pack loads), all of which carry role:librarian.
        Returns an error string if denied, else None.
        """
        scopes = session.active_scopes
        is_priv = "role:librarian" in scopes  # system.weaver / librarian / admin
        for_client = data.get("_for_client")
        if for_client and for_client != session.client_id and not is_priv:
            return "weaver: '_for_client' override requires a librarian/system role"
        if nucleus_write and not is_priv:
            return "weaver: nucleus weaving requires a librarian/collective-write role"
        return None

    def _handle_weave(self, rid, data, session) -> dict:
        """sys.weaver.weave — weave a single atom's text into protoword links."""
        denied = self._weaver_denied(session, data, nucleus_write=True)
        if denied:
            return _err(rid, -32003, denied)
        nucleus = getattr(session, 'nucleus', None)
        if not nucleus:
            return _ok(rid, {"status": "skipped", "reason": "no nucleus"})

        key  = data.get("key", "")
        text = data.get("text", "")
        alias = data.get("alias", "")

        if not key and alias:
            key = nucleus.core.get_key_by_alias(alias) or ""
        if not key:
            return _ok(rid, {"status": "skipped", "reason": "atom not found"})

        if not text and key:
            raw = nucleus.core.get_chunk_raw(key)
            if raw:
                content = raw.get("content", "") if isinstance(raw, dict) else str(raw)
                # Strip "[name]\n" prefix written by _handle_define
                text = content.split("\n", 1)[1] if "\n" in content else content

        if not text:
            return _ok(rid, {"status": "skipped", "reason": "no text"})

        woven = self._weave_atom(nucleus, key, text)
        return _ok(rid, {"status": "woven", "key": key, "links_created": woven})

    def _handle_weave_batch(self, rid, data, session) -> dict:
        """sys.weaver.weave_batch — weave a list of {alias, text} items in one step."""
        denied = self._weaver_denied(session, data, nucleus_write=True)
        if denied:
            return _err(rid, -32003, denied)
        nucleus = getattr(session, 'nucleus', None)
        if not nucleus:
            return _ok(rid, {"status": "skipped", "reason": "no nucleus"})

        items = data.get("items", [])
        total_woven = 0
        processed   = 0

        for item in items:
            alias = item.get("alias", "")
            text  = item.get("text", "")
            key   = item.get("key", "")

            if not key and alias:
                key = nucleus.core.get_key_by_alias(alias) or ""
            if not key or not text:
                continue

            try:
                total_woven += self._weave_atom(nucleus, key, text)
                processed += 1
            except Exception as _be:
                logger.debug("[Weaver] batch item '%s': %s", alias or key[:8], _be)

        logger.info("[Weaver] batch: %d atoms processed, %d links woven", processed, total_woven)
        return _ok(rid, {"status": "woven",
                          "atoms_processed": processed,
                          "links_created": total_woven})

    def _weave_client_atom(self, cortex, nucleus, chunk_key: str, text: str) -> int:
        """
        Client-space weave: link chunk_key to EXISTING nucleus protowords only,
        and add chunk_key to a per-lemma set in the client's own cortex.

        Privacy contract (black-hole boundary):
        - Lemmatizes text and looks up the lemma in nucleus (read-only access).
        - Lookup tries bare alias first, then qualified 'word:{lang}:{lemma}'.
        - Never creates new protowords in nucleus — no client data leaks outward.
        - Links and set memberships are written into the client's own cortex only.
        - Direction: client_atom → nucleus_protoword (one-way; no reverse link).
        - set:word:{lemma} in cortex = private index of client's atoms by concept.
        """
        woven = 0
        for (surface, lemma, lang, _morph) in _lemmatize_for_weave(text):
            if len(lemma) < 2 or lemma in _WEAVE_STOPWORDS or lemma.isdigit():
                continue
            try:
                proto_key = (nucleus.core.get_key_by_alias(lemma) or
                             nucleus.core.get_key_by_alias(f"word:{lang}:{lemma}"))
                if proto_key and proto_key != chunk_key:
                    cortex.put_link(chunk_key, proto_key, "sys:refers_to",
                                    author="sys:weaver", status="inferred")
                    cortex.add_to_set(f"set:word:{lemma}", chunk_key)
                    woven += 1
            except Exception as _we:
                logger.debug("[Weaver/client] '%s'→lemma:'%s': %s", surface, lemma, _we)
        return woven

    def _handle_weave_client(self, rid, data, session) -> dict:
        """sys.weaver.weave_client — weave a client atom into existing nucleus protowords."""
        # weave_client only READS nucleus protowords and writes into the target
        # cortex, so it is safe on one's own cortex; the _for_client override
        # (writing into another client's cortex) is the privileged part.
        denied = self._weaver_denied(session, data, nucleus_write=False)
        if denied:
            return _err(rid, -32003, denied)
        # When running as system.weaver on behalf of a guest, _for_client names
        # the original session so we access the correct cortex.
        for_client = data.get("_for_client")
        if for_client:
            _target = self.manager.get_session(for_client)
            nucleus = getattr(_target, 'nucleus', None)
            cortex  = _target.local_cortex
        else:
            nucleus = getattr(session, 'nucleus', None)
            cortex  = session.local_cortex
        if not nucleus:
            return _ok(rid, {"status": "skipped", "reason": "no nucleus"})

        key   = data.get("key", "")
        text  = data.get("text", "")
        alias = data.get("alias", "")

        if not key and alias:
            key = cortex.resolve_alias(alias) or ""
        if not key:
            return _ok(rid, {"status": "skipped", "reason": "atom not found"})

        if not text and key:
            raw = cortex.get_chunk_raw(key) if hasattr(cortex, 'get_chunk_raw') else None
            if raw:
                content = raw.get("content", "") if isinstance(raw, dict) else str(raw)
                text = content.split("\n", 1)[1] if "\n" in content else content

        if not text:
            return _ok(rid, {"status": "skipped", "reason": "no text"})

        woven = self._weave_client_atom(cortex, nucleus, key, text)
        return _ok(rid, {"status": "woven", "key": key, "links_created": woven})

    def _enqueue_weave(self, session, is_nucleus: bool, key: str, text: str, label: str) -> None:
        """
        Fire-and-forget weave job.  Skipped inside JCL worker threads (pack loading
        uses the batch weaver; per-atom jobs would double-weave and flood the queue).

        Guest sessions lack WRITE capability so the job runs under system.weaver
        (LIBRARIAN role) with _for_client carrying the original session owner so
        the Weaver handler can access the right cortex.
        """
        import threading as _thr
        if _thr.current_thread().name.startswith("JCLWorker"):
            return
        if not (text and self.jcl_worker and JCLJob and JCLStep):
            return
        method = "sys.weaver.weave" if is_nucleus else "sys.weaver.weave_client"
        cid = getattr(session, 'client_id', 'system')
        role = getattr(session, 'role', None)
        is_guest = (role is not None and str(getattr(role, 'value', role)) == "guest")
        jcl_owner = "system.weaver" if is_guest else cid
        params = {"key": key, "text": text}
        if is_guest:
            params["_for_client"] = cid
        self.harmonia.submit_job(JCLJob(
            owner=jcl_owner,
            label=label[:60],
            steps=[JCLStep(method=method, params=params)],
            fail_fast=False,
        ))

    # ------------------------------------------------------------------
    # Unified post-write hook
    # ------------------------------------------------------------------

    def _post_write(self, session, is_nucleus: bool, atom_id: str, text: str,
                    label: str = None) -> None:
        """
        Single entry point called after every Atom write.
        Queues both protoword linking and NLP word decomposition so all paths
        (w / def / al / s.add / onto load / fetch) go through the same pipeline.
        """
        if not text:
            return
        lbl = label or f"sys.weaver:{atom_id[:8]}"
        self._enqueue_weave(session, is_nucleus, atom_id, text, lbl)
        self._enqueue_decompose(session, is_nucleus, atom_id, text)

    def _enqueue_decompose(self, session, is_nucleus: bool, atom_id: str,
                           text: str, label: str = None) -> None:
        """
        Queue a word-decomposition job. Skipped inside JCL worker threads
        and for single-word texts (already atomic — nothing to decompose).

        Guest sessions lack WRITE capability so the job runs under system.weaver
        (LIBRARIAN role) with _for_client carrying the original session owner.
        """
        import threading as _thr
        if _thr.current_thread().name.startswith("JCLWorker"):
            return
        if not (text and self.jcl_worker and JCLJob and JCLStep):
            return
        if len(_tokenize_for_weave(text)) < 2:
            return
        cid    = getattr(session, 'client_id', 'system')
        role   = getattr(session, 'role', None)
        is_guest = (role is not None and str(getattr(role, 'value', role)) == "guest")
        jcl_owner = "system.weaver" if is_guest else cid
        locale = getattr(getattr(session, 'locale', None), 'primary', 'en')
        lbl    = (label or f"decompose:{atom_id[:8]}")[:60]
        params = {"key": atom_id, "text": text, "is_nucleus": is_nucleus, "locale": locale}
        if is_guest:
            params["_for_client"] = cid
        self.harmonia.submit_job(JCLJob(
            owner=jcl_owner,
            label=lbl,
            steps=[JCLStep(method="sys.weaver.decompose", params=params)],
            fail_fast=False,
        ))

    def _nlp_extract_tags(self, text: str, locale: str = "en") -> dict:
        """
        Extract semantic tags from text with graceful multi-tier degradation.

        Tier 3 (NLP): Harmonia nlp.extract plugin (SpaCy-based MultiLocaleNLP).
                      Returns trait:*, chrono:*, and geo:* tags.
        Tier 1 (Basic): _tokenize_for_weave — regex split, stopwords, len≥3.
                        Always available for Latin-script text.
        Tier 0 (CJK):  Character bigrams for CJK text when no model is available.

        Returns dict with keys:
          words   — word tokens to materialise as Atoms in components set
          chrono  — chrono: tags (for chrono:period links)
          geo     — geo: tags (for geo:at links)
          quality — 'nlp' | 'basic'
        """
        import re as _re

        is_cjk = bool(_re.search(r'[぀-鿿가-힯一-鿿]', text))

        # T3 — try registered NLP plugin
        if self.harmonia:
            _plugins = getattr(self.harmonia, '_plugins', {})
            nlp_fn   = _plugins.get("nlp.extract")
            if nlp_fn:
                try:
                    raw    = nlp_fn(text)
                    words  = []
                    chrono = []
                    geo    = []
                    for tag in (raw or []):
                        if tag.startswith("trait:"):
                            words.append(tag[6:])
                        elif tag.startswith("chrono:"):
                            chrono.append(tag)
                        elif tag.startswith("geo:"):
                            geo.append(tag)
                        elif not tag.startswith("sys:"):
                            words.append(tag)
                    if words or chrono or geo:
                        return {"words": words, "chrono": chrono,
                                "geo": geo, "quality": "nlp"}
                except Exception as _e:
                    logger.debug("[Weaver/decompose] NLP plugin failed: %s", _e)

        # T0 — CJK character bigrams when no morphological model
        if is_cjk:
            chars   = [c for c in text
                       if _re.match(r'[぀-鿿가-힯一-鿿]', c)]
            bigrams = [chars[i] + chars[i + 1] for i in range(len(chars) - 1)]
            tokens  = list(dict.fromkeys(bigrams + chars))
            return {"words": tokens, "chrono": [], "geo": [], "quality": "basic"}

        # T1 — basic Latin tokenizer (always available)
        tokens = _tokenize_for_weave(text)
        return {"words": tokens, "chrono": [], "geo": [], "quality": "basic"}

    def _find_or_create_word_atom(self, write_ctx, nucleus, client_id: str,
                                   token: str, is_nucleus: bool):
        """
        Locate an existing Atom for a word token, or create one.
        For nucleus Atoms the protoword (word:{token}) is the canonical word Atom.
        For client Atoms we prefer an existing cortex alias, then nucleus protoword,
        and finally create a new private cortex Atom.
        """
        if is_nucleus and nucleus:
            existing = (nucleus.core.get_key_by_alias(f"word:{token}") or
                        nucleus.core.get_key_by_alias(token))
            if existing:
                return existing

        if hasattr(write_ctx, 'resolve_alias'):
            existing = write_ctx.resolve_alias(token)
            if existing:
                return existing

        if nucleus:
            proto = nucleus.core.get_key_by_alias(f"word:{token}")
            if proto:
                return proto

        try:
            scopes = [] if is_nucleus else [
                f"owner:user_{client_id}",
                f"view:user_{client_id}",
            ]
            word_key = write_ctx.put_chunk(
                content=token,
                meta={"type": "word", "source": "weave_decompose"},
                author=client_id,
                scopes=scopes,
            )
            write_ctx.set_alias(word_key, token)
            return word_key
        except Exception as _e:
            logger.debug("[Decompose] create word atom '%s': %s", token, _e)
            return None

    def _handle_weave_decompose(self, rid, data, session) -> dict:
        """
        sys.weaver.decompose — NLP word decomposition and component set population.

        For each meaningful token extracted from the source Atom's text:
          1. Finds or creates a word Atom in the appropriate context.
          2. Adds the word Atom to components:{key} set of the source Atom.
          3. Weaves protoword links for the word Atom directly (already in JCL
             context, so no secondary JCL job is needed).

        When NLP quality is 'basic', the source Atom is queued in
        weave:pending:{locale} for reprocessing when a full model loads.
        """
        key        = data.get("key", "")
        text       = data.get("text", "")
        is_nucleus = data.get("is_nucleus", False)
        locale     = data.get("locale", "en")

        if not key or not text:
            return _err(rid, -32602, "decompose requires key and text")

        denied = self._weaver_denied(session, data, nucleus_write=bool(is_nucleus))
        if denied:
            return _err(rid, -32003, denied)

        # When running as system.weaver on behalf of a guest, _for_client names
        # the original session so we write to the correct cortex.
        for_client = data.get("_for_client")
        if for_client:
            _target = self.manager.get_session(for_client)
            nucleus = getattr(_target, 'nucleus', None)
            cortex  = getattr(_target, 'local_cortex',
                              getattr(_target, 'cortex', None))
            cid     = for_client
        else:
            nucleus = getattr(session, 'nucleus', None)
            cortex  = getattr(session, 'local_cortex',
                              getattr(session, 'cortex', None))
            cid     = getattr(session, 'client_id', 'system')
        write_ctx = nucleus if is_nucleus else cortex
        if not write_ctx:
            return _ok(rid, {"status": "skipped", "reason": "no write context"})

        result  = self._nlp_extract_tags(text, locale)
        words   = result["words"]
        chrono  = result["chrono"]
        geo     = result["geo"]
        quality = result["quality"]

        if not (words or chrono or geo):
            return _ok(rid, {"status": "skipped", "reason": "no tokens extracted"})

        component_set = f"components:{key}"
        created = 0

        for token in words:
            word_key = self._find_or_create_word_atom(
                write_ctx, nucleus, cid, token, is_nucleus)
            if not word_key or word_key == key:
                continue
            try:
                write_ctx.add_to_set(component_set, word_key)
            except Exception as _e:
                logger.debug("[Decompose] add_to_set '%s': %s", token, _e)
                continue
            # Weave protoword links for the word Atom directly — we are already
            # inside a JCL worker thread, so _enqueue_weave would no-op here.
            try:
                if is_nucleus and nucleus:
                    self._weave_atom(nucleus, word_key, token)
                elif cortex and nucleus:
                    self._weave_client_atom(cortex, nucleus, word_key, token)
            except Exception as _e:
                logger.debug("[Decompose] weave word atom '%s': %s", token, _e)
            created += 1

        # Create chrono:period and geo:at links for semantic tags produced by NLP
        tag_links = (
            [(t, "chrono:period") for t in chrono] +
            [(t, "geo:at") for t in geo]
        )
        for tag, rel in tag_links:
            try:
                tag_key = write_ctx.resolve_alias(tag) if hasattr(write_ctx, 'resolve_alias') else None
                if not tag_key:
                    tag_key = write_ctx.put_chunk(
                        content=tag,
                        meta={"type": "tag", "role": rel},
                        author=cid,
                    )
                    if hasattr(write_ctx, 'set_alias'):
                        write_ctx.set_alias(tag_key, tag)
                write_ctx.put_link(key, tag_key, rel, author=cid)
                created += 1
            except Exception as _e:
                logger.debug("[Decompose] tag link '%s' → '%s': %s", tag, rel, _e)

        pending_set = f"weave:pending:{locale}"
        if quality == "basic":
            try:
                write_ctx.add_to_set(pending_set, key)
            except Exception:
                pass
        else:
            try:
                write_ctx.remove_from_set(pending_set, key)
            except Exception:
                pass

        return _ok(rid, {"status": "ok", "key": key,
                         "components": created, "quality": quality})

    def _handle_weave_drain_pending(self, rid, data, session) -> dict:
        """
        sys.weaver.drain_pending — reprocess atoms in weave:pending:{locale}
        after a full NLP model has become available.
        """
        locale  = data.get("locale", "en")
        nucleus = getattr(session, 'nucleus', None)
        cortex  = getattr(session, 'local_cortex',
                          getattr(session, 'cortex', None))
        pending_set = f"weave:pending:{locale}"
        processed = 0
        remaining = 0

        for ctx_label, ctx_obj in [("nucleus", nucleus), ("cortex", cortex)]:
            if not ctx_obj:
                continue
            try:
                members = ctx_obj.list_set(pending_set) or []
            except Exception:
                continue
            for member in members:
                atom_key = member.get("key", "")
                if not atom_key:
                    continue
                try:
                    raw = (ctx_obj.get_chunk_raw(atom_key)
                           if hasattr(ctx_obj, 'get_chunk_raw') else None)
                    if not raw:
                        continue
                    text = (raw.get("content", "")
                            if isinstance(raw, dict) else str(raw))
                    _result = self._nlp_extract_tags(text, locale)
                    if _result["quality"] == "nlp":
                        is_nucleus = (ctx_label == "nucleus")
                        self._handle_weave_decompose(rid, {
                            "key": atom_key, "text": text,
                            "is_nucleus": is_nucleus, "locale": locale,
                        }, session)
                        processed += 1
                    else:
                        remaining += 1
                except Exception as _e:
                    logger.debug("[DrainPending] %s: %s", atom_key, _e)

        return _ok(rid, {"locale": locale,
                         "processed": processed, "remaining": remaining})

    def _member_group_engines(self, session, scopes):
        """(gid, engine) for each group the caller is a scoped member of.

        Read / navigation handlers use this to surface atoms shared into the
        caller's groups — the same associative reach a member has via `look`.
        Other members' PRIVATE atoms never live in the group space (they carry
        owner:/view: scopes, not scope:group_<gid>), so scope does the
        black-holing automatically: a member sees the shared graph but not each
        other's private cortex."""
        out = []
        for gid, ge in getattr(session, 'group_engines', {}).items():
            if f"scope:group_{gid}" in scopes:
                out.append((gid, ge))
        return out

    def _handle_read(self, rid, data, session, ctx, scopes, history) -> dict:
        target = data.get("id") or data.get("target", "")
        if not target:
            target = session.last_written_id or ""
        if not target:
            return _err(rid, -32602, "read requires 'id' or an active session context")

        resolved = self._resolve_target(target, session, history) or target
        # Scoped read only.  get_scoped_chunk applies check_access and returns
        # None on BOTH "denied" and "not found" — we must NOT fall back to an
        # unscoped get_chunk(), which would leak atoms outside the caller's
        # scope (including nucleus-resident collective/DNA/admin atoms).
        content = ctx.get_scoped_chunk(resolved, scopes)
        if content is None:
            # Group-space fallback: an atom shared into one of the caller's groups
            # lives in that group's engine, not the local cortex. Membership is
            # proven two ways before revealing it: scope:group_<gid> is in the
            # caller's scopes AND the atom carries that group's scope
            # (ge.check_access) — mirrors the consciousness/view fallback so `r` is
            # consistent with `look`. Link-graph traversal is not attempted for a
            # group atom here; `look` gives the full associative view.
            for gid, ge in self._member_group_engines(session, scopes):
                if not ge.check_access(resolved):
                    continue
                gc = ge.get_chunk(resolved)
                if gc is None:
                    continue
                grow = ge.get_chunk_raw(resolved) or {}
                try:
                    import json as _json
                    gmeta = _json.loads(grow.get("meta") or "{}")
                except Exception:
                    gmeta = {}
                return _ok(rid, {
                    "key":       resolved,
                    "content":   gc,
                    "meta":      gmeta,
                    "aliases":   ge.get_aliases_by_key(resolved),
                    "out_links": [],
                    "in_links":  [],
                    "sets":      ge.core.get_collections_for_key(resolved),
                    "shared_from": f"group:{gid}",
                })
            return _err(rid, -32002, f"Atom not found or out of scope: '{target}'")

        nucleus = getattr(session, 'nucleus', None)
        focus   = self._get_display_focus(session)
        if focus and not self._passes_display_focus(resolved, focus, ctx, nucleus):
            return _err(rid, -32002, f"Atom not in current focus: '{target}'")

        meta    = ctx.get_meta(resolved)
        aliases = ctx.get_aliases_by_key(resolved)

        # Build link list with previews for display.  A neighbour's content and
        # aliases are only revealed if the caller may actually see that neighbour;
        # out-of-scope endpoints show the edge but redact the payload so links
        # cannot be used to enumerate private/nucleus atoms.
        _rel_desc_cache: dict = {}
        def _rd(rel: str):
            # First-class relation: the reldef:<rel> full-spelling, memoised per rel.
            if rel not in _rel_desc_cache:
                _rel_desc_cache[rel] = lexicon.rel_description(ctx, rel)
            return _rel_desc_cache[rel]

        def _link_entry(key: str, rel: str, direction: str) -> dict:
            rd = _rd(rel)
            if not ctx.check_access(key, scopes):
                entry = {
                    "key":       key,
                    "rel":       rel,
                    "direction": direction,
                    "aliases":   [],
                    "preview":   "",
                    "restricted": True,
                }
                if rd: entry["rel_desc"] = rd
                return entry
            preview = ctx.get_chunk(key) or ""
            entry = {
                "key":       key,
                "rel":       rel,
                "direction": direction,
                "aliases":   ctx.get_aliases_by_key(key),
                "preview":   preview[:60],
            }
            if rd: entry["rel_desc"] = rd
            return entry

        out_links = [_link_entry(dst, rel, "out")
                     for dst, rel in ctx.get_adjacent_links(resolved)
                     if not focus or self._passes_display_focus(dst, focus, ctx, nucleus)]
        in_links  = [_link_entry(src, rel, "in")
                     for src, rel in ctx.get_incoming_links(resolved)
                     if not focus or self._passes_display_focus(src, focus, ctx, nucleus)]

        # Set membership: which collections contain this atom
        sets: list = ctx.core.get_collections_for_key(resolved)
        if not sets and nucleus:
            sets = nucleus.core.get_collections_for_key(resolved)

        # First-class namespace: plain-language gloss of the atom's namespace prefix.
        ns_desc = lexicon.namespace_description(
            ctx, lexicon.namespace_of_alias(aliases[0] if aliases else None))

        result = {
            "key":      resolved,
            "content":  content,
            "meta":     meta,
            "aliases":  aliases,
            "out_links": out_links,
            "in_links":  in_links,
            "sets":     sets,
        }
        if ns_desc:
            result["namespace_desc"] = ns_desc
        return _ok(rid, result)

    def _handle_drop(self, rid, data, session, ctx, scopes) -> dict:
        target = data.get("id") or data.get("target", "")
        if not target:
            return _err(rid, -32602, "drop requires 'id'")

        history = ctx.stream(10)
        resolved = self._resolve_target(target, session, history) or target

        result = ctx.drop_chunk(resolved, requester_scopes=scopes)
        if "error" in result:
            return _err(rid, -32001, result["error"])

        return _ok(rid, result)

    def _handle_link(self, rid, data, session, ctx, client_id) -> dict:
        src = data.get("src", "")
        dst = data.get("dst", "")
        rel = data.get("rel", "sys:associated_with")
        w   = float(data.get("w", 1.0))

        if not src or not dst:
            return _err(rid, -32602, "link requires 'src' and 'dst'")

        # "=" prefix on src/dst opts into strict alias resolution: the link
        # dangles permanently if the target is not registered, rather than
        # falling back to the bare-segment proto-word (the default behaviour).
        # Used when two namespace atoms are intentionally distinct senses
        # and the link must target the specific sense, not the shared proto-word.
        src_strict = src.startswith("=")
        if src_strict:
            src = src[1:]
        dst_strict = dst.startswith("=")
        if dst_strict:
            dst = dst[1:]

        # Normalize bare-word relations to proper semantic namespace at write-time.
        # Known types remap to their canonical ns (antonym→sys:antonym, evoked_by→emo:, …).
        # All other bare words default to calc: (general conceptual vocabulary).
        if rel and ':' not in rel and not rel.startswith('@'):
            from lib.akasha.composite import _BARE_REL_REMAP
            rel = _BARE_REL_REMAP.get(rel, f"calc:{rel}")

        _src_alias_resolved = ctx.resolve_alias(src)
        src_key = _src_alias_resolved or src
        _dst_alias_resolved = ctx.resolve_alias(dst)
        dst_key = _dst_alias_resolved or dst

        # ctx.put_link routes to the correct store when ctx is _NucleusWriteCtx.
        # For local_cortex ctx: if the src atom lives in nucleus, write the link
        # there so it is visible to all cells (not buried in one cell's DB).
        # When ctx is _NucleusWriteCtx, resolve_alias already preferred nucleus
        # keys, so no extra alias lookup is needed.
        nucleus = getattr(session, 'nucleus', None)
        # A 64-char hex value is a raw atom key ($var.key expansions, or the
        # canon normalizer's proto-word roll-up which targets an exact key to
        # avoid alias ambiguity) — never a proto-word to mint. Guard both write
        # branches so a raw key is used verbatim, not content-addressed into a
        # new atom whose text is the hash string.
        _is_hex = lambda v: len(v) == 64 and all(c in '0123456789abcdef' for c in v)
        if isinstance(ctx, _NucleusWriteCtx):
            # Late-binding: auto-create proto-words for any unresolved alias.
            # Using the bare segment (last ':'-delimited token) as the universal
            # anchor means ordering and repeated execution are both irrelevant.
            # When the qualified atom is later defined, it links back to the
            # same proto-word via 'specializes', making the graph path traversable.
            if _src_alias_resolved is None and not _is_hex(src):
                bare_src = src.rsplit(":", 1)[-1] if ":" in src else src
                src_key = nucleus._ensure_protoword(bare_src)
            if _dst_alias_resolved is None and not _is_hex(dst):
                bare_dst = dst.rsplit(":", 1)[-1] if ":" in dst else dst
                dst_key = nucleus._ensure_protoword(bare_dst)
            ctx.put_link(src_key, dst_key, rel, w=w, author=client_id)
        else:
            # Prefer nucleus alias resolution over ctx for local_cortex case:
            # the local cortex may hold stale aliases whose keys are absent from
            # nucleus, which would silently route the link to the wrong DB.
            _src_nucleus_key = nucleus.core.get_key_by_alias(src) if nucleus else None
            if _src_nucleus_key:
                src_key = _src_nucleus_key
            _dst_nucleus_key = nucleus.core.get_key_by_alias(dst) if nucleus else None
            if _dst_nucleus_key:
                dst_key = _dst_nucleus_key
            # Proto-word fallback for unresolved alias strings (default behaviour).
            # Skipped when "=" strict prefix is set, or for raw hex key values
            # ($var.key expansions are 64-char all-hex strings).
            _is_hex = lambda v: len(v) == 64 and all(c in '0123456789abcdef' for c in v)
            if not src_strict and nucleus and \
                    _src_alias_resolved is None and _src_nucleus_key is None and not _is_hex(src):
                bare_src = src.rsplit(":", 1)[-1] if ":" in src else src
                src_key = nucleus._ensure_protoword(bare_src)
            if not dst_strict and nucleus and \
                    _dst_alias_resolved is None and _dst_nucleus_key is None and not _is_hex(dst):
                bare_dst = dst.rsplit(":", 1)[-1] if ":" in dst else dst
                dst_key = nucleus._ensure_protoword(bare_dst)
            if nucleus and nucleus.core.get_chunk_raw(src_key):
                nucleus.put_link(src_key, dst_key, rel, w=w, author=client_id)
            else:
                ctx.put_link(src_key, dst_key, rel, w=w, author=client_id)
        return _ok(rid, {"status": "linked", "src": src_key, "dst": dst_key, "rel": rel, "w": w})

    def _handle_link_list(self, rid, data, ctx, scopes) -> dict:
        target = data.get("id", "")
        if not target:
            return _err(rid, -32602, "link.list requires 'id'")
        resolved = ctx.resolve_alias(target) or target
        # get_magnetic_neighborhood returns List[Dict] with "direction","rel","key","w"
        # (get_adjacent_links returns List[List] which the renderer cannot use)
        links = ctx.get_magnetic_neighborhood(resolved)
        window, page = _paginate(links, data.get("limit"), data.get("cursor"),
                                 default=0, max_limit=500)   # default: whole list (link.list is literal)
        return _ok(rid, {"key": resolved, "links": window, "count": len(window), "page": page})

    def _handle_link_reinforce(self, rid, data, ctx, client_id) -> dict:
        src = data.get("src", "")
        dst = data.get("dst", "")
        rel = data.get("rel", "sys:associated_with")
        delta = float(data.get("delta", 0.1))
        if not src or not dst:
            return _err(rid, -32602, "link.reinforce requires 'src' and 'dst'")
        if rel and ':' not in rel and not rel.startswith('@'):
            from lib.akasha.composite import _BARE_REL_REMAP
            rel = _BARE_REL_REMAP.get(rel, f"calc:{rel}")
        src_key = ctx.resolve_alias(src) or src
        dst_key = ctx.resolve_alias(dst) or dst
        new_w = ctx.reinforce_link(src_key, dst_key, rel, delta_w=delta, author=client_id)
        return _ok(rid, {"status": "reinforced", "src": src_key, "dst": dst_key, "rel": rel, "w": new_w})

    def _handle_link_rm(self, rid, data, session, ctx) -> dict:
        src = data.get("src", "")
        dst = data.get("dst", "")
        rel = data.get("rel", "")
        if not src or not dst or not rel:
            return _err(rid, -32602, "ln.rm requires 'src', 'dst', and 'rel'")
        history = getattr(session, 'last_written_ids', [])
        src_key = self._resolve_target(src, session, history) or ctx.resolve_alias(src) or src
        dst_key = self._resolve_target(dst, session, history) or ctx.resolve_alias(dst) or dst
        ctx.remove_link(src_key, dst_key, rel)
        return _ok(rid, {"status": "removed", "src": src_key, "dst": dst_key, "rel": rel})

    def _handle_meta_set(self, rid, data, ctx) -> dict:
        target = data.get("id", "")
        key = data.get("key", "")
        value = data.get("value")
        if not target or not key:
            return _err(rid, -32602, "meta.set requires 'id' and 'key'")
        resolved = ctx.resolve_alias(target) or target
        result = ctx.set_meta(resolved, key, value)
        return _ok(rid, result)

    # ------------------------------------------------------------------
    # Alias handlers
    # ------------------------------------------------------------------

    def _handle_alias(self, rid, data, session, ctx, history) -> dict:
        target = data.get("id", "")
        name = data.get("name", "")
        if not target or not name:
            return _err(rid, -32602, "alias requires 'id' and 'name'")
        resolved = self._resolve_target(target, session, history) or ctx.resolve_alias(target) or target
        # If target lives in nucleus, register the alias there (with proto-word creation).
        # force=True: explicit management command — intentional rebind, bypasses first-wins.
        nucleus = getattr(session, 'nucleus', None)
        _in_nucleus = bool(nucleus and nucleus.core.get_chunk_raw(resolved))
        # Reject aliasing a target that names no stored atom. Without this guard an
        # unresolved `target` falls through to the raw string above and a DANGLING
        # alias is bound (key column holds a literal like "place:france" with no atom
        # body). That dangling alias then SHADOWS the real nucleus atom of the same
        # name on every later read — a silent trap (`al place:france france` before
        # place:france exists locks the user out of the shared `france` atom). A valid
        # target has a body in the local cortex, the nucleus, or a visible group space.
        #
        # ⚠️ EXEMPT explicit 64-hex content-addresses (F6). A `write`→`alias` pair (the
        # global-relations phase COMPLETION SENTINEL is exactly this) aliases the key the
        # write just returned; that key is a legitimate content-address even when the
        # cross-context get_chunk_raw here cannot see it (separate re-authenticated JCL
        # step contexts / an async commit). Rejecting it made the sentinel alias fail →
        # the sentinel never landed → the relations phase REPLAYED on every boot → RSS
        # climbed into the OOM ceiling and the daemon was killed. Only NON-hash raw
        # strings (the true dangling-alias case) are rejected.
        _is_hexkey = (len(resolved) == 64
                      and all(c in "0123456789abcdef" for c in resolved.lower()))
        if not _is_hexkey and not _in_nucleus and not ctx.core.get_chunk_raw(resolved):
            _scopes = getattr(session, "active_scopes", None) or []
            _in_group = any(
                ge.check_access(resolved) and ge.get_chunk_raw(resolved)
                for _gid, ge in self._member_group_engines(session, _scopes)
            )
            if not _in_group:
                return _err(rid, -32602,
                            f"cannot alias '{target}': no such atom — write or define it first")
        if _in_nucleus:
            result = nucleus.set_alias(resolved, name, force=True)
        else:
            result = ctx.set_alias(resolved, name, force=True)
        # Weave alias label words → protoword links so alias names enrich graph connectivity
        self._post_write(session, _in_nucleus, resolved, name, f"sys.weaver:al:{name[:30]}")
        return _ok(rid, result)

    def _handle_alias_rm(self, rid, data, session, ctx) -> dict:
        alias = (data.get("name") or data.get("alias") or "").strip()
        if not alias:
            return _err(rid, -32602, "al.rm requires 'name'")
        nucleus = getattr(session, 'nucleus', None)
        if nucleus and nucleus.resolve_alias(alias):
            nucleus.core.delete_alias(alias)
        else:
            ctx.delete_alias(alias)
        return _ok(rid, {"status": "removed", "alias": alias})

    # ------------------------------------------------------------------
    # Ontology dump & collision report
    # ------------------------------------------------------------------

    def _handle_onto_dump(self, rid, data, ctx) -> dict:
        """
        Flexible ontology dump.
        mode: atoms (default) | links | antonyms | aliases | sets | namespaces
        sort: alpha (default) | count | recent
        ns:         namespace prefix filter, e.g. "word:en"
        rel:        relation type filter for links mode, e.g. "sys:antonym"
        collection: collection name for sets mode
        limit:      max items returned (default 500, max 5000)
        pattern:    alias LIKE pattern for aliases mode
        """
        mode    = (data.get("mode") or "atoms").lower()
        sort    = (data.get("sort") or "alpha").lower()
        ns      = (data.get("ns") or "").rstrip(":")
        rel_f   = (data.get("rel") or "")
        coll    = (data.get("collection") or "")
        pattern = (data.get("pattern") or "")
        cursor  = data.get("cursor")
        # Cursor pagination over the FULL sorted result — so pages are consistent, the
        # list must be built and sorted whole before slicing. For the unbounded modes
        # (links, atoms) `scan` bounds that universe (admin may raise it); the page
        # envelope's `total` is the size within the scanned universe.
        scan    = min(int(data.get("scan") or 20000), 100000)

        def _page(items):
            window, page = _paginate(items, data.get("limit"), cursor,
                                     default=500, max_limit=5000)
            return window, page

        def _best_alias(key: str) -> str:
            als = ctx.core.get_aliases_by_key(key)
            if not als:
                _nuc = getattr(ctx, '_nucleus', None)
                if _nuc:
                    als = _nuc.core.get_aliases_by_key(key)
            if not als:
                return key[:16]
            return min(als, key=lambda a: (a.count(":"), len(a)))

        if mode == "namespaces":
            depth = int(data.get("depth") or 1)
            items = ctx.core.get_namespace_counts(depth=depth)
            _nuc = getattr(ctx, '_nucleus', None)
            if _nuc:
                nuc_items = _nuc.core.get_namespace_counts(depth=depth)
                local_ns = {i["ns"]: i for i in items}
                for ni in nuc_items:
                    ns_key = ni["ns"]
                    if ns_key in local_ns:
                        local_ns[ns_key]["count"] += ni["count"]
                    else:
                        items.append(ni)
                        local_ns[ns_key] = ni
            if sort == "alpha":
                items.sort(key=lambda x: x["ns"])
            window, page = _page(items)
            return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})

        if mode in ("links", "antonyms"):
            effective_rel = "sys:antonym" if mode == "antonyms" else rel_f
            rows = ctx.core.get_all_links(rel_filter=effective_rel or None, limit=scan)
            items = []
            for r in rows:
                src_a = _best_alias(r["src"])
                dst_a = _best_alias(r["dst"])
                items.append({"src": src_a, "dst": dst_a, "rel": r["rel"], "w": r["w"]})
            if sort == "alpha":
                items.sort(key=lambda x: (x["rel"], x["src"]))
            window, page = _page(items)
            return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})

        if mode == "sets":
            name = coll or "ontology.narrative_typology"
            keys = ctx.get_collection_members(name)
            items = []
            for k in keys:
                main = _best_alias(k)
                items.append({"alias": main, "key": k[:12]})
            if sort == "alpha":
                items.sort(key=lambda x: x["alias"])
            elif sort == "count":
                pass  # no count available per-member
            window, page = _page(items)
            return _ok(rid, {"mode": mode, "collection": name, "count": len(window),
                             "items": window, "page": page})

        if mode == "aliases":
            pat = pattern or (f"{ns}:%" if ns else "%")
            rows = ctx.core.get_aliases_by_pattern(pat)
            items = [{"alias": r["alias"], "key": r["key"][:12]} for r in rows]
            if sort == "alpha":
                items.sort(key=lambda x: x["alias"])
            window, page = _page(items)
            return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})

        # default: atoms — one row per distinct atom key, primary alias + content preview.
        # Composed from ISA primitives (alias pattern match + per-key content) rather
        # than a relational JOIN, so it holds on non-SQL backends too.
        pat = f"{ns}:%" if ns else "%:%"
        alias_rows = list(ctx.core.get_aliases_by_pattern(pat))
        _nucleus = getattr(ctx, '_nucleus', None)
        if _nucleus:
            alias_rows += list(_nucleus.core.get_aliases_by_pattern(pat))
        seen: set = set()
        items = []
        for r in alias_rows[:scan]:
            key = r["key"]
            if key in seen:
                continue
            seen.add(key)
            row = ctx.core.get_chunk_raw(key)
            if row is None and _nucleus:
                row = _nucleus.core.get_chunk_raw(key)
            preview = ((row["content"] if row else "") or "")[:100].replace("\n", " ")
            items.append({"alias": r["alias"], "key": key[:12], "preview": preview})
        items.sort(key=lambda x: x["alias"])
        window, page = _page(items)
        return _ok(rid, {"mode": mode, "count": len(window), "items": window, "page": page})

    # ------------------------------------------------------------------
    # Ontology export  (DB → .ak files)
    # ------------------------------------------------------------------

    def _handle_onto_export(self, rid, data, ctx) -> dict:
        """
        Export ontology atoms to .ak files in out/ (or a specified directory).

        Params
        ------
        ns         : namespace prefix, e.g. "myth" — exports all myth:* atoms.
                     May be a comma-separated list: "myth,deity,era".
                     Omit (or "*") to export everything.
        collection : set name filter, e.g. "ontology.narrative_genres".
                     When given, only atoms that belong to this collection
                     are exported (AND-ed with ns if both are supplied).
        era        : era alias filter, e.g. "ancient".  Only atoms that carry
                     the link  ln X era:<era> sys:part_of  are included.
        out        : output directory, relative to project root (default: out/).
        split      : "ns" (one file per namespace, default)
                   | "single" (one file, filename = ns or "export")
                   | "set"    (one file per collection the atoms belong to)
        """
        import os, re, textwrap

        core = ctx.core

        # ── resolve project root ──────────────────────────────────────
        _kdir  = os.path.dirname(os.path.abspath(__file__))  # lib/akasha/
        _ldir  = os.path.dirname(_kdir)                       # lib/
        _proot = os.path.dirname(_ldir)                       # project root

        out_base = os.path.join(_proot, (data.get("out") or "out").strip("/"))
        os.makedirs(out_base, exist_ok=True)

        split = (data.get("split") or "ns").lower()

        # ── build namespace list ──────────────────────────────────────
        ns_raw = (data.get("ns") or "").strip()
        if ns_raw in ("", "*"):
            ns_list = []            # no ns filter
        else:
            ns_list = [n.strip().rstrip(":") for n in ns_raw.split(",") if n.strip()]

        coll_filter = (data.get("collection") or "").strip()
        era_filter  = (data.get("era") or "").strip().lstrip("era:")

        # ── collect candidate keys ────────────────────────────────────
        def _primary_alias(key: str) -> str:
            als = core.get_aliases_by_key(key)
            if not als:
                return ""
            return min(als, key=lambda a: (a.count(":"), len(a)))

        def _aliases_for_ns(ns: str):
            """Return {key: primary_alias} for all atoms in namespace ns."""
            rows = core.get_aliases_by_pattern(f"{ns}:%")
            seen = {}
            for r in rows:
                k = r["key"]
                if k in seen:
                    continue
                a = r["alias"]
                # keep the primary (shortest / fewest colons)
                if k not in seen or (a.count(":"), len(a)) < (seen[k].count(":"), len(seen[k])):
                    seen[k] = a
            return seen  # {key: alias}

        # gather all candidate keys → {key: primary_alias}
        if ns_list:
            candidates = {}
            for ns in ns_list:
                candidates.update(_aliases_for_ns(ns))
        else:
            # all aliases in DB
            rows = core.get_aliases_by_pattern("%:%")
            candidates = {}
            for r in rows:
                k = r["key"]
                a = r["alias"]
                if k not in candidates or (a.count(":"), len(a)) < \
                        (candidates[k].count(":"), len(candidates[k])):
                    candidates[k] = a

        # ── apply collection filter ───────────────────────────────────
        if coll_filter:
            coll_keys = set(core.get_collection_members(coll_filter))
            candidates = {k: v for k, v in candidates.items() if k in coll_keys}

        # ── apply era filter ─────────────────────────────────────────
        if era_filter:
            era_alias = f"era:{era_filter}"
            era_key   = core.get_key_by_alias(era_alias)
            if era_key:
                era_keys = {
                    lk["src"]
                    for lk in core.get_incoming_links(era_key, rel_pattern="sys:part_of")
                }
                candidates = {k: v for k, v in candidates.items() if k in era_keys}

        if not candidates:
            return _ok(rid, {"exported": 0, "files": [], "note": "no atoms matched filters"})

        # ── build atom blocks ─────────────────────────────────────────
        def _escape(s: str) -> str:
            return s.replace('\\', '\\\\').replace('"', '\\"')

        def _atom_block(key: str, alias: str) -> str:
            """Return the .ak text block for one atom."""
            raw = core.get_chunk_raw(key)
            content = (raw.get("content") or "") if raw else ""
            lines = [f'def "{alias}" "{_escape(content)}"']

            # outgoing links
            for lk in core.get_adjacent_links(key):
                dst_alias = _primary_alias(lk["dst"])
                if not dst_alias:
                    continue
                rel = lk["rel"]
                lines.append(f"ln {alias} {dst_alias} {rel}")

            # collection memberships
            for cname in sorted(core.get_collections_for_key(key)):
                lines.append(f'set.add name="{cname}" id="{alias}"')

            return "\n".join(lines)

        # ── group by split mode ───────────────────────────────────────
        # groups: {filename_stem: [(key, alias), ...]}
        groups: dict = {}

        if split == "set":
            # group by the first ontology.* collection the atom belongs to
            for key, alias in candidates.items():
                colls = [c for c in core.get_collections_for_key(key)
                         if c.startswith("ontology.")]
                stem = colls[0] if colls else "misc"
                groups.setdefault(stem, []).append((key, alias))
        elif split == "single":
            stem = (coll_filter or (ns_list[0] if ns_list else "export"))
            stem = re.sub(r"[^\w.\-]", "_", stem)
            groups[stem] = list(candidates.items())
        else:  # "ns" (default)
            for key, alias in candidates.items():
                stem = alias.split(":")[0] if ":" in alias else "misc"
                groups.setdefault(stem, []).append((key, alias))

        # ── write files ───────────────────────────────────────────────
        written_files = []
        total_atoms   = 0

        for stem, pairs in sorted(groups.items()):
            pairs.sort(key=lambda p: p[1])          # alpha by alias
            filename = re.sub(r"[^\w.\-]", "_", stem) + ".ak"
            filepath = os.path.join(out_base, filename)

            header = (
                f"# Akasha ontology export — {stem}\n"
                f"# atoms: {len(pairs)}"
                + (f"  ns: {ns_raw}" if ns_raw else "")
                + (f"  collection: {coll_filter}" if coll_filter else "")
                + (f"  era: {era_filter}" if era_filter else "")
                + "\n#\n"
            )

            blocks = [header]
            for key, alias in pairs:
                blocks.append(_atom_block(key, alias))
                blocks.append("")   # blank line separator

            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write("\n".join(blocks))

            written_files.append({"file": os.path.relpath(filepath, _proot),
                                   "atoms": len(pairs)})
            total_atoms += len(pairs)

        return _ok(rid, {
            "exported": total_atoms,
            "files":    written_files,
            "out_dir":  os.path.relpath(out_base, _proot),
        })

    # ------------------------------------------------------------------
    # Ontology reload / reset
    # ------------------------------------------------------------------

    def _handle_onto_reload(self, rid, data, session, scopes) -> dict:
        """
        Remove ontology sentinels and re-trigger _boot_load_ontology.
        Existing atoms are idempotent (re-written but unchanged). New or
        modified .ak/.csl/curation files will be picked up.
        Requires role:librarian.
        """
        if "role:librarian" not in scopes:
            return _err(rid, -32601, "onto.reload requires role:librarian")

        confirm = (data.get("confirm") or "").strip()
        if confirm != "RELOAD":
            return _err(rid, -32602,
                "⚠️  This will clear all ontology load sentinels and re-trigger a full boot load.\n"
                "Modified .ak / .csl / curation files will be picked up on next scan.\n"
                "Existing atoms are re-written idempotently (no data loss).\n\n"
                "To proceed: onto.reload confirm=\"RELOAD\"")

        nucleus = getattr(session, 'nucleus', None)
        if not nucleus:
            return _err(rid, -32001, "No nucleus available for this session")

        _PREFIXES = [
            "ont:ak:f:",            # ⚠️ per-file atom sentinel — MUST be cleared or the re-load is
                                    # a silent no-op. Phase 1 skips any file whose ont:ak:f:* alias
                                    # is still present (kernel.py ~1052), so leaving these behind
                                    # means the pack re-enters but re-writes NO atoms — the exact
                                    # failure that left recipe-content chunks empty and un-healable
                                    # by onto.reload (docs/handoff/recipe-body-empty-content-chunk.md).
            "ont:ak:atoms:loaded:",
            "ont:ak:loaded:",
            "ont:csl:loaded:",
            "ont:curation:loaded:",
        ]
        removed = []
        for prefix in _PREFIXES:
            rows = nucleus.core.get_aliases_by_pattern(prefix) or []
            for row in rows:
                alias = row["alias"] if isinstance(row, dict) else row
                nucleus.core.delete_alias(alias)
                removed.append(alias)

        # Also remove filesystem sentinel files so _boot_load_ontology re-runs fully.
        import glob as _glob
        _sent_dir = os.path.join(self.base_dir, "central", "sentinels")
        _removed_files = 0
        for _sf in _glob.glob(os.path.join(_sent_dir, "*.done")):
            try:
                os.remove(_sf)
                _removed_files += 1
            except OSError:
                pass

        import threading as _thr
        _thr.Thread(target=self._boot_load_ontology, daemon=True,
                    name="ontology-reload").start()

        return _ok(rid, {
            "status": "reload_triggered",
            "sentinels_cleared": removed,
            "sentinel_files_removed": _removed_files,
            "message": "Ontology reload started in background.",
        })

    def _pack_def_keys(self, session, pack_name: str):
        """The atom keys a pack's .ak files currently define — parse each `def <name>` and
        resolve the name to its (loaded) nucleus key. Requires the pack to be loaded (aliases
        resolvable). Returns (keys:set, names:list)."""
        import shlex as _shlex
        _kernel_dir  = os.path.dirname(os.path.abspath(__file__))
        _project_dir = os.path.dirname(os.path.dirname(_kernel_dir))
        pack_dir = os.path.join(_project_dir, "ontology", pack_name)
        keys, names = set(), []
        if not os.path.isdir(pack_dir):
            return keys, names
        nucleus = getattr(session, "nucleus", None)
        resolver = nucleus if nucleus else session.local_cortex
        for _root, _dirs, _files in os.walk(pack_dir):
            for fn in sorted(_files):
                if not fn.endswith(".ak"):
                    continue
                try:
                    with open(os.path.join(_root, fn), encoding="utf-8", errors="ignore") as _f:
                        for raw in _f:
                            line = raw.strip()
                            if not line or line[:4].lower() != "def ":
                                continue
                            try:
                                parts = _shlex.split(line)
                            except ValueError:
                                continue
                            if len(parts) >= 2 and parts[1]:
                                names.append(parts[1])
                                k = resolver.resolve_alias(parts[1])
                                if k:
                                    keys.add(k)
                except Exception:
                    pass
        return keys, names

    def _active_reconcile_packs(self, session, explicit: str = ""):
        """Packs to reconcile: an explicit `pack=` if given, else every pack that already has a
        member-ledger (`ont:pack:members:<name>`) — i.e. one we have tracked on a prior load."""
        if explicit:
            return [explicit]
        nucleus = getattr(session, "nucleus", None)
        core = nucleus.core if nucleus else session.local_cortex.core
        out = []
        try:
            for nm in (core.get_distinct_collection_names("ont:pack:members:") or []):
                p = nm[len("ont:pack:members:"):]
                if p:
                    out.append(p)
        except Exception:
            pass
        return sorted(set(out))

    def _handle_onto_reconcile(self, rid, data, session, scopes) -> dict:
        """[onto.reconcile] Retire ontology atoms a pack no longer contributes — the data-side
        analog of the seed code prune. Fenced to provenance=ontology + no user scope + cross-pack
        ref-count; soft-evict (recoverable) by default. `dry=yes` (default) reports without
        mutating; `apply=yes` retires; `compact=yes` (superuser) hard-drops evicted orphans.
        Requires role:librarian. Spec: docs/for-llm/ontology-reconciliation-spec.md."""
        if "role:librarian" not in scopes:
            return _err(rid, -32601, "onto.reconcile requires role:librarian")
        nucleus = getattr(session, "nucleus", None)
        if not nucleus:
            return _err(rid, -32001, "No nucleus available for this session")
        from lib.akasha.ontology_reconcile import OntologyReconciler
        R = OntologyReconciler(nucleus)

        def _truthy(v):
            return str(v).strip().lower() in ("yes", "true", "1", "on")

        if _truthy(data.get("compact")):
            if "role:superuser" not in scopes and "scope:sys:admin" not in scopes:
                return _err(rid, -32601, "onto.reconcile compact=yes requires role:superuser")
            res = R.compact(scopes)
            return _ok(rid, {"status": "compacted", "dropped_count": len(res.get("dropped", [])),
                             "dropped": res.get("dropped", [])[:50]})

        apply = _truthy(data.get("apply"))
        dry = not apply
        pack = (data.get("pack") or "").strip()
        packs = self._active_reconcile_packs(session, pack)
        reports = []
        for pn in packs:
            keys, names = self._pack_def_keys(session, pn)
            if not names:
                continue                         # pack absent / not loaded → nothing to diff
            R.stamp_provenance(pn, list(keys))
            rep = R.reconcile(pn, keys, dry_run=dry)
            reports.append(rep)
        total_retired = sum(len(r["retired"]) for r in reports)
        total_warn = sum(len(r["user_ref_warnings"]) for r in reports)
        return _ok(rid, {
            "status": "dry_run" if dry else "applied",
            "packs": [r["pack"] for r in reports],
            "retired_total": total_retired,
            "user_ref_warning_total": total_warn,
            "reports": reports,
            "hint": ("Preview only — re-run with apply=yes to retire (soft-evict, recoverable)."
                     if dry else "Retired via soft-evict; re-add the pack to restore."),
        })

    def _handle_onto_reset(self, rid, data, session, scopes) -> dict:
        """
        ⚠️  DANGEROUS ZONE ⚠️

        Hard-reset nucleus: deletes ALL atoms, links, and aliases except the
        35 DNA primal atoms, then re-triggers _boot_load_ontology.
        This CANNOT be undone.

        Required: confirm="RESET"
        Requires role:librarian.
        """
        if "role:librarian" not in scopes:
            return _err(rid, -32601, "onto.reset requires role:librarian")

        confirm = (data.get("confirm") or "").strip()
        if confirm != "RESET":
            return _err(rid, -32602,
                "⚠️  DANGEROUS ZONE ⚠️\n"
                "onto.reset will delete ALL ontology data from nucleus.\n"
                "Only the 35 DNA primal atoms will be preserved.\n"
                "All atoms, links, aliases, namespace_counts, and collections will be erased.\n"
                "This CANNOT be undone.\n\n"
                "To proceed: onto.reset confirm=\"RESET\"")

        nucleus = getattr(session, 'nucleus', None)
        if not nucleus:
            return _err(rid, -32001, "No nucleus available for this session")

        from lib.akasha.dna import get_primal_sequence
        import hashlib as _hl
        dna = get_primal_sequence()
        dna_keys = [_hl.sha256(t.encode("utf-8")).hexdigest() for t in dna.values()]

        nucleus.core.clear_ontology_data(dna_keys)
        nucleus.core._unfold_dna()

        # Remove filesystem sentinel files so the reload starts clean.
        import glob as _glob
        _sent_dir = os.path.join(self.base_dir, "central", "sentinels")
        for _sf in _glob.glob(os.path.join(_sent_dir, "*.done")):
            try:
                os.remove(_sf)
            except OSError:
                pass

        import threading as _thr
        _thr.Thread(target=self._boot_load_ontology, daemon=True,
                    name="ontology-reset-reload").start()

        return _ok(rid, {
            "status": "reset_complete",
            "dna_atoms_preserved": len(dna_keys),
            "message": "Nucleus cleared. DNA atoms restored. Ontology reload started.",
        })

    def _handle_onto_genesis_redo(self, rid, data, session, scopes) -> dict:
        """
        ⚠️  DANGEROUS ZONE ⚠️

        Remove the genesis anchor atoms so genesis_rite can be re-run.
        Ontology data, users, and atoms are NOT affected — only the
        two genesis markers (sys:genesis:anchor / sys:genesis:complete)
        are deleted.  The admin can then run genesis again to rename
        the Akasha instance or correct the initial setup.

        Required: confirm="GENESIS"
        Requires scope:sys:admin.
        """
        if "scope:sys:admin" not in scopes:
            return _err(rid, -32601, "onto.genesis.redo requires admin")

        confirm = (data.get("confirm") or "").strip()
        if confirm != "GENESIS":
            return _err(rid, -32602,
                "⚠️  DANGEROUS ZONE ⚠️\n"
                "onto.genesis.redo will delete the genesis anchor atoms, allowing\n"
                "a fresh genesis_rite to be performed.\n"
                "Ontology data, users, and all other atoms are NOT deleted.\n"
                "The system will be in an uninitialized state until genesis is re-run.\n\n"
                "To proceed: onto.genesis.redo confirm=\"GENESIS\"")

        nucleus = getattr(session, 'nucleus', None)
        if not nucleus:
            return _err(rid, -32001, "No nucleus available for this session")

        removed = []
        for alias in ("sys:genesis:complete", "sys:genesis:anchor"):
            key = nucleus.resolve_alias(alias)
            if key:
                nucleus.core.drop_chunk(key)
                removed.append(alias)

        return _ok(rid, {
            "status": "genesis_reset",
            "removed_anchors": removed,
            "message": "Genesis anchors removed. Run genesis_rite to re-initialize.",
        })

    def _handle_onto_scope_drop(self, rid, data, session, scopes) -> dict:
        """
        ⚠️  DANGEROUS ZONE ⚠️

        Delete all atoms that carry a specific access scope from the nucleus.
        Useful for purging a decommissioned user's contributed atoms, or
        removing all atoms donated under a particular scope.

        Required: confirm="DROP:<scope>"  (scope name embedded in confirm string)
        Requires role:librarian.
        Operates on nucleus only.  Personal cortex atoms are not affected.
        """
        if "role:librarian" not in scopes:
            return _err(rid, -32601, "onto.scope.drop requires role:librarian")

        target_scope = (data.get("scope") or "").strip()
        if not target_scope:
            return _err(rid, -32602, "onto.scope.drop requires 'scope'")

        confirm = (data.get("confirm") or "").strip()
        expected = f"DROP:{target_scope}"
        if confirm != expected:
            return _err(rid, -32602,
                f"⚠️  DANGEROUS ZONE ⚠️\n"
                f"onto.scope.drop will permanently delete ALL nucleus atoms\n"
                f"that carry the scope '{target_scope}'.\n"
                f"This CANNOT be undone.\n\n"
                f"To proceed: onto.scope.drop scope=\"{target_scope}\" confirm=\"{expected}\"")

        nucleus = getattr(session, 'nucleus', None)
        if not nucleus:
            return _err(rid, -32001, "No nucleus available for this session")

        keys = nucleus.core.get_keys_by_scope(target_scope)
        dropped = 0
        for key in keys:
            try:
                nucleus.core.drop_chunk(key)
                dropped += 1
            except Exception:
                pass

        return _ok(rid, {
            "status": "scope_dropped",
            "scope":   target_scope,
            "dropped": dropped,
            "message": f"Deleted {dropped} atoms carrying scope '{target_scope}'.",
        })

    def _handle_onto_pack_list(self, rid, data, session, scopes) -> dict:
        """
        List all ontology packages defined in ontology/REGISTRY.json.

        Each package entry includes:
          autoload  — true for base (always loaded), false for opt-in packs
          enabled   — true when listed in config/ontology_packs.json["enabled"]
          loaded    — true when a filesystem sentinel file exists for this pack
          ak_files  — number of .ak files in the package directory
        """
        import json as _json
        import glob as _glob

        _kernel_dir  = os.path.dirname(os.path.abspath(__file__))
        _project_dir = os.path.dirname(os.path.dirname(_kernel_dir))
        ont_dir      = os.path.join(_project_dir, "ontology")
        cfg_path     = os.path.join(_project_dir, "config", "ontology_packs.json")
        _sent_dir    = os.path.join(self.base_dir, "central", "sentinels")

        try:
            with open(cfg_path) as f:
                _cfg = _json.load(f)
                enabled  = set(_cfg.get("enabled", []))
                load_all = bool(_cfg.get("load_all", False))
        except Exception:
            enabled, load_all = set(), False

        def _sentinel_loaded(pack_name: str) -> bool:
            return bool(os.path.isdir(_sent_dir) and
                        _glob.glob(os.path.join(_sent_dir, f"{pack_name}_*.done")))

        def _pack_meta(pack_dir: str) -> dict:
            fpath = os.path.join(pack_dir, "PACK.json")
            if os.path.isfile(fpath):
                try:
                    with open(fpath) as f:
                        return _json.load(f)
                except Exception:
                    pass
            return {}

        def _ak_count(pack_dir: str) -> int:
            if not os.path.isdir(pack_dir):
                return 0
            return sum(1 for fn in os.listdir(pack_dir) if fn.endswith(".ak"))

        # Read REGISTRY.json for ordered package list
        reg_path = os.path.join(ont_dir, "REGISTRY.json")
        registry: list = []
        try:
            with open(reg_path) as f:
                registry = _json.load(f).get("packages", [])
        except Exception:
            pass

        RESERVED = {"seeds", "thesaurus"}
        registry_names = set()
        packages = []
        for pkg in registry:
            pname    = pkg.get("name", "")
            autoload = pkg.get("autoload", False)
            if not pname or pname in RESERVED:
                continue
            registry_names.add(pname)
            pack_dir = os.path.join(ont_dir, pname)
            pmeta    = _pack_meta(pack_dir)
            packages.append({
                "name":        pname,
                "label":       pmeta.get("label", pname),
                "description": pmeta.get("description", ""),
                "autoload":    autoload,
                "enabled":     autoload or load_all or pname in enabled,
                "loaded":      _sentinel_loaded(pname),
                "ak_files":    _ak_count(pack_dir),
                "license":     pmeta.get("license", ""),
            })

        # Packs enabled in config but absent from REGISTRY (user-added externals)
        for pname in sorted(enabled - registry_names):
            if pname in RESERVED:
                continue
            pack_dir = os.path.join(ont_dir, pname)
            pmeta    = _pack_meta(pack_dir)
            packages.append({
                "name":        pname,
                "label":       pmeta.get("label", pname),
                "description": pmeta.get("description", ""),
                "autoload":    False,
                "enabled":     True,
                "loaded":      _sentinel_loaded(pname),
                "ak_files":    _ak_count(pack_dir),
                "license":     pmeta.get("license", ""),
                "unregistered": True,
            })

        return _ok(rid, {
            "packages": packages,
            "enabled":  sorted(enabled),
            "load_all": load_all,
        })

    def _handle_onto_pack_enable(self, rid, data, session, scopes) -> dict:
        """
        Enable an optional pack and trigger its load in the background.
        All packages live at ontology/{name}/.  Requires role:librarian.
        """
        import json as _json
        if "role:librarian" not in scopes:
            return _err(rid, -32601, "onto.pack.enable requires role:librarian")

        pack_name = data.get("name", "").strip()
        if not pack_name:
            return _err(rid, -32602, "Missing param: name")
        if pack_name in ("base1", "base2", "base3"):
            return _err(rid, -32602, f"Pack '{pack_name}' has autoload:true — no enable needed.")

        _kernel_dir  = os.path.dirname(os.path.abspath(__file__))
        _project_dir = os.path.dirname(os.path.dirname(_kernel_dir))
        ont_dir      = os.path.join(_project_dir, "ontology")
        cfg_path     = os.path.join(_project_dir, "config", "ontology_packs.json")

        pack_dir = os.path.join(ont_dir, pack_name)
        if not os.path.isdir(pack_dir):
            return _err(rid, -32602, f"Pack '{pack_name}' not found at ontology/{pack_name}/")

        os.makedirs(os.path.join(_project_dir, "config"), exist_ok=True)
        try:
            with open(cfg_path) as f:
                cfg = _json.load(f)
        except Exception:
            cfg = {"enabled": []}

        if pack_name not in cfg["enabled"]:
            cfg["enabled"].append(pack_name)
            with open(cfg_path, "w") as f:
                _json.dump(cfg, f, indent=2)

        import threading as _thr
        _thr.Thread(target=self._boot_load_ontology, daemon=True,
                    name=f"ontology-pack-{pack_name}").start()

        return _ok(rid, {
            "status":   "enabled",
            "pack":     pack_name,
            "location": f"ontology/{pack_name}/",
            "message":  f"Pack '{pack_name}' enabled. Load running in background.",
        })

    def _handle_onto_pack_disable(self, rid, data, session, scopes) -> dict:
        """Disable an optional pack (does not remove already-loaded atoms)."""
        import json as _json
        if "role:librarian" not in scopes:
            return _err(rid, -32601, "onto.pack.disable requires role:librarian")

        pack_name = data.get("name", "").strip()
        if not pack_name:
            return _err(rid, -32602, "Missing param: name")
        if pack_name in ("base1", "base2", "base3"):
            return _err(rid, -32602, f"Pack '{pack_name}' is built-in and cannot be disabled.")

        _kernel_dir  = os.path.dirname(os.path.abspath(__file__))
        _project_dir = os.path.dirname(os.path.dirname(_kernel_dir))
        cfg_path = os.path.join(_project_dir, "config", "ontology_packs.json")

        try:
            with open(cfg_path) as f:
                cfg = _json.load(f)
        except Exception:
            cfg = {"enabled": []}

        if pack_name in cfg["enabled"]:
            cfg["enabled"].remove(pack_name)
            with open(cfg_path, "w") as f:
                _json.dump(cfg, f, indent=2)

        return _ok(rid, {
            "status": "disabled",
            "pack": pack_name,
            "message": f"Pack '{pack_name}' disabled. Atoms remain in nucleus until onto.reset.",
        })

    def _handle_onto_report(self, rid, data, ctx) -> dict:
        """Alias collision report — reads alias_collision_log from nucleus."""
        nucleus = getattr(ctx, '_nucleus', None)
        src = nucleus if nucleus else ctx
        since = float(data.get("since", 0.0) or 0.0)
        limit = int(data.get("limit", 200) or 200)
        entries_raw = src.get_alias_collision_log(since=since, limit=limit, unresolved_only=False)
        should_clear = str(data.get("clear", "")).lower() in ("true", "1", "yes")
        if should_clear and entries_raw:
            nucleus_core = getattr(src, 'core', None)
            if nucleus_core:
                try:
                    nucleus_core.clear_alias_collision_log()
                except Exception:
                    pass
        overwrites = sum(1 for e in entries_raw if e.get("event") == "overwrite")
        leaf_skips = sum(1 for e in entries_raw if e.get("event") == "leaf_skip")
        entries = [
            {"alias": e["alias"], "winner": e.get("new_key", ""), "loser": e.get("old_key", ""),
             "event": e.get("event", ""), "ts": e.get("ts", 0)}
            for e in entries_raw
        ]
        return _ok(rid, {"overwrites": overwrites, "leaf_skips": leaf_skips, "entries": entries})

    def _handle_iam_grant(self, rid, method, data, session) -> dict:
        """Admin composes per-client authority as grants (capability-delegation-iam-spec §4.1).
        `iam.grant`/`iam.revoke` are IAM_MANAGE-gated (enforced by METHOD_TO_ACTION); `iam.grants`
        lists a principal's grants (own, or any for an admin). The bounded sub-admin
        request→approve flow (§4.2) and enterprise signing are staged."""
        iam = self.iam
        client_id = getattr(session, "client_id", "")
        role = getattr(session, "role", None)
        if method == "iam.grants":
            target = (data.get("grantee") or data.get("id") or client_id).strip()
            # A non-admin may only list its OWN grants.
            if target != client_id:
                from lib.akasha.identity import Capability
                pol = iam._policies.get(role)
                if not (pol and pol.has(Capability.IAM_MANAGE)):
                    return _err(rid, -32001, "listing another principal's grants requires admin")
            return _ok(rid, {"grantee": target, "grants": iam.grants_list(target)})
        if method == "iam.revoke":
            grantee = (data.get("grantee") or "").strip()
            gid = (data.get("grant_id") or data.get("id") or "").strip()
            if not grantee or not gid:
                return _err(rid, -32602, "iam.revoke requires grantee= and grant_id=")
            ok = iam.grant_revoke(grantee, gid)
            return _ok(rid, {"revoked": ok, "grantee": grantee, "grant_id": gid})
        # iam.grant
        grantee = (data.get("grantee") or "").strip()
        capability = (data.get("capability") or data.get("cap") or "").strip().lower()
        resource = (data.get("resource") or "*").strip()
        if not grantee or not capability:
            return _err(rid, -32602, "iam.grant requires grantee= and capability=")
        # Fail-closed: only known, delegable capabilities may be granted.
        from lib.akasha.identity import Capability
        try:
            Capability(capability)
        except ValueError:
            return _err(rid, -32602, f"unknown capability '{capability}'")
        # Reserved-unit safety for service grants: a grant selector may never cover the
        # writer/root or job units (service-extension-and-delegation-spec §5).
        if capability == Capability.SVC_OPERATE.value:
            if resource in ("*", "svc:*") or resource.startswith(("svc:cell", "job:")):
                return _err(rid, -32003,
                            "svc_operate grant selector may not cover svc:cell/job:* "
                            "(use svc:app:<operator>:* — never the writer/root)")
        verbs = data.get("verbs") or "*"
        expires = data.get("expires")
        grant = iam.grant_add(grantor=client_id, grantee=grantee, capability=capability,
                              resource=resource, verbs=verbs, expires=expires)
        return _ok(rid, {"granted": grant})

    # svc.ls fields that are safe to reveal to a plain READ caller (e.g. a network guest on
    # a deployment that exposes the RPC, like thesaurus08). The respawn RECIPE (argv/env), the
    # pid, filesystem log paths, and deps are internal machinery — shown only to a holder of
    # SVC_OPERATE (operators/admin), never leaked to a reader.
    _SVC_LS_PUBLIC_FIELDS = ("id", "kind", "state", "engine", "host", "port",
                             "live", "restart", "substrate", "trust", "serve_only", "detail")

    def _handle_svc_rpc(self, rid, method, data, session) -> dict:
        """Operate the Supervisor plane over RPC. `svc ls` lists the run-dir; `svc
        start/restart` respawn from the persisted recipe (P1) — spawned HERE, in the daemon
        that hosts the Supervisor (P3), never by the client. Authz (svc.read / svc.operate)
        is enforced by the dispatcher via METHOD_TO_ACTION before this handler runs."""
        try:
            from lib.harmonia import supervisor as sv
            from lib.akasha.identity import Capability
        except Exception as exc:
            return _err(rid, -32603, f"supervisor unavailable: {exc}")
        sup = sv.Supervisor(self.base_dir)
        if method == "svc.ls":
            units = sv.list_units(self.base_dir)
            # Only an operator (base SVC_OPERATE — admin today) sees the full descriptor;
            # a plain reader gets a redacted operational view with no recipe/pid/paths.
            pol = self.iam._policies.get(getattr(session, "role", None))
            if not (pol and pol.has(Capability.SVC_OPERATE)):
                units = [{k: u[k] for k in self._SVC_LS_PUBLIC_FIELDS if k in u} for u in units]
            return _ok(rid, {"units": units})
        unit_id = (data.get("id") or data.get("name") or "").strip()
        if not unit_id:
            return _err(rid, -32602, "svc requires id=<unit>")
        if not unit_id.startswith(("svc:", "job:")):
            unit_id = f"svc:{unit_id}"
        # Reserved units are never client-operable via this path (writer/root + jobs).
        if method in ("svc.start", "svc.restart") and unit_id == "svc:cell":
            return _err(rid, -32003, "svc:cell is the daemon root — not restartable via RPC")
        if unit_id.startswith("job:"):
            return _err(rid, -32003, "job units are executor-owned, not svc-operable")
        try:
            if method == "svc.start":
                result = sup.start(unit_id)
            elif method == "svc.restart":
                result = sup.restart(unit_id)
            elif method == "svc.stop":
                result = sup.stop(unit_id)
            else:
                return _err(rid, -32601, f"unknown svc method {method}")
        except Exception as exc:
            return _err(rid, -32603, f"svc {method} failed: {exc}")
        if isinstance(result, dict) and result.get("error"):
            return _err(rid, -32003, result["error"])
        return _ok(rid, result)

    def _handle_onto_status(self, rid, data, session, scopes) -> dict:
        """Ontology status: nucleus counts, REGISTRY packages, and sentinel files."""
        import json as _json
        import glob as _glob

        _kernel_dir  = os.path.dirname(os.path.abspath(__file__))
        _project_dir = os.path.dirname(os.path.dirname(_kernel_dir))
        ont_dir      = os.path.join(_project_dir, "ontology")
        cfg_path     = os.path.join(_project_dir, "config", "ontology_packs.json")
        _sent_dir    = os.path.join(self.base_dir, "central", "sentinels")

        nucleus = getattr(session, "nucleus", None)
        atom_count = link_count = alias_count = 0
        if nucleus:
            try:
                _t = nucleus.core.get_store_totals()
                atom_count, link_count, alias_count = _t["chunks"], _t["links"], _t["aliases"]
            except Exception:
                pass

        sent_names = []
        if os.path.isdir(_sent_dir):
            sent_names = sorted(os.path.basename(f) for f in _glob.glob(os.path.join(_sent_dir, "*.done")))

        # A pack's atom-load is complete when its phase-2 sentinel file exists
        # ({pack}_{hash}.done). Present-on-disk packs without one are still loading
        # (or not yet reached). Use the sentinel basenames already globbed above.
        def _pack_loaded(pname: str) -> bool:
            return any(s.startswith(pname + "_") and s.endswith(".done") for s in sent_names)

        # REGISTRY summary
        reg_path = os.path.join(ont_dir, "REGISTRY.json")
        registry_packages = []
        try:
            with open(reg_path) as f:
                for pkg in _json.load(f).get("packages", []):
                    pname = pkg.get("name", "")
                    pdir  = os.path.join(ont_dir, pname)
                    fcount = sum(1 for fn in os.listdir(pdir) if fn.endswith(".ak")) if os.path.isdir(pdir) else 0
                    registry_packages.append({
                        "name":       pname,
                        "autoload":   pkg.get("autoload", False),
                        "file_count": fcount,
                        "exists":     os.path.isdir(pdir),
                        "loaded":     _pack_loaded(pname),
                    })
        except Exception:
            pass

        # ── Load-progress summary — one-glance "still loading / done" ──────────────
        # The boot load is a background daemon; a fresh seed re-extract re-imports
        # everything on the next boot (mtime-changed manifest hash). This tells the
        # operator whether that pass is still running, without having to eyeball the
        # sentinel list. Phase markers: _relations_*.done = all atoms+links loaded (the
        # definitive core-complete signal the portal/learn daemons gate on); curations
        # complete is a DB alias (ont:curation:loaded:*), CSL likewise.
        def _phase_done(prefix: str) -> bool:
            return any(s.startswith(prefix) and s.endswith(".done") for s in sent_names)

        def _alias_phase_done(pattern: str) -> bool:
            try:
                return bool(nucleus and nucleus.core.get_aliases_by_pattern(pattern))
            except Exception:
                return False

        # A pack that exists but ships 0 .ak files has nothing to load — it never gets a
        # sentinel, so counting it as "present" would pin the summary at IN PROGRESS
        # forever (the archaeology/biology/literature/medicine placeholders do this).
        _present = [p for p in registry_packages if p["exists"] and p.get("file_count", 0) > 0]
        _present_loaded = [p for p in _present if p["loaded"]]
        _pending = [p["name"] for p in _present if not p["loaded"]]
        _relations_done = _phase_done("_relations_")
        _has_curations = os.path.isdir(os.path.join(_project_dir, "curations"))
        _curations_done = (not _has_curations) or _alias_phase_done("ont:curation:loaded:")
        # "complete" = the CORE graph is loaded (all atoms + links = _relations_done, and no
        # present pack still pending). Curations and reconcile are OPTIONAL layers that do NOT
        # gate core completeness: curations are example ENRICHMENTS (not every tier runs them —
        # the seeds tier would otherwise pin complete=False forever), and reconcile only runs on
        # load_all tiers. Both are reported separately below. The portal/learn daemons already
        # gate on _relations_done, not on these, so this matches what the system treats as ready.
        _complete = bool(_relations_done and not _pending)
        load_summary = {
            "complete":        _complete,
            "in_progress":     not _complete,
            "packs_present":   len(_present),
            "packs_loaded":    len(_present_loaded),
            "packs_pending":   _pending,
            "relations_done":  _relations_done,     # atoms + all links loaded
            "canon_done":      _phase_done("_canon_"),
            "reconcile_done":  _phase_done("_reconcile_"),   # load_all tiers only; informational
            "curations_done":  _curations_done,              # optional enrichment; does not gate 'complete'
            # atoms count keeps climbing while loading — poll onto.status to watch it move.
            "atoms":           atom_count,
            "hint": (("ontology core load complete."
                      + ("" if _curations_done else " (curation enrichments still loading in the background.)"))
                     if _complete else
                     "ontology still loading — safe to exit; unfinished packs re-load on the "
                     "next boot (content-addressed, no data loss). Re-run onto.status to watch."),
        }

        enabled_packs = []
        try:
            with open(cfg_path) as f:
                enabled_packs = _json.load(f).get("enabled", [])
        except Exception:
            pass

        return _ok(rid, {
            "load": load_summary,
            "nucleus": {
                "atoms":   atom_count,
                "links":   link_count,
                "aliases": alias_count,
            },
            "registry": {
                "packages": registry_packages,
            },
            "enabled_packs": enabled_packs,
            "sentinels": {
                "count": len(sent_names),
                "files": sent_names,
            },
        })

    # ------------------------------------------------------------------
    # Exploration
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Scope session state (sys.scope.*)
    # ------------------------------------------------------------------

    def _get_scope_state(self, session) -> dict:
        """Returns effective scope state, reading from whiteboard-local keys when active."""
        active_wb = session.get_context("active_whiteboard")
        if active_wb:
            return {
                "axis":  session.get_context(f"wb:{active_wb}:scope_axis"),
                "scope": session.get_context(f"wb:{active_wb}:scope_scope"),
                "time":  session.get_context(f"wb:{active_wb}:scope_time"),
            }
        return {
            "axis":  session.get_context("active_axis"),
            "scope": session.get_context("active_scope"),
            "time":  session.get_context("active_time"),
        }

    # ------------------------------------------------------------------
    # Display Focus
    # ------------------------------------------------------------------

    def _parse_focus_tokens(self, tokens: list, client_id: str) -> dict:
        """Parse @-prefixed focus tokens into a structured filter dict."""
        scopes: list = []
        ns_prefixes: list = []
        for tok in tokens:
            if tok == "@me":
                scopes.append(f"owner:{client_id}")
            elif tok.startswith("@group:"):
                scopes.append(f"scope:group:{tok[len('@group:'):]}")
            elif tok.startswith("@ns:"):
                ns_prefixes.append(tok[len("@ns:"):] + ":")
        return {"scopes": scopes, "ns_prefixes": ns_prefixes}

    def _get_display_focus(self, session) -> dict:
        return session.get_context("display_focus") or {}

    def _passes_display_focus(self, key: str, focus: dict, ctx, nucleus) -> bool:
        """Return True if atom passes all active display focus filters (AND logic)."""
        if not focus:
            return True
        for scope in focus.get("scopes", []):
            ok = ctx.core.check_chunk_access_any(key, [scope])
            if not ok and nucleus:
                ok = nucleus.core.check_chunk_access_any(key, [scope])
            if not ok:
                return False
        for prefix in focus.get("ns_prefixes", []):
            aliases = ctx.core.get_aliases_by_key(key) or []
            if nucleus:
                aliases += nucleus.core.get_aliases_by_key(key) or []
            if not any(a.startswith(prefix) for a in aliases):
                return False
        return True

    def _handle_focus(self, rid, data, session, client_id) -> dict:
        tokens = data.get("tokens", [])
        nucleus = getattr(session, 'nucleus', None)
        ctx    = session.local_cortex

        if not tokens:
            current = session.get_context("display_focus") or {}
            active: list = []
            for s in current.get("scopes", []):
                if s == f"owner:{client_id}":
                    active.append("@me")
                elif s.startswith("scope:group:"):
                    active.append("@group:" + s[len("scope:group:"):])
                else:
                    active.append(s)
            for p in current.get("ns_prefixes", []):
                active.append("@ns:" + p.rstrip(":"))
            return _ok(rid, {"focus_state": " + ".join(active) if active else "@all"})

        if tokens == ["@all"]:
            session.set_context("display_focus", None)
            return _ok(rid, {"focus_state": "@all", "status": "cleared"})

        focus = self._parse_focus_tokens(tokens, client_id)
        session.set_context("display_focus", focus)
        labels: list = []
        for s in focus["scopes"]:
            if s == f"owner:{client_id}":
                labels.append("@me")
            elif s.startswith("scope:group:"):
                labels.append("@group:" + s[len("scope:group:"):])
        for p in focus["ns_prefixes"]:
            labels.append("@ns:" + p.rstrip(":"))
        return _ok(rid, {"focus_state": " + ".join(labels), "status": "set"})

    def _handle_scope_set(self, rid, data, session) -> dict:
        active_wb = session.get_context("active_whiteboard")
        if active_wb:
            if "axis" in data:
                session.set_context(f"wb:{active_wb}:scope_axis",  data["axis"] or None)
            if "scope" in data:
                val = data["scope"]
                session.set_context(f"wb:{active_wb}:scope_scope", int(val) if val is not None else None)
            if "time" in data:
                session.set_context(f"wb:{active_wb}:scope_time",  data["time"] or None)
            scope = self._get_scope_state(session)
            return _ok(rid, {
                "status":       "scope_updated",
                "whiteboard":   active_wb,
                "active_axis":  scope["axis"],
                "active_scope": scope["scope"],
                "active_time":  scope["time"],
            })
        else:
            if "axis" in data:
                session.set_context("active_axis",  data["axis"] or None)
            if "scope" in data:
                val = data["scope"]
                session.set_context("active_scope", int(val) if val is not None else None)
            if "time" in data:
                session.set_context("active_time",  data["time"] or None)
            return _ok(rid, {
                "status":       "scope_updated",
                "active_axis":  session.get_context("active_axis"),
                "active_scope": session.get_context("active_scope"),
                "active_time":  session.get_context("active_time"),
            })

    def _handle_scope_get(self, rid, session) -> dict:
        active_wb = session.get_context("active_whiteboard")
        scope = self._get_scope_state(session)
        result = {
            "active_axis":  scope["axis"],
            "active_scope": scope["scope"],
            "active_time":  scope["time"],
        }
        if active_wb:
            result["whiteboard"] = active_wb
        return _ok(rid, result)

    def _handle_scope_reset(self, rid, session) -> dict:
        active_wb = session.get_context("active_whiteboard")
        if active_wb:
            for key in (f"wb:{active_wb}:scope_axis",
                        f"wb:{active_wb}:scope_scope",
                        f"wb:{active_wb}:scope_time"):
                session.set_context(key, None)
            return _ok(rid, {
                "status":       "scope_reset",
                "whiteboard":   active_wb,
                "active_axis":  None,
                "active_scope": None,
                "active_time":  None,
            })
        else:
            for key in ("active_axis", "active_scope", "active_time"):
                session.set_context(key, None)
            return _ok(rid, {
                "status":       "scope_reset",
                "active_axis":  None,
                "active_scope": None,
                "active_time":  None,
            })

    # ------------------------------------------------------------------
    # Exploration
    # ------------------------------------------------------------------

    def _handle_gap_scan(self, rid, data, session, ctx, scopes) -> dict:
        """gap.scan [limit=] [scan=] — surface the self-expanding-ontology-loop entry
        points: concepts that are USED a lot (distributional importance) but UNDER-CURATED
        (few semantic links). The mismatch between how much a node is referenced and how
        richly it is linked is the signal for what to enrich next (via fetch / weaver /
        an LLM). Structural maturity is the ShelfScore idea, generalised to any atom;
        importance is inbound weave references (sys:refers_to). Scope-filtered."""
        limit = max(1, min(int(data.get("limit", 20)), 200))
        scan = max(1, min(int(data.get("scan", 3000)), 30000))
        gaps = self._scan_gaps(ctx, scopes, scan, limit)
        out = [{"key": g["key"], "gap_score": g["gap_score"], "importance": g["importance"],
                "curated_links": g["curated_links"], "preview": g["content"][:80]}
               for g in gaps]
        return _ok(rid, {"gaps": out, "count": len(out)})

    def _scan_gaps(self, ctx, scopes, scan, limit) -> list:
        """Rank atoms by the self-expanding-loop gap signal: importance (inbound
        references) × (1 − structural maturity of curated outbound links). Scope-filtered,
        external atoms excluded. Shared by gap.scan (report) and gap.fetch (act)."""
        results = []
        for row in (ctx.stream(limit=scan) or []):
            key = row.get("key")
            if not key or (scopes and not ctx.check_access(key, scopes)):
                continue
            # Externally-fetched atoms are not enrichment targets — they ARE the
            # enrichment material. Curating them would loop fetch→gap→fetch. Skip.
            if _is_external(row.get("meta")):
                continue
            # Importance: read the atom's incrementally-maintained meaning-density
            # (meta['salience']) — bumped on every link, so no per-atom link scan here. Falls
            # back to counting inbound links for atoms written before salience existed.
            _m = row.get("meta")
            if isinstance(_m, str):
                try:
                    _m = json.loads(_m)
                except Exception:
                    _m = {}
            importance = (_m or {}).get("salience")
            if importance is None:
                importance = len(ctx.get_incoming_links(key) or [])
            if not importance or importance < 0.5:
                continue
            # Structural maturity: curated semantic links out (exclude sys:/weave scaffolding).
            adj = ctx.get_adjacent_links(key) or []
            curated = sum(1 for pair in adj
                          if len(pair) > 1 and not str(pair[1]).startswith("sys:"))
            struct = min(1.0, curated / 6.0)
            imp = min(1.0, importance / 8.0)
            gap = imp * (1.0 - struct)          # important but thin → high
            if gap > 0.0:
                results.append({"gap_score": round(gap, 4), "key": key,
                                "importance": importance, "curated_links": curated,
                                "content": row.get("content") or ""})
        results.sort(key=lambda r: r["gap_score"], reverse=True)
        return results[:limit]

    def _handle_gap_fetch(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """gap.fetch [limit=] [scan=] — close the self-expanding-ontology loop: find the
        important-but-thin concepts (gap.scan), then AUTO-FETCH external context to enrich
        each, weaving it into the graph so the next semantic.learn sees a richer corpus.
        This is the avatar-delegate step (#31): whichever agent/avatar session invokes it
        performs the fetch under its own identity, and every fetched atom carries the
        provenance=external guardrail (trust score + provenance scopes) so unvetted web
        text can neither poison the learned model nor masquerade as curation. Bounded and
        degrades gracefully offline (no network → fetched=false, no error). Admin/librarian
        only (external network writes). Runs inside the caller's write workspace."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        if not self.contexa:
            return _err(rid, -32001, "ContexaEngine not available in this environment.")
        limit = max(1, min(int(data.get("limit", 3)), 10))
        scan = max(1, min(int(data.get("scan", 3000)), 30000))
        gaps = self._scan_gaps(ctx, scopes, scan, limit)

        enriched = []
        for g in gaps:
            key = g["key"]
            query = self._gap_query(ctx, key, g["content"])
            if not query:
                enriched.append({"gap_key": key, "query": None, "fetched": False,
                                 "reason": "no query term"})
                continue
            try:
                res = self._do_fetch(session, ctx, scopes, client_id, query,
                                     link_to=key, link_rel="calc:enriches")
            except Exception as exc:                       # network / provider failure
                enriched.append({"gap_key": key, "query": query, "fetched": False,
                                 "reason": str(exc)[:120]})
                continue
            if res.get("written"):
                enriched.append({"gap_key": key, "query": query, "fetched": True,
                                 "atom_key": res.get("atom_key"),
                                 "trust": res.get("evidence", {}).get("authority")})
            else:
                enriched.append({"gap_key": key, "query": query, "fetched": False,
                                 "reason": res.get("error", "no content")})
        n_ok = sum(1 for e in enriched if e["fetched"])
        return _ok(rid, {"enriched": enriched, "gaps_scanned": len(gaps),
                         "fetched": n_ok})

    def _gap_query(self, ctx, key, content) -> str:
        """Derive a fetch query for a gap atom: prefer a human-readable alias (the concept
        name), else the leading words of its content. Namespace prefixes are stripped so
        'concept:icarus' queries 'icarus'."""
        try:
            aliases = ctx.get_aliases_by_key(key) if hasattr(ctx, "get_aliases_by_key") else None
        except Exception:
            aliases = None
        if aliases:
            term = str(aliases[0]).split(":")[-1].replace("_", " ").strip()
            if len(term) >= 2:
                return term[:80]
        text = (content or "").strip()
        if len(text) >= 2:
            return " ".join(text.split()[:6])[:80]
        return ""

    def _handle_semantic_learn(self, rid, data, session, ctx, scopes) -> dict:
        """semantic.learn [limit=] [dim=] [max_vocab=] — learn a distributional embedding
        model (PPMI + SVD, numpy) from the FULL corpus (nucleus ontology + this cortex)
        and persist it to the nucleus vault so every session's semantic.search uses it.
        Admin/librarian only (a heavy, shared, one-shot compute)."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        from lib.akasha.semantic_learn import OntologyLearner, tokens, store_model
        nucleus = getattr(session, "nucleus", None)
        if nucleus is None:
            return _err(rid, -32002, "Nucleus unavailable")
        if not OntologyLearner.available():
            return _err(rid, -32002,
                        "numpy unavailable — learner needs numpy (search degrades to the "
                        "feature-hashing floor)")
        limit = max(10, min(int(data.get("limit", 40000)), 200000))
        min_len = int(data.get("min_len", 8))
        dim = max(8, min(int(data.get("dim", 64)), 256))
        max_vocab = max(50, min(int(data.get("max_vocab", 2000)), 8000))

        docs, n = [], 0
        for src in (nucleus.core, ctx.core):
            try:
                chunks = src.get_all_chunks()
            except Exception:
                chunks = []
            for row in chunks:
                content = row.get("content") or ""
                if len(content) >= min_len and not _is_external(row.get("meta")):
                    docs.append(tokens(content))
                    n += 1
                    if n >= limit:
                        break
            if n >= limit:
                break

        learner = OntologyLearner(dim=dim, max_vocab=max_vocab)
        if not learner.learn(docs):
            return _err(rid, -32002,
                        f"learn failed (docs={len(docs)} — need >=3 with a shared vocab)")
        store_model(nucleus, learner)
        return _ok(rid, {"status": "learned", "docs": len(docs),
                         "vocab": len(learner.vocab), "dim": dim})

    def _handle_node_learn(self, rid, data, session, ctx, scopes) -> dict:
        """node.learn [dim=] [walks=] [length=] — learn STRUCTURAL node embeddings from the
        typed-link graph (random walks → PPMI+SVD, the NodeWalkLearner). Complementary to the
        content model: it captures "connected the same way" rather than "means the same".
        Persisted to the nucleus vault. Admin/librarian only, numpy-gated."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        from lib.akasha.semantic_learn import NodeWalkLearner, store_node_model
        nucleus = getattr(session, "nucleus", None)
        if nucleus is None:
            return _err(rid, -32002, "Nucleus unavailable")
        if not NodeWalkLearner.available():
            return _err(rid, -32002, "numpy unavailable — node embeddings need numpy")
        dim = max(8, min(int(data.get("dim", 32)), 256))
        walks = max(1, min(int(data.get("walks", 10)), 40))
        length = max(2, min(int(data.get("length", 8)), 20))
        links = []
        for src in (nucleus.core, ctx.core):
            try:
                links.extend(src.get_all_links(limit=200000) or [])
            except Exception:
                pass
        nwl = NodeWalkLearner(dim=dim, walks_per_node=walks, length=length, seed=7)
        if not nwl.learn(links):
            return _err(rid, -32002,
                        f"node.learn failed (links={len(links)} — need a connected graph)")
        store_node_model(nucleus, nwl)
        return _ok(rid, {"status": "learned", "links": len(links),
                         "nodes": len(nwl.vocab), "dim": dim})

    # Abstract / definitional vocabulary that crowds CONTENT similarity once loaded — its
    # glosses are lexically dense, so it dominates sim/search though it is not a real
    # content neighbour. Two populations:
    #   • the lexicon layer  — reldef:/nsdef: atoms (members of the `rels`/`namespaces` sets)
    #   • abstract hub atoms — the DNA/structural/logical vocabulary whose whole job is to
    #     DEFINE (emotions, system relations, set operations, logic, frames, …), detected
    #     by their namespace prefix.
    # Both are excluded from sim / semantic.search / node.sim by default; opt back in with
    # meta=1 / all=1 (vocabulary exploration). Content namespaces (word:, concept:, ingred:,
    # dish:, geo:, …) are never excluded.
    _META_NAMESPACES = frozenset({
        "sys", "set_op", "log", "frame", "emo", "calc", "dna", "meta", "scope", "tmp",
    })

    def _meta_scope_flag(self, data) -> bool:
        return str(data.get("meta") or data.get("all") or "").strip().lower() in ("1", "yes", "true", "all", "y")

    def _meta_scope_keys(self, ctx) -> set:
        # Lexicon layer via set membership (synchronous); abstract hubs via an INDEXED
        # alias-prefix scan (`alias LIKE 'emo:%'` — a prefix range, index-backed), which is
        # synchronous and does not depend on the async ns:/leaf: derivation queue having
        # drained. Built once per call; unioned local cell + nucleus.
        keys: set = set()
        nucleus = getattr(ctx, "_nucleus", None)
        try:
            keys |= set(ctx.get_collection_members("rels") or [])          # reldef: layer
            keys |= set(ctx.get_collection_members("namespaces") or [])    # nsdef: layer
            for ns in self._META_NAMESPACES:                              # abstract hubs
                for r in (ctx.core.get_aliases_by_pattern(f"{ns}:%") or []):
                    keys.add(r["key"])
                if nucleus:
                    for r in (nucleus.core.get_aliases_by_pattern(f"{ns}:%") or []):
                        keys.add(r["key"])
        except Exception:
            pass
        return keys

    def _handle_node_sim(self, rid, data, session, ctx, scopes) -> dict:
        """node.sim id= [limit=] — atoms STRUCTURALLY similar to an atom (nearest node-walk
        embeddings): "connected the same way". Requires a learned model (node.learn) and that
        the anchor is a linked node. Scope-filtered. Complements semantic.search (content)."""
        from lib.akasha.semantic_learn import get_node_model, cosine as _lcos
        nucleus = getattr(session, "nucleus", None)
        model = get_node_model(nucleus) if nucleus is not None else None
        if model is None:
            return _err(rid, -32002, "no structural model — run node.learn first (or numpy absent)")
        target = (data.get("id") or data.get("key") or session.last_written_id or "").strip()
        if not target:
            return _err(rid, -32602, "node.sim requires 'id'")
        anchor = ctx.resolve_alias(target) or target
        avec = model.node_vector(anchor)
        if not avec:
            # Proto-word hub (e.g. 'rome'): the real links hang off its senses, each of
            # which --specializes--> the proto-word. Anchor on the sense that IS in the
            # structural model, so `node.sim rome` behaves like node.sim on
            # geo:capital:rome — parity with how `r`/the explorer resolve a bare word.
            for _src, _rel in (ctx.get_incoming_links(anchor, "specializes") or []):
                _sv = model.node_vector(_src)
                if _sv:
                    anchor, avec = _src, _sv
                    break
        if not avec:
            return _err(rid, -32002,
                        f"atom '{anchor}' is not in the structural model (no links, or re-run node.learn)")
        _meta = set() if self._meta_scope_flag(data) else self._meta_scope_keys(ctx)
        scored = []
        for key in list(model.vocab.keys()):
            if key == anchor:
                continue
            if key in _meta:                       # lexicon definition atom — not a content neighbour
                continue
            if scopes and not ctx.check_access(key, scopes):
                continue
            v = model.node_vector(key)
            if not v:
                continue
            s = _lcos(avec, v)
            if s > 0.0:
                scored.append((s, key))
        scored.sort(key=lambda t: t[0], reverse=True)
        window, page = _paginate(scored, data.get("limit"), data.get("cursor"),
                                 default=10, max_limit=100)
        results = [{"key": k, "name": _readable(ctx, k), "score": round(s, 4),
                    "preview": (ctx.get_chunk(k) or "")[:80]} for s, k in window]
        return _ok(rid, {"anchor": anchor, "results": results, "count": len(results),
                         "mode": "structural", "page": page})

    def _handle_semantic_search(self, rid, data, session, ctx, scopes) -> dict:
        """semantic.search query=|id= [limit=] [scan=] — rank atoms by cosine similarity.
        `query=` is free text; `id=`/`like=` anchors on an EXISTING atom ("find atoms like
        THIS one") — its own content is re-embedded as the query and the anchor is excluded
        from the results. Scope-filtered (fail-closed). Uses the learned model when one has
        been built (re-embedding candidates into one space) else the stored feature-hashing
        vectors. `tier` says which; `anchor` echoes the atom key when id-anchored."""
        query = (data.get("query") or data.get("q") or "").strip()
        anchor_ref = (data.get("id") or data.get("like") or "").strip()
        anchor_key = None
        if anchor_ref and not query:
            # Atom-anchored: resolve to an existing atom and search by its own meaning.
            resolved = ctx.resolve_alias(anchor_ref) or anchor_ref
            content = ctx.get_scoped_chunk(resolved, scopes) if scopes else ctx.get_chunk(resolved)
            if content is None:
                query = anchor_ref                       # not an atom → treat as free text
            else:
                query, anchor_key = content, resolved
        if not query:
            return _err(rid, -32602, "semantic.search requires 'query' or 'id'")
        limit = max(1, min(int(data.get("limit", 10)), 100))
        scan = max(1, min(int(data.get("scan", 2000)), 20000))

        from lib.akasha.semantic_learn import get_shared_model, cosine as _lcos
        nucleus = getattr(session, "nucleus", None)
        model = get_shared_model(nucleus) if nucleus is not None else None
        tensor = getattr(ctx, "tensor", None)

        if model is not None and model.embed_text(query):
            tier = "learned"
            qvec = model.embed_text(query)
        elif tensor is not None and tensor.embed("", query, {}):
            tier = "floor"
            qvec = tensor.embed("", query, {})
        else:
            return _ok(rid, {"query": query, "results": [], "count": 0, "tier": "none"})

        _meta = set() if self._meta_scope_flag(data) else self._meta_scope_keys(ctx)
        import json as _json
        # The searchable corpus is the SHARED ONTOLOGY, which lives in the nucleus — not
        # in the session's private cell. Streaming only ctx.stream() searched an isolated
        # guest cell (near-empty) and returned a handful of stray atoms; the ingredients /
        # concepts a guest MCP "read-first" client wants were invisible. Union the nucleus
        # candidates (deduped), exactly like discover_atoms/explore. Every candidate still
        # passes ctx.check_access(key, scopes), so isolation is unchanged — the nucleus holds
        # shared ground-truth only, never another user's private cell atoms.
        _rows = list(ctx.stream(limit=scan) or [])
        if nucleus is not None and nucleus is not ctx:
            # NucleusEngine has no stream() wrapper — go straight to the backend primitive.
            _rows += list(nucleus.core.fetch_stream(scan) or [])
        _seen_keys: set = set()
        scored = []
        for row in _rows:
            key = row.get("key")
            if not key or key in _seen_keys:
                continue
            _seen_keys.add(key)
            if key == anchor_key or key in _meta or (scopes and not ctx.check_access(key, scopes)):
                continue
            content = row.get("content") or ""
            if tier == "learned":
                vec = model.embed_text(content)             # re-embed → same space as qvec
            else:
                meta = row.get("meta")
                if isinstance(meta, str):
                    try:
                        meta = _json.loads(meta)
                    except Exception:
                        meta = {}
                vec = meta.get("semantic_vector") if isinstance(meta, dict) else None
            if not vec:
                continue
            s = _lcos(qvec, vec)
            if s > 0.0:
                scored.append((s, key, content))
        scored.sort(key=lambda t: t[0], reverse=True)
        window, page = _paginate(scored, data.get("limit"), data.get("cursor"),
                                 default=10, max_limit=100)
        results = [{"key": k, "name": _readable(ctx, k), "score": round(s, 4), "preview": c[:80]}
                   for s, k, c in window]
        out = {"results": results, "count": len(results), "tier": tier, "page": page}
        if anchor_key:
            out["anchor"] = anchor_key
        else:
            out["query"] = query
        return _ok(rid, out)

    def _handle_explore(self, rid, data, session, ctx, scopes, history) -> dict:
        """
        explore — query/filter tool for discovering atoms in the ontology.

        Filters (at least one required):
          ns=    namespace prefix (aliases matching ns:*)
          set=   set membership (atoms in this named set)
          type=  meta.type filter
          pat=   alias wildcard pattern (% and _ wildcards)
          id=    positional alias/pattern (falls through to pat= if no other filter)

        Multiple filters are ANDed. Results are numbered for dive navigation.
        """
        ns        = (data.get("ns") or "").strip()
        set_filt  = (data.get("set") or "").strip()
        atom_type = (data.get("type") or "").strip()
        pat       = (data.get("pat") or data.get("id") or "").strip()
        limit     = int(data.get("limit", 50))
        nucleus   = getattr(session, 'nucleus', None)

        if not (ns or set_filt or atom_type or pat):
            return _err(rid, -32602,
                "explore requires at least one filter: ns=, set=, type=, or pat= (or a positional pattern)")

        # ── Delegate to the shared discovery core (also backs thesaurus.explore) ──
        from lib.akasha.discovery import discover_atoms
        group_engines = self._member_group_engines(session, scopes) if session else []
        results = discover_atoms(
            ctx, nucleus, group_engines, scopes,
            ns=ns, set_filt=set_filt, atom_type=atom_type, pat=pat, limit=limit)

        session.set_context("last_signposts",
            [{"key": r["key"], "alias": r["alias"]} for r in results])

        filters = {k: v for k, v in
                   {"ns": ns, "set": set_filt, "type": atom_type, "pat": pat}.items() if v}
        return _ok(rid, {
            "atoms":   results,
            "count":   len(results),
            "filters": filters,
        })

    # ------------------------------------------------------------------
    # Graph Tree (link-traversal tree view)
    # ------------------------------------------------------------------

    def _handle_graph_tree(self, rid, data, session, ctx, scopes) -> dict:
        """
        graph.tree — BFS link-traversal tree from an atom, set, or namespace.

          target= atom alias/key, set:<name>, or ns:<prefix>
          depth=  traversal depth (default 2, capped 1–5)
          follow= relation type filter (empty = all outgoing)
          format= rich | ascii (default rich)
          concept= yes → the CONCEPT tree (sys:is_a subset/superset only), delegated to
                   the concept navigator (concept.tree) — ignores every other link type + sets
        """
        # Concept-hierarchy mode: `tree <c> concept=yes` walks the sys:is_a up/down lattice only.
        if str(data.get("concept", "")).strip().lower() in ("yes", "true", "1", "y") \
                and _concept_registry:
            r = _concept_registry.dispatch_if_handled(
                "concept.tree", session,
                {"root": data.get("target") or data.get("id") or "",
                 "depth": data.get("depth", ""), "limit": data.get("limit", ""),
                 "leaves": data.get("leaves", "")},
                rid)
            if r is not None:
                return r

        target = (data.get("target") or data.get("id") or "").strip()
        depth  = int(data.get("depth", 2))
        follow = (data.get("follow") or "").strip()
        fmt    = (data.get("format") or "rich").strip()

        if not target:
            return _err(rid, -32602, "graph.tree requires target= (atom alias/key, set:<name>, or ns:<prefix>)")

        try:
            tv = ctx.graph_tree(
                target         = target,
                depth          = depth,
                follow         = follow,
                fmt            = fmt,
                allowed_scopes = scopes or [],
            )
            return _ok(rid, tv)
        except Exception as e:
            logger.error("[graph.tree] %s", e, exc_info=True)
            return _err(rid, -32000, f"graph.tree error: {e}")

    # ------------------------------------------------------------------
    # Dive / View (consciousness layer)
    # ------------------------------------------------------------------

    def _handle_view(self, rid, data, session, scopes) -> dict:
        """view id= — the consciousness view of an atom on its own: signposts (1-hop),
        resonance (2-hop / semantic neighbours), cosmos_nd (spatial-emotional vector), and
        aura_color. Same payload dive/look produces, but standalone and without changing the
        session focus or signpost stack — a read-only 'show me the meaning of this'."""
        ctx = session.local_cortex
        target = (data.get("id") or data.get("key")
                  or session.last_written_id or session.get_context("focus", "")).strip()
        if not target:
            return _err(rid, -32602, "view requires 'id' or a focus/last-written atom")
        resolved = self._resolve_target(target, session, ctx.stream(10)) or target
        if session.consciousness is None:
            return _err(rid, -32001, "consciousness engine unavailable")
        result = session.consciousness.generate_view(resolved, allowed_scopes=scopes)
        if isinstance(result, dict) and "error" in result:
            return _err(rid, -32002, result["error"])
        return _ok(rid, result)

    def _handle_dive_look(self, rid, data, session, scopes) -> dict:
        ctx = session.local_cortex

        # Signpost navigation: bare number resolves to stored signpost key
        signpost_idx = data.get("signpost")
        target = data.get("id", "")

        if signpost_idx is not None:
            stored = session.get_context("last_signposts") or []
            idx = int(signpost_idx)
            if 0 <= idx < len(stored):
                target = stored[idx]["key"]
            else:
                return _err(rid, -32602, f"No signpost {idx}. Run 'look' first.")

        if not target:
            target = session.get_context("focus", "$origin")

        history = ctx.stream(10)
        resolved = self._resolve_target(target, session, history) or target

        nucleus = getattr(session, 'nucleus', None)
        focus   = self._get_display_focus(session)
        if focus and not self._passes_display_focus(resolved, focus, ctx, nucleus):
            return _err(rid, -32002, f"Atom not in current focus: '{target}'")

        session.set_context("focus", resolved)
        result = session.consciousness.generate_view(resolved, allowed_scopes=scopes)

        if "error" in result:
            return _err(rid, -32002, result["error"])

        # Apply display focus to signposts
        if focus:
            result["signposts"] = [
                sp for sp in result.get("signposts", [])
                if self._passes_display_focus(sp["key"], focus, ctx, nucleus)
            ]

        # Persist signpost index for number navigation
        session.set_context("last_signposts",
            [{"key": sp["key"], "alias": sp.get("alias")}
             for sp in result.get("signposts", [])])

        # Enrich: associations + resonance via the same pipeline as kernel.associate
        _sess  = self._get_scope_state(session)
        axis   = data.get("axis") or _sess.get("axis") or None
        scope  = int(data.get("scope") or _sess.get("scope") or 2)
        assoc  = ctx.associate(resolved, axis=axis, scope=scope, allowed_scopes=scopes)
        result["associations"] = assoc.get("associations", [])

        # Annotate resonance items with a readable via_alias
        resonance = assoc.get("resonance", [])
        for r in resonance:
            via_key = r.get("via", "")
            via_aliases = ctx.get_aliases_by_key(via_key) if via_key else []
            r["via_alias"] = via_aliases[0] if via_aliases else via_key[:12]
        result["resonance"] = resonance

        # Cosmos graph format (nodes + links for 3D visualization)
        content       = ctx.get_chunk(resolved) or ""
        focal_aliases = ctx.get_aliases_by_key(resolved)
        focal_info    = {
            "key":     resolved,
            "content": content,
            "preview": content[:50],
            "alias":   focal_aliases[0] if focal_aliases else None,
        }
        result["cosmos"] = self._format_associate_cosmos(
            focal_info, axis, assoc, {"status": "unavailable"}, ctx
        )

        # Attach active_time from session (consumed by UI; consciousness layer
        # does not yet filter by time, so it is passed as context metadata only)
        active_time = data.get("time") or session.get_context("active_time")
        if active_time:
            result["active_time"] = active_time

        return _ok(rid, result)

    def _handle_dive_out(self, rid, data, session, scopes) -> dict:
        target = data.get("id", "")
        if not target:
            target = session.get_context("focus", "$origin")

        history = session.local_cortex.stream(10)
        resolved = self._resolve_target(target, session, history) or target

        result = session.consciousness.zoom_out(resolved, allowed_scopes=scopes)
        return _ok(rid, result)

    # ------------------------------------------------------------------
    # Sets
    # ------------------------------------------------------------------

    def _handle_set_add(self, rid, data, session, ctx) -> dict:
        name = data.get("name", "")
        target = data.get("id", "")
        if not name or not target:
            return _err(rid, -32602, "set.add requires 'name' and 'id'")
        # 'ws:' (Harmonia workspace tracking, reclaimed by the boot orphan scan) and
        # 'wf:' (named workflow definitions) are reserved set-name prefixes.
        if name.startswith("ws:") or name.startswith("wf:"):
            return _err(rid, -32602,
                        f"Set name prefix '{name.split(':', 1)[0]}:' is reserved for internal use.")
        nucleus = getattr(session, 'nucleus', None)
        # An ontology / shared-set membership MUST live in the nucleus so EVERY session — guests
        # included — can see it. resolve_alias() is local-first, so when a spurious local
        # "Conceptual hub" proto-word shadows the real nucleus content atom for the same alias
        # (e.g. a cross-file set.add whose target is defined in another pack), the membership
        # would land in the writer's PRIVATE cortex: visible to admin (all-scope/librarian read)
        # but invisible to guests, which merge scoped-local + UNSCOPED-NUCLEUS only — the empty
        # cuisine/pairing sets. For an ONTOLOGY writer (librarian: boot pack-load, onto.reload),
        # resolve the target against the NUCLEUS first and, if it's a real nucleus atom, add
        # there. Regular users keep local-first (their set.add targets their own cell atoms, and
        # they cannot write the nucleus anyway).
        _is_onto_writer = "role:librarian" in (getattr(session, "active_scopes", None) or [])
        key = None
        if _is_onto_writer and nucleus:
            _nk = nucleus.core.get_key_by_alias(target)
            if _nk and nucleus.core.get_chunk_raw(_nk):
                key = _nk
                nucleus.add_to_set(name, key)
        if key is None:
            key = ctx.resolve_alias(target) or target
            _in_nucleus = bool(nucleus and nucleus.core.get_chunk_raw(key))
            if _in_nucleus:
                nucleus.add_to_set(name, key)
            else:
                ctx.add_to_set(name, key)
        _in_nucleus = bool(nucleus and nucleus.core.get_chunk_raw(key))
        # Weave the Atom's own content through the unified post-write hook.
        # (Atom may have been bulk-imported without prior weaving; this is idempotent
        # if it was already weaved at write time.)
        _atom_raw = None
        try:
            if _in_nucleus and nucleus:
                _atom_raw = nucleus.core.get_chunk_raw(key)
            elif hasattr(ctx, 'get_chunk_raw'):
                _atom_raw = ctx.get_chunk_raw(key)
        except Exception:
            pass
        _atom_text = ""
        if _atom_raw:
            _atom_text = (_atom_raw.get("content", "")
                          if isinstance(_atom_raw, dict) else str(_atom_raw))
        if _atom_text:
            self._post_write(session, _in_nucleus, key, _atom_text,
                             f"sys.weaver:s.add:{key[:20]}")
        return _ok(rid, {"status": "added", "set": name, "key": key})

    def _handle_set_rm(self, rid, data, ctx) -> dict:
        name = data.get("name", "")
        target = data.get("id", "")
        if not name or not target:
            return _err(rid, -32602, "set.rm requires 'name' and 'id'")
        key = ctx.resolve_alias(target) or target
        ctx.remove_from_set(name, key)
        return _ok(rid, {"status": "removed", "set": name, "key": key})

    def _handle_set_ls(self, rid, data, ctx, scopes, session=None) -> dict:
        name = data.get("name", "")
        if not name:
            # No-arg: list all user-defined set names
            names = ctx.list_set_names()
            return _ok(rid, {"sets": names, "count": len(names)})
        members = ctx.list_set(name, allowed_scopes=scopes)
        # Fallback: if no members found and name lacks "set:" prefix, retry with it.
        if not members and not name.startswith("set:"):
            members = ctx.list_set(f"set:{name}", allowed_scopes=scopes)
            if members:
                name = f"set:{name}"
        # Group-space fallback: a set shared into the caller's group lives in the
        # group engine, not the local cortex. Merge its members (scope-gated),
        # deduped by key, so a member can list a shared set.
        group_engines = self._member_group_engines(session, scopes) if session else []
        if group_engines:
            _seen = {m["key"] for m in members}
            for _gid, _ge in group_engines:
                for gm in _ge.list_set(name):
                    if gm["key"] not in _seen:
                        _seen.add(gm["key"])
                        members.append(gm)
        if session:
            nucleus = getattr(session, 'nucleus', None)
            focus   = self._get_display_focus(session)
            if focus:
                members = [m for m in members
                           if self._passes_display_focus(m["key"], focus, ctx, nucleus)]
        # Cursor pagination: page the member list, then enrich only the window.
        window, page = _paginate(members, data.get("limit"), data.get("cursor"),
                                 default=20, max_limit=200)
        for m in window:
            aliases = ctx.get_aliases_by_key(m["key"])
            if not aliases and group_engines:
                for _gid, _ge in group_engines:
                    aliases = _ge.get_aliases_by_key(m["key"])
                    if aliases:
                        break
            m["alias"] = aliases[0] if aliases else None
        return _ok(rid, {"set": name, "members": window, "count": len(window), "page": page})

    def _handle_set_clear(self, rid, data, ctx) -> dict:
        name = data.get("name", "")
        if not name:
            return _err(rid, -32602, "set.clear requires 'name'")
        result = ctx.clear_set(name)
        return _ok(rid, result)

    def _handle_set_op(self, rid, data, ctx) -> dict:
        op = data.get("op", "")
        res = data.get("result", "")
        a = data.get("a", "")
        b = data.get("b", "")
        if not all([op, res, a, b]):
            return _err(rid, -32602, "set.op requires 'op', 'result', 'a', 'b'")
        if op not in ("union", "isect", "diff"):
            return _err(rid, -32602, "set.op 'op' must be union|isect|diff")
        members = ctx.set_operation(op, res, a, b)
        return _ok(rid, {"result_set": res, "members": members})

    # ------------------------------------------------------------------
    # JCL (job.*)
    # ------------------------------------------------------------------

    def _handle_job_submit(self, rid, data, session) -> dict:
        scopes = session.active_scopes
        if "scope:sys:admin" not in scopes and "role:librarian" not in scopes:
            return _err(rid, -32003, "job.submit requires admin or librarian role")
        if not self.jcl_worker or not JCLJob or not JCLStep:
            return _err(rid, -32002, "JCL worker not available")
        steps_raw = data.get("steps", [])
        if not steps_raw:
            return _err(rid, -32602, "job.submit requires 'steps'")
        steps = [
            JCLStep(method=s["method"], params=s.get("params", {}), cmd=s.get("cmd", ""))
            for s in steps_raw if s.get("method")
        ]
        if not steps:
            return _err(rid, -32602, "No valid steps in job submission")
        # Defense-in-depth: reject privileged/recursive methods inside a batch
        # (job control, sys.su, user/group admin, auth, destructive onto ops).
        try:
            from lib.akasha.jcl.validator import validate_steps as _validate_steps
            _valid, _vmsg = _validate_steps(steps)
            if not _valid:
                return _err(rid, -32003, _vmsg)
        except ImportError:
            pass
        # Optional slice-3 scheduling declarations: PERT dependencies (this job waits
        # for the named job_ids), bounded retry, and a soft wall-clock budget. All
        # bounded at admission so a single job cannot wedge or hog the one worker.
        _JOB_MAX_RETRIES = 8       # mirrors worker._MAX_RETRIES_CEILING
        _JOB_MAX_TIMEOUT = 3600.0  # 1 h soft ceiling
        depends_on = data.get("depends_on") or []
        if isinstance(depends_on, str):
            depends_on = [depends_on]
        depends_on = [str(d) for d in depends_on]
        # Dependencies may only reference the submitter's OWN jobs (unless admin) — a
        # cross-owner dep would let one client couple its scheduling to another's job.
        is_admin = "scope:sys:admin" in session.active_scopes
        if depends_on and not is_admin:
            for dep_id in depends_on:
                dep = self.jcl_worker.get_job(dep_id) if self.jcl_worker else None
                if dep is not None and dep.owner != session.client_id:
                    return _err(rid, -32003,
                                "depends_on may only reference your own jobs.")
        try:
            max_retries = min(max(0, int(data.get("max_retries", 0))), _JOB_MAX_RETRIES)
        except (TypeError, ValueError):
            max_retries = 0
        timeout_s = data.get("timeout_s")
        try:
            timeout_s = float(timeout_s) if timeout_s is not None else None
            if timeout_s is not None:
                timeout_s = max(0.0, min(timeout_s, _JOB_MAX_TIMEOUT))
        except (TypeError, ValueError):
            timeout_s = None
        job = JCLJob(
            owner=session.client_id,
            label=data.get("label", ""),
            steps=steps,
            fail_fast=bool(data.get("fail_fast", True)),
            depends_on=depends_on,
            max_retries=max_retries,
            timeout_s=timeout_s,
        )
        # A user-submitted batch requires consistency as a set — Class 2.
        self.harmonia.submit_job(job, job_class=CLASS_BATCH_ATOM)
        return _ok(rid, {"job_id": job.job_id, "label": job.label,
                         "step_count": job.step_count, "status": job.status,
                         "depends_on": job.depends_on})

    def _handle_job_ls(self, rid, data, session) -> dict:
        if not self.jcl_worker:
            return _ok(rid, {"summary": {}, "jobs": [], "queue_depth": 0})
        is_admin     = "scope:sys:admin" in session.active_scopes
        owner_filter = data.get("owner") if is_admin else session.client_id
        all_jobs     = self.jcl_worker.list_jobs(owner=owner_filter or None)

        from collections import Counter
        counts = Counter(j.status for j in all_jobs)

        show_all    = str(data.get("all", "")).lower() in ("true", "1", "yes")
        status_filt = data.get("status", "").strip().upper() or None
        n_done      = max(0, int(data.get("n_done", 10)))

        if show_all or status_filt:
            visible = [j for j in all_jobs if not status_filt or j.status == status_filt]
        else:
            # Default: all active + last n_done completed jobs
            active  = [j for j in all_jobs if j.status in ("RUNNING", "PENDING", "FAILED", "CANCELLED")]
            done    = [j for j in all_jobs if j.status == "DONE"][:n_done]
            visible = active + done

        return _ok(rid, {
            "summary": {
                "running":   counts.get("RUNNING", 0),
                "pending":   counts.get("PENDING", 0),
                "done":      counts.get("DONE", 0),
                "failed":    counts.get("FAILED", 0),
                "cancelled": counts.get("CANCELLED", 0),
            },
            "queue_depth": self.jcl_worker.queue_depth(),
            "showing":     f"{len(visible)}/{len(all_jobs)} (add all=true to see all)",
            "jobs":        [_job_to_dict(j, brief=True) for j in visible],
        })

    def _handle_job_stat(self, rid, data, session) -> dict:
        job_id = data.get("job_id", "").strip()
        if not job_id:
            return _err(rid, -32602, "job.stat requires 'job_id'")
        if not self.jcl_worker:
            return _err(rid, -32002, "JCL worker not available")
        job = self.jcl_worker.get_job(job_id)
        if not job:
            return _err(rid, -32002, f"Job '{job_id}' not found")
        if job.owner != session.client_id and "scope:sys:admin" not in session.active_scopes:
            return _err(rid, -32003, "Permission denied")
        return _ok(rid, _job_to_dict(job, brief=False))

    def _handle_job_cancel(self, rid, data, session) -> dict:
        scopes = session.active_scopes
        if "scope:sys:admin" not in scopes and "role:librarian" not in scopes:
            return _err(rid, -32003, "job.cancel requires admin or librarian role")
        job_id = data.get("job_id", "").strip()
        if not job_id:
            return _err(rid, -32602, "job.cancel requires 'job_id'")
        if not self.jcl_worker:
            return _err(rid, -32002, "JCL worker not available")
        cancelled = self.jcl_worker.cancel(job_id, requester=session.client_id)
        return _ok(rid, {"cancelled": cancelled, "job_id": job_id})

    # ------------------------------------------------------------------
    # Workflow (workflow.*) — a stored CSL script run as an orchestrated JCL job.
    #
    # Minimal reception layer (jcl/workflow_vocab). A workflow is one executable
    # atom whose body is a CSL script; running it submits ONE bounded JCL job with a
    # single `csl.run` step, so it inherits the whole orchestration stack (priority,
    # bounded retry/timeout, single-route guard, workspace rollback). Step-granular
    # DAG projection (ref:therefore/ref:if traversal, $var→edges, conditions) is the
    # post-launch work the reserved vocabulary is there to receive.
    # ------------------------------------------------------------------

    def _handle_workflow_def(self, rid, data, session, ctx) -> dict:
        name   = (data.get("name") or "").strip()
        script = data.get("script") or ""
        if not name or not script:
            return _err(rid, -32602, "workflow.def requires 'name' and 'script'")
        # Reject only genuine SYNTAX errors at definition time (tokenize/parse). We do
        # NOT run the semantic method-existence validator here: it loads its own
        # ConceptRegistry which can differ from the live kernel's, producing false
        # "unknown method" rejections for perfectly valid concept-model calls. Real
        # method/param errors surface at run time via csl.run.
        try:
            from lib.akasha.csl import tokenize, parse
            parse(tokenize(script))
        except ImportError:
            pass
        except Exception as _pe:
            return _err(rid, -32602, f"workflow CSL syntax error: {_pe}")
        cid = session.client_id
        key = ctx.put_chunk(
            content=script,
            meta={"type": _wf.META_WORKFLOW, "name": name,
                  "description": data.get("description", "")},
            author=cid,
            scopes=[_wf.SCOPE_EXECUTABLE, f"owner:user_{cid}", f"view:user_{cid}"],
        )
        ctx.set_alias(key, f"{_wf.WF_ALIAS_PREFIX}{name}")
        return _ok(rid, {"status": "defined", "name": name, "key": key,
                         "alias": f"{_wf.WF_ALIAS_PREFIX}{name}"})

    def _handle_workflow_run(self, rid, data, session, ctx) -> dict:
        # workflow.run submits a JCL job → same gate as job.submit.
        scopes = session.active_scopes
        if "scope:sys:admin" not in scopes and "role:librarian" not in scopes:
            return _err(rid, -32003, "workflow.run requires admin or librarian role")
        if not self.jcl_worker or not JCLJob or not JCLStep:
            return _err(rid, -32002, "JCL worker not available")
        name = (data.get("name") or "").strip()
        if not name:
            return _err(rid, -32602, "workflow.run requires 'name'")
        key = ctx.resolve_alias(f"{_wf.WF_ALIAS_PREFIX}{name}")
        if not key:
            return _err(rid, -32001, f"Workflow '{name}' not found.")
        meta = ctx.get_meta(key) or {}
        if meta.get("type") != _wf.META_WORKFLOW:
            return _err(rid, -32001, f"'{name}' is not a workflow definition.")
        script = ctx.get_chunk(key) or ""
        if not script:
            return _err(rid, -32001, f"Workflow '{name}' has no script body.")
        # One bounded JCL job, one csl.run step: the CSL runtime resolves the script's
        # named $vars inline; Harmonia provides the orchestration around it.
        job = JCLJob(
            owner=session.client_id,
            label=f"wf:{name}",
            steps=[JCLStep(method="csl.run", params={"script": script})],
            fail_fast=True,
        )
        self.harmonia.submit_job(job, job_class=CLASS_BATCH_ATOM)
        return _ok(rid, {"status": "submitted", "workflow": name,
                         "job_id": job.job_id, "job_label": job.label})

    def _handle_workflow_ls(self, rid, data, session, ctx) -> dict:
        rows = ctx.get_aliases_by_pattern(f"{_wf.WF_ALIAS_PREFIX}%") or []
        out = []
        for r in rows:
            alias = r.get("alias") if isinstance(r, dict) else r
            key   = r.get("key") if isinstance(r, dict) else ctx.resolve_alias(alias)
            meta  = (ctx.get_meta(key) or {}) if key else {}
            if meta.get("type") == _wf.META_WORKFLOW:
                out.append({"name": meta.get("name", alias[len(_wf.WF_ALIAS_PREFIX):]),
                            "alias": alias, "description": meta.get("description", "")})
        return _ok(rid, {"workflows": out, "count": len(out)})

    def _handle_workflow_get(self, rid, data, session, ctx) -> dict:
        name = (data.get("name") or "").strip()
        if not name:
            return _err(rid, -32602, "workflow.get requires 'name'")
        key = ctx.resolve_alias(f"{_wf.WF_ALIAS_PREFIX}{name}")
        if not key:
            return _err(rid, -32001, f"Workflow '{name}' not found.")
        meta = ctx.get_meta(key) or {}
        return _ok(rid, {"name": name, "key": key,
                         "description": meta.get("description", ""),
                         "script": ctx.get_chunk(key) or ""})

    def _handle_workflow_rm(self, rid, data, session, ctx) -> dict:
        name = (data.get("name") or "").strip()
        if not name:
            return _err(rid, -32602, "workflow.rm requires 'name'")
        alias = f"{_wf.WF_ALIAS_PREFIX}{name}"
        key = ctx.resolve_alias(alias)
        if not key:
            return _err(rid, -32001, f"Workflow '{name}' not found.")
        meta = ctx.get_meta(key) or {}
        if meta.get("type") != _wf.META_WORKFLOW:
            return _err(rid, -32001, f"'{name}' is not a workflow definition.")
        # Unbind the wf:<name> alias — the workflow disappears from ls/run/get. The
        # (content-addressed, now-unreferenced) definition atom is harmless residue.
        ctx.delete_alias(alias)
        return _ok(rid, {"status": "removed", "name": name})

    # ------------------------------------------------------------------
    # Locale (locale.*)
    # ------------------------------------------------------------------

    def _handle_locale_get(self, rid, session) -> dict:
        loc = session.locale
        return _ok(rid, {
            "primary":   loc.primary,
            "supported": loc.supported,
            "priority":  loc.get_priority_list(),
        })

    def _handle_locale_set(self, rid, data, session) -> dict:
        """
        locale.set  primary=<code>  [supported=<code>,<code>,...]

        If only 'primary' is given, the code is moved to the front of the
        existing supported list (added if absent).
        If 'supported' is given, it replaces the full supported list
        (primary is always prepended automatically).
        """
        primary   = data.get("primary", "").strip().lower()
        supported = data.get("supported", "")

        if not primary and not supported:
            return _err(rid, -32602, "locale.set requires 'primary' and/or 'supported'")

        loc = session.locale

        if supported:
            codes = [c.strip().lower() for c in supported.replace(",", " ").split() if c.strip()]
            if not codes:
                return _err(rid, -32602, "locale.set: 'supported' must be a non-empty list")
            loc.supported = codes

        if primary:
            loc.set_primary(primary)

        session.save_locale()
        return _ok(rid, {
            "primary":   loc.primary,
            "supported": loc.supported,
            "priority":  loc.get_priority_list(),
        })

    # ------------------------------------------------------------------
    # CSL (csl.*)
    # ------------------------------------------------------------------

    def _handle_csl(self, rid, method: str, data: dict, session) -> dict:
        try:
            from lib.akasha.csl import tokenize, parse, validate, compile_script, CslRuntime
        except ImportError as exc:
            return _err(rid, -32603, f"CSL runtime not available: {exc}")

        import os as _os

        # Resolve input — inline CSL text or path to a .csl file
        source = (data.get("script") or data.get("source") or "").strip()
        if not source:
            return _err(rid, -32602, "csl requires 'script' (inline CSL text or path to a .csl file)")

        from_file = None
        if source.endswith(".csl") and "\n" not in source:
            from_file = source
            try:
                with open(from_file, "r", encoding="utf-8") as fh:
                    source = fh.read().strip()
            except OSError as exc:
                return _err(rid, -32602, f"Cannot read CSL file '{from_file}': {exc}")

        # ── Parse ─────────────────────────────────────────────────────────
        try:
            tokens = tokenize(source)
            ast    = parse(tokens)
        except Exception as exc:
            return _err(rid, -32602, f"CSL parse error: {exc}")

        # ── csl.check — validation only ───────────────────────────────────
        if method == "csl.check":
            errors = validate(ast)
            return _ok(rid, {
                "valid": not any(e.level == "error" for e in errors),
                "errors": [
                    {
                        "line":       e.line,
                        "col":        e.col,
                        "error":      e.error,
                        "parameter":  e.parameter,
                        "suggestion": e.suggestion,
                        "level":      e.level,
                    }
                    for e in errors
                ],
            })

        # Validate before compile/run
        errors      = validate(ast)
        hard_errors = [e for e in errors if e.level == "error"]
        if hard_errors:
            return _err(
                rid, -32602,
                f"CSL validation failed: {hard_errors[0].error} (line {hard_errors[0].line})",
            )

        calls = compile_script(ast)

        # ── csl.build — transpile to .ak ──────────────────────────────────
        if method == "csl.build":
            ak_lines = _csl_calls_to_ak(calls)
            out_path = (data.get("out") or "").strip() or None
            if out_path:
                try:
                    with open(out_path, "w", encoding="utf-8") as fh:
                        fh.write(ak_lines)
                except OSError as exc:
                    return _err(rid, -32603, f"Cannot write .ak file '{out_path}': {exc}")
            return _ok(rid, {
                "ak":           ak_lines,
                "call_count":   len(calls),
                "source_lines": len(source.splitlines()),
                "out":          out_path,
            })

        # ── csl / csl.run — check + build + execute via CslRuntime ────────
        # begin_batch() / set_sync_fast() on the DB WriteQueue threads so
        # each commit is instant (synchronous=OFF) without losing cross-thread
        # read visibility.  Restored in the finally block.
        nucleus   = getattr(session, 'nucleus', None)
        _nuc_core = nucleus.core if nucleus else None
        _loc_core = getattr(getattr(session, 'local_cortex', None), 'core', None)
        for _core in (_nuc_core, _loc_core):
            if _core is not None:
                try:
                    _core.begin_batch()
                    _core.set_sync_fast()
                except Exception:
                    pass
        try:
            runtime = CslRuntime(session, dispatcher=self)
            results = runtime.run(calls)
        finally:
            for _core in (_nuc_core, _loc_core):
                if _core is not None:
                    try:
                        _core.end_batch()
                        _core.set_sync_normal()
                    except Exception:
                        pass
        return _ok(rid, {
            "results": [
                {
                    "method":     r.method,
                    "result":     r.result,
                    "error":      r.error,
                    "assigns_to": r.assigns_to,
                }
                for r in results
            ]
        })

    # ------------------------------------------------------------------
    # Onboarding (sys.onboarding.*)
    # ------------------------------------------------------------------

    def _handle_onboarding_seed(self, rid, data, session) -> dict:
        """Load sample seeds for app_name on the user's first login to that app."""
        app_name = (data or {}).get("app", "").strip()
        if not app_name:
            return _err(rid, -32602, "sys.onboarding.seed requires 'app'")
        if app_name in self.iam.get_onboarded_apps(session.client_id):
            return _ok(rid, {"already_done": True, "seeds_loaded": 0, "titles": []})
        from pathlib import Path
        from .seeding import SeedManager
        seeds_root = Path(__file__).resolve().parent.parent.parent / "seeds"
        result = SeedManager(seeds_root).seed_app(session, app_name)
        self.iam.mark_onboarded(session.client_id, app_name)
        return _ok(rid, result)

    # ------------------------------------------------------------------
    # Log (log.*)
    # ------------------------------------------------------------------

    def _handle_log_new(self, rid, data, session) -> dict:
        name = data.get("name", "")
        if not name:
            return _err(rid, -32602, "log.new requires 'name'")
        try:
            concept = LogConcept(session)
            res = concept.op_new(name=name)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_log_ls(self, rid, session) -> dict:
        try:
            concept = LogConcept(session)
            res = concept.op_ls()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_log_checkpoint(self, rid, data, session) -> dict:
        concept = LogConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active log. Use log.new first.")
        try:
            res = concept.op_checkpoint(note=data.get("note") or None)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_log_annotate(self, rid, data, session) -> dict:
        text = data.get("text", "")
        if not text:
            return _err(rid, -32602, "log.annotate requires 'text'")
        concept = LogConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active log. Use log.new first.")
        try:
            res = concept.op_annotate(text=text)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_log_replay(self, rid, session) -> dict:
        concept = LogConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active log. Use log.new first.")
        try:
            res = concept.op_replay()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_log_read(self, rid, session) -> dict:
        concept = LogConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active log. Use log.new first.")
        try:
            res = concept.op_read()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_log_rm(self, rid, session) -> dict:
        concept = LogConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active log. Use log.new first.")
        try:
            res = concept.op_delete()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    # ------------------------------------------------------------------
    # Whiteboard (wb.*)
    # ------------------------------------------------------------------

    def _handle_wb_new(self, rid, data, session) -> dict:
        name = data.get("name", "")
        if not name:
            return _err(rid, -32602, "wb.new requires 'name'")
        try:
            res = WhiteboardConcept(session).op_new(name=name)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_wb_pin(self, rid, data, session) -> dict:
        concept = data.get("concept", "")
        if not concept:
            return _err(rid, -32602, "wb.pin requires 'concept'")
        try:
            res = WhiteboardConcept(session).op_pin(concept=concept)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_wb_unpin(self, rid, data, session) -> dict:
        concept = data.get("concept", "")
        if not concept:
            return _err(rid, -32602, "wb.unpin requires 'concept'")
        try:
            res = WhiteboardConcept(session).op_unpin(concept=concept)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_wb_focus(self, rid, data, session) -> dict:
        name = data.get("name", "")
        if not name:
            return _err(rid, -32602, "wb.focus requires 'name'")
        try:
            res = WhiteboardConcept(session).op_focus(name=name)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_wb_ls(self, rid, session) -> dict:
        try:
            res = WhiteboardConcept(session).op_list()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_wb_show(self, rid, session) -> dict:
        try:
            res = WhiteboardConcept(session).op_show()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_wb_rm(self, rid, data, session) -> dict:
        name = data.get("name", "")
        if not name:
            return _err(rid, -32602, "wb.rm requires 'name'")
        try:
            res = WhiteboardConcept(session).op_delete(name=name)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    # ------------------------------------------------------------------
    # Cross-concept intersection (sys.cross.*)
    # ------------------------------------------------------------------

    def _resolve_concept_to_set_name(self, concept: str, session) -> Optional[str]:
        """Maps a concept name, slot name, or set: path to its active collection set name.

        Resolution order:
          1. Raw set: prefix — used as-is.
          2. Space slot — check the session Space's mounted instances by slot name
             or model prefix (requires instance.mount to have been called).
          3. ConceptRegistry — use CONTEXT_KEY_ACTIVE for any registered model prefix
             to find the active concept root set.
          4. Legacy hardcoded fallback — note, log (pre-registry naming convention).
        """
        # 1. Direct set name
        if concept.startswith("set:"):
            return concept

        # 2. Space: check mounted instances by slot name or model prefix
        try:
            from lib.akasha.session.space import SpaceConcept as _SpaceConcept
            _space = _SpaceConcept(session)
            if _space.concept_id:
                for slot_info in _space._slot_atoms():
                    meta = slot_info["meta"]
                    if meta.get("slot") == concept or meta.get("model") == concept:
                        cid = meta.get("concept_id")
                        if cid:
                            return f"set:concept:{cid}"
        except Exception:
            pass

        # 3. Registry: CONTEXT_KEY_ACTIVE → session context → set name
        if _concept_registry:
            cls = _concept_registry.get_class(concept)
            if cls:
                ctx_key = getattr(cls, "CONTEXT_KEY_ACTIVE", None)
                if ctx_key:
                    root_id = session.get_context(ctx_key)
                    if root_id:
                        return f"set:concept:{root_id}"

        # 4. Legacy fallback (pre-BaseConcept naming conventions)
        if concept == "note":
            root = session.get_context("active_note_root")
            return f"set:note:{root}" if root else None
        if concept == "log":
            root = session.get_context("active_log_root")
            return f"set:log:{root}" if root else None

        return None

    def _handle_cross_query(self, rid, data, session, ctx, scopes) -> dict:
        concepts_raw = data.get("concepts", [])
        if isinstance(concepts_raw, str):
            concepts = concepts_raw.split()
        else:
            concepts = list(concepts_raw)

        if not concepts:
            return _err(rid, -32602, "sys.cross.query requires 'concepts' (list of concept names)")

        set_names: List[str] = []
        resolved_names: List[str] = []
        for c in concepts:
            sname = self._resolve_concept_to_set_name(c, session)
            if sname:
                set_names.append(sname)
                resolved_names.append(c)

        if not set_names:
            return _err(rid, -32002, "None of the specified concepts have an active root in this session.")

        focal_raw = data.get("id", "") or session.get_context("focus") or ""
        focal_key = focal_raw or None
        fmt = data.get("format", "raw")

        try:
            result = ctx.cross_query(set_names, resolved_names, allowed_scopes=scopes)
        except Exception as e:
            return _err(rid, -32603, f"cross_query failed: {e}")

        payload = {
            "focal":    focal_key,
            "concepts": resolved_names,
            **result,
        }

        if fmt == "cosmos":
            payload = self._format_cross_cosmos(focal_key, resolved_names, result)

        return _ok(rid, payload)

    def _handle_cross_axes(self, rid, data, session, ctx, scopes) -> dict:
        concepts_raw = data.get("concepts", [])
        if isinstance(concepts_raw, str):
            concepts = [c.strip() for c in concepts_raw.split() if c.strip()]
        else:
            concepts = [c for c in list(concepts_raw) if c]

        # No concepts specified: enumerate all registered models
        if not concepts and _concept_registry:
            concepts = list(_concept_registry.get_concept_prefixes().values())

        set_names: List[str] = []
        resolved_names: List[str] = []
        for c in concepts:
            sname = self._resolve_concept_to_set_name(c, session)
            if sname:
                set_names.append(sname)
                resolved_names.append(c)

        if not set_names:
            return _ok(rid, {"concepts": [], "available_axes": [], "recommended": None})

        try:
            result = ctx.cross_axes(set_names, resolved_names, allowed_scopes=scopes)
        except Exception as e:
            return _err(rid, -32603, f"cross_axes failed: {e}")

        return _ok(rid, result)

    def _handle_cross_atom(self, rid, data, session, ctx, scopes) -> dict:
        atom_raw = (data.get("atom") or "").strip()
        if not atom_raw:
            return _err(rid, -32602, "sys.cross.atom requires 'atom' (proto-word alias or key)")

        concepts_raw = data.get("concepts", [])
        if isinstance(concepts_raw, str):
            concepts = [c.strip() for c in concepts_raw.split() if c.strip()]
        else:
            concepts = [str(c) for c in concepts_raw if c]

        # Resolve alias (e.g. "icarus" → word:icarus key) then fall back to raw
        resolved_key = ctx.resolve_alias(atom_raw) or atom_raw

        set_names: List[str] = []
        resolved_names: List[str] = []
        for c in concepts:
            sname = self._resolve_concept_to_set_name(c, session)
            if sname:
                set_names.append(sname)
                resolved_names.append(c)

        try:
            result = ctx.cross_atom(resolved_key, set_names, resolved_names, allowed_scopes=scopes)
        except Exception as e:
            return _err(rid, -32603, f"cross.atom failed: {e}")

        return _ok(rid, {
            "atom":       resolved_key,
            "atom_query": atom_raw,
            "concepts":   resolved_names or None,
            **result,
        })

    @staticmethod
    def _format_cross_cosmos(
        focal_key: Optional[str],
        concepts: List[str],
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Formats cross_query result as a Cosmos/3D-Force-Graph ready payload."""
        nodes: List[Dict[str, Any]] = []
        links: List[Dict[str, Any]] = []
        seen: set = set()

        if focal_key and focal_key not in seen:
            nodes.append({"id": focal_key, "name": focal_key[:16], "group": "focus", "val": 20})
            seen.add(focal_key)

        for item in result.get("intersection", []):
            key = item["key"]
            if key not in seen:
                nodes.append({
                    "id":         key,
                    "name":       item["preview"],
                    "group":      "cross",
                    "val":        int(item["weight"] * 15) + 5,
                    "present_in": item["present_in"],
                })
                seen.add(key)
            if focal_key:
                links.append({"source": focal_key, "target": key, "type": "cross"})

        return {
            "focal":    focal_key,
            "concepts": concepts,
            "nodes":    nodes,
            "links":    links,
            "count":    result.get("count", len(nodes)),
        }

    # ------------------------------------------------------------------
    # Jataka
    # ------------------------------------------------------------------

    # ── dream — the asynchronous incubation / bridge-proposer ─────────────────────────────
    #
    # Unlike assoc (1-hop, high-confidence gap-fill) and sim/node.sim (rank what is already
    # near), dream finds atoms that are NEAR in meaning/emotion but FAR in the explicit graph
    # — the connections the graph is missing — and stages them as tentative (tent:) links for
    # a HUMAN to confirm. It runs as a LOW-priority background JCL job ("sleep on it"): the
    # first call submits and returns "dreaming…"; a later call returns the staged candidates.
    _DREAM_REL = "tent:calc:hidden_affinity"

    def _dream_pending(self, ctx, focus_key, scopes):
        """The tent: candidates already staged on a focus (a completed dream awaiting approval)."""
        out = []
        try:
            raw = ctx.core.get_adjacent_links(focus_key) or []
        except Exception:
            raw = []
        for l in raw:
            dst = l.get("dst") if isinstance(l, dict) else (l[0] if l else None)
            rel = l.get("rel") if isinstance(l, dict) else (l[1] if len(l) > 1 else "")
            if not dst or not str(rel).startswith("tent:"):
                continue
            if scopes and not ctx.check_access(dst, scopes):
                continue
            w = float(l.get("w", 0.0) or 0.0) if isinstance(l, dict) else 0.0
            al = ctx.get_aliases_by_key(dst)
            out.append({"dst": dst, "alias": al[0] if al else None,
                        "score": round(w, 4), "rel": rel,
                        "preview": (ctx.get_chunk(dst) or "")[:60]})
        out.sort(key=lambda c: c["score"], reverse=True)
        return out

    def _handle_dream(self, rid, data, session, ctx, scopes, history) -> dict:
        """dream id= [boldness=] [reach=] [again=yes] — incubate hidden connections for a
        focus atom, asynchronously. First call submits a background job and returns
        status="dreaming"; call again later to get status="ready" with the staged candidates
        (near-in-meaning, far-in-graph) for you to confirm with dream.confirm. Human approval
        is mandatory — dream never links on its own. Degrades to a synchronous run if JCL is
        unavailable."""
        target = (data.get("id") or session.get_context("dream:last") or "").strip()
        if not target:
            return _err(rid, -32602, "dream requires 'id' (the atom to dream around)")
        focus = self._resolve_target(target, session, history) or ctx.resolve_alias(target) or target
        if (ctx.get_scoped_chunk(focus, scopes) if scopes else ctx.get_chunk(focus)) is None:
            return _err(rid, -32002, f"Atom '{focus}' not found or access denied")
        session.set_context("dream:last", focus)
        again = str(data.get("again", "")).lower() in ("yes", "true", "1")

        # Poll an in-flight job for this focus.
        job_id = session.get_context(f"dream:{focus}")
        job = self.jcl_worker.get_job(job_id) if (job_id and self.jcl_worker) else None
        if job and job.status in ("PENDING", "RUNNING") and not again:
            elapsed = round(time.time() - (job.started_at or job.submitted_at), 1)
            return _ok(rid, {"status": "dreaming", "focus": focus, "job_id": job_id,
                             "elapsed_s": elapsed,
                             "hint": "still incubating — come back with `dream id=` later"})

        # A finished dream: staged tent: candidates awaiting approval.
        if not again:
            pending = self._dream_pending(ctx, focus, scopes)
            if pending:
                return _ok(rid, {"status": "ready", "focus": focus,
                                 "candidates": pending, "count": len(pending),
                                 "hint": "approve with `dream.confirm dst=` or drop with `dream.forget`"})
            if job and job.status == "FAILED":
                session.set_context(f"dream:{focus}", None)
                return _ok(rid, {"status": "failed", "focus": focus, "error": job.error})

        # Nothing pending (or again=yes) → start a fresh dream.
        if again:
            for c in self._dream_pending(ctx, focus, scopes):
                try:
                    ctx.remove_link(focus, c["dst"], c["rel"])
                except Exception:
                    pass
        params = {"focus": focus,
                  "boldness": float(data.get("boldness", 0.2)),
                  "reach":    float(data.get("reach", 0.5)),
                  "threshold": float(data.get("threshold", 0.12)),
                  "limit":    int(data.get("limit", 5)),
                  "scan":     int(data.get("scan", 2000))}
        # Prefer the background JCL job (the "while sleeping" tier); degrade to synchronous.
        if self.harmonia and self.jcl_worker and JCLJob and JCLStep:
            job = JCLJob(owner=session.client_id, label=f"dream:{target[:32]}",
                         steps=[JCLStep(method="dream.run", params=params)])
            self.harmonia.submit_job(job, job_class=CLASS_LINK)
            session.set_context(f"dream:{focus}", job.job_id)
            return _ok(rid, {"status": "dreaming", "focus": focus, "job_id": job.job_id,
                             "hint": "dreaming… come back with `dream id=` to see the candidates"})
        # Synchronous fallback (no JCL): compute + stage now.
        n = self._dream_stage(ctx, session, scopes, params)
        return _ok(rid, {"status": "ready", "focus": focus,
                         "candidates": self._dream_pending(ctx, focus, scopes),
                         "count": n, "note": "computed synchronously (JCL unavailable)"})

    def _handle_dream_run(self, rid, data, session, ctx, scopes) -> dict:
        """dream.run — the background computation (JCL-dispatched, internal). Computes the
        affinity-gap candidates and stages them as tent: links. Not for direct use."""
        params = {"focus": data.get("focus", ""),
                  "boldness": float(data.get("boldness", 0.2)),
                  "reach":    float(data.get("reach", 0.5)),
                  "threshold": float(data.get("threshold", 0.12)),
                  "limit":    int(data.get("limit", 5)),
                  "scan":     int(data.get("scan", 2000))}
        n = self._dream_stage(ctx, session, scopes, params)
        return _ok(rid, {"status": "dreamed", "focus": params["focus"], "staged": n})

    def _dream_stage(self, ctx, session, scopes, params) -> int:
        """Compute affinity-gap candidates for a focus and write them as tent: links."""
        focus = params["focus"]
        cands = self._dream_affinities(ctx, session, focus, scopes, params)
        author = getattr(session, "client_id", "system")
        n = 0
        for c in cands:
            try:
                ctx.put_link(focus, c["dst"], self._DREAM_REL, w=c["score"], author=author)
                n += 1
            except Exception:
                pass
        return n

    def _dream_affinities(self, ctx, session, focus, scopes, params) -> list:
        """The affinity gap: atoms NEAR in meaning/emotion/structure but FAR in the explicit
        graph. Multi-signal, scope-filtered. Conservative by default (rewards signal
        agreement and graph distance); `boldness` shifts toward a single strong signal, `reach`
        strengthens the graph-distance reward."""
        import json as _json
        boldness = max(0.0, min(params.get("boldness", 0.2), 1.0))
        reach = max(0.0, min(params.get("reach", 0.5), 2.0))
        threshold = max(0.0, params.get("threshold", 0.12))
        limit = max(1, min(int(params.get("limit", 5)), 50))
        scan = max(1, min(int(params.get("scan", 2000)), 20000))

        tensor = getattr(ctx, "tensor", None)
        nucleus = getattr(session, "nucleus", None)
        try:
            from lib.akasha.semantic_learn import get_node_model, cosine as _lcos
            node_model = get_node_model(nucleus) if nucleus is not None else None
        except Exception:
            node_model, _lcos = None, None

        def _meta_vec(key, row=None):
            try:
                raw = row if row is not None else ctx.core.get_chunk_raw(key)
                m = _json.loads(raw["meta"]) if raw and raw.get("meta") else {}
                v = m.get("semantic_vector") if isinstance(m, dict) else None
                return v if isinstance(v, list) and v else None
            except Exception:
                return None

        def _neighbors(key):
            out = set()
            try:
                for l in (ctx.get_adjacent_links(key) or []):
                    d = l[0] if not isinstance(l, dict) else l.get("dst")
                    if d:
                        out.add(d)
            except Exception:
                pass
            return out

        def _tags(nbrs):
            return {n for n in nbrs}  # neighbour set doubles as the emo:/calc: tag set for overlap

        focus_vec = _meta_vec(focus)
        focus_nbrs = _neighbors(focus)
        focus_nvec = node_model.node_vector(focus) if node_model else None
        linked = focus_nbrs | {focus}

        scored = []
        for row in (ctx.stream(limit=scan) or []):
            dst = row.get("key")
            if not dst or dst in linked:
                continue
            if scopes and not ctx.check_access(dst, scopes):
                continue
            # signals in [0,1]
            content = 0.0
            if tensor is not None and focus_vec:
                cv = _meta_vec(dst, row)
                if cv:
                    content = max(0.0, tensor.cosine(focus_vec, cv))
            struct = 0.0
            if node_model is not None and focus_nvec:
                nv = node_model.node_vector(dst)
                if nv:
                    struct = max(0.0, _lcos(focus_nvec, nv))
            dst_nbrs = _neighbors(dst)
            shared = len(focus_nbrs & dst_nbrs)
            tag = (shared / len(focus_nbrs | dst_nbrs)) if (focus_nbrs or dst_nbrs) else 0.0
            present = [s for s in (content, struct, tag) if s > 0.05]
            if not present:
                continue
            gap = 1.0 / (1.0 + shared)                       # far in the graph → near 1.0
            agreement = len(present) / 3.0
            strength_cons = (sum(present) / len(present)) * (0.5 + 0.5 * agreement)
            strength_bold = max(present)
            nearness = (1.0 - boldness) * strength_cons + boldness * strength_bold
            score = nearness * (gap ** reach)
            if score >= threshold:
                scored.append({"dst": dst, "score": round(score, 4),
                               "signals": {"content": round(content, 3),
                                           "struct": round(struct, 3),
                                           "tag": round(tag, 3)},
                               "shared_neighbours": shared})
        scored.sort(key=lambda c: c["score"], reverse=True)
        return scored[:limit]

    def _handle_dream_confirm(self, rid, data, session, ctx, scopes, history) -> dict:
        """dream.confirm dst= [src=] — promote a staged (tent:) dream link to a real link.
        Human approval of a proposed connection: the tent: prefix is stripped so the affinity
        becomes a first-class edge. `src` defaults to the last-dreamed focus."""
        src_ref = (data.get("src") or data.get("id") or session.get_context("dream:last") or "").strip()
        dst_ref = (data.get("dst") or "").strip()
        if not src_ref or not dst_ref:
            return _err(rid, -32602, "dream.confirm requires 'dst' (and 'src' or a last-dreamed focus)")
        src = self._resolve_target(src_ref, session, history) or ctx.resolve_alias(src_ref) or src_ref
        dst = ctx.resolve_alias(dst_ref) or dst_ref
        # Find the staged tent: link src→dst.
        rel = next((c["rel"] for c in self._dream_pending(ctx, src, scopes) if c["dst"] == dst), None)
        if not rel:
            return _err(rid, -32002, "no staged dream link from that focus to that atom")
        real_rel = rel[len("tent:"):] if rel.startswith("tent:") else rel
        author = getattr(session, "client_id", "system")
        try:
            ctx.remove_link(src, dst, rel)
            ctx.put_link(src, dst, real_rel, author=author)
        except Exception as exc:
            return _err(rid, -32000, f"confirm failed: {exc}")
        return _ok(rid, {"status": "confirmed", "src": src, "dst": dst, "rel": real_rel})

    def _handle_dream_forget(self, rid, data, session, ctx, scopes, history) -> dict:
        """dream.forget [dst=] [src=] [all=yes] — drop staged (tent:) dream links that did not
        resonate. Without dst=, `all=yes` clears every staged candidate on the focus."""
        src_ref = (data.get("src") or data.get("id") or session.get_context("dream:last") or "").strip()
        if not src_ref:
            return _err(rid, -32602, "dream.forget requires 'src' or a last-dreamed focus")
        src = self._resolve_target(src_ref, session, history) or ctx.resolve_alias(src_ref) or src_ref
        dst_ref = (data.get("dst") or "").strip()
        drop_all = str(data.get("all", "")).lower() in ("yes", "true", "1") or not dst_ref
        pending = self._dream_pending(ctx, src, scopes)
        dropped = 0
        for c in pending:
            if drop_all or (dst_ref and (c["dst"] == (ctx.resolve_alias(dst_ref) or dst_ref)
                                         or c["alias"] == dst_ref)):
                try:
                    ctx.remove_link(src, c["dst"], c["rel"])
                    dropped += 1
                except Exception:
                    pass
        session.set_context(f"dream:{src}", None)
        return _ok(rid, {"status": "forgotten", "src": src, "dropped": dropped})

    # ── nebula — the cartographer: inductive concept-model discovery ──────────────────────
    #
    # The third explorer (assoc=local, dream=pairwise, nebula=global). Surveys the whole
    # meaning-universe for REGIONS becoming a concept model — dense clumps of atoms that
    # independently grew the SAME schema (shared relation signature) — and PROPOSES them
    # with an inferred salient-rel profile. Like dream it runs as a LOW-priority background
    # job ("the surveyor of the universe") and only PROPOSES: a human confirms + names, which
    # plants the cluster set + rel:salient profile and emits a concept-model skeleton to review.
    # Proposals live in the nucleus vault (focus-less — nebula has no single anchor atom).

    def _nebula_cartographer(self, ctx):
        from lib.akasha.nebula import NebulaCartographer
        node_vec = None
        try:
            from lib.akasha.semantic_learn import get_node_model
            nucleus = getattr(self.manager, "shared_nucleus", None)
            nm = get_node_model(nucleus) if nucleus else None
            if nm is not None:
                node_vec = nm.node_vector
        except Exception:
            node_vec = None
        return NebulaCartographer(ctx, node_vec=node_vec)

    def _nebula_vault_key(self, session) -> str:
        return getattr(session, "client_id", "system")

    def _nebula_store(self, session, payload) -> None:
        try:
            self._nucleus().vault_store("nebula", self._nebula_vault_key(session), payload)
        except Exception:
            pass

    def _nebula_load(self, session):
        try:
            return self._nucleus().vault_retrieve("nebula", self._nebula_vault_key(session)) or {}
        except Exception:
            return {}

    def _nebula_survey(self, ctx, session, scopes, params) -> list:
        cands = self._nebula_cartographer(ctx).survey(scopes=scopes, params=params)
        self._nebula_store(session, {"candidates": cands, "params": params})
        return cands

    def _handle_nebula(self, rid, data, session, ctx, scopes, history) -> dict:
        """nebula [again=yes] [ns=] [limit=] [min_size=] [threshold=] [scan=] — survey the
        accumulated atoms for regions that are becoming a concept model (dense clumps sharing
        a relation schema), asynchronously. First call submits a background survey and returns
        status="surveying"; call again to get status="ready" with ranked candidate regions,
        each with an inferred salient-rel profile. Confirm one with `nebula.confirm id=`. The
        machine only proposes — a human names + plants the concept. Degrades to a synchronous
        run when JCL is unavailable."""
        again = str(data.get("again", "")).lower() in ("yes", "true", "1")
        params = {
            "scan":       int(data.get("scan", 4000)),
            "cluster_cap": int(data.get("cluster_cap", 600)),
            "min_size":   int(data.get("min_size", 4)),
            "limit":      int(data.get("limit", 8)),
            "threshold":  float(data.get("threshold", 0.34)),
            "salience":   float(data.get("salience", 0.0)),
        }

        # Poll an in-flight survey.
        job_id = session.get_context("nebula:job")
        job = self.jcl_worker.get_job(job_id) if (job_id and self.jcl_worker) else None
        if job and job.status in ("PENDING", "RUNNING") and not again:
            elapsed = round(time.time() - (job.started_at or job.submitted_at), 1)
            return _ok(rid, {"kind": "nebula", "status": "surveying", "job_id": job_id, "elapsed_s": elapsed,
                             "hint": "still mapping the universe — come back with `nebula` later"})

        # A finished survey: read candidates back from the vault.
        if not again:
            stored = self._nebula_load(session)
            cands = stored.get("candidates") if isinstance(stored, dict) else None
            if cands:
                return _ok(rid, {"kind": "nebula", "status": "ready", "candidates": cands, "count": len(cands),
                                 "hint": "plant one with `nebula.confirm id=<neb:…> name=<concept>`, "
                                         "or drop it with `nebula.forget id=`"})
            if job and job.status == "FAILED":
                session.set_context("nebula:job", None)
                return _ok(rid, {"kind": "nebula", "status": "failed", "error": job.error})

        # Submit a fresh survey (background), or run synchronously if JCL is unavailable.
        if self.harmonia and self.jcl_worker and JCLJob and JCLStep:
            job = JCLJob(owner=session.client_id, label="nebula:survey",
                         steps=[JCLStep(method="nebula.run", params=params)])
            self.harmonia.submit_job(job, job_class=CLASS_LINK)
            session.set_context("nebula:job", job.job_id)
            return _ok(rid, {"kind": "nebula", "status": "surveying", "job_id": job.job_id,
                             "hint": "surveying… come back with `nebula` to see candidate regions"})
        cands = self._nebula_survey(ctx, session, scopes, params)
        return _ok(rid, {"kind": "nebula", "status": "ready", "candidates": cands, "count": len(cands),
                         "note": "computed synchronously (JCL unavailable)"})

    def _handle_nebula_run(self, rid, data, session, ctx, scopes) -> dict:
        """nebula.run — the background survey (JCL-dispatched, internal). Not for direct use."""
        params = {k: data.get(k) for k in
                  ("scan", "cluster_cap", "min_size", "limit", "threshold", "salience")}
        cands = self._nebula_survey(ctx, session, scopes, params)
        return _ok(rid, {"status": "surveyed", "candidates": len(cands)})

    def _handle_nebula_forget(self, rid, data, session, ctx, scopes, history) -> dict:
        """nebula.forget [id=] [all=yes] — drop a proposed region (or all) from the survey."""
        cid = (data.get("id") or "").strip()
        stored = self._nebula_load(session)
        cands = stored.get("candidates", []) if isinstance(stored, dict) else []
        drop_all = str(data.get("all", "")).lower() in ("yes", "true", "1") or not cid
        if drop_all:
            self._nebula_store(session, {"candidates": [], "params": stored.get("params", {})})
            session.set_context("nebula:job", None)
            return _ok(rid, {"status": "forgotten", "dropped": len(cands)})
        kept = [c for c in cands if c.get("id") != cid]
        self._nebula_store(session, {"candidates": kept, "params": stored.get("params", {})})
        return _ok(rid, {"status": "forgotten", "dropped": len(cands) - len(kept)})

    def _handle_nebula_confirm(self, rid, data, session, ctx, scopes, history) -> dict:
        """nebula.confirm id=<neb:…> [name=<concept>] — the human's approval of a proposed
        region. Names the emerging concept, materialises its set (members + sys:is_a spine),
        plants the inferred salient-rel profile (reldef + rel:salient) so `resolve_salient_rels`
        picks it up, and returns a concept-model SKELETON (Python class + .ak lexicon block) to
        review and place. The machine never writes the skeleton file itself."""
        cid = (data.get("id") or "").strip()
        if not cid:
            return _err(rid, -32602, "nebula.confirm requires 'id' (a neb:… candidate id)")
        stored = self._nebula_load(session)
        cands = stored.get("candidates", []) if isinstance(stored, dict) else []
        cand = next((c for c in cands if c.get("id") == cid), None)
        if not cand:
            return _err(rid, -32002, "no such nebula candidate — run `nebula` and use its id")
        raw_name = (data.get("name") or cand.get("name") or "concept").strip().lower()
        name = re.sub(r"[^a-z0-9_]+", "_", raw_name).strip("_") or "concept"
        author = getattr(session, "client_id", "system")

        planted = {"set": name, "members": 0, "salient_rels": []}
        set_proto = None
        try:
            for mk in cand.get("members", []):
                ctx.add_to_set(name, mk)
                planted["members"] += 1
            set_proto = ctx.resolve_alias(name)
        except Exception as exc:
            log.debug("[nebula] set materialise partial: %s", exc)
        # sys:is_a spine + rel:salient profile (best-effort; the skeleton is returned regardless).
        if set_proto:
            for mk in cand.get("members", []):
                try:
                    ctx.put_link(mk, set_proto, "sys:is_a", author=author)
                except Exception:
                    pass
            for rel in cand.get("salient_rels", []):
                try:
                    reldef_key = self._nebula_ensure_reldef(ctx, rel, author)
                    if reldef_key:
                        ctx.put_link(set_proto, reldef_key, "rel:salient", author=author)
                        planted["salient_rels"].append(rel)
                except Exception:
                    pass

        # Remove the confirmed candidate from the survey.
        self._nebula_store(session, {"candidates": [c for c in cands if c.get("id") != cid],
                                     "params": stored.get("params", {})})
        skeleton = self._nebula_scaffold(name, cand)
        return _ok(rid, {"status": "planted", "name": name, "planted": planted,
                         "kind": cand.get("kind"), "skeleton": skeleton,
                         "hint": "review the skeleton, then drop the .py into lib/akasha/concepts/ "
                                 "and the .ak block into ontology/lexicon/ (onto.csl.transpile if CSL)"})

    def _nebula_ensure_reldef(self, ctx, rel, author):
        """Ensure a reldef:<rel> atom exists (aliased, in the `rels` set); return its key."""
        alias = f"reldef:{rel}"
        key = ctx.resolve_alias(alias)
        if not key:
            desc = f"{rel} — '{rel}' relation asserted between two atoms."
            key = ctx.put_chunk(content=desc, meta={"type": "lexicon:reldef", "rel": rel},
                                author=author)
            ctx.set_alias(key, alias)
        try:
            ctx.add_to_set("rels", key)
        except Exception:
            pass
        return key

    def _nebula_scaffold(self, name: str, cand: dict) -> dict:
        """Generate the concept-model skeleton (Python class + .ak lexicon block) as TEXT —
        the inductive→deductive bridge. Reviewed and placed by the human; never auto-written."""
        cls = "".join(p.capitalize() for p in name.split("_")) + "Concept"
        rels = cand.get("salient_rels", [])
        aliases = cand.get("member_aliases", [])[:8]
        py = (
            f'# lib/akasha/concepts/{name}.py — nebula-proposed skeleton (#52). REVIEW before use.\n'
            f'# Discovered region: {cand.get("size")} members, dominant ns "{cand.get("dominant_ns")}",\n'
            f'# kind={cand.get("kind")}, score={cand.get("score")}. Examples: {", ".join(aliases)}\n'
            f'from lib.akasha.concepts.base import BaseConcept\n\n'
            f'class {cls}(BaseConcept):\n'
            f'    CONCEPT_PREFIX = "{name}"\n'
            f'    CONCEPT_LABEL  = "{name} — nebula-discovered concept (rename me)"\n'
            f'    # Inferred salient relations (shared across members): {", ".join(rels) or "(none)"}\n'
            f'    CONCEPT_METHODS = {{\n'
            f'        "new": {{"op": "op_new", "action": "write"}},\n'
            f'        "ls":  {{"op": "op_list", "action": "read"}},\n'
            f'        "get": {{"op": "op_get", "action": "read"}},\n'
            f'    }}\n\n'
            f'    def op_new(self, title):\n'
            f'        """Create a {name}."""\n'
            f'        ...\n\n'
            f'    def op_list(self):\n'
            f'        """List {name} instances."""\n'
            f'        ...\n\n'
            f'    def op_get(self, id):\n'
            f'        """Read one {name}."""\n'
            f'        ...\n'
        )
        ak_lines = [f'# ontology/lexicon — nebula-proposed salient-rels for "{name}"']
        for i, rel in enumerate(rels):
            ak_lines.append(f'def "reldef:{rel}" "{rel} — \'{rel}\' relation asserted between two atoms."')
            ak_lines.append(f'set.add name="rels" id="reldef:{rel}"')
        for rel in rels:                       # author most-important-first (link order = priority)
            ak_lines.append(f'ln {name} reldef:{rel} rel:salient')
        return {"python": py, "ak": "\n".join(ak_lines),
                "salient_rels": rels, "class_name": cls}

    # ------------------------------------------------------------------
    # Contexa
    # ------------------------------------------------------------------

    def _find_or_create_url_atom(self, ctx, url: str, title: str,
                                  client_id: str, scopes: list):
        """
        Find an existing URL Atom (by alias url:{url}) or create one.
        URL Atoms are the exit points — their content IS the URL, allowing
        navigation from Akasha to the external source.
        """
        alias = f"url:{url}"
        try:
            existing = ctx.resolve_alias(alias)
            if existing:
                return existing
        except Exception:
            pass
        try:
            key = ctx.put_chunk(
                content=url,
                meta={"type": "ref:url", "url": url, "title": title},
                author=client_id,
                scopes=scopes,
            )
            ctx.set_alias(key, alias)
            return key
        except Exception as exc:
            logger.debug("[Fetch] create URL atom '%s': %s", url, exc)
            return None

    @staticmethod
    def _external_trust(evidence: dict, source_type: str) -> float:
        """Ground a fetched atom's curation trust in its evidence rather than asserting a
        flat value: trust = 0.5·authority + 0.3·reach + 0.2·nature. Wikipedia (authority
        0.9, reach 1.0, factual) → ~0.95; a scraped URL (authority 0.5) → lower. The score
        is stored on the atom so any downstream curation decision is inspectable."""
        try:
            authority = float(evidence.get("authority", 0.3))
            reach = float(evidence.get("reach", 0.3))
        except (TypeError, ValueError):
            authority, reach = 0.3, 0.3
        nature = str(evidence.get("nature", "unknown")).lower()
        nature_f = {"factual": 1.0, "reference": 0.9, "opinion": 0.5,
                    "unknown": 0.3}.get(nature, 0.3)
        return round(max(0.0, min(1.0, 0.5 * authority + 0.3 * reach + 0.2 * nature_f)), 3)

    def _handle_contexa_fetch(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """
        contexa.fetch — fetch external content and write to Akasha.

        Wikipedia (keyword query):
          - Full article text → written as Atom with evidence.authority=0.9
          - Triggers Weaver + NLP (same pipeline as any w command)
          - URL Atom created as exit point; linked via ref:source
          - Query Atom linked via ctx:topic
          - Added to fetch:{client_id}:refs set

        URL fetch:
          - Scraped content → written as Atom with evidence.authority=0.5
          - Same Weaver/NLP pipeline
          - URL Atom (the URL itself) created as exit point

        In both cases the atom_key is returned so the user can navigate
        or link from it immediately ($it).
        """
        if not self.contexa:
            return _err(rid, -32001, "ContexaEngine not available in this environment.")
        query = data.get("query") or data.get("url", "")
        if not query:
            return _err(rid, -32602, "contexa.fetch requires 'query' or 'url'")
        return _ok(rid, self._do_fetch(session, ctx, scopes, client_id, query))

    def _do_fetch(self, session, ctx, scopes, client_id, query,
                  link_to=None, link_rel="calc:enriches") -> dict:
        """Fetch external content for `query` and integrate it as atoms (the write half
        of contexa.fetch, shared with gap.fetch). Returns the provider result dict with
        atom_key/written on success, or the raw provider result (error/no-text) otherwise.
        Every written atom carries the provenance=external guardrail (trust score +
        provenance scopes) so unvetted web text stays distinguishable from curation.
        `link_to`, when given, is linked FROM the fetched atom via `link_rel` so the graph
        records which concept the fetch enriched. Callers run under a write workspace."""
        result = self.contexa.fetch(query)
        if "error" in result:
            return result

        text = result.get("text", "")
        if not text:
            return result

        source_type = result.get("source_type", "web")
        evidence    = result.get("evidence", {})
        url         = result.get("url", "")
        title       = result.get("title", "")
        alias       = result.get("alias")

        # ── Provenance guardrail (curation trust has an explicit, inspectable basis) ──
        # External content is an attack surface (ASI06 memory poisoning) and must never
        # be indistinguishable from curated ontology. Every fetched atom is:
        #   - tagged provenance=external + source, with a computed `trust` score, and
        #   - placed in the computational scopes provenance:external / provenance:<source>
        #     so curated-only reads/learning can exclude it and curators can review it.
        # trust is grounded in the fetch evidence, not asserted flat.
        trust = self._external_trust(evidence, source_type)
        write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}",
                        "provenance:external", f"provenance:{source_type}"]

        # Write the content Atom
        atom_key = ctx.put_chunk(
            content=text,
            meta={"type": f"fetch:{source_type}", "evidence": evidence,
                  "url": url, "title": title,
                  "provenance": "external", "source": source_type, "trust": trust},
            author=client_id,
            scopes=write_scopes,
        )
        session.last_written_id = atom_key
        session.set_context("last_written_id", atom_key)
        if alias:
            try:
                ctx.set_alias(atom_key, alias)
            except Exception:
                pass

        # URL exit-point Atom + ref:source link
        url_key = None
        if url:
            url_key = self._find_or_create_url_atom(ctx, url, title,
                                                     client_id, write_scopes)
            if url_key:
                try:
                    ctx.put_link(atom_key, url_key, "ref:source", author=client_id)
                except Exception:
                    pass

        # Query Atom + ctx:topic link (find or create)
        query_key = None
        if query and not query.startswith("http"):
            q_alias = f"query:{query[:60]}"
            try:
                query_key = ctx.resolve_alias(q_alias)
            except Exception:
                pass
            if not query_key:
                try:
                    query_key = ctx.put_chunk(
                        content=query,
                        meta={"type": "query"},
                        author=client_id,
                        scopes=write_scopes,
                    )
                    ctx.set_alias(query_key, q_alias)
                except Exception:
                    pass

        # Macro context binding (ctx:topic + fetch set)
        session_id = getattr(session, "session_id", client_id)
        if self.contexa:
            self.contexa.bind_context(
                ctx, atom_key,
                topic_key=query_key,
                set_names=[f"fetch:{session_id}:refs"],
                author=client_id,
            )

        # Enrichment link: fetched atom → the concept it was fetched to enrich, so the
        # self-expanding loop is recorded in the graph (gap.fetch sets link_to).
        if link_to and link_to != atom_key:
            try:
                ctx.put_link(atom_key, link_to, link_rel, author=client_id)
            except Exception:
                pass

        # Trigger Weaver + NLP — same pipeline as w command
        self._post_write(session, isinstance(ctx, _NucleusWriteCtx), atom_key, text)

        result["atom_key"] = atom_key
        result["written"]  = True
        return result

    def _handle_image_profile(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """image.profile path=|url= [top_k=] — classify an image (local file or URL) into
        labels via the LiteRT vision engine and integrate them into the graph. This is the
        image counterpart of contexa.fetch: the image becomes an atom, each predicted label
        becomes/links a concept (`calc:depicts`, weighted by confidence), and everything
        carries the provenance=external guardrail (trust = model confidence) so model-
        inferred labels can neither poison the learned model nor be mistaken for curation.
        Degrades gracefully (no runtime/model/PIL, or offline → written=false, no error).
        Runs inside the write workspace."""
        src = (data.get("path") or data.get("url") or data.get("src")
               or data.get("image") or "").strip()
        if not src:
            return _err(rid, -32602, "image.profile requires 'path' or 'url'")
        if not self.vision or not self.vision.available():
            return _err(rid, -32001,
                        "Vision engine unavailable (no TFLite/LiteRT runtime or PIL).")

        top_k = max(1, min(int(data.get("top_k", 5)), 10))
        res = self.vision.classify(src, top_k=top_k)
        labels = res.get("labels") or []
        if not labels:
            return _ok(rid, res)                          # error / no labels → graceful

        import re
        is_url = src.startswith("http")
        top = labels[0]
        summary = "image: " + ", ".join(l["label"] for l in labels)
        write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}",
                        "provenance:external", "provenance:vision"]
        image_key = ctx.put_chunk(
            content=summary,
            meta={"type": "image", "provenance": "external", "source": "vision",
                  "model": res.get("model"), "backend": res.get("backend"),
                  "trust": round(float(top.get("score", 0.0)), 3),
                  "labels": labels, "src": src},
            author=client_id, scopes=write_scopes)
        session.last_written_id = image_key
        session.set_context("last_written_id", image_key)

        # Each label → a concept atom (find-or-create by alias), linked from the image via
        # calc:depicts weighted by confidence. Concepts are ordinary (curated) atoms, so the
        # graph gains real, referenceable nodes; the *inference* provenance lives on the edge
        # weight + the image atom, not on the concept.
        for lab in labels:
            name = lab["label"]
            c_alias = f"concept:{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}"
            c_key = None
            try:
                c_key = ctx.resolve_alias(c_alias)
            except Exception:
                c_key = None
            if not c_key:
                try:
                    c_key = ctx.put_chunk(content=name, meta={"type": "concept"},
                                          author=client_id, scopes=write_scopes)
                    ctx.set_alias(c_key, c_alias)
                except Exception:
                    c_key = None
            if c_key:
                try:
                    ctx.put_link(image_key, c_key, "calc:depicts",
                                 w=float(lab.get("score", 1.0)), author=client_id)
                except Exception:
                    pass

        # URL exit-point atom (so the source image is navigable) + fetch/vision ref set.
        if is_url:
            url_key = self._find_or_create_url_atom(ctx, src, top["label"],
                                                    client_id, write_scopes)
            if url_key:
                try:
                    ctx.put_link(image_key, url_key, "ref:source", author=client_id)
                except Exception:
                    pass
        session_id = getattr(session, "session_id", client_id)
        try:
            ctx.add_to_set(f"vision:{session_id}:refs", image_key)
        except Exception:
            pass

        # Weave the label summary into the semantic layer (same pipeline as w / fetch).
        self._post_write(session, isinstance(ctx, _NucleusWriteCtx), image_key, summary)

        res["atom_key"] = image_key
        res["written"] = True
        return _ok(rid, res)

    # ------------------------------------------------------------------
    # General file import/export — the single disk-I/O route (io.*)
    # ------------------------------------------------------------------

    @staticmethod
    def _io_slug(path: str) -> str:
        import re
        base = os.path.splitext(os.path.basename(path.rstrip("/")))[0] or os.path.basename(path.rstrip("/"))
        return re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_") or "import"

    # The kernel builds pipeline endpoints from injected closures so lib/harmonia/pipeline.py
    # stays graph-agnostic (it never imports akasha). io.* is just "wire a Source to a Sink".

    def _io_dispatch(self, session, rid) -> Callable:
        """A (method, data) -> result closure over the concept registry — used by pipeline
        graph endpoints to reach table/lens operators through the one dispatch route."""
        def _dispatch(method, data):
            if _concept_registry is None:
                raise RuntimeError("concept models unavailable")
            return _concept_registry.dispatch_if_handled(method, session, data, rid)
        return _dispatch

    def _io_doc_sink(self, ctx, session, client_id, set_name) -> "DocSink":
        """A DocSink that writes through the guarded composite path and weaves the text."""
        def _write_atom(text, meta, scopes_):
            return ctx.put_chunk(content=text, meta=meta, author=client_id, scopes=scopes_)

        def _weave(key, text):
            self._post_write(session, isinstance(ctx, _NucleusWriteCtx), key, text)
        return DocSink(_write_atom, ctx.add_to_set, _weave, client_id, set_name)

    def _io_ingest(self, source, ctx, session, client_id, rid, table_name=None,
                   set_name=None, origin_slug=None) -> dict:
        """Connect a Source to the right graph Sink (table vs document, decided by the stream
        kind) and run the pipeline. Shared by io.import (one file) and io.index (many)."""
        stream = source.read()                                   # may raise (path/parse)
        # The graph Sink is chosen by the stream kind, so we peek the stream here and write it
        # (rather than run_pipeline reading it a second time). Transform hooks, when added, go
        # between this read and the write.
        if stream.kind == "table":
            import re as _re
            name = _re.sub(r"[^a-z0-9_]+", "_", str(table_name or "").lower()).strip("_") \
                or origin_slug or self._io_slug(stream.origin or "import")
            sink = TableSink(self._io_dispatch(session, rid), name)
        else:
            sink = self._io_doc_sink(ctx, session, client_id,
                                     set_name or f"docs:{origin_slug or self._io_slug(stream.origin or 'doc')}")
        result = sink.write(stream)
        if stream.origin and "source" not in result:
            result["source"] = stream.origin
        return result

    def _handle_io_import(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """io.import path=|text= [format=] [table=] — connect a file (or an inline upload
        payload) Source to a graph Sink: tabular → the `table` model; a document → an indexed
        atom. The single disk-read route into the graph; confined to permitted roots
        (io.allow). Admin/librarian only. Runs in the write workspace."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        if not self.fileio:
            return _err(rid, -32001, "FileIO unavailable in this environment.")
        fmt = (data.get("format") or "").strip() or None
        # Source: a local file, OR an inline payload (text=) — the latter is how a future Web
        # GUI upload plugs into the SAME pipeline without touching disk.
        if data.get("text") is not None:
            if not fmt:
                return _err(rid, -32602, "io.import text= requires 'format'")
            source = InlineSource(str(data["text"]), fmt, name=data.get("name") or "upload")
        else:
            path = (data.get("path") or data.get("file") or "").strip()
            if not path:
                return _err(rid, -32602, "io.import requires 'path' or 'text'")
            source = FileSource(self.fileio, path, fmt)
        try:
            return _ok(rid, self._io_ingest(source, ctx, session, client_id, rid,
                                            table_name=data.get("table")))
        except PermissionError as exc:
            return _err(rid, -32001, str(exc))
        except FileNotFoundError:
            return _err(rid, -32002, "file not found")
        except (ValueError, RuntimeError) as exc:
            return _err(rid, -32602, str(exc))
        except Exception as exc:
            return _err(rid, -32002, f"import failed: {str(exc)[:140]}")

    def _handle_io_index(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """io.index dir= [exts=] [limit=] — index every supported file under a permitted
        directory (the local-directory-indexing feature: the maintainer permits a dir, and its
        files' content/keywords become index atoms — raw files are never stored). Each file is
        a FileSource run through the ingest pipeline. Bounded; admin/librarian only."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        if not self.fileio:
            return _err(rid, -32001, "FileIO unavailable in this environment.")
        dirp = (data.get("dir") or data.get("path") or "").strip()
        if not dirp:
            return _err(rid, -32602, "io.index requires 'dir'")
        exts = None
        if data.get("exts"):
            exts = {e if e.startswith(".") else "." + e
                    for e in str(data["exts"]).lower().replace(",", " ").split()}
        limit = max(1, min(int(data.get("limit", 1000)), 5000))
        slug = self._io_slug(dirp)
        set_name = f"index:{slug}"
        indexed = tables = errors = files = 0
        try:
            paths = list(self.fileio.iter_dir(dirp, exts))
        except PermissionError as exc:
            return _err(rid, -32001, str(exc))
        except FileNotFoundError:
            return _err(rid, -32002, f"directory not found: {dirp}")
        for fpath in paths[:limit]:
            files += 1
            try:
                r = self._io_ingest(FileSource(self.fileio, fpath), ctx, session, client_id, rid,
                                    set_name=set_name)
                if r.get("kind") == "table":
                    tables += 1
                else:
                    indexed += 1
            except Exception as exc:
                logger.warning("[io.index] %s: %s", fpath, exc)
                errors += 1
        return _ok(rid, {"dir": dirp, "files": files, "indexed_docs": indexed,
                         "tables": tables, "errors": errors, "set": set_name,
                         "truncated": len(paths) > limit})

    def _handle_io_export(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """io.export (table=|set=) (path=|inline=true) [format=] — connect a graph Source (a
        `table`, or a set of atoms) to a Sink: FileSink writes CSV/JSON/MD to a permitted path;
        with inline=true a ResponseSink returns the serialised content in the result instead
        (the client 'receive' path — a session downloads a table/set as a file). The reverse
        of io.import through the SAME pipeline. Admin/librarian only."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        if not self.fileio:
            return _err(rid, -32001, "FileIO unavailable in this environment.")
        inline = str(data.get("inline", "")).lower() in ("true", "1", "yes")
        path = (data.get("path") or data.get("file") or "").strip()
        if not inline and not path:
            return _err(rid, -32602, "io.export requires 'path' (or inline=true)")
        fmt = (data.get("format") or "").strip() \
            or (self.fileio.detect_format(path) if path else None) or "csv"
        if data.get("table"):
            source = TableSource(self._io_dispatch(session, rid), data["table"])
        elif data.get("set"):
            set_name = data["set"]
            source = SetSource(
                list_members=lambda: ctx.list_set(set_name, allowed_scopes=scopes),
                get_content=lambda k: (ctx.get_scoped_chunk(k, scopes) if scopes
                                       else ctx.get_chunk(k)),
                set_name=set_name)
        else:
            return _err(rid, -32602, "io.export requires 'table' or 'set'")
        sink = ResponseSink(fmt) if inline else FileSink(self.fileio, path, fmt)
        try:
            return _ok(rid, run_pipeline(source, sink))
        except PermissionError as exc:
            return _err(rid, -32001, str(exc))
        except (ValueError, RuntimeError) as exc:
            return _err(rid, -32002, str(exc))
        except Exception as exc:
            return _err(rid, -32002, f"export failed: {str(exc)[:140]}")

    def _handle_io_project(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """io.project src= [model=table|rec] [into=] [depth=] — project an in-graph source (a set,
        an atom/alias tree root, or an Exportable model instance such as a survey) into a concept
        model through the lens pipeline (LensScanSource -> ConceptCastSink). This is the base of the
        general "project into any concept model" path and of model->model chaining; targets today are
        `table` (schema-first) and `rec` (schema-free universal fallback); survey is Exportable
        (other models are a per-model follow-up — issue #43). Admin/librarian only; write."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        if _concept_registry is None:
            return _err(rid, -32001, "concept models unavailable")
        src = (data.get("src") or data.get("source") or "").strip()
        if not src:
            return _err(rid, -32602, "io.project requires 'src' (a set name or atom/alias)")
        model = (data.get("model") or "table").strip()
        dispatch = self._io_dispatch(session, rid)
        try:
            return _ok(rid, run_pipeline(
                LensScanSource(dispatch, src, depth=int(data.get("depth", 2))),
                ConceptCastSink(dispatch, model, into=data.get("into"))))
        except (ValueError, RuntimeError) as exc:
            return _err(rid, -32602, str(exc))
        except Exception as exc:
            return _err(rid, -32002, f"project failed: {str(exc)[:140]}")

    def _handle_io_allow(self, rid, data, session) -> dict:
        """io.allow dir= — permit a local directory for io.import/io.index/io.export (the
        maintainer explicitly grants a directory; reads/writes are otherwise confined to
        data/import, data/export, data). Admin/librarian only."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        if not self.fileio:
            return _err(rid, -32001, "FileIO unavailable in this environment.")
        dirp = (data.get("dir") or data.get("path") or "").strip()
        if not dirp:
            return _err(rid, -32602, "io.allow requires 'dir'")
        root = self.fileio.add_root(dirp)
        return _ok(rid, {"allowed": root, "roots": list(self.fileio.roots)})

    # ── Contexa ingest / Jataka present — the client session's I/O sides ──────────
    # These are the survey round-trip on the pipe: Contexa reads collected responses IN (with
    # macro context-binding), the client projects/analyses via concept models (lens / table),
    # and Jataka presents OUT. Consciousness is the substrate both flow through — Contexa's
    # writes are auto-woven; Jataka's reads pass through generate_view — never a pipe endpoint.

    def _survey_questions_ordered(self, dispatch, ctx, survey_id):
        """Open a survey and return its question atom ids ordered by meta['order'] then
        creation. Returns (question_ids, error_msg)."""
        opened = dispatch("survey.open", {"survey_id": survey_id})
        if not isinstance(opened, dict) or opened.get("error") or "result" not in opened:
            return None, f"survey '{survey_id[:12]}' not found or not a survey root"
        inv = (dispatch("survey.list", {}) or {}).get("result") or {}
        q_ids = list(inv.get("questions") or [])

        def _order(q):
            m = ctx.get_meta(q) or {}
            o = m.get("order")
            return (o if o is not None else 1e9, m.get("created_at", 0))
        return sorted(q_ids, key=_order), None

    def _handle_contexa_ingest(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """contexa.ingest survey=<id> (path=|text=) [format=] [respondent_col=] [map=] — the
        client's INPUT side: read collected responses (a CSV/JSON file, or an inline upload
        payload) into the survey graph WITH Contexa macro-binding (ctx:answers → question,
        ctx:from → respondent, per-question set) layered on the survey model's structural links.

        Columns after the respondent column map to the survey's questions: explicitly via
        map=col:qid[,col:qid] (qid may be a question id, an alias, or a 1-indexed position),
        else to the survey's questions in order. Writes into the client's own survey (WRITE);
        disk reads honour the io.allow list. Runs in the write workspace (single-route guard)."""
        if _concept_registry is None:
            return _err(rid, -32001, "concept models unavailable")
        if not self.contexa:
            return _err(rid, -32001, "ContexaEngine not available in this environment.")
        survey_id = (data.get("survey") or data.get("survey_id") or "").strip()
        if not survey_id:
            survey_id = getattr(session, "get_context", lambda k: None)("active_survey_root") or ""
        if not survey_id:
            return _err(rid, -32602, "contexa.ingest requires 'survey' (survey id)")

        dispatch = self._io_dispatch(session, rid)
        q_ids, qerr = self._survey_questions_ordered(dispatch, ctx, survey_id)
        if qerr:
            return _err(rid, -32602, qerr)

        # Source: an inline upload (text=) — the Web-GUI path — or a permitted file.
        fmt = (data.get("format") or "").strip() or None
        if data.get("text") is not None:
            if not fmt:
                return _err(rid, -32602, "contexa.ingest text= requires 'format'")
            source = InlineSource(str(data["text"]), fmt, name=data.get("name") or "responses")
        else:
            path = (data.get("path") or data.get("file") or "").strip()
            if not path:
                return _err(rid, -32602, "contexa.ingest requires 'path' or 'text'")
            if not self.fileio:
                return _err(rid, -32001, "FileIO unavailable in this environment.")
            # Disk reads are admin/librarian only (same posture as io.import — the io.allow
            # list is maintainer-managed); a WRITE client ingests its own data via text=.
            err = self._assert_admin(session)
            if err:
                return _err(rid, -32003, err)
            source = FileSource(self.fileio, path, fmt)

        try:
            stream = source.read()
        except PermissionError as exc:
            return _err(rid, -32001, str(exc))
        except FileNotFoundError:
            return _err(rid, -32002, "file not found")
        except (ValueError, RuntimeError) as exc:
            return _err(rid, -32602, str(exc))
        if stream.kind != "table":
            return _err(rid, -32602, "contexa.ingest requires a tabular source (CSV/JSON rows)")

        cols = list(stream.columns)
        if not cols:
            return _err(rid, -32602, "no columns in the response source")
        respondent_col = (data.get("respondent_col") or "").strip() or cols[0]
        if respondent_col not in cols:
            return _err(rid, -32602,
                        f"respondent_col '{respondent_col}' not in columns {cols}")

        question_map = {}
        if data.get("map"):
            for pair in str(data["map"]).split(","):
                if ":" not in pair:
                    continue
                col, q = (p.strip() for p in pair.split(":", 1))
                if col not in cols:
                    continue
                if q.isdigit():
                    idx = int(q) - 1
                    if 0 <= idx < len(q_ids):
                        question_map[col] = q_ids[idx]
                elif q in q_ids:
                    question_map[col] = q
                else:
                    resolved = ctx.resolve_alias(q)
                    if resolved:
                        question_map[col] = resolved
        else:
            q_cols = [c for c in cols if c != respondent_col]
            for i, col in enumerate(q_cols):
                if i < len(q_ids):
                    question_map[col] = q_ids[i]
        if not question_map:
            return _err(rid, -32602, "no question columns could be mapped "
                        "(add questions to the survey first, or pass map=col:qid)")

        def _bind(resp_id, question_key=None, respondent_key=None, set_names=None):
            return self.contexa.bind_context(
                ctx, resp_id, question_key=question_key, respondent_key=respondent_key,
                set_names=set_names, author=client_id)

        sink = ResponseIngestSink(dispatch, _bind, survey_id, respondent_col, question_map)
        try:
            result = sink.write(stream)
        except (ValueError, RuntimeError) as exc:
            return _err(rid, -32602, str(exc))
        result["mapped_questions"] = {c: q[:12] for c, q in question_map.items()}
        if stream.origin:
            result.setdefault("source", stream.origin)
        return _ok(rid, result)

    def _handle_jataka_present(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """jataka.present (survey=<id>|set=<name>|focus=<atom>) as=table|scatter|narrative
        [format=] — the client's OUTPUT side: read a graph selection THROUGH the Consciousness
        substrate and render a presentation, returned inline (READ-level; no graph write).
          as=table     survey=|set=   → per-(question,answer) counts / listed rows (+ format=)
          as=scatter   survey=|set=   → 2-D points positioned by cosmos_nd
          as=narrative focus=|survey= → prose from generate_view (LLM-optional; template floor)"""
        as_fmt = (data.get("as") or data.get("mode") or "table").strip().lower()
        survey_id = (data.get("survey") or data.get("survey_id") or "").strip()
        set_name = (data.get("set") or "").strip()
        focus = (data.get("focus") or data.get("id") or "").strip()
        dispatch = self._io_dispatch(session, rid)

        def _view(k):
            return session.consciousness.generate_view(k, allowed_scopes=scopes)

        def _content(k):
            return (ctx.get_scoped_chunk(k, scopes) if scopes else ctx.get_chunk(k)) or ""

        def _agg_source(sid):
            return SurveyAggregateSource(
                lambda: (dispatch("survey.list", {}) or {}).get("result") or {},
                lambda k: ctx.get_meta(k) or {}, _content, sid)

        try:
            if as_fmt == "table":
                if survey_id:
                    opened = dispatch("survey.open", {"survey_id": survey_id})
                    if not isinstance(opened, dict) or "result" not in opened:
                        return _err(rid, -32602, f"survey '{survey_id[:12]}' not found")
                    source = _agg_source(survey_id)
                elif set_name:
                    source = SetSource(
                        list_members=lambda: ctx.list_set(set_name, allowed_scopes=scopes),
                        get_content=_content, set_name=set_name)
                else:
                    return _err(rid, -32602, "jataka.present as=table requires 'survey' or 'set'")
                sink = PresentTableSink((data.get("format") or "").strip() or None)
                return _ok(rid, run_pipeline(source, sink))

            if as_fmt in ("scatter", "cosmos"):
                sset = f"set:survey:{survey_id}:responses" if survey_id else set_name
                if not sset:
                    return _err(rid, -32602, "jataka.present as=scatter requires 'survey' or 'set'")
                source = SetSource(
                    list_members=lambda: ctx.list_set(sset, allowed_scopes=scopes),
                    get_content=_content, set_name=sset)

                def _coords(k):
                    v = _view(k) or {}
                    if "error" in v:
                        return None
                    f = v.get("focus") or {}
                    nd = f.get("cosmos_nd") or []
                    if len(nd) < 2:
                        return None
                    label = f.get("alias") or (f.get("content") or "")[:20].replace("\n", " ")
                    color = nd[5] if len(nd) > 5 else "#888888"
                    return (nd[0], nd[1], label, color)
                return _ok(rid, run_pipeline(source, ScatterSink(_coords)))

            if as_fmt in ("narrative", "story", "narrate"):
                if not focus and survey_id:
                    focus = survey_id
                if not focus:
                    return _err(rid, -32602,
                                "jataka.present as=narrative requires 'focus' or 'survey'")
                resolved = ctx.resolve_alias(focus) or focus
                rows, cols = [], []
                if survey_id:
                    opened = dispatch("survey.open", {"survey_id": survey_id})
                    if not isinstance(opened, dict) or "result" not in opened:
                        return _err(rid, -32602, f"survey '{survey_id[:12]}' not found")
                    agg = _agg_source(survey_id).read()
                    rows, cols = agg.rows, agg.columns
                source = InterpretationSource(_view, resolved, data_rows=rows, data_columns=cols)
                return _ok(rid, run_pipeline(source, NarrativeSink(getattr(self, "_narrative_llm", None))))

            return _err(rid, -32602,
                        f"unknown presentation mode '{as_fmt}' (table|scatter|narrative)")
        except (ValueError, RuntimeError) as exc:
            return _err(rid, -32602, str(exc))
        except Exception as exc:
            return _err(rid, -32002, f"present failed: {str(exc)[:140]}")

    def _handle_curation_project(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """curation.project id=<cur>|name= as=presentation [title=] — HOP A: project a curation's
        narrative path into a PRIVATE working presentation deck (1 frame per path atom, in order).
        run_pipeline(CurationPathSource → PresentationSink). Idempotent: if the curation already
        has a projected presentation (curation:projected_as), returns it. CLI: cur.project."""
        as_fmt = (data.get("as") or "presentation").strip().lower()
        if as_fmt != "presentation":
            return _err(rid, -32602, "curation.project supports as=presentation "
                                     "(as=table|scatter → jataka.present)")
        cur = (data.get("id") or data.get("curation_id") or data.get("name") or "").strip()
        if not cur:
            return _err(rid, -32602, "curation.project requires 'id' (or name=)")
        dispatch = self._io_dispatch(session, rid)
        # Idempotency: reuse a prior projection if linked.
        try:
            cur_key = ctx.resolve_alias(cur) or cur
            for (dst, _rel) in (ctx.get_adjacent_links(cur_key, "curation:projected_as") or []):
                if (ctx.get_meta(dst) or {}).get("concept") == "presentation":
                    return _ok(rid, {"status": "exists", "presentation_id": dst,
                                     "source": f"curation:{cur_key}", "reused": True})
        except Exception:
            cur_key = cur
        try:
            result = run_pipeline(CurationPathSource(dispatch, cur),
                                  PresentationSink(dispatch, title=(data.get("title") or "").strip() or None))
        except (ValueError, RuntimeError) as exc:
            return _err(rid, -32602, str(exc))
        except Exception as exc:
            return _err(rid, -32002, f"project failed: {str(exc)[:140]}")
        pres_id = result.get("presentation_id")
        if pres_id:
            try:
                ctx.put_link(cur_key, pres_id, "curation:projected_as", author=client_id)
            except Exception:
                pass
        result["status"] = "projected"
        return _ok(rid, result)

    def _handle_pres_export(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """pres.export id=<pres> as=scroll|kamishibai [inline=true | publish=<slug>] — HOP B:
        resolve each frame's ref atom into a full self-contained card and render the export
        object (§6). inline=true (default) returns it in-band (+ a CLI text rendering); publish=
        <slug> (librarian) writes the frozen artifact to archives/curation/exports/<slug>.<fmt>.json
        and returns its URL. Format-only, no graph write. CLI: pr.export."""
        pres_id = (data.get("id") or data.get("pres_id") or data.get("presentation_id") or "").strip()
        if not pres_id:
            return _err(rid, -32602, "pres.export requires 'id'")
        pres_id = ctx.resolve_alias(pres_id) or pres_id
        fmt = (data.get("as") or data.get("format") or "scroll").strip().lower()
        if fmt not in ("scroll", "kamishibai"):
            return _err(rid, -32602, "pres.export as= must be scroll|kamishibai")
        publish = (data.get("publish") or "").strip()
        dispatch = self._io_dispatch(session, rid)

        def _get_links(key, rel):
            return [(l[0], l[1]) for l in (ctx.get_adjacent_links(key, rel) or [])]

        try:
            source = PresentationSceneSource(dispatch, pres_id, fmt,
                                             lambda k: ctx.get_meta(k) or {}, _get_links)
            result = run_pipeline(source, ExportSink(fmt))
        except (ValueError, RuntimeError) as exc:
            return _err(rid, -32602, str(exc))
        except Exception as exc:
            return _err(rid, -32002, f"export failed: {str(exc)[:140]}")
        export = result.get("export") or {}

        if publish:
            # Publishing writes a PUBLIC static artifact → librarian-gated (it exposes a snapshot).
            if "role:librarian" not in scopes:
                return _err(rid, -32601, "pres.export publish=<slug> requires role:librarian")
            if not self.fileio:
                return _err(rid, -32001, "FileIO unavailable in this environment.")
            import re as _re
            slug = _re.sub(r"[^a-z0-9._-]+", "-", publish.lower()).strip("-") or "export"
            _kernel_dir  = os.path.dirname(os.path.abspath(__file__))
            _project_dir = os.path.dirname(os.path.dirname(_kernel_dir))
            exports_dir  = os.path.join(_project_dir, "archives", "curation", "exports")
            try:
                os.makedirs(exports_dir, exist_ok=True)
                self.fileio.add_root(exports_dir)        # allow-list this public archives dir
                rel_path = os.path.join(exports_dir, f"{slug}.{fmt}.json")
                # FileIO.serialize(payload,"json") dumps the payload directly → the file is the
                # RAW export object (self-contained, renderable with zero graph access).
                self.fileio.write(rel_path, export, "json")
                # Maintain a published-exhibits index so the archives Exhibition Room can
                # list and link exhibits (it can't know a slug otherwise). Upsert by slug,
                # tracking which formats exist. Non-fatal — a bad index never fails a publish.
                try:
                    import json as _json, time as _t
                    idx_path = os.path.join(exports_dir, "index.json")
                    by_slug = {}
                    if os.path.exists(idx_path):
                        with open(idx_path, "r", encoding="utf-8") as _f:
                            for e in (_json.load(_f) or {}).get("exhibits", []):
                                if e.get("slug"):
                                    by_slug[e["slug"]] = e
                    entry = by_slug.get(slug, {"slug": slug})
                    entry.update({"slug": slug, "title": export.get("title", ""),
                                  "thesis": export.get("thesis", ""),
                                  "count": export.get("count", 0), "updated_at": _t.time()})
                    entry["formats"] = sorted(set(entry.get("formats") or []) | {fmt})
                    by_slug[slug] = entry
                    with open(idx_path, "w", encoding="utf-8") as _f:
                        _json.dump({"exhibits": sorted(by_slug.values(),
                                    key=lambda e: e.get("updated_at", 0), reverse=True)},
                                   _f, ensure_ascii=False, indent=2)
                except Exception as _iexc:
                    logger.warning("[pres.export] exhibits index update failed: %s", _iexc)
            except Exception as exc:
                return _err(rid, -32002, f"publish failed: {str(exc)[:140]}")
            return _ok(rid, {"status": "published", "format": fmt, "slug": slug,
                             "url": f"/curation/exports/{slug}.{fmt}.json",
                             "scenes": export.get("count", 0)})

        # inline (default): return the export + a CLI text rendering.
        return _ok(rid, {"status": "exported", "format": fmt, "export": export,
                         "text": self._render_export_text(export)})

    @staticmethod
    def _render_export_text(export: dict) -> str:
        """A plain-text rendering of an export object for the CLI — the same scenes the archives
        page draws, as a readable 紙芝居/scroll transcript (headword, description, caption, refs,
        links per scene). Degradation-first: a headword-only scene still prints."""
        lines: List[str] = []
        title = export.get("title") or "(untitled)"
        fmt = export.get("format", "scroll")
        lines.append(f"╔═ {title}  [{fmt}]")
        if export.get("thesis"):
            lines.append(f"║  {export['thesis']}")
        lines.append(f"╚═ {export.get('count', 0)} scene(s)")
        for sc in export.get("scenes") or []:
            n = sc.get("scene")
            lines.append("")
            lines.append(f"── [{n}] {sc.get('headword') or '(no headword)'} ──"
                         + (f"   {sc['href']}" if sc.get("href") else ""))
            desc = (sc.get("description") or "").strip()
            if desc:
                lines.append(desc if len(desc) <= 400 else desc[:400] + "…")
            if sc.get("caption"):
                lines.append(f"  ⟨caption⟩ {sc['caption']}")
            img = sc.get("image") or None
            if isinstance(img, dict) and img.get("url"):
                lines.append(f"  ⟨image⟩ {img['url']}"
                             + (f"  ({img.get('source')})" if img.get("source") else ""))
            for rf in (sc.get("refs") or [])[:6]:
                lines.append(f"  → {rf.get('label') or rf.get('url')}  [{rf.get('source','')}] "
                             f"{rf.get('url','')}")
            links = sc.get("links") or []
            if links:
                lines.append("  related: " + ", ".join(l.get("name", "") for l in links[:8]))
            for blk in (sc.get("blocks") or []):
                lines.append(f"    · {blk.get('region','')}/{blk.get('role','')}: "
                             f"{(blk.get('headword') or blk.get('body') or '')[:60]}")
        return "\n".join(lines)

    def _handle_web_search(self, rid, data, session, ctx, scopes, client_id) -> dict:
        """
        web.search — surface-level web search; results stored as lightweight refs.

        For each result: a ref Atom (title + snippet) is created and linked to
        a URL exit-point Atom via ref:source.  The full page is NOT fetched or
        processed — only the search API snippet is stored.  No Weaver/NLP is
        triggered on ref Atoms (they are reference metadata, not knowledge).

        All refs are added to search:{client_id}:refs for navigation.
        """
        if not self.contexa:
            return _err(rid, -32001, "ContexaEngine not available in this environment.")
        query = data.get("query", "")
        if not query:
            return _err(rid, -32602, "web.search requires 'query'")
        limit = int(data.get("limit", 5))

        result  = self.contexa.search(query, limit=limit)
        results = result.get("results", [])

        write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}"]
        session_id   = getattr(session, "session_id", client_id)
        ref_set      = f"search:{session_id}:refs"
        ref_keys: List[str] = []

        for r in results:
            url     = r.get("url", "")
            title   = r.get("title", "")
            snippet = r.get("snippet", "")
            if not url:
                continue

            # URL exit-point Atom
            url_key = self._find_or_create_url_atom(ctx, url, title,
                                                     client_id, write_scopes)

            # Lightweight ref Atom: title + snippet only (no page fetch)
            ref_content = f"{title}\n{snippet}".strip() if snippet else title
            if ref_content:
                try:
                    ref_key = ctx.put_chunk(
                        content=ref_content,
                        meta={"type": "ref:web", "url": url, "title": title},
                        author=client_id,
                        scopes=write_scopes,
                    )
                    if url_key:
                        ctx.put_link(ref_key, url_key, "ref:source", author=client_id)
                    ctx.add_to_set(ref_set, ref_key)
                    ref_keys.append(ref_key)
                except Exception as exc:
                    logger.debug("[WebSearch] ref atom '%s': %s", url, exc)
            elif url_key:
                try:
                    ctx.add_to_set(ref_set, url_key)
                    ref_keys.append(url_key)
                except Exception:
                    pass

        result["ref_keys"] = ref_keys
        return _ok(rid, result)

    # ------------------------------------------------------------------
    # Associate (kernel.associate + associate.unwritten)
    # ------------------------------------------------------------------

    def _handle_emotion_profile(self, rid, data, session, ctx, scopes) -> dict:
        """emotion.profile id= [scope=] [normalize=] — the Akasha-native emotion vector of an
        atom: the emo:* atoms it is linked to (via calc:associated_with / has_emotion / …),
        weighted by edge strength and depth, ranked and (by default) L1-normalised. This is
        the link-based track of the two-track emotion design; the external-NLP sentiment track
        is separate. Scope-filtered; an atom with no emotion links returns an empty vector."""
        target = data.get("id") or data.get("key") or session.last_written_id or ""
        if not target:
            return _err(rid, -32602, "emotion.profile requires 'id' or a last-written atom")
        focal_key = ctx.resolve_alias(target) or target
        content = ctx.get_scoped_chunk(focal_key, scopes) if scopes else ctx.get_chunk(focal_key)
        if content is None:
            return _err(rid, -32002, f"Atom '{focal_key}' not found or access denied")
        scope = max(1, min(int(data.get("scope", 2)), 4))
        normalize = str(data.get("normalize", "true")).lower() not in ("0", "false", "no")
        profile = ctx.emotion_profile(focal_key, scope=scope,
                                      allowed_scopes=scopes, normalize=normalize)
        return _ok(rid, profile)

    def _handle_emotion_find(self, rid, data, session, ctx, scopes) -> dict:
        """emotion.find emo= [limit=] — the reverse of emotion.profile: the atoms that FEEL a
        given emotion, i.e. those linking to the `emo:*` atom (incoming edges), ranked by edge
        strength. `emo=` accepts 'awe' or 'emo:awe'. Scope-filtered (fail-closed)."""
        emo = (data.get("emo") or data.get("emotion") or data.get("id") or "").strip()
        if not emo:
            return _err(rid, -32602, "emotion.find requires 'emo' (e.g. emo=awe)")
        alias = emo if emo.startswith("emo:") else f"emo:{emo}"
        emo_key = ctx.resolve_alias(alias) or (emo if emo != alias else None)
        if not emo_key:
            return _err(rid, -32002, f"emotion '{alias}' not found")
        limit = max(1, min(int(data.get("limit", 20)), 200))
        seen, results = set(), []
        for link in (ctx.get_incoming_links(emo_key) or []):
            src = link.get("src") if isinstance(link, dict) else (link[0] if link else None)
            if not src or src in seen:
                continue
            seen.add(src)
            if scopes and not ctx.check_access(src, scopes):
                continue
            content = ctx.get_chunk(src)
            if content is None:
                continue
            w = link.get("w", 1.0) if isinstance(link, dict) else 1.0
            rel = link.get("rel", "") if isinstance(link, dict) else ""
            results.append({"key": src, "name": _readable(ctx, src),
                            "weight": float(w or 1.0), "rel": rel,
                            "preview": content[:80]})
        results.sort(key=lambda r: r["weight"], reverse=True)
        return _ok(rid, {"emotion": alias, "results": results[:limit],
                         "count": min(len(results), limit)})

    def _handle_associate(self, rid, data, session, ctx, scopes, history) -> dict:
        """
        assoc — gap detection and fill for a specific atom.

        Scans ONE-LEVEL outgoing links from the target atom.
        Identifies which semantic axes are absent (voids).
        Finds structural candidates from peer atoms in shared sets (no inference).
        Optionally fills each void with the top structural candidate.

        Parameters:
          id=   target atom (required, or falls back to last-written)
          axis= focus on one axis only (optional)
          fill= yes → write a link for the top candidate of each void
        """
        target = data.get("id", "") or session.last_written_id or ""
        if not target:
            return _err(rid, -32602, "assoc requires 'id' or a last-written atom")

        axis = (data.get("axis") or "").strip() or None
        fill = data.get("fill", "").strip().lower() in ("yes", "true", "1")

        focal_key = (
            self._resolve_target(target, session, history)
            or ctx.resolve_alias(target)
            or target
        )

        content = ctx.get_scoped_chunk(focal_key, scopes) if scopes else ctx.get_chunk(focal_key)
        if content is None:
            return _err(rid, -32002, f"Atom '{focal_key}' not found or access denied")

        # Gap detection — structural, one level, no inference
        voids = ctx.find_link_voids(focal_key, axis=axis, allowed_scopes=scopes)

        filled: List[Dict[str, Any]] = []
        if fill:
            author_id = getattr(session, 'client_id', 'system')
            for void in voids:
                cands = void.get("candidates", [])
                if not cands:
                    continue
                best = cands[0]
                rel  = best["rel"]
                dst  = best["key"]
                ctx.put_link(focal_key, dst, rel, author=author_id)
                filled.append({
                    "axis":  void["axis"],
                    "rel":   rel,
                    "dst":   dst,
                    "alias": best.get("alias"),
                })

        focal_aliases = ctx.get_aliases_by_key(focal_key)
        return _ok(rid, {
            "focal":   {"key": focal_key, "alias": focal_aliases[0] if focal_aliases else None,
                        "preview": content[:60]},
            "axis":    axis or "all",
            "voids":   voids,
            "filled":  filled,
        })

    def _handle_associate_unwritten(self, rid, data, session, ctx, scopes) -> dict:
        """
        Heuristic UnwrittenVoid detection.
        Checks which semantic axes are absent from the focal atom's outgoing links.
        When TensorEngine is available, vector distance replaces heuristics.
        Executed as an async JCL step — result retrievable via job.log.
        """
        focal_key = data.get("focal_key", "")
        axis      = data.get("axis") or None

        if not focal_key:
            return _err(rid, -32602, "associate.unwritten requires 'focal_key'")

        # Collect axes that ARE present in the focal atom's outgoing links
        present_axes: set = set()
        for dst, rel in ctx.get_adjacent_links(focal_key):
            for ax_name, ax_prefixes in _AXIS_PREFIXES.items():
                if any(rel.startswith(p) for p in ax_prefixes):
                    present_axes.add(ax_name)

        # Determine which axes to check
        check_axes = [axis] if (axis and axis in _AXIS_PREFIXES) else list(_AXIS_PREFIXES.keys())

        voids = []
        for ax in check_axes:
            if ax not in present_axes:
                ax_prefixes = _AXIS_PREFIXES.get(ax, [])
                example_rel = ax_prefixes[0] if ax_prefixes else ax
                voids.append({
                    "axis":    ax,
                    "missing": example_rel,
                    "hint":    f"No '{ax}' links found on this atom.",
                })

        # Write result to cortex so job.log can surface it
        if voids:
            ctx.put_chunk(
                content=f"[UnwrittenVoid] focal={focal_key[:8]} missing={[v['axis'] for v in voids]}",
                meta={
                    "type":      "sys:associate_unwritten",
                    "focal_key": focal_key,
                    "voids":     voids,
                },
                author="system.associate",
                scopes=["scope:sys:universal"],
            )

        return _ok(rid, {"focal_key": focal_key, "voids": voids})

    @staticmethod
    def _format_associate_cosmos(
        focal: Dict[str, Any],
        axis: Optional[str],
        result: Dict[str, Any],
        unwritten: Dict[str, Any],
        ctx=None,
    ) -> Dict[str, Any]:
        """Formats associate result as a Cosmos/3D-Force-Graph ready payload.

        Each node carries a REAL semantic position (x/y/z = projection of its self-owned
        embedding via CosmosMapper.position, scaled to force-graph units) so the layout means
        something — near in space ⇒ near in meaning — and a degree-based size (val). A
        front-end that seeds ForceGraph positions from x/y/z gets a semantic layout instead of
        pure physics; one that ignores them is unaffected (additive, backward-compatible)."""
        _POS_SCALE = 60.0   # force-graph world units (position() returns ~unit-scale)

        def _geom(key: str, base_val: float):
            x, y, z = CosmosMapper.position(ctx, key) if ctx else (0.0, 0.0, 0.0)
            deg = len(ctx.get_adjacent_links(key)) if ctx else 0
            return {"x": round(x * _POS_SCALE, 3), "y": round(y * _POS_SCALE, 3),
                    "z": round(z * _POS_SCALE, 3), "val": round(base_val + min(deg, 40) * 0.6, 2)}

        _focal_node = {
            "id":    focal["key"],
            "name":  focal["preview"],
            "alias": focal.get("alias"),
            "group": "focus",
            "color": "#ffffff",
        }
        _focal_node.update(_geom(focal["key"], 20))
        _focal_node["val"] = 20          # focus stays visually dominant regardless of degree
        nodes: List[Dict[str, Any]] = [_focal_node]
        links: List[Dict[str, Any]] = []
        seen: set = {focal["key"]}

        def _alias(key: str):
            if not ctx:
                return None
            aliases = ctx.get_aliases_by_key(key)
            return aliases[0] if aliases else None

        _ATYPE_COLOR = {
            "emotion":   "#ff6699",
            "concept":   "#00ffcc",
            "word":      "#66ccff",
            "structure": "#cc99ff",
            "relation":  "#ffcc44",  # bare-word, pre-namespace ontology
            "chunk":     "#aaaaaa",
        }

        def _node_color(key: str, atype: str) -> str:
            # Emotion/sense aura takes priority over structural type color
            if ctx:
                aura = CosmosMapper.get_aura_color(ctx, key)
                if aura:
                    return aura
            return _ATYPE_COLOR.get(atype, "#00ffcc")

        for a in result.get("associations", []):
            if a["key"] not in seen:
                color = _node_color(a["key"], a.get("type", "chunk"))
                node = {
                    "id":    a["key"],
                    "name":  a["preview"],
                    "alias": _alias(a["key"]),
                    "group": a.get("type", "association"),
                    "color": color,
                }
                node.update(_geom(a["key"], 8))
                nodes.append(node)
                seen.add(a["key"])
            links.append({
                "source": focal["key"],
                "target": a["key"],
                "rel":    a.get("rel"),
                "type":   a.get("type", "association"),
            })

        for r in result.get("resonance", []):
            if r["key"] not in seen:
                color = _node_color(r["key"], "resonance")
                node = {
                    "id":    r["key"],
                    "name":  r["preview"],
                    "alias": _alias(r["key"]),
                    "group": "resonance",
                    "color": color,
                }
                node.update(_geom(r["key"], 10))
                nodes.append(node)
                seen.add(r["key"])
            links.append({
                "source": focal["key"],
                "target": r["key"],
                "rel":    r.get("rel"),
                "type":   "resonance",
            })

        return {
            "focal":     {"key": focal["key"], "preview": focal["preview"], "alias": focal.get("alias")},
            "axis":      axis or "all",
            "nodes":     nodes,
            "links":     links,
            "unwritten": unwritten,
        }

    # ------------------------------------------------------------------
    # Guest session handlers
    # ------------------------------------------------------------------

    def _handle_guest_create(self, rid: str, data: dict) -> dict:
        """
        Claim a pool slot and issue a self-verifying guest binding token tied to it.
        No authentication required — any HTTP client may call this.  Returns an
        opaque binding_key (prefix "gbk:") signed with the Akasha HMAC secret.
        """
        # Clamp the token TTL to the pool's inactivity TTL.  A token that outlives
        # its slot could otherwise re-activate a slot that has since been reclaimed
        # (and possibly handed to another visitor), so the two must not diverge.
        _pool_ttl = getattr(getattr(self.manager, "guest_pool", None), "ttl", 600)
        try:
            _req_ttl = int(data.get("ttl", _pool_ttl))
        except (TypeError, ValueError):
            _req_ttl = _pool_ttl
        ttl     = max(60, min(_req_ttl, _pool_ttl))
        slot_id = self.manager.checkout_guest_session()
        if slot_id is None:
            return _err(rid, -32000, "Guest pool exhausted — try again shortly.")
        binding = self.iam.guest_bindings.create_for_session(slot_id, ttl)
        return _ok(rid, {
            "binding_key": binding["binding_key"],
            "expires_at":  binding["expires_at"],
            "ttl":         ttl,
        })

    def _handle_guest_extend(self, rid: str, raw_token: str, data: dict) -> dict:
        """
        Issue a replacement token for the same session with a fresh TTL.
        Also touches the pool slot so the sweeper doesn't reclaim it early.
        Returns a new binding_key; the client should switch to it.
        """
        if not self.iam.guest_bindings.is_guest_key(raw_token):
            return _err(rid, -32001, "session.guest.extend requires a guest binding key.")
        try:
            _pool_ttl = getattr(getattr(self.manager, "guest_pool", None), "ttl", 600)
            try:
                _req_ttl = int(data.get("ttl", _pool_ttl))
            except (TypeError, ValueError):
                _req_ttl = _pool_ttl
            ttl    = max(60, min(_req_ttl, _pool_ttl))
            result = self.iam.guest_bindings.extend(raw_token, ttl)
            self.manager.touch_guest_session(result["session_id"])
            return _ok(rid, {
                "binding_key": result["binding_key"],
                "expires_at":  result["expires_at"],
                "ttl":         ttl,
            })
        except PermissionError as e:
            return _err(rid, -32001, str(e))

    def _handle_session_ctx_set(self, rid: str, data: dict, session) -> dict:
        """Store a context value in the current Akasha session."""
        key   = data.get("key")
        value = data.get("value")
        if not key:
            return _err(rid, -32602, "session.context.set requires 'key'.")
        session.set_context(key, value)
        return _ok(rid, {"key": key, "stored": True})

    def _handle_session_ctx_get(self, rid: str, data: dict, session) -> dict:
        """Retrieve a context value from the current Akasha session."""
        key = data.get("key")
        if not key:
            return _err(rid, -32602, "session.context.get requires 'key'.")
        return _ok(rid, {"key": key, "value": session.get_context(key)})

    # ------------------------------------------------------------------
    # Plugin registration
    # ------------------------------------------------------------------

    def _register_harmonia_plugins(self):
        """Wire up the cognitive metabolism plugins that Harmonia orchestrates.

        nlp.extract is registered by lib/harmonia/plugins/__init__.py (MultiLocaleNLP
        via SpaCy) and is already present in self.harmonia._plugins by the time this
        method runs.  No kernel-level override is needed.
        """
        if not self.harmonia:
            return
        logger.info("[Kernel] Harmonia plugin hook ready (nlp.extract via plugins/__init__)")
