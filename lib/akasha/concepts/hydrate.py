"""S1-a §1.2 — `hydrate.*`, the ONE registry for regenerating derived accelerators.

The S1 invariant: *a materialized semantic horizon is an accelerator, never the source of semantic
truth.* Every accelerator (a derived Set, a coordinate layer, a semcache plan, a leaderboard) is
therefore REGENERABLE from canonical inputs, and this registry gives every regenerator ONE surface (the
purge order §2 deleted the migrations that used to sit here — `retention`, `cronon.migrate`: a cell
starts at Genesis and the writes keep the state live):

  - `hydrate.ls` — every accelerator: name, canonical inputs, the op that regenerates it, its
    `layer_v` (the R1 lesson — idempotence keys on the version stamp, never a coincidental field),
    the boot policy, and the epoch it was last regenerated at.
  - `hydrate.run name= [since_epoch=]` — regenerate one accelerator (idempotent, bounded), logging
    `[hydrate] <name> from=<epoch> assigned=<n> t=…s Δrss=…MB`, and record the run epoch.
  - `hydrate.verify [name=]` — re-run a regeneration and report the delta (expected 0 assigned on an
    already-hydrated accelerator: the cheap production probe that the accelerator still equals its
    regeneration).

The registry is DATA (the HORIZON inventory in code form); it dispatches the existing regenerators
rather than duplicating them. `hydrate.*` is librarian/admin — regeneration is a writer-role act.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts._universal import UniversalConcept

logger = logging.getLogger("akasha.kernel")

# The kernel wires itself here at boot (like workflow.set_active_kernel), so a hydrate entry can reach
# the SECURED dispatch path (an RPC regenerator) or a kernel-level regenerator (the retention backfill).
_ACTIVE_KERNEL = None


def set_active_kernel(kernel) -> None:
    global _ACTIVE_KERNEL
    _ACTIVE_KERNEL = kernel


# The HORIZON inventory, as data. `method` is an internal RPC; `kernel_call` a kernel method; either
# absent ⇒ the accelerator is regenerated ONLY at boot (in-RAM, no on-demand op) and `run` reports so.
# `boot_verify` (H1) is how the boot pass touches the entry: "run" re-runs the (cheap, idempotent)
# regenerator through the registry and records the result; "record" stamps the epoch WITHOUT re-running
# (for a regenerator whose first pass is owned elsewhere and must not repeat — the O(store) retention
# scan, the daily semcache replan, the in-RAM boot index).
_REGISTRY: List[Dict[str, Any]] = [
    {"name": "semcache_plan", "layer_v": 1, "on_boot": "rebuild", "boot_verify": "record",
     "inputs": "set:stage:featured + pulse demand",
     "method": "cache.replan", "assigned_key": "planned", "droppable": True,
     "desc": "the semantic macro-cache plan (residency by membership; the daily replan owns the rebuild)"},
    {"name": "boot_index", "layer_v": 1, "on_boot": "rebuild", "boot_verify": "record",
     "inputs": "the Silica store under data/ (atoms/links/Sets)",
     "assigned_key": None, "droppable": False,
     "desc": "the in-RAM index rebuilt from disk at boot (accelerator, never the truth)"},
    {"name": "leaderboard", "layer_v": 1, "on_boot": "verify", "boot_verify": "run",
     "inputs": "set:wb:<b>:sweep:<s>:evaluations (per sweep, indexed by set:wb:sweeps:all)",
     "regen": "manifest", "assigned_key": "rebuilt", "droppable": True,
     "desc": "the sweep leaderboards — a lens.rank projection of each sweep's evaluations Set, "
             "rebuilt when an evaluation lands (learning.evaluate) and verified/repaired at boot (S2-l)"},
]


# An APPLICATION accelerator is declared by its OWNER, on the op that regenerates it (group 4,
# 4.13): `"hydrate": {"name": …, "layer_v": …, "on_boot": …, "boot_verify": …, "inputs": …,
# "assigned_key": …, "droppable": …, "desc": …}` on the op's manifest entry. The registry is this
# platform table plus every op that declares one; the platform names no application regenerator.
_ENTRY_DEFAULTS = {"layer_v": 1, "on_boot": "rebuild", "boot_verify": "run", "inputs": "",
                   "assigned_key": "assigned", "droppable": True, "desc": ""}


def _registry() -> List[Dict[str, Any]]:
    out = list(_REGISTRY)
    seen = {e["name"] for e in out}
    attrs = getattr(getattr(_ACTIVE_KERNEL, "api", None), "op_attrs", None) or {}
    for method in sorted(attrs):
        decl = (attrs.get(method) or {}).get("hydrate")
        if not isinstance(decl, dict) or not decl.get("name") or decl["name"] in seen:
            continue
        e = dict(_ENTRY_DEFAULTS)
        e.update(decl)
        e["method"] = method
        seen.add(e["name"])
        out.append(e)
    return out


class HydrateConcept(UniversalConcept):
    """Regeneration registry for the accelerator layer (S1-a §1.2)."""

    CONCEPT_PREFIX = "hydrate"
    CONCEPT_METHODS = {
        "ls":     {"op": "op_ls", "action": "read",
                   "desc": "List every regenerable accelerator with its inputs / regen op / layer_v / "
                           "boot policy / last-run epoch: hydrate.ls"},
        "run":    {"op": "op_run", "action": "record",
                   "desc": "Regenerate one accelerator (idempotent, bounded): hydrate.run name= "
                           "[since_epoch=]"},
        "verify": {"op": "op_verify", "action": "record",
                   "desc": "Re-run a regeneration and report the delta (expected 0 on an already-"
                           "hydrated accelerator): hydrate.verify [name=]"},
        "boot_pass": {"op": "op_boot_pass", "action": "record",
                      "desc": "Execute every entry's boot policy once (internal, writer boot)."},
    }

    # ── vault (last-run epoch) — the shared nucleus, or the local store on a single-store cell ──
    def _vault(self):
        return self._nuc if self._nuc is not None else self.cortex

    def _last_run(self, name: str) -> Dict[str, Any]:
        try:
            return self._vault().vault_retrieve("hydrate", name) or {}
        except Exception:
            return {}

    def _record_run(self, name: str, epoch: Any, assigned: Any) -> None:
        try:
            self._vault().vault_store("hydrate", name, {
                "name": name, "epoch": epoch, "assigned": assigned, "wall": round(time.time(), 3)})
        except Exception:
            pass

    def _universe_epoch(self) -> Optional[int]:
        """The current universe epoch — the shared Akasha-Time counter (a monotonic commit coordinate).
        Used as the `from=`/run epoch; a bench-scoped accelerator would key on its chronon (§1.5)."""
        try:
            return int(self._akasha_now())
        except Exception:
            return None

    def _entry(self, name: str) -> Optional[Dict[str, Any]]:
        for e in _registry():
            if e["name"] == name:
                return e
        return None

    def op_ls(self) -> Dict[str, Any]:
        """[hydrate.ls] The HORIZON registry: every accelerator, its canonical inputs, the op that
        regenerates it, its layer_v, its boot policy, and the epoch it was last regenerated at."""
        rows = []
        for e in _registry():
            lr = self._last_run(e["name"])
            rows.append({"name": e["name"], "inputs": e["inputs"], "desc": e["desc"],
                         "regenerate": e.get("method") or e.get("kernel_call")
                                       or ("manifest:hydrate.%s" % e["name"] if e.get("regen") == "manifest" else "boot-only"),
                         "layer_v": e["layer_v"], "on_boot": e["on_boot"], "droppable": e["droppable"],
                         "last_run_epoch": lr.get("epoch"), "last_assigned": lr.get("assigned")})
        return {"accelerators": rows, "count": len(rows), "universe_epoch": self._universe_epoch()}

    def _regenerate(self, e: Dict[str, Any], since_epoch: str = "") -> Dict[str, Any]:
        """Run the entry's regenerator (RPC or kernel call) and return its result dict. None-method
        entries (boot-only, e.g. the in-RAM index) return a boot_only marker."""
        if _ACTIVE_KERNEL is None:
            return {"status": "unavailable", "note": "kernel not wired"}
        if e.get("method"):
            data = {"since_epoch": since_epoch} if since_epoch else {}
            resp = _ACTIVE_KERNEL.dispatch(
                {"jsonrpc": "2.0", "method": e["method"],
                 "params": {"client_id": "system.librarian", "data": data}, "id": "hyd"}, "internal")
            if isinstance(resp, dict) and resp.get("error"):
                return {"status": "error", "error": resp["error"]}
            return (resp or {}).get("result") or {}
        if e.get("regen") == "manifest":
            # the owning package declares the regenerator in its MANIFEST.json `hydrate` map
            fn = (getattr(getattr(_ACTIVE_KERNEL, "api", None), "hydrate_fns", None) or {}).get(e["name"])
            if callable(fn):
                try:
                    return fn(_ACTIVE_KERNEL) or {}
                except Exception as exc:
                    return {"status": "error", "error": str(exc)}
            return {"status": "unavailable", "note": "no package declares hydrate.%s" % e["name"]}
        if e.get("kernel_call"):
            fn = getattr(_ACTIVE_KERNEL, e["kernel_call"], None)
            if callable(fn):
                try:
                    return fn() or {}
                except Exception as exc:
                    return {"status": "error", "error": str(exc)}
            return {"status": "unavailable", "note": "no kernel call %s" % e["kernel_call"]}
        return {"status": "boot_only", "note": "regenerated at boot (in-RAM), no on-demand op"}

    def op_run(self, name: str = "", since_epoch: str = "") -> Dict[str, Any]:
        """[hydrate.run] Regenerate one accelerator from canonical inputs. Idempotent + bounded; logs
        `[hydrate] <name> from=<epoch> assigned=<n> t=…s Δrss=…MB` and records the run epoch."""
        if not name:
            raise ValueError("hydrate.run requires name= (see hydrate.ls)")
        e = self._entry(name)
        if e is None:
            raise ValueError("unknown accelerator '%s' (see hydrate.ls)" % name)
        try:
            from lib.akasha import memtrace as _mt
            _rss0 = _mt._rss_mb()
        except Exception:
            _mt, _rss0 = None, None
        _from = since_epoch or (self._last_run(name).get("epoch"))
        t0 = time.time()
        res = self._regenerate(e, since_epoch=since_epoch)
        assigned = res.get(e["assigned_key"]) if e.get("assigned_key") else None
        _rss1 = _mt._rss_mb() if _mt is not None else None
        _dr = round(_rss1 - _rss0, 1) if (_rss0 is not None and _rss1 is not None) else "?"
        epoch = self._universe_epoch()
        logger.info("[hydrate] %s from=%s assigned=%s t=%.1fs Δrss=%sMB status=%s",
                    name, _from if _from is not None else "-", assigned if assigned is not None else "-",
                    time.time() - t0, _dr, res.get("status", "ok"))
        if res.get("status") not in ("error", "unavailable"):
            self._record_run(name, epoch, assigned)
        return {"name": name, "regenerated": True, "assigned": assigned, "epoch": epoch,
                "status": res.get("status", "ok"), "result": res}

    def op_verify(self, name: str = "") -> Dict[str, Any]:
        """[hydrate.verify] Re-run one (or every droppable) accelerator's regeneration and report the
        delta — an already-hydrated accelerator regenerates with `assigned=0`, the cheap production
        probe that the accelerator still equals its regeneration (§1.3). Never drops anything."""
        names = [name] if name else [e["name"] for e in _registry() if e["droppable"]]
        out = []
        for n in names:
            e = self._entry(n)
            if e is None:
                out.append({"name": n, "status": "unknown"}); continue
            res = self._regenerate(e)
            assigned = res.get(e["assigned_key"]) if e.get("assigned_key") else None
            _ok = res.get("status") not in ("error", "unavailable")
            if _ok:
                self._record_run(n, self._universe_epoch(), assigned)   # H1 — verify records the epoch
            out.append({"name": n, "assigned": assigned, "verified": _ok and (assigned in (0, None)),
                        "status": res.get("status", "ok")})
            logger.info("[hydrate.verify] %s assigned=%s status=%s", n,
                        assigned if assigned is not None else "-", res.get("status", "ok"))
        return {"verified": out, "count": len(out)}

    def op_mark(self, name: str = "") -> Dict[str, Any]:
        """[hydrate.mark] H1 (internal) — record that an accelerator was regenerated at boot by its own
        one-time/boot-owned path (the O(store) retention scan, the daily semcache replan, the in-RAM
        index) WITHOUT re-running it. Stamps last_run_epoch so no entry reads null after the boot pass."""
        e = self._entry(name)
        if e is None:
            raise ValueError("unknown accelerator '%s'" % name)
        epoch = self._universe_epoch()
        self._record_run(name, epoch, None)
        logger.info("[hydrate] %s boot=%s recorded epoch=%s", name, e.get("on_boot"), epoch)
        return {"name": name, "recorded": True, "epoch": epoch}

    def op_boot_pass(self) -> Dict[str, Any]:
        """[hydrate.boot_pass] H1 — execute each entry's boot policy through the registry ONCE per boot:
        `boot_verify=run` re-runs the (cheap, idempotent) regenerator and records it; `boot_verify=
        record` stamps the epoch without re-running. So after boot NO entry reads last_run_epoch=null and
        the log carries one `[hydrate]`/`[hydrate.verify]` line per entry. Internal (writer boot only)."""
        done = []
        for e in _registry():
            n = e["name"]
            try:
                if e.get("boot_verify") == "run":
                    r = self.op_verify(name=n)
                    _asg = (r.get("verified") or [{}])[0].get("assigned")
                    # H1-b — ONE log shape for all five: emit the `[hydrate] <name> boot=… recorded
                    # epoch=` line for the re-run entries too (they also log their own regenerator line +
                    # `[hydrate.verify]`, but the unified boot line now appears for every accelerator).
                    logger.info("[hydrate] %s boot=%s recorded epoch=%s assigned=%s", n, e.get("on_boot"),
                                self._last_run(n).get("epoch"), _asg if _asg is not None else "-")
                    done.append({"name": n, "mode": "run", "assigned": _asg})
                else:
                    self.op_mark(name=n)
                    done.append({"name": n, "mode": "record"})
            except Exception as exc:
                logger.debug("[hydrate] boot pass entry %s skipped: %s", n, exc)
        return {"boot_pass": done, "count": len(done)}
