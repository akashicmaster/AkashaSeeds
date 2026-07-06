# Akasha ontology — namespace: game
# atoms: 34

def "game.vocab.role_identity" "Role and identity vocabulary: terms describing player roles, team functions, account identity, moderation, and spending behavior."
ln game.vocab.role_identity ont.community_gaming sys:part_of
set.add name="ontology.community_gaming" id="game.vocab.role_identity"

def "game.vocab.social_vibe" "Social and vibe vocabulary: terms describing community behavior, atmosphere, etiquette, identity, and online presence."
ln game.vocab.social_vibe ont.community_gaming sys:part_of
set.add name="ontology.community_gaming" id="game.vocab.social_vibe"

def "game.vocab.state_action" "State and action vocabulary: temporary conditions, tactical actions, repetitive play patterns, and momentary performance states."
ln game.vocab.state_action ont.community_gaming sys:part_of
set.add name="ontology.community_gaming" id="game.vocab.state_action"

def "game.vocab.world_system" "World and system vocabulary: terms describing game worlds, mechanics, randomness, resources, and technical conditions."
ln game.vocab.world_system ont.community_gaming sys:part_of
set.add name="ontology.community_gaming" id="game.vocab.world_system"

def "game:afk" "AFK: Away From Keyboard; a state in which a player is logged in but temporarily absent or inactive."
ln game:afk game.vocab.state_action sys:is_a
set.add name="ontology.community_gaming" id="game:afk"

def "game:aggro" "Aggro: hostile attention or threat drawn from enemies; to pull aggro is to become the target of enemy attacks."
ln game:aggro game.vocab.state_action sys:is_a
set.add name="ontology.community_gaming" id="game:aggro"

def "game:buff" "Buff: a temporary or persistent enhancement of ability, performance, status, or advantage."
ln game:buff game.vocab.state_action sys:is_a
set.add name="ontology.community_gaming" id="game:buff"

def "game:camping" "Camping: waiting in a fixed location to ambush opponents, control a spawn point, or repeatedly exploit a positional advantage."
ln game:camping game.vocab.state_action sys:is_a
set.add name="ontology.community_gaming" id="game:camping"

def "game:carry" "Carry: a player who leads a team to victory through superior skill, scaling power, decision-making, or decisive impact."
ln game:carry game.vocab.role_identity sys:is_a
ln game:carry game:clutch @can_perform
set.add name="ontology.community_gaming" id="game:carry"

def "game:cheesing" "Cheesing: winning or progressing by using an unusually simple, exploitative, or unintended tactic rather than normal play."
ln game:cheesing game.vocab.state_action sys:is_a
ln game:cheesing game:exploit @related_to
set.add name="ontology.community_gaming" id="game:cheesing"

def "game:clutch" "Clutch: a decisive play that reverses or saves a situation under extreme pressure."
ln game:clutch game.vocab.state_action sys:is_a
set.add name="ontology.community_gaming" id="game:clutch"

def "game:cooldown" "Cooldown: the waiting period before an ability, item, spell, or action can be used again."
ln game:cooldown game.vocab.world_system sys:is_a
ln game:cooldown game:meta @constrains
set.add name="ontology.community_gaming" id="game:cooldown"

def "game:dps" "DPS: Damage Per Second; also a role focused on dealing damage as the primary contribution to a team."
ln game:dps game.vocab.role_identity sys:is_a
ln game:dps game:support @benefits_from
set.add name="ontology.community_gaming" id="game:dps"

def "game:exploit" "Exploit: use of a bug, loophole, unintended interaction, or design oversight for advantage."
ln game:exploit game.vocab.world_system sys:is_a
set.add name="ontology.community_gaming" id="game:exploit"

def "game:farming" "Farming: repeated collection of specific resources, items, drops, materials, or rewards with efficiency as the goal."
ln game:farming game:grinding sys:is_a
set.add name="ontology.community_gaming" id="game:farming"

def "game:ganking" "Ganking: attacking a weaker, isolated, or outnumbered target from an overwhelming advantage, often by surprise."
ln game:ganking game.vocab.state_action sys:is_a
set.add name="ontology.community_gaming" id="game:ganking"

def "game:grinding" "Grinding: repetitive work performed to gain levels, currency, experience, reputation, or progress."
ln game:grinding game.vocab.state_action sys:is_a
set.add name="ontology.community_gaming" id="game:grinding"

