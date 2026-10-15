# Stage 2B — user-run Linux GPU validation

**IMPLEMENTED — AWAITING SCIENTIFIC VALIDATION.** Run these commands only on
the dedicated Linux GPU host, from the slip-springs repository root. None of
the long campaigns below was executed in Codex. CUDA 13 / RTX 3060 Ti commands
are shown; choose an architecture supported by your GPU if different.
Keep all logs, metadata, analysis JSON and compact CSV files for review.
No source edits are required; each run uses a fresh directory.

## Fixed criteria (declare before execution)

Mandatory scientific gates retain Stage 1/2A's **5 standard error** limit and
95% confidence intervals. Independent chains are clusters; time origins are
not independent observations. The six-channel g uncertainty includes their
covariance by forming g within each chain first. No tolerance is adjusted after
seeing results. `stream_analysis.py` checks g and all six normalized channels
against exact nonstationary finite-step **block-averaged** theory; raw normal
correlations/SE are divided by four only for comparison to shear theory.
Bins with fewer than eight pairs per chain are reported but excluded from
these scientific gates. A terminal check additionally requires bins within 25%
of both 2 and 4 stress relaxation times and positive signal exceeding 2 SE.
Failing that resolution criterion requires more independent data, not a looser
gate. Preserve a failed run and investigate before rerunning with more data.

Pipeline comparisons use rtol=atol=2e-11 for independent CPU reconstruction;
sync/async, batching and exact-seed replay within one precision must produce
byte-identical relaxation.csv. Float and double are compared statistically,
never pathwise. Finite-step bias and coarse averaging are included in each
reference, rather than attributed to precision.

## 1. Setup, builds and regression tests — mandatory

```sh
PROJECT=$(realpath examples/slip-springs)
RESULTS=$(mktemp -d /tmp/rouse-stage2b-host.XXXXXX)
export PROJECT RESULTS
printf 'Results: %s\n' "$RESULTS"
nvidia-smi > "$RESULTS/gpu.txt"
/usr/local/cuda/bin/nvcc --version > "$RESULTS/cuda.txt"
set -o pipefail
make -C "$PROJECT" check-lifetime 2>&1 | tee "$RESULTS/lifetime.log"
for precision in single double; do
  make -C "$PROJECT" check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION="$precision" 2>&1 | tee "$RESULTS/check-$precision.log"
done
# Long historical scientific regressions: HOST ONLY.
python3 "$PROJECT/validate.py" suite "$RESULTS/stage1" | tee "$RESULTS/stage1.log"
python3 "$PROJECT/stress.py" suite "$RESULTS/stage2a" | tee "$RESULTS/stage2a.log"
```

All tests and both historical summary.json files must pass. ASan/LSan must
report no leaks, invalid frees or access errors before large allocations.
Unchanged KG unused-persistence fscanf compiler warnings do not indicate a
runtime failure. Do not disable leak detection.

## 2. Matrix and Stage 2A agreement — mandatory

This also tests all N=8,32,100, dt=.01,.005,.0025, both precisions, with
identical physical workloads/seed across CSV, sync and async.

```sh
set -euo pipefail
for precision in single double; do
  for n in 8 32 100; do
    for dt in 0.01 0.005 0.0025; do
      base="$RESULTS/matrix-$precision-N$n-dt$dt"
      for mode in csv sync async; do
        extra=(--output-mode csv)
        if [ "$mode" != csv ]; then extra=(--output-mode stream --backend "$mode"); fi
        "$PROJECT/build/$precision/rouse" --springs "$n" --chains 1024 --dt "$dt" --steps 600 --sample 5 --equil 0 --seed 620032 --batch 7 --corr-levels 12 --corr-slots 16 --corr-m 2 "${extra[@]}" --output "$base-$mode" > "$base-$mode.log" 2>&1
      done
      python3 "$PROJECT/stress.py" analyze "$base-csv"
      python3 "$PROJECT/tests/test_stream.py" --compare "$base-csv" "$base-sync"
      python3 "$PROJECT/tests/test_stream.py" --compare "$base-csv" "$base-async"
      cmp "$base-sync/relaxation.csv" "$base-async/relaxation.csv"
      python3 "$PROJECT/stream_analysis.py" "$base-sync"
      python3 "$PROJECT/stream_analysis.py" "$base-async"
    done
  done
done
```

The CPU reconstruction checks every exported bin, including the finest exact
point lags and coarser **stress block means**, all raw channels/counts and paired
g SE. Stage 2A's own analysis remains an independent Gaussian-science baseline.

## 3. Terminal Rouse decay — mandatory, HOST ONLY (long)

80 slowest stress relaxation times; sampling approximately tau_stress/64.
No equilibration is required because initialization is exact equilibrium; the
reference includes EM variance evolution from the initial sample.

```sh
for precision in single double; do
  for n in 8 32 100; do
    read -r steps stride < <(python3 - "$n" <<'PY'
import math,sys
n=int(sys.argv[1]); dt=.005
stress_tau=1/(24*math.sin(math.pi/(2*(n+1)))**2)
print(math.ceil(80*stress_tau/dt),max(1,int(stress_tau/(64*dt))))
PY
)
    seed=620100; if [ "$precision" = double ]; then seed=620101; fi
    dest="$RESULTS/terminal-$precision-N$n"
    "$PROJECT/build/$precision/rouse" --springs "$n" --chains 2048 --dt .005 --steps "$steps" --sample "$stride" --equil 0 --seed "$seed" --output-mode stream --backend async --batch 64 --corr-levels 20 --corr-slots 16 --corr-m 2 --output "$dest" > "$dest.log" 2>&1
    python3 "$PROJECT/stream_analysis.py" "$dest" --terminal
done
done
```

