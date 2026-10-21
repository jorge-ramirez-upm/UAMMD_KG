# E1 Stage D1.1 — frozen proposed pilot preparation

Prepared 21 October 2026 on `slip-springs`, starting at
`0dea651b58171a72206774bcebb2f4c74960069b`; local and remote HEAD were independently verified and
tracked work was initially clean. The user accepts the E1 model/observer's
bounded technical gates. E1, D0/D0.1, D1.0, Stage C, backbone authority, project
status, local rules and actual observer/checker schemas were inspected.

**Preparation only. No scientific pilot was authorized or executed. No D2 work.**
The simulator, force/Brownian/hopping/renewal algorithms, observer and all
historical scientific margins/source allowlists remain unchanged. The new
Python tools and configuration are local to `examples/slip-springs/`.

## 1. Frozen proposed matrix and identities

The proposed manifest is [manifest.json](e1_d1_pilot_config/manifest.json), SHA256:

```text
a14612088cab809f101c22c5c60c1879a136e9383305980864c014cae899dc2f
```

This freezes a **proposal and its software/input identities**, not permission to
run or scientific acceptance. `execution_authorized` stays false and
`approved_limits` stays null in the manifest. Execution needs a separate reviewed
approval record; do not edit the frozen manifest to enable it. Regeneration into
a NEW directory is deterministic and refuses overwrite. All four preparation
modules are hashed in the manifest, alongside accepted E1/observer/reference and
D0 authority files. Their content must stay unchanged during build/execution.

Exactly eight cells, four independent replicas per cell, M=64, b0=1,kb=30,
kBT=zeta=1,A2=5,T=.25, double precision, end renewal on, stress off, full scalars:

| Cell | N | kappa | Ne | nu_hop | dt | Z | rho=Z/[64(N+1)] | Steps | Seeds (replicas 1–4) |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1 | 8 | 0 | 16 | 10 | 0.0001 | 32 | 1/18 | 2500 | 620261101–620261104 |
| 2 | 8 | 0 | 16 | 10 | 0.00025 | 32 | 1/18 | 1000 | 620261201–620261204 |
| 3 | 8 | 10 | 4 | 100 | 0.0001 | 128 | 2/9 | 2500 | 620261301–620261304 |
| 4 | 8 | 10 | 4 | 100 | 0.00025 | 128 | 2/9 | 1000 | 620261401–620261404 |
| 5 | 32 | 0 | 4 | 100 | 0.0001 | 512 | 8/33 | 2500 | 620261501–620261504 |
| 6 | 32 | 0 | 4 | 100 | 0.00025 | 512 | 8/33 | 1000 | 620261601–620261604 |
| 7 | 32 | 10 | 16 | 10 | 0.0001 | 128 | 2/33 | 2500 | 620261701–620261704 |
| 8 | 32 | 10 | 16 | 10 | 0.00025 | 128 | 2/33 | 1000 | 620261801–620261804 |

Z is computed with exact rational arithmetic as round_half_up(64*N/Ne), not a
constant site density or a Poisson approximation. Seeds are
`620261000 + 100*cell + replica`; all 32 differ. No initial states are shared
across cells or replicas. Cross-dt comparisons are therefore independent;
reusing replica numbers does not create pairing. Only changes over time within
the same replica are paired. No extra cells, extensions, rates, timesteps or
replicas can be selected through the runner.

## 2. Exact schedules and bounded audit states

One shared tick is exactly 1/2000=.0005 physical time. Shared ticks are
`0..20`, then `30,40,...,500`: 69 shared times. Thus observations are dense
through .01 at spacing .0005 and sparse from .015 through .25 at spacing .005.
The switch at .01 is a **prospective pilot choice requiring review**, using the
two D0.1 cadences; it replaces the earlier all-dense 501-frame pilot proposal
with 70 observer frames. D0 scientific margins are unchanged. No burn-in is
removed from this exact-start preservation pilot.

| dt | Exact shared step ranges | Extra diagnostic-only step | Snapshot steps | Legacy sample stride |
|---:|---|---:|---|---:|
| .0001 | 0,5,10,...,100; 150,200,...,2500 | 1 (t=.0001) | 0,1,5,100,500,2500 | 50 (.005) |
| .00025 | 0,2,4,...,40; 60,80,...,1000 | 1 (t=.00025) | 0,1,2,40,200,1000 | 20 (.005) |

