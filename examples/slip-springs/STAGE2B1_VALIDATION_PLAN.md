# Stage 2B.1 Linux-host validation (user-run only)

**STAGE 2B.1 IMPLEMENTED — AWAITING LINUX-HOST VALIDATION**

Run from the repository root on the dedicated Linux GPU host. Do not run this
performance campaign in Codex. Stage 2B's reported 54-run matrix and N32 terminal
504/504 checks are the scientific starting point supplied by the user. Preserve
all historical scientific thresholds; no resampling or estimator changes are
permitted. Performance acceptance requires reviewing actual host results.

## Setup and bounded regression

```bash
set -euo pipefail
PROJECT=$(realpath examples/slip-springs)
RESULTS=$(mktemp -d /tmp/rouse-stage2b1-host.XXXXXX)
export PROJECT RESULTS
nvidia-smi > "$RESULTS/gpu.txt"
lscpu > "$RESULTS/cpu.txt"
cat /proc/self/status > "$RESULTS/process.txt"
cat /proc/self/cgroup > "$RESULTS/cgroup.txt"
make -C "$PROJECT" check-lifetime
for precision in single double; do
  make -C "$PROJECT" check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION="$precision" > "$RESULTS/check-$precision.log" 2>&1
done
```

Use the appropriate CUDA architecture for your GPU. `check` includes the small
ASan/UBSan/LSan worker tests, serial-reference and 1/2/4/8-worker byte comparisons,
invalid CLI guards and both streaming backends. No scientific tolerance changes.
To check against the exact historical executable without switching branches:

```bash
mkdir -p "$PROJECT/build/reference"
for f in rouse.cu rouse.cuh stream_correlator.h stream_pipeline.cuh; do
  git show "6aadcc7edd6f2cfbb4051654b1a0dd881fd44718:examples/slip-springs/$f" > "$PROJECT/build/reference/$f"
done
# Read-only KG include dependency for the archived headers.
ln -s ../../KG "$PROJECT/build/KG" 2>/dev/null || test -e "$PROJECT/build/KG/correlator.h"
for precision in single double; do
  flags=(); if [ "$precision" = double ]; then flags=(-DDOUBLE_PRECISION); fi
  /usr/local/cuda/bin/nvcc -ccbin=g++ -I src -I src/third_party -O2 -std=c++17 --extended-lambda -arch=sm_86 "${flags[@]}" -DSLIP_SPRINGS_DIR="\"$PROJECT\"" "$PROJECT/build/reference/rouse.cu" examples/KG/correlator.cpp -Xcompiler -pthread -o "$PROJECT/build/reference/rouse-$precision"
  python3 "$PROJECT/tests/stage2b1_regression.py" "$PROJECT/build/reference/rouse-$precision" "$PROJECT/build/$precision/rouse"
done
```

## Main worker sweep, fixed physical workload

4096 independent N32 chains, 80,000 steps, dt .005, stress every 20 steps,
L20/p16/m2 and batch128, identical seed per precision and worker count. Float
and double trajectories need not agree pathwise. Execute runs sequentially;
repeat the whole block with a fresh RESULTS directory to assess variability.
If the machine cannot support 16 workers efficiently, retain the measurement
as oversubscription evidence rather than silently changing N. Explicit N is
allowed above CPU availability, but rejected above chain count or 1024.

```bash
for precision in single double; do
  for workers in 1 2 4 8 12 16; do
    dest="$RESULTS/$precision-w$workers-b128"
    /usr/bin/time -v -o "$dest.time" "$PROJECT/build/$precision/rouse" --springs 32 --chains 4096 --dt .005 --steps 80000 --sample 20 --equil 0 --seed 620032 --output-mode stream --backend async --cpu-workers "$workers" --batch 128 --corr-levels 20 --corr-slots 16 --corr-m 2 --output "$dest" > "$dest.log" 2>&1
    cmp "$RESULTS/$precision-w1-b128/relaxation.csv" "$dest/relaxation.csv"
    python3 "$PROJECT/stream_analysis.py" "$dest" --terminal
  done
done
```

