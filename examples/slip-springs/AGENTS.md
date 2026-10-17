# Scientific and repository rules

## Isolation and stage gate

ALL project modifications must remain under `examples/slip-springs/`. Never
modify, delete, reformat, or move UAMMD core files, KG, KG_Assoc, other examples,
or repository-wide build/configuration/documentation files. Existing code may
be inspected, included, and linked only as a read-only dependency. Document any
obstacle that would require an outside change and propose a local alternative.
Do not copy entire KG modules. Preserve unrelated work and branch history.

Work on `slip-springs`, never on `KremerGrest`. Keep generated outputs and
compiler products here or outside the repository. Before committing, compare
against the recorded source SHA in STAGE0_REPORT.md and programmatically check
tracked, untracked, and ignored generated paths. Stop and report any outside
change; never silently remove it. Use an isolated worktree when needed.

Stage 1 is implemented and scientifically validated: independent GPU Rouse chains.
Stage 2A is implemented: per-chain configurational stress and direct-lag validation.
**STAGE 2B COMPLETE — STREAMING STRESS RELAXATION VALIDATED**
Evidence: Stage 1/2A regressions; 54-simulation matrix; N32 terminal 504/504;
Stage 2B.1 acceptance; million-step memory 728/728; N100 terminal 686/686.
See STAGE2B_N100_TERMINAL_RESULTS.md for closure and the permanent N100 archive.
This validates the independent Rouse reference, not a slip-spring model.
Slip-spring physics is neither implemented nor scientifically validated.
Stage 2B.1 is accepted on the development host; see STAGE2B1_HOST_RESULTS.md.
Stages 3–4 and new physics are not authorized.
The project stages are:
1. Independent Rouse chains on the GPU.
2. Configurational stress correlations and modulus using Correlator6.
3. Benchmarking and optimization.
4. Semiflexibility and slip-spring dynamics.

## Permanent initial physical model

This is a coarse-grained Gaussian-chain model, distinct from Kremer–Grest MD.
A chain has **N springs and N+1 beads**, with bead indices 0 through N, free
ends, statistical bond length b=1, thermal energy kBT=1, and friction zeta=1
**per bead**. There is no excluded volume, no hydrodynamic interaction, and no
interaction between chains. Coordinates remain unwrapped throughout.

With q_i = r_(i+1) - r_i,

    U = (3/2) sum_(i=0)^(N-1) |q_i|^2.
    dr_i = F_i dt + sqrt(2) dW_i.
    tau_0 = zeta b^2/(kBT) = 1.
    tau_s = zeta b^2/(3 kBT) = 1/3.

Use truly overdamped dynamics, independent Gaussian noise for each bead,
Cartesian component, and time increment, and correct fluctuation-dissipation
normalization. NVT Langevin dynamics with mass and velocity is a different
model. Do not introduce new physics by changing core or existing KG code.

Draw initial conformations directly from equilibrium Gaussian statistics:
independent bond components with mean zero and variance 1/3, accumulated along
the chain. Dynamic equilibration alone is insufficient initialization. Choose
chain translations separately without adding forces or interchain interactions.

## Stress and validation

Use chain configurational stress

    S_ab^(c) = 3 sum_(i=0)^(N-1) q_ia^(c) q_ib^(c).

The six Correlator6 inputs per independent chain are, in order:
S_xy, S_xz, S_yz, S_xx-S_yy, S_xx-S_zz, S_yy-S_zz.
Stage 2A uses direct-lag CPU analysis of GPU per-chain stress samples.
Stage 2B adds Correlator6 under the current authorization. Reuse
`../KG/correlator.h` and `../KG/correlator.cpp` unchanged; do not copy them.
Read the limitations in STAGE0_REPORT.md before allocating many objects.

Normalize the relaxation modulus consistently with the chain or bead density.
If C chains occupy volume V, chain density is C/V and bead density is
C(N+1)/V. Averaging per-chain correlations must not introduce an extra factor
of C or 1/C. Distinguish chain stress from volume-normalized total stress;
never import KG's volume prefactors without deriving the normalization.

