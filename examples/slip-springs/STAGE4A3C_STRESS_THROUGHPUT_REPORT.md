# CPU stress-correlator throughput benchmark

19 October 2026, Europe/Madrid. Starting local/fetched `origin/slip-springs`:
`a546c02d41e248400c4580fdd693886dc8061286`. All work used the development
worktree. Only the two new CPU benchmark/test sources and this report are added.
No scientific simulation, GPU work, campaign analysis, production rebuild or
change to an existing source, estimator, threshold or frozen artifact occurred.

## Method and measurement scopes

`tests/stress_throughput.cpp` links the unchanged KG `correlator.cpp` and uses
`stream_correlator.h::Bank` and `cpu_workers.h::CpuWorkers` directly. All samples
and reductions use CPU double; compilation is `g++ -O2 -std=c++17 -pthread`,
without fast-math or architecture-specific flags. No simulator is linked.

Inputs are precomputed outside the update timer. The deterministic1024-frame
cycle uses exact dyadic fractions, explicit chain indices, nonzero means,
correlated shears and raw normal differences. Its channels represent sums of
shared varying terms, so correlating the total retains their cross terms.
Normal differences obey xx-zz=(xx-yy)+(yy-zz). Additional constant and alternating
fixtures test distinct temporal behavior. These are prescribed numerical inputs,
not equilibrium polymer configurations or independent physical replicas.

Each measurement runs in a fresh child process, allocates one bank, constructs
persistent workers, generates one bounded input cycle, consumes1024 warm-up
frames, then times1025 updates. The last timed batch has one frame. Warm-up
remains in the bank: its exported2049 frames include the initial frame and all
subsequent observations. It is not cleared, decimated or counted as timed work.
An additional longer series times8193 frames after the same warm-up, exporting
9217 frames. Both totals leave incomplete coarse blocks. Every frame reaches the
actual six-channel correlation updates; input generation, allocation and output
evaluation cannot be mistaken for correlation throughput.

The harness `tests/run_stress_throughput.py` records commands, source/binary/log/
correlation hashes, per-trial configuration, load, timers and RSS in a unique
ignored `build/stress-throughput/run-*` directory. It runs children serially;
no simultaneous correlator banks. Every subprocess timeout is at most120s,
and the suite enforces a540s deadline without silently shortening a case.
The1GiB preflight applies to aggregate correlator allocation, using the actual
`OwnedCorrelator6::bytes` formula; separate input/worker memory is recorded.
Budget/dimension rejection tests exercise the guard before any bank allocation.

Rates count one complete six-channel observation per chain, not six observations:
R_chain=C*timed_frames/update_wall; R_frames=timed_frames/update_wall. Timers are:

- Bank allocation/initialization, worker construction, input generation and
  warm-up measured separately.
- Update wall includes calls to `CpuWorkers::consume` and all required completion
  barriers. Existing pool wall, worker aggregate range time and caller barrier
  time are differenced across the timed window. Aggregate worker time sums
  overlapping worker scopes; it is not elapsed time or CPU utilization.
- `update_wall-pool_wall` measures the outer submission-loop/timer cost. Dispatch
  inside `consume` remains in pool wall. The unchanged implementation does not
  expose an exclusive dispatch timer. Barrier wait is a subset of pool wall,
  overlaps helper work, and includes scheduling imbalance; do not add it again.
- Process user+system CPU time from `getrusage`, divided by update wall, measures
  core equivalents (1=one fully occupied CPU;8=800% process CPU). Worker range
  wall timers include possible descheduling and cannot replace that measure.
- Final `Bank::write` evaluates/reduces every chain and serializes the CSV, timed
  separately. Worker join and bank teardown have separate timers. No finalization
  cost appears in update throughput. Linux peak RSS is process lifetime high
  water; current RSS is also sampled before/after bank and input allocation.

### Matrix and reproducibility

