"""
DECLARED TARGETS — the second half of the gate's question, for every op that declares one.

`kernel.dispatch` asks `gate(identity, <action>)`: it knows the method, not what the call is about.
An op that writes somewhere names WHERE in a parameter, and declares which one — so the gate can be
asked again WITH the place (step 3, "on this target"). The Concept Model registry has done this since
4.17 (`target` in a `CONCEPT_METHODS` spec, `CONCEPT_TARGET_ARG` on the class); a MANIFEST op did not
ask at all, so an op such as the analysis projection writer was gated by its action alone
(directive 2026-10-02 §6.4: "the ops take the target").

What an op declares, as data — on its manifest entry or its `CONCEPT_METHODS` spec:

    "target":          the parameter that names the place ("bench", "pool", …)
    "target_kind":     how that value becomes a place — `bench` (a bench name → `wb:<slug>` for a
                       public bench, `<gid>/wb:<slug>` for a group bench: the spelling an assignment
                       line uses), or absent (the value IS the place)
    "target_required": true → a call WITHOUT the parameter is refused `out_of_scope`. For an op
                       that would otherwise write to a fixed universal namespace when the caller
                       says nothing, which is the door this closes.

Nothing here names an application method or a package: a kind is resolved by the Concept Model
that DECLARES the prefix (`bench` → the platform's workbench model, found by prefix).
"""
from typing import Any, Dict, Optional, Tuple

KIND_BENCH = "bench"
KINDS = (KIND_BENCH,)


def resolve(kernel, kind: str, value: str, session=None) -> str:
    """The place `value` names, for a target of `kind` — the string a gate question and an
    assignment line both use. An unknown or absent kind returns the value unchanged."""
    v = str(value or "").strip()
    if kind == KIND_BENCH and v:
        try:
            from lib.akasha import api as _api
            cls = _api.concept_class(kernel, KIND_BENCH)
            if cls is not None and hasattr(cls, "gate_target"):
                sess = session or kernel.manager.get_session("admin")
                return str(cls(sess).gate_target(v))
        except Exception:
            pass
        return v if v.startswith("wb:") else "wb:%s" % v
    return v


def declared(attrs: Optional[Dict[str, Any]]) -> Tuple[str, str, bool]:
    """(param, kind, required) an op declares — ("", "", False) when it declares no target."""
    a = attrs or {}
    return (str(a.get("target") or ""), str(a.get("target_kind") or ""),
            a.get("target_required") is True)


def check(kernel, who: str, action: str, attrs: Optional[Dict[str, Any]], data: Optional[dict],
          session=None) -> Tuple[bool, str, str]:
    """Ask the gate about the op's declared target. Returns (ok, reason, target).

    No declared target → (True, "", ""). A declared, REQUIRED target that is absent → refused
    `out_of_scope` with the param named. A declared optional target that is absent asks nothing
    (the op's own shape error, if any, is the op's to raise — as the registry has always done)."""
    param, kind, required = declared(attrs)
    if not param or not action:
        return True, "", ""
    from lib.akasha.api import gate as _gate
    raw = (data or {}).get(param)
    raw = "" if raw is None else str(raw).strip()
    if not raw:
        if required:
            return False, _gate.R_TARGET, "(no %s=)" % param
        return True, "", ""
    target = resolve(kernel, kind, raw, session)
    if action == _gate.RUN:
        # `run` over a PLACE asks reach only (step 3). The run facts — declared · armed ·
        # source_ready · headroom — are facts about a WORKLOAD, keyed by its key, and the driver and
        # admission ask them with that key; a bench or a pool is not a workload key, so asking them
        # of one refuses every job (`declared`). Every other action keeps its facts (publish still
        # needs the place in `public`).
        ok, why = _gate.gate(who, action, None, place=target)
    else:
        ok, why = _gate.gate(who, action, target)
    return ok, why, target
