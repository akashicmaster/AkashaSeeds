# Akasha ontology — namespace: sys
# atoms: 119

def "sys:abstraction" "Simplification of complex systems by focusing on essentials."
ln sys:abstraction system.design sys:is_a
ln sys:abstraction complex @manages
set.add name="ontology.system" id="sys:abstraction"

def "sys:acid" "Atomicity, Consistency, Isolation, Durability properties of transactions."
ln sys:acid system.data sys:is_a
ln sys:acid sys:transaction @characterizes
set.add name="ontology.system" id="sys:acid"

def "sys:alert" "Notification triggered by abnormal conditions."
ln sys:alert system.infrastructure sys:is_a
ln sys:alert sys:incident @signals
set.add name="ontology.system" id="sys:alert"

def "sys:api" "Interface enabling communication between components."
ln sys:api system.architecture sys:is_a
ln sys:api sys:interface @is_a_type_of
set.add name="ontology.system" id="sys:api"

def "sys:api_gateway" "Unified entry point for API traffic."
ln sys:api_gateway system.architecture sys:is_a
set.add name="ontology.system" id="sys:api_gateway"

def "sys:app_builder" "Tool for assembling applications visually."
ln sys:app_builder system.nocode sys:is_a
set.add name="ontology.system" id="sys:app_builder"

def "sys:audit_log" "Log recording access and changes for accountability."
ln sys:audit_log system.data sys:is_a
set.add name="ontology.system" id="sys:audit_log"

def "sys:automation" "Rule-based or event-driven automated action."
ln sys:automation system.nocode sys:is_a
set.add name="ontology.system" id="sys:automation"

def "sys:backup" "Copy of data taken for recovery purposes."
ln sys:backup system.data sys:is_a
ln sys:backup sys:resilience @supports
set.add name="ontology.system" id="sys:backup"

def "sys:batch_processing" "Processing data in large groups at intervals."
ln sys:batch_processing system.data sys:is_a
set.add name="ontology.system" id="sys:batch_processing"

def "sys:blueprint" "High-level design plan for a system."
ln sys:blueprint system.design sys:is_a
set.add name="ontology.system" id="sys:blueprint"

def "sys:branch" "Parallel line of development in version control."
ln sys:branch system.development sys:is_a
set.add name="ontology.system" id="sys:branch"

def "sys:cache" "High-speed storage for frequently accessed data."
ln sys:cache system.architecture sys:is_a
ln sys:cache sys:performance @improves
ln sys:cache sys:query @optimizes
set.add name="ontology.system" id="sys:cache"

def "sys:cd" "Continuous Delivery/Deployment pipeline."
ln sys:cd system.development sys:is_a
set.add name="ontology.system" id="sys:cd"

def "sys:check_constraint" "Constraint enforcing a boolean condition on values."
ln sys:check_constraint system.data sys:is_a
ln sys:check_constraint sys:constraint @specializes
set.add name="ontology.system" id="sys:check_constraint"

def "sys:choreography" "Decentralized event-driven coordination."
ln sys:choreography system.architecture sys:is_a
set.add name="ontology.system" id="sys:choreography"

def "sys:ci" "Continuous Integration: frequent automated merging and testing."
ln sys:ci system.development sys:is_a
set.add name="ontology.system" id="sys:ci"

def "sys:cloud" "On-demand computing resources delivered over the internet."
ln sys:cloud system.infrastructure sys:is_a
set.add name="ontology.system" id="sys:cloud"

def "sys:cohesion" "Degree to which parts of a component belong together conceptually and functionally."
ln sys:cohesion system.principles sys:is_a
ln sys:cohesion sys:maintainability @supports
set.add name="ontology.system" id="sys:cohesion"

def "sys:column" "Named field describing an attribute of records."
ln sys:column system.data sys:is_a
ln sys:column sys:table @part_of
set.add name="ontology.system" id="sys:column"

