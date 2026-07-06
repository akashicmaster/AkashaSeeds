"""
GuestPool — Pre-allocated, recycling pool for guest sessions.

Up to `size` session slots are reserved at startup with fixed IDs
("guest:pool:0" … "guest:pool:{size-1}").  Sessions are created lazily
on first checkout and kept warm between visits to avoid repeated
SQLiteBackend init overhead.

Slot lifecycle:
  checkout()  → claim free slot, return slot_id
  touch()     → renew inactivity timer on every request
  reclaim()   → free slot, clear transient session state
  _sweep_once → background daemon reclaims slots idle > TTL seconds

Configurable via environment:
  AKASHA_GUEST_POOL_SIZE  (default: 20)
  AKASHA_GUEST_TTL        (default: 600 seconds = 10 minutes)
"""
import threading
import time
import logging
from typing import Callable, List, Optional

logger = logging.getLogger("Harmonia.GuestPool")

_SENTINEL = 0.0   # activity == 0.0 means slot is free


class GuestPool:
    """
    Thread-safe reservation table for guest session slots.

    Mutation methods (checkout, touch, reclaim) hold a lock briefly.
    The sweeper runs as a daemon thread and is the only writer outside
    of the main-thread mutation methods.
    """

    def __init__(self, size: int = 20, ttl: int = 600,
                 on_reclaim: Optional[Callable[[str], None]] = None):
        """
        size      — maximum number of simultaneous guest sessions
        ttl       — inactivity timeout in seconds (default 600 = 10 min)
        on_reclaim — called with slot_id when a slot is reclaimed
        """
        self.size = size
        self.ttl  = ttl
        self._on_reclaim = on_reclaim

        # slot_id → last_activity timestamp (0.0 = free)
        self._activity: dict = {f"guest:pool:{i}": _SENTINEL for i in range(size)}
        self._lock = threading.Lock()

        t = threading.Thread(target=self._sweep_loop, daemon=True,
                             name="guest-pool-sweeper")
        t.start()
        logger.info("[GuestPool] Initialized — %d slots, TTL=%ds", size, ttl)

    @property
    def slot_ids(self) -> List[str]:
        return list(self._activity.keys())

    # ── Slot operations ───────────────────────────────────────────────────────

    def checkout(self) -> Optional[str]:
        """
        Claim a free slot.  Returns the slot_id or None if the pool is full.
        If the slot was previously used, the warm session is reused automatically
        (the manager keeps it in its sessions dict between visits).
        """
        now = time.time()
        with self._lock:
            for slot_id, last in self._activity.items():
                if last == _SENTINEL:
                    self._activity[slot_id] = now
                    logger.debug("[GuestPool] Checked out %s", slot_id)
                    return slot_id
        logger.warning("[GuestPool] Pool exhausted — all %d slots in use", self.size)
        return None

    def touch(self, slot_id: str) -> bool:
        """
        Renew the inactivity timer for a slot.
        If the slot was reclaimed (swept) but the token is still valid,
        re-activates the slot so the warm session continues to be used.
        Returns False if slot_id is not a pool slot.
        """
        if slot_id not in self._activity:
            return False
        with self._lock:
            self._activity[slot_id] = time.time()
        return True

    def reclaim(self, slot_id: str) -> None:
        """
        Mark a slot free and invoke the on_reclaim callback (clears transient state).
        The underlying AkashaSession stays in the manager's session dict — warm
        for the next visitor who checks out this slot.
        """
        with self._lock:
            if self._activity.get(slot_id, _SENTINEL) == _SENTINEL:
                return   # already free
            self._activity[slot_id] = _SENTINEL
        logger.debug("[GuestPool] Reclaimed %s", slot_id)
        if self._on_reclaim:
            try:
                self._on_reclaim(slot_id)
            except Exception as exc:
                logger.warning("[GuestPool] on_reclaim error for %s: %s", slot_id, exc)

    def is_active(self, slot_id: str) -> bool:
        """True if the slot is currently checked out."""
        return self._activity.get(slot_id, _SENTINEL) != _SENTINEL

    def stats(self) -> dict:
        with self._lock:
            in_use = sum(1 for v in self._activity.values() if v != _SENTINEL)
        return {
            "pool_size": self.size,
            "in_use":    in_use,
            "free":      self.size - in_use,
            "ttl":       self.ttl,
        }

    # ── Background sweeper ─────────────────────────────────────────────────────

    def _sweep_loop(self) -> None:
        interval = max(30, self.ttl // 4)
        while True:
            time.sleep(interval)
            self._sweep_once()

    def _sweep_once(self) -> None:
        deadline = time.time() - self.ttl
        expired  = []
        with self._lock:
            for slot_id, last in self._activity.items():
                if last != _SENTINEL and last < deadline:
                    self._activity[slot_id] = _SENTINEL
                    expired.append(slot_id)
        for slot_id in expired:
            logger.info("[GuestPool] TTL expired — reclaiming %s", slot_id)
            if self._on_reclaim:
                try:
                    self._on_reclaim(slot_id)
                except Exception as exc:
                    logger.warning("[GuestPool] on_reclaim sweep error: %s", exc)
