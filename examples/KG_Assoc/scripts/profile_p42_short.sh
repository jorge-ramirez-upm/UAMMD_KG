#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$repo_root"
: "${INPUT:?set INPUT to a chemically valid C1 .restart.lammpsdat file}"
case "$INPUT" in
  *.restart.lammpsdat) restart_prefix=${INPUT%.restart.lammpsdat} ;;
  *) echo "INPUT must name a .restart.lammpsdat file" >&2; exit 2 ;;
esac
[[ -r "$restart_prefix.assoc_restart" ]] || exit 2

workdir=${P42_PROFILE_DIR:-p42_profile_short}
mkdir -p "$workdir"
steps=${P42_STEPS:-2000}
nsys=${NSYS:-nsys}

make -B -C examples/KG_Assoc kg_assoc_stars kg_assoc_production

# Same restart, steps, physics, and GPU. These are short captures only.
"$nsys" profile --force-overwrite --trace=cuda,nvtx,osrt --stats=true \
  -o "$workdir/baseline" -- \
  ./examples/KG_Assoc/kg_assoc_stars --restart-prefix "$restart_prefix" \
    --steps "$steps" --output "$workdir/baseline_output"
"$nsys" profile --force-overwrite --trace=cuda,nvtx,osrt --stats=true \
  -o "$workdir/production" -- \
  ./examples/KG_Assoc/kg_assoc_production --restart-prefix "$restart_prefix" \
    --steps "$steps" --output "$workdir/production_output"

"$nsys" stats --report cudaapisum,gpukernsum,osrtsum \
  "$workdir/baseline.nsys-rep" > "$workdir/baseline.stats.txt"
"$nsys" stats --report cudaapisum,gpukernsum,osrtsum \
  "$workdir/production.nsys-rep" > "$workdir/production.stats.txt"

echo "P4.2 short Nsight captures written to $workdir"
echo "Compare baseline.stats.txt and production.stats.txt for launches,"
echo "synchronization, device-host copies, and dominant kernels."

if [[ "${NSIGHT_COMPUTE:-0}" == 1 ]]; then
  ncu=${NCU:-ncu}
  "$ncu" --target-processes all --set full \
    -o "$workdir/production_ncu" -- \
    ./examples/KG_Assoc/kg_assoc_production --restart-prefix "$restart_prefix" \
      --steps "${NCU_STEPS:-100}" --output "$workdir/production_ncu_output"
fi
