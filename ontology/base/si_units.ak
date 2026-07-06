# si_units.ak
# SI base units, named derived units, and CODATA fundamental constants
# Bureau International des Poids et Mesures (BIPM) — https://www.bipm.org/
# CODATA 2018 recommended values — NIST — https://physics.nist.gov/cuu/Constants/
# Public domain
#

# ── SI Base Units ──────────────────────────────────────────────────────────────

def "si:unit:metre" "SI base unit of length. Defined by fixing the speed of light c = 299,792,458 m/s exactly."
al si:unit:metre si:unit:meter
ln si:unit:metre si:unit sys:part_of

def "si:unit:kilogram" "SI base unit of mass. Defined by fixing the Planck constant h = 6.62607015×10⁻³⁴ J·s exactly."
ln si:unit:kilogram si:unit sys:part_of

def "si:unit:second" "SI base unit of time. Defined by 9,192,631,770 cycles of the Cs-133 ground-state hyperfine transition."
ln si:unit:second si:unit sys:part_of

def "si:unit:ampere" "SI base unit of electric current. Defined by fixing the elementary charge e = 1.602176634×10⁻¹⁹ C exactly."
ln si:unit:ampere si:unit sys:part_of

def "si:unit:kelvin" "SI base unit of thermodynamic temperature. Defined by fixing the Boltzmann constant k = 1.380649×10⁻²³ J/K exactly."
ln si:unit:kelvin si:unit sys:part_of

def "si:unit:mole" "SI base unit of amount of substance. Defined by fixing the Avogadro constant Nₐ = 6.02214076×10²³ mol⁻¹ exactly."
ln si:unit:mole si:unit sys:part_of

def "si:unit:candela" "SI base unit of luminous intensity. Defined by fixing the luminous efficacy Kcd = 683 lm/W at 540 THz exactly."
ln si:unit:candela si:unit sys:part_of

# ── SI Derived Units (named) ───────────────────────────────────────────────────

def "si:unit:radian" "SI unit of plane angle. Dimensionless (m/m). 2π rad = full circle."
al si:unit:radian si:unit:rad
ln si:unit:radian si:unit sys:part_of

def "si:unit:steradian" "SI unit of solid angle. Dimensionless (m²/m²). 4π sr = full sphere."
al si:unit:steradian si:unit:sr
ln si:unit:steradian si:unit sys:part_of

def "si:unit:hertz" "SI unit of frequency. 1 Hz = 1 s⁻¹ (cycles per second)."
al si:unit:hertz si:unit:hz
ln si:unit:hertz si:unit sys:part_of

def "si:unit:newton" "SI unit of force. 1 N = 1 kg⋅m⋅s⁻². Named after Isaac Newton."
al si:unit:newton si:unit:n
ln si:unit:newton si:unit sys:part_of

def "si:unit:pascal" "SI unit of pressure and stress. 1 Pa = 1 N/m² = 1 kg⋅m⁻¹⋅s⁻²."
al si:unit:pascal si:unit:pa
ln si:unit:pascal si:unit sys:part_of

def "si:unit:joule" "SI unit of energy, work, and heat. 1 J = 1 N⋅m = 1 kg⋅m²⋅s⁻²."
al si:unit:joule si:unit:j
ln si:unit:joule si:unit sys:part_of

def "si:unit:watt" "SI unit of power (rate of energy transfer). 1 W = 1 J/s = 1 kg⋅m²⋅s⁻³."
al si:unit:watt si:unit:w
ln si:unit:watt si:unit sys:part_of

def "si:unit:coulomb" "SI unit of electric charge. 1 C = 1 A⋅s. Approximately 6.242×10¹⁸ elementary charges."
al si:unit:coulomb si:unit:c
ln si:unit:coulomb si:unit sys:part_of

def "si:unit:volt" "SI unit of electric potential difference (EMF). 1 V = 1 J/C = 1 kg⋅m²⋅s⁻³⋅A⁻¹."
al si:unit:volt si:unit:v
ln si:unit:volt si:unit sys:part_of

def "si:unit:farad" "SI unit of electrical capacitance. 1 F = 1 C/V = 1 kg⁻¹⋅m⁻²⋅s⁴⋅A²."
al si:unit:farad si:unit:f
ln si:unit:farad si:unit sys:part_of

