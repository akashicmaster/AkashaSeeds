# Akasha ontology — namespace: cook
# atoms: 21

def "cook:bit" "A small non-standard fragment or piece."

def "cook:clove" "One segment of a head of garlic."
ln cook:clove dna:smell:pungent calc:associated_with

def "cook:cup" "Standard volume measure; approximately 240 ml."
ln cook:cup unit:base:milliliter calc:associated_with

def "cook:dash" "A very small dry quantity; typically 1/8 teaspoon."

def "cook:dash_liquid" "A quick liquid pour; typically used for bitters or sauce."

def "cook:handful" "The approximate amount held loosely in one hand."

def "cook:lump" "A solid irregular mass; typically used for butter or sugar."

def "cook:pinch" "The amount of a dry ingredient held between thumb and index finger."
ln cook:pinch dna:taste:salty calc:associated_with

def "cook:slice" "A single piece of food cut from a larger piece."

def "cook:splash" "A small, unspecified amount of liquid added to a dish."

def "cook:tablespoon" "Standard culinary volume spoon; approximately 15 ml."
ln cook:tablespoon unit:base:milliliter calc:associated_with

def "cook:teaspoon" "Small culinary volume spoon; approximately 5 ml."
ln cook:teaspoon unit:base:milliliter calc:associated_with

def "cook:temp:boiling" "100C; vigorous full rolling boil."
ln cook:temp:boiling dna:touch:hot calc:associated_with
ln cook:temp:boiling haccp:biological_hazard @destroys

def "cook:temp:chilled" "0C - 5C; refrigerated temperature."
ln cook:temp:chilled dna:touch:cold calc:associated_with

def "cook:temp:human_skin" "36C - 37C; ideal for proofing yeast or testing baby food."
ln cook:temp:human_skin dna:touch:warm calc:associated_with

def "cook:temp:ice_cold" "Below 0C; frost-covered or near-freezing."
ln cook:temp:ice_cold dna:touch:ice_cold sys:same_as

def "cook:temp:lukewarm" "30C - 35C; slightly below body temperature."
ln cook:temp:lukewarm dna:touch:warm calc:associated_with

def "cook:temp:room_temp" "20C - 25C; standard bench or ambient state."

def "cook:temp:searing_hot" "180C and above; smoking oil and rapid surface browning."
ln cook:temp:searing_hot dna:touch:hot calc:associated_with

def "cook:temp:simmering" "80C - 95C; small bubbles rising steadily."
ln cook:temp:simmering dna:touch:hot calc:associated_with

def "cook:temp:warm" "40C - 60C; comfortably hot to the touch."
ln cook:temp:warm dna:touch:warm calc:associated_with
