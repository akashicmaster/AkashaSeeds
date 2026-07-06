# Akasha ontology — namespace: emo
# atoms: 29

def "emo:admiration" "Respect and warm approval."

def "emo:adoration" "Deep love and respect."

def "emo:aesthetic" "Aesthetic Appreciation. Experiencing beauty."

def "emo:amusement" "Finding something funny or entertaining."

def "emo:anger" "A strong feeling of annoyance, displeasure, or hostility."

def "emo:anticipation" "A feeling of excitement about something that will happen."

def "emo:anxiety" "A feeling of worry, nervousness, or unease."
ln emo:anxiety emo:fear sys:is_a
ln emo:anxiety emo:sadness sys:is_a
ln emo:anxiety concept:darkness calc:associated_with

def "emo:awe" "A feeling of reverential respect mixed with fear or wonder."
ln emo:awe emo:surprise sys:is_a
ln emo:awe emo:fear sys:is_a
ln emo:awe concept:sun calc:associated_with

def "emo:awkwardness" "Hard to do or deal with; causing unease."

def "emo:boredom" "Feeling weary and restless through lack of interest."

def "emo:calmness" "The state of being tranquil and quiet."
ln emo:calmness emo:joy sys:is_a
ln emo:calmness concept:peace calc:associated_with
ln emo:calmness concept:water calc:associated_with

def "emo:confusion" "Lack of understanding; uncertainty."

def "emo:craving" "A powerful desire for something."

def "emo:desire" "Sexual Desire. Strong physical attraction and longing."

def "emo:disgust" "A feeling of revulsion or strong disapproval aroused by something unpleasant."

def "emo:empathetic_pain" "Empathetic Pain. Feeling the physical or emotional pain of others."
ln emo:empathetic_pain emo:sadness sys:is_a
ln emo:empathetic_pain concept:friendship calc:associated_with

def "emo:entrancement" "Being filled with wonder and delight, spellbound."

def "emo:excitement" "A feeling of great enthusiasm and eagerness."

def "emo:fear" "An unpleasant emotion caused by the threat of danger or harm."

def "emo:horror" "An intense feeling of fear, shock, or disgust."
ln emo:horror emo:fear sys:is_a
ln emo:horror emo:disgust sys:is_a
ln emo:horror concept:death calc:associated_with

def "emo:interest" "The state of wanting to know or learn about something."

def "emo:joy" "A feeling of great pleasure and happiness."

def "emo:nostalgia" "A sentimental longing for the past."
ln emo:nostalgia emo:sadness sys:is_a
ln emo:nostalgia emo:joy sys:is_a
ln emo:nostalgia concept:home calc:associated_with

def "emo:relief" "Reassurance and relaxation following release from anxiety."
ln emo:relief emo:joy sys:is_a
ln emo:relief concept:peace calc:associated_with
ln emo:relief concept:protection calc:associated_with

def "emo:romance" "A feeling of excitement and mystery associated with love."
ln emo:romance emo:joy sys:is_a
ln emo:romance concept:love calc:associated_with

def "emo:sadness" "A feeling of sorrow or unhappiness."

def "emo:satisfaction" "Fulfillment of one's wishes, expectations, or needs."

def "emo:surprise" "Mild astonishment or shock caused by something unexpected."

def "emo:trust" "Firm belief in the reliability or truth of someone or something."
