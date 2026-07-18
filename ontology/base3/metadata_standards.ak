# Akasha ontology — metadata standards + digital archives.
# Metadata is Akasha-native (every atom carries meta); Dublin Core especially
# maps onto the atom model. Standards + digital-preservation practice, bridged
# to glam (lib/mus cataloging) and the thesaurus. Base pack.

# ── metadata categories ──
def "meta:descriptive" "Descriptive (記述メタデータ) — describes content for discovery metadata."
ln meta:descriptive meta:citation thesaurus:related
def "meta:structural" "Structural — how parts relate metadata."
ln meta:structural meta:citation thesaurus:related
def "meta:administrative" "Administrative — management/rights info metadata."
ln meta:administrative meta:citation thesaurus:related
def "meta:preservation" "Preservation (保存メタデータ) — info for long-term keeping metadata."
ln meta:preservation meta:citation thesaurus:related
def "meta:technical" "Technical — format/technical detail metadata."
ln meta:technical meta:citation thesaurus:related

# ── metadata standards ──
def "metastd" "A metadata standard."
def "metastd:dublin_core" "DUBLIN_CORE — a 15-element cross-domain standard."
ln metastd:dublin_core metastd thesaurus:related
def "metastd:marc" "MARC — library MARC records."
ln metastd:marc metastd thesaurus:related
def "metastd:mods" "MODS — a richer bibliographic schema."
ln metastd:mods metastd thesaurus:related
def "metastd:mets" "METS — a packaging/structural standard."
ln metastd:mets metastd thesaurus:related
def "metastd:ead" "EAD — encoded archival description."
ln metastd:ead metastd thesaurus:related
def "metastd:premis" "PREMIS — preservation metadata."
ln metastd:premis metastd thesaurus:related
def "metastd:schema_org" "SCHEMA_ORG — web structured-data vocabulary."
ln metastd:schema_org metastd thesaurus:related
def "metastd:rdf" "RDF — the Resource Description Framework."
ln metastd:rdf metastd thesaurus:related
def "metastd:oai_pmh" "OAI_PMH — a metadata harvesting protocol."
ln metastd:oai_pmh metastd thesaurus:related
def "metastd:iiif" "IIIF — image interoperability framework."
ln metastd:iiif metastd thesaurus:related
def "metastd:cidoc_crm" "CIDOC_CRM — a museum/cultural ontology."
ln metastd:cidoc_crm metastd thesaurus:related
def "metastd:vra_core" "VRA_CORE — visual-resources metadata."
ln metastd:vra_core metastd thesaurus:related
ln metastd:marc lib:bibliographic_record thesaurus:related
ln metastd:cidoc_crm mus:cataloging thesaurus:related
ln metastd:rdf sys:network thesaurus:related

# ── Dublin Core 15 elements — maps onto Akasha atom meta ──
def "dc:title" "Dublin Core: title."
ln dc:title metastd:dublin_core sys:part_of
def "dc:creator" "Dublin Core: creator."
ln dc:creator metastd:dublin_core sys:part_of
def "dc:subject" "Dublin Core: subject."
ln dc:subject metastd:dublin_core sys:part_of
def "dc:description" "Dublin Core: description."
ln dc:description metastd:dublin_core sys:part_of
def "dc:publisher" "Dublin Core: publisher."
ln dc:publisher metastd:dublin_core sys:part_of
def "dc:contributor" "Dublin Core: contributor."
ln dc:contributor metastd:dublin_core sys:part_of
def "dc:date" "Dublin Core: date."
ln dc:date metastd:dublin_core sys:part_of
def "dc:type" "Dublin Core: type."
ln dc:type metastd:dublin_core sys:part_of
def "dc:format" "Dublin Core: format."
ln dc:format metastd:dublin_core sys:part_of
def "dc:identifier" "Dublin Core: identifier."
ln dc:identifier metastd:dublin_core sys:part_of
def "dc:source" "Dublin Core: source."
ln dc:source metastd:dublin_core sys:part_of
def "dc:language" "Dublin Core: language."
ln dc:language metastd:dublin_core sys:part_of
def "dc:relation" "Dublin Core: relation."
ln dc:relation metastd:dublin_core sys:part_of
def "dc:coverage" "Dublin Core: coverage."
ln dc:coverage metastd:dublin_core sys:part_of
def "dc:rights" "Dublin Core: rights."
ln dc:rights metastd:dublin_core sys:part_of
ln dc:subject thesaurus:related thesaurus:related
ln dc:relation cite:cites thesaurus:related
ln dc:identifier rdm:persistent_identifier thesaurus:related

# ── digital archives & preservation ──
def "digarch:digital_archive" "Digital archive (デジタルアーカイブ) — a curated store of digital objects."
ln digarch:digital_archive metastd thesaurus:related
def "digarch:digital_repository" "Digital repository — a managed digital store."
ln digarch:digital_repository metastd thesaurus:related
def "digarch:digitization" "Digitization (電子化) — converting analog to digital."
ln digarch:digitization metastd thesaurus:related
def "digarch:born_digital" "Born digital (ボーンデジタル) — created digitally from the start."
ln digarch:born_digital metastd thesaurus:related
def "digarch:digital_preservation" "Digital preservation (デジタル保存) — keeping digital content usable over time."
ln digarch:digital_preservation metastd thesaurus:related
def "digarch:format_migration" "Format migration — moving to current formats."
ln digarch:format_migration metastd thesaurus:related
def "digarch:emulation" "Emulation — running old environments."
ln digarch:emulation metastd thesaurus:related
def "digarch:fixity" "Fixity — proof content is unchanged."
ln digarch:fixity metastd thesaurus:related
def "digarch:checksum" "Checksum (チェックサム) — a hash verifying integrity."
ln digarch:checksum metastd thesaurus:related
def "digarch:oais" "Oais — the Open Archival Information System model."
ln digarch:oais metastd thesaurus:related
def "digarch:institutional_repository" "Institutional repository (機関リポジトリ) — an institution's digital archive."
ln digarch:institutional_repository metastd thesaurus:related
def "digarch:digital_object" "Digital object — a managed digital item."
ln digarch:digital_object metastd thesaurus:related
def "digarch:controlled_vocabulary" "Controlled vocabulary (統制語彙) — a governed term list."
ln digarch:controlled_vocabulary metastd thesaurus:related
def "digarch:authority_file" "Authority file — controlled names."
ln digarch:authority_file metastd thesaurus:related
def "digarch:crosswalk" "Crosswalk (クロスウォーク) — mapping between metadata standards."
ln digarch:crosswalk metastd thesaurus:related
def "digarch:metadata_harvesting" "Metadata harvesting — gathering metadata across repositories."
ln digarch:metadata_harvesting metastd thesaurus:related
def "digarch:sip" "Submission Information Package (OAIS)."
def "digarch:aip" "Archival Information Package (OAIS)."
def "digarch:dip" "Dissemination Information Package (OAIS)."
ln digarch:sip digarch:oais sys:part_of
ln digarch:aip digarch:oais sys:part_of
ln digarch:dip digarch:oais sys:part_of
ln digarch:digital_preservation rdm:data_archiving thesaurus:related
ln digarch:digital_object rdm:dataset thesaurus:related
ln digarch:controlled_vocabulary thesaurus:related thesaurus:related
ln digarch:authority_file lib:authority_control thesaurus:related
ln digarch:digital_archive place:archive thesaurus:related
ln digarch:crosswalk metastd:dublin_core thesaurus:related
