# Stage 0 technical report

Assessment and validation date: 15 October 2026 (Europe/Madrid).
Only infrastructure and feasibility work is implemented. No Rouse integration,
polymer forces/stress, semiflexible interactions, or slip-spring dynamics were
implemented. Stage 1 requires review and approval.

## Provenance and isolation

- Repository: `jorge-ramirez-upm/UAMMD_KG`, remote `origin` over SSH.
- Fetched `origin/KremerGrest` and independently queried remote heads.
- Exact source HEAD: **81fe5de9cd5ded849202eebab7c14e6bd35fb9ae**.
  This matches the supplied last-known commit; remote access succeeded.
- Neither local nor remote `slip-springs` existed at inspection. Created it
  directly from the fetched SHA, without merges, overwrites or force pushes.
- Active development worktree: `/tmp/UAMMD_KG-slip-springs`, outside the original
  checkout `/home/jramirez/UAMMD_KG`. The original checkout had a modified
  `examples/KG/Makefile` and untracked `examples/KG/Stars_TEST/`; these are
  unrelated, preserved, and excluded from this branch by worktree isolation.
  The original checkout stays on `KremerGrest`.
- All seven added files are under `examples/slip-springs/`: `.gitignore`,
  `AGENTS.md`, `Makefile`, `README.md`, `STAGE0_REPORT.md`, `smoke_test.cu`,
  `correlator_smoke.cpp`. No existing tracked file was changed. Git metadata
  necessarily records the new worktree, branch, commit and remote tracking.
- Build products stay in this directory's ignored `build/`; additional
  regression/sanitizer executables and logs are under `/tmp/`. No existing
  application was rebuilt or executed. No PR is requested; no Stage 1 work.

The source SHA is the reproducible comparison base. The final Stage 0 commit
SHA and push outcome are supplied in the handoff (a commit cannot contain its
own SHA). Check the branch with `git rev-parse slip-springs`.

## Overdamped integrator inspection

All paths below refer to the exact source commit above, inspected read-only.

### Existing nonhydrodynamic Brownian API

`src/Integrator/BrownianDynamics.cuh` declares `uammd::BD::Parameters` and
`BD::EulerMaruyama`, `MidPoint`, `AdamsBashforth`, and `Leimkuhler`. The actual
constructors accept `(shared_ptr<ParticleData>, Parameters)` or
`(shared_ptr<ParticleGroup>, Parameters)`. The introductory comment still shows
an older signature; use the declarations. `Integrator::addInteractor` in
`src/Integrator/Integrator.cuh` registers force providers. Each forward step
resets forces and calls registered interactors with force=true on the BD stream.

`BaseBrownianIntegrator` in `src/Integrator/BrownianDynamics.cu` computes
self-mobility `M=1/(6*pi*viscosity*hydrodynamicRadius)` for a fixed radius.
Explicit `hydrodynamicRadius=1` and `viscosity=1/(6*pi)` give M=1 to floating-point
roundoff. Set `temperature=1`, `dt` explicitly, `is2D=false`, and keep the default
zero shear matrix K. The radius here parameterizes **self** drag; it does not
introduce hydrodynamic interactions or excluded volume. Explicit radius avoids
accidentally using an allocated per-particle radius property.

`EulerMaruyama_ns::integrateGPU` reads positions and forces only, applies

    R += dt*(K*R + M*F)
    B = sqrt(2*temperature*M*dt)
    R += make_real3(rng.gf(0,B), rng.gf(0,B).x)

and writes xyz without wrapping. Thus K=0, M=1, T=1 realizes the intended
`r_next=r+F*dt+sqrt(2*dt)*xi`, with no mass or velocity variable. Force and
noise share the same mobility, giving the required fluctuation-dissipation
normalization. `Saru rng(i, stepNum, seed)` seeds separate bead/step streams;
`src/third_party/saruprng.cuh::gf` uses Box–Muller for two Gaussian components,
then the next call supplies the third. The source is designed for independent
pseudorandom bead/component/increment noise, not a common chain noise.
Independence and statistical quality have not been measured in Stage 0.

