#!/usr/bin/env bash
# Bounded, user-invoked Stage 4A.3c nonlinear pilot preflight/Stage-A runner.
set -euo pipefail

project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
development=/tmp/UAMMD_KG-slip-springs-dev
protected_sha=4e46d6014aa812b1fc687335654c4b1f681ddd22
cuda_home="${CUDA_HOME:-/usr/local/cuda-13.0}"
host_cxx="${CXX:-g++}"
execute=false
root=""
steps=100000
limit_seconds=300

fail(){ printf 'FAIL: %s\n' "$*" >&2; exit 1; }
usage(){ printf 'usage: %s [--execute-stage-a] [--root NEW_ABSOLUTE_DIRECTORY]\n' "$0"; }
while (($#)); do
  case "$1" in
    --execute-stage-a) execute=true ;;
    --root) shift; (($#)) || fail '--root needs a value'; root="$1" ;;
    --help) usage; exit 0 ;;
    *) fail "unknown argument: $1" ;;
  esac
  shift
done

[[ "$(pwd -P)" == "$development" ]] || fail "run only from $development"
[[ "$project" == "$development/examples/slip-springs" ]] || fail 'runner location/worktree mismatch'
[[ "$(git rev-parse --abbrev-ref HEAD)" == slip-springs ]] || fail 'slip-springs branch required'
git diff --quiet || fail 'worktree is not clean'
git diff --cached --quiet || fail 'index is not clean'
[[ -z "$(git status --porcelain)" ]] || fail 'untracked files are not allowed'
for protected in /tmp/UAMMD_KG-slip-springs /tmp/UAMMD_KG-stage4a3c-exec; do
  [[ -d "$protected/.git" || -f "$protected/.git" ]] || fail "missing protected checkout: $protected"
  [[ "$(git -C "$protected" rev-parse HEAD)" == "$protected_sha" ]] || fail "protected checkout not pinned: $protected"
  [[ -z "$(git -C "$protected" status --porcelain)" ]] || fail "protected checkout dirty: $protected"
done
[[ -x "$cuda_home/bin/nvcc" ]] || fail "CUDA_HOME must contain nvcc: $cuda_home"
[[ -x "$project/build/double/semiflexible" ]] || fail 'missing double-precision simulator; build it separately'
command -v nvidia-smi >/dev/null || fail 'nvidia-smi unavailable'
command -v timeout >/dev/null || fail 'timeout unavailable'
[[ -x /usr/bin/time ]] || fail '/usr/bin/time unavailable'
"$cuda_home/bin/nvcc" --version | grep -q 'release 13\.0' || fail 'CUDA Toolkit 13.0 required'

if [[ -z "$root" ]]; then
  root="$(mktemp -d /tmp/stage4a3c-nonlinear-pilot-preflight.XXXXXX)"
