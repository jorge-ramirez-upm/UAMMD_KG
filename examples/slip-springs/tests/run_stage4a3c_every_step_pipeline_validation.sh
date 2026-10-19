#!/usr/bin/env bash
# Bounded Milestone-B validation; no campaign or production trajectory is launched.
set -u -o pipefail
project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cuda_home="${CUDA_HOME:-/usr/local/cuda-13.0}"
host_cxx="${CXX:-g++}"
[[ "$PWD" == "/tmp/UAMMD_KG-slip-springs-dev" ]] || { echo "run from the development worktree" >&2; exit 1; }
[[ -x "$cuda_home/bin/nvcc" ]] || { echo "CUDA_HOME must be CUDA 13.0" >&2; exit 1; }
"$cuda_home/bin/nvcc" --version | grep -q 'release 13\.0' || { echo "CUDA 13.0 required" >&2; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "clean worktree required" >&2; exit 1; }
for p in single double; do
  timeout 120s make -C "$project" "CUDA_HOME=$cuda_home" "CXX=$host_cxx" PRECISION="$p" semiflexible
  timeout 120s python3 "$project/tests/test_semiflexible_every_step_gpu.py" "$project/build/$p/semiflexible"
done
performance_root="$(mktemp -d /tmp/stage4a3c-every-step-performance-XXXXXX)"
timeout 120s "$project/build/single/semiflexible" --output "$performance_root/run" --springs 8 --chains 2048 \
  --steps 10000 --sample 10000 --dt .000025 --seed 433202 --kappa 10 --stress-mode every-step \
  --stress-batch 256 --cpu-workers 4 --corr-levels 12 --corr-slots 64 --correlator-mib 512
echo "PERFORMANCE_EVIDENCE=$performance_root/run/stress_metadata.json"
echo "PASS bounded every-step pipeline validation"
