"""
Station bench (seeds-14) — the broadcast station on the Workbench. KIND=station.

A studio becomes a PUBLIC bench `wb:<gid>` (nucleus, guest-readable) whose aired broadcast TURNS are
recorded as observations through the one recorder: each `station.air.record` tees an observation, mints
the bench coordinate `cronon:wb:<gid>:c<n>`, and an act `{declared: the ネタ/script, judged: aired|standby}`
— the anti-やらせ evidence trail (the exact provider/model on the record) carried as first-class bench
coordinates. The publish families (air / relay / post) are effectful.

This is ADDITIVE: the station's existing feed / mirror (`broadcast:*`) / chronon timeline / GC / GUI / X
machinery is unchanged; this concept only records a PARALLEL observation of each turn on the bench clock
and never re-writes the mirror. Spec: docs/for-llm/station-workbench-port.md.
"""
import hashlib
import json
import os
import re
import time
import logging
from lib.akasha.api import gate as _gate
from typing import Any, Dict, Optional, Tuple

from lib.akasha.api.concepts import slug as _uslug
from lib.akasha.api.concepts import WorkbenchConcept
import lib.akasha.api as _api
from lib.akasha.api.concepts import active_kernel as _ACTIVE_KERNEL_FN

logger = logging.getLogger("Harmonia.Concept.BenchStation")

# Programme-state vocabulary (`app/ontology/station/programme_state.ak`, nsdef:station). A value the code
# compares against is vocabulary: these are the ids, defined once in the pack and used here — never a
# free string, so a refusal can never reach a surface as prose nobody defined.
STATE_WARMING_UP = "station:state:warming_up"
STATE_ON_AIR = "station:state:on_air"
STATE_REBROADCAST = "station:state:rebroadcast"
STATE_STANDING_BY = "station:state:standing_by"
REASON_FRESH = "station:reason:fresh"
REASON_LLM_POOL = "station:reason:llm_pool"
REASON_BUDGET_CALLS = "station:reason:budget_calls"
REASON_BUDGET_TOKENS = "station:reason:budget_tokens"
REASON_PROVIDER_429 = "station:reason:provider_429"
REASON_NO_TEXT = "station:reason:no_text"
# A turn the FEED would not take. It USED to answer `not_provisioned`, on the reasoning that a
# missing society or an unadmitted cast is a missing runtime precondition and so is the same thing.
# It is not, and the 09-22 boot showed why: `not_provisioned` is also what the DRIVER says when a
# bench has no workflow, so one id named two failures and a reader could not tell which had
# happened. They share a cure (a boot, never a retry) and nothing else — one is decided before a
# programme runs, the other after its line exists. Two failures, two ids.
REASON_NOT_SAID = "station:reason:not_said"
# The space has not consented to leave the building. None of the other ten means this: it is not a
# missing grant a boot would write (`not_provisioned`), not a ceiling and not a wait on a source —
# it is a person deciding, and it is cured by `society.public open=yes` and nothing else.
REASON_NO_CONSENT = "station:reason:no_consent"
REASON_WAITING_SOURCE = "station:reason:waiting_source"
REASON_NOT_DECLARED = "station:reason:not_declared"
REASON_NOT_PROVISIONED = "station:reason:not_provisioned"
# The two that close the last reason-less exits (2026-09-26 — the 09-25 incident: ~160 paid airings
# that aired nothing, every run record `reason=''`). `no_current` is never a root cause: it points
# upstream, at the turn that opened the airing. `turn_error` is the op RAISING, which used to return
# nothing at all — so a paid turn could fail with no trace but the bill.
REASON_NO_CURRENT = "station:reason:no_current"
REASON_TURN_ERROR = "station:reason:turn_error"
# D13: a turn whose source resolved and whose prompt cannot carry it. Never generated, never charged.
REASON_PROMPT_WITHOUT_SOURCE = "station:reason:prompt_without_source"
# D14: every item of the episode has aired (grounded) and the declaration says `on_exhausted:
# stand_by`. No programme declares it today — the station rebroadcasts (`wrap`) around the clock —
# but the option stays, with its reason, for a programme that must never repeat. No model call.
REASON_SOURCE_EXHAUSTED = "station:reason:source_exhausted"

# What a programme does once every item has aired (D14). Declared, never inferred from the domain.
ON_EXHAUSTED_WRAP = "wrap"            # read on: the least recently aired item comes round again
ON_EXHAUSTED_STAND_BY = "stand_by"    # stop, and say so, until the notebook gets new items

# One deprecation line per process for the old model env name — news, not a per-turn refrain.

# X's own limits, which are not ours to choose. 280 is the hard cap; 270 leaves room for the
# disclosure tail to survive a body that ends on a wide character.
_X_MAX = 270


