# Ea-transfer capped GPU smoke — complete and passed

**Smoke complete and passed: ready to consider a separately authorized kinetic screen.**
The eleven remaining histories each completed exactly 10,000 additional MD steps
at absolute 8,010,000. New aggregate usage is exactly **110,000 steps**. The
previously validated Ea4 r001 diagnostic is retained as separate historical
evidence, with its original attempt, seeds and source SHA; it was not rerun,
modified or extended. Together these provide twelve numerical-validation histories
and 120,000 steps of combined evidence, not 120,000 new steps.

Starting clean local/remote KremerGrest SHA:
`e85441dec103659ced660933e5d8df410b92c353`. Date: 2026-10-17, Europe/Madrid.
Committed administrative launch source: `dd83add6eab03c795fc5343764af23410ebdc736`.
The final Git SHA is the containing assessment commit, reported after push.

All eleven actual device-to-host initial readbacks pass for 43,563 particles each,
with exact represented coordinates, velocities, identities, types and partners.
All 1,100 corrected independent host-oracle comparisons on synchronized
GPU-evolved positions pass, with exact sets/distances under the frozen strict
cutoff contract. All accepted events, reciprocal chemistry, cumulative counters,
finite sampled states/energies, bond geometry and endpoint validators pass. No
new mismatch, incomplete receipt, failure or retry occurred. The combined cohort
includes the earlier r001 readback and 100 comparisons, for 1,200 comparisons.

## Per-history outcomes

| Ea | Replica | Provenance | MD steps | Readback / oracle | C / B | Neighbor gains / losses | Bonds initial → final |
|---|---|---|---:|---|---|---|---|
| 4 | r001 | existing, not rerun | 10000 | pass / 100 pass | 190 / 187 | 170 / 160 | 1783 → 1786 |
| 4 | r002 | new | 10000 | pass / 100 pass | 188 / 183 | 170 / 169 | 1787 → 1792 |
| 4 | r003 | new | 10000 | pass / 100 pass | 168 / 180 | 157 / 162 | 1803 → 1791 |
| 6 | r001 | new | 10000 | pass / 100 pass | 44 / 29 | 40 / 28 | 1783 → 1798 |
| 6 | r002 | new | 10000 | pass / 100 pass | 38 / 31 | 36 / 28 | 1787 → 1794 |
| 6 | r003 | new | 10000 | pass / 100 pass | 21 / 22 | 20 / 20 | 1803 → 1802 |
| 8 | r001 | new | 10000 | pass / 100 pass | 2 / 2 | 2 / 1 | 1783 → 1783 |
| 8 | r002 | new | 10000 | pass / 100 pass | 4 / 2 | 4 / 0 | 1787 → 1789 |
| 8 | r003 | new | 10000 | pass / 100 pass | 4 / 2 | 3 / 2 | 1803 → 1805 |
| 10 | r001 | new | 10000 | pass / 100 pass | 0 / 0 | 0 / 0 | 1783 → 1783 |
| 10 | r002 | new | 10000 | pass / 100 pass | 1 / 0 | 1 / 0 | 1787 → 1788 |
| 10 | r003 | new | 10000 | pass / 100 pass | 1 / 0 | 1 / 0 | 1803 → 1804 |

C/B counts are accepted creations/breaks. Neighbor gains/losses count changes of
distinct inter-star edges; repeat recrossings can involve the same identities.
No initial synthetic reactions were added and no inherited counters were reset.
Each history starts at 8,000,000, ends at 8,010,000, and spans 100 physical time
units at dt=.01. Inherited counters remain parent-specific.

## Exact exposures and kinetic comparison

| Ea | Replica | Bond × time | Free sticker × time | q/q4 | Expected C / observed C | Expected B / observed B |
|---|---|---:|---:|---:|---|---|
| 4 | r001 | 178442.00 | 43116.00 | 1.000000000 | control | control |
| 4 | r002 | 178588.00 | 42824.00 | 1.000000000 | control | control |
| 4 | r003 | 179481.00 | 41038.00 | 1.000000000 | control | control |
| 6 | r001 | 179134.00 | 41732.00 | 0.157691681 | 29.000 / 44 | 29.603 / 29 |
| 6 | r002 | 179092.00 | 41816.00 | 0.157691681 | 28.948 / 38 | 28.939 / 31 |
| 6 | r003 | 180614.00 | 38772.00 | 0.157691681 | 25.029 / 21 | 28.564 / 22 |
| 8 | r001 | 178330.00 | 43340.00 | 0.021801398 | 4.164 / 2 | 4.074 / 2 |
| 8 | r002 | 178768.00 | 42464.00 | 0.021801398 | 4.064 / 4 | 3.994 / 2 |
| 8 | r003 | 180518.00 | 38964.00 | 0.021801398 | 3.478 / 4 | 3.947 / 2 |
| 10 | r001 | 178300.00 | 43400.00 | 0.002959064 | 0.566 / 0 | 0.553 / 0 |
| 10 | r002 | 178732.00 | 42536.00 | 0.002959064 | 0.553 / 1 | 0.542 / 0 |
| 10 | r003 | 180329.00 | 39342.00 | 0.002959064 | 0.477 / 1 | 0.535 / 0 |

