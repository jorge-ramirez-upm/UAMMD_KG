# Ee10: joint scientific assessment through absolute 12M

**Recommend qualified acceptance of exactly r001/r002/r003 at absolute 12,000,000
MD steps solely as `production_initial_state` for `F04_N010_RP080_EE10_EA04`.**
No additional equilibration is recommended on the combined evidence for this
restricted use. The extension reverses the specific r001/r002 population trends
that motivated the 8M hold, resolves r002's L1 rise as a large returning excursion,
and shows recurrent, replica-dependent redistribution rather than sustained common
bulk relaxation. This is a scientific judgment from the paths, not proof of
equilibrium or an inference from zero-containing confidence intervals.

Important qualifications remain: poorly sampled slow topology, r002's substantial
L1 excursion and elevated late mean, r003's newer intra/inter/degree redistribution,
replica population offsets, and a common conformational offset from 6–8M.
Complete stationarity, structural decorrelation and absence of initialization
bias have not been demonstrated. The original 8M hold remains preserved as
historical evidence; this recommendation concerns only the new exact 12M states.
No formal acceptance, registry selection/activation or production permission is
created.

Starting local/remote `KremerGrest` HEAD, initially clean:
`4ada00d18cff6ac5e83872faf469409ee892f28f`. Review date: 2026-10-15,
Europe/Madrid. Final SHA is the containing assessment commit, reported after push.
Only this new review directory changes.

## Authentication and actual 8M boundary

The original attempt `equilibrate_fb8954dc860740d6b923759b2b21a703` covers 0–8M;
the extension `equilibrate_18d492ee0f4b4a7d98ca32e39ce8f95a` covers 8–12M.
Extension plan SHA256:
`9ceb3ce52582e1e781ee36072b4018254dca0f663f58a73edb3111093322f28a`.
Fresh CPU numerical, accepted-event, network and conformation validation passed
for all six segments. Original histories have 8,001 samples and
54118/53832/53545 accepted events; extensions have 4,001 samples and
25674/25653/25903 events. Final bond counts are 1926/1915/1926.

All three 8M restart/sidecar pairs match the prior immutable endpoint dossier and
the new plan's parent bindings. Chemical seeds 420701/420702/420703, partners,
absolute steps and cumulative creation/break counters continue. The requested
MD seeds change from 520112/520113/520114 to **520118/520119/520120**, with effective
seeds **3011452588/3003084460/2894249636**. Source and logs establish a new GJ
integrator with `internal_start_step=0` and `initVelocities=false`: positions and
velocities are restored, but the MD random stream is reseeded. This is not bitwise
MD continuation. **No IAT, SEM or bond lifetime is stitched through 8M.**

Approvals, smoke witnesses, execution commands/seeds, source/build manifests,
build logs, completion receipts, all outputs and current extension executable
bytes authenticate. All **289 common native/build-recipe source hashes** match
between builds. The rebuilt binaries replaced the originals; original executable
digests, source/build logs and the approved review remain authenticated, but old
binary bytes are not independently reauthenticated now. Historical E1 executable
bytes remain a similar limitation. E1 parent identities and available bytes are
authenticated. [ENDPOINTS.md](ENDPOINTS.md) binds the exact parent and final pairs;
[provenance](evidence/provenance.json) records the full authentication scopes.

## Full context and uncertainty policy

Frame exports contain **12,001 unique steps per replica**, including initially
unbound step zero. One 8M display row is retained; both raw boundary states remain
authenticated. Nonoverlapping 500k, 1M and 2M windows cover all 0–12M, with shifted
and final-quarter comparisons. Every estimator interval belongs to one actual MD
segment. Original interval estimates are reused only when their exact bounds
match the authenticated 8M dossier; every extension interval is computed directly.
No IAT or blocking error is averaged to manufacture a longer interval.

[Full tables](evidence/WINDOWS.md), [all estimates](evidence/summary.json), frame
CSVs and figures retain early preparation. It is not silently discarded or
asserted stationary. Paired Student-t intervals use only the **three original
histories** (df=2); displayed ± values are 95% half-widths. Frames, blocks and
windows are not independent replicas. Overlapping contrasts and multiple
observables are exploratory, unadjusted and correlated. Zero inclusion does not
prove stationarity, equivalence or the absence of bias.