def "sys:consistency_model" "Contract describing how quickly replicas converge."
ln sys:consistency_model system.data sys:is_a
set.add name="ontology.system" id="sys:consistency_model"

def "sys:constraint" "Limit or requirement that shapes system design."
ln sys:constraint system.principles sys:is_a
ln sys:constraint system.data sys:is_a
ln sys:constraint sys:data_integrity @supports
set.add name="ontology.system" id="sys:constraint"

def "sys:container" "Lightweight isolated runtime environment."
ln sys:container system.infrastructure sys:is_a
set.add name="ontology.system" id="sys:container"

def "sys:contract" "Formal specification of expected behavior."
ln sys:contract system.design sys:is_a
ln sys:contract sys:api @specifies
set.add name="ontology.system" id="sys:contract"

def "sys:coupling" "Degree of dependency between components; high coupling makes change harder."
ln sys:coupling system.principles sys:is_a
ln sys:coupling sys:maintainability @affects
set.add name="ontology.system" id="sys:coupling"

def "sys:data_integrity" "Correctness, consistency, and trustworthiness of stored data."
ln sys:data_integrity system.data sys:is_a
ln sys:data_integrity system.quality @supports
set.add name="ontology.system" id="sys:data_integrity"

def "sys:data_lake" "Large repository storing raw or semi-structured data."
ln sys:data_lake system.data sys:is_a
set.add name="ontology.system" id="sys:data_lake"

def "sys:data_lineage" "Trace of data origins and transformations."
ln sys:data_lineage system.data sys:is_a
set.add name="ontology.system" id="sys:data_lineage"

def "sys:data_pipeline" "Connected steps that move and transform data."
ln sys:data_pipeline system.data sys:is_a
ln sys:data_pipeline sys:etl @may_implement
set.add name="ontology.system" id="sys:data_pipeline"

def "sys:data_warehouse" "Central store optimized for analytical queries."
ln sys:data_warehouse system.data sys:is_a
ln sys:data_warehouse sys:analytics @supports
set.add name="ontology.system" id="sys:data_warehouse"

def "sys:database" "Organized persistence layer for storing and retrieving structured information."
ln sys:database system.data sys:is_a
ln sys:database sys:storage @uses
set.add name="ontology.system" id="sys:database"

def "sys:ddd" "Domain-Driven Design: modeling based on domain language."
ln sys:ddd system.architecture sys:is_a
ln sys:ddd sys:domain_model @uses
set.add name="ontology.system" id="sys:ddd"

def "sys:deadlock" "State where transactions wait on each other's locks indefinitely."
ln sys:deadlock system.data sys:is_a
ln sys:deadlock sys:lock @may_cause
set.add name="ontology.system" id="sys:deadlock"

def "sys:denormalization" "Intentional redundancy to improve read performance."
ln sys:denormalization system.data sys:is_a
ln sys:denormalization sys:normalization @contrasts_with
set.add name="ontology.system" id="sys:denormalization"

def "sys:dependency" "External or internal component required for a system to function."
ln sys:dependency system.principles sys:is_a
set.add name="ontology.system" id="sys:dependency"

def "sys:deployment" "Process of releasing software to production."
ln sys:deployment system.development sys:is_a
set.add name="ontology.system" id="sys:deployment"

def "sys:dns" "Domain Name System mapping names to IP addresses."
ln sys:dns system.infrastructure sys:is_a
set.add name="ontology.system" id="sys:dns"

def "sys:domain_model" "Conceptual model representing business logic."
ln sys:domain_model system.architecture sys:is_a
set.add name="ontology.system" id="sys:domain_model"

def "sys:etl" "Extract, Transform, Load process for moving data."
ln sys:etl system.data sys:is_a
set.add name="ontology.system" id="sys:etl"

def "sys:event" "State change broadcasted to other components."
ln sys:event system.architecture sys:is_a
ln sys:event sys:queue @may_flow_through
set.add name="ontology.system" id="sys:event"

