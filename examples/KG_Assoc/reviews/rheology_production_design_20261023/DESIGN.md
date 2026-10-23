# Production design centered on stress relaxation

2026-10-23. CPU-only proposal; **no execution authorization, production registry,
run plan, attempt, seed reservation or new trajectory is created**. Ea10's separate
user-approved qualification permits initial-state use despite scientific uncertainty;
it does not make production stationary. See the accompanying existing-method review.

## Scientific program and staged length decision

Use all **fifteen qualified associating conditions**, each retaining its exact
three parent families (45 histories). CONDITIONS.csv binds the formal records and
initial endpoints. Keep paired comparisons wherever systems inherit a common
original preparation family; different conditions/segments/channels do not create
new independent preparations. Existing non-associating validation is contextual;
no additional control replicas are scheduled in this scope.

Primary outcomes are the six-channel G(t), terminal relaxation with uncertainty,
and eta0 only where a defensible tail is resolved. Secondary observables from the
same histories connect stress to association population/exchange, loops, triangles,
multiplicity, distinct neighbors, component identities, chain conformation and
transport. No result about universal equilibrium invariance follows just from
varying Ea at fixed nominal Hamiltonian. Compare measured stress, bond-exchange and
neighbor-renewal times rather than imposing a clock rescaling. The frozen attempt
probability is q=-expm1(-nu0*exp(-Ea/T)*Nevery*dt); changing Ea changes conditional
attempts, while eligibility, energy acceptance and MD relaxation also affect response.

The recommended first observation length is **32M uninterrupted production steps
per selected history**, not automatically100M. At dt=.01 this supplies320000 reduced
time units. Historical five-replica C1 data reached the noise floor around 2e4 and
supported an approximate cutoff integral near 2.9e4; 32M allows a useful span beyond
that scale while retaining every-step short-time stress. Three new families offer
less ensemble information than that five-replica pilot. Historical chemistry predates
the periodic correction, and slower/high-Ee/high-Ea or longer-arm systems may have
very different relaxation. Thus32M is an information-gathering starting length, not
a sufficiency guarantee or a prescribed extension of any equilibration history.

| Proposed stage | Conditions/families | Steps if subsequently approved | Decision before proceeding |
|---|---|---:|---|
| 0: instrumentation readiness | Representative small/large geometry and current exact parents; user-run bounded validation only | No long run selected here | Prove current optimized stress/build, initial-state fidelity, reaction/oracle compatibility, output synchronization and non-destructive launch handling. |
| 1: rheology sentinels | F04 N010 RP080: Ee8/Ea4, Ee12/Ea4, Ee8/Ea8, Ee8/Ea10; all three families each | 12×32M=384M | Review full channels, early/late G, supported tails, structural conditioning, runtime/I/O and CIs; stop on numerical/provenance failures. |
| 2: complete the matrix | Remaining eleven conditions, all three families each | 33×32M=1056M | Proceed only after stage1 methodology is usable; assess each system separately, including long-arm/low-density modes. |
| 3: targeted precision/long horizon | Only scientifically unresolved conditions/families after review | No count or budget approved | Choose a new uninterrupted length or more original preparations according to horizon versus replica-noise limitation. No automatic run/extension. |

Stages1+2 would total **1.44 billion steps** across 45 completed32M trajectories.
These are prospective scientific/resource scenarios, not an approval or prepared
campaign. If a lag horizon is limiting, a separately reviewed64M uninterrupted
run approximately doubles its horizon; if existing-lag replica noise dominates,
repeating the same trajectory longer may be poor value compared with genuinely
independent preparations. Do not promote windows to replicas. New preparations,
if justified, require their own scientific and execution decisions.

The current strict campaign schema, launcher validation and front end **fix 100M**.
They do not currently implement this 32M staged policy. Before any stage is executable,
add and test a narrowly approved administrative length configuration and consistent
receipts/validators; retain frozen physics and the existing stress estimator. Do
not use compile-time smoke overrides or the old pilot script to bypass those gates.
If 100M is ultimately chosen, its justification must be the required horizon/precision
and feasibility, not merely that it is today's CLI default.

## Sampling, lag horizon and estimator

Retain dt=.01, T=1 and every-MD-step stress, Correlator6(40,16,2), the six-channel
projection and raw n_pairs. Keep stress step zero excluded. The normal differences
are dependent; all six channels reduce tensor anisotropy noise but supply no extra
replica degrees of freedom. Retain original channels and signs, not positive-only
curves or a single xy substitute. Show G0 and .01-scale behavior alongside
intermediate/terminal log-time views, including signed noise-floor values.

