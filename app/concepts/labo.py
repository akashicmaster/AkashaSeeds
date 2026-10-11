"""
Labo Concept Model — labo.*  (Research Labo + Hyper Labo)

A **Research Labo is a bounded research namespace** observed through canonical projections (Labo
World-Model Directive §2): SOURCE (what is present/observed), CONCEPT (what it may mean), SOCIETY
(who is observing/interpreting, with rationale) and NOTEBOOK (the cronon-ordered research history).
These are canonical VIEWS of the same namespace, not separate applications — cross-view navigation is
by Atom/Set/Link/Chunk reference, never GUI-state copying.

A **Hyper Labo composes multiple bounded namespaces without merging or rewriting them** (§9): each
participating Labo keeps its own Source Pools, concepts, Societies, notebooks, scopes and provenance;
the Hyper Labo adds a cross-lab namespace + a Joint Research Task Force Society, and its cross-lab
relations MUST NOT silently assert equivalence between local concepts.

This model is a COMPOSITION layer: it binds (references) existing `source:*` pools, `clab:*`
concepts and `society:*` spaces — it never OWNS them (§10: Society observes/operates/governs a
namespace, never owns it). New behaviour lives here in operators; the primitive operands stay passive.

Interpretations (§5) are represented as PLURAL claims with provenance (role, society, client,
rationale, evidence, cronon, competing readings) — never as irreversible categories. One source
statement may carry multiple or contradictory labels.
"""
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.api.concepts import UniversalConcept, slug

logger = logging.getLogger("Harmonia.Concept.Labo")

# Research roles (§5) and Joint-Society roles (§9.1) — modest, auditable roles, not an all-purpose
# autonomous agent. The labo layer records the ROLE + its rationale/evidence; the actual labelling is
# done by a client/plugin/LLM, whose provenance is preserved.
LABO_ROLES = ("literal_labeler", "latent_theme_labeler", "summarizer", "differentiator",
              "counter_reader", "exception_finder", "evidence_linker", "research_recorder")
HYPER_ROLES = ("bridge_finder", "translation_role", "methodology_critic", "analogy_skeptic",
               "synthesis_role", "joint_recorder")

R_HAS_SOURCE  = "labo:has_source"          # labo → a bound Source Pool / Snapshot / Set
R_HAS_CONCEPT = "labo:has_concept"         # labo → a bound concept / clab field
R_HAS_SOCIETY = "labo:has_society"         # labo → a bound Society (observer, not owner)
R_IN_LABO     = "labo:in_labo"             # an interpretation/resource → its labo namespace
R_INTERP_OF   = "labo:interpretation_of"   # interpretation → the target it reads (source/concept/set)
R_COMPETES    = "labo:competes_with"       # interpretation → a competing interpretation (plural claims)
R_BASED_ON    = "source:based_on"          # interpretation/chunk → supporting source atom (reused)

HR_COMPOSES   = "hyperlabo:composes"       # hyperlabo → a participating labo (reference, no merge)
HR_JOINT_SOC  = "hyperlabo:joint_society"  # hyperlabo → its Joint Research Task Force Society
HR_BRIDGES    = "hyperlabo:bridges"        # a cross-lab bridge → a local concept (NO equivalence asserted)
HR_IN         = "hyperlabo:in"             # a bridge/chunk → its hyperlabo namespace


