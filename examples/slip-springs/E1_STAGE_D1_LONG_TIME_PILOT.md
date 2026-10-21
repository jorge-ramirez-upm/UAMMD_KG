# E1 Stage D1.2 — long-time pilot design v1

Prepared on `slip-springs` from local and remote HEAD
`c2fc9c537263b801ace93c9386bca4f62f6f7753`, verified before edits.
**Proposal preparation only: no phase is authorized and no scientific simulation
was executed.** The D1.1 framework is accepted, but its T=.25, 32-run scientific
proposal remains unapproved. D1.2 replaces that execution proposal prospectively;
it does not rewrite its manifest, schedules, reports, source identities or data.

Authority reviewed: [D0/D0.1 protocol](E1_STAGE_D_VALIDATION_PROTOCOL.md),
[timestep screen](E1_STAGE_D_TIMESTEP_SCREENING.md),
[observer acceptance](E1_STAGE_D1_OBSERVER_REPORT.md),
[D1.1 preparation](E1_STAGE_D1_PILOT_PREPARATION.md), E1 model, Stage C,
backbone authority, project rules/status/roadmap, and the actual observer,
checker, specification, runner, authentication and analysis implementations.
D0 scientific margins and proposed timesteps are unchanged. Local curvature
screening does not validate equilibrium or dynamical accuracy.

## 1. Separate proposed phases and parameter matrices

Common settings: M=64, b0=1,kb=30,kBT=zeta=1,A2=5, double precision,
end renewal on, stress off, full scalar schema, independent exact-equilibrium
initialization. Z=round_half_up(M*N/Ne); rho=Z/[M(N+1)]. The target for Phase A
is an RTX 3060 Ti (sm_86) with CUDA 13; actual GPU UUID, compiler/runtime versions,
architecture and free resources must be authenticated at execution.

### Phase A: performance and output benchmark proposal

| Cell | N | kappa | Ne | nu_hop | dt | Z | rho | T | BD steps/profile |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 1 | 8 | 0 | 16 | 10 | .0001 | 32 | 1/18 | .25 | 2500 |
| 2 | 8 | 0 | 16 | 10 | .00025 | 32 | 1/18 | .25 | 1000 |
| 3 | 32 | 10 | 4 | 100 | .0001 | 512 | 8/33 | .25 | 2500 |
| 4 | 32 | 10 | 4 | 100 | .00025 | 512 | 8/33 | .25 | 1000 |

One deliberately paired observer-off/observer-sparse replay per cell: eight
processes, four physical initializations. Both profiles retain the .1 scalar
stride. Off omits only the opt-in equilibrium observer. Pairing is for physical
replay and descriptive overhead comparison, not eight independent scientific
replicas. These extremes bracket size, stiffness, density and event rate;
they do not identify separate performance effects of those factors. No repeats
or extra cells are implicit. If one pair is too noisy, another benchmark needs
review rather than automatic expansion.

Measure actual initialization, production/integration and overall wall seconds,
seconds/BD step, attempts and accepted events/second, recurrent scalar costs,
observer exclusive/transfer/wall timers, bytes by file and peak host/GPU use.
Timer scopes overlap: do not add observer wall to production time or interpret
integration timers as an isolated hopping-kernel timer. Attempts/production-wall
is end-to-end event throughput; existing counters do not isolate serial hopping
kernel time. Paired wall differences include startup/timing noise. Preserve both
profiles' hashes and compare physical outputs before interpreting overhead.
No equilibrium acceptance claims come from this short benchmark.

### Phase B: initial longer-time scientific pilot proposal

| Cell | N | kappa | Ne | nu_hop | dt | Z | rho | Candidate T | Steps/replica | Replicas |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 1 | 32 | 0 | 4 | 100 | .0001 | 512 | 8/33 | 10 | 100000 | 2 |
| 2 | 32 | 0 | 4 | 100 | .00025 | 512 | 8/33 | 10 | 40000 | 2 |
| 3 | 32 | 10 | 4 | 100 | .0001 | 512 | 8/33 | 10 | 100000 | 2 |
| 4 | 32 | 10 | 4 | 100 | .00025 | 512 | 8/33 | 10 | 40000 | 2 |

Eight independent replica-runs; no cross-dt initial-state sharing. Choosing the
same longer N and density/rate for flexible/stiff comparisons avoids confounding
stiffness with N, Ne or nu. This sentinel subset does not cover N8 equilibrium,
intermediate stiffness, dilute populations or low hopping rates. It explores
drift and temporal resolution, not convergence or reliable independence.
Two replicas are deliberately limited feasibility evidence, not adequate power
for D0 confirmatory equivalence.

