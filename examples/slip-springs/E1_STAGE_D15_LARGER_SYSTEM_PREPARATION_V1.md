# E1 Stage D1.5 — larger-system preparation v1

22 October 2026 (Europe/Madrid). **PREPARATION ONLY; NOT AUTHORIZED FOR EXECUTION.**
No simulation, benchmark, build, test, equilibrium draw or scientific analysis
was run in Codex. Work was source inspection, authentication/readout of existing
serialization/timing records, preparation arithmetic, scripts, documentation and
Git provenance checks. The new scripts and their tests remain unexecuted here.
An independent local readiness review is mandatory before any execution.

Starting local/fetched remote slip-springs SHA:
`7a889b060132a6d248a88128009fc9f595ef2b88`. Development uses the existing clean
`/tmp/UAMMD_KG-slip-springs-dev` worktree. The original KremerGrest checkout and
its unrelated KG changes are preserved. All changes are preparation files under
examples/slip-springs/. No simulator, E1 initializer, force, Brownian update,
hopping/renewal, observer, old test, build file, D0 tolerance, frozen manifest,
authentication allowlist or campaign artifact is changed.

Accepted scientific source remains `0dea651b58171a72206774bcebb2f4c74960069b`.
Preparation is not scientific acceptance of equilibrium, timestep, mixing,
terminal relaxation, production scalability or rheology. Active E1 stress stays off.

## 1. Staged scope for review

All cells have N32, Ne4, M256, Z2048, b0=1, kb30, A2=5, nu_hop100,
kBT=zeta=1, double precision, canonical end renewal and the accepted independent
exact-equilibrium initializer. Occupied-site fraction is8/33, mean chain
population8. This is the accepted finite-rest-length/bending E1 model, not a
Gaussian Rouse replacement.

| Cell | kappa | dt | Benchmark steps, T=.1 | Bounded pilot steps, T=1 | T100 design steps/replica |
|---|---:|---:|---:|---:|---:|
| 1 | 0 | .0001 | 1000 | 10000 | 1000000 |
| 2 | 0 | .00025 | 400 | 4000 | 400000 |
| 3 | 10 | .0001 | 1000 | 10000 | 1000000 |
| 4 | 10 | .00025 | 400 | 4000 | 400000 |

Only four benchmark processes are proposed first, one per cell; no repeat or
batch-size sweep. Their total is2800 BD steps,23,654,400 bead updates and81,920
expected attempts. This short benchmark assesses costs/readiness, not equilibrium.
Then stop and review its actual authenticated results. Only a separate approved
record can unlock the four-process T1 observation pilot (28000 steps,
236,544,000 bead updates,819,200 expected attempts). There is no automatic
progression, retry, resume, alternate seed, larger M or longer horizon.

The T100 design is a **non-executable planning artifact**: four independent
replicas per cell,16 processes,11,200,000 BD steps,94,617,600,000 bead updates
and327,680,000 expected attempts. Both build and execution entry points reject
it regardless of supplied flags/approvals. A new reviewed execution/resource
protocol is required after the smaller stages and earlier evidence are reviewed.
M512/1024/2048 are arithmetic projections only, not selectable runner workloads.

Seeds are fixed independently across phases/cells/replicas:
`721500000 + 10000*phase + 100*cell + replica`, phase1=benchmark,2=pilot,
3=exploratory. Thus benchmark cell1 seed721510101, pilot cell1 seed721520101,
exploratory cell1 seeds721530101..104. Every frozen run records its exact seed.
No retroactive pairing or reuse of Phase A/B seeds is introduced.

## 2. T100 observation design

| Clock | Physical times | Frames per replica |
|---|---|---:|
| Backbone scalar | 0,.5,1,...,100 | 201 |
| Full E1 regular | 0,2,4,...,100 | 51 |
| Extra full early diagnostics | .0005,.0025,.01,.05 and the first BD step | 5 |
| Complete-state audits | 0, first BD step, .01,100 | 4 |

