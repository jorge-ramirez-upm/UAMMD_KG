# Stage 4A.3c — every-step GPU stress acquisition benchmark

19 October 2026. This is an isolated benchmark implementation, not a simulator
change and not a campaign execution. It was committed from `slip-springs` at
`d0f9553ab8249cf91f3e69e6d063b9fb26324ac4`. The authenticated campaign source
and execution checkouts remain detached at
`4e46d6014aa812b1fc687335654c4b1f681ddd22` and were not edited.

## Execution status

No GPU measurement is claimed in this checkout. `nvcc` is present at
`/usr/bin/nvcc`, but `nvidia-smi` fails with “couldn't communicate with the
NVIDIA driver”; consequently there is no CUDA device on which a bounded fixture
can safely run. GPU name, driver version, executable SHA-256, throughput, event
timings and peak device allocation are therefore **not
measured**, not zero. The benchmark itself prints the GPU identity, precision,
frame hash, all timings, rates and allocation capacities as one JSON record on
an execution host. Capture `nvcc --version`, `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader`, `sha256sum` of both binaries,
and every JSON line with the host result.

The attempted local single-precision build also failed before device execution:
CUDA 11.5.119 (18 Nov 2021) cannot parse the installed GCC 11.4 standard-library
headers (`std::function` parameter-pack errors). No alternate compiler was
installed or selected. This is a build-host blocker, separate from the absent
driver; the host report must record its successful compiler/build transcript.

This environment did run the bounded CPU prescribed-coordinate reference suite
(`tests/test_semiflexible_reference.py`): 12 tests passed. The new static test
also verifies that the benchmark uses the existing stretching/bending/channel
kernels, pinned D2H allocation, async-copy path, ordered frame hash, separate
integration/overall ns-per-bead-step fields, and explicit final-partial transfer.
GPU kernel/reference/replay results remain pending an execution host; do not
represent those as passed from this report.

## Benchmark design

`tests/every_step_gpu_stress_benchmark.cu` is a standalone executable. It does
not link `semiflexible.cu` and does not change forces, RNG, campaign commands or
production transport. It uses the existing `stretch`, optional `bend`, `update`,
`stress3b::stretchTensor`, `stress3b::bendTensor` and `stress3b::channels`
kernels. The deterministic fixture uses 2,048 independent chains, N=8 or32,
`dt=0.000025`, κ=0 or10, a 100-step warm-up and at most 10,000 timed updates.
Every timed state is acquired: steps0 through10,000, hence10,001 frames.

The timing scopes are deliberately not added together:

| JSON field | Scope |
| --- | --- |
| `integration_seconds` | force kernels plus Euler–Maruyama update, CUDA-event elapsed |
| `stretch_seconds`, `bend_seconds`, `channels_seconds` | separate stress CUDA-event elapsed; κ=0 reports bend=0 and issues no bend launch |
| `d2h_seconds` | host wall time enclosing transfer/completion only |
| `diagnostic_seconds` | mandatory force/stress error-key D2H checks |
| `wall_seconds` | complete timed producer run, including synchronization and transfer |

`stress_frames_per_second` and `chain_observations_per_second` are complete
producer rates based on `wall_seconds`; GPU-kernel-only throughput can be derived
from the appropriate non-overlapping kernel scope, but must not be described as
end-to-end. `integration_ns_per_bead_step` is CUDA-event integration cost;
`overall_ns_per_bead_step` is complete wall cost. Frame hashes are FNV-1a over
each copied six-channel frame in order. Matching hashes across direct, batch and
async runs establishes no missing, duplicate or reordered transport frame for
the deterministic replay. Retain all JSON files and fail a comparison on a hash
mismatch.

Three transport mechanisms are included:

1. `direct` performs a synchronous six-channel D2H copy per frame.
2. `batch` writes frames into a bounded device slab and performs synchronous D2H
   at 256 or1,024 frames, with the incomplete final slab copied explicitly.