def "sys:eventual_consistency" "Model where replicas converge over time without immediate agreement."
ln sys:eventual_consistency system.data sys:is_a
ln sys:eventual_consistency sys:consistency_model @specializes
ln sys:eventual_consistency sys:strong_consistency @contrasts_with
set.add name="ontology.system" id="sys:eventual_consistency"

def "sys:flowchart" "Diagram representing process flow."
ln sys:flowchart system.design sys:is_a
set.add name="ontology.system" id="sys:flowchart"

def "sys:foreign_key" "Field referencing a primary key in another table."
ln sys:foreign_key system.data sys:is_a
ln sys:foreign_key sys:table @constrains
set.add name="ontology.system" id="sys:foreign_key"

def "sys:fragility" "Tendency of a system to break under change, load, dependency failure, or unexpected input."
ln sys:fragility system.risk sys:is_a
ln sys:fragility sys:reliability @reduces
set.add name="ontology.system" id="sys:fragility"

def "sys:graphql" "Query-based API allowing clients to specify required data."
ln sys:graphql system.architecture sys:is_a
set.add name="ontology.system" id="sys:graphql"

def "sys:incident" "Unexpected event that disrupts service, correctness, performance, or security."
ln sys:incident system.operations sys:is_a
ln sys:incident sys:reliability @threatens
set.add name="ontology.system" id="sys:incident"

def "sys:index" "Auxiliary structure that improves lookup or retrieval speed."
ln sys:index system.data sys:is_a
ln sys:index sys:performance @supports
ln sys:index sys:table @optimizes
set.add name="ontology.system" id="sys:index"

def "sys:integration_test" "Test verifying interaction between components."
ln sys:integration_test system.development sys:is_a
ln sys:integration_test sys:test sys:is_a
set.add name="ontology.system" id="sys:integration_test"

def "sys:interface" "Boundary defining interactions between components."
ln sys:interface system.design sys:is_a
set.add name="ontology.system" id="sys:interface"

def "sys:isolation_level" "Degree to which concurrent transactions are separated."
ln sys:isolation_level system.data sys:is_a
ln sys:isolation_level sys:transaction @configures
set.add name="ontology.system" id="sys:isolation_level"

def "sys:join" "Operation combining rows from multiple tables based on a condition."
ln sys:join system.data sys:is_a
ln sys:join sys:table @operates_on
set.add name="ontology.system" id="sys:join"

def "sys:layered_architecture" "Architecture divided into presentation, domain, data layers."
ln sys:layered_architecture system.architecture sys:is_a
set.add name="ontology.system" id="sys:layered_architecture"

def "sys:load_balancer" "Distributes traffic across multiple servers."
ln sys:load_balancer system.architecture sys:is_a
ln sys:load_balancer sys:scalability @supports
set.add name="ontology.system" id="sys:load_balancer"

def "sys:local_first" "Design principle where data and core functionality remain available on the user's local device."
ln sys:local_first system.principles sys:is_a
ln sys:local_first sys:reliability @supports
ln sys:local_first sys:cloud @contrasts_with
set.add name="ontology.system" id="sys:local_first"

def "sys:lock" "Mechanism controlling concurrent access to data."
ln sys:lock system.data sys:is_a
ln sys:lock sys:transaction @supports
set.add name="ontology.system" id="sys:lock"

def "sys:log" "Recorded event stream used for debugging, audit, diagnosis, or operational history."
ln sys:log system.operations sys:is_a
ln sys:log sys:monitoring @supports
set.add name="ontology.system" id="sys:log"

def "sys:maintainability" "Ease of modifying and improving a system."
ln sys:maintainability system.quality sys:is_a
set.add name="ontology.system" id="sys:maintainability"

def "sys:mapping" "Transformation between models or schemas."
ln sys:mapping system.design sys:is_a
set.add name="ontology.system" id="sys:mapping"

def "sys:materialized_view" "View whose results are stored physically."
ln sys:materialized_view system.data sys:is_a
ln sys:materialized_view sys:view @extends
set.add name="ontology.system" id="sys:materialized_view"

