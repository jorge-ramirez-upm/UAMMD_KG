# CPU correlator locality and optimization experiment

19 October 2026, Europe/Madrid. This isolated CPU experiment started from `84303ec6b685770bcef2c94a9ba5f95e2b5b652a`. It adds a test-only chain-major prototype, its bounded harness, a traversal option to the prior benchmark, and this report. No CUDA source, simulator, force/update kernel, RNG, scientific estimator, frozen plan, campaign artifact, UAMMD/KG/KG_Assoc source, or Rouse source changed.

## Outcome

At 2048 chains, 64 slots, 24 levels, eight workers and batch 256, chain-major processing sustained **4.834 million chain-observations/s**, or **2360 complete six-channel frames/s**. The unchanged frame-major path sustained **1.935 million/s**, or **945 frames/s**. The gain is **2.50x** with byte-identical CSV output and essentially identical peak process RSS: 671.36 versus 671.28 MiB.

This correct bounded CPU consumer remains below the roughly 51–57 million chain observations/s implied by historical N8/N32 integration-only rates. It does not establish the future GPU producer/transfer rate and does not change the every-timestep, step0-inclusive stress-acquisition requirement.

## Prototype and semantics

`tests/chain_major_correlator.h` is test-only. It uses the existing `streaming::OwnedCorrelator6` owners and their unchanged `push`, `evaluate`, `gett`, `getn`, and `getf` methods. Its writer retains the reference chain order, six raw channels, within-chain H combination (shears/5 and raw normal differences/30), Welford chain-cluster uncertainty, lag/block grid, incomplete-block handling, deepest-level omission, CSV order and precision.

```text
reference:  for each frame, process each owned chain
prototype:  for each owned chain, process its batch frames chronologically
```

Each owner receives the same chronological samples; there is no cross-chain state. The local worker pool preserves fixed contiguous chain ownership, persistent helpers, caller worker0, one batch at a time, completion before reuse, error propagation and frame accounting. The production `streaming::Bank` and `CpuWorkers` remain unchanged. This is a scheduling prototype, not a new estimator, storage representation, normalization, temporal averaging, thinning, or production integration.

## Method and validation

`tests/stress_throughput.cpp` now selects `frame` or `chain`. It feeds precomputed deterministic six-channel inputs with nonzero means, correlated channels, chain identity and nontrivial temporal variation. Input construction, bank initialization, warm-up, final `write`, worker join and teardown are outside the update rate. Each normal child warms 1024 frames and times 1025; sustained children warm 1024 and time 8193. A 1 GiB correlator-allocation preflight, 120-second per-child timeout, and 540-second fail-closed suite limit apply.

`tests/run_correlator_locality.py` ran 26 selected configurations, interleaved with deterministic seed 433202. It covers C=256, 1024, 2048; P32/L20 and P64/L24; batches 32, 256, 1024; and practical workers 1, 2, 4, 8. The 2048-chain cases repeat three times and smaller cases twice. Host: Linux 5.15.0-198-generic, Intel Core i7-12700, 20 logical CPUs in inherited affinity, g++ 11.4.0. There was no thread pinning, fixed frequency, or idle-host claim. The suite completed in 467.40 seconds; its longest child took 14.47 seconds.

The independent NumPy oracle evaluates complete block means and time-origin products, all six means and SEs, H after within-chain channel combination, physical lags, block widths and pair counts. It uses the established 3e-11 absolute/relative tolerance. All **3904 exported bins** passed with maximum absolute discrepancy **2.220446049250313e-16**. Every matched frame-major/chain-major CSV, worker/batch variant, and sustained repetition was byte-identical. This covers incomplete terminal blocks, deepest-level omission, chain-cluster uncertainty and output ordering.

## Representative measurements

Rates are medians with ranges across independent child processes. Frames/s means complete C-chain frames; RSS includes input, allocator/runtime pages and workers.

| C | P/L | W | Batch | Frame M chain-obs/s | Chain M chain-obs/s | Gain |
|---:|---:|---:|---:|---:|---:|---:|
| 2048 | 64/24 | 1 | 256 | 0.332 [0.307,0.359] | 0.621 [0.574,0.623] | 1.87x |
| 2048 | 64/24 | 4 | 256 | 1.057 [0.497,1.067] | 2.493 [2.364,2.493] | 2.36x |
| 2048 | 64/24 | 8 | 32 | 1.651 [1.546,1.677] | 4.815 [4.141,4.830] | 2.92x |
| 2048 | 64/24 | 8 | 256 | 1.155 [0.842,1.770] | 4.310 [4.233,4.313] | 3.73x |
| 2048 | 64/24 | 8 | 1024 | 1.794 [1.175,1.863] | 4.426 [4.001,4.443] | 2.47x |
| 2048 | 32/20 | 8 | 256 | 3.144 [1.974,3.652] | 8.939 [6.728,9.273] | 2.84x |

The sustained P64/L24/8-worker/batch256 series is the representative comparison:

| Traversal | M chain-obs/s | Frames/s | CPU cores | Caller barrier ms | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|
| Frame-major | 1.935 [1.929,1.936] | 945 | 7.57 | 681.38 | 671.28 |
| Chain-major | 4.834 [4.813,4.838] | 2360 | 7.97 | 18.43 | 671.36 |

The P64/L24 bank allocates 560.09 MiB and the bounded 1024-frame input cycle is 96 MiB. Chain-major adds no material memory. Batch choice is not universal: chain-major eight-worker medians are 4.815, 4.310 and 4.426 M/s for batches 32, 256 and 1024. These CPU measurements do not select a GPU pipeline batch.

## Bottleneck evidence and recommendation

`perf` is absent; Valgrind, LIKWID, VTune and PCM are also unavailable. Therefore there are no cache-miss, bandwidth, instruction-count or microarchitectural stall claims.

The measured result identifies the dominant actionable limitation in the reference path: applying the same owner operations in per-chain chronological order gives a 2.50x sustained gain, with unchanged RSS, while the caller barrier falls from 681 ms to 18 ms. The frame-major schedule therefore has material locality and worker-completion loss. This is scheduling evidence, not proof of a particular cache level, pointer-chase rate, DRAM ceiling or SIMD limitation.

The result justifies a future local chain-major consumption change after focused review. It is simpler than a replacement estimator and preserves reference semantics exactly here. Further contiguous/pool-allocation work is justified for investigation because the remaining gap is still about an order of magnitude; begin with a local prototype that preserves per-chain arithmetic and the same oracle. Do not add SIMD or multi-chain reduction that changes arithmetic order without its own numerical contract.

Before production integration, run a bounded GPU acquisition benchmark measuring actual every-step virial evaluation, mandatory diagnostics, D2H transfer and sustained CPU backpressure. CPU buffering cannot establish those values, and no future optimization may drop samples, thin observations, remove cross terms or count origins as independent chains.

## Evidence and limits

```sh
python3 -B examples/slip-springs/tests/run_correlator_locality.py
```

The completed ignored evidence is `build/correlator-locality/run-jke2f68g/results.json`, SHA-256 `2f4f74e7747f0853412cc32b0bd76f6cbda7b699c39a74f974da6e6a211dabaa`. It includes source, binary, command, log and CSV hashes. It is benchmark evidence, not campaign evidence.

The protected execution checkout remains clean at `4e46d6014aa812b1fc687335654c4b1f681ddd22`. No GPU simulation, production trajectory, campaign analysis, sanitizer run, hardware-counter profile or production replay was performed.
