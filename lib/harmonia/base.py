"""
Harmonia Service Infrastructure (Pro Edition).

Base class for application services running on the Harmonia platform.
Acts as a sensory/motor interface layer, translating external
requests into internal semantic operations within the Akasha ecosystem.

[IAM & SESSION INJECTION COMPATIBILITY]
Fully utilizes the pre-authenticated session objects injected directly 
by the AkashaGateway. This guarantees that app services execute with the 
exact same multidimensional security scopes as native core operations.

[JSON-RPC 2.0 COMPLIANCE]
Standardized error handling ensures that service failures degrade gracefully
and format perfectly for the Web/CGI receptors.
"""
import logging
import traceback
from typing import Any, Dict, Optional

logger = logging.getLogger("Harmonia.Service")

class HarmoniaService:
    """
    Base class for all application services in the Harmonia ecosystem.
    Inherit from this class to build specialized cognitive tools (e.g., NLP extensions,
    Swarm intelligence monitors, external API integrators).
    """
    def __init__(self, gateway: Any):
        """
        Initializes the service and binds it to the central nervous system.
        
        Args:
            gateway: An instance of AkashaGateway, providing session-aware 
                     access to the Cortex, Nucleus, and operational engines.
        """
        self.gateway = gateway
        logger.debug(f"[HarmoniaService] '{self.__class__.__name__}' mounted to Gateway.")

    def execute(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches incoming RPC methods to their corresponding internal handlers.
        Handlers must be prefixed with 'rpc_' to be exposed securely.
        
        Args:
            method: The name of the method to execute (e.g., 'get_pilgrimage').
            params: A dictionary of parameters, containing the payload and 
                    the IAM-verified 'session' injected by the Gateway.
            
        Returns:
            The result of the handler execution or a structured JSON-RPC error dictionary.
        """
        handler_name = f"rpc_{method}"
        handler = getattr(self, handler_name, None)
        
        if handler and callable(handler):
            try:
                return handler(params)
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error(f"[{self.__class__.__name__}] Execution error in '{handler_name}':\n{error_trace}")
                return {
                    "error": {
                        "code": -32603,
                        "message": f"Service Execution Error ({self.__class__.__name__}): {str(e)}"
                    }
                }
        
        return {
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found or not exposed in service '{self.__class__.__name__}'"
            }
        }

    def call_core(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes primitive memory operations (read/write/explore/dive) 
        through the centralized gateway. This ensures that all memory access
        within an App Service strictly respects session contexts and IAM security policies.
        
        Args:
            method: The core method to call (e.g., 'write', 'explore', 'dive').
            params: Parameters including client_id and specific method arguments.
        """
        # Internal calls are marked with a specific ID for traceability within the swarm
        call_id = f"svc_{self.__class__.__name__.lower()}_{method}"
        
        payload = {
            "jsonrpc": "2.0",
            "method": method, 
            "params": params, 
            "id": call_id
        }
        
        # Dispatch through Gateway (which re-authenticates and enforces scopes automatically)
        response = self.gateway.dispatch(payload)
        
        # Return the unwrapped result or error directly for the app service to handle
        if "error" in response:
            return {"error": response["error"]}
        return response.get("result", response)

    def get_session_context(self, params: Dict[str, Any]) -> str:
        """
        Helper to extract or verify the client_id from parameters.
        Useful for sub-classes to quickly validate ownership.
        """
        client_id = params.get("client_id")
        if not client_id:
            # Fallback to checking the injected session object
            session = params.get("session")
            if session and hasattr(session, "client_id"):
                return session.client_id
            raise ValueError("client_id is required for this service operation.")
        return client_id

    def get_session(self, params: Dict[str, Any]) -> Any:
        """
        [PRO EDITION UPGRADE]
        Helper to retrieve the full, IAM-resolved AkashaSession object.
        Instead of re-fetching from the manager (which bypasses gateway-level
        injection), this first extracts the perfectly secure 'session' object 
        injected by AkashaGateway during dispatch.
        """
        # 1. Prefer the securely injected session from the Gateway
        session = params.get("session")
        if session:
            return session
            
        # 2. Fallback to manual manager retrieval (for internal direct calls)
        client_id = self.get_session_context(params)
        if hasattr(self.gateway, 'manager') and self.gateway.manager:
            return self.gateway.manager.get_session(client_id)
            
        raise RuntimeError("Critical: AkashaGateway is missing a valid manager reference, and no session was injected.")
