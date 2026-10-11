# Akasha ontology — namespace: astro
# atoms: 37

def "astro:body:celestial_body" "Any natural body outside of the Earth's atmosphere."

def "astro:body:planet" "A large astronomical body that is neither a star nor a stellar remnant."
ln astro:body:planet astro:body:celestial_body sys:is_a
ln astro:body:planet astro:body:star @orbits

def "astro:body:satellite" "A moon, planet or machine that orbits a planet or star."
ln astro:body:satellite astro:body:celestial_body sys:is_a
ln astro:body:satellite astro:body:planet @orbits

def "astro:body:star" "An astronomical object comprising a luminous spheroid of plasma held together by its gravity."
ln astro:body:star astro:body:celestial_body sys:is_a
ln astro:body:star astro:remnant:neutron_star @collapses_into
ln astro:body:star astro:remnant:black_hole @collapses_into

def "astro:concept:eccentricity" "A parameter that determines the amount by which its orbit around another body deviates from a perfect circle."

def "astro:concept:orbit" "The gravitationally curved trajectory of an object."

def "astro:constellation:aquarius" "aquarius."

def "astro:constellation:aries" "aries."

def "astro:constellation:cancer" "cancer."

def "astro:constellation:capricornus" "capricornus."

def "astro:constellation:gemini" "gemini."

def "astro:constellation:leo" "leo."

def "astro:constellation:libra" "libra."

def "astro:constellation:pisces" "pisces."

def "astro:constellation:sagittarius" "sagittarius."

def "astro:constellation:scorpius" "scorpius."

def "astro:constellation:taurus" "taurus."

def "astro:constellation:virgo" "virgo."

def "astro:cosmo:big_bang" "The prevailing cosmological model explaining the existence of the observable universe from the earliest known periods through its subsequent large-scale evolution."
ln astro:cosmo:big_bang astro:phenomenon:cosmic_expansion @initiates

def "astro:cosmo:dark_energy" "An unknown form of energy which is hypothesized to permeate all of space, tending to accelerate the expansion of the universe."
ln astro:cosmo:dark_energy astro:phenomenon:cosmic_expansion @accelerates

def "astro:cosmo:dark_matter" "A hypothetical form of matter thought to account for approximately 85% of the matter in the universe; it does not interact with the electromagnetic field."
ln astro:cosmo:dark_matter phys:unif:gravitational_interaction @exerts
ln astro:cosmo:dark_matter phys:unif:electromagnetic_interaction @lacks

def "astro:law:keplers_first_law" "The orbit of a planet is an ellipse with the Sun at one of the two foci."
ln astro:law:keplers_first_law astro:concept:orbit @describes

def "astro:law:keplers_second_law" "A line segment joining a planet and the Sun sweeps out equal areas during equal intervals of time."
ln astro:law:keplers_second_law astro:concept:orbit @describes

def "astro:law:keplers_third_law" "The square of the orbital period of a planet is directly proportional to the cube of the semi-major axis of its orbit."
ln astro:law:keplers_third_law astro:concept:orbit @describes

def "astro:law:universal_gravitation" "Newton's law stating that every particle attracts every other particle in the universe with a force proportional to the product of their masses and inversely proportional to the square of the distance between them."
ln astro:law:universal_gravitation phys:force:gravity @quantifies
ln astro:law:universal_gravitation phys:mech:mass @depends_on
ln astro:law:universal_gravitation astro:body:celestial_body @applies_to

def "astro:phenomenon:cosmic_expansion" "The increase in distance between gravitationally unbound parts of the observable universe with time."
ln astro:phenomenon:cosmic_expansion astro:phenomenon:redshift @causes

def "astro:phenomenon:redshift" "The displacement of spectral lines towards longer wavelengths in radiation from distant galaxies and celestial objects."
ln astro:phenomenon:redshift phys:em:electromagnetic_wave @affects

def "astro:remnant:black_hole" "A region of spacetime where gravity is so strong that nothing—no particles or even electromagnetic radiation such as light—can escape from it."
ln astro:remnant:black_hole phys:geom:spacetime_curvature @exhibits_extreme
ln astro:remnant:black_hole astro:remnant:event_horizon @possesses
ln astro:remnant:black_hole astro:remnant:singularity @contains

def "astro:remnant:event_horizon" "A boundary beyond which events cannot affect an observer; the 'point of no return' around a black hole."

def "astro:remnant:neutron_star" "The collapsed core of a massive supergiant star, composed almost entirely of neutrons and possessing extreme density and gravity."

