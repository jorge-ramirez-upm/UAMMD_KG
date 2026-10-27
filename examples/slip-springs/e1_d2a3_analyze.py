#!/usr/bin/env python3
"""Shared read-only D2A.3/D2A.4 authentication and analysis, preparation only.

Direct execution retains D2A.3 defaults. No analysis or simulation on import.
Never imports code from the evidence tree.
"""
import argparse
import csv
import datetime
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
from e1_d1_pilot import file_record, require
from e1_d2a3_run import MANIFEST_SHA, QUANTITIES, validate_output

PROJECT = Path(__file__).resolve().parent
PREPARATION_SHA = '5f9aa4daf35b4e4fd4df51b31bce34aa1aa09f68'
LOCAL_VALIDATOR_SHA = '31e5d47b2b39dec0377c3455c30b487c37c8f2b1bba8e81bb0932e14e9c5f438'
SUMMARY_SHA = '6e8e95a86318a60644ce5164dc0725a6ad62aad922d39fabb95174831e9ceabc'
LAUNCH_SHA = 'a8fa886971e56c8025e97587e494c732ed273fdc2a250dbda32de2f0520aa8a2'
DEFAULT_EVIDENCE = Path('/home/jramirez/UAMMD_KG-evidence/d2a3/exploratory-eight-v1')
LABELS = {'A': r'A: $\kappa=0,\ Z=0$', 'B': r'B: $\kappa=0,\ Z=2048$',
          'C': r'C: $\kappa=10,\ Z=0$', 'D': r'D: $\kappa=10,\ Z=2048$'}
COLORS = {'A': '#0072B2', 'B': '#D55E00', 'C': '#009E73', 'D': '#CC79A7'}
SUPPORT = ['lag_samples', 'lag_steps', 'lag_time', 'origins_per_chain',
           'decimation_samples', 'diffusion_phase_samples', 'orientation_block_samples',
           'orientation_block_duration']
REGIONS = ('fine', 'coarse_primary', 'weak_tail')


D3_PROFILE = {
    'name': 'D2A.3', 'preparation_sha': PREPARATION_SHA, 'summary_sha': SUMMARY_SHA,
    'launch_sha': LAUNCH_SHA, 'manifest_sha': MANIFEST_SHA, 'config': 'e1_d2a3_config',
    'replicas': 2, 'word': 'eight', 'primary_samples': 1920, 'maximum_samples': 7680,
    'features': (1, 15, 128, 512, 1920, 7680), 'endpoint_key': 'value_at_19p2', 'T': 100,
}


def support_region(lag_samples, origins, profile=D3_PROFILE):
    return ('weak_tail' if lag_samples > profile['primary_samples'] or origins < 32
            else ('fine' if lag_samples <= 15 else 'coarse_primary'))


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load(path):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, f'duplicate JSON key {k}: {path}')
            result[k] = v
        return result
    value = json.loads(path.read_text(), object_pairs_hook=pairs)
    json.dumps(value, allow_nan=False)
    return value


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def write_csv(path, rows):
    require(bool(rows), f'empty derived table: {path}')
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            require(all(not isinstance(v, (float, np.floating)) or math.isfinite(v)
                        for v in row.values()), f'nonfinite derived table: {path}')
            writer.writerow(row)


def snapshot(root):
    require(root.is_dir() and not root.is_symlink(), f'nonregular root: {root}')
    result = {}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(), f'symlink in evidence: {p}')
        require(p.is_file() or p.is_dir(), f'special evidence file: {p}')
        if p.is_file():
            result[str(p.relative_to(root))] = file_record(p)
    return result


def git_blob(name, preparation_sha=PREPARATION_SHA):
    result = subprocess.run(['git', '-C', str(PROJECT), 'show',
                             f'{preparation_sha}:examples/slip-springs/{name}'],
                            capture_output=True, check=True, timeout=20)
    return result.stdout


