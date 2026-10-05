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
workdir=$(mktemp -d /tmp/kg_assoc_p41_benchmark.XXXXXX)
trap 'rm -rf "$workdir"' EXIT

make -B -C examples/KG_Assoc kg_assoc_stars kg_assoc_production
./examples/KG_Assoc/kg_assoc_stars --restart-prefix "$restart_prefix" \
  --steps 20000 --output "$workdir/baseline" > "$workdir/baseline.log"
./examples/KG_Assoc/kg_assoc_production --restart-prefix "$restart_prefix" \
  --steps 20000 --output "$workdir/production" > "$workdir/production.log"
python3 - "$workdir/baseline.log" "$workdir/production.log" <<'PY'
import re, sys
def metrics(path):
  text = open(path).read()
  m = re.search(r'wall_seconds\s+([\deE+.-]+).*particle_timesteps_per_second\s+([\deE+.-]+)', text)
  assert m, 'missing timing metrics in ' + path
  return float(m.group(1)), float(m.group(2))
bw, bt = metrics(sys.argv[1]); pw, pt = metrics(sys.argv[2])
assert bw > 0 and bt > 0 and pw > 0 and pt > 0
print(f'P4.1_BENCHMARK baseline_wall_seconds={bw:.6g} baseline_particle_timesteps_per_second={bt:.6g}')
print(f'P4.1_BENCHMARK production_wall_seconds={pw:.6g} production_particle_timesteps_per_second={pt:.6g}')
print(f'P4.1_BENCHMARK relative_wall_overhead={pw/bw-1:.6g} relative_throughput_loss={1-pt/bt:.6g}')
print('P4.1_BENCHMARK PASS')
PY
