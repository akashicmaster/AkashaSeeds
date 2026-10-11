# Akasha ontology — namespace: data
# atoms: 142

def "data.ai_llm_era" "AI・LLM era: vector databases, semantic search, embeddings, retrieval-augmented generation, and meaning-centric data infrastructure."
ln data.ai_llm_era ont.data_history sys:part_of
set.add name="ontology.data" id="data.ai_llm_era"

def "data.directory" "Directory-based information organization lineage: Unix directories, GUI folder metaphor, and their influence on spreadsheets and data management."
ln data.directory ont.data_history sys:part_of
set.add name="ontology.data" id="data.directory"

def "data.early_db" "Early database era: hierarchical DB, network DB, navigational access, and schema/subschema models."
ln data.early_db ont.data_history sys:part_of
set.add name="ontology.data" id="data.early_db"

def "data.filesystem" "Early digital file systems: sequential files, hierarchical storage, ISAM/VSAM, and record-based access."
ln data.filesystem ont.data_history sys:part_of
set.add name="ontology.data" id="data.filesystem"

def "data.gui_folder" "Graphical representation of a directory as a folder icon."
ln data.gui_folder data:desktop_metaphor sys:is_a
ln data.gui_folder data:workbook_as_folder @influences
ln data.gui_folder data.lake @influences
ln data.gui_folder data:dashboard @analogous_to
ln data.gui_folder data:gold_layer @analogous_to
set.add name="ontology.data" id="data.gui_folder"

def "data.lake" "Data Lake and Lakehouse era: schema-on-read, distributed storage, ELT, and unified analytical platforms."
ln data.lake ont.data_history sys:part_of
set.add name="ontology.data" id="data.lake"

def "data.nosql" "NoSQL database era: key-value, document, columnar, graph, CAP theorem, BASE, distributed systems."
ln data.nosql ont.data_history sys:part_of
set.add name="ontology.data" id="data.nosql"

def "data.pre_digital" "Pre-digital era: physical filing systems, card indexes, manual classification and retrieval."
ln data.pre_digital ont.data_history sys:part_of
set.add name="ontology.data" id="data.pre_digital"

def "data.relational" "Relational database era: relational model, SQL, ACID, normalization, and commercial RDBMS."
ln data.relational ont.data_history sys:part_of
set.add name="ontology.data" id="data.relational"

def "data.spreadsheet" "Spreadsheet lineage: from early personal spreadsheets to modern cloud-based collaborative sheets, functioning as de facto databases."
ln data.spreadsheet ont.data_history sys:part_of
set.add name="ontology.data" id="data.spreadsheet"

def "data.warehouse" "Data Warehouse era: OLAP, star schema, ETL, MPP, and enterprise analytics systems."
ln data.warehouse ont.data_history sys:part_of
set.add name="ontology.data" id="data.warehouse"

def "data:acid" "Atomicity, Consistency, Isolation, Durability: properties of reliable transactions."
ln data:acid data.relational sys:is_a
set.add name="ontology.data" id="data:acid"

def "data:ad_hoc_database" "Spreadsheet used as an improvised database for small-scale or temporary solutions."
ln data:ad_hoc_database data.spreadsheet sys:is_a
ln data:ad_hoc_database data:rag @used_with
set.add name="ontology.data" id="data:ad_hoc_database"

def "data:ai_agent" "Autonomous LLM-driven process capable of planning, retrieving, and acting."
ln data:ai_agent data.ai_llm_era sys:is_a
set.add name="ontology.data" id="data:ai_agent"

def "data:alan_kay_object_metaphor" "Alan Kay's concept of interacting with information as objects in a manipulable space."
ln data:alan_kay_object_metaphor data:desktop_metaphor sys:is_a
set.add name="ontology.data" id="data:alan_kay_object_metaphor"

def "data:approximate_nearest_neighbor" "Algorithms for fast similarity search in high-dimensional spaces."
ln data:approximate_nearest_neighbor data:vector_database sys:is_a
set.add name="ontology.data" id="data:approximate_nearest_neighbor"

