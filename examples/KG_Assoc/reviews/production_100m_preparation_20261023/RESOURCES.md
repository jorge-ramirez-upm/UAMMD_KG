# 100M resource arithmetic and later200M policy

The prepared scope is45×100M=4.5 billion additional steps, each history1,000,000
reduced time units at dt=.01. No execution or allocation has occurred.

`BUDGET.csv` selects the100M rows of the authenticated preceding budget, removes
its proposed raw-stress allocation, and retains the source's explicit linear
approximation:11383.05s per32M steps for43563 atoms, scaled by atom count.
The sum is **696.01 GPU-hours** (29.0 serial GPU-days), excluding interruptions,
analysis, validation, filesystem stalls and hardware variability. The largest
conditions are ~39.5h/history by this approximation, the reference ~9.9h/history.
These are historical-model estimates, not current timing measurements. Polymer
size, density, chemistry/event activity and transfer overhead may invalidate linear
scaling; refine using the separately approved production-compatibility tests.
No promise of runtime precision is made.

The exact fixed binary-bead layout gives **36.8784GB** decimal across45 histories,
including headers and1000 frames/history. Each header is84+12N+8B bytes and each
frame20+12N bytes (N beads,B permanent bonds), as in the existing budget source.
There are **zero raw-stress-trajectory bytes**. Stress final output is195 rows ×45,
with nine columns; it is tiny relative to trajectory storage. The earlier252GB raw
stress proposal is superseded and is not part of this campaign.

Each history additionally has100,000 thermo rows,10,000 COM frames,10,000 topology
frames, all accepted events, final archives and logs. Text bytes depend on the
number of stars, active bonds and accepted events/decimal formatting, so a precise
total is unsupported before measurement. Provision **at least150GB free for the
live campaign as a provisional planning allowance**, and a separate independent
backup of immutable inputs/results. This is not a hard upper bound: measure all
nine-file byte rates in the bounded compatibility runs, extrapolate by actual
cadence/event activity, and reserve2×that measured total if larger. Preserve partial
attempt storage separately; never remove protected history to free space. A user's
future launch preflight must check actual available space, not assume the bead-only
number is sufficient. Tables are prospective estimates only.

For100M, the existing finite grid has195 rows and last raw lag838860.8 with just
one pair. At minimum raw counts8,16,32,64,128 the eligible horizons are respectively
629145.6,314572.8,314572.8,157286.4,78643.2. Eligibility is not terminal-relaxation
resolution or an effective-independent-pair count. Do not infer viscosity from
nominal observation length alone. The existing P4 five-replica32M result is useful
method evidence; its chemistry predates the periodic correction and cannot promise
adequate terminal support for every current condition, particularly Ea10.

## A possible later200M observation

No200M history, stream or approval is prepared. If later scientific analysis shows
a lag-horizon limitation worth addressing, the present executable cannot continue
100M bitwise: it has neither a full MD checkpoint nor integrator/RNG/correlator
restart integration. Under this policy200M means **one new uninterrupted200M run
from an accepted initial pair**, with new attempt/streams/authorization;100M+100M
cannot create an uninterrupted200M correlation measurement.

Minimum future work would consistently update the explicit production-length policy
in schema/protocol, select/test a distinct200M native compile-time target, update
hardcoded launch/status/validation/cadence budgets and authenticate new plans/builds.
Keep the same estimator/configuration unless a demonstrated compatibility problem
requires review. No full restart implementation is implied. Existing100M results
remain separate scientific evidence, not a prefix that can be silently extended.
Nothing in this milestone changes the current100M length policy.
