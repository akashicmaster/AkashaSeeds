"""
Base Concept and Primitive Chunk Mechanics Module.
Implements the core BaseConcept class under the "Operand-First" philosophy.
Exposes hardware-accelerated set operations, transactional undo/redo, and the
highly critical, primitive "Structured Chunk" generator.

[CRITICAL FIX: STAGED COMMIT KEY RE-MAPPING]
When committing staged mutations, the text content may have changed, resulting 
in a completely new cryptographic hash from put_chunk. 
The commit_staged method now explicitly maps the old staged key to the actual 
materialized key, guaranteeing that concept registration and topology links 
never suffer from orphaned references.
"""

import json
import logging
import hashlib
import time
import re
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("Harmonia.Concept")

class BaseConcept:
    """
    The mathematical blueprint for all Akasha Concept Models.
    Provides universal set packaging, staging transaction controls, and the
    primitive structural Chunk-level subset generator.
    """

    # Subclasses that support session focus set this to the session context key
    # used to track the active instance (e.g. "active_cast_root").
    # SpaceConcept reads this to manage cross-model focus without hard-coding
    # model-specific key names.
    CONTEXT_KEY_ACTIVE: Optional[str] = None

    # One-line description shown in 'help -c' listings.
    # Set this in subclasses to auto-populate CommandRouter.CONCEPT_LABELS.
    CONCEPT_LABEL: str = ""

    def __init__(self, session, concept_id: Optional[str] = None, namespace: Optional[str] = None):
        self.session = session
        self.namespace = namespace
        self._ns = f"{namespace}:" if namespace else ""
        self.cortex = getattr(session, 'cortex', getattr(session, 'local_cortex', None))
        if not self.cortex:
            raise RuntimeError("Cortex (AkashaEngine) is unavailable in the current session.")

        self.concept_id = concept_id
        self.set_name = f"set:concept:{self.concept_id}" if self.concept_id else None

        # Staging area for atomic editing history (Undo/Redo mechanics)
        self.staged_changes: Dict[str, Dict[str, Any]] = {}
        self.staged_links: List[Tuple[str, str, str, float]] = []
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []

    @property
    def allowed_scopes(self) -> List[str]:
        """Retrieves active security and language scopes from the running session."""
        return getattr(self.session, 'active_scopes', [])

    def _require_concept(self):
        """
        Guard: raises RuntimeError if no concept_id is mounted.
        Call at the top of every op_* method that requires an initialized concept.
        """
        if not self.concept_id:
            raise RuntimeError(
                f"No active concept in {self.__class__.__name__}. Call op_new first."
            )

    def _ctx_key(self, key: str) -> str:
        """Return the namespace-prefixed session context key."""
        return f"{self._ns}{key}"

    # ── Shared session-mount helpers ──────────────────────────────────────────

    def _active_key(self, ctx: str) -> Optional[str]:
        """Return the atom key stored in session context under `ctx`, or None."""
        return self.session.get_context(ctx)

    def _require_active(self, ctx: str, label: str = "instance") -> str:
        """Return the atom key stored under `ctx`, or raise if not set."""
        key = self.session.get_context(ctx)
        if not key:
            raise RuntimeError(
                f"No active {label}. Open or create one first."
            )
        return key

    def _write(self, fn):
        """Execute a write closure (hook point for future serialisation layers)."""
        return fn()

    def _read(self, fn):
        """Execute a read closure."""
        return fn()

    def dispatch(self, operator: str, params: Dict[str, Any]) -> Any:
        """Dynamically dispatches string commands to operator handlers."""
        clean_op = operator.replace('.', '_')
        handler_name = f"op_{clean_op}"
        if hasattr(self, handler_name):
            return getattr(self, handler_name)(**params)
        raise NotImplementedError(f"Operator '{operator}' not supported by {self.__class__.__name__}.")

    def register_concept_node(self, key: str, subset_suffix: Optional[str] = None):
        """Registers a node to the concept's main Set and optional sub-sets."""
        if not self.set_name:
            raise RuntimeError("Concept instance must be initialized with a root ID.")
        self.cortex.add_to_set(self.set_name, key)
        if subset_suffix:
            self.cortex.add_to_set(f"{self.set_name}:{subset_suffix}", key)
        # Universal readability hook: the catalog set exists now (add_to_set auto-creates it),
        # so give it a human-readable alias. Idempotent + collision-safe; covers models that
        # build the set implicitly (via add_to_set) rather than an explicit ensure_concept_set().
        self.alias_concept_set()

    def alias_concept_set(self, name: Optional[str] = None) -> Optional[str]:
        """Give this concept's catalog set (`set:concept:<hash>`) a human-readable alias.

        **Human readability is the concept model's first priority.** When a client warps to a
        concept the focus is this hash-keyed set, whose only "name" is the hash — so the Cosmos
        FOCAL LOCK / wake / node labels / hover read as `set:concept:a48c51e1…` unless the
        front-end guesses from content. Registering `concept:<slug(name)>` on the set key makes
        every surface resolve to a real alias without guessing.

        When `name` is omitted it is derived from the concept root's meta (`name` / `title`) or,
        failing that, its content head (stripping decoration like `[ Survey: Foo ]` → `Foo`), so
        callers usually need no argument.

        Collision-safe (first-wins — never steals an alias already bound to another key) and
        side-effect-free: it writes a raw alias row via `core.put_alias`, deliberately NOT the
        `set_alias` proto-word / collection-derivation machinery (a set is not an atom). Returns
        the alias registered, or None. Idempotent — safe to call on every open/new."""
        if not self.set_name:
            return None
        if not name and self.concept_id:
            try:
                meta = self.cortex.get_meta(self.concept_id) or {}
            except Exception:
                meta = {}
            name = meta.get("name") or meta.get("title")
            if not name:
                content = self.cortex.get_chunk(self.concept_id) or ""
                m = re.search(r"\[\s*[^:\]]+:\s*(.+?)\s*\]", content)   # "[ Survey: Foo ]" → Foo
                name = (m.group(1) if m else content).strip().split("\n", 1)[0]
        if not name:
            return None
        core = getattr(self.cortex, "core", None)
        if core is None:
            return None
        slug = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
        if not slug:
            return None
        alias = f"concept:{slug}"
        try:
            existing = core.get_key_by_alias(alias)
            if existing and existing != self.set_name:
                return None                      # first-wins: leave the incumbent alone
            core.put_alias(self.set_name, alias)
            return alias
        except Exception:
            return None

    def ensure_concept_set(self) -> None:
        """Create this concept's catalog set AND give it a human-readable alias in one step —
        a drop-in replacement for `self.cortex.create_set(self.set_name)` in a model's op_new,
        so readability is applied uniformly at creation (human readability is the concept
        model's first priority). The root atom must already exist (alias derives from its meta)."""
        if self.set_name:
            self.cortex.create_set(self.set_name)
            self.alias_concept_set()

    # =========================================================================
    # 🧬 PRIMITIVE CORE: STRUCTURAL CHUNK GENERATOR (Universal Operand)
    # =========================================================================
    def create_structured_chunk(self, content: str, role: str, 
                                author_id: str, scopes: List[str], 
                                parent_set_id: Optional[str] = None) -> Dict[str, Any]:
        """
        [PRIMITIVE MECHANIC]
        Materializes a raw text string as a structured Chunk. 
        Auto-generates tokens, offsets, and thesaurus bridges autonomously via the Composite Layer.
        """
        chunk_meta = {
            "role": role,
            "created_at": time.time(),
            "type": "primitive:chunk"
        }
        
        # Immediate physical write. The backend (Weaver) handles NLP tokenization asynchronously.
        chunk_id = self.cortex.put_chunk(
            content=content,
            meta=chunk_meta,
            author=author_id,
            scopes=scopes
        )
        
        # Register to main set if a concept is active
        if self.set_name:
            self.register_concept_node(chunk_id)
            if parent_set_id:
                self.cortex.add_to_set(parent_set_id, chunk_id)

        # Create a localized private subset (Set) specifically for this chunk's inner elements
        chunk_subset_name = f"set:chunk:{chunk_id}"
        self.cortex.create_set(chunk_subset_name)
        self.cortex.add_to_set(chunk_subset_name, chunk_id)

        return {
            "chunk_id": chunk_id,
            "chunk_set": chunk_subset_name
        }

    # =========================================================================
    # 🧬 SUB-ATOM GRANULAR SPAN ANNOTATIONS
    # =========================================================================
    def annotate_span(self, parent_chunk_key: str, start_char: int, end_char: int, 
                      annotation_text: str, role: str = "annotation", 
                      target_concept_id: Optional[str] = None) -> str:
        """
        Creates a granular sub-atom annotation mapped directly to a character offset
        within a physical Chunk. Encapsulates it inside the Chunk's private subset.
        """
        author_id = getattr(self.session, 'client_id', "system")
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

        annot_meta = {
            "role": role,
            "span_start": start_char,
            "span_end": end_char,
            "parent_ref": parent_chunk_key,
            "created_at": time.time(),
            "offset_mapping": {
                "start": start_char,
                "end": end_char,
                "author": author_id
            }
        }
        
        annot_key = self.cortex.put_chunk(
            content=annotation_text,
            meta=annot_meta,
            author=author_id,
            scopes=user_scopes
        )

        # Register in Concept Package and local Chunk Set
        chunk_subset_name = f"set:chunk:{parent_chunk_key}"
        self.cortex.add_to_set(chunk_subset_name, annot_key)
        if self.set_name:
            self.register_concept_node(annot_key, subset_suffix="annotations")

        # Establish coordinate mapping link (Chunk -> Annotation)
        self.cortex.put_link(parent_chunk_key, annot_key, "sys:has_annotation_span", author=author_id)
        self.cortex.put_link(parent_chunk_key, annot_key, "sys:included", author=author_id)

        if target_concept_id:
            self.cortex.put_link(annot_key, target_concept_id, "sys:associated_with", author="system")

        return annot_key

    def get_span_annotations(self, parent_chunk_key: str) -> List[Dict[str, Any]]:
        """Retrieves and sorts all active span annotations bound to this parent Chunk."""
        links = self.cortex.get_adjacent_links(parent_chunk_key, "sys:has_annotation_span")
        annotations = []
        scopes = self.allowed_scopes
        
        for dst, _ in links:
            if scopes and not self.cortex.check_access(dst, scopes):
                continue
                
            content = self.cortex.get_chunk(dst)
            meta = self.cortex.get_meta(dst)
            mapping = meta.get("offset_mapping", {})
            
            annotations.append({
                "annotation_id": dst,
                "text": content,
                "role": meta.get("role", "annotation"),
                "start": mapping.get("start"),
                "end": mapping.get("end"),
                "author": mapping.get("author")
            })
            
        return sorted(annotations, key=lambda x: x.get("start", 0))

    # =========================================================================
    # 🛡️ TRANSACTIONAL STAGING & AUTOMATIC UNDO / REDO
    # =========================================================================
    def stage_change(self, key: str, content: str, meta: Dict[str, Any], action_type: str = "update"):
        """Stages a node modification to local cache prior to committing."""
        original_node = self.cortex.core.get_chunk_raw(key)
        self.undo_stack.append({
            "type": "node_mutation",
            "key": key,
            "content": original_node["content"] if original_node else None,
            "meta": json.loads(original_node["meta"]) if original_node and original_node["meta"] else {},
            "action_type": "delete" if not original_node else "update"
        })
        self.redo_stack.clear()
        self.staged_changes[key] = {"content": content, "meta": meta, "action_type": action_type}

    def stage_link(self, src: str, dst: str, rel: str, w: float = 1.0):
        """Stages a new relational linkage to local cache."""
        self.undo_stack.append({"type": "link_creation", "src": src, "dst": dst, "rel": rel, "w": w})
        self.redo_stack.clear()
        self.staged_links.append((src, dst, rel, w))

    def undo(self) -> Optional[Dict[str, Any]]:
        """Reverts the last staged action on the undo stack."""
        if not self.undo_stack:
            return None
        last_action = self.undo_stack.pop()
        self.redo_stack.append(last_action)
        
        if last_action["type"] == "node_mutation":
            target_key = last_action["key"]
            if last_action["content"] is None:
                self.staged_changes.pop(target_key, None)
            else:
                self.staged_changes[target_key] = {
                    "content": last_action["content"],
                    "meta": last_action["meta"],
                    "action_type": "update"
                }
            return {"status": "undone", "type": "node", "key": target_key}
            
        elif last_action["type"] == "link_creation":
            link_tuple = (last_action["src"], last_action["dst"], last_action["rel"], last_action["w"])
            if link_tuple in self.staged_links:
                self.staged_links.remove(link_tuple)
            return {"status": "undone", "type": "link", "details": last_action}
        return None

    def redo(self) -> Optional[Dict[str, Any]]:
        """Re-applies the last undone action on the redo stack."""
        if not self.redo_stack:
            return None
        next_action = self.redo_stack.pop()
        self.undo_stack.append(next_action)
        
        if next_action["type"] == "node_mutation":
            target_key = next_action["key"]
            self.staged_changes[target_key] = {
                "content": next_action["content"],
                "meta": next_action["meta"],
                "action_type": next_action["action_type"]
            }
            return {"status": "redone", "type": "node", "key": target_key}
            
        elif next_action["type"] == "link_creation":
            self.staged_links.append((next_action["src"], next_action["dst"], next_action["rel"], next_action["w"]))
            return {"status": "redone", "type": "link", "details": next_action}
        return None

    def commit_staged(self) -> Dict[str, Any]:
        """
        [CRITICAL FIX APPLIED]
        Flushes all staged changes permanently into the Cortex.
        Safely bridges the old staged hashes to the new generated hashes to prevent
        graph topology corruption or orphaned nodes.

        BOUNDARY NOTE: Staging is per-concept in-process state. It is NOT a
        Harmonia workspace transaction. If this concept is used inside a JCL job
        and the job rolls back, staged commits that already reached the Cortex
        will NOT be reversed. Stage only within a single JCL step, or call
        commit_staged before the Harmonia rollback boundary.
        """
        author_id = getattr(self.session, 'client_id', "system")
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        
        committed_nodes = []
        committed_links = 0
        
        # Translation map: { "old_staged_key": "new_materialized_key" }
        key_translation_map = {}
        
        # 1. Materialize all nodes first and capture their actual new cryptographic keys
        for old_key, details in self.staged_changes.items():
            if details["action_type"] == "delete":
                # Handle deletions gracefully
                session_scopes = getattr(self.session, 'active_scopes', None)
                self.cortex.drop_chunk(old_key, requester_scopes=session_scopes)
                continue
                
            actual_new_key = self.cortex.put_chunk(
                content=details["content"],
                meta=details["meta"],
                author=author_id,
                scopes=user_scopes
            )
            
            # Map the old key to the new reality
            if actual_new_key != old_key:
                key_translation_map[old_key] = actual_new_key
                
            # Register the ACTUAL new key to the concept set
            self.register_concept_node(actual_new_key)
            committed_nodes.append(actual_new_key)
            
        # 2. Re-wire all staged links using the translation map
        for src, dst, rel, w in self.staged_links:
            # Resolve to new key if it mutated during this commit, otherwise keep original
            resolved_src = key_translation_map.get(src, src)
            resolved_dst = key_translation_map.get(dst, dst)
            
            self.cortex.put_link(resolved_src, resolved_dst, rel, w=w, author=author_id)
            committed_links += 1
            
        self.staged_changes.clear()
        self.staged_links.clear()
        
        return {
            "status": "committed", 
            "nodes_written": len(committed_nodes), 
            "links_woven": committed_links,
            "mutations": len(key_translation_map)
        }

    # =========================================================================
    # 📦 STANDARDIZED OBJECT SERIALIZATION (SAVE / LOAD)
    # =========================================================================
    def serialize_concept(self) -> Dict[str, Any]:
        """Serializes the complete concept universe into a standardized JSON representation."""
        if not self.concept_id:
            return {}
        allowed_scopes = self.allowed_scopes
        member_keys = self.cortex.get_collection_members(self.set_name)
        visible_keys = [k for k in member_keys if self.cortex.check_access(k, allowed_scopes)]
        
        export_atoms = {}
        export_links = []
        
        for k in visible_keys:
            export_atoms[k] = {
                "content": self.cortex.get_chunk(k),
                "meta": self.cortex.get_meta(k)
            }
            adjacents = self.cortex.get_adjacent_links(k)
            for dst, rel in adjacents:
                if dst in visible_keys or dst.startswith("scope:") or dst.startswith("emo:"):
                    export_links.append({
                        "src": k, "dst": dst, "rel": rel, "w": 1.0
                    })
                    
        return {
            "specification": "akasha_concept_schema_v1.0",
            "concept_type": self.__class__.__name__,
            "concept_id": self.concept_id,
            "atoms": export_atoms,
            "links": export_links
        }

    def hydrate_concept(self, schema_data: Dict[str, Any]) -> str:
        """Hydrates and materializes a concept object from an exported schema."""
        author_id = getattr(self.session, 'client_id', "system")
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        
        self.concept_id = schema_data.get("concept_id")
        self.set_name = f"set:concept:{self.concept_id}"
        self.cortex.create_set(self.set_name)
        
        atoms = schema_data.get("atoms", {})
        
        # Translation map for importing across different systems
        hydration_map = {}
        
        for old_key, val in atoms.items():
            new_key = self.cortex.put_chunk(content=val["content"], meta=val["meta"], author=author_id, scopes=user_scopes)
            hydration_map[old_key] = new_key
            self.register_concept_node(new_key)
            
        links = schema_data.get("links", [])
        for link in links:
            safe_src = hydration_map.get(link["src"], link["src"])
            safe_dst = hydration_map.get(link["dst"], link["dst"])
            self.cortex.put_link(src=safe_src, dst=safe_dst, rel=link["rel"], w=link.get("w", 1.0), author=author_id)
            
        return self.concept_id

    # =========================================================================
    # 🌐 FORMAT IMPORT / EXPORT ENTRYPOINTS
    # =========================================================================
    def export_concept(self, format_type: str, **kwargs) -> Any:
        """Exports the current concept to an external format (markdown, pdf, csv)."""
        internal_schema = self.serialize_concept()
        if not internal_schema:
            raise ValueError(f"Concept '{self.concept_id}' has no data.")

        plugin_name = f"transform.export.{format_type.lower()}"
        transformer = getattr(self.cortex, '_plugins', {}).get(plugin_name)
        if not transformer:
            if format_type.lower() == "json":
                return json.dumps(internal_schema, ensure_ascii=False, indent=2)
            raise NotImplementedError(f"Export format plugin '{plugin_name}' not registered.")
            
        try:
            return transformer(internal_schema, **kwargs)
        except Exception as e:
            logger.error(f"Failed to export concept to {format_type}: {e}")
            raise RuntimeError(f"Transform failed: {str(e)}")

    def import_concept(self, raw_data: Any, format_type: str, **kwargs) -> str:
        """Transforms external documents into a standard concept graph schema."""
        plugin_name = f"transform.import.{format_type.lower()}"
        parser = getattr(self.cortex, '_plugins', {}).get(plugin_name)
        if not parser:
            if format_type.lower() == "json":
                parsed_schema = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                return self.hydrate_concept(parsed_schema)
            raise NotImplementedError(f"Import parser plugin '{plugin_name}' not registered.")

        try:
            standard_schema = parser(raw_data, **kwargs)
        except Exception as e:
            logger.error(f"Failed to import format {format_type}: {e}")
            raise ValueError(f"Failed to parse: {str(e)}")
        return self.hydrate_concept(standard_schema)
