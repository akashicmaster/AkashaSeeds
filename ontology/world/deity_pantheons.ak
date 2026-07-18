# Akasha ontology (world pack) — pantheon classification, gap-filling & equivalents.
# Groups deity:* into pantheons, fills major gaps (Zeus/Odin/Osiris/Marduk/Vishnu),
# links Roman↔Greek, and draws cross-pantheon equivalents. A-tier.

def "deity:pantheon" "A pantheon — the gods of one mythological system."
def "deity:pantheon:greek" "The greek pantheon."
ln deity:pantheon:greek deity:pantheon thesaurus:related
ln deity:pantheon:greek geo:country:GRC thesaurus:related
def "deity:pantheon:roman" "The roman pantheon."
ln deity:pantheon:roman deity:pantheon thesaurus:related
ln deity:pantheon:roman geo:country:ITA thesaurus:related
def "deity:pantheon:norse" "The norse pantheon."
ln deity:pantheon:norse deity:pantheon thesaurus:related
def "deity:pantheon:egyptian" "The egyptian pantheon."
ln deity:pantheon:egyptian deity:pantheon thesaurus:related
ln deity:pantheon:egyptian geo:country:EGY thesaurus:related
def "deity:pantheon:mesopotamian" "The mesopotamian pantheon."
ln deity:pantheon:mesopotamian deity:pantheon thesaurus:related
ln deity:pantheon:mesopotamian geo:country:IRQ thesaurus:related
def "deity:pantheon:hindu" "The hindu pantheon."
ln deity:pantheon:hindu deity:pantheon thesaurus:related
ln deity:pantheon:hindu geo:country:IND thesaurus:related
def "deity:pantheon:japanese" "The japanese pantheon."
ln deity:pantheon:japanese deity:pantheon thesaurus:related
ln deity:pantheon:japanese geo:country:JPN thesaurus:related
def "deity:pantheon:celtic" "The celtic pantheon."
ln deity:pantheon:celtic deity:pantheon thesaurus:related
def "deity:pantheon:slavic" "The slavic pantheon."
ln deity:pantheon:slavic deity:pantheon thesaurus:related
ln deity:pantheon:slavic geo:country:RUS thesaurus:related
def "deity:pantheon:aztec" "The aztec pantheon."
ln deity:pantheon:aztec deity:pantheon thesaurus:related
ln deity:pantheon:aztec geo:country:MEX thesaurus:related
def "deity:pantheon:zoroastrian" "The zoroastrian pantheon."
ln deity:pantheon:zoroastrian deity:pantheon thesaurus:related
ln deity:pantheon:zoroastrian geo:country:IRN thesaurus:related
def "deity:pantheon:yoruba" "The yoruba pantheon."
ln deity:pantheon:yoruba deity:pantheon thesaurus:related
def "deity:pantheon:polynesian" "The polynesian pantheon."
ln deity:pantheon:polynesian deity:pantheon thesaurus:related

