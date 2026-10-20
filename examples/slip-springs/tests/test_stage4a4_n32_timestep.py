import contextlib
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_stage4a4_n32_timestep as runner
import stage4a4_n32_timestep_analysis as analysis


class N32Test(unittest.TestCase):
    def test_plan_has_four_equal_duration_cases(self):
        cases = runner.cases(Path('/evidence'), Path('/simulator'))
        self.assertEqual([(c['kappa'], c['steps']) for c in cases], [(0, 800000), (0, 40000), (10, 800000), (10, 40000)])
        for case in cases:
            self.assertEqual(case['dt']*case['steps'], 20.)
            self.assertAlmostEqual(case['dt']*case['sample'], .01)
            options = dict(zip(case['argv'][1::2], case['argv'][2::2]))
            self.assertEqual(options['--corr-levels'], '24')
            self.assertEqual(options['--stress-mode'], 'every-step')
            self.assertEqual(options['--cpu-workers'], '8')
            self.assertEqual(options['--scalar-output'], 'full')
        self.assertEqual(sum(c['timeout_seconds'] for c in cases), 4200)

    def test_default_preflight_never_starts_a_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'fresh'
            with patch.object(sys, 'argv', ['runner', '--root', str(root)]), \
                    patch.object(runner, 'identity', return_value=runner.START), \
                    patch.object(runner, 'git', return_value='origin'), \
                    patch.object(runner, 'digest', return_value=runner.EXECUTABLE_SHA), \
                    patch.object(subprocess, 'Popen') as start, contextlib.redirect_stdout(io.StringIO()):
                runner.main()
            start.assert_not_called()
            self.assertEqual(len(list((root/'commands').glob('*.cmd'))), 4)
            self.assertEqual(json.loads((root/'receipts/preflight.json').read_text())['mode'], 'preflight')
            with patch.object(sys, 'argv', ['runner', '--root', str(root)]), \
                    patch.object(runner, 'identity', return_value=runner.START):
                with self.assertRaises(FileExistsError): runner.main()

    def test_identity_rejects_unexpected_binary_and_dirty_protected_checkout(self):
        def git(directory, *args):
            if args[0] == 'branch': return 'slip-springs'
            if args[0] == 'remote': return 'git@github.com:jorge-ramirez-upm/UAMMD_KG.git'
            if args[0] == 'status': return ''
            return runner.PIN
        with patch.object(Path, 'cwd', return_value=runner.DEVELOPMENT), \
                patch.object(runner, 'git', side_effect=git), patch.object(subprocess, 'run'), \
                patch.object(runner.os, 'access', return_value=True), patch.object(runner, 'digest', return_value='bad'):
            with self.assertRaisesRegex(ValueError, 'SHA-256'): runner.identity(Path('/binary'), runner.EXECUTABLE_SHA)
        def dirty(directory, *args):
            if directory == runner.PROTECTED[1] and args[0] == 'status': return ' M file'
            return git(directory, *args)
        with patch.object(Path, 'cwd', return_value=runner.DEVELOPMENT), \
                patch.object(runner, 'git', side_effect=dirty), patch.object(subprocess, 'run'):
            with self.assertRaisesRegex(ValueError, 'dirty'): runner.identity(Path('/binary'), runner.EXECUTABLE_SHA)

    def test_timeout_and_failure_preserve_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('logs', 'receipts'): (root/name).mkdir()
            with self.assertRaises(subprocess.TimeoutExpired):
                runner.timed(root, 'timeout', [sys.executable, '-c', 'import time; time.sleep(20)'], .05)
            receipt = json.loads((root/'receipts/timeout.json').read_text())
            self.assertEqual(receipt['status'], 'timeout')
            self.assertEqual(receipt['restart'], 'unsupported')
            with self.assertRaises(RuntimeError): runner.timed(root, 'failure', [sys.executable, '-c', 'raise SystemExit(7)'], 5)
            self.assertEqual(json.loads((root/'receipts/failure.json').read_text())['exit_code'], 7)

    def test_exact_lag_rule_keeps_nearest_bin_diagnostics_unresolved(self):
        def data(spacing, middle):
            rows = []
            for lag, h in ((0., 10.), (.01, 8.), (middle, 5.), (.1 if spacing == .0005 else .0992, 2.)):
                row = dict(lag_time=lag, H=h, H_se=.001, block_samples=128, pairs_per_chain=100)
                for key in analysis.dynamic.CHANNELS: row.update({key: h/0.7, key+'_se': .001})
                rows.append(row)
            return dict(metadata=dict(spacing=spacing), rows=rows)
        result = analysis.dynamics(data(.000025, .0496), data(.0005, .05))
        self.assertEqual(result['lags'][0]['gate'], 'pass')
        self.assertEqual([x['gate'] for x in result['lags'][1:]], ['unresolved', 'unresolved'])
        self.assertIn('no approved amplitude threshold', result['h0']['decision'])

    def test_execution_stops_after_first_failed_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'fresh'
            calls = []
            def timed(root, tag, argv, limit):
                calls.append(tag)
                if 'dt' in tag: raise RuntimeError('synthetic GPU failure; no simulator launched')
            with patch.object(sys, 'argv', ['runner', '--execute-n32', '--root', str(root)]), \
                    patch.object(runner, 'identity', return_value=runner.START), \
                    patch.object(runner, 'git', return_value='origin'), \
                    patch.object(runner, 'digest', return_value=runner.EXECUTABLE_SHA), \
                    patch.object(runner, 'timed', side_effect=timed), \
                    patch.object(subprocess, 'run'), \
                    patch.object(subprocess, 'check_output', return_value='release 13.0'), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'synthetic GPU failure'): runner.main()
            self.assertEqual(calls, ['N32-k0-reference', 'N32-k10-reference', 'N32-k0-dt.000025'])

    def test_histogram_three_se_gate_includes_reference_uncertainty(self):
        with tempfile.TemporaryDirectory() as tmp:
            reference = Path(tmp)/'ref.json'
            reference.write_text(json.dumps({'histogram': {'se': [.001]*32}}))
            measured = dict(total_variation=.001, chain_se=[0.]*33, difference=[0.]*33)
            with patch.object(analysis, 'histogram', return_value=measured):
                result = analysis.distributions(Path(tmp), reference)
            self.assertEqual(result['total_variation_gate']['decision'], 'unresolved')
            self.assertEqual(result['bin_gates'][-1]['tolerance'], .005)

    def test_three_se_decisions_and_missing_diagnostics(self):
        self.assertEqual(analysis.decision(.001, .001, .01)['decision'], 'pass')
        self.assertEqual(analysis.decision(.02, .001, .01)['decision'], 'fail')
        self.assertEqual(analysis.decision(.009, .001, .01)['decision'], 'unresolved')
        self.assertTrue(any('energies' in x for x in analysis.UNAVAILABLE))
        self.assertTrue(any('full contour' in x for x in analysis.UNAVAILABLE))

    def test_histogram_contract_and_malformed_files(self):
        fields = ['chain', 'bond', 'frames', 'mean_r', 'mean_r2'] + [f'bin{i}' for i in range(33)]
        base = dict(frames=1001, mean_r=1., mean_r2=1., **{f'bin{i}': 1001 if i == 0 else 0 for i in range(33)})
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            def fixture(change=None, missing=False, duplicate=False):
                with (directory/'bond_statistics.csv').open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    for chain in range(512):
                        for bond in range(32):
                            if missing and (chain, bond) == (511, 31): continue
                            row = dict(base, chain=chain, bond=bond)
                            if change and (chain, bond) == (0, 0): row.update(change)
                            writer.writerow(row)
                    if duplicate: writer.writerow(dict(base, chain=0, bond=0))
            reference = directory/'reference.json'
            reference.write_text(json.dumps({'springs': 32, 'histogram': {
                'probability': [1.] + [0.]*31, 'se': [0.]*32}}))
            for steps, sample in ((800000, 400), (40000, 20)):
                fixture()
                analysis.validate_bond_histogram(directory, dict(steps=steps, sample=sample))
                result = analysis.distributions(directory, reference)
                self.assertEqual(result['frames_per_bond'], 1001)
                self.assertEqual(result['probability'], [1.] + [0.]*32)
                self.assertEqual(result['total_variation_gate']['decision'], 'pass')
                self.assertIn('10 <= t <= 20', result['scope'])
            for change in ({'frames': 2001, 'bin0': 2001}, {'frames': 1000}, {'frames': 1002},
                           {'bin0': 1000}, {'bin0': 1002}, {'bin0': 1002, 'bin1': -1},
                           {'bin1': '0.5'}, {'bin0': 'nan'}, {'bin0': 'inf'}, {'mean_r': 'nan'}, {'mean_r2': 'inf'},
                           {'chain': 512}, {'chain': -1}, {'bond': 32}, {'bond': -1}):
                with self.subTest(change=change):
                    fixture(change)
                    with self.assertRaises(ValueError):
                        analysis.validate_bond_histogram(directory, dict(steps=800000, sample=400))
            for options in ({'missing': True}, {'duplicate': True}):
                with self.subTest(options=options):
                    fixture(**options)
                    with self.assertRaises(ValueError):
                        analysis.validate_bond_histogram(directory, dict(steps=40000, sample=20))

    def test_truncated_trajectory_cannot_enter_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = dict(springs=32, chains=512, precision_bits=64, seed=433201,
                        steps=800000, sample=400, dt=.000025, production_time=20.,
                        kbt=1., zeta=1., initialization_method='CPU-direct-equilibrium')
            (root/'metadata.json').write_text(json.dumps(meta))
            (root/'parameters.txt').write_text(' '.join(map(str, [32]+[1, 30]*32+[0]*33)))
            (root/'samples.csv').write_text('step,time,chain,min_length\n0,0,0,1\n')
            with self.assertRaisesRegex(ValueError, 'incomplete scalar'): analysis.validate(root, .000025, {'kappa': 0})
            (root/'samples.csv').write_text('step,time,chain,min_length\n0,0,0,nan\n')
            with self.assertRaisesRegex(ValueError, 'nonfinite'): analysis.validate(root, .000025, {'kappa': 0})


if __name__ == '__main__': unittest.main()
