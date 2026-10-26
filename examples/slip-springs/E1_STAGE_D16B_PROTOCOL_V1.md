# D1.6B v1 — long-time exploratory equilibrium preservation

PREPARATION ONLY. This protocol, its candidate manifest and its resource amendment
grant no execution approval. The T100 experiment requires a new independently
reviewed readiness packet and an explicit user approval. No D0 confirmatory
acceptance, D2, stress or rheology is implemented here.

Authorities: `EQUILIBRIUM_MODEL_E1.md`, `E1_STAGE_D_VALIDATION_PROTOCOL.md`,
D1.4 Phase B preparation/analyzer, D1.5 benchmark/pilot preparation, and the three
D1.6 scientific design/reference/resource documents. The accepted simulator,
observer, initialization, RNG domains, one-step BD/jump splitting, transitions,
D0 margins and historical workflows remain unchanged. Scientific model source
is pinned to `0dea651b58171a72206774bcebb2f4c74960069b`; preparation began at
`e533e0412476c3e98875d9518afae42d75273928` after checking the fetched branch tip.

## Frozen physical cohort and independent seeds

The new `e1_d16b_config/manifest.json` is a non-executable candidate. Its false
`execution_authorized` and true `candidate_only` fields remain unchanged even
after a separate approval. Only the explicitly invoked new runner can execute
its cohort, and only with the exact new approval and explicit T100 flag. There
is no change to the old D1.5 T100 manifest, its unsupported execution status,
resource validator or approval semantics.

All 16 runs have N32 (33 beads), M256, Z2048, Ne4, A2=5, nu_hop100,
kb30, b0=kBT=zeta=1, exact independent E1 initial conformations, renewal on,
stress off, double precision and T100. Independent cells/replicas remain unpaired.

| Cell | kappa | dt | BD steps | Four preserved D1.5 T100 seeds |
|---|---:|---|---:|---|
| 1 | 0 | .0001 | 1,000,000 | 721530101, 721530102, 721530103, 721530104 |
| 2 | 0 | .00025 | 400,000 | 721530201, 721530202, 721530203, 721530204 |
| 3 | 10 | .0001 | 1,000,000 | 721530301, 721530302, 721530303, 721530304 |
| 4 | 10 | .00025 | 400,000 | 721530401, 721530402, 721530403, 721530404 |

These identities are retained from the never executed D1.5 exploratory arm.
Readiness validates all 16 identities against that immutable manifest. No
retrospective pairing, seed replacement, additional replica, retry, continuation
or duration extension is allowed. A partial cohort remains incomplete.

## Exact observation phase and retained records

Regular scalar frames: 0,.5,...,100 (201). Regular complete E1 frames:
0,2,...,100 (51). Five extra full frames are the timestep-specific first step
(.0001 or .00025) plus .0005,.0025,.01,.05. Thus 56 full frames, five supplemental
non-scalar frames and 206 distinct observation times per run. First-step frames
are diagnostic and never used in matched-time dt contrasts. Scalar-only frames
contain backbone observables; no population/connector value is carried forward.

Complete-state audits are 0,.01,50,100: positions, anchors, attachments, stable
spring IDs and contour links. The old first-step audit is replaced in this NEW
protocol only. First-step scalar/full diagnostics remain. All audits lie on
actual full frames. Step identity is computed with rational arithmetic; no
interpolation, nearest-step rounding or missing-state reconstruction is allowed.
Observer phase is unchanged: initialized t0, otherwise completed BD followed by
the entire jump/renewal batch.

Event rows count actual events over `(previous_full_frame,current_full_frame]`;
t0 counts are zero and t0 rates undefined. Irregular early intervals are shown
as recorded. For shared-time contrasts, first-step event bins are exactly summed
to the next shared observed boundary. Regular rate bins are (0,2],...,(98,100].
These are interval observables, distinct from instantaneous full frames and audits.

Expected data rows/run (CSV headers excluded):

