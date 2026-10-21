# Joint scientific assessment: Ea8 at 40M and Ea10 at 56M

Review date: 2026-10-21. Starting local and remote `KremerGrest` HEAD:
`31c3d0660876fc020f1f15f5c38b5a4918945e29`; starting working tree clean.

## Separate scientific decisions

| Exact system | Outcome | Bounded proposal requiring separate authorization |
|---|---|---|
| `F04_N010_RP080_EE08_EA08` | **B. Scientific hold** | An additional **8M per existing replica**, to absolute **48M**, to examine the still-rising r002 intra population and associated shape/coordination redistribution, together with r001 multiplicity excursions. |
| `F04_N010_RP080_EE08_EA10` | **B. Scientific hold** | An additional **32M per existing replica**, to absolute **88M**, to examine r001 multiplicity/shape drift, r002 triangle redistribution, and remaining identity-specific residence and inherited connectivity. |

All six exact endpoints in ENDPOINTS.csv are numerically eligible for scientific review.
Neither system is recommended for formal qualified acceptance at these endpoints. These holds
follow observed replica-specific changes; they do not impose complete decorrelation, zero inherited
edges, an arbitrary ESS threshold, or a stricter new definition of qualified initialization.
The proposals are bounded scientific recommendations, not prepared plans or execution approvals.
No GPU calculation, new extension, acceptance registration, registry action, or production action
was performed in this review.

## Authentication and independent numerical replay

The durable `manual_ea_extensions_readback_v2` campaign contains exactly six histories and no
retired/replacement attempts. Ea8 histories each completed 16M additional steps, 24M--40M;
Ea10 each completed 32M, 24M--56M. Total existing extension execution is exactly 144M MD steps.
The standard strict independent E2 validator reproduced every receipt's validation object exactly:
**1,440,000 recorded candidate-oracle comparisons, 48,239 accepted events, and six actual
initial GPU device-readback payloads covering 43,563 particles each**. Candidate equality is
authenticated from the instrumented executable and complete runtime sweep records against
synchronized GPU-evolved positions; it is not a new GPU calculation or an offline recomputation
from a full-bead trajectory that was never saved.

Plans, preparation-only approvals, execution approvals, immutable source-authorization chains,
seed reservations, exact qualified 24M parent pairs, inherited counters and chemical seeds,
new effective MD streams, native start receipts, PASS footers, endpoint identities, and output
hashes authenticate. The exact parent restart and sidecar are preserved. The native build is
`ea_24m_extensions_readback_20261019_v2`, source/build commit
`055a1a1de43a04edebaad76364726d53cfe654f5`, NVCC 12.8.93 / GCC 11.2.0 optimized toolchain.
The selected `kg_assoc_stars_candidate_smoke` executable SHA256 is
`cab431ac0d110bd635390ffe37fae2527df02642666cc4f8105997b21f780306`.
Its historical filename does not change the guarded ordinary extension semantics.
Exact source maps, build records, commands and seeds are in RESULTS.log and PROVENANCE.tar.gz.

Ea8 r001 retains `incomplete.json` and the distinct `validation_recovery.json`, SHA256
`91a4fa743735a515353d592213d0ee67cf9e2208ca31dc29cfda4b002aaa5091`.
The original administrative error `prepared extension sources/history changed` occurred after
native completion. Its original failure SHA256 remains
`14772d19744e253097b4376195210f9591eb6c85df0a012b0ad25f60c46b017c`.
The recovery record was reauthenticated and its full numerical validation independently reproduced;
it remains distinguishable from the other five ordinary `complete.json` receipts.

The replay checks exact initial positions/velocities under the documented float32 representation,
IDs/types/partners, reciprocal chemistry, accepted-event order and counters, permanent topology,
sampled bond geometry, finite numerical/conformation records, and final restart/sidecar pairs.
Extension sampled permanent distances span 0.819321--1.248051, below R0=1.5. Recorded kinetic
temperature spans 0.962179--0.994752 under the frozen thermostat setting T=1. The same qualifications
about the discrete-time estimator apply as in the previous review; no new temperature calibration
is claimed. Complete potential-energy or stress histories were not recorded and cannot be claimed
as independently checked here. No numerical or provenance failure was found.

