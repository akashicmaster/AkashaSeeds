# Akasha Station — the state vocabulary of a registered programme.
# Ruling: `ruling-station-airing-2026-09-18.md`. A registered programme is NEVER silent: it is in
# exactly one of the four states below at any moment, and a standing-by always carries a reason.
# `unclassified` stays reserved for a value that does not exist, which a registered programme's
# cells never are.

def "station:programme_state" "Programme state — the condition a REGISTERED station programme is in at a given moment. A programme is a member of exactly one state Set at a time; the previous membership ENDS on the bench clock (it is not deleted), so the state history is readable as validity rather than overwritten."
al station:programme_state programme_state
set.add name="station:vocabulary" id="station:programme_state"

# ── the four states ──────────────────────────────────────────────────────────────────────────────
def "station:state:warming_up" "warming up — registered, and its boot airing is queued but has not aired yet. The state of a studio between provisioning and its first airing; NOT an error and not an absence of information."
al station:state:warming_up warming_up
ln station:state:warming_up station:programme_state sys:is_a
set.add name="station:vocabulary" id="station:state:warming_up"

def "station:state:on_air" "on air — a turn of this programme aired inside the live window. What a listener is hearing was generated for this airing."
al station:state:on_air on_air
ln station:state:on_air station:programme_state sys:is_a
set.add name="station:vocabulary" id="station:state:on_air"

def "station:state:rebroadcast" "rebroadcast — the last airing is being repeated until the next scheduled one lands, because the programme is shorter than its interval. A rebroadcast is NOT an airing: no model call, no reservation, no new observation and no new atom. It is read from the last airing, and it is labelled, because filling a gap is honest while presenting an old airing as live is not."
al station:state:rebroadcast rebroadcast
ln station:state:rebroadcast station:programme_state sys:is_a
set.add name="station:vocabulary" id="station:state:rebroadcast"

def "station:state:standing_by" "standing by — registered and not playing. Always carries a REASON (station:reason:*): an admission or provider refusal when there was one, otherwise the next scheduled slot. Silence without a reason is the defect this state exists to prevent."
al station:state:standing_by standing_by
ln station:state:standing_by station:programme_state sys:is_a
set.add name="station:vocabulary" id="station:state:standing_by"

# ── the reasons a standing-by or a skipped airing carries ────────────────────────────────────────
def "station:skip_reason" "Skip / standby reason — why an airing did not happen, or why a registered programme is not playing. Coded as vocabulary so a refusal can never reach a surface as a bare string; a new reason is added here when it is added to the code, never inline."
al station:skip_reason skip_reason
set.add name="station:vocabulary" id="station:skip_reason"

def "station:reason:fresh" "fresh — the programme's last airing is younger than its interval, so the boot airing was skipped. This is what makes a redeploy idempotent: a restart at 13:07 after a 13:00 airing neither airs twice nor spends twice."
al station:reason:fresh reason_fresh
ln station:reason:fresh station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:fresh"

def "station:reason:llm_pool" "llm_pool — admission refused the airing because the day's shared PROVIDER POOL could not hold its reservation: other programmes have it committed. The airing is not started (rather than dying half-way), and the programme goes first next time. NOT the same as budget_calls / budget_tokens, which are this cell's OWN ceilings — reading one for the other sends an operator to the provider when the limit is ours."
al station:reason:llm_pool reason_llm_pool
ln station:reason:llm_pool station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:llm_pool"

def "station:reason:provider_429" "provider 429 — the model provider rate-limited the call, so the turn produced nothing and was recorded standby. Distinct from llm_pool: the pool had room, the provider refused."
al station:reason:provider_429 reason_provider_429
ln station:reason:provider_429 station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:provider_429"

def "station:reason:provider_capacity" "provider capacity — the model provider could not take the call for lack of capacity (distinct from the 429 rate limit), so the turn produced nothing and was recorded standby. The driver treats it as transient and retries it with a growing backoff."
al station:reason:provider_capacity reason_provider_capacity
ln station:reason:provider_capacity station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:provider_capacity"

def "station:reason:provider_absent" "provider absent — no model provider is available to this cell for the call, so the turn could not be produced and was recorded standby. The driver does not treat it as transient: it waits for the next trigger."
al station:reason:provider_absent reason_provider_absent
ln station:reason:provider_absent station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:provider_absent"

