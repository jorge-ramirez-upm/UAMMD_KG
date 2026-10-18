# KremerGrest buffering reuse audit

18 October 2026, Europe/Madrid. Documentation-only inspection; no compilation,
benchmark, GPU work, simulation, analyzer execution or campaign modification.

**Recommendation:** reuse the asynchronous transport/lifecycle pattern already
inside slip-springs, retaining its existing stress bank and workers. Do not copy
the KG driver or stress reducer. A short architecture review and bounded
throughput benchmark are needed before implementation approval: every-step
acquisition is feasible with bounded storage, but the measured CPU correlation
rate does not support an assumption that it can keep up with integration.
Backpressure must slow production rather than lose samples.

## Provenance and inspected sources

The development worktree `/tmp/UAMMD_KG-slip-springs-dev` was clean on local and
fetched `origin/slip-springs` at
`f11cb748967dc4235abd2eee57ced70b1c8836f9`. Fetching both branches resolved
`origin/KremerGrest` to **`ceb4048a00897b8c335d718d885f9e14ac2c37e7`**.
The local `KremerGrest` branch remains at `81fe5de9...`; it is not the current
remote reference. The audit reads committed remote blobs with `git show` and
`git grep`, without checkout, merge or changes to KG's working files.

Exact source locations, relative to the repository root:

| Branch | Files and functions inspected | Purpose |
|---|---|---|
| KremerGrest, SHA above | `examples/KG/kg_uammd.cu`: `main`, `queueStressSample`, `flushBufferedStressSamples` (roughly lines168–333) | Original KG batching and output |
| KremerGrest | `examples/KG/kg_runtime.cuh`: `detail::StressTensorSample`, `computeStressTensorContribution`, `reduceStressTensorParticlesKernel`, `reduceStressTensorPartialsKernel`, both `appendStressTensorSampleAsync` overloads (lines305–692) | GPU reduction and actual stress convention |
| KremerGrest | `examples/KG/kg_interactors.cuh`: WCA/FENE `sum`, cached stress getters | Producers of per-particle force/stress caches |
| KremerGrest | `examples/KG_Assoc/kg_assoc_production.cu`: `flushStressSamples`, `queueCachedStressSample`, `refreshAssociatingStressAfterChemistry`, production loop and modulus writer (lines1046–1290) | Current every-step buffering consumer |
| Both | `examples/KG/correlator.h`, `correlator.cpp`: `Correlator6::add/evaluate`, `VectorCorrelator`, base ownership/export | Identical committed files: branch comparison produced no diff |
| KremerGrest | `examples/KG_Assoc/kg_assoc_stress_test.cu`, `kg_correlator6_counts_test.cpp`, `kg_assoc_correlator_checkpoint.cuh`, `kg_assoc_correlator_checkpoint_test.cpp`, `VALIDATION.md` | Existing tests; retained checkpoint utility is unused by production |
| slip-springs, f11cb748 | `examples/slip-springs/stream_pipeline.cuh`: `Pipeline::sample/submit/process/consume/finish`, destructor, `Slot` | Existing asynchronous Rouse transport |
| slip-springs | `stream_correlator.h`: `OwnedCorrelator6`, `Bank::consumeRange/write`, `Moments`; `cpu_workers.h`: `CpuWorkers::consume` and fixed-range workers | Safe ownership, unchanged KG estimator, chain uncertainty |
| slip-springs | `semiflexible_stress.cuh`: `stretchTensor/bendTensor/channels`, `Observer::sample/failure/finish`; `semiflexible_stress_stream.h`: `Correlations::received/consume/write` | Current complete virial and synchronous observation path |
| slip-springs | `semiflexible.cu`: `observe`, integration loop; `orientation_correlator.h`: `OwnedVector`, `Bank::observe/evaluate` | Acquisition clocks and validated CPU orientation adapter |
| slip-springs | `tests/semiflexible_stress_analysis.py`: `lag_grid/terminal`; frozen `STAGE4A3C_VALIDATION_PLAN.md`; prior temporal/orientation reports | Physical support requirements and existing measurements |

The original execution checkout remains clean and pinned to
`4e46d6014aa812b1fc687335654c4b1f681ddd22`. The compact campaign directory exists
locally; no new analysis of its trajectories is claimed here. Measurements below
are explicitly taken from the committed temporal-resolution and orientation
reports, not new experiments. The frozen plan SHA-256 remains
`efd040ceba8cd903dee7a145296dce08435e3df3efa940c65170f4bcf98acb36`.