def authenticate(root, profile=D3_PROFILE):
    """No scientific reductions; hash closure, schemas, finite data and support only."""
    sha, n = profile['preparation_sha'], profile['replicas']
    before = snapshot(root)
    require(set(p.name for p in root.iterdir()) == {'config', 'provenance', 'runs', 'summary.json'},
            'unexpected campaign root entries')
    require(before['summary.json']['sha256'] == profile['summary_sha'], 'summary snapshot changed')
    require(before['provenance/launch.json']['sha256'] == profile['launch_sha'], 'launch snapshot changed')
    require(before['config/manifest.json']['sha256'] == profile['manifest_sha'], 'frozen manifest changed')
    require((root / 'config/manifest.json').read_bytes() == git_blob(profile['config'] + '/manifest.json', sha),
            'manifest differs from reviewed preparation')
    m = load(root / 'config/manifest.json')
    summary, launch = load(root / 'summary.json'), load(root / 'provenance/launch.json')
    ids = [r['id'] for r in m['runs']]
    require(ids == [f'{c}-r{r}' for c in 'ABCD' for r in range(1, n + 1)], 'four-cell run order')
    require(len({r['seed'] for r in m['runs']}) == len({r['replica_id'] for r in m['runs']}) == 4 * n,
            'duplicate seeds/whole-run IDs')
    require(summary['status'] == f"completed_{profile['word']}_runs_not_scientific_acceptance" and
            summary['completed_runs'] == ids and summary['failed_run'] is None, 'incomplete campaign')
    require([r['id'] for r in summary['run_records']] == ids, 'summary run records')
    require(launch['preparation_sha'] == sha and
            launch['manifest_sha256'] == summary['manifest_sha256'] == profile['manifest_sha'] and
            launch['limits'] == m['limits'], 'launch identity/limits')
    require(launch['executable'] == {k: m['executable'][k] for k in ('bytes', 'sha256')},
            'recorded executable identity')
    require(launch['child_environment']['CUDA_VISIBLE_DEVICES'] == m['gpu_uuid'], 'GPU selection')
    require(launch['execution_choice'] == f"all {profile['word']} sequentially without intermediate confirmation",
            'execution policy')
    expected_config = {f'config/{name}': record for name, record in launch['config_files'].items()}
    require({p.name for p in (root / 'config').iterdir()} ==
            {'manifest.json', 'manifest.sha256', 'equilibrium.steps', 'snapshots.steps'}, 'config set')
    for rel, record in expected_config.items():
        require(before[rel] == record, f'config hash: {rel}')
        require((root / rel).read_bytes() == git_blob(profile['config'] + '/' + Path(rel).name, sha),
                f'config differs from preparation: {rel}')
    require(set(expected_config) == {f'config/{p.name}' for p in (root / 'config').iterdir()},
            'config inventory omitted file')
    tools = launch['tool_files']
    require({p.name for p in (root / 'provenance').iterdir()} == set(tools) | {'launch.json'},
            'provenance set')
    for name, record in tools.items():
        require(before[f'provenance/{name}'] == record, f'provenance hash: {name}')
        if name.endswith('.py'):
            require((root / 'provenance' / name).read_bytes() == git_blob(name, sha), f'tool identity: {name}')
            if name == 'e1_d2a3_run.py':
                require(file_record(PROJECT / name)['sha256'] == LOCAL_VALIDATOR_SHA,
                        'reviewed parameterized local validator changed')
            else:
                require((PROJECT / name).read_bytes() == git_blob(name, sha), f'local validation helper changed: {name}')
    require(before['provenance/build-settings.json']['sha256'] == m['build_provenance']['sha256'],
            'build-settings identity')
    build = load(root / 'provenance/build-settings.json')
    require(build['precision'] == 'double' and build['CUDA_ARCH'] == 'sm_86' and
            build['builds']['current']['source_sha'] == m['source']['sha'] and
            build['builds']['current']['executable_sha256'] == m['executable']['sha256'] and
            build['builds']['current']['build_exit_code'] == 0, 'recorded build identity')
    for key, value in m['toolchain'].items():
        require(build[key] == value, f'build setting mismatch: {key}')
    require({p.name for p in (root / 'runs').iterdir()} == set(ids), 'run directory set')
    for run, record in zip(m['runs'], summary['run_records']):
        directory = root / 'runs' / run['id']
        require(file_record(directory / 'receipt.json') == record['receipt'], f"receipt hash: {run['id']}")
        receipt = load(directory / 'receipt.json')
        actual = {rel[len(f"runs/{run['id']}/"):]: v for rel, v in before.items()
                  if rel.startswith(f"runs/{run['id']}/") and not rel.endswith('/receipt.json')}
        require(actual == receipt['files'], f"receipt file closure: {run['id']}")
        process = load(directory / 'process.json')
        require(process == receipt['process'] == record['process'] and process['exit_code'] == 0 and
                process['status'] == 'exited', f"run exit/status: {run['id']}")
        require(0 <= process['wall_seconds'] <= record['stage_wall_seconds'] <= m['limits']['per_run_seconds'] and
                0 < process['max_rss_bytes'] <= m['limits']['max_host_rss_bytes'], 'recorded run limits')
        require(sum(v['bytes'] for rel, v in before.items() if rel.startswith(f"runs/{run['id']}/"))
                == record['output_bytes'] <= m['limits']['per_run_output_bytes'], 'run byte count/limit')
        run_launch = load(directory / 'launch.json')
        require(run_launch['argv'] == run['argv'], 'complete CLI mismatch')
        require(run_launch['gpu']['uuid'] == m['gpu_uuid'] and
                run_launch['gpu']['compute_capability'] == '8.6', 'run GPU identity')
        require(load(directory / 'output/metadata.json')['gpu'] == run_launch['gpu']['name'],
                'physical GPU-name record mismatch')
        for key in ('available_host_bytes', 'free_gpu_bytes', 'free_disk_bytes'):
            require(run_launch['resources'][key] >= m['limits'][{'available_host_bytes':
                    'min_available_host_bytes', 'free_gpu_bytes': 'min_free_gpu_bytes',
                    'free_disk_bytes': 'min_free_disk_bytes'}[key]], 'recorded prelaunch headroom')
        require(record['disk_free_after_bytes'] >= m['limits']['min_free_disk_bytes'], 'recorded final disk')
        require(validate_output(directory / 'output', run, m['expected']) == receipt['validation'], 'completion validation mismatch')
        # Parse every JSON file strictly as well as the schema checks above.
        for p in directory.rglob('*.json'):
            load(p)
    require(summary['max_child_rss_bytes'] == max(r['process']['max_rss_bytes'] for r in summary['run_records']),
            'summary peak RSS mismatch')
    require(summary['child_wall_seconds_sum'] == sum(r['process']['wall_seconds'] for r in summary['run_records']),
            'summary child-wall sum mismatch')
    require(sum(r['stage_wall_seconds'] for r in summary['run_records']) <= summary['wall_seconds'] <= m['limits']['aggregate_seconds'],
            'recorded campaign deadline')
    require(sum(v['bytes'] for v in before.values()) <= m['limits']['aggregate_output_bytes'], 'evidence size limit')
    require(summary['gpu_peak_memory_bytes'] is None, 'unsupported GPU peak claim')
    require(snapshot(root) == before, 'evidence changed during authentication')
    return m, summary, before


