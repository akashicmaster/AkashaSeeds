# Akasha ontology — Philosophy World: the 17 notions of the French Baccalauréat (voie générale,
# 2020). The exhibit's core: how philosophy has handled each concept. Each notion carries a rich
# note with its genealogy (named thinkers + their move), a wp:<Title> Wikipedia exit, links to the
# base phil:field:* branches and to key thinkers (thinkers.ak / authors.ak), and membership in
# phil:notions and one of the three perspectives. See docs/for-llm/philosophy-world-bac-notions.md.

def "phil:notion:art" "Art (l'art) — human creation aimed at the beautiful or the expressive, and the questions it raises: imitation, genius, taste, the autonomy of the work. Plato distrusted art as an imitation twice removed from truth; Aristotle valued mimesis and the catharsis of tragedy; Kant located beauty in a disinterested, universal judgment of taste; Nietzsche made art the highest affirmation of life."
al phil:notion:art wp:Art
ln phil:notion:art phil:philosophy sys:part_of
ln phil:notion:art phil:field:aesthetics thesaurus:related
ln phil:notion:art phil:thinker:plato thesaurus:related
ln phil:notion:art phil:thinker:aristotle thesaurus:related
ln phil:notion:art phil:thinker:kant thesaurus:related
ln phil:notion:art phil:thinker:nietzsche thesaurus:related
set.add name="phil:notions" id="phil:notion:art"
set.add name="phil:perspective:existence_culture" id="phil:notion:art"

def "phil:notion:bonheur" "Happiness (le bonheur) — the complete and lasting good life, and whether it can be pursued or only received. Aristotle defined eudaimonia as activity of the soul in accord with virtue; Epicurus as ataraxia, freedom from pain and disturbance; the Stoics as living according to nature; Kant warned it cannot ground morality; Mill tied it to utility."
al phil:notion:bonheur wp:Happiness
ln phil:notion:bonheur phil:philosophy sys:part_of
ln phil:notion:bonheur phil:field:ethics thesaurus:related
ln phil:notion:bonheur phil:thinker:aristotle thesaurus:related
ln phil:notion:bonheur phil:thinker:epicurus thesaurus:related
ln phil:notion:bonheur phil:thinker:mill thesaurus:related
set.add name="phil:notions" id="phil:notion:bonheur"
set.add name="phil:perspective:morale_politique" id="phil:notion:bonheur"

def "phil:notion:conscience" "Consciousness / conscience (la conscience) — the mind's presence to itself and to the world, and the moral conscience. Descartes made the thinking self (cogito) the first certainty; Locke tied personal identity to the continuity of consciousness; Kant to the unity of apperception; Husserl analysed it as always intentional; Sartre as a freedom-bearing nothingness."
al phil:notion:conscience wp:Consciousness
ln phil:notion:conscience phil:philosophy sys:part_of
ln phil:notion:conscience phil:field:philosophy_of_mind thesaurus:related
ln phil:notion:conscience phil:field:epistemology thesaurus:related
ln phil:notion:conscience phil:thinker:descartes thesaurus:related
ln phil:notion:conscience phil:thinker:locke thesaurus:related
ln phil:notion:conscience phil:thinker:sartre thesaurus:related
ln phil:notion:conscience phil:thinker:husserl thesaurus:related
set.add name="phil:notions" id="phil:notion:conscience"
set.add name="phil:perspective:connaissance" id="phil:notion:conscience"

def "phil:notion:devoir" "Duty (le devoir) — what morality obliges independently of inclination or reward. Kant grounded it in the categorical imperative — act only on a maxim you could will as universal law; the Stoics in accord with reason and one's role; utilitarians reduced it to consequences; Bergson distinguished a closed morality of pressure from an open morality of aspiration."
al phil:notion:devoir wp:Duty
ln phil:notion:devoir phil:philosophy sys:part_of
ln phil:notion:devoir phil:field:ethics thesaurus:related
ln phil:notion:devoir phil:deontology thesaurus:related
ln phil:notion:devoir phil:thinker:kant thesaurus:related
ln phil:notion:devoir phil:thinker:bergson thesaurus:related
set.add name="phil:notions" id="phil:notion:devoir"
set.add name="phil:perspective:morale_politique" id="phil:notion:devoir"

