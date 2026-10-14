# RP040, Ee8: joint scientific assessment at absolute 6M

**Recommendation: a targeted additional 2M of E2 for each of the three original
histories, followed by a joint 0–8M scientific review. Hold qualified acceptance
of the 6M endpoints pending that check.** The endpoints pass numerical validation;
the unresolved coordinated L1/multiplicity evolution warrants stronger evidence
before recommending even qualified production initialization. This is a scientific
recommendation only, not preparation or authorization of an extension, formal
acceptance, registry selection or production authorization.

System: `F04_N010_RP040_EE08_EA04`; f=4, N=10, polymer density 0.4, total bead
density 0.85, unit masses, orthorhombic box, Ea=4, Ee=8, dt=0.01.
Starting remote HEAD was `979929480cb443aff23da332852fa2ed9c997e09`. The clean local
checkout began at `bb7d72acbcadfaef5a09333b27439de763597b93` and was fast-forwarded
to that remote HEAD before analysis. The intervening commit changed only ROADMAP.md.
The final commit is the commit containing this dossier, reported separately.

## Authenticated evidence and proposed endpoints

The attempt is `equilibrate_704163de5b044a3f8293eedd2e1c5304`, with plan SHA256
`5884973e9a8db39cf40fbb5e0e4298a65b41c517e76db1b60f0552cfbdb79b50`.
The supplied checkpoint is `review_6f4af68f173d4a81925e3670b4ce6fc7`.
The proposed endpoints are **r001/state, r002/state and r003/state at absolute
6,000,000**, never the earlier stopped attempt or smoke states. Exact restart,
sidecar and E1 hashes and all seeds are in [ENDPOINTS.md](ENDPOINTS.md).

The established read-only analyzer freshly authenticated the frozen campaign
system definition, E1 inventory/snapshots/commands/diagnostics, independent replica
identities, chemical seed map, MD/effective MD seeds, plan approval, parent lineage,
source hashes, embedded and external build manifest, build logs and current binary
bytes. Started receipts also matched commands, plan/approval and smoke digests.
All completion receipts and eight output hashes per history matched current bytes.
Fresh numerical/event/graph validation passed: 6001 frames and 60000 chemistry
sweeps per replica, accepted events 197626/198337/198306, final bonds 1692/1701/1710.
Reciprocal valence-one chemistry, permanent topology, particle identity, intra/inter
classification, neighbor exchange, geometry/FENE limits, restart/sidecar/mirror
consistency and final conformation reconstruction passed. The checkpoint report,
config, payload and analyzer bindings also authenticated. This validates recorded
numerical behavior, not scientific stationarity or exact thermostat invariance.

[provenance.json](evidence/provenance.json) retains the plan, build, complete source
maps, entries, validation results and every output binding. [AUTHENTICATION.json](AUTHENTICATION.json)
adds E1 commands, started receipts, environment/log hashes and checkpoint checks.
Historical E1 executable bytes were not independently reauthenticated. Current E2
binary bytes and build logs were authenticated. Rejected reaction opportunities,
per-sweep candidate sets (oracle coverage is zero), inter-diagnostic coordinates,
and per-star slow-shape/orientation histories were not reconstructed.

## Method and uncertainty policy

Only r001/r002/r003 are statistical replicates. All step-zero association transients
and every diagnostic frame are retained in exported paths and figures. 0–1M is
preparation context; it is not retroactively labeled equilibrium or silently
removed. Frame/event intervals are left-exclusive and right-inclusive. Consecutive
500k, 1M and 2M windows, shifted 1–2M comparisons and final 250k subdivisions are
calculated within each uninterrupted 0–6M history. No replica pooling, transport
stitching, averaging of IATs or combining of window SEMs is used.

Each interval receives fresh first-nonpositive-lag IAT, effective-sample estimate,
slope and 5/10/20-block uncertainty using the validated helpers. These assume local
stationarity and can underestimate slower unresolved tails. Blocks and overlapping
windows are correlated evidence, not new histories. Paired three-history Student-t
intervals use df=2, are exploratory and unadjusted for many comparisons; neither
including zero nor excluding zero alone determines acceptance. No equivalence
margin or universal percentage tolerance is being invented. The dossier executes
the unchanged IAT function bytecode with an exact per-call cache for its repeated
identical mean calculation; arithmetic is not reordered. CPU regressions check
bit-exact equality and restoration of the original helper. All 5040 shared 500k
scalar/vector estimates matched the authenticated checkpoint exactly. No repository
analysis helper or simulation source was changed.

