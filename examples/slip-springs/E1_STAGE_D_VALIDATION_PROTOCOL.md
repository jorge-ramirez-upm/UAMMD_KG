# E1 Stage D0 — coupled equilibrium validation protocol

## 1. Status, authority and objectives

Protocol version: **D0.1, timestep amendment and bounded CPU screening**
(21 October 2026). Amendment starting revision:
**31643cef8838a22b38267338f124f558274b39dd**, verified on `slip-springs` with a
clean tracked working tree. Original D0 inspection was at
`621f3f10118d30797a636c17945c59982f87b58e`; its documentation-only execution
record remains historical. D0.1 changes timestep proposals and their arithmetic,
with six independently seeded 100-configuration CPU Hessian screens and the
seven existing preselector tests; see [screening report](E1_STAGE_D_TIMESTEP_SCREENING.md).
No observer, dynamics, force/Hessian code, scientific accuracy margin or earlier
scientific result is changed. No GPU trajectory or pilot was run.

| Status | Meaning in this document |
|---|---|
| Frozen existing science | E1 measure, Hamiltonian, rates and accepted A/B/C behavior; unchanged |
| D0 design baseline | Separate D1/D2 questions, references, dependency handling, evidence categories, data/provenance requirements and approval gates below; changes require a versioned amendment |
| Proposed numerical choices | Every new matrix entry, tolerance, replica count, cadence, duration, support floor and resource cap below; requires scientific approval before becoming a campaign acceptance plan |
| Authorized now | D0.1 documentation, bounded existing CPU preselector and relevant tests, commit and push on `slip-springs` |
| Not authorized | Instrumentation or initial-state importer implementation, new tests, pilot execution, campaign reference generation, production or analysis of new trajectories |

Commitment of this design freezes its recorded contents, **not scientific
approval of its proposed numerical choices or permission to execute them**.
A later approved manifest must mark each proposal accepted, replaced or
excluded before data are collected. Pilot-informed duration and uncertainty
planning follow a predefined rule; scientific accuracy tolerances must be
approved before the pilot and must not be fitted to its outcomes.

Two distinct questions govern acceptance:

- **D1, preservation:** do independent exact E1 starts retain the intended
  equilibrium distribution under the complete finite-step algorithm?
- **D2, equilibration:** do specified nonequilibrium ensembles approach that
  distribution, for each observable, within demonstrated sampling support?

A/B/C establish bounded implementation and fixed-coordinate jump-kernel
behavior. They do not answer these fully coupled questions. Stage D concerns
internal equilibrium statistics and numerical accuracy only. Terminal diffusion,
reptation, stress/modulus or cross-correlations, deformation, anchor transforms,
constraint release, stiffness-dependent entanglement parameters and event-engine
optimization are excluded. Do not use existing MSD columns for Stage D claims.

Authorities inspected: [local rules](AGENTS.md), [E1](EQUILIBRIUM_MODEL_E1.md),
[Stage A audit](E1_STAGE_A_AUDIT.md), [Stage B report](E1_STAGE_B_REPORT.md),
[Stage C report](E1_STAGE_C_REPORT.md), [backbone authority](BACKBONE_MODEL_AND_VALIDATION.md),
[timestep evidence](TIMESTEP_SELECTION.md), [status](PROJECT_STATUS.md),
[CPU reference](semiflexible_reference.py), the simulator driver and output
serializer, and the existing host equilibrium predictions. Historical reports
retain their original acceptance scope; this protocol does not amend them.

## 2. Target measure and independent predictions

Use N bonds, m=N+1 beads per chain, M chains, L=Mm sites, Z springs, rho=Z/L,
A2=a_ss^2, beta=1/kBT, and k_ss=3kBT/A2. Require 0<Z<L for the active matrix.
The E1 target on distinct site sets S and anchors A is, modulo translation,

```text
pi(R,S,A) = pi_bb(R) / C(L,Z) * product_{x in S} g(a_x | r_x),
g(a|r) = (3/(2*pi*A2))^(3/2) exp[-3|a-r|^2/(2*A2)].
```

Integrating anchors makes occupied-site sets uniform and restores the **bare
nonlinear semiflexible backbone** marginal. There is no additional melt,
Gaussian-chain approximation or stiffness-dependent weighting in this test.

### 2.1 Backbone reference

For homogeneous b0,kb,kappa, let q_i=r_(i+1)-r_i, ell_i=|q_i| and u_i=q_i/ell_i.
The independent exact sampling construction factorizes into

```text
p(ell) proportional to ell^2 exp[-kb(ell-b0)^2/(2kBT)], ell>0,
p(u_(i+1)|u_i) proportional to exp[(kappa/kBT) u_(i+1).u_i].
```

Define mu1=<ell>, mu2=<ell^2>, and h=coth(kappa/kBT)-kBT/kappa, with h=0 at
kappa=0, evaluated with the stable Langevin function in the CPU reference.
Then, for s>=1,

```text
C_t(s) = <u_i.u_(i+s)> = h^s,
B(d) = <|r_(i+d)-r_i|^2>
     = d*mu2 + 2*mu1^2 * sum_{s=1}^{d-1} (d-s)*h^s,
<Re^2> = B(N),
<Rg^2> = (1/m^2) * sum_{d=1}^N (m-d)*B(d).
```

These sums, rather than large-N wormlike-chain or Gaussian limits, define the
size targets. The existing `Chain.equilibrium_predictions` supplies radial
moments and Re^2; `tests/semiflexible_host.py:predictions` obtains Rg^2 by
subchain sums and tangent separations 1–4. Those helpers assume kBT=1 in their
host wrapper, consistent with the proposed matrix. They must not be silently
reused at another temperature. Radial moments use controlled quadrature, not
closed-form-integer moment assumptions. Before future analysis, verify
quadrature/tail errors at independently increased accuracy against a numerical
error budget below the scientific tolerance; do not count them as zero merely
because the initializer is described as exact.

