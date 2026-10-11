"""
PulseRecorder — the server-side capture half of pulse analytics (docs/for-llm/pulse-analytics-spec).

A portal calls `recorder.capture(...)` once per concept view (after the response is sent). The
recorder is the seam that keeps analytics **off the critical path and out of the guest write
path**:

  • It NEVER blocks the request: `capture()` only appends to a bounded in-memory buffer and
    returns. A single background daemon thread drains the buffer and records each event by
    dispatching `pulse.emit` INTERNALLY under the system identity `system.librarian` — so a guest
    never needs (and never gets) write capability.
  • It is DROPPABLE: the buffer is a fixed-size deque; under overload the oldest pending events
    are discarded rather than growing memory or stalling. Analytics loss is not data loss (the
    volatile-layer contract). A dispatch error drops that event too.

Privacy (fixed): no PII is stored. The visitor id is a DAILY-ROTATING salted hash of
`ip‖user-agent` — the salt is regenerated each day and never persisted, so events are not
linkable across days and no durable identifier exists. `DNT: 1` skips capture entirely; bots are
labelled (not dropped) so they never inflate human figures; geo is country-only.
"""
import hashlib
import logging
import secrets
import threading
import time
from collections import deque
from typing import Callable, Optional

logger = logging.getLogger("Harmonia.PulseRecorder")

_SYSTEM_IDENTITY = "system.librarian"   # holds WRITE; internal-only, never a network login
_TRUST_INTERNAL  = "internal"
_BUFFER_MAX      = 4096                  # bounded — oldest pending events drop under overload
_DRAIN_IDLE_S    = 30.0                  # F47-1.4 — idle re-check cadence. New events wake the drainer
                                         # IMMEDIATELY via _wake.set(), so this timeout only paces the
                                         # coarse hourly-flush / daily-compact predicate checks. It was
                                         # 2 s (a wakeup every 2 s forever, each a GIL slice that widens
                                         # a concurrent render); 30 s cuts idle wakeups 15× with no effect
                                         # on drain latency or maintenance granularity (hour/day).


def _classify_ua(ua: str) -> str:
    u = (ua or "").lower()
    if any(b in u for b in ("bot", "crawl", "spider", "slurp", "bingpreview",
                            "facebookexternalhit", "embedly", "preview", "monitor")):
        return "bot"
    if any(m in u for m in ("mobile", "android", "iphone", "ipad", "ipod")):
        return "mobile"
    return "desktop" if u else "unknown"


def _classify_ref(referer: str, own_host: str = "") -> str:
    """A coarse acquisition class from the Referer header — never the full URL (no PII)."""
    r = (referer or "").strip().lower()
    if not r:
        return "direct"
    host = r.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    if own_host and (host == own_host.lower() or host.endswith("." + own_host.lower())):
        return "internal"
    for needle, label in (("google", "google"), ("github", "github"), ("bing", "bing"),
                          ("duckduckgo", "duckduckgo"), ("reddit", "reddit"),
                          ("t.co", "twitter"), ("twitter", "twitter"), ("x.com", "twitter"),
                          ("facebook", "facebook"), ("linkedin", "linkedin"),
                          ("news.ycombinator", "hackernews"), ("wikipedia", "wikipedia")):
        if needle in host:
            return label
    host = host[4:] if host.startswith("www.") else host
    return host[:48] or "direct"


