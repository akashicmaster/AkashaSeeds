# Akasha ontology — food therapy (dietary therapy) frame + traditions.
# DESCRIPTIVE cultural knowledge: how each tradition classifies foods, NOT
# medical advice or claims of efficacy. provenance: traditional.

def "foodtherapy" "Dietary therapy (食養): classifying foods by their perceived qualities/effects within traditional systems. Descriptive cultural knowledge, not medical advice."
def "tradition:tcm" "Traditional Chinese Medicine dietary therapy (中医食養・薬膳): five natures, five flavours, meridian tropism."
def "tradition:kampo" "Japanese Kampo (日本漢方), derived from Chinese medicine."
def "tradition:ayurveda" "Ayurvedic dietary science (アーユルヴェーダ): six tastes (rasa), potency (virya), and dosha balance."
def "tradition:homeopathy" "Homeopathy: a modality of highly-diluted remedies (like-cures-like). It is NOT a food-classification system and has no scientific evidence of efficacy; recorded here only as a named concept, with no food properties attached."

ln tradition:tcm foodtherapy thesaurus:related
ln tradition:kampo tradition:tcm thesaurus:related
ln tradition:kampo foodtherapy thesaurus:related
ln tradition:ayurveda foodtherapy thesaurus:related
ln tradition:homeopathy foodtherapy thesaurus:related
