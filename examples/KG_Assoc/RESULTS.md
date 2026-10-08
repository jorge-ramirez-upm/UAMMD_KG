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

The earlier P4.7 quantitative paragraph is withdrawn pending re-analysis. The
documented five-replica command accidentally mixed two short 10,000-time-unit
segments with three 32M segments, so those numbers are not a valid C1 ensemble
result. The corrected analyzer rejects such mixed-duration input.

The corrected C1 analysis will use requested half-windows as its primary
comparison and normalize each event by the unconditional MSD at its own
replica's actual snapped total lag. No corrected C1 conclusions are recorded
until the five true 32M replicas have been analyzed and inspected.
