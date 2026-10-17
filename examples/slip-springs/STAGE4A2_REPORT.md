# Stage 4A.2 — GPU semiflexible backbone dynamics

Implementation recorded 16 October 2026; scientific acceptance recorded
17 October 2026 (Europe/Madrid).

**STAGE 4A.2 ACCEPTED — GPU SEMIFLEXIBLE BACKBONE SCIENTIFIC VALIDATION PASSED**

The independent user-executed Linux-host campaign completed 204 experiments
under the frozen plan with zero automated statistical failures. Acceptance
applies to the tested configurations and numerical tolerances, not arbitrary
stiffness, timestep or chain length. No Stage 4A.3, stress-relaxation extensions,
slip-springs, excluded volume or hydrodynamics are implemented. The archival
closure below distinguishes inspected evidence from user-supplied provenance.

## Provenance and isolation

Repository `jorge-ramirez-upm/UAMMD_KG`, branch `slip-springs`, worktree
`/tmp/UAMMD_KG-slip-springs`. Fetched `origin/slip-springs` before editing;
local HEAD and fetched remote both matched the required starting SHA
`58ea94a5fae40f2e8b6adbce815460487b8f3924`. The worktree was clean.

All changes are local to `examples/slip-springs/`. New files:
`semiflexible.cuh`, `semiflexible.cu`, `tests/test_semiflexible_gpu.py`,
`tests/semiflexible_host.py`, `tests/test_semiflexible_host.py`,
`STAGE4A2_VALIDATION_PLAN.md` and this report. Existing changes are limited to
README, appended AGENTS rules and appended Makefile targets. Existing Makefile
content remains an identical prefix; default `all`, `check`, Rouse builds and
clean behavior remain unchanged. Use explicit `semiflexible`,
`check-semiflexible`, `clean-semiflexible` targets.

UAMMD, KG, KG_Assoc, Rouse source/RNG/CLI/tests/correlator and the authoritative
Stage 4A.1 Python reference are unchanged. The final path audit compares against
both this starting commit and Stage 0 source
`81fe5de9cd5ded849202eebab7c14e6bd35fb9ae`, including tracked, untracked and
ignored paths. Generated products/logs stay under the local ignored `build/`
and caches, or temporary directories outside the repository.

## Model, forces and architecture

Exactly the Stage 4A.1 open-chain Hamiltonian is implemented. There are N bonds,
N+1 beads, unwrapped positions and independent chains. `b0[i]`, `kb[i]` index
bonds; `kappa[i]` indexes beads and has N+1 entries with mandatory zero endpoints.
The CLI supports homogeneous scalars and a tested parameter-file pathway for
independent heterogeneous arrays, shared across chains. Uniform per-bead
friction zeta and thermal energy kBT are independently configurable and positive.
No Gaussian Rouse prediction is applied to finite-rest-length dynamics.

Require finite kb>0,b0>=0,kappa>=0; reject unrepresentable parameter casts and
update scales. Strictly positive kb preserves the normalizable radial equilibrium
reference. Both float and double builds use their respective UAMMD `real` for
forces, positions, Gaussian noise and integration. Host initialization and
observation arithmetic use double. Effective parameter arrays, mobility step
and noise scale are saved, so nominal input and precision rounding are explicit.

For stretching, g_i=kb[i](|q_i|-b0[i])*q_i/|q_i| adds +g_i to the left bead
and -g_i to the right bead. At q=0,b0=0 the smooth zero gradient is used.
For angle i, u=q_(i-1)/|q_(i-1)|,v=q_i/|q_i|,c=u dot v:

    A=-kappa[i]*(v-c*u)/|q_(i-1)|
    B=-kappa[i]*(u-c*v)/|q_i|.

The contributions on i-1,i,i+1 are A,B-A,-B, as derived independently in
[Stage 4A.1](STAGE4A1_REPORT.md). Stretch energy is split equally over its two
beads; bending energy is evaluated as kappa*|u-v|^2/2 and split into thirds.
Thus the force-only interface's per-bead energies sum to the Hamiltonian.
No acos, sine denominator, force clamp or angular regularization is introduced.

