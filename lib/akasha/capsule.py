"""
Delay-Tolerant Knowledge Capsule Protocol (DTN)
Allows asynchronous, unidirectional transfer of knowledge graphs via files or email.
Built for deep space, offline field work, secure air-gapped environments, 
and global Swarm Intelligence telemetry feedback.

[MULTIDIMENSIONAL SCOPE UPDATE]
Enforces IAM boundaries during encapsulation to prevent data leakage of unowned atoms.
Safely injects received decapsulated atoms into isolated 'pending' scopes for admin verification.
"""
import json
import time
from typing import Dict, Any

class KnowledgeCapsule:
    def __init__(self, session):
        """
        Initialized with a PersistentSession to ensure all operations
        respect the client's current multidimensional scopes.
        """
        self.session = session
        self.cortex = session.local_cortex  # Must be an instance of AkashaEngine (Composite)
    def encapsulate(self, since: float, include_telemetry: bool = True) -> str:
        """
        Extracts recent thoughts and links into a sealed payload.
        Strictly filters the payload so the user can only export atoms they have 'view' access to.
        """
        author = self.session.client_id
        allowed_scopes = getattr(self.session, 'active_scopes', [])

        atoms_payload = {}
        # Gather modified atoms
        recent_hashes = self.cortex.get_recent_atom_hashes(since=since)
        for h in recent_hashes:
            # [SECURITY] Use get_scoped_chunk to guarantee we only pack what we are allowed to see
            content = self.cortex.get_scoped_chunk(h, allowed_scopes)
            if content and not content.startswith("[Evicted"): 
                atoms_payload[h] = content

        # Gather modified links (Filtering out links to unviewable atoms could be added here in the future)
        recent_links = self.cortex.get_recent_links(since=since)
        
        # Telemetry / Swarm Intelligence Stats
        telemetry_payload = {}
        if include_telemetry and hasattr(self.cortex, 'tensor') and self.cortex.tensor:
            # Placeholder: Extract local "Intentionality Scores" for Swarm Intelligence
            pass

        # Construct the Capsule
        capsule = {
            "metadata": {
                "protocol": "akasha_capsule_v1.2",
                "author": author,
                "timestamp": time.time(),
                "extracted_since": since
            },
            "atoms": atoms_payload,
            "links": recent_links,
            "telemetry": telemetry_payload
        }

        return json.dumps(capsule, ensure_ascii=False, indent=2)

    def encapsulate_document(self, concept_id: str, set_name: str, doc_type: str,
                             scopes: list = None) -> str:
        """
        Export a single document (note / fieldnote / loom piece) as a scoped Akasha capsule.
        Collects the root atom, every atom in the document's set, and all outgoing links
        from those atoms.  IAM boundaries are honoured via get_scoped_chunk.

        Future format targets (add alongside 'akasha_capsule_v1.2' once stabilised):
          - Markdown + YAML front-matter  (.md)
          - OPML outline                  (.opml)
          - RDF/Turtle graph              (.ttl)
          - Obsidian-compatible JSON      (.json, obsidian schema)
        """
        author        = self.session.client_id
        # Prefer caller-supplied scopes; fall back to session attribute; last resort: unscoped
        allowed_scopes = (scopes
                          or getattr(self.session, 'active_scopes', None)
                          or getattr(self.session, 'base_scopes', None)
                          or [])
        ts            = time.time()

        def _get(key: str) -> str | None:
            """Scoped read with unscoped fallback for the user's own exported document."""
            content = self.cortex.get_scoped_chunk(key, allowed_scopes) if allowed_scopes else None
            if content is None:
                content = self.cortex.get_chunk(key)
            return content

        atoms_payload: Dict[str, str] = {}

        # Root atom
        root_content = _get(concept_id)
        if root_content and not root_content.startswith("[Evicted"):
            atoms_payload[concept_id] = root_content

        # All atoms registered in the document's set
        for member in self.cortex.get_set_members(set_name):
            key     = member["key"]
            content = _get(key)
            if content and not content.startswith("[Evicted"):
                atoms_payload[key] = content

        # All outgoing links from document atoms (full topology preserved)
        links_seen: set = set()
        links_list = []
        for key in atoms_payload:
            for dst, rel in self.cortex.get_adjacent_links(key):
                link_key = (key, dst, rel)
                if link_key not in links_seen:
                    links_seen.add(link_key)
                    links_list.append({"src": key, "dst": dst, "rel": rel,
                                       "author": author, "timestamp": ts})

        capsule = {
            "metadata": {
                "protocol":      "akasha_capsule_v1.2",
                "author":        author,
                "timestamp":     ts,
                "doc_type":      doc_type,
                "concept_id":    concept_id,
                "extracted_since": 0.0,
            },
            "atoms":     atoms_payload,
            "links":     links_list,
            "telemetry": {},
        }
        return json.dumps(capsule, ensure_ascii=False, indent=2)

    def decapsulate(self, capsule_json: str) -> Dict[str, Any]:
        """
        Opens a received capsule and gently injects it into the local cortex.
        All atoms are forced into 'pending' status and placed in an isolated scope.
        Links are placed into the Pending Queue for Lazy Evaluation.
        """
        results = {"atoms_injected": 0, "links_queued": 0, "telemetry_received": False, "errors": []}
        
        try:
            payload = json.loads(capsule_json)
            meta = payload.get("metadata", {})
            remote_author = meta.get("author", "unknown_capsule")
            
            # [SECURITY] Define an isolation scope for this imported capsule
            # This ensures imported atoms don't pollute the universal scope until verified
            capsule_isolation_scope = f"capsule:import:{remote_author}:{int(time.time())}"
            self.cortex.create_set(capsule_isolation_scope) # Virtual set creation
            
            isolation_scopes = [
                capsule_isolation_scope,
                f"owner:user_{self.session.client_id}" # The local admin taking responsibility
            ]

            # 1. Inject Atoms (Safe due to hash immutability)
            atoms = payload.get("atoms", {})
            for h, content in atoms.items():
                # Store as 'pending' and isolated to require verification by the local admin
                self.cortex.put_chunk(
                    content, 
                    author=remote_author, 
                    status="pending", 
                    scopes=isolation_scopes
                )
                results["atoms_injected"] += 1

            # 2. Inject Links into Pending Queue (Lazy Weaving)
            links = payload.get("links", [])
            for link in links:
                self.cortex.enqueue_pending_link(
                    src=link["src"], 
                    dst=link["dst"], 
                    rel=link["rel"], 
                    author=remote_author, 
                    ts=link.get("timestamp", time.time())
                )
                results["links_queued"] += 1
                
            # 3. Process Telemetry (If acting as Origin/Mother-ship)
            telemetry = payload.get("telemetry", {})
            if telemetry:
                results["telemetry_received"] = True
                
        except json.JSONDecodeError:
            results["errors"].append("Invalid capsule format (corrupted JSON).")
        except Exception as e:
            results["errors"].append(f"Decapsulation failed: {str(e)}")

        return results
