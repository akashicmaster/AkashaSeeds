# Akasha ontology — seasoning metadata: fill flavour, origin (cuisine), use
# Adds missing taste/smell for existing herbs/spices, links strongly-
# associated spices/herbs to a cuisine, and a culinary:use axis. Base pack.

# ── fill missing flavour ──
ln ingred:herb:curry_leaf dna:smell:fragrant calc:associated_with
ln ingred:herb:dill dna:smell:fragrant calc:associated_with
ln ingred:herb:kaffir_lime_leaf dna:smell:fragrant calc:associated_with
ln ingred:herb:lemongrass dna:smell:fragrant calc:associated_with
ln ingred:herb:mint dna:smell:fragrant calc:associated_with
ln ingred:herb:oregano dna:smell:fragrant calc:associated_with
ln ingred:herb:rosemary dna:smell:fragrant calc:associated_with
ln ingred:herb:thyme dna:smell:fragrant calc:associated_with
ln ingred:spice:ajwain dna:smell:pungent calc:associated_with
ln ingred:spice:ajwain dna:taste:bitter calc:associated_with
ln ingred:spice:black_pepper dna:smell:pungent calc:associated_with
ln ingred:spice:coriander_seed dna:smell:fragrant calc:associated_with
ln ingred:spice:cumin dna:smell:fragrant calc:associated_with
ln ingred:spice:cumin dna:taste:bitter calc:associated_with
ln ingred:spice:mustard_seed dna:smell:pungent calc:associated_with
ln ingred:spice:nigella_seed dna:smell:pungent calc:associated_with
ln ingred:spice:nutmeg dna:smell:fragrant calc:associated_with
ln ingred:spice:nutmeg dna:taste:sweet calc:associated_with
ln ingred:spice:star_anise dna:taste:sweet calc:associated_with
ln ingred:spice:star_anise dna:smell:fragrant calc:associated_with
ln ingred:spice:black_pepper dna:pungency:hot calc:associated_with
ln ingred:spice:mustard_seed dna:pungency:hot calc:associated_with

# ── origin (cuisine) ──
ln ingred:spice:turmeric cuisine:indian thesaurus:related
ln ingred:spice:cumin cuisine:indian thesaurus:related
ln ingred:spice:coriander_seed cuisine:indian thesaurus:related
ln ingred:spice:cardamom cuisine:indian thesaurus:related
ln ingred:spice:fenugreek cuisine:indian thesaurus:related
ln ingred:spice:ajwain cuisine:indian thesaurus:related
ln ingred:spice:asafoetida cuisine:indian thesaurus:related
ln ingred:spice:nigella_seed cuisine:indian thesaurus:related
ln ingred:spice:amchur cuisine:indian thesaurus:related
ln ingred:herb:curry_leaf cuisine:indian thesaurus:related
ln ingred:blend:garam_masala cuisine:indian thesaurus:related
ln ingred:blend:curry_powder cuisine:indian thesaurus:related
ln ingred:blend:chaat_masala cuisine:indian thesaurus:related
ln ingred:blend:panch_phoran cuisine:indian thesaurus:related
ln ingred:spice:sichuan_pepper cuisine:chinese thesaurus:related
ln ingred:spice:star_anise cuisine:chinese thesaurus:related
ln ingred:blend:five_spice cuisine:chinese thesaurus:related
ln ingred:herb:shiso cuisine:japanese thesaurus:related
ln ingred:condiment:wasabi cuisine:japanese thesaurus:related
ln ingred:condiment:mirin cuisine:japanese thesaurus:related
ln ingred:condiment:ponzu cuisine:japanese thesaurus:related
ln ingred:herb:lemongrass cuisine:thai thesaurus:related
ln ingred:spice:galangal cuisine:thai thesaurus:related
ln ingred:herb:kaffir_lime_leaf cuisine:thai thesaurus:related
ln ingred:herb:basil cuisine:italian thesaurus:related
ln ingred:herb:oregano cuisine:italian thesaurus:related
ln ingred:herb:marjoram cuisine:italian thesaurus:related
ln ingred:condiment:pesto cuisine:italian thesaurus:related
ln ingred:spice:cayenne cuisine:mexican thesaurus:related
ln ingred:spice:chili_powder cuisine:mexican thesaurus:related
ln ingred:condiment:salsa cuisine:mexican thesaurus:related
ln ingred:herb:tarragon cuisine:french thesaurus:related
ln ingred:herb:chervil cuisine:french thesaurus:related
ln ingred:herb:bay_leaf cuisine:french thesaurus:related
ln ingred:blend:ras_el_hanout cuisine:moroccan thesaurus:related
ln ingred:condiment:harissa cuisine:moroccan thesaurus:related
ln ingred:condiment:gochujang cuisine:korean thesaurus:related
ln ingred:ferment:kimchi cuisine:korean thesaurus:related
ln ingred:ferment:doenjang cuisine:korean thesaurus:related

# ── culinary use ──
def "culinary:use:sweet" "Used in sweet dishes / baking."
def "culinary:use:meat" "Used with meat."
def "culinary:use:fish" "Used with fish/seafood."
def "culinary:use:pickling" "Used in pickling/preserving."
ln ingred:spice:cinnamon culinary:use:sweet culinary:use
ln ingred:spice:nutmeg culinary:use:sweet culinary:use
ln ingred:spice:vanilla culinary:use:sweet culinary:use
ln ingred:spice:anise_seed culinary:use:sweet culinary:use
ln ingred:spice:fennel_seed culinary:use:sweet culinary:use
ln ingred:spice:allspice culinary:use:sweet culinary:use
ln ingred:spice:cardamom culinary:use:sweet culinary:use
ln ingred:spice:clove culinary:use:sweet culinary:use
ln ingred:spice:star_anise culinary:use:sweet culinary:use
ln ingred:spice:mace culinary:use:sweet culinary:use
ln ingred:spice:ginger culinary:use:sweet culinary:use
ln ingred:herb:rosemary culinary:use:meat culinary:use
ln ingred:herb:thyme culinary:use:meat culinary:use
ln ingred:herb:sage culinary:use:meat culinary:use
ln ingred:spice:juniper culinary:use:meat culinary:use
ln ingred:spice:black_pepper culinary:use:meat culinary:use
ln ingred:spice:garlic_powder culinary:use:meat culinary:use
ln ingred:herb:bay_leaf culinary:use:meat culinary:use
ln ingred:spice:cumin culinary:use:meat culinary:use
ln ingred:spice:paprika culinary:use:meat culinary:use
ln ingred:herb:oregano culinary:use:meat culinary:use
ln ingred:herb:dill culinary:use:fish culinary:use
ln ingred:herb:lemongrass culinary:use:fish culinary:use
ln ingred:herb:kaffir_lime_leaf culinary:use:fish culinary:use
ln ingred:spice:fennel_seed culinary:use:fish culinary:use
ln ingred:herb:parsley culinary:use:fish culinary:use
ln ingred:herb:tarragon culinary:use:fish culinary:use
ln ingred:spice:mustard_seed culinary:use:pickling culinary:use
ln ingred:herb:dill culinary:use:pickling culinary:use
ln ingred:herb:bay_leaf culinary:use:pickling culinary:use
ln ingred:spice:coriander_seed culinary:use:pickling culinary:use
ln ingred:spice:black_pepper culinary:use:pickling culinary:use
ln ingred:spice:caraway culinary:use:pickling culinary:use
