#!/usr/bin/env python3
"""Prepared CPU-only D2A.5 audit. No tests or reduction run on import."""
import os
for _pool in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS'):
    os.environ[_pool] = '2'
os.environ['OMP_THREAD_LIMIT'] = '2'

import argparse
import csv
from pathlib import Path
import subprocess
import sys

import numpy as np
import e1_d2a5_n64_analyze as d
import e1_d2a5_n64_statics as s
from e1_d2a5_validate import validate_output

BASE = Path('/home/jramirez/UAMMD_KG-evidence/d2a5-analysis/n128-v1')
IDS = [f'n{n}-{c}-r{r}' for n in (64, 128) for c in 'ABCD' for r in (1, 2, 3)]
require = d.require


def output_path(path):
    path = d.regular_path(Path(path).absolute())
    base = d.regular_path(BASE).resolve()
    resolved = path.resolve()
    require(resolved != base and resolved.is_relative_to(base), 'output must be beneath n128-v1')
    return resolved


def windows_for(run):
    e = run['expected']
    total, stride = e['T'], e['scalar_stride']*e['dt']
    return {'initial': (0, 0), 'post_initial': (stride, total),
            'early': (stride, total/5), 'middle': (2*total/5, 3*total/5),
            'late': (4*total/5, total)}


def completed_records(summary):
    require(summary['manifest_sha256'] == d.MANIFEST_SHA, 'summary manifest identity')
    require(summary['status'] == 'completed_24_runs_not_scientific_acceptance' and
            summary['phase'] == 'finished' and summary['active_run'] is None and
            summary.get('error') is None and not summary['resource_limit_violations'],
            'campaign must be completed without errors or resource violations')
    require(summary['completed_runs'] == IDS and [r['id'] for r in summary['run_records']] == IDS,
            'exactly 24 ordered completed independent runs required')
    return {r['id']: r for r in summary['run_records']}


def input_stamps(root):
    d.regular_path(root)
    return {str(p.relative_to(root)): d.stamp(d.regular_path(p))
            for p in sorted(root.rglob('*')) if p.is_file()}