Use independently seeded `Chain.sample` ensembles for reference distributions
of Re^2, Rg^2 and other quantities without a supplied analytic CDF. Its sampler
has no dynamics/burn-in or shared production CUDA RNG. Audit its factorized
law against the analytic moments before treating it as authority; sharing a
physical derivation with the production initializer is not an independent
algorithmic proof. Archive reference seed, count, parameters, code revision and
sampling uncertainty. Analytic targets take priority over an unnecessarily
noisy sampled estimate when both exist.

### 2.2 Slip-spring reference

At equilibrium the following are **annealed marginals**, not conditional laws
at fixed anchors:

```text
P(occupied c,i) = rho,
P(Z_c=z) = C(m,z)*C((M-1)*m,Z-z)/C(L,Z),
E[Z_c] = Z/M,
Var(Z_c) = m*rho*(1-rho)*(L-m)/(L-1),
Cov(Z_c,Z_d) = -Var(Z_c)/(M-1), c != d, M>1,
e = r_s-a: E[e_d]=0, E[e_d^2]=Var(e_d)=A2/3,
E[e_d e_f]=0 (d != f), E[|e|^2]=A2,
3|e|^2/A2 has a chi-square distribution with three degrees of freedom.
```

Binomial or Poisson approximations do not replace the hypergeometric reference.
Exclusion alone correlates site indicators; renewal creates temporal and
cross-chain dependence. Connector extension is prescribed by E1; it is **not**
an emergent tube diameter. Equilibrium second moments must be measured over
all live springs at observation times, not just newly renewed survivors or
samples selected at event times.

### 2.3 Joint-law checks beyond marginal agreement

Correct individual marginals need not imply the correct coupled distribution.
After changing variables from anchors to connectors e, E1 factorizes into the
bare backbone, uniform sites and independent Gaussian connectors. Add a small
preregistered joint diagnostic family. Let f_c=Re_c^2/<Re^2>_bb-1 and
sigma_Z=sqrt(Var(Z_c)). For the proposed nondegenerate M>1 matrix, both scores
below have exact target zero:

```text
A_joint = (1/(M*sigma_Z)) * sum_c f_c*(Z_c-Z/M),
B_joint = (1/(Z*A2)) * sum_c f_c*(sum_{j on c} |e_j|^2-Z_c*A2).
```

Analyze them as whole-replica statistics. They probe shape/population and
shape/connector dependence that matching all one-dimensional means could miss.
As a secondary diagnostic compare shape distributions conditional on Z_c=0,1,
>=2 to the same bare reference, flagging unsupported rare groups. These checks
require synchronized per-chain sizes, populations and connector sums; initial/
final audit snapshots also allow independent recomputation. No finite list of
moments/CDF cuts proves equality of the entire joint law. Acceptance is evidence
within the stated observable family, not a theorem about all observables.

### 2.4 Event frequencies: useful independent equilibrium checks

In ideal canonical equilibrium, for L>1 and m>=2, define
v=(L-Z)/(L-1), sigma=sqrt(A2/3), and

```text
J_attempt = Z*nu,
J_outward = Z*nu/m,
J_renew = (Z*nu/m) * ((2M-1)/(2M)) * v,
J_cross = (Z*nu/m) * ((M-1)/M) * v,
J_same = (Z*nu/m) * (1/(2M)) * v.
```

The source is occupied in the pre-event state; this supplies the missing
self-destination factor. Interior acceptance can also be independently averaged:
for a bond displacement of length ell, the integral of the Metropolis
acceptance over the conditional old anchor equals the overlap of two Gaussian
densities, `erfc(ell/(2*sqrt(2)*sigma))`. Thus for homogeneous chains,

```text
J_hop = Z*nu*(N/m)*v*
        E_radial[erfc(ell/(2*sqrt(2)*sigma))].
```

This follows by summing both directed internal bonds, each proposed at nu/2,
and using the distinct-site vacancy probability v. Future reference work must
verify this quadrature/overlap derivation independently before making it a
primary rate gate; the renewal expression is already checked in Stage C.
J_hop is not nu times the number of springs unconditionally. Ideal rates are
linear in nu at the same equilibrium law; relaxation of the coupled polymer
need not scale as 1/nu because its Brownian generator is unchanged.

These are continuous-time equilibrium reference rates. Finite-dt event
observations use the new, post-BD coordinates and may inherit numerical bias.
Compare counters per **physical duration** with finite-step sensitivity and
whole-replica uncertainty, not a naive independent-Poisson model for accepted
events. Only proposed attempt counts have the prescribed Poisson clock.

## 3. Proposed parameter matrix and exclusions

All numbers in this section are **proposals requiring scientific approval**.
Use b0=1,kb=30,kBT=zeta=1, unwrapped coordinates, homogeneous bending, renewal
on, stress off, full scalar output and double precision for primary science.

| Factor | Candidate levels | Reason |
|---|---|---|
| N | 8,32 | Local versus longer contour; no terminal-time claim |
| kappa | 0,2,10 | Flexible, intermediate and stiff backbone references |
| dt | 1e-4,2.5e-4 | Primary finer/coarser pair, ratio 2.5; proposed for testing, not validated |
| nu_hop | 10,100 | Factor ten in the jump dynamics; provisional numerical comparison, not calibrated physical rates |
| Host N_e | 16 (dilute),4 (denser stress case) | Vary constraint density without a kappa dependence |
| A2 | 5 at every kappa and both density levels | Provisional host-controlled extension, consistent with a prior short development example, not a measured tube scale |
| M | 64 per replica initially | Bounded ensemble; per-replica uncertainty retained |
| Independent replicas R | At least 32 per confirmatory cell; actual R from approved precision planning | A starting floor, not a promise of adequate power |

Set `Z=round_half_up(M*N/N_e)`; record the actual integer and rho. This gives:

| N | m | Z dilute / dense | rho dilute / dense |
|---:|---:|---|---|
| 8 | 9 | 32 / 128 | 1/18 / 2/9 |
| 32 | 33 | 128 / 512 | 2/33 / 8/33 |

