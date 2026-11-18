#!/usr/bin/env python3
"""Prepared synthetic CPU checks. Never opens production evidence; no import-time checks."""
import argparse
import copy
import csv
import os
from pathlib import Path
import sys
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import e1_d2a5_n128_analyze as a
import numpy as np
from e1_d2a5_validate import curves, curve_header
from d2a5_n64_analysis_regression import synthetic_curves, reject


def authentication_checks(out, manifest):
    """Mock bytes/JSON and physical validation only; exercise the real 24-run closure logic."""
    root = out/'mock-campaign'
    root.mkdir()
    records, documents = [], {}
    inventory = {}
    for name in ('manifest.json', 'manifest.sha256', *manifest['schedules']):
        inventory['config/'+name] = a.d.file_record(a.d.CONFIG/name)
    archived = {name: record for name, record in manifest['tools'].items()}
    for label, proof in manifest['prerequisites'].items():
        archived[label+'-'+Path(proof['path']).name] = proof['file']
    inventory.update({'provenance/'+k: v for k, v in archived.items()})
    tree = a.subprocess.run(['git', '-C', str(PROJECT), 'ls-tree', '-r', manifest['implementation_sha']],
                            check=True, capture_output=True, text=True).stdout.strip()
    documents[root/'provenance/launch.json'] = dict(manifest_sha256=a.d.MANIFEST_SHA,
        implementation_sha=manifest['implementation_sha'], executable=manifest['executable'],
        compiler_provenance=manifest['compiler_provenance'], source_tree=tree, preserved_files=archived)
    inventory['provenance/launch.json'] = dict(bytes=1, sha256='synthetic')
    # Real config bytes are used for the pinned identity comparison, no campaign access.
    (root/'config').mkdir()
    for name in ('manifest.json', 'manifest.sha256'):
        (root/'config'/name).write_bytes((a.d.CONFIG/name).read_bytes())
    for run in manifest['runs']:
        directory = root/'runs'/run['id']
        directory.mkdir(parents=True)
        process = dict(status='exited', exit_code=0)
        documents[directory/'process.json'] = process
        documents[directory/'launch.json'] = dict(argv=run['argv'], seed=run['seed'],
            replica_id=run['replica_id'], gpu=dict(uuid=manifest['gpu_uuid'], name='synthetic'))
        documents[directory/'output/metadata.json'] = dict(gpu='synthetic')
        files = {name: dict(bytes=1, sha256='synthetic') for name in
                 ('process.json', 'launch.json', 'output/metadata.json')}
        documents[directory/'receipt.json'] = dict(id=run['id'], manifest_sha256=a.d.MANIFEST_SHA,
            process=process, validation={'synthetic': True}, files=files)
        files = dict(files, **{'receipt.json': dict(bytes=1, sha256='synthetic')})
        inventory.update({'runs/'+run['id']+'/'+k: v for k, v in files.items()})
        records.append(dict(id=run['id'], process=process, receipt=files['receipt.json'], output_bytes=4))
    summary = dict(status='completed_24_runs_not_scientific_acceptance', phase='finished', active_run=None,
        resource_limit_violations=[], manifest_sha256=a.d.MANIFEST_SHA, completed_runs=a.IDS, run_records=records)
    documents[root/'summary.json'] = summary
    original_load = a.d.load
    def load(path):
        return documents[path] if path in documents else original_load(path)
    with patch.object(a.d, 'load', side_effect=load), patch.object(a.d, 'snapshot', return_value=inventory), \
         patch.object(a, 'input_stamps', return_value={}), \
         patch.object(a, 'validate_output', return_value={'synthetic': True}) as validator:
        _, before, auth = a.authenticate(root)
        assert before == inventory and len(auth['completed_runs']) == validator.call_count == 24
        for field, bad in (('completed_runs', a.IDS[:-1]), ('completed_runs', a.IDS+[a.IDS[0]]),
                           ('active_run', a.IDS[-1]), ('error', 'failure'), ('status', 'running'),
                           ('resource_limit_violations', ['disk'])):
            altered = dict(summary, **{field: bad})
            reject(lambda: a.completed_records(altered))
        receipt = documents[root/'runs'/a.IDS[-1]/'receipt.json']
        original = receipt['files']
        receipt['files'] = {}
        reject(lambda: a.authenticate(root))
        receipt['files'] = original
        launch = documents[root/'runs'/a.IDS[-1]/'launch.json']
        launch['seed'] += 1
        reject(lambda: a.authenticate(root))
        launch['seed'] -= 1
        validator.return_value = {'wrong': True}
        reject(lambda: a.authenticate(root))
    # Real filesystem inventory checks, independent of the mocks above.
    tiny = out/'inventory-fixture'
    tiny.mkdir()
    (tiny/'input.csv').write_text('fixture\n')
    before = a.d.snapshot(tiny)
    (tiny/'input.csv').write_text('changed\n')
    assert a.d.snapshot(tiny) != before
    (tiny/'symlink').symlink_to(tiny/'input.csv')
    reject(lambda: a.d.snapshot(tiny))