def "data:attribute" "Column in a relational table."
ln data:attribute data:relational_model sys:is_a
set.add name="ontology.data" id="data:attribute"

def "data:base" "Basically Available, Soft state, Eventual consistency—NoSQL alternative to ACID."
ln data:base data.nosql sys:is_a
set.add name="ontology.data" id="data:base"

def "data:batch_processing" "Processing model where jobs are executed in large, scheduled batches."
ln data:batch_processing data.filesystem sys:is_a
set.add name="ontology.data" id="data:batch_processing"

def "data:bronze_layer" "Lake layer storing raw or lightly processed data."
ln data:bronze_layer data.lake sys:is_a
set.add name="ontology.data" id="data:bronze_layer"

def "data:business_intelligence" "Tools and processes for analyzing warehouse data to support decisions."
ln data:business_intelligence data.warehouse sys:is_a
set.add name="ontology.data" id="data:business_intelligence"

def "data:cap_theorem" "CAP theorem: consistency, availability, partition tolerance—choose two."
ln data:cap_theorem data.nosql sys:is_a
set.add name="ontology.data" id="data:cap_theorem"

def "data:card_index" "Indexed cards storing structured information for fast lookup."
ln data:card_index data.pre_digital sys:is_a
ln data:card_index data.filesystem @precedes
ln data:card_index data.spreadsheet @influences
set.add name="ontology.data" id="data:card_index"

def "data:cassandra" "Distributed wide-column store inspired by Bigtable and Dynamo."
ln data:cassandra data:columnar_store sys:is_a
set.add name="ontology.data" id="data:cassandra"

def "data:catalog_system" "System for organizing items using categories, indexes, and controlled vocabularies."
ln data:catalog_system data.pre_digital sys:is_a
ln data:catalog_system data.relational @influences
set.add name="ontology.data" id="data:catalog_system"

def "data:cell" "Atomic unit of a spreadsheet, holding a value or formula."
ln data:cell data:tuple @analogous_to
ln data:cell data:worksheet sys:is_a
set.add name="ontology.data" id="data:cell"

def "data:classification_scheme" "Taxonomy or controlled vocabulary used to categorize documents or items."
ln data:classification_scheme data.pre_digital sys:is_a
set.add name="ontology.data" id="data:classification_scheme"

def "data:codasyl" "Network database model using sets and pointers for flexible record relationships."
ln data:codasyl data.early_db sys:is_a
set.add name="ontology.data" id="data:codasyl"

def "data:codasyl_set" "Owner-member record grouping representing relationships in CODASYL."
ln data:codasyl_set data:codasyl sys:is_a
set.add name="ontology.data" id="data:codasyl_set"

def "data:codd" "E. F. Codd, creator of the relational model."
ln data:codd data.relational sys:is_a
set.add name="ontology.data" id="data:codd"

def "data:collaborative_spreadsheet" "Spreadsheet model supporting real-time multi-user editing and sharing."
ln data:collaborative_spreadsheet data:google_sheets sys:is_a
set.add name="ontology.data" id="data:collaborative_spreadsheet"

def "data:columnar_store" "NoSQL model storing data in column families for high write throughput."
ln data:columnar_store data.nosql sys:is_a
ln data:columnar_store data.warehouse @influences
ln data:columnar_store data:mpp @influences
ln data:columnar_store data:parquet @influences
set.add name="ontology.data" id="data:columnar_store"

def "data:context_window" "LLM input window where retrieved knowledge is injected for reasoning."
ln data:context_window data:rag sys:is_a
set.add name="ontology.data" id="data:context_window"

def "data:couchdb" "Document database with replication and offline-first design."
ln data:couchdb data:document_store sys:is_a
set.add name="ontology.data" id="data:couchdb"

def "data:dashboard" "Visual interface summarizing key metrics and trends."
ln data:dashboard data:business_intelligence sys:is_a
set.add name="ontology.data" id="data:dashboard"

def "data:data_silo_spreadsheet" "Isolated spreadsheet-based dataset not integrated with central systems."
ln data:data_silo_spreadsheet data.spreadsheet sys:is_a
set.add name="ontology.data" id="data:data_silo_spreadsheet"

