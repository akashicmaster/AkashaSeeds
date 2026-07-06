# =============================================================================
# AKASHA Test Suite 03 — Sets: s.add / s.rm / s.ls / s.clear / s.op
# =============================================================================
# HOW TO RUN:  run test/test_03_sets.ak
# VERIFY (run these interactively after job is DONE):
#   s.ls test:03:fruits           → apple, banana, cherry
#   s.ls test:03:vegetables       → carrot, broccoli, cherry (cherry in both)
#   s.ls test:03:union            → 5 members (union of fruits+vegetables)
#   s.ls test:03:intersection     → 1 member (cherry — in both)
#   s.ls test:03:diff             → fruits minus vegetables
#   s.ls test:03:mutable          → should be empty (cleared) or 1 item
# =============================================================================

# ── 1. Create atoms for fruits set ───────────────────────────────────────────
w "Apple — a round fruit of the rose family."
al $0 "t03:item:apple"

w "Banana — a long curved fruit with yellow skin."
al $0 "t03:item:banana"

w "Cherry — a small round stone fruit, red or black."
al $0 "t03:item:cherry"

# ── 2. Create atoms for vegetables set ───────────────────────────────────────
w "Carrot — a tapering orange root vegetable."
al $0 "t03:item:carrot"

w "Broccoli — a green vegetable of the cabbage family."
al $0 "t03:item:broccoli"

# ── 3. Populate sets ─────────────────────────────────────────────────────────
s.add test:03:fruits t03:item:apple
s.add test:03:fruits t03:item:banana
s.add test:03:fruits t03:item:cherry

s.add test:03:vegetables t03:item:carrot
s.add test:03:vegetables t03:item:broccoli
s.add test:03:vegetables t03:item:cherry

# ── 4. Set operations ─────────────────────────────────────────────────────────
s.op union test:03:union         test:03:fruits test:03:vegetables
s.op isect test:03:intersection  test:03:fruits test:03:vegetables
s.op diff  test:03:diff          test:03:fruits test:03:vegetables

# ── 5. Test s.rm and s.clear via a mutable set ───────────────────────────────
s.add test:03:mutable t03:item:apple
s.add test:03:mutable t03:item:banana
s.rm  test:03:mutable t03:item:apple
# At this point test:03:mutable contains only banana

s.add test:03:clearme t03:item:carrot
s.add test:03:clearme t03:item:broccoli
s.clear test:03:clearme
# At this point test:03:clearme is empty
