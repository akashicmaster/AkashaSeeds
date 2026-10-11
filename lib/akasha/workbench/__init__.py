"""
`workbench` — the driver (Part II §A20/§A21): workloads, schedules, provisioning, admission,
states, the LLM gate.

    autorun.py       the auto-execution driver (bench.auto tick, readiness gate, sweep pick, breaker),
                     the leaderboard hydrate regenerator
    provision.py     the ONE provisioning authority — every declared workload (bench, society,
                     casts, capabilities, resources); the boot admin session is obtained here and
                     nowhere else
    admission.py     job.* (submit_job — the one admission point) and workflow.*
    llm.py           the LLM gate's stores (pool, back-off), llm.key / llm.budget / llm.diag
    llm_pool.py      shared LLM resource allocation (reserve / settle / credits)
    llm_provider.py  the one gate every model call passes (meter, pacing, 429 back-off)
    workload.py      the declaration: the nine fields, read here and nowhere else
    workload_provision.py   one declaration → its society, bench branch, Sets and armed policy
    wl_state.py      a workload's state and reason ids, its airing count, the mirror's housekeeping
    x_broadcast.py   the generic outbound-channel poster (thread splitting, the one send)
    learned_head.py  the numpy learner the ML template trains
    MANIFEST.json    what this package contributes: ops, writer-phase bodies, thread units

There is no `station.py`: the news programme's daemon, its turn logic and its X op were the platform
knowing one application by name, and step 2 deleted them. A programme is a DECLARATION now — its
turn is its own Concept Model's op (`concepts/`, the user's), reached by dispatch; what was generic
in that file moved to `wl_state.py` / `workload_provision.py` / `x_broadcast.py`.

It imports the heart only through `lib.akasha.api` and may import `concepts`, `source`, `ontology`.
"""
