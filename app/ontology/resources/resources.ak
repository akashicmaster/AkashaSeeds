# resources.ak
# Natural resources — energy, critical minerals, ecosystem resources
# Sources: USGS, IEA, FAO, IUCN — Public domain
#

# ─── ENERGY NAMESPACE ANCHOR ─────────────────────────────────────────────────

def "resource:energy" "Energy resources: primary sources of energy used by human civilisation; includes fossil fuels, nuclear fuels, renewables, and energy carriers."
set.add name="ontology.natural_resources" id="resource:energy"

# ─── FOSSIL FUELS ────────────────────────────────────────────────────────────

def "resource:energy:coal" "Coal: combustible sedimentary rock formed from ancient plant matter; ranked by carbon content from lowest to highest: lignite (brown coal), sub-bituminous, bituminous (thermal/coking), anthracite; primary fuel for steel and electricity generation."
ln resource:energy:coal resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:coal"

def "resource:energy:oil" "Crude petroleum: liquid hydrocarbon mixture extracted from geological formations; conventional (reservoir rock) and unconventional (tight/shale oil, oil sands/tar sands); refined into petrol, diesel, aviation fuel, plastics feedstocks."
ln resource:energy:oil resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:oil"

def "resource:energy:natural_gas" "Natural gas: fossil fuel consisting primarily of methane (CH4); conventional (reservoir traps) and unconventional (shale gas, coalbed methane, tight gas); used for heating, electricity generation, and as industrial feedstock."
ln resource:energy:natural_gas resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:natural_gas"

def "resource:energy:oil_sands" "Oil sands (tar sands): sand or sandstone saturated with highly viscous bitumen; major deposits in Alberta (Canada) and Orinoco Belt (Venezuela); requires energy-intensive extraction (mining or in-situ steam) and upgrading to synthetic crude."
ln resource:energy:oil_sands resource:energy:oil sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:oil_sands"

def "resource:energy:shale_gas" "Shale gas: natural gas trapped within fine-grained shale formations; extracted via hydraulic fracturing (fracking) and horizontal drilling; US shale revolution (~2008 onward) transformed global gas markets."
ln resource:energy:shale_gas resource:energy:natural_gas sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:shale_gas"

# ─── NUCLEAR ─────────────────────────────────────────────────────────────────

def "resource:energy:uranium" "Uranium: fissile heavy metal (primarily U-235 and U-238); primary fuel for nuclear fission reactors worldwide; mined as uranium ore then enriched; also produced as MOX (mixed oxide) from weapons stockpiles. Major producers: Kazakhstan, Canada, Australia."
ln resource:energy:uranium resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:uranium"

def "resource:energy:thorium" "Thorium: fertile radioactive metal (~3× more abundant in Earth's crust than uranium); must be converted to fissile U-233 by neutron capture; leading candidate fuel for molten salt reactors (MSRs) and advanced nuclear designs; large deposits in India, Brazil, Australia."
ln resource:energy:thorium resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:thorium"

# ─── RENEWABLES ──────────────────────────────────────────────────────────────

def "resource:energy:solar" "Solar energy: radiant energy from the Sun converted to electricity via photovoltaic (PV) cells or to heat via concentrated solar power (CSP) with mirrors/lenses; fastest-growing energy source globally; costs fallen ~90% 2010–2024."
ln resource:energy:solar resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:solar"

def "resource:energy:wind" "Wind energy: kinetic energy of moving air converted to electricity by wind turbines; onshore and offshore installations; offshore wind has higher and more consistent speeds; third-largest source of electricity in many countries."
ln resource:energy:wind resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:wind"

def "resource:energy:hydroelectric" "Hydroelectric power: potential and kinetic energy of flowing or falling water converted to electricity via turbines; largest source of renewable electricity globally (~16% of world electricity); includes run-of-river, reservoir dams, and pumped-storage hydro."
ln resource:energy:hydroelectric resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:hydroelectric"

def "resource:energy:geothermal" "Geothermal energy: heat from Earth's interior (radioactive decay + primordial heat) used for electricity generation and direct heating; most viable near tectonic boundaries; primary users: Iceland, Kenya, El Salvador, the Philippines, New Zealand."
ln resource:energy:geothermal resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:geothermal"