## What KremerGrest actually does

The data path is:

1. WCA/FENE interactors populate device per-particle diagonal/off-diagonal stress
   caches during force evaluation. KG_Assoc additionally refreshes the temporary
   bond cache after chemistry, before observing that changed state.
2. `appendStressTensorSampleAsync` launches a 256-thread particle reduction and
   a second partial-sum reduction on `integrator->getStream()`. The result is one
   six-double tensor, `xx,yy,zz,xy,xz,yz`, appended to a device slab. This is a
   spatial reduction of an instantaneous frame, not a temporal average.
3. The integrator and reductions share a stream, ordering cache reads before
   subsequent updates. Partial-sum scratch is safely reused in that order.
4. Flushing explicitly calls `cudaStreamSynchronize(samplingStream)`, then
   blocking `cudaMemcpy` to an ordinary `std::vector` host slab. The caller feeds
   every copied record, in order, to one CPU `Correlator6::add`.
5. Final flushing copies the actual remaining count; evaluation and correlation
   output follow. Incomplete multi-tau blocks are not padded.

Despite the helper's `Async` name, there is **no pinned host allocation,
`cudaMemcpyAsync`, transfer stream/event handoff, double buffering or persistent
CPU worker pool in these KG/KG_Assoc paths**. Asynchronous kernel submission
allows accumulation between flushes; it does not establish overlap between host
correlation and GPU integration. The caller stops at a flush until transfer and
CPU consumption finish. This provides synchronous backpressure and prevents
slab overwrite. `thrust::device_vector` and host vectors own the buffers; their
lexical lifetimes extend through final flush. CUDA calls use checked error paths;
there is no queued consumer thread to drain.

Capacity and clocks differ:

- Original `kg_uammd.cu`: capacity `ceil(restartEvery/ncorr)+2` when restart output
  is enabled, otherwise65,536 tensors. Flush on capacity, restart, or completion.
  Step0 is included, subsequent samples only at multiples of `ncorr`. Every-step
  acquisition therefore requires `ncorr=1`; it is not unconditional.
- KG_Assoc production: fixed4,096 tensors,192KiB per host/device slab, independent
  of total steps. Flush before appending to a full slab and at completion.
  Every production integration step queues one sample unless topology-only;
  output explicitly records `step0_sampled=no`, `stress_interval_steps=1`.
- These are different initial-frame conventions. Semiflexible acquisition must
  retain its own step0 and all S subsequent steps: **S+1 frames**, not copy the
  KG_Assoc omission.

Every queued frame reaches `add`. Temporal coarse-graining occurs **inside**
the correlator: each m consecutive inputs forms a nonoverlapping arithmetic
block mean passed to the next level. Fine-level correlations still consume all
instantaneous samples. Coarse blocks are not unit-normalized, independently
thinned samples, or an acquisition filter. `evaluate` omits the deepest populated
level, as in the existing slip-springs estimator.

### Physics and statistical differences that forbid direct reducer reuse

KG computes a whole-system, volume-normalized tensor including kinetic stress,
WCA and FENE contributions, with cache-specific signs and half factors. KG_Assoc
adds temporary-FENE stress. One six-channel correlator follows the global sum;
there are no independent-chain banks, chain-cluster errors or per-chain outputs
in this path. Channels are raw shears and normal differences. KG_Assoc exports
pair counts and the1/5,1/30 isotropic combination with volume/temperature factors;
original KG exports the six volume-scaled correlations. Neither supplies the
semiflexible independent-chain uncertainty estimator.

Semiflexible needs unnormalized configurational **per-chain** complete virials,
including stretch–bend cross terms, no kinetic/WCA/FENE substitution, and explicit
chain density. Its existing `Correlations::write` already provides
`H`, `g=H/(kBT)^2`, and optionally `G=n_chain*H/kBT`. Preserve this implementation.
The shared KG stock destructors omit allocated per-level rows; reuse the local
safe owners rather than instantiate thousands of stock owners directly.

## Functionality already present locally