N_e is the same host value across N and kappa for each regime; site density
rho therefore changes slightly with N by the specified N-versus-m convention.
Do not silently replace this with constant rho. Holding A2 fixed while varying
N_e is a numerical density stress test, not a new physical host calibration.
Neither parameter is allowed to acquire a probe-stiffness dependence.

The full D1 crossing contains **48 active cells** (2N*3kappa*2dt*2nu*2densities),
or 1536 replica-runs at the proposed R floor. This is a candidate scope, not a
small job already authorized or demonstrated feasible. Gate it behind the pilot
and a host budget. For bare-backbone controls, only 2N*3kappa*2dt=12 cells are
needed: crossing them with nu or host density would be redundant. NU=0 and
renewal-off controls are optional attribution cases, not another full matrix.
Their sector restrictions prevent D2 full-canonical population acceptance.

For D2 initially propose four sentinel base cases:
(N8,kappa0,dense), (N8,kappa10,dilute), (N32,kappa0,dilute),
(N32,kappa10,dense). Cross both rates at the finer dt with each of the three
required bias families in section 6: 24 D2 cells, or 768 replica-runs at R=32.
These sentinel results do not certify omitted combinations. Optional backbone
biases and timestep attribution runs add scope only after explicit approval.

Exclude Z=L from mixing claims: no vacant destination exists and anchors cannot
renew; Z=0 has no connector/population uncertainty. Exclude invalid/extremely
small A2, nonfinite coefficients, excessive Poisson means, heterogeneous kappa,
end escape without renewal, and arbitrarily larger nu justified as a supposed
adiabatic limit. Existing hard resource/numerical guards remain mandatory.

### 3.1 Timestep rationale and what two timesteps cannot prove

| Purpose | Proposed dt |
|---|---:|
| Primary finer | 1e-4 |
| Primary coarser | 2.5e-4 |
| Reserved finer reference | 5e-5 |
| Exploratory larger | 5e-4 |

Only the primary pair enters the matrix and initial pilot counts. Activate the
reserved reference for separately approved ambiguous/disagreeing cells; the
exploratory level needs a separate approved manifest/budget. None is validated.

An occupied bead has an added isotropic Hessian k_ss*I3 at fixed attachment
and fixed anchors. At A2=5, k_ss=3kBT/A2=0.6. Single occupancy makes H_ss
positive semidefinite and block diagonal with operator norm at most 0.6, so

```text
lambda_max(H_bb + H_ss) <= lambda_max(H_bb) + 0.6.
```

This is a fixed-attachment positional Hessian inequality, not stability of the
stochastic hopping/renewal process or an equilibrium-accuracy guarantee. It
needs no sampled slip-spring states and does not multiply curvature by Z.
The bare harmonic approximation `4kb+16kappa/b0^2` is not a nonlinear bound:
bending has singular short-bond geometry and local curvature fluctuates.
The [D0.1 screen](E1_STAGE_D_TIMESTEP_SCREENING.md) reports six-system Q99
curvatures and q=dt*Q99/zeta, with the additive 0.6 estimate separately.
Its finite sample may miss rare configurations. It reveals no reason to reject
2.5e-4 from the upcoming pilot, but cannot approve any timestep scientifically.

For a fixed positive harmonic mode lambda, EM is linearly stable only if
q=dt*lambda/zeta<2; its stationary variance is
`(kBT/lambda)/(1-q/2)`. The relative excess `q/(2-q)` illustrates bias before
instability, not an error bound on nonlinear chain sizes or connector moments.
For an isolated tether tau_ss=zeta/k_ss=5/3; neither that time nor the fastest
local backbone mode bounds slow equilibration. Tighter A2 requires reassessment.
Local stability, static equilibrium accuracy and dynamical accuracy are distinct.

Poisson processing permits repeated attempts within dt; nu*dt need not be
forced small to approximate a Bernoulli clock. Moving-bead coupling, invariant
bias and load still require dt/rate comparisons. The largest primary mean is
512*100*2.5e-4=12.8 attempts/step (25.6 at exploratory 5e-4), below the accepted
10000 guard; this is arithmetic, not performance evidence. Expected attempts
per physical time remain Z*nu_hop at every dt.

Two timesteps test agreement and bias sensitivity, not convergence order or
the exact dt->0 limit. The primary pair is not dt versus dt/2. The reserved
5e-5 is not exact. Prior N32 global-size/stationarity comparisons remained
unresolved, and earlier bare-backbone evidence does not validate active E1.

## 4. Data audit at the inspected revision

The following is source inspection, not execution of new runs.

| Existing output/interface | What it supports | Limitation for D1/D2 |
|---|---|---|
| `samples.csv` full mode | Step 0 and each scheduled per-chain mean_r,mean_r2,Re^2,Rg^2,tangent1..4,min_length | Rows, times, chains and contour pairs are not independent; no spring state in these frames |
| `initial.csv`, `final.csv` | Unwrapped chain/bead coordinates; offline conformation checks at both endpoints | No coordinate trajectory or interior-time long-separation tangent/distribution reconstruction |
| `initial_bonds.csv` | Initial per-bond lengths | No per-bond time series |
| `bond_statistics.csv` | Per-chain/bond mean lengths/squares and 32-bin-plus-overflow histogram over scheduled frames at step>=steps/2 | Hardcoded final-half summary; loses temporal ordering and cannot supply D1 drift or justify D2 burn-in |
| `fixed_slip_springs.csv` | Initial occupied sites/anchors | Always an initial snapshot, never the later state |
| `slip_springs_initial.csv`, `slip_springs_final.csv` | For Z>0,nu>0, stable ID, chain, bead, anchor | Endpoint connector/site/population observables can be paired with matching positions; no regular spring trajectory or serialized links |
| `hopping_metadata.json` v2 | Whole-run attempt/interior-accept/outward/renewal counters, rate, splitting, domains | No interval rates, per-ID renewal coverage or chain entry/exit history |
| `metadata.json`, `parameters.txt`, failures | Effective precision/model coefficients, seed, duration, timings, capacities; failure evidence | No complete executable/toolchain/source identity receipt; no restart state |
| `--initial` | Supplied coordinate triples | Does not import attachment IDs/anchors; normal spring initialization still runs, so controlled D2 spring states are not currently expressible |