def "resource:energy:tidal" "Tidal energy: kinetic and potential energy of ocean tides (driven by lunar and solar gravity) harnessed by tidal stream turbines or tidal barrages; predictable but site-constrained to strong tidal currents; examples: La Rance (France), MeyGen (Scotland)."
ln resource:energy:tidal resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:tidal"

def "resource:energy:wave" "Wave energy: kinetic energy of ocean surface waves converted to electricity by wave energy converters (oscillating water columns, attenuators, point absorbers); still pre-commercial at scale; large resource along western coastlines at mid-latitudes."
ln resource:energy:wave resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:wave"

def "resource:energy:biomass" "Biomass energy: organic material (wood, crop residues, energy crops, biogas, biofuel) burned or processed for heat and electricity; carbon-neutral if sustainably managed; includes biogas (anaerobic digestion), bioethanol, biodiesel, and direct combustion."
ln resource:energy:biomass resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:biomass"

def "resource:energy:hydrogen" "Hydrogen: energy carrier (not a primary source) produced by several pathways — green (electrolysis powered by renewables, zero-emission), blue (steam methane reforming + carbon capture and storage), grey (steam methane reforming, no CCS), turquoise (methane pyrolysis, solid carbon byproduct); used in fuel cells, industry, heavy transport."
ln resource:energy:hydrogen resource:energy sys:part_of
set.add name="ontology.natural_resources" id="resource:energy:hydrogen"

# ─── MINERAL NAMESPACE ANCHOR ────────────────────────────────────────────────

def "resource:mineral" "Critical minerals: minerals designated as essential for national security, economic health, and clean energy transition, with supply chains concentrated in few countries and vulnerable to disruption; USGS 2022 list contains 50 minerals."
set.add name="ontology.natural_resources" id="resource:mineral"

# ─── BATTERY / EV MINERALS ───────────────────────────────────────────────────

def "resource:mineral:lithium" "Lithium: lightest metal; essential for lithium-ion battery cathodes and electrolytes in EVs and grid storage; also used in psychiatric medication and ceramics. Major producers: Chile (Atacama brine), Australia (hard rock), Argentina; 'Lithium Triangle' holds ~60% of global reserves."
ln resource:mineral:lithium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:lithium"

def "resource:mineral:cobalt" "Cobalt: transition metal used as cathode material (NMC, NCA chemistries) in lithium-ion batteries; also in superalloys and cutting tools. ~70% of global supply from Democratic Republic of Congo; significant human-rights concerns around artisanal mining."
ln resource:mineral:cobalt resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:cobalt"

def "resource:mineral:nickel" "Nickel: used in stainless steel (~70% of demand), EV battery cathodes (high-nickel NMC, NCA), and superalloys for jet engines; Class 1 nickel (>99.8% pure) needed for batteries. Major producers: Indonesia, Philippines, Russia."
ln resource:mineral:nickel resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:nickel"

def "resource:mineral:graphite" "Graphite: naturally occurring form of carbon; primary anode material in all lithium-ion batteries (each EV uses ~50–70 kg); also used as a moderator in nuclear reactors and in lubricants. China produces ~65% of natural graphite and dominates synthetic graphite."
ln resource:mineral:graphite resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:graphite"

def "resource:mineral:manganese" "Manganese: essential for steel production (deoxidiser and desulphuriser); increasingly used in EV battery cathodes (LMFP, high-manganese NMC). Major producers: South Africa (~36%), Australia, Gabon; reserves widely distributed but processing concentrated."
ln resource:mineral:manganese resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:manganese"

def "resource:mineral:vanadium" "Vanadium: used in high-strength low-alloy (HSLA) steels for construction and automotive; active material in vanadium redox flow batteries (VRFB) for long-duration grid storage. China produces ~57% of global supply; also produced in Russia and South Africa."
ln resource:mineral:vanadium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:vanadium"

# ─── RARE EARTH ELEMENTS ─────────────────────────────────────────────────────