The four committed `.steps` files contain every integer explicitly, with their
SHA256 and complete lists in the manifest. Each observation schedule has 70
frames; each snapshot schedule has six, below the observer cap of eight. The
snapshots cover t=0, that dt's first update, .0005,.01,.05,.25. All include final
state, are sorted/unique/in range, and are validated before execution. Time
conversion uses `Fraction`; a noninteger time/step request raises an error.
There is no rounding, interpolation or nearest-bin comparison.

Existing `samples.csv` supplies the 51 regular frames at physical stride .005;
`equilibrium_backbone.csv` supplies just the 19 additional observer frames.
Tangents 8/16 for N32 come from the accepted separate tangent stream. First-step
frames are retained and explicitly excluded from cross-dt shared-time contrasts.
Event deltas are **summed between consecutive shared times**, including deltas
at any intervening first-step frame: the first shared interval is [0,.0005] for
both dt values, not intervals of unequal length after their first updates.

## 3. Independent references and exploratory science

`e1_d1_pilot_analysis.py` consumes only authenticated complete evidence. At each
shared time it first reduces a whole replica (all 64 chains and all Z live
springs), then computes means, sample SD (ddof=1) and SE across the four replica
estimators. Chains, connectors, components, frames and overlapping time windows
are never counted as independent replicas.

Backbone targets use the accepted independent CPU radial moments and stable
Langevin function h=coth(kappa)-1/kappa, with h=0 at kappa=0. The finite-chain
sums are exactly those in D0: B(d)=d*mu2+2*mu1²*sum_(s<d)(d-s)h^s,
Re²=B(N), Rg²=sum_d(m-d)B(d)/m², and tangent(s)=h^s. No Gaussian-chain or
large-N approximation and no fit to slip-spring output is used.

| N,kappa | Re² target | Rg² target |
|---|---:|---:|
| 8,0 | 9.3161290326 | 1.7252090801 |
| 8,10 | 56.3256847737 | 6.4288329579 |
| 32,0 | 37.2645161305 | 6.3989573153 |
| 32,10 | 493.0134446496 | 58.8782832386 |

Production radial/rate quadrature uses order 128 and checks order 256 with a
1e-11 absolute refinement guard. Independent tests integrate the radial law to
16 thermal standard deviations with 384 nodes, and check finite-chain sizes
through a separate bond-covariance/coordinate-centering calculation. A 48-node
orientation transfer matrix verifies h^s through s=16, including kappa=2.
The accepted sampler is not used to generate a new reference ensemble. Tail/
quadrature error is not declared zero, and confirmatory reference error budgets
remain a separate review requirement.

The exact canonical population law is
`C(m,z)*C((M-1)m,Z-z)/C(Mm,Z)`, using integer binomial coefficients and exact
normalization identity before floating conversion. Its mean is Z/M and variance
m*rho*(1-rho)*(Mm-m)/(Mm-1). A small enumeration of all 84 subsets of three out
of nine sites independently verifies the PMF, site occupancy and moments.

The Gaussian connector reference has component means zero, second moments A2/3,
off-diagonal moments zero and mean squared extension A2=5. Analysis reports raw
component moments, unbiased within-replica component variance (divisor Z-1),
radial and component CDFs at fixed theoretical .01,.05,.10,.25,.50,.75,.90,.95,.99
quantiles. These CDF cuts are calculated analytically/numerically from the
reference, never calibrated on pilot trajectories. Numerical Gaussian overlap
and Maxwell radial integrals independently test the rate/CDF formulas. Size
CDF targets are not invented; no large reference ensemble is generated.

At each frame the analysis includes per-chain Re²,Rg²,bond moments and supported
tangents, contour occupancy means at each bead index, the whole population PMF
and CDF, population variance about the known Z/M, connector moments, and the
exact D0 joint scores:

```text
f_c = Re²_c / <Re²>_bb - 1
A_joint = sum_c f_c*(Z_c-Z/M) / (M*sqrt(Var(Z_c)))
B_joint = sum_c f_c*(sum_live_on_c |e|²-Z_c*A2) / (Z*A2)
```

Both joint targets are zero. Site/chain identities remain available in the raw
observer data. Per-replica observed site/chain occupancy coverage and renewal
counts are reported. Coverage is only at scheduled frames; total renewals do
not establish per-ID renewal coverage, independent samples or mixing. The
accepted observer does not record exact per-ID renewal history or per-chain
entry/exit events, so these quantities remain unavailable rather than inferred.

