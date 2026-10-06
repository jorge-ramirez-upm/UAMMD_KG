#!/usr/bin/env bash
# Generate P3.3-style C1 chemical restart-bank entries on a CUDA host.
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
assoc_dir="$root/examples/KG_Assoc"
bank_dir="$assoc_dir/systems/restart_bank/C1"
executable="$assoc_dir/kg_assoc_stars"

mkdir -p "$bank_dir"

read -r -a seeds <<< "${P33_C1_SEEDS:-12001 12002}"
if (( ${#seeds[@]} == 0 )); then
  echo "P33_C1_SEEDS must contain at least one seed" >&2
  exit 2
fi

declare -A seen_seeds
for seed in "${seeds[@]}"; do
  if [[ ! "$seed" =~ ^[1-9][0-9]*$ ]]; then
    echo "invalid seed: $seed" >&2
    exit 2
  fi
  if [[ -n ${seen_seeds[$seed]+x} ]]; then
    echo "duplicate seed: $seed" >&2
    exit 2
  fi
  seen_seeds[$seed]=1
done

for seed in "${seeds[@]}"; do
  for time_label in 40000 50000 60000; do
    prefix="$bank_dir/C1_e2_s${seed}_t${time_label}"
    if [[ -e "$prefix.restart.lammpsdat" || -e "$prefix.assoc_restart" ]]; then
      echo "refusing to overwrite restart-bank entry: $prefix" >&2
      exit 1
    fi
  done
done

for seed in "${seeds[@]}"; do
  input="$assoc_dir/systems/e1_equilibrated/C1_long_s${seed}.e1.lammpsdat"
  t40000="$bank_dir/C1_e2_s${seed}_t40000"
  t50000="$bank_dir/C1_e2_s${seed}_t50000"
  t60000="$bank_dir/C1_e2_s${seed}_t60000"

  "$executable" --input "$input" --arms 4 --narm 10 --steps 4000000 \
    --Nevery 100 --diagnostic-every 1000 --seed "$seed" --output "$t40000"
  "$executable" --restart-prefix "$t40000" --steps 1000000 \
    --diagnostic-every 1000 --output "$t50000"
  "$executable" --restart-prefix "$t50000" --steps 1000000 \
    --diagnostic-every 1000 --output "$t60000"
done

seed_csv=$(IFS=,; echo "${seeds[*]}")
python3 "$assoc_dir/analysis/validate_c1_restart_bank.py" --bank-dir "$bank_dir" \
  --seeds "$seed_csv"
