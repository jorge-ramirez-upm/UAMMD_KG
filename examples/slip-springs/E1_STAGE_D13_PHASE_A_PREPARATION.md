# E1 Stage D1.3 — Phase A adapter preparation v1

Prepared on `slip-springs` from local and remote HEAD
`3788e4808d2fed7af80055c3df25712525511f7e`, independently verified before edits.
**Implementation and bounded verification only. The Phase A benchmark was not
executed. No scientific campaign, Phase B/C execution or D2 work is authorized.**

Reviewed the local rules, accepted D1.2 long-time design, D1.1 preparation,
D1.0 observer report, D0/D0.1 protocol/screen, actual observer/checker/CLI,
D1.1 build/runner/authentication/analysis and D1.2 generator/schedules. The
accepted force, Brownian, hopping, renewal, observer, RNG, timer semantics and
historical authentication allowlists remain unchanged. All new files stay here.

## 1. Immutable Phase A execution manifest

[manifest.json](e1_d13_phase_a_config/manifest.json), schema
`e1-d13-phase-a-execution-v1`, SHA256:

```text
0c2df3279faf6a7457125cdc12f78c233d5d8999c6e459560edbfe1cb9a3fd3e
```

The manifest derives its runs directly from the accepted D1.2 Phase A proposal,
not a new matrix generator. It binds that proposal's SHA and the D1.2 design
SHA `2da957a5ee44956c395004bd20c23bee8e809b6d312ceee814e3f6934b2a5bbe`.
D1.1 manifest SHA remains
`a14612088cab809f101c22c5c60c1879a136e9383305980864c014cae899dc2f`.
All D1.1/D1.2 frozen tools, configurations, reports and scientific margins are
preserved. The new specification authenticates its parent before generation
and validation. Preparation freezes content/identities, **not permission**.

| Cell | N | kappa | Ne | nu_hop | dt | Z | rho | Steps/profile | Paired seed |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 1 | 8 | 0 | 16 | 10 | .0001 | 32 | 1/18 | 2500 | 721300101 |
| 2 | 8 | 0 | 16 | 10 | .00025 | 32 | 1/18 | 1000 | 721300201 |
| 3 | 32 | 10 | 4 | 100 | .0001 | 512 | 8/33 | 2500 | 721300301 |
| 4 | 32 | 10 | 4 | 100 | .00025 | 512 | 8/33 | 1000 | 721300401 |

Common M64,kb30,b0=1,kBT=zeta=1,A2=5,T=.25,double,end renewal on,stress off,
full scalars and direct exact-equilibrium initialization. Z follows E1's
round_half_up(M*N/Ne) convention. Each cell runs `off` then `sparse`, sharing
its seed within the pair only: **eight processes, four physical initializations,
14000 total BD steps and 51520 expected attempts**. No extra repetitions/cells.
These are benchmark work estimates, not observed Phase A results.

Manifest contents include exact run/profile/pair IDs, seeds and parameters,
all integer schedules and SHA256s, exact argument templates with only binary,
output and config path placeholders, expected versions/row counts, accepted
scientific source hashes, twelve preparation/dependency module hashes, target
physical GPU UUID/model/architecture, and required external trust anchors.
Actual absolute argv is printed at preflight and bound in every receipt.
Generation refuses overwrite; validation compares exact deterministic content
and schedule bytes against the frozen definition. Revisions require a new
reviewed version/root/hash. B/C proposals, extra runs, new physics parameters,
changed source/tools or changed schedules are refused.

Every committed authorization is false; all eight `approved_limits` values are
null. The separate approval template is also false/null. Never edit this manifest
to authorize execution. No approved execution record was created by this task.

## 2. Exact sparse schedules and output profiles

| dt | Regular scalar steps (.1) | Full E1 steps | Complete-state audit steps |
|---:|---|---|---|
| .0001 | 0,1000,2000 | 0,1,5,25,100,500,2500 | 0,1,100,2500 |
| .00025 | 0,400,800 | 0,1,2,10,40,200,1000 | 0,1,40,1000 |

