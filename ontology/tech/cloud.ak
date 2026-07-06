# Akasha ontology — namespace: cloud
# atoms: 26

def "cloud:anycast" "Routing technique where multiple nodes share the same IP."
ln cloud:anycast cloud_networking.distributed sys:is_a
ln cloud:anycast cloud:pop @supports
set.add name="ontology.cloud_networking" id="cloud:anycast"

def "cloud:api_gateway" "Gateway managing API traffic."
ln cloud:api_gateway cloud_networking.service_mesh sys:is_a
set.add name="ontology.cloud_networking" id="cloud:api_gateway"

def "cloud:cdn" "Content Delivery Network for global content distribution."
ln cloud:cdn cloud_networking.edge sys:is_a
set.add name="ontology.cloud_networking" id="cloud:cdn"

def "cloud:direct_connect" "Dedicated private connection to cloud provider."
ln cloud:direct_connect cloud_networking.connectivity sys:is_a
ln cloud:direct_connect cloud:vpc @connects
set.add name="ontology.cloud_networking" id="cloud:direct_connect"

def "cloud:edge_compute" "Compute resources deployed close to users."
ln cloud:edge_compute cloud_networking.edge sys:is_a
set.add name="ontology.cloud_networking" id="cloud:edge_compute"

def "cloud:express_route" "Private connection for Microsoft Azure."
ln cloud:express_route cloud_networking.connectivity sys:is_a
set.add name="ontology.cloud_networking" id="cloud:express_route"

def "cloud:failover" "Automatic switching to backup systems."
ln cloud:failover cloud_networking.distributed sys:is_a
set.add name="ontology.cloud_networking" id="cloud:failover"

def "cloud:global_load_balancing" "Load balancing across regions."
ln cloud:global_load_balancing cloud_networking.distributed sys:is_a
ln cloud:global_load_balancing cloud:cdn @supports
set.add name="ontology.cloud_networking" id="cloud:global_load_balancing"

def "cloud:iam" "Identity and Access Management for cloud resources."
ln cloud:iam cloud_networking.security sys:is_a
ln cloud:iam cloud:api_gateway @controls
set.add name="ontology.cloud_networking" id="cloud:iam"

def "cloud:internet_gateway" "Gateway enabling public internet access."
ln cloud:internet_gateway cloud_networking.foundation sys:is_a
set.add name="ontology.cloud_networking" id="cloud:internet_gateway"

def "cloud:mtls" "Mutual TLS for service authentication."
ln cloud:mtls cloud_networking.service_mesh sys:is_a
set.add name="ontology.cloud_networking" id="cloud:mtls"

def "cloud:nacl" "Network ACL controlling subnet-level traffic."
ln cloud:nacl cloud_networking.security sys:is_a
set.add name="ontology.cloud_networking" id="cloud:nacl"

def "cloud:nat_gateway" "Gateway enabling outbound internet access for private subnets."
ln cloud:nat_gateway cloud_networking.foundation sys:is_a
set.add name="ontology.cloud_networking" id="cloud:nat_gateway"

def "cloud:overlay" "Virtual network built on top of physical infrastructure."
ln cloud:overlay cloud_networking.sdn sys:is_a
ln cloud:overlay cloud:vpc @supports
set.add name="ontology.cloud_networking" id="cloud:overlay"

def "cloud:pop" "Point of Presence for edge delivery."
ln cloud:pop cloud_networking.edge sys:is_a
set.add name="ontology.cloud_networking" id="cloud:pop"

def "cloud:private_link" "Private connectivity to cloud services."
ln cloud:private_link cloud_networking.security sys:is_a
set.add name="ontology.cloud_networking" id="cloud:private_link"

def "cloud:route_table" "Routing rules controlling traffic flow."
ln cloud:route_table cloud_networking.foundation sys:is_a
set.add name="ontology.cloud_networking" id="cloud:route_table"

def "cloud:service_mesh_core" "Core service mesh providing traffic management and security."
ln cloud:service_mesh_core cloud_networking.service_mesh sys:is_a
set.add name="ontology.cloud_networking" id="cloud:service_mesh_core"

def "cloud:sidecar_proxy" "Proxy deployed alongside services for mesh control."
ln cloud:sidecar_proxy cloud_networking.service_mesh sys:is_a
ln cloud:sidecar_proxy cloud:mtls @supports
set.add name="ontology.cloud_networking" id="cloud:sidecar_proxy"

def "cloud:site_to_site_vpn" "Encrypted tunnel between on-prem and cloud."
ln cloud:site_to_site_vpn cloud_networking.connectivity sys:is_a
set.add name="ontology.cloud_networking" id="cloud:site_to_site_vpn"

def "cloud:subnet" "Logical subdivision of a VPC."
ln cloud:subnet cloud_networking.foundation sys:is_a
set.add name="ontology.cloud_networking" id="cloud:subnet"

def "cloud:underlay" "Physical network supporting virtual overlays."
ln cloud:underlay cloud_networking.sdn sys:is_a
set.add name="ontology.cloud_networking" id="cloud:underlay"

def "cloud:virtual_switch" "Software-based switch for virtual networks."
ln cloud:virtual_switch cloud_networking.sdn sys:is_a
set.add name="ontology.cloud_networking" id="cloud:virtual_switch"

def "cloud:vpc" "Virtual Private Cloud — isolated virtual network."
ln cloud:vpc cloud_networking.foundation sys:is_a
set.add name="ontology.cloud_networking" id="cloud:vpc"

def "cloud:vxlan" "Overlay tunneling protocol for virtual networks."
ln cloud:vxlan cloud_networking.sdn sys:is_a
set.add name="ontology.cloud_networking" id="cloud:vxlan"

def "cloud:waf" "Web Application Firewall protecting HTTP traffic."
ln cloud:waf cloud_networking.security sys:is_a
set.add name="ontology.cloud_networking" id="cloud:waf"