def "phil:notion:etat" "The State (l'État) — the organised political authority that claims legitimate power, and what could justify it. Hobbes founded it on a covenant to escape the war of all against all; Locke on the protection of natural rights; Rousseau on the general will; Hegel saw it as the realisation of ethical life; Marx as an instrument of class domination destined to wither away."
al phil:notion:etat wp:State_(polity)
ln phil:notion:etat phil:philosophy sys:part_of
ln phil:notion:etat phil:field:political_philosophy thesaurus:related
ln phil:notion:etat phil:thinker:hobbes thesaurus:related
ln phil:notion:etat phil:thinker:locke thesaurus:related
ln phil:notion:etat phil:thinker:rousseau thesaurus:related
ln phil:notion:etat phil:thinker:hegel thesaurus:related
ln phil:notion:etat phil:thinker:marx thesaurus:related
set.add name="phil:notions" id="phil:notion:etat"
set.add name="phil:perspective:morale_politique" id="phil:notion:etat"

def "phil:notion:inconscient" "The Unconscious (l'inconscient) — mental processes outside awareness that shape thought and action, and whether the notion is coherent. Leibniz spoke of small perceptions; Schopenhauer of a blind Will; Freud made the unconscious the core of psychic life, read through repression, dreams and slips; Sartre contested it as bad faith — a self that deceives itself."
al phil:notion:inconscient wp:Unconscious_mind
ln phil:notion:inconscient phil:philosophy sys:part_of
ln phil:notion:inconscient phil:field:philosophy_of_mind thesaurus:related
ln phil:notion:inconscient phil:thinker:freud thesaurus:related
ln phil:notion:inconscient phil:thinker:sartre thesaurus:related
ln phil:notion:inconscient phil:thinker:schopenhauer thesaurus:related
set.add name="phil:notions" id="phil:notion:inconscient"
set.add name="phil:perspective:connaissance" id="phil:notion:inconscient"

def "phil:notion:justice" "Justice (la justice) — giving each their due, and the fairness of laws and institutions. Plato defined it as each part of the soul and the city doing its own work; Aristotle distinguished distributive from corrective justice; Hobbes tied it to the covenant; Rousseau to the general will; Mill to utility."
al phil:notion:justice wp:Justice
ln phil:notion:justice phil:philosophy sys:part_of
ln phil:notion:justice phil:justice thesaurus:related
ln phil:notion:justice phil:field:political_philosophy thesaurus:related
ln phil:notion:justice phil:field:ethics thesaurus:related
ln phil:notion:justice phil:thinker:plato thesaurus:related
ln phil:notion:justice phil:thinker:aristotle thesaurus:related
ln phil:notion:justice phil:thinker:rousseau thesaurus:related
set.add name="phil:notions" id="phil:notion:justice"
set.add name="phil:perspective:morale_politique" id="phil:notion:justice"

def "phil:notion:langage" "Language (le langage) — the sign-system by which we think and communicate, and the gap between word and thing. Plato's Cratylus asked whether names are natural or conventional; Aristotle treated meaning through convention; Rousseau traced language to passion; the twentieth century tied meaning to use (Wittgenstein) and to the arbitrary sign (Saussure)."
al phil:notion:langage wp:Language
ln phil:notion:langage phil:philosophy sys:part_of
ln phil:notion:langage philosophy.language thesaurus:related
ln phil:notion:langage phil:thinker:plato thesaurus:related
ln phil:notion:langage phil:thinker:aristotle thesaurus:related
ln phil:notion:langage phil:thinker:rousseau thesaurus:related
ln phil:notion:langage phil:thinker:wittgenstein thesaurus:related
set.add name="phil:notions" id="phil:notion:langage"
set.add name="phil:perspective:existence_culture" id="phil:notion:langage"

