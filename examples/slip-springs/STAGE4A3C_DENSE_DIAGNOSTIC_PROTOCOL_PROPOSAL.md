# Dense diagnostic protocol proposal: end-to-end orientation and GPU buffering

18 October 2026, Europe/Madrid. Design investigation at development commit
`2ec0076efd3dfdfc19e4d88b29d14a255ebeabf1`, in
`/tmp/UAMMD_KG-slip-springs-dev`. Both execution worktrees remain pinned at
`4e46d6014aa812b1fc687335654c4b1f681ddd22`. Only this document is added.
No correlator, kernel, simulator, benchmark executable, campaign, manifest or
existing result is changed. No GPU work or simulations were launched.

This supplements the [temporal-resolution audit](STAGE4A3C_TEMPORAL_RESOLUTION_AUDIT.md),
which proposes investigating stress cadence0.001/64 slots against dense0.0005
references. Orientation is a separate observable and acquisition clock; its
cadence cannot replace or repair stress temporal support. Nothing here freezes
an amendment or authorizes implementation/experiments.

**Recommendation:** reuse the stock numerical Vector correlator with local safe
ownership, feed normalized vectors for C1 and tensor features for C2, and retain
one correlator result per independent chain. First benchmark reuse of already-
available host coordinates and simple transfers. If independent endpoint-only
acquisition is needed and transfer latency is material, evaluate a bounded GPU
slab, initially flushed every10000 integration steps. Adopt asynchronous double
buffering only after it beats the simpler same-cadence alternatives.

## 1. Verified stock utility and scientific contractions

Read-only sources: [correlator.h](../KG/correlator.h), `VectorCorrelator`;
[correlator.cpp](../KG/correlator.cpp), `VectorCorrelator::setsize`, `initialize`,
`add`, destructors and `Correlator::evaluate`. Inspected source SHA256s:

* Header: `1ce5842bc5557879e5beb0f9b6d0144bf616258bd7bae3d5092719719f084e4d`.
* Implementation: `84ca3742820824d9e093c8f62b6f408e2e42017d5a7539f5cbf76e4f81fff9c0`.

The CPU utility accepts three **double** components, stores their histories,
accumulates the dot product for each valid origin, and divides by its origin
count at evaluation. It has no GPU implementation, vector normalization,
Legendre transform, empirical mean subtraction or uncertainty estimator.

For chain c define R_c=r_(cM+N)-r_(cM), u_c=R_c/|R_c|, using fixed endpoint labels.
Then C1(t)=<u(t) dot u(0)> and C2(t)=<P2(u(t) dot u(0))>, P2(x)=(3x²-1)/2.
Passing u to VectorCorrelator computes C1 directly at fine lags. Passing R
instead gives length-weighted <R(t) dot R(0)>; dividing that by <R²> does not
recover unit-vector C1 for fluctuating lengths.

The stock Vector correlator cannot compute C2 directly from its three u inputs.
In particular, C2 is not P2(C1): the average of a squared dot product is required,
not the square of its average. Use the five-component feature

\[
 f(u)=\left(\sqrt3u_xu_y,\sqrt3u_xu_z,\sqrt3u_yu_z,
 \frac{\sqrt3}{2}(u_x^2-u_y^2),\frac{3u_z^2-1}{2}\right).
\]

For unit u,v, f(u) dot f(v)=P2(u dot v), and |f(u)|²=1. Two existing Vector
instances, receiving(f1,f2,f3) and(f4,f5,0), yield C2 by adding their per-chain
outputs. Together with C1 this uses three Vector instances per chain. A checked
alternative is the existing Correlator6 with the six components of
sqrt(3/2)*(uu-I/3), weighting off-diagonals by sqrt2; sum its six autocorrelations
with unit weights. Do not apply the stress pipeline's1/5 and1/30 factors.
The six-channel alternative can reuse its validated ownership mechanism but
needs separate orientation aggregation and generally more memory.

At coarse levels the utility first averages **input components** into complete
nonoverlapping blocks. Thus its output is a block-averaged C1 or, if f is formed
before coarsening, a block-averaged C2. Never normalize averaged u blocks, form
f from an averaged u, or square a block-averaged C1. These are different
estimators. Coarse results are not point-sampled Legendre curves at the nominal
lag. Incomplete final coarse blocks are truncated; `evaluate()` omits the
deepest populated level, just as in the existing stress definitions.

