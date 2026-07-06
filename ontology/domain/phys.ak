# Akasha ontology — namespace: phys
# atoms: 75

def "phys:aero:drag" "The aerodynamic force that opposes an aircraft's motion through the air."

def "phys:aero:lift" "The component of aerodynamic force that is perpendicular to the flow direction, overcoming gravity."
ln phys:aero:lift phys:force:gravity @opposes

def "phys:aero:thrust" "A reaction force described quantitatively by Newton's third law, moving an aircraft forward."
ln phys:aero:thrust phys:aero:drag @opposes

def "phys:charge:electric_charge" "The physical property of matter that causes it to experience a force when placed in an electromagnetic field."
ln phys:charge:electric_charge phys:em:electric_field @generates

def "phys:em:electric_current" "A stream of charged particles, such as electrons or ions, moving through an electrical conductor or space."
ln phys:em:electric_current phys:em:magnetic_field @generates
ln phys:em:electric_current prop:phys:electrical_conductivity @requires

def "phys:em:electric_field" "A physical field that surrounds electrically charged particles and exerts force on all other charged particles in the field."

def "phys:em:electromagnetic_wave" "Synchronized oscillations of electric and magnetic fields that propagate at the speed of light through a vacuum."

def "phys:em:magnetic_field" "A vector field that describes the magnetic influence on moving electric charges, electric currents, and magnetic materials."

def "phys:em:voltage" "The difference in electric potential between two points, also called electric pressure or electric tension."
ln phys:em:voltage phys:energy:potential_energy @derived_from

def "phys:energy:kinetic_energy" "The energy that an object possesses due to its motion."

def "phys:energy:potential_energy" "The energy held by an object because of its position relative to other objects, stresses within itself, electric charge, and other factors."

def "phys:energy:work" "The energy transferred to or from an object via the application of force along a displacement."
ln phys:energy:work phys:force:force @requires
ln phys:energy:work nutri:diet:calorie sys:related_to

def "phys:force:force" "Any interaction that, when unopposed, will change the motion of an object."
ln phys:force:force phys:mech:mass @depends_on
ln phys:force:force phys:mech:acceleration @depends_on

def "phys:force:friction" "The force resisting the relative motion of solid surfaces, fluid layers, and material elements sliding against each other."
ln phys:force:friction phys:energy:kinetic_energy @reduces

def "phys:force:gravity" "A natural phenomenon by which all things with mass or energy are brought toward one another."
ln phys:force:gravity astro:concept:orbit @maintains

def "phys:geom:spacetime_curvature" "The geometric distortion of spacetime caused by the presence of mass and energy."

def "phys:law:amperes_law" "Relates the integrated magnetic field around a closed loop to the electric current passing through the loop."
ln phys:law:amperes_law phys:em:magnetic_field @relates_to
ln phys:law:amperes_law phys:em:electric_current @relates_to

def "phys:law:conservation_of_energy" "The total energy of an isolated system remains constant; it is conserved over time."
ln phys:law:conservation_of_energy phys:energy:kinetic_energy @governs
ln phys:law:conservation_of_energy phys:energy:potential_energy @governs

def "phys:law:coulombs_law" "An experimental law of physics that quantifies the force between two stationary, electrically charged particles."
ln phys:law:coulombs_law phys:force:force @defines
ln phys:law:coulombs_law phys:charge:electric_charge @depends_on

def "phys:law:faradays_law" "A basic law of electromagnetism predicting how a magnetic field will interact with an electric circuit to produce an electromotive force (EMF)."
ln phys:law:faradays_law phys:em:magnetic_field @utilizes
ln phys:law:faradays_law phys:em:voltage @produces

def "phys:law:maxwells_equations" "A set of coupled partial differential equations that form the foundation of classical electromagnetism, classical optics, and electric circuits."
ln phys:law:maxwells_equations phys:em:electric_field @unifies
ln phys:law:maxwells_equations phys:em:magnetic_field @unifies
ln phys:law:maxwells_equations phys:em:electromagnetic_wave @predicts

