#!/usr/bin/env bash
# GPU host: ./run_k1_large_campaign.sh ../../kg_assoc_k1 pilot|central|full|list
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

seed_for() {
    local ea=$1
    local ee=$2
    local every=$3
    local replica=$4

    # Unique while Ea/Ee/replica are single-digit integers and Nevery < 1000.
    echo $(((((particle_count * 10 + ea) * 10 + ee) * 1000 + every) * 10 + replica))
}

run_condition() {
    local ea=$1
    local ee=$2
    local every=$3
    local replica=$4
    local steps=$5
    local label=$6

    local tag="large_Np${particle_count}_Ea${ea}_Ee${ee}_N${every}_r${replica}"
    if [[ "$label" == "pilot" ]]; then
        tag="pilot_${tag}"
    fi

    local output_prefix="$output_directory/$tag"
    local seed
    seed=$(seed_for "$ea" "$ee" "$every" "$replica")

    if [[ -s "${output_prefix}.state" ]]; then
        echo "SKIP completed condition: ${tag}"
        return
    fi

    if [[ "$mode" == "list" ]]; then
        echo "${tag} seed=${seed} steps=${steps}"
        return
    fi

    echo "RUN ${tag} seed=${seed} steps=${steps}"
    "$executable" \
        --n "$particle_count" \
        --rho "$rho" \
        --temperature "$temperature" \
        --dt "$dt" \
        --nu0 "$nu0" \
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
    local ea=$1
    local ee=$2
    local every=$3
    local steps=$4
    local label=$5

    for ((replica = 1; replica <= replica_count; ++replica)); do
        run_condition "$ea" "$ee" "$every" "$replica" "$steps" "$label"
    done
}

run_full_grid() {
    local ea
    local ee
    local every

    for ea in 2 3 4 5 6; do
        run_replicas "$ea" 4 100 "$production_steps" full
    done

    for ee in 2 6 8; do
        run_replicas 4 "$ee" 100 "$production_steps" full
    done

    for every in 50 200; do
        run_replicas 4 4 "$every" "$production_steps" full
    done
}

case "$mode" in
    pilot)
        run_condition 4 4 100 1 "$pilot_steps" pilot
        ;;
    central)
        run_condition 4 4 100 1 "$production_steps" central
        ;;
    full|list)
        run_full_grid
        ;;
    *)
        echo "mode: pilot|central|full|list" >&2
        exit 2
        ;;
esac
