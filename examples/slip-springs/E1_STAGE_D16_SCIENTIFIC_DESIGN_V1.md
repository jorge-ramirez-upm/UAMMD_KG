# E1 D1.6 v1 — long-time equilibrium preservation design

**PREPARATION / SCIENTIFIC DESIGN ONLY — NO EXPERIMENT IS AUTHORIZED.**
Starting local/fetched remote `slip-springs` revision:
`0ad8fbdda55318e04c835bc02a012708a4ed04de`.
The user reports completed, authenticated and reviewed M256/T.1 and M256/T1
D1.5 performance cohorts. Their recorded summaries are present locally and
were inspected as files, not reauthenticated or reanalyzed in this task.
No test, build, equilibrium draw, simulation, benchmark, analysis job or GPU
preflight ran. No accepted kernel, initializer, RNG, transition semantics,
observer, frozen campaign or D0 tolerance changes.

Companion deliverables:

- [Reference derivations and bounded local procedure](E1_STAGE_D16_REFERENCE_MOMENTS_V1.md).
- [Evidence, runtime, memory and schema-based storage plan](E1_STAGE_D16_RESOURCE_PLAN_V1.md).

## 1. Scientific question and authority

Test **D1 preservation**, starting from independent exact E1 equilibrium states.
The target is the accepted nonlinear finite-rest-length, Kratky–Porod backbone
with canonical anchored slip-springs, single-site exclusion and end renewal.
It is not a Gaussian Rouse chain. E1's ideal continuous-time detailed balance
does not prove finite-dt Euler–Maruyama/splitting invariance or ergodicity.

Authorities inspected: `EQUILIBRIUM_MODEL_E1.md`,
`E1_STAGE_D_VALIDATION_PROTOCOL.md` (D0.1), `E1_STAGE_D14_PHASE_B_PREPARATION.md`,
`e1_d14_phase_b_analysis.py`, the D1.5 preparation/handoffs and immutable
manifests, accepted CPU reference, observer and CUDA driver/event source.
D1.4's committed report is a preparation report, not evidence that long-time
variance, IAT or preservation has been accepted. No completed D1.4 scientific
result was supplied among the inspected committed reports or the local
`/home/jramirez/UAMMD_KG-evidence/` entries (which contain D1.5 only).
If elsewhere available, its full cohort, trusted approval/completion identities,
analysis configuration/source hashes and authenticated result are needed.

D1.5 establishes observed feasibility on one host/one run per cell, not an
equilibrium-preservation test, uncertainty across replicas or a measured terminal
time. Accepted-event throughput is not an independent sample rate. A stationary
exact-start ensemble does not by itself demonstrate mixing from other starts.
D2 nonequilibrium relaxation, stress/rheology and parameter recalibration remain
outside this design.

## 2. Candidate designs and allocation choice

Primary exploratory candidate: N32,M256,Z2048,Ne4,A2=5,nu_hop100,kb30,
b0=kBT=zeta=1, kappa0/10 and dt=.0001/.00025, four independent replicas per
cell, T100, double precision, exact independent E1 initialization, renewal on,
stress off. This is the existing **non-executable** D1.5 T100 design, not an
execution request. Four cells means 16 independent runs, not four.

The old exploratory manifest SHA remains
`c4ffe6758b3c913c7b4ed2a9894d603e3f8f01fc3496448dc83e4ca269bdb0b5`;
`execution_supported=false`, `execution_authorized=false`, and null budgets
remain untouched. A changed audit placement or allocation requires a future
separate versioned protocol; do not regenerate or relabel that frozen manifest.

| Planning option | M | R/cell | T | MR at one time | Chain-time/cell | Runs over four cells |
|---|---:|---:|---:|---:|---:|---:|
| A, primary exploration | 256 | 4 | 100 | 1024 | 102400 | 16 |
| B, more independent replicas | 256 | 8 | 50 | 2048 | 102400 | 32 |
| C, larger ensemble | 512 | 4 | 50 | 2048 | 102400 | 16 |
| D, larger/shorter | 1024 | 4 | 25 | 4096 | 102400 | 16 |
| E, more replica clusters | 256 | 16 | 25 | 4096 | 102400 | 64 |
| F, larger long record | 512 | 4 | 100 | 2048 | 204800 | 16 |
| G, M>1000 planning | 1024 | 4 | 100 | 4096 | 409600 | 16 |

