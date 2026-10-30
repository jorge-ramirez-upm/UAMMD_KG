#!/usr/bin/env python3
"""Prepared CPU-only checks using synthetic evidence; no campaign or GPU access.

No checks run on import. Fixtures persist under the prescribed analysis root.
"""
import csv
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import e1_d2a5_n64_analyze as a
from e1_d2a3_run import exported_grid
from e1_d2a5_validate import curve_header, curves


def reject(action):
    try:
        action()
    except (ValueError, KeyError, AssertionError):
        return
    raise AssertionError('malformed evidence accepted')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False))


def synthetic_curves(path, run, n):
    path.parent.mkdir(parents=True, exist_ok=True)
    e = run['expected']
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=curve_header(n))
        writer.writeheader()
        for lag, block in exported_grid(e):
            t = lag * e['stride'] * e['dt']
            row = {k: 0 for k in curve_header(n)}
            row.update(replica=run['replica_id'], chain='', lag_samples=lag,
                       lag_steps=lag*e['stride'], lag_time=t,
                       origins_per_chain=e['dynamics_frames']//block-lag//block,
                       decimation_samples=block, diffusion_phase_samples=block-1,
                       orientation_block_samples=block,
                       orientation_block_duration=block*e['stride']*e['dt'])
            for key in row:
                if key.endswith('_msd'):
                    row[key] = (1 + .01*run['replica']) * 6*t/(n+1)
            row.update(c1=float(np.exp(-t/200)), c2=float(np.exp(-t/100)))
            writer.writerow(row)


