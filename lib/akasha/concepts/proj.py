"""
TensorProjection (proj) — Concept Model (M2)
============================================

Universal Operand for organising chunks. The "watchful eye alongside" of the writing-support Note Loom.
spec: tensor-projection-spec.md v1.0.0 / loom-ui-spec v2.5.0

Design core:
  - FocalPoint = any atom (especially a Note chunk). proj references chunks without owning them.
  - Each chunk has three threads: Resonance (tensor neighbourhood) / Lens (interpretive ontology) /
    Thread (associative traversal).
  - UnwrittenVoid = unconnected axes → ? tags (pointing below the iceberg).
  - **There is not a single write operator** (proj.write/compose/suggest do not exist =
    structural guarantee that the system cannot write on the author's behalf).
  - domain-agnostic: swap out the ontology (axes) for molecule / cosmos etc. and the structure is isomorphic.
  - proj weight = proximity / associative strength; entirely separate from fact/corr credibility (truth/falsity).

────────────────────────────────────────────────────────────────────────
"Intelligence" lives in the backend (Tier 1). Policy for this file:
  Concept model skeleton (atom/link/operator/set) + graph-based deterministic fallback
  + pluggable hooks for real models (self.cortex._plugins["proj.*"]).
  → Works and is debuggable right now; real NLP/embedding/web can be plugged in later.

Pluggable hooks (used when available, fallback when absent):
  proj.extract.nlp        text → [tag words]     (fallback: body-text match against registered axis words)
  proj.resonate.embed     focal,scope → [(id,w)] (fallback: Jaccard neighbourhood via shared tags)
  proj.associate.web      query → [link]          (fallback: empty)

────────────────────────────────────────────────────────────────────────
Integration notes (for Claude Code)
  kernel.py _METHOD_TO_ACTION:
    "proj.new":"write","proj.open":"write","proj.ls":"read","proj.map":"read","proj.rm":"drop",
    "proj.axis.add":"write","proj.extract":"write","proj.project":"read","proj.scope":"read",
    "proj.resonate":"read","proj.lens":"read","proj.associate":"read",
    "proj.void":"write","proj.tag":"write","proj.diagnose":"read",
  router.py: optionally add short forms such as cp/pj.

  ★ Integration with note (following §8: concepts must not call each other directly):
    Calling proj.extract(focal=version_id) after note.add/edit is the responsibility of
    the loom orchestration layer (UI or kernel job). Do not import/dispatch proj directly
    from note.py. The M1 _extract_tags hook belongs to that layer.

DEBUG notes:
  - The return type of get_chunk (dict/str) is absorbed by _content/_meta. Verify against the implementation.
  - Align get_collection_members / get_set_members names with the implementation.
  - Fallback is deterministic, so expected values can be verified with The Notebook fixture
    (#pen shared → Ch.1↔Ch.3 resonate, sense:* unconnected → void).
  - Plugging in a real model goes through the _plugin hook (return shape of operations is fixed).
"""

import time
import logging
from typing import List, Dict, Any, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Projection")

CONTEXT_KEY_ACTIVE = "active_proj_root"
INDEX_SET = "set:proj:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"