def "phil:notion:liberte" "Freedom (la liberté) — the power to act or will otherwise, from free will to political liberty. The Stoics located freedom in inner assent, not outer circumstance; Descartes affirmed an infinite will; Spinoza denied free will and defined freedom as acting from one's own nature; Kant made it autonomy — obeying a law one gives oneself; Sartre held the human 'condemned to be free'."
al phil:notion:liberte wp:Free_will
ln phil:notion:liberte phil:philosophy sys:part_of
ln phil:notion:liberte phil:free_will thesaurus:related
ln phil:notion:liberte phil:field:ethics thesaurus:related
ln phil:notion:liberte phil:field:political_philosophy thesaurus:related
ln phil:notion:liberte phil:thinker:descartes thesaurus:related
ln phil:notion:liberte phil:thinker:spinoza thesaurus:related
ln phil:notion:liberte phil:thinker:kant thesaurus:related
ln phil:notion:liberte phil:thinker:sartre thesaurus:related
set.add name="phil:notions" id="phil:notion:liberte"
set.add name="phil:perspective:morale_politique" id="phil:notion:liberte"

def "phil:notion:nature" "Nature (la nature) — the order of the given world and the 'nature' of a thing, set against art, culture and freedom. The Greeks read nature as an ordered cosmos with ends (physis); the moderns (Descartes) as matter in mathematical motion, to be mastered; Rousseau opposed a good state of nature to corrupting society; ecology now questions the nature/culture divide."
al phil:notion:nature wp:Nature
ln phil:notion:nature phil:philosophy sys:part_of
ln phil:notion:nature phil:field:philosophy_of_science thesaurus:related
ln phil:notion:nature phil:field:metaphysics thesaurus:related
ln phil:notion:nature phil:thinker:descartes thesaurus:related
ln phil:notion:nature phil:thinker:rousseau thesaurus:related
set.add name="phil:notions" id="phil:notion:nature"
set.add name="phil:perspective:existence_culture" id="phil:notion:nature"

def "phil:notion:raison" "Reason (la raison) — the faculty of principles, inference and justification, and its limits. Plato trusted reason to grasp the Forms; the rationalists (Descartes) made it the source of knowledge; the empiricists (Hume) bounded it by experience; Kant critiqued reason's own limits; Nietzsche exposed the non-rational beneath it."
al phil:notion:raison wp:Reason
ln phil:notion:raison phil:philosophy sys:part_of
ln phil:notion:raison phil:rationalism thesaurus:related
ln phil:notion:raison phil:field:epistemology thesaurus:related
ln phil:notion:raison phil:field:logic thesaurus:related
ln phil:notion:raison phil:thinker:descartes thesaurus:related
ln phil:notion:raison phil:thinker:hume thesaurus:related
ln phil:notion:raison phil:thinker:kant thesaurus:related
ln phil:notion:raison phil:thinker:nietzsche thesaurus:related
set.add name="phil:notions" id="phil:notion:raison"
set.add name="phil:perspective:connaissance" id="phil:notion:raison"

def "phil:notion:religion" "Religion (la religion) — belief, ritual and the sacred that bind a community to the transcendent, and its critique. Pascal wagered on faith beyond reason; Hume questioned miracles and the design argument; Kant reduced religion to morality within reason's limits; Feuerbach and Marx read God as a human projection; Durkheim as society worshipping itself."
al phil:notion:religion wp:Religion
ln phil:notion:religion phil:philosophy sys:part_of
ln phil:notion:religion phil:field:metaphysics thesaurus:related
ln phil:notion:religion phil:thinker:hume thesaurus:related
ln phil:notion:religion phil:thinker:kant thesaurus:related
ln phil:notion:religion phil:thinker:marx thesaurus:related
ln phil:notion:religion phil:thinker:pascal thesaurus:related
set.add name="phil:notions" id="phil:notion:religion"
set.add name="phil:perspective:existence_culture" id="phil:notion:religion"

