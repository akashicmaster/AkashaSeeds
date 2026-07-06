# Akasha ontology — namespace: cyber
# atoms: 38

def "cyber.application_security" "Application security including OWASP, API security, SAST, and DAST."
ln cyber.application_security ont.cybersecurity sys:part_of
set.add name="ontology.cybersecurity" id="cyber.application_security"

def "cyber.cloud_security" "Cloud security including CSPM, CWPP, IAM, and encryption."
ln cyber.cloud_security ont.cybersecurity sys:part_of
set.add name="ontology.cybersecurity" id="cyber.cloud_security"

def "cyber.defense" "Defense technologies including firewalls, IDS/IPS, EDR, SIEM, and SOAR."
ln cyber.defense ont.cybersecurity sys:part_of
set.add name="ontology.cybersecurity" id="cyber.defense"

def "cyber.grc" "Governance, risk, and compliance including ISO27001, NIST, and SOC2."
ln cyber.grc ont.cybersecurity sys:part_of
set.add name="ontology.cybersecurity" id="cyber.grc"

def "cyber.incident_response" "Incident response including forensics, threat intelligence, and SOC operations."
ln cyber.incident_response ont.cybersecurity sys:part_of
set.add name="ontology.cybersecurity" id="cyber.incident_response"

def "cyber.network_security" "Network security including zero trust, segmentation, VPN, and WAF."
ln cyber.network_security ont.cybersecurity sys:part_of
set.add name="ontology.cybersecurity" id="cyber.network_security"

def "cyber.threats" "Cyber threats including malware, phishing, APT, exploits, and ransomware."
ln cyber.threats ont.cybersecurity sys:part_of
set.add name="ontology.cybersecurity" id="cyber.threats"

def "cyber:api_security" "API security controls."
ln cyber:api_security cyber.application_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:api_security"

def "cyber:apt" "Advanced Persistent Threat."
ln cyber:apt cyber.threats sys:is_a
set.add name="ontology.cybersecurity" id="cyber:apt"

def "cyber:cspm" "Cloud Security Posture Management."
ln cyber:cspm cyber.cloud_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:cspm"

def "cyber:cwpp" "Cloud Workload Protection Platform."
ln cyber:cwpp cyber.cloud_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:cwpp"

def "cyber:dast" "Dynamic Application Security Testing."
ln cyber:dast cyber.application_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:dast"

def "cyber:edr" "Endpoint Detection and Response."
ln cyber:edr cyber.defense sys:is_a
set.add name="ontology.cybersecurity" id="cyber:edr"

def "cyber:exploit" "Attack leveraging software vulnerabilities."
ln cyber:exploit cyber.threats sys:is_a
set.add name="ontology.cybersecurity" id="cyber:exploit"

def "cyber:firewall" "Network firewall."
ln cyber:firewall cyber.defense sys:is_a
set.add name="ontology.cybersecurity" id="cyber:firewall"

def "cyber:forensics" "Digital forensics."
ln cyber:forensics cyber.incident_response sys:is_a
set.add name="ontology.cybersecurity" id="cyber:forensics"

def "cyber:iam" "Identity and Access Management."
ln cyber:iam cyber.cloud_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:iam"

def "cyber:ids" "Intrusion Detection System."
ln cyber:ids cyber.defense sys:is_a
set.add name="ontology.cybersecurity" id="cyber:ids"

def "cyber:ips" "Intrusion Prevention System."
ln cyber:ips cyber.defense sys:is_a
set.add name="ontology.cybersecurity" id="cyber:ips"

def "cyber:ir_process" "Incident response process."
ln cyber:ir_process cyber.incident_response sys:is_a
set.add name="ontology.cybersecurity" id="cyber:ir_process"

def "cyber:iso27001" "ISO/IEC 27001 security standard."
ln cyber:iso27001 cyber.grc sys:is_a
set.add name="ontology.cybersecurity" id="cyber:iso27001"

def "cyber:kms" "Key Management Service."
ln cyber:kms cyber.cloud_security sys:is_a
ln cyber:kms cyber:ransomware @mitigates
set.add name="ontology.cybersecurity" id="cyber:kms"

def "cyber:malware" "Malicious software including viruses, worms, and trojans."
ln cyber:malware cyber.threats sys:is_a
set.add name="ontology.cybersecurity" id="cyber:malware"

def "cyber:nist_cs" "NIST Cybersecurity Framework."
ln cyber:nist_cs cyber.grc sys:is_a
set.add name="ontology.cybersecurity" id="cyber:nist_cs"

def "cyber:owasp_top10" "OWASP Top 10 application risks."
ln cyber:owasp_top10 cyber.application_security sys:is_a
ln cyber:owasp_top10 cyber:api_security @related_to
set.add name="ontology.cybersecurity" id="cyber:owasp_top10"

def "cyber:phishing" "Social engineering attack to steal credentials."
ln cyber:phishing cyber.threats sys:is_a
set.add name="ontology.cybersecurity" id="cyber:phishing"

def "cyber:ransomware" "Malware encrypting data for ransom."
ln cyber:ransomware cyber.threats sys:is_a
set.add name="ontology.cybersecurity" id="cyber:ransomware"

def "cyber:risk_management" "Cyber risk management."
ln cyber:risk_management cyber.grc sys:is_a
set.add name="ontology.cybersecurity" id="cyber:risk_management"

def "cyber:sast" "Static Application Security Testing."
ln cyber:sast cyber.application_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:sast"

def "cyber:segmentation" "Network segmentation."
ln cyber:segmentation cyber.network_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:segmentation"

def "cyber:siem" "Security Information and Event Management."
ln cyber:siem cyber.defense sys:is_a
ln cyber:siem cyber:soc @supports
set.add name="ontology.cybersecurity" id="cyber:siem"

def "cyber:soar" "Security Orchestration, Automation, and Response."
ln cyber:soar cyber.defense sys:is_a
set.add name="ontology.cybersecurity" id="cyber:soar"

def "cyber:soc" "Security Operations Center."
ln cyber:soc cyber.incident_response sys:is_a
set.add name="ontology.cybersecurity" id="cyber:soc"

def "cyber:soc2" "SOC2 compliance framework."
ln cyber:soc2 cyber.grc sys:is_a
set.add name="ontology.cybersecurity" id="cyber:soc2"

def "cyber:threat_intel" "Threat intelligence."
ln cyber:threat_intel cyber.incident_response sys:is_a
ln cyber:threat_intel cyber:apt @informs
set.add name="ontology.cybersecurity" id="cyber:threat_intel"

def "cyber:vpn" "Virtual Private Network."
ln cyber:vpn cyber.network_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:vpn"

def "cyber:waf" "Web Application Firewall."
ln cyber:waf cyber.network_security sys:is_a
set.add name="ontology.cybersecurity" id="cyber:waf"

def "cyber:zero_trust" "Zero Trust security model."
ln cyber:zero_trust cyber.network_security sys:is_a
ln cyber:zero_trust cyber:iam @requires
set.add name="ontology.cybersecurity" id="cyber:zero_trust"
