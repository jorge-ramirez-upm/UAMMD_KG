# GPU Rouse chains and configurational stress: Stage 2A

This standalone UAMMD/CUDA example simulates independent Gaussian chains with
local Euler–Maruyama Brownian dynamics. It is a distinct coarse-grained model
from Kremer–Grest molecular dynamics. Stage 1 implements equilibrium Gaussian
initialization, free-end harmonic forces, unwrapped updates, conformation
observables and direct-lag dynamic validation. Stage 2A adds double-accumulated
GPU per-chain configurational stress, direct-lag stress correlations and permanent
performance reporting. Correlator6, stress multi-tau analysis, relaxation modulus,
semiflexibility and slip-springs remain future, unauthorized work.

A chain has **N springs and N+1 beads**, numbered 0 through N. Units are
b=kBT=zeta=1 per bead, tau_0=1, tau_s=1/3. Its energy is
`U=(3/2) sum |r_(i+1)-r_i|^2`; there are no excluded-volume, hydrodynamic,
interchain or periodic interactions. Every update reads an old buffer and writes
a different buffer. All chains share one UAMMD particle ensemble.

All source changes and generated files must stay in `examples/slip-springs/`
or, for generated artifacts, outside the repository. Existing UAMMD, KG and
KG_Assoc files remain read-only. `STAGE0_REPORT.md` is historical; see
[STAGE1_REPORT.md](STAGE1_REPORT.md) and [STAGE2A_REPORT.md](STAGE2A_REPORT.md)
for numerical results and limitations, and
[AGENTS.md](AGENTS.md) for permanent scientific/development rules.

## Build and quick tests

Requirements: GNU Make, a C++17 host compiler, a CUDA toolkit including cuRAND
headers and Thrust/CUB, a compatible NVIDIA GPU, and Python 3.10+ with NumPy for
analysis/tests. Nothing is downloaded automatically. CUDA 13 requires C++17.
The device RNG is header-only; no cuRAND library linkage is needed.

From this worktree's repository root:

```sh
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
```

`check` builds/runs the Stage 0 smokes, GPU force/observation/RNG unit tests,
independent CPU matrix/Wick-theory tests, and CLI/reproducibility/timer tests. It does
**not** run the full stochastic suite below. Use `make rouse` for the simulator
alone or `make all` to build all executables without running them. `make
check-correlator` remains CPU-only; Correlator6 is not used by the simulator.

`CUDA_HOME` selects the toolkit, or set `NVCC=/path/to/nvcc`. `CXX=/path/to/g++`
also selects nvcc's host compiler. `CUDA_ARCH=sm_86` matches the validation GPU;
choose yours or omit it for nvcc's default. `UAMMD_ROOT` overrides the default
relative repository root. CPPFLAGS, CXXFLAGS, NVCCFLAGS and LDLIBS are configurable;
retain C++17 and `--extended-lambda`, and do not enable fast-math for validated
precision behavior. Clean and rebuild after changing compiler/flags/header root.

`PRECISION=single` (default) uses UAMMD `real=float`; `PRECISION=double` defines
`DOUBLE_PRECISION`. Separate binaries live in `build/single/` and `build/double/`.
`make clean` removes only named executables/dependency files, preserving run data.
The previous Stage 0 smoke and correlator sources remain available unchanged.

## Running the current simulator

Run these from the `slip-springs` worktree's repository root (the development
worktree is `/tmp/UAMMD_KG-slip-springs`). Commands below target the RTX 3060 Ti
with CUDA13 at `/usr/local/cuda`. Output directories must not exist; choose a
new name for subsequent runs. Both short runs and the moderate run were executed.
Create a fresh parent once in the same shell; each simulator gets a new child:

```sh
STRESS_EXAMPLES=$(mktemp -d /tmp/rouse-stage2a-examples.XXXXXX)
```

Build single precision and run a short example (N=8, 256 chains, dt0.005,
200 steps, sample10, seed240008):

```sh
make -C examples/slip-springs rouse CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
examples/slip-springs/build/single/rouse --springs 8 --chains 256 --dt 0.005 --steps 200 --sample 10 --equil 0 --seed 240008 --output "$STRESS_EXAMPLES/single"
python3 examples/slip-springs/stress.py analyze "$STRESS_EXAMPLES/single"
```

Build double precision and run the same small configuration with seed240009:

```sh
make -C examples/slip-springs rouse CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
examples/slip-springs/build/double/rouse --springs 8 --chains 256 --dt 0.005 --steps 200 --sample 10 --equil 0 --seed 240009 --output "$STRESS_EXAMPLES/double"
python3 examples/slip-springs/stress.py analyze "$STRESS_EXAMPLES/double"
```

A moderately long Rouse run with stress at every observation (N=32, 512 chains,
dt0.005, 20,000 steps, sample20, seed240032; physical duration100 tau_0):