def "phil:notion:science" "Science (la science) — systematic knowledge sought through method, and what makes it valid. Aristotle grounded it in demonstration from causes; Bacon and the moderns in experiment and induction; Hume exposed the problem of induction; Popper set falsifiability as the mark of science; Bachelard and Kuhn showed knowledge advancing by breaks and paradigm shifts."
al phil:notion:science wp:Science
ln phil:notion:science phil:philosophy sys:part_of
ln phil:notion:science phil:field:philosophy_of_science thesaurus:related
ln phil:notion:science phil:empiricism thesaurus:related
ln phil:notion:science phil:thinker:aristotle thesaurus:related
ln phil:notion:science phil:thinker:hume thesaurus:related
set.add name="phil:notions" id="phil:notion:science"
set.add name="phil:perspective:connaissance" id="phil:notion:science"

def "phil:notion:technique" "Technics (la technique) — the arts and tools by which humans transform the world, and their promise and peril. The Greeks saw technē as productive know-how below theory; Descartes made us 'masters and possessors of nature'; Marx analysed the machine and labour; Heidegger warned that modern technology 'enframes' the world as mere resource."
al phil:notion:technique wp:Technology
ln phil:notion:technique phil:philosophy sys:part_of
ln phil:notion:technique phil:field:philosophy_of_science thesaurus:related
ln phil:notion:technique phil:thinker:descartes thesaurus:related
ln phil:notion:technique phil:thinker:marx thesaurus:related
ln phil:notion:technique phil:thinker:heidegger thesaurus:related
set.add name="phil:notions" id="phil:notion:technique"
set.add name="phil:perspective:existence_culture" id="phil:notion:technique"

def "phil:notion:temps" "Time (le temps) — the passage of past, present and future, and whether it is real or of the mind. Aristotle defined it as the number of motion; Augustine found it in the soul that stretches between memory, attention and expectation; Kant made it an a priori form of intuition; Bergson opposed lived duration (durée) to clock-time."
al phil:notion:temps wp:Time
ln phil:notion:temps phil:philosophy sys:part_of
ln phil:notion:temps phil:field:metaphysics thesaurus:related
ln phil:notion:temps phil:thinker:aristotle thesaurus:related
ln phil:notion:temps phil:thinker:augustine thesaurus:related
ln phil:notion:temps phil:thinker:kant thesaurus:related
ln phil:notion:temps phil:thinker:bergson thesaurus:related
set.add name="phil:notions" id="phil:notion:temps"
set.add name="phil:perspective:connaissance" id="phil:notion:temps"

def "phil:notion:travail" "Work / Labour (le travail) — the effort by which humans produce, sustain and shape themselves; both a curse and a vocation. Locke grounded property in one's own labour; Hegel's master–slave dialectic made labour the road to self-consciousness; Marx analysed alienated labour under capital; Arendt distinguished labour, work and action."
al phil:notion:travail wp:Work_(human_activity)
ln phil:notion:travail phil:philosophy sys:part_of
ln phil:notion:travail phil:field:political_philosophy thesaurus:related
ln phil:notion:travail phil:thinker:locke thesaurus:related
ln phil:notion:travail phil:thinker:hegel thesaurus:related
ln phil:notion:travail phil:thinker:marx thesaurus:related
ln phil:notion:travail phil:thinker:arendt thesaurus:related
set.add name="phil:notions" id="phil:notion:travail"
set.add name="phil:perspective:existence_culture" id="phil:notion:travail"

def "phil:notion:verite" "Truth (la vérité) — the property of thought or speech that matches what is, and the criteria for it. Plato set truth in the Forms; Aristotle defined it as saying of what is that it is; Descartes sought it in clear and distinct ideas; the pragmatists tied it to what works; Nietzsche unmasked 'truths' as useful fictions we have forgotten are fictions."
al phil:notion:verite wp:Truth
ln phil:notion:verite phil:philosophy sys:part_of
ln phil:notion:verite phil:truth thesaurus:related
ln phil:notion:verite phil:field:epistemology thesaurus:related
ln phil:notion:verite phil:field:logic thesaurus:related
ln phil:notion:verite phil:thinker:plato thesaurus:related
ln phil:notion:verite phil:thinker:aristotle thesaurus:related
ln phil:notion:verite phil:thinker:descartes thesaurus:related
ln phil:notion:verite phil:thinker:nietzsche thesaurus:related
set.add name="phil:notions" id="phil:notion:verite"
set.add name="phil:perspective:connaissance" id="phil:notion:verite"
