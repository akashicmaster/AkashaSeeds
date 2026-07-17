# Akasha ontology — dna:pungency (trigeminal / chemesthetic axis)
# 'Hot' spiciness is a trigeminal irritation, not one of the basic tastes.
# Give it its own axis, bridge the legacy dna:taste:hot into it, wire it to
# emotion, and register the proto-words. Base pack.

def "dna:pungency:hot" "Pungent heat — capsaicin/piperine irritation (chilli, pepper, ginger)."
def "dna:pungency:cooling" "Cooling — menthol freshness (mint, menthol)."
def "dna:pungency:numbing" "Numbing tingle — sanshool (Sichuan pepper)."
def "dna:pungency:astringent" "Astringency — drying tannic pucker (tea, tannin)."

ln dna:taste:hot dna:pungency:hot thesaurus:related

ln dna:pungency:hot emo:excitement calc:associated_with
ln dna:pungency:cooling emo:calmness calc:associated_with
ln dna:pungency:cooling emo:relief calc:associated_with
ln dna:pungency:numbing emo:surprise calc:associated_with
ln dna:pungency:astringent emo:disgust calc:associated_with

ln spicy dna:pungency:hot thesaurus:related
ln piquant dna:pungency:hot thesaurus:related
ln minty dna:pungency:cooling thesaurus:related
ln menthol dna:pungency:cooling thesaurus:related
ln numbing dna:pungency:numbing thesaurus:related
ln tingling dna:pungency:numbing thesaurus:related
ln astringent dna:pungency:astringent thesaurus:related
ln tannic dna:pungency:astringent thesaurus:related

ln ingred:herb:mint dna:pungency:cooling calc:associated_with
ln ingred:spice:sichuan_pepper dna:pungency:numbing calc:associated_with