Validate future GPU results against exact **discrete** Rouse predictions for
equilibrium dimensions, center-of-mass diffusion, relaxation times, and stress
relaxation. With M=N+1: <Re^2>=N, <Rg^2>=(M^2-1)/(6M), D_CM=1/M,
and mode decay rates lambda_p=12 sin^2(p*pi/(2M)), p=1,...,M-1.
Stress mode contributions decay at twice these rates. Separate finite-step
Euler–Maruyama bias from statistical uncertainty and floating-point effects.
Check free ends, multiple chains, and the absence of interchain forces.

Start with UAMMD ordinary precision (`real=float`); maintain a documented
`DOUBLE_PRECISION` build for statistical validation. Do not claim double noise
or full double arithmetic solely because coordinates are double. Do not add a
mixed-precision coordinate representation without an approved later scope.
Report actual compilation and execution separately; unexecuted tests never pass.

## Stage 1 implementation conventions

The local `rouse.cuh` Euler–Maruyama update uses immutable logical bead IDs,
Philox4x32-10 and two old/new buffers. Never turn it into an in-place neighbor
update. Fixed chain-contiguous layout supplies topology; do not reorder bead
storage without remapping topology and preserving IDs. No sorting is performed.
Reserve eight 32-bit RNG draws per bead per unsigned 64-bit step; reject runs
whose equilibration+production count exceeds floor(UINT64_MAX/8). Keep domain
separation for bond initialization and independent chain translations. Use
curand_normal4 for float and two curand_normal2_double calls for double.

`tests/VALIDATION_PLAN.md` sets acceptance before stochastic execution. Compare
nonstationary finite-step mode covariance as well as continuous-time theory.
Cluster uncertainties by independent chain, never count overlapping origins
as independent observations. The Stage 1 Python analysis remains available; `stress.py` performs Stage 2A
direct-lag stress analysis, with no multi-tau correlator. Preserve `STAGE0_REPORT.md` as historical evidence.
Refuse to overwrite run directories; keep outputs inside this project or outside
the repository. `make clean` must not delete scientific run data.

## Permanent performance and example requirements

Every simulation must print and save measured performance data: chains, springs
and beads per chain, total beads, production steps/time, integration seconds,
ns/bead/step and bead-updates/s, production wall time and overall ns/bead/step,
sampling/recurrent transfer overhead, recurrent output and final data-output time.
Use actual timers. Define the rate denominator as total_beads*production_steps,
excluding optional equilibration. Zero production steps have null/N/A costs.
Production timing excludes initialization/equilibration and final data flushing.
State whether GPU timing includes launch gaps, synchronization and sampling.
Keep timer scope/version and units explicit in metadata; never change physics
to improve reported efficiency. Metadata/terminal telemetry overhead is outside
the production/final-data timers and must be disclosed.

Every future stage must update README's **Running the current simulator**
section with tested, copy-and-paste build commands for both precisions, a short
example and a moderately long example, validation commands and output locations.
Specify N, chains, dt, production steps, sample stride and seed for each run.
Run short examples before claiming they work. End task reports with the most
useful current commands, not just links. Preserve refusal to overwrite outputs.

Stage 2A computes six raw tensor components with double GPU reductions of stored
unwrapped bonds, without a volume factor or bead coordinate transfer. Keep
xy,xz,yz and xx-yy,xx-zz,yy-zz correlations separate. Stage 2A normalized normal-difference PRODUCTS
carry a factor1/4; Stage 2B correlator inputs/products remain raw. Never treat correlated channels or overlapping origins as
independent statistical units. Square the exact EM covariance at each origin
BEFORE averaging over origins. Preserve raw per-chain samples/contributions.
`tests/STAGE2A_VALIDATION_PLAN.md` fixes the Stage 2A scientific gates.