Force-only output is not a dynamics energy time series. Compact scalars currently
require stress streaming; they cannot be used with active springs under the
accepted stress prohibition. Stress must not be enabled to obtain compact
output. The current full scalars already support the minimum tangent separations
1–4; propose additional s=8 (N>=9) and s=16 (N32) to probe longer contour scales.
They require future diagnostics or synchronized coordinate snapshots.

Existing endpoints alone could support a costly independently initialized D1
endpoint design at separately rerun durations. Such reruns would share prefixes
if seeds were reused and are not additional independent replicas. They do not
replace needed D2 time series or controlled initial states. No source or output
format is modified in D0.

### 4.1 Minimum future instrumentation, separately authorized

Propose an opt-in equilibrium observer, read-only with respect to dynamics/RNGs,
without a stress dependency or changes to force/update kernels, transition
probabilities or event ordering. New per-event diagnostic counters, if approved,
would be additive bookkeeping at accepted transitions:

1. At the same post-batch state as scalar observations, record step/time, a
   full occupancy bitmap (or equivalent per-chain/site indicators), all Z_c,
   connector component sums and squares/cross products, per-chain |e|^2 sums and a fixed
   connector CDF/histogram, and the existing backbone scalars. Define e=r-a.
   Record a few synchronized R/S/A snapshots including t=0 for independent
   offline recomputation. Preserve exact chain/ID associations in snapshots.
2. Record interval differences of all cumulative event counters, with actual
   time denominators; per-ID renewal counts or last-renewal steps and per-chain
   accepted entry/exit counts. Keep O(Z+M) counters, not an unbounded event log.
   Preserve `accepted`=interior hops and separate same/cross-chain renewal.
3. Add contour tangent scalars at the approved longer separations and fixed
   CDF thresholds for size/connector distributions where raw values are omitted.
   Keep per-chain backbone rows and whole-replica joint observation records;
   online means alone cannot reconstruct autocorrelation or ensemble tests.
4. Provide a validated import of complete initial R, stable IDs, S, A and
   reconstructed contour links/occupancy for controlled D2 arms. Exact D1
   starts remain the default production initializer, cross-checked against the
   independent CPU reference. Reject duplicate/missing IDs or invalid sites.
5. Optionally at a small predefined diagnostic subset, observe spring moments
   immediately after BD and after the jump batch. This distinguishes propagation
   of integration error from jump effects; it does not change the splitting.

These are data requirements, not instructions to implement now. Every schema
must specify integer steps, exact observation phase, units, finite/minimum and
coverage checks, cumulative-counter semantics, and final partial intervals.
Observer behavior must preserve disabled-path compatibility and RNG isolation.
A snapshot CSV is not a restart checkpoint. Future restart support, if approved,
must save complete R/S/A, absolute next BD step, counters, initial-reference
state needed by outputs, precision and RNG identities; resetting step to zero
would reuse Philox streams. In D0, checkpointing means analysis/receipt progress
only; current simulator interruption requires a documented fresh run, not a
purported continuation from `final.csv`.

## 5. D1 — exact-start preservation procedure

For each approved cell and independent replica:

1. Sample the bare equilibrium backbone independently for all chains using
   the accepted exact factorized initializer; sample Z distinct sites uniformly
   and conditional independent Gaussian anchors. Archive the actual uploaded,
   precision-rounded state and RNG domains. Cross-check t=0 against analytic
   and independent equilibrium reference distributions. Using `--initial` does
   not by itself certify equilibrium. All chains may start at bead zero: only
   internal conformations, site statistics and relative connectors are tested,
   not a normalizable absolute-position equilibrium on infinite space.
2. Observe t=0 before integration. Evolve with the accepted complete BD-then-
   hopping/renewal composition, one batch per BD step, fixed anchors between
   renewals. Observe
   synchronized backbone/spring quantities after completed batches. Never
   recenter evolving beads without the corresponding anchor transformation;
   offline translation-invariant shape calculations require no dynamics change.
3. Propose shared physical times 0,.0005,.0025,.01,.05,.25,1,2,
   subject to a pilot-informed final horizon. The old 5e-5 and 1e-4 shared
   frames cannot occur at primary coarser dt=2.5e-4; 2.5e-4 itself is not an
   integer step at primary finer dt=1e-4. Replace the shared early frames
   explicitly with .0005, the smallest common positive time; never round or
   interpolate. Integer schedules are:

   | dt | Steps at the shared times above |
   |---:|---|
   | 1e-4 | 0,5,25,100,500,2500,10000,20000 |
   | 2.5e-4 | 0,2,10,40,200,1000,4000,8000 |
   | 5e-5 (reserved) | 0,10,50,200,1000,5000,20000,40000 |
   | 5e-4 (exploratory) | 0,1,5,20,100,500,2000,4000 |

   Additionally retain step 1 at each dt as a timestep-specific first-update
   diagnostic; those unequal times are not cross-dt contrasts. Serialize
   integer schedules. The present constant `--sample` alone does not provide
   the union of selected frames and regular records.
4. Compare each time ensemble to the absolute canonical reference; also compare
   paired changes from t=0 within each replica. Require both: a chance initial
   offset must not cancel a later bias. Propose early/middle/late windows only
   after the pilot fixes duration, before confirmatory runs. Record drift and
   window contrasts, with simultaneous uncertainty across the whole schedule.
