"""
The canonical labs' registration — a PASS op that a declared workload runs (`app/config/workbench/workloads/labo_register.json`).

It was a boot thread (`schedule_labo_register`) that waited on a kernel-private readiness predicate and dispatched as
admin. Now it is ONE bounded, idempotent pass, run as the workload's client: each lab in `app/scripts/labo_register.LABS`
becomes a `labo:<name>` namespace (`labo.new`) and BINDS the pool / concept / society it names when that resource is
present on this cell (`labo.bind origin=registered`). A resource that lands later (a corpus imported after the first
pass) is bound by a later pass — the repeating trigger is the self-healing each boot used to give.

  labo.register.pass bench=<own bench>
"""
import logging

from lib.akasha.api.rpc import ok as _ok, err as _err
from app.concepts.precompute import _as_caller

logger = logging.getLogger("Akasha.Kernel")


def handle_labo_register_pass(kernel, rid, data, session) -> dict:
    bench = str((data or {}).get("bench") or "").strip()
    if not bench:
        return _err(rid, -32602, "labo.register.pass requires bench= (the workload's own bench)")
    try:
        from app.scripts.labo_register import LABS
    except Exception as exc:
        return _err(rid, -32002, "the lab table is unavailable: %s" % exc)
    d = _as_caller(kernel, session)
    registered = bound = refused = 0
    per = {}
    for lab in LABS:
        r = d("labo.new", {"name": lab["name"], "about": lab.get("about", ""), "scope": lab.get("scope", "public")})
        if isinstance(r, dict) and "__error__" in r:
            refused += 1
            per[lab["name"]] = "refused: %s" % str((r["__error__"] or {}).get("message", ""))[:80]
            continue
        registered += 1
        bind = {"name": lab["name"]}
        for kind in ("pool", "concept", "society"):
            ref = lab.get(kind)
            if ref and (d("read", {"id": ref}) or {}).get("content"):
                bind[kind] = ref
        if len(bind) > 1:
            br = d("labo.bind", dict(bind, origin="registered"))
            if isinstance(br, dict) and "__error__" in br:
                refused += 1
                per[lab["name"]] = "bind refused: %s" % str((br["__error__"] or {}).get("message", ""))[:80]
                continue
            bound += len(bind) - 1
        per[lab["name"]] = "registered"
    logger.info("[labo.register.pass] caller=%s bench=%s labs=%d bindings=%d refused=%d",
                session.client_id, bench, registered, bound, refused)
    return _ok(rid, {"labs": registered, "bindings": bound, "refused": refused, "per_lab": per, "bench": bench})
