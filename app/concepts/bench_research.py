"""
Research bench (world-workbench-society spec v1.0, G1.3) — the concrete `bench` concept, kind
`research`. It subclasses the workbench base and adds the operation FAMILIES a research bench exposes:

  source      — reference material from the Source Data Layer (never a copy)
  hypothesis  — claims under test
  evidence    — passages/atoms bound to a hypothesis with a stance + provenance
  proof       — a claim over cited evidence (status follows the hypothesis)
  note        — free notes

Every op runs through the base `_perform(family, op, …)` dispatcher: grant-check (G2.3) → run →
tee ONE observation onto the bench stream (the at_seq is the observation chronon) → return the result
plus {observed_at_seq}. All atoms live in the bench's engine (the society's group engine for a closed
bench), aliased under `wb:<name>:…` and added to `scope:wb:<name>`. There are NO seminar-specific
categories here — those are DATA of an instance (or a later kind), exactly as radu.py v0.1 kept clab
clean.
"""
import logging
import time
from typing import Any, Dict, List

from lib.akasha.api.concepts import slug as _uslug
from lib.akasha.api.concepts import WorkbenchConcept

logger = logging.getLogger("Harmonia.Concept.BenchResearch")

_HYP_STATES = ("open", "supported", "refuted", "withdrawn")
_STANCES = ("supports", "contradicts", "context")

# ── Research Notebook (seeds-14 §2 port, Option B) — a research CHUNK is a NOTE-family entry with
# provenance; a PUBLICATION is a Set + composed_from / published_in links + a presentation macro. The
# chunk vocabulary is the note's `type` facet; the reference fields become typed relations. Spec:
# docs/for-llm/research-workbench-port.md.
CHUNK_TYPES = ("research_setting", "question", "hypothesis", "experiment", "observation", "finding",
               "consideration", "decision", "method_change", "negative_result", "failed_hypothesis",
               "publication_note")
_ARG_ORDER = {t: i for i, t in enumerate(
    ("research_setting", "question", "hypothesis", "experiment", "observation", "finding",
     "consideration", "negative_result", "failed_hypothesis", "decision", "method_change",
     "publication_note"))}
R_IN_LABO   = "research:in_labo"
R_COMPOSED  = "research:composed_from"     # publication → chunk
R_PUBLISHED = "research:published_in"      # chunk → publication (backlink)
_CHUNK_RELS = {"based_on": "source:based_on", "concerns": "research:concerns",
               "produced_by": "research:produced_by", "assessed_by": "research:assessed_by",
               "supports": "research:supports", "contradicts": "research:contradicts",
               "supersedes": "research:supersedes", "follows": "research:follows",
               "refines": "research:refines"}
_NOTE_CONCEPTS = ("bench_note", "research_chunk")   # reads accept the ported + the legacy concept


