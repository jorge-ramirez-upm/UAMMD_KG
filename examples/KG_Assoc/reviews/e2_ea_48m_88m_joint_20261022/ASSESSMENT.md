# Scientific assessment: Ea8 at 48M and Ea10 at 88M

Review date: 2026-10-22 (client date). Starting clean local and remote
`KremerGrest` HEAD: `3077b0ef56e551899ba30de197995b5d4b4d42da`.

## Separate scientific recommendations

| Exact system | Recommendation for its three exact endpoints |
|---|---|
| F04_N010_RP080_EE08_EA08 | **A. Qualified acceptance recommended**, as `production_initial_state`, for r001/r002/r003 at 48M in ENDPOINTS.csv. |
| F04_N010_RP080_EE08_EA10 | **B. Scientific hold** at 88M: r003's late triangle enrichment and accompanying conformation redistribution remain unresolved. |

These recommendations use the existing E2 qualified-initialization standard, not
proof of equilibrium, an ESS cutoff, complete topology renewal, or fully independent
networks. No formal acceptance was registered. No extension was prepared or authorized.
Ea8 is ready for a separate formal-registration decision. Ea10 has no numerical or
provenance failure, and its previous holds have substantially improved; its remaining
hold concerns a specific observed structural mode, not elapsed runtime alone.

## Authentication and strict independent validation

The immutable `manual_ea_extensions_48m_88m_v1` preparations remain unchanged.
Its frozen state still describes preparation; all six actual `complete.json`
receipts, rather than that historical status label or console output alone, establish
completion. No runtime replacement or interrupted attempt was substituted.

All six strict ordinary endpoint replays passed, reproducing each receipt's
validation object exactly. Ea8 r001--r003 completed **40M to 48M**, exactly 8M each;
Ea10 r001--r003 completed **56M to 88M**, exactly 32M each. Existing new-segment
execution totals **120,000,000 MD steps**. This review integrated **zero** steps.
The replay authenticates **1,200,000 runtime candidate-oracle sweeps**, **29,045
accepted reaction events**, and **six actual initial GPU readback payloads**, each
covering 43,563 particles. Device coordinates, velocities under the documented
float32 representation, IDs, types and chemical partners pass the exact checks.

The independent validator checks parent identity, chemistry continuity, event order,
reciprocity, cumulative counters, particle/permanent topology, sampled numerical
geometry, finite state/conformation data, final restart/sidecar compatibility and
all required output hashes. Candidate evidence is the complete instrumented runtime
comparison record on synchronized GPU-evolved positions, authenticated to its
executable and PASS log. This is not a new GPU comparison or an offline reconstruction
from unsaved full-bead trajectories. No oracle or readback requirement was waived.

Preparation, per-replica execution and source approvals, immutable reservations,
requested/effective MD seeds, inherited chemical seeds/counters, exact parent hashes,
commands, source maps, source-file ancestry, build manifests and executable hashes
authenticate. Started receipts bind the same execution/source records used by
pre-launch and post-native-PASS authentication. The exact selected optimized binary is
`ea_extensions_48m_88m_20261021_v1/kg_assoc_stars_candidate_smoke`, SHA256
`6331c034d8ddb494be616770f2bcc56f5a5fb644f5cb30838e593d259eaf451d`;
NVCC 12.8.93 / GCC 11.2.0, `-O3`, source/build commit
`64070a327d320ac2fb6984adbc002036e396721d`. No executable was rebuilt or replaced.

Ea8 r001's **parent at 40M** retains its special `recovered_complete` lineage:
`validation_recovery.json` SHA256
`91a4fa743735a515353d592213d0ee67cf9e2208ca31dc29cfda4b002aaa5091` and original
`incomplete.json` SHA256
`14772d19744e253097b4376195210f9591eb6c85df0a012b0ad25f60c46b017c`.
The new 48M child has an ordinary validated completion; this does not reclassify or
replace its parent's original failure/recovery. Both original files remain unchanged.

Recorded kinetic-temperature samples span 0.960644--0.995280. Sampled permanent-bond
distances span 0.819148--1.248817, below R0=1.5. The existing discrete-time estimator
qualifications remain; no new thermostat calibration is inferred. Complete potential
energy/stress histories were not recorded and cannot be claimed independently verified.
Numerical completion remains distinct from scientific equilibration.

## Exact endpoint and event summary

