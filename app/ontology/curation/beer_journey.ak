# beer_journey.ak — atoms for the AUTHORED curation "Beer's Journey".
# Third installment of the exhibition series 「夢追い人の系譜」 (A Genealogy of Dream-Chasers).
#
# "労働を癒す夢のビバレッジ、ビールの旅" — beer as the drink that soothes labour. Like the
# printing story it is a TWO-BRANCH tree: an ancient common stem, then a modern fork.
#   STEM — Mesopotamia → Egypt → the medieval monasteries keep brewing alive.
#   ALE  — the old warm (top-fermented) soul: the Benelux abbeys, England's porter/IPA,
#          Poland's smoked grodziskie.
#   LAGER — the modern cold (bottom-fermented) clarity: Vienna's amber lager and Germany's
#          Bavarian lager. The 19th-century split of ale vs lager.
# The stem and the two branches are cut into the graph with `chrono:before` (earlier →
# later), all edges intra-pack so the demo stays self-contained. The reading ORDER is
# authored in the CSL. `beer:` namespace is defined (nsdef:beer). Editorial text: MIT.

# ── The ancient stem ─────────────────────────────────────────────────────────
def "beer:origin:mesopotamia" "Mesopotamia (Sumer, c.4000 BCE onward) — beer older than written history; the Hymn to Ninkasi, goddess of brewing, is both prayer and recipe. Barley bread turned to drink: the first civilising cup."
def "beer:origin:egypt"       "Ancient Egypt — beer as daily bread and wage: the builders of the pyramids and temples were paid and fed in it. Thick, nourishing, and holy — the labourer's sustenance and the offering of the dead."
def "beer:era:monastery"      "The medieval monasteries (Europe, c.6th–15th c.) — through the Middle Ages the abbeys keep brewing alive, refine it, and add hops for keeping. The common European stem from which the modern branches — ale and lager — will fork."

# ── ALE branch — the old warm (top-fermented) soul ───────────────────────────
def "beer:ale:benelux"        "The Benelux (Belgium) — Trappist and abbey ales still brewed by monks, and the wild-fermented lambics of the Senne valley. Ale as devotion and terroir: patience, place, and prayer in a warm-fermented glass."
def "beer:ale:england"        "England — London porter, the dark strong ale of the 18th-century worker, and the pale ales sent to India (IPA). Top-fermented and characterful; the pub becomes the labourer's hearth."
def "beer:ale:poland"         "Poland — grodziskie (Grätzer), the oak-smoked wheat ale once called 'Polish Champagne'. The northern plains keep their own bright, smoky, top-fermented thirst-quencher."

# ── LAGER branch — the modern cold (bottom-fermented) clarity ─────────────────
def "beer:lager:vienna"       "Vienna (Austria, 1841) — Anton Dreher's Vienna lager and its amber malt; cold, bottom-fermented, clear and keeping. The modern branch begins: beer turns from cloudy craft to bright science."
def "beer:lager:germany"      "Germany / Bavaria — the Reinheitsgebot (1516) and the great lager tradition; cold cellars, patient bottom fermentation, the Pilsner-bright pour and the beer hall. The lager becomes the world's beer."

# ── The stem + the modern fork (chrono:before = earlier → later, intra-pack) ──
ln beer:origin:mesopotamia beer:origin:egypt   chrono:before
ln beer:origin:egypt       beer:era:monastery  chrono:before
ln beer:era:monastery      beer:ale:benelux    chrono:before
ln beer:ale:benelux        beer:ale:england    chrono:before
ln beer:ale:england        beer:ale:poland     chrono:before
ln beer:era:monastery      beer:lager:vienna   chrono:before
ln beer:lager:vienna       beer:lager:germany  chrono:before

# ── The curated set (the CSL orders these by ids=) ───────────────────────────
set.add name="curation:demo:beer_journey" id="beer:origin:mesopotamia"
set.add name="curation:demo:beer_journey" id="beer:origin:egypt"
set.add name="curation:demo:beer_journey" id="beer:era:monastery"
set.add name="curation:demo:beer_journey" id="beer:ale:benelux"
set.add name="curation:demo:beer_journey" id="beer:ale:england"
set.add name="curation:demo:beer_journey" id="beer:ale:poland"
set.add name="curation:demo:beer_journey" id="beer:lager:vienna"
set.add name="curation:demo:beer_journey" id="beer:lager:germany"
