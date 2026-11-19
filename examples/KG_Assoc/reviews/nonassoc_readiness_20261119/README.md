# B. Non-associating readiness assessment — 18–19 November 2026

Starting SHA: `4cfb7d3de92020197a328a5b03c5da7b9096c4ff`, `KremerGrest`.
Final publication SHA: `git log -1 --format=%H -- examples/KG_Assoc/reviews/nonassoc_readiness_20261119`.
This is a CPU-only assessment, not a prepared or activated campaign.

## Readiness decision

**24/24 intended E1 states exist and are numerically valid; 0/24 have formal
acceptance for direct non-associating production.** There is no missing E1
configuration and no basis here for automatically repeating equilibration.
Scientific qualification and a narrowly scoped immutable-launcher adaptation
remain prerequisites. Existing E2 acceptance does not automatically accept E1
for direct control production.

[e1.csv](e1.csv) inventories all 24 exact resolved paths and state hashes,
geometry, replica, original seed, protocol argv, Stage-4 duration, final absolute
step, finite positions/velocities, original-input hash, source/executable evidence,
stationarity metrics, retry and acceptance status. Paths are resolved by the
established `e1_bank_path`, not newest-directory selection. Preparation seeds are
12001, 12002 and 12003 in each geometry. All 24 state hashes differ.

| Geometry | Atoms per replica | Stage-4 steps at dt=.01 | Final absolute E1 step | States |
|---|---:|---:|---:|---:|
| F03_N010_RP080 | 32,938 | 2,000,000 | 2,075,900 | 3 |
| F04_N010_RP020 | 174,250 | 2,000,000 | 2,075,900 | 3 |
| F04_N010_RP040 | 87,125 | 2,000,000 | 2,075,900 | 3 |
| F04_N010_RP060 | 58,083 | 2,000,000 | 2,075,900 | 3 |
| F04_N010_RP080 | 43,563 | 2,000,000 | 2,075,900 | 3 |
| F04_N020_RP080 | 86,063 | 2,000,000 | 2,075,900 | 3 |
| F04_N040_RP080 | 171,063 | 8,000,000 | 8,075,900 | 3 |
| F06_N010_RP080 | 64,813 | 2,000,000 | 2,075,900 | 3 |

Stage-4 physical duration is 20,000 or 80,000 time units. The preceding protocol
uses DPD preparation, WCA ramp/promotion and permanent FENE, with chemistry
disabled throughout E1. Total steps are not all at the Stage-4 timestep. Ten
historical histories used dt_DPD=.01; fourteen later histories used the corrected
71,400-step DPD schedule at .002, effective gamma=4.5, followed by 4,500 WCA
steps and Stage 4. Original histories are retained, not retroactively relabeled.
The final GJF NVT stage has target T=1, dt=.01, friction=.5 (damping=2).

RP060/r002 resolves exactly to
`banks/e1_retries/F04_N010_RP060/r002/attempt001/state.e1.lammpsdat`, registered
in `banks/e1/active_states.json`. Its original `banks/e1/.../r002` record has
exit code 1 and `status=incomplete`; it remains preserved and is not a start.
The retry has exit code 0, preparation seed 12002, and an explicit
`previous_attempt` pointing to that failure. No alternative attempt was selected.

## Equilibration evidence and provenance limits

The original review is
`kg_assoc_100m/aggregate/e1/review_20261010T135200_586153Z`;
the stronger audit is
`kg_assoc_100m/aggregate/e1/audit_20261010T154908Z_v1/REPORT.md`.
Their state/diagnostic hashes and the latter's report/CSV/results integrity map
were reauthenticated. Fresh `kg_assoc_e1.check_snapshot` checks pass for all
24: expected geometry/densities and stable IDs, all finite positions/velocities,
permanent bonds strictly inside (0,1.5), correct final header step and seed.
The diagnostic histories are authenticated against the inspected prior audit;
no new MD or costly force reconstruction was required.

The audit found stationary temperature and pressure, and plausible late shape
plateaux. It explicitly describes these as reasonable **E1 starts for E2**,
not unconditional publication-grade direct non-associating acceptance. Integer-time
GJF kinetic temperatures of about .979–.989 are consistent with finite-step
velocity-estimator bias; no velocity rescaling or thermostat retuning is justified.
The remaining nonlinear configurational timestep-accuracy question is unresolved.
For N=40, first-half shape changes reach about 2.3–2.4%, late effective temporal
samples are modest (Rg² roughly 5–18), and slower modes are not excluded. N=20
also has a swelling transient. The audit's autocorrelation truncation is heuristic,
not a rigorous error estimate or automatic equilibration criterion.