Review continuous and EM predictions in stream_analysis.json, residuals and
confidence intervals, including terminal coverage/resolution flags. Values
`block_samples>1` compare to averaged theory; the continuous point prediction
alone is inappropriate there. Both precision runs must pass their own exact
reference; the existing regressions retain statistical precision comparison.
Terminal runs use different seeds in the two precisions. Compare matching bins
across float/double using combined independent SE (5 SE),
as automated below. Differences of EM references are removed first.

```sh
python3 "$PROJECT/tests/stage2b_compare.py" precision "$RESULTS"
```

## 4. Sampling sensitivity — mandatory, HOST ONLY

Same seed/dynamics, sample every 5,10,20 steps for a fixed 50,000-step N32
trajectory. Grids deliberately differ: compare each to its OWN block theory,
not raw coarse-bin equality. No independence is assumed between paired runs.

```sh
for stride in 5 10 20; do
  dest="$RESULTS/sampling-$stride"
  "$PROJECT/build/double/rouse" --springs 32 --chains 1024 --dt .005 --steps 50000 --sample "$stride" --equil 0 --seed 620032 --output-mode stream --backend async --batch 100 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$dest" > "$dest.log" 2>&1
  python3 "$PROJECT/stream_analysis.py" "$dest"
done
```

## 5. Buffer scaling, backend/CSV cost — mandatory comparison; tuning exploratory

Batch frames 100,500,1000 at stride10 represent about 1,000,5,000,10,000
integration steps. Same physical workload for every backend/batch, including
CSV. One pass suffices for correctness; repeat in fresh directories to assess
performance variability. No speedup threshold is a scientific gate. Prefer
sync if async does not measurably reduce total production cost.

```sh
for mode in csv sync async; do
  for batch in 100 500 1000; do
    dest="$RESULTS/performance-$mode-B$batch"
    extra=(--output-mode csv)
    if [ "$mode" != csv ]; then extra=(--output-mode stream --backend "$mode"); fi
    /usr/bin/time -v -o "$dest.time" "$PROJECT/build/single/rouse" --springs 32 --chains 512 --dt .005 --steps 20000 --sample 10 --equil 0 --seed 620032 --batch "$batch" --corr-levels 16 --corr-slots 16 --corr-m 2 "${extra[@]}" --output "$dest" > "$dest.log" 2>&1
  done
done
for mode in sync async; do
  for batch in 100 500 1000; do
    cmp "$RESULTS/performance-sync-B100/relaxation.csv" "$RESULTS/performance-$mode-B$batch/relaxation.csv"
  done
done
python3 "$PROJECT/tests/stage2b_compare.py" performance "$RESULTS"
```

Compare production wall cost and GPU integration ns/bead/step separately.
CSV cost includes repeated text output. Streaming final evaluate/write is
separate; measured_simulation_seconds includes initialization/equilibration and
final output, excluding metadata, terminal logging and resource destruction.
Async worker, GPU integration, sampling and transfer timers overlap: never add
them to infer elapsed time. Record buffer/transfer wait times and host RSS.

## 6. Memory stability and reproducibility — mandatory, HOST ONLY

This is the only long memory test; do not run it in Codex. RSS includes normal
allocator retention; after startup, neither RSS nor GPU memory should have a
positive trend proportional to processed frames. Allow a fixed 32 MiB RSS
allocator/noise band after the first 10% of samples; investigate larger growth.
GPU allocation should remain constant after setup (nvidia-smi rounding aside).
Preserve the raw time series. Process repetition plus LSan tests resource
release; it cannot replace the within-process check below.

```sh
dest="$RESULTS/memory"
"$PROJECT/build/single/rouse" --springs 32 --chains 512 --dt .005 --steps 1000000 --sample 10 --equil 0 --seed 620032 --output-mode stream --backend async --batch 100 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$dest" > "$dest.log" 2>&1 &
sim_pid=$!
printf 'utc rss_kib\n' > "$RESULTS/rss.txt"
while kill -0 "$sim_pid" 2>/dev/null; do
  printf '%s ' "$(date -u +%s)" >> "$RESULTS/rss.txt"
  ps -o rss= -p "$sim_pid" >> "$RESULTS/rss.txt" || true
  nvidia-smi --query-compute-apps=pid,used_gpu_memory --format=csv,noheader >> "$RESULTS/gpu-memory.txt"
  sleep 2
done
wait "$sim_pid"
python3 "$PROJECT/stream_analysis.py" "$dest"
for repeat in 1 2; do
  "$PROJECT/build/single/rouse" --springs 8 --chains 64 --dt .005 --steps 200 --sample 10 --equil 7 --seed 620008 --output-mode stream --backend async --batch 7 --corr-levels 8 --corr-slots 16 --corr-m 2 --output "$RESULTS/replay-$repeat" > "$RESULTS/replay-$repeat.log" 2>&1
done
cmp "$RESULTS/replay-1/relaxation.csv" "$RESULTS/replay-2/relaxation.csv"
```

Success requires all mandatory checks and review of actual artifacts, not just
exit status. Timings/metadata naturally vary on replay; relaxation.csv must not.
Send the reports, summary JSON, RSS/GPU memory logs and performance table for
review. Scientific acceptance and selection of the production backend remain
pending that review. Do not start the next stage automatically.
