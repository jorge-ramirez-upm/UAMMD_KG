# Stage 4A.3c — Nonlinear Relaxation Pilot (Prospective Protocol)

This document defines a bounded host-execution pilot. It was prepared from
the frozen Stage 4A.3c plan, the current `semiflexible` CLI, and the existing
GPU/multi-tau capacity reports. **No pilot, GPU simulation, production
trajectory, or protected checkout was run.**

## What is established

The controlled Gaussian harmonic reference has stress times

| model | Gaussian stress time |
|---|---:|
| N=8 | 1.381809895 |
| N=32 | 18.40369002 |

These are mode-spectrum results and are not assigned to the finite-rest-length
model. The prior N=32 rigid-rod estimate near 565 is a planning scale only,
not a measured nonlinear relaxation time. The nonlinear N=8 κ=0, N=8 κ=10,
N=32 κ=0, and N=32 κ=10 times remain unknown.

## Staged pilot matrix

The pilot uses the existing exact radial/conditional equilibrium initializer;
there is no artificial burn-in. Each run retains step 0 and acquires all six
stress channels at every integration step. Correlations use all stress frames;
stationarity and scalar summaries use the existing final-half diagnostics.

| stage | N | κ | precision | chains | replicas/seeds | duration | steps at dt=2.5e-5 | stress hierarchy |
|---|---:|---:|---|---:|---|---:|---:|---|
| A: throughput preflight | 32 | 10 | double | 512 | 433201 | 2.5 | 100,000 | 32×24, m=2 |
| B: first replica | 8 | 0, 10 | double | 512 | 433201 | reviewed fraction of 200 | not fixed before A/B review | 32×20, m=2 |
| B: first replica | 32 | 0, 10 | double | 512 | 433201 | reviewed fraction of 4,000 | not fixed before A/B review | 32×24, m=2 |
| C: confirmation | cases with reviewed first replica | same κ | double, then single | 512 | 433202, then 433201 single | reviewed | reviewed | same |

Stage A is a performance/backpressure measurement only; its duration is not a
polymer-relaxation observation. Stage B begins with one double-precision
replica per model only after Stage A has been reviewed. The original durations
200 and 4,000 are upper planning horizons, not automatic Stage-B expenditures:
the review must select the initial duration from observed throughput and retain
an explicit stopping rule. Stage C adds the independent seed only after the
first-replica evidence is reviewed. Single precision remains conditional on a
resolved double-precision case. No stage is a restart or extension of another
trajectory.

The N=32 32×24 hierarchy is the provisional engineering choice requested for
the next phase. N=8 uses 32×20 because the shorter duration does not need the
additional redundant levels. Both settings retain the frozen deepest-level
omission and the 16-origin reporting requirement.

Scalar diagnostics use `--sample 400`, which is physical spacing 0.01 at this
timestep and is independent of the every-step stress clock. Use
`--scalar-output compact` to retain bounded per-chain equilibrium dimensions,
end-to-end/tangent summaries, finite-row hashes, and stationarity statistics.
Compact output does not contain the full center-of-mass time series; CM
diffusion is therefore a secondary diagnostic only if a separately bounded
full-scalar run is authorized. No dynamics change is proposed.

## Observables and gates

The primary observable is the complete configurational stress correlation,
including stretching, bending, and cross terms. The reported isotropic value is

```text
H(t) = (Cxy+Cxz+Cyz)/5
     + (Cxx_yy+Cxx_zz+Cyy_zz)/30.
```

For every model, replica, and precision, retain the six component correlations,
H, per-chain standard errors, frame/pair counts, and lag widths. Apply the
frozen gates without reinterpretation:

1. no missing, nonfinite, duplicated, reordered, or failed stress frames;
2. diagnostic tensor, force, RNG/replay, and zero-bending checks pass;
3. independent-chain uncertainty is computed across the 512 chains, never from
   overlapping time origins;
4. a resolved positive H near `2*tau_e` exceeds 3 chain standard errors;
5. a supported bin beyond `4*tau_e` has at least 16 origins per chain,
   block width no greater than `tau_e/4`, and satisfies the frozen terminal
   amplitude/noise condition;
6. crossings and support must agree across replicas and fitting windows.

Define `tau_e` only from the first H(0)/e crossing with the existing pointwise
uncertainty bounds. Do not fit an unsupported tail, assign the Gaussian or
rigid-rod spectrum to the nonlinear chain, or alter a threshold after seeing
the result.

Secondary existing scalar fields are `re2`, `rg2`, `cm_msd` (full output only),
and tangent summaries. Use them for stationarity, dimension, end-to-end, and
orientation diagnostics; they do not replace the six-channel stress gate.

