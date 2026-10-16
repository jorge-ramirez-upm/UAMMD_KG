# Ea4 r001 single-history GPU diagnostic — runtime pass

**The one authorized history completed all existing runtime gates at exactly
10,000 additional MD steps. No further GPU work was launched.** The repaired
initial device readback actually executed and passed for all 43,563 particles,
with zero position MIC error and zero velocity error. All 100 corrected candidate
comparisons passed during the actual GPU trajectory; accepted-event replay,
numerical checks and the single endpoint validator also pass.

Implementation distinction: the established independent all-pairs oracle is a
host routine over live positions read after GPU synchronization. Those runtime
comparisons actually executed during GPU MD; they are not host-only synthetic
fixtures. No oracle CUDA kernel exists in this implementation or was executed.
Under a literal requirement that the oracle itself run as a CUDA kernel, that
criterion remains unfulfilled. This report claims validation against the oracle
on live GPU-evolved states, not GPU-kernel validation of the oracle algorithm.
No search, oracle, force, integrator or reaction implementation was changed here.

The original requested starting SHA was
`e63944aedfa7432c69a0b40fff2437a58a24bd21`. The prior preflight documented that
zero-step execution was unsupported and the launcher always ran a triplet, at
`b645475647ccb70930635f5f948c8db18990cdd0`. After the user explicitly authorized
a narrowly scoped launcher selector, administrative source/tests were committed
at `83910377c98049170aacd4bd42dfef434dd6e44e`. Clean local and remote HEAD agreed
there before launch. The final SHA is this dossier's containing receipt commit.
The earlier held-preflight dossier and both historical failed smoke campaigns
remain unchanged; this is a new immutable attempt, not their continuation.

The selector accepts only derived Ea4 r001 reference-control smokes with a
3,000–10,000-step plan. Its approval must name authorized_replicas=[1] and the
exact additional-step cap. The same approval cannot launch the default triplet.
Existing parent, build, clean-source, seed, output-reuse, locking, event and endpoint
checks remain active. Scope is rechecked immediately before execution. Defaults
retain their existing three-history behavior. Ten deterministic selector tests
cover these restrictions, approval tampering, source failure, no retry after
failure and untouched unselected directories. Native sources are unchanged, so
no rebuild was required; the latest repaired out-of-tree executable authenticated.

The existing planner and reservation schema still require three plan entries and
twelve reservation rows. Only r001 had execution approval and was launched. r002
and r003 directories are empty; no new Ea6/8/10 branch attempt was prepared or
executed. All rows in the new reservation set are retired after this diagnostic,
including unexecuted entries; they are not future execution authority.

## Gates exercised

| Gate | Observed result |
|---|---|
| Host parent/acceptance/build authentication | Passed; exact qualified corrected-C1 r001 at 8M |
| Actual device-to-host initial readback | Passed; 43,563 particles; exact represented coordinates/velocities, stable IDs/types and partners |
| Initial chemistry/counters | Reciprocal parent pairs preserved; creations 119665, breaks 117882, bonds 1783 |
| Live-trajectory candidate comparisons | 100 passed; 250367 ordered candidate-pair observations; strict corrected contract |
| Accepted-event replay | 377 events; all partners, identities, cadence and counters consistent |
| Numerical checks | Standard runtime invariants plus 11 finite numerical/conformation samples and final snapshot checks passed |
| Single endpoint | Validated complete receipt at absolute 8,010,000 |
| Other histories | Unexecuted; no replica r002/r003 outputs |

The complete readback compares every actual chemical partner to the authenticated
reciprocal parent graph. Molecule columns are host metadata, not an independent
device molecule-property measurement. Permanent topology is authenticated on input
and endpoint with the native load count; no separate device bond-table dump exists.
Cumulative chemistry counters are host accounting, verified by initial state and
complete event replay, not a GPU counter-memory readback.

Physical time runs 80,000 to 80,100 (dt=.01), branch age 0 to 10,000 steps.
Accepted creations/breaks are 190/187, with distinct-neighbor gains/losses 170/160.
Cumulative counters end at 119855/118069, conserving 1786 active bonds. Exact
integer event integration gives 17,844,200 bond-steps and 4,311,600 free-sticker-steps,
or 178442 bond-time and 43116 free-sticker-time. Same-step events contribute zero
lag. The 178442 active-candidate observations precede chemistry updates; nonactive
geometric candidates include occupied/unavailable pairs and are not eligible
formation opportunities.

