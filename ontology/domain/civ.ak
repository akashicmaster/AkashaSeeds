# Akasha ontology — namespace: civ
# atoms: 36

def "civ:accessibility" "Ease with which people can understand, enter, use, or participate in a public process or service."
ln civ:accessibility public.participation sys:is_a
ln civ:accessibility civ:briefing @improves
ln civ:accessibility civ:representation @supports
set.add name="ontology.public" id="civ:accessibility"

def "civ:appeal" "Formal request to review, revise, or overturn a decision."
ln civ:appeal public.accountability sys:is_a
ln civ:appeal civ:policy_proposal @challenges
ln civ:appeal public.accountability @uses
set.add name="ontology.public" id="civ:appeal"

def "civ:briefing" "Session where officials explain issues or plans."
ln civ:briefing public.deliberation sys:is_a
ln civ:briefing civ:policy_proposal @explains
ln civ:briefing civ:public_trust @supports
set.add name="ontology.public" id="civ:briefing"

def "civ:cluster" "Group of similar opinions or responses."
ln civ:cluster public.aggregation sys:is_a
ln civ:cluster civ:topic @emerges_from
set.add name="ontology.public" id="civ:cluster"

def "civ:comment" "Free-text citizen opinion or feedback."
ln civ:comment public.opinion sys:is_a
ln civ:comment civ:topic @classified_as
ln civ:comment civ:sentiment @expresses
set.add name="ontology.public" id="civ:comment"

def "civ:complaint" "Expression of dissatisfaction, harm, procedural concern, or request for correction."
ln civ:complaint public.accountability sys:is_a
ln civ:complaint civ:comment @is_a_type_of
ln civ:complaint civ:policy_revision @may_trigger
set.add name="ontology.public" id="civ:complaint"

def "civ:consensus" "Broad agreement or acceptable convergence among participants after discussion or negotiation."
ln civ:consensus public.legitimacy sys:is_a
ln civ:consensus public.deliberation @emerges_from
set.add name="ontology.public" id="civ:consensus"

def "civ:evidence" "Document, data, testimony, or observation used to support a public claim, proposal, or assessment."
ln civ:evidence public.transparency sys:is_a
set.add name="ontology.public" id="civ:evidence"

def "civ:explanation" "Plain-language account of a policy, decision, method, or trade-off."
ln civ:explanation public.transparency sys:is_a
ln civ:explanation civ:briefing @used_in
set.add name="ontology.public" id="civ:explanation"

def "civ:facilitation" "Process of guiding group discussion."
ln civ:facilitation public.deliberation sys:is_a
ln civ:facilitation civ:consensus @supports
set.add name="ontology.public" id="civ:facilitation"

def "civ:fairness" "Perceived and procedural fairness in public decision-making and resource allocation."
ln civ:fairness public.legitimacy sys:is_a
ln civ:fairness civ:public_trust @supports
set.add name="ontology.public" id="civ:fairness"

def "civ:impact_assessment" "Evaluation of expected effects of a policy."
ln civ:impact_assessment public.policy sys:is_a
ln civ:impact_assessment civ:evidence @requires
set.add name="ontology.public" id="civ:impact_assessment"

def "civ:implementation" "Execution phase of a policy or plan."
ln civ:implementation public.policy sys:is_a
ln civ:implementation civ:policy_proposal @follows
set.add name="ontology.public" id="civ:implementation"

def "civ:minority_view" "Opinion or concern held by a smaller group that may be lost in majority aggregation."
ln civ:minority_view public.opinion sys:is_a
ln civ:minority_view civ:fairness @requires_attention
ln civ:minority_view civ:summary @may_be_hidden_by
set.add name="ontology.public" id="civ:minority_view"

def "civ:ngo" "Non-governmental organization participating in civic processes."
ln civ:ngo public.community sys:is_a
set.add name="ontology.public" id="civ:ngo"

def "civ:official" "Government staff or elected representative."
ln civ:official public.community sys:is_a
set.add name="ontology.public" id="civ:official"

def "civ:open_data" "Publicly accessible data released for inspection, reuse, analysis, or accountability."
ln civ:open_data public.transparency sys:is_a
ln civ:open_data civ:statistic @supports
ln civ:open_data civ:traceability @enables
set.add name="ontology.public" id="civ:open_data"

