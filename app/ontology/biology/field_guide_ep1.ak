# The Plant Geek — field guide, episode 1: the hedge bank and the wayside
#
# The episode Set `bio:plants:field_guide:ep1` that `app/config/workbench/workloads/plant_geek.json`
# pins. The programme's declaration has carried the line "Residue, target: a `biology` episode
# pack, as its own delivery" since it was switched on; this is that delivery.
#
# WHAT A RECORD MUST CARRY, and why it is shaped this way. The station reads a plain-text body as
# "an ordinary ontology atom's description, which is already a record of the thing" — the atom's
# own alias is the anchor, and nothing is parsed out of the text. The three roles then read ONE
# record between them, so everything all three are allowed to say has to be IN it:
#
#   Keyer   may name the species and its place in the taxonomy, read the RECORDED characters, and
#           give a one-line setting — and must not "guess a habitat or a range that is not
#           recorded". So every entry states its characters, its habitat and its range outright.
#   Walker  asks one ordinary question. Nothing is written for it; a record with a real diagnostic
#           character is what gives it something to ask about.
#   Geek    answers, then supplies "habitat, range and naming history", then opens ONE door. So
#           every entry carries its naming history, and the doors are real links below.
#
# WHAT A RECORD MUST NOT CARRY. All three roles are forbidden foraging, edibility, medicinal and
# dosage claims. That is a contract on the speaker, but a record that volunteered a use would be
# putting the words in reach — so no entry here states one, for any species, including the ones
# where a reader will expect it. The guide describes what a plant IS and where it grows.
#
# The species chosen are the ones an ordinary walker in temperate Europe actually meets on a hedge
# bank, and each was picked for a character you can SEE without a lens — which is what makes an
# episode audible rather than a recitation of names.

# ── the spine: where these ranks hang ───────────────────────────────────────────────────────────
def "bio:kingdom:plantae" "Plantae — the plant kingdom: multicellular eukaryotes with cellulose cell walls and plastids, most of them photosynthetic. The top of the ranks this pack records."
al bio:kingdom:plantae plantae
set.add name="bio:plants:field_guide:ep1:spine" id="bio:kingdom:plantae"

def "bio:clade:angiosperms" "Angiosperms — the flowering plants: seeds enclosed in a carpel, and a flower as the reproductive structure. Every species in this episode is one. Placed as a clade rather than a rank, because that is what it is: the ranks between it and order are not recorded here."
al bio:clade:angiosperms angiosperms
ln bio:clade:angiosperms bio:kingdom:plantae sys:is_a
set.add name="bio:plants:field_guide:ep1:spine" id="bio:clade:angiosperms"

# ── orders ──────────────────────────────────────────────────────────────────────────────────────
def "bio:order:rosales" "Rosales — an order of angiosperms holding the roses, elms, figs, buckthorns and nettles. Its members are otherwise unalike enough that the grouping is a molecular result rather than something a walker would guess."
al bio:order:rosales rosales
ln bio:order:rosales bio:clade:angiosperms sys:is_a

def "bio:order:lamiales" "Lamiales — an order of angiosperms holding the mints, figworts, plantains, olives and foxgloves. Largely plants with bilaterally symmetrical flowers, though the plantains have given that up for wind."
al bio:order:lamiales lamiales
ln bio:order:lamiales bio:clade:angiosperms sys:is_a

def "bio:order:asterales" "Asterales — an order of angiosperms dominated by the daisy family, whose innovation is the head: many small flowers packed into one structure that a visitor reads as a single flower."
al bio:order:asterales asterales
ln bio:order:asterales bio:clade:angiosperms sys:is_a

def "bio:order:geraniales" "Geraniales — a small order of angiosperms holding the cranesbills and storksbills, named for fruits shaped like a bird's beak."
al bio:order:geraniales geraniales
ln bio:order:geraniales bio:clade:angiosperms sys:is_a

def "bio:order:caryophyllales" "Caryophyllales — a large order of angiosperms holding the pinks and campions, the docks, the goosefoots and the cacti. Many of its members tolerate ground that other plants will not."
al bio:order:caryophyllales caryophyllales
ln bio:order:caryophyllales bio:clade:angiosperms sys:is_a

