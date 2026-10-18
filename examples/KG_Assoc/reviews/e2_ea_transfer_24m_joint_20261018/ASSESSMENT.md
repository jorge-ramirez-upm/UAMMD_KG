# Joint scientific assessment: nine Ea-transfer 24M endpoints

Review date: 2026-10-18. Starting local/remote `KremerGrest` SHA:
`deb0ef3797917ee1cd890d19765ec654ecc3efce`; starting tree clean.

## Decisions

| Exact system | Outcome | Recommendation |
|---|---|---|
| `F04_N010_RP080_EE08_EA06` | **A. Qualified acceptance recommended** | The three exact 24M pairs in ENDPOINTS.csv are suitable as `production_initial_state`, subject to the qualifications below and separate formal approval. |
| `F04_N010_RP080_EE08_EA08` | **B. Scientific hold** | Propose one additional 16M per existing history, to absolute 40M, then reassess individual slow structural regimes. |
| `F04_N010_RP080_EE08_EA10` | **B. Scientific hold** | Propose one additional 32M per existing history, to absolute 56M, then reassess topology renewal, peripheral residence and late changes. |

These are system-specific scientific recommendations, not acceptance records or
simulation authorizations. No formal acceptance, registry selection, production
preparation or extension was performed. **No GPU calculation was launched by
this assessment.** The 144M steps were completed manually before the review.

## Authentication and numerical completion

The durable `aggregate/e2/manual_ea16m_v1/state.json`, its three unique plans,
nine replica-bound approvals and nine started/completed receipts authenticate
nine distinct histories executed on `titan`. Every actual plan is 16,000,000
additional steps, absolute 8,000,000→24,000,000; no retired/replacement attempts
are present. Every history has 16,001 diagnostic frames and 160,000 candidate
comparisons. Independent CPU validation reproduces all nine complete receipts'
validation objects exactly, with 319,041 accepted events replayed and 1,440,000
candidate comparisons authenticated. No failed/incomplete output was promoted.

`PROVENANCE.log` binds original parents, acceptance and reservations, all source
and executable hashes, exact commands, approvals, receipts, logs and endpoint
outputs. `ENDPOINTS.csv` identifies every exact final restart/chemistry pair.
The shared qualified parent is the corrected-C1 Ea4/Ee8 acceptance
`F04_N010_RP080_EE08_EA04_8M_qualified_20261013_v1`, hash
`525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22`.
Parents are the original r001/r002/r003 8M pairs, never short-smoke descendants.
Chemistry/cumulative counters and absolute steps are inherited; future chemical
and effective MD streams are fresh and collision-checked under the immutable
manual reservations. The three parent families remain the preparation units.

The unchanged executable is the authenticated out-of-tree
`builds/ea_transfer_16m_20261017_v1/kg_assoc_stars_candidate_smoke`, SHA256
`f108e201b2280af28df6ffc607f5b138900bca9f0a67954e59a90e05f51ab5f8`.
Its legacy filename does not change the explicitly guarded ordinary 16M mode.
Build source commit is `2d56f2ec26ba5780fcf38549264e7070ec46c71c`;
NVCC12.8/GCC11.2 optimized build. The manual plans' source commit is the starting
SHA above. Their scientific-source identity and build manifests authenticate;
no rebuilding or execution of a GPU binary was needed in this review.

For all 43,563 particles/history, recorded actual initial device-to-host readback
matches parent positions/velocities under the exact float32 contract, identities,
types and reciprocal partners. Actual payloads match across Ea within each
parent family, also matching the preserved successful smoke payloads. Candidate
records are the independent host oracle against synchronized GPU-evolved
positions at every reaction sweep; they are not new host-only surrogate runs.
Strict cutoff semantics and equality remain unchanged. There is no full-bead trajectory from which every historical candidate set could be recalculated offline; per-sweep equality is authenticated from the instrumented runtime records and executable identity, while event replay is independently recomputed. Ordered accepted-event
replay verifies valence, inherited counters, each sampled intra/inter and graph
observable, and exact final partners/sidecars. Final restart timestamps, particle
identities, permanent topology, conformation, finite coordinates/velocities,
kinetic observations and runtime seed logs all validate.

Permanent-bond sampled distances span 0.823720–1.248770, below R0=1.5. Active
bond geometry and runtime invariants pass the established validator. Sampled
kinetic temperatures span 0.962271–0.996474 across the nine paths; the frozen
thermostat setting remains T=1. These are the existing discrete-time kinetic
estimator values, not a new calibration of configurational temperature. No
barrier-specific numerical failure was detected. Outputs do not contain a full
potential-energy or stress trajectory; this review does not claim those tests.