def static_checks(out, manifest):
    s = a.s
    runs = [r for r in manifest['runs'] if r['N'] == 128]
    w = a.windows_for(runs[0])
    scalar = [(float(tm), {'q': float(tm)}) for tm in range(0, 40001, 40)]
    full = [(float(tm), {'q': float(tm)}) for tm in range(0, 40001, 4000)]
    assert s.window(scalar, 'q', 'early', w) == (4020., 200, 40., 8000.)
    assert s.window(full, 'q', 'early', w) == (6000., 2, 4000., 8000.)
    assert s.window(full, 'q', 'late', w) == (36000., 3, 32000., 40000.)
    # N64 defaults remain the reviewed schedules and statistical definitions.
    assert s.WINDOWS['late'] == (8000, 10000)
    np.testing.assert_allclose(s.stats([1., 2., 3.])['se'], 1/np.sqrt(3))
    assert s.stats([1., 1., 1.])['interval'] is None
    assert s.contrast([0., 0., 0.], [1., 1., 1.])['interval'] is None
    assert s.contrast([1., 2., 3.], [4., 5., 6.], .005)['interval'][0] < \
           s.contrast([1., 2., 3.], [4., 5., 6.])['interval'][0]
    for n in (32, 64, 128):
        law = s.canonical_population(chains=256, n=n, z=64*n)
        k = np.arange(n+2)
        np.testing.assert_allclose([sum(law['pmf']), np.dot(k, law['pmf']),
            np.dot((k-n/4)**2, law['pmf'])], [1, n/4, law['variance']])
        flexible = s.reference_targets(0, 128, n)
        np.testing.assert_allclose(flexible['re2'], n*flexible['mean_r2'])
        np.testing.assert_allclose(flexible['rg2'], flexible['mean_r2']*((n+1)**2-1)/(6*(n+1)))
    refs = s.references(128)
    assert refs['targets']['B']['connector_e4'] == 125/3
    assert refs['targets']['B']['population_mean'] == 32
    connectors = [dict(ex=np.sqrt(5), ey=0., ez=0., e2=5.) for _ in range(8192)]
    pop = [dict(z=32) for _ in range(256)]
    sites = [dict(spring=i if i%129 < 32 else -1) for i in range(256*129)]
    tangents = [dict(tangent8=.2, tangent16=.1) for _ in range(256)]
    context = s.context(connectors, pop, sites, tangents, 128)
    assert context['population_pmf_32'] == 1 and context['occupancy_128'] == 0
    connectors[0]['e2'] = 10
    reject(lambda: s.context(connectors, pop, sites, tangents, 128))
    # Streaming frames validate shape, finite values, labels and clock.
    path = out/'tiny.csv'
    header = ['step', 'time', 'chain', 'value']
    def write(rows):
        with path.open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(rows)
    good = [[0, 0, 0, 1], [0, 0, 1, 2], [100, .01, 0, 3], [100, .01, 1, 4]]
    write(good)
    assert len(list(s.frames(path, header, 2, 100, 100, 128))) == 2
    for bad in (good[:-1], good+[[200, .02, 0, 5]], [[0, 0, 0, 'nan']]+good[1:],
                [good[0], [0, 0, 0, 2]]+good[2:]):
        write(bad)
        reject(lambda: list(s.frames(path, header, 2, 100, 100, 128)))
    assert s.acf_diagnostic([str(tm) for tm, _ in full], [v['q'] for _, v in full], '4000')['tau_int'] is None
    # Exercise static table/plot plumbing with fabricated finite records only.
    data = {}
    for run in runs:
        def values(time, grid):
            keys = s.PRIMARY if grid == 'scalar' else ('tangent8', 'tangent16')
            if grid == 'full' and run['Z']:
                keys += ('connector_e2', 'connector_e4', 'population_variance')
            result = {k: float(refs['targets'][run['cell']][k])*(1+.001*run['replica'])+.000001*time for k in keys}
            if grid == 'full' and run['Z']:
                result.update({prefix+str(k): refs['targets'][run['cell']][prefix+str(k)]
                               for prefix, count in (('population_pmf_',130), ('occupancy_',129)) for k in range(count)})
            return result
        data[run['id']] = dict(scalar=[(tm, values(tm, 'scalar')) for tm in range(0,40001,40)],
            full=[(tm, values(tm, 'full')) for tm in range(0,40001,4000)],
            histogram=dict(probabilities=[1/33]*33, bins=[1]*33, histogram_max=4,
                           start=20000, end=40000, frames=501),
            events=[dict(start=tm-4000 if tm else 0, end=tm, counts={'attempts': 1 if tm else 0})
                    for tm in range(0,40001,4000)])
    target = out/'statics/n128'
    target.mkdir(parents=True)
    contrasts = s.tables(target, runs, data, refs, w)
    assert sum(r['primary'] for r in contrasts) == 10
    s.plots(target, data, refs)
    a.population_figures(target, runs, data, refs)
    a.static_length_comparison(out, {128:(runs, data)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=a.BASE/'regression')
    out = a.output_path(parser.parse_args().output)
    out.mkdir(parents=True, exist_ok=False)
    os.environ['MPLCONFIGDIR'] = str(out/'matplotlib-cache')
    reject(lambda: a.output_path(a.BASE))
    reject(lambda: a.output_path(a.BASE/'..'/'outside'))
    (out/'link').symlink_to(out, target_is_directory=True)
    reject(lambda: a.output_path(out/'link'/'child'))
    manifest = a.d.load(a.d.CONFIG/'manifest.json')
    authentication_checks(out, manifest)
    old = a.d.load(PROJECT/'e1_d2a4_config/manifest.json')
    a.comparison_context(manifest, old)
    bad = copy.deepcopy(old)
    bad['runs'][0]['seed'] = manifest['runs'][0]['seed']
    reject(lambda: a.comparison_context(manifest, bad))
    root = out/'synthetic-curves'
    cohorts = {}
    for n in (32, 64, 128):
        runs = ([dict(r, N=32, expected=old['expected']) for r in old['runs']] if n == 32 else
                [r for r in manifest['runs'] if r['N'] == n])
        for run in runs:
            path = root/'runs'/run['id']/'output/dynamics/replica_correlations.csv'
            synthetic_curves(path, run, n)
            assert curves(path, run, ['']) == run['expected']['exported_bins_per_chain']
        if n == 32:
            cells = a.d.read_replicas(root, old, a.d.N32_PROFILE)
            from e1_d2a3_run import QUANTITIES
            for cell, data in cells.items():
                data['runs'] = [r for r in runs if r['cell'] == cell]
                data['values'] = data['values'][:, :, [QUANTITIES.index(q) for q in ('cm_msd','bead16_msd','c1','c2')]]
        else:
            cells = a.d.read_cells(root, manifest, runs, n)
        cohorts[n] = cells
        target = out/f'dynamics/n{n}'
        target.mkdir(parents=True)
        windows, orientation = a.d.numerical_tables(target, cells, n)
        assert len(orientation) == 24 and all(np.isclose(r['slope_min'], 1) for r in windows)
        assert all(r['min_origins'] >= 32 and 5*r['end_lag_steps'] <= runs[0]['expected']['steps'] for r in windows)
        a.d.figures(target, cells, n)
        if n == 128:
            assert max(r['end_lag_steps'] for r in windows) == 78643200
            with (target/'bare_com.csv').open(newline='') as stream:
                assert all(np.isclose(float(r['ratio_mean']), 1.02) for r in csv.DictReader(stream))
            # Exact integer support survives a physical timestamp rounded above the endpoint.
            for data in cells.values():
                i = next(i for i,r in enumerate(data['rows']) if int(r['lag_steps']) == 78643200)
                data['time'][i] = np.nextafter(7864.32, np.inf)
            endpoint = out/'rounded-endpoint'
            endpoint.mkdir()
            ww, _ = a.d.numerical_tables(endpoint, cells, n)
            assert sum(r['end_lag_steps'] == 78643200 for r in ww) == 24
            for data in cells.values():
                data['time'] = np.array([float(r['lag_time']) for r in data['rows']])
    # Exercise actual malformed-grid rejection, without the authentication mocks.
    run = next(r for r in manifest['runs'] if r['N'] == 128)
    path = root/'runs'/run['id']/'output/dynamics/replica_correlations.csv'
    with path.open(newline='') as stream:
        bad_rows = list(csv.DictReader(stream))
    bad_path = out/'bad.csv'
    for key, value in (('origins_per_chain', '31'), ('c1', 'nan'), ('lag_steps', '1')):
        rows = copy.deepcopy(bad_rows)
        rows[20][key] = value
        with bad_path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=curve_header(128))
            writer.writeheader()
            writer.writerows(rows)
        reject(lambda: curves(bad_path, run, ['']))
    comparison = out/'comparison'
    comparison.mkdir()
    rows, ratios, common = a.comparison_tables(comparison, cohorts)
    assert common and all(np.isclose(r['ratio_of_means'], 1) for r in ratios)
    a.compare_figures(comparison, rows, ratios, common)
    a.slope_diffusion_figures(comparison, cohorts)
    a.secondary_tables(out/'dynamics/n128', root, manifest)
    static_checks(out, manifest)
    a.review(out)
    assert len(list(comparison.glob('comparison_*.png'))) == 6
    a.d.write_json(out/'PASS.json', dict(status='SYNTHETIC_CPU_CHECKS_PASSED_NOT_ACCEPTANCE',
        authentication_scope='Mocked inventory/JSON and physical validator; real closure logic and standalone CSV validators.'))
    print(out)


if __name__ == '__main__':
    main()
