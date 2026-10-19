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

## Pilot matrix

The pilot uses the existing exact radial/conditional equilibrium initializer;
there is no artificial burn-in. Each run retains step 0 and acquires all six
stress channels at every integration step. Correlations use all stress frames;
stationarity and scalar summaries use the existing final-half diagnostics.

| phase | N | κ | precision | chains | replicas/seeds | duration | steps at dt=2.5e-5 | stress hierarchy |
|---|---:|---:|---|---:|---|---:|---:|---|
| screening/measurement | 8 | 0, 10 | double | 512 | 2: 433201, 433202 | 200 | 8,000,000 | 32×20, m=2 |
| screening/measurement | 32 | 0, 10 | double | 512 | 2: 433201, 433202 | 4,000 | 160,000,000 | 32×24, m=2 |
| precision confirmation | resolved cases only | same κ | single | 512 | seed 433201 | same | same | same |

The first four double-precision runs are the minimum physical pilot. The
single-precision confirmation is deliberately conditional: it is run only for
cases whose double-precision result passes the relaxation gates, avoiding a
full 16-run precision matrix before the unknown times are established. A
failure of the precision comparison is itself a pilot outcome and blocks
campaign design.

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
uncertain. Set a hard per-run wall limit of 12 hours for N=32 and 30 minutes
for N=8; stop, preserve the partial evidence, and review if a limit is reached.
No larger buffer or duration is authorized to mask backpressure.

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

The following commands are preparation/execution commands for the user’s CUDA
host only. They must not be run in either protected checkout. Review the
preflight output before setting `RUN=1`.

```sh
set -eu
ROOT=/tmp/stage4a3c-nonlinear-pilot-$(date -u +%Y%m%dT%H%M%SZ)
REPO=/tmp/UAMMD_KG-slip-springs-dev
mkdir -p "$ROOT"
cd "$REPO"
test "$(git rev-parse HEAD)" = 8a2f40078f45206aa1b432a84ea38f4f9885a9b5
git status --short
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
sha256sum build/double/semiflexible build/single/semiflexible
build/double/semiflexible --help > "$ROOT/double.help.txt"
build/single/semiflexible --help > "$ROOT/single.help.txt"
```

After independent review, the bounded double-precision pilot commands are:

```sh
set -eu
ROOT=/tmp/stage4a3c-nonlinear-pilot-REPLACE_TIMESTAMP
REPO=/tmp/UAMMD_KG-slip-springs-dev
for spec in '8 0 200 8000000 20' '8 10 200 8000000 20' '32 0 4000 160000000 24' '32 10 4000 160000000 24'; do
  set -- $spec; N=$1; K=$2; T=$3; STEPS=$4; LEVELS=$5
  for SEED in 433201 433202; do
    OUT="$ROOT/double-N${N}-k${K}-seed${SEED}"
    printf '%s\n' "$REPO/build/double/semiflexible --output $OUT --springs $N --chains 512 --b0 1 --kb 30 --kappa $K --dt .000025 --steps $STEPS --sample 400 --seed $SEED --stress-mode every-step --stress-batch 256 --cpu-workers 8 --corr-levels $LEVELS --corr-slots 32 --corr-m 2 --correlator-mib 512 --scalar-output compact" > "$ROOT/command-N${N}-k${K}-seed${SEED}.txt"
    sha256sum "$REPO/build/double/semiflexible" > "$ROOT/executable-N${N}-k${K}-seed${SEED}.sha256"
    (/usr/bin/time -v "$REPO/build/double/semiflexible" --output "$OUT" --springs "$N" --chains 512 --b0 1 --kb 30 --kappa "$K" --dt .000025 --steps "$STEPS" --sample 400 --seed "$SEED" --stress-mode every-step --stress-batch 256 --cpu-workers 8 --corr-levels "$LEVELS" --corr-slots 32 --corr-m 2 --correlator-mib 512 --scalar-output compact) > "$OUT/run.log" 2>&1
  done
done
```

The single-precision confirmation substitutes `build/single/semiflexible`,
uses one seed (`433201`), and is run only for cases passing the double gates.
The command text and output directory must be changed to a fresh root.

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