def authenticate(root):
    """Two hash passes overall; never read a live binary or execute archived code."""
    d.regular_path(root)
    stamps = input_stamps(root)
    before = d.snapshot(root)
    require(input_stamps(root) == stamps, 'inputs changed during initial hashing')
    manifest = d.load(d.CONFIG/'manifest.json')
    require(d.file_record(d.CONFIG/'manifest.json')['sha256'] == d.MANIFEST_SHA ==
            '297ad861edb98232ca91c9fbd11b7eef2443bc685d7c89ec592a7ab86777c365', 'pinned manifest')
    require(before['config/manifest.json']['sha256'] == d.MANIFEST_SHA and
            (root/'config/manifest.json').read_bytes() == (d.CONFIG/'manifest.json').read_bytes(),
            'archived manifest identity')
    require((root/'config/manifest.sha256').read_bytes() == (d.CONFIG/'manifest.sha256').read_bytes(),
            'manifest checksum record')
    records = completed_records(d.load(root/'summary.json'))
    require([r['id'] for r in manifest['runs']] == IDS and
            len({r['seed'] for r in manifest['runs']}) ==
            len({r['replica_id'] for r in manifest['runs']}) == 24, 'independent manifest cohort')
    require({p.name for p in (root/'runs').iterdir()} == set(IDS), 'run directory closure')
    for name, record in manifest['schedules'].items():
        require(before['config/'+name] == d.file_record(d.CONFIG/name) == record, 'frozen schedule identity')
    for name, record in manifest['tools'].items():
        require(before['provenance/'+name] == d.file_record(d.PROJECT/name) == record,
                'archived/local validator identity')
    launch = d.load(root/'provenance/launch.json')
    require(launch['manifest_sha256'] == d.MANIFEST_SHA and
            launch['implementation_sha'] == manifest['implementation_sha'] and
            launch['executable'] == manifest['executable'] and
            launch['compiler_provenance'] == manifest['compiler_provenance'], 'launch provenance')
    tree = subprocess.run(['git', '-C', str(d.PROJECT), 'ls-tree', '-r', manifest['implementation_sha']],
                          check=True, capture_output=True, text=True).stdout.strip()
    require(tree == launch['source_tree'].strip(), 'recorded source tree identity')
    archived = {k.removeprefix('provenance/'): v for k, v in before.items()
                if k.startswith('provenance/') and k != 'provenance/launch.json'}
    require(archived == launch['preserved_files'], 'preserved provenance closure')
    for label, proof in manifest['prerequisites'].items():
        require(archived[label+'-'+Path(proof['path']).name] == proof['file'], 'prerequisite identity')
    for run in manifest['runs']:
        n, e = run['N'], run['expected']
        require(n in (64, 128) and run['M'] == 256 and
                run['Z'] == (64*n if run['cell'] in 'BD' else 0) and
                run['kappa'] == (10 if run['cell'] in 'CD' else 0), 'physical matrix')
        require((e['N'], e['T'], e['steps'], e['dt'], e['stride'], e['slots'], e['m'], e['levels']) ==
                (n, 10000 if n == 64 else 40000, 100000000 if n == 64 else 400000000,
                 .0001, 100, 16, 2, 19 if n == 64 else 21), 'acquisition matrix')
        prefix = 'runs/'+run['id']+'/'
        directory = root/'runs'/run['id']
        record = records[run['id']]
        require(before[prefix+'receipt.json'] == record['receipt'], 'receipt summary anchor')
        receipt = d.load(directory/'receipt.json')
        require(receipt['id'] == run['id'] and receipt['manifest_sha256'] == d.MANIFEST_SHA,
                'receipt identity')
        files = {k[len(prefix):]: v for k, v in before.items()
                 if k.startswith(prefix) and k != prefix+'receipt.json'}
        require(files == receipt['files'] and
                sum(v['bytes'] for k, v in before.items() if k.startswith(prefix)) == record['output_bytes'],
                'complete output size/SHA256 closure')
        process = d.load(directory/'process.json')
        require(process == receipt['process'] == record['process'] and
                process['status'] == 'exited' and process['exit_code'] == 0, 'process completion')
        run_launch = d.load(directory/'launch.json')
        require(run_launch['argv'] == run['argv'] and run_launch['seed'] == run['seed'] and
                run_launch['replica_id'] == run['replica_id'] and
                run_launch['gpu']['uuid'] == manifest['gpu_uuid'] and
                d.load(directory/'output/metadata.json')['gpu'] == run_launch['gpu']['name'],
                'run identity and recorded device provenance')
        require(validate_output(directory/'output', run) == receipt['validation'], 'completion revalidation')
        grid = manifest['supports'][str(n)]['grid']
        require(len(grid) == e['exported_bins_per_chain'] and grid[-1] == e['last_exported'] and
                [p for p in grid if p['primary']][-1] == e['primary_last'], 'manifest support closure')
        require(all(p['primary'] == (5*p['lag_steps'] <= e['steps'] and p['origins_per_chain'] >= 32)
                    for p in grid), 'integer primary support rule')
    require(input_stamps(root) == stamps, 'inputs changed during completion authentication')
    return manifest, before, dict(status='AUTHENTICATED_BEFORE_REDUCTION_NOT_ACCEPTANCE',
        manifest_sha256=d.MANIFEST_SHA, input_inventory=before, input_stamps=stamps, completed_runs=IDS,
        compiler_provenance=manifest['compiler_provenance'],
        scope='Recorded receipts, source tree, executable identity and output bytes; no independent physical execution attestation.')