def "resource:mineral:rare_earth_elements" "Rare earth elements (REEs): group of 17 metals comprising 15 lanthanides (La–Lu) plus scandium (Sc) and yttrium (Y); used in permanent magnets, phosphors, catalysts, and electronic components; despite name, not geologically rare but rarely concentrated; China produces ~60% of mined REEs and dominates processing."
ln resource:mineral:rare_earth_elements resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:rare_earth_elements"

def "resource:mineral:neodymium" "Neodymium (Nd): light rare earth; key ingredient in neodymium-iron-boron (NdFeB) permanent magnets — the strongest permanent magnets known; essential for EV motors, wind turbine generators, and hard disk drives."
ln resource:mineral:neodymium resource:mineral:rare_earth_elements sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:neodymium"

def "resource:mineral:dysprosium" "Dysprosium (Dy): heavy rare earth; added to NdFeB magnets to retain magnetic properties at high temperatures (critical for EV motors and industrial motors); supply almost entirely from China; few known substitutes."
ln resource:mineral:dysprosium resource:mineral:rare_earth_elements sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:dysprosium"

def "resource:mineral:europium" "Europium (Eu): heavy rare earth; produces the red emission in fluorescent lamps and LED phosphors; historically in CRT television red phosphors; also used in anti-counterfeiting features on euro banknotes."
ln resource:mineral:europium resource:mineral:rare_earth_elements sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:europium"

def "resource:mineral:cerium" "Cerium (Ce): most abundant rare earth; used in catalytic converters (as oxygen storage component), glass polishing powders, UV-filtering glass, and petroleum refining catalysts; also a component of mischmetal (lighter flints)."
ln resource:mineral:cerium resource:mineral:rare_earth_elements sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:cerium"

def "resource:mineral:lanthanum" "Lanthanum (La): light rare earth; used in camera and telescope lens glass (high refractive index, low dispersion), nickel-metal hydride (NiMH) batteries, and fluid catalytic cracking catalysts in oil refining."
ln resource:mineral:lanthanum resource:mineral:rare_earth_elements sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:lanthanum"

def "resource:mineral:yttrium" "Yttrium (Y): rare earth (not a lanthanide); used in LED and CRT phosphors (white LEDs), yttria-stabilised zirconia (YSZ) for thermal barrier coatings in jet engines, and targeted cancer radiotherapy (Y-90 isotope)."
ln resource:mineral:yttrium resource:mineral:rare_earth_elements sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:yttrium"

def "resource:mineral:scandium" "Scandium (Sc): rare earth; added to aluminium alloys to dramatically increase strength and weldability for aerospace frames and bicycle components; also used in solid oxide fuel cells (SOFC) electrolytes. Very limited production; byproduct of uranium and titanium mining."
ln resource:mineral:scandium resource:mineral:rare_earth_elements sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:scandium"

# ─── PLATINUM GROUP METALS ───────────────────────────────────────────────────

def "resource:mineral:platinum_group" "Platinum group metals (PGMs): six chemically related noble metals — platinum (Pt), palladium (Pd), rhodium (Rh), ruthenium (Ru), iridium (Ir), osmium (Os); exceptional catalytic, electrical, and chemical resistance properties; South Africa holds ~91% of world reserves."
ln resource:mineral:platinum_group resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:platinum_group"

def "resource:mineral:platinum" "Platinum (Pt): PGM; used in diesel catalytic converters (oxidation catalysts), hydrogen fuel cell catalysts, laboratory equipment, and jewelry. ~80% of world supply from South Africa (Bushveld Complex); highly resistant to corrosion."
ln resource:mineral:platinum resource:mineral:platinum_group sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:platinum"

def "resource:mineral:palladium" "Palladium (Pd): PGM; primary use in gasoline (petrol) catalytic converters (three-way catalysts); also in electronics, dentistry, and as a hydrogen purification membrane. Primary producers: Russia (~40%) and South Africa (~38%); price surged ~10× 2016–2022."
ln resource:mineral:palladium resource:mineral:platinum_group sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:palladium"

def "resource:mineral:rhodium" "Rhodium (Rh): rarest and most expensive PGM; essential in three-way catalytic converters for NOx reduction; no known substitutes for this function; supply dominated by South Africa; extreme price volatility (reached $29,800/troy oz in 2021)."
ln resource:mineral:rhodium resource:mineral:platinum_group sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:rhodium"

