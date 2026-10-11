# architecture_styles.ak
# Architectural styles and traditions — ancient to 20th century
# Sources: Watkin, Ching, Frampton, Fletcher — Public domain terminology
#

# ── Namespace anchors ──────────────────────────────────────────────────────────

def "arch:style" "Root node for architectural styles and traditions worldwide."
def "arch:region:western" "Western architecture from ancient Mediterranean through 20th-century Europe and Americas."
def "arch:region:islamic" "Islamic architecture — mosques, madrasas, palaces, and domestic traditions."
def "arch:region:east_asian" "East Asian architecture — Chinese, Japanese, Korean traditions."
def "arch:region:south_asian" "South Asian / Indian architecture — Hindu, Buddhist, Islamic, and colonial traditions."
def "arch:region:vernacular" "Vernacular and regional building traditions using local materials and techniques."

# ── Ancient ───────────────────────────────────────────────────────────────────

def "arch:style:egyptian_temple" "Pylon gateway + hypostyle hall + sanctuary; axial processional; massive stone columns; Karnak, Abu Simbel; post-and-lintel; carved hieroglyphic relief."
ln arch:style:egyptian_temple arch:style sys:part_of
ln arch:style:egyptian_temple arch:region:western arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:egyptian_temple"

def "arch:style:pyramid" "Egyptian funerary monument; stepped (Saqqara, c.2650 BCE) → true pyramid (Giza, c.2560 BCE); corbelled chambers; astronomical orientation; mortuary complex."
ln arch:style:pyramid arch:style sys:part_of
ln arch:style:pyramid arch:region:western arch:influenced_by
ln arch:style:pyramid arch:style:egyptian_temple arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:pyramid"

def "arch:style:ziggurat" "Mesopotamian stepped temple-tower; Ur-Nammu's ziggurat (c.2100 BCE); mud brick; solid mass with no interior spaces; Babylon's Etemenanki possibly origin of Tower of Babel."
ln arch:style:ziggurat arch:style sys:part_of
ln arch:style:ziggurat arch:region:western arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:ziggurat"

def "arch:style:greek_doric" "Earliest and heaviest Greek order; no base; capital with plain echinus and abacus; triglyphs and metopes in frieze; Parthenon (447–432 BCE); austere Doric ideal."
ln arch:style:greek_doric arch:style sys:part_of
ln arch:style:greek_doric arch:region:western arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:greek_doric"

def "arch:style:greek_ionic" "Scroll volute capitals; base on column; more slender than Doric; continuous sculptural frieze; Erechtheion (421–406 BCE); spread through Asia Minor."
ln arch:style:greek_ionic arch:style sys:part_of
ln arch:style:greek_ionic arch:region:western arch:influenced_by
ln arch:style:greek_ionic arch:style:greek_doric arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:greek_ionic"

def "arch:style:greek_corinthian" "Acanthus leaf capital; most ornate Greek order; Hellenistic and Roman preferred; Tholos of Epidaurus; Choragic Monument of Lysicrates."
ln arch:style:greek_corinthian arch:style sys:part_of
ln arch:style:greek_corinthian arch:region:western arch:influenced_by
ln arch:style:greek_corinthian arch:style:greek_ionic arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:greek_corinthian"

def "arch:style:roman_arch" "Semicircular load-bearing arch; concrete (opus caementicium); aqueducts, triumphal arches, amphitheatres; Pont du Gard; structural revolution over Greek post-and-lintel."
ln arch:style:roman_arch arch:style sys:part_of
ln arch:style:roman_arch arch:region:western arch:influenced_by
ln arch:style:roman_arch arch:style:greek_doric arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:roman_arch"

def "arch:style:roman_basilica" "Large rectangular public hall; apse at one or both ends; clerestory lighting; colonnaded nave and aisles; prototype for Christian church; Basilica Ulpia."
ln arch:style:roman_basilica arch:style sys:part_of
ln arch:style:roman_basilica arch:region:western arch:influenced_by
ln arch:style:roman_basilica arch:style:roman_arch arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:roman_basilica"

def "arch:style:roman_dome" "Concrete shell dome with oculus; Pantheon (c.126 CE, 43.3m diameter); pendentive problem solved later by Byzantines; largest unreinforced concrete dome for 1,300 years."
ln arch:style:roman_dome arch:style sys:part_of
ln arch:style:roman_dome arch:region:western arch:influenced_by
ln arch:style:roman_dome arch:style:roman_arch arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:roman_dome"

