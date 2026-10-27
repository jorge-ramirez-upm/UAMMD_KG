# D2A.0 — focused implementation plan

Documentation only, 27 October 2026. Starting local/actual remote HEAD both
`7ffbc4735bb0fb832025656fc9eb98cf5333ec59`. No simulator changes, tests,
builds, analyses, benchmarks or GPU work are authorized by this plan.
D1.6 remains [closed with qualifications](E1_STAGE_D16_SCIENTIFIC_CLOSURE.md),
with equilibrium preservation not confirmed. This plan does not reopen it.

## Minimal next milestone: a CPU-only observable adapter

Recommend **D2A.1: standalone CPU estimator/ownership implementation**, after
independent review and explicit authorization. Its input is prescribed uniform
frames containing, per chain, CM plus r_0,r_8,r_16,r_24,r_32; it does not run the
simulator or consume the old scientific campaign as a test. Implement only:

1. A safe local owner around unchanged KG DiffusionCorrelator, preserving its
   direct differences, last-sample decimation and inherited export/count rules.
2. A small per-chain bundle: one CM MSD, five absolute MSDs, five internal MSDs,
   and an unchanged one-chain orientation::Bank for C1+C2. Derive rho_i and the
   end-to-end vector on the CPU from the six input vectors. Optional amplitude
   correlation can wait; it is explicitly different from directional C1.
3. Integer-clock validation, one fixed offset per absolute series, bounded
   allocation checks, and a small result writer carrying per-chain/per-replica
   curves, counts and precise lag semantics. Reduce symmetry/chain means within
   replicas before reporting replica uncertainty. Keep the accepted orientation
   header and its mathematical normalization unchanged.
4. Short prescribed-trajectory direct references and ownership/lifetime checks,
   prepared and executed only under that later milestone's explicit permission.
   No CUDA, simulator build, performance campaign or historical analysis is needed
   to establish this adapter's CPU correctness.

Use the [observable definitions](E1_STAGE_D2A_OBSERVABLES.md) and
[source/reuse assessment](E1_STAGE_D2A_CORRELATOR_REUSE.md) as the contract. Do
not create a generalized scheduler, new statistical framework, full-trajectory
archive, or alternative multi-tau algorithm. The missing adapter is ownership,
clock and reduction glue, not MSD arithmetic. No implementation is added now.

## Existing D1.6 data: what is and is not recoverable

The [frozen D1.6B protocol](E1_STAGE_D16B_PROTOCOL_V1.md), lines 43–78, and
`e1_equilibrium_observer.h:98–109,146–157` show the saved information:

| Existing output | Actual acquisition / content | Available for future authorized analysis |
|---|---|---|
| `samples.csv` | Regular scalar times 0,.5,...,100: CM squared displacement from initial CM, all-bead mean squared displacement from initial beads, E², Rg², bond statistics and spatial tangent summaries | Fixed-origin CM/all-bead displacement curves; cannot reconstruct CM vectors, selected-bead lag MSDs or directional C1/C2 |
| Full equilibrium frames | Regular times 0,2,...,100 plus five early diagnostics; sites, connectors, populations/events and supplemental backbone/tangent scalars | Occupancy/connector histories, not complete backbone coordinate or orientation histories |
| `equilibrium_positions.csv` / attachment audits | Full joint snapshots only at 0,.01,50,100 | Direct coordinate/orientation pairs at those saved times; only a tiny uniform subset 0,50,100, insufficient for a supported long-time multi-tau spectrum or diffusion fit |
| Initial/final positions | Endpoints of the run | One long displacement/orientation pair per chain; not a time-origin ensemble |

The .5 scalar and 2 full-frame spacings are **not** position sampling intervals.
Magnitudes E² do not supply directions; spatial tangent correlations are not
end-to-end temporal correlations. Connector vectors at occupied sites do not
recover missing arbitrary bead/anchor coordinates across renewals. Do not
interpolate positions or fabricate data from summaries. No T100 terminality or
new diffusion coefficient is inferred here. Historical bare-backbone outputs
must likewise be checked against their actual retained coordinate schedules;
identical scalar column names do not imply trajectory availability. In particular,
the original Rouse `samples.csv` does retain CM and end-to-end Cartesian vectors,
and `validate.py:106–134` already computes direct-lag CM displacement estimates.
Those records could support their vector observables after separate authorization,
but the Gaussian Rouse model is not the nonlinear Z=0 semiflexible control.