Unit-vector input makes fine C1(0)=C2(0)=1 without a fitted normalization.
Coarse block norms need not be1. Preserve raw orientational correlations:
anisotropic stationary ensembles can have genuine nonzero plateaus. Do not
subtract a trajectory mean or force late-time values to zero. For an ideal rigid
rotational diffuser C1=exp(-2*D_r*t), C2=exp(-6*D_r*t); that useful controlled
reference is not an assumed relation for flexible-chain end-to-end motion.

**Ownership caveat:** stock destructors free pointer tables but not their
allocated per-level rows. Copying its owning objects is unsafe, its base
destructor is nonvirtual, construction does not initialize histories, and
allocation failure cleanup is incomplete. A future local noncopyable concrete
owner must stage allocations, initialize explicitly and free rows exactly once,
following [OwnedCorrelator6](stream_correlator.h)'s existing pattern. No KG or
Rouse edit is needed. The add/evaluate mathematics should remain the stock code;
its numerical and lifetime tests remain prerequisites, not claims made here.
The stock sentinel checks only the first component. Unit vectors/tensor features
stay safely above its-1e10 cutoff, but local input finiteness checks are still
required before every push; a NaN must not masquerade as an unused sample.

## 2. Acquisition clock and normalization domain

Use exact integer schedules n=k*s, including step0; physical spacing Delta=s*dt.
Do not use wall time, transfer completion time or accumulated floating-point
time to select samples. Normalize each instantaneous R, not an ensemble average.
R=0 or nonfinite R makes orientation undefined even if all physical bonds are
valid. Flag the frame/chain and invalidate the observable evidence; do not clamp
its denominator, drop the row and compress the clock, or change the dynamics.
Very small R is ill-conditioned; report its minimum and precision sensitivity
without introducing an arbitrary scientific cutoff. Long-time end-to-end
orientation need not share stress's e-fold time.

| dt | Every10 steps | Every100 steps | Strides for Delta0.01 /0.02 /0.05 |
|---:|---:|---:|---|
| 0.0001 | 0.001 | 0.01 | 100 /200 /500 |
| 0.00005 | 0.0005 | 0.005 | 200 /400 /1000 |
| 0.000025 | 0.00025 | 0.0025 | 400 /800 /2000 |

“Every100 steps” is therefore not a fixed-physical-cadence timestep comparison.
Start the orientation resolution study with Delta0.01, compare0.02 and0.05 by
instantaneous decimation of a denser shared history, and use10/100-step variants
to expose early motion and acquisition cost. Adequacy of any interval is
unverified: C2 can relax faster than C1, and small-|R| chains can reorient rapidly.
Do not infer an orientation cadence from the stored total-stress curves alone.

## 3. GPU endpoint gather and batch protocol

A future read-only gather has one thread per chain, loads only its two endpoint
real4 coordinates, casts to double before subtracting and stores a packed
double3 R in frame-major, chain-contiguous order. This is O(C), independent of
N, with no atomics except an optional deterministic invalidity record. It reads
2*C*sizeof(real4) logical GPU bytes and writes24*C bytes per frame. Strided
endpoint addresses can cause additional memory transactions; measure actual
device bandwidth rather than assuming all logical reads are coalesced.

CPU double normalization of R and generation of f(u) keeps GPU work small and
allows both ranks from the same24-byte record. GPU normalization is an option
to benchmark, not necessary. Extra tensor features need not cross PCIe. Double
subtraction does not recover precision already lost in stored float coordinates;
test large translations and near-zero R in both precisions.

Let H=10000 integration steps be the initial **flush interval**, not the sample
stride. Every scheduled vector is stored until its slab is transferred, not
until the end of production. Allocate capacity ceil(H/s)+1 frames to handle
step0 and nondivisible schedules. Batch0 includes step0 and scheduled steps up
to H; subsequent batches contain(qH,(q+1)H], with no duplicate boundary. Flush
the last partial slab and every complete scheduled frame at finalization, but
do not invent a final off-grid observation. For s800, batches alternate12/13
steady frames; a constant assumed count would lose data.

The same10000-step flush spans physical time1.0/0.5/0.25 across the three dt.
This changes observation delivery latency, not physical sample times or lag
spacing. Record batch IDs, first global frame index, frame count, integer sample
steps, chain count/order, schema, precision and checksum. Validate total
F=floor(S/s)+1 and contiguous frame IDs; expected lag is ell*s*dt and origins
floor(F/B)-ell/B. Persist block width and origins alongside chain mean/SE.

