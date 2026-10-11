"""
Stylometry Concept Model — textual stratification by measurement (a SUBSET of Genealogy).

`sty` is the operator layer of a *文献測定学* (stylometry) laboratory: it treats a single text as an
ordered sequence of measurable loci (books / chapters / sections), holds a feature × locus MATRIX of
stylometric measurements, and reads the discontinuities in that matrix as candidate composition
seams (成立層境界) — the joins between authorial strata. Competing scholarly hypotheses about where
the seams fall, and the published sources that support or contest them, are first-class and carry
their tension unresolved.

**Stylometry is a proper SUBSET of the Genealogy model** (`gen`, app/concepts/gen.py):
genealogy restricted to the *single stylometric lens*. `StyConcept` subclasses `GenConcept` and
reuses its engine verbatim; it only NARROWS the surface — it drops the cross-lens overlay
(`gen.cross`), the cross-witness/work alignment (`gen.align` / `gen.alignment`), and the corpus
source-stemma (`gen.genealogy`), which are genealogy's superset machinery. What remains is
single-work seam detection through one lens. The two models share nothing but the engine: stylometry
mints atoms under the `sty:` namespace (`NS = "sty"`), genealogy under `gen:`.

  work ── @next_locus ─▶ locus … locus            the reading order (the composition trajectory)
  measure ─ @of_locus ▶ locus ; ─ @of_feature ▶ feature     one matrix cell  (io.ingest target)
  seam ── @seam_after ─▶ locus                    a boundary that falls AFTER this locus
  hyp  ── @posits_seam ▶ seam ; @groups_layer ▶ layer       a stratification hypothesis
  source ─ @supports_hyp / @contests_hyp ▶ hyp    the evidence, with its tension

The DURABLE catalog (work, witnesses, loci, features, layers, seams, hypotheses, sources) is
authored as an `.ak` pack (app/ontology/base3/stylometry.ak). The RUNTIME matrix — the actual measured
values — is streamed in with `io.ingest model=sty into=<work> path=<matrix.jsonl>` (each record a
{locus, feature, value, witness} cell). `sty.matrix` returns the grid, `sty.seams` reads where the
joins stand, `sty.project` casts the 成立トラジェクトリ for the Archives lab. Degradation-first:
seam detection is deterministic stdlib (z-scored adjacent-locus distance); a connected model can
sharpen the SAME surface without touching the pipeline.
"""

from typing import Any, Dict

from app.concepts.gen import GenConcept

_W, _R = "record", "read"


class StyConcept(GenConcept):
    """Stylometry / textual-stratification operators — the single-lens SUBSET of Genealogy.

    Inherits the whole engine from GenConcept; overrides only the namespace, the ingest model id,
    and the exposed method surface (single-work seam detection, no cross-lens / alignment / stemma).
    """

    CONCEPT_PREFIX = "sty"
    NS = "sty"

    # io.ingest model=sty into=<work>: raw measurement rows → matrix cells. locus+feature+value
    # are required; witness is preferred (which recension the value was measured on).
    IMPORT_SCHEMA = {
        "model": "sty", "requires": ["locus", "feature", "value"], "prefers": ["witness", "unit"],
        "min_nodes": 1,
        "description": "Stylometric feature×locus measurements → matrix cells. Each record is one "
                       "{locus, feature, value, [witness]} cell. into=<work id/alias>.",
    }

    # The stylometry surface = the single-lens subset. The genealogy superset adds cross / align /
    # alignment / genealogy (see gen.py); those op_ methods are INHERITED but deliberately NOT routed
    # here, so `sty.*` stays a clean single-work-seam vocabulary.
    CONCEPT_METHODS = {
        "work":     {"op": "op_work", "action": _W, "cli": "sty.work", "args": ["id"],
                     "desc": "Mint/open a work under study: sty.work id=<slug> [title=\"…\"] [lang=pali] [kind=stratified]"},
        "witness":  {"op": "op_witness", "action": _W, "cli": "sty.witness", "args": ["work", "id"],
                     "desc": "Add a witness/recension to a work: sty.witness work=<w> id=<slug> [title=] [lang=]"},
        "locus":    {"op": "op_locus", "action": _W, "cli": "sty.locus", "args": ["work", "id"],
                     "desc": "Add an ordered locus (book/chapter): sty.locus work=<w> id=<slug> [title=] "
                             "[after=<locus>] [layer=<layer>] [attested=<witness,witness>]"},
        "feature":  {"op": "op_feature", "action": _W, "cli": "sty.feature", "args": ["id"],
                     "desc": "Define a stylometric feature: sty.feature id=<slug> [title=] [desc=] [higher=]"},
        "layer":    {"op": "op_layer", "action": _W, "cli": "sty.layer", "args": ["work", "id"],
                     "desc": "Define a composition stratum: sty.layer work=<w> id=<slug> [title=] [desc=]"},
        "seam":     {"op": "op_seam", "action": _W, "cli": "sty.seam", "args": ["work", "id", "after"],
                     "desc": "Posit a composition seam AFTER a locus: sty.seam work=<w> id=<slug> after=<locus> [desc=]"},
        "hyp":      {"op": "op_hyp", "action": _W, "cli": "sty.hyp", "args": ["work", "id"],
                     "desc": "Add a stratification hypothesis: sty.hyp work=<w> id=<slug> [title=] [desc=] "
                             "[seams=<seam,seam>] [layers=<layer,layer>]"},
        "source":   {"op": "op_source", "action": _W, "cli": "sty.source", "args": ["id"],
                     "desc": "Add a published source: sty.source id=<slug> [title=] [author=] [year=] "
                             "[supports=<hyp>] [contests=<hyp>] [locator=]"},
        "measure":  {"op": "op_measure", "action": _W, "cli": "sty.measure", "args": ["work", "locus", "feature", "value"],
                     "desc": "Record ONE matrix cell (CLI-native): sty.measure work=<w> locus=<l> feature=<f> value=<x> [witness=]"},
        "ingest":   {"op": "op_ingest", "action": _W, "cli": "sty.ingest", "args": ["work"],
                     "desc": "Batch-ingest matrix cells (RPC form): sty.ingest work=<w> records=<json>"},
        "matrix":   {"op": "op_matrix", "action": _R, "cli": "sty.matrix", "args": ["work"],
                     "desc": "The feature×locus measurement grid: sty.matrix work=<w> [witness=]"},
        "seams":    {"op": "op_seams", "action": _R, "cli": "sty.seams", "args": ["work"],
                     "desc": "Where the joins stand — z-scored adjacent-locus distance + the features "
                             "driving each, aligned to the posited seams: sty.seams work=<w> [witness=]"},
        "compare":  {"op": "op_compare", "action": _R, "cli": "sty.compare", "args": ["work", "locus"],
                     "desc": "Inspect ONE locus in the feature space — distance from prev / next / corpus "
                             "centroid + the features driving it + its distinctiveness rank (a distance is "
                             "evidence, not an attribution): sty.compare work=<w> locus=<l> [witness=]"},
        "project":  {"op": "op_project", "action": _R, "cli": "sty.project", "args": ["work"],
                     "desc": "Cast the composition-trajectory projection for the lab GUI: "
                             "sty.project work=<w> [mode=trajectory|matrix|seams|hypotheses|layers|sources]"},
        "trace":    {"op": "op_trace", "action": _R, "cli": "sty.trace", "args": ["id"],
                     "desc": "Trace a projection object back to its source atom: sty.trace id=<alias/key>"},
    }