# ── classify existing deities ──
ln deity:apollo deity:pantheon:greek deity:worshipped_in
ln deity:ares deity:pantheon:greek deity:worshipped_in
ln deity:artemis deity:pantheon:greek deity:worshipped_in
ln deity:hades deity:pantheon:greek deity:worshipped_in
ln deity:hera deity:pantheon:greek deity:worshipped_in
ln deity:hermes deity:pantheon:greek deity:worshipped_in
ln deity:hephaestus deity:pantheon:greek deity:worshipped_in
ln deity:dionysus deity:pantheon:greek deity:worshipped_in
ln deity:cronus deity:pantheon:greek deity:worshipped_in
ln deity:persephone deity:pantheon:greek deity:worshipped_in
ln deity:greek_demeter deity:pantheon:greek deity:worshipped_in
ln deity:greek_helios deity:pantheon:greek deity:worshipped_in
ln deity:loki deity:pantheon:norse deity:worshipped_in
ln deity:norse_thor deity:pantheon:norse deity:worshipped_in
ln deity:egyptian_ra deity:pantheon:egyptian deity:worshipped_in
ln deity:sekhmet deity:pantheon:egyptian deity:worshipped_in
ln deity:agni deity:pantheon:hindu deity:worshipped_in
ln deity:indra deity:pantheon:hindu deity:worshipped_in
ln deity:durga deity:pantheon:hindu deity:worshipped_in
ln deity:ganesha deity:pantheon:hindu deity:worshipped_in
ln deity:hanuman deity:pantheon:hindu deity:worshipped_in
ln deity:surya deity:pantheon:hindu deity:worshipped_in
ln deity:varuna deity:pantheon:hindu deity:worshipped_in
ln deity:yama deity:pantheon:hindu deity:worshipped_in
ln deity:dyaus deity:pantheon:hindu deity:worshipped_in
ln deity:ushas deity:pantheon:hindu deity:worshipped_in
ln deity:ashvins deity:pantheon:hindu deity:worshipped_in
ln deity:mitra deity:pantheon:hindu deity:worshipped_in
ln deity:ahura_mazda deity:pantheon:zoroastrian deity:worshipped_in
ln deity:angra_mainyu deity:pantheon:zoroastrian deity:worshipped_in
ln deity:mithra deity:pantheon:zoroastrian deity:worshipped_in
ln deity:asha deity:pantheon:zoroastrian deity:worshipped_in
ln deity:atar deity:pantheon:zoroastrian deity:worshipped_in
ln deity:anahita deity:pantheon:zoroastrian deity:worshipped_in
ln deity:verethragna deity:pantheon:zoroastrian deity:worshipped_in
ln deity:japanese_amaterasu deity:pantheon:japanese deity:worshipped_in
ln deity:benzaiten deity:pantheon:japanese deity:worshipped_in
ln deity:bishamonten deity:pantheon:japanese deity:worshipped_in
ln deity:bonten deity:pantheon:japanese deity:worshipped_in
ln deity:daikokuten deity:pantheon:japanese deity:worshipped_in
ln deity:emma deity:pantheon:japanese deity:worshipped_in
ln deity:taishakuten deity:pantheon:japanese deity:worshipped_in
ln deity:arianrhod deity:pantheon:celtic deity:worshipped_in
ln deity:brigid deity:pantheon:celtic deity:worshipped_in
ln deity:cernunnos deity:pantheon:celtic deity:worshipped_in
ln deity:lugh deity:pantheon:celtic deity:worshipped_in
ln deity:manannan deity:pantheon:celtic deity:worshipped_in
ln deity:nuada deity:pantheon:celtic deity:worshipped_in
ln deity:the_dagda deity:pantheon:celtic deity:worshipped_in
ln deity:the_morrigan deity:pantheon:celtic deity:worshipped_in
ln deity:mokosh deity:pantheon:slavic deity:worshipped_in
ln deity:perun deity:pantheon:slavic deity:worshipped_in
ln deity:svarog deity:pantheon:slavic deity:worshipped_in
ln deity:dazhbog deity:pantheon:slavic deity:worshipped_in
ln deity:morana deity:pantheon:slavic deity:worshipped_in
ln deity:veles deity:pantheon:slavic deity:worshipped_in
ln deity:huitzilopochtli deity:pantheon:aztec deity:worshipped_in
ln deity:mictlantecuhtli deity:pantheon:aztec deity:worshipped_in
ln deity:quetzalcoatl deity:pantheon:aztec deity:worshipped_in
ln deity:tezcatlipoca deity:pantheon:aztec deity:worshipped_in
ln deity:tlaloc deity:pantheon:aztec deity:worshipped_in
ln deity:tonatiuh deity:pantheon:aztec deity:worshipped_in
ln deity:eshu deity:pantheon:yoruba deity:worshipped_in
ln deity:polynesian_maui deity:pantheon:polynesian deity:worshipped_in

