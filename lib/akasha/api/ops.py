"""RPC ops — the dispatch table the heart builds from the manifests.

An op is any function `fn(kernel, <named parameters>)`. It declares what it needs by PARAMETER
NAME, drawn from the request vocabulary below; the table binds those names from the `Req` at
call time, once per op at registration (an unknown name is a boot error naming the op). This is
what lets a handler move from the kernel class into a package module without an adapter: the
same signature, minus `self`, plus the manifest line.

    rid, method, data, session, ctx, scopes, client_id, history, su_key, transport_trust,
    raw_token, role

`stage` says WHERE in the request path the op runs — declared data, not an `if` on a name:

    pre_identity   before the identity is resolved (ping, status, auth.*, guest sessions)
    post_identity  with the resolved identity, before the capability check (whoami)
    pre_su         under the real identity, before `su` elevation is applied
    pre            after su/ctx resolution, before the Concept Model registry is consulted
    post           after the registry (the registry wins a name it handles)
"""
import inspect
from typing import Any, Callable, Dict, List, Optional

STAGES = ("pre_identity", "post_identity", "pre_su", "pre", "post")
REQ_FIELDS = ("rid", "method", "data", "session", "ctx", "scopes", "client_id", "history",
              "su_key", "transport_trust", "raw_token", "role")
# a handler may name the caller's identity `real_client_id` (the su handler does): same field
_ALIASES = {"real_client_id": "client_id"}


class Req:
    """One request, as the dispatcher has resolved it so far. Fields not yet resolved are None."""
    __slots__ = REQ_FIELDS

    def __init__(self, **kw):
        for f in REQ_FIELDS:
            setattr(self, f, kw.get(f))


class Entry:
    __slots__ = ("name", "fn", "stage", "access", "params", "source")

    def __init__(self, name: str, fn: Callable, stage: str, access: Optional[str], source: str):
        if stage not in STAGES:
            raise ValueError(f"op {name!r}: unknown stage {stage!r} (one of {STAGES})")
        self.name, self.fn, self.stage, self.access, self.source = name, fn, stage, access, source
        params: List[str] = []
        sig = inspect.signature(fn)
        for i, (pname, p) in enumerate(sig.parameters.items()):
            if i == 0:
                continue                       # the kernel (self)
            if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                raise ValueError(f"op {name!r}: *args/**kwargs are not bindable ({source})")
            field = _ALIASES.get(pname, pname)
            if field not in REQ_FIELDS:
                raise ValueError(f"op {name!r}: parameter {pname!r} is not a request field ({source})")
            params.append(field)
        self.params = params

    def call(self, kernel, req: Req):
        # THE DECLARED TARGET (directive 2026-10-02 §6.4). An op whose manifest entry declares
        # `target` is asked again WITH the place before it runs — the boundary only asked the
        # action. Declared as data on the op; nothing here names a method.
        attrs = (getattr(getattr(kernel, "api", None), "op_attrs", None) or {}).get(self.name)
        if attrs and attrs.get("target") and req.client_id is not None:
            from lib.akasha.api import targets as _targets
            ok, why, tgt = _targets.check(kernel, str(req.client_id or ""), str(self.access or ""),
                                          attrs, req.data if isinstance(req.data, dict) else {},
                                          req.session)
            if not ok:
                from lib.akasha.api import gate as _gate
                _gate.refuse_log(str(req.client_id or ""), str(self.access or ""), tgt, why)
                return {"jsonrpc": "2.0", "id": req.rid,
                        "error": {"code": -32001, "message": "%s: %s %s on %s"
                                  % (req.client_id, why, self.access, tgt)}}
        return self.fn(kernel, *[getattr(req, f) for f in self.params])


class OpsTable:
    """name → Entry, with the stage order fixed. `resolve(name, stage)` answers only for that stage."""

    def __init__(self):
        self._entries: Dict[str, Entry] = {}

    def register(self, name: str, fn: Callable, stage: str = "post", access: Optional[str] = None,
                 source: str = "") -> Entry:
        if name in self._entries:
            prev = self._entries[name]
            raise ValueError(f"op {name!r} defined twice: {prev.source} and {source}")
        e = Entry(name, fn, stage, access, source)
        self._entries[name] = e
        return e

    def get(self, name: str) -> Optional[Entry]:
        return self._entries.get(name)

    def resolve(self, name: str, stage: str) -> Optional[Entry]:
        e = self._entries.get(name)
        return e if (e is not None and e.stage == stage) else None

    def names(self) -> List[str]:
        return sorted(self._entries)

    def __len__(self):
        return len(self._entries)

    def __contains__(self, name):
        return name in self._entries
