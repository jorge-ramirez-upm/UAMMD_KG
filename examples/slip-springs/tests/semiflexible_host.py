"""Frozen user-host campaign. Default generates commands; --run is long work.

Analysis streams CSV rows, retaining only per-chain summaries. A passing analysis
is necessary, not sufficient: also archive the plan's device/memory/tool evidence.
"""
import argparse
import csv
from functools import lru_cache
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain, langevin

PROJECT = Path(__file__).resolve().parents[1]
SEEDS = (420201, 420202, 420203)


def safe_output(path):
    path = path.resolve()
    repo = PROJECT.parents[1]
    if path.is_relative_to(repo) and not path.is_relative_to(PROJECT):
        raise ValueError('repository output must stay in examples/slip-springs')
    return path


def parameters(path, model):
    path.write_text(str(model.n)+'\n'+''.join(f'{b:.17g} {k:.17g}\n' for b, k in zip(model.b0, model.kb))
                    +'\n'.join(f'{k:.17g}' for k in model.kappa)+'\n')


def generate(root, build):
    root.mkdir(parents=True, exist_ok=False)
    models = [(f'N{n}-k{k}', Chain.homogeneous(n, kappa=k), 2048, 50 if n == 32 else 20)
              for n in (1, 8, 32) for k in (0, 2, 10)]
    models += [('heterogeneous', Chain([0.8, 1.2]*4, [20, 40]*4, [0, 0, 2, 0, 10, 0, 2, 0, 0]), 2048, 20),
               ('gaussian', Chain.homogeneous(8, b0=0, kb=3, kappa=0), 4096, 5)]
    manifest = []
    for precision in ('single', 'double'):
        binary = str((build/precision/'semiflexible').resolve())
        for label, model, chains, duration in models:
            p = root/f'{label}.txt'
            if not p.exists():
                parameters(p, model)
            for seed in SEEDS:
                for dt in ((0.001, 0.0005, 0.00025) if label == 'gaussian' else (0.0002, 0.0001, 0.00005)):
                    stride = round((0.01 if label == 'gaussian' else 0.02)/dt)
                    run = root/f'{precision}-{label}-s{seed}-h{dt}'
                    command = [binary, '--springs', str(model.n), '--chains', str(chains),
                               '--parameters', str(p), '--dt', str(dt), '--steps', str(round(duration/dt)),
                               '--sample', str(stride), '--seed', str(seed), '--output', str(run)]
                    manifest.append(dict(label=label, precision=precision, seed=seed, dt=dt, duration=duration,
                                         chains=chains, b0=model.b0.tolist(), kb=model.kb.tolist(),
                                         kappa=model.kappa.tolist(), output=str(run), command=command))
        # The larger one-step noise test in the frozen plan (zero force at t=0).
        p = root/'noise.txt'
        if not p.exists():
            parameters(p, Chain.homogeneous(1, b0=0, kb=3, kappa=0))
            np.savetxt(root/'zeros.txt', np.zeros((16384, 3)), fmt='%.1f')
        for seed in SEEDS:
            command = [binary, '--springs', '1', '--chains', '8192', '--parameters', str(p),
                       '--initial', str(root/'zeros.txt'), '--dt', '0.001', '--steps', '1',
                       '--sample', '1', '--seed', str(seed), '--zeta', '2', '--output', str(root/f'{precision}-noise-{seed}')]
            manifest.append(dict(label='noise', precision=precision, seed=seed, command=command,
                                 output=str(root/f'{precision}-noise-{seed}')))
    (root/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (root/'commands.sh').write_text('#!/bin/sh\nset -eu\n'+''.join(shlex.join(r['command'])+'\n' for r in manifest))
    print(f'Generated {len(manifest)} host experiments; no simulations executed. Commands: {root/"commands.sh"}')
    return manifest


def stats(values):
    values = np.asarray(values)
    return values.mean(axis=0), values.std(axis=0, ddof=1)/math.sqrt(len(values))


def radial_cdf(model, maximum):
    edges = np.linspace(0, maximum, 33)
    result = []
    for b, k in zip(model.b0, model.kb):
        grid = np.linspace(0, max(maximum, b+14/math.sqrt(k)), 40001)
        w = grid**2*np.exp(-k*(grid-b)**2/2)
        cdf = np.r_[0, np.cumsum((w[1:]+w[:-1])*(grid[1]-grid[0])/2)]
        cdf /= cdf[-1]
        result.append(np.interp(edges[1:], grid, cdf))
    return np.array(result)


def predictions(model):
    return _predictions(tuple(model.b0), tuple(model.kb), tuple(model.kappa))


@lru_cache(maxsize=32)
def _predictions(b0, kb, kappa):
    model = Chain(b0, kb, kappa)
    pred = model.equilibrium_predictions()
    subchains = {}
    rg2 = 0
    for i in range(model.n):
        for j in range(i+1, model.n+1):
            sub = Chain(model.b0[i:j], model.kb[i:j], np.r_[0, model.kappa[i+1:j], 0])
            key = (tuple(sub.b0), tuple(sub.kb), tuple(sub.kappa))
            if key not in subchains:
                subchains[key] = sub.equilibrium_predictions()['re2']
            rg2 += subchains[key]/(model.n+1)**2
    result = dict(mean_r=pred['mean_r'].mean(), mean_r2=pred['mean_r2'].mean(), re2=pred['re2'], rg2=rg2)
    for s in range(1, min(4, model.n-1)+1):
        result[f'tangent{s}'] = np.mean([math.prod(langevin(k) for k in model.kappa[i+1:i+s+1])
                                        for i in range(model.n-s)])
    return pred, result


def analyze(root):
    manifest = json.loads((root/'manifest.json').read_text())
    failures, summaries = [], []

    def gate(label, values, target, relative=0.005, floor=0):
        mean, se = stats(values)
        if not np.all(np.isfinite(mean)) or np.any(np.abs(mean-target) > 6*se+relative*np.abs(target)+floor):
            failures.append(label)
        return np.asarray(mean).tolist(), np.asarray(se).tolist()

    for run in manifest:
        directory = Path(run['output'])
        label = directory.name
        meta = json.loads((directory/'metadata.json').read_text())
        if (directory/'failure.json').exists():
            failures.append(label+': GPU failure')
        if run['label'] == 'noise':
            final = np.genfromtxt(directory/'final.csv', delimiter=',', names=True)
            noise = np.column_stack([final[k] for k in ('x', 'y', 'z')])/math.sqrt(0.001)
            gate(label+': noise mean', noise, 0, relative=0)
            # Frozen theoretical sampling thresholds, not fitted SE for these gates.
            n = len(noise)
            if (np.any(np.abs(noise.mean(axis=0)) >= 6/math.sqrt(n))
                    or np.any(np.abs(noise.var(axis=0, ddof=1)-1) >= 6*math.sqrt(2/(n-1)))
                    or np.max(np.abs(np.cov(noise.T)-np.diag(noise.var(axis=0, ddof=1)))) >= 6/math.sqrt(n)):
                failures.append(label+': noise covariance/variance')
            continue
        model = Chain(run['b0'], run['kb'], run['kappa'])
        pred, targets = predictions(model)
        chains, n = run['chains'], model.n
        initial = np.zeros((chains, len(targets)))
        averaged = np.zeros_like(initial)
        counts = np.zeros(chains, dtype=int)
        cm_targets = (0.02, 0.1, 1, 5, 20, 50)
        cm = {t: [] for t in cm_targets if t <= run['duration']}
        gaussian_time, gaussian_step, gaussian_mono, gaussian_cm = None, 0, [], []
        nonfinite_seen = False

        def gaussian_frame():
            if gaussian_time is None:
                return
            t = gaussian_time
            lam = 12*np.sin(np.arange(1, n+1)*np.pi/(2*(n+1)))**2
            a = 1-run['dt']*lam
            vn = a**(2*gaussian_step)/lam + 2*run['dt']*(1-a**(2*gaussian_step))/(1-a*a)
            exact = 6*t/(n+1)+3/(n+1)*np.sum(vn+1/lam-2*a**gaussian_step/lam)
            gate(label+': exact EM monomer MSD '+str(t), gaussian_mono, exact)
            gate(label+': Gaussian COM '+str(t), gaussian_cm, 6*t/(n+1))
            if run['dt'] == 0.00025:
                continuous = 6*t/(n+1)+6/(n+1)*np.sum(-np.expm1(-lam*t)/lam)
                gate(label+': continuous monomer MSD '+str(t), gaussian_mono, continuous, 0.01)

        # Only O(C*N) analysis state; no complete time history in memory.
        with (directory/'samples.csv').open() as f:
            for row in csv.DictReader(f):
                c, t = int(row['chain']), float(row['time'])
                values = [float(row[k]) for k in targets]
                if not nonfinite_seen and not all(math.isfinite(float(v)) for v in row.values()):
                    failures.append(label+': nonfinite observation')
                    nonfinite_seen = True
                if int(row['step']) == 0:
                    initial[c] = values
                if t >= run['duration']/2-1e-10:
                    averaged[c] += values
                    counts[c] += 1
                for target in cm:
                    if abs(t-target) < 1e-9:
                        cm[target].append(float(row['cm_msd']))
                if run['label'] == 'gaussian':
                    if gaussian_time is not None and t != gaussian_time:
                        gaussian_frame()
                        gaussian_mono, gaussian_cm = [], []
                    gaussian_time, gaussian_step = t, int(row['step'])
                    gaussian_mono.append(float(row['monomer_msd']))
                    gaussian_cm.append(float(row['cm_msd']))
        if run['label'] == 'gaussian':
            gaussian_frame()
        if np.any(counts == 0):
            failures.append(label+': no final-half samples')
            continue
        averaged /= counts[:, None]
        result = dict(run=label, dt=run['dt'], label=run['label'], precision=run['precision'], seed=run['seed'], observables={})
        for index, (key, target) in enumerate(targets.items()):
            floor = 0.005 if key.startswith('tangent') else 0
            gate(label+': initial '+key, initial[:, index], target, 0.001, floor)
            mean, se = stats(averaged[:, index])
            result['observables'][key] = dict(mean=float(mean), se=float(se), target=float(target))
            # Finest only: continuous equilibrium acceptance; others quantify bias.
            if run['dt'] == (0.00025 if run['label'] == 'gaussian' else 0.00005):
                gate(label+': finest '+key, averaged[:, index], target, 0.005, floor)
        for t, values in cm.items():
            if len(values) != chains:
                failures.append(label+': missing COM time '+str(t))
            else:
                gate(label+': COM '+str(t), values, 6*t/(n+1))
        expected_cdf = radial_cdf(model, meta['histogram_max'])
        lengths = np.zeros((chains, n))
        with (directory/'initial_bonds.csv').open() as f:
            for row in csv.DictReader(f):
                lengths[int(row['chain']), int(row['bond'])] = float(row['length'])
        gate(label+': initial bond means', lengths, pred['mean_r'], 0.001)
        gate(label+': initial bond squares', lengths**2, pred['mean_r2'], 0.001)
        edges = np.linspace(0, meta['histogram_max'], 33)[1:]
        for b in range(n):
            empirical = (lengths[:, b, None] <= edges).mean(axis=0)
            if np.max(np.abs(empirical-expected_cdf[b])) > 0.065:
                failures.append(label+': initial radial CDF bond '+str(b))
        radial = np.zeros((chains, n, 2));cdf = np.zeros((chains, n, 32))
        with (directory/'bond_statistics.csv').open() as f:
            for row in csv.DictReader(f):
                c,b = int(row['chain']),int(row['bond'])
                radial[c,b] = [float(row['mean_r']),float(row['mean_r2'])]
                bins = np.array([int(row[f'bin{i}']) for i in range(33)])
                frames = int(row['frames'])
                if bins.sum() != frames:
                    failures.append(label+': histogram counts')
                cdf[c,b] = np.cumsum(bins[:32])/frames
        if run['dt'] == (0.00025 if run['label'] == 'gaussian' else 0.00005):
            gate(label+': final-half radial means', radial[:,:,0], pred['mean_r'])
            gate(label+': final-half radial squares', radial[:,:,1], pred['mean_r2'])
            if np.max(np.abs(cdf.mean(axis=0)-expected_cdf)) > 0.03:
                failures.append(label+': final-half radial CDF')
        result['cdf_max_cluster_se'] = float(stats(cdf)[1].max())
        result['minimum_sampled_bond'] = meta['minimum_sampled_bond']
        lmin = meta['minimum_sampled_bond']
        result['stiffness_indicator'] = run['dt']*max(max(model.kb),max(model.kappa)/lmin**2)
        summaries.append(result)
        print(label, 'analyzed', flush=True)
    # Compare timestep estimates separately for each replica and precision.
    groups, timestep_checks = {}, []
    for result in summaries:
        groups.setdefault((result['label'],result['precision'],result['seed']), []).append(result)
    for group, runs in groups.items():
        coarse,middle,fine = sorted(runs, key=lambda r:r['dt'], reverse=True)
        for key in fine['observables']:
            c,m,f = [r['observables'][key] for r in (coarse,middle,fine)]
            floor = 0.005 if key.startswith('tangent') else 0
            uncertainty = 6*math.hypot(m['se'],f['se'])
            if abs(f['mean']-m['mean']) > uncertainty+0.005*abs(f['target'])+floor:
                failures.append(str(group)+': refinement '+key)
            resolved = abs(c['mean']-c['target']) > 6*c['se']
            timestep_checks.append(dict(group=list(group), observable=key, coarse_bias_resolved=resolved,
                                        coarse_error=abs(c['mean']-c['target']), finest_error=abs(f['mean']-f['target'])))
            if resolved:
                # A resolved coarse bias must decrease by >=25%; account for
                # uncertainty in both estimates rather than labeling noise bias.
                if abs(f['mean']-f['target']) > 0.75*abs(c['mean']-c['target'])+6*math.hypot(c['se'],f['se']):
                    failures.append(str(group)+': resolved bias trend '+key)
    replicas = {}
    for result in summaries:
        replicas.setdefault((result['label'],result['precision'],result['dt']), []).append(result)
    for group, runs in replicas.items():
        for i, left in enumerate(runs):
            for right in runs[i+1:]:
                for key, a in left['observables'].items():
                    b = right['observables'][key]
                    floor = 0.005 if key.startswith('tangent') else 0
                    if abs(a['mean']-b['mean']) > 6*math.hypot(a['se'],b['se'])+0.005*abs(a['target'])+floor:
                        failures.append(str(group)+': replica disagreement '+key)
    report = dict(failures=failures, summaries=summaries, timestep_checks=timestep_checks,
                  status='statistical gates passed; manual host evidence still required' if not failures else 'failed')
    target = root/'analysis.json'
    if target.exists():
        raise FileExistsError('refusing to overwrite analysis.json')
    target.write_text(json.dumps(report, indent=2)+'\n')
    print(report['status'], 'failures:', len(failures))
    return bool(failures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--build', type=Path, default=PROJECT/'build')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--analyze', type=Path)
    args = parser.parse_args()
    if args.analyze:
        return analyze(safe_output(args.analyze))
    if args.output is None:
        parser.error('--output or --analyze required')
    manifest = generate(safe_output(args.output), args.build.resolve())
    if args.run:
        for run in manifest:
            subprocess.run(run['command'], check=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