def "sys:merge" "Combining changes from different branches."
ln sys:merge system.development sys:is_a
set.add name="ontology.system" id="sys:merge"

def "sys:metric" "Measured value used to evaluate system behavior, health, or performance."
ln sys:metric system.operations sys:is_a
ln sys:metric sys:monitoring @supports
set.add name="ontology.system" id="sys:metric"

def "sys:microservice" "Independent deployable service with bounded context."
ln sys:microservice system.architecture sys:is_a
ln sys:microservice sys:coupling @reduces
set.add name="ontology.system" id="sys:microservice"

def "sys:migration" "Change process that transforms stored data or schema from one version to another."
ln sys:migration system.data sys:is_a
ln sys:migration sys:schema @changes
set.add name="ontology.system" id="sys:migration"

def "sys:mock" "Simulated component used for testing or design."
ln sys:mock system.design sys:is_a
set.add name="ontology.system" id="sys:mock"

def "sys:monitoring" "Observing system health and performance."
ln sys:monitoring system.infrastructure sys:is_a
ln sys:monitoring sys:incident @detects
set.add name="ontology.system" id="sys:monitoring"

def "sys:monolith" "Single unified codebase deployed as one unit."
ln sys:monolith system.architecture sys:is_a
ln sys:monolith sys:coupling @may_increase
set.add name="ontology.system" id="sys:monolith"

def "sys:network" "Interconnected systems enabling communication."
ln sys:network system.infrastructure sys:is_a
set.add name="ontology.system" id="sys:network"

def "sys:nocode_form" "User interface built with drag-and-drop tools."
ln sys:nocode_form system.nocode sys:is_a
set.add name="ontology.system" id="sys:nocode_form"

def "sys:nocode_integration" "Connector linking apps without code."
ln sys:nocode_integration system.nocode sys:is_a
set.add name="ontology.system" id="sys:nocode_integration"

def "sys:nocode_workflow" "Visual workflow built without coding."
ln sys:nocode_workflow system.nocode sys:is_a
set.add name="ontology.system" id="sys:nocode_workflow"

def "sys:normalization" "Process of structuring data to reduce redundancy."
ln sys:normalization system.data sys:is_a
set.add name="ontology.system" id="sys:normalization"

def "sys:optimizer" "Component that selects efficient query plans."
ln sys:optimizer system.data sys:is_a
ln sys:optimizer sys:query @optimizes
set.add name="ontology.system" id="sys:optimizer"

def "sys:orchestration" "Centralized coordination of services or workflows."
ln sys:orchestration system.architecture sys:is_a
set.add name="ontology.system" id="sys:orchestration"

def "sys:partition" "Logical or physical subdivision of a dataset."
ln sys:partition system.data sys:is_a
ln sys:partition sys:table @subdivides
set.add name="ontology.system" id="sys:partition"

def "sys:performance" "Speed and efficiency of system operations."
ln sys:performance system.quality sys:is_a
set.add name="ontology.system" id="sys:performance"

def "sys:portability" "Ability of a system to run across environments with minimal change."
ln sys:portability system.quality sys:is_a
ln sys:portability sys:dependency @reduced_by
ln sys:portability sys:container @supported_by
set.add name="ontology.system" id="sys:portability"

def "sys:primary_key" "Unique identifier for records in a table."
ln sys:primary_key system.data sys:is_a
ln sys:primary_key sys:table @constrains
set.add name="ontology.system" id="sys:primary_key"

def "sys:prototype" "Early model used to test concepts."
ln sys:prototype system.design sys:is_a
set.add name="ontology.system" id="sys:prototype"

def "sys:query" "Request to read or manipulate data."
ln sys:query system.data sys:is_a
ln sys:query sys:sql @often_expressed_in
set.add name="ontology.system" id="sys:query"