def mean_se(values):
    require(values.shape[0] >= 2 and np.isfinite(values).all(), 'at least two finite whole-run replicas required')
    mean, se = values.mean(axis=0), values.std(axis=0, ddof=1) / math.sqrt(values.shape[0])
    require(np.isfinite(mean).all() and np.isfinite(se).all(), 'nonfinite replica reduction')
    return mean, se


def region(lag, origins):
    return 'weak_tail' if lag > 19.2 or origins < 32 else ('fine' if lag <= 0.15 else 'coarse_primary')


def local_slopes(time, values, blocks, regions):
    """Centered three-point logarithmic stencil; no coarse-level boundary crossing."""
    out = np.full_like(values, np.nan, dtype=float)
    reasons = []
    for i in range(len(time)):
        if i == 0 or i == len(time) - 1:
            reason = 'record_edge'
        elif not blocks[i - 1] == blocks[i] == blocks[i + 1]:
            reason = 'multi_tau_level_boundary'
        elif any(regions[j] == 'weak_tail' for j in (i - 1, i, i + 1)):
            reason = 'weak_support_stencil'
        else:
            reason = 'available_same_level_stencil'
        per_replica = []
        for r in range(values.shape[0]):
            status = reason
            if status == 'available_same_level_stencil':
                if time[i - 1] <= 0 or np.any(values[r, i - 1:i + 2] <= 0):
                    status = 'logarithm_undefined'
                else:
                    left = math.log(time[i] / time[i - 1])
                    right = math.log(time[i + 1] / time[i])
                    backward = math.log(values[r, i]) - math.log(values[r, i - 1])
                    forward = math.log(values[r, i + 1]) - math.log(values[r, i])
                    # Three-point derivative at log(t_i), with unequal log spacing.
                    out[r, i] = (right / left * backward + left / right * forward) / (left + right)
            per_replica.append(status)
        reasons.append(per_replica)
    return out, reasons


