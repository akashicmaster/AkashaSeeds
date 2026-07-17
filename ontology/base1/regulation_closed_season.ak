# Akasha ontology — regulated closed seasons (禁漁 / 禁猟).
# A legal closure that constrains WILD availability. Dates are jurisdiction-
# specific and region-relative, so they are NOT materialised per food — only
# the fact that a species is subject to a closure is recorded. Farmed/cultured
# stock is unaffected (source:farmed available year-round). Base pack.

def "regulation:closed_season" "A legally regulated period when taking a species is prohibited; protects spawning/breeding or stocks. Dates vary by jurisdiction."
def "regulation:fishing_ban" "禁漁期間 — closed fishing season / spawning protection."
def "regulation:hunting_ban" "禁猟期間 — closed hunting season."
ln regulation:fishing_ban regulation:closed_season thesaurus:related
ln regulation:hunting_ban regulation:closed_season thesaurus:related
# the closure constrains the wild catch, not farmed stock
ln regulation:closed_season source:wild thesaurus:related

# ── subject to a fishing ban (禁漁) ──
ln ingred:seafood:eel regulation:fishing_ban regulation:subject_to
ln ingred:seafood:sturgeon regulation:fishing_ban regulation:subject_to
ln ingred:seafood:sea_urchin regulation:fishing_ban regulation:subject_to
ln ingred:seafood:salmon regulation:fishing_ban regulation:subject_to
ln ingred:seafood:tuna regulation:fishing_ban regulation:subject_to
ln ingred:seafood:trout regulation:fishing_ban regulation:subject_to

# ── subject to a hunting ban (禁猟) — open season typically autumn/winter ──
ln ingred:meat:venison regulation:hunting_ban regulation:subject_to
ln ingred:meat:venison season:autumn in_season   # typical open (huntable) season
ln ingred:meat:venison season:winter in_season