| Ensemble mean | 6–8M | 8–10M | 10–12M |
|---|---:|---:|---:|
| Total bonds | 1920.772 | 1921.646 | 1921.406 |
| Intra / inter bonds | 103.352 / 1817.420 | 94.834 / 1826.812 | 95.796 / 1825.609 |
| L1 parallel-bond pairs | 40.236 | 45.994 | 49.447 |
| L2 distinct-star triangles | 36.616 | 41.004 | 37.622 |
| Giant fraction | 0.998206 | 0.998829 | 0.998818 |
| Mean distinct degree | 3.555341 | 3.562423 | 3.553754 |
| Rg² | 7.047982 | 7.035012 | 7.023146 |
| Center–terminal R² | 15.941257 | 15.915243 | 15.877746 |

## Resolution of the original population concerns

The per-replica intra means are:

| Replica | 6–8M | 8–10M | 10–12M |
|---|---:|---:|---:|
| r001 | 100.8925 | 88.0050 | 83.3690 |
| r002 | 107.1090 | 110.5385 | 105.1730 |
| r003 | 102.0540 | 85.9575 | 98.8465 |

r001's continued increase at 8M **does not persist**: 6–8M → 10–12M intra changes
−17.5235 and inter +20.230, with distinct degree recovering +0.039708 and second
moment +0.227523. A new smaller rise within 10–12M remains: 10–11M → 11–12M
intra +5.750. But the final 500k reverses −5.600, followed by a final-quarter
change −0.944. The path includes a clear low near 10–10.5M and subsequent return;
it is not uninterrupted loop growth or coordination erosion.

r002 initially reaches a higher intra level, then reverses: the last two 2M
windows change intra **−5.3655**, inter +7.626 and degree +0.004378. Last-1M intra
change is −4.118; final-500k change −2.044. Its final quarter rises +1.712, so no
single late sign is universal. The earlier plateau hypothesis was incomplete,
but continuing common loop growth is not supported through 12M.

r003 follows a different phase: intra 102.054 → 85.9575 → 98.8465. Its newer
8–10M → 10–12M increase **+12.889**, inter loss −15.074 and degree decrease
−0.032497 are real observed evolution. Shifted 8.5–10.5M → 9.5–11.5M gives intra
+9.460 and inter −10.831. These are retained qualifications, not erased by the
ensemble mean (+0.9625 ± 25.6759 intra). However, 500k intra means settle from
90.430 to 100.262, 102.474 and 102.220; final-quarter change is −1.336. Its final
quarter inter and degree still decline, partly alongside a total-bond fluctuation.
The evidence favors return from its low-intra excursion with residual local
redistribution, rather than the original shared trend continuing in all histories.

All final-500k intra changes are negative (−5.600/−2.044/−0.254), while final-quarter
changes have mixed signs. Late mean populations remain replica-dependent, especially
r001's lower intra level. The recommendation does not assert identical equilibrium
means per replica or exclude history-specific initialization bias.

## r002 L1 excursion, complete multiplicity and triangles

L1 counts parallel bond pairs; L2 counts distinct-star triangles. Permanent-star
membership is fixed. All frames satisfy inter = sum(m × edges_m) and
L1 = sum(choose(m,2) × edges_m), for all allowed multiplicities m=1…4.

| Inter-star bonds per distinct star pair | 6–8M mean pair count | 8–10M | 10–12M |
|---|---:|---:|---:|
| 1 | 1738.4072 | 1736.0040 | 1728.8592 |
| 2 | 38.7772 | 44.8142 | 47.3033 |
| 3 | 0.4862 | 0.3932 | 0.7145 |
| 4 | 0 | 0 | 0 |

Zero quadruple observations do not establish exclusion or adequate sampling.
Late stars carrying 0/1/2 intra bonds average 905.2672/93.6695/1.0633. Both
multiplicity and intra-loop distributions are retained by replica and window.

