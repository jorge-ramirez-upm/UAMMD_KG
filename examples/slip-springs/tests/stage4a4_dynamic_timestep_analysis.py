#!/usr/bin/env python3
"""Read-only Stage 4A.4 stress-dynamics comparison from exported correlations."""
import argparse
import csv
import json
import math
from pathlib import Path

CHANNELS = ('Cxy', 'Cxz', 'Cyz', 'Cxx_yy', 'Cxx_zz', 'Cyy_zz')
WEIGHTS = dict(zip(CHANNELS, (1/5, 1/5, 1/5, 1/30, 1/30, 1/30)))
TARGETS = (.01, .05, .10)


def fail(message): raise ValueError(message)


def load(directory):
    directory = Path(directory)
    metadata = json.loads((directory/'stress_metadata.json').read_text())
    rows = []
    with (directory/'stress_correlations.csv').open(newline='') as handle:
        for raw in csv.DictReader(handle):
            row = {key: float(raw[key]) for key in ('lag_time', 'H', 'H_se', 'block_samples', 'pairs_per_chain', *CHANNELS, *(key+'_se' for key in CHANNELS))}
            row['block_samples'], row['pairs_per_chain'] = int(row['block_samples']), int(row['pairs_per_chain'])
            expected = sum(WEIGHTS[key]*row[key] for key in CHANNELS)
            if not math.isclose(expected, row['H'], rel_tol=3e-11, abs_tol=3e-11): fail('six-channel H mismatch')
            rows.append(row)
    if metadata['mode'] != 'every-step' or not rows or rows[0]['lag_time'] != 0: fail('requires every-step correlations with H(0)')
    return {'metadata': metadata, 'rows': rows}


def selected(data, target):
    rows, spacing = data['rows'], data['metadata']['spacing']
    exact = next((row for row in rows if math.isclose(row['lag_time'], target, abs_tol=spacing*1e-8)), None)
    row = exact or min(rows, key=lambda item: abs(item['lag_time']-target))
    width = row['block_samples'] * spacing
    if abs(row['lag_time']-target) > width/2 + spacing*1e-8: fail('target lacks an admissible exported bin')
    result = dict(row)
    result.update(target_time=target, exact_lag=exact is not None, lag_offset=row['lag_time']-target, block_width=width)
    h0 = rows[0]
    result['normalized_H'] = row['H']/h0['H']
    # Conservative propagation: no lag-zero/lag covariance is assumed.
    result['normalized_H_se'] = math.hypot(row['H_se']/h0['H'], row['H']*h0['H_se']/h0['H']**2)
    return result


def crossing(data, multiplier=0):
    rows = data['rows']; h0 = rows[0]
    target = (h0['H'] + multiplier*h0['H_se']) / math.e
    values = [row['H'] + multiplier*row['H_se'] for row in rows]
    for left, right, a, b in zip(rows, rows[1:], values, values[1:]):
        if a >= target >= b:
            fraction = (a-target)/(a-b)
            return left['lag_time'] + fraction*(right['lag_time']-left['lag_time'])
    return None


def compare(small, large):
    if small['metadata']['spacing'] >= large['metadata']['spacing']: fail('small/large timestep order invalid')
    result = {'small_dt': small['metadata']['spacing'], 'large_dt': large['metadata']['spacing'],
              'method': 'conservative unpaired propagation across timesteps; multi-tau bins selected without interpolation',
              'h0': {}, 'lags': [], 'crossing': {}}
    a, b = small['rows'][0], large['rows'][0]
    result['h0'] = {'small': {'H': a['H'], 'se': a['H_se']}, 'large': {'H': b['H'], 'se': b['H_se']},
                    'large_minus_small': b['H']-a['H'], 'unpaired_se': math.hypot(a['H_se'], b['H_se'])}
    result['h0']['z'] = result['h0']['large_minus_small']/result['h0']['unpaired_se']
    result['h0']['channels'] = {key: {
        'weight': WEIGHTS[key], 'large_minus_small_contribution': WEIGHTS[key]*(b[key]-a[key]),
        'unpaired_se': abs(WEIGHTS[key])*math.hypot(a[key+'_se'], b[key+'_se'])} for key in CHANNELS}
    for target in TARGETS:
        a, b = selected(small, target), selected(large, target)
        difference, se = b['H']-a['H'], math.hypot(a['H_se'], b['H_se'])
        normalized_difference = b['normalized_H']-a['normalized_H']
        normalized_se = math.hypot(a['normalized_H_se'], b['normalized_H_se'])
        channels = {}
        for key in CHANNELS:
            contribution, contribution_se = WEIGHTS[key]*(b[key]-a[key]), abs(WEIGHTS[key])*math.hypot(a[key+'_se'], b[key+'_se'])
            channels[key] = {'weight': WEIGHTS[key], 'large_minus_small_contribution': contribution,
                             'unpaired_se': contribution_se}
        result['lags'].append({'target_time': target, 'small': a, 'large': b,
                               'large_minus_small': difference, 'unpaired_se': se,
                               'upper_3sigma': abs(difference)+3*se,
                               'amplitude_gate': .05*small['rows'][0]['H'],
                               'gate': 'pass' if abs(difference)+3*se <= .05*small['rows'][0]['H'] else 'fail',
                               'normalized_large_minus_small': normalized_difference, 'normalized_unpaired_se': normalized_se,
                               'channels': channels})
    center_a, center_b = crossing(small), crossing(large)
    early_a, late_a = crossing(small, -3), crossing(small, 3)
    early_b, late_b = crossing(large, -3), crossing(large, 3)
    if None not in (center_a, center_b, early_a, late_a, early_b, late_b):
        delta = abs(center_b-center_a); allowance = .1*center_a
        upper = delta + max(center_a-early_a, late_a-center_a) + max(center_b-early_b, late_b-center_b)
        result['crossing'] = {'small': center_a, 'small_3se_interval': [early_a, late_a], 'large': center_b,
                              'large_3se_interval': [early_b, late_b], 'difference': center_b-center_a,
                              'conservative_upper_difference': upper, 'allowance': allowance,
                              'gate': 'pass' if upper <= allowance else 'unresolved'}
    else: result['crossing'] = {'gate': 'unresolved', 'reason': '1/e crossing not bracketed'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--small', type=Path, required=True); parser.add_argument('--large', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True); args = parser.parse_args()
    if args.report.exists(): parser.error('refusing to overwrite report')
    args.report.write_text(json.dumps(compare(load(args.small), load(args.large)), indent=2, sort_keys=True)+'\n')
    print(args.report)


if __name__ == '__main__': main()
