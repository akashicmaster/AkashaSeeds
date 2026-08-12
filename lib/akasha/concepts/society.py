"""
SocietyConcept — the virtual dialogue space (a "society") that lives on a group.

A **society** is a first-class interaction space: a named channel inside a group where AVATARS
(casts) converse. It is the general, LLM-agnostic chat substrate — humans, remote clients, and
LLM agents all speak into the same space through their avatars, and read the same timeline. LLMs
are connected LATER as just another avatar; nothing here depends on them.

Division of labour (kept clean, per Akasha's Operand/Operator/Agent methodology):
  • **cast**  = the PERSONA — an avatar's identity, traits, wounds, bonds, … (unchanged).
  • **society** = the SPACE — it holds the roster of casts, owns the timeline, and defines turn
    ordering. You speak into a society AS an avatar you own (never as the bare client): the
    avatar is the unit of participation, so anonymity is the default and business "real-identity"
    use is just a stricter cast definition later.

Why avatar-only: a client is present in a society through an alter-ego, not in person. High
anonymity keeps application free; if identity must be pinned (org/company), tighten the cast,
not this layer.

Storage (all in the GROUP engine, so it is shared and gated by group membership):
  • society object atom  — aliased `society:<gid>:<name>`, indexed in `societies:<gid>`.
  • roster set           — the casts registered into the space.
  • feed set (timeline)  — the utterance atoms, ordered by time.
  The DEFAULT space is name "main", and it maps onto the group's existing `soc:<gid>` /
  `soc:<gid>:casts` sets — so `cast.say`/`cast.feed` (the quick "speak to the group") ARE this
  society's main space, fully interoperable. Named spaces add `:<name>` and let one group hold
  several conversations (lounge, debate, …). A society may be crossed with a `world`
  (`sys:in_world`) so it sits inside a worldview.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Akasha.Concept.Society")

CAST_INDEX_SET = "set:cast:index"           # where a client's owned casts are indexed
CONTEXT_KEY_ACTIVE = "active_society"
DEFAULT_SPACE = "main"


class SocietyConcept(BaseConcept):
    CONCEPT_PREFIX = "society"
    CONCEPT_METHODS = {
        "new":    {"op": "op_new"},
        "ls":     {"op": "op_list"},
        "open":   {"op": "op_open"},
        "join":   {"op": "op_join"},
        "say":    {"op": "op_say"},
        "feed":   {"op": "op_feed"},
        "roster": {"op": "op_roster"},
        "turn":   {"op": "op_turn"},
        "world":  {"op": "op_world"},
        "info":   {"op": "op_info"},
        "decider": {"op": "op_decider"},   # designate the responsible cast (coworking anchor)
        # ── seeds13 governance (Agent / Responsible / Chairman delegation) ──
        "admit":       {"op": "op_admit"},        # admit a cast → mint its agent binding
        "chairman":    {"op": "op_chairman"},     # appoint the chairman (admin-only delegation)
        "responsible": {"op": "op_responsible"},  # set scribe/broadcaster/… (admin or chairman)
        "now":         {"op": "op_now"},          # read the society's chronon frontier(s)
        "workflow":    {"op": "op_workflow"},     # bind a wf: → compile it to a prospective chronon graph
        "project":     {"op": "op_project"},      # projection: view a society/workflow/chronon face
        # ── seeds13 deliberation (協議 / 採決 / 意思決定 — typed feed atoms, no schema change) ──
        "propose":     {"op": "op_propose"},      # table a proposal (step of a workflow)
        "vote":        {"op": "op_vote"},         # cast a vote on a proposal
        "tally":       {"op": "op_tally"},        # count the votes on a proposal
        "decide":      {"op": "op_decide"},       # record the decision (chairman/decider/admin, or tally)
        "guest":  {"op": "op_guest"},      # toggle the open_guest gate (external-LLM guests)
        "public": {"op": "op_public"},     # toggle the public-broadcast gate (archives live view)
        "broadcast": {"op": "op_broadcast"},  # read a public society's feed + AI disclosures
        "rm":     {"op": "op_delete"},
    }

    # ── space addressing ─────────────────────────────────────────────────────────
    def _resolve(self, group: str = "", name: str = "", society: str = "", space: str = "") -> (str, str):
        """Resolve a space to (gid, name). Accepts an explicit `society` id ("<gid>/<name>" or a
        bare "<gid>" = main), or `group` [+ `name`/`space`, default "main"], or the session-active
        space. `space` is an alias for `name` (the channel), clearer for external/LLM callers."""
        name = (space or "").strip() or name
        society = (society or "").strip()
        if society:
            gid, _, nm = society.partition("/")
            return gid.strip(), (nm.strip() or DEFAULT_SPACE)
        gid = (group or "").strip()
        nm = (name or "").strip() or DEFAULT_SPACE
        if not gid:
            active = None
            if hasattr(self.session, "get_context"):
                active = self.session.get_context(CONTEXT_KEY_ACTIVE)
            if active:
                g2, _, n2 = str(active).partition("/")
                return g2.strip(), (n2.strip() or DEFAULT_SPACE)
        return gid, nm

    @staticmethod
    def _sid(gid: str, name: str) -> str:
        return f"{gid}/{name}"

    @staticmethod
    def _feed_set(gid: str, name: str) -> str:
        # main maps onto the group's existing timeline → interop with cast.say/cast.feed.
        return f"soc:{gid}" if name == DEFAULT_SPACE else f"soc:{gid}:{name}"

    @staticmethod
    def _roster_set(gid: str, name: str) -> str:
        return f"soc:{gid}:casts" if name == DEFAULT_SPACE else f"soc:{gid}:{name}:casts"

    @staticmethod
    def _society_alias(gid: str, name: str) -> str:
        return f"society:{gid}:{name}"

    @staticmethod
    def _guest_set(gid: str) -> str:
        # society object keys whose space is opened to external-LLM guests (the outbound gate).
        # A plain group-engine set — no new relation/namespace, consistent with the soc:* sets.
        return f"soc:open_guest:{gid}"

    def _is_open_guest(self, ge, gid: str, key: str) -> bool:
        return bool(key) and key in ge.core.get_collection_members(self._guest_set(gid))

    @staticmethod
    def _public_set(gid: str) -> str:
        # society object keys the creator has consented to display PUBLICLY (the "broadcast" gate —
        # e.g. a live public curation meeting on the archives portal). Distinct from open_guest:
        # open_guest = "OK to send this feed OUT to an external LLM"; public = "OK to show this feed
        # to the public web". A public curation meeting is a society with BOTH set.
        return f"soc:public:{gid}"

    def _is_public(self, ge, gid: str, key: str) -> bool:
        return bool(key) and key in ge.core.get_collection_members(self._public_set(gid))

    # Attribution notices for AI-generated utterances shown publicly — required by the model
    # providers' terms/brand rules and by AI-disclosure norms (e.g. EU AI Act transparency). The
    # gateway stamps provider/model on a guest's utterance; the public broadcast renders the notice.
    _PROVIDER_NOTICE = {
        "gemini": "Powered by Google Gemini",
        "openrouter": "via OpenRouter",
        "ollama": "local open model",
    }
    _MODEL_NOTICE = (            # substring → attribution required by that model's licence
        ("llama", "Built with Llama"),
        ("gemma", "Built with Gemma"),
        ("mistral", "Mistral AI model"),
        ("qwen", "Qwen model"),
        ("deepseek", "DeepSeek model"),
        ("gemini", "Powered by Google Gemini"),
    )

    @classmethod
    def _attribution_notice(cls, provider: str, model: str) -> str:
        """The public-display disclosure + attribution for one AI utterance: an "AI-generated"
        disclosure plus the model/provider attribution its terms require. Empty for a human."""
        provider = (provider or "").strip().lower()
        model = (model or "").strip().lower()
        if not provider and not model:
            return ""
        parts = []
        for frag, note in cls._MODEL_NOTICE:      # model licence attribution wins (most specific)
            if frag in model:
                parts.append(note)
                break
        else:
            if provider in cls._PROVIDER_NOTICE:
                parts.append(cls._PROVIDER_NOTICE[provider])
        if provider == "openrouter" and "via OpenRouter" not in parts:
            parts.append("via OpenRouter")
        tail = (" · " + " · ".join(parts)) if parts else ""
        return "AI-generated" + tail

    def _group_engine(self, gid: str):
        ge = getattr(self.session, "group_engines", {}).get(gid)
        if ge is None or f"scope:group_{gid}" not in (self.allowed_scopes or []):
            raise RuntimeError(f"Not a member of group '{gid}'.")
        return ge

    def _client(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _owned_cast(self, cast: str) -> (str, str):
        """Resolve a cast id or owned name to (cast_id, cast_name) from the CALLER's own cortex —
        you speak only as an avatar you own (impersonation of another member's cast is blocked)."""
        cast = (cast or "").strip()
        if not cast:
            raise ValueError("a cast (avatar) is required — you speak only as an avatar you own.")
        meta = self.cortex.get_meta(cast)
        if meta and meta.get("concept") == "cast":
            return cast, meta.get("name", "")
        for key in self.cortex.get_collection_members(CAST_INDEX_SET):
            m = self.cortex.get_meta(key)
            if m and m.get("concept") == "cast" and m.get("name") == cast:
                return key, m.get("name", "")
        raise RuntimeError(f"No owned avatar '{cast}'.")

    def _society_key(self, ge, gid: str, name: str) -> Optional[str]:
        return ge.resolve_alias(self._society_alias(gid, name))

    def _feed_name_map(self, ge, gid: str, name: str) -> Dict[str, str]:
        """cast_id → display name, learned from what the feed recorded (personas live in each
        owner's cortex, not the group engine)."""
        nm: Dict[str, str] = {}
        for k in ge.core.get_collection_members(self._feed_set(gid, name)):
            row = ge.core.get_chunk_raw(k)
            if not row:
                continue
            try:
                m = json.loads(row.get("meta") or "{}")
            except Exception:
                m = {}
            if m.get("from_cast") and m.get("cast_name"):
                nm[m["from_cast"]] = m["cast_name"]
        return nm

    def _owned_or_roster_cast(self, ge, gid: str, name: str, cast: str) -> (str, str):
        """Resolve a cast id or name to a (cast_id, cast_name) that is PRESENT in the space's
        roster — a decider is a participant, and may be another member's avatar (unlike say, which
        requires ownership)."""
        cast = (cast or "").strip()
        if not cast:
            raise ValueError("a cast (avatar) is required.")
        roster = set(ge.core.get_collection_members(self._roster_set(gid, name)))
        name_map = self._feed_name_map(ge, gid, name)
        if cast in roster:
            return cast, name_map.get(cast, "")
        for cid in roster:
            if name_map.get(cid) == cast:
                return cid, cast
        try:
            cid, cname = self._owned_cast(cast)
            if cid in roster:
                return cid, cname
        except Exception:
            pass
        raise RuntimeError(f"'{cast}' is not an avatar present in this space.")

    # ── operators ────────────────────────────────────────────────────────────────
    def op_new(self, group: str = "", name: str = DEFAULT_SPACE, topic: str = "",
               world: str = "", society: str = "", space: str = "", kind: str = "chat",
               open_guest: Any = False, public: Any = False) -> Dict[str, Any]:
        """Create a dialogue space in a group (idempotent — reuse if it exists). Any group member
        may open a space. `world=` crosses it with a world (id or title) so it sits in a worldview.

        `kind` marks what the space is FOR: "chat" (default) or "cowork" — a society is not merely
        a chat room, it is a coworking space, and a cowork space is the anchor for the deliberation
        / voting / responsible-decider governance that layers on top (see the spec). The flag is
        recorded now so those features can attach without a schema change.

        `open_guest=yes` opens the space to external-LLM guests (the outbound gate): only then will
        the guest gateway send this feed to a free external tier that may train on it. Applies only
        on fresh creation (the caller is the creator); toggle an existing space with society.guest."""
        gid, name = self._resolve(group, name, society, space)
        if not gid:
            raise ValueError("society.new requires a group.")
        ge = self._group_engine(gid)
        sid = self._sid(gid, name)
        existing = self._society_key(ge, gid, name)
        if existing:
            self._maybe_open(sid)
            return {"status": "exists", "society_id": sid, "key": existing, "group": gid,
                    "name": name, "open_guest": self._is_open_guest(ge, gid, existing)}
        owner = self._client()
        kind = (kind or "chat").strip().lower()
        meta = {"type": "society", "concept": "society", "group": gid, "name": name,
                "sid": sid, "topic": topic, "kind": kind if kind in ("chat", "cowork") else "chat",
                "created_by": owner, "created_at": time.time()}
        key = ge.put_atom(f"[ Society: {sid} ]", meta, author=owner)
        ge.core.put_alias(key, self._society_alias(gid, name))
        ge.add_to_set(f"societies:{gid}", key)
        # feed/roster sets are created lazily on first add_to_set (as cast.publish relies on).
        linked = ""
        if world:
            linked = self._link_world(ge, key, world)
        og = self._truthy(open_guest)
        if og:
            ge.add_to_set(self._guest_set(gid), key)
        pub = self._truthy(public)
        if pub:
            ge.add_to_set(self._public_set(gid), key)
        self._maybe_open(sid)
        logger.info("[Society] created %s (kind=%s, topic=%r, world=%r, open_guest=%s, public=%s)",
                    sid, meta["kind"], topic, linked, og, pub)
        return {"status": "created", "society_id": sid, "key": key, "group": gid,
                "name": name, "kind": meta["kind"], "topic": topic, "world": linked,
                "open_guest": og, "public": pub}

    def op_guest(self, open: Any = "", society: str = "", group: str = "", name: str = "",
                 space: str = "") -> Dict[str, Any]:
        """Toggle the open_guest gate on an existing space — the outbound consent that external-LLM
        guests may join and this feed may leave to a free external tier (which may train on it).
        Creator-only (like decider). `open=yes|no`; omitting `open` just reports the current state."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        key = self._society_key(ge, gid, name)
        if not key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        current = self._is_open_guest(ge, gid, key)
        req = str(open or "").strip()
        if req == "":                                   # read-only query
            return {"status": "guest_policy", "society_id": self._sid(gid, name),
                    "open_guest": current}
        row = ge.core.get_chunk_raw(key) or {}
        try:
            smeta = json.loads(row.get("meta") or "{}")
        except Exception:
            smeta = {}
        if smeta.get("created_by") not in (self._client(), None):
            raise RuntimeError("only the society's creator may change its guest policy.")
        want = self._truthy(req)
        if want and not current:
            ge.add_to_set(self._guest_set(gid), key)
        elif not want and current:
            ge.core.remove_from_collection(self._guest_set(gid), key)
        return {"status": "guest_policy", "society_id": self._sid(gid, name), "open_guest": want}

    def op_public(self, open: Any = "", society: str = "", group: str = "", name: str = "",
                  space: str = "") -> Dict[str, Any]:
        """Toggle the PUBLIC-broadcast gate — the creator's consent that this space may be shown to
        the public web (e.g. a live public curation meeting on the archives portal). Distinct from
        open_guest (which is consent to send the feed OUT to an external LLM). A public curation
        meeting sets both. Creator-only. `open=yes|no`; omitting `open` reports the current state.
        Only a space flagged public is served by society.broadcast."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        key = self._society_key(ge, gid, name)
        if not key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        current = self._is_public(ge, gid, key)
        req = str(open or "").strip()
        if req == "":
            return {"status": "public_policy", "society_id": self._sid(gid, name), "public": current}
        row = ge.core.get_chunk_raw(key) or {}
        try:
            smeta = json.loads(row.get("meta") or "{}")
        except Exception:
            smeta = {}
        if smeta.get("created_by") not in (self._client(), None):
            raise RuntimeError("only the society's creator may change its public policy.")
        want = self._truthy(req)
        if want and not current:
            ge.add_to_set(self._public_set(gid), key)
        elif not want and current:
            ge.core.remove_from_collection(self._public_set(gid), key)
        return {"status": "public_policy", "society_id": self._sid(gid, name), "public": want}

    def op_broadcast(self, society: str = "", group: str = "", name: str = "",
                     limit: Any = 50, space: str = "") -> Dict[str, Any]:
        """Read a PUBLIC space's timeline for public display (the archives live-view / "public
        curation meeting" surface). Refuses a space that is not flagged public — so a private feed
        is never broadcast. Each message carries its AI disclosure (`ai`, `provider`, `model`,
        `ai_notice`); the response bundles the required `attribution` notices + a `disclosure`
        banner so the display satisfies the providers' terms and AI-transparency rules. Read-level:
        the archives operator's authorized session renders only the spaces it has flagged public."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        key = self._society_key(ge, gid, name)
        if not key or not self._is_public(ge, gid, key):
            raise RuntimeError(f"'{self._sid(gid, name)}' is not a public broadcast "
                               f"(set it with society.public open=yes).")
        feed = self.op_feed(society=society, group=group, name=name, space=space, limit=limit)
        notices = set()
        for m in feed["messages"]:
            note = self._attribution_notice(m.get("provider", ""), m.get("model", ""))
            m["ai_notice"] = note
            if note:
                notices.add(note)
        info = self.op_info(society=society, group=group, name=name, space=space)
        return {"society_id": feed["society_id"], "topic": info.get("topic", ""),
                "kind": info.get("kind", "chat"), "count": feed["count"],
                "messages": feed["messages"], "attribution": sorted(notices),
                "disclosure": ("This is an AI-assisted public discussion; messages marked "
                               "AI-generated are produced by machine models, not humans.")}

    def op_decider(self, cast: str = "", society: str = "", group: str = "",
                   name: str = "", space: str = "") -> Dict[str, Any]:
        """Designate the RESPONSIBLE cast (decision-maker) for a space — the anchor of society-as-
        coworking: deliberation and votes inform, but a named decider decides. Only the space's
        creator may set it. Recorded as a single society→cast `society:decider` link (immutable-
        friendly; re-setting replaces it). The decider must be an avatar present in the space.
        The deliberation/voting ops that consume this are reserved (see the spec)."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        key = self._society_key(ge, gid, name)
        if not key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        row = ge.core.get_chunk_raw(key) or {}
        try:
            smeta = json.loads(row.get("meta") or "{}")
        except Exception:
            smeta = {}
        if smeta.get("created_by") not in (self._client(), None):
            raise RuntimeError("only the society's creator may designate its decider.")
        cid, cname = self._owned_or_roster_cast(ge, gid, name, cast)
        for lk in ge.core.get_adjacent_links(key, "society:decider"):
            ge.core.remove_link_raw(key, lk.get("dst"), "society:decider")
        ge.put_link(key, cid, "society:decider", author=self._client())
        return {"status": "decider_set", "society_id": self._sid(gid, name),
                "decider": cid, "decider_name": cname}

    def op_info(self, society: str = "", group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """The space object: name, kind (chat/cowork), topic, world, the responsible decider
        (if designated), and the open_guest gate. The read surface for a society's identity and
        governance anchors — and what the guest gateway checks before it joins."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        key = self._society_key(ge, gid, name)
        if not key:
            # An implicit space (used via say/feed without society.new) has no object yet —
            # report sensible defaults instead of failing (the space still works).
            return {"society_id": self._sid(gid, name), "key": "", "name": name,
                    "kind": "chat", "topic": "", "created_by": "", "world": "",
                    "decider": "", "decider_name": "", "open_guest": False, "public": False,
                    "exists": False}
        row = ge.core.get_chunk_raw(key) or {}
        try:
            m = json.loads(row.get("meta") or "{}")
        except Exception:
            m = {}
        world = next((l.get("dst") for l in ge.core.get_adjacent_links(key, "sys:in_world")), "")
        decider = next((l.get("dst") for l in ge.core.get_adjacent_links(key, "society:decider")), "")
        dname = ""
        if decider:
            roster = self.op_roster(society=society, group=group, name=name, space=space)["casts"]
            dname = next((c["name"] for c in roster if c["cast_id"] == decider), "")
        return {"society_id": self._sid(gid, name), "key": key, "name": m.get("name", name),
                "kind": m.get("kind", "chat"), "topic": m.get("topic", ""),
                "created_by": m.get("created_by", ""), "world": world,
                "decider": decider, "decider_name": dname,
                "open_guest": self._is_open_guest(ge, gid, key),
                "public": self._is_public(ge, gid, key), "exists": True}

    def op_list(self, group: str = "") -> Dict[str, Any]:
        gid = (group or "").strip()
        if not gid:
            raise ValueError("society.ls requires a group.")
        ge = self._group_engine(gid)
        spaces = []
        for key in ge.core.get_collection_members(f"societies:{gid}"):
            row = ge.core.get_chunk_raw(key)
            if not row:
                continue
            try:
                m = json.loads(row.get("meta") or "{}")
            except Exception:
                m = {}
            if m.get("concept") != "society":
                continue
            spaces.append({"society_id": m.get("sid", ""), "name": m.get("name", ""),
                           "topic": m.get("topic", ""), "key": key,
                           "created_at": m.get("created_at", 0)})
        spaces.sort(key=lambda s: s.get("created_at", 0))
        return {"group": gid, "count": len(spaces), "societies": spaces}

    def op_open(self, society: str = "", group: str = "", name: str = "") -> Dict[str, Any]:
        gid, name = self._resolve(group, name, society)
        if not gid:
            raise ValueError("society.open requires a society or group.")
        self._group_engine(gid)  # membership check
        sid = self._sid(gid, name)
        self._maybe_open(sid)
        return {"status": "opened", "society_id": sid}

    def op_join(self, cast: str = "", society: str = "", group: str = "",
                name: str = "") -> Dict[str, Any]:
        """Register one of your avatars into a space's roster (so others can see who is present)."""
        gid, name = self._resolve(group, name, society)
        ge = self._group_engine(gid)
        cast_id, cast_name = self._owned_cast(cast)
        ge.add_to_set(self._roster_set(gid, name), cast_id)
        return {"status": "joined", "society_id": self._sid(gid, name),
                "cast_id": cast_id, "cast_name": cast_name}

    def op_say(self, text: str = "", cast: str = "", society: str = "", group: str = "",
               name: str = "", reply: str = "", disclose: Any = False, space: str = "",
               agent: str = "", provider: str = "", model: str = "") -> Dict[str, Any]:
        """Speak into a space AS an owned avatar. Flat timeline with optional `reply=<key>`
        threading. Pseudonymous by default (the human is hidden); disclose=true stamps the member.
        Auto-registers the avatar in the roster on first utterance.

        `agent`/`provider`/`model` mark an AI-generated utterance (the guest gateway stamps them):
        they drive the AI disclosure + licence attribution shown when the space is broadcast
        publicly (society.broadcast) — required by the model providers' terms."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        cast_id, cast_name = self._owned_cast(cast)
        msg = (text or "").strip()
        if not msg:
            raise ValueError("society.say requires text.")
        sid = self._sid(gid, name)
        meta = {"type": "cast_utterance", "concept": "cast", "society": sid,
                "from_cast": cast_id, "cast_name": cast_name, "created_at": time.time()}
        if str(reply or "").strip():
            meta["reply_to"] = reply.strip()
        if self._truthy(disclose):
            meta["client_id"] = self._client()
        if str(agent or "").strip() or str(provider or "").strip():
            meta["agent"] = (agent or "ai").strip()
            meta["provider"] = (provider or "").strip()
            meta["model"] = (model or "").strip()
        key = ge.put_atom(msg, meta, author=cast_id)
        ge.add_to_set(self._feed_set(gid, name), key)
        ge.add_to_set(self._roster_set(gid, name), cast_id)   # auto-join
        return {"status": "said", "key": key, "society_id": sid, "cast_id": cast_id,
                "cast_name": cast_name, "reply_to": meta.get("reply_to", "")}

    def op_feed(self, society: str = "", group: str = "", name: str = "",
                limit: Any = 20, thread: str = "", space: str = "") -> Dict[str, Any]:
        """Read the space's timeline, resolved to {cast_name, from_cast, text, created_at,
        reply_to}, oldest→newest. `thread=<key>` filters to that message and its direct replies."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        try:
            lim = max(1, min(int(limit), 200))
        except (TypeError, ValueError):
            lim = 20
        thread = (thread or "").strip()
        items = []
        for key in ge.core.get_collection_members(self._feed_set(gid, name)):
            row = ge.core.get_chunk_raw(key)
            if not row:
                continue
            try:
                m = json.loads(row.get("meta") or "{}")
            except Exception:
                m = {}
            mtype = m.get("type", "")
            if mtype not in ("cast_utterance", "proposal", "decision"):
                continue        # raw votes stay out of the chat timeline (query them via society.tally)
            items.append({"key": key, "from_cast": m.get("from_cast", ""),
                          "cast_name": m.get("cast_name", ""), "text": row.get("content") or "",
                          "created_at": m.get("created_at", 0), "reply_to": m.get("reply_to", ""),
                          "disclosed": bool(m.get("client_id")), "client_id": m.get("client_id", ""),
                          "agent": m.get("agent", ""), "provider": m.get("provider", ""),
                          "model": m.get("model", ""), "msg_type": mtype,
                          "step": m.get("step", ""), "proposal": m.get("proposal", ""),
                          "outcome": m.get("outcome", "")})
        items.sort(key=lambda x: x.get("created_at", 0))
        if thread:
            items = [m for m in items if m["key"] == thread or m.get("reply_to") == thread]
        items = items[-lim:]
        return {"society_id": self._sid(gid, name), "count": len(items), "messages": items}

    def op_roster(self, society: str = "", group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        # A cast's persona lives in ITS OWNER's cortex, not the group engine, so resolve display
        # names from what the feed recorded (cast_name on each utterance); fall back to a
        # published persona in the group engine if present.
        name_map: Dict[str, str] = {}
        for key in ge.core.get_collection_members(self._feed_set(gid, name)):
            row = ge.core.get_chunk_raw(key)
            if not row:
                continue
            try:
                m = json.loads(row.get("meta") or "{}")
            except Exception:
                m = {}
            if m.get("type") == "cast_utterance" and m.get("from_cast") and m.get("cast_name"):
                name_map[m["from_cast"]] = m["cast_name"]
        casts = []
        for cid in ge.core.get_collection_members(self._roster_set(gid, name)):
            nm, ident = name_map.get(cid, ""), ""
            if not nm:
                row = ge.core.get_chunk_raw(cid)
                if row:
                    try:
                        mm = json.loads(row.get("meta") or "{}")
                    except Exception:
                        mm = {}
                    nm, ident = mm.get("name", ""), mm.get("identity", "")
            casts.append({"cast_id": cid, "name": nm, "identity": ident})
        return {"society_id": self._sid(gid, name), "count": len(casts), "casts": casts}

    def op_turn(self, society: str = "", group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """Turn ordering IS defined here (not in the client): who spoke last and a suggested next
        speaker (a roster avatar other than the last), so any driver — human or LLM — shares one
        rule. v1 is last-speaker + round-robin over the roster; richer policies layer on top."""
        feed = self.op_feed(society=society, group=group, name=name, space=space, limit=200)
        roster = self.op_roster(society=society, group=group, name=name, space=space)["casts"]
        msgs = feed["messages"]
        last = msgs[-1] if msgs else None
        last_cast = last["from_cast"] if last else ""
        others = [c for c in roster if c["cast_id"] != last_cast]
        suggested = others[0] if others else (roster[0] if roster else None)
        return {"society_id": feed["society_id"], "turns": len(msgs),
                "last_cast": last_cast, "last_cast_name": last["cast_name"] if last else "",
                "roster": roster,
                "suggested_next": suggested["cast_id"] if suggested else "",
                "suggested_next_name": suggested["name"] if suggested else ""}

    def op_world(self, world: str = "", society: str = "", group: str = "",
                 name: str = "") -> Dict[str, Any]:
        """Cross a society with a world — place this dialogue space inside a worldview."""
        gid, name = self._resolve(group, name, society)
        ge = self._group_engine(gid)
        key = self._society_key(ge, gid, name)
        if not key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        linked = self._link_world(ge, key, world)
        return {"status": "crossed", "society_id": self._sid(gid, name), "world": linked}

    def op_delete(self, society: str = "", group: str = "", name: str = "") -> Dict[str, Any]:
        """Retire a space (drops the society object + its index membership). Utterance atoms are
        content-addressed and left intact; only the space handle is removed."""
        gid, name = self._resolve(group, name, society)
        if name == DEFAULT_SPACE:
            raise ValueError("the main space cannot be deleted.")
        ge = self._group_engine(gid)
        key = self._society_key(ge, gid, name)
        if key:
            ge.core.remove_from_collection(f"societies:{gid}", key)
        return {"status": "deleted", "society_id": self._sid(gid, name)}

    # ── seeds13 governance: Agent · Responsible · Chairman delegation ─────────────
    @staticmethod
    def _agents_set(gid: str, name: str) -> str:
        return f"soc:{gid}:agents" if name == DEFAULT_SPACE else f"soc:{gid}:{name}:agents"

    @staticmethod
    def _cast_slug(cast_name: str, cast_id: str) -> str:
        import re as _re
        slug = _re.sub(r"[^a-z0-9]+", "_", (cast_name or "").lower()).strip("_")
        return slug or (cast_id or "")[:8]

    def _agent_alias(self, gid: str, name: str, slug: str) -> str:
        return f"agent:{gid}:{name}:{slug}"

    def _is_admin(self) -> bool:
        role = getattr(self.session, "role", None)
        return getattr(role, "value", str(role)) == "admin"

    def _society_meta(self, ge, key: str) -> Dict[str, Any]:
        row = ge.core.get_chunk_raw(key) or {}
        try:
            return json.loads(row.get("meta") or "{}")
        except Exception:
            return {}

    def _is_chairman(self, ge, society_key: str, client: str) -> bool:
        return bool(client) and self._society_meta(ge, society_key).get("chairman_client") == client

    def _gate_admin_or_chairman(self, ge, society_key: str, what: str) -> None:
        """The single delegation crossing (B.4): admit + responsible-setting are gated by
        'requester is admin OR the chairman of THIS society'. Every other gate is by responsible:*."""
        client = self._client()
        if self._is_admin() or self._is_chairman(ge, society_key, client):
            return
        raise RuntimeError(f"only an admin or this society's chairman may {what}.")

    def _mint_agent(self, ge, gid: str, name: str, society_key: str,
                    cast_id: str, cast_name: str, client: str) -> Dict[str, str]:
        """Mint (idempotently) the cast×society binding — the agent atom. Content-addressed on
        (agent|sid|cast), so re-admitting the same cast unifies. Records the controlling client
        (governance metadata; the feed stays pseudonymous). Adds agent:as→cast, agent:in→society,
        and joins soc:<sid>:agents (readable from every member — the R1 invariant)."""
        sid = self._sid(gid, name)
        slug = self._cast_slug(cast_name, cast_id)
        content = f"[ Agent: {cast_name or slug} in {sid} ]\x00{cast_id}"
        meta = {"type": "agent", "concept": "agent", "group": gid, "space": name, "sid": sid,
                "cast": cast_id, "cast_name": cast_name, "cast_slug": slug, "client": client,
                "created_by": self._client(), "created_at": time.time()}
        key = ge.put_atom(content, meta, author=self._client())
        ge.core.put_alias(key, self._agent_alias(gid, name, slug))
        ge.put_link(key, cast_id, "agent:as", author=self._client())
        ge.put_link(key, society_key, "agent:in", author=self._client())
        ge.add_to_set(self._agents_set(gid, name), key)
        return {"key": key, "alias": self._agent_alias(gid, name, slug), "slug": slug}

    def _resolve_agent(self, ge, gid: str, name: str, agent: str = "",
                       cast: str = "") -> Optional[str]:
        """Resolve a target agent atom key from either an agent ref (alias/key) or a cast ref
        (id/name → its agent binding in this space)."""
        agent = (agent or "").strip()
        if agent:
            row = None
            try:
                row = ge.core.get_chunk_raw(agent)
            except Exception:
                row = None
            return agent if row else ge.resolve_alias(agent)
        cast = (cast or "").strip()
        if cast:
            for akey in ge.core.get_collection_members(self._agents_set(gid, name)):
                m = self._society_meta(ge, akey)
                if m.get("concept") != "agent":
                    continue
                if cast in (akey, m.get("cast"), m.get("cast_name"), m.get("cast_slug")):
                    return akey
        return None

    def op_admit(self, cast: str = "", client: str = "", society: str = "", group: str = "",
                 name: str = "", space: str = "") -> Dict[str, Any]:
        """Admit a cast into a society — mint its AGENT binding (a cast admitted to a society).
        Gate: admin OR this society's chairman (the delegation, B.4). The cast becomes an agent OF
        this society; the same cast may be an agent of several societies at once.

        `client=` names the controlling client of the admitted cast (who may act as this agent).
        Resolve order: explicit `client=`; else the caller's own client when the caller owns the
        cast (self-join is still gated — a plain member cannot self-admit unless admin/chairman);
        else "" (bound later when the owner first acts). Feed anonymity is unaffected — this is the
        same client-level governance bookkeeping society.created_by already keeps."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        self._gate_admin_or_chairman(ge, society_key, "admit a cast")
        cid, cname = self._owned_or_roster_cast_lenient(ge, gid, name, cast)
        owner_client = (client or "").strip()
        if not owner_client:
            # bind to the caller only if the caller actually owns the cast
            try:
                own_cid, _ = self._owned_cast(cast)
                if own_cid == cid:
                    owner_client = self._client()
            except Exception:
                owner_client = ""
        minted = self._mint_agent(ge, gid, name, society_key, cid, cname, owner_client)
        ge.add_to_set(self._roster_set(gid, name), cid)   # an agent is also a roster participant
        return {"status": "admitted", "society_id": self._sid(gid, name), "agent": minted["alias"],
                "key": minted["key"], "cast": cid, "cast_name": cname, "client": owner_client}

    def op_chairman(self, agent: str = "", cast: str = "", client: str = "", society: str = "",
                    group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """Appoint the society's CHAIRMAN — the one place the permission line meets the
        responsibility line (B.4). **Admin only.** Appointing a chairman DELEGATES two powers for
        THIS society to that chairman: admit-a-cast and set-`responsible:*` (the chairman need not
        be an admin). Recorded as a single society→agent `responsible:chairman` link plus a fast
        `chairman_client` on the society (the gate reads it). Generalises society.decider; the
        decider read-alias continues to resolve to the chairman."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        if not self._is_admin():
            raise RuntimeError("only an admin may appoint the chairman (this is the delegation).")
        akey = self._resolve_agent(ge, gid, name, agent, cast)
        if not akey:
            raise RuntimeError("chairman target must be an admitted agent (admit the cast first).")
        am = self._society_meta(ge, akey)
        chairman_client = (client or "").strip() or am.get("client", "")
        # single responsible:chairman link (replace any prior)
        for l in ge.core.get_adjacent_links(society_key, "responsible:chairman"):
            ge.core.remove_link_raw(society_key, l.get("dst"), "responsible:chairman")
        ge.put_link(society_key, akey, "responsible:chairman", author=self._client())
        # persist the chairman's controlling client on the society for the fast gate
        smeta = self._society_meta(ge, society_key)
        smeta["chairman_client"] = chairman_client
        row = ge.core.get_chunk_raw(society_key) or {}
        ge.core.put_chunk_raw(society_key, row.get("content") or f"[ Society: {self._sid(gid, name)} ]",
                              json.dumps(smeta, ensure_ascii=False), row.get("author") or self._client(),
                              "verified", time.time())
        ge.core.put_chunk_access(society_key, [ge.scope])
        return {"status": "chairman_set", "society_id": self._sid(gid, name), "agent": agent or cast,
                "key": akey, "chairman_client": chairman_client}

    def op_responsible(self, kind: str = "", agent: str = "", cast: str = "", society: str = "",
                       group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """Set a responsibility (責務) on an agent — scribe / broadcaster / approve:<step> /
        exec:<step> / an open workflow role (proposer / critic / …). Gate: admin OR chairman.
        `responsible:<kind>` society→agent. Chairman is appointed separately (society.chairman)."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        self._gate_admin_or_chairman(ge, society_key, "set a responsible")
        kind = (kind or "").strip()
        if not kind or kind == "chairman":
            raise ValueError("kind is required and must not be 'chairman' (use society.chairman).")
        akey = self._resolve_agent(ge, gid, name, agent, cast)
        if not akey:
            raise RuntimeError("responsible target must be an admitted agent (admit the cast first).")
        rel = f"responsible:{kind}"
        # a single-holder responsibility (scribe/broadcaster) replaces; a per-step one may coexist.
        if kind in ("scribe", "broadcaster"):
            for l in ge.core.get_adjacent_links(society_key, rel):
                ge.core.remove_link_raw(society_key, l.get("dst"), rel)
        ge.put_link(society_key, akey, rel, author=self._client())
        return {"status": "responsible_set", "society_id": self._sid(gid, name), "kind": kind,
                "rel": rel, "agent": agent or cast, "key": akey}

    def op_now(self, society: str = "", group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """Read the society's chronon FRONTIER(s) — the present of Akasha Time (society:now). A
        society may hold several frontiers (branches / alternative futures). Read-level."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            return {"society_id": self._sid(gid, name), "frontiers": [], "count": 0}
        fr = [l.get("dst") for l in ge.core.get_adjacent_links(society_key, "society:now")]
        rows = []
        for k in fr:
            m = self._society_meta(ge, k)
            rows.append({"chronon": next((a for a in ge.get_aliases_by_key(k) if a.startswith("chronon:")), k),
                         "key": k, "aspect": m.get("aspect", ""), "label": m.get("label", "")})
        return {"society_id": self._sid(gid, name), "count": len(rows), "frontiers": rows}

    # ── seeds13 deliberation: propose / vote / tally / decide (typed feed atoms) ──
    def op_propose(self, text: str = "", cast: str = "", step: str = "", society: str = "",
                   group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """Table a proposal in a society (協議) — a typed feed atom (type=proposal) authored by an
        owned avatar. `step=` names the workflow step it advances (optional). Proposals/votes/
        decisions ride the SAME feed substrate as chat (no schema change); society.feed shows them."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        cast_id, cast_name = self._owned_cast(cast)
        msg = (text or "").strip()
        if not msg:
            raise ValueError("society.propose requires text.")
        sid = self._sid(gid, name)
        meta = {"type": "proposal", "concept": "cast", "society": sid, "from_cast": cast_id,
                "cast_name": cast_name, "step": (step or "").strip(), "created_at": time.time()}
        key = ge.put_atom(f"[proposal] {msg}", meta, author=cast_id)
        ge.add_to_set(self._feed_set(gid, name), key)
        ge.add_to_set(self._roster_set(gid, name), cast_id)
        return {"status": "proposed", "key": key, "society_id": sid, "cast_id": cast_id,
                "cast_name": cast_name, "step": meta["step"]}

    def op_vote(self, proposal: str = "", choice: str = "yes", cast: str = "", society: str = "",
                group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """Cast a vote on a proposal (採決) — a typed feed atom (type=vote) referencing the proposal
        by key, authored by an owned avatar. choice=yes|no|abstain. One vote per (cast, proposal):
        re-voting replaces the avatar's prior vote."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        cast_id, cast_name = self._owned_cast(cast)
        proposal = (proposal or "").strip()
        if not proposal:
            raise ValueError("society.vote requires proposal=<key>.")
        ch = (choice or "yes").strip().lower()
        if ch not in ("yes", "no", "abstain"):
            raise ValueError("choice must be yes|no|abstain.")
        # replace this avatar's prior vote on the same proposal
        for k in ge.core.get_collection_members(self._feed_set(gid, name)):
            m = self._society_meta(ge, k)
            if m.get("type") == "vote" and m.get("proposal") == proposal and m.get("from_cast") == cast_id:
                ge.core.remove_from_collection(self._feed_set(gid, name), k)
        sid = self._sid(gid, name)
        meta = {"type": "vote", "concept": "cast", "society": sid, "from_cast": cast_id,
                "cast_name": cast_name, "proposal": proposal, "choice": ch, "created_at": time.time()}
        key = ge.put_atom(f"[vote:{ch}] {proposal[:12]} · {cast_id[:8]}", meta, author=cast_id)
        ge.add_to_set(self._feed_set(gid, name), key)
        return {"status": "voted", "key": key, "society_id": sid, "proposal": proposal,
                "choice": ch, "cast_name": cast_name}

    def op_tally(self, proposal: str = "", society: str = "", group: str = "", name: str = "",
                 space: str = "") -> Dict[str, Any]:
        """Count the votes on a proposal — yes / no / abstain and the leading choice. Read-level."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        proposal = (proposal or "").strip()
        counts = {"yes": 0, "no": 0, "abstain": 0}
        for k in ge.core.get_collection_members(self._feed_set(gid, name)):
            m = self._society_meta(ge, k)
            if m.get("type") == "vote" and m.get("proposal") == proposal:
                counts[m.get("choice", "abstain")] = counts.get(m.get("choice", "abstain"), 0) + 1
        lead = max(("yes", "no", "abstain"), key=lambda c: counts[c])
        decided = counts["yes"] != counts["no"]
        return {"society_id": self._sid(gid, name), "proposal": proposal, "counts": counts,
                "leading": lead if decided else "tie", "total": sum(counts.values())}

    def op_decide(self, proposal: str = "", outcome: str = "", cast: str = "", society: str = "",
                  group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """Record the decision on a proposal (意思決定) — a typed feed atom (type=decision).
        Authority = the chairman/decider or an admin; `outcome=` may be given explicitly, else it
        falls to the tally's leading choice. A tie with no explicit outcome is refused."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist.")
        # authority: chairman OR admin OR the (legacy) decider cast's owner
        client = self._client()
        authorized = self._is_admin() or self._is_chairman(ge, society_key, client)
        if not authorized:
            raise RuntimeError("only the chairman or an admin may record a decision.")
        proposal = (proposal or "").strip()
        if not proposal:
            raise ValueError("society.decide requires proposal=<key>.")
        out = (outcome or "").strip().lower()
        if not out:
            t = self.op_tally(proposal=proposal, society=society, group=group, name=name, space=space)
            if t["leading"] == "tie":
                raise RuntimeError("the vote is tied — supply outcome= explicitly to decide.")
            out = t["leading"]
        sid = self._sid(gid, name)
        meta = {"type": "decision", "concept": "cast", "society": sid, "proposal": proposal,
                "outcome": out, "decided_by": client, "created_at": time.time()}
        if cast:
            try:
                meta["from_cast"], meta["cast_name"] = self._owned_or_roster_cast(ge, gid, name, cast)
            except Exception:
                pass
        key = ge.put_atom(f"[decision:{out}] {proposal[:12]}", meta, author=client)
        ge.add_to_set(self._feed_set(gid, name), key)
        return {"status": "decided", "key": key, "society_id": sid, "proposal": proposal,
                "outcome": out, "decided_by": client}

    def op_project(self, society: str = "", group: str = "", name: str = "", space: str = "",
                   as_: str = "dag", **kw) -> Dict[str, Any]:
        """Projection (P7, Part A/B.9) — view a society/workflow/chronon face WITHOUT changing the
        underlying representation. `as=feed|dag|table|narrative`:
          • feed      — the timeline utterances/proposals/decisions (society ≡ chat face).
          • dag       — the chronon:next topology (society ≡ workflow face) + frontiers.
          • table     — chronon counts by aspect (record vs scenario) + frontier count.
          • narrative — a deterministic prose summary (degradation-first; no LLM required).
        Read-level; the same selection can be rendered any of these ways."""
        as_ = (kw.get("as") or as_ or "dag").strip().lower()
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        sid = self._sid(gid, name)
        from lib.akasha.concepts.chronon import ChrononConcept
        chr = ChrononConcept(self.session)
        if as_ == "feed":
            feed = self.op_feed(society=society, group=group, name=name, space=space, limit=200)
            return {"projection": "feed", "society_id": sid, "count": feed["count"],
                    "messages": feed["messages"]}
        ls = chr.op_list(society=society, group=group, name=name, space=space)
        chronons = ls["chronons"]
        if as_ == "table":
            by_aspect: Dict[str, int] = {}
            for r in chronons:
                by_aspect[r["aspect"]] = by_aspect.get(r["aspect"], 0) + 1
            return {"projection": "table", "society_id": sid, "chronons": len(chronons),
                    "by_aspect": by_aspect, "frontiers": len(ls["frontiers"])}
        if as_ == "narrative":
            perf = [r for r in chronons if r["aspect"] == "perfective"]
            pros = [r for r in chronons if r["aspect"] == "prospective"]
            labels = ", ".join(r["label"] or r["cid"] for r in perf) or "nothing yet"
            plan = ", ".join(r["label"] or r["cid"] for r in pros)
            text = (f"The society {sid} has recorded {len(perf)} state(s) ({labels}). "
                    + (f"It has {len(pros)} planned step(s) ahead ({plan}). " if pros else "")
                    + f"Akasha Time stands at {len(ls['frontiers'])} frontier(s).")
            return {"projection": "narrative", "society_id": sid, "text": text,
                    "recorded": len(perf), "planned": len(pros)}
        # default: dag — the chronon:next topology
        edges = []
        for r in chronons:
            for e in ge.core.get_adjacent_links(r["key"], "chronon:next"):
                edges.append([r["chronon"], chr._alias_of(ge, e.get("dst"))])
        return {"projection": "dag", "society_id": sid, "nodes": [r["chronon"] for r in chronons],
                "edges": edges, "frontiers": ls["frontiers"]}

    def op_workflow(self, wf: str = "", society: str = "", group: str = "", name: str = "",
                    space: str = "") -> Dict[str, Any]:
        """Bind a workflow to a society — the law **society ≡ workflow** made concrete (B.9/SC4).
        Reads the `wf:<name>` CSL template (the authoring template) from the caller's cortex,
        **COMPILES it to a PROSPECTIVE chronon graph** in the society's group space (one chronon per
        step, chained by chronon:next), links society --society:workflow--> the root, and aliases the
        root as `scenario:<gid>:<space>:<wf>` so scenario.run drives it (workflow ≡ scenario). Gate:
        admin OR chairman. Step gates are set separately with society.responsible kind=approve:<step>."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        self._gate_admin_or_chairman(ge, society_key, "bind a workflow")
        wfname = (wf or "").strip()
        if not wfname:
            raise ValueError("society.workflow requires wf=<name>.")
        wf_key = self.cortex.resolve_alias(f"wf:{wfname}") if not self.cortex.get_chunk(wfname) else wfname
        if not wf_key:
            raise RuntimeError(f"No workflow 'wf:{wfname}' defined (workflow.def it first).")
        script = self.cortex.get_chunk(wf_key) or ""
        steps = [s.strip() for s in script.replace(";", "\n").split("\n")
                 if s.strip() and not s.strip().startswith("#")]
        if not steps:
            raise ValueError(f"workflow 'wf:{wfname}' has no steps.")
        from lib.akasha.concepts.chronon import ChrononConcept, PROSPECTIVE
        chr = ChrononConcept(self.session)
        prev, root, made = "", "", []
        for i, body in enumerate(steps):
            res = chr._mint(ge, gid, name, society_key, body, label=f"{wfname}:{i+1}",
                            members=[], aspect=PROSPECTIVE, from_key=prev, mutates_key="",
                            scribe=self._client(), advance_now=False)
            if i == 0:
                root = res["key"]
                ge.core.put_alias(root, f"scenario:{gid}:{name}:{wfname}")
            prev = res["key"]
            made.append(res["chronon"])
        # single society:workflow link (replace any prior binding)
        for l in ge.core.get_adjacent_links(society_key, "society:workflow"):
            ge.core.remove_link_raw(society_key, l.get("dst"), "society:workflow")
        ge.put_link(society_key, root, "society:workflow", author=self._client())
        return {"status": "workflow_bound", "society_id": self._sid(gid, name), "wf": wfname,
                "root": made[0] if made else "", "steps": len(made), "chronons": made,
                "scenario": f"scenario:{gid}:{name}:{wfname}"}

    def _owned_or_roster_cast_lenient(self, ge, gid: str, name: str, cast: str) -> (str, str):
        """Resolve a cast id/name to (cast_id, cast_name). Accepts a cast present in the roster OR
        one the caller owns (admission may bring in a cast not yet in the roster). Unlike say, it
        does not require ownership — admission is a governance act by admin/chairman. The display
        name is enriched from the published cast root in the group engine when the feed has none."""
        cid, cname = "", ""
        try:
            cid, cname = self._owned_or_roster_cast(ge, gid, name, cast)
        except Exception:
            cast_s = (cast or "").strip()
            row = ge.core.get_chunk_raw(cast_s) if cast_s else None
            if row:
                try:
                    m = json.loads(row.get("meta") or "{}")
                except Exception:
                    m = {}
                if m.get("concept") == "cast":
                    cid, cname = cast_s, m.get("name", "")
            if not cid:
                cid, cname = self._owned_cast(cast)   # last resort — raises if truly unknown
        if cid and not cname:                          # enrich name from the published root
            row = ge.core.get_chunk_raw(cid)
            if row:
                try:
                    mm = json.loads(row.get("meta") or "{}")
                except Exception:
                    mm = {}
                cname = mm.get("name", "") or cname
        return cid, cname

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _link_world(self, ge, society_key: str, world: str) -> str:
        """Resolve a world (id or title) and link society→world via sys:in_world."""
        world = (world or "").strip()
        if not world:
            return ""
        world_id = world
        if not self.cortex.get_meta(world):
            for wk in self.cortex.get_collection_members("set:world:index"):
                wm = self.cortex.get_meta(wk) or {}
                if wm.get("concept") == "world" and wm.get("title") == world:
                    world_id = wk
                    break
        ge.put_link(society_key, world_id, "sys:in_world", author=self._client())
        return world_id

    def _maybe_open(self, sid: str) -> None:
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, sid)

    @staticmethod
    def _truthy(value: Any) -> bool:
        return str(value).strip().lower() in ("1", "true", "yes", "on") if value is not None else False
