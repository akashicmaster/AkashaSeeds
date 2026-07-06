"""
Custom API routes for the Cosmos sub-service.

Registered automatically by app_server.py when launched as:
    python -m services.app_server --app cosmos --port 8081
"""
from api.gateway import gateway


def cosmos_sync_handler(req_data: dict) -> dict:
    """
    Returns a combined dive.look snapshot for the Cosmos graph viewer.
    dive.look now includes 'cosmos' (ForceGraph3D nodes+links), 'associations',
    'resonance', and 'signposts' — no separate explore call needed.
    session_token is validated upstream by _execute_custom_handler.
    """
    session_token = req_data.get("session_token", "")
    target        = req_data.get("target", "")
    axis          = req_data.get("axis")
    scope         = req_data.get("scope")

    params: dict = {"id": target}
    if axis:  params["axis"]  = axis
    if scope: params["scope"] = scope

    dive_res = gateway.dispatch({
        "jsonrpc": "2.0",
        "method":  "dive.look",
        "params":  {"session_token": session_token, "data": params},
        "id":      "cosmos-dive",
    })
    if "error" in dive_res:
        return dive_res

    return {"dive": dive_res.get("result", {})}


ROUTES = {
    "/api/cosmos/sync": ("POST", cosmos_sync_handler),
}
