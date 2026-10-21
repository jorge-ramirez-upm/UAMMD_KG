# E1 Stage D1.4: Phase B preparation v1

Prepared 21 October 2026 from local and remote `slip-springs` HEAD
`50e5b50c794837e26d2ad6daf90cd410f4c8e2f6`. This is execution and analysis
software preparation. **No Phase B scientific trajectory was run and no Phase B
execution approval was created.** Phase C and D2 remain outside scope.

The E1 model, force, Brownian update, initializer, jump/renewal processor,
observer, RNG domains and historical authentication allowlists are unchanged.
The original D1.1, D1.2 and Phase A files and evidence remain frozen.
Scientific D0 tolerances and timestep proposals remain unchanged.

## Frozen execution specification

[e1_d14_phase_b_config/manifest.json](e1_d14_phase_b_config/manifest.json)
uses schema `e1-d14-phase-b-execution-v1`, campaign `e1-stage-d14-phase-b-v1`.
Its external SHA256 is:

```text
1fdb92b972137276fda6f1fc0b057192b3ee8afcb5eb345efd8c27c15f557f9a
```

The accepted D1.2 design SHA256 is
`2da957a5ee44956c395004bd20c23bee8e809b6d312ceee814e3f6934b2a5bbe`.
The new manifest authenticates that complete design, its Phase B proposal and
step-file bytes, accepted simulator files, all preparation/reference dependencies,
and the Phase A results and execution-reference index. It includes exact argv
substitution templates, schedules, expected schemas and record counts. Validation
recomputes the complete frozen specification; changed tools, source, parameters,
seeds or schedules require a separately reviewed version, rather than adoption
by changing only an external digest. Generation refuses an existing directory.

| Cell | N | kappa | Ne | nu_hop | dt | T | Steps per replica | Replica seeds |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| B1 | 32 | 0 | 4 | 100 | 0.0001 | 10 | 100000 | 721400101, 721400102 |
| B2 | 32 | 0 | 4 | 100 | 0.00025 | 10 | 40000 | 721400201, 721400202 |
| B3 | 32 | 10 | 4 | 100 | 0.0001 | 10 | 100000 | 721400301, 721400302 |
| B4 | 32 | 10 | 4 | 100 | 0.00025 | 10 | 40000 | 721400401, 721400402 |

All eight runs use M=64, Z=512, b0=1, kb=30, kBT=zeta=1, A2=5,
double precision, canonical end renewal on, stress off, and independent exact-E1
equilibrium initialization. These are the unchanged D1.2 seeds. No seeds,
initializations or RNG states are shared across cells or replicas. The manifest
has an empty pairing list. Run ordering is B1 replica 1,2 through B4 replica 1,2.
Total work is 560000 BD steps; expected attempts are
8*10*512*100 = 4096000. Density is Z/[M(N+1)] = 8/33, not 1/Ne.

## Exact observations and output

The six committed step files are copied byte for byte from D1.2 Phase B. Times
are rational step*dt identities; there is no interpolation or rounding.

| Schedule | dt=0.0001 steps | dt=0.00025 steps | Frames |
|---|---|---|---:|
| Regular scalar | 0,1000,...,100000 | 0,400,...,40000 | 101 |
| Full E1 | 0,1,5,25,100,500; then 5000,10000,...,100000 | 0,1,2,10,40,200; then 2000,4000,...,40000 | 26 |
| Audit snapshots | 0,1,100,100000 | 0,1,40,40000 | 4 |

Full E1 shared physical times are 0, .0005, .0025, .01, .05,
then .5,1,...,10. The timestep-specific first observations .0001 and .00025
are diagnostic only. Snapshots are initial, first step, .01 and final. Scalar
frames are 0,.1,...,10. Each replica has 106 distinct observation times;
105 are shared across timesteps. The final state is explicitly included.

The observer operates on the accepted completed state after BD and the entire
jump/renewal batch, with an initialized t=0 frame. No new observation semantics
were introduced. At scalar-only times the analyzer reads backbone quantities
only. It never carries forward springs or uses unsynchronized joint records.
Full E1 frames retain chain and spring identity in raw files; reductions retain
contour occupancy plus per-site ever-occupied coverage. Neither coverage nor .5
spacing establishes independent samples or complete renewal-history coverage.

