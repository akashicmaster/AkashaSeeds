# Akasha ontology — namespace: color
# Basic colour atoms; each linked to emotions and primal concepts.
# Warm / cool / neutral sets for palette-level queries.
# atoms: 13

def "color:red" "Red — the colour of blood and fire; warm, energetic, intense."
ln color:red emo:anger calc:associated_with
ln color:red emo:romance calc:associated_with
ln color:red emo:excitement calc:associated_with
ln color:red concept:fire thesaurus:related
set.add name="set:color:warm" id="color:red"
set.add name="set:color:index" id="color:red"

def "color:orange" "Orange — the colour of autumn leaves and embers; warm, playful, creative."
ln color:orange emo:excitement calc:associated_with
ln color:orange emo:joy calc:associated_with
ln color:orange concept:fire thesaurus:related
ln color:orange concept:autumn thesaurus:related
set.add name="set:color:warm" id="color:orange"
set.add name="set:color:index" id="color:orange"

def "color:yellow" "Yellow — the colour of sunlight and gold; bright, optimistic, warm."
ln color:yellow emo:joy calc:associated_with
ln color:yellow emo:awe calc:associated_with
ln color:yellow concept:sun thesaurus:related
ln color:yellow concept:light thesaurus:related
set.add name="set:color:warm" id="color:yellow"
set.add name="set:color:index" id="color:yellow"

def "color:pink" "Pink — a soft warm hue; associated with gentleness and affection."
ln color:pink emo:romance calc:associated_with
ln color:pink emo:adoration calc:associated_with
ln color:pink concept:love thesaurus:related
set.add name="set:color:warm" id="color:pink"
set.add name="set:color:index" id="color:pink"

def "color:green" "Green — the colour of leaves and growth; calm, vital, balanced."
ln color:green emo:calmness calc:associated_with
ln color:green emo:relief calc:associated_with
ln color:green concept:nature thesaurus:related
ln color:green concept:growth thesaurus:related
set.add name="set:color:cool" id="color:green"
set.add name="set:color:index" id="color:green"

def "color:blue" "Blue — the colour of sky and ocean; calm, deep, melancholic."
ln color:blue emo:calmness calc:associated_with
ln color:blue emo:sadness calc:associated_with
ln color:blue emo:trust calc:associated_with
ln color:blue concept:water thesaurus:related
ln color:blue concept:sky thesaurus:related
set.add name="set:color:cool" id="color:blue"
set.add name="set:color:index" id="color:blue"

def "color:purple" "Purple — the colour of dusk and rare dyes; mysterious, creative, spiritual."
ln color:purple emo:awe calc:associated_with
ln color:purple emo:nostalgia calc:associated_with
ln color:purple concept:dusk thesaurus:related
set.add name="set:color:cool" id="color:purple"
set.add name="set:color:index" id="color:purple"

def "color:white" "White — the colour of snow and pure light; open, peaceful, clean."
ln color:white emo:calmness calc:associated_with
ln color:white emo:awe calc:associated_with
ln color:white concept:snow thesaurus:related
ln color:white concept:light thesaurus:related
set.add name="set:color:neutral" id="color:white"
set.add name="set:color:index" id="color:white"

def "color:black" "Black — the colour of deep night and ink; powerful, solemn, mysterious."
ln color:black emo:fear calc:associated_with
ln color:black emo:awe calc:associated_with
ln color:black emo:sadness calc:associated_with
ln color:black concept:night thesaurus:related
ln color:black concept:darkness thesaurus:related
set.add name="set:color:neutral" id="color:black"
set.add name="set:color:index" id="color:black"

def "color:grey" "Grey — between white and black; neutral, ambiguous, contemplative."
ln color:grey emo:sadness calc:associated_with
ln color:grey emo:boredom calc:associated_with
ln color:grey emo:nostalgia calc:associated_with
ln color:grey concept:rain thesaurus:related
set.add name="set:color:neutral" id="color:grey"
set.add name="set:color:index" id="color:grey"

def "color:gold" "Gold — the colour of precious metal and harvest; warm, glorious, precious."
ln color:gold emo:admiration calc:associated_with
ln color:gold emo:awe calc:associated_with
ln color:gold emo:excitement calc:associated_with
ln color:gold concept:sun thesaurus:related
set.add name="set:color:warm" id="color:gold"
set.add name="set:color:index" id="color:gold"

def "color:silver" "Silver — the colour of the moon and still water; cool, elegant, reflective."
ln color:silver emo:aesthetic calc:associated_with
ln color:silver emo:awe calc:associated_with
ln color:silver concept:moon thesaurus:related
set.add name="set:color:cool" id="color:silver"
set.add name="set:color:index" id="color:silver"

def "color:brown" "Brown — the colour of soil and bark; grounded, natural, enduring."
ln color:brown emo:satisfaction calc:associated_with
ln color:brown emo:nostalgia calc:associated_with
ln color:brown concept:earth thesaurus:related
ln color:brown concept:autumn thesaurus:related
set.add name="set:color:neutral" id="color:brown"
set.add name="set:color:index" id="color:brown"
