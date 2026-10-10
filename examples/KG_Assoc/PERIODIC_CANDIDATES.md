# Periodic reaction-candidate correction and recovery gate

Recovery launcher, seeded segment validation, fresh-MD policy and four-window
analysis are now prepared in [C1_E2_RECOVERY.md](C1_E2_RECOVERY.md). The old plan
below is retained as the correction-stage record; its missing-runner/MD-reseed
gates are superseded by the new workflow, not by execution authorization.

Starting HEAD: `c4d310f6b33c601de881a6086bcc2e375600d3b3`, branch `KremerGrest`.
This correction does not authorize recovery equilibration or production.

## Root cause and correction

`kg_assoc_star_runtime.cuh::cellIndex()` clamped unwrapped MD coordinates to
boundary cells. Periodic neighboring-cell lookup was already present, but cannot
repair incorrect cell membership. Consequently valid minimum-image pairs never
reached chemical consideration. Both creations and ruptures were omitted,
including ruptures of mechanically active bonds. This explains an artificial
time-dependent suppression of activity; it does not establish the size or sign
of every resulting equilibrium bias.

The only ordinary-runtime change is periodic reduction of the coordinate used
for cell assignment. ParticleData positions remain unwrapped. Existing periodic
neighbor indexing, minimum-image distance checks, strict `r < 1.25`, pair
deduplication, force field, integrator, seeds, RNG algorithms, cadence and
acceptance rules are unchanged. With cell widths at least the cutoff (or a
single cell on a short dimension), the existing 27 offsets cover the search.
The existing ID-pair set removes repeats when offsets alias on one/two-cell axes.

Traversal order can change as cells change. This is not the reaction ordering:
`Kinetics::update()` sorts by stateless `(seed, absolute step, ordered pair)`
hash, with ID tie-breaks. Neither order nor acceptance draws consume a mutable
stream based on candidate enumeration. An independent reversed enumeration
produces identical ordered events and partners in the regression. Newly restored
pairs intentionally change defective trajectories; bitwise agreement with those
trajectories is neither expected nor scientifically desirable.

The local LAMMPS reference on `feature/associating-stickers` was inspected:
`fix_associating_kinetics.cpp` uses periodic minimum-image strict-cutoff edges.
No chemical acceptance semantics were replaced with generic assumptions.

## Saved C1 endpoint checks

The actual corrected C++ helper and an independent all-pairs minimum-image
oracle agree on every pair, not only counts. All eligible active bonds are found.

| Replica | Defective candidates | Correct candidates | Correct eligible active / total |
|---|---:|---:|---:|
| r001 | 1623 | 2484 | 1775 / 1775 |
| r002 | 1690 | 2538 | 1770 / 1770 |
| r003 | 1598 | 2438 | 1767 / 1767 |

Defective counts are retained audit evidence, not new corrected simulations.
The previous search missed 583, 546 and 599 active endpoint bonds, respectively.

## Impact inventory and scientific qualification

Affected executables using this shared implementation:

- `kg_assoc_stars`: S1/E2, historical P3.1/P3.3 C1 preparation and restart-bank
  workflows, fresh C1 pilot and campaign E2.
- `kg_assoc_production`: historical P4 validation, profiling/rheology pilots,
  five retained 32M C1 trajectories, and any Ee-staircase runs using that binary.
- `kg_assoc_campaign_production` and its 100k smoke build: include the same
  production implementation. Rebuild before any future use; no new 100M runs
  were launched by this correction.
- The new test binaries also intentionally exercise the shared helper.

Affected launchers include `run_p33_c1_restart_bank.sh`,
`scripts/prepare_p42_c1_replicas.sh`, `benchmark_p41_short.sh`,
`run_p41_validation.sh`, `profile_p42_short.sh`, `run_p42_rheology_pilot.sh`,
the P4.8b staircase workflow, and the campaign E2/production launchers.
Earlier C1 E2 endpoints inspected by the activity audit exhibit missing periodic
pairs too. Original uninterrupted historical E2 raw records are not all retained;
do not invent a quantitative correction for inaccessible trajectories.

