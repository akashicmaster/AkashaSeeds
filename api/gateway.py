"""
Master Gateway Engine (Boundary Proxy).
Acts as the JSON-RPC 2.0 proxy between the Shell (api/, remote/) and the Kernel.
Contains NO direct cognitive logic — it delegates everything to KernelDispatcher.
"""
import logging
import uuid

logger = logging.getLogger("Akasha.Gateway")


class AkashaGateway:
    def __init__(self, kernel_client=None):
        """
        Accepts a KernelDispatcher instance as `kernel_client`.
        When None, all dispatches return a kernel-offline error.
        """
        self.kernel_client = kernel_client

    def dispatch(self, request_payload: dict) -> dict:
        """Unified entry point for all portal types (stdio, ASGI, MCP, remote)."""
        if not self._is_valid_rpc(request_payload):
            return self._rpc_error(
                request_payload.get("id") if isinstance(request_payload, dict) else None,
                -32600, "Invalid JSON-RPC 2.0 Request"
            )

        # sys.cli_exec: parse a raw command string here (shell responsibility)
        # so the kernel never needs to import api.router
        if request_payload.get("method") == "sys.cli_exec":
            return self._handle_cli_exec(request_payload)

        try:
            if self.kernel_client:
                return self.kernel_client.dispatch(request_payload)
            else:
                return self._rpc_error(
                    request_payload.get("id"), -32001,
                    "Kernel offline: no kernel_client attached to gateway"
                )
        except Exception as e:
            logger.error(f"[Gateway] Boundary error: {e}", exc_info=True)
            return self._rpc_error(
                request_payload.get("id"), -32000,
                f"Internal Gateway Error: {e}"
            )

    def _handle_cli_exec(self, payload: dict) -> dict:
        """Translates a raw command string into a JSON-RPC call and dispatches it."""
        from api.router import CommandRouter
        params = payload.get("params", {})
        data = params.get("data", params)
        cmd = data.get("command", "") or data.get("cmd", "")
        session_token = params.get("session_token") or params.get("client_id") or "anonymous"
        rid = payload.get("id")

        if not cmd:
            return self._rpc_error(rid, -32602, "sys.cli_exec requires 'command'")

        rpc_payload = CommandRouter.build_rpc_request(cmd, session_token)
        if not rpc_payload:
            return self._rpc_error(rid, -32602, f"Cannot parse command: '{cmd}'")

        if self.kernel_client:
            return self.kernel_client.dispatch(rpc_payload)
        return self._rpc_error(rid, -32001, "Kernel offline")

    def _is_valid_rpc(self, payload: dict) -> bool:
        return (
            isinstance(payload, dict)
            and payload.get("jsonrpc") == "2.0"
            and "method" in payload
        )

    def _rpc_error(self, req_id, code: int, message: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": req_id or str(uuid.uuid4())
        }


def create_gateway(series: str = "seeds", base_dir: str = "data") -> AkashaGateway:
    """
    Factory: instantiates KernelDispatcher and wraps it in AkashaGateway.
    Call this once at boot from akasha.py or api/main.py.
    """
    from lib.akasha.kernel import KernelDispatcher
    kernel = KernelDispatcher(series=series, base_dir=base_dir)
    return AkashaGateway(kernel_client=kernel)


# Lazy singleton — replaced at boot time by create_gateway()
gateway = AkashaGateway()