Shared early times are 0,.0005,.0025,.01,.05, with explicit final .25.
Step one is dt-specific diagnostic evidence. The proposed .5 late full-E1
cadence has no positive multiple inside this short phase; it is not replaced
with a denser late cadence. All conversions use exact rational/integer steps,
with no interpolation or rounding. Six committed step files contain the full,
scalar-audit and snapshot schedules. The scalar list audits `--sample`;
it is not an unsupported CLI argument.

Off omits both observer CLI arguments and must contain exactly eleven legacy
files, **no optional E1 files or observer marker**. Completion is proven by its
successful supervised exit, terminal metadata/counters, full raw checksums and
paired replay against the independently checked on profile. On requires exactly
21 files, v1 schema/completion and all seven E1 frames/four snapshots. Existing
scalar rows are reused; six supplementary backbone frames supply full-E1 times
off the scalar cadence. N32 long tangents are present only at full-E1 times.

At T=.25 the final step is not a .1 scalar multiple. Both profiles still write
legacy final coordinates and spring states; on additionally writes a synchronized
final E1 observation and snapshot. The independent observer checker reconstructs
those states and binds them to legacy endpoints. Initial observations precede
all dynamics; subsequent E1 observations follow the complete BD/jump batch.
The observer's completed-state phase and streaming memory behavior are unchanged.

## 3. Runner and scientific/executable identities

New modules are `e1_d13_phase_a.py`, `_runner.py`, `_auth.py`, `_analysis.py`
and the small `e1_d13_reuse.py` binding helper. Private module bindings reuse
frozen D1.1 functions with Phase A specification/authentication references.
They do not mutate the original imported modules or rewrite historical files.
Reused components include real fresh builds/dependency closure, restricted
process environments, physical GPU/runtime probes, POSIX supervision/resource
checks, GPU locks, per-run receipts and independent whole-cohort authentication.

New behavior is restricted to off-profile validation, strict Phase A identity,
paired replay, benchmark metrics, and eight-process orchestration. New execution
orchestration is necessary to check every pair **before** publishing completion;
calling the old execution function and validating pairs afterward would be too
late. The generic D1.1 on-profile checker is reused, including independent
snapshot reconstruction and counter/schedule checks. Off validates exact legacy
headers/counts/identities, parameters, finite diagnostics, single occupancy,
canonical spring IDs, seed/GPU/model/RNG provenance, and all counter identities.
Raw inventories/checksums plus the final paired gate cover valid-but-altered
numeric CSV values that cannot be detected from syntax alone.

The simulator source remains pinned to accepted D1.0
`0dea651b58171a72206774bcebb2f4c74960069b` in a separate clean checkout of the
correct GitHub repository. The current adapter commit is a preparation identity,
not the compiled scientific revision. Build receipts bind exact source/origin,
flags/command, actual CUDA13 and C++ compiler identities, 1914 dependency records,
five linked-library records, runtime library, observed compilation transcript,
fresh executable and all preparation hashes. A no-op/adopted binary is refused.
Live checks revalidate source/compiler/dependencies/binary; archival analysis
validates externally trusted build receipt and copied binary/transcript hashes.

Actual bounded fresh build performed:

- Source `/tmp/e1-d11-source`, clean accepted D1.0 checkout.
- New root `/tmp/e1-d13-build`, double, sm_86, CUDA13.0.88, g++11.4.0.
- Observed compilation wall 17.457 s; no trajectories during build.
- Build receipt SHA256
  `1739e51ebbe43a81a810d09274d9a9304fafb339166d7e13f5e4600bd32d37e0`.
- Executable SHA256
  `41b778f5ce4087be5f7713b3c5df788035d911354810824d028bfab605ffe7f7`,
  2709792 bytes. This is a measured binary identity, not inferred reproducibility.