# ─── SEMICONDUCTOR / ELECTRONICS MINERALS ───────────────────────────────────

def "resource:mineral:gallium" "Gallium (Ga): soft metal; critical semiconductor substrate (gallium arsenide, gallium nitride) for RF chips, LEDs, laser diodes, and high-efficiency solar cells; almost exclusively a byproduct of aluminium and zinc smelting. China produces ~80% of refined gallium; imposed export controls in 2023."
ln resource:mineral:gallium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:gallium"

def "resource:mineral:germanium" "Germanium (Ge): metalloid; used in fibre optic cables (as GeO2 dopant), infrared optics (night-vision, thermal imaging), and thin-film solar cells (multi-junction); byproduct of zinc smelting and coal combustion residues. China produces ~60%; imposed export controls in 2023."
ln resource:mineral:germanium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:germanium"

def "resource:mineral:indium" "Indium (In): soft post-transition metal; primary use as indium tin oxide (ITO) — transparent conductive coating for LCD displays, touchscreens, and thin-film solar cells; almost entirely a byproduct of zinc smelting. China is dominant producer."
ln resource:mineral:indium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:indium"

def "resource:mineral:tellurium" "Tellurium (Te): metalloid; key component of cadmium telluride (CdTe) thin-film photovoltaic panels (used by First Solar) and thermoelectric devices; one of the rarest stable elements in Earth's crust (~1 ppb); almost entirely a byproduct of copper anode slimes."
ln resource:mineral:tellurium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:tellurium"

def "resource:mineral:arsenic" "Arsenic (As): metalloid; used in gallium arsenide (GaAs) semiconductors for high-frequency electronics, and historically in wood preservatives (CCA); byproduct of copper and lead smelting. Highly toxic; regulated substance in most jurisdictions."
ln resource:mineral:arsenic resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:arsenic"

# ─── REFRACTORY / STRUCTURAL METALS ─────────────────────────────────────────

def "resource:mineral:tungsten" "Tungsten (W): highest melting point of all metals (3,422 °C); used in cutting tools (WC cemented carbide), electrical filaments, armour-piercing projectiles, and radiation shielding. China produces ~80% of global supply; significant strategic concern."
ln resource:mineral:tungsten resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:tungsten"

def "resource:mineral:chromium" "Chromium (Cr): hard metal; primary use in stainless steel (minimum 10.5% Cr) and hard chrome plating; also in refractory bricks and pigments. Kazakhstan and South Africa hold ~80% of chromite reserves; South Africa dominates ferrochrome production."
ln resource:mineral:chromium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:chromium"

def "resource:mineral:titanium" "Titanium (Ti): strong, lightweight, corrosion-resistant metal; structural metal in aerospace (airframes, engines), medical implants, and marine applications; also used as TiO2 white pigment (largest use by mass). Australia and South Africa are major ilmenite/rutile producers."
ln resource:mineral:titanium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:titanium"

def "resource:mineral:hafnium" "Hafnium (Hf): refractory metal chemically similar to zirconium (always co-occurs); used in nuclear reactor control rods (high neutron absorption), high-k gate dielectric in advanced CMOS transistors (HfO2), and superalloy turbine blades. Byproduct of zirconium processing."
ln resource:mineral:hafnium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:hafnium"

def "resource:mineral:niobium" "Niobium (Nb): refractory metal; primary use as microalloying addition to high-strength low-alloy (HSLA) steels for pipelines and automotive; also used in superconducting magnets (NbTi, Nb3Sn for MRI and particle accelerators). Brazil produces ~92% of global supply (CBMM, Araxá)."
ln resource:mineral:niobium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:niobium"

def "resource:mineral:tantalum" "Tantalum (Ta): refractory metal; primary use in miniature electrolytic capacitors for smartphones, laptops, and medical devices; also in surgical implants and chemical processing equipment (high acid resistance). DRC and Rwanda are primary producers; historically linked to conflict minerals."
ln resource:mineral:tantalum resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:tantalum"

