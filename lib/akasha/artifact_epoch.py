"""S1-a §1.4/§1.5 — epoch identity for DERIVED semantic artifacts (the accelerator layer).

The S1 invariant: *a materialized semantic horizon is an accelerator, never the source of semantic
truth.* A derived artifact (a stored `lens.compare` aggregate, a semcache plan, a leaderboard, an SSR
snapshot, the reference cache) is therefore identified by WHAT it was derived from and WHEN, so a
reader can tell a fresh artifact from a stale one and regenerate the stale one from canonical inputs.

Two primitives, no new storage:

- `artifact_id(...)` — a stable content identity: two artifacts with the same id ARE the same artifact
  regardless of backend (the "did we recompute the same thing" test). Includes `access_context`
  because a guest's compare and an admitted member's compare are different artifacts (F3 / R5).
- `is_stale(built_at_epoch, inputs_epoch)` — the artifact was built at `built_at_epoch`; if any input
  Set has advanced past it (`inputs_epoch` is the max last-write epoch of the inputs), the artifact is
  a stale accelerator: serve it `stale=true` while a rebuild is scheduled, or rebuild under a budget.

`epoch` here is Akasha's existing commit/coordinate sequence (the Silica `at_seq`, or a bench chronon
coordinate) — NOT wall-clock. §1.5: a bench artifact keyed by its bench chronon answers "as of which
execution" for free; a world artifact keyed by the world chronon does the same for world.sync.
"""
import hashlib
from typing import Any, Iterable, Optional


def artifact_id(universe_epoch: Any, scope: str, coordinate: Any, inputs: Iterable[str],
                transform: str, projection: str = "", access_context: str = "") -> str:
    """A stable sha256 identity for a derived artifact. `inputs` are the canonical input Set aliases
    (order-independent — sorted). Equality of ids ⇒ equality of artifacts."""
    parts = [
        "epoch=%s" % (universe_epoch if universe_epoch is not None else ""),
        "scope=%s" % (scope or ""),
        "coord=%s" % (coordinate if coordinate is not None else ""),
        "inputs=%s" % ",".join(sorted(str(x) for x in (inputs or []))),
        "transform=%s" % (transform or ""),
        "projection=%s" % (projection or ""),
        "access=%s" % (access_context or ""),
    ]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8", "replace")).hexdigest()


def is_stale(built_at_epoch: Optional[int], inputs_epoch: Optional[int]) -> bool:
    """True when the artifact's inputs have advanced past the epoch it was built at. Unknown epochs
    (either side None) are treated as NOT stale — an artifact with no recorded epoch predates epoch
    keying and is left to its own replace-on-change contract, never spuriously flagged."""
    if built_at_epoch is None or inputs_epoch is None:
        return False
    try:
        return int(inputs_epoch) > int(built_at_epoch)
    except (TypeError, ValueError):
        return False
