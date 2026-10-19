#!/usr/bin/env python3
"""Read-only Stage 4A.4 static-screen analysis for one completed run."""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

PRIMARY = ('mean_r', 'mean_r2', 're2', 'rg2')
TOLERANCE = {'mean_r': .01, 'mean_r2': .01, 're2': .02, 'rg2': .02}


def fail(message): raise ValueError(message)


def stats(value):
    return {'mean': float(value.mean()), 'se': float(value.std(ddof=1)/math.sqrt(len(value)))}


def analyze(directory, reference):
    directory, reference = Path(directory), Path(reference)
    meta = json.loads((directory/'metadata.json').read_text())
    ref = json.loads(reference.read_text())
    if meta['springs'] != ref['springs']:
        fail('reference/simulator spring count mismatch')
    # metadata intentionally records only active-angle count.  The committed
    # parameter file is the authoritative run-specific bending definition.
    parameters = (directory/'parameters.txt').read_text().split()
    if int(parameters[0]) != ref['springs']:
        fail('parameter/simulator spring count mismatch')
    angles = np.asarray(parameters[1 + 2*ref['springs']:], dtype=float)
    if len(angles) != ref['springs'] + 1 or not np.allclose(angles[1:-1], ref['kappa']):
        fail('reference/simulator kappa mismatch')
    columns = PRIMARY + tuple('tangent%d' % i for i in range(1, min(4, meta['springs']-1)+1))
    per_chain = {name: np.zeros(meta['chains']) for name in columns}; counts = np.zeros(meta['chains'], dtype=int)
    with (directory/'samples.csv').open(newline='') as handle:
        for row in csv.DictReader(handle):
            if float(row['time']) + 1e-15 < meta['production_time']/2: continue
            chain = int(row['chain']); counts[chain] += 1
            for name in columns: per_chain[name][chain] += float(row[name])
    if not np.all(counts == counts[0]) or counts[0] < 2: fail('second-half scalar frames are incomplete')
    result = {'run': {'dt': meta['dt'], 'steps': meta['steps'], 'chains': meta['chains'], 'springs': meta['springs'],
                      'physical_duration': meta['production_time'], 'second_half_frames_per_chain': int(counts[0])},
              'criteria': {'confidence_sigma': 3, 'normalized_static_tolerances': TOLERANCE}, 'observables': {},
              'limitations': ['energy and local-angle distributions are not emitted by the existing full scalar contract; they remain required before a final static acceptance decision']}
    decisions = []
    comparisons = list(PRIMARY) + [('tangent%d' % s, 'orientation_correlation', str(s))
                                   for s in range(1, min(4, meta['springs']-1)+1)]
    for item in comparisons:
        if isinstance(item, tuple):
            name, family, key = item
            expected = ref[family][key]
            tolerance = .02
        else:
            name = item
            expected = ref['observables'][name]
            tolerance = TOLERANCE[name]
        observed = stats(per_chain[name]/counts)
        # Unit-vector correlations have a natural O(1) scale even when their
        # exact flexible-chain value is zero.
        scale = max(abs(expected['mean']), 1.0 if name.startswith('tangent') else 1e-12)
        delta = abs(observed['mean']-expected['mean'])/scale
        upper = delta + 3*math.hypot(observed['se'], expected['se'])/scale
        lower = max(0., delta - 3*math.hypot(observed['se'], expected['se'])/scale)
        decision = 'pass' if upper <= tolerance else ('fail' if lower > tolerance else 'unresolved')
        result['observables'][name] = dict(simulation=observed, reference=expected, normalized_difference=delta,
                                           normalized_upper_3sigma=upper, tolerance=tolerance, decision=decision)
        decisions.append(decision)
    result['static_screen'] = 'pass-provisional' if all(x == 'pass' for x in decisions) else ('fail' if 'fail' in decisions else 'unresolved')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path); parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True); args = parser.parse_args()
    if args.report.exists(): parser.error('refusing to overwrite report')
    args.report.write_text(json.dumps(analyze(args.run_directory, args.reference), indent=2, sort_keys=True)+'\n')
    print(args.report)


if __name__ == '__main__': main()