Default operation is read-only preflight. Execution additionally requires
`--authorize-phase-a-execution` **and** a separately reviewed SHA-bound approval
with exact manifest/build/environment/GPU/output-root identities and every budget.
The physical target UUID is pinned to the approved host. Read-only default
hardware probing may initialize a temporary CUDA context to query runtime/free
memory; it never calls the simulator or advances physical states.

Execution uses a new nonoverwriting root, shared GPU lock and one child at a time.
It rechecks inputs/source/build/environment around runs, applies per-file limits
and per-run/aggregate wall/output/host-RSS/headroom checks, and preserves commands,
resources, process results, logs, exit codes, failures and interruptions. The
reused supervisor terminates process groups on timeout/failure and uses a Linux
parent-death guard. Polling is .05 s, so limits can overshoot between observations;
these are not hard cgroup RSS/aggregate-disk quotas. There is no resume, skip,
partial adoption or automatic phase chaining. Physics is never changed to fit a
budget. Setup failures preserve failed status; child failures preserve receipts.

Only after all eight successful raw authentications, receipt checks and four
byte-replay gates does the runner publish the campaign completion marker. Missing,
malformed, nonfinite, truncated, interrupted or inconsistent evidence is refused.
The independent consumer requires externally recorded manifest, approval and
completion hashes; the approval binds build/environment identities. It checks
all eight ordered processes, receipt/log/raw hashes, elapsed limits, copied
binary/transcript, GPU/environment, source, schedules and pairs. A directory name
or a checksum stored beside unauthenticated data is insufficient evidence.
Analysis reauthenticates before publication and refuses overwrite or writing into
raw evidence. No historical campaign source allowlist was relaxed.

## 4. Paired replay and benchmark-analysis definitions

For every pair, require equal file sizes/SHA256 for all legacy files except
`metadata.json`: initial/final polymer coordinates; initial/final stable spring
IDs, chain/site and anchors; fixed anchors; parameters; scalar rows, initial
bonds/final bond summaries; hopping and renewal sidecar counters. Metadata is
compared as bytes after replacing **only** ten explicit numeric timing/rate
fields: initialization, integration, production wall, observation, recurrent
output, final output, force/diagnostic seconds; integration/overall ns per bead
step; and bead-updates/s. All non-timing bytes remain required equal. Optional
observer-owned files and timing values are not paired equality requirements.

`e1-d13-phase-a-analysis-v1` reports for each process:

- Initialization, CUDA integration, production wall and supervised process wall;
  each integration/production/process wall divided by actual BD steps separately.
- Attempts, accepted interior hops, proposed/accepted renewals, same/cross-chain
  transfers, and attempts divided by production wall (end-to-end throughput).
- Observer exclusive/wall/transfer seconds and transferred bytes when enabled;
  null when disabled. Zero optional timers are allowed, but missing, nonnumeric,
  negative or nonfinite timers/rates are rejected. Required positive-duration
  initialization/integration/production/final/process timers must be positive;
  zero production time is not converted to an infinite throughput.
- Raw bytes per file and per disjoint category: legacy backbone, legacy state,
  spring/site/connector, audit snapshots, observer backbone and raw metadata.
  Run logs/receipt sizes, total campaign evidence and shared provenance/log
  residual are retained separately; category totals must sum exactly.
- Peak child host RSS from wait4/proc supervision, explicit device-array bytes,
  and prelaunch/postexit free-GPU observations. **Peak GPU usage is null**:
  no reliable per-process peak sampler was added. Free-memory snapshots and
  explicit-array allocation are not presented as peak GPU memory/RSS.
- Actual GPU/environment identity, executable path/size/SHA and source/build,
  approval, manifest and completion trust anchors.

