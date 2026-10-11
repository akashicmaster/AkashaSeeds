# Aspect — the seeds13 time coordinate, as SET MEMBERSHIP.
#
# Law 2 of Space·Process·Time: chronon (past = PERFECTIVE) ≡ scenario (future = PROSPECTIVE) — one
# structure, opposite time.  This pack declares that coordinate as vocabulary, and the two Sets a
# coordinate is joined to, BEFORE the scenario port mints them (a port that mints a Set the lexicon
# does not define is reported).
#
# The point of declaring it as membership: a coordinate that was PLANNED and then HAPPENED holds
# BOTH memberships.  `perfective` is ADDED; `prospective` is NOT removed and NOT overwritten.  What
# was planned stays legible beside what occurred — including where they differ — which a meta field
# rewritten in place destroys.  Aspect is therefore never a rewrite, and never a single value.

def "aspect" "Aspect — where a coordinate stands in Akasha Time: authored in advance (PROSPECTIVE) or holding as the record of what happened (PERFECTIVE). It is a MEMBERSHIP, not a field: one structure read in two times, so both memberships may hold at once."
al aspect aspect
set.add name="aspect:vocabulary" id="aspect"

def "aspect:prospective" "PROSPECTIVE — authored in advance: a plan, a scenario, a step that has not happened yet. A coordinate joins set:aspect:prospective when it is written, and KEEPS that membership for good — running it never revokes the fact that it was planned."
al aspect:prospective prospective
ln aspect:prospective aspect sys:is_a
set.add name="aspect:vocabulary" id="aspect:prospective"

def "aspect:perfective" "PERFECTIVE — the record: it happened. Running a scenario ADDS set:aspect:perfective to each coordinate it walks. A coordinate that carries both memberships was planned and then occurred; one that carries only prospective is still outstanding; one that carries only perfective happened unplanned."
al aspect:perfective perfective
ln aspect:perfective aspect sys:is_a
set.add name="aspect:vocabulary" id="aspect:perfective"

def "aspect:sets" "The aspect Sets — `set:aspect:prospective` and `set:aspect:perfective`. Declared here, populated by the scenario / chronon ports at run time; they hold COORDINATES, so a read of one never answers with the aspect atom itself. Membership is additive and is never removed: the difference between the two Sets is the difference between what was intended and what occurred, and that difference is the readable part."
set.add name="aspect:vocabulary" id="aspect:sets"