def "phys:law:newtons_first_law" "An object either remains at rest or continues to move at a constant velocity, unless acted upon by a force (Law of Inertia)."

def "phys:law:newtons_second_law" "The vector sum of the forces F on an object equals mass m multiplied by acceleration a (F = ma)."
ln phys:law:newtons_second_law phys:force:force @defines

def "phys:law:newtons_third_law" "When one body exerts a force on a second body, the second body simultaneously exerts a force equal in magnitude and opposite in direction on the first body."

def "phys:mech:acceleration" "The rate of change of the velocity of an object with respect to time."

def "phys:mech:mass" "A property of a physical body and a measure of its resistance to acceleration when a net force is applied."

def "phys:mech:momentum" "The product of the mass and velocity of an object."
ln phys:mech:momentum phys:mech:mass @depends_on
ln phys:mech:momentum phys:mech:velocity @depends_on

def "phys:mech:velocity" "The rate of change of position with respect to a frame of reference, as a function of time."

def "phys:metric:chemical_shift" "The resonant frequency of a nucleus relative to a standard in a magnetic field, used in NMR."

def "phys:metric:wavenumber" "The spatial frequency of a wave, measured in cycles per unit distance (commonly cm⁻¹ in IR spectroscopy)."

def "phys:optics:absorption" "The physical process in which light energy is taken up by matter, typically exciting an electron to a higher energy state."

def "phys:optics:chromophore" "The part of a molecule responsible for its color by absorbing certain wavelengths of visible light."

def "phys:optics:conjugation" "A system of connected p-orbitals with delocalized electrons in a molecule, which lowers the overall energy and shifts light absorption into the visible spectrum."

def "phys:optics:d_d_transition" "Electronic transitions between the d-orbitals of transition metals, often responsible for the bright colors of coordination complexes."

def "phys:optics:fluorescence" "The emission of light by a substance that has absorbed light or other electromagnetic radiation, typically at a longer wavelength."

def "phys:phenomenon:brownian_motion" "The random, uncontrolled movement of particles in a fluid as they constantly collide with other molecules."

def "phys:phenomenon:coagulation" "The process by which colloidal particles come together to form larger masses or flocs."
ln phys:phenomenon:coagulation sci:cook:coagulation sys:same_as

def "phys:phenomenon:dialysis" "The separation of suspended colloidal particles from dissolved ions or molecules of small dimensions by means of their unequal rates of diffusion through the pores of semipermeable membranes."

def "phys:phenomenon:molecular_vibration" "Periodic motion of atoms of a molecule relative to each other (e.g., stretching, bending)."

def "phys:phenomenon:nuclear_spin" "An intrinsic form of angular momentum carried by atomic nuclei, exploited in NMR."

def "phys:phenomenon:tyndall_effect" "The scattering of light as a light beam passes through a colloid."

def "phys:qft:higgs_boson" "The fundamental particle associated with the Higgs field, which gives mass to other elementary particles."

def "phys:qft:quantum_field_theory" "The theoretical framework that combines classical field theory, special relativity, and quantum mechanics."

def "phys:qft:standard_model" "The theory describing three of the four fundamental forces in the universe and classifying all known elementary particles."

def "phys:rel:equivalence_principle" "The postulate that gravitational and inertial forces are of a similar nature and often indistinguishable."

def "phys:rel:galilean_invariance" "The law of mechanics that states the laws of motion are the same in all inertial frames."

def "phys:rel:general_relativity" "Einstein's theory of gravitation, which replaces the concept of force with the geometry of spacetime."
ln phys:rel:general_relativity astro:remnant:black_hole @predicts

def "phys:rel:gravitational_wave" "Ripples in the curvature of spacetime which propagate as waves, traveling outward from the source."

