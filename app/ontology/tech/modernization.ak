# Akasha ontology — namespace: modernization
# atoms: 31

def "modernization.architecture" "Target architecture design including microservices, cloud-native, and event-driven models."
ln modernization.architecture ont.system_modernization sys:part_of
set.add name="ontology.system_modernization" id="modernization.architecture"

def "modernization.assessment" "Assessment of legacy systems including technical debt, architecture review, and business-process analysis."
ln modernization.assessment ont.system_modernization sys:part_of
set.add name="ontology.system_modernization" id="modernization.assessment"

def "modernization.data" "Data migration, quality improvement, lineage, and synchronization strategies."
ln modernization.data ont.system_modernization sys:part_of
set.add name="ontology.system_modernization" id="modernization.data"

def "modernization.governance" "Governance, risk management, compliance, and modernization KPIs."
ln modernization.governance ont.system_modernization sys:part_of
set.add name="ontology.system_modernization" id="modernization.governance"

def "modernization.migration" "Migration strategies including rehost, refactor, rearchitect, and strangler patterns."
ln modernization.migration ont.system_modernization sys:part_of
set.add name="ontology.system_modernization" id="modernization.migration"

def "modernization.operation" "Operational modernization including SRE, automation, monitoring, and DevOps."
ln modernization.operation ont.system_modernization sys:part_of
set.add name="ontology.system_modernization" id="modernization.operation"

def "modernization.organization" "Organizational transformation including team structure, skills, and change management."
ln modernization.organization ont.system_modernization sys:part_of
set.add name="ontology.system_modernization" id="modernization.organization"

def "modernization:architecture_review" "Evaluation of current architecture and dependencies."
ln modernization:architecture_review modernization.assessment sys:is_a
set.add name="ontology.system_modernization" id="modernization:architecture_review"

def "modernization:automation" "Automation of deployment, testing, and operations."
ln modernization:automation modernization.operation sys:is_a
set.add name="ontology.system_modernization" id="modernization:automation"

def "modernization:business_process_analysis" "Analysis of business workflows and system alignment."
ln modernization:business_process_analysis modernization.assessment sys:is_a
set.add name="ontology.system_modernization" id="modernization:business_process_analysis"

def "modernization:cdc" "Change Data Capture for real-time sync."
ln modernization:cdc modernization.data sys:is_a
ln modernization:cdc modernization:event_driven @supports
set.add name="ontology.system_modernization" id="modernization:cdc"

def "modernization:change_management" "Organizational change management."
ln modernization:change_management modernization.organization sys:is_a
ln modernization:change_management modernization:risk_management @influences
set.add name="ontology.system_modernization" id="modernization:change_management"

def "modernization:cloud_native" "Cloud-native design principles."
ln modernization:cloud_native modernization.architecture sys:is_a
set.add name="ontology.system_modernization" id="modernization:cloud_native"

def "modernization:compliance" "Compliance with standards and regulations."
ln modernization:compliance modernization.governance sys:is_a
set.add name="ontology.system_modernization" id="modernization:compliance"

def "modernization:data_migration" "Data migration as part of system modernization programs."
ln modernization:data_migration ont.data_migration sys:related_to
set.add name="ontology.data_migration" id="modernization:data_migration"

def "modernization:data_quality" "Data quality improvement and cleansing."
ln modernization:data_quality modernization.data sys:is_a
set.add name="ontology.system_modernization" id="modernization:data_quality"

def "modernization:etl" "Extract-Transform-Load processes."
ln modernization:etl modernization.data sys:is_a
set.add name="ontology.system_modernization" id="modernization:etl"

def "modernization:event_driven" "Event-driven architecture."
ln modernization:event_driven modernization.architecture sys:is_a
set.add name="ontology.system_modernization" id="modernization:event_driven"

def "modernization:kpi" "Modernization KPIs and metrics."
ln modernization:kpi modernization.governance sys:is_a
set.add name="ontology.system_modernization" id="modernization:kpi"

def "modernization:microservices" "Microservices-based target architecture."
ln modernization:microservices modernization.architecture sys:is_a
set.add name="ontology.system_modernization" id="modernization:microservices"

def "modernization:monitoring" "Unified monitoring and observability."
ln modernization:monitoring modernization.operation sys:is_a
set.add name="ontology.system_modernization" id="modernization:monitoring"

def "modernization:rearchitect" "Architectural transformation."
ln modernization:rearchitect modernization.migration sys:is_a
set.add name="ontology.system_modernization" id="modernization:rearchitect"

def "modernization:refactor" "Code restructuring."
ln modernization:refactor modernization.migration sys:is_a
set.add name="ontology.system_modernization" id="modernization:refactor"

def "modernization:rehost" "Lift-and-shift migration."
ln modernization:rehost modernization.migration sys:is_a
set.add name="ontology.system_modernization" id="modernization:rehost"

def "modernization:replatform" "Platform upgrade with minimal code change."
ln modernization:replatform modernization.migration sys:is_a
set.add name="ontology.system_modernization" id="modernization:replatform"

def "modernization:risk_management" "Risk management for modernization programs."
ln modernization:risk_management modernization.governance sys:is_a
set.add name="ontology.system_modernization" id="modernization:risk_management"

def "modernization:skill_shift" "Skill transformation from legacy to modern technologies."
ln modernization:skill_shift modernization.organization sys:is_a
set.add name="ontology.system_modernization" id="modernization:skill_shift"

def "modernization:sre" "Site Reliability Engineering practices."
ln modernization:sre modernization.operation sys:is_a
ln modernization:sre modernization:cloud_native @aligned_with
set.add name="ontology.system_modernization" id="modernization:sre"

def "modernization:strangler" "Strangler Fig incremental replacement pattern."
ln modernization:strangler modernization.migration sys:is_a
ln modernization:strangler modernization:microservices @enables
set.add name="ontology.system_modernization" id="modernization:strangler"

def "modernization:team_structure" "Team structure transformation including cross-functional teams."
ln modernization:team_structure modernization.organization sys:is_a
set.add name="ontology.system_modernization" id="modernization:team_structure"

def "modernization:technical_debt" "Accumulated complexity and outdated components increasing maintenance cost."
ln modernization:technical_debt modernization.assessment sys:is_a
ln modernization:technical_debt modernization:refactor @motivates
set.add name="ontology.system_modernization" id="modernization:technical_debt"
