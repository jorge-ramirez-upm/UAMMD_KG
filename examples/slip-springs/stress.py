#!/usr/bin/env python3
"""Per-chain direct-lag stress analysis and Stage 2A scientific validation."""
import argparse
from pathlib import Path
import subprocess
import sys
import numpy as np
import validate as rouse

CHANNELS = ('xy', 'xz', 'yz', 'xx-yy', 'xx-zz', 'yy-zz')
TENSOR = ('Sxx', 'Syy', 'Szz', 'Sxy', 'Sxz', 'Syz')
LAGS = (0, 1, 4, 16, 32)


def reference(n, dt, origins, lag, continuous=False):
    """Return normalized shear/normal-difference and raw diagonal references."""
    lam, _ = rouse.modes(n)
    if continuous:
        squared = np.exp(-2*lam*dt*lag).sum()
        return float(squared), float(n*n+2*squared)
    origins = np.asarray(origins, dtype=np.uint64)
    old = rouse.variance(n, dt, origins)
    new = rouse.variance(n, dt, origins+lag)
    covariance = lam*old*(1-lam*dt)**lag
    # Wick contraction at EACH origin, then average; these operations do not commute.
    squared = (covariance**2).sum(axis=-1)
    diagonal = (lam*old).sum(axis=-1)*(lam*new).sum(axis=-1)+2*squared
    return float(squared.mean()), float(diagonal.mean())


def direct_products(values, lag):
    if lag < 0 or lag >= len(values):
        raise ValueError('lag must index the available sample history')
    return (values[:len(values)-lag]*values[lag:]).mean(axis=0)


def check_location(directory):
    path = Path(directory).resolve()
    if path.is_relative_to(rouse.PROJECT.parent.parent) and not path.is_relative_to(rouse.PROJECT):
        raise ValueError('analysis outputs must stay in the project or outside the repository')
    return path


def analyze(directory):
    directory = check_location(directory)
    meta, data, steps = rouse.load_samples(directory)
    if np.any(steps[1:] <= steps[:-1]):
        raise ValueError('sample steps must increase strictly')
    if len(steps) > 2 and np.diff(steps)[-1] != np.diff(steps)[0]:
        data, steps = data[:-1], steps[:-1]
    if len(steps) > 1 and (np.any(np.diff(steps) == 0) or not np.all(np.diff(steps) == steps[1]-steps[0])):
        raise ValueError('direct stress lags require equally spaced samples')
    n, dt = meta['springs'], meta['dt']
    origins = steps+meta['equil']
    tensor = np.stack([data[name] for name in TENSOR], axis=-1)
    # Dividing differences by2 makes their PRODUCTS carry the required factor1/4.
    channels = np.stack((tensor[..., 3], tensor[..., 4], tensor[..., 5],
                         (tensor[..., 0]-tensor[..., 1])/2,
                         (tensor[..., 0]-tensor[..., 2])/2,
                         (tensor[..., 1]-tensor[..., 2])/2), axis=-1)
    means, moments, correlations, diagonals, isotropy = [], [], [], [], []
    second, _ = reference(n, dt, origins, 0)
    diagonal_mean = float((rouse.variance(n, dt, origins)*rouse.modes(n)[0]).sum(axis=-1).mean())
    for j, name in enumerate(CHANNELS):
        factor = 1 if j < 3 else 2
        value, se = rouse.estimate(channels[..., j].mean(axis=0)*factor)
        means.append(rouse.record('mean_'+name, value, se, 0))
        value, se = rouse.estimate((channels[..., j]**2).mean(axis=0))
        record = rouse.record('second_'+name, value, se, second, n)
        record.update(raw_value=value*factor**2, raw_se=se*factor**2, raw_reference=second*factor**2)
        moments.append(record)
    for j, name in enumerate(TENSOR[:3]):
        value, se = rouse.estimate(tensor[..., j].mean(axis=0))
        means.append(rouse.record('mean_'+name, value, se, diagonal_mean, n))
    retained, retained_diagonal, lag_steps, origin_counts = [], [], [], []
    stride = int(steps[1]-steps[0]) if len(steps) > 1 else 0
    for lag in LAGS:
        if lag >= len(steps):
            continue
        ell = lag*stride
        theory, diagonal_theory = reference(n, dt, origins[:len(steps)-lag], ell)
        continuous, diagonal_continuous = reference(n, dt, origins[:len(steps)-lag], ell, True)
        per_chain = direct_products(channels, lag)
        per_chain_diagonal = direct_products(tensor[..., :3], lag)
        retained.append(per_chain)
        retained_diagonal.append(per_chain_diagonal)
        lag_steps.append(ell)
        origin_counts.append(len(steps)-lag)
        for j, name in enumerate(CHANNELS):
            value, se = rouse.estimate(per_chain[:, j])
            result = rouse.record(name, value, se, theory, continuous)
            factor = 1 if j < 3 else 4
            result.update(lag_samples=lag, lag_steps=ell, lag_time=ell*dt,
                          raw_value=value*factor, raw_se=se*factor, raw_reference=theory*factor)
            correlations.append(result)
            if j:
                value, se = rouse.estimate(per_chain[:, j]-per_chain[:, 0])
                difference = rouse.record(name+'-xy', value, se, 0)
                difference['lag_samples'] = lag
                isotropy.append(difference)
        for j, name in enumerate(TENSOR[:3]):
            value, se = rouse.estimate(per_chain_diagonal[:, j])
            result = rouse.record(name, value, se, diagonal_theory, diagonal_continuous)
            result.update(lag_samples=lag, lag_steps=ell, lag_time=ell*dt)
            diagonals.append(result)
    # shortcut: bounded direct histories fit RAM; replace with streaming before large campaigns.
    np.savez_compressed(directory/'stress_chain_contributions.npz', channels=np.array(CHANNELS),
                        contributions=np.array(retained), diagonal_contributions=np.array(retained_diagonal),
                        chain_ids=np.arange(meta['chains'], dtype=np.uint64),
                        lag_steps=np.array(lag_steps, dtype=np.uint64), origins_per_lag=origin_counts)
    records = means+moments+correlations+diagonals+isotropy
    stable = meta['sampled_zero_bonds'] == 0 and meta['max_spacing_over_noise'] < .01
    return dict(metadata=meta, means=means, moments=moments, correlations=correlations,
                diagonal_correlations=diagonals, isotropy=isotropy, stability_passed=bool(stable),
                checks=len(records), passed=bool(stable and all(x['passed'] for x in records)))


