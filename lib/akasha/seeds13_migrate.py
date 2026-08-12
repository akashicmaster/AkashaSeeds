"""
seeds13 migration — derive `responsible:chairman` from legacy `society:decider` (R3).

seeds13 generalises the old single `society:decider` (society→cast) into the Agent/Responsible
model: a chairman is `responsible:chairman` society→**agent** (a cast admitted to the society),
and the delegation gate reads a `chairman_client`. Pre-seeds13 societies only have the decider
link. This migration mints an agent binding for each such decider cast and adds the
`responsible:chairman` link, **non-destructively** (the decider link is kept) and **without**
granting delegation to an unknown client — `chairman_client` is left empty, so until the cast's
owner rebinds, only an admin retains the two delegated powers. Idempotent: re-running skips a
society that already has a chairman.

**R3 — boot-once behind a completion sentinel (the F6 isomorph).** A migration that re-scans every
group on every boot is the same OOM-replay trap the F6 sentinel closed for the global-relations
phase. So the whole pass is gated on a fsync'd filesystem sentinel: present ⇒ skip entirely.
Content-address idempotency is NOT enough — the sentinel stops the *scan*, not just the writes.
"""
import glob
import hashlib
import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger("Akasha.seeds13.migrate")

SENTINEL_NAME = "seeds13_decider_chairman.done"


def _sentinel_path(base_dir: str) -> str:
    return os.path.join(base_dir, SENTINEL_NAME)


def _sentinel_present(base_dir: str) -> bool:
    return os.path.exists(_sentinel_path(base_dir))


def _write_sentinel(base_dir: str, summary: dict) -> None:
    """Write the completion sentinel and fsync it — filesystem durability does not depend on any
    DB backend (the crash-stop principle: sentinels are fsync'd files, not just DB rows)."""
    path = _sentinel_path(base_dir)
    try:
        os.makedirs(base_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(json.dumps({"done_at": time.time(), **summary}, ensure_ascii=False))
            fp.flush()
            os.fsync(fp.fileno())
    except OSError as exc:
        logger.warning("[seeds13.migrate] could not write sentinel %s: %s", path, exc)


def _meta(ge, key: str) -> dict:
    row = ge.core.get_chunk_raw(key) or {}
    try:
        return json.loads(row.get("meta") or "{}")
    except Exception:
        return {}


def _cast_slug(cast_name: str, cast_id: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "_", (cast_name or "").lower()).strip("_")
    return slug or (cast_id or "")[:8]


def _migrate_group(ge, gid: str) -> int:
    """Derive chairmen for one group's legacy societies. Returns the number derived."""
    derived = 0
    for society_key in list(ge.core.get_collection_members(f"societies:{gid}") or []):
        m = _meta(ge, society_key)
        if m.get("concept") != "society":
            continue
        # already has a chairman? skip (idempotent)
        if ge.core.get_adjacent_links(society_key, "responsible:chairman"):
            continue
        decider = next((l.get("dst") for l in ge.core.get_adjacent_links(society_key, "society:decider")), "")
        if not decider:
            continue
        space = m.get("name", "main")
        cast_id = decider
        cname = _meta(ge, cast_id).get("name", "")
        slug = _cast_slug(cname, cast_id)
        # mint the agent binding (content-addressed on agent|sid|cast — matches society.py)
        sid = f"{gid}/{space}"
        content = f"[ Agent: {cname or slug} in {sid} ]\x00{cast_id}"
        ameta = {"type": "agent", "concept": "agent", "group": gid, "space": space, "sid": sid,
                 "cast": cast_id, "cast_name": cname, "cast_slug": slug, "client": "",
                 "created_by": "system.migrate", "created_at": time.time(),
                 "derived_from": "society:decider"}
        akey = hashlib.sha256(content.encode("utf-8")).hexdigest()
        ge.core.put_chunk_raw(akey, content, json.dumps(ameta, ensure_ascii=False),
                              "system.migrate", "verified", time.time())
        ge.core.put_chunk_access(akey, [ge.scope])
        ge.core.put_alias(akey, f"agent:{gid}:{space}:{slug}")
        ge.put_link(akey, cast_id, "agent:as")
        ge.put_link(akey, society_key, "agent:in")
        agents_set = f"soc:{gid}:agents" if space == "main" else f"soc:{gid}:{space}:agents"
        ge.core.add_to_collection(agents_set, akey)
        # add the responsible:chairman link (chairman_client left empty — no unknown-client delegation)
        ge.put_link(society_key, akey, "responsible:chairman")
        derived += 1
    return derived


def migrate_deciders_to_chairman(base_dir: str, force: bool = False) -> dict:
    """Boot-once (sentinel-gated) derivation across every group under base_dir/groups/*. Best-effort
    and safe to call on every boot: it returns immediately when the sentinel is present. Never
    raises — a migration failure must not block boot."""
    if not force and _sentinel_present(base_dir):
        return {"status": "skipped", "reason": "sentinel present"}
    try:
        from lib.akasha.composite import GroupEngine
    except Exception as exc:            # pragma: no cover
        logger.warning("[seeds13.migrate] GroupEngine unavailable: %s", exc)
        return {"status": "error", "reason": str(exc)}
    groups_dir = os.path.join(base_dir, "groups")
    total, groups = 0, 0
    if os.path.isdir(groups_dir):
        for gpath in sorted(glob.glob(os.path.join(groups_dir, "*"))):
            gid = os.path.basename(gpath)
            if not os.path.exists(os.path.join(gpath, "g_space.db")):
                continue
            ge = None
            try:
                ge = GroupEngine(gid, base_dir)
                n = _migrate_group(ge, gid)
                total += n
                groups += 1
                if n:
                    logger.info("[seeds13.migrate] group '%s': derived %d chairman(s) from decider", gid, n)
            except Exception as exc:
                logger.warning("[seeds13.migrate] group '%s' failed: %s", gid, exc)
            finally:
                if ge is not None:
                    try:
                        ge.close()
                    except Exception:
                        pass
    summary = {"status": "done", "groups": groups, "derived": total}
    _write_sentinel(base_dir, summary)
    return summary
