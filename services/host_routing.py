"""
Host-based document-root routing for the archives portal.

One Akasha Cell can front several domains/subdomains from a single `archives/`
tree.  The apex/base domain serves `archives/index.html` (unchanged); any other
host is mapped to a same-named child directory:

    akashicarchives.net            → archives/index.html            (default)
    world.akashicarchives.net      → archives/world/index.html      (subdomain → leftmost label)
    akashickitchen.net             → archives/akashickitchen.net/…  (foreign domain → full host)

The mapping is **rule-based, not an allow-list**: adding a new site is just
`mkdir archives/<name>/` with an `index.html` — no code change.  If the target
directory does not exist the request degrades to the default archives root, so a
DNS record can be pointed here before its content is authored without 404-ing
the whole host.

Configuration:
  AKASHA_BASE_DOMAIN  — comma-separated apex domain(s) that serve the default
                        root and whose subdomains map to a leftmost-label dir.
                        Default: "akashicarchives.net".

Shared by both portals (uvicorn/ASGI in api/portals/asgi.py, httpd in
services/http_gateway.py) so the behaviour is identical whichever engine serves.
Reserved API paths (/rpc, /health, …) must be excluded by the caller — this
module only answers "which archives sub-directory does this Host map to?".
"""
import os

__all__ = ["resolve_host_dir", "base_domains"]


def base_domains():
    """The configured apex domain(s), lower-cased, no empties."""
    raw = os.environ.get("AKASHA_BASE_DOMAIN", "akashicarchives.net")
    return [d.strip().lower() for d in raw.split(",") if d.strip()]


def _strip_port(host: str) -> str:
    """Drop the :port suffix, handling IPv6 literals like [::1]:80."""
    host = host.strip().lower()
    if host.startswith("["):            # [ipv6]:port
        return host[1:].split("]", 1)[0]
    return host.split(":", 1)[0]


def _is_ip_literal(host: str) -> bool:
    # IPv6 literals were already unwrapped by _strip_port (contain ':'), and a
    # dotted-quad is all digits + dots.
    if ":" in host:
        return True
    parts = host.split(".")
    return len(parts) == 4 and all(p.isdigit() for p in parts)


def resolve_host_dir(host_header, archives_root, base=None):
    """Map a request Host header to an ``archives/<dir>`` sub-directory name.

    Returns the sub-directory name (a single safe path segment, e.g. ``"world"``
    or ``"akashickitchen.net"``) when that directory exists and has an
    ``index.html``; otherwise ``None`` (serve the default archives root).

    Never returns a value that escapes *archives_root* (path-traversal safe).
    """
    if not host_header or not archives_root:
        return None
    # A Host header is a single value, but be defensive about a stray comma.
    host = _strip_port(host_header.split(",", 1)[0])
    if not host or host == "localhost" or _is_ip_literal(host):
        return None

    bases = base if base is not None else base_domains()

    candidate = None
    for b in bases:
        if host == b or host == "www." + b:
            return None                         # apex / www → default root
        if b and host.endswith("." + b):
            sub = host[: -(len(b) + 1)]         # e.g. "world" from world.<base>
            if sub.startswith("www."):
                sub = sub[4:]
            # Only the leftmost label names the directory (world.<base>, not a.b).
            candidate = sub.split(".")[0]
            break
    if candidate is None:
        # Foreign domain → the whole host is the directory name.
        candidate = host[4:] if host.startswith("www.") else host

    if not _safe_segment(candidate):
        return None

    target = os.path.realpath(os.path.join(archives_root, candidate))
    root = os.path.realpath(archives_root)
    if target != root and not target.startswith(root + os.sep):
        return None                             # traversal guard
    if os.path.isfile(os.path.join(target, "index.html")):
        return candidate
    return None


def _safe_segment(seg: str) -> bool:
    """A single path segment: no separators, no traversal, no hidden/empty."""
    if not seg or seg in (".", ".."):
        return False
    if seg.startswith("."):
        return False
    if "/" in seg or "\\" in seg or "\x00" in seg or os.sep in seg:
        return False
    return True
