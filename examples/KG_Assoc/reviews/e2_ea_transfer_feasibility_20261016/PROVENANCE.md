# Restart and reproducibility audit

Starting local/remote HEAD was `bd77a09daa28791972810fc81ffc82b8a9024460`,
branch `KremerGrest`, clean tree. Only this new review directory is added.
[PROVENANCE.json](PROVENANCE.json) binds the exact reference record, its inherited
qualifications, all six endpoint payload digests, parent chemical seeds and the
LAMMPS source commit. No parent is copied, reclassified or rewritten.

The twelve existing records were checked against the previous immutable
[acceptance inventory](../e2_ee12_formal_acceptance_20261016/RECORDS.json), then
validated using the unchanged `exclusive_validate` API. This independently loads
payloads; the catalog alone is a deferred metadata inventory. It still reports
12 acceptances, no registry view/selection, and absent production authorization
for all 23 systems. Eight non-associating systems retain `E1_acceptance_unknown`;
the three higher-Ea systems retain `review_required`. No accepted scope expands.

## Reference lineage

Only corrected C1 absolute-8M prefixes are candidates for future transfer:
`banks/e2_extensions/C1_periodic_recovery_v1/r001/state`, `r002/state`, `r003/state`.
The permanent/chemical payloads are bound by the accepted record and the frozen
remaining-inventory map. Parent history seeds are 22001/22002/22003; corrected
6–8M MD requests were 32001/32002/32003, effective 3928609932/3937019018/3945428108.
The same three original histories remain the independent units.

`reproduce.py` calls the established corrected-C1 authenticator with replay enabled.
That reader uses `authenticate_parent(..., oracle=False)` and the CPU-only
`validate_periodic_e2_smoke.validate(..., oracle=False, md_seed=...)` function
on existing 2M continuations; despite its historical filename, this performs no
smoke run and invokes no GPU executable. It checks numerical/event/network
accounting, original 6M parent identities, final 8M pairs, output/status bindings,
absolute steps, counters, seeds and retained runtime logs. The defective 6M
history is authenticated as lineage only; it is never an accepted transfer start.
The original global `recovery.verify` entry point is not used: it requires the
historical preparation HEAD and is inappropriate at today's review HEAD.
No check is monkeypatched or weakened to bypass that historical constraint.

A second fresh accepted-event replay reconstructs distinct-neighbor gains/losses
from the original ordered events and inherited partner multiplicities. Summing
all four corrected 500k windows reproduces archived event rates exactly. Only
the actual corrected 6–8M segment contributes to reference rates and timings;
defective history and early chemistry are not silently appended to a kinetic
estimate. No IAT, SEM or lifetime is stitched across a restart. This review does
not calculate new slow-mode IATs: it assesses feasibility and preserves the
source's limited topology qualification.

Source status receipt validation and actual event counts are in
[evidence/REFERENCE.json](evidence/REFERENCE.json). The source status qualifier
`short_numerical_test_only` is a numerical-validator field, not a substitute for
the separately existing formal qualified scientific acceptance.

## Restart feasibility findings

The native front end loads snapshot positions/velocities and sidecar partners,
physics, absolute step, chemistry seed and cumulative counts. It supports an
explicit Ea-only switch and an independent new MD stream, with unchanged
initVelocities=false. Initial scalar/numerical/conformation samples precede MD.
A freshly constructed GJ integrator resets its local step and noise memory.
The sidecar has no complete MD/thermostat state. PBC folding and single-precision
loading change representation, so physical-state preservation is understood
modulo periodic images and numeric conversion, not bytewise MD continuation or
unwrapped trajectory continuity.

However, `--seed NEW` on restart currently throws if NEW differs from the parent
seed; the loaded seed is restored unconditionally. No supported fresh-chemistry
stream option exists in this E2 executable/validator. The ordinary planner allows
Ea4 preparation, same-condition extensions, or capped corrected-C1 switching
smokes; it does not support an ordinary higher-Ea derived equilibration. Parent
seed equality and frozen same-system predecessor checks are deliberate guards,
not obstacles to bypass manually. The shared bank identifier omits Ea, so full
system/branch identity is essential in future derived metadata and seed policy.
The native Ea switch is implemented; the complete requested system-specific
fresh-MD/fresh-chemistry transfer workflow is not.

A transferred microstate at target Ea has the same Hamiltonian; changing its
seed and Ea metadata is legitimate only through a documented new preparation
mode, not by modifying an accepted payload. Keep absolute 8M and cumulative
chemical counts, record a branch-age offset and separate old/new seeds. Initial
pairs are left-censored in child lifetime analysis. Full implementation/test
requirements are in [PROTOCOL.md](PROTOCOL.md), and exact source lines are in
[CODE_REFERENCES.md](CODE_REFERENCES.md).

## Authentication limits and preservation

Historical reference executable bytes are unavailable; the formal acceptance
already records that limitation and weaker legacy source/build provenance.
This task authenticates available inputs/outputs, recorded identities and the
accepted record; it does not claim to recreate an unavailable historical binary.
K1/S2/dimer evidence is supporting historical validation, with cutoff/cadence and
system differences explicitly retained. No new stochastic convergence result is
fabricated from deterministic CPU checks.

[PRESERVED_SHA256.json](PRESERVED_SHA256.json) contains all **1,312** inherited
current file bindings: the previous 1,294 plus its 18-file registration commit.
It already includes every tracked `examples/KG` and `src` file; an explicit
enumeration added no missing path. All bindings are checked before and after
analysis and again before commit. [SOURCE_SHA256.json](SOURCE_SHA256.json)
additionally pins 47 inspected source/evidence files, including four local LAMMPS
files and K1/S2 artifacts. Read-only checks hash existing artifacts; they do not
rewrite protected evidence or update historical manifests to today's bytes.