def "resource:mineral:rhenium" "Rhenium (Re): highest boiling point of all elements; critical additive in single-crystal nickel superalloy turbine blades for jet engines and gas turbines (improves creep resistance); almost entirely a byproduct of molybdenum smelting from porphyry copper deposits. Chile is primary producer."
ln resource:mineral:rhenium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:rhenium"

def "resource:mineral:zirconium" "Zirconium (Zr): corrosion-resistant metal; primary use in nuclear fuel rod cladding (transparent to neutrons); also in high-performance ceramics, refractories, and dental crowns (zirconia). Australia and South Africa are primary zircon sand producers."
ln resource:mineral:zirconium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:zirconium"

def "resource:mineral:beryllium" "Beryllium (Be): lightest structural metal; used in aerospace alloys (beryllium-copper, beryllium-aluminium), nuclear moderator and reflector (transparent to X-rays and neutrons), X-ray windows, and gyroscopes. United States is dominant producer; highly toxic if inhaled as dust."
ln resource:mineral:beryllium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:beryllium"

# ─── SPECIALIST / TECHNOLOGY MINERALS ───────────────────────────────────────

def "resource:mineral:cesium" "Cesium (Cs): alkali metal; primary use in cesium atomic clocks (primary frequency standard underpinning GPS, internet timing, and financial transactions); also in cesium formate drilling fluids for high-pressure oil and gas wells. Produced mainly from pollucite in Canada and Zimbabwe."
ln resource:mineral:cesium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:cesium"

def "resource:mineral:rubidium" "Rubidium (Rb): alkali metal; used in rubidium atomic clocks (secondary frequency standard), specialty glass for fibre optics, and research applications; byproduct of lithium processing from lepidolite. No large-scale primary mines."
ln resource:mineral:rubidium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:rubidium"

def "resource:mineral:antimony" "Antimony (Sb): metalloid; primary use as flame retardant (antimony trioxide synergist in plastics and textiles) and in lead-acid battery plates; also in semiconductors and pigments. China produces ~50% of global supply; export restricted."
ln resource:mineral:antimony resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:antimony"

def "resource:mineral:bismuth" "Bismuth (Bi): post-transition metal; used in pharmaceuticals (bismuth subsalicylate — Pepto-Bismol), lead-free solders and plumbing fittings, cosmetics, and pigments; low toxicity compared to lead. China is primary producer; largely a byproduct of lead refining."
ln resource:mineral:bismuth resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:bismuth"

def "resource:mineral:tin" "Tin (Sn): soft metal; primary uses in solder (electronics manufacturing, ~50% of demand), tin-plated steel cans, and bronze (Cu-Sn alloy); increasingly used in indium-tin oxide. China is largest producer; also significant production in Indonesia and Myanmar."
ln resource:mineral:tin resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:tin"

def "resource:mineral:zinc" "Zinc (Zn): used primarily for galvanising steel against corrosion (~60% of demand), in brass (Cu-Zn), die casting, and as a dietary supplement; also an important host rock for indium, germanium, and gallium. China is dominant producer; also Australia, Peru, India."
ln resource:mineral:zinc resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:zinc"

def "resource:mineral:magnesium" "Magnesium (Mg): lightest structural metal; used in lightweight alloys for automotive and aerospace (Mg-Al), refractory bricks for steel furnaces, and as a desulphurising agent in steel. China produces ~85% of global refined magnesium."
ln resource:mineral:magnesium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:magnesium"

def "resource:mineral:barite" "Barite (barium sulphate, BaSO4): high-density mineral (SG ~4.5); primary use as weighting agent in oil and gas drilling fluids (keeps borehole pressure controlled); also in X-ray shielding, paints, and rubber. China and India are primary producers."
ln resource:mineral:barite resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:barite"

def "resource:mineral:fluorspar" "Fluorspar (fluorite, CaF2): primary industrial source of fluorine; used to produce hydrofluoric acid (HF) for aluminium smelting flux, steel refining, refrigerants (HFCs), and fluoropolymers (PTFE/Teflon). China and Mexico are leading producers."
ln resource:mineral:fluorspar resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:fluorspar"

