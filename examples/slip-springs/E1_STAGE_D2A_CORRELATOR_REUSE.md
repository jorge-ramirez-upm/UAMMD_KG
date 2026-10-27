# D2A.0 — correlator inspection and reuse decision

Read-only inspection at `7ffbc4735bb0fb832025656fc9eb98cf5333ec59` on
27 October 2026. No tools for scientific execution were run. Paths below are
relative to `examples/slip-springs/` unless prefixed otherwise. Source line ranges
refer to this starting revision; KG and UAMMD remain read-only dependencies.

## Existing capabilities and actual source behavior

| Capability / inspected source | Reuse decision |
|---|---|
| `../KG/correlator.h:9–92,125–150`, `correlator.cpp:112–185,385–440` | Scalar and vector autocorrelations are available. Vector sums Cartesian dot products; neither computes displacements. Coarse levels use complete nonoverlapping **means**, not decimated coordinates. Reuse unchanged for their defined observables. |
| `../KG/correlator.h:237–251`, `correlator.cpp:902–960` | **DiffusionCorrelator already computes MSD directly**, summing squared coordinate differences. At each m samples it forwards the **last position**, not the mean. This is the preferred MSD engine; no position-correlation reconstruction is needed. |
| `../KG/correlator.h:392–435`, `correlator.cpp:1643–1729` | ChainCorrelator selects monomers and computes direct MSD with last-frame decimation, but retains full supplied chain arrays, has no analogous public raw-count interface, and needs separate ownership auditing. Eleven small Diffusion owners are a more focused reuse path. No chain-wide replacement correlator is proposed. |
| `orientation_correlator.h:13–70,73–85,113–229` | Validated CPU owner, robust normalization, rank-two features, clocks, counts and C1/C2 mathematics are reusable. Reuse unchanged, with a replica-aware caller. |
| `stream_correlator.h:15–25,28–89,100–146` | Reuse parameter validation and staged/noncopyable ownership pattern. The existing six-channel stress bank and its stress normalization are not a generic displacement/orientation bank. |
| `cpu_workers.h:76–152`, `semiflexible_stress_stream.h:39–70` | Persistent ranges and bounded producer/consumer transport are established patterns, but concrete `Bank&`/`Sample*` and six-channel types prevent drop-in reuse for new records. Start serial; a small separately reviewed typed adapter may later reuse this scheduling/lifetime design. Do not add a generic framework now. |
| `rouse.cuh:62–112`, `rouse.cu:181,190–232`, `validate.py:106–134` | Existing GPU Rouse observation includes double-reduced CM/end-to-end Cartesian vectors; its validation code computes direct-lag CM MSD and amplitude-sensitive vector correlations. Reuse the direct-reference definitions and coordinate-reduction/ID pattern; its Rouse timescale/target/tolerances are not E1 or nonlinear-backbone predictions. |
| `semiflexible.cu:359–360,363–440` | Current full-coordinate host readback computes CM MSD from initialization and all-bead mean displacement from initialization. This is fixed-origin information, not all-origin lag MSD. Its CM/local-origin summation is reusable as a formula, not a generic lag engine. |
| `semiflexible_stress.cuh:15–65` | GPU per-chain gather/reduction and compact sample infrastructure exists for stress; selected positions/CM need a small new read-only gather if later authorized. No existing integrated E1 orientation acquisition was found. Stress must remain off with E1. |

CrossCorrelator/CrossVectorCorrelator and anisotropic/R4/scattering utilities
also exist in KG, but add no requirement for the five observables. The repository
`test/BDHI/*/tools/msd.cpp` offline full-trajectory tools are not preferred:
they are not this streaming pipeline and introduce different parsing/storage
assumptions. The relevant reusable displacement implementation is KG Diffusion.

## Recommended small MSD adapter

Prepare a local noncopyable owner derived from DiffusionCorrelator, using the
same staged allocation/row cleanup pattern as `orientation::OwnedVector`.
KG's stock constructors/destructors do not provide that adapter's full
allocation-failure/lifetime guarantees (`correlator.cpp:22–71,354–374`). Keep
DiffusionCorrelator::add, Vector initialization and Correlator::evaluate unchanged.
The layout is the same Vector layout, but `OwnedVector::push` calls the
nonvirtual **Vector** add; wrapping it and expecting Diffusion dispatch would
silently compute the wrong observable. A distinct small owner is justified.