def "bio:order:alismatales" "Alismatales — an order of monocots, mostly of water and wet ground, holding the water-plantains, the pondweeds, the seagrasses and the arums."
al bio:order:alismatales alismatales
ln bio:order:alismatales bio:clade:angiosperms sys:is_a

def "bio:order:brassicales" "Brassicales — an order of angiosperms holding the cabbage family and its relatives, united by glucosinolates: the mustard-oil chemistry that gives the group its sharp smell when a leaf is broken."
al bio:order:brassicales brassicales
ln bio:order:brassicales bio:clade:angiosperms sys:is_a

def "bio:order:apiales" "Apiales — an order of angiosperms holding the carrot family and the ivies, many of them with flowers gathered into umbels."
al bio:order:apiales apiales
ln bio:order:apiales bio:clade:angiosperms sys:is_a

# ── families ────────────────────────────────────────────────────────────────────────────────────
def "bio:family:urticaceae" "Urticaceae — the nettle family: mostly herbs with small, wind-pollinated, petal-less flowers, many of them armed with stinging hairs."
al bio:family:urticaceae urticaceae
ln bio:family:urticaceae bio:order:rosales sys:is_a

def "bio:family:plantaginaceae" "Plantaginaceae — the plantain family as now circumscribed: a large family that took in the speedwells, foxgloves and toadflaxes when molecular work broke up the old figworts."
al bio:family:plantaginaceae plantaginaceae
ln bio:family:plantaginaceae bio:order:lamiales sys:is_a

def "bio:family:asteraceae" "Asteraceae — the daisy family, one of the two largest families of flowering plants. Its flowers are gathered into a head (a capitulum) subtended by bracts, so what reads as one flower is a crowd of them."
al bio:family:asteraceae asteraceae
ln bio:family:asteraceae bio:order:asterales sys:is_a

def "bio:family:geraniaceae" "Geraniaceae — the cranesbill family: five-petalled flowers and a fruit with a long beak that splits and flings the seeds away from the parent."
al bio:family:geraniaceae geraniaceae
ln bio:family:geraniaceae bio:order:geraniales sys:is_a

def "bio:family:caryophyllaceae" "Caryophyllaceae — the pink family: opposite leaves at swollen nodes, and five petals that are very often notched or deeply cut at the tip."
al bio:family:caryophyllaceae caryophyllaceae
ln bio:family:caryophyllaceae bio:order:caryophyllales sys:is_a

def "bio:family:araceae" "Araceae — the arum family: the inflorescence is a spadix, a fleshy spike of tiny flowers, wrapped in a modified leaf called a spathe. Several members generate heat and a carrion smell to draw insects."
al bio:family:araceae araceae
ln bio:family:araceae bio:order:alismatales sys:is_a

def "bio:family:brassicaceae" "Brassicaceae — the cabbage family: four petals set in a cross, six stamens of which four are long and two short, and a fruit that splits into two valves off a persistent partition."
al bio:family:brassicaceae brassicaceae
ln bio:family:brassicaceae bio:order:brassicales sys:is_a

def "bio:family:araliaceae" "Araliaceae — the ivy family: woody climbers, shrubs and trees with flowers in umbels and, in several genera, a sharp change of leaf shape between the climbing and the flowering stage."
al bio:family:araliaceae araliaceae
ln bio:family:araliaceae bio:order:apiales sys:is_a

# ── genera ──────────────────────────────────────────────────────────────────────────────────────
def "bio:genus:urtica" "Urtica — the nettles: herbs with opposite toothed leaves and stinging hairs, the flowers in hanging greenish clusters from the leaf axils. The name is Latin, from urere, to burn."
al bio:genus:urtica urtica
ln bio:genus:urtica bio:family:urticaceae sys:is_a

def "bio:genus:plantago" "Plantago — the plantains of the northern waysides: a basal rosette of strongly ribbed leaves and a leafless stalk carrying a dense spike of small wind-pollinated flowers. Nothing to do with the banana of the same English name."
al bio:genus:plantago plantago
ln bio:genus:plantago bio:family:plantaginaceae sys:is_a

