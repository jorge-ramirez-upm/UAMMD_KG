# Ea-extension source-authorization repair

## Forensic result

Ea8 r001 did not stop before GPU work. Its immutable `started.json`, native
stdout and endpoint records show that the corrected candidate executable ran
from absolute step 24,000,000 to 40,000,000, completed all 16,000,000 requested
steps and printed `STAR_ASSOCIATION_SMOKE PASS`. It recorded 160,000 chemistry
sweeps, 132,319 creations and 130,526 breaks.

The failure happened after native completion. `kg_assoc_e2.launch()` first
called `live_code(plan, approved_overrides)` correctly, but later called
`check_plan(..., live=True)`. That path called `live_code(plan)` without the
approved administrative overrides and raised `prepared extension sources/history
changed` before independent replay/receipt creation. The resulting r001
`incomplete.json` and failed durable-state record remain unchanged.

The exact map comparison at repair time found zero added, missing or changed
entries for every one of the six prepared histories after applying its approved
overrides. The prepared commit is an ancestor of the live commit in every case.
The discrepancy therefore involved only the omitted post-run authorization
argument. No physics, native executable, reaction, candidate search, integrator,
RNG, parent, seed, output command or validation implementation changed.

## Repair

The post-run path now performs `check_plan(..., live=False)` followed by the
same override-aware `live_code()` check used before native launch. Each original
execution approval remains immutable. A new immutable per-replica source
authorization binds that execution-approval SHA, its plan SHA and the exact
three administrative source hashes. The durable state binds each new record.
There is no general whitelist for future source edits.

The regression suite covers exact equality and rejects missing entries, added
entries, a modified physics file and a non-ancestor source history. It also
exercises the normal extension lifecycle with the new authorization argument.

## Campaign status

Ea8 r001 is a completed native trajectory with an independent-validation hold;
it is not a zero-step administrative prelaunch failure and cannot be cleared,
restarted or treated as validated by this repair. Its current failed state stops
the cohort, so the other five histories remain unstarted. They authenticate the
new source authorization but are not authorized to bypass that stop condition.

A zero-step source-authorization failure is safe to clear only when there is no
`started.json`, process/environment receipt, native log, output file or endpoint
artifact. That proof does not hold for Ea8 r001. Any decision to independently
validate its completed immutable outputs or to prepare a replacement is a
separate authorization decision.