Expected per-run data rows (headers excluded): samples 6464; initial/final
positions 2112 each; initial/final springs 512 each; fixed springs 512;
initial bonds and bond statistics 2048 each; supplemental equilibrium backbone
320; long tangents 1664; chain populations 1664; connectors 13312; sites 54912;
events 26; snapshot positions 8448; snapshot attachments 2048. All expected
schemas, headers, ordering, counts, schedules and completion sizes are checked.
Large raw tables stream with bounded per-frame storage. Analysis retains reduced
replica series; it does not archive new particle trajectories.

## Runner and trust policy

[e1_d14_phase_b_runner.py](e1_d14_phase_b_runner.py) binds private copies of the
accepted D1.3 orchestration and D1.1 build/supervision components to the new Phase
B specification and authentication module. Original imported Phase A globals
remain unchanged (regression tested). The wrapper accepts only the new
`--authorize-phase-b-execution` gate. After that check, an internal compatibility
field calls the reused orchestration; this does not expose a Phase A CLI bypass.
A Phase A approval/build manifest cannot authenticate the Phase B specification.

Default invocation is read-only. Execution needs both the Phase B CLI flag and
an independently approved, externally SHA256-bound record containing the exact
manifest, authenticated build, environment, GPU UUID, fresh evidence root,
approval reference and all eight reviewed resource limits. The committed
`approval.template.json` has `execution_authorized: false` and every limit null.
It is not executable authorization. Synthetic test approvals refer only to
fake nonexecutable build fixtures and temporary directories.

The reused runner requires a clean accepted scientific checkout and a real fresh
double CUDA13/sm86 build, fingerprints the compiler, dependency closure, linked
libraries and binary, restricts the child environment, rechecks host/GPU/disk
headroom and identities, executes serially, polls time/RSS/output ceilings and
terminates process groups on failure. Polling may overshoot a limit between
samples. Outputs use a fresh nonoverwriting root. Failures/interruption preserve
receipts and stop execution; there is no retry, resume or partial-data adoption.
Complete observer/schema checks and raw size/SHA256 authentication precede each
success receipt. Cohort completion requires all eight runs. The separate analyzer
requires externally supplied manifest, approval and completion SHA256 anchors,
authenticates the entire cohort before and after reading, and writes a fresh
analysis file outside raw evidence. Missing or altered evidence is rejected.
Phase B has no on/off replay pairs: its eight initializations are independent.

## Exact references and analysis definitions

[e1_d14_phase_b_analysis.py](e1_d14_phase_b_analysis.py) reuses the accepted
independent CPU references, not simulator calculations or fitted trajectories.
Radial quadrature evaluates the finite-rest-length bond distribution, including
the r^2 measure, with 128/256-node refinement. The stable Langevin function gives
h=L(kappa/kBT). With radial moments mu1,mu2,

```text
Ct(s) = h^s
B(d) = d*mu2 + 2*mu1^2 * sum(s=1..d-1) (d-s)*h^s
<Ee^2> = B(N)
<Rg^2> = sum(d=1..N) (N+1-d)*B(d)/(N+1)^2
```

Reference values for this matrix are mu1=1.064516129079,
mu2=1.164516129079, h=0 (flexible) or .9000000041223 (kappa10).
Re2 targets are 37.26451613052 and 493.0134446496; Rg2 targets are
6.398957315341 and 58.87828323855. Tangent separations 1,2,3,4,8,16 are
reported wherever recorded; 8/16 exist only on full E1 frames.

Canonical populations use the exact hypergeometric law over 2112 sites with
512 occupied sites. E[Zc]=8, Var(Zc)=5.968735196589, and occupancy=8/33.
Connector components have zero mean and variance 5/3; e2 has mean 5 and scaled
chi-square(3) CDF. Analysis reports component moments/cross moments, connector
and component CDFs at the nine accepted fixed quantiles, contour occupancy,
population PMF/CDF/variance and occupancy coverage. Raw site identities remain
available for independent verification.