Exposure is integrated exactly from accepted-event order in integer MD-step
units, with same-step events contributing zero elapsed duration, then converted
using dt=.01. The exact bond-step and free-sticker-step integers are retained in
RESULTS.log. Diagnostic-frame averages are not substituted for event integration.
Formation/free-sticker and breaking/bond exposure rates, per-time neighbor activity
and the full time series are recorded per history.

At frozen T=1, nu0=20, Nevery=100, dt=.01,
q(Ea)=-expm1(-20*exp(-Ea)). The exact finite-step ratios, not exp(-ΔEa) alone,
are used in every paired prediction.

| Ea | q | q/q4 |
|---|---:|---:|
| 4 | 0.306714077134 | 1 |
| 6 | 0.0483662585016 | 0.1576916813 |
| 8 | 0.00668679577392 | 0.021801398346 |
| 10 | 0.000907586489265 | 0.00295906369132 |

Predictions use each corresponding control rate per bond-time or free-sticker-time
multiplied by the target exposure and exact q ratio. They are conditional short-run
activity predictions, not a uniform rescaling of the coupled MD/chemistry process.
All-pair geometric counts include occupied/unavailable pairs, so the free-sticker
denominator is descriptive rather than complete eligible formation-pair exposure.
Geometry, energy acceptance and competing updates vary between reseeded children.

Ea6 has 103 creations versus 82.98 predicted and 82 breaks versus 87.11 predicted.
Formation is higher than this simple prediction in r001/r002 (44/38 versus
29.00/28.95), while r003 has 21 versus 25.03. This difference must remain visible;
the smoke neither establishes rate equivalence nor diagnoses equilibrium bias.
Ea8 has 10 creations versus 11.71 predicted and 6 breaks versus 12.01 predicted.
Ea10 has 2 creations versus 1.60 predicted and no breaks versus 1.63 predicted.
With only two Ea8 breaks per history and zero Ea10 breaks, high-barrier rates and
neighbor-loss times are poorly resolved. Zero observed events do not imply zero
attempt probability. No sparse/constant bin is declared converged or mixed.

## Structure and conformation

| Ea | Replica | Intra initial → final | Inter initial → final | L1 / L2 initial → final | Distinct degree initial → final | Components initial → final | Giant initial → final | Rg² initial → final | Terminal R² initial → final |
|---|---|---|---|---|---|---|---|---|---|
| 4 | r001 | 100 → 96 | 1683 → 1690 | 40/33 → 37/30 | 3.286 → 3.306 | 5 → 7 | 996 → 994 | 7.040507 → 7.008466 | 15.951795 → 15.796849 |
| 4 | r002 | 85 → 86 | 1702 → 1706 | 37/42 → 40/40 | 3.330 → 3.332 | 2 → 1 | 999 → 1000 | 6.961489 → 7.035940 | 15.603110 → 15.963685 |
| 4 | r003 | 84 → 81 | 1719 → 1710 | 47/37 → 43/37 | 3.348 → 3.338 | 1 → 1 | 1000 → 1000 | 6.988360 → 6.997073 | 15.827428 → 15.839127 |
| 6 | r001 | 100 → 101 | 1683 → 1697 | 40/33 → 42/33 | 3.286 → 3.310 | 5 → 6 | 996 → 993 | 7.040507 → 6.993768 | 15.951795 → 15.803319 |
| 6 | r002 | 85 → 84 | 1702 → 1710 | 37/42 → 37/43 | 3.330 → 3.346 | 2 → 3 | 999 → 998 | 6.961489 → 7.010905 | 15.603110 → 15.821407 |
| 6 | r003 | 84 → 82 | 1719 → 1720 | 47/37 → 48/37 | 3.348 → 3.348 | 1 → 2 | 1000 → 999 | 6.988360 → 7.042014 | 15.827428 → 15.832236 |
| 8 | r001 | 100 → 99 | 1683 → 1684 | 40/33 → 40/33 | 3.286 → 3.288 | 5 → 5 | 996 → 996 | 7.040507 → 7.029029 | 15.951795 → 15.789353 |
| 8 | r002 | 85 → 83 | 1702 → 1706 | 37/42 → 37/43 | 3.330 → 3.338 | 2 → 2 | 999 → 999 | 6.961489 → 6.974533 | 15.603110 → 15.812117 |
| 8 | r003 | 84 → 85 | 1719 → 1720 | 47/37 → 47/37 | 3.348 → 3.350 | 1 → 1 | 1000 → 1000 | 6.988360 → 7.048486 | 15.827428 → 16.059747 |
| 10 | r001 | 100 → 100 | 1683 → 1683 | 40/33 → 40/33 | 3.286 → 3.286 | 5 → 5 | 996 → 996 | 7.040507 → 7.033472 | 15.951795 → 15.795781 |
| 10 | r002 | 85 → 85 | 1702 → 1703 | 37/42 → 37/42 | 3.330 → 3.332 | 2 → 2 | 999 → 999 | 6.961489 → 6.959513 | 15.603110 → 15.714948 |
| 10 | r003 | 84 → 84 | 1719 → 1720 | 47/37 → 47/37 | 3.348 → 3.350 | 1 → 1 | 1000 → 1000 | 6.988360 → 7.007351 | 15.827428 → 15.801150 |