| Requirement | Existing reusable component | Remaining adaptation |
|---|---|---|
| Correct heterogeneous complete virial | `stress3b::stretchTensor/bendTensor/channels` | Write each scheduled channel frame to a slab offset; preserve kernels' mathematics and zero-bend path |
| Bounded asynchronous transport | Rouse `streaming::Pipeline` slot/event/consumer pattern | Local semiflexible transport using its producer and diagnostics; current class is hardwired to Rouse stress |
| Persistent chain-parallel correlation | `streaming::Bank`, `CpuWorkers` already used by semiflexible | Feed completed slabs to the same objects; no new estimator or worker algorithm |
| Safe KG ownership and chain SE | `OwnedCorrelator6`, `Bank::write` | Preserve unchanged; combine H within chain before SE |
| Stress moments and optional dumps | `stress3b::Correlations::received` | Process every frame on the consumer with its original integer step, in order |
| Orientation C1/C2 | `orientation::Bank`, `OwnedVector` | GPU endpoint producer and independent clock/transport; CPU bank currently serial and not compatible with typed stress workers |

Rouse `Pipeline` has one slot in synchronous mode, two in asynchronous mode.
Each owns a device slab and pinned host slab. `sample` writes frames in order;
`submit` records producer-ready, makes the nonblocking transfer stream wait on
that event, issues one contiguous `cudaMemcpyAsync`, and records copy-done.
The persistent consumer waits for copy-done, invokes the fixed-range CPU pool,
then marks the slot free. A condition variable blocks the producer when both
slots are occupied. It does not drop/overwrite frames. `finish` submits a final
partial slab and joins; failures propagate and teardown joins/drains before
freeing CUDA/pinned resources. Per-frame start/stop events currently measure
sampling time. Event counts and overhead grow with batch capacity.

The semiflexible observer already shares **the same bank and workers**, but its
transport is different: one device frame, per-sample event synchronization,
synchronous error-key readback and D2H into a pinned CPU batch. Host batches are
consumed synchronously from the producer. Thus changing only `--stress-batch`
does not introduce GPU batching or overlap.

Furthermore `semiflexible.cu::observe` currently couples stress to full-coordinate
D2H, scalar reductions, bond histograms and compact/full output handling.
Simply setting the existing sample stride to1 also evaluates/transfers all these
scalars every step. Compact serialization does not remove that work. A new stress
clock must be independent of the existing scalar clock, with explicit metadata
and reviewed scientific coverage; legacy full/compact and Stage4A.2 behavior must
remain available. Force/update diagnostics already synchronize independently:
buffering alone will not make this an asynchronous integrator.

## Every-step lag grid: acquisition is not a flush policy

Let acquisition spacing Delta=dt, F=S+1, m=2, slots P, levels L. Level k has
block width B=2^k and physical width B*dt. Fine lags are j=0..P-1; coarse
lags j=P/2..P-1 have physical lag j*B*dt and origin count floor(F/B)-j when
positive. Only complete blocks contribute; the deepest populated level is
omitted. Frame delivery/batch size must not affect these definitions.

The frozen `terminal()` requires at least16 origins per chain and B*dt<=tau_e/4,
a supported bin reaching2*tau_e with positive signal>3SE, and a supported bin
strictly beyond4*tau_e satisfying |H|/H0<=0.1+6SE/H0. Every-step sampling removes
the old Delta0.01 obstruction for N8 kappa0, but does **not** guarantee the late
criterion. Source-level enumeration with the unchanged `lag_grid` gives:

| N8 empirical tau used only as planning input | Maximum eligible lag, P32 | Maximum eligible lag, P64 |
|---|---:|---:|
| kappa0,0.0224778885 |0.0992|0.2016|
| kappa10 pilot,0.1005591501 |0.3968|0.8064|

These values hold at each proposed dt=0.0001,0.00005,0.000025, since the timesteps
are dyadically related. Existing kappa0 tail evidence first meets the amplitude
gate near0.15; the kappa10 pilot meets it around0.5. P32 is therefore a poor
choice even with every-step acquisition. P64 is a justified **candidate**, not
proof that its newly block-averaged curves will pass. Neither kappa2 nor N32
terminal times are established by these two N8 observations.

At N32,T4000, an allocated20-level ladder saturates. Its maximum exported lags
are:

| dt | P32,L20 | P64,L20 | P64,L24 |
|---:|---:|---:|---:|
|0.0001|812.6464|1651.5072|3879.7312|
|0.00005|406.3232|825.7536|3879.7312|
|0.000025|203.1616|412.8768|3879.7312|

