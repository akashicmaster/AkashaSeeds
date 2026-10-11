# The assignment file — one line per identity, `<identity> <idset> [on <target>]`.
#
# THIS FILE IS THE AUDIT TRAIL. The in-memory table is its read, never the other way round:
# every permission the cell grants can be traced to a line here, and every observation an
# effect writes carries the line that admitted it (`admitted: {identity, action, target,
# idset}`). That is the provenance Akasha sells, and it costs one field.
#
# WHO WRITES IT
#   boot                 — reads it; writes nothing
#   `identity.assign`    — admin only; appends a line
#   `workload_provision` — appends `<client> <idset> on <place>` for each declaration's own two
#                          places, and `<client> consumer on <resource>` for each `source:pool:` /
#                          `model:` entry of its `requires`; removes a line when it is no longer
#                          declared
#
# A line is `<identity> <idset> [on <target>]`. `#` starts a comment. Blank lines are ignored.
# A target is a place (`<group>/<space>`, `wb:<bench>`, `source:pool:<id>`, …) or a NAMED
# target the gate resolves to a class of places: `feeds` — the source feeds.
# An idset name that is not a row of `config/identity/idsets.json` is a boot error naming the
# line — never a silently ungranted identity.
#
# An AGENT — a cast, an LLM speaking through a client — has NO LINE OF ITS OWN. It acts under
# the client's id-set, and `say` is allowed only as the casts the target workload declares.
# That is the whole delegation mechanism, and it is why `chairman`, `scribe`, `broadcaster`,
# `decider`, `responsible`, `admit` and `owned avatar` are not concepts here: each was a way of
# writing one of these lines.
#
# An identity with NO LINE is a GUEST, not an error. A name that appears nowhere is answered
# exactly as `anonymous` is, so a refusal cannot tell a prober which names exist.
#
# The lines below are the ones a cell cannot boot without. Everything else is appended at
# runtime by the two writers above.


# The internal identities. They are reachable only over TRUST_INTERNAL / TRUST_LOCAL — that is
# whether the caller may be BELIEVED to be them, which is transport trust and a different
# question from what they may do. What they may do is these lines.

# (the application adds no line: the platform's own seed lines — admin, anonymous, the internal identities —
# are written first, and a repeated line is never written twice. Declared identities live in identities.json.)
