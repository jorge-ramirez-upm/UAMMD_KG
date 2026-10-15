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

    def test_performance_timers(self):
        with tempfile.TemporaryDirectory(prefix='rouse-timing-') as tmp:
            for steps, equil in ((0,0), (0,3), (7,3)):
                output = Path(tmp)/f's{steps}_e{equil}'
                process = subprocess.run([BINARY, '--springs', '1', '--chains', '16',
                                          '--steps', str(steps), '--equil', str(equil),
                                          '--sample', '2', '--seed', '20261015', '--output', output],
                                         check=True, capture_output=True, text=True)
                meta = json.loads((output/'metadata.json').read_text())
                self.assertEqual(meta['timing_schema_version'], 2)
                self.assertEqual(meta['beads_per_chain'], 2)
                self.assertEqual(meta['physical_time'], steps*meta['dt'])
                self.assertEqual(meta['wall_seconds'], meta['production_seconds'])
                self.assertGreaterEqual(meta['production_seconds'], meta['sampling_seconds']+meta['recurrent_output_seconds'])
                self.assertAlmostEqual(meta['output_seconds'], meta['recurrent_output_seconds']+meta['final_output_seconds'])
                for field in ('initialization_seconds','production_seconds','sampling_seconds','final_output_seconds'):
                    self.assertGreater(meta[field], 0)
                self.assertEqual(meta['equilibration_gpu_seconds']>0, equil>0)
                self.assertTrue(meta['gpu_timing_includes_launch_gaps'])
                self.assertFalse(meta['gpu_timing_includes_sampling'])
                self.assertFalse(meta['gpu_timing_includes_host_sync_wait'])
                self.assertIn('Performance: chains=16 springs/chain=1 beads/chain=2 total_beads=32', process.stderr)
                if steps:
                    updates = 32*steps
                    self.assertAlmostEqual(meta['integration_ns_per_bead_step'], 1e9*meta['update_seconds']/updates)
                    self.assertAlmostEqual(meta['overall_ns_per_bead_step'], 1e9*meta['production_seconds']/updates)
                    self.assertAlmostEqual(meta['bead_updates_per_second'], updates/meta['update_seconds'])
                else:
                    self.assertEqual(meta['update_seconds'], 0)
                    for field in ('integration_ns_per_bead_step','overall_ns_per_bead_step','bead_updates_per_second'):
                        self.assertIsNone(meta[field])
                    self.assertIn('N/A', process.stderr)

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