The last P64,L24 bin has only1 origin; it is **not terminal-supported**.
At finest dt the corresponding P64,L20 last bin has547 origins. Coverage must
be assessed per bin with both origin and block-duration gates, not by the final
lag alone. For N8,T200, P64,L20 exports541/573/605 bins over the timestep triplet;
P64,L24 does not extend those populated ladders. For N32,P64,L24 the counts are
678/710/742. Preserving a long physical horizon at every-step acquisition calls
for a reviewed candidate such as P64,L24, with an explicit larger memory budget.
The physical lag grid and frame counts differ from the frozen campaign; this
requires a **prospective versioned scientific amendment**, not an operational
profile substitution. Existing results, plan, thresholds and identities stay intact.

## Resource and throughput estimates

All estimates below use C2048. Stress records remain six doubles in both CUDA
precisions:96KiB/frame. Coordinates differ in precision, not this PCIe payload.
No complete stress history is required in RAM or on disk.

| Device batch frames | One stress slab | Two device slabs | Two pinned host slabs |
|---:|---:|---:|---:|
|32|3MiB|6MiB|6MiB|
|256|24MiB|48MiB|48MiB|
|1024|96MiB|192MiB|192MiB|
|10000|937.5MiB|1875MiB|1875MiB|

Scratch tensor storage, diagnostics, parameters, positions, events, worker stacks
and allocator overhead are additional. A10,000-step stress flush is unnecessarily
large as a starting point;256–1024 frames is a bounded benchmark range, not a
selected production optimum. The current semiflexible settings reject batches
above4096 or a single host batch above256MiB;4,096 stress frames at C2048 exceed
that byte guard. Preserve guards unless a separately reviewed budget replaces
this limit. Two slabs cannot absorb unlimited CPU lag.

LP64 stress-bank allocation formula from `OwnedCorrelator6::bytes` gives about
236.84MiB for P32,L20;466.84MiB for P64,L20;560.09MiB for P64,L24, including
chain-owner pointers. The last exceeds the existing512MiB bank budget. This is
an allocation estimate, not peak RSS. Adding the validated C1+C2 orientation
bank at P64,L20 adds approximately608.44MiB of array payload plus objects,
scratch and allocator overhead; its prior measured standalone peak was624.33MiB.

Every-step traffic is substantial even though storage is bounded:

| System | Steps at coarsest/finest dt | Total stress D2H, decimal GB, including step0 |
|---|---:|---:|
|N8,T200|2,000,000 /8,000,000|196.608 /786.432|
|N32,T4000|40,000,000 /160,000,000|3932.160 /15728.640|

Batching preserves these bytes; it reduces the number of transfer submissions
from F to ceil(F/batch), their latency and synchronization cost. Raw CSV dumps
would grow with C*F and should be confined to bounded diagnostics. Compact scalar
summaries and exported multi-tau bins remain bounded/logarithmic at fixed banks;
never enable an unbounded raw stress history as the normal transport.

For context, the committed temporal audit reports the N8,kappa10 pilot:
8M steps, dt0.000025,20,001 stress frames, integration286.497s
(**1.943ns/bead/step**), production351.511s (**2.384ns/bead/step**), stress
GPU2.023s, D2H0.153s, CPU bank wall15.139s using4 workers,P32. These are old
sparse-acquisition measurements, not every-step benchmarks. Rough unit-cost
projections are:

- About101microseconds GPU stress/frame, or5.49ns/bead/step if repeated every
  step at unchanged N8 active-bending cost. This GPU work is ordered alongside
  integration; transfer batching cannot hide it from its producer stream.
- About2.706million chain-frames/s CPU correlation, or369.6ns/chain-frame.
  Eight million every-step frames would require about6055s of CPU bank wall
  work at that rate, before P64 costs and stress-moment processing. That alone
  corresponds to about41.1 overall ns/bead/step for N8. It is a throughput
  warning, **not a measured lower bound or forecast** for a new implementation.
- The old96KiB/frame D2H scope averages about7.7microseconds/frame. Its apparent
  bandwidth includes latency; it cannot prove the bandwidth or overlap of
  larger pinned transfers. At an illustrative integration rate2ns/bead/step,
  the stress stream requires2.67GB/s for N8 and0.73GB/s for N32. Added stress
  computation/backpressure reduces the real rate. No N32 integration benchmark
  is inferred from these arithmetic examples.

