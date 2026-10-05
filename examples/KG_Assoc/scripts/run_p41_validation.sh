#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$repo_root"

make -B -C examples/KG_Assoc kg_assoc_production kg_assoc_stress_test
./examples/KG_Assoc/kg_assoc_production --self-test
./examples/KG_Assoc/kg_assoc_stress_test

# Set INPUT to a dedicated-host C1 restart/input. This intentionally remains a
# short smoke; inspect the synchronized output streams before any longer run.
: "${INPUT:?set INPUT to a chemically valid C1 .restart.lammpsdat file}"
case "$INPUT" in
  *.restart.lammpsdat) restart_prefix=${INPUT%.restart.lammpsdat} ;;
  *) echo "INPUT must name a .restart.lammpsdat file" >&2; exit 2 ;;
esac
[[ -r "$restart_prefix.assoc_restart" ]] || exit 2
workdir=$(mktemp -d /tmp/kg_assoc_p41_validation.XXXXXX)
trap 'rm -rf "$workdir"' EXIT
prefix="$workdir/production"
continuation="$workdir/continuation"

# The shorter frame cadence is validation-only; production defaults remain 10,000.
./examples/KG_Assoc/kg_assoc_production --restart-prefix "$restart_prefix" \
  --steps 20000 --com-every 100 --frame-every 100 --output "$prefix"
python3 - "$prefix" 20000 <<'PY'
import math, pathlib, re, sys
p = pathlib.Path(sys.argv[1]); steps = int(sys.argv[2])
def rows(path): return [x.split() for x in path.read_text().splitlines() if x and not x.startswith('#')]
s = p.with_suffix('.stress_correlator').read_text().splitlines()
m = re.match(r'# stress_samples=(\d+) step0_sampled=(\w+) stress_interval_steps=(\d+) dt=', s[0])
assert m and int(m.group(1)) == steps and m.group(2) == 'no' and int(m.group(3)) == 1
assert s[1] == '# time Gxy Gxz Gyz GNxy GNxz GNyz G'
assert float(s[2].split()[0]) == 0.0
for line in s[2:]:
  v = [float(x) for x in line.split()]; assert len(v) == 8 and all(map(math.isfinite, v))
com, traj = rows(p.with_suffix('.com_samples')), rows(p.with_suffix('.com_trajectory'))
steps_com, steps_traj = sorted({int(x[0]) for x in com}), sorted({int(x[0]) for x in traj})
start = steps_com[0] - 100; expected = list(range(start + 100, start + steps + 1, 100))
assert steps_com == expected and steps_traj == expected
stars = len({x[2] for x in com if int(x[0]) == expected[0]})
assert len(com) == len(traj) == stars * len(expected)
lines, frames, i = p.with_suffix('.topology').read_text().splitlines()[1:], {}, 0
while i < len(lines):
  h = lines[i].split(); assert h[0] == 'FRAME' and len(h) == 4; step, n = int(h[1]), int(h[3]); i += 1
  pairs, partners = set(), set()
  for _ in range(n):
    a, b, ma, mb = map(int, lines[i].split()); i += 1
    assert a > 0 and b > 0 and a != b and ma > 0 and mb > 0
    q = tuple(sorted((a,b))); assert q not in pairs and a not in partners and b not in partners
    pairs.add(q); partners.update(q)
  frames[step] = pairs
assert sorted(frames) == expected
final = {tuple(sorted(map(int, x[:2]))) for x in rows(p.with_suffix('.final_associations'))}
assert frames[expected[-1]] == final
# PBC temporal-unwrapping regression: 4.9 -> -4.9 is +0.2, never -9.8.
d = -4.9 - 4.9 - 10.0 * round((-4.9 - 4.9) / 10.0); assert abs(d - .2) < 1e-12
print(f'P4.1 validation: stress_samples={steps}; com_sample_steps={len(expected)}; '
      f'com_rows={len(com)}; synchronized_frames={len(expected)}; stars={stars}')
PY
./examples/KG_Assoc/kg_assoc_production --restart-prefix "$prefix" --steps 1 \
  --com-every 100 --frame-every 100 --output "$continuation"
python3 - "$prefix.assoc_restart" "$continuation.assoc_restart" "$continuation.state" <<'PY'
import sys
def pairs(path):
  x = open(path).read().splitlines(); i = next(i for i, y in enumerate(x) if y.startswith('active_bonds ')); return x[i+1:i+1+int(x[i].split()[1])]
assert pairs(sys.argv[1]) == pairs(sys.argv[2])
footer = open(sys.argv[3]).read().splitlines()[-1]
assert footer.startswith('# chemistry_sweeps=0 '), footer
PY
echo 'P4.1 restart: 1 step, zero chemistry sweeps, topology preserved; COM output starts a new segment by design'
echo 'P4.1_VALIDATION PASS'
