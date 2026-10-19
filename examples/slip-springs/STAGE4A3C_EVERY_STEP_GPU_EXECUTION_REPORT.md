# Stage 4A.3c — every-step GPU benchmark execution report

19 October 2026. This is an execution-validation report for benchmark commit
`853dc2e71366dbb3b3298d31333ef7318f900c47`, not a new benchmark implementation.

## Phase 1 result: blocked before build

The `slip-springs` execution worktree was clean and at the requested SHA:

```
853dc2e71366dbb3b3298d31333ef7318f900c47
```

Both frozen Stage 4A.3c worktrees were separately checked, clean, and remain
pinned at:

```
4e46d6014aa812b1fc687335654c4b1f681ddd22
```

The mandatory first GPU preflight command failed:

```text
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.
```

No usable CUDA GPU is available to this execution environment. Per the approved
task boundary, execution stopped here: no compiler/toolkit changes, package
changes, driver actions, builds, GPU tests, replays, CPU throughput reruns or
benchmark fixtures were launched.

## Measurements and correctness

All requested execution measurements are unavailable, rather than zero:

| Item | Status |
| --- | --- |
| GPU model, driver and memory | unavailable: driver not communicating |
| CUDA benchmark binaries / SHA-256 | not built |
| Prescribed-coordinate GPU reference | not run |
| Direct/batch/async frame-hash replay | not run |
| N=8/N=32, kappa=0/10 timing matrix | not run |
| GPU stress frames/s / observations/s | not measured |
| D2H/event/diagnostic timing | not measured |
| GPU/pinned peak allocation | not measured |
| Same-host chain-major CPU comparison | not run |

It would be invalid to compare the earlier 1.935M and 4.834M CPU
chain-observations/s baselines with absent GPU producer data or to infer CPU
backpressure from this host.

## Required next step

Use a production CUDA host on which `nvidia-smi` successfully reports the GPU,
driver and memory, and where the CUDA toolkit is compatible with the selected
host compiler. Then follow the bounded matrix and correctness/replay order in
`STAGE4A3C_EVERY_STEP_GPU_BENCHMARK_REPORT.md`, keeping every invocation at or
below the existing 120-second cap and writing results outside frozen campaign
directories. No long-running authorization is needed for that already bounded
matrix; stop and report if any invocation approaches the cap or any correctness
check fails.
