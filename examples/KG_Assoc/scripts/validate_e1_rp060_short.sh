#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$repo_root"
input=examples/KG_Assoc/kg_assoc_100m/inputs/F04_N010_RP060/initial.lammpsdat
executable=examples/KG_Assoc/kg_assoc_star_equilibrate
[[ -r "$input" ]] || { echo "Missing user configuration: $input" >&2; exit 2; }
make -C examples/KG_Assoc kg_assoc_star_equilibrate
validation_dir=$(mktemp -d /tmp/kg_e1_rp060_s12002.XXXXXX)
echo "Retaining validation outputs in $validation_dir"
git rev-parse HEAD > "$validation_dir/git_sha.txt"
sha256sum "$input" "$executable" > "$validation_dir/sha256.txt"
command=("$executable" --input "$input" --output "$validation_dir/unused.lammpsdat"
  --diagnostics "$validation_dir/diagnostics.tsv" --arms 4 --narm 10 --seed 12002
  --dt-dpd 0.002 --dt-wca 0.01 --stage3b-steps 20000
  --stage3b-diagnostic-every 500 --wca-ramp --wca-ramp-steps 500
  --stage4-promotion-test --promotion-steps 1000)
printf '%q ' "${command[@]}" > "$validation_dir/command.txt"
printf '\n' >> "$validation_dir/command.txt"
# Promotion mode ends after 71,400 DPD and 4,500 WCA steps, writing no E1 bank.
/usr/bin/time -f '%e %U %S %M' -o "$validation_dir/timing.txt" \
  "${command[@]}" > "$validation_dir/stdout.log" 2> "$validation_dir/stderr.log"
python3 - "$validation_dir" <<'PY'
import json
import math
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
stdout = (root / 'stdout.log').read_text()
stderr = (root / 'stderr.log').read_text()
if 'E1_PROMOTION PASS' not in stdout:
    raise SystemExit('Missing WCA promotion success marker')
effective = []
for line in stderr.splitlines():
    if '[E1 DPD effective]' not in line:
        continue
    values = dict(re.findall(r'(\w+)=([^\s]+)', line))
    if float(values['gamma']) != 4.5 or not math.isclose(
            float(values['noise_squared_dt']), 9.0, rel_tol=1e-5):
        raise SystemExit('Effective DPD gamma/noise validation failed')
    if not math.isclose(float(values['dt']), 0.002, rel_tol=1e-6):
        raise SystemExit('Effective DPD timestep validation failed')
    effective.append(values)
if len(effective) != 16:
    raise SystemExit('Expected effective parameters for all 16 DPD segments')
holds = []
for line in (root / 'diagnostics.tsv').read_text().splitlines():
    if '[E1 transition]' not in line:
        continue
    values = dict(re.findall(r'([\w.]+)=([^\s]+)', line))
    for key in ('temperature', 'max_speed', 'min_permanent_bond', 'max_permanent_bond'):
        if not math.isfinite(float(values[key])):
            raise SystemExit('Nonfinite transition diagnostic')
    if float(values['max_permanent_bond']) >= 1.5:
        raise SystemExit('Invalid permanent FENE extension')
    if values['label'] == 'during_stage3b_relaxation_hold':
        holds.append(values)
if len(holds) != 40 or int(holds[-1]['step']) != 71400:
    raise SystemExit('Incomplete Stage 3b diagnostics')
wall, user, system, memory = map(float, (root / 'timing.txt').read_text().split())
summary = {
    'status': 'passed', 'seed': 12002, 'dpd_steps': 71400, 'wca_steps': 4500,
    'wall_seconds': wall, 'user_seconds': user, 'system_seconds': system,
    'max_rss_kib': memory,
    'effective_dpd': effective[-1],
    'stage3b_temperature_first': float(holds[0]['temperature']),
    'stage3b_temperature_last': float(holds[-1]['temperature']),
    'stage3b_minimum_bond': min(float(row['min_permanent_bond']) for row in holds),
    'stage3b_maximum_bond': max(float(row['max_permanent_bond']) for row in holds),
}
(root / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
PY
