# Site analytics anchors (F17) — outward web properties of THIS deployment: pages that are
# not concept atoms themselves (a landing page, the portal front). A pulse beacon fired from
# such a page resolves its `concept` to one of these anchors, so the traffic is recorded
# concept-side like everything else. Autoloaded (base1, every tier); content-addressed, so a
# re-extract over an existing install is a no-op, and a hand-made ontology/user/site.ak with
# the same text yields the same atom.
def "site:github_landing" "The AkashaSeeds GitHub Pages landing page."
def "site:archives_home" "The archives portal front page."

# F18 — one anchor per archives SHELL page (rooms / entrances that are not themselves a concept
# atom). A pulse beacon fired on load from such a page resolves its `concept` to one of these.
def "site:archives_hall" "The archives reading-hall entrance."
def "site:archives_field" "The archives field-gallery entrance."
def "site:archives_worldmap" "The archives world-map room."
def "site:archives_cosmos" "The archives cosmos room (the living archive)."
def "site:archives_explore" "The archives explore room."
def "site:archives_reference" "The archives reference room."
def "site:archives_curation" "The archives curation-gallery room."
def "site:archives_exhibit" "The archives exhibition room."
def "site:archives_labo" "The archives thought-experiment laboratories entrance."
def "site:archives_consensus" "The archives Form-a-Consensus deliberation view."
def "site:oriental_home" "The Oriental Archives — the special reading room of Eastern wisdom."
def "site:oriental_medicine" "The Oriental Archives — the lineage of Eastern medicine."
def "site:oriental_ayurveda" "The Oriental Archives — Ayurveda (आयुर्वेद)."
def "site:ancient_home" "The Ancient Civilizations Archives — an antique world map of the ancient cultures, by region."
def "site:labo_stylometry" "The Stylometry Laboratory — tracing a single text's composition seams by measurement (the Milindapañha)."
def "site:labo_genealogy" "The Genealogy Laboratory — where traditions come from: cross-provenance over many lenses (the Ayurvedic saṃhitās)."
def "site:archives_live" "Live Telemetry — dynamic world facts (disasters, earthquakes, the ISS) mapped to atoms and crossed on shared space·time."

# F18 — the Akashic Kitchen virtual-host suite (rooms of the food/drink surface).
def "site:kitchen_home" "The Akashic Kitchen entrance (a door for food)."
def "site:kitchen_cheese" "The Akashic Kitchen cheese room."
def "site:kitchen_larder" "The Akashic Kitchen larder room."
def "site:kitchen_ingredient" "The Akashic Kitchen ingredient room."
def "site:kitchen_pairing" "The Akashic Kitchen pairing room."
def "site:kitchen_flavors" "The Akashic Kitchen world-flavors hub."
def "site:kitchen_recipes" "The Akashic Kitchen recipes room."
def "site:kitchen_regions" "The Akashic Kitchen world-regions room."

def "site:archives_starchart" "The archives star-chart room — the celestial sphere of bright stars."
def "site:archives_periodic" "The archives periodic-table room — the elements."

# F27-6 — the remaining archives SHELL pages that were still uninstrumented: the station front,
# the academy entrance, and the applied- / liberal-arts halls. One anchor each so a pulse beacon
# fired on load resolves concept-side like every other room.
def "site:archives_station" "The archives station page — the AI News Station front."
def "site:archives_academy" "The archives academy entrance — the schools/disciplines hub."
def "site:archives_applied" "The archives applied-arts hall."
def "site:archives_liberal" "The archives liberal-arts hall."
