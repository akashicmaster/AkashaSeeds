"""
Research Notebook Concept Model — research.* (PORTED to the Workbench, seeds-14 §2, Option B).

Every Labo has a Research Notebook whose persistent unit is the **Research Chunk** (Labo World-Model
§6): the evolving research process recorded in small addressable units, cronon-ordered, with failed and
superseded states preserved (§6.1). Publication Sets recompose chunks into papers (§7).

**As of the seeds-14 §2 port, the Notebook runs on the existing RESEARCH BENCH** (`bench_research.py`,
kind=research): a chunk is a **note-family entry with provenance** (`research.note` with `type=` + author/
society/role + the `set:wb:<labo>:by:*` provenance Set), a publication is a **Publication Set +
`composed_from`/`published_in` links + a presentation macro**, and the four orderings are **macros**
over `research.note.timeline`. `research.*` is a thin FORWARDER onto `bench.*` — this module mints/joins
NO atoms of its own (except the one-time hydrate backfill of legacy atoms); the bench is the only
writer. The old surface stays callable (and `labo.notebook`, which delegates here). One
`config/bench_<labo>.json` per Labo provisions the governed benches; a bench also auto-creates on the
first chunk. Spec: docs/for-llm/research-workbench-port.md.
"""
import logging
from typing import Any, Dict

from lib.akasha.api.concepts import UniversalConcept, slug as _uslug
from app.concepts.bench_research import BenchResearchConcept

logger = logging.getLogger("Harmonia.Concept.Research")