Interval hopping/renewal rates are counts divided by their **shared physical
interval**. Ideal canonical references use v=(L-Z)/(L-1): J_attempt=Z*nu,
J_out=Z*nu/m, J_renew=J_out*(2M-1)/(2M)*v,
J_cross=J_out*(M-1)/M*v, J_same=J_out*v/(2M), and
J_hop=Z*nu*N/m*v*E_radial[erfc(ell/(2*sqrt(2)*sqrt(A2/3)))].
Interior vacancy/Metropolis and occupied-renewal rejection references follow
from the corresponding complementary event categories. These are ideal
**continuous-time equilibrium expectations**, not proof of finite-dt accuracy
or independent Poisson accepted counts. The existing counter semantics are
preserved and all cumulative/interval identities must agree before analysis.

Intervals are exploratory, pointwise nominal 95% Student-t3 intervals on means.
Cross-dt contrasts use independent replica variances and the t3 critical value
(conservative relative to normal/Welch critical values with df>=3, not a theorem
for four skewed replicas). Time contrasts use per-replica paired changes from
step zero, alongside absolute reference discrepancies. Temporal ranges of means
are reported. Zero observed replica variance is explicitly flagged and is not
proof of precision. There is **no simultaneous coverage or equivalence/pass
classification**; four replicas do not implement the D0 confirmatory R floor.
Approved D0 margins are neither relaxed nor fitted to these exploratory outputs.

Late records from .01 to .25 have only 49 equally spaced frames per replica.
The pipeline may report demeaned, finite-series ACF diagnostics through lag 10,
with zero-variance/insufficient cases marked. It deliberately leaves tau_int null:
stationarity, slow modes and reliable IATs are unsupported over this horizon.
No terminal dynamics, rheology, diffusion, D2 equilibration or unrestricted
mixing claim is made.

## 4. Authentication and failure handling

The tools are separate from historical campaign runners, whose frozen physics,
plans and source-authentication allowlists are not changed. They reuse the
accepted observer checker/reference rather than substituting a new observer or
loosening old authentication rules.

Trust anchors are explicit inputs: externally reviewed manifest SHA256,
build-receipt SHA256 in the independent approval, environment SHA256 in that
approval, the approval file's SHA256, and an externally recorded **completion
SHA256** printed by a successful runner. The latter binds the complete ledger
and every per-run receipt/raw checksum; analysis never derives its trust solely
from checksum files stored beside the data.

The binary source is pinned to accepted D1.0 commit
`0dea651b58171a72206774bcebb2f4c74960069b` in a separate clean source checkout.
This preparation commit contains only the new tools/docs/config; do not pretend
its later Git identity is the compiled simulator revision. Build receipts bind:

- Exact repository origin/commit and accepted E1/observer source file hashes.
- A real, fresh double build command with explicit CUDA architecture, host
  compiler and flags, compiler/toolkit versions and executable SHA256.
- The dependency closure from nvcc preprocessing, compiler/header identities,
  linked libraries, runtime library, and the actual build transcript.
- Observed compilation and a newly produced target; existing build directories,
  no-op compilation and adopted binaries are refused.

Default runner operation is a **read-only preflight**, printing all 32 commands,
parameters, schedules, estimates, measured available resources, identities and
blockers. A build and physical GPU UUID enable a read-only runtime probe. The
probe checks a single GPU, UUID/name/compute capability, driver/runtime versions,
Python/NumPy identities, stable execution environment and absence of other GPU
compute processes. GPU/host/disk headroom must satisfy separately approved limits.
Compiler injection flags, LD_PRELOAD and arbitrary inherited environment values
are excluded; the child gets a recorded, restricted environment.

Execution additionally requires the explicit `--authorize-pilot-execution` flag
AND a SHA-bound, reviewed approval with `execution_authorized:true`, a review
reference, the exact output root/build/environment/GPU identity and all resource
budgets filled. The committed template has false/null values and cannot launch
anything. No task action set this execution flag or issued an actual approval.

Configuration, build, evidence and analysis paths are checked before writes:
repository outputs must stay under this project, and the pinned source checkout
is read-only. The runner creates a fresh root, archives binary/build/input identities, locks
its selected GPU against other D1 runners and runs **one replica at a time**.
It rechecks source/toolchain/binary/configuration/environment identities around
runs. Per-run and aggregate wall time/output bytes, disk headroom and host RSS
are checked at .05-second polling intervals and after exit/validation; per-file
RLIMIT_FSIZE is also applied. Timeouts terminate the process group and escalate
to SIGKILL after one second. SIGINT/TERM/HUP preserve interruption receipts; a
Linux parent-death guard kills the child if the supervisor is killed. Polling
can overshoot a limit between checks; this is not a hard cgroup RSS/total-disk
quota, and any violation rejects the run. Budget review must allow safe headroom.

