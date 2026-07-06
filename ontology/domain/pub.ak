# Akasha ontology — namespace: pub
# atoms: 26

def "pub:advocacy" "Efforts to influence public policy or opinion."
ln pub:advocacy publicity.stakeholder sys:is_a
set.add name="ontology.publicity" id="pub:advocacy"

def "pub:apology_strategy" "Structured approach to issuing apologies effectively."
ln pub:apology_strategy publicity.crisis sys:is_a
set.add name="ontology.publicity" id="pub:apology_strategy"

def "pub:briefing" "Structured communication session providing essential information."
ln pub:briefing publicity.communication sys:is_a
set.add name="ontology.publicity" id="pub:briefing"

def "pub:community_relations" "Building positive relationships with local communities."
ln pub:community_relations publicity.stakeholder sys:is_a
set.add name="ontology.publicity" id="pub:community_relations"

def "pub:corporate_citizenship" "Organization's role and responsibility within society."
ln pub:corporate_citizenship publicity.stakeholder sys:is_a
set.add name="ontology.publicity" id="pub:corporate_citizenship"

def "pub:credibility" "Perceived trustworthiness and expertise."
ln pub:credibility publicity.reputation sys:is_a
ln pub:credibility pub:sentiment @influences
set.add name="ontology.publicity" id="pub:credibility"

def "pub:crisis_communication" "Communication strategies during emergencies or reputational threats."
ln pub:crisis_communication publicity.crisis sys:is_a
ln pub:crisis_communication pub:transparency @supports
set.add name="ontology.publicity" id="pub:crisis_communication"

def "pub:damage_control" "Actions taken to limit negative impact on reputation."
ln pub:damage_control publicity.crisis sys:is_a
ln pub:damage_control pub:apology_strategy @related_to
set.add name="ontology.publicity" id="pub:damage_control"

def "pub:earned_media" "Publicity gained through editorial coverage rather than paid promotion."
ln pub:earned_media publicity.media sys:is_a
set.add name="ontology.publicity" id="pub:earned_media"

def "pub:government_relations" "Engagement with government bodies and regulators."
ln pub:government_relations publicity.stakeholder sys:is_a
ln pub:government_relations pub:advocacy @related_to
set.add name="ontology.publicity" id="pub:government_relations"

def "pub:influencer_relations" "Engagement with individuals who shape public opinion."
ln pub:influencer_relations publicity.reputation sys:is_a
ln pub:influencer_relations pub:social_proof @enhances
set.add name="ontology.publicity" id="pub:influencer_relations"

def "pub:interview" "A conversation with media for publication or broadcast."
ln pub:interview publicity.media sys:is_a
set.add name="ontology.publicity" id="pub:interview"

def "pub:media_pitch" "A proposal sent to journalists suggesting a story idea."
ln pub:media_pitch publicity.media sys:is_a
set.add name="ontology.publicity" id="pub:media_pitch"

def "pub:messaging" "Core ideas communicated to shape public understanding."
ln pub:messaging publicity.communication sys:is_a
ln pub:messaging pub:narrative_framing @supports
set.add name="ontology.publicity" id="pub:messaging"

def "pub:narrative_framing" "Shaping how information is interpreted by audiences."
ln pub:narrative_framing publicity.communication sys:is_a
set.add name="ontology.publicity" id="pub:narrative_framing"

def "pub:news_value" "Qualities that make a topic newsworthy."
ln pub:news_value publicity.media sys:is_a
ln pub:news_value pub:earned_media @enables
set.add name="ontology.publicity" id="pub:news_value"

def "pub:ngo_relations" "Interaction with non-governmental organizations."
ln pub:ngo_relations publicity.stakeholder sys:is_a
set.add name="ontology.publicity" id="pub:ngo_relations"

def "pub:press_relations" "Building and maintaining relationships with journalists."
ln pub:press_relations publicity.media sys:is_a
ln pub:press_relations pub:media_pitch @supports
set.add name="ontology.publicity" id="pub:press_relations"

def "pub:press_release" "Official statement issued to media outlets."
ln pub:press_release publicity.media sys:is_a
set.add name="ontology.publicity" id="pub:press_release"

def "pub:reputation_management" "Managing public perception and long-term credibility."
ln pub:reputation_management publicity.reputation sys:is_a
set.add name="ontology.publicity" id="pub:reputation_management"

def "pub:rumor_management" "Identifying and countering misinformation or rumors."
ln pub:rumor_management publicity.crisis sys:is_a
set.add name="ontology.publicity" id="pub:rumor_management"

def "pub:sentiment" "Emotional tone of public opinion."
ln pub:sentiment publicity.reputation sys:is_a
set.add name="ontology.publicity" id="pub:sentiment"

def "pub:social_proof" "Influence created by others' actions or endorsements."
ln pub:social_proof publicity.reputation sys:is_a
set.add name="ontology.publicity" id="pub:social_proof"

def "pub:spokesperson" "Official representative who communicates with the public or media."
ln pub:spokesperson publicity.communication sys:is_a
set.add name="ontology.publicity" id="pub:spokesperson"

def "pub:talking_points" "Prepared key messages for consistent communication."
ln pub:talking_points publicity.communication sys:is_a
set.add name="ontology.publicity" id="pub:talking_points"

def "pub:transparency" "Open and honest communication to maintain trust."
ln pub:transparency publicity.crisis sys:is_a
set.add name="ontology.publicity" id="pub:transparency"
