# Stage 4A.3b — GPU virial and streaming implementation

17 October 2026. Starting local and fetched `origin/slip-springs` SHA:
`d48bb6956e0cc42e70b7b4090bb1ee536600f5c9`; initially clean worktree.
**Implementation and bounded verification complete; independent review pending.**
This is not scientific acceptance of stress relaxation. No Stage 4A.3c campaign,
slip-springs, new interactions or production experiments were executed.

## Scientific convention and GPU architecture

The authoritative references remain `semiflexible_stress_reference.py` and
`STAGE4A3A_REPORT.md`, unchanged. Return unnormalized per-chain
W=V*sigma=+sum(g outer q), the positive affine-energy derivative. Stretching is
sum kb*(|q|-b0)*(q outer q)/|q|. Each active angle contributes

    W_b = kappa*[c*(u outer u + v outer v) - u outer v - v outer u].

The latter is the independently derived metric expression from Stage 4A.3a,
not UAMMD's stock angular virial. It is symmetric and traceless without repair.
The smooth b0=0,|q|=0 stretching contribution is zero; undefined active angular
geometry, nonfinite results and undefined stretching gradients fail explicitly.
No clamps, force cutoffs, trace subtraction or symmetrization are introduced.

`semiflexible_stress.cuh` uses one CUDA thread per chain, traversing bonds and
active angles in ascending order. Each chain has one writer. A stretching kernel
overwrites its tensor; a separate angular kernel adds on the same stream; a
final kernel packs channels. AtomicMin is used only for the deterministic
first-error key, not tensor accumulation. Serial per-chain reduction is the
small initial implementation; long-chain efficiency has not been benchmarked.
Stress arithmetic and sums are double in BOTH builds, using the stored real
coordinates and precision-rounded heterogeneous parameter arrays. This does
not change the precision of dynamics, forces or noise.

Internal tensors retain all nine entries and a cancellation-aware scale bound.
Each active angle is checked for symmetry/trace before accumulation; total
symmetry/finiteness is checked before extracting six entries. Diagnostic CSV
retains independent stretch,bend,total raw tensors. Prescribed-configuration
probes also compare positions and forces byte-for-byte after stress evaluation.
Stress kernels have no RNG or force-buffer interface. Failed stress evaluation
records step, seed, flat bead/reason and the complete failed coordinate snapshot.
Input/force failures retain the accepted driver's diagnostics. Error codes in
the stress record are 1 undefined stretch geometry, 2 nonfinite stretch,
3 collapsed/nonfinite active angle, 4 nonfinite tensor/channel, 5 asymmetry,
6 nonzero bending trace.

Stress is opt-in (`--stress-mode off|diagnostic|stream`, default off).
`--stress-input FILE` uses prescribed coordinates without integration. When off,
no stress observer, tensor, channel, CPU bank or pinned buffer is constructed.
When all kappa are zero, there is no angular stress allocation, kernel or
normalization. Mixed inactive angles are skipped before geometry. Active
streaming adds bending directly to total without a separate angular buffer;
only active diagnostic mode allocates a separate bending tensor. Metadata
distinguishes capacity, active bending and launch counts. The accepted force
fast path is untouched. Conformational tangent observations remain available
even in flexible chains, as before.

## Reuse, estimator and normalization

`semiflexible_stress_stream.h` adapts the existing `streaming::Bank` and
`streaming::CpuWorkers`, linking the unchanged KG `correlator.cpp`. Rouse,
its streaming implementation and all their scientific definitions are unchanged.
The existing asynchronous GPU pipeline is coupled to the Rouse sampler;
this adapter uses synchronous D2H and persistent workers to avoid modifying
that accepted path. This is a deliberate initial limitation, not a throughput
claim or evidence of superiority over UAMMD. No correlator implementation is
copied. UAMMD remains the existing read-only CUDA/runtime/type dependency;
the local exact stress law follows the accepted potential/convention assessment.
Reuse-first comparisons in ROADMAP.md remain future work.

Raw channels are xy,xz,yz,xx-yy,xx-zz,yy-zz. No factors 1/2 or 1/4 enter normal
differences. Total stretch+bend is assembled BEFORE entering the bank, so all
stretch/bend cross-correlations are retained automatically. The estimator is
the raw mean of per-chain products of complete nonoverlapping block means,
not a finite-trajectory mean-subtracted connected estimator. Isotropic ensemble
deviatoric means vanish; finite-trajectory means are not silently removed.

Sampling occurs at step0 and exact stride multiples. An unsampled final MD
interval is integrated without inventing an observation. All measured frames
are consumed; incomplete final batches are drained. Incomplete coarse blocks
are truncated, never padded. With coarsening m, level l uses width m^l frames;
level0 exports j=0..p-1 and higher exported levels j=p/m..p-1, subject to
available pairs. Preserve the legacy omission of the deepest populated level.
Counts distinguish frames, complete blocks, origins per chain and total pairs.
The inherited KG sentinel boundary (xy must exceed -1e10) remains an explicit
admission error, not a silently lost frame or regularization.

