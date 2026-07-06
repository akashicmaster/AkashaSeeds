"""
Cast Concept Model.
A cognitive topology model for fictional characters, scenario entities,
game agents, and future HumanConcept-compatible actor analysis.

Concept:
    A Cast is not a list of attributes.
    A Cast is a graph of tensions.

Namespace contract:
    - Content atoms        -> set:cast:{concept_id} and subset sets
    - Concept-word atoms   -> set:concept:{concept_id}

Version: 2.0.1 (Claude review / bug fixes applied)
Fixes:
    - Bug 1: op_new no longer passes concept_word="cast" to _register
    - Bug 2: sys:bottom is now set when first atom is added
    - Bug 3: subset→relation mapping uses explicit table (SUBSET_TO_RELATION)
    - Bug 4: reaction_threshold capped at 0.9 to allow crisis breakthrough
    - Bug 5: cast:fears link direction corrected (root → emotion atom)
    - Bug 6: op_add_emotion parameter renamed from 'object' (Python built-in)
             to 'obj' to avoid shadowing
"""

import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Cast")

CONTEXT_KEY_ACTIVE = "active_cast_root"
INDEX_SET = "set:cast:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

# Bug 3 fix: explicit mapping to avoid broken string manipulation
SUBSET_TO_RELATION: Dict[str, str] = {
    "identity":         "cast:has_identity",
    "appearance":       "cast:has_appearance",
    "ability":          "cast:has_ability",
    "adornments":       "cast:has_adornment",
    "skills":           "cast:has_skill",
    "possessions":      "cast:has_possession",
    "social_positions": "cast:has_social_position",
    "emotions":         "cast:has_emotion",
    "wounds":           "cast:has_wound",
    "policies":         "cast:has_policy",
    "rules":            "cast:has_rule",
    "traits":           "cast:has_trait",
    "thresholds":       "cast:has_threshold",
    "states":           "cast:has_state",
    "masks":            "cast:has_mask",
    "secrets":          "cast:has_secret",
    "outputs":          "cast:has_output",
    "contradictions":   "cast:has_contradiction",
    "shadows":          "cast:has_shadow",
    "bonds":            "cast:has_bond",
    "bond_updates":     "cast:has_bond_update",
    "fates":            "cast:has_fate",
    "callings":         "cast:has_calling",
    "roles":            "cast:has_role",
    "myths":            "cast:has_myth",
    "arcs":             "cast:has_arc",
}


