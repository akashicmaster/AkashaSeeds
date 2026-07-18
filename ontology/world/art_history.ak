# Akasha ontology (world pack) — art history: movements in order.
# Western/world art movements, tied to period, technique (art:technique:),
# studies (artsci:) and artists (person:). A-tier.

def "art:movement" "A style or movement in the history of art (美術運動)."
def "art:movement:cave_art" "The Paleolithic painted caves — humanity's first images."
ln art:movement:cave_art art:movement thesaurus:related
ln art:movement:cave_art hist:period:paleolithic art:of_period
ln art:movement:cave_art archaeo:site:lascaux thesaurus:related
def "art:movement:egyptian_art" "Ancient Egypt's frontal, canonical style over three millennia."
ln art:movement:egyptian_art art:movement thesaurus:related
ln art:movement:egyptian_art hist:period:bronze_age art:of_period
ln art:movement:cave_art art:movement:egyptian_art chrono:before
ln art:movement:egyptian_art hist:ancient_egypt thesaurus:related
def "art:movement:classical_greek_art" "Idealized human form and proportion — the classical ideal."
ln art:movement:classical_greek_art art:movement thesaurus:related
ln art:movement:classical_greek_art hist:period:classical_antiquity art:of_period
ln art:movement:egyptian_art art:movement:classical_greek_art chrono:before
ln art:movement:classical_greek_art hist:ancient_greece thesaurus:related
def "art:movement:byzantine_art" "Golden, hieratic icons and mosaics of the Christian East."
ln art:movement:byzantine_art art:movement thesaurus:related
ln art:movement:byzantine_art hist:period:late_antiquity art:of_period
ln art:movement:classical_greek_art art:movement:byzantine_art chrono:before
ln art:movement:byzantine_art hist:byzantine_empire thesaurus:related
ln art:movement:byzantine_art art:technique:mosaic thesaurus:related
def "art:movement:gothic_art" "Soaring cathedrals, stained glass and the pointed arch."
ln art:movement:gothic_art art:movement thesaurus:related
ln art:movement:gothic_art hist:period:high_middle_ages art:of_period
ln art:movement:byzantine_art art:movement:gothic_art chrono:before
def "art:movement:renaissance_art" "The rebirth of naturalism, perspective and the classical."
ln art:movement:renaissance_art art:movement thesaurus:related
ln art:movement:renaissance_art hist:period:renaissance art:of_period
ln art:movement:gothic_art art:movement:renaissance_art chrono:before
ln art:movement:renaissance_art person:leonardo_da_vinci thesaurus:related
ln art:movement:renaissance_art person:michelangelo thesaurus:related
ln art:movement:renaissance_art art:technique:oil_painting thesaurus:related
ln art:movement:renaissance_art art:technique:sfumato thesaurus:related
ln art:movement:renaissance_art artsci:art_history thesaurus:related
def "art:movement:mannerism" "Late-Renaissance elongation, tension and artifice."
ln art:movement:mannerism art:movement thesaurus:related
ln art:movement:mannerism hist:period:renaissance art:of_period
ln art:movement:renaissance_art art:movement:mannerism chrono:before
def "art:movement:baroque" "Dramatic light, movement and grandeur."
ln art:movement:baroque art:movement thesaurus:related
ln art:movement:baroque hist:period:reformation_era art:of_period
ln art:movement:mannerism art:movement:baroque chrono:before
ln art:movement:baroque person:rembrandt thesaurus:related
ln art:movement:baroque art:technique:chiaroscuro thesaurus:related
def "art:movement:rococo" "Light, ornate, playful aristocratic elegance."
ln art:movement:rococo art:movement thesaurus:related
ln art:movement:rococo hist:period:enlightenment art:of_period
ln art:movement:baroque art:movement:rococo chrono:before
def "art:movement:neoclassicism" "A return to classical order and civic virtue."
ln art:movement:neoclassicism art:movement thesaurus:related
ln art:movement:neoclassicism hist:period:enlightenment art:of_period
ln art:movement:rococo art:movement:neoclassicism chrono:before
def "art:movement:romanticism_art" "Emotion, the sublime and the individual over reason."
ln art:movement:romanticism_art art:movement thesaurus:related
ln art:movement:romanticism_art hist:period:industrial_revolution art:of_period
ln art:movement:neoclassicism art:movement:romanticism_art chrono:before
def "art:movement:realism_art" "The unidealized depiction of ordinary life."
ln art:movement:realism_art art:movement thesaurus:related
ln art:movement:realism_art hist:period:modern_era art:of_period
ln art:movement:romanticism_art art:movement:realism_art chrono:before
def "art:movement:impressionism" "Light and fleeting perception, painted en plein air."
ln art:movement:impressionism art:movement thesaurus:related
ln art:movement:impressionism hist:period:modern_era art:of_period
ln art:movement:realism_art art:movement:impressionism chrono:before
ln art:movement:impressionism art:technique:pointillism thesaurus:related
def "art:movement:post_impressionism" "Structure and expression beyond the impression."
ln art:movement:post_impressionism art:movement thesaurus:related
ln art:movement:post_impressionism hist:period:modern_era art:of_period
ln art:movement:impressionism art:movement:post_impressionism chrono:before
ln art:movement:post_impressionism person:van_gogh thesaurus:related
ln art:movement:post_impressionism art:technique:impasto thesaurus:related
def "art:movement:expressionism" "Distorted form to convey raw emotion."
ln art:movement:expressionism art:movement thesaurus:related
ln art:movement:expressionism hist:period:world_wars_era art:of_period
ln art:movement:post_impressionism art:movement:expressionism chrono:before
def "art:movement:cubism" "Fragmented, multi-viewpoint form (Picasso, Braque)."
ln art:movement:cubism art:movement thesaurus:related
ln art:movement:cubism hist:period:world_wars_era art:of_period
ln art:movement:expressionism art:movement:cubism chrono:before
ln art:movement:cubism person:picasso thesaurus:related
def "art:movement:surrealism" "The dream, the unconscious and the uncanny."
ln art:movement:surrealism art:movement thesaurus:related
ln art:movement:surrealism hist:period:world_wars_era art:of_period
ln art:movement:cubism art:movement:surrealism chrono:before
ln art:movement:surrealism nar:device:symbolism thesaurus:related
def "art:movement:abstract_art" "Non-representational form, line and colour."
ln art:movement:abstract_art art:movement thesaurus:related
ln art:movement:abstract_art hist:period:world_wars_era art:of_period
ln art:movement:surrealism art:movement:abstract_art chrono:before
def "art:movement:pop_art" "The imagery of mass consumer culture."
ln art:movement:pop_art art:movement thesaurus:related
ln art:movement:pop_art hist:period:cold_war art:of_period
ln art:movement:abstract_art art:movement:pop_art chrono:before
def "art:movement:contemporary_art" "The plural, conceptual art of the present."
ln art:movement:contemporary_art art:movement thesaurus:related
ln art:movement:contemporary_art hist:period:information_age art:of_period
ln art:movement:pop_art art:movement:contemporary_art chrono:before
ln art:movement:contemporary_art dh:cultural_analytics thesaurus:related