def "data:db2" "IBM's relational database system."
ln data:db2 data.relational sys:is_a
set.add name="ontology.data" id="data:db2"

def "data:delta_lake" "Lakehouse storage layer providing ACID transactions and versioning."
ln data:delta_lake data:lakehouse sys:is_a
set.add name="ontology.data" id="data:delta_lake"

def "data:desktop_metaphor" "GUI metaphor representing files and folders as objects on a desktop."
ln data:desktop_metaphor data.directory sys:is_a
set.add name="ontology.data" id="data:desktop_metaphor"

def "data:dimension_table" "Table describing attributes used for grouping and filtering facts."
ln data:dimension_table data:star_schema sys:is_a
set.add name="ontology.data" id="data:dimension_table"

def "data:document_store" "Schema-flexible NoSQL model storing semi-structured documents (JSON-like)."
ln data:document_store data.nosql sys:is_a
ln data:document_store data.lake @precedes
ln data:document_store data:raw_zone @similar_to
ln data:document_store data:semantic_space @precedes
set.add name="ontology.data" id="data:document_store"

def "data:drill_down" "OLAP operation for navigating from summary to detail."
ln data:drill_down data:olap sys:is_a
set.add name="ontology.data" id="data:drill_down"

def "data:elt" "Load raw data first, then transform inside the lake or lakehouse."
ln data:elt data.lake sys:is_a
ln data:elt data:rag @supports
set.add name="ontology.data" id="data:elt"

def "data:embedding" "Numerical vector representation of text, images, or multimodal content capturing semantic meaning."
ln data:embedding data.ai_llm_era sys:is_a
set.add name="ontology.data" id="data:embedding"

def "data:embedding_dimension" "Dimensionality of embedding vectors, affecting expressiveness and performance."
ln data:embedding_dimension data:embedding sys:is_a
set.add name="ontology.data" id="data:embedding_dimension"

def "data:etl" "Process of extracting, transforming, and loading data into a warehouse."
ln data:etl data.warehouse sys:is_a
ln data:etl data.lake @precedes
ln data:etl data:elt @contrasts_with
set.add name="ontology.data" id="data:etl"

def "data:eventual_consistency" "Consistency model where updates propagate asynchronously."
ln data:eventual_consistency data:base sys:is_a
ln data:eventual_consistency data:lakehouse @related_to
set.add name="ontology.data" id="data:eventual_consistency"

def "data:excel" "Microsoft Excel, the dominant desktop spreadsheet application, widely used as an unofficial database."
ln data:excel data.spreadsheet sys:is_a
set.add name="ontology.data" id="data:excel"

def "data:extract" "Retrieving data from operational systems."
ln data:extract data:etl sys:is_a
set.add name="ontology.data" id="data:extract"

def "data:fact_table" "Central table storing quantitative metrics for analysis."
ln data:fact_table data:star_schema sys:is_a
set.add name="ontology.data" id="data:fact_table"

def "data:faiss" "Facebook AI Similarity Search library for vector indexing and ANN."
ln data:faiss data:approximate_nearest_neighbor sys:is_a
set.add name="ontology.data" id="data:faiss"

def "data:file_folder" "Paper folder grouping related documents under a labeled category."
ln data:file_folder data.pre_digital sys:is_a
ln data:file_folder data:filing_cabinet @part_of
set.add name="ontology.data" id="data:file_folder"

def "data:file_icon" "Graphical representation of a file as an icon."
ln data:file_icon data:desktop_metaphor sys:is_a
ln data:file_icon data:worksheet_as_file @analogous_to
set.add name="ontology.data" id="data:file_icon"

def "data:filing_cabinet" "Physical cabinet storing documents in folders, organized by labels or categories."
ln data:filing_cabinet data.pre_digital sys:is_a
set.add name="ontology.data" id="data:filing_cabinet"

def "data:formula" "Expression in a cell that computes values based on other cells."
ln data:formula data:sql @related_to
ln data:formula data:worksheet sys:is_a
set.add name="ontology.data" id="data:formula"

