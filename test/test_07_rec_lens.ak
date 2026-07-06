# =============================================================================
# AKASHA Test Suite 07 — Records, Lens & Structured Analysis
# =============================================================================
# Covers: rec.new / rec.set / rec.idx / rec.get / rec.ls / rec.sum / rec.rm
#         rec.table / lens / lens.flatten / quadrant.plot
#         cross / cross.axes / ref.set / ref.get / table.*
#
# HOW TO RUN:  run test/test_07_rec_lens.ak
#
# VERIFY (interactively after job is DONE):
#   rec.ls type=fruit            → apple, banana, mango (cherry was removed)
#   rec.ls in_set=set:rec:fruit  → same 3 records
#   rec.sum attr=sweetness in_set=set:rec:fruit   → numeric total
#   rec.table in_set=set:rec:fruit                → formatted table of fruit records
#   lens src=set:rec:fruit       → scan and list importable concept models
#   quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness → ASCII scatter plot
#   table.ls table=t07_products  → rows from the structured table
#   cross.axes                   → axes available across loaded concept models
# =============================================================================

# ── 1. Create fruit records with typed attributes ─────────────────────────────
rec.new type=fruit content="Apple" color=red sweetness=6 acidity=7
al $0 "t07:rec:apple"
rec.idx t07:rec:apple set:rec:fruit

rec.new type=fruit content="Banana" color=yellow sweetness=8 acidity=2
al $0 "t07:rec:banana"
rec.idx t07:rec:banana set:rec:fruit

rec.new type=fruit content="Mango" color=orange sweetness=9 acidity=4
al $0 "t07:rec:mango"
rec.idx t07:rec:mango set:rec:fruit

rec.new type=fruit content="Cherry" color=red sweetness=7 acidity=6
al $0 "t07:rec:cherry"
rec.idx t07:rec:cherry set:rec:fruit

# ── 2. rec.set — update an attribute after creation ───────────────────────────
rec.set t07:rec:apple acidity 8
# Apple acidity corrected to 8.

# ── 3. rec.get — read a single record with all attributes ─────────────────────
rec.get t07:rec:banana
# Result captured in job log: shows content, color, sweetness, acidity.

# ── 4. rec.ls — list by type and by set ───────────────────────────────────────
rec.ls type=fruit
rec.ls in_set=set:rec:fruit

# ── 5. rec.rm — delete a record ───────────────────────────────────────────────
rec.rm t07:rec:cherry
# VERIFY: rec.ls type=fruit should now show 3 records (no cherry).

# ── 6. rec.sum — aggregate a numeric attribute ───────────────────────────────
rec.sum attr=sweetness in_set=set:rec:fruit
# Returns sum of sweetness across the 3 remaining fruit records.

# ── 7. rec.table — formatted table view ──────────────────────────────────────
rec.table in_set=set:rec:fruit
# Renders all records in the set as an aligned table.

# ── 8. ref.set / ref.get — typed context variables ───────────────────────────
ref.set who t07:rec:apple
ref.get who
# ref.get returns the currently bound atom for the "who" dimension.

# ── 9. lens — scan a set for importable concept model targets ─────────────────
lens src=set:rec:fruit
# Lists concept models whose schema can be satisfied by these rec atoms.
# Stores scan results in session context for lens.flatten.

lens.flatten into=fruit_snap
# Creates rec atoms in set:fruit_snap, one per scanned node.
# VERIFY: rec.ls in_set=fruit_snap  →  3 snapshot records

# ── 10. quadrant.plot — 4-quadrant ASCII scatter plot ────────────────────────
quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness
# Plots the 3 fruits as points. High-sweetness / high-acidity → top-right quadrant.

# ── 11. cross.axes — enumerate all available cross-concept axes ───────────────
cross.axes
# Lists the axes that have been registered by concept models.

# ── 12. table.* — structured table (schema-first, flat rows) ─────────────────
table.new name=t07_products cols="name:text,price:float,stock:int"
table.row.add table=t07_products name=Widget price=9.99  stock=42
table.row.add table=t07_products name=Gadget price=24.50 stock=7
table.row.add table=t07_products name=Doohickey price=3.49 stock=120
table.ls table=t07_products
# VERIFY: table.ls shows 3 rows with correct column values.

# ── 13. Register test set ─────────────────────────────────────────────────────
s.add test:07:rec t07:rec:apple
s.add test:07:rec t07:rec:banana
s.add test:07:rec t07:rec:mango
