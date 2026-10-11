# painting_movements.ak
# Painting movements and traditions — prehistoric cave art to 20th century
# Sources: Grove Art, Janson, Oxford Art Online — Public domain terminology
#

# ── Namespace anchors ──────────────────────────────────────────────────────────

def "art:movement" "Root node for painting movements and traditions worldwide."
def "art:region:western" "Western art traditions, from ancient Mediterranean to 20th-century Europe and Americas."
def "art:region:east_asian" "East Asian painting traditions — Chinese, Japanese, Korean."
def "art:region:south_asian" "South Asian painting traditions — Indian subcontinent."
def "art:region:islamic_art" "Islamic visual arts including manuscript illustration, calligraphy, and geometric ornament."
def "art:region:african_oceanic" "African, Oceanic, and Pre-Columbian visual traditions."

# ── Prehistoric and Ancient ────────────────────────────────────────────────────

def "art:movement:paleolithic_art" "Oldest known art (c.40,000–10,000 BCE); Chauvet Cave (France, 36,000 BCE), Altamira (Spain, 15,000 BCE), Lascaux (France, 17,000 BCE); charcoal and ochre animals; hand stencils."
ln art:movement:paleolithic_art art:movement sys:part_of
ln art:movement:paleolithic_art art:region:african_oceanic art:influenced_by
set.add name="ontology.art_movements" id="art:movement:paleolithic_art"

def "art:movement:neolithic_rock_art" "Post-Palaeolithic cave and rock painting worldwide; Laas Geel (Somalia, c.9,000 BCE); Tassili n'Ajjer (Algeria); figures and hunting scenes; worldwide phenomenon."
ln art:movement:neolithic_rock_art art:movement sys:part_of
ln art:movement:neolithic_rock_art art:movement:paleolithic_art art:preceded_by
set.add name="ontology.art_movements" id="art:movement:neolithic_rock_art"

def "art:movement:egyptian_painting" "Tomb and temple painting (c.3100–30 BCE); hieratic scale; composite figures (head profile, shoulders frontal); mineral pigments on plaster; Valley of the Kings."
ln art:movement:egyptian_painting art:movement sys:part_of
ln art:movement:egyptian_painting art:region:western art:influenced_by
set.add name="ontology.art_movements" id="art:movement:egyptian_painting"

def "art:movement:minoan_fresco" "Aegean Bronze Age fresco (c.1700–1400 BCE); Knossos palace; naturalistic dolphins, bull-leapers, lilies; imported by Mycenae; lost with palace destruction."
ln art:movement:minoan_fresco art:movement sys:part_of
ln art:movement:minoan_fresco art:region:western art:influenced_by
ln art:movement:minoan_fresco art:movement:egyptian_painting art:influenced_by
set.add name="ontology.art_movements" id="art:movement:minoan_fresco"

def "art:movement:greek_vase_painting" "Black-figure (700–480 BCE) and red-figure (530 BCE onward) ceramic painting; mythological narrative; Exekias, Euphronios; main surviving Greek pictorial record."
ln art:movement:greek_vase_painting art:movement sys:part_of
ln art:movement:greek_vase_painting art:region:western art:influenced_by
ln art:movement:greek_vase_painting art:movement:minoan_fresco art:preceded_by
set.add name="ontology.art_movements" id="art:movement:greek_vase_painting"

def "art:movement:pompeii_fresco" "Roman wall painting (1st c. BCE–79 CE); four Pompeian styles; Villa dei Misteri Dionysiac frieze; illusionistic architecture; preserved by Vesuvius eruption."
ln art:movement:pompeii_fresco art:movement sys:part_of
ln art:movement:pompeii_fresco art:region:western art:influenced_by
ln art:movement:pompeii_fresco art:movement:greek_vase_painting art:preceded_by
set.add name="ontology.art_movements" id="art:movement:pompeii_fresco"

def "art:movement:buddhist_mural" "Cave and temple painting spanning Asia; Ajanta Caves (India, 2nd c. BCE–7th c. CE); Dunhuang Mogao Caves (China, 4th–14th c.); Korean Goguryeo tomb murals; spread of Buddhist iconography."
ln art:movement:buddhist_mural art:movement sys:part_of
ln art:movement:buddhist_mural art:region:south_asian art:influenced_by
ln art:movement:buddhist_mural art:region:east_asian art:influenced_by
set.add name="ontology.art_movements" id="art:movement:buddhist_mural"

