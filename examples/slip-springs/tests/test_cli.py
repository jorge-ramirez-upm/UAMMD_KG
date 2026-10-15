"""Small runtime/CLI contract tests, with all artifacts in a temporary directory."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BINARY = Path(sys.argv.pop(1)).resolve()
PROJECT = Path(__file__).resolve().parents[1]

class CliTests(unittest.TestCase):
    def test_replay_sampling_equil_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='rouse-cli-') as tmp:
            paths = [Path(tmp)/name for name in ('a', 'b')]
            for path in paths:
                subprocess.run([BINARY, '--springs', '1', '--chains', '16', '--steps', '7',
                                '--equil', '3', '--sample', '2', '--seed', str(2**64-1),
                                '--output', path], check=True, capture_output=True)
            self.assertEqual((paths[0]/'samples.csv').read_bytes(), (paths[1]/'samples.csv').read_bytes())
            meta = json.loads((paths[0]/'metadata.json').read_text())
            self.assertEqual(meta['equil'], 3)
            self.assertEqual(meta['seed'], 2**64-1)
            import csv
            with (paths[0]/'samples.csv').open() as f:
                rows = list(csv.DictReader(f))
            self.assertEqual([int(r['step']) for r in rows[::16]], [0, 2, 4, 6, 7])
            before = (paths[0]/'samples.csv').read_bytes()
            p = subprocess.run([BINARY, '--output', paths[0]], capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual((paths[0]/'samples.csv').read_bytes(), before)

    def test_invalid_arguments_and_isolation(self):
        with tempfile.TemporaryDirectory(prefix='rouse-invalid-') as tmp:
            output = Path(tmp)/'unused'
            for args in (['--springs', '0'], ['--springs', '-1'], ['--chains', '0'],
                         ['--dt', 'nan'], ['--dt', '0'], ['--dt', '1'], ['--dt', '0.1x'],
                         ['--sample', '0'], ['--steps', str(2**61)],
                         ['--steps', str(2**61-1), '--equil', '1'],
                         ['--seed', str(2**64)], ['--springs', str(2**31)],
                         ['--unknown', '1'], ['--steps']):
                # Missing-value test must leave its option at the end.
                p = subprocess.run([BINARY, '--output', output, *args], capture_output=True)
                self.assertNotEqual(p.returncode, 0, args)
                self.assertFalse(output.exists(), args)
            forbidden = PROJECT.parent/'stage1-forbidden-test'
            self.assertFalse(forbidden.exists())
            p = subprocess.run([BINARY, '--output', forbidden], capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertFalse(forbidden.exists())

if __name__ == '__main__':
    unittest.main()
