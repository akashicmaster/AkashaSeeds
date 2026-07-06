# art_techniques.ak
# Painting techniques, media, and architectural structural elements
# Sources: Mayer's Artist's Handbook, Ching's Architectural Graphics — Public domain
#

# ── Namespace anchors ──────────────────────────────────────────────────────────

def "art:technique" "Root node for painting techniques, media, and visual art methods."
def "arch:element" "Root node for structural and formal architectural elements."

# ── Painting techniques ───────────────────────────────────────────────────────

def "art:technique:buon_fresco" "Painting on wet intonaco plaster; pigments bond with calcium carbonate as it dries; permanent; Giotto, Michelangelo; cannot be corrected once dry."
ln art:technique:buon_fresco art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:buon_fresco"

def "art:technique:fresco_secco" "Painting on dry plaster with glue or lime binder; less permanent than buon fresco; allows correction; more prone to detachment; many medieval church decorations."
ln art:technique:fresco_secco art:technique sys:part_of
ln art:technique:fresco_secco art:technique:buon_fresco art:derived_from
set.add name="ontology.art_techniques" id="art:technique:fresco_secco"

def "art:technique:egg_tempera" "Egg yolk emulsion binder; quick-drying; luminous translucent layers; Byzantine and medieval panel painting; revived by Pre-Raphaelites and Andrew Wyeth."
ln art:technique:egg_tempera art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:egg_tempera"

def "art:technique:oil_painting" "Linseed, walnut, or poppy oil binder; Jan van Eyck credited with perfecting; slow drying allows blending; sfumato, glazing, impasto all possible; dominant since 15th c."
ln art:technique:oil_painting art:technique sys:part_of
ln art:technique:oil_painting art:technique:egg_tempera art:derived_from
set.add name="ontology.art_techniques" id="art:technique:oil_painting"

def "art:technique:watercolour" "Transparent water-soluble pigments on absorbent paper; white of paper creates luminosity; Dürer's nature studies; Turner, Cézanne; correction difficult."
ln art:technique:watercolour art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:watercolour"

def "art:technique:gouache" "Opaque watercolour with chalk or Chinese white added; flat opaque colour; Persian miniature, poster design, animation backgrounds; corrections possible."
ln art:technique:gouache art:technique sys:part_of
ln art:technique:gouache art:technique:watercolour art:derived_from
set.add name="ontology.art_techniques" id="art:technique:gouache"

def "art:technique:encaustic" "Pigmented hot beeswax applied to surface; Fayum mummy portraits (Egypt, 1st–3rd c. CE); ancient Greek ship painting; encaustic tiles; highly durable medium."
ln art:technique:encaustic art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:encaustic"

def "art:technique:mosaic" "Small tesserae (glass, stone, ceramic, gold leaf) set in mortar; Byzantine church interiors; Ravenna (Sant'Apollinare, 6th c.); Pompeii floors; durable and luminous."
ln art:technique:mosaic art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:mosaic"

def "art:technique:gilding" "Application of gold leaf to surface; gold ground in icon painting; manuscript illumination; carved frame decoration; mordant gilding vs water gilding techniques."
ln art:technique:gilding art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:gilding"

def "art:technique:illuminated_manuscript" "Vellum or parchment; gold leaf + egg tempera + ink; dedicated scriptoria; Book of Kells (c.800 CE); Lindisfarne Gospels; Très Riches Heures du Duc de Berry."
ln art:technique:illuminated_manuscript art:technique sys:part_of
ln art:technique:illuminated_manuscript art:technique:egg_tempera art:derived_from
ln art:technique:illuminated_manuscript art:technique:gilding art:derived_from
set.add name="ontology.art_techniques" id="art:technique:illuminated_manuscript"

def "art:technique:woodblock_print" "Relief printing from carved wood matrix; ink applied to raised surface; Chinese origin (Tang dynasty); Ukiyo-e polychrome nishiki-e; Dürer."
ln art:technique:woodblock_print art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:woodblock_print"

def "art:technique:intaglio_print" "Ink held in incised lines of metal plate; engraving (burin), etching (acid), drypoint (needle); Mantegna, Dürer, Rembrandt; enables fine detail."
ln art:technique:intaglio_print art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:intaglio_print"

