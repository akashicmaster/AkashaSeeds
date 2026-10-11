# Akasha ontology — namespace: bdg
# atoms: 26

def "bdg:bom" "Bill of Materials — list of components and their costs."
ln bdg:bom budgeting.project sys:is_a
set.add name="ontology.budgeting" id="bdg:bom"

def "bdg:bottom_up_budgeting" "Budgeting approach where teams estimate needs from the ground up."
ln bdg:bottom_up_budgeting budgeting.planning sys:is_a
set.add name="ontology.budgeting" id="bdg:bottom_up_budgeting"

def "bdg:budget_cycle" "Annual or periodic process for planning and approving budgets."
ln bdg:budget_cycle budgeting.planning sys:is_a
set.add name="ontology.budgeting" id="bdg:budget_cycle"

def "bdg:burn_rate" "Rate at which budget is consumed over time."
ln bdg:burn_rate budgeting.control sys:is_a
ln bdg:burn_rate bdg:variance_analysis @related_to
set.add name="ontology.budgeting" id="bdg:burn_rate"

def "bdg:capex" "Capital expenditures for long-term assets."
ln bdg:capex budgeting.allocation sys:is_a
set.add name="ontology.budgeting" id="bdg:capex"

def "bdg:contingency_budget" "Funds set aside for unexpected events."
ln bdg:contingency_budget budgeting.control sys:is_a
set.add name="ontology.budgeting" id="bdg:contingency_budget"

def "bdg:cost_driver" "Factors that significantly influence cost."
ln bdg:cost_driver budgeting.project sys:is_a
set.add name="ontology.budgeting" id="bdg:cost_driver"

def "bdg:cost_estimation" "Predicting the cost of a project or activity."
ln bdg:cost_estimation budgeting.planning sys:is_a
ln bdg:cost_estimation bdg:wbs_budgeting @supports
set.add name="ontology.budgeting" id="bdg:cost_estimation"

def "bdg:cost_reduction" "Efforts to reduce cost through design, process, or sourcing."
ln bdg:cost_reduction budgeting.project sys:is_a
set.add name="ontology.budgeting" id="bdg:cost_reduction"

def "bdg:design_to_cost" "Design approach that targets a specific cost constraint."
ln bdg:design_to_cost budgeting.project sys:is_a
ln bdg:design_to_cost bdg:cost_driver @related_to
set.add name="ontology.budgeting" id="bdg:design_to_cost"

def "bdg:engineering_link" "Budgeting connection to design, engineering, and manufacturing."
ln bdg:engineering_link budgeting.integration sys:is_a
ln bdg:engineering_link ont.system @related_to
set.add name="ontology.budgeting" id="bdg:engineering_link"

def "bdg:ideation_link" "Budgeting connection to ideation and concept development."
ln bdg:ideation_link budgeting.integration sys:is_a
set.add name="ontology.budgeting" id="bdg:ideation_link"

def "bdg:kpi_alignment" "Ensuring budgets align with key performance indicators."
ln bdg:kpi_alignment budgeting.control sys:is_a
set.add name="ontology.budgeting" id="bdg:kpi_alignment"

def "bdg:marketing_link" "Budgeting connection to marketing strategy and spend."
ln bdg:marketing_link budgeting.integration sys:is_a
ln bdg:marketing_link ont.marketing @related_to
set.add name="ontology.budgeting" id="bdg:marketing_link"

def "bdg:opex" "Operating expenses for day-to-day operations."
ln bdg:opex budgeting.allocation sys:is_a
set.add name="ontology.budgeting" id="bdg:opex"

def "bdg:organization_link" "Budgeting connection to organizational structure and authority."
ln bdg:organization_link budgeting.integration sys:is_a
ln bdg:organization_link ont.organization @related_to
set.add name="ontology.budgeting" id="bdg:organization_link"

def "bdg:prioritization" "Ranking initiatives based on value, cost, and constraints."
ln bdg:prioritization budgeting.allocation sys:is_a
ln bdg:prioritization bdg:tradeoff @supports
set.add name="ontology.budgeting" id="bdg:prioritization"

def "bdg:project_budgeting" "Budgeting for specific projects across planning, design, and execution."
ln bdg:project_budgeting budgeting.project sys:is_a
ln bdg:project_budgeting bdg:ideation_link @related_to
set.add name="ontology.budgeting" id="bdg:project_budgeting"

def "bdg:risk_buffer" "Budget reserved for uncertainties and risks."
ln bdg:risk_buffer budgeting.control sys:is_a
set.add name="ontology.budgeting" id="bdg:risk_buffer"

def "bdg:rolling_forecast" "Continuously updated forecast based on latest data."
ln bdg:rolling_forecast budgeting.planning sys:is_a
set.add name="ontology.budgeting" id="bdg:rolling_forecast"

def "bdg:scenario_planning" "Exploring alternative futures to guide resource allocation."
ln bdg:scenario_planning budgeting.allocation sys:is_a
ln bdg:scenario_planning bdg:rolling_forecast @supports
set.add name="ontology.budgeting" id="bdg:scenario_planning"

def "bdg:top_down_budgeting" "Budgeting approach where leadership sets high-level targets."
ln bdg:top_down_budgeting budgeting.planning sys:is_a
set.add name="ontology.budgeting" id="bdg:top_down_budgeting"

def "bdg:tradeoff" "Choosing between competing options under limited resources."
ln bdg:tradeoff budgeting.allocation sys:is_a
set.add name="ontology.budgeting" id="bdg:tradeoff"

def "bdg:variance_analysis" "Comparing actual vs budgeted performance."
ln bdg:variance_analysis budgeting.control sys:is_a
set.add name="ontology.budgeting" id="bdg:variance_analysis"

def "bdg:wbs_budgeting" "Budgeting based on Work Breakdown Structure."
ln bdg:wbs_budgeting budgeting.project sys:is_a
set.add name="ontology.budgeting" id="bdg:wbs_budgeting"

def "bdg:zero_based_budgeting" "Budgeting method requiring justification for all expenses from zero."
ln bdg:zero_based_budgeting budgeting.planning sys:is_a
set.add name="ontology.budgeting" id="bdg:zero_based_budgeting"