The fourteen newer preparation records bind input and executable hashes and
source SHA `b27081b4515604e370b703b8dbb316b9f74e5552`; recorded executable hash
is `44ab8cf8fbded75d74193f207c7f5d246454f418dbb0fd20778c59ea02c1bf60`.
Ten historical records bind source SHA `61aeb9611d7c0ecac327b096504d4e95e5a0cc96`
but lack contemporaneous input/executable hashes. Current input hashes agree
with the prior audit, which does not retroactively certify their use at launch.
No missing historical binary or build provenance has been invented. The full
argv and source SHA per state are in e1.csv; original build logs/records remain
where recorded. No `banks/e1/<geometry>/validation.json` acceptance exists for
any of the eight geometries. The existing numerical reports explicitly leave
`scientific_status=review_required`. No later direct-control acceptance or
resolution of the audit's timestep/N40 qualifications was found in the reviewed
bank, aggregate and tracked acceptance/review infrastructure.

## Independence and comparison

[../production_closure_20261119/pairing.log](../production_closure_20261119/pairing.log)
traces all 45 accepted associating starts through actual E2 plans, extensions,
transfers and historical C1 command records back to the **same 24 resolved E1
states**. Each path is checked against the registered state and hash. The retry
lineage is preserved. Each geometry has three separately seeded preparation
trajectories. Replicas share the original externally supplied geometry input;
different noise and endpoint hashes do not prove loss of all common slow-mode
memory. These are three preparation families, not additional independent samples
created by Ea/Ee variants or later reseeding.

Exact stable atom/molecule/type maps, permanent bond lists and box bounds agree
between each E1 state and each corresponding accepted associating parent.
The protocol matrix agrees on functionality, arm length, 1,000 stars, polymer
density, total density .85, particle counts, T=1, dt=.01 and all output cadences.
The shared implementation retains GJF NVT at friction .5, WCA epsilon=sigma=1,
permanent FENE K=30/R0=1.5, unit masses and topology. Density rounding is shared
with the original geometry, not silently regenerated.

Reversible bonds and reaction kinetics are the only intended physical change.
The control begins at E1, whereas association has additional E2 preparation;
they share preparation families, not identical production-time conformations or
absolute preparation age. With direct `--input`, the production step clock starts
at zero; preserve E1's absolute preparation step separately. This is initialization,
not continuation. Fresh production streams must be distinct from all existing
requested, effective GJF and chemical streams and preserve family labels.

## Actual implementation audit

The local executable's inspected `--help` branch was executed (CPU return before
simulation setup). It advertises the documented `--input ... --arms ... --narm ...
--non-associating` route. The native binary is the existing authenticated
`kg_assoc_campaign_production`, SHA256
`5c396533482e08a48bd20fc27e6bb63bec790efecf843ae73cf01a52bf6265e5`.
No rebuild or GPU probe was performed.

| Requirement | Existing capability and limitation |
|---|---|
| Load E1 directly | Yes: input reads permanent LAMMPS data/velocities; no E2 sidecar needed. Scientific acceptance is an administrative prerequisite. |
| No reversible forces | Yes physically: partners initialize to -1, no bonds load, empty association kernel contributes zero. The interactor is still attached. |
| No stochastic reactions | Yes: front end sets nu0=0; chemistry-step condition is false, so candidate search and kinetics update are skipped. |
| Permanent dynamics | Same WCA, permanent FENE, GJF NVT, masses and loaded velocities. No integrator redesign. |
| Complete microscopic stress | Existing kinetic + WCA + permanent-FENE stress; empty temporary cache is zero. Same cache reduction and stable-ID handling. |
| Six-channel estimator | Same six shear/normal-difference channels, volume normalization and combined estimator. |
| Every-step sampling | Unconditional production loop sampling after forwardTime; no chemistry refresh needed. |
| Correlator | Existing Correlator6(40,16,2), exact contribution counts and actual lag grid. |
| Scientific outputs | Same thermo, COM, topology, bead coordinates, final configuration, empty association/events archives. Shape/transport readers reuse those outputs offline. |
| Completion and validation | Native atomic completion and `campaign.verify_run` support controls; exact immutable 24-history E1-aware authority/receipt path is not implemented or certified. |

Code inspected: `kg_assoc_campaign_production.cu`, `kg_assoc_production.cu`,
`kg_assoc_interactors.cuh`, `campaign/kg_assoc_campaign.py`, and the unchanged
production activation driver/adapter. The front end fixes **100,000,000 steps**
by default, T=1, dt=.01, Nevery=100, diagnostics=1000, COM/topology=10000,
beads=100000. Placeholder Ea=4/Ee=8 remain in metadata but have no physical
chemical effect at nu0=0 with no partners. There is no continuation/checkpoint
route. `--validate-initial-state` currently requires an associating E2 parent
and rejects direct E1: it is not an E1 CPU preflight. The existing CPU E1
snapshot checker is the appropriate reusable preflight.