def secondary_tables(out, root, manifest):
    rows = []
    grid = manifest['supports']['128']['grid']
    for run in (r for r in manifest['runs'] if r['N'] == 128):
        path = root/'runs'/run['id']/'output/dynamics/replica_correlations.csv'
        with path.open(newline='') as stream:
            for row, p in zip(csv.DictReader(stream), grid):
                for bead in (0, 32, 96, 128):
                    require(float(row[f'bead{bead}_msd']) >= 0, 'nonnegative secondary MSD')
                    rows.append(dict(run=run['id'], cell=run['cell'], bead=bead,
                        **{k: row[k] for k in d.SUPPORT}, primary=p['primary'], msd=float(row[f'bead{bead}_msd'])))
    d.write_csv(out/'secondary_monomers.csv', rows)
    summaries = []
    for cell in 'ABCD':
        for p in grid:
            for bead in (0, 32, 96, 128):
                selected = [r for r in rows if r['cell'] == cell and r['bead'] == bead and
                            int(r['lag_steps']) == p['lag_steps']]
                require(len(selected) == 3, 'three secondary replicas')
                mean, se = d.mean_se(np.array([r['msd'] for r in selected]))
                summaries.append(dict(cell=cell, bead=bead, lag_steps=p['lag_steps'],
                    lag_time=selected[0]['lag_time'], primary=p['primary'], mean=mean, se_R3=se))
    d.write_csv(out/'secondary_monomer_means.csv', summaries)


def comparison_tables(out, cohorts):
    """Unpaired run means; never pair runs by replica number or interpolate filters."""
    rows, ratios = [], []
    for n, cells in cohorts.items():
        for cell, data in cells.items():
            mean, se = d.mean_se(data['values'])
            for i, support in enumerate(data['rows']):
                for j, quantity in enumerate(('cm_msd', 'central_msd', 'c1', 'c2')):
                    rows.append(dict(N=n, beads=n+1, cell=cell, quantity=quantity,
                        **{k: support[k] for k in d.SUPPORT}, region=data['regions'][i],
                        T=data['runs'][0]['expected']['T'], mean=mean[i, j], se_R3=se[i, j],
                        **{f'r{r+1}': data['values'][r, i, j] for r in range(3)}))
        for bare, constrained in (('A', 'B'), ('C', 'D')):
            left, right = cells[bare], cells[constrained]
            for i, support in enumerate(left['rows']):
                require(d.alignment_key(dict(cell=bare, **support)) ==
                        d.alignment_key(dict(cell=bare, **right['rows'][i])), 'ratio support mismatch')
                if float(support['lag_time']) <= 0:
                    continue
                for j, q in enumerate(('cm_msd', 'central_msd')):
                    a, b = left['values'][:, i, j], right['values'][:, i, j]
                    am, bm = a.mean(), b.mean()
                    require(am > 0, 'positive bare ratio denominator')
                    # Delta-method descriptive uncertainty, independent cells, R=3 each.
                    error = np.sqrt(b.var(ddof=1)/3/am**2 + bm**2*a.var(ddof=1)/3/am**4)
                    ratios.append(dict(N=n, contrast=f'{constrained}/{bare}', quantity=q,
                        **{k: support[k] for k in d.SUPPORT}, region=left['regions'][i],
                        ratio_of_means=bm/am, descriptive_delta_se=error,
                        bare_runs=a.tolist(), constrained_runs=b.tolist()))
    d.write_csv(out/'all_lengths_curves.csv', rows)
    d.write_csv(out/'constrained_bare_ratios.csv', ratios)
    common = []
    indexed = {n: {(r['cell'], r['quantity'], d.alignment_key(r)): r for r in rows if r['N'] == n}
               for n in cohorts}
    for key in sorted(set.intersection(*(set(v) for v in indexed.values()))):
        selected = [indexed[n][key] for n in sorted(cohorts)]
        require(len({r['lag_time'] for r in selected}) == 1 and
                len({r['orientation_block_duration'] for r in selected}) == 1, 'physical/filter alignment')
        for row in selected:
            common.append(dict(primary_in_all=all(r['region'] != 'weak_tail' for r in selected), **row))
    d.write_csv(out/'common_supported_lags.csv', common)
    return rows, ratios, common


