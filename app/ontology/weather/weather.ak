# weather.ak
# Meteorological phenomena, cloud types, storm classifications, atmospheric layers,
# climate zones, and weather measurement scales
# Sources: WMO, NOAA, Köppen — Public domain
#

# ── Namespace anchors ─────────────────────────────────────────────────────────

def "weather:cloud" "Namespace anchor for cloud genera and special cloud forms (WMO classification)"

def "weather:precipitation" "Namespace anchor for precipitation types — water in any phase falling from the atmosphere"

def "weather:storm" "Namespace anchor for storm types — organised, energetic atmospheric disturbances"

def "weather:phenomenon" "Namespace anchor for atmospheric optical, electrical, and other observable phenomena"

def "weather:layer" "Namespace anchor for vertical atmospheric layers defined by temperature profile"

def "weather:scale" "Namespace anchor for meteorological measurement and classification scales"

def "weather:climate" "Namespace anchor for Köppen climate classification zones"

def "weather:system" "Namespace anchor for large-scale ocean-atmosphere climate oscillation systems"

# ── Cloud genera (WMO 10 genera) ──────────────────────────────────────────────

def "weather:cloud:cirrus" "High-altitude ice-crystal cloud; wispy, hair-like filaments; base above 6,000 m; often precede warm fronts; genus Ci"
ln weather:cloud:cirrus weather:cloud sys:part_of

def "weather:cloud:cirrocumulus" "High-altitude cloud of small white puffs or ripples arranged in rows; mackerel sky appearance; base 6,000–12,000 m; genus Cc"
ln weather:cloud:cirrocumulus weather:cloud sys:part_of

def "weather:cloud:cirrostratus" "Thin transparent high-altitude veil covering much of the sky; produces 22° halo phenomena; base 6,000–12,000 m; genus Cs"
ln weather:cloud:cirrostratus weather:cloud sys:part_of

def "weather:cloud:altocumulus" "Mid-level cloud of grey-white patches, puffs, or waves; often in rows; base 2,000–7,000 m; can indicate thunderstorm development; genus Ac"
ln weather:cloud:altocumulus weather:cloud sys:part_of

def "weather:cloud:altostratus" "Grey or blue-grey sheet of uniform cloud covering the sky; mid-level; sun appears as through frosted glass; base 2,000–7,000 m; genus As"
ln weather:cloud:altostratus weather:cloud sys:part_of

def "weather:cloud:nimbostratus" "Dark grey rain cloud with diffuse base; produces continuous moderate precipitation; no distinct base; extensive vertical range; genus Ns"
ln weather:cloud:nimbostratus weather:cloud sys:part_of

def "weather:cloud:stratocumulus" "Low grey or whitish lumpy layer; patches, rolls, or rounded masses; most common cloud type on Earth; base below 2,000 m; genus Sc"
ln weather:cloud:stratocumulus weather:cloud sys:part_of

def "weather:cloud:stratus" "Low uniform grey layer resembling fog that does not reach the ground; may produce drizzle; base below 2,000 m; like fog aloft; genus St"
ln weather:cloud:stratus weather:cloud sys:part_of

def "weather:cloud:cumulus" "Puffy white fair-weather clouds; flat horizontal base; cauliflower top; base 300–2,000 m; formed by convective thermals; genus Cu"
ln weather:cloud:cumulus weather:cloud sys:part_of

def "weather:cloud:cumulonimbus" "Towering convective storm cloud; anvil-shaped glaciated top; produces lightning, thunder, heavy rain, and hail; can extend from near-surface to tropopause; genus Cb"
ln weather:cloud:cumulonimbus weather:cloud sys:part_of

# ── Special cloud forms ────────────────────────────────────────────────────────

def "weather:cloud:lenticular" "Lens-shaped orographic wave cloud; forms in stable air over mountains or ridges; often mistaken for UFOs; does not move despite strong winds"
ln weather:cloud:lenticular weather:cloud sys:part_of

def "weather:cloud:mammatus" "Pouch-like protrusions hanging below cumulonimbus anvil; indicate severe turbulence and downdraughts; associated with powerful thunderstorms"
ln weather:cloud:mammatus weather:cloud sys:part_of

def "weather:cloud:noctilucent" "Mesospheric cloud at ~80 km altitude; composed of ice crystals; visible at twilight in summer high latitudes; highest clouds in Earth's atmosphere"
ln weather:cloud:noctilucent weather:cloud sys:part_of

def "weather:cloud:fog" "Ground-level cloud reducing visibility below 1 km; forms when air is cooled to dewpoint or moisture is added; radiation, advection, and valley types"
ln weather:cloud:fog weather:cloud sys:part_of

