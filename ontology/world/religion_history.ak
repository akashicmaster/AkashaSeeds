# Akasha ontology (world pack) — religious history.
# World religions, their branches, founders and holy sites — tied to deity:,
# founder-figures (person:), geo:country and hist:period. A-tier.

def "religion:religion" "A world religion or major faith tradition (宗教)."
def "religion:hinduism" "The oldest living religion, of many gods, dharma and rebirth."
ln religion:hinduism religion:religion thesaurus:related
ln religion:hinduism geo:country:IND religion:originated_in
ln religion:hinduism deity:pantheon:hindu thesaurus:related
def "religion:buddhism" "The path from suffering to awakening taught by the Buddha."
ln religion:buddhism religion:religion thesaurus:related
ln religion:buddhism geo:country:IND religion:originated_in
ln religion:buddhism person:buddha thesaurus:related
ln religion:buddhism phil:school:buddhist_philosophy thesaurus:related
def "religion:judaism" "The covenant faith of one God, Torah and the Jewish people."
ln religion:judaism religion:religion thesaurus:related
ln religion:judaism geo:country:ISR religion:originated_in
def "religion:christianity" "The faith in Jesus as the risen Christ, the world's largest religion."
ln religion:christianity religion:religion thesaurus:related
ln religion:christianity geo:country:ISR religion:originated_in
def "religion:islam" "Submission to the one God, revealed to Muhammad in the Quran."
ln religion:islam religion:religion thesaurus:related
ln religion:islam geo:country:SAU religion:originated_in
ln religion:islam ethnicity:arabs thesaurus:related
def "religion:taoism_r" "The Chinese religion of the Way, immortals and ritual."
ln religion:taoism_r religion:religion thesaurus:related
ln religion:taoism_r geo:country:CHN religion:originated_in
ln religion:taoism_r phil:school:taoism thesaurus:related
def "religion:confucianism_r" "The ethical-ritual tradition ordering Chinese society."
ln religion:confucianism_r religion:religion thesaurus:related
ln religion:confucianism_r geo:country:CHN religion:originated_in
ln religion:confucianism_r phil:school:confucianism thesaurus:related
def "religion:shinto" "Japan's indigenous way of the kami."
ln religion:shinto religion:religion thesaurus:related
ln religion:shinto geo:country:JPN religion:originated_in
ln religion:shinto deity:pantheon:japanese thesaurus:related
ln religion:shinto deity:inari thesaurus:related
def "religion:sikhism" "The North Indian faith of one God taught by Guru Nanak."
ln religion:sikhism religion:religion thesaurus:related
ln religion:sikhism geo:country:IND religion:originated_in
def "religion:jainism" "The Indian religion of radical nonviolence and many-sidedness."
ln religion:jainism religion:religion thesaurus:related
ln religion:jainism geo:country:IND religion:originated_in
def "religion:zoroastrianism" "The ancient Persian faith of cosmic good against evil."
ln religion:zoroastrianism religion:religion thesaurus:related
ln religion:zoroastrianism geo:country:IRN religion:originated_in
ln religion:zoroastrianism deity:pantheon:zoroastrian thesaurus:related
ln religion:zoroastrianism deity:ahura_mazda thesaurus:related

# ── major branches ──
def "religion:branch:catholicism" "Catholicism — a branch of christianity."
ln religion:branch:catholicism religion:christianity religion:branch_of
def "religion:branch:eastern_orthodoxy" "Eastern Orthodoxy — a branch of christianity."
ln religion:branch:eastern_orthodoxy religion:christianity religion:branch_of
def "religion:branch:protestantism" "Protestantism — a branch of christianity."
ln religion:branch:protestantism religion:christianity religion:branch_of
def "religion:branch:sunni_islam" "Sunni Islam — a branch of islam."
ln religion:branch:sunni_islam religion:islam religion:branch_of
def "religion:branch:shia_islam" "Shia Islam — a branch of islam."
ln religion:branch:shia_islam religion:islam religion:branch_of
def "religion:branch:sufism" "Sufism — a branch of islam."
ln religion:branch:sufism religion:islam religion:branch_of
def "religion:branch:theravada" "Theravada — a branch of buddhism."
ln religion:branch:theravada religion:buddhism religion:branch_of
def "religion:branch:mahayana" "Mahayana — a branch of buddhism."
ln religion:branch:mahayana religion:buddhism religion:branch_of
def "religion:branch:vajrayana" "Vajrayana — a branch of buddhism."
ln religion:branch:vajrayana religion:buddhism religion:branch_of
def "religion:branch:zen_buddhism" "Zen Buddhism — a branch of buddhism."
ln religion:branch:zen_buddhism religion:buddhism religion:branch_of
def "religion:branch:vaishnavism" "Vaishnavism — a branch of hinduism."
ln religion:branch:vaishnavism religion:hinduism religion:branch_of
def "religion:branch:shaivism" "Shaivism — a branch of hinduism."
ln religion:branch:shaivism religion:hinduism religion:branch_of
def "religion:branch:orthodox_judaism" "Orthodox Judaism — a branch of judaism."
ln religion:branch:orthodox_judaism religion:judaism religion:branch_of
def "religion:branch:reform_judaism" "Reform Judaism — a branch of judaism."
ln religion:branch:reform_judaism religion:judaism religion:branch_of

