"""
Unified cursor pagination — one page envelope for every list-returning surface.

Before this, three disjoint mechanisms limited output: a terminal `less` pager (CLI
only, scroll-based), fixed renderer truncations (`[:15]`), and per-command `items[:limit]`
first-N slices with no offset. Only the recipe model had real cursor pagination, so the
shared graph/explore commands could not page past the first window, and web/mobile
clients had no next/prev affordance at all.

`paginate()` gives every handler the SAME page envelope, so every client (CLI, web,
mobile, MCP) renders next/prev identically from the JSON:

    window, page = paginate(items, limit, cursor)
    return _ok(rid, {"items": window, "page": page})

    page = {
        "limit":       20,          # effective window size (0 = unbounded)
        "offset":      0,           # window start
        "total":       137,         # total items available
        "count":       20,          # items in this window
        "has_more":    True,        # more after this window
        "next_cursor": "20",        # pass as `cursor` for the next page (None at end)
        "prev_cursor": None,        # pass as `cursor` for the previous page (None at start)
    }

The cursor is a plain offset string — stateless, self-evident, and portable across
clients. Backward-compatible: a caller that wants the whole list passes limit=0.
"""

from typing import Any, Dict, List, Optional, Tuple


def resolve_limit(limit: Any, *, default: int = 20,
                  max_limit: Optional[int] = None) -> int:
    """Effective window size. Unspecified (None / "") → `default`. `<= 0` → 0 (unbounded,
    the caller's opt-in to the whole list). Positive values clamp to `max_limit` if given."""
    if limit is None or (isinstance(limit, str) and limit.strip() == ""):
        return default
    try:
        n = int(limit)
    except (TypeError, ValueError):
        return default
    if n <= 0:
        return 0
    return min(n, max_limit) if max_limit else n


def resolve_offset(cursor: Any) -> int:
    """Offset from a cursor (offset string). Non-numeric / negative → 0."""
    try:
        return max(0, int(cursor or 0))
    except (TypeError, ValueError):
        return 0


def paginate(items: List[Any], limit: Any = None, cursor: Any = None, *,
             default: int = 20,
             max_limit: Optional[int] = None) -> Tuple[List[Any], Dict[str, Any]]:
    """Slice `items` into a window + a page envelope (see module docstring).

    - `limit` unspecified → `default`; `<= 0` → whole remaining list (unbounded).
    - `cursor` is an offset string; the returned `next_cursor` is the offset to pass next.
    """
    total = len(items)
    off = resolve_offset(cursor)
    lim = resolve_limit(limit, default=default, max_limit=max_limit)

    if lim <= 0:                                   # unbounded — whole list from offset
        window = items[off:]
        return window, {
            "limit": 0, "offset": off, "total": total, "count": len(window),
            "has_more": False, "next_cursor": None,
            "prev_cursor": str(max(0, off - default)) if off > 0 else None,
        }

    window = items[off:off + lim]
    nxt = off + lim
    more = nxt < total
    return window, {
        "limit": lim, "offset": off, "total": total, "count": len(window),
        "has_more": more,
        "next_cursor": str(nxt) if more else None,
        "prev_cursor": str(max(0, off - lim)) if off > 0 else None,
    }
