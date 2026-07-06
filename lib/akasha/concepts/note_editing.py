"""
NoteConcept — Editing Extension (M1)
====================================

The "revision" core of the writing-support Note Loom. Integrates the following methods into the existing NoteConcept.
No dependency on proj; self-contained. Intended for Claude Code to integrate into the real note.py and debug/test.

Design core (two-layer links):
  Original links (chronological / entry order) = sys:top/next/previous/bottom  ← immutable, sacred
  Edit links (revision) = · Content versions: note:revises (new version → old version, chain of history)
                          · Current-version pointer: note:current (anchor → active version)
                          · Order versions: edit:top/next/previous/bottom (reordering; falls back to sys: if absent)
  undo/redo/restore = driven by note:edit_journal (root → journal atom · JSON: history+cursor)

Terminology:
  anchor  … The immutable id of the "slot" accumulated chronologically by note.add (slot identity).
            The anchor id does not change when content is edited (version resolved via note:current).
  version … The atom holding the current content of an anchor (new hash from content-addressing).

────────────────────────────────────────────────────────────────────────
Integration notes (for Claude Code)
────────────────────────────────────────────────────────────────────────
1) Add to NoteConcept.CONCEPT_METHODS:
     "list":    {"op": "op_list_chunks"},
     "edit":    {"op": "op_edit_chunk",
                 "coerce": lambda d: {"chunk_id": d.get("chunk_id") or d.get("id",""),
                                      "text": d.get("text","")}},
     "move":    {"op": "op_move_chunk",
                 "coerce": lambda d: {"chunk_id": d.get("chunk_id") or d.get("id",""),
                                      "after": d.get("after")}},
     "undo":    {"op": "op_undo_edit"},
     "redo":    {"op": "op_redo_edit"},
     "restore": {"op": "op_restore_original"},
     "rename":  {"op": "op_rename"},

2) Add to kernel.py _METHOD_TO_ACTION:
     "note.list": "read", "note.edit": "write", "note.move": "write",
     "note.undo": "write", "note.redo": "write", "note.restore": "write",
     "note.rename": "write",

3) Add to api/router.py COMMAND_SPECS (optional for CLI):
     "n.list":    {"method":"note.list",    "args":[],                 "desc":"List chunks (head only)"},
     "n.edit":    {"method":"note.edit",    "args":["chunk_id","text"],"desc":"Edit a chunk (new version)"},
     "n.move":    {"method":"note.move",    "args":["chunk_id","after"],"desc":"Reorder a chunk"},
     "n.undo":    {"method":"note.undo",    "args":[],                 "desc":"Undo last edit"},
     "n.redo":    {"method":"note.redo",    "args":[],                 "desc":"Redo"},
     "n.restore": {"method":"note.restore", "args":[],                 "desc":"Restore original order/content"},
     "n.rename":  {"method":"note.rename",  "args":["title"],          "desc":"Rename the note"},

4) Add to §9 Reserved Relations:
     note:revises, note:current, note:title, note:edit_journal,
     edit:top, edit:next, edit:previous, edit:bottom

DEBUG notes (areas Claude Code should focus on):
  - The return of get_chunk (dict or str) varies across documentation; absorbed by _content/_meta.
    Verify against the implementation.
  - Align get_collection_members / get_set_members names with the implementation.
  - Verify the branch case of editing after undo then redoing (redo history is discarded).
  - section/paragraph also rides the sys: timeline, so _effective_order returns them including role.
  - _extract_tags is a no-op hook until proj is implemented (connected in M2).
"""

import time
import json