Within EACH chain combine H=sum(C_shear)/5+sum(C_normal_difference)/30, then
estimate mean/SE across independent chains. Channels and overlapping origins
are not independent samples. A single chain has undefined SE (NaN), explicitly
tested. `stress_correlations_raw.csv` preserves exact Bank output; its legacy
g/g_se names mean raw H/H_se here. `stress_correlations.csv` labels H explicitly,
adds g=H/(kBT)^2, and adds G=n_chain*H/kBT ONLY with positive explicit
`--chain-density`. Otherwise G is absent and metadata density is null. The
simulator assigns no melt volume or physical density. Normalization overflow
is rejected.

Per-chain final-half means and all 36 raw equal-time products are retained in
`stress_moments.csv`, with explicit selected-frame counts. They are diagnostic
moments, not a subtraction applied to the all-frame correlation estimator.
Optional `--stress-dump 1` enables bounded direct-reference sample storage;
ordinary streaming does not retain full stress or coordinate trajectories.

## Bounded verification and tolerances

Executed on NVIDIA GeForce RTX 3060 Ti, driver580.178.04, CUDA13.0.88 nvcc,
g++11.4, Python3.10, NumPy2.2.4. Both sm_86 builds succeeded. Existing warnings
in read-only KG input routines remain. Every test command was bounded below
ten minutes; no long campaign was run. Detailed development logs are ignored
under `build/stage4a3b-*.log`, not acceptance archives.

| Check actually run | Outcome |
| --- | --- |
| New stress suite, single and double (including cross-precision binary) | 7 groups each, PASS; final runs 5.064s / 5.136s |
| Existing `make check`, both precisions | PASS, including force/RNG, pipeline, CLI, theory and worker sanitizer regressions |
| Existing `make check-semiflexible`, both precisions | PASS: 7 GPU, 2 host-analysis and 12 CPU-reference tests per build |
| Existing CPU stress reference suite | 11 tests PASS |
| Existing lifetime ASan/UBSan/LSan | PASS, 200 ownership cycles |
| New CPU streaming fixture ASan/UBSan/LSan | PASS, 3 chains/35 frames, 3 workers, batch7 |
| CUDA memcheck, double active + single zero bending | 0 errors, 9 steps/3 chains each |
| CUDA racecheck, double active bending | 0 hazards/errors/warnings, 9 steps/3 chains |
| Exact README short examples | Both passed, 20 steps/64 chains, 5 frames, partial batch7 |
| Python syntax, whitespace and repository/evidence isolation | PASS |

New deterministic tensor tests include N1/N2, heterogeneous arrays, straight,
bent, nearly parallel/antiparallel bonds, rotations/translations, kappa1000,
nonunit kBT1.7, zero-rest-length Gaussian bonds, inactive collapsed bonds and
invalid/nonfinite/active singular cases. Stretch and bend must EACH agree with
the independent CPU reference; cancellation in total cannot pass. For
S=max(1,max kb,max kappa), absolute/relative bounds are:

* Single: 2e-7*S +3e-6*abs(reference).
* Double: 5e-13*S +3e-12*abs(reference).
* Raw symmetry: 1e-11*S; bending trace: 3e-11*S.
* Cross-precision geometry comparisons: 1e-5*S +3e-5*abs(reference).

The looser single bounds accommodate stored coordinate/parameter rounding
and covariance under rounded rotations. Stress sums themselves are double.
Scale-aware absolute terms cover cancellation near stationary/collinear cases.
Existing force thresholds are unchanged, not replaced by these stress bounds.

The independent direct oracle forms block means/products from explicitly stored
short sequences, rather than calling KG. It checks all six channels and SE,
paired H/SE, exact lag grid and counts. Coverage includes constant, zero-mean,
nonzero-mean, known-lag, identical/independent-chain sequences and nonzero
stretch/bend cross terms; short runs, incomplete blocks, m2/m3, workers1/all/auto
and batches1/7/32 are exercised. Product/SE tolerances are absolute3e-11 plus
relative3e-11 (different reduction order); thermal/density factors use relative
2e-14. Per-run worker/batch replay outputs are byte-identical.

A bounded Gaussian N2,b0=0,kb3 control (2048 independent chains,40 steps,
dt0.02,stride2,kBT1.7) reuses the unchanged exact finite-step Rouse analysis,
including effective drift/noise and origin-wise covariance before squaring and
block averaging. Raw channels and normalized g pass six-chain-SE +1e-5 gates.
This reference is used ONLY in the Gaussian limit.

Stress off/on replay yields byte-identical initial/final coordinates, scalar
observations and bond statistics in each precision with identical seed. The
new kernels do not change forces or RNG counters; appended chains preserve
existing-chain outputs. Frame accounting, final-half moments, no angular
capacity/launches at zero kappa, active launches and worker exception cleanup
are verified. Tests do not assert cross-precision trajectory identity.