### Phase C: preservation planning envelope, not a selected campaign

The four proposed physical cells are exactly Phase B's four rows. For storage
and work estimates only, use T=100 and R=2 per cell (1000000/400000 steps per
replica, eight runs). **Actual T>=100 and actual R are unselected**: the separate
Phase C proposal leaves `frozen_execution_T` and `frozen_execution_replicas`
null. A/B reviews must choose horizon, replica count, temporal resolution and
budgets, then create a new frozen execution manifest with those decisions and
A/B evidence hashes. Longer T or more replicas require new estimates; neither
is an automatic escalation. Exact-equilibrium initialization remains mandatory.
A longer exact-start preservation run is not a D2 convergence experiment.

| Phase/envelope | Processes | Sum physical time | Replica BD steps | Bead updates | Expected attempts |
|---|---:|---:|---:|---:|---:|
| A, both profiles | 8 | 2 | 14000 | 18816000 | 51520 |
| B | 8 | 80 | 560000 | 1182720000 | 4096000 |
| C planning only | 8 | 800 | 5600000 | 11827200000 | 40960000 |

Expected attempts/run are Z*nu*T: A's small/dense cases 80/12800, B 512000,
C 5120000. The coarse dt cuts BD steps by 60%, but leaves attempts/physical time
Z*nu unchanged. Serial event processing, renewal scans, invariant checks,
readbacks and diagnostics may dominate. Runtime cannot be extrapolated linearly
from BD step reduction or from four-chain technical fixtures. No runtime budget
or benchmark result is invented here.

## 2. Exact independent observation schedules

No instrumentation extension is required. The accepted driver already calls
`observe(step, regular)` on the union of `--sample` multiples and
`--equilibrium-steps`. Only the `eq` branch reads spring slots, occupancy,
anchors and event counters. Scalar-only observations reuse existing reductions
and `samples.csv`; they do not create connector/site rows. Full E1 observations
reuse those scalar rows when coincident, otherwise write
`equilibrium_backbone.csv`. They all use the completed post-BD/post-jump state;
step zero precedes all dynamics. No RNG, kernel, force, event ordering or
accepted observer implementation changed.

Let end=T/dt exactly. Scalar steps are `0,stride,2*stride,...<=end`, where
stride=.1/dt. Full E1 shared times are the union of:

