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
from lib.akasha.concepts._universal import slug as _uslug
from lib.akasha import api as _api
from lib.akasha.concepts.workflow import active_kernel as _ACTIVE_KERNEL_FN
from lib.akasha.api.trust import TRUST_INTERNAL as _TRUST_INTERNAL
from lib.akasha.api import facts as _facts
from lib.akasha.api import gate as _gate
from lib.akasha.api import trust as _trust

# The internal identities this module ACTS AS, registered at load (group 4, 4.15). Each is reachable
# only over TRUST_INTERNAL / TRUST_LOCAL; what each may do is its line in `config/identity/assign.ak`.
#   system.broadcaster — mirrors a public society feed to the shared nucleus (the broadcast relay);
#                        librarian to publish universal-scope, a group member of each space to read it.
#   system.moderator   — G2.7, the acting identity of an auto-mode society's moderator: the auto-run
#                        driver drives the moderator AGENT as it, under a declared policy.
#   system.observer    — G2.7, the mandatory scribe of an auto-mode society.
for _sid_name in ("system.broadcaster", "system.moderator", "system.observer"):
    _trust.system_identity(_sid_name, "librarian")

logger = logging.getLogger("Akasha.Concept.Society")

CAST_INDEX_SET = "set:cast:index"           # where a client's owned casts are indexed
CONTEXT_KEY_ACTIVE = "active_society"
DEFAULT_SPACE = "main"

# G2.7 — the auto-execution POLICY the auto moderator cannot exceed. Validated fail-closed: anything
# not listed is refused, so the driver can never admit/grant/revoke/connect/change-mode itself.
_AUTO_POLICY_DEFAULTS = {
    "workflows": [], "trigger": "manual", "auto_dispatch": False,
    "budget": {"runs_per_day": 4, "max_steps": 500, "max_wall_s": 14400},
    "on_failure": {"retries": 1, "breaker": 3}, "run_once": False,
    # Seed-time autonomy (2026-09-07): `requires` = the source pools the auto workflows read; the
    # driver opens a `boot` trigger only when every one exists AND is FROZEN (readiness is DECLARED,
    # not inferred). `then` is what a fired `boot` trigger continues as (`daily:HH:MM`|`interval:<s>`
    # |`none`), so a one-shot boot run can still recur without a second trigger.
    "requires": [], "then": "none",
    # Does this workload's output face a ROOM — a page someone can open? DECIDED ONCE, at the
    # declaration (`workload.publishes_to_room`), and carried here because the driver and the
    # status read it and must not re-derive it. It was NOT carried, and the reader fell back to
    # `effect == publish` — a different question (a channel publishes too and has no room), so the
    # fallback answered for every policy ever stored and the right answer never reached anyone.
    # Dropping the fallback without carrying the key would simply invert the error (P4).
    "room": False,
    # P0-a slice 2 — `sweeps` = the names of sweeps whose branches this society ADMITS for society.run
    # (the armed line reports them; the driver picks branches in P0-b). Names only; the grid definitions
    # ship as config/<bench>/sweeps/<name>.json and are applied at provisioning.
    "sweeps": [],
    # Seed A slice 1 — the DECLARED fields the driver reads, carried verbatim so the policy is the
    # declaration's projection and not a translation of it. `duty` is the only behavioural switch
    # (what the driver owes this workload when a gate stops it), `effect` says whether its output
    # faces the public, `appetite` what one run costs the model provider, and `workload` is the
    # accounting key the provider ledger is kept under. Fail-closed like the rest: an unknown duty
    # or effect falls back to the safe default rather than being carried through.
    "duty": "wb:duty:best_effort", "effect": "record", "appetite": {}, "workload": "",
}
_DUTIES = ("wb:duty:continuous", "wb:duty:best_effort")
_EFFECTS = ("publish", "record")
# The nucleus index the auto-run driver scans: one pointer atom per auto-mode society.
_AUTO_INDEX_SET = "set:society:auto"


def _validate_auto_policy(raw: Any) -> Dict[str, Any]:
    """Coerce + validate an auto-execution policy fail-closed. Unknown keys are dropped; a malformed
    trigger/budget falls back to the default. `workflows` MUST be a non-empty list of names.

    Trigger / then grammar: `manual` | `boot` | `interval:<seconds>` | `daily:HH:MM`. ⚠️ A32 —
    `daily:HH:MM` is evaluated in **UTC** (the driver uses time.gmtime), so `daily:03:00` fires at
    03:00 UTC = 12:00 JST. There is no per-policy timezone field yet; convert to UTC when authoring."""
    p = dict(_AUTO_POLICY_DEFAULTS)
    if isinstance(raw, str) and raw.strip():
        raw = json.loads(raw)
    if isinstance(raw, dict):
        wf = raw.get("workflows")
        if isinstance(wf, list):
            p["workflows"] = [str(w) for w in wf if str(w).strip()]
        trig = str(raw.get("trigger") or p["trigger"])
        if trig == "boot" or trig == "manual" or trig.startswith("interval:") or trig.startswith("daily:"):
            p["trigger"] = trig
        then = str(raw.get("then") or p["then"])
        if then in ("none", "manual") or then.startswith("interval:") or then.startswith("daily:"):
            p["then"] = then
        req = raw.get("requires")
        if isinstance(req, list):
            p["requires"] = [str(x) for x in req if str(x).strip()]
        sw = raw.get("sweeps")            # P0-a slice 2 — preserve the admitted sweep names
        if isinstance(sw, list):
            p["sweeps"] = [str(x) for x in sw if str(x).strip()]
        p["auto_dispatch"] = bool(raw.get("auto_dispatch", False))
        p["run_once"] = bool(raw.get("run_once", False))
        b = raw.get("budget") or {}
        if isinstance(b, dict):
            p["budget"] = {"runs_per_day": int(b.get("runs_per_day", 4)),
                           "max_steps": int(b.get("max_steps", 500)),
                           "max_wall_s": int(b.get("max_wall_s", 14400))}
        duty = str(raw.get("duty") or "")
        if duty in _DUTIES:
            p["duty"] = duty
        eff = str(raw.get("effect") or "")
        if eff in _EFFECTS:
            p["effect"] = eff
        if "room" in raw:
            p["room"] = bool(raw.get("room"))
        ap = raw.get("appetite") or {}
        if isinstance(ap, dict):
            p["appetite"] = {"llm_calls_per_run": int(ap.get("llm_calls_per_run", 0) or 0),
                             "weight": float(ap.get("weight", 0.0) or 0.0)}
        p["workload"] = str(raw.get("workload") or "")
        # 4.12(b) — how the workload's effect is read: carried verbatim when well-formed (an op name
        # and an args dict). The platform dispatches it; it never interprets the row fields.
        er = raw.get("effect_read")
        if isinstance(er, dict) and str(er.get("op") or "").strip() \
                and isinstance(er.get("args", {}), dict):
            p["effect_read"] = {k: v for k, v in er.items()
                                if k in ("op", "args", "rows", "effect", "reason", "at")}
        f = raw.get("on_failure") or {}
        if isinstance(f, dict):
            p["on_failure"] = {"retries": int(f.get("retries", 1)),
                               "breaker": int(f.get("breaker", 3))}
    return p


# ── the programme-state vocabulary this module WRITES ────────────────────────────────────────────
# THE `station:state:*` / `station:reason:*` VOCABULARY IS GONE FROM THIS PLATFORM MODULE, with
# the stamped register that used it (ruling 2026-09-23 §2: "the platform records and answers; the
# application names"). Four states, four reason ids, a `station:show:*` atom per programme and a
# `set:station:state:*` membership — every one of them was the platform deciding what "on air" or
# "standing by" MEANS, which is the station's word for the station's own surface, not a fact about
# a workload. `workload.status` answers with `last`, `gate`, `next_at` and `spent_today`; the
# station Concept Model and the room pages compose the sentence. The atoms keep their home in
# `ontology/station/`, where they always belonged, as the application's own vocabulary.
_MIRROR_WRITER = "system.broadcaster"      # the platform identity the public mirror is written as