## Stage 2B workflow and streaming conventions

The current user authorization supersedes the historical stage gate above:
Stage 2B is complete on the recorded user-executed host evidence; Stage 2B.1
acceptance remains development-host-specific. See STAGE2B1_HOST_RESULTS.md and
STAGE2B_N100_TERMINAL_RESULTS.md. Later stages remain unauthorized.
Never declare scientific acceptance from smoke tests or generalize host-specific
performance to other hardware. Production servers require separate benchmarking.

Do not run long tests, statistical campaigns, long relaxation runs, production
simulations or broad benchmarks in Codex. Supply exact executable commands for
the dedicated Linux GPU host instead. Short unit, sanitizer, bounded pipeline
and example checks are allowed. Preserve all existing tests and their fixed
scientific acceptance limits. Avoid complexity/optimization without profiling.
All repository modifications remain here; KG/UAMMD remain read-only.

Streaming is explicit (`--output-mode stream`); historical CSV behavior remains
the default. Streaming samples step 0 after equilibration and exact multiples of
`--sample`; it integrates but does not correlate a shorter final interval.
Batches count observation frames, not integration steps. Never allocate a full
stress history. CPU ownership is exclusive: main thread in sync mode; in async mode each
persistent worker owns one fixed contiguous chain range. Worker 0 is the existing
consumer and coordinates N−1 helpers, without a dispatcher. Join/drain before evaluation and release CUDA resources
only after pending producers/transfers/consumers have completed. Keep backpressure
and exception propagation. Never copy/move or resize the owning Correlator6 adapter.

Use RAW xy,xz,yz,xx-yy,xx-zz,yy-zz channels with unchanged KG Correlator6.
Its sentinel, block means and omitted deepest-level export are documented limits.
The modulus is G/(n_ch*kBT) = sum(shears)/5 + sum(raw normal differences)/30.
The earlier factor1/4 applies ONLY to Stage 2A's normalized normal products;
never apply it before the Stage 2B 1/30 weight. Correlate each chain separately;
combine all six channels within each chain before estimating modulus SE across
chains. Overlapping origins and correlated channels are not independent samples.
Compare coarse bins to block-averaged theory, never point-sample theory.

Every stage must maintain tested short example commands, both-precision build
commands, current CLI/output documentation and runnable external long-test
commands. Every simulation must print/save measured ns/bead/step (null/N/A for
zero steps), integration and overall wall costs. Report GPU sampling/D2H and CPU
worker times separately; overlapping times must not be added as wall time.

## Stage 2B.1 CPU worker conventions

Preserve `--cpu-workers 1` as default and serial reference; 0 auto respects Linux
CPU affinity and standard cgroup quotas when readable, with a portable hardware
concurrency/one fallback. Explicit counts >chains or >1024 are rejected; N>1
requires async streaming. Record requested/effective counts. Do not assume
physical-core counts, homogeneous cores or Intel-specific APIs.

Workers read the same completed pinned batch, with no redundant batch copy.
Dispatch and completion synchronization stay outside the frame/chain inner loops.
Only after all workers complete may the consumer free a slot, including errors.
No concurrent writes to one correlator. Join consumer/helpers before bank release;
evaluate and reduce in deterministic ascending-chain order after finish.
Thread stacks/counters scale with workers; chain banks/buffers do not multiply.
Do not present summed worker execution time as elapsed correlation time. Worker 0
barrier waits are a subset of pool wall time; consumer queue idle and transfer
wait are separate, overlapping producer/GPU scopes. Keep the primary production
ns/bead/step metric and unchanged sampling/math/RNG/uncertainty conventions.