def comparison_context(manifest, old_manifest):
    """Authenticate comparability rather than assuming different binaries imply it."""
    runs = manifest['runs'] + old_manifest['runs']
    require(len({r['seed'] for r in runs}) == len(runs), 'cross-campaign seeds must be distinct')
    excluded = {'--springs', '--slip-count', '--steps', '--seed', '--dynamics-replica', '--output',
                '--sample', '--equilibrium-steps', '--equilibrium-snapshots', '--dynamics-levels',
                '--dynamics-mib'}
    for cell in 'ABCD':
        options = []
        for n in (32, 64, 128):
            r = next(r for r in runs if r['cell'] == cell and
                     (r.get('N', 32) == n))
            require(r['Z'] == (64*n if cell in 'BD' else 0), 'fixed contour constraint density')
            options.append({k: v for k, v in zip(r['argv'][1::2], r['argv'][2::2]) if k not in excluded})
        require(options[0] == options[1] == options[2], 'model/acquisition compatibility across lengths')
    return dict(N32=old_manifest['expected'], N64=manifest['runs'][0]['expected'],
        N128=next(r['expected'] for r in manifest['runs'] if r['N'] == 128),
        executable_n32=old_manifest['executable'], executable_n64_n128=manifest['executable'],
        qualification='Different recorded binaries; validated common model/export semantics, not bitwise equivalence.')


def compare_figures(out, rows, ratios, common):
    import matplotlib.pyplot as plt
    for quantity in ('cm_msd', 'central_msd', 'c1', 'c2'):
        fig, axes = plt.subplots(2, 2, figsize=(10, 7))
        for cell, ax in zip('ABCD', axes.flat):
            for n, style in ((32, '-'), (64, '--'), (128, '-.')):
                selected = [r for r in common if r['N'] == n and r['cell'] == cell and
                            r['quantity'] == quantity and r['primary_in_all'] and float(r['lag_time']) > 0]
                for block in sorted({r['decimation_samples'] for r in selected}, key=int):
                    group = [r for r in selected if r['decimation_samples'] == block]
                    ax.errorbar([float(r['lag_time']) for r in group], [r['mean'] for r in group],
                                yerr=[r['se_R3'] for r in group], color={32:'C0',64:'C1',128:'C2'}[n],
                                ls=style, lw=.8, label=f'N{n}' if block == '1' else None)
            ax.set(xscale='log', title=cell, xlabel='common supported lag', ylabel=quantity)
            if quantity.endswith('msd'):
                ax.set_yscale('log')
            ax.legend()
        fig.tight_layout()
        fig.savefig(out/f'comparison_{quantity}.png', dpi=200)
        plt.close(fig)

    for quantity in ('cm_msd', 'central_msd'):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        for contrast, ax in zip(('B/A', 'D/C'), axes):
            for n in (32, 64, 128):
                selected = [r for r in ratios if r['N'] == n and r['contrast'] == contrast and
                            r['quantity'] == quantity and r['region'] != 'weak_tail']
                for block in sorted({r['decimation_samples'] for r in selected}, key=int):
                    group = [r for r in selected if r['decimation_samples'] == block]
                    ax.errorbar([float(r['lag_time']) for r in group], [r['ratio_of_means'] for r in group],
                                yerr=[r['descriptive_delta_se'] for r in group], color={32:'C0',64:'C1',128:'C2'}[n],
                                lw=.8, label=f'N{n}' if block == '1' else None)
            ax.set(xscale='log', title=contrast, xlabel='supported lag (support differs by N)', ylabel='ratio of means')
            ax.legend()
        fig.tight_layout()
        fig.savefig(out/f'comparison_ratios_{quantity}.png', dpi=200)
        plt.close(fig)


