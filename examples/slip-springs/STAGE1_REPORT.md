# Stage 1: independent GPU Rouse dynamics

15 October 2026 (Europe/Madrid). Stage 1 is implemented and its predeclared
scientific gates passed. Stages 2–4 remain unauthorized and unimplemented.

## Provenance and repository boundaries

Fetched `origin/slip-springs` and verified its remote HEAD before implementation:
**d899817cdc459c8bbe11cd2bfa02e6b580b60a90**. Work continues from that commit
on `slip-springs` in `/tmp/UAMMD_KG-slip-springs`. The original checkout stays
on KremerGrest with its pre-existing KG Makefile change and Stars_TEST directory
preserved. No upstream source or existing example was changed or rebuilt.
Stage 0's source SHA and historical findings remain in STAGE0_REPORT.md.

Modified: `.gitignore`, `AGENTS.md`, `Makefile`, `README.md`.
Added: `rouse.cuh`, `rouse.cu`, `validate.py`, `STAGE1_REPORT.md`,
`tests/rouse_tests.cu`, `tests/test_theory.py`, `tests/test_cli.py`,
`tests/VALIDATION_PLAN.md`. Every path is under `examples/slip-springs/`.
Build products stay under its ignored build/; run data, extra logs and sanitizer
artifacts are outside the repository under /tmp. The final commit SHA and normal
push outcome are in the handoff; no PR or merge is requested.

## Implementation and RNG source inspection

`rouse.cuh::force/update` applies adjacent-bead Gaussian forces with free ends,
reads only the old buffer and writes only the other buffer. All chains share a
single UAMMD ParticleData ensemble plus one scratch buffer; host pointer swaps
alternate them. The current pointer is authoritative (ParticleData's backing
buffer alone is not necessarily the latest odd-step configuration). Positions
and immutable logical RNG IDs are held for the run; no sorting, velocities,
Box, minimum image, neighbor list or interactor machinery is involved.

Every force is exactly the gradient of U=(3/2)sum q^2; endpoint beads have only
one neighbor. The kernel has one logical thread/update per bead and no chain
closure or interchain edge. Initialization accumulates independent component
Gaussians of variance 1/3, with independent Gaussian xyz translations of variance 1
per component for each chain. Translations affect no force or internal statistic.

Read-only RNG investigation included `src/third_party/saruprng.cuh` (gf and gd
both use float ingredients) and the installed CUDA 13 headers:

- `curand_philox4x32_x.h`: Philox4x32-10 round function and counter arithmetic.
- `curand_kernel.h`: curand_init(seed,subsequence,offset), skipahead and
  skipahead_sequence. Subsequences are spaced 2^66 32-bit outputs apart.
- `curand_normal.h`: float normal4 and double normal2 implementations and
  their Box–Muller transforms. Double construction combines 32-bit words into
  53-bit uniforms and uses double log/sqrt/sincospi, not float Gaussian casts.

The chosen RNG is CUDA cuRAND **Philox4x32-10**. The full user unsigned 64-bit
seed is the key. Subsequence is `logical_id | (domain << 62)`; domains0/1/2
separate dynamics, initial bonds and initial chain translations. Total beads
are restricted by ParticleData's int indexing, well below 2^62, so domains
cannot alias IDs. The fixed layout maps IDs to chain-contiguous slots; RNG
itself is independent of storage index, tested by permutation. Reordering
physical storage would also need topology remapping and is unsupported here.

Offset is `8*absolute_step`. Float uses curand_normal4 (four 32-bit draws),
double uses two public curand_normal2_double calls (eight draws); the fourth
Gaussian is discarded. Both reserve the same eight-word span. Each update
constructs a local state from its counter, so no persistent RNG arrays exist.
Equilibration and production share a continuous unsigned 64-bit counter. Runs
with total steps >floor(UINT64_MAX/8) are rejected before allocation, rather
than wrapping or reseeding. IDs/chains cannot share a subsequence within a run.
Same seed/configuration reproduces samples on the same build/device. Separate
runs with the same seed intentionally replay; there is no checkpoint/resume.