3. `async` is a benchmark-only pinned-slot/event adapter. It uses an async D2H
   copy and event completion at slab ownership hand-off. It is not production
   transport and does not alter the Rouse pipeline.

The diagnostic keys are read after every integration/acquisition; a failed key
aborts rather than suppressing geometry diagnostics. The existing prescribed
coordinate GPU test remains the numerical six-tensor oracle and must be run on
both precision binaries before accepting timing data. The benchmark's stable
ordered hash must additionally agree across mechanisms/capacities for a short
replay. Compare stress-off/on final coordinates and force/RNG traces with the
existing short GPU fixture; no new relaxed tolerance is introduced.

## Preflight memory

Six channels are double `Sample` values (48 bytes/chain/frame). The largest
requested slab is `1024*2048*48 = 100,663,296` bytes (96 MiB) in both device and
pinned host memory. Tensor and position/force buffers are bounded by N and
chains, never steps. The executable emits actual vector capacities as
`device_bytes` and `pinned_host_bytes`; record the maximum of those plus the
host process/GPU monitor, not this arithmetic estimate, as peak memory. Refuse
runs whose requested fixture exceeds the executable bounds; do not shrink frame
retention or skip diagnostics.

## Required bounded host run

Build both precisions, then place each JSON result in a new external results
directory (never a frozen campaign directory):

```sh
make -C examples/slip-springs PRECISION=single every-step-gpu-benchmark
make -C examples/slip-springs PRECISION=double every-step-gpu-benchmark
for p in single double; do
  b=examples/slip-springs/build/$p/every_step_gpu_stress_benchmark
  for n in 8 32; do for k in 0 10; do
    for mode in direct batch async; do "$b" --n "$n" --kappa "$k" --batch 256 --mode "$mode" > "RESULTS/$p-N$n-k$k-$mode.json"; done
  done; done
  "$b" --n 32 --kappa 10 --batch 1024 --mode batch > "RESULTS/$p-N32-k10-batch1024.json"
  "$b" --n 32 --kappa 10 --batch 1024 --mode async > "RESULTS/$p-N32-k10-async1024.json"
done
```

Each invocation is bounded to 10,000 timed steps and must be stopped/reduced if
it approaches120 seconds. Run the prescribed-coordinate GPU suite and a short
mechanism replay first. The N8/N32, κ=0/10 and two-precision matrix covers the
required physics/precision; 1,024-frame capacity is sampled at the larger active
case where capacity is most informative, avoiding a redundant full Cartesian
matrix.

## CPU comparison and decision rule

The existing sustained CPU correlator baselines are 1.935 million
chain-observations/s (frame-major) and 4.834 million chain-observations/s
(validated chain-major prototype). They are from a CPU host and must not be
treated as same-host GPU results. For every measured GPU producer rate `P`, report
`P/1.935e6` and `P/4.834e6`; a sustained producer rate above either CPU rate
does not itself prove a pipeline backlog because the CPU correlator's workload,
cores and overlap policy differ. Backpressure is likely when a complete producer
rate remains above the measured same-host CPU consumer rate over repeated bounded
runs; larger batches only absorb a finite burst and cannot fix that sustained
inequality.

No recommendation beyond a minimum benchmark result is justified yet. If the
host evidence has matching hashes, prescribed-coordinate/replay checks and the
async adapter lowers producer wall time without a sustained CPU deficit, the
minimum production change to consider is reuse of the existing bounded
slot/event transport with a 256-frame initial capacity. Otherwise retain
synchronous bounded batches and investigate the dominant measured scope first.

## Remaining blockers

* A GPU host with a working driver is required for all requested actual throughput,
  transfer, event, compiler/executable identity and peak-memory results.
* The current adapter synchronizes its event before reusing a single benchmark
  slab; it measures transport mechanics but does not prove concurrent CPU
  correlation behavior. Any production overlap needs a separately authorized
  adapter/integration change and same-host backpressure experiment.
* The benchmark retains the required failure check but does not serialize the
  production simulator's geometry snapshot itself. Existing simulator GPU tests
  remain the source of first-failure geometry evidence.
