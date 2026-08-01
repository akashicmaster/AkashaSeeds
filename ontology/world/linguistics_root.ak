# Linguistics field root — unify the ling.* branches under the existing `ling` concept so the
# concept navigator can show the Language/Linguistics room as a taxonomy (archives ROOM_ROOT
# ling: → ling). Additive + idempotent; `ling` and the branches are defined elsewhere in world.
def "ling" "Linguistics — the scientific study of language; the apex of its branches (phonology, morphology, syntax, semantics, pragmatics, discourse, semiotics)."
ln ling.pragmatics ling sys:is_a
ln ling.semantics ling sys:is_a
ln ling.discourse ling sys:is_a
ln ling.semiotics ling sys:is_a
ln ling.syntax ling sys:is_a
ln ling.morphology ling sys:is_a