# ── gap-filling: major deities added ──
def "deity:zeus" "King of the gods, sky and thunder."
ln deity:zeus deity:pantheon:greek deity:worshipped_in
def "deity:poseidon" "God of the sea and earthquakes."
ln deity:poseidon deity:pantheon:greek deity:worshipped_in
def "deity:athena" "Goddess of wisdom and just war."
ln deity:athena deity:pantheon:greek deity:worshipped_in
def "deity:aphrodite" "Goddess of love and beauty."
ln deity:aphrodite deity:pantheon:greek deity:worshipped_in
def "deity:jupiter" "King of the Roman gods (= Zeus)."
ln deity:jupiter deity:pantheon:roman deity:worshipped_in
def "deity:juno" "Queen of the gods (= Hera)."
ln deity:juno deity:pantheon:roman deity:worshipped_in
def "deity:mars" "God of war (= Ares)."
ln deity:mars deity:pantheon:roman deity:worshipped_in
def "deity:venus" "Goddess of love (= Aphrodite)."
ln deity:venus deity:pantheon:roman deity:worshipped_in
def "deity:neptune" "God of the sea (= Poseidon)."
ln deity:neptune deity:pantheon:roman deity:worshipped_in
def "deity:minerva" "Goddess of wisdom (= Athena)."
ln deity:minerva deity:pantheon:roman deity:worshipped_in
def "deity:odin" "All-father, god of wisdom, war and death."
ln deity:odin deity:pantheon:norse deity:worshipped_in
def "deity:freya" "Goddess of love, war and seidr."
ln deity:freya deity:pantheon:norse deity:worshipped_in
def "deity:frigg" "Queen of the Aesir, goddess of foresight."
ln deity:frigg deity:pantheon:norse deity:worshipped_in
def "deity:tyr" "God of war and justice."
ln deity:tyr deity:pantheon:norse deity:worshipped_in
def "deity:baldr" "God of light, whose death heralds Ragnarok."
ln deity:baldr deity:pantheon:norse deity:worshipped_in
def "deity:heimdall" "Watchman of the gods."
ln deity:heimdall deity:pantheon:norse deity:worshipped_in
def "deity:osiris" "God of the afterlife and resurrection."
ln deity:osiris deity:pantheon:egyptian deity:worshipped_in
def "deity:isis" "Goddess of magic and motherhood."
ln deity:isis deity:pantheon:egyptian deity:worshipped_in
def "deity:horus" "Falcon god of kingship and the sky."
ln deity:horus deity:pantheon:egyptian deity:worshipped_in
def "deity:anubis" "Jackal god of mummification."
ln deity:anubis deity:pantheon:egyptian deity:worshipped_in
def "deity:set" "God of chaos, storms and the desert."
ln deity:set deity:pantheon:egyptian deity:worshipped_in
def "deity:thoth" "God of writing, wisdom and the moon."
ln deity:thoth deity:pantheon:egyptian deity:worshipped_in
def "deity:hathor" "Goddess of love, music and joy."
ln deity:hathor deity:pantheon:egyptian deity:worshipped_in
def "deity:marduk" "Babylon's chief god, slayer of Tiamat."
ln deity:marduk deity:pantheon:mesopotamian deity:worshipped_in
def "deity:ishtar" "Goddess of love and war."
ln deity:ishtar deity:pantheon:mesopotamian deity:worshipped_in
def "deity:enlil" "God of wind, air and storms."
ln deity:enlil deity:pantheon:mesopotamian deity:worshipped_in
def "deity:enki" "God of water, wisdom and creation."
ln deity:enki deity:pantheon:mesopotamian deity:worshipped_in
def "deity:anu" "The sky-father, highest of the gods."
ln deity:anu deity:pantheon:mesopotamian deity:worshipped_in
def "deity:tiamat" "Primordial sea-dragon of chaos."
ln deity:tiamat deity:pantheon:mesopotamian deity:worshipped_in
def "deity:vishnu" "The preserver, who descends as avatars."
ln deity:vishnu deity:pantheon:hindu deity:worshipped_in
def "deity:shiva" "The destroyer and transformer."
ln deity:shiva deity:pantheon:hindu deity:worshipped_in
def "deity:brahma" "The creator god."
ln deity:brahma deity:pantheon:hindu deity:worshipped_in
def "deity:lakshmi" "Goddess of wealth and fortune."
ln deity:lakshmi deity:pantheon:hindu deity:worshipped_in
def "deity:saraswati" "Goddess of knowledge, music and speech."
ln deity:saraswati deity:pantheon:hindu deity:worshipped_in
def "deity:krishna" "Beloved avatar of Vishnu."
ln deity:krishna deity:pantheon:hindu deity:worshipped_in
def "deity:kali" "Fierce goddess of time and destruction."
ln deity:kali deity:pantheon:hindu deity:worshipped_in
def "deity:susanoo" "Storm god, brother of Amaterasu."
ln deity:susanoo deity:pantheon:japanese deity:worshipped_in
def "deity:izanagi" "Creator god who made the islands."
ln deity:izanagi deity:pantheon:japanese deity:worshipped_in
def "deity:izanami" "Creator goddess, mother of the land."
ln deity:izanami deity:pantheon:japanese deity:worshipped_in
def "deity:inari" "Deity of rice, fertility and foxes."
ln deity:inari deity:pantheon:japanese deity:worshipped_in
ln deity:pantheon:roman deity:pantheon:greek thesaurus:related