The first-step diagnostic is dt-specific (.0001 or .00025), not a matched
physical-time contrast. Shared early diagnostics and regular clocks have exact
integer-step identities for both timesteps. No interpolation is permitted.
This retains the earlier initial/first-step/early/final audit convention;
distributing audit snapshots later in time is a separate review option.

The accepted observer reads completed states after BD and the entire jump batch;
t=0 is before dynamics. Four audits include every bead position, stable spring
identity, attachment, anchor and contour links; full frames also retain site
occupancy, per-chain populations, connectors and event intervals. These are
complete **physical-state** audits, not restart checkpoints or complete event
histories. The immutable seed/step also identifies Philox counters.

Keep raw samples.csv (M rows per scalar frame) and five supplemental early
backbone frames, plus per-chain Re2,Rg2,bond/tangent summaries. Keep all raw
chain/spring/site IDs and synchronized full E1 records. There are206 distinct
backbone frames and56 full frames per replica. Full E1 times join to their
backbone frame by replica,step,chain. Never carry spring/population data forward
to scalar-only times. Chain-resolved data support distributions, spatial
variances and unchanged D0 A_joint/B_joint calculations; ensemble means alone
would be insufficient. Use the exact M-dependent hypergeometric population
variance, not the M64 normalization. With L=33M,Z=8M:

    Var(Zc) = Z*(1/M)*(1-1/M)*(L-Z)/(L-1).

Event counters are differences over exact intervals; sum counts across early
subintervals before dividing by a shared interval duration. Frame counts and
raw event counts are not independent sample sizes. No burn-in deletion or
endpoint-only verdict is introduced.

Short benchmark: scalar0,.1 and the same early full diagnostics plus final.1.
Short pilot: scalar0,.5,1, early full diagnostics plus final1. Each has7 full
frames and4 audits. Their finer scalar cadence versus the benchmark's duration
is explicit, not an attempt to estimate equilibrium drift from two observations.

## 3. Storage evidence and projections

`e1_d15_observed_rows.json` extracts actual N32/kappa10/M64 Phase A C3+/C4+
CSV headers and row sizes. Each original run receipt is SHA256-bound to the
committed Phase A reference index; every CSV size/hash was authenticated before
extraction. No original bytes were edited. Phase B's frozen manifest uses the
same accepted source/observer schemas and the D1.2 schema calibration. No
completed Phase B campaign was supplied or located; **there are no measured
Phase B performance/row-size claims** in this report.

Selected pooled observed row widths, including comma/newline but not header:

| File | Mean bytes/row | Observed maximum |
|---|---:|---:|
| samples.csv | 224.279 | 246 |
| equilibrium_backbone.csv | 196.227 | 205 |
| equilibrium_sites.csv | 25.088 | 35 |
| equilibrium_connectors.csv | 104.768 | 123 |
| equilibrium_chains.csv | 99.397 | 113 |
| equilibrium_tangents.csv | 59.638 | 71 |
| equilibrium_positions.csv | 73.858 | 100 |
| equilibrium_attachments.csv | 85.324 | 105 |

Actual per-file counts at M256,T100: samples51,456; supplemental backbone1,280;
tangents14,336; sites473,088; connectors114,688; chain populations14,336;
events56; audit positions33,792; audit attachments8,192. Also retain the original
mandatory initial/final positions (8,448 each), initial/final/fixed springs
(2,048 each), initial bonds and bond statistics (8,192 each). No endpoint
file or bond histogram has been silently omitted from projections.

`e1_d15_projections.json` contains per-file counts and bytes for every proposed
run and larger system. Empirical projection=rows*observed pooled mean+header.
The separate conservative CSV envelope uses24 characters per finite float and
20 per integer/counter, plus separators/headers. The empirical estimate may
underestimate longer time strings, larger IDs, flexible chains or coordinate
magnitudes; it is not a quota. No compression is assumed. Add2 MiB per run for
JSON/log/receipt planning and a separately reviewed shared build/provenance
allowance (64 MiB placeholder); neither is automatically an approved budget.