def "bio:genus:achillea" "Achillea — the yarrows: aromatic perennials with finely divided leaves and small heads gathered into a flat-topped cluster. Named for Achilles."
al bio:genus:achillea achillea
ln bio:genus:achillea bio:family:asteraceae sys:is_a

def "bio:genus:geranium" "Geranium — the cranesbills: five-petalled flowers with a radially symmetrical face and a long-beaked fruit. Not the scarlet pot 'geranium' of a window box, which is Pelargonium."
al bio:genus:geranium geranium
ln bio:genus:geranium bio:family:geraniaceae sys:is_a

def "bio:genus:silene" "Silene — the campions and catchflies: opposite leaves, a tubular or inflated calyx, and five petals that are usually notched."
al bio:genus:silene silene
ln bio:genus:silene bio:family:caryophyllaceae sys:is_a

def "bio:genus:arum" "Arum — the arums: a spathe wrapped round a spadix in spring, and a spike of berries left standing bare when the leaves have gone."
al bio:genus:arum arum
ln bio:genus:arum bio:family:araceae sys:is_a

def "bio:genus:cardamine" "Cardamine — the bittercresses: crucifers with pinnate leaves, mostly of damp ground and streamsides."
al bio:genus:cardamine cardamine
ln bio:genus:cardamine bio:family:brassicaceae sys:is_a

def "bio:genus:hedera" "Hedera — the ivies: evergreen woody climbers that hold on with adventitious rootlets and change their leaf shape when they begin to flower."
al bio:genus:hedera hedera
ln bio:genus:hedera bio:family:araliaceae sys:is_a

# ── the doors: characters a walker can be shown twice ───────────────────────────────────────────
# The Geek is allowed to "open ONE door", and a door has to lead somewhere that exists. These are
# the characters this episode can show in more than one species, so the door is a comparison the
# listener can check rather than a name they have to take on trust.
def "bio:trait:dioecy" "Dioecy — a species whose male and female flowers are on SEPARATE plants, so any one individual is one sex. Latin-Greek for 'two households'. It appears twice in this episode, in plants that are not otherwise related: the common nettle and the red campion. Uncommon in flowering plants as a whole, where most flowers carry both."
al bio:trait:dioecy dioecy
set.add name="bio:plants:field_guide:ep1:traits" id="bio:trait:dioecy"

def "bio:trait:heterophylly" "Heterophylly — one plant bearing leaves of more than one shape, on different shoots or at different stages. In ivy the split is between the climbing shoots and the flowering ones, and it is sharp enough that the two have been taken for different plants."
al bio:trait:heterophylly heterophylly
set.add name="bio:plants:field_guide:ep1:traits" id="bio:trait:heterophylly"

def "bio:trait:thermogenesis" "Thermogenesis — a plant generating its own heat. In the arums the spadix warms well above the surrounding air for a few hours, which volatilises the scent that brings the pollinators in. A flower that is briefly warm to the touch is a thing worth saying out loud."
al bio:trait:thermogenesis thermogenesis
set.add name="bio:plants:field_guide:ep1:traits" id="bio:trait:thermogenesis"

# ── the episode ─────────────────────────────────────────────────────────────────────────────────
# Members of `bio:plants:field_guide:ep1`. The station keys them out in Set order, one per airing,
# and the cursor is derived from the bench's own record — so this order is the running order.

def "bio:species:urtica_dioica" "Urtica dioica — common nettle. Urticaceae, order Rosales. Characters: a square-sectioned, usually unbranched stem to about 1.5 m; leaves OPPOSITE, stalked, coarsely toothed, pointed, the base heart-shaped; the whole plant clothed in two kinds of hair, ordinary ones and brittle stinging hairs whose tip breaks off against skin; flowers tiny, greenish, without petals, hanging in branched catkin-like clusters from the leaf axils; the species is usually dioecious, so a stand is male or female, and the male's stamens spring open and throw pollen to the wind. Setting: deep, damp, nitrogen-rich, disturbed ground — farmyards, middens, riverbanks, the shaded foot of a wall, and the ground where people have lived. Range: native across temperate Europe and Asia and into North Africa, carried by settlement almost everywhere else. Naming: urtica from Latin urere, to burn; dioica from the Greek for 'two households', which is the character itself written into the name."
al bio:species:urtica_dioica nettle
ln bio:species:urtica_dioica bio:genus:urtica sys:is_a
ln bio:species:urtica_dioica bio:trait:dioecy thesaurus:related
set.add name="bio:plants:field_guide:ep1" id="bio:species:urtica_dioica"