All source-dependent association populations, loops/connectivity/percolation,
lifetimes/rebinding/exchange, walking/hopping, stress relaxation/viscosity and
transport/network relationships require qualification and corrected-dynamics
revalidation. Offline analyzers can accurately describe a defective trajectory
without making it a sample of the intended chemistry. Previously plausible
static populations do not repair the kinetic defect. The three fresh 6M E2
banks are **not accepted equilibrium starts for production**.

Not affected by this helper: chemistry-disabled E1 and non-associating dynamics;
dimer kinetics (explicit pair); K1 (separate modulo-indexed search); force/stress
definitions and correlator algorithms. Their analytic/unit evidence remains
valid. Old primary-cell smoke tests checked examples, not arbitrary-image
completeness, and were insufficient to certify this helper. Existing numerical
health, event conservation and provenance checks remain valid but cannot certify
candidate completeness. Historical files and completion records are preserved,
not silently relabeled, deleted or regenerated.

## Executed validation

CUDA 12.8 / GCC 11.2 rebuilt all six affected build targets (ordinary E2,
ordinary production, 100M production, 100k production smoke, candidate CPU test,
capped E2 candidate smoke). Candidate CPU tests do not initialize a GPU.

- Five anisotropic/degenerate boxes, 30 independent random integer translations
  per box (each sticker independently, up to +/-16 box lengths), reversed input
  ordering, faces/edges/corners, positive/negative multiple images, ordered
  unique pairs and strict-cutoff tests passed. Dyadic synthetic coordinates avoid
  mistaking float representation loss for a search error. Arbitrarily huge
  translations cannot retain geometric accuracy once input precision is lost.
- Existing primary-cell indices agree with the prior indexing; 200 actual
  host-chemistry sweeps, including an active periodic bond, agree with reversed
  brute-force enumeration in event order and partner state.
- Three actual C1 snapshot pair-set checks passed with the counts above.
- Campaign/E1/C1 pilot/seeded-segment fixture suite: 24 tests passed. Seeded replay
  tests cover inherited bonds/counters, reciprocal valence, neighbor loss/gain,
  invalid initial state, and missing oracle sweep rejection.
- Stars/production, dimer, K1, E1, E2 stationarity, P4.5 topology, P4.6 bond
  dynamics, restart reader, Correlator6 counts and correlator checkpoint tests
  passed. Serialization remains unused by dedicated production.

GPU trajectory validation is **pending**: the NVIDIA driver is inaccessible.
No MD trajectory, E2 recovery or production was executed here. Existing Python
restart-parser ResourceWarnings are nonfatal and unrelated; no parser semantics
were changed solely to silence them.
The additional rheology/walking-hopping/percolation analyzer self-tests passed.
COM MSD and Fs analyzer self-tests could not import the external `correlator`
Python extension in this environment; these unrelated optional checks remain
pending, not reported as successes. The C++ correlator checks passed.
All 24 E1 final-state hashes and 93 recorded E2/historical input/output hashes
were independently checked unchanged against the retained audits.

## Dedicated-host short GPU validation

From repository root, use a NEW versioned output directory. First review the dry
run. The `--execute` command below authorizes only the short validation requested
for this correction; it cannot launch a 2M recovery segment.

```bash
make -C examples/KG_Assoc -j2 kg_assoc_stars kg_assoc_production \
  kg_assoc_campaign_production kg_assoc_campaign_production_smoke \
  kg_assoc_candidates_test kg_assoc_stars_candidate_smoke
export DATASET_ROOT="$(pwd)/examples/KG_Assoc/kg_assoc_100m"
export SMOKE_OUTPUT="$DATASET_ROOT/aggregate/e2/C1_periodic_smoke_HOST_VERSION"
python3 examples/KG_Assoc/campaign/validate_periodic_e2_smoke.py \
  --dataset-root "$DATASET_ROOT" --output "$SMOKE_OUTPUT"
python3 examples/KG_Assoc/campaign/validate_periodic_e2_smoke.py \
  --dataset-root "$DATASET_ROOT" --output "$SMOKE_OUTPUT" --execute
python3 examples/KG_Assoc/campaign/validate_periodic_e2_smoke.py \
  --dataset-root "$DATASET_ROOT" --output "$SMOKE_OUTPUT" --verify
```

