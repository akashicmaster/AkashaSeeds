# Akasha ontology — namespace: meta
# atoms: 28

def "meta:ambiguity" "Condition where multiple interpretations remain possible."
ln meta:ambiguity epistemic.error sys:is_a
ln meta:ambiguity meta:uncertain @supports
ln meta:ambiguity sem:ambiguity sys:same_as
set.add name="ontology.epistemic" id="meta:ambiguity"

def "meta:assumed" "Status of a premise accepted temporarily without full proof."
ln meta:assumed epistemic.status sys:is_a
ln meta:assumed phil:belief @related_to
set.add name="ontology.epistemic" id="meta:assumed"

def "meta:auditability" "Capacity for a claim or process to be inspected and traced."
ln meta:auditability epistemic.process sys:is_a
ln meta:auditability meta:reliability @supports
ln meta:auditability ont.system @supports
set.add name="ontology.epistemic" id="meta:auditability"

def "meta:bias" "Systematic distortion in perception, interpretation, source selection, or judgment."
ln meta:bias epistemic.error sys:is_a
ln meta:bias meta:credibility @reduces
set.add name="ontology.epistemic" id="meta:bias"

def "meta:citation" "Reference pointing to the source of a claim or evidence."
ln meta:citation epistemic.source sys:is_a
ln meta:citation meta:traceability @supports
ln meta:citation rhet:evidence @supports
set.add name="ontology.epistemic" id="meta:citation"

def "meta:confidence" "Degree of trust assigned to a claim, inference, source, or interpretation."
ln meta:confidence epistemic.quality sys:is_a
set.add name="ontology.epistemic" id="meta:confidence"

def "meta:confirmed" "Status of a claim supported by sufficient evidence or verification."
ln meta:confirmed epistemic.status sys:is_a
ln meta:confirmed meta:confidence @increases
set.add name="ontology.epistemic" id="meta:confirmed"

def "meta:corroboration" "Independent evidence or source support strengthening a claim."
ln meta:corroboration epistemic.process sys:is_a
ln meta:corroboration meta:evidence_strength @increases
set.add name="ontology.epistemic" id="meta:corroboration"

def "meta:credibility" "Perceived believability of a claim or source."
ln meta:credibility epistemic.quality sys:is_a
set.add name="ontology.epistemic" id="meta:credibility"

def "meta:disinformation" "False information spread deliberately to mislead."
ln meta:disinformation epistemic.error sys:is_a
set.add name="ontology.epistemic" id="meta:disinformation"

def "meta:disputed" "Status of a claim actively contested by alternative claims or sources."
ln meta:disputed epistemic.status sys:is_a
ln meta:disputed meta:confidence @reduces
set.add name="ontology.epistemic" id="meta:disputed"

def "meta:evidence_strength" "Degree to which evidence supports a claim."
ln meta:evidence_strength epistemic.quality sys:is_a
set.add name="ontology.epistemic" id="meta:evidence_strength"

def "meta:falsification" "Process or result of showing a claim to be false."
ln meta:falsification epistemic.process sys:is_a
ln meta:falsification meta:confirmed @contrasts_with
ln meta:falsification phil:skepticism @uses
set.add name="ontology.epistemic" id="meta:falsification"

def "meta:hearsay" "Information reported indirectly rather than witnessed firsthand."
ln meta:hearsay epistemic.source sys:is_a
ln meta:hearsay meta:source_quality @reduces
set.add name="ontology.epistemic" id="meta:hearsay"

def "meta:inferred" "Status of knowledge derived indirectly from evidence or reasoning."
ln meta:inferred epistemic.status sys:is_a
set.add name="ontology.epistemic" id="meta:inferred"

def "meta:misinformation" "False or inaccurate information, regardless of intent."
ln meta:misinformation epistemic.error sys:is_a
set.add name="ontology.epistemic" id="meta:misinformation"

def "meta:noise" "Irrelevant, misleading, or low-signal information that obscures interpretation."
ln meta:noise epistemic.error sys:is_a
ln meta:noise meta:evidence_strength @reduces
set.add name="ontology.epistemic" id="meta:noise"

def "meta:primary_source" "Source directly connected to an event, observation, or original material."
ln meta:primary_source epistemic.source sys:is_a
ln meta:primary_source meta:source_quality @supports
set.add name="ontology.epistemic" id="meta:primary_source"

def "meta:provenance" "Origin and transmission history of information."
ln meta:provenance epistemic.source sys:is_a
ln meta:provenance meta:traceability @supports
set.add name="ontology.epistemic" id="meta:provenance"

def "meta:reliability" "Expected consistency and trustworthiness of information or source behavior."
ln meta:reliability epistemic.quality sys:is_a
set.add name="ontology.epistemic" id="meta:reliability"

def "meta:rumor" "Unverified circulating claim."
ln meta:rumor epistemic.error sys:is_a
set.add name="ontology.epistemic" id="meta:rumor"

def "meta:secondary_source" "Source interpreting, summarizing, or analyzing primary material."
ln meta:secondary_source epistemic.source sys:is_a
ln meta:secondary_source meta:source_quality @qualifies
set.add name="ontology.epistemic" id="meta:secondary_source"

def "meta:source_quality" "Assessment of the origin, authority, and evidential value of a source."
ln meta:source_quality epistemic.quality sys:is_a
set.add name="ontology.epistemic" id="meta:source_quality"

def "meta:tentative" "Provisional status held pending further evidence."
ln meta:tentative epistemic.status sys:is_a
set.add name="ontology.epistemic" id="meta:tentative"

def "meta:testimony" "Information provided by a witness, participant, or informant."
ln meta:testimony epistemic.source sys:is_a
ln meta:testimony hist:testimony sys:same_as
set.add name="ontology.epistemic" id="meta:testimony"

def "meta:traceability" "Ability to follow a claim back through evidence, sources, and transformations."
ln meta:traceability epistemic.process sys:is_a
ln meta:traceability ont.historiography @supports
set.add name="ontology.epistemic" id="meta:traceability"

def "meta:uncertain" "Status of a claim whose truth remains unresolved."
ln meta:uncertain epistemic.status sys:is_a
ln meta:uncertain meta:confidence @reduces
set.add name="ontology.epistemic" id="meta:uncertain"

def "meta:verification" "Process of checking whether a claim is true or supported."
ln meta:verification epistemic.process sys:is_a
ln meta:verification phil:truth @seeks
set.add name="ontology.epistemic" id="meta:verification"