| Ea | Replica | Initial isolated stars | Final isolated stars |
|---|---|---|---|
| 4 | r001 | [143, 526, 595, 950] | [143, 230, 526, 595, 870, 950] |
| 4 | r002 | [272] | [] |
| 4 | r003 | [] | [] |
| 6 | r001 | [143, 526, 595, 950] | [143, 526, 595, 950] |
| 6 | r002 | [272] | [272, 573] |
| 6 | r003 | [] | [18] |
| 8 | r001 | [143, 526, 595, 950] | [143, 526, 595, 950] |
| 8 | r002 | [272] | [272] |
| 8 | r003 | [] | [] |
| 10 | r001 | [143, 526, 595, 950] | [143, 526, 595, 950] |
| 10 | r002 | [272] | [272] |
| 10 | r003 | [] | [] |

Complete multiplicity 0–4, intra-loop and degree distributions, component sizes,
all isolated identities and every conformation sample are in RESULTS.log. The
Ea6 r001 giant shrinks to 993 while its four isolated IDs persist: a three-star
satellite component is also present. Isolated-star counts alone do not describe
the peripheral network. L1, multiplicity and degree are algebraically related.

The independently hashed actual initial device payload is identical across
Ea4/6/8/10 for each corresponding parent family, including preserved Ea4 r001.
This covers coordinates/velocities, stable IDs/types and chemical partners.
The statistical preparation units remain the three original parent families;
descendants are paired and correlated, not twelve independent preparations.
GJ noise/internal memory resets with fresh streams; these are non-bitwise branches.
Do not stitch correlations, IATs or full bond lifetimes across the 8M boundary.
Initial active bonds are left-censored in child-only lifetime estimates.

## Numerical checks, integrity and limits

New sampled temperature spans 0.967858–0.993254.
Permanent distances span 0.845173–1.169032; recorded active-bond maximum is 1.150149, all below R0=1.5.
There are 121 new finite numerical/conformation samples, plus the existing
eleven r001 samples. Standard runtime invariants and final particle/chemistry
snapshots pass. No invalid FENE state was clamped or ignored. There is no emitted
potential-energy time series or independent proof for every intervening MD step.
Molecule labels in readback are host metadata; permanent topology is authenticated
at input/endpoint, not via a separate device bond-table dump.

170 shared/selector tests, fourteen transfer tests and five forensic tests pass
(189 distinct Python tests). The new selector contributes eleven cases; prior
ten single-history selector cases remain passing. Native host self-tests, original
candidate regressions, 398 cutoff/periodic cases and twelve ULP corruption
rejections also pass. Actual reservation checks exclude requested and effective
stream collisions against all prior reservations/plans/sidecars/state headers.

All twelve formal acceptance records and their payloads pass fresh validation;
their inventory is unchanged. 2,331 old bindings remain byte-identical. The one
intended administrative launcher transition is authenticated against starting Git;
the new test module is an authorized addition. Both failed campaigns, the completed
r001 diagnostic, old seeds, previous dossiers and historical builds remain immutable.
No native/header, reaction, search, force, loader, integrator or frozen parameter
changed; examples/KG and src are unchanged. No native rebuild or replacement was
needed because the established build checker treats only these launcher/tests as
administrative. The preserved repaired executable is used for every new history.

The finite selector accepts only the authorized control r002/r003 and Ea6/8/10
subsets, under explicit system/replica, per-history and aggregate capped approvals.
Omitting the selector cannot use those approvals to launch a default triplet.
Existing ordinary E2 behavior and legacy single-history authorization remain intact.
The planner retains a format-required control r001 entry, but its directory is
empty and it has no execution approval. The entire new reservation set is retired
after this campaign; do not recycle its unused r001 row. All source/approval/parent
and output-reuse gates remained active, with campaign-wide stop on first failure.

The numerical smoke is complete under tested conditions. The historical failing
Ea8 pair remains unidentified; this does not retroactively validate that attempt
or prove the search for every possible boundary state. All reference qualifications,
including incomplete slow-topology relaxation and possible initialization bias,
remain. The smoke does not establish coupled equilibrium invariance or production
readiness. No kinetic screen, ordinary equilibration, new formal acceptance, registry
selection/activation or 100M preparation/launch occurred. GPU execution stops here.

**Smoke complete and passed: ready to consider a separately authorized kinetic screen.**

See EXECUTION.md, REPRODUCTION.md, HISTORIES.csv, RESULTS.log and bound metadata.
