# Akasha ontology (world pack) — history of science & technology.
# The genealogy of discovery & invention: each keyed to WHEN (hist:period:),
# WHO (person:) and WHICH field, and bridged to the science/tech domains it
# founded (electron:/mecheng:/life:/matsci:…). (Research-level → C.) A-tier.

def "sci_hist:advance" "A landmark scientific discovery or technological invention (発見/発明)."
# ── advances → period, discoverer, field/domain ──
def "sci_hist:agriculture_inv" "The domestication of plants and animals — the invention that made civilization possible."
ln sci_hist:agriculture_inv sci_hist:advance thesaurus:related
ln sci_hist:agriculture_inv hist:period:neolithic sci_hist:achieved_in
ln sci_hist:agriculture_inv agron:agronomy thesaurus:related
ln sci_hist:agriculture_inv hist:event:neolithic_revolution thesaurus:related
def "sci_hist:writing_inv" "The invention of writing in Sumer and Egypt — recording language for the first time."
ln sci_hist:writing_inv sci_hist:advance thesaurus:related
ln sci_hist:writing_inv hist:period:bronze_age sci_hist:achieved_in
ln sci_hist:writing_inv epig:cuneiform thesaurus:related
ln sci_hist:writing_inv hist:event:invention_of_writing thesaurus:related
def "sci_hist:the_wheel" "The wheel and axle — transport, pottery and machines."
ln sci_hist:the_wheel sci_hist:advance thesaurus:related
ln sci_hist:the_wheel hist:period:bronze_age sci_hist:achieved_in
ln sci_hist:the_wheel mecheng:machine_design thesaurus:related
def "sci_hist:iron_smelting" "Iron metallurgy — cheaper, stronger tools and weapons than bronze."
ln sci_hist:iron_smelting sci_hist:advance thesaurus:related
ln sci_hist:iron_smelting hist:period:iron_age sci_hist:achieved_in
ln sci_hist:iron_smelting matsci:metal thesaurus:related
ln sci_hist:iron_smelting resource:smelting thesaurus:related
def "sci_hist:geometry_inv" "Euclid's axiomatic geometry — the model of deductive proof."
ln sci_hist:geometry_inv sci_hist:advance thesaurus:related
ln sci_hist:geometry_inv hist:period:classical_antiquity sci_hist:achieved_in
ln sci_hist:geometry_inv person:euclid sci_hist:discovered_by
ln sci_hist:geometry_inv math:geometry thesaurus:related
def "sci_hist:archimedes_principle" "Buoyancy, levers and the screw — the birth of physics and engineering."
ln sci_hist:archimedes_principle sci_hist:advance thesaurus:related
ln sci_hist:archimedes_principle hist:period:classical_antiquity sci_hist:achieved_in
ln sci_hist:archimedes_principle person:archimedes sci_hist:discovered_by
ln sci_hist:archimedes_principle mecheng:statics thesaurus:related
def "sci_hist:papermaking" "Cai Lun's paper — cheap writing that spread learning across the world."
ln sci_hist:papermaking sci_hist:advance thesaurus:related
ln sci_hist:papermaking hist:period:classical_antiquity sci_hist:achieved_in
ln sci_hist:papermaking matsci:polymer thesaurus:related
def "sci_hist:zero_and_place_value" "The Indian decimal place-value system and zero — the foundation of arithmetic."
ln sci_hist:zero_and_place_value sci_hist:advance thesaurus:related
ln sci_hist:zero_and_place_value hist:period:late_antiquity sci_hist:achieved_in
ln sci_hist:zero_and_place_value person:aryabhata sci_hist:discovered_by
ln sci_hist:zero_and_place_value math:arithmetic thesaurus:related
def "sci_hist:algebra_inv" "Al-Khwarizmi's algebra — solving the unknown, and the word 'algorithm'."
ln sci_hist:algebra_inv sci_hist:advance thesaurus:related
ln sci_hist:algebra_inv hist:period:early_middle_ages sci_hist:achieved_in
ln sci_hist:algebra_inv person:al_khwarizmi sci_hist:discovered_by
ln sci_hist:algebra_inv math:algebra thesaurus:related
ln sci_hist:algebra_inv cs:algorithm thesaurus:related
def "sci_hist:optics_inv" "Alhazen's experimental optics — light, vision and the scientific method."
ln sci_hist:optics_inv sci_hist:advance thesaurus:related
ln sci_hist:optics_inv hist:period:high_middle_ages sci_hist:achieved_in
ln sci_hist:optics_inv person:alhazen sci_hist:discovered_by
ln sci_hist:optics_inv bme:medical_imaging thesaurus:related
def "sci_hist:gunpowder" "The Chinese invention of gunpowder — fireworks, then the transformation of war."
ln sci_hist:gunpowder sci_hist:advance thesaurus:related
ln sci_hist:gunpowder hist:period:high_middle_ages sci_hist:achieved_in
ln sci_hist:gunpowder war:war thesaurus:related
ln sci_hist:gunpowder chemeng:reaction_engineering thesaurus:related
def "sci_hist:magnetic_compass" "The Chinese compass — enabling the age of oceanic navigation."
ln sci_hist:magnetic_compass sci_hist:advance thesaurus:related
ln sci_hist:magnetic_compass hist:period:high_middle_ages sci_hist:achieved_in
ln sci_hist:magnetic_compass geog:cartography thesaurus:related
ln sci_hist:magnetic_compass eleceng:electromagnetism thesaurus:related
def "sci_hist:printing_press" "Gutenberg's movable type (c.1440) — mass literacy and the Reformation."
ln sci_hist:printing_press sci_hist:advance thesaurus:related
ln sci_hist:printing_press hist:period:renaissance sci_hist:achieved_in
ln sci_hist:printing_press hist:event:protestant_reformation thesaurus:related
ln sci_hist:printing_press lib:cataloging thesaurus:related
def "sci_hist:heliocentrism" "Copernicus's sun-centred cosmos — dethroning the earth."
ln sci_hist:heliocentrism sci_hist:advance thesaurus:related
ln sci_hist:heliocentrism hist:period:scientific_revolution sci_hist:achieved_in
ln sci_hist:heliocentrism person:copernicus sci_hist:discovered_by
ln sci_hist:heliocentrism astrophys:cosmology thesaurus:related
def "sci_hist:telescope_inv" "Galileo's telescope turned to the heavens — moons, phases and a new sky."
ln sci_hist:telescope_inv sci_hist:advance thesaurus:related
ln sci_hist:telescope_inv hist:period:scientific_revolution sci_hist:achieved_in
ln sci_hist:telescope_inv person:galileo sci_hist:discovered_by
ln sci_hist:telescope_inv astrophys:orbital_mechanics thesaurus:related
def "sci_hist:blood_circulation" "Harvey's discovery that the heart pumps blood in a circuit."
ln sci_hist:blood_circulation sci_hist:advance thesaurus:related
ln sci_hist:blood_circulation hist:period:scientific_revolution sci_hist:achieved_in
ln sci_hist:blood_circulation med:basic:physiology thesaurus:related
ln sci_hist:blood_circulation bme:ecg thesaurus:related
def "sci_hist:laws_of_motion" "Newton's laws and universal gravitation — the clockwork cosmos."
ln sci_hist:laws_of_motion sci_hist:advance thesaurus:related
ln sci_hist:laws_of_motion hist:period:scientific_revolution sci_hist:achieved_in
ln sci_hist:laws_of_motion person:newton sci_hist:discovered_by
ln sci_hist:laws_of_motion mecheng:dynamics thesaurus:related
ln sci_hist:laws_of_motion astrophys:gravity thesaurus:related
def "sci_hist:calculus_inv" "Newton and Leibniz's calculus — the mathematics of change."
ln sci_hist:calculus_inv sci_hist:advance thesaurus:related
ln sci_hist:calculus_inv hist:period:scientific_revolution sci_hist:achieved_in
ln sci_hist:calculus_inv person:newton sci_hist:discovered_by
ln sci_hist:calculus_inv math:calculus thesaurus:related
def "sci_hist:steam_engine" "Watt's steam engine — the prime mover of the Industrial Revolution."
ln sci_hist:steam_engine sci_hist:advance thesaurus:related
ln sci_hist:steam_engine hist:period:industrial_revolution sci_hist:achieved_in
ln sci_hist:steam_engine mecheng:thermodynamics thesaurus:related
ln sci_hist:steam_engine hist:event:industrial_revolution thesaurus:related
def "sci_hist:vaccination" "Jenner's smallpox vaccine — the conquest of infectious disease begins."
ln sci_hist:vaccination sci_hist:advance thesaurus:related
ln sci_hist:vaccination hist:period:industrial_revolution sci_hist:achieved_in
ln sci_hist:vaccination life:immunity thesaurus:related
ln sci_hist:vaccination med:specialty:public_health_medicine thesaurus:related
def "sci_hist:electric_battery" "Volta's battery and Faraday's induction — harnessing electricity."
ln sci_hist:electric_battery sci_hist:advance thesaurus:related
ln sci_hist:electric_battery hist:period:industrial_revolution sci_hist:achieved_in
ln sci_hist:electric_battery eleceng:circuit thesaurus:related
ln sci_hist:electric_battery eleceng:generator thesaurus:related
def "sci_hist:electromagnetism_theory" "Maxwell's equations — unifying electricity, magnetism and light."
ln sci_hist:electromagnetism_theory sci_hist:advance thesaurus:related
ln sci_hist:electromagnetism_theory hist:period:modern_era sci_hist:achieved_in
ln sci_hist:electromagnetism_theory eleceng:electromagnetism thesaurus:related
ln sci_hist:electromagnetism_theory electron:signal_processing thesaurus:related
def "sci_hist:germ_theory" "Pasteur and Koch's germ theory — disease has microbial causes."
ln sci_hist:germ_theory sci_hist:advance thesaurus:related
ln sci_hist:germ_theory hist:period:modern_era sci_hist:achieved_in
ln sci_hist:germ_theory person:pasteur sci_hist:discovered_by
ln sci_hist:germ_theory life:bacteria thesaurus:related
ln sci_hist:germ_theory foodsafe:pathogen thesaurus:related
def "sci_hist:periodic_table" "Mendeleev's periodic table — order and prediction in chemistry."
ln sci_hist:periodic_table sci_hist:advance thesaurus:related
ln sci_hist:periodic_table hist:period:modern_era sci_hist:achieved_in
ln sci_hist:periodic_table chemeng:reaction_engineering thesaurus:related
def "sci_hist:evolution_theory" "Darwin's natural selection — the unifying theory of life."
ln sci_hist:evolution_theory sci_hist:advance thesaurus:related
ln sci_hist:evolution_theory hist:period:modern_era sci_hist:achieved_in
ln sci_hist:evolution_theory person:darwin sci_hist:discovered_by
ln sci_hist:evolution_theory life:evolution thesaurus:related
ln sci_hist:evolution_theory life:natural_selection thesaurus:related
def "sci_hist:genetics_inv" "Mendel's laws of inheritance — the birth of genetics."
ln sci_hist:genetics_inv sci_hist:advance thesaurus:related
ln sci_hist:genetics_inv hist:period:modern_era sci_hist:achieved_in
ln sci_hist:genetics_inv person:mendel sci_hist:discovered_by
ln sci_hist:genetics_inv life:genetics thesaurus:related
ln sci_hist:genetics_inv life:heredity thesaurus:related
def "sci_hist:telephone_inv" "Bell's telephone — the human voice across distance."
ln sci_hist:telephone_inv sci_hist:advance thesaurus:related
ln sci_hist:telephone_inv hist:period:modern_era sci_hist:achieved_in
ln sci_hist:telephone_inv appliance:telephone thesaurus:related
ln sci_hist:telephone_inv electron:signal_processing thesaurus:related
def "sci_hist:radioactivity_inv" "The Curies' radioactivity — a new physics of the atom."
ln sci_hist:radioactivity_inv sci_hist:advance thesaurus:related
ln sci_hist:radioactivity_inv hist:period:modern_era sci_hist:achieved_in
ln sci_hist:radioactivity_inv person:marie_curie sci_hist:discovered_by
ln sci_hist:radioactivity_inv astrophys:nuclear_fusion thesaurus:related
ln sci_hist:radioactivity_inv bme:medical_imaging thesaurus:related
def "sci_hist:relativity" "Einstein's relativity — space, time and gravity remade."
ln sci_hist:relativity sci_hist:advance thesaurus:related
ln sci_hist:relativity hist:period:world_wars_era sci_hist:achieved_in
ln sci_hist:relativity person:einstein sci_hist:discovered_by
ln sci_hist:relativity astrophys:gravity thesaurus:related
ln sci_hist:relativity astrophys:cosmology thesaurus:related
def "sci_hist:quantum_mechanics" "Planck, Bohr and Heisenberg's quantum theory — the strange world of the atom."
ln sci_hist:quantum_mechanics sci_hist:advance thesaurus:related
ln sci_hist:quantum_mechanics hist:period:world_wars_era sci_hist:achieved_in
ln sci_hist:quantum_mechanics electron:semiconductor thesaurus:related
ln sci_hist:quantum_mechanics cs:information_theory thesaurus:related
def "sci_hist:penicillin" "Fleming's antibiotic — the age of curable bacterial infection."
ln sci_hist:penicillin sci_hist:advance thesaurus:related
ln sci_hist:penicillin hist:period:world_wars_era sci_hist:achieved_in
ln sci_hist:penicillin life:bacteria thesaurus:related
ln sci_hist:penicillin med:medicine thesaurus:related
def "sci_hist:powered_flight" "The Wright brothers' aeroplane — humanity takes to the air."
ln sci_hist:powered_flight sci_hist:advance thesaurus:related
ln sci_hist:powered_flight hist:period:modern_era sci_hist:achieved_in
ln sci_hist:powered_flight mecheng:fluid_mechanics thesaurus:related
def "sci_hist:computer_inv" "Turing and von Neumann's computer — the universal machine."
ln sci_hist:computer_inv sci_hist:advance thesaurus:related
ln sci_hist:computer_inv hist:period:world_wars_era sci_hist:achieved_in
ln sci_hist:computer_inv person:turing sci_hist:discovered_by
ln sci_hist:computer_inv cs:turing_machine thesaurus:related
ln sci_hist:computer_inv electron:microprocessor thesaurus:related
def "sci_hist:dna_structure" "Watson, Crick and Franklin's double helix — the code of life read."
ln sci_hist:dna_structure sci_hist:advance thesaurus:related
ln sci_hist:dna_structure hist:period:cold_war sci_hist:achieved_in
ln sci_hist:dna_structure life:dna thesaurus:related
ln sci_hist:dna_structure life:molecular_biology thesaurus:related
def "sci_hist:transistor" "The transistor — the atom of the digital age."
ln sci_hist:transistor sci_hist:advance thesaurus:related
ln sci_hist:transistor hist:period:cold_war sci_hist:achieved_in
ln sci_hist:transistor electron:transistor thesaurus:related
ln sci_hist:transistor electron:integrated_circuit thesaurus:related
def "sci_hist:internet_inv" "The internet and the Web — a networked humanity."
ln sci_hist:internet_inv sci_hist:advance thesaurus:related
ln sci_hist:internet_inv hist:period:information_age sci_hist:achieved_in
ln sci_hist:internet_inv cs:cs thesaurus:related
ln sci_hist:internet_inv dh:knowledge_graph thesaurus:related
ln sci_hist:internet_inv sys:network thesaurus:related