## Conformation: small common offsets, heterogeneous late paths

| Ensemble mean | 0–1M (transient context) | 1–2M | 2–3M | 3–4M | 4–5M | 5–6M |
|---|---:|---:|---:|---:|---:|---:|
| Rg² | 7.641924 | 7.647270 | 7.648049 | 7.648394 | 7.652051 | 7.655430 |
| Center–terminal R² | 17.327928 | 17.344238 | 17.343637 | 17.350515 | 17.351737 | 17.366425 |
| L1 parallel-bond pairs | 52.366667 | 50.509000 | 56.810667 | 50.527000 | 51.573000 | 49.087333 |

From 1–2M to 5–6M, Rg² increases by +0.008160 (~0.107%) and center–terminal R²
by +0.022187 (~0.128%). Paired half-widths are 0.015280 and 0.096642; these do
not exclude residual bias. The 1–3M versus 4–6M Rg² comparison is +0.006081 ±
0.003524 (~0.080%), and a shifted overlapping comparison also excludes zero.
The ensemble increases therefore must not be dismissed merely because another
interval includes zero. Comparing transient 0–1M with 5–6M gives ~0.177% and
~0.222%, but includes association initialization and is not a stationarity test.

Replica changes 1–2M → 5–6M are Rg² +0.014866/+0.006834/+0.002781 and R²
+0.062249/+0.019749/−0.015438. r001 has the largest early-to-late change (~0.194%
Rg² and ~0.359% R²); residual initialization bias cannot be excluded. The last
1M comparison changes sign across replicas: Rg² +0.000847/−0.017873/+0.027162,
R² +0.015992/−0.054611/+0.082685. r002 swings up and down strongly even within
250k subdivisions. Fine-window reversals and mixed late slopes support bounded
correlated fluctuations as an explanation of part of the signal, but do not
identify all of the common long-window increment as equilibrium noise. Genuine
slow relaxation and equilibrium fluctuations cannot be cleanly separated with
these three paths. The shape offset alone would not establish a need for extension. It is retained
as unresolved initialization evidence alongside the coordinated multiplicity change;
we cannot authenticate it as equilibrium noise.

## Chemical redistribution and accepted exchange

The final 500k comparison shows a shared intra increase +7.658/+9.466/+4.866
(mean +7.330 ± 5.757), and inter decrease −3.952/−6.038/−5.612 (−5.201 ± 2.738).
Bonds overall increase +2.129 ± 6.196; this is redistribution plus population
fluctuation, not one-for-one inter-to-intra conversion. At 1M resolution the
redistribution loses its common sign: intra −15.710/+12.720/−1.548, inter
+14.988/−16.568/+5.723. At 2M resolution (2–4M → 4–6M), intra +2.428 ± 3.706
and inter −2.269 ± 12.095. A small coarser mean offset remains; a coordinated
persistent shift of the final-500k magnitude does not. The last 250k intra
increments are positive in all histories, whereas the inter increment reverses
in r003. No claim of complete late redistribution reversal is made.

The 4–6M mean is 1704.132 bonds (bound fraction 0.852066), 143.238 intra and
1560.894 inter. Accepted creations/ruptures are 1.639900/1.640383 per physical
time; distinct-neighbor gains/losses are 1.404933/1.405317. These are per-system
rates; divide by 1000 for per-star rates. Accepted-event rates and exact population
exposures are not attempted-reaction hazards, diffusion or bond-lifetime estimates.
The scientific kinetics interpretation uses the actual LAMMPS associating fix/pair
implementation on `feature/associating-stickers`, authenticated locally at
`1c6faf70e94aef2389c208e8c80c60c084a96907`: both make/break opportunities are
restricted to candidate edges within r_assoc, with the exact finite-step attempt
probability and Metropolis factors. Thus accepted exchange per population is not
a measurement of rejected opportunities. Reference source hashes are retained in
AUTHENTICATION.json; no new LAMMPS simulation was run.

The 2M exchange comparisons are small and mixed across replicas. One shifted
neighbor-gain contrast (4.5–5M versus 5.5–6M) decreases −0.008067 ± 0.004481;
an overlapping bond contrast changes −1.023 ± 0.303. These exploratory coordinated
changes are retained rather than used to claim perfectly stationary exchange.