# ── Medieval ──────────────────────────────────────────────────────────────────

def "arch:style:byzantine" "Centrally planned domed church; pendentive transitions square bay to round dome; Hagia Sophia (537 CE); gold mosaic interiors; Greek cross plan; Eastern Orthodox spread."
ln arch:style:byzantine arch:style sys:part_of
ln arch:style:byzantine arch:region:western arch:influenced_by
ln arch:style:byzantine arch:style:roman_dome arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:byzantine"

def "arch:style:romanesque" "c.1000–1200; thick walls; round arch; barrel and groin vault; small windows; pilgrimage church plan; Santiago de Compostela; Speyer Cathedral; monumental solid mass."
ln arch:style:romanesque arch:style sys:part_of
ln arch:style:romanesque arch:region:western arch:influenced_by
ln arch:style:romanesque arch:style:roman_arch arch:derived_from
ln arch:style:romanesque arch:style:byzantine arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:romanesque"

def "arch:style:gothic" "c.1140–1500; pointed arch; ribbed vault; flying buttress externalises thrust; large stained glass windows; verticality; Notre-Dame de Paris; Chartres; Cologne Cathedral."
ln arch:style:gothic arch:style sys:part_of
ln arch:style:gothic arch:region:western arch:influenced_by
ln arch:style:gothic arch:style:romanesque arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:gothic"

def "arch:style:mudejar" "Iberian hybrid (12th–16th c.); Islamic craftsmen in Christian kingdoms; brick, stucco, artesonado geometric woodwork; Seville Alcazar; Toledo synagogues."
ln arch:style:mudejar arch:style sys:part_of
ln arch:style:mudejar arch:region:western arch:influenced_by
ln arch:style:mudejar arch:region:islamic arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:mudejar"

# ── Islamic ───────────────────────────────────────────────────────────────────

def "arch:style:hypostyle_mosque" "Multiple bays of columns; horizontal emphasis; Great Mosque of Cordoba (784 CE, expanded); congregational prayer space; repetitive modular structure."
ln arch:style:hypostyle_mosque arch:style sys:part_of
ln arch:style:hypostyle_mosque arch:region:islamic arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:hypostyle_mosque"

def "arch:style:four_iwan_mosque" "Seljuk and Persian tradition; four iwans (vaulted halls) facing central courtyard; Masjid-i Shah, Isfahan; blue tile facades; adopted for madrasas."
ln arch:style:four_iwan_mosque arch:style sys:part_of
ln arch:style:four_iwan_mosque arch:region:islamic arch:influenced_by
ln arch:style:four_iwan_mosque arch:style:hypostyle_mosque arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:four_iwan_mosque"

def "arch:style:ottoman_mosque" "Sinan's synthesis (16th c.); single great dome + cascading half-domes; Süleymaniye (1557), Selimiye (1575); pencil minarets; centralised unobstructed space."
ln arch:style:ottoman_mosque arch:style sys:part_of
ln arch:style:ottoman_mosque arch:region:islamic arch:influenced_by
ln arch:style:ottoman_mosque arch:style:byzantine arch:influenced_by
ln arch:style:ottoman_mosque arch:style:four_iwan_mosque arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:ottoman_mosque"

def "arch:style:mughal_architecture" "Timurid + Indian fusion (16th–18th c.); white marble inlay (pietra dura); charbagh (4-part garden); Taj Mahal (1632–53); Fatehpur Sikri."
ln arch:style:mughal_architecture arch:style sys:part_of
ln arch:style:mughal_architecture arch:region:islamic arch:influenced_by
ln arch:style:mughal_architecture arch:region:south_asian arch:influenced_by
ln arch:style:mughal_architecture arch:style:four_iwan_mosque arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:mughal_architecture"

def "arch:style:moorish" "Nasrid Granada (13th–15th c.); Alhambra; muqarnas stalactite vaults; zellige tilework; artesonado ceilings; stucco arabesque; geometric poetry in space."
ln arch:style:moorish arch:style sys:part_of
ln arch:style:moorish arch:region:islamic arch:influenced_by
ln arch:style:moorish arch:style:hypostyle_mosque arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:moorish"

