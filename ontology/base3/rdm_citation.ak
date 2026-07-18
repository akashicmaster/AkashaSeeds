# Akasha ontology — research data management (RDM) + citation networks.
# Built on academia.ak (research:*, pub:*). The citation network is a directed
# typed-link graph — Akasha-native: cite:cites / cite:cited_by ARE the edges.
# Base pack.

def "rdm" "Research data management."
# ── data management ──
def "rdm:dataset" "Dataset — a body of research data."
ln rdm:dataset rdm thesaurus:related
def "rdm:raw_data" "Raw data — unprocessed data."
ln rdm:raw_data rdm thesaurus:related
def "rdm:processed_data" "Processed data — cleaned/derived data."
ln rdm:processed_data rdm thesaurus:related
def "rdm:metadata" "Metadata — data describing data."
ln rdm:metadata rdm thesaurus:related
def "rdm:data_repository" "Data repository (データリポジトリ) — a store for datasets."
ln rdm:data_repository rdm thesaurus:related
def "rdm:data_management_plan" "Data management plan (データ管理計画(DMP)) — a plan for handling data."
ln rdm:data_management_plan rdm thesaurus:related
def "rdm:data_curation" "Data curation (データキュレーション) — maintaining data over time."
ln rdm:data_curation rdm thesaurus:related
def "rdm:persistent_identifier" "Persistent identifier (永続識別子) — a stable id (DOI/handle)."
ln rdm:persistent_identifier rdm thesaurus:related
def "rdm:provenance" "Provenance (来歴) — the origin & history of data."
ln rdm:provenance rdm thesaurus:related
def "rdm:versioning" "Versioning (版管理) — tracking data versions."
ln rdm:versioning rdm thesaurus:related
def "rdm:data_license" "Data license — terms for reuse."
ln rdm:data_license rdm thesaurus:related
def "rdm:data_archiving" "Data archiving — long-term preservation."
ln rdm:data_archiving rdm thesaurus:related
def "rdm:data_sharing" "Data sharing — making data available."
ln rdm:data_sharing rdm thesaurus:related
def "rdm:open_data" "Open data (オープンデータ) — freely reusable data."
ln rdm:open_data rdm thesaurus:related
def "rdm:backup" "Backup — a safeguard copy."
ln rdm:backup rdm thesaurus:related
def "rdm:codebook" "Codebook — documentation of variables."
ln rdm:codebook rdm thesaurus:related
def "rdm:data_lifecycle" "Data lifecycle — data from creation to disposal."
ln rdm:data_lifecycle rdm thesaurus:related
ln rdm:dataset research:dataset thesaurus:related
ln rdm:data_management_plan academia thesaurus:related

# ── FAIR principles ──
def "rdm:fair" "FAIR — Findable, Accessible, Interoperable, Reusable data."
def "rdm:fair:findable" "Findable data."
ln rdm:fair:findable rdm:fair sys:part_of
def "rdm:fair:accessible" "Accessible data."
ln rdm:fair:accessible rdm:fair sys:part_of
def "rdm:fair:interoperable" "Interoperable data."
ln rdm:fair:interoperable rdm:fair sys:part_of
def "rdm:fair:reusable" "Reusable data."
ln rdm:fair:reusable rdm:fair sys:part_of
ln rdm:fair rdm thesaurus:related
ln rdm:provenance rdm:data_curation thesaurus:related

# ── citation network — directed typed-link graph ──
def "cite" "Scholarly citation and its network."
def "cite:cites" "A cites B — a work references another (directed edge)."
def "cite:cited_by" "A is cited by B — the inverse edge."
ln cite:cites cite:cited_by sys:antonym
ln cite:cited_by cite:cites sys:antonym
ln cite:cites cite thesaurus:related
ln cite:cites pub:paper thesaurus:related

def "cite:reference" "Reference (参考文献) — a cited work."
ln cite:reference cite thesaurus:related
def "cite:bibliography" "Bibliography — the list of references."
ln cite:bibliography cite thesaurus:related
def "cite:co_citation" "Co citation (共引用) — two works cited together by a third."
ln cite:co_citation cite thesaurus:related
def "cite:bibliographic_coupling" "Bibliographic coupling (書誌結合) — two works citing the same source."
ln cite:bibliographic_coupling cite thesaurus:related
def "cite:citation_network" "Citation network (引用ネットワーク) — the graph of citations."
ln cite:citation_network cite thesaurus:related
def "cite:citation_index" "Citation index (引用索引) — an index of who-cites-whom."
ln cite:citation_index cite thesaurus:related
def "cite:self_citation" "Self citation (自己引用) — citing one's own work."
ln cite:self_citation cite thesaurus:related
def "cite:citation_count" "Citation count — number of citations received."
ln cite:citation_count cite thesaurus:related
def "cite:citation_analysis" "Citation analysis — studying citation patterns."
ln cite:citation_analysis cite thesaurus:related
def "cite:reference_manager" "Reference manager (文献管理ツール) — a tool managing references (Zotero/BibTeX)."
ln cite:reference_manager cite thesaurus:related
ln cite:citation_count pub:metric:citation_count thesaurus:related
ln cite:reference pub:part:reference thesaurus:related
ln cite:citation_network sys:network thesaurus:related
ln cite:citation_network cite:cites thesaurus:related
