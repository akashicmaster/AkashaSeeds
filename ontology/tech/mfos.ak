# Akasha ontology — namespace: mfos
# atoms: 29

def "mfos.batch_processing" "Batch processing and job control on mainframes."
ln mfos.batch_processing ont.mainframe_os sys:part_of
set.add name="ontology.mainframe_os" id="mfos.batch_processing"

def "mfos.family" "Mainframe OS families and lineages."
ln mfos.family ont.mainframe_os sys:part_of
set.add name="ontology.mainframe_os" id="mfos.family"

def "mfos.fujitsu" "Fujitsu mainframe OS family including OSIV, MSP, and XSP."
ln mfos.fujitsu ont.mainframe_os sys:part_of
set.add name="ontology.mainframe_os" id="mfos.fujitsu"

def "mfos.hitachi" "Hitachi mainframe OS family including VOS3."
ln mfos.hitachi ont.mainframe_os sys:part_of
set.add name="ontology.mainframe_os" id="mfos.hitachi"

def "mfos.ibm" "IBM mainframe OS family including z/OS, z/VM, and z/VSE."
ln mfos.ibm ont.mainframe_os sys:part_of
set.add name="ontology.mainframe_os" id="mfos.ibm"

def "mfos.operations" "Operations, reliability, and system management for mainframes."
ln mfos.operations ont.mainframe_os sys:part_of
set.add name="ontology.mainframe_os" id="mfos.operations"

def "mfos.virtualization" "Virtualization and partitioning on mainframes."
ln mfos.virtualization ont.mainframe_os sys:part_of
set.add name="ontology.mainframe_os" id="mfos.virtualization"

def "mfos:cics" "Customer Information Control System, IBM transaction monitor."
ln mfos:cics mfos.batch_processing sys:is_a
ln mfos:cics mfos:zos @runs_on
set.add name="ontology.mainframe_os" id="mfos:cics"

def "mfos:fujitsu_family" "Fujitsu mainframe OS lineage including OSIV, MSP, and XSP."
ln mfos:fujitsu_family mfos.family sys:is_a
set.add name="ontology.mainframe_os" id="mfos:fujitsu_family"

def "mfos:high_availability" "High availability features of mainframe OS."
ln mfos:high_availability mfos.operations sys:is_a
set.add name="ontology.mainframe_os" id="mfos:high_availability"

def "mfos:hitachi_family" "Hitachi mainframe OS lineage including VOS3."
ln mfos:hitachi_family mfos.family sys:is_a
set.add name="ontology.mainframe_os" id="mfos:hitachi_family"

def "mfos:ibm_family" "IBM mainframe OS lineage from OS/360 to z/OS, z/VM, and z/VSE."
ln mfos:ibm_family mfos.family sys:is_a
set.add name="ontology.mainframe_os" id="mfos:ibm_family"

def "mfos:ims" "IBM Information Management System, hierarchical DB and transaction monitor."
ln mfos:ims mfos.batch_processing sys:is_a
ln mfos:ims mfos:zos @runs_on
set.add name="ontology.mainframe_os" id="mfos:ims"

def "mfos:jcl" "Job Control Language used to define batch jobs."
ln mfos:jcl mfos.batch_processing sys:is_a
set.add name="ontology.mainframe_os" id="mfos:jcl"

def "mfos:jes2" "Job Entry Subsystem 2 for z/OS."
ln mfos:jes2 mfos.batch_processing sys:is_a
ln mfos:jes2 mfos:zos @runs_on
set.add name="ontology.mainframe_os" id="mfos:jes2"

def "mfos:lpar" "Logical Partitioning on mainframes."
ln mfos:lpar mfos.virtualization sys:is_a
set.add name="ontology.mainframe_os" id="mfos:lpar"

def "mfos:mainframe_hypervisor" "Hypervisor capabilities provided by z/VM and similar systems."
ln mfos:mainframe_hypervisor mfos.virtualization sys:is_a
set.add name="ontology.mainframe_os" id="mfos:mainframe_hypervisor"

def "mfos:msp_os" "Fujitsu MSP mainframe operating system."
ln mfos:msp_os mfos.fujitsu sys:is_a
set.add name="ontology.mainframe_os" id="mfos:msp_os"

def "mfos:mvs" "Multiple Virtual Storage (MVS), predecessor of z/OS."
ln mfos:mvs mfos.ibm sys:is_a
set.add name="ontology.mainframe_os" id="mfos:mvs"

def "mfos:os_360" "IBM OS/360, ancestor of modern IBM mainframe OS."
ln mfos:os_360 mfos.ibm sys:is_a
set.add name="ontology.mainframe_os" id="mfos:os_360"

def "mfos:osiv" "Fujitsu OSIV mainframe operating system family."
ln mfos:osiv mfos.fujitsu sys:is_a
set.add name="ontology.mainframe_os" id="mfos:osiv"

def "mfos:recovery_management" "Recovery and restart management for mainframe workloads."
ln mfos:recovery_management mfos.operations sys:is_a
set.add name="ontology.mainframe_os" id="mfos:recovery_management"

def "mfos:smf" "System Management Facility (SMF) logging and metrics in z/OS."
ln mfos:smf mfos.operations sys:is_a
ln mfos:smf mfos:zos @runs_on
set.add name="ontology.mainframe_os" id="mfos:smf"

def "mfos:vos1" "Hitachi VOS1 mainframe OS (historical)."
ln mfos:vos1 mfos.hitachi sys:is_a
set.add name="ontology.mainframe_os" id="mfos:vos1"

def "mfos:vos3_os" "Hitachi VOS3 mainframe OS for large-scale systems."
ln mfos:vos3_os mfos.hitachi sys:is_a
set.add name="ontology.mainframe_os" id="mfos:vos3_os"

def "mfos:xsp" "Fujitsu XSP mainframe operating system."
ln mfos:xsp mfos.fujitsu sys:is_a
set.add name="ontology.mainframe_os" id="mfos:xsp"

def "mfos:zos" "IBM z/OS, primary mainframe OS for batch and transaction processing."
ln mfos:zos mfos.ibm sys:is_a
ln mfos:zos mfos:lpar @runs_within
set.add name="ontology.mainframe_os" id="mfos:zos"

def "mfos:zvm" "IBM z/VM, virtualization-oriented mainframe OS."
ln mfos:zvm mfos.ibm sys:is_a
ln mfos:zvm mfos:mainframe_hypervisor @implements
set.add name="ontology.mainframe_os" id="mfos:zvm"

def "mfos:zvse" "IBM z/VSE, mainframe OS for smaller workloads."
ln mfos:zvse mfos.ibm sys:is_a
set.add name="ontology.mainframe_os" id="mfos:zvse"
