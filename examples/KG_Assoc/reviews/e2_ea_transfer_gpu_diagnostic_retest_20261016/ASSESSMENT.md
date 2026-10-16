# Ea-transfer GPU diagnostic retest — failed before MD

**Decision: retain the hold; do not advance to a kinetic screen.** The first
history, the reseeded Ea4 r001 control, failed its new initial device readback
before any integration or chemical sweep. The established launcher stopped the
campaign immediately. The other eleven histories were not executed. Aggregate
MD usage is **exactly zero additional steps**, against a 120,000-step authorization.
There are no completed smoke endpoints and no new acceptance.

Starting clean local and remote KremerGrest HEAD:
`ecce23aad26884d0ec270a25d769ca0abf341a5b`. Date: 2026-10-16.
All four immutable plans bind this SHA. Their source/build checks, exact parents,
fresh streams, twelve host initialization probes and plan-bound approvals passed.
Four branch attempts contain twelve histories, following the established planner's
three-replica convention. No alternate launch mechanism was used.

## Observed failure and forensic distinction

The GPU initialized on the authenticated TITAN Xp, constructed 43,563 particles,
loaded the 40,000 permanent bonds, reciprocal chemical partners and preserved
velocities, and constructed the GJ integrator. The validation-only device-to-host
copies actually executed. The complete 43,563-row readback was saved before the
native executable rejected it:

`STAR_ASSOCIATION_SMOKE FAIL: initial device state differs from authenticated loader representation`

The failed footer records zero coordinate error and maximum velocity error
`1.1917114273174434e-07`. Independent CPU reanalysis against the authenticated
parent finds **every actual device coordinate and velocity exactly matches the
parent's prescribed float32/PBC representation**, with exact IDs, types and
partners. The diagnostic's expected-velocity column is inconsistent with that
representation: x is wrong for 43,559 particles, y for 43,556, z for zero. All x/y
expected values equal the unrounded serialized parent doubles; all z expected
values equal float32. Nine serialized z values happen to be exactly representable.

This localizes the discrepancy to how expected evidence is materialized. At
`kg_assoc_stars.cu:734`, float casts are immediately widened into
`std::array<double,3>`. The new **host-only** compiler probe reproduces the same
x/y pattern using the recorded NVCC 12.8/GCC 11.2 `-O3` toolchain. A volatile-float
storage comparison produces all three correctly rounded values; `-O0` also rounds
all three. This demonstrates compiler/optimization-dependent loss of the intended
intermediate rounding in this expression. It does not identify which compiler
pass is responsible or prove that a proposed runtime change fixes the whole path.
No diagnostic or runtime implementation is changed in this milestone.

For the illustrative parent value 0.270623, the saved expected x velocity is
0.270623, while actual GPU x is 0.27062299847602844, exactly float32(0.270623).
`RESULTS.json`, `COMPILER_PROBE.json`, the probe logs and
[READBACK_ERRORS.png](READBACK_ERRORS.png) preserve the evidence.

The native readback remains **failed**, despite the independent fidelity result.
The corrected candidate oracle was **not reached**: its output contains only a
header, with zero comparison sweeps. No candidate mismatch occurred and no pair
mismatch file was produced. Thus this retest does not resolve the original GPU
candidate-search concern. The earlier failed Ea8 history remains failed historical
evidence; none of its outputs or consumed streams was reused.

## Scope of scientific observations

The failure occurs before Kinetics construction, the initial state/numerical/
conformation writes and the MD loop (`kg_assoc_stars.cu:1059–1095`). The state,
event, numerical and conformation files are empty. No final restart or sidecar,
completion marker or complete receipt exists. This establishes zero MD steps,
zero chemical/neighbor events and zero integrated exposures for the started
history. Rates are **undefined (zero exposure)**; the eleven unstarted histories
have no activity observations. Empty outputs are not evidence of suppressed Ea10
reactions. There is no event replay interval, energy time series, post-integration
geometry check or initial/final population contrast to validate.

Only the initial reference graphs and snapshot conformations can be reported.
They are tabulated below and fully enumerated in RESULTS.json (multiplicities
0–4, intra-loop and distinct-degree distributions, components and isolated IDs).
Their identity is authenticated for all planned parents; device-state fidelity
was observed only for Ea4 r001. Molecule labels in the readback are host metadata,
not a separate device molecule property. Permanent topology was authenticated
at input and its load count logged; there is no separate device bond-table dump.
No native conformation or energy sample was emitted before termination.

The exact probabilities remain
`q(Ea)=-expm1(-20*exp(-Ea))` at T=1, Nevery=100 and dt=.01. Relative to Ea4,
the q ratios are approximately 0.15769168, 0.02180140 and 0.00295906 for Ea6/8/10.
They are algorithmic ratios, not observed kinetic results. There is no usable new
control rate with which to make the requested conditional rate comparison.
Existing control results from the earlier smoke cannot stand in for this failed
reseeded control. No inference about coupled equilibrium invariance follows.

