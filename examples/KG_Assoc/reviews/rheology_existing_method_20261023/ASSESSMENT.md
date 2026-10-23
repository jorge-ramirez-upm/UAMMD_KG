# Established six-channel rheology: implementation and P4 evidence

CPU-only review, 2026-10-23; starting SHA
`75d169da8a54fc49032c8c41c22156a6d0e6c432`.
No stress, correlator, integrator, force or reaction implementation was changed.

## Equation, conventions and source map

With symmetric intensive stress sigma, define its traceless part S and normal
stress differences Nxy=sigma_xx−sigma_yy, Nxz=sigma_xx−sigma_zz,
Nyz=sigma_yy−sigma_zz. The implemented isotropic deviatoric projection is

    G(t) = V/(10 kB T) <S(0):S(t)>
         = V/(5 kB T) [Cxy + Cxz + Cyz + (CNxy + CNxz + CNyz)/6].

The contraction counts the three off-diagonal terms twice; the sum of the three
normal-difference products is three times the diagonal traceless contraction.
Under isotropic covariance each normal-difference autocorrelation is four times
one shear autocorrelation, so the six-channel average recovers the common shear
modulus. This identity concerns ensemble isotropy; finite-sample anisotropy and
nonstationarity require diagnostics. The three normal differences obey
**Nxz=Nxy+Nyz** and are not three independent observables or extra replicas.
Historical wording calling six channels “independent” must not be read as six
statistical replicas: the traceless symmetric tensor has five independent components.
No single-xy replacement is proposed.

The correlator receives intensive xy,xz,yz,Nxy,Nxz,Nyz. Output Gxy etc already
include V; they are not bare stress correlations. The exact output is
`G=(Gxy+Gxz+Gyz)/(5T)+(GNxy+GNxz+GNyz)/(30T)`.
Reduced units use kB=1, epsilon=sigma=mass unit=1 and the frozen T=1, dt=.01;
G has pressure units and viscosity pressure×time. Do not multiply by V twice,
replace target T with an instantaneous kinetic temperature, or count channels
as independent samples. Correlations are uncentered products; zero mean of shear
and normal differences is an isotropic equilibrium assumption, not enforced by
subtracting sample means. A persistent deviatoric mean could contaminate a tail.

| Source at reviewed SHA | Implementation evidence |
|---|---|
| `kg_assoc_production.cu:1006–1049` | WCA, permanent and reversible FENE are integrator interactors; Correlator6(40,16,2) initialized empty. |
| `kg_assoc_production.cu:1061–1094` | 4096-entry device buffer, synchronized flush into all six correlator inputs, 256-thread particle reduction. |
| `kg_assoc_production.cu:1143–1201` | Advance MD; scheduled chemistry; refresh changed association cache; sample current post-chemistry stress. No step-zero stress sample. G(0) is the zero-lag average over sampled steps, not an initial-time tensor. |
| `kg_assoc_production.cu:1268–1296` | Flush/evaluate, multiply each channel by V, exact 1/(5T),1/(30T) normalization, lag×dt and common raw n_pairs. |
| `../KG/kg_runtime.cuh:379–417,562–599,635–699` | Tensor is [sum m vv −WCA_cache/2 + permanent_cache/2 + association_cache/2]/V, with the cache-specific signs and doubled endpoints. |
| `../KG/kg_interactors.cuh:220–282,309–348` | WCA minimum-image pair stress and permanent-FENE bonded-cache convention. |
| `kg_assoc_interactors.cuh:40–98,116–145` | Live reciprocal partner topology; shifted FENE stress; force passes refresh caches. |
| `../KG/correlator.cpp:585–699`; `correlator.h` | Six product sums and one denominator at each lag, block averaging before coarse levels, populated output bins. |
| `kg_assoc_campaign_production.cu` | Includes the same production implementation; frozen campaign CLI, 100M default, no alternate stress estimator. |
| `analysis/analyze_p42_rheology_pilot.py:52–136` | Reader validates sampling, temperature, lag/count agreement and recomputes G from all six channels for every row. |

The stress includes particle kinetic, all intended WCA nonbonded, permanent FENE
and reversible shifted-FENE contributions. Association adds no second WCA term;
its constant energy shift has no force/stress derivative. An active reversible
bond contributes mechanically out to R0, irrespective of the kinetic candidate
cutoff r_assoc. The Langevin thermostat is not separately inserted as a fictitious
pair virial. This is the implemented model's microscopic stress and time sampling,
not proof of a thermostat-independent or continuous-time material response.