| File/group | Rows |
|---|---:|
| samples | 51,456 |
| supplemental equilibrium backbone | 1,280 |
| long tangents / chain populations | 14,336 each |
| sites / connectors | 473,088 / 114,688 |
| event intervals | 56 |
| audit positions / audit attachments | 33,792 / 8,192 |
| initial / final positions | 8,448 each |
| initial bonds / final bond statistics | 8,192 each |
| fixed springs / initial springs / final springs | 2,048 each |

The unchanged structural/snapshot checker plus new schedule binding verifies
headers, row ordering/counts, finite values, unique site/spring/link identities,
canonical conservation, event identities, audits and endpoint correspondence.
Raw chain- and spring-resolved CSVs stay local. The final-half legacy bond
histogram is retained but does not replace time-resolved bond moments.

## Reviewed equilibrium-reference import

`reference-lock.json` pins the existing D1.6A.2 root, archived source session,
configuration, original CPU approval, readiness/seed audit, both completion and
assessment records, final inference, frozen cuts, sizing identities and reviewed
results archive/sidecar. The provenance basis is the user's D1.6B statement that
both moment families were independently reviewed and nominally accepted. The
lock captures identities, not a new scientific review or T100 approval.

Local readiness reauthenticates the original full closure read-only with the
unchanged D1.6A.2 authenticator, including raw-file hashes and batch/seed ledgers.
It checks recorded covariance dimensions, symmetry, numerical PSD and precision
acceptance. It imports full intervals, delta covariance, batch-jackknife diagnostics
and all reference precision statuses. It never resamples, reruns the reference
inference, writes to old evidence or imports previous D1.6A samples. Stage B/C
reauthenticate these identities. Missing/moved/corrupt evidence blocks use.

Kappa0 analytical moments remain primary. Both size means at kappa10 remain
analytical. Stiff variances, covariance and raw fourth-length moments use the
accepted independent final Monte Carlo estimates with their recorded uncertainty.
The stiff CDF family remains `CDF_PRECISION_UNRESOLVED`; it is available only as
an explicitly qualified exploratory reference with full intervals. It is never
accepted distributional calibration. Calibration quantile labels are not silently
substituted for the independently estimated probabilities at their frozen cuts.

The performance lock similarly pins both M256 D1.5 benchmark/pilot reports,
report receipts, launches, approved cohorts and completion identities. Readiness
reauthenticates their existing raw cohorts and binds report metadata to authenticated
receipts. These are planning inputs, not scientific preservation acceptance.

## Frozen exploratory estimators and uncertainty

At each supported time, retain each replica's backbone means, bond moments,
tangents1..4 (plus8/16 at full frames), spatial sample variances/covariance,
raw fourth-length moments, reference-centered squared/cross deviations and
18 frozen-cut backbone CDF probabilities. Reference-centered second moments
include mean drift squared. Under exchangeability the sample spatial variance
estimates marginal variance minus cross-chain covariance, not the variance of
the replica mean. Report M*Var_replica(mean)/Var_reference as a qualified R4
design-effect diagnostic with nominal Gaussian-replica variance bounds.

Full frames additionally use the exact finite-M hypergeometric population law,
all z=0..33 PMF/CDF entries, multiple-springs-on-one-chain probability, all 33
contour occupancies, connector Cartesian means/second/cross/centered moments,
radial mean/fourth moment and analytic Gaussian/chi-square CDF cuts. The population
mean8 is a conservation diagnostic. The finite-M negative interchain/site
covariances are retained. E1 connector components have variance5/3, E[e²]=5,
E[e⁴]=125/3 and 3e²/5 ~ chi-square3. All live springs enter each measurement;
there is no event-selected or surviving-spring subset. A_joint and B_joint keep
the original formulas and analytical mean normalization. Event rates use actual
interval counts and ideal continuous-time references, without IID event errors.

Whole independent M256 replicas are the primary clusters: exactly R4 per cell.
At fixed times, intervals use the four replica estimators. Window averages are
computed within each replica first. Early/late windows are [0,10]/[90,100]: 21
regular scalar or six regular full frames each. Regular event rates use five
whole two-time-unit intervals/window. Extra early frames are displayed separately
and never overweight uniform window means. Paired initial-to-late-window and early-to-late changes use the same replica
initial/early/late values; independent dt cells are never paired. All replicas
and leave-one-out means remain available. No initial burn-in is discarded.