def main():
    output = a.regular_path(a.OUTPUT / 'regression')
    output.mkdir(parents=True, exist_ok=False)
    root = output / 'synthetic-campaign'
    manifest = a.load(a.CONFIG / 'manifest.json')
    runs = [r for r in manifest['runs'] if r['N'] == 64]
    for name in ('manifest.json', 'manifest.sha256', 'n64-equilibrium.steps', 'n64-snapshots.steps'):
        target = root / 'config' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(a.CONFIG / name, target)
    for name in manifest['tools']:
        target = root / 'provenance' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT / name, target)
    save(root / 'provenance/launch.json', dict(manifest_sha256=a.MANIFEST_SHA,
         implementation_sha=manifest['implementation_sha'], executable=manifest['executable']))
    records = []
    for run in runs:
        directory = root / 'runs' / run['id']
        save(directory / 'process.json', dict(status='exited', exit_code=0))
        save(directory / 'launch.json', dict(argv=run['argv'], seed=run['seed'],
             replica_id=run['replica_id'], gpu=dict(name='synthetic-not-a-device', uuid=manifest['gpu_uuid'])))
        save(directory / 'output/metadata.json', dict(gpu='synthetic-not-a-device'))
        synthetic_curves(directory / 'output/dynamics/replica_correlations.csv', run, 64)
        process = a.load(directory / 'process.json')
        save(directory / 'receipt.json', dict(id=run['id'], manifest_sha256=a.MANIFEST_SHA,
             validation={'synthetic': True}, process=process, files=a.snapshot(directory)))
        records.append(dict(id=run['id'], process=process, receipt=a.file_record(directory / 'receipt.json'),
                            output_bytes=sum(v['bytes'] for v in a.snapshot(directory).values())))
    summary = dict(manifest_sha256=a.MANIFEST_SHA, completed_runs=a.IDS,
                   run_records=records, status='running', active_run='n128-A-r1')
    save(root / 'summary.json', summary)
    # A forbidden sibling makes accidental whole-campaign traversal fail.
    (root / 'runs/n128-A-r1').symlink_to(output / 'absent-active-directory', target_is_directory=True)
    (root / 'progress.jsonl').write_text('mutable progress\n')
    with patch.object(a, 'validate_output', return_value={'synthetic': True}) as validator:
        _, _, immutable, before, auth = a.authenticate(root)
        assert validator.call_count == 12
        assert all(call.args[0].is_relative_to(root / 'runs') and
                   call.args[0].parent.name in a.IDS for call in validator.call_args_list)
        assert set(auth['completed_n64_records']) == set(a.IDS)
        assert all('n128' not in p for p in before['files'])
        summary['active_run'] = 'n128-B-r1'
        summary['completed_runs'] = a.IDS + ['n128-A-r1']
        save(root / 'summary.json', summary)
        (root / 'progress.jsonl').write_text('changed progress\n')
        assert a.selected_inventory(root, immutable) == before
        a.authenticate(root)  # Campaign completion and mutable summary hashes are irrelevant.
        validator.return_value = {'incorrect_validation': True}
        reject(lambda: a.authenticate(root))
        validator.return_value = {'synthetic': True}
        bad = dict(summary, completed_runs=a.IDS[:-1])
        reject(lambda: a.completed_records(bad))
        reject(lambda: a.completed_records(dict(summary, completed_runs=a.IDS + [a.IDS[0]])))
        reject(lambda: a.completed_records(dict(summary, manifest_sha256='0'*64)))
        receipt_path = root / 'runs' / a.IDS[0] / 'receipt.json'
        original = receipt_path.read_bytes()
        receipt_path.write_bytes(original + b' ')
        reject(lambda: a.authenticate(root))
        receipt_path.write_bytes(original)
        launch_path = receipt_path.parent / 'launch.json'
        launch = a.load(launch_path)
        launch['seed'] += 1
        save(launch_path, launch)
        # Re-anchor this deliberately malformed fixture to reach the seed check.
        receipt = a.load(receipt_path)
        receipt['files']['launch.json'] = a.file_record(launch_path)
        save(receipt_path, receipt)
        records[0]['receipt'] = a.file_record(receipt_path)
        records[0]['output_bytes'] = sum(v['bytes'] for v in a.snapshot(receipt_path.parent).values())
        save(root / 'summary.json', summary)
        reject(lambda: a.authenticate(root))
        assert a.selected_inventory(root, immutable) != before

    # Independently test actual streaming grid/schema validation without mocking it.
    run = runs[1]
    source = root / 'runs' / run['id'] / 'output/dynamics/replica_correlations.csv'
    assert curves(source, run, ['']) == 143
    bad_curve = output / 'bad_curve.csv'
    with source.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    def bad_write():
        with bad_curve.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=curve_header(64))
            writer.writeheader()
            writer.writerows(rows)
    rows[20]['origins_per_chain'] = '31'
    bad_write()
    reject(lambda: curves(bad_curve, run, ['']))
    rows[20]['origins_per_chain'] = str(run['expected']['dynamics_frames']//2-24//2)
    rows[20]['c1'] = 'nan'
    bad_write()
    reject(lambda: curves(bad_curve, run, ['']))

    cells = a.read_cells(root, manifest, runs)
    assert all(d['rows'][np.flatnonzero(np.array(d['regions']) != 'weak_tail')[-1]]['lag_samples'] == '196608'
               for d in cells.values())
    tables = output / 'tables'
    tables.mkdir()
    windows, orientation = a.numerical_tables(tables, cells)
    assert windows and len(orientation) == 24
    assert all(np.isclose(w['slope_min'], 1) and np.isclose(w['slope_max'], 1) for w in windows)
    assert all(np.isclose(w['effective_D_min'], w['effective_D_max']) for w in windows)
    assert all(w['min_origins'] >= 32 and w['end_time'] <= 1966.08 for w in windows)
    with (tables / 'bare_com.csv').open(newline='') as stream:
        assert all(np.isclose(float(r['ratio_mean']), 1.02) for r in csv.DictReader(stream))
    assert all(w['quantity'] in ('cm_msd', 'bead32_msd') for w in windows)
    with (tables / 'slopes.csv').open(newline='') as stream:
        slopes = list(csv.DictReader(stream))
    assert any(r['status_r1'] == 'multi_tau_level_boundary' and r['alpha_r1'] == '' for r in slopes)
    assert any(r['status_r1'] == 'weak_support_stencil' and r['alpha_r1'] == '' for r in slopes)
    values = np.array([[1., 3.], [2., 6.], [3., 9.]])
    mean, se = a.mean_se(values)
    np.testing.assert_allclose(mean, [2, 6])
    np.testing.assert_allclose(se, [1/np.sqrt(3), np.sqrt(3)])

    old_manifest = a.load(PROJECT / 'e1_d2a4_config/manifest.json')
    old_root = output / 'synthetic-n32'
    for old_run in old_manifest['runs']:
        synthetic_curves(old_root / 'runs' / old_run['id'] / 'output/dynamics/replica_correlations.csv',
                         dict(old_run, expected=old_manifest['expected']), 32)
    old_cells = a.read_replicas(old_root, old_manifest, a.N32_PROFILE)
    a.compare_n32(tables, cells, old_cells, old_manifest, runs)
    a.figures(tables, cells)
    a.report(tables, windows, orientation)
    assert len(list(tables.glob('figure_*.png'))) == len(list(tables.glob('figure_*.pdf'))) == 4
    save(output / 'regression_complete.json', dict(status='synthetic_cpu_checks_passed',
         scope='subset isolation, receipt integrity, support, numerical diagnostics, comparison, plots; '
               'full physical validator mocked in synthetic authentication only'))
    print(f'CPU-only regression products: {output}')


if __name__ == '__main__':
    main()