Important implementation constraints:

- `gf(float,float)` returns `float2` and uses float uniforms/transcendentals in
  **both** precision configurations. B is converted to float for this call.
  Coordinates/force arithmetic can be double, but thermal noise is not fully
  double. Even `Saru::gd` uses `f()` and float functions internally; switching
  its name alone would not solve this issue.
- `BaseBrownianIntegrator::steps` is signed `int`, incremented before each step.
  It cannot safely cover more than INT_MAX steps; RNG stepNum is unsigned int.
  Long production runs need a counter/RNG policy within the new example.
- EM uses current storage index `i` as RNG identity. Particle sorting changes
  that association; cross-precision pathwise comparisons require deliberate
  identity/seeding choices. Statistical comparisons remain the intended goal.
- EM performs one force reset, registered force evaluations and one movement
  kernel per step, with O(beads+bonds) expected work for simple local bonds.
  There is no dense mobility matrix, neighbor list, or interchain force unless
  the caller adds one. Use a single dataset/group for all chains; instantiate
  only intrachain bonds. Per-chain integrators would add avoidable launch costs.
- The BD class owns a stream but does not expose the `getStream()` convenience
  used by KG's NVT class. Future asynchronous diagnostics must account for
  ordering explicitly; a device synchronization is a simple initial boundary.

`MidPoint::forwardTime` evaluates forces twice and uses temporary positions and
additional movement launches. `AdamsBashforth` stores previous forces and uses
1.5 F_n - 0.5 F_previous; it adds storage/copies and is not the requested EM
update. `Leimkuhler` sums current and previous-step noise, giving temporally
correlated increments; it is not independent-increment Euler–Maruyama. All are
overdamped, but their algorithms should not be substituted without validation.

`src/Integrator/BDHI/BDHI_EulerMaruyama.cuh` describes an overdamped integrator
with RPY mobility, square-root mobility noise and optional drift; methods include
Cholesky, Lanczos and spectral schemes. `BDHI/BDHI.cuh` supplies off-diagonal
hydrodynamic mobility. These are unnecessary complexity/overhead and unwanted
coupling for independent free-draining chains; they were not instantiated.

### Bonded forces and unwrapped coordinates

`src/Interactor/BondedForces.cuh` provides
`BondedForces<BondedType::Harmonic,2>`. Its Parameters accept `file` or in-memory
`data`; bond records are `i j k r0`. `Harmonic::compute` applies the bond's Box
to **displacements**, then `detail::harmonicBond` returns force `-k*r_ij` for
r0=0. With k=3 this gives the desired Gaussian force. Per-particle energy is
k*r^2/4, accumulated for both endpoints, hence total bond energy 3*r^2/2.
There is a zero-distance guard. Only list adjacent beads of each chain, omit
end closure, and omit all nonbonded interactors.

`src/utils/Box.cuh`: a default `Box()` has zero lengths and nonperiodic flags;
`setPeriodicity(false,false,false)` also disables minimum-image displacement
changes. Harmonic interactions with a finite periodic Box would change the
model. BD itself has no Box and does not wrap positions. ParticleData stores
`real4` coordinates without mandatory wrapping. Some other components do use
periodicity (KG cell-list/nonbonded paths, periodic Boxes and hydrodynamic
schemes); no claim is made that every UAMMD component accepts unbounded data.
A default nonperiodic bonded Box and no cell-list/sorting path suffice here.

### Recommendation: B, local Euler–Maruyama in Stage 1

Existing `BD::EulerMaruyama` is a viable ordinary-precision overdamped baseline,
and its normalization and unwrapped update match the initial physics. However,
recommend **a dedicated CUDA Euler–Maruyama kernel entirely within this
example in Stage 1**, to support an explicit long-run step/RNG counter policy,
stable bead identities, and a genuinely precision-aware Gaussian generator for
validation. Those limitations cannot be corrected in the existing integrator
under the isolation rule. The initial local implementation can be small:
linear Gaussian nearest-neighbor forces and additive diagonal noise, with old
positions read consistently and new positions written separately. No such
force/update kernel or RNG has been implemented in Stage 0. Expected O(beads)
work and storage; actual overhead/performance must be measured in Stage 3.

