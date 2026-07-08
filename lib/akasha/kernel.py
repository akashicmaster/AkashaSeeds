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
    from lib.akasha.jcl.job import CLASS_BATCH_ATOM, CLASS_LINK
except ImportError:
    JCLWorker = None  # type: ignore
    JCLJob    = None  # type: ignore
    JCLStep   = None  # type: ignore
    CLASS_BATCH_ATOM = "batch_atom"  # type: ignore
    CLASS_LINK       = "link"        # type: ignore

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
    """
    try:
        from lib.harmonia.plugins.nlp import nlp_manager as _nlp
        pairs = _nlp.lemmatize_tokens(text)
        if pairs:
            return pairs
    except Exception:
        pass
    import re as _re
    seen: set = set()
    result = []
    for tok in _re.split(r"[\W_]+", text.lower()):
        if tok and tok not in seen:
            seen.add(tok)
            result.append((tok, tok, "en", {}))
    return result


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

    def set_alias(self, key, name):
        """Register alias in nucleus with proto-word auto-creation."""
        return self._nuc.set_alias(key, name)

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

        if not JCLJob or not JCLStep:
            return  # JCL imports failed at module load

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

            # Manifest hash: sha256 of (basename:size) for all files.
            # Detects both new/removed files and content edits that change file size.
            # Uses stat (no file reads) so it is fast even for large ontologies.
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
                    logger.info("[Kernel] Pack '%s': atoms sentinel found — collecting links only…", pack_name)
                    for fpath in ak_files:
                        try:
                            with open(fpath, "r", encoding="utf-8") as _f:
                                for raw in _f:
                                    s = _parse_ak_line(raw)
                                    if s is None:
                                        continue
                                    if s["method"] == "kernel.memory.link":
                                        all_link_steps.append(s)
                                    elif s["method"] == "kernel.memory.define":
                                        _p = s["params"]
                                        _desc = _p.get("description", "")
                                        if _desc and not _desc.startswith("Conceptual hub:"):
                                            all_atom_defs.append({
                                                "alias": _p.get("name", ""),
                                                "text": _desc,
                                            })
                        except Exception as exc:
                            logger.warning("[Kernel] Pack '%s' links (recovery) %s: %s",
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
                                    if s["method"] == "kernel.memory.link":
                                        all_link_steps.append(s)
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
                _p3_queued = False
                if all_atom_defs and self.jcl_worker and JCLJob and JCLStep:
                    self.harmonia.submit_job(JCLJob(
                        owner="admin",
                        label=f"sys.weaver.batch:{pack_name}",
                        steps=[JCLStep(method="sys.weaver.weave_batch",
                                       params={"items": all_atom_defs})],
                        fail_fast=False,
                    ))
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
            # autoload:false → load only if pack name is in config/ontology_packs.json["enabled"]
            _enabled = _read_enabled_packs()
            for _pkg in _read_registry():
                _pname     = _pkg.get("name", "")
                _autoload  = _pkg.get("autoload", False)
                if not _pname or _pname in RESERVED_DIRS:
                    continue
                if not _autoload and _pname not in _enabled:
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

        except Exception as exc:
            logger.warning("[Kernel] Ontology boot load failed (non-fatal): %s", exc, exc_info=True)

    def _schedule_semantic_learn(self) -> None:
        """After the ontology is loaded, learn the distributional embedding model in the
        background so semantic.search / dream are smart from (shortly after) startup —
        with no external model. Non-blocking (a daemon thread), numpy-gated, and skipped
        if a model already exists. Set AKASHA_NO_AUTOLEARN=1 to disable. This is the
        'startup makes Akasha an order smarter' hook: the graph learns from itself."""
        if os.environ.get("AKASHA_NO_AUTOLEARN"):
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
                if get_shared_model(nucleus) is not None:     # already learned/persisted
                    return
                import json as _json
                chunks = nucleus.core.get_all_chunks() or []
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
                    if len(docs) >= 40000:
                        break
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
                    if baked >= 40000:
                        break
                if baked:
                    logger.info("[Kernel] Learned vectors baked into %d atoms", baked)
            except Exception as exc:                          # never break boot
                logger.warning("[Kernel] Auto semantic.learn failed (non-fatal): %s", exc)

        import threading
        threading.Thread(target=_run, name="semantic-autolearn", daemon=True).start()

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

        # Map full RPC method names to the capability action tokens IAM understands
        action = _METHOD_TO_ACTION.get(method, method)
        try:
            authorized = self.iam.authorize(role, action, data)
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
        # its atom/link bundle (祖語 + w + set + alias — the ~4-6-write critical
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

        if method in ("semantic.search", "search"):
            return self._handle_semantic_search(rid, data, session, ctx, scopes)

        if method == "semantic.learn":
            return self._handle_semantic_learn(rid, data, session, ctx, scopes)

        if method in ("gap.scan", "gaps"):
            return self._handle_gap_scan(rid, data, session, ctx, scopes)

        if method in ("gap.fetch", "gap.enrich"):
            return self._handle_gap_fetch(rid, data, session, ctx, scopes, client_id)

        # ── Dive / View ────────────────────────────────────────────────
        if method in ("dive.look", "look"):
            return self._handle_dive_look(rid, data, session, scopes)

        if method in ("dive.out", "out"):
            return self._handle_dive_out(rid, data, session, scopes)

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

        # ── Notes ─────────────────────────────────────────────────────
        if NoteConcept:
            if method == "note.new":       return self._handle_note_new(rid, data, session)
            if method == "note.add":       return self._handle_note_add(rid, data, session)
            if method == "note.section":   return self._handle_note_section(rid, data, session)
            if method == "note.paragraph": return self._handle_note_paragraph(rid, data, session)
            if method == "note.toc":       return self._handle_note_toc(rid, data, session)
            if method == "note.read":      return self._handle_note_read(rid, data, session)
            if method == "note.list":      return self._handle_note_list(rid, data, session)
            if method == "note.edit":      return self._handle_note_edit(rid, data, session)
            if method == "note.move":      return self._handle_note_move(rid, data, session)
            if method == "note.undo":      return self._handle_note_undo(rid, data, session)
            if method == "note.redo":      return self._handle_note_redo(rid, data, session)
            if method == "note.restore":   return self._handle_note_restore(rid, data, session)
            if method == "note.rename":    return self._handle_note_rename(rid, data, session)
            if method == "note.rm":        return self._handle_note_rm(rid, data, session)
            if method == "note.ls":        return self._handle_note_ls(rid, ctx, client_id)
            if method == "note.open":      return self._handle_note_open(rid, data, session, ctx)
            if method == "note.export":    return self._handle_note_export(rid, session)
            if method == "note.import":    return self._handle_note_import(rid, data, session)
            if method == "note.clone":     return self._handle_note_clone(rid, session)
            # Loom — same operations, isolated under namespace="loom"
            if method == "loom.note.new":     return self._handle_note_new(rid, data, session, namespace="loom")
            if method == "loom.note.add":     return self._handle_note_add(rid, data, session, namespace="loom")
            if method == "loom.note.read":    return self._handle_note_read(rid, data, session, namespace="loom")
            if method == "loom.note.list":    return self._handle_note_list(rid, data, session, namespace="loom")
            if method == "loom.note.rm":      return self._handle_note_rm(rid, data, session, namespace="loom")
            if method == "loom.note.edit":    return self._handle_note_edit(rid, data, session, namespace="loom")
            if method == "loom.note.move":    return self._handle_note_move(rid, data, session, namespace="loom")
            if method == "loom.note.undo":    return self._handle_note_undo(rid, data, session, namespace="loom")
            if method == "loom.note.redo":    return self._handle_note_redo(rid, data, session, namespace="loom")
            if method == "loom.note.restore": return self._handle_note_restore(rid, data, session, namespace="loom")
            if method == "loom.note.rename":  return self._handle_note_rename(rid, data, session, namespace="loom")
            if method == "loom.note.ls":      return self._handle_note_ls(rid, ctx, client_id)
            if method == "loom.note.open":    return self._handle_note_open(rid, data, session, ctx, namespace="loom")
            if method == "loom.note.export":  return self._handle_note_export(rid, session, namespace="loom")
            if method == "loom.note.import":  return self._handle_note_import(rid, data, session, namespace="loom")
            if method == "loom.note.clone":   return self._handle_note_clone(rid, session, namespace="loom")

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

        # ── FieldNote ─────────────────────────────────────────────────
        if FieldNoteConcept:
            if method == "fieldnote.new":    return self._handle_fieldnote_new(rid, data, session)
            if method == "fieldnote.ls":     return self._handle_fieldnote_ls(rid, session)
            if method == "fieldnote.open":   return self._handle_fieldnote_open(rid, data, session)
            if method == "fieldnote.add":    return self._handle_fieldnote_add(rid, data, session)
            if method == "fieldnote.read":   return self._handle_fieldnote_read(rid, session)
            if method == "fieldnote.rm":     return self._handle_fieldnote_rm(rid, session)
            if method == "fieldnote.export": return self._handle_fieldnote_export(rid, session)
            if method == "fieldnote.import": return self._handle_fieldnote_import(rid, data, session)

        # ── Survey ────────────────────────────────────────────────────
        if SurveyConcept:
            if method == "survey.new":     return self._handle_survey_new(rid, data, session)
            if method == "survey.open":    return self._handle_survey_open(rid, data, session)
            if method == "survey.ls":      return self._handle_survey_ls(rid, session)
            if method == "survey.q.add":   return self._handle_survey_add_question(rid, data, session)
            if method == "survey.opt.add": return self._handle_survey_add_option(rid, data, session)
            if method == "survey.res.add": return self._handle_survey_add_respondent(rid, data, session)
            if method == "survey.ans":     return self._handle_survey_add_response(rid, data, session)
            if method == "survey.list":    return self._handle_survey_list(rid, session)
            if method == "survey.rm":      return self._handle_survey_rm(rid, session)

        # ── Associate ─────────────────────────────────────────────────
        if method == "kernel.associate":
            return self._handle_associate(rid, data, session, ctx, scopes, history)

        if method == "associate.unwritten":
            return self._handle_associate_unwritten(rid, data, session, ctx, scopes)

        if method in ("emotion.profile", "emo.vector", "emo.profile"):
            return self._handle_emotion_profile(rid, data, session, ctx, scopes)

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

        # ── Jataka ────────────────────────────────────────────────────
        if method in ("jataka.dream", "dream"):
            return self._handle_jataka_dream(rid, data, session, ctx, scopes, history)

        # ── Contexa ───────────────────────────────────────────────────
        if method in ("contexa.fetch", "fetch"):
            return self._handle_contexa_fetch(rid, data, session, ctx, scopes, client_id)

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
        # Try to attach session context if client is known; degrade gracefully
        session = None
        try:
            role = self.iam.authenticate(client_id)
            session = self.manager.get_session(client_id)
        except (PermissionError, Exception):
            pass

        if session:
            return _ok(rid, session.consciousness.ping(session))

        # Kernel alive but no session: report via any available consciousness
        if self.manager.sessions:
            first_session = next(iter(self.manager.sessions.values()))
            return _ok(rid, first_session.consciousness.ping(None))

        return _ok(rid, {
            "status": "kernel_online",
            "series": self.series,
            "timestamp": time.time(),
            "note": "No sessions active; full cogito unavailable without a session."
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
        try:
            limit = min(int(data.get("limit", 10)), 100)
        except (TypeError, ValueError):
            limit = 10
        raw = ctx.stream(limit * 5 + 20)
        # su root: expose all atoms including system-owned ones
        if scopes and "scope:sys:root" in scopes:
            user_atoms = raw[:limit]
        else:
            # Keep only atoms authored by this user; exclude internal sys: atoms.
            user_atoms = [item for item in raw
                          if item.get("author") == client_id and not _is_sys_atom(item)][:limit]
        atoms = []
        for i, item in enumerate(user_atoms):
            key     = item.get("key", "")
            content = item.get("content") or ctx.get_chunk(key) or ""
            aliases = ctx.get_aliases_by_key(key)
            atoms.append({"idx": i, "key": key, "preview": content[:60], "aliases": aliases})
        return _ok(rid, {"atoms": atoms, "count": len(atoms)})

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
            admin_name, akasha_name = None, "AKASHA"
        return _ok(rid, {
            "initialized": admin_name is not None,
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
        ctx.set_alias(key, name)

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
        def _link_entry(key: str, rel: str, direction: str) -> dict:
            if not ctx.check_access(key, scopes):
                return {
                    "key":       key,
                    "rel":       rel,
                    "direction": direction,
                    "aliases":   [],
                    "preview":   "",
                    "restricted": True,
                }
            preview = ctx.get_chunk(key) or ""
            return {
                "key":       key,
                "rel":       rel,
                "direction": direction,
                "aliases":   ctx.get_aliases_by_key(key),
                "preview":   preview[:60],
            }

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

        return _ok(rid, {
            "key":      resolved,
            "content":  content,
            "meta":     meta,
            "aliases":  aliases,
            "out_links": out_links,
            "in_links":  in_links,
            "sets":     sets,
        })

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
        if isinstance(ctx, _NucleusWriteCtx):
            # Late-binding: auto-create proto-words for any unresolved alias.
            # Using the bare segment (last ':'-delimited token) as the universal
            # anchor means ordering and repeated execution are both irrelevant.
            # When the qualified atom is later defined, it links back to the
            # same proto-word via 'specializes', making the graph path traversable.
            if _src_alias_resolved is None:
                bare_src = src.rsplit(":", 1)[-1] if ":" in src else src
                src_key = nucleus._ensure_protoword(bare_src)
            if _dst_alias_resolved is None:
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
        return _ok(rid, {"key": resolved, "links": links})

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
        limit   = min(int(data.get("limit") or 500), 5000)
        pattern = (data.get("pattern") or "")

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
            return _ok(rid, {"mode": mode, "count": len(items), "items": items[:limit]})

        if mode in ("links", "antonyms"):
            effective_rel = "sys:antonym" if mode == "antonyms" else rel_f
            rows = ctx.core.get_all_links(rel_filter=effective_rel or None, limit=limit * 2)
            items = []
            for r in rows:
                src_a = _best_alias(r["src"])
                dst_a = _best_alias(r["dst"])
                items.append({"src": src_a, "dst": dst_a, "rel": r["rel"], "w": r["w"]})
            if sort == "alpha":
                items.sort(key=lambda x: (x["rel"], x["src"]))
            return _ok(rid, {"mode": mode, "count": len(items), "items": items[:limit]})

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
            return _ok(rid, {"mode": mode, "collection": name, "count": len(items), "items": items[:limit]})

        if mode == "aliases":
            pat = pattern or (f"{ns}:%" if ns else "%")
            rows = ctx.core.get_aliases_by_pattern(pat)
            items = [{"alias": r["alias"], "key": r["key"][:12]} for r in rows]
            if sort == "alpha":
                items.sort(key=lambda x: x["alias"])
            return _ok(rid, {"mode": mode, "count": len(items), "items": items[:limit]})

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
        for r in alias_rows[: limit * 4]:
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
        return _ok(rid, {"mode": mode, "count": len(items), "items": items[:limit]})

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
                enabled = set(_json.load(f).get("enabled", []))
        except Exception:
            enabled = set()

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
                "enabled":     autoload or pname in enabled,
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
        if pack_name == "base":
            return _err(rid, -32602, "Pack 'base' has autoload:true — no enable needed.")

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
        if pack_name == "base":
            return _err(rid, -32602, "Pack 'base' is built-in and cannot be disabled.")

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
                    })
        except Exception:
            pass

        enabled_packs = []
        try:
            with open(cfg_path) as f:
                enabled_packs = _json.load(f).get("enabled", [])
        except Exception:
            pass

        return _ok(rid, {
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
            # Importance: how referenced this concept is — weave mentions (sys:refers_to)
            # plus any other inbound links. A concept many atoms point to is important.
            importance = len(ctx.get_incoming_links(key) or [])
            if importance < 1:
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

    def _handle_semantic_search(self, rid, data, session, ctx, scopes) -> dict:
        """semantic.search query= [limit=] [scan=] — rank atoms by cosine similarity to
        the query. Scope-filtered (fail-closed). Uses the learned model when one has been
        built (semantic.learn) — re-embedding candidates via the model so query and corpus
        share one space — otherwise the stored feature-hashing vectors. `tier` says which."""
        query = (data.get("query") or data.get("q") or data.get("id") or "").strip()
        if not query:
            return _err(rid, -32602, "semantic.search requires 'query'")
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

        import json as _json
        scored = []
        for row in (ctx.stream(limit=scan) or []):
            key = row.get("key")
            if not key or (scopes and not ctx.check_access(key, scopes)):
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
        results = [{"key": k, "score": round(s, 4), "preview": c[:80]}
                   for s, k, c in scored[:limit]]
        return _ok(rid, {"query": query, "results": results,
                         "count": len(results), "tier": tier})

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

        # ── Collect candidate keys ───────────────────────────────────────
        # candidate_keys: dict {key → alias_or_None} or None (not yet filtered)
        candidate_keys = None

        # Pattern / namespace → alias search
        if pat or ns:
            pattern = pat if pat else f"{ns}:%"
            # Auto-add wildcard suffix if no wildcards present
            if "%" not in pattern and "_" not in pattern:
                pattern = f"{pattern}%"

            rows = ctx.get_aliases_by_pattern(pattern)
            seen_k = {r["key"] for r in rows}
            if nucleus:
                for r in nucleus.core.get_aliases_by_pattern(pattern) or []:
                    if r["key"] not in seen_k:
                        rows.append(r)
                        seen_k.add(r["key"])
            # Group-space atoms shared into the caller's groups (scope-gated).
            for _gid, _ge in (self._member_group_engines(session, scopes) if session else []):
                for r in (_ge.core.get_aliases_by_pattern(pattern) or []):
                    if r["key"] not in seen_k:
                        rows.append(r)
                        seen_k.add(r["key"])

            pat_keys = {}
            for r in rows:
                if r["key"] not in pat_keys:
                    pat_keys[r["key"]] = r.get("alias")

            candidate_keys = pat_keys if candidate_keys is None else {
                k: v for k, v in pat_keys.items() if k in candidate_keys
            }

        # Set membership filter
        if set_filt:
            normalized = set_filt if set_filt.startswith("set:") else f"set:{set_filt}"
            set_members = set(ctx.get_collection_members(normalized))
            # A shared set's membership lives in the group engine.
            for _gid, _ge in (self._member_group_engines(session, scopes) if session else []):
                set_members |= set(_ge.core.get_collection_members(normalized))

            if candidate_keys is None:
                candidate_keys = {k: None for k in set_members}
            else:
                candidate_keys = {k: v for k, v in candidate_keys.items() if k in set_members}

        if candidate_keys is None:
            candidate_keys = {}

        # Meta-type filter (checked against raw chunk meta)
        if atom_type:
            filtered: Dict[str, Any] = {}
            for k, alias in list(candidate_keys.items())[: limit * 4]:
                raw = None
                try:
                    raw = ctx.core.get_chunk_raw(k)
                except Exception:
                    pass
                if not raw and nucleus:
                    try:
                        raw = nucleus.core.get_chunk_raw(k)
                    except Exception:
                        pass
                if not raw:
                    for _gid, _ge in (self._member_group_engines(session, scopes) if session else []):
                        try:
                            raw = _ge.core.get_chunk_raw(k)
                        except Exception:
                            raw = None
                        if raw:
                            break
                if raw:
                    try:
                        meta = json.loads(raw.get("meta", "{}") or "{}")
                    except Exception:
                        meta = {}
                    if meta.get("type") == atom_type or meta.get("rec_type") == atom_type:
                        filtered[k] = alias
            candidate_keys = filtered

        # ── Build result list ────────────────────────────────────────────
        group_engines = self._member_group_engines(session, scopes) if session else []
        results = []
        for k, alias in list(candidate_keys.items())[:limit]:
            # Fail-closed: check_access denies when scopes is empty, so no
            # `scopes and ...` short-circuit that would leak on an empty list.
            src = ctx
            if not ctx.check_access(k, scopes):
                # Not in the local cortex/scope — is it shared into one of the
                # caller's groups? If so, read it from that group engine; if not,
                # it stays black-holed (another member's private atom).
                src = next((ge for _gid, ge in group_engines if ge.check_access(k)), None)
                if src is None:
                    continue
            if alias is None:
                als = src.get_aliases_by_key(k)
                alias = als[0] if als else None
            content = src.get_chunk(k) or ""
            results.append({
                "key":     k,
                "alias":   alias,
                "preview": content[:60],
                "color":   CosmosMapper.get_aura_color(ctx, k),
            })

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
        """
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
        key = ctx.resolve_alias(target) or target
        # If key belongs to nucleus, track the set membership there so all cells see it.
        nucleus = getattr(session, 'nucleus', None)
        _in_nucleus = bool(nucleus and nucleus.core.get_chunk_raw(key))
        if _in_nucleus:
            nucleus.add_to_set(name, key)
        else:
            ctx.add_to_set(name, key)
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
        for m in members:
            aliases = ctx.get_aliases_by_key(m["key"])
            if not aliases and group_engines:
                for _gid, _ge in group_engines:
                    aliases = _ge.get_aliases_by_key(m["key"])
                    if aliases:
                        break
            m["alias"] = aliases[0] if aliases else None
        return _ok(rid, {"set": name, "members": members, "count": len(members)})

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
    # Notes
    # ------------------------------------------------------------------

    def _note_concept(self, session, namespace=None):
        return NoteConcept(session, namespace=namespace)

    def _handle_note_new(self, rid, data, session, namespace=None) -> dict:
        title = data.get("title") or data.get("name", "")
        if not title:
            return _err(rid, -32602, "note.new requires 'title'")
        concept = self._note_concept(session, namespace)
        try:
            res = concept.op_new(title=title)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_add(self, rid, data, session, namespace=None) -> dict:
        text = data.get("text") if data.get("text") is not None else data.get("content", "")
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_add_chunk(text=text)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_section(self, rid, data, session, namespace=None) -> dict:
        title = data.get("title", "")
        role  = data.get("role", "section")
        if not title:
            return _err(rid, -32602, "note.section requires 'title'")
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_section(title=title, role=role)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_paragraph(self, rid, data, session, namespace=None) -> dict:
        category = data.get("category", "memo")
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_paragraph(category=category)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_toc(self, rid, data, session, namespace=None) -> dict:
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            toc = concept.op_toc()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, toc)

    def _handle_note_read(self, rid, data, session, namespace=None) -> dict:
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            seq = concept.op_get_sequential_text()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, seq)

    def _handle_note_list(self, rid, data, session, namespace=None) -> dict:
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_list_chunks(head_len=data.get("head_len", 80) if data else 80)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_edit(self, rid, data, session, namespace=None) -> dict:
        chunk_id = data.get("chunk_id") or data.get("id", "")
        text = data.get("text", "")
        if not chunk_id:
            return _err(rid, -32602, "note.edit requires 'chunk_id'")
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_edit_chunk(chunk_id=chunk_id, text=text)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_move(self, rid, data, session, namespace=None) -> dict:
        chunk_id = data.get("chunk_id") or data.get("id", "")
        after    = data.get("after")
        if not chunk_id:
            return _err(rid, -32602, "note.move requires 'chunk_id'")
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_move_chunk(chunk_id=chunk_id, after=after)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_undo(self, rid, data, session, namespace=None) -> dict:
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_undo_edit()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_redo(self, rid, data, session, namespace=None) -> dict:
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_redo_edit()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_restore(self, rid, data, session, namespace=None) -> dict:
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_restore_original()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_rename(self, rid, data, session, namespace=None) -> dict:
        title = data.get("title", "")
        if not title:
            return _err(rid, -32602, "note.rename requires 'title'")
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_rename(title=title)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_rm(self, rid, data, session, namespace=None) -> dict:
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new first.")
        try:
            res = concept.op_delete()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_note_export(self, rid, session, namespace=None) -> dict:
        """Export the active note as an Akasha capsule file."""
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.new or note.open first.")
        try:
            from .capsule import KnowledgeCapsule
            doc_type   = f"{namespace}:note" if namespace else "note"
            set_name   = f"set:note:{concept.concept_id}"
            capsule_json = KnowledgeCapsule(session).encapsulate_document(
                concept_id = concept.concept_id,
                set_name   = set_name,
                doc_type   = doc_type,
                scopes     = session.active_scopes,
            )
            return _ok(rid, {"capsule": capsule_json,
                              "doc_type": doc_type,
                              "concept_id": concept.concept_id})
        except Exception as e:
            return _err(rid, -32603, str(e))

    def _handle_note_import(self, rid, data, session, namespace=None) -> dict:
        """Import a note from an Akasha capsule.  Atoms land in a pending isolation scope."""
        capsule_json = (data or {}).get("capsule", "")
        if not capsule_json:
            return _err(rid, -32602, "note.import requires 'capsule' (Akasha capsule JSON string)")
        try:
            from .capsule import KnowledgeCapsule
            result = KnowledgeCapsule(session).decapsulate(capsule_json)
            return _ok(rid, result)
        except Exception as e:
            return _err(rid, -32603, str(e))

    def _handle_note_clone(self, rid, session, namespace=None) -> dict:
        """Duplicate the active note as a new user-owned document."""
        concept = self._note_concept(session, namespace)
        if not concept.concept_id:
            return _err(rid, -32002, "No active note. Use note.open first.")
        try:
            return _ok(rid, concept.op_clone())
        except Exception as e:
            return _err(rid, -32603, str(e))

    def _handle_note_ls(self, rid, ctx, client_id: str) -> dict:
        rows = ctx.fetch_by_meta_field("concept", "note", author=client_id)
        notes = []
        for row in rows:
            try:
                meta = json.loads(row.get("meta") or "{}")
            except Exception:
                meta = {}
            if meta.get("role") == "document":
                notes.append({
                    "note_id":    row["key"],
                    "title":      meta.get("title", ""),
                    "created_at": meta.get("created_at", 0),
                })
        notes.sort(key=lambda x: x["created_at"], reverse=True)
        return _ok(rid, {"notes": notes})

    def _handle_note_open(self, rid, data, session, ctx, namespace=None) -> dict:
        note_id = data.get("note_id", "").strip()
        if not note_id:
            return _err(rid, -32602, "note.open requires 'note_id'")
        try:
            meta = ctx.get_meta(note_id)
        except Exception:
            meta = {}
        if not meta or meta.get("concept") != "note":
            return _err(rid, -32002, f"Note '{note_id[:12]}' not found")
        ns = f"{namespace}:" if namespace else ""
        session.set_context(f"{ns}active_note_root", note_id)
        session.set_context(f"{ns}active_container_id", note_id)
        return _ok(rid, {"status": "opened", "note_id": note_id, "title": meta.get("title", "")})

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
    # FieldNote (fieldnote.*)
    # ------------------------------------------------------------------

    def _handle_fieldnote_new(self, rid, data, session) -> dict:
        title = data.get("title") or data.get("name", "")
        if not title:
            return _err(rid, -32602, "fieldnote.new requires 'title'")
        try:
            res = FieldNoteConcept(session).op_new(
                title   = title,
                project = data.get("project") or None,
                region  = data.get("region")  or None,
                season  = data.get("season")  or None,
            )
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_fieldnote_ls(self, rid, session) -> dict:
        try:
            res = FieldNoteConcept(session).op_list()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_fieldnote_open(self, rid, data, session) -> dict:
        fieldnote_id = data.get("fieldnote_id", "").strip()
        if not fieldnote_id:
            return _err(rid, -32602, "fieldnote.open requires 'fieldnote_id'")
        try:
            res = FieldNoteConcept(session).op_open(fieldnote_id)
        except RuntimeError as e:
            return _err(rid, -32002, str(e))
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_fieldnote_add(self, rid, data, session) -> dict:
        text = data.get("text") or data.get("observation", "")
        if not text:
            return _err(rid, -32602, "fieldnote.add requires 'text'")
        concept = FieldNoteConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active fieldnote. Use fieldnote.new or fieldnote.open first.")
        role       = data.get("role", "observation")
        period     = data.get("period") or None
        confidence = data.get("confidence")
        if confidence is not None:
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = None
        try:
            res = concept.op_add(text=text, role=role, period=period, confidence=confidence)
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_fieldnote_read(self, rid, session) -> dict:
        concept = FieldNoteConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active fieldnote. Use fieldnote.new or fieldnote.open first.")
        try:
            sequence = concept.op_read()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, {"observations": sequence, "count": len(sequence)})

    def _handle_fieldnote_rm(self, rid, session) -> dict:
        concept = FieldNoteConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active fieldnote. Use fieldnote.new or fieldnote.open first.")
        try:
            res = concept.op_delete()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_fieldnote_export(self, rid, session) -> dict:
        """Export the active fieldnote as an Akasha capsule file."""
        concept = FieldNoteConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active fieldnote. Use fieldnote.new or fieldnote.open first.")
        try:
            from .capsule import KnowledgeCapsule
            set_name     = f"set:fieldnote:{concept.concept_id}"
            capsule_json = KnowledgeCapsule(session).encapsulate_document(
                concept_id = concept.concept_id,
                set_name   = set_name,
                doc_type   = "fieldnote",
                scopes     = session.active_scopes,
            )
            return _ok(rid, {"capsule": capsule_json,
                              "doc_type": "fieldnote",
                              "concept_id": concept.concept_id})
        except Exception as e:
            return _err(rid, -32603, str(e))

    def _handle_fieldnote_import(self, rid, data, session) -> dict:
        """Import a fieldnote from an Akasha capsule.  Atoms land in a pending isolation scope."""
        capsule_json = (data or {}).get("capsule", "")
        if not capsule_json:
            return _err(rid, -32602, "fieldnote.import requires 'capsule' (Akasha capsule JSON string)")
        try:
            from .capsule import KnowledgeCapsule
            result = KnowledgeCapsule(session).decapsulate(capsule_json)
            return _ok(rid, result)
        except Exception as e:
            return _err(rid, -32603, str(e))

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
    # Survey (survey.*)
    # ------------------------------------------------------------------

    def _handle_survey_new(self, rid, data, session) -> dict:
        title = data.get("title", "").strip()
        if not title:
            return _err(rid, -32602, "survey.new requires 'title'")
        try:
            res = SurveyConcept(session).op_new(
                title=title,
                description=data.get("description") or None,
            )
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_survey_open(self, rid, data, session) -> dict:
        survey_id = data.get("survey_id", "").strip()
        if not survey_id:
            return _err(rid, -32602, "survey.open requires 'survey_id'")
        try:
            res = SurveyConcept(session).op_open(survey_id)
        except RuntimeError as e:
            return _err(rid, -32002, str(e))
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_survey_ls(self, rid, session) -> dict:
        try:
            res = SurveyConcept(session).op_surveys()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_survey_add_question(self, rid, data, session) -> dict:
        text = data.get("text", "").strip()
        if not text:
            return _err(rid, -32602, "survey.q.add requires 'text'")
        concept = SurveyConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active survey. Use survey.new or survey.open first.")
        try:
            res = concept.op_add_question(
                text=text,
                qtype=data.get("qtype", "free_text"),
                order=data.get("order"),
            )
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_survey_add_option(self, rid, data, session) -> dict:
        question_id = data.get("question_id", "").strip()
        label       = data.get("label", "").strip()
        if not question_id or not label:
            return _err(rid, -32602, "survey.opt.add requires 'question_id' and 'label'")
        concept = SurveyConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active survey.")
        try:
            res = concept.op_add_option(
                question_id=question_id,
                label=label,
                value=data.get("value") or None,
            )
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_survey_add_respondent(self, rid, data, session) -> dict:
        respondent_id = data.get("respondent_id", "").strip()
        if not respondent_id:
            return _err(rid, -32602, "survey.res.add requires 'respondent_id'")
        concept = SurveyConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active survey.")
        try:
            res = concept.op_add_respondent(
                respondent_id=respondent_id,
                attributes=data.get("attributes"),
            )
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_survey_add_response(self, rid, data, session) -> dict:
        question_id     = data.get("question_id", "").strip()
        respondent_atom = data.get("respondent_atom", "").strip()
        answer          = data.get("answer")
        if not question_id or not respondent_atom or answer is None:
            return _err(rid, -32602, "survey.ans requires 'question_id', 'respondent_atom', 'answer'")
        concept = SurveyConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active survey.")
        try:
            res = concept.op_add_response(
                question_id=question_id,
                respondent_atom=respondent_atom,
                answer=answer,
            )
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_survey_list(self, rid, session) -> dict:
        concept = SurveyConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active survey.")
        try:
            res = concept.op_list()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

    def _handle_survey_rm(self, rid, session) -> dict:
        concept = SurveyConcept(session)
        if not concept.concept_id:
            return _err(rid, -32002, "No active survey.")
        try:
            res = concept.op_delete()
        except Exception as e:
            return _err(rid, -32603, str(e))
        return _ok(rid, res)

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

    def _handle_jataka_dream(self, rid, data, session, ctx, scopes, history) -> dict:
        """
        dream — inference-based hypothetical linking.

        Uses all available knowledge processing (JatakaEngine, vector proximity,
        structural inference) to propose links that do not yet exist.
        Proposed links are written with a 'tent:' prefix (tentative).

        Parameters:
          id=     focus atom (optional; without id, runs a free dream cycle)
          axis=   focus on one semantic axis (optional)
          commit= yes → write tent: links; no (default) → return proposals only
        """
        target = (data.get("id") or "").strip()
        axis   = (data.get("axis") or "").strip() or None
        commit = data.get("commit", "").strip().lower() in ("yes", "true", "1")

        focal_key: Optional[str] = None
        if target:
            focal_key = (
                self._resolve_target(target, session, history)
                or ctx.resolve_alias(target)
                or target
            )

        proposals: List[Dict[str, Any]] = []
        _proposed_dsts: set = set()  # dedup by destination key

        def _add_proposal(p: Dict[str, Any]) -> None:
            dst = p.get("dst", "")
            if dst and dst not in _proposed_dsts:
                _proposed_dsts.add(dst)
                proposals.append(p)

        # ── JatakaEngine: vector/Jaccard affinity discovery ────────────
        if session.jataka and focal_key:
            try:
                for hit in session.jataka.dream_affinities(ctx, focal_key):
                    dst = hit.get("dst", "")
                    if not dst:
                        continue
                    al = ctx.get_aliases_by_key(dst)
                    _add_proposal({
                        "axis":       "affinity",
                        "rel":        f"tent:{hit.get('rel', 'calc:hidden_affinity')}",
                        "dst":        dst,
                        "alias":      al[0] if al else None,
                        "preview":    hit.get("preview", ""),
                        "confidence": hit.get("confidence", 0),
                        "source":     "affinity",
                        "color":      CosmosMapper.get_aura_color(ctx, dst),
                    })
            except Exception:
                pass

        # ── Structural inference: pattern from set peers ────────────────
        if focal_key:
            voids = ctx.find_link_voids(focal_key, axis=axis, allowed_scopes=scopes)
            for void in voids:
                for cand in void.get("candidates", [])[:2]:
                    _add_proposal({
                        "axis":    void["axis"],
                        "rel":     f"tent:{cand['rel']}",
                        "dst":     cand["key"],
                        "alias":   cand.get("alias"),
                        "preview": cand.get("preview", ""),
                        "count":   cand.get("count", 0),
                        "source":  "structural",
                        "color":   CosmosMapper.get_aura_color(ctx, cand["key"]),
                    })

        # ── Transitive inference: A→B, B→C → propose tent: A→C ─────────
        if focal_key:
            try:
                a_links = ctx.get_adjacent_links(focal_key) or []
                existing_dsts = {lnk[0] for lnk in a_links} | {focal_key} | _proposed_dsts
                trans_counts: Dict[str, Dict[str, Any]] = {}
                for b_key, _rel_ab in a_links[:12]:
                    for c_key, rel_bc in (ctx.get_adjacent_links(b_key) or []):
                        if c_key in existing_dsts:
                            continue
                        # Skip meta/system rels and tent: to avoid noise
                        if rel_bc.startswith(("sys:", "tent:", "chrono:")):
                            continue
                        if c_key not in trans_counts:
                            trans_counts[c_key] = {"count": 0, "rel": rel_bc}
                        trans_counts[c_key]["count"] += 1
                for c_key, info in sorted(trans_counts.items(),
                                          key=lambda x: -x[1]["count"])[:3]:
                    al = ctx.get_aliases_by_key(c_key)
                    content = ctx.get_chunk(c_key) or ""
                    _add_proposal({
                        "axis":    "transitive",
                        "rel":     f"tent:{info['rel']}",
                        "dst":     c_key,
                        "alias":   al[0] if al else None,
                        "preview": content[:40],
                        "count":   info["count"],
                        "source":  "transitive",
                        "color":   CosmosMapper.get_aura_color(ctx, c_key),
                    })
            except Exception:
                pass

        # ── Write tentative links if commit=yes ─────────────────────────
        committed: List[Dict[str, Any]] = []
        if commit and focal_key:
            author_id = getattr(session, 'client_id', 'system')
            for p in proposals:
                dst = p.get("dst")
                rel = p.get("rel", "")
                if dst and rel:
                    if not rel.startswith("tent:"):
                        rel = f"tent:{rel}"
                    try:
                        ctx.put_link(focal_key, dst, rel, author=author_id)
                        committed.append({"rel": rel, "dst": dst, "alias": p.get("alias")})
                    except Exception:
                        pass

        focal_aliases = ctx.get_aliases_by_key(focal_key) if focal_key else []
        return _ok(rid, {
            "focal":     {"key": focal_key, "alias": focal_aliases[0] if focal_aliases else None}
                         if focal_key else None,
            "axis":      axis or "all",
            "proposals": proposals,
            "committed": committed,
            "status":    "committed" if committed else ("proposed" if proposals else "empty"),
        })

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
        """io.project src= [model=table] [into=] [depth=] — project an in-graph source (a set,
        or an atom/alias tree root) into a concept model through the lens pipeline
        (LensScanSource -> ConceptCastSink). This is the base of the general "project into any
        concept model" path and of model->model chaining; today `table` is the working target
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
        """Formats associate result as a Cosmos/3D-Force-Graph ready payload."""
        nodes: List[Dict[str, Any]] = [{
            "id":    focal["key"],
            "name":  focal["preview"],
            "alias": focal.get("alias"),
            "group": "focus",
            "val":   20,
            "color": "#ffffff",
        }]
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
                nodes.append({
                    "id":    a["key"],
                    "name":  a["preview"],
                    "alias": _alias(a["key"]),
                    "group": a.get("type", "association"),
                    "val":   10,
                    "color": color,
                })
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
                nodes.append({
                    "id":    r["key"],
                    "name":  r["preview"],
                    "alias": _alias(r["key"]),
                    "group": "resonance",
                    "val":   12,
                    "color": color,
                })
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