## Giant component, peripheral populations and motifs

The late giant remains near 0.993; 1–2M → 5–6M changes by
−0.000448/−0.000448/−0.000557 (−0.000484 ± 0.000156), about half a star in the
mean giant. This small common offset is resolved in that exploratory contrast.
The final 500k changes are mixed, and final 250k changes are −0.003444/+0.000328/
+0.003584. There is no sustained shared late collapse. Peripheral statistics
must still be inspected rather than hiding the change under a near-unity fraction.

At 4–6M there are on average 7.313 components, 5.526 isolated stars, 0.787
non-singleton satellite components and 1.758 satellite stars. Compared with 2–4M,
components increase 0.332, isolates 0.244 and satellite stars 0.223, with mixed
replica changes. Satellite populations are small and bounded; the last-500k
satellite-star changes are +0.236/−0.812/−0.038. Giant/peripheral relationships
remain exact within each recorded frame after the initial isolated-star state.

Distinct-neighbor degree is 3.022169, its second moment 9.974919, and fractions
for degrees 0/1/2/3/4 are 0.005526/0.054242/0.213987/0.365027/0.361218. They show
small coordinated shifts in some comparisons, including the 2–3M → 3–4M degree
redistribution; no degree-sector instability or progressive giant fragmentation
appears. Temporary associations never alter permanent star membership.

L1 counts parallel inter-star bond pairs, including choose(m,2) for multiplicity m;
intra-star loops are tracked separately by intra bonds. L2 counts distinct-star
triangles. From 2–4M to 4–6M L1 decreases −3.1555/−2.9165/−3.9440, mean
−3.338667 ± 1.335783 (~6.2%). The 1–3M versus 4–6M contrast also decreases
−3.329667 ± 1.151786. This is a retained scientific qualification. Much of the
contrast reflects the shared 2–3M peak, followed by lower fluctuating means;
r002/r003 do not show a monotonic late decline. r001 has a more persistent L1
decrease. The final-500k L1 slopes are negative/positive/positive, but the full 4–6M
slopes are negative in every history: −0.0001383/−0.00009383/−0.0004312 per
physical time (fitted changes of roughly −2.77/−1.88/−8.62 over that interval).
The last two consecutive 500k comparisons both decrease in all three histories:
4.5–5M → 5–5.5M is −1.884/−2.956/−0.054 (−1.631 ± 3.646), followed by
5–5.5M → 5.5–6M at −4.372/−3.742/−0.158 (−2.757 ± 5.647). Their wide intervals
do not prove absence of this directed replica-level pattern.
The 4–5M → 5–6M mean changes are also negative in all histories:
−1.755/−1.736/−3.966, mean −2.486 ± 3.185. Relative to 1–2M, the final 1M
contrast is −1.422 ± 6.075. The shared earlier peak and fine-window reversals
make the mechanism ambiguous, but they do not establish that multiplicity
relaxation has ended. A stable giant fraction is insufficient to waive this
specific topology question.
L2 changes +0.067 ± 3.568 between the two late 2M windows and has mixed replica
signs; the earlier high 1–2M triangle population is not uniformly retained.

The supplemental full multigraph replay resolves the L1 change into actual bond
multiplicities. At 4–6M, mean counts of distinct star pairs with 1/2/3/4 bonds are
1461.796/48.768/0.521/0.000. The mean parallel-edge fraction is 0.032629 and mean
edge multiplicity 1.032974 (mean of per-frame ratios). Relative to 2–4M, double
edges decrease by 2.899, triple edges by 0.093 and quadruple edges by 0.027;
weighted by choose(m,2), these reproduce the −3.339 L1 change exactly. This is
mostly a small directed change of the duplicate-edge population, not a proliferation
of high multiplicity or network collapse. Zero late quadruple counts are not proof
of mixing or a forbidden state. Permanent-star intra-loop counts 0/1/2 average
858.454/139.854/1.692 at 4–6M; the final-500k intra rise is mainly an increase of
single-loop stars (135.339 → 141.980) with a smaller double-loop contribution
(1.739 → 2.083). Each frame's L1 and intra/inter accounting were checked against
validated diagnostics. Full distributions and fresh interval uncertainties are in
[multiplicity.json](evidence/multiplicity.json); all initial frames are retained in
three accompanying multiplicity CSVs.