## Per-history execution and topology renewal

All rows below passed numerical replay and exact device readback. C/B are new
accepted events, excluding inherited offsets. G/L are distinct neighbor edge
transitions, not parallel physical-bond events. Survival means never broken/lost
since the 8M branch boundary; current overlap, including returns, is separately
recorded. All counters and exposures are in KINETICS.csv and RENEWAL.csv.

| Ea | Replica | C / B | G / L | Bonds 8M→24M | Intra 8M→24M | L1/L2 at 24M | Original bonds / edges never lost | Stars losing ≥1 neighbor |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 6 | r001 | 46111 / 46089 | 41810 / 41768 | 1783→1805 | 100→79 | 41/26 | 0/1783 / 0/1643 | 1000/1000 |
| 6 | r002 | 46090 / 46087 | 41814 / 41833 | 1787→1790 | 85→107 | 37/27 | 0/1787 / 0/1665 | 1000/1000 |
| 6 | r003 | 45688 / 45690 | 41432 / 41438 | 1803→1801 | 84→88 | 46/35 | 0/1803 / 0/1674 | 1000/1000 |
| 8 | r001 | 6401 / 6387 | 5784 / 5752 | 1783→1797 | 100→82 | 40/28 | 47/1783 / 48/1643 | 1000/1000 |
| 8 | r002 | 6379 / 6389 | 5828 / 5815 | 1787→1777 | 85→64 | 35/34 | 59/1787 / 65/1665 | 1000/1000 |
| 8 | r003 | 6329 / 6341 | 5693 / 5718 | 1803→1791 | 84→105 | 37/44 | 61/1803 / 68/1674 | 1000/1000 |
| 10 | r001 | 807 / 813 | 733 / 739 | 1783→1777 | 100→95 | 45/34 | 1133/1783 / 1048/1643 | 790/1000 |
| 10 | r002 | 846 / 837 | 771 / 769 | 1787→1796 | 85→98 | 32/34 | 1123/1787 / 1053/1665 | 811/1000 |
| 10 | r003 | 864 / 893 | 787 / 806 | 1803→1774 | 84→77 | 42/35 | 1098/1803 / 1039/1674 | 807/1000 |

## Analysis and interpretation

There are 32 nonoverlapping `(start,end]` 500k-step windows/history, coarsened
into 16×1M, 8×2M and 4×4M windows. Shifted 4M windows start at 10M,14M,18M.
Initial frames, complete-segment and early/middle/late thirds are retained; the
last quarter is absolute 20M–24M. No burn-in is silently discarded. Event bins
use absolute 100-step chemistry cadence; activity summaries use 1000-step bins.
Exact integer event-integrated bond, free-sticker and distinct-edge exposures
include ordered same-step events and both boundary censoring conventions.
Each history spans 160,000 physical time units, dt=.01. Sticker conservation
`2*bond_steps + free_sticker_steps = 4000*16M` holds exactly.

REPLICA_DIAGNOSTICS.md supplies each replica's four-quarter chemical, network and
conformation statistics, correlation estimates and complete endpoint degree,
loop, multiplicity and component distributions. The replay archives contain
all 16,001 enriched frames, window distributions, exact identity-specific
residence episodes, and never-lost survival versus current-overlap histories.
Intra-loop populations mean stars with 0/1/2 intra bonds; L1 counts pairs of
parallel inter-star bonds and L2 counts distinct-star triangles. Multiplicity
0 is reported over all 499,500 possible inter-star pairs. Largest component is
connectivity, not a periodic-wrapping/percolation measurement. Mean Rg² is the
recorded conformation observable, not the square of a measured mean Rg.

The existing biased autocorrelation/first-nonpositive-lag IAT definition is
retained. Review-local FFT evaluation is tested against direct summation on
synthetic and actual data. No shared estimator or validator was edited.
CORRELATIONS.csv retains IAT, ESS, slopes in the replay archive, and 5/10/20-block
SEM sensitivity at all four window scales. Constant series have unresolved
mixing and null ESS/IAT, not artificial independent-sample counts. Even a
nonconstant series can have unresolved IAT or ESS<10. These flags do not impose
a new scientific acceptance threshold. SEM assumes local stationarity; long
slow drift and rare identities can invalidate that assumption. ACF plots are
descriptive. Repeated same-star events and repeated neighbor returns are never
counted as independent preparations.

### Ea6: qualified initialization recommended

