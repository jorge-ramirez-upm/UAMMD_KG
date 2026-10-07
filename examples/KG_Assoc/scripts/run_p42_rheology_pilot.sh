#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$repo_root"

steps=${P42_PILOT_STEPS:-1000000}
pilot_root=${P42_PILOT_DIR:-p42_rheology_pilot}
throughput=${P42_PILOT_THROUGHPUT:-1.14428e8}
particles=${P42_PILOT_PARTICLES:-43563}
stars=${P42_PILOT_STARS:-1000}
com_every=${P42_PILOT_COM_EVERY:-100}
run_kind=${P42_PILOT_RUN_KIND:-restart_segment}
frame_every=10000

if (( steps <= 0 )); then
  echo "P42_PILOT_STEPS must be positive" >&2
  exit 2
fi
if (( com_every <= 0 )); then
  echo "P42_PILOT_COM_EVERY must be positive" >&2
  exit 2
fi
if (( stars <= 0 )); then
  echo "P42_PILOT_STARS must be positive" >&2
  exit 2
fi

if (( $# > 0 )); then
  restart_prefixes=("$@")
else
  restart_prefixes=(
    examples/KG_Assoc/systems/restart_bank/C1/C1_e2_s12001_t40000
    examples/KG_Assoc/systems/restart_bank/C1/C1_e2_s12002_t40000
  )
fi

if (( ${#restart_prefixes[@]} < 2 )); then
  echo "provide one restart prefix for each independent seed" >&2
  exit 2
fi

com_rows_per_seed=$(awk -v steps="$steps" -v com_every="$com_every" -v stars="$stars" \
  'BEGIN { printf "%.0f", (steps / com_every) * stars }')
wall_seconds_per_seed=$(awk -v steps="$steps" -v particles="$particles" -v throughput="$throughput" \
  'BEGIN { printf "%.6f", steps * particles / throughput }')
serial_wall_seconds=$(awk -v per_seed="$wall_seconds_per_seed" -v seeds="${#restart_prefixes[@]}" \
  'BEGIN { printf "%.6f", per_seed * seeds }')

echo "P4.2 rheology pilot steps per seed: $steps"
echo "P4.2 rheology pilot COM cadence: $com_every MD steps"
echo "P4.2 rheology pilot estimated COM rows per seed: $com_rows_per_seed"
echo "P4.2 rheology pilot estimated serial wall seconds: $serial_wall_seconds"

mkdir -p "$pilot_root"
workdir=$(mktemp -d "$pilot_root/run.XXXXXX")

fail() {
  echo "P4.2 rheology pilot failed: $1" >&2
  echo "Incomplete pilot directory: $workdir" >&2
  exit 1
}

require_completed_run() {
  local label=$1
  local output_prefix=$2
  local log_path=$3
  if ! grep -Fxq 'STAR_ASSOCIATION_SMOKE PASS' "$log_path"; then
    fail "$label did not report successful completion"
  fi
  for suffix in state events stress_correlator com_samples com_trajectory topology \
                final_associations final_permanent.lammpsdat restart.lammpsdat assoc_restart; do
    [[ -s "$output_prefix.$suffix" ]] || fail "$label is missing .$suffix"
  done
}

make -B -C examples/KG_Assoc kg_assoc_production

{
  echo "pilot_git_sha $(git rev-parse HEAD)"
  echo "pilot_run_kind $run_kind"
  echo "pilot_steps $steps"
  echo "pilot_com_every $com_every"
  echo "pilot_frame_every $frame_every"
  echo "pilot_stress_sampling every_md_step"
  echo "estimated_com_rows_per_seed $com_rows_per_seed"
  echo "stars $stars"
  echo "optimized_particle_timesteps_per_second $throughput"
  echo "particles $particles"
  echo "estimated_wall_seconds_per_seed $wall_seconds_per_seed"
  echo "estimated_serial_wall_seconds $serial_wall_seconds"
  echo "executable_sha256 $(sha256sum examples/KG_Assoc/kg_assoc_production | awk '{print $1}')"
  echo "host $(hostname)"
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
  fi
} > "$workdir/provenance.txt"

declare -A seen_seeds
for restart_prefix in "${restart_prefixes[@]}"; do
  [[ -r "$restart_prefix.restart.lammpsdat" ]] || fail "missing restart data: $restart_prefix"
  [[ -r "$restart_prefix.assoc_restart" ]] || fail "missing restart metadata: $restart_prefix"
  seed=$(awk '$1 == "seed" { print $2; exit }' "$restart_prefix.assoc_restart")
  [[ -n "$seed" ]] || fail "missing seed in restart metadata: $restart_prefix"
  if [[ -n ${seen_seeds[$seed]+x} ]]; then
    fail "restart prefixes must use independent seeds; duplicate seed: $seed"
  fi
  seen_seeds[$seed]=1
  label=$(basename "$restart_prefix")
  output_prefix="$workdir/$label"
  [[ ! -e "$output_prefix.state" ]] || fail "duplicate output label: $label"

  {
    echo "restart_prefix $restart_prefix"
    echo "restart_seed $seed"
    echo "restart_data_sha256 $(sha256sum "$restart_prefix.restart.lammpsdat" | awk '{print $1}')"
    echo "restart_metadata_sha256 $(sha256sum "$restart_prefix.assoc_restart" | awk '{print $1}')"
  } >> "$workdir/provenance.txt"

  ./examples/KG_Assoc/kg_assoc_production --restart-prefix "$restart_prefix" \
    --steps "$steps" --com-every "$com_every" --frame-every "$frame_every" \
    --output "$output_prefix" \
    > "$workdir/$label.log" 2>&1
  require_completed_run "$label" "$output_prefix" "$workdir/$label.log"
  grep -F 'S1 total_timesteps' "$workdir/$label.log" | tail -n 1
done

echo "P4.2 rheology pilot directory: $workdir"
echo "Analyze with: python3 examples/KG_Assoc/analysis/analyze_p42_rheology_pilot.py --output-prefix $workdir/rheology $workdir/*.stress_correlator"
