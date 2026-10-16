# Ee12: joint assessment through absolute 20M

**Recommend qualified acceptance of exactly r001/r002/r003 at absolute
20,000,000 MD steps solely as `production_initial_state` for
`F04_N010_RP080_EE12_EA04`. No further equilibration is recommended for this
restricted use on the present joint evidence.** This is a scientific
recommendation, not formal registration, registry selection or production permission.
The earlier exact-16M hold remains immutable historical evidence.

The specific held r002 trajectory now exhibits genuine population returns and a
late plateau instead of prolonged uninterrupted coarse loop loss. r001 and r003
follow different phases of redistribution; r003 has an observed late return and
singleton turnover rather than satellite fragmentation. The recommendation rests
on these paths together with sustained exchange and bounded bulk connectivity,
not on stable occupancy, cancellation between replicas, or zero-containing
intervals. It does not assert that every slow observable has equilibrated.

Important qualifications remain: a common L1 offset from 12–16M, residual
r002 multiplicity evolution, r001's late degree/L1 changes, r003's substantial
intra/inter/degree excursion and new isolated states, replica offsets, coherent
late terminal contraction, poorly resolved slow modes and possible initialization
bias. **Complete stationarity, structural decorrelation and absence of
initialization bias have not been demonstrated.**

Starting clean local/remote `KremerGrest` HEAD:
`c1e0b5d472dbf0c5e09274f8079cd92a92d7d3dd`. Review date: 2026-10-16,
Europe/Madrid. The final SHA is the containing review commit, reported after push.

## Authentication and actual continuation boundary

Original 0–16M attempt: `equilibrate_9be4b5a8840d48b79b2bc5f9d714f9c0`.
Continuation: `equilibrate_553522b9ed9b4253a6b910d817ad65f8`, plan SHA256
`5d0045e99d2c7631a4c8d96416229c07d9e12d241a9753e8ba721f8d4071b0b9`.
Fresh CPU numerical, accepted-event, multigraph and conformation replay passes
for **all six segments**. Original histories each have 16,001 frames and
18,824/18,410/18,850 accepted events; continuations have 4,001 frames and
4,069/4,182/4,100 events. Final 20M bond counts are 1,971/1,962/1,976.
Fresh validation results equal all six completion receipts exactly.

The exact 16M restart/sidecar pairs match the frozen dossier and new parent
bindings. Chemical partners, seeds 420801/420802/420803, absolute steps and
cumulative counters continue. New requested MD seeds are **520130/520131/520132**;
effective seeds **3381585552/3373217424/3398338192**. A new GJ integrator loads
positions/velocities with `initVelocities=false` and `internal_start_step=0`.
This is **not bitwise MD continuation**. [BOUNDARY.json](evidence/BOUNDARY.json)
records exact partners, counters and old/new MD streams.

E1 active lineage and available snapshot/command/diagnostic bytes, plan/approval
bindings, smoke witnesses, execution commands, completion/output hashes,
source/build/log evidence and current extension executable bytes authenticate.
All **289 common native/build-recipe source hashes** match between builds.
The original six executables were replaced before this review by the new build;
their recorded digests, source/build logs, outputs and original integrity-bound
review authenticate, but their old executable bytes are not independently
reauthenticated now. Historical E1 executable bytes remain similarly limited.
No executable or GPU calculation ran here.

[ENDPOINTS.md](ENDPOINTS.md) binds the exact three 20M pairs, 16M parents, seeds,
output and receipt hashes. [Provenance](evidence/provenance.json) records both
plans, authentication scopes and fresh validations. All eleven acceptance records
and 1,258 preexisting relevant file bindings remain unchanged.

## Complete context and uncertainty policy

Each frame export has **20,001 unique absolute steps**, including initially
unbound step zero. Both raw 16M boundary observations authenticate; one is retained
for display. Nonoverlapping **40 × 500k, 20 × 1M, 10 × 2M and 5 × 4M** windows
cover 0–20M, with shifted and final-quarter contrasts. No preparation transient
is discarded. Window means use `(start,end]`; figure shading of 0–1M marks early
context rather than declaring subsequent stationarity.

