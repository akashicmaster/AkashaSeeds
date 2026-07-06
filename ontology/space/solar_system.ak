# solar_system.ak
# Solar system objects — planets, moons, dwarf planets, comets, notable deep-sky objects
# Data: IAU, JPL, NASA — Public domain
#

# ── Namespace anchors ────────────────────────────────────────────────────────

def "astro:solar_system" "The gravitationally bound system of the Sun and the objects that orbit it, within the Milky Way galaxy"

def "astro:planet" "Namespace anchor for solar system planets; a body that orbits the Sun, has cleared its orbital neighbourhood, and has sufficient mass for hydrostatic equilibrium"

def "astro:moon" "Namespace anchor for natural satellites — bodies in stable orbit around a planet or dwarf planet"

def "astro:dwarf_planet" "Namespace anchor for dwarf planets; bodies that orbit the Sun and have hydrostatic equilibrium but have not cleared their orbital neighbourhood"

def "astro:comet" "Namespace anchor for comets; icy small solar system bodies that develop a coma and tails when near the Sun"

def "astro:nebula" "Namespace anchor for nebulae; interstellar clouds of gas and dust, often regions of star formation or stellar remnants"

def "astro:galaxy" "Namespace anchor for galaxies; gravitationally bound systems of stars, gas, dust, and dark matter"

# ── The Sun ──────────────────────────────────────────────────────────────────

def "astro:star:sun" "G2V main-sequence star at centre of the solar system; diameter 1,392,700 km; mass 1.989×10³⁰ kg; surface temp 5,778 K; age ~4.6 Gyr"
al astro:star:sun astro:sun
ln astro:star:sun astro:solar_system sys:part_of

# ── Regions ──────────────────────────────────────────────────────────────────

def "astro:region:inner_solar_system" "Region inside the asteroid belt containing the four terrestrial planets; roughly 0.3–2 AU from the Sun"
ln astro:region:inner_solar_system astro:solar_system sys:part_of

def "astro:region:asteroid_belt" "Torus-shaped region between Mars and Jupiter, 2.2–3.2 AU; contains most of the solar system's asteroids"
ln astro:region:asteroid_belt astro:solar_system sys:part_of

def "astro:region:outer_solar_system" "Region beyond the asteroid belt containing the four giant planets; roughly 5–30 AU from the Sun"
ln astro:region:outer_solar_system astro:solar_system sys:part_of

def "astro:region:kuiper_belt" "Disc-shaped region beyond Neptune, 30–50 AU; contains icy bodies including Pluto, Eris, Makemake, and Haumea"
ln astro:region:kuiper_belt astro:solar_system sys:part_of

def "astro:region:scattered_disc" "Sparsely populated region overlapping the Kuiper Belt and extending to ~100 AU; source of short-period comets"
ln astro:region:scattered_disc astro:solar_system sys:part_of

def "astro:region:oort_cloud" "Hypothetical vast spherical shell of icy bodies, ~2,000–100,000 AU; long-period comet reservoir"
ln astro:region:oort_cloud astro:solar_system sys:part_of

def "astro:region:heliopause" "Boundary where the solar wind is stopped by interstellar medium; outer edge of the heliosphere, ~120 AU"
ln astro:region:heliopause astro:solar_system sys:part_of

# ── Inner planets ─────────────────────────────────────────────────────────────

def "astro:planet:mercury" "Innermost planet; diameter 4,879 km; mass 3.301×10²³ kg; orbital period 87.97 days; 0.387 AU from Sun; no moons; largest temperature swings in solar system"
al astro:planet:mercury astro:mercury
ln astro:planet:mercury astro:planet sys:part_of
ln astro:planet:mercury astro:solar_system sys:part_of
ln astro:planet:mercury astro:region:inner_solar_system sys:part_of

def "astro:planet:venus" "Second planet; diameter 12,104 km; mass 4.867×10²⁴ kg; orbital period 224.7 days; 0.723 AU; hottest planet (465°C mean surface); retrograde rotation; dense CO₂ atmosphere"
al astro:planet:venus astro:venus
ln astro:planet:venus astro:planet sys:part_of
ln astro:planet:venus astro:solar_system sys:part_of
ln astro:planet:venus astro:region:inner_solar_system sys:part_of