class BenchResearchConcept(WorkbenchConcept):
    """`bench.*` — a research bench (the registered bench concept). Lifecycle from the base +
    source/hypothesis/evidence/proof/note families."""

    CONCEPT_PREFIX = "research"
    CONCEPT_LABEL = "Research bench — sources, hypotheses, evidence, proofs, notes (observed)"

    KIND = "research"
    _FAMILIES = ("source", "hypothesis", "evidence", "proof", "note", "publication")

    CONCEPT_METHODS: Dict[str, Any] = {
        "source.bind":  {"op": "op_source_bind", "action": "record",
                         "desc": "Reference a Source pool/stream into the bench (never a copy): "
                                 "research.source.bind name= pool=|stream="},
        "source.ls":    {"op": "op_source_ls", "action": "read",
                         "desc": "List the bench's bound sources: research.source.ls name="},
        "hyp.new":      {"op": "op_hyp_new", "action": "record",
                         "desc": "State a hypothesis: research.hyp.new name= text= [about=<atom>]"},
        "hyp.ls":       {"op": "op_hyp_ls", "action": "read", "desc": "List hypotheses: research.hyp.ls name="},
        "hyp.status":   {"op": "op_hyp_status", "action": "record",
                         "desc": "Set a hypothesis status: research.hyp.status name= id= "
                                 "open|supported|refuted|withdrawn"},
        "evidence.bind": {"op": "op_evidence_bind", "action": "record",
                          "desc": "Bind evidence to a hypothesis: research.evidence.bind name= hyp= "
                                  "ref=<atom|passage> [stance=supports|contradicts|context] [note=]"},
        "proof.new":    {"op": "op_proof_new", "action": "record",
                         "desc": "A proof over cited evidence: research.proof.new name= hyp= claim= evidence=<ids>"},
        "note":         {"op": "op_note", "action": "record",
                         "desc": "A bench note, or a research CHUNK when type= is given (a note-family "
                                 "entry with provenance): research.note name= text= [type= author= society= "
                                 "role= based_on= concerns= supersedes= …]"},
        "note.get":     {"op": "op_note_get", "action": "read",
                         "desc": "One note/chunk's detail + relations: research.note.get id="},
        "note.timeline": {"op": "op_note_timeline", "action": "read",
                          "desc": "The notes/chunks in cronon|argument|evidence|publication order "
                                  "(superseded retained): research.note.timeline name= [order=]"},
        "note.trace":   {"op": "op_note_trace", "action": "read",
                         "desc": "A note/chunk's relation links, both directions: research.note.trace id="},
        "publication.compose": {"op": "op_publication_compose", "action": "record",
                                "desc": "Compose a Publication Set (composed_from / published_in links): "
                                        "research.publication.compose name= pub= chunks=<ids>"},
        "publication.ls": {"op": "op_publication_ls", "action": "read",
                           "desc": "List the bench's Publication Sets: research.publication.ls name="},
        "publication.present": {"op": "op_publication_present", "action": "read",
                                "desc": "Present a Publication Set — its chunks in composed order: "
                                        "research.publication.present name= pub="},
    }

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _require_bench(self, name: str) -> str:
        alias = self._bench_alias(name)
        if not self._key(alias):
            raise ValueError(f"unknown bench '{name}' — bench.new it first")
        return alias

    def _sub(self, name: str, suffix: str) -> str:
        return f"{self._bench_alias(name)}:{suffix}"

    def _next_n(self, name: str, family_set: str) -> int:
        return len(self._members(self._sub(name, family_set))) + 1

    def _record(self, name: str, alias: str, key: str, family_set: str) -> None:
        self._add_to_set(self._sub(name, family_set), key)
        self._add_to_set(self._scope_set(name), key)

    # ── source family ──────────────────────────────────────────────────────────────
    def op_source_bind(self, name: str, pool: str = "", stream: str = "", cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            ref = pool or stream
            if not ref:
                raise ValueError("research.source.bind requires pool= or stream=")
            n = self._next_n(name, "sources")
            alias = self._sub(name, f"source:{n}")
            key = self._mk(alias, f"[{alias}] source reference → {ref}",
                           {"concept": "bench_source", "bench": self._bench_alias(name),
                            "ref": ref, "ref_kind": "pool" if pool else "stream", "n": n,
                            "author": self._client(), "created_wall": round(time.time(), 3)})
            self._record(name, alias, key, "sources")
            self._link(alias, ref, "bench:references")     # a reference, never a copy
            return {"bound": alias, "ref": ref, "n": n}
        return self._perform(name, "source", "bind", {"pool": pool, "stream": stream, "cast": cast}, _fn)

    def op_source_ls(self, name: str) -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)
        rows = []
        for k in self._members(self._sub(name, "sources")):
            m = self._meta(k)
            rows.append({"id": self._alias(k), "ref": m.get("ref"), "kind": m.get("ref_kind")})
        return {"bench": self._bench_alias(name), "sources": rows, "count": len(rows)}

    # ── hypothesis family ───────────────────────────────────────────────────────────
    def op_hyp_new(self, name: str, text: str = "", about: str = "", cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            if not text:
                raise ValueError("research.hyp.new requires text=")
            n = self._next_n(name, "hyps")
            alias = self._sub(name, f"hyp:{n}")
            key = self._mk(alias, text,
                           {"concept": "bench_hypothesis", "bench": self._bench_alias(name),
                            "text": text, "about": about or None, "status": "open", "n": n,
                            "author": self._client(), "created_wall": round(time.time(), 3)})
            self._record(name, alias, key, "hyps")
            if about:
                self._link(alias, about, "bench:about")
            return {"hyp": alias, "n": n, "status": "open", "text": text}
        return self._perform(name, "hypothesis", "new", {"text": text, "about": about, "cast": cast}, _fn)

    def op_hyp_ls(self, name: str) -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)
        rows = []
        for k in self._members(self._sub(name, "hyps")):
            m = self._meta(k)
            rows.append({"id": self._alias(k), "n": m.get("n"), "status": m.get("status"),
                         "text": m.get("text")})
        rows.sort(key=lambda r: r.get("n") or 0)
        return {"bench": self._bench_alias(name), "hypotheses": rows, "count": len(rows)}

    def op_hyp_status(self, name: str, id: str = "", status: str = "", cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            hid = self._resolve_hyp(name, id)
            if status not in _HYP_STATES:
                raise ValueError(f"status must be one of {list(_HYP_STATES)}")
            self._set_meta(self._key(hid), "status", status)
            return {"hyp": hid, "status": status}
        return self._perform(name, "hypothesis", "status", {"id": id, "status": status, "cast": cast}, _fn)

    def _resolve_hyp(self, name: str, ref: str) -> str:
        """A hypothesis by full alias, by n (an int), or by 'hyp:<n>'."""
        ref = str(ref or "").strip()
        if not ref:
            raise ValueError("a hypothesis id (or number) is required")
        if self._key(ref):
            return self._alias(self._key(ref))
        if ref.isdigit():
            cand = self._sub(name, f"hyp:{int(ref)}")
            if self._key(cand):
                return cand
        cand = self._sub(name, ref if ref.startswith("hyp:") else f"hyp:{ref}")
        if self._key(cand):
            return cand
        raise ValueError(f"unknown hypothesis '{ref}' on bench '{name}'")

    # ── evidence family ─────────────────────────────────────────────────────────────
    def op_evidence_bind(self, name: str, hyp: str = "", ref: str = "", stance: str = "supports",
                         note: str = "", cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            hid = self._resolve_hyp(name, hyp)
            if not ref:
                raise ValueError("research.evidence.bind requires ref=<atom|passage>")
            st = stance if stance in _STANCES else "context"
            n = self._next_n(name, "evidence")
            alias = self._sub(name, f"evidence:{n}")
            tick = self._world().op_tick(reason="env", ref=alias,
                                         world=self._bench_meta(name).get("world") or "default")
            key = self._mk(alias, note or f"evidence → {ref}",
                           {"concept": "bench_evidence", "bench": self._bench_alias(name),
                            "hyp": hid, "ref": ref, "stance": st, "note": note or None, "n": n,
                            "author": self._client(), "cronon": tick.get("cronon"),
                            "created_wall": round(time.time(), 3)})
            self._record(name, alias, key, "evidence")
            self._link(alias, hid, "bench:evidence_for")
            self._link(alias, ref, "bench:cites")
            return {"evidence": alias, "hyp": hid, "stance": st, "n": n}
        return self._perform(name, "evidence", "bind",
                             {"hyp": hyp, "ref": ref, "stance": stance, "note": note, "cast": cast}, _fn)

    # ── proof family ────────────────────────────────────────────────────────────────
    def op_proof_new(self, name: str, hyp: str = "", claim: str = "", evidence: Any = "",
                     cast: str = "") -> Dict[str, Any]:
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)

        def _fn():
            hid = self._resolve_hyp(name, hyp)
            if not claim:
                raise ValueError("research.proof.new requires claim=")
            ev_ids = evidence if isinstance(evidence, list) else \
                [e for e in str(evidence or "").replace(",", " ").split() if e]
            n = self._next_n(name, "proofs")
            alias = self._sub(name, f"proof:{n}")
            key = self._mk(alias, claim,
                           {"concept": "bench_proof", "bench": self._bench_alias(name),
                            "hyp": hid, "claim": claim, "evidence": ev_ids, "n": n,
                            "status": (self._meta(hid).get("status") or "open"),
                            "author": self._client(), "created_wall": round(time.time(), 3)})
            self._record(name, alias, key, "proofs")
            self._link(alias, hid, "bench:proves")
            for e in ev_ids:
                self._link(alias, e, "bench:cites")
            return {"proof": alias, "hyp": hid, "n": n, "evidence": ev_ids}
        return self._perform(name, "proof", "new",
                             {"hyp": hyp, "claim": claim, "evidence": evidence, "cast": cast}, _fn)

    # ── note family (a plain note, or a research CHUNK with provenance) ───────────────
    def _labo_name(self, labo: str) -> str:
        return labo.replace("labo:", "") if labo else labo

    def _cronon_mappings(self, at: Any) -> Any:
        m = self._meta("cronon:c%s" % at)
        return (m.get("mappings") or []) if m else []

    def op_note(self, name: str, text: str = "", ref: str = "", cast: str = "", type: str = "",
                labo: str = "", content: str = "", author: str = "", society: str = "", role: str = "",
                visibility: str = "public", based_on: str = "", concerns: str = "", produced_by: str = "",
                assessed_by: str = "", supports: str = "", contradicts: str = "", supersedes: str = "",
                follows: str = "", refines: str = "", branch: str = "", run: str = "") -> Dict[str, Any]:
        """A bench note, OR a research CHUNK when `type=` is given (§2 port, Option B): a chunk is a
        note-family entry with PROVENANCE — the author/society/role in meta + `set:wb:<name>:by:<author>`,
        the chunk `type`, and the reference fields as typed relations. Recorded through `_perform` so it
        tees an observation + a bench coordinate + the inline act; a superseded chunk is never deleted."""
        self._bind("")
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)
        balias = self._bench_alias(name)
        body = content or text
        is_chunk = bool(type)
        if is_chunk and type not in CHUNK_TYPES:
            raise ValueError("type must be one of %s (got '%s')" % (CHUNK_TYPES, type))
        nm = self._labo_name(labo) or _uslug(name)
        rels = {f: [x.strip() for x in str(v).split(",") if x.strip()]
                for f, v in (("based_on", based_on), ("concerns", concerns), ("produced_by", produced_by),
                             ("assessed_by", assessed_by), ("supports", supports),
                             ("contradicts", contradicts), ("supersedes", supersedes),
                             ("follows", follows), ("refines", refines))}

        def _fn():
            if not body:
                raise ValueError("research.note requires text= (or content=)")
            if is_chunk:
                seq = len(self._members("research:chunk:%s" % nm)) + 1
                alias = "research:chunk:%s:%d" % (nm, seq)
                at = self._akasha_now()
                auth = author or self._author()
                meta = {"concept": "bench_note", "family": "note", "bench": balias,
                        "labo": "labo:%s" % _uslug(nm), "type": type, "chunk_type": type,
                        "text": body, "content": body, "author": auth,
                        "observer": author or society or self._client(),
                        "observer_version": role or society or "human",
                        "society": society or None, "role": role or None, "cronon": at,
                        "external_time": self._cronon_mappings(at), "visibility": visibility,
                        "human_authored": bool(author) or not society, "n": seq,
                        "branch": branch or None, "run": run or None,
                        "mode": "thought", "purpose": "thought", **rels}
                self._mk(alias, "[%s] %s: %s" % (alias, type, body[:80]), meta)
                self._link(alias, "labo:%s" % _uslug(nm), R_IN_LABO)
                for f, rel in _CHUNK_RELS.items():
                    for r in rels[f]:
                        self._link(alias, r, rel)
                        if f == "supersedes" and self._key(r):
                            self._set_meta(self._key(r), "superseded_by",
                                           list(set((self._meta(r).get("superseded_by") or []) + [alias])))
                k = self._key(alias)
                self._add_to_set("research:chunk:%s" % nm, k)            # legacy index (reads)
                self._add_to_set("research:type:%s" % type, k)          # legacy index (reads)
                self._add_to_set("%s:notes" % balias, k)                # the note-family Set
                self._add_to_set("set:%s:notes:type:%s" % (balias, type), k)
                self._add_to_set("set:%s:by:%s" % (balias, _uslug(auth)), k)   # PROVENANCE Set
                self._add_to_set(self._scope_set(name), k)
                return {"chunk": alias, "note": alias, "labo": "labo:%s" % _uslug(nm), "type": type,
                        "cronon": at, "human_authored": meta["human_authored"],
                        "relations": {kk: v for kk, v in rels.items() if v}, "n": seq}
            # a plain note (unchanged shape)
            n = self._next_n(name, "notes")
            alias = self._sub(name, f"note:{n}")
            key = self._mk(alias, body,
                           {"concept": "bench_note", "family": "note", "bench": balias,
                            "text": body, "ref": ref or None, "n": n,
                            "author": author or self._client(), "created_wall": round(time.time(), 3)})
            self._record(name, alias, key, "notes")
            if ref:
                self._link(alias, ref, "bench:refers_to")
            return {"note": alias, "n": n}

        args = {"text": body, "ref": ref, "cast": cast, "type": type, "branch": branch, "run": run}
        if is_chunk:
            args.update({"mode": "thought", "purpose": "thought",
                         "act": {"declared": (body or type)[:80], "judged": None}})
        out = self._perform(name, "note", ("record" if is_chunk else "add"), args, _fn)
        if is_chunk and isinstance(out, dict) and out.get("note"):
            self._act(name, gid, out.get("observed_at_seq"), "chunk")
        return out

    def op_note_get(self, id: str) -> Dict[str, Any]:
        """One note/chunk's detail + relations."""
        self._bind("")
        k = self._key(id)
        if not k:
            raise ValueError("unknown note '%s'" % id)
        m = self.cortex.get_meta(k) or {}
        if m.get("concept") not in _NOTE_CONCEPTS:
            raise ValueError("'%s' is not a note/chunk" % id)
        return {"chunk": self._alias(k), "note": self._alias(k), "labo": m.get("labo"),
                "type": m.get("type"), "content": m.get("content") or m.get("text"),
                "author": m.get("author"), "society": m.get("society"), "role": m.get("role"),
                "human_authored": m.get("human_authored"), "cronon": m.get("cronon"),
                "external_time": m.get("external_time") or [], "visibility": m.get("visibility"),
                "superseded_by": m.get("superseded_by") or [],
                "relations": {f: m.get(f) or [] for f in _CHUNK_RELS}}

    def op_note_timeline(self, name: str, order: str = "cronon", limit: int = 500,
                         labo: str = "") -> Dict[str, Any]:
        """The bench's chunks in cronon | argument | evidence | publication order (superseded retained).
        The four orderings ship as macros over this op (app/config/macros/research.*.csl)."""
        self._bind("")
        nm = self._labo_name(labo) or _uslug(name)
        rows = []
        for k in self._members("research:chunk:%s" % nm):
            m = self.cortex.get_meta(k) or {}
            rows.append({"chunk": self._alias(k), "type": m.get("type"),
                         "content": (m.get("content") or m.get("text") or "")[:120],
                         "cronon": m.get("cronon"), "author": m.get("author"),
                         "society": m.get("society"), "human_authored": m.get("human_authored"),
                         "superseded": bool(m.get("superseded_by")),
                         "evidence": len(m.get("based_on") or [])})
        balias = self._bench_alias(name)
        if order == "argument":
            rows.sort(key=lambda r: (_ARG_ORDER.get(r["type"], 99), r.get("cronon") or 0))
        elif order == "evidence":
            rows.sort(key=lambda r: (-(r.get("evidence") or 0), r.get("cronon") or 0))
        elif order == "publication":
            pub = {}
            for ps in self._members("%s:publications" % balias):
                for i, ck in enumerate(self._members("%s:chunks" % self._alias(ps))):
                    pub[self._alias(ck)] = (self._alias(ps), i)
            rows.sort(key=lambda r: (pub.get(r["chunk"], ("~", 0)),))
        else:
            order = "cronon"
            rows.sort(key=lambda r: r.get("cronon") or 0)
        return {"labo": "labo:%s" % _uslug(nm), "bench": balias, "order": order,
                "chunks": rows[:max(1, int(limit))], "count": len(rows),
                "note": "failed/superseded research states are retained, never erased"}

    def op_note_trace(self, id: str) -> Dict[str, Any]:
        """A note/chunk's relation links, both directions."""
        self._bind("")
        k = self._key(id)
        if not k:
            raise ValueError("unknown note '%s'" % id)
        out_links: Dict[str, List[str]] = {}
        in_links: Dict[str, List[str]] = {}
        rel_names = {v: f for f, v in _CHUNK_RELS.items()}
        rel_names[R_PUBLISHED] = "published_in"
        for dst, rel in self.cortex.get_adjacent_links(k):
            f = rel_names.get(rel)
            if f:
                out_links.setdefault(f, []).append(self._alias(dst))
        ida = self._alias(k)
        nm = self._labo_name((self.cortex.get_meta(k) or {}).get("labo", ""))
        for ck in self._members("research:chunk:%s" % nm):
            cm = self.cortex.get_meta(ck) or {}
            for f in ("supports", "contradicts", "supersedes", "refines", "follows"):
                if ida in (cm.get(f) or []):
                    in_links.setdefault(f + "_by", []).append(self._alias(ck))
        return {"chunk": ida, "note": ida, "out": out_links, "in": in_links}

    # ── publication family (a Set + composed_from / published_in links) ──────────────
    def op_publication_compose(self, name: str, pub: str = "", chunks: str = "", labo: str = "",
                               cast: str = "") -> Dict[str, Any]:
        """Compose a Publication Set — a curated recomposition of chunks (§7). Records `composed_from`
        (publication → chunk) + `published_in` (chunk → publication) links; the research chronology is
        untouched. Runs through the recorder. Present it with `research.publication.present` (a macro)."""
        self._bind("")
        gid = self._bench_gid(name); self._bind(gid); self._require_bench(name)
        balias = self._bench_alias(name)
        nm = self._labo_name(labo) or _uslug(name)

        def _fn():
            if not pub:
                raise ValueError("research.publication.compose requires pub= (the set name)")
            pid = "%s:publication:%s" % (balias, _uslug(pub))
            order = [x.strip() for x in str(chunks).split(",") if x.strip()]
            at = self._akasha_now()
            artifact_id = self._digest({"pid": pid, "order": order})
            self._mk(pid, "[%s] Publication Set — %s (%d chunks)" % (pid, pub, len(order)),
                     {"concept": "bench_publication", "bench": balias, "labo": "labo:%s" % _uslug(nm),
                      "name": pub, "chunk_order": order, "cronon": at, "built_at_epoch": at,
                      "artifact_id": artifact_id, "client": self._author()})
            self._add_to_set("%s:publications" % balias, self._key(pid))
            for ck in order:
                if self._key(ck):
                    self._add_to_set("%s:chunks" % pid, self._key(ck))
                    self._link(pid, ck, R_COMPOSED)     # publication → chunk (composed_from)
                    self._link(ck, pid, R_PUBLISHED)    # chunk → publication (published_in)
            return {"publication_set": pid, "publication": pid, "name": pub, "chunks": order,
                    "count": len(order), "artifact_id": artifact_id, "built_at_epoch": at,
                    "note": "a curated recomposition of chunks; the research chronology is untouched"}
        return self._perform(name, "publication", "compose",
                             {"pub": pub, "cast": cast, "mode": "thought", "purpose": "thought"}, _fn)

    def op_publication_ls(self, name: str) -> Dict[str, Any]:
        """List the bench's Publication Sets."""
        gid = self._bench_gid(name); self._bind(gid)
        balias = self._bench_alias(name)
        out = []
        for k in self._members("%s:publications" % balias):
            m = self._meta(k)
            out.append({"publication_set": self._alias(k), "name": m.get("name"),
                        "chunks": len(m.get("chunk_order") or []), "cronon": m.get("cronon"),
                        "artifact_id": m.get("artifact_id")})
        return {"bench": balias, "publications": out, "count": len(out)}

    def op_publication_present(self, name: str, pub: str = "") -> Dict[str, Any]:
        """Present a Publication Set — its chunks in composed order (a read; the presentation macro
        forwards here). Backlinks are inspectable via research.note.trace."""
        gid = self._bench_gid(name); self._bind(gid)
        balias = self._bench_alias(name)
        pid = "%s:publication:%s" % (balias, _uslug(pub))
        if not self._key(pid):
            raise ValueError("unknown publication '%s' on %s" % (pub, balias))
        m = self._meta(pid)
        sections = []
        for ck in (m.get("chunk_order") or []):
            cm = self._meta(ck) or {}
            sections.append({"chunk": ck, "type": cm.get("type"),
                             "content": cm.get("content") or cm.get("text"), "author": cm.get("author")})
        return {"publication_set": pid, "name": m.get("name"), "sections": sections,
                "count": len(sections), "built_at_epoch": m.get("built_at_epoch"),
                "artifact_id": m.get("artifact_id")}