Run only bounded checks in Codex, including check-workers ASan/UBSan/LSan and both
precision checks. The exact Linux performance/memory campaign is in
STAGE2B1_VALIDATION_PLAN.md; completed user-executed results and their provenance
are in STAGE2B1_HOST_RESULTS.md. Development-host science, performance and memory
validation passed. N100 terminal relaxation also passed (686/686 checks), closing
Stage 2B. Do not begin Stage 3; benchmark production-server performance separately.
The roadmap still places optimization in Stage 3 and semiflexibility/slip-spring
dynamics in Stage 4. NEXT_STAGE_ASSESSMENT.md lists open model and kinetic choices;
do not select consequential physics or change stage sequencing without explicit
scientific decisions and implementation authorization.


## Stage 4A.2 authorization and isolated semiflexible implementation

The explicit 16 October 2026 user authorization supersedes the historical
Stage 4 gate only for Stage 4A.1/4A.2. A separate `semiflexible` CPU/GPU model
is implemented. **STAGE 4A.2 ACCEPTED — GPU SEMIFLEXIBLE BACKBONE SCIENTIFIC
VALIDATION PASSED** on 17 October 2026, under the unchanged frozen
`STAGE4A2_VALIDATION_PLAN.md`: 204 user-host experiments, zero statistical
failures, archived original analysis/metadata and separate memory evidence in
`validation/stage4a2-acceptance/`. Acceptance is limited to tested cases and
tolerances. All 456 coarse-bias comparisons were unresolved: never claim a
measured convergence order. Do not infer future acceptance from bounded tests.
Stage 4A.3, stress extensions and slip-springs remain unauthorized.

Keep `rouse`, its RNG, CLI, correlator, physical model and existing thresholds
unchanged. New local files are `semiflexible.cuh/.cu`; independent force and
equilibrium authority remains `semiflexible_reference.py`. Explicit kappa
indices are internal beads 1..N-1, with zero endpoint entries in N+1 arrays.
Positive kb, nonnegative b0/kappa and positive uniform kBT/zeta are required.
No excluded volume, closure, periodic wrapping or hydrodynamics.

CUDA forces gather per bead, with one writer per force slot. Stretch overwrites;
bend adds on the same stream. All-zero kappa means NO angular allocation,
topology, launch or force geometry. Mixed zero angles are skipped before
normalization. Observation-time tangent measurements remain available in the
flexible model. Dynamics uses immutable flat IDs, Philox domain 3, eight
reserved draws per step, and separate old/new buffers. Do not change Rouse's
domains 0/1/2 or share initialization counters. CPU direct equilibrium sampling
uses a separate per-chain engine; do not replace it with Gaussian finite-rest-
length initialization or artificial long equilibration.

Fail on undefined forces, collapsed active angles and nonfinite proposals;
never clamp/regularize or continue past a failed timestep. Preserve deterministic
first-failing-step diagnostics and full old/proposed snapshots. Per-step
synchronous diagnostics are an explicit initial limitation, not a throughput
claim. Full-coordinate observation readback and CPU double reductions are
measured separately. Do not lower observation frequency to improve timings.
Bound workspace independently of step count, keep per-chain statistical units,
and preserve refusal to overwrite output directories. `parameters.txt` saves
actual precision-rounded model parameters. No full coordinate trajectories are
retained; initial/final/failure snapshots and streaming scalar observations only.

Run `make check-semiflexible` in both precisions, the original bounded checks
and lifetime sanitizer before changes are accepted. New GPU suites and host-
analysis smoke tests are bounded; `tests/semiflexible_host.py --run` is strictly
user-host work, never run its full campaign in Codex. Keep the acceptance plan
frozen before long experiments; archive deviations separately. Production-server
performance and memory behavior require separate host evidence.

## Reuse roadmap and active-campaign protection

Before future implementation work, read [ROADMAP.md](ROADMAP.md). It records the
user's reuse-first requirement, the unproven performance advantage of the local
kernels, and proposed UAMMD-backed comparisons. It does not authorize those
refactors or benchmarks. Preserve running campaign binaries, scripts, frozen
criteria and inputs; queued runs reuse executable paths. Documentation-only
roadmap changes must not trigger rebuilds or alter campaign artifacts.


