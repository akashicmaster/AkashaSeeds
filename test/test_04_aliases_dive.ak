# =============================================================================
# AKASHA Test Suite 04 — Aliases & Dive: al / al.ls / al.find / al.rm / look
# =============================================================================
# HOW TO RUN:  run test/test_04_aliases_dive.ak
# VERIFY (interactively after job is DONE):
#   al.find t04:%               → all t04 aliases (t04:discard should be absent)
#   al.find %philosophy%        → finds t04:hub:philosophy
#   look t04:concept:dialectics → dive view: content + signposts
#   d t04:hub:philosophy        → same as look (short alias)
#   out t04:concept:dialectics  → macro view zooming out
#   ln.ls t04:hub:philosophy    → outgoing sys:contains links to four concepts
# =============================================================================

# ── 1. Create a philosophy knowledge cluster ──────────────────────────────────
def "t04:hub:philosophy"

w "Dialectics — a method of reasoning through contradictions: thesis vs antithesis resolving into synthesis."
al $0 "t04:concept:dialectics"

w "Empiricism — the theory that knowledge comes primarily from sensory experience."
al $0 "t04:concept:empiricism"

w "Rationalism — the view that reason is the chief source and test of knowledge."
al $0 "t04:concept:rationalism"

w "Pragmatism — a philosophical tradition that evaluates theories by their practical consequences."
al $0 "t04:concept:pragmatism"

# ── 2. Link hub to concepts ───────────────────────────────────────────────────
ln t04:hub:philosophy t04:concept:dialectics  sys:contains
ln t04:hub:philosophy t04:concept:empiricism  sys:contains
ln t04:hub:philosophy t04:concept:rationalism sys:contains
ln t04:hub:philosophy t04:concept:pragmatism  sys:contains

# ── 3. Semantic links between concepts ────────────────────────────────────────
ln t04:concept:empiricism t04:concept:rationalism sys:associated_with
ln t04:concept:dialectics t04:concept:pragmatism  sys:associated_with

# ── 4. Alternative alias for the hub ─────────────────────────────────────────
w "Philosophy overview node — links to the major epistemological traditions."
al $0 "t04:overview"
ln t04:hub:philosophy t04:overview sys:associated_with

# ── 5. Test al.rm — add a transient alias then remove it ─────────────────────
al t04:concept:dialectics "t04:discard"
al.rm "t04:discard"
# VERIFY: al.find t04:% should not include "t04:discard"

# ── 6. In-script al.find call (result captured in job log) ───────────────────
al.find "t04:%"
# Job log should show all t04:* aliases found so far.

# ── 7. Add all to test set ────────────────────────────────────────────────────
s.add test:04:aliases t04:hub:philosophy
s.add test:04:aliases t04:concept:dialectics
s.add test:04:aliases t04:concept:empiricism
s.add test:04:aliases t04:concept:rationalism
s.add test:04:aliases t04:concept:pragmatism
