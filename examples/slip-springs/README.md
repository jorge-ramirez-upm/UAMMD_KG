# GPU Rouse chains: Stage 1

This standalone UAMMD/CUDA example simulates independent Gaussian chains with
local Euler–Maruyama Brownian dynamics. It is a distinct coarse-grained model
from Kremer–Grest molecular dynamics. Stage 1 implements equilibrium Gaussian
initialization, free-end harmonic forces, unwrapped updates, conformation
observables and direct-lag dynamic validation. Semiflexibility, slip-springs,
stress tensors and relaxation moduli are future, unauthorized stages.

A chain has **N springs and N+1 beads**, numbered 0 through N. Units are
b=kBT=zeta=1 per bead, tau_0=1, tau_s=1/3. Its energy is
`U=(3/2) sum |r_(i+1)-r_i|^2`; there are no excluded-volume, hydrodynamic,
interchain or periodic interactions. Every update reads an old buffer and writes
a different buffer. All chains share one UAMMD particle ensemble.

All source changes and generated files must stay in `examples/slip-springs/`
or, for generated artifacts, outside the repository. Existing UAMMD, KG and
KG_Assoc files remain read-only. `STAGE0_REPORT.md` is historical; see
[STAGE1_REPORT.md](STAGE1_REPORT.md) for current results and limitations and
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
independent CPU matrix-theory tests, and CLI/reproducibility tests. It does
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

## Run and analyze

```sh
examples/slip-springs/build/single/rouse \
  --springs 32 --chains 512 --dt 0.005 --steps 9240 \
  --sample 231 --equil 0 --seed 713201 \
  --output /tmp/rouse-example
python3 examples/slip-springs/validate.py analyze /tmp/rouse-example
```

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
  maximum absolute coordinate and count of collapsed bonds. Double reductions
  operate on the stored coordinate precision. This is O(chains*samples) data.
- `ensemble.csv`: conformation means and standard errors across independent
  chains at each sample. For one chain, SE is NaN because it is not estimable.
- `metadata.json`: configuration, **effective** precision-rounded dt, seed,
  hardware, timing/memory measurements and coordinate-resolution diagnostics.
- `analysis.json` from Python: chain-cluster uncertainty estimates, conformation
  theory, multi-origin COM diffusion, normalized end-to-end and p=1 correlations,
  longest relaxation time and explicit checks that were available for the run.

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

## Roadmap

Stage 0 infrastructure and Stage 1 independent Rouse dynamics are implemented.
After review, Stage 2 may add chain configurational stresses and density-consistent
Correlator6 relaxation modulus, including resolution of its known memory/lag
limitations. Stage 3 is performance optimization; Stage 4 is semiflexibility and
slip-spring dynamics. None of Stages 2–4 is implemented or authorized here.