Every launch records exact argv, environment identity, replica/seed, start/end
status, exit code, actual wall/RSS, resources, stdout/stderr and process results.
Raw authentication checks exact physical/effective parameters, precision, model,
RNG domains, complete schedules and row counts, source/schema versions, initial/
final state agreement, actual duration and all event totals. All raw files get
sizes and SHA256; duplicate/nonfinite JSON, malformed CSV, unexpected files,
symlinks, truncation, missing completion, changed receipts and inconsistent
metadata/counters are rejected. File-name patterns are not identity evidence.

The final campaign marker is published only after all 32 required authenticated
runs and resource checks succeed. A final size check precedes publication.
Interrupted, failed, preparing, running, missing or partially completed roots
are never analyzed as a complete pilot. Failures and partial logs remain in
place; there is no resume, skip, append, checkpoint or automatic rerun. Even a
completed simulator directory is insufficient without successful execution and
campaign receipts. Copies can be authenticated using their original approved
command identities plus their actual content hashes. Future analysis writes a
fresh file outside raw evidence and reauthenticates before publication.

## 5. Resource planning and unresolved budgets

Exact arithmetic gives **56,000 replica BD steps**, **75,264,000 bead updates**
and **131,200 expected hopping attempts**, over 32 runs. Each run retains 70
observer frames, 51 legacy scalar frames and six full-state audit snapshots.
The full plan has 4,302,784 CSV data rows. At an explicitly assumed 256 bytes/row,
this is 1,101,512,704 bytes (~1.026 GiB), excluding headers, JSON, binary/build
provenance, logs and analysis output. This is a planning estimate, **not a measured
size, compression prediction or execution cap**.

The largest explicit double device-array estimate is 303,964 bytes. The largest
legacy host-workspace estimate is 2,913,112 bytes, plus 39,936 observer vector
bytes. These are accepted allocation formulas, not total GPU memory or process
RSS: CUDA context, libraries, stream buffers, allocator and compiler storage add
costs. The observer adds no device array. Headroom/RSS budgets remain unknown.

Runtime has no defensible measured pilot estimate. Planning must include BD
updates, Z*nu*T attempts, serial renewal scans, synchronization, observation and
output costs, plus per-process CUDA startup/authentication. Hopping attempts per
physical time remain Z*nu at either dt; step-count savings need not translate
linearly to runtime. Earlier D1.0 four-chain technical timings and Stage C tiny
examples are not M64/N32/dense throughput benchmarks.

D0 candidate ceilings are retained (<=120 s/run, <=3600 s aggregate, <=5 GiB
aggregate output), but are **not active approval**. All eight actual budget
fields in `approval.template.json` are null: per-run/aggregate seconds and bytes,
minimum disk/GPU/host headroom, and maximum host RSS. Safe dedicated-host values
must be reviewed explicitly, including polling overshoot, CUDA startup/context,
analysis/provenance space and other workloads. The preflight refuses incomplete,
inconsistent or ceiling-exceeding limits instead of inventing permissive defaults.

## 6. Bounded tests actually executed

No 32-run pilot, large reference ensemble, production simulation or D2 trajectory
was run. Tests use analytical quadrature/enumeration, moment-balanced synthetic
data, deliberately biased synthetic data and tiny technical simulations:

| Check | Result |
|---|---|
| New CPU/synthetic/specification/supervision suite | 24 tests passed; 2.964 s in the final recorded run |
| Five-step authentication/analysis/legacy-output technical suite | 6 tests passed; 0.419 s |
| Exact manifest/schedules/seeds | Eight cells, four replicas, 32 unique seeds; all time maps exact; deterministic regeneration |
| Independent references | Radial quadrature, orientation transfer, finite covariance sizes, enumerated hypergeometric law, Gaussian CDF/overlap identities passed |
| Replica aggregation | Known SD/SE across R=4; independent contrasts, paired time changes, unbiased/specified synthetic means and deliberately shifted coarser means passed; no scientific acceptance inferred |
| Failure tests | Manifest/tool/schedule changes, duplicate/nonfinite JSON, corrupt/truncated/missing output, wrong seeds/parameters/GPU/schema, bad row/counter totals and interrupted receipts rejected |
| Supervision | Bounded CPU children: ordinary failure, per-run/aggregate timeout, output limit, interrupt cleanup and parent-death guard passed; no pilot flag set |
| Fresh build and preflight | Separate pinned-source double build tested; live read-only GPU/environment probe tested; approval/budget blockers remain |