def "bio:species:plantago_lanceolata" "Plantago lanceolata — ribwort plantain. Plantaginaceae, order Lamiales. Characters: a flat basal rosette of narrow lance-shaped leaves, each with three to five strong ribs running the length of the blade and no branching side-veins; from the rosette rise leafless, deeply furrowed stalks, each ending in a short, dense, brown-black ovoid spike; the flowers on that spike open in a ring that travels up it, throwing out long white stamens on fine filaments — the plant is wind-pollinated and has no need of colour. Setting: grassland, meadows, waysides and trodden ground, where the flat rosette survives what standing plants do not. Range: native across Eurasia and North Africa, now naturalised on every continent but Antarctica. Naming: planta is the sole of the foot, for a plant of the path; lanceolata for the shape of the leaf. Its English name is shared with the banana called plantain, which is a different plant in a different family on a different continent — two words that arrived in English by separate roads."
al bio:species:plantago_lanceolata ribwort
ln bio:species:plantago_lanceolata bio:genus:plantago sys:is_a
ln bio:species:plantago_lanceolata ingred:fruit:plantain thesaurus:related
set.add name="bio:plants:field_guide:ep1" id="bio:species:plantago_lanceolata"

def "bio:species:achillea_millefolium" "Achillea millefolium — yarrow. Asteraceae, order Asterales. Characters: leaves finely cut two or three times over into narrow segments, so the whole leaf reads as a feather rather than a blade; stems tough, furrowed, faintly downy; the heads small and numerous, carried in a flat-topped cluster that the plant holds level like a tray; each head has about five short white — occasionally pink — ray florets round a cream disc; the plant spreads by creeping rhizomes, so a patch is often one individual; aromatic when crushed. Setting: dry and moderately dry grassland, meadows, road verges, pasture. Range: across the Northern Hemisphere, and widely naturalised beyond it. Naming: Achillea for Achilles, who is said in the old herbals to have carried it; millefolium, a thousand leaves, for the dissection of the foliage."
al bio:species:achillea_millefolium yarrow
ln bio:species:achillea_millefolium bio:genus:achillea sys:is_a
set.add name="bio:plants:field_guide:ep1" id="bio:species:achillea_millefolium"

def "bio:species:geranium_robertianum" "Geranium robertianum — herb-Robert. Geraniaceae, order Geraniales. Characters: a slender, brittle plant whose stems and leaf-stalks flush red, strongly so in sun and on poor ground; leaves palmately cut into three or five stalked divisions, themselves deeply lobed, so the outline is lacy; flowers small, bright pink, five petals, borne in pairs; the fruit is the family's signature — a long beak that dries, splits from the base upward and flicks each seed away; the crushed plant has a sharp, distinctive scent. Setting: shaded hedge banks, woodland floors, walls, and stony ground and scree, where it will grow out of a crack with almost no soil. Range: Europe, western Asia and North Africa; introduced and locally abundant in North America. Naming: geranium from geranos, a crane, for the beaked fruit — 'cranesbill'; Robertianum is unsettled, read variously as Robert of Molesme or as a worn-down form of ruber, red, which is what the stems are."
al bio:species:geranium_robertianum herb_robert
ln bio:species:geranium_robertianum bio:genus:geranium sys:is_a
set.add name="bio:plants:field_guide:ep1" id="bio:species:geranium_robertianum"