Trajectory alpha=.025 per comparison. Unbounded quantities use nominal t3
intervals, with explicit R4/CLT limitations. Bounded probability estimators use
the independent-replica Hoeffding fallback, avoiding false zero-width rare-bin
intervals; nominal t intervals are retained as diagnostics. A zero observed
replica SD is flagged and cannot certify precision or a resolved discrepancy
for unbounded observables. Reference comparisons subtract the recorded reference
interval from the trajectory interval and add numerical centering-error bounds.
Independent combined SEs are also recorded; sampled-reference covariance is
preserved in full rather than discarded or treated as independent per time.

D1.6A.2 allocated .025 simultaneously to M across both kappas and .025 to C.
Combining a stored .025 reference-family statement with a .025 trajectory
interval yields a **nominal pointwise** >=95% reference comparison by a union
bound, subject to the original moment-CLT qualification. This is not simultaneous
coverage over all campaign comparisons. Exact analytical targets retain the original numerical error estimates
and their engineering (not certified interval-arithmetic) qualification. No additional final-reference draws or coverage relabeling
occurs. C precision remains separate from coverage and acceptance.

At identical rational physical times, dt contrasts use both independent-cell
variance contributions and Welch degrees of freedom. Bounded-probability
contrasts use a two-cell Hoeffding union bound. Both pointwise and matched-window
contrasts are reported. Shared references cancel from dt differences. Two dt
levels do not establish convergence order or the zero-dt limit. D0 margins are
unchanged contextual targets; no variance/fourth-moment tolerance is invented.

## Temporal support and interpretations

Analyze regular grids only, separately over [0,100] and [50,100], including
replica observables, fixed-label Re²/Rg², population and connector-score series,
and regular-bin event rates. Average fixed-label correlation products INSIDE a
replica; labels/chains/origins do not become uncertainty clusters. Report lag
spacing, physical lag, actual origin counts, segment duration and sample count.
The quarter-record rule permits scalar lag25 and full lag24 on the whole record;
late-segment support is shorter. No inherited D1.4 lag20 display cap is used.
No fast dynamics below .5/2 sampling spacing is inferred from this grid.

Report sample-mean and equilibrium-target centering, finite-lag partial sums,
initial-positive-pair truncation and self-consistent windows. Candidate sampled
IAT is Delta*(1/2+sum rho); positive pairs are (rho0+rho1),(rho2+rho3),...
with rho0=1. The retained products use overlap-corrected finite-record covariance.
Resolution requires a terminated positive sequence, positive stable estimate,
W>=5*tau, W<=duration/4, duration>=50*tau, <=20% neighboring-window/positive-pair
sensitivity and <=50% half-record sensitivity with terminated half-record positive sequences. Where an exact-target centering
is available, both centerings must support estimates within25%. These are
conservative exploratory diagnostics, not a theorem or new D0 criterion.

Unsupported tails yield `tau_int=null`, never zero. Conserved/zero-variance
series have undefined normalized ACFs and are distinguished from supported
correlation tails; they do not by themselves prove insufficient physical horizon.
No rigorous lower bound is claimed from a partial sum that can have negative
omitted terms. Report support separately for every replica and segment; unresolved
replicas are not dropped or averaged as zero. Apparent drift makes stationarity
assumptions questionable even if a numerical IAT diagnostic is supported.

Outcomes can coexist: reference-consistent within exploratory uncertainty,
pointwise statistically detectable deviation, insufficient independent-replica
precision, unresolved correlation tail, insufficient horizon, finite-dt difference,
and numerical/provenance/resource failure. A detectable pointwise deviation is
not a familywise discovery across thousands of comparisons. An interval containing
zero is not equivalence. Wide intervals cannot establish preservation. Matching
marginals/joint scores or equilibrium samples proves neither exact sampling
correctness, dynamical invariant-measure preservation nor ergodicity.

T100/R4 informs later power/horizon/replica planning. Confirmation needs a new,
independent, separately powered and approved dataset and simultaneous comparison
family. No new run follows automatically from any exploratory outcome.