def "station:reason:budget_calls" "budget calls — AKASHA'S OWN daily CALL ceiling is spent (llm.budget calls=), not the provider's. Distinct from llm_pool: the pool had room and the provider was willing; this cell stopped the airing itself, to hold the spend it was told to hold. The fix is a cadence or a ceiling, and both are ours."
al station:reason:budget_calls reason_budget_calls
ln station:reason:budget_calls station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:budget_calls"

def "station:reason:budget_tokens" "budget tokens — AKASHA'S OWN token ceiling for the day or the month is spent (llm.budget tokens_day= / tokens_month=). This is the MONEY bound: cost is per token, so this is the ceiling that actually caps the bill. Distinct from budget_calls, which bounds how often, and from llm_pool, which is the shared pool having no room."
al station:reason:budget_tokens reason_budget_tokens
ln station:reason:budget_tokens station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:budget_tokens"

def "station:reason:waiting_source" "waiting on a source — the programme declares a source it reads from (policy `requires`) and that source is not present-and-frozen yet, so the airing is held. A DECLARED wait, not a stall: it clears by itself when the source freezes, and it is named here so the wait is visible rather than looking like silence."
al station:reason:waiting_source reason_waiting_source
ln station:reason:waiting_source station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:waiting_source"

def "station:reason:runs_per_day" "runs per day — the programme has already run its declared number of times today (policy `budget.runs_per_day`). The next airing is tomorrow's first slot. This is the programme's OWN schedule being honoured, not a refusal by anything outside it."
al station:reason:runs_per_day reason_runs_per_day
ln station:reason:runs_per_day station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:runs_per_day"

def "station:reason:breaker" "breaker — the programme's runs failed consecutively up to its declared `on_failure.breaker`, so the driver stopped starting new ones. For a RESEARCH bench that means dropping to manual until an operator looks. For a STATION programme it does not: a broadcaster that removes itself from the schedule is exactly the silence the airing ruling forbids, so it stays armed, reports THIS reason, and keeps trying on its declared cadence."
al station:reason:breaker reason_breaker
ln station:reason:breaker station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:breaker"

def "station:reason:not_provisioned" "not provisioned — a RUNTIME PRECONDITION of the programme is missing: its cycle is not on the bench, or a grant it needs is absent. The declaration says what the programme is; this says the cell has not been reconciled to it. It is NOT a failure of the programme and must never be reported as one: for two days a shelf whose bench had no workflow at all was reported as a tripped breaker and a fresh skip, which sent every reader looking in the wrong place. The cure is a boot (which reconciles), never a retry."
al station:reason:not_provisioned reason_not_provisioned
ln station:reason:not_provisioned station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:not_provisioned"

def "station:reason:not_said" "not said — the turn was produced but the feed refused it: the speaking client does not own the cast, or the cast is not admitted. No model call is made once this is known. Provisioning repairs it; a retry cannot. Distinct from not_provisioned, which the DRIVER decides before a programme runs: they share a cure and nothing else, and one id for both left a reader unable to tell which of the two had happened."
al station:reason:not_said reason_not_said
ln station:reason:not_said station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:not_said"

def "station:reason:no_text" "no text — the provider answered but produced nothing usable for that turn (an empty or refused completion). The turn is recorded standby and NOTHING is said: a turn the model did not produce is never invented."
al station:reason:no_text reason_no_text
ln station:reason:no_text station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:no_text"

def "station:reason:not_declared" "not declared — this cell's build carries NO declaration for the workload that armed this programme. The programme is RETIRED, not deleted: the society, its feed, its bench and everything it ever aired stand, and a declaration that comes back re-arms it with its history intact. It is the other half of *a declaration is a desired state* — reconciling only ever created, so a workload whose declaration was deleted kept running because nothing looked for the absence. It stops running and stops claiming a slot; nothing is lost."
al station:reason:not_declared reason_not_declared
ln station:reason:not_declared station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:not_declared"

# The two below close the last turns that could stand by WITHOUT a reason (2026-09-26). On 09-25 the
# news show ran ~160 paid airings that aired nothing, and every run record read `reason=''`: the
# platform dropped what the op returned (D10), AND there were turns on this side that returned no
# vocabulary id at all — four that returned a sentence and wrote no record, and every turn that
# RAISED, which returned nothing. A stop that cannot name itself is found by reading code at 3 a.m.

def "station:reason:no_current" "no current passage — a turn that works from the CURRENT passage found none, because nothing of this programme has aired for it to continue from. Never a root cause: the turn that opens the airing (source=next) stood by first, and ITS reason is the one to read. Named so that a reader of an airing where every turn stood by is sent to the first turn instead of the last."
al station:reason:no_current reason_no_current
ln station:reason:no_current station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:no_current"

