#!/usr/bin/env python3
"""Synthetic CPU specifications only. Execution requires separate authorization."""
import argparse
import csv
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import e1_d2a5_n64_statics as s
import numpy as np


def reject(action):
    try:
        action()
    except (ValueError, KeyError, AssertionError, FileNotFoundError):
        return
    raise AssertionError('invalid input accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=s.BASE/'regression')
    out = s.output_path(parser.parse_args().output)
    out.mkdir(parents=True, exist_ok=False)
    reject(lambda: s.output_path(s.BASE))
    reject(lambda: s.output_path(s.BASE/'..'/'outside'))
    reject(lambda: s.output_path(s.auth.EVIDENCE/'statics'))
    reject(lambda: s.output_path(s.auth.OUTPUT/'statics'))
    (out/'link').symlink_to(out, target_is_directory=True)
    reject(lambda: s.output_path(out/'link'/'child'))

    # Exact R3 reduction, small-R t interval, zero-variance rejection and LOO.
    x = s.stats([1., 2., 3.])
    np.testing.assert_allclose([x['mean'], x['se']], [2., 1/np.sqrt(3)])
    np.testing.assert_allclose(x['loo'], [2.5, 2., 1.5])
    np.testing.assert_allclose(x['interval'], [2-4.302652729911275/np.sqrt(3), 2+4.302652729911275/np.sqrt(3)])
    assert s.stats([1., 1., 1.])['interval'] is None
    assert s.stats([0., 0., 0.], bounded=(0., 1.))['interval'][1] > 0
    reject(lambda: s.stats([1., 2.]))
    reject(lambda: s.stats([1., 2., float('nan')]))
    c = s.contrast([1., 2., 3.], [4., 5., 6.])
    np.testing.assert_allclose([c['difference'], c['se'], c['df']], [3., np.sqrt(2/3), 4.])
    assert len(c['loo']) == 9
    assert s.contrast([0., 0., 0.], [1., 1., 1.])['interval'] is None
    assert s.contrast([1., 2., 3.], [4., 5., 6.], .005)['interval'][0] < c['interval'][0]

    scalar = [(float(tm), {'q': float(tm)}) for tm in range(0, 10001, 10)]
    full = [(float(tm), {'q': float(tm)}) for tm in range(0, 10001, 1000)]
    assert s.window(scalar, 'q', 'early') == (1005., 200, 10., 2000.)
    assert s.window(full, 'q', 'early') == (1500., 2, 1000., 2000.)
    assert s.window(full, 'q', 'late') == (9000., 3, 8000., 10000.)
    assert s.window(scalar, 'q', 'initial') == (0., 1, 0., 0.)
    assert s.window(scalar, 'q', 'late')[0]-s.window(scalar, 'q', 'early')[0] == 7995.
    reject(lambda: s.window(full, 'absent', 'late'))
    reject(lambda: s.window([], 'q', 'late'))
    reject(lambda: s.acf_diagnostic(['0', '10', '30'], [1., 2., 1.], '10'))
    assert s.acf_diagnostic([str(tm) for tm, _ in full], [v['q'] for _, v in full], '1000')['tau_int'] is None

    rows = [{key: float(i+1) for key in ('re2', 'rg2', 'mean_r', 'mean_r2', 'tangent1', 'tangent2', 'tangent3', 'tangent4')}
            for i in range(256)]
    b = s.backbone(rows)
    values = np.arange(1., 257.)
    np.testing.assert_allclose([b['re2'], b['spatial_var_re2'], b['raw_re4'], b['spatial_cov_re2_rg2']],
                               [values.mean(), values.var(ddof=1), np.mean(values**2), values.var(ddof=1)])
    reject(lambda: s.backbone(rows[:-1]))
    connectors = [{'ex': np.sqrt(5), 'ey': 0., 'ez': 0., 'e2': 5.} for _ in range(4096)]
    pop = [{'z': 16} for _ in range(256)]
    sites = [{'spring': i if i%65 < 16 else -1} for i in range(256*65)]
    tangents = [{'tangent8': .2, 'tangent16': .1} for _ in range(256)]
    context = s.context(connectors, pop, sites, tangents)
    np.testing.assert_allclose([context['connector_e2'], context['connector_e4'], context['population_pmf_16']], [5., 25., 1.])
    assert context['population_mean'] == 16 and context['population_variance'] == 0
    assert context['occupancy_0'] == 1 and context['occupancy_64'] == 0
    connectors[0]['e2'] = 10.
    reject(lambda: s.context(connectors, pop, sites, tangents))
    law = s.canonical_population(chains=256, n=64, z=4096)
    np.testing.assert_allclose(sum(law['pmf']), 1.)
    np.testing.assert_allclose(np.dot(np.arange(66), law['pmf']), 16.)
    np.testing.assert_allclose(np.dot((np.arange(66)-16)**2, law['pmf']), law['variance'])

    # Tiny streaming schema/clock/label fixtures: no scientific inputs.
    path = out/'tiny.csv'
    columns = ['step', 'time', 'chain', 'value']
    def write(rows, header=columns):
        with path.open('w', newline='') as stream:
            w = csv.writer(stream)
            w.writerow(header)
            w.writerows(rows)
    good = [[0, 0, 0, 1], [0, 0, 1, 2], [100, .01, 0, 3], [100, .01, 1, 4]]
    write(good)
    assert len(list(s.frames(path, columns, 2, 100, 100))) == 2
    write(good[:-1])
    reject(lambda: list(s.frames(path, columns, 2, 100, 100)))
    write(good+[[200, .02, 0, 5]])
    reject(lambda: list(s.frames(path, columns, 2, 100, 100)))
    write([[0, 0, 0, 'nan']]+good[1:])
    reject(lambda: list(s.frames(path, columns, 2, 100, 100)))
    write(good, ['step', 'time', 'chain', 'unavailable'])
    reject(lambda: list(s.frames(path, columns, 2, 100, 100)))
    write([good[0], [0, 0, 0, 2]]+good[2:])
    reject(lambda: list(s.frames(path, columns, 2, 100, 100)))

    # Existing authenticator's explicit-cohort inventory must ignore an inaccessible N128 sibling.
    root = out/'synthetic-campaign'
    root.mkdir()
    (root/'immutable.json').write_text('{}')
    for identity in s.auth.IDS:
        directory = root/'runs'/identity
        directory.mkdir(parents=True)
        (directory/'tiny.csv').write_text('fixture\n')
    (root/'runs'/'n128-A-r1').symlink_to(out/'absent-active', target_is_directory=True)
    before = s.auth.selected_inventory(root, ['immutable.json'])
    assert len(before['files']) == 13 and all('n128' not in name for name in before['files'])
    (root/'summary.json').write_text('{"mutable":true}')
    assert s.auth.selected_inventory(root, ['immutable.json']) == before
    target = root/'runs'/s.auth.IDS[0]/'tiny.csv'
    target.write_text('changed\n')
    assert s.auth.selected_inventory(root, ['immutable.json']) != before
    s.auth.write_json(out/'PASS.json', dict(status='SYNTHETIC_CPU_CHECKS_PASSED_NOT_SCIENTIFIC_ACCEPTANCE'))


if __name__ == '__main__':
    main()