This is distinct from `examples/KG/kg_uammd.cu:122`, which chooses
`VerletNVT::GronbechJensen`. `src/Integrator/VerletNVT.cuh` explicitly evolves
`mass*dv/dt = F - friction*mass*v + noise`; its GronbechJensen implementation
reads/writes velocities and uses inverse mass. Friction=1 in that integrator
does not turn finite-step inertial MD into the intended overdamped Rouse model.

## Correlator6: read-only compatibility and limitations

The standalone CPU target includes the original `examples/KG/correlator.h`
through an include path and compiles/links the original
`examples/KG/correlator.cpp` directly, writing its executable only here. It
requires neither CUDA nor a KG application. No dependency was copied or edited.

API (`Correlator6` declaration in correlator.h and definitions at
correlator.cpp:483–723):

1. Construct a concrete `Correlator6`, call `setsize(levels,p,m)` **once**, then
   `initialize()`. The parameterized constructor calls setsize, but still needs
   initialize. Sizing does not initialize the sample buffers.
2. `add(w1,w2,w3,w4,w5,w6)` feeds one evenly spaced observation at level zero.
   Caller must pass Sxy, Sxz, Syz, Sxx-Syy, Sxx-Szz, Syy-Szz in that order.
3. `evaluate()` flattens populated bins; iterate `i < npcorr`. `gett(i)` is a
   lag in original sampling intervals; multiply by sampling stride * dt for
   physical time. `getf(i,j)` with j=0,...,5 returns a channel autocorrelation;
   `getn(i)` returns its raw contribution count. There is no implicit mean
   subtraction or modulus/density normalization, and no cross-channel product.
4. `clear()` resets current run buffers/counts for reuse. `initialize()` also
   resets experiment-average state. `evaluate()` does not consume samples.
   Inherited `toaverage()` only handles the base channel, and inherited
   `save/read(FILE*)` do not persist all six channels; do not use them as a
   six-channel averaging/checkpoint interface. KG_Assoc has a separate derived
   checkpoint implementation, inspected and regression-tested, not adopted here.

Multi-tau layout: defaults are levels=32, p=16 slots per level, m=2 samples per
block. Existing KG uses `(40,16,2)`. Every m samples are **averaged** and forwarded
to the next level; coarse correlations are correlations of block averages,
not exact point-sample correlations. Level k has spacing m^k sample intervals.
Level zero emits lags 0,...,p-1; higher emitted levels start at dmin=p/m to avoid
overlap. Require positive levels, p>=m>=2 and p divisible by m; the API does
not validate these assumptions. Nominal last allocated level has lag up to
(p-1)*m^(levels-1), but this is **not** the actual exported maximum:

- `evaluate()` loops `k < kmax` for coarse levels, while kmax is the deepest
  reached index. The deepest reached level is excluded, including the last
  allocated one when saturated. For `(3,4,2)` the emitted coarse level is 1
  once level 2 is reached, with lags 4 and 6. A two-level correlator never emits
  its level-1 data. Plan an extra level and validate the actual lag grid; do not
  assume advertised capacity equals available output. No fix was made.
- Sample validity uses channel-one stored values `> -1e10`, with -2e10 as the
  unused sentinel. Finite negative stresses are supported in ordinary ranges;
  values <= -1e10 and nonfinite inputs can invalidate results. Validate future
  stress samples before feeding; this API is not robust for arbitrary doubles.

Independent objects own separate state; 16 objects with distinct six-channel
signed inputs passed the standalone test. No shared mutable state was found in
this code path, so many objects are functionally supported, subject to memory
and CPU cost. No synchronization protects a single object: serialize add,
evaluate and clear for that object. Distinct-object parallelism is plausible
from inspection but was not thread-tested. Never copy/move objects by value:
raw owning pointers have shallow compiler-generated copy semantics. Use stable
concrete ownership (e.g. unique_ptr<Correlator6>); the base destructor is not
virtual. Do not repeatedly call setsize, which allocates without releasing old
storage.