Sampled temperature is 0.972475–0.984692; permanent distances span
0.848585–1.160430, below R0=1.5. Recorded maximum active-bond distance is 1.131955.
Kinetic energies and sampled/final states are finite. Standard checks do not emit
a potential-energy time series or prove every intervening MD-step state separately.
No invalid FENE state was ignored or clamped.

## Initial/final structure and earlier-control comparison

| Observable | Initial parent | New endpoint | Earlier r001 control endpoint |
|---|---:|---:|---:|
| Association bonds | 1783 | 1786 | 1791 |
| Intra / inter bonds | 100 / 1683 | 96 / 1690 | 100 / 1691 |
| L1 / L2 | 40 / 33 | 37 / 30 | 41 / 29 |
| Mean distinct degree | 3.286 | 3.306 | 3.300 |
| Connected components | 5 | 7 | 5 |
| Largest component | 996 | 994 | 996 |
| Isolated stars | 4 | 6 | 4 |
| Rg² | 7.040507 | 7.008466 | 7.024596 |
| Center–terminal R² | 15.951795 | 15.796849 | 15.845755 |

Initial isolated IDs [143,526,595,950] persist at the new endpoint, joined by
[230,870]. Initial/final inter-star multiplicities 0/1/2/3/4 are
497857/1603/40/0/0 and 497847/1616/37/0/0. Intra-loop populations 0/1/2 change
903/94/3 to 906/92/2. Full distinct-degree distributions, component sizes, isolated
identities and all eleven samples are in RESULTS.log. L1, multiplicity and degree
changes are algebraically related, not independent mixing evidence.

The earlier r001 control from the same exact parent recorded creations/breaks
195/187 and neighbor gains/losses 180/173 over the same 100 physical time units.
New rates per time are 1.90/1.87 for creation/breaking and 1.70/1.60 for neighbor
gain/loss, versus 1.95/1.87 and 1.80/1.73 earlier. Ea remains 4, so the exact
q=-expm1(-20*exp(-4)) is unchanged (about 0.3067140771). Applying the earlier
break hazard per bond-time to the new exposure predicts 187.3486 breaks versus
187 observed (ratio 0.99814). This is a conditional short-run comparison; geometry,
competing events and correlations vary. It is not a rate-equivalence test.

Both descendants share one parent preparation and have fresh MD/chemistry streams.
They are not independent preparations or bitwise continuations. GJ noise/internal
state resets; velocities and represented physical state are preserved. Initial
bonds remain left-censored for child-only lifetimes; do not stitch correlations,
IATs or lifetimes across the branch boundary. Similar activity and small endpoint
changes do not establish equilibrium invariance, peripheral-state relaxation,
slow-topology mixing or production readiness. All reference qualifications persist.

## Validation and decision

159 shared/selector tests, 14 transfer tests and nine focused readback/forensic
tests pass (178 distinct Python tests; four focused tests overlap the shared set).
Native candidate regressions, 398 cutoff/periodic cases, twelve exact ULP rejection
cases and both native host self-tests pass. The three planner host probes passed;
only r001 proceeded to CUDA. All twelve formal acceptances pass fresh exclusive
validation. 2,255 old file bindings remain identical; one administrative launcher
source transition is authenticated against the continuation-start Git blob.
The new selector test module is an explicitly authorized addition. Both historical
failures, their seeds/attempts, prior builds/reviews and protected outputs remain
immutable. examples/KG, src and all native/frozen simulation sources are unchanged.

**Single-history runtime infrastructure passes under these tested conditions.**
The wider campaign and kinetic screen remain on hold; r002/r003 and higher barriers
were not tested by this milestone. The historical Ea8 failing pair remains unknown,
and this Ea4 result does not prove all future cutoff/search cases. No formal
acceptance, registry selection, ordinary equilibration or production preparation
was performed. Further GPU work requires separate authorization. Execution stops
here at exactly 10,000 aggregate additional MD steps.

See EXECUTION.md, REPRODUCTION.md, RESULTS.log and the immutable metadata/hash maps.
