# E1 Stage B — nearest-neighbor Metropolis hopping

Implemented and bounded verification completed on 21 October 2026. Starting
local and remote `slip-springs` HEAD both matched the requested
`3301b3a8d0b02eebaa01cd2fc8414700f1d64261`; the working tree was clean.
Stage A remains available without hopping. This report does not establish
terminal dynamics, rheology, full E1 ergodicity, or a numerical timestep limit.

## Interface and splitting

The existing `semiflexible` executable adds `--hop-rate NU`, in inverse simulation
time, default **0**. It must be finite and nonnegative. No scientific numerical
value of NU is frozen. Existing `--slip-count Z` and `--slip-ms2 A2` retain their
meaning. Every active slip-spring still requires `--stress-mode off`, including
when NU=0; no stress estimator was changed or added.

One timestep is:

1. Evaluate the accepted backbone and spring forces at `(R_n,S_n,A)`.
2. Apply the unchanged Euler–Maruyama bead update, including its existing noise.
3. Freeze the new coordinates `R_(n+1)` and draw
   `K ~ Poisson(Z*NU*dt)`.
4. Process K attempts sequentially, selecting a spring uniformly **with
   replacement** and either direction with probability 1/2. Check boundaries
   and occupancy, then accept with `min(1,exp(-DeltaE/kBT))`. Each acceptance
   immediately updates the attachment, occupancy map and bead-indexed anchor
   buffer; later attempts in that batch read the updated state.
5. Check invariants, diagnose errors, then observe. The next force evaluation
   (including the final-state check) uses the new attachment state.

Thus m=1 is fixed and no interval option exists. At zero integration steps or
with `--force-input`, no hopping batch runs. NU=0 or Z=0 skips hopping RNG,
allocations, kernels, diagnostics and additional output files. Disabled results
preserve Stage A's exact deterministic data and non-timing metadata.

## State, arithmetic, RNG and bounds

Each stable spring slot stores a fixed anchor, current flat bead site, chain and
previous/next spring IDs along the contour. A dense integer occupancy map maps
beads to IDs; the existing Stage A dense anchor buffer and force kernel are
reused. An accepted move clears its source and fills its destination. Neighbor
links and chain membership never change in Stage B. This separation permits a
future renewal event to relink a stable slot and replace its anchor/chain without
changing the force interface; no such event is implemented here.

Outward proposals are null events. There is no chain transfer, escape,
reanchoring, renewal or constraint release. Static slot count and immutable
chain membership conserve global and individual-chain populations. Vacancy of
an adjacent bead prevents overtaking; explicit linked-order, reciprocal-neighbor,
site/chain, anchor-buffer and bidirectional occupancy checks run on the GPU.
The one global event producer is one CUDA thread, so there are no conflicting
accepted moves or stale concurrent occupancy reads.

Positions, anchors and forces retain Stage A `real` precision. Metropolis uses
double intermediate arithmetic on the stored coordinates, the same effective
precision-rounded spring stiffness as the force kernel, and the input kBT.
A difference-of-squares expression computes DeltaE/kBT; log-uniform comparison
avoids exponent overflow. Nonfinite changes fail instead of being clamped or
converted into acceptance. No validated backbone force law, Brownian RNG,
initializer or stress computation was modified.

Philox is initialized from the full simulation seed and subsequence
`2^61 | step`, offset zero. These step subsequences lie in `[2^61,2^62)` and are
disjoint from the bounded stable bead IDs and existing Rouse/semiflexible RNG
domains. Variable event counts use a whole subsequence, **not** an overlapping
fixed draw reservation per step. Integer rejection sampling removes modulo
bias from spring selection. Uniform variates and acceptance logs use double in
both builds. Replay is for the same executable/toolkit/hardware/precision;
cross-platform or cross-precision trajectories are not promised.