def "bio:species:silene_dioica" "Silene dioica — red campion. Caryophyllaceae, order Caryophyllales. Characters: softly hairy throughout, the leaves opposite and set at slightly swollen nodes; flowers deep rose-pink, about 2 cm across, the five petals each so deeply notched at the tip that they read as ten; behind them a tubular calyx, inflated and net-veined; the species is DIOECIOUS, and the two sexes can be told apart at arm's length — a female flower shows five styles at the mouth of the tube and its calyx is the broader, a male shows ten stamens and a narrower calyx. Setting: hedgerows, woodland edges, shaded banks, and the ground under coppice, on soils that are not too acid. Range: Europe, east to western Siberia; introduced in North America. Naming: Silene is usually read as a reference to Silenus, foster-father of Dionysus, though the derivation is not settled; dioica names the same two households as the nettle, arrived at quite separately."
al bio:species:silene_dioica red_campion
ln bio:species:silene_dioica bio:genus:silene sys:is_a
ln bio:species:silene_dioica bio:trait:dioecy thesaurus:related
set.add name="bio:plants:field_guide:ep1" id="bio:species:silene_dioica"

def "bio:species:arum_maculatum" "Arum maculatum — lords-and-ladies, cuckoo-pint. Araceae, order Alismatales. Characters: arrow-shaped leaves appearing in early spring, often blotched dark purple-black; the inflorescence a pale green hood — the spathe — wrapped round a dull purple club, the spadix; the tiny true flowers sit hidden at the base of that club in a chamber, females below, males above, with a ring of downward-pointing hairs across the entrance; for a few hours the spadix WARMS, several degrees above the air, and the heat carries a smell of dung that draws in owl-midges, which fall past the hairs and are held overnight until the pollen is shed and the hairs wither; after the leaves die back, a bare spike of red berries is left standing. Setting: woodland, coppice and shaded hedge banks on base-rich, moist soils. Range: western, central and southern Europe, north to Britain and southern Scandinavia. Naming: arum from the Greek aron; maculatum, spotted, for the leaf — though plenty of populations are not."
al bio:species:arum_maculatum lords_and_ladies
ln bio:species:arum_maculatum bio:genus:arum sys:is_a
ln bio:species:arum_maculatum bio:trait:thermogenesis thesaurus:related
set.add name="bio:plants:field_guide:ep1" id="bio:species:arum_maculatum"

def "bio:species:cardamine_pratensis" "Cardamine pratensis — cuckooflower, lady's-smock. Brassicaceae, order Brassicales. Characters: a basal rosette of pinnate leaves whose leaflets are rounded, almost stalked coins, and stem leaves whose leaflets are narrow and strap-like — the same plant reading differently top and bottom; flowers in a loose head, four petals set in a cross, pale lilac fading nearly to white, with yellow anthers; the fruit a long slender pod that springs open. Setting: damp and wet meadows, streamsides, ditches, marshy grassland and damp woodland rides. Range: across Europe, northern Asia and northern North America. Naming: pratensis, of the meadow; the English name marks the time rather than the plant — it opens as the cuckoo is first heard."
al bio:species:cardamine_pratensis cuckooflower
ln bio:species:cardamine_pratensis bio:genus:cardamine sys:is_a
set.add name="bio:plants:field_guide:ep1" id="bio:species:cardamine_pratensis"

def "bio:species:hedera_helix" "Hedera helix — common ivy. Araliaceae, order Apiales. Characters: an evergreen woody climber that holds to bark, brick and stone with short adventitious rootlets along the stem — it grips, it does not twine and it does not tap the host for sap; and it bears TWO kinds of shoot. The juvenile climbing shoots have the leaf everyone pictures: dark, glossy, three- to five-lobed, pale-veined. The adult flowering shoots, produced only once the plant reaches light, have no rootlets, stand out from the wall, and carry unlobed oval leaves — then greenish umbels of nectar-rich flowers in autumn, late enough to be one of the last things open, and black berries the following spring. Setting: woodland, hedges, old walls, rock faces. Range: Europe and western Asia; widely planted and naturalised. Naming: helix, a spiral or twist. The two leaf forms were long enough taken for two plants that the difference has its own name: heterophylly."
al bio:species:hedera_helix ivy
ln bio:species:hedera_helix bio:genus:hedera sys:is_a
ln bio:species:hedera_helix bio:trait:heterophylly thesaurus:related
set.add name="bio:plants:field_guide:ep1" id="bio:species:hedera_helix"
