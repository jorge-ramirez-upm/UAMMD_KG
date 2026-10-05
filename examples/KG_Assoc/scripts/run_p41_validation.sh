#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$repo_root"

make -B -C examples/KG_Assoc kg_assoc_production kg_assoc_stress_test
./examples/KG_Assoc/kg_assoc_production --self-test
./examples/KG_Assoc/kg_assoc_stress_test

# Set INPUT to a dedicated-host C1 restart/input. This intentionally remains a
# short smoke; inspect the synchronized output streams before any longer run.
: "${INPUT:?set INPUT to the C1 LAMMPS data file}"
./examples/KG_Assoc/kg_assoc_production --input "$INPUT" --arms 4 --narm 10 \
  --steps 20000 --output /tmp/kg_assoc_p41_validation --force
