# Akasha ontology — heat / spiciness intensity (Scoville-informed). Base pack.
# rec:heat is a 0-1 heat intensity (capsaicin ~ log Scoville; pepper/mustard/
# wasabi pungency scaled by perception). heat_level bands mild/medium/hot/
# very_hot (culinary:heat_level). Chilli varieties carry approximate SHU.

def "heat_level:mild" "Mild heat."
def "heat_level:medium" "Medium heat."
def "heat_level:hot" "Hot."
def "heat_level:very_hot" "Very hot / extreme."

# ── chilli varieties (Scoville spectrum) ──
def "ingred:veg:poblano" "A mild, dark chilli (~1,500 SHU)."
al ingred:veg:poblano poblano
ln ingred:veg:poblano plantpart:fruit_veg bio:plant_part
ln ingred:veg:poblano dna:color:red calc:associated_with
def "ingred:veg:jalapeno" "A medium fresh chilli (~5,000 SHU)."
al ingred:veg:jalapeno jalapeno
ln ingred:veg:jalapeno plantpart:fruit_veg bio:plant_part
ln ingred:veg:jalapeno dna:color:red calc:associated_with
def "ingred:veg:serrano" "A brighter, hotter chilli (~15,000 SHU)."
al ingred:veg:serrano serrano
ln ingred:veg:serrano plantpart:fruit_veg bio:plant_part
ln ingred:veg:serrano dna:color:red calc:associated_with
def "ingred:veg:thai_chili" "A fiery bird's-eye chilli (~75,000 SHU)."
al ingred:veg:thai_chili thai_chili
ln ingred:veg:thai_chili plantpart:fruit_veg bio:plant_part
ln ingred:veg:thai_chili dna:color:red calc:associated_with
def "ingred:veg:scotch_bonnet" "A fruity, very hot chilli (~150,000 SHU)."
al ingred:veg:scotch_bonnet scotch_bonnet
ln ingred:veg:scotch_bonnet plantpart:fruit_veg bio:plant_part
ln ingred:veg:scotch_bonnet dna:color:red calc:associated_with
def "ingred:veg:habanero" "An intensely hot chilli (~200,000 SHU)."
al ingred:veg:habanero habanero
ln ingred:veg:habanero plantpart:fruit_veg bio:plant_part
ln ingred:veg:habanero dna:color:red calc:associated_with
def "ingred:veg:ghost_pepper" "Bhut jolokia — searing heat (~1,000,000 SHU)."
al ingred:veg:ghost_pepper ghost_pepper
ln ingred:veg:ghost_pepper plantpart:fruit_veg bio:plant_part
ln ingred:veg:ghost_pepper dna:color:red calc:associated_with
def "ingred:veg:carolina_reaper" "The record-hot chilli (~2,000,000 SHU)."
al ingred:veg:carolina_reaper carolina_reaper
ln ingred:veg:carolina_reaper plantpart:fruit_veg bio:plant_part
ln ingred:veg:carolina_reaper dna:color:red calc:associated_with