def "arch:style:mamluk_architecture" "Cairo (13th–16th c.); striped ablaq stonework; stalactite portals; Sultan Hassan complex (1356–63); fusion of Syrian and Egyptian traditions."
ln arch:style:mamluk_architecture arch:style sys:part_of
ln arch:style:mamluk_architecture arch:region:islamic arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:mamluk_architecture"

# ── East Asian ────────────────────────────────────────────────────────────────

def "arch:style:chinese_palace" "Axial symmetry; walled compound; dougong bracket system; glazed tile roof with upturned eaves; Forbidden City (1406–20); red walls, yellow roofs; hall-on-platform."
ln arch:style:chinese_palace arch:style sys:part_of
ln arch:style:chinese_palace arch:region:east_asian arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:chinese_palace"

def "arch:style:chinese_pagoda" "Buddhist tower derived from Indian stupa; multi-storey; timber or brick; each storey with upturned eaves; Giant Wild Goose Pagoda, Xi'an (652 CE)."
ln arch:style:chinese_pagoda arch:style sys:part_of
ln arch:style:chinese_pagoda arch:region:east_asian arch:influenced_by
ln arch:style:chinese_pagoda arch:style:chinese_palace arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:chinese_pagoda"

def "arch:style:japanese_shinto_shrine" "Unpainted cedar or hinoki cypress; torii gate; honden (inner sanctuary); raised floor; Ise Jingu rebuilt every 20 years; purity through impermanence."
ln arch:style:japanese_shinto_shrine arch:style sys:part_of
ln arch:style:japanese_shinto_shrine arch:region:east_asian arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:japanese_shinto_shrine"

def "arch:style:japanese_temple" "Buddhist; gate (sanmon), main hall (hondo), pagoda; Horyuji (607 CE, oldest surviving wooden structure); graceful bracketing systems; garden setting."
ln arch:style:japanese_temple arch:style sys:part_of
ln arch:style:japanese_temple arch:region:east_asian arch:influenced_by
ln arch:style:japanese_temple arch:style:chinese_palace arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:japanese_temple"

def "arch:style:japanese_sukiya" "Tea house and residential aesthetic (16th c. onward); wabi-sabi; asymmetry; natural materials; roji stepping stone path; tokonoma alcove; Katsura Imperial Villa."
ln arch:style:japanese_sukiya arch:style sys:part_of
ln arch:style:japanese_sukiya arch:region:east_asian arch:influenced_by
ln arch:style:japanese_sukiya arch:style:japanese_shinto_shrine arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:japanese_sukiya"

def "arch:style:korean_architecture" "Dancheong painted bracket system; Joseon palace; Gyeongbokgung (1395); stone foundations; curved roofs; Confucian spatial hierarchy and axial planning."
ln arch:style:korean_architecture arch:style sys:part_of
ln arch:style:korean_architecture arch:region:east_asian arch:influenced_by
ln arch:style:korean_architecture arch:style:chinese_palace arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:korean_architecture"

# ── South Asian ───────────────────────────────────────────────────────────────

def "arch:style:nagara" "North Indian temple style (5th–13th c.); curvilinear shikhara tower over garbhagriha (sanctuary); amalaka finial; Khajuraho, Konark Sun Temple."
ln arch:style:nagara arch:style sys:part_of
ln arch:style:nagara arch:region:south_asian arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:nagara"

def "arch:style:dravida" "South Indian temple style (7th c. onward); tiered gopuram gateway towers; vimana tower; axial mandapa halls; Brihadisvara Temple, Thanjavur (1010 CE)."
ln arch:style:dravida arch:style sys:part_of
ln arch:style:dravida arch:region:south_asian arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:dravida"

def "arch:style:vesara" "Hybrid Nagara-Dravida style; Deccan plateau; Chalukya and Hoysala dynasties; star-shaped plan; densely carved exterior; Belur, Halebidu."
ln arch:style:vesara arch:style sys:part_of
ln arch:style:vesara arch:region:south_asian arch:influenced_by
ln arch:style:vesara arch:style:nagara arch:derived_from
ln arch:style:vesara arch:style:dravida arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:vesara"

