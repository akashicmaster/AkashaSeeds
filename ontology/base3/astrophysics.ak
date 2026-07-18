# Akasha ontology — astrophysics & cosmology.
# astro: is rich in instances (constellations, moons, planets); this adds the
# physical concepts and processes. Bridged to astro:/phys:/math:/earthsci:. Base pack.

def "astrophys" "Astrophysics — the physics of stars, galaxies and the cosmos (天体物理学)."
ln astrophys astro:galaxy thesaurus:related
# ── cosmology ──
def "astrophys:cosmology" "The study of the universe's origin, structure and fate (宇宙論)."
ln astrophys:cosmology astrophys thesaurus:related
def "astrophys:big_bang" "The hot dense beginning from which the universe expanded (ビッグバン)."
ln astrophys:big_bang astrophys thesaurus:related
ln astrophys:big_bang astrophys:cosmology thesaurus:related
def "astrophys:cosmic_expansion" "The ongoing stretching of space, discovered via redshift."
ln astrophys:cosmic_expansion astrophys thesaurus:related
ln astrophys:cosmic_expansion astrophys:redshift thesaurus:related
def "astrophys:dark_matter" "Unseen mass whose gravity shapes galaxies (暗黒物質)."
ln astrophys:dark_matter astrophys thesaurus:related
def "astrophys:dark_energy" "The unknown agent accelerating cosmic expansion (暗黒エネルギー)."
ln astrophys:dark_energy astrophys thesaurus:related
def "astrophys:cosmic_microwave_background" "The relic radiation of the early universe (宇宙マイクロ波背景放射)."
ln astrophys:cosmic_microwave_background astrophys thesaurus:related
ln astrophys:cosmic_microwave_background astrophys:big_bang thesaurus:related
def "astrophys:redshift" "The lengthening of light from receding objects, a cosmic distance/speed clue (赤方偏移)."
ln astrophys:redshift astrophys thesaurus:related
def "astrophys:gravity" "The attraction between masses shaping cosmic structure (重力)."
ln astrophys:gravity astrophys thesaurus:related
ln astrophys:gravity mecheng:statics thesaurus:related
ln astrophys:gravity earthsci:tide thesaurus:related
# ── stars & objects ──
def "astrophys:stellar_evolution" "The life cycle of a star from cloud to remnant (恒星進化)."
ln astrophys:stellar_evolution astrophys thesaurus:related
def "astrophys:nuclear_fusion" "The fusing of nuclei that powers stars (核融合)."
ln astrophys:nuclear_fusion astrophys thesaurus:related
ln astrophys:nuclear_fusion energy:nuclear thesaurus:related
ln astrophys:nuclear_fusion astrophys:stellar_evolution thesaurus:related
def "astrophys:supernova" "The explosive death of a massive star, forging heavy elements (超新星)."
ln astrophys:supernova astrophys thesaurus:related
ln astrophys:supernova astro:nebula thesaurus:related
ln astrophys:supernova matsci:metal thesaurus:related
def "astrophys:black_hole" "A region whose gravity lets nothing escape (ブラックホール)."
ln astrophys:black_hole astrophys thesaurus:related
ln astrophys:black_hole astrophys:gravity thesaurus:related
def "astrophys:neutron_star" "An ultra-dense stellar remnant (中性子星)."
ln astrophys:neutron_star astrophys thesaurus:related
def "astrophys:nebula" "A cloud of gas and dust, a stellar nursery or remnant (星雲)."
ln astrophys:nebula astrophys thesaurus:related
def "astrophys:exoplanet" "A planet orbiting another star (系外惑星)."
ln astrophys:exoplanet astrophys thesaurus:related
ln astrophys:exoplanet astro:planet thesaurus:related
ln astrophys:exoplanet astrophys:habitable_zone thesaurus:related
def "astrophys:orbital_mechanics" "The motion of bodies under gravity (軌道力学)."
ln astrophys:orbital_mechanics astrophys thesaurus:related
ln astrophys:orbital_mechanics astro:moon thesaurus:related
ln astrophys:orbital_mechanics mecheng:dynamics thesaurus:related
ln astrophys:orbital_mechanics earthsci:tide thesaurus:related
def "astrophys:light_year" "The distance light travels in a year (光年)."
ln astrophys:light_year astrophys thesaurus:related
def "astrophys:spectroscopy_astro" "Reading composition and motion from starlight spectra (分光)."
ln astrophys:spectroscopy_astro astrophys thesaurus:related
ln astrophys:spectroscopy_astro matsci:materials_characterization thesaurus:related
ln astrophys:spectroscopy_astro astrophys:redshift thesaurus:related
def "astrophys:habitable_zone" "The orbital band where liquid water — and maybe life — can exist."
ln astrophys:habitable_zone astrophys thesaurus:related
ln astrophys:habitable_zone spacefood:mars_food thesaurus:related
ln astrophys:habitable_zone life:evolution thesaurus:related