Memory is O(levels*p) per chain, CPU sample work is roughly O(6*p) with an
amortized geometric overhead for coarser levels. On this LP64 host the principal
arrays occupy approximately `184*levels*p + 160*levels` bytes, excluding object
and allocator overhead: about 124,160 bytes (121.25 KiB) per `(40,16,2)` object,
about 1.16 GiB for 10,000 chains, plus transfer buffers and allocation overhead.
CPU throughput and GPU-to-host sampling traffic therefore need measurement.

**Confirmed dependency leak:** both Correlator and Correlator6 destructors
delete top-level pointer tables but not their separately allocated rows.
The leaked rows total `104*levels*p` bytes per object on LP64 (66,560 bytes for
40/16/2), surviving object destruction until process exit. AddressSanitizer
confirmed 19,968 bytes in 624 allocations for our 16 objects at (3,4,2).
The functional smoke passes; the leak check fails. Keep a fixed pool alive and
reuse with clear for bounded single-process workloads. Repeated recreation or
large chain counts need a separately reviewed local ownership adapter (protected
rows are accessible to a derived class) or process-lifetime isolation, without
editing Correlator6. Neither workaround is implemented at Stage 0.

KG usage at kg_uammd.cu:168 onward buffers GPU stress samples, feeds the same
six components on the CPU and evaluates at run end. Its final `volume*getf`
conversion applies to KG's volume-normalized total stress. It must not be copied
for per-chain configurational stresses. Future modulus normalization must use
chain density times mean per-chain shear correlation divided by kBT; bead
density requires the corresponding factor 1/(N+1). Normal-difference channels
also need their isotropic weighting derived explicitly.

## Numerical precision

`src/global/defines.h:9–42` defines SINGLE_PRECISION unless DOUBLE_PRECISION is
set. Default real/real2/real3/real4 are float types. `-DDOUBLE_PRECISION` selects
double types; do not also define SINGLE_PRECISION. CUDA >=13 uses double4_16a
through the repository's existing double4_type alias. No new compatibility
changes were needed. All UAMMD translation units within a future executable
must agree on the macro. Correlator6 uses native double regardless of it.

The smoke compiled the BD and harmonic headers/definitions and exercised
System, ParticleData and a minimal kernel in both precisions. This establishes
the used infrastructure and header-level API compatibility. No BD trajectory,
instantiated bonded-force simulation, statistical independence, harmonic energy,
or physical validation is claimed. BD's noise precision caveat remains even
though the double build compiles. Correlator inputs are doubles but cannot
recover precision already lost in GPU coordinates/stress calculations.

The validation GPU supports double arithmetic (runtime smoke passed); future
throughput, register use and doubled coordinate storage may constrain scale.
No double-versus-single performance measurement was performed. Capability and
performance should be checked on each deployment GPU.

For unwrapped Brownian coordinates, single relative roundoff is O(1e-7) times
coordinate magnitude: eventually increments sqrt(2*dt) can fall below local
spacing, and subtracting nearby large bead coordinates loses bond accuracy.
The chain COM diffuses without bound, so duration, chain length and dt matter.
Double delays this loss but does not eliminate it or finite-step bias. Future
checks should monitor coordinate/bond scales and timestep convergence, and
compare precision variants statistically against exact Rouse results. No
recentring or mixed-precision coordinate representation has been implemented.

## Validation results and reproduction

Environment: CUDA toolkit **13.0.88** at `/usr/local/cuda`, GNU g++ **11.4.0**,
NVIDIA driver **580.178.04**, NVIDIA GeForce **RTX 3060 Ti**, capability **8.6**,
8 GiB memory. nvcc was installed but absent from PATH; CUDA_HOME selects it.
Initial C++14 compilation failed because CUDA 13 CCCL requires C++17; the local
Makefile now uses C++17. This required no upstream modification. Existing
correlator.cpp emits ignored-fscanf-return-value warnings; they were not edited
or globally suppressed.

