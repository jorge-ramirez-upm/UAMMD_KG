"""Prepared, UNEXECUTED local arithmetic/parser checks; no campaign data or figures.

Command: python3 -B examples/slip-springs/tests/d2a3_analysis_regression.py
Three-point analytical stencils below are verification inputs, not scientific curves.
"""
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e1_d2a3_analyze import load, local_slopes, mean_se, region


class AnalysisArithmetic(unittest.TestCase):
    def test_replica_se_has_run_count_not_origin_count(self):
        mean, se = mean_se(np.array([[1., 3.], [3., 7.]]))
        np.testing.assert_allclose(mean, [2, 5], rtol=1e-14)
        np.testing.assert_allclose(se, [1, 2], rtol=1e-14)
        with self.assertRaises(ValueError):
            mean_se(np.array([[1., 3.]]))

    def test_same_level_log_stencil(self):
        a, reasons = local_slopes(np.array([1., 2., 4.]), np.array([[1., 2., 4.], [1., 4., 16.]]),
                                  np.array([1, 1, 1]), ['fine'] * 3)
        np.testing.assert_allclose(a[:, 1], [1, 2], rtol=1e-14)
        self.assertEqual(reasons, [['record_edge'] * 2, ['available_same_level_stencil'] * 2,
                                  ['record_edge'] * 2])

    def test_boundary_weak_support_and_zero_excluded_with_reason(self):
        for blocks, regions, times, expected in (
                ([1, 2, 2], ['fine'] * 3, [1, 2, 4], 'multi_tau_level_boundary'),
                ([1, 1, 1], ['fine', 'fine', 'weak_tail'], [1, 2, 4], 'weak_support_stencil'),
                ([1, 1, 1], ['fine'] * 3, [0, 2, 4], 'logarithm_undefined')):
            a, reasons = local_slopes(np.array(times), np.ones((2, 3)), np.array(blocks), regions)
            self.assertTrue(np.isnan(a[:, 1]).all())
            self.assertEqual(reasons[1], [expected] * 2)

    def test_unequal_log_spacing_quadratic_derivative(self):
        times = np.array([1., 2., 3.])
        log_time = np.log(times)
        values = np.array([np.exp(log_time**2), np.exp(2 * log_time**2)])
        a, _ = local_slopes(times, values, np.array([1, 1, 1]), ['fine'] * 3)
        np.testing.assert_allclose(a[:, 1], [2 * np.log(2), 4 * np.log(2)], rtol=1e-13)

    def test_undefined_replica_does_not_remove_other_replica_slope(self):
        a, reasons = local_slopes(np.array([1., 2., 4.]), np.array([[0., 2., 4.], [1., 2., 4.]]),
                                  np.array([1, 1, 1]), ['fine'] * 3)
        self.assertTrue(np.isnan(a[0, 1]))
        self.assertAlmostEqual(a[1, 1], 1)
        self.assertEqual(reasons[1], ['logarithm_undefined', 'available_same_level_stencil'])

    def test_region_edges(self):
        self.assertEqual(region(.15, 9986), 'fine')
        self.assertEqual(region(19.2, 63), 'coarse_primary')
        self.assertEqual(region(20.48, 31), 'weak_tail')

    def test_duplicate_and_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'record.json'
            for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    load(path)


if __name__ == '__main__':
    unittest.main()
