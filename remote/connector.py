"""
Remote RPC Connector (Pro Edition).
Base class for communicating with an external Akasha Gateway (e.g., ASGI or CGI server)
via strict JSON-RPC 2.0 over HTTP/HTTPS.

[ZERO-DEPENDENCY SURVIVAL STRATEGY]
Designed exclusively with standard libraries (`urllib`, `json`) to ensure maximum 
portability. This connector can be dropped into any minimal Python environment 
(IoT edge devices, bare-metal servers, restricted containers) and instantly 
establish a synaptic link to the Akasha Matrix without running `pip install`.

[SESSION & IDENTITY ENCAPSULATION]
Fully manages authentication handshakes, token upgrades, and automatic identity 
injection (IAM) for all outbound cognitive requests.
"""

import json
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("Harmonia.RemoteConnector")

class AkashaRemoteConnector:
    """
    Client connector for interacting with remote Akasha instances over HTTP/HTTPS.
    Handles identity injection (IAM), session state upgrades, and robust network 
    error capturing without third-party dependencies.
    """
    
    def __init__(self, endpoint_url: str, client_id: str = "guest", timeout: float = 30.0):
        """
        Initializes the synaptic connection to a remote Akasha instance.
        
        Args:
            endpoint_url (str): The full HTTP/HTTPS URL of the remote Gateway (e.g., http://mesh.local:8000/rpc).
            client_id (str): The initial identity token (defaults to guest until authenticated).
            timeout (float): Max seconds to wait for a network response before aborting.
        """
        self.endpoint = endpoint_url
        self.client_id = client_id
        self.user_id: Optional[str] = None
        self.role: Optional[str] = None
        self.timeout = timeout
        logger.debug(f"[RemoteConnector] Synapse targeted at endpoint: {self.endpoint}")

    def authenticate(self, user_id: str, passphrase: str) -> Dict[str, Any]:
        """
        Negotiates authentication with the remote Gateway.
        If successful, automatically upgrades the internal client_id to the official Session ID
        issued by the server, which will be used securely for all subsequent RPC calls.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "auth.login",
            "params": {"user": user_id, "passphrase": passphrase},
            "id": "remote_auth"
        }
        
        req = urllib.request.Request(
            self.endpoint, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AkashaRemoteSynapse/2.0'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                res_data = response.read().decode('utf-8')
                res = json.loads(res_data)
                
                if "error" not in res and "result" in res:
                    # Upgrade session state seamlessly from the Gateway's auth response
                    result_data = res["result"]
                    self.client_id = result_data.get("token", self.client_id)
                    self.role = result_data.get("role", "admin")
                    self.user_id = result_data.get("user", user_id)
                    logger.info(f"[RemoteConnector] Authentication successful for '{self.user_id}'.")
                    
                return res
                
        except urllib.error.HTTPError as e:
            # Server responded with an HTTP error code (e.g., 401, 500)
            return {"jsonrpc": "2.0", "error": {"code": e.code, "message": f"HTTP Error: {e.reason}"}, "id": "remote_auth"}
        except urllib.error.URLError as e:
            # Complete network failure (DNS, connection refused, timeout)
            return {"jsonrpc": "2.0", "error": {"code": -32000, "message": f"Network Error: {e.reason}"}, "id": "remote_auth"}
        except json.JSONDecodeError:
            return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Invalid JSON response from remote server."}, "id": "remote_auth"}
        except Exception as e:
            return {"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Unexpected Connector Error: {str(e)}"}, "id": "remote_auth"}

    def send_rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends a structured JSON-RPC 2.0 request to the remote endpoint.
        Automatically injects the active session identity for secure routing.
        """
        if params is None:
            params = {}
        
        # Inject active session identity into params for Gateway IAM verification
        params["client_id"] = self.client_id

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": "remote_rpc"
        }
        
        req = urllib.request.Request(
            self.endpoint, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AkashaRemoteSynapse/2.0'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                res_data = response.read().decode('utf-8')
                return json.loads(res_data)
                
        except urllib.error.HTTPError as e:
            return {"jsonrpc": "2.0", "error": {"code": e.code, "message": f"HTTP Error: {e.reason}"}, "id": "remote_rpc"}
        except urllib.error.URLError as e:
            return {"jsonrpc": "2.0", "error": {"code": -32000, "message": f"Network Error: {e.reason}"}, "id": "remote_rpc"}
        except json.JSONDecodeError:
            return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Invalid JSON response from remote server."}, "id": "remote_rpc"}
        except Exception as e:
            return {"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Unexpected Connector Error: {str(e)}"}, "id": "remote_rpc"}

    def execute_cli_command(self, cmd_line: str, stdin_data: Optional[Any] = None) -> Any:
        """
        Helper method to execute a raw CLI command string on the remote server.
        Translates the human-readable shell command into a 'sys.cli_exec' RPC call,
        which the remote Gateway will internally route just like local shell input.
        """
        params = {"command": cmd_line}
        if stdin_data is not None:
            params["stdin"] = stdin_data
            
        # Target the native Gateway CLI translator interceptor
        response = self.send_rpc("sys.cli_exec", params)
        
        if "error" in response:
            return {"error": response["error"]}
            
        return response.get("result")