# ── founders / prophets ──
def "person:jesus" "The founder/prophet of christianity."
ln person:jesus person:figure thesaurus:related
ln person:jesus religion:christianity religion:founded_by
ln person:jesus person:field:religion person:worked_in
ln person:jesus geo:country:ISR person:from_country
def "person:muhammad" "The founder/prophet of islam."
ln person:muhammad person:figure thesaurus:related
ln person:muhammad religion:islam religion:founded_by
ln person:muhammad person:field:religion person:worked_in
ln person:muhammad geo:country:SAU person:from_country
def "person:moses" "The founder/prophet of judaism."
ln person:moses person:figure thesaurus:related
ln person:moses religion:judaism religion:founded_by
ln person:moses person:field:religion person:worked_in
ln person:moses geo:country:EGY person:from_country
def "person:guru_nanak" "The founder/prophet of sikhism."
ln person:guru_nanak person:figure thesaurus:related
ln person:guru_nanak religion:sikhism religion:founded_by
ln person:guru_nanak person:field:religion person:worked_in
ln person:guru_nanak geo:country:IND person:from_country
def "person:zoroaster" "The founder/prophet of zoroastrianism."
ln person:zoroaster person:figure thesaurus:related
ln person:zoroaster religion:zoroastrianism religion:founded_by
ln person:zoroaster person:field:religion person:worked_in
ln person:zoroaster geo:country:IRN person:from_country
def "person:mahavira" "The founder/prophet of jainism."
ln person:mahavira person:figure thesaurus:related
ln person:mahavira religion:jainism religion:founded_by
ln person:mahavira person:field:religion person:worked_in
ln person:mahavira geo:country:IND person:from_country

def "religion:site" "A sacred place of pilgrimage or worship (聖地)."
def "religion:site:jerusalem_holy" "Sacred to Judaism, Christianity and Islam alike."
ln religion:site:jerusalem_holy religion:site thesaurus:related
ln religion:site:jerusalem_holy geo:country:ISR religion:located_in
ln religion:site:jerusalem_holy religion:judaism religion:sacred_to
ln religion:site:jerusalem_holy religion:christianity religion:sacred_to
ln religion:site:jerusalem_holy religion:islam religion:sacred_to
def "religion:site:mecca" "Islam's holiest city, the goal of the Hajj."
ln religion:site:mecca religion:site thesaurus:related
ln religion:site:mecca geo:country:SAU religion:located_in
ln religion:site:mecca religion:islam religion:sacred_to
def "religion:site:medina" "The Prophet's city, Islam's second holiest."
ln religion:site:medina religion:site thesaurus:related
ln religion:site:medina geo:country:SAU religion:located_in
ln religion:site:medina religion:islam religion:sacred_to
def "religion:site:vatican_city" "The seat of the Catholic Church."
ln religion:site:vatican_city religion:site thesaurus:related
ln religion:site:vatican_city geo:country:ITA religion:located_in
ln religion:site:vatican_city religion:branch:catholicism religion:sacred_to
def "religion:site:varanasi" "Hinduism's holiest city on the Ganges."
ln religion:site:varanasi religion:site thesaurus:related
ln religion:site:varanasi geo:country:IND religion:located_in
ln religion:site:varanasi religion:hinduism religion:sacred_to
def "religion:site:bodh_gaya" "Where the Buddha attained enlightenment."
ln religion:site:bodh_gaya religion:site thesaurus:related
ln religion:site:bodh_gaya geo:country:IND religion:located_in
ln religion:site:bodh_gaya religion:buddhism religion:sacred_to
def "religion:site:ise_shrine" "Shinto's most sacred shrine, to Amaterasu."
ln religion:site:ise_shrine religion:site thesaurus:related
ln religion:site:ise_shrine geo:country:JPN religion:located_in
ln religion:site:ise_shrine religion:shinto religion:sacred_to
def "religion:site:amritsar" "Site of the Golden Temple, Sikhism's holiest."
ln religion:site:amritsar religion:site thesaurus:related
ln religion:site:amritsar geo:country:IND religion:located_in
ln religion:site:amritsar religion:sikhism religion:sacred_to
ln religion:site:bodh_gaya person:buddha thesaurus:related
ln religion:site:ise_shrine deity:japanese_amaterasu thesaurus:related