Executed from the isolated repository root:

```sh
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
```

Both commands exited **0**. GPU tests passed device query, UAMMD initialization,
8-particle GPU allocation, deterministic CUDA kernel, launch/error checks,
explicit synchronization, component-wise CPU readback, destruction before
System::finish and normal termination. Reported real sizes were 32 and 64 bits.
The headers for BD and harmonic interactions compile in both configurations;
no integrator object is created or advanced.

The standalone CPU test passed in both check invocations, linking the original
KG implementation. It compares all six channels and raw counts to independently
computed offline block averages and direct autocorrelation sums, using 16
independent objects, 32 signed/nonconstant samples per object, then clear/reuse
with signed constant data. Both fine and exported coarse levels and repeated
evaluation are checked. Checks throw on failure and are active under NDEBUG.

Existing read-only regressions were separately compiled to /tmp and executed:

```sh
g++ -std=c++14 -O2 examples/KG_Assoc/kg_correlator6_counts_test.cpp examples/KG/correlator.cpp -o /tmp/slip-springs-counts-test
/tmp/slip-springs-counts-test
g++ -std=c++14 -O2 examples/KG_Assoc/kg_assoc_correlator_checkpoint_test.cpp examples/KG/correlator.cpp -o /tmp/slip-springs-checkpoint-test
/tmp/slip-springs-checkpoint-test
```

Both exited **0**. This is header/link/runtime compatibility evidence, not a
validation of future polymer stress or modulus calculations.

The additional diagnostic below exited **1**, reporting the confirmed upstream
row leak (no claim that a leak-free sanitizer check passed):

```sh
g++ -std=c++17 -O1 -g -fsanitize=address -Iexamples/KG examples/slip-springs/correlator_smoke.cpp examples/KG/correlator.cpp -o /tmp/slip-springs-correlator-asan
/tmp/slip-springs-correlator-asan
```

Build/run logs: `/tmp/slip-springs-single.log`,
`/tmp/slip-springs-double.log`, `/tmp/slip-springs-asan.log`; temporary evidence
is not part of the committed source. The Makefile clean target deletes only its
five named generated files and leaves directories alone. Cleanup and CPU-only
rebuild were checked separately.

Before committing, isolation was checked against the source with the following
program, including **all untracked paths, even ignored build artifacts**:

```sh
python3 - <<'PY'
import subprocess
base = '81fe5de9cd5ded849202eebab7c14e6bd35fb9ae'
def paths(*args):
    return [p for p in subprocess.check_output(['git', *args]).split(b'\0') if p]
changed = paths('diff', '--no-renames', '--name-only', '-z', base)
untracked = paths('ls-files', '--others', '-z')
bad = [p for p in changed + untracked if not p.startswith(b'examples/slip-springs/')]
if bad:
    raise SystemExit('ISOLATION VIOLATION: ' + repr(bad))
assert subprocess.check_output(['git', 'branch', '--show-current']).strip() == b'slip-springs'
assert subprocess.check_output(['git', 'merge-base', base, 'HEAD']).strip().decode() == base
print('PASS: branch ancestry and all changed/untracked paths confined to examples/slip-springs/')
PY
```

The final source diff contains seven new project files and no modifications or
deletions to existing paths. The original checkout's unrelated changes remain
in place. Clean/CPU-only validation and the final path check precede commit;
commit and normal branch push are recorded in the handoff.

## Remaining risks and Stage 1 scope

Infrastructure and available-environment validation are complete. Physical
simulation validation remains intentionally unperformed. Resolve the local
step/RNG design in Stage 1; implement direct equilibrium conformations and an
ordinary/double overdamped update entirely here, test free ends and independent
chains against exact discrete Rouse dimensions, D_CM and mode relaxation, with
timestep convergence and uncertainty estimates. No stress implementation or
performance campaign should enter that stage. Stage 2 must address Correlator6
memory lifecycle, coarse-lag export and block-averaging effects before a large
per-chain deployment. Do not change existing integrators/correlators or start
Stage 1 until Stage 0 is reviewed and approved.