def "si:unit:ohm" "SI unit of electrical resistance. 1 Ω = 1 V/A = 1 kg⋅m²⋅s⁻³⋅A⁻²."
al si:unit:ohm si:unit:ohm_symbol
ln si:unit:ohm si:unit sys:part_of

def "si:unit:siemens" "SI unit of electrical conductance (reciprocal of ohm). 1 S = 1 A/V = 1 kg⁻¹⋅m⁻²⋅s³⋅A²."
al si:unit:siemens si:unit:s_conductance
ln si:unit:siemens si:unit sys:part_of

def "si:unit:weber" "SI unit of magnetic flux. 1 Wb = 1 V⋅s = 1 kg⋅m²⋅s⁻²⋅A⁻¹."
al si:unit:weber si:unit:wb
ln si:unit:weber si:unit sys:part_of

def "si:unit:tesla" "SI unit of magnetic flux density (magnetic field strength). 1 T = 1 Wb/m² = 1 kg⋅s⁻²⋅A⁻¹."
al si:unit:tesla si:unit:t_field
ln si:unit:tesla si:unit sys:part_of

def "si:unit:henry" "SI unit of electrical inductance. 1 H = 1 Wb/A = 1 kg⋅m²⋅s⁻²⋅A⁻²."
al si:unit:henry si:unit:h_inductance
ln si:unit:henry si:unit sys:part_of

def "si:unit:lumen" "SI unit of luminous flux. 1 lm = 1 cd⋅sr."
al si:unit:lumen si:unit:lm
ln si:unit:lumen si:unit sys:part_of

def "si:unit:lux" "SI unit of illuminance (luminous flux per unit area). 1 lx = 1 lm/m²."
al si:unit:lux si:unit:lx
ln si:unit:lux si:unit sys:part_of

def "si:unit:becquerel" "SI unit of radioactivity. 1 Bq = 1 s⁻¹ (one nuclear decay per second)."
al si:unit:becquerel si:unit:bq
ln si:unit:becquerel si:unit sys:part_of

def "si:unit:gray" "SI unit of absorbed ionising radiation dose. 1 Gy = 1 J/kg = 1 m²⋅s⁻²."
al si:unit:gray si:unit:gy
ln si:unit:gray si:unit sys:part_of

def "si:unit:sievert" "SI unit of ionising radiation dose equivalent (weighted by biological effect). 1 Sv = 1 J/kg."
al si:unit:sievert si:unit:sv
ln si:unit:sievert si:unit sys:part_of

def "si:unit:katal" "SI unit of catalytic activity. 1 kat = 1 mol⋅s⁻¹ (moles of substrate converted per second)."
al si:unit:katal si:unit:kat
ln si:unit:katal si:unit sys:part_of

# ── Namespace anchor ───────────────────────────────────────────────────────────

def "si:unit" "The International System of Units (SI) — 7 base units and 22 named derived units defined by the BIPM."
ln si:unit phys:measurement sys:part_of

# ── CODATA Fundamental Physical Constants (2018 values) ───────────────────────

def "phys:const:c" "Speed of light in vacuum. c = 299,792,458 m/s (exact, defines the metre)."
al phys:const:c phys:const:speed_of_light
ln phys:const:c phys:const sys:part_of

def "phys:const:h" "Planck constant. h = 6.62607015×10⁻³⁴ J·s (exact, defines the kilogram)."
al phys:const:h phys:const:planck
ln phys:const:h phys:const sys:part_of

def "phys:const:hbar" "Reduced Planck constant (Dirac constant). ħ = h/2π = 1.054571817×10⁻³⁴ J·s."
al phys:const:hbar phys:const:dirac
ln phys:const:hbar phys:const sys:part_of

def "phys:const:e" "Elementary charge (charge of one proton). e = 1.602176634×10⁻¹⁹ C (exact, defines the ampere)."
al phys:const:e phys:const:elementary_charge
ln phys:const:e phys:const sys:part_of

def "phys:const:k" "Boltzmann constant. k = 1.380649×10⁻²³ J/K (exact, defines the kelvin)."
al phys:const:k phys:const:boltzmann
ln phys:const:k phys:const sys:part_of

def "phys:const:na" "Avogadro constant. Nₐ = 6.02214076×10²³ mol⁻¹ (exact, defines the mole)."
al phys:const:na phys:const:avogadro
ln phys:const:na phys:const sys:part_of