# ── Precipitation types ────────────────────────────────────────────────────────

def "weather:precipitation:rain" "Liquid water droplets falling from clouds; diameter >0.5 mm; primary source of freshwater for terrestrial ecosystems"
ln weather:precipitation:rain weather:precipitation sys:part_of

def "weather:precipitation:drizzle" "Fine liquid droplets falling from stratus clouds; diameter 0.2–0.5 mm; lower intensity than rain; associated with stratocumulus or stratus"
ln weather:precipitation:drizzle weather:precipitation sys:part_of

def "weather:precipitation:snow" "Precipitation of ice crystals aggregating into snowflakes; forms when temperature throughout cloud and air column is below 0°C"
ln weather:precipitation:snow weather:precipitation sys:part_of

def "weather:precipitation:sleet" "Rain drops that freeze into ice pellets before reaching the ground; distinct from freezing rain; transparent or translucent spherical ice"
ln weather:precipitation:sleet weather:precipitation sys:part_of

def "weather:precipitation:hail" "Balls or lumps of ice ≥5 mm diameter formed by repeated updraft cycling in cumulonimbus; can reach softball size in severe supercells"
ln weather:precipitation:hail weather:precipitation sys:part_of

def "weather:precipitation:graupel" "Soft hail or snow pellets; snow crystals rimed by supercooled water droplets to form soft opaque pellets 2–5 mm; also called soft hail or snow pellets"
ln weather:precipitation:graupel weather:precipitation sys:part_of

def "weather:precipitation:freezing_rain" "Rain that freezes on contact with surfaces at or below 0°C; forms glaze ice; creates dangerous icing conditions on roads, aircraft, and infrastructure"
ln weather:precipitation:freezing_rain weather:precipitation sys:part_of

def "weather:precipitation:virga" "Precipitation that evaporates or sublimes before reaching the ground; visible as streaks or wisps below cloud base; common in arid regions"
ln weather:precipitation:virga weather:precipitation sys:part_of

# ── Storm types ────────────────────────────────────────────────────────────────

def "weather:storm:thunderstorm" "Convective storm produced by cumulonimbus; characterised by lightning, thunder, heavy rain, and strong gusts; can produce tornadoes, hail, and flooding"
ln weather:storm:thunderstorm weather:storm sys:part_of

def "weather:storm:tropical_cyclone" "Organised rotating convective system over warm ocean (SST >26°C); named hurricane (Atlantic/E Pacific), typhoon (W Pacific), cyclone (Indian/S Pacific); ≥74 mph sustained winds"
al weather:storm:tropical_cyclone weather:storm:hurricane
ln weather:storm:tropical_cyclone weather:storm sys:part_of

def "weather:storm:extratropical_cyclone" "Mid-latitude synoptic-scale low-pressure system; derives energy from temperature contrast between air masses; drives much of mid-latitude weather; frontal structure"
ln weather:storm:extratropical_cyclone weather:storm sys:part_of

def "weather:storm:tornado" "Violently rotating column of air in contact with both cumulonimbus and the ground; rated EF0–EF5 on Enhanced Fujita scale; most common in US Great Plains"
ln weather:storm:tornado weather:storm sys:part_of

def "weather:storm:blizzard" "Severe winter storm combining heavy snow or blowing snow with sustained winds ≥56 km/h and visibility <400 m for ≥3 hours; dangerous wind chill"
ln weather:storm:blizzard weather:storm sys:part_of

def "weather:storm:derecho" "Long-lived, fast-moving family of downburst clusters producing straight-line winds; path ≥400 km; can cause damage comparable to tornadoes"
ln weather:storm:derecho weather:storm sys:part_of

def "weather:storm:haboob" "Intense wall of dust and sand generated by thunderstorm outflow; can be >1 km tall and >100 km wide; common in Sudan, Sahara, Arabian Peninsula, and US Southwest"
ln weather:storm:haboob weather:storm sys:part_of

def "weather:storm:nor_easter" "Intense extratropical cyclone affecting north-eastern North America; winds from north-east; can produce heavy snow, coastal flooding, and hurricane-force winds"
ln weather:storm:nor_easter weather:storm sys:part_of

def "weather:storm:bomb_cyclone" "Extratropical cyclone that undergoes explosive deepening (rapid intensification ≥24 hPa in 24 hours); process called bombogenesis; creates rapidly worsening severe weather"
ln weather:storm:bomb_cyclone weather:storm sys:part_of
ln weather:storm:bomb_cyclone weather:storm:extratropical_cyclone sys:is_a

# ── Atmospheric phenomena ──────────────────────────────────────────────────────

