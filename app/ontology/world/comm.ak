# Akasha ontology — namespace: comm
# atoms: 13

def "comm:based" "Based: praise for someone who acts from conviction, authenticity, confidence, or unapologetic individuality."
ln comm:based game.vocab.social_vibe sys:is_a
ln comm:based comm:vibe_check @passes
set.add name="ontology.community_gaming" id="comm:based"

def "comm:copypasta" "Copypasta: a block of text repeatedly copied and pasted across communities, often as joke, ritual, spam, or shared reference."
ln comm:copypasta comm:meme sys:is_a
set.add name="ontology.community_gaming" id="comm:copypasta"

def "comm:fomo" "FOMO: Fear Of Missing Out; anxiety that one is missing an event, trend, reward, opportunity, or shared social moment."
ln comm:fomo game.vocab.social_vibe sys:is_a
ln comm:fomo game:grinding @can_drive
ln comm:fomo game:farming @can_drive
set.add name="ontology.community_gaming" id="comm:fomo"

def "comm:gatekeeping" "Gatekeeping: controlling access to a community, identity, practice, or fandom by declaring who counts as legitimate."
ln comm:gatekeeping game.vocab.social_vibe sys:is_a
ln comm:gatekeeping game:newbie @excludes
set.add name="ontology.community_gaming" id="comm:gatekeeping"

def "comm:ghosting" "Ghosting: suddenly disappearing from communication without explanation; in streaming, watching a broadcaster's screen to gain unfair information."
ln comm:ghosting game.vocab.social_vibe sys:is_a
set.add name="ontology.community_gaming" id="comm:ghosting"

def "comm:lurker" "Lurker: a person who reads, watches, or remains present in a community without actively speaking or participating."
ln comm:lurker game.vocab.social_vibe sys:is_a
ln comm:lurker game.vocab.social_vibe @observes_without_participating
set.add name="ontology.community_gaming" id="comm:lurker"

def "comm:meme" "Meme: a repeatable cultural unit, joke, image, phrase, or pattern that spreads through imitation and variation."
ln comm:meme game.vocab.social_vibe sys:is_a
set.add name="ontology.community_gaming" id="comm:meme"

def "comm:mod" "Mod: either a moderator who manages community behavior, or a modification that changes a game, tool, or system."
ln comm:mod game.vocab.role_identity sys:is_a
ln comm:mod comm:toxic @moderates
set.add name="ontology.community_gaming" id="comm:mod"

def "comm:op" "OP: either Overpowered, meaning too strong, or Original Poster, meaning the person who started a thread or discussion."
ln comm:op game.vocab.social_vibe sys:is_a
set.add name="ontology.community_gaming" id="comm:op"

def "comm:shitposting" "Shitposting: deliberately low-effort, absurd, ironic, or chaotic posting used for humor, disruption, bonding, or signal distortion."
ln comm:shitposting game.vocab.social_vibe sys:is_a
ln comm:shitposting comm:troll @can_overlap_with
set.add name="ontology.community_gaming" id="comm:shitposting"

def "comm:toxic" "Toxic: harmful, hostile, abusive, demoralizing, or socially corrosive behavior within a group, team, or community."
ln comm:toxic game.vocab.social_vibe sys:is_a
ln comm:toxic comm:troll @related_to
ln comm:toxic comm:vibe_check @fails
set.add name="ontology.community_gaming" id="comm:toxic"

def "comm:troll" "Troll: a person or behavior that intentionally disrupts, provokes, derails, or damages a conversation, game, or community."
ln comm:troll game.vocab.social_vibe sys:is_a
set.add name="ontology.community_gaming" id="comm:troll"

def "comm:vibe_check" "Vibe Check: an informal test of whether a person, group, place, or situation feels safe, aligned, trustworthy, or socially compatible."
ln comm:vibe_check game.vocab.social_vibe sys:is_a
set.add name="ontology.community_gaming" id="comm:vibe_check"