The implementation uses local gather kernels:
each bead thread reads its one/two bonds and up to three incident angles and
writes only its own force slot. Stretch overwrites the force/energy buffer;
bend adds on the same CUDA stream. There is no non-atomic scatter, shared force
writer, separate-stream race or in-place neighbor update. The UAMMD assessment
in Stage 4A.1 still applies: the stock harmonic potential matches nondegenerate
forces, but its zero-length policy differs; stock Angular lacks energy and has
a different coefficient convention. Neither is silently substituted or changed.

**Flexible fast path:** when all coefficients are zero, the device angular
vector remains empty with zero allocation capacity, no angular topology is
constructed, and the host never invokes the bending kernel. Only stretch and
update execute. In heterogeneous cases the bead-indexed parameter buffer is
uploaded once, and zero entries are skipped before reading angular bonds or
normalizing. Actual angular-vector capacity and bending launch counts are
exported and tested. Tangent measurements, requested even for flexible chains,
are separate CPU observation work at the unchanged sampling schedule; they do
not add angular work to the force/integration path.

## Equilibrium initialization and RNG

The CPU initializer samples the exact radial and conditional orientation laws,
then uploads the rounded coordinates. It is an independent C++ implementation
of the Stage 4A.1 construction, not Gaussian finite-rest-length initialization
or a long Monte Carlo equilibration. Initialization has O(C*N) storage and work
in expectation; per-bond rejection has a 10000-trial fail-fast bound.

For sigma=sqrt(kBT/kb),a=b0/sigma,t=r/sigma, use a unit-width Gaussian proposal
centered at m=(a+sqrt(a^2+8))/2. Accept t>0 with probability
exp(2*[log(t/m)-(t-m)/m]). The mode identity m-a=2/m and log(z)<=z-1 give the
Gaussian envelope; the resulting target is t^2*exp[-(t-a)^2/2], including the
3D Jacobian. Compute the logarithm with log1p. The first direction is isotropic.
For x=kappa/kBT>0 draw uniform h and azimuth, and use
c=1+log[h+(1-h)*exp(-2*x)]/x. Small x uses log1p/expm1; exponentially negligible
tails are bounded at x=350 for numerical safety. Zero stiffness draws a new
independent isotropic direction without an angular frame. This implements the
conditional Kratky–Porod law, hence the isolated open-chain equilibrium measure.
Only roundoff excursions of a sampled cosine are clipped, not force geometry.

CPU generation uses per-chain mt19937_64 engines seeded by the low/high halves
of the unsigned 64-bit seed, chain index and a Stage 4A.2 initialization tag.
Appending chains leaves previous initial chains unchanged. Standard-library
normal sampling is reproducible in the same implementation/build environment;
no cross-library/platform bitwise guarantee is claimed. It consumes no dynamics
Philox counters. Dynamics uses stable flat bead IDs in Philox domain **3**, with
eight reserved 32-bit draws per bead/step, bounded at floor(UINT64_MAX/8) steps.
Rouse domains 0/1/2 are unchanged. Float uses normal4; double uses two
normal2_double calls. Each update reads the same old-position buffer:

    next_i = old_i + real(dt/zeta)*F_i
                    + real(sqrt(2*kBT*dt/zeta))*xi_i.

Old/new buffers swap only after diagnostics succeed. Independent-chain replay
and identical-seed repeatability are tested separately in both precisions.

## Diagnostics and numerical stability

Before each update, force evaluation rejects nonfinite coordinates, undefined
stretch forces at q=0,b0>0, collapsed active bending bonds and nonfinite energy
or force. It does not reject a smooth b0=0 collapsed bond incident only to
inactive angles. The proposal kernel checks nonfinite new coordinates; the host
aborts before swapping/advancing. The final state is force-validated even when
its step is not a sample multiple. No unstable step is skipped or accepted
with a modified potential.

