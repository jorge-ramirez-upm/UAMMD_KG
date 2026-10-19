#!/usr/bin/env bash
# Bounded host-only evidence runner. Results are intentionally outside all campaigns.
set -u -o pipefail

project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
expected="ac468c7d17af697663eae6211f5419a484059baa"
protected="4e46d6014aa812b1fc687335654c4b1f681ddd22"
cuda_home="${CUDA_HOME:-/usr/local/cuda-13.0}"
host_cxx="${CXX:-g++}"
result_root="${STAGE4A3C_RESULTS_ROOT:-/tmp/stage4a3c-gpu-validation-$(date -u +%Y%m%dT%H%M%SZ)}"

fail(){ echo "FAIL: $*" >&2; exit 1; }
[[ "$PWD" == "/tmp/UAMMD_KG-slip-springs-dev" ]] || fail "run only from /tmp/UAMMD_KG-slip-springs-dev"
[[ -d "$cuda_home" && -x "$cuda_home/bin/nvcc" ]] || fail "CUDA_HOME must name a CUDA Toolkit installation"
[[ ! -e "$result_root" ]] || fail "refusing to overwrite evidence directory: $result_root"
git -C "$PWD" diff --quiet || fail "worktree is not clean"
git -C "$PWD" diff --cached --quiet || fail "index is not clean"
git -C "$PWD" merge-base --is-ancestor "$expected" HEAD || fail "benchmark baseline is absent from HEAD"
mkdir -p "$result_root/logs"

status="$result_root/status.tsv"
printf 'name\texit_code\n' > "$status"
record(){ local name="$1"; shift; printf '%q ' "$@" > "$result_root/commands/$name.cmd"; printf '\n' >> "$result_root/commands/$name.cmd"; }
run(){ local name="$1"; shift; mkdir -p "$result_root/commands"; record "$name" "$@"; timeout 120s "$@" >"$result_root/logs/$name.log" 2>&1; local code=$?; printf '%s\t%s\n' "$name" "$code" >> "$status"; return "$code"; }
capture(){ local name="$1"; shift; run "$name" "$@" || fail "${name}; inspect $result_root/logs/$name.log"; }

capture git-head git -C "$PWD" rev-parse HEAD
capture git-status git -C "$PWD" status --short --branch
capture protected-a git -C /tmp/UAMMD_KG-slip-springs rev-parse HEAD
capture protected-b git -C /tmp/UAMMD_KG-stage4a3c-exec rev-parse HEAD
capture protected-a-status git -C /tmp/UAMMD_KG-slip-springs status --short
capture protected-b-status git -C /tmp/UAMMD_KG-stage4a3c-exec status --short
[[ "$(<"$result_root/logs/protected-a.log")" == "$protected" ]] || fail "first protected checkout is not pinned"
[[ "$(<"$result_root/logs/protected-b.log")" == "$protected" ]] || fail "second protected checkout is not pinned"
[[ ! -s "$result_root/logs/protected-a-status.log" && ! -s "$result_root/logs/protected-b-status.log" ]] || fail "protected checkout is dirty"
capture nvidia-smi nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
capture nvcc "$cuda_home/bin/nvcc" --version
capture compiler "$host_cxx" --version
capture os uname -a
capture cpu nproc
capture load uptime
grep -q 'release 13\.0' "$result_root/logs/nvcc.log" || fail "CUDA Toolkit 13.0 is required"

make_args=(make -C "$project" "CUDA_HOME=$cuda_home" "CXX=$host_cxx")
capture build-single "${make_args[@]}" PRECISION=single semiflexible every-step-gpu-benchmark "$project/build/semiflexible_stress_correlator"
capture build-double "${make_args[@]}" PRECISION=double semiflexible every-step-gpu-benchmark
for binary in "$project/build/single/semiflexible" "$project/build/double/semiflexible" "$project/build/single/every_step_gpu_stress_benchmark" "$project/build/double/every_step_gpu_stress_benchmark" "$project/build/semiflexible_stress_correlator"; do
  [[ -x "$binary" ]] || fail "missing expected executable: $binary"
  sha256sum "$binary" >> "$result_root/binary-sha256.txt"
done

# Run each precision as primary: this exercises the prescribed-coordinate oracle,
# stress on/off replay, zero-bending path and incomplete streaming batches.
capture oracle-single python3 "$project/tests/test_semiflexible_stress_gpu.py" "$project/build/single/semiflexible" "$project/build/semiflexible_stress_correlator" "$project/build/double/semiflexible"
capture oracle-double python3 "$project/tests/test_semiflexible_stress_gpu.py" "$project/build/double/semiflexible" "$project/build/semiflexible_stress_correlator" "$project/build/single/semiflexible"
for precision in single double; do
  capture "replay-$precision" env SEMIFLEXIBLE_GPU_BIN="$project/build/$precision/semiflexible" EVERY_STEP_GPU_BENCHMARK_BIN="$project/build/$precision/every_step_gpu_stress_benchmark" SEMIFLEXIBLE_STRESS_FIXTURE="$project/build/semiflexible_stress_correlator" python3 "$project/tests/test_every_step_gpu_stress_benchmark.py"
done

printf 'PASS\n' > "$result_root/RESULT"
printf 'PASS: evidence=%s\n' "$result_root"
