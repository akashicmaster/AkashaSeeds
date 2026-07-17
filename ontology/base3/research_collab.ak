# Akasha ontology — research collaboration + open science.
# The co-authorship network is a symmetric typed-link graph — the twin of the
# citation network (cite:*). Open science practices tie into rdm:*/pub:*.
# Base pack.

def "collab" "Research collaboration."
# ── co-authorship network (共著ネットワーク) — symmetric typed-link graph ──
def "collab:coauthor_of" "A co-authored a work with B (symmetric edge)."
ln collab:coauthor_of collab:coauthor_of sys:synonym   # symmetric
ln collab:coauthor_of pub:role:coauthor thesaurus:related
ln collab:coauthor_of social:colleague_of thesaurus:related
def "collab:collaborator_of" "Works together on research (symmetric)."
ln collab:collaborator_of collab:collaborator_of sys:synonym
def "collab:coauthorship_network" "The graph of who co-authors with whom."
ln collab:coauthorship_network sys:network thesaurus:related
ln collab:coauthorship_network collab:coauthor_of thesaurus:related
ln collab:coauthorship_network cite:citation_network thesaurus:related

def "collab:collaboration" "Collaboration — working together on research."
ln collab:collaboration collab thesaurus:related
def "collab:research_team" "Research team — a team on a project."
ln collab:research_team collab thesaurus:related
def "collab:research_group" "Research group (研究グループ) — a standing research group."
ln collab:research_group collab thesaurus:related
def "collab:consortium" "Consortium (コンソーシアム) — a multi-party research alliance."
ln collab:consortium collab thesaurus:related
def "collab:interdisciplinary" "Interdisciplinary (学際) — across disciplines."
ln collab:interdisciplinary collab thesaurus:related
def "collab:cross_institutional" "Cross institutional — across institutions."
ln collab:cross_institutional collab thesaurus:related
def "collab:international_collaboration" "International collaboration (国際共同研究) — across countries."
ln collab:international_collaboration collab thesaurus:related
def "collab:co_pi" "Co pi — a co-principal-investigator."
ln collab:co_pi collab thesaurus:related
def "collab:research_network" "Research network — a network of collaborators."
ln collab:research_network collab thesaurus:related
ln collab:research_team work:team thesaurus:related
ln collab:co_pi acad:principal_investigator thesaurus:related

# ── open science (オープンサイエンス) ──
def "os" "Open science — transparent, shareable research."
def "os:open_access" "Open access (オープンアクセス) — free access to publications."
ln os:open_access os thesaurus:related
def "os:open_data" "Open data — free reuse of data."
ln os:open_data os thesaurus:related
def "os:open_source" "Open source — open research code."
ln os:open_source os thesaurus:related
def "os:preprint" "Preprint — early open sharing of a paper."
ln os:preprint os thesaurus:related
def "os:open_peer_review" "Open peer review (オープン査読) — transparent review."
ln os:open_peer_review os thesaurus:related
def "os:reproducibility" "Reproducibility — repeatable results."
ln os:reproducibility os thesaurus:related
def "os:replication" "Replication (追試) — an independent repeat study."
ln os:replication os thesaurus:related
def "os:preregistration" "Preregistration (事前登録) — registering a study before data."
ln os:preregistration os thesaurus:related
def "os:registered_report" "Registered report (登録報告) — pre-accepted on method."
ln os:registered_report os thesaurus:related
def "os:citizen_science" "Citizen science (市民科学) — public participation in research."
ln os:citizen_science os thesaurus:related
def "os:research_integrity" "Research integrity (研究公正) — honest research conduct."
ln os:research_integrity os thesaurus:related
def "os:transparency" "Transparency — openness of process."
ln os:transparency os thesaurus:related
def "os:orcid" "Orcid (研究者ID(ORCID)) — a persistent researcher identifier."
ln os:orcid os thesaurus:related
def "os:institutional_repository" "Institutional repository (機関リポジトリ) — an institution's open store."
ln os:institutional_repository os thesaurus:related
def "os:apc" "Apc — article processing charge."
ln os:apc os thesaurus:related
def "os:fair_data" "Fair data — FAIR-principled data."
ln os:fair_data os thesaurus:related
ln os:open_access pub:flow:open_access thesaurus:related
ln os:open_data rdm:open_data thesaurus:related
ln os:preprint pub:preprint thesaurus:related
ln os:reproducibility research:reproducibility thesaurus:related
ln os:fair_data rdm:fair thesaurus:related
ln os:institutional_repository rdm:data_repository thesaurus:related
def "os:oa:gold" "Gold OA — published open in the journal."
def "os:oa:green" "Green OA — self-archived in a repository."
def "os:oa:diamond" "Diamond OA — open with no author fee."
ln os:oa:gold os:open_access sys:part_of
ln os:oa:green os:open_access sys:part_of
ln os:oa:diamond os:open_access sys:part_of
