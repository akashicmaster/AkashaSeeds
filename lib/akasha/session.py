"""
Cognitive Session Anchor (Persistent Context - Pro Edition).

Manages the cognitive context of each client purely within the semantic graph.
Replaces brittle global variables with persistent, mathematically rigorous Cognitive Sessions.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("Harmonia.Session")

class AkashaSession:
    """Represents the shared consciousness and continuous dialogue context."""
    def __init__(self, cortex: Any, client_id: str):
        self.cortex = cortex
        self.local_cortex = cortex 
        self.client_id = client_id
        
        self.allowed_scopes = [
            f"owner:user_{self.client_id}", 
            f"view:user_{self.client_id}",
            "scope:sys:universal",
            "view:public"
        ]
        self.locale = "en_US"
        
        self.session_node_id = self._anchor_consciousness()
        
        self.last_written_id = self.get_context("last_written_id")
        self.last_written_vector = self.get_context("last_written_vector")

    def _anchor_consciousness(self) -> str:
        """Locates the existing shared consciousness anchor in the graph, or creates it."""
        alias_name = f"sys:session:{self.client_id}"
        
        if hasattr(self.cortex, "get_all_aliases"):
            aliases = self.cortex.get_all_aliases()
            for a in aliases:
                if a.get("alias") == alias_name:
                    return a["key"]
                    
        initial_meta = {
            "type": "sys:session",
            "client_id": self.client_id,
            "focus": "@Atlantis",
            "mode": "root"
        }
        
        private_scopes = [f"owner:user_{self.client_id}", f"view:user_{self.client_id}"]
        
        if hasattr(self.cortex, "put_chunk"):
            node_id = self.cortex.put_chunk(
                content=f"Shared Consciousness Anchor for {self.client_id}",
                meta=initial_meta,
                author=self.client_id,
                scopes=private_scopes
            )
            if hasattr(self.cortex, "set_alias"):
                self.cortex.set_alias(node_id, alias_name)
            logger.debug(f"[Session] Root consciousness anchored for '{self.client_id}' at node {node_id[:8]}")
            return node_id
        else:
            logger.warning("[Session] Cortex interface missing 'put_chunk'. Operating in virtual mode.")
            return "virtual_session"

    def get_context(self, key: str, default: Any = None) -> Any:
        if not hasattr(self.cortex, "core") or not hasattr(self.cortex.core, "get_chunk_raw"):
            return default
            
        meta_row = self.cortex.core.get_chunk_raw(self.session_node_id)
        if not meta_row or not meta_row.get("meta"): 
            return default
        try:
            meta = json.loads(meta_row["meta"])
            return meta.get(key, default)
        except json.JSONDecodeError:
            return default

    def set_context(self, key: str, value: Any):
        if not hasattr(self.cortex, "core") or not hasattr(self.cortex.core, "get_chunk_raw"):
            return
            
        meta_row = self.cortex.core.get_chunk_raw(self.session_node_id)
        meta = {}
        if meta_row and meta_row.get("meta"):
            try:
                meta = json.loads(meta_row["meta"])
            except json.JSONDecodeError:
                pass
                
        meta[key] = value
        if hasattr(self.cortex, "set_meta"):
            self.cortex.set_meta(self.session_node_id, key, value)
        
        if key == "last_written_id": self.last_written_id = value
        if key == "last_written_vector": self.last_written_vector = value


class AkashaManager:
    """Singleton orchestrator that manages all active consciousness synchronizations."""
    _instance = None
    
    def __init__(self, series_name: str = "seeds", cortex: Any = None, harmonia_engine: Any = None):
        self.series_name = os.environ.get("AKASHA_SERIES", series_name)
        
        # [ARCHITECTURAL PURITY]
        # Cortex is strictly injected from outside (via Gateway -> Harmonia).
        # We no longer attempt unauthorized imports here.
        self.cortex = cortex
        self.harmonia_engine = harmonia_engine
        
        self._active_sessions: Dict[str, AkashaSession] = {}
        AkashaManager._instance = self

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_session(self, cortex: Any, client_id: str) -> AkashaSession:
        self.cortex = cortex 
        return self.get_session(client_id)

    def get_session(self, client_id: str, scopes: Optional[List[str]] = None) -> AkashaSession:
        max_leaves = int(os.environ.get("AKASHA_MAX_LEAVES", 999999))
        
        if client_id not in self._active_sessions:
            if len(self._active_sessions) >= max_leaves and client_id != "admin":
                logger.warning(f"[Manager] Cognitive capacity reached (Max: {max_leaves}). Cannot anchor '{client_id}'.")
                raise PermissionError(f"Akasha Node reached maximum active leaves ({max_leaves}).")
                
            if not getattr(self, "cortex", None):
                raise RuntimeError("AkashaManager requires a Cortex instance to anchor sessions.")
                
            self._active_sessions[client_id] = AkashaSession(self.cortex, client_id)
            if scopes:
                self._active_sessions[client_id].allowed_scopes = scopes

        return self._active_sessions[client_id]
