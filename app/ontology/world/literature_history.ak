# Akasha ontology (world pack) — literature history: movements.
# Literary periods/movements, tied to period, epics (epic:) and authors. A-tier.

def "lit:movement" "A movement or period in literary history (文学運動)."
def "lit:movement:classical_literature" "The epics, tragedy and rhetoric of Greece and Rome."
ln lit:movement:classical_literature lit:movement thesaurus:related
ln lit:movement:classical_literature hist:period:classical_antiquity lit:of_period
ln lit:movement:classical_literature epic:iliad thesaurus:related
ln lit:movement:classical_literature epic:aeneid thesaurus:related
def "lit:movement:medieval_literature" "Chivalric romance, allegory and the Divine Comedy."
ln lit:movement:medieval_literature lit:movement thesaurus:related
ln lit:movement:medieval_literature hist:period:high_middle_ages lit:of_period
ln lit:movement:classical_literature lit:movement:medieval_literature chrono:before
ln lit:movement:medieval_literature epic:divine_comedy thesaurus:related
ln lit:movement:medieval_literature epic:canterbury_tales thesaurus:related
def "lit:movement:renaissance_literature" "Humanism, the sonnet and the first modern drama."
ln lit:movement:renaissance_literature lit:movement thesaurus:related
ln lit:movement:renaissance_literature hist:period:renaissance lit:of_period
ln lit:movement:medieval_literature lit:movement:renaissance_literature chrono:before
ln lit:movement:renaissance_literature epic:don_quixote thesaurus:related
def "lit:movement:enlightenment_literature" "Satire, reason and the rise of the novel."
ln lit:movement:enlightenment_literature lit:movement thesaurus:related
ln lit:movement:enlightenment_literature hist:period:enlightenment lit:of_period
ln lit:movement:renaissance_literature lit:movement:enlightenment_literature chrono:before
ln lit:movement:enlightenment_literature phil:school:empiricism thesaurus:related
def "lit:movement:romanticism_literature" "Emotion, nature and imagination (Goethe, the Romantics)."
ln lit:movement:romanticism_literature lit:movement thesaurus:related
ln lit:movement:romanticism_literature hist:period:industrial_revolution lit:of_period
ln lit:movement:enlightenment_literature lit:movement:romanticism_literature chrono:before
ln lit:movement:romanticism_literature person:goethe thesaurus:related
def "lit:movement:realism_literature" "The unvarnished depiction of society (Tolstoy, Dickens)."
ln lit:movement:realism_literature lit:movement thesaurus:related
ln lit:movement:realism_literature hist:period:modern_era lit:of_period
ln lit:movement:romanticism_literature lit:movement:realism_literature chrono:before
ln lit:movement:realism_literature quote:tolstoy_change thesaurus:related
def "lit:movement:naturalism" "Determinist realism of heredity and environment (Zola)."
ln lit:movement:naturalism lit:movement thesaurus:related
ln lit:movement:naturalism hist:period:modern_era lit:of_period
ln lit:movement:realism_literature lit:movement:naturalism chrono:before
def "lit:movement:symbolism" "Suggestion and the music of language over statement."
ln lit:movement:symbolism lit:movement thesaurus:related
ln lit:movement:symbolism hist:period:modern_era lit:of_period
ln lit:movement:naturalism lit:movement:symbolism chrono:before
ln lit:movement:symbolism nar:device:symbolism thesaurus:related
def "lit:movement:modernist_literature" "Stream of consciousness and the broken form (Joyce, Woolf)."
ln lit:movement:modernist_literature lit:movement thesaurus:related
ln lit:movement:modernist_literature hist:period:world_wars_era lit:of_period
ln lit:movement:symbolism lit:movement:modernist_literature chrono:before
ln lit:movement:modernist_literature nar:pov:stream_of_consciousness thesaurus:related
def "lit:movement:postmodern_literature" "Metafiction, irony and mistrust of grand narratives."
ln lit:movement:postmodern_literature lit:movement thesaurus:related
ln lit:movement:postmodern_literature hist:period:information_age lit:of_period
ln lit:movement:modernist_literature lit:movement:postmodern_literature chrono:before
ln lit:movement:postmodern_literature nar:device:unreliable_narrator thesaurus:related
