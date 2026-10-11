"""The JSON-RPC 2.0 envelope every op returns — the heart never raises to the caller.

Key order is part of the wire shape (a client may hash or diff the raw response), so it is fixed
here: `result` before `id`; an error with no request id is given one.
"""
import uuid
from typing import Any, Dict


def ok(rid, data: Any) -> dict:
    return {"jsonrpc": "2.0", "result": data, "id": rid}


def err(rid, code: int, message: str, data: Any = None) -> dict:
    e: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "error": e, "id": rid or str(uuid.uuid4())}