Each pair reports on-minus-off differences descriptively. There is only one pair
per cell: no confidence interval, variance estimate or precise overhead/speedup
claim. Supervised wall includes process startup/exit and polling granularity;
production excludes initialization and final output. CUDA integration includes
hopping/invariants/forces/update/diagnostic D2H and host gaps. Observer wall
includes reductions/transfers; exclusive and transfer timers overlap other
scopes. They are never added into a purported total. There is no isolated hopping
kernel timing. No scientific equilibrium, timestep, mixing, convergence, long-time
independence or rheological acceptance is produced by this analyzer.

## 5. Bounded tests actually performed

No Phase A cell/duration was run. No B/C or 32-run pilot was run. GPU tests use
only N3,M4,Z4,kappa10,dt=.0001,nu20000,seed72103, **five BD steps**, sample2,
E1 steps 0,1,2,5 and snapshots 0,1,5, in double precision. Each technical suite
launches one off/on pair; test failures/corruption use copies, not new campaigns.
Test-only timeout/RSS/disk caps and synthetic reader records are not Phase A
budgets or executable approvals. Synthetic supervisor tests mock every child;
their temporary proof binary is nonexecutable and cannot pass live source/build
checks. They set no real CLI execution flag and leave no approved record.

| Check | Result |
|---|---|
| New CPU/synthetic adapter suite | 11 passed, 16.849 s |
| New five-step technical suite, fresh binary | 6 passed, .501 s |
| Frozen D1.1 CPU/synthetic/reference/supervision suite | 24 passed, 2.988 s |
| Frozen D1.1 five-step technical suite, fresh binary | 6 passed, .538 s |
| Frozen D1.2 proposal/preservation suite | 6 passed, 1.522 s |
| Fresh build and live read-only preflight | Passed; approval/budget blocker remains |

Tests cover deterministic manifest reproduction, exact matrix/pair seeds and
integer/off-cadence schedules; modified sources/tools/parameters/extra cells/B
refusal; false/null approvals and resource refusal; incorrect executable/source,
GPU/runtime/environment; missing/changed files and absent markers; invalid
counters; valid numeric corruption detected through receipt hashes; metadata
masking that accepts timing changes and rejects non-timing changes; actual
snapshot reconstruction, exact paired legacy bytes, output category arithmetic,
per-step/throughput definitions, zero/negative/nonfinite/nonnumeric timers,
complete-eight-only aggregation, interrupted/partial cohorts, and publication
that reauthenticates and refuses overwrite. Mocked orchestration exercises
interruption, a failed paired gate (no completion marker), and eight-child/four-
pair success before completion. No mock is claimed as real scientific evidence.

Only Python instrumentation/management files were added; C++/CUDA/observer
physics is unchanged. No new sanitizer or single-precision build was necessary;
prior D1.0 sanitizer/both-precision evidence remains prior evidence, not a new
D1.3 claim. All actual commands were bounded below ten minutes. Reused frozen
modules and D1.2 content were separately checked for byte preservation.

## 6. Live GPU-host preflight and remaining approval fields

Read-only preflight with the new authenticated build measured:

| Item | Observed value (availability, not an approval) |
|---|---|
| GPU UUID | GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 |
| GPU model / capability | NVIDIA GeForce RTX 3060 Ti / 8.6 |
| Driver / toolkit | 580.178.04 / CUDA13.0.88 |
| Runtime / driver API | 13000 / 13000 |
| Whole GPU reported memory | 8589934592 B |
| Free GPU after temporary runtime probe | 8072724480 B |
| Available host/cgroup memory | 31085785088 B |
| Free disk | 1247454162944 B |
| Planned processes / BD steps | 8 / 14000 |
| Proposed output root | /tmp/e1-d13-phase-a-NOT-EXECUTED (does not exist) |

Environment SHA256:
`05e9f076948c5d562925dd24b9d9d47bc8611698516efea13808029ad5d8c79a`.
Raw read-only summary: `/tmp/e1-d13-live-preflight.json`; build transcript/receipt
are under `/tmp/e1-d13-build`. These external technical artifacts were preserved.
Availability varies and must be rechecked; toolkit/runtime inventories and the
bound execution environment are recorded separately. Default sandbox preflight
also succeeds, explicitly reporting GPU probe unavailable where driver access
is denied, without creating an output root.

