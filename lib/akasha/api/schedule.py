"""The timer registry — one mechanism, many bodies, none of them named by the heart.

A schedule body is `fn(kernel)`; it starts its own daemon thread (or does its one-shot boot work)
exactly as before. The heart runs the registered bodies of a PHASE in ascending `order`:

    load          the boot load itself — run in the "ont-boot-loader" thread at boot and again after
                  genesis (the heart's `_boot_load_ontology` seam runs this phase; evals patch it)
    writer        once per writer process, right after "Kernel online" (independent of the load)
    post_load     once per process, from the load path after the admin exists

Each phase RUN is reported, one line per body, so a boot's shape is readable without a debugger:

    [boot] phase=1:load package=ontology name=ontology_load when=new_build status=ok t=12.40s Δrss=310MB
    [boot] phase=2:writer package=heart name=wal_maintenance when=every_boot status=ok t=0.00s Δrss=0MB
    [boot] complete phase=2:writer ran=15 failed=0 t=0.42s Δrss=8MB

`when` is the body's own DECLARATION of whether its work is expected once per new build
(`new_build` — it is sentinel-gated inside) or on every boot (`every_boot`). It is a label on the
line, not a gate: this registry runs every registered body exactly as before, and the body keeps
its own sentinel. A body that raises is reported `status=error` and the phase continues — a boot
has always survived one bad schedule, and hiding that was how a silent skip went unnoticed.

A body may declare `after: "<gate>"` — a named condition it must not run before — and the body
that satisfies it declares `provides: "<gate>"`. Both are manifest entries, so the pairing is DATA:
the registry knows a gate has a producer before any phase runs, which is what stops a consumer in
the writer phase from slipping through ahead of a producer whose thread has not started. A body
whose gate is shut is reported `status=deferred reason=<gate>` and re-run, in order, the moment
`open_gate` fires. A gate NOBODY declares is open, so an eval that patches the ontology load away,
or a seed with no packs, runs its `after=` bodies at their normal place rather than waiting forever
on work nobody is doing.

    [boot] phase=2:writer package=workbench name=workload_provision when=every_boot status=deferred
           reason=ontology.loaded t=0.00s Δrss=0MB

A thread unit is a host-bound thread the thread guard re-creates when it dies: it declares a
wanted-predicate `wanted(kernel) -> bool`, the kernel attribute holding its Thread, an idempotent
starter `start(kernel)`, and its unit name — again as data, so the guard names nothing itself.
"""
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

PHASES = ("load", "writer", "post_load")
WHENS = ("new_build", "every_boot")

logger = logging.getLogger("Akasha.Kernel")


def _rss_mb():
    """This process's RSS in MB, or None off-Linux — the same reading Health takes."""
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


# ── named gates ───────────────────────────────────────────────────────────────────────────────
# A gate is a name, the set of gates already opened in this process, and the bodies waiting on
# each. A gate is SHUT while a body that declares `provides:` it has yet to call `open_gate`, and
# OPEN otherwise — including when nothing declares it at all. `provides` is read at registration,
# so the shut state exists from the first phase onward and no consumer can win a race against a
# producer that has not begun.

def _gates(kernel) -> Dict[str, Any]:
    g = getattr(kernel, "_schedule_gates", None)
    if g is None:
        g = kernel._schedule_gates = {"opened": set(), "waiting": {}, "running": set()}
    return g


def gate_open(kernel, name: str, registry=None) -> bool:
    """Is this gate open?

    A gate is shut only while a DECLARED producer has yet to open it. "Declared" means some
    schedule's manifest entry says `provides: "<gate>"` — which is known at REGISTRATION time,
    before any phase runs, and that is what removes the race: a consumer in the writer phase cannot
    slip through ahead of a producer whose thread has not started yet. A gate nobody produces is
    open, so an eval that patches the load away, or a seed with no packs, is unaffected."""
    n = str(name or "")
    g = _gates(kernel)
    if n in g["opened"]:
        return True
    reg = registry if registry is not None else getattr(getattr(kernel, "api", None), "schedules", None)
    return not (reg is not None and n in reg.provided())


def mark_running(kernel, name: str) -> None:
    """The producer announcing that its work is IN FLIGHT right now.

    Distinct from the gate being shut, and needed by a consumer that is not part of the boot
    sequence at all. A schedule body is ordered against the producer by the registry (`after:` +
    `provides:`, which is race-free because the phases are ordered); a long-lived DAEMON is not —
    its first tick happens minutes later, by which time the producer has either finished or was
    never going to run. `running` answers that second question honestly: a cell whose producer is
    patched away (an eval skipping the ontology load) has nothing in flight, so the daemon ticks
    rather than waiting on work nobody is doing."""
    _gates(kernel)["running"].add(str(name))


def is_running(kernel, name: str) -> bool:
    """Is this gate's producer working right now?"""
    return str(name or "") in _gates(kernel)["running"]


def open_gate(kernel, name: str) -> None:
    """Open a gate and run, in order, every body that was deferred on it."""
    g = _gates(kernel)
    g["opened"].add(str(name))
    g["running"].discard(str(name))
    held = g["waiting"].pop(str(name), [])
    logger.info("[boot] gate open name=%s released=%d", name, len(held))
    for bname, fn in held:
        t0 = time.time()
        status, detail = "ok", ""
        try:
            fn(kernel)
        except Exception as exc:                           # noqa: BLE001 — same contract as a phase
            status, detail = "error", "%s: %s" % (type(exc).__name__, exc)
        (logger.warning if status == "error" else logger.info)(
            "[boot] released name=%s gate=%s status=%s t=%.2fs%s",
            bname, name, status, time.time() - t0, (" detail=%s" % detail) if detail else "")