def slope_diffusion_figures(out, cohorts):
    import matplotlib.pyplot as plt
    rows = []
    for cell in 'ABCD':
        for j, quantity in enumerate(('cm_msd', 'central_msd')):
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            for n, cells in cohorts.items():
                data = cells[cell]
                alpha, reasons = d.local_slopes(data['time'], data['values'][:, :, j], data['blocks'], data['regions'])
                for block in np.unique(data['blocks']):
                    ii = [i for i in range(len(data['time'])) if data['blocks'][i] == block and
                          all(r == 'available_same_level_stencil' for r in reasons[i])]
                    if not ii:
                        continue
                    mean, se = d.mean_se(alpha[:, ii])
                    effective = data['values'][:, ii, j]/(6*data['time'][ii])
                    dm, ds = d.mean_se(effective)
                    color = {32:'C0',64:'C1',128:'C2'}[n]
                    for ax, y, error in ((axes[0], mean, se), (axes[1], dm, ds)):
                        ax.errorbar(data['time'][ii], y, yerr=error, color=color, lw=.8,
                                    label=f'N{n}' if block == 1 else None)
                    for k, i in enumerate(ii):
                        rows.append(dict(N=n, cell=cell, quantity=quantity, **{key: data['rows'][i][key] for key in d.SUPPORT},
                            alpha_mean=mean[k], alpha_se_R3=se[k], effective_D_mean=dm[k], effective_D_se_R3=ds[k]))
            axes[0].axhline(1, color='.5', lw=.6)
            for ax, label in zip(axes, ('local logarithmic slope', 'g/(6t), diagnostic')):
                ax.set(xscale='log', xlabel='supported lag', ylabel=label, title=f'{cell}: {quantity}')
                ax.legend()
            fig.tight_layout()
            fig.savefig(out/f'diagnostics_{cell}_{quantity}.png', dpi=200)
            plt.close(fig)
    d.write_csv(out/'supported_slopes_diffusion.csv', rows)


def static_length_comparison(out, datasets):
    rows = []
    for n, (runs, data) in datasets.items():
        w = windows_for(runs[0])
        for a, b in (('A', 'B'), ('C', 'D')):
            for q in s.PRIMARY:
                x, y = [[s.window(data[r['id']]['scalar'], q, 'late', w)[0]
                         for r in runs if r['cell'] == cell] for cell in (a, b)]
                rows.append(dict(N=n, beads=n+1, T=runs[0]['expected']['T'], contrast=f'{b}-{a}',
                    quantity=q, window_start=w['late'][0], window_end=w['late'][1],
                    bare_runs=x, constrained_runs=y, alpha=.005, **s.contrast(x, y, .005)))
    d.write_csv(out/'static_length_comparison.csv', rows)
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(s.PRIMARY), 2, figsize=(10, 12))
    for i, q in enumerate(s.PRIMARY):
        for j, contrast in enumerate(('B-A', 'D-C')):
            ax = axes[i, j]
            for row in rows:
                if row['quantity'] == q and row['contrast'] == contrast:
                    interval = row['interval']
                    ax.errorbar(row['N'], row['difference'], yerr=None if interval is None else
                        [[row['difference']-interval[0]], [interval[1]-row['difference']]], fmt='o', color='C0')
            ax.axhline(0, color='.5', lw=.6)
            ax.set(xlabel='N bonds', ylabel=q+' difference', title=contrast)
    fig.tight_layout()
    fig.savefig(out/'static_length_comparison.png', dpi=200)
    plt.close(fig)


def population_figures(out, runs, data, refs):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    w = windows_for(runs[0])
    for column, cell in enumerate('BD'):
        selected = [r for r in runs if r['cell'] == cell]
        for row, (prefix, count) in enumerate((('population_pmf_', 130), ('occupancy_', 129))):
            keys = [prefix+str(k) for k in range(count)]
            values = np.array([[s.window(data[r['id']]['full'], key, 'late', w)[0] for key in keys]
                               for r in selected])
            mean, se = d.mean_se(values)
            ax = axes[row, column]
            for replica in values:
                ax.plot(range(count), replica, color='C0', alpha=.3, lw=.5)
            ax.errorbar(range(count), mean, yerr=se, color='C0', lw=.8, label='R3 mean, descriptive SE')
            ax.plot(range(count), [refs['targets'][cell][key] for key in keys], color='black',
                    ls=':', lw=1, label='finite-population E1 target')
            ax.set(title=cell, xlabel='population k' if row == 0 else 'contour site',
                   ylabel='late-window probability')
            ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out/'population_occupancy.png', dpi=200)
    plt.close(fig)