Both Gaussian implementations have finite discrete inputs/tails and math
roundoff. Double is genuinely double-based Gaussian arithmetic, not unlimited
precision. No fast-math flag is used. Toolkit/device changes can alter final
bits, and float/double outputs need not be pathwise identical. Moment/covariance
checks are evidence for the tested streams, not an exhaustive RNG certification.

## Analytical references and statistical method

Let M=N+1, theta_p=p*pi/(2M), lambda_p=12 sin^2(theta_p). Orthonormal bead modes
are phi_p(j)=sqrt(2/M)cos(p*pi*(j+1/2)/M), p=1,...,N. For the endpoint difference,

    d_p^2 = 8/M cos^2(theta_p) for odd p, and 0 for even p.
    Cee_cont(t) = [3/N] sum_p [d_p^2/lambda_p] exp(-lambda_p*t).
    tau1_cont = 1/lambda_1; D_CM = 1/M.

These are exact finite-N amplitudes, not a longest-exponential approximation.
The independent CPU tests diagonalize the free-end spring stiffness matrix,
check all eigenvalues, propagate its full covariance directly and compare to
the scalar mode formulas. Continuous dimensions are q^2=1, Ree^2=N,
Rg^2=N(N+2)/(6(N+1)).

For dt=h, a_p=1-lambda_p*h, initialized at continuous equilibrium:

    v_p(0) = 1/lambda_p                 (per Cartesian mode component)
    v_p(*) = 1/[lambda_p*(1-lambda_p*h/2)]
    v_p(n) = v_p(*) + [v_p(0)-v_p(*)]*a_p^(2n).
    <q^2> = (1/N)sum lambda_p*v_p(n)
    <Ree^2> = 3 sum d_p^2*v_p(n)
    <Rg^2> = (3/M)sum v_p(n).

The simulator rejects h*lambda_max>=2. Validated timesteps also have positive
a_p. Exact EM lag covariance is a_p^lag*v_p(origin), averaged over the actual
origins. The end-to-end denominator uses the same origins, essential when the
EM covariance is not stationary. Optional equilibration is included in origin
step counts. The slowest-mode estimator is -lag_time/log(C1), compared against
-dt/log(1-lambda1*dt). Very large stable timesteps can cause alternating modes;
the positive-correlation relaxation-time estimator is not intended for them.

Direct-lag MSD and vector dot products use multiple overlapping origins.
Origins are averaged **within each chain**; 512 independent chains, not the
number of pairs, determine the standard error. Ratio uncertainties use the
chain-cluster delta method; the nonlinear tau uncertainty uses its derivative.
Conformation averages first average observations within chains and then use
across-chain SE. Tables report mean +/- **one SE**; approximate 95% intervals
are mean +/-1.96 SE and are also written in analysis.json.

`tests/VALIDATION_PLAN.md` fixed seeds and thresholds before stochastic tests.
The family gate is |residual|<=5 SE, not an assertion that every individual 95%
interval contains theory. There are 225 dimension/dynamics/precision checks;
the nominal Gaussian union bound is <0.0002 even for 300 checks. CLT/delta-method
intervals are approximate. RNG gates separately use six analytic SE for mean,
second/fourth moments and component/adjacent-ID/consecutive-step products.
No threshold was loosened after seeing the data.

## Scientific results

The final suite used both precisions, N=8,32,100, dt=0.01,0.005,0.0025,
seed=710000+100*N+dt_index+10000*precision_index. Each dynamic case has 512
chains and 41 observations. Sampling stride=ceil(tau1/(32*dt)); total steps
are 40*stride, ensuring duration >=1.25 tau1. No equilibration is discarded:
initial state is already exact continuous equilibrium and transient EM bias is
included explicitly. Initialization-only runs use 8192 chains and seed 20261015+N.

Initialization (continuous references: q²=1, Ree²=N; Rg²=1.48148148, 5.49494949, 16.83168317 for N=8,32,100):

