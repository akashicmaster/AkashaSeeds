# Akasha ontology — namespace: nar
# atoms: 46

def "nar:apocalypse" "Apocalypse: unveiling and/or destruction of an existing world order, often accompanied by judgment, catastrophe, or renewal."
ln nar:apocalypse narrative.typology.society sys:is_a
ln nar:apocalypse narrative.typology.revelation @also_belongs_to
ln nar:apocalypse narrative.typology.revelation @literalizes
set.add name="ontology.narrative_typology" id="nar:apocalypse"

def "nar:betrayal" "Betrayal: violation of trust, oath, kinship, loyalty, secrecy, or shared cause."
ln nar:betrayal narrative.typology.conflict sys:is_a
ln nar:betrayal nar:revenge @may_cause
set.add name="ontology.narrative_typology" id="nar:betrayal"

def "nar:bolero_crescendo" "Small repetitions accumulate weight."
ln nar:bolero_crescendo narrative.bolero sys:is_a
ln nar:bolero_crescendo nar:bolero_resolution @then
set.add name="ontology.narrative" id="nar:bolero_crescendo"

def "nar:bolero_resolution" "The motif resolves quietly; its significance withheld, then admitted."
ln nar:bolero_resolution narrative.bolero sys:is_a
ln nar:bolero_resolution emo:trust @reads_as
set.add name="ontology.narrative" id="nar:bolero_resolution"

def "nar:bolero_theme" "A motif is stated plainly."
ln nar:bolero_theme narrative.bolero sys:is_a
ln nar:bolero_theme nar:bolero_variation @then
set.add name="ontology.narrative" id="nar:bolero_theme"

def "nar:bolero_variation" "The motif returns changed."
ln nar:bolero_variation narrative.bolero sys:is_a
ln nar:bolero_variation nar:bolero_crescendo @then
set.add name="ontology.narrative" id="nar:bolero_variation"

def "nar:comedy" "Comedy: narrative movement from confusion, blockage, disorder, or separation toward renewal, union, restoration, or social reintegration."
ln nar:comedy narrative.typology.fall_rise sys:is_a
ln nar:comedy nar:tragedy @contrasts_with
ln nar:comedy nar:reconciliation @often_ends_in
ln nar:comedy plot:comedy sys:same_as
set.add name="ontology.narrative_typology" id="nar:comedy"

def "nar:coming_of_age" "Coming of Age: transition from childhood, innocence, ignorance, or dependence into adult knowledge, responsibility, or identity."
ln nar:coming_of_age narrative.typology.transformation sys:is_a
ln nar:coming_of_age civ:responsibility @introduces
set.add name="ontology.narrative_typology" id="nar:coming_of_age"

def "nar:conversion" "Conversion: profound change of belief, loyalty, worldview, faith, or moral orientation."
ln nar:conversion narrative.typology.transformation sys:is_a
ln nar:conversion truth @reorients_toward
set.add name="ontology.narrative_typology" id="nar:conversion"

def "nar:dystopia" "Dystopia: narrative imagining a damaged, oppressive, dehumanizing, or failed social order."
ln nar:dystopia narrative.typology.society sys:is_a
ln nar:dystopia nar:utopia @contrasts_with
ln nar:dystopia warning @functions_as
set.add name="ontology.narrative_typology" id="nar:dystopia"

def "nar:exile" "Exile: forced or painful departure from home, status, community, or origin, often producing longing, identity change, or return desire."
ln nar:exile narrative.typology.journey sys:is_a
ln nar:exile memory @evokes
set.add name="ontology.narrative_typology" id="nar:exile"

def "nar:fall" "Fall: descent from innocence, power, virtue, order, grace, prosperity, or legitimacy into loss or corruption."
ln nar:fall narrative.typology.fall_rise sys:is_a
ln nar:fall nar:tragedy @can_lead_to
ln nar:fall nar:redemption @may_be_answered_by
set.add name="ontology.narrative_typology" id="nar:fall"

def "nar:foundation" "Foundation: origin story of a city, people, institution, law, dynasty, covenant, or world order."
ln nar:foundation narrative.typology.society sys:is_a
ln nar:foundation myth @often_takes_form_of
set.add name="ontology.narrative_typology" id="nar:foundation"

def "nar:initiation" "Initiation: passage through trial, secrecy, teaching, ritual, or danger into a new social or symbolic status."
ln nar:initiation narrative.typology.transformation sys:is_a
ln nar:initiation nar:coming_of_age @related_to
ln nar:initiation ritual @uses
set.add name="ontology.narrative_typology" id="nar:initiation"

def "nar:journal_consequence" "The understanding changes an action, however small."
ln nar:journal_consequence narrative.journal sys:is_a
set.add name="ontology.narrative" id="nar:journal_consequence"

