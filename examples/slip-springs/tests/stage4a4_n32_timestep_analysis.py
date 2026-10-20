#!/usr/bin/env python3
"""Read-only N32 comparison, reusing the validated Stage 4A.4 analyzers."""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

import stage4a4_dynamic_timestep_analysis as dynamic
import stage4a4_static_drift_analysis as static
from stage4a4_intermediate_timestep_analysis import histogram, cost

UNAVAILABLE = [
    'stretching and bending energies (1%): no trajectory energy output',
    'local-angle distribution (TV 0.02): no trajectory angle histogram',
    'end-to-end distribution: no trajectory distribution diagnostic',
    'raw bond-vector correlations along the full contour: no trajectory output; tangent1..4 are available',
    'bond histogram first/second-half stationarity: only the midpoint-inclusive second-half histogram is emitted',
]


def decision(delta, se, tolerance):
    lower, upper = max(0., abs(delta)-3*se), abs(delta)+3*se
    return dict(difference=delta, se=se, lower_3se=lower, upper_3se=upper, tolerance=tolerance,
                decision='pass' if upper <= tolerance else ('fail' if lower > tolerance else 'unresolved'))


def validate_bond_histogram(directory, meta):
    """observe(0) and sample multiples accumulate iff step >= steps//2."""
    first_index = (meta['steps']//2 + meta['sample'] - 1)//meta['sample']
    frames = meta['steps']//meta['sample'] - first_index + 1
    seen = set()
    with (directory/'bond_statistics.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            pair = int(row['chain']), int(row['bond'])
            bins = [int(row[f'bin{i}']) for i in range(33)]
            if (pair in seen or not (0 <= pair[0] < 512 and 0 <= pair[1] < 32) or
                    int(row['frames']) != frames or min(bins) < 0 or sum(bins) != frames or
                    not all(math.isfinite(float(value)) for value in row.values())):
                raise ValueError('invalid or incomplete bond histogram')
            seen.add(pair)
    if len(seen) != 512*32: raise ValueError('missing bond histogram rows')


def validate(directory, dt, reference):
    """Reject truncated/duplicate/nonfinite evidence before existing analyzers read it."""
    meta = json.loads((directory/'metadata.json').read_text())
    expected = dict(springs=32, chains=512, precision_bits=64, seed=433201,
                    steps=round(20/dt), sample=round(.01/dt), dt=dt,
                    production_time=20., kbt=1., zeta=1.,
                    initialization_method='CPU-direct-equilibrium')
    for key, value in expected.items():
        if meta.get(key) != value: raise ValueError(f'{directory}: unexpected {key}')
    parameters = [float(x) for x in (directory/'parameters.txt').read_text().split()]
    if parameters != [32.] + [1., 30.]*32 + [0.] + [reference['kappa']]*31 + [0.]:
        raise ValueError('physical parameter mismatch')
    counts = np.zeros(512, dtype=int)
    with (directory/'samples.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            chain = int(row['chain'])
            if not 0 <= chain < 512: raise ValueError('invalid chain')
            index = counts[chain]
            if (int(row['step']) != index*meta['sample'] or
                    not math.isclose(float(row['time']), index*.01, abs_tol=1e-10)):
                raise ValueError('incomplete, duplicated or unordered scalar clock')
            if not all(math.isfinite(float(value)) for value in row.values()) or float(row['min_length']) <= 0:
                raise ValueError('nonfinite or invalid sampled geometry')
            counts[chain] += 1
    if not np.all(counts == 2001): raise ValueError('incomplete scalar trajectory')
    validate_bond_histogram(directory, meta)
    stress = json.loads((directory/'stress_metadata.json').read_text())
    for key, value in dict(mode='every-step', frames=meta['steps']+1, spacing=dt,
                           batch=256, cpu_workers=8, levels=24, slots=32, coarsening=2,
                           raw_connected=False, empirical_mean_subtraction=False).items():
        if stress.get(key) != value: raise ValueError(f'unexpected stress {key}')
    data = dynamic.load(directory)
    previous = -1.
    for row in data['rows']:
        if (not all(math.isfinite(value) for value in row.values()) or
                row['lag_time'] <= previous or row['pairs_per_chain'] < 1 or row['block_samples'] < 1 or
                any(row[key] < 0 for key in ('H_se', *(key+'_se' for key in dynamic.CHANNELS)))):
            raise ValueError('invalid exported stress evidence')
        previous = row['lag_time']
    if data['rows'][0]['H'] <= 0: raise ValueError('nonpositive H(0)')
    # The established capacity audit requires at least 16 block origins.
    data['rows'] = [row for row in data['rows'] if row['pairs_per_chain'] >= 16]
    return meta, data


def distributions(directory, reference_path):
    result = histogram(directory, reference_path)
    ref = json.loads(reference_path.read_text())
    reference_se = ref['histogram']['se'] + [sum(ref['histogram']['se'])]
    se = [math.hypot(a, b) for a, b in zip(result['chain_se'], reference_se)]
    # Triangle inequality gives a conservative TV uncertainty bound, without
    # treating correlated histogram bins as independent observations.
    result['total_variation_gate'] = decision(result['total_variation'], .5*sum(se), .02)
    result['bin_gates'] = [decision(d, s, .005 if i == 32 else .01)
                           for i, (d, s) in enumerate(zip(result['difference'], se))]
    result['scope'] = 'second-half bond histogram, 10 <= t <= 20 at spacing 0.01 (both endpoints included); all finite bins checked at 0.01, overflow at 0.005'
    return result


def dynamics(small, large):
    result = dynamic.compare(small, large)
    result['h0']['relative_discrepancy'] = result['h0']['large_minus_small']/small['rows'][0]['H']
    result['h0']['decision'] = 'diagnostic only; no approved amplitude threshold'
    for item in result['lags']:
        # The original analyzer supplies nearest-bin diagnostics. A different
        # center cannot substantiate an identical-physical-lag accuracy gate.
        a, b = item['small'], item['large']
        item['nearest_bin_diagnostic_gate'] = item.pop('gate')
        if a['exact_lag'] and b['exact_lag']:
            item['gate'] = decision(item['large_minus_small'], item['unpaired_se'], item['amplitude_gate'])['decision']
        else:
            item['gate'] = 'unresolved'
            item['reason'] = 'requested identical physical lag is not exported by both hierarchies'
        item['block_average_caveat'] = 'different block widths remain; these are block-mean correlations'
    return result


def analyze(small_dir, large_dir, reference_path):
    ref = json.loads(reference_path.read_text())
    if (ref['springs'] != 32 or ref['kappa'] not in (0, 10) or ref['chains'] != 65536 or
            ref['method'] != 'exact-independent-equilibrium-sampling' or
            (ref['b0'], ref['kb'], ref['kbt']) != (1., 30., 1.)):
        raise ValueError('unexpected exact equilibrium reference')
    _, small_data = validate(small_dir, .000025, ref)
    _, large_data = validate(large_dir, .0005, ref)
    statics, histograms, costs = {}, {}, {}
    for name, directory in (('small', small_dir), ('large', large_dir)):
        report = static.run(directory, reference_path)
        for key, value in report['observables'].items():
            _, tolerance, scale = static.reference_for(key, ref)
            drift = value['drift_second_minus_first']
            value['stationarity'] = decision(drift['mean']/scale, drift['se']/scale, tolerance)
        statics[name] = report
        histograms[name] = distributions(directory, reference_path)
        a, b = cost(directory)
        costs[name] = dict(simulator=a, stress=b)
    decisions = []
    for report in statics.values():
        for item in report['observables'].values():
            decisions.extend([item['first']['decision'], item['second']['decision'], item['stationarity']['decision']])
    for report in histograms.values():
        decisions.append(report['total_variation_gate']['decision'])
        decisions.extend(item['decision'] for item in report['bin_gates'])
    dynamic_result = dynamics(small_data, large_data)
    decisions.extend(item['gate'] for item in dynamic_result['lags'])
    decisions.append(dynamic_result['crossing']['gate'])
    acceptance = 'rejected' if 'fail' in decisions else 'unresolved'
    return dict(status='completed-input-analysis', acceptance=acceptance,
                scope='N32 short-time timestep validation; no terminal relaxation claim',
                static=statics, static_comparison=static.compare(statics['small'], statics['large']),
                bond_histograms=histograms, dynamic=dynamic_result,
                unresolved_required_diagnostics=UNAVAILABLE, cost=costs,
                uncertainty='independent chains; conservative unpaired timestep propagation; no origin-count SE')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('small', 'large', 'reference', 'report'): parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): parser.error('refusing to overwrite report')
    result = analyze(args.small, args.large, args.reference)
    with args.report.open('x') as stream: json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
    print(args.report)


if __name__ == '__main__': main()