# ── Medieval ──────────────────────────────────────────────────────────────────

def "art:movement:byzantine_art" "Sacred icon painting (4th–15th c.); gold ground; hieratic frontal figures; theological programme; Ravenna mosaics; Pantocrator type; Greek cross church interiors."
ln art:movement:byzantine_art art:movement sys:part_of
ln art:movement:byzantine_art art:region:western art:influenced_by
ln art:movement:byzantine_art art:movement:pompeii_fresco art:preceded_by
set.add name="ontology.art_movements" id="art:movement:byzantine_art"

def "art:movement:romanesque_painting" "Church fresco and manuscript illumination (c.1000–1200); stylised drapery; didactic narrative; Saint-Savin-sur-Gartempe vault frescoes."
ln art:movement:romanesque_painting art:movement sys:part_of
ln art:movement:romanesque_painting art:region:western art:influenced_by
ln art:movement:romanesque_painting art:movement:byzantine_art art:derived_from
set.add name="ontology.art_movements" id="art:movement:romanesque_painting"

def "art:movement:gothic_painting" "International Gothic and early Italian panel painting (c.1200–1400); Cimabue, Duccio; gold ground giving way to spatial depth; Sienese vs Florentine schools."
ln art:movement:gothic_painting art:movement sys:part_of
ln art:movement:gothic_painting art:region:western art:influenced_by
ln art:movement:gothic_painting art:movement:romanesque_painting art:preceded_by
set.add name="ontology.art_movements" id="art:movement:gothic_painting"

def "art:movement:illuminated_manuscript" "Decorated books on vellum (6th–15th c.); gold leaf and egg tempera; Book of Kells, Très Riches Heures du Duc de Berry; secular and sacred programmes."
ln art:movement:illuminated_manuscript art:movement sys:part_of
ln art:movement:illuminated_manuscript art:region:western art:influenced_by
ln art:movement:illuminated_manuscript art:movement:byzantine_art art:derived_from
set.add name="ontology.art_movements" id="art:movement:illuminated_manuscript"

def "art:movement:proto_renaissance" "Giotto di Bondone (c.1267–1337); Arena Chapel frescoes (1304–06); naturalistic figures, spatial depth, emotional expression; revolutionary break from Byzantine convention."
ln art:movement:proto_renaissance art:movement sys:part_of
ln art:movement:proto_renaissance art:region:western art:influenced_by
ln art:movement:proto_renaissance art:movement:gothic_painting art:preceded_by
ln art:movement:proto_renaissance art:movement:byzantine_art art:reacts_against
set.add name="ontology.art_movements" id="art:movement:proto_renaissance"

# ── Renaissance ───────────────────────────────────────────────────────────────

def "art:movement:early_renaissance" "Florence 15th c.; Masaccio (Brancacci Chapel), Fra Angelico, Botticelli; linear perspective (Brunelleschi-Alberti); anatomical study; classical themes revived."
ln art:movement:early_renaissance art:movement sys:part_of
ln art:movement:early_renaissance art:region:western art:influenced_by
ln art:movement:early_renaissance art:movement:proto_renaissance art:derived_from
set.add name="ontology.art_movements" id="art:movement:early_renaissance"

def "art:movement:northern_renaissance" "Flemish and German painting (15th–16th c.); Van Eyck's oil technique; Dürer; Memling; minute naturalistic detail; merchant patronage; moralising interior scenes."
ln art:movement:northern_renaissance art:movement sys:part_of
ln art:movement:northern_renaissance art:region:western art:influenced_by
ln art:movement:northern_renaissance art:movement:early_renaissance art:influenced_by
set.add name="ontology.art_movements" id="art:movement:northern_renaissance"

def "art:movement:high_renaissance" "Italy c.1490–1520; Leonardo, Michelangelo, Raphael; sfumato, contrapposto, grand idealisation; Sistine Chapel ceiling (1508–12); School of Athens."
ln art:movement:high_renaissance art:movement sys:part_of
ln art:movement:high_renaissance art:region:western art:influenced_by
ln art:movement:high_renaissance art:movement:early_renaissance art:derived_from
set.add name="ontology.art_movements" id="art:movement:high_renaissance"

