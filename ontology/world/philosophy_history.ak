# Akasha ontology (world pack) — philosophy & intellectual history.
# East & West schools (phil:school:*) and their thinkers (person:*), tied to
# phil:field branches, era/period and quotes. (Research-level → C.) A-tier.

def "phil:school" "A philosophical school or movement (学派)."
def "phil:school:presocratic" "The first Greek philosophers seeking the arché of nature (Thales, Heraclitus)."
ln phil:school:presocratic phil:school thesaurus:related
def "phil:school:platonism" "Plato's philosophy of eternal Forms behind the changing world."
ln phil:school:platonism phil:school thesaurus:related
def "phil:school:aristotelianism" "Aristotle's empirical, logical philosophy of substance and purpose."
ln phil:school:aristotelianism phil:school thesaurus:related
def "phil:school:stoicism" "Virtue through reason and acceptance of what we cannot control."
ln phil:school:stoicism phil:school thesaurus:related
def "phil:school:epicureanism" "The good life as tranquil pleasure and freedom from fear."
ln phil:school:epicureanism phil:school thesaurus:related
def "phil:school:skepticism" "The suspension of judgement where certainty is impossible."
ln phil:school:skepticism phil:school thesaurus:related
def "phil:school:neoplatonism" "Plotinus's mystical hierarchy emanating from the One."
ln phil:school:neoplatonism phil:school thesaurus:related
def "phil:school:scholasticism" "The medieval synthesis of faith and Aristotelian reason."
ln phil:school:scholasticism phil:school thesaurus:related
def "phil:school:rationalism" "Reason as the primary source of knowledge (Descartes, Spinoza, Leibniz)."
ln phil:school:rationalism phil:school thesaurus:related
def "phil:school:empiricism" "Knowledge from sensory experience (Locke, Berkeley, Hume)."
ln phil:school:empiricism phil:school thesaurus:related
def "phil:school:german_idealism" "Kant to Hegel — mind's role in constituting reality."
ln phil:school:german_idealism phil:school thesaurus:related
def "phil:school:utilitarianism" "The right act maximizes overall happiness (Bentham, Mill)."
ln phil:school:utilitarianism phil:school thesaurus:related
def "phil:school:marxism" "Historical materialism and the critique of capital."
ln phil:school:marxism phil:school thesaurus:related
def "phil:school:existentialism" "Existence precedes essence; meaning is freely made."
ln phil:school:existentialism phil:school thesaurus:related
def "phil:school:phenomenology" "The study of the structures of lived experience (Husserl)."
ln phil:school:phenomenology phil:school thesaurus:related
def "phil:school:pragmatism" "Truth as what works in practice (Peirce, James, Dewey)."
ln phil:school:pragmatism phil:school thesaurus:related
def "phil:school:analytic_philosophy" "Clarity through logic and language (Frege, Russell, Wittgenstein)."
ln phil:school:analytic_philosophy phil:school thesaurus:related
def "phil:school:confucianism" "Ethics of ritual, benevolence and good order (Confucius, Mencius)."
ln phil:school:confucianism phil:school thesaurus:related
def "phil:school:neo_confucianism" "The Song-Ming metaphysical revival (Zhu Xi, Wang Yangming)."
ln phil:school:neo_confucianism phil:school thesaurus:related
def "phil:school:taoism" "Harmony with the spontaneous Way (Laozi, Zhuangzi)."
ln phil:school:taoism phil:school thesaurus:related
def "phil:school:legalism" "Rule by strict law and state power (Han Feizi)."
ln phil:school:legalism phil:school thesaurus:related
def "phil:school:mohism" "Impartial care and utility against Confucian partiality."
ln phil:school:mohism phil:school thesaurus:related
def "phil:school:buddhist_philosophy" "Analysis of suffering, impermanence and no-self."
ln phil:school:buddhist_philosophy phil:school thesaurus:related
def "phil:school:vedanta" "The Hindu philosophy of Brahman and the self (Shankara)."
ln phil:school:vedanta phil:school thesaurus:related
def "phil:school:nyaya" "The Indian school of logic and epistemology."
ln phil:school:nyaya phil:school thesaurus:related
def "phil:school:zen" "Buddhism of direct experience beyond words (Chan/Zen)."
ln phil:school:zen phil:school thesaurus:related

