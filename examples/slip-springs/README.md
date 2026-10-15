# Gaussian chains and slip-springs: Stage 0

This directory starts a distinct coarse-grained Gaussian-chain project using
UAMMD and CUDA. It does not implement Kremer–Grest molecular dynamics.
**Only infrastructure and feasibility tests are implemented.** There are no
polymer forces, Brownian trajectories, stress calculations, or slip-springs yet.
Stage 1 must wait for review and approval of Stage 0.

The initial model will have N Gaussian springs, N+1 beads (indices 0 through N),
free ends, b=kBT=zeta=1, unwrapped coordinates, and energy
`U=(3/2) sum |r_(i+1)-r_i|^2`. It has no excluded volume, hydrodynamics, or
interchain interactions. Initial bonds will be drawn directly from equilibrium
Gaussian statistics. The fundamental time is tau_0=1; spring time tau_s=1/3.
The long-term aim is GPU Brownian dynamics of semiflexible Gaussian chains
with slip-springs, informed by previous CPU work and KG/KG_Assoc GPU experience.
Those extensions are future work.

## Files and isolation

- `Makefile`: independent build; never invokes existing application builds.
- `smoke_test.cu`: UAMMD initialization, 8 particles, deterministic CUDA fill,
  synchronization, CPU readback, resource release and shutdown. Also compiles
  the inspected BD and harmonic APIs without constructing or running them.
- `correlator_smoke.cpp`: CPU-only deterministic six-channel test linked to
  the original `../KG/correlator.cpp`, without copying or editing it.
- `AGENTS.md`: permanent scientific requirements and development boundaries.
- `STAGE0_REPORT.md`: source provenance, API evidence, results and limitations.
- `.gitignore`: ignores local `build/` products.

All modifications and build outputs stay here, or temporary artifacts go
outside the repository. Existing UAMMD, KG and KG_Assoc files are read-only.
See the report for the isolated worktree used to preserve pre-existing changes.

## Build and run

Requirements: GNU Make, a C++17 host compiler, CUDA toolkit with its bundled
Thrust/CUB headers, and a compatible NVIDIA GPU for the CUDA runtime test.
No installation, root privileges, or automatic dependency downloads are needed.
CUDA 13's bundled CCCL requires C++17; the KG C++14 flags cannot be reused as-is.

From the repository root:

```sh
# CPU-only; works without nvcc or a GPU:
make -C examples/slip-springs check-correlator

# Ordinary UAMMD precision (float). Use your own CUDA toolkit path:
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86

# Double coordinates/arithmetic; keeps a separate executable:
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double

# Build only, without executing:
make -C examples/slip-springs all CUDA_HOME=/usr/local/cuda

# Remove only explicitly named build products in this directory:
make -C examples/slip-springs clean
```

`CUDA_ARCH=sm_86` matches the validation GPU; choose the architecture of your
own GPU, or omit it to use nvcc's default. Set `NVCC=/path/to/nvcc` instead of
`CUDA_HOME` if preferred. `CXX=/path/to/g++` selects both the CPU compiler and
nvcc's host compiler. `UAMMD_ROOT=/path/to/UAMMD_KG` overrides the default
relative repository root (must contain the KG correlator dependency).
`CPPFLAGS`, `CXXFLAGS`, `NVCCFLAGS`, and `LDLIBS` are also configurable. Preserve
C++17 and `--extended-lambda` when replacing nvcc flags. Run `clean` when
changing toolchain/flags/header root; precision variants have distinct paths.

Executables are `build/single/smoke_test`, `build/double/smoke_test`, and
`build/correlator_smoke`. They write diagnostics only to stdout/stderr. Both
smoke tests return zero only on success. A missing GPU/driver is an unavailable
runtime check, never a pass. `make check` requires successful CPU and GPU tests.
`make double` builds both tests with the double GPU variant; use `check
PRECISION=double` to execute them.

Without `DOUBLE_PRECISION`, UAMMD uses `real=float`. `PRECISION=double` defines
`DOUBLE_PRECISION` for the CUDA translation unit; the independent CPU
Correlator6 always uses double. The existing BD noise implementation remains
float based even in a double build. Growing unwrapped coordinates can lose
small displacements and bond differences in single precision. See the report
before interpreting long-duration or precision comparisons.

## Roadmap

1. **Stage 0 (this directory):** isolation, standalone build, minimal CPU/CUDA
   smoke tests, integrator/precision assessment. Recommendation: a dedicated
   local Euler–Maruyama CUDA kernel in Stage 1 (option B); none implemented now.
2. **Stage 1, after approval:** independent Rouse chains, direct equilibrium
   initialization, overdamped updates, ordinary/double validation against exact
   discrete Rouse dimensions, diffusion and mode times. No stress feature yet.
3. **Stage 2:** GPU chain configurational stress samples and one read-only CPU
   Correlator6 per chain, six observables, correctly density-normalized modulus,
   comparison with exact discrete stress relaxation.
4. **Stage 3:** performance benchmarks and optimization after scientific checks.
5. **Stage 4:** semiflexibility and slip-spring dynamics with separate validation.
