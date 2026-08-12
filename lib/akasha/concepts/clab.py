"""
Concept Laboratory (Nebula) Concept Model — clab.*

An executable substrate for **thought experiments about concept formation**. A *Nebula* is a
bounded experimental field that preserves incomplete, contradictory, and competing structures
without forcing an early conclusion. Observation, Example, Evidence, Hypothesis, Interpretation,
Bridge, Concept, Consensus, Tension, and Assessment are first-class operands.

Design (see docs/for-llm/nebula-concept-model.md):
- **No forced lifecycle** — Observation → Example → Concept is a possible trajectory, not a schema.
- **Contradiction is preserved** — competing interpretations/assessments coexist; nothing is overwritten.
- **Agent attribution is mandatory for judgement** — every Assessment/Interpretation names its agent.
- **Proposal ≠ commitment** — a Bridge/Proposal is staged (`tentative`) and MUST NOT create a real
  edge in the graph until an authorized agent `clab.accept`s it. Rejected items stay queryable.
- **CLI first** — the web UI and Society surfaces call these same operators.

Naming note: this is the *Concept-Laboratory* model (prefix `clab.*`); it is distinct from the
existing inductive **Nebula cartographer** (`nebula`/`nebula.confirm`/…). The workspace object is
still called a "Nebula" conceptually. The corpus it operates on ships as the tier-C philosophy
pack `ontology/primary_examples/` (pe:* atoms, clab:* relations).
"""
import logging
import re
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Clab")

CONTEXT_KEY_ACTIVE = "active_nebula"      # session context: the open Nebula's root key

# Relations (all defined in gen_lexicon CORE_RELS, clab: namespace).
R = {
    "frames": "clab:frames", "supports": "clab:supports", "challenges": "clab:challenges",
    "interprets_as": "clab:interprets_as", "bridges": "clab:bridges", "between": "clab:between",
    "evaluates": "clab:evaluates", "stabilizes_as": "clab:stabilizes_as",
    "emerges_from": "clab:emerges_from", "reframes": "clab:reframes",
    "selects_as_example": "clab:selects_as_example", "proposes": "clab:proposes",
}
PART_OF = "sys:part_of"     # operand → its Nebula root
SOURCED_BY = "clab:sourced_by"   # research operand → citation
CITES = "clab:cites"             # citation → Source

SOURCE_TYPES = ("paper", "book", "chapter", "dataset", "webpage", "archive", "experiment_report",
                "primary_document", "secondary_source", "personal_communication", "article",
                "webpage_or_news", "other")
PROVENANCE_ROLES = ("quotes", "paraphrases", "derived_from", "supports", "challenges", "discusses",
                    "reports", "historical_source", "primary_scientific_source", "secondary_source",
                    "interpretation_of")
LOCATOR_FIELDS = ("page", "pages", "section", "chapter", "figure", "table", "paragraph",
                  "timestamp", "quote_anchor", "note")

# Operand kinds (meta.clab_kind).
KINDS = ("question", "observation", "example", "claim", "hypothesis", "interpretation",
         "bridge", "tension", "assessment", "concept", "proposal", "consensus",
         # seeds13 research primitives (Part C.9)
         "master_thesis", "cluster", "key_proof", "turning_point", "conclusion", "family")

EXAMPLE_KINDS = ("ordinary", "primary_candidate", "counterexample", "boundary", "failed",
                 "central_case", "prototype", "exemplar")


