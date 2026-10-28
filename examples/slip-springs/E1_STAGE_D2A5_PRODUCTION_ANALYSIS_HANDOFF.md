# D2A.5 scientific analysis handoff — future work only

This document prepares questions and evidence requirements, not an analyzer or
an acceptance result. No scientific reduction, fit, plot or hypothetical result
is generated during campaign preparation. Later analysis requires its own
authorization after authenticated completion evidence is returned.

First authenticate the frozen manifest, prerequisites, all24 receipts and raw
file inventories. Require complete physical/E1 and dynamics records and preserve
each seed/run/cell identity. Missing or failed runs remain missing or failed;
do not replace a replica, merge partial runs or turn a numerically finite output
into scientific acceptance. Existing D2A.3/D2A.4 analyzers retain their frozen N32
assumptions and must not be pointed directly at this evidence.

The principal questions are whether constrained CM MSD develops an extended
linear regime, whether selected monomers become diffusive, whether C1/C2
substantially decorrelate, how crossover windows differ between N32/N64/N128,
and how those patterns depend on kappa. Retain all A/B/C/D controls separately.
Use the original authenticated N32 campaigns as references with their own time
windows, grids, scalar schedules and replica uncertainties; do not imply an
identical-duration or identical-filter comparison by simply overlaying exports.

Treat each independently seeded whole run as the statistical replica. There
are only three replicas/cell, two degrees of freedom for a sample variance.
Compute means and across-replica uncertainty on common support, retaining the
individual curves. Canonical renewal can correlate chains within a run;
256 chains and overlapping time origins are not256 independent replicas or
independent error bars. Do not discard an inconvenient replica or select seeds
after observing curves.

The frozen primary rule is integer lag<=steps/5 and at least32 origins/chain.
Its last eligible lags are1966.08/7864.32 with49 origins/chain. The retained final
tails9175.04/36700.16 have only one origin/chain and are descriptive weak support.
Preserve actual integer counts, block widths and the primary mask; they are not
effective independent sample counts. Inspect consistency across replicas and
adjacent supported windows before drawing conclusions. Passing this support
rule proves neither stationarity nor completed relaxation.

CM/monomer curves are absolute unwrapped MSDs, using direct displacement and
last-position decimation, phase b-1. They are not internal MSDs. C1/C2 use fine
orientation features followed by block averaging; their coarse bins have a
triangular time-support filter and are not point samples at the nominal lag.
Do not combine the two filters or interpret a slope across a level boundary
without handling its support change. Incomplete blocks and omitted deepest
levels remain omitted; do not pad, interpolate missing bins as new evidence,
or rerun the correlator under a different estimator.

For future diffusion assessment, inspect supported windows of MSD/t and local
logarithmic slope, and test sensitivity to window boundaries and replica choice.
Use slope near1 only with a sufficiently extended, stable window and uncertainty;
do not force a reptation exponent or terminal fit. A bare-chain reference uses
6t/(N+1) for CM under these units, not a universal constrained-chain prediction.
For orientation, inspect sustained decay and tails with their finite support
and uncertainty; a sign change, isolated near-zero bin or weak-tail point does
not establish complete decorrelation. Lack of a supported terminal regime must
remain unresolved, even after the requested long physical horizon.

The1001 scalar frames/run and11 full E1 contexts support checks for slow drift,
bond/conformation changes, occupancy/population and hopping/renewal consistency.
Initial/final joint snapshots preserve serialization and structural context;
there is no full positional or scalar fine-time trajectory to reconstruct.
Keep scalar cadence differences from N32 explicit. Stability and reproducible
numerics alone do not resolve D1.6's qualified equilibrium-preservation status
or establish timestep accuracy, ergodicity, terminal rheology or quantitative
entanglement length. No stress/G(t), six-component rheology, new physical model
or force-distribution work is included in this campaign.