def "phys:rel:length_contraction" "The phenomenon that a moving object's length is measured to be shorter than its proper length."

def "phys:rel:lorentz_transformation" "The set of equations that relate the space and time coordinates of two observers moving at a constant velocity relative to each other."

def "phys:rel:mass_energy_equivalence" "E=mc², stating that mass and energy are interchangeable."

def "phys:rel:spacetime" "A mathematical model that combines the three dimensions of space and the one dimension of time into a single four-dimensional continuum."

def "phys:rel:special_relativity" "The physical theory of measurement in inertial frames of reference, based on the principle that the speed of light is constant."

def "phys:rel:time_dilation" "The phenomenon where time passes more slowly for an object in motion relative to an observer."

def "phys:spectrum:infrared" "Electromagnetic radiation with wavelengths longer than visible light (700 nm to 1 mm), often associated with heat."
ln phys:spectrum:infrared phys:em:electromagnetic_wave sys:is_a

def "phys:spectrum:radio_wave" "Electromagnetic radiation with the longest wavelengths in the electromagnetic spectrum."
ln phys:spectrum:radio_wave phys:em:electromagnetic_wave sys:is_a

def "phys:spectrum:ultraviolet" "Electromagnetic radiation with a wavelength from 10 nm to 400 nm, shorter than visible light."
ln phys:spectrum:ultraviolet phys:em:electromagnetic_wave sys:is_a

def "phys:spectrum:visible_light" "The portion of the electromagnetic spectrum that is visible to the human eye (approx. 400-700 nm)."
ln phys:spectrum:visible_light phys:em:electromagnetic_wave sys:is_a

def "phys:spectrum:x_ray" "Electromagnetic radiation of extremely short wavelength and high frequency."
ln phys:spectrum:x_ray phys:em:electromagnetic_wave sys:is_a

def "phys:state:gas" "A compressible fluid that will conform to the shape of its container and expand to fill it completely."

def "phys:state:liquid" "A nearly incompressible fluid that conforms to the shape of its container but retains a nearly constant volume."

def "phys:state:plasma" "A state of matter consisting of a gas of ions and free electrons, highly electrically conductive."

def "phys:state:solid" "A fundamental state of matter characterized by structural rigidity and resistance to a change of shape or volume."

def "phys:transition:boiling" "The rapid phase transition from liquid to gas or vapor; the reverse of condensation."
ln phys:transition:boiling phys:state:liquid @from
ln phys:transition:boiling phys:state:gas @to

def "phys:transition:condensation" "The change of the physical state of matter from the gas phase into the liquid phase."

def "phys:transition:freezing" "A phase transition where a liquid turns into a solid when its temperature is lowered below its freezing point."

def "phys:transition:melting" "A physical process that results in the phase transition of a substance from a solid to a liquid."
ln phys:transition:melting phys:state:solid @from
ln phys:transition:melting phys:state:liquid @to

def "phys:transition:sublimation" "The transition of a substance directly from the solid to the gas state, without passing through the liquid state."
ln phys:transition:sublimation phys:state:solid @from
ln phys:transition:sublimation phys:state:gas @to

def "phys:unif:electromagnetic_interaction" "The force acting between electrically charged particles."

def "phys:unif:grand_unified_theory" "Models that seek to unify the strong, weak, and electromagnetic forces into a single gauge group."

def "phys:unif:gravitational_interaction" "The force of attraction between all matter, described by general relativity."

def "phys:unif:quantum_gravity" "A field of theoretical physics that seeks to describe gravity according to the principles of quantum mechanics."

def "phys:unif:string_theory" "A theoretical framework in which point-like particles are replaced by one-dimensional objects called strings."

def "phys:unif:strong_interaction" "The force responsible for binding quarks together in hadrons (protons/neutrons)."

def "phys:unif:weak_interaction" "The force responsible for radioactive decay and nuclear fusion."