def suite(output):
    root = check_location(output)
    root.mkdir(parents=True, exist_ok=False)
    summary = dict(initialization=[], dynamics=[], precision=[], convergence=[])
    for precision_index, precision in enumerate(('single', 'double')):
        binary = rouse.PROJECT/'build'/precision/'rouse'
        cases = [(n, None) for n in (8, 32, 100)] + [(n, index) for n in (8, 32, 100) for index in range(3)]
        for n, index in cases:
            initial = index is None
            dt = .005 if initial else (.01, .005, .0025)[index]
            stride = round(.05/dt)
            chains, steps = (8192, 0) if initial else (2048, 64*stride)
            seed = (20262015+n if initial else 820000+100*n+index)+10000*precision_index
            name = f'{precision}_init_N{n}' if initial else f'{precision}_N{n}_dt{dt}'
            directory = root/name
            print('STRESS', name, 'seed', seed, flush=True)
            with Path(str(directory)+'.log').open('x') as log:
                subprocess.run([str(binary), '--springs', str(n), '--chains', str(chains),
                                '--dt', str(dt), '--steps', str(steps), '--sample', str(stride),
                                '--equil', '0', '--seed', str(seed), '--output', str(directory)],
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            result = analyze(directory)
            if not initial:
                result['passed'] = result['passed'] and len(result['correlations']) == 30
            rouse.save(directory/'stress_analysis.json', result)
            summary['initialization' if initial else 'dynamics'].append(result)
            rouse.save(root/'summary.json', summary)
    def key(r):
        return r['metadata']['springs'], r['metadata']['dt_requested']
    singles = {key(r): r for r in summary['dynamics'] if r['metadata']['real_bits'] == 32}
    doubles = {key(r): r for r in summary['dynamics'] if r['metadata']['real_bits'] == 64}
    for config, first in singles.items():
        second = doubles[config]
        for x, y in zip(first['moments']+first['correlations'], second['moments']+second['correlations']):
            difference = (x['value']-x['reference'])-(y['value']-y['reference'])
            result = rouse.record(f'N{config[0]}_dt{config[1]}_'+x['name'], difference,
                                  np.hypot(x['se'], y['se']), 0)
            if 'lag_samples' in x:
                result['lag_samples'] = x['lag_samples']
            summary['precision'].append(result)
    for bits in (32, 64):
        for j, channel in enumerate(CHANNELS):
            estimates = []
            for dt in (.01, .005, .0025):
                cases = [r for r in summary['dynamics'] if r['metadata']['real_bits'] == bits
                         and r['metadata']['dt_requested'] == dt]
                moments = [r['moments'][j] for r in cases]
                ns = np.array([r['metadata']['springs'] for r in cases])
                errors = np.array([x['se'] for x in moments])/ns
                weights = 1/errors**2
                measured = float(np.average(np.array([x['value'] for x in moments])/ns-1, weights=weights))
                expected = float(np.average(np.array([x['reference'] for x in moments])/ns-1, weights=weights))
                result = rouse.record('bias_'+channel, measured, 1/np.sqrt(weights.sum()), expected, 0)
                result['dt'] = dt
                estimates.append(result)
            change = estimates[0]['value']-estimates[-1]['value']
            change_se = float(np.hypot(estimates[0]['se'], estimates[-1]['se']))
            summary['convergence'].append(dict(real_bits=bits, channel=channel, estimates=estimates,
                                               decrease=change, decrease_se=change_se,
                                               decrease_z=change/change_se,
                                               passed=bool(change >= 1.96*change_se and all(x['passed'] for x in estimates))))
    summary['checks'] = sum(r['checks'] for r in summary['initialization']+summary['dynamics'])+len(summary['precision'])+4*len(summary['convergence'])
    summary['passed'] = all(r['passed'] for group in ('initialization', 'dynamics', 'precision', 'convergence') for r in summary[group])
    rouse.save(root/'summary.json', summary)
    print('PASS' if summary['passed'] else 'FAIL', summary['checks'], root/'summary.json', flush=True)
    return summary['passed']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('analyze', 'suite'))
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if args.command == 'suite':
        return 0 if suite(args.directory) else 1
    result = analyze(args.directory)
    rouse.save(args.directory/'stress_analysis.json', result)
    print('PASS' if result['passed'] else 'FAIL', result['checks'], 'checks;', args.directory/'stress_analysis.json')
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
