#!/usr/bin/env bash
# GPU host: ./run_k1_large_campaign.sh ../../kg_assoc_k1 pilot|central|full|rho|nu0|parametric|rho-ee
set -euo pipefail

executable=${1:?executable path is required}
mode=${2:-pilot}
script_directory=$(cd "$(dirname "$0")" && pwd)
output_directory="$script_directory/results_large"

particle_count=32768
rho=0.05
temperature=1
dt=0.005
nu0=20
damp=2
push_steps=10000
warmup_steps=20000
production_steps=1000000
pilot_steps=20000
replica_count=${REPLICAS:-1}

if (( replica_count < 1 )); then
    echo "REPLICAS must be at least 1" >&2
    exit 2
fi

mkdir -p "$output_directory"

rho_code_for() {
    local density=$1

    case "$density" in
        0.025)
            echo 25
            ;;
        0.05)
            echo 50
            ;;
        0.10)
            echo 100
            ;;
        0.20)
            echo 200
            ;;
        *)
            echo "unsupported density for deterministic seed: ${density}" >&2
            exit 2
            ;;
    esac
}

legacy_seed_for() {
    local ea=$1
    local ee=$2
    local every=$3
    local replica=$4

    echo $(((((particle_count * 10 + ea) * 10 + ee) * 1000 + every) * 10 + replica))
}

seed_for() {
    local density=$1
    local ea=$2
    local ee=$3
    local attempt_frequency=$4
    local every=$5
    local replica=$6
    local density_code
    density_code=$(rho_code_for "$density")

    # Encodes Np, 1000*rho, Ea, Ee, nu0, Nevery, and replica without rounding.
    echo $(((((((particle_count * 1000 + density_code) * 10 + ea) * 10 + ee) \
        * 100 + attempt_frequency) * 1000 + every) * 10 + replica))
}

run_condition() {
    local density=$1
    local ea=$2
    local ee=$3
    local attempt_frequency=$4
    local every=$5
    local replica=$6
    local steps=$7
    local label=$8
    local tag
    local seed

    if [[ "$label" == "pilot" || "$label" == "central" || "$label" == "full" ]]; then
        tag="large_Np${particle_count}_Ea${ea}_Ee${ee}_N${every}_r${replica}"
        seed=$(legacy_seed_for "$ea" "$ee" "$every" "$replica")
    else
        tag="large_Np${particle_count}_rho${density}_Ea${ea}_Ee${ee}_nu${attempt_frequency}_N${every}_r${replica}"
        seed=$(seed_for "$density" "$ea" "$ee" "$attempt_frequency" "$every" \
            "$replica")
    fi

    if [[ "$label" == "pilot" ]]; then
        tag="pilot_${tag}"
    fi

    local output_prefix="$output_directory/$tag"
    local existing_state="${output_prefix}.state"
    local legacy_rho05_prefix
    legacy_rho05_prefix="$output_directory/large_Np${particle_count}_Ea4_Ee${ee}_N100_r${replica}"
    if [[ "$density" == "0.05" && "$ea" == "4" &&
          "$attempt_frequency" == "20" && "$every" == "100" &&
          -s "${legacy_rho05_prefix}.state" ]]; then
        existing_state="${legacy_rho05_prefix}.state"
    fi

    if [[ "$mode" == list* ]]; then
        if [[ -s "$existing_state" ]]; then
            echo "COMPLETED ${tag} reuses ${existing_state##*/} seed=${seed} steps=${steps}"
        else
            echo "PENDING ${tag} seed=${seed} steps=${steps}"
        fi
        return
    fi

    if [[ -s "$existing_state" ]]; then
        echo "SKIP completed condition: ${tag}"
        return
    fi

    echo "RUN ${tag} seed=${seed} steps=${steps}"
    "$executable" \
        --n "$particle_count" \
        --rho "$density" \
        --temperature "$temperature" \
        --dt "$dt" \
        --nu0 "$attempt_frequency" \
        --damp "$damp" \
        --push-steps "$push_steps" \
        --warmup "$warmup_steps" \
        --Ea "$ea" \
        --Ee "$ee" \
        --Nevery "$every" \
        --steps "$steps" \
        --seed "$seed" \
        --output "$output_prefix"
}

run_replicas() {
    local density=$1
    local ea=$2
    local ee=$3
    local attempt_frequency=$4
    local every=$5
    local steps=$6
    local label=$7

    for ((replica = 1; replica <= replica_count; ++replica)); do
        run_condition "$density" "$ea" "$ee" "$attempt_frequency" "$every" \
            "$replica" "$steps" "$label"
    done
}

run_full_grid() {
    local ea
    local ee
    local every

    for ea in 2 3 4 5 6; do
        run_replicas "$rho" "$ea" 4 "$nu0" 100 "$production_steps" full
    done

    for ee in 2 6 8; do
        run_replicas "$rho" 4 "$ee" "$nu0" 100 "$production_steps" full
    done

    for every in 50 200; do
        run_replicas "$rho" 4 4 "$nu0" "$every" "$production_steps" full
    done
}

run_rho_sweep() {
    local density

    for density in 0.025 0.05 0.10 0.20; do
        run_replicas "$density" 4 4 20 100 "$production_steps" rho
    done
}

run_nu0_sweep() {
    local include_central=${1:-true}
    local attempt_frequency

    for attempt_frequency in 1 5 10 20 40 80; do
        if [[ "$include_central" != true && "$attempt_frequency" == "20" ]]; then
            continue
        fi
        run_replicas 0.05 4 4 "$attempt_frequency" 100 \
            "$production_steps" nu0
    done
}

run_parametric_grid() {
    run_rho_sweep
    run_nu0_sweep false
}

run_rho_ee_sweep() {
    local density
    local ee

    for density in 0.025 0.05 0.10 0.20; do
        for ee in 2 4 6 8; do
            run_replicas "$density" 4 "$ee" 20 100 "$production_steps" rho-ee
        done
    done
}

case "$mode" in
    pilot)
        run_condition "$rho" 4 4 "$nu0" 100 1 "$pilot_steps" pilot
        ;;
    central)
        run_condition "$rho" 4 4 "$nu0" 100 1 "$production_steps" central
        ;;
    full|list)
        run_full_grid
        ;;
    rho|list-rho)
        run_rho_sweep
        ;;
    nu0|list-nu0)
        run_nu0_sweep
        ;;
    parametric|list-parametric)
        run_parametric_grid
        ;;
    rho-ee|list-rho-ee)
        run_rho_ee_sweep
        ;;
    *)
        echo "mode: pilot|central|full|list|rho|nu0|parametric|rho-ee|list-rho|list-nu0|list-parametric|list-rho-ee" >&2
        exit 2
        ;;
esac
