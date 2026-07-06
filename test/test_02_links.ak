# =============================================================================
# AKASHA Test Suite 02 — Links: ln / ln.ls / ln.+ / ln.rm / tree / exp
# =============================================================================
# HOW TO RUN:  run test/test_02_links.ak
# VERIFY (interactively after job is DONE):
#   ln.ls t02:node:sun           → orbits links to earth and mars
#   ln.ls t02:node:earth         → @has_moon link to luna; sys:causes from sun
#   ln.ls t02:node:phobos        → @has_moon only (@test_only link was removed)
#   tree t02:node:sun 3          → branching solar system tree
#   exp ns=t02                   → BFS neighborhood of all t02 atoms
#   al.find t02:%                → all t02 aliases
# =============================================================================

# ── 1. Build a small solar system graph ──────────────────────────────────────
w "Sol — the star at the centre of our planetary system."
al $0 "t02:node:sun"

w "Earth — third planet from Sol; home of humanity."
al $0 "t02:node:earth"

w "Luna — Earth's natural satellite."
al $0 "t02:node:luna"

w "Mars — fourth planet; the red planet."
al $0 "t02:node:mars"

w "Phobos — larger of Mars's two moons."
al $0 "t02:node:phobos"

# ── 2. Create directed links ──────────────────────────────────────────────────
# rel without @ or namespace → auto-prefixed as @orbits
ln t02:node:earth t02:node:sun orbits
ln t02:node:mars  t02:node:sun orbits

# rel with @ already present → unchanged
ln t02:node:luna   t02:node:earth @has_moon
ln t02:node:phobos t02:node:mars  @has_moon

# rel with sys: namespace → unchanged
ln t02:node:sun t02:node:earth sys:causes

# ── 3. Reinforce a link ────────────────────────────────────────────────────────
ln.+ t02:node:earth t02:node:sun orbits
ln.+ t02:node:earth t02:node:sun orbits

# ── 4. Test ln.rm — write a link then immediately remove it ──────────────────
ln  t02:node:phobos t02:node:mars @test_only
ln.rm t02:node:phobos t02:node:mars @test_only
# VERIFY: ln.ls t02:node:phobos should show @has_moon only

# ── 5. Set structural metadata ────────────────────────────────────────────────
meta t02:node:sun   type "star"
meta t02:node:earth type "planet"
meta t02:node:luna  type "moon"
meta t02:node:mars  type "planet"

# ── 6. Add all to a test set ──────────────────────────────────────────────────
s.add test:02:links t02:node:sun
s.add test:02:links t02:node:earth
s.add test:02:links t02:node:luna
s.add test:02:links t02:node:mars
s.add test:02:links t02:node:phobos
