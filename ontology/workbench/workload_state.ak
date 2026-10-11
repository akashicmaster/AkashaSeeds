# Workbench — a WORKLOAD's state and the reason a gate stopped it, in workload terms.
#
# A scheduled workload is in exactly ONE state at a time and a stop always carries a REASON. Both are
# the platform's vocabulary, minted here: the driver names a state or a reason by its bare id, and
# `wl:state:<id>` / `wl:reason:<id>` is the atom that id resolves to. An application that has its own
# words for these (a broadcast's "on air") defines them in its own packs and relates them to these.

def "wl:workload_state" "Workload state — the condition a scheduled workload is in at a given moment, whether it is a broadcast programme, a research bench or an operational process. A workload is a member of exactly one state Set at a time; the previous membership ENDS on the bench clock rather than being deleted, so the history reads as validity."
al wl:workload_state workload_state
set.add name="wb:vocabulary" id="wl:workload_state"

# ── the four states ───────────────────────────────────────────────────────────────────────────
def "wl:state:warming_up" "warming up — registered, and its boot airing is queued but has not aired yet. The state of a studio between provisioning and its first airing; NOT an error and not an absence of information."
al wl:state:warming_up wl_state_warming_up
ln wl:state:warming_up wl:workload_state sys:is_a
set.add name="wb:vocabulary" id="wl:state:warming_up"

def "wl:state:on_air" "on air — a turn of this workload aired inside the live window. What a listener is hearing was generated for this airing."
al wl:state:on_air wl_state_on_air
ln wl:state:on_air wl:workload_state sys:is_a
set.add name="wb:vocabulary" id="wl:state:on_air"

def "wl:state:rebroadcast" "rebroadcast — the last airing is being repeated until the next scheduled one lands, because the workload is shorter than its interval. A rebroadcast is NOT an airing: no model call, no reservation, no new observation and no new atom. It is read from the last airing, and it is labelled, because filling a gap is honest while presenting an old airing as live is not."
al wl:state:rebroadcast wl_state_rebroadcast
ln wl:state:rebroadcast wl:workload_state sys:is_a
set.add name="wb:vocabulary" id="wl:state:rebroadcast"

def "wl:state:standing_by" "standing by — registered and not playing. Always carries a REASON (wl:reason:*): an admission or provider refusal when there was one, otherwise the next scheduled slot. Silence without a reason is the defect this state exists to prevent."
al wl:state:standing_by wl_state_standing_by
ln wl:state:standing_by wl:workload_state sys:is_a
set.add name="wb:vocabulary" id="wl:state:standing_by"

# ── the reasons the driver names ───────────────────────────────────────────────────────────────
def "wl:reason:fresh" "fresh — the workload's last airing is younger than its interval, so the boot airing was skipped. This is what makes a redeploy idempotent: a restart at 13:07 after a 13:00 airing neither airs twice nor spends twice."
al wl:reason:fresh wl_reason_fresh
set.add name="wb:vocabulary" id="wl:reason:fresh"

def "wl:reason:llm_pool" "llm_pool — admission refused the airing because the day's shared PROVIDER POOL could not hold its reservation: other workloads have it committed. The airing is not started (rather than dying half-way), and the workload goes first next time. NOT the same as budget_calls / budget_tokens, which are this cell's OWN ceilings — reading one for the other sends an operator to the provider when the limit is ours."
al wl:reason:llm_pool wl_reason_llm_pool
set.add name="wb:vocabulary" id="wl:reason:llm_pool"

def "wl:reason:provider_429" "provider 429 — the model provider rate-limited the call, so the turn produced nothing and was recorded standby. Distinct from llm_pool: the pool had room, the provider refused."
al wl:reason:provider_429 wl_reason_provider_429
set.add name="wb:vocabulary" id="wl:reason:provider_429"

