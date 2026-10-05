#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$repo_root"
: "${INPUT:?set INPUT to the C1 LAMMPS data file}"

make -B -C examples/KG_Assoc kg_assoc_stars kg_assoc_production
./examples/KG_Assoc/kg_assoc_stars --input "$INPUT" --arms 4 --narm 10 \
  --steps 20000 --output /tmp/kg_assoc_baseline --force
./examples/KG_Assoc/kg_assoc_production --input "$INPUT" --arms 4 --narm 10 \
  --steps 20000 --output /tmp/kg_assoc_p41_benchmark --force