5. Compare the primary finer and coarser dt at identical times/durations and
   parameters, and compare both nu levels against the same target. Use independent seeds across cells
   unless an explicit paired-start design and its covariance are preregistered.
   Sharing a seed across timesteps does not couple Brownian paths correctly;
   step-based Philox and different Poisson batches preclude assuming pathwise
   cancellation. A shared initial ensemble is possible with a declared pairing,
   but is not an independent reference ensemble.

There is **no burn-in deletion in D1**: the intended initial ensemble is already
equilibrium. Existing final-half bond summaries do not override this. Early
transients induced by the numerical integrator are evidence to retain.

These observations exercise the complete coupled force/update/jump process:
changes of backbone conformations under active forces, connector evolution
between renewals, and joint population/attachment evolution with moving beads.
Frozen-coordinate detailed balance or fresh-anchor checks remain useful
controls but cannot pass D1 on their own.

### 5.1 Attribution without overclaiming

For an exact conditional Brownian propagator B and exact jump propagator J,
`pi B=pi` and `pi J=pi` imply `pi BJ=pi` for any split duration. Lie splitting
would change finite-time dynamics but would not by itself change this invariant
measure. Production uses Euler–Maruyama, not exact B. Its invariant defect and
interaction with the following jumps can depend on dt and nu. D1 measures that
combined numerical effect; two-step comparisons cannot uniquely decompose it.

Use the following evidence sequence, with any extra runs separately approved:

- Failure already at t=0 suggests ensemble construction, precision, observer
  or reference/provenance defects. Do not repair it by discarding early frames.
- Failed invariants, finite checks or counter identities are numerical failures,
  not equilibrium deviations to average away.
- Deviations shrinking with dt support finite-step bias; persistence of a
  resolved discrepancy under refinement demands implementation/reference checks
  or more refined analysis, not a declared convergence order from two points.
- Bare controls distinguish baseline integrator error from active-spring effects.
  Exact-start NU=0 can test preservation of the mixture of conditional sectors;
  its lack of full mixing does not invalidate that preservation question.
- Nu dependence of static errors at fixed dt flags interaction with jump coupling
  or sampling; only tighter uncertainty/refinement distinguishes them. Changing
  operator order or replacing kernels is outside D0 and not needed as a first
  response. A high nu is not a shortcut to equilibrium acceptance.
- Wide intervals without a resolved drift are insufficient evidence, not proof
  of no bias. A bounded horizon limits the preservation claim to that horizon.

## 6. D2 — controlled nonequilibrium ensembles

Use independently sampled exact backbones initially, then alter only the
specified spring variables. Keep single occupancy, fixed global Z, finite
anchors and correct sorted contour links in every start. Do not simulate an
illegal crossed/duplicate state in order to test relaxation.

| Required bias arm | Construction | Main distances to track |
|---|---|---|
| Population concentration | Select a declared subset of chain labels and fill whole chains up to m, with one residual chain if needed; others empty. Draw anchors conditionally correctly | Population CDF, variance, empty/one/multiple fractions, initially loaded-versus-empty group contrast, per-chain entry/exit and size statistics |
| Contour concentration | Draw chain counts from a canonical distinct-site sample, then pack each chain's same count into a declared left-biased block; retain each count and redraw correct conditional anchors | Site/contour occupancy CDF and left-right asymmetry; population law initially correct is a control, not proof of later equilibrium |
| Anchor bias | Exact sites and backbones, but zero-mean Gaussian connector variance 4*A2/3 instead of A2/3 | All connector components, radial CDF and moments, subsequent conformation/population response, renewal coverage |

Propose a separate optional anchor-mean arm with displacement mean
`sqrt(A2/3)*(1,0,0)` and correct variance to expose directional relaxation.
Do not combine it with the variance arm and then lose attribution. Optional
backbone-biased starts can use independently oriented straight chains with
valid positive radial equilibrium lengths and otherwise exact springs. They
probe shape relaxation directly and require extra matrix/budget approval.
No collapsed active angles or unbounded artificially stretched connectors are
needed. Every biased realization and its construction RNG must be archived.

Track distances from the analytic/reference target **separately** for global
sizes, local bond/tangent statistics, connectors, contour occupancy and chain
populations. Proposed distances are normalized moment errors, fixed-grid CDF
errors, full discrete population CDF error, and declared label-group/asymmetry
contrasts. Distances need not decay monotonically: biased anchors may first
distort the backbone before it recovers. Correct connectors after a few fresh
renewals do not imply correct global populations or shapes.

Propose relaxation evidence only if all of the following hold:

- Late absolute discrepancies meet the same approved equivalence margins as D1;
  comparison to matched exact-start D1 runs also meets its declared margin.
  A numerically biased D1 plateau is not a new equilibrium reference for D2.
- Three consecutive predefined late windows, each at least five times the
  largest credibly estimated relevant autocorrelation time, meet equivalence;
  between-window contrasts and slope times window duration are bounded within
  half the corresponding scientific margin. Use simultaneous intervals.
- The conclusion is stable across independent starts and the observed bias
  families; retain initially loaded/empty chain labels in comparisons so global
  histograms cannot hide a persistent label-population bias. Observation support
  for rare population regions and slow coordinates is adequate.
- Renewal/mixing support is documented. Proposed diagnostic floors per replica
  are at least 20*M accepted **cross-chain** renewals and at least 95% of stable
  IDs renewed once, plus recorded chain entry/exit coverage. These are support
  flags, **not sufficient conditions or independent samples**. Counts can be
  dominated by repeated motion of a few springs. No conclusion follows from
  any fixed number of successful renewals alone.

The mean equilibrium cross-chain event budget gives an informative planning
scale, `T_count approximately (20*M)/J_cross`; use its uncertainty and never
apply it as a nonequilibrium rate guarantee. Slow central springs can remain
unrenewed despite many total events. Obtain uncertainty from complete replica
population histories, including residence/entry/exit correlations. For rare
population categories, require a preregistered precision bound; an expected
raw count (proposed support flag: 25 across the planned ensemble) does not
convert dependent counts into 25 independent observations. Report unresolved
tails separately rather than merging them after seeing an empty histogram.