Per-frame correlator work is approximately O(C*P), with an amortized dyadic
ladder; increasing P32 toP64 increases both memory and work. The stress producer
is approximately O(C*N). Larger N therefore changes the GPU/CPU balance, but
N32 timings need measurement. Every-step scalar-coordinate transfers would add
3x/11x the stress bytes for N8/N32 single, or6x/22x for double, before CPU scalar
work. Decoupling clocks is important; it must not weaken scalar scientific gates.
Timers overlap in an asynchronous pipeline: retain GPU integration,
GPU stress, D2H, diagnostic waits, CPU pool wall/barrier, producer buffer wait,
initialization, finalization and overall production separately. Do not add
subset/overlapping scopes to manufacture wall time or claim a production-server
speedup from the pilot or a microbenchmark.

## Independent orientation acquisition

The existing endpoint layout allows one GPU thread per chain to form
R=r[c*(N+1)+N]-r[c*(N+1)] without full bead readback. A packed double3 record is
48KiB/frame at C2048. Packing is explicit: copying `real4` would change the byte
count. CPU `orientation::Bank` already safely normalizes finite nonzero R and
forms the five rank-two features; two Vector banks are summed per chain before
SE. Preserve C1=<u dot v>, C2=<P2(u dot v)>, no squared averaged C1, no coarse
feature renormalization, no empirical mean subtraction.

With independent stride s=10 or100 and a provisional10,000-integration-step
flush interval, one orientation slab holds1000 or100 records, respectively:
46.875 or4.6875MiB in double-packed form. Two device and two pinned slabs double
each memory class. Step0 needs explicit inclusion/capacity accounting, not an
extra untracked frame. Float-packed records halve PCIe/slab bytes but introduce
endpoint-rounding differences that require cross-precision validation; CPU
correlation arrays still use double. At s10/100, double orientation adds5%/0.5%
of the every-step stress transfer bytes.

Direct per-frame transfer has the same total payload as batching but
approximately1000/100 transfer submissions per10,000 steps rather than one.
GPU buffering reduces latency/fences, not bytes or normalization work. A separate
bounded slot queue can share the transfer stream while keeping its own clock,
metadata and CPU consumer; sharing a flush boundary must not force orientation
sampling to match stress or flush on every integration step. Endpoint sampling
must be ordered before old-coordinate buffers are reused; ready/copy-done events
protect transport storage independently. A full slot may legitimately stall the
producer: "independent" does not mean no resource contention or backpressure.

The validated orientation adapter is serial. At C2048, its prior P32/P64 C1+C2
throughputs were0.789/0.585million chain-observations/s; C1-only3.617/2.357million.
At the illustrative N8 integration-only2ns rate, s10 requests5.56million chain
observations/s and s100 requests0.556million. Thus s10 cannot be assumed cheap
with the serial adapter; s100/P64 is already near its standalone rate before
sharing CPUs with stress. These comparisons mix microbenchmark and illustrative
rates and establish no production performance. Stress workers cannot directly
consume the typed orientation bank. Review fixed chain ownership or bounded
orientation parallelism without oversubscribing the stress pool. Preserve
integer acquisition steps, exact physical lag/block widths, complete-chain
frames, origin counts and C-1 chain-cluster variance. Neither origins nor lags
are independent statistical samples.

## Minimal implementation proposal and approval requirements

1. Keep the accepted semiflexible producer mathematics and zero-angular fast
   path. Add a slab destination without changing force/update/RNG execution.
   Use the local Rouse slot/event/backpressure pattern, not KG-specific caches,
   kinetic terms, volume normalization or a new multi-tau implementation.
   Leave Rouse itself unchanged. Review whether a small local transport helper
   or isolated adaptation has the smaller tested surface; no whole-module copy.
2. Reuse `Correlations`, `Bank` and `CpuWorkers`; deliver all slab frames and
   moment updates in chronological order with deterministic chain ranges. Drain
   final partial slabs before evaluating; no silent overload drops. Preserve
   stretch–bend cross terms and existing chain-level covariance treatment.
3. Separate stress every-step, scalar acquisition and optional orientation
   clocks. Preserve original behavior as an explicit legacy path. New metadata
   must authenticate all schedules, S+1 stress frames, batch identities/counts,
   worker settings, lag grids and the versioned scientific amendment.
