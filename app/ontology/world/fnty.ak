# Akasha ontology — namespace: fnty
# atoms: 17

def "fnty:ancient_artifact" "古代遺物/アーティファクト: Devices left behind by lost civilizations or higher entities that bypass modern technological understanding or magical limits."
ln fnty:ancient_artifact fantasy.category.power_system sys:is_a
ln fnty:ancient_artifact fnty:cheat_ability @sources
set.add name="ontology.entertainment_fantasy" id="fnty:ancient_artifact"

def "fnty:cheat_ability" "チート能力: Anomalous talents or parameters that break the established balance of the world's standard operational rules."
ln fnty:cheat_ability fantasy.category.character_trope sys:is_a
set.add name="ontology.entertainment_fantasy" id="fnty:cheat_ability"

def "fnty:chuunibyou" "中二病: The desperate, beautiful, or delusional manifested desire to possess a secret reality, an hidden lineage, or an unrevealed cosmic curse."
ln fnty:chuunibyou fantasy.category.character_trope sys:is_a
ln fnty:chuunibyou fnty:curse_stigma @obsessed_with
set.add name="ontology.entertainment_fantasy" id="fnty:chuunibyou"

def "fnty:curse_stigma" "呪印/聖痕: A permanent branding on the body or soul representing a contract, an unpayable debt, or an involuntary canalization of power."
ln fnty:curse_stigma fantasy.category.power_system sys:is_a
ln fnty:curse_stigma fnty:equivalent_exchange @governed_by
set.add name="ontology.entertainment_fantasy" id="fnty:curse_stigma"

def "fnty:destined_rival" "宿敵/運命のライバル: Two entities whose existence, philosophies, and growth curves are perfectly mirrored and bound to violently collide."
ln fnty:destined_rival fantasy.category.fate_relation sys:is_a
ln fnty:destined_rival fnty:quasard_emotion @generates
set.add name="ontology.entertainment_fantasy" id="fnty:destined_rival"

def "fnty:dystopia_cyber" "ディストピア/サイバーパンク: High tech, low life. Regulated societies, absolute corporate control, and human consciousness treated as an externalized commodity."
ln fnty:dystopia_cyber fantasy.category.world_type sys:is_a
ln fnty:dystopia_cyber fnty:urban_fantasy @contrasts_with
set.add name="ontology.entertainment_fantasy" id="fnty:dystopia_cyber"

def "fnty:equivalent_exchange" "等価交換: The fundamental law of balanced transaction. To obtain something, something of equal value (frequently memories, lifespans, or organic parts) must be lost."
ln fnty:equivalent_exchange fantasy.category.power_system sys:is_a
set.add name="ontology.entertainment_fantasy" id="fnty:equivalent_exchange"

def "fnty:isekai_reincarnation" "异世界転生/転移: Transitioning to another reality. Often involves a reset of societal standing, subversion of destiny, or acquisition of cheat-grade rule compliance."
ln fnty:isekai_reincarnation fantasy.category.world_type sys:is_a
ln fnty:isekai_reincarnation fnty:cheat_ability @frequently_utilizes
set.add name="ontology.entertainment_fantasy" id="fnty:isekai_reincarnation"

def "fnty:kumorase" "曇らせ/Emotional Despair: The narrative practice of placing beloved characters into systematic, tragic, or bittersweet situations to extract intense emotional resonance."
ln fnty:kumorase fantasy.category.character_trope sys:is_a
ln fnty:kumorase fnty:yamiodochi @triggers
set.add name="ontology.entertainment_fantasy" id="fnty:kumorase"

def "fnty:mana_ether" "魔力/エーテル: The primordial substance or energy grid required to distort causality. Follows dynamic or rigid physical-semantic laws."
ln fnty:mana_ether fantasy.category.power_system sys:is_a
set.add name="ontology.entertainment_fantasy" id="fnty:mana_ether"

def "fnty:quasard_emotion" "クソデカ感情/Quasar-grade Emotion: Interpersonal feelings that are too massive, contradictory, or intense to be categorized into simple labels like love or hate."
ln fnty:quasard_emotion fantasy.category.fate_relation sys:is_a
set.add name="ontology.entertainment_fantasy" id="fnty:quasard_emotion"

def "fnty:science_fiction" "Science Fiction"
ln fnty:science_fiction speculation sys:refers_to
ln fnty:science_fiction science sys:refers_to
ln fnty:science_fiction the_future calc:associated_with

def "fnty:soul_contractor" "契約者/Soul Contractor: A binding transaction connecting a mortal entity with an absolute concept, god, demon, or artificial engine."
ln fnty:soul_contractor fantasy.category.fate_relation sys:is_a
set.add name="ontology.entertainment_fantasy" id="fnty:soul_contractor"

def "fnty:soul_twin" "魂の半身/Soul Twin: Metaphorical or literal partitioning of a single existential essence across two separate individuals. If one falls, the other is destabilized."
ln fnty:soul_twin fantasy.category.fate_relation sys:is_a
ln fnty:soul_twin fnty:equivalent_exchange @bound_by
set.add name="ontology.entertainment_fantasy" id="fnty:soul_twin"

def "fnty:steampunk_antique" "スチームパンク: Retro-futurism driven by massive steam engines, brass mechanisms, and Victorian or industrialized aesthetics."
ln fnty:steampunk_antique fantasy.category.world_type sys:is_a
set.add name="ontology.entertainment_fantasy" id="fnty:steampunk_antique"

def "fnty:urban_fantasy" "現代伝奇/アーバンファンタジー: A setting where magic or supernatural elements bleed into the margins of common everyday modern life under the veil of secrecy."
ln fnty:urban_fantasy fantasy.category.world_type sys:is_a
set.add name="ontology.entertainment_fantasy" id="fnty:urban_fantasy"

def "fnty:yamiodochi" "闇堕ち/ダークフォール: The structural collapse or deliberate abandonment of a character's core moral framework, frequently driven by extreme trauma or absolute disillusionment."
ln fnty:yamiodochi fantasy.category.character_trope sys:is_a
set.add name="ontology.entertainment_fantasy" id="fnty:yamiodochi"