| M | T100 empirical CSV/run MiB | Width envelope/run MiB | 16-run empirical bytes | 16-run envelope bytes |
|---:|---:|---:|---:|---:|
| 256 | 41.73 | 109.86 | 700158944 | 1843078592 |
| 512 | 83.46 | 219.69 | 1400244800 | 3685852608 |
| 1024 | 166.92 | 439.37 | 2800416512 | 7371400640 |
| 2048 | 333.83 | 878.72 | 5600759936 | 14742496704 |

Four benchmark runs project37,748,728 empirical CSV bytes or111,333,924 envelope
bytes total. Four T1 pilot runs:37,978,388 or111,684,132 bytes. Audits and fixed
legacy outputs dominate these tiny runs; cost per physical time is not constant.
The long16-run M1024 envelope exceeds the existing5 GiB aggregate cap; at M2048
even the empirical CSV estimate exceeds it. A resource amendment and new
protocol are required, not a tolerance change or an output omission.

## 4. Source-based scaling analysis

No scientific kernel is optimized or modified. Inspection refers to the
accepted files; their SHA256s remain in each new manifest.

* `semiflexible.cuh::stretch/bend/update`: one bead-owned thread; stretch uses
  at most two bonds, bend at most three angles; two coordinate buffers prevent
  EM races. `semiflexible_slipspring.cuh` adds dense per-site spring force.
  Work is O(33M) per step at fixed N, with no neighbor lists or interchain pair
  loop. Grid blocks at256 threads are33,66,132,264 for the four M values.
  Greater occupancy may improve bead throughput; this is not measured here.
* `slip_renewal.cuh::hopping<<<1,1>>>`: global sequential attempts with
  replacement. `slip_hopping.cuh::poisson` draws K by exponential interarrivals
  (O(K+1)), then serially processes K attempts. E[K]=Z*nu*dt grows linearly
  with M. The one thread cannot use extra SMs. This is a likely eventual
  bottleneck, not a measured fraction of runtime.
* Renewal chooses a destination chain/end in O(1) and scans at most33 sites
  to restore the destination contour extreme. It does not scan every chain.
  Source occupancy is tested before mutation, including same-chain proposals.
  Stable identities, source/destination occupancy, reciprocal links and fixed
  global Z must remain. Parallelizing events naively would change conflicts,
  ordering/RNG semantics and possibly the accepted dynamics; it is outside scope.
* `slip_hopping.cuh::checkState`: parallel O(33M+8M) site/spring invariants
  **every BD step**. Do not remove or reduce these checks to improve timings.
* `semiflexible.cu::diagnose/evaluate`: three blocking4-byte diagnostic D2H
  reads per active step (after forces, proposal and hopping), plus a stop-event
  synchronization per step. Stiff/flexible paths launch six/five core kernels
  per step respectively, with initial/final force checks extra. At T100 the
  fine/coarse schedules have3,000,000/1,200,000 diagnostic readbacks and
  1,000,000/400,000 stop-event synchronizations per replica. Transfer bandwidth
  is tiny (12/4.8 MB), but latency and host scheduling can dominate small M.
* `semiflexible.cu::observe` and `e1_equilibrium_observer.h`: full positions
  are synchronously copied for scalar/full frames; CPU double reductions and
  formatting scale with M. Full E1 frames additionally copy sparse Spring
  state, occupancy, both counter structs and dense anchors. At M256,T100,
  position readback over206 distinct frames is55,689,216 bytes; additional
  full-E1 readback is22,541,120 bytes. Both scale linearly with M (apart from
  88 counter bytes/frame). This includes **readbacks**, not a GPU-only reduction
  scheme. CPU geometry, slot copies, CSV serialization, synchronous flushes and
  final bond summaries are possible bottlenecks. Stress/correlator workers are
  not active in this accepted E1 path and cannot be credited with its speedup.

| M | Beads | Z | Mean K fine/coarse | Expected attempts per T100 run | GPU explicit MiB, stiff | Legacy workspace estimate MiB | Observer vectors MiB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 256 | 8448 | 2048 | 20.48 / 51.2 | 20480000 | 1.158 | 11.112 | .152 |
| 512 | 16896 | 4096 | 40.96 / 102.4 | 40960000 | 2.315 | 22.225 | .305 |
| 1024 | 33792 | 8192 | 81.92 / 204.8 | 81920000 | 4.630 | 44.449 | .609 |
| 2048 | 67584 | 16384 | 163.84 / 409.6 | 163840000 | 9.259 | 88.899 | 1.219 |