class ProjectionConcept(BaseConcept):
    """TensorProjection — universal Operand for organising chunks."""

    CONCEPT_PREFIX = "proj"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE
    CONCEPT_METHODS = {
        "new":   {"op": "op_new"},
        "open":  {"op": "op_open",
                  "coerce": lambda d: {"proj_id": d.get("proj_id") or d.get("id", "")}},
        "ls":    {"op": "op_list_all"},
        "map":   {"op": "op_map"},
        "rm":    {"op": "op_delete"},
        "axis.add": {"op": "op_add_axis",
                     "coerce": lambda d: {"word": d.get("word") or d.get("name", ""),
                                          "ref_id": d.get("ref_id")}},
        "extract":  {"op": "op_extract",
                     "coerce": lambda d: {"focal": (d.get("focal") or d.get("version_id")
                                                    or d.get("atom_id") or d.get("id", "")),
                                          "text": d.get("text")}},
        "project":  {"op": "op_project"},
        "scope":    {"op": "op_scope"},
        "resonate": {"op": "op_resonate",
                     "coerce": lambda d: {"focal": (d.get("focal") or d.get("atom_id")
                                                    or d.get("id", "")),
                                          "scope": d.get("scope", 1)}},
        "lens":     {"op": "op_lens",
                     "coerce": lambda d: {"focal": (d.get("focal") or d.get("atom_id")
                                                    or d.get("id", ""))}},
        "associate": {"op": "op_associate",
                      "coerce": lambda d: {"focal": (d.get("focal") or d.get("atom_id")
                                                     or d.get("id", "")),
                                           "axis": d.get("axis"), "scope": d.get("scope", 1)}},
        "void":  {"op": "op_void",
                  "coerce": lambda d: {"focal": (d.get("focal") or d.get("atom_id")
                                                 or d.get("id", ""))}},
        "tag":   {"op": "op_tag"},
        "diagnose": {"op": "op_diagnose"},
    }

    # ── ctor / auto-mount ───────────────────────────────────
    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ── helpers ─────────────────────────────────────────────
    def _auth(self):
        aid = getattr(self.session, "client_id", "system")
        return aid, [f"owner:user_{aid}", f"view:user_{aid}"]

    def _pset(self, suffix: Optional[str] = None) -> str:
        base = f"set:proj:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _content(self, key):
        c = self.cortex.get_chunk(key)
        return (c.get("content", "") if isinstance(c, dict) else c) or ""

    def _meta(self, key):
        if hasattr(self.cortex, "get_meta"):
            m = self.cortex.get_meta(key)
            if m is not None:
                return m
        c = self.cortex.get_chunk(key)
        return (c.get("meta", {}) if isinstance(c, dict) else {}) or {}

    def _plugin(self, name):
        plugins = getattr(self.cortex, "_plugins", {}) or {}
        return plugins.get(name)

    def _require_access(self, atom_id, label="Atom"):
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    def _get_or_create_tag(self, word: str) -> str:
        """tag = concept-word atom (vocab; the set:concept side of the two namespaces)."""
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        author, scopes = self._auth()
        key = self.cortex.put_chunk(
            content=word,
            meta={"type": "concept_word", "word": word,
                  "concept_model": "proj", "created_at": time.time()},
            author=author, scopes=scopes,
        )
        self.cortex.set_alias(key, alias)
        return key

    def _axis_words(self) -> List[str]:
        """Words of registered axes (vocabulary for fallback extraction)."""
        words = []
        for axis_id in self.cortex.get_collection_members(self._pset("axes")):
            words.append(self._content(axis_id))
        return [w for w in words if w]

    def _tags_of(self, focal: str) -> set:
        """Tags connected to focal (concept_word targets of lens_of / associates)."""
        out = set()
        for rel in ("proj:lens_of", "proj:associates"):
            for dst, _r in self.cortex.get_adjacent_links(focal, rel):
                if self._meta(dst).get("type") == "concept_word":
                    out.add(dst)
        return out

    # ── lifecycle ───────────────────────────────────────────
    def op_new(self, title: str, domain: str = "writing") -> Dict[str, Any]:
        author, scopes = self._auth()
        root_id = self.cortex.put_chunk(
            content=f"[ Projection: {title} ]",
            meta={"type": "concept", "concept": "proj", "role": "root",
                  "title": title, "domain": domain, "created_at": time.time()},
            author=author, scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        # sets first
        self.ensure_concept_set()
        self.cortex.create_set(self._pset())
        for sub in ("axes", "projections", "voids", "threads", "tags"):
            self.cortex.create_set(self._pset(sub))
        self.cortex.create_set(INDEX_SET)
        self.cortex.add_to_set(INDEX_SET, root_id)
        self.cortex.add_to_set(self._pset(), root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        logger.info("[ProjectionConcept] new '%s' (%s) domain=%s", title, root_id[:8], domain)
        return {"status": "created", "concept_id": root_id, "proj_id": root_id,
                "title": title, "domain": domain}

    def op_open(self, proj_id: str) -> Dict[str, Any]:
        meta = self._meta(proj_id)
        if not meta or meta.get("concept") != "proj":
            raise RuntimeError(f"Atom '{proj_id[:12]}' is not a proj root.")
        self.concept_id = proj_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, proj_id)
        return {"status": "opened", "proj_id": proj_id, "title": meta.get("title", "")}

    def op_list_all(self) -> Dict[str, Any]:
        items = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self.cortex.check_access(key, self.allowed_scopes):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "proj":
                continue
            items.append({"proj_id": key, "title": meta.get("title", ""),
                          "domain": meta.get("domain", ""), "created_at": meta.get("created_at", 0)})
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"projections": items, "count": len(items)}

    def op_delete(self) -> Dict[str, Any]:
        self._require_concept()
        target = self.concept_id
        self.cortex.drop_chunk(target, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "proj_id": target}

    # ── axis registration (incorporating ontology as an axis) ──────────
    def op_add_axis(self, word: str, ref_id: str = None) -> Dict[str, Any]:
        """[proj.axis.add] Register an axis. If ref_id is provided, points to that ontology atom.
        word is the axis name (emo:craving / sense:texture / polti:supplication …)."""
        self._require_concept()
        author, _ = self._auth()
        axis_id = self._get_or_create_tag(word)
        self.cortex.add_to_set(self._pset("axes"), axis_id)
        self.register_concept_node(axis_id)                      # set:concept side (vocab)
        self.cortex.put_link(self.concept_id, axis_id, "proj:has_axis", author=author)
        if ref_id:
            self._require_access(ref_id, "Ontology atom")
            self.cortex.put_link(axis_id, ref_id, "proj:refers_to", author=author)
        return {"status": "axis_added", "axis": word, "axis_id": axis_id}

    # ── extract (auto-tag: called by the loom layer immediately after writing) ──────
    def op_extract(self, focal: str, text: str = None) -> Dict[str, Any]:
        """[proj.extract] Extract tags from focal (chunk) and wire chunk→tag links.
        Uses the NLP plugin if available; falls back to body-text matching against registered axis words."""
        self._require_concept()
        self._require_access(focal, "Focal")
        author, _ = self._auth()
        if text is None:
            text = self._content(focal)

        nlp = self._plugin("proj.extract.nlp")
        if nlp:
            words = list(nlp(text)) or []
        else:
            low = (text or "").lower()
            words = [w for w in self._axis_words() if w and w.lower() in low]

        tagged = []
        for w in words:
            tag_id = self._get_or_create_tag(w)
            self.cortex.add_to_set(self._pset("tags"), tag_id)
            # lens_of: interpretive ontology axis (emo/polti…); otherwise associates
            rel = "proj:lens_of" if (":" in w) else "proj:associates"
            self.cortex.put_link(focal, tag_id, rel, author=author)
            tagged.append(w)
        return {"status": "extracted", "focal": focal, "tags": tagged}

    # ── The three threads ─────────────────────────────────────────────
    def op_resonate(self, focal: str, scope: int = 1) -> Dict[str, Any]:
        """[proj.resonate] DimensionalResonance: tensor neighbourhood.
        Uses the embed plugin if available; falls back to Jaccard neighbourhood via shared tags."""
        self._require_concept()
        self._require_access(focal, "Focal")
        author, _ = self._auth()
        embed = self._plugin("proj.resonate.embed")
        if embed:
            neighbors = embed(focal, scope) or []          # [(id, weight)]
        else:
            ftags = self._tags_of(focal)
            scored = []
            for other in self.cortex.get_collection_members(self._pset("tags")):
                pass  # tags are not focals; iterate focals via incoming links below
            # Gather other focals that share tags
            cand = {}
            for tag in ftags:
                for src, _r in self.cortex.get_incoming_links(tag, "proj:lens_of"):
                    if src != focal:
                        cand.setdefault(src, set()).add(tag)
                for src, _r in self.cortex.get_incoming_links(tag, "proj:associates"):
                    if src != focal:
                        cand.setdefault(src, set()).add(tag)
            for other, shared in cand.items():
                otags = self._tags_of(other)
                union = ftags | otags
                w = len(shared) / len(union) if union else 0.0
                if w > 0:
                    scored.append((other, round(w, 3)))
            scored.sort(key=lambda x: x[1], reverse=True)
            neighbors = scored[: max(1, scope) * 5]

        for other, w in neighbors:
            self.cortex.put_link(focal, other, "proj:resonates_with", w=w, author=author)
        return {"status": "resonated", "focal": focal,
                "neighbors": [{"id": i, "weight": w} for i, w in neighbors]}

    def op_lens(self, focal: str) -> Dict[str, Any]:
        """[proj.lens] SemanticLens: the interpretive ontology connected to focal (by axis).
        A different way of viewing the same chunk."""
        self._require_concept()
        self._require_access(focal, "Focal")
        lenses = {}
        for dst, _r in self.cortex.get_adjacent_links(focal, "proj:lens_of"):
            word = self._content(dst)
            family = word.split(":", 1)[0] if ":" in word else "other"
            lenses.setdefault(family, []).append(word)
        return {"status": "lensed", "focal": focal, "lenses": lenses}

    def op_associate(self, focal: str, axis: str = None, scope: int = 1) -> Dict[str, Any]:
        """[proj.associate] AssociativeThread: associative traversal through the semantic network.
        axis='web' → external links (web plugin; empty if absent)."""
        self._require_concept()
        self._require_access(focal, "Focal")
        author, _ = self._auth()
        if axis == "web":
            web = self._plugin("proj.associate.web")
            query = self._content(focal)[:120]
            links = (web(query) if web else []) or []
            return {"status": "associated", "focal": focal, "axis": "web", "links": links}

        # Association: BFS through shared tags + existing proj:associates, up to scope levels
        seen, frontier, out = {focal}, [focal], []
        for _ in range(max(1, scope)):
            nxt = []
            for node in frontier:
                for tag in self._tags_of(node):
                    if axis and not self._content(tag).startswith(axis):
                        continue
                    for src, _r in self.cortex.get_incoming_links(tag, "proj:associates"):
                        if src not in seen:
                            seen.add(src); nxt.append(src); out.append(src)
                    for src, _r in self.cortex.get_incoming_links(tag, "proj:lens_of"):
                        if src not in seen:
                            seen.add(src); nxt.append(src); out.append(src)
            frontier = nxt
        return {"status": "associated", "focal": focal, "axis": axis,
                "neighbors": out}

    # ── UnwrittenVoid (pointing below the iceberg) ──────────────────────
    def op_void(self, focal: str) -> Dict[str, Any]:
        """[proj.void] Surface registered axes that focal is not connected to as ? tags.
        Weakness threshold is adjustable via plugin (fallback: 'unconnected = void')."""
        self._require_concept()
        self._require_access(focal, "Focal")
        author, _ = self._auth()
        connected = {self._content(t) for t in self._tags_of(focal)}
        voids = []
        for axis_id in self.cortex.get_collection_members(self._pset("axes")):
            w = self._content(axis_id)
            if w and w not in connected:
                self.cortex.put_link(focal, axis_id, "proj:void_at", author=author)
                voids.append(w)
        return {"status": "void_surfaced", "focal": focal, "voids": voids,
                "question": self._void_question(voids)}

    def _void_question(self, voids):
        """The question posed by a ? tag (minimal — a question, not a command). Wording is swappable via ontology/locale."""
        if not voids:
            return None
        sense = [v for v in voids if v.startswith("sense:")]
        if sense:
            kind = sense[0].split(":", 1)[1]
            return f"Does this carry {kind}?"
        return f"Unwritten: {', '.join(voids[:3])}?"

    def op_tag(self, focal: str, word: str, action: str = "add") -> Dict[str, Any]:
        """[proj.tag] Add or remove a ? tag / tag (manual pin/fold)."""
        self._require_concept()
        self._require_access(focal, "Focal")
        author, _ = self._auth()
        tag_id = self._get_or_create_tag(word)
        if action == "clear":
            for rel in ("proj:lens_of", "proj:associates", "proj:void_at"):
                self.cortex.remove_link(focal, tag_id, rel)
            return {"status": "tag_cleared", "focal": focal, "tag": word}
        self.cortex.add_to_set(self._pset("tags"), tag_id)
        self.cortex.put_link(focal, tag_id, "proj:associates", author=author)
        return {"status": "tag_added", "focal": focal, "tag": word}

    # ── Projection / re-projection (integration of the three threads) ───────────────────────
    def op_project(self, focal: str, axes: List[str] = None, scope: int = 1) -> Dict[str, Any]:
        """[proj.project] Project focal through chosen axes and scope → ResonanceField (all three threads combined)."""
        self._require_concept()
        self._require_access(focal, "Focal")
        field = {
            "resonance": self.op_resonate(focal, scope).get("neighbors", []),
            "lens": self.op_lens(focal).get("lenses", {}),
            "thread": self.op_associate(focal, None, scope).get("neighbors", []),
            "void": self.op_void(focal).get("voids", []),
        }
        if axes:
            field["lens"] = {k: v for k, v in field["lens"].items() if k in axes}
        return {"status": "projected", "focal": focal, "axes": axes, "scope": scope,
                "field": field}

    def op_scope(self, focal: str, scope: int = 1, axes: List[str] = None) -> Dict[str, Any]:
        """[proj.scope] Re-project with a different scope/axis (slider)."""
        return self.op_project(focal, axes=axes, scope=scope)

    # ── map / diagnose ──────────────────────────────────────
    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        return {
            "proj_id": self.concept_id,
            "axes": [self._content(a) for a in self.cortex.get_collection_members(self._pset("axes"))],
            "tag_count": len(self.cortex.get_collection_members(self._pset("tags"))),
        }

    def op_diagnose(self) -> Dict[str, Any]:
        """[proj.diagnose] Surface focals with many voids / isolated / unprojected (targets tagged focals)."""
        self._require_concept()
        void_heavy, isolated = [], []
        focals = set()
        for tag in self.cortex.get_collection_members(self._pset("tags")):
            for rel in ("proj:lens_of", "proj:associates"):
                for src, _r in self.cortex.get_incoming_links(tag, rel):
                    focals.add(src)
        for f in focals:
            voids = self.cortex.get_adjacent_links(f, "proj:void_at")
            res = self.cortex.get_adjacent_links(f, "proj:resonates_with")
            if len(voids) >= 3:
                void_heavy.append(f)
            if not res and not self._tags_of(f):
                isolated.append(f)
        return {"void_heavy": void_heavy, "isolated": isolated}