C/B are accepted creations/breaks in the newest segment; G/L are distinct-neighbor
gains/losses, excluding parallel-bond changes that do not change neighbor identity.
L1 counts parallel inter-star bond pairs; L2 counts distinct-star triangles.
Largest-component membership is not a wrapping/percolation test.

| Ea | Replica | C / B | G / L | Final bonds | Intra / inter | L1 / L2 | Giant | Isolated star IDs |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 8 | r001 | 3176 / 3167 | 2874 / 2855 | 1802 | 88 / 1714 | 46 / 40 | 998 | 66,646 |
| 8 | r002 | 3107 / 3104 | 2804 / 2788 | 1796 | 93 / 1703 | 37 / 45 | 998 | 422,659 |
| 8 | r003 | 3150 / 3135 | 2878 / 2863 | 1806 | 97 / 1709 | 28 / 31 | 998 | 679,900 |
| 10 | r001 | 1692 / 1660 | 1527 / 1507 | 1807 | 87 / 1720 | 40 / 45 | 999 | 718 |
| 10 | r002 | 1732 / 1749 | 1565 / 1584 | 1775 | 91 / 1684 | 32 / 36 | 1000 | none |
| 10 | r003 | 1689 / 1684 | 1529 / 1522 | 1804 | 89 / 1715 | 40 / 43 | 999 | 458 |

ENDPOINTS.csv gives exact restart, sidecar, receipt, plan and seed identities/hashes.
RESULTS.log and PROVENANCE.tar.gz preserve authenticated source/build/lineage and
receipt metadata. KINETICS.csv contains exact event-integrated active-bond,
free-sticker and neighbor-edge exposures. For every segment,
`2*bond_steps + free_sticker_steps = 4000*segment_steps` holds exactly.
Degree, intra-loop, multiplicity and component distributions and final graph
identities are retained in REPLICA_DIAGNOSTICS.md and the replay archives.

## Complete history, partitions and statistical limits

The full structural history starts at the shared qualified Ea4 parent at 8M.
The authenticated 8M--24M and 24M--40M/56M analyses are retained, and the newest
segments are independently replayed. All three segments appear in absolute-time
plots. Exact events from all three are reread for the original-identity ledger.
That ledger tracks survival/current overlap, not uninterrupted lifetime or IAT.

Every dynamical estimate retains its own MD segment: 8M--24M, 24M--40M/56M,
and 40M--48M or 56M--88M. Fresh GJ streams preclude bitwise MD continuation.
No correlation, SEM, residence or lifetime origin crosses either restart boundary.
Initial and all later frames are retained; no burn-in is silently discarded.

WINDOWS.csv contains 500k, 1M, 2M, 4M and supported 8M windows for every segment.
CORRELATIONS.csv includes full-segment and final-quarter IAT/ESS and 5/10/20-block
SEM sensitivity. FFT and direct estimates agree in synthetic and all six actual
late series. These are descriptive first-nonpositive-lag, biased-ACF estimates;
they presume local stationarity. A constant series has null IAT/ESS, not evidence
of fast mixing. Drift and rare events can invalidate estimated errors. No universal
ESS or arbitrary significance threshold is used for the decisions.

The raw structural, conformation, degree/multiplicity/loop distributions, late ACF,
original identity and censored isolated-residence plots accompany
`plots/coarse_structural_histories.png`, which shows faint 1M and bold 4M means.
The coarse plot makes replica-specific excursions visible without ensemble averaging.

## Ea8: the targeted holds resolve sufficiently for qualified initialization

**r002's rising intra population reverses.** Its previous 4M means at 24M--40M
were 78.46,79.69,85.22,97.12. New 4M means are **107.12 then 96.75**.
The new 2M means are 105.32,108.92,102.20,91.29; final 1M means are 91.08 and
91.50. This is a high-band excursion and return, not an uninterrupted increase.
Its Rg² means are 6.9917 then 6.9992, with final 2M 7.0121; degree recovers from
3.3017 to 3.3295. These changes reverse the previous joint intra/shape/coordination
redistribution. They do not establish a precisely stationary independent sample.

**r001's L1 rise becomes a fluctuating band.** Its former 4M L1 means
32.24,36.10,38.60,44.59 are followed by **43.27,43.87**. New 1M means range
40.26--47.76 with repeated reversals. The high intra band declines: new 4M means
94.57 then 79.86, followed by a final-2M return from 78.69 to 81.03. Rg² is
7.0345/7.0378, within earlier visited bands. Low final-quarter L1 ESS (~3.49)
remains a qualification, not a newly imposed rejection threshold.