## Replica-level correlation and block sensitivity

Fresh 4–6M estimates (physical-time IAT / effective samples) are:

| Observable | r001 | r002 | r003 |
|---|---:|---:|---:|
| Rg² | 100.84 / 99.17 | 281.81 / 35.48 | 196.29 / 50.95 |
| Center–terminal R² | 58.93 / 169.71 | 269.00 / 37.17 | 234.85 / 42.58 |
| Intra bonds | 1971.74 / 5.07 | 2072.63 / 4.82 | 770.59 / 12.98 |
| Inter bonds | 918.93 / 10.88 | 1137.24 / 8.79 | 265.60 / 37.65 |
| Distinct degree | 1177.19 / 8.49 | 792.60 / 12.62 | 512.28 / 19.52 |
| L1 | 657.30 / 15.21 | 665.17 / 15.03 | 603.88 / 16.56 |
| L2 | 320.55 / 31.20 | 331.44 / 30.17 | 886.13 / 11.29 |

The final 1M intra effective samples are only 4.56/6.97/12.53 and L1 samples
7.19/10.01/16.32. The final 500k r002 shape has only 9.39 Rg² and 6.96 R²
effective samples; apparent mean reversals do not imply independent sampling.
In 4–6M the 5/10/20-block Rg² SEMs are r001 0.004418/0.003843/0.004321,
r002 0.010697/0.007988/0.006778, r003 0.006968/0.005744/0.005420. The corresponding
r002 R² SEMs are 0.029401/0.023799/0.020079. Slow intra uncertainties are strongly
block dependent: r001 4.769/3.522/2.510 and r002 4.441/3.024/2.336 bonds. L1
r001 SEMs are 1.559/1.160/0.913, r002 1.731/1.524/1.466, r003 2.033/1.427/1.254.
Shorter blocks can understate uncertainty; no favorable block count is selected.

Peripheral sampling is better resolved in these long windows: isolated-star effective
samples ~51/20/27 and satellite-star samples ~42/55/106, still correlated and not
independent stars. Accepted exchange counts have much shorter correlations than
slow composition/multiplicity, but their turnover does not certify relaxation of
network shape or motif identities. All interval estimates, slopes, flags, rate
exposures and block sensitivities are in [summary.json](evidence/summary.json) and
[window_estimates.csv](evidence/window_estimates.csv).

## Neighboring accepted density conditions

Both RP020 and RP080 acceptance records, evidence, plans, receipts, exact endpoint
payloads, chemistry and permanent geometry independently authenticated via the
read-only registry validator; no registry was selected. RP020 summary evidence
was hash-bound to its immutable decision. RP080 statistics below come exclusively
from the corrected 7.5–8M C1 window, with its archived analyzer and source hashes
verified; no historical PBC-defective values enter this comparison.

| Late mean | RP020 (5–6M) | RP040 (4–6M) | RP080 corrected (7.5–8M) |
|---|---:|---:|---:|
| Bonds / bound fraction | 1582.398 / 0.791199 | 1704.132 / 0.852066 | 1793.701 / 0.896851 |
| Intra / inter | 243.465 / 1338.933 | 143.238 / 1560.894 | 93.744 / 1699.957 |
| Giant fraction | 0.965958 | 0.992717 | 0.997569 |
| Distinct degree | 2.550833 | 3.022169 | 3.318495 |
| L1 / L2 | 64.268 / 35.169 | 50.330 / 36.967 | 41.225 / 33.471 |
| Creation rate / neighbor gain rate | 1.470633 / 1.132300 | 1.639900 / 1.404933 | 1.821867 / 1.651333 |

At identical f, N, Ee and total bead density, increasing polymer density increases
inter-star contact opportunities while reducing the relative intra-star population;
these qualitative trends are physically plausible and the observed RP040 chemistry
lies between the authenticated neighbors. Different windows and histories prevent
quantitative equivalence claims. Density dependence of motif geometry need not be
monotonic. RP020 late Rg²/R² are 8.005764/18.170953, versus RP040 7.653741/17.359081.
The authenticated corrected RP080 reference lacks comparable conformation series;
no defective or inferred shape value substitutes for them. Neighbor agreement is
context only and never proof of equilibration. See [NEIGHBORS.json](NEIGHBORS.json)
and [NEIGHBOR_STATISTICS.json](NEIGHBOR_STATISTICS.json).