class BenchStationConcept(WorkbenchConcept):
    """`bench.*` — a station bench (kind=station). Aired turns recorded on the workbench recorder."""

    CONCEPT_PREFIX = "station"
    CONCEPT_LABEL = "Station bench — aired broadcast turns recorded on the workbench (observed)"

    # The bench's kind is the EFFECT this workload class has on the world, not a domain noun. A
    # `publish` bench is one whose ops leave the world; "station" was a name the platform had a
    # table for, and a table of names is the branch this whole port exists to remove.
    KIND = "publish"
    _FAMILIES = ("air", "relay", "post")

    CONCEPT_METHODS: Dict[str, Any] = {
        "air.record": {"op": "op_air", "action": "annotate",
                       "desc": "Record one aired broadcast turn as an observation (provider/model/source/"
                               "turn provenance + act declared=source/judged=aired): station.air.record "
                               "name= source= [provider= model= turn= aired= chronon=]"},
        "air.ls":     {"op": "op_air_ls", "action": "read",
                       "desc": "The bench's aired-turn observations, ordered by wall clock, newest last; `limit=N` is the newest N. `program=<key>` narrows to ONE workload (four share the station bench) and `since=<epoch>` to rows after that moment — one run's rows: station.air.ls name= [program=] [since=] [limit=]"},
        "publish":    {"op": "op_publish", "action": "publish", "effectful": True,
                       "desc": "Publish a programme's latest sealed, unposted turn to an external "
                               "channel: station.publish channel=x program=<key> [dry=yes]"},
        "air.turn":   {"op": "op_air_turn", "action": "say", "effectful": True,
                       "desc": "Produce and air ONE turn of a programme IN THE DAEMON (the model call "
                               "goes through the shared gate): station.air.turn program=<key> role=<role> "
                               "[source=<passage atom>] [provider= model=]"},
    }

    def _aired_set(self, name: str) -> str:
        return "%s:aired" % self._bench_alias(name)

    def op_air(self, name: str, source: str = "", provider: str = "", model: str = "", turn: str = "",
               aired: str = "1", chronon: str = "", cast: str = "", reason: str = "",
               program: str = "", grounded: str = "", atom: str = "",
               turn_no: str = "") -> Dict[str, Any]:
        """Record ONE aired broadcast turn as a bench observation, through `_perform` (→ a bench
        coordinate + an act). The exact provider/model is on the record (anti-やらせ evidence). A turn that
        did not air (standby) is recorded too — `aired=0`, `judged=standby` — so the standby history is
        legible. Public bench (nucleus). Best-effort at the caller (the daemon never blocks on it).

        `program` is the WORKLOAD KEY (`<bench>/<slug>`), and it is on the record because four
        workloads now share one bench. Before seed A each studio had a bench of its own, so "every
        observation on this bench" and "this programme's observations" were the same set and a room
        could read one for the other. They are not the same set any more: without the key on the
        record, `station.air.ls name=studio_ai` hands a room four programmes' turns and it has no way
        to tell which are its own. The key is the one identifier that cannot drift — the driver, the
        gate's ledger and the guide row all account under it."""
        self._ensure_public_bench(name, self.KIND, by="station.air_turn")
        gid = self._bench_gid(name); self._bind(gid)
        balias = self._bench_alias(name)
        try:
            _aired = int(aired)
        except (TypeError, ValueError):
            _aired = 1
        _ai = bool(provider) and str(provider).strip().lower() not in ("", "akasha", "script")
        # D14: `grounded` = the source's TEXT was in the message the model was sent. Only such rows
        # consume an episode item; a row without it names a source the line may never have read.
        _grounded = str(grounded or "").strip().lower() in ("1", "true", "yes")

        def _fn():
            n = len(self._members(self._aired_set(name))) + 1
            alias = "%s:aired:%d" % (balias, n)
            at = self._akasha_now()
            key = self._mk(alias, "[%s] aired turn %d — %s" % (alias, n, source or "news"),
                           {"concept": "station_aired", "family": "air", "bench": balias,
                            "source": source or None, "provider": provider or None,
                            "model": model or None, "turn": turn or None, "chronon": chronon or None,
                            "aired": _aired, "ai": _ai, "cronon": at, "n": n, "purpose": "broadcast",
                            "program": program or None,
                            "grounded": True if (_grounded and _aired) else None,
                            # D17: the ATOM the turn worked from. `source` is the listener-facing
                            # anchor ("The Preface · p.[i]"), and two passages may share one — so the
                            # cursor keys by the atom, which is unique, and never by the anchor.
                            "atom": atom or None,
                            # D18: the number of the TURN this beat belongs to, stored so the next beat
                            # continues it and the next turn is one higher — never re-derived from a window.
                            "turn_no": int(turn_no) if str(turn_no or "").strip().isdigit() else None,
                            # WALL-CLOCK, beside the Akasha-Time `cronon`. `cronon` orders runs
                            # against each other; a cadence ("every 1800s", "daily at 12:00Z") and
                            # a freshness guard are measured in seconds, and they read this. It was
                            # the guide row's `last_post_at` until that row was deleted, and an
                            # observation with no clock cannot answer "when did this last air".
                            "wall": time.time(),
                            # A standby carries WHY on the record itself (a station:reason:* id). The
                            # turn is the only thing that knows; without it the driver that reports the
                            # run to the programme guide has to ASSUME an outcome, and it assumed the
                            # happy one — a run whose every turn stood by was published as an airing.
                            "reason": (reason or None) if not _aired else None,
                            "observer": provider or "akasha", "observer_version": model or "script"})
            k = self._key(alias)
            self._add_to_set(self._aired_set(name), k)
            if source:
                self._add_to_set("set:%s:by:%s" % (balias, _uslug(source)), k)   # provenance (by source)
            self._add_to_set(self._scope_set(name), k)
            return {"aired_obs": alias, "turn": turn, "source": source, "aired": _aired, "ai": _ai, "program": program or "",
                    "reason": (reason or "") if not _aired else ""}

        out = self._perform(name, "air", "record",
                            {"source": source, "provider": provider, "model": model, "turn": turn,
                             "cast": cast, "purpose": "broadcast",
                             "act": {"declared": (source or "news"),
                                     "judged": ("aired" if _aired > 0 else "standby")}}, _fn)
        if isinstance(out, dict) and out.get("aired_obs"):
            self._act(name, gid, out.get("observed_at_seq"), "air")
        return out

    def op_air_ls(self, name: str, limit: str = "200", program: str = "",
                  since: str = "") -> Dict[str, Any]:
        """The bench's aired-turn observations, NEWEST LAST — and that is now true.

        It said "newest last" and returned STORE order: the rows came out in whatever order the
        aired Set yields its members, and `limit` sliced the tail of that. So `limit=40` was forty
        arbitrary turns, and every reader that took the last row as "the latest" — the rooms, the
        Source Viewer, and until 09-26 the platform's own run outcome — was reading a row chosen by
        hash order. On the platform side that made a run's reason come back `''` eleven times in
        twelve (P7 / D10). The rows are now ordered by their wall clock `at` (the observation's
        counter breaks a tie) BEFORE `limit` applies, so `limit=N` means the newest N.

        `since=<epoch>` keeps only rows strictly AFTER that moment — one run's rows, when a caller
        passes the run's start — so a reader that needs one run no longer pulls the whole history.

        `program=<key>` narrows them to ONE workload. Four workloads share the station bench since
        seed A, so an unfiltered read is four programmes' turns interleaved — which is the right
        answer for the bench and the wrong one for a room, whose whole subject is one programme.
        Both filters apply DURING the walk, before ordering and `limit`, so a programme's last 40
        turns are forty of ITS turns rather than forty of the bench's.

        The walk itself is still over every member of the aired Set: membership has no order to
        read from, so finding the newest N means looking at each `at`. Only the newest N are ever
        HELD (a bounded heap), never the whole history — O(members) reads, O(limit) memory.

        A record written before the key was stamped carries no `program`; those rows answer no
        filter rather than being attributed to whoever asks. `count` is what this read returned and
        `bench_count` is the bench's total, so a caller can see it was narrowed."""
        gid = self._bench_gid(name); self._bind(gid)
        balias = self._bench_alias(name)
        try:
            lim = max(1, int(limit))
        except (TypeError, ValueError):
            lim = 200
        want = (program or "").strip()
        try:
            after = float(since) if str(since or "").strip() else 0.0
        except (TypeError, ValueError):
            after = 0.0
        import heapq
        heap, total, seq = [], 0, 0
        for k in self._members(self._aired_set(name)):
            m = self._meta(k)
            total += 1
            if want and str(m.get("program") or "") != want:
                continue
            at = float(m.get("wall") or m.get("created_at") or 0.0)
            if after and at <= after:
                continue
            alias = self._alias(k)
            # the observation's own counter (`…:aired:<n>`) breaks a tie on `at`, then walk order
            tail = str(alias).rsplit(":", 1)[-1]
            n = int(tail) if tail.isdigit() else 0
            seq += 1
            row = {"obs": alias, "program": m.get("program"),
                         "source": m.get("source"), "provider": m.get("provider"),
                         "model": m.get("model"), "turn": m.get("turn"), "aired": m.get("aired"),
                         "ai": m.get("ai"), "cronon": m.get("cronon"), "reason": m.get("reason"),
                         "grounded": bool(m.get("grounded")),
                         "atom": m.get("atom"), "turn_no": m.get("turn_no"),
                         # WALL-CLOCK, beside the Akasha-Time `cronon`. The two answer different
                         # questions and a reader needs both: `cronon` orders the runs against each
                         # other, `at` is what a cadence ("every 1800s", "daily at 12:00Z") and a
                         # freshness guard are measured in. They came from the guide row's
                         # `last_post_at` until that row was deleted, and a record without a clock
                         # cannot answer "when did this last air" at all.
                         "at": at,
                         "by": m.get("cast") or m.get("observer") or ""}
            key = (at, n, seq)
            if len(heap) < lim:
                heapq.heappush(heap, (key, row))
            elif key > heap[0][0]:
                heapq.heapreplace(heap, (key, row))
        rows = [r for _, r in sorted(heap, key=lambda x: x[0])]     # oldest first, newest LAST
        return {"bench": balias, "program": want or None, "since": after or None,
                "aired": rows, "count": len(rows), "bench_count": total}

    # ── publishing a programme's turn to an EXTERNAL channel ────────────────────────
    # This was twenty `x_*` functions and an op in the platform, driven by its own timer and gated
    # by the presence of a file on disk. It is a workload: one declaration (`news_show_x.json`)
    # naming the channel and the programme it republishes, one template line, and the driver's own
    # cadence. Nothing about X is special — the channel is a pin, and the only platform seam is the
    # HTTP client that holds the credentials.

    @staticmethod
    def _x_weight(s: str) -> int:
        """X's weighted character count, which is not `len()`. A URL counts as its fixed t.co
        length whatever it really is, and a wide character (emoji, CJK) counts two. A body dense in
        wide characters passes a `len() <= n` check and then blows the 280 cap — and what gets
        dropped is the tail, which is the AI disclosure."""
        s2 = re.sub(r"https?://\S+", "x" * 23, s or "")
        return sum(2 if ord(ch) > 0x1100 else 1 for ch in s2)

    @classmethod
    def _x_clip(cls, s: str, n: int) -> str:
        """Clip to a WEIGHTED budget, reserving one for the ellipsis."""
        s = (s or "").strip()
        w = (lambda ch: 2 if ord(ch) > 0x1100 else 1)
        if sum(w(ch) for ch in s) <= n:
            return s
        budget, acc, cut = max(0, n - 1), 0, 0
        for i, ch in enumerate(s):
            if acc + w(ch) > budget:
                break
            acc += w(ch)
            cut = i + 1
        return s[:cut].rstrip() + "\u2026"

    def _x_format(self, beats: list, link: str) -> list:
        """One turn's beats → a reply chain of at most three tweets, each inside the cap, with the
        AI disclosure baked in. The first opens with the notice and the hashtag; the last carries
        the notice and a link back to the room. The disclosure is not decoration — it is what makes
        posting a model's words in public honest, and it is budgeted for BEFORE the body is clipped
        so that a long body can never push it out."""
        texts = [(b.get("text") or "").strip() for b in beats if (b.get("text") or "").strip()]
        if not texts:
            return []
        model = next((b.get("model") for b in beats if b.get("model")), "")
        notice = next((b.get("ai_notice") for b in beats if b.get("ai_notice")),
                      ("AI-generated \u00b7 " + model if model else "AI-generated"))
        head = "\n\n\U0001f916 %s \u00b7 #AkashaNews" % notice
        tail = "\n\n\U0001f916 %s\n%s" % (notice, link) if link else "\n\n\U0001f916 %s" % notice
        hw, tw, last, out = self._x_weight(head), self._x_weight(tail), len(texts) - 1, []
        for i, t in enumerate(texts):
            if i == 0:
                out.append(self._x_clip(t, _X_MAX - hw) + head)
            elif i == last:
                out.append(self._x_clip(t, _X_MAX - tw) + tail)
            else:
                out.append(self._x_clip(t, _X_MAX - self._x_weight(" \U0001f916")) + " \U0001f916")
        return out

    def _posted_count(self, bench: str, channel: str, program: str) -> int:
        """How many turns of `program` this bench has POSTED to `channel` — from the posted records,
        so a failed post (never recorded) does not count."""
        pref = "%s:%s:%s:" % (self._bench_alias(bench), _uslug(channel), _uslug(program))
        return sum(1 for k in (self._members(self._posted_set(bench)) or [])
                   if str(self._alias(k) or "").startswith(pref))

    def _sponsor_line(self, xprog: Dict[str, Any], beats: list, turn: int, program: str,
                      posted: int = 0) -> str:
        """The channel's SPONSOR line for this turn, or "" — a closing reply of its own, never mixed
        into the news or its AI disclosure.

        Declared by the CHANNEL workload (`pins.sponsor_set`), so the rooms never carry it. An item
        may name its own line (`<item>:sponsor`, authored beside the item in the ネタ帖) and that
        wins; otherwise one line of the Set is picked — varied across turns, but the SAME line for
        the same turn, so a retried post does not change its wording. The lines are authored copy
        and carry their own `#ad`: a paid link is labelled as one."""
        pins = (xprog or {}).get("pins") or {}
        set_name = str(pins.get("sponsor_set") or "").strip()
        if not set_name:
            return ""
        # Not on every post (the owner, 09-28: "every time reads as a nag") — on every Nth
        # post, counted from the posted RECORD: the Nth, 2Nth, … post carries it. A failed post is
        # not recorded, so its retry is judged the same way. `sponsor_every: 1` = every post.
        try:
            every = max(1, int(pins.get("sponsor_every") or 1))
        except (TypeError, ValueError):
            every = 1
        if (posted + 1) % every:
            return ""
        src = next((str(b.get("source") or "") for b in beats if b.get("source")), "")
        if src:
            own = self._body("%s:sponsor" % src)
            if own:
                return own
        lines = sorted(filter(None, (self._body(self._alias(k) or k)
                                     for k in (self._members(set_name) or []))))
        if not lines:
            return ""
        pick = int(hashlib.sha256(("%s#%s" % (program, turn)).encode("utf-8")).hexdigest(), 16)
        return lines[pick % len(lines)]

    def _latest_turn(self, gid: str, space: str):
        """The newest sealed turn's beats, in the order they were spoken, from the SOCIETY'S OWN
        record. Returns (turn, [beat, ...]) or (0, []).

        It read the public mirror through `society.broadcast.live`, which asked nobody anything —
        and now that the public read is ONE gated surface (`feed.read`, ruling 2026-09-23 §3), that
        route answers "not a public broadcast" for exactly the space this op is about to refuse for
        `no_consent`, three gates further down. Two refusals for one fact, and the earlier one wins,
        so the operator's preview and the op's own reason both disappear behind it.

        The publisher is not the public: it reads its own society's feed as itself, under its own
        read grant, and the CONSENT question is asked once, by this op, where it belongs. The
        notice is baked with the same function the mirror bakes with, so the thread carries the
        identical licence attribution the room shows rather than a second rendering of it."""
        from lib.akasha.api.concepts import model as _model, model_class as _model_class
        live = _model(self.session, "society").op_feed(
            society="%s/%s" % (gid, space), limit=90) or {}
        for _m in live.get("messages") or []:
            _m["ai_notice"] = _model_class("society").attribution_notice(
                _m.get("provider", ""), _m.get("model", ""), _m.get("mode", ""))
        by_turn: Dict[int, list] = {}
        for m in live.get("messages") or []:
            by_turn.setdefault(int(m.get("turn", 0) or 0), []).append(m)
        by_turn.pop(0, None)                       # only genuine (turn > 0) segments
        if not by_turn:
            return 0, []
        top = max(by_turn)
        order = {"adlib": 0, "read": 0, "react": 1, "question": 1, "wrap": 2, "explain": 2}
        return top, sorted(by_turn[top], key=lambda m: order.get(m.get("mode", ""), 9))

    def _posted_set(self, name: str) -> str:
        return "%s:posted" % self._bench_alias(name)

    def _already_posted(self, name: str, channel: str, program: str, turn: int) -> bool:
        return bool(self._key("%s:%s:%s:%d" % (self._bench_alias(name), _uslug(channel),
                                               _uslug(program), turn)))

    def op_publish(self, channel: str = "x", program: str = "", dry: str = "",
                   name: str = "", workload: str = "") -> Dict[str, Any]:
        """Publish a programme's latest sealed, unposted turn — and name the reason when it does
        not. The same rule as `op_air_turn`, for the same incident: a publish that RAISED returned
        nothing, so its run record read an empty reason. An exception is now a `turn_error`
        stand-by with its traceback in the log.

        `workload` is the key of the workload that RAN this publish (`studio_ai/news_show_x`), as
        distinct from `program`, the programme it republishes. The outcome — posted or stood by,
        with its reason — is recorded on the bench under THAT key, because that is the key the
        platform reads a run's outcome by. Written under the programme's key (or not at all) the
        X channel's every run read `reason=''` while its log said `no_consent`."""
        chan = (channel or "x").strip().lower()
        wl = (workload or "").strip()
        bench = name
        if wl and not bench:
            bench = str((self._workload(wl) or {}).get("bench") or "").replace("wb:", "")
        try:
            return self._publish(chan, program, dry, name, wl, bench)
        except Exception as exc:                  # noqa: BLE001 — every failure must name itself
            return self._pub_standby(program, chan, 0, REASON_TURN_ERROR,
                                     "%s: %s" % (type(exc).__name__, exc), exc_info=True,
                                     workload=wl, bench=bench)

    def _pub_standby(self, program: str, chan: str, turn: int, reason: str, detail: str = "",
                     status: str = "standby", exc_info: bool = False, workload: str = "",
                     bench: str = "") -> Dict[str, Any]:
        """The ONE way a publish stands by: one `[station.publish] standby key=<workload> program=…
        reason=<id> — detail` line, and the vocabulary id in the return.

        With the running `workload` known, the stand-by is also a row on the bench under that key
        (`aired=0`, the reason on it) — the X workload's OWN record, which is where the platform
        looks for the run's reason. It is never written under the republished programme's key: a
        publish that did not post is not an airing of the news show, and the news show's room
        reads only its own key. A dry run is a preview, not a run, and records nothing."""
        loud = reason in (REASON_NOT_SAID, REASON_TURN_ERROR, REASON_NOT_DECLARED,
                          REASON_NOT_PROVISIONED)
        (logger.warning if loud else logger.info)(
            "[station.publish] standby key=%s program=%s channel=%s turn=%s reason=%s — %s",
            workload or program or "-", program or "-", chan, turn, reason, detail or "-",
            exc_info=exc_info)
        if workload and bench:
            self._pub_record(bench, workload, chan, turn, aired=0, reason=reason)
        return {"status": status, "reason": reason, "turn": turn, "program": program,
                "workload": workload, "channel": chan, "detail": detail}

    def _pub_record(self, bench: str, workload: str, chan: str, turn: int, aired: int,
                    reason: str = "") -> None:
        """One row of the running workload's record. Best-effort: the outcome was already decided
        and logged; a record that cannot be written must not turn it into a different one."""
        try:
            self.op_air(name=bench, source="", provider="", model="",
                        turn="%s:%s" % (chan, turn), aired=str(aired), reason=reason,
                        program=workload)
        except Exception:                          # noqa: BLE001
            logger.warning("[station.publish] record failed key=%s channel=%s turn=%s",
                           workload, chan, turn, exc_info=True)

    def _publish(self, chan: str, program: str, dry: str, name: str, workload: str = "",
                 run_bench: str = "") -> Dict[str, Any]:
        """Publish a programme's latest sealed, unposted turn to an external channel.

        `program` is the workload key of the programme being republished — its declaration says
        which society to read and which room to link back to. This workload's own declaration says
        which channel (`pins.channel`) and which programme (`pins.program`), so the op carries no
        knowledge of either.

        Three gates, each naming itself: nothing sealed yet (`waiting_source`), the newest turn
        already posted (`fresh`), and the space has not consented to be shown outside
        (`no_consent`). The last is a person's decision and no boot can supply it.

        `dry=yes` formats and returns the thread without posting — the preview an operator wants
        before consenting, and what the conformance eval rehearses."""
        _dry = str(dry or "").strip().lower() in ("1", "yes", "true")

        def sb(*a, **kw):                          # a dry run is a preview: logged, never recorded
            return self._pub_standby(*a, workload=workload, bench="" if _dry else run_bench, **kw)

        prog = self._workload(program)
        if not prog:
            return sb(program, chan, 0, REASON_NOT_DECLARED,
                      "no workload declares program=%r" % program, status="refused")
        gid, _, space = str(prog.get("society") or "").partition("/")
        bench = name or str(prog.get("bench") or "").replace("wb:", "") or gid
        if not (gid and space):
            return sb(program, chan, 0, REASON_NOT_PROVISIONED,
                      "workload %s names no society to read" % program,
                      status="refused")

        turn, beats = self._latest_turn(gid, space)
        if not beats:
            return sb(program, chan, 0, REASON_WAITING_SOURCE,
                      "nothing sealed on %s/%s yet" % (gid, space))
        # The link back is the SOURCE programme's declared room — not a constant, so a room that
        # moves takes its own links with it.
        room = str(prog.get("room") or "/station/%s/" % str(prog.get("workflow") or "").replace("_", "-"))
        site = (os.environ.get("AKASHA_X_LINK", "").strip()
                or "https://akashicarchives.net" + room)
        tweets = self._x_format(beats, site)
        # the channel's sponsor line, if the RUNNING workload declares one — its own last reply
        _sp = self._sponsor_line(self._workload(workload) if workload else {}, beats, turn, program,
                                 posted=self._posted_count(bench, chan, program))
        if _sp:
            tweets.append(self._x_clip(_sp, _X_MAX))
        if str(dry or "").strip().lower() in ("1", "yes", "true"):
            return {"status": "dry_run", "turn": turn, "tweets": tweets, "count": len(tweets),
                    "program": program, "channel": chan}
        if self._already_posted(bench, chan, program, turn):
            return sb(program, chan, turn, REASON_FRESH,
                      "turn %s is already posted to %s" % (turn, chan))

        # `station.publish` declares the action `publish`, and step 4 of `publish` IS "target ∈
        # public" — so this asks the gate with the target the dispatcher could not know, instead of
        # re-reading the consent Set under a second rule that could answer differently.
        from lib.akasha.api import gate as _gate
        from lib.akasha.api.concepts import model as _model, model_class as _model_class
        skey = _model(self.session, "society").society_key(gid, space)
        if not skey:
            return sb(program, chan, turn, REASON_NOT_PROVISIONED,
                      "no society %s/%s visible to %s" % (gid, space, self._client()))
        ok, why = _gate.gate(self._client(), _gate.PUBLISH, "%s/%s" % (gid, space))
        if not ok:
            # The gate's OWN term decides the id. Only `public` is the space's consent; every other
            # refusal (`out_of_scope` above all — the client holds no line on that place) is a grant
            # a declaration + boot supply. Until 2026-09-28 every refusal read `no_consent`, which
            # sent the operator to flip a consent that was already given while the real cause —
            # the X workload running as a client with no reach on the news show — went unnamed.
            if why == getattr(_gate, "R_PUBLIC", "public"):
                return sb(program, chan, turn, REASON_NO_CONSENT,
                          "%s/%s has not consented to be shown outside" % (gid, space))
            return sb(program, chan, turn, REASON_NOT_PROVISIONED,
                      "the gate refused %s publish on %s/%s: %s"
                      % (self._client(), gid, space, why))

        post = _api.hook(_ACTIVE_KERNEL_FN(), "channel.%s.post_thread" % chan)
        if not post:
            return sb(program, chan, turn, REASON_NOT_SAID,
                      "no client hook for channel %s" % chan)
        # The hook's OWN signature — `post_thread_hook(tweets, dry=False)`. A hook takes what it
        # needs and no more (`llm_quota(provider)` takes no kernel either), and passing one here
        # made every REAL post die `-32602 post_thread_hook() takes from 1 to 2 positional
        # arguments but 3 were given`. It was invisible because the consent gate above returns
        # first on a space nobody opened, and the eval's stub had copied the wrong signature — so
        # the one call that mattered was the one never exercised.
        res = post(tweets, False) or {}
        ids = res.get("ids") or []
        if not ids:
            # The slot is NOT marked posted: a failure that recorded itself as a success would
            # lose the turn for good, and the next run is the retry.
            return sb(program, chan, turn, REASON_NOT_SAID,
                      "the %s client posted nothing — %s"
                      % (chan, res.get("reason") or "post_failed"))

        # Posted-state is a RECORD on the bench, not a file beside the process. A cursor in a file
        # is invisible to `lens`, to `as_of` and to retention, and it does not survive a cell that
        # is moved; this is an atom, and it says what was posted, where, and when.
        alias = "%s:%s:%s:%d" % (self._bench_alias(bench), _uslug(chan), _uslug(program), turn)
        self._mk(alias, "[%s] posted turn %d to %s" % (alias, turn, chan),
                 {"concept": "station_posted", "family": "post", "bench": self._bench_alias(bench),
                  "channel": chan, "program": program, "turn": turn, "ids": ids,
                  "count": len(ids), "cronon": self._akasha_now(), "purpose": "broadcast"})
        self._add_to_set(self._posted_set(bench), self._key(alias))
        logger.info("[station.publish] posted key=%s program=%s channel=%s turn=%s count=%d",
                    workload or program, program, chan, turn, len(ids))
        if workload and run_bench:
            self._pub_record(run_bench, workload, chan, turn, aired=1)
        return {"status": "posted", "turn": turn, "channel": chan, "program": program,
                "workload": workload, "ids": ids, "count": len(ids)}

    # ── one turn of a programme, produced INSIDE the daemon ─────────────────────────
    # Why this lives here and not in a driver script: `llm_provider`'s meter, rate pacing and 429
    # back-off are process state, and the durable store is installed by the KERNEL. A model call made
    # in a separate driver process is therefore invisible to the day's pool — it is neither counted
    # nor debited against a reservation, so two drivers plus the station could each believe they are
    # under the cap. Producing the turn here puts every call behind the one gate by construction.
    #
    # It adds NO second write path: the utterance goes out through `society.say` (the one feed write)
    # and the record through `op_air` above (the one recorder, via `_perform`). Everything specific to
    # a programme — its roles, their contracts, their prompts, its source — is DATA read from the
    # programme's declaration; this operator knows about none of it.

    def _workload(self, program: str = "", gid: str = "", space: str = "") -> Dict[str, Any]:
        """The WORKLOAD DECLARATION this turn belongs to, from the platform, by key or by society.

        One lookup, through the Application API's hooks — `workload.by_key` and
        `workload.for_society`. The declaration carries everything a turn needs: the society to
        speak in, the role contracts, the prompts, the casts and the episode Set. It is the same
        object the driver read to schedule the run, so the turn and its run cannot disagree about
        which programme they are.

        This used to be a private reader that globbed `app/config/workbench/workloads/*.json` itself.
        Two readers of one directory is two chances to disagree with it, and the private one did:
        a deployed cell has files there that no development tree carries (`auto_exec.json`, whose
        top level is a LIST), and `.get()` on it raised — every turn of every programme failed on
        the seed while every eval in the repo was green. The platform's reader validates the shape
        once; this asks it."""
        kernel = _ACTIVE_KERNEL_FN()
        # A hook is `fn(kernel, …)` — the manifest convention, which is what lets the platform hand
        # a package a handle without the heart importing it. §3 of the order states the logical
        # shape; the kernel is the calling convention around it.
        want = (program or "").strip()
        if want:
            fn = _api.hook(kernel, "workload.by_key")
            return (fn(kernel, want) if fn else None) or {}
        if gid and space:
            fn = _api.hook(kernel, "workload.for_society")
            return (fn(kernel, gid, space) if fn else None) or {}
        return {}

    def _body(self, ident: str) -> str:
        """An atom's content, with the `[alias]` hub header a `def`-written atom carries stripped.
        Read from the NUCLEUS: a passage arrives with the ontology pack at universal scope, so the
        lookup must not be bound to a group space."""
        self._space = ""
        k = self._key(ident)
        if not k:
            return ""
        body = ""
        # `self.cortex` unions local + nucleus; the raw cores are tried after it because a passage
        # that arrived with an ontology pack lives in the NUCLEUS, not in the caller's cortex.
        for get in (lambda: self.cortex.get_chunk(k),
                    lambda: (self.cortex.core.get_chunk_raw(k) or {}).get("content"),
                    lambda: ((self._nuc.core.get_chunk_raw(k) or {}).get("content") if self._nuc else None)):
            try:
                body = (get() or "").strip()
            except Exception:
                body = ""
            if body:
                break
        if body.startswith("[") and "\n" in body:
            body = body.split("\n", 1)[1].strip()
        # An atom defined with NO description still answers with a body — its bare `[alias]` header,
        # or the placeholder the store writes for an empty define (`Conceptual hub: <alias>`).
        # Neither is the atom's text. Returned as-is they reached the model as "today's item", which
        # is D13 again by another road: a turn recorded against a source whose words it never had.
        # So a body that is only this atom's own header or placeholder is NO text.
        alias = self._alias(k) or str(ident or "")
        if body in ("[%s]" % alias, "Conceptual hub: %s" % alias,
                    "[%s]" % ident, "Conceptual hub: %s" % ident):
            return ""
        return body

    # ── the cursor is DERIVED from the record, never stored ─────────────────────────
    # A static workflow step cannot name a passage, so a step says `source=next` (the next passage of
    # the episode that has not aired) or `source=current` (the one the last aired turn worked from).
    # Both are read back out of the bench's own record: the record IS the state, so a crash or a
    # re-run cannot desynchronise a cursor, and there is no second store to keep.

    def _episode(self, prog: Dict[str, Any]) -> list:
        """The episode's entries as [{atom, anchor, text}], read out of the graph (the Set the
        programme declares). Empty when the pack is not loaded on this cell.

        TWO shapes of entry, because two kinds of programme read from two kinds of pack:

        · a JSON body — a transcribed PASSAGE, carrying its own bibliographic anchor (book, section,
          page). The reading room's `shelf_dibdin` pack is this: the anchor is what lets a listener
          go back to the printed page, so it is built from the fields rather than from the atom id.
        · a PLAIN-TEXT body — an ordinary ontology atom's description, which is already a record of
          the thing (`art:movement:baroque`, a species entry). Here the atom's own alias IS the
          anchor: it is stable, it is what `op_air` records as the turn's `source`, and there is no
          page to return to.

        The second shape is what lets a programme read the graph's OWN atoms with no corpus to ship
        — the Set is the episode. It also means the anchor a turn records and the anchor this list
        carries are the same string in both shapes, which is what `_resolve_source` compares."""
        # A workload names its episode in `pins` — `episode_set`, or `item_set` for the news 台本.
        # One spelling; the legacy programme file's `source.episode_set` is gone with the file.
        pins = prog.get("pins") or {}
        set_name = (pins.get("episode_set") or pins.get("item_set") or "").strip()
        if not set_name:
            return []
        self._space = ""
        out = []
        for k in self._members(set_name) or []:
            alias = self._alias(k) or k
            body = (self._body(alias) or "").strip()
            if not body:
                continue
            try:
                doc = json.loads(body)
            except ValueError:
                doc = None
            if isinstance(doc, dict):
                if not doc.get("text"):
                    continue
                a = doc.get("anchor") or {}
                # The passage names its OWN atom (`doc["atom"]`). The store's `alias(k)` is the
                # FIRST alias of the key, and an atom with several aliases answers whichever sorts
                # first — which is how the reading room came to read p.[i], dedication, imprint, title
                # page (09-27): identity and order were the store's accident, not the pack's.
                declared = str(doc.get("atom") or "").strip()
                if declared and self._key(declared) == k:
                    alias = declared
                out.append({"atom": alias, "seq": doc.get("seq"), "_json": True,
                            "anchor": " · ".join(str(x) for x in
                                                 [doc.get("book"), doc.get("section"),
                                                  ("p.%s" % a["page"]) if a.get("page") else None] if x),
                            "text": doc.get("text")})
            else:
                # A plain description. Nothing is parsed out of it and nothing is invented: the
                # text is the record as the pack wrote it, and the alias is the anchor.
                out.append({"atom": alias, "anchor": alias, "text": body})
        out.sort(key=self._episode_order)
        return out

    @staticmethod
    def _episode_order(p: Dict[str, Any]) -> tuple:
        """The PACK's order. A passage that declares `seq` goes by it; otherwise by its declared atom
        name in NATURAL order (`ep1-2` before `ep1-10`), which for a generated pack IS the order of
        its passages file. A plain-text item (the news show's, the gallery's) has no document to
        declare an order: its alias order stands, as it always has."""
        seq, atom = p.get("seq"), str(p.get("atom") or "")
        if p.get("_json"):
            nat = tuple((0, int(t), "") if t.isdigit() else (1, 0, t) for t in re.split(r"(\d+)", atom) if t)
            return (0, seq if isinstance(seq, (int, float)) else float("inf"), nat)
        return (1, 0, atom)

    @staticmethod
    def _aired_only(rows: list, count_unmarked: bool = False) -> list:
        """`[(source, atom, at)]` of the turns that actually AIRED and READ their source, oldest first.

        A standby must NOT count: a turn the model failed to produce has not read its passage, and
        letting it consume one would skip that passage for good.

        Nor may a row that does not carry `grounded` (D14): until the D13 fix the news show's prompts
        never sent the item, so a row naming an item records one nobody read. From the fix on the op
        stamps each aired row `grounded: true`. A programme whose prompts ALWAYS carried the source
        (the reading room, the gallery) declares `unmarked_rows: count`, so its earlier, genuinely
        read rows keep its place in the book; old rows are never rewritten either way.

        `atom` is the atom the turn worked from (D17); a row written before it existed carries only
        its `source` (the anchor), and the caller resolves that when it is unambiguous."""
        out = []
        for r in rows or []:
            if str(r.get("aired")) not in ("1", "True", "true") or not r.get("source"):
                continue
            if r.get("grounded") or count_unmarked:
                out.append((r["source"], r.get("atom") or "", float(r.get("at") or 0.0)))
        return out

    @staticmethod
    def _on_exhausted(prog: Dict[str, Any]) -> str:
        v = str(prog.get("on_exhausted") or "").strip().lower()
        # Absent → WRAP. The station is on air 24 hours with no gap (project owner, 2026-09-27):
        # running out of new items means a rebroadcast, never silence. `stand_by` must be declared.
        return v if v in (ON_EXHAUSTED_WRAP, ON_EXHAUSTED_STAND_BY) else ON_EXHAUSTED_WRAP

    def _pick_source(self, want: str, bench: str, prog: Dict[str, Any],
                     program: str = "") -> Tuple[str, str]:
        """`(atom, reason)` for `source=next|current`, read from THIS programme's record.

        `next` → the first item of the episode with no grounded airing. Once every item has aired,
        the declaration decides (`on_exhausted`): `wrap` takes the LEAST RECENTLY aired item — a
        rebroadcast, so the station stays on air around the clock, and an item added later airs
        first because it has never aired; `stand_by` answers `("", source_exhausted)` and nothing
        is generated. Absent → `wrap` (every programme declares it today). It used to be `eps[0]`
        forever — item 001 on every run, D14.

        `current` → the item the newest grounded turn worked from, so the follow-up roles stay on
        what was just read; `""` when nothing has aired yet.

        The rows are this programme's ONLY (`program=<key>`), all of them: five workloads share the
        bench, and a window over the bench's newest rows let another programme's turns push this
        one's out of sight — "seen" then depended on who else had aired lately."""
        eps = self._episode(prog)
        if not eps:
            return "", ""
        key = program or self._workload_key_of(prog)
        rows = self.op_air_ls(name=bench, program=key, limit=str(10 ** 9)).get("aired") or [] \
            if key else []
        aired = self._aired_only(rows, count_unmarked=str(prog.get("unmarked_rows") or "")
                                 .strip().lower() == "count")
        # The cursor keys by ATOM (D17). Two passages may share an anchor — the Dibdin preface's
        # first two both read "The Preface · p.[i]" — and keyed by anchor, airing one marked both as
        # read, so the other never aired on its own. A row names its atom; a row from before that
        # names only its anchor, and counts only when the anchor picks out exactly one atom (an
        # ambiguous one cannot say which it read, so it consumes none and the shared passages air).
        by_anchor: Dict[str, list] = {}
        for p in eps:
            by_anchor.setdefault(p["anchor"], []).append(p["atom"])
        atoms = {p["atom"] for p in eps}

        def _atom_of(src: str, atom: str, newest_ambiguous_first: bool = False) -> str:
            if atom and atom in atoms:
                return atom
            cands = by_anchor.get(src) or []
            if len(cands) == 1:
                return cands[0]
            return cands[0] if (cands and newest_ambiguous_first) else ""

        if want == "current":
            for src, atom, _at in reversed(aired):
                a = _atom_of(src, atom, newest_ambiguous_first=True)
                if a:
                    return a, ""
            return "", ""
        last: Dict[str, float] = {}
        for src, atom, at in aired:
            a = _atom_of(src, atom)
            if a:
                last[a] = at                      # rows are oldest first, so this keeps the newest
        for p in eps:
            if p["atom"] not in last:
                return p["atom"], ""
        if self._on_exhausted(prog) == ON_EXHAUSTED_WRAP:
            return min(eps, key=lambda p: (last.get(p["atom"], 0.0), self._episode_order(p)))["atom"], ""
        return "", REASON_SOURCE_EXHAUSTED

    @staticmethod
    def _workload_key_of(prog: Dict[str, Any]) -> str:
        b = str(prog.get("bench") or "").replace("wb:", "")
        w = str(prog.get("workflow") or "")
        return "%s/%s" % (b, w) if b and w else ""

    def _resolve_source(self, want: str, bench: str, prog: Dict[str, Any],
                        program: str = "") -> str:
        return self._pick_source(want, bench, prog, program)[0]

    def _feed_last(self, gid: str, space: str) -> str:
        """The previous aired line, read from the space's own feed — the feed IS the state, so nothing
        has to be threaded between workflow steps."""
        from lib.akasha.api.concepts import model as _model, model_class as _model_class
        try:
            msgs = (_model(self.session, "society").op_feed(group=gid, space=space, limit=1)
                    or {}).get("messages") or []
            return (msgs[-1].get("text") or "").strip() if msgs else ""
        except Exception:
            return ""

    def op_air_turn(self, program: str = "", role: str = "", name: str = "", source: str = "",
                    last: str = "", provider: str = "", model: str = "",
                    turn: str = "") -> Dict[str, Any]:
        """Produce and air ONE turn — and whatever happens, return a REASON when it does not air.

        On 09-25 the news show ran ~160 paid airings that aired nothing and every run record read
        `reason=''`. The platform dropped what this op returned (D10, theirs); but this side had
        turns that returned no vocabulary id either — four that returned a sentence and wrote no
        record, and every turn that RAISED, which returned nothing at all. A turn that raised after
        the model call was a paid failure with no trace but the bill.

        So the body runs inside this wrapper, and an exception becomes a `turn_error` stand-by that
        is RECORDED, LOGGED with its traceback, and says whether the model had already been called.
        One exception to the exception: a turn whose line is already ON THE FEED did air, and is
        reported as aired with the failure beside it — recording it as a stand-by would make the
        record and the feed disagree, which is the one outcome that must never happen."""
        trace = {"called": False, "said": "", "bench": ""}
        try:
            return self._air_turn(trace, program, role, name, source, last, provider, model, turn)
        except Exception as exc:                  # noqa: BLE001 — every failure must name itself
            detail = "%s: %s" % (type(exc).__name__, exc)
            if trace["said"]:
                logger.warning("[station] aired but NOT sealed program=%s role=%s said=%s — %s",
                               program or "-", role or "-", trace["said"], detail, exc_info=True)
                return {"status": "aired", "role": role, "program": program,
                        "said": trace["said"], "detail": detail}
            return self._stood_by(program=program, bench=trace["bench"], role=role, turn=turn,
                                  reason=REASON_TURN_ERROR, detail=detail, called=trace["called"],
                                  exc_info=True)

    def _stood_by(self, *, program: str, bench: str, role: str, turn: str, reason: str,
                  detail: str = "", called: bool = False, provider: str = "", model: str = "",
                  source: str = "", status: str = "standby", record: bool = True,
                  exc_info: bool = False) -> Dict[str, Any]:
        """The ONE way a turn stands by. Every exit that does not air comes through here, so every
        one of them does the same three things and none can forget one:

          · logs ONE line — `[station] standby program=… role=… reason=<id> called=yes|no — detail`
            — at the place that decided it (doctrine rule 3). The prefix is the one the 09-18 note
            already documented, so an existing grep keeps working. `called` says whether a model
            call had gone out: a stand-by after a call is the incident's shape, and is a WARNING.
          · RECORDS it on the bench (`aired=0`, the reason on the observation). The record is where
            `workload.status.last` and the run record read from, so a reason written here reaches
            the guide even on a cell where the op's RETURNED reason is dropped on the way (D10).
            A record that fails is itself logged, and never loses the reason from the return.
          · RETURNS the vocabulary id, never a sentence — the sentence goes in `detail`. A reason
            is read through the station vocabulary by every surface; a sentence resolves to nothing
            and reaches the reader as a raw token."""
        loud = called or reason in (REASON_NOT_SAID, REASON_TURN_ERROR,
                                    REASON_NOT_DECLARED, REASON_NOT_PROVISIONED)
        (logger.warning if loud else logger.info)(
            "[station] standby program=%s role=%s reason=%s called=%s — %s",
            program or "-", role or "-", reason, "yes" if called else "no", detail or "-",
            exc_info=exc_info)
        out: Dict[str, Any] = {}
        if record and bench:
            try:
                out = self.op_air(name=bench, source=source or role, provider=provider, model=model,
                                  turn=turn or (role or "").lower(), aired="0", reason=reason,
                                  program=program) or {}
            except Exception as rec_exc:          # noqa: BLE001 — the reason must survive this
                logger.warning("[station] standby NOT recorded program=%s role=%s reason=%s — %s: %s",
                               program or "-", role or "-", reason, type(rec_exc).__name__, rec_exc)
        out.update({"status": status, "reason": reason, "role": role, "text": "",
                    "detail": detail, "called": bool(called)})
        return out

    def _air_turn(self, trace: Dict[str, Any], program: str, role: str, name: str, source: str,
                  last: str, provider: str, model: str, turn: str) -> Dict[str, Any]:
        """Produce and air ONE turn of a programme, in the daemon, under the role's declared contract.

        `program` is the accounting key from the declaration (`<bench>/<studio>`); `role` names one of
        that programme's roles; `source` is the atom being worked from (a passage, a 台本 item) and
        `last` the previous aired line, when the role's prompt asks for them. The model call goes
        through `llm_provider.generate` HERE, so the shared pool sees it.

        A turn the model does not produce is NOT invented: it is recorded `aired=0` (judged=standby)
        and nothing is said. Role scope is the contract in the declaration, never improvised."""
        # The WORKLOAD DECLARATION, and nothing else. One object, from the platform, carrying the
        # society, the roles, the prompts, the casts and the episode — the same object the driver
        # read to schedule this run. There is no second source and therefore no fallback: a cell
        # that has no declaration for this key has no such programme, and saying so is the answer.
        prog = self._workload(program)
        if not prog:
            # No declaration, so no bench to record on: logged and returned, with the id.
            return self._stood_by(program=program, bench="", role=role, turn=turn,
                                  reason=REASON_NOT_DECLARED, status="refused", record=False,
                                  detail="no workload declares program=%r" % program)
        gid, _, space = str(prog.get("society") or "").partition("/")
        bench = name or str(prog.get("bench") or "").replace("wb:", "") or gid
        trace["bench"] = bench
        spec = (prog.get("roles") or {}).get(role) or {}
        if not spec or role.startswith("_"):
            # A ROLE NOBODY DECLARED IS A STANDBY, NOT A BARE REFUSAL — and it is the case that
            # actually protects the budget: a template naming a role the declaration does not
            # carry must cost nothing and must leave a trace. A refusal returned from here was
            # neither: no record, so the guide showed the run as simply not having happened, and
            # whoever had to fix it got the driver's `not_provisioned` instead of the reason.
            #
            # The reason is `not_said`, the same id as a cast the space will not let this caller
            # speak as, because it is the same fact — step 4's `roles` — reached from the
            # declaration's side rather than the roster's. `detail` carries the gate's own term
            # and the cast, which is what names the fix.
            _why = self._cast_unowned(role, gid, space) or \
                "%s: workload %s declares no role %r" % (_gate.R_ROLES, program, role)
            return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                  reason=REASON_NOT_SAID, detail=_why)
        if not (gid and space):
            return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                  reason=REASON_NOT_PROVISIONED, status="refused",
                                  detail="workload %s names no society to speak in" % program)

        # `source=next|current` and `last=feed:last` are resolved HERE, from the record and the feed,
        # so a workflow step can be a fixed line of data (see the cycle the programme declares).
        source = (source or "").strip()
        if source in ("next", "current"):
            _want = source
            source, _why = self._pick_source(source, bench, prog, program)
            if _why == REASON_SOURCE_EXHAUSTED:
                _pins = prog.get("pins") or {}
                return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                      reason=REASON_SOURCE_EXHAUSTED, status="refused",
                                      detail="every item of %s has aired and the programme declares "
                                             "on_exhausted=%s; no model call made — add items to "
                                             "the episode Set to go back on air"
                                             % (_pins.get("episode_set") or _pins.get("item_set")
                                                or "its episode", self._on_exhausted(prog)))
            if not source:
                _pins = prog.get("pins") or {}
                _ep = _pins.get("episode_set") or _pins.get("item_set") or ""
                if not self._episode(prog):
                    return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                          reason=REASON_WAITING_SOURCE, status="refused",
                                          detail="the episode Set %r is empty on this cell — the "
                                                 "work's pack is not loaded" % _ep)
                return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                      reason=REASON_NO_CURRENT, status="refused",
                                      detail="no %s passage to work from: nothing of this "
                                             "programme has aired — read the turn that opened "
                                             "the airing" % _want)
        if (last or "").strip() == "feed:last":
            last = self._feed_last(gid, space)

        # the passage / source atom, and the anchor a listener can return to
        body, anchor = "", (source or "")
        if source:
            body = self._body(source)
            try:
                doc = json.loads(body)
                if isinstance(doc, dict):
                    a = doc.get("anchor") or {}
                    body = doc.get("text") or body
                    anchor = " · ".join(str(x) for x in
                                        [doc.get("book"), doc.get("section"),
                                         ("p.%s" % a["page"]) if a.get("page") else None] if x)
            except ValueError:
                pass

        # ── GROUNDING (D13) — a turn is generated FROM its source, or not at all ────────────────
        # From the port until 2026-09-26 the news show's prompts had no `{source}`: the item was
        # resolved above, never sent, and still written to the row as the turn's source — so the
        # Anchor read out news the model had made up, under a record saying otherwise. A row may
        # name a source only when that source's text was in the message. Both halves are checked
        # BEFORE the model is called, so a turn that cannot be grounded costs nothing.
        _prompt = spec.get("prompt") or "{source}"
        if source and "{source}" not in _prompt:
            return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                  reason=REASON_PROMPT_WITHOUT_SOURCE,
                                  detail="source %s resolved, and role %s's declared prompt has no "
                                         "{source} to carry it; no model call made"
                                         % (source, role))
        if source and not str(body or "").strip():
            return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                  reason=REASON_WAITING_SOURCE,
                                  detail="source %s resolved and carries no text; no model call "
                                         "made" % source)

        system = self._contract(role, spec, prog)
        # 演出 — the item's editorial ANGLE, a companion atom `<item>:angle` in the same pack
        # (direction handed to the caster, never read out). `{angle}` expands to a headed block
        # when the item has one and to NOTHING when it does not, so a prompt carries no empty
        # heading and an item without an angle is simply told straight.
        _angle = self._body("%s:angle" % source) if (source and "{angle}" in _prompt) else ""
        _angle_block = ("\n\nThe angle to take (direction, not a script — ad-lib within it):\n%s"
                        % _angle) if _angle else ""
        user = (_prompt.replace("{source}", body).replace("{last}", last or "")
                .replace("{angle}", _angle_block))

        _gen = _api.hook(_ACTIVE_KERNEL_FN(), "llm_generate")
        _dflt = _api.hook(_ACTIVE_KERNEL_FN(), "llm_default_model")
        # The provider is the CELL's, not this workload's, so it is read where the cell decides it
        # — one hook, one default, one deprecation warning. Spelling the env name here again would
        # be an eighth copy of a default, and the old name is dropped next seed with no fallback
        # left behind it. An explicit `provider=` argument still wins: a rehearsal names its own.
        _prov_fn = _api.hook(_ACTIVE_KERNEL_FN(), "llm_active_provider")
        prov = (provider or "").strip().lower() or (
            _prov_fn(_ACTIVE_KERNEL_FN()) if _prov_fn else "mistral")
        mdl = (model or self._model_env() or (_dflt(prov) if _dflt else "") or "")

        # ── the SAY GATE, BEFORE the model call ─────────────────────────────────────────────────
        # A paid call whose line cannot be spoken is money spent on nothing. At 03:32 on 09-22 the
        # three boot-owed programmes each generated a turn and were refused at the say (`No owned
        # avatar`): the day's spend moved, the feed did not, and the only trace was a standby.
        # The gate is a pure read, so it can be asked FIRST — the SAME function the feed write
        # asks, so there is no second notion of who may speak to drift from the one that decides.
        _cast_wanted = str(spec.get("cast") or role)
        _own_err = self._cast_unowned(_cast_wanted, gid, space)
        if _own_err:
            return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                  reason=REASON_NOT_SAID, provider=prov, model=mdl,
                                  source=anchor or role,
                                  detail="cast %s — %s; no model call made" % (_cast_wanted, _own_err))

        # Marked BEFORE the call: if it raises part-way, the wrapper must still be able to say a
        # call went out, because that is the difference between a free failure and a paid one.
        trace["called"] = bool(_gen)
        text = ((_gen(prov, mdl, system, user) if _gen else "") or "").strip()

        if not text:
            # standing by is a RECORDED state, not a silent gap — and never a fabricated line.
            # THREE refusals, three reasons. `quota().exhausted` is this cell's OWN ceiling, not the
            # shared pool's — reporting it as `llm_pool` sent an operator to the provider when the
            # limit was ours. `quota().limit` names which one, decided once beside the gate.
            _q = _api.hook(_ACTIVE_KERNEL_FN(), "llm_quota")
            _lim = ((_q(prov) if _q else None) or {}).get("limit") or ""
            why = (REASON_PROVIDER_429 if (lambda _f: _f(prov) if _f else 0)(_api.hook(_ACTIVE_KERNEL_FN(), "llm_backoff_seconds"))
                   else REASON_BUDGET_CALLS if _lim == "calls"
                   else REASON_BUDGET_TOKENS if _lim.startswith("tokens")
                   else REASON_NO_TEXT)
            return self._stood_by(program=program, bench=bench, role=role, turn=turn, reason=why,
                                  called=trace["called"], provider=prov, model=mdl,
                                  source=anchor or role,
                                  detail=("no llm_generate hook on this cell" if not _gen
                                          else "provider=%s model=%s answered nothing usable"
                                          % (prov, mdl or "-")))

        turn_no = self._turn_no(bench, program, anchor or role, source)
        said = self._say(gid, space, spec, role, text, prov, mdl, anchor, turn_no)
        if not said.get("key"):
            # The model produced a line and the FEED did not take it — the society is missing, the
            # cast is not admitted, a scope refused the write. The turn did not air, and recording
            # it as `aired=1` is the one outcome that must never happen: the bench record and the
            # room's live feed would then disagree about what was broadcast, and the record is what
            # the guide, the airing panel and the day's count all believe. So it is a standby, with
            # a reason. (This code carried a comment saying a failure here is never swallowed while
            # doing exactly that; a fresh cell provisioned from workload declarations, where the
            # pre-convergence society does not exist, made it visible: `aired`, and an empty feed.)
            return self._stood_by(program=program, bench=bench, role=role, turn=turn,
                                  reason=REASON_NOT_SAID, called=trace["called"], provider=prov,
                                  model=mdl, source=anchor or role,
                                  detail="the line was produced and the feed at %s/%s did not take "
                                         "it — %s" % (gid, space, said.get("error")
                                                      or "no key returned"))
        # From here the line is ON THE FEED. A failure after this point is not a stand-by.
        trace["said"] = said.get("key", "")
        chronon = self._seal(gid, space, anchor or role, said.get("key", ""))
        # `grounded`: this turn's source text WAS in the message (the D13 guard above refuses any
        # turn where it would not be), so the row may consume its item (D14).
        out = self.op_air(name=bench, source=anchor or role, provider=prov, model=mdl,
                          turn=turn or role.lower(), aired="1", cast=said.get("cast_id", ""),
                          program=program, chronon=chronon, grounded="1" if source else "",
                          atom=source or "", turn_no=str(turn_no))
        out.update({"status": "aired", "role": role, "cast": said.get("cast_name") or role,
                    "text": text, "provider": prov, "model": mdl, "program": program,
                    "said": said.get("key", ""), "chronon": chronon, "turn_no": turn_no})
        return out

    @staticmethod
    def _contract(role: str, spec: Dict[str, Any], prog: Dict[str, Any]) -> str:
        """The role's system prompt, built from what the programme DECLARES — a role is scoped, never
        given free conversation. Identical in shape to the off-line driver's, so a turn produced here
        and one produced there are held to the same law."""
        topic = ((prog.get("space") or {}).get("topic") or "").strip()
        lines = ["You are the %s of %s." % (role, topic or "this programme"),
                 spec.get("identity", ""),
                 "Your turn is: %s. You speak ONLY on your turn." % spec.get("turn", "")]
        if spec.get("answer_shape"):
            lines.append("Answer in this order: " + " → ".join(spec["answer_shape"]) + ".")
        if spec.get("may"):
            lines.append("You may: " + "; ".join(spec["may"]) + ".")
        if spec.get("must_not"):
            lines.append("You must NOT: " + "; ".join(spec["must_not"]) + ".")
        if spec.get("allowed_levels"):
            lines.append("Mark any statement that is not in the text itself as interpretation. "
                         "Levels you may use: " + ", ".join(spec["allowed_levels"]) + ".")
        lines.append("Be brief. This is radio, not an essay.")
        return "\n".join(x for x in lines if x)

    def _turn_no(self, bench: str, program: str, source: str, atom: str = "") -> int:
        """Which TURN of this programme this beat belongs to (D18).

        A turn is the run of beats that work from one source: the news show's three beats share one
        item, the reading room's five share one passage. `society.say` stamps the number on the
        utterance, the room's player uses a CHANGE of it as the boundary where the between-turn
        bumper plays, and a channel workload republishes one turn at a time.

        It is CONTINUED, not recounted. The newest aired row of this programme carries its turn
        number: a beat working from the same source as that row is the same turn; a beat on another
        source is the next one. It used to be the position of the source in the programme's last 200
        rows — a sliding window — so as the record outgrew it the number moved between the beats of
        ONE item (68, 67, 66) and the room played a bumper in the middle of the turn, after the
        Anchor and the Commentator and before the close. A rebroadcast (`on_exhausted: wrap`) also
        reused the item's FIRST number, so the numbers ran backwards. The row now stores the number
        (`turn_no`); only a record from before it (no `turn_no`) is counted once, over the FULL
        record, and every row after that continues from it."""
        def _aired(r):
            return str(r.get("aired")) in ("1", "True", "true")

        newest = None
        for r in reversed(self.op_air_ls(name=bench, program=program, limit="40").get("aired") or []):
            if _aired(r):
                newest = r
                break
        try:
            last_no = int(newest.get("turn_no")) if newest else 0
        except (TypeError, ValueError):
            last_no = 0
        if newest and last_no:
            same = (newest.get("atom") == atom) if (atom and newest.get("atom")) \
                else (newest.get("source") == source)
            return last_no if same else last_no + 1
        seen = []                                   # a record from before `turn_no`: count it once
        for r in (self.op_air_ls(name=bench, program=program, limit=str(10 ** 9)).get("aired") or []):
            if _aired(r) and r.get("source") and r.get("source") not in seen:
                seen.append(r.get("source"))
        if source in seen:
            return seen.index(source) + 1
        return len(seen) + 1

    @staticmethod
    def _model_env() -> str:
        """The model this cell speaks with, from the environment.

        `AKASHA_LLM_MODEL` is the name (a declared deployment fact)."""
        return (os.environ.get("AKASHA_LLM_MODEL") or "").strip()

    def _cast_unowned(self, cast: str, gid: str = "", space: str = "") -> str:
        """"" when this speaker may say as this cast, else the gate's reason — asked BEFORE
        anything is paid for, so a turn that cannot be published costs no model call.

        It used to ask whether the caller OWNED the avatar, which is the check
        that burned two days of model calls: provisioning runs as admin, so the casts are not
        the programme's, and ownership answered a question nobody had asked. It asks the gate
        now — the same function the feed write asks, so the probe and the write cannot disagree.

        A probe that cannot run is NOT a refusal: the turn proceeds and the say reports whatever
        it finds. Failing closed on a broken probe would silence a programme over a bug in the
        probe."""
        try:
            from lib.akasha.api.concepts import model as _model, model_class as _model_class
            # THE SAME INPUTS as the write, not just the same function. Asking without
            # `declared_casts` leaves step 4 with nothing to compare, so it returns OK and the
            # probe admits every cast — including one the workload does not declare. The turn then
            # paid for a model call and was refused at the feed, which is the exact cost this
            # probe exists to avoid, and a role nobody declared read as aired.
            _dec = (_model(self.session, "society").declared_casts(gid, space) if gid else None)
            ok, why = _gate.gate(getattr(self.session, "client_id", ""), _gate.SAY,
                                 "%s/%s" % (gid, space) if gid else None, cast=cast,
                                 declared_casts=_dec)
            return "" if ok else "%s: say as '%s'" % (why, cast)
        except Exception as exc:                      # noqa: BLE001 — a broken probe never refuses
            logger.warning("[station] say probe failed for cast=%s (%s) — proceeding", cast, exc)
            return ""

    def _say(self, gid: str, space: str, spec: Dict[str, Any], role: str, text: str,
             provider: str, model: str, source: str, turn_no: int = 0) -> Dict[str, Any]:
        """Put the turn on the public feed through the ONE feed write path (`society.say`), as the
        role's own cast, stamped with the exact provider/model so the broadcast renders the honest
        disclosure. A failure here is reported, never swallowed — an unaired turn must not look aired."""
        from lib.akasha.api.concepts import model as _model, model_class as _model_class
        try:
            return _model(self.session, "society").op_say(
                group=gid, space=space, cast=(spec.get("cast") or role), text=text,
                agent="ai", provider=provider, model=model, mode=(spec.get("turn") or "adlib"),
                source=source, turn=str(turn_no or 0)) or {}
        except Exception as exc:                  # noqa: BLE001 — the caller names the stand-by
            # Returned rather than logged here: the stand-by line the caller writes carries it, so
            # the reason and its cause are on ONE line instead of two a reader has to pair up.
            return {"error": "%s: %s" % (type(exc).__name__, exc)}

    def _seal(self, gid: str, space: str, source: str, member_key: str) -> str:
        """Seal this turn as a PERFECTIVE chronon on the society and advance `society:now`.

        The `chronon:next` chain IS Akasha Time on a programme's society: the room plays by
        traversing it and HOLDS at `society:now` — the live head — when nothing further is sealed.
        That is the front/back sync, and it is structural rather than a wall-clock guess.

        Ported from the platform daemon (`station.py station_seal_turn`), which was the only path
        that sealed. Since the driver took the news show, turns have aired WITHOUT advancing the
        timeline the GUI plays, so the room has had nothing to traverse.

        Two differences from the daemon's version, both deliberate:

        · the daemon sealed one chronon per three-beat turn; the driver's unit is ONE BEAT, because
          one `society.air` step is one turn op. The chain is finer-grained and the player advances
          per line, which is what a room reading a conversation wants;
        · continuity across a restart is read from the society's own `society:now` FRONTIER, never
          from an attribute on the kernel. A process-lifetime variable is not state — a restart
          silently started a second chain from nothing, and the graph is the only thing that knows
          where the timeline had got to.

        Best-effort: a programme that airs is never stopped by its bookkeeping."""
        if not member_key:
            return ""
        try:
            from lib.akasha.api.concepts import model as _model, model_class as _model_class
            if not _model(self.session, "society").society_key(gid, space):
                return ""
            # The public door, `chronon.seal`: it defaults `from` to the single `society:now`
            # frontier, holds the seal gate (every programme client is its society's chairman)
            # and records the scribe. A forked frontier is REFUSED (R4) — which on a linear
            # programme timeline is a real fork worth a log line, not something to extend blindly.
            chrono = _model(self.session, "chronon")
            seq = (chrono.op_list(group=gid, space=space) or {}).get("chronons") or []
            body = "%s · turn %d" % (source or "turn", len(seq) + 1)
            res = chrono.op_seal(group=gid, space=space, label=(source or "turn"),
                                 members=member_key, body=body) or {}
            if not res.get("chronon"):
                logger.warning("[station.seal] refused society=%s/%s source=%s — %s",
                               gid, space, source, res.get("error") or res.get("reason") or res)
            return res.get("chronon") or ""
        except Exception as exc:
            logger.warning("[station.seal] failed society=%s/%s source=%s reason=seal_failed (%s)",
                           gid, space, source, exc)
            return ""