class ResearchNotebook(UniversalConcept):
    """The Research Notebook surface — forwards to the research bench (the recorder). No writer here."""

    CONCEPT_PREFIX = "research"
    # Two application models share this prefix (the bench kind is `bench_research`). The notebook is
    # the one `cross.query concepts=research`, space mounts, lens casts and `io.ingest model=research`
    # reach — the answer `get_class("research")` has always given.
    CONCEPT_PRIMARY = True
    CONCEPT_LABEL = "Research Notebook — cronon-ordered chunks as note-family entries (history + publication source)"

    CONCEPT_METHODS: Dict[str, Any] = {
        "chunk":    {"op": "op_chunk", "action": "record",
                     "desc": "Record a Research Chunk (type + content + provenance + relations) as a "
                             "note-family entry with provenance. → research.note"},
        "get":      {"op": "op_get", "action": "read", "desc": "Read one Research Chunk's detail + relations."},
        "timeline": {"op": "op_timeline", "action": "read",
                     "desc": "The Labo's chunks in cronon / argument / evidence / publication order (superseded preserved)."},
        "trace":    {"op": "op_trace", "action": "read",
                     "desc": "A chunk's relation links, both directions."},
        "publication": {"op": "op_publication", "action": "record",
                        "desc": "Compose a Publication Set (composed_from / published_in links). → research.publication.compose"},
        "publications": {"op": "op_publications", "action": "read", "desc": "List a Labo's Publication Sets."},
        "digest":   {"op": "op_digest", "action": "read", "desc": "A periodic digest projection of a Labo's recent chunks."},
        "layer.backfill": {"op": "op_layer_backfill", "action": "record",
                           "desc": "Hydrate: map legacy research_chunk atoms once to the note-entry shape "
                                   "(concept + provenance Sets + bench coordinate). Idempotent."},
    }

    def _br(self) -> BenchResearchConcept:
        br = getattr(self, "_br_cache", None)
        if br is None:
            br = self._br_cache = BenchResearchConcept(self.session)
        return br

    @staticmethod
    def _labo_name(labo: str) -> str:
        return labo.replace("labo:", "") if labo else labo

    def _ensure(self, labo: str) -> str:
        """Ensure the labo's PUBLIC research bench (named after the labo) exists; return the bench name."""
        nm = self._labo_name(labo)
        self._br().ensure_public_bench(nm, "research", by="research.ensure")
        return nm

    # ── forwarders (the research bench is the single writer / reader) ───────────────
    def op_chunk(self, labo: str, type: str, content: str, based_on: str = "", concerns: str = "",
                 produced_by: str = "", assessed_by: str = "", supports: str = "", contradicts: str = "",
                 supersedes: str = "", follows: str = "", refines: str = "", author: str = "",
                 society: str = "", role: str = "", visibility: str = "public") -> Dict[str, Any]:
        """Record a Research Chunk → `research.note` (a note-family entry with provenance, through the
        recorder). Return shape unchanged for back-compat."""
        nm = self._ensure(labo)
        return self._br().op_note(
            name=nm, labo=nm, type=type, content=content, based_on=based_on, concerns=concerns,
            produced_by=produced_by, assessed_by=assessed_by, supports=supports, contradicts=contradicts,
            supersedes=supersedes, follows=follows, refines=refines, author=author, society=society,
            role=role, visibility=visibility)

    def op_get(self, id: str) -> Dict[str, Any]:
        return self._br().op_note_get(id=id)

    def op_timeline(self, name: str, order: str = "cronon", limit: int = 500) -> Dict[str, Any]:
        nm = self._ensure(name)
        return self._br().op_note_timeline(name=nm, labo=nm, order=order, limit=limit)

    def op_trace(self, id: str) -> Dict[str, Any]:
        return self._br().op_note_trace(id=id)

    def op_publication(self, labo: str, name: str, chunks: str) -> Dict[str, Any]:
        nm = self._ensure(labo)
        return self._br().op_publication_compose(name=nm, labo=nm, pub=name, chunks=chunks)

    def op_publications(self, labo: str) -> Dict[str, Any]:
        nm = self._ensure(labo)
        return self._br().op_publication_ls(name=nm)

    def op_digest(self, labo: str, n: int = 10) -> Dict[str, Any]:
        nm = self._ensure(labo)
        tl = self._br().op_note_timeline(name=nm, labo=nm, order="cronon")
        chunks = tl.get("chunks", [])[-max(1, int(n)):]
        return {"labo": tl.get("labo"), "digest": chunks, "count": len(chunks),
                "note": "broadcast/publication outputs backlink to these research chunks"}

    # ── hydrate backfill (item 4/5) ─────────────────────────────────────────────────
    def op_layer_backfill(self, since_epoch: Any = None) -> Dict[str, Any]:
        """Map every legacy `research_chunk` atom ONCE to the ported note-entry shape: re-tag the concept
        to `bench_note` + the D2-M facets, join the research bench's notes / by:<author> / type Sets, and
        mint the bench coordinate `cronon:wb:<labo>:c<cronon>` — WITHOUT rewriting content. Idempotent +
        bounded: enumerated from `labo:all` → each labo's `research:chunk:<labo>` set; a chunk already in
        note shape is skipped, so `assigned=0` on every later boot. `[hydrate] research_layer …`."""
        assigned = 0
        self._space = ""
        for lk in self._members("labo:all"):
            nm = (self._alias(lk) or "").replace("labo:", "")
            if not nm:
                continue
            balias = "wb:%s" % _uslug(nm)
            for ck in self._members("research:chunk:%s" % nm):
                m = self.cortex.get_meta(ck) or {}
                if m.get("concept") == "bench_note":
                    continue
                if m.get("concept") != "research_chunk":
                    continue
                typ = m.get("type") or "observation"
                auth = m.get("author") or "unknown"
                self._set_meta(ck, "concept", "bench_note")
                self._set_meta(ck, "family", "note")
                self._set_meta(ck, "chunk_type", typ)
                self._set_meta(ck, "mode", "thought")
                self._set_meta(ck, "purpose", "thought")
                self._set_meta(ck, "bench", balias)
                self._add_to_set("%s:notes" % balias, ck)
                self._add_to_set("set:%s:notes:type:%s" % (balias, typ), ck)
                self._add_to_set("set:%s:by:%s" % (balias, _uslug(auth)), ck)
                cr = m.get("cronon")
                if isinstance(cr, int):
                    self._add_to_set("cronon:%s:c%d" % (balias, cr), ck)
                assigned += 1
        if assigned:
            logger.info("[hydrate] research_layer mapped=%d legacy research_chunk → note", assigned)
        # seeds-14 §2 — the port completion line (once per boot pass): the research lab runs on the
        # research bench; all 7 research.* ops forward to bench.*, the orderings + present are macros.
        logger.info("[port] lab=research templates=0 old_ops=7 forwarded=7 retired_records=%d", assigned)
        return {"assigned": assigned}