def "art:movement:venetian_renaissance" "Bellini, Giorgione, Titian; rich colour over Florentine contour; atmospheric landscape; poesia; oil on canvas as standard medium."
ln art:movement:venetian_renaissance art:movement sys:part_of
ln art:movement:venetian_renaissance art:region:western art:influenced_by
ln art:movement:venetian_renaissance art:movement:early_renaissance art:derived_from
ln art:movement:venetian_renaissance art:movement:northern_renaissance art:influenced_by
set.add name="ontology.art_movements" id="art:movement:venetian_renaissance"

def "art:movement:mannerism" "c.1520–1600; Pontormo, Rosso, Parmigianino, El Greco; elongated figures; acidic colour; emotional distortion; reaction to High Renaissance harmony."
ln art:movement:mannerism art:movement sys:part_of
ln art:movement:mannerism art:region:western art:influenced_by
ln art:movement:mannerism art:movement:high_renaissance art:reacts_against
set.add name="ontology.art_movements" id="art:movement:mannerism"

# ── Baroque and after ─────────────────────────────────────────────────────────

def "art:movement:baroque_painting" "c.1600–1750; Caravaggio (tenebrism), Rubens, Bernini; dramatic chiaroscuro; movement; emotional intensity; Counter-Reformation imagery."
ln art:movement:baroque_painting art:movement sys:part_of
ln art:movement:baroque_painting art:region:western art:influenced_by
ln art:movement:baroque_painting art:movement:mannerism art:preceded_by
set.add name="ontology.art_movements" id="art:movement:baroque_painting"

def "art:movement:dutch_golden_age" "Amsterdam 17th c.; Rembrandt, Vermeer, Hals, de Hooch; Protestant domestic scenes; guild portraits; interior light from windows; no church patronage."
ln art:movement:dutch_golden_age art:movement sys:part_of
ln art:movement:dutch_golden_age art:region:western art:influenced_by
ln art:movement:dutch_golden_age art:movement:baroque_painting art:derived_from
set.add name="ontology.art_movements" id="art:movement:dutch_golden_age"

def "art:movement:spanish_baroque" "Velázquez, Zurbarán, Murillo; royal portraiture; bodegones (still life); Las Meninas (1656); restrained colour; strong tonal contrasts."
ln art:movement:spanish_baroque art:movement sys:part_of
ln art:movement:spanish_baroque art:region:western art:influenced_by
ln art:movement:spanish_baroque art:movement:baroque_painting art:derived_from
set.add name="ontology.art_movements" id="art:movement:spanish_baroque"

def "art:movement:rococo_painting" "France 18th c.; Watteau, Boucher, Fragonard; pastel palette; fête galante; aristocratic playfulness; reaction against Baroque gravity."
ln art:movement:rococo_painting art:movement sys:part_of
ln art:movement:rococo_painting art:region:western art:influenced_by
ln art:movement:rococo_painting art:movement:baroque_painting art:reacts_against
set.add name="ontology.art_movements" id="art:movement:rococo_painting"

def "art:movement:neoclassicism" "c.1760–1820; David, Ingres, Mengs; moral history painting; Roman subject matter; clear contour; response to Pompeii discovery and Enlightenment ideals."
ln art:movement:neoclassicism art:movement sys:part_of
ln art:movement:neoclassicism art:region:western art:influenced_by
ln art:movement:neoclassicism art:movement:rococo_painting art:reacts_against
set.add name="ontology.art_movements" id="art:movement:neoclassicism"

def "art:movement:romanticism" "c.1800–1850; Delacroix, Goya, Géricault, Friedrich, Turner; emotion over reason; sublime landscape; nationalism; Raft of the Medusa (Géricault, 1819)."
ln art:movement:romanticism art:movement sys:part_of
ln art:movement:romanticism art:region:western art:influenced_by
ln art:movement:romanticism art:movement:neoclassicism art:reacts_against
set.add name="ontology.art_movements" id="art:movement:romanticism"

def "art:movement:realism" "c.1840–1880; Courbet, Millet, Daumier; contemporary peasant and working life; unidealized; rejected by Salon; Courbet's Stone Breakers (1849–50); social critique."
ln art:movement:realism art:movement sys:part_of
ln art:movement:realism art:region:western art:influenced_by
ln art:movement:realism art:movement:romanticism art:reacts_against
set.add name="ontology.art_movements" id="art:movement:realism"

def "art:movement:impressionism" "Paris 1870s–1880s; Monet, Renoir, Degas, Pissarro; painting outdoors; broken brushwork; light effects; rejected by Salon; named from Monet's Impression, Sunrise (1872)."
ln art:movement:impressionism art:movement sys:part_of
ln art:movement:impressionism art:region:western art:influenced_by
ln art:movement:impressionism art:movement:realism art:derived_from
set.add name="ontology.art_movements" id="art:movement:impressionism"