- t=0,.0005,.0025,.01,.05 (predefined early diagnostics);
- .5,1,1.5,...<=T (candidate sparse cadence);
- t=T (explicit final record, including Phase A's off-cadence .25).

Also retain step 1 at each dt as a **timestep-specific diagnostic**, never a
shared-time comparison. The full schedule is the sorted unique union. Audit
snapshots are exactly t=0, that dt's first step, .01 and T (four, below cap eight),
synchronized with complete E1 observations. Initial/final legacy state files
remain, so a few endpoint copies are intentionally retained for authentication.
There is no full particle trajectory or per-step connector archive.

| Quantity | dt=.0001 | dt=.00025 |
|---|---|---|
| Scalar stride (.1) | 1000 steps | 400 steps |
| Full E1 stride (.5) | 5000 steps | 2000 steps |
| Shared early steps | 0,5,25,100,500 | 0,2,10,40,200 |
| Extra first-step diagnostic | 1 (t=.0001) | 1 (t=.00025) |
| Snapshots | 0,1,100,end | 0,1,40,end |
| A end | 2500 | 1000 |
| B end | 100000 | 40000 |
| C planning end | 1000000 | 400000 |

| T | Regular scalar frames | Full E1 frames | Extra backbone frames | Snapshots |
|---:|---:|---:|---:|---:|
| .25 | 3 (0,.1,.2) | 7 | 6 | 4 |
| 10 | 101 | 26 | 5 | 4 |
| 100 | 1001 | 206 | 5 | 4 |

At .25 the final backbone record is supplementary, not a silently rounded scalar
stride. For T10/100 the full cadence coincides with every fifth scalar frame.
Tangent separations 1–4 are available at all backbone frames; N32's 8 and 16 are
recorded only at full E1 frames by the accepted observer. Long-tangent ACFs thus
have .5 late spacing. If A/B review needs those at .1, separately review a
minimal host-side extension; do not claim existing long-tangent rows at .1.

`e1_d12_plan.py` uses exact rational conversion and rejects a noninteger T/dt or
requested cadence/time/dt. For example t=.0001 is unrepresentable at .00025 and
cannot be a shared observation. Explicit integer `.scalar.steps`, `.full.steps`
and `.snapshots.steps` files are generated/authenticated for each phase/dt.
The scalar list is an audit of `--sample`, not an unsupported simulator flag.
Do not interpolate or silently round. Physical identity is the integer step
and exact dt; serialized binary-double time is checked as step*dt, not used as
an equality key across dt. The simulator validates schedule order, uniqueness,
range, endpoints and snapshot membership before running. It streams frames with
memory independent of their number; no new per-frame device allocation.

## 3. Scientific analysis and uncertainty contract

Retain the independent whole 64-chain replica as the primary uncertainty unit.
No chain, component, spring, frame or overlapping window increases R. Phase A
on/off pairs are technical replays only. B/C seeds differ across timesteps;
contrasts between dt use independent-replica variances. Time differences from
initial state within one replica are paired. Seeds are deterministic:
`721200000 + 100000*phase_number + 100*cell + replica`, with phase numbers 1–3.
Only Phase A's two profiles reuse a seed; phases, cells and replicas otherwise
do not. All proposed IDs and seeds are explicit in the phase JSON files.
Phase C seed assignments are planning reservations, not permission to launch.

Reduce each replica first, retaining per-chain raw data for verification:

- At each backbone time: means of Re², Rg², bond length/length², minimum lengths
  and tangent correlations 1–4. Use long tangents only where actually recorded.
  `bond_statistics.csv` is a final-half histogram summary, not a drift series;
  use time-resolved per-chain scalar moments for drift.
- At full E1 times: connector squared extension, Cartesian means, second/centered
  and off-diagonal moments, fixed theoretical connector CDF cuts; contour-site
  occupancy by chain/site, chain-population PMF/CDF and variance. Preserve empty,
  single and multiple populations. Use all live connectors, not renewal-selected
  connectors. Report scheduled site/chain coverage and renewal counts; per-ID
  renewal histories are unavailable and must not be inferred.
- Joint diagnostics use only synchronous per-chain Re², Zc and connector sums:
  `f_c=Re²_c/<Re²>_bb-1`,
  `A_joint=sum_c f_c*(Zc-Z/M)/(M*sqrt(Var(Zc)))`,
  `B_joint=sum_c f_c*(sum_on_c e²-Zc*A2)/(Z*A2)`.
  Both targets are zero. Never carry the last spring frame forward onto a .1
  scalar-only frame. Retain optional size comparisons conditional on Zc=0,1,>=2,
  marking unsupported rare groups rather than pooling them as independent units.
- Event rates use summed counter deltas divided by shared physical intervals.
  The first shared interval includes the intervening dt-specific first-step
  delta. Preserve interior acceptance/boundary/occupancy/Metropolis and renewal
  proposed/accepted/occupied/same-chain/cross-chain semantics. Do not independently
  Poisson-model accepted counts or rename boundary proposals as accepted hops.

Use the independently tested D1.1 reference functions without fitting targets:
radial moments mu1/mu2, h=coth(kappa)-1/kappa (h=0 for kappa=0), C_t(s)=h^s,
B(d)=d*mu2+2*mu1²*sum_(s<d)(d-s)*h^s,
Re²=B(N), Rg²=sum_(d=1)^N (N+1-d)*B(d)/(N+1)².
The exact population PMF is
`C(N+1,z)*C((M-1)(N+1),Z-z)/C(M(N+1),Z)`.
Connectors are Gaussian with component variance A2/3 and mean e²=A2=5;
site mean rho and D0 ideal continuous-time event references remain unchanged.
Reference uncertainty and tail coverage remain separate review obligations.
No large reference ensemble or fitted size-CDF threshold is introduced here.

Report replica means, SD (ddof=1), differences from analytical targets, independent
cross-dt contrasts, paired time changes and ranges over time. With R=2, any
nominal 95% t interval has df=1 (critical ~12.706), so it can be extremely wide;
D1.1's hard-coded t3 aggregation must not be reused for these replicas. Do not
claim equivalence, narrow precision, convergence or that zero observed variance
proves accuracy. D0 §7 margins, stricter timestep contrasts, reference-error
budgets and confirmatory power/replica requirements remain unchanged. Pilot
results cannot relax them.

Examine per-replica scalar ACFs on the regular .1 grid and E1 ACFs on the late
regular .5 grid, separately from irregular early diagnostics. At T10 this gives
only 101 and 21 regular points; at T100, 1001 and 201. Estimate uncertainty and
inspect decay, drift and lag truncation before any tentative IAT. A .5 grid can
miss fast decay and make an IAT unidentifiable even if it suffices for static
means; unresolved slow tails also prevent reliable IATs. Do not concatenate
replicas or treat spacing .5 as independence. A/B review chooses later spacing
from this evidence, potentially through a separately approved finer technical
observation study. No finite horizon alone establishes long-time independence.

## 4. Versioning, authentication and execution boundary

New design: [e1_d12_proposed_config/design.json](e1_d12_proposed_config/design.json)
(schema `e1-d12-design-v1`), SHA256:

```text
2da957a5ee44956c395004bd20c23bee8e809b6d312ceee814e3f6934b2a5bbe
```

Each phase has its own `proposal.json` (`e1-d12-proposal-v1`), six explicit step
files, counts and per-file storage model. The index hashes all 21 phase files,
the generator, calibration and accepted model/observer/source authorities. It
also binds all four frozen D1.1 modules and all seven D1.1 configuration files
to their bytes at starting SHA. D1.1 manifest SHA remains:

```text
a14612088cab809f101c22c5c60c1879a136e9383305980864c014cae899dc2f
```

Generation refuses overwrite. Verification requires the externally recorded
design SHA and exact deterministic content, rejecting missing/extra/changed files
and symlinks. These are authenticated **proposals**, not execution receipts.
`execution_authorized:false`, all eight budget fields null, and null execution
T/R occur separately in every phase. The generator has no execution command or
authorization switch. No executable authorization flag was set in this task.

The frozen D1.1 runner correctly accepts only its original 32-run manifest;
its analysis hard-codes that schedule, four replicas and t3 intervals.
**Do not pass D1.2 files to that runner/analyzer, edit its frozen hashes, or use
its default command to execute D1.2.** This task deliberately adds no new runner
or scientific data consumer. Minimum future compatible work, before any phase
execution, is a separately reviewed D1.2 adapter reusing the existing build,
process supervision, per-run checker and provenance helpers, while accepting
only one externally approved frozen phase manifest. Its analyzer must stream
all scalar rows independently, join spring/joint records only at full times,
use actual R for uncertainty and verify each complete phase cohort. The existing
generic per-run authentication already accepts explicit observation/snapshot
lists and sample stride; scientific cohort and aggregation logic must change.
This is an explicit implementation/review gate, not an implied ready-to-run claim.

The future adapter must preserve every existing fail-closed safeguard: clean
accepted simulator source `0dea651b58171a72206774bcebb2f4c74960069b` and repository
identity; real double build/dependency/toolchain receipt and binary SHA; runtime
GPU UUID/architecture/environment; externally trusted manifest/schedule, approval
and completion hashes; exact parameters/seeds/profiles; raw sizes/SHA256,
schema/header/full schedule/counts, endpoint reconstruction, duration/counter
identities; complete simulator and whole-phase markers. Missing, malformed,
nonfinite, truncated, interrupted or inconsistent data cannot enter analysis.
A checksum beside unauthenticated data is not its own trust anchor.

Execution requires separate user approval for **each** phase, a reviewed frozen
exact matrix/T/R/schedules, signed-off physical GPU/build/environment identities,
fresh nonoverwriting output root, serial replicas, all per-run and aggregate
wall/output/RSS/headroom limits and an explicit runner execution flag. No automatic
resume, partial-run adoption, phase chaining or physical-parameter changes to
meet a budget. Preserve failures/logs and reject partial analysis. Historical
campaign allowlists and frozen evidence are unchanged; D1.2 roots must be
separate. No runnable scientific execution instruction exists until the adapter
and that phase's exact budgets/manifest are independently accepted.

## 5. Storage model and projections

All estimates are uncompressed ASCII and count actual v1 schema fields, commas,
newlines and header bytes. [e1_d12_schema_calibration.json](e1_d12_schema_calibration.json)
records headers, row/file sizes and SHA256 from an existing D1.0 double technical
fixture (N32,kappa10,M4,Z6,12 steps); no new ensemble was generated. Typical
measured row lengths were: samples 222 B, supplementary backbone 196.8 B,
long tangents 61.5 B, sites 25.5 B, connectors 102.9 B, chain sums 64.8 B,
events 60 B, positions 80.6 B and attachments 87.9 B. Small IDs/times, zero values
and empty chains make direct reuse of those means optimistic for M64/long T.

The prospective model therefore uses **21 characters per real field**, exact
maximum decimal widths for step/chain/bead/spring/link/population IDs, and
explicit per-run count widths. For event counters the nominal width is the
larger of BD steps and twice expected whole-run attempts plus 100, even though
rows normally contain interval counts. The separate wide envelope uses 24
characters for real fields (including signed finite IEEE double at precision17)
and 20 for event counters (unsigned64); count widths for the 33 histogram bins
allow up to all scalar frames. Coordinate `z` is real, population `z` integer.
These are transparent planning models, not measured sizes or hard quotas;
Poisson counts have no deterministic bound from their expectation. JSON/logs
are estimated separately. `projection()` exposes every file's columns, rows,
row bytes and total bytes, so the estimates can be independently recomputed.

Example nominal N32,M64,Z512,T100,dt=.0001 field/row accounting:

| Stream | Columns | Rows | Model bytes/row |
|---|---:|---:|---:|
| samples | 14: step,time,chain + 7 scalars + 4 tangents | 64064 | 275 |
| supplementary backbone | 12: step,time,chain + 5 scalars + 4 tangents | 320 | 231 |
| long tangents | 5: step,time,chain,tangent8,tangent16 | 13184 | 77 |
| sites | 5: step,time,chain,bead,spring | 435072 | 40 |
| connectors | 9: step,time,spring,chain,bead,ex,ey,ez,e2 | 105472 | 128 |
| chain sums | 8: step,time,chain,z,ex_sum,ey_sum,ez_sum,e2_sum | 13184 | 124 |
| event deltas | 15: step,time,previous_step,interval_time + 11 counters | 206 | 159 |
| audit positions | 7: step,time,chain,bead,x,y,z | 8448 | 102 |
| audit attachments | 10: step,time,spring,chain,bead,ax,ay,az,previous,next | 2048 | 114 |
| bond summary | 38: chain,bond,frames,mean_r,mean_r2 + 33 bins | 2048 | 220 |

Existing fixed-size endpoint files are retained: two L-row coordinate files,
MN initial bond lengths, Z fixed anchors and two Z-row spring states. Initial
bonds and final bond histogram summaries are included in the backbone category.
There are no missing per-step particle rows hidden in these totals.

Per-replica N32,Z512 projections, identical for flexible/stiff field counts;
bytes include CSV headers:

| T | dt | Backbone scalars/tangents/bonds | Sites/connectors/chain sums/events | Audit snapshots | Legacy endpoint states | CSV total | Wide CSV total |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | .0001 | 2409937 | 4040957 | 1084750 | 418924 | 7954568 | 8801322 |
| 10 | .00025 | 2401489 | 3971017 | 1074254 | 418924 | 7865684 | 8712438 |
| 100 | .0001 | 19215057 | 32571163 | 1095246 | 418924 | 53300390 | 59044658 |
| 100 | .00025 | 19137489 | 32017023 | 1084750 | 418924 | 52658186 | 58402454 |

Physical times/frame counts match across dt, so the small size difference comes
from wider integer step fields, not fewer observations at the coarse dt.
Provenance/checksum/log planning allowances: 2 MiB per process for raw JSON,
receipts, checksum inventories, stdout/stderr and reduced exploratory reports,
plus 64 MiB campaign-wide for binary/build/dependency/environment evidence and
configuration. Existing technical raw JSON totals 3484 B and the authenticated
D1.1 double binary is 2709792 B, supporting these deliberately larger allowances;
Phase A must measure actual values. These are **not approved resource limits**.

| Phase/envelope | CSV nominal bytes | CSV wide bytes | Per-run provenance/log allowance (all runs) | Shared build/provenance allowance | Total nominal / wide MiB |
|---|---:|---:|---:|---:|---:|
| A | 9514112 | 10537230 | 16777216 | 67108864 | 89.07 / 90.05 |
| B | 63281008 | 70055040 | 16777216 | 67108864 | 140.35 / 146.81 |
| C, R2/T100 planning | 423834304 | 469788448 | 16777216 | 67108864 | 484.20 / 528.03 |

The eight-run T100 envelope is about .47 GiB nominal or .52 GiB wide, well under
the 1 GiB design target without compression or omitted scientific E1 records.
Storage for R, T or grids chosen later must be recalculated; doubling R is not
implicitly approved and would approach/exceed this target with overheads.
No limits are relaxed to fit estimates. Redundant audits/checksums stay intact.

Largest explicit double device arrays for the dense stiff case are 304228 B;
legacy host workspace estimate 2913112 B, observer vector payload 39936 B.
The observer adds zero device arrays. These are allocation formulas, not total
GPU use or RSS: CUDA context, libraries, allocators and output buffers add costs.
Frame streaming remains O(beads+springs), with legacy fixed per-bond histogram
storage, independent of T and observation-frame count. Actual resource headroom,
wall limits and event throughput are Phase A unknowns. All budgets remain null;
D1.1's short-run ceilings cannot be silently enlarged or assumed adequate for T10.

## 6. Bounded verification performed and reproducible commands

No simulator, observer, force, Brownian, hopping/renewal, RNG or historical
source-authentication code was changed. No Phase A benchmark, B/C scientific run,
32-run D1.1 pilot, large reference ensemble or D2 work was executed. New tests:

- Six CPU proposal tests passed (final recorded run 1.311 s): exact/shared grids,
  rejection of unrepresentable times, matrices/Z/rho/steps/attempts, independent
  seeds and declared A pairing, false authorization/null budgets, field-aware
  storage/counts, frozen D1.1 preservation, deterministic generation, changed/
  missing/extra/symlink configuration refusal and overwrite refusal.
- Existing D1.1 CPU suite: 24 tests passed in 2.685 s, including independent
  reference predictions, replica aggregation, biased synthetic inputs,
  authentication, authorization refusal, interrupted/partial evidence and
  bounded process supervision. This does not validate a future D1.2 analyzer.
- New sparse technical test passed in single precision (.867 s) and double
  (.694 s). Each executes two paired on/off cases: N8/kappa0/dt=.0001 and
  N32/kappa10/dt=.00025, M4,Z6,nu20000,seed914203,13 steps, sample2;
  E1 steps 0,1,5,13 and audits 0,5,13. These are noncampaign fixtures.
  Scalar-only steps produce no E1 rows; the off-cadence final state is complete;
  accepted hopping and cross-chain renewal occur over the fixtures. The accepted
  independent checker reconstructs snapshots. Initial/final coordinates/springs,
  scalar/bond outputs, counters and non-timing metadata are byte-identical on/off.

Technical tests reused the accepted D1.0 binaries, not a fresh compile:
single SHA256 `e02320178dcf17072395dea0ad6b0527be6c40a793f1459460c7dd2521d2815d`,
double `4246b6e01926b5de6ef5d10c1ed5eb835edc4858aab5324087c6845e445ac2c4`.
No sanitizer rerun was necessary for unchanged C++/CUDA; earlier sanitizer results
remain those documented by D1.0, not new D1.2 evidence. Technical checks used
CUDA13/RTX3060Ti outside the sandbox, Python3.10/NumPy2.2.4, and bounded timeouts.
The first draft storage test caught a mistaken half-GiB assertion (the declared
target is under 1 GiB); the final bound checks under .75 GiB. A per-case renewal
assertion was corrected to require cross-chain events over the paired fixture
set: not every tiny N32 trajectory necessarily visits an end. No scientific
margin or simulator behavior was changed to make a test pass.

From repository root, safe preparation checks actually used:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 examples/slip-springs/tests/test_e1_d12_plan.py -v
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 examples/slip-springs/tests/test_e1_d1_pilot.py -v
PYTHONDONTWRITEBYTECODE=1 python3 examples/slip-springs/e1_d12_plan.py --check examples/slip-springs/e1_d12_proposed_config --sha256 2da957a5ee44956c395004bd20c23bee8e809b6d312ceee814e3f6934b2a5bbe
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 60s python3 examples/slip-springs/tests/test_e1_d12_sparse_technical.py /tmp/e1-d1-build/single/semiflexible -v
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 60s python3 examples/slip-springs/tests/test_e1_d12_sparse_technical.py /tmp/e1-d1-build/double/semiflexible -v
```

The last two are bounded technical GPU checks only and require those externally
stored accepted binaries and driver access. A deterministic NEW proposal copy
can be made with `python3 examples/slip-springs/e1_d12_plan.py --freeze NEW_DIR`;
existing directories are refused. This never builds or launches a simulator.
After any proposal revision use a new version/root/hash and repeat review.
Before scientific execution: independently accept the adapter/analyzer, freeze
and authorize A with actual resource caps; review A measurements before freezing
B budgets; review B drift/ACF/uncertainty before selecting/finalizing C.
