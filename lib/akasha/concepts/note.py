"""
Hierarchical and Relational Note Concept Module (Pro Edition).

[OPERAND-FIRST DESIGN]
Implements the Cognitive Document Concept using a dual-topology architecture:
1. Horizontal Timeline: Every structural element (Chapter, Section, Paragraph, Chunk)
   is fundamentally a node in an absolute sequential timeline (`top` -> `next` -> `bottom`).
2. Vertical Sets: Nodes are simultaneously packaged into nested sets via `sys:contains`,
   allowing hierarchical TOC traversal while maintaining flat readability.

[ZERO-OVERHEAD METABOLISM]
Relies entirely on the BaseConcept and the underlying Cortex to trigger 
asynchronous Cognitive Weaving (NLP + Thesaurus Gate). This class focuses 
exclusively on constructing the beautiful mathematical topology of a Book.
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Note")

# Alias prefix for general concept-word atoms shared across concept models.
# One atom per structural role word (e.g. "section", "paragraph", "chunk").
# These live in the user's scope and are linked one-directionally from note
# content atoms — note atoms are derived from them, not equal to them.
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

class NoteConcept(BaseConcept):
    """
    Cognitive Document Model.
    Bridges the gap between qualitative research and structural graph databases.
    """

    CONCEPT_METHODS = {
        "list":    {"op": "op_list_chunks"},
        "edit":    {"op": "op_edit_chunk",
                    "coerce": lambda d: {"chunk_id": d.get("chunk_id") or d.get("id", ""),
                                         "text": d.get("text", "")}},
        "move":    {"op": "op_move_chunk",
                    "coerce": lambda d: {"chunk_id": d.get("chunk_id") or d.get("id", ""),
                                         "after": d.get("after")}},
        "undo":    {"op": "op_undo_edit"},
        "redo":    {"op": "op_redo_edit"},
        "restore": {"op": "op_restore_original"},
        "rename":  {"op": "op_rename"},
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None, namespace: Optional[str] = None):
        super().__init__(session, concept_id, namespace=namespace)

        # If no explicit concept_id is provided, attempt to mount the active note from the session
        if not self.concept_id:
            active_root = getattr(self.session, "get_context", lambda k: None)(self._ctx_key("active_note_root"))
            if active_root:
                self.concept_id = active_root
                self.set_name = f"set:concept:{self.concept_id}"

    def _get_set_name(self, suffix: str = "") -> str:
        """Generates the absolute namespace for this Note's local Set."""
        return f"set:note:{self.concept_id}:{suffix}" if suffix else f"set:note:{self.concept_id}"

    def _get_or_create_concept_word(self, word: str) -> str:
        """
        Returns the key of the general concept-word atom for `word`, creating it
        if it does not yet exist.

        Concept-word atoms are vocabulary atoms that represent structural roles
        (e.g. "section", "paragraph") as general concepts, independent of any
        particular note document. They are stored in the user's private scope and
        aliased as `concept:word:<word>` for stable lookup.

        Note content atoms link ONE-DIRECTIONALLY to these atoms via
        `sys:derived_from`, expressing that the content node is a particular
        instance of the general concept, not a redefinition of it.
        """
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing

        author_id = getattr(self.session, 'client_id', 'system')
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        meta = {
            "type": "concept_word",
            "word": word,
            "concept_model": "note",
            "created_at": time.time(),
        }
        key = self.cortex.put_chunk(content=word, meta=meta, author=author_id, scopes=scopes)
        self.cortex.set_alias(key, alias)
        return key

    def _register_to_package(self, key: str, subset_suffix: Optional[str] = None,
                             concept_word: Optional[str] = None):
        """
        Registers a content node to the note's scope sets.

        Design (Issue #3 fix):
        - The content atom lives ONLY in set:note:* (note-model scope).
        - If a concept_word is given, a separate general concept-word atom is
          looked up or created and registered to set:concept:* (BaseConcept
          catalog). The content atom links to the concept-word atom via
          sys:derived_from (one-directional: note-instance → general concept).
        - The same physical atom is NEVER registered to both namespaces.
        """
        author_id = getattr(self.session, 'client_id', 'system')

        # Note-scope registration (content atoms only)
        self.cortex.add_to_set(self._get_set_name(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._get_set_name(subset_suffix), key)

        # General concept-word registration (separate atom, one-directional link)
        if concept_word:
            cw_key = self._get_or_create_concept_word(concept_word)
            self.register_concept_node(cw_key)   # adds cw_key to set:concept:{root_id}
            self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    def _append_to_timeline(self, node_id: str, author_id: str):
        """
        [THE HORIZONTAL THREAD]
        Appends any node (Chunk, Section, Paragraph) to the absolute sequential timeline
        of the document, updating the floating 'sys:bottom' pointer dynamically.
        """
        tail_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")

        if not tail_links:
            # First element ever written to this Note
            self.cortex.put_link(self.concept_id, node_id, "sys:top", author=author_id)
        else:
            # Sequence bridging
            last_node_id = tail_links[0][0]
            self.cortex.put_link(last_node_id, node_id, "sys:next", author=author_id)
            self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)

            # Move the floating sys:bottom pointer via the Cortex abstraction layer
            self.cortex.remove_link(self.concept_id, last_node_id, "sys:bottom")

        # Bind the new bottom pointer
        self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)

    # =========================================================================
    # 📖 TOPOLOGICAL CONSTRUCTORS: BUILDING THE BOOK
    # =========================================================================
    
    def op_new(self, title: str, author: str = "system", isbn: Optional[str] = None) -> Dict[str, Any]:
        """
        [n.new] Instantiates a new Note Book Cosmos.
        Roots the primary Note Set and establishes structural sub-packages.
        """
        author_id = getattr(self.session, 'client_id', author)
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

        # 1. Materialize Root Anchor
        root_meta = {
            "type": "concept", "concept": "note", "role": "document",
            "title": title, "created_at": time.time()
        }
        if isbn:
            root_meta["isbn"] = isbn

        root_id = self.cortex.put_chunk(
            content=f"[ Note Book: {title} ]",
            meta=root_meta,
            author=author_id,
            scopes=user_scopes
        )

        # 2. Mount Context
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"

        # 3. Initialize Physical Set Bags
        self.cortex.create_set(self._get_set_name())
        self.cortex.create_set(self._get_set_name("paragraphs"))
        self.cortex.create_set(self._get_set_name("sections"))

        # Root atom registers to note-scope; concept_word "document" anchors the
        # general concept catalog for this note instance.
        self._register_to_package(root_id, concept_word="document")

        # 4. Context Focus Shift
        if hasattr(self.session, 'set_context'):
            self.session.set_context(self._ctx_key("active_note_root"), root_id)
            self.session.set_context(self._ctx_key("active_container_id"), root_id)

        logger.info(f"[NoteConcept] Sprouted new Book: '{title}' ({root_id[:8]})")
        return {"status": "initialized", "note_id": root_id, "title": title}

    def op_section(self, title: str, role: str = "section") -> Dict[str, Any]:
        """
        [n.chap / n.sec] Materializes a Structural Boundary (Chapter/Section/Appendix).
        """
        self._require_concept()

        author_id = getattr(self.session, 'client_id', "system")
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

        # 1. Create Structural Node
        sec_meta = {"role": role, "title": title, "created_at": time.time()}
        sec_id = self.cortex.put_chunk(content=title, meta=sec_meta, author=author_id, scopes=user_scopes)

        # 2. Package into note-scope sets; link to general concept word for this role
        sec_set_name = f"set:{role}:{sec_id}"
        self.cortex.create_set(sec_set_name)
        self.cortex.add_to_set(sec_set_name, sec_id)
        self._register_to_package(sec_id, subset_suffix="sections", concept_word=role)

        # 3. Append to Absolute Timeline
        self._append_to_timeline(sec_id, author_id)

        # 4. Vertical Thread (Hierarchy Nesting)
        active_container = getattr(self.session, "get_context", lambda k: None)(self._ctx_key("active_container_id")) or self.concept_id
        if role == "chapter":
            active_container = self.concept_id
            self.session.set_context(self._ctx_key("active_chapter_id"), sec_id)

        self.cortex.put_link(active_container, sec_id, "sys:contains", author=author_id)
        self.cortex.put_link(sec_id, active_container, "sys:part_of", author=author_id)

        # Shift active container focus to this new section
        self.session.set_context(self._ctx_key("active_container_id"), sec_id)

        return {"status": f"{role}_created", "section_id": sec_id, "title": title}

    def op_paragraph(self, category: str = "memo") -> Dict[str, Any]:
        """
        [n.para] Creates a categorized contextual wrapper (e.g. memo, code, hint).
        """
        self._require_concept()

        author_id = getattr(self.session, 'client_id', "system")
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

        para_meta = {"role": "paragraph", "category": category, "created_at": time.time()}
        para_id = self.cortex.put_chunk(content=f"[{category.upper()}]", meta=para_meta, author=author_id, scopes=user_scopes)

        # Bag initialization
        para_set_name = f"set:paragraph:{para_id}"
        self.cortex.create_set(para_set_name)
        self.cortex.add_to_set(para_set_name, para_id)
        self._register_to_package(para_id, subset_suffix="paragraphs", concept_word="paragraph")

        # Topology
        self._append_to_timeline(para_id, author_id)

        active_container = getattr(self.session, "get_context", lambda k: None)(self._ctx_key("active_container_id")) or self.concept_id
        self.cortex.put_link(active_container, para_id, "sys:contains", author=author_id)
        self.cortex.put_link(para_id, active_container, "sys:part_of", author=author_id)

        self.session.set_context(self._ctx_key("active_container_id"), para_id)
        return {"status": "paragraph_created", "paragraph_id": para_id, "category": category}

    def op_add_chunk(self, text: str, role: str = "chunk") -> Dict[str, Any]:
        """
        [n.add] Ingests physical content.
        Uses BaseConcept to autonomously trigger Weaver parsing without blocking.
        """
        self._require_concept()

        author_id = getattr(self.session, 'client_id', "system")
        user_scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

        # 1. BaseConcept handles immediate physical commit & asynchronous Weaver trigger.
        #    create_structured_chunk adds the chunk to set:concept:* via register_concept_node
        #    — for content chunks we skip the concept_word derivation link since the concept
        #    word is the role label itself, already implicit in the meta.
        chunk_res = self.create_structured_chunk(
            content=text, role=role, author_id=author_id,
            scopes=user_scopes, parent_set_id=self._get_set_name()
        )
        chunk_id = chunk_res["chunk_id"]

        # 2. Append to absolute sequence timeline
        self._append_to_timeline(chunk_id, author_id)

        # 3. Vertically bind to the current active container (Paragraph/Section)
        active_container = getattr(self.session, "get_context", lambda k: None)(self._ctx_key("active_container_id")) or self.concept_id
        if active_container != self.concept_id:
            self.cortex.put_link(active_container, chunk_id, "sys:contains", author=author_id)
            self.cortex.put_link(chunk_id, active_container, "sys:part_of", author=author_id)

        return {"status": "chunk_added", "chunk_id": chunk_id, "content_preview": text[:30]}

    def op_delete(self) -> Dict[str, Any]:
        """
        [n.rm] Purges the entire note package.
        Requires DELETE capability; drop_chunk enforces the superuser scope check
        via requester_scopes derived from the authenticated session.
        """
        self._require_concept()

        scopes = self.allowed_scopes
        self.cortex.drop_chunk(self.concept_id, requester_scopes=scopes)

        self.session.set_context(self._ctx_key("active_note_root"), None)
        self.session.set_context(self._ctx_key("active_container_id"), None)
        return {"status": "deleted", "note_id": self.concept_id}

    # =========================================================================
    # 🗺️ MORPHIC PROJECTIONS: THE ESSENCE OF Note
    # =========================================================================
    
    def op_toc(self) -> List[Dict[str, Any]]:
        """
        [n.toc] Hierarchy Projection.
        Traverses nested Set containers (Note -> Chapters -> Sections -> Paragraphs),
        while strictly respecting IAM multidimensional boundaries.
        """
        self._require_concept()

        note_set = self._get_set_name()
        allowed_scopes = self.allowed_scopes
        
        # High-speed set intersection: Only visible nodes within this note's universe
        visible_elements = set(self.cortex.core.get_keys_in_all_collections([note_set] + allowed_scopes))
        
        # Bypass check for Librarians
        is_librarian = "role:librarian" in allowed_scopes or "scope:sys:admin" in allowed_scopes
        if is_librarian:
            visible_elements = set(self.cortex.core.get_collection_members(note_set))

        toc = []

        def traverse_hierarchy(node_key, depth=0):
            if not is_librarian and node_key not in visible_elements:
                return

            content = self.cortex.get_chunk(node_key)
            meta = self.cortex.get_meta(node_key)
            role = meta.get("role", "")

            # Render structural containers
            if role in ["chapter", "section", "prologue", "epilogue", "appendix", "paragraph"]:
                title_val = content if role != "paragraph" else f"[{meta.get('category', 'memo').upper()}]"
                toc.append({
                    "depth": depth,
                    "title": title_val,
                    "id": node_key,
                    "role": role
                })

            links = self.cortex.get_adjacent_links(node_key)
            child_containers = [dst for dst, rel in links if rel == "sys:contains"]

            # Sort children using the absolute timeline (sys:next) to maintain perfect order
            ordered_children = self._sort_sequential_nodes(child_containers)
            for child in ordered_children:
                traverse_hierarchy(child, depth + 1 if role in ["chapter", "section"] else depth)

        traverse_hierarchy(self.concept_id)
        return toc

    def _sort_sequential_nodes(self, keys: List[str]) -> List[str]:
        """Sorts unordered set keys by aligning them with the absolute sys:next timeline."""
        if not keys: return []
        next_map = {}
        has_previous = set()
        
        for k in keys:
            links = self.cortex.get_adjacent_links(k)
            for dst, rel in links:
                if rel == "sys:next" and dst in keys:
                    next_map[k] = dst
                    has_previous.add(dst)
                    
        roots = [k for k in keys if k not in has_previous]
        if not roots: return keys
        
        ordered = []
        current = roots[0]
        while current:
            ordered.append(current)
            current = next_map.get(current)
            
        # Append any orphans just in case topology was corrupted manually
        for k in keys:
            if k not in ordered:
                ordered.append(k)
        return ordered

    def op_get_sequential_text(self) -> List[Dict[str, Any]]:
        """
        [n.read] Sequence Projection.
        Disregards vertical sets entirely and simply slides down the absolute
        timeline ('sys:top' to 'sys:bottom'), generating a flat, readable document.
        """
        self._require_concept()

        allowed_scopes = self.allowed_scopes
        is_librarian = "role:librarian" in allowed_scopes or "scope:sys:admin" in allowed_scopes
        sequence = []
        seen = set()

        # Find absolute top of the Note
        top_links = self.cortex.get_adjacent_links(self.concept_id, "sys:top")
        if not top_links: return []

        current_id = top_links[0][0]
        while current_id and current_id not in seen:
            seen.add(current_id)
            # Enforce IAM security boundaries
            if is_librarian or self.cortex.check_access(current_id, allowed_scopes):
                content = self.cortex.get_chunk(current_id)
                meta = self.cortex.get_meta(current_id)

                # Fetch dynamically woven offset annotations
                annotations = self.get_span_annotations(current_id)

                sequence.append({
                    "id": current_id,
                    "content": content,
                    "role": meta.get("role", "chunk"),
                    "category": meta.get("category"),
                    "annotations": annotations
                })

            # Traverse to next sequence link
            next_links = self.cortex.get_adjacent_links(current_id, "sys:next")
            current_id = next_links[0][0] if next_links else None

        return sequence

    # =========================================================================
    # ✏️ EDITING LAYER (M1) — revision, reorder, undo/redo
    # =========================================================================

    def _require_access(self, atom_id: str, label: str = "Atom"):
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise PermissionError(f"{label} {atom_id!r} is not accessible.")

    def _auth(self):
        aid = getattr(self.session, "client_id", "system")
        return aid, [f"owner:user_{aid}", f"view:user_{aid}"]

    def _content(self, key):
        c = self.cortex.get_chunk(key)
        if isinstance(c, dict):
            return c.get("content", "") or ""
        return c or ""

    def _meta(self, key):
        if hasattr(self.cortex, "get_meta"):
            m = self.cortex.get_meta(key)
            if m is not None:
                return m
        c = self.cortex.get_chunk(key)
        if isinstance(c, dict):
            return c.get("meta", {}) or {}
        return {}

    def _walk(self, start_rel, next_rel):
        """Walk a linked list starting from root→first (start_rel) via next_rel."""
        out, seen = [], set()
        top = self.cortex.get_adjacent_links(self.concept_id, start_rel)
        cur = top[0][0] if top else None
        while cur and cur not in seen:
            seen.add(cur)
            out.append(cur)
            nx = self.cortex.get_adjacent_links(cur, next_rel)
            cur = nx[0][0] if nx else None
        return out

    def _sys_anchors(self):
        return self._walk("sys:top", "sys:next")

    def _effective_order(self):
        """Return edit:top chain if it exists, otherwise fall back to sys:top chain."""
        if self.cortex.get_adjacent_links(self.concept_id, "edit:top"):
            return self._walk("edit:top", "edit:next")
        return self._sys_anchors()

    def _current(self, anchor):
        l = self.cortex.get_adjacent_links(anchor, "note:current")
        return l[0][0] if l else anchor

    def _set_current(self, anchor, version, author):
        for dst, _rel in self.cortex.get_adjacent_links(anchor, "note:current"):
            self.cortex.remove_link(anchor, dst, "note:current")
        if version and version != anchor:
            self.cortex.put_link(anchor, version, "note:current", author=author)

    def _clear_edit_order(self):
        for anchor in self._walk("edit:top", "edit:next"):
            for rel in ("edit:next", "edit:previous"):
                for dst, _r in self.cortex.get_adjacent_links(anchor, rel):
                    self.cortex.remove_link(anchor, dst, rel)
        for rel in ("edit:top", "edit:bottom"):
            for dst, _r in self.cortex.get_adjacent_links(self.concept_id, rel):
                self.cortex.remove_link(self.concept_id, dst, rel)

    def _build_edit_order(self, order, author):
        """Rebuild edit:top/next/previous/bottom links from ordered anchor list. None/empty restores sys: fallback."""
        self._clear_edit_order()
        if not order:
            return
        self.cortex.put_link(self.concept_id, order[0], "edit:top", author=author)
        for a, b in zip(order, order[1:]):
            self.cortex.put_link(a, b, "edit:next", author=author)
            self.cortex.put_link(b, a, "edit:previous", author=author)
        self.cortex.put_link(self.concept_id, order[-1], "edit:bottom", author=author)

    # ── edit journal (undo/redo stack) ─────────────────────────────────

    def _journal(self):
        l = self.cortex.get_adjacent_links(self.concept_id, "note:edit_journal")
        if l:
            try:
                j = json.loads(self._content(l[0][0]))
                if "history" in j and "cursor" in j:
                    return j
            except Exception:
                pass
        return {"history": [{"order": None, "active": {}}], "cursor": 0}

    def _save_journal(self, j, author):
        _aid, scopes = self._auth()
        old = self.cortex.get_adjacent_links(self.concept_id, "note:edit_journal")
        new = self.cortex.put_chunk(
            content=json.dumps(j, ensure_ascii=False),
            meta={"type": "note_edit_journal", "updated_at": time.time()},
            author=author, scopes=scopes,
        )
        for dst, _r in old:
            self.cortex.remove_link(self.concept_id, dst, "note:edit_journal")
        self.cortex.put_link(self.concept_id, new, "note:edit_journal", author=author)

    def _push_state(self, j, state):
        """Truncate redo-future after cursor and push new state."""
        j["history"] = j["history"][: j["cursor"] + 1] + [state]
        j["cursor"] += 1
        return j

    def _materialize(self, state, author):
        """Apply stored order/active to edit links and note:current pointers."""
        self._build_edit_order(state.get("order"), author)
        active = state.get("active", {}) or {}
        for anchor in self._sys_anchors():
            self._set_current(anchor, active.get(anchor), author)

    def _extract_tags(self, version_id):
        """No-op hook — M2 proj.extract connects here."""
        return

    # ── editing operators ───────────────────────────────────────────────

    def op_list_chunks(self, head_len: int = 80) -> Dict[str, Any]:
        """[note.list] List all content chunks in current display order, with head preview."""
        self._require_concept()
        out = []
        for i, anchor in enumerate(self._effective_order()):
            meta = self._meta(anchor)
            role = meta.get("role", "chunk")
            if role == "document":
                continue
            ver = self._current(anchor)
            content = self._content(ver).strip()
            head = content.splitlines()[0][:head_len] if content else ""
            out.append({"id": anchor, "version": ver, "head": head, "content": content,
                        "role": role, "order": i})
        return {"chunks": out, "count": len(out)}

    def op_edit_chunk(self, chunk_id: str, text: str) -> Dict[str, Any]:
        """[note.edit] Replace chunk content with a new version atom. Original stays as history."""
        self._require_concept()
        self._require_access(chunk_id, "Chunk")
        author, scopes = self._auth()
        prev = self._current(chunk_id)
        new = self.cortex.put_chunk(
            content=text,
            meta={"role": self._meta(chunk_id).get("role", "chunk"),
                  "edited_at": time.time(), "anchor": chunk_id},
            author=author, scopes=scopes,
        )
        self.cortex.add_to_set(self._get_set_name(), new)
        self.cortex.put_link(new, prev, "note:revises", author=author)

        j = self._journal()
        cur = j["history"][j["cursor"]]
        active = dict(cur.get("active", {}))
        active[chunk_id] = new
        self._push_state(j, {"order": cur.get("order"), "active": active})
        self._save_journal(j, author)

        self._set_current(chunk_id, new, author)
        self._extract_tags(new)
        return {"status": "edited", "chunk_id": chunk_id, "version": new}

    def op_move_chunk(self, chunk_id: str, after: str = None) -> Dict[str, Any]:
        """[note.move] Reorder chunk to immediately after `after` (None = move to top). sys: timeline unchanged."""
        self._require_concept()
        self._require_access(chunk_id, "Chunk")
        author, _scopes = self._auth()
        order = [a for a in self._effective_order() if a != chunk_id]
        if after and after in order:
            order.insert(order.index(after) + 1, chunk_id)
        else:
            order.insert(0, chunk_id)

        j = self._journal()
        cur = j["history"][j["cursor"]]
        self._push_state(j, {"order": order, "active": cur.get("active", {})})
        self._save_journal(j, author)

        self._build_edit_order(order, author)
        return {"status": "moved", "chunk_id": chunk_id, "after": after, "order": order}

    def op_undo_edit(self) -> Dict[str, Any]:
        """[note.undo] Step back one edit or reorder in the journal."""
        self._require_concept()
        author, _ = self._auth()
        j = self._journal()
        if j["cursor"] <= 0:
            return {"status": "nothing_to_undo"}
        j["cursor"] -= 1
        self._save_journal(j, author)
        self._materialize(j["history"][j["cursor"]], author)
        return {"status": "undone", "cursor": j["cursor"]}

    def op_redo_edit(self) -> Dict[str, Any]:
        """[note.redo] Step forward one edit in the journal."""
        self._require_concept()
        author, _ = self._auth()
        j = self._journal()
        if j["cursor"] >= len(j["history"]) - 1:
            return {"status": "nothing_to_redo"}
        j["cursor"] += 1
        self._save_journal(j, author)
        self._materialize(j["history"][j["cursor"]], author)
        return {"status": "redone", "cursor": j["cursor"]}

    def op_restore_original(self) -> Dict[str, Any]:
        """[note.restore] Drop edit-layer order/content overrides and return to original input order.
        History atoms (revises chain) are preserved; the restore itself is undo-able."""
        self._require_concept()
        author, _ = self._auth()
        j = self._journal()
        self._push_state(j, {"order": None, "active": {}})
        self._save_journal(j, author)
        self._materialize({"order": None, "active": {}}, author)
        return {"status": "restored_to_original"}

    def op_rename(self, title: str) -> Dict[str, Any]:
        """[note.rename] Set a mutable display name for this note via note:title pointer atom."""
        self._require_concept()
        author, scopes = self._auth()
        new_title = self.cortex.put_chunk(
            content=title,
            meta={"type": "note_title", "updated_at": time.time()},
            author=author, scopes=scopes,
        )
        for dst, _r in self.cortex.get_adjacent_links(self.concept_id, "note:title"):
            self.cortex.remove_link(self.concept_id, dst, "note:title")
        self.cortex.put_link(self.concept_id, new_title, "note:title", author=author)
        return {"status": "renamed", "note_id": self.concept_id, "title": title}

    def _display_title(self) -> str:
        """Return note:title pointer content if set, otherwise fall back to root meta title."""
        l = self.cortex.get_adjacent_links(self.concept_id, "note:title")
        if l:
            return self._content(l[0][0])
        return self._meta(self.concept_id).get("title", "")

    def op_clone(self) -> Dict[str, Any]:
        """[note.clone] Duplicate the active note as a new user-owned document.
        Creates a clean copy with no version history. Title is prefixed with '(Copy) '."""
        self._require_concept()
        title  = self._display_title() or "Untitled"
        chunks = self.op_get_sequential_text()

        clone = NoteConcept(self.session, namespace=self.namespace)
        clone.op_new(title=f"(Copy) {title}")
        for ch in chunks:
            text = ch.get("content") or ""
            if text:
                clone.op_add_chunk(text=text)
        return {"note_id": clone.concept_id, "title": f"(Copy) {title}"}