def "resource:mineral:potash" "Potash: potassium-bearing evaporite minerals (primarily sylvite, KCl) used as potassium fertilizer — one of the three macronutrients (N-P-K) essential for crop growth; Saskatchewan (Canada) holds the world's largest deposits. Canada, Russia, and Belarus historically dominant exporters."
ln resource:mineral:potash resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:potash"

def "resource:mineral:helium" "Helium (He): noble gas; used as cryogen to cool MRI superconducting magnets, quantum computing systems, and particle accelerators (liquid helium at 4 K); also for pressurising rocket fuel tanks, welding shield gas, and lifting gas. United States and Qatar are primary producers; non-renewable on human timescales (escapes to space)."
ln resource:mineral:helium resource:mineral sys:part_of
set.add name="ontology.natural_resources" id="resource:mineral:helium"

# ─── ECOSYSTEM RESOURCES ─────────────────────────────────────────────────────

def "resource:ecosystem" "Ecosystem resources: natural systems and biotic/abiotic components that provide goods and services essential to human civilisation and life on Earth; includes freshwater, forests, oceans, soil, fisheries, and timber."
set.add name="ontology.natural_resources" id="resource:ecosystem"

def "resource:ecosystem:freshwater" "Freshwater: water with low dissolved salt content; ~2.5% of Earth's total water, of which ~69% is locked in glaciers and ice caps and ~30% in groundwater — only ~0.007% is readily accessible in rivers and lakes; essential for drinking, agriculture (~70% of withdrawals), and industry."
ln resource:ecosystem:freshwater resource:ecosystem sys:part_of
set.add name="ontology.natural_resources" id="resource:ecosystem:freshwater"

def "resource:ecosystem:forests" "Forests: land dominated by trees (crown cover >10–30%); cover ~31% of Earth's land surface; classified as tropical, temperate, and boreal (taiga); provide carbon sinks (~2.6 Gt C/yr absorbed), biodiversity habitat (~80% of terrestrial species), timber, water regulation, and oxygen."
ln resource:ecosystem:forests resource:ecosystem sys:part_of
set.add name="ontology.natural_resources" id="resource:ecosystem:forests"

def "resource:ecosystem:oceans" "Oceans: saltwater bodies covering ~71% of Earth's surface; absorb ~25% of anthropogenic CO2 emissions and ~90% of excess heat; phytoplankton produce ~50% of Earth's oxygen; support global fisheries and regulate climate via thermohaline circulation."
ln resource:ecosystem:oceans resource:ecosystem sys:part_of
set.add name="ontology.natural_resources" id="resource:ecosystem:oceans"

def "resource:ecosystem:soil" "Soil: complex mixture of minerals, organic matter (humus), water, air, and living organisms; supports virtually all terrestrial food production; a single teaspoon contains ~25,000 species; takes ~500 years to form 1 inch (2.5 cm) of topsoil; degraded by erosion, compaction, salinisation."
ln resource:ecosystem:soil resource:ecosystem sys:part_of
set.add name="ontology.natural_resources" id="resource:ecosystem:soil"

def "resource:ecosystem:fisheries" "Fisheries: wild-capture marine and freshwater fisheries plus aquaculture; global production ~180–185 million tonnes/year (2022); ~3.3 billion people rely on seafood as primary protein source; ~35% of wild stocks fished at biologically unsustainable levels (FAO 2022)."
ln resource:ecosystem:fisheries resource:ecosystem sys:part_of
ln resource:ecosystem:fisheries resource:ecosystem:oceans @drawn_from
set.add name="ontology.natural_resources" id="resource:ecosystem:fisheries"

def "resource:ecosystem:timber" "Timber: wood harvested for construction, furniture, paper, and fuel; classified as softwood (conifers — pine, spruce, fir; used in construction framing) and hardwood (angiosperms — oak, teak, mahogany; used in furniture and flooring); global production ~3.8 billion m³/year."
ln resource:ecosystem:timber resource:ecosystem sys:part_of
ln resource:ecosystem:timber resource:ecosystem:forests @drawn_from
set.add name="ontology.natural_resources" id="resource:ecosystem:timber"