def "astro:planet:earth" "Third planet; diameter 12,742 km; mass 5.972×10²⁴ kg; orbital period 365.25 days; 1.000 AU; only known body with confirmed life; one natural satellite (Luna)"
al astro:planet:earth astro:earth
ln astro:planet:earth astro:planet sys:part_of
ln astro:planet:earth astro:solar_system sys:part_of
ln astro:planet:earth astro:region:inner_solar_system sys:part_of

def "astro:planet:mars" "Fourth planet; diameter 6,779 km; mass 6.39×10²³ kg; orbital period 686.97 days; 1.524 AU; red iron-oxide surface; Olympus Mons (tallest volcano); two moons"
al astro:planet:mars astro:mars
ln astro:planet:mars astro:planet sys:part_of
ln astro:planet:mars astro:solar_system sys:part_of
ln astro:planet:mars astro:region:inner_solar_system sys:part_of

# ── Outer planets ─────────────────────────────────────────────────────────────

def "astro:planet:jupiter" "Fifth planet; largest in solar system; diameter 142,984 km; mass 1.898×10²⁷ kg; orbital period 11.86 yr; 5.203 AU; gas giant; Great Red Spot; 95 known moons"
al astro:planet:jupiter astro:jupiter
ln astro:planet:jupiter astro:planet sys:part_of
ln astro:planet:jupiter astro:solar_system sys:part_of
ln astro:planet:jupiter astro:region:outer_solar_system sys:part_of

def "astro:planet:saturn" "Sixth planet; diameter 120,536 km; mass 5.683×10²⁶ kg; orbital period 29.46 yr; 9.537 AU; gas giant; prominent ring system; lowest density of any planet; 146 known moons"
al astro:planet:saturn astro:saturn
ln astro:planet:saturn astro:planet sys:part_of
ln astro:planet:saturn astro:solar_system sys:part_of
ln astro:planet:saturn astro:region:outer_solar_system sys:part_of

def "astro:planet:uranus" "Seventh planet; diameter 51,118 km; mass 8.681×10²⁵ kg; orbital period 84.01 yr; 19.19 AU; ice giant; rotational axis tilted 97.8°; 27 known moons"
al astro:planet:uranus astro:uranus
ln astro:planet:uranus astro:planet sys:part_of
ln astro:planet:uranus astro:solar_system sys:part_of
ln astro:planet:uranus astro:region:outer_solar_system sys:part_of

def "astro:planet:neptune" "Eighth planet; diameter 49,528 km; mass 1.024×10²⁶ kg; orbital period 164.8 yr; 30.07 AU; ice giant; strongest winds in solar system (2,100 km/h); 16 known moons"
al astro:planet:neptune astro:neptune
ln astro:planet:neptune astro:planet sys:part_of
ln astro:planet:neptune astro:solar_system sys:part_of
ln astro:planet:neptune astro:region:outer_solar_system sys:part_of

# ── Earth's Moon ─────────────────────────────────────────────────────────────

def "astro:moon:luna" "Earth's only natural satellite; diameter 3,474 km; mass 7.342×10²² kg; orbital period 27.3 days; synchronous rotation; only extraterrestrial body visited by humans"
al astro:moon:luna astro:moon:earth:luna
ln astro:moon:luna astro:moon sys:part_of
ln astro:moon:luna astro:planet:earth sys:part_of

# ── Mars moons ────────────────────────────────────────────────────────────────

def "astro:moon:phobos" "Larger of Mars's two moons; diameter ~27 km; orbital period 7.6 h; closer than any other moon to its planet; gradually spiralling inward"
ln astro:moon:phobos astro:moon sys:part_of
ln astro:moon:phobos astro:planet:mars sys:part_of

def "astro:moon:deimos" "Smaller of Mars's two moons; diameter ~15 km; orbital period 30.3 h; outermost Martian moon; very low surface gravity"
ln astro:moon:deimos astro:moon sys:part_of
ln astro:moon:deimos astro:planet:mars sys:part_of

# ── Galilean moons of Jupiter ─────────────────────────────────────────────────

def "astro:moon:io" "Innermost Galilean moon of Jupiter; diameter 3,643 km; most volcanically active body in the solar system; sulphur-rich surface; discovered 1610"
ln astro:moon:io astro:moon sys:part_of
ln astro:moon:io astro:planet:jupiter sys:part_of