The technical suite launches **only two N3,M4,Z4,5-step** double fixtures at
kappa10,dt=.0001,nu20000,A2=5,stride2,seed72103 (observer on/off). It verifies
real completed-state reconstruction, exact record counts, interval rebinning and
byte-identical legacy files/non-timing metadata. These are not matrix cells.
The 32-record synthetic aggregation/cohort-reader test contains no trajectories;
build/run readers are mocked only for cohort-completeness tests. An actual
per-run reader is separately tested with the five-step data. Synthetic approval
objects used inside unit tests are not executable approvals and are removed with
the isolated test directories.

Environment: Linux, g++11.4, CUDA13.0.88 and RTX3060Ti sm_86 for the bounded build/
GPU checks; Python3.10.12, NumPy2.2.4, one OpenBLAS thread. GPU tests/probes used
execution outside the sandbox to access the driver. All individual commands
were bounded below ten minutes. Compilation is actual, not inferred from an
installed toolkit or a no-op make. Existing simulator/checker/model/observer and
D0 authority files remain byte-identical to starting HEAD; historical roots and
authentication safeguards were preserved.

## 7. Reproducible preparation checks (safe now)

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 examples/slip-springs/tests/test_e1_d1_pilot.py -v
# Defaults to read-only; prints blockers and never creates a campaign root.
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 examples/slip-springs/e1_d1_pilot_runner.py
# Deterministic proposal generation into a NEW location; no authorization.
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 examples/slip-springs/e1_d1_pilot.py --freeze /tmp/e1-d11-config-review-new
```

The executed build used the isolated detached checkout `/tmp/e1-d11-source`:

```sh
git worktree add --detach /tmp/e1-d11-source 0dea651b58171a72206774bcebb2f4c74960069b
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 examples/slip-springs/e1_d1_pilot_runner.py build --manifest examples/slip-springs/e1_d1_pilot_config/manifest.json --manifest-sha256 a14612088cab809f101c22c5c60c1879a136e9383305980864c014cae899dc2f --source-tree /tmp/e1-d11-source --build-root /tmp/e1-d11-build-isolated --cuda-home /usr/local/cuda --arch sm_86
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 examples/slip-springs/tests/test_e1_d1_pilot_technical.py /tmp/e1-d11-build-isolated/bin/semiflexible -v
```

The build command uses the literal reviewed hash in section 1. Reproduction
needs new source/build paths if the above paths already exist. Build execution
has a 240-second technical timeout and runs no dynamics. A read-only preflight
with a real build uses `--build-receipt`, its `--build-sha256`, and `--gpu-uuid`;
without an approved record it still cannot launch. Read-only default output was
captured at `/tmp/e1-d11-default-preflight.json`; CPU/build/technical/live-probe
logs and exact tested binary/build hashes are recorded below. These `/tmp`
artifacts are local technical evidence, not a permanent scientific archive.

## 8. Required independent review and later execution

Before execution, review the frozen matrix/seeds, .01 cadence switch, first-step
handling, six audit states, reference/error budgets, exploratory estimator and
interval assumptions, and limitations of four replicas/short ACF support. Confirm
that the pilot addresses feasibility rather than confirmatory equivalence and
that D0 scientific margins remain unchanged. Independently review the runner,
authentication chain, serial operation, output inventory, failure/interrupt rules,
and dedicated-host resource ceilings/headroom. Accept the new tool/manifest
identities explicitly; do not relax historical campaign allowlists.

After **separate explicit authorization**, a human must copy the approval
template outside the frozen config, fill its review reference/output root/GPU,
manifest/build/environment hashes and every reviewed resource budget, and only
then set its `execution_authorized` to true. Hash that approved file externally.
A CLI flag alone is insufficient. Preserve both approval and final completion
hashes outside the raw evidence directory. The flag is shown below solely as
instructions for a later authorized task; it was not set here.

```sh
# Define these from independently reviewed records on the dedicated host:
# MANIFEST_SHA, BUILD_SHA, GPU_UUID, APPROVAL_SHA, and the fresh output root.
python3 examples/slip-springs/e1_d1_pilot_runner.py preflight --manifest examples/slip-springs/e1_d1_pilot_config/manifest.json --manifest-sha256 "$MANIFEST_SHA" --build-receipt /absolute/build/build.json --build-sha256 "$BUILD_SHA" --gpu-uuid "$GPU_UUID" --output-root /absolute/NEW-e1-d1-pilot
# Review the printed environment_sha256, then the completed approval file.
python3 examples/slip-springs/e1_d1_pilot_runner.py preflight --manifest-sha256 "$MANIFEST_SHA" --build-receipt /absolute/build/build.json --build-sha256 "$BUILD_SHA" --gpu-uuid "$GPU_UUID" --approval /absolute/reviewed-approval.json --approval-sha256 "$APPROVAL_SHA" --output-root /absolute/NEW-e1-d1-pilot
# ONLY after separate execution authorization and a clean preflight:
python3 examples/slip-springs/e1_d1_pilot_runner.py preflight --manifest-sha256 "$MANIFEST_SHA" --build-receipt /absolute/build/build.json --build-sha256 "$BUILD_SHA" --gpu-uuid "$GPU_UUID" --approval /absolute/reviewed-approval.json --approval-sha256 "$APPROVAL_SHA" --output-root /absolute/NEW-e1-d1-pilot --authorize-pilot-execution
```

The last command executes exactly the 32 serial replicas. If interrupted or
failed, keep the root untouched: do not rerun into it or assume resumption is
safe. Review any missing data/resource limit under a separately authorized
amendment. A successful runner prints `completion_sha256`; record it externally
as `COMPLETION_SHA`. Only then can independently authenticated exploratory
analysis be requested:

```sh
python3 examples/slip-springs/e1_d1_pilot_auth.py --manifest-sha256 "$MANIFEST_SHA" --campaign /absolute/NEW-e1-d1-pilot --approval-sha256 "$APPROVAL_SHA" --completion-sha256 "$COMPLETION_SHA"
python3 examples/slip-springs/e1_d1_pilot_analysis.py --manifest-sha256 "$MANIFEST_SHA" --campaign /absolute/NEW-e1-d1-pilot --approval-sha256 "$APPROVAL_SHA" --completion-sha256 "$COMPLETION_SHA" --output /absolute/NEW-exploratory-analysis.json
```

## 9. Remaining decisions

The frozen proposed inputs, software and bounded tests are reviewable. Actual
pilot feasibility/runtime/disk/RSS/GPU headroom and scientific timestep sensitivity
remain unmeasured. The approval template is deliberately incomplete. Four-replica
intervals, short-horizon preservation, late-time stationarity/IATs, rare-population
precision and exact per-ID renewal coverage remain limitations; none is a pass.
No production timestep is frozen, no pilot results exist, and D2 is not begun.

## Recorded preparation evidence

The final fresh build rechecked **1914 compilation dependencies** and **five
linked libraries**; its source checkout remained clean at accepted D1.0.

```text
build receipt SHA256 8a6a46a1bbe71dd6fe1c820a6d659536b45e3e3d0cef27f3e4fd2cf16c562d60
executable SHA256    a11a96a70a8961df62ce2fd59ae31874d0697c2b099e4420561964c5794c6846
development environment SHA256 05e9f076948c5d562925dd24b9d9d47bc8611698516efea13808029ad5d8c79a
```

The live preflight used the above receipt, manifest and
`--gpu-uuid GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274`, targeting the nonexistent
`/tmp/e1-d11-not-executed` root, without approval or execution flag. It reported
`independent approval and explicit resource budgets required`; the root was
verified still absent. It observed driver 580.178.04, CC8.6, 8-GiB total GPU
memory and about 8.07 GB free after the read-only context probe. These are
availability/provenance observations, not approved safety margins or pilot
resource measurements. The environment hash must be recaptured/reviewed on the
actual execution host; it is not authorization for this development host.

Executed bounded-command logs: `/tmp/e1-d11-cpu-final.log` (24 passed),
`/tmp/e1-d11-technical-final.log` (6 passed), `/tmp/e1-d11-build-isolated.log`,
`/tmp/e1-d11-build-isolated/{build.json,build.log}` and
`/tmp/e1-d11-live-preflight.json`; default preflight output is
`/tmp/e1-d11-default-preflight.json`. An initial fresh build and intermediate
CPU/technical checks were repeated after provenance/gate refinements. Only the
final identities above belong to the committed frozen proposal. There is no
pilot campaign-completion receipt or scientific analysis output to report.
