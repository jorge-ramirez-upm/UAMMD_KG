#!/usr/bin/env python3
"""Prepared read-only N64 static audit. Review before authorizing execution."""
import os
# Set before importing NumPy/SciPy, including indirectly through existing helpers.
for _pool in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS'):
    os.environ[_pool] = '2'
os.environ['OMP_THREAD_LIMIT'] = '2'

import argparse
import csv
import itertools
import math
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t
import e1_d2a5_n64_analyze as auth
from e1_d16b_analysis import acf_diagnostic, canonical_population
from semiflexible_reference import langevin, radial_moments

BASE = Path('/home/jramirez/UAMMD_KG-evidence/d2a5-statics/n64-v1')
PRIMARY = ('re2', 'rg2', 'mean_r', 'mean_r2', 'tangent1')
# Frozen before looking at any differences. Initialization has its own one-frame row.
WINDOWS = {'initial': (0, 0), 'post_initial': (10, 10000),
           'early': (10, 2000), 'middle': (4000, 6000), 'late': (8000, 10000)}
require = auth.require


def output_path(path):
    path = auth.regular_path(Path(path).absolute())
    base = auth.regular_path(BASE).resolve()
    resolved = path.resolve()
    require(resolved != base and resolved.is_relative_to(base), 'output must be a child of static root')
    return resolved