def "wl:reason:provider_capacity" "provider capacity — the model provider could not take the call for lack of capacity (distinct from the 429 rate limit), so the turn produced nothing and was recorded standby. The driver treats it as transient and retries it with a growing backoff."
al wl:reason:provider_capacity wl_reason_provider_capacity
set.add name="wb:vocabulary" id="wl:reason:provider_capacity"

def "wl:reason:provider_absent" "provider absent — no model provider is available to this cell for the call, so the turn could not be produced and was recorded standby. The driver does not treat it as transient: it waits for the next trigger."
al wl:reason:provider_absent wl_reason_provider_absent
set.add name="wb:vocabulary" id="wl:reason:provider_absent"

def "wl:reason:no_text" "no text — the provider answered but produced nothing usable for that turn (an empty or refused completion). The turn is recorded standby and NOTHING is said: a turn the model did not produce is never invented."
al wl:reason:no_text wl_reason_no_text
set.add name="wb:vocabulary" id="wl:reason:no_text"

def "wl:reason:runs_per_day" "runs per day — the workload has already run its declared number of times today (policy `budget.runs_per_day`). The next airing is tomorrow's first slot. This is the workload's OWN schedule being honoured, not a refusal by anything outside it."
al wl:reason:runs_per_day wl_reason_runs_per_day
set.add name="wb:vocabulary" id="wl:reason:runs_per_day"

def "wl:reason:not_provisioned" "not provisioned — a RUNTIME PRECONDITION of the workload is missing: its cycle is not on the bench, or a grant it needs is absent. The declaration says what the workload is; this says the cell has not been reconciled to it. It is NOT a failure of the workload and must never be reported as one: for two days a shelf whose bench had no workflow at all was reported as a tripped breaker and a fresh skip, which sent every reader looking in the wrong place. The cure is a boot (which reconciles), never a retry."
al wl:reason:not_provisioned wl_reason_not_provisioned
set.add name="wb:vocabulary" id="wl:reason:not_provisioned"

def "wl:reason:waiting_source" "waiting on a source — the workload declares a source it reads from (policy `requires`) and that source is not present-and-frozen yet, so the airing is held. A DECLARED wait, not a stall: it clears by itself when the source freezes, and it is named here so the wait is visible rather than looking like silence."
al wl:reason:waiting_source wl_reason_waiting_source
set.add name="wb:vocabulary" id="wl:reason:waiting_source"

def "wl:reason:breaker" "breaker — the workload's runs failed consecutively up to its declared `on_failure.breaker`, so the driver stopped starting new ones. For a RESEARCH bench that means dropping to manual until an operator looks. For a STATION workload it does not: a broadcaster that removes itself from the schedule is exactly the silence the airing ruling forbids, so it stays armed, reports THIS reason, and keeps trying on its declared cadence."
al wl:reason:breaker wl_reason_breaker
set.add name="wb:vocabulary" id="wl:reason:breaker"

# ── a reason the PLATFORM owns, minted here and nowhere else ─────────────────────────────────────
# The driver's own guard, applying to any continuous workload whether or not it broadcasts.
def "wl:reason:spent_without_effect" "spent without effect — a CONTINUOUS workload's last K runs each spent model calls and none produced the declared effect, so the driver stopped it for real (to manual), whatever its duty. A continuous workload normally keeps its cadence through failures, because stopping a broadcaster is the silence the airing ruling forbids; that rule assumes retrying is free, and here every retry was paid for. K is 3 unless the declaration sets `on_failure.spent_without_effect`. A new build or config re-arms it — the only thing that can change the outcome of a run that is being paid for and producing nothing. Named after 09-25, when ~160 paid runs of the news show went by with the pool at 498/500 and nothing on the record said why."
al wl:reason:spent_without_effect wl_reason_spent_without_effect
al wl:reason:spent_without_effect spent_without_effect
set.add name="wb:vocabulary" id="wl:reason:spent_without_effect"