Synchronous diagnostic readback identifies the first failing step and chooses
the lowest bead/reason key deterministically among failures at that step.
`failure.json` records seed, step/time, dt, temperature, friction, precision,
chain/bead and force/proposal stage. `parameters.txt` is saved before the first
force validation. Full old coordinates, and failed proposals when relevant,
are retained. Error codes are documented in README. Invalid text/options/scales
also return nonzero with a diagnostic. Successful runs cannot continue past a
reported GPU numerical failure. A smooth collapsed bond's *tangent observable*
is undefined and written as nan; this is not a regularized interaction.

Bending force scales as kappa/l and curvature as kappa/l^2 (mixed derivatives
also involve 1/(l_a*l_b)). Stretch longitudinal curvature is kb and transverse
curvature is kb*(1-b0/l), potentially large and negative near collapse. A useful
local stiffness indicator is (dt/zeta)*max(kb,kappa/l_min^2), but it is not a
universal stability bound and omits additional b0/l factors. Finite dt must
resolve these scales and be checked by refinement; no positive global dt is
guaranteed for the singular orientation potential over all possible thermal
configurations. Minimum sampled lengths are recorded; unsampled minima may be
smaller. Coordinate cancellation in long single-precision runs is another host
validation concern. There is no unapproved cutoff, adaptive step or implicit
integrator. The accepted frozen host campaign below covers specified test cases;
it does not supply a universal timestep guarantee.

## Observations, performance and memory

At step0 and exact sample multiples, full coordinates are copied to host and
reduced in double. Per-chain scalars include mean r,r^2,Re^2,Rg^2, initial-origin
COM MSD, initial-origin monomer MSD, minimum bond and tangent correlations at
separations 1..min(4,N-1). Free-chain COM has the independent exact prediction
6*kBT*t/((N+1)*zeta), because internal forces sum to zero. Monomer MSD has an
exact controlled Gaussian-limit test; finite-rest-length dynamics is not given
a Rouse relaxation prediction.

Per-chain/per-bond moments and fixed radial histogram counts accumulate only
over sampled frames in the final half. They retain independent chain clusters
for uncertainty estimates. Initial individual lengths and initial/final
coordinate snapshots are saved, but complete coordinate trajectories are not.
The histogram has 32 uniform finite bins up to max_i(b0_i+8*sigma_i) and one
overflow bin. All lengths, including outliers, contribute to moments/counts.
The final partial sampling interval is integrated/validated but not sampled.

Workspace is O(C*N), independent of steps; a conservative 2 GiB estimate is
checked before coordinate/workspace allocation, excluding the CUDA context.
Known device allocations and the CPU workspace budget estimate are saved.
Output scalars grow as O(C*frames); histogram output is O(C*N*33). The long
campaign requires substantial disk space. This is an initial reference-oriented
implementation, not a production-server performance optimization.

Initialization includes host sampling, CUDA setup/upload, initial validation,
workspace and initial files; parameter parsing/output-directory setup precede
that timer. GPU integration event intervals encompass force/update kernels,
diagnostic D2H and host launch/sync gaps. There are two synchronous diagnostic
readbacks per step. Observation D2H/CPU reductions/formatting and recurrent
writes are separately measured. Overall production includes the initial
observation and final force validation, excludes initialization and final output.
Final snapshots/statistics have their own timer. Metadata/terminal telemetry
is outside production/final-output timers. Force/diagnostic wall time is a
subset of integration timing, not an additional cost to sum. Zero-step rates
are null; denominator is beads*production_steps. Sample frequency is unchanged.

## Executed bounded verification

Host: RTX 3060 Ti (sm_86), CUDA 13.0.88, g++ 11.4.0, Python 3.10.12,
NumPy 2.2.4. Both new CUDA precisions were compiled and executed.

* Each `check-semiflexible` invocation passes **7 GPU test groups, 2 host-tool
  tests and the unchanged 12 Stage 4A.1 CPU tests**. GPU checks cover independent
  CPU forces/energy, straight/bent/nearly collinear geometries, rotations,
  translations, torque/net force, endpoints/N=1, mixed coefficients, skipped
  collapsed inactive angles, diagnosed invalid geometry, CLI/counter guards,
  exact replay, chain isolation, noise and observables.
