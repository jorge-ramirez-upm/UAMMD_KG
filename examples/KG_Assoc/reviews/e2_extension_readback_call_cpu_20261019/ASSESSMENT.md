# Repaired Ea extension readback call path: CPU-only handoff

The validation-only initial-readback dispatch is repaired. Six fresh immutable
Ea8/Ea10 extension preparations and a new optimized native build are ready for
**separately authorized user-run GPU validation/execution**. This milestone ran
zero GPU steps. All six preparation approvals explicitly deny GPU execution.

Starting clean local/remote KremerGrest SHA:
`32adf91b3dda2ef94b535597744234685d422e87`.
Repair source commit before compilation:
`055a1a1de43a04edebaad76364726d53cfe654f5`.
Date: 2026-10-19 Europe/Madrid.

## Repair and evidence levels

The old pre-MD call only ran for reseeded chemistry. It now uses the small shared
`dispatchInitialReadback(reseedChemistry, e2Extension, callback)` dispatcher,
which invokes the unchanged device-readback function once when either flag is
true. Ordinary restarts with both flags false keep their previous behavior.
Reseeded preparations retain their existing readback. The call remains after
integrator construction and before the first forwardTime call. Exceptions
propagate to the native fatal path before MD integration.

The complete expected-float32 materialization/readback implementation is unchanged.
Exact position/velocity/identity/type/partner comparisons, reciprocity, candidate
oracle and fail-stop behavior remain mandatory. No force, reaction probability,
physical candidate search, integrator setting, RNG implementation, physical
restart restoration or frozen parameter changed. A source comparison reconstructs
the entire original physical tail after reversing only this validation dispatch.
All remaining physics/header sources retain their original bytes.

| Evidence | Actually exercised | Limit |
|---|---|---|
| Source/placement checks | Production block wired to real readback before first integration; unchanged readback body/physics | Static evidence |
| NVCC/GCC -O3 CPU harness | Exact production call block with CPU callback spy; all four flag combinations and callback failures | GPU callback is a spy |
| Mutation control | Compiled harness with extension argument disabled fails | Reproduces omitted extension call |
| Corrected native CPU probe | Selected optimized candidate executable executes the shared dispatcher; four cases, three fail-stop cases | No device construction or readback |
| Missing-evidence integration regression | Actual held native-PASS Ea8 r001 rejects missing readback even with oracle=False; original files unchanged | Held history stays unvalidated |
| Actual initial GPU readback | Not executed | Pending separate approval |
| GPU-evolved-position oracle/new MD | Not executed | Pending separate approval |

A host initialization preflight alone would not establish this call path. The
optimized harness executes the exact production block and observes the named
readback callback, including failure before simulated integration. The compiled
native probe tests its shared dispatcher. Neither is represented as an actual
GPU readback. No synthetic device evidence was created in a real attempt.

A positive execution gate pins the exact corrected native and dispatcher source
identities, checks executable hashes and requires the selected executable's
CPU_ONLY call-path probe to pass. Old, missing, tampered or unknown call paths
are rejected. This gate supplements all original ancestry, parent, plan and
approval checks. Genuine GPU readback evidence will still be required for every
completed trajectory; the probe cannot substitute for it.

## Fresh preparations and authorization boundary

| System | Replicas | Immediate parent | Added/history | Endpoint | 500k windows |
|---|---|---:|---:|---:|---:|
| F04_N010_RP080_EE08_EA08 | r001–r003 | corresponding exact 24M | 16M | 40M | 32 |
| F04_N010_RP080_EE08_EA10 | r001–r003 | corresponding exact 24M | 32M | 56M | 64 |

Prospective completed extensions total 144M steps; new execution is zero. All
six actual parents, source/build identities, initial counters and chemistry
states were authenticated; native host initialization and effective-MD probes
passed. Fresh requested/effective MD streams exclude every historical consumed
and unused reserved stream, including the entire old cohort. Chemistry remains
on the same seed and absolute-step keys, with inherited counters. Fresh GJ noise
is not bitwise continuation; cross-segment IAT/SEM/lifetime origins must not be
stitched. Original parent families remain paired across Ea.

The new state is `aggregate/e2/manual_ea_extensions_readback_v2/state.json`.
New attempts have `_readback_v2_` identities. The held original
`manual_ea_extensions_v1` state, old plans, all reservations and the unvalidated
Ea8 r001 16M trajectory are byte-identical. No current path migrates that failed
attempt into the new cohort or reclaims its seeds. Its missing initial readback
remains absent and its scientific/numerical hold remains in force.

Each of the six new immutable plan-bound approvals is a CPU preparation approval
with `GPU_execution_authorized=false`. The runner and common E2 launcher reject
it before MD. Later separate approval must supply new immutable execution
authorization; no activation command or automatic approval is included here.
RUN_YOURSELF.md gives exact tested commands and the safe interruption procedure
for eventual approved execution. The existing lifecycle still skips independently
validated completions, recovers receipts only with genuine complete evidence,
preserves interrupted attempts and restarts true partials from exact 24M parents
with fresh MD. Failures do not trigger scientific retries or further extensions.

## Validation, preservation and next decision

All **250 Python tests passed**, including the final 41-test focused suite with
no skips, 189 shared regressions, 14 transfer tests against the fresh optimized
front-end, and six formal-registration checks. Native host groups, 398 cutoff
cases, 12 velocity-ULP rejection cases, corrected compiled dispatcher probe and
ordinary-probe rejection also passed. Every assistant job was bounded by timeout
600. TESTS.md contains reproduction and actual limits.

Of 3,128 starting bindings, 3,122 are unchanged; six existing source/test files
have scoped changes. Two new files supply the dispatcher and its CPU regression.
All thirteen formal acceptances/payload bindings, prior reviews, failed/successful
smokes, historical native builds, accepted states, protected outputs and registry
bindings remain preserved. `src/` and `examples/KG/` were not modified.

The repair is ready for a separate decision authorizing user-run GPU validation.
It has not established actual GPU execution of the new call path, new endpoint
completion, equilibration or scientific acceptance. Ea8/Ea10 remain on hold.
Their future review must retain the earlier replica-specific intra/network-drift,
slow renewal, inherited-edge survival and isolated/satellite qualifications.
No formal acceptance, registry selection/activation or production action occurred.
