# Philosophy field root — a single apex over the philosophy.* branches so the concept navigator
# can show the Philosophy room as a taxonomy (archives ROOM_ROOT phil: → philosophy; the phil:*
# entries hang under these branches via their own sys:is_a). Additive + idempotent; the branches
# are defined elsewhere in base3.
def "philosophy" "Philosophy — the study of fundamental questions of existence, knowledge, value and reason; the apex of the philosophy branches (logic, metaphysics, epistemology, ethics, mind, language, …)."
ln philosophy.logic philosophy sys:is_a
ln philosophy.metaphysics philosophy sys:is_a
ln philosophy.mind philosophy sys:is_a
ln philosophy.epistemology philosophy sys:is_a
ln philosophy.hermeneutics philosophy sys:is_a
ln philosophy.ethics philosophy sys:is_a
ln philosophy.language philosophy sys:is_a
ln philosophy.dialectics philosophy sys:is_a
ln philosophy.politics philosophy sys:is_a