# ── heat scores + pungency + level ──
ln ingred:condiment:chili_oil score:0.5 rec:heat
ln ingred:condiment:chili_oil dna:pungency:hot calc:associated_with
ln ingred:condiment:chili_oil heat_level:medium culinary:heat_level
ln ingred:condiment:gochujang score:0.3 rec:heat
ln ingred:condiment:gochujang dna:pungency:hot calc:associated_with
ln ingred:condiment:gochujang heat_level:medium culinary:heat_level
ln ingred:condiment:harissa score:0.6 rec:heat
ln ingred:condiment:harissa dna:pungency:hot calc:associated_with
ln ingred:condiment:harissa heat_level:hot culinary:heat_level
ln ingred:condiment:horseradish score:0.55 rec:heat
ln ingred:condiment:horseradish dna:pungency:hot calc:associated_with
ln ingred:condiment:horseradish heat_level:hot culinary:heat_level
ln ingred:condiment:hot_sauce score:0.5 rec:heat
ln ingred:condiment:hot_sauce dna:pungency:hot calc:associated_with
ln ingred:condiment:hot_sauce heat_level:medium culinary:heat_level
ln ingred:condiment:mustard score:0.3 rec:heat
ln ingred:condiment:mustard dna:pungency:hot calc:associated_with
ln ingred:condiment:mustard heat_level:medium culinary:heat_level
ln ingred:condiment:salsa score:0.3 rec:heat
ln ingred:condiment:salsa dna:pungency:hot calc:associated_with
ln ingred:condiment:salsa heat_level:medium culinary:heat_level
ln ingred:condiment:sriracha score:0.4 rec:heat
ln ingred:condiment:sriracha dna:pungency:hot calc:associated_with
ln ingred:condiment:sriracha heat_level:medium culinary:heat_level
ln ingred:condiment:tabasco score:0.5 rec:heat
ln ingred:condiment:tabasco dna:pungency:hot calc:associated_with
ln ingred:condiment:tabasco heat_level:medium culinary:heat_level
ln ingred:condiment:wasabi score:0.6 rec:heat
ln ingred:condiment:wasabi dna:pungency:hot calc:associated_with
ln ingred:condiment:wasabi heat_level:hot culinary:heat_level
ln ingred:seafood:mentaiko score:0.35 rec:heat
ln ingred:seafood:mentaiko dna:pungency:hot calc:associated_with
ln ingred:seafood:mentaiko heat_level:medium culinary:heat_level
ln ingred:spice:black_pepper score:0.25 rec:heat
ln ingred:spice:black_pepper dna:pungency:hot calc:associated_with
ln ingred:spice:black_pepper heat_level:mild culinary:heat_level
ln ingred:spice:cayenne score:0.75 rec:heat
ln ingred:spice:cayenne dna:pungency:hot calc:associated_with
ln ingred:spice:cayenne heat_level:hot culinary:heat_level
ln ingred:spice:chili_powder score:0.4 rec:heat
ln ingred:spice:chili_powder dna:pungency:hot calc:associated_with
ln ingred:spice:chili_powder heat_level:medium culinary:heat_level
ln ingred:spice:galangal score:0.2 rec:heat
ln ingred:spice:galangal dna:pungency:hot calc:associated_with
ln ingred:spice:galangal heat_level:mild culinary:heat_level
ln ingred:spice:ginger score:0.15 rec:heat
ln ingred:spice:ginger dna:pungency:hot calc:associated_with
ln ingred:spice:ginger heat_level:mild culinary:heat_level
ln ingred:spice:long_pepper score:0.3 rec:heat
ln ingred:spice:long_pepper dna:pungency:hot calc:associated_with
ln ingred:spice:long_pepper heat_level:medium culinary:heat_level
ln ingred:spice:mustard_seed score:0.3 rec:heat
ln ingred:spice:mustard_seed dna:pungency:hot calc:associated_with
ln ingred:spice:mustard_seed heat_level:medium culinary:heat_level
ln ingred:spice:paprika score:0.1 rec:heat
ln ingred:spice:paprika dna:pungency:hot calc:associated_with
ln ingred:spice:paprika heat_level:mild culinary:heat_level
ln ingred:spice:sichuan_pepper score:0.2 rec:heat
ln ingred:spice:sichuan_pepper dna:pungency:hot calc:associated_with
ln ingred:spice:sichuan_pepper heat_level:mild culinary:heat_level
ln ingred:spice:white_pepper score:0.2 rec:heat
ln ingred:spice:white_pepper dna:pungency:hot calc:associated_with
ln ingred:spice:white_pepper heat_level:mild culinary:heat_level
ln ingred:veg:bell_pepper score:0.0 rec:heat
ln ingred:veg:carolina_reaper score:1.0 rec:heat
ln ingred:veg:carolina_reaper dna:pungency:hot calc:associated_with
ln ingred:veg:carolina_reaper heat_level:very_hot culinary:heat_level
ln ingred:veg:chili_pepper score:0.5 rec:heat
ln ingred:veg:chili_pepper dna:pungency:hot calc:associated_with
ln ingred:veg:chili_pepper heat_level:medium culinary:heat_level
ln ingred:veg:ghost_pepper score:0.95 rec:heat
ln ingred:veg:ghost_pepper dna:pungency:hot calc:associated_with
ln ingred:veg:ghost_pepper heat_level:very_hot culinary:heat_level
ln ingred:veg:habanero score:0.85 rec:heat
ln ingred:veg:habanero dna:pungency:hot calc:associated_with
ln ingred:veg:habanero heat_level:very_hot culinary:heat_level
ln ingred:veg:jalapeno score:0.35 rec:heat
ln ingred:veg:jalapeno dna:pungency:hot calc:associated_with
ln ingred:veg:jalapeno heat_level:medium culinary:heat_level
ln ingred:veg:poblano score:0.15 rec:heat
ln ingred:veg:poblano dna:pungency:hot calc:associated_with
ln ingred:veg:poblano heat_level:mild culinary:heat_level
ln ingred:veg:scotch_bonnet score:0.82 rec:heat
ln ingred:veg:scotch_bonnet dna:pungency:hot calc:associated_with
ln ingred:veg:scotch_bonnet heat_level:very_hot culinary:heat_level
ln ingred:veg:serrano score:0.5 rec:heat
ln ingred:veg:serrano dna:pungency:hot calc:associated_with
ln ingred:veg:serrano heat_level:medium culinary:heat_level
ln ingred:veg:thai_chili score:0.75 rec:heat
ln ingred:veg:thai_chili dna:pungency:hot calc:associated_with
ln ingred:veg:thai_chili heat_level:hot culinary:heat_level