| bits | N | q² +/- SE | Ree² +/- SE | Rg² +/- SE |
|---|---|---|---|---|
| 32 | 8 | 1.000951 +/- 0.003164 | 8.108145 +/- 0.074072 | 1.490525 +/- 0.008891 |
| 32 | 32 | 0.998188 +/- 0.001592 | 31.832251 +/- 0.289058 | 5.439762 +/- 0.031359 |
| 32 | 100 | 0.999745 +/- 0.000909 | 100.125289 +/- 0.902515 | 16.909355 +/- 0.095564 |
| 64 | 8 | 0.996003 +/- 0.003171 | 7.932559 +/- 0.071802 | 1.469284 +/- 0.008689 |
| 64 | 32 | 1.004721 +/- 0.001594 | 32.245023 +/- 0.293015 | 5.514596 +/- 0.031456 |
| 64 | 100 | 0.999312 +/- 0.000908 | 100.630480 +/- 0.896408 | 16.837314 +/- 0.094561 |

Dynamic-run conformation averages; q² EM is the exact transient prediction for the sampled times. Ree²/Rg² predictions follow the formulas above and are retained in raw analysis.json.

| bits | N | dt | steps | q² +/- SE | q² EM | Ree² +/- SE | Rg² +/- SE |
|---|---|---|---|---|---|---|---|
| 32 | 8 | 0.01 | 360 | 1.023303 +/- 0.004528 | 1.030207 | 7.95219 +/- 0.19258 | 1.47880 +/- 0.02405 |
| 32 | 8 | 0.005 | 720 | 1.011759 +/- 0.004439 | 1.014762 | 7.81735 +/- 0.18884 | 1.46697 +/- 0.02376 |
| 32 | 8 | 0.0025 | 1400 | 1.004634 +/- 0.004787 | 1.007294 | 7.85159 +/- 0.18320 | 1.45926 +/- 0.02338 |
| 32 | 32 | 0.01 | 4640 | 1.031944 +/- 0.001462 | 1.030633 | 33.40850 +/- 0.72706 | 5.66576 +/- 0.08894 |
| 32 | 32 | 0.005 | 9240 | 1.016065 +/- 0.001405 | 1.014965 | 31.91349 +/- 0.69169 | 5.49939 +/- 0.08660 |
| 32 | 32 | 0.0025 | 18440 | 1.008421 +/- 0.001377 | 1.007398 | 31.72698 +/- 0.67908 | 5.45184 +/- 0.08279 |
| 32 | 100 | 0.01 | 43080 | 1.030996 +/- 0.000671 | 1.030650 | 98.56919 +/- 2.01001 | 16.70136 +/- 0.24357 |
| 32 | 100 | 0.005 | 86160 | 1.013560 +/- 0.000621 | 1.014971 | 97.20554 +/- 2.15325 | 16.46776 +/- 0.26038 |
| 32 | 100 | 0.0025 | 172280 | 1.007765 +/- 0.000638 | 1.007400 | 100.74967 +/- 2.17732 | 16.87711 +/- 0.26477 |
| 64 | 8 | 0.01 | 360 | 1.039490 +/- 0.004714 | 1.030207 | 8.45884 +/- 0.21139 | 1.55132 +/- 0.02663 |
| 64 | 8 | 0.005 | 720 | 1.020528 +/- 0.004583 | 1.014762 | 8.04423 +/- 0.19648 | 1.49486 +/- 0.02447 |
| 64 | 8 | 0.0025 | 1400 | 1.004085 +/- 0.004314 | 1.007294 | 7.62799 +/- 0.16628 | 1.44895 +/- 0.02128 |
| 64 | 32 | 0.01 | 4640 | 1.032372 +/- 0.001398 | 1.030633 | 31.67293 +/- 0.70852 | 5.48168 +/- 0.08480 |
| 64 | 32 | 0.005 | 9240 | 1.012632 +/- 0.001405 | 1.014965 | 30.28949 +/- 0.68443 | 5.25484 +/- 0.08264 |
| 64 | 32 | 0.0025 | 18440 | 1.004303 +/- 0.001409 | 1.007398 | 31.77168 +/- 0.70419 | 5.45007 +/- 0.08602 |
| 64 | 100 | 0.01 | 43080 | 1.030752 +/- 0.000640 | 1.030650 | 100.12677 +/- 2.36330 | 16.87327 +/- 0.27731 |
| 64 | 100 | 0.005 | 86160 | 1.015032 +/- 0.000620 | 1.014971 | 103.52384 +/- 2.22050 | 17.17758 +/- 0.26920 |
| 64 | 100 | 0.0025 | 172280 | 1.006179 +/- 0.000624 | 1.007400 | 99.32772 +/- 2.01295 | 16.79209 +/- 0.24444 |