A normal force pass supplies WCA/permanent/association caches at current coordinates.
On a chemistry step only association partners change, so only its stress cache is
refreshed before reduction. All operations use the sampling/integrator stream,
and buffered host transfer synchronizes it. This optimized ordering supersedes the
older prose describing a redundant full three-interactor stress-only pass. Stress,
event and topology observations refer to the post-chemistry state at the same
absolute step. A buffer flush changes transfer cadence, not physical sampling.

## Multi-tau sampling and continuity

Stress is sampled every step (time spacing .01). Parameters are 40 levels, p=16,
m=2, dmin=8. Fine lags are j=0..15. At level k>0, lags j=8..15 correspond to
`j*2^k*.01`. Incoming pairs of samples are **averaged** recursively; the coarse
correlations are block-averaged correlations, not exact unsmoothed point-ACF
values. For N samples, fine counts are N−j, and coarse counts are
`floor(N/2^k)−j` when positive. The implementation excludes its deepest populated
level (`k<kmax`); all five finite 32M grids were checked against the populated-count
formula, with no assumption that all 40 levels yield output.

LAG_GRID.csv supplies the actual finite grids/counts for 1M,8M,16M,32M,64M,100M
sample lengths. At 32M the raw last lag is 293601.28 with only one contribution;
threshold-8 eligibility ends at 157286.4, and threshold-128 at 19660.8. These
eligibility horizons are not resolved terminal relaxation or independent-origin
counts. Never divide a variance by sqrt(n_pairs) to claim rheological precision.
Use actual lag widths for integration; multi-tau smoothing/discretization can
matter where G changes appreciably across a coarse block.

`Correlator6` itself has no six-channel persistence interface. The derived
`kg_assoc_correlator_checkpoint.cuh` utility serializes all six rings, numerators,
counts, partial block accumulators and cursors. Its existing deterministic test
saves at sample 12345, loads exactly, and continues both objects to 25000 with
identical six channels, counts and lags. It is **not used by campaign production**.
It does not serialize the integrator, RNG, particles or chemistry, and its native
binary format is not evidence of portable full-simulation checkpointing.

The strict campaign executable emits no reloadable production restart/chemistry
pair, only archival final state and an atomic completion marker. It initializes
an empty correlator for each run. Historical ordinary `kg_assoc_production`
restart segments can reload physical/chemical pairs, but start fresh GJ noise,
COM history and correlator; they are not bitwise production continuation. No
correlation or lifetime origin can cross such boundaries legitimately. One cannot
resume the campaign by restoring the correlator alone, concatenate whole-run
correlation files to invent cross-segment pairs, or treat different restart times
of one family as independent replicas.

## Existing test coverage and evidence strength

P4.0/P4.1 GPU tests were already executed on TITAN Xp, as recorded in
VALIDATION.md (P4.0/P4.1/P4.2 sections). `kg_assoc_stress_test.cu` checks a non-axis
aligned bond against analytic values in six tensor entries, reversal invariance,
trace/virial sign, no duplicated/stale association stress after break, full
kinetic+WCA+permanent+association decomposition, asynchronous versus direct reduction,
force-cache versus recomputation and live chemistry creation/breaking. Earlier
campaign 100k smokes checked every-step stress, cadence, output consumers and atomic
completion. These are historical GPU evidence; no GPU test was rerun here, and
none establishes stationarity or universal long-time rheological accuracy.

Fresh optimized CPU builds in a unique /tmp directory pass the existing
`kg_correlator6_counts_test.cpp` exact six-channel/lag/count/block-average probe and
`kg_assoc_correlator_checkpoint_test.cpp` serialization/continuation probe.
The unchanged P4 analyzer's self-test passes fourteen synthetic/parser regimes:
replica-sensitive tail inference, support sensitivity, outliers, lag-zero treatment,
nonuniform trapezoidal integration and refusal of viscosity for unresolved tails.
Six new review-local deterministic tests cover the tensor-projection identity,
normal-channel dependence, isotropic normalization, every actual pilot channel/count,
corrupt G/sampling rejection and refusal to interpret counts as replica agreement.
This is CPU/static confirmation and existing GPU evidence, not a fresh GPU claim.
No protected KG code was edited.

## P4 chronology, reproduced results and qualifications

The 1M two-seed pilot resolved fast bonded stress, G(0)~66, but not a terminal tail.
The original 0.05 G(0) uncertainty floor was rejected because it hides O(.01–.001)
slow stress. An early 32M two-seed result appeared to show a weak plateau near
39321.6–57671.68; raw support there was ~50, but replica disagreement/noise prevented
a reliable terminal conclusion under the then-current classifier. The length-scaled
320-count eligibility rule was superseded by sensitivity across 8,16,32,64,128 raw
counts. Existing documentation correctly records those historical decisions.