**r003's loops and periphery retain excursions and returns.** New intra means
89.70/90.96 are below the earlier elevated-loop regime and show a final 2M return
toward 93.37. L1 rises within the segment (1M means ~41.6) and returns to 25.84
in the final 1M; this is not a one-way continuation of the earlier decline.
Triangle means 29.99/35.74 return into the original preparation's visited band.
The final graph has no satellite and only isolated stars 679 and 900. Star 900's
2.0558M isolation is right-censored, not asserted equilibrated; comparable finite
episodes include r001 star 235, which leaves isolation after 2.5762M.

Renewal is substantial: only **0/1643,1/1665,1/1674** original 8M distinct edges
survive continuously to 48M; current original-edge overlaps are 8/11/14 because
returns are counted separately. All 1000 stars per family have reacted and gained
and lost a neighbor over the full history. In the newest segment, isolation visits
involve 35/32/31 identities, with 4/2/3 identities returning after a nonzero gap.
No initially present triangle survives continuously through the new 8M segment.
This is not a stable mean sustained by a frozen inherited topology.

Under the same qualified-initialization standard used for Ea6, the observed returns,
resolved targeted late rise, broadly stable conformation, and actual renewal support
the **three exact Ea8 48M endpoints**. Their slow fluctuations, residual inherited
bias, and incomplete rare-state sampling remain explicit. Complete decorrelation,
equilibrium invariance or removal of all initialization bias is not claimed.

## Ea10: earlier holds improve, but r003's late motif mode remains open

**r001's former L1 and shape decline reverses.** New L1 8M means are
32.78,34.27,39.79,41.16, returning toward its earlier 41--45 band; final 4M means
41.02/41.29 are similar. Rg² rises from 7.0001 to 7.0786 across the four 8M blocks,
turning back from its earlier low band rather than continuing the old compaction.
Its final 2M shape decreases from 7.0888 to 7.0728, so the last window is not
strictly monotone. Intra means 88.63,94.18,91.30,86.07 show an excursion and return.
These observations resolve the original one-direction L1 decline, with slow shape
uncertainty retained.

**r002's triangle decline also reverses.** Its old final 4M triangle means
28.57/23.79 are followed by new 8M means **25.04,26.13,33.14,35.78**. New final
4M means 37.23/34.32 and 2M means 34.08/34.56 show a return from the peak rather
than ongoing accumulation. Intra means 94.07,101.58,101.26,91.88 likewise return.
Conformation fluctuates within earlier visited bands. The final graph is connected.

**r003's triangle/shape redistribution is not yet similarly resolved.** Intra
8M means are nearly stable (87.19,85.32,87.84,87.18), but L2 means rise
**30.90,32.71,36.81,40.26**. The last four 2M L2 means are
**37.84,39.90,41.07,42.22**, and the final 1M mean is **43.53**. This increasingly
occupied high-triangle band exceeds its earlier 4M bands (~28.77--36.17).
There are local reversals (e.g. 76M--82M), so an irreversible relaxation is not
proven; however, no sustained return from the final high band is observed.
Concurrent Rg² 8M means decrease 7.0675,7.0577,7.0414 after the early high band;
final 2M means are 7.0391 then 7.0193. Shape alone revisits earlier values, but the
joint late triangle/conformation redistribution remains an open mode. Similar
ensemble means would conceal it.

An additional independent triangle-identity replay checks **every diagnostic L2**.
For r003 at 56M there are 34 triangles; the new segment has **108 gains and
99 losses**, ends with 43 triangles, and visits 135 distinct triangle identities.
Only **3** initial triangles survive continuously, and **4** overlap the final set.
The last 16M has 63 gains/52 losses. Thus the concern is active distinct-neighbor
rewiring into a more closed local network, not frozen triangles. Counts include
repeated motifs and correlated changes; no independent-Poisson significance or
causal claim about conformation is inferred. TRIANGLE_TURNOVER.csv and
TRIANGLE_IDENTITIES.log retain exact identities and changes.

Inherited connectivity is greatly reduced but not absent: continuously surviving
8M distinct edges number **170/1643,164/1665,152/1674** (~9--10%); current overlaps
are 206/195/192. All 1000 stars per family now have reacted and gained/lost a
neighbor. Original physical bonds never broken number 163/161/153. These are
qualifications, not automatic reasons to reject qualified initialization.

