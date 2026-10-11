# Akasha ontology — namespace: process
# atoms: 18

def "process:chem:contact_process" "The current method of producing sulfuric acid in the high concentrations needed for industrial processes."
ln process:chem:contact_process chem_ind.processes sys:is_a
ln process:chem:contact_process chem:compound:sulfuric_acid @produces
set.add name="ontology.industrial_chemistry" id="process:chem:contact_process"

def "process:chem:haber_process" "An artificial nitrogen fixation process and the main industrial procedure for the production of ammonia."
ln process:chem:haber_process chem_ind.processes sys:is_a
ln process:chem:haber_process chem:compound:ammonia @produces
set.add name="ontology.industrial_chemistry" id="process:chem:haber_process"

def "process:chem:ostwald_process" "A chemical process for making nitric acid from ammonia."
ln process:chem:ostwald_process chem_ind.processes sys:is_a
ln process:chem:ostwald_process chem:compound:ammonia @consumes
ln process:chem:ostwald_process chem:compound:nitric_acid @produces
set.add name="ontology.industrial_chemistry" id="process:chem:ostwald_process"

def "process:chem:steam_cracking" "A petrochemical process in which saturated hydrocarbons are broken down into smaller, often unsaturated, hydrocarbons."
ln process:chem:steam_cracking chem_ind.processes sys:is_a
ln process:chem:steam_cracking chem:compound:ethylene @produces
ln process:chem:steam_cracking chem:compound:propylene @produces
set.add name="ontology.industrial_chemistry" id="process:chem:steam_cracking"

def "process:cook_chill" "A systematic workflow of cooking, rapidly chilling, and storing food."
ln process:cook_chill tool:large:combi_oven @uses
ln process:cook_chill tool:large:blast_chiller @uses
ln process:cook_chill tool:large:refrigerator @uses
ln process:cook_chill tool:large:freezer @uses
ln process:cook_chill haccp:temperature_danger_zone @bypasses

def "process:mixology:build" "Assembling the cocktail directly in the serving glass."

def "process:mixology:clarification" "Removing suspended particles from a liquid via milk washing, gelatin, or centrifugation to produce a crystal-clear result."
ln process:mixology:clarification verb:cook:clarify sys:refers_to
ln process:mixology:clarification dna:color:clear calc:associated_with

def "process:mixology:double_strain" "Pouring a shaken drink through both a primary strainer and a fine-mesh sieve to remove ice shards and fruit pulp."
ln process:mixology:double_strain process:mixology:shake @requires

def "process:mixology:dry_shake" "Shaking cocktail ingredients without ice to emulsify proteins (especially egg white) before the chilled shake."
ln process:mixology:dry_shake verb:cook:emulsify sys:refers_to
ln process:mixology:dry_shake dna:texture:soft calc:associated_with
ln process:mixology:dry_shake dna:texture:smooth calc:associated_with

def "process:mixology:express" "Holding a citrus peel skin-side down over a drink and twisting sharply to spray essential oils across the surface."
ln process:mixology:express verb:cook:press sys:refers_to
ln process:mixology:express dna:smell:fragrant calc:associated_with

def "process:mixology:fat_washing" "Infusing spirits with a flavorful fat (butter, bacon fat, etc.), chilling to solidify, then skimming to leave fat-soluble flavor compounds."
ln process:mixology:fat_washing verb:cook:infuse sys:refers_to

def "process:mixology:infusion" "Steeping ingredients (spices/herbs) in alcohol over time."
ln process:mixology:infusion verb:cook:infuse sys:refers_to

def "process:mixology:layer" "Carefully pouring liquids of different densities to form distinct bands."
ln process:mixology:layer dna:color:vivid calc:associated_with
ln process:mixology:layer verb:cook:pour sys:refers_to

def "process:mixology:reverse_dry_shake" "Shaking with ice first, straining, then re-shaking without ice to maximise foam volume and texture."
ln process:mixology:reverse_dry_shake process:mixology:dry_shake sys:is_a

def "process:mixology:rim" "Coating the edge of a glass with salt, sugar, or spice by running a citrus wedge then pressing the rim into the coating."

def "process:mixology:shake" "Aerating and chilling liquid by rapid mechanical movement."
ln process:mixology:shake verb:cook:whip sys:refers_to
ln process:mixology:shake verb:cook:chill sys:refers_to

def "process:mixology:stir" "Gently mixing ingredients without aerating, common for spirit-forward cocktails."
ln process:mixology:stir verb:cook:stir sys:refers_to

def "process:sous_vide" "Vacuum-sealed precision temperature cooking."
ln process:sous_vide tool:large:vacuum_machine @uses
ln process:sous_vide tool:large:combi_oven @uses
ln process:sous_vide tool:small:sous_vide_circulator @uses
ln process:sous_vide tool:small:vacuum_sealer @uses
ln process:sous_vide prop:cook:anaerobic sys:is_a