def "nar:journal_echo" "The observation recurs, slightly altered; a pattern begins."
ln nar:journal_echo narrative.journal sys:is_a
ln nar:journal_echo nar:journal_insight @then
set.add name="ontology.narrative" id="nar:journal_echo"

def "nar:journal_insight" "The pattern resolves into understanding."
ln nar:journal_insight narrative.journal sys:is_a
ln nar:journal_insight nar:journal_consequence @then
set.add name="ontology.narrative" id="nar:journal_insight"

def "nar:journal_observation" "A plain observation is recorded without judgement."
ln nar:journal_observation narrative.journal sys:is_a
ln nar:journal_observation nar:journal_echo @then
set.add name="ontology.narrative" id="nar:journal_observation"

def "nar:magic_expectation" "A promise is felt; something is expected to happen."
ln nar:magic_expectation narrative.magic sys:is_a
ln nar:magic_expectation nar:magic_silence @then
ln nar:magic_expectation emo:anticipation @reads_as
set.add name="ontology.narrative" id="nar:magic_expectation"

def "nar:magic_revelation" "The change was internal all along; the reader sees it first."
ln nar:magic_revelation narrative.magic sys:is_a
ln nar:magic_revelation nar:magic_transfer @then
ln nar:magic_revelation emo:joy @reads_as
set.add name="ontology.narrative" id="nar:magic_revelation"

def "nar:magic_silence" "Nothing overt happens; the promise stays unspoken."
ln nar:magic_silence narrative.magic sys:is_a
ln nar:magic_silence nar:magic_revelation @then
set.add name="ontology.narrative" id="nar:magic_silence"

def "nar:magic_transfer" "The medium goes blank and the gift flows onward."
ln nar:magic_transfer narrative.magic sys:is_a
set.add name="ontology.narrative" id="nar:magic_transfer"

def "nar:metamorphosis" "Metamorphosis: bodily, spiritual, social, or symbolic transformation into another form or identity."
ln nar:metamorphosis narrative.typology.transformation sys:is_a
ln nar:metamorphosis identity @alters
set.add name="ontology.narrative_typology" id="nar:metamorphosis"

def "nar:mystery" "Mystery: narrative structured around concealed causes, missing knowledge, hidden agents, or unresolved events."
ln nar:mystery narrative.typology.revelation sys:is_a
ln nar:mystery nar:unmasking @resolved_by
set.add name="ontology.narrative_typology" id="nar:mystery"

def "nar:pilgrimage" "Pilgrimage: a journey toward a sacred, moral, ancestral, or symbolic destination that transforms the traveller."
ln nar:pilgrimage narrative.typology.journey sys:is_a
ln nar:pilgrimage nar:quest @related_to
ln nar:pilgrimage nar:conversion @may_cause
set.add name="ontology.narrative_typology" id="nar:pilgrimage"

def "nar:plot_bloom" "The latent element finally acts."
ln nar:plot_bloom narrative.plot sys:is_a
set.add name="ontology.narrative" id="nar:plot_bloom"

def "nar:plot_dormant" "The seed lies unremarked for a long stretch."
ln nar:plot_dormant narrative.plot sys:is_a
ln nar:plot_dormant nar:plot_bloom @then
set.add name="ontology.narrative" id="nar:plot_dormant"

def "nar:plot_seed" "A latent element is planted (e.g. an inherited gift)."
ln nar:plot_seed narrative.plot sys:is_a
ln nar:plot_seed nar:plot_dormant @then
ln nar:plot_seed emo:nostalgia @reads_as
set.add name="ontology.narrative" id="nar:plot_seed"

def "nar:prophecy" "Prophecy: narrative shaped by foretelling, fate, warning, divine message, or future obligation."
ln nar:prophecy narrative.typology.revelation sys:is_a
ln nar:prophecy fate @concerns
set.add name="ontology.narrative_typology" id="nar:prophecy"

def "nar:quest" "Quest: a narrative in which a protagonist seeks a person, object, place, truth, cure, or sacred goal through trials."
ln nar:quest narrative.typology.journey sys:is_a
ln nar:quest nar:sacrifice @may_require
ln nar:quest nar:recognition @may_lead_to
ln nar:quest plot:the_quest sys:same_as
set.add name="ontology.narrative_typology" id="nar:quest"

def "nar:rebellion" "Rebellion: resistance against authority, empire, law, hierarchy, divine order, or inherited constraint."
ln nar:rebellion narrative.typology.conflict sys:is_a
ln nar:rebellion narrative.typology.society @concerns
ln nar:rebellion nar:restoration @seeks
set.add name="ontology.narrative_typology" id="nar:rebellion"