Dynamics at the longer checked lag (approximately tau1/2); the additional tau1/4 lag also passed in every case. Continuous tau1=2.76361979, 36.80738003, 344.55357723 approximately; D=0.111111111, 0.0303030303, 0.00990099010. EM references in the last two columns account for the actual dt.

| bits | N | dt | D_CM +/- SE | Cee +/- SE | Cee EM | tau1 +/- SE | tau1 EM |
|---|---|---|---|---|---|---|---|
| 32 | 8 | 0.01 | 0.1145074 +/- 0.0023940 | 0.527914 +/- 0.012560 | 0.548007 | 2.52808 +/- 0.09982 | 2.75862 |
| 32 | 8 | 0.005 | 0.1089409 +/- 0.0023370 | 0.532842 +/- 0.012055 | 0.548819 | 2.63581 +/- 0.10093 | 2.76112 |
| 32 | 8 | 0.0025 | 0.1111172 +/- 0.0023622 | 0.536322 +/- 0.012787 | 0.539195 | 2.72677 +/- 0.11714 | 2.76237 |
| 32 | 32 | 0.01 | 0.0290790 +/- 0.0006053 | 0.507661 +/- 0.012709 | 0.504659 | 36.49044 +/- 1.53853 | 36.80238 |
| 32 | 32 | 0.005 | 0.0307750 +/- 0.0007392 | 0.506644 +/- 0.012626 | 0.505995 | 36.78316 +/- 1.57198 | 36.80488 |
| 32 | 32 | 0.0025 | 0.0300434 +/- 0.0006533 | 0.509531 +/- 0.012393 | 0.506663 | 35.44161 +/- 1.43979 | 36.80613 |
| 32 | 100 | 0.01 | 0.0097221 +/- 0.0001989 | 0.488743 +/- 0.012050 | 0.497277 | 346.39562 +/- 14.63200 | 344.54858 |
| 32 | 100 | 0.005 | 0.0096152 +/- 0.0002193 | 0.489628 +/- 0.013114 | 0.497349 | 338.09431 +/- 14.95850 | 344.55108 |
| 32 | 100 | 0.0025 | 0.0099146 +/- 0.0002081 | 0.510870 +/- 0.013250 | 0.497444 | 366.05327 +/- 16.90376 | 344.55233 |
| 64 | 8 | 0.01 | 0.1125030 +/- 0.0021437 | 0.552637 +/- 0.013378 | 0.548007 | 2.83996 +/- 0.12840 | 2.75862 |
| 64 | 8 | 0.005 | 0.1113962 +/- 0.0022433 | 0.543177 +/- 0.012778 | 0.548819 | 2.65526 +/- 0.11082 | 2.76112 |
| 64 | 8 | 0.0025 | 0.1087905 +/- 0.0022438 | 0.501585 +/- 0.013265 | 0.539195 | 2.39889 +/- 0.09854 | 2.76237 |
| 64 | 32 | 0.01 | 0.0295299 +/- 0.0006296 | 0.507971 +/- 0.012610 | 0.504659 | 36.56806 +/- 1.53125 | 36.80238 |
| 64 | 32 | 0.005 | 0.0295544 +/- 0.0006003 | 0.474126 +/- 0.013865 | 0.505995 | 33.55373 +/- 1.49491 | 36.80488 |
| 64 | 32 | 0.0025 | 0.0303159 +/- 0.0006582 | 0.504420 +/- 0.013048 | 0.506663 | 36.23773 +/- 1.55834 | 36.80613 |
| 64 | 100 | 0.01 | 0.0096488 +/- 0.0002025 | 0.498814 +/- 0.012852 | 0.497277 | 336.62397 +/- 14.15155 | 344.54858 |
| 64 | 100 | 0.005 | 0.0097374 +/- 0.0002300 | 0.506530 +/- 0.012203 | 0.497349 | 364.09032 +/- 14.94403 | 344.55108 |
| 64 | 100 | 0.0025 | 0.0094513 +/- 0.0002005 | 0.504863 +/- 0.011632 | 0.497444 | 349.73292 +/- 14.05429 | 344.55233 |

