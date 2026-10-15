#!/usr/bin/env python3
"""Direct-lag Rouse analysis and fixed Stage 1 validation. Requires NumPy only."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

PROJECT = Path(__file__).resolve().parent
Z_LIMIT = 5.0


def modes(n):
    m = n + 1
    p = np.arange(1, m)
    lam = 12 * np.sin(p * np.pi / (2*m))**2
    # Squared endpoint difference of orthonormal cosine eigenvectors.
    d2 = np.where(p % 2, 8/m * np.cos(p*np.pi/(2*m))**2, 0.0)
    return lam, d2


def variance(n, dt, steps):
    lam, _ = modes(n)
    a = 1-lam*dt
    stationary = 1/(lam*(1-lam*dt/2))
    return stationary + (1/lam-stationary)*a**(2*np.asarray(steps)[..., None])


def dimensions(n, dt, steps):
    lam, d2 = modes(n)
    v = variance(n, dt, steps)
    return np.stack(((v*lam).sum(axis=-1)/n,
                     3*(v*d2).sum(axis=-1),
                     3*v.sum(axis=-1)/(n+1)), axis=-1)


def correlation(n, dt, origins, lag_steps, mode1=False, continuous=False):
    lam, d2 = modes(n)
    weights = np.zeros(n) if mode1 else d2
    if mode1:
        weights[0] = 1
    if continuous:
        v = np.broadcast_to(1/lam, (len(origins), n))
        decay = np.exp(-lam*lag_steps*dt)
    else:
        v = variance(n, dt, origins)
        decay = (1-lam*dt)**lag_steps
    den = (v*weights).sum(axis=-1).mean()
    return float((v*weights*decay).sum(axis=-1).mean()/den)


def estimate(values):
    values = np.asarray(values)
    return float(values.mean()), float(values.std(ddof=1)/np.sqrt(len(values)))


def ratio(numerator, denominator):
    value = float(numerator.mean()/denominator.mean())
    influence = (numerator-value*denominator)/denominator.mean()
    return value, float(influence.std(ddof=1)/np.sqrt(len(influence)))


def record(name, value, se, reference, continuous=None):
    z = (value-reference)/se if se > 0 else (0 if value == reference else float('inf'))
    result = dict(name=name, value=float(value), se=float(se), reference=float(reference),
                  ci95=[float(value-1.96*se), float(value+1.96*se)], z=float(z),
                  passed=bool(np.isfinite(z) and abs(z) <= Z_LIMIT))
    if continuous is not None:
        result['continuous'] = float(continuous)
    return result


def load_samples(directory):
    directory = Path(directory)
    meta = json.loads((directory/'metadata.json').read_text())
    c, n, dt = meta['chains'], meta['springs'], meta['dt']
    if c < 2:
        raise ValueError('at least two independent chains are required for uncertainty estimates')
    # shortcut: histories fit RAM; use streaming/block analysis before large campaigns.
    data = np.atleast_1d(np.genfromtxt(directory/'samples.csv', names=True, delimiter=',', dtype=None, encoding='utf-8'))
    if len(data) % c:
        raise ValueError('incomplete sample frame')
    data = data.reshape(-1, c)
    if not np.all(data['chain'] == np.arange(c)):
        raise ValueError('chain order mismatch')
    for name in data.dtype.names:
        if not np.isfinite(data[name]).all():
            raise ValueError('nonfinite sample: '+name)
    steps = data['step'][:, 0].astype(np.uint64)
    if not np.all(data['step'] == steps[:, None]):
        raise ValueError('inconsistent sample step')
    return meta, data, steps


def analyze(directory):
    meta, data, steps = load_samples(directory)
    c, n, dt = meta['chains'], meta['springs'], meta['dt']
    full_steps = steps + meta['equil']
    continuous = np.array([1, n, n*(n+2)/(6*(n+1))])
    references = dimensions(n, dt, full_steps).mean(axis=0)
    results = []
    for i, name in enumerate(('q2', 'ree2', 'rg2')):
        value, se = estimate(data[name].mean(axis=0))
        results.append(record(name, value, se, references[i], continuous[i]))
    dynamics = []
    if len(steps) > 2:
        # The executable may append a shorter final interval; exclude it for lag analysis.
        delta = np.diff(steps)
        if delta[-1] != delta[0]:
            data, steps, full_steps = data[:-1], steps[:-1], full_steps[:-1]
        if not np.all(np.diff(steps) == steps[1]-steps[0]):
            raise ValueError('direct-lag analysis requires evenly spaced samples')
        stride = int(steps[1]-steps[0])
        tau = 1/modes(n)[0][0]
        vectors = {key: np.stack([data[f'{key}_{a}'] for a in 'xyz'], axis=-1)
                   for key in ('cm', 'ee', 'mode1')}
        lags = sorted(set(max(1, round(f*tau/(stride*dt))) for f in (.25, .5)))
        for lag in lags:
            if lag >= len(steps):
                continue
            lag_steps, time = lag*stride, lag*stride*dt
            displacements = vectors['cm'][lag:]-vectors['cm'][:-lag]
            chain_msd = (displacements**2).sum(axis=-1).mean(axis=0)
            value, se = estimate(chain_msd/(6*time))
            dynamics.append(record(f'D_cm_lag_{time:.6g}', value, se, 1/(n+1)))
            for key in ('ee', 'mode1'):
                start, end = vectors[key][:-lag], vectors[key][lag:]
                num = (start*end).sum(axis=-1).mean(axis=0)
                den = (start**2).sum(axis=-1).mean(axis=0)
                value, se = ratio(num, den)
                theory = correlation(n, dt, full_steps[:-lag], lag_steps, key == 'mode1')
                ct = correlation(n, dt, full_steps[:-lag], lag_steps, key == 'mode1', True)
                dynamics.append(record(f'C_{key}_lag_{time:.6g}', value, se, theory, ct))
                if key == 'mode1' and lag == lags[-1]:
                    if not 0 < value < 1:
                        raise ValueError('cannot infer positive longest relaxation time')
                    tau_value = -time/np.log(value)
                    tau_se = time*se/(value*np.log(value)**2)
                    tau_em = -dt/np.log1p(-modes(n)[0][0]*dt)
                    dynamics.append(record('tau1', tau_value, tau_se, tau_em, tau))
    stability = (meta['sampled_zero_bonds'] == 0 and meta['max_spacing_over_noise'] < .01)
    result = dict(metadata=meta, dimensions=results, dynamics=dynamics,
                  stability_passed=bool(stability),
                  passed=bool(stability and all(r['passed'] for r in results+dynamics)))
    return result


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def run(binary, output, args):
    output = Path(output)
    if output.exists():
        raise ValueError(f'refusing to overwrite {output}')
    log = Path(str(output)+'.log')
    with log.open('x') as stream:
        subprocess.run([str(binary), '--output', str(output), *map(str, args)],
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    result = analyze(output)
    save(output/'analysis.json', result)
    return result


def schedule(n, dt):
    interval = max(1, int(np.ceil(1/modes(n)[0][0]/(32*dt))))
    return interval, 40*interval


def suite(root):
    root = Path(root).resolve()
    # Reuse the executable's repository isolation rule for generated analysis artifacts.
    repo = PROJECT.parent.parent
    if root.is_relative_to(repo) and not root.is_relative_to(PROJECT):
        raise ValueError('validation output must stay inside the project or outside the repository')
    root.mkdir(parents=True, exist_ok=False)
    summary = dict(initialization=[], dynamics=[], precision=[], convergence=[], performance=[])
    for precision_index, precision in enumerate(('single', 'double')):
        binary = PROJECT/'build'/precision/'rouse'
        for n in (8, 32, 100):
            result = run(binary, root/f'{precision}_init_N{n}',
                         ['--springs', n, '--chains', 8192, '--steps', 0, '--seed', 20261015+n])
            summary['initialization'].append(result)
        for n in (8, 32, 100):
            for index, dt in enumerate((.01, .005, .0025)):
                interval, steps = schedule(n, dt)
                print(f'VALIDATING {precision} N={n} dt={dt} steps={steps}', flush=True)
                result = run(binary, root/f'{precision}_N{n}_dt{dt}',
                             ['--springs', n, '--chains', 512, '--dt', dt,
                              '--steps', steps, '--sample', interval,
                              '--seed', 710000+100*n+index+10000*precision_index])
                result['passed'] = result['passed'] and len(result['dynamics']) == 7
                summary['dynamics'].append(result)
                save(root/'summary.json', summary)
        # A separate fixed-size performance probe; no kernel optimization or campaign.
        timing = root/f'{precision}_timing'
        with Path(str(timing)+'.log').open('x') as stream:
            subprocess.run([str(binary), '--output', str(timing), '--springs', '31',
                            '--chains', '2048', '--dt', '.005', '--steps', '2000',
                            '--sample', '2000', '--seed', '991027'],
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
        summary['performance'].append(json.loads((timing/'metadata.json').read_text()))
    def config(result):
        meta = result['metadata']
        return meta['springs'], meta['dt_requested']
    singles = {config(r): r for r in summary['dynamics'] if r['metadata']['real_bits'] == 32}
    doubles = {config(r): r for r in summary['dynamics'] if r['metadata']['real_bits'] == 64}
    for key in singles:
        a, b = singles[key], doubles[key]
        for x, y in zip(a['dimensions'], b['dimensions']):
            # Compare statistical residuals: the effective float dt differs slightly.
            difference = (x['value']-x['reference'])-(y['value']-y['reference'])
            summary['precision'].append(record(f'N{key[0]}_dt{key[1]}_{x["name"]}', difference,
                                               np.hypot(x['se'], y['se']), 0))
    for bits in (32, 64):
        estimates = []
        for dt in (.01, .005, .0025):
            runs = [r for r in summary['dynamics'] if r['metadata']['real_bits'] == bits
                    and r['metadata']['dt_requested'] == dt]
            q = [r['dimensions'][0] for r in runs]
            weights = np.array([1/x['se']**2 for x in q])
            value = float(np.average([x['value']-1 for x in q], weights=weights))
            expected = float(np.average([x['reference']-1 for x in q], weights=weights))
            se = float(1/np.sqrt(weights.sum()))
            estimates.append(dict(dt=dt, bias=value, se=se, predicted_bias=expected))
        change = estimates[0]['bias']-estimates[-1]['bias']
        change_se = np.hypot(estimates[0]['se'], estimates[-1]['se'])
        summary['convergence'].append(dict(real_bits=bits, estimates=estimates,
                                           decrease_z=float(change/change_se)))
    summary['passed'] = all(r['passed'] for r in summary['initialization']+summary['dynamics']+summary['precision'])
    save(root/'summary.json', summary)
    print('PASS' if summary['passed'] else 'FAIL', root/'summary.json', flush=True)
    return summary['passed']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    one = sub.add_parser('analyze')
    one.add_argument('directory', type=Path)
    all_runs = sub.add_parser('suite')
    all_runs.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.command == 'suite':
        return 0 if suite(args.output) else 1
    directory = args.directory.resolve()
    if directory.is_relative_to(PROJECT.parent.parent) and not directory.is_relative_to(PROJECT):
        raise ValueError('analysis output must stay inside the project or outside the repository')
    result = analyze(directory)
    save(directory/'analysis.json', result)
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