class ClabConcept(BaseConcept):
    """Create and manipulate a Nebula: a field in which a concept may emerge."""

    CONCEPT_PREFIX = "clab"
    CONCEPT_LABEL  = "Concept Laboratory — thought experiments over a Nebula (concept-formation field)"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    _W = "write"
    _R = "read"
    _CANON = {
        # ── workspace ──
        "new":     {"op": "op_new", "action": _W, "cli": "clab.new", "args": ["title"],
                    "desc": "Create a Nebula (experimental field) and open it: clab.new title=\"...\""},
        "open":    {"op": "op_open", "action": _R, "cli": "clab.open", "args": ["id"],
                    "desc": "Open an existing Nebula as the active field: clab.open id=<nebula>"},
        "status":  {"op": "op_status", "action": _R, "cli": "clab.status", "args": [],
                    "desc": "Summary of the active Nebula — operand counts + open tensions: clab.status"},
        "members": {"op": "op_members", "action": _R, "cli": "clab.members", "args": [],
                    "desc": "List operands in the active Nebula: clab.members [kind=observation] [limit=]"},
        "replay":  {"op": "op_replay", "action": _R, "cli": "clab.replay", "args": [],
                    "desc": "Reconstruct the Nebula's operands in creation order: clab.replay [limit=]"},
        "fork":    {"op": "op_fork", "action": _W, "cli": "clab.fork", "args": ["name"],
                    "desc": "Fork the active Nebula into a new branch (copy membership): clab.fork name=<branch>"},
        # ── operand creation ──
        "question":    {"op": "op_question", "action": _W, "cli": "clab.question", "args": ["text"],
                        "desc": "Frame an inquiry: clab.question text=\"...\""},
        "observe":     {"op": "op_observe", "action": _W, "cli": "clab.observe", "args": ["text"],
                        "desc": "Add an Observation: clab.observe text=\"...\" [observer=] [instrument=] [source=]"},
        "example":     {"op": "op_example", "action": _W, "cli": "clab.example", "args": ["target"],
                        "desc": "Select a case as an Example: clab.example target=<id> [kind=primary_candidate]"},
        "claim":       {"op": "op_claim", "action": _W, "cli": "clab.claim", "args": ["text"],
                        "desc": "State a Claim small enough to evaluate: clab.claim text=\"...\""},
        "hypothesize": {"op": "op_hypothesize", "action": _W, "cli": "clab.hypothesize", "args": ["text"],
                        "desc": "Propose a Hypothesis: clab.hypothesize text=\"...\""},
        "interpret":   {"op": "op_interpret", "action": _W, "cli": "clab.interpret", "args": ["target"],
                        "desc": "Add an agent-attributed Interpretation: clab.interpret target=<id> text=\"...\" [agent=]"},
        "bridge":      {"op": "op_bridge", "action": _W, "cli": "clab.bridge", "args": ["from", "to"],
                        "desc": "Stage a tentative Bridge (not committed until accepted): clab.bridge from=<id> to=<id> [rel=] rationale=\"...\""},
        "tension":     {"op": "op_tension", "action": _W, "cli": "clab.tension", "args": ["left", "right"],
                        "desc": "Record an unresolved Tension: clab.tension left=<id> right=<id> kind=<kind> [rationale=]"},
        # ── epistemic operations ──
        "support":   {"op": "op_support", "action": _W, "cli": "clab.support", "args": ["evidence", "target"],
                      "desc": "Assert evidence supports a target: clab.support evidence=<id> target=<id> [rationale=]"},
        "challenge": {"op": "op_challenge", "action": _W, "cli": "clab.challenge", "args": ["evidence", "target"],
                      "desc": "Assert evidence challenges a target: clab.challenge evidence=<id> target=<id> [rationale=]"},
        "assess":    {"op": "op_assess", "action": _W, "cli": "clab.assess", "args": ["target"],
                      "desc": "Evaluate a target under a criterion (agent-attributed, non-overwriting): clab.assess target=<id> criterion=pertinence judgement=strong rationale=\"...\""},
        "compare":   {"op": "op_compare", "action": _R, "cli": "clab.compare", "args": ["targets"],
                      "desc": "Compare targets under criteria — shows every agent's assessment, dissent preserved: clab.compare targets=<a,b,...> [by=<criterion,...>]"},
        "stabilize": {"op": "op_stabilize", "action": _W, "cli": "clab.stabilize", "args": ["target"],
                      "desc": "Treat a pattern as a (provisional) Concept — never deletes precursors: clab.stabilize target=<id> as=<name> [rationale=]"},
        "reframe":   {"op": "op_reframe", "action": _W, "cli": "clab.reframe", "args": ["target"],
                      "desc": "Reframe a target (keeps the original): clab.reframe target=<id> text=\"...\""},
        # ── human / LLM proposal boundary ──
        "propose": {"op": "op_propose", "action": _W, "cli": "clab.propose", "args": ["text"],
                    "desc": "Stage a proposal (does not mutate stable state until accepted): clab.propose text=\"...\" [from=] [to=] [rel=]"},
        "accept":  {"op": "op_accept", "action": _W, "cli": "clab.accept", "args": ["proposal"],
                    "desc": "Accept a staged proposal/bridge — materializes its edge: clab.accept proposal=<id>"},
        "reject":  {"op": "op_reject", "action": _W, "cli": "clab.reject", "args": ["proposal"],
                    "desc": "Reject a staged proposal/bridge — stays queryable for replay: clab.reject proposal=<id> [rationale=]"},
        # ── research provenance (iteration 0.3) ──
        "source.add":    {"op": "op_source_add", "action": _W, "cli": "clab.source.add", "args": ["title"],
                          "desc": "Register a research Source: clab.source.add title=\"...\" [author=] [year=] [type=paper] [doi=] [url=] [journal=] [pages=] [note=]"},
        "source.link":   {"op": "op_source_link", "action": _W, "cli": "clab.source.link", "args": ["target", "source"],
                          "desc": "Link a Source to an operand with a locator (role belongs to the link): clab.source.link target=<id> source=<src> role=derived_from [pages=] [section=] [note=]"},
        "source.show":   {"op": "op_source_show", "action": _R, "cli": "clab.source.show", "args": ["id"],
                          "desc": "Show a Source's bibliography + every linked operand and locator: clab.source.show id=<src>"},
        "source.list":   {"op": "op_source_list", "action": _R, "cli": "clab.source.list", "args": [],
                          "desc": "List registered Sources: clab.source.list"},
        "source.unlink": {"op": "op_source_unlink", "action": _W, "cli": "clab.source.unlink", "args": ["target", "source"],
                          "desc": "Remove a provenance link (the Source itself is kept): clab.source.unlink target=<id> source=<src>"},
        "trace":   {"op": "op_trace", "action": _R, "cli": "clab.trace", "args": ["target"],
                    "desc": ("Trace the meaning-provenance genealogy of an operand — sources, observations, "
                             "assessments (dissent preserved), interpretations, tensions, stabilization: "
                             "clab.trace target=<id> [depth=all] [include=rejected] [order=time|reason]")},
        "diff":    {"op": "op_diff", "action": _R, "cli": "clab.diff", "args": ["other"],
                    "desc": "Compare two experiment paths (the active Nebula vs another): clab.diff other=<nebula>"},
        "consensus": {"op": "op_consensus", "action": _W, "cli": "clab.consensus", "args": ["subject"],
                      "desc": "Record a scoped consensus (does NOT erase dissent): clab.consensus subject=<id> agreement=<level> [participants=] [scope=]"},
        "aliases": {"op": "op_aliases", "action": _R, "cli": "clab.aliases", "args": [],
                    "desc": "List the canonical→short alias table (aliases are semantically identical): clab.aliases"},
        # ── seeds13 research primitives (Part C.9 — the 7 minimal + relations) ──
        "master_thesis": {"op": "op_master_thesis", "action": _W, "cli": "clab.master_thesis", "args": ["text"],
                          "desc": "State the overall intended dynamic (\"prove X via Y\"): clab.master_thesis text=\"...\" [agent=]"},
        "cluster.new":   {"op": "op_cluster_new", "action": _W, "cli": "clab.cluster.new", "args": ["name"],
                          "desc": "Open a Thesis-Arguments Cluster (a semantic structure, references only): clab.cluster.new name=\"...\""},
        "cluster.add":   {"op": "op_cluster_add", "action": _W, "cli": "clab.cluster.add", "args": ["cluster", "members"],
                          "desc": "Add references (claims/args/evidence/…) to a cluster: clab.cluster.add cluster=<id> members=<a,b,...>"},
        "key_proof":     {"op": "op_key_proof", "action": _W, "cli": "clab.key_proof", "args": ["cluster", "hypothesis"],
                          "desc": "Judge a cluster decisive for a hypothesis/thesis (agent-attributed judgement, not intrinsic): clab.key_proof cluster=<id> hypothesis=<id> [agent=] [rationale=]"},
        "turning_point": {"op": "op_turning_point", "action": _W, "cli": "clab.turning_point", "args": ["cluster", "hypothesis"],
                          "desc": "Mark a cluster that redirects the trajectory AGAINST a hypothesis (distinct from a mere challenge): clab.turning_point cluster=<id> hypothesis=<id> [agent=] [rationale=]"},
        "conclude":      {"op": "op_conclude", "action": _W, "cli": "clab.conclude", "args": ["hypothesis", "judgement"],
                          "desc": "Reach a first-class conclusion (multiple may coexist; non-forcing): clab.conclude hypothesis=<id> judgement=affirm|negate|mixed|undetermined [agent=] [rationale=]"},
        "family.new":    {"op": "op_family_new", "action": _W, "cli": "clab.family.new", "args": ["name"],
                          "desc": "Open a Theoretical Family (a semantic neighborhood at one trajectory stage): clab.family.new name=\"...\" [stage=initial|intermediate|destination]"},
        "family.add":    {"op": "op_family_add", "action": _W, "cli": "clab.family.add", "args": ["family", "members"],
                          "desc": "Add concepts/clusters to a family: clab.family.add family=<id> members=<a,b,...>"},
        "family.next":   {"op": "op_family_next", "action": _W, "cli": "clab.family.next", "args": ["from", "to"],
                          "desc": "Chain one family to the next along a trajectory: clab.family.next from=<family> to=<family>"},
        "family.bridge": {"op": "op_family_bridge", "action": _W, "cli": "clab.family.bridge", "args": ["from", "to"],
                          "desc": "Bridge one family to the next along a trajectory (Rubik bridge; = family_next): clab.family.bridge from=<family> to=<family>"},
        "theory.new":    {"op": "op_theory_new", "action": _W, "cli": "clab.theory.new", "args": ["name"],
                          "desc": "Declare a Competing Theory (a traceable trajectory through families): clab.theory.new name=\"...\""},
        "theory.path":   {"op": "op_theory_path", "action": _W, "cli": "clab.theory.path", "args": ["theory", "family"],
                          "desc": "Append a family to a theory's trajectory path: clab.theory.path theory=<id> family=<id>"},
        "neighborhood.new": {"op": "op_neighborhood_new", "action": _W, "cli": "clab.neighborhood.new", "args": ["name"],
                          "desc": "Open a Theoretical Neighborhood (a research area grouping families — a Nebula input): clab.neighborhood.new name=\"...\""},
        "neighborhood.add": {"op": "op_neighborhood_add", "action": _W, "cli": "clab.neighborhood.add", "args": ["neighborhood", "family"],
                          "desc": "Group a family into a neighborhood: clab.neighborhood.add neighborhood=<id> family=<id>"},
        "conclusion.compare": {"op": "op_conclusion_compare", "action": _R, "cli": "clab.conclusion.compare", "args": [],
                          "desc": "Compare all conclusions side by side — every polarity kept, none overwrites another: clab.conclusion.compare"},
        # ── Concept Laboratory Projection Model v0.1 (read-only GUI projection) ──
        "project":       {"op": "op_project", "action": _R, "cli": "clab.project", "args": [],
                          "desc": ("Project the research field into a GUI-ready view (read-only, derived, "
                                   "never writes canonical): clab.project [target=<nebula>] "
                                   "[mode=trajectory|family|evidence|time] [at=<chronon>] [include=rejected] "
                                   "[society=] [workflow=]")},
        "rubik":         {"op": "op_rubik", "action": _R, "cli": "clab.rubik", "args": [],
                          "desc": ("Rubik projection — theoretical families as pseudo-3D pages with "
                                   "precomputed transformation deltas (read-only, never writes canonical): "
                                   "clab.rubik [target=<nebula>] [trajectory=<theory>] [society=]")},
    }

    # Short aliases (iteration 0.3): each resolves to exactly ONE canonical operator, with identical
    # semantics and the same audit/replay event (same op → same operand kind). Verbose forms stay
    # canonical/documented; aliases are an expert efficiency layer.
    _ALIASES = {
        "n": "new", "st": "status", "q": "question", "obs": "observe", "ex": "example",
        "clm": "claim", "hyp": "hypothesize", "int": "interpret", "as": "assess", "ch": "challenge",
        "ten": "tension", "br": "bridge", "cmp": "compare", "stb": "stabilize", "acc": "accept",
        "con": "consensus", "rp": "replay", "tr": "trace", "fk": "fork", "df": "diff",
        "src.add": "source.add", "src.ln": "source.link", "src.sh": "source.show",
        "src.ls": "source.list", "src.rm": "source.unlink",
    }
    CONCEPT_METHODS = dict(_CANON)
    for _al, _canon in _ALIASES.items():
        CONCEPT_METHODS[_al] = dict(_CANON[_canon], cli="clab." + _al)
    del _al, _canon

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _author(self) -> str:
        return getattr(self.session, "client_id", "system")

    @staticmethod
    def _slug(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")[:48] or "nebula"

    def _resolve(self, ref: str) -> Optional[str]:
        ref = (ref or "").strip()
        if not ref:
            return None
        try:
            if self.cortex.get_chunk(ref) is not None:
                return ref
            k = self.cortex.resolve_alias(ref)
            if k:
                return k
        except Exception:
            pass
        # by-NAME fallback: operands minted with a name (family / cluster / theory / neighborhood)
        # are keyed by content-hash, so callers naturally reference them by their human name. Match
        # an active-nebula member whose content (or clab_name/title/concept_name meta) equals ref.
        try:
            for mk in self._members():
                mm = self.cortex.get_meta(mk) or {}
                if ref in (mm.get("clab_name"), mm.get("title"), mm.get("concept_name")):
                    return mk
                if (self.cortex.get_chunk(mk) or "").strip() == ref:
                    return mk
        except Exception:
            pass
        return None

    def _alias(self, key: str) -> str:
        try:
            al = self.cortex.get_aliases_by_key(key) or []
        except Exception:
            al = []
        return next((a for a in al if a.startswith("clab:") or ":" in a), al[0] if al else key)

    def _active(self) -> str:
        root = self.session.get_context(CONTEXT_KEY_ACTIVE) if hasattr(self.session, "get_context") else None
        if not root:
            raise RuntimeError("No active Nebula. Create one with clab.new or open one with clab.open.")
        return root

    def _neb_meta(self) -> Dict[str, Any]:
        return self.cortex.get_meta(self._active()) or {}

    def _members_set(self, root: str = None) -> str:
        m = self.cortex.get_meta(root or self._active()) or {}
        return m.get("clab_set") or f"clab:neb:{m.get('clab_slug', 'x')}:members"

    def _members(self, root: str = None) -> List[str]:
        try:
            return list(self.cortex.get_collection_members(self._members_set(root)) or [])
        except Exception:
            return []

    def _mk(self, kind: str, content: str, extra: Dict[str, Any] = None,
            links: List[tuple] = None, alias_hint: str = "") -> Dict[str, Any]:
        """Create an operand atom, tag it, add it to the active Nebula, and link it. Returns
        a compact descriptor {id (alias), key, kind}. Every operand is content atom text — it is
        woven/indexed like any note (this is workspace content, not opaque analytics)."""
        root = self._active()
        author = self._author()
        meta = {"clab_kind": kind, "clab_nebula": root, "created_by": author,
                "created_at": time.time()}
        if extra:
            meta.update(extra)
        key = self.cortex.put_chunk(content=content, meta=meta, author=author,
                                    scopes=[f"owner:user_{author}", f"view:user_{author}"])
        # readable, referenceable alias
        alias = f"clab:{kind}:{self._slug(alias_hint)[:24] + '_' if alias_hint else ''}{key[:8]}"
        try:
            self.cortex.set_alias(key, alias)
        except Exception:
            alias = key
        try:
            self.cortex.add_to_set(self._members_set(), key)
            self.cortex.put_link(key, root, PART_OF, author=author)
        except Exception:
            pass
        for (dst, rel) in (links or []):
            if dst:
                try:
                    self.cortex.put_link(key, dst, rel, author=author)
                except Exception:
                    pass
        return {"id": self._alias(key), "key": key, "kind": kind}

    def _need(self, ref: str, what: str) -> str:
        k = self._resolve(ref)
        if not k:
            raise ValueError(f"clab: {what} '{ref}' does not resolve to an atom.")
        return k

    # ── workspace ────────────────────────────────────────────────────────────────
    def op_new(self, title: str = "") -> Dict[str, Any]:
        """[clab.new] Create a Nebula — a bounded experimental field — around a framing question or
        title, and open it as the active field. Returns its id."""
        title = (title or "").strip()
        if not title:
            raise ValueError("clab.new requires a title/question.")
        author = self._author()
        slug = self._slug(title)
        meta = {"clab_kind": "nebula", "clab_slug": slug, "clab_set": f"clab:neb:{slug}:members",
                "title": title, "created_by": author, "created_at": time.time()}
        key = self.cortex.put_chunk(content=f"[Nebula] {title}", meta=meta, author=author,
                                    scopes=[f"owner:user_{author}", f"view:user_{author}"])
        try:
            self.cortex.set_alias(key, f"clab:nebula:{slug}")
        except Exception:
            pass
        try:
            self.cortex.add_to_set(meta["clab_set"], key)
        except Exception:
            pass
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, key)
        return {"type": "clab:nebula", "id": self._alias(key), "key": key, "title": title,
                "status": "open"}

    def op_open(self, id: str = "") -> Dict[str, Any]:
        """[clab.open] Open an existing Nebula (by alias or key) as the active field."""
        key = self._need(id, "nebula")
        m = self.cortex.get_meta(key) or {}
        if m.get("clab_kind") != "nebula":
            raise ValueError("clab.open: that atom is not a Nebula.")
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, key)
        return {"type": "clab:open", "id": self._alias(key), "title": m.get("title", ""),
                "members": len(self._members(key))}

    def op_status(self) -> Dict[str, Any]:
        """[clab.status] A summary of the active Nebula: operand counts by kind + open tensions."""
        root = self._active()
        m = self.cortex.get_meta(root) or {}
        counts: Dict[str, int] = {}
        tensions = 0
        for k in self._members(root):
            mm = self.cortex.get_meta(k) or {}
            kind = mm.get("clab_kind", "?")
            if kind == "nebula":
                continue
            counts[kind] = counts.get(kind, 0) + 1
            if kind == "tension":
                tensions += 1
        return {"type": "clab:status", "id": self._alias(root), "title": m.get("title", ""),
                "operands": sum(counts.values()), "by_kind": counts, "open_tensions": tensions}

    def _rows(self, root: str = None, kind: str = "") -> List[Dict[str, Any]]:
        out = []
        for k in self._members(root):
            mm = self.cortex.get_meta(k) or {}
            kd = mm.get("clab_kind", "?")
            if kd == "nebula" or (kind and kd != kind):
                continue
            head = (self.cortex.get_chunk(k) or "").replace("\n", " ").strip()
            out.append({"id": self._alias(k), "kind": kd, "at": mm.get("created_at", 0),
                        "by": mm.get("created_by", ""), "text": head[:160], "_meta": mm})
        return out

    def op_members(self, kind: str = "", limit: Any = 100) -> Dict[str, Any]:
        """[clab.members] List the operands in the active Nebula, optionally filtered by kind."""
        try:
            lim = max(1, min(int(limit), 500))
        except (TypeError, ValueError):
            lim = 100
        rows = self._rows(kind=kind.strip())
        rows.sort(key=lambda r: r["at"])
        for r in rows:
            r.pop("_meta", None)
        return {"type": "clab:members", "id": self._alias(self._active()), "kind": kind or None,
                "count": len(rows), "results": rows[:lim]}

    def op_replay(self, limit: Any = 200) -> Dict[str, Any]:
        """[clab.replay] Reconstruct the Nebula's operands in creation order — the thought
        experiment as it unfolded. (v0.1: creation-time ordering; a fuller event log is future work.)"""
        try:
            lim = max(1, min(int(limit), 1000))
        except (TypeError, ValueError):
            lim = 200
        rows = self._rows()
        rows.sort(key=lambda r: r["at"])
        seq = [{"n": i + 1, "id": r["id"], "kind": r["kind"], "by": r["by"],
                "when": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(r["at"])) if r["at"] else "",
                "text": r["text"]} for i, r in enumerate(rows[:lim])]
        for r in rows:
            r.pop("_meta", None)
        return {"type": "clab:replay", "id": self._alias(self._active()), "steps": len(seq),
                "sequence": seq}

    def op_fork(self, name: str = "") -> Dict[str, Any]:
        """[clab.fork] Fork the active Nebula into a new branch: a new Nebula whose membership is
        copied from the parent. The parent is never silently overwritten (invariant 9)."""
        parent = self._active()
        pm = self.cortex.get_meta(parent) or {}
        title = (name or "").strip() or (pm.get("title", "nebula") + " (fork)")
        created = self.op_new(title=title)          # opens the fork as active
        fork_set = self._members_set(created["key"])
        author = self._author()
        copied = 0
        for k in self._members(parent):
            if (self.cortex.get_meta(k) or {}).get("clab_kind") == "nebula":
                continue
            try:
                self.cortex.add_to_set(fork_set, k)     # share the operand atoms (immutable)
                copied += 1
            except Exception:
                pass
        try:
            self.cortex.put_link(created["key"], parent, R["emerges_from"], author=author)
        except Exception:
            pass
        return {"type": "clab:fork", "id": created["id"], "forked_from": self._alias(parent),
                "copied": copied}

    # ── operand creation ─────────────────────────────────────────────────────────
    def op_question(self, text: str = "") -> Dict[str, Any]:
        if not (text or "").strip():
            raise ValueError("clab.question requires text.")
        r = self._mk("question", text.strip(), links=[(self._active(), R["frames"])])
        return {"type": "clab:question", **r}

    def op_observe(self, text: str = "", observer: str = "", instrument: str = "",
                   source: str = "", confidence: str = "") -> Dict[str, Any]:
        if not (text or "").strip():
            raise ValueError("clab.observe requires text.")
        extra = {k: v for k, v in (("observer", observer), ("instrument", instrument),
                                   ("source", source), ("confidence", confidence)) if v}
        r = self._mk("observation", text.strip(), extra=extra)
        return {"type": "clab:observation", **r}

    def op_example(self, target: str = "", kind: str = "ordinary") -> Dict[str, Any]:
        """Select an existing atom as an Example (a candidate classification, not a kernel truth —
        invariant 4)."""
        tk = self._need(target, "example target")
        kind = (kind or "ordinary").strip()
        if kind not in EXAMPLE_KINDS:
            kind = "ordinary"
        talias = self._alias(tk)
        r = self._mk("example", f"[Example · {kind}] {talias}",
                     extra={"example_kind": kind, "target": tk},
                     links=[(tk, R["selects_as_example"])], alias_hint=kind)
        return {"type": "clab:example", "example_kind": kind, "of": talias, **r}

    def op_claim(self, text: str = "") -> Dict[str, Any]:
        if not (text or "").strip():
            raise ValueError("clab.claim requires text.")
        return {"type": "clab:claim", **self._mk("claim", text.strip())}

    def op_hypothesize(self, text: str = "") -> Dict[str, Any]:
        if not (text or "").strip():
            raise ValueError("clab.hypothesize requires text.")
        return {"type": "clab:hypothesis",
                **self._mk("hypothesis", text.strip(), extra={"status": "proposed"})}

    # ── seeds13 research primitives (Part C.9) — extend, never replace, the existing clab.* ──
    def op_master_thesis(self, text: str = "", agent: str = "") -> Dict[str, Any]:
        """The overall intended dynamic of an investigation ("prove X via Y") — broader than one
        hypothesis, an optional global orientation. Never auto-accepted as ontology truth."""
        if not (text or "").strip():
            raise ValueError("clab.master_thesis requires text.")
        extra = {"agent": (agent or self._author())}
        return {"type": "clab:master_thesis", **self._mk("master_thesis", text.strip(), extra=extra)}

    def op_cluster_new(self, name: str = "") -> Dict[str, Any]:
        """Open a Thesis-Arguments Cluster — a structured local reasoning unit that holds REFERENCES
        (claims/args/evidence/examples/interpretations/…), never copies. A semantic structure, not a
        paragraph (the members-are-references rule, SC2/SC6)."""
        if not (name or "").strip():
            raise ValueError("clab.cluster.new requires name.")
        return {"type": "clab:cluster", **self._mk("cluster", name.strip(), alias_hint=name)}

    def op_cluster_add(self, cluster: str = "", members: str = "", member: str = "") -> Dict[str, Any]:
        """Add references to a cluster (clab:contains links — references, never copies). Accepts
        `members=<a,b,…>` or a single `member=<x>`."""
        ck = self._need(cluster, "cluster")
        joined = ",".join(x for x in (members, member) if x)
        refs = [self._resolve(r) for r in joined.split(",") if r.strip()]
        added = 0
        for rk in refs:
            if rk:
                try:
                    self.cortex.put_link(ck, rk, "clab:contains", author=self._author())
                    added += 1
                except Exception:
                    pass
        return {"type": "clab:cluster_add", "id": self._alias(ck), "added": added}

    def op_key_proof(self, cluster: str = "", hypothesis: str = "", target: str = "", agent: str = "",
                     rationale: str = "") -> Dict[str, Any]:
        """Judge a cluster DECISIVE for a hypothesis/thesis (or the case it is about) — a research
        judgement (keeps agent, rationale, provenance), not an intrinsic property; agents may
        disagree. Accepts `hypothesis=` or `target=` for the decisively-supported atom."""
        ck = self._need(cluster, "cluster")
        hk = self._need(hypothesis or target, "hypothesis/target")
        extra = {"agent": (agent or self._author()), "rationale": rationale}
        # kind-tag the content so a judgement never collides (content-address) with another operand
        # that happens to share the same rationale text (a conclusion, a turning point, …).
        r = self._mk("key_proof", f"[key_proof cluster={self._alias(ck)}] {rationale}".strip(), extra=extra,
                     links=[(ck, "clab:key_proof"), (hk, "clab:decisively_supports")])
        return {"type": "clab:key_proof", **r}

    def op_turning_point(self, cluster: str = "", hypothesis: str = "", target: str = "", agent: str = "",
                         rationale: str = "") -> Dict[str, Any]:
        """Mark a cluster that REDIRECTS the trajectory against a hypothesis/thesis (or the case it
        is about) — distinct from a mere challenge (it changes the trajectory, making conceptual
        change observable as process). Accepts `hypothesis=` or `target=`."""
        ck = self._need(cluster, "cluster")
        hk = self._need(hypothesis or target, "hypothesis/target")
        extra = {"agent": (agent or self._author()), "rationale": rationale}
        r = self._mk("turning_point", f"[turning_point cluster={self._alias(ck)}] {rationale}".strip(), extra=extra,
                     links=[(ck, "clab:turning_point"), (hk, "clab:challenges")])
        return {"type": "clab:turning_point", **r}

    def op_conclude(self, hypothesis: str = "", target: str = "", judgement: str = "", agent: str = "",
                    rationale: str = "", text: str = "") -> Dict[str, Any]:
        """Reach a FIRST-CLASS conclusion about a hypothesis/thesis (or the case it is about) —
        polarity affirm/negate/mixed/undetermined. Multiple conclusions may coexist (per agent/
        branch); a conclusion CLOSES a trajectory, not the conceptual world (non-forcing). Never
        auto-promotes to ontology truth. Accepts `hypothesis=` or `target=`, and `rationale=`/`text=`."""
        hk = self._need(hypothesis or target, "hypothesis/target")
        j = (judgement or "undetermined").strip().lower()
        if j not in ("affirm", "negate", "mixed", "undetermined"):
            raise ValueError("judgement must be affirm|negate|mixed|undetermined.")
        rationale = rationale or text
        extra = {"agent": (agent or self._author()), "judgement": j, "rationale": rationale,
                 "status": "proposed"}
        r = self._mk("conclusion", f"[conclusion:{j} about={self._alias(hk)}] {rationale}".strip(), extra=extra,
                     links=[(hk, "clab:concludes_about")])
        return {"type": "clab:conclusion", "judgement": j, **r}

    def op_family_new(self, name: str = "", stage: str = "intermediate") -> Dict[str, Any]:
        """Open a Theoretical Family — a semantic neighborhood of mutually-meaningful concepts/
        clusters at one stage of a trajectory (initial | intermediate | destination)."""
        if not (name or "").strip():
            raise ValueError("clab.family.new requires name.")
        st = (stage or "intermediate").strip().lower()
        if st not in ("initial", "intermediate", "destination"):
            raise ValueError("stage must be initial|intermediate|destination.")
        return {"type": "clab:family",
                **self._mk("family", name.strip(), extra={"stage": st}, alias_hint=name)}

    def op_family_add(self, family: str = "", members: str = "", member: str = "") -> Dict[str, Any]:
        """Add concepts/clusters to a theoretical family (clab:belongs_to_family — references).
        Accepts `members=<a,b,…>` or a single `member=<x>`. Unknown atoms are skipped (not fatal)."""
        fk = self._need(family, "family")
        joined = ",".join(x for x in (members, member) if x)
        refs = [self._resolve(r) for r in joined.split(",") if r.strip()]
        added, skipped = 0, 0
        for rk in refs:
            if rk:
                try:
                    self.cortex.put_link(rk, fk, "clab:belongs_to_family", author=self._author())
                    added += 1
                except Exception:
                    skipped += 1
            else:
                skipped += 1
        return {"type": "clab:family_add", "id": self._alias(fk), "added": added, "skipped": skipped}

    def op_family_next(self, from_: str = "", to: str = "", **kw) -> Dict[str, Any]:
        """Chain one theoretical family to the next along a trajectory (clab:family_next)."""
        src = self._need(kw.get("from", from_), "family (from)")
        dst = self._need(to, "family (to)")
        self.cortex.put_link(src, dst, "clab:family_next", author=self._author())
        return {"type": "clab:family_next", "from": self._alias(src), "to": self._alias(dst)}

    def op_family_bridge(self, from_: str = "", to: str = "", **kw) -> Dict[str, Any]:
        """[Rubik bridge] Bridge one theoretical family to the next along a trajectory. A branch-only
        transformation that never mutates canonical ontology; here it lays the clab:family_next edge
        the trajectory/projection reads."""
        src = self._need(kw.get("from", from_), "family (from)")
        dst = self._need(to, "family (to)")
        self.cortex.put_link(src, dst, "clab:family_next", author=self._author())
        return {"type": "clab:family_bridge", "from": self._alias(src), "to": self._alias(dst)}

    def op_theory_new(self, name: str = "") -> Dict[str, Any]:
        """Declare a Competing Theory — a traceable trajectory through theoretical families (not a
        duplicated ontology). Build its path with clab.theory.path."""
        if not (name or "").strip():
            raise ValueError("clab.theory.new requires name.")
        return {"type": "clab:theory", **self._mk("theory", name.strip(), alias_hint=name)}

    def op_theory_path(self, theory: str = "", family: str = "") -> Dict[str, Any]:
        """Append a family to a theory's trajectory path (clab:contains, ordered by call)."""
        tk = self._need(theory, "theory")
        fk = self._need(family, "family")
        self.cortex.put_link(tk, fk, "clab:contains", author=self._author())
        n = len(self.cortex.get_adjacent_links(tk, "clab:contains") or [])
        return {"type": "clab:theory_path", "theory": self._alias(tk), "family": self._alias(fk),
                "path_len": n}

    def op_neighborhood_new(self, name: str = "") -> Dict[str, Any]:
        """Open a Theoretical Neighborhood — a research-area grouping of families (organizational/
        exploratory, NOT a truth classification; a natural input to Nebula)."""
        if not (name or "").strip():
            raise ValueError("clab.neighborhood.new requires name.")
        return {"type": "clab:neighborhood", **self._mk("neighborhood", name.strip(), alias_hint=name)}

    def op_neighborhood_add(self, neighborhood: str = "", family: str = "") -> Dict[str, Any]:
        """Group a family into a neighborhood (clab:contains)."""
        nk = self._need(neighborhood, "neighborhood")
        fk = self._need(family, "family")
        self.cortex.put_link(nk, fk, "clab:contains", author=self._author())
        n = len(self.cortex.get_adjacent_links(nk, "clab:contains") or [])
        return {"type": "clab:neighborhood_add", "neighborhood": self._alias(nk),
                "family": self._alias(fk), "count": n}

    def op_conclusion_compare(self) -> Dict[str, Any]:
        """Compare every conclusion in the active field side by side — all polarities kept, none
        overwrites another (the non-forcing invariant made observable). Read-only."""
        rows = []
        by_pol: Dict[str, int] = {}
        for r in self._rows(kind="conclusion"):
            mm = r.get("_meta", {})
            pol = mm.get("judgement", "undetermined")
            by_pol[pol] = by_pol.get(pol, 0) + 1
            rows.append({"id": r["id"], "polarity": pol, "agent": mm.get("agent", r.get("by", "")),
                         "lifecycle": mm.get("status", "proposed"), "rationale": mm.get("rationale", ""),
                         "text": r["text"]})
        return {"type": "clab:conclusion_compare", "count": len(rows), "by_polarity": by_pol,
                "coexist": len(by_pol) > 1, "conclusions": rows}

    # ── Concept Laboratory Projection Model v0.1 (read-only) ──────────────────────
    def op_project(self, target: str = "", mode: str = "trajectory", at: str = "",
                   include: str = "", society: str = "", workflow: str = "") -> Dict[str, Any]:
        """[clab.project] Project the research field into a GUI-ready view — the Concept Laboratory
        Projection Model v0.1. READ-ONLY and derived: it casts the canonical clab operands/relations
        into visual primitives (pv:concept/cluster/family/hypothesis/key_proof/turning_point/
        conclusion/tension/source) + typed edges + trajectories + timepoints + layout hints, and
        NEVER writes canonical state (invariant V1). Every projected object keeps its source_atom
        (V7 — GUI → CLI → clab.trace is reversible). `mode=trajectory|family|evidence|time`;
        `target=` a nebula (default: the active one); `include=rejected` surfaces hidden paths (V3).
        Archives reads this JSON directly."""
        from lib.akasha.clab_projection import ClabProjectionBuilder
        target = (target or "").strip()
        if target in ("", "active"):
            root = self._active()
        else:
            resolved = self._resolve(target)
            # a Nebula projects itself; any operand inside the field (a neighborhood/theory/family
            # named as target) projects the field that contains it — the active nebula.
            root = resolved if (resolved and (self.cortex.get_meta(resolved) or {}).get("clab_kind") == "nebula") else self._active()
        if not root:
            raise RuntimeError("clab.project: no active nebula (open one with clab.open, or pass target=).")
        m = self.cortex.get_meta(root) or {}
        if m.get("clab_kind") != "nebula":
            raise ValueError("clab.project target must be a Nebula (research field).")
        try:
            now_ts = time.time()
        except Exception:
            now_ts = 0.0
        builder = ClabProjectionBuilder(self.cortex, self._alias, now_ts)
        members = self._members(root)
        include_rejected = (include or "").strip().lower() in ("rejected", "all", "yes", "true", "1")
        return builder.build(root, members, title=m.get("title", ""), mode=mode, at=at,
                             include_rejected=include_rejected, source_society=society,
                             source_workflow=workflow, source_chronon_root="",
                             source_frontier=self._society_frontier(society))

    def op_rubik(self, target: str = "", trajectory: str = "", society: str = "",
                 workflow: str = "concept-labo") -> Dict[str, Any]:
        """[clab.rubik] Rubik projection v0.1 — the read-only, PRECOMPUTED spatial projection that
        shows how theoretical families TRANSFORM as a theory's path is built (vs the Trajectory view,
        which shows where research went). Akasha computes every page coordinate, page depth, per-page
        concept coordinate, and the transformation delta (added/removed/retained); the GUI only
        renders + animates. Three axes stay separate: (x,y)=semantic, z=transformation depth (NOT
        time), t=Akasha-Time. NEVER writes canonical (V1); every object keeps source_atom (V7).
        `trajectory=<theory>` restricts to one competing theory's families (e.g. the LIGO branch)."""
        from lib.akasha.clab_rubik_projection import RubikProjectionBuilder
        target = (target or "").strip()
        if target in ("", "active"):
            root = self._active()
        else:
            resolved = self._resolve(target)
            root = resolved if (resolved and (self.cortex.get_meta(resolved) or {}).get("clab_kind") == "nebula") else self._active()
        if not root:
            raise RuntimeError("clab.rubik: no active nebula (open one with clab.open, or pass target=).")
        m = self.cortex.get_meta(root) or {}
        if m.get("clab_kind") != "nebula":
            raise ValueError("clab.rubik target must be a Nebula (research field).")
        # optional trajectory filter → the families of that theory (clab.theory contains)
        restrict = None
        traj = (trajectory or "").strip()
        if traj:
            tk = self._resolve(traj)
            if not tk or (self.cortex.get_meta(tk) or {}).get("clab_kind") != "theory":
                raise ValueError(f"clab.rubik: trajectory '{traj}' is not a theory (clab.theory.new).")
            restrict = []
            for lk in self.cortex.get_adjacent_links(tk, "clab:contains"):
                dst = lk[0] if isinstance(lk, (list, tuple)) else lk.get("dst")
                if dst and (self.cortex.get_meta(dst) or {}).get("clab_kind") == "family":
                    restrict.append(dst)
        try:
            now_ts = time.time()
        except Exception:
            now_ts = 0.0
        builder = RubikProjectionBuilder(self.cortex, self._alias, now_ts)
        return builder.build(root, self._members(root), restrict, title=m.get("title", ""),
                             society=society, workflow=workflow)

    def _society_frontier(self, society: str) -> List[str]:
        """The society's current chronon frontier(s) (society:now) at generation time — baked into
        the projection meta so a consumer detects 'canonical changed' by comparing against the live
        frontier (society.now). Empty when no society is bound or it is not reachable."""
        society = (society or "").strip()
        if "/" not in society:
            return []
        gid, _, space = society.partition("/")
        gid, space = gid.strip(), (space.strip() or "main")
        ge = getattr(self.session, "group_engines", {}).get(gid)
        if ge is None:
            return []
        try:
            skey = ge.resolve_alias(f"society:{gid}:{space}")
            if not skey:
                return []
            out = []
            for l in ge.core.get_adjacent_links(skey, "society:now"):
                dst = l.get("dst")
                al = next((a for a in ge.get_aliases_by_key(dst) if a.startswith("chronon:")), dst)
                out.append(al)
            return out
        except Exception:
            return []

    def op_interpret(self, target: str = "", text: str = "", agent: str = "",
                     status: str = "") -> Dict[str, Any]:
        """Add an agent-attributed reading of a target. Invariant 2: an Interpretation MUST identify
        its agent (defaults to the caller). Competing interpretations coexist. An optional
        `status=` (e.g. rejected / challenged / retained) records a deliberative outcome — a
        rejected interpretation stays queryable and is surfaced by `clab.trace include=rejected`."""
        tk = self._need(target, "interpretation target")
        if not (text or "").strip():
            raise ValueError("clab.interpret requires text.")
        ag = (agent or "").strip() or self._author()
        extra = {"agent": ag, "target": tk}
        if (status or "").strip():
            extra["status"] = status.strip()
        r = self._mk("interpretation", text.strip(), extra=extra, links=[(tk, R["interprets_as"])])
        return {"type": "clab:interpretation", "agent": ag, "of": self._alias(tk),
                "status": extra.get("status", ""), **r}

    def op_bridge(self, **kw) -> Dict[str, Any]:
        """Stage a **tentative** Bridge between two atoms. Invariant / principle 7: it does NOT
        create a real edge until an agent `clab.accept`s it. Until then it is queryable but inert."""
        frm = kw.get("from") or kw.get("frm") or ""
        to = kw.get("to") or ""
        rel = (kw.get("rel") or R["bridges"]).strip()
        rationale = (kw.get("rationale") or "").strip()
        fk, tk = self._need(frm, "bridge from"), self._need(to, "bridge to")
        content = f"[Bridge · tentative] {self._alias(fk)} —{rel}→ {self._alias(tk)}" + \
                  (f"  ::{rationale}" if rationale else "")
        r = self._mk("bridge", content,
                     extra={"status": "tentative", "from": fk, "to": tk, "rel": rel,
                            "rationale": rationale})
        return {"type": "clab:bridge", "status": "tentative", **r,
                "note": "tentative — not committed until clab.accept"}

    def op_tension(self, left: str = "", right: str = "", kind: str = "contradiction",
                   rationale: str = "") -> Dict[str, Any]:
        """Record an unresolved Tension between two operands. Tensions are preserved, not resolved
        (principle 5)."""
        lk, rk = self._need(left, "tension left"), self._need(right, "tension right")
        content = f"[Tension · {kind}] {self._alias(lk)} ⟂ {self._alias(rk)}" + \
                  (f"  ::{rationale}" if rationale else "")
        r = self._mk("tension", content, extra={"tension_kind": kind, "left": lk, "right": rk,
                                                 "rationale": rationale},
                     links=[(lk, R["between"]), (rk, R["between"])], alias_hint=kind)
        return {"type": "clab:tension", "tension_kind": kind, **r}

    # ── epistemic operations ─────────────────────────────────────────────────────
    def _evidence(self, kind_rel: str, evidence: str, target: str, rationale: str) -> Dict[str, Any]:
        ek, tk = self._need(evidence, "evidence"), self._need(target, "target")
        author = self._author()
        try:
            self.cortex.put_link(ek, tk, kind_rel, author=author)
        except Exception:
            pass
        # record the evidential judgement as an attributable operand (rationale + agent)
        verb = "supports" if kind_rel == R["supports"] else "challenges"
        r = self._mk("assessment", f"[Evidence · {verb}] {self._alias(ek)} → {self._alias(tk)}" +
                     (f"  ::{rationale}" if rationale else ""),
                     extra={"assessment_kind": "evidence", "polarity": verb, "evidence": ek,
                            "target": tk, "agent": author, "rationale": rationale})
        return {"type": f"clab:{verb}", "of": self._alias(tk), "evidence": self._alias(ek), **r}

    def op_support(self, evidence: str = "", target: str = "", rationale: str = "") -> Dict[str, Any]:
        return self._evidence(R["supports"], evidence, target, rationale.strip())

    def op_challenge(self, evidence: str = "", target: str = "", rationale: str = "") -> Dict[str, Any]:
        return self._evidence(R["challenges"], evidence, target, rationale.strip())

    def op_assess(self, target: str = "", criterion: str = "", judgement: str = "",
                  rationale: str = "", agent: str = "") -> Dict[str, Any]:
        """Evaluate a target under an explicit criterion. **Non-overwriting**: every assessment is a
        distinct, agent-attributed atom, so opposing assessments coexist (invariants 5, principle 6,
        10). No hidden scalar — the judgement + rationale are explicit."""
        tk = self._need(target, "assessment target")
        criterion = (criterion or "").strip() or "pertinence"
        judgement = (judgement or "").strip() or "mixed"
        ag = (agent or "").strip() or self._author()
        content = f"[Assessment] {self._alias(tk)} · {criterion} = {judgement}" + \
                  (f"  ::{rationale}" if rationale else "")
        r = self._mk("assessment", content,
                     extra={"assessment_kind": "criterion", "target": tk, "criterion": criterion,
                            "judgement": judgement, "agent": ag, "rationale": rationale.strip()},
                     links=[(tk, R["evaluates"])], alias_hint=criterion)
        return {"type": "clab:assessment", "target": self._alias(tk), "criterion": criterion,
                "judgement": judgement, "agent": ag, **r}

    def op_compare(self, targets: str = "", by: str = "") -> Dict[str, Any]:
        """Compare targets under criteria. Gathers **every** agent's assessment for each
        (target, criterion) so competing judgements are shown side by side — dissent preserved,
        nothing collapsed to a single truth."""
        tks = [self._need(t, "compare target") for t in re.split(r"[,\s]+", targets.strip()) if t]
        if not tks:
            raise ValueError("clab.compare requires targets=<a,b,...>")
        crit_filter = [c for c in re.split(r"[,\s]+", (by or "").strip()) if c]
        # index assessments by target
        table: Dict[str, Dict[str, List[Dict[str, Any]]]] = {self._alias(t): {} for t in tks}
        for t in tks:
            ta = self._alias(t)
            try:
                incoming = self.cortex.get_incoming_links(t, R["evaluates"]) or []
            except Exception:
                incoming = []
            for pair in incoming:
                src = pair[0] if isinstance(pair, (list, tuple)) else pair
                mm = self.cortex.get_meta(src) or {}
                if mm.get("clab_kind") != "assessment":
                    continue
                crit = mm.get("criterion", "?")
                if crit_filter and crit not in crit_filter:
                    continue
                table[ta].setdefault(crit, []).append(
                    {"judgement": mm.get("judgement", ""), "agent": mm.get("agent") or mm.get("created_by", ""),
                     "rationale": mm.get("rationale", "")})
        return {"type": "clab:compare", "targets": [self._alias(t) for t in tks],
                "criteria": crit_filter or None, "matrix": table}

    def op_stabilize(self, target: str = "", **kw) -> Dict[str, Any]:
        """Treat a pattern as a **provisional** Concept. Invariant 8: `stabilize` NEVER deletes the
        precursor operands — the Concept `emerges_from` the target and coexists with it."""
        tk = self._need(target, "stabilize target")
        as_name = (kw.get("as") or kw.get("as_") or kw.get("name") or "").strip()
        if not as_name:
            raise ValueError("clab.stabilize requires as=<concept-name>.")
        rationale = (kw.get("rationale") or "").strip()
        r = self._mk("concept", f"[Concept · tentative] {as_name}" +
                     (f"  ::{rationale}" if rationale else ""),
                     extra={"maturity": "tentative", "from": tk, "concept_name": as_name,
                            "rationale": rationale},
                     links=[(tk, R["emerges_from"])], alias_hint=as_name)
        # the precursor stabilizes_as the concept (both remain)
        try:
            self.cortex.put_link(tk, r["key"], R["stabilizes_as"], author=self._author())
        except Exception:
            pass
        return {"type": "clab:concept", "name": as_name, "from": self._alias(tk),
                "maturity": "tentative", **r}

    def op_reframe(self, target: str = "", text: str = "") -> Dict[str, Any]:
        """Reframe a target (a new reading that keeps the original — nothing is edited in place)."""
        tk = self._need(target, "reframe target")
        if not (text or "").strip():
            raise ValueError("clab.reframe requires text.")
        r = self._mk("interpretation", text.strip(),
                     extra={"agent": self._author(), "target": tk, "reframe": True},
                     links=[(tk, R["reframes"])])
        return {"type": "clab:reframe", "of": self._alias(tk), **r}

    # ── proposal boundary (human / LLM) ──────────────────────────────────────────
    def op_propose(self, text: str = "", **kw) -> Dict[str, Any]:
        """Stage a proposal. Principle 7 / invariant 10: a proposal MUST NOT mutate stable ontology
        state before acceptance. If it carries from/to/rel, the edge is created only on
        `clab.accept`. LLM-originated proposals stay tentative until an authorized agent accepts."""
        if not (text or "").strip():
            raise ValueError("clab.propose requires text.")
        frm, to = kw.get("from") or "", kw.get("to") or ""
        fk = self._resolve(frm) if frm else ""
        tk = self._resolve(to) if to else ""
        rel = (kw.get("rel") or "").strip()
        extra = {"status": "proposed", "proposed_by": self._author()}
        if fk and tk:
            extra.update({"from": fk, "to": tk, "rel": rel or R["bridges"]})
        r = self._mk("proposal", "[Proposal · proposed] " + text.strip(), extra=extra)
        return {"type": "clab:proposal", "status": "proposed", **r,
                "note": "staged — inert until clab.accept"}

    def _set_status(self, key: str, status: str, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        meta = self.cortex.get_meta(key) or {}
        meta["status"] = status
        if extra:
            meta.update(extra)
        try:
            self.cortex.core.update_meta(key, meta)
        except Exception:
            pass
        return meta

    def op_accept(self, proposal: str = "") -> Dict[str, Any]:
        """Accept a staged proposal or tentative Bridge — **materializes** its edge (creates the
        real from—rel→to link) and marks it accepted. This is the only path from tentative to
        committed."""
        pk = self._need(proposal, "proposal")
        m = self.cortex.get_meta(pk) or {}
        if m.get("clab_kind") not in ("proposal", "bridge"):
            raise ValueError("clab.accept: target is not a proposal or bridge.")
        if m.get("status") == "accepted":
            return {"type": "clab:accept", "id": self._alias(pk), "status": "accepted",
                    "note": "already accepted"}
        materialized = None
        fk, tk, rel = m.get("from"), m.get("to"), m.get("rel")
        if fk and tk and rel:
            try:
                self.cortex.put_link(fk, tk, rel, author=self._author())
                materialized = f"{self._alias(fk)} —{rel}→ {self._alias(tk)}"
            except Exception:
                pass
        self._set_status(pk, "accepted", {"accepted_by": self._author()})
        return {"type": "clab:accept", "id": self._alias(pk), "status": "accepted",
                "materialized": materialized}

    def op_reject(self, proposal: str = "", rationale: str = "") -> Dict[str, Any]:
        """Reject a staged proposal/bridge. Invariant 7: rejected items remain **queryable** for
        replay/audit — they are marked, not deleted, and no edge is created."""
        pk = self._need(proposal, "proposal")
        m = self.cortex.get_meta(pk) or {}
        if m.get("clab_kind") not in ("proposal", "bridge"):
            raise ValueError("clab.reject: target is not a proposal or bridge.")
        self._set_status(pk, "rejected", {"rejected_by": self._author(),
                                          "reject_rationale": (rationale or "").strip()})
        return {"type": "clab:reject", "id": self._alias(pk), "status": "rejected"}

    # ── research provenance — Sources & citations (iteration 0.3) ─────────────────
    def _put_source_atom(self, content: str, meta: dict) -> str:
        """Sources/citations are provenance infrastructure — written without weaving them into the
        word graph (they are bibliographic records, not vocabulary)."""
        author = self._author()
        meta = dict(meta, created_by=author, created_at=time.time())
        key = self.cortex.put_chunk(content=content, meta=meta, author=author,
                                    scopes=[f"owner:user_{author}", f"view:user_{author}"])
        return key

    def op_source_add(self, title: str = "", author: str = "", authors: str = "", year: str = "",
                      type: str = "", journal: str = "", volume: str = "", issue: str = "",
                      pages: str = "", doi: str = "", url: str = "", language: str = "",
                      note: str = "", **kw) -> Dict[str, Any]:
        """[clab.source.add] Register a research Source as an addressable operand. Only `title` is
        required. A DOI is stored as the identifier; `url` stores a resolvable link."""
        title = (title or "").strip()
        if not title:
            raise ValueError("clab.source.add requires a title.")
        auth = (authors or author or "").strip()
        stype = (type or kw.get("source_type") or "other").strip() or "other"
        meta = {"clab_kind": "source", "title": title, "authors": auth, "year": str(year or ""),
                "source_type": stype, "journal": journal, "volume": volume, "issue": issue,
                "pages": pages, "doi": doi, "url": url, "language": language, "note": note}
        cite = f"{auth + ' ' if auth else ''}{'(' + str(year) + '). ' if year else ''}{title}." + \
               (f" {journal}." if journal else "") + (f" DOI:{doi}" if doi else "")
        key = self._put_source_atom("[Source] " + cite, meta)
        alias = f"clab:source:{self._slug(title)[:24]}_{key[:6]}"
        try:
            self.cortex.set_alias(key, alias)
        except Exception:
            alias = key
        try:
            self.cortex.add_to_set("clab:sources", key)
        except Exception:
            pass
        return {"type": "clab:source", "id": self._alias(key), "key": key, "title": title,
                "authors": auth, "year": str(year or ""), "doi": doi, "url": url}

    def _cites_set(self, source_key: str) -> str:
        return f"clab:src:{source_key[:12]}:cites"

    def op_source_link(self, target: str = "", source: str = "", role: str = "derived_from",
                       **kw) -> Dict[str, Any]:
        """[clab.source.link] Link a Source to a research operand with a locator. The locator
        (pages/section/…) and the provenance `role` belong to THIS relationship, not to the Source —
        one Source may cite many operands with different roles and pages. Creates a citation
        operand: `operand —sourced_by→ citation —cites→ Source`."""
        tk = self._need(target, "source-link target")
        sk = self._need(source, "source")
        if (self.cortex.get_meta(sk) or {}).get("clab_kind") != "source":
            raise ValueError("clab.source.link: `source` is not a Source (use clab.source.add first).")
        role = (role or "derived_from").strip()
        locator = {f: kw[f] for f in LOCATOR_FIELDS if kw.get(f)}
        loc_s = ", ".join(f"{k}={v}" for k, v in locator.items())
        content = f"[Citation · {role}] {self._alias(sk)} → {self._alias(tk)}" + \
                  (f"  ({loc_s})" if loc_s else "")
        meta = {"clab_kind": "citation", "source": sk, "target": tk, "role": role, "locator": locator}
        ck = self._put_source_atom(content, meta)
        try:
            self.cortex.set_alias(ck, f"clab:cite:{ck[:8]}")
        except Exception:
            pass
        author = self._author()
        for (s, dnode, rel) in ((tk, ck, SOURCED_BY), (ck, sk, CITES)):
            try:
                self.cortex.put_link(s, dnode, rel, author=author)
            except Exception:
                pass
        try:
            self.cortex.add_to_set(self._cites_set(sk), ck)
        except Exception:
            pass
        return {"type": "clab:citation", "id": self._alias(ck), "target": self._alias(tk),
                "source": self._alias(sk), "role": role, "locator": locator}

    def _source_citations(self, source_key: str) -> List[Dict[str, Any]]:
        out = []
        for ck in (self._members_named(self._cites_set(source_key))):
            mm = self.cortex.get_meta(ck) or {}
            if mm.get("clab_kind") != "citation":
                continue
            tgt = mm.get("target")
            out.append({"citation": self._alias(ck), "target": self._alias(tgt) if tgt else "",
                        "role": mm.get("role", ""), "locator": mm.get("locator", {})})
        return out

    def _members_named(self, set_name: str) -> List[str]:
        try:
            return list(self.cortex.get_collection_members(set_name) or [])
        except Exception:
            return []

    def op_source_show(self, id: str = "") -> Dict[str, Any]:
        """[clab.source.show] Full bibliography of a Source plus every operand it is linked to and
        the per-link locator."""
        sk = self._need(id, "source")
        m = self.cortex.get_meta(sk) or {}
        if m.get("clab_kind") != "source":
            raise ValueError("clab.source.show: not a Source.")
        biblio = {k: m.get(k, "") for k in ("title", "authors", "year", "source_type", "journal",
                                            "volume", "issue", "pages", "doi", "url", "note")}
        return {"type": "clab:source", "id": self._alias(sk), **biblio,
                "citations": self._source_citations(sk)}

    def op_source_list(self) -> Dict[str, Any]:
        """[clab.source.list] List every registered Source (title / authors / year / doi)."""
        rows = []
        for sk in self._members_named("clab:sources"):
            m = self.cortex.get_meta(sk) or {}
            if m.get("clab_kind") != "source":
                continue
            rows.append({"id": self._alias(sk), "title": m.get("title", ""),
                         "authors": m.get("authors", ""), "year": m.get("year", ""),
                         "doi": m.get("doi", "")})
        rows.sort(key=lambda r: (r["authors"], r["year"]))
        return {"type": "clab:source_list", "count": len(rows), "sources": rows}

    def op_source_unlink(self, target: str = "", source: str = "", id: str = "") -> Dict[str, Any]:
        """[clab.source.unlink] Remove a provenance link (citation). The Source operand is NEVER
        deleted. Give a citation `id=`, or a `target=`+`source=` pair."""
        removed = []
        cks = []
        if id:
            cks = [self._need(id, "citation")]
        else:
            tk = self._need(target, "target")
            sk = self._need(source, "source")
            for ck in self._members_named(self._cites_set(sk)):
                mm = self.cortex.get_meta(ck) or {}
                if mm.get("target") == tk and mm.get("source") == sk:
                    cks.append(ck)
        for ck in cks:
            mm = self.cortex.get_meta(ck) or {}
            sk = mm.get("source")
            try:
                if mm.get("target"):
                    self.cortex.remove_link(mm["target"], ck, SOURCED_BY)
                if sk:
                    self.cortex.remove_link(ck, sk, CITES)
                    self.cortex.remove_from_set(self._cites_set(sk), ck)
                self.cortex.drop_chunk(ck)
                removed.append(self._alias(ck))
            except Exception:
                pass
        return {"type": "clab:source_unlink", "removed": removed, "source_kept": True}

    # ── clab.trace / clab.tr — meaning-provenance genealogy ───────────────────────
    def _node(self, key: str, rel: str) -> Dict[str, Any]:
        mm = self.cortex.get_meta(key) or {}
        text = (self.cortex.get_chunk(key) or "").replace("\n", " ").strip()
        return {"kind": mm.get("clab_kind", "atom"), "id": self._alias(key),
                "text": text[:200], "agent": mm.get("agent") or mm.get("created_by", ""),
                "at": mm.get("created_at", 0), "status": mm.get("status", ""),
                "rationale": mm.get("rationale", ""), "relation_to_parent": rel, "_meta": mm}

    def _incoming(self, key: str, rel: str) -> List[str]:
        try:
            return [p[0] if isinstance(p, (list, tuple)) else p
                    for p in (self.cortex.get_incoming_links(key, rel) or [])]
        except Exception:
            return []

    def _outgoing(self, key: str, rel: str) -> List[str]:
        try:
            return [row[0] if isinstance(row, (list, tuple)) else row
                    for row in (self.cortex.get_adjacent_links(key, rel) or [])]
        except Exception:
            return []

    def op_trace(self, target: str = "", depth: Any = "all", include: str = "",
                 order: str = "time", mode: str = "research") -> Dict[str, Any]:
        """[clab.trace / clab.tr] Reconstruct the **meaning-provenance genealogy** of an operand:
        the sources, observations/examples, evidence roles, assessments (with agent + rationale,
        dissent preserved), interpretations, tensions, and any tentative stabilization that led to
        the current conceptual state. Distinct from `clab.replay` (which is experiment history).
        `include=rejected|all` surfaces rejected/challenged paths (research evidence); `order=time`
        is chronological, `order=reason` groups by deliberative role. Preserves agent attribution."""
        tk = self._need(target, "trace target")
        show_rej = (include or "").strip().lower() in ("rejected", "all")
        tmeta = self.cortex.get_meta(tk) or {}

        def keep(n):
            return show_rej or n.get("status", "") not in ("rejected",)

        # ── gather layers (backward provenance) ──
        sources = []
        for ck in self._outgoing(tk, SOURCED_BY):
            cm = self.cortex.get_meta(ck) or {}
            for sk in self._outgoing(ck, CITES):
                sm = self.cortex.get_meta(sk) or {}
                sources.append({"id": self._alias(sk), "title": sm.get("title", ""),
                                "authors": sm.get("authors", ""), "year": sm.get("year", ""),
                                "doi": sm.get("doi", ""), "url": sm.get("url", ""),
                                "role": cm.get("role", ""), "locator": cm.get("locator", {})})
        assessments = [self._node(k, "evaluates") for k in self._incoming(tk, R["evaluates"])]
        interpretations = ([self._node(k, "interprets_as") for k in self._incoming(tk, R["interprets_as"])] +
                           [self._node(k, "reframes") for k in self._incoming(tk, R["reframes"])])
        evidence = ([self._node(k, "supports") for k in self._incoming(tk, R["supports"])] +
                    [self._node(k, "challenges") for k in self._incoming(tk, R["challenges"])])
        examples = [self._node(k, "selects_as_example") for k in self._incoming(tk, R["selects_as_example"])]
        tensions = [self._node(k, "between") for k in self._incoming(tk, R["between"])]
        concepts = ([self._node(k, "emerges_from") for k in self._incoming(tk, R["emerges_from"])] +
                    [self._node(k, "stabilizes_as") for k in self._outgoing(tk, R["stabilizes_as"])])
        for grp in (assessments, interpretations, evidence, examples, tensions, concepts):
            grp[:] = [n for n in grp if keep(n)]

        # assessments grouped by criterion (dissent preserved)
        by_crit: Dict[str, List[Dict[str, Any]]] = {}
        for a in assessments:
            by_crit.setdefault(a["_meta"].get("criterion", "—"), []).append(a)

        # ── render research mode ──
        lines = ["TRACE", f"Target: {self._alias(tk)}", f"State: {tmeta.get('maturity') or tmeta.get('status') or '—'}", ""]
        if concepts:
            lines.append("[Concept candidate]")
            for c in concepts:
                lines.append(f"  {c['_meta'].get('concept_name') or c['text']}  ({c['relation_to_parent']})")
            lines.append("")
        if interpretations:
            lines.append("[Interpretations]")
            for n in interpretations:
                tag = f"  · [{n['status']}]" if n["status"] else ""
                lines.append(f"  agent: {n['agent'] or '— (corpus)'}{tag}")
                lines.append(f"    \"{n['text']}\"")
            lines.append("")
        if by_crit:
            lines.append("[Assessments]")
            for crit, items in by_crit.items():
                lines.append(f"  {crit}")
                for a in items:
                    lines.append(f"    {a['_meta'].get('judgement','?')} — {a['agent']}" +
                                 (f"  · [{a['status']}]" if a['status'] else ""))
                    if a["rationale"]:
                        lines.append(f"    rationale: {a['rationale']}")
            lines.append("")
        if tensions:
            lines.append("[Open tensions]")
            for n in tensions:
                lines.append(f"  {n['text']}")
            lines.append("")
        if evidence or examples:
            lines.append("[Evidence / observations]")
            for n in evidence + examples:
                lines.append(f"  ({n['relation_to_parent']}) {n['id']}: {n['text'][:120]}")
            lines.append("")
        if sources:
            lines.append("[Sources]")
            for s in sources:
                loc = ", ".join(f"{k} {v}" for k, v in (s["locator"] or {}).items())
                lines.append(f"  {s['authors']} ({s['year']}), {s['title']}  · role={s['role']}")
                if loc:
                    lines.append(f"    {loc}")
                if s["doi"]:
                    lines.append(f"    DOI: {s['doi']}")
                if s["url"]:
                    lines.append(f"    {s['url']}")
            lines.append("")

        def clean(ns):
            for n in ns:
                n.pop("_meta", None)
            return ns
        struct = {"target": self._alias(tk), "state": tmeta.get("maturity") or tmeta.get("status") or "",
                  "order": order, "include_rejected": show_rej,
                  "sources": sources, "assessments": clean(assessments),
                  "interpretations": clean(interpretations), "evidence": clean(evidence),
                  "examples": clean(examples), "tensions": clean(tensions), "concepts": clean(concepts)}
        if order == "time":
            seq = sorted(struct["assessments"] + struct["interpretations"] + struct["evidence"] +
                         struct["examples"] + struct["tensions"] + struct["concepts"],
                         key=lambda n: n.get("at", 0))
            struct["timeline"] = [{"kind": n["kind"], "id": n["id"], "agent": n["agent"]} for n in seq]
        return {"type": "clab:trace", **struct, "render": "\n".join(lines)}

    # ── clab.diff — compare two experiment paths ──────────────────────────────────
    def op_diff(self, other: str = "", **kw) -> Dict[str, Any]:
        """[clab.diff] Compare the active Nebula against another (e.g. a fork): which operands each
        holds that the other does not."""
        a = self._active()
        b = self._need(other or kw.get("b", ""), "other nebula")
        if (self.cortex.get_meta(b) or {}).get("clab_kind") != "nebula":
            raise ValueError("clab.diff: `other` is not a Nebula.")
        sa = {self._alias(k) for k in self._members(a) if (self.cortex.get_meta(k) or {}).get("clab_kind") != "nebula"}
        sb = {self._alias(k) for k in self._members(b) if (self.cortex.get_meta(k) or {}).get("clab_kind") != "nebula"}
        return {"type": "clab:diff", "a": self._alias(a), "b": self._alias(b),
                "only_in_a": sorted(sa - sb), "only_in_b": sorted(sb - sa),
                "shared": len(sa & sb)}

    # ── clab.consensus — scoped shared commitment (does not erase dissent) ────────
    def op_consensus(self, subject: str = "", agreement: str = "", participants: str = "",
                     scope: str = "", **kw) -> Dict[str, Any]:
        """[clab.consensus] Record a scoped consensus about a subject. Per the model, consensus does
        NOT erase dissent — competing assessments/interpretations remain queryable; this only notes
        a shared commitment at a scope."""
        sk = self._need(subject, "consensus subject")
        parts = [p for p in re.split(r"[,\s]+", (participants or "").strip()) if p]
        r = self._mk("consensus", f"[Consensus] {self._alias(sk)} · {agreement or 'noted'}" +
                     (f"  scope={scope}" if scope else ""),
                     extra={"subject": sk, "agreement_level": agreement, "participants": parts,
                            "scope": scope, "preserved_dissent": True})
        return {"type": "clab:consensus", "subject": self._alias(sk), "agreement": agreement,
                "participants": parts, "preserved_dissent": True, **r}

    # ── clab.aliases — alias discovery ───────────────────────────────────────────
    def op_aliases(self) -> Dict[str, Any]:
        """[clab.aliases] The canonical→short alias table. Aliases are semantically identical to
        their canonical operator (same audit/replay event); verbose forms stay documented."""
        table = [{"canonical": "clab." + canon, "alias": "clab." + al}
                 for al, canon in sorted(self._ALIASES.items(), key=lambda kv: kv[1])]
        return {"type": "clab:aliases", "count": len(table), "aliases": table,
                "note": "aliases resolve to exactly one canonical operator with identical semantics"}