def review(out):
    lines = ['# D2A.5 N128 scientific review — independent assessment required', '',
        'Numerical completion, authenticated file closure, and scientific acceptance are separate.',
        'Successful execution produces descriptive diagnostics; scientific acceptance remains false.', '',
        '## 1. Dynamical characterization', '',
        'Inspect dynamics/n128/{terminal_windows,slopes,bare_com,orientation,curves}.csv and replica figures.',
        'Terminal COM diffusion and central-bead recovery require sustained supported windows, slopes near one,',
        'stable g/(6t), consistency across three replicas, and orientation-tail inspection. No automatic exponent',
        'or terminal time is assigned. The primary endpoint is t=7864.32 (49 origins/chain); the t=36700.16',
        'tail has one origin and cannot alone establish either result. C1/C2 half crossings are sampled diagnostics,',
        'not fitted relaxation times. MSD decimates last positions; orientation averages fine rank-one/rank-two',
        'features before correlation without renormalization. Slopes never cross multi-tau level boundaries.', '',
        '## 2. Static conformational preservation', '',
        'EQUILIBRIUM PRESERVATION NOT CONFIRMED. Inspect statics/n128/backbone_comparisons.csv,',
        'equilibrium_summaries.csv, drift_summaries.csv, autocorrelation.json and replica traces.',
        'The five late-window B−A and D−C primary contrasts use nominal 99.5% Welch intervals',
        '(Bonferroni sensitivity for ten comparisons). R=3 independent whole runs; normal/CLT coverage is',
        'qualified, especially with unresolved temporal tails. Zero observed dispersion does not imply certainty.',
        'All other comparisons are exploratory. Nonsignificance is not equality; no equivalence margin is assigned.',
        'Connector targets are E²=5 and E⁴=125/3. Population/occupancy targets use the exact finite-M',
        'hypergeometric law for 8192 occupied sites among 256×129 sites. Mean population 32 is conservation,',
        'not a mixing test. Bounded PMF/CDF/occupancy intervals are conservative Hoeffding diagnostics.',
        'The N128 nonlinear reference is evaluated analytically by radial quadrature and Langevin tangent',
        'correlations. Quadrature refinement is a sensitivity estimate; no N32/N64 sampled reference errors transfer.', '',
        '## 3. Finite-timestep limitations', '',
        'One timestep, dt=0.0001, does not establish timestep convergence, stationary bias or ensemble ergodicity.',
        'Sparse full E1 records (11 frames, spacing 4000) do not resolve long connector/population correlation times.',
        'Autocorrelation tails may remain unresolved; conditional effective-frame counts never increase R.', '',
        '## 4. Chain-length dependence', '',
        'comparison/common_supported_lags.csv matches integer lag, decimation phase and orientation filter width',
        'across authenticated N32/N64/N128 records. Use primary_in_all; durations are 1000/10000/40000.',
        'Local slopes and sampled crossings for all lengths are in dynamics/n{32,64,128}; compare supported',
        'ranges first. Ratios use unpaired cell means and descriptive delta-method SE, never paired replica labels.',
        'Static comparisons use each campaign’s late 20% and include unpaired uncertainty; these are different',
        'physical windows and unresolved mixing may affect them. Three lengths do not establish asymptotic',
        'scaling. Slowing alone proves neither reptation nor physical topological entanglements.', '',
        '## 5. Remaining scientific questions', '',
        'Independent review must assess sustained diffusion, monomer recovery, orientation residuals,',
        'stiffness-dependent crossovers, static differences, drift, and compatibility of E1 diagnostics.',
        'No stress/rheology, full coordinate history, independent entanglement measure, controlled timestep series,',
        'or authenticated N128 sampled numerical-reference uncertainty is available.', '']
    lines += ['', '## Numerical evidence for review', '',
              '| cell | quantity | replica | latest supported alpha range | D_eff range |',
              '|---|---|---|---|---|']
    with (out/'dynamics/n128/terminal_windows.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    for cell in 'ABCD':
        for quantity in ('cm_msd', 'bead64_msd'):
            selected = [r for r in rows if r['cell'] == cell and r['quantity'] == quantity]
            latest = max(int(r['end_lag_steps']) for r in selected)
            for r in selected:
                if int(r['end_lag_steps']) == latest:
                    lines.append(f"| {cell} | {quantity} | {r['run']} | {float(r['slope_min']):.4g}–{float(r['slope_max']):.4g} | "
                                 f"{float(r['effective_D_min']):.4g}–{float(r['effective_D_max']):.4g} |")
    lines += ['', '| contrast | late primary | difference | nominal 99.5% Welch interval |',
              '|---|---|---|---|']
    with (out/'statics/n128/backbone_comparisons.csv').open(newline='') as stream:
        for r in csv.DictReader(stream):
            if r['primary'] == 'True':
                lines.append(f"| {r['contrast']} | {r['quantity']} | {float(r['difference']):.5g} | {r['interval']} |")
    (out/'SCIENTIFIC_REVIEW.md').write_text('\n'.join(lines)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-reviewed-analysis', action='store_true', required=True)
    args = parser.parse_args()
    require(args.run_reviewed_analysis and os.getpriority(os.PRIO_PROCESS, 0) == 19,
            'explicit review flag and nice -n 19 required')
    # Linux IOPRIO_CLASS_IDLE, checked without changing system or device settings.
    import ctypes
    import platform
    number = {'x86_64': 252, 'aarch64': 31}.get(platform.machine())
    require(number is not None, 'review ioprio_get syscall for this architecture')
    priority = ctypes.CDLL(None, use_errno=True).syscall(number, 1, 0)
    require(priority >= 0 and priority >> 13 == 3, 'launch with ionice -c 3')
    out = output_path(BASE/'analysis')
    out.mkdir(parents=True, exist_ok=False)
    os.environ['MPLCONFIGDIR'] = str(out/'matplotlib-cache')
    try:
        paths = sorted(d.PROJECT.glob('*.py')) + sorted(d.PROJECT.glob('tests/d2a5*regression.py'))
        paths += sorted(d.PROJECT.glob('E1_STAGE_D*.md')) + [d.PROJECT/'EQUILIBRIUM_MODEL_E1.md']
        sources = {str(p.relative_to(d.PROJECT)): d.file_record(p) for p in paths}
        manifest, before, authentication = authenticate(d.EVIDENCE)
        old_root = d.regular_path(Path(d.N32_PROFILE['evidence']))
        old_manifest, _, old_before = d.authenticate_n32(old_root, d.N32_PROFILE)
        d.write_json(out/'comparison_context.json', comparison_context(manifest, old_manifest))
        d.write_json(out/'authentication.json', authentication)
        d.write_json(out/'n32_authentication.json', dict(root=str(old_root), input_inventory=old_before,
            manifest_sha256=d.N32_PROFILE['manifest_sha']))
        d.write_json(out/'input_inventory.json', dict(production_root=str(d.EVIDENCE), production=before,
                                                    n32_root=str(old_root), n32=old_before))
        (out/'AUTHENTICATION_REPORT.md').write_text(
            '# Recorded evidence authentication\n\n24/24 D2A.5 completion receipts and the pinned D2A.4 N32 campaign '
            'passed the prepared validators before reduction. See authentication.json, n32_authentication.json '
            'and input_inventory.json for exact identities and scope. Recorded source/executable provenance '
            'does not independently attest physical execution; historical compiler invocation remains unproved. '
            'Final unchanged-input closure is required in provenance.json; FAILED.json invalidates all products.\n')
        (out/'REPRODUCIBILITY.md').write_text((d.PROJECT/'E1_STAGE_D2A5_N128_PREPARATION.md').read_text())
        (out/'OUTPUT_AVAILABILITY.md').write_text(
            '# Observable availability\n\nCOM, bead64 and secondary bead0/32/96/128 absolute MSD, C1, C2; '
            'scalar backbone properties and tangent1–4; sparse tangent8/16, connector vectors/moments, '
            'populations, site occupancy and hopping/renewal events; late-half bond histograms. '
            'Initial/final snapshots only. No stress/rheology, full trajectories, timestep series, physical '
            'entanglement estimator or authenticated N128 sampled numerical-reference error ensemble. '
            'See REPRODUCIBILITY.md for exact schedules and statistical limitations.\n')
        cohorts = {32: d.read_replicas(old_root, old_manifest, d.N32_PROFILE)}
        cohorts.update({n: d.read_cells(d.EVIDENCE, manifest,
            [r for r in manifest['runs'] if r['N'] == n], n) for n in (64, 128)})
        # Give the legacy N32 run records the same explicit schedule interface.
        old_expected = dict(old_manifest['expected'], full_steps=[int(v) for v in
            (old_root/'config/equilibrium.steps').read_text().splitlines()])
        old_runs = [dict(r, N=32, expected=old_expected) for r in old_manifest['runs']]
        from e1_d2a3_run import QUANTITIES as old_quantities
        for cell, data in cohorts[32].items():
            data['runs'] = [r for r in old_runs if r['cell'] == cell]
            data['values'] = data['values'][:, :, [old_quantities.index(q)
                              for q in ('cm_msd', 'bead16_msd', 'c1', 'c2')]]
        for n, cells in cohorts.items():
            target = out/f'dynamics/n{n}'
            target.mkdir(parents=True)
            d.numerical_tables(target, cells, n)
            d.figures(target, cells, n)
        secondary_tables(out/'dynamics/n128', d.EVIDENCE, manifest)
        datasets = {}
        for n in (32, 64, 128):
            runs = old_runs if n == 32 else [r for r in manifest['runs'] if r['N'] == n]
            root = old_root if n == 32 else d.EVIDENCE
            data = {r['id']: s.read_run(root, r) for r in runs}
            datasets[n] = (runs, data)
            if n == 128:
                target = out/'statics/n128'
                target.mkdir(parents=True)
                refs = s.references(n)
                d.write_json(target/'references.json', refs)
                s.tables(target, runs, data, refs, windows_for(runs[0]))
                s.plots(target, data, refs)
                population_figures(target, runs, data, refs)
        target = out/'comparison'
        target.mkdir()
        rows, ratios, common = comparison_tables(target, cohorts)
        compare_figures(target, rows, ratios, common)
        slope_diffusion_figures(target, cohorts)
        static_length_comparison(target, datasets)
        review(out)
        require(d.snapshot(d.EVIDENCE) == before, 'production input changed; all products invalid')
        require(input_stamps(d.EVIDENCE) == authentication['input_stamps'], 'production input identity changed')
        require(d.snapshot(old_root) == old_before, 'N32 input changed; all products invalid')
        require({str(p.relative_to(d.PROJECT)): d.file_record(p) for p in paths} == sources,
                'analysis source changed; all products invalid')
        d.write_json(out/'provenance.json', dict(status='DESCRIPTIVE_ANALYSIS_FOR_INDEPENDENT_REVIEW',
            scientific_acceptance=False, utc=d.utc(), sources=sources, python=sys.version,
            numpy=np.__version__, scipy=__import__('scipy').__version__,
            matplotlib=__import__('matplotlib').__version__, manifest_sha256=d.MANIFEST_SHA,
            input_hash_closure_after_analysis=True, argv=sys.argv,
            head=subprocess.run(['git', '-C', str(d.PROJECT), 'rev-parse', 'HEAD'],
                                check=True, capture_output=True, text=True).stdout.strip(),
            threads={p: os.environ[p] for p in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')},
            nice=os.getpriority(os.PRIO_PROCESS, 0), iopriority=priority))
        # Inventory excludes itself; provenance acts as the completion record.
        d.write_json(out/'result_inventory.json', d.snapshot(out))
    except BaseException as error:
        d.write_json(out/'FAILED.json', dict(status='ALL_PRODUCTS_INVALID', error=f'{type(error).__name__}: {error}'))
        raise


if __name__ == '__main__':
    main()
