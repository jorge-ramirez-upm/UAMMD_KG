# C1 scientific results

## System/condition

These conclusions apply only to the current C1 associating-star condition:
1,000 stars, four stickers per star, and five independent 32M-step segments
(`dt=0.01`, 320,000 time units each). They are not universal across sticker
strengths or architectures.

## Static association/network

The transient network contains about 1,766 temporary bonds: 1,649 inter-star
and 118 intra-star. The intra-star fraction is 0.0665. Mean inter-bond degree
is 3.298 and mean distinct-neighbor degree is 3.212; 0.0045 of stars are
isolated. About 2.6% of connected star pairs have multiple simultaneous sticker
bonds. The largest simple-graph component contains 0.9947 of stars. This is a
dominant connected component, not demonstrated periodic-boundary percolation.

## Bond dynamics

Intra-star median lifetimes are about 690--700 and inter-star medians about
725--731; their `S=1/e` times are about 1,000 and 1,060, respectively. After
a break, about 53% of stickers rebind the same sticker pair, 2% bind another
sticker on the same prior-partner star, and about 45% bind a different star.
Median waits are 9 for same-pair rebinding and roughly 150--200 for changed
partners. Thus a sticker break often does not produce a persistent star-neighbor
rearrangement.

P4.6 neighbor gain/loss and multiplicity-only rates are whole-system event
counts divided by segment duration, not per-star or per-event rates. Neighbor
gains and losses are each about 1.8 per time unit; multiplicity-only inter-star
events are about 0.10 per time unit.

## Stress relaxation and viscosity

Five replicas show a last sustained nonzero `G(t)` region near
11,796--17,039, followed by sustained statistical compatibility with the
available noise floor by about 20,972. A later positive excursion is not
replica-robust. This does not assert that the modulus is mathematically zero.

The deliberately approximate C1 viscosity is `eta0 ~= 184.28`, with 95%
replica-CI half-width about 89.36 and cutoff sensitivity about 16.32. It is
adequate for approximate comparison, not a precision viscosity result.

## COM motion and self F_s(q,t)

The 32M COM segments remain subdiffusive: late local MSD slopes are about
0.63--0.86. Apparent `D` values around `2.6e-4--2.8e-4` are diagnostic only;
no terminal diffusion coefficient is claimed. At `q=0.1`, self `F_s` remains
about 0.514 at lag 281,600. Intermediate wave numbers relax on intermediate
scales, `q=1` on `O(10^3)`, and `q>=3.162` falls below 0.2 by the first useful
100-time-unit lag.

## Emerging timescale hierarchy

Approximate C1 scales are: same-pair rebinding `O(10)`, different-star
rebinding wait `O(10^2)`, bond lifetime `O(10^3)`, stress relaxation
`O(10^4)`, and large-scale COM translation `O(10^5+)`, with terminal diffusion
still unresolved.

## Open questions

Terminal diffusion, topology-defined walking versus hopping, the coupling of
neighbor exchange to displacement, PBC wrapping/percolation, and extension to
other association strengths remain open.

## Topology-defined walking and hopping

For C1, the corrected five-replica analysis used five equal 320000-time-unit
segments. Walking events occurred about 208 times more frequently than hops
(mean rates 3.64353375 and 0.017556875 per time unit, respectively; the
multiplicity-only rate was 0.197208125).

The primary mobility statistic is event-wise
`distance_squared / unconditional_MSD(replica, actual_total_lag)`, grouped by
requested half-window. For C1, walking mobility was essentially ordinary
matched-lag motion: 1.0025, 1.0035, 1.0069, and 1.0135 at half-windows 100,
200, 500, and 1000. Hop mobility was enhanced and increased across the same
windows: 1.1771, 1.2250, 1.3169, and 1.4095. Multiplicity-only enhancement
was modest: 1.0272, 1.0336, 1.0399, and 1.0525. Uncertainties are replica-level
95% Student-t half-widths, not event-count errors.

| requested half-window | multiplicity-only | walking | hopping |
| ---: | ---: | ---: | ---: |
| 100 | 1.027243 +/- 0.007115 | 1.002533 +/- 0.000893 | 1.177068 +/- 0.007022 |
| 200 | 1.033633 +/- 0.003583 | 1.003488 +/- 0.001036 | 1.225049 +/- 0.016282 |
| 500 | 1.039925 +/- 0.009491 | 1.006923 +/- 0.002094 | 1.316885 +/- 0.004794 |
| 1000 | 1.052454 +/- 0.005034 | 1.013542 +/- 0.002875 | 1.409472 +/- 0.008477 |

For C1, completed hop durations were broad: median 25.8 +/- 1.36, p75
123.35 +/- 3.05, p90 410.64 +/- 34.70, p95 913.82 +/- 139.93, and p99
3584.31 +/- 501.48 time units. Rare completed hops exceeded 1e5 time units in
one replica; the maximum is not treated as a characteristic timescale.

For C1, hops were enriched among large COM displacements, but walking still
provided most large-displacement events because walking was overwhelmingly
more frequent. These overlapping event windows are descriptive and do not
decompose the total diffusion coefficient. These conclusions are specific to
this C1 architecture, density, Ea, Ee, and production condition; other
systems are required before making cross-system mechanistic claims.

## P4.8a periodic wrapping

The periodic wrapping analyzer is implemented and its C1 production command
is documented, but the five-replica C1 wrapping analysis remains pending
offline. A giant component will not be interpreted as percolation without a
nonzero periodic winding vector.