There are25 selected configurations, each repeated three times in deterministic
shuffled order (seed433201). The full Cartesian product would contain144 cases.
All1/2/4/8-worker and32/256/1024-batch combinations run at the largest bank:
C2048,P64,L24. At batch256, smaller C256/1024 run workers1/4/8; C2048,P32,L20
runs all four worker counts. Matched L20/L24 comparisons use P64 workers1/4 and
P32 workers4. This excludes119 redundant combinations prospectively, not after
seeing their performance. All selected cases complete; none is silently resized.
Three further repetitions use the fastest median large-bank configuration for
the longer8193-update check. Small-bank timing windows are brief; their highest
rates should not be advertised as sustainable large-system throughput.

Only allocated levels20/24 are compared: short streams populate fewer levels.
The long fixture reaches zero-indexed level13; it does not empirically exercise hours of
acquisition or saturate level23. Deep-level arrivals are geometrically rare,
but long-duration cache/scheduler behavior remains unmeasured. The full bank
allocation and teardown costs are measured at the requested levels.

## Independent correctness

The harness's NumPy oracle constructs complete nonoverlapping block means,
then explicitly averages time-origin products per chain for **every** exported
bin. It independently calculates all six means/SEs and forms
H_chain=sum(shear products)/5+sum(normal-difference products)/30 **before**
computing ensemble mean and sample-standard-deviation/sqrt(C). It does not
subtract empirical time means or treat time origins/channels as independent.
The legacy Bank columns `g,g_se` are raw H,H_se here, as in existing stress code;
this benchmark does not assign temperature, chain density or a physical modulus.

The oracle checks the exact lag grid, physical spacing1, complete-block width,
origin counts per chain and in total, inherited deepest-level omission and
incomplete-block truncation. It uses the existing CPU stress tolerance
**absolute3e-11 plus relative3e-11**, unchanged from
`test_semiflexible_stress_gpu.py::check_direct`.

Twenty-four nontrivial fixtures cover P32/L20 and P64/L24, nine chains,
1027 frames, all four worker counts and all three batch sizes. Two259-frame
fixtures cover constant and alternating signals. All **3808 exported bins**
pass; maximum absolute discrepancy across channel/H means and SE is
**2.220446049250313e-16**. Output CSVs are byte-identical across worker/batch
variants of each ladder. Timed matrix outputs are also hash-compared across
repetitions/workers/batches for the same C/P/L. The three longer-run outputs
match each other exactly. Bank frame counters match all submitted frames.

The existing `tests/cpu_workers.cpp` regression is compiled and run unchanged,
including unequal ranges, worker counts, batches and poisoned-worker cleanup.
It passes. Existing stock KG reader warnings concern unused `read()` methods;
those methods are not called. No scientific tolerance was weakened.

## Measured host and results

Host: Linux-5.15.0-198-generic-x86_64-with-glibc2.35; Intel Core i7-12700; g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0.
Inherited affinity contains CPUs0–19 (20 logical CPUs). No individual thread/core pinning;
this hybrid P/E-core CPU and normal scheduler placement limit scaling claims.
System load averages were (0.12, 0.03, 0.009) before and (4.136, 2.043, 0.883) after;
per-child load is saved. Load includes these benchmark workers, not only
external contention. CPU frequency/boost was not locked. Standard root cgroup
quota files were unavailable; no quota or homogeneous-core assumption is made.
The entire executed suite took **352.98s**, including builds, correctness,
75 matrix measurements and three longer checks; longest child wall was
**10.55s**.

Rates below are median [minimum,maximum] of three independent processes.