else
  [[ "$root" = /* && ! -e "$root" ]] || fail '--root must be a new absolute directory'
  mkdir -p "$root"
fi
mkdir -p "$root"/{commands,environment,logs,receipts}
head_sha="$(git rev-parse HEAD)"
printf '%s\n' "$head_sha" > "$root/environment/git-head.txt"
git status --short --branch > "$root/environment/git-status.txt"
git log -1 --format='%H%n%cs%n%s' > "$root/environment/git-identity.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader > "$root/environment/gpu.txt"
nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader > "$root/environment/gpu-before.csv"
"$cuda_home/bin/nvcc" --version > "$root/environment/nvcc.txt"
"$host_cxx" --version > "$root/environment/compiler.txt"
uname -a > "$root/environment/os.txt"
nproc > "$root/environment/cpu-count.txt"
uptime > "$root/environment/load.txt"
sha256sum "$project/build/double/semiflexible" > "$root/environment/executable.sha256"
"$project/build/double/semiflexible" --help > "$root/environment/semiflexible-help.txt"
printf 'mode=%s\nrepository_sha=%s\ncheckpoint_restart=unsupported\n' \
  "$([[ "$execute" == true ]] && printf stage-a || printf preflight)" "$head_sha" > "$root/receipts/preflight.tsv"

if [[ "$execute" != true ]]; then
  printf 'PREFLIGHT_PASS evidence=%s\n' "$root"
  exit 0
fi

out="$root/run-double-N32-k10-seed433201"
[[ ! -e "$out" ]] || fail 'run output already exists'
argv=("$project/build/double/semiflexible" --output "$out" --springs 32 --chains 512
  --b0 1 --kb 30 --kappa 10 --dt .000025 --steps "$steps" --sample 400 --seed 433201
  --stress-mode every-step --stress-batch 256 --cpu-workers 8 --corr-levels 24 --corr-slots 32
  --corr-m 2 --correlator-mib 512 --scalar-output compact)
printf '%q ' "${argv[@]}" > "$root/commands/stage-a.cmd"
printf '\n' >> "$root/commands/stage-a.cmd"

set +e
timeout --foreground --signal=TERM --kill-after=20s "${limit_seconds}s" \
  /usr/bin/time -v -o "$root/receipts/stage-a.time.txt" "${argv[@]}" \
  > "$root/logs/stage-a.log" 2>&1
code=$?
set -e
case "$code" in
  0) kind=completed ;;
  124) kind=timeout ;;
  130|143) kind=interrupted ;;
  *) kind=application_failure ;;
esac
nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader > "$root/environment/gpu-after.csv" || true
printf 'status=%s\nexit_code=%s\ntimeout_seconds=%s\nsteps=%s\noutput=%s\npartial_evidence_preserved=true\ncheckpoint_restart=unsupported\n' \
  "$kind" "$code" "$limit_seconds" "$steps" "$out" > "$root/receipts/stage-a.tsv"

if [[ -f "$out/stress_metadata.json" && -f "$out/metadata.json" ]]; then
  python3 - "$out" "$root/receipts/stage-a-summary.json" <<'PY'
import json, pathlib, re, sys
out, target = map(pathlib.Path, sys.argv[1:])
stress=json.loads((out/'stress_metadata.json').read_text())
main=json.loads((out/'metadata.json').read_text())
time=(target.parent/'stage-a.time.txt').read_text()
rss=re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)', time)
fields=('frames','gpu_stress_seconds','stress_transfer_seconds','stress_transfer_completion_wait_seconds','stress_transfer_bytes','cpu_correlation_seconds','cpu_barrier_seconds','cpu_worker_execution_sum_seconds','buffer_wait_seconds','producer_blocked_seconds','max_inflight_slots','queue_slot_capacity','gpu_stress_bytes','host_stress_batch_bytes','estimated_bytes')
summary={key: stress.get(key) for key in fields}
summary.update(total_wall_seconds=main.get('production_wall_seconds'), overall_ns_per_bead_step=main.get('overall_ns_per_bead_step'), integration_ns_per_bead_step=main.get('integration_ns_per_bead_step'), peak_host_rss_kib=int(rss.group(1)) if rss else None)
frames=summary['frames']; wall=summary['total_wall_seconds']; chains=main['chains']
summary['stress_frames_per_second']=frames/wall if wall and wall > 0 else None
summary['chain_observations_per_second']=frames*chains/wall if wall and wall > 0 else None
gpu=summary['gpu_stress_seconds']; cpu=summary['cpu_correlation_seconds']
summary['gpu_stress_frames_per_second']=frames/gpu if gpu and gpu > 0 else None
summary['cpu_correlation_chain_observations_per_second']=frames*chains/cpu if cpu and cpu > 0 else None
with target.open('w') as handle: json.dump(summary, handle, indent=2, sort_keys=True)
PY
fi
[[ "$code" == 0 ]] || exit "$code"
printf 'STAGE_A_PASS evidence=%s\n' "$root"