def "data:gold_layer" "Lake layer storing aggregated, analytics-ready data."
ln data:gold_layer data.lake sys:is_a
set.add name="ontology.data" id="data:gold_layer"

def "data:google_sheets" "Cloud-based collaborative spreadsheet, enabling multi-user editing and integration via APIs."
ln data:google_sheets data.spreadsheet sys:is_a
set.add name="ontology.data" id="data:google_sheets"

def "data:graph_database" "Database model optimized for graph structures and relationship traversal."
ln data:graph_database data.nosql sys:is_a
set.add name="ontology.data" id="data:graph_database"

def "data:grid_model" "Two-dimensional grid for organizing data, analogous to a directory of cells."
ln data:grid_model data.directory sys:is_a
ln data:grid_model data:spatial_navigation @related_to
set.add name="ontology.data" id="data:grid_model"

def "data:hbase" "Hadoop-based columnar store modeled after Google Bigtable."
ln data:hbase data:columnar_store sys:is_a
set.add name="ontology.data" id="data:hbase"

def "data:hierarchical_file_system" "Directory-based file organization allowing nested folders."
ln data:hierarchical_file_system data.filesystem sys:is_a
ln data:hierarchical_file_system data.spreadsheet @influences
set.add name="ontology.data" id="data:hierarchical_file_system"

def "data:hierarchical_model" "Database model organizing data in parent-child tree structures."
ln data:hierarchical_model data.early_db sys:is_a
ln data:hierarchical_model data:ims @defines
ln data:hierarchical_model data.gui_folder @precedes
ln data:hierarchical_model data.relational @precedes
ln data:hierarchical_model data:relational_model @contrasts_with
set.add name="ontology.data" id="data:hierarchical_model"

def "data:hierarchical_namespace" "Tree-structured naming system for organizing files and directories."
ln data:hierarchical_namespace data:unix_directory sys:is_a
ln data:hierarchical_namespace data.gui_folder @influences
ln data:hierarchical_namespace data:document_store @influences
ln data:hierarchical_namespace data:bronze_layer @analogous_to
ln data:hierarchical_namespace data:meaning_graph @analogous_to
set.add name="ontology.data" id="data:hierarchical_namespace"

def "data:hnsw" "Hierarchical Navigable Small World graph for efficient ANN search."
ln data:hnsw data:approximate_nearest_neighbor sys:is_a
set.add name="ontology.data" id="data:hnsw"

def "data:hudi" "Data Lake framework supporting incremental processing and upserts."
ln data:hudi data:lakehouse sys:is_a
set.add name="ontology.data" id="data:hudi"

def "data:hybrid_search" "Combining keyword search, vector search, and structured filters."
ln data:hybrid_search data.ai_llm_era sys:is_a
set.add name="ontology.data" id="data:hybrid_search"

def "data:iceberg" "Table format for large analytic datasets with schema evolution and partitioning."
ln data:iceberg data:lakehouse sys:is_a
set.add name="ontology.data" id="data:iceberg"

def "data:implicit_schema" "Unwritten structure inferred from column names, conventions, and user practices."
ln data:implicit_schema data.spreadsheet sys:is_a
ln data:implicit_schema data:document_store @analogous_to
ln data:implicit_schema data:semantic_space @analogous_to
set.add name="ontology.data" id="data:implicit_schema"

def "data:ims" "IBM's Information Management System: hierarchical database using tree-structured records."
ln data:ims data.early_db sys:is_a
set.add name="ontology.data" id="data:ims"

def "data:ims_segment" "Record type in IMS representing a node in the hierarchy."
ln data:ims_segment data:ims sys:is_a
set.add name="ontology.data" id="data:ims_segment"

def "data:index_file" "Auxiliary file storing key-to-record mappings for faster lookup."
ln data:index_file data.filesystem sys:is_a
ln data:index_file data:isam @supports
set.add name="ontology.data" id="data:index_file"

def "data:inode" "Unix metadata structure describing file attributes and pointers to data blocks."
ln data:inode data:unix_directory sys:is_a
ln data:inode data:ims_segment @analogous_to
set.add name="ontology.data" id="data:inode"

