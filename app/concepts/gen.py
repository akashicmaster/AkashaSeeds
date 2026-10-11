"""
Genealogy Concept Model — where traditions come from (cross-laboratory provenance).

`gen` is the SUPERSET research model of the Genealogy Laboratory. It traces how a body of
knowledge emerges from multiple sources by treating a corpus as ordered, measurable *loci* and
measuring each locus through MANY discipline *lenses* at once — textual strata (stylometry),
chronology, concepts, traditions, materials, attestation, geography. Where several lenses break at
the same locus, that boundary is a *corroborated provenance*; where a lens breaks elsewhere, or
reads the loci as continuous, the divergence is held as an unresolved tension — nothing is collapsed
into one truth. Across works, a *source-stemma* (@derives_from) traces the corpus upstream to its
origins, and explicit *alignments* (@aligns_locus) let a lens be crossed across recensions/works
that number differently.

  work ── @next_locus ─▶ locus … locus            the reading order (the composition trajectory)
  measure ─ @of_locus ▶ locus ; ─ @of_feature ▶ feature     one matrix cell  (io.ingest target)
  feature ─ @via_lens ─▶ lens                     a feature belongs to one discipline lens
  seam ── @seam_after ─▶ locus                    a boundary that falls AFTER this locus
  align ── @aligns_locus ▶ locus (×2)             an explicit cross-witness/work correspondence
  work ── @derives_from ─▶ work                   the source-stemma (a corpus upstream)
  hyp  ── @posits_seam ▶ seam ; @groups_layer ▶ layer       a stratification hypothesis
  source ─ @supports_hyp / @contests_hyp ▶ hyp    the evidence, with its tension

Stylometry (`sty`, app/concepts/sty.py) is a SUBSET of this model — genealogy restricted to
the single stylometric lens (single-work seam detection), without the cross-lens overlay, the
alignments, or the corpus stemma. Both share this engine; `sty` narrows the surface and uses the
`sty:` namespace, `gen` owns the full surface under `gen:`.

The DURABLE catalog (work, witnesses, loci, features, layers, seams, hypotheses, sources, the
source-stemma) is authored as an `.ak` pack. The RUNTIME matrix — the actual measured values — is
streamed in with `io.ingest model=gen into=<work> path=<matrix.jsonl>` (each record a
{locus, feature, value, witness} cell). `gen.matrix` returns the grid, `gen.seams` reads where the
joins stand, `gen.cross` overlays every lens (coincidence vs divergence), `gen.genealogy` casts the
stemma, `gen.alignment` the correspondence ribbon, `gen.project` casts the projections for the
Archives lab. Degradation-first: seam detection is deterministic stdlib (z-scored adjacent-locus
distance); a connected model can sharpen the SAME surface without touching the pipeline.
"""

import math
import logging
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.api.concepts import BaseConcept
from lib.akasha.api.concepts import ImportableMixin

logger = logging.getLogger("Harmonia.Concept.Gen")

_W, _R = "record", "read"