def read_replicas(root, manifest, profile=D3_PROFILE):
    cells = {}
    for cell in 'ABCD':
        selected = [r for r in manifest['runs'] if r['cell'] == cell]
        records = []
        for run in selected:
            with (root / 'runs' / run['id'] / 'output/dynamics/replica_correlations.csv').open(newline='') as f:
                records.append(list(csv.DictReader(f)))
        n = profile['replicas']
        require(len(records) == n and all(len(rows) == manifest['expected']['exported_bins_per_chain']
                                         for rows in records), 'replica grid size')
        anchor = [[row[k] for k in SUPPORT] for row in records[0]]
        require(all([[row[k] for k in SUPPORT] for row in rows] == anchor
                    for rows in records[1:]), 'replica support mismatch')
        values = np.array([[[float(row[q]) for q in QUANTITIES] for row in rows] for rows in records])
        require(np.isfinite(values).all() and (values[:, :, :8] >= 0).all(), 'nonfinite/negative squared displacement')
        t = np.array([float(r['lag_time']) for r in records[0]])
        cells[cell] = {'runs': selected, 'rows': records[0], 'time': t, 'values': values,
                       'blocks': np.array([int(r['decimation_samples']) for r in records[0]]),
                       'regions': [support_region(int(row['lag_samples']), int(row['origins_per_chain']), profile)
                                   for row in records[0]]}
    return cells