## Execution and endpoint summary

C/B are extension-only accepted creations/breaks; G/L are distinct-neighbor gains/losses,
excluding parallel-bond changes that do not change neighbor identity. Intra/inter and final L1/L2
are exact endpoint quantities. L1 counts parallel inter-star bond pairs; L2 counts distinct-star
triangles. Largest-component membership is connectivity, not a wrapping/percolation test.

| Ea | Replica | C / B | G / L | Final bonds | Intra / inter | L1 / L2 | Giant | Isolated identities |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 8 | r001 | 6253 / 6257 | 5645 / 5671 | 1793 | 105 / 1688 | 39 / 32 | 998 | 615,858 |
| 8 | r002 | 6263 / 6247 | 5675 / 5703 | 1793 | 106 / 1687 | 37 / 36 | 1000 | none |
| 8 | r003 | 6437 / 6437 | 5885 / 5867 | 1791 | 92 / 1699 | 32 / 21 | 999 | 507 |
| 10 | r001 | 1710 / 1712 | 1578 / 1555 | 1775 | 87 / 1688 | 28 / 35 | 999 | 62 |
| 10 | r002 | 1719 / 1723 | 1573 / 1569 | 1792 | 90 / 1702 | 31 / 25 | 998 | 637,787 |
| 10 | r003 | 1753 / 1728 | 1585 / 1571 | 1799 | 90 / 1709 | 41 / 34 | 999 | 494 |

REPLICA_DIAGNOSTICS.md includes each original and extension 4M block, exact endpoint degree,
loop/multiplicity/component distributions, correlations, exposures and residence evidence.
WINDOWS.csv contains all 500k, 1M, 2M, 4M and 8M structural windows. KINETICS.csv retains exact
integer event-integrated active-bond, free-sticker and neighbor-edge exposure. Sticker conservation
`2*bond_steps + free_sticker_steps = 4000*segment_steps` holds for every extension.
RESIDENCE.csv and the replay archives retain individual identities, gains/losses and censored
episodes rather than replacing identity turnover with reaction counts.

## Full-history analysis and segment boundaries

The prior 8M--24M review, archived enriched frames and event/network results are hash-authenticated
and retained, including its hold decisions. Original accepted-event files are reread for a new
full structural identity ledger: original-pair/edge never-lost survival, current overlap including
returns, and stars reacting or exchanging neighbors. The extension samples, events and network
observables are independently replayed with the ordinary validator. Plots show both segments in
absolute time, with a visible 24M boundary. Physical and chemical state is inherited there;
GJ noise is fresh, so this is not bitwise MD continuation.

All IATs, SEMs, block estimates and residence/lifetime origins are restricted to their own segment.
No ACF or lifetime estimate is stitched through 24M. Original-edge continuity is used only as a
structural provenance/identity ledger, never as an uninterrupted dynamical trajectory estimate.
Initial frames, all windows and late excursions are retained; no burn-in is silently discarded.
The existing biased-ACF/first-nonpositive-lag IAT estimator is evaluated by the previously validated
FFT implementation and checked against direct summation on synthetic and actual data.
5/10/20-block SEMs and 0.5/1/2/4/8M coarsening show sensitivity. Constant series have null ESS/IAT
and are not evidence of fast mixing. Even nonconstant IAT/ESS estimates presume local stationarity;
drift and sparse identity events can invalidate that premise.

## Ea8: the earlier decline reversed, but late redistribution remains

r002 no longer shows the 8M--24M intra decline (4M means 85.64,75.84,74.02,70.59).
Its extension 4M means are **78.46,79.69,85.22,97.12**. This is a clear reversal, not evidence
that the endpoint has settled. Within the last 8M, the 2M means rise **82.90,87.53,91.24,102.99**.
The final 4M intra slope corresponds to about +26.62 bonds across that window, and its ESS is
only 3.66. Concurrently the last two 4M Rg² means fall 7.0507 to 6.9907, and mean degree falls
about 3.352 to 3.313. The coupled intra/shape/coordination redistribution is material even though
its endpoint bond population is typical and the ensemble intra mean looks smoother.

