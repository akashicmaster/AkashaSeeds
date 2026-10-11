# Workbench — the DUTY a workload declares, and what the driver owes it in return.
#
# A workbench is not a laboratory with extra steps. The same bench, the same driver and the same
# workflow machinery run a research experiment, a broadcast programme and an operational business
# process — and those three do NOT want the same behaviour when something goes wrong. An experiment
# that stops after three consecutive failures and waits for a human is behaving correctly. A payroll
# run, or a programme on the air, that does the same thing has just gone silent, and worse, silently:
# it stops appearing rather than reporting.
#
# So the difference is not the DOMAIN (lab vs station vs back office) — it is a DUTY the workload
# declares, and the driver reads. Coded here so a bench can claim it without being a broadcaster, and
# so nothing has to be special-cased by name.

def "wb:duty" "The duty a scheduled workload declares — what the driver owes it when a gate stops it. Declared in the automation policy (`duty:`), not inferred from what the bench is about: the same driver serves research, operations and broadcast, and only the workload knows which guarantee it needs."
al wb:duty duty
set.add name="wb:vocabulary" id="wb:duty"

def "wb:duty:continuous" "CONTINUOUS — this workload must not go silent. Three things follow, and they are the driver's obligations, not the workload's: (1) any gate that stops it WRITES a state and a reason, so a stop is always legible; (2) the failure breaker does not unschedule it — removing a continuous workload from the schedule is the silence itself, and an invisible one, since it simply stops appearing; (3) a start-up run that produced no OUTPUT leaves the obligation owed, so it is retried (bounded) rather than deferred to the next slot. Declared by a broadcast programme and by an operational process alike; the guarantee is the same, only the output differs."
al wb:duty:continuous duty_continuous
ln wb:duty:continuous wb:duty sys:is_a
set.add name="wb:vocabulary" id="wb:duty:continuous"

def "wb:duty:best_effort" "BEST EFFORT — the default. The workload runs when its trigger is due and its gates allow; a repeated failure may take it off the schedule until someone looks, and a start-up run that produced nothing is simply a run that produced nothing. Correct for a research bench, where stopping to be examined is the right response to repeated failure and where nobody is watching a room."
al wb:duty:best_effort duty_best_effort
ln wb:duty:best_effort wb:duty sys:is_a
set.add name="wb:vocabulary" id="wb:duty:best_effort"
