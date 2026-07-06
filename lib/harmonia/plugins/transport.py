"""
Transport Plugin for Harmonia.
Orchestrates the movement of data between external files (e.g., CSV) and 
internal memory layers. Now fully integrated with Harmonia's Workspace 
transaction system to ensure crash-proof, semantic-only staging (no volatile lists).
"""
import csv
import io
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AkashaBundle:
    """
    Data Transfer Object (DTO) for bulk memory operations.
    Acts as a portable container for atoms, links, and spatiotemporal metadata.
    """
    atoms: List[Dict[str, Any]]
    sets: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class CsvTransport:
    """
    CSV specific transport handler.
    Supports hierarchical inheritance for efficient spatiotemporal data entry.
    """
    def __init__(self, session):
        self.session = session

    def parse(self, csv_text: str) -> AkashaBundle:
        """
        Parses CSV into an AkashaBundle.
        Handles inheritance for traits, links, period, and locale.
        Columns expected: content, traits, links, lat, lng, period, locale
        """
        f = io.StringIO(csv_text.strip())
        reader = csv.DictReader(f)
        
        parsed_atoms = []
        # Buffers for hierarchical inheritance
        last_traits = ""
        last_links = ""
        last_period = ""
        last_locale = self.session.locale.primary if hasattr(self.session, 'locale') else "en"

        for i, row in enumerate(reader):
            content = row.get('content', '').strip()
            
            # Inheritance Logic: Fallback to previous row's value if current is empty
            traits_str = row.get('traits', '').strip() or last_traits
            links_str = row.get('links', '').strip() or last_links
            period = row.get('period', '').strip() or last_period
            locale = row.get('locale', '').strip() or last_locale
            
            lat = row.get('lat', '').strip()
            lng = row.get('lng', '').strip()

            if not content and not traits_str:
                continue

            # Process Traits and Links
            traits = [t.strip() for t in traits_str.replace('|', ';').split(';') if t.strip()]
            links = []
            if links_str:
                for item in links_str.split('|'):
                    if ':' in item:
                        rel, target = item.split(':', 1)
                        links.append({"rel": rel.strip(), "target": target.strip()})

            parsed_atoms.append({
                "temp_id": i,
                "content": content,
                "traits": traits,
                "links": links,
                "geo": {"lat": float(lat), "lng": float(lng)} if lat and lng else None,
                "period": period,
                "locale": locale
            })
            
            # Update buffers for the next row
            last_traits, last_links, last_period, last_locale = traits_str, links_str, period, locale

        return AkashaBundle(atoms=parsed_atoms)

    def serialize(self, keys: List[str]) -> str:
        """
        Exports specified atoms from the Cortex into a CSV string.
        Useful for backing up specific strata or sharing research data.
        """
        output = io.StringIO()
        fieldnames = ['content', 'traits', 'links', 'lat', 'lng', 'period', 'locale']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for key in keys:
            content = self.session.local_cortex.core.get_chunk(key)
            # Fetch aliases/traits as a single semicolon-separated string
            traits = ";".join(self.session.local_cortex.core.get_aliases_by_key(key))
            
            writer.writerow({
                "content": content,
                "traits": traits,
                "locale": getattr(self.session, 'locale', type('obj', (object,), {'primary': 'en'})).primary
            })
        
        return output.getvalue()

class TransportPlugin:
    """
    Main Transport Orchestrator.
    Moves data from external bundles safely into the semantic memory using
    the Harmonia transaction layer. Eliminates volatile in-memory staging.
    """
    def __init__(self, session):
        self.session = session
        self.csv = CsvTransport(session)
        self.current_tx_id: Optional[str] = None

    def stage_to_hippo(self, bundle: AkashaBundle) -> List[Dict[str, Any]]:
        """
        Stages the bundle into the Cortex as 'pending' atoms via a Harmonia Workspace.
        (Retains the 'hippo' method name for legacy compatibility, but now backed by DB).
        """
        harmonia = getattr(self.session, 'harmonia_engine', None)
        cortex = getattr(self.session, 'local_cortex', None)
        
        if not harmonia or not cortex:
            raise RuntimeError("Harmonia or Cortex not available in session.")

        # 1. Open a safe workspace transaction
        self.current_tx_id = harmonia.begin_workspace(cortex, f"transport_import:{len(bundle.atoms)}")
        
        # 2. Record Evidence
        evidence_key = cortex.put_chunk(
            content=f"Transport Import Session: {len(bundle.atoms)} atoms staged.",
            meta={"type": "sys:action_evidence", "tx_id": self.current_tx_id, "plugin": "transport"}
        )

        content_map = {}
        staged_summaries = []

        # 3. Insert Atoms as 'pending' and assign explicit traits/geos
        for data in bundle.atoms:
            meta = {
                "status": "pending",
                "tx_id": self.current_tx_id,
                "evidence_key": evidence_key
            }
            # Write to Cortex (Safely marked as pending)
            key = cortex.put_chunk(data['content'], meta=meta)
            cortex.add_to_set(self.current_tx_id, key)
            
            content_map[data['content']] = key
            data['real_key'] = key
            
            # Attach Jataka Anchors & Traits using Core API
            for trait in data['traits']:
                cortex.core.put_link(key, trait, "sys:associated_with")
            
            if data['geo']:
                coord = f"geo:at:{data['geo']['lat']},{data['geo']['lng']}"
                cortex.core.put_link(key, coord, "geo:at")
                
            if data['period']:
                cortex.core.put_link(key, f"chrono:{data['period']}", "chrono:period")

            staged_summaries.append({
                "preview": data['content'][:30],
                "geo": data['geo'],
                "period": data['period']
            })

        # 4. Synthesize Internal Cross-References (Links defined in CSV)
        for data in bundle.atoms:
            for link in data['links']:
                # Resolve target key if it refers to another content cell in the same bundle
                target = content_map.get(link['target'], link['target'])
                cortex.core.put_link(data['real_key'], target, link['rel'])

        # Return a preview summary for the UI
        return staged_summaries[:5]

    def commit_to_cortex(self) -> Dict[str, Any]:
        """
        Permanent commitment of staged data into semantic memory.
        Uses Harmonia to promote all 'pending' atoms to 'active'.
        """
        if not self.current_tx_id:
            return {"error": "No active transport staging (Workspace) found."}

        # Delegate crystallization to Harmonia Engine
        self.session.harmonia_engine.commit_workspace(
            self.session.local_cortex, 
            self.current_tx_id
        )
        
        tx_id = self.current_tx_id
        self.current_tx_id = None
        
        return {
            "status": "success", 
            "message": f"Workspace {tx_id} successfully committed to formal memory."
        }

    def rollback_staging(self) -> Dict[str, Any]:
        """
        [NEW] Allows the user/system to discard the staged CSV data 
        before committing, cleaning up all pending atoms instantly.
        """
        if not self.current_tx_id:
            return {"error": "No active staging to rollback."}
            
        self.session.harmonia_engine.rollback_workspace(
            self.session.local_cortex, 
            self.current_tx_id
        )
        self.current_tx_id = None
        return {"status": "rolled_back", "message": "Staged items discarded."}