For f_c=Re_c^2/<Re^2>-1, sigma_Z^2=Var(Zc), the unchanged D0 joints are

```text
A_joint = sum_c f_c*(Zc-Z/M)/(M*sigma_Z)
B_joint = sum_c f_c*(sum_s_on_c e_s^2 - A2*Zc)/(Z*A2)
```

Both reference means are zero. Only synchronous full frames enter these
statistics. Empty and multiply occupied chains are preserved, not dropped.

Independent equilibrium event predictions reuse radial Gaussian Metropolis
overlap integration and exact single-occupancy combinatorics. With L=M(N+1),
v=(L-Z)/(L-1), J=E_radial[erfc(r/(2*sqrt(2*A2/3)))],
accepted interior rate is Z*nu*N/(N+1)*v*J and accepted renewal rate is
Z*nu/(N+1)*(2*M-1)/(2*M)*v. Here attempts=51200, accepted interior
=25620.15961638 and accepted renewals=1166.759973013 per physical time.
Rejected/accepted renewal, same/cross-chain and interior rejection categories are
also retained. These are equilibrium continuous-time reference frequencies,
not acceptance gates for the finite-dt splitting process.

Every frame reduces the complete 64-chain replica first. For each observable,
retain individual replicas, t=0/reference deviations, time-resolved means and SD,
within-replica changes from t=0, predefined early/late differences, temporal
ranges and shared-time coarse-minus-fine contrasts. Event rates are interval
counts/duration; their t=0 and change-from-t=0 are undefined/null. First-step
counter deltas are summed into the next shared interval, never lost or divided
by an incorrect time interval.

The primary independent sample size is two. SD uses ddof=1; exploratory
pointwise mean intervals use t1=12.706204736 times SD/sqrt(2). Cross-timestep
contrasts use independent replica variances and this conservative critical value;
no cross-cell pairing or four-replica t3 calculation is used. Such nominal
intervals have weak support and no guaranteed coverage for skewed two-replica
estimators; zero observed SD is explicitly flagged, not proof of precision.
Individual replica values accompany aggregates. There is no scientific pass/fail,
equivalence decision, burn-in removal, retuned D0 margin or endpoint-only verdict.
Synthetic transient bias returning to zero at the final frame remains visible.

Early and late windows are fixed before data: scalar 0..1 versus 9..10 (11
regular frames each); static E1/long tangents use .5 grids (3 frames each);
event rates sum exact deltas into uniform .5 bins and compare (0,1] versus
(9,10] (2 bins each). No frame count is used as replica count.

Preliminary demeaned ACFs use the exact .1 scalar grid (101 samples, 10 units)
and .5 static E1 grid (21 samples, 10 units); interval rates use 20 disjoint .5
bins (9.5-unit support between bin endpoints). Irregular early frames are excluded
from uniform estimators. At most min(20,floor(n/4)) lags are displayed: 2 units
for scalar and 2.5 for E1/rates. Output includes variance, decay shape, observed
crossing below .2 and support, with an unresolved-tail warning. Constant/short
series are explicitly unsupported. All IATs remain null and independence is never
established automatically; apparent decay does not establish stationarity,
terminal relaxation or a reliably resolved long-time tail.

## Bounded verification actually performed

All commands used PYTHONDONTWRITEBYTECODE=1, OPENBLAS_NUM_THREADS=1 and bounded
timeouts. Fresh-source compilation took 18.403 s; no T=10 process was launched.

| Suite | Result | Elapsed |
|---|---|---:|
| New Phase B CPU/synthetic plus independent reference tests | 19 passed | 14.160 s |
| New tiny GPU reader/schema/reconstruction tests | 4 passed | .626 s |
| Unchanged D1.3 CPU regression | 11 passed | 8.147 s |
| Unchanged D1.1 CPU regression, rerun | 24 passed | 2.570 s |
| Unchanged D1.2 planning regression | 6 passed | .949 s |

The first D1.1 invocation passed 23 tests and hit ProcessLookupError reading
`/proc/<pid>/status` after its short-lived test child disappeared. The unchanged
suite passed on rerun; both logs are preserved. No production or frozen test was
altered to hide this historical test race.