Every IAT, SEM, blocking estimate and correlation interval belongs to one actual
MD segment. A selector rejects intervals crossing 16M. No bond lifetime is
stitched through reseeding. Exactly matching original interval estimates are
reused from the hash-bound 16M review, with source path/SHA labels, after fresh
raw-data authentication; all continuation intervals are computed directly.

[Replica tables](evidence/REPLICA_WINDOWS.md), [ensemble tables](evidence/WINDOWS.md),
[late diagnostics](evidence/LATE_DIAGNOSTICS.md), full frame CSVs and
[all estimates](evidence/summary.json) retain the complete evolution.
Paired Student-t intervals use the **three original histories** (df=2), not six
segments or extra windows. ± below denotes an exploratory, unadjusted 95%
half-width. Overlapping contrasts are correlated; zero inclusion does not prove
stationarity, equivalence or absence of bias. Slopes are descriptive OLS values,
not frame-level significance tests.

| Ensemble mean | 12–16M | 16–18M | 18–20M | 16–20M |
|---|---:|---:|---:|---:|
| Bonds | 1970.9839 | 1971.4898 | 1971.1275 | 1971.3087 |
| Intra / inter | 91.8088 / 1879.1752 | 92.2023 / 1879.2875 | 90.0367 / 1881.0908 | 91.1195 / 1880.1892 |
| L1 / L2 | 53.7760 / 45.0652 | 49.9222 / 43.1570 | 50.1538 / 43.2873 | 50.0380 / 43.2222 |
| Distinct degree | 3.651718 | 3.659312 | 3.662536 | 3.660924 |
| Giant fraction | 0.9989968 | 0.9989997 | 0.9986850 | 0.9988423 |
| Rg² | 7.033888 | 7.026617 | 7.035308 | 7.030962 |
| Center–terminal R² | 15.908809 | 15.891569 | 15.920285 | 15.905927 |

The primary intra change is −0.6893 ± 12.0098, comprising +4.4753/−5.1060/−1.4370.
Its broad interval and cancellation are not the reason for the recommendation.

## Resolution of the r002 hold; separate r001 trajectory

| Replica, intra mean | 8–12M | 12–16M | 16–18M | 18–20M |
|---|---:|---:|---:|---:|
| r001 | 87.4810 | 86.2483 | 90.1580 | 91.2890 |
| r002 | 95.4143 | 90.4988 | 86.0340 | 84.7515 |
| r003 | 97.9543 | 98.6793 | 100.4150 | 94.0695 |

r002's lower new 4M mean alone would not resolve the hold. The path does:
500k intra means are **83.578, 84.842, 87.756, 87.960, 85.430, 84.124, 84.612,
84.840**. There is a substantial return from the initial low to approximately
88, followed by another decrease and smaller return. Last-1M means are
84.777 → **84.726**; final-500k change is **+0.228**. Final-quarter means
85.076 → 84.604 still decline **−0.472**, so a perfectly flat endpoint is not
claimed. The new observed pattern is consistent with an oscillatory plateau around a lower level,
not the preceding many-window one-direction trajectory.

The intra slope changes from −2.305 bonds/M at 12–16M to **−0.133** at 16–20M,
−0.336 at 18–20M and **+0.602** at 19–20M. The smaller slope is supporting
context, not a stationarity test. Shifted 16–19M → 17–20M changes intra **+0.172**;
16.5–18.5M → 17.5–19.5M gives **−0.9655**. Both retain the intervening return.

Distinct degree also returns: its final-1M slope is **−0.011632/M**, with
final-500k change **−0.005876**, after earlier gains. At 18–20M, L1 is
39.130 versus 39.341 at 16–18M; L2 falls from its earlier high, then rises.
Residual multiplicity changes persist: final-quarter L1 falls −2.080. But its
quarter means revisit a low already seen at 17.5–17.75M (37.296 versus final
37.112), rather than continuing an unbroken decay at all scales.