Equal chain-time is **not demonstrated equal wall time**: launch/synchronization
costs, serial events, GPU occupancy, startup and observation costs differ.
M512/M1024 have no measured D1.5 scaling result and no executable campaign here.

Recommend A as the initial long-horizon *exploration*, after the reference and
resource gates below. T1 gives no basis for asserting that T25 or T50 captures
the relevant drift or slow correlations. If later supported evidence shows T50
suffices, B is preferable to C for estimating independent-replica variability
at similar chain-time, until measured scaling establishes a contrary cost case.
E buys many replica clusters but loses late-time coverage and repeats endpoint/
audit/startup costs. F/G buy spatial precision at much greater unverified cost;
they do not solve small-R uncertainty or remove timestep bias.

Do not execute all alternatives as an open-ended search. Choose/freeze a single
exploratory allocation after review; further durations/cells need new approval.
There is no assumed restart/continuation from a final CSV or snapshot. Preserve
the frozen independent seed design; a paired-initial-state timestep arm would
be a separate new protocol, not a retrospective relabeling of independent runs.

## 3. Why affordability does not establish power

For kappa0, the derived non-Gaussian radial law gives

    CV_X^2 = Var(Re^2)/E[Re^2]^2
           = (mu4/mu2^2-1)/N + (2/3)*(N-1)/N >=31/48, N=32.

Even under ideal independent backbone sampling, a normal-approximation
pointwise 95% half-width is therefore **at least**
1.96*sqrt(31/48)/sqrt(MR), relative to the mean:

| MR | Ideal half-width lower bound |
|---:|---:|
| 1024 | 4.92% |
| 2048 | 3.48% |
| 4096 | 2.46% |

These are analytic planning illustrations, not measurements or guaranteed
confidence coverage. They already exceed D0's 2% size margin before power,
reference error or multiple comparisons. At A's R4, the nominal replica-t
critical t3=3.182446 would instead give about 8% at the null variance scale.
An ideal pointwise 95% precision calculation needs roughly 6203 independent
backbones for a 2% half-width, with **no** multiplicity/power allowance.

Long trajectories might improve window-mean precision only with supported
temporal covariance. They do not multiply the independent snapshot count by
the number of frames. For confirmation use the measured upper uncertainty on
whole-replica estimator variance, not an optimistic IID chain formula:

    R_needed approximately ((c_simultaneous+z_power)*s_replica/Delta_eff)^2.

Include a predeclared target such as 90% power and the desired smallest effect
relative to the equivalence boundary. Delta_eff is the remaining error budget,
not an enlarged D0 margin. Recompute critical values/variance uncertainty
consistently with R; use conservative bounds when R4 variance is imprecise.
D0's proposed R>=32 confirmation floor is retained as a planning floor, not
proof of power. M>1000 may be worthwhile after measured design effects/costs;
R4 does not become confirmatory because M is large.

## 4. Retained data and estimators

Keep raw chain-resolved scalar records and synchronized full E1 chain/site/
connector records under the existing schemas. Never replace them with a single
global mean, carry forward populations between frames or discard identity.
Analyze one authenticated replica/frame at a time with bounded memory; retain
the independent-replica vectors and references needed to recompute inference.

For X=Re^2,Y=Rg^2 record, per replica and time, their chain means, second
moments, covariance, distributions/CDFs and spatial variance. Pair t with t0
within a replica for changes; do not pair independently seeded timestep cells.
Report both conventional sample spatial variance and reference-centered second
moments. With exchangeable evolved chains,

    Var(Xbar_r) = [sigma_X^2+(M-1)*gamma_X]/M,
    E[spatial sample variance] = sigma_X^2-gamma_X.