def "data:isam" "Indexed Sequential Access Method: combining sequential storage with index-based lookup."
ln data:isam data.filesystem sys:is_a
ln data:isam data:sequential_file @extends
ln data:isam data.early_db @precedes
set.add name="ontology.data" id="data:isam"

def "data:job_control_language" "Scripting language for defining batch jobs and file operations."
ln data:job_control_language data:batch_processing sys:is_a
set.add name="ontology.data" id="data:job_control_language"

def "data:key_value_store" "Simple NoSQL model storing values indexed by keys."
ln data:key_value_store data.nosql sys:is_a
ln data:key_value_store data:ai_agent @supports
set.add name="ontology.data" id="data:key_value_store"

def "data:lakehouse" "Unified architecture combining Data Lake flexibility with Data Warehouse management features."
ln data:lakehouse data.lake sys:is_a
ln data:lakehouse data:meaning_graph @influences
set.add name="ontology.data" id="data:lakehouse"

def "data:ledger" "Bound book for recording structured entries such as transactions or inventories."
ln data:ledger data.pre_digital sys:is_a
ln data:ledger data.spreadsheet @influences
set.add name="ontology.data" id="data:ledger"

def "data:load" "Loading processed data into the warehouse."
ln data:load data:etl sys:is_a
set.add name="ontology.data" id="data:load"

def "data:lotus_123" "Lotus 1-2-3, a dominant DOS-era spreadsheet combining calculation, graphing, and database-like features."
ln data:lotus_123 data.spreadsheet sys:is_a
set.add name="ontology.data" id="data:lotus_123"

def "data:magnetic_disk" "Random-access magnetic storage enabling faster retrieval than tape."
ln data:magnetic_disk data.filesystem sys:is_a
set.add name="ontology.data" id="data:magnetic_disk"

def "data:magnetic_tape" "Sequential-access magnetic storage medium used for early digital data processing."
ln data:magnetic_tape data.filesystem sys:is_a
set.add name="ontology.data" id="data:magnetic_tape"

def "data:manual_data_cleaning" "Human-driven correction and normalization of spreadsheet data."
ln data:manual_data_cleaning data.spreadsheet sys:is_a
ln data:manual_data_cleaning data.warehouse @contrasts_with
ln data:manual_data_cleaning data:etl @contrasts_with
set.add name="ontology.data" id="data:manual_data_cleaning"

def "data:manual_retrieval" "Human-driven process of locating information using physical indexes or labels."
ln data:manual_retrieval data.pre_digital sys:is_a
set.add name="ontology.data" id="data:manual_retrieval"

def "data:meaning_graph" "Graph structure representing semantic relationships between concepts, embeddings, and contexts."
ln data:meaning_graph data.ai_llm_era sys:is_a
set.add name="ontology.data" id="data:meaning_graph"

def "data:mongodb" "Popular document database using BSON documents."
ln data:mongodb data:document_store sys:is_a
set.add name="ontology.data" id="data:mongodb"

def "data:mpp" "Massively Parallel Processing: distributed execution of analytical queries."
ln data:mpp data.warehouse sys:is_a
ln data:mpp data.lake @influences
ln data:mpp data:presto @influences
set.add name="ontology.data" id="data:mpp"

def "data:multiplan" "Microsoft Multiplan, an early spreadsheet predating Excel, popular on CP/M and early DOS systems."
ln data:multiplan data.spreadsheet sys:is_a
set.add name="ontology.data" id="data:multiplan"

def "data:mysql" "Popular open-source relational database."
ln data:mysql data.relational sys:is_a
set.add name="ontology.data" id="data:mysql"

def "data:neo4j" "Popular graph database using nodes, relationships, and Cypher query language."
ln data:neo4j data:graph_database sys:is_a
set.add name="ontology.data" id="data:neo4j"