def "art:technique:lithography" "Planographic printing; grease on limestone repels water; Senefelder (1796); Daumier's political satire; Toulouse-Lautrec's posters; basis of offset printing."
ln art:technique:lithography art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:lithography"

def "art:technique:serigraphy" "Silk-screen printing; stencil on mesh; ink pushed through; commercial and fine art applications; Warhol (Marilyn, 1962); multiple colour registration passes."
ln art:technique:serigraphy art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:serigraphy"

def "art:technique:sfumato" "\"Like smoke\"; Leonardo's gradual tonal transition without hard outline; atmospheric perspective; Mona Lisa; Ginevra de' Benci; achieved through oil glazing layers."
ln art:technique:sfumato art:technique sys:part_of
ln art:technique:sfumato art:technique:oil_painting art:derived_from
set.add name="ontology.art_techniques" id="art:technique:sfumato"

def "art:technique:chiaroscuro" "Strong light-dark contrast modelling form through shadow; Caravaggio's tenebrism (extreme version); Rembrandt's warm light emerging from darkness; chiaroscuro woodcut."
ln art:technique:chiaroscuro art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:chiaroscuro"

def "art:technique:impasto" "Thick paint application creating textured surface; Van Gogh's swirling strokes; Rembrandt's highlights; palette knife work; physical presence of paint as subject."
ln art:technique:impasto art:technique sys:part_of
ln art:technique:impasto art:technique:oil_painting art:derived_from
set.add name="ontology.art_techniques" id="art:technique:impasto"

def "art:technique:pointillism" "Juxtaposed dots of pure colour; optical mixing in viewer's eye; Seurat (A Sunday on La Grande Jatte, 1886); Signac; Neo-Impressionism; also called Divisionism."
ln art:technique:pointillism art:technique sys:part_of
ln art:technique:pointillism art:technique:oil_painting art:derived_from
set.add name="ontology.art_techniques" id="art:technique:pointillism"

def "art:technique:grisaille" "Painting in grey tones simulating sculpture; monochrome underpainting; Jan van Eyck's Ghent Altarpiece wings; stained glass imitation; preparatory technique."
ln art:technique:grisaille art:technique sys:part_of
ln art:technique:grisaille art:technique:egg_tempera art:derived_from
set.add name="ontology.art_techniques" id="art:technique:grisaille"

def "art:technique:nihonga" "Japanese painting style (Meiji onward); mineral pigments and nikawa (hide glue) on washi or silk; Yokoyama Taikan; contrasted with Western-style yoga."
ln art:technique:nihonga art:technique sys:part_of
set.add name="ontology.art_techniques" id="art:technique:nihonga"

# ── Architectural elements ────────────────────────────────────────────────────

def "arch:element:arch" "Curved structure spanning an opening; transfers compressive load to piers; Roman mastery; semicircular, pointed, horseshoe, ogee, and segmental variants."
ln arch:element:arch arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:arch"

def "arch:element:barrel_vault" "Semicircular arched ceiling extruded along an axis; continuous compressive tunnel; Romanesque nave; requires thick walls with no clerestory."
ln arch:element:barrel_vault arch:element sys:part_of
ln arch:element:barrel_vault arch:element:arch arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:barrel_vault"

def "arch:element:groin_vault" "Intersection of two barrel vaults at right angles; load concentrated on four piers; allows windows in bay walls; predecessor to ribbed vault."
ln arch:element:groin_vault arch:element sys:part_of
ln arch:element:groin_vault arch:element:barrel_vault arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:groin_vault"

def "arch:element:ribbed_vault" "Stone skeleton of ribs carries load; infill web panels non-structural; Gothic invention; allows thinner bay construction; fan vault is English Perpendicular variant."
ln arch:element:ribbed_vault arch:element sys:part_of
ln arch:element:ribbed_vault arch:element:groin_vault arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:ribbed_vault"