GPU explicit formula in double is132L+48Z+16N+8(N+1)+92 bytes for stiff chains,
L=33M; flexible uses264 fewer bytes. The legacy conservative workspace estimate
is1356L+96Z+88; observer vectors40(M+Z)+8L. These are accepted implementation
allocation estimates, **not peak GPU memory or measured host RSS**. CUDA context,
allocator, temporary/formatting buffers, library workspace and postprocessing
need separate headroom. Existing Phase A child peak RSS was about106 MiB even
at M64. Observer-owned quantities are not necessarily disjoint from all broader
budget estimates, so do not claim their sum is an exact RSS prediction.

Fixed limits inspected:

- maxMean=10000; maxEvents=100000 per batch, no clipping. M2048 means remain
  well below maxMean. The mean cap would first exclude M>50000 at coarse dt
  (125000 fine) with this density/rate. The drawn-count cap and128-retry RNG
  guards remain error paths even below that mean; never silently rescale rates.
- Bead diagnostic keys require L <= floor((INT_MAX-8)/8); M2048 is far below
  that constraint. Sparse IDs/indices are signed int, counts/RNG steps uint64.
  BD steps <=floor(UINT64_MAX/8). T100's1e6/4e5 steps and expected counts are
  far below these limits, although overflow checks are still mandatory.
- Population is bounded by33 per chain and Z=8M<L. No fixed M1024 chain array
  was found in this E1 path; the Rouse CPU-worker limit1024 is not a chain cap.
- Existing D0 operational caps remain120 seconds/run,3600 aggregate and5 GiB
  aggregate output. Historical Phase A/B128 MiB/run approvals are not approvals
  for D1.5. New limits stay null pending review. Host memory/JSON parsing and
  authentication time can matter before device-array capacity does.

## 5. Measured results versus unverified runtime proxies

Only old Phase A measurements are used. At M64,N32,kappa10,T.25:

| dt | Integration s | Production s | Supervised child s |
|---:|---:|---:|---:|
| .0001 | .270635775 | .302015702 | .5154917 (rounded) |
| .00025 | .13754998 | .16377767 | .3653529 (rounded) |

Exact recorded values/proofs are in e1_d15_observed_rows.json. Integration
includes hopping, invariants, diagnostics and submission/synchronization gaps;
it does not isolate an EM kernel. Production includes observation/output, not
initialization/final output. Child wall includes startup/exit/polling. These
nested scopes must not be added. Runner authentication overhead is separate.

For planning ONLY, multiplying production by(T/.25)*(M/64) gives:

| M | T100 fine proxy s | T100 coarse proxy s |
|---:|---:|---:|
| 256 | 483.23 | 262.04 |
| 512 | 966.45 | 524.09 |
| 1024 | 1932.90 | 1048.18 |
| 2048 | 3865.80 | 2096.35 |

These are neither bounds nor verified extrapolations: launch costs need not
scale with M, serial events do, GPU occupancy changes, and cadence differs.
Flexible N32 performance is not measured by those stiff references. They warn
against launching T100 under a120-second cap; they do not justify raising it.
First measure the four short benchmark cells, including initialization, overall
and integration ns/bead/step, observer wall/exclusive/D2H bytes/times, recurrent
and final output, child wall/RSS, event counts and resource headroom. The
new summary preserves all timer scopes and accepted-event rate per **production
wall** second; peak GPU allocation remains unknown when not measured.

Review per-step and per-physical-time costs separately. Fine/coarse runs have
the same expected attempts per physical time but different batching/splitting
and step counts. Do not call a speed advantage scientific timestep acceptance.
No profiling/optimization or M512+ benchmark is included in this pilot.

## 6. Exploratory statistics and later sample-size decisions

