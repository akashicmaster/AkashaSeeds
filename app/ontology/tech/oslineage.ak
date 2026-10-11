# Akasha ontology — namespace: oslineage
# atoms: 8

def "oslineage.bsd" "BSD family including FreeBSD, NetBSD, OpenBSD, and Darwin lineage."
ln oslineage.bsd ont.os_lineage sys:part_of
set.add name="ontology.os_lineage" id="oslineage.bsd"

def "oslineage.linux" "Linux kernel and its distribution families."
ln oslineage.linux ont.os_lineage sys:part_of
set.add name="ontology.os_lineage" id="oslineage.linux"

def "oslineage.mainframe" "Mainframe OS lineage including IBM z/OS, z/VM, and Japanese mainframe OS."
ln oslineage.mainframe ont.os_lineage sys:part_of
set.add name="ontology.os_lineage" id="oslineage.mainframe"

def "oslineage.mobile" "Mobile OS lineage including Android, iOS, and historical mobile OS."
ln oslineage.mobile ont.os_lineage sys:part_of
set.add name="ontology.os_lineage" id="oslineage.mobile"

def "oslineage.rtos" "Real-time and embedded OS lineage including QNX, VxWorks, and FreeRTOS."
ln oslineage.rtos ont.os_lineage sys:part_of
set.add name="ontology.os_lineage" id="oslineage.rtos"

def "oslineage.unix" "UNIX family including AT&T UNIX, System V, BSD, and descendants."
ln oslineage.unix ont.os_lineage sys:part_of
set.add name="ontology.os_lineage" id="oslineage.unix"

def "oslineage.windows" "Windows OS lineage including DOS-based and NT-based systems."
ln oslineage.windows ont.os_lineage sys:part_of
set.add name="ontology.os_lineage" id="oslineage.windows"

def "oslineage:mainframe_anchor" "Anchor node linking mainframe OS lineage to detailed mainframe OS domain."
ln oslineage:mainframe_anchor ont.mainframe_os sys:related_to
set.add name="ontology.mainframe_os" id="oslineage:mainframe_anchor"