```sh
examples/slip-springs/build/single/rouse --springs 32 --chains 512 --dt 0.005 --steps 20000 --sample 20 --equil 0 --seed 240032 --output "$STRESS_EXAMPLES/moderate"
python3 examples/slip-springs/stress.py analyze "$STRESS_EXAMPLES/moderate"
python3 examples/slip-springs/validate.py analyze "$STRESS_EXAMPLES/moderate"
```

Scientific validation, including the complete Stage 1 regression suite:

```sh
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
python3 examples/slip-springs/validate.py suite /tmp/rouse-stage1-regression-new
python3 examples/slip-springs/stress.py suite /tmp/rouse-stage2a-validation-new
```

The Stage 1 suite specifies N=8/32/100, dt0.01/0.005/0.0025, 512 chains,
stride=ceil(tau1/(32dt)), steps=40*stride, and seed710000+100N+dt_index+
10000*precision_index. Its initialization runs use8192 chains and seed20261015+N.
The Stage 2A suite specifies N=8/32/100, dt0.01/0.005/0.0025, 2048 chains,
stride=round(0.05/dt), steps=64*stride and seed820000+100N+dt_index+
10000*precision_index. Its zero-step equilibrium runs use8192 chains,
dt0.005, stride10 and seed20262015+N+10000*precision_index.
Both use equil0, precision_index0/1 and dt_index0/1/2. The plans in tests/ fix
all seeds and acceptance rules before execution.

Locate the example results:

```sh
ls "$STRESS_EXAMPLES/single/"
ls "$STRESS_EXAMPLES/double/"
ls "$STRESS_EXAMPLES/moderate/"
```

The simulator prints the absolute output path; `$STRESS_EXAMPLES` holds it
for these commands. They contain CSV samples/ensembles and metadata.json; stress analysis adds
stress_analysis.json and stress_chain_contributions.npz. Full suites save
summary.json plus per-run data and terminal logs under the named /tmp directory.

`--output` must name a **new** directory. The executable refuses overwrite and
rejects output elsewhere inside its source repository. The default is this
project's `build/run`. All options are optional; `--help` lists them. `--steps`
is the production count; `--equil` advances before the first observation and
uses the same continuous RNG counter. Step/time zero in output is the end of
that optional equilibration, not the original initialization. Samples include
production step zero, every sampling interval, and a final shorter interval
when needed. No full bead trajectories are written. There is no thermostat,
box, checkpoint/resume or snapshot configuration.

Outputs:

- `samples.csv`: one row per chain/sample: production step, time, chain ID,
  mean bond q^2, Ree^2, Rg^2, COM xyz, end-to-end xyz, orthonormal p=1 mode xyz,
  maximum absolute coordinate, count of collapsed bonds, and raw per-chain
  Sxx,Syy,Szz,Sxy,Sxz,Syz (appended after existing Stage 1 columns). Double reductions
  operate on the stored coordinate precision. This is O(chains*samples) data.
- `ensemble.csv`: conformation means and standard errors across independent
  chains at each sample. For one chain, SE is NaN because it is not estimable.
- `metadata.json`: configuration, **effective** precision-rounded dt, seed,
  hardware, timing/memory measurements and coordinate-resolution diagnostics.
- `analysis.json` from Python: chain-cluster uncertainty estimates, conformation
  theory, multi-origin COM diffusion, normalized end-to-end and p=1 correlations,
  longest relaxation time and explicit checks that were available for the run.
- `stress_analysis.json`: raw diagonal and separate shear/normal-difference lag
  correlations, continuous and exact transient EM references, means, second
  moments, paired isotropy checks, chain-based SE and approximate 95% intervals.
- `stress_chain_contributions.npz`: lag_steps, origins_per_lag, chain_ids,
  channels and per-chain correlations (axes: lag,chain,channel), plus raw
  diagonal contributions. Normal-difference contributions are divided by4.
  These retain channel covariance; do not average their SEs as if independent.

Analysis loads sampled chain vectors into RAM and uses direct lag sums; use
small/moderate histories. Overlapping origins are averaged within each chain;
uncertainty uses independent chains, not the number of time-origin pairs. A
short run may have no dynamic checks; only the full suite validates Stage 1.
An irregular final sample is excluded from lag calculations. At least two chains
are needed for uncertainty estimates.

## RNG and precision

The local kernel uses CUDA cuRAND **Philox4x32-10** with the explicit 64-bit seed.
Each logical bead owns a subsequence; eight 32-bit draws are reserved per unsigned
64-bit timestep. Initialization bonds and independent Gaussian chain translations
use disjoint subsequence domains. Immutable IDs, not launch/storage indices,
key the RNG. Topology is fixed chain-contiguous; sorting/reordering requires
remapping neighbors while retaining IDs and is not supported by this executable.

Float builds call `curand_normal4` (float Gaussian math). Double builds call
`curand_normal2_double` twice: 53-bit uniform construction and double
Box–Muller/transcendentals, rather than casting float Gaussians. Only xyz are
used. Both are finite-precision pseudorandom approximations, with finite tails;
reproducibility is for the same executable/toolkit/device, not across platforms
or precisions. No claim of cryptographic randomness or exhaustive RNG testing.