| C | P | L | Workers | Batch | Million chain-observations/s | Frames/s median |
|---:|---:|---:|---:|---:|---:|---:|
| 256 | 64 | 24 | 1 | 256 | 0.588 [0.588,0.589] | 2296.8 |
| 256 | 64 | 24 | 4 | 256 | 2.285 [2.270,2.296] | 8925.1 |
| 256 | 64 | 24 | 8 | 256 | 4.665 [4.663,4.675] | 18221.1 |
| 1024 | 64 | 24 | 1 | 256 | 0.445 [0.445,0.452] | 435.0 |
| 1024 | 64 | 24 | 4 | 256 | 1.582 [1.565,1.586] | 1544.5 |
| 1024 | 64 | 24 | 8 | 256 | 3.176 [3.168,3.208] | 3101.8 |
| 2048 | 32 | 20 | 1 | 256 | 0.649 [0.647,0.650] | 316.7 |
| 2048 | 32 | 20 | 2 | 256 | 1.107 [1.104,1.147] | 540.8 |
| 2048 | 32 | 20 | 4 | 256 | 2.022 [1.982,2.051] | 987.3 |
| 2048 | 32 | 20 | 8 | 256 | 3.858 [3.793,3.884] | 1883.8 |
| 2048 | 32 | 24 | 4 | 256 | 2.005 [1.976,2.007] | 978.9 |
| 2048 | 64 | 20 | 1 | 256 | 0.400 [0.400,0.401] | 195.3 |
| 2048 | 64 | 20 | 4 | 256 | 1.165 [1.164,1.185] | 568.9 |
| 2048 | 64 | 24 | 1 | 32 | 0.398 [0.396,0.399] | 194.5 |
| 2048 | 64 | 24 | 1 | 256 | 0.398 [0.394,0.399] | 194.5 |
| 2048 | 64 | 24 | 1 | 1024 | 0.394 [0.394,0.399] | 192.5 |
| 2048 | 64 | 24 | 2 | 32 | 0.704 [0.696,0.706] | 343.7 |
| 2048 | 64 | 24 | 2 | 256 | 0.699 [0.699,0.701] | 341.4 |
| 2048 | 64 | 24 | 2 | 1024 | 0.699 [0.699,0.700] | 341.3 |
| 2048 | 64 | 24 | 4 | 32 | 1.129 [1.127,1.132] | 551.3 |
| 2048 | 64 | 24 | 4 | 256 | 1.167 [1.149,1.169] | 569.9 |
| 2048 | 64 | 24 | 4 | 1024 | 1.171 [1.167,1.173] | 571.8 |
| 2048 | 64 | 24 | 8 | 32 | 1.884 [1.875,1.885] | 919.7 |
| 2048 | 64 | 24 | 8 | 256 | 1.972 [1.958,1.975] | 962.7 |
| 2048 | 64 | 24 | 8 | 1024 | 1.963 [1.958,1.986] | 958.5 |

Per-configuration setup/resource/timer medians follow. RSS is the maximum over
three processes. Init is bank allocation+initialization; evaluation includes CSV
output. Free combines worker join and bank teardown (recorded separately in raw
JSON). WorkerΣ is summed overlapping range wall time during1025 timed frames;
barrier is caller wait within pool wall. Outer cost is caller time outside pool
per submission, **not** an exclusive measurement of dispatch inside the pool.