def "astro:remnant:singularity" "A location in spacetime where the gravitational field of a celestial body becomes infinite in a way that does not depend on the coordinate system."

def "astro:star:aldebaran" "A red giant star located in the zodiac constellation of Taurus."
ln astro:star:aldebaran astro:body:star sys:is_a
ln astro:star:aldebaran astro:constellation:taurus @located_in

def "astro:star:antares" "A red supergiant star in the constellation of Scorpius."
ln astro:star:antares astro:body:star sys:is_a
ln astro:star:antares astro:constellation:scorpius @located_in

def "astro:star:hamal" "The brightest star in the northern constellation of Aries."
ln astro:star:hamal astro:body:star sys:is_a
ln astro:star:hamal astro:constellation:aries @located_in

def "astro:star:pollux" "An orange giant star in the constellation of Gemini."
ln astro:star:pollux astro:body:star sys:is_a
ln astro:star:pollux astro:constellation:gemini @located_in

def "astro:star:regulus" "The brightest star in the constellation of Leo."
ln astro:star:regulus astro:body:star sys:is_a
ln astro:star:regulus astro:constellation:leo @located_in

def "astro:star:spica" "The brightest object in the constellation of Virgo."
ln astro:star:spica astro:body:star sys:is_a
ln astro:star:spica astro:constellation:virgo @located_in

# ── major bright + navigation stars (for the star-chart reading room) ──
def "astro:star:sirius" "The brightest star in the night sky, in Canis Major; a blue-white main-sequence star 8.6 light-years away."
ln astro:star:sirius astro:body:star sys:is_a
def "astro:star:canopus" "The second-brightest star in the night sky, a white supergiant in the southern constellation Carina."
ln astro:star:canopus astro:body:star sys:is_a
def "astro:star:arcturus" "The brightest star in Boötes and the northern celestial hemisphere; an orange giant."
ln astro:star:arcturus astro:body:star sys:is_a
def "astro:star:vega" "The brightest star in Lyra; a blue-white star that was the northern pole star c. 12,000 BCE."
ln astro:star:vega astro:body:star sys:is_a
def "astro:star:capella" "The brightest star in Auriga; a system of two giant stars, appearing golden-yellow."
ln astro:star:capella astro:body:star sys:is_a
def "astro:star:rigel" "A blue supergiant, the brightest star in Orion, marking the hunter's left foot."
ln astro:star:rigel astro:body:star sys:is_a
def "astro:star:procyon" "The brightest star in Canis Minor; a nearby white main-sequence star with a white-dwarf companion."
ln astro:star:procyon astro:body:star sys:is_a
def "astro:star:betelgeuse" "A red supergiant marking Orion's shoulder; a variable star that may end as a supernova."
ln astro:star:betelgeuse astro:body:star sys:is_a
def "astro:star:bellatrix" "A blue giant marking the other shoulder of Orion, the 'Amazon Star'."
ln astro:star:bellatrix astro:body:star sys:is_a
def "astro:star:mintaka" "The westernmost star of Orion's Belt; a multiple star system near the celestial equator."
ln astro:star:mintaka astro:body:star sys:is_a
def "astro:star:alnilam" "The central, brightest star of Orion's Belt; a blue supergiant."
ln astro:star:alnilam astro:body:star sys:is_a
def "astro:star:alnitak" "The easternmost star of Orion's Belt; a triple star system beside the Flame Nebula."
ln astro:star:alnitak astro:body:star sys:is_a
def "astro:star:achernar" "The brightest star in Eridanus, marking the river's end; a rapidly rotating blue star."
ln astro:star:achernar astro:body:star sys:is_a
def "astro:star:hadar" "Beta Centauri, a blue giant and the second-brightest star in Centaurus, a southern pointer to Crux."
ln astro:star:hadar astro:body:star sys:is_a
def "astro:star:rigil_kentaurus" "Alpha Centauri, the nearest bright star system to the Sun (4.4 light-years), in Centaurus."
ln astro:star:rigil_kentaurus astro:body:star sys:is_a
def "astro:star:acrux" "The brightest star of the Southern Cross (Crux), a multiple blue star system."
ln astro:star:acrux astro:body:star sys:is_a
def "astro:star:altair" "The brightest star in Aquila; a nearby, rapidly rotating white star, a vertex of the Summer Triangle."
ln astro:star:altair astro:body:star sys:is_a
def "astro:star:deneb" "A distant, luminous blue-white supergiant, the brightest star in Cygnus and a vertex of the Summer Triangle."
ln astro:star:deneb astro:body:star sys:is_a
def "astro:star:fomalhaut" "The brightest star in Piscis Austrinus, 'the Lonely Star of Autumn', encircled by a debris disc."
ln astro:star:fomalhaut astro:body:star sys:is_a
def "astro:star:castor" "A six-star system in Gemini, appearing as the twin beside Pollux."
ln astro:star:castor astro:body:star sys:is_a
def "astro:star:polaris" "The North Star, closely aligned with the north celestial pole; the brightest star in Ursa Minor."
ln astro:star:polaris astro:body:star sys:is_a
def "astro:star:dubhe" "A pointer star of the Big Dipper (Ursa Major); an orange giant that, with Merak, points to Polaris."
ln astro:star:dubhe astro:body:star sys:is_a
def "astro:star:merak" "The lower pointer star of the Big Dipper's bowl in Ursa Major."
ln astro:star:merak astro:body:star sys:is_a
def "astro:star:alioth" "The brightest star of Ursa Major, the first star in the Big Dipper's handle."
ln astro:star:alioth astro:body:star sys:is_a
def "astro:star:mizar" "A star in the Big Dipper's handle famous as a naked-eye double with Alcor."
ln astro:star:mizar astro:body:star sys:is_a
def "astro:star:alkaid" "The star at the end of the Big Dipper's handle in Ursa Major; a hot blue star."
ln astro:star:alkaid astro:body:star sys:is_a
def "astro:star:algol" "The 'Demon Star' in Perseus, a famous eclipsing binary whose brightness visibly dips every ~2.9 days."
ln astro:star:algol astro:body:star sys:is_a