def "phys:const:g" "Newtonian gravitational constant. G = 6.67430×10⁻¹¹ m³⋅kg⁻¹⋅s⁻² (CODATA 2018, relative uncertainty 2.2×10⁻⁵)."
al phys:const:g phys:const:gravitational_constant
ln phys:const:g phys:const sys:part_of

def "phys:const:alpha" "Fine-structure constant. α ≈ 1/137.035999084 ≈ 7.2973525693×10⁻³ (dimensionless; characterises electromagnetic coupling)."
al phys:const:alpha phys:const:fine_structure
ln phys:const:alpha phys:const sys:part_of

def "phys:const:me" "Electron rest mass. mₑ = 9.1093837015×10⁻³¹ kg = 0.51099895 MeV/c²."
al phys:const:me phys:const:electron_mass
ln phys:const:me phys:const sys:part_of

def "phys:const:mp" "Proton rest mass. mₚ = 1.67262192369×10⁻²⁷ kg = 938.27208816 MeV/c²."
al phys:const:mp phys:const:proton_mass
ln phys:const:mp phys:const sys:part_of

def "phys:const:mn" "Neutron rest mass. mₙ = 1.67492749804×10⁻²⁷ kg = 939.56542052 MeV/c²."
al phys:const:mn phys:const:neutron_mass
ln phys:const:mn phys:const sys:part_of

def "phys:const:u" "Unified atomic mass unit (dalton). u = 1.66053906660×10⁻²⁷ kg = 931.49410242 MeV/c²."
al phys:const:u phys:const:atomic_mass_unit
al phys:const:u phys:const:dalton
ln phys:const:u phys:const sys:part_of

def "phys:const:r" "Molar gas constant. R = Nₐ k = 8.314462618 J⋅mol⁻¹⋅K⁻¹."
al phys:const:r phys:const:gas_constant
ln phys:const:r phys:const sys:part_of

def "phys:const:sigma" "Stefan-Boltzmann constant. σ = 5.670374419×10⁻⁸ W⋅m⁻²⋅K⁻⁴ (relates blackbody radiance to temperature)."
al phys:const:sigma phys:const:stefan_boltzmann
ln phys:const:sigma phys:const sys:part_of

def "phys:const:epsilon0" "Vacuum electric permittivity (electric constant). ε₀ = 8.8541878128×10⁻¹² F⋅m⁻¹."
al phys:const:epsilon0 phys:const:permittivity_vacuum
ln phys:const:epsilon0 phys:const sys:part_of

def "phys:const:mu0" "Vacuum magnetic permeability (magnetic constant). μ₀ = 1.25663706212×10⁻⁶ N⋅A⁻²."
al phys:const:mu0 phys:const:permeability_vacuum
ln phys:const:mu0 phys:const sys:part_of

def "phys:const:a0" "Bohr radius. a₀ = 5.29177210903×10⁻¹¹ m (most probable distance of electron from proton in ground-state hydrogen)."
al phys:const:a0 phys:const:bohr_radius
ln phys:const:a0 phys:const sys:part_of

def "phys:const:mub" "Bohr magneton. μB = 9.2740100783×10⁻²⁴ J⋅T⁻¹ (natural unit of magnetic moment for electrons)."
al phys:const:mub phys:const:bohr_magneton
ln phys:const:mub phys:const sys:part_of

def "phys:const:rinf" "Rydberg constant. R∞ = 10,973,731.568160 m⁻¹ (governs hydrogen spectral line positions)."
al phys:const:rinf phys:const:rydberg
ln phys:const:rinf phys:const sys:part_of

def "phys:const:f" "Faraday constant. F = Nₐ e = 96,485.33212 C⋅mol⁻¹ (charge of one mole of electrons)."
al phys:const:f phys:const:faraday
ln phys:const:f phys:const sys:part_of

def "phys:const:ry" "Rydberg unit of energy. Ry = hcR∞ = 13.605693122994 eV = 2.1798723611×10⁻¹⁸ J."
al phys:const:ry phys:const:rydberg_energy
ln phys:const:ry phys:const sys:part_of

# ── Namespace anchor ───────────────────────────────────────────────────────────

def "phys:const" "Fundamental physical constants — CODATA 2018 recommended values published by NIST."
