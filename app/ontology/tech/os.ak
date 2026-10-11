# Akasha ontology — namespace: os
# atoms: 30

def "os:android" "Android mobile operating system."
ln os:android oslineage.mobile sys:is_a
set.add name="ontology.os_lineage" id="os:android"

def "os:arch" "Arch Linux distribution."
ln os:arch oslineage.linux sys:is_a
set.add name="ontology.os_lineage" id="os:arch"

def "os:att_unix" "Original AT&T UNIX from Bell Labs."
ln os:att_unix oslineage.unix sys:is_a
ln os:att_unix os:system_v @ancestor_of
ln os:att_unix os:bsd_4x @ancestor_of
set.add name="ontology.os_lineage" id="os:att_unix"

def "os:bsd_4x" "4.x BSD releases from Berkeley."
ln os:bsd_4x oslineage.unix sys:is_a
ln os:bsd_4x os:darwin @ancestor_of
set.add name="ontology.os_lineage" id="os:bsd_4x"

def "os:darwin" "Darwin OS forming the base of macOS and iOS."
ln os:darwin oslineage.bsd sys:is_a
ln os:darwin os:ios @base_of
set.add name="ontology.os_lineage" id="os:darwin"

def "os:debian" "Debian Linux distribution."
ln os:debian oslineage.linux sys:is_a
set.add name="ontology.os_lineage" id="os:debian"

def "os:freebsd" "FreeBSD operating system."
ln os:freebsd oslineage.bsd sys:is_a
set.add name="ontology.os_lineage" id="os:freebsd"

def "os:freertos" "FreeRTOS embedded operating system."
ln os:freertos oslineage.rtos sys:is_a
set.add name="ontology.os_lineage" id="os:freertos"

def "os:harmonyos" "Huawei HarmonyOS."
ln os:harmonyos oslineage.mobile sys:is_a
set.add name="ontology.os_lineage" id="os:harmonyos"

def "os:ios" "Apple iOS mobile operating system."
ln os:ios oslineage.mobile sys:is_a
set.add name="ontology.os_lineage" id="os:ios"

def "os:linux_kernel" "Linux kernel created by Linus Torvalds."
ln os:linux_kernel oslineage.linux sys:is_a
ln os:linux_kernel os:android @base_of
set.add name="ontology.os_lineage" id="os:linux_kernel"

def "os:msdos" "MS-DOS operating system."
ln os:msdos oslineage.windows sys:is_a
set.add name="ontology.os_lineage" id="os:msdos"

def "os:msp" "Fujitsu MSP mainframe OS."
ln os:msp oslineage.mainframe sys:is_a
set.add name="ontology.os_lineage" id="os:msp"

def "os:netbsd" "NetBSD operating system."
ln os:netbsd oslineage.bsd sys:is_a
set.add name="ontology.os_lineage" id="os:netbsd"

def "os:openbsd" "OpenBSD operating system."
ln os:openbsd oslineage.bsd sys:is_a
set.add name="ontology.os_lineage" id="os:openbsd"

def "os:qnx" "QNX real-time operating system."
ln os:qnx oslineage.rtos sys:is_a
set.add name="ontology.os_lineage" id="os:qnx"

def "os:rhel" "Red Hat Enterprise Linux."
ln os:rhel oslineage.linux sys:is_a
set.add name="ontology.os_lineage" id="os:rhel"

def "os:sles" "SUSE Linux Enterprise Server."
ln os:sles oslineage.linux sys:is_a
set.add name="ontology.os_lineage" id="os:sles"

def "os:symbian" "Symbian OS (historical mobile OS)."
ln os:symbian oslineage.mobile sys:is_a
set.add name="ontology.os_lineage" id="os:symbian"

def "os:system_v" "UNIX System V Release 4."
ln os:system_v oslineage.unix sys:is_a
set.add name="ontology.os_lineage" id="os:system_v"

def "os:ubuntu" "Ubuntu Linux distribution."
ln os:ubuntu oslineage.linux sys:is_a
set.add name="ontology.os_lineage" id="os:ubuntu"

def "os:vos3" "Hitachi VOS3 mainframe OS."
ln os:vos3 oslineage.mainframe sys:is_a
set.add name="ontology.os_lineage" id="os:vos3"

def "os:vxworks" "VxWorks real-time operating system."
ln os:vxworks oslineage.rtos sys:is_a
set.add name="ontology.os_lineage" id="os:vxworks"

def "os:windows_11" "Windows 11 operating system."
ln os:windows_11 oslineage.windows sys:is_a
set.add name="ontology.os_lineage" id="os:windows_11"

def "os:windows_9x" "Windows 95/98/Me family."
ln os:windows_9x oslineage.windows sys:is_a
set.add name="ontology.os_lineage" id="os:windows_9x"

def "os:windows_nt" "Windows NT family."
ln os:windows_nt oslineage.windows sys:is_a
ln os:windows_nt os:windows_11 @ancestor_of
set.add name="ontology.os_lineage" id="os:windows_nt"

def "os:zephyr" "Zephyr RTOS for embedded systems."
ln os:zephyr oslineage.rtos sys:is_a
set.add name="ontology.os_lineage" id="os:zephyr"

def "os:zos" "IBM z/OS mainframe operating system."
ln os:zos oslineage.mainframe sys:is_a
set.add name="ontology.os_lineage" id="os:zos"

def "os:zvm" "IBM z/VM virtualization OS."
ln os:zvm oslineage.mainframe sys:is_a
set.add name="ontology.os_lineage" id="os:zvm"

def "os:zvse" "IBM z/VSE operating system."
ln os:zvse oslineage.mainframe sys:is_a
set.add name="ontology.os_lineage" id="os:zvse"
