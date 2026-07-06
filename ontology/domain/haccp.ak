# Akasha ontology — namespace: haccp
# atoms: 16

def "haccp:allergen" "A substance that causes an allergic reaction, requiring strict cross-contact prevention."

def "haccp:biological_hazard" "Dangers from microorganisms such as bacteria, viruses, and parasites."

def "haccp:chemical_hazard" "Dangers from naturally occurring toxins or added chemicals."

def "haccp:corrective_action" "Procedures followed when a deviation occurs at a CCP."
ln haccp:corrective_action haccp:critical_limit @restores

def "haccp:critical_control_point" "A step at which control can be applied to prevent or eliminate a food safety hazard."

def "haccp:critical_limit" "The maximum or minimum value to which a parameter must be controlled at a CCP."

def "haccp:cross_contamination" "The transfer of harmful bacteria or other microorganisms from one substance to another."

def "haccp:hazard_analysis" "The process of identifying and evaluating potential food safety hazards."
ln haccp:hazard_analysis haccp:biological_hazard @identifies
ln haccp:hazard_analysis haccp:chemical_hazard @identifies
ln haccp:hazard_analysis haccp:physical_hazard @identifies

def "haccp:monitoring" "Conducting a planned sequence of observations or measurements to assess whether a CCP is under control."
ln haccp:monitoring haccp:critical_limit @evaluates
ln haccp:monitoring haccp:critical_control_point @observes

def "haccp:physical_hazard" "Foreign objects in food that can cause illness or injury."

def "haccp:prerequisite_program" "Basic environmental and operating conditions necessary to produce safe food (PRP)."
ln haccp:prerequisite_program haccp:allergen @manages

def "haccp:record_keeping" "Maintaining accurate documents demonstrating the effective application of the HACCP system."
ln haccp:record_keeping haccp:monitoring @documents

def "haccp:sanitization" "The reduction of microorganisms to safe levels on food-contact surfaces."
ln haccp:sanitization haccp:cross_contamination @prevents
ln haccp:sanitization haccp:biological_hazard @reduces

def "haccp:temperature_danger_zone" "The temperature range (typically 5C to 60C) in which foodborne bacteria can grow rapidly."
ln haccp:temperature_danger_zone cook:temp:room_temp @includes
ln haccp:temperature_danger_zone cook:temp:lukewarm @includes
ln haccp:temperature_danger_zone cook:temp:human_skin @includes

def "haccp:traceability" "The ability to track food through all stages of production, processing, and distribution."

def "haccp:verification" "The application of methods, procedures, and tests to determine compliance with the HACCP plan."
ln haccp:verification haccp:monitoring @confirms