def "data:network_model" "Database model allowing many-to-many relationships via explicit pointers."
ln data:network_model data.early_db sys:is_a
ln data:network_model data:codasyl @defines
ln data:network_model data.relational @contrasts_with
ln data:network_model data:relational_model @contrasts_with
set.add name="ontology.data" id="data:network_model"

def "data:normal_form" "Formal rules defining levels of normalization (1NF, 2NF, 3NF, BCNF)."
ln data:normal_form data:normalization sys:is_a
set.add name="ontology.data" id="data:normal_form"

def "data:normalization" "Process of organizing data to reduce redundancy and improve integrity."
ln data:normalization data.relational sys:is_a
ln data:normalization data:document_store @contrasts_with
ln data:normalization data:snowflake_schema @influences
set.add name="ontology.data" id="data:normalization"

def "data:olap" "Online Analytical Processing: multidimensional analysis for decision support."
ln data:olap data.warehouse sys:is_a
set.add name="ontology.data" id="data:olap"

def "data:olap_cube" "Multidimensional data structure enabling fast aggregation and slicing."
ln data:olap_cube data:olap sys:is_a
set.add name="ontology.data" id="data:olap_cube"

def "data:oracle" "Commercial RDBMS implementing SQL and relational concepts."
ln data:oracle data.relational sys:is_a
set.add name="ontology.data" id="data:oracle"

def "data:orc" "Optimized Row Columnar format for Hadoop ecosystems."
ln data:orc data.lake sys:is_a
set.add name="ontology.data" id="data:orc"

def "data:parquet" "Columnar storage format optimized for analytics."
ln data:parquet data.lake sys:is_a
ln data:parquet data:vector_database @used_with
set.add name="ontology.data" id="data:parquet"

def "data:path_traversal" "Navigating hierarchical namespaces using paths."
ln data:path_traversal data:unix_directory sys:is_a
ln data:path_traversal data:pointer_traversal @similar_to
ln data:path_traversal data:sql @influences
ln data:path_traversal data:key_value_store @related_to
set.add name="ontology.data" id="data:path_traversal"

def "data:pivot_table" "Excel feature for aggregating and summarizing tabular data, similar to OLAP operations."
ln data:pivot_table data:excel sys:is_a
ln data:pivot_table data:normalization @related_to
ln data:pivot_table data.warehouse @influences
ln data:pivot_table data:olap @analogous_to
ln data:pivot_table data:gold_layer @analogous_to
set.add name="ontology.data" id="data:pivot_table"

def "data:pointer_traversal" "Navigating records by following explicit pointers between them."
ln data:pointer_traversal data.early_db sys:is_a
ln data:pointer_traversal data:codasyl @implements
ln data:pointer_traversal data.gui_folder @influences
ln data:pointer_traversal data.spreadsheet @related_to
ln data:pointer_traversal data.nosql @influences
set.add name="ontology.data" id="data:pointer_traversal"

def "data:postgresql" "Open-source relational database with advanced features."
ln data:postgresql data.relational sys:is_a
set.add name="ontology.data" id="data:postgresql"

def "data:presto" "Distributed SQL query engine for large-scale data lakes."
ln data:presto data.lake sys:is_a
set.add name="ontology.data" id="data:presto"

def "data:punch_card" "Card with holes encoding data, used for early mechanical and digital processing."
ln data:punch_card data.pre_digital sys:is_a
ln data:punch_card data.early_db @precedes
set.add name="ontology.data" id="data:punch_card"

def "data:query_optimizer" "Component that transforms SQL queries into efficient execution plans."
ln data:query_optimizer data:sql sys:is_a
set.add name="ontology.data" id="data:query_optimizer"

def "data:rag" "Retrieval-Augmented Generation: combining LLMs with external knowledge via vector search."
ln data:rag data.ai_llm_era sys:is_a
set.add name="ontology.data" id="data:rag"

def "data:raw_zone" "Storage area for unprocessed raw data."
ln data:raw_zone data.lake sys:is_a
set.add name="ontology.data" id="data:raw_zone"

def "data:record_oriented_storage" "Storage model where data is organized as fixed or variable-length records."
ln data:record_oriented_storage data.filesystem sys:is_a
ln data:record_oriented_storage data.relational @influences
set.add name="ontology.data" id="data:record_oriented_storage"

