"""
The Application API — the ONLY door into the heart (Part II §A21).

The heart (`lib/akasha/kernel.py` and the core modules) is generic: it knows no Concept Model, no
Source, no bench, no room, no programme by name. Application packages (`ontology/`, `source/`,
`concepts/`, `workbench/`) reach the heart through THIS package and nothing else, and the heart
reaches them only through what their `MANIFEST.json` declares:

    akasha.api.rpc        ok / err                                  the JSON-RPC envelope
    akasha.api.trust      TRUST_NETWORK / TRUST_LOCAL / TRUST_INTERNAL   transport trust levels
    akasha.api.ops        Req + OpsTable                            RPC ops, bound from manifests
    akasha.api.schedule   ScheduleRegistry (+ thread units)         the timer registry
    akasha.api.provision  ProvisionRegistry                         boot provisioning hooks
    akasha.api.manifest   load_manifests(...)                       the aggregator the heart boots from

A handler declares what it needs by PARAMETER NAME (rid, data, session, ctx, scopes, client_id,
history, su_key, transport_trust, raw_token, method, role) and the dispatcher binds those from the
request — no per-op adapter, no argument list to keep in sync. A manifest entry is
`"<dotted.module>:<qualname>"`; a name that does not resolve is a boot error naming the entry.

Pure Python, dependency-free (it imports no heart module), so the heart behind it may be compiled.
"""


# ── the router protocol, for code that must reach a Concept Model without importing it ──
_ACTIVE_ROUTERS = []


def set_routers(routers) -> None:
    """Record the dispatchers the manifests declared, so a module with no kernel in hand (the CSL
    validator, the thin CLI client) can still resolve a Concept Model. Called once, by the
    aggregate that built them."""
    global _ACTIVE_ROUTERS
    _ACTIVE_ROUTERS = list(routers or [])


def routers(kernel=None) -> list:
    """The active routers: the ones this kernel carries, else the process-wide ones."""
    live = getattr(getattr(kernel, "api", None), "routers", None)
    return list(live) if live else list(_ACTIVE_ROUTERS)


def discover_routers() -> list:
    """The manifests' routers, built on demand for a process that never boots a kernel (the CSL
    validator, the thin CLI client attached to a remote writer). Reads only each manifest's
    `routers` entry, so nothing else in the application layer is imported."""
    global _ACTIVE_ROUTERS
    if _ACTIVE_ROUTERS:
        return list(_ACTIVE_ROUTERS)
    import os as _os
    from . import manifest as _m
    out = []
    for path in _m.default_manifest_paths(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))):
        try:
            spec = (_m.read_manifest(path).get("routers") or {})
        except Exception:
            continue
        for name, ref in spec.items():
            ref = ref["fn"] if isinstance(ref, dict) else ref
            try:
                router = _m.resolve(ref, "%s routers.%s" % (path, name))()
            except Exception:
                continue
            if router is not None:
                out.append(router)
    _ACTIVE_ROUTERS = out
    return list(out)


def concept_class(kernel, prefix: str):
    """The Concept Model class registered under `prefix`, or None.

    The ONE way a lower layer reaches a Concept Model: it asks the router by the model's declared
    prefix instead of importing the module, so the import graph keeps its one direction
    (backend layout order 2026-09-20 §1.3)."""
    for router in routers(kernel):
        try:
            cls = router.get_class(prefix)
        except Exception:
            continue
        if cls is not None:
            return cls
    return None


def op_attr(kernel, method: str, attr: str, default=None):
    """An attribute an op declares about itself in its package's manifest (`dive_bearing`,
    `projection`, `block_branch`, …), or `default`. The heart and the mechanism ask BY ATTRIBUTE —
    "is this op dive-bearing?" — and never keep a list of method names of their own."""
    attrs = (getattr(getattr(kernel, "api", None), "op_attrs", None) or {}).get(str(method or ""))
    return (attrs or {}).get(attr, default)


def ops_with(kernel, attr: str) -> dict:
    """Every method whose manifest entry declares `attr` (truthy), mapped to its value."""
    table = getattr(getattr(kernel, "api", None), "op_attrs", None) or {}
    return {m: a[attr] for m, a in table.items() if a.get(attr)}


def implementer(kernel, point: str) -> str:
    """The method that declares it IMPLEMENTS an extension point (`"implements": "<point>"`, or a
    list of points, on its manifest entry), or "" when none does. An extension point a platform op
    forwards to is registered this way — as data on the implementing op — so the platform names
    the POINT and never the application method that fills it (group 4, 4.12(c))."""
    for method, val in ops_with(kernel, "implements").items():
        pts = val if isinstance(val, (list, tuple)) else [val]
        if str(point) in [str(p) for p in pts]:
            return method
    return ""


def hooks_all(kernel, name: str) -> list:
    """EVERY package's registration of hook `name`, in package order ([] when none). For a question
    each package answers for its own atoms."""
    return list((getattr(getattr(kernel, "api", None), "hook_lists", None) or {}).get(name) or [])


def hook(kernel, name: str):
    """A named upward call a package declared in its manifest (`hooks`), or None when no package
    provides it — the caller degrades, it never imports the package."""
    return (getattr(getattr(kernel, "api", None), "hooks", None) or {}).get(name)