Peripheral escape is demonstrated. r003's previously isolated star 494 leaves at
**58,953,900**; its new-segment episode is left-censored at 56M rather than stitched
into a lifetime across fresh GJ noise. New r003 star 166 leaves after a 19.0125M
episode at 76,471,500. r002's satellite star 72 leaves that category after 11.0219M
at 82,388,400. No star stays isolated for the whole new extension. Sparse returns
and long residences still limit rare-mode precision, but do not drive this hold.

**Retain the Ea10 scientific hold**, principally because the late r003 motif/shape
mode remains unresolved, not because its ESS is low or some original edges survive.
This does not prove nonequilibrium: the data do not yet distinguish a long structural
excursion from continuing redistribution in that family well enough to recommend
the entire exact triplet. The more relaxed qualified standard is retained; no
complete-renewal or exhaustive-stationarity criterion is introduced.

A further *targeted observation of the r003 triangle/shape return* could be
scientifically useful. Another blanket long extension of all three families is
**not justified automatically**: r001/r002's targeted modes have reversed, and
low ESS by itself supplies neither a duration nor an extension rule. The useful
question is whether the new r003 high-triangle band persists, reverses with motif
losses, or continues shifting, not whether an arbitrary ESS target is reached.
No new duration, plan, seed reservation or GPU approval is issued here. A later
user decision should weigh that specific information gain against cost; simply
running longer cannot prove coupled-algorithm equilibrium invariance.

## Paired comparisons, rates and qualifications

The original three Ea4 families remain the preparation units. Ea8 and Ea10 children
are paired and correlated, not six independent original preparations. Tables retain
per-family final-4M contrasts (different absolute ages) and common absolute 40M--48M
contrasts drawn from their respective valid segments. Neither comparison establishes
an exact rescaled-clock experiment or equilibrium equivalence.

Final-4M Ea10-minus-Ea8 paired means (exploratory Student-t intervals, df=2) are:
intra **-0.523 ±13.503**, L1 **-0.561 ±9.779**, L2 **+1.189 ±18.188** and
Rg² **+0.03186 ±0.08185**. The wide intervals do not demonstrate equivalence;
replica-specific redistribution remains visible. The nominally Ea-independent target
Hamiltonian is an expectation, not proof about the finite-step coupled dynamics.

Using exactly `q=-expm1(-20*exp(-Ea))`, q10/q8 is **0.13572816038514587**.
New-segment formation rates per exact free-sticker exposure have family ratios
0.13455/0.13873/0.13709; breaking rates per exact active-bond exposure give
0.13089/0.14094/0.13394. This is descriptive compatibility with the conditional
attempt scale. Eligibility, energy-dependent acceptance, repeated partners and MD
relaxation have not been divided out; no exact clock rescaling follows.

## Tests, preservation and scope

All **4,802** before/after protected file bindings remain unchanged, covering the
thirteen formal acceptances and bound states, historical source/build evidence,
all previous dossiers, reservations, historical attempts/failures/recovery and the
six current completed output sets. All **13** formal acceptances authenticate.
No file in `src/*`, `examples/KG/*`, the physical model, RNG, integrator, numerical
validator, or production launcher was modified. New tracked files are confined to
this review dossier. Exact inventories and byte archives make preservation auditable.

Established E2 CPU regressions: **189 passed**. Review-local estimator, conservation,
partition, actual-series FFT/direct, endpoint/identity and recovery tests: **11 passed**.
Triangle handling/parallel-bond/return regressions: **2 passed**; all six independent
triangle replays matched every sampled L2 (120,006 samples). The driver self-tests
also pass. All assistant jobs were CPU-only, each bounded by a timeout of at most
600 s. INTEGRITY.sha256, PROVENANCE.sha256 and ANALYSIS.sha256 authenticate artifacts.
REPRODUCE.md gives read-only verification and bounded reproduction commands.

The accepted-reference inherited Ea4 route and historical provenance qualifications,
unproven equilibrium invariance, incomplete initialization-bias removal, limited slow
observable effective samples, correlated families and sparse rare-component sampling
remain explicit for both systems. Ea8's recommendation is restricted to qualified
`production_initial_state`; Ea10 remains held. No formal registration, simulation,
extension preparation, registry activation or production action was performed.