All three paths show repeated structural excursions and returns. Quarter means
of total bonds lie in 1791.23–1794.82, rather than moving coherently away from
the qualified reference. r001 intra means 88.09,90.73,97.89,91.42 return after
an upward excursion; r002 96.23,95.28,85.18,98.95 return after a downward one;
r003 86.43,80.56,92.21,89.88 also reverses. Shifted windows retain these reversals.
L1/L2 and coordination fluctuate with corresponding returns; the late Rg²
last-minus-previous-quarter changes are +.00014,−.00329,−.00059. The giant remains
near the system size with repeated peripheral excursions, not a new sustained
fragmentation regime. Endpoint isolated IDs are [484], [383], [].

There are ~45.7–46.1k breaks and ~41.4–41.8k distinct edge losses per replica.
All 1000 stars in each path react and gain/lose a neighbor; no original physical
bond or distinct edge survives uninterrupted to 24M. Isolation visits involve
350/351/335 stars (including zero-duration ordered episodes), with 128/133/108
stars returning after a nonzero gap. This is substantial identity renewal and
observed peripheral return evidence, not merely a stable global bond count.

Some late-window slow observables remain imprecise: final-quarter intra ESS
is about 10.0/5.0/7.1 and L1 ESS 6.2/10.1/11.8. We therefore do not claim fully
independent endpoint networks, equilibrium invariance or exhaustive rare-state
sampling. Under the established **qualified production-initialization** standard,
the absence of a resolved coherent late relaxation together with multiple
replica-specific returns, stable shape and broad actual renewal supports the
three exact Ea6 endpoints. Full structural decorrelation is not made an extra
prerequisite. r002 is still on a late upward intra excursion, so its endpoint
is not declared a stationary independent network sample. Its return toward the
earlier high-intra band, rather than a new monotone regime across the complete
segment, is the qualified-initialization evidence. This distinction follows the
earlier [qualified E2 review](../e2_rp040_ee8_8m_20261014/ASSESSMENT.md); it does
not eliminate replica-specific uncertainty. The inherited reference-route and
timestep qualifications remain.

### Ea8: scientific hold; propose 16M additional per existing history

This is not a numerical failure or a lack of chemical events. Every star in all
three replicas reacts and gains/loses neighbors; only 48/65/68 original edges
remain never lost, about 2.9–4.1%. Approximately 6.3–6.4k breaks and 5.7–5.8k
neighbor losses/history show real activity. Nevertheless there is a material
replica-specific redistribution that the ensemble mean conceals.

r002 intra quarter means are 85.64→75.84→74.02→70.59, with shifted means
79.56→75.53→71.26 and endpoint 64. r003 follows the opposing path
87.20→92.99→104.65→104.56, shifted 85.95→100.23→105.73. Its last-quarter
largest-component fraction drops from .99840 to .99644 and includes a persistent
two-star satellite. r001 reverses an intra excursion but final-quarter L1/L2
ESS are only about 4.36/3.28. r003 has a local intra plateau, yet L2 ESS≈3.37;
a plateau in one mode does not resolve the inter-star/peripheral redistribution.
Final-quarter Rg² means are 7.0386/7.0583/6.9940: finite and overlapping in broad
family uncertainty, but not a demonstration that individual slow regimes match.

Intra quarter differences and correlated distributions remain unresolved despite
wide paired confidence intervals. Holding is based on these actual slow paths,
not on requiring every original edge to disappear or requiring a universal ESS.
An additional bounded **16M/history to absolute 40M** should test whether r002
returns from its low-intra regime and r003's high-loop/satellite regime persists
or returns, while retaining paired families and 500k/1M/2M/4M diagnostics. This
adds another segment comparable to the observed relaxation, not a promise of
acceptance. Reassess all modes jointly; do not discard the first segment.

### Ea10: scientific hold; propose 32M additional per existing history

Activity is limited: only 813/837/893 breaks and 739/769/806 distinct neighbor
losses, less than one neighbor loss/star over 16M. 1048/1053/1039 original edges
survive uninterrupted (62.1–63.8%); 1133/1123/1098 original bonds survive
(60.9–63.5%). Only 790/811/807 stars lose a neighbor; 881/887/896 experience any
accepted reaction. This cannot be equated to whole-network relaxation.

r001's initially isolated stars **526 and 950 remain isolated for all 16M**;
595 first leaves isolation only at absolute 20,588,700. Only 16/13/12 stars visit
isolation and 0/0/2 return after a nonzero gap. Satellite plateaus include a
late persistent r002 pair and a long r003 excursion. Constant peripheral bins
therefore remain censored/inadequately explored, not equilibrated.