Proposed long design: M256, four independent replicas per kappa/dt cell,T100,
exact equilibrium at t0. Retain each replica's complete time series and spatial
chain-level distributions. Report ensemble mean, spatial variance and joint
statistics per frame; use whole independently seeded replicas as primary
clusters for evolution/contrasts. Cross-chain canonical population dependence
and renewal transfer prohibit casually treating all spring/site records as IID.
Successive frames must never be counted as independent replicas.

For exploratory pointwise ensemble-mean uncertainty use SD across four replicas
(ddof1), SE=SD/sqrt(4), with t3=3.182446 for nominal95% intervals. Replicas are
independent, not cells. These are not familywise acceptance/equivalence limits.
Use independent-seed fine/coarse contrasts with predeclared Welch or conservative
t3 intervals. Initial/final differences within a replica are paired, but cells
are not. Retain transients, early/late windows (proposed0..10 vs90..100) and
matched-time contrasts, not just endpoints. Early/late definitions and any
analysis adaptations require review before a long execution protocol is frozen.

Uniform ACFs can use201 scalar frames and51 regular full E1 frames; exclude the
irregular early diagnostics. With the previous max20/floor(n/4) display rule,
scalar lag support is10 and E1 lag support24 physical units. This does not
establish stationarity, mixing, resolved IAT or independence; long-tail support
may remain insufficient even at T100. Do not divide errors by sqrt(frame count).

Variance planning should use independent **exact-equilibrium backbone draws**,
not arbitrary separated dynamic frames. E1's integrated anchor/occupancy factor
leaves the accepted backbone equilibrium marginal unchanged. Initial chains
supply independent backbone samples, despite canonical population coupling.
At T100 proposal scale there would be1024 initial chains per cell; these are
useful pilot variance estimates, not a newly accepted reference ensemble.

Recommended separate CPU-only reference proposal, **not executed or authorized**:
N32, b0=1,kb30,kBT1, kappa0/10; start8192 independent exact draws per kappa,
bounded batches512, distinct seed namespace721590000+kappa; assess uncertainty
of Var(Re2),Var(Rg2) and their covariance, with independent-batch/bootstrap
intervals. Predeclare a refinement rule (e.g. relative variance-SE <=5%, at most
65536 draws per kappa) and explicit CPU/time/RSS/storage caps before execution.
Use `semiflexible_reference.Chain.sample(count,rng,kbt)` without modifying it.
Archive initial moments, covariance and Monte Carlo uncertainty, not just means.
Reaching the maximum without precision is an unresolved planning result.
No executable sampler or automatic large reference draw is added in D1.5.

For flexible chains an independent analytic fourth-moment check is available.
Let mu2=E[r^2],mu4=E[r^4] under the accepted radial density
r^2 exp[-30(r-1)^2/2], r>0; mu4 is the ratio of sixth/second radial integrals,
not a Gaussian-vector assumption. Then

    Var(Re^2) = N*(mu4-mu2^2) + (2/3)*N*(N-1)*mu2^2.
    A_ij = (min(i,j)+1)*(N-max(i,j))/(N+1)^2, i,j=0..N-1.
    Var(Rg^2) = (mu4-mu2^2)*sum_i A_ii^2
                + (4/3)*mu2^2*sum_(i<j) A_ij^2.

At kappa10 correlated orientations require fourth-order transfer/quadrature or
independent exact draws; substituting the Rouse chi-square variance is incorrect.
Reference refinement/error must be assessed independently of target BD evidence.

For an initially IID backbone observable X with variance sigma_X^2, the mean
across M chains and R replicas has variance sigma_X^2/(MR). For a target half-width
h, a preliminary requirement is MR >= (q*sigma_X/h)^2, with q chosen for the
frozen multiplicity/power plan. Use the conservative end of variance uncertainty,
not the point estimate alone. For later dynamics compare measured variance of
whole-replica means to sigma_X^2/M; dependence/design effects or finite-step
bias invalidate the simple IID planning formula. Time averaging requires a
supported cluster covariance/IAT estimate; no such support is claimed here.
Allocate only part of the unchanged D0 error margin to sampling; retain budgets
for reference error, temporal/timestep bias and multiplicity. M growth reduces
sampling error, not systematic bias. Choose M and R jointly with measured cost;
R4 provides weak variance precision and does not prove confirmatory power.
D0 margins (including2% Re2/Rg2 targets and stricter timestep contrasts) are not
changed, relaxed or declared passed by this preparation.