def "arch:element:dome" "Hemispheric surface of revolution; pendentive (Byzantine) or squinch (Islamic) resolves square-to-circle transition; oculus; Pantheon, Hagia Sophia, St. Peter's."
ln arch:element:dome arch:element sys:part_of
ln arch:element:dome arch:element:arch arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:dome"

def "arch:element:flying_buttress" "External arched support transferring lateral thrust of nave vault away from walls; Gothic essential; allows thin clerestory walls and large stained glass windows."
ln arch:element:flying_buttress arch:element sys:part_of
ln arch:element:flying_buttress arch:element:arch arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:flying_buttress"

def "arch:element:column_order" "Classical column with capital; Tuscan, Doric, Ionic, Corinthian, Composite orders; proportional system in Vitruvius; fundamental grammar of Western architecture."
ln arch:element:column_order arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:column_order"

def "arch:element:pilotis" "Ground-floor columns raising building off ground; Le Corbusier's first point of five; creates free ground plane beneath; Villa Savoye; circulation beneath building."
ln arch:element:pilotis arch:element sys:part_of
ln arch:element:pilotis arch:element:column_order arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:pilotis"

def "arch:element:cantilever" "Beam or slab anchored at one end and unsupported at other; steel and reinforced concrete enable long spans; Fallingwater (Wright, 1936); corbelling is masonry version."
ln arch:element:cantilever arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:cantilever"

def "arch:element:curtain_wall" "Non-structural glass-and-metal facade hung from floor slabs; separates weather envelope from structure; Lever House (1952); standard skyscraper cladding system."
ln arch:element:curtain_wall arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:curtain_wall"

def "arch:element:dougong" "Chinese interlocking wood bracket cluster distributing roof load to column; mortise-and-tenon joinery; no metal fasteners; highly ornamental; Forbidden City."
ln arch:element:dougong arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:dougong"

def "arch:element:muqarnas" "Islamic corbelled stalactite vaulting; honeycombed concave cells; purely decorative; Alhambra Hall of the Abencerrajes; mathematically generated geometry."
ln arch:element:muqarnas arch:element sys:part_of
ln arch:element:muqarnas arch:element:dome arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:muqarnas"

def "arch:element:torii" "Japanese Shinto gate marking transition to sacred space; two upright posts + two crossbeams; vermilion lacquer; Fushimi Inari; also constructed in stone and metal."
ln arch:element:torii arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:torii"

def "arch:element:pagoda" "East Asian multi-storey Buddhist tower; derived from Indian stupa; each storey with upturned eaves; timber or brick; Giant Wild Goose Pagoda (Xi'an, 652 CE)."
ln arch:element:pagoda arch:element sys:part_of
ln arch:element:pagoda arch:element:dome arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:pagoda"

def "arch:element:shikhara" "Curvilinear tower of North Indian Nagara temple style; rises over garbhagriha (inner sanctuary); amalaka finial disk at apex; Khajuraho."
ln arch:element:shikhara arch:element sys:part_of
ln arch:element:shikhara arch:element:dome arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:shikhara"

def "arch:element:gopuram" "Monumental gateway tower of South Indian Dravidian temple; tiered horizontal bands; densely carved mythological figures; Meenakshi Temple, Madurai."
ln arch:element:gopuram arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:gopuram"

def "arch:element:minaret" "Tower from which muezzin calls to prayer; cylindrical (Ottoman), square (North African), spiral (Samarra); usually at mosque corners; marks Islamic sacred space."
ln arch:element:minaret arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:minaret"

def "arch:element:mihrab" "Niche in mosque's qibla wall indicating direction of Mecca; prayer orientation; richly decorated; first at Masjid an-Nabawi (Medina, expanded 706 CE)."
ln arch:element:mihrab arch:element sys:part_of
set.add name="ontology.arch_elements" id="arch:element:mihrab"

def "arch:element:iwan" "Large vaulted hall open at one end to courtyard; Persian origin; Seljuk mosque and madrasa plan; Sasanian palace predecessor; monumental entrance framing device."
ln arch:element:iwan arch:element sys:part_of
ln arch:element:iwan arch:element:barrel_vault arch:derived_from
set.add name="ontology.arch_elements" id="arch:element:iwan"