def frames(path, columns, count, steps, stride):
    """Streaming, bounded by one observation frame; strict schema/order/clock."""
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == columns, f'CSV schema: {path}')
        for step in range(0, steps + 1, stride):
            batch = list(itertools.islice(reader, count))
            require(len(batch) == count, f'missing frame: {path}, {step}')
            for i, row in enumerate(batch):
                require(set(row) == set(columns) and all(v is not None for v in row.values()), 'CSV shape')
                require(all(math.isfinite(float(v)) for v in row.values()), 'nonfinite static input')
                require(row['step'] == str(step) and float(row['time']) == step*.0001, 'static clock')
                label = 'spring' if 'spring' in columns and path.name == 'equilibrium_connectors.csv' else 'chain'
                if path.name == 'equilibrium_sites.csv':
                    require(int(row['chain']) == i//65 and int(row['bead']) == i%65, 'site order')
                elif count > 1:
                    require(int(row[label]) == i, 'static label order')
            yield step*.0001, batch
        require(next(reader, None) is None, f'extra frame: {path}')


def backbone(rows):
    a = {k: np.array([float(r[k]) for r in rows]) for k in
         ('re2', 'rg2', 'mean_r', 'mean_r2', 'tangent1', 'tangent2', 'tangent3', 'tangent4')}
    require(len(rows) == 256 and all(np.isfinite(v).all() for v in a.values()), '256 finite chains')
    require(all((a[k] >= 0).all() for k in ('re2', 'rg2', 'mean_r', 'mean_r2')), 'negative size/length')
    result = {k: float(v.mean()) for k, v in a.items()}
    x, y = a['re2'], a['rg2']
    result.update(spatial_var_re2=float(x.var(ddof=1)), spatial_var_rg2=float(y.var(ddof=1)),
                  spatial_cov_re2_rg2=float(np.dot(x-x.mean(), y-y.mean())/255),
                  raw_re4=float(np.mean(x*x)), raw_rg4=float(np.mean(y*y)),
                  stretch_energy=15*64*(result['mean_r2']-2*result['mean_r']+1))
    return result


def context(connectors, populations, sites, tangents):
    e = np.array([[float(r[k]) for k in ('ex', 'ey', 'ez')] for r in connectors])
    e2 = np.array([float(r['e2']) for r in connectors])
    z = np.array([int(r['z']) for r in populations])
    require(len(e) == 4096 and z.shape == (256,) and z.sum() == 4096, 'canonical population')
    require(np.allclose(np.sum(e*e, axis=1), e2, rtol=2e-12, atol=2e-12), 'connector norm')
    require(np.all((z >= 0) & (z <= 65)), 'population bounds')
    result = dict(connector_e2=float(e2.mean()), connector_e4=float(np.mean(e2*e2)),
                  population_mean=float(z.mean()), population_variance=float(np.mean((z-16)**2)),
                  population_multiple=float(np.mean(z >= 2)))
    for i, axis in enumerate('xyz'):
        result['connector_mean_' + axis] = float(e[:, i].mean())
        result['connector_second_' + axis] = float(np.mean(e[:, i]**2))
        for j in range(i+1, 3):
            result['connector_cross_' + axis + 'xyz'[j]] = float(np.mean(e[:, i]*e[:, j]))
    pmf = np.bincount(z, minlength=66)/256
    for k in range(66):
        result[f'population_pmf_{k}'] = float(pmf[k])
        result[f'population_cdf_{k}'] = float(pmf[:k+1].sum())
    occupied = np.array([int(r['spring']) >= 0 for r in sites]).reshape(256, 65)
    require(np.array_equal(occupied.sum(axis=1), z), 'site/population consistency')
    for k, value in enumerate(occupied.mean(axis=0)):
        result[f'occupancy_{k}'] = float(value)
    for k in (8, 16):
        result[f'tangent{k}'] = float(np.mean([float(r[f'tangent{k}']) for r in tangents]))
    return result


def read_run(root, run):
    directory = root / 'runs' / run['id'] / 'output'
    steps = run['expected']['steps']
    with (directory / 'samples.csv').open(newline='') as stream:
        scalar_header = next(csv.reader(stream))
    require(scalar_header == 'step,time,chain,mean_r,mean_r2,re2,rg2,cm_msd,monomer_msd,min_length,tangent1,tangent2,tangent3,tangent4'.split(','), 'scalar schema')
    scalar = [(time, backbone(rows)) for time, rows in frames(directory/'samples.csv', scalar_header, 256, steps, 100000)]
    headers = {
        'tangents': 'step,time,chain,tangent8,tangent16',
        'chains': 'step,time,chain,z,ex_sum,ey_sum,ez_sum,e2_sum',
        'connectors': 'step,time,spring,chain,bead,ex,ey,ez,e2',
        'sites': 'step,time,chain,bead,spring'}
    counts = dict(tangents=256, chains=256, connectors=4096, sites=256*65)
    full = []
    if run['Z']:
        readers = [frames(directory/f'equilibrium_{key}.csv', header.split(','), counts[key], steps, 10000000)
                   for key, header in headers.items()]
        for joint in itertools.zip_longest(*readers):
            require(all(v is not None for v in joint) and len({v[0] for v in joint}) == 1, 'full grids')
            tangent, pop, con, site = [v[1] for v in joint]
            full.append((joint[0][0], context(con, pop, site, tangent)))
    else:
        full = [(time, {k: float(np.mean([float(r[k]) for r in rows])) for k in ('tangent8', 'tangent16')})
                for time, rows in frames(directory/'equilibrium_tangents.csv', headers['tangents'].split(','), 256, steps, 10000000)]
    # Histograms are accumulated over regular observations in [T/2,T], not all time.
    with (directory/'bond_statistics.csv').open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == ['chain', 'bond', 'frames', 'mean_r', 'mean_r2'] + [f'bin{k}' for k in range(33)], 'histogram schema')
        bins = np.zeros(33, dtype=np.int64)
        means = np.zeros(2)
        count = 0
        for i, row in enumerate(reader):
            require(int(row['chain']) == i//64 and int(row['bond']) == i%64 and int(row['frames']) == 501, 'histogram support')
            values = np.array([int(row[f'bin{k}']) for k in range(33)])
            require((values >= 0).all() and values.sum() == 501, 'histogram counts')
            bins += values
            means += [float(row['mean_r']), float(row['mean_r2'])]
            count += 1
        require(count == 256*64 and np.isfinite(means).all(), 'histogram bond closure')
    meta = auth.load(directory/'metadata.json')
    histogram = dict(bins=bins.tolist(), probabilities=(bins/bins.sum()).tolist(),
                     mean_r=float(means[0]/count), mean_r2=float(means[1]/count),
                     frames=501, start=5000, end=10000, histogram_max=meta['histogram_max'])
    for k in ('mean_r', 'mean_r2'):
        expected = np.mean([v[k] for time, v in scalar if time >= 5000])
        require(math.isclose(histogram[k], expected, rel_tol=2e-11, abs_tol=2e-11), 'bond/scalar reduction agreement')
    events = []
    with (directory/'equilibrium_events.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            start, end = int(row['previous_step'])*.0001, int(row['step'])*.0001
            require(float(row['interval_time']) == end-start, 'event interval duration')
            # Complete event identities and metadata totals are checked by authenticate().
            events.append(dict(start=start, end=end, counts={k: int(v) for k, v in row.items()
                          if k not in ('step', 'time', 'previous_step', 'interval_time')}))
    return dict(scalar=scalar, full=full, histogram=histogram, events=events)


def stats(values, alpha=.05, bounded=None):
    x = np.asarray(values, dtype=float)
    require(x.shape == (3,) and np.isfinite(x).all(), 'three finite independent run estimators')
    mean, se = float(x.mean()), float(x.std(ddof=1)/math.sqrt(3))
    half = float(t.ppf(1-alpha/2, 2))*se
    interval = [mean-half, mean+half] if se > 0 else None
    if bounded is not None:
        lo, hi = bounded
        require(lo < hi and ((x >= lo) & (x <= hi)).all(), 'bounded estimator outside declared range')
        radius = (hi-lo)*math.sqrt(math.log(2/alpha)/6)
        interval = [max(lo, mean-radius), min(hi, mean+radius)]
    return dict(values=x.tolist(), mean=mean, se=se, interval=interval,
                zero_dispersion=se == 0, loo=[float(np.delete(x, i).mean()) for i in range(3)])


def contrast(a, b, alpha=.05):
    """Unpaired cells; matching replica numbers do not create matched seeds."""
    aa, bb = stats(a), stats(b)
    va, vb = aa['se']**2, bb['se']**2
    se = math.sqrt(va+vb)
    df = (va+vb)**2/(va*va/2+vb*vb/2) if se > 0 else None
    delta = bb['mean']-aa['mean']
    half = float(t.ppf(1-alpha/2, df))*se if df else None
    return dict(difference=delta, se=se, df=df,
                interval=[delta-half, delta+half] if half is not None else None,
                loo=[float(np.delete(b, j).mean()-np.delete(a, i).mean()) for i in range(3) for j in range(3)])


def window(series, key, name):
    lo, hi = WINDOWS[name]
    selected = [(time, row[key]) for time, row in series if lo <= time <= hi]
    require(bool(selected), f'unsupported window: {key}, {name}')
    return float(np.mean([v for _, v in selected])), len(selected), selected[0][0], selected[-1][0]


def reference_targets(kappa, order):
    """D1.6 reference formulas evaluated for N64; no sampling or N32 MC reuse."""
    mu1, mu2 = radial_moments(1, 30, order=order)
    c = langevin(kappa)
    def size(k):
        return k*mu2+2*mu1*mu1*sum((k-s)*c**s for s in range(1, k))
    result = dict(mean_r=mu1, mean_r2=mu2, re2=size(64),
                  rg2=sum((65-k)*size(k) for k in range(1, 65))/65**2)
    result.update({f'tangent{k}': c**k for k in (1, 2, 3, 4, 8, 16)})
    result['stretch_energy'] = 15*64*(mu2-2*mu1+1)
    return {k: float(v) for k, v in result.items()}


def references():
    targets, refinement = {}, {}
    for cell in 'ABCD':
        kappa = 10 if cell in 'CD' else 0
        low, high = reference_targets(kappa, 128), reference_targets(kappa, 256)
        require(abs(low['mean_r']-high['mean_r']) < 1e-11 and
                abs(low['mean_r2']-high['mean_r2']) < 1e-11, 'accepted radial refinement gate')
        targets[cell] = high
        refinement[cell] = {k: abs(high[k]-low[k]) for k in high}
    law = canonical_population(chains=256, n=64, z=4096)
    for cell in 'BD':
        target = targets[cell]
        target.update(connector_e2=5., connector_e4=125/3, population_mean=16.,
                      population_variance=law['variance'], population_multiple=1-sum(law['pmf'][:2]))
        for axis in 'xyz':
            target['connector_mean_'+axis] = 0.
            target['connector_second_'+axis] = 5/3
        for pair in ('xy', 'xz', 'yz'):
            target['connector_cross_'+pair] = 0.
        for k in range(66):
            target[f'population_pmf_{k}'] = law['pmf'][k]
            target[f'population_cdf_{k}'] = sum(law['pmf'][:k+1])
        for k in range(65):
            target[f'occupancy_{k}'] = law['site_probability']
    return dict(targets=targets, refinement=refinement, canonical_law=law,
                qualification='Exact target laws evaluated in float64. Quadrature differences are engineering '
                'sensitivity estimates, not certified error bounds. No N64 numerical-reference ensemble '
                'authenticated; N32 D1.6 MC dimensions/variances/CDFs cannot be transferred to N64.')


def bounded(key):
    return (0., 1.) if key.startswith(('occupancy_', 'population_pmf_', 'population_cdf_')) or key == 'population_multiple' else None


def tables(out, runs, data, refs):
    traces, windows, drifts, comparisons, histograms, events = [], [], [], [], [], []
    acfs = {}
    for run in runs:
        identity, cell = run['id'], run['cell']
        record = data[identity]
        acfs[identity] = {}
        for grid in ('scalar', 'full'):
            series = record[grid]
            spacing = 10 if grid == 'scalar' else 1000
            for key in series[0][1]:
                for time, values in series:
                    traces.append(dict(run=identity, cell=cell, grid=grid, time=time, quantity=key, value=values[key]))
                for name in WINDOWS:
                    value, count, first, last = window(series, key, name)
                    windows.append(dict(run=identity, cell=cell, grid=grid, quantity=key, window=name,
                                        value=value, frames=count, first_time=first, last_time=last, duration=last-first))
                for left, right in (('initial', 'late'), ('early', 'middle'), ('middle', 'late'), ('early', 'late')):
                    drifts.append(dict(run=identity, cell=cell, grid=grid, quantity=key, contrast=f'{right}-{left}',
                                       value=window(series, key, right)[0]-window(series, key, left)[0]))
                # Retain small, meaningful temporal family; no interpolation of full-grid data.
                if key in PRIMARY or key in ('connector_e2', 'connector_e4', 'population_variance', 'tangent8', 'tangent16'):
                    acfs[identity][key] = {}
                    for segment, start in (('post_initial', spacing), ('late_half', 5000)):
                        selected = [(tm, v[key]) for tm, v in series if tm >= start]
                        result = acf_diagnostic([str(tm) for tm, _ in selected], [v for _, v in selected],
                                                str(spacing), refs['targets'][cell].get(key))
                        tau = result['tau_int']
                        # This is conditional diagnostic support, never an independent-replica count.
                        result['nominal_effective_frames'] = (min(len(selected), len(selected)*spacing/(2*tau))
                                                              if tau is not None and tau > 0 else None)
                        acfs[identity][key][segment] = result
        h = record['histogram']
        for k, probability in enumerate(h['probabilities']):
            histograms.append(dict(run=identity, cell=cell, bin=k, probability=probability, count=h['bins'][k],
                                   lower=k*h['histogram_max']/32,
                                   upper=(k+1)*h['histogram_max']/32 if k < 32 else '',
                                   start=5000, end=10000, frames=501))
        for event in record['events']:
            for key, count in event['counts'].items():
                duration = event['end']-event['start']
                events.append(dict(run=identity, cell=cell, start=event['start'], end=event['end'], quantity=key,
                                   count=count, rate=count/duration if duration else ''))
    summaries = []
    for cell in 'ABCD':
        selected_runs = [r['id'] for r in runs if r['cell'] == cell]
        prototype = [w for w in windows if w['run'] == selected_runs[0]]
        for row in prototype:
            key, grid, name = row['quantity'], row['grid'], row['window']
            values = [window(data[r][grid], key, name)[0] for r in selected_runs]
            s = stats(values, bounded=bounded(key))
            target = refs['targets'][cell].get(key)
            interval = s['interval']
            numerical = refs['refinement'][cell].get(key, 0.) if target is not None else None
            difference_interval = ([interval[0]-target-numerical, interval[1]-target+numerical]
                                   if interval is not None and target is not None else None)
            status = ('UNAVAILABLE_REFERENCE' if target is None else 'CONSERVATION_ONLY' if key == 'population_mean'
                      else 'INSUFFICIENT_PRECISION_ZERO_DISPERSION' if interval is None
                      else 'DESCRIPTIVE_DIFFERENCE' if difference_interval[0] > 0 or difference_interval[1] < 0
                      else 'COMPATIBLE_WITH_AVAILABLE_UNCERTAINTY_NOT_EQUIVALENCE')
            summaries.append(dict(cell=cell, grid=grid, quantity=key, window=name, target=target,
                                  difference_from_target=s['mean']-target if target is not None else None,
                                  numerical_refinement_sensitivity=numerical,
                                  difference_interval_engineering=difference_interval, status=status, **s))
    for a, b in (('A', 'B'), ('C', 'D')):
        left, right = [[r['id'] for r in runs if r['cell'] == c] for c in (a, b)]
        for grid in ('scalar', 'full'):
            # Only compare quantities supported in both bare and constrained records.
            common = data[left[0]][grid][0][1].keys() & data[right[0]][grid][0][1].keys()
            for key in sorted(common):
                for name in WINDOWS:
                    x, y = [[window(data[r][grid], key, name)[0] for r in group] for group in (left, right)]
                    primary = key in PRIMARY and name == 'late'
                    comparisons.append(dict(contrast=f'{b}-{a}', grid=grid, quantity=key, window=name,
                                            primary=primary, alpha=.005 if primary else .05,
                                            **contrast(x, y, .005 if primary else .05)))
    drift_summaries = []
    for cell in 'ABCD':
        ids = [r['id'] for r in runs if r['cell'] == cell]
        for row in [d for d in drifts if d['run'] == ids[0]]:
            selected = [d['value'] for d in drifts if d['cell'] == cell and d['grid'] == row['grid']
                        and d['quantity'] == row['quantity'] and d['contrast'] == row['contrast']]
            drift_summaries.append(dict(cell=cell, grid=row['grid'], quantity=row['quantity'],
                                        contrast=row['contrast'], **stats(selected)))
    histogram_summaries, histogram_contrasts, event_summaries = [], [], []
    for cell in 'ABCD':
        ids = [r['id'] for r in runs if r['cell'] == cell]
        for k in range(33):
            histogram_summaries.append(dict(cell=cell, bin=k, **stats(
                [data[r]['histogram']['probabilities'][k] for r in ids], bounded=(0., 1.))))
        for name, (lo, hi) in WINDOWS.items():
            if name == 'initial':
                continue  # Rates at t=0 are undefined, not zero.
            for key in data[ids[0]]['events'][0]['counts']:
                values = []
                for identity in ids:
                    selected = [e for e in data[identity]['events']
                                if e['start'] >= lo and e['end'] <= hi and e['end'] > e['start']]
                    if selected:
                        values.append(sum(e['counts'][key] for e in selected)/
                                      sum(e['end']-e['start'] for e in selected))
                if values:
                    require(len(values) == 3, 'event window replica support')
                    event_summaries.append(dict(cell=cell, window=name, quantity=key,
                        intervals_per_run=len(selected), first_time=selected[0]['start'],
                        last_time=selected[-1]['end'], **stats(values)))
    for a, b in (('A', 'B'), ('C', 'D')):
        ids_a, ids_b = [[r['id'] for r in runs if r['cell'] == c] for c in (a, b)]
        limits = [data[r]['histogram']['histogram_max'] for r in ids_a+ids_b]
        require(len(set(limits)) == 1, 'histogram edges differ between runs')
        for k in range(33):
            x, y = [[data[r]['histogram']['probabilities'][k] for r in ids] for ids in (ids_a, ids_b)]
            # Hoeffding union bound for two independent three-run bounded means.
            radius = 2*math.sqrt(math.log(4/.05)/6)
            difference = float(np.mean(y)-np.mean(x))
            histogram_contrasts.append(dict(contrast=f'{b}-{a}', bin=k,
                bounded_interval=[max(-1., difference-radius), min(1., difference+radius)],
                **contrast(x, y)))
    for filename, rows in (('traces', traces), ('replica_windows', windows), ('replica_drifts', drifts),
                           ('backbone_comparisons', comparisons), ('equilibrium_summaries', summaries),
                           ('drift_summaries', drift_summaries), ('bond_histograms', histograms),
                           ('bond_histogram_summaries', histogram_summaries),
                           ('bond_histogram_contrasts', histogram_contrasts),
                           ('event_intervals', events), ('event_summaries', event_summaries)):
        auth.write_csv(out/f'{filename}.csv', rows)
    auth.write_json(out/'autocorrelation.json', acfs)
    return comparisons


def plots(out, data, refs):
    os.environ['MPLCONFIGDIR'] = str(out/'matplotlib-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for number, quantities, grid in ((1, PRIMARY, 'scalar'),
                                     (2, ('connector_e2', 'connector_e4', 'population_variance', 'tangent16'), 'full')):
        fig, axes = plt.subplots(len(quantities), 2, figsize=(11, 2.6*len(quantities)), squeeze=False)
        for column, cells in enumerate(('AB', 'CD')):
            for row, key in enumerate(quantities):
                ax = axes[row, column]
                for identity, record in data.items():
                    series = record[grid]
                    cell = identity.split('-')[1]
                    if cell not in cells or key not in series[0][1]:
                        continue
                    ax.plot([tm for tm, _ in series], [v[key] for _, v in series], color=auth.COLORS[cell],
                            alpha=.65, linewidth=.8, label=identity)
                target = refs['targets'][cells[-1]].get(key)
                if target is not None:
                    ax.axhline(target, color='black', linestyle=':', linewidth=.8, label='target')
                ax.set(xlabel='time', ylabel=key, title=f'kappa={0 if column == 0 else 10}')
            axes[0, column].legend(fontsize=6, ncol=2)
        fig.tight_layout()
        for ext in ('png', 'pdf'):
            fig.savefig(out/f'figure_{number}.{ext}', dpi=200)
        plt.close(fig)
    return matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-reviewed-analysis', action='store_true', required=True)
    args = parser.parse_args()
    require(args.run_reviewed_analysis, 'explicit reviewed execution flag')
    require(os.getpriority(os.PRIO_PROCESS, 0) == 19, 'launch with nice -n 19 ionice -c 3')
    out = output_path(BASE/'analysis')
    out.mkdir(parents=True, exist_ok=False)
    try:
        # Capture every local Python module before any reductions, plus review documents/tests.
        source_paths = sorted(auth.PROJECT.glob('*.py')) + [auth.PROJECT/'tests/d2a5_n64_statics_regression.py']
        source_paths += [auth.PROJECT/name for name in ('E1_STAGE_D2A5_N64_STATICS_PREPARATION.md',
                         'EQUILIBRIUM_MODEL_E1.md', 'E1_STAGE_D16_REFERENCE_MOMENTS_V1.md',
                         'E1_STAGE_D16_SCIENTIFIC_CLOSURE.md', 'E1_STAGE_D16B_PROTOCOL_V1.md')]
        source_paths = sorted(set(source_paths) | set(auth.PROJECT.glob('E1_STAGE_D16[BCDEF]*.md')))
        sources = {str(p.relative_to(auth.PROJECT)): auth.file_record(p) for p in source_paths}
        manifest, runs, immutable, before, authentication = auth.authenticate(auth.EVIDENCE)
        auth.write_json(out/'authentication.json', authentication)
        refs = references()
        auth.write_json(out/'references.json', refs)
        data = {run['id']: read_run(auth.EVIDENCE, run) for run in runs}
        comparisons = tables(out, runs, data, refs)
        plot_version = plots(out, data, refs)
        report = (auth.PROJECT/'E1_STAGE_D2A5_N64_STATICS_PREPARATION.md').read_text()
        (out/'OUTPUT_AVAILABILITY.md').write_text(report)
        lines = ['# N64 static equilibrium review — descriptive, no acceptance', '',
                 'EQUILIBRIUM PRESERVATION NOT CONFIRMED. Inspect replica tables, traces and unresolved ACF tails.',
                 'Exact E1 target theory differs from numerical preservation at finite dt.', '',
                 '| contrast | late primary | difference | nominal 99.5% Welch interval | assessment |',
                 '|---|---|---|---|---|']
        for row in comparisons:
            if row['primary']:
                interval = row['interval']
                assessment = ('Insufficient precision: zero observed dispersion' if interval is None else
                              'Descriptive statistical difference; no equivalence or stationary-bias claim'
                              if interval[0] > 0 or interval[1] < 0 else
                              'Compatible within available uncertainty; practical equivalence unavailable')
                lines.append(f"| {row['contrast']} | {row['quantity']} | {row['difference']} | {interval} | {assessment} |")
        lines += ['', '## Connector drift on the sparse full grid', '',
                  '| cell | late minus early e2, each run | R3 mean | nominal 95% t2 interval |',
                  '|---|---|---|---|']
        for cell in 'BD':
            values = [window(data[r['id']]['full'], 'connector_e2', 'late')[0]-
                      window(data[r['id']]['full'], 'connector_e2', 'early')[0]
                      for r in runs if r['cell'] == cell]
            result = stats(values)
            lines.append(f"| {cell} | {values} | {result['mean']} | {result['interval']} |")
        lines += ['', 'These ten prespecified comparisons use Bonferroni nominal 95% family sensitivity.',
                  'R=3 and replica-normal/CLT assumptions limit coverage. No practical equivalence margin is assigned.',
                  'Initial, early, middle and late records and paired within-run drift contrasts are separate.',
                  'All other comparisons are exploratory; related moments are not independent confirmations.',
                  'No stationary bias, timestep convergence, canonical mixing or ergodicity follows from these tables.',
                  'The D1.6 stiff/coarse connector change (-0.04462, dt=.00025, N32, T100) was post-selected.',
                  'N64 uses dt=.0001, T10000: neither reproduces that controlled experiment nor resolves timestep error.',
                  'Connector late-minus-early signs and intervals in drift_summaries.csv can strengthen or weaken',
                  'a descriptive drift concern, but cannot identify its mechanism or a stationary shift.',
                  'Temporal effective counts are conditional diagnostics; unresolved tails remain null.',
                  'D1.6 N32 Monte Carlo reference variances/CDFs are unavailable for N64. No new draws made.', '']
        (out/'SCIENTIFIC_REVIEW.md').write_text('\n'.join(lines))
        require(auth.selected_inventory(auth.EVIDENCE, immutable) == before, 'N64 inputs changed during reduction')
        require({str(p.relative_to(auth.PROJECT)): auth.file_record(p) for p in source_paths} == sources, 'source changed during analysis')
        auth.write_json(out/'provenance.json', dict(sources=sources, python=sys.version, numpy=np.__version__,
                        scipy=__import__('scipy').__version__, matplotlib=plot_version, utc=auth.utc(),
                        threads={p: os.environ[p] for p in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')},
                        status='COMPLETE_DESCRIPTIVE_AUDIT_NOT_ACCEPTANCE', manifest_sha256=auth.MANIFEST_SHA))
        auth.write_json(out/'result_inventory.json', auth.snapshot(out))
    except Exception as error:
        auth.write_json(out/'FAILED.json', dict(error=str(error), status='INCOMPLETE_DO_NOT_INTERPRET'))
        raise


if __name__ == '__main__':
    main()