Use the actual finite lag/count grid (LAG_GRID.csv in the rheology dossier).
At 32M the raw endpoint 293601.28 has one contribution; threshold 8 reaches 157286.4,
threshold 128 only 19660.8. Longer horizons follow the same finite grid:

| Samples/steps | Last raw lag | Last lag with ≥8 pairs | Last lag with ≥128 pairs |
|---:|---:|---:|---:|
| 32M | 293601.28 | 157286.40 | 19660.80 |
| 64M | 587202.56 | 314572.80 | 39321.60 |
| 100M | 838860.80 | 629145.60 | 78643.20 |

All times are reduced units; these horizons do not establish terminal decay. Reproduce the existing support sweep 8,16,32,64,128 and
five-bin/three-overlapping-window persistence analysis. A bin can be eligible and
still scientifically unresolved; raw counts are neither independent stress pairs
nor an ESS. Compare all three families before interpreting a tail.

Coarse levels correlate block-averaged stress, with geometrically spaced lags.
Integrate each family's G with the existing nonuniform-grid trapezoid rule and its
actual G0 row. Inspect cutoff and coarse-grid sensitivity, especially when a terminal
feature spans only a few bins. Existing arithmetic tests do not prove that coarsening
bias is negligible for every new material. Do not change the estimator or resample
the lag grid into invented independent observations.

## Required temporal stress observability

Existing whole-run `.stress_correlator` files cannot supply early/late or
triangle-conditioned correlations. Before launching this design, implement/test
**an observational export of the existing reduced six-component tensor buffer**,
with absolute step and no extra force evaluation, at every stress step.
The earlier plan correctly said raw tensors need not be dumped for whole-run G;
that remains true. The additional early/late and structural-conditioning objectives
cannot be recovered from the old aggregate alone. This proposed observational
output addresses that extra requirement, while retaining the established estimator. A compact
proposal is step:int64 plus six float64 sigma entries (56 bytes/sample), with
versioned header, box volume, T, dt, component order, stress phase, parent/segment
and executable identity. Preserve exact original buffer ordering and normalization.
This is proposed missing output support, not an implemented feature or replacement
for the online Correlator6. Authenticate chunks and completion; retain the online
full-run result as an offline-replay cross-check. Benchmark its I/O before long runs.

Reuse the same Correlator6 offline for predefined temporal windows; no new stress
formula is needed. At 32M, compare production-relative0–16M and16–32M stress origins
using lags supportable in both, and retain0–8/8–16/16–24/24–32M structural summaries.
Use4/8M stress subwindows only for shorter lags with credible support. Boundary-truncated
pairs must have their own counts. Output cumulative snapshots alone cannot be
subtracted to obtain a full later-window correlation, because the cumulative curve
also contains cross-window pairs and changing denominators.

For Ea10, reconstruct exact triangle/L1/degree/component histories from the accepted
initial graph plus timestamped reaction events (chemistry cadence100); cross-check
against topology frames. Synchronize event-derived L2 with post-chemistry stress at
each absolute step. Compare descriptive origin-conditioned stress products in
triangle-rich/poor states, with35/40/45 threshold sensitivity and per-family reporting.
Distinguish conditioning only at the origin from conditioning both ends or an entire
residence; the latter selection favors persistent regimes. Neither is automatically
an equilibrium Green–Kubo response or a causal effect of triangles.

Conformation from saved beads is only every100k steps; COM/topology every10k. These
permit coarse structural matching, not every-step bead/velocity reconstruction.
If time-resolved Rg²-conditioned stress is required at finer resolution, save an
additional synchronized conformation observable at its declared cadence; do not
interpolate unavailable microscopic trajectories or use positions to reconstruct
kinetic stress. The proposed raw stress stream also permits direct checks of mean
shear/normal differences and channel anisotropy, absent from a final whole-run G.

## Restart, failures and completion policy

Current campaign production has no bitwise restart, no serialized GJ/RNG state,
no active correlator checkpoint, and no reloadable final chemistry pair. Production
ends with archives plus atomic completion. The standalone tested correlator
serialization is not a simulation checkpoint. Keep each production history one
uninterrupted segment; no correlation/IAT/lifetime origin crosses a fresh-noise
boundary. Do not splice partial G curves or regard successive starts as independent.

Production uses the campaign-requested seed for both system MD RNG and chemistry,
while retaining the initial physical partners, absolute step and inherited reaction
counter offsets; ordinary historical pilot restart semantics differ. Before launch,
explicitly authenticate and reserve the requested/effective streams according to
this actual policy, label the new chemistry stream, and never claim exact chemical
or MD RNG continuation from accepted E2. No RNG semantics are changed here.