Source-level claims follow the local LAMMPS reference branch
`feature/associating-stickers`, SHA `1c6faf70e94aef2389c208e8c80c60c084a96907`,
`src/ASSOCIATING/fix_associating_kinetics.*` and `pair_associating.*`: kinetic
attempts use the finite-step exponential, both transitions use the candidate
cutoff, temporary mechanics add shifted FENE without another WCA. No model or
kinetic implementation was changed. The local reference's unrelated benchmark
working files are dirty; no reference file was edited and no assertion about
remote branch freshness is made.

### Reuse versus adaptation

Reuse unchanged: optimized -O3 build recipe and preserved native binary/build
manifests; E1 resolver/check_snapshot; protocol/geometry matrix; six-channel
native correlator and existing reader; `verify_run` endpoint/output/event
reconstruction for control systems; generic output-path, history-digest and
journal-identity helpers; immutable file creation, source authentication,
workflow lock, fail-stop/no-resume policy and fresh-attempt preservation pattern.

The activated driver cannot be pointed at controls: it hard-binds 45 associating
approvals and an E2 registry. The adapter's `authenticate`, `chemistry_trace`
and numerical-validation dispatch assume `accepted_parent` is E2;
`e2.system_by_id` rejects controls. Its expected one-million chemistry sweeps
would be wrong for nu0=0. The old generic control launcher mutates run.json and
is not equivalent to the newer immutable execution-journal authority. Do not
bypass that difference by running it.

Small future adaptation: a separate control authority/adapter must bind exact
accepted E1 bytes and lineage instead of E2 sidecars, dispatch `verify_run` with
the existing control system object, and require zero chemistry sweeps, events,
temporary pairs, energy/virial, creations and breaks. Retain the existing strict
stress-grid/count/normalization checks. Bind all effective/requested fresh seeds,
commands, source/build/executable, acceptance qualifications, output paths and
receipt hashes. Test rejected E2 parents, stale/missing E1 acceptance, changed
inputs/seed/argv/output, nonzero chemistry, interruption, overwrite, duplicate
attempt and authenticated completed-skip behavior using CPU fixtures. Keep this
administration separate so historical associating source authorities and journals
remain byte-identical and still authenticate. No GPU stress code is needed.

## Production policy, performance and storage

Retain **24 × 100M uninterrupted steps = 2.4 billion steps**. The native loop's
step range supports this, and the matching associating executable has now run
100M per history. That is strong shared-path evidence, not a current 100M
non-associating completion. Do not shorten the campaign based on expected faster
relaxation. Any length change needs a separate scientific decision.

`VALIDATION.md` records a historical 100k C1 non-associating GPU smoke in
21.06 s versus a 35.19 s associating smoke: ratio .5985 (~1.67× throughput).
It records zero chemistry sweeps/events/bonds/temporary energy with the requested
outputs. Its full contemporaneous payload/build binding was not recovered in
the current production validation folder, which contains the fifteen associating
compatibility runs. Treat it as documented historical evidence, not reauthenticated
current-build performance or eight-geometry certification.

Actual current 100M associating times in
[../production_closure_20261119/production.csv](../production_closure_20261119/production.csv)
provide a better same-hardware reference than the old short extrapolation:

| Geometry | Three matching EE08/Ea4 histories, GPU-hours | Shared scientific output, GB |
|---|---:|---:|
| F03_N010_RP080 | 23.60 | 3.600 |
| F04_N010_RP020 | 71.18 | 8.754 |
| F04_N010_RP040 | 41.64 | 5.580 |
| F04_N010_RP060 | 33.77 | 4.521 |
| F04_N010_RP080 | 29.95 | 3.988 |
| F04_N020_RP080 | 42.15 | 5.544 |
| F04_N040_RP080 | 65.97 | 8.652 |
| F06_N010_RP080 | 43.18 | 4.766 |
| Total | **351.43** | **45.407** |

“Shared” subtracts events, topology and final-association files from those
actual outputs, retaining bead/COM/thermo/stress/final coordinates/completion.
Empty control topology/events still have headers/frame records, so this is a
reference, not a byte-exact prediction. Molecular COM motion and text widths can
change. Bead storage is fixed by atom/frame counts (12 bytes per atom per frame
plus schema/ID/bond headers). A **50–65 GB working estimate**, with **96 GiB
(103.1 GB) free space reserved** for new outputs and operational headroom, is a
reasonable provisional allocation; retain all associating/historical evidence.
Observed free space was about 692.8 GB, not a future launch guarantee. The old
384-GiB associating launch threshold is not a control storage measurement.

