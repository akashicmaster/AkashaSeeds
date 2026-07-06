# Akasha ontology — namespace: virt
# atoms: 24

def "virt:cgroup" "Linux cgroups for resource control."
ln virt:cgroup virtualization.container sys:is_a
set.add name="ontology.virtualization" id="virt:cgroup"

def "virt:chroot" "Filesystem isolation using chroot."
ln virt:chroot virtualization.os sys:is_a
set.add name="ontology.virtualization" id="virt:chroot"

def "virt:clone" "Virtual disk cloning."
ln virt:clone virtualization.storage sys:is_a
set.add name="ontology.virtualization" id="virt:clone"

def "virt:clr" ".NET Common Language Runtime."
ln virt:clr virtualization.app sys:is_a
set.add name="ontology.virtualization" id="virt:clr"

def "virt:docker" "Docker container engine."
ln virt:docker virtualization.container sys:is_a
ln virt:docker virt:namespace @uses
set.add name="ontology.virtualization" id="virt:docker"

def "virt:esxi" "VMware ESXi hypervisor."
ln virt:esxi virtualization.compute sys:is_a
set.add name="ontology.virtualization" id="virt:esxi"

def "virt:hyperv" "Microsoft Hyper-V hypervisor."
ln virt:hyperv virtualization.compute sys:is_a
set.add name="ontology.virtualization" id="virt:hyperv"

def "virt:jail" "FreeBSD jail isolation."
ln virt:jail virtualization.os sys:is_a
set.add name="ontology.virtualization" id="virt:jail"

def "virt:jvm" "Java Virtual Machine."
ln virt:jvm virtualization.app sys:is_a
set.add name="ontology.virtualization" id="virt:jvm"

def "virt:kubernetes" "Kubernetes container orchestration."
ln virt:kubernetes virtualization.management sys:is_a
set.add name="ontology.virtualization" id="virt:kubernetes"

def "virt:kvm" "Kernel-based Virtual Machine hypervisor."
ln virt:kvm virtualization.compute sys:is_a
set.add name="ontology.virtualization" id="virt:kvm"

def "virt:microvm" "Lightweight virtual machine (e.g., Firecracker)."
ln virt:microvm virtualization.os sys:is_a
ln virt:microvm virt:kubernetes @supports
set.add name="ontology.virtualization" id="virt:microvm"

def "virt:namespace" "Linux namespace isolation."
ln virt:namespace virtualization.container sys:is_a
set.add name="ontology.virtualization" id="virt:namespace"

def "virt:nfv" "Network Function Virtualization."
ln virt:nfv virtualization.network sys:is_a
set.add name="ontology.virtualization" id="virt:nfv"

def "virt:openstack" "OpenStack cloud management platform."
ln virt:openstack virtualization.management sys:is_a
set.add name="ontology.virtualization" id="virt:openstack"

def "virt:runc" "OCI-compliant container runtime."
ln virt:runc virtualization.container sys:is_a
set.add name="ontology.virtualization" id="virt:runc"

def "virt:snapshot" "Snapshot of virtual storage state."
ln virt:snapshot virtualization.storage sys:is_a
set.add name="ontology.virtualization" id="virt:snapshot"

def "virt:terraform" "Infrastructure as Code tool."
ln virt:terraform virtualization.management sys:is_a
set.add name="ontology.virtualization" id="virt:terraform"

def "virt:thin_provisioning" "Thin provisioning for virtual storage."
ln virt:thin_provisioning virtualization.storage sys:is_a
ln virt:thin_provisioning virt:snapshot @supports
set.add name="ontology.virtualization" id="virt:thin_provisioning"

def "virt:vcenter" "VMware vCenter management."
ln virt:vcenter virtualization.management sys:is_a
set.add name="ontology.virtualization" id="virt:vcenter"

def "virt:virtual_switch" "Software-based network switch."
ln virt:virtual_switch virtualization.network sys:is_a
set.add name="ontology.virtualization" id="virt:virtual_switch"

def "virt:vxlan" "Virtual Extensible LAN overlay protocol."
ln virt:vxlan virtualization.network sys:is_a
ln virt:vxlan virt:virtual_switch @requires
set.add name="ontology.virtualization" id="virt:vxlan"

def "virt:wasm" "WebAssembly runtime."
ln virt:wasm virtualization.app sys:is_a
ln virt:wasm virt:jvm @contrasts_with
set.add name="ontology.virtualization" id="virt:wasm"

def "virt:xen" "Xen hypervisor."
ln virt:xen virtualization.compute sys:is_a
set.add name="ontology.virtualization" id="virt:xen"
