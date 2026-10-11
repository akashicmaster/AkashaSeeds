# ── Ontology corrections ─────────────────────────────────────────────────────────────────
# Applied by the kernel AFTER all packs load, on every install that has not yet applied them
# (content-hash gated). A `def` here RE-AUTHORS an atom: ak defs dispatch scope=universal, so a
# CHANGED definition force-rebinds its alias to the corrected atom and soft-retires the stale one
# (see _handle_define) — fixing an already-loaded nucleus.db WITHOUT a data wipe, no `rm`, no
# Linux. Idempotent: an already-correct definition is a content-addressed no-op.
#
# To ship a fix for a mis-authored release atom: add one `def "alias" "corrected description"`
# line below and regenerate the seeds. That's the whole procedure.

# 2026-08-14 — the Ayurveda gloss shipped as katakana (アーユルヴェーダ); correct it to Devanagari
# so the Oriental Archives (and every surface reading the graph) shows आयुर्वेद, not Japanese.
def "tradition:ayurveda" "Ayurvedic dietary science (आयुर्वेद): six tastes (rasa), potency (virya), and dosha balance."