class SocietyConcept(BaseConcept):
    CONCEPT_PREFIX = "society"
    CONCEPT_METHODS = {
        "new":    {"op": "op_new"},
        "ls":     {"op": "op_list"},
        "open":   {"op": "op_open"},
        "join":   {"op": "op_join"},
        "say":    {"op": "op_say", "effectful": True},   # B5 §A7 — a feed write leaves the world
        # A programme turn IS the workload speaking, and the relay IS putting it in front of
        # the public — `say` and `publish`, declared, because the verb convention derives
        # `record` for both and the `programme` row has no `record` (ruling §1).
        "air":    {"op": "op_air", "action": "say", "effectful": True},   # one programme turn — FORWARDS to the bench
        "feed":   {"op": "op_feed"},
        "roster": {"op": "op_roster"},
        "turn":   {"op": "op_turn"},
        "world":  {"op": "op_world"},
        "info":   {"op": "op_info"},
        "decider": {"op": "op_decider"},   # designate the responsible cast (coworking anchor)
        # ── seeds13 governance (Agent / Responsible / Chairman delegation) ──
        "admit":       {"op": "op_admit"},        # admit a cast → mint its agent binding
        "chairman":    {"op": "op_chairman"},     # appoint the chairman (admin-only delegation)
        "moderator":   {"op": "op_moderator"},    # G2.2 — alias of chairman (admin-only, one)
        "responsible": {"op": "op_responsible"},  # set scribe/broadcaster/operator:<F>/… (admin or chairman)
        "role":        {"op": "op_role"},         # G2.2 — the five world-society roles (thin front)
        "connect":     {"op": "op_connect"},      # G2.1 — connect the society to a bench (society:connected)
        "sever":       {"op": "op_sever"},        # G2.1 — sever a society↔bench connection
        # A run IS a job (ruling §3), so the action is `run` — not the `record` the verb
        # convention would derive. Declared, because the convention cannot know it.
        "run":         {"op": "op_run", "action": "run"},   # G2.7 — enqueue one auto-policy run
        "now":         {"op": "op_now"},          # read the society's chronon frontier(s)
        "workflow":    {"op": "op_workflow"},     # bind a wf: → compile it to a prospective chronon graph
        "project":     {"op": "op_project"},      # projection: view a society/workflow/chronon face
        # ── seeds13 deliberation (協議 / 採決 / 意思決定 — typed feed atoms, no schema change) ──
        "propose":     {"op": "op_propose"},      # table a proposal (step of a workflow)
        "vote":        {"op": "op_vote"},         # cast a vote on a proposal
        "tally":       {"op": "op_tally"},        # count the votes on a proposal
        "decide":      {"op": "op_decide"},       # record the decision (chairman/decider/admin, or tally)
        "guest":  {"op": "op_guest"},      # toggle the open_guest gate (external-LLM guests)
        "public": {"op": "op_public", "effectful": True},  # publish gate — exposes the feed to the world (B5/§3)
        # ONE public-feed read, under three names. `society.feed.read` is what it is; the two
        # `broadcast` spellings are aliases kept so a rendered page and a running script do not
        # break on the rename. They dispatch to the same op, so the member view and the guest view
        # cannot drift — which is what they had been doing.
        "feed.read":       {"op": "op_feed_read"},
        "broadcast":       {"op": "op_feed_read"},
        # ── public-experiment broadcasting (station → studios → talk shows) ──
        "broadcast.relay": {"op": "op_broadcast_relay", "action": "publish", "effectful": True},  # MECHANISM: mirror a public feed → nucleus (B5: leaves the world)
        "broadcast.live":  {"op": "op_feed_read"},        # alias — the archives live view
        "broadcast.gc":    {"op": "op_broadcast_gc"},     # HARD backlog purge of orphaned mirror atoms (F55)
        "rm":     {"op": "op_delete"},
    }

    # ── space addressing ─────────────────────────────────────────────────────────
    def resolve_society(self, group: str = "", name: str = "", society: str = "",
                        space: str = "") -> (str, str):
        """PUBLIC (group 4, 4.16) — resolve a space to (gid, name). Accepts an explicit `society` id ("<gid>/<name>" or a
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
    def society_id(gid: str, name: str) -> str:
        """PUBLIC (group 4, 4.16) — the society id `<gid>/<name>`, the inverse of `resolve_society`."""
        return f"{gid}/{name}"

    # The old spellings, kept ONE seed while the application switches (4.16).
    _resolve = resolve_society
    _sid = society_id

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

    def _public_fact(self, gid: str, name: str) -> bool:
        """Is this space public? Read from `set:society:public` — the ONE fact Set step 4 consults
        (`publish` needs target ∈ public). It used to read the group-engine set directly, which
        meant the concept and the gate answered the same question from two stores; the consent op
        writes both, but only one of them decides."""
        return _facts.has(_ACTIVE_KERNEL_FN(), _facts.PUBLIC, self._sid(gid, name))

    # Attribution notices for AI-generated utterances shown publicly — required by the model
    # providers' terms/brand rules and by AI-disclosure norms (e.g. EU AI Act transparency). The
    # gateway stamps provider/model on a guest's utterance; the public broadcast renders the notice.
    _PROVIDER_NOTICE = {
        "gemini": "Powered by Google Gemini",
        "openrouter": "via OpenRouter",
        "mistral": "Mistral AI model",
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
    def attribution_notice(cls, provider: str, model: str, mode: str = "") -> str:
        """The public-display disclosure + attribution for one utterance. HONESTY IS THE CONTRACT
        (anti-ヤラセ): a line that was SCRIPTED by Akasha (read from a 台本, or a canned quip) is NOT an
        external LLM's work and must NOT claim to be — it returns a "Scripted" notice. Only a line an
        external LLM actually generated returns the "AI-generated · <licence>" attribution its terms
        require. Empty for a plain human line."""
        provider = (provider or "").strip().lower()
        model = (model or "").strip().lower()
        mode = (mode or "").strip().lower()
        if mode in ("script", "quip") or provider in ("", "akasha"):
            # machine-assembled by Akasha itself, no external model in the loop — say so plainly
            return "Scripted from the graph — Akasha, no external LLM" if mode or provider == "akasha" else ""
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

    def _say_cast(self, gid: str, name: str, cast: str) -> (str, str):
        """Resolve a cast to (cast_id, cast_name), and ASK THE GATE whether this speaker may use
        it (`gate(client, say, <gid>/<name>, cast=…)`).

        This replaces the cast-OWNERSHIP check, which asked whether the caller owned the avatar — a second
        store of the same fact, and the check that burned two days of model calls. The casts a
        workload speaks through belong to the WORKLOAD, not to whoever created them (provisioning
        runs as admin), so ownership answers the wrong question. Step 4 answers the right one: a
        cast that is one of the target's declared roles, OR the speaker's own identity, so a human
        member speaks as itself with no avatar and no `provision`.

        Resolution stays local — the roster and the caller's own cortex both name casts — but the
        DECISION is the gate's and is made here, once, before anything is written or paid for.

        AN UNDECLARED CAST IS REFUSED, and there is no second question. I had added a fallback
        here — if step 4 said `roles`, ask whether the speaker may `record` on the space, on the
        grounds that `society.say` auto-registers an avatar on its first utterance and the real
        question was "may this speaker ADD a role". It is one function asked twice, which is why
        it looked defensible, and it cost a guarantee the station eval exists to hold: an `admin`
        has `record` everywhere, so a turn naming a role the workload does NOT declare
        (`role=Listener` on a shelf that declares Reader and Commentator) was admitted and AIRED
        instead of standing by. Step 4 is the ruling's, exactly: a declared role, or the speaker
        itself. Putting a new avatar into a space is `society.join`, which is `record`, asked at
        the op that actually does it — which is what provisioning has always called."""
        cast = (cast or "").strip()
        who = self._client()
        if not cast:
            cast = who              # say as oneself: the speaker IS the cast (ruling §1)
        # RESOLVE FIRST, then decide. Resolution is not a permission — it turns whichever spelling
        # the caller used (a cast id, a cast name, or nothing at all) into the one identifier the
        # roster holds. Asking step 4 with the raw spelling meant a cast joined BY ID was sayable
        # by id and refused by name: one cast, two answers, decided by how the caller happened to
        # type it. The gate is asked with the canonical id, and `_declared_casts` carries both
        # spellings so either way in resolves to the same question.
        cid, cname = self._resolve_cast(cast)
        sid = self._sid(gid, name)
        declared = self._declared_casts(gid, name)
        ok, why = _gate.gate(who, _gate.SAY, sid, cast=cid, declared_casts=declared)
        if not ok and cast != cid:
            ok, why = _gate.gate(who, _gate.SAY, sid, cast=cast, declared_casts=declared)
        if not ok:
            _gate.refuse_log(who, _gate.SAY, sid, why)
            raise RuntimeError("%s: say as '%s'" % (why, cast))
        return cid, cname

    def _resolve_cast(self, cast: str) -> (str, str):
        """RESOLUTION ONLY — a cast id/name to (cast_id, cast_name). Decides nothing.

        Split out of `_say_cast` because two callers need the lookup WITHOUT the say decision, and
        one of them broke when the decision arrived. `society.admit` resolves a cast in order to
        ADMIT it, and admitting is what makes it a declared role — so asking step 4 first is a
        question that can only be answered after the act it guards. `_owned_or_roster_cast_lenient`
        said so in its own docstring ("admission is a governance act, unlike say") and then called
        the deciding resolver anyway, which left every bench eval with an empty grant table and a
        society nobody had been admitted to."""
        cast = (cast or "").strip()
        meta = self.cortex.get_meta(cast)
        if meta and meta.get("concept") == "cast":
            return cast, meta.get("name", "")
        for key in self.cortex.get_collection_members(CAST_INDEX_SET):
            m = self.cortex.get_meta(key)
            if m and m.get("concept") == "cast" and m.get("name") == cast:
                return key, m.get("name", "")
        return cast, cast           # speaking as oneself, or as a roster name with no local atom

    def _declared_casts(self, gid: str, name: str) -> list:
        """The roles this space declares — what step 4 compares the caller's `cast=` against.

        Read from the ROSTER, which provisioning fills from the declaration's `roles`. The
        declaration is the source; the roster is its read, and it is the one this concept can
        reach without importing the workbench (a rightward import, §A21).

        BOTH SPELLINGS, because `society.say cast=` accepts both. The roster Set holds cast
        IDS; a caller — and every one of the declared workloads' templates — names a cast by its
        NAME (`turn role=Curator`). Names used to enter this list only through the FEED, i.e.
        only for a cast that had already spoken, so a declared role was refused on its FIRST
        utterance and admitted from the second: the station produced four turns and said none of
        them (`turn produced but NOT said … role=Curator`). The agent atom provisioning mints at
        admission carries `cast_name`, which is the same source `society.roster` renders from, so
        the name is read from there and the two spellings answer alike."""
        try:
            ge = self._group_engine(gid)
            out = [n for n in self._feed_name_map(ge, gid, name).values() if n]
            for cid in (ge.core.get_collection_members(self._roster_set(gid, name)) or []):
                out.append(cid)
                # …and the roster id's NAME, resolved the way `society.roster` resolves it: from
                # the published cast root in the group engine. A cast joined by id would otherwise
                # be sayable by id and refused by name, which is one cast with two answers.
                row = ge.core.get_chunk_raw(cid)
                if row:
                    try:
                        nm = (json.loads(row.get("meta") or "{}") or {}).get("name")
                    except Exception:
                        nm = None
                    if nm and nm not in out:
                        out.append(nm)
            for akey in (ge.core.get_collection_members(self._agents_set(gid, name)) or []):
                am = self._society_meta(ge, akey)
                if am.get("concept") == "agent":
                    for v in (am.get("cast_name"), am.get("cast")):
                        if v and v not in out:
                            out.append(v)
            return out
        except Exception:
            return []

    def _society_key(self, ge, gid: str, name: str) -> Optional[str]:
        return ge.resolve_alias(self._society_alias(gid, name))

    # ── PUBLIC READS for another Concept Model ─────────────────────────────────────────────────────
    # The application's station concept reached for `_group_engine` + `_society_key` to ask "is
    # there a society here, and which atom is it", and for `_declared_casts` to hand the gate the
    # roles a space declares — because no public read answered either question. A private member
    # is free to change shape; an application that calls it breaks on the platform's next refactor
    # and cannot be told so by any contract. These two are the contract, and they are READS: the
    # caller's session decides what it can see, exactly as the private path did.

    def society_key(self, gid: str, space: str) -> str:
        """The society atom's key for `<gid>/<space>`, or "" when there is none THIS SESSION CAN SEE.

        "" covers both "no such society" and "not a member of the group" — the same answer the
        private path gave by raising, and the fail-closed one: a caller that cannot see a society
        cannot be told whether it exists. Never raises."""
        try:
            return str(self._society_key(self._group_engine(gid), gid, space) or "")
        except Exception:
            return ""

    def declared_casts(self, gid: str, space: str) -> list:
        """The roles this space declares, by id AND by name — what the gate's `say` step compares a
        caller's `cast=` against, so a probe asked with this list answers exactly as the feed write
        will. [] when the society cannot be read. See `_declared_casts` for why both spellings."""
        return list(self._declared_casts(gid, space) or [])

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
            cid, cname = self._say_cast(gid, name, cast)
            if cid in roster:
                return cid, cname
        except Exception:
            pass
        raise RuntimeError(f"'{cast}' is not an avatar present in this space.")

    # ── operators ────────────────────────────────────────────────────────────────
    def op_new(self, group: str = "", name: str = DEFAULT_SPACE, topic: str = "",
               world: str = "", society: str = "", space: str = "", kind: str = "chat",
               open_guest: Any = False, public: Any = False, category: str = "",
               daily_budget: Any = 0, segments: str = "", bench: str = "",
               identity: str = "open") -> Dict[str, Any]:
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
        try:
            budget = max(0, int(daily_budget or 0))
        except (TypeError, ValueError):
            budget = 0
        seg_list = [s.strip() for s in (segments or "").split("|") if s.strip()]
        meta = {"type": "society", "concept": "society", "group": gid, "name": name,
                "sid": sid, "topic": topic, "kind": kind if kind in ("chat", "cowork") else "chat",
                "category": (category or "").strip(), "daily_budget": budget, "segments": seg_list,
                "identity": ("locked" if str(identity).strip().lower() == "locked" else "open"),
                "created_by": owner, "created_at": time.time()}
        # Store the connected bench NAME directly on the society (op_run reads `bench_name` first). A
        # PUBLIC bench lives in the nucleus, so the `society:connected` link points at a nucleus key
        # whose alias the group engine cannot resolve — a stored name makes society.run/the auto driver
        # work for a public bench too, not only a closed one (the `_bench_name_for` link-walk fallback
        # stays for pre-existing societies).
        if bench:
            meta["bench_name"] = bench
        key = ge.put_atom(f"[ Society: {sid} ]", meta, author=owner)
        ge.core.put_alias(key, self._society_alias(gid, name))
        ge.add_to_set(f"societies:{gid}", key)
        # feed/roster sets are created lazily on first add_to_set (as cast.publish relies on).
        linked = ""
        if world:
            linked = self._link_world(ge, key, world)
            # G2.1 — a society ON THE WORLD: record society.formed on the world axis, and when it is
            # bound to a bench, link society:connected + record society.connected. `world=` names the
            # commons clock (default: "default"); the axis lives in the nucleus (world-level).
            wname = self._world_name(world)
            self._world_record(kind="society.formed", ref=sid, note=name, world=wname)
            if bench:
                bkey = self._bench_key(ge, bench)
                if bkey:
                    ge.put_link(key, bkey, "society:connected", author=self._client())
                    self._register_bench_conn(gid, name, key, bkey, bench)   # public-bench grant bridge
                self._world_record(kind="society.connected", ref=sid,
                                            note=f"{name}→wb:{_uslug(bench)}", world=wname)
        og = self._truthy(open_guest)
        if og:
            ge.add_to_set(self._guest_set(gid), key)
        pub = self._truthy(public)
        if pub:
            ge.add_to_set(self._public_set(gid), key)
        # …AND STATE IT AS THE FACT, because `society.new public=yes` is the SECOND door to the
        # same consent and `_public_fact` reads only the fact Set now. Writing the group-local
        # Set alone left a space that answered `public: true` to its creator and "not a public
        # broadcast" to the gate, the guest and the relay — the precise disagreement a fact Set
        # exists to make impossible. The fact is idempotent, so a create followed by
        # `society.public open=yes` states the same thing twice and means it once.
        _facts.public(_ACTIVE_KERNEL_FN(), sid, pub)
        self._maybe_open(sid)
        logger.info("[Society] created %s (kind=%s, topic=%r, world=%r, open_guest=%s, public=%s)",
                    sid, meta["kind"], topic, linked, og, pub)
        return {"status": "created", "society_id": sid, "key": key, "group": gid,
                "name": name, "kind": meta["kind"], "topic": topic, "world": linked,
                "identity": meta["identity"], "bench": (f"wb:{_uslug(bench)}" if bench else None),
                "connected": bool(world and bench), "open_guest": og, "public": pub}

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
        current = self._public_fact(gid, name)
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
        # …and state it where everyone can read it. The group-local Set above can only be asked
        # by something holding this group's engine, which is why the publicness test had to live inside
        # this concept and why every other reader grew its own copy of the question. The fact
        # Set is universal: the gate, a guest, the guide and an eval all get the same answer
        # (order 2026-09-22 §2). `society.public` is the ONE writer of it.
        _facts.public(_ACTIVE_KERNEL_FN(), self._sid(gid, name), want)
        return {"status": "public_policy", "society_id": self._sid(gid, name), "public": want}

    # ── public-experiment broadcasting: the nucleus mirror + station registry ─────────
    # A PUBLIC space's feed is group-scoped, so an unauthenticated archives page cannot read it. A
    # BROADCASTER (a group member that also holds role:librarian — e.g. system.broadcaster) MIRRORS
    # the public feed into the SHARED NUCLEUS at scope:sys:universal, exactly like live telemetry:
    # guests then read it through the composite's nucleus merge. All broadcasting reads/writes below
    # sit on top of that mirror, never on the group feed, so no group scope is ever needed to VIEW.
    _BROADCAST_PROV = "broadcast"
    # ONE disclosure contract (F21), served identically by op_broadcast (member view) and
    # op_broadcast_live (guest view) and reused by the X relay — so the surfaces cannot drift. The
    # honesty contract: distinguish Scripted vs AI-generated and state that no line is written by a
    # human. Per-message ai_notice carries the licence; this banner is the standing frame.
    _DISCLOSURE_BANNER = ("Machine-assembled from Akasha's knowledge graph. Lines marked "
                          "'Scripted' are read from the graph (no external LLM); lines marked "
                          "'AI-generated' are produced by an external language model. A "
                          "transparency experiment in LLM participation — never a human.")

    @staticmethod
    def _broadcast_set(gid: str, name: str) -> str:
        return f"broadcast:{gid}:{name}"        # the public mirror timeline for one show (nucleus)

    def _nuc_put(self, nuc, alias: str, content: str, meta: Dict[str, Any], sets=()):
        """Idempotent nucleus write at scope:sys:universal (mirror of feed._mint): reuse by alias,
        else create + alias + set-add. Returns the atom key."""
        core = nuc.core
        key = core.get_key_by_alias(alias)
        if not key:
            import hashlib
            key = hashlib.sha256((content or alias).encode("utf-8")).hexdigest()
            core.put_chunk_raw(key, content, json.dumps(meta, ensure_ascii=False),
                               self._client(), "verified", time.time())
            core.put_chunk_access(key, ["scope:sys:universal"])
            try:
                core.put_alias(key, alias)
            except Exception:
                pass
        for s in sets:
            try:
                core.add_to_collection(s, key)
            except Exception:
                pass
        return key

    def _mirror_writer(self):
        """The nucleus handle the public mirror is written through — the PLATFORM's mirror-writer
        identity, whatever client asked for the pass (step 2 §1).

        The relay used to demand that the CALLER carry role:librarian, which made a mechanism into a
        privilege the caller had to bring: provisioning ran it as admin, a workflow step could not,
        and the one thing it does — copy a message a society has already consented to publish into
        the universal scope — is the same act whoever asks. The CONSENT is still checked (a
        non-public space is refused, above); what changed is that the WRITE no longer borrows the
        asker's role — and no role is compared here at all (the purge order §4.1)."""
        try:                       # always the mirror writer, never the caller
            from lib.akasha.concepts.base import BaseConcept as _BC     # noqa: F401  (session shape)
            sess = _ACTIVE_KERNEL_FN().manager.get_session(_MIRROR_WRITER)
            return getattr(sess.local_cortex, "_nucleus", None)
        except Exception as exc:   # noqa: BLE001 — reported, never silent
            logger.warning("[society] skipped reason=no_mirror_writer detail=%s", exc)
            return None

    def _mirror_cursor(self, gid: str, name: str, value: float = None) -> float:
        """The per-show relay cursor, read or written — a record ON THE SOCIETY.

        It lived in `kernel._broadcast_cursors`, a dict on the heart: application state on the
        platform, lost on every restart, and invisible to anyone reading the society. Then it lived
        on the stamped guide row `station:show:<gid>:<space>` — which is deleted (ruling
        2026-09-23), and a bookmark is not status anyway: how far a mirror has copied is the RELAY's
        own mechanism, while `on air` is the station's word for a person.

        It is a field on the SOCIETY the relay mirrors, beside `autorun`. Same property as before —
        a restart resumes where the last pass stopped, and a person reading the society can see how
        far the mirror has got — with nothing of the application's in it."""
        try:
            ge = self._group_engine(gid)
            sk = self._society_key(ge, gid, name)
            if not sk:
                return 0.0
            sm = self._society_meta(ge, sk)
            if value is None:
                return float(sm.get("relay_cursor") or 0.0)
            sm["relay_cursor"] = float(value)
            self._write_society_meta(ge, sk, sm)
            return float(value)
        except Exception:
            return 0.0

    def op_broadcast_relay(self, society: str = "", group: str = "", name: str = "",
                           space: str = "", since: Any = 0) -> Dict[str, Any]:
        """[society.broadcast.relay] MECHANISM (one relay pass). Read a PUBLIC space's feed since the
        cursor and MIRROR each new message into the shared nucleus (`broadcast:<gid>:<space>` @
        scope:sys:universal), baking the AI disclosure (`ai_notice`) IN at mirror time so the public
        copy is self-contained. Idempotent (content-addressed by source key). Requires the caller to
        be a group MEMBER (to read the feed) AND role:librarian (to publish the mirror) — i.e. the
        broadcaster. Refuses a non-public space. Registers the show in the station lineup. Returns
        {sid, mirrored, skipped, cursor}. A loop (society_broadcaster.py, later svc:broadcast-relay)
        calls this repeatedly, carrying `cursor` back as `since`.

        THE QUESTION IS ASKED AS THE PUBLIC, and it is `read`. Two mistakes were available here
        and this op made both in turn:

        · asking `publish` as the CALLER re-created the gate the ruling deletes (the mirror
          writer's role test, "that made the relay a privilege", §6) under a new word — `publish` is on
          `admin`/`librarian`/`programme`, so a group member relaying their own public space was
          refused again. The mirror write is the MIRROR WRITER's authority, not the caller's;
        · asking `read` as the caller loses the CONSENT. An operator's row reaches everything, so
          step 4's `public` fact is not consulted for them (§4: "`read` needs target ∈ public
          *unless idset.on covers it*") — and a relay that refuses a private space for everyone
          except the one person likely to run it refuses nobody.

        So the question is the one `society.broadcast` asks, and the ruling's own sentence for this
        surface: "the public feed asks `gate(guest, read, key)`". What is being decided is whether
        the PUBLIC may read this feed — because that is precisely what the relay is about to make
        true. Whether the CALLER may read it is settled below, by `op_feed`, which refuses a
        non-member outright."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        key = self._society_key(ge, gid, name)
        _sid = self._sid(gid, name)
        _ok, _why = _gate.gate("anonymous", _gate.READ, _sid)
        if not key or not _ok:
            raise RuntimeError(f"{_why or _gate.R_PUBLIC}: '{_sid}' is not a public broadcast "
                               f"(set it with society.public open=yes).")
        nuc = self._mirror_writer()
        if nuc is None:
            raise RuntimeError("society.broadcast.relay has no mirror writer on this cell.")
        try:
            since_ts = float(since or 0)
        except (TypeError, ValueError):
            since_ts = 0.0
        if not since_ts:
            since_ts = self._mirror_cursor(gid, name)   # resume where the last pass stopped
        feed = self.op_feed(society=society, group=group, name=name, space=space, limit=200)
        info = self.op_info(society=society, group=group, name=name, space=space)
        sid = feed["society_id"]
        bset = self._broadcast_set(gid, name)
        mirrored, skipped, newest = 0, 0, since_ts
        for m in feed["messages"]:
            ct = float(m.get("created_at", 0) or 0)
            if ct <= since_ts:
                continue
            src_key = m.get("key", "")
            mode = m.get("mode", "")
            note = self.attribution_notice(m.get("provider", ""), m.get("model", ""), mode)
            # an external LLM in the loop ⇒ real AI; a scripted/quip line is machine-assembled, NOT AI
            is_llm = bool((m.get("provider") or "").strip() and (m.get("provider") or "").strip().lower() != "akasha")
            mmeta = {"concept": "broadcast_msg", "sid": sid, "space": name,
                     "from_cast": m.get("from_cast", ""), "cast_name": m.get("cast_name", ""),
                     "provider": m.get("provider", ""), "model": m.get("model", ""),
                     "ai": is_llm, "ai_notice": note, "mode": mode, "source": m.get("source", ""),
                     # THE SPACE'S OWN LABELS, BAKED IN AT MIRROR TIME — the same reason the AI
                     # notice is baked here: a guest has no group scope, so anything the public
                     # read must show has to already be in the public copy. They used to come from
                     # the stamped `station:show:*` register, which is deleted (ruling 2026-09-23);
                     # these are the society's OWN labels carried across the consent boundary, not
                     # a status the platform decided.
                     "topic": info.get("topic", ""), "kind": info.get("kind", "chat"),
                     "category": info.get("category", ""),
                     "turn": m.get("turn", 0),      # the chronon turn this line belongs to (Akasha Time)
                     "created_at": ct, "src_key": src_key, "reply_to": m.get("reply_to", ""),
                     "provenance": self._BROADCAST_PROV}
            import hashlib
            alias = f"broadcast:msg:{hashlib.sha256(f'{sid}|{src_key}'.encode()).hexdigest()[:12]}"
            before = nuc.core.get_key_by_alias(alias)
            # A48.1 — a mirror atom joins BOTH its rolling window (`bset`, trimmed) AND a durable
            # per-society mirror registry, so `station.compact` can iterate the mirror (O(mirror)) to
            # find orphans instead of decoding every atom in the store (the nightly O(store) sweep).
            self._nuc_put(nuc, alias, m.get("text", ""), mmeta, sets=(bset, f"broadcast:mirror:{gid}"))
            if before:
                skipped += 1
            else:
                mirrored += 1
            newest = max(newest, ct)
        # The relay used to REGISTER/refresh the show in the station lineup here. That register is
        # deleted (ruling 2026-09-23): mirroring a message and maintaining a status row are two
        # jobs, and the second was the platform keeping a second copy of facts — `last_post_at`,
        # `today`, `state` — that the mirror and the bench stream already hold. The relay does the
        # one thing it is for: it copies what a society consented to publish into the public store.
        self._trim_broadcast(nuc, bset)          # bound the always-on mirror's growth (rolling window)
        self._trim_feed(ge, gid, name)           # bound the raw group feed too (else it grows forever)
        self._mirror_cursor(gid, name, newest)   # the cursor is the society's, not a kernel attribute
        return {"sid": sid, "mirrored": mirrored, "skipped": skipped, "cursor": newest}

    _BROADCAST_KEEP = 240        # rolling window of mirrored messages kept per show (bounds growth)
    _FEED_KEEP = 400             # rolling window of the raw group feed for an always-on broadcast space

    def _trim_feed(self, ge, gid: str, name: str) -> None:
        """Bound the raw GROUP FEED of an always-on broadcast space: the relay only ever reads the last
        ~200 and guests read the nucleus mirror, so the raw feed need not grow forever (an unbounded feed
        is what made station.poll clear time out). Drops the OLDEST overflow beyond _FEED_KEEP, at most 50
        per pass so it NEVER blocks the relay — a pre-grown feed shrinks over a few passes, then stays
        bounded. Insertion-order approximate (no per-member read) so it is cheap even on a big feed."""
        fset = self._feed_set(gid, name)
        try:
            members = list(ge.core.get_collection_members(fset) or [])
        except Exception:
            return
        overflow = len(members) - self._FEED_KEEP
        if overflow <= 0:
            return
        for k in members[:min(overflow, 50)]:        # oldest-first; bounded per pass
            try:
                ge.core.remove_from_collection(fset, k)
            except Exception:
                pass

    def _trim_broadcast(self, nuc, bset: str) -> None:
        """Bound the public mirror: an always-on station appends forever, so keep only the newest
        _BROADCAST_KEEP messages in the guest-read set (the page shows a rolling live window, not an
        archive). Drops the OLDEST overflow, ordered by the mirrored atom's created_at so it is correct
        regardless of collection order. Idempotent; only pays a cost when over the cap.

        F55 §2 — HARD eviction (memory-discipline R5/C2): the overflow atom is `drop_chunk`ed, not
        merely removed from the set. A mirror atom is a self-contained copy (no inbound links, its
        alias `broadcast:msg:*` is not referenced elsewhere), so dropping it fully reclaims the RAM —
        soft removal from the set alone is what let ~76k orphaned mirror atoms accumulate."""
        core = nuc.core
        try:
            members = list(core.get_collection_members(bset) or [])
        except Exception:
            return
        if len(members) <= self._BROADCAST_KEEP:
            return
        def _ts(k):
            try:
                return float((self.cortex.get_meta(k) or {}).get("created_at", 0) or 0)
            except Exception:
                return 0.0
        members.sort(key=_ts)
        for k in members[:len(members) - self._BROADCAST_KEEP]:
            try:
                for coll in list(core.get_collections_for_key(k) or [bset]):
                    try:
                        core.remove_from_collection(coll, k)
                    except Exception:
                        pass
                core.drop_chunk(k)                    # full C2 eviction — links + alias go with it
            except Exception:
                pass

    def op_broadcast_gc(self, limit: Any = 0) -> Dict[str, Any]:
        """[society.broadcast.gc] HARD backlog purge (F55 §2, memory-discipline R5/C2) of the public
        mirror: `drop_chunk` every `broadcast_msg` atom that is no longer in ANY live broadcast window
        set — the ORPHANS left resident by the pre-F55 soft trim (removed from the set, never dropped),
        which is what let ~76k mirror atoms accumulate. A message still inside its show's rolling window
        (`broadcast:<gid>:<space>`) is KEPT; only atoms with no such membership are dropped, so the live
        page is untouched.

        Writer-side + BOUNDED (`limit` drops per pass, default 20000; `truncated` flags a re-run needed)
        — the nightly job re-enters until clean. Idempotent. The gate admits `record` on `universal`
        (operator, librarian); the purge writes as the mirror writer. Going forward `_trim_broadcast` drops overflow inline, so this is the one-off
        backlog drain plus a safety net."""
        # The GATE decides who may purge the universal mirror (record on `universal` — the operator
        # and the librarian rows); the op compares no role (the purge order §4.1).
        from lib.akasha.api import gate as _gate
        ok, why = _gate.gate(self._client(), _gate.RECORD, _gate.UNIVERSAL)
        if not ok:
            raise PermissionError("society.broadcast.gc: refused (%s)" % why)
        nuc = self._mirror_writer()
        if nuc is None:
            return {"status": "skipped", "note": "society.broadcast.gc: no mirror writer on this cell"}
        core = nuc.core
        try:
            budget = int(limit) if int(limit) > 0 else 20000
        except (TypeError, ValueError):
            budget = 20000
        try:
            from lib.akasha import memtrace as _mt
            _rss0 = _mt._rss_mb()
        except Exception:
            _mt, _rss0 = None, None
        # A48.1 — iterate the per-society MIRROR registries (O(mirror)) and check orphan-ness per member,
        # instead of decoding every atom in the store to find the trimmed-out orphans (the F33/F50 "O(K),
        # never O(store)" rule — the old iter_all_chunks sweep left ~110 MB resident every night).
        try:
            registries = [c for c in (core.get_distinct_collection_names() or [])
                          if str(c).startswith("broadcast:mirror:")]
        except Exception:
            registries = []

        def _phase(name, fn):
            """A56 §2 — run one sweep phase and log `[station.compact] phase=<n> n= Δrss= t=`, so a
            regression names its phase. The orphan test (scan) reads only the collections table
            (get_collections_for_key) — NEVER a body; a body is touched only by drop_chunk."""
            r0 = _mt._rss_mb() if _mt is not None else None
            t0 = time.time()
            n, out = fn()
            r1 = _mt._rss_mb() if _mt is not None else None
            dr = round(r1 - r0, 1) if (r0 is not None and r1 is not None) else "?"
            logger.info("[mirror.compact] phase=%s n=%d Δrss=%sMB t=%ss",
                        name, n, dr, round(time.time() - t0, 1))
            return out

        # ── scan: orphan-ness from META only (the collections table), never the body ──
        state = {"victims": [], "scanned": 0, "truncated": False}

        def _scan():
            for cname in registries:
                for k in (core.get_collection_members(cname) or []):
                    state["scanned"] += 1
                    if not k:
                        continue
                    colls = list(core.get_collections_for_key(k) or [])
                    if any(str(c).startswith("broadcast:") and not str(c).startswith("broadcast:msg:")
                           and not str(c).startswith("broadcast:mirror:") for c in colls):
                        continue                          # still in a LIVE broadcast window → keep
                    state["victims"].append(k)
                    if len(state["victims"]) >= budget:
                        state["truncated"] = True
                        break
                if state["truncated"]:
                    break
            return state["scanned"], None

        def _drop():
            dropped = 0
            for k in state["victims"]:
                if not k:
                    continue
                try:
                    for coll in list(core.get_collections_for_key(k) or []):
                        try:
                            core.remove_from_collection(coll, k)
                        except Exception:
                            pass
                    core.drop_chunk(k)                    # the ONLY body touch, and only for a dropped entry
                    dropped += 1
                except Exception:
                    pass
            return dropped, dropped

        _phase("scan", _scan)
        dropped = _phase("drop", _drop)
        # A58 — phase=commit: return the sweep's transient allocations to the OS (gc + malloc_trim), so
        # the summary Δrss (the +75MB that landed OUTSIDE scan/drop) is accounted and does not become the
        # writer's permanent floor. `retained` = RSS after the trim minus RSS before the whole sweep.
        def _commit():
            if _mt is not None:
                _mt.gc_trim()
            return 0, None
        _phase("commit", _commit)
        scanned, truncated = state["scanned"], state["truncated"]
        _rss1 = _mt._rss_mb() if _mt is not None else None
        _dr = round(_rss1 - _rss0, 1) if (_rss0 is not None and _rss1 is not None) else "?"
        logger.info("[mirror.compact] mirror backlog: scanned=%d orphans_dropped=%d truncated=%s "
                    "Δrss=%sMB retained=%sMB", scanned, dropped, truncated, _dr, _dr)
        return {"status": "ok", "type": "broadcast:gc", "scanned": scanned,
                "dropped": dropped, "truncated": truncated, "retained": _dr}

    # `set_programme_appetite` is GONE with the register it stamped. A programme's declared cost is
    # in its DECLARATION, which provisioning already reads and `workload.status` already reports as
    # `spent_today` against it; copying it onto a platform-owned guide row made the declaration and
    # the row two answers to one question, and the row was the one a page happened to read.
    def op_feed_read(self, society: str = "", group: str = "", name: str = "",
                     space: str = "", since: Any = 0, limit: Any = 100) -> Dict[str, Any]:
        """[society.feed.read] THE public-feed read, and the only one. `society.broadcast` and
        `society.broadcast.live` are aliases of it.

        THE GATE ANSWERS, AND NOTHING ELSE DOES. `op_broadcast` used to open the group engine ten
        lines BEFORE it asked the gate — `self._group_engine(gid)` raises for a non-member, so a
        GUEST was refused by a membership test that the gate had already been moved to replace.
        A second gate, inside the op the stage-2 note said had moved (ruling 2026-09-23 §1). The
        question is asked once, as the PUBLIC, because this surface's whole job is the consent
        boundary: `gate("anonymous", read, sid)`, and step 4 requires the public fact.

        THEN IT READS THE PUBLIC SET. The mirror `broadcast:<gid>:<space>` lives in the shared
        nucleus at `scope:sys:universal`, so no group scope is needed to view it — which is what
        makes ONE op serve the member and the guest instead of two that drift apart. `since=<epoch>`
        returns only what is newer; the response carries `cursor`.

        ORDERED BY `created_at`, AND BY NOTHING ELSE. The sort was `(turn, created_at)`, and `turn`
        is APPLICATION data: the station's sealing restarted its sequence at 1, so a whole day's
        turns sorted before the previous day's and fell off every windowed read — the rooms held at
        yesterday while today's lines sat in the mirror. Time is the platform's and it does not
        reset; a turn number is the application's and may."""
        gid, name = self._resolve(group, name, society, space)
        _sid = self._sid(gid, name)
        _ok, _why = _gate.gate("anonymous", _gate.READ, _sid)
        if not _ok:
            raise RuntimeError(f"{_why or _gate.R_PUBLIC}: '{_sid}' is not a public broadcast "
                               f"(set it with society.public open=yes).")
        try:
            since_ts = float(since or 0)
        except (TypeError, ValueError):
            since_ts = 0.0
        try:
            lim = max(1, min(int(limit or 100), 500))
        except (TypeError, ValueError):
            lim = 100
        rows = []
        try:
            members = list(self.cortex.get_collection_members(self._broadcast_set(gid, name)) or [])
        except Exception:
            members = []
        for mk in members:
            mm = self.cortex.get_meta(mk) or {}
            if mm.get("concept") != "broadcast_msg":
                continue
            ct = float(mm.get("created_at", 0) or 0)
            if ct <= since_ts:
                continue
            rows.append({"text": self.cortex.get_chunk(mk) or "",
                         "cast_name": mm.get("cast_name", ""), "from_cast": mm.get("from_cast", ""),
                         "provider": mm.get("provider", ""), "model": mm.get("model", ""),
                         "ai": bool(mm.get("ai")), "ai_notice": mm.get("ai_notice", ""),
                         "created_at": ct, "reply_to": mm.get("reply_to", ""),
                         "mode": mm.get("mode", ""), "source": mm.get("source", ""),
                         "topic": mm.get("topic", ""), "kind": mm.get("kind", ""),
                         "category": mm.get("category", ""),
                         "turn": int(mm.get("turn", 0) or 0)})
        rows.sort(key=lambda r: r["created_at"])
        rows = rows[-lim:]
        notices = sorted({r["ai_notice"] for r in rows if r["ai_notice"]})
        cursor = rows[-1]["created_at"] if rows else since_ts
        n_llm = sum(1 for r in rows if r["ai"])
        provenance = {"llm": n_llm, "scripted": len(rows) - n_llm, "total": len(rows),
                      "llm_pct": round(100.0 * n_llm / len(rows)) if rows else 0,
                      "models": sorted({r.get("model", "") for r in rows
                                        if r["ai"] and r.get("model")})}
        # DISPLAY FIELDS, read best-effort from the society itself. They used to come from the
        # stamped `station:show:*` registry — the register this ruling deletes. A caller that
        # cannot resolve the society gets "": a missing label, never a refusal, because the
        # decision was taken above and a read must not re-take it.
        topic = kind = category = ""
        for r in reversed(rows):                       # the newest row that carries a label wins
            topic = topic or str(r.get("topic") or "")
            kind = kind or str(r.get("kind") or "")
            category = category or str(r.get("category") or "")
            if topic and kind and category:
                break
        if not (topic or kind or category):
            try:                                        # a member asking: read the society itself
                ge = self._group_engine(gid)
                _m = self._society_meta(ge, self._society_key(ge, gid, name)) or {}
                topic, kind = _m.get("topic", ""), _m.get("kind", "")
                category = _m.get("category", "")
            except Exception:
                pass
        return {"sid": _sid, "society_id": _sid, "topic": topic, "kind": kind or "chat",
                "category": category,
                "count": len(rows), "messages": rows, "cursor": cursor,
                "now": max((r.get("turn", 0) for r in rows), default=0),
                "attribution": notices, "provenance": provenance,
                "disclosure": self._DISCLOSURE_BANNER}

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
        host = next((l.get("dst") for l in ge.core.get_adjacent_links(key, "responsible:host")), "")
        return {"society_id": self._sid(gid, name), "key": key, "name": m.get("name", name),
                "kind": m.get("kind", "chat"), "topic": m.get("topic", ""),
                "category": m.get("category", ""), "daily_budget": m.get("daily_budget", 0),
                "segments": m.get("segments", []), "host": host,
                "created_by": m.get("created_by", ""), "world": world,
                "decider": decider, "decider_name": dname,
                "open_guest": self._is_open_guest(ge, gid, key),
                "public": self._public_fact(gid, name), "exists": True}

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
                name: str = "", space: str = "") -> Dict[str, Any]:
        """Register one of your avatars into a space's roster (so others can see who is present).

        RESOLVES the cast, it does not ask the say gate about it — joining is what PUTS a cast on
        the roster, and the roster is what makes it one of the space's declared roles. Asking step
        4 first is the admission chicken-and-egg: the answer can only be yes after the act. Who may
        join is decided at the dispatcher, where `society.join` is a `record`."""
        # `space=` is the spelling every other society op takes (`say`, `feed`, `info`, `public`,
        # …), and `join` was the one that did not — so `society.join space=jam` silently joined
        # `main` and the say into `jam` was then refused for a cast nobody had put on its roster.
        # That asymmetry was harmless while `say` auto-registered; it is not any more.
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        cast_id, cast_name = self._resolve_cast(cast)
        ge.add_to_set(self._roster_set(gid, name), cast_id)
        return {"status": "joined", "society_id": self._sid(gid, name),
                "cast_id": cast_id, "cast_name": cast_name}

    def op_say(self, text: str = "", cast: str = "", society: str = "", group: str = "",
               name: str = "", reply: str = "", disclose: Any = False, space: str = "",
               agent: str = "", provider: str = "", model: str = "",
               mode: str = "", source: str = "", turn: Any = 0) -> Dict[str, Any]:
        """Speak into a space AS an owned avatar. Flat timeline with optional `reply=<key>`
        threading. Pseudonymous by default (the human is hidden); disclose=true stamps the member.
        Auto-registers the avatar in the roster on first utterance.

        `agent`/`provider`/`model` mark an AI-generated utterance (the guest gateway stamps them):
        they drive the AI disclosure + licence attribution shown when the space is broadcast
        publicly (society.broadcast) — required by the model providers' terms.

        `mode`/`source` are the OBSERVABILITY (anti-ヤラセ) provenance: `mode` says HOW the line was
        produced — `script` (read from a 台本 verbatim), `quip` (a canned template line), `adlib` /
        `react` (generated by an external LLM) — and `source` names the atom it was derived from (e.g.
        the 台本 alias). They let a viewer tell, per line, what an external LLM actually authored vs
        what was scripted — the whole point of an LLM-participation experiment."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        cast_id, cast_name = self._say_cast(gid, name, cast)
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
        if str(mode or "").strip():
            meta["mode"] = mode.strip()
        if str(source or "").strip():
            meta["source"] = source.strip()
        # `turn` = the chronon sequence this utterance belongs to (the broadcast station groups an
        # anchor+skeptic pair under one chronon = one turn of Akasha Time). Both utterances of a turn
        # carry the same `turn`, so a reader reconstructs the dialogue turns and their order — this is
        # what lets the page play by turn and hold at the live head instead of looping stale content.
        try:
            _t = int(turn)
        except (TypeError, ValueError):
            _t = 0
        if _t > 0:
            meta["turn"] = _t
        key = ge.put_atom(msg, meta, author=cast_id)
        ge.add_to_set(self._feed_set(gid, name), key)
        ge.add_to_set(self._roster_set(gid, name), cast_id)   # auto-join
        return {"status": "said", "key": key, "society_id": sid, "cast_id": cast_id,
                "cast_name": cast_name, "reply_to": meta.get("reply_to", "")}

    def op_air(self, program: str = "", role: str = "", source: str = "", last: str = "",
               provider: str = "", model: str = "", turn: str = "", bench: str = "") -> Dict[str, Any]:
        """[society.air] ONE turn of a programme — forwarded to whichever op IMPLEMENTS it.

        This holds no logic and opens no write path of its own. The turn is produced and recorded by
        the application op whose manifest entry declares `"implements": "society.air"` — the
        programme's recorder, which speaks through `society.say`, the one feed write. The forward
        exists so a programme's turn can be spelled in society terms (and stand as a workflow step)
        without a second implementation drifting from the first.

        It used to dispatch `station.air.turn` BY NAME: the platform naming an application method
        (group 4, 4.12(c)). Now the platform names only the POINT; the application registers the
        method that fills it. With no implementer the step fails, and says which declaration is
        missing — a turn that silently did nothing would be recorded as a run that succeeded."""
        _k = _ACTIVE_KERNEL_FN()
        _impl = _api.implementer(_k, "society.air")
        if not _impl:
            raise RuntimeError("society.air: no op declares `\"implements\": \"society.air\"` on "
                               "this cell — the application registers its programme recorder in "
                               "its manifest")
        r = _k.dispatch(
            {"jsonrpc": "2.0", "method": _impl,
             "params": {"client_id": self._client(),
                        "data": {"program": program, "role": role, "name": bench, "source": source,
                                 "last": last, "provider": provider, "model": model, "turn": turn}},
             "id": "soc-air"}, _TRUST_INTERNAL)
        if isinstance(r, dict) and r.get("error"):
            raise RuntimeError(str((r["error"] or {}).get("message") or r["error"]))
        return (r or {}).get("result") or {}

    def op_feed(self, society: str = "", group: str = "", name: str = "",
                limit: Any = 20, thread: str = "", space: str = "", since: Any = 0) -> Dict[str, Any]:
        """Read the space's timeline, resolved to {cast_name, from_cast, text, created_at,
        reply_to}, oldest→newest. `thread=<key>` filters to that message and its direct replies.
        `since=<epoch>` returns only messages strictly AFTER that time (incremental polling — used by
        the broadcaster relay); absent = the current tail."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        try:
            lim = max(1, min(int(limit), 200))
        except (TypeError, ValueError):
            lim = 20
        try:
            since_ts = float(since or 0)
        except (TypeError, ValueError):
            since_ts = 0.0
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
                          "model": m.get("model", ""), "mode": m.get("mode", ""),
                          "source": m.get("source", ""), "turn": m.get("turn", 0),
                          "msg_type": mtype,
                          "step": m.get("step", ""), "proposal": m.get("proposal", ""),
                          "outcome": m.get("outcome", "")})
        items.sort(key=lambda x: x.get("created_at", 0))
        if since_ts:
            items = [m for m in items if float(m.get("created_at", 0) or 0) > since_ts]
        if thread:
            items = [m for m in items if m["key"] == thread or m.get("reply_to") == thread]
        items = items[-lim:]
        return {"society_id": self._sid(gid, name), "count": len(items), "messages": items}

    def op_roster(self, society: str = "", group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        # G2.2 — the AGENT atoms are the reliable roster source in the group engine: each carries
        # cast (id) + cast_name + the controlling client, whereas a persona lives in its owner's
        # private cortex (unreadable here). Build cast_id → {name} from them.
        agent_by_cast: Dict[str, Dict[str, str]] = {}
        for akey in ge.core.get_collection_members(self._agents_set(gid, name)):
            am = self._society_meta(ge, akey)
            if am.get("concept") == "agent" and am.get("cast"):
                agent_by_cast[am["cast"]] = {"name": am.get("cast_name", "")}
        # role per cast: moderator/observer/broadcaster from the society's responsible:* links →
        # each points at an agent atom whose meta.cast is the cast id; else participant.
        role_by_castid: Dict[str, str] = {}
        if society_key:
            for rel, role in (("responsible:chairman", "moderator"),
                              ("responsible:scribe", "observer"),
                              ("responsible:broadcaster", "broadcaster")):
                for l in ge.core.get_adjacent_links(society_key, rel):
                    am = self._society_meta(ge, l.get("dst"))
                    c = am.get("cast")
                    if c:
                        role_by_castid[c] = role
        # display names: prefer what the feed recorded (cast_name on each utterance), then the
        # agent atom's cast_name, then a published persona in the group engine.
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
            nm = name_map.get(cid) or agent_by_cast.get(cid, {}).get("name", "")
            ident = ""
            if not nm:
                row = ge.core.get_chunk_raw(cid)
                if row:
                    try:
                        mm = json.loads(row.get("meta") or "{}")
                    except Exception:
                        mm = {}
                    nm, ident = mm.get("name", ""), mm.get("identity", "")
            role = role_by_castid.get(cid, "participant")
            casts.append({"cast_id": cid, "name": nm, "identity": ident, "role": role})
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
            # bind to the caller when the cast is one of the caller's own — BOOKKEEPING, not a
            # permission, so it resolves without asking the gate a question about an admission
            # that has not happened yet.
            try:
                own_cid, _ = self._resolve_cast(cast)
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

    # ── G2 — society-on-world ops ──────────────────────────────────────────────────
    def op_connect(self, bench: str = "", society: str = "", group: str = "", name: str = "",
                   space: str = "") -> Dict[str, Any]:
        """[society.connect] Connect this society to a research bench (society:connected society→bench)
        and record society.connected on the world axis. Moderator gate (admin or chairman)."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        self._gate_admin_or_chairman(ge, society_key, "connect a bench")
        bkey = self._bench_key(ge, bench)
        if not bkey:
            raise RuntimeError(f"bench 'wb:{_uslug(bench)}' does not exist in this group — bench.new it first.")
        ge.put_link(society_key, bkey, "society:connected", author=self._client())
        self._register_bench_conn(gid, name, society_key, bkey, bench)       # public-bench grant bridge
        # Persist the bench name on the society too (op_run reads it first) — a public bench's nucleus
        # key is not alias-resolvable from the group engine, so the link-walk alone leaves it invisible.
        sm = self._society_meta(ge, society_key)
        sm["bench_name"] = bench
        self._write_society_meta(ge, society_key, sm)
        wname = self._world_name(self._society_world(ge, society_key) or "default")
        self._world_record(kind="society.connected", ref=self._sid(gid, name),
                                    note=f"{name}→wb:{_uslug(bench)}", world=wname)
        return {"status": "connected", "society_id": self._sid(gid, name), "bench": f"wb:{_uslug(bench)}"}

    def op_sever(self, bench: str = "", society: str = "", group: str = "", name: str = "",
                 space: str = "") -> Dict[str, Any]:
        """[society.sever] Sever a society↔bench connection (records society.severed on the axis).
        Moderator gate."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist.")
        self._gate_admin_or_chairman(ge, society_key, "sever a bench")
        bkey = self._bench_key(ge, bench)
        if bkey:
            ge.core.remove_link_raw(society_key, bkey, "society:connected")
        self._unregister_bench_conn(gid, name, bench)                        # drop the reverse-index
        wname = self._world_name(self._society_world(ge, society_key) or "default")
        self._world_record(kind="society.severed", ref=self._sid(gid, name),
                                    note=f"{name}✕wb:{_uslug(bench)}", world=wname)
        return {"status": "severed", "society_id": self._sid(gid, name), "bench": f"wb:{_uslug(bench)}"}

    def op_moderator(self, agent: str = "", cast: str = "", client: str = "", society: str = "",
                     group: str = "", name: str = "", space: str = "", mode: str = "",
                     policy: str = "") -> Dict[str, Any]:
        """[society.moderator] Appoint the moderator (an ALIAS of society.chairman — admin-only, exactly
        one) AND/OR set the auto-execution MODE (G2.7). With `cast=`/`agent=` it appoints the chairman.
        With `mode=manual|auto [policy=]` it arms/disarms autonomous execution:

        - `mode=auto` ARMS, and arming checks no precondition (the ruling, 2026-09-22). It does not
          ask whether a moderator or a scribe is admitted: an admission is an assignment line now,
          provisioning performs it as admin, and asking again here was a second gate refusing what
          the first admits. The governance casts are DATA provisioning creates from the
          declaration; a missing one is a provisioning failure at the moment it happens
          (`[bench] provision failed … reason=governance:<name>`), never a refusal here.

          The only thing still refused is an auto policy with an empty `workflows` list, which is
          not a precondition but the policy's own content: arming with nothing permitted to run
          would name no runs at all. Where a moderator AGENT exists its controlling client becomes
          `system.moderator` while auto (the driver drives it under the declared policy) and
          reverts on `mode=manual`; where none does, arming simply carries no agent to rebind. The
          mode + policy are stored on the society meta and joined to `set:society:auto` for the
          driver; the change is recorded `society.moderator.mode` on the world axis. WHO may arm is
          the gate's answer (`society.moderator` is a `provision`)."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist — create it first.")
        appointed = None
        if str(cast or "").strip() or str(agent or "").strip():
            appointed = self.op_chairman(agent=agent, cast=cast, client=client, society=society,
                                         group=group, name=name, space=space)
        m = (mode or "").strip().lower()
        if not m:
            return appointed or {"status": "no_change", "society_id": self._sid(gid, name)}
        # WHO MAY ARM is the gate's answer, not a role test here (`society.moderator` is a
        # `provision`). The `_is_admin()` line that stood here was a second gate on a call site
        # that has moved.
        if m not in ("manual", "auto"):
            raise ValueError("society.moderator mode must be 'manual' or 'auto'.")
        smeta = self._society_meta(ge, society_key)
        mod_key = self._moderator_agent_key(ge, society_key)
        if m == "auto":
            # THE ADMISSION PRECONDITIONS ARE GONE — "needs a moderator and an observer (scribe)
            # admitted" and "needs a moderator (chairman) appointed first".
            #
            # They are the same shape as the cast-ownership check: they ask about an ADMISSION, and an
            # admission is an assignment line now (ruling §2 — `chairman`, `scribe`,
            # `broadcaster`, `decider`, `responsible`, `admit` all collapse into the table).
            # Provisioning performs it as admin, so these refused exactly what the gate admits:
            # a second gate in a call site that has moved, which stage 2's rule forbids.
            #
            # Nothing about WHO RUNS is lost. The driver runs as the workload's declared client
            # (§1) and asks `gate(client, run, key)`; the record's keeper is the recorder, which
            # writes `admitted` on every effect. A chairman was one way of writing a line, and
            # the line is what the gate reads.
            pol = _validate_auto_policy(policy)
            if not pol["workflows"]:
                return {"status": "refused", "society_id": self._sid(gid, name),
                        "reason": "auto policy needs a non-empty workflows list (the only runs allowed)"}
            smeta["mode"] = "auto"
            smeta["policy"] = pol
            smeta["driver_client"] = "system.moderator"
            smeta.pop("mode_by", None)          # A35 — arming is provisioning-/driver-owned, not an operator manual
            smeta.pop("mode_reason", None)
            smeta.pop("mode_at", None)
            # A moderator agent is no longer REQUIRED to arm; where one exists its binding is
            # still remembered so `mode=manual` can restore it, and where none does the arming
            # simply carries no agent to rebind.
            if mod_key:
                am = self._society_meta(ge, mod_key)
                smeta["moderator_human_client"] = am.get("client", "")
                self._set_agent_client(ge, mod_key, "system.moderator")
            self._write_society_meta(ge, society_key, smeta)
            self._auto_index_add(gid, name)
        else:  # manual
            smeta["mode"] = "manual"
            smeta["mode_by"] = "operator"        # A35 — a human's manual is preserved across re-provision
            if mod_key and smeta.get("moderator_human_client") is not None:
                self._set_agent_client(ge, mod_key, smeta.get("moderator_human_client", ""))
            smeta.pop("driver_client", None)
            self._write_society_meta(ge, society_key, smeta)
            self._auto_index_rm(gid, name)
        wname = self._world_name(self._society_world(ge, society_key) or "default")
        self._world_record(kind="society.moderator.mode", ref=self._sid(gid, name),
                                    note=f"{name}→mode={m}", world=wname)
        return {"status": "mode_set", "society_id": self._sid(gid, name), "mode": m,
                "policy": smeta.get("policy") if m == "auto" else None,
                "chairman": (appointed or {}).get("agent")}

    # ── G2.7 auto-execution helpers ────────────────────────────────────────────────
    def _u(self):
        """A UniversalConcept bound to this session — writes the nucleus auto-run index."""
        u = getattr(self, "_u_cache", None)
        if u is None:
            from lib.akasha.concepts._universal import UniversalConcept
            u = self._u_cache = UniversalConcept(self.session)
        return u

    def _write_society_meta(self, ge, society_key: str, smeta: Dict[str, Any]) -> None:
        row = ge.core.get_chunk_raw(society_key) or {}
        ge.core.put_chunk_raw(society_key, row.get("content") or "[ Society ]",
                              json.dumps(smeta, ensure_ascii=False), row.get("author") or self._client(),
                              "verified", time.time())
        ge.core.put_chunk_access(society_key, [ge.scope])

    def _has_scribe(self, ge, society_key: str) -> bool:
        return bool(ge.core.get_adjacent_links(society_key, "responsible:scribe"))

    def _moderator_agent_key(self, ge, society_key: str) -> Optional[str]:
        for l in ge.core.get_adjacent_links(society_key, "responsible:chairman"):
            return l.get("dst")
        return None

    def _set_agent_client(self, ge, agent_key: str, client: str) -> None:
        am = self._society_meta(ge, agent_key)
        am["client"] = client
        row = ge.core.get_chunk_raw(agent_key) or {}
        ge.core.put_chunk_raw(agent_key, row.get("content") or "[ Agent ]",
                              json.dumps(am, ensure_ascii=False), row.get("author") or self._client(),
                              "verified", time.time())
        ge.core.put_chunk_access(agent_key, [ge.scope])

    @staticmethod
    def _auto_ptr_alias(gid: str, name: str) -> str:
        return f"society:auto:{gid}:{name}"

    def _auto_index_add(self, gid: str, name: str) -> None:
        """Add a nucleus pointer atom {gid, name, sid} to set:society:auto so the writer-side driver
        can enumerate auto-mode societies across group engines (their society atoms are group-local)."""
        u = self._u()
        alias = self._auto_ptr_alias(gid, name)
        u._space = ""   # nucleus
        u._mk(alias, f"[{alias}] auto-mode society {self._sid(gid, name)}",
              {"concept": "society_auto", "gid": gid, "name": name, "sid": self._sid(gid, name)})
        u._add_to_set(_AUTO_INDEX_SET, u._key(alias))

    def _auto_index_rm(self, gid: str, name: str) -> None:
        u = self._u()
        u._space = ""
        key = u._key(self._auto_ptr_alias(gid, name))
        if key:
            u._remove_from_set(_AUTO_INDEX_SET, key)

    def op_run(self, workflow: str = "", bench: str = "", branch: str = "", society: str = "",
               group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """[society.run] Enqueue ONE run of a policy workflow under the auto moderator's policy (admin or
        this society's moderator). The workflow name MUST be in the policy's `workflows` list — a run of
        anything else is refused and recorded. A run = `wf.advance bench=<b> as=job` over the branch.
        Useful for scripts and tests (`trigger: manual`); the driver uses the same path on its tick."""
        gid, name = self._resolve(group, name, society, space)
        ge = self._group_engine(gid)
        society_key = self._society_key(ge, gid, name)
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, name)}' does not exist.")
        client = self._client()
        # The GATE decided this at the RPC boundary (`society.run` is action `run`, and a run
        # needs declared ∩ armed ∩ source_ready ∩ headroom). The admin-or-moderator test that
        # stood here was a SECOND gate: it refused the workload's own declared client, which is
        # precisely who the driver runs as since §1, and stage 2's rule forbids a window in
        # which the two can disagree.
        smeta = self._society_meta(ge, society_key)
        pol = smeta.get("policy") or {}
        allowed = list(pol.get("workflows") or [])
        sweeps = list(pol.get("sweeps") or [])
        wf = (workflow or "").strip()
        if not wf:
            raise ValueError("society.run requires workflow=")
        b = bench or smeta.get("bench_name") or self._bench_name_for(ge, society_key)
        if not b:
            raise ValueError("society.run needs bench= (no bench connected to this society)")
        # P0-a slice 2 — admit a workflow that is a BRANCH of an admitted sweep (pol.sweeps): the sweep's
        # `wf.branch` stamped `wf:sweep:<b>:<lineage>` with the sweep name, so a lineage whose marker
        # names an admitted sweep runs even though it is not a static `workflows` entry.
        admitted = (not allowed) or (wf in allowed)
        if not admitted and sweeps:
            admitted = self._is_admitted_sweep_branch(b, sweeps, wf)
        if allowed and not admitted:
            # B1 §A3 — the run was refused (workflow not admitted, not a sweep branch): mint an
            # `admission_refused` deviation through the one deviation writer, so the fan records the
            # refusal as a fact (guest-readable Set), not only a returned reason.
            try:
                from lib.akasha.concepts.workflow import WorkflowConcept
                _bare = b[3:] if str(b).startswith("wb:") else b
                WorkflowConcept(self.session)._mint_deviation(
                    _bare, gid, wf, 0, "admission_refused",
                    {"allowed": allowed, "sweeps": sweeps}, {"workflow": wf}, exec_id=wf)
            except Exception:
                pass
            return {"status": "refused", "society_id": self._sid(gid, name), "workflow": wf,
                    "reason": f"workflow '{wf}' is not in the society's policy "
                              f"(allowed: {allowed} sweeps: {sweeps})"}
        # The policy workflow NAME selects the workflow branch (wf.load names each block's branch by
        # its file, e.g. plants_b3); an explicit branch= overrides. Default "main" for a single-branch
        # bench (back-compat with the autorun/provision evals whose one workflow is "main").
        br = (branch or wf or "main")
        r = self._run_bench_workflow(b, gid, br, driver="auto")
        return {"status": "queued", "society_id": self._sid(gid, name), "workflow": wf,
                "bench": b, "branch": br, **r}

    def _is_admitted_sweep_branch(self, bench: str, sweeps: list, wf: str) -> bool:
        """P0-a slice 2 — True if `wf` is the lineage branch of a branch materialised under one of the
        admitted `sweeps`. The sweep's `wf.branch` stamped `wf:sweep:<bench>:<lineage>` with the sweep
        name; O(1) marker read (no Set scan)."""
        try:
            u = self._u()
            marker = u._meta("wf:sweep:%s:%s" % (_uslug(bench), _uslug(wf))) or {}
            return marker.get("sweep") in set(sweeps)
        except Exception:
            return False

    def _bench_name_for(self, ge, society_key: str) -> str:
        """The bench name a society is connected to (first society:connected → wb:<name>).

        A28 — a PUBLIC bench (ruling D: `bench.new` with no group=) lives in the NUCLEUS, so its key is
        a nucleus key that the GROUP engine cannot alias-resolve (`ge.get_aliases_by_key` returns
        nothing). Resolve each connected target through the universal resolver too (local + nucleus),
        so society.run finds a public bench, not only a closed one. This works for a society created
        BEFORE `bench_name` was stored on the meta (the box's existing plants-vision society)."""
        u = self._u()
        for l in ge.core.get_adjacent_links(society_key, "society:connected"):
            dst = l.get("dst")
            aliases = list(ge.get_aliases_by_key(dst) or [])
            nuc_alias = u._alias(dst)          # nucleus-aware; returns the key itself if no alias
            if nuc_alias and nuc_alias not in aliases:
                aliases.append(nuc_alias)
            for a in aliases:
                if a and a.startswith("wb:"):
                    return a[len("wb:"):]
        return ""

    def _run_bench_workflow(self, bench: str, gid: str, branch: str, driver: str = "auto") -> Dict[str, Any]:
        """Enqueue `wf.advance bench=<bench> branch=<branch> as=job` through the WorkflowConcept, so
        each entry step passes the bench's grant table + tees an observation. The moderator's own
        operator:* grants gate the steps — the policy narrows WHAT runs, never bypasses the grants."""
        try:
            from lib.akasha.concepts.workflow import WorkflowConcept
            wfc = WorkflowConcept(self.session)
            # A policy run executes the workflow AFRESH each time (rewind to 0, then advance the whole
            # branch as one JCL job) — a scheduled/daily run re-runs the script, it does not drain it.
            # Bind to the bench's engine BEFORE the head lookup (a closed bench's workflow head lives in
            # the group engine, invisible to the default nucleus/local read).
            wfc._bind(wfc._bench_gid(bench))
            if wfc._key(wfc._wf_head(bench)):
                # E2-1 (F4) — the driver's reset-before-rerun is NOT a thought experiment; by=driver
                # records it under the execution coordinate so the 'Thought experiments' view stays clean.
                wfc.op_rewind(bench=bench, pos=0, branch=branch, by="driver")
            return wfc.op_advance(bench=bench, n=10 ** 6, branch=branch,
                                  **{"as": "job", "driver": driver, "by": "driver"})
        except Exception as exc:
            logger.warning("[society.run] workflow advance failed for %s: %s", bench, exc)
            return {"status": "error", "error": str(exc)}

    # ── G3.7 auto-run driver support (read from the kernel daemon) ──────────────────
    def list_auto_societies(self) -> List[Dict[str, str]]:
        """The (gid, name) of every auto-mode society, from the nucleus index the driver scans."""
        u = self._u(); u._space = ""
        out = []
        for k in u._members(_AUTO_INDEX_SET):
            m = u._meta(u._alias(k)) if u._alias(k) else {}
            if m.get("concept") == "society_auto" and m.get("gid") and m.get("name"):
                out.append({"gid": m["gid"], "name": m["name"]})
        return out

    def read_autorun(self, gid: str, name: str) -> Dict[str, Any]:
        """The society's mode / policy / autorun STATE (last_run, runs_today, breaker, run_once) — the
        driver's read. Returns mode='' when the society is gone."""
        ge = self._group_engine(gid)
        sk = self._society_key(ge, gid, name)
        if not sk:
            return {"mode": "", "policy": {}, "state": {}}
        sm = self._society_meta(ge, sk)
        return {"mode": sm.get("mode", "manual"), "policy": sm.get("policy") or {},
                "state": sm.get("autorun") or {}, "bench": self._bench_name_for(ge, sk),
                "mode_by": sm.get("mode_by")}      # A35 — 'breaker' | 'operator' | None (provisioning-owned)

    def read_provisioned(self, gid: str, name: str):
        """A26 — the provisioning MARKER on the society: {sha, mode, policy} that provisioning last
        applied, or None if this society was never provisioned by the framework (a pre-A26 society, or a
        hand-made one). The re-provisioner compares the society's CURRENT mode/policy against this
        snapshot to tell an OPERATOR edit (drifted) apart from provisioning's own last write (unchanged),
        so a config change re-applies without clobbering an operator's edit."""
        ge = self._group_engine(gid)
        sk = self._society_key(ge, gid, name)
        if not sk:
            return None
        return (self._society_meta(ge, sk) or {}).get("provisioned")

    def write_provisioned(self, gid: str, name: str, marker: Dict[str, Any]) -> None:
        ge = self._group_engine(gid)
        sk = self._society_key(ge, gid, name)
        if not sk:
            return
        sm = self._society_meta(ge, sk)
        sm["provisioned"] = marker
        self._write_society_meta(ge, sk, sm)

    def write_autorun_state(self, gid: str, name: str, state: Dict[str, Any]) -> None:
        ge = self._group_engine(gid)
        sk = self._society_key(ge, gid, name)
        if not sk:
            return
        sm = self._society_meta(ge, sk)
        sm["autorun"] = state
        self._write_society_meta(ge, sk, sm)

    def force_manual(self, gid: str, name: str, reason: str = "breaker", by: str = "") -> None:
        """The driver's breaker: flip a runaway society back to manual itself, record it on the axis,
        and drop it from the auto index. A35 — stamp `mode_by` (+ reason, wall) so the
        re-provisioner can tell this SYSTEM safety trip apart from a human's `mode=manual`: on a new
        config sha / new build the breaker trip is re-armed, but an operator's manual is preserved."""
        ge = self._group_engine(gid)
        sk = self._society_key(ge, gid, name)
        if not sk:
            return
        sm = self._society_meta(ge, sk)
        sm["mode"] = "manual"
        # `by` is WHO disarmed it, and it is not always the breaker: provisioning retires a
        # workload whose declaration this build no longer carries, and recording that as a breaker
        # trip would claim a failure that never happened — and would let the A35 re-arm bring it
        # back on the next build. Defaults to the breaker, which is what every earlier caller meant.
        sm["mode_by"] = str(by or "breaker")
        sm["mode_reason"] = str(reason)
        sm["mode_at"] = round(time.time(), 3)
        mod_key = self._moderator_agent_key(ge, sk)
        if mod_key and sm.get("moderator_human_client") is not None:
            self._set_agent_client(ge, mod_key, sm.get("moderator_human_client", ""))
        sm.pop("driver_client", None)
        self._write_society_meta(ge, sk, sm)
        self._auto_index_rm(gid, name)
        wname = self._world_name(self._society_world(ge, sk) or "default")
        self._world_record(kind="society.moderator.mode", ref=self._sid(gid, name),
                                    note=f"{name}→mode=manual ({reason})", world=wname)

    def op_role(self, cast: str = "", role: str = "", client: str = "", society: str = "",
                group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """[society.role] A thin front over the existing ops for the five world-society roles:
        moderator=chairman, participant=admit, observer=responsible:scribe,
        broadcaster=responsible:broadcaster, audience=public. Gates are the underlying ops'."""
        r = (role or "").strip().lower()
        if r == "moderator":
            return self.op_chairman(cast=cast, client=client, society=society, group=group,
                                    name=name, space=space)
        if r == "participant":
            return self.op_admit(cast=cast, client=client, society=society, group=group,
                                 name=name, space=space)
        if r == "observer":
            return self.op_responsible(kind="scribe", cast=cast, society=society, group=group,
                                       name=name, space=space)
        if r == "broadcaster":
            return self.op_responsible(kind="broadcaster", cast=cast, society=society, group=group,
                                       name=name, space=space)
        if r == "audience":
            return self.op_public(open="yes", society=society, group=group, name=name, space=space)
        raise ValueError("role must be one of moderator|participant|observer|broadcaster|audience")

    def _society_world(self, ge, society_key: str) -> str:
        """The world a society sits in (from its sys:in_world link), or ''."""
        for l in ge.core.get_adjacent_links(society_key, "sys:in_world"):
            return l.get("dst") or ""
        return ""

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
        cast_id, cast_name = self._say_cast(gid, name, cast)
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
        cast_id, cast_name = self._say_cast(gid, name, cast)
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
                cid, cname = self._resolve_cast(cast)   # RESOLUTION, never the say decision
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
    # ── G2 — society on the world (commons) ────────────────────────────────────────
    def _world(self):
        """The world's AXIS bound to this session — the society-on-world records (society.formed /
        society.connected / society.moderator.mode) go through it (nucleus, world-level). It is the
        platform's minimal world container (group 4, 4.14), not the application's world model, so
        a platform model no longer depends on an application one."""
        w = getattr(self, "_world_cache", None)
        if w is None:
            from lib.akasha.concepts.world_axis import axis as _axis
            w = self._world_cache = _axis(self.session)
        return w

    def _world_record(self, **kw) -> None:
        """Record one society event on the world axis, if this cell carries a world concept.

        The six call sites used to chain onto `self._world()`, which imported the concept and would
        have raised on a cell without it. The concept is reached by prefix now (step 2 §5) and can
        legitimately answer None, so the degradation is written HERE once rather than guessed at six
        places — and it is a WARNING, because an axis record that silently did not happen is a gap
        in the history nobody would look for."""
        w = self._world()
        if w is None:
            logger.warning("[society] skipped reason=no_world_concept kind=%s ref=%s",
                           kw.get("kind"), kw.get("ref"))
            return
        try:
            w.op_env_record(**kw)
        except Exception as exc:                       # noqa: BLE001 — reported, never silent
            logger.warning("[society] skipped reason=world_record_failed kind=%s detail=%s",
                           kw.get("kind"), exc)

    @staticmethod
    def _world_name(world: str) -> str:
        """The commons clock name from a world= arg: 'world:default' or 'default' → 'default';
        'world:<slug>' → '<slug>'."""
        w = str(world or "default").strip()
        return w[len("world:"):] if w.startswith("world:") else (w or "default")

    def _bench_key(self, ge, bench: str):
        """The bench atom key — a CLOSED bench lives in this group engine; a PUBLIC bench (ruling D:
        `bench.new` with no group=) lives in the nucleus, so fall back to the nucleus by alias."""
        alias = bench if str(bench).startswith("wb:") else f"wb:{_uslug(bench)}"
        try:
            k = ge.resolve_alias(alias)
        except Exception:
            k = None
        if not k:                                    # a public bench in the shared nucleus
            k = self._u()._key(alias)
        return k

    def _bench_public(self, bench_key: str) -> bool:
        """A bench is PUBLIC when it lives in the nucleus (no group). Read its meta from the nucleus."""
        m = self._u()._meta(bench_key) if bench_key else {}
        return bool(m) and not m.get("group")

    @staticmethod
    def _bench_conn_index(bench_key_or_name: str) -> str:
        return f"set:bench:{_uslug(bench_key_or_name)}:societies"

    def _register_bench_conn(self, gid: str, name: str, society_key: str, bench_key: str,
                             bench_ref: str) -> None:
        """For a PUBLIC bench, record the society↔bench connection in a NUCLEUS reverse-index so the
        bench's grant check (which runs from the nucleus side) can find its governing group society.
        A closed bench needs no index — the society + bench share the group engine. Bench name slug is
        taken from the bench alias (`wb:<slug>`)."""
        if not self._bench_public(bench_key):
            return
        bslug = _uslug(bench_ref[len("wb:"):]) if str(bench_ref).startswith("wb:") else _uslug(bench_ref)
        u = self._u(); u._space = ""
        palias = f"bench:conn:{bslug}:{gid}:{name}"
        pkey = u._mk(palias, f"[{palias}] {self._sid(gid, name)} → wb:{bslug}",
                     {"concept": "bench_conn", "society_key": society_key, "gid": gid,
                      "sid": self._sid(gid, name), "bench": f"wb:{bslug}"})
        u._add_to_set(self._bench_conn_index(bslug), pkey)

    def _unregister_bench_conn(self, gid: str, name: str, bench_ref: str) -> None:
        bslug = _uslug(bench_ref[len("wb:"):]) if str(bench_ref).startswith("wb:") else _uslug(bench_ref)
        u = self._u(); u._space = ""
        pkey = u._key(f"bench:conn:{bslug}:{gid}:{name}")
        if pkey:
            u._remove_from_set(self._bench_conn_index(bslug), pkey)

    def _link_world(self, ge, society_key: str, world: str) -> str:
        """Resolve a world (id or title) and link society→world via sys:in_world."""
        world = (world or "").strip()
        if not world:
            return ""
        world_id = world
        # G2 — a bare commons name ('default') or 'world:<name>' resolves to the commons world atom.
        if not self.cortex.get_meta(world):
            commons = world if world.startswith("world:") else f"world:{world}"
            if self.cortex.get_meta(commons) or self.cortex.resolve_alias(commons):
                ge.put_link(society_key, commons, "sys:in_world", author=self._client())
                return commons
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