* GPU force relative tolerance is 3e-5 in float and 2e-12 in double, with absolute
  floors scaled by max(1,kb,kappa): 3e-6 and 3e-14 respectively. Near collinearity
  can have near-zero true components and large coefficient-scaled cancellation,
  so relative-only tests would be inappropriate. Energy and force/torque symmetry
  thresholds use the same precision/scale rationale; exact code is in the tests.
* Zero-bending tests assert zero actual device angular capacity and zero bending
  launches, not just zero angular force. The kernel's inactive-angle branch is
  exercised by a collapsed bond that would otherwise fail normalization.
* Fixed-seed runs use at most 4096 short chains and 40 updates per case. Moment
  tests use six independent-chain SE plus 1e-5 numerical floor. Initial radial
  and conditional cosine empirical CDF tests include kappa=1e-9 and 1000 and
  use 0.065 at C=2048 (per-test DKW
  bound <6.2e-8), with independent uniform-grid radial integration.
* Noise variance/covariance is checked in a prescribed zero-force configuration
  of the smooth b0=0,kappa=0 harmonic model, including friction scaling. Short
  finite-rest-length trajectories check radial/orientational moments, Re^2,Rg^2
  and COM. A separate exact Gaussian EM mode calculation verifies the finite-dt
  second moments and timestep refinement at dt=0.04,0.02,0.01 over physical 0.4.
  This controlled limit is explicitly distinguished from the target model.
* Host-tool tests generate the entire command manifest **without executing it**,
  exercise streaming analysis on short finite-rest-length and Gaussian outputs,
  and deliberately corrupt radial data to check rejection. The analyzer checks
  exact controlled EM monomer MSD/COM at every recorded Gaussian frame, clustered
  equilibrium moments, CDFs, replicas and timestep trends. Unresolved coarse
  bias is explicitly recorded, not interpreted as observed convergence order.
* Original bounded `make check` passes in **both precisions**, including GPU
  Rouse force/stress/RNG/pipeline checks, correlator smoke, 4 theory + 2 streaming
  theory + 4 stress + 3 CLI tests, six bounded streaming cases and 14 guards.
  CPU worker ASan/UBSan/LSan checks pass. Separate `check-lifetime` passes
  200 ownership cycles. Existing read-only KG fscanf compilation warnings remain.
* CUDA memcheck: **0 errors**; racecheck: **0 errors/0 warnings**, on a bounded
  double-precision N=4,C=3,3-step active-bending run. The system
  `/usr/bin/compute-sanitizer` first failed to locate its injection library;
  using `/usr/local/cuda/bin/compute-sanitizer` resolved the tool-path problem.
  These tiny sanitizer examples do not establish campaign-wide correctness.
* Both README short examples (N=8,C=64,dt=0.0001,20 steps,sample5,seed42021)
  were executed successfully. The moderate example and full host campaign were
  **not run**. Python compilation, diff whitespace and path isolation checks pass.

## Frozen scientific acceptance plan and implementation-handoff limitations

`STAGE4A2_VALIDATION_PLAN.md` is frozen before long experiments. SHA256:
`fd57af47349304a9f71bae89ff6c23a4fae844894e2b12658d25b1f009cb60c2`.
The generator supplies **204 user-host runs**: both precisions, seeds
420201/420202/420203, N=1/8/32, kappa=0/2/10 and a heterogeneous case, three
refined timesteps, plus controlled Gaussian dynamics and one-step noise tests.
The plan fixes durations, observation cadence, clustered uncertainties,
CDF/moment/diffusion/refinement gates and memory/performance evidence in advance.
No full scientific acceptance is claimed from bounded checks.

Remaining limitations are explicit CPU initialization/observation costs,
per-step diagnostic synchronization, uniform friction (heterogeneous force
parameters are supported), no restart/checkpointing, and no universal timestep
bound near singular geometries. At the 16 October implementation handoff, the full host campaign and host report
were outstanding; the 17 October closure below records their acceptance. Separate
production-server memory/performance measurements remain outstanding. Stage
4A.3 and slip-spring physics remain unauthorized.

