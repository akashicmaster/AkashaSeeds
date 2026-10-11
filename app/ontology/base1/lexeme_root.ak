# Lexeme field root — the vocabulary apex. Proto-words (bare lemmas created by the weaver) are
# rolled up `sys:is_a lexeme` (at creation in composite._ensure_protoword, and back-filled on load
# by the canon normalizer), so the vocabulary becomes a rooted, navigable field: concept.roots
# field=lexeme → lemmas → their senses (reached via the specializes ⊂ sys:is_a family). Standalone
# field root (not under a role); archives ROOM_ROOT word: → lexeme.
def "lexeme" "Lexeme — a word of the vocabulary; the apex of the language layer. Its children are the proto-words (lemmas), each specialised by the word-senses that use it."