This is adequate evidence to remove the specific hold for **qualified
initialization**, while not proving equilibrium or excluding a slowly shifting
population baseline. Only about 5.5 effective intra samples are estimated in the
new 4M interval; that limitation stays with the recommendation.

r001 is assessed separately. Primary changes are intra **+4.4753**, inter
**−3.4728**, degree **−0.002553** and L1 **−3.150**. Within the continuation,
intra 500k means rise toward 92.840 then fall to 91.342 and **89.664**.
The last two 2M windows give intra +1.131 and degree −0.010014, coupled to L1
+2.9885. Last-500k/final-quarter intra changes are −1.678/−0.752; the final-1M
slope is −3.138/M. L1 returns from an early low near 50 to about 56 before a
small fall. These recurrent paths and opposing late directions do not resemble
r002's previously persistent loop loss. They do not certify full motif sampling.

## r003: redistribution and the actual peripheral change

r003 reaches intra 102.148 at 16.5–17M, falls through 97.930, 95.764 and 94.370
to **91.668** at 19–19.5M, then returns to **94.476**. The new 2M contrast is
intra **−6.3455**, inter **+4.8115**, degree **+0.014194**, second degree moment
+0.096996 and L1 **−2.0825**. Shifted 16.5–18.5M → 17.5–19.5M still gives
intra −4.344, degree +0.008527: this is real observed redistribution.

The new 4M intra slope is −2.764/M, but the last-1M slope reverses to **+4.994/M**;
inter and degree reverse to −3.720 and −0.006003/M. Final-500k intra rises +2.808,
then the final-quarter contrast falls −1.104. No smaller slope or single
reversal proves stationarity. However, unlike the prolonged r002 preparation
path, r003 already reversed upward at 12–16M and has now returned downward and
partly back upward. Its 4M intra levels since 8M are **97.954, 98.679, 97.242**,
with larger internal excursions. This favors a returning slow fluctuation for
restricted initialization use, while leaving a residual-relaxation interpretation
possible. The new excursion and low effective sample count remain qualifications.

The giant-component reduction is fully attributable to **singletons at sampled
steps**, not larger satellites: no satellite is observed in any continuation
frame. r003 giant means are 0.999 at 16–18M and 0.998058 at 18–20M. Exact
accepted-event isolation residence identifies:

| Star | Isolation begins | Isolation ends |
|---|---:|---:|
| 531 | 7,354,500 | 19,499,100: reconnects |
| 684 | 18,399,600 | right-censored at 20M |
| 868 | 19,216,600 | right-censored at 20M |

The temporary overlap creates three isolated stars; after star 531 reconnects,
two remain and the giant has **998 stars at the exact endpoint**. This is a
persistent singleton-population change at the present endpoint, with observed
exit/entry turnover, not continuing fragmentation into a nontrivial satellite.
It is not dismissed by the ensemble interval. Rare-state equilibrium is poorly
resolved, but reconnecting every isolated star is not an acceptance requirement.

r001 star 771 remains isolated from step zero through 20M. r002 star 491 remains
isolated from 11,175,200, with an additional brief star-885 isolation at
19,734,100–19,740,600. [PERIPHERY.md](evidence/PERIPHERY.md) and exact
[isolation records](evidence/ISOLATION.json) distinguish these identities from
population counts. Cross-boundary connectivity residence is explicitly labeled:
it is observed chemical continuity, not a stitched bond lifetime or stationary
lifetime estimate. [Satellite records](evidence/SATELLITES.json) use 1000-step
samples and make no claim about unsampled brief satellite visits.

## Complete multiplicity, loops, degree and correlations

