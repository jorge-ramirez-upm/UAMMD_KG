# Stage 4A.4 — N=32 timestep validation

Prepared only; no GPU simulation launched. Starting development HEAD was verified
as `8440bb377c458120a97ff74bc39baf20bb291341` on `slip-springs` in
`/tmp/UAMMD_KG-slip-springs-dev`. The supplied working directory and
`/tmp/UAMMD_KG-stage4a3c-exec` are protected, clean, detached checkouts at
`4e46d6014aa812b1fc687335654c4b1f681ddd22`. All edits belong to the development
worktree, under `examples/slip-springs/`.

## Experiments and resources

Run sequentially in this order; never infer N=32 acceptance from N=8:

| N | κ | dt | T | steps | scalar stride | timeout |
|---:|---:|---:|---:|---:|---:|---:|
|32|0|0.000025|20|800,000|400|1,800 s|
|32|0|0.0005|20|40,000|20|300 s|
|32|10|0.000025|20|800,000|400|1,800 s|
|32|10|0.0005|20|40,000|20|300 s|

Each case uses 512 independent chains (33 beads each), seed 433201, double
precision, b0=1, kb=30, kBT=zeta=1, free ends and uniform interior κ. Preserve
the exact equilibrium initializer, Euler–Maruyama update, complete six-channel
stress every integration step including step zero, 32 slots × 24 levels,
coarsening 2, 256-frame batches, eight CPU workers and full scalar output.
Scalar spacing is 0.01 in physical time, giving 2,001 frames / 1,024,512 scalar
rows per case. Stress has 800,001 or 40,001 frames, accumulated online without
dumping a stress history. No simulator, initializer or correlator change is made.

Stage A evidence (`/tmp/stage4a3c-stage-a-results-v2.tgz`,
`receipts/stage-a-summary.json` and `commands/stage-a.cmd`) measured precisely
this N32/κ10/512-chain/32×24/eight-worker configuration for 100,000 steps:
49.5365505 s wall, 197,048 KiB peak RSS, zero producer blocking. Scaling by step
count estimates 396.3 s per baseline and 19.8 s per coarse case, about **14 minutes
for four GPU cases**. This is a planning estimate on the same host, including
scalar work that does not scale linearly; κ0 and changed host load can differ.
The prospective caps total 4,200 s (70 minutes) plus at most 20 s termination
grace per process. They are not retrospectively extended after a timeout.

Allow eight CPU cores for workers (plus producer/consumer threads), **2 GiB host
RAM, 1 GiB free GPU memory including context, and 4 GiB free disk**. The bank is
about 71 MiB, with 12 MiB pinned transport and 12 MiB device transport, plus
integration/stress state, thread stacks, runtime/context and output buffers.
Stage A RSS is a useful measurement, not a guaranteed peak. Full scalar CSVs
are roughly 0.2–0.35 GiB each; budget 1–1.5 GiB for four completed cases plus
logs, histograms, initial/final snapshots, references and reports. Keep failures
and any earlier roots separately. Stress D2H traffic is approximately 18.31 GiB
per baseline and 0.916 GiB per coarse case (38.45 GiB total); this is traffic,
not retained disk storage. Record actual metadata and `/usr/bin/time -v` costs;
never add overlapping timer scopes.

Two exact independent-equilibrium references (N32, κ0/10, 65,536 chains each,
seed 440401) are generated on the execution host with the existing reference
script, at most 900 s each. Postprocessing has 600 s per κ. Including these CPU
caps, total managed child time is at most 120 minutes plus termination grace,
provenance checks and file checksumming. Preflight runs neither ensembles nor
simulations. No new compilation is necessary or performed.

## Host commands and provenance

Safe preflight (CPU only; even GPU queries and executable `--help` are skipped):

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
python3 examples/slip-springs/tests/run_stage4a4_n32_timestep.py
```

User-host execution, after inspecting preflight and allocating the resources:

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
python3 examples/slip-springs/tests/run_stage4a4_n32_timestep.py --execute-n32
```

Each invocation prints a fresh `/tmp/stage4a4-n32-*` evidence root. Optionally
supply `--root /absolute/new/directory` outside every worktree; existing roots
are refused, including a previous preflight root. Keep the preflight root for
review; execution prepares a separate root with the same four commands. The
root contains exact shell-quoted argv, plan/estimates, source hashes, repository
identity, executable hash, host GPU/toolkit identities, separate per-process
started/final receipts, time reports and logs. Successful case files receive
SHA-256 inventories before analysis. Analysis completion means reports exist,
not that the scientific gates passed.

The runner requires a clean `slip-springs` checkout with the specified GitHub
origin and ancestry from the expected starting commit. It verifies both
protected pins/cleanliness and the executable SHA before and after every case.
Expected executable: `examples/slip-springs/build/double/semiflexible`, SHA-256
`0a8d5bb7f3fc87617e4c6790457e504f4946816e884de9f44b22728ae538e859`.
A mismatch stops work; never rebuild or replace a queued campaign binary.
Execution requires the existing CUDA 13.0 toolkit (`CUDA_HOME` defaults to
`/usr/local/cuda-13.0`), `nvidia-smi`, Python with NumPy, and `/usr/bin/time`.
Toolkit version and a checksum do not independently prove compilation provenance.

