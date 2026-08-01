"""
OntologyReconciler — retire atoms a pack no longer contributes, WITHOUT a data wipe.

Pack re-import is additive (content-addressed, idempotent): it applies additions and edits but
never purges atoms deleted from a pack. This module adds the missing half — removal — as the
data-side analog of the seed's code prune (reproductor prune_stale, which retires seed-managed
files no longer shipped while protecting user assets). It is fenced so it can NEVER touch user
knowledge. Full spec: docs/for-llm/ontology-reconciliation-spec.md.

  RETIRE a key ONLY IF   meta.provenance == "ontology"
                   AND   it carries no user access scope (owner:* / view:* / *user_*)
                   AND   no still-enabled pack still owns it (meta.pack ref-count is empty)

Retirement is SOFT by default (evict_chunk → status "evicted"): reads treat an evicted atom as
gone, but the row survives — a mistaken retire is recoverable and re-adding the pack un-evicts it
(the load path re-writes the atom → status back to live). Hard physical deletion (drop_chunk) is a
separate, superuser-only opt-in vacuum, never on the automatic path.

State (durable, universal, in the nucleus):
  ont:pack:members:<name>   a collection of the atom KEYS the pack contributed on its last load.
  atom meta                 provenance="ontology", pack=[<name>, …]  (ref-count across packs).

The link/alias/set-membership cleanup for a retired key is RECONSTRUCTED from the live graph at
retire time (its own aliases, its OUTGOING links, its set memberships) rather than from a stored
per-edge ledger — the graph is the exact current state, and a retired atom's own edges are the
pack's to remove. Incoming links from OTHER atoms are left intact (soft-evict handles the dangle;
a user reference is surfaced as a warning, never hard-dropped).
"""
import json
from typing import Any, Dict, List, Optional, Set

# Access scopes that mark an atom as user-owned/shared — its presence makes an atom untouchable,
# no matter what its provenance says (defence in depth against a content-collision).
_USER_SCOPE_PREFIXES = ("owner:", "view:", "user:")
# Sets whose membership the reconciler must NOT touch during cleanup — the reconciler's own
# ledgers (managed by the ledger rewrite) and phase sentinels.
_LEDGER_SET_PREFIXES = ("ont:pack:", "ont:ak:", "ws:", "wf:")

PROVENANCE_ONTOLOGY = "ontology"


def _ledger_set(pack: str) -> str:
    return f"ont:pack:members:{pack}"