## Timing and bounded storage observations

The two README 20-step runs (N8,C64,dt0.0001,stride5,kBT1.7,seed433101) measured:

| Measurement | Single | Double |
| --- | ---: | ---: |
| Initialization, seconds | 0.221109 | 0.129360 |
| GPU integration, ns/bead/step | 53.664 | 140.594 |
| Overall production, ns/bead/step | 205.957 | 282.750 |
| Stress GPU, seconds | 0.000347904 | 0.000314848 |
| Stress D2H, seconds | 0.000019555 | 0.000019526 |
| Stress synchronization/diagnostic wait, seconds | 0.000319998 | 0.000289263 |
| CPU correlation pool wall, seconds | 0.000063692 | 0.000061926 |
| Stress finalization/output, seconds | 0.000883335 | 0.000865954 |

These tiny, unrepeated runs are functional timer observations, NOT benchmarks
or precision comparisons. Existing integration events exclude observations;
overall production includes stress, CPU observations, output and final batch
consumption. Finalization/export is separately timed. Stress-on timer_version2
includes stress exports/metadata in final output; off retains version1. CPU
barrier time is a subset of pool wall time; worker-time sum is not wall time.
GPU event time overlaps host synchronization wait. Do not add these timers.
Synchronous buffer-queue wait is zero because no asynchronous queue exists.

Both examples report 8200 extra stress GPU bytes, 21504 pinned batch bytes,
zero separate angular diagnostic bytes and five active angular stress launches.
The stress allocation estimate including CPU bank/moments is 592904 bytes.
These are capacities/estimates, not process RSS or whole-device consumption.
Storage scales O(chains) on GPU and O(chains*levels*slots + chains*batch) on CPU,
independently of total steps, excluding allocator/context/thread-stack costs.
The 2GiB workspace estimate, bank and batch budgets remain checked. Existing
scalar observations and optional stress dumps grow on disk, not in memory.
No long-duration memory plateau or production-server performance claim is made.

## Frozen host plan and review boundary

`STAGE4A3C_VALIDATION_PLAN.md` is frozen before long experiments. SHA-256:
`efd040ceba8cd903dee7a145296dce08435e3df3efa940c65170f4bcf98acb36`.
The dry generator writes 282 commands: 162 main streams,54 zero-step diagnostics,
54 direct-reference runs and12 repeated memory runs, with fixed three seeds,
both precisions, dt/stride choices and copied plan/hash. It has NO --run option.
Tests verify generation and shell syntax without executing these commands.
Some proposed runs have 160 million integration steps and can take hours.

The plan specifies independent-chain uncertainties, exact Gaussian finite-step
controls, independent equilibrium stress moments/covariances, separate tensor
comparisons, direct multi-tau gates, timestep comparisons, terminal coverage,
singular-bond failures and memory/performance provenance. Nonlinear durations
are coverage proposals with measured terminal-support gates, not an assigned
Rouse spectrum. Unresolved timestep bias must stay unresolved; no convergence
order is claimed. Missing terminal support requires a reviewed extension.
The provided diagnostic/direct checkers are not a complete scientific acceptance
analyzer: an independently reviewed host analysis/report remains required.

All modified/new paths are confined to this directory. The accepted force
header, initializer and integration loop, original tests/CPU references,
Rouse/shared correlator sources, previous frozen plans and evidence are
byte-identical. Both existing evidence archives were verified: 233 Stage4A.2
and5 Stage2B-N100 checksum payloads passed. No archive or checksum was edited.

Changed files: `semiflexible.cu`, `semiflexible_stress.cuh`,
`semiflexible_stress_stream.h`, `Makefile`,
`tests/semiflexible_stress_correlator.cpp`,
`tests/test_semiflexible_stress_gpu.py`, `tests/semiflexible_stress_host.py`,
`STAGE4A3B_REPORT.md`, `STAGE4A3C_VALIDATION_PLAN.md`, `README.md`, `ROADMAP.md`,
`AGENTS.md`. No unresolved bounded-test failures. Remaining limits are the
synchronous adapter, unchanged KG sentinel/export conventions, inverse-length
force singularities and absent scientific host acceptance. Stage4A.3b requires
independent review BEFORE host execution; Stage4A.3c/Stage4B remain unexecuted.

Build/check commands (sequential; adjust CUDA paths/architecture for the host):

```sh
make -C examples/slip-springs check-semiflexible-stress CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check-semiflexible-stress CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
```

Generate the frozen host campaign WITHOUT executing it:

```sh
STRESS_HOST=$(mktemp -d /tmp/semiflexible-stress-host.XXXXXX)
python3 examples/slip-springs/tests/semiflexible_stress_host.py --output "$STRESS_HOST/campaign"
(cd "$STRESS_HOST/campaign" && sha256sum -c PLAN_SHA256)
```