Optional **separate paired-initial-condition timestep study**: freeze new pairs,
seeds and analysis outside the independent design. The accepted initializer is
dt-independent; verify byte equality of initial bead AND attachment/anchor
files before calling states paired. Paired estimates use D_r=X_coarse-X_fine
and variance across independent pairs. Sharing the overall seed also couples
step-indexed RNG draws, not Brownian increments at equal physical times; do
not claim a Brownian bridge/strong-error study or pathwise convergence. Such
coupling must be explicitly documented, never retroactively applied to the
frozen independent Phase A/B/D1.5 cells. It changes neither marginal simulator
nor D0 margins and still needs separate scientific approval.

## 7. Fail-closed handoff and unresolved decisions

See E1_STAGE_D15_OPERATOR_GUIDE_V1.md. All three committed manifests remain
execution_authorized=false and all approved limits null. The T100 schema has
execution_supported=false. The new private bindings reuse the accepted build,
source/toolchain/executable/environment/GPU checks, process-group supervision,
nonoverwriting roots, raw schema/count/identity checks and whole-cohort receipts.
There is no automatic true-approval writer. A flag alone is not authorization.

Each bounded execution requires an external approval SHA, exact manifest/build/
environment/GPU/output identities, eight explicit positive resource budgets,
and a separately SHA-bound readiness review of actual user-run checks. The T1
pilot also requires an independent review of the complete authenticated four-run
D1.5 benchmark, bound to this exact pilot manifest. Approval references bind
both review pointers. Readiness review/artifacts and benchmark evidence must be
retained at their approved absolute paths; moving/missing files fails closed.
A Phase A/B approval cannot authorize D1.5. An old build receipt cannot be
relabeled: new manifests require a fresh observed build, even when source is the
same. No partial/failed/orphan adoption, retries or resume are added.

The raw completion marker alone is not a trust anchor. The new host wrapper
returns its completion SHA only after the whole cohort and added review gates
authenticate. If a later authentication fails, preserve evidence and reject it;
do not manually promote an on-disk marker. Supervision uses the unchanged .05s
polling; limits can be crossed briefly between polls and postprocessing also
has costs. Current operational caps remain unchanged.

Review decisions still needed:

1. Accept the unexecuted preparation code after local checks and independent
   review; no claim that those checks passed is made here.
2. Authorize ONLY the four short benchmark runs, their exact limits, source/build,
   environment/GPU and fresh root; inspect actual costs and identities afterward.
3. Decide whether the four T1 runs are informative/affordable, and separately
   approve them. No result from this task supplies that decision.
4. Supply/review any Phase B results; do not infer absent evidence.
5. Review T100 duration, R4, cadence, audit placement, tail support, variance
   reference precision, paired-study option and confirmatory power/multiplicity.
6. Review a new operational budget/protocol for long and M>1000 runs, based on
   actual measurements. Production GPU migration requires separate readiness.
7. Decide whether profiling (not scientific changes) is justified after the
   benchmark. Serial events, synchronization and I/O are hypotheses to measure.

No scientific or computational feasibility gate is accepted by this report.
Final commit/push SHA and isolation audit are supplied in the task handoff.

Frozen v1 manifest SHA256 trust anchors (all unauthorized):

- benchmark: `4c6805221db1ddf3d3ffaa6ae62f2f890150b6c967214be97642546941454dc9`
- pilot: `05f7f06141899d139b9e3fda3f740c92b0fe2b6894b280434ffe48b04c643c69`
- exploratory: `c4ffe6758b3c913c7b4ed2a9894d603e3f8f01fc3496448dc83e4ca269bdb0b5`

Derived projections SHA256: `1f3317c313396d66e2927b0aa5f4f170c646a8d0cdb232da19169be1ec338a08`.