## Later read-only acquisition, separately authorized

First integrate the CPU consumer through a small observer using the existing
regular host position readback, if that cadence is sufficient for the reviewed
scientific question. This minimizes the integration change and provides a
reference for any later compact GPU gather, but **does not reduce the existing
full-coordinate D2H cost**. Keep measurement phase explicit: initial state,
otherwise after BD and the entire hopping/renewal batch, exactly as E1 observes
today. Validate chain IDs and uniform acquisition steps independently of file
dump cadence. Flush only actual complete frames; never add a synthetic final
frame to complete a block.

If later measurement shows full-coordinate readback dominates, add a separate
read-only per-chain GPU gather: sum all 33 bead coordinates in double using a
local reference for CM accuracy and retain only five selected bead vectors.
Computing CM needs all bead reads even though storage is selected-only. Transfer
six double 3-vectors per chain/frame (18 doubles); derive orientation and internal
coordinates on the CPU. This is a proposed observer, not reuse of a nonexistent
integrated orientation kernel. Preserve stable IDs, unwrapped coordinates,
precision disclosure and default-off trajectory identity. Do not enable the
stress/rheology observer to bypass E1's stress-off restriction.

Begin serial/synchronous with bounded batches. Existing stress GPU slabs, pinned
copies, event dependencies, backpressure and exclusive CPU chain ranges supply
a tested design for a later small typed transport adapter if profiling warrants
it; their current concrete types are not plug-compatible. The caller owns a
frame until copies and consumers finish; no concurrent mutation/evaluation of
a bank, buffer overwrite, dropped batch or hidden acquisition-clock change.
Drain/join before evaluation/destruction and propagate failures. No generic
worker refactor or asynchronous implementation is part of the first milestone.

## Memory and storage budget

With L levels and P slots, the existing Vector-layout payload on LP64 is
V=80*L*P+72*L bytes per owner, as documented and historically measured in the
[orientation report](STAGE4A3C_ORIENTATION_CORRELATOR_REPORT.md). A Diffusion
owner using that layout has the same payload; its new lifetime checks are still
pending. Eleven MSD owners plus three Vector owners for C1+C2 give **14 owners
per physical chain**, or approximately 14*M*V payload per replica. Add objects,
allocator overhead, pointers, reference offsets, output curves and temporary
construction storage. An optional raw end-to-end owner adds M*V. Choose the
smallest L,P covering the reviewed lag/cadence; historical 20-level orientation
settings are not a new default. Do not allocate all replica banks simultaneously
when sequential processing suffices.

A frame is 18*M*sizeof(double) packed data; a batch is B times that. Two slots
each with host and device storage require four such batch payloads, plus all
correlators and result storage. These are accounting formulas, not measured
new runtime/RSS budgets. Precheck integer/byte overflow and a user memory cap;
do not count workers as extra copies of the bank. Pair counters use the actual
platform unsigned-long limits, not assumed infinite 64-bit support.

Default output should be lag curves and support/clock metadata, with replica
identity, N, selected indices, parameters, dt, acquisition stride/phase, record
duration, per-bin lag, level, point/block width, promotion phase and raw counts.
Keep selected-coordinate dumps optional and bounded for verification. No
all-monomer trajectory is needed. This has O(M*L*P+B*M) retained acquisition
state independent of run duration, plus O(M*L*P) final curves if retained;
callers must not accumulate every intermediate result in memory. Disk scales
with curve size unless an explicit trajectory dump is requested.

Before performance claims, a separately authorized measurement must distinguish
GPU gather, synchronization, D2H, CPU consumption, waiting, output and total
wall cost; overlapping times cannot be added. No new overhead or throughput
claim is made here.

## Decisions reserved for review

Review the support semantics (decimated MSD versus block-mean orientation),
sentinel/large-coordinate limits, one-chain orientation-bank overhead, result
format and replica reduction. Scientific acquisition cadence, maximum lag,
independent replica count, record duration, fitting/support thresholds and
timestep comparisons require a later focused design, not an assumed T100
terminal window. No hardware memory availability was queried and no CPU/GPU
profiling ran. D2B's model-changing alternatives are recorded separately and
must not enter this observer implementation. Stop for independent review.
