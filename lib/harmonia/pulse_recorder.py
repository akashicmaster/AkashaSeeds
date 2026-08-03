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
_DRAIN_IDLE_S    = 2.0                   # coalesce window: how long the drainer waits when idle


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
        self._compact_day = self._today()   # compaction runs once when the UTC day rolls over

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
            self._maybe_compact()

    def _maybe_compact(self) -> None:
        """Nightly roll-up: when the UTC day rolls over, compact day-old raw events into per-day
        summaries once (idempotent). Driven off this always-running thread — no separate
        scheduler. Best-effort: any failure is swallowed (analytics is volatile)."""
        today = self._today()
        if today == self._compact_day or self._dispatch is None:
            return
        self._compact_day = today
        try:
            self._dispatch({"jsonrpc": "2.0", "method": "pulse.compact", "id": "pulse-compact",
                            "params": {"client_id": _SYSTEM_IDENTITY, "keep": 2}}, _TRUST_INTERNAL)
        except Exception as exc:
            logger.debug("pulse compaction skipped: %s", exc)

    def _record(self, ev: dict) -> None:
        payload = {
            "jsonrpc": "2.0", "method": "pulse.emit", "id": "pulse",
            "params": {
                "client_id": _SYSTEM_IDENTITY,
                "concept": ev["concept"], "surface": ev["surface"], "ref": ev["ref"],
                "visit": ev["visit"], "prev": ev["prev"], "ua": ev["ua"],
            },
        }
        try:
            resp = self._dispatch(payload, _TRUST_INTERNAL)
            if isinstance(resp, dict) and resp.get("error"):
                logger.debug("pulse.emit rejected: %s", resp["error"])
            else:
                self._recorded += 1
        except Exception as exc:            # analytics is volatile — never propagate
            logger.debug("pulse capture dropped: %s", exc)

    def stats(self) -> dict:
        return {"recorded": self._recorded, "dropped": self._dropped,
                "buffered": len(self._buf), "configured": self.configured}


# Process-wide singleton.
recorder = PulseRecorder()