| C/P/L/W/B | Init/evaluate/free ms | WorkerΣ s | Barrier ms | Outer microseconds/batch | CPU core equivalents | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|
| 256/64/24/1/256 | 28.5/2.5/1.5 | 0.446 | 0.00 | 0.149 | 1.00 | 87.34 |
| 256/64/24/4/256 | 20.0/2.6/2.3 | 0.456 | 0.60 | 0.830 | 3.97 | 87.54 |
| 256/64/24/8/256 | 23.1/2.7/2.1 | 0.443 | 0.69 | 0.864 | 7.90 | 87.64 |
| 1024/64/24/1/256 | 80.2/7.6/6.8 | 2.356 | 0.00 | 0.223 | 1.00 | 337.36 |
| 1024/64/24/4/256 | 78.2/7.7/7.4 | 2.651 | 0.56 | 0.907 | 4.00 | 337.52 |
| 1024/64/24/8/256 | 77.7/7.8/7.8 | 2.616 | 0.29 | 0.661 | 7.99 | 337.86 |
| 2048/32/20/1/256 | 64.0/8.2/10.0 | 3.236 | 0.00 | 0.228 | 1.00 | 345.48 |
| 2048/32/20/2/256 | 68.8/8.2/11.8 | 3.665 | 0.42 | 0.388 | 1.93 | 345.63 |
| 2048/32/20/4/256 | 68.1/8.3/12.6 | 3.692 | 13.86 | 0.661 | 3.55 | 345.70 |
| 2048/32/20/8/256 | 67.9/8.3/11.9 | 4.206 | 6.80 | 0.800 | 7.73 | 346.20 |
| 2048/32/24/4/256 | 83.3/8.4/14.5 | 3.720 | 106.12 | 0.607 | 3.52 | 395.33 |
| 2048/64/20/1/256 | 126.3/14.1/12.3 | 5.249 | 0.00 | 0.322 | 1.00 | 575.90 |
| 2048/64/20/4/256 | 130.3/14.0/14.6 | 6.796 | 38.10 | 0.822 | 3.78 | 576.20 |
| 2048/64/24/1/32 | 152.7/14.2/13.6 | 5.269 | 0.00 | 0.245 | 1.00 | 671.00 |
| 2048/64/24/1/256 | 150.1/14.3/13.7 | 5.271 | 0.00 | 0.307 | 1.00 | 670.99 |
| 2048/64/24/1/1024 | 152.3/14.2/13.7 | 5.324 | 0.00 | 0.358 | 1.00 | 671.01 |
| 2048/64/24/2/32 | 154.3/14.3/15.3 | 5.958 | 1.09 | 0.364 | 2.00 | 671.11 |
| 2048/64/24/2/256 | 149.3/14.3/19.2 | 5.938 | 0.32 | 0.412 | 1.98 | 671.24 |
| 2048/64/24/2/1024 | 151.5/14.2/15.4 | 5.941 | 0.34 | 0.668 | 1.98 | 671.28 |
| 2048/64/24/4/32 | 151.9/14.2/16.0 | 6.796 | 264.58 | 0.598 | 3.65 | 671.31 |
| 2048/64/24/4/256 | 149.5/14.2/15.8 | 6.832 | 27.19 | 0.834 | 3.80 | 671.14 |
| 2048/64/24/4/1024 | 150.0/14.3/16.0 | 6.773 | 0.64 | 0.801 | 3.77 | 671.21 |
| 2048/64/24/8/32 | 148.4/14.2/16.0 | 7.947 | 126.12 | 0.919 | 7.11 | 671.17 |
| 2048/64/24/8/256 | 152.0/14.2/15.6 | 7.844 | 3.59 | 0.528 | 7.37 | 671.20 |
| 2048/64/24/8/1024 | 152.3/14.4/18.6 | 7.726 | 0.70 | 0.565 | 7.25 | 671.27 |

Allocation preflight and observed working sets, grouping identical C/P/L banks:

| C/P/L | Bank allocation MiB | Input cycle MiB | Current RSS after bank, median MiB | Peak RSS max MiB |
|---|---:|---:|---:|---:|
| 256/64/24 | 70.01 | 12.00 | 74.75 | 87.64 |
| 1024/64/24 | 280.05 | 48.00 | 288.73 | 337.86 |
| 2048/32/20 | 236.84 | 96.00 | 249.28 | 346.20 |
| 2048/32/24 | 284.09 | 96.00 | 298.52 | 395.33 |
| 2048/64/20 | 466.84 | 96.00 | 479.27 | 576.20 |
| 2048/64/24 | 560.09 | 96.00 | 574.40 | 671.31 |

The longer fixture chose **C/P/L/W/B=2048/64/24/8/256**
(fastest median for the largest bank). It achieved **1.938million
chain-observations/s**, range[1.934,1.938], or
**946.2complete frames/s**. Median timed update duration was
8.659s per repetition; warm-up0.975s,
evaluation/output18.4ms,
CPU utilization7.30core equivalents. This establishes
only a bounded warm-state rate, not a guarantee over multi-day production.

The highest individual short-window rate was4.675million/s
at C/P/L/W/B=256/64/24/8/256;
its timed window was only0.056s. It is not the representative
2048-chain rate.

## Producer–consumer balance

Historical GPU measurements below are from the permanent Stage4A.2 archive,
`validation/stage4a2-acceptance/campaign/<run>/metadata.json`, C2048,kappa10,
RTX3060Ti. Four files were verified against `ORIGINAL_FILES.json` SHA-256
entries without changing the archive. They exclude observations from integration
events but include the documented diagnostic/host launch gaps; they are not pure
force-kernel rates. Original executable/compiler provenance has the limitations
recorded in `STAGE4A2_REPORT.md`. These older timings are context, not a benchmark
of the current every-step producer.