## Resource estimates and stop bounds

The validated Linux64 correlator accounting gives, for 512 chains:

| hierarchy | CPU correlator bank |
|---|---:|
| 32×20 | 59.21 MiB |
| 32×24 | 71.02 MiB |

Two 256-frame six-channel stress slabs add about 12 MiB in double precision
(6 MiB single) for 512 chains; integration state and compact scalar storage are
small by comparison. A 512 MiB correlator budget remains the declared cap.

The earlier measured N=8 κ=10 result was 2.381 s for 10,000 steps and 2,048
chains, including overlapping GPU/CPU work. Linear scaling from that result is
only a planning extrapolation: it suggests minutes for an 8-million-step N=8
run and many hours for a 160-million-step N=32 run. N32 bead count, hierarchy,
CPU backpressure, output, and host differences make the extrapolation
uncertain. Stage A therefore uses exactly 100,000 steps (physical time 2.5),
a five-minute wall timeout, and no scientific relaxation claim. It records
total wall time, stress-frame and chain-observation rates, producer blocking,
CPU correlation timing, queue occupancy, stress-buffer allocations, and peak
host RSS. A later reviewed run may retain the prospective 30-minute N=8 and
12-hour N=32 caps; it may not increase buffers or duration merely to hide
backpressure.

## Evidence and provenance requirements

Use a new output root outside both frozen campaigns, with one immutable
directory per `(precision,N,kappa,seed)`. Before each run archive:

- repository SHA and clean-tree status;
- SHA-256 of the selected executable and `--help` output;
- compiler/CUDA/driver/GPU identities and host load;
- the exact argv, model parameters, hierarchy, seed, and resource cap.

After each run archive metadata, scalar/stress summaries, `/usr/bin/time -v`,
GPU/pinned-buffer measurements, diagnostics, and SHA-256 manifests. Never reuse
an output directory or overwrite a failed receipt.

## Exact user-host commands

The isolated runner is
`tests/run_stage4a3c_nonlinear_pilot.sh`. It only operates from
`/tmp/UAMMD_KG-slip-springs-dev`, verifies both protected worktrees remain
clean/pinned, records the current dynamic Git identity rather than a stale
hard-coded SHA, and refuses a dirty worktree or pre-existing evidence root.

Preflight-only mode is the default and does not launch the simulator:

```sh
cd /tmp/UAMMD_KG-slip-springs-dev
bash examples/slip-springs/tests/run_stage4a3c_nonlinear_pilot.sh
```

Only after the user explicitly authorizes the bounded Stage-A run:

```sh
cd /tmp/UAMMD_KG-slip-springs-dev
bash examples/slip-springs/tests/run_stage4a3c_nonlinear_pilot.sh --execute-stage-a
```

The runner creates a fresh `/tmp/stage4a3c-nonlinear-pilot-preflight.*` root,
then records `environment/`, `commands/`, `logs/`, and `receipts/`. Stage A
uses `timeout --foreground --signal=TERM --kill-after=20s 300s`; its receipt
classifies completed, timeout, interruption, and application failure. Logs,
`/usr/bin/time -v` output, GPU before/after snapshots, and any simulator output
survive a timeout. On successful completion, `stage-a-summary.json` includes
the requested timing, throughput, queue, producer-blocking, device/host stress
allocation, and peak-RSS fields.

## Checkpoint/restart capability

Exact restart is **not supported**. The CLI can accept initial coordinates but
does not serialize or restore the integration step, correlator banks, pending
GPU/CPU transport state, scalar state, or correlation history. The RNG is
counter-based by `(seed, bead, step)`, so restarting at CLI step zero would also
reuse the wrong stochastic timestep sequence. An interrupted run is preserved
as evidence only and cannot be treated as the first segment of an extended
trajectory.

## Decision gates and stopping rules

* **Resolves relaxation:** both replicas show a consistent `tau_e`, positive
  support near `2*tau_e`, and supported terminal behavior beyond `4*tau_e`.
  Use those measured times to draft a separately versioned production plan.
* **Detects relaxation but lacks terminal support:** report the measured
  crossing and extend only by a prospective rule, such as a reviewed duration
  sufficient for at least four measured `tau_e` plus 16 origins and width
  `<=tau_e/4`; do not silently extend.
* **Inconclusive:** classify the cause as duration, chain uncertainty,
  temporal resolution, numerical precision, or computational backpressure.
  Stop rather than launching an unbounded extension.

This protocol prepares the next review only. It does not authorize the pilot,
the revised production campaign, or any change to the correlator hierarchy.