def "civ:policy_option" "Alternative solution considered during policy design."
ln civ:policy_option public.policy sys:is_a
set.add name="ontology.public" id="civ:policy_option"

def "civ:policy_proposal" "Draft plan or recommendation for public action."
ln civ:policy_proposal public.policy sys:is_a
ln civ:policy_proposal civ:summary @based_on
ln civ:policy_proposal civ:impact_assessment @requires
ln civ:policy_proposal civ:evidence @based_on
set.add name="ontology.public" id="civ:policy_proposal"

def "civ:policy_revision" "Modification of a proposal, option, or implemented policy based on evidence, feedback, review, or changed conditions."
ln civ:policy_revision public.policy sys:is_a
ln civ:policy_revision civ:complaint @may_respond_to
ln civ:policy_revision civ:impact_assessment @informed_by
set.add name="ontology.public" id="civ:policy_revision"

def "civ:public_hearing" "Formal meeting where residents express opinions."
ln civ:public_hearing public.deliberation sys:is_a
ln civ:public_hearing civ:summary @informed_by
ln civ:public_hearing public.participation @enables
set.add name="ontology.public" id="civ:public_hearing"

def "civ:public_trust" "Confidence that public institutions, processes, or decisions are fair, reliable, and accountable."
ln civ:public_trust public.legitimacy sys:is_a
set.add name="ontology.public" id="civ:public_trust"

def "civ:questionnaire" "Structured set of questions used to collect public input."
ln civ:questionnaire public.survey sys:is_a
set.add name="ontology.public" id="civ:questionnaire"

def "civ:representation" "Degree to which affected groups, residents, or interests are present in the process."
ln civ:representation public.participation sys:is_a
ln civ:representation civ:sample @affects
set.add name="ontology.public" id="civ:representation"

def "civ:resident" "Person living in the jurisdiction."
ln civ:resident public.community sys:is_a
set.add name="ontology.public" id="civ:resident"

def "civ:response" "Answer submitted by a participant."
ln civ:response public.survey sys:is_a
ln civ:response civ:comment @refers_to
ln civ:response civ:sample @comes_from
set.add name="ontology.public" id="civ:response"

def "civ:responsibility" "Assigned duty or ownership for an action, decision, process, or outcome."
ln civ:responsibility public.accountability sys:is_a
ln civ:responsibility civ:official @assigned_to
set.add name="ontology.public" id="civ:responsibility"

def "civ:sample" "Group of respondents selected for a survey."
ln civ:sample public.survey sys:is_a
set.add name="ontology.public" id="civ:sample"

def "civ:sentiment" "Emotional tone or attitude expressed in opinions."
ln civ:sentiment public.opinion sys:is_a
set.add name="ontology.public" id="civ:sentiment"

def "civ:stakeholder_map" "Structured map of affected parties, interests, influence, relationships, and responsibilities."
ln civ:stakeholder_map public.community sys:is_a
ln civ:stakeholder_map civ:resident @includes
ln civ:stakeholder_map civ:ngo @includes
ln civ:stakeholder_map civ:official @includes
ln civ:stakeholder_map public.policy @informs
set.add name="ontology.public" id="civ:stakeholder_map"

def "civ:statistic" "Numerical measure derived from survey data."
ln civ:statistic public.aggregation sys:is_a
set.add name="ontology.public" id="civ:statistic"

def "civ:summary" "Condensed representation of multiple opinions."
ln civ:summary public.aggregation sys:is_a
ln civ:summary civ:cluster @derived_from
ln civ:summary civ:explanation @supports
set.add name="ontology.public" id="civ:summary"

def "civ:survey_item" "Individual question or prompt within a survey."
ln civ:survey_item public.survey sys:is_a
set.add name="ontology.public" id="civ:survey_item"

def "civ:topic" "Thematic category representing a public issue."
ln civ:topic public.opinion sys:is_a
set.add name="ontology.public" id="civ:topic"

def "civ:traceability" "Ability to follow a decision back through evidence, comments, summaries, assumptions, and responsible actors."
ln civ:traceability public.transparency sys:is_a
ln civ:traceability civ:policy_proposal @supports
ln civ:traceability public.accountability @supports
set.add name="ontology.public" id="civ:traceability"

def "civ:trend" "Pattern or directional change observed over time."
ln civ:trend public.aggregation sys:is_a
ln civ:trend civ:statistic @derived_from
set.add name="ontology.public" id="civ:trend"