def "sys:query_plan" "Execution strategy chosen by the optimizer."
ln sys:query_plan system.data sys:is_a
ln sys:query_plan sys:query @implements
set.add name="ontology.system" id="sys:query_plan"

def "sys:queue" "Asynchronous message buffer for decoupled systems."
ln sys:queue system.architecture sys:is_a
set.add name="ontology.system" id="sys:queue"

def "sys:record" "Single row representing one entity instance."
ln sys:record system.data sys:is_a
ln sys:record sys:table @part_of
set.add name="ontology.system" id="sys:record"

def "sys:recovery" "Process of restoring system function after failure, incident, corruption, or outage."
ln sys:recovery system.operations sys:is_a
ln sys:recovery sys:rollback @may_use
set.add name="ontology.system" id="sys:recovery"

def "sys:refactoring" "Improving internal structure without changing external behavior."
ln sys:refactoring system.development sys:is_a
ln sys:refactoring sys:technical_debt @reduces
ln sys:refactoring sys:maintainability @improves
set.add name="ontology.system" id="sys:refactoring"

def "sys:referential_integrity" "Integrity of relationships enforced by foreign keys."
ln sys:referential_integrity system.data sys:is_a
ln sys:referential_integrity sys:foreign_key @depends_on
set.add name="ontology.system" id="sys:referential_integrity"

def "sys:relation" "Abstract table defined by attributes and tuples."
ln sys:relation system.data sys:is_a
set.add name="ontology.system" id="sys:relation"

def "sys:reliability" "Ability of a system to operate consistently."
ln sys:reliability system.quality sys:is_a
set.add name="ontology.system" id="sys:reliability"

def "sys:replica" "Copy of data kept in sync with a primary source."
ln sys:replica system.data sys:is_a
set.add name="ontology.system" id="sys:replica"

def "sys:replication" "Process of copying and synchronizing data across locations."
ln sys:replication system.data sys:is_a
ln sys:replication sys:replica @produces
ln sys:replication sys:reliability @supports
set.add name="ontology.system" id="sys:replication"

def "sys:repository" "Version-controlled storage for code."
ln sys:repository system.development sys:is_a
set.add name="ontology.system" id="sys:repository"

def "sys:rest" "Representational State Transfer API style."
ln sys:rest system.architecture sys:is_a
set.add name="ontology.system" id="sys:rest"

def "sys:restore" "Process of rebuilding data from a backup."
ln sys:restore system.data sys:is_a
ln sys:restore sys:backup @depends_on
set.add name="ontology.system" id="sys:restore"

def "sys:rollback" "Reverting to a previous stable version."
ln sys:rollback system.development sys:is_a
ln sys:rollback sys:recovery @supports
set.add name="ontology.system" id="sys:rollback"

def "sys:scalability" "Capacity to handle increased load."
ln sys:scalability system.quality sys:is_a
set.add name="ontology.system" id="sys:scalability"

def "sys:scaling" "Increasing or decreasing system capacity."
ln sys:scaling system.infrastructure sys:is_a
set.add name="ontology.system" id="sys:scaling"

def "sys:schema" "Structured definition of data format."
ln sys:schema system.design sys:is_a
ln sys:schema sys:contract @may_define
set.add name="ontology.system" id="sys:schema"

def "sys:schema_migration" "Controlled change to database structure over time."
ln sys:schema_migration system.data sys:is_a
set.add name="ontology.system" id="sys:schema_migration"

def "sys:security" "Protection against threats and vulnerabilities."
ln sys:security system.quality sys:is_a
set.add name="ontology.system" id="sys:security"

def "sys:server" "Machine or process providing services to clients."
ln sys:server system.infrastructure sys:is_a
set.add name="ontology.system" id="sys:server"

def "sys:shard" "Partition of data distributed across nodes."
ln sys:shard system.data sys:is_a
set.add name="ontology.system" id="sys:shard"