r002 L1 rises through 44.054, 50.276, 51.482, 59.008, 61.348 and **64.180** in
successive 500k windows from 8M, then falls to **58.424 and 46.616**. Final-quarter
means fall 49.136 → **44.096**. The 10–11M → 11–12M change is −10.244 and the
final-500k change −11.808. This is a substantial observed reversal, not a stalled
monotone increase. Its 10–12M mean remains elevated at 57.642 and poorly sampled;
neither the return nor the lower endpoint scalar proves full motif equilibrium.

The peak is not just a double-edge fluctuation: at 10.5–11M, r002 has 57.370
double and 2.270 triple edges, contributing 57.370 + 3×2.270 = 64.180 to L1.
At 11.5–12M these fall to 45.302 and 0.438. Its primary 8–10M → 10–12M L1 rise
+6.437 consists of doubles +3.437 and triples +1.000. r001/r003 also rise across
those 2M windows (+2.502/+1.4205), but the last-1M changes are
+5.228/−10.244/−1.603 and final-500k changes +5.542/−11.808/+3.864. There is no
common sustained late multiplicity direction. r003's pre-8M L1 loss has reversed:
33.6175 → 45.943 → 47.3635 across the three coarse windows.

L2 changes 8–10M → 10–12M are **+8.371/−8.9805/−9.5375**, mean −3.382 ± 25.297.
r001's earlier triangle loss reverses; r002's triangle minimum near its L1 peak
returns from 25.420 to 32.792 and 37.764 in the last three 500k windows. All final
500k L2 changes are mixed. These large oppositely phased paths support bounded
excursions, with unresolved sampling of slow collective topology.

## Connectivity, loop isolation and correlations

Late giant fraction is **0.998818**, isolated stars 1.1667 and satellite stars
0.0157 among 1000 permanent stars; satellite components average 0.00783.
The primary giant changes −0.000233/+0.000803/−0.000605 are mixed and the ensemble
change is −0.0000115 ± 0.001813. Relative to 6–8M, all three giant fractions rise;
satellite populations fall, especially r003's earlier satellite excursion.
r001's dip near 10.5–11M reverses to a final-500k giant mean 0.999504.
All final-quarter giant means increase by approximately 0.00015. There is no
observed continuing common peripheral deterioration, though rare-event sampling
is limited and a zero-containing interval is not the reason for that conclusion.

Most late isolation is accounted for by stars carrying two intra bonds: means
1.478/0.870/0.842, versus isolated-star means 1.5405/1.0215/0.938. Such a star has
no sticker left for inter-star bonding. These are structurally coupled counts,
not independent evidence of a separate connectivity process.

Late distinct-degree fractions are:

| Replica | degree 0 | degree 1 | degree 2 | degree 3 | degree 4 |
|---|---:|---:|---:|---:|---:|
| r001 | 0.001541 | 0.008121 | 0.089586 | 0.199388 | 0.701366 |
| r002 | 0.001022 | 0.010690 | 0.114905 | 0.212145 | 0.661239 |
| r003 | 0.000938 | 0.009840 | 0.104472 | 0.209333 | 0.675419 |

Primary mean-degree changes are +0.002113/+0.004378/−0.032497; second-moment
changes +0.009706/+0.016830/−0.196591. Final-quarter degree changes are
+0.009168/+0.005056/−0.011632. r003's residual coordination path is explicit;
there is no shared late erosion across all three original histories.

[CORRELATIONS.json](evidence/CORRELATIONS.json) reports segment-local Pearson
coefficients for raw diagnostics and 250k/500k means, with no frame/block p-values.
At 10–12M, r002 L1 correlates with degree at −0.834 raw and −0.947 for four 500k
means, and with L2 at −0.872/−0.930. The L1/degree link is partly algebraic:
distinct edge count = inter − L1 + edges_m3 + 3×edges_m4. Correlations therefore
cannot be counted as independent confirmation or causal evidence. Over the entire
8–12M segment, intra/inter correlations of 500k means are −0.956/−0.968/−0.994;
intra/Rg² correlations are only +0.136/−0.102/+0.051. Raw and blocked values can
differ strongly, and four or eight block means do not supply independent replicas.

## Conformations, exchange and Ee8 context