def tables(root, out, manifest, summary, cells, profile=D3_PROFILE):
    n = profile['replicas']
    se_name = f'se_R{n}'
    curve_rows, features, slopes, ratio_regions, orientation = [], [], [], [], []
    for cell, data in cells.items():
        mean, se = mean_se(data['values'])
        for i, row in enumerate(data['rows']):
            result = {'cell': cell, **{k: row[k] for k in SUPPORT}, 'region': data['regions'][i]}
            for j, q in enumerate(QUANTITIES):
                result.update({q + f'_r{r+1}': data['values'][r, i, j] for r in range(n)})
                result.update({q + '_mean': mean[i, j], q + '_' + se_name: se[i, j]})
            for suffix in (*[f'r{r+1}' for r in range(n)], 'mean', se_name):
                result['bare_cm_ratio_' + suffix] = (result['cm_msd_' + suffix] / (6 * data['time'][i] / 33)
                                                     if cell in 'AC' and data['time'][i] > 0 else '')
            curve_rows.append(result)
            if int(row['lag_samples']) in profile['features']:
                features.append(dict(result))
        for q in ('cm_msd', 'bead16_msd'):
            alpha, reasons = local_slopes(data['time'], data['values'][:, :, QUANTITIES.index(q)],
                                          data['blocks'], data['regions'])
            for i, reason in enumerate(reasons):
                available = [r == 'available_same_level_stencil' for r in reason]
                a, error = mean_se(alpha[:, i]) if all(available) else (None, None)
                slope_row = {'cell': cell, 'quantity': q, 'lag_time': data['time'][i],
                             'lag_samples': int(data['rows'][i]['lag_samples']),
                             'decimation_samples': int(data['blocks'][i]), 'region': data['regions'][i]}
                slope_row.update({f'stencil_status_r{r+1}': reason[r] for r in range(n)})
                slope_row.update({f'alpha_r{r+1}': alpha[r, i] if available[r] else '' for r in range(n)})
                slope_row.update({'alpha_mean': a if all(available) else '',
                                  'alpha_' + se_name: error if all(available) else ''})
                slopes.append(slope_row)
        if cell in 'AC':
            for name in REGIONS:
                mask = np.array([r == name for r in data['regions']]) & (data['time'] > 0)
                ratios = data['values'][:, mask, QUANTITIES.index('cm_msd')] / (6 * data['time'][mask] / 33)
                row = {'cell': cell, 'region': name, 'lag_bins_descriptive_not_independent': int(mask.sum())}
                for label, numbers in [(f'r{r+1}', ratios[r]) for r in range(n)] + [('mean_curve', ratios.mean(axis=0))]:
                    row.update({label + '_min_ratio': numbers.min(), label + '_max_ratio': numbers.max(),
                                label + '_max_absolute_deviation_from_one': np.max(np.abs(numbers - 1))})
                row['max_absolute_between_replica_ratio_gap'] = np.max(np.ptp(ratios, axis=0))
                ratio_regions.append(row)
        for q in ('c1', 'c2'):
            for r in range(n):
                y = data['values'][r, :, QUANTITIES.index(q)]
                eligible = np.flatnonzero((data['time'] > 0) &
                                          np.array([name != 'weak_tail' for name in data['regions']]))
                below = [i for i in eligible if y[i] <= 0.5]
                i = below[0] if below else None
                orientation.append({'cell': cell, 'run': data['runs'][r]['id'], 'quantity': q,
                    'first_sample_at_or_below_half_in_primary': data['time'][i] if i is not None else '',
                    'previous_sample_lag': data['time'][i - 1] if i is not None else '',
                    'block_duration_at_sample': float(data['rows'][i]['orientation_block_duration']) if i is not None else '',
                    'status': 'sampled_crossing_no_interpolation_or_fit' if i is not None else 'not_observed_in_primary',
                    profile['endpoint_key']: y[next(i for i, row in enumerate(data['rows'])
                                                  if int(row['lag_samples']) == profile['primary_samples'])],
                    'minimum_primary_sample': y[np.array([name != 'weak_tail' for name in data['regions']])].min()})
    performance = []
    for run, record in zip(manifest['runs'], summary['run_records']):
        base = root / 'runs' / run['id'] / 'output'
        main, dyn, eq = load(base / 'metadata.json'), load(base / 'dynamics/metadata.json'), load(base / 'equilibrium_complete.json')
        p = {'run': run['id'], 'cell': run['cell'], 'child_wall_seconds': record['process']['wall_seconds'],
             'stage_wall_seconds': record['stage_wall_seconds'], 'peak_child_rss_bytes': record['process']['max_rss_bytes'],
             'recorded_run_bytes': record['output_bytes']}
        for prefix, source, keys in (
                ('main_', main, ('initialization_seconds', 'integration_seconds', 'production_wall_seconds',
                                 'observation_seconds', 'recurrent_output_seconds', 'final_output_seconds',
                                 'force_and_diagnostic_wall_seconds')),
                ('dynamics_', dyn, ('shared_readback_seconds', 'extra_readback_seconds',
                                    'acquisition_cpu_seconds', 'evaluation_csv_seconds')),
                ('equilibrium_', eq, ('exclusive_seconds', 'observer_wall_seconds', 'transfer_seconds'))):
            for key in keys:
                require(isinstance(source[key], (int, float)) and math.isfinite(source[key]) and source[key] >= 0,
                        f'nonfinite timing: {run["id"]}/{key}')
                p[prefix + key] = source[key]
        performance.append(p)
    performance_cells = []
    for cell in 'ABCD':
        pair = [p for p in performance if p['cell'] == cell]
        times = [p['child_wall_seconds'] for p in pair]
        row = {'cell': cell, **{f'child_wall_r{r+1}_seconds': t for r, t in enumerate(times)},
               'mean_child_wall_seconds': sum(times) / n,
               'absolute_gap_percent_of_mean': (max(times) - min(times)) / (sum(times) / n) * 100,
               'max_recorded_child_rss_bytes': max(p['peak_child_rss_bytes'] for p in pair),
               'recorded_pair_bytes' if n == 2 else 'recorded_cell_bytes': sum(p['recorded_run_bytes'] for p in pair)}
        performance_cells.append(row)
    for filename, rows in [('curves.csv', curve_rows), ('features.csv', features), ('slopes.csv', slopes),
                           ('bare_com_ratios_by_region.csv', ratio_regions), ('orientation_features.csv', orientation),
                           ('performance.csv', performance), ('performance_by_cell.csv', performance_cells)]:
        write_csv(out / filename, rows)
    return features, performance_cells, orientation