No arbitrary fraction of a D2 trajectory is called burn-in. Pilot estimates
set candidate windows for an independent confirmatory ensemble. If bias or
slow trends persist, classify incomplete equilibration over the demonstrated
horizon. A flat but displaced plateau could be metastability, an inaccessible
sector or numerical bias; distinguish by D1 and refinement evidence where
possible, otherwise retain the ambiguity. Do not infer unrestricted ergodicity
from the successful cases or reinterpret insufficient support as a pass.

## 7. Statistical estimators and decision rules

### 7.1 Units and references

The primary independent unit is an entire separately seeded **M-chain replica**.
At a time t form a replica vector Y_r(t): average chain Re^2/Rg^2, bond moments
and tangent means; average connector moments over all Z live springs; occupancy
at each contour index averaged over chains; and population probabilities
`H_r(z,t)=M^-1 sum_c 1[Z_c(t)=z]`. Keep left/right and initially biased label-
group contrasts. Pool all z in a CDF for the population shape, without assuming
independent multinomial chain draws. Required contour occupancy tests do not
by themselves certify every labeled flat site to the same precision.

For an observable use the mean of Y_r over R independent replicas and its
replica-to-replica variance divided by R. At fixed times, trajectory correlation
does not multiply the number of ensemble samples. For window averages compute
one average per replica using common time weights; whole-replica vectors retain
all covariance across times and observables. Do not use chains, Cartesian
components, springs, contour pairs, frames, windows or overlapping origins as
independent replicate counts. Treat a declared paired contrast as one paired
vector per independent replica pair.

For estimated backbone references, add their independent sampling variance
(or use an independent reference-resampling hierarchy), plus a separately
bounded quadrature/truncation error. Never subtract reference error using a
shared initializer seed. Choose future reference sample size to place its
uncertainty contribution below one quarter of the approved error margin; that
is an error-budget goal, not a preset claim about a particular sample count.
Precision rounding of uploaded parameters and k_ss must be accounted for:
report intended continuum targets and independently computed effective-parameter
corrections rather than moving target definitions to fit the output.

Estimate autocorrelation only for apparently stationary parts of each relevant
replica observable, with positive-sequence or self-consistent-window estimates
and block-size stability checks. Quote uncertainty/truncation of tau_int and
use a conservative upper estimate. Do not estimate a stationary IAT from the
initial D2 drift. If no stable plateau or IAT fits in the pilot, report a lower
bound/insufficient horizon, not a small estimated mixing time. Block estimates
within runs are diagnostics; resampling entire replicas is the primary scheme.

### 7.2 Proposed scientific accuracy margins

These are prospective **approval candidates**, not historical frozen thresholds
or values tuned to a pilot. They target percent-level equilibrium moments and
visible distribution distortions, not machine equality.

| Observable/contrast against reference | Proposed allowed absolute error Delta |
|---|---|
| <Re^2>, <Rg^2> | 2% of the respective positive exact target |
| Bond <ell>, <ell^2> | 1% of the respective positive target |
| Tangent C_t(s), approved s including near-zero targets | 0.02 absolute |
| Mean-square connector extension | 2% of A2 |
| Connector Cartesian means | 0.05*sqrt(A2/3) each |
| Cartesian second moments and centered variances | 2% of A2/3 each; gate means too |
| Cartesian off-diagonal moments | 0.02*A2/3 absolute |
| Dimensionless A_joint, B_joint | 0.02 absolute each |
| Contour-site occupancy probability p_i | min(0.01,0.10*rho) absolute at each i |
| Population CDF, at every integer threshold 0..m | 0.02 absolute per CDF value |
| Size and connector CDFs, approved fixed thresholds | 0.02 absolute per CDF value |
| Equilibrium accepted event rates against approved ideal references | 5% of each positive rate; interval counters and dt sensitivity required |

Propose size-reference and connector CDF thresholds at target quantiles
.01,.05,.10,.25,.50,.75,.90,.95,.99. For sizes, derive them from a separately
archived reference ensemble and quantify threshold/CDF uncertainty. Use separate
reference subsets for threshold calibration and CDF evaluation, or propagate
their joint uncertainty explicitly; for
connectors use the analytic chi-square law and Cartesian normal quantiles.
These are finite-grid CDF gates, not a claim to control the full continuous
CDF sup norm or all tails. Population CDF uses every integer threshold and is
not a substitute for recording empty, one and multiple-spring frequencies.
Exact occupancy/population sums, unique identities, finite values, and
counter identities have **zero** allowed violation, not statistical margins.

For timestep and rate contrasts, propose half the corresponding static Delta
as the maximum difference, in addition to each cell meeting its absolute
reference margin. Same for precision comparisons on the declared subset.
Reference uncertainty and numerical error budgets are included in the interval,
not added as a permissive tolerance adjustment. These stricter contrasts can
remain unresolved even when each individual comparison passes.

### 7.3 Simultaneous intervals, equivalence and power

Before confirmatory execution, enumerate the finite family of primary comparisons
K across approved cells, times/windows, contrasts, components, contour separations
and distribution thresholds. Propose a familywise error budget alpha=0.05 and
Bonferroni simultaneous two-sided intervals at coverage 1-alpha/K each.
Student-t/Welch intervals across replicas are a large-replica approximation,
not an exact finite-sample theorem for skewed observables. R>=32 alone does not
guarantee their validity. Check replica dispersion and robustness in planning;
use more replicas or an approved, independently justified whole-replica
simultaneous bootstrap if needed, **before** confirmatory outcomes are seen.
For bounded occupancy/CDF means, a conservative Hoeffding interval across
independent replica averages is a distribution-free fallback; within-replica
chain independence is unnecessary. If too wide, its result is insufficient
precision, not permission to pool chains. Pilot data are excluded from final
confirmatory gates; repeated unplanned looks need a new error-spending plan.