The shared 6–8M → 10–12M contraction is retained: Rg² changes
−0.026849/−0.022071/−0.025588, mean **−0.024836 ± 0.006152**; terminal R² changes
−0.062018/−0.054412/−0.074103, mean **−0.063511 ± 0.024669**. Both intervals
exclude zero in the exploratory comparison. Shapes also decrease in all three
8–10M → 10–12M comparisons. These offsets cannot be declared absent.

However, last-1M shape changes are −/+/+ in both observables, and final-quarter
changes are Rg² +/+/− and terminal R² +/−/−. r002 expands out of its compact
L1-rich excursion. Full 0–12M paths show repeated contractions and expansions;
the shared offset from the elevated 6–8M period does not establish uninterrupted
current shrinkage. Residual shape offsets and possible initialization bias remain
qualifications. Rg² and terminal R² use permanent-bond minimum-image unwrapping,
with independent endpoint reconstruction; they are not COM transport estimates.

At 10–12M, accepted creation/break rates both average **0.321383 per physical
time**; distinct-neighbor gains/losses average **0.289967/0.290133**. Primary paired
changes are −0.000783 ± 0.017505, −0.000850 ± 0.016832,
−0.001233 ± 0.012156 and −0.000650 ± 0.015079. Turnover persists without a common
large kinetic change. Balanced total chemistry does not establish equilibration
of its intra/inter partition or collective topology.

The qualified corrected Ee8 reference at the same f=4, N=10, density 0.8 and Ea=4
has bound fraction 0.897003, mean degree 3.318562, giant fraction 0.997694 and
L1/L2 means 39.646/33.394. Ee10 late values are 0.960703, 3.553754, 0.998818 and
49.447/37.622. Genuine Ee dependence is allowed; these need not coincide.
Ee8 creation/break rates 1.81950/1.81848 and neighbor gains/losses 1.64923/1.64718
are roughly 5.7 times faster. Ee10 event-integrated rupture rates per active-bond
time are 0.0001646–0.0001689 versus 0.001012–0.001016 at Ee8. This is context for
slow sampling, not an equilibration-time scaling law or a stopping rule.
Reference record/payloads authenticate again; comparison values reuse only the
frozen corrected 6–8M review, not defective historical C1 windows or a new Ee8
simulation/replay. Histories are not paired across Ee.

## Limits and decision

At 10–12M, interval-local IAT/effective-sample ranges are: intra **2067–2467
physical time / 4.05–4.84 samples**; L1 **1451–2604 / 3.84–6.89**; L2
**738–2601 / 3.85–13.55**; giant fraction **773–1854 / 5.39–12.94**; Rg²
**239–553 / 18.1–41.9**. IATs are finite-window first-nonpositive-lag heuristics;
trends and slow states can make them misleading. r002 L1 5/10/20-block SEMs are
3.644/2.521/1.769 versus IAT SEM 4.002; r003 intra SEMs are 2.505/1.700/1.205
versus IAT SEM 2.490. Slow-mode errors do not show a robust block-size plateau.
Constant bins and sparse satellite events do not certify mixing.

The recommendation rests on the observed reversals of the specific held paths,
bounded large excursions, stable bulk occupancy/connectivity and persistent
exchange together. It does not require complete structural decorrelation and
does not use broad uncertainty as evidence of equilibrium. r002's elevated L1
average, r003's late redistribution, replica offsets, shared shape contraction,
rare-event sampling and executable-authentication limits must accompany any
future qualified registration of the exact 12M pairs. Equilibrium inference from
subsequent production would need to assess initialization bias separately.

The inspected, hash-bound LAMMPS reference remains
`feature/associating-stickers` at `1c6faf70e94aef2389c208e8c80c60c084a96907`:
both kinetic directions are gated by r_assoc, active shifted-FENE bonds remain
mechanical below R0, WCA is not duplicated, and
`q = -expm1(-nu0 * exp(-Ea/T) * Nevery * dt)`. Ee changes energetics; Ea sets the
attempt scale. Exact coupled-integrator equilibrium invariance remains unproven.
No physics or simulation data changed. [VALIDATION.md](VALIDATION.md) records
reproduction and CPU checks. No GPU, additional equilibration, acceptance
registration, registry action or production preparation/launch occurred.
