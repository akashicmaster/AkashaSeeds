# Akasha ontology — seafood tuning: eel flesh, predominant source
# Fine-tuning on top of seafood_species.ak:
#  · eel is a fatty white-fleshed fish → flesh_type:white.
#  · for species that are both wild & farmed, mark the predominant commercial
#    source with bio:source_primary (the both-links on bio:source remain).
# Base pack.

ln ingred:seafood:eel flesh_type:white bio:flesh_type

# ── predominant source ──
ln ingred:seafood:salmon source:farmed bio:source_primary
ln ingred:seafood:trout source:farmed bio:source_primary
ln ingred:seafood:sea_bass source:farmed bio:source_primary
ln ingred:seafood:bream source:farmed bio:source_primary
ln ingred:seafood:shrimp source:farmed bio:source_primary
ln ingred:seafood:oyster source:farmed bio:source_primary
ln ingred:seafood:mussel source:farmed bio:source_primary
ln ingred:seafood:eel source:farmed bio:source_primary
ln ingred:seafood:sturgeon source:farmed bio:source_primary
ln ingred:seafood:kombu source:farmed bio:source_primary
ln ingred:seafood:yellowtail source:farmed bio:source_primary
ln ingred:seafood:scallop source:wild bio:source_primary
ln ingred:seafood:clam source:wild bio:source_primary
