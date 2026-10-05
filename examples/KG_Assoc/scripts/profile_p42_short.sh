#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$repo_root"
: "${INPUT:?set INPUT to a chemically valid C1 .restart.lammpsdat file}"
case "$INPUT" in
  *.restart.lammpsdat) restart_prefix=${INPUT%.restart.lammpsdat} ;;
  *) echo "INPUT must name a .restart.lammpsdat file" >&2; exit 2 ;;
esac
[[ -r "$restart_prefix.assoc_restart" ]] || exit 2

profile_root=${P42_PROFILE_DIR:-p42_profile_short}
mkdir -p "$profile_root"
workdir=$(mktemp -d "$profile_root/run.XXXXXX")
steps=${P42_STEPS:-2000}
nsys=${NSYS:-nsys}

fail() {
  echo "P4.2 profiling failed: $1" >&2
  echo "Incomplete profiling run directory: $workdir" >&2
  exit 1
}

require_target_success() {
  local label=$1
  local output_prefix=$2
  local log_path=$3
  if ! grep -Fxq 'STAR_ASSOCIATION_SMOKE PASS' "$log_path"; then
    fail "$label target did not report success"
  fi
  if [[ ! -s "$output_prefix.state" || ! -s "$output_prefix.assoc_restart" ||
        ! -s "$output_prefix.restart.lammpsdat" ]]; then
    fail "$label target is missing completion artifacts"
  fi
}

extract_cuda_stats() {
  local label=$1
  local report_path="$workdir/$label.nsys-rep"
  local stats_path="$workdir/$label.stats.txt"
  "$nsys" stats --force-export=true --report cuda_api_sum,cuda_gpu_kern_sum,osrt_sum \
    "$report_path" > "$stats_path"
  if grep -Fq 'SKIPPED:' "$stats_path" ||
      ! grep -Fq 'CUDA API Summary' "$stats_path" ||
      ! grep -Fq 'CUDA GPU Kernel Summary' "$stats_path"; then
    fail "$label report has no usable CUDA profiling data"
  fi
}

make -B -C examples/KG_Assoc kg_assoc_stars kg_assoc_production

# Same restart, steps, physics, and GPU. These are short captures only.
"$nsys" profile --force-overwrite=true --trace=cuda,nvtx,osrt --stats=true \
  -o "$workdir/baseline" -- \
  ./examples/KG_Assoc/kg_assoc_stars --restart-prefix "$restart_prefix" \
    --steps "$steps" --output "$workdir/baseline_output" \
    > "$workdir/baseline.target.log" 2>&1
require_target_success baseline "$workdir/baseline_output" "$workdir/baseline.target.log"
"$nsys" profile --force-overwrite=true --trace=cuda,nvtx,osrt --stats=true \
  -o "$workdir/production" -- \
  ./examples/KG_Assoc/kg_assoc_production --restart-prefix "$restart_prefix" \
    --steps "$steps" --output "$workdir/production_output" \
    > "$workdir/production.target.log" 2>&1
require_target_success production "$workdir/production_output" "$workdir/production.target.log"

extract_cuda_stats baseline
extract_cuda_stats production

if [[ "${NSIGHT_COMPUTE:-0}" == 1 ]]; then
  ncu=${NCU:-ncu}
  "$ncu" --target-processes all --set full \
    -o "$workdir/production_ncu" -- \
    ./examples/KG_Assoc/kg_assoc_production --restart-prefix "$restart_prefix" \
      --steps "${NCU_STEPS:-100}" --output "$workdir/production_ncu_output"
fi

echo "P4.2 profiling run directory: $workdir"
echo "Compare baseline.stats.txt and production.stats.txt for launches,"
echo "synchronization, device-host copies, and dominant kernels."
