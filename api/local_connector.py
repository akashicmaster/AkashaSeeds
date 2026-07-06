"""
Local RPC Connector (Pro Edition).
Acts as a programmatic bridge between local UI applications, automated scripts,
and the in-memory Akasha Gateway. 

[ZERO-OVERHEAD ARCHITECTURE]
By residing in the 'api' layer, it bypasses HTTP/ASGI serialization entirely,
invoking the Python-native memory address of the Gateway directly while preserving
the strict JSON-RPC 2.0 interface. This ensures 100% compatibility with remote
connectors for seamless transitions between local and edge topologies.
"""

import logging
import traceback
from typing import Dict, Any, Optional

import api.gateway as _gw_module

logger = logging.getLogger("Harmonia.LocalConnector")

class AkashaLocalConnector:
    """
    Client adapter for executing high-speed, direct interactions with the local Akasha instance.
    Provides identical method signatures to remote clients but resolves via pure memory pointers.
    """
    def __init__(self, client_id: str = "guest"):
        """
        Initializes the local connector instance.
        
        Args:
            client_id (str): The identity token used for Gateway IAM authentication.
                             Determines the multidimensional active scopes during dispatch.
        """
        self.client_id = client_id
        logger.debug(f"[LocalConnector] Interface initialized for client '{self.client_id}'.")

    def send_rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Directly dispatches a structured JSON-RPC 2.0 request to the local Gateway.
        
        Args:
            method (str): The RPC method to invoke (e.g., 'write', 'note.new', 'explore').
            params (Optional[Dict]): The parameter payload containing contextual data.
            
        Returns:
            Dict: A strictly formatted JSON-RPC 2.0 response object.
        """
        if params is None:
            params = {}
        
        # Securely inject the initialized client identity for Gateway IAM verification
        params["client_id"] = self.client_id

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": "local_rpc"
        }
        
        try:
            # High-speed internal direct dispatch to the active Thalamus (Gateway)
            response = _gw_module.gateway.dispatch(payload)
            
            # Failsafe Boundary Guard: Ensure output strictly complies with expected types
            if not isinstance(response, dict):
                raise ValueError(f"Gateway did not return a valid dictionary payload. Received: {type(response)}")
                
            return response
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"[LocalConnector] Critical failure dispatching '{method}':\n{error_trace}")
            return {
                "jsonrpc": "2.0", 
                "error": {
                    "code": -32603, 
                    "message": f"Local Gateway Interface Error: {str(e)}"
                },
                "id": "local_rpc"
            }
