# Akasha ontology — namespace: hist
# atoms: 30

def "hist:anachronism" "Placement of ideas, objects, or values outside their historical context."
ln hist:anachronism historiography.temporality sys:is_a
ln hist:anachronism phil:context @violates
ln hist:anachronism sem:ambiguity @may_produce
set.add name="ontology.historiography" id="hist:anachronism"

def "hist:archive" "Institutional or symbolic repository preserving historical traces and records."
ln hist:archive historiography.archive sys:is_a
ln hist:archive sys:storage @analogous_to
ln hist:archive sys:repository @analogous_to
ln hist:archive hist:document @contains
set.add name="ontology.historiography" id="hist:archive"

def "hist:canonization" "Process through which texts, events, or figures become culturally authoritative."
ln hist:canonization historiography.memory sys:is_a
ln hist:canonization rhet:ethos @supports
ln hist:canonization myth:canon @related_to
set.add name="ontology.historiography" id="hist:canonization"

def "hist:chronicle" "Sequential recording of events ordered through time."
ln hist:chronicle historiography.method sys:is_a
ln hist:chronicle ont.narrative @uses
set.add name="ontology.historiography" id="hist:chronicle"

def "hist:collective_memory" "Shared remembrance maintained by a community, culture, or society."
ln hist:collective_memory historiography.memory sys:is_a
ln hist:collective_memory civ:community @maintained_by
ln hist:collective_memory nar:testimony @supports
ln hist:collective_memory hist:commemoration @supports
ln hist:collective_memory anth:worldview @shapes
set.add name="ontology.historiography" id="hist:collective_memory"

def "hist:commemoration" "Act of publicly remembering persons, events, or collective experiences."
ln hist:commemoration historiography.memory sys:is_a
ln hist:commemoration hist:collective_memory @reinforces
ln hist:commemoration myth:ritual @can_take_form_as
set.add name="ontology.historiography" id="hist:commemoration"

def "hist:continuity" "Persistence of structures, meanings, or traditions across time."
ln hist:continuity historiography.temporality sys:is_a
ln hist:continuity hist:rupture @contrasts_with
set.add name="ontology.historiography" id="hist:continuity"

def "hist:cultural_memory" "Long-term symbolic memory preserved through narratives, rituals, monuments, and traditions."
ln hist:cultural_memory historiography.memory sys:is_a
ln hist:cultural_memory ritual @preserved_by
ln hist:cultural_memory myth @preserves
set.add name="ontology.historiography" id="hist:cultural_memory"

def "hist:document" "Written, visual, or material source preserving historical information."
ln hist:document historiography.archive sys:is_a
ln hist:document sem:sign @can_function_as
set.add name="ontology.historiography" id="hist:document"

def "hist:enlightenment" "Intellectual movement emphasizing reason, critique, science, and universal principles."
ln hist:enlightenment historiography.period sys:is_a
ln hist:enlightenment phil:reason @elevates
set.add name="ontology.historiography" id="hist:enlightenment"

def "hist:epoch" "Distinct historical phase or age within broader chronology."
ln hist:epoch historiography.period sys:is_a
set.add name="ontology.historiography" id="hist:epoch"

def "hist:era" "Large-scale historical period characterized by shared structures, values, or events."
ln hist:era historiography.period sys:is_a
set.add name="ontology.historiography" id="hist:era"

def "hist:forgetting" "Loss, suppression, or fading of historical memory."
ln hist:forgetting historiography.memory sys:is_a
ln hist:forgetting oblivion @related_to
ln hist:forgetting hist:collective_memory @reduces
set.add name="ontology.historiography" id="hist:forgetting"

def "hist:genealogy" "Method tracing contingent historical emergence of concepts, institutions, or identities."
ln hist:genealogy historiography.method sys:is_a
ln hist:genealogy phil:identity @examines
ln hist:genealogy phil:causality @questions
set.add name="ontology.historiography" id="hist:genealogy"

def "hist:historical_consciousness" "Awareness of oneself and society as historically situated."
ln hist:historical_consciousness historiography.method sys:is_a
ln hist:historical_consciousness phil:selfhood @shapes
set.add name="ontology.historiography" id="hist:historical_consciousness"