def "data:redis" "In-memory key-value store supporting rich data structures."
ln data:redis data:key_value_store sys:is_a
set.add name="ontology.data" id="data:redis"

def "data:redshift" "Cloud-based MPP data warehouse by Amazon."
ln data:redshift data:mpp sys:is_a
set.add name="ontology.data" id="data:redshift"

def "data:relational_model" "Model representing data as relations (tables) with tuples and attributes."
ln data:relational_model data.relational sys:is_a
ln data:relational_model data:codd @defined_by
ln data:relational_model data.nosql @contrasts_with
set.add name="ontology.data" id="data:relational_model"

def "data:riak" "Distributed key-value store inspired by Amazon Dynamo."
ln data:riak data:key_value_store sys:is_a
set.add name="ontology.data" id="data:riak"

def "data:schema" "Logical description of database structure, record types, and relationships."
ln data:schema data.early_db sys:is_a
ln data:schema data.spreadsheet @influences
ln data:schema data.warehouse @precedes
ln data:schema data:relational_model @precedes
set.add name="ontology.data" id="data:schema"

def "data:schema_less_table" "Spreadsheet used without explicit schema, where structure is implicit in headers and usage."
ln data:schema_less_table data.spreadsheet sys:is_a
ln data:schema_less_table data.nosql @precedes
set.add name="ontology.data" id="data:schema_less_table"

def "data:schema_on_read" "Applying schema at query time rather than ingestion time."
ln data:schema_on_read data.lake sys:is_a
set.add name="ontology.data" id="data:schema_on_read"

def "data:semantic_retrieval" "Retrieving relevant items from a semantic space using vector similarity."
ln data:semantic_retrieval data:rag sys:is_a
set.add name="ontology.data" id="data:semantic_retrieval"

def "data:semantic_space" "High-dimensional space where semantically similar items are located near each other."
ln data:semantic_space data.ai_llm_era sys:is_a
set.add name="ontology.data" id="data:semantic_space"

def "data:sequential_file" "File organized in a fixed order, typically matching tape layout."
ln data:sequential_file data.filesystem sys:is_a
ln data:sequential_file data:magnetic_tape @implements
ln data:sequential_file data.pre_digital @evolves_from
set.add name="ontology.data" id="data:sequential_file"

def "data:shadow_it" "Unofficial, user-managed systems built with spreadsheets outside formal IT governance."
ln data:shadow_it data.spreadsheet sys:is_a
set.add name="ontology.data" id="data:shadow_it"

def "data:sheet_script_automation" "Script-based automation for spreadsheets (e.g., Apps Script), integrating external systems."
ln data:sheet_script_automation data:google_sheets sys:is_a
set.add name="ontology.data" id="data:sheet_script_automation"

def "data:silver_layer" "Lake layer storing cleaned and structured data."
ln data:silver_layer data.lake sys:is_a
set.add name="ontology.data" id="data:silver_layer"

def "data:slice_and_dice" "Filtering and reorienting OLAP cubes for analysis."
ln data:slice_and_dice data:olap sys:is_a
set.add name="ontology.data" id="data:slice_and_dice"

def "data:snowflake_schema" "Normalized variant of star schema with hierarchical dimensions."
ln data:snowflake_schema data.warehouse sys:is_a
set.add name="ontology.data" id="data:snowflake_schema"

def "data:spark_sql" "SQL engine built on Apache Spark for distributed processing."
ln data:spark_sql data.lake sys:is_a
set.add name="ontology.data" id="data:spark_sql"

def "data:spatial_navigation" "Navigating information by spatial arrangement rather than strict hierarchy."
ln data:spatial_navigation data:desktop_metaphor sys:is_a
ln data:spatial_navigation data:grid_model @influences
set.add name="ontology.data" id="data:spatial_navigation"

def "data:sql" "Structured Query Language for defining and manipulating relational data."
ln data:sql data.relational sys:is_a
ln data:sql data.warehouse @precedes
ln data:sql data:document_store @contrasts_with
ln data:sql data:olap @supports
ln data:sql data:hybrid_search @used_with
set.add name="ontology.data" id="data:sql"