The Poisson sampler counts unit-rate exponential arrivals until their cumulative
time exceeds the requested double mean. This is the Poisson-process construction
of K, not a normal approximation. It consumes O(K+1) draws. Inspection of installed
CUDA 13.0 `curand_poisson.h` found a float-mean conversion and a large-mean normal
branch; see also [NVIDIA's cuRAND source](https://docs.nvidia.com/cuda/curand/curand/curand__poisson_8h_source.html).
Those shortcuts were unsuitable for the requested scheduling contract.

The host computes the mean with a wider intermediate and rejects a positive
mean that underflows on conversion, any nonfinite mean, and means above **10000**.
A drawn K above **100000**, random rejection retry exhaustion, or uint64 batch/
attempt-counter overflow aborts with a diagnostic. These are explicit resource
bounds: there is no rate reduction, K clipping, redraw of excessive K, or partial
successful batch reported after a failure. Guards are tested by fault injection;
no claim is made that the extremely rare supported-mean upper tail was sampled.
Finite random-number resolution and floating-point summation remain limitations.

## Outputs and diagnostics

With Z>0 and NU>0:

- `slip_springs_initial.csv` / `slip_springs_final.csv`: stable spring ID, chain,
  current bead, fixed anchor. `fixed_slip_springs.csv` remains the legacy **initial**
  Stage A snapshot and must not be interpreted as final attachments in Stage B.
- `hopping_metadata.json`: rate, requested Poisson mean, m=1, splitting/RNG
  convention, resource limits, attempted/accepted/boundary/exclusion/Metropolis
  counts, actual added device capacity and timer scope.
- Main metadata identifies `metropolis-hopping-development` and includes added
  allocations in `device_bytes` and the conservative workspace estimate.
  Integration CUDA events explicitly include hopping, invariants and diagnostic
  D2H plus launch/synchronization gaps; observation/output remain separate.
- On failure, existing coordinate/proposal snapshots remain. The additional
  `slip_springs_failure.csv` records attachment/anchor state, and `failure.json`
  includes hopping rate/mean and stage. Reasons 6/7 denote hopping state invariant
  failure and numerical/scheduling failure respectively. A fatal batch can
  contain earlier accepted attempts; it is not a completed scientific sample.

No event or attachment trajectory is retained. All new output streams explicitly
check close/write errors. Existing refusal to overwrite run directories remains.

## Independent scientific reference and bounded evidence

`slip_hopping_reference.py` is independent NumPy/Python code, with total energies,
explicit admissible-sector enumeration, a continuous-time generator, its matrix
exponential, and CPU Poisson/Metropolis sampling. It does not call production
CUDA arithmetic or RNG code. For adjacent allowed states:

```text
w(X,Y) = NU/2 * min(1, exp(-(E_Y-E_X)/kBT))
pi_X*w(X,Y) = pi_Y*w(Y,X)
```

Null boundary/occupied proposals add holding probability. Uniform Poissonization
of the sequential attempt kernel gives `exp(dt*Q)` at fixed coordinates. Varying
NU scales Q but does not change its stationary vector within the fixed population/
order sector. The implemented BD/hopping composition has finite-dt integration
and splitting errors and is not claimed to sample that law exactly at finite dt.

Tests enumerate four one-spring states and six ordered two-spring states on a
four-bead chain, and 36 two-chain configurations at fixed populations. They verify
forward/reverse ratios and flux symmetry, exclusion, ordering, endpoints,
repeated spring selections in one batch, force relocation and the conditional
Boltzmann weights. Conditional weights at fixed anchors are deliberately tested
as **nonuniform**. Independent Gaussian anchor integrals recover equal annealed
site weights; these are different ensembles.

GPU fixtures call the actual production device functions at fixed coordinates.
Independent replicas, rather than overlapping origins from a long trajectory,
provide the statistical units. Predeclared 6-SE checks use 8192 independent
replicas, 8 batches, dt=0.25, rates 0.5 and 4, in the six-state two-spring sector.
The tests check stationarity from independent exact equilibrium starts and
transient distributions from a definite start against `exp(t*Q)`.

| Rate | Maximum absolute stationary-frequency error | Measured probability of final state differing from initial | Exact generator prediction |
|---:|---:|---:|---:|
| 0.5 | 0.00615213 | 0.519165 | 0.508826 |
| 4 | 0.00738528 | 0.811768 | 0.805182 |

Both precisions pass all declared uncertainty checks. These rates change
kinetics while preserving the predicted stationary distribution. Poisson means
0, 0.3, 4, 64 and 4096 pass bounded mean/variance checks; small-mean zero-count
probabilities are checked as well. This is limited numerical evidence, not an
exhaustive RNG or rare-tail certification.

Execution host: RTX 3060 Ti (sm_86), driver 580.178.04, CUDA 13.0.88, g++ 11.4.0,
C++17, `-O2`, no fast math; isolated `build/e1-stage-b/{single,double}` binaries.
GPU and leak-sanitizer checks ran outside the sandbox to obtain device/thread
access. Original campaign binaries, frozen criteria and authentication rules
were not rebuilt, replaced or relaxed. Programmatic tracked/untracked/ignored
path checks and comparison with the Stage 0 source SHA
`81fe5de9cd5ded849202eebab7c14e6bd35fb9ae` found no changes or generated paths
outside `examples/slip-springs/`. Byte checks confirmed the accepted backbone,
Stage A initializer/force, Rouse, stress and frozen analysis/plan sources are unchanged.

| Check | Actual result |
|---|---|
| New host mean/budget C++ checks and independent CPU reference (4 tests) | Pass |
| New CPU/GPU suite (8 tests), both precisions | Pass: enumeration, downhill/uphill acceptance, sequential/repeated events, blocked/full chains, multiple-chain populations, invariant/numeric/budget/counter fault injection, Poisson moments, equilibrium/transient kinetics, replay, zero modes and input/stress guards |
| Full timestep force relocation/noise isolation | Pass in both precisions: first BD update is byte-identical with hopping enabled; next-step coordinate difference equals the relocated spring drift |
| Existing Stage A initializer, frozen-anchor force/finite differences and 4 Python regressions | Pass in both precisions |
| Existing `check-semiflexible` and `check-semiflexible-stress` | Pass in both precisions (7 GPU, 2 host-tool, 12 CPU-reference and 7 stress cases) |
| Existing `make check` Rouse/CUDA/pipeline/CLI/stream/theory checks | Pass in both precisions |
| Stage A source reconstructed from starting SHA | Pass: default/explicit NU0 versus Stage A byte-identical initial/final coordinates, scalar/bond/parameter/anchor outputs and all non-timing metadata, both precisions, kappa0/2, Z0/3, N3,C4,kBT1.7,dt0.0001,5 steps,stride1,seed4317 |
| CUDA memcheck and racecheck, scripted plus stochastic multi-chain fixture | 0 errors / 0 hazards reported, both precisions |
| CUDA memcheck, active simulator N3,C2,kappa2,Z3,A2=2.4,NU10000,8 steps,stride2,seed4317 | 0 errors, both precisions |
| New C++ host checks ASan/UBSan/LSan; existing workers/lifetime sanitizers | Pass, leak detection enabled |
| Documented N8,C64,100-step active example | Pass in both precisions |
| Default CUDA 11.5.119/GCC 11 build | Fails with the preserved `std_function.h` parameter-pack compiler error; CUDA 13 builds pass |
| Historical campaign suite | 12/13 pass; authentication errors for changed `semiflexible.cu` source identity |
| Historical scalar suite | 6/7 pass; overlay authentication errors for the same frozen source identity |

The last two historical suites **do not pass overall**; their source-identity
refusal is preserved. The same limitation already applies to accepted Stage A.
Use the pinned historical checkout/binaries for that frozen campaign. No frozen
experiment was run. Local ignored logs, short outputs and comparison scripts
remain under `build/e1-stage-b/`; no generated scientific data is committed.

## Scaling, measured tiny examples and remaining limits

The current global event loop is deliberately serial: O(K) event/Poisson work,
plus a parallel O(L+Z) invariant pass each timestep, where L is total beads.
It is a correctness implementation, not an optimized large-ensemble scheduler.
There are no recurrent coordinate/attachment transfers for hopping; one integer
error readback follows each batch, consistent with existing synchronous
first-failing-step diagnostics. Initial/final state transfers and output are
separate. The original scalar observation transfers remain unchanged.

Added device storage is `L*sizeof(int)+Z*sizeof(Spring)+sizeof(Statistics)`:
4L+32Z+48 bytes in float and 4L+48Z+48 in double on this host. Host mirrors have
O(L+Z) storage and enter the conservative 2 GiB budget. All workspace is
independent of simulation length; resource limits also constrain large
Z*NU*dt explicitly.

The documented short run (N8,C64,Z32,A2=5,NU100,dt0.0001,100 steps,stride10,
seed4317,kappa2) gave 36 attempts and 21 acceptances in each precision. Added
hopping device bytes were 3376 (float) and 3888 (double). Integration/overall
costs were 77.83/128.65 ns per bead-step in float and 162.84/211.01 in double.
These single tiny-run measurements include synchronous diagnostics and are
neither a throughput benchmark nor evidence of portable performance.

Stage B fixes per-chain populations, contour order sectors and anchor identities.
It is **not dynamically ergodic over the full E1 ensemble**. Finite-dt accuracy,
very high rates, extreme parameters, large ensembles, terminal relaxation and
physical rheology remain unvalidated. No end escape, renewal, constraint release,
deformation or slip-spring stress correlation is implemented. Stage C has not
started. No long simulation campaign was run. All requested bounded GPU checks
were supported and executed; no hardware-unavailable GPU check remains pending.

## Reproducible bounded commands

From the repository root, with a compatible GPU and appropriate architecture:

```sh
B_BUILD="$PWD/examples/slip-springs/build/e1-stage-b"
make -C examples/slip-springs check-slip-hopping-cpu
make -C examples/slip-springs check-slip-hopping check-fixed-slip-springs check-semiflexible check-semiflexible-stress PRECISION=single CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$B_BUILD/single"
make -C examples/slip-springs check-slip-hopping check-fixed-slip-springs check-semiflexible check-semiflexible-stress PRECISION=double CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$B_BUILD/double"
SAN_OUT=$(mktemp /tmp/e1-b-sanitizer.XXXXXX)
/usr/local/cuda/bin/compute-sanitizer --tool memcheck --error-exitcode 99 "$B_BUILD/double/slip_hopping_gpu" examples/slip-springs/tests/slip_hopping_sanitizer.txt "$SAN_OUT"
B_RUNS=$(mktemp -d /tmp/e1-stage-b.XXXXXX)
"$B_BUILD/double/semiflexible" --springs 8 --chains 64 --kappa 2 --dt .0001 --steps 100 --sample 10 --seed 4317 --slip-count 32 --slip-ms2 5 --hop-rate 100 --stress-mode off --output "$B_RUNS/short"
```

A moderately long **unexecuted host-only demonstration**, not accepted numerical
parameters, uses N8,C64,dt0.0001,10000 steps,stride100,seed4317:

```sh
"$B_BUILD/double/semiflexible" --springs 8 --chains 64 --kappa 2 --dt .0001 --steps 10000 --sample 100 --seed 4317 --slip-count 32 --slip-ms2 5 --hop-rate 100 --stress-mode off --output "$B_RUNS/moderate"
```
