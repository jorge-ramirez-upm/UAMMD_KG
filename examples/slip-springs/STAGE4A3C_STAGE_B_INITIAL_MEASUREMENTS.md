# Stage 4A.3c — Stage B Initial Nonlinear Relaxation Measurements

This is a prospective, execution-free Stage B protocol. It does not authorize
or launch either N=8 measurement. Stage A on `cholosimeone` completed N=32,
κ=10, double precision, 512 chains, 100,000 steps in 49.54 s with zero
producer blocking and approximately 192 MiB peak RSS. Those are measured
Stage-A facts; the N=8 estimates below are extrapolations.

## Initial measurements

| case | chains | seed | duration | steps | dt | stress hierarchy | batch/workers |
|---|---:|---:|---:|---:|---:|---|---|
| N=8, κ=0 | 512 | 433201 | 200 | 8,000,000 | 2.5e-5 | 32×20, m=2 | 256 / 8 |
| N=8, κ=10 | 512 | 433201 | 200 | 8,000,000 | 2.5e-5 | 32×20, m=2 | 256 / 8 |

Every integration step, including zero, produces the six raw configurational
stress channels. Scalar diagnostics remain on their independent 400-step
clock. `--scalar-output full` is mandatory because compact scalars are only
accepted by legacy stream mode. Each measurement is one exploratory replica:
the 512 chains are independent uncertainty clusters, not independent
trajectory replicas.

## Runtime and storage gate

Stage A achieved about 2,019 stress frames/s and 1.03 million chain
observations/s for N=32. Directly applying its per-step wall time to 8,000,000
steps gives about 3,963 s (66 min), already above the Stage-B 30-minute cap.
N=8 has fewer beads and may be faster, but that has not been measured. This is
therefore a pre-execution blocker, not grounds to raise the cap silently. The
runner enforces 1,800 s and preserves evidence if it times out; review that
result before selecting a different duration or resource limit.

The 32×20 correlator bank is 59.21 MiB for 512 chains. Two 256-frame
double-precision stress slabs are about 12 MiB. Online correlation retains no
raw every-step stress trajectory. Full scalar output produces
20,001×512 = 10,240,512 rows per run; reserve at least 3 GiB per run for scalar
CSV plus logs and metadata before any authorization. This is a planning reserve,
not a measured file size.

## Read-only analysis

`tests/stage4a3c_stage_b_analysis.py` reads `stress_correlations.csv`,
`stress_metadata.json`, and `metadata.json`. It verifies the six-channel H
combination, exact every-step frame count, multi-tau lag/block/origin grid, and
independent-chain pair totals. It reports every bin's actual origins, width,
H, and H standard error; identifies the first H(0)/e crossing with six-SE
pointwise bounds; then applies the frozen checks for a resolved positive signal
near 2τ and a supported terminal bin beyond 4τ (at least 16 origins and width
at most τ/4).

Its outcomes are `passed`, `failed`, or `insufficient_support`. A single
replica cannot be a scientific acceptance result even if the terminal check
passes. It must never infer a fitted time from an unsupported tail.

## Host commands

Preflight only; this does not execute a simulator:

```sh
cd /tmp/UAMMD_KG-slip-springs-dev
bash examples/slip-springs/tests/run_stage4a3c_stage_b.sh
```

Explicit user-authorized sequential execution, subject to the 30-minute cap
per case:

```sh
cd /tmp/UAMMD_KG-slip-springs-dev
bash examples/slip-springs/tests/run_stage4a3c_stage_b.sh --execute-stage-b
```

The runner requires the clean `slip-springs` development worktree, CUDA 13.0,
the double executable, and both protected worktrees clean/pinned at
`4e46d6014aa812b1fc687335654c4b1f681ddd22`. It creates a new `/tmp` evidence
root containing `environment/`, `commands/`, `logs/`, and `receipts/`, with a
separate immutable simulator output directory for each κ. It runs κ=0 then
κ=10, stops after a failure/timeout, writes the exit classification and
`/usr/bin/time -v` receipt, and does not treat interruption as resumable.

## Stopping and extension

* If a run times out, do not launch the second case or extend the first one.
  Review measured N=8 throughput, output growth, host RSS, GPU allocation, and
  producer/consumer timing first.
* If H crosses H(0)/e but lacks supported 2τ/4τ evidence, record the crossing
  as exploratory and draft a separately reviewed extension using the measured
  τ, 16-origin condition, and width condition.
* If no resolved crossing occurs, classify the result as insufficient duration
  or uncertainty; do not call duration 200 sufficient.
* Only after the first-replica reports are reviewed may seed 433202 be run for
  independent confirmation. Scientific acceptance additionally requires the
  existing precision/replication review.

No checkpoint/restart facility exists: an interrupted output is evidence, not
a prefix that can be resumed into the same stochastic/correlation history.