def "nar:rebirth" "Rebirth: renewal after deathlike suspension, defeat, despair, winter, curse, illness, or symbolic burial."
ln nar:rebirth narrative.typology.fall_rise sys:is_a
ln nar:rebirth nar:redemption @related_to
ln nar:rebirth plot:rebirth sys:same_as
set.add name="ontology.narrative_typology" id="nar:rebirth"

def "nar:recognition" "Recognition: discovery of true identity, kinship, guilt, meaning, or hidden relation."
ln nar:recognition narrative.typology.revelation sys:is_a
ln nar:recognition identity @reveals
set.add name="ontology.narrative_typology" id="nar:recognition"

def "nar:reconciliation" "Reconciliation: restoration of relationship, trust, social bond, family order, or political peace after conflict."
ln nar:reconciliation narrative.typology.society sys:is_a
ln nar:reconciliation narrative.typology.conflict @resolves
set.add name="ontology.narrative_typology" id="nar:reconciliation"

def "nar:redemption" "Redemption: restoration of moral, social, spiritual, or personal value after guilt, failure, exile, or fall."
ln nar:redemption narrative.typology.transformation sys:is_a
ln nar:redemption narrative.typology.fall_rise @related_to
set.add name="ontology.narrative_typology" id="nar:redemption"

def "nar:restoration" "Restoration: recovery of rightful order, authority, home, justice, memory, or social balance after disruption."
ln nar:restoration narrative.typology.fall_rise sys:is_a
ln nar:restoration nar:return @related_to
set.add name="ontology.narrative_typology" id="nar:restoration"

def "nar:return" "Return: movement back to an origin, home, rightful place, memory, or lost order after absence or transformation."
ln nar:return narrative.typology.journey sys:is_a
ln nar:return nar:exile @resolves
ln nar:return nar:restoration @supports
set.add name="ontology.narrative_typology" id="nar:return"

def "nar:revenge" "Revenge: a narrative driven by retaliation for injury, betrayal, murder, dishonor, or injustice."
ln nar:revenge narrative.typology.conflict sys:is_a
set.add name="ontology.narrative_typology" id="nar:revenge"

def "nar:rivalry" "Rivalry: sustained competition between characters, groups, siblings, lovers, institutions, or ideals."
ln nar:rivalry narrative.typology.conflict sys:is_a
ln nar:rivalry nar:tragedy @may_lead_to
set.add name="ontology.narrative_typology" id="nar:rivalry"

def "nar:sacrifice" "Sacrifice: voluntary or forced loss of life, desire, status, possession, or future for a higher value or communal need."
ln nar:sacrifice narrative.typology.conflict sys:is_a
ln nar:sacrifice nar:redemption @may_enable
set.add name="ontology.narrative_typology" id="nar:sacrifice"

def "nar:succession" "Succession: transfer or contest of authority, inheritance, kingship, office, legitimacy, or lineage."
ln nar:succession narrative.typology.society sys:is_a
ln nar:succession public.legitimacy @concerns
set.add name="ontology.narrative_typology" id="nar:succession"

def "nar:testimony" "Testimony: narrative organized around witness, memory, account-giving, evidence, or contested truth."
ln nar:testimony narrative.typology.revelation sys:is_a
ln nar:testimony memory @depends_on
ln nar:testimony truth @claims
set.add name="ontology.narrative_typology" id="nar:testimony"

def "nar:tragedy" "Tragedy: narrative of irreversible loss, downfall, fatal conflict, or destruction of value through action and necessity."
ln nar:tragedy narrative.typology.fall_rise sys:is_a
ln nar:tragedy nar:sacrifice @may_include
ln nar:tragedy plot:tragedy sys:same_as
set.add name="ontology.narrative_typology" id="nar:tragedy"

def "nar:unmasking" "Unmasking: exposure of deception, disguise, false identity, hidden motive, corruption, or illusion."
ln nar:unmasking narrative.typology.revelation sys:is_a
ln nar:unmasking nar:recognition @related_to
set.add name="ontology.narrative_typology" id="nar:unmasking"

def "nar:utopia" "Utopia: narrative imagining an ideal social order, alternative community, perfected institution, or transformed world."
ln nar:utopia narrative.typology.society sys:is_a
ln nar:utopia desire @expresses
set.add name="ontology.narrative_typology" id="nar:utopia"

def "nar:voyage_and_return" "Voyage and Return: a narrative in which a character enters an unfamiliar world, undergoes disorientation or trial, and returns changed."
ln nar:voyage_and_return narrative.typology.journey sys:is_a
ln nar:voyage_and_return narrative.typology.transformation @enables
ln nar:voyage_and_return plot:voyage_and_return sys:same_as
set.add name="ontology.narrative_typology" id="nar:voyage_and_return"