4. Review diagnostic handling before claiming asynchronous readiness. Existing
   stress failure readback produces a failing-coordinate snapshot immediately.
   Deferring it until a slab flush could lose that configuration when positions
   are overwritten. Keep fail-fast checks initially, or obtain separate approval
   for a bounded first-failure capture design preserving step/seed/reason and
   geometry. Do not relax failure detection or accepted integration diagnostics
   simply to remove synchronization. All-zero bending must allocate/launch no
   angular stress work in either transport mode.
5. Start with bounded throughput tests of256/1024-frame slabs and existing CPU
   workers before adding transport complexity. At sustained CPU overload accept
   slower overall production or review a measured local optimization; larger
   queues and fewer stress frames are not solutions. P64,L24 and combined-bank
   memory need explicit guards and a reviewed lag-support calculation for every
   model. No claim that this candidate resolves unmeasured N32/kappa2 tails.

### Reusable verification and bounded benchmark design

No tests were run during this audit. Existing relevant sources are:

- KG_Assoc `kg_assoc_stress_test.cu`: instantaneous versus buffered reduction;
  `kg_correlator6_counts_test.cpp`: all six channels, coarse means and counts.
  The retained checkpoint regression checks serialization/continuation of
  deterministic inputs; it does **not** establish production resume or per-chain
  persistence for semiflexible, and is unnecessary for this transport task.
- Local `tests/pipeline_tests.cu`, `tests/stream_lifetime.cpp`,
  `tests/cpu_workers.cpp`, `correlator_smoke.cpp`: queue/failure lifetime,
  sanitizers, worker partitioning, signed samples and direct block counts.
- `tests/test_stream.py`, `test_stream_theory.py`,
  `semiflexible_stress_correlator.cpp`, `test_semiflexible_stress_gpu.py`:
  direct correlations, discrete Gaussian theory, prescribed virials, chain
  isolation, zero-bending and stress-on/off trajectory replay.
- `tests/test_semiflexible_scalar_output.py`,
  `test_semiflexible_stress_campaign.py`: exact output/profile replay,
  fail-closed provenance, schedule/count validation and Gaussian finite windows.
- `tests/orientation_cpu.cpp`, `orientation_allocation_failure.cpp`,
  `run_orientation_cpu.py`: direct C1/C2/block/SE oracle, allocation failures,
  repeated lifetime and ASan/UBSan/LSan.

A future authorized bounded validation should first use prescribed numbered
frames: compare direct transfer, synchronous batching and two-slot async delivery
for every exported bin/channel/H/SE, moments, counts and order. Test batch1/7/32/
256/1024, short and partial runs, S+1 including step0, forced slow consumers,
producer/transfer/consumer errors, clean drain and memory caps. Use finite
prescribed N1/2/8/32 chains, heterogeneous/inactive bending and singular failures.
Compare exact replay with observation off/on and different buffering settings
in each CUDA precision; retain existing force/stress tolerances and CPU
orientation3e-11 absolute/relative tolerance. Buffering must not change the order
of per-chain floating-point additions.

Then benchmark acquisition-only prescribed coordinates and deterministic CPU
sequences separately from short integrated fixtures. At C2048,N8/N32,both
precisions, compare direct versus batch256/1024, workers1/2/4 and permitted
additional counts, P32/P64, and orientation stride10/100. Measure completed
frames/s, transfer bytes/submissions, slot occupancy/backpressure, peak RSS,
GPU allocations, pinned bytes, CPU pool wall cost, event overhead, integration
and overall ns/bead/step. Warm up and repeat within bounded host budgets; use
short unit fixtures here and provide user-host commands for anything exceeding
10minutes. Only prefer asynchronous buffering if it reduces measured wall cost
at unchanged acquisition and estimators. Review per-frame timing-event overhead
before replacing it with any batch timing; never conflate GPU integration and
production timing. Long scientific simulations require separate authorization.

## Decision

There is no missing KG asynchronous worker framework to import: the strongest
reusable transport already exists locally, and its bank/CPU workers are already
shared with semiflexible. KG contributes a useful confirmation of instantaneous
GPU batching and final-partial handling, not a drop-in independent-chain pipeline.

**A focused architecture design/review is still necessary**, rather than another
broad implementation: settle the stress/scalar clocks and versioned protocol,
P/L/budget choice, first-failure snapshot ownership, bounded asynchronous slot
interface, and CPU throughput/backpressure policy. Optional orientation should
remain a separately clocked consumer. Approval cannot rest on buffer capacity
alone. This audit neither approves a new campaign nor changes any frozen
scientific threshold, accepted executable, dynamics, RNG or existing evidence.
