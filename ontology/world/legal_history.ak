# Akasha ontology (world pack) — legal history.
# The milestones of law across time, chaining the rich existing law:tradition:/
# law:code:/law:concept: layer to hist:period. A-tier.

def "legalhist:milestone" "A milestone in the history of law (法史の画期)."
def "legalhist:hammurabi_code" "Babylon's carved law code (~1754 BCE) — 'an eye for an eye'."
ln legalhist:hammurabi_code legalhist:milestone thesaurus:related
ln legalhist:hammurabi_code hist:period:bronze_age legalhist:dates_from
ln legalhist:hammurabi_code law:code:hammurabi thesaurus:related
ln legalhist:hammurabi_code hist:babylonia thesaurus:related
def "legalhist:mosaic_law" "The Torah's covenant law — the Ten Commandments."
ln legalhist:mosaic_law legalhist:milestone thesaurus:related
ln legalhist:mosaic_law hist:period:iron_age legalhist:dates_from
ln legalhist:hammurabi_code legalhist:mosaic_law chrono:before
ln legalhist:mosaic_law religion:judaism thesaurus:related
def "legalhist:twelve_tables" "Rome's first written law (451 BCE) — the root of Western jurisprudence."
ln legalhist:twelve_tables legalhist:milestone thesaurus:related
ln legalhist:twelve_tables hist:period:classical_antiquity legalhist:dates_from
ln legalhist:mosaic_law legalhist:twelve_tables chrono:before
ln legalhist:twelve_tables hist:roman_empire thesaurus:related
def "legalhist:justinian_code" "The Corpus Juris Civilis (529 CE) — the foundation of civil-law tradition."
ln legalhist:justinian_code legalhist:milestone thesaurus:related
ln legalhist:justinian_code hist:period:late_antiquity legalhist:dates_from
ln legalhist:twelve_tables legalhist:justinian_code chrono:before
ln legalhist:justinian_code law:code:corpus_juris_civilis thesaurus:related
ln legalhist:justinian_code law:tradition:civil_law_tradition thesaurus:related
def "legalhist:canon_law" "The Church's law that shaped medieval Europe."
ln legalhist:canon_law legalhist:milestone thesaurus:related
ln legalhist:canon_law hist:period:high_middle_ages legalhist:dates_from
ln legalhist:justinian_code legalhist:canon_law chrono:before
ln legalhist:canon_law law:tradition:canon_law thesaurus:related
def "legalhist:magna_carta" "England's 1215 charter limiting the king — the seed of constitutional government."
ln legalhist:magna_carta legalhist:milestone thesaurus:related
ln legalhist:magna_carta hist:period:high_middle_ages legalhist:dates_from
ln legalhist:canon_law legalhist:magna_carta chrono:before
ln legalhist:magna_carta law:concept:rule_of_law thesaurus:related
ln legalhist:magna_carta law:branch:constitutional_law thesaurus:related
def "legalhist:common_law" "The English case-law tradition of precedent."
ln legalhist:common_law legalhist:milestone thesaurus:related
ln legalhist:common_law hist:period:late_middle_ages legalhist:dates_from
ln legalhist:magna_carta legalhist:common_law chrono:before
ln legalhist:common_law law:tradition:english_common_law thesaurus:related
ln legalhist:common_law law:concept:stare_decisis thesaurus:related
def "legalhist:napoleonic_code" "The 1804 Civil Code that spread codified law across the world."
ln legalhist:napoleonic_code legalhist:milestone thesaurus:related
ln legalhist:napoleonic_code hist:period:modern_era legalhist:dates_from
ln legalhist:common_law legalhist:napoleonic_code chrono:before
ln legalhist:napoleonic_code law:tradition:civil_law_tradition thesaurus:related
ln legalhist:napoleonic_code hist:event:napoleonic_wars thesaurus:related
def "legalhist:human_rights_law" "The Universal Declaration (1948) — rights as a global standard."
ln legalhist:human_rights_law legalhist:milestone thesaurus:related
ln legalhist:human_rights_law hist:period:world_wars_era legalhist:dates_from
ln legalhist:napoleonic_code legalhist:human_rights_law chrono:before
ln legalhist:human_rights_law law:branch:international_law thesaurus:related
ln legalhist:human_rights_law law:concept:legal_personhood thesaurus:related