Add only finite-input, KG sentinel and clock/count checks plus output metadata.
The diffusion code regards x<=-1e10 as unpopulated; subtract one fixed initial
reference from each absolute series to reduce initial offsets, and reject an
unrepresentable/sentinel-overlapping sample explicitly. Never silently recenter
each frame or change stored origins during a run. Direct double differences
avoid subtracting two large squared moments, but cannot recover displacement
bits already lost in stored `real` coordinates. Overflow/count limits remain
explicit errors. No new precision representation is selected here.

## Exact multi-tau semantics to retain

Let F be the number of uniform frames, p slots, m coarsening, b=m^k at level k,
and delta=stride*dt. Level 0 exports ell=0,...,p-1 when populated; higher
exported levels use ell=p/m,...,p-1. Nominal lag is ell*b*delta and the valid
pair count is max(0,floor(F/b)-ell). Stock evaluate uses `k<kmax` for k>=1:
the deepest populated level is omitted, not silently repaired by a new adapter.
Do not promise all configured lags are exported. Incomplete final blocks are
not promoted. Physical times come from integer samples/steps, not delivery time.

**Diffusion:** the retained series is x_k(j)=x((j+1)*b-1). Its estimator is

    MSD_k(ell)=sum_(j=0)^(floor(F/b)-ell-1)
                 |x_k(j+ell)-x_k(j)|² / (floor(F/b)-ell).

It is a fine-position displacement at the stated lag with **decimated origin
support**, not an average over every fine origin. Report origin stride b, phase
b-1, actual count and point-sample width 1. `block_samples=b` here describes
promotion period, not a temporal average. At level zero it equals the direct
all-origin reference. For finite/nonstationary increments, higher levels need
not equal the full-origin curve; even for homogeneous increments their sample
estimates differ. Phase sensitivity belongs in future verification.

**Orientation:** u_k(j)=(1/b)*sum_(a=0)^(b-1)u(j*b+a), and likewise average the
instantaneously formed rank-two features t(u). KG returns dot products of
these block means, without renormalizing either means or features. Each block
pair averages b² original directional pairs with separations ell*b+(a'-a).
This is a triangular within-block lag mixture with support
[ell*b-(b-1),ell*b+(b-1)]*delta, not fine C1/C2 at exactly ell*b*delta.
Coarse lag-zero means would not in general be one; the exported fine zero is.
Report width b and block duration b*delta; never rescale coarse vectors to unit
norm to hide this averaging. Diffusion and orientation bins can have the same
nominal lag/count yet different support semantics.

## Why position-autocorrelation reconstruction is a fallback only

For any exact pair set O,

    mean_O |x_later-x_earlier|²
      =mean_O |x_later|²+mean_O |x_earlier|²
         -2*mean_O x_later dot x_earlier.

All three terms must use identical endpoints, origins, block transformations,
phase and count. Replacing them by 2*(global <x²>-C_x) is invalid for diffusing
nonstationary positions, and can suffer catastrophic cancellation even when
an endpoint-matched identity is used. Squared block means are not block means
of squared positions. For a deliberately block-averaged position MSD, compute
the squared difference of the actual two block means; this changes the observable
and must be labeled separately. Existing direct-difference Diffusion avoids
both reconstruction and that block-mean ambiguity, so no fallback is proposed.

## Orientation statistics and future deterministic checks

The historical [orientation report](STAGE4A3C_ORIENTATION_CORRELATOR_REPORT.md)
records bounded CPU validation, not integration into E1 or checks rerun here.
Bank computes SE across its input chains and labels them independent. For E1,
use one unchanged one-chain Bank per physical chain (SE absent), then reduce
chain estimates inside each replica and uncertainty across replicas externally.
Do not relabel its M-chain SE as replica uncertainty. Optional bare-chain
independence must be justified separately; the first implementation can use the
same replica-safe path for both models.

Future prescribed fixtures should compare against explicit direct sums on the
**actual** fine, decimated and block-mean supports: stationary point, straight
translation plus large fixed offset, periodic/deforming shapes, rigid translation,
rotating vectors with changing length, reversal/orthogonal directions, unequal
record lengths and incomplete blocks. Include m=2 and another supported m,
sentinel/clock failures, counts, repeated evaluation, lifetime and per-replica
symmetry reduction. These are test requirements only; no test code or run is
introduced in D2A.0.