def "art:movement:post_impressionism" "c.1886–1910; Cézanne (structure), Seurat (pointillism), Van Gogh (expression), Gauguin (primitivism); divergent individual responses to Impressionism."
ln art:movement:post_impressionism art:movement sys:part_of
ln art:movement:post_impressionism art:region:western art:influenced_by
ln art:movement:post_impressionism art:movement:impressionism art:derived_from
set.add name="ontology.art_movements" id="art:movement:post_impressionism"

def "art:movement:symbolism" "1880s–1900s; Moreau, Redon, Puvis de Chavannes, Klimt; inner states over observed reality; myth, dream, decadence; precursor to Surrealism."
ln art:movement:symbolism art:movement sys:part_of
ln art:movement:symbolism art:region:western art:influenced_by
ln art:movement:symbolism art:movement:impressionism art:reacts_against
set.add name="ontology.art_movements" id="art:movement:symbolism"

def "art:movement:fauvism" "France c.1905–1908; Matisse, Derain, Vlaminck; pure non-descriptive colour; \"wild beasts\"; 1905 Salon d'Automne; precursor to Expressionism."
ln art:movement:fauvism art:movement sys:part_of
ln art:movement:fauvism art:region:western art:influenced_by
ln art:movement:fauvism art:movement:post_impressionism art:derived_from
set.add name="ontology.art_movements" id="art:movement:fauvism"

def "art:movement:expressionism" "German c.1905–1930; Die Brücke (Kirchner), Der Blaue Reiter (Marc, Kandinsky); distorted form, vivid colour, inner anxiety; Munch's Scream (1893) as precursor."
ln art:movement:expressionism art:movement sys:part_of
ln art:movement:expressionism art:region:western art:influenced_by
ln art:movement:expressionism art:movement:fauvism art:influenced_by
ln art:movement:expressionism art:movement:symbolism art:influenced_by
set.add name="ontology.art_movements" id="art:movement:expressionism"

def "art:movement:cubism" "Paris c.1907–1920; Picasso and Braque; simultaneous viewpoints; fractured planes; Analytic (monochrome) vs Synthetic (collage); Les Demoiselles d'Avignon (1907)."
ln art:movement:cubism art:movement sys:part_of
ln art:movement:cubism art:region:western art:influenced_by
ln art:movement:cubism art:movement:post_impressionism art:derived_from
set.add name="ontology.art_movements" id="art:movement:cubism"

def "art:movement:futurism" "Italy c.1909–1944; Boccioni, Severini; speed, technology, violence; simultaneity of motion; Marinetti's manifesto (1909); influenced Constructivism."
ln art:movement:futurism art:movement sys:part_of
ln art:movement:futurism art:region:western art:influenced_by
ln art:movement:futurism art:movement:cubism art:influenced_by
set.add name="ontology.art_movements" id="art:movement:futurism"

def "art:movement:dada" "1916–1924; Zürich, New York, Berlin; anti-art; chance procedures; readymade (Duchamp); Cabaret Voltaire; Arp, Ernst, Man Ray; reaction to WWI destruction."
ln art:movement:dada art:movement sys:part_of
ln art:movement:dada art:region:western art:influenced_by
ln art:movement:dada art:movement:futurism art:reacts_against
set.add name="ontology.art_movements" id="art:movement:dada"

def "art:movement:surrealism" "1924 onwards; Breton's manifesto; unconscious and dreamlike imagery; Dalí, Magritte, Ernst, Kahlo; automatic writing; biomorphic and illusionistic variants."
ln art:movement:surrealism art:movement sys:part_of
ln art:movement:surrealism art:region:western art:influenced_by
ln art:movement:surrealism art:movement:dada art:derived_from
ln art:movement:surrealism art:movement:symbolism art:influenced_by
set.add name="ontology.art_movements" id="art:movement:surrealism"

def "art:movement:abstract_expressionism" "New York 1940s–50s; Pollock (action painting), de Kooning, Rothko (colour field), Newman; large scale; gestural; first major American movement."
ln art:movement:abstract_expressionism art:movement sys:part_of
ln art:movement:abstract_expressionism art:region:western art:influenced_by
ln art:movement:abstract_expressionism art:movement:surrealism art:influenced_by
ln art:movement:abstract_expressionism art:movement:expressionism art:influenced_by
set.add name="ontology.art_movements" id="art:movement:abstract_expressionism"