class OntologyReconciler:
    """Diff a pack's old member-ledger against its new contribution and retire what it dropped.

    `store` is a write-capable engine over the shared/universal layer (the nucleus engine): it
    must expose evict_chunk / remove_link / delete_alias and a `.core` backend with
    get_chunk_raw / get_chunk_access_scopes / get_aliases_by_key / get_adjacent_links /
    get_incoming_links / get_collections_for_key / add_to_collection / remove_from_collection /
    get_collection_members / update_meta. All mutators are WriteQueue-serialised (crash-stop).
    """

    def __init__(self, store: Any):
        self.store = store
        self.core = store.core

    # ── provenance + ledger ──────────────────────────────────────────────────
    def _has_user_scope(self, key: str) -> bool:
        try:
            scopes = self.core.get_chunk_access_scopes(key) or []
        except Exception:
            return True                      # unknown → treat as protected (fail-safe)
        return any(s.startswith(_USER_SCOPE_PREFIXES) or "user_" in s for s in scopes)

    def _meta(self, key: str) -> Optional[dict]:
        row = self.core.get_chunk_raw(key)
        if not row:
            return None
        try:
            return json.loads(row["meta"]) if row["meta"] else {}
        except Exception:
            return {}

    def stamp_provenance(self, pack: str, keys: List[str]) -> int:
        """Mark each pack-contributed atom `provenance="ontology"` and append `pack` to its
        owner list (ref-count). Skips any key that carries a user access scope (never mutate a
        user atom that content-collided into a pack key). Idempotent. Returns count stamped."""
        # Fast path: one-transaction batch on the backend (an fsync per atom would make an 8k-atom
        # pack's stamp glacial). Falls back to the per-key path if the backend lacks it.
        batch = getattr(self.core, "stamp_pack_provenance", None)
        if batch:
            try:
                return batch(list(keys), pack)
            except Exception:
                pass
        n = 0
        for key in keys:
            if not key or self._has_user_scope(key):
                continue
            meta = self._meta(key)
            if meta is None:
                continue
            owners = meta.get("pack")
            owners = list(owners) if isinstance(owners, list) else ([owners] if owners else [])
            changed = False
            if meta.get("provenance") != PROVENANCE_ONTOLOGY:
                meta["provenance"] = PROVENANCE_ONTOLOGY
                changed = True
            if pack not in owners:
                owners.append(pack)
                meta["pack"] = owners
                changed = True
            elif meta.get("pack") != owners:
                meta["pack"] = owners
                changed = True
            if changed:
                try:
                    self.core.update_meta(key, meta)
                    n += 1
                except Exception:
                    pass
        return n

    def read_ledger(self, pack: str) -> Set[str]:
        try:
            return set(self.core.get_collection_members(_ledger_set(pack)) or [])
        except Exception:
            return set()

    def _write_ledger(self, pack: str, new_keys: Set[str]) -> None:
        """Incremental, idempotent rewrite of the pack member-ledger (crash-stop: called LAST,
        after retirement, so a kill mid-retire just re-runs the whole diff on resume)."""
        old = self.read_ledger(pack)
        lset = _ledger_set(pack)
        for k in old - new_keys:
            try: self.core.remove_from_collection(lset, k)
            except Exception: pass
        for k in new_keys - old:
            try: self.core.add_to_collection(lset, k)
            except Exception: pass

    # ── fence ────────────────────────────────────────────────────────────────
    def retirable(self, key: str) -> bool:
        """The safety fence: retire ONLY a live, ontology-provenance atom with no user scope."""
        row = self.core.get_chunk_raw(key)
        if not row:
            return False
        if row["status"] == "evicted":
            return False                     # already retired
        meta = self._meta(key) or {}
        if meta.get("provenance") != PROVENANCE_ONTOLOGY:
            return False
        if self._has_user_scope(key):
            return False
        return True

    def _user_referrers(self, key: str) -> List[str]:
        """Non-ontology atoms that link TO `key` — a user reference the operator should see
        before the concept disappears (soft-evict leaves the edge dangling, never hard-drops)."""
        out: List[str] = []
        try:
            incoming = self.core.get_incoming_links(key, limit=200) or []
        except TypeError:
            incoming = self.core.get_incoming_links(key) or []
        except Exception:
            incoming = []
        for link in incoming:
            src = link.get("src")
            if not src or src == key:
                continue
            m = self._meta(src) or {}
            if m.get("provenance") != PROVENANCE_ONTOLOGY:
                out.append(src)
        return out

    # ── retire ───────────────────────────────────────────────────────────────
    def retire(self, key: str) -> Dict[str, int]:
        """Soft-retire a fenced key: evict the atom, and remove ITS OWN pack-owned aliases,
        outgoing links, and set memberships (reconstructed from the live graph). Incoming links
        are left intact (a dangling edge to an evicted node is handled by the read path)."""
        counts = {"aliases": 0, "links": 0, "sets": 0}
        # All mutators are WriteQueue-serialised backend primitives on `self.core` (evict /
        # delete_alias / remove_link_raw / remove_from_collection) — the NucleusEngine exposes
        # only `.core`, and going straight to it keeps every retire op on the crash-stop path.
        # aliases the pack registered for this atom
        for alias in (self.core.get_aliases_by_key(key) or []):
            try:
                self.core.delete_alias(alias); counts["aliases"] += 1
            except Exception:
                pass
        # outgoing links (includes canon/lexeme derived edges: <food> sys:is_a ingredient,
        # <proto> sys:is_a lexeme) so no derived edge is left pointing FROM the retired atom
        for link in (self.core.get_adjacent_links(key) or []):
            dst, rel = link.get("dst"), link.get("rel")
            if dst and rel:
                try:
                    self.core.remove_link_raw(key, dst, rel); counts["links"] += 1
                except Exception:
                    pass
        # set memberships (meal:all, drink:all, leaf:*, ns:* …) — but not the reconciler's own
        # ledgers/sentinels, which are managed by the ledger rewrite.
        for sname in (self.core.get_collections_for_key(key) or []):
            if sname.startswith(_LEDGER_SET_PREFIXES):
                continue
            try:
                self.core.remove_from_collection(sname, key); counts["sets"] += 1
            except Exception:
                pass
        # soft-evict last: the atom vanishes from reads; the row (and thus recovery) survives.
        try:
            self.core.update_chunk_status(key, "evicted", None)
        except Exception:
            pass
        return counts

    # ── the reconcile step ───────────────────────────────────────────────────
    def reconcile(self, pack: str, new_keys: Set[str], dry_run: bool = True) -> Dict[str, Any]:
        """Diff the pack's old ledger against `new_keys` and retire what it dropped —
        ref-counted (a key still owned by another pack is kept) and fenced (only ontology
        provenance, no user scope). `dry_run=True` reports without mutating anything except the
        ref-count decrement bookkeeping is ALSO withheld on a dry run (pure preview)."""
        new_keys = {k for k in new_keys if k}
        old = self.read_ledger(pack)
        gone = old - new_keys

        report: Dict[str, Any] = {
            "pack": pack, "dry_run": dry_run,
            "old_count": len(old), "new_count": len(new_keys), "gone_count": len(gone),
            "retired": [], "kept_shared": [], "skipped_fenced": [], "user_ref_warnings": [],
        }

        for key in sorted(gone):
            meta = self._meta(key)
            if meta is None:
                continue                     # already physically gone
            owners = meta.get("pack")
            owners = list(owners) if isinstance(owners, list) else ([owners] if owners else [])
            remaining = [p for p in owners if p != pack]
            if remaining:
                # another enabled pack still contributes this content-addressed key → keep it,
                # just drop THIS pack from the owner list.
                report["kept_shared"].append(key)
                if not dry_run and remaining != owners:
                    meta["pack"] = remaining
                    try: self.core.update_meta(key, meta)
                    except Exception: pass
                continue
            if not self.retirable(key):
                report["skipped_fenced"].append(key)
                if not dry_run and owners:   # clear the now-empty owner list bookkeeping
                    meta["pack"] = []
                    try: self.core.update_meta(key, meta)
                    except Exception: pass
                continue
            refs = self._user_referrers(key)
            if refs:
                report["user_ref_warnings"].append({"key": key, "referrers": refs[:20]})
            report["retired"].append(key)
            if not dry_run:
                self.retire(key)

        if not dry_run:
            self._write_ledger(pack, new_keys)
        return report

    def compact(self, requester_scopes: List[str], pack: Optional[str] = None) -> Dict[str, Any]:
        """Superuser-only vacuum: HARD-drop already-evicted ontology-provenance atoms. Never on
        the automatic path. Scans the ledger(s) is not enough (evicted atoms have left the
        ledger), so this walks evicted rows via the backend and drops the fenced ones."""
        out = {"dropped": [], "denied": False}
        if not requester_scopes or ("role:superuser" not in requester_scopes
                                    and "scope:sys:admin" not in requester_scopes):
            out["denied"] = True
            return out
        try:
            evicted = self.core.get_keys_by_status("evicted") if hasattr(
                self.core, "get_keys_by_status") else []
        except Exception:
            evicted = []
        for key in evicted:
            meta = self._meta(key) or {}
            if meta.get("provenance") != PROVENANCE_ONTOLOGY or self._has_user_scope(key):
                continue
            try:
                self.core.drop_chunk(key); out["dropped"].append(key)
            except Exception:
                pass
        return out