The first process failure, timeout or interruption stops the sequence. The
whole process group is terminated, with 20 s grace before SIGKILL. SIGINT/SIGTERM
leave an interruption receipt; SIGKILL/power loss may leave only a started
receipt. Preserve all outputs in either case. No partial output enters analysis,
no completed case is overwritten, and **interrupted trajectories are never
resumable**. A subsequent attempt requires a new evidence root and starts fresh.
Completed cases remain available for read-only inspection if a later case fails.

## Static and dynamic decisions

The N32 analysis is a narrow wrapper around the existing Stage 4A.4 static,
histogram and dynamic tools. It checks physical parameters, 64-bit precision,
complete scalar clocks, histogram coverage, stress frame counts/configuration
and finite evidence before reading estimates. Each chain is one statistical
cluster. Across timesteps use conservative unpaired SE even with the same seed
and initial conformations; differing step indices do not establish paired noise.

Static means and stationarity use equal physical halves `0 <= t < 10` and
`10 < t <= 20`, omitting the midpoint (1,000 frames per chain per half).
Retain 1% for mean bond length and bond-square, 2% for Re², Rg² and tangents 1–4;
tangent differences use the natural unit scale, including κ0. Compare both halves
to the exact reference. Assess within-chain second-minus-first drift with the
same scale/tolerance and chain SE. For normalized absolute difference d and
combined SE s, pass requires d+3s <= tolerance, fail requires
max(0,d−3s) > tolerance, otherwise unresolved. A stationarity failure blocks
acceptance and calls for a separately budgeted extension decision, never an
automatic longer run.

Whole-run bond histograms retain chain SE and reference SE, a TV limit 0.02,
0.01 absolute finite-bin differences and 0.005 overflow probability difference.
Checking every finite bin includes central bins without choosing bins after
seeing data. TV uncertainty uses the conservative triangle bound
`0.5 sum(bin_SE)`; it does not assume independent bins. Half-specific histogram
stationarity cannot be reconstructed. Local tangent correlation at separation 1
is the available local angle mean; separations 1–4 supply short-contour
orientation correlations. Full-contour raw bond-vector correlations, trajectory
energies (1%), local angle distributions (TV 0.02), and end-to-end distributions
remain **explicitly unresolved** because existing outputs do not provide them.
Thus even passing all available gates cannot yield final static acceptance.

Dynamics reports absolute H(0), its relative and absolute discrepancy and
unpaired SE separately, with **no new amplitude threshold**. Preserve
`H=(Cxy+Cxz+Cyz)/5+(Cxx_yy+Cxx_zz+Cyy_zz)/30`, its exported chain SE, all six
channel correlations/contributions and SE, H(t)/H(0) and conservative propagated
SE. The fixed-lag tolerance remains `|ΔH|+3SE <= 0.05 H_baseline(0)`;
resolved excess fails and uncertainty overlapping the tolerance is unresolved.
No separate normalized-shape or channel threshold is invented.

For targets 0.01, 0.05 and 0.10, report actual bin centers, block widths and
per-chain origins. The unchanged 32-slot multi-tau export has an exact center
at 0.01 for both timesteps; block widths still differ (0.0004/0.0005).
For the baseline, targets 0.05 and 0.10 have nearest exported centers 0.0496
and 0.0992 (widths 0.0016 and 0.0032); the coarse timestep has exact centers.
**Identical requested physical lags at 0.05 and 0.10 are unavailable in those
baseline exports.** Keep the established nearest-bin diagnostics, but mark the
exact-lag gates unresolved; do not interpolate or call different centers an
identical-lag measurement. Resolving those gates requires a separately approved
diagnostic/export approach, not an estimator change hidden in this preparation.

Report the first H(0)/e crossing only where the supported export brackets it,
with the established conservative three-SE envelope and 10% tolerance. Require
at least 16 block origins per chain for dynamic support; origins are not
independent samples. No tail fit or extrapolated crossing is permitted. T=20 may
be far too short for the slowest N32 mode: this tests short-time timestep error,
not terminal relaxation. A supported first crossing is not proof of terminal
sampling. Any observed rejection remains visible; otherwise the report remains
unresolved while required diagnostics or support are missing. No timestep is
authorized for production by preparation or operational success.

To repeat read-only analysis into a new report after all four cases complete:

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
ROOT=/absolute/path/to/completed/stage4a4-n32-root
for KAPPA in 0 10; do
  python3 examples/slip-springs/tests/stage4a4_n32_timestep_analysis.py \
    --small "$ROOT/run-double-N32-k${KAPPA}-dt.000025" \
    --large "$ROOT/run-double-N32-k${KAPPA}-dt.0005" \
    --reference "$ROOT/references/N32-k${KAPPA}.json" \
    --report "$ROOT/receipts/N32-k${KAPPA}-review.json"
done
```

CPU-only regression commands (no GPU, model rebuild, or long reference ensemble):

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
timeout 120s python3 -m unittest discover -s examples/slip-springs/tests -p test_stage4a4_n32_timestep.py -v
timeout 180s python3 -m unittest discover -s examples/slip-springs/tests -p test_stage4a4_timestep_tools.py -v
```

Preparation verification: 16 CPU-only tests passed (nine N32 safety/analysis
regressions plus seven existing timestep-tool regressions). No GPU run, build,
or full N32 reference ensemble was executed. The Stage0-base branch scope and
tracked/untracked/ignored paths were checked programmatically; all paths remain
under `examples/slip-springs/`. Both protected worktrees stayed clean and pinned.