class CastConcept(BaseConcept):
    """Cognitive topology model for a character / narrative actor."""

    CONCEPT_PREFIX = "cast"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE  # expose module constant as class attribute
    CONCEPT_METHODS = {
        # Basic
        "new":  {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "cast_id": d.get("cast_id") or d.get("id") or d.get("entity_id", "")
            },
        },
        "ls":       {"op": "op_list_all"},
        "map":      {"op": "op_map"},
        "clone":    {"op": "op_clone"},
        "rm":       {"op": "op_delete"},
        # Identity / Physique / Social
        "identity.set": {"op": "op_set_identity"},
        "appear.set":   {"op": "op_set_appearance"},
        "ability.set":  {"op": "op_set_ability"},
        "adorn.add":    {"op": "op_add_adornment"},
        "skill.add":    {"op": "op_add_skill"},
        "possess.add":  {"op": "op_add_possession"},
        "pos.set":      {"op": "op_set_social_position"},
        # Behaviour-generating layers
        "emotion.add":  {"op": "op_add_emotion"},
        "wound.add":    {"op": "op_add_wound"},
        "policy.add":   {"op": "op_add_policy"},
        "rule.add":     {"op": "op_add_rule"},
        "trait.set":    {"op": "op_set_trait"},
        "state.set":    {"op": "op_set_state"},
        # Surface layers
        "mask.add":     {"op": "op_add_mask"},
        "secret.add":   {"op": "op_add_secret"},
        "output.add":   {"op": "op_add_output"},
        # Contradiction / Shadow
        "conflict.add": {"op": "op_add_contradiction"},
        "shadow.add":   {"op": "op_add_shadow"},
        # Bond
        "bond.add":     {"op": "op_add_bond"},
        "bond.update":  {"op": "op_update_bond"},
        # Destiny
        "fate.set":     {"op": "op_set_fate"},
        "calling.set":  {"op": "op_set_calling"},
        "role.set":     {"op": "op_set_role"},
        "myth.set":     {"op": "op_set_myth"},
        "arc.add":      {"op": "op_add_arc"},
        # Analysis
        "react":        {"op": "op_react"},
        "diagnose":     {"op": "op_diagnose"},
    }

    SUBSETS = list(SUBSET_TO_RELATION.keys())

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cast_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:cast:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._cast_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._cast_set(suffix))
        self.cortex.create_set(INDEX_SET)

    def _get_or_create_concept_word(self, word: str) -> str:
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        author_id, scopes = self._author_and_scopes()
        key = self.cortex.put_chunk(
            content=word,
            meta={
                "type": "concept_word",
                "word": word,
                "concept_model": "cast",
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.set_alias(key, alias)
        return key

    def _register(
        self,
        key: str,
        subset_suffix: Optional[str] = None,
        concept_word: Optional[str] = None,
    ) -> None:
        author_id, _ = self._author_and_scopes()
        self.cortex.add_to_set(self._cast_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._cast_set(subset_suffix), key)
        if concept_word:
            cw_key = self._get_or_create_concept_word(concept_word)
            self.register_concept_node(cw_key)
            self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        if not atom_id:
            raise ValueError(f"{label} id is required.")
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    def _visible(self, atom_id: str) -> bool:
        return bool(atom_id and self.cortex.check_access(atom_id, self.allowed_scopes))

    def _members(self, suffix: str) -> List[str]:
        return [
            key for key in self.cortex.get_collection_members(self._cast_set(suffix))
            if self._visible(key)
        ]

    def _meta(self, key: str) -> Dict[str, Any]:
        return self.cortex.get_meta(key) or {}

    def _content(self, key: str) -> str:
        value = self.cortex.get_chunk(key)
        if isinstance(value, dict):
            return value.get("content", "")
        return value or ""

    def _summary(self, key: str) -> Dict[str, Any]:
        return {"id": key, "content": self._content(key), "meta": self._meta(key)}

    def _put_atom(
        self,
        content: str,
        atom_type: str,
        subset: str,
        meta_extra: Optional[Dict[str, Any]] = None,
        concept_word: Optional[str] = None,
    ) -> str:
        author_id, scopes = self._author_and_scopes()
        meta = {
            "type": atom_type,
            "concept": "cast",
            "created_at": time.time(),
        }
        if meta_extra:
            meta.update(meta_extra)
        key = self.cortex.put_chunk(
            content=content, meta=meta, author=author_id, scopes=scopes
        )
        self._register(key, subset_suffix=subset, concept_word=concept_word)

        # Bug 3 fix: use explicit relation table
        relation = SUBSET_TO_RELATION.get(subset, f"cast:has_{subset}")
        self.cortex.put_link(self.concept_id, key, relation, author=author_id)

        self._append_to_timeline(key, author_id)
        return key

    def _append_to_timeline(self, node_id: str, author_id: str) -> None:
        tail_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")
        if not tail_links:
            # Bug 2 fix: set both sys:top AND sys:bottom for the first node
            self.cortex.put_link(self.concept_id, node_id, "sys:top", author=author_id)
            self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)
        else:
            last_node_id = tail_links[0][0]
            self.cortex.put_link(last_node_id, node_id, "sys:next", author=author_id)
            self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)
            self.cortex.remove_link(self.concept_id, last_node_id, "sys:bottom")
            self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)

    @staticmethod
    def _clamp01(value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except Exception:
            return default

    @staticmethod
    def _as_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _current_trait_vector(self) -> Dict[str, float]:
        """Return the most recent trait vector, or defaults."""
        defaults = {
            "energy": 0.5,
            "process": 0.5,
            "response": 0.5,
            "trust": 0.5,
            "flexibility": 0.5,
        }
        trait_ids = self._members("traits")
        if trait_ids:
            stored = self._meta(trait_ids[-1]).get("vector", {})
            defaults.update({k: self._clamp01(v) for k, v in stored.items()})
        return defaults

    # ------------------------------------------------------------------
    # Basic operators
    # ------------------------------------------------------------------

    def op_new(
        self,
        name: str,
        identity: str = "",
        title: str = "",
    ) -> Dict[str, Any]:
        author_id, scopes = self._author_and_scopes()
        cast_name = name or title
        if not cast_name:
            raise ValueError("cast.new requires name.")

        root_id = self.cortex.put_chunk(
            content=f"[ Cast: {cast_name} ]",
            meta={
                "type": "concept",
                "concept": "cast",
                "role": "root",
                "name": cast_name,
                "identity": identity,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        self._create_sets()

        # Bug 1 fix: root atom goes into content set only.
        # Do NOT pass concept_word="cast" here — that would register root_id
        # into the concept namespace, violating the Two-Namespace Rule.
        self.cortex.add_to_set(self._cast_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)

        if identity:
            self.op_set_identity(identity)

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)

        logger.info("[CastConcept] Created '%s' (%s)", cast_name, root_id[:8])
        return {
            "status": "created",
            "concept_id": root_id,   # standard key for SpaceConcept
            "cast_id": root_id,
            "name": cast_name,
            "identity": identity,
        }

    def op_open(self, cast_id: str) -> Dict[str, Any]:
        meta = self._meta(cast_id)
        if not meta or meta.get("concept") != "cast":
            raise RuntimeError(f"Atom '{cast_id[:12]}' is not a cast root.")
        if not self._visible(cast_id):
            raise RuntimeError(f"Cast not accessible: {cast_id[:12]}")
        self.concept_id = cast_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, cast_id)
        return {
            "status": "opened",
            "cast_id": cast_id,
            "name": meta.get("name", ""),
            "identity": meta.get("identity", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        casts = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "cast":
                continue
            casts.append({
                "cast_id": key,
                "name": meta.get("name", ""),
                "identity": meta.get("identity", ""),
                "created_at": meta.get("created_at", 0),
            })
        casts.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"casts": casts, "count": len(casts)}

    def op_delete(self) -> Dict[str, Any]:
        self._require_concept()
        target = self.concept_id
        self.cortex.drop_chunk(target, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "cast_id": target}

    def op_clone(self, name: str) -> Dict[str, Any]:
        """[cast.clone] Copy the full cast graph to a new named cast.

        All subset atoms (traits, masks, wounds, bonds, arcs, …) are shared
        between source and clone — atoms are content-addressed, so identity is
        preserved without duplication. Only the new root atom and its outgoing
        links (root→atom, sys:top, sys:bottom) are freshly created.

        Inter-atom links (sys:next/previous, cast:wounded_by, etc.) already
        exist at the atom level and are inherited automatically.

        Back-links from atoms to the original root (e.g. cast:hides on mask
        atoms) remain pointing to the source root; this is a known v1 limitation.

        Session focus is restored to the source cast after cloning.
        """
        self._require_concept()
        if not name:
            raise ValueError("cast.clone requires a name.")

        src_id = self.concept_id
        src_meta = self._meta(src_id)
        author_id, _ = self._author_and_scopes()

        # Create a bare new root (no identity seed — subset copy covers all atoms).
        clone = type(self)(self.session)
        result = clone.op_new(name=name)
        new_id = result["cast_id"]

        # Copy subset members: set membership + root-level links.
        cloned_count = 0
        for subset_name, rel in SUBSET_TO_RELATION.items():
            for atom_id in self.cortex.get_collection_members(
                f"set:cast:{src_id}:{subset_name}"
            ):
                if not self._visible(atom_id):
                    continue
                self.cortex.add_to_set(f"set:cast:{new_id}", atom_id)
                self.cortex.add_to_set(f"set:cast:{new_id}:{subset_name}", atom_id)
                self.cortex.put_link(new_id, atom_id, rel, author=author_id)
                cloned_count += 1

        # Copy concept catalog.
        for atom_id in self.cortex.get_collection_members(f"set:concept:{src_id}"):
            if self._visible(atom_id):
                self.cortex.add_to_set(f"set:concept:{new_id}", atom_id)

        # Reconstruct timeline anchors on the new root.
        top_links = self.cortex.get_adjacent_links(src_id, "sys:top")
        if top_links:
            self.cortex.put_link(new_id, top_links[0][0], "sys:top", author=author_id)
        bottom_links = self.cortex.get_adjacent_links(src_id, "sys:bottom")
        if bottom_links:
            self.cortex.put_link(new_id, bottom_links[0][0], "sys:bottom", author=author_id)

        # Restore session focus to the source cast (op_new moved it to the clone).
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, src_id)

        src_name = src_meta.get("name", src_id[:12])
        logger.info("[CastConcept] Cloned '%s' (%s) → '%s' (%s)",
                    src_name, src_id[:8], name, new_id[:8])
        return {
            "status": "cloned",
            "src_id": src_id,
            "cast_id": new_id,
            "name": name,
            "atoms_cloned": cloned_count,
            "message": f"Cast '{src_name}' cloned as '{name}' ({cloned_count} atoms).",
        }

    # ------------------------------------------------------------------
    # Identity / Physique / Social
    # ------------------------------------------------------------------

    def op_set_identity(
        self,
        text: str,
        source_id: str = "",
        evidence: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=text,
            atom_type="cast_identity",
            subset="identity",
            meta_extra={
                "role": "identity",
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="identity",
        )
        return {"status": "identity_set", "identity_id": key, "text": text}

    def op_set_appearance(
        self, vector: Dict[str, float], note: str = ""
    ) -> Dict[str, Any]:
        self._require_concept()
        if not isinstance(vector, dict):
            raise ValueError("appearance vector must be an object.")
        key = self._put_atom(
            content=note or f"appearance:{vector}",
            atom_type="cast_appearance",
            subset="appearance",
            meta_extra={"role": "appearance", "vector": vector},
            concept_word="appearance",
        )
        return {"status": "appearance_set", "appearance_id": key, "vector": vector}

    def op_set_ability(
        self, vector: Dict[str, float], note: str = ""
    ) -> Dict[str, Any]:
        self._require_concept()
        if not isinstance(vector, dict):
            raise ValueError("ability vector must be an object.")
        key = self._put_atom(
            content=note or f"ability:{vector}",
            atom_type="cast_ability",
            subset="ability",
            meta_extra={"role": "ability", "vector": vector},
            concept_word="ability",
        )
        return {"status": "ability_set", "ability_id": key, "vector": vector}

    def op_add_adornment(
        self,
        item: str,
        signal: Optional[List[str]] = None,
        intent: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=note or item,
            atom_type="cast_adornment",
            subset="adornments",
            meta_extra={
                "role": "adornment",
                "item": item,
                "signal": signal or [],
                "intent": intent,
            },
            concept_word="adornment",
        )
        return {"status": "adornment_added", "adornment_id": key, "item": item}

    def op_add_skill(
        self, name: str, level: float = 0.5, note: str = ""
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=note or name,
            atom_type="cast_skill",
            subset="skills",
            meta_extra={
                "role": "skill",
                "name": name,
                "level": self._clamp01(level, 0.5),
            },
            concept_word="skill",
        )
        return {
            "status": "skill_added",
            "skill_id": key,
            "name": name,
            "level": self._clamp01(level, 0.5),
        }

    def op_add_possession(
        self,
        item: str,
        attachment: float = 0.5,
        emotion: str = "",
        story_flag: bool = False,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=note or item,
            atom_type="cast_possession",
            subset="possessions",
            meta_extra={
                "role": "possession",
                "item": item,
                "attachment": self._clamp01(attachment, 0.5),
                "emotion": emotion,
                "story_flag": bool(story_flag),
            },
            concept_word="possession",
        )
        return {"status": "possession_added", "possession_id": key, "item": item}

    def op_set_social_position(
        self, position: Dict[str, Any], note: str = ""
    ) -> Dict[str, Any]:
        self._require_concept()
        if not isinstance(position, dict):
            raise ValueError("social_position must be an object.")
        key = self._put_atom(
            content=note or f"social_position:{position}",
            atom_type="cast_social_position",
            subset="social_positions",
            meta_extra={"role": "social_position", "position": position},
            concept_word="social_position",
        )
        return {
            "status": "social_position_set",
            "position_id": key,
            "position": position,
        }

    # ------------------------------------------------------------------
    # Behaviour-generating layers
    # ------------------------------------------------------------------

    def op_add_emotion(
        self,
        verb: str,
        obj: str,           # Bug 6 fix: renamed from 'object' (shadows Python built-in)
        intensity: float = 0.5,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        label = f"{verb}({obj})"
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or label,
            atom_type="cast_emotion",
            subset="emotions",
            meta_extra={
                "role": "emotion",
                "verb": verb,
                "object": obj,
                "label": label,
                "intensity": self._clamp01(intensity, 0.5),
            },
            concept_word="emotion",
        )
        # Bug 5 fix: link direction is root → emotion atom
        if verb in ("fear", "fears"):
            self.cortex.put_link(
                self.concept_id, key, "cast:fears", author=author_id
            )
        elif verb in ("love", "desire", "crave"):
            self.cortex.put_link(
                self.concept_id, key, "cast:desires", author=author_id
            )
        if self._clamp01(intensity, 0.5) >= 0.8:
            self.cortex.put_link(
                self.concept_id, key, "cast:obsesses_over", author=author_id
            )
        return {"status": "emotion_added", "emotion_id": key, "label": label}

    def op_add_wound(
        self,
        event: str,
        emotion: str = "",
        depth: float = 0.5,
        distortion: str = "",
        event_id: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if event_id:
            self._require_access(event_id, "Wound event")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=event,
            atom_type="cast_wound",
            subset="wounds",
            meta_extra={
                "role": "wound",
                "event": event,
                "event_id": event_id or None,
                "emotion": emotion,
                "depth": self._clamp01(depth, 0.5),
                "distortion": distortion,
            },
            concept_word="wound",
        )
        if event_id:
            self.cortex.put_link(key, event_id, "cast:wounded_by", author=author_id)
            self.cortex.put_link(
                self.concept_id, event_id, "cast:haunted_by", author=author_id
            )
        return {"status": "wound_added", "wound_id": key, "event": event}

    def op_add_policy(
        self,
        logic: str,
        emotional_root: str = "",
        pleasure_score: float = 0.5,
        depth: float = 0.5,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=note or logic,
            atom_type="cast_policy",
            subset="policies",
            meta_extra={
                "role": "policy",
                "logic": logic,
                "emotional_root": emotional_root,
                "pleasure_score": self._clamp01(pleasure_score, 0.5),
                "depth": self._clamp01(depth, 0.5),
            },
            concept_word="policy",
        )
        return {"status": "policy_added", "policy_id": key, "logic": logic}

    def op_add_rule(self, text: str, strength: float = 0.5) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=text,
            atom_type="cast_rule",
            subset="rules",
            meta_extra={"role": "rule", "strength": self._clamp01(strength, 0.5)},
            concept_word="rule",
        )
        return {"status": "rule_added", "rule_id": key, "text": text}

    def op_set_trait(
        self,
        trait: Optional[Dict[str, float]] = None,
        key: str = "",
        value: Any = None,
    ) -> Dict[str, Any]:
        self._require_concept()
        # Merge with current vector so partial updates are safe
        vector = self._current_trait_vector()
        updates = trait or {}
        if key:
            updates[key] = self._clamp01(value, 0.5)
        vector.update({k: self._clamp01(v, 0.5) for k, v in updates.items()})

        threshold = {
            "reaction": self._reaction_threshold(vector.get("response", 0.5)),
            "accumulation_decay": round(vector["flexibility"], 4),
            "trust_gate": round(vector["trust"], 4),
        }

        trait_id = self._put_atom(
            content=f"trait:{vector}",
            atom_type="cast_trait",
            subset="traits",
            meta_extra={"role": "trait", "vector": vector},
            concept_word="trait",
        )
        threshold_id = self._put_atom(
            content=f"threshold:{threshold}",
            atom_type="cast_threshold",
            subset="thresholds",
            meta_extra={
                "role": "threshold",
                "derived_from": trait_id,
                "threshold": threshold,
            },
            concept_word="threshold",
        )
        return {
            "status": "trait_set",
            "trait_id": trait_id,
            "threshold_id": threshold_id,
            "trait": vector,
            "threshold": threshold,
        }

    @staticmethod
    def _reaction_threshold(response: float) -> float:
        """
        Bug 4 fix: cap at 0.9 so that a maximum-intensity event always
        exceeds the threshold regardless of how cautious the entity is.
        Cautious (response→1.0) → threshold→0.9
        Impulsive (response→0.0) → threshold→0.55
        """
        raw = 1.0 - (1.0 - float(response)) * 0.45
        return round(min(0.9, raw), 4)

    def op_set_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self._require_concept()
        if not isinstance(state, dict):
            raise ValueError("state must be an object.")
        key = self._put_atom(
            content=f"state:{state}",
            atom_type="cast_state",
            subset="states",
            meta_extra={"role": "state", "state": state},
            concept_word="state",
        )
        return {"status": "state_set", "state_id": key, "state": state}

    # ------------------------------------------------------------------
    # Surface layers
    # ------------------------------------------------------------------

    def op_add_mask(
        self, presentation: str, hides: str = "", audience: str = "public"
    ) -> Dict[str, Any]:
        self._require_concept()
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=presentation,
            atom_type="cast_mask",
            subset="masks",
            meta_extra={
                "role": "mask",
                "presentation": presentation,
                "hides": hides,
                "audience": audience,
            },
            concept_word="mask",
        )
        self.cortex.put_link(self.concept_id, key, "cast:presents_as", author=author_id)
        if hides:
            self.cortex.put_link(key, self.concept_id, "cast:hides", author=author_id)
        return {"status": "mask_added", "mask_id": key}

    def op_add_secret(
        self,
        content: str,
        protection: float = 0.8,
        shared_with: Optional[List[str]] = None,
        revealed_by: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        author_id, _ = self._author_and_scopes()
        for target in self._as_list(shared_with):
            self._require_access(target, "Shared-with cast")
        key = self._put_atom(
            content=content,
            atom_type="cast_secret",
            subset="secrets",
            meta_extra={
                "role": "secret",
                "protection": self._clamp01(protection, 0.8),
                "shared_with": shared_with or [],
                "revealed_by": revealed_by,
            },
            concept_word="secret",
        )
        self.cortex.put_link(self.concept_id, key, "cast:secret", author=author_id)
        for target in self._as_list(shared_with):
            self.cortex.put_link(key, target, "cast:shared_with", author=author_id)
        return {"status": "secret_added", "secret_id": key}

    def op_add_output(
        self,
        modality: str,
        content: str,
        valence: float = 0.0,
        leakage: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=content,
            atom_type="cast_output",
            subset="outputs",
            meta_extra={
                "role": "output",
                "modality": modality,
                "valence": float(valence),
                "leakage": leakage,
            },
            concept_word="output",
        )
        return {"status": "output_added", "output_id": key}

    # ------------------------------------------------------------------
    # Contradiction / Shadow
    # ------------------------------------------------------------------

    def op_add_contradiction(
        self, a: str, b: str, tension: float = 0.5, result: str = ""
    ) -> Dict[str, Any]:
        self._require_concept()
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=result or f"{a} conflicts with {b}",
            atom_type="cast_contradiction",
            subset="contradictions",
            meta_extra={
                "role": "contradiction",
                "a": a,
                "b": b,
                "tension": self._clamp01(tension, 0.5),
                "result": result,
            },
            concept_word="contradiction",
        )
        self.cortex.put_link(
            self.concept_id, key, "cast:conflicts_with", author=author_id
        )
        return {"status": "contradiction_added", "contradiction_id": key}

    def op_add_shadow(
        self,
        kind: str,
        content: str,
        trigger: str = "",
        source_wound_id: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if kind not in ("suppressed", "projected", "disowned"):
            raise ValueError("kind must be suppressed, projected, or disowned.")
        if source_wound_id:
            self._require_access(source_wound_id, "Source wound")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=content,
            atom_type="cast_shadow",
            subset="shadows",
            meta_extra={
                "role": "shadow",
                "kind": kind,
                "trigger": trigger,
                "source_wound_id": source_wound_id or None,
            },
            concept_word="shadow",
        )
        if source_wound_id:
            self.cortex.put_link(key, source_wound_id, "cast:formed_by", author=author_id)
        return {"status": "shadow_added", "shadow_id": key}

    # ------------------------------------------------------------------
    # Bonds
    # ------------------------------------------------------------------

    def op_add_bond(
        self,
        target_id: str,
        types: Optional[List[str]] = None,
        direction: str = "directed",
        trust: float = 0.5,
        power: float = 0.0,
        affect: float = 0.0,
        visible: bool = True,
        dependency: str = "",
        history: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(target_id, "Target cast")
        for event_id in self._as_list(history):
            self._require_access(event_id, "Bond history event")
        author_id, _ = self._author_and_scopes()
        bond_types = types or ["relationship"]
        key = self._put_atom(
            content=note or f"bond:{bond_types}->{target_id[:12]}",
            atom_type="cast_bond",
            subset="bonds",
            meta_extra={
                "role": "bond",
                "target_id": target_id,
                "types": bond_types,
                "direction": direction,
                "trust": self._clamp01(trust, 0.5),
                "power": float(power),
                "affect": float(affect),
                "visible": bool(visible),
                "dependency": dependency,
                "history": history or [],
            },
            concept_word="bond",
        )
        self.cortex.put_link(self.concept_id, target_id, "cast:bond", author=author_id)
        self.cortex.put_link(key, target_id, "cast:refers_to", author=author_id)
        if "love" in bond_types:
            self.cortex.put_link(
                self.concept_id, target_id, "cast:love", author=author_id
            )
        if "rivalry" in bond_types:
            self.cortex.put_link(
                self.concept_id, target_id, "cast:rivalry", author=author_id
            )
        if "envy" in bond_types:
            self.cortex.put_link(
                self.concept_id, target_id, "cast:envy", author=author_id
            )
        if self._clamp01(trust, 0.5) >= 0.7:
            self.cortex.put_link(
                self.concept_id, target_id, "cast:trust", author=author_id
            )
        if dependency:
            self.cortex.put_link(
                self.concept_id, target_id, "cast:dependency", author=author_id
            )
        return {"status": "bond_added", "bond_id": key, "target_id": target_id}

    def op_update_bond(
        self,
        bond_id: str,
        delta: Dict[str, Any],
        event_id: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(bond_id, "Bond")
        if event_id:
            self._require_access(event_id, "Bond update event")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"bond_update:{delta}",
            atom_type="cast_bond_update",
            subset="bond_updates",
            meta_extra={
                "role": "bond_update",
                "bond_id": bond_id,
                "event_id": event_id or None,
                "delta": delta,
            },
            concept_word="bond_update",
        )
        self.cortex.put_link(bond_id, key, "cast:updated_by", author=author_id)
        if event_id:
            self.cortex.put_link(key, event_id, "cast:formed_by", author=author_id)
        return {"status": "bond_updated", "bond_update_id": key, "bond_id": bond_id}

    # ------------------------------------------------------------------
    # Destiny / Arc
    # ------------------------------------------------------------------

    def op_set_fate(
        self, event: str, certainty: float = 0.5, awareness: bool = False
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=event,
            atom_type="cast_fate",
            subset="fates",
            meta_extra={
                "role": "fate",
                "event": event,
                "certainty": self._clamp01(certainty, 0.5),
                "awareness": bool(awareness),
            },
            concept_word="fate",
        )
        return {"status": "fate_set", "fate_id": key}

    def op_set_calling(
        self, mission: str, discovered: bool = False, alignment: float = 0.0
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=mission,
            atom_type="cast_calling",
            subset="callings",
            meta_extra={
                "role": "calling",
                "mission": mission,
                "discovered": bool(discovered),
                "alignment": self._clamp01(alignment, 0.0),
            },
            concept_word="calling",
        )
        return {"status": "calling_set", "calling_id": key}

    def op_set_role(
        self,
        role: str,
        perspective: str = "",
        source_ontology: str = "d_propp_roles.ak",
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=role,
            atom_type="cast_role",
            subset="roles",
            meta_extra={
                "role": "destiny_role",
                "destiny_role": role,
                "perspective": perspective,
                "source_ontology": source_ontology,
            },
            concept_word="role",
        )
        return {"status": "role_set", "role_id": key, "role": role}

    def op_set_myth(
        self, archetype: str, symbol: str = "", resonance: float = 0.5
    ) -> Dict[str, Any]:
        self._require_concept()
        key = self._put_atom(
            content=f"{archetype}:{symbol}",
            atom_type="cast_myth",
            subset="myths",
            meta_extra={
                "role": "myth",
                "archetype": archetype,
                "symbol": symbol,
                "resonance": self._clamp01(resonance, 0.5),
            },
            concept_word="myth",
        )
        return {"status": "myth_set", "myth_id": key}

    def op_add_arc(
        self,
        arc_type: str,
        initial_state: str,
        conflict_state: str,
        transformed_state: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        valid_types = ("growth", "fall", "flat", "corruption", "healing")
        if arc_type not in valid_types:
            raise ValueError(f"arc_type must be one of {valid_types}.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"arc:{arc_type}",
            atom_type="cast_arc",
            subset="arcs",
            meta_extra={
                "role": "arc",
                "arc_type": arc_type,
                "initial_state": initial_state,
                "conflict_state": conflict_state,
                "transformed_state": transformed_state,
            },
            concept_word="arc",
        )
        self.cortex.put_link(
            self.concept_id, key, "cast:fractures_into", author=author_id
        )
        if transformed_state:
            self.cortex.put_link(
                key, self.concept_id, "cast:resolves_into", author=author_id
            )
        return {"status": "arc_added", "arc_id": key, "arc_type": arc_type}

    # ------------------------------------------------------------------
    # Analysis operators
    # ------------------------------------------------------------------

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        return {
            "cast_id": self.concept_id,
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_diagnose(self) -> Dict[str, Any]:
        self._require_concept()
        contradictions = [self._summary(k) for k in self._members("contradictions")]
        wounds        = [self._summary(k) for k in self._members("wounds")]
        policies      = [self._summary(k) for k in self._members("policies")]
        masks         = [self._summary(k) for k in self._members("masks")]
        secrets       = [self._summary(k) for k in self._members("secrets")]
        bonds         = [self._summary(k) for k in self._members("bonds")]
        callings      = [self._summary(k) for k in self._members("callings")]

        pressure = 0.0
        for c in contradictions:
            pressure += float(c["meta"].get("tension", 0.0))
        for w in wounds:
            pressure += float(w["meta"].get("depth", 0.0)) * 0.7
        for s in secrets:
            pressure += float(s["meta"].get("protection", 0.0)) * 0.3

        low_alignment_callings = [
            c for c in callings
            if float(c["meta"].get("alignment", 0.0)) < 0.3
            and not c["meta"].get("discovered", False)
        ]

        trait_vector = self._current_trait_vector()
        wound_trust_distortion = any(
            float(w["meta"].get("depth", 0.0)) > 0.6
            for w in wounds
        ) and trait_vector.get("trust", 0.5) < 0.4

        return {
            "cast_id": self.concept_id,
            "pressure_score": round(pressure, 4),
            "contradictions": contradictions,
            "wounds": wounds,
            "policies": policies,
            "masks": masks,
            "secrets": secrets,
            "bonds": bonds,
            "diagnosis": {
                "high_tension":           pressure >= 2.0,
                "arc_ready":              bool(contradictions and wounds),
                "calling_unresolved":     bool(low_alignment_callings),
                "wound_trust_distortion": wound_trust_distortion,
                "secret_pressure":        len(secrets),
                "relationship_pressure":  len(bonds),
            },
        }

    def op_react(
        self,
        event: Optional[Dict[str, Any]] = None,
        event_id: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        event_data = event or {}
        event_content = ""
        if event_id:
            self._require_access(event_id, "Event")
            event_data    = self._meta(event_id)
            event_content = self._content(event_id)

        intensity    = self._clamp01(event_data.get("intensity", 0.5), 0.5)
        frequency    = float(event_data.get("frequency", 1.0))
        accumulation = self._clamp01(event_data.get("accumulation", 0.0), 0.0)
        event_force  = min(1.0, intensity * max(1.0, frequency) + accumulation * 0.5)

        trait_vector = self._current_trait_vector()

        # Bug 4 fix: use capped threshold
        reaction_threshold = self._reaction_threshold(trait_vector.get("response", 0.5))
        threshold_exceeded = event_force >= reaction_threshold

        emotions       = [self._summary(k) for k in self._members("emotions")]
        policies       = [self._summary(k) for k in self._members("policies")]
        contradictions = [self._summary(k) for k in self._members("contradictions")]
        masks          = [self._summary(k) for k in self._members("masks")]

        triggered_emotions = []
        for s in emotions:
            m = s["meta"]
            if float(m.get("intensity", 0.0)) + event_force >= 1.1:
                triggered_emotions.append(m.get("label") or s["content"])

        activated_policies = []
        for s in policies:
            m = s["meta"]
            if float(m.get("depth", 0.0)) + event_force >= 1.0:
                activated_policies.append(m.get("logic") or s["content"])

        triggered_contradictions = []
        for s in contradictions:
            m = s["meta"]
            if float(m.get("tension", 0.0)) + event_force >= 1.0:
                triggered_contradictions.append(f"{m.get('a')} vs {m.get('b')}")

        process_filter = float(trait_vector.get("process", 0.5))
        trust_filter   = float(trait_vector.get("trust", 0.5))

        if threshold_exceeded:
            perceived_result = "Threshold exceeded: direct reaction before interpretation"
        elif process_filter >= 0.7:
            perceived_result = "Perceived as a logical threat"
        elif trust_filter <= 0.3:
            perceived_result = "Perceived as hostility or hidden motive"
        else:
            perceived_result = "Perceived as an emotional event"

        valence  = -0.2 if (triggered_contradictions or threshold_exceeded) else 0.1
        leakage  = "current_emotion leaks subtly into voice.tone" \
                   if (masks and triggered_emotions) else ""

        # NOTE: output.content will in future be generated from current_emotion
        # in a_emotions_27.ak. Currently a placeholder (Phase 2 implementation planned).
        output_content = (
            "This should be handled logically" if process_filter >= 0.7 else "It is time to act"
        )

        return {
            "entity":        self._meta(self.concept_id).get("name", self.concept_id),
            "cast_id":       self.concept_id,
            "event_id":      event_id or None,
            "event_content": event_content,
            "event": {
                "intensity":    intensity,
                "frequency":    frequency,
                "accumulation": accumulation,
                "force":        round(event_force, 4),
            },
            "threshold":           reaction_threshold,
            "threshold_exceeded":  threshold_exceeded,
            "perceived_event": {
                "process_filter": process_filter,
                "trust_filter":   trust_filter,
                "result":         perceived_result,
            },
            "contradiction_triggered": triggered_contradictions,
            "emotion_triggered":       triggered_emotions,
            "policy_activated":        activated_policies,
            "mask_engaged":            bool(masks),
            "output": {
                "modality": "voice",
                "valence":  valence,
                "content":  output_content,
                "leakage":  leakage,
            },
            "arc_delta": {
                "trait.response":  0.01 if threshold_exceeded else 0.0,
                "accumulation":    round(accumulation + intensity * 0.1, 4),
            },
        }