# ── thinkers → school, era, country, period ──
def "person:plato" "The Athenian founder of the Academy and the theory of Forms."
ln person:plato person:figure thesaurus:related
ln person:plato phil:school:platonism person:belongs_to_school
ln person:plato person:era:ancient person:lived_in
ln person:plato person:field:philosophy person:worked_in
ln person:plato geo:country:GRC person:from_country
ln person:plato hist:period:classical_antiquity person:active_in
def "person:aristotle_p" "Plato's pupil, the systematizer of logic, ethics and science."
ln person:aristotle_p person:figure thesaurus:related
ln person:aristotle_p phil:school:aristotelianism person:belongs_to_school
ln person:aristotle_p person:era:ancient person:lived_in
ln person:aristotle_p person:field:philosophy person:worked_in
ln person:aristotle_p geo:country:GRC person:from_country
ln person:aristotle_p hist:period:classical_antiquity person:active_in
def "person:epicurus" "Founder of the Garden, teacher of tranquil pleasure."
ln person:epicurus person:figure thesaurus:related
ln person:epicurus phil:school:epicureanism person:belongs_to_school
ln person:epicurus person:era:ancient person:lived_in
ln person:epicurus person:field:philosophy person:worked_in
ln person:epicurus geo:country:GRC person:from_country
ln person:epicurus hist:period:classical_antiquity person:active_in
def "person:zeno_of_citium" "Founder of Stoicism in the Athenian Stoa."
ln person:zeno_of_citium person:figure thesaurus:related
ln person:zeno_of_citium phil:school:stoicism person:belongs_to_school
ln person:zeno_of_citium person:era:ancient person:lived_in
ln person:zeno_of_citium person:field:philosophy person:worked_in
ln person:zeno_of_citium geo:country:GRC person:from_country
ln person:zeno_of_citium hist:period:classical_antiquity person:active_in
def "person:plotinus" "Founder of Neoplatonism and its mysticism of the One."
ln person:plotinus person:figure thesaurus:related
ln person:plotinus phil:school:neoplatonism person:belongs_to_school
ln person:plotinus person:era:late_antique person:lived_in
ln person:plotinus person:field:philosophy person:worked_in
ln person:plotinus geo:country:EGY person:from_country
ln person:plotinus hist:period:late_antiquity person:active_in
def "person:augustine" "The Church Father who fused Christianity with Platonism."
ln person:augustine person:figure thesaurus:related
ln person:augustine phil:school:neoplatonism person:belongs_to_school
ln person:augustine person:era:late_antique person:lived_in
ln person:augustine person:field:philosophy person:worked_in
ln person:augustine geo:country:DZA person:from_country
ln person:augustine hist:period:late_antiquity person:active_in
def "person:aquinas" "The scholastic who synthesized Aristotle with Christian theology."
ln person:aquinas person:figure thesaurus:related
ln person:aquinas phil:school:scholasticism person:belongs_to_school
ln person:aquinas person:era:medieval person:lived_in
ln person:aquinas person:field:philosophy person:worked_in
ln person:aquinas geo:country:ITA person:from_country
ln person:aquinas hist:period:high_middle_ages person:active_in
def "person:averroes" "Ibn Rushd, the great Andalusian commentator on Aristotle."
ln person:averroes person:figure thesaurus:related
ln person:averroes phil:school:aristotelianism person:belongs_to_school
ln person:averroes person:era:medieval person:lived_in
ln person:averroes person:field:philosophy person:worked_in
ln person:averroes geo:country:ESP person:from_country
ln person:averroes hist:period:high_middle_ages person:active_in
def "person:descartes_p" "The father of modern philosophy — 'I think, therefore I am'."
ln person:descartes_p person:figure thesaurus:related
ln person:descartes_p phil:school:rationalism person:belongs_to_school
ln person:descartes_p person:era:early_modern person:lived_in
ln person:descartes_p person:field:philosophy person:worked_in
ln person:descartes_p geo:country:FRA person:from_country
ln person:descartes_p hist:period:scientific_revolution person:active_in
def "person:spinoza" "The rationalist of a single divine substance, God-or-Nature."
ln person:spinoza person:figure thesaurus:related
ln person:spinoza phil:school:rationalism person:belongs_to_school
ln person:spinoza person:era:early_modern person:lived_in
ln person:spinoza person:field:philosophy person:worked_in
ln person:spinoza geo:country:NLD person:from_country
ln person:spinoza hist:period:enlightenment person:active_in
def "person:locke" "The empiricist of the blank slate and natural rights."
ln person:locke person:figure thesaurus:related
ln person:locke phil:school:empiricism person:belongs_to_school
ln person:locke person:era:enlightenment person:lived_in
ln person:locke person:field:philosophy person:worked_in
ln person:locke geo:country:GBR person:from_country
ln person:locke hist:period:enlightenment person:active_in
def "person:hume" "The skeptic who questioned causation and the self."
ln person:hume person:figure thesaurus:related
ln person:hume phil:school:empiricism person:belongs_to_school
ln person:hume person:era:enlightenment person:lived_in
ln person:hume person:field:philosophy person:worked_in
ln person:hume geo:country:GBR person:from_country
ln person:hume hist:period:enlightenment person:active_in
def "person:kant" "Who reconciled reason and experience in the Critique of Pure Reason."
ln person:kant person:figure thesaurus:related
ln person:kant phil:school:german_idealism person:belongs_to_school
ln person:kant person:era:enlightenment person:lived_in
ln person:kant person:field:philosophy person:worked_in
ln person:kant geo:country:DEU person:from_country
ln person:kant hist:period:enlightenment person:active_in
def "person:hegel" "The idealist of dialectic and the march of Spirit through history."
ln person:hegel person:figure thesaurus:related
ln person:hegel phil:school:german_idealism person:belongs_to_school
ln person:hegel person:era:romantic_era person:lived_in
ln person:hegel person:field:philosophy person:worked_in
ln person:hegel geo:country:DEU person:from_country
ln person:hegel hist:period:industrial_revolution person:active_in
def "person:mill" "The utilitarian champion of liberty and women's rights."
ln person:mill person:figure thesaurus:related
ln person:mill phil:school:utilitarianism person:belongs_to_school
ln person:mill person:era:industrial_era person:lived_in
ln person:mill person:field:philosophy person:worked_in
ln person:mill geo:country:GBR person:from_country
ln person:mill hist:period:modern_era person:active_in
def "person:marx" "The critic of capital and prophet of revolution."
ln person:marx person:figure thesaurus:related
ln person:marx phil:school:marxism person:belongs_to_school
ln person:marx person:era:industrial_era person:lived_in
ln person:marx person:field:philosophy person:worked_in
ln person:marx geo:country:DEU person:from_country
ln person:marx hist:period:industrial_revolution person:active_in
def "person:nietzsche_p" "Who proclaimed the death of God and the will to power."
ln person:nietzsche_p person:figure thesaurus:related
ln person:nietzsche_p phil:school:existentialism person:belongs_to_school
ln person:nietzsche_p person:era:industrial_era person:lived_in
ln person:nietzsche_p person:field:philosophy person:worked_in
ln person:nietzsche_p geo:country:DEU person:from_country
ln person:nietzsche_p hist:period:modern_era person:active_in
def "person:kierkegaard" "The Danish father of existentialism and the leap of faith."
ln person:kierkegaard person:figure thesaurus:related
ln person:kierkegaard phil:school:existentialism person:belongs_to_school
ln person:kierkegaard person:era:romantic_era person:lived_in
ln person:kierkegaard person:field:philosophy person:worked_in
ln person:kierkegaard geo:country:DNK person:from_country
ln person:kierkegaard hist:period:industrial_revolution person:active_in
def "person:sartre" "The existentialist of radical freedom and bad faith."
ln person:sartre person:figure thesaurus:related
ln person:sartre phil:school:existentialism person:belongs_to_school
ln person:sartre person:era:modern person:lived_in
ln person:sartre person:field:philosophy person:worked_in
ln person:sartre geo:country:FRA person:from_country
ln person:sartre hist:period:world_wars_era person:active_in
def "person:wittgenstein" "Who twice remade the philosophy of language."
ln person:wittgenstein person:figure thesaurus:related
ln person:wittgenstein phil:school:analytic_philosophy person:belongs_to_school
ln person:wittgenstein person:era:modern person:lived_in
ln person:wittgenstein person:field:philosophy person:worked_in
ln person:wittgenstein geo:country:AUT person:from_country
ln person:wittgenstein hist:period:world_wars_era person:active_in
def "person:laozi_p" "The traditional founder of Taoism and author of the Tao Te Ching."
ln person:laozi_p person:figure thesaurus:related
ln person:laozi_p phil:school:taoism person:belongs_to_school
ln person:laozi_p person:era:ancient person:lived_in
ln person:laozi_p person:field:philosophy person:worked_in
ln person:laozi_p geo:country:CHN person:from_country
ln person:laozi_p hist:period:iron_age person:active_in
def "person:zhuangzi_p" "The Taoist of the butterfly dream and spontaneous freedom."
ln person:zhuangzi_p person:figure thesaurus:related
ln person:zhuangzi_p phil:school:taoism person:belongs_to_school
ln person:zhuangzi_p person:era:ancient person:lived_in
ln person:zhuangzi_p person:field:philosophy person:worked_in
ln person:zhuangzi_p geo:country:CHN person:from_country
ln person:zhuangzi_p hist:period:classical_antiquity person:active_in
def "person:mencius" "The Confucian who held human nature to be good."
ln person:mencius person:figure thesaurus:related
ln person:mencius phil:school:confucianism person:belongs_to_school
ln person:mencius person:era:ancient person:lived_in
ln person:mencius person:field:philosophy person:worked_in
ln person:mencius geo:country:CHN person:from_country
ln person:mencius hist:period:iron_age person:active_in
def "person:zhu_xi" "The synthesizer of Neo-Confucian metaphysics."
ln person:zhu_xi person:figure thesaurus:related
ln person:zhu_xi phil:school:neo_confucianism person:belongs_to_school
ln person:zhu_xi person:era:medieval person:lived_in
ln person:zhu_xi person:field:philosophy person:worked_in
ln person:zhu_xi geo:country:CHN person:from_country
ln person:zhu_xi hist:period:high_middle_ages person:active_in
def "person:nagarjuna" "The Buddhist philosopher of emptiness (śūnyatā)."
ln person:nagarjuna person:figure thesaurus:related
ln person:nagarjuna phil:school:buddhist_philosophy person:belongs_to_school
ln person:nagarjuna person:era:late_antique person:lived_in
ln person:nagarjuna person:field:philosophy person:worked_in
ln person:nagarjuna geo:country:IND person:from_country
ln person:nagarjuna hist:period:late_antiquity person:active_in
def "person:shankara" "The founder of Advaita Vedanta, non-dualism."
ln person:shankara person:figure thesaurus:related
ln person:shankara phil:school:vedanta person:belongs_to_school
ln person:shankara person:era:medieval person:lived_in
ln person:shankara person:field:philosophy person:worked_in
ln person:shankara geo:country:IND person:from_country
ln person:shankara hist:period:early_middle_ages person:active_in