def "wl:reason:onto_load" "held for an ontology load — an ontology load in flight declares a name this workload declares it reads (a `pins` value, or a `requires` Set), so the driver does not pick it this tick: a run now would resolve a pack being rewritten under it. On a cell's FIRST load every workload is held, because the graph is not there yet; after that only the workloads a changed pack touches wait, and the rest keep their cadence. Not a run and not a failure: nothing is recorded, the breaker is untouched, and the hold lifts on the tick after the load's `ontology.loaded` gate opens. Named after 09-28, when one 400-atom pack held all five programmes for 17 minutes."
al wl:reason:onto_load wl_reason_onto_load
al wl:reason:onto_load onto_load
set.add name="wb:vocabulary" id="wl:reason:onto_load"

# ── what a workload IS, as the declaration states it ─────────────────────────────────────────────
def "wl:workload" "Workload — one scheduled unit of work on a workbench, DECLARED in a single file (`config/workbench/workloads/<slug>.json`) and read by one driver. Nine fields, frozen: bench, workflow, society, trigger, duty, effect, appetite, budget, pins. Every field is also a membership on the workload's atom (`set:wl:*`), so the declaration is inspectable as data. Identified by `<bench>/<slug>` — the key the model-provider ledger is accounted against."
al wl:workload workload
set.add name="wb:vocabulary" id="wl:workload"

def "wl:effect" "Effect — what a run of this workload PRODUCES, and therefore who can see it. Declared, never inferred from what the workload is about: `publish` means the output faces the public (it gets a row on the programme guide and a room), `record` means it writes to the graph and nothing leaves the cell. It is what `bench.info`'s `programmes` counts, in place of a test for what the bench is called."
al wl:effect effect
set.add name="wb:vocabulary" id="wl:effect"

def "wl:effect:publish" "publish — a run of this workload puts something in front of the public. It carries a guide row, a state and a reason at all times, and its stops are visible to a listener."
al wl:effect:publish effect_publish
ln wl:effect:publish wl:effect sys:is_a
set.add name="wb:vocabulary" id="wl:effect:publish"

def "wl:effect:record" "record — a run of this workload writes to the graph and nothing leaves the cell. No guide row, no room; a research bench's default, and the reason a bench that waits is simply idle rather than a silence somebody is watching."
al wl:effect:record effect_record
ln wl:effect:record wl:effect sys:is_a
set.add name="wb:vocabulary" id="wl:effect:record"

def "wl:trigger" "Trigger — WHEN a workload is due. `boot` (a deploy airs: the schedule's first slot is the boot) and/or `then`, which is either `every:<n>s` or `daily:HH:MMZ` (UTC, and the Z is in the spelling so nobody has to remember which clock). It is the only cadence: a workload with a second timer of its own is the defect this field replaced."
al wl:trigger trigger
set.add name="wb:vocabulary" id="wl:trigger"

def "wl:appetite" "Appetite — what ONE run of this workload asks of the model provider: `llm_calls_per_run` and a `weight` for its share of a contested day. Read at admission to size the reservation, and DERIVED from the declaration rather than taken from whoever submitted the job, because a client that could name its own appetite could spend another workload's carry-over credit."
al wl:appetite appetite
set.add name="wb:vocabulary" id="wl:appetite"

def "wl:budget" "Budget — what a DAY of this workload may cost: `per_day` runs (the airing allowance, not poll beats), `max_wall_s` and `max_steps` per run. `per_day` is the ceiling the driver holds it at, and reading it as anything else is how a guide came to serve `219 / 4320` on the day the real ceiling was spent."
al wl:budget budget
set.add name="wb:vocabulary" id="wl:budget"

def "wl:pins" "Pins — the atoms and Sets this workload's template steps resolve against, named in the declaration so a template step stays a fixed line of data. A pin that resolves to an empty Set is a workload standing by on `waiting_source`, which is the correct outcome: a programme with no source says so rather than inventing one."
al wl:pins pins
set.add name="wb:vocabulary" id="wl:pins"
