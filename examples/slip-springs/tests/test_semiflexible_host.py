"""Bounded tests for campaign generation and streaming host analysis."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import semiflexible_host as host

BINARY = Path(sys.argv.pop(1)).resolve()


class HostTools(unittest.TestCase):
    def test_generation_is_dry_and_frozen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'campaign'
            with contextlib.redirect_stdout(io.StringIO()):
                manifest = host.generate(root, BINARY.parent.parent)
            self.assertEqual(len(manifest), 204)
            self.assertEqual(len(list(root.glob('*/metadata.json'))), 0)
            self.assertTrue(all(r['command'][0].endswith('/semiflexible') for r in manifest))
            self.assertEqual(set(r['seed'] for r in manifest if 'seed' in r), set(host.SEEDS))
            with self.assertRaises(FileExistsError):
                host.generate(root, BINARY.parent.parent)

    def test_streaming_analysis_on_short_real_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = host.Chain.homogeneous(1, kappa=0)
            params = root/'p.txt'
            host.parameters(params, model)
            manifest = []
            for h in (0.0002, 0.0001, 0.00005):
                output = root/str(h)
                command = [str(BINARY), '--springs', '1', '--chains', '128', '--dt', str(h),
                           '--steps', str(round(0.002/h)), '--sample', str(round(0.001/h)),
                           '--parameters', str(params), '--output', str(output)]
                subprocess.run(command, check=True, capture_output=True, timeout=60)
                manifest.append(dict(label='smoke', precision='test', seed=42001, dt=h, duration=0.002,
                                     chains=128, b0=model.b0.tolist(), kb=model.kb.tolist(),
                                     kappa=model.kappa.tolist(), output=str(output)))
            gaussian = host.Chain.homogeneous(2, b0=0, kb=3, kappa=0)
            params = root/'gaussian.txt'
            host.parameters(params, gaussian)
            for h in (0.001, 0.0005, 0.00025):
                output = root/f'gaussian-{h}'
                command = [str(BINARY), '--springs', '2', '--chains', '128', '--dt', str(h),
                           '--steps', str(round(0.002/h)), '--sample', str(round(0.001/h)),
                           '--parameters', str(params), '--output', str(output)]
                subprocess.run(command, check=True, capture_output=True, timeout=60)
                manifest.append(dict(label='gaussian', precision='test', seed=42001, dt=h, duration=0.002,
                                     chains=128, b0=gaussian.b0.tolist(), kb=gaussian.kb.tolist(),
                                     kappa=gaussian.kappa.tolist(), output=str(output)))
            (root/'manifest.json').write_text(json.dumps(manifest))
            with contextlib.redirect_stdout(io.StringIO()):
                failed = host.analyze(root)
            report = json.loads((root/'analysis.json').read_text())
            self.assertEqual(len(report['summaries']), 6)
            self.assertEqual(failed, bool(report['failures']))
            # Deliberate corruption must trigger a mean acceptance failure.
            (root/'analysis.json').unlink()
            file = Path(manifest[2]['output'])/'bond_statistics.csv'
            import csv
            with file.open() as f:
                reader = csv.DictReader(f)
                fields, rows = reader.fieldnames, list(reader)
            for row in rows:
                row['mean_r'] = '1000'
            with file.open('w') as f:
                writer = csv.DictWriter(f, fields)
                writer.writeheader()
                writer.writerows(rows)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(host.analyze(root))
            report = json.loads((root/'analysis.json').read_text())
            self.assertTrue(any('final-half radial means' in s for s in report['failures']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