The following commands were supplied at implementation handoff for independent
replication. The campaign has now completed; no rerun was performed for archival:

```sh
make -C examples/slip-springs check-semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check-semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
SEMI_HOST=$(mktemp -d /tmp/semiflexible-host.XXXXXX)
python3 examples/slip-springs/tests/semiflexible_host.py --output "$SEMI_HOST/campaign"
# Review commands first. The following two commands are user-host work only:
bash "$SEMI_HOST/campaign/commands.sh"
python3 examples/slip-springs/tests/semiflexible_host.py --analyze "$SEMI_HOST/campaign"
```


## Final scientific acceptance and archival — 17 October 2026

**STAGE 4A.2 ACCEPTED — GPU SEMIFLEXIBLE BACKBONE SCIENTIFIC VALIDATION PASSED**

The user reports successful independent Linux-host execution and authorizes
scientific acceptance. Codex inspected accessible original records and archived
them; it did not independently execute/authenticate the experiments or rerun
large statistical analyses. This is a documentation/evidence-only closure.

### Campaign and statistical interpretation

The original directory is `/tmp/semiflexible-host.CR6bWs/campaign/`. Its original
manifest contains **204 experiments**, 102 per precision and 68 per seed across
420201,420202,420203. Coverage includes homogeneous N=1,8,32 and kappa=0,2,10;
heterogeneous stretching/bending; three timesteps; exact-equilibrium radial and
conditional angular initialization; bond-length/angular statistics; Re^2,Rg^2;
COM diffusion; controlled Gaussian-limit monomer MSD; noise and timestep checks.
The nonlinear finite-rest-length model is not a Gaussian Rouse chain. The
Gaussian limit is a separate explicitly controlled test case.

The unchanged original analysis contains 198 non-noise summaries, six noise
experiments covered by its gates, an empty failure list, and the status:

    statistical gates passed; manual host evidence still required failures: 0

All automated statistical gates passed. The JSON preserves its literal status
`statistical gates passed; manual host evidence still required` and the empty
`failures` list; it is not rewritten to change that provenance. The separate
manual host evidence and the user's acceptance instruction complete this
closure. The original plan and all validation thresholds remain unchanged;
plan SHA-256 is
`fd57af47349304a9f71bae89ff6c23a4fae844894e2b12658d25b1f009cb60c2`.

**Coarse-timestep bias was not statistically resolved:** all **456/456**
reported timestep comparisons have `coarse_bias_resolved=false`. Agreement
within the stated uncertainty/tolerances is supported; an experimentally
measured Euler–Maruyama convergence order is not. No order is inferred from
these unresolved comparisons.

### Permanent archive and integrity

Original compact records are copied byte-for-byte to
[validation/stage4a2-acceptance/](validation/stage4a2-acceptance/). The archive
contains 230 original files: campaign manifest/analysis/commands, 12 small
parameter inputs, **all 204 metadata files**, and 11 memory-experiment files.
The original supplied review/memory tar members match their accessible loose
files. Redundant tar containers, large per-chain/trajectory observations and
executables are not committed. The originals are left untouched.

[ORIGINAL_FILES.json](validation/stage4a2-acceptance/ORIGINAL_FILES.json) lists
all original source paths, archived paths, sizes and hashes.
[BENDING_METADATA_INDEX.json](validation/stage4a2-acceptance/BENDING_METADATA_INDEX.json)
is a derived index. Both indexes are labeled as derived rather than additional
independent measurements. [SHA256SUMS](validation/stage4a2-acceptance/SHA256SUMS)
covers all archive payloads. Source/copy SHA-256 comparisons and the complete
archive checksum check passed. Checksums identify preserved bytes, not the
identity of the experimenter or original executable build.

The worktree initially contained the prior user-requested ROADMAP.md and its
AGENTS link, so it was **not initially clean**. Only those known documentation
changes were present; they were preserved, updated for this closure and included.
The closure starting HEAD and live remote were verified as
`cde9d092a29ac3f6fc4f9729992948dd8f09d547`. No simulator, test, RNG, numerical
method, validation plan/threshold or build file was changed.

