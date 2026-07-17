# Akasha ontology — GLAM practice: librarian (司書) & curator (学芸員).
# Professional practice of libraries and museums — close to Akasha's own
# thesaurus / curation / librarian roles. Adds place:museum. Base pack.

# ── occupations ──
def "occupation:librarian" "Librarian."
ln occupation:librarian occupation_sector:education occupation:sector
ln occupation:librarian librarian thesaurus:related
def "occupation:curator" "Curator."
ln occupation:curator occupation_sector:arts_media occupation:sector
ln occupation:curator curator thesaurus:related
def "occupation:archivist" "Archivist."
ln occupation:archivist occupation_sector:arts_media occupation:sector
ln occupation:archivist archivist thesaurus:related
def "occupation:conservator" "Conservator."
ln occupation:conservator occupation_sector:arts_media occupation:sector
ln occupation:conservator conservator thesaurus:related
def "occupation:museum_registrar" "Museum registrar."
ln occupation:museum_registrar occupation_sector:arts_media occupation:sector
ln occupation:museum_registrar museum thesaurus:related

def "place:museum" "Museum — a place that collects and exhibits."
def "place:gallery" "Gallery — an exhibition space."
def "place:archive" "Archive — a repository of records."
ln place:museum place_type:education civic:function
ln place:gallery place_type:education civic:function
ln place:archive place_type:education civic:function
ln occupation:librarian place:library civic:role_at
ln occupation:curator place:museum civic:role_at
ln occupation:archivist place:archive civic:role_at

# ── librarian practice (司書実務) ──
def "lib:cataloging" "Cataloging (目録) — describing an item for the catalog."
ln lib:cataloging place:library civic:role_at
ln lib:cataloging occupation:librarian thesaurus:related
def "lib:classification" "Classification (分類) — assigning a class (NDC/Dewey)."
ln lib:classification place:library civic:role_at
ln lib:classification occupation:librarian thesaurus:related
def "lib:call_number" "Call number (請求記号) — an item's shelf address."
ln lib:call_number place:library civic:role_at
ln lib:call_number occupation:librarian thesaurus:related
def "lib:accession" "Accession (登録受入) — adding an item to the collection."
ln lib:accession place:library civic:role_at
ln lib:accession occupation:librarian thesaurus:related
def "lib:acquisition" "Acquisition (受入) — obtaining new items."
ln lib:acquisition place:library civic:role_at
ln lib:acquisition occupation:librarian thesaurus:related
def "lib:circulation" "Circulation (貸出業務) — lending, return and renewal."
ln lib:circulation place:library civic:role_at
ln lib:circulation occupation:librarian thesaurus:related
def "lib:lending" "Lending — issuing an item to a borrower."
ln lib:lending place:library civic:role_at
ln lib:lending occupation:librarian thesaurus:related
def "lib:overdue" "Overdue — a late return."
ln lib:overdue place:library civic:role_at
ln lib:overdue occupation:librarian thesaurus:related
def "lib:reservation" "Reservation — holding an item for a patron."
ln lib:reservation place:library civic:role_at
ln lib:reservation occupation:librarian thesaurus:related
def "lib:weeding" "Weeding (除籍) — withdrawing worn/unused items."
ln lib:weeding place:library civic:role_at
ln lib:weeding occupation:librarian thesaurus:related
def "lib:shelving" "Shelving — reshelving returned items."
ln lib:shelving place:library civic:role_at
ln lib:shelving occupation:librarian thesaurus:related
def "lib:reference_service" "Reference service (レファレンス) — helping patrons find information."
ln lib:reference_service place:library civic:role_at
ln lib:reference_service occupation:librarian thesaurus:related
def "lib:opac" "Opac (蔵書検索(OPAC)) — online public access catalog."
ln lib:opac place:library civic:role_at
ln lib:opac occupation:librarian thesaurus:related
def "lib:bibliographic_record" "Bibliographic record — a catalog record."
ln lib:bibliographic_record place:library civic:role_at
ln lib:bibliographic_record occupation:librarian thesaurus:related
def "lib:authority_control" "Authority control (典拠管理) — controlling names/terms."
ln lib:authority_control place:library civic:role_at
ln lib:authority_control occupation:librarian thesaurus:related
def "lib:subject_heading" "Subject heading (件名標目) — a controlled subject term."
ln lib:subject_heading place:library civic:role_at
ln lib:subject_heading occupation:librarian thesaurus:related
def "lib:interlibrary_loan" "Interlibrary loan (相互貸借) — borrowing from another library."
ln lib:interlibrary_loan place:library civic:role_at
ln lib:interlibrary_loan occupation:librarian thesaurus:related
def "lib:collection_development" "Collection development (蔵書構築) — shaping the collection."
ln lib:collection_development place:library civic:role_at
ln lib:collection_development occupation:librarian thesaurus:related
def "lib:indexing" "Indexing — making content findable."
ln lib:indexing place:library civic:role_at
ln lib:indexing occupation:librarian thesaurus:related
def "lib:reading_room" "Reading room (閲覧室) — a space for reading."
ln lib:reading_room place:library civic:role_at
ln lib:reading_room occupation:librarian thesaurus:related
ln lib:subject_heading thesaurus:related thesaurus:related
ln lib:authority_control thesaurus:related thesaurus:related
ln lib:classification thesaurus:related thesaurus:related
ln lib:circulation lib:lending sys:part_of
ln lib:lending verb:act:lend thesaurus:related

