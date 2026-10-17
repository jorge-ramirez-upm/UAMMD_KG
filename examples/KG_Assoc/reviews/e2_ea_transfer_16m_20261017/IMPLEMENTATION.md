# Authorized nine-history derived E2 preparation

Starting SHA: `798cf932510a9345a0103f2706e1744e4d3b17a9` (clean local and remote KremerGrest).
Authority: the user's explicit 16M E2 preparation milestone, 2026-10-17.
Only Ea6/8/10 × r001/r002/r003 are authorized. Each starts from its original
qualified corrected-C1 Ea4/Ee8 absolute 8M parent, with independent fresh streams,
and requests exactly 16M additional steps, ending at absolute 24M. Aggregate cap
is 144M. No smoke endpoint is a parent and no Ea4 history is authorized.

## Minimal validation/front-end changes

The ordinary executable does not contain initial device readback or the independent
candidate oracle. The diagnostic executable previously rejected any length over
10k. Its validation-only cap now has one exception: exactly 16M steps, explicit
chemical reseeding and Ea4-to-Ea6/8/10 switching, a nonempty restart/branch identity,
no reference-control flag, and absolute parent step exactly 8M. This code is inside
`KG_ASSOC_VALIDATE_CANDIDATES`; the ordinary executable's preprocessed simulation
tokens are unchanged except two CUDA error-report line numbers (1103→1113 and
1159→1169). These metadata changes do not alter a successful trajectory. No loader, integrator, reaction, candidate search, force or
frozen physics implementation is modified. Historical executables are preserved;
all affected targets must be rebuilt in a fresh authenticated out-of-tree build.

The existing derived planner already supports ordinary segments and full parent
provenance. The launcher now selects the diagnostic executable for its exact 16M
branches, rejects other ordinary derived lengths/targets or replica selections,
and requires a plan-bound `e2_derived_segment` approval explicitly binding target,
replicas [1,2,3], 16M/history, 48M/triplet, start 8M and end 24M. Only titan can launch.
The existing global preparation lock, immutable paths, live source checks, stream
collision checks, matching-smoke requirement and stop-on-first-failure behavior stay.
The endpoint validator requires readback and every chemistry-sweep oracle record
for these ordinary derived branches even if a caller supplies `oracle=False`.

Because a cap-only diagnostic rebuild changes its binary hash, inheritance of the
completed smoke permits only an exact canonicalized source transition: the two
native cap guards above and the validator's mandatory diagnostic gate. Both old
and new executable hashes are checked. Every remaining scientific source hash must
match exactly; no blanket exclusion of native/validation files is introduced.
CPU tests reject modified physical hashes and tampered build/source identities.
Ordinary E2 and prior scoped-smoke behavior retain their existing checks.

## Execution and review policy

Each history is one uninterrupted 16M segment. 500k scientific windows partition
its observations into 32 windows; they are not integrator restarts. The established
restart does not preserve GJ internal/noise memory, so no bitwise checkpoint resume
is claimed or added. A failed attempt is preserved and never reseeded/retried.
An outer campaign driver stops before any subsequent history/system on failure.

Every started history must execute actual initial device readback before MD,
then the independent host oracle on synchronized GPU-evolved positions every
chemistry sweep, plus standard numerical, chemistry, counter and output checks.
Complete endpoint replay and hashing are required before a completion receipt.
The nine descendants retain three original statistical preparation units, paired
across barriers. Initial bonds are left-censored; no correlations are stitched
across the new-stream boundary. Sparse Ea10 topology is not stationarity evidence.

The later assessment must cover 500k/1M/2M windows, early/middle/late changes,
returns, network identity coverage/residence, conformation, event-integrated
exposures, correlation/ESS and 5/10/20-block sensitivity where resolved. Existing
E2 scientific qualifications remain. Recommendations do not register acceptance.
No registry selection, activation, production preparation or extra MD is allowed.
