# Akasha ontology — namespace: org
# atoms: 31

def "org:accountability" "Ownership of outcomes and responsibilities."
ln org:accountability organization.structure sys:is_a
set.add name="ontology.organization" id="org:accountability"

def "org:autonomy" "Freedom to make decisions about one's work."
ln org:autonomy organization.motivation sys:is_a
set.add name="ontology.organization" id="org:autonomy"

def "org:burnout" "State of emotional, mental, and physical exhaustion."
ln org:burnout organization.motivation sys:is_a
ln org:burnout org:engagement @contrasts_with
set.add name="ontology.organization" id="org:burnout"

def "org:coaching" "Supporting others' growth through guidance and feedback."
ln org:coaching organization.leadership sys:is_a
ln org:coaching org:mastery @supports
set.add name="ontology.organization" id="org:coaching"

def "org:collaboration" "Active cooperation toward shared outcomes."
ln org:collaboration organization.teamwork sys:is_a
set.add name="ontology.organization" id="org:collaboration"

def "org:communication" "Exchange of information to coordinate and collaborate."
ln org:communication organization.teamwork sys:is_a
ln org:communication org:collaboration @supports
set.add name="ontology.organization" id="org:communication"

def "org:conflict_resolution" "Processes for resolving disagreements constructively."
ln org:conflict_resolution organization.teamwork sys:is_a
set.add name="ontology.organization" id="org:conflict_resolution"

def "org:decision_making" "Processes for selecting actions among alternatives."
ln org:decision_making organization.leadership sys:is_a
set.add name="ontology.organization" id="org:decision_making"

def "org:delegation" "Assigning responsibility and authority to others."
ln org:delegation organization.leadership sys:is_a
ln org:delegation org:autonomy @enables
set.add name="ontology.organization" id="org:delegation"

def "org:diversity_inclusion" "Practices promoting diverse perspectives and equitable participation."
ln org:diversity_inclusion organization.culture sys:is_a
set.add name="ontology.organization" id="org:diversity_inclusion"

def "org:engagement" "Level of enthusiasm and commitment toward work."
ln org:engagement organization.motivation sys:is_a
set.add name="ontology.organization" id="org:engagement"

def "org:extrinsic_motivation" "Motivation driven by external rewards or pressures."
ln org:extrinsic_motivation organization.motivation sys:is_a
set.add name="ontology.organization" id="org:extrinsic_motivation"

def "org:flat_structure" "An organization with minimal hierarchical layers."
ln org:flat_structure organization.structure sys:is_a
set.add name="ontology.organization" id="org:flat_structure"

def "org:hierarchy" "A layered structure of authority and responsibility."
ln org:hierarchy organization.structure sys:is_a
set.add name="ontology.organization" id="org:hierarchy"

def "org:intrinsic_motivation" "Motivation driven by internal satisfaction and interest."
ln org:intrinsic_motivation organization.motivation sys:is_a
set.add name="ontology.organization" id="org:intrinsic_motivation"

def "org:mastery" "Desire to improve skills and achieve excellence."
ln org:mastery organization.motivation sys:is_a
set.add name="ontology.organization" id="org:mastery"

def "org:matrix_structure" "A structure where individuals report to multiple managers."
ln org:matrix_structure organization.structure sys:is_a
set.add name="ontology.organization" id="org:matrix_structure"

def "org:mission" "The organization's fundamental purpose."
ln org:mission organization.culture sys:is_a
ln org:mission org:purpose @supports
set.add name="ontology.organization" id="org:mission"

def "org:norms" "Shared expectations for behavior within the organization."
ln org:norms organization.culture sys:is_a
set.add name="ontology.organization" id="org:norms"

def "org:onboarding" "Process of integrating new members into the organization."
ln org:onboarding organization.culture sys:is_a
set.add name="ontology.organization" id="org:onboarding"

def "org:psychological_safety" "A shared belief that the team is safe for interpersonal risk-taking."
ln org:psychological_safety organization.teamwork sys:is_a
ln org:psychological_safety org:trust @supports
set.add name="ontology.organization" id="org:psychological_safety"

def "org:purpose" "Sense of meaning and contribution in one's work."
ln org:purpose organization.motivation sys:is_a
set.add name="ontology.organization" id="org:purpose"

def "org:rituals" "Repeated practices that reinforce culture."
ln org:rituals organization.culture sys:is_a
set.add name="ontology.organization" id="org:rituals"

def "org:role_clarity" "Clear understanding of one's responsibilities and expectations."
ln org:role_clarity organization.structure sys:is_a
set.add name="ontology.organization" id="org:role_clarity"

def "org:servant_leadership" "Leadership focused on serving and empowering others."
ln org:servant_leadership organization.leadership sys:is_a
set.add name="ontology.organization" id="org:servant_leadership"

def "org:shared_goals" "Common objectives that align team members."
ln org:shared_goals organization.teamwork sys:is_a
ln org:shared_goals organization.teamwork @supports
set.add name="ontology.organization" id="org:shared_goals"

def "org:situational_leadership" "Leadership style that adapts to team maturity and context."
ln org:situational_leadership organization.leadership sys:is_a
set.add name="ontology.organization" id="org:situational_leadership"

def "org:transformational_leadership" "Leadership that inspires change through vision and motivation."
ln org:transformational_leadership organization.leadership sys:is_a
ln org:transformational_leadership org:engagement @enables
set.add name="ontology.organization" id="org:transformational_leadership"

def "org:trust" "The degree of confidence team members have in each other's reliability and integrity."
ln org:trust organization.teamwork sys:is_a
set.add name="ontology.organization" id="org:trust"

def "org:united_nations" "United Nations — intergovernmental organisation founded 1945; 193 member states; primary mission: international peace, security, and cooperation."
ln org:united_nations ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="org:united_nations"

def "org:values" "Core principles guiding behavior and decisions."
ln org:values organization.culture sys:is_a
set.add name="ontology.organization" id="org:values"
