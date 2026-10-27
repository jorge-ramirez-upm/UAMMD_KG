"""Prepared, UNEXECUTED CPU-only support/configuration/CSV regression checks.

No child process, GPU, trajectory generation, rheology or campaign execution.
Command: python3 -B examples/slip-springs/tests/d2a4_campaign_regression.py
"""
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e1_d2a3_run import HEADER, acquisition_expected, curves, exported_grid, load

PROJECT = Path(__file__).resolve().parents[1]


class LongCampaignSupport(unittest.TestCase):
    def setUp(self):
        self.manifest = load(PROJECT / 'e1_d2a4_config/manifest.json')
        self.e = self.manifest['expected']

    def test_partial_last_exported_level_and_primary_range(self):
        grid = exported_grid(self.e)
        self.assertEqual(len(grid), 116)
        self.assertEqual(grid[-4:], [(65536, 8192), (73728, 8192),
                                    (81920, 8192), (90112, 8192)])
        self.assertEqual([100001 // b - lag // b for lag, b in grid[-4:]], [4, 3, 2, 1])
        self.assertFalse(any(b == 16384 for lag, b in grid))
        primary = [(lag, b) for lag, b in grid if lag * 100 <= 10000000 // 5
                   and 100001 // b - lag // b >= 32]
        self.assertEqual(primary[-1], (18432, 2048))
        self.assertEqual(100001 // 2048 - 9, 39)

    def test_previous_default_and_second_coarsening_factor(self):
        old = acquisition_expected()
        self.assertEqual(len(exported_grid(old)), 88)
        self.assertEqual(exported_grid(old)[-1], (7680, 512))
        alternate = dict(self.e, dynamics_frames=1001, levels=7, slots=18, m=3)
        grid = exported_grid(alternate)
        self.assertEqual(len(grid), 60)
        self.assertEqual(grid[-1], (891, 81))
        self.assertEqual(exported_grid(dict(self.e, dynamics_frames=18))[-1], (16, 2))

    def test_frozen_matrix_schedules_and_stress_off(self):
        runs = self.manifest['runs']
        self.assertEqual([r['id'] for r in runs], [f'{c}-r{i}' for c in 'ABCD' for i in (1, 2, 3)])
        self.assertEqual(len({r['seed'] for r in runs}), 12)
        self.assertEqual(len({r['replica_id'] for r in runs}), 12)
        for r in runs:
            options = dict(zip(r['argv'][1::2], r['argv'][2::2]))
            for name, value in {'--stress-mode': 'off', '--steps': '10000000',
                                '--sample': '5000', '--dynamics-levels': '15',
                                '--dynamics-stride': '100', '--dynamics-mib': '256'}.items():
                self.assertEqual(options[name], value)
            self.assertEqual((r['kappa'], r['Z']),
                             {'A': (0, 0), 'B': (0, 2048), 'C': (10, 0), 'D': (10, 2048)}[r['cell']])
        config = PROJECT / 'e1_d2a4_config'
        self.assertEqual(list(map(int, (config / 'equilibrium.steps').read_text().split())),
                         list(range(0, 10000001, 1000000)))
        self.assertEqual((config / 'snapshots.steps').read_text().split(), ['0', '10000000'])

    def test_prescribed_csv_support_and_bad_tail_rejection(self):
        # Independent floor-count definition; only 116 synthetic correlation records.
        rows = []
        for k in range(14):
            b = 2**k
            for ell in range(0 if k == 0 else 8, min(16, 100001 // b)):
                lag = ell * b
                row = dict.fromkeys(HEADER, 0)
                row.update(replica=732404101, chain='0', lag_samples=lag, lag_steps=lag * 100,
                           lag_time=(lag * 100) * .0001, origins_per_chain=100001 // b - ell,
                           decimation_samples=b, diffusion_phase_samples=b - 1,
                           orientation_block_samples=b, orientation_block_duration=(b * 100) * .0001)
                rows.append(row)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic_support.csv'
            def write():
                with path.open('w', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=HEADER)
                    w.writeheader()
                    w.writerows(rows)
            write()
            self.assertEqual(curves(path, 732404101, ['0'], self.e), 116)
            for key, value in [('origins_per_chain', 2), ('lag_steps', 9011201), ('cm_msd', 'nan')]:
                original = rows[-1][key]
                rows[-1][key] = value
                write()
                with self.assertRaises(ValueError):
                    curves(path, 732404101, ['0'], self.e)
                rows[-1][key] = original
            rows.pop()
            write()
            with self.assertRaises(ValueError):
                curves(path, 732404101, ['0'], self.e)


if __name__ == '__main__':
    unittest.main()
