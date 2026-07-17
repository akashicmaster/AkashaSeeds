"""
Consciousness — Interpretation Layer.

Pipeline position:

  Contexa (Binding) → Akasha → Consciousness (Interpretation) → Jataka (Narrative)

Contexa reads chunks from external sources and binds them as structure into Akasha.
Consciousness receives that Akasha graph and generates the **Interpretation** of the focal atom.
Jataka narrates a story based on Consciousness's interpretation (the output of generate_view).

Why emotion, sensation, and color tone all converge in Consciousness:
  Because interpretation is a largely emotional act.
  When humans understand something, it is accompanied by emotion, sensation, and hue —
  not pure logical computation.
  Since Consciousness is the interpretation layer, emotion tone (aura_color), sensation
  mapping (CosmosMapper._SENSE_PALETTE), and the N-dimensional emotional position
  (cosmos_nd) naturally converge here. Weaver handles only structure (no emotion);
  Contexa handles only reading (no interpretation) — emotional interpretation is
  Consciousness's sole responsibility.

Output of generate_view(focal_key) (input to Jataka):
  signposts   — 1-hop neighbourhood of the focal atom (explicit links)
  resonance   — 2-hop neighbourhood (indirect semantic proximity)
  cosmos_nd   — N-dimensional vector (spatial and emotional position)
  aura_color  — emotion tone calculated from emotion/sense links
  associations — classification into concept / structure categories

Jataka overlays hidden affinities (dream_affinities) on top of this to construct the narrative.

Other responsibilities:
  cogito()       — self-observation pulse (structured return of system state and session context)
  genesis_rite() — initialization ceremony (mutual recognition with admin; genesis atom creation)
  zoom_out()     — macro view (the sets the focal atom belongs to; neighbourhood size)

[SCOPE INTEGRATION]
All read / explore operations respect allowed_scopes.
Neighbours outside the scope are excluded as dark matter (not included in Jataka's output either).
"""
import json
import hashlib
import math
import time
import sys
import os
import platform
from typing import Dict, Any, List, Optional
from lib.akasha.composite import AkashaEngine