r003's formerly elevated loop/satellite regime has substantially relaxed. Extension intra means
are **99.87,92.47,99.06,93.21**, with nearly equal 8M means 96.17 and 96.14 and explicit excursions
and returns. Its original endpoint satellite category for star 909 ends at 24,934,300; the final
graph has no satellite and only isolated star 507. This resolves much of the earlier peripheral
hold, but r003 L1 still shifts 35.72,32.62,31.67,30.50, and triangles end lower (L2=21).

r001 intra changes **87.70,99.38,105.40,103.65**, with a late high band rather than a continuing
monotone intra rise. Multiplicity is less resolved: L1 block means **32.24,36.10,38.60,44.59**,
with last-4M L1/L2 ESS 3.88/3.87. The endpoint L1=39 is a return from the late peak, but it does
not erase that window's slow excursion. Rg² also fluctuates rather than establishing one common
family mean.

Actual renewal is strong. Only **2/1643, 2/1665, 3/1674** original 8M distinct edges survive
continuously to 40M; current overlaps are 23/29/21 because some original neighbors return.
All 1000 stars in each family have reacted and gained/lost a neighbor. Extension isolation
visits involve 64/63/57 identities and nonzero-gap returns involve 14/13/8; no star stays isolated
for the entire extension. The hold is therefore not based on near-frozen chemistry.

Under the established qualified-initialization standard, full decorrelation is unnecessary,
but r002's still-rising final 8M and accompanying structural change remain unresolved. Propose
**8M more per existing family to 48M**, giving two additional 4M and four 2M windows to test
whether that new high-intra regime plateaus or returns, while monitoring r001 multiplicity and
r003 peripheral/multiplicity changes. This is a targeted observation interval, not a promise of
acceptance or an automatic extension rule.

## Ea10: peripheral escape and renewal improved; slow structural modes remain

The earlier coherent late intra decrease does not continue unchanged in all replicas. Extension
8M intra means are r001 **96.76,93.58,87.20,88.92**; r002 **92.69,85.84,90.24,92.86**;
r003 **76.70,86.25,84.05,91.73**. r002 returns after a downward excursion, r003 reverses its
early low population, and r001 occupies a lower late band. The final 4M means are 87.10/92.54/91.65.
These changes improve the case over 24M but do not resolve every slow mode.

r001 L1 4M means decline from 45.28 near 24M to 31.54 at 52M--56M, with last two 2M means
33.53 then 29.56 and endpoint 28. This is an unresolved multiplicity redistribution, accompanied
by an Rg² change from first-8M 7.0528 to last-8M 6.9945. r002 L2 changes from an 8M mean 37.45
at 32M--40M to **33.79 then 26.18** in subsequent 8M blocks; its last two 4M means are 28.57
and 23.79. r003 has more returns in multiplicity and conformation, but intra shifts upward late.
Final-4M L1 ESS is only 3.54/4.23/3.34 across families. The concern is the observed shifts,
not low ESS alone.

Original bonds never broken now number **428/1783,458/1787,432/1803**; original distinct edges
never lost number **410/1643,448/1665,421/1674** (24.95%,26.91%,25.15%). Current original-edge
overlap is 451/478/452. There is substantial new exposure: 993/990/986 stars have lost a neighbor
over the full available history, and 998/996/991 have reacted. This is genuine renewal, but it is
still slower and more parent-dependent than Ea8, and remaining inherited edges cannot be treated
as independently renewed samples.

The earlier r001 isolated stars 526 and 950 both leave isolation, at absolute **35,780,300** and
**38,472,300**, respectively. Star 595 stays in the giant throughout the extension. No star remains
isolated for an entire extension. However, sparse peripheral returns remain: extension isolation
visits involve 25/18/22 stars, and only 2/4/2 have nonzero-gap returns. r002 star 767 is isolated
from 37,482,600 to 51,016,700 (13.5341M); r003 star 494's isolation from 51,519,300 remains
right-censored at 56M. Satellite category episodes include r001 star 225 for 5.4491M. Exact
identities/episodes are preserved; a constant component plateau would not establish stationarity.

