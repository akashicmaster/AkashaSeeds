wrote docs/ontology/pack-manifest.md
  447 packs listed, grand total 200,132 steps
 re-run to refresh after editing packs.

A **step** is one executable `.ak` statement — `def` (define an atom), `ln` (typed
link), `al` (alias), or `set.add` (add to a collection). Comments and blank lines
are excluded. Steps map one-to-one onto the JCL job steps the loader executes, so
the step count is a direct measure of how much work a pack costs to load.

**Load behaviour differs by edition** — the two columns show what happens at startup:

- **Seeds** — `●` loads at startup (base packs) · `○` bundled but OFF, enable with
  `onto.pack.enable name=<pack>` · `–` not shipped with Seeds (the heavy **nutrition**
  pack is Thesaurus-only).
- **Thesaurus** — `●` every pack loads automatically at startup (the `load_all` flag,
  in REGISTRY order); there is no opt-in step.

## Packages (REGISTRY order)

| pack | Seeds | Thes. | files | def | ln | al | set | steps | content |
|---|:--:|:--:|--:|--:|--:|--:|--:|--:|---|
| lexicon | ● | ● | 3 | 612 | 432 | — | 612 | **1,656** | First-class, self-describing definitio |
| base1 | ● | ● | 65 | 9,596 | 7,561 | 1,125 | 138 | **18,420** | Words, feelings and the everyday table |
| base2 | ● | ● | 67 | 1,840 | 4,565 | 251 | 1,226 | **7,882** | The human world grows: home & househol |
| base3 | ● | ● | 72 | 4,941 | 8,243 | 2,362 | 2,467 | **18,013** | The canopy of knowledge: the professio |
| vocab | ○ | ● | 10 | 19,025 | 5,520 | — | — | **24,545** | Extended vocabulary building on word_c |
| world | ○ | ● | 54 | 4,335 | 9,075 | 88 | 1,993 | **15,491** | Geography (countries, maps), world his |
| tech | ○ | ● | 61 | 2,303 | 2,585 | — | 2,181 | **7,069** | Computing, software engineering, netwo |
| domain | ○ | ● | 45 | 1,606 | 1,739 | — | 854 | **4,199** | Specialized domains: medicine, chemist |
| archaeology | ○ | ● | — | — | — | — | — | **—** | ~38,000 ancient Greek, Roman, and Medi |
| art | ○ | ● | 3 | 151 | 345 | — | 137 | **633** | Painting movements from Palaeolithic c |
| biology | ○ | ● | — | — | — | — | — | **—** | Taxonomic hierarchy for vertebrates, v |
| film | ○ | ● | 3 | 145 | 157 | 3 | 137 | **442** | Historical film movements (German Expr |
| geology | ○ | ● | 3 | 72 | 60 | 1 | 72 | **205** | Complete ICS 2024 geological time scal |
| law | ○ | ● | 3 | 162 | 305 | 18 | 162 | **647** | Legal traditions from ancient Sumer to |
| literature | ○ | ● | — | — | — | — | — | **—** | Classical and historical literary work |
| medicine | ○ | ● | — | — | — | — | — | **—** | Medical terms from NLM MeSH: diseases, |
| music | ○ | ● | 4 | 228 | 322 | — | 213 | **763** | Classical and ethnic music traditions  |
| people | ○ | ● | 1 | 77 | 103 | — | 77 | **257** | Occupation/field taxonomy (philosopher |
| resources | ○ | ● | 2 | 68 | 66 | — | 68 | **202** | Energy resources (fossil fuels, nuclea |
| space | ○ | ● | 1 | 63 | 107 | 29 | — | **199** | Solar system objects (planets, moons,  |
| war | ○ | ● | 4 | 147 | 221 | — | 147 | **515** | Military theory (Sun Tzu, Clausewitz,  |
| weather | ○ | ● | 1 | 73 | 69 | 5 | — | **147** | WMO cloud genera, precipitation types, |
| wine | ○ | ● | 21 | 684 | 888 | — | 301 | **1,873** | Drinks & tasting from the eater's side |
| curation | ● | ● | 4 | 29 | 24 | — | 29 | **82** | A small relation-web (a patriline thro |
| recipe | ● | ● | 1 | 15 | — | 15 | — | **30** | The shared building blocks the recipe  |
| nutrition | – | ● | 9 | 11,984 | 18,306 | 9,414 | 3,392 | **43,096** | ~8,800 foods with full nutrient profil |
| drinks_c | ○ | ● | 4 | 12,335 | 14,503 | 409 | 23,910 | **51,157** | Comprehensive C-tier beverage catalogu |
| smallplates_c | ○ | ● | 1 | 31 | 53 | — | 64 | **148** | Cross-cultural small-plate / finger-fo |
| sweets_bread_c | ○ | ● | 1 | 39 | 58 | — | 71 | **168** | Two dish families in one pack: sweets  |
| kitchen_index | ○ | ● | 4 | — | — | — | 2,293 | **2,293** | Lightweight membership sets that power |

## Totals

| group | files | steps |
|---|--:|--:|
| Seeds startup (base, autoload, no nutrition) | 212 | **46,083** |
| opt-in specialist packs (Seeds: on demand) | 235 | **154,049** |
| nutrition (Thesaurus-only) | 9 | **43,096** |
| **Thesaurus full load (every pack)** | **447** | **200,132** |

## Approximate load time

At the reference rate of ~40 steps/second (single-thread serial write path,
measured on the soak-test VM):

| edition · scenario | steps | ~time |
|---|--:|--:|
| **Seeds** startup (base only) | 46,083 | ~19 min |
| **Seeds** + all opt-in packs enabled | 157,036 | ~65 min |
| **Thesaurus** startup = full load (every pack, incl. nutrition) | 200,132 | ~83 min |

## Notes

- **The six autoload packs are `lexicon`, `base1`, `base2`, `base3`, `curation`, `recipe`.**
  `nutrition` is NOT autoload — it is an opt-in tier-C pack (USDA FoodData Central) that
  ships only with the **Thesaurus** tier; the Seeds edition omits it, so a Seeds startup
  is the six autoload packs alone.
- **Zero-file packs** (archaeology, biology, literature, medicine) are reserved
  REGISTRY slots for external gazetteers (Pleiades, NCBI Taxonomy, Project Gutenberg,
  MeSH). They are registered but carry no `.ak` data yet, so they cost 0 steps even
  under `load_all`.
- Loading is idempotent and content-addressed: enabling an overlapping pack never
  creates duplicates.