There are also actual late changes: last-minus-previous-quarter intra means are
−1.9275/−3.4500/−3.3890. Across the three families the exploratory mean is
−2.9222±2.1414 (95% t, df=2), before any multiple-comparison correction.
All three giant fractions increase over the same comparison: returns are
occurring, but a common settled late regime has not been established. r001
bond mean drops 1797.48→1781.81 between the last two quarters. Final-quarter
L2 ESS is only about 4.18/4.11/3.29, and degree ESS remains low in all three paths.
Narrow fluctuations in individual constant bins do not override this evidence.

Propose a bounded **32M/history to absolute 56M**, retaining existing histories
and all earlier evidence. At observed activity this may add roughly 1.5–1.6k
neighbor losses/history, useful for testing identity coverage and peripheral
returns. This is a budget estimate conditional on changing eligibility, not an
exact rescaled clock or a target decorrelation percentage. Examine 4M and 8M
late subsegments as well as the standard windows, with no automatic acceptance
at the new endpoint. No extension or restart execution is authorized here.

## Paired cross-Ea comparisons and kinetics

For every parent family the physical/chemical initial payload is identical
across barriers; future MD/chemistry streams differ. Cross-Ea children are
correlated descendants of three original preparations, not nine independent
samples. PAIRED_CONTRASTS.csv compares all three barrier pairs with df=2
uncertainty; DISTRIBUTION_CONTRASTS.csv also reports correlated empirical-CDF
distances per parent family, without misleading IID KS p-values.

For intra bonds, paired late Ea8−Ea6 differences are −3.952,−28.364,+14.676;
the family mean is −5.880±53.624. Ea10−Ea6 is −2.748±19.630. These intervals
show limited independent-family resolution; containing zero is not evidence of
equivalence. The opposing Ea8 family paths matter more than a small ensemble
mean. Degree, multiplicity, loops, L1/L2, connectivity and shape distributions
remain explicitly paired. Neither nominal Ea-independent Hamiltonian nor
similar means establishes equilibrium invariance of the split coupled process.

With `q=-expm1(-20*exp(-Ea))`, exact finite-step q is
.04836625850157813 / .0066867957739190345 / .0009075864892651985 for Ea6/8/10.
Ratios q8/q6=.13825331917499578 and q10/q6=.018764868678762595 are compared with
actual event-integrated exposure rates. Paired creation rate ratios are
.13872/.13968/.13831 for Ea8 and .01738/.01859/.01858 for Ea10; rupture rate
ratios .13859/.13848/.13881 and .01765/.01814/.01959. These are descriptively
compatible with the conditional attempt-scale expectation. They neither prove
equilibrium nor turn MD+chemistry into an exact clock rescaling: geometric
eligibility, repeated partners and energy-dependent acceptance are not divided
out. The short historical Ea4 controls are preserved as separately seeded
conditional-rate comparison evidence, not bitwise continuations or precise
long-run rate estimates.

## Preservation, tests and reproducibility

All twelve formal records and all bound scientific payloads authenticate. The
previous handoff verifier confirms its 2626 protected bindings, with only its
three already documented earlier administrative/validation source transitions.
The new before/after snapshot verifies **2895 current file bindings unchanged**,
including prior dossiers, both failed smoke campaigns, successful diagnostic/
smoke evidence, manual outputs, source/build files and historical executable
builds. No protected `examples/KG/*` or `src/*` file was modified.

Established E2 suite: **189/189 passed** (19.595 s; final output-directory driver rerun 17.693 s). Transfer suite: **14/14
passed** (103.795 s). Review-local analysis: **14/14 passed** (final rerun 1.803 s). Five synthetic
IAT fixtures plus all nine actual histories' intra/L1/degree snippets agree with
direct summation. Exact same-sweep residence, return, censoring, parallel-edge
and sticker-time conservation tests pass. All CPU invocations have a 600 s
outer timeout; no CPU job exceeded ten minutes.

Broad discovery is retained transparently in REGRESSION.log: 229 tests,
226 passed, two obsolete acceptance-count assertions (9 versus the existing12)
and one unrelated missing `correlator` import. These pre-existing suite issues
were not edited or hidden and do not change the successful endpoint validation.
Nonfatal legacy unclosed-file warnings are retained in that log. They remain
maintenance limitations separate from the scientific recommendations.

See REPRODUCE.md for bounded read-only commands, software versions, archived
analysis records and dataset requirements. New materials are confined to this
review directory. No simulation algorithm, numerical gate, accepted state,
historical reservation or output was changed. Formal acceptance of **only the
three exact Ea6 24M pairs** is ready to be considered under separate approval;
Ea8 and Ea10 remain on scientific hold.