All 225 family checks passed. Maximum absolute physics residual was **3.689 SE** (double N=8, dt=0.0025, nonlinear tau1 estimate). Some individual 95% intervals exclude theory; this is disclosed rather than reclassified or rerun with a different seed. All 27 single/double conformation residual differences passed using combined independent SE; largest |z|=**2.476**. Both precisions independently passed the same dynamic theory checks.

### Timestep convergence

Inverse-variance pooling of q²-1 across the independent N cases gives:

| bits | dt | measured bias +/- SE | exact transient EM bias |
|---|---|---|---|
| 32 | 0.01 | 0.0310210 +/- 0.0006041 | 0.0306391 |
| 32 | 0.005 | 0.0139339 +/- 0.0005634 | 0.0149663 |
| 32 | 0.0025 | 0.0078339 +/- 0.0005751 | 0.0073982 |
| 64 | 0.01 | 0.0311596 +/- 0.0005776 | 0.0306403 |
| 64 | 0.005 | 0.0147295 +/- 0.0005633 | 0.0149665 |
| 64 | 0.0025 | 0.0058398 +/- 0.0005660 | 0.0073979 |

The coarse-to-fine bias decrease is resolved at **27.80 SE** (float) and **31.31 SE** (double). All pooled predictions differ from measurement by less than 3 SE. Individual long-scale dimensions and relaxation times are too noisy to resolve their much smaller O(dt) bias monotonically; the strong bond-size convergence is the appropriate detectable signature. No precision loss is invoked to explain EM variance inflation.

### Performance, separate from scientific gates

Each probe used N=31, 2048 chains, **65,536 beads**, **2,000 steps**, dt 0.005, sampling only at start/end. Timings exclude initialization, allocation and CUDA context startup. CUDA events measure the update-stream interval, including host launch gaps; sampling/readback and CSV output use wall clocks. There is no kernel tuning or broad benchmark claim.

| bits | GPU update s | sampling/readback s | CSV output s | wall s | bead updates/s | explicit device bytes | CUDA memory delta bytes |
|---|---|---|---|---|---|---|---|
| 32 | 0.0087716 | 0.0003324 | 0.0119428 | 0.0210528 | 1.49427e+10 | 2851072 | 6291456 |
| 64 | 0.1857193 | 0.0003125 | 0.0118644 | 0.1979013 | 7.05753e+08 | 4948224 | 8388608 |

Explicit bytes cover the two coordinate buffers, immutable RNG IDs, weights and observations; UAMMD has additional internal storage. cudaMemGetInfo deltas include allocator granularity. The short float probe is cache/launch sensitive and CSV output dominates its wall time; these numbers are not production-scale throughput estimates. Double RNG/transcendentals are materially slower on this GPU.

## Build, execution and diagnostic results

Hardware/toolchain: NVIDIA GeForce RTX 3060 Ti (8 GiB, capability 8.6), NVIDIA
driver 580.178.04, CUDA 13.0.88 at /usr/local/cuda, g++ 11.4.0, NumPy 2.2.4.
Both ordinary UAMMD float and DOUBLE_PRECISION builds compiled and executed.

From the isolated repository root, exact reproduction commands:

```sh
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
python3 examples/slip-springs/validate.py suite /tmp/rouse-validation-new
```

Both make checks and the full suite exited 0. GPU tests checked N=1,2,8 force
oracles, constant/straight/arbitrary chains, free ends, conservation, translating
one chain, CPU-reference EM update and deterministic conformation/COM/mode
observations including large common coordinate translations. RNG tests used
131072 IDs, all components, Gaussian moments/covariances, exact replay and ID
permutation, steps 2^40 and floor(UINT64_MAX/8)-1. Float component second moments
were 0.998243,0.998402,0.997586; double 1.00421,1.00342,0.998327, within fixed gates.
CPU matrix/theory tests, decimal-log naming regression, minimum duration check,
CLI invalid-input/stability/counter checks, sample scheduling, optional
equilibration, maximum seed replay, no-overwrite and output isolation passed.
Stage 0's GPU and read-only Correlator6 smokes still passed in both make checks.
Its previously documented Correlator6 leak was not changed and is not used here.