Each replica runs 10,000 standard KG steps from its preserved chemical endpoint.
The special executable hard-refuses larger runs and checks every candidate pair
against the oracle at all 100 chemistry sweeps. All-pairs work is compile-guarded
test instrumentation, absent from ordinary production. No per-MD-step permanent
bond scan was added. Existing geometry checks remain hard failures.

The runner refuses existing output directories, creates exclusive logs, stops on
first failure, records incomplete status, hashes parents/executable/outputs and
records current SHA and MD-reseed policy. Its validator checks inherited event
counters/partners, absolute cadence/times, all diagnostic samples, full network
reconstruction, final geometry/mirrors, loaded/final kinetic temperatures and
effective NVT parameters. A successful smoke does not establish stationarity or
measure ordinary-runtime performance (its oracle is intentionally expensive).

## Proposed recovery test — separate execution approval required

The preserved 6M molecular/velocity states and reciprocal temporary partners are
numerically and chemically loadable, though not equilibrium samples of corrected
chemistry. They can start **re-equilibration**, with three independent histories
retained, not three new histories invented from snapshots. Keep the original
bank, its completed records and the activity audit unchanged.

Before launch, require successful host GPU smoke review and a scientific decision
on stochastic restart semantics. The current reader restores velocities, partners,
cumulative counters, parameters and absolute chemistry step, but **does not**
restore the GJF MD RNG/internal timestep. System is reseeded with the original
seed, so MD reuses the original noise prefix; chemistry hashes the new absolute
steps. This is a documented state restart, not uninterrupted stochastic
continuation. Approve that policy explicitly, or separately authorize a fresh
MD-stream mechanism. Do not edit restart seeds or claim exact RNG continuation.

Use a new, exclusively created directory:
`DATASET_ROOT/banks/e2_extensions/C1_periodic_recovery_APPROVED_VERSION/r001..r003`.
Lock the attempt, retain running/incomplete/completed provenance, exclusively
create logs, validate all parents before/after and stop at the first failure.
Never use `--force`, reuse an attempt directory or replace original banks.
Retain old/new git and executable hashes, build/GPU identity, full commands,
original E1/E2 parents, chemical seed, MD-reseed policy, inherited counters,
start/end steps, output hashes and scientific acceptance=`review_required`.

For each `r=001,002,003`, the **command specification, not run authorization**, is:

```text
examples/KG_Assoc/kg_assoc_stars
  --restart-prefix DATASET_ROOT/banks/e2/F04_N010_RP080_EE08/rXXX/state
  --steps 2000000 --diagnostic-every 1000 --seed 2200X --r-assoc 1.25
  --output DATASET_ROOT/banks/e2_extensions/C1_periodic_recovery_APPROVED_VERSION/rXXX/state
```

The reader freezes dt=.01, T=1, Ea=4, Ee=8, nu0=20, Nevery=100, damping=2,
K=30, R0=1.5. These are additional steps: absolute 6M to 8M, 20,000 chemistry
sweeps and 2,001 diagnostic rows including the inherited boundary. Events must
satisfy `6M < step <= 8M`, cadence 100; absolute time is step*.01. Final counters
must equal inherited counters plus new events, and replayed partners must match
both endpoint mirrors. Do not count the inherited row twice in window estimators.

The seeded replay utility now supports this continuity. The capped smoke runner
does NOT launch or validate 2M segments: an extension-specific completeness and
provenance validator/runner must be prepared and tested before any recovery launch.
This is an explicit remaining execution gate, not silent permission to use the
fresh-pilot validator (which assumes step zero/unassociated starts).

Review corrected `(6,7M]` and `(7,8M]` windows, 250k/500k blocks and trends;
compare all three histories using autocorrelation-aware block uncertainty.
Track bound/free populations, intra/inter bonds, accepted creation/break and
population-normalized activity, neighbor gain/loss/turnover, largest component,
distinct degree, L1/L2, temporary geometry, temperature and permanent bonds.
Use corrected candidate/eligible-opportunity diagnostics if separately approved
for ordinary recovery; current outputs alone cannot separate attempted/rejected
events from unavailable candidates. Compare against old windows only as
defect-labeled context, not equilibrium targets. Do not stitch lifetime or
rheological estimators across the algorithm/RNG boundary; retain censoring.
Two million steps are diagnostic, not guaranteed sufficient. Further recovery
and final equilibrium acceptance require another scientific review.
