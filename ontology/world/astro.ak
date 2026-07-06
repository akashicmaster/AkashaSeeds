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