Thus spatial variance alone is not the uncertainty of Xbar. Reference-centered
mean squared deviation includes mean drift squared; distinguish it from a
variance increase. Estimate design effect M*Var_r(Xbar)/Var_ref(X) with an
honest small-R uncertainty, rather than assuming gamma_X=0. At t0 independent
backbone initialization is known; at later times independence is part of the
null law being checked, not a guaranteed variance estimator under alternatives.

For every supported physical time report reference-relative size/bond deviations,
absolute tangent/joint/probability deviations, replica values and changes from
initial. Scalar-only frames support backbone quantities only. Tangents1..4
exist there; tangents8/16 and all joint/slip quantities require full E1 frames.
Use all live springs for connector statistics, never only event-selected or
surviving connectors.

Finite-M references, m=33,L=33M,rho=8/33,Z=8M:

    P(Z_c=z)=C(m,z) C(L-m,Z-z)/C(L,Z),
    E[Z_c]=8,
    V_Z=m*rho*(1-rho)*(L-m)/(L-1),
    Cov(Z_c,Z_d)=-V_Z/(M-1),
    P(occupied c,i)=rho,
    Cov(distinct site indicators)=-rho*(1-rho)/(L-1).

The mean population is exactly 8 in every valid frame, so it is primarily a
conservation check, not a precision test. Record Var(Z_c) around that known
mean, the whole PMF/CDF (including empty/one/multiple frequencies), every contour
occupancy, end/interior contrasts and rare-category support. Do not substitute
a binomial/Poisson distribution or independent multinomial error bars for the
canonical finite-M law. Recompute references for M512/1024.

For e=r_site-a, retain Cartesian means, second/cross moments, radial moments and
CDFs: e_d is N(0,5/3), E[e^2]=5, Var(e^2)=2*25/3, and 3e^2/5 is chi-square3
under E1. Reference connector CDF cuts are analytic. Backbone tangent target is
Langevin(kappa)^s at s=1,2,3,4,8,16. Size CDF thresholds/evaluation are independent
of trajectories and have quantified reference error (companion derivation).

Retain existing A_joint and B_joint exactly, with
f_c=Re_c^2/E[Re^2]-1, sigma_Z=sqrt(V_Z):

    A_joint=sum_c f_c*(Z_c-8)/(M*sigma_Z),
    B_joint=sum_c f_c*(sum_(j on c) e_j^2-5Z_c)/(5Z).

Their target is zero. The companion derives null-law instantaneous variances;
use whole-replica uncertainty for evolved scores. Zero correlation/matching
marginals is not proof of the full joint law. Event rates remain interval counts
per physical time with timestep/replica uncertainty; accepted events are not IID
Poisson samples and observed renewal counts do not prove complete mixing.
Rates are undefined at t0; rebin actual counter intervals only at observed
shared boundaries, never invent an initial rate or interpolate unobserved events.

## 5. Hierarchical uncertainty and temporal analysis

Primary independent units are whole independently seeded replicas. At a fixed
time use the R-vector of replica estimators. For a window, average scheduled
frames **inside each replica first**, with the same weights across cells, then
estimate variability across replicas. Preserve time/observable covariance by
resampling whole replica vectors. R4 t3 pointwise intervals are descriptive
nominal intervals; a four-cluster bootstrap cannot establish reliable tail
coverage or confirmatory power. Do not manufacture precision from components,
bonds, contour pairs, springs, chains or overlapping origins.

For bounded replica CDF/occupancy means, D0's independent-replica Hoeffding
fallback has simultaneous half-width sqrt(log(2K/alpha)/(2R)); it does not need
within-replica chain independence. At R4 it will generally be far too wide.
That is insufficient precision, not permission to use independent-binomial
chain errors or a zero-width interval when no rare event was observed.

Predeclare exploratory early and late windows [0,10] and [90,100] at T100;
report each and paired within-replica late-minus-early. For scalar windows these
are 21 frames; full E1 regular windows have 6 frames. Irregular early diagnostics
are shown individually, not over-weighted as extra uniform window samples.
No burn-in is discarded from D1 exact-start preservation plots. A separately
declared late-window ACF analysis does not erase initial drift.