def "weather:phenomenon:aurora_borealis" "Northern Lights; luminous display in high-latitude skies caused by solar wind particles colliding with atmospheric gases; green, red, and purple colours"
ln weather:phenomenon:aurora_borealis weather:phenomenon sys:part_of

def "weather:phenomenon:aurora_australis" "Southern Lights; counterpart of aurora borealis in Southern Hemisphere high latitudes; mirrors northern aurora activity linked to geomagnetic activity"
ln weather:phenomenon:aurora_australis weather:phenomenon sys:part_of

def "weather:phenomenon:rainbow" "Optical phenomenon caused by refraction, dispersion, and reflection of sunlight in water droplets; appears as arc of spectral colours; red on outside, violet inside"
ln weather:phenomenon:rainbow weather:phenomenon sys:part_of

def "weather:phenomenon:supernumerary_rainbow" "Series of faint additional bows inside the primary rainbow; caused by wave interference of light; visible under specific drop-size conditions"
ln weather:phenomenon:supernumerary_rainbow weather:phenomenon sys:part_of

def "weather:phenomenon:fog_bow" "White or pale arc similar to rainbow but formed in fog; droplets too small for colour separation; diameter similar to rainbow but colourless"
ln weather:phenomenon:fog_bow weather:phenomenon sys:part_of

def "weather:phenomenon:halo" "Ring of light around the Sun or Moon at 22° angular radius; caused by refraction through hexagonal ice crystals in cirrostratus cloud"
ln weather:phenomenon:halo weather:phenomenon sys:part_of

def "weather:phenomenon:glory" "Circular optical phenomenon seen opposite the Sun around the shadow of the observer; caused by backscattering in water droplets; visible from aircraft"
ln weather:phenomenon:glory weather:phenomenon sys:part_of

def "weather:phenomenon:mirage" "Optical illusion caused by refraction of light through layers of air with different temperatures and densities; inferior (hot road) and superior (cold surface) types"
ln weather:phenomenon:mirage weather:phenomenon sys:part_of

def "weather:phenomenon:fata_morgana" "Complex superior mirage with multiple distorted, stacked images; occurs over cold water or flat terrain; can make ships or cliffs appear to float"
ln weather:phenomenon:fata_morgana weather:phenomenon sys:part_of
ln weather:phenomenon:fata_morgana weather:phenomenon:mirage sys:is_a

def "weather:phenomenon:sun_pillar" "Vertical column of light above or below the Sun; caused by reflection of sunlight off flat plate-shaped ice crystals oriented near-horizontally"
ln weather:phenomenon:sun_pillar weather:phenomenon sys:part_of

def "weather:phenomenon:green_flash" "Brief green colour at upper edge of setting or rising Sun; caused by atmospheric dispersion; visible only at sea horizon or very flat terrain"
ln weather:phenomenon:green_flash weather:phenomenon sys:part_of

def "weather:phenomenon:ball_lightning" "Rare, unexplained luminous sphere observed during thunderstorms; 1–50 cm diameter; moves slowly and may persist for seconds; no consensus physical explanation"
ln weather:phenomenon:ball_lightning weather:phenomenon sys:part_of

# ── Atmospheric layers ─────────────────────────────────────────────────────────

def "weather:layer:troposphere" "Lowest atmospheric layer; 0–12 km (varies with latitude); contains ~75% of atmosphere's mass; all weather occurs here; temperature decreases with altitude"
ln weather:layer:troposphere weather:layer sys:part_of

def "weather:layer:stratosphere" "Atmospheric layer 12–50 km altitude; temperature increases with altitude due to ozone absorption of UV; contains the ozone layer; jet aircraft cruise here"
ln weather:layer:stratosphere weather:layer sys:part_of

def "weather:layer:mesosphere" "Atmospheric layer 50–85 km altitude; coldest part of atmosphere (−90°C at mesopause); meteors burn up here; site of noctilucent clouds"
ln weather:layer:mesosphere weather:layer sys:part_of

def "weather:layer:thermosphere" "Atmospheric layer 85–600 km altitude; absorbs high-energy solar radiation; temperatures can reach 2,500°C; auroras occur here; ISS orbits within this layer"
ln weather:layer:thermosphere weather:layer sys:part_of

def "weather:layer:exosphere" "Outermost atmospheric layer above ~600 km; atoms and molecules escape to space; merges with interplanetary space; no sharp outer boundary"
ln weather:layer:exosphere weather:layer sys:part_of

# ── Measurement and classification scales ──────────────────────────────────────

def "weather:scale:beaufort" "Empirical wind force scale 0–12; 0 = calm (<1 km/h); 6 = strong breeze (39–49 km/h); 12 = hurricane force (>118 km/h); devised by Admiral Beaufort 1805"
ln weather:scale:beaufort weather:scale sys:part_of