Candidate construction, CPU/GPU synchronization for reactions, kinetics sorting/
acceptance, event output and post-chemistry stress refresh disappear at nu0=0.
Active bond force arithmetic disappears, but empty-kernel launches/cache zeroing,
WCA neighbor lists, permanent forces, every-step microscopic stress reductions,
GPU-to-host buffers, CPU correlation and COM/bead I/O remain. No profile separates
these costs; the chemical share and whether shared stress dominates are **unknown**.
Removing reaction work makes a speedup plausible, not quantified. Retain this
implementation until measured; do not optimize away its empty interactor here.

Applying the historical ratio indiscriminately gives about **210 GPU-hours**;
using current matching associating time gives **351 GPU-hours**. These are planning
scenarios, not confidence bounds. Provision roughly **450 GPU-hours (~19 days)
including operational margin**, then replace the estimate with bounded measured
control timings. No speedup is promised and no GPU job ran in this review.

## Recommended next milestone and separate gates

1. **Already satisfied:** complete associating inventory/authentication as recorded
   in dossier A; 24 recovered numerically valid E1 snapshots; exact 45-to-24 family
   pairing; geometry/topology/parameter comparability; existing direct-input mode,
   full stress estimator/output readers and optimized build infrastructure.
2. **CPU-only work still needed:** review the original E1 qualifications explicitly
   for direct control starts. Resolve or explicitly decide how to carry the
   nonlinear timestep question and N40 uncertainty, without silently converting
   E2 suitability into direct-control acceptance. Publish new immutable qualified
   E1 acceptances with state/diagnostic/source lineage and historical provenance
   gaps. Implement/test the separate E1-aware control adapter and an immutable
   future seed-reservation/plan/approval design; do not reuse or alter the active
   associating registry. A future preparation milestone must allocate distinct
   control campaign/output identities, preserve partial attempts, allocate fresh
   attempts only under separate approval, skip only validated completions, and
   retain family pairing. No 24-history plan, seeds or approvals are created here.
3. **Bounded user-run GPU compatibility, separately authorized later:** propose
   the existing 100k smoke front end, same T/dt/thermostat/output/stress settings,
   one r001 per geometry plus registered RP060/r002 retry (nine tests). Each is
   one uninterrupted 100k job with timeout 600 s, unique output root and separately
   reserved seed. Apply independent control-zero-chemistry and complete output/
   stress validators. Add r002/r003 repetitions for RP080/N10, RP020/N10 and
   RP080/N40 to estimate timing dispersion (six further 100k tests; fifteen total,
   1.5M steps). Do not use validation outputs as production histories. Compare
   throughput and storage with the matching associating records; no isolated
   chemistry percentage can be inferred from total-time ratios alone.
4. **Later production activation and launch:** only after qualified E1 acceptance,
   CPU adapter tests, actual GPU compatibility receipts and resource review,
   prepare/approve exactly 24 distinct 100M histories in a separate campaign.
   Activation and user-run launch require separate authorization. No approval in
   the completed 45-history campaign covers any control or benchmark.

The proposed compatibility argv shape, **not an executable authorization**, is:

```text
<authenticated-existing-100k-smoke-binary>
  --input <exact-resolved-E1-path-from-e1.csv> --arms <f> --narm <N>
  --seed <separately-reserved-validation-seed> --non-associating
  --output <new-independent-validation-directory>/run
```

The binary must be the preserved smoke build with
`KG_ASSOC_CAMPAIGN_STEPS="100000"`, not the default 100M executable. E1 acceptance,
source/build binding and output nonexistence must be checked before any later
execution. Proposed tests have not been prepared and no validation or production
seed is allocated. Do not issue GPU authorizations during this review.

The original E1 audit separately proposes an equal-physical-window dt=.01 versus
.005 KG comparison for RP020 and RP080 N10, inspecting on-site/half-step kinetic,
configurational and energy/pressure diagnostics. That scientific accuracy question
is not answered by a 100k compatibility smoke. A later milestone must specify
sampling/uncertainty and inspect results, or make an explicit qualified acceptance
decision, before unconditional direct-control readiness. No new E1/E2 equilibration
or physics/timestep change is proposed as an automatic remedy here.

## Validation and preservation

See dossier A's CPU test and inventory logs: eight campaign plus eight E1 tests
pass, and actual 24-state geometry/velocity/bond checks, hash comparisons, seed
independence and all 45 ancestry/topology comparisons pass. These are deterministic
checks, not new stochastic convergence evidence. Reproduce with dossier A's
read-only inventory script and full authority audit; e1.csv is its unchanged
24-state output. Full rheology/structure analysis and host-wide process surveying
were not performed. No scientific discrepancy was repaired or reinterpreted.

Tracked additions are confined to the two new review directories. An isolated
ignored review workspace preserves CPU audit drafts/checkpoints/logs; no existing
dataset artifact was modified. No protected `examples/KG/` or
`src/` file, native source/header/binary, existing review, dataset output, E1/E2
record, acceptance, registry, approval, reservation or immutable journal changed.
No GPU/MD, preparation, execution approval or production activation occurred.
