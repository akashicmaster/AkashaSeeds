"""
Cognitive Context Resolver.
Translates abstract human-readable target strings into absolute SHA-256 graph keys.
Bridges the gap between human intuition and the physical semantic network.

[MULTIDIMENSIONAL SCOPE UPDATE]
Fully integrated with the Multidimensional Scope model. 
Link traversals (paths) and Set expansions implicitly filter out atoms 
that the client does not have the IAM capability to view.
"""
import re
from typing import Union, List, Optional


def _history_key(item) -> str:
    """Extract a plain key string from a history item (dict row or bare string)."""
    if isinstance(item, dict):
        return item.get("key", "")
    return item or ""


class ContextResolver:
    """
    Cognitive layer that resolves abstract target strings into keys.
    
    Supported Syntaxes:
    - Context: $0 (latest), $it (focus), $1..n (history), $0:5 (range)
    - Aliases: 'alias_name', 'concept_target'
    - Jataka:  @here (current GPS), @now (current chrono), @2026 (era anchor)
    - Sets:    set:target_set, #trait:target_trait (member expansion)
    - Paths:   target.parent, target.child (link traversal)
    - Vectors: ~emo:target (Semantic/Tensor search closest match)
    """

    @staticmethod
    def resolve(session, target: str, history: List[str]) -> Union[str, List[str], None]:
        """
        Translates a human-readable target into exact atom key(s).
        Returns a single key (str) or a list of keys (List[str]) if range/set syntax is used.
        """
        if not target:
            return history[0] if history else None

        # Safely acquire the Cortex (Composite Layer) and IAM Scopes from the session
        cortex = getattr(session, 'cortex', getattr(session, 'local_cortex', None))
        allowed_scopes = getattr(session, 'allowed_scopes', None)
        
        if not cortex:
            return target

        # --- 1. Range / Slicing Resolution ($0:5) ---
        range_match = re.match(r'^\$(\d+):(\d+)$', str(target))
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            return [_history_key(item) for item in history[start:end]]

        # --- 2. Reserved Context Variables ($it, $0, $1, ...) ---
        if target == "$it":
            # $it always points to what the user last wrote, not an internal node
            return getattr(session, 'last_written_id', None) or (_history_key(history[0]) if history else None)
        if target == "$0":
            return _history_key(history[0]) if history else None

        if str(target).startswith("$") and target[1:].isdigit():
            idx = int(target[1:])
            return _history_key(history[idx]) if 0 <= idx < len(history) else None

        # --- 2.5. Typed ref-slot variables ($who, $where, $why, $when, $how, $what, $which …) ---
        # These are typed anaphoric slots backed by ref: cognitive primitives.
        # Set explicitly via `ref.set dim=<dim> target=<atom>`.
        if str(target).startswith("$"):
            from lib.akasha.ref_primitives import REF_SLOT_DIMENSIONS
            dim = target[1:]
            if dim in REF_SLOT_DIMENSIONS:
                val = session.get_ref_slot(dim) if hasattr(session, "get_ref_slot") else None
                return val  # None if slot is empty

        # --- 3. Jataka Spatiotemporal Modifiers (@here, @now, @2026) ---
        if str(target).startswith("@"):
            modifier = target[1:]
            
            def get_from_vault(cat, ident):
                if hasattr(cortex, 'core') and hasattr(cortex.core, 'vault_retrieve'):
                    return cortex.core.vault_retrieve(cat, ident)
                return None

            if modifier == "here":
                # Resolves to the atom representing the user's current GPS position
                return get_from_vault("jataka.state", "current_gps_key")
            elif modifier == "now":
                return get_from_vault("jataka.state", "current_chrono_key")
            elif modifier.isdigit():
                # Temporal anchor lookup
                year_alias = f"chrono:year:{modifier}"
                return cortex.resolve_alias(year_alias)
            else:
                # User-defined alias with @ prefix (@chunk2 → alias "chunk2")
                key = cortex.resolve_alias(modifier)
                if key:
                    return key

        # --- 4. Set & Trait Expansion (set:name, #trait) ---
        if str(target).startswith("set:"):
            set_name = target[4:]
            # list_set handles scope filtering natively
            members = cortex.list_set(set_name, allowed_scopes)
            return [m["key"] for m in members]

        if str(target).startswith("#"):
            trait_name = target[1:]
            trait_key = cortex.resolve_alias(f"trait:{trait_name}")
            if trait_key:
                links = cortex.get_incoming_links(trait_key)
                valid_sources = []
                for src, rel in links:
                    if rel == "sys:associated_with":
                        # [SECURITY] Filter out invisible atoms
                        if not allowed_scopes or cortex.check_access(src, allowed_scopes):
                            valid_sources.append(src)
                return valid_sources

        # --- 5. Relative Navigation (target.parent, target.child) ---
        if "." in str(target):
            base_ref, relation = target.split(".", 1)
            base_key = ContextResolver.resolve(session, base_ref, history)
            if not isinstance(base_key, str): return None
            
            if relation == "child":
                links = cortex.get_adjacent_links(base_key)
                valid_dests = []
                for dst, rel in links:
                    if not allowed_scopes or cortex.check_access(dst, allowed_scopes):
                        valid_dests.append(dst)
                return valid_dests
                
            elif relation == "parent":
                links = cortex.get_incoming_links(base_key)
                valid_sources = []
                for src, rel in links:
                    if not allowed_scopes or cortex.check_access(src, allowed_scopes):
                        valid_sources.append(src)
                return valid_sources

        # --- 6. Alias Resolution ---
        key = cortex.resolve_alias(target)
        if key:
            return key

        # --- 6.1. Nucleus fallback (universal / proto-word atoms shared across cells) ---
        _nucleus = getattr(cortex, '_nucleus', None) or getattr(session, 'nucleus', None)
        if _nucleus:
            nucleus_key = _nucleus.resolve_alias(target)
            if nucleus_key:
                return nucleus_key

        # --- 6.2. Group space fallback (atoms shared within the user's groups) ---
        _group_engines = getattr(session, 'group_engines', {})
        for _geng in _group_engines.values():
            gkey = _geng.resolve_alias(target)
            if gkey:
                return gkey

        # --- 6.5. Leaf-collection fallback (cross-namespace, single SQL JOIN) ---
        # 'love' → finds word:en:love AND emo:love via leaf:love collection.
        # active_scopes  → Dim-1 permission + Dim-2 capability (never locale)
        # locale_codes   → Dim-3 priority order for display filtering + ordering
        if ":" not in str(target) and not str(target).startswith(("$", "@", "~", "#")):
            _scopes = getattr(session, 'active_scopes', None)
            _locale_obj = getattr(session, 'locale', None)
            _locale_codes = _locale_obj.get_priority_list() if _locale_obj else None
            leaf_keys = cortex.list_leaf(target, _scopes, _locale_codes)
            if leaf_keys:
                return leaf_keys[0] if len(leaf_keys) == 1 else leaf_keys

        # --- 7. Tensor/Magnetic Resolution (~emo:sadness) ---
        if str(target).startswith("~") and hasattr(cortex, 'tensor') and cortex.tensor:
            # Placeholder: closest_key = cortex.tensor.find_closest(...)
            pass

        # --- 8. Session Symbols & Direct Hash fallback ---
        if hasattr(session, 'symbols') and target in session.symbols:
            return session.symbols[target]
            
        # If it's already a 64-char hex string, assume it's a key
        if len(str(target)) == 64 and all(c in '0123456789abcdef' for c in str(target)):
            return target

        return target

    @staticmethod
    def resolve_to_list(session, target: str, history: List[str]) -> List[str]:
        """
        Force resolution into a list. Useful for batch operations like 'set.op'.
        """
        res = ContextResolver.resolve(session, target, history)
        if res is None: return []
        if isinstance(res, list): return res
        return [res]
