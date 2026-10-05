#!/usr/bin/env bash
# Usage: run_s2_campaign.sh INPUT_FILE OUTPUT_DIRECTORY baseline|cadence|ea|ee|list [--force]
set -euo pipefail

input_file=${1:?missing equilibrated LAMMPS input file}
output_directory=${2:?missing output directory}
stage=${3:?choose baseline, cadence, ea, ee, or list}
force=${4:-}

if [[ ! -f "$input_file" ]]; then
    echo "Input file does not exist: $input_file" >&2
    exit 2
fi
if [[ -n "$force" && "$force" != "--force" ]]; then
    echo "Only --force is accepted as the optional fourth argument" >&2
    exit 2
fi

root=$(cd "$(dirname "$0")/.." && pwd)
executable=${S2_EXE:-"$root/kg_assoc_stars"}
nevery=${S2_NEVERY:-100}
mkdir -p "$output_directory"

run() {
    local tag=$1
    local seed=$2
    local ea=$3
    local ee=$4
    local every=$5
    local steps=$6
    local prefix="$output_directory/$tag"
    local -a command=(
        "$executable"
        --input "$input_file"
        --arms 4
        --narm 10
        --steps "$steps"
        --dt 0.01
        --temperature 1
        --Ea "$ea"
        --Ee "$ee"
        --nu0 20
        --Nevery "$every"
        --r-assoc 1.25
        --damp 2
        --K 30
        --R0 1.5
        --seed "$seed"
        --output "$prefix")

    if [[ "$stage" == "list" ]]; then
        printf '%q ' "${command[@]}"
        printf '\n'
        return
    fi

    if [[ -n "$force" ]]; then
        command+=(--force)
    elif [[ -e "$prefix.state" || -e "$prefix.events" || -e "$prefix.log" ||
            -e "$prefix.command" ]]; then
        echo "Refusing to overwrite existing output for $tag; pass --force to override" >&2
        exit 3
    fi

    printf '%q ' "${command[@]}" > "$prefix.command"
    printf '\n' >> "$prefix.command"
    "${command[@]}" > "$prefix.log" 2>&1
}

case "$stage" in
    baseline)
        run baseline_Ee8_Ea4_N100_seed12001 12001 4 8 100 500000
        run baseline_Ee8_Ea4_N100_seed12002 12002 4 8 100 500000
        run baseline_Ee8_Ea4_N100_seed12003 12003 4 8 100 500000
        ;;
    cadence)
        run cadence_Ee8_Ea4_N20_seed12100 12100 4 8 20 500000
        run cadence_Ee8_Ea4_N50_seed12100 12100 4 8 50 500000
        run cadence_Ee8_Ea4_N100_seed12100 12100 4 8 100 500000
        run cadence_Ee8_Ea4_N200_seed12100 12100 4 8 200 500000
        ;;
    ea)
        run ea_Ea2_Ee8_N${nevery}_seed12200 12200 2 8 "$nevery" 500000
        run ea_Ea4_Ee8_N${nevery}_seed12200 12200 4 8 "$nevery" 500000
        run ea_Ea6_Ee8_N${nevery}_seed12200 12200 6 8 "$nevery" 1000000
        ;;
    ee)
        run ee_Ea4_Ee2_N${nevery}_seed12300 12300 4 2 "$nevery" 500000
        run ee_Ea4_Ee4_N${nevery}_seed12300 12300 4 4 "$nevery" 500000
        run ee_Ea4_Ee6_N${nevery}_seed12300 12300 4 6 "$nevery" 500000
        run ee_Ea4_Ee8_N${nevery}_seed12300 12300 4 8 "$nevery" 500000
        ;;
    list)
        run baseline_Ee8_Ea4_N100_seed12001 12001 4 8 100 500000
        run baseline_Ee8_Ea4_N100_seed12002 12002 4 8 100 500000
        run baseline_Ee8_Ea4_N100_seed12003 12003 4 8 100 500000
        run cadence_Ee8_Ea4_N20_seed12100 12100 4 8 20 500000
        run cadence_Ee8_Ea4_N50_seed12100 12100 4 8 50 500000
        run cadence_Ee8_Ea4_N100_seed12100 12100 4 8 100 500000
        run cadence_Ee8_Ea4_N200_seed12100 12100 4 8 200 500000
        run ea_Ea2_Ee8_N${nevery}_seed12200 12200 2 8 "$nevery" 500000
        run ea_Ea4_Ee8_N${nevery}_seed12200 12200 4 8 "$nevery" 500000
        run ea_Ea6_Ee8_N${nevery}_seed12200 12200 6 8 "$nevery" 1000000
        run ee_Ea4_Ee2_N${nevery}_seed12300 12300 4 2 "$nevery" 500000
        run ee_Ea4_Ee4_N${nevery}_seed12300 12300 4 4 "$nevery" 500000
        run ee_Ea4_Ee6_N${nevery}_seed12300 12300 4 6 "$nevery" 500000
        run ee_Ea4_Ee8_N${nevery}_seed12300 12300 4 8 "$nevery" 500000
        ;;
    *)
        echo "Stage must be baseline, cadence, ea, ee, or list" >&2
        exit 2
        ;;
esac