class PulseRecorder:
    """Process-wide singleton. Buffers access events and records them via an internal
    system-identity dispatch on one background daemon thread."""

    def __init__(self) -> None:
        self._dispatch: Optional[Callable[[dict, str], dict]] = None
        self._buf: "deque[dict]" = deque(maxlen=_BUFFER_MAX)
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._salt = secrets.token_hex(16)
        self._salt_day = self._today()
        self._dropped = 0
        self._recorded = 0
        self._rejected = 0                  # emits the kernel REJECTED (never silent again — F16)
        self._last_reject: Optional[str] = None
        # C4/F44 — bots NEVER write a raw per-hit atom (that is the per-request permanent-RAM exhaust
        # that OOMs the writer under a crawl storm). Their hits accumulate in an in-memory per-day
        # aggregate (concept × surface × ref → count) flushed hourly as ONE summary write; only HUMANS
        # write raw per-hit atoms. Bounded: a flush is forced if the key count crosses the cap.
        self._bot_agg = {}                  # (day, concept, surface, ref) -> count
        self._bot_hits = 0
        self._bot_hour = self._hour()
        self._bot_summaries = 0
        self._BOT_AGG_MAX = 50000
        # C1/F44 — init to YESTERDAY, not today: the recorder lives in the web-portal process, which
        # respawns every deploy (and, lately, every ~15 min), so a portal born mid-day that inits
        # _compact_day=today never sees a rollover and never compacts (same bug class as F26's
        # never-called checkpoint). Seeding yesterday makes a freshly-started portal run one
        # (idempotent — already-summarised days are skipped) compaction pass. The AUTHORITATIVE
        # nightly compaction now runs writer-side (kernel _schedule_pulse_compact), boot-if-behind;
        # this portal trigger is the belt-and-suspenders.
        self._compact_day = self._yesterday()

    # ── configuration ─────────────────────────────────────────────────────────
    def configure(self, dispatch: Callable[[dict, str], dict]) -> None:
        """Attach the gateway dispatch (payload, transport_trust) and start the drainer.
        Idempotent — safe to call from every portal at boot."""
        with self._lock:
            self._dispatch = dispatch
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._drain_loop, name="pulse-recorder",
                                                daemon=True)
                self._thread.start()

    @property
    def configured(self) -> bool:
        return self._dispatch is not None

    # ── capture (called per request — must be cheap and non-blocking) ───────────
    def capture(self, concept: str, surface: str = "", referer: str = "", prev: str = "",
                ip: str = "", ua: str = "", dnt: bool = False, own_host: str = "") -> bool:
        """Enqueue one access event. Returns False (skipped/dropped) or True (buffered).
        Respects DNT; derives a within-day pseudonymous visit id server-side; never blocks."""
        if not concept or self._dispatch is None:
            return False
        if dnt:
            return False
        ev = {
            "concept": str(concept)[:160],
            "surface": (surface or "")[:32],
            "ref": _classify_ref(referer, own_host),
            "prev": str(prev or "")[:160],
            "visit": self._visit(ip, ua),
            "ua": _classify_ua(ua),
        }
        with self._lock:
            if len(self._buf) >= _BUFFER_MAX:
                self._dropped += 1     # deque maxlen already evicts oldest; count the loss
            self._buf.append(ev)
        self._wake.set()
        return True

    # ── privacy: daily-rotating salted visitor hash ─────────────────────────────
    @staticmethod
    def _today() -> str:
        return time.strftime("%Y-%m-%d", time.gmtime())

    @staticmethod
    def _yesterday() -> str:
        return time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400))

    @staticmethod
    def _hour() -> str:
        return time.strftime("%Y-%m-%dT%H", time.gmtime())

    def _visit(self, ip: str, ua: str) -> str:
        today = self._today()
        if today != self._salt_day:
            # New day → new salt → yesterday's visitors are unlinkable to today's.
            self._salt = secrets.token_hex(16)
            self._salt_day = today
        h = hashlib.sha256(f"{self._salt}|{ip}|{ua}".encode("utf-8")).hexdigest()
        return "d" + h[:15]

    # ── background drainer ──────────────────────────────────────────────────────
    def _drain_loop(self) -> None:
        while True:
            self._wake.wait(timeout=_DRAIN_IDLE_S)
            self._wake.clear()
            while True:
                with self._lock:
                    if not self._buf:
                        break
                    ev = self._buf.popleft()
                self._record(ev)
            self._maybe_flush_bots()
            self._maybe_compact()

    def _maybe_flush_bots(self) -> None:
        """Flush the bot aggregate when the UTC hour rolls over (bounded: ≤24 summary writes/day)."""
        h = self._hour()
        if h != self._bot_hour and self._bot_agg:
            self._flush_bots()
        self._bot_hour = h

    def _flush_bots(self) -> None:
        """Write the accumulated bot hits as ONE bulk summary emit and clear the aggregate — so a
        crawl storm costs a handful of atoms per day, not one per hit. Never blocks; volatile."""
        if not self._bot_agg or self._dispatch is None:
            return
        rows = [{"day": d, "concept": c, "surface": s, "ref": r, "count": n}
                for (d, c, s, r), n in self._bot_agg.items()]
        self._bot_agg = {}
        params = {"client_id": _SYSTEM_IDENTITY, "records": rows}
        payload = {"jsonrpc": "2.0", "method": "pulse.emit_bulk", "id": "pulse-bulk", "params": params}
        self._sign_internal(payload, "pulse.emit_bulk", params)
        try:
            resp = self._dispatch(payload, _TRUST_INTERNAL)
            if isinstance(resp, dict) and resp.get("error"):
                self._note_reject(resp["error"])
            else:
                self._bot_summaries += 1
        except Exception as exc:
            self._note_reject({"message": str(exc)})

    def _maybe_compact(self) -> None:
        """Nightly roll-up: when the UTC day rolls over, compact day-old raw events into per-day
        summaries once (idempotent). Driven off this always-running thread — no separate
        scheduler. Best-effort: any failure is swallowed (analytics is volatile)."""
        today = self._today()
        if today == self._compact_day or self._dispatch is None:
            return
        self._compact_day = today
        try:
            params = {"client_id": _SYSTEM_IDENTITY, "keep": 2}
            payload = {"jsonrpc": "2.0", "method": "pulse.compact", "id": "pulse-compact",
                       "params": params}
            self._sign_internal(payload, "pulse.compact", params)
            self._dispatch(payload, _TRUST_INTERNAL)
        except Exception as exc:
            logger.debug("pulse compaction skipped: %s", exc)

    def _sign_internal(self, payload: dict, method: str, params: dict) -> None:
        """Attach an HMAC over (method, params, ts) so the local socket may RAISE this analytics
        emit to `internal` trust (F16). In the split topology the emit is forwarded over the
        daemon socket, whose ceiling is `local`; without this signature the socket clamps it and
        the kernel rejects the system identity (-32001) — the silent, permanent capture loss. In
        the embedded topology there is no socket and no secret is needed; signing is a harmless
        no-op the in-process kernel ignores."""
        try:
            from api.portals.cell_ipc import sign_internal
            ts = time.time()
            sig = sign_internal(method, params, ts)
            if sig:
                payload["_sig"] = sig
                payload["_ts"] = ts
        except Exception:                   # no api layer / no secret → embedded path, no elevation
            pass

    def _note_reject(self, err) -> None:
        """A rejected emit must NEVER vanish silently again (F16). Count it, remember the last
        cause, and log at WARNING on the first drop and every 100th — one log read reveals a
        structural failure (e.g. the IPC trust clamp) instead of endless zeros."""
        self._rejected += 1
        self._last_reject = (err.get("message") if isinstance(err, dict) else str(err))
        if self._rejected == 1 or self._rejected % 100 == 0:
            logger.warning("[PulseRecorder] %d emit(s) rejected (last: %s)",
                           self._rejected, self._last_reject)

    def _record(self, ev: dict) -> None:
        # C4 — a BOT hit never becomes a raw atom: fold it into the in-memory per-day aggregate. Only
        # humans fall through to a raw per-hit emit below.
        if ev.get("ua") == "bot":
            day = self._today()
            key = (day, ev["concept"], ev["surface"], ev["ref"])
            self._bot_agg[key] = self._bot_agg.get(key, 0) + 1
            self._bot_hits += 1
            if len(self._bot_agg) >= self._BOT_AGG_MAX:
                self._flush_bots()
            return
        params = {
            "client_id": _SYSTEM_IDENTITY,
            "concept": ev["concept"], "surface": ev["surface"], "ref": ev["ref"],
            "visit": ev["visit"], "prev": ev["prev"], "ua": ev["ua"],
        }
        payload = {"jsonrpc": "2.0", "method": "pulse.emit", "id": "pulse", "params": params}
        self._sign_internal(payload, "pulse.emit", params)
        try:
            resp = self._dispatch(payload, _TRUST_INTERNAL)
            if isinstance(resp, dict) and resp.get("error"):
                self._note_reject(resp["error"])
            else:
                self._recorded += 1
        except Exception as exc:            # analytics is volatile — never propagate
            self._note_reject({"message": str(exc)})

    def stats(self) -> dict:
        # C3 — recorded (raw human emits), rejected (kernel refused — never silent, F16), dropped
        # (buffer overflow), plus the C4 bot path: bot hits folded + hourly summaries flushed.
        return {"recorded": self._recorded, "dropped": self._dropped,
                "rejected": self._rejected, "last_reject": self._last_reject,
                "buffered": len(self._buf), "configured": self.configured,
                "bot_hits": self._bot_hits, "bot_summaries": self._bot_summaries,
                "bot_pending": len(self._bot_agg)}


# Process-wide singleton.
recorder = PulseRecorder()