A future user-run runner must preserve incomplete output, logs and reservations,
skip only independently validated complete histories, and allocate a fresh immutable
attempt if genuine partial work cannot continue. Native completion followed by an
administrative exception must enter validation recovery, not automatically repeat
MD. Every replacement needs explicit limits/approval; interruption overhead is
separate. Source/build/parent authentication must be identical pre- and post-run.
No such launch/retry workflow is newly prepared or authorized in this milestone.

## Statistical and scientific acceptance of rheology

Retain family-resolved curves and diagnostics. Compute equal-family means and
replica spread/CIs; for three independent families Student-t df=2, t*=4.302653,
not six-channel or time-bin df. Shared original preparations require paired
cross-condition contrasts. Temporal blocks are correlated repeated information;
show block-size/age sensitivity and between-family disagreement separately.
The existing reader requires matching lag grids and exact support counts across
families. Keep equal-length windows for its standard aggregation; unequal-length
follow-up curves need a separately validated common-window analysis, not a silent
relaxation of the reader. Sparse regime occupancy prevents precise conditional G for that family even if
raw stress-pair counts are large. Do not conceal r003 with ensemble averaging.

Use the existing P4 tail labels and analyzer as the baseline, with explicit
scientific review beyond its automatic recommendation:

- Require authenticated numerical completion, finite tensors, correct counts and
  source/initial-state provenance. Numerical PASS alone is not rheological acceptance.
- Distinguish sustained nonzero tail, noise-compatible decay, support-limited and
  unresolved classifications across support choices; show signed channel and replica
  curves. A wide CI containing zero is not evidence of a small unobserved tail.
- Inspect early/late and structural-regime dependence at matched lags. Report detected
  age dependence as G(t;age), not a single stationary modulus. Predefine windows,
  retain early data, and do not silently choose a favorable burn-in or cutoff.
- Report eta0 only after sufficiently supported terminal relaxation and scientifically
  useful uncertainty/cutoff stability are demonstrated for that system. Apply the
  existing candidate cutoffs for C1-like resolved cases; choose any slower-system set
  transparently from its supported terminal range, before selecting a preferred value.
- If the tail is unresolved, show finite-cutoff integrals as truncated diagnostics
  where useful and label missing tail area; do not call them converged eta0. No
  exponential extrapolation or exact q(Ea) clock rescaling is assumed.
- The automatic “cutoff sensitivity < replica-CI half-width” criterion is necessary
  context, not sufficient useful precision: today's two-file reanalysis passes it
  even with eta CI−881..1320. State desired precision for each manuscript claim
  (ordering, factor changes, or quantitative values) and assess against actual CI,
  age and cutoff sensitivity. No arbitrary universal percentage threshold is added.

Ea10's initialization exception does not waive these criteria. A statistically
unresolved or aging Ea10 modulus can be reported as such while the qualified other
systems support stronger conclusions; initialization permission does not guarantee
an equilibrium viscosity. More data have value only if they can discriminate the
specific conditioning/terminal mode, not merely reach a prescribed runtime.

## Budget and prerequisites

BUDGET.csv uses actual accepted-state atom/permanent-bond counts, a measured historical
C1 32M mean time 11383.05s at 43563 particles, and exact binary bead schema sizes.
These linear particle-work estimates are provisional, not modern benchmarks for
all geometries, Ee/Ea values, file systems or raw-stress export. Rebenchmark small
and large systems and measure event/I/O overhead on the user's host before approval.
The optional56-byte stress stream alone costs **1.792GB/history** at 32M,
**80.64GB across 45 histories**, without compression. Exact bead-byte estimates,
text/COM/topology/event headroom and restart overhead must be added. The prior
150–250GB envelope for 69×100M did not include this proposed raw-stress stream and
must not be copied as a guarantee. BUDGET_SUMMARY.log supplies current totals: the 45×32M scenario gives about
**222.7 historical-linear GPU hours**, **11.84GB bead data** and **80.64GB proposed
stress data**, before text outputs, analysis duplication or I/O overhead.
Use free-space preflight and reserve scratch/analysis duplication and at least
1.5–2× the measured uncompressed working footprint; observed text rates should
replace estimates before scheduling.

Launch prerequisites are: separate user decision on stages/lengths/resources;
explicit selection/activation of an approved exact-state registry (not done here);
minimal tested length/approval/receipt support; stress-time export/window capability
with offline/online equality tests; fresh optimized out-of-tree build/authenticated
source map; user-run bounded GPU stress/readback/candidate/numerical validation on
current corrected code/parents; explicit stream policy and immutable attempts;
replay/analysis compatibility; adequate storage and interruption policy. Only then
provide tested manual execution commands. No production command is offered as ready
while these concrete gates remain open.
