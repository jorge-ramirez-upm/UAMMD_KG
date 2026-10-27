#!/usr/bin/env python3
"""Prepared, unexecuted read-only D2A.3 authentication followed by analysis.

No simulation or analysis on import. Never imports code from the evidence tree.
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


def git_blob(name):
    result = subprocess.run(['git', '-C', str(PROJECT), 'show',
                             f'{PREPARATION_SHA}:examples/slip-springs/{name}'],
                            capture_output=True, check=True, timeout=20)
    return result.stdout


def authenticate(root):
    """No scientific reductions; hash closure, schemas, finite data and support only."""
    before = snapshot(root)
    require(set(p.name for p in root.iterdir()) == {'config', 'provenance', 'runs', 'summary.json'},
            'unexpected campaign root entries')
    require(before['summary.json']['sha256'] == SUMMARY_SHA, 'summary snapshot changed')
    require(before['provenance/launch.json']['sha256'] == LAUNCH_SHA, 'launch snapshot changed')
    require(before['config/manifest.json']['sha256'] == MANIFEST_SHA, 'frozen manifest changed')
    require((root / 'config/manifest.json').read_bytes() == git_blob('e1_d2a3_config/manifest.json'),
            'manifest differs from reviewed preparation')
    m = load(root / 'config/manifest.json')
    summary, launch = load(root / 'summary.json'), load(root / 'provenance/launch.json')
    ids = [r['id'] for r in m['runs']]
    require(ids == [f'{c}-r{r}' for c in 'ABCD' for r in (1, 2)], 'four-cell run order')
    require(len({r['seed'] for r in m['runs']}) == len({r['replica_id'] for r in m['runs']}) == 8,
            'duplicate seeds/whole-run IDs')
    require(summary['status'] == 'completed_eight_runs_not_scientific_acceptance' and
            summary['completed_runs'] == ids and summary['failed_run'] is None, 'incomplete campaign')
    require([r['id'] for r in summary['run_records']] == ids, 'summary run records')
    require(launch['preparation_sha'] == PREPARATION_SHA and
            launch['manifest_sha256'] == summary['manifest_sha256'] == MANIFEST_SHA and
            launch['limits'] == m['limits'], 'launch identity/limits')
    require(launch['executable'] == {k: m['executable'][k] for k in ('bytes', 'sha256')},
            'recorded executable identity')
    require(launch['child_environment']['CUDA_VISIBLE_DEVICES'] == m['gpu_uuid'], 'GPU selection')
    require(launch['execution_choice'] == 'all eight sequentially without intermediate confirmation',
            'execution policy')
    expected_config = {f'config/{name}': record for name, record in launch['config_files'].items()}
    require({p.name for p in (root / 'config').iterdir()} ==
            {'manifest.json', 'manifest.sha256', 'equilibrium.steps', 'snapshots.steps'}, 'config set')
    for rel, record in expected_config.items():
        require(before[rel] == record, f'config hash: {rel}')
        require((root / rel).read_bytes() == git_blob('e1_d2a3_config/' + Path(rel).name),
                f'config differs from preparation: {rel}')
    require(set(expected_config) == {f'config/{p.name}' for p in (root / 'config').iterdir()},
            'config inventory omitted file')
    tools = launch['tool_files']
    require({p.name for p in (root / 'provenance').iterdir()} == set(tools) | {'launch.json'},
            'provenance set')
    for name, record in tools.items():
        require(before[f'provenance/{name}'] == record, f'provenance hash: {name}')
        if name.endswith('.py'):
            require((root / 'provenance' / name).read_bytes() == git_blob(name), f'tool identity: {name}')
            if name == 'e1_d2a3_run.py':
                require(file_record(PROJECT / name)['sha256'] == LOCAL_VALIDATOR_SHA,
                        'reviewed parameterized local validator changed')
            else:
                require((PROJECT / name).read_bytes() == git_blob(name), f'local validation helper changed: {name}')
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
        require(0 <= process['wall_seconds'] <= record['stage_wall_seconds'] <= 600 and
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
        require(validate_output(directory / 'output', run) == receipt['validation'], 'completion validation mismatch')
        # Parse every JSON file strictly as well as the schema checks above.
        for p in directory.rglob('*.json'):
            load(p)
    require(summary['max_child_rss_bytes'] == max(r['process']['max_rss_bytes'] for r in summary['run_records']),
            'summary peak RSS mismatch')
    require(summary['child_wall_seconds_sum'] == sum(r['process']['wall_seconds'] for r in summary['run_records']),
            'summary child-wall sum mismatch')
    require(sum(r['stage_wall_seconds'] for r in summary['run_records']) <= summary['wall_seconds'] <= 7200,
            'recorded campaign deadline')
    require(sum(v['bytes'] for v in before.values()) <= m['limits']['aggregate_output_bytes'], 'evidence size limit')
    require(summary['gpu_peak_memory_bytes'] is None, 'unsupported GPU peak claim')
    require(snapshot(root) == before, 'evidence changed during authentication')
    return m, summary, before


def mean_se(values):
    require(values.shape[0] == 2 and np.isfinite(values).all(), 'two finite whole-run replicas required')
    mean, se = values.mean(axis=0), values.std(axis=0, ddof=1) / math.sqrt(2)
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
        for r in range(2):
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


def read_replicas(root, manifest):
    cells = {}
    for cell in 'ABCD':
        selected = [r for r in manifest['runs'] if r['cell'] == cell]
        records = []
        for run in selected:
            with (root / 'runs' / run['id'] / 'output/dynamics/replica_correlations.csv').open(newline='') as f:
                records.append(list(csv.DictReader(f)))
        require(len(records) == 2 and len(records[0]) == len(records[1]) == 88, 'replica grid size')
        require(all([row[k] for k in SUPPORT] == [other[k] for k in SUPPORT]
                    for row, other in zip(*records)), 'replica support mismatch')
        values = np.array([[[float(row[q]) for q in QUANTITIES] for row in rows] for rows in records])
        require(np.isfinite(values).all() and (values[:, :, :8] >= 0).all(), 'nonfinite/negative squared displacement')
        t = np.array([float(r['lag_time']) for r in records[0]])
        counts = np.array([int(r['origins_per_chain']) for r in records[0]])
        cells[cell] = {'runs': selected, 'rows': records[0], 'time': t, 'values': values,
                       'blocks': np.array([int(r['decimation_samples']) for r in records[0]]),
                       'regions': [region(lag, count) for lag, count in zip(t, counts)]}
    return cells


def tables(root, out, manifest, summary, cells):
    curve_rows, features, slopes, ratio_regions, orientation = [], [], [], [], []
    for cell, data in cells.items():
        mean, se = mean_se(data['values'])
        for i, row in enumerate(data['rows']):
            result = {'cell': cell, **{k: row[k] for k in SUPPORT}, 'region': data['regions'][i]}
            for j, q in enumerate(QUANTITIES):
                result.update({q + '_r1': data['values'][0, i, j], q + '_r2': data['values'][1, i, j],
                               q + '_mean': mean[i, j], q + '_se_R2': se[i, j]})
            for suffix in ('r1', 'r2', 'mean', 'se_R2'):
                result['bare_cm_ratio_' + suffix] = (result['cm_msd_' + suffix] / (6 * data['time'][i] / 33)
                                                     if cell in 'AC' and data['time'][i] > 0 else '')
            curve_rows.append(result)
            if int(row['lag_samples']) in (1, 15, 128, 512, 1920, 7680):
                features.append(dict(result))
        for q in ('cm_msd', 'bead16_msd'):
            alpha, reasons = local_slopes(data['time'], data['values'][:, :, QUANTITIES.index(q)],
                                          data['blocks'], data['regions'])
            for i, reason in enumerate(reasons):
                available = [r == 'available_same_level_stencil' for r in reason]
                a, error = mean_se(alpha[:, i]) if all(available) else (None, None)
                slopes.append({'cell': cell, 'quantity': q, 'lag_time': data['time'][i],
                               'decimation_samples': int(data['blocks'][i]), 'region': data['regions'][i],
                               'stencil_status_r1': reason[0], 'stencil_status_r2': reason[1],
                               'alpha_r1': alpha[0, i] if available[0] else '',
                               'alpha_r2': alpha[1, i] if available[1] else '',
                               'alpha_mean': a if all(available) else '',
                               'alpha_se_R2': error if all(available) else ''})
        if cell in 'AC':
            for name in REGIONS:
                mask = np.array([r == name for r in data['regions']]) & (data['time'] > 0)
                ratios = data['values'][:, mask, QUANTITIES.index('cm_msd')] / (6 * data['time'][mask] / 33)
                row = {'cell': cell, 'region': name, 'lag_bins_descriptive_not_independent': int(mask.sum())}
                for label, numbers in [('r1', ratios[0]), ('r2', ratios[1]), ('mean_curve', ratios.mean(axis=0))]:
                    row.update({label + '_min_ratio': numbers.min(), label + '_max_ratio': numbers.max(),
                                label + '_max_absolute_deviation_from_one': np.max(np.abs(numbers - 1))})
                row['max_absolute_between_replica_ratio_gap'] = np.max(np.abs(ratios[0] - ratios[1]))
                ratio_regions.append(row)
        for q in ('c1', 'c2'):
            for r in range(2):
                y = data['values'][r, :, QUANTITIES.index(q)]
                eligible = np.flatnonzero((data['time'] > 0) & (data['time'] <= 19.2))
                below = [i for i in eligible if y[i] <= 0.5]
                i = below[0] if below else None
                orientation.append({'cell': cell, 'run': data['runs'][r]['id'], 'quantity': q,
                    'first_sample_at_or_below_half_in_primary': data['time'][i] if i is not None else '',
                    'previous_sample_lag': data['time'][i - 1] if i is not None else '',
                    'block_duration_at_sample': float(data['rows'][i]['orientation_block_duration']) if i is not None else '',
                    'status': 'sampled_crossing_no_interpolation_or_fit' if i is not None else 'not_observed_in_primary',
                    'value_at_19p2': y[np.flatnonzero(data['time'] == 19.2)[0]],
                    'minimum_primary_sample': y[data['time'] <= 19.2].min()})
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
        a, b = [p['child_wall_seconds'] for p in pair]
        performance_cells.append({'cell': cell, 'child_wall_r1_seconds': a, 'child_wall_r2_seconds': b,
            'mean_child_wall_seconds': (a + b) / 2, 'absolute_gap_percent_of_mean': abs(a - b) / ((a + b) / 2) * 100,
            'max_recorded_child_rss_bytes': max(p['peak_child_rss_bytes'] for p in pair),
            'recorded_pair_bytes': sum(p['recorded_run_bytes'] for p in pair)})
    for filename, rows in [('curves.csv', curve_rows), ('features.csv', features), ('slopes.csv', slopes),
                           ('bare_com_ratios_by_region.csv', ratio_regions), ('orientation_features.csv', orientation),
                           ('performance.csv', performance), ('performance_by_cell.csv', performance_cells)]:
        write_csv(out / filename, rows)
    return features, performance_cells, orientation


def figures(out, cells):
    import matplotlib
    # Backend selected before pyplot; this produces files only on explicit user execution.
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.size': 10, 'axes.labelsize': 11, 'pdf.fonttype': 42,
                         'savefig.dpi': 300, 'axes.spines.top': False, 'axes.spines.right': False})
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
        ax.axvspan(0.01, 0.15, color='#EAF1F5', zorder=0)
        ax.axvspan(19.2, 76.8, color='0.92', zorder=0)
        ax.axvline(0.15, color='0.65', linewidth=0.6)
        ax.axvline(19.2, color='0.55', linewidth=0.6)
        for cell, data in cells.items():
            y = data['values'][:, :, QUANTITIES.index(q)]
            mean, _ = mean_se(y)
            for block in np.unique(data['blocks']):
                mask = (data['blocks'] == block) & (data['time'] > 0)
                x = data['time'][mask]
                weak = x > 19.2
                for r, style in enumerate(('-', '--')):
                    values = y[r, mask]
                    if logarithmic:
                        omissions.extend({'cell': cell, 'quantity': q, 'replica': r + 1,
                                          'lag_time': float(t), 'reason': 'zero_MSD_cannot_be_logged'}
                                         for t in x[values == 0])
                        values = np.ma.masked_less_equal(values, 0)
                    ax.plot(x, values, color=COLORS[cell], linestyle=style, alpha=0.48, linewidth=0.85)
                displayed_mean = np.ma.masked_less_equal(mean[mask], 0) if logarithmic else mean[mask]
                ax.plot(x, displayed_mean, color=COLORS[cell], linewidth=1.8,
                        linestyle=':' if weak.all() else '-', marker='o' if block == 1 else 's',
                        markersize=2.6, markeredgewidth=0)
        handles = [Line2D([], [], color=COLORS[c], linewidth=2, label=LABELS[c]) for c in 'ABCD']
        if q == 'cm_msd':
            t = np.array([0.01, 76.8])
            ax.plot(t, 6 * t / 33, color='black', linestyle='-.', linewidth=1.2)
            handles.append(Line2D([], [], color='black', linestyle='-.', label=r'Bare reference $6\tau/33$'))
        ax.legend(handles=handles, frameon=False, fontsize=8, loc='best')
        ax.set(xlabel=r'Lag $\tau$ (model time units)', ylabel=ylabel, xlim=(0.009, 85))
        ax.grid(True, which='major', alpha=0.15)
        ax.set_title(f'Exploratory E1 dynamics: {q.replace("_", " ")}', fontsize=11)
        fig.text(0.12, 0.055, 'Thin solid: replica 1; thin dashed: replica 2; thick: equal-weight mean.\n'
                 'Circles: fine; squares: coarse; gray/dotted: weak tail. R=2; no confidence band.\n'
                 'N=32 bonds, M=256 chains/run, T=100, dt=0.0001; unwrapped coordinates.', fontsize=8)
        fig.subplots_adjust(left=0.12, right=0.98, bottom=0.23, top=0.91)
        for ext in ('png', 'pdf'):
            fig.savefig(out / f'figure_{number}_{q}.{ext}')
        plt.close(fig)
    write_json(out / 'plot_support.json', {
        'zero_lag_omitted_from_log_x_only': True, 'all_input_values_preserved_in_curves_csv': True,
        'nonpositive_MSD_omissions': omissions, 'fine_end': 0.15, 'primary_end': 19.2,
        'weak_tail_end': 76.8, 'line_segments_do_not_bridge_multi_tau_levels': True})
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-reviewed-analysis', action='store_true', required=True)
    parser.add_argument('--evidence', type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.evidence.is_symlink(), 'symlink evidence root')
    require(not args.output.is_symlink(), 'symlink output root')
    root, out = args.evidence.resolve(strict=True), args.output.resolve()
    require(not out.is_relative_to(root) and not root.is_relative_to(out), 'analysis/evidence trees must be disjoint')
    require(not out.is_relative_to(PROJECT.parents[1]), 'derived products must be outside repository')
    require(not out.is_relative_to(Path('/tmp')) and not out.is_relative_to(Path('/var/tmp')),
            'permanent output path required')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=False)
    phase = 'authentication'
    try:
        manifest, summary, before = authenticate(root)
        write_json(out / 'authentication.json', {'status': 'authenticated_before_reduction',
            'utc': utc(), 'preparation_sha': PREPARATION_SHA, 'summary_anchor': SUMMARY_SHA,
            'launch_anchor': LAUNCH_SHA, 'manifest_sha256': MANIFEST_SHA, 'input_inventory': before,
            'scope': 'committed manifest/tool identities plus captured summary/launch anchors and receipt closure; not independent execution attestation'})
        phase = 'scientific_reduction'
        cells = read_replicas(root, manifest)
        features, performance, orientation = tables(root, out, manifest, summary, cells)
        matplotlib_version = figures(out, cells)
        report(out, summary, before, features, performance, orientation)
        require(snapshot(root) == before, 'evidence changed during analysis; all derived products invalid')
        write_json(out / 'analysis_complete.json', {'status': 'exploratory_analysis_completed_for_review',
            'utc': utc(), 'evidence_unchanged_after_analysis': True, 'code': file_record(Path(__file__)),
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


if __name__ == '__main__':
    main()
