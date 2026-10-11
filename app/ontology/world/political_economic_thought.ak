# Akasha ontology (world pack) — political & economic thought.
# The schools of political and economic ideas, tied to thinkers (person:),
# phil:field:political_philosophy and hist:period. A-tier.

def "polthought:school" "A tradition of political thought (政治思想)."
def "polthought:classical_republicanism" "Civic virtue and the mixed constitution (Plato, Aristotle, Cicero)."
ln polthought:classical_republicanism polthought:school thesaurus:related
ln polthought:classical_republicanism person:aristotle_p thesaurus:related
ln polthought:classical_republicanism person:plato thesaurus:related
def "polthought:social_contract" "Government by the consent of the governed (Hobbes, Locke, Rousseau)."
ln polthought:social_contract polthought:school thesaurus:related
ln polthought:social_contract law:concept:social_contract thesaurus:related
ln polthought:social_contract person:locke thesaurus:related
ln polthought:social_contract phil:field:political_philosophy thesaurus:related
def "polthought:liberalism" "Individual liberty, rights and limited government."
ln polthought:liberalism polthought:school thesaurus:related
ln polthought:liberalism person:locke thesaurus:related
ln polthought:liberalism person:mill thesaurus:related
ln polthought:liberalism econ:market thesaurus:related
def "polthought:conservatism" "Tradition, order and gradual change (Burke)."
ln polthought:conservatism polthought:school thesaurus:related
def "polthought:socialism" "Collective ownership and social equality."
ln polthought:socialism polthought:school thesaurus:related
def "polthought:communism" "Marx's classless, stateless society after revolution."
ln polthought:communism polthought:school thesaurus:related
ln polthought:communism person:marx thesaurus:related
ln polthought:communism hist:event:russian_revolution thesaurus:related
def "polthought:anarchism" "The rejection of the coercive state."
ln polthought:anarchism polthought:school thesaurus:related
def "polthought:nationalism" "The nation as the primary political community."
ln polthought:nationalism polthought:school thesaurus:related
def "polthought:liberal_democracy" "Representative government with rights and rule of law."
ln polthought:liberal_democracy polthought:school thesaurus:related
ln polthought:liberal_democracy law:concept:separation_of_powers thesaurus:related
ln polthought:liberal_democracy hist:event:french_revolution thesaurus:related
def "polthought:fascism" "Authoritarian ultranationalism — the 20th century's dark turn."
ln polthought:fascism polthought:school thesaurus:related
def "polthought:feminist_theory" "The political analysis of gender and patriarchy."
ln polthought:feminist_theory polthought:school thesaurus:related
ln polthought:feminist_theory person:mary_wollstonecraft thesaurus:related
ln polthought:feminist_theory socio:inequality thesaurus:related

# ── economic thought ──
def "econ:school" "A school of economic thought (経済学派)."
def "econ:school:mercantilism" "Wealth as bullion, secured by trade surplus and empire (16th–18th c.)."
ln econ:school:mercantilism econ:school thesaurus:related
def "econ:school:physiocracy" "Land and agriculture as the source of all wealth."
ln econ:school:physiocracy econ:school thesaurus:related
def "econ:school:classical_economics" "Adam Smith's free markets and the invisible hand."
ln econ:school:classical_economics econ:school thesaurus:related
ln econ:school:classical_economics econ:market thesaurus:related
ln econ:school:classical_economics phil:school:empiricism thesaurus:related
def "econ:school:marxist_economics" "Labour value, surplus and the critique of capital."
ln econ:school:marxist_economics econ:school thesaurus:related
ln econ:school:marxist_economics person:marx thesaurus:related
ln econ:school:marxist_economics polthought:communism thesaurus:related
def "econ:school:neoclassical" "Marginal utility, supply-demand equilibrium and rational agents."
ln econ:school:neoclassical econ:school thesaurus:related
ln econ:school:neoclassical econ:marginal_utility thesaurus:related
ln econ:school:neoclassical econ:equilibrium_price thesaurus:related
def "econ:school:keynesian" "Demand management and state action against depression."
ln econ:school:keynesian econ:school thesaurus:related
ln econ:school:keynesian econ:keynesian_economics thesaurus:related
ln econ:school:keynesian econ:fiscal_policy thesaurus:related
def "econ:school:monetarist" "Control of the money supply as the key to stability."
ln econ:school:monetarist econ:school thesaurus:related
def "econ:school:behavioral" "Economics informed by real, biased human psychology."
ln econ:school:behavioral econ:school thesaurus:related
ln econ:school:behavioral econ:behavioral_economics thesaurus:related
ln econ:school:behavioral psy:cognitive_bias thesaurus:related

# ── founding economists ──
def "person:adam_smith" "The father of modern economics — the Wealth of Nations and the invisible hand."
ln person:adam_smith person:figure thesaurus:related
ln person:adam_smith person:field:economics person:worked_in
ln person:adam_smith econ:school:classical_economics person:belongs_to_school
ln person:adam_smith hist:period:enlightenment person:active_in
ln person:adam_smith geo:country:GBR person:from_country
def "person:keynes" "The economist whose demand management reshaped 20th-century policy."
ln person:keynes person:figure thesaurus:related
ln person:keynes person:field:economics person:worked_in
ln person:keynes econ:school:keynesian person:belongs_to_school
ln person:keynes hist:period:world_wars_era person:active_in
ln person:keynes geo:country:GBR person:from_country