### Separate memory-stability experiment

Original directory: `/tmp/semiflexible-memory.wLFbVS/`. Both single-precision
runs use N=8,2048 chains,kappa=10,dt=0.00005,sample400,seed420201, with the same
recorded parameters. Original time reports, GPU-monitor readings, execution
logs, build-command output and both run metadata/parameter files were accessible
and are archived under `memory/` with verified hashes.

| Measurement | 20,000 steps | 400,000 steps |
| --- | ---: | ---: |
| Physical production time | 1 | 20 |
| Peak CPU RSS (KiB) | 108,556 | 108,392 |
| Observed GPU run plateau (MiB) | 145 | 145 |
| GPU integration (ns/bead/step) | 1.934 | 1.944 |
| Overall production (ns/bead/step) | 2.926 | 2.939 |

The underlying log values are 1.934223/1.944431 for GPU integration and
2.925933/2.939158 overall. GPU memory remained at a monitored 145 MiB plateau
during the longer experiment; the monitoring files also retain startup readings
of 1/2 MiB. `nvidia-smi` reports **whole-device memory**, not process-specific
allocations. The small RSS difference is not meaningful evidence of growth or
shrinkage. These measurements support bounded observed memory for this duration
comparison; they are not proof for every workload or a production-server claim.
Timer scopes retain diagnostic synchronization costs and separate observation,
recurrent output and final-output costs, as recorded in the original metadata.

### Hardware, software and build provenance

| Item | Recorded provenance |
| --- | --- |
| User-reported campaign Git SHA | `cde9d092a29ac3f6fc4f9729992948dd8f09d547` |
| GPU | NVIDIA GeForce RTX 3060 Ti; corroborated in run metadata |
| GPU memory | 8192 MiB, user-supplied host provenance |
| NVIDIA driver | 580.178.04, user-supplied host provenance |
| NumPy | 2.2.4, user-supplied host provenance |
| System nvcc | CUDA 11.5.119, user-supplied host provenance |
| Historical development toolkit | CUDA 13.0.88, recorded in the implementation section |
| Original campaign executable compiler toolkit | **Not independently established** |

The archived user-host build-command output says `Nothing to be done for
'semiflexible'`; it does not prove which CUDA toolkit originally compiled the
executables. Do not assign system CUDA 11.5.119 or development CUDA 13.0.88 to
the campaign binaries without build evidence. No original campaign commit file,
executable hashes, hardware/compiler terminal transcript or campaign-wide stdout
log was present in the supplied evidence directories. The stated provenance is
retained as user-reported where not corroborated; no missing record or checksum
is fabricated. Inspection verifies the result records, not their executable
source/compiler identity.

### Structural zero-bending regression and remaining limits

All 204 accessible original metadata files were inspected. **114** have zero
active angles and report zero angular GPU capacity (`bending_device_bytes=0`)
and zero bending-kernel launches. The other **90** report active angles, nonzero
angular capacity and nonzero launches. For example, archived single N32,kappa0
has 0/0/0 bytes/angles/launches; single N32,kappa10 has 132 bytes,31 angles,
1,000,002 launches; double N32,kappa10 has 264 bytes,31 angles,1,000,002 launches.
This structural optimization is a permanent scientific/computational regression
condition; zero resulting bending force alone is insufficient evidence.

Acceptance is limited to the tested configurations and frozen tolerances.
There is no universal timestep guarantee near singular configurations and no
measured convergence order from this campaign. Synchronous diagnostic transfers
and CPU observations remain performance costs. No production-server performance
or superiority over equivalent UAMMD infrastructure is established. The reuse
review in ROADMAP.md remains future work, requiring separate authorization and
validation. Existing `rouse` is unchanged. No slip-springs or stress-relaxation
extensions are implemented; Stage 4A.3 is neither implemented nor authorized.

Verify the permanent archive without rerunning simulations:

```sh
(cd examples/slip-springs/validation/stage4a2-acceptance && sha256sum -c SHA256SUMS)
```