class GenConcept(BaseConcept, ImportableMixin):
    """Genealogy / cross-provenance operators — the SUPERSET (many lenses · alignment · stemma).

    Stylometry (StyConcept, sty.py) subclasses this and narrows it to the single stylometric lens."""

    CONCEPT_PREFIX = "gen"
    NS = "gen"

    # io.ingest model=gen into=<work>: raw measurement rows → matrix cells. locus+feature+value
    # are required; witness is preferred (which recension the value was measured on).
    IMPORT_SCHEMA = {
        "model": "gen", "requires": ["locus", "feature", "value"], "prefers": ["witness", "unit"],
        "min_nodes": 1,
        "description": "Stylometric feature×locus measurements → matrix cells. Each record is one "
                       "{locus, feature, value, [witness]} cell. into=<work id/alias>.",
    }
    CONCEPT_METHODS = {
        "work":     {"op": "op_work", "action": _W, "cli": "gen.work", "args": ["id"],
                     "desc": "Mint/open a work under study: gen.work id=<slug> [title=\"…\"] [lang=pali] "
                             "[derives=<work,work>] [kind=source|stratified]"},
        "genealogy":{"op": "op_genealogy", "action": _R, "cli": "gen.genealogy", "args": [],
                     "desc": "The source-stemma across works (@derives_from) — trace a corpus upstream: "
                             "gen.genealogy [root=<work>]"},
        "witness":  {"op": "op_witness", "action": _W, "cli": "gen.witness", "args": ["work", "id"],
                     "desc": "Add a witness/recension to a work: gen.witness work=<w> id=<slug> [title=] [lang=]"},
        "locus":    {"op": "op_locus", "action": _W, "cli": "gen.locus", "args": ["work", "id"],
                     "desc": "Add an ordered locus (book/chapter): gen.locus work=<w> id=<slug> [title=] "
                             "[after=<locus>] [layer=<layer>] [attested=<witness,witness>]"},
        "align":    {"op": "op_align", "action": _W, "cli": "gen.align", "args": ["a", "b"],
                     "desc": "Align two loci ACROSS witnesses/recensions or works — an explicit "
                             "locus↔locus correspondence for when the numbering diverges (Pāli III ↔ "
                             "Chinese ch.2). A first-class, traceable alignment atom: gen.align a=<locus> "
                             "b=<locus> [kind=parallel|translation|quotation|adaptation] [note=]"},
        "alignment":{"op": "op_alignment", "action": _R, "cli": "gen.alignment", "args": ["work"],
                     "desc": "The cross-witness/work correspondence map — per locus, its aligned "
                             "counterparts and which work they sit in (the ribbon that survives divergent "
                             "numbering; the substrate for crossing a lens across the corpus): "
                             "gen.alignment work=<w>"},
        "feature":  {"op": "op_feature", "action": _W, "cli": "gen.feature", "args": ["id"],
                     "desc": "Define a feature in a measurement lens: gen.feature id=<slug> [title=] [desc=] "
                             "[higher=] [lens=stylometry|chronology|geography|concept|attestation]"},
        "layer":    {"op": "op_layer", "action": _W, "cli": "gen.layer", "args": ["work", "id"],
                     "desc": "Define a composition stratum: gen.layer work=<w> id=<slug> [title=] [desc=]"},
        "seam":     {"op": "op_seam", "action": _W, "cli": "gen.seam", "args": ["work", "id", "after"],
                     "desc": "Posit a composition seam AFTER a locus: gen.seam work=<w> id=<slug> after=<locus> [desc=]"},
        "hyp":      {"op": "op_hyp", "action": _W, "cli": "gen.hyp", "args": ["work", "id"],
                     "desc": "Add a stratification hypothesis: gen.hyp work=<w> id=<slug> [title=] [desc=] "
                             "[seams=<seam,seam>] [layers=<layer,layer>]"},
        "source":   {"op": "op_source", "action": _W, "cli": "gen.source", "args": ["id"],
                     "desc": "Add a published source: gen.source id=<slug> [title=] [author=] [year=] "
                             "[supports=<hyp>] [contests=<hyp>] [locator=]"},
        "measure":  {"op": "op_measure", "action": _W, "cli": "gen.measure", "args": ["work", "locus", "feature", "value"],
                     "desc": "Record ONE matrix cell (CLI-native): gen.measure work=<w> locus=<l> feature=<f> value=<x> [witness=]"},
        "ingest":   {"op": "op_ingest", "action": _W, "cli": "gen.ingest", "args": ["work"],
                     "desc": "Batch-ingest matrix cells (RPC form): gen.ingest work=<w> records=<json>"},
        "matrix":   {"op": "op_matrix", "action": _R, "cli": "gen.matrix", "args": ["work"],
                     "desc": "The feature×locus measurement grid: gen.matrix work=<w> [witness=]"},
        "seams":    {"op": "op_seams", "action": _R, "cli": "gen.seams", "args": ["work"],
                     "desc": "Where the joins stand — z-scored adjacent-locus distance + the features "
                             "driving each, aligned to the posited seams: gen.seams work=<w> [witness=]"},
        "compare":  {"op": "op_compare", "action": _R, "cli": "gen.compare", "args": ["work", "locus"],
                     "desc": "Inspect ONE locus in the feature space — distance from prev / next / corpus "
                             "centroid + the features driving it + its distinctiveness rank (a distance is "
                             "evidence, not an attribution): gen.compare work=<w> locus=<l> [witness=]"},
        "cross":    {"op": "op_cross", "action": _R, "cli": "gen.cross", "args": ["work"],
                     "desc": "The interdisciplinary overlay — every feature-space (lens) boundary on the "
                             "SAME loci: coincidence (corroborated provenance) vs divergence (a lens that "
                             "abstains, a held tension): gen.cross work=<w> [lenses=<lens,lens>]"},
        "project":  {"op": "op_project", "action": _R, "cli": "gen.project", "args": ["work"],
                     "desc": "Cast the composition-trajectory projection for the lab GUI: "
                             "gen.project work=<w> [mode=trajectory|matrix|seams|hypotheses|layers|sources|cross]"},
        "trace":    {"op": "op_trace", "action": _R, "cli": "gen.trace", "args": ["id"],
                     "desc": "Trace a projection object back to its source atom: gen.trace id=<alias/key>"},
    }

    # ── identity / minting helpers ────────────────────────────────────────────
    def _author(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _scopes(self) -> List[str]:
        a = self._author()
        return [f"owner:user_{a}", f"view:user_{a}"]

    def _resolve(self, ref: str) -> Optional[str]:
        """Resolve a slug OR a full alias OR a raw key to an atom key."""
        ref = (ref or "").strip()
        if not ref:
            return None
        return self.cortex.resolve_alias(ref) or (ref if self.cortex.get_chunk(ref) else None)

    def _mint(self, alias: str, content: str, meta: Optional[Dict[str, Any]] = None,
              sets: Tuple[str, ...] = ()) -> str:
        """Idempotent: reuse the atom if the alias already resolves, else create + alias it."""
        key = self.cortex.resolve_alias(alias)
        if not key:
            key = self.cortex.put_chunk(content=content, meta=(meta or {}),
                                        author=self._author(), scopes=self._scopes())
            # atoms are content-addressed: two distinct loci that share a title (e.g. the
            # "Sūtrasthāna" of both the Caraka and the Suśruta Saṃhitā) would collide into ONE
            # atom and the alias would go first-wins, corrupting the per-work sets and the
            # @next_locus chains. If the returned atom already owns a different alias, salt the
            # content (invisibly — a trailing newline the reader ignores) to force a fresh atom.
            try:
                owned = self.cortex.get_aliases_by_key(key) or []
            except Exception:
                owned = []
            if owned and alias not in owned:
                key = self.cortex.put_chunk(content=(content + "\n" + alias), meta=(meta or {}),
                                            author=self._author(), scopes=self._scopes())
            try:
                self.cortex.set_alias(key, alias)
            except Exception:
                pass
        elif meta:                                   # refresh meta on an existing catalog atom
            try:
                self.cortex.core.merge_meta(key, dict(meta))    # one atomic merge, never read-edit-write
            except Exception:
                pass
        for s in sets:
            try:
                self.cortex.add_to_set(s, key)
            except Exception:
                pass
        return key

    def _link(self, src: str, dst: str, rel: str) -> None:
        if src and dst:
            try:
                self.cortex.put_link(src, dst, rel, author=self._author())
            except Exception:
                pass

    def _alias_of(self, key: str) -> str:
        try:
            al = self.cortex.get_aliases_by_key(key) or []
        except Exception:
            al = []
        return next((a for a in al if a.startswith(f"{self.NS}:")), (al[0] if al else key))

    def _label(self, key: str) -> str:
        meta = self.cortex.get_meta(key) or {}
        if meta.get("title"):
            return meta["title"]
        c = (self.cortex.get_chunk(key) or "").strip()      # .ak-loaded atoms carry the title as content
        if c and len(c) <= 90 and "\n" not in c:
            return c.rstrip(".")
        return self._alias_of(key).split(":")[-1].replace("_", " ")

    # ── catalog builders (CLI-native; the .ak pack authors the same atoms durably) ──
    def op_work(self, id: str = "", title: str = "", lang: str = "", desc: str = "",
                derives: str = "", kind: str = "") -> Dict[str, Any]:
        slug = id.strip()
        if not slug:
            return {"error": "gen.work needs id="}
        alias = slug if slug.startswith(f"{self.NS}:work:") else f"{self.NS}:work:{slug}"
        key = self._mint(alias, (desc or title or slug),
                         {"title": title or slug.split(':')[-1], "lang": lang, "node_kind": "work",
                          "stream_kind": (kind or "")},
                         sets=(f"{self.NS}:works",))
        for src in [x.strip() for x in (derives or "").split(",") if x.strip()]:
            sk = self._resolve(src if src.startswith(f"{self.NS}:") else f"{self.NS}:work:{src}")
            if sk:
                self._link(key, sk, "@derives_from")
        return {"status": "ok", "work": alias, "key": key}

    def op_genealogy(self, root: str = "") -> Dict[str, Any]:
        """The source-stemma over the works: nodes = works, edges = @derives_from (downstream→source)."""
        works = list(self.cortex.get_collection_members(f"{self.NS}:works") or [])
        info = {}
        for wk in works:
            wa = self._alias_of(wk)
            meta = self.cortex.get_meta(wk) or {}
            has_loci = bool(self.cortex.get_collection_members(f"{wa}:loci"))
            has_mat = bool(self.cortex.get_collection_members(f"{wa}:measures"))
            deriv = [self._alias_of(d) for d, _ in (self.cortex.get_adjacent_links(wk, "@derives_from") or [])]
            info[wa] = {"id": wa, "title": self._label(wk),
                        "kind": meta.get("stream_kind") or ("stratified" if has_loci else "source"),
                        "has_stratification": has_loci, "has_matrix": has_mat,
                        "note": self.cortex.get_chunk(wk) or "", "derives_from": deriv,
                        "source_atom": wa}
        edges = [{"from": wa, "to": d} for wa, n in info.items() for d in n["derives_from"] if d in info]
        keep = set(info)
        if root:
            rk = self._resolve(root if root.startswith(f"{self.NS}:") else f"{self.NS}:work:{root}")
            ra = self._alias_of(rk) if rk else None
            if ra:                                        # keep the weakly-connected component of root
                adj = {}
                for e in edges:
                    adj.setdefault(e["from"], set()).add(e["to"]); adj.setdefault(e["to"], set()).add(e["from"])
                seen = set(); stack = [ra]
                while stack:
                    c = stack.pop()
                    if c in seen: continue
                    seen.add(c); stack.extend(adj.get(c, ()))
                keep = seen or {ra}
        nodes = [info[a] for a in info if a in keep]
        # depth from the upstream roots (no derives_from within the kept set) for layout
        kept_edges = [e for e in edges if e["from"] in keep and e["to"] in keep]
        upstream = {n["id"]: [e["to"] for e in kept_edges if e["from"] == n["id"]] for n in nodes}
        depth = {}
        def _d(a, guard):
            if a in depth: return depth[a]
            if a in guard: return 0
            ups = upstream.get(a, [])
            depth[a] = 0 if not ups else 1 + max(_d(u, guard | {a}) for u in ups)
            return depth[a]
        for n in nodes:
            n["depth"] = _d(n["id"], set())
        return {"status": "ok", "root": (root or None), "nodes": nodes, "edges": kept_edges}

    def op_witness(self, work: str = "", id: str = "", title: str = "", lang: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        walias = self._alias_of(wk)
        alias = id if id.startswith(f"{self.NS}:witness:") else f"{self.NS}:witness:{id}"
        key = self._mint(alias, (title or id), {"title": title or id, "lang": lang, "node_kind": "witness"},
                         sets=(f"{walias}:witnesses",))
        self._link(key, wk, "@witness_of")
        return {"status": "ok", "witness": alias, "key": key}

    def op_locus(self, work: str = "", id: str = "", title: str = "", after: str = "",
                 layer: str = "", attested: str = "", desc: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        walias = self._alias_of(wk)
        alias = id if id.startswith(f"{self.NS}:locus:") else f"{self.NS}:locus:{id}"
        # ordinal: 1 + current count of loci in the work's ordered set
        try:
            n = len(self.cortex.get_collection_members(f"{walias}:loci") or [])
        except Exception:
            n = 0
        key = self._mint(alias, (desc or title or id),
                         {"title": title or id, "node_kind": "locus", "ordinal": n + 1},
                         sets=(f"{walias}:loci",))
        self._link(key, wk, "@in_work")
        if after:
            ak = self._resolve(after if after.startswith(f"{self.NS}:") else f"{self.NS}:locus:{after}")
            if ak:
                self._link(ak, key, "@next_locus")
        if layer:
            lk = self._resolve(layer if layer.startswith(f"{self.NS}:") else f"{self.NS}:layer:{layer}")
            if lk:
                self._link(key, lk, "@in_layer")
        for wtn in [w for w in (attested or "").split(",") if w.strip()]:
            wk2 = self._resolve(wtn if wtn.startswith(f"{self.NS}:") else f"{self.NS}:witness:{wtn.strip()}")
            if wk2:
                self._link(key, wk2, "@attested_in")
        return {"status": "ok", "locus": alias, "key": key, "ordinal": n + 1}

    def op_align(self, a: str = "", b: str = "", note: str = "", kind: str = "") -> Dict[str, Any]:
        """[gen.align] Align two loci ACROSS witnesses/recensions or works — the EXPLICIT locus↔locus
        correspondence that survives divergent chapter/section numbering (Pāli book III ↔ Chinese
        chapter 2, or a Caraka sthāna ↔ its Suśruta counterpart). `@attested_in` only flags THAT a
        locus has a parallel in a witness; alignment records WHICH locus it is, so a lens can be crossed
        across recensions/works that number differently. Realised as a first-class, order-independent
        alignment atom (kind + note, traceable via gen.trace — P5); idempotent per unordered pair."""
        ak = self._resolve(a if a.startswith(f"{self.NS}:") else f"{self.NS}:locus:{a}")
        bk = self._resolve(b if b.startswith(f"{self.NS}:") else f"{self.NS}:locus:{b}")
        if not ak or not bk:
            return {"error": f"gen.align needs two known loci (a={a!r} b={b!r})"}
        if ak == bk:
            return {"error": "gen.align: a and b are the same locus"}
        kind = (kind or "parallel").strip()
        lo, hi = sorted([ak, bk])                       # order-independent identity (one atom per pair)
        alias = f"{self.NS}:align:{lo[:8]}_{hi[:8]}"
        title = f"{self._label(ak)} ⇔ {self._label(bk)}"
        key = self._mint(alias, (note or title),
                         {"title": title, "node_kind": "alignment", "kind": kind, "note": note,
                          "a": lo, "b": hi}, sets=(f"{self.NS}:alignments",))
        self._link(key, ak, "@aligns_locus")
        self._link(key, bk, "@aligns_locus")
        return {"status": "ok", "alignment": alias, "a": self._alias_of(ak),
                "b": self._alias_of(bk), "kind": kind}

    def _aligned(self, locus_key: str) -> List[Tuple[str, str, str]]:
        """Loci aligned to this one via any alignment atom: [(counterpart_key, kind, align_atom)].
        Symmetric — read through the atom's two @aligns_locus targets, in either direction."""
        out = []
        for atom, _ in (self.cortex.get_incoming_links(locus_key, "@aligns_locus") or []):
            m = self.cortex.get_meta(atom) or {}
            for tgt, _r in (self.cortex.get_adjacent_links(atom, "@aligns_locus") or []):
                if tgt and tgt != locus_key:
                    out.append((tgt, m.get("kind", "parallel"), atom))
        return out

    def op_alignment(self, work: str = "", witness: str = "") -> Dict[str, Any]:
        """[gen.alignment] The cross-witness / cross-work correspondence map: for each locus of the
        work (in reading order), its aligned counterparts and which work they sit in. This is the
        ribbon that survives divergent numbering, and the substrate for crossing a lens across the
        corpus (align the loci, then overlay each work's boundaries on the shared correspondence)."""
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        wa = self._alias_of(wk)
        rows, pairs = [], 0
        for lk in (self.cortex.get_collection_members(f"{wa}:loci") or []):
            cps = []
            for (tgt, kind, atom) in self._aligned(lk):
                owner = next((d for d, _ in (self.cortex.get_adjacent_links(tgt, "@in_work") or [])), "")
                cps.append({"locus": self._alias_of(tgt), "label": self._label(tgt),
                            "work": self._alias_of(owner) if owner else "", "kind": kind,
                            "source_atom": self._alias_of(atom)})
                pairs += 1
            if cps:
                cps.sort(key=lambda c: c["locus"])
                rows.append({"locus": self._alias_of(lk), "label": self._label(lk),
                             "ordinal": (self.cortex.get_meta(lk) or {}).get("ordinal"), "aligned": cps})
        rows.sort(key=lambda r: (r.get("ordinal") or 0))
        return {"status": "ok", "work": wa, "count": len(rows), "pairs": pairs, "alignment": rows}

    def op_feature(self, id: str = "", title: str = "", desc: str = "", higher: str = "",
                   lens: str = "") -> Dict[str, Any]:
        alias = id if id.startswith(f"{self.NS}:feature:") else f"{self.NS}:feature:{id}"
        lens = (lens or "stylometry").strip()
        key = self._mint(alias, (desc or title or id),
                         {"title": title or id, "node_kind": "feature", "higher_means": higher, "lens": lens},
                         sets=(f"{self.NS}:features",))
        lk = self._mint(f"{self.NS}:lens:{lens}", lens.replace("_", " ").title() + " lens",
                        {"title": lens.replace("_", " ").title() + " lens", "node_kind": "lens"},
                        sets=(f"{self.NS}:lenses",))
        self._link(key, lk, "@via_lens")
        return {"status": "ok", "feature": alias, "key": key, "lens": lens}

    def _feature_lens(self, feat_alias: str) -> str:
        """A feature's measurement lens — meta.lens (runtime) or the @via_lens link (.ak) or stylometry."""
        k = self._resolve(feat_alias)
        if not k:
            return "stylometry"
        meta = self.cortex.get_meta(k) or {}
        if meta.get("lens"):
            return meta["lens"]
        for dst, rel in (self.cortex.get_adjacent_links(k, "@via_lens") or []):
            return self._alias_of(dst).split(":")[-1]
        return "stylometry"

    def op_layer(self, work: str = "", id: str = "", title: str = "", desc: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        walias = self._alias_of(wk) if wk else f"{self.NS}:work:unknown"
        alias = id if id.startswith(f"{self.NS}:layer:") else f"{self.NS}:layer:{id}"
        key = self._mint(alias, (desc or title or id), {"title": title or id, "node_kind": "layer"},
                         sets=(f"{walias}:layers",))
        if wk:
            self._link(key, wk, "@in_work")
        return {"status": "ok", "layer": alias, "key": key}

    def op_seam(self, work: str = "", id: str = "", after: str = "", desc: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        walias = self._alias_of(wk) if wk else f"{self.NS}:work:unknown"
        alias = id if id.startswith(f"{self.NS}:seam:") else f"{self.NS}:seam:{id}"
        key = self._mint(alias, (desc or id), {"title": desc or id, "node_kind": "seam"},
                         sets=(f"{walias}:seams",))
        ak = self._resolve(after if after.startswith(f"{self.NS}:") else f"{self.NS}:locus:{after}")
        if ak:
            self._link(key, ak, "@seam_after")
        if wk:
            self._link(key, wk, "@in_work")
        return {"status": "ok", "seam": alias, "key": key, "after": after}

    def op_hyp(self, work: str = "", id: str = "", title: str = "", desc: str = "",
               seams: str = "", layers: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        walias = self._alias_of(wk) if wk else f"{self.NS}:work:unknown"
        alias = id if id.startswith(f"{self.NS}:hyp:") else f"{self.NS}:hyp:{id}"
        key = self._mint(alias, (desc or title or id), {"title": title or id, "node_kind": "hypothesis"},
                         sets=(f"{walias}:hyps",))
        if wk:
            self._link(key, wk, "@in_work")
        for s in [x for x in (seams or "").split(",") if x.strip()]:
            sk = self._resolve(s if s.startswith(f"{self.NS}:") else f"{self.NS}:seam:{s.strip()}")
            if sk:
                self._link(key, sk, "@posits_seam")
        for l in [x for x in (layers or "").split(",") if x.strip()]:
            lk = self._resolve(l if l.startswith(f"{self.NS}:") else f"{self.NS}:layer:{l.strip()}")
            if lk:
                self._link(key, lk, "@groups_layer")
        return {"status": "ok", "hyp": alias, "key": key}

    def op_source(self, id: str = "", title: str = "", author: str = "", year: str = "",
                  supports: str = "", contests: str = "", locator: str = "", desc: str = "") -> Dict[str, Any]:
        alias = id if id.startswith(f"{self.NS}:source:") else f"{self.NS}:source:{id}"
        head = title or id
        cite = " · ".join([x for x in (author, year) if x])
        key = self._mint(alias, (desc or (head + (" — " + cite if cite else ""))),
                         {"title": head, "author": author, "year": year, "locator": locator, "node_kind": "source"},
                         sets=(f"{self.NS}:sources",))
        for h in [x for x in (supports or "").split(",") if x.strip()]:
            hk = self._resolve(h if h.startswith(f"{self.NS}:") else f"{self.NS}:hyp:{h.strip()}")
            if hk:
                self._link(key, hk, "@supports_hyp")
        for h in [x for x in (contests or "").split(",") if x.strip()]:
            hk = self._resolve(h if h.startswith(f"{self.NS}:") else f"{self.NS}:hyp:{h.strip()}")
            if hk:
                self._link(key, hk, "@contests_hyp")
        return {"status": "ok", "source": alias, "key": key}

    # ── matrix cells ──────────────────────────────────────────────────────────
    def _put_measure(self, work_key: str, walias: str, locus: str, feature: str,
                     value: Any, witness: str = "") -> Optional[str]:
        lk = self._resolve(locus if locus.startswith(f"{self.NS}:") else f"{self.NS}:locus:{locus}")
        fk = self._resolve(feature if feature.startswith(f"{self.NS}:") else f"{self.NS}:feature:{feature}")
        if not lk or not fk:
            return None
        try:
            val = float(value)
        except (TypeError, ValueError):
            return None
        la = self._alias_of(lk).split(":")[-1]
        fa = self._alias_of(fk).split(":")[-1]
        wtag = (witness or "obs").split(":")[-1]
        alias = f"{self.NS}:measure:{walias.split(':')[-1]}:{la}:{fa}:{wtag}"
        key = self._mint(alias, f"{fa}({la})={val}",
                         {"node_kind": "measure", "value": val, "locus": self._alias_of(lk),
                          "feature": self._alias_of(fk), "witness": witness},
                         sets=(f"{walias}:measures",))
        self._link(key, lk, "@of_locus")
        self._link(key, fk, "@of_feature")
        if witness:
            wk2 = self._resolve(witness if witness.startswith(f"{self.NS}:") else f"{self.NS}:witness:{witness}")
            if wk2:
                self._link(key, wk2, "@on_witness")
        return key

    def op_measure(self, work: str = "", locus: str = "", feature: str = "", value: str = "",
                   witness: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        key = self._put_measure(wk, self._alias_of(wk), locus, feature, value, witness)
        return {"status": "ok", "measure": (self._alias_of(key) if key else None)} if key else \
               {"error": "could not record measure (unknown locus/feature or bad value)"}

    def op_ingest(self, work: str = "", records: Any = None) -> Dict[str, Any]:
        if not isinstance(records, list):
            return {"error": "gen.ingest needs records=<json list of {locus,feature,value,witness}>"}
        return self.import_records(records, into=work)

    # ── io.ingest model=gen into=<work> path=<matrix.jsonl> ─────────────────────
    def import_records(self, records: List[Dict[str, Any]], into: str = "",
                       mapping: Dict[str, str] = None, **opts) -> Dict[str, Any]:
        into = (into or "").strip()
        wk = self._resolve(into if into.startswith(f"{self.NS}:") else f"{self.NS}:work:{into}")
        if not wk:
            raise ValueError("gen import needs into=<work id/alias> (mint it first with gen.work)")
        walias = self._alias_of(wk)
        n = 0; skipped = 0; feats = set(); loci = set()
        for rec in records:
            locus = self._mapped(rec, mapping, "locus", "unit_id", "section")
            feature = self._mapped(rec, mapping, "feature", "metric", "variable")
            value = self._mapped(rec, mapping, "value", "score", "measurement")
            witness = self._mapped(rec, mapping, "witness", "recension", "manuscript")
            if not locus or not feature or value == "":
                skipped += 1
                continue
            key = self._put_measure(wk, walias, locus, feature, value, witness)
            if key:
                n += 1; feats.add(feature); loci.add(locus)
            else:
                skipped += 1
        return {"status": "ingested", "work": walias, "count": n, "skipped": skipped,
                "features": sorted(feats), "loci": sorted(loci)}

    # ── reads: matrix / seams / projection ──────────────────────────────────────
    def _ordered_loci(self, walias: str) -> List[str]:
        """Locus keys in reading order (by @next_locus chain; ordinal meta as a fallback)."""
        members = list(self.cortex.get_collection_members(f"{walias}:loci") or [])
        if not members:
            return []
        # follow the @next_locus chain from the head (a locus with no incoming @next_locus)
        nxt = {}; has_in = set()
        for k in members:
            for dst, rel in (self.cortex.get_adjacent_links(k, "@next_locus") or []):
                nxt[k] = dst; has_in.add(dst)
        heads = [k for k in members if k not in has_in]
        order = []
        if heads:
            cur = sorted(heads, key=lambda k: (self.cortex.get_meta(k) or {}).get("ordinal", 0))[0]
            seen = set()
            while cur and cur not in seen:
                seen.add(cur); order.append(cur); cur = nxt.get(cur)
            # append any stragglers not on the chain, by ordinal
            for k in sorted(members, key=lambda k: (self.cortex.get_meta(k) or {}).get("ordinal", 0)):
                if k not in seen:
                    order.append(k)
        else:
            order = sorted(members, key=lambda k: (self.cortex.get_meta(k) or {}).get("ordinal", 0))
        return order

    def _matrix(self, walias: str, witness: str = "") -> Dict[str, Any]:
        loci = self._ordered_loci(walias)
        locus_alias = [self._alias_of(k) for k in loci]
        cells: Dict[Tuple[str, str], float] = {}
        feats: List[str] = []
        for mk in (self.cortex.get_collection_members(f"{walias}:measures") or []):
            meta = self.cortex.get_meta(mk) or {}
            if witness and (meta.get("witness") or "") not in (witness, self._alias_of_safe(witness)):
                continue
            la = meta.get("locus"); fa = meta.get("feature")
            if la is None or fa is None:
                continue
            if fa not in feats:
                feats.append(fa)
            try:
                cells[(la, fa)] = float(meta.get("value"))
            except (TypeError, ValueError):
                pass
        feats.sort()
        grid = [[cells.get((la, fa)) for fa in feats] for la in locus_alias]
        return {"loci": locus_alias, "locus_keys": loci, "features": feats,
                "cells": {f"{la}|{fa}": v for (la, fa), v in cells.items()}, "grid": grid}

    def _alias_of_safe(self, ref: str) -> str:
        k = self._resolve(ref)
        return self._alias_of(k) if k else ref

    def op_matrix(self, work: str = "", witness: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        m = self._matrix(self._alias_of(wk), witness)
        return {"status": "ok", "work": self._alias_of(wk), "witness": witness or None,
                "loci": m["loci"], "features": m["features"], "grid": m["grid"], "cells": m["cells"],
                "feature_titles": {f: self._label(self._resolve(f) or f) for f in m["features"]},
                "locus_titles": {l: self._label(self._resolve(l) or l) for l in m["loci"]}}

    @staticmethod
    def _zscore_columns(grid: List[List[Optional[float]]], nfeat: int) -> List[List[Optional[float]]]:
        """Column-wise z-score so features on different scales are comparable."""
        cols = [[row[j] for row in grid if row[j] is not None] for j in range(nfeat)]
        stats = []
        for c in cols:
            if len(c) >= 2:
                mu = sum(c) / len(c)
                sd = math.sqrt(sum((x - mu) ** 2 for x in c) / len(c)) or 1.0
            else:
                mu, sd = (c[0] if c else 0.0), 1.0
            stats.append((mu, sd))
        out = []
        for row in grid:
            out.append([None if row[j] is None else (row[j] - stats[j][0]) / stats[j][1] for j in range(nfeat)])
        return out

    def _seams(self, walias: str, witness: str = "") -> Dict[str, Any]:
        m = self._matrix(walias, witness)
        loci, feats, grid = m["loci"], m["features"], m["grid"]
        nfeat = len(feats)
        z = self._zscore_columns(grid, nfeat) if nfeat else []
        # adjacent-locus euclidean distance in z-space + the single most-driving feature
        joins = []
        dists = []
        for i in range(len(loci) - 1):
            a, b = z[i], z[i + 1]
            comps = [(feats[j], abs((b[j] - a[j])) ) for j in range(nfeat)
                     if a[j] is not None and b[j] is not None]
            d = math.sqrt(sum(c[1] ** 2 for c in comps)) if comps else 0.0
            drivers = [f for f, _ in sorted(comps, key=lambda c: -c[1])[:3]]
            dists.append(d)
            joins.append({"after": loci[i], "before": loci[i + 1], "distance": round(d, 3),
                          "drivers": drivers})
        # normalize distance to a 0..1 strength
        mx = max(dists) if dists else 1.0
        for j in joins:
            j["strength"] = round(j["distance"] / mx, 3) if mx else 0.0
        # align to the posited seams in the catalog (@seam_after → locus)
        posited = {}
        for sk in (self.cortex.get_collection_members(f"{walias}:seams") or []):
            after = None
            for dst, rel in (self.cortex.get_adjacent_links(sk, "@seam_after") or []):
                after = self._alias_of(dst); break
            if after:
                posited[after] = {"seam": self._alias_of(sk), "title": self._label(sk),
                                  "hyps": [self._alias_of(s) for s, _ in
                                           (self.cortex.get_incoming_links(sk, "@posits_seam") or [])]}
        for j in joins:
            if j["after"] in posited:
                j["posited"] = posited[j["after"]]
        joins_sorted = sorted(joins, key=lambda x: -x["strength"])
        return {"joins": joins, "ranked": joins_sorted, "features": feats, "loci": loci,
                "posited_after": posited}

    def op_seams(self, work: str = "", witness: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        s = self._seams(self._alias_of(wk), witness)
        top = s["ranked"][0] if s["ranked"] else None
        return {"status": "ok", "work": self._alias_of(wk), "witness": witness or None,
                "joins": s["joins"], "ranked": s["ranked"], "primary_seam": top,
                "locus_titles": {l: self._label(self._resolve(l) or l) for l in s["loci"]}}

    def op_compare(self, work: str = "", locus: str = "", witness: str = "") -> Dict[str, Any]:
        """[gen.compare] Inspect ONE locus within the work's feature space: its distance from the
        previous locus, the next locus, and the corpus centroid (all in column-z space, so features
        on different scales are comparable), plus the per-feature contributors to how far it sits from
        the average locus, and where it ranks among all loci by that distance. A single-work, single-
        lens read (the stylometry surface) — e.g. 'does Book X of the Iliad behave unusually within the
        measured feature space?'. A distance is EVIDENCE, not an attribution: it says a locus is
        measurably distinctive, never who wrote it."""
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        walias = self._alias_of(wk)
        m = self._matrix(walias, witness)
        loci, feats, grid = m["loci"], m["features"], m["grid"]
        nfeat = len(feats)
        if not loci or not nfeat:
            return {"error": "no matrix — ingest measurements first"}
        lk = self._resolve(locus if locus.startswith(f"{self.NS}:") else f"{self.NS}:locus:{locus}")
        la = self._alias_of(lk) if lk else None
        if la not in loci:
            return {"error": f"locus '{locus}' is not a measured locus of {walias}"}
        i = loci.index(la)
        z = self._zscore_columns(grid, nfeat)

        def _dist(u, v):
            comps = [(u[j] - v[j]) for j in range(nfeat) if u[j] is not None and v[j] is not None]
            return round(math.sqrt(sum(c * c for c in comps)), 3) if comps else None

        centroid = [0.0] * nfeat                       # column-z mean is ~0 by construction
        tz = z[i]
        # per-feature contribution to the distance-from-average (|z|), most-distinctive first
        contribs = []
        for j in range(nfeat):
            if tz[j] is None:
                continue
            contribs.append({"feature": feats[j], "title": self._label(self._resolve(feats[j]) or feats[j]),
                             "value": grid[i][j], "z": round(tz[j], 3), "deviation": round(abs(tz[j]), 3)})
        contribs.sort(key=lambda c: -c["deviation"])
        # rank every locus by its distance from the centroid, so the target's standing is honest
        cdists = [(loci[t], _dist(z[t], centroid) or 0.0) for t in range(len(loci))]
        ranked = sorted(cdists, key=lambda x: -x[1])
        rank = [t for t, _ in ranked].index(la) + 1
        adj = [d for d in (_dist(z[t], z[t + 1]) for t in range(len(loci) - 1)) if d is not None]
        mean_adj = round(sum(adj) / len(adj), 3) if adj else None

        def _peer(idx):
            if idx < 0 or idx >= len(loci):
                return None
            return {"locus": loci[idx], "title": self._label(self._resolve(loci[idx]) or loci[idx]),
                    "distance": _dist(tz, z[idx])}
        return {"status": "ok", "work": walias, "locus": la, "title": self._label(lk),
                "index": i, "n": len(loci),
                "distance_from_previous": _peer(i - 1),
                "distance_from_next": _peer(i + 1),
                "distance_from_corpus_centroid": _dist(tz, centroid),
                "mean_adjacent_distance": mean_adj,
                "rank_by_distinctiveness": rank, "of": len(loci),
                "feature_contributors": contribs,
                "features": feats,
                "locus_titles": {l: self._label(self._resolve(l) or l) for l in loci}}

    # ── cross-laboratory overlay: many lenses' boundaries on the SAME loci ───────
    def _boundaries(self, loci: List[str], feats: List[str],
                    grid: List[List[Optional[float]]]) -> List[Dict[str, Any]]:
        """Per-gap z-scored adjacent-locus distance over a (sub)set of features + its drivers."""
        nfeat = len(feats)
        z = self._zscore_columns(grid, nfeat) if nfeat else []
        joins = []; dists = []
        for i in range(len(loci) - 1):
            a, b = z[i], z[i + 1]
            comps = [(feats[j], abs(b[j] - a[j])) for j in range(nfeat)
                     if a[j] is not None and b[j] is not None]
            d = math.sqrt(sum(c[1] ** 2 for c in comps)) if comps else 0.0
            drivers = [f for f, _ in sorted(comps, key=lambda c: -c[1])[:3]]
            dists.append(d)
            joins.append({"after": loci[i], "before": loci[i + 1], "distance": round(d, 3), "drivers": drivers})
        mx = max(dists) if dists else 1.0
        for j in joins:
            j["strength"] = round(j["distance"] / mx, 3) if mx else 0.0
        return joins

    def op_cross(self, work: str = "", lenses: str = "", witness: str = "",
                 threshold: str = "0.6") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        walias = self._alias_of(wk)
        m = self._matrix(walias, witness)
        loci, feats, grid = m["loci"], m["features"], m["grid"]
        want = set(x.strip() for x in (lenses or "").split(",") if x.strip()) or None
        lens_of = {f: self._feature_lens(f) for f in feats}
        try:
            TH = float(threshold)
        except (TypeError, ValueError):
            TH = 0.6
        # one lane per lens: its own boundaries over its own feature sub-space
        order = []
        for f in feats:
            L = lens_of[f]
            if L not in order and (want is None or L in want):
                order.append(L)
        lanes = []
        per_gap: Dict[str, Dict[str, float]] = {}
        for L in order:
            cols = [j for j, f in enumerate(feats) if lens_of[f] == L]
            subfeats = [feats[j] for j in cols]
            subgrid = [[row[j] for j in cols] for row in grid]
            b = self._boundaries(loci, subfeats, subgrid)
            top = max(b, key=lambda x: x["strength"]) if b else None
            # decisiveness: does ONE gap dominate, or is the lens flat? (normalised strength always
            # maxes at 1.0, so compare the top RAW distance against the mean of the rest — a lens
            # with no dominant gap ABSTAINS instead of casting a spurious vote.)
            ds = sorted((j["distance"] for j in b), reverse=True)
            rest = ds[1:]
            decis = (ds[0] / (sum(rest) / len(rest))) if (rest and sum(rest) > 0) else (999.0 if ds else 0.0)
            abstains = decis < 1.5
            lanes.append({"lens": L, "features": subfeats, "boundaries": b,
                          "top_gap": (None if abstains else (top["after"] if top else None)),
                          "top_strength": (0.0 if abstains else (top["strength"] if top else 0.0)),
                          "decisiveness": round(decis, 2), "abstains": abstains})
            if not abstains:                             # only a decisive lens votes at a gap
                for j in b:
                    per_gap.setdefault(j["after"], {})[L] = j["strength"]
        # coincidence: a locus-gap where ≥2 lenses find a strong boundary — corroborated provenance
        coincidence = []
        for after, d in per_gap.items():
            strong = sorted([L for L, s in d.items() if s >= TH], key=lambda L: -d[L])
            if len(strong) >= 2:
                coincidence.append({"after": after, "lenses": strong, "count": len(strong),
                                    "score": round(sum(d[L] for L in strong) / max(1, len(order)), 3)})
        coincidence.sort(key=lambda x: (-x["count"], -x["score"]))
        consensus = coincidence[0]["after"] if coincidence else None
        # divergence: a lens that abstains (no decisive boundary) or breaks elsewhere — a held tension
        divergence = []
        for lane in lanes:
            if lane["abstains"]:
                divergence.append({"lens": lane["lens"], "kind": "abstains",
                                   "note": "no decisive boundary — this lens reads the loci as continuous",
                                   "top_gap": None, "top_strength": 0.0})
            elif consensus and lane["top_gap"] != consensus:
                divergence.append({"lens": lane["lens"], "kind": "elsewhere",
                                   "note": "its strongest boundary falls elsewhere than the consensus",
                                   "top_gap": lane["top_gap"], "top_strength": lane["top_strength"]})
        return {"status": "ok", "work": walias, "work_title": self._label(wk),
                "loci": loci, "lenses": lanes, "coincidence": coincidence,
                "divergence": divergence, "consensus_after": consensus, "threshold": TH,
                "locus_titles": {l: self._label(self._resolve(l) or l) for l in loci},
                "lens_count": len(order)}

    # ── the projection (the lab GUI contract) ───────────────────────────────────
    def op_project(self, work: str = "", mode: str = "trajectory", feature: str = "",
                   witness: str = "") -> Dict[str, Any]:
        wk = self._resolve(work if work.startswith(f"{self.NS}:") else f"{self.NS}:work:{work}")
        if not wk:
            return {"error": f"unknown work '{work}'"}
        walias = self._alias_of(wk)
        mode = (mode or "trajectory").strip()
        meta = {"projection": f"projection:{self.NS}:{walias.split(':')[-1]}", "mode": mode,
                "work": walias, "work_title": self._label(wk), "witness": witness or None,
                "projection_version": "0.1"}
        if mode == "matrix":
            return {"meta": meta, **self.op_matrix(work, witness)}
        if mode == "seams":
            return {"meta": meta, **self.op_seams(work, witness)}
        if mode == "layers":
            return {"meta": meta, "layers": self._layers_view(walias)}
        if mode == "hypotheses":
            return {"meta": meta, "hypotheses": self._hyps_view(walias)}
        if mode == "sources":
            return {"meta": meta, "sources": self._sources_view(walias)}
        if mode == "cross":
            return {"meta": meta, **self.op_cross(work, witness=witness)}
        # default: the composition-trajectory hero
        return {"meta": meta, **self._trajectory_view(walias, feature, witness)}

    def _layer_of(self, locus_key: str) -> Optional[str]:
        for dst, rel in (self.cortex.get_adjacent_links(locus_key, "@in_layer") or []):
            return self._alias_of(dst)
        return None

    def _trajectory_view(self, walias: str, feature: str = "", witness: str = "") -> Dict[str, Any]:
        m = self._matrix(walias, witness)
        loci, feats, grid = m["loci"], m["features"], m["grid"]
        seams = self._seams(walias, witness)
        # default the hero to an external-attestation feature (the clean cliff) when one exists
        _attest = next((f for f in feats if "attest" in f), None)
        feat = feature or _attest or (feats[0] if feats else "")
        fidx = feats.index(feat) if feat in feats else -1
        nodes = []
        for i, la in enumerate(loci):
            lk = m["locus_keys"][i]
            val = grid[i][fidx] if fidx >= 0 else None
            nodes.append({"id": la, "label": self._label(lk), "ordinal": i + 1,
                          "layer": self._layer_of(lk), "attested": [self._alias_of(d) for d, _ in
                                    (self.cortex.get_adjacent_links(lk, "@attested_in") or [])],
                          "value": val, "source_atom": la, "layout": {"depth": i, "lane": 0, "rank": i}})
        # seam markers between nodes, carrying strength + which hypotheses posit them
        markers = []
        for j in seams["joins"]:
            markers.append({"after": j["after"], "before": j["before"], "strength": j["strength"],
                            "distance": j["distance"], "drivers": j["drivers"],
                            "posited": j.get("posited")})
        return {"feature": feat, "features": feats, "nodes": nodes, "seams": markers,
                "layers": self._layers_view(walias),
                "hypotheses": self._hyps_view(walias)}

    def _layers_view(self, walias: str) -> List[Dict[str, Any]]:
        out = []
        for lk in (self.cortex.get_collection_members(f"{walias}:layers") or []):
            contains = [self._alias_of(s) for s, _ in (self.cortex.get_incoming_links(lk, "@in_layer") or [])]
            out.append({"id": self._alias_of(lk), "title": self._label(lk),
                        "desc": self.cortex.get_chunk(lk) or "", "contains": contains,
                        "source_atom": self._alias_of(lk)})
        return out

    def _hyps_view(self, walias: str) -> List[Dict[str, Any]]:
        out = []
        for hk in (self.cortex.get_collection_members(f"{walias}:hyps") or []):
            seams = [self._alias_of(d) for d, _ in (self.cortex.get_adjacent_links(hk, "@posits_seam") or [])]
            seam_after = []
            for sk_alias in seams:
                sk = self._resolve(sk_alias)
                for dst, _ in (self.cortex.get_adjacent_links(sk, "@seam_after") or []):
                    seam_after.append(self._alias_of(dst))
            supports = [self._alias_of(s) for s, _ in (self.cortex.get_incoming_links(hk, "@supports_hyp") or [])]
            contests = [self._alias_of(s) for s, _ in (self.cortex.get_incoming_links(hk, "@contests_hyp") or [])]
            out.append({"id": self._alias_of(hk), "title": self._label(hk),
                        "desc": self.cortex.get_chunk(hk) or "", "posits_seams": seams,
                        "seam_after": seam_after, "supports": supports, "contests": contests,
                        "tension": bool(supports and contests), "source_atom": self._alias_of(hk)})
        return out

    def _sources_view(self, walias: str) -> List[Dict[str, Any]]:
        out = []
        for sk in (self.cortex.get_collection_members(f"{self.NS}:sources") or []):
            meta = self.cortex.get_meta(sk) or {}
            supports = [self._alias_of(d) for d, _ in (self.cortex.get_adjacent_links(sk, "@supports_hyp") or [])]
            contests = [self._alias_of(d) for d, _ in (self.cortex.get_adjacent_links(sk, "@contests_hyp") or [])]
            # only sources touching THIS work's hypotheses
            work_hyps = set(self._alias_of(h) for h in (self.cortex.get_collection_members(f"{walias}:hyps") or []))
            if not (set(supports) | set(contests)) & work_hyps and work_hyps:
                continue
            out.append({"id": self._alias_of(sk), "title": meta.get("title") or self._label(sk),
                        "author": meta.get("author", ""), "year": meta.get("year", ""),
                        "locator": meta.get("locator", ""), "supports": supports, "contests": contests,
                        "source_atom": self._alias_of(sk)})
        return out

    def op_trace(self, id: str = "") -> Dict[str, Any]:
        k = self._resolve(id)
        if not k:
            return {"error": f"unknown object '{id}'"}
        meta = self.cortex.get_meta(k) or {}
        return {"status": "ok", "id": self._alias_of(k), "key": k, "kind": meta.get("node_kind"),
                "title": self._label(k), "content": self.cortex.get_chunk(k) or "", "meta": meta,
                "links": [{"to": self._alias_of(d), "rel": r}
                          for d, r in (self.cortex.get_adjacent_links(k) or [])]}