For asynchronous operation, propose two independently owned GPU slabs and two
pinned host slabs. Enqueue the endpoint gather **on the integration stream**
after the scheduled update and before that coordinate buffer can be reused.
Reading live coordinates on another stream without such protection is unsafe.
When a slab closes, record a ready event; a nonblocking transfer stream waits
on that event, copies the contiguous slab, and records copy completion. CPU
workers wait for completion off the integration thread, consume chains in fixed
ranges, and release the host slab. Reuse GPU memory only after its copy is done,
and host memory only after its consumer is done. A coupled two-slot lifecycle
is the simplest bounded design; decoupled GPU/host rings are an unneeded next
optimization until profiling justifies them.

The [existing Rouse pipeline](stream_pipeline.cuh) already demonstrates ready/
copy-complete events, pinned double buffers, backpressure and joined consumers.
Its kernel, Sample6 format and Bank/CpuWorkers types are stress-specific; it
cannot simply be instantiated for VectorCorrelator. Reuse those ownership and
queue patterns in an isolated orientation adapter, not a fork of correlator
mathematics or a change to Rouse. [CpuWorkers](cpu_workers.h) is currently typed
to the stress bank; any later shared refactoring needs separate authorization
and proof of unchanged Rouse behavior.

No orientation host wait is required on ordinary integration steps, or on each
sample while a free slab exists. There is still a gather launch at each sample
and possible backpressure at slab reuse. Never overwrite a busy slab, drop a
frame, or assume two buffers can absorb sustained CPU overload. Device-invalidity
flags can be read with closed batches, avoiding an added per-sample diagnostic
D2H; the diagnostic delay must be explicit. They cannot silently validate an
undefined orientation or alter force/RNG behavior.