Propose **32M more per existing family to 88M**, with 4M/8M structural reviews and unchanged
500k diagnostics. This is comparable to the observed 16--32M multiplicity/triangle and peripheral
relaxation scales, and at the observed activity adds roughly 1.6k neighbor losses per family.
That rate projection is conditional on changing eligibility, not an exact kinetic clock or a
required decorrelation percentage. Reassess all earlier evidence and late modes together.

## Paired comparisons and kinetics

The three original Ea4 parent families remain the statistical preparation units. Ea8 and Ea10
descendants are paired, correlated children, not six independent initial preparations. Tables
retain each family and report both shared absolute 36M--40M contrasts and final-4M contrasts
(36M--40M versus 52M--56M). The latter compare different elapsed ages and cannot be interpreted
as a controlled equilibrium barrier experiment.

Final-4M paired Ea10-minus-Ea8 intra differences are **-16.546,-4.579,-1.562**, mean
**-7.562 ±19.689** (exploratory 95% Student-t, df=2). L1 differences are
**-13.043,-10.019,+10.917**, mean **-4.048 ±32.416**; L2 mean is **+0.986 ±19.443**.
Rg² differences are **-0.02427,+0.09262,-0.00082**, mean **+0.02251 ±0.15363**.
These broad, correlated family intervals do not prove equivalence, and ensemble means must not
hide the opposing family paths. Degree, loop and multiplicity contrasts remain in the tables.
The nominally Ea-independent target Hamiltonian supplies an expectation, not proof of equilibrium
invariance of the finite-step coupled MD/chemistry process.

Using exactly `q=-expm1(-20*exp(-Ea))`, **q10/q8=0.13572816038514587**. Extension formation
rates per exact free-sticker exposure have paired Ea10/Ea8 ratios **0.136669,0.139328,0.134197**;
breaking rates per exact active-bond exposure give **0.136814,0.137671,0.134451**. These are
descriptively compatible with the conditional attempt scale. Geometric eligibility, repeated
partners, energy-dependent acceptance, and MD relaxation are not divided out; no exact rescaled
clock, equilibrium equivalence, or sufficient rare-event mixing follows from these ratios.

## Integrity, tests and remaining qualifications

All **3,588** before/after protected file bindings remain unchanged, including prior dossiers,
historical attempts, acceptances, current completed outputs, seed reservations and historical
builds. All **13** formal acceptance records and bound scientific payloads authenticate.
Ea8 r001's original failure, special recovery receipt and campaign state remain unchanged.
No file in `src/*` or `examples/KG/*` changed; no simulation, validator, RNG, physics or
administrative launcher code was modified. New tracked materials are confined to this dossier.

Established E2 CPU suite: **189/189 passed**. Focused extension/transfer/acceptance/selector
suite: **63 tests, 62 passed and 1 existing opt-in skip**; these suites overlap and their counts
must not be added as unique tests. Review-local tests: **10/10 passed**, including direct/FFT
synthetic and actual-series comparisons, same-sweep residence/returns, exact sticker and neighbor
conservation, segment partitions and recovered-record identity. The focused suite retained legacy
unclosed-file ResourceWarnings; no scientific gate was waived. All analysis/test commands were
CPU-only with timeouts no greater than 600 seconds. Six strict endpoint replays passed; no GPU
steps were run by the assessment.

Inherited Ea4 preparation bias, historical source/build provenance limitations already documented
for the accepted reference, incomplete proof of equilibrium invariance, limited effective samples
for slow observables, and incomplete initialization-bias removal remain explicit qualifications.
No additional GPU execution is authorized by this review. **No Ea8 or Ea10 endpoint is presently
recommended for formal qualified acceptance.** See REPRODUCE.md for bounded read-only commands.