def "station:reason:turn_error" "turn error — the op RAISED before it could decide — a turn (`bench.air.turn`) or the republish of one (`bench.publish`) — so nothing was said or posted. A defect, never a state to wait out: the exception's class and message are in the `[station] stood by` log line beside this id, together with `paid=yes|no` — whether the model had already been called, which is what separates a free failure from a paid one. A turn that fails this way used to return nothing at all, so the run record read an empty reason and the only evidence was the bill."
al station:reason:turn_error reason_turn_error
ln station:reason:turn_error station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:turn_error"

# D13 (2026-09-26). From the port until this seed the news show's three role prompts carried neither
# `{source}` nor `{last}`: the ネタ帖 item was resolved, never sent, and recorded as the turn's source
# anyway — so the Anchor read out news the model made up, under a source row saying otherwise.
def "station:reason:prompt_without_source" "prompt without source — the turn resolved a source to work from, and the role's declared prompt has no place to put it (no `{source}`), so the source's text would never reach the model. Nothing is generated and no model call is made: a turn must not be recorded against a source it was not given, and a model given no item invents one. The cure is the DECLARATION — add `{source}` to the role's prompt — never a retry."
al station:reason:prompt_without_source reason_prompt_without_source
ln station:reason:prompt_without_source station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:prompt_without_source"

def "station:reason:source_exhausted" "source exhausted — every item of the programme's episode has aired (grounded) and the programme declares `on_exhausted: stand_by`, so it stands by rather than re-air an old item as new. No model call is made. The cure is authoring — add items to the episode Set — not a retry. A programme that reads on (`on_exhausted: wrap`) never stops for this: it takes the least recently aired item."
al station:reason:source_exhausted reason_source_exhausted
ln station:reason:source_exhausted station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:source_exhausted"

# ── the Sets the code joins a programme to ───────────────────────────────────────────────────────
# One membership at a time; the previous one ends on the bench clock rather than being removed.
def "station:state_sets" "The programme-state Sets — `set:station:state:warming_up`, `:on_air`, `:rebroadcast`, `:standing_by`. A programme is joined to exactly one; membership IS the state, and the ended membership stays readable as history rather than being deleted. The Sets hold PROGRAMMES only: they are populated by the station at run time and are declared here, not seeded, so a read of one never answers with the state atom itself."
set.add name="station:vocabulary" id="station:state_sets"

# ── consent: the one stop no boot can clear ──────────────────────────────────────────────────────
def "station:reason:no_consent" "no consent — the space has not been opened to be shown outside itself, so a workload whose effect leaves the world refused. Distinct from every other reason here: it is not a ceiling, not a wait on a source, and not a grant a boot writes. A person decides it (`society.public open=yes`), and until they do, refusing is the correct behaviour rather than a fault to clear."
al station:reason:no_consent reason_no_consent
ln station:reason:no_consent station:skip_reason sys:is_a
set.add name="station:vocabulary" id="station:reason:no_consent"

# ── one vocabulary, two names (step 1 §1.8) ──────────────────────────────────────────────────────
# The driver speaks about a programme, a research bench and a payroll run in the same words, so
# every state and reason carries a `wl:` alias beside its `station:` one. The atom is the same atom;
# a guide row and a stored `reason=` written before this keep resolving, and nothing migrates. The
# platform inverts the stored prefix in step 2; the pack owns the alias, which is why it is here.
al station:state:warming_up wl:state:warming_up
al station:state:on_air wl:state:on_air
al station:state:rebroadcast wl:state:rebroadcast
al station:state:standing_by wl:state:standing_by
al station:reason:fresh wl:reason:fresh
al station:reason:llm_pool wl:reason:llm_pool
al station:reason:provider_429 wl:reason:provider_429
al station:reason:budget_calls wl:reason:budget_calls
al station:reason:budget_tokens wl:reason:budget_tokens
al station:reason:waiting_source wl:reason:waiting_source
al station:reason:runs_per_day wl:reason:runs_per_day
al station:reason:breaker wl:reason:breaker
al station:reason:not_provisioned wl:reason:not_provisioned
al station:reason:no_text wl:reason:no_text
al station:reason:no_consent wl:reason:no_consent
al station:reason:not_said wl:reason:not_said
al station:reason:not_declared wl:reason:not_declared
al station:reason:no_current wl:reason:no_current
al station:reason:turn_error wl:reason:turn_error
al station:reason:prompt_without_source wl:reason:prompt_without_source
al station:reason:source_exhausted wl:reason:source_exhausted