def "game:healer" "Healer: a support role focused on restoring health, preventing death, cleansing harm, or sustaining the party."
ln game:healer game.vocab.role_identity sys:is_a
ln game:healer game:support sys:is_a
set.add name="ontology.community_gaming" id="game:healer"

def "game:instance" "Instance: a separately generated copy of a game space, dungeon, mission, or environment for a player or party."
ln game:instance game.vocab.world_system sys:is_a
set.add name="ontology.community_gaming" id="game:instance"

def "game:loot" "Loot: rewards, items, resources, or equipment obtained from enemies, containers, quests, or events."
ln game:loot game.vocab.world_system sys:is_a
ln game:loot game:farming @motivates
set.add name="ontology.community_gaming" id="game:loot"

def "game:meta" "Meta: the currently dominant, most effective, or widely accepted strategy, build, tactic, or interpretation within a game or community."
ln game:meta game.vocab.world_system sys:is_a
ln game:meta game:grinding @optimizes
set.add name="ontology.community_gaming" id="game:meta"

def "game:nerf" "Nerf: a weakening or downward balance adjustment applied to a character, item, ability, strategy, or system."
ln game:nerf game.vocab.state_action sys:is_a
ln game:nerf game:buff @contrasts_with
set.add name="ontology.community_gaming" id="game:nerf"

def "game:newbie" "Newbie: a new or inexperienced participant who is still learning rules, norms, mechanics, or community expectations."
ln game:newbie game.vocab.role_identity sys:is_a
set.add name="ontology.community_gaming" id="game:newbie"

def "game:patch" "Patch: an update that modifies game systems, fixes bugs, changes balance, or adds content."
ln game:patch game.vocab.world_system sys:is_a
ln game:patch game:buff @may_cause
ln game:patch game:nerf @may_cause
ln game:patch game:meta @changes
set.add name="ontology.community_gaming" id="game:patch"

def "game:ping" "Ping: network response latency, or a signal placed on a map or interface to indicate location, danger, or attention."
ln game:ping game.vocab.world_system sys:is_a
set.add name="ontology.community_gaming" id="game:ping"

def "game:respawn" "Respawn: reappearance after death, removal, collection, or reset."
ln game:respawn game:spawn sys:is_a
set.add name="ontology.community_gaming" id="game:respawn"

def "game:rng" "RNG: Random Number Generator; the random or luck-based element that determines drops, outcomes, encounters, or variation."
ln game:rng game.vocab.world_system sys:is_a
ln game:rng game:loot @affects
set.add name="ontology.community_gaming" id="game:rng"

def "game:smurf" "Smurf: an alternate account used by an experienced player, often to play below their true skill level."
ln game:smurf game.vocab.role_identity sys:is_a
ln game:smurf game:ganking @can_enable
set.add name="ontology.community_gaming" id="game:smurf"

def "game:spawn" "Spawn: the appearance of a character, enemy, object, or resource in the game world."
ln game:spawn game.vocab.world_system sys:is_a
set.add name="ontology.community_gaming" id="game:spawn"

def "game:support" "Support: a role that improves team effectiveness through healing, buffs, control, protection, utility, or information."
ln game:support game.vocab.role_identity sys:is_a
ln game:support game:buff @uses
ln game:support game:tank @supports
set.add name="ontology.community_gaming" id="game:support"

def "game:tank" "Tank: a durable role that protects allies by absorbing damage, controlling enemy attention, and holding aggro."
ln game:tank game.vocab.role_identity sys:is_a
ln game:tank game:aggro @manages
ln game:tank game:dps @complements
ln game:tank game:healer @depends_on
set.add name="ontology.community_gaming" id="game:tank"

def "game:veteran" "Veteran: an experienced player or community member with long participation, accumulated knowledge, and practical fluency."
ln game:veteran game.vocab.role_identity sys:is_a
ln game:veteran game:newbie @contrasts_with
ln game:veteran game:newbie @may_mentor
set.add name="ontology.community_gaming" id="game:veteran"

def "game:whale" "Whale: a player who spends unusually large amounts of real money or in-game currency, especially in free-to-play economies."
ln game:whale game.vocab.role_identity sys:is_a
ln game:whale game:meta @can_distort
set.add name="ontology.community_gaming" id="game:whale"

def "game:wipe" "Wipe: total party or team failure, usually resulting in death, reset, or loss of encounter progress."
ln game:wipe game.vocab.state_action sys:is_a
set.add name="ontology.community_gaming" id="game:wipe"