class LaboConcept(UniversalConcept):
    """A bounded research namespace with four canonical projections, plus Hyper-Labo composition."""

    CONCEPT_PREFIX = "labo"
    CONCEPT_LABEL = "Research Labo — a bounded research namespace (Source·Concept·Society·Notebook)"

    CONCEPT_METHODS: Dict[str, Any] = {
        "new":     {"op": "op_new", "action": "record",
                    "desc": "Create a bounded research namespace (labo:<name>) with the four canonical projections."},
        "ls":      {"op": "op_ls", "action": "read", "desc": "List research laboratories."},
        "info":    {"op": "op_info", "action": "read",
                    "desc": "Open a Labo: its Source/Concept/Society/Notebook projection summaries + bound resources."},
        "open":    {"op": "op_info", "action": "read", "desc": "Alias of labo.info."},
        "bind":    {"op": "op_bind", "action": "record",
                    "desc": "Bind (reference) an existing Source Pool / concept / Society into a Labo (composition, not ownership)."},
        "of":      {"op": "op_of", "action": "read",
                    "desc": "Which Labos hold a Source Pool, registered first: labo.of pool=<source:pool:…>"},
        "source":  {"op": "op_source", "action": "read",
                    "desc": "SOURCE projection: the Labo's bound Source Pools/Snapshots + provenance."},
        "concept": {"op": "op_concept", "action": "read",
                    "desc": "CONCEPT projection: the Labo's bound concepts, hypotheses and interpretations."},
        "society": {"op": "op_society", "action": "read",
                    "desc": "SOCIETY projection: the Labo's bound Society + research roles + recent interpretations."},
        "notebook": {"op": "op_notebook", "action": "read",
                     "desc": "NOTEBOOK projection: the Labo's cronon-ordered Research Chunks (delegates to research.*)."},
        "interpret": {"op": "op_interpret", "action": "record",
                      "desc": "Record an interpretation (a PLURAL claim with role/rationale/evidence/cronon) of a target."},
        "why":     {"op": "op_why", "action": "read",
                    "desc": "'Why this interpretation?' — its role, Society, input, rationale/criteria and evidence (not a summary)."},
        "interpretations": {"op": "op_interpretations", "action": "read",
                            "desc": "List a Labo's interpretations (plural, competing) — optionally for one target."},
        # ── Hyper Labo (interdisciplinary composition) ──
        "hyper.new":    {"op": "op_hyper_new", "action": "record",
                         "desc": "Create a Hyper Labo composing existing Labos (no merge/rewrite of local worlds)."},
        "hyper.info":   {"op": "op_hyper_info", "action": "read",
                         "desc": "A Hyper Labo: participating Labos, cross-lab namespace, and Joint Society."},
        "hyper.bridge": {"op": "op_hyper_bridge", "action": "record",
                         "desc": "A cross-lab relation in the Hyper namespace that does NOT assert equivalence between local concepts."},
    }

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _labo_id(self, name: str) -> str:
        return name if name.startswith("labo:") else f"labo:{slug(name)}"

    def _require_labo(self, name: str) -> str:
        lid = self._labo_id(name)
        if not self._key(lid):
            raise ValueError(f"unknown labo '{name}' — labo.new it first")
        return lid

    # ── 1. lifecycle ─────────────────────────────────────────────────────────────
    def op_new(self, name: str, about: str = "", scope: str = "public",
               society: str = "") -> Dict[str, Any]:
        """Create a bounded research namespace `labo:<name>` — the unit that unifies Source, Concept,
        Society and Notebook as canonical projections of ONE namespace. A Society may later be bound
        as an observer/operator (never an owner)."""
        lid = self._labo_id(name)
        at = self._akasha_now()
        meta = {"concept": "labo", "name": name, "about": about, "scope": scope,
                "created_cronon": at, "created_wall": self._now_wall()}
        self._mk(lid, f"[{lid}] Research Labo — {about or name}", meta)
        self._add_to_set("labo:all", self._key(lid))
        if society:
            self._link(lid, society, R_HAS_SOCIETY)
        return {"labo": lid, "about": about or None, "scope": scope, "created_cronon": at,
                "projections": ["source", "concept", "society", "notebook"]}

    def op_ls(self) -> Dict[str, Any]:
        """List research laboratories (bounded research namespaces)."""
        out = []
        for k in self._members("labo:all"):
            m = self.cortex.get_meta(k) or {}
            out.append({"labo": self._alias(k), "about": m.get("about") or None, "scope": m.get("scope")})
        return {"labos": out, "count": len(out)}

    def op_bind(self, name: str, pool: str = "", concept: str = "", society: str = "",
                snapshot: str = "", origin: str = "registered") -> Dict[str, Any]:
        """Bind (reference) an existing resource into a Labo — composition, never ownership. A Source
        Pool/Snapshot, a concept/clab field, and a Society can each be bound; the resource keeps its
        own identity and provenance and may be observed by other Labos/Societies too.

        `origin` records WHO made the binding: `registered` (a hand-registered lab — the default, and
        what every binding made before this parameter existed counts as) or `shadow` (the Labo a
        workload mints for a pool no lab holds, so the Source Viewer's text analysis has a namespace).
        Resolution is registered-first (`labo.of`): a shadow never outranks a registered lab."""
        origin = str(origin or "registered").strip().lower()
        if origin not in ("registered", "shadow"):
            raise ValueError("origin must be registered or shadow")
        lid = self._require_labo(name)
        bound = {}
        for res, rel, kind in ((pool, R_HAS_SOURCE, "source"), (snapshot, R_HAS_SOURCE, "source"),
                               (concept, R_HAS_CONCEPT, "concept"), (society, R_HAS_SOCIETY, "society")):
            if res:
                self._link(lid, res, rel)
                self._link(res, lid, R_IN_LABO)
                bound.setdefault(kind, []).append(res)
                if kind == "source" and origin == "shadow":
                    # the origin of a binding is a Set, not a link property (links carry none): the pool
                    # is a member of THIS labo's shadow-bound Set. Absent = registered.
                    rk = self._key(res)
                    if rk:
                        self._add_to_set(self._shadow_set(lid), rk)
        if not bound:
            raise ValueError("pass at least one of pool= / snapshot= / concept= / society=")
        return {"labo": lid, "bound": bound, "origin": origin}

    @staticmethod
    def _shadow_set(lid: str) -> str:
        return "set:%s:shadow_bound" % lid

    def _origin_of(self, lid: str, pool_key: str) -> str:
        """`shadow` | `registered` — how THIS labo holds THIS pool. A binding made before `origin`
        existed carries no mark and counts as registered, EXCEPT the Labos the old boot schedule minted
        for pools no lab held (`src_<slug>`, about "Auto — text analysis of …"), which were shadows
        in all but the mark."""
        if pool_key and pool_key in set(self._members(self._shadow_set(lid)) or []):
            return "shadow"
        m = self.cortex.get_meta(self._key(lid)) or {}
        if str(m.get("name") or "").startswith("src_") and str(m.get("about") or "").startswith("Auto — text analysis of"):
            return "shadow"
        return "registered"

    def op_of(self, pool: str) -> Dict[str, Any]:
        """[labo.of] Which Labos hold this Source Pool, REGISTERED FIRST. The one pool → lab lookup:
        the Source Viewer's lab resolution and the workbench's shadow-labo decision
        (`workload.labo.of`) both read it, so a shadow labo can never outrank a lab someone registered,
        even one left over from an earlier run. `labos: [{labo, origin}]`, registered before shadow,
        each group in the order the labos were created."""
        pk = self._key(pool) or ""
        rows = []
        for k in self._members("labo:all") or []:
            lid = self._alias(k)
            if not any(a == pool or self._key(a) == pk for a, _r in self._links(lid, R_HAS_SOURCE)):
                continue
            rows.append({"labo": lid, "origin": self._origin_of(lid, pk)})
        rows.sort(key=lambda r: 0 if r["origin"] == "registered" else 1)     # stable: creation order within
        return {"pool": pool, "labos": rows, "count": len(rows)}

    def op_info(self, name: str) -> Dict[str, Any]:
        """Open the Labo shell: one namespace, four projection summaries + its bound resources and
        its creation cronon. Cross-view navigation is by the referenced Atoms/Sets, never a copy."""
        lid = self._require_labo(name)
        m = self.cortex.get_meta(self._key(lid)) or {}
        src = [a for a, r in self._links(lid, R_HAS_SOURCE)]
        con = [a for a, r in self._links(lid, R_HAS_CONCEPT)]
        soc = [a for a, r in self._links(lid, R_HAS_SOCIETY)]
        chunks = self._members(f"research:chunk:{self._name_of(lid)}")
        interps = self._members(f"labo:interpretation:{self._name_of(lid)}")
        return {"labo": lid, "about": m.get("about") or None, "scope": m.get("scope"),
                "created_cronon": m.get("created_cronon"),
                "projections": {
                    "source":  {"bound_pools": src, "count": len(src)},
                    "concept": {"bound_concepts": con, "interpretations": len(interps)},
                    "society": {"bound_societies": soc, "roles": list(LABO_ROLES)},
                    "notebook": {"research_chunks": len(chunks)},
                },
                "note": "canonical projections of ONE namespace — navigate by Atom/Set/Link/Chunk reference"}

    def _name_of(self, lid: str) -> str:
        return self._alias(self._key(lid)).replace("labo:", "")

    # ── 2. the four projections ──────────────────────────────────────────────────
    def op_source(self, name: str) -> Dict[str, Any]:
        """SOURCE projection — the Labo's bound Source Pools/Snapshots with status + provenance
        (dive deeper with source.pool.ls / source.read)."""
        lid = self._require_labo(name)
        pools = []
        for a, r in self._links(lid, R_HAS_SOURCE):
            pm = self._meta(a)
            pools.append({"source": a, "kind": pm.get("concept"), "status": pm.get("status"),
                          "doi": pm.get("doi") or None, "dataset_version": pm.get("dataset_version") or None,
                          "member_count": pm.get("member_count")})
        return {"labo": lid, "sources": pools, "count": len(pools),
                "note": "raw Source Atoms, pools/snapshots, provenance and analysis are reached via source.* / analysis.*"}

    def op_concept(self, name: str) -> Dict[str, Any]:
        """CONCEPT projection — the Labo's bound concepts/hypotheses + its interpretations (a
        statistical/interpretive Set opened from another projection, not sent as GUI payload)."""
        lid = self._require_labo(name)
        concepts = [{"concept": a} for a, r in self._links(lid, R_HAS_CONCEPT)]
        interps = self.op_interpretations(name).get("interpretations", [])
        return {"labo": lid, "concepts": concepts, "interpretations": interps,
                "note": "opens the SAME persisted Sets from a semantic projection; results project back as overlays"}

    def op_society(self, name: str) -> Dict[str, Any]:
        """SOCIETY projection — the Labo's bound Society + the available research roles + recent
        interpretations (each auditable via labo.why)."""
        lid = self._require_labo(name)
        socs = [a for a, r in self._links(lid, R_HAS_SOCIETY)]
        interps = self.op_interpretations(name).get("interpretations", [])
        return {"labo": lid, "societies": socs, "roles": list(LABO_ROLES),
                "recent_interpretations": interps[:20], "count": len(interps),
                "note": "interpretations are plural claims with provenance — open 'why' for role/rationale/evidence"}

    def op_notebook(self, name: str, order: str = "cronon") -> Dict[str, Any]:
        """NOTEBOOK projection — the Labo's cronon-ordered Research Chunks (delegates to research.*).
        A time-oriented projection of research activity, not a fourth data world."""
        lid = self._require_labo(name)
        try:
            from app.concepts.research import ResearchNotebook
            return ResearchNotebook(self.session).op_timeline(name=self._name_of(lid), order=order)
        except Exception as exc:
            logger.debug("labo.notebook delegate failed: %s", exc)
            chunks = self._members(f"research:chunk:{self._name_of(lid)}")
            return {"labo": lid, "research_chunks": len(chunks), "note": "use research.timeline for the ordered view"}

    # ── 3. interpretations (§5 — plural claims, provenance, cronon) ───────────────
    def op_interpret(self, name: str, target: str, role: str, label: str, rationale: str = "",
                     evidence: Any = None, confidence: str = "", society: str = "",
                     competing: str = "") -> Dict[str, Any]:
        """Record an interpretation of `target` (a Source Atom/Set/concept) by a research `role`, as
        a PLURAL claim — never an irreversible category. Keeps role, Society, client identity,
        rationale, evidence (source atoms), confidence, cronon and competing interpretations. The
        same target may carry multiple or even contradictory interpretations."""
        lid = self._require_labo(name)
        nm = self._name_of(lid)
        if role not in LABO_ROLES and role not in HYPER_ROLES:
            raise ValueError(f"role must be one of {LABO_ROLES + HYPER_ROLES} (got '{role}')")
        if not self._key(target):
            # a target that is not (yet) a stored atom is still recorded by reference
            logger.debug("labo.interpret: target '%s' is not a stored atom (recorded by reference)", target)
        at = self._akasha_now()
        seq = len(self._members(f"labo:interpretation:{nm}")) + 1
        iid = f"labo:interpretation:{nm}:{seq}"
        ev = evidence if isinstance(evidence, list) else ([] if not evidence else
                                                          [x.strip() for x in str(evidence).split(",") if x.strip()])
        meta = {"concept": "labo_interpretation", "labo": self._alias(self._key(lid)), "target": target,
                "role": role, "label": label, "rationale": rationale, "evidence": ev,
                "confidence": confidence or None, "society": society or None, "client": self._author(),
                "cronon": at, "competing": []}
        self._mk(iid, f"[{iid}] {role}: '{label}' of {target}", meta)
        self._link(iid, target, R_INTERP_OF)
        self._link(iid, lid, R_IN_LABO)
        for e in ev:
            self._link(iid, e, R_BASED_ON)
        self._add_to_set(f"labo:interpretation:{nm}", self._key(iid))
        self._add_to_set(f"labo:role:{role}", self._key(iid))
        if competing:
            for c in [x.strip() for x in competing.split(",") if x.strip()]:
                self._link(iid, c, R_COMPETES)
                self._link(c, iid, R_COMPETES)          # symmetric: the two readings compete
                cm = self._meta(c)
                if cm:
                    self._set_meta(self._key(c), "competing", list(set((cm.get("competing") or []) + [iid])))
            self._set_meta(self._key(iid), "competing",
                           [x.strip() for x in competing.split(",") if x.strip()])
        return {"interpretation": iid, "labo": self._alias(self._key(lid)), "target": target,
                "role": role, "label": label, "cronon": at, "evidence": ev,
                "note": "a plural claim — not an irreversible category; the target may hold competing readings"}

    def op_why(self, interpretation: str) -> Dict[str, Any]:
        """'Why this interpretation?' — expose the Society, role, input target, rationale/criteria and
        evidence links that produced it. Provenance is NOT collapsed into an opaque summary (§5.2)."""
        k = self._key(interpretation)
        if not k:
            raise ValueError(f"unknown interpretation '{interpretation}'")
        m = self.cortex.get_meta(k) or {}
        if m.get("concept") != "labo_interpretation":
            raise ValueError(f"'{interpretation}' is not an interpretation")
        return {"interpretation": self._alias(k), "labo": m.get("labo"), "role": m.get("role"),
                "society": m.get("society"), "client": m.get("client"), "target": m.get("target"),
                "label": m.get("label"), "rationale": m.get("rationale") or "(no rationale recorded)",
                "criteria": m.get("rationale") or None, "evidence": m.get("evidence") or [],
                "confidence": m.get("confidence"), "cronon": m.get("cronon"),
                "competing": m.get("competing") or []}

    def op_interpretations(self, name: str, target: str = "") -> Dict[str, Any]:
        """List a Labo's interpretations (plural, possibly contradictory) — optionally only those of
        one target (so double-meaning / role-dependent readings are visible side by side)."""
        lid = self._require_labo(name)
        nm = self._name_of(lid)
        out = []
        for k in self._members(f"labo:interpretation:{nm}"):
            m = self.cortex.get_meta(k) or {}
            if target and m.get("target") != target and self._alias(self._key(target)) != m.get("target"):
                continue
            out.append({"interpretation": self._alias(k), "role": m.get("role"), "label": m.get("label"),
                        "target": m.get("target"), "society": m.get("society"), "client": m.get("client"),
                        "cronon": m.get("cronon"), "evidence": len(m.get("evidence") or []),
                        "competing": m.get("competing") or []})
        out.sort(key=lambda r: r.get("cronon") or 0)
        return {"labo": lid, "target": target or None, "interpretations": out, "count": len(out)}

    # ── 4. Hyper Labo (§9 — composition without merge) ────────────────────────────
    def _hyper_id(self, name: str) -> str:
        return name if name.startswith("hyperlabo:") else f"hyperlabo:{slug(name)}"

    def op_hyper_new(self, name: str, labos: str, about: str = "", society: str = "") -> Dict[str, Any]:
        """Create a Hyper Labo composing existing Labos WITHOUT merging or rewriting them. Each
        participating Labo keeps its own Source Pools, concepts, Societies, notebooks, scopes and
        provenance; the Hyper Labo adds a cross-lab namespace + (optionally) a Joint Society."""
        hid = self._hyper_id(name)
        members = [x.strip() for x in labos.split(",") if x.strip()]
        for lb in members:
            if not self._key(self._labo_id(lb)):
                raise ValueError(f"participating labo '{lb}' does not exist — labo.new it first")
        at = self._akasha_now()
        meta = {"concept": "hyperlabo", "name": name, "about": about,
                "participating": [self._alias(self._key(self._labo_id(lb))) for lb in members],
                "created_cronon": at}
        self._mk(hid, f"[{hid}] Hyper Labo — {about or name}", meta)
        self._add_to_set("hyperlabo:all", self._key(hid))
        for lb in members:
            self._link(hid, self._labo_id(lb), HR_COMPOSES)
        if society:
            self._link(hid, society, HR_JOINT_SOC)
        return {"hyperlabo": hid, "participating": meta["participating"], "roles": list(HYPER_ROLES),
                "created_cronon": at, "note": "composes autonomous Labos — it never mutates or merges them"}

    def op_hyper_info(self, name: str) -> Dict[str, Any]:
        """A Hyper Labo: its participating Labos, the cross-lab namespace, its Joint Task-Force
        Society, and the cross-lab bridges recorded so far."""
        hid = self._hyper_id(name)
        if not self._key(hid):
            raise ValueError(f"unknown hyperlabo '{name}'")
        m = self.cortex.get_meta(self._key(hid)) or {}
        joint = [a for a, r in self._links(hid, HR_JOINT_SOC)]
        bridges = self._members(f"hyperlabo:bridge:{slug(name)}")
        return {"hyperlabo": hid, "about": m.get("about") or None,
                "participating": [a for a, r in self._links(hid, HR_COMPOSES)],
                "joint_society": joint, "roles": list(HYPER_ROLES), "cross_lab_bridges": len(bridges),
                "note": "cross-lab findings live HERE until a local Labo explicitly adopts them"}

    def op_hyper_bridge(self, name: str, a: str, b: str, rel: str = "related_across",
                        rationale: str = "") -> Dict[str, Any]:
        """Record a CROSS-LAB relation between two local concepts in the Hyper namespace. It does NOT
        assert equivalence — a superficial similarity is a bridge to investigate, not a merge (§9,§14).
        Written only into the Hyper namespace; the participating Labos are never mutated."""
        hid = self._hyper_id(name)
        if not self._key(hid):
            raise ValueError(f"unknown hyperlabo '{name}'")
        at = self._akasha_now()
        seq = len(self._members(f"hyperlabo:bridge:{slug(name)}")) + 1
        bid = f"hyperlabo:bridge:{slug(name)}:{seq}"
        meta = {"concept": "hyperlabo_bridge", "hyperlabo": self._alias(self._key(hid)),
                "a": a, "b": b, "relation": rel, "rationale": rationale, "asserts_equivalence": False,
                "adopted_by": [], "cronon": at, "client": self._author()}
        self._mk(bid, f"[{bid}] cross-lab: {a} —{rel}— {b} (no equivalence asserted)", meta)
        self._link(bid, a, HR_BRIDGES)
        self._link(bid, b, HR_BRIDGES)
        self._link(bid, hid, HR_IN)
        self._add_to_set(f"hyperlabo:bridge:{slug(name)}", self._key(bid))
        return {"bridge": bid, "hyperlabo": self._alias(self._key(hid)), "a": a, "b": b, "relation": rel,
                "asserts_equivalence": False, "cronon": at,
                "note": "a candidate cross-domain link; a local Labo may later accept/challenge/refine/reject it"}
