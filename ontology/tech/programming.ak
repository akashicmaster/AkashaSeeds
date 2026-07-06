# Akasha ontology — namespace: programming
# atoms: 7

def "programming.agile" "Agile & Lean era: iterative development, collaboration, continuous delivery, and adaptive planning."
ln programming.agile ont.programming sys:part_of
set.add name="ontology.programming" id="programming.agile"

def "programming.ai" "AI-assisted development era: LLMs, code generation, semantic modeling, ontology-driven design, co-design workflows."
ln programming.ai ont.programming sys:part_of
set.add name="ontology.programming" id="programming.ai"

def "programming.early" "Early programming era: machine code, assembly, structured programming foundations."
ln programming.early ont.programming sys:part_of
set.add name="ontology.programming" id="programming.early"

def "programming.engineering" "Software engineering era: modularity, structured methods, and the response to the software crisis."
ln programming.engineering ont.programming sys:part_of
set.add name="ontology.programming" id="programming.engineering"

def "programming.modern" "Modern architecture era: DDD, hexagonal, CQRS, event sourcing, cloud-native, resilience, observability."
ln programming.modern ont.programming sys:part_of
ln programming.modern programming.ai @precedes
set.add name="ontology.programming" id="programming.modern"

def "programming.oo" "Object-oriented era: objects, classes, encapsulation, design patterns, and component-based design."
ln programming.oo ont.programming sys:part_of
set.add name="ontology.programming" id="programming.oo"

def "programming.web" "Web and distributed systems era: client-server, REST, SOA, microservices, event-driven architecture."
ln programming.web ont.programming sys:part_of
set.add name="ontology.programming" id="programming.web"
