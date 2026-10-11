# Akasha ontology (world pack) — music history: periods & genres.
# Western art-music periods plus popular and world traditions, tied to period
# and composers (person:). A-tier.

def "music:period" "A period or genre in the history of music (音楽の時代/様式)."
def "music:period:medieval_music" "Gregorian chant and the birth of polyphony."
ln music:period:medieval_music music:period thesaurus:related
ln music:period:medieval_music hist:period:high_middle_ages music:of_period
def "music:period:renaissance_music" "Rich vocal polyphony of the Renaissance."
ln music:period:renaissance_music music:period thesaurus:related
ln music:period:renaissance_music hist:period:renaissance music:of_period
ln music:period:medieval_music music:period:renaissance_music chrono:before
def "music:period:baroque_music" "Ornate counterpoint and the birth of opera (Bach, Vivaldi)."
ln music:period:baroque_music music:period thesaurus:related
ln music:period:baroque_music hist:period:enlightenment music:of_period
ln music:period:renaissance_music music:period:baroque_music chrono:before
ln music:period:baroque_music person:bach thesaurus:related
def "music:period:classical_music" "Balance, form and clarity (Mozart, Haydn)."
ln music:period:classical_music music:period thesaurus:related
ln music:period:classical_music hist:period:enlightenment music:of_period
ln music:period:baroque_music music:period:classical_music chrono:before
ln music:period:classical_music person:mozart thesaurus:related
def "music:period:romantic_music" "Emotion, nationalism and the expanded orchestra (Beethoven, Chopin)."
ln music:period:romantic_music music:period thesaurus:related
ln music:period:romantic_music hist:period:industrial_revolution music:of_period
ln music:period:classical_music music:period:romantic_music chrono:before
ln music:period:romantic_music person:beethoven thesaurus:related
def "music:period:impressionist_music" "Colour and atmosphere over structure (Debussy, Ravel)."
ln music:period:impressionist_music music:period thesaurus:related
ln music:period:impressionist_music hist:period:modern_era music:of_period
ln music:period:romantic_music music:period:impressionist_music chrono:before
def "music:period:modernist_music" "Atonality and rhythmic revolution (Stravinsky, Schoenberg)."
ln music:period:modernist_music music:period thesaurus:related
ln music:period:modernist_music hist:period:world_wars_era music:of_period
ln music:period:impressionist_music music:period:modernist_music chrono:before
def "music:period:jazz" "The improvised African-American art form of the 20th century."
ln music:period:jazz music:period thesaurus:related
ln music:period:jazz hist:period:world_wars_era music:of_period
ln music:period:modernist_music music:period:jazz chrono:before
def "music:period:blues" "The soulful African-American root of much modern popular music."
ln music:period:blues music:period thesaurus:related
ln music:period:blues hist:period:modern_era music:of_period
ln music:period:jazz music:period:blues chrono:before
def "music:period:rock_and_roll" "The electric popular music that defined post-war youth."
ln music:period:rock_and_roll music:period thesaurus:related
ln music:period:rock_and_roll hist:period:cold_war music:of_period
ln music:period:blues music:period:rock_and_roll chrono:before
# ── non-Western traditions ──
def "music:tradition:indian_classical" "The raga-and-tala classical music of India."
def "music:tradition:gamelan" "The bronze percussion orchestra of Java and Bali."
def "music:tradition:chinese_classical" "The guqin and court music of China."
ln music:tradition:indian_classical geo:country:IND thesaurus:related
ln music:tradition:gamelan geo:country:IDN thesaurus:related