def "arch:style:indo_saracenic" "British colonial synthesis of Islamic, Rajput, and Gothic elements; Chhatrapati Shivaji Terminus; Victoria Memorial; hybrid imperial style (19th–20th c.)."
ln arch:style:indo_saracenic arch:style sys:part_of
ln arch:style:indo_saracenic arch:region:south_asian arch:influenced_by
ln arch:style:indo_saracenic arch:style:mughal_architecture arch:influenced_by
ln arch:style:indo_saracenic arch:style:gothic arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:indo_saracenic"

# ── Renaissance and after ─────────────────────────────────────────────────────

def "arch:style:renaissance_architecture" "Classical orders revived (15th–17th c.); Brunelleschi's dome (Florence, 1436); Alberti's theoretical treatise; symmetry; Palladio's villas."
ln arch:style:renaissance_architecture arch:style sys:part_of
ln arch:style:renaissance_architecture arch:region:western arch:influenced_by
ln arch:style:renaissance_architecture arch:style:roman_arch arch:derived_from
ln arch:style:renaissance_architecture arch:style:gothic arch:reacts_against
set.add name="ontology.architecture_styles" id="arch:style:renaissance_architecture"

def "arch:style:palladian" "Andrea Palladio (1508–80); I Quattro Libri dell'Architettura; temple front on villa; harmonic proportions; Villa Rotonda; exported to England (Inigo Jones) and America."
ln arch:style:palladian arch:style sys:part_of
ln arch:style:palladian arch:region:western arch:influenced_by
ln arch:style:palladian arch:style:renaissance_architecture arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:palladian"

def "arch:style:baroque_architecture" "c.1600–1750; dramatic curves; theatrical spatial sequences; Bernini (St. Peter's colonnades), Borromini (San Carlo), Wren (St. Paul's)."
ln arch:style:baroque_architecture arch:style sys:part_of
ln arch:style:baroque_architecture arch:region:western arch:influenced_by
ln arch:style:baroque_architecture arch:style:renaissance_architecture arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:baroque_architecture"

def "arch:style:rococo_architecture" "Early 18th c.; playful asymmetry; shell (rocaille) motifs; pastel colour; Bavarian Wieskirche (Zimmermann brothers); French salons; reaction against Baroque heaviness."
ln arch:style:rococo_architecture arch:style sys:part_of
ln arch:style:rococo_architecture arch:region:western arch:influenced_by
ln arch:style:rococo_architecture arch:style:baroque_architecture arch:reacts_against
set.add name="ontology.architecture_styles" id="arch:style:rococo_architecture"

def "arch:style:neoclassical_architecture" "c.1750–1840; Greek and Roman revival; Panthéon (Soufflot), Altes Museum (Schinkel), US Capitol; Enlightenment civic purpose; Beaux-Arts later variant."
ln arch:style:neoclassical_architecture arch:style sys:part_of
ln arch:style:neoclassical_architecture arch:region:western arch:influenced_by
ln arch:style:neoclassical_architecture arch:style:rococo_architecture arch:reacts_against
ln arch:style:neoclassical_architecture arch:style:renaissance_architecture arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:neoclassical_architecture"

def "arch:style:gothic_revival" "19th c.; Pugin, Viollet-le-Duc, Scott; pointed arches on modern buildings; Westminster Palace (Barry and Pugin, 1840); High Victorian muscular Gothic."
ln arch:style:gothic_revival arch:style sys:part_of
ln arch:style:gothic_revival arch:region:western arch:influenced_by
ln arch:style:gothic_revival arch:style:gothic arch:derived_from
ln arch:style:gothic_revival arch:style:neoclassical_architecture arch:reacts_against
set.add name="ontology.architecture_styles" id="arch:style:gothic_revival"

def "arch:style:art_nouveau" "c.1890–1910; organic natural forms; sinuous line; Gaudí (Sagrada Família), Guimard (Paris Metro), Horta (Brussels); Jugendstil in Germany; rejected historicism."
ln arch:style:art_nouveau arch:style sys:part_of
ln arch:style:art_nouveau arch:region:western arch:influenced_by
ln arch:style:art_nouveau arch:style:gothic_revival arch:reacts_against
set.add name="ontology.architecture_styles" id="arch:style:art_nouveau"

