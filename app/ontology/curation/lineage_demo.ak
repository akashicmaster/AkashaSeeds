# lineage_demo.ak — auto path-discovery example for the curation concept model.
#
# A patriline through time. Two relation axes run over the same atoms:
#   chrono:before   — the time axis  (earlier → later)
#   lineage:begat   — the bloodline  (father → son)
#
# Curation's DERIVED mode intersects the two: an edge survives only where a is
# BOTH earlier-in-time AND begat the next — so the surviving chain is the
# succession narrative. `myth:gaia` is time-early but off this patriline (no
# begat edge into the chain), so the intersection correctly leaves her off the path.
#
# After this pack loads, discover the narrative with:
#   curate "Succession of the Sky" set=curation:demo:lineage rels=chrono:before,lineage:begat
#   narrate <curation_id>
#
# Figures: public-domain Greek mythology. Editorial text: MIT.

# ── The atoms ────────────────────────────────────────────────────────────────
def "myth:gaia"    "Primordial earth — contemporary of the primordial sky, but not on this father-to-son patriline"
def "myth:ouranos" "Primordial sky; father of the Titans — the head of the succession"
def "myth:kronos"  "Titan; son of Ouranos; father of the Olympian gods"
def "myth:zeus"    "King of the Olympians; son of Kronos; father of Apollo"
def "myth:apollo"  "Olympian of light and prophecy; son of Zeus"

# ── The time axis (chrono:before) ────────────────────────────────────────────
ln myth:gaia    myth:ouranos chrono:before
ln myth:ouranos myth:kronos  chrono:before
ln myth:kronos  myth:zeus    chrono:before
ln myth:zeus    myth:apollo  chrono:before

# ── The bloodline axis (lineage:begat) ───────────────────────────────────────
# Note: no begat edge from gaia into the patriline — she is off the followed line.
ln myth:ouranos myth:kronos  lineage:begat
ln myth:kronos  myth:zeus    lineage:begat
ln myth:zeus    myth:apollo  lineage:begat

# ── The target set the curation interprets ───────────────────────────────────
set.add name="curation:demo:lineage" id="myth:gaia"
set.add name="curation:demo:lineage" id="myth:ouranos"
set.add name="curation:demo:lineage" id="myth:kronos"
set.add name="curation:demo:lineage" id="myth:zeus"
set.add name="curation:demo:lineage" id="myth:apollo"
