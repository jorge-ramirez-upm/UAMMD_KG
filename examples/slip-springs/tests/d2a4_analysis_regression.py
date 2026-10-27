"""Prepared, UNEXECUTED CPU checks; analytical stencils and disposable CSV records.

No original evidence, scientific curves, figures, GPU or child processes used.
Command: python3 -B examples/slip-springs/tests/d2a4_analysis_regression.py
"""
import csv
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e1_d2a3_analyze import (D3_PROFILE, QUANTITIES, SUPPORT, local_slopes, mean_se,
                            read_replicas, support_region)
from e1_d2a4_analyze import PROFILE, alignment_key


class ThreeReplicaAnalysis(unittest.TestCase):
    def test_three_run_mean_and_standard_error(self):
        mean, se = mean_se(np.array([[1., 2.], [2., 4.], [3., 6.]]))
        np.testing.assert_allclose(mean, [2., 4.], rtol=1e-14)
        np.testing.assert_allclose(se, np.array([1., 2.]) / np.sqrt(3), rtol=1e-14)
        mean2, se2 = mean_se(np.array([[1., 3.], [3., 7.]]))
        np.testing.assert_allclose(mean2, [2., 5.], rtol=1e-14)
        np.testing.assert_allclose(se2, [1., 2.], rtol=1e-14)

    def test_integer_primary_boundaries_and_previous_profile(self):
        self.assertEqual(support_region(18432, 39, PROFILE), 'coarse_primary')
        self.assertEqual(support_region(20480, 38, PROFILE), 'weak_tail')
        self.assertEqual(support_region(18432, 31, PROFILE), 'weak_tail')
        self.assertEqual(support_region(1920, 63, D3_PROFILE), 'coarse_primary')
        self.assertEqual(support_region(2048, 31, D3_PROFILE), 'weak_tail')

    def test_three_replica_stencil_keeps_individual_failures(self):
        times = np.array([1., 2., 3.])
        log_t = np.log(times)
        values = np.array([np.exp(log_t**2), np.exp(2 * log_t**2), np.ones(3)])
        values[2, 0] = 0
        alpha, reasons = local_slopes(times, values, np.array([1, 1, 1]), ['fine'] * 3)
        np.testing.assert_allclose(alpha[:2, 1], [2 * np.log(2), 4 * np.log(2)], rtol=1e-13)
        self.assertTrue(np.isnan(alpha[2, 1]))
        self.assertEqual(reasons[1], ['available_same_level_stencil'] * 2 + ['logarithm_undefined'])
        a, r = local_slopes(times, np.ones((3, 3)), np.array([1, 2, 2]), ['fine'] * 3)
        self.assertTrue(np.isnan(a[:, 1]).all())
        self.assertEqual(r[1], ['multi_tau_level_boundary'] * 3)

    def test_overlap_key_uses_clock_filter_not_origin_count_or_float_text(self):
        left = {'cell': 'A', 'lag_samples': '1920', 'lag_steps': '192000',
                'decimation_samples': '128', 'diffusion_phase_samples': '127',
                'orientation_block_samples': '128', 'origins_per_chain': '63', 'lag_time': '19.2'}
        right = dict(left, origins_per_chain='766', lag_time='19.200000000000003')
        self.assertEqual(alignment_key(left), alignment_key(right))
        # Time consistency is separately authenticated; phase changes are never aligned.
        self.assertNotEqual(alignment_key(left), alignment_key(dict(right, diffusion_phase_samples='126')))

    def test_read_three_replicas_and_reject_mismatched_support(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = {'runs': [], 'expected': {'exported_bins_per_chain': 3}}
            for cell in 'ABCD':
                for rep in (1, 2, 3):
                    run = {'cell': cell, 'id': f'{cell}-r{rep}'}
                    manifest['runs'].append(run)
                    target = root / 'runs' / run['id'] / 'output/dynamics'
                    target.mkdir(parents=True)
                    with (target / 'replica_correlations.csv').open('w', newline='') as f:
                        w = csv.DictWriter(f, fieldnames=SUPPORT + QUANTITIES)
                        w.writeheader()
                        for lag in (0, 1, 15):
                            row = dict.fromkeys(QUANTITIES, rep)
                            row.update(lag_samples=lag, lag_steps=100 * lag, lag_time=lag * .01,
                                       origins_per_chain=100001 - lag, decimation_samples=1,
                                       diffusion_phase_samples=0, orientation_block_samples=1,
                                       orientation_block_duration=.01)
                            w.writerow(row)
            cells = read_replicas(root, manifest, PROFILE)
            self.assertEqual(cells['A']['values'].shape, (3, 3, 12))
            path = root / 'runs/A-r3/output/dynamics/replica_correlations.csv'
            path.write_text(path.read_text().replace('100001', '99999', 1))
            with self.assertRaises(ValueError):
                read_replicas(root, manifest, PROFILE)


if __name__ == '__main__':
    unittest.main()