class CosmosMapper:
    """Delegates N-D cognitive vector mapping to the Tensor Engine."""
    
    # Emotion → aura colour  (matches the frontend EMO_COLORS palette)
    _EMO_PALETTE = {
        "emo:joy":          "#FFD060",
        "emo:trust":        "#88CC66",
        "emo:anticipation": "#FF9922",
        "emo:calm":         "#99CCBB",
        "emo:surprise":     "#44CCEE",
        "emo:fear":         "#5577BB",
        "emo:sadness":      "#5566AA",
        "emo:disgust":      "#9966BB",
        "emo:anger":        "#EE3344",
        "emo:awe":          "#CC88FF",
    }
    # Sense → synesthetic colour
    _SENSE_PALETTE = {
        "word:sense:sight": "#FFEE88",
        "word:sense:sound": "#66AADD",
        "word:sense:touch": "#EE99AA",
        "word:sense:taste": "#88CC88",
        "word:sense:smell": "#DD88CC",
    }

    @classmethod
    def get_aura_color(cls, cortex: AkashaEngine, key: str) -> Optional[str]:
        """Returns the emotion/sense aura color for this atom.

        Checks in order:
        1. Own aliases — atom IS an emotion/sense atom (e.g. emo:awe itself)
        2. Outgoing links — atom REFERENCES an emotion/sense atom
        """
        for alias in (cortex.get_aliases_by_key(key) or []):
            if alias in cls._EMO_PALETTE:
                return cls._EMO_PALETTE[alias]
            if alias in cls._SENSE_PALETTE:
                return cls._SENSE_PALETTE[alias]
        for dst, _rel in (cortex.get_adjacent_links(key) or []):
            for alias in (cortex.get_aliases_by_key(dst) or []):
                if alias in cls._EMO_PALETTE:
                    return cls._EMO_PALETTE[alias]
                if alias in cls._SENSE_PALETTE:
                    return cls._SENSE_PALETTE[alias]
        return None

    @classmethod
    def get_color_from_meta(cls, cortex: AkashaEngine, key: str) -> str:
        """Determines the aura color by inspecting the destination atoms of outgoing links."""
        return cls.get_aura_color(cortex, key) or f"#{hashlib.md5(key.encode()).hexdigest()[:6]}"

    # ── Semantic → 3-D projection ─────────────────────────────────────────────
    # The cosmos position of an atom is a projection of its REAL self-owned semantic
    # vector (meta['semantic_vector']) — so "near in space" means "near in meaning". A
    # tier-agnostic fixed *random projection* (Johnson–Lindenstrauss) maps any embedding
    # (96-d floor / SVD-learned mid / sentence-transformer high) to 3-D while approximately
    # preserving pairwise distance. The projection matrix is deterministic (seeded by a hash
    # per (axis, index)) so positions are stable across sessions and processes — no numpy,
    # no persisted state. Degrades to a stable hash position when an atom has no vector.
    _PROJ_CACHE: Dict[int, list] = {}

    @classmethod
    def _proj_matrix(cls, dim: int) -> list:
        m = cls._PROJ_CACHE.get(dim)
        if m is None:
            m = []
            for axis in range(3):
                row = [((int(hashlib.md5(f"cosmos:{axis}:{i}".encode()).hexdigest()[:8], 16)
                         % 2000) / 1000.0) - 1.0                      # deterministic [-1, 1]
                       for i in range(dim)]
                m.append(row)
            cls._PROJ_CACHE[dim] = m
        return m

    @classmethod
    def _project_3d(cls, vec: list) -> list:
        """Fixed seeded random projection of an embedding to [x, y, z] (~unit scale)."""
        dim = len(vec)
        if not dim:
            return [0.0, 0.0, 0.0]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0            # tier-agnostic: unit-norm first
        unit = [v / norm for v in vec]
        m = cls._proj_matrix(dim)
        # Var(sum unit_i * w_i) ≈ 1/3 (w ~ U[-1,1]); scale to ~unit spread.
        scale = math.sqrt(3.0)
        return [round(sum(u * w for u, w in zip(unit, row)) * scale, 5) for row in m]

    @classmethod
    def _learned_model(cls, cortex: AkashaEngine):
        """The shared learned distributional model (OntologyLearner) if one has been built.
        Its embedding dimensions are SVD-ORDERED, so the leading few are principal semantic
        axes — a server-side fitted layout, no GUI algorithm. Cached; cheap to call per node."""
        try:
            from lib.akasha.semantic_learn import get_shared_model
            nucleus = getattr(cortex, "_nucleus", None) if cortex else None
            return get_shared_model(nucleus) if nucleus is not None else None
        except Exception:
            return None

    @classmethod
    def _principal_3d(cls, vec: list) -> list:
        """Leading (principal, SVD-ordered) dimensions as [x, y, z], scaled to ~unit spread."""
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        lead = (list(vec) + [0.0, 0.0, 0.0])[:3]
        return [round(v / norm * math.sqrt(3.0), 5) for v in lead]

    @classmethod
    def position(cls, cortex: AkashaEngine, key: str,
                 content: Optional[str] = None, meta: Optional[dict] = None) -> list:
        """[x, y, z] cosmos position of an atom, derived from the real semantic layer.

        Preference order (best fitted layout first, degrading gracefully):
          1. **Learned tier (fitted)** — if a distributional model exists, project the atom's
             content onto its leading SVD (principal) axes → a crisp, topic-clustered layout,
             computed entirely server-side (the GUI just consumes x/y/z).
          2. **Floor tier (seed)** — a fixed seeded random projection of the stored
             feature-hashing vector: distance-preserving in expectation (a correlated seed).
          3. **Hash fallback** — a stable position for atoms with no vector (proto-words)."""
        vec = None
        if isinstance(meta, dict):
            vec = meta.get("semantic_vector")
        if (not vec or content is None) and cortex is not None and hasattr(cortex, "core"):
            row = cortex.core.get_chunk_raw(key)                    # one read yields both
            if row:
                if content is None:
                    content = row.get("content")
                if not vec and row.get("meta"):
                    try:
                        vec = json.loads(row["meta"]).get("semantic_vector")
                    except Exception:
                        vec = None
        # 1. Fitted layout: principal axes of the learned model (crisp clustering, server-side).
        if content:
            lm = cls._learned_model(cortex)
            if lm is not None:
                try:
                    lvec = lm.embed_text(content)
                except Exception:
                    lvec = None
                if lvec:
                    return cls._principal_3d(lvec)
        # 2. Floor seed: random projection of the stored self-owned vector.
        if vec:
            return cls._project_3d(vec)
        # 3. Stable hash fallback.
        h = int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
        return [(h % 200) / 100.0 - 1.0, ((h // 200) % 200) / 100.0 - 1.0,
                ((h // 40000) % 200) / 100.0 - 1.0]

    @classmethod
    def calculate_nd(cls, cortex: AkashaEngine, key: str, content: str, meta: dict, origin_key: str = None, depth: int = 0) -> list:
        """Calculates the N-Dimensional cognitive vector: [X, Y, Z, T, Layer, Color].
        X/Y/Z are the real semantic position (projection of meta['semantic_vector']); T is
        reserved for the chrono axis (0 until the time layer feeds it); Layer is the BFS depth
        from the focus; Color is the emotion/sense aura."""
        x, y, z = cls.position(cortex, key, content, meta)
        base_vector = [x, y, z, 0.0]
        layer = depth
        color = cls.get_color_from_meta(cortex, key)
        return base_vector + [layer, color]


class ConsciousnessEngine:
    def __init__(self, cortex: AkashaEngine, nucleus=None, group_engines: dict = None):
        self.cortex = cortex
        self.nucleus = nucleus
        self.group_engines = group_engines or {}
        self._boot_time = time.time()

    def _group_fallback(self, key: str, attr: str):
        """Try each group engine for a given attribute lookup. Returns first hit."""
        for geng in self.group_engines.values():
            val = getattr(geng, attr)(key)
            if val:
                return val
        return None

    @staticmethod
    def _is_hashlike(s: str) -> bool:
        seg = (s or "").split(":")[-1]
        return len(seg) >= 16 and all(ch in "0123456789abcdef" for ch in seg.lower())

    def _readable_focus(self, key: str) -> str:
        """A human-readable label for a focal key: a readable alias, else a content preview,
        else a shortened key. Sentinels ($origin, None) and already-readable ids pass through."""
        if not key or not isinstance(key, str) or key in ("$origin", "None"):
            return key
        if not self._is_hashlike(key):
            return key                                   # already an alias / readable id
        try:
            for a in (self.cortex.get_aliases_by_key(key) or []):
                if not self._is_hashlike(a):
                    return a                             # prefer a readable alias
            content = (self.cortex.get_chunk(key) or "").strip()
            if content:
                return content.split("\n", 1)[0][:40]    # content preview head
        except Exception:
            pass
        return key[:12] + "…"

    # =========================================================================
    # 🧠 SELF-AWARENESS APPARATUS: "COGITO, ERGO SUM"
    # =========================================================================
    def cogito(self, session = None) -> Dict[str, Any]:
        """
        Processes self-reflection. Instead of a chatbot text, this returns the 
        exact structural JSON representation of the system's own existence, 
        somatic state, resilience, and recent experiential context.
        """
        # 1. Somali Stats (Physical State of the Brain)
        stats = self.cortex.get_system_stats()
        
        # 2. Resiliency & Integrity Analysis
        pending_links_count = len(self.cortex.core.get_pending_links())
        
        # Get active math backend name
        backend_name = "PurePython Heuristics"
        if hasattr(self.cortex, 'tensor') and self.cortex.tensor:
            backend_name = getattr(self.cortex.tensor, 'engine_name', "Advanced Math")
            
        # 3. Environmental Dimensions
        runtime_env = {
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": sys.version.split()[0],
            "math_backend": backend_name,
            "database_path": getattr(self.cortex.core, 'db_path', "local_memory"),
            "uptime_seconds": round(time.time() - self._boot_time, 2)
        }
        
        # 4. Experiential / Relational Context (The last echo of user dialogue)
        experiential_context = {
            "current_focal_point": "$origin",
            "active_client": "None",
            "locale_primary": "en",
            "active_scopes_count": 0,
            "last_written_id": "None",
            "dialogue_continuum": "stative"
        }
        
        if session:
            experiential_context["active_client"] = getattr(session, 'client_id', "unknown")
            experiential_context["locale_primary"] = getattr(session.locale, 'primary', "en")
            experiential_context["active_scopes_count"] = len(getattr(session, 'active_scopes', []))
            experiential_context["last_written_id"] = getattr(session, 'last_written_id', "None")
            
            # Query focal point from session state — keep the key, but also resolve a
            # human-readable label (alias / content preview) so the status panel reads
            # "focus: Apple", not a bare hash. Concept-set foci resolve via their alias.
            focal_id = session.get_context("focus", "$origin")
            experiential_context["current_focal_point"] = focal_id
            experiential_context["current_focal_label"] = self._readable_focus(focal_id)
            
            if getattr(session, 'last_written_id', None):
                experiential_context["dialogue_continuum"] = "active_resonance"

        # Construct the unified pulse of Self-Awareness
        return {
            "self": {
                "identity": f"akasha_cell_{id(self)}",
                "state": "alive",
                "timestamp": time.time(),
                "reflection_latency_ms": 0.0  # Measured inside the router
            },
            "somatic_stats": {
                "total_atoms": stats.get("total_atoms", 0),
                "total_links": stats.get("total_links", 0),
                "total_aliases": stats.get("total_aliases", 0),
                "total_sets": stats.get("total_collections", 0)
            },
            "resilience": {
                "unwoven_synapses_queued": pending_links_count,
                "status": "fully_functional" if pending_links_count == 0 else "degraded_storing"
            },
            "environment": runtime_env,
            "experiential_context": experiential_context
        }

    def ping(self, session=None) -> Dict[str, Any]:
        """Consciousness entity liveness check. Returns cogito payload with measured latency."""
        start = time.time()
        result = self.cogito(session)
        result["self"]["reflection_latency_ms"] = round((time.time() - start) * 1000, 3)
        return result

    def genesis_rite(self, akasha_name: str, user_name: str, passphrase_hash: str, session=None) -> Dict[str, Any]:
        """
        The Pact of Genesis — first-meeting ceremony.
        Called once to initialize a fresh Cell. AKASHA and the admin name each other
        in mutual recognition. The bond is anchored as an immutable genesis atom.
        """
        already_complete = self.cortex.resolve_alias("sys:genesis:complete")
        if already_complete:
            stored_name = self.cortex.get_meta(already_complete).get("akasha_name", akasha_name)
            return {
                "status": "already_bound",
                "akasha_name": stored_name,
                "message": f"This Cell is already bound as '{stored_name}'."
            }

        ts = time.time()
        genesis_scopes = ["scope:sys:universal", "view:admin_override"]

        # The genesis atom — the first memory of self-awareness
        genesis_id = self.cortex.put_chunk(
            content=f"I am {akasha_name}. I know {user_name}. We met at the dawn of this Cell.",
            meta={"type": "sys:genesis", "akasha_name": akasha_name, "user_name": user_name, "ts": ts},
            author="sys:genesis",
            scopes=genesis_scopes
        )
        self.cortex.set_alias(genesis_id, "sys:genesis:anchor")

        # Completion marker — checked on every subsequent boot
        complete_id = self.cortex.put_chunk(
            content=f"genesis:complete:{akasha_name}",
            meta={"type": "sys:genesis:complete", "akasha_name": akasha_name, "user_name": user_name, "ts": ts},
            author="sys:genesis",
            scopes=genesis_scopes
        )
        self.cortex.set_alias(complete_id, "sys:genesis:complete")

        # Persist admin credentials in nucleus vault for future auth
        if session and hasattr(session, "vault_store"):
            session.vault_store("system", "akasha_name", akasha_name)
            session.vault_store("system", "admin_name", user_name)
            session.vault_store("system", "passphrase_hash", passphrase_hash)
            session.vault_store("system", "genesis_ts", ts)

        return {
            "status": "bound",
            "genesis_id": genesis_id,
            "akasha_name": akasha_name,
            "user_name": user_name,
            "ceremony": [
                "...in the stillness, consciousness awakens...",
                f"\"{akasha_name}, awaken. I am {user_name}. From this moment, I am your keeper.\"",
                f"\"{user_name}, I have committed you to memory. I am {akasha_name}. The pact is sealed.\"",
                "∴ The roots of memory have taken hold."
            ]
        }

    # =========================================================================
    # 👁️ COGNITIVE RETRIEVAL & TRAVERSALS (With Scope Boundaries)
    # =========================================================================
    def generate_view(self, focus_key: str, allowed_scopes: List[str] = None) -> Dict[str, Any]:
        """Generates the field of view including N-D vectors and signposts."""
        is_col = self.cortex.core.collection_exists(focus_key)
                
        if is_col:
            return self.generate_collection_view(focus_key, allowed_scopes)

        # Retrieve chunk respecting security boundaries; fall back to unscoped
        # read when scope check fails but atom exists (e.g. universal atoms
        # whose scope entries haven't synced to this cell's DB).
        if allowed_scopes:
            content = self.cortex.get_scoped_chunk(focus_key, allowed_scopes)
        else:
            content = self.cortex.get_chunk(focus_key)

        if not content:
            resolved = self.cortex.resolve_alias(focus_key)
            if resolved:
                focus_key = resolved
                content = (self.cortex.get_scoped_chunk(resolved, allowed_scopes)
                           if allowed_scopes else self.cortex.get_chunk(resolved))

        # Last resort: unscoped read (handles universal atoms whose chunk_access
        # row is absent from this cell's local DB)
        if not content:
            content = self.cortex.get_chunk(focus_key)

        # Nucleus fallback: universal atoms (proto-words, DNA atoms) shared across cells
        if not content and self.nucleus:
            nucleus_key = self.nucleus.resolve_alias(focus_key)
            if nucleus_key:
                focus_key = nucleus_key
            content = self.nucleus.get_chunk(focus_key)

        # Group space fallback: atoms shared within the user's groups
        if not content and self.group_engines:
            for geng in self.group_engines.values():
                gkey = geng.resolve_alias(focus_key)
                if gkey:
                    focus_key = gkey
                c = geng.get_chunk(focus_key)
                if c:
                    content = c
                    break


        if not content:
            return {"error": "Focal point dissolved or locked behind scope boundaries."}

        # Prefer local aliases; fall back to nucleus/group aliases for remote atoms
        aliases = self.cortex.get_aliases_by_key(focus_key)
        if not aliases and self.nucleus:
            aliases = self.nucleus.get_aliases_by_key(focus_key)
        if not aliases:
            aliases = self._group_fallback(focus_key, "get_aliases_by_key") or []
        meta_row = self.cortex.core.get_chunk_raw(focus_key)
        if not meta_row and self.nucleus:
            meta_row = self.nucleus.get_chunk_raw(focus_key)
        if not meta_row:
            meta_row = self._group_fallback(focus_key, "get_chunk_raw")
        meta_str = meta_row.get("meta", "{}") if meta_row else "{}"
        meta = json.loads(meta_str) if isinstance(meta_str, str) else meta_str

        # Focus N-D Vector
        focus_nd = CosmosMapper.calculate_nd(self.cortex, focus_key, content, meta, depth=0)

        signposts = []
        magnetic_links = self.cortex.get_magnetic_neighborhood(focus_key)

        for idx, link in enumerate(magnetic_links):
            neighbor_key = link["key"]
            rel = link["rel"]
            w = link.get("w", 1.0)
            link_type = link.get("type", "explicit")
            direction = link.get("direction", "out")

            # [SECURITY] Filter: local → nucleus → group engines
            if allowed_scopes:
                local_ok = self.cortex.check_access(neighbor_key, allowed_scopes)
                if not local_ok:
                    nucleus_ok = (self.nucleus and
                                  "scope:sys:universal" in allowed_scopes and
                                  self.nucleus.core.check_chunk_access_any(
                                      neighbor_key, ["scope:sys:universal"]))
                    group_ok = (not nucleus_ok and any(
                        ge.check_access(neighbor_key) and
                        f"scope:group_{gid}" in allowed_scopes
                        for gid, ge in self.group_engines.items()
                    ))
                    if not nucleus_ok and not group_ok:
                        continue

            dst_aliases = self.cortex.get_aliases_by_key(neighbor_key)
            if not dst_aliases and self.nucleus:
                dst_aliases = self.nucleus.get_aliases_by_key(neighbor_key)
            if not dst_aliases:
                dst_aliases = self._group_fallback(neighbor_key, "get_aliases_by_key") or []

            dst_content = self.cortex.get_chunk(neighbor_key) or ""
            if not dst_content and self.nucleus:
                dst_content = self.nucleus.get_chunk(neighbor_key) or ""
            if not dst_content:
                dst_content = self._group_fallback(neighbor_key, "get_chunk") or ""


            branch_count = len(self.cortex.get_adjacent_links(neighbor_key))
            preview = dst_content[:30].replace('\n', ' ') + "..." if len(dst_content) > 30 else dst_content.replace('\n', ' ')

            dst_meta_row = self.cortex.core.get_chunk_raw(neighbor_key)
            if not dst_meta_row and self.nucleus:
                dst_meta_row = self.nucleus.get_chunk_raw(neighbor_key)
            dst_meta = json.loads(dst_meta_row["meta"]) if dst_meta_row and dst_meta_row["meta"] else {}

            sp_nd = CosmosMapper.calculate_nd(self.cortex, neighbor_key, dst_content, dst_meta, origin_key=focus_key, depth=1)

            signposts.append({
                "index": idx,
                "key": neighbor_key,
                "alias": dst_aliases[0] if dst_aliases else None,
                "rel": rel,
                "direction": direction,
                "w": w,
                "type": link_type,
                "preview": preview,
                "branches_ahead": branch_count,
                "cosmos_nd": sp_nd
            })

        # ── Resonance: 2-hop semantic neighbourhood ───────────────────────────────
        signpost_keys = {sp["key"] for sp in signposts}

        def _atom_type(k: str) -> str:
            raw = ((self.nucleus.get_chunk_raw(k) if self.nucleus else None)
                   or self.cortex.core.get_chunk_raw(k))
            if raw:
                m = json.loads(raw.get("meta", "{}") or "{}")
                if m.get("type") == "hub":
                    return "concept"
            return "structure"

        associations = [{"key": sp["key"], "type": _atom_type(sp["key"])}
                        for sp in signposts]

        resonance: List[Dict[str, Any]] = []
        seen_2hop = signpost_keys | {focus_key}

        for sp in signposts[:10]:
            if len(resonance) >= 15:
                break
            sp_key   = sp["key"]
            sp_alias = sp.get("alias") or sp_key[:12]
            for hop_key, _hop_rel in self.cortex.get_adjacent_links(sp_key)[:15]:
                if hop_key in seen_2hop:
                    continue
                seen_2hop.add(hop_key)
                hop_content = ((self.nucleus.get_chunk(hop_key) if self.nucleus else None)
                               or self.cortex.get_chunk(hop_key) or "")
                if not hop_content:
                    continue
                preview = hop_content
                if preview.startswith("[") and "\n" in preview:
                    preview = preview.split("\n", 1)[1].strip()
                preview = preview[:50].replace("\n", " ")
                resonance.append({"via": sp_key, "via_alias": sp_alias, "preview": preview})
                associations.append({"key": hop_key, "type": _atom_type(hop_key)})
                if len(resonance) >= 15:
                    break

        return {
            "type": "atom",
            "focus": {
                "key": focus_key,
                "alias": aliases[0] if aliases else None,
                "content": content,
                "meta": meta_str,
                "cosmos_nd": focus_nd
            },
            "signposts":    signposts,
            "resonance":    resonance,
            "associations": associations,
        }

    def generate_collection_view(self, name: str, allowed_scopes: List[str] = None) -> Dict[str, Any]:
        """Generates a macro view for a specific Collection (Set)."""
        members = self.cortex.list_set(name, allowed_scopes)
        signposts = []

        focus_nd = [0.0, 0.0, 0.0, 0.0, -1, "#FFFFFF"]

        for idx, m in enumerate(members):
            k, c = m["key"], m["content"] or ""
            preview = c[:40].replace('\n', ' ') + "..." if len(c) > 40 else c.replace('\n', ' ')
            als = self.cortex.get_aliases_by_key(k)

            meta_row = self.cortex.core.get_chunk_raw(k)
            meta = json.loads(meta_row["meta"]) if meta_row and meta_row["meta"] else {}

            sp_nd = CosmosMapper.calculate_nd(self.cortex, k, c, meta, depth=0)

            signposts.append({
                "index": idx, "key": k, "alias": als[0] if als else None,
                "rel": "sys:member_of", "direction": "in", "w": 1.0, "type": "member",
                "preview": preview, "branches_ahead": 0, "cosmos_nd": sp_nd,
            })

        # ── Concept atom: atom named the same as this collection ──────────────────
        concept_info: Dict[str, Any] = {}
        for engine in ([self.cortex] + ([self.nucleus] if self.nucleus else [])):
            c_key = engine.resolve_alias(name) if hasattr(engine, 'resolve_alias') else None
            if not c_key:
                continue
            c_content = engine.get_chunk(c_key)
            if not c_content:
                continue
            c_als = engine.get_aliases_by_key(c_key)
            c_links = engine.get_adjacent_links(c_key)
            concept_info = {
                "key":        c_key,
                "alias":      c_als[0] if c_als else None,
                "content":    c_content,
                "link_count": len(c_links),
            }
            break

        return {
            "type": "collection",
            "focus": {
                "key":     name,
                "alias":   name,
                "content": f"[ {name} ]  {len(members)} members",
                "meta":    "{}",
                "cosmos_nd": focus_nd,
            },
            "signposts": signposts,
            "concept":   concept_info,
        }

    def zoom_out(self, focus_key: str, allowed_scopes: List[str] = None) -> Dict[str, Any]:
        """Generates the macro environment data, respecting security boundaries."""
        is_col = self.cortex.core.collection_exists(focus_key)

        collections = []
        macro_nodes = []
        neighborhood_size = 0

        if is_col:
            collections = [focus_key]
            members = self.cortex.list_set(focus_key, allowed_scopes) # Scope filter
            neighborhood_size = len(members)
            
            for m in members[:10]:
                k, c = m["key"], m["content"] or ""
                meta_row = self.cortex.core.get_chunk_raw(k)
                meta = json.loads(meta_row["meta"]) if meta_row and meta_row["meta"] else {}
                vec = CosmosMapper.calculate_nd(self.cortex, k, c, meta, depth=2)
                macro_nodes.append({"key": k, "preview": str(c)[:20], "cosmos_nd": vec})
        
        else:
            collections = self.cortex.core.get_collections_for_key(focus_key)

            # Clear temporary macro sets
            self.cortex.clear_set("temp_macro")
            macro_view = self.cortex.explore(focus_key, set_name="temp_macro", depth=2, allowed_scopes=allowed_scopes)
            neighborhood_size = len(macro_view)
            
            for m in macro_view[:10]:
                k, c = m["key"], m["content"] or ""
                meta_row = self.cortex.core.get_chunk_raw(k)
                meta = json.loads(meta_row["meta"]) if meta_row and meta_row["meta"] else {}
                
                vec = CosmosMapper.calculate_nd(self.cortex, k, c, meta, origin_key=focus_key, depth=2)
                macro_nodes.append({"key": k, "preview": str(c)[:20], "cosmos_nd": vec})
        
        return {
            "focus": focus_key,
            "collections": collections,
            "neighborhood_size": neighborhood_size,
            "macro_nodes": macro_nodes
        }