| Archived run | Integration ns/bead/step | Historical overall ns/bead/step | Integration-only frames/s | Required million chain-observations/s | CPU/integration demand |
|---|---:|---:|---:|---:|---:|
| single-N8-k10-s420202-h5e-05 | 1.950483 | 2.942832 | 27815.4 | 56.966 | 3.4% |
| double-N8-k10-s420202-h5e-05 | 7.222734 | 8.213612 | 7511.5 | 15.384 | 12.6% |
| single-N32-k10-s420202-h5e-05 | 0.597832 | 0.983676 | 24750.1 | 50.688 | 3.8% |
| double-N32-k10-s420201-h0.0001 | 5.920182 | 6.639276 | 2499.3 | 5.119 | 37.9% |

A more recent Stage4A.3c N8 single,kappa10 pilot, quoted in the temporal audit,
measured integration1.943 and overall2.384ns/bead/step. Its integration-only
demand is similarly about57.2million chain-observations/s. The historical
overall rates used sparse stress/scalar sampling and must not be described as
every-step throughput.

For the actual future pipeline distinguish four rates:

1. Integration-only rate from the corresponding hardware/precision/configuration.
2. GPU stress-production rate: integration **plus** each ordered complete-stress
   evaluation and mandatory diagnostics. This has not been measured at every step.
3. CPU consumption measured here, excluding GPU transfer, stress moments, scalar
   observations, failure snapshots and output management. Those costs can only
   reduce production capacity or compete for resources.
4. Sustained end-to-end rate is limited by the slowest producer, transfer and
   consumer, with producer backpressure when buffers fill. GPU work ordered on
   the integration stream cannot be hidden behind itself. Overlapping CPU/GPU
   scopes must not be summed as wall time.

The sparse N8 single pilot reported2.023s GPU stress for20001 frames, roughly
101microseconds/frame. Combining that unit cost with35.8microseconds/integration
step gives a **hypothetical** every-step producer near7300frames/s, about15million
chain-observations/s, still much faster than this CPU consumer. This is an
unvalidated linear unit-cost projection; batching/diagnostics and contention
may change it. Equivalent every-step GPU stress measurements for N8 double and
N32 single/double are missing; whether their actual GPU stress producer outruns
the CPU cannot be settled by integration times alone.

At the measured representative CPU rate, consumption takes approximately
1056.9microseconds per complete frame. With ideal overlap and no other
CPU work, its corresponding optimistic overall cost floors would be
**57.34ns/bead/step for N8** and **15.64 for N32**.
CPU-only budget projections are2.35hours for8M+1 N8 stress
frames and46.97hours for160M+1 N32 frames. These are conditional
throughput calculations, not actual simulator wall times or guaranteed bounds.
No number of buffers removes this sustained processing demand.

## Bottlenecks and recommendation

At C2048,P32,L20,batch256, worker speedups relative to1 are
1:1.00x, 2:1.71x, 4:3.12x, 8:5.95x.
At C2048,P64,L24,batch256, worker speedups relative to1 are
1:1.00x, 2:1.76x, 4:2.93x, 8:4.95x.

Both ladders show sublinear scaling. At P64/L24,batch256/1024, caller barrier
waits are generally small and process CPU utilization is high, indicating that
correlation-update work dominates. Batch32 has material caller waits: about
265ms at four workers and126ms at eight workers per1025 timed frames. These
waits overlap helper computation; they are not exclusive dispatch overhead.
Batch256 improves the eight-worker median rate by about4.7% relative to32,
while1024 adds no measured improvement. Batch dispatch alone is not the
sustained throughput bottleneck. P64 reduces throughput relative to P32.
At matched P64/L24/batch256/eight workers, increasing C256 to2048 lowers
chain-observations/s despite a larger nominal work unit. The repeated
frame-major traversal through independently allocated chain ladders is a
plausible cache/locality cost: the bank grows from70 to560MiB, far beyond
private caches. This is a source-supported hypothesis, not a measured cache-miss
or bandwidth attribution; no hardware performance counters were collected.