def "astro:moon:europa" "Second Galilean moon of Jupiter; diameter 3,122 km; smooth ice surface; likely subsurface liquid-water ocean; high astrobiological interest"
ln astro:moon:europa astro:moon sys:part_of
ln astro:moon:europa astro:planet:jupiter sys:part_of

def "astro:moon:ganymede" "Largest moon in the solar system; diameter 5,268 km; third Galilean moon of Jupiter; larger than Mercury; has its own magnetosphere"
ln astro:moon:ganymede astro:moon sys:part_of
ln astro:moon:ganymede astro:planet:jupiter sys:part_of

def "astro:moon:callisto" "Outermost Galilean moon of Jupiter; diameter 3,008 km; heavily cratered ancient surface; possible subsurface ocean; low radiation environment"
ln astro:moon:callisto astro:moon sys:part_of
ln astro:moon:callisto astro:planet:jupiter sys:part_of

# ── Saturn moons ──────────────────────────────────────────────────────────────

def "astro:moon:titan" "Largest moon of Saturn; diameter 5,151 km; thick nitrogen atmosphere with methane cycle; lakes of liquid methane; Huygens probe landed 2005"
ln astro:moon:titan astro:moon sys:part_of
ln astro:moon:titan astro:planet:saturn sys:part_of

def "astro:moon:enceladus" "Sixth-largest moon of Saturn; diameter 504 km; active cryovolcanic geysers at south pole ejecting water vapour; subsurface ocean confirmed"
ln astro:moon:enceladus astro:moon sys:part_of
ln astro:moon:enceladus astro:planet:saturn sys:part_of

def "astro:moon:mimas" "Smallest of Saturn's major moons; diameter 396 km; giant Herschel impact crater gives it a Death Star appearance"
ln astro:moon:mimas astro:moon sys:part_of
ln astro:moon:mimas astro:planet:saturn sys:part_of

def "astro:moon:tethys" "Moon of Saturn; diameter 1,062 km; almost pure water ice; features large Odysseus crater and Ithaca Chasma canyon system"
ln astro:moon:tethys astro:moon sys:part_of
ln astro:moon:tethys astro:planet:saturn sys:part_of

def "astro:moon:dione" "Moon of Saturn; diameter 1,123 km; heavily cratered trailing hemisphere; bright wispy terrain of ice cliffs on leading face"
ln astro:moon:dione astro:moon sys:part_of
ln astro:moon:dione astro:planet:saturn sys:part_of

def "astro:moon:rhea" "Second-largest moon of Saturn; diameter 1,527 km; heavily cratered; primarily water ice with rocky core; thin oxygen-CO₂ exosphere"
ln astro:moon:rhea astro:moon sys:part_of
ln astro:moon:rhea astro:planet:saturn sys:part_of

def "astro:moon:iapetus" "Third-largest moon of Saturn; diameter 1,469 km; striking two-tone colouration — dark leading hemisphere, bright trailing hemisphere"
ln astro:moon:iapetus astro:moon sys:part_of
ln astro:moon:iapetus astro:planet:saturn sys:part_of

def "astro:moon:hyperion" "Irregular moon of Saturn; ~360 km longest axis; chaotic rotation; sponge-like porous surface; not in synchronous rotation"
ln astro:moon:hyperion astro:moon sys:part_of
ln astro:moon:hyperion astro:planet:saturn sys:part_of

# ── Uranus moons ──────────────────────────────────────────────────────────────

def "astro:moon:miranda" "Innermost major moon of Uranus; diameter 472 km; extreme terrain including Verona Rupes cliff (~20 km high); likely tectonic activity"
ln astro:moon:miranda astro:moon sys:part_of
ln astro:moon:miranda astro:planet:uranus sys:part_of

def "astro:moon:ariel" "Moon of Uranus; diameter 1,158 km; youngest and brightest surface of the large Uranian moons; extensive canyon systems"
ln astro:moon:ariel astro:moon sys:part_of
ln astro:moon:ariel astro:planet:uranus sys:part_of

def "astro:moon:umbriel" "Moon of Uranus; diameter 1,169 km; darkest of the major Uranian moons; ancient heavily cratered surface; mysterious bright Wunda crater ring"
ln astro:moon:umbriel astro:moon sys:part_of
ln astro:moon:umbriel astro:planet:uranus sys:part_of