Require byte-identical curves within each precision, including SE and counts.
The unchanged analyzer retains the 5-SE analytical gates and terminal coverage
requirements. Any scientific failure must be investigated before acceptance.
Primary performance metric: overall production ns/bead/step. Check GPU
integration separately; execution sums are not elapsed processing time.

## Small batch sensitivity extension

Only single precision, worker counts 1 and 8; reuse batch128 from above.

```bash
for workers in 1 8; do
  for batch in 32 512; do
    dest="$RESULTS/single-w$workers-b$batch"
    /usr/bin/time -v -o "$dest.time" "$PROJECT/build/single/rouse" --springs 32 --chains 4096 --dt .005 --steps 80000 --sample 20 --equil 0 --seed 620032 --output-mode stream --backend async --cpu-workers "$workers" --batch "$batch" --corr-levels 20 --corr-slots 16 --corr-m 2 --output "$dest" > "$dest.log" 2>&1
    cmp "$RESULTS/single-w1-b128/relaxation.csv" "$dest/relaxation.csv"
  done
done
```

## Compact performance table

Peak RSS is process-wide (KiB, includes initialization/output); other times are
production scopes. Speedup uses the same precision and batch's one-worker run.

```bash
python3 - "$RESULTS" <<'PY'
import csv,json,re,sys
from pathlib import Path
root=Path(sys.argv[1]); rows=[]
for path in sorted(root.glob('*-w*-b*/metadata.json')):
    m=json.loads(path.read_text()); name=path.parent.name
    match=re.fullmatch(r'(single|double)-w\d+-b(\d+)',name)
    if not match: continue
    rss=None; timefile=root/(name+'.time')
    if timefile.exists():
        hit=re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',timefile.read_text())
        if hit: rss=int(hit[1])
    rows.append((match[1],int(match[2]),m,rss))
base={(p,b):m['overall_ns_per_bead_step'] for p,b,m,rss in rows if m['cpu_workers_effective']==1}
out=csv.writer(sys.stdout)
out.writerow(['precision','batch','workers','overall_ns/bead/step','GPU_ns/bead/step','correlation_wall_s','buffer_wait_s','production_s','peak_RSS_KiB','speedup'])
for p,b,m,rss in rows:
    out.writerow([p,b,m['cpu_workers_effective'],m['overall_ns_per_bead_step'],m['integration_ns_per_bead_step'],m['cpu_correlation_wall_seconds'],m['buffer_wait_seconds'],m['production_seconds'],rss,base[p,b]/m['overall_ns_per_bead_step']])
PY
```

## Memory stability and replay (HOST ONLY)

One within-process extension using 8 workers and the same chain/sample settings.
This is deliberately separate from the performance sweep. Do not compare its
curve bytewise to the shorter workload. RSS after startup must stay within the
established 32 MiB allocator/noise band, without growth proportional to frames;
GPU allocation should stay constant. Preserve raw observations.

```bash
dest="$RESULTS/memory"
"$PROJECT/build/single/rouse" --springs 32 --chains 4096 --dt .005 --steps 1000000 --sample 20 --equil 0 --seed 620032 --output-mode stream --backend async --cpu-workers 8 --batch 128 --corr-levels 20 --corr-slots 16 --corr-m 2 --output "$dest" > "$dest.log" 2>&1 &
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
  "$PROJECT/build/double/rouse" --springs 8 --chains 17 --dt .005 --steps 200 --sample 10 --equil 0 --seed 620008 --output-mode stream --backend async --cpu-workers 8 --batch 7 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$RESULTS/replay-$repeat" > "$RESULTS/replay-$repeat.log" 2>&1
done
cmp "$RESULTS/replay-1/relaxation.csv" "$RESULTS/replay-2/relaxation.csv"
```

Send the table, metadata, logs, analyses and memory traces for review. No fixed
speedup is promised on heterogeneous CPUs. Stage 3 remains unauthorized.