def "hist:historical_propaganda" "Strategic shaping of historical interpretation for political or ideological purposes."
ln hist:historical_propaganda historiography.power sys:is_a
ln hist:historical_propaganda rhet:propaganda @extends
set.add name="ontology.historiography" id="hist:historical_propaganda"

def "hist:legitimacy" "Recognition of authority as justified, lawful, or culturally accepted."
ln hist:legitimacy historiography.power sys:is_a
ln hist:legitimacy civ:fairness @depends_on
ln hist:legitimacy civ:consensus @depends_on
set.add name="ontology.historiography" id="hist:legitimacy"

def "hist:modernity" "Historical condition associated with industrialization, rationalization, and modern social structures."
ln hist:modernity historiography.period sys:is_a
ln hist:modernity phil:reason @elevates
set.add name="ontology.historiography" id="hist:modernity"

def "hist:mythmaking" "Construction of legitimizing narratives around peoples, leaders, nations, or origins."
ln hist:mythmaking historiography.power sys:is_a
ln hist:mythmaking sem:mythic_signification @uses
ln hist:mythmaking civ:policy_proposal @may_legitimize
ln hist:mythmaking hist:collective_memory @shapes
ln hist:mythmaking myth:myth @constructs
set.add name="ontology.historiography" id="hist:mythmaking"

def "hist:periodization" "Division of history into meaningful temporal segments."
ln hist:periodization historiography.period sys:is_a
set.add name="ontology.historiography" id="hist:periodization"

def "hist:postmodernity" "Condition characterized by fragmentation, skepticism toward grand narratives, and reflexivity."
ln hist:postmodernity historiography.period sys:is_a
ln hist:postmodernity nar:fragmentation @related_to
set.add name="ontology.historiography" id="hist:postmodernity"

def "hist:record" "Preserved trace documenting events, transactions, or experiences."
ln hist:record historiography.archive sys:is_a
set.add name="ontology.historiography" id="hist:record"

def "hist:recurrence" "Reappearance of patterns, events, or structures across historical time."
ln hist:recurrence historiography.temporality sys:is_a
ln hist:recurrence repeat @related_to
set.add name="ontology.historiography" id="hist:recurrence"

def "hist:renaissance" "Period associated with revival of classical learning, art, and humanism."
ln hist:renaissance historiography.period sys:is_a
ln hist:renaissance phil:humanism @supports
set.add name="ontology.historiography" id="hist:renaissance"

def "hist:revisionism" "Reinterpretation of historical narratives through new evidence or perspectives."
ln hist:revisionism historiography.method sys:is_a
ln hist:revisionism phil:critique @uses
ln hist:revisionism phil:dialectic @may_use
ln hist:revisionism hist:canonization @challenges
ln hist:revisionism meta:disputed @may_be
set.add name="ontology.historiography" id="hist:revisionism"

def "hist:rupture" "Break or discontinuity separating historical periods or meanings."
ln hist:rupture historiography.temporality sys:is_a
ln hist:rupture hist:continuity @contrasts_with
ln hist:rupture nar:apocalypse @resembles
set.add name="ontology.historiography" id="hist:rupture"

def "hist:sovereignty" "Supreme political authority over territory, law, or governance."
ln hist:sovereignty historiography.power sys:is_a
ln hist:sovereignty civ:official @embodied_by
set.add name="ontology.historiography" id="hist:sovereignty"

def "hist:teleology" "Interpretation of history as moving toward predetermined ends or purposes."
ln hist:teleology historiography.method sys:is_a
ln hist:teleology fate @related_to
ln hist:teleology nar:quest @structures
set.add name="ontology.historiography" id="hist:teleology"

def "hist:testimony" "Witness account contributing to historical understanding or evidence."
ln hist:testimony historiography.archive sys:is_a
ln hist:testimony rhet:evidence @functions_as
ln hist:testimony meta:testimony sys:same_as
set.add name="ontology.historiography" id="hist:testimony"

def "hist:trace" "Residual mark or fragment through which the past becomes inferable."
ln hist:trace historiography.archive sys:is_a
ln hist:trace sem:index @resembles
ln hist:trace phil:evidence @supports
ln hist:trace anth:trace sys:same_as
set.add name="ontology.historiography" id="hist:trace"