def "sys:single_point_of_failure" "Component whose failure can cause the whole system or workflow to fail."
ln sys:single_point_of_failure system.risk sys:is_a
ln sys:single_point_of_failure sys:reliability @threatens
set.add name="ontology.system" id="sys:single_point_of_failure"

def "sys:sql" "Structured Query Language for relational databases."
ln sys:sql system.data sys:is_a
set.add name="ontology.system" id="sys:sql"

def "sys:storage" "Persistent data storage system."
ln sys:storage system.infrastructure sys:is_a
set.add name="ontology.system" id="sys:storage"

def "sys:stream_processing" "Processing data continuously as it arrives."
ln sys:stream_processing system.data sys:is_a
ln sys:stream_processing sys:batch_processing @contrasts_with
set.add name="ontology.system" id="sys:stream_processing"

def "sys:strong_consistency" "Model where all reads see the latest committed write."
ln sys:strong_consistency system.data sys:is_a
ln sys:strong_consistency sys:consistency_model @specializes
set.add name="ontology.system" id="sys:strong_consistency"

def "sys:table" "Structured set of rows and columns in a relational database."
ln sys:table system.data sys:is_a
ln sys:table sys:database @part_of
set.add name="ontology.system" id="sys:table"

def "sys:technical_debt" "Accumulated design or implementation compromise that makes future change more expensive."
ln sys:technical_debt system.risk sys:is_a
ln sys:technical_debt sys:maintainability @reduces
ln sys:technical_debt sys:workaround @may_result_from
set.add name="ontology.system" id="sys:technical_debt"

def "sys:test" "Procedure to verify correctness of code."
ln sys:test system.development sys:is_a
ln sys:test sys:reliability @supports
set.add name="ontology.system" id="sys:test"

def "sys:trace" "Record of execution path across components or operations."
ln sys:trace system.operations sys:is_a
ln sys:trace debug @supports
set.add name="ontology.system" id="sys:trace"

def "sys:tradeoff" "Design choice where improving one quality may reduce another."
ln sys:tradeoff system.principles sys:is_a
set.add name="ontology.system" id="sys:tradeoff"

def "sys:transaction" "Atomic unit of work that either completes fully or leaves the system unchanged."
ln sys:transaction system.data sys:is_a
ln sys:transaction sys:reliability @supports
set.add name="ontology.system" id="sys:transaction"

def "sys:tx_commit" "Operation that makes a transaction's changes durable."
ln sys:tx_commit system.data sys:is_a
ln sys:tx_commit sys:transaction @finalizes
set.add name="ontology.system" id="sys:tx_commit"

def "sys:tx_rollback" "Operation that reverts a transaction's changes."
ln sys:tx_rollback system.data sys:is_a
ln sys:tx_rollback sys:transaction @reverts
set.add name="ontology.system" id="sys:tx_rollback"

def "sys:uml" "Unified Modeling Language for system diagrams."
ln sys:uml system.design sys:is_a
set.add name="ontology.system" id="sys:uml"

def "sys:unique_constraint" "Constraint enforcing uniqueness of values."
ln sys:unique_constraint system.data sys:is_a
ln sys:unique_constraint sys:constraint @specializes
set.add name="ontology.system" id="sys:unique_constraint"

def "sys:unit_test" "Test verifying behavior of a small component."
ln sys:unit_test system.development sys:is_a
ln sys:unit_test sys:test sys:is_a
set.add name="ontology.system" id="sys:unit_test"

def "sys:view" "Virtual table defined by a query."
ln sys:view system.data sys:is_a
ln sys:view sys:database @part_of
set.add name="ontology.system" id="sys:view"

def "sys:vm" "Virtual machine emulating hardware."
ln sys:vm system.infrastructure sys:is_a
set.add name="ontology.system" id="sys:vm"

def "sys:workaround" "Temporary solution that bypasses a problem without fully resolving the underlying cause."
ln sys:workaround system.risk sys:is_a
ln sys:workaround sys:technical_debt @may_create
set.add name="ontology.system" id="sys:workaround"
