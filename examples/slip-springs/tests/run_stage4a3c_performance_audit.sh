#!/usr/bin/env bash
# User-run, bounded performance audit. Writes only to a new /tmp evidence root.
set -u -o pipefail
project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cuda_home="${CUDA_HOME:-/usr/local/cuda-13.0}"; host_cxx="${CXX:-g++}"
root="${STAGE4A3C_AUDIT_ROOT:-/tmp/stage4a3c-performance-audit-$(date -u +%Y%m%dT%H%M%SZ)}"
[[ "$PWD" == /tmp/UAMMD_KG-slip-springs-dev ]] || { echo "run from development worktree" >&2; exit 1; }
[[ ! -e "$root" && -x "$cuda_home/bin/nvcc" ]] || { echo "new root and CUDA_HOME required" >&2; exit 1; }
"$cuda_home/bin/nvcc" --version | grep -q 'release 13\.0' || { echo "CUDA 13.0 required" >&2; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "clean worktree required" >&2; exit 1; }
mkdir -p "$root/logs"; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader > "$root/gpu.txt"
"$cuda_home/bin/nvcc" --version > "$root/nvcc.txt"; "$host_cxx" --version > "$root/compiler.txt"; uptime > "$root/load-start.txt"
for precision in single double; do timeout 120s make -C "$project" "CUDA_HOME=$cuda_home" "CXX=$host_cxx" PRECISION="$precision" semiflexible > "$root/logs/build-$precision.log" 2>&1 || exit $?; done
g++ -O2 -std=c++17 -pthread "$project/tests/stress_throughput.cpp" "$project/../KG/correlator.cpp" -o "$root/stress_throughput"
for cfg in "64 20" "32 24"; do set -- $cfg; slots="$1"; levels="$2"; for rep in 1 2 3; do
  timeout 120s "$root/stress_throughput" 2048 "$slots" "$levels" 8 256 100 2001 "$root/cpu-p${slots}-l${levels}-r${rep}" 0 $((512*1024*1024)) chain > "$root/logs/cpu-p${slots}-l${levels}-r${rep}.log" 2>&1 || exit $?
done; done
for precision in single double; do for n in 8 32; do for kappa in 0 10; do for cfg in "64 20" "32 24"; do set -- $cfg; slots="$1"; levels="$2"; for rep in 1 2 3; do
  out="$root/gpu-${precision}-n${n}-k${kappa}-p${slots}-l${levels}-r${rep}"
  timeout 120s "$project/build/$precision/semiflexible" --output "$out" --springs "$n" --chains 2048 --steps 2000 --sample 2000 --dt .000025 --seed $((433300+rep)) --kappa "$kappa" --stress-mode every-step --stress-batch 256 --cpu-workers 8 --corr-slots "$slots" --corr-levels "$levels" --correlator-mib 512 > "$root/logs/$(basename "$out").log" 2>&1 || exit $?
done; done; done; done; done
python3 - "$root" <<'PY'
import csv,json,pathlib,sys
r=pathlib.Path(sys.argv[1]); rows=[]
for path in sorted(r.glob('gpu-*/stress_metadata.json')):
 d=json.loads(path.read_text()); d['run']=path.parent.name; rows.append(d)
fields=['run','frames','slots','levels','batch','cpu_workers','gpu_stress_seconds','stress_transfer_seconds','stress_transfer_completion_wait_seconds','stress_consumer_idle_seconds','stress_diagnostic_wait_seconds','cpu_correlation_seconds','cpu_barrier_seconds','cpu_worker_execution_sum_seconds','buffer_wait_seconds','producer_blocked_seconds','max_inflight_slots','queue_slot_capacity','estimated_bytes']
with (r/'gpu-summary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fields);w.writeheader();w.writerows([{k:x.get(k) for k in fields} for x in rows])
PY
echo "PASS audit evidence: $root"