Compare between-replica trajectories, window differences, dispersion/outliers
and leave-one-replica-out summaries. Outliers remain in the evidence; they are
not grounds for an unapproved new seed. Shared-time dt contrasts are independent
cell contrasts with both replica variance terms. Use integer-step/rational-time
intersection, not interpolation; exclude timestep-specific first-step frames
from matched-time claims. Two dt levels show sensitivity, not convergence order
or an established dt->0 extrapolation for this nonlinear model.

For apparently stationary segments compute descriptive demeaned ACFs separately
for replica means/joint/population/connector scores and for fixed-label chain
conformations where available. Correlated per-chain ACFs may be averaged within
a replica, but uncertainty still clusters by replica. Report centering choice,
window duration, lag-origin counts, block-length sensitivity and sampling-grid
limits. Baseline-centering on an exact target is a useful sensitivity check;
demeaning a drifting finite record can hide long correlations.
Conserved or zero-variance series (including the exact mean population8 and
constant CDF endpoints) have undefined normalized ACFs, not tau_int=0. Flag
zero observed replica dispersion rather than treating it as proven precision.

Define sampled-series tau_int=Delta*(1/2+sum_(k>=1)rho_k). Use initial-positive-
sequence and self-consistent-window diagnostics, not the first zero as an IAT
proof. A proposed resolvability check requires a stable tail/window estimate
with W>=5*tau_int, W<=segment_duration/4 and segment_duration>=50*tau_int,
plus sensible replica/block sensitivity. Treat these as planning diagnostics,
not a coverage theorem or new D0 tolerance. If unsupported, output tau_int=null,
the finite-lag partial sum/support, and `unresolved_tail=true`. A partial sum is
not a rigorous lower bound if omitted correlations can be negative.

Pointwise exact-start ensemble inference does not require an IAT estimate.
Unresolved IAT instead blocks claims about mixing, independent temporal samples
and power gains from time averaging. Do not require a Gaussian Rouse relaxation
time, an isolated connector time or frequent renewal as a replacement.

## 6. Observation cadence and audits

Retain the proposed .5 backbone scalar and 2 full E1 spacing for A, with the
five extra early frames: the timestep-specific first step and shared physical
times .0005,.0025,.01,.05. There are 201 regular scalar frames, 51 regular full
frames, 56 total full frames and 206 distinct observation times. Preserve the
initialized t0 and completed-post-BD/post-jump sampling phase.

Recommend future audits at **0,.01,50,100**, replacing the old first-step full
state audit with an intermediate state. First-step scalar/E1 diagnostics remain.
Time50 already belongs to the full grid, so no frame/row-count increase occurs;
all four audits remain complete R/S/A/link/identity records. For T50 alternatives
use 0,.01,24,50, and for T25 use 0,.01,12,25, keeping the interior audit on the
existing full grid. These are unapproved new schedule choices, not edits to D1.5.

The cadence is suitable for spatial distributions at selected times and broad
drift, but not automatically for fast ACFs. A bare local stretch time of order
1/kb and the isolated-tether time 5/3 are illustrations, not actual coupled
relaxation predictions. Full spacing2 cannot resolve sub-2 dynamics; scalar
spacing.5 cannot recover faster bond fluctuations. Irregular early points do
not form a uniformly sampled ACF record.

Over the entire T100 record a quarter-record lag rule permits scalar lags to25
and full E1 lags to24; the existing D1.4 display cap20 would show scalar only
to10. On a stationary late segment [50,100], those quarter-record supports
shrink to12.5 and12. Thus T100 can still leave slow tails unresolved. The D1.4
analyzer is hard-bound to its R2/M64/T10 matrix and cadence; do not relabel its
output or silently alter it for D1.6. A future separately tested adapter must
implement this new analysis protocol without changing the old evidence/tools.

Do not increase the default cadence merely to inflate record count. If fast
connector/population correlations are essential, first approve a separate
short high-cadence diagnostic design, with a stated target lag resolution and
schema-based additional storage. No such trajectories are added here; baseline
analysis must honestly retain unresolved fast/slow-time flags.

## 7. Exploratory versus confirmatory decisions