## Stage 4A.2 acceptance evidence and scope

`STAGE4A2_REPORT.md` records the accepted tested model and provenance limits.
Keep the frozen plan and thresholds unchanged. Preserve the zero-angle GPU
capacity/active-count/launch regression condition: all three are zero for the
flexible path; active configurations execute bending. Archived original metadata
verifies 114 inactive and 90 active cases. Preserve archive byte identity and
verify SHA256SUMS before relying on copies; indexes are derived evidence aids.
The memory run plateau was 145 MiB whole-device (nvidia-smi), not process-specific
allocation evidence. CPU RSS differences are not meaningful growth/shrinkage.
No original compiler-toolkit identity is proved by a no-op host build; reported
system CUDA 11.5.119 and development CUDA 13.0.88 are distinct provenance facts.
Acceptance gives no universal timestep/stiffness/chain-length guarantee and no
production-server performance claim. Synchronous diagnostic transfers and CPU
observations remain costs. Rouse, RNGs, methods, tests and builds are unchanged.
No stress-relaxation extensions or slip-springs; Stage 4A.3 remains unauthorized.

## Stage 4A.3a scope and ten-minute execution limit

The user's 17 October 2026 authorization supersedes the historical Stage 4A.3
prohibition ONLY for Stage 4A.3a: analytical stress derivation, independent CPU
stress reference, bounded CPU tests and documentation. See STAGE4A3A_REPORT.md.
Do not modify accepted dynamics, RNG, existing tests, build behavior or frozen
plans. No GPU stress sampling, correlations/multi-tau, slip-springs or production
runs. Stage 4A.3b requires independent review of the Stage 4A.3a derivation/tests
and separate authorization before implementation.

Do not run any test, simulation or experiment expected to take longer than
10 minutes in Codex. Supply exact commands and resource/output expectations for
the dedicated Linux host; the user will execute them and return the results.
Split/reduce bounded verification where scientifically valid, never weaken
acceptance thresholds to fit the limit. Unknown-cost work must be bounded with
an appropriate timeout or deferred to the host. This reinforces the existing
ban on long campaigns; it does not authorize ten-minute production simulations.

The CPU virial uses W=V*sigma=+sum(g outer q)=-sum(F outer (r-r_ref)); no volume
or physical chain density is silently assigned. Stretch and bend stay separate;
validate raw tensors without symmetry/trace projection. Preserve raw channel
ordering xy,xz,yz,xx-yy,xx-zz,yy-zz. At isotropic equilibrium <W>=N*kBT*I,
not zero; the mean bending tensor and mean deviatoric stresses vanish. Future
Green–Kubo normalization requires explicit chain density and thermal-energy
factors, including total stretch/bend cross-correlations. No modulus or new
stress-relaxation acceptance is established by CPU static checks.


## Stage 4A.3b implementation authorization and host-review boundary

The user's 17 October 2026 Stage 4A.3b task supersedes historical prohibitions
only for complete GPU virials, six-channel streaming, bounded tests and a frozen
Stage 4A.3c plan. Use STAGE4A3A_REPORT.md and semiflexible_stress_reference.py
as the accepted science; see STAGE4A3B_REPORT.md for implementation scope.
Accepted force/update/RNG kernels, Rouse, CPU references, old tests, evidence
and frozen prior plans remain unchanged. Stress is opt-in; default-off dynamics
and precision-specific replay must be preserved. No stock angular virial.

The isolated synchronous stress adapter reuses Bank/CpuWorkers/KG unchanged.
Do not fork the multi-tau estimator or modify Rouse's scientific definitions.
All frames and final partial batches must be consumed; incomplete coarse blocks
are not padded and legacy deepest-populated-level export behavior is preserved.
Keep raw products (no empirical mean subtraction), per-chain clusters and raw
xy,xz,yz,xx-yy,xx-zz,yy-zz channels. Assemble total W before the correlator.
Export H, g=H/(kBT)^2 and G=n_chain*H/kBT only for explicit density. Preserve
read-only stress probes, individual stretch/bend validation, raw symmetry/trace
checks and zero-angular-allocation/launch conditions. No force regularization.