class _NoteEditingExtension:
    """Methods to integrate into NoteConcept (presented mixin-style; actual implementation lives inside NoteConcept)."""

    # ── Helpers ───────────────────────────────────────────────
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
        """Walk from start_rel (root→first) following next_rel and return an ordered list."""
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
        """Use edit-link order if present; otherwise fall back to entry order (sys:)."""
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
        """Rebuild edit links from order (anchor sequence). If None/empty, revert to entry order."""
        self._clear_edit_order()
        if not order:
            return
        self.cortex.put_link(self.concept_id, order[0], "edit:top", author=author)
        for a, b in zip(order, order[1:]):
            self.cortex.put_link(a, b, "edit:next", author=author)
            self.cortex.put_link(b, a, "edit:previous", author=author)
        self.cortex.put_link(self.concept_id, order[-1], "edit:bottom", author=author)

    # ── Edit journal (drives undo/redo/restore) ────────────
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
        """Discard everything after cursor (redo branch) and push a new state."""
        j["history"] = j["history"][: j["cursor"] + 1] + [state]
        j["cursor"] += 1
        return j

    def _materialize(self, state, author):
        """Apply state (order/active) to edit links."""
        self._build_edit_order(state.get("order"), author)
        active = state.get("active", {}) or {}
        for anchor in self._sys_anchors():
            self._set_current(anchor, active.get(anchor), author)

    def _extract_tags(self, version_id):
        """No-op hook until proj is implemented (M2: calls proj.extract)."""
        # TODO(M2): wire version_id to tag/axis via proj.extract
        return

    # ── operators ────────────────────────────────────────────
    def op_list_chunks(self, head_len: int = 80):
        """[note.list] List of chunks with head preview only. Returned in current order (edit links take priority)."""
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
            out.append({"id": anchor, "version": ver, "head": head,
                        "role": role, "order": i})
        return {"chunks": out, "count": len(out)}

    def op_edit_chunk(self, chunk_id: str, text: str):
        """[note.edit] Rewrite the content of a chunk. Creates a new version atom; the old version remains in history.
        The sys: timeline is immutable. note:current is updated to the new version."""
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
        self.cortex.add_to_set(self._get_set_name(), new)        # content set
        self.cortex.put_link(new, prev, "note:revises", author=author)  # chain of history

        j = self._journal()
        cur = j["history"][j["cursor"]]
        active = dict(cur.get("active", {}))
        active[chunk_id] = new
        self._push_state(j, {"order": cur.get("order"), "active": active})
        self._save_journal(j, author)

        self._set_current(chunk_id, new, author)
        self._extract_tags(new)
        return {"status": "edited", "chunk_id": chunk_id, "version": new}

    def op_move_chunk(self, chunk_id: str, after: str = None):
        """[note.move] Reorder: move immediately after 'after' (after=None moves to the top).
        The sys: timeline is immutable. Only the edit: order is rewired."""
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
        return {"status": "moved", "chunk_id": chunk_id, "after": after,
                "order": order}

    def op_undo_edit(self):
        """[note.undo] Step back one level from the last edit/reorder."""
        self._require_concept()
        author, _ = self._auth()
        j = self._journal()
        if j["cursor"] <= 0:
            return {"status": "nothing_to_undo"}
        j["cursor"] -= 1
        self._save_journal(j, author)
        self._materialize(j["history"][j["cursor"]], author)
        return {"status": "undone", "cursor": j["cursor"]}

    def op_redo_edit(self):
        """[note.redo] Step forward one level, re-applying an undone edit."""
        self._require_concept()
        author, _ = self._auth()
        j = self._journal()
        if j["cursor"] >= len(j["history"]) - 1:
            return {"status": "nothing_to_redo"}
        j["cursor"] += 1
        self._save_journal(j, author)
        self._materialize(j["history"][j["cursor"]], author)
        return {"status": "redone", "cursor": j["cursor"]}

    def op_restore_original(self):
        """[note.restore] Discard edit links and revert to entry order and original content.
        History (old atoms, revises chain) is preserved. The restore operation itself is also undo-able."""
        self._require_concept()
        author, _ = self._auth()
        j = self._journal()
        self._push_state(j, {"order": None, "active": {}})
        self._save_journal(j, author)
        self._materialize({"order": None, "active": {}}, author)
        return {"status": "restored_to_original"}

    def op_rename(self, title: str):
        """[note.rename] Rename the note. Since root meta is immutable (content-addressed),
        the mutable display name is held in a note:title pointer atom (note:title takes display priority)."""
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

    def _display_title(self):
        """Return note:title if present, otherwise the title from root meta. Usable in op_open/op_list_all."""
        l = self.cortex.get_adjacent_links(self.concept_id, "note:title")
        if l:
            return self._content(l[0][0])
        return self._meta(self.concept_id).get("title", "")