Five 32M replicas (12001–12005; two from run.MBA5fA and three from run.RqADk7)
then showed that the apparent plateau was not replica-robust. The updated estimator
uses five-bin equal-bin means within each replica, then replica SEM and 95%
Student-t intervals (df=4, t*=2.776445). Three overlapping windows provide a
persistence guard, not independent tests. Four support choices (8–64) give sustained
compatibility with zero at the available noise floor by ~20972, after sustained
nonzero support near 11796–17039; threshold 128 is support-limited, not contradictory.
A later positive excursion's CI includes zero. Current reanalysis reproduces
`robust_resolved_decay_to_zero`, G(0)=**66.18243447** and the documented viscosity.
The label means noise-floor compatibility, not proof of mathematically zero stress.

| Actual cutoff | Mean eta | Replica 95% CI |
|---:|---:|---:|
| 19660.80 | 167.96 | 103.76–232.16 |
| 23592.96 | 177.03 | 101.81–252.24 |
| 28835.84 | 184.28 | 94.93–273.64 |
| 39321.60 | 188.57 | 69.48–307.67 |
| 47185.92 | 195.91 | 47.77–344.04 |

Integration is trapezoidal on the actual nonuniform grid, including G(0)'s first
0→.01 trapezoid, with no tail fit or infinite-time extrapolation. The median target
30000 snaps to 28835.84, yielding **184.28363 ±89.35759**, and separate cutoff
sensitivity **16.32183**. This is an approximate historical C1 comparison, not a
precision result or a universal production-duration guarantee.

**Versioned-report discrepancy:** original saved run summaries remain `unresolved_tail`,
including the five-file aggregate saved before the final analyzer revision. They
are preserved, not overwritten. The new `replay/` results use today's hash-bound
analyzer. Applied to only the two original 32M files, that updated Student-t method
also labels noise-floor decay and declares cutoff adequacy, despite an eta interval
**−881.07 to1319.70**. The earlier two-replica recommendation must not be rewritten
as an established precise result. A wide CI can make both zero compatibility and
“cutoff change less than CI half-width” easy to satisfy. Those automatic labels
alone are insufficient production acceptance criteria; retain their statistical
caveat and inspect scientific precision. No classifier is changed here.

**Historical physics qualification:** the pilot source commits (8ee9ad6,6aa6e37)
predate the periodic reaction-cell correction documented in PERIODIC_CANDIDATES.md.
The old bank states/trajectories are not the current corrected-C1 qualified starts.
Their measured G and viscosity remain historical finite-trajectory evidence; they
cannot establish unbiased equilibrium rheology of today's corrected chemistry.
The tensor, buffering, sampling, support and uncertainty lessons remain valuable.
No historical scientific file or result is deleted/reinterpreted as a new run.

## Genuine remaining issues and launch implications

- Current full-run G contains no origin-time tags or stress microseries. Existing
  event/topology histories do not recover early/late or motif-conditioned stress
  products. Synchronized raw six-component stress or additional instances of the
  **same** correlator for predefined windows are needed; no new estimator is needed.
- Current strict schema/CLI fixes100M and offers no interruption checkpoint/resume.
  A proposed shorter staged design needs separately tested administrative support,
  not an undocumented CLI override. Full MD continuity cannot be supplied by the
  standalone correlator utility.
- Isotropic/zero-mean stress assumptions, structural stationarity and terminal-tail
  precision must be checked for each condition, especially user-excepted Ea10.
  The existing classifier is a diagnostic, not automatic proof of stationarity or
  a useful-precision viscosity. Raw counts do not solve either limitation.
- Coarse-grid smoothing/quadrature and finite observation cutoff need sensitivity
  checks; existing analytic integration tests validate arithmetic, not arbitrary
  coarse-time bias. No stress-resolved microtrajectory can be inferred from sparse
  full-bead positions without velocities at every stress time.
- No new optimized production build or GPU validation is performed in this CPU-only
  milestone. Before launch, authenticate a fresh out-of-tree build and user-run
  bounded tests on the current corrected source/accepted parent formats. Existing
  preparation readback/oracle evidence is not automatically a GPU test of this
  distinct production executable.

SOURCE_INPUTS.sha256 and replay/INPUTS.sha256 authenticate inspected implementation,
project decisions and original pilot inputs. REPRODUCE.md gives bounded CPU commands.
The separate production design addresses these limits without replacing G(t).
