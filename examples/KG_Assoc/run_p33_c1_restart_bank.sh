#!/usr/bin/env bash
# Generate the six P3.3 C1 chemical restart-bank entries on a CUDA host.
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
assoc_dir="$root/examples/KG_Assoc"
bank_dir="$assoc_dir/systems/restart_bank/C1"
executable="$assoc_dir/kg_assoc_stars"

mkdir -p "$bank_dir"

for seed in 12001 12002; do
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

python3 "$assoc_dir/analysis/validate_c1_restart_bank.py" --bank-dir "$bank_dir"
