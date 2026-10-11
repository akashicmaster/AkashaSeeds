# Akasha ontology — namespace: pm
# atoms: 39

def "pm.constraints" "Scope, time, cost, and related project constraints."
ln pm.constraints ont.project_management sys:part_of
set.add name="ontology.project_management" id="pm.constraints"

def "pm.governance" "Project governance, roles, and decision structures."
ln pm.governance ont.project_management sys:part_of
set.add name="ontology.project_management" id="pm.governance"

def "pm.lifecycle" "Project lifecycle phases from initiation to closure."
ln pm.lifecycle ont.project_management sys:part_of
set.add name="ontology.project_management" id="pm.lifecycle"

def "pm.methodology" "Project management methodologies and delivery frameworks."
ln pm.methodology ont.project_management sys:part_of
set.add name="ontology.project_management" id="pm.methodology"

def "pm.risk_quality" "Risk management, quality management, and assurance."
ln pm.risk_quality ont.project_management sys:part_of
set.add name="ontology.project_management" id="pm.risk_quality"

def "pm.stakeholder" "Stakeholders, communication, and expectations management."
ln pm.stakeholder ont.project_management sys:part_of
set.add name="ontology.project_management" id="pm.stakeholder"

def "pm:agile" "Iterative and incremental approach emphasizing adaptability and collaboration."
ln pm:agile pm.methodology sys:is_a
ln pm:agile pm:iteration @enables
set.add name="ontology.project_management" id="pm:agile"

def "pm:baseline" "Approved version of scope, schedule, and cost used for comparison."
ln pm:baseline pm.lifecycle sys:is_a
ln pm:baseline pm:monitoring_control @enables
set.add name="ontology.project_management" id="pm:baseline"

def "pm:change_control" "Formal process for evaluating and approving changes to baseline."
ln pm:change_control pm.governance sys:is_a
set.add name="ontology.project_management" id="pm:change_control"

def "pm:closure" "Formal completion, handover, and lessons learned."
ln pm:closure pm.lifecycle sys:is_a
set.add name="ontology.project_management" id="pm:closure"

def "pm:communication_plan" "Plan defining what, when, and how information is shared."
ln pm:communication_plan pm.stakeholder sys:is_a
set.add name="ontology.project_management" id="pm:communication_plan"

def "pm:cost" "Budget and financial resources required for the project."
ln pm:cost pm.constraints sys:is_a
set.add name="ontology.project_management" id="pm:cost"

def "pm:execution" "Coordinating people and resources to carry out the plan."
ln pm:execution pm.lifecycle sys:is_a
set.add name="ontology.project_management" id="pm:execution"

def "pm:expectation_management" "Aligning stakeholder expectations with realistic outcomes."
ln pm:expectation_management pm.stakeholder sys:is_a
set.add name="ontology.project_management" id="pm:expectation_management"

def "pm:hybrid" "Combination of predictive and adaptive approaches."
ln pm:hybrid pm.methodology sys:is_a
set.add name="ontology.project_management" id="pm:hybrid"

def "pm:initiation" "Defining the project at a high level and authorizing its start."
ln pm:initiation pm.lifecycle sys:is_a
set.add name="ontology.project_management" id="pm:initiation"

def "pm:iron_triangle" "Interdependent relationship between scope, time, and cost."
ln pm:iron_triangle pm.constraints sys:is_a
ln pm:iron_triangle pm:planning @concerns
set.add name="ontology.project_management" id="pm:iron_triangle"

def "pm:issue_management" "Handling problems that have already occurred."
ln pm:issue_management pm.risk_quality sys:is_a
set.add name="ontology.project_management" id="pm:issue_management"

def "pm:iteration" "Repeated cycle of planning, executing, and reviewing work."
ln pm:iteration pm.methodology sys:is_a
set.add name="ontology.project_management" id="pm:iteration"

def "pm:kanban" "Flow-based method focusing on limiting work in progress and visualizing work."
ln pm:kanban pm.methodology sys:is_a
ln pm:kanban pm:agile @related_to
set.add name="ontology.project_management" id="pm:kanban"