def "astro:moon:titania" "Largest moon of Uranus; diameter 1,578 km; mix of craters and rift valleys; possible subsurface ocean; named after Shakespearean character"
ln astro:moon:titania astro:moon sys:part_of
ln astro:moon:titania astro:planet:uranus sys:part_of

def "astro:moon:oberon" "Outermost major moon of Uranus; diameter 1,523 km; ancient cratered surface; prominent mountain near limb; named after Shakespearean character"
ln astro:moon:oberon astro:moon sys:part_of
ln astro:moon:oberon astro:planet:uranus sys:part_of

# ── Neptune moons ─────────────────────────────────────────────────────────────

def "astro:moon:triton" "Largest moon of Neptune; diameter 2,707 km; retrograde orbit indicating captured Kuiper Belt origin; surface temp −235°C; nitrogen geysers; will eventually be torn apart"
ln astro:moon:triton astro:moon sys:part_of
ln astro:moon:triton astro:planet:neptune sys:part_of

def "astro:moon:nereid" "Irregular moon of Neptune; diameter ~340 km; highly eccentric orbit (eccentricity 0.75); likely a captured object; second moon of Neptune discovered"
ln astro:moon:nereid astro:moon sys:part_of
ln astro:moon:nereid astro:planet:neptune sys:part_of

# ── Dwarf planets ─────────────────────────────────────────────────────────────

def "astro:dwarf_planet:pluto" "Largest known Kuiper Belt object by volume; diameter 2,376 km; companion Charon (diameter 1,212 km); thin nitrogen atmosphere; 5 moons total; visited by New Horizons 2015"
al astro:dwarf_planet:pluto astro:pluto
ln astro:dwarf_planet:pluto astro:dwarf_planet sys:part_of
ln astro:dwarf_planet:pluto astro:solar_system sys:part_of
ln astro:dwarf_planet:pluto astro:region:kuiper_belt sys:part_of

def "astro:dwarf_planet:ceres" "Only dwarf planet in the asteroid belt; diameter 945 km; largest body in the asteroid belt (~33% of its total mass); water ice mantle; visited by Dawn spacecraft 2015"
al astro:dwarf_planet:ceres astro:ceres
ln astro:dwarf_planet:ceres astro:dwarf_planet sys:part_of
ln astro:dwarf_planet:ceres astro:solar_system sys:part_of
ln astro:dwarf_planet:ceres astro:region:asteroid_belt sys:part_of

def "astro:dwarf_planet:eris" "Most massive known dwarf planet; diameter 2,326 km; mass slightly greater than Pluto; highly eccentric orbit; located in scattered disc; moon Dysnomia"
al astro:dwarf_planet:eris astro:eris
ln astro:dwarf_planet:eris astro:dwarf_planet sys:part_of
ln astro:dwarf_planet:eris astro:solar_system sys:part_of
ln astro:dwarf_planet:eris astro:region:scattered_disc sys:part_of

def "astro:dwarf_planet:haumea" "Dwarf planet in Kuiper Belt; elongated triaxial shape due to rapid 3.9 h rotation; two moons (Hi'iaka, Namaka); has a ring; density similar to rock"
al astro:dwarf_planet:haumea astro:haumea
ln astro:dwarf_planet:haumea astro:dwarf_planet sys:part_of
ln astro:dwarf_planet:haumea astro:solar_system sys:part_of
ln astro:dwarf_planet:haumea astro:region:kuiper_belt sys:part_of

def "astro:dwarf_planet:makemake" "Dwarf planet in Kuiper Belt; diameter ~1,430 km; reddish surface of tholins and methane ice; one small moon (MK2); no detected atmosphere"
al astro:dwarf_planet:makemake astro:makemake
ln astro:dwarf_planet:makemake astro:dwarf_planet sys:part_of
ln astro:dwarf_planet:makemake astro:solar_system sys:part_of
ln astro:dwarf_planet:makemake astro:region:kuiper_belt sys:part_of

# ── Notable comets ────────────────────────────────────────────────────────────

def "astro:comet:halley" "Most famous periodic comet; orbital period ~75–76 yr; last perihelion 1986, next expected 2061; visible to naked eye; nucleus ~15×8 km; records back to 240 BCE"
al astro:comet:halley astro:1p_halley
ln astro:comet:halley astro:comet sys:part_of
ln astro:comet:halley astro:solar_system sys:part_of

