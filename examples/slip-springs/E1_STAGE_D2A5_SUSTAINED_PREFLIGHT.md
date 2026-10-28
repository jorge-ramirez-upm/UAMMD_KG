# D2A.5 minimal sustained-performance preflight

Preparation only, 28 October 2026. Starting HEAD and verified implementation:
`d622e0cc34d4019358bebad5ce8a86e64c265351`. No build, test, simulation,
benchmark or scientific analysis was executed in Codex. Independent review is
required before the user runs the commands below. No simulator, physical model,
observable, correlator arithmetic, historical campaign or binary is modified.

## Two sequential measurements

The [driver](e1_d2a5_preflight.py) reuses `run_process` from the unchanged
`e1_d1_pilot_runner.py`. It runs exactly these two configurations in order:

| N bonds | M chains | kappa | Z | Beads | Steps | Dynamics frames |
|---|---|---|---|---|---|---|
| 64 | 256 | 10 | 4096 | 16640 | 100000 | 1001 |
| 128 | 256 | 10 | 8192 | 33024 | 100000 | 1001 |

Both retain double precision, dt=0.0001, kb=30, b0=kBT=zeta=1,
slip-ms2=5, hop-rate=100, canonical end renewal, stress off and dynamics stride100.
The seed73350501 and replica9077 are retained from the earlier technical timing
driver; these are timing probes, not new independent scientific replicas.
L15/P16/m2 and a256 MiB observer budget match the preceding resource plan's
measurement baseline. There is no automatic duration increase or retry.

Scalar observations and full E1 context/joint snapshots occur only at0 and the
final step. Initial/final coordinate files remain. This intentionally removes
unnecessary scalar work for timing, while preserving every dynamics acquisition
at0,100,...,steps. There is no dense trajectory. A later production scalar
schedule, larger L19/L21 banks or other hardware can change runtime and memory.
These probes do not themselves authorize or establish resources for24 long runs.

## Recorded resource summary and limits

Each `n64/receipt.json` and `n128/receipt.json`, plus root `summary.json`, retains:

- Actual completed steps, production and child steps/s, child wall seconds from
  the supervisor and total per-run elapsed seconds including checks/inventory.
- Existing initialization, integration, production, observation, recurrent
  output, final output and force/diagnostic timers with their scope strings.
- Dynamics shared/extra readback seconds and bytes, acquisition CPU seconds and
  evaluation/CSV seconds. These scopes overlap; do not sum them as elapsed time.
- Peak recorded child host RSS in `process.max_rss_bytes` (Linux `wait4` maximum
  plus50 ms polling). Host supervisor RSS is not included.
- Reliable prelaunch device-wide total/free GPU memory and physical array byte
  accounting. `gpu_peak_memory_bytes` stays null: neither is a peak measurement.
- Output bytes and file SHA256/size inventory, logs, original argv/environment,
  process status, resource-limit violations and failure evidence.

Use `production_steps_per_second` for sustained estimates; the integration
CUDA-event timer excludes observations/output but includes force/update/hopping,
diagnostic transfers and launch/synchronization gaps. Production includes step0
acquisition and final force validation. It is the available sustained window,
not a regression fit. Initialization is separately timed. Main final-output
time excludes later equilibrium/dynamics publication; dynamics evaluation has
its own timer. `child_minus_production_seconds` includes all remaining startup,
finalization, telemetry and supervisor polling, so it is a residual, not a pure
initialization timer. Total elapsed also includes authentication and inventories.
Compare the100000 and optional1000000 results manually to assess fixed overhead
and throughput stability; do not infer stability from a single short measurement.

| Safeguard | Limit |
|---|---|
| Per child | 1800 s |
| Aggregate supervisor budget | 3900 s |
| Peak recorded child RSS | 2 GiB |
| Available host/cgroup memory before each launch | 8 GiB minimum |
| Available GPU memory before each launch | 1 GiB minimum, idle selected GPU |
| Per-run output including logs | 128 MiB |
| Aggregate evidence | 512 MiB |
| Free disk initially / maintained | 11 GiB / 10 GiB |

The supervisor enforces polled time/RSS/output/disk limits, per-file RLIMIT_FSIZE,
process-group termination and Linux parent-death protection. Polling can overshoot;
RSS is not a hard address-space or cgroup quota. Host headroom is checked before
each run; child RSS is monitored during execution. GPU free memory is a prelaunch
check only. The outer GNU timeout bounds parent checks and inventories too.
Failures stop the sequence, preserve outputs/logs/process records and write a
failed summary when storage permits. There is no tolerance change, replacement
run, checkpoint, resume, output adoption or overwriting. SIGTERM/HUP/interrupts
trigger evidence preservation; SIGKILL or full disk can prevent a final receipt.

## Identity and provenance

The executable must match SHA256
`54dc84a9aac35fd6574ce6e2890a6c8a0f545743fdc2bbd32bc0a70863dcf9ce`
before each launch and after completion. Its same-binary bounded correctness
summary must report `bounded_checks_completed`. No correctness suite is rerun.
The driver retains that summary, the existing `.d` dependency file, source
Makefile, implementation Git tree/blob identities, preparation HEAD and helper
sources with hashes. Additional existing build logs/settings may be passed with
repeatable `--build-provenance FILE`. It does not build, replace or copy over the
verified executable. The recorded implementation SHA is the verified source
identity supplied for this task; a tree listing is not a new compilation proof.

The local build directory currently contains the executable/dependency file but
no compiler transcript or build-settings receipt. This preparation cannot recover
missing historical toolchain evidence. That limitation is explicit in the output;
system compiler versions and the source Makefile are never called proof of the
actual historical compiler invocation. Existing external build records should be
supplied if available, without rebuilding or changing the verified binary.

## Exact local command after independent review

Linux prerequisites: Python3.9+ and NumPy (existing supervisor dependency), Git,
GNU timeout, nvidia-smi and the existing CUDA13 runtime. The default GPU is the
previously recorded sm86 UUID; another compatible local GPU can be selected with
`--gpu-uuid GPU-...`, and its identity is recorded. Use a new persistent output
root for each invocation. From any working directory:

```bash
timeout --signal=TERM --kill-after=15s 4000s python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d2a5_preflight.py --execute-reviewed-preflight --output /home/jramirez/UAMMD_KG-evidence/d2a5/sustained-100k-v1
```

Default verified executable:
`/home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/build/d2a5-review-v1/double/semiflexible`.
Default prior correctness record:
`/home/jramirez/UAMMD_KG-evidence/d2a5/bounded-v1/summary.json`.
Explicit `--binary`/`--correctness-summary` overrides still require the pinned hash
and completed same-binary checks. The output root must not already exist.

Only if the first measurements do not provide a stable sustained estimate,
and after reviewing their timers and budget use, the user may explicitly select
the longer window (10001 dynamics frames/configuration, unchanged time limits):

```bash
timeout --signal=TERM --kill-after=15s 4000s python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d2a5_preflight.py --execute-reviewed-preflight --steps 1000000 --output /home/jramirez/UAMMD_KG-evidence/d2a5/sustained-1m-v1
```

Do not launch the longer probe if the observed throughput predicts exceeding the
unchanged1800 s child budget. Request a separately reviewed budget instead.
Return both receipts, root summary and preserved provenance/logs for review.
No numerical throughput or new measured resource result is claimed here.

The prepared command-contract regression is intentionally unexecuted:

```bash
python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/tests/d2a5_preflight_regression.py
```

It checks both lengths/windows and fixed physical/acquisition flags without
launching subprocesses. It does not validate real supervision or GPU behavior.