def "pm:monitoring_control" "Tracking progress and performance, managing changes."
ln pm:monitoring_control pm.lifecycle sys:is_a
set.add name="ontology.project_management" id="pm:monitoring_control"

def "pm:planning" "Detailing scope, schedule, cost, and plans for execution and control."
ln pm:planning pm.lifecycle sys:is_a
ln pm:planning pm:baseline @supports
set.add name="ontology.project_management" id="pm:planning"

def "pm:project_charter" "Document that formally authorizes a project and defines high-level objectives."
ln pm:project_charter pm.lifecycle sys:is_a
set.add name="ontology.project_management" id="pm:project_charter"

def "pm:project_manager" "Role responsible for achieving project objectives within constraints."
ln pm:project_manager pm.governance sys:is_a
ln pm:project_manager pm:stakeholder_management @responsible_for
set.add name="ontology.project_management" id="pm:project_manager"

def "pm:project_sponsor" "Executive accountable for project success and providing support."
ln pm:project_sponsor pm.governance sys:is_a
ln pm:project_sponsor pm:project_charter @authorizes
set.add name="ontology.project_management" id="pm:project_sponsor"

def "pm:quality_assurance" "Activities to ensure processes will meet quality standards."
ln pm:quality_assurance pm.risk_quality sys:is_a
ln pm:quality_assurance pm:quality_plan @supports
set.add name="ontology.project_management" id="pm:quality_assurance"

def "pm:quality_control" "Activities to verify deliverables meet quality requirements."
ln pm:quality_control pm.risk_quality sys:is_a
ln pm:quality_control pm:quality_plan @supports
set.add name="ontology.project_management" id="pm:quality_control"

def "pm:quality_plan" "Plan describing quality standards and how they will be met."
ln pm:quality_plan pm.risk_quality sys:is_a
set.add name="ontology.project_management" id="pm:quality_plan"

def "pm:resources" "People, equipment, and materials needed to execute the project."
ln pm:resources pm.constraints sys:is_a
set.add name="ontology.project_management" id="pm:resources"

def "pm:responsibility_matrix" "Matrix clarifying who is responsible, accountable, consulted, and informed."
ln pm:responsibility_matrix pm.governance sys:is_a
set.add name="ontology.project_management" id="pm:responsibility_matrix"

def "pm:risk_management" "Processes for identifying, analyzing, and responding to project risks."
ln pm:risk_management pm.risk_quality sys:is_a
ln pm:risk_management pm:planning @supports
set.add name="ontology.project_management" id="pm:risk_management"

def "pm:risk_register" "Structured list of identified risks, owners, and responses."
ln pm:risk_register pm.risk_quality sys:is_a
ln pm:risk_register pm:risk_management @supports
set.add name="ontology.project_management" id="pm:risk_register"

def "pm:scope" "All work required to deliver the project outcomes."
ln pm:scope pm.constraints sys:is_a
set.add name="ontology.project_management" id="pm:scope"

def "pm:scrum" "Agile framework with sprints, roles, and ceremonies."
ln pm:scrum pm.methodology sys:is_a
ln pm:scrum pm:agile @specializes
set.add name="ontology.project_management" id="pm:scrum"

def "pm:stakeholder_management" "Identifying stakeholders and managing their expectations and engagement."
ln pm:stakeholder_management pm.stakeholder sys:is_a
set.add name="ontology.project_management" id="pm:stakeholder_management"

def "pm:status_reporting" "Regular communication of progress, risks, and issues."
ln pm:status_reporting pm.stakeholder sys:is_a
set.add name="ontology.project_management" id="pm:status_reporting"

def "pm:steering_committee" "Group providing strategic oversight and key decisions."
ln pm:steering_committee pm.governance sys:is_a
ln pm:steering_committee pm:change_control @governs
set.add name="ontology.project_management" id="pm:steering_committee"

def "pm:time" "Time dimension of the project, including schedule and deadlines."
ln pm:time pm.constraints sys:is_a
set.add name="ontology.project_management" id="pm:time"

def "pm:waterfall" "Sequential project delivery model with distinct phases."
ln pm:waterfall pm.methodology sys:is_a
set.add name="ontology.project_management" id="pm:waterfall"