def "astro:comet:hale_bopp" "Exceptionally bright comet visible in 1997; orbital period ~2,520 yr; nucleus ~60 km; one of the most widely observed comets of the 20th century"
al astro:comet:hale_bopp astro:c1995_o1
ln astro:comet:hale_bopp astro:comet sys:part_of
ln astro:comet:hale_bopp astro:solar_system sys:part_of

def "astro:comet:67p" "Short-period comet; orbital period 6.44 yr; nucleus is a bilobed contact binary ~4×3 km; target of ESA Rosetta mission (2014–2016); Philae lander deployed"
al astro:comet:67p astro:comet:churyumov_gerasimenko
ln astro:comet:67p astro:comet sys:part_of
ln astro:comet:67p astro:solar_system sys:part_of

# ── Notable deep-sky objects ──────────────────────────────────────────────────

def "astro:nebula:m1" "Crab Nebula; supernova remnant in Taurus; remnant of SN 1054 observed by Chinese astronomers; ~6,500 ly distant; contains Crab Pulsar at centre"
al astro:nebula:m1 astro:ngc:1952
ln astro:nebula:m1 astro:nebula sys:part_of

def "astro:nebula:m42" "Orion Nebula; diffuse emission nebula in Orion; ~1,344 ly distant; one of the most observed and photographed objects; active star-forming region; visible to naked eye"
al astro:nebula:m42 astro:ngc:1976
ln astro:nebula:m42 astro:nebula sys:part_of

def "astro:nebula:m45" "Pleiades; open star cluster in Taurus; ~444 ly distant; ~1,000 stars; reflection nebula; naked-eye object; named for the Seven Sisters in Greek mythology"
al astro:nebula:m45 astro:pleiades
ln astro:nebula:m45 astro:nebula sys:part_of

def "astro:nebula:m57" "Ring Nebula in Lyra; planetary nebula; ~2,300 ly distant; shell of ionised gas ejected by a dying star; white dwarf at centre; ~1 ly diameter"
al astro:nebula:m57 astro:ngc:6720
ln astro:nebula:m57 astro:nebula sys:part_of

def "astro:galaxy:m31" "Andromeda Galaxy; nearest large spiral galaxy; ~2.537 million ly distant; diameter ~220,000 ly; on collision course with Milky Way in ~4.5 Gyr; ~1 trillion stars"
al astro:galaxy:m31 astro:ngc:224
ln astro:galaxy:m31 astro:galaxy sys:part_of

def "astro:galaxy:m87" "Virgo A; giant elliptical galaxy in Virgo Cluster; ~53.5 million ly distant; contains M87* — first black hole directly imaged by Event Horizon Telescope (2019); relativistic jet"
al astro:galaxy:m87 astro:ngc:4486
al astro:galaxy:m87 astro:virgo_a
ln astro:galaxy:m87 astro:galaxy sys:part_of

def "astro:galaxy:m101" "Pinwheel Galaxy; face-on spiral galaxy in Ursa Major; ~21 million ly distant; diameter ~170,000 ly; asymmetric due to tidal interaction with companion galaxies"
al astro:galaxy:m101 astro:ngc:5457
ln astro:galaxy:m101 astro:galaxy sys:part_of

def "astro:galaxy:lmc" "Large Magellanic Cloud; irregular satellite galaxy of the Milky Way; ~163,000 ly distant; ~14,000 ly diameter; most active star-forming region: 30 Doradus (Tarantula Nebula)"
al astro:galaxy:lmc astro:large_magellanic_cloud
ln astro:galaxy:lmc astro:galaxy sys:part_of

def "astro:galaxy:smc" "Small Magellanic Cloud; irregular satellite galaxy of the Milky Way; ~200,000 ly distant; ~7,000 ly diameter; interacts with LMC and Milky Way through Magellanic Stream"
al astro:galaxy:smc astro:small_magellanic_cloud
ln astro:galaxy:smc astro:galaxy sys:part_of

def "astro:remnant:sgr_a_star" "Sagittarius A*; supermassive black hole at the centre of the Milky Way; mass ~4 million solar masses; distance ~26,000 ly; imaged by Event Horizon Telescope 2022"
al astro:remnant:sgr_a_star astro:galactic_centre
ln astro:remnant:sgr_a_star astro:remnant:black_hole sys:is_a