**Still unset and requiring separate review:** per-run/aggregate seconds,
per-run/aggregate output bytes, minimum disk/GPU/host headroom, and maximum host
RSS. The reused D0/D1.1 candidate ceilings (120 s/run, 3600 s aggregate, 5 GiB
aggregate output) remain ceilings, not approved defaults or predicted runtime.
Unknown startup/context/event/diagnostic costs require headroom review. D1.2's
rough 90 MiB Phase A storage envelope remains a projection, not a safety budget.
No values were inferred from the tiny technical fixtures to authorize Phase A.

## 7. Reproducible preparation and independent review commands

From repository root, commands actually used (no execution authorization):

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 examples/slip-springs/tests/test_e1_d13_phase_a.py -v
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 examples/slip-springs/tests/test_e1_d1_pilot.py -v
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 examples/slip-springs/tests/test_e1_d12_plan.py -v
# Read-only default; prints all eight commands and blockers.
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 examples/slip-springs/e1_d13_phase_a_runner.py
# Fresh build only; NEW build root required. Existing source checkout is pinned/clean.
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 300s python3 examples/slip-springs/e1_d13_phase_a_runner.py build --source-tree /tmp/e1-d11-source --build-root /tmp/e1-d13-build --cuda-home /usr/local/cuda --arch sm_86 --cxx /usr/bin/g++
# Read-only bound runtime/resource review; output root remains absent.
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 90s python3 examples/slip-springs/e1_d13_phase_a_runner.py preflight --build-receipt /tmp/e1-d13-build/build.json --build-sha256 1739e51ebbe43a81a810d09274d9a9304fafb339166d7e13f5e4600bd32d37e0 --gpu-uuid GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 --output-root /tmp/e1-d13-phase-a-NOT-EXECUTED
# Tiny technical fixtures only; these need GPU driver access.
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 90s python3 examples/slip-springs/tests/test_e1_d13_phase_a_technical.py /tmp/e1-d13-build/bin/semiflexible -v
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 90s python3 examples/slip-springs/tests/test_e1_d1_pilot_technical.py /tmp/e1-d13-build/bin/semiflexible -v
```

Reproduce configuration into a **new** directory with
`python3 examples/slip-springs/e1_d13_phase_a.py --freeze NEW_DIR`; compare the
printed SHA to the manifest SHA above. The existing committed directory cannot
be overwritten by this API. A repeated build also needs a new root and its own
reviewed receipt/executable hashes; do not reuse the existing path expecting a
fresh compilation. GPU commands here used execution outside the sandbox.

Before the benchmark: independently accept this adapter and its technical
report, review the exact frozen manifest, authenticate a fresh build/runtime,
choose a fresh output root, fill every resource field in a separately reviewed
approval copy, record its SHA and obtain explicit Phase A execution authorization.
Only then may the separate execution flag be supplied. This task supplies none
of those approvals. After separately authorized execution, the runner prints an
external completion SHA. Analysis requires all three external anchors:

```sh
python3 examples/slip-springs/e1_d13_phase_a_analysis.py --campaign COMPLETED_ROOT --manifest examples/slip-springs/e1_d13_phase_a_config/manifest.json --manifest-sha256 0c2df3279faf6a7457125cdc12f78c233d5d8999c6e459560edbfe1cb9a3fd3e --approval-sha256 REVIEWED_APPROVAL_SHA --completion-sha256 EXTERNALLY_RECORDED_COMPLETION_SHA --output NEW_ANALYSIS.json
```

This analysis command was not run on a real Phase A cohort because none exists.
Phase A performance is still unknown. Phase B/C execution remains unimplemented
and unauthorized; Phase A results cannot automatically authorize either phase.