There is little evidence that increasing batches beyond256 solves the sustained
limit. Allocating24 rather than20 levels increases memory and initialization;
short acquisitions have identical active-depth requirements and show similar
update rates. Do not infer a full long-acquisition comparison from this result.
P32 is faster but is not a substitute for the scientifically required candidate
P64 lag support described in the buffering audit. Stress acquisition remains
every step, including step0.

**Recommended next development step:** an isolated CPU locality/profile experiment
before building the complete asynchronous GPU acquisition pipeline. Test whether
chain-major consumption of a completed batch can reuse each chain ladder in
cache while retaining chronological additions within each chain, fixed worker
ownership, frame accounting, unchanged KG add/evaluate and byte-identical output.
This report does not implement that traversal or authorize production changes.
Avoid a new correlation algorithm or copying KG modules. Use measured results
to decide whether a minimal local scheduling change is justified.

A bounded GPU acquisition-only benchmark remains necessary after the design
review to measure the actual every-step producer, diagnostic fences, stress
transfer bytes/latency and CPU/GPU contention. A simple bounded pipeline may
operate correctly today by stalling, but optimizing only transport cannot meet
integration-only throughput. Never conceal the bottleneck by discarding frames,
reducing stress frequency, removing cross terms or counting origins as chains.

## Reproduction, evidence and limitations

From the development worktree, the following runs only isolated CPU code:

```sh
python3 -B examples/slip-springs/tests/run_stress_throughput.py
python3 -B examples/slip-springs/tests/run_stress_throughput.py --benchmarks
```

This completed run is `build/stress-throughput/run-4n4sl8r5`.
Its `results.json` SHA-256 is
`0cba03b88d064f7e86ec815354f1ea38843e2fde52f33d7de54fa8826419330c`.
The benchmark executable SHA-256 is
`33fef5fcfc0bbd36cb0f03439976233e81de52c166e8f961b6d50f0b9b6bc2f3`.
Raw JSON/log/CSV evidence remains in ignored build storage; it is not campaign
evidence and may be lost if that storage is cleaned. This report preserves all
configuration-level rate spreads, timer/resource medians and correctness outcomes.
Exact trial metrics and output hashes are in the local JSON; the harness records
source identities and explicit failure status on exceptions/timeouts. No selected
case was skipped; the119 unselected Cartesian cases are explained above.

The development source hashes used by the run are:

- `stream_correlator.h`: `3be57db604dc0b23a96fbe103b328baa3634815eb785c4a1eb050c2d29be0a68`
- `cpu_workers.h`: `8bf5e78123f84e1e37ff1b6d169abac0491f0ec6271d33e9bd5e56ed6df0c290`
- `../KG/correlator.h`: `1ce5842bc5557879e5beb0f9b6d0144bf616258bd7bae3d5092719719f084e4d`
- `../KG/correlator.cpp`: `84ca3742820824d9e093c8f62b6f408e2e42017d5a7539f5cbf76e4f81fff9c0`
- `tests/stress_throughput.cpp`: `fe6e0b9bdb7ccecbe5b0f5b76ccead180aa41aedef81193135cbd2f6286132cf`
- `tests/run_stress_throughput.py`: `1fd7c0bd0564a6a42a28b4a54ea481f873f22515d9762dd3ddd973dcfede50f0`

Peak RSS includes input, allocator metadata, shared runtime pages and resident
worker stacks; bank bytes are not a process-RSS cap. No concurrency beyond
the requested workers was benchmarked. Benchmarks did not exercise physical
stress distributions, every-step GPU timing, asynchronous transfers or scientific
terminal relaxation. No new sanitizer campaign was required or run; unchanged
owners/workers have prior sanitizer coverage and the existing worker regression
passes here. The original execution checkout remains clean and pinned at
`4e46d6014aa812b1fc687335654c4b1f681ddd22`; its original single/double executable
hashes were checked unchanged. Existing scientific references, frozen artifacts,
Rouse, GPU sources, build behavior and campaign results remain untouched.