# ── cross-pantheon equivalents ──
def "deity:archetype" "A divine role recurring across pantheons."
def "deity:archetype:sky_father" "The sky father across cultures."
ln deity:archetype:sky_father deity:archetype thesaurus:related
ln deity:zeus deity:archetype:sky_father deity:embodies
ln deity:jupiter deity:archetype:sky_father deity:embodies
ln deity:dyaus deity:archetype:sky_father deity:embodies
ln deity:anu deity:archetype:sky_father deity:embodies
def "deity:archetype:thunderer" "The thunderer across cultures."
ln deity:archetype:thunderer deity:archetype thesaurus:related
ln deity:zeus deity:archetype:thunderer deity:embodies
ln deity:perun deity:archetype:thunderer deity:embodies
ln deity:norse_thor deity:archetype:thunderer deity:embodies
ln deity:indra deity:archetype:thunderer deity:embodies
def "deity:archetype:love_goddess" "The love goddess across cultures."
ln deity:archetype:love_goddess deity:archetype thesaurus:related
ln deity:aphrodite deity:archetype:love_goddess deity:embodies
ln deity:venus deity:archetype:love_goddess deity:embodies
ln deity:ishtar deity:archetype:love_goddess deity:embodies
ln deity:freya deity:archetype:love_goddess deity:embodies
def "deity:archetype:war_god" "The war god across cultures."
ln deity:archetype:war_god deity:archetype thesaurus:related
ln deity:ares deity:archetype:war_god deity:embodies
ln deity:mars deity:archetype:war_god deity:embodies
ln deity:tyr deity:archetype:war_god deity:embodies
def "deity:archetype:sun_deity" "The sun deity across cultures."
ln deity:archetype:sun_deity deity:archetype thesaurus:related
ln deity:egyptian_ra deity:archetype:sun_deity deity:embodies
ln deity:greek_helios deity:archetype:sun_deity deity:embodies
ln deity:surya deity:archetype:sun_deity deity:embodies
ln deity:japanese_amaterasu deity:archetype:sun_deity deity:embodies
ln deity:tonatiuh deity:archetype:sun_deity deity:embodies
def "deity:archetype:underworld_ruler" "The underworld ruler across cultures."
ln deity:archetype:underworld_ruler deity:archetype thesaurus:related
ln deity:hades deity:archetype:underworld_ruler deity:embodies
ln deity:osiris deity:archetype:underworld_ruler deity:embodies
ln deity:yama deity:archetype:underworld_ruler deity:embodies
ln deity:mictlantecuhtli deity:archetype:underworld_ruler deity:embodies
ln deity:emma deity:archetype:underworld_ruler deity:embodies
def "deity:archetype:wisdom_deity" "The wisdom deity across cultures."
ln deity:archetype:wisdom_deity deity:archetype thesaurus:related
ln deity:athena deity:archetype:wisdom_deity deity:embodies
ln deity:minerva deity:archetype:wisdom_deity deity:embodies
ln deity:thoth deity:archetype:wisdom_deity deity:embodies
ln deity:saraswati deity:archetype:wisdom_deity deity:embodies
ln deity:odin deity:archetype:wisdom_deity deity:embodies
def "deity:archetype:sea_god" "The sea god across cultures."
ln deity:archetype:sea_god deity:archetype thesaurus:related
ln deity:poseidon deity:archetype:sea_god deity:embodies
ln deity:neptune deity:archetype:sea_god deity:embodies
ln deity:enki deity:archetype:sea_god deity:embodies
ln deity:manannan deity:archetype:sea_god deity:embodies
