# Akasha ontology — namespace: datamig
# atoms: 29

def "datamig.assessment" "Assessment of existing data, quality, structure, and dependencies before migration."
ln datamig.assessment ont.data_migration sys:part_of
set.add name="ontology.data_migration" id="datamig.assessment"

def "datamig.cleansing" "Data cleansing and normalization prior to or during migration."
ln datamig.cleansing ont.data_migration sys:part_of
set.add name="ontology.data_migration" id="datamig.cleansing"

def "datamig.execution" "Execution of migration runs, cutover, and rollback strategies."
ln datamig.execution ont.data_migration sys:part_of
set.add name="ontology.data_migration" id="datamig.execution"

def "datamig.mapping" "Source-to-target data mapping and transformation rules."
ln datamig.mapping ont.data_migration sys:part_of
set.add name="ontology.data_migration" id="datamig.mapping"

def "datamig.sync" "Synchronization strategies between legacy and target systems."
ln datamig.sync ont.data_migration sys:part_of
set.add name="ontology.data_migration" id="datamig.sync"

def "datamig.transform" "ETL/ELT processes and schema transformations."
ln datamig.transform ont.data_migration sys:part_of
set.add name="ontology.data_migration" id="datamig.transform"

def "datamig.validation" "Post-migration validation, data quality checks, and optimization."
ln datamig.validation ont.data_migration sys:part_of
set.add name="ontology.data_migration" id="datamig.validation"

def "datamig:batch_sync" "Batch-based synchronization between legacy and target."
ln datamig:batch_sync datamig.sync sys:is_a
set.add name="ontology.data_migration" id="datamig:batch_sync"

def "datamig:cdc_sync" "Change Data Capture-based synchronization."
ln datamig:cdc_sync datamig.sync sys:is_a
ln datamig:cdc_sync datamig:streaming_sync @evolves_to
ln datamig:cdc_sync datamig:cutover @enables_low_downtime
set.add name="ontology.data_migration" id="datamig:cdc_sync"

def "datamig:cutover" "Final switch from legacy to target system."
ln datamig:cutover datamig.execution sys:is_a
set.add name="ontology.data_migration" id="datamig:cutover"

def "datamig:data_consistency_check" "Validation of referential and logical consistency after migration."
ln datamig:data_consistency_check datamig.validation sys:is_a
set.add name="ontology.data_migration" id="datamig:data_consistency_check"

def "datamig:data_dependency_map" "Mapping dependencies between tables, jobs, and interfaces."
ln datamig:data_dependency_map datamig.assessment sys:is_a
set.add name="ontology.data_migration" id="datamig:data_dependency_map"

def "datamig:data_model_reverse_engineering" "Reverse engineering of legacy data models and relationships."
ln datamig:data_model_reverse_engineering datamig.assessment sys:is_a
set.add name="ontology.data_migration" id="datamig:data_model_reverse_engineering"

def "datamig:data_quality_assessment" "Assessment of data quality including nulls, duplicates, and inconsistencies."
ln datamig:data_quality_assessment datamig.assessment sys:is_a
ln datamig:data_quality_assessment datamig:data_quality_monitoring @informs
set.add name="ontology.data_migration" id="datamig:data_quality_assessment"

def "datamig:data_quality_monitoring" "Ongoing monitoring of data quality post-migration."
ln datamig:data_quality_monitoring datamig.validation sys:is_a
set.add name="ontology.data_migration" id="datamig:data_quality_monitoring"

def "datamig:deduplication" "Removing duplicate records."
ln datamig:deduplication datamig.cleansing sys:is_a
set.add name="ontology.data_migration" id="datamig:deduplication"

def "datamig:elt" "ELT pipeline for data migration."
ln datamig:elt datamig.transform sys:is_a
set.add name="ontology.data_migration" id="datamig:elt"

def "datamig:etl" "ETL pipeline for data migration."
ln datamig:etl datamig.transform sys:is_a
ln datamig:etl datamig:batch_sync @typically_implemented_as
set.add name="ontology.data_migration" id="datamig:etl"

def "datamig:implicit_rule_extraction" "Extraction of implicit business rules from legacy data."
ln datamig:implicit_rule_extraction datamig.mapping sys:is_a
set.add name="ontology.data_migration" id="datamig:implicit_rule_extraction"

def "datamig:mapping_dictionary" "Formal mapping of source fields to target fields and rules."
ln datamig:mapping_dictionary datamig.mapping sys:is_a
set.add name="ontology.data_migration" id="datamig:mapping_dictionary"

def "datamig:master_data_cleanup" "Cleaning and consolidating master data."
ln datamig:master_data_cleanup datamig.cleansing sys:is_a
set.add name="ontology.data_migration" id="datamig:master_data_cleanup"

def "datamig:migration_rehearsal" "Trial migration run for validation and timing."
ln datamig:migration_rehearsal datamig.execution sys:is_a
ln datamig:migration_rehearsal datamig:cutover @precedes
set.add name="ontology.data_migration" id="datamig:migration_rehearsal"

def "datamig:migration_window" "Planned time window for migration execution."
ln datamig:migration_window datamig.execution sys:is_a
set.add name="ontology.data_migration" id="datamig:migration_window"

def "datamig:normalization" "Normalizing data formats and codes."
ln datamig:normalization datamig.cleansing sys:is_a
set.add name="ontology.data_migration" id="datamig:normalization"

def "datamig:performance_validation" "Performance validation of migrated workloads."
ln datamig:performance_validation datamig.validation sys:is_a
set.add name="ontology.data_migration" id="datamig:performance_validation"

def "datamig:rollback_strategy" "Strategy to revert migration if issues occur."
ln datamig:rollback_strategy datamig.execution sys:is_a
set.add name="ontology.data_migration" id="datamig:rollback_strategy"

def "datamig:schema_transformation" "Transformation of schema between legacy and target models."
ln datamig:schema_transformation datamig.transform sys:is_a
set.add name="ontology.data_migration" id="datamig:schema_transformation"

def "datamig:streaming_sync" "Streaming-based real-time synchronization."
ln datamig:streaming_sync datamig.sync sys:is_a
set.add name="ontology.data_migration" id="datamig:streaming_sync"

def "datamig:transformation_rule" "Field-level transformation rule."
ln datamig:transformation_rule datamig.mapping sys:is_a
set.add name="ontology.data_migration" id="datamig:transformation_rule"
