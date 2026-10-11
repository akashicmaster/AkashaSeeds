# Akasha ontology — Philosophy World: the thinkers behind the fields. Entrance: Socrates.
# Tier-B pack (教養 · liberal-arts, 任意ロード). References the base phil:field:* / phil:* concepts
# (base3/philosophy_branches.ak) via core relations; collects them in the phil:thinkers set.
# Every thinker carries a wp:<Title> alias → a Wikipedia exit link (surfaced in external_refs).

def "phil:thinker:socrates" "Socrates (c.470–399 BCE) — Athenian founder of Western moral philosophy. He claimed to know nothing, and examined others by relentless questioning (the Socratic method / elenchus). 'The unexamined life is not worth living.' He left no writings; we know him through Plato and Xenophon. Tried and condemned in Athens, he drank hemlock rather than flee."
al phil:thinker:socrates socrates
al phil:thinker:socrates wp:Socrates
ln phil:thinker:socrates phil:philosophy sys:part_of
ln phil:thinker:socrates phil:field:ethics thesaurus:related
ln phil:thinker:socrates phil:field:epistemology thesaurus:related
ln phil:thinker:socrates philosophy.dialectics thesaurus:related
ln phil:thinker:socrates phil:virtue thesaurus:related
set.add name="phil:thinkers" id="phil:thinker:socrates"

def "phil:thinker:plato" "Plato (c.428–348 BCE) — Socrates' student and founder of the Academy. His Theory of Forms holds that abstract ideals are more real than the sensible world. He wrote in dialogues (The Republic, Phaedo) and taught Aristotle."
al phil:thinker:plato plato
al phil:thinker:plato wp:Plato
ln phil:thinker:plato phil:philosophy sys:part_of
ln phil:thinker:plato phil:thinker:socrates thesaurus:related
ln phil:thinker:plato phil:field:metaphysics thesaurus:related
ln phil:thinker:plato phil:field:political_philosophy thesaurus:related
ln phil:thinker:plato phil:justice thesaurus:related
set.add name="phil:thinkers" id="phil:thinker:plato"

def "phil:thinker:aristotle" "Aristotle (384–322 BCE) — Plato's student and tutor of Alexander. He founded formal logic and empirical inquiry, taught virtue ethics as the golden mean, and analysed causation through the four causes. His work spans physics, biology, ethics, politics and poetics."
al phil:thinker:aristotle aristotle
al phil:thinker:aristotle wp:Aristotle
ln phil:thinker:aristotle phil:philosophy sys:part_of
ln phil:thinker:aristotle phil:thinker:plato thesaurus:related
ln phil:thinker:aristotle phil:field:logic thesaurus:related
ln phil:thinker:aristotle phil:field:ethics thesaurus:related
ln phil:thinker:aristotle phil:virtue thesaurus:related
set.add name="phil:thinkers" id="phil:thinker:aristotle"

def "phil:thinker:descartes" "René Descartes (1596–1650) — the French father of modern philosophy. Methodological doubt led him to 'Cogito, ergo sum' (I think, therefore I am). He argued for mind–body dualism and a rationalist foundation for knowledge."
al phil:thinker:descartes descartes
al phil:thinker:descartes wp:René_Descartes
ln phil:thinker:descartes phil:philosophy sys:part_of
ln phil:thinker:descartes phil:rationalism thesaurus:related
ln phil:thinker:descartes phil:field:philosophy_of_mind thesaurus:related
ln phil:thinker:descartes phil:field:epistemology thesaurus:related
set.add name="phil:thinkers" id="phil:thinker:descartes"

def "phil:thinker:kant" "Immanuel Kant (1724–1804) — German philosopher of the Enlightenment. He synthesised rationalism and empiricism, grounded ethics in the categorical imperative, and distinguished phenomena from things-in-themselves in the Critique of Pure Reason."
al phil:thinker:kant kant
al phil:thinker:kant wp:Immanuel_Kant
ln phil:thinker:kant phil:philosophy sys:part_of
ln phil:thinker:kant phil:deontology thesaurus:related
ln phil:thinker:kant phil:field:epistemology thesaurus:related
ln phil:thinker:kant phil:field:ethics thesaurus:related
set.add name="phil:thinkers" id="phil:thinker:kant"

def "phil:thinker:nietzsche" "Friedrich Nietzsche (1844–1900) — German philosopher and philologist. He critiqued morality and religion ('God is dead'), and advanced the will to power, the Übermensch and eternal recurrence. A forerunner of existentialism."
al phil:thinker:nietzsche nietzsche
al phil:thinker:nietzsche wp:Friedrich_Nietzsche
ln phil:thinker:nietzsche phil:philosophy sys:part_of
ln phil:thinker:nietzsche phil:existentialism thesaurus:related
ln phil:thinker:nietzsche phil:field:ethics thesaurus:related
set.add name="phil:thinkers" id="phil:thinker:nietzsche"
