# Emotion field root — a single apex over the basic emotions so the concept navigator can show the
# Emotions room as a taxonomy (archives ROOM_ROOT emo: → emo:emotion). Each basic emotion already
# has its finer feelings as sub-concepts; this only adds the top. Additive + idempotent.
def "emo:emotion" "Emotion — the apex of the basic-emotion families (joy, fear, sadness, surprise, disgust, excitement) and the finer feelings that specialise them."
ln emo:joy emo:emotion sys:is_a
ln emo:fear emo:emotion sys:is_a
ln emo:sadness emo:emotion sys:is_a
ln emo:surprise emo:emotion sys:is_a
ln emo:disgust emo:emotion sys:is_a
ln emo:excitement emo:emotion sys:is_a