def "data:star_schema" "Schema with central fact table and surrounding dimension tables."
ln data:star_schema data.warehouse sys:is_a
ln data:star_schema data:gold_layer @used_with
set.add name="ontology.data" id="data:star_schema"

def "data:subschema" "Application-specific view of a database schema."
ln data:subschema data.early_db sys:is_a
ln data:subschema data:schema @subset_of
ln data:subschema data.spreadsheet @influences
set.add name="ontology.data" id="data:subschema"

def "data:table" "Two-dimensional structure representing a relation."
ln data:table data:relational_model sys:is_a
ln data:table data.lake @influences
ln data:table data:fact_table @precedes
ln data:table data:embedding @contrasts_with
set.add name="ontology.data" id="data:table"

def "data:teradata" "Enterprise MPP data warehouse platform."
ln data:teradata data:mpp sys:is_a
set.add name="ontology.data" id="data:teradata"

def "data:transaction" "Unit of work executed with ACID guarantees."
ln data:transaction data:acid sys:is_a
set.add name="ontology.data" id="data:transaction"

def "data:transform" "Cleaning, normalizing, and reshaping data for analysis."
ln data:transform data:etl sys:is_a
set.add name="ontology.data" id="data:transform"

def "data:trino" "Successor to Presto, supporting federated queries across heterogeneous sources."
ln data:trino data.lake sys:is_a
set.add name="ontology.data" id="data:trino"

def "data:tuple" "Row in a relational table."
ln data:tuple data:relational_model sys:is_a
set.add name="ontology.data" id="data:tuple"

def "data:unix_directory" "Hierarchical directory structure in Unix, organizing files via paths and inodes."
ln data:unix_directory data.directory sys:is_a
ln data:unix_directory data:hierarchical_model @influences
ln data:unix_directory data:table @analogous_to
ln data:unix_directory data:desktop_metaphor @precedes
set.add name="ontology.data" id="data:unix_directory"

def "data:vba_macro" "Excel macro/VBA automation, enabling procedural logic over spreadsheet data."
ln data:vba_macro data:excel sys:is_a
set.add name="ontology.data" id="data:vba_macro"

def "data:vector_database" "Database optimized for storing and querying embedding vectors."
ln data:vector_database data.ai_llm_era sys:is_a
set.add name="ontology.data" id="data:vector_database"

def "data:visicalc" "VisiCalc, the first widely used personal computer spreadsheet, enabling interactive recalculation."
ln data:visicalc data.spreadsheet sys:is_a
set.add name="ontology.data" id="data:visicalc"

def "data:vsam" "Virtual Storage Access Method: IBM's advanced indexed file system supporting multiple access paths."
ln data:vsam data.filesystem sys:is_a
ln data:vsam data:isam @evolves_from
ln data:vsam data.early_db @precedes
set.add name="ontology.data" id="data:vsam"

def "data:workbook" "Excel workbook: container for multiple worksheets, often used as a logical dataset."
ln data:workbook data:excel sys:is_a
ln data:workbook data.gui_folder @analogous_to
set.add name="ontology.data" id="data:workbook"

def "data:workbook_as_folder" "Spreadsheet workbook functioning as a folder containing multiple sheets."
ln data:workbook_as_folder data.directory sys:is_a
set.add name="ontology.data" id="data:workbook_as_folder"

def "data:worksheet" "Sheet within a workbook, functioning as a table-like structure."
ln data:worksheet data:table @similar_to
ln data:worksheet data:workbook sys:is_a
ln data:worksheet data.lake @used_with
ln data:worksheet data:file_icon @analogous_to
ln data:worksheet data:raw_zone @used_with
set.add name="ontology.data" id="data:worksheet"

def "data:worksheet_as_file" "Spreadsheet worksheet functioning as a file within a workbook."
ln data:worksheet_as_file data:workbook_as_folder sys:is_a
set.add name="ontology.data" id="data:worksheet_as_file"