For discrepancy d, let I be its simultaneous confidence interval expanded by
bounded numerical/reference error. The equivalence region is [-Delta,+Delta].
Do not use p>0.05 from a test of zero difference as evidence of equivalence.

| Classification | Required interpretation |
|---|---|
| Scientific agreement within scope | I lies wholly inside the equivalence region for every required gate, with complete valid evidence and D2 relaxation/support conditions when relevant |
| Scientific disagreement | A valid, adequately equilibrated estimate has I wholly outside the allowed region for at least one gate; D1 resolved drift beyond tolerance also qualifies |
| Insufficient statistical evidence | I overlaps a tolerance boundary, missing power/IAT/tail support, or approximation validity is unestablished; a wide interval containing zero cannot pass |
| Incomplete equilibration | D2 retains supported initial-state dependence, drift, or fails its preregistered late-window/renewal-support conditions at the tested horizon; distinguish underpowered evidence explicitly |
| Numerical or provenance failure | Nonfinite/invariant/counter failure, incomplete/corrupt schedule/data, unknown executable or parameter identity, or failed authentication; no physical inference from that run |

A persistent D2 discrepancy with valid matched D1 preservation is first reported
as failure to demonstrate relaxation, not automatically a wrong invariant
measure. Agreement is bounded to approved cells, margins, times and initial
families. Report all statuses per gate and per cell; do not average a failure
away with passes. A case can carry both incomplete-equilibration and insufficient-
precision flags, with numerical/provenance failures taking precedence.

Plan R with pilot replica variance, not the number of frames. For a scalar
replica SD s and remaining margin Delta_eff after reference/numerical budgets,
a prospective approximation is

```text
R_goal approximately [(c_simultaneous + z_power) * s / Delta_eff]^2,
```

using approved power (candidate 80%) and conservative variance uncertainty.
Plan all primary endpoints, not only the easiest local moment. Predefine any
maximum R and resource budget; if the goal exceeds them, report insufficient
feasibility or seek an explicit scope/budget amendment. For illustration only,
a hypothetical replica relative SD 0.10 and critical value 5 already needs
roughly (5*0.10/0.02)^2=625 replicas just for a 2% half-width before power/reference
allowances. Neither SD nor critical value is a measurement here. Thus the
R=32 floor and 48-cell grid cannot honestly be advertised as a powered
production protocol before the pilot. Tight tolerances are not loosened to
make the grid appear manageable.

## 8. Proposed pilot, feasibility and data volume

**No pilot is authorized by D0.** After separate instrumentation review and
scientific approval of tolerances, propose a bounded host-only planning pilot:

- Four corner cases: (N8,kappa0,dilute,nu10),
  (N8,kappa10,dense,nu100), (N32,kappa0,dense,nu100),
  (N32,kappa10,dilute,nu10); both proposed dt levels; four independent exact-start
  replicas each: 32 short runs. This estimates costs/dispersion, not acceptance.
- Start with T=0.25 and a dense scalar/spring diagnostic cadence 5e-4.
  This is exactly 5 finer or 2 coarser primary steps (10 reserved, 1 exploratory); retain
  separately tagged step-1 frames. Propose a later cadence
  0.005 for planning longer records: exactly 50 finer or 20 coarser steps (100
  reserved, 10 exploratory), subject to a documented pilot IAT study.
  Sampling at all BD steps is unnecessary for static ensemble means, but
  the retained cadence must resolve the slow-coordinate correlation analysis.
- A preregistered optional extension of selected existing replicas to T=.5,1,2
  is for IAT/cost assessment only and requires correct continuation support
  or explicit fresh reruns. It is not assumed feasible with current outputs.
  Include a few separately approved D2 starts only after the exact-start cost
  pilot; their cost/horizon is not inferred from near-equilibrium IAT alone.
- Candidate limits: 120 seconds per pilot run, 3600 seconds aggregate GPU wall
  time, 5 GiB pilot storage, and the existing 2 GiB workspace guard. Stop at
  any budget without changing physics or dropping failures. Missing pilot
  cells/horizons remain missing; the limits do not authorize work now.
- Estimate distribution/observable-specific replica variance, IAT bounds,
  per-step integration/diagnostic/event costs, observation and output costs,
  actual file sizes, CPU/GPU memory and renewal coverage. Then propose fixed
  confirmation R,T,cadence,windows and seed manifest with no outcome-based
  tolerance edits. New confirmatory data must be independent of pilot data.

For T=.25 the primary run lengths are 2500/1000 steps (finer/coarser),
versus 10000/5000 for the old 2.5e-5/5e-5 pair. The 32-run initial pilot
therefore totals 56000 replica BD steps, versus 240000 previously, a factor
30/7 reduction (76.7% fewer). Optional horizons .5,1,2 require respectively
5000/2000,10000/4000,20000/8000 primary steps; these are total lengths, not
extension increments. Reserved/exploratory T=.25 lengths are 5000/500.
The dense cadence yields 501 regular frames including t=0; the separate
primary step-1 frame adds one. Shared selected times are already cadence
multiples. Count additional audit snapshots separately.
These reductions apply to BD steps, not total runtime. Observation counts at
fixed physical cadence and expected hopping attempts Z*nu*T are unchanged;
serial hopping and diagnostics may dominate. Keep existing wall/storage caps.

Production horizon must address the slowest *measured supported* internal,
occupancy, connector and population coordinate; no Rouse terminal-time formula
or tau_ss alone sets it. D1 exact-start ensemble snapshots need not wait for
mixing to be unbiased, but a short horizon cannot rule out later drift. D2
may require substantially longer than T=2, especially for N32/low nu/denser
populations. If the bounded pilot cannot resolve this, the answer is a revised
host study proposal, not a declaration of full equilibration.