# ── curator practice (学芸員実務) ──
def "mus:exhibition" "Exhibition (展覧会) — planning and mounting a show."
ln mus:exhibition place:museum civic:role_at
ln mus:exhibition occupation:curator thesaurus:related
def "mus:collection_management" "Collection management — caring for the collection."
ln mus:collection_management place:museum civic:role_at
ln mus:collection_management occupation:curator thesaurus:related
def "mus:accession" "Accession (登録受入) — registering a new object."
ln mus:accession place:museum civic:role_at
ln mus:accession occupation:curator thesaurus:related
def "mus:deaccession" "Deaccession (除籍) — removing an object from the collection."
ln mus:deaccession place:museum civic:role_at
ln mus:deaccession occupation:curator thesaurus:related
def "mus:conservation" "Conservation (保存修復) — preventive care of objects."
ln mus:conservation place:museum civic:role_at
ln mus:conservation occupation:curator thesaurus:related
def "mus:restoration" "Restoration (修復) — repairing an object."
ln mus:restoration place:museum civic:role_at
ln mus:restoration occupation:curator thesaurus:related
def "mus:cataloging" "Cataloging (目録) — documenting an object."
ln mus:cataloging place:museum civic:role_at
ln mus:cataloging occupation:curator thesaurus:related
def "mus:provenance" "Provenance (来歴) — an object's ownership history."
ln mus:provenance place:museum civic:role_at
ln mus:provenance occupation:curator thesaurus:related
def "mus:loan" "Loan (貸借) — lending/borrowing objects between institutions."
ln mus:loan place:museum civic:role_at
ln mus:loan occupation:curator thesaurus:related
def "mus:acquisition" "Acquisition (受入) — acquiring objects."
ln mus:acquisition place:museum civic:role_at
ln mus:acquisition occupation:curator thesaurus:related
def "mus:appraisal" "Appraisal (評価鑑定) — valuing/authenticating objects."
ln mus:appraisal place:museum civic:role_at
ln mus:appraisal occupation:curator thesaurus:related
def "mus:condition_report" "Condition report (状態報告) — recording an object's state."
ln mus:condition_report place:museum civic:role_at
ln mus:condition_report occupation:curator thesaurus:related
def "mus:display" "Display — mounting objects for view."
ln mus:display place:museum civic:role_at
ln mus:display occupation:curator thesaurus:related
def "mus:storage" "Storage — safe keeping of objects."
ln mus:storage place:museum civic:role_at
ln mus:storage occupation:curator thesaurus:related
def "mus:docent" "Docent (解説員) — a museum guide."
ln mus:docent place:museum civic:role_at
ln mus:docent occupation:curator thesaurus:related
def "mus:artifact" "Artifact (収蔵品) — a collection object."
ln mus:artifact place:museum civic:role_at
ln mus:artifact occupation:curator thesaurus:related
def "mus:label" "Label — an object's explanatory caption."
ln mus:label place:museum civic:role_at
ln mus:label occupation:curator thesaurus:related
def "mus:guided_tour" "Guided tour — a led tour of the museum."
ln mus:guided_tour place:museum civic:role_at
ln mus:guided_tour occupation:curator thesaurus:related
ln mus:provenance rdm:provenance thesaurus:related
ln mus:loan verb:act:lend thesaurus:related
ln mus:cataloging lib:cataloging thesaurus:related
ln mus:accession lib:accession thesaurus:related