def _defer(kernel, gate: str, name: str, fn: Callable) -> None:
    _gates(kernel)["waiting"].setdefault(str(gate), []).append((name, fn))


class ScheduleRegistry:
    def __init__(self):
        self._bodies: Dict[str, Tuple[Callable, str, int, str]] = {}
        self._meta: Dict[str, Dict[str, Any]] = {}
        self._units: List[Tuple[int, str, Callable, str, Callable]] = []
        self.log: List[Dict[str, Any]] = []          # the boot report, as data (the eval reads it)

    def register(self, name: str, fn: Callable, phase: str, order: int, source: str = "",
                 when: str = "every_boot", package: str = "", after: str = "",
                 provides: str = "") -> None:
        if phase not in PHASES:
            raise ValueError(f"schedule {name!r}: unknown phase {phase!r} (one of {PHASES})")
        if when not in WHENS:
            raise ValueError(f"schedule {name!r}: unknown `when` {when!r} (one of {WHENS})")
        if name in self._bodies:
            raise ValueError(f"schedule {name!r} defined twice: {self._bodies[name][3]} and {source}")
        self._bodies[name] = (fn, phase, int(order), source)
        self._meta[name] = {"when": when, "after": str(after or ""), "provides": str(provides or ""),
                            "package": package or (source.split(":", 1)[0] if source else "")}

    def provided(self) -> set:
        """The gate names some registered body declares it PRODUCES. Known before any phase runs,
        which is what lets `gate_open` answer "shut" for a producer that has not started yet."""
        # A body may provide more than one gate (`"ontology.loaded,ontology.normalized"`): the
        # boot load opens the first when atoms + relations are in and the second when it returns.
        return {g.strip() for m in self._meta.values() if m.get("provides")
                for g in str(m["provides"]).split(",") if g.strip()}

    def meta(self, name: str) -> Dict[str, Any]:
        return dict(self._meta.get(name) or {})

    def register_unit(self, name: str, wanted: Callable, thread_attr: str, start: Callable,
                      order: int = 100) -> None:
        self._units.append((int(order), name, wanted, thread_attr, start))

    def phase(self, phase: str) -> List[Tuple[str, Callable]]:
        rows = [(order, name, fn) for name, (fn, ph, order, _s) in self._bodies.items() if ph == phase]
        return [(name, fn) for order, name, fn in sorted(rows, key=lambda r: (r[0], r[1]))]

    def run_phase(self, kernel, phase: str) -> None:
        """Run a phase's bodies in order, reporting each one. Never raises: a body that fails is
        logged `status=error` and the rest of the phase still runs."""
        n = PHASES.index(phase) + 1
        t_phase, rss_phase = time.time(), _rss_mb()
        ran = failed = 0
        for name, fn in self.phase(phase):
            meta = self._meta.get(name) or {}
            t0, rss0 = time.time(), _rss_mb()
            status, detail = "ok", ""
            gate = meta.get("after") or ""
            if gate and not gate_open(kernel, gate):
                # Held, not dropped: the body is queued against its gate and runs the moment the
                # producer opens it. Reported at INFO with the gate as its reason, because a body
                # that did not run is exactly the kind of absence that reads as "nothing happened".
                _defer(kernel, gate, name, fn)
                status, detail = "deferred", "reason=%s" % gate
            else:
                try:
                    fn(kernel)
                except Exception as exc:                   # noqa: BLE001 — a boot survives one bad body
                    status, detail, failed = "error", "%s: %s" % (type(exc).__name__, exc), failed + 1
            ran += 1
            dt = time.time() - t0
            rss1 = _rss_mb()
            drss = (rss1 - rss0) if (rss0 is not None and rss1 is not None) else None
            row = {"phase": phase, "phase_no": n, "package": meta.get("package") or "?",
                   "name": name, "when": meta.get("when") or "every_boot", "status": status,
                   "t": round(dt, 2), "rss_delta": drss, "detail": detail}
            self.log.append(row)
            (logger.warning if status == "error" else logger.info)(
                "[boot] phase=%d:%s package=%s name=%s when=%s status=%s t=%.2fs Δrss=%sMB%s",
                n, phase, row["package"], name, row["when"], status, dt,
                drss if drss is not None else "?", (" detail=%s" % detail) if detail else "")
        rssE = _rss_mb()
        total_drss = (rssE - rss_phase) if (rss_phase is not None and rssE is not None) else None
        self.log.append({"phase": phase, "phase_no": n, "name": "*", "status": "complete",
                         "ran": ran, "failed": failed, "t": round(time.time() - t_phase, 2),
                         "rss_delta": total_drss})
        logger.info("[boot] complete phase=%d:%s ran=%d failed=%d t=%.2fs Δrss=%sMB",
                    n, phase, ran, failed, time.time() - t_phase,
                    total_drss if total_drss is not None else "?")

    def units(self) -> List[Tuple[str, Callable, str, Callable]]:
        return [(n, w, a, st) for _o, n, w, a, st in sorted(self._units, key=lambda u: (u[0], u[1]))]

    def names(self) -> List[str]:
        return sorted(self._bodies)

    def get(self, name: str) -> Optional[Callable]:
        row = self._bodies.get(name)
        return row[0] if row else None