def figures(out, cells, profile=D3_PROFILE):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.size': 10, 'axes.labelsize': 11, 'pdf.fonttype': 42,
                         'savefig.dpi': 300, 'axes.spines.top': False, 'axes.spines.right': False})
    primary, maximum = profile['primary_samples'] * .01, profile['maximum_samples'] * .01
    n = profile['replicas']
    omissions = []
    for number, (q, ylabel, logarithmic) in enumerate([
            ('cm_msd', r'$g_{\rm CM}(\tau)$', True),
            ('bead16_msd', r'$g_{16}(\tau)$ (absolute MSD)', True),
            ('c1', r'$C_1(\tau)$ (direction)', False),
            ('c2', r'$C_2(\tau)$ ($P_2$ orientation)', False)], 1):
        fig, ax = plt.subplots(figsize=(7.2, 5.2))
        ax.set_xscale('log')
        if logarithmic:
            ax.set_yscale('log')
        else:
            ax.axhline(0, color='0.45', linewidth=0.7)
        ax.axvspan(.01, .15, color='#EAF1F5', zorder=0)
        ax.axvspan(primary, maximum, color='0.92', zorder=0)
        for boundary in (.15, primary):
            ax.axvline(boundary, color='0.6', linewidth=.6)
        for cell, data in cells.items():
            y = data['values'][:, :, QUANTITIES.index(q)]
            mean, _ = mean_se(y)
            tail = np.array([r == 'weak_tail' for r in data['regions']])
            for block in np.unique(data['blocks']):
                for weak in (False, True):
                    mask = (data['blocks'] == block) & (data['time'] > 0) & (tail == weak)
                    if not mask.any():
                        continue
                    x = data['time'][mask]
                    for r in range(n):
                        values = y[r, mask]
                        if logarithmic:
                            omissions.extend({'cell': cell, 'quantity': q, 'replica': r + 1,
                                              'lag_time': float(t), 'reason': 'zero_MSD_cannot_be_logged'}
                                             for t in x[values == 0])
                            values = np.ma.masked_less_equal(values, 0)
                        ax.plot(x, values, color=COLORS[cell], linestyle=('-', '--', '-.')[r],
                                alpha=.38 if n == 3 else .48, linewidth=.7)
                    displayed = np.ma.masked_less_equal(mean[mask], 0) if logarithmic else mean[mask]
                    ax.plot(x, displayed, color=COLORS[cell], linewidth=1.8,
                            linestyle=':' if weak else '-', marker='o' if block == 1 else 's',
                            markersize=2.6, markeredgewidth=0)
        handles = [Line2D([], [], color=COLORS[c], linewidth=2, label=LABELS[c]) for c in 'ABCD']
        if q == 'cm_msd':
            t = np.array([.01, maximum])
            ax.plot(t, 6 * t / 33, color='black', linestyle='-.', linewidth=1.2)
            handles.append(Line2D([], [], color='black', linestyle='-.', label=r'Bare reference $6\tau/33$'))
        ax.legend(handles=handles, frameon=False, fontsize=8, loc='best')
        ax.set(xlabel=r'Lag $\tau$ (model time units)', ylabel=ylabel, xlim=(.009, maximum * 1.1))
        ax.grid(True, which='major', alpha=.15)
        ax.set_title(f"{profile['name']} exploratory E1 dynamics: {q.replace('_', ' ')}", fontsize=11)
        styles = 'solid / dashed / dash-dot' if n == 3 else 'solid / dashed'
        fig.text(.12, .055, f'Thin {styles}: replicas; thick: equal-weight mean.\n'
                 f'Circles: fine; squares: coarse; gray/dotted: weak tail. R={n}; no confidence band.\n'
                 f"N=32, M=256, T={profile['T']}, dt=0.0001; unwrapped coordinates.", fontsize=8)
        fig.subplots_adjust(left=.12, right=.98, bottom=.23, top=.91)
        for ext in ('png', 'pdf'):
            fig.savefig(out / f'figure_{number}_{q}.{ext}')
        plt.close(fig)
    write_json(out / 'plot_support.json', {
        'zero_lag_omitted_from_log_x_only': True, 'all_input_values_preserved_in_curves_csv': True,
        'nonpositive_MSD_omissions': omissions, 'fine_end': .15, 'primary_end': primary,
        'primary_end_samples': profile['primary_samples'], 'weak_tail_end': maximum,
        'line_segments_do_not_bridge_multi_tau_levels': True})
    return matplotlib.__version__