## COM correction and E2 provenance

The attempt was prepared and built at the corrected observer commit `bb7d72a…`.
All 283 relevant recorded C++/CUDA and shared physics/integrator source identities
checked here are identical to pre-correction `75abee1…`, and match current bytes.
The E2 `kg_assoc_stars.cu` includes the unchanged conformation helper, not the
production COM observer. Its E2 compile recipes and flags were unchanged; only
production dependency lists changed in Makefile. The campaign change affects COM
output validation, not E2 dynamics or conformation. [E2_CODE_IDENTITY.json](E2_CODE_IDENTITY.json)
records exact digests. No E2 physics, chemistry or conformation calculation was
altered by that correction. Rebuilding produced a different E2 executable digest;
we authenticate the new plan-bound bytes rather than claiming binary equivalence.
This assessment does not use COM transport as equilibration evidence.

## Decision, justified duration and evidence that would resolve uncertainty

The exact 6M endpoints remain numerically valid, provenance-authenticated candidates;
we do not recommend their qualified acceptance yet. This is a scientific hold on
initialization, not a declaration of numerical failure or a proven large equilibrium
bias. Chemistry, giant/peripheral behavior and degree moments are largely bounded,
and the final chemical redistribution is strongly window dependent. Nevertheless,
L1 has a coordinated 2M mean decrease, negative 4–6M slopes in all histories and
negative latest 1M and last two consecutive 500k changes in all histories. Slow-shape mean shifts also appear in
some paired/shifted comparisons. Limited local effective samples and block sensitivity
prevent treating this combination as authenticated equilibrium fluctuations. The
recommendation rests on this observable-specific pattern, not on a universal 6%
threshold, a zero-containing interval, or a demand for complete topology decorrelation.

A **targeted additional 2M per original history (absolute 6–8M, Ea=4 and all other
frozen parameters unchanged)** would provide two new 1M and four 500k windows plus
one independent segment-local 2M estimate. This duration is long enough for a useful
comparison with 4–6M: roughly 30 existing late L1 IAT units and about ten of the
largest late intra-population IAT units. One extra 500k would remain vulnerable to
the redistribution excursion and give only about 2–3 of those slow intra IAT units.
These times are heuristic estimates under local stationarity, not a guarantee that
2M achieves equilibrium. The original replicas remain three independent histories,
not six; fresh segment-local IAT/SEM estimates must not be stitched through any
MD reseeding boundary. No plan, command, seed allocation, approval or extension was
created or executed here.

The follow-up should answer whether each history's L1 stabilizes or rebounds at the
lower level, or continues a coordinated directional decrease in both 6–7M and 7–8M;
whether r001's larger shape/L1 offsets stabilize; whether Rg²/R² increments reverse
or remain coherent in longer-window comparisons; and whether inter/intra excursions
recur without secular population, degree or peripheral changes. Retain the entire
0–8M context and recheck 500k/1M/2M and shifted contrasts with 5/10/20 blocks. A
jointly bounded later regime, without continued coordinated motif/shape changes
and with better resolved uncertainty, would support reconsidering qualified
initialization. Continuing trends or unresolved correlation/block flags would
justify a further hold and duration chosen from the new slowest time scale. No
single p-value or exact preselected tolerance is an automatic acceptance rule.

Per-star Rg², arm-vector/orientation and association-persistence histories, or
additional independent preparation histories, would strengthen diagnosis of hidden
slow modes if aggregate diagnostics remain inconclusive. They are absent from the
present diagnostic record and would require separately authorized prospective data
collection. No output-format change or simulation is prepared in this review.

Any later formal acceptance requires separate user approval and the immutable
acceptance API. It must be bound to the exact reviewed endpoints and permit only
`production_initial_state` for this system, retaining unresolved shape/topology
sampling and provenance limitations. No COM transport-origin continuity across
restarts follows from E2 numerical validation. All eight existing formal acceptances,
original simulation files and historical reviews remain unchanged.

[Full chemistry](evidence/chemistry.png), [full peripheral network](evidence/periphery.png),
[full shape histories](evidence/shape.png) and [late paths](evidence/late_paths.png).
Full plots retain the initial unbound transient. Consecutive paired evidence is in
[consecutive_comparisons.json](evidence/consecutive_comparisons.json).