At M64,N32, L=2112 and Z<=512. The current simulator uses O(L+Z) state plus
O(M*N) histogram workspace; Stage C adds 40 explicitly allocated device bytes
of counters, not 40 bytes for the entire dynamics. New history must be streamed,
not retained in GPU memory. A double-coordinate snapshot alone has 24L=50688
payload bytes, before headers/IDs/anchors; a full occupancy bitmap is 264 bytes
per frame. For a hypothetical T=2,cadence=.005 record there are 401 frames and
25664 existing per-chain scalar rows; raw double coordinates at every frame
would add about 20 MB before anchors/text overhead. These are storage arithmetic,
not measured file sizes or recommended full-coordinate recording. Prefer scalar
records/bitmaps plus a few complete audit snapshots. Multiply all costs by R,
cell count, precision copies, and reference/analysis artifacts before approval.
Do not assume CSV compression ratios. Bound host analysis memory by streaming
one replica at a time and retaining only the replica estimators required for
simultaneous inference; preserve original records/checksums.

For cost budgeting use
`steps=T/dt` (require an exact integer), expected attempts `Z*nu*T`, and
`raw scalar rows approximately M*(1+floor(T/cadence))`. Accepted-renewal
cost includes the serial destination scan. Stage C measured only a tiny
N8,M64,Z32,nu100,100-step example: single integration/overall 79.827/127.798
and double 164.658/214.289 ns/bead/step on the recorded RTX3060Ti/CUDA13 host.
Its report explicitly disclaims throughput extrapolation; these measurements
do not predict N32,dense,other nu, future observer or long-run performance.
The separate bare-backbone GPU and CPU stress benchmarks do not budget active
E1 work. No D0 runtime/memory measurement is invented, and no event processor
optimization is proposed.

## 9. Provenance, review and execution gates

A future independently authenticated E1 campaign must record and checksum:

- Source commit, clean/dirty status and exact source-diff identity; protocol
  version/hash, approved manifest/hash, approval record and amendments.
- Executable SHA256, real build command, compiler/host-compiler versions,
  CUDA toolkit, architecture, precision, optimization/fast-math flags, linked
  dependencies, build log and binary-to-source receipt. A no-op `make` or
  installed nvcc version is not compilation provenance.
- GPU model, driver/runtime/toolkit versions, host/CPU/thread environment and
  analysis/library versions; explicit unsupported hardware/toolchain status.
  Preserve the documented CUDA11.5 compatibility limitation.
- N,m,M,L,Z,rho,Ne and its rounding, b0,kb,kappa,kBT,zeta,A2, effective stored
  coefficients, dt,nu,renewal-on,stress-off,one-BD-step batch interval, splitting
  and all RNG domains.
- Full seed and immutable replica identity; distinct initialization/backbone/
  jump/renewal/reference/construction domains; initial ensemble family and
  recipe/version, initial-state hashes, uploaded precision, any declared pairing.
- Absolute starting/ending BD steps, physical duration, observation and counter
  schedules/phase, integer time mapping, expected/actual records, failures and
  counters; actual performance, memory and disk records with timer scopes.
- Raw output checksums/sizes, schema versions, completeness receipts, reference
  identities/sample sizes/errors and analysis commit/configuration, comparison
  family K, margins/alpha/power, uncertainty method and all gate classifications.

Keep new E1 roots and receipts separate from frozen historical campaigns.
Never edit their source allowlists, manifests, plan hashes or thresholds, and
never call their expected later-source authentication refusals physical failures
or bypass them to authenticate E1. Do not overwrite pinned binaries/outputs.
Archive interrupted and failed runs with explicit status. An analysis cache may
reuse only complete authenticated raw data under the same approved analysis
identity; a changed analysis/protocol requires a new receipt and preserved
previous result. Record optional stopping and extensions rather than relabeling
them as an originally frozen duration.

Review sequence:

1. Approve the proposed scientific accuracy margins, primary distributions,
   comparison family and error budget independently of pilot outcomes.
2. Separately authorize minimal observer/import/provenance implementation and
   bounded correctness verification; D0 supplies requirements only.
3. Approve the exact pilot manifest and resource caps before any execution.
4. Review feasibility/IAT/variance and missing support; fix final R,M,T,cadence,
   windows, seed list, precision subset and any reserved refinement cells.
   Freeze a separately hashed executable protocol/manifest before confirmation.
5. Separately authorize host execution. Analyze all required outcomes under the
   frozen protocol, preserve failures and report scope-limited D1/D2 statuses.

## 10. Unresolved decisions requiring scientific approval

The numerical proposals have not been scientifically frozen. Review must settle:

1. Whether Ne=16/4 and A2=5 are appropriate host-controlled numerical probes,
   without treating them as a physical host calibration or tube diameter.
2. Whether the dt pair and nu=10/100 span an informative regime, and when to
   activate the reserved third timestep; all rate/timestep acceptance is pending.
3. Whether the proposed 1–2% moment, absolute correlation/probability/CDF and 5%
   event-rate and joint-score margins meet scientific needs, including omitted
   continuous tails; independently approve the new interior-rate reference.
4. The final comparison family and simultaneous-interval method, reference
   accuracy budget, power target and maximum feasible R. Decide whether to
   reduce declared scope or increase resources if equivalence is underpowered.
5. M and reference ensemble sizes; pilot/final durations/cadences/windows,
   renewal/rare-category support floors, D2 sentinel scope and optional bias arms.
6. Minimal time-resolved schemas, long-separation tangent coverage, initial
   state importer, audit snapshots, and whether true restart support is worth
   separate implementation. Decide how to retain evidence without bulk trajectories.
7. A precision confirmation subset: propose N8/N32,kappa0/10,dense,nu100 at
   both dt levels (8 cells) in float with independent replicas and matched double
   targets; this does not validate untested float matrix entries. No cross-
   precision trajectory identity or unconditional double accuracy is assumed.
8. Host wall-time/storage budgets and authenticated new E1 campaign preparation.

At D0 completion the deliverable is this reviewed-by-author design and its Git
identity, **not D1/D2 scientific acceptance or execution approval**. A/B/C remain
accepted within their bounded scope. No future tests, simulations or scientific
results are asserted by the proposed commands/settings in this document.
