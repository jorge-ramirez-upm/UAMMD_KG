#!/usr/bin/env bash
# User-invoked Stage 4A.4 N=8 screen.  Default: provenance preflight only.
set -euo pipefail

project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
development=/tmp/UAMMD_KG-slip-springs-dev
protected_sha=4e46d6014aa812b1fc687335654c4b1f681ddd22
cuda_home="${CUDA_HOME:-/usr/local/cuda-13.0}"
execute=false
root=""
physical_duration=20
limit_seconds=900

fail(){ printf 'FAIL: %s\n' "$*" >&2; exit 1; }
while (($#)); do
  case "$1" in
    --execute-first-screen) execute=true ;;
    --root) shift; (($#)) || fail '--root needs a value'; root="$1" ;;
    --help) printf 'usage: %s [--execute-first-screen] [--root NEW_ABSOLUTE_DIRECTORY]\n' "$0"; exit 0 ;;
    *) fail "unknown argument: $1" ;;
  esac
  shift
done
[[ "$(pwd -P)" == "$development" && "$project" == "$development/examples/slip-springs" ]] || fail "run only from $development"
[[ "$(git rev-parse --abbrev-ref HEAD)" == slip-springs ]] || fail 'slip-springs branch required'
git diff --quiet && git diff --cached --quiet && [[ -z "$(git status --porcelain)" ]] || fail 'clean worktree required'
for protected in /tmp/UAMMD_KG-slip-springs /tmp/UAMMD_KG-stage4a3c-exec; do
  [[ "$(git -C "$protected" rev-parse HEAD)" == "$protected_sha" ]] || fail "protected checkout not pinned: $protected"
  [[ -z "$(git -C "$protected" status --porcelain)" ]] || fail "protected checkout dirty: $protected"
done
[[ -x "$cuda_home/bin/nvcc" && -x "$project/build/double/semiflexible" ]] || fail 'CUDA 13.0 and double simulator required'
"$cuda_home/bin/nvcc" --version | grep -q 'release 13\.0' || fail 'CUDA Toolkit 13.0 required'
command -v nvidia-smi >/dev/null && command -v timeout >/dev/null && [[ -x /usr/bin/time ]] || fail 'nvidia-smi, timeout, and /usr/bin/time required'

if [[ -z "$root" ]]; then root="$(mktemp -d /tmp/stage4a4-timestep-preflight.XXXXXX)"
else [[ "$root" = /* && ! -e "$root" ]] || fail '--root must be a new absolute directory'; mkdir -p "$root"; fi
mkdir -p "$root"/{commands,environment,logs,receipts,references}
git rev-parse HEAD > "$root/environment/git-head.txt"; git status --short --branch > "$root/environment/git-status.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader > "$root/environment/gpu.txt"
"$cuda_home/bin/nvcc" --version > "$root/environment/nvcc.txt"; uname -a > "$root/environment/os.txt"; uptime > "$root/environment/load.txt"
sha256sum "$project/build/double/semiflexible" > "$root/environment/executable.sha256"
"$project/build/double/semiflexible" --help > "$root/environment/semiflexible-help.txt"
printf 'mode=%s\nphysical_duration=%s\ntimeout_seconds_per_run=%s\nrestart=unsupported\n' \
  "$([[ "$execute" == true ]] && printf first-screen || printf preflight)" "$physical_duration" "$limit_seconds" > "$root/receipts/preflight.tsv"
if [[ "$execute" != true ]]; then printf 'PREFLIGHT_PASS evidence=%s\n' "$root"; exit 0; fi

run_case(){
  local kappa="$1" dt="$2" sample="$3" tag="N8-k${1}-dt${2}" steps out code kind
  steps="$(python3 -c "print(round($physical_duration/$dt))")"
  out="$root/run-double-${tag}"; [[ ! -e "$out" ]] || fail "output exists: $out"
  python3 "$project/tests/stage4a4_equilibrium_reference.py" --springs 8 --kappa "$kappa" --chains 65536 --seed 440401 --report "$root/references/${tag}.json" > "$root/logs/${tag}-reference.log"
  local argv=("$project/build/double/semiflexible" --output "$out" --springs 8 --chains 512 --b0 1 --kb 30 --kappa "$kappa" --dt "$dt" --steps "$steps" --sample "$sample" --seed 433201 --stress-mode every-step --stress-batch 256 --cpu-workers 8 --corr-levels 20 --corr-slots 32 --corr-m 2 --correlator-mib 512 --scalar-output full)
  printf '%q ' "${argv[@]}" > "$root/commands/${tag}.cmd"; printf '\n' >> "$root/commands/${tag}.cmd"
  nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader > "$root/environment/${tag}-gpu-before.csv"
  set +e
  timeout --foreground --signal=TERM --kill-after=20s "${limit_seconds}s" /usr/bin/time -v -o "$root/receipts/${tag}.time.txt" "${argv[@]}" > "$root/logs/${tag}.log" 2>&1
  code=$?
  set -e
  case "$code" in 0) kind=completed;; 124) kind=timeout;; 130|143) kind=interrupted;; *) kind=application_failure;; esac
  nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader > "$root/environment/${tag}-gpu-after.csv" || true
  printf 'status=%s\nexit_code=%s\ntimeout_seconds=%s\nsteps=%s\nphysical_duration=%s\noutput=%s\npartial_evidence_preserved=true\nrestart=unsupported\n' "$kind" "$code" "$limit_seconds" "$steps" "$physical_duration" "$out" > "$root/receipts/${tag}.tsv"
  [[ "$code" == 0 ]] || exit "$code"
  python3 "$project/tests/stage4a4_timestep_analysis.py" "$out" --reference "$root/references/${tag}.json" --report "$root/receipts/${tag}-static.json" > "$root/logs/${tag}-analysis.log" 2>&1
}

# Bracketing first screen: conservative reference and a deliberately coarse candidate.
run_case 0 .000025 400
run_case 0 .001 10
run_case 10 .000025 400
run_case 10 .001 10
printf 'FIRST_SCREEN_PASS evidence=%s\n' "$root"