def report(out, summary, authenticated, features, performance, orientation):
    lines = ['# D2A.3 — authenticated exploratory products for scientific review', '',
             'Generated only after hash/schema/support authentication. This is an automated descriptive',
             'summary, not equilibrium, terminal-dynamics, performance or model acceptance.', '',
             f"Recorded campaign wall: {summary['wall_seconds']:.6f} s; peak child RSS: {summary['max_child_rss_bytes']} bytes.",
             f"Authenticated current evidence files: {sum(v['bytes'] for v in authenticated.values())} bytes.",
             f"Recorded pre-final-summary evidence size: {summary['campaign_bytes_before_final_summary']} bytes (different accounting endpoint).", '',
             '| Cell | child wall r1 / r2 (s) | gap / mean (%) | peak child RSS (bytes) | pair evidence (bytes) |',
             '|---|---|---|---|---|']
    for p in performance:
        lines.append(f"| {p['cell']} | {p['child_wall_r1_seconds']:.3f} / {p['child_wall_r2_seconds']:.3f} | "
                     f"{p['absolute_gap_percent_of_mean']:.3f} | {p['max_recorded_child_rss_bytes']} | {p['recorded_pair_bytes']} |")
    lines += ['', 'All available timer categories are in performance.csv. They overlap and must not',
              'be added as independent wall contributions. No isolated observer benchmark or GPU peak',
              'measurement was conducted. Runtime consistency here is descriptive for two runs.', '',
              '## Primary support endpoint (19.2; 63 origins per chain, not independent samples)', '',
              '| Cell | quantity | replica 1 | replica 2 | mean | descriptive SE (R=2) |', '|---|---|---|---|---|---|']
    for p in features:
        if float(p['lag_time']) == 19.2:
            for q in ('cm_msd', 'bead16_msd', 'c1', 'c2'):
                lines.append(f"| {p['cell']} | {q} | {p[q+'_r1']:.6g} | {p[q+'_r2']:.6g} | {p[q+'_mean']:.6g} | {p[q+'_se_R2']:.3g} |")
    lines += ['', '## Interpretation and next-study decision', '',
              'Inspect the four figures, full replica curves, bare COM regional ratios, slopes and',
              'orientation_features.csv together. Bare ratios are a consistency reference, with no',
              'new pass/fail tolerance. Half-level entries are first sampled values at or below 0.5,',
              'not interpolated relaxation times or evidence of exponential decay. Coarse values',
              'are feature-block correlations; transitions between support levels are not fine-lag fits.', '']
    unresolved = sorted({p['cell'] for p in orientation if p['status'] == 'not_observed_in_primary'})
    if unresolved:
        lines += [f"At least one replica/quantity has no sampled half-level crossing in primary support in cells: {', '.join(unresolved)}.",
                  'Recommendation for review: prioritize longer records for supported orientational',
                  'coverage in those cells, while checking timestep sensitivity before physical conclusions.']
    else:
        lines += ['Every replica/orientation quantity has a sampled half-level crossing in primary support.',
                  'Recommendation for review: compare decay shapes and replica agreement, then prioritize',
                  'a matched-physical-cadence finer-timestep study before asserting model-dependent rates.',
                  'A half-level crossing alone neither resolves the far tail nor establishes terminal motion.']
    lines += ['', 'This recommendation is provisional and must be checked against the actual figures.',
              'If early decay is already below resolution, review a shorter stride; if long supported',
              'lags are lacking, review longer duration. No next campaign is authorized automatically.', '',
              'Fixed spatial anchors between renewals can restrict motion; hopping moves attachment',
              'along the contour and canonical renewal can transfer constraints between chains.',
              'Bending stiffness changes backbone conformations and force relaxation. These are',
              'mechanistic possibilities, not identified causal contributions: this matrix does not',
              'vary hop/renewal rates or isolate these processes. Record observed ordering/shape',
              'separately from any mechanism proposed after inspection.', '',
              'Do not infer a constrained-chain nonzero terminal diffusion coefficient, reptation/tube',
              'scaling, single-exponential relaxation or invariant equilibrium from these curves.',
              'T=100 and lag<=19.2 primary support do not by themselves establish terminal behavior.',
              'D1.6 remains scientifically closed with qualifications: finite-timestep equilibrium',
              'preservation not confirmed. Startup drift, origin averaging and timestep sensitivity',
              'remain interpretation limitations. R=2 has one variance degree of freedom; SE is',
              'descriptive only. No chains, origins, monomers or lag bins are additional replicas.', '']
    (out / 'SCIENTIFIC_REVIEW.md').write_text('\n'.join(lines))