Every frame satisfies `inter = Σ m·edges_m`,
`L1 = Σ choose(m,2)·edges_m`, and
`intra = stars_intra_loops_1 + 2·stars_intra_loops_2`.
Full allowed multiplicities 1–4, loop counts 0–2 and degree distributions 0–4
are retained in [distribution tables](evidence/NETWORK_DISTRIBUTIONS.md), frame
CSVs and summary estimates. For all 499,500 unordered star pairs, the zero-bond
bin is exactly `499500 − Σ edges_m`; it is derived, not independent evidence.

| Replica, 16–20M | m=0 | edges m=1 | m=2 | m=3 | m=4 | L1 | L2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| r001 | 497672.8640 | 1774.0688 | 53.0260 | 0.04125 | 0 | 53.1498 | 39.9873 |
| r002 | 497653.5748 | 1807.1898 | 39.2355 | 0 | 0 | 39.2355 | 48.8075 |
| r003 | 497682.1750 | 1761.8793 | 55.0543 | 0.89150 | 0 | 57.7288 | 40.8718 |

**All three L1 means fall** relative to 12–16M: −3.150/−3.171/−4.893,
mean **−3.738 ± 2.485**. This coherent offset is retained, not declared absent.
r001's loss is mostly fewer triples (0.995 → 0.04125); r002 loses double edges;
r003 loses 6.41325 doubles while gaining 0.50675 triples, whose L1 contribution
partly offsets the loss. Thus the full distributions add information beyond L1.
The absence of sampled quadruples and late r002 triples establishes neither their
exclusion nor adequate rare-bin sampling.

The within-extension L1 changes are oppositely phased: +2.9885/−0.2110/−2.0825
across its two 2M windows. All final-500k L1 changes are negative, mean
−0.610 ± 0.271, but final-quarter signs are +/−/+.
The common older-to-newer offset could include residual motif relaxation;
no sustained common latest direction is established. L2 also returns within
replica-dependent ranges rather than showing a common monotone late path.

Late 0/1/2-loop star populations are 910.277/88.724/1.000,
915.607/83.393/1.000 and 904.181/94.397/1.423. Double loops consume all four
stickers and force isolation. Degree-0/1/2/3/4 fractions are:

| Replica | 0 | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|---:|
| r001 | 0.0010005 | 0.0048405 | 0.0893225 | 0.1485595 | 0.7562770 |
| r002 | 0.0010015 | 0.0040563 | 0.0827735 | 0.1254278 | 0.7867410 |
| r003 | 0.0014710 | 0.0069730 | 0.0941300 | 0.1492870 | 0.7481390 |

These are coupled observables: `bonds = intra + inter` and
`1000·mean_degree/2 = inter − L1 + edges_m3 + 3·edges_m4`.
They cannot be counted as independent evidence. At 16–20M, correlations of eight
500k means for r003 are intra/inter −0.850, intra/degree −0.875 and
L1/degree −0.843. For r001 L1/degree is −0.821; for r002 it is only +0.049.
[Raw and coarse correlations](evidence/CORRELATIONS.json) are descriptive,
segment-local and have no frame/block p-values. L2 carries motif information
but still does not supply another independent history.

## Conformations, reaction balance and slow-mode resolution

Rg² primary changes are **+0.006192/+0.012883/−0.027851**; center–terminal R²
changes **+0.026873/+0.043214/−0.078735**. r001 expands then levels/returns;
r002 is broadly stable in the extension; r003 remains more compact than in
12–16M. The last two 2M windows have Rg² changes +0.027897/+0.001926/−0.003751.

There is a coherent late terminal contraction: 18–19M → 19–20M gives mean
**−0.023826 ± 0.011558**, and the final-quarter contrast gives
**−0.056074 ± 0.042343**, with all three signs negative. These exploratory
intervals exclude zero and must not be erased by broad primary uncertainty.
Over the full continuation, terminal slopes are positive/approximately flat/
negative across r001/r002/r003; the common final pulse does not establish an
uninterrupted shared shrinkage. Residual shape offsets and possible initialization
bias remain qualifications. [Full shape paths](evidence/shape.png) retain early
preparation; [late paths](evidence/late.png) show the 16M reseeding boundary.