def "art:movement:pop_art" "1950s–60s UK and USA; Warhol, Lichtenstein, Hamilton, Hockney; consumer imagery; mass media; irony; reaction against Abstract Expressionism's seriousness."
ln art:movement:pop_art art:movement sys:part_of
ln art:movement:pop_art art:region:western art:influenced_by
ln art:movement:pop_art art:movement:abstract_expressionism art:reacts_against
set.add name="ontology.art_movements" id="art:movement:pop_art"

def "art:movement:conceptual_art" "1960s onwards; Kosuth, LeWitt, Lawrence Weiner; idea over object; \"art after philosophy\"; instructions as art; dematerialised artwork."
ln art:movement:conceptual_art art:movement sys:part_of
ln art:movement:conceptual_art art:region:western art:influenced_by
ln art:movement:conceptual_art art:movement:dada art:influenced_by
set.add name="ontology.art_movements" id="art:movement:conceptual_art"

def "art:movement:land_art" "1960s–70s; Smithson (Spiral Jetty, 1970), Long, Heizer; landscape-scale interventions outside gallery system; photography as primary documentary record."
ln art:movement:land_art art:movement sys:part_of
ln art:movement:land_art art:region:western art:influenced_by
ln art:movement:land_art art:movement:conceptual_art art:derived_from
set.add name="ontology.art_movements" id="art:movement:land_art"

# ── East Asian traditions ──────────────────────────────────────────────────────

def "art:movement:chinese_landscape_painting" "山水画 shanshui; ink and brush on silk or paper; Song dynasty (10th–13th c.); Fan Kuan, Guo Xi; negative space; atmospheric mist; literati ideal."
ln art:movement:chinese_landscape_painting art:movement sys:part_of
ln art:movement:chinese_landscape_painting art:region:east_asian art:influenced_by
set.add name="ontology.art_movements" id="art:movement:chinese_landscape_painting"

def "art:movement:chinese_bird_flower" "花鳥画 huaniao; Song Academy painting; Emperor Hui Zong; meticulous gongbi and expressive xieyi styles; nature as moral exemplar."
ln art:movement:chinese_bird_flower art:movement sys:part_of
ln art:movement:chinese_bird_flower art:region:east_asian art:influenced_by
set.add name="ontology.art_movements" id="art:movement:chinese_bird_flower"

def "art:movement:literati_painting" "文人画 wenrenhua; scholar-amateur ideal over court professionalism; Su Shi (Su Dongpo); calligraphic brushwork; Four Masters of Yuan; expression over representation."
ln art:movement:literati_painting art:movement sys:part_of
ln art:movement:literati_painting art:region:east_asian art:influenced_by
ln art:movement:literati_painting art:movement:chinese_landscape_painting art:derived_from
set.add name="ontology.art_movements" id="art:movement:literati_painting"

def "art:movement:yamato_e" "Japanese court painting (9th–14th c.); horizontal narrative scrolls (emakimono); Tale of Genji scroll; bright mineral pigments; flat patterns; Japanese subject matter."
ln art:movement:yamato_e art:movement sys:part_of
ln art:movement:yamato_e art:region:east_asian art:influenced_by
set.add name="ontology.art_movements" id="art:movement:yamato_e"

def "art:movement:kano_school" "Dominant Japanese painting lineage (15th–19th c.); ink monochrome and gold screen painting; Kano Eitoku; shogunal patronage; fusuma sliding door compositions."
ln art:movement:kano_school art:movement sys:part_of
ln art:movement:kano_school art:region:east_asian art:influenced_by
ln art:movement:kano_school art:movement:chinese_landscape_painting art:influenced_by
ln art:movement:kano_school art:movement:yamato_e art:derived_from
set.add name="ontology.art_movements" id="art:movement:kano_school"

def "art:movement:rinpa" "Japanese decorative painting (17th c.); Hon'ami Koetsu, Tawaraya Sotatsu, Ogata Korin; bold design; gold and silver leaf; natural motifs; Korin's Irises."
ln art:movement:rinpa art:movement sys:part_of
ln art:movement:rinpa art:region:east_asian art:influenced_by
ln art:movement:rinpa art:movement:yamato_e art:derived_from
set.add name="ontology.art_movements" id="art:movement:rinpa"