CUDA overlap requires suitable device capability, pinned host memory and correct
stream/event dependencies; asynchronous APIs alone do not guarantee overlap.
Query copy-engine capabilities and verify a trace. Legacy default-stream rules
and the semiflexible simulator's existing synchronous diagnostic/readback calls
can limit realized overlap. This design does not remove those calls or promise
fully asynchronous integration. See NVIDIA's [CUDA13 guide, asynchronous concurrent
execution](https://docs.nvidia.com/cuda/archive/13.0.0/cuda-c-programming-guide/index.html#asynchronous-concurrent-execution).

## 4. Quantitative transfer and allocation comparison

Example C2048: one packed float3 frame is24KiB; packed double3 is48KiB.
Using float4/double4 instead raises these to32/64KiB; padding is not free.
Recommend24-byte double records in both coordinate precisions initially, with
CPU correlator storage always double. Float transport is an explicitly tested
optional optimization, halving payload but not copy-call latency.

For a standalone endpoint measurement, full-position readback would be288KiB
(N8,float),1056KiB(N32,float),576KiB(N8,double),2112KiB(N32,double).
The double3 gather reduces that PCIe volume by6/22/12/44 times, respectively.
However, if the stress/scalar pipeline **already copied those coordinates at
the exact orientation time**, calculating R from that host frame adds **zero**
PCIe bytes or GPU launches. This reuse baseline may beat any new GPU pipeline.
It couples availability to existing observation times and does not provide
independent dense orientation sampling. Do not claim existing stress readbacks
disappear when adding endpoint-only observations.

The following totals assume T200,dt0.000025,C2048,double3; main T4000 totals at
fixed physical cadence are approximately20 times larger. All mechanisms that
transfer the same vector records have the same payload, excluding tiny headers.

| Schedule | Frames | Vector D2H GB | Per-frame copies |10000-step slab copies | Steady frames/slab |
|---|---:|---:|---:|---:|---:|
| Every10 steps, Delta0.00025 | 800001 | 39.32165 | 800001 | 800 | 1000 |
| Every100 steps, Delta0.0025 | 80001 | 3.93221 | 80001 | 800 | 100 |
| Delta0.01 | 20001 | 0.98309 | 20001 | 800 | 25 |
| Delta0.02 | 10001 | 0.49157 | 10001 | 800 | 12/13 |
| Delta0.05 | 4001 | 0.19666 | 4001 | 800 | 5 |

Steady one-slab double storage is46.875MiB at10 steps,4.6875MiB at100 steps.
The two GPU slabs therefore take93.75/9.375MiB, and pinned host slabs take the
same again; allow one extra48KiB frame per slab. For fixed Delta0.01 at finest
dt, guarded two-slab GPU storage is2.4375MiB and pinned storage the same.
All scale linearly with C and H/s, not production duration. Pinned allocations
need explicit caps; unconstrained page locking is not a resource strategy.

| Mechanism | PCIe calls | CPU dispatch | Main limitations |
|---|---|---|---|
| Reuse coincident host positions | None added | Per frame or host batch | Not independent of existing readbacks |
| Direct vector D2H and immediate consume | F | F | Simplest reference; copy latency and frequent barriers |
| Per-frame D2H into pinned host batch | F | About S/H | Saves CPU dispatch, not PCIe calls; device-output overwrite needs ordering |
| GPU slab, synchronous batch copy/consume | About S/H | About S/H | Simple bounded option; pauses at flush boundaries |
| GPU slabs, async copy/worker consumer | About S/H | About S/H | Potential overlap; larger memory and lifecycle complexity |

Model transfer time as calls*L+bytes/bandwidth. GPU batching cuts the latency
term and boundary waits, not vector PCIe volume or gather-launch count. As an
**illustration only**, L5–20microseconds gives approximately4–16s less call
latency for the10-step example and0.096–0.384s for Delta0.01. At an assumed
12GB/s the respective payload terms are3.28s and0.082s for either mechanism.
These are not measured RTX3060Ti rates. Host batching alone cannot obtain those
PCIe-call savings; asynchronous direct copies may overlap some waits but still
issue F calls. GPU buffering will not cure a CPU correlation bottleneck.

## 5. Correlator memory, throughput and independent-chain statistics

On LP64 (8-byte double/pointer/unsigned long,4-byte unsigned int), Vector's
allocated array payload is

    per chain =80*L*P +72*L bytes, plus object/malloc overhead.

This counts three shift rows, one dot-product accumulator row and origin-count
row per level, four flattened double outputs and flattened counts, five pointer
tables, three level accumulators and two cursor arrays. It is independent of
trajectory length. At L20,C2048:

| Slots | One Vector bank | C1 plus two Vector banks for C2 |
|---:|---:|---:|
| 32 | 102.8125MiB | 308.4375MiB |
| 64 | 202.8125MiB | 608.4375MiB |

Add slab memory, worker stacks and the existing stress bank; do not silently
reuse its512MiB budget. Stock allocations involve many small rows: about115
allocations/object at L20, before any local owner bookkeeping. Measure actual
RSS, allocation time and teardown; staged ownership or a later proven local
allocation layout can avoid leaks without changing KG. Never delete through
the nonvirtual base or copy/move raw owning correlators.

Per-frame work scales approximately as C*P with amortized coarser levels. C1
requires three component products per pair; the two Vector C2 banks add six,
including a zero component. Feature generation is O(C) per frame. Real CPU
throughput, normalization cost, cache effects and useful worker counts are
unknown. All CPU correlations remain double in either CUDA precision.

For context only, the recorded N8,kappa10 stress pilot processed40,962,048
chain-frames in15.139s CPU bank wall time:2.71million/s. Its integration cost
was0.358s per10000 steps. Orientation every10/100 steps would require about
5.72/0.572million chain-vectors/s to keep pace with that integration, even
before CPU contention with stress. Scaling stress's six scalar products to
nine orientation component products suggests about1.8million/s, an **unverified
operation-count estimate**. It suggests10-step acquisition could become CPU-
bound; it does not justify thinning observations to report faster performance.
Double-precision integration and other N/chain counts need their own timings.

Own correlators per chain, with fixed contiguous worker ranges and exclusive
ownership. Form each chain's C2 as the sum of its two banks **before** computing
SE across chains, retaining their covariance. For lag estimator q_c, report
mean(q_c),sd(q_c,ddof1)/sqrt(C). Never pool chains into one input stream, treat
overlapping origins as independent chains, or combine rank/bank SE in quadrature.
Track origins separately from measurement frames and independent chain count.
Ratios or fitted times need paired-chain uncertainty, not pointwise SE alone.

## 6. Proposed bounded benchmark gates — not executed

Authorize implementation and benchmarks separately. No timing claim follows
from this design. Keep each phase timeout-bounded (CPU120s,GPU correctness120s,
transfer90s,integration replay120s); stop rather than silently enlarging work.
Reduce performance matrix breadth, not correctness thresholds, if limits bind.

**CPU numerical/lifetime phase:** deterministic unit vectors with constant,
alternating sign and orthogonal/periodic patterns; independent isotropic and
anisotropic sequences;17/31/65-frame tails and repeated evaluate/clear cycles.
Directly compute every exported point/block dot product and average P2 pairwise.
Check unit zero lag, antiparallel C1=-1/C2=1, orthogonal C1=0/C2=-1/2,
normalization, counts, incomplete blocks and deepest-level omission. Different
workers/batches must match deterministic chain-order results. Use absolute+
relative3e-11 against direct double reductions and lifetime/ASan/UBSan/LSan.
Measure C1 alone and C1+C2 throughput separately; include feature conversion.

**GPU prescribed-coordinate phase:** N1,2,8,32;C1,3,64,2048; translations,
rotations, end-label reversal, nonfinite/zero/near-zero R; both precisions. Check
double endpoint subtraction/CPU features against stored coordinates with a
scale-aware32*epsilon_double*max(1,endpoint magnitude) arithmetic allowance and
explicit orientation conditioning: |delta-u| scales as |delta-R|/|R|. Do not
weaken near-zero checks by a universal large angular tolerance. If float
transport is evaluated, propagate its epsilon and near-zero error separately.
Check step counts0,9999,10000,10001,20037, including s800's nondivisible batches,
step0, partial slabs and artificially delayed consumers. Race/memcheck must
exercise both buffers and failure cleanup. No source/core modification needed.

**Transfer/throughput phase:** fixed already-prescribed endpoint arrays, no long
Brownian run. Screen C64/2048,N8/32,both precisions,10/100-step-equivalent
records and Delta0.01/0.02/0.05 schedules. Compare all five mechanisms above;
measure bytes/calls, kernel launch/gather time, memcpy duration, host wait,
CPU wall/worker sums, queue occupancy and memory. Include synchronous GPU slabs
before asynchronous ones, and H1000/10000/50000 only if memory bounds allow.
Initial GPU and pinned slab caps512MiB each; preflight each allocation instead
of constructing an excessive bank. CPU bank cap1GiB for this bounded benchmark.
Apply that cap to combined live banks, including stress. Screen out excessive
performance cases before allocation; a larger combined benchmark needs an
explicit resource budget rather than an implicit increase.
Five interleaved repetitions after warm-up; report median/spread and paired
wall-time differences, not one noisy timing. Expand only useful cases on host.
Record GPU/driver/runtime, actual build transcript and executable hashes, CPU
affinity/worker counts, stream mode and device copy-engine capabilities. Keep
profiler traces separate from unprofiled timing repetitions.

**Dynamics replay phase:** later authorized short fixtures with unchanged EM,
seed,dt,initial state and step count, orientation off/direct/slab/async; stress
off/on. Verify exact coordinate-prefix replay under the existing precision
contract, unchanged forces/RNG counters, stress channels and correlations.
Use tiny per-step prefixes and bounded10000-step boundary fixtures; do not run
production. Trace events to show no new per-step host synchronization from
orientation and identify existing synchronization separately. Sampling/readback
and final drain/output costs must be included in overall wall time; keep GPU
integration ns/bead/step separate and do not add overlapping timers.

Proposed engineering adoption rule: after correctness/lifetime/replay pass,
retain the simplest mechanism unless GPU slabs reduce **overall** wall time
by at least10% with a positive paired95% interval versus the best feasible
same-cadence baseline, within declared memory limits and without sustained queue
growth. Async must separately beat synchronous slabs enough to justify its
complexity. This is a prospective benchmark decision rule, not a changed frozen
scientific gate. Otherwise retain direct/reused-host acquisition. Never compare
different sampling frequencies as if they established buffering speedup.

## 7. Dense orientation diagnostics before selecting a protocol

For a later authorized initial screen, one finest-dt seed,C128,T2,N8/N32,
kappa0/2/10 with10-step orientation acquisition is a candidate:8001 frames,
about24.6MB raw double R/model, bounded independently of the long campaign.
Use its instantaneous10-step history to compare100-step and fixed0.01/0.02/
0.05 schedules with paired-chain errors and exact common physical lags. T2
does not guarantee a C1/C2 crossing, especially N32; unresolved slow support
requires separately reviewed longer evidence, not assigning a Gaussian/rod
spectrum. Include independent-seed/precision confirmation before generalizing.

Freeze cadence and statistical resolution gates before those diagnostics; do
not choose them post hoc to make0.05 pass. Preserve the stress acquisition
proposal independently. Any new orientation data/schema, auxiliary memory,
clock, lag grid and executable identity belong in a separately authenticated
prospective protocol, never retroactively in the frozen282-run campaign.

Checks actually performed here were source inspection, memory/transfer arithmetic
and pure NumPy feature identities:24 deterministic unit-vector pairs gave a
maximum P2 contraction error3.89e-16; four complete-block direct P2 sums agreed
within1.12e-16. The stock Vector numerical/lifetime suite, GPU integration,
throughput, overlap and proposed scientific diagnostics remain **unexecuted**.
