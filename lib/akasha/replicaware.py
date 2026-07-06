"""
Replicaware Cell (Distributed Network & IoT Hub)
Distributed network node and IoT control hub for the Akasha Cell.
Performs P2P communication (JSON-RPC) using only standard modules.

[MULTIDIMENSIONAL SCOPE UPDATE]
Integrates IAM to ensure that P2P offloading and telemetry respect 
the multidimensional ownership and view boundaries of the local node.
Ensures private or unverified nodes are not inadvertently leaked to peers.
"""
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Callable

class ReplicawareCell:
    def __init__(self, cell_id: str):
        self.cell_id = cell_id
        
        # Physical device bindings (for IoT)
        self.sensors: Dict[str, Callable[[], str]] = {}
        self.actuators: Dict[str, Callable[[str], None]] = {}
        
        # Other collaborating Akasha Cells (e.g., VPS mothership)
        self.peers: Dict[str, dict] = {}

    def add_peer(self, peer_name: str, url: str, client_id: str = "admin", token: str = None):
        """Registers a remote Akasha server (e.g., Thesaurus) as a peer."""
        self.peers[peer_name] = {
            "url": url.rstrip('/'), 
            "client_id": client_id,
            "token": token
        }
        print(f"[Replicaware] 🌐 Peer '{peer_name}' registered at {url}")

    def _rpc_call(self, peer_name: str, method: str, params: dict) -> dict:
        """Sends JSON-RPC requests using only standard libraries."""
        if peer_name not in self.peers:
            return {}
            
        peer = self.peers[peer_name]
        url = f"{peer['url']}/rpc"
        
        # Auto-inject identity context for remote IAM resolution
        if "client_id" not in params:
            params["client_id"] = peer["client_id"]
        if peer.get("token") and "token" not in params:
            params["token"] = peer["token"]
        
        req_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": f"replicaware_{self.cell_id}"
        }
        
        headers = {'Content-Type': 'application/json'}
        if peer.get("token"):
            headers['Authorization'] = f"Bearer {peer['token']}"
            
        req = urllib.request.Request(
            url, 
            data=json.dumps(req_data).encode('utf-8'),
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5.0) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            print(f"[Replicaware] RPC Error to '{peer_name}': {e}")
            return {}

    # --- P2P Memory Sharing (Offload & Fetch) ---
    def fetch_remote_memory(self, chunk_id: str) -> Optional[str]:
        """
        Queries all registered peers to acquire unknown memories.
        The remote peer's IAM will determine if this client_id is allowed to read it.
        """
        for peer_name in self.peers:
            res = self._rpc_call(peer_name, "read", {"id": chunk_id})
            if res.get("result") and isinstance(res["result"], dict) and "content" in res["result"]:
                content = res["result"]["content"]
                print(f"[Replicaware] 📥 Acquired memory chunk {chunk_id[:8]} from peer '{peer_name}'.")
                return content
        return None

    def offload_memory(self, chunk_id: str, content: str, peer_name: str, allowed_scopes: list = None, node_scopes: list = None) -> bool:
        """
        Transfers (offloads) memories to a specified peer.
        [SECURITY] Prevents offloading of purely private memories unless explicitly overridden.
        """
        # Safety Check: If the node is strictly private, do not offload to public peers.
        if node_scopes and not any(s in ["scope:sys:universal", "view:public"] for s in node_scopes):
            # In a real scenario, you might check if the peer represents an allowed group.
            # For now, we enforce strict isolation for purely private chunks.
            print(f"[Replicaware] 🛑 Blocked offload of private chunk {chunk_id[:8]} to '{peer_name}'.")
            return False
            
        res = self._rpc_call(peer_name, "write", {"text": content})
        if "result" in res:
            print(f"[Replicaware] 📤 Memory chunk {chunk_id[:8]} successfully offloaded to '{peer_name}'.")
            return True
        return False

    def push_telemetry_to_peer(self, peer_name: str, telemetry_data: dict) -> bool:
        """Explicit Swarm Telemetry Push via RPC."""
        res = self._rpc_call(peer_name, "sys.telemetry", {"telemetry": telemetry_data})
        return "error" not in res

    # --- Hardware Integration (IoT Stubs) ---
    def bind_sensor(self, node_id: str, read_func: Callable[[], str]):
        self.sensors[node_id] = read_func

    def bind_actuator(self, node_id: str, write_func: Callable[[str], None]):
        self.actuators[node_id] = write_func

    def is_sensor(self, node_id: str) -> bool: return node_id in self.sensors
    def is_actuator(self, node_id: str) -> bool: return node_id in self.actuators
    
    def read_sensor(self, node_id: str) -> str: 
        return self.sensors[node_id]()
        
    def trigger_actuator(self, node_id: str, value: str): 
        # [FUTURE] Ensure simulation (dream) mode is OFF before triggering real hardware.
        self.actuators[node_id](value)
