# Akasha ontology — life sciences: cell, molecular biology, genetics, evolution.
# Deepens the thin bio: layer, bridged to chem:/med:/nutrisci:/futureag:/ecol:.
# Base pack.

def "life" "Life science — the study of living organisms and their processes (生命科学)."
# ── cell & molecular biology ──
def "life:cell" "The basic unit of life (細胞)."
ln life:cell life thesaurus:related
def "life:cell_membrane" "The boundary controlling what enters and leaves a cell."
ln life:cell_membrane life thesaurus:related
def "life:nucleus_cell" "The organelle housing the cell's DNA."
ln life:nucleus_cell life thesaurus:related
def "life:mitochondria" "The cell's energy-producing organelles (ミトコンドリア)."
ln life:mitochondria life thesaurus:related
ln life:mitochondria life:cellular_respiration thesaurus:related
def "life:ribosome" "The organelle that builds proteins."
ln life:ribosome life thesaurus:related
def "life:molecular_biology" "The study of biological molecules and their interactions (分子生物学)."
ln life:molecular_biology life thesaurus:related
def "life:dna" "The double-helix molecule carrying genetic instructions (デオキシリボ核酸)."
ln life:dna life thesaurus:related
ln life:dna life:genetics thesaurus:related
ln life:dna life:molecular_biology thesaurus:related
def "life:rna" "The molecule translating genes into proteins."
ln life:rna life thesaurus:related
def "life:protein_synthesis" "Building proteins from a gene via transcription and translation."
ln life:protein_synthesis life thesaurus:related
ln life:protein_synthesis life:dna thesaurus:related
def "life:enzyme" "A protein catalysing a biochemical reaction (酵素)."
ln life:enzyme life thesaurus:related
ln life:enzyme foodsci:fermentation_science thesaurus:related
ln life:enzyme chemeng:catalysis thesaurus:related
ln life:enzyme med:pharma:pharmacodynamics thesaurus:related
def "life:metabolism" "The chemical reactions sustaining life (代謝)."
ln life:metabolism life thesaurus:related
ln life:metabolism nutrisci:metabolomics thesaurus:related
ln life:metabolism med:basic:physiology thesaurus:related
def "life:photosynthesis" "Converting light, water and CO2 into sugar and oxygen (光合成)."
ln life:photosynthesis life thesaurus:related
ln life:photosynthesis ecol:producer thesaurus:related
ln life:photosynthesis ecol:carbon_cycle thesaurus:related
ln life:photosynthesis ecol:ecosystem thesaurus:related
def "life:cellular_respiration" "Releasing energy from food in cells."
ln life:cellular_respiration life thesaurus:related
# ── genetics ──
def "life:genetics" "The study of heredity and variation (遺伝学)."
ln life:genetics life thesaurus:related
def "life:gene" "A unit of heredity coding a trait (遺伝子)."
ln life:gene life thesaurus:related
def "life:allele" "A variant form of a gene."
ln life:allele life thesaurus:related
def "life:chromosome" "A packaged strand of DNA (染色体)."
ln life:chromosome life thesaurus:related
def "life:genotype" "An organism's genetic makeup."
ln life:genotype life thesaurus:related
def "life:phenotype" "The observable traits arising from genotype and environment."
ln life:phenotype life thesaurus:related
def "life:mutation" "A change in DNA sequence, the raw material of evolution (突然変異)."
ln life:mutation life thesaurus:related
ln life:mutation life:genetics thesaurus:related
def "life:heredity" "The passing of traits from parents to offspring (遺伝)."
ln life:heredity life thesaurus:related
ln life:heredity kin:parent_of thesaurus:related
ln life:heredity kin:descendant_of thesaurus:related
def "life:genomics" "The study of whole genomes (ゲノミクス)."
ln life:genomics life thesaurus:related
ln life:genomics nutrisci:nutrigenomics thesaurus:related
ln life:genomics rdm:dataset thesaurus:related
def "life:epigenetics" "Heritable changes in gene expression without DNA change (エピジェネティクス)."
ln life:epigenetics life thesaurus:related
ln life:epigenetics nutrisci:nutrigenetics thesaurus:related
def "life:gene_editing" "Directly altering DNA sequences (CRISPR) (ゲノム編集)."
ln life:gene_editing life thesaurus:related
ln life:gene_editing futureag:gene_editing_crops thesaurus:related
ln life:gene_editing futurefood:cultured_meat thesaurus:related
# ── evolution & microbiology ──
def "life:evolution" "The change in heritable traits of populations over generations (進化)."
ln life:evolution life thesaurus:related
def "life:natural_selection" "Differential survival and reproduction shaping species (自然選択)."
ln life:natural_selection life thesaurus:related
ln life:natural_selection life:evolution thesaurus:related
def "life:adaptation" "A trait improving fit to the environment (適応)."
ln life:adaptation life thesaurus:related
ln life:adaptation life:natural_selection thesaurus:related
def "life:speciation" "The origin of new species (種分化)."
ln life:speciation life thesaurus:related
def "life:phylogeny" "The evolutionary tree of relationships (系統樹)."
ln life:phylogeny life thesaurus:related
ln life:phylogeny dh:network thesaurus:related
ln life:phylogeny sys:network thesaurus:related
def "life:common_descent" "The principle that all life shares ancestry."
ln life:common_descent life thesaurus:related
def "life:fitness" "Reproductive success relative to others."
ln life:fitness life thesaurus:related
def "life:microbiology" "The study of microorganisms (微生物学)."
ln life:microbiology life thesaurus:related
def "life:bacteria" "Single-celled prokaryotes, agents of disease and fermentation (細菌)."
ln life:bacteria life thesaurus:related
ln life:bacteria foodsci:lactic_acid_bacteria thesaurus:related
ln life:bacteria enveng:bioremediation thesaurus:related
def "life:virus" "A sub-cellular infectious agent (ウイルス)."
ln life:virus life thesaurus:related
ln life:virus foodsafe:pathogen thesaurus:related
ln life:virus med:specialty:public_health_medicine thesaurus:related
def "life:immunity" "The body's defence against pathogens (免疫)."
ln life:immunity life thesaurus:related
ln life:immunity med:basic:immunology thesaurus:related
ln life:immunity nutrisci:functional_food thesaurus:related
