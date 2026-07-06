"""
Resilient Sync Engine (Lazy Propagation Model)
Handles asynchronous, offline-first synchronization using chunked batches
and a pending-link queue for lazy evaluation of semantic relationships.
Includes Telemetry Sync for the global Swarm Intelligence feedback loop.
"""
import time
from typing import Dict, List, Any
from remote.connector import AkashaRemoteConnector

class ResilientSync:
    def __init__(self, cortex, connector: AkashaRemoteConnector, batch_size: int = 50):
        self.cortex = cortex
        self.connector = connector
        self.batch_size = batch_size

    def sync_atoms_incremental(self, last_sync_time: float) -> Dict[str, Any]:
        results = {"uploaded": 0, "downloaded": 0, "errors": []}

        try:
            # 1. Upload local changes
            local_new_hashes = self.cortex.get_recent_atom_hashes(since=last_sync_time)
            for i in range(0, len(local_new_hashes), self.batch_size):
                batch = local_new_hashes[i : i + self.batch_size]
                payload = {}
                for h in batch:
                    content = self.cortex.get_chunk(h)
                    if content: payload[h] = content
                
                res = self.connector.send_rpc("sync.push_atoms", {"atoms": payload})
                if "error" in res:
                    results["errors"].append(f"Upload batch {i} failed: {res['error']}")
                    break
                results["uploaded"] += len(payload)

            # 2. Download remote changes
            res = self.connector.send_rpc("sync.get_recent_hashes", {"since": last_sync_time})
            if "error" in res:
                results["errors"].append(f"Download failed: {res['error']}")
                return results

            remote_new_hashes = res.get("result", [])
            local_all_hashes = set(self.cortex.get_all_keys())
            missing_hashes = [h for h in remote_new_hashes if h not in local_all_hashes]

            for i in range(0, len(missing_hashes), self.batch_size):
                batch = missing_hashes[i : i + self.batch_size]
                pull_res = self.connector.send_rpc("sync.pull_atoms", {"hashes": batch})
                
                if "error" in pull_res:
                    results["errors"].append(f"Download batch {i} failed: {pull_res['error']}")
                    break
                    
                pulled_atoms = pull_res.get("result", {})
                for h, content in pulled_atoms.items():
                    self.cortex.put_chunk(content, status="pending")
                    results["downloaded"] += 1

        except Exception as e:
            results["errors"].append(f"Sync Engine Error: {str(e)}")

        return results

    def sync_links_incremental(self, last_sync_time: float) -> Dict[str, Any]:
        results = {"links_uploaded": 0, "links_queued": 0, "errors": []}
        
        try:
            # 1. Upload local links
            local_new_links = self.cortex.get_recent_links(since=last_sync_time)
            for i in range(0, len(local_new_links), self.batch_size):
                batch = local_new_links[i : i + self.batch_size]
                res = self.connector.send_rpc("sync.push_links", {"links": batch})
                if "error" in res:
                    results["errors"].append(f"Link upload failed: {res['error']}")
                    break
                results["links_uploaded"] += len(batch)

            # 2. Download remote links
            res = self.connector.send_rpc("sync.get_recent_links", {"since": last_sync_time})
            if "error" in res:
                results["errors"].append(f"Link download failed: {res['error']}")
                return results
                
            remote_links = res.get("result", [])
            for link in remote_links:
                self.cortex.enqueue_pending_link(
                    src=link["src"], dst=link["dst"], rel=link["rel"], 
                    author=link.get("author", "sync"), ts=link["timestamp"]
                )
                results["links_queued"] += 1
                
        except Exception as e:
            results["errors"].append(f"Link Sync Error: {str(e)}")

        return results

    def sync_telemetry(self) -> Dict[str, Any]:
        """
        [NEW] Swarm Intelligence Telemetry Sync.
        Pushes local intentionality profiles (density, vectors) to the Origin
        without uploading private raw atom text.
        """
        results = {"telemetry_pushed": False, "errors": []}
        try:
            if hasattr(self.cortex, 'tensor') and self.cortex.tensor:
                # Placeholder: Extract Intentionality / Magnetic field stats
                # telemetry_payload = self.cortex.tensor.get_global_intentionality_profile()
                telemetry_payload = {"status": "active_swarm_node"}
                
                res = self.connector.send_rpc("sync.push_telemetry", {"telemetry": telemetry_payload})
                if "error" in res:
                    results["errors"].append(f"Telemetry upload failed: {res['error']}")
                else:
                    results["telemetry_pushed"] = True
        except Exception as e:
            results["errors"].append(f"Telemetry Sync Error: {str(e)}")
            
        return results

    def perform_sync_cycle(self) -> Dict[str, Any]:
        start_time = time.time()
        # In a real implementation, last_sync_time would be fetched from the vault.
        last_sync_time = 0.0 
        
        atom_stats = self.sync_atoms_incremental(last_sync_time)
        link_stats = self.sync_links_incremental(last_sync_time)
        tele_stats = self.sync_telemetry()
        
        elapsed = round(time.time() - start_time, 2)
        
        all_errors = atom_stats["errors"] + link_stats["errors"] + tele_stats["errors"]
        
        return {
            "status": "partial" if all_errors else "complete",
            "atoms_downloaded": atom_stats["downloaded"],
            "atoms_uploaded": atom_stats["uploaded"],
            "links_queued": link_stats["links_queued"],
            "telemetry_synced": tele_stats["telemetry_pushed"],
            "errors": all_errors,
            "elapsed_sec": elapsed
        }