def analysis_main(profile=D3_PROFILE, report_writer=None, history_authenticator=None,
                  history_comparator=None, entry_point=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-reviewed-analysis', action='store_true', required=True)
    parser.add_argument('--evidence', type=Path, default=Path(profile.get('evidence', str(DEFAULT_EVIDENCE))))
    parser.add_argument('--output', type=Path, required=True)
    if history_authenticator is not None:
        parser.add_argument('--d2a3-analysis', type=Path, default=Path(
            '/home/jramirez/UAMMD_KG-evidence/d2a3-analysis/exploratory-eight-v1-analysis-v1'))
        parser.add_argument('--without-d2a3-comparison', action='store_true')
    args = parser.parse_args()
    require(not args.evidence.is_symlink(), 'symlink evidence root')
    require(not args.output.is_symlink(), 'symlink output root')
    root, out = args.evidence.resolve(strict=True), args.output.resolve()
    protected = [root]
    use_history = history_authenticator is not None and not args.without_d2a3_comparison
    if use_history:
        require(not args.d2a3_analysis.is_symlink(), 'symlink historical analysis root')
        protected.extend([args.d2a3_analysis.resolve(strict=True), DEFAULT_EVIDENCE.resolve(strict=True)])
    for original in protected:
        require(not out.is_relative_to(original) and not original.is_relative_to(out),
                'analysis output and all original evidence/products must be disjoint')
    require(not out.is_relative_to(PROJECT.parents[1]), 'derived products must be outside repository')
    require(not out.is_relative_to(Path('/tmp')) and not out.is_relative_to(Path('/var/tmp')),
            'permanent output path required')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=False)
    phase, history = 'authentication', None
    try:
        manifest, summary, before = authenticate(root, profile)
        if use_history:
            history = history_authenticator(args.d2a3_analysis.resolve(strict=True))
            write_json(out / 'historical_authentication.json', {k: v for k, v in history.items() if k != 'rows'})
        write_json(out / 'authentication.json', {'status': 'authenticated_before_reduction',
            'utc': utc(), 'preparation_sha': profile['preparation_sha'], 'summary_anchor': profile['summary_sha'],
            'launch_anchor': profile['launch_sha'], 'manifest_sha256': profile['manifest_sha'], 'input_inventory': before,
            'historical_comparison': 'authenticated_prior_products' if history else 'not_requested',
            'scope': 'committed manifest/tool identities plus captured summary/launch anchors and receipt closure; not independent execution attestation'})
        phase = 'scientific_reduction'
        cells = read_replicas(root, manifest, profile)
        features, performance, orientation = tables(root, out, manifest, summary, cells, profile)
        comparison = history_comparator(cells, history, out) if history else None
        matplotlib_version = figures(out, cells, profile)
        if report_writer is None:
            report(out, summary, before, features, performance, orientation)
        else:
            report_writer(out, summary, before, features, performance, orientation, cells, comparison)
        require(snapshot(root) == before, 'evidence changed during analysis; all derived products invalid')
        if history:
            require(snapshot(Path(history['analysis_root'])) == history['analysis_inventory'] and
                    snapshot(Path(history['evidence_root'])) == history['input_inventory'],
                    'historical evidence/products changed; all derived products invalid')
        write_json(out / 'analysis_complete.json', {'status': 'exploratory_analysis_completed_for_review',
            'utc': utc(), 'evidence_unchanged_after_analysis': True, 'code': file_record(Path(__file__)),
            'entry_point': file_record(Path(entry_point)) if entry_point else None, 'profile': profile,
            'validation_code': file_record(PROJECT / 'e1_d2a3_run.py'), 'python': sys.version,
            'analysis_checkout_head': subprocess.run(['git', '-C', str(PROJECT), 'rev-parse', 'HEAD'],
                                                     capture_output=True, text=True, check=True,
                                                     timeout=20).stdout.strip(),
            'platform': platform.platform(), 'numpy': np.__version__, 'matplotlib': matplotlib_version,
            'products': snapshot(out), 'scientific_acceptance': False})
    except BaseException as error:
        write_json(out / 'FAILED.json', {'status': 'failed_products_not_valid', 'phase': phase,
                                        'error': f'{type(error).__name__}: {error}', 'utc': utc()})
        raise
    print(f'Authenticated exploratory products for independent review: {out}')


def main():
    analysis_main()


if __name__ == '__main__':
    main()