# ── extended star catalogue (planisphere: southern constellations + fuller figures) ──
def "astro:star:saiph" "Saiph, a hot blue star (apparent magnitude 2.06)."
ln astro:star:saiph astro:body:star sys:is_a
def "astro:star:adhara" "Adhara, a hot blue star (apparent magnitude 1.5)."
ln astro:star:adhara astro:body:star sys:is_a
def "astro:star:wezen" "Wezen, a yellow-white star (apparent magnitude 1.83)."
ln astro:star:wezen astro:body:star sys:is_a
def "astro:star:mirzam" "Mirzam, a hot blue star (apparent magnitude 1.98)."
ln astro:star:mirzam astro:body:star sys:is_a
def "astro:star:elnath" "Elnath, a hot blue star (apparent magnitude 1.65)."
ln astro:star:elnath astro:body:star sys:is_a
def "astro:star:menkalinan" "Menkalinan, a white star (apparent magnitude 1.9)."
ln astro:star:menkalinan astro:body:star sys:is_a
def "astro:star:alhena" "Alhena, a white star (apparent magnitude 1.9)."
ln astro:star:alhena astro:body:star sys:is_a
def "astro:star:denebola" "Denebola, a white star (apparent magnitude 2.11)."
ln astro:star:denebola astro:body:star sys:is_a
def "astro:star:algieba" "Algieba, an orange star (apparent magnitude 2.28)."
ln astro:star:algieba astro:body:star sys:is_a
def "astro:star:zosma" "Zosma, a white star (apparent magnitude 2.56)."
ln astro:star:zosma astro:body:star sys:is_a
def "astro:star:izar" "Izar, an orange star (apparent magnitude 2.35)."
ln astro:star:izar astro:body:star sys:is_a
def "astro:star:phecda" "Phecda, a white star (apparent magnitude 2.44)."
ln astro:star:phecda astro:body:star sys:is_a
def "astro:star:megrez" "Megrez, a white star (apparent magnitude 3.31)."
ln astro:star:megrez astro:body:star sys:is_a
def "astro:star:kochab" "Kochab, an orange star (apparent magnitude 2.07)."
ln astro:star:kochab astro:body:star sys:is_a
def "astro:star:pherkad" "Pherkad, a white star (apparent magnitude 3.0)."
ln astro:star:pherkad astro:body:star sys:is_a
def "astro:star:schedar" "Schedar, an orange star (apparent magnitude 2.24)."
ln astro:star:schedar astro:body:star sys:is_a
def "astro:star:caph" "Caph, a yellow-white star (apparent magnitude 2.28)."
ln astro:star:caph astro:body:star sys:is_a
def "astro:star:navi" "Navi, a hot blue star (apparent magnitude 2.15)."
ln astro:star:navi astro:body:star sys:is_a
def "astro:star:ruchbah" "Ruchbah, a white star (apparent magnitude 2.68)."
ln astro:star:ruchbah astro:body:star sys:is_a
def "astro:star:segin" "Segin, a hot blue star (apparent magnitude 3.35)."
ln astro:star:segin astro:body:star sys:is_a
def "astro:star:mirfak" "Mirfak, a yellow-white star (apparent magnitude 1.79)."
ln astro:star:mirfak astro:body:star sys:is_a
def "astro:star:alpheratz" "Alpheratz, a hot blue star (apparent magnitude 2.06)."
ln astro:star:alpheratz astro:body:star sys:is_a
def "astro:star:mirach" "Mirach, a red star (apparent magnitude 2.05)."
ln astro:star:mirach astro:body:star sys:is_a
def "astro:star:almach" "Almach, an orange star (apparent magnitude 2.1)."
ln astro:star:almach astro:body:star sys:is_a
def "astro:star:markab" "Markab, a hot blue star (apparent magnitude 2.49)."
ln astro:star:markab astro:body:star sys:is_a
def "astro:star:scheat" "Scheat, a red star (apparent magnitude 2.42)."
ln astro:star:scheat astro:body:star sys:is_a
def "astro:star:algenib" "Algenib, a hot blue star (apparent magnitude 2.83)."
ln astro:star:algenib astro:body:star sys:is_a
def "astro:star:sadr" "Sadr, a yellow-white star (apparent magnitude 2.23)."
ln astro:star:sadr astro:body:star sys:is_a
def "astro:star:gienah_cyg" "Gienah, an orange star (apparent magnitude 2.48)."
ln astro:star:gienah_cyg astro:body:star sys:is_a
def "astro:star:delta_cyg" "Fawaris, a hot blue star (apparent magnitude 2.87)."
ln astro:star:delta_cyg astro:body:star sys:is_a
def "astro:star:albireo" "Albireo, an orange star (apparent magnitude 3.05)."
ln astro:star:albireo astro:body:star sys:is_a
def "astro:star:tarazed" "Tarazed, an orange star (apparent magnitude 2.72)."
ln astro:star:tarazed astro:body:star sys:is_a
def "astro:star:shaula" "Shaula, a hot blue star (apparent magnitude 1.62)."
ln astro:star:shaula astro:body:star sys:is_a
def "astro:star:sargas" "Sargas, a yellow-white star (apparent magnitude 1.86)."
ln astro:star:sargas astro:body:star sys:is_a
def "astro:star:dschubba" "Dschubba, a hot blue star (apparent magnitude 2.29)."
ln astro:star:dschubba astro:body:star sys:is_a
def "astro:star:kaus_australis" "Kaus Aus., a hot blue star (apparent magnitude 1.85)."
ln astro:star:kaus_australis astro:body:star sys:is_a
def "astro:star:nunki" "Nunki, a hot blue star (apparent magnitude 2.05)."
ln astro:star:nunki astro:body:star sys:is_a
def "astro:star:menkent" "Menkent, an orange star (apparent magnitude 2.06)."
ln astro:star:menkent astro:body:star sys:is_a
def "astro:star:gacrux" "Gacrux, a red star (apparent magnitude 1.63)."
ln astro:star:gacrux astro:body:star sys:is_a
def "astro:star:mimosa" "Mimosa, a hot blue star (apparent magnitude 1.25)."
ln astro:star:mimosa astro:body:star sys:is_a
def "astro:star:imai" "Imai, a hot blue star (apparent magnitude 2.79)."
ln astro:star:imai astro:body:star sys:is_a
def "astro:star:miaplacidus" "Miaplacidus, a white star (apparent magnitude 1.68)."
ln astro:star:miaplacidus astro:body:star sys:is_a
def "astro:star:avior" "Avior, an orange star (apparent magnitude 1.86)."
ln astro:star:avior astro:body:star sys:is_a
def "astro:star:aspidiske" "Aspidiske, a white star (apparent magnitude 2.21)."
ln astro:star:aspidiske astro:body:star sys:is_a
def "astro:star:suhail" "Suhail, an orange star (apparent magnitude 2.21)."
ln astro:star:suhail astro:body:star sys:is_a
def "astro:star:alsephina" "Alsephina, a white star (apparent magnitude 1.75)."
ln astro:star:alsephina astro:body:star sys:is_a
def "astro:star:alnair" "Alnair, a hot blue star (apparent magnitude 1.74)."
ln astro:star:alnair astro:body:star sys:is_a
def "astro:star:peacock" "Peacock, a hot blue star (apparent magnitude 1.94)."
ln astro:star:peacock astro:body:star sys:is_a
def "astro:star:atria" "Atria, an orange star (apparent magnitude 1.91)."
ln astro:star:atria astro:body:star sys:is_a