The three original parent histories remain the independent preparation units;
cross-barrier descendants would be paired by parent. All reference qualifications
carry over: incomplete slow-topology decorrelation, possible initialization bias,
corrected-from-defective historical C1 lineage and limited historical executable
byte authentication. Fresh streams do not erase those limitations. GJ internal
state resets with a fresh MD stream: the prepared branch is **not bitwise MD
continuation**. Correlations or bond lifetimes must not be stitched across 8M.

## Smallest corrective next step

Repair only the validation path's construction of expected represented velocities,
forcing an actual float32 materialization before widening. Test the actual compiled
expression under the exact campaign compiler/optimization, including the saved
parent values, all axes and deliberately corrupted actual velocities. Keep exact
comparison and the physical loader, kernels, candidate search and random semantics
unchanged. Build a new unique out-of-tree executable and authenticate it.

After that CPU repair, seek a **new separately authorized capped GPU retest**, with
fresh attempts and reservations. Preserve this attempt as failed and retire the
whole reservation set, including its eleven unexecuted rows. Do not resume this
campaign or substitute seeds to obtain a pass. The independent oracle must still
actually execute successfully; CPU success is insufficient. A kinetic screen
remains on hold. A successful later smoke would establish execution only, not
equilibrium invariance, topology mixing or production suitability.

## Validation and preservation

149 shared/readback regressions, fourteen transfer tests and five new forensic
analysis tests pass (168 Python tests total). Host candidate regressions, 398
additional cutoff/periodic cases and injected evidence tests pass. The native host
self-test passes. The first shared-suite invocation omitted two review import
paths: 135 tests passed and two import errors occurred. That log is retained;
the documented environment then passed all 149. No failed GPU history was rerun.

All **1,773** starting file bindings remain byte-identical, including twelve formal
acceptance records and their payloads, earlier reviews, historical builds/source
bindings and all 106 previous failed-smoke artifact bindings. All twelve acceptances
also passed fresh exclusive validation before planning. New campaign metadata and
the partial outputs are separately bound in NEW_OUTPUTS_SHA256.json. No existing
simulation/campaign source file, frozen physics, examples/KG or src file changed.
There is no acceptance, registry action, longer equilibration or production action.
See [EXECUTION.md](EXECUTION.md) and [VALIDATION.md](VALIDATION.md) for exact identities
and reproduction. The final commit is the containing dossier commit, reported
following push, avoiding a self-referential Git SHA.

## Per-history outcomes

| Ea | Replica | Outcome | MD steps | Chemical seed | Requested / effective MD seed |
|---|---|---|---:|---:|---|
| 4 | r001 | failed_before_MD | 0 | 720401 | 730401 / 2405369836 |
| 4 | r002 | not_executed | 0 | 720402 | 730402 / 2380232682 |
| 4 | r003 | not_executed | 0 | 720403 | 730403 / 2388633576 |
| 6 | r001 | not_executed | 0 | 720601 | 730601 / 1939613503 |
| 6 | r002 | not_executed | 0 | 720602 | 730602 / 1914476345 |
| 6 | r003 | not_executed | 0 | 720603 | 730603 / 1922877243 |
| 8 | r001 | not_executed | 0 | 720801 | 730801 / 3069923887 |
| 8 | r002 | not_executed | 0 | 720802 | 730802 / 3044786741 |
| 8 | r003 | not_executed | 0 | 720803 | 730803 / 3053187635 |
| 10 | r001 | not_executed | 0 | 721001 | 731001 / 454635296 |
| 10 | r002 | not_executed | 0 | 721002 | 731002 / 429498146 |
| 10 | r003 | not_executed | 0 | 721003 | 731003 / 437899044 |

Only Ea4 r001 has a logged actual effective MD seed; all other MD values are authenticated planned/host-queried seeds. No child chemical sweep was executed.

## Reference initial populations (not new trajectory results)

| Parent | Bonds | Intra / inter | L1 / L2 | Mean distinct degree | Giant | Isolated stars | Rg² | Center–terminal R² |
|---|---:|---|---|---:|---:|---|---:|---:|
| r001 | 1783 | 100 / 1683 | 40 / 33 | 3.286 | 996 | [143, 526, 595, 950] | 7.040508 | 15.951796 |
| r002 | 1787 | 85 / 1702 | 37 / 42 | 3.33 | 999 | [272] | 6.961489 | 15.603110 |
| r003 | 1803 | 84 / 1719 | 47 / 37 | 3.348 | 1000 | [] | 6.988360 | 15.827429 |