def "arch:style:arts_and_crafts" "1880s–1910s; Ruskin and Morris; vernacular materials; handcraft over industry; Voysey, Mackintosh; Red House (Webb for Morris, 1859); reaction against industrialisation."
ln arch:style:arts_and_crafts arch:style sys:part_of
ln arch:style:arts_and_crafts arch:region:western arch:influenced_by
ln arch:style:arts_and_crafts arch:style:gothic_revival arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:arts_and_crafts"

def "arch:style:bauhaus" "Dessau 1919–1933; Gropius; form follows function; industrial materials; flat roof; no ornament; steel and glass; influenced International Style globally."
ln arch:style:bauhaus arch:style sys:part_of
ln arch:style:bauhaus arch:region:western arch:influenced_by
ln arch:style:bauhaus arch:style:arts_and_crafts arch:influenced_by
ln arch:style:bauhaus arch:style:art_nouveau arch:reacts_against
set.add name="ontology.architecture_styles" id="arch:style:bauhaus"

def "arch:style:international_style" "1920s–1970s; Le Corbusier (five points), Mies van der Rohe (less is more); glass curtain wall; pilotis; flat roof; open plan; Seagram Building; modernist orthodoxy."
ln arch:style:international_style arch:style sys:part_of
ln arch:style:international_style arch:region:western arch:influenced_by
ln arch:style:international_style arch:style:bauhaus arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:international_style"

def "arch:style:brutalism" "1950s–1970s; béton brut (raw concrete); Le Corbusier's Unité d'Habitation; Smithsons; Barbican (London); Preston Bus Station; exposed structure; social housing ideal."
ln arch:style:brutalism arch:style sys:part_of
ln arch:style:brutalism arch:region:western arch:influenced_by
ln arch:style:brutalism arch:style:international_style arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:brutalism"

def "arch:style:metabolism" "Japan 1960s; Tange Kenzo, Kurokawa Kisho; modular megastructure; replaceable capsule units; Nakagin Capsule Tower (1972); organic growth model for cities."
ln arch:style:metabolism arch:style sys:part_of
ln arch:style:metabolism arch:region:east_asian arch:influenced_by
ln arch:style:metabolism arch:style:international_style arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:metabolism"

def "arch:style:postmodern_architecture" "1960s–1990s; Venturi, Jencks, Johnson; ornament returns; irony; historical quotation; AT&T Building (Johnson, 1984); Piazza d'Italia (Moore)."
ln arch:style:postmodern_architecture arch:style sys:part_of
ln arch:style:postmodern_architecture arch:region:western arch:influenced_by
ln arch:style:postmodern_architecture arch:style:international_style arch:reacts_against
set.add name="ontology.architecture_styles" id="arch:style:postmodern_architecture"

def "arch:style:deconstructivism" "1980s–present; Gehry, Hadid, Libeskind, Koolhaas; fragmented forms; no right angles; Guggenheim Bilbao (1997); Jewish Museum Berlin; destabilised geometry."
ln arch:style:deconstructivism arch:style sys:part_of
ln arch:style:deconstructivism arch:region:western arch:influenced_by
ln arch:style:deconstructivism arch:style:postmodern_architecture arch:derived_from
set.add name="ontology.architecture_styles" id="arch:style:deconstructivism"

# ── Vernacular ────────────────────────────────────────────────────────────────

def "arch:style:cave_dwelling" "Carved into rock or earth; Cappadocia, Matmata (Tunisia), Loess Plateau yaodong (China); passive thermal mass; Petra rock-cut architecture."
ln arch:style:cave_dwelling arch:style sys:part_of
ln arch:style:cave_dwelling arch:region:vernacular arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:cave_dwelling"

def "arch:style:adobe_architecture" "Sun-dried mud brick; Saharan, Southwestern USA (Pueblo), Mali (Great Mosque of Djenné); thermal mass; annual replastering maintains form."
ln arch:style:adobe_architecture arch:style sys:part_of
ln arch:style:adobe_architecture arch:region:vernacular arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:adobe_architecture"

def "arch:style:stave_church" "Norwegian wooden post construction (11th–14th c.); Borgund stave church; no nails in main structure; dragon-head gables; Norse decorative vocabulary."
ln arch:style:stave_church arch:style sys:part_of
ln arch:style:stave_church arch:region:vernacular arch:influenced_by
set.add name="ontology.architecture_styles" id="arch:style:stave_church"