Reject equilibration+production >floor(UINT64_MAX/8); never reset/wrap that
counter to extend a run. Restarting this executable with the same seed starts
again from the same initial ensemble. A future checkpoint feature must preserve
absolute steps/IDs. There are no persistent per-bead RNG states.

Bonds are sampled independently with each component variance1/3 and accumulated
in the selected precision. No dynamic equilibration is required to obtain the
initial continuous-time equilibrium distribution. Euler–Maruyama subsequently
introduces stationary variance bias. Analysis uses exact transient finite-step
mode covariance as well as continuous theory; this bias is not a precision bug.
Unwrapped COM coordinates grow without bound, eventually losing small increments
and bond differences. Metadata records max coordinate spacing/sqrt(2dt) and
collapsed sampled bonds; these diagnostics certify only the sampled range.
No recentering or mixed-precision coordinates are implemented.

## Full scientific validation

Acceptance thresholds, seeds and uncertainty definitions are in
[tests/VALIDATION_PLAN.md](tests/VALIDATION_PLAN.md), set before execution.
After both precision builds:

```sh
python3 examples/slip-springs/validate.py suite /tmp/rouse-validation-new
```

The new output directory contains per-run CSVs/metadata, logs and `summary.json`.
The suite executes N=8,32,100 initialization checks (8192 chains), then three
timesteps 0.01/0.005/0.0025 and both precisions (512 chains). Each trajectory
covers at least 1.25 exact slowest relaxation times. It also compares the two
precisions statistically and records one separate small timing probe per build.
Exit zero requires every predeclared scientific gate; runtime failure never
counts as a pass. This is bounded validation, not a production campaign.

## Configurational stress and exact references

At each requested observation the existing GPU pass accumulates
`S_ab=3 sum_i q_ia*q_ib` from unwrapped stored bonds in double precision, even
when coordinates use float. Only chain observables are copied to the CPU.
There is no simulation volume, kinetic stress or density prefactor.

`stress.py` preserves xy,xz,yz,xx-yy,xx-zz,yy-zz separately. Shear products are
unchanged; normal-difference products carry1/4. It computes uncentered direct
products at matching chain IDs and multiple time origins, then chain-level SE.
Raw diagonal autocorrelations include the mean-stress product; they are not
compared to a zero-mean shear formula. There is no mean subtraction or channel
averaging. The three normal differences are linearly dependent.

Continuous equilibrium shear correlation is sum_p exp(-2 lambda_p*t).
For EM, with a_p=1-lambda_p*dt and per-coordinate mode variance v_p(n), use
`mean_origins(sum_p (lambda_p*v_p(n)*a_p^lag)^2)`. The square is taken BEFORE
the origin average. Evolved zero-lag moments reflect EM bias, whereas initial
moments are N for shears and4N for raw normal differences. Default direct lags
are0,1,4,16,32 sample intervals; unavailable lags are skipped. Short examples
are demonstrations, not replacements for the full predeclared validation suite.

## Permanent performance reporting

Every successful simulation prints counts, physical time and measured rates,
including zero-step initialization runs. Metadata timing_schema_version2 uses:

- update_seconds: summed CUDA-event intervals for production integration only.
  Includes host launch gaps between recorded events; excludes sampling and host
  synchronization wait. GPU event timing is not the sum of isolated kernel times.
- production_seconds (wall_seconds alias): wall interval containing the initial
  sample, all production updates/synchronization, sampling/D2H and recurrent
  CSV formatting/writing. Excludes initialization, optional equilibration and
  final file flush/close.
- sampling_seconds: GPU observation plus blocking recurrent D2H wall time.
  It is part of production_seconds, not an additional disjoint run duration.
- recurrent_output_seconds: in-loop CSV formatting/writing (also part of production).
- final_output_seconds: final CSV flush/close, measured after production ends.
  output_seconds is recurrent_output_seconds+final_output_seconds.
- initialization_seconds: System/CUDA context creation, allocation, weights,
  Gaussian conformation initialization and output setup. Context time is also
  separately available. Equilibration wall/GPU times have separate fields.
- integration_ns_per_bead_step=1e9*update_seconds/(total_beads*production_steps).
  overall_ns_per_bead_step uses production_seconds with the same denominator.
  bead_updates_per_second uses the inverse measured update time. All three are
  JSON null and terminal N/A for zero production steps, including runs with
  nonzero optional equilibration.

All duration fields are seconds; rates are labeled explicitly. Metadata
serialization/closing, terminal logging and final System shutdown are telemetry
or teardown outside these intervals. File timers measure buffered OS I/O, not
fsync-to-device durability. Timer scope intentionally differs from historical
Stage 1 schema1, which included equilibration and final flushing in broader sums.

## Roadmap

Stages 0, 1 and 2A are implemented. Stage 2B may integrate the read-only
Correlator6 after review and explicit authorization, including its known memory
and lag limitations. Modulus normalization needs a separate derivation. Stage 3
is optimization; Stage 4 is semiflexibility and slip-spring dynamics. No Stage 2B
or later feature is implemented or authorized here.