New tests cover exact matrix/seeds/parent bytes, reproducible manifests,
false/null gates, source/build/binary/compiler/GPU/environment mismatches,
whole-cohort failures, missing/corrupt/incomplete/interrupted evidence, mock serial
completion/failure, counter interval summation, R=2 estimators, shared-time
contrasts, windows, transient/drifting biases, zero joints and deliberate joint
bias, exact ACF grids and constant-series handling. Deterministic reduced-series
oracles at reference targets test software arithmetic, not statistical acceptance
of sampled equilibrium ensembles. Independent quadrature, orientation transfer,
finite-chain covariance and enumerated hypergeometric tests verify the references.

GPU fixtures were only N3/M4/kappa0 and N17/M2/kappa10, each Z4 and nine steps,
with accepted algorithms and high attempt rate to exercise events. They verify
t=0, scalar-only frames, long tangents, final inclusion, independent snapshot
reconstruction of backbone/connectors/joints, occupancy and population conservation,
raw hashes and completion failures. The two fixtures were checked using the prior
accepted binary and then the fresh build (four tiny processes total, 36 BD steps).
No new on/off physical replay suite or sanitizer campaign was needed: no simulator
or observer source changed, and accepted D1.0/D1.3 byte-identity evidence remains
applicable within its established scope. This does not extend scientific acceptance.

## Build and live read-only preflight

The source remains clean at accepted scientific SHA
`0dea651b58171a72206774bcebb2f4c74960069b` in `/tmp/e1-d11-source`.
The new authenticated build is `/tmp/e1-d14-build/build.json`:

```text
build receipt SHA256 79a9dca3f43e5982abe1e21c828d70ef008bc2e2026bf43e05e9bd05f289d7d5
executable SHA256    45876d8b61150b6259236d31e7a2d0f5f1418f710f444430b8fd4fbd4c8eb063
environment SHA256   05e9f076948c5d562925dd24b9d9d47bc8611698516efea13808029ad5d8c79a
```

Binary size is 2709792 bytes; real compilation records 1914 dependencies and five
linked libraries, nvcc13.0.88, GNU g++11.4.0, double precision and sm86. A new
binary digest is expected for a distinct fresh build; it does not imply changed
scientific source. The complete receipt is required, not merely these strings.

Live preflight `/tmp/e1-d14-live-preflight.json` authenticated RTX3060Ti,
UUID `GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274`, CC8.6, driver580.178.04,
CUDA runtime/driver API13000. Observed free GPU was 8072724480 B, available host
30364889088 B and free disk 1247423946752 B. These are momentary availability
measurements, not safety budgets or process peak measurements. Its sole blocker
was independent approval and explicit resource budgets. The proposed output
`/tmp/e1-d14-phase-b-NOT-EXECUTED` was not created.

[e1_d14_preparation_receipts.json](e1_d14_preparation_receipts.json) preserves
selected measured fields and hashes/paths of the build, live preflight and test
logs. Its SHA256 is
`8e4b20296f22267e574cc58b2f49154d43ff97ff1e3541a83a37627438b01d9c`.
Large build artifacts and transient fixture CSVs are not committed.

## Resource planning and remaining approval gates

Phase A sparse N32/kappa10 production times .302015702 and .163777670 s give
40-fold work proxies 12.0806 s fine and 6.5511 s coarse. Applying these to all
four fine/four coarse runs gives 74.53 s total production as a planning proxy.
N32/kappa0 was not benchmarked; event processing, diagnostics, disk and host
load may alter this. Full-process time adds startup, initialization and teardown.
Phase A child-wall total was 2.936 s versus 1.375 s production; campaign wall
16.351 s also included about 13.415 s beyond children, including authentication
and orchestration. These scopes overlap; they are not all additive timers or a
40-fold runtime law. Allow several minutes operationally, pending actual review;
no Phase B duration is measured or guaranteed. Two complete analysis authentication
passes, larger files and the new analysis add CPU/I/O overhead not yet benchmarked
on a real Phase B cohort.