def "weather:scale:saffir_simpson" "Hurricane intensity scale Category 1–5; C1: 119–153 km/h; C2: 154–177 km/h; C3: 178–208 km/h; C4: 209–251 km/h; C5: >252 km/h sustained winds"
ln weather:scale:saffir_simpson weather:scale sys:part_of

def "weather:scale:fujita" "Enhanced Fujita scale EF0–EF5 for tornado wind speed estimation from damage indicators; EF0: 105–137 km/h; EF5: >322 km/h; replaced original Fujita scale 2007"
ln weather:scale:fujita weather:scale sys:part_of

# ── Köppen climate zones ───────────────────────────────────────────────────────

def "weather:climate:tropical" "Köppen group A; tropical climates where all months average ≥18°C; subdivisions: rainforest (Af), monsoon (Am), savanna (Aw/As); no winter season"
ln weather:climate:tropical weather:climate sys:part_of

def "weather:climate:dry" "Köppen group B; arid and semi-arid climates where potential evaporation exceeds precipitation annually; desert (BW: <250 mm/yr), steppe (BS: 250–500 mm/yr)"
ln weather:climate:dry weather:climate sys:part_of

def "weather:climate:temperate" "Köppen group C; temperate climates with mild winters (coldest month −3°C to 18°C); Mediterranean (Cs), humid subtropical (Cfa), oceanic (Cfb/Cfc)"
ln weather:climate:temperate weather:climate sys:part_of

def "weather:climate:continental" "Köppen group D; continental climates with cold winters (coldest month <−3°C) and warm summers; humid continental (Dfa/Dfb), sub-arctic/boreal taiga (Dfc/Dfd)"
ln weather:climate:continental weather:climate sys:part_of

def "weather:climate:polar" "Köppen group E; polar climates where all months average <10°C; tundra (ET: warmest month 0–10°C), ice cap (EF: all months <0°C)"
ln weather:climate:polar weather:climate sys:part_of

def "weather:climate:highland" "Köppen group H; mountain and highland climates where altitude overrides latitude; characterised by rapid vertical change in temperature, precipitation, and vegetation"
ln weather:climate:highland weather:climate sys:part_of

# ── Ocean-atmosphere climate systems ──────────────────────────────────────────

def "weather:system:enso" "El Niño-Southern Oscillation; coupled ocean-atmosphere phenomenon in the tropical Pacific; alternates between El Niño (warm phase) and La Niña (cool phase) on 2–7 yr cycles"
al weather:system:enso weather:system:el_nino_southern_oscillation
ln weather:system:enso weather:system sys:part_of

def "weather:system:el_nino" "Warm phase of ENSO; anomalous warming of central and eastern equatorial Pacific; disrupts global precipitation patterns; weakens trade winds"
ln weather:system:el_nino weather:system sys:part_of
ln weather:system:el_nino weather:system:enso sys:part_of

def "weather:system:la_nina" "Cool phase of ENSO; anomalous cooling of central and eastern equatorial Pacific; strengthens trade winds; opposite effects on precipitation to El Niño"
ln weather:system:la_nina weather:system sys:part_of
ln weather:system:la_nina weather:system:enso sys:part_of

def "weather:system:nao" "North Atlantic Oscillation; variation in pressure difference between Icelandic Low and Azores High; positive phase brings mild wet winters to Europe; dominant mode of N Atlantic variability"
al weather:system:nao weather:system:north_atlantic_oscillation
ln weather:system:nao weather:system sys:part_of

def "weather:system:pdo" "Pacific Decadal Oscillation; long-lived pattern of ocean-atmosphere climate variability in the North Pacific; positive phase mimics El Niño effects; decadal timescale"
al weather:system:pdo weather:system:pacific_decadal_oscillation
ln weather:system:pdo weather:system sys:part_of

def "weather:system:iod" "Indian Ocean Dipole; irregular oscillation of sea surface temperatures in the Indian Ocean; positive phase: warm west, cool east; affects monsoon rainfall in East Africa and Australia"
al weather:system:iod weather:system:indian_ocean_dipole
ln weather:system:iod weather:system sys:part_of

def "weather:system:polar_vortex" "Large area of low pressure and cold air surrounding the polar regions; weakening allows cold Arctic air to spill into mid-latitudes causing extreme cold spells"
ln weather:system:polar_vortex weather:system sys:part_of

def "weather:system:jet_stream" "Fast-flowing narrow air current in the upper troposphere/lower stratosphere; ~9–16 km altitude; speeds 130–400 km/h; polar and subtropical branches; steers mid-latitude storms"
ln weather:system:jet_stream weather:system sys:part_of
