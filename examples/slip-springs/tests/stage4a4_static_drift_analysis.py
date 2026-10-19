#!/usr/bin/env python3
"""Read-only, chain-cluster Stage 4A.4 static drift analysis."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

PRIMARY = ('mean_r', 'mean_r2', 're2', 'rg2')
TOLERANCE = {'mean_r': .01, 'mean_r2': .01, 're2': .02, 'rg2': .02}


def fail(message):
    raise ValueError(message)


def estimate(values):
    values = np.asarray(values, dtype=float)
    return {'mean': float(values.mean()), 'se': float(values.std(ddof=1)/math.sqrt(len(values)))}


def reference_for(name, reference):
    if name.startswith('tangent'):
        return reference['orientation_correlation'][name.removeprefix('tangent')], .02, 1.
    return reference['observables'][name], TOLERANCE[name], max(abs(reference['observables'][name]['mean']), 1e-12)


def half_difference(values, reference, name):
    observed = estimate(values)
    expected, tolerance, scale = reference_for(name, reference)
    delta = abs(observed['mean'] - expected['mean']) / scale
    combined = math.hypot(observed['se'], expected['se']) / scale
    upper, lower = delta + 3*combined, max(0., delta - 3*combined)
    decision = 'pass' if upper <= tolerance else ('fail' if lower > tolerance else 'unresolved')
    return {'estimate': observed, 'reference': expected, 'difference': observed['mean']-expected['mean'],
            'normalized_difference': delta, 'upper_3sigma': upper, 'lower_3sigma': lower,
            'tolerance': tolerance, 'decision': decision}


def run(directory, reference_path):
    directory = Path(directory)
    metadata = json.loads((directory/'metadata.json').read_text())
    reference = json.loads(Path(reference_path).read_text())
    if metadata['springs'] != reference['springs'] or metadata['chains'] != 512:
        fail('unexpected reference or chain count')
    names = list(PRIMARY) + ['tangent%d' % x for x in range(1, min(4, metadata['springs']-1)+1)]
    chains = metadata['chains']
    first = {name: np.zeros(chains) for name in names}
    second = {name: np.zeros(chains) for name in names}
    total = {name: np.zeros(chains) for name in names}
    squares = {name: np.zeros(chains) for name in names}
    products = {name: np.zeros(chains) for name in names}
    previous = {name: np.full(chains, np.nan) for name in names}
    links = {name: np.zeros(chains, dtype=int) for name in names}
    nfirst = np.zeros(chains, dtype=int); nsecond = np.zeros(chains, dtype=int); ntotal = np.zeros(chains, dtype=int)
    with (directory/'samples.csv').open(newline='') as handle:
        for row in csv.DictReader(handle):
            chain, time = int(row['chain']), float(row['time'])
            if not 0 <= chain < chains: fail('invalid chain id')
            if time < metadata['production_time']/2:
                nfirst[chain] += 1; target = first
            elif time > metadata['production_time']/2:
                nsecond[chain] += 1; target = second
            else:
                # The midpoint belongs to neither equal-duration half.
                for name in names: previous[name][chain] = np.nan
                continue
            ntotal[chain] += 1
            for name in names:
                value = float(row[name])
                target[name][chain] += value; total[name][chain] += value; squares[name][chain] += value*value
                if math.isfinite(previous[name][chain]):
                    products[name][chain] += previous[name][chain]*value; links[name][chain] += 1
                previous[name][chain] = value
    if not (np.all(nfirst == nfirst[0]) and np.all(nsecond == nsecond[0]) and nfirst[0] and nsecond[0]):
        fail('incomplete or nonuniform scalar halves')
    result = {'metadata': {key: metadata[key] for key in ('springs', 'chains', 'dt', 'steps', 'production_time', 'seed')},
              'first_frames_per_chain': int(nfirst[0]), 'second_frames_per_chain': int(nsecond[0]),
              'initial_coordinates_sha256': hashlib.sha256((directory/'initial.csv').read_bytes()).hexdigest(),
              'method': 'equal-duration within-chain averages; chains are statistical clusters; midpoint omitted',
              'observables': {}}
    for name in names:
        a, b = first[name]/nfirst, second[name]/nsecond
        drift = b-a
        # Lag-one correlation is diagnostic only: it demonstrates why frames
        # cannot be used as independent samples.
        n = ntotal
        mean = total[name]/n
        variance = squares[name]/n - mean*mean
        covariance = products[name]/np.maximum(links[name], 1) - mean*mean
        valid = variance > 1e-30
        lag_one = float(np.mean(covariance[valid]/variance[valid])) if np.any(valid) else None
        first_result, second_result = half_difference(a, reference, name), half_difference(b, reference, name)
        result['observables'][name] = {'first': first_result, 'second': second_result,
            'drift_second_minus_first': estimate(drift),
            'drift_z': float(estimate(drift)['mean']/estimate(drift)['se']) if estimate(drift)['se'] else None,
            'mean_chain_lag_one_autocorrelation': lag_one}
    return result


def compare(small, large):
    if small['metadata']['dt'] >= large['metadata']['dt']:
        fail('comparison requires increasing dt')
    same_initial = small['initial_coordinates_sha256'] == large['initial_coordinates_sha256']
    result = {'small_dt': small['metadata']['dt'], 'large_dt': large['metadata']['dt'],
              'same_initial_coordinates': same_initial, 'same_seed': small['metadata']['seed'] == large['metadata']['seed'],
              'method': 'conservative unpaired chain-cluster SE; identical initial-coordinate hashes are recorded but stochastic paths are not assumed paired',
              'observables': {}}
    for name, item in small['observables'].items():
        a, b = item['second']['estimate'], large['observables'][name]['second']['estimate']
        difference = b['mean']-a['mean']; se = math.hypot(a['se'], b['se'])
        result['observables'][name] = {'large_minus_small': difference, 'unpaired_se': se,
                                       'unpaired_z': difference/se if se else None}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--small', type=Path, required=True); parser.add_argument('--large', type=Path, required=True)
    parser.add_argument('--small-reference', type=Path, required=True); parser.add_argument('--large-reference', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): parser.error('refusing to overwrite report')
    small, large = run(args.small, args.small_reference), run(args.large, args.large_reference)
    args.report.write_text(json.dumps({'small': small, 'large': large, 'comparison': compare(small, large)}, indent=2, sort_keys=True)+'\n')
    print(args.report)


if __name__ == '__main__': main()