Record stress GPU,D2H,synchronization,CPU pool,barrier,output and total production
costs; do not add subset timers or reduce sampling frequency. Existing CPU
conformation observations remain an explicit cost. The frozen new plan and host
generator are preparation only: no --run option, no Stage 4A.3c experiments.
Stage 4A.3b needs independent review BEFORE scientific host execution and further
user authorization. Respect the ten-minute rule above. No Stage 4B/slip-springs.


## Stage 4A.3b.1 host readiness; no production execution authorization

The user accepts Stage 4A.3b. Current authorization permits host analysis,
resumable execution-management tools, bounded fixtures and documentation ONLY.
See STAGE4A3B1_REPORT.md. Do not modify simulator/kernels/dynamics/RNG,
correlators, Rouse, accepted CPU references, build behavior, original generator,
old tests, archives or frozen scientific criteria. Preserve all282 commands and
plan SHA efd040ceba8cd903dee7a145296dce08435e3df3efa940c65170f4bcf98acb36.
Clarification proposal V1 is not an applied plan amendment.

Authenticate plan/manifest/inputs before analysis or execution. Cache only
completed authenticated work, use atomic integrity-protected checkpoints,
retain invalid/missing/support/provenance records, and never accept partial
outputs. Independent chains remain statistical clusters. Unknown compilation
provenance cannot be inferred from system nvcc or a no-op build. Keep raw
multi-tau definitions and all existing thresholds unchanged. Unresolved bias
is not a convergence order; unsupported terminal tails cannot pass.

The runner is serial, requires an explicit user-host execution flag, refuses
partial/failed/orphan evidence and preserves original argv. That flag is not
user authorization by itself. No frozen pilot/campaign member or large CPU
reference ensemble may run in Codex during readiness work. The10-minute limit
remains; only tiny noncampaign GPU fixtures and bounded tests are permitted.
Stage4A.3c production and Stage4B require separate explicit authorization.

## Stage 4A.3b.2b compact output and operational identities

The current explicit user task authorizes host scalar serialization, compatible
analysis/runner changes and bounded tests; it supersedes the preceding source/
build prohibition only for this scope. See STAGE4A3B2_IMPLEMENTATION_REPORT.md
and STAGE4A3C_OUTPUT_SCHEMA_V1.md. Full remains the default with original output
semantics; compact requires stress streaming. Every original scalar computation
and stress frame, including step0, must remain. Do not thin observations, change
windows, kernels, initializers, RNGs, stress/correlator math or thresholds.
Preserve full mode, existing references/tests and Stage4A.2/Rouse behavior.

Compact summaries retain independent-chain clusters, all-frame finite/minimum/
coverage evidence and exact scheduled quarter frames. Checksums detect accidental
corruption; SHA256 receipts authenticate files. Do not claim reconstruction of
the omitted scalar trajectory. Reject partial/nonfinite evidence. Smooth zero-
rest-length collapsed bonds are force-defined, but undefined tangents still fail
the unchanged frozen analyzer domain rules.

Keep the original scientific plan/hash and 282-command generator unchanged.
Use semiflexible_stress_profile.py to create a separate authenticated compact-v1
root against a preserved original full parent; profile IDs/outputs/receipts/
checkpoints cannot be mixed. Source/executable/version proofs must be explicit.
Use separate GPU_BUILD paths; never replace binaries queued by another campaign.
Run the new scalar suite in both precisions, existing Rouse/semiflexible/stress/
host-analysis regressions and required sanitizers with bounded timeouts. No
Stage4A.3c production run or old interrupted-pilot restart is authorized. Do not
touch the interrupted /tmp/semiflexible-readiness.oH8Vnc pilot. The ten-minute
Codex limit remains; provide host preparation commands without running them.
