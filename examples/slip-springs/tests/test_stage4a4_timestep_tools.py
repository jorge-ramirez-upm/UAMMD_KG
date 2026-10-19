import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests'))
import stage4a4_equilibrium_reference as reference
import stage4a4_timestep_analysis as analysis
import stage4a4_static_drift_analysis as drift
import stage4a4_dynamic_timestep_analysis as dynamics


class Stage4A4ToolsTest(unittest.TestCase):
    def test_exact_reference_has_required_observables_and_zero_bend(self):
        result = reference.reference(8, 0, 512, 7, chunk=64)
        self.assertEqual(result['method'], 'exact-independent-equilibrium-sampling')
        self.assertLess(result['observables']['bend_energy']['mean'], 1e-14)
        self.assertEqual(len(result['histogram']['probability']), 32)
        self.assertAlmostEqual(sum(result['histogram']['probability']), 1., places=12)
        self.assertIn('1', result['orientation_correlation'])

    def test_reference_cli_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = pathlib.Path(tmp)/'reference.json'
            subprocess.run([sys.executable, str(ROOT/'tests/stage4a4_equilibrium_reference.py'), '--springs', '8', '--kappa', '10', '--chains', '256', '--seed', '9', '--report', str(report)], check=True)
            result = json.loads(report.read_text())
            self.assertEqual((result['springs'], result['kappa'], result['chains']), (8, 10., 256))

    def test_runner_is_preflight_by_default_and_bounded(self):
        script = ROOT/'tests/run_stage4a4_timestep_screen.sh'
        subprocess.run(['bash', '-n', str(script)], check=True)
        source = script.read_text()
        self.assertIn('limit_seconds=900', source)
        self.assertIn('--execute-first-screen', source)
        self.assertIn('--stress-mode every-step', source)
        self.assertIn('--scalar-output full', source)
        self.assertIn('run_case 0 .000025 400', source)
        self.assertIn('run_case 10 .001 10', source)
        self.assertIn('if [[ "$execute" != true ]]', source)

    def test_static_analysis_uses_chain_clusters_and_tangent_scale(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)/'run'; directory.mkdir()
            ref = reference.reference(8, 0, 65536, 7, chunk=256)
            ref_path = pathlib.Path(tmp)/'reference.json'; ref_path.write_text(json.dumps(ref))
            (directory/'metadata.json').write_text(json.dumps({'springs': 8, 'chains': 512, 'dt': .001,
                'steps': 20000, 'production_time': 20.}))
            values = {key: item['mean'] for key, item in ref['observables'].items()}
            tangent = {str(k): item['mean'] for k, item in ref['orientation_correlation'].items()}
            header = 'step,time,chain,mean_r,mean_r2,re2,rg2,tangent1,tangent2,tangent3,tangent4\n'
            with (directory/'samples.csv').open('w') as out:
                out.write(header)
                for time in (10., 20.):
                    for chain in range(512):
                        out.write(f"0,{time},{chain},{values['mean_r']},{values['mean_r2']},{values['re2']},{values['rg2']},{tangent['1']},{tangent['2']},{tangent['3']},{tangent['4']}\n")
            (directory/'parameters.txt').write_text('8\n' + '1 30\n'*8 + '0\n'*9)
            result = analysis.analyze(directory, ref_path)
            self.assertEqual(result['static_screen'], 'pass-provisional')
            self.assertEqual(result['run']['second_half_frames_per_chain'], 2)

    def test_drift_analysis_omits_midpoint_and_uses_conservative_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp); ref = reference.reference(8, 0, 65536, 3, chunk=256)
            ref_path = root/'reference.json'; ref_path.write_text(json.dumps(ref))
            values = {key: item['mean'] for key, item in ref['observables'].items()}
            tangent = {key: item['mean'] for key, item in ref['orientation_correlation'].items()}
            def fixture(name, dt, shift):
                directory = root/name; directory.mkdir()
                (directory/'metadata.json').write_text(json.dumps({'springs': 8, 'chains': 512, 'dt': dt,
                    'steps': 20000, 'production_time': 20., 'seed': 9}))
                (directory/'initial.csv').write_text('identical initial coordinates\n')
                with (directory/'samples.csv').open('w') as out:
                    out.write('step,time,chain,mean_r,mean_r2,re2,rg2,tangent1,tangent2,tangent3,tangent4\n')
                    for time in (0., 10., 20.):
                        for chain in range(512):
                            out.write(f"0,{time},{chain},{values['mean_r']+shift},{values['mean_r2']},{values['re2']},{values['rg2']},{tangent['1']},{tangent['2']},{tangent['3']},{tangent['4']}\n")
                return directory
            small, large = fixture('small', .000025, 0.), fixture('large', .001, .001)
            a, b = drift.run(small, ref_path), drift.run(large, ref_path)
            result = drift.compare(a, b)
            self.assertEqual((a['first_frames_per_chain'], a['second_frames_per_chain']), (1, 1))
            self.assertTrue(result['same_initial_coordinates'])
            self.assertIn('conservative unpaired', result['method'])
            self.assertAlmostEqual(result['observables']['mean_r']['large_minus_small'], .001)

    def test_dynamic_analysis_checks_six_channel_h_and_unpaired_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            def fixture(name, spacing, offset):
                directory = root/name; directory.mkdir()
                (directory/'stress_metadata.json').write_text(json.dumps({'mode': 'every-step', 'spacing': spacing}))
                header = ['lag_time', 'H', 'H_se', 'block_samples', 'pairs_per_chain']
                for key in dynamics.CHANNELS: header.extend((key, key+'_se'))
                with (directory/'stress_correlations.csv').open('w') as out:
                    out.write(','.join(header)+'\n')
                    for time, h in ((0, 7+offset), (.01, 5+offset), (.05, 3+offset), (.1, 2+offset), (.2, 1+offset)):
                        values = [time, h, .01, max(1, round(time/spacing)), 100]
                        for key in dynamics.CHANNELS: values.extend((h/.7, .01/.7))
                        out.write(','.join(map(str, values))+'\n')
                return directory
            small, large = fixture('small', .001, 0), fixture('large', .002, .01)
            result = dynamics.compare(dynamics.load(small), dynamics.load(large))
            self.assertEqual(len(result['lags']), 3)
            self.assertEqual(result['lags'][0]['gate'], 'pass')
            self.assertIn('Cxy', result['h0']['channels'])
            self.assertIn(result['crossing']['gate'], ('pass', 'unresolved'))


if __name__ == '__main__': unittest.main()
