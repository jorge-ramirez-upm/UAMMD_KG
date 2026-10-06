#!/usr/bin/env bash
# Prepare independent C1 E1 states, then construct matching P3.3 restart entries.
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
assoc_dir="$repo_root/examples/KG_Assoc"
input="$assoc_dir/systems/generated/Stars_NA4N10C1000rho0.85rhopoly0.8.lammpsdat"
bank_dir="$assoc_dir/systems/restart_bank/C1"

if (( $# > 0 )); then
  seeds=("$@")
else
  seeds=(12003 12004)
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
  e1="$assoc_dir/systems/e1_equilibrated/C1_long_s${seed}.e1.lammpsdat"
  if [[ -e "$e1" || -e "$e1.e1_diagnostics" || -e "$e1.stationarity.txt" ||
        -e "$e1.preparation.txt" ]]; then
    echo "refusing to overwrite E1 output for seed $seed" >&2
    exit 1
  fi
  for time_label in 40000 50000 60000; do
    prefix="$bank_dir/C1_e2_s${seed}_t${time_label}"
    if [[ -e "$prefix.restart.lammpsdat" || -e "$prefix.assoc_restart" ]]; then
      echo "refusing to overwrite restart-bank entry: $prefix" >&2
      exit 1
    fi
  done
  smoke="$bank_dir/C1_e2_s${seed}_t60000.p42_continuation_smoke"
  if [[ -e "$smoke.restart.lammpsdat" || -e "$smoke.assoc_restart" ]]; then
    echo "refusing to overwrite continuation smoke for seed $seed" >&2
    exit 1
  fi
done

[[ -r "$input" ]] || { echo "missing C1 generated input: $input" >&2; exit 1; }

make -B -C "$assoc_dir" kg_assoc_star_equilibrate kg_assoc_stars

for seed in "${seeds[@]}"; do
  e1="$assoc_dir/systems/e1_equilibrated/C1_long_s${seed}.e1.lammpsdat"
  diagnostics="$e1.e1_diagnostics"
  stationarity="$e1.stationarity.txt"
  provenance="$e1.preparation.txt"
  {
    echo "git_sha $(git -C "$repo_root" rev-parse HEAD)"
    echo "input $input"
    echo "input_sha256 $(sha256sum "$input" | awk '{print $1}')"
    echo "seed $seed"
    echo "stage3b_steps 20000"
    echo "wca_ramp 0.01,0.03,0.10,0.30,1.00"
    echo "wca_ramp_steps 500"
    echo "promotion_steps 1000"
    echo "dt_dpd 0.002"
    echo "dt_wca 0.01"
    echo "stage4_steps 2000000"
    echo "conformation_every 1000"
  } > "$provenance"
  "$assoc_dir/kg_assoc_star_equilibrate" --input "$input" --output "$e1" \
    --diagnostics "$diagnostics" --arms 4 --narm 10 --seed "$seed" \
    --stage3b-steps 20000 --stage3b-diagnostic-every 500 --wca-ramp \
    --wca-ramp-steps 500 --promotion-steps 1000 --dt-dpd 0.002 --dt-wca 0.01 \
    --stage4-steps 2000000 --conformation-every 1000
  python3 "$assoc_dir/analyze_e1_stationarity.py" "$diagnostics" > "$stationarity"
done

P33_C1_SEEDS="${seeds[*]}" "$assoc_dir/run_p33_c1_restart_bank.sh"

for seed in "${seeds[@]}"; do
  restart="$assoc_dir/systems/restart_bank/C1/C1_e2_s${seed}_t60000"
  smoke="${restart}.p42_continuation_smoke"
  [[ ! -e "$smoke.restart.lammpsdat" && ! -e "$smoke.assoc_restart" ]] || {
    echo "refusing to overwrite continuation smoke for seed $seed" >&2
    exit 1
  }
  "$assoc_dir/kg_assoc_stars" --restart-prefix "$restart" --steps 20000 \
    --diagnostic-every 1000 --output "$smoke"
  [[ -s "$smoke.restart.lammpsdat" && -s "$smoke.assoc_restart" ]] || {
    echo "missing continuation-smoke restart pair for seed $seed" >&2
    exit 1
  }
done