D1.2 projects raw CSV 63281008 nominal to 70055040 wide bytes, plus 16 MiB
run-provenance/log allowance and 64 MiB shared build provenance: 140.35–146.81
MiB. The deterministic drifting analysis-oracle JSON serialized to 32763132 B
(31.25 MiB; actual numbers/metadata can differ). A working total near 180 MiB,
with review headroom, remains well below 1 GiB. It is not an observed Phase B
size or permission to discard verification data. Raw schemas and field-based
D1.2 estimates are preserved unchanged.

Explicit state arrays are about 304 kB device, 2913112 B estimated legacy host
workspace and 39936 B observer vectors per run. Phase A peak host RSS was
106229760 B; GPU free-memory readings did not measure peak process allocation.
CUDA context/allocator use, longer-time behavior and analysis memory remain
unmeasured for Phase B. Only one process may run at once.

For a subsequent safety review, retaining the conservative Phase A ceilings is
a reasonable **unapproved recommendation**: 120 s/run, 3600 s aggregate,
128 MiB/run output, 1 GiB aggregate output, 2 GiB max host RSS, 8 GiB available
host, 4 GiB free GPU and 10 GiB free disk. Compatibility validators retain the
accepted outer budget restrictions. No such values have been inserted into the
Phase B template; all eight executable limits remain null. Review must freeze
these or other permissible exact limits, evidence root, build and live environment
and issue a new SHA-bound Phase B approval. Phase A approval is insufficient.
Phase C requires separate scientific design/resource authorization after B review.

## Reproducible preparation and separate future execution

From the repository root (each test bounded by 120 s):

```sh
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 examples/slip-springs/e1_d14_phase_b_runner.py
python3 examples/slip-springs/e1_d14_phase_b.py --freeze /tmp/e1-d14-review-copy
sha256sum /tmp/e1-d14-review-copy/manifest.json
for suite in test_e1_d14_phase_b test_e1_d13_phase_a test_e1_d1_pilot test_e1_d12_plan; do
  timeout 120s python3 examples/slip-springs/tests/$suite.py -v
done
# Use a fresh, nonexistent build root for reproduction:
timeout 300s python3 examples/slip-springs/e1_d14_phase_b_runner.py build \
  --source-tree /tmp/e1-d11-source --build-root /tmp/e1-d14-build-review \
  --cuda-home /usr/local/cuda --arch sm_86 --cxx /usr/bin/g++
timeout 120s python3 examples/slip-springs/tests/test_e1_d14_phase_b_technical.py \
  /tmp/e1-d14-build-review/bin/semiflexible -v
python3 examples/slip-springs/e1_d14_phase_b_runner.py preflight \
  --build-receipt /tmp/e1-d14-build/build.json \
  --build-sha256 79a9dca3f43e5982abe1e21c828d70ef008bc2e2026bf43e05e9bd05f289d7d5 \
  --gpu-uuid GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 \
  --output-root /tmp/e1-d14-phase-b-NOT-EXECUTED
```

The executed build used `/tmp/e1-d14-build`, and fixture validation used its
binary; the fresh `-review` path above is for safe reproduction. The same CPU
suite commands generated the recorded logs. Do not regenerate over frozen files.

Only after separate user approval: copy the false template outside frozen
configuration, fill approved identities/root/all limits, externally preserve its
SHA256, run `preflight` with `--approval` and `--approval-sha256` plus the above
build/GPU fields, inspect every blocker, then explicitly add
`--authorize-phase-b-execution`. This task did not issue that command. Upon
complete success, externally record the completion SHA256 and invoke:

```sh
python3 examples/slip-springs/e1_d14_phase_b_analysis.py \
  --campaign /APPROVED/FRESH/EVIDENCE --output /FRESH/EXTERNAL/analysis.json \
  --manifest-sha256 1fdb92b972137276fda6f1fc0b057192b3ee8afcb5eb345efd8c27c15f557f9a \
  --approval-sha256 APPROVED_EXTERNAL_SHA --completion-sha256 EXTERNAL_COMPLETION_SHA
```

No Phase B approval, scientific preservation conclusion, timestep acceptance,
long-time independence, terminal dynamics or rheological inference follows from
this preparation or from Phase A timing evidence.