The installed /usr/bin/compute-sanitizer was unusable (missing injection
library). Selecting the complete CUDA13 tool resolved the tooling obstacle.
Executed:

```sh
/usr/local/cuda/compute-sanitizer/compute-sanitizer --tool memcheck --error-exitcode 99 examples/slip-springs/build/single/rouse --springs 8 --chains 16 --steps 17 --sample 4 --equil 3 --output /tmp/rouse-stage1-memcheck-single
/usr/local/cuda/compute-sanitizer/compute-sanitizer --tool memcheck --error-exitcode 99 examples/slip-springs/build/double/rouse --springs 1 --chains 16 --steps 17 --sample 4 --equil 3 --output /tmp/rouse-stage1-memcheck-double
/usr/local/cuda/compute-sanitizer/compute-sanitizer --tool racecheck --error-exitcode 99 examples/slip-springs/build/single/rouse --springs 8 --chains 16 --steps 17 --sample 4 --output /tmp/rouse-stage1-racecheck
```

Both memchecks reported 0 errors; racecheck reported 0 hazards. Racecheck detects
shared-memory hazards and does not prove absence of global-memory update races;
separate old/new arrays and the CPU-reference tests supply that evidence.
Use fresh output paths to reproduce these no-overwrite commands.

Execution issues were investigated and retained:

1. The first suite stopped after its first dynamic case: using Path.with_suffix
   on decimal timestep directory names made different timesteps share one log
   path. Fixed log naming without overwriting original artifacts; added a
   regression test. No scientific check failed and no tolerance changed.
2. The next complete suite passed, but review found nearest-integer sampling
   strides could make the duration slightly shorter than the predeclared
   1.25tau1 minimum. Changed scheduling to ceiling, added a duration regression
   and reran the entire final suite with the same seeds/thresholds in a new
   directory. Its results are the tables above, not a selected seed rerun.

Final raw CSV/analysis/metadata and summary:
`/tmp/rouse-stage1-validation-final/`; suite log:
`/tmp/rouse-stage1-suite-final.log`; make logs:
`/tmp/rouse-stage1-check-single.log`, `/tmp/rouse-stage1-check-double.log`.
Earlier run directories /tmp/rouse-stage1-validation and
/tmp/rouse-stage1-validation-v2 remain for audit. Raw data are temporary artifacts,
not committed source; the documented commands regenerate them. Generated CSV
rows contain unwrapped COMs and chain observables, not full bead trajectories.

## Precision limits, remaining scope and recommendation

No sampled collapsed bond or nonfinite observable occurred. Across the final
N=8,32,100 dynamic cases the largest absolute coordinates were approximately 27;
maximum coordinate spacing/sqrt(2dt) was 2.70e-5 for float and 5.03e-14 for double,
well below the predeclared 0.01 threshold. Double accumulation of observables
cannot recover coordinate information already rounded away in float. No
recentering, wrapping or mixed-precision coordinates were added. Arbitrarily
long COM diffusion can eventually defeat either precision; this finite test
range is not a guarantee for very long trajectories. Counter overflow is
prevented, but statistical quality across all 2^61 possible step values has not
been certified, and wall-time/output-time resolution is finite.

Direct-lag Python analysis uses RAM proportional to chain sample history;
per-chain CSV output can dominate short, fast simulations. These are intentional
Stage 1 limits. The 512-chain dynamics study has percent-level uncertainties,
not production-quality precision on every relaxation time. Both precision
variants were checked statistically; identical paths are neither expected nor
required. No production campaign or kernel optimization was performed.

**Stage 2 is scientifically justified after review of Stage 1**, using this
validated Rouse baseline and its exact finite-step theory. It remains necessary
to derive chain-density normalization and channel weights, validate stress
relaxation against exact discrete modes, and address the read-only Correlator6
memory lifecycle/deepest-lag behavior documented in Stage 0. Those are Stage 2
requirements, not implemented physics or claims of stress validation here.
No semiflexible, slip-spring, hydrodynamic or excluded-volume feature was added.

Before commit, a programmatic diff against d899817 and the original 81fe5de base,
plus all untracked/ignored paths, must contain only examples/slip-springs/ paths;
Git diff whitespace checks and branch ancestry must pass. The handoff records
the final audit and commit/push result.