A is exploratory: describe drift, distributions, reference agreement, variance,
design effects, ACF support and dt contrasts, with all limitations. No automatic
pass/fail from pointwise intervals, no fitted tolerances and no retrospective
confirmation. R4's imprecise replica variance is itself a planning result.

Confirmation needs a new independent dataset, approved fixed M,R,T, seed list,
cadence, windows, reference version and finite comparison family K. A candidate
primary-time set is {0,2,10,50,100}; all other recorded times can remain
descriptive. Count every declared cell/time/window/contrast, tangent, component,
contour index and CDF cut before choosing simultaneous intervals. Do not select
the easiest times after seeing confirmatory outcomes. Reference calibration
may be shared, but its uncertainty/covariance is retained across comparisons.

D0 sections7.2–7.3 remain authoritative and unchanged: sizes2%; bond moments1%;
tangents/joint scores/CDFs .02 absolute; connector e^2 mean2% of A2; Cartesian
means .05*sqrt(A2/3), diagonal second moments/variances2% of A2/3, off-diagonal
moments .02*A2/3; contour occupancy min(.01,.10*rho); approved event-rate
references5%. Dt contrasts retain half the matching static margin. Exact
conservation, identity, finite-value and counter violations have zero allowance.
Variance/fourth-moment estimates are power diagnostics unless a separate future
criterion is approved; D1.6 invents no new scientific variance tolerance.

Propose FWER .05 over the frozen finite family, following D0's Bonferroni
simultaneous intervals or a separately justified/approved whole-replica method.
Intervals for deviations combine independent trajectory and sampled-reference
variance plus bounded numerical error. Shared references cancel algebraically
in appropriate dt differences; do not double-count them or assume all contrasts
independent. Confidence intervals must lie entirely inside unchanged equivalence
margins; p>.05 is not equivalence. Distinguish disagreement, insufficient
precision/support and numerical/provenance failure. A wide interval is not a pass.
If separate reference intervals are used as bounds, allocate the total .05
error budget explicitly, for example .01 to the shared reference family and
.04 to trajectory comparisons. Recompute those reference intervals at the
allocated coverage; a .05-quality reference plus .05 trajectory intervals do
not establish .05 overall error. Alternatively jointly calibrate both variance
sources with preserved shared-reference covariance. Freeze that choice first.

Timestep bias is not sampling noise and cannot be removed by increasing M,R,T.
Do not retarget references to measured EM equilibrium or apply Gaussian harmonic
mode bias corrections to this nonlinear backbone. A separately approved finer
dt may be needed if the primary pair disagrees or is jointly biased. Do not
spend reference uncertainty as extra tolerance. Predeclare alpha allocation,
power and conservative variance/refinement rules before confirmation.

## 8. Decisions and explicit gates

1. Review these derivations, observable family, independent reference procedure,
   uncertainty targets and reference CPU/time/RSS/output caps; authorize no draws
   merely by accepting the documentation.
2. Reauthenticate/consume the D1.5 full evidence and approved host identities;
   obtain any missing D1.4 scientific results rather than inventing IATs.
3. Review A versus B–G, duration, cadence limitations, intermediate audit choice,
   exploratory windows and what unresolved IAT would imply. Choose one scope.
4. Independently approve a versioned operational resource amendment: old
   120s/run and 3600s aggregate limits remain active. Resource suggestions are
   in the companion plan, not approval records or bypass flags.
5. Separately authorize future analysis/reference tooling and its bounded local
   correctness checks. A new long-time execution protocol/manifest would need
   fresh source/build/environment proofs, nonoverwrite, bounded sequential
   supervision, sample/schema/invariant checks and full-cohort authentication.
   No such runner, true approval, new frozen manifest or execution is created now.
6. Review actual exploratory/reference results before powering and freezing a
   separate confirmation. Never relabel exploratory data as confirmation.

Acceptance of this report is acceptance of a design for review, not acceptance
of equilibrium preservation, timestep accuracy, long-time ergodicity or any
T100/M512/M1024 execution. The existing T100 manifest stays non-executable.
