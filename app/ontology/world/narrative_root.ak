# Narrative field root — a single apex over the narrative.* branches so the concept navigator can
# show the Narrative room as a taxonomy (archives ROOM_ROOT nar: → narrative). The six story
# typologies group under narrative.typology (already defined); the other narrative forms hang
# directly under narrative. Additive + idempotent; branches are defined elsewhere in world.
def "narrative" "Narrative — the craft and study of story; the apex of the narrative branches: the typologies of story, plot, and the narrative forms."
ln narrative.typology.society narrative.typology sys:is_a
ln narrative.typology.conflict narrative.typology sys:is_a
ln narrative.typology.fall_rise narrative.typology sys:is_a
ln narrative.typology.journey narrative.typology sys:is_a
ln narrative.typology.revelation narrative.typology sys:is_a
ln narrative.typology.transformation narrative.typology sys:is_a
ln narrative.typology narrative sys:is_a
ln narrative.bolero narrative sys:is_a
ln narrative.journal narrative sys:is_a
ln narrative.magic narrative sys:is_a
ln narrative.plot narrative sys:is_a