Accepted creation/break rates at 16–20M average **0.051433/0.051492 per physical
time**; distinct-neighbor gains/losses **0.046700/0.046608**. Primary changes are
−0.001142 ± 0.005227, −0.001117 ± 0.005116, −0.000883 ± 0.004788 and
−0.000942 ± 0.005466. At 18–20M creation/break rates are 0.050950/0.050933.
Exchange persists without a large common kinetic change. Balanced chemistry
and bulk bound fraction near 0.98565 do not prove equilibration of its partition.
Exact event-integrated rupture rates per active-bond time are
2.58–2.66×10⁻⁵; qualified Ee10 context remains about six times faster, with genuine
Ee-dependent populations allowed. [Reference evidence](evidence/EE10_COMPARISON.json)
reuses the authenticated frozen 12M review, not new reference simulation/replay.

The inherited IAT convention is
`tau = frame_dt·(1/2 + Σ rho_lag)` to first nonpositive lag,
`N_eff = N/(2·tau/frame_dt)`. At 16–20M:

| Observable | IAT, physical time | Estimated effective samples |
|---|---:|---:|
| Intra | 2053–6560 | 3.05–9.74 |
| L1 | 1300–4503 | 4.44–15.39 |
| L2 | 3459–4188 | 4.78–5.78 |
| Degree | 1555–4734 | 4.23–12.86 |
| Rg² | 103–673 | 29.7–194.7 |
| Terminal R² | 85–762 | 26.3–236.4 |

r003 intra 5/10/20-block SEMs are **1.689/1.181/0.838**, versus IAT SEM 2.136;
r001 L1 gives 0.975/0.711/0.513 versus 1.112; r002 intra gives
0.721/0.525/0.377 versus 0.735. Slow errors lack a robust block-size plateau.
Finite-window IATs can mistake drift for correlation and miss slower modes.
Constant-bin numerical placeholders and zero SEMs are flagged, not mixing evidence.
These estimates never increase the independent-unit count beyond three histories.

## Restricted scientific recommendation and limits

The hold's prolonged r002 population/coordination path is resolved sufficiently
for initialization by actual returns and a late plateau. r001 and r003 provide
independent, differently phased paths with recurrent changes; r003's singleton
turnover is explicitly identified, with no sampled satellite fragmentation.
Bulk connectivity remains large and chemistry/neighbor exchange persists.
Together these support **qualified initialization of the three exact 20M states**.
They do not certify equilibrium of all network or conformation observables.

The common L1 offset, r003's newer redistribution/isolates and compaction,
r001 degree/L1 evolution, residual r002 multiplicity changes, coherent final
terminal contraction, rare populations, replica offsets and poor slow-mode
resolution must accompany any future formal registration. Initialization bias
cannot be excluded. Complete stationarity and structural decorrelation are not
demonstrated and are not being required as automatic gates for this restricted use.
Equilibrium inference from subsequent data would need its own bias assessment.
No additional calculation is recommended here solely to force all slow observables
to decorrelate; this recommendation creates no production preparation or authorization.

The inspected LAMMPS associating sources remain byte-bound to branch
`feature/associating-stickers`, commit `1c6faf70e94aef2389c208e8c80c60c084a96907`:
both reaction directions are gated by r_assoc; active shifted-FENE bonds remain
mechanical below R0; WCA is not duplicated; and
`q = -expm1(-nu0 * exp(-Ea/T) * Nevery * dt)`. Ee changes energetics; Ea sets the
attempt scale. At configured T=1, observed kinetic temperatures remain near
0.979 under the unchanged GJ setup, as in the prior review. Numerical validity
does not establish exact coupled-integrator equilibrium invariance.

[VALIDATION.md](VALIDATION.md) records CPU checks and reproduction. Only this new
review dossier changes. No GPU calculation, equilibration, acceptance registration,
registry action or production preparation/launch occurred. Prior reviews, simulation
outputs, frozen physics and eleven acceptance records remain unchanged.