def "art:movement:ukiyo_e" "Japanese woodblock prints and paintings (17th–19th c.); floating world; Hokusai (Great Wave), Hiroshige, Utamaro; kabuki actors, courtesans, landscapes; influenced Impressionism."
ln art:movement:ukiyo_e art:movement sys:part_of
ln art:movement:ukiyo_e art:region:east_asian art:influenced_by
ln art:movement:impressionism art:movement:ukiyo_e art:influenced_by
set.add name="ontology.art_movements" id="art:movement:ukiyo_e"

# ── South Asian traditions ────────────────────────────────────────────────────

def "art:movement:mughal_miniature" "Indo-Persian court painting (16th–18th c.); Humayun brought Persian masters; Akbar's atelier; naturalistic portraiture; Hamzanama; hunt and court scenes."
ln art:movement:mughal_miniature art:movement sys:part_of
ln art:movement:mughal_miniature art:region:south_asian art:influenced_by
ln art:movement:mughal_miniature art:movement:persian_miniature art:derived_from
set.add name="ontology.art_movements" id="art:movement:mughal_miniature"

def "art:movement:rajput_painting" "Hindu court painting (17th–18th c.); Mewar, Bundi, Kishangarh schools; Radha-Krishna devotional theme; bold colour; contrasts with Mughal naturalism."
ln art:movement:rajput_painting art:movement sys:part_of
ln art:movement:rajput_painting art:region:south_asian art:influenced_by
ln art:movement:rajput_painting art:movement:mughal_miniature art:reacts_against
set.add name="ontology.art_movements" id="art:movement:rajput_painting"

def "art:movement:pahari_painting" "Hill-state painting (Kangra, Guler, Basohli; 17th–19th c.); lyrical Krishnaite themes; delicate line; Nainsukh; Gita Govinda illustrations."
ln art:movement:pahari_painting art:movement sys:part_of
ln art:movement:pahari_painting art:region:south_asian art:influenced_by
ln art:movement:pahari_painting art:movement:rajput_painting art:derived_from
set.add name="ontology.art_movements" id="art:movement:pahari_painting"

# ── Islamic traditions ────────────────────────────────────────────────────────

def "art:movement:persian_miniature" "Book illustration (13th–17th c.); Herat, Tabriz, Safavid schools; Behzad; bright lapis lazuli and gold; no cast shadow; Shahnameh illustrations."
ln art:movement:persian_miniature art:movement sys:part_of
ln art:movement:persian_miniature art:region:islamic_art art:influenced_by
set.add name="ontology.art_movements" id="art:movement:persian_miniature"

def "art:movement:islamic_calligraphy" "Sacred art of the written word; Kufic, Naskh, Thuluth, Nastaliq scripts; Quran illumination; applied to tiles and ceramics; highest art form in Islamic world."
ln art:movement:islamic_calligraphy art:movement sys:part_of
ln art:movement:islamic_calligraphy art:region:islamic_art art:influenced_by
set.add name="ontology.art_movements" id="art:movement:islamic_calligraphy"

def "art:movement:islamic_geometric_art" "Arabesque and geometric pattern; girih tile (mathematically generated); zellige mosaic; avoidance of figural representation in sacred contexts; infinite repeat."
ln art:movement:islamic_geometric_art art:movement sys:part_of
ln art:movement:islamic_geometric_art art:region:islamic_art art:influenced_by
set.add name="ontology.art_movements" id="art:movement:islamic_geometric_art"

# ── African and Pre-Columbian traditions ──────────────────────────────────────

def "art:movement:african_rock_art" "San/Bushman rock art (southern Africa); Drakensberg; X-ray figures; trance-state imagery; 3,000+ BCE to recent; Saharan rock art tradition distinct."
ln art:movement:african_rock_art art:movement sys:part_of
ln art:movement:african_rock_art art:region:african_oceanic art:influenced_by
ln art:movement:african_rock_art art:movement:paleolithic_art art:derived_from
set.add name="ontology.art_movements" id="art:movement:african_rock_art"

def "art:movement:pre_columbian_mural" "Teotihuacan (c.100–650 CE), Maya (Bonampak, c.790 CE), Aztec; narrative murals in temple precincts; Tlalocan paradise mural; vivid mineral pigments."
ln art:movement:pre_columbian_mural art:movement sys:part_of
ln art:movement:pre_columbian_mural art:region:african_oceanic art:influenced_by
set.add name="ontology.art_movements" id="art:movement:pre_columbian_mural"
