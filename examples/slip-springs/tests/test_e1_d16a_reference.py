"""Local CPU readiness tests. No equilibrium configurations are sampled."""
import math
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import e1_d16a_reference as ref


class AnalyticalTests(unittest.TestCase):
    def test_finite_sums_and_quadratic_forms(self):
        for n in (1, 2, 8, 32, 100):
            m = n+1
            a = ref.matrix_a(n)
            np.testing.assert_allclose([np.trace(a), np.sum(np.diag(a)**2), np.trace(a @ a), a.sum()],
                [(m*m-1)/(6*m), (m**4-1)/(30*m**3), (m*m-1)*(2*m*m+7)/(180*m*m), (m*m-1)/12],
                rtol=3e-14, atol=3e-14)
            mu2, mu4 = 1.2, 1.7
            actual = ref.flexible(n, mu2, mu4)
            j = np.ones_like(a)
            np.testing.assert_allclose([actual['var_X'], actual['var_Y'], actual['cov_XY']],
                [ref.quadratic_covariance(j, j, mu2, mu4), ref.quadratic_covariance(a, a, mu2, mu4),
                 ref.quadratic_covariance(j, a, mu2, mu4)], rtol=3e-14, atol=3e-14)
            self.assertAlmostEqual(ref.quadratic_covariance(j, a, mu2, mu4),
                                   ref.quadratic_covariance(a, j, mu2, mu4), places=11)
            eigen = np.linalg.eigvalsh([[actual['var_X'], actual['cov_XY']], [actual['cov_XY'], actual['var_Y']]])
            self.assertGreaterEqual(eigen.min(), -1e-12*max(1, eigen.max()))

    def test_single_bond_fixed_length_and_gaussian_algebra(self):
        result = ref.flexible(1, 1.2, 1.7)
        for y, x, factor in (('mean_Y', 'mean_X', 4), ('var_Y', 'var_X', 16),
                             ('cov_XY', 'var_X', 4), ('mean_Y2', 'mean_X2', 16)):
            self.assertAlmostEqual(result[y]*factor, result[x], places=13)
        for n in (1, 2, 32):
            mu2 = 1.2
            self.assertAlmostEqual(ref.flexible(n, mu2, mu2**2)['mean_X2'], (5*n*n-2*n)*mu2**2/3, places=10)
            a = ref.matrix_a(n)
            self.assertAlmostEqual(ref.quadratic_covariance(a, a, mu2, 5*mu2**2/3),
                                   2*mu2**2/3*np.trace(a @ a), places=11)

    def test_actual_radial_law_and_quadrature(self):
        checks = ref.numerical_checks()
        moments = checks['radial_recurrence']
        self.assertGreater(moments['4'], moments['2']**2)
        # The finite-rest-length density is not a Gaussian-vector radial law.
        self.assertGreater(abs(moments['4']-5*moments['2']**2/3), .1)
        for p in ('1', '2', '4', '8'):
            self.assertLessEqual(checks['radial_absolute_error_estimates'][p], 1e-10*moments[p])
        for name in ('mean_X', 'mean_Y'):
            self.assertAlmostEqual(checks['size_means']['0'][name], checks['flexible'][name], places=12)

    def test_half_line_zero_rest_length(self):
        # Independent gamma integral at b=0, not a whole-line normal radius.
        a = 15.
        moments = ref.radial_recurrence(a=a, b=0.)
        for p in (1, 2, 4, 8):
            self.assertAlmostEqual(moments[str(p)], a**(-p/2)*math.gamma((p+3)/2)/math.gamma(1.5), places=13)

    def test_joint_null_law(self):
        value = ref.joint_variances(32, 640, 256, 2048)
        self.assertEqual(value['cov_A_B'], 0)
        self.assertAlmostEqual(value['var_A_joint'], 640/32**2/256)
        self.assertAlmostEqual(value['var_B_joint'], 2*640/32**2/(3*2048))


class ProtocolTests(unittest.TestCase):
    def rows(self):
        # Deterministic heterogeneous batches exercise central merging, not a
        # scientific sample or an assumed physical probability distribution.
        x = np.linspace(1, 20, ref.BATCH)
        cuts = [list(np.linspace(2, 18, 9)), list(np.linspace(2, 10, 9))]
        arrays = [np.column_stack((x+i/8, .3*x+(x % 3)+i/32)) for i in range(32)]
        return arrays, [ref.batch_summary(xy, cuts) for xy in arrays]

    def test_stable_merging_and_inference(self):
        arrays, rows = self.rows()
        xy = np.concatenate(arrays)
        point = ref.estimates(rows)
        expected_cov = np.cov(xy, rowvar=False, ddof=1)
        np.testing.assert_allclose(point[:7], [*xy.mean(axis=0), expected_cov[0, 0], expected_cov[1, 1],
                                              expected_cov[0, 1], *np.mean(xy**2, axis=0)], rtol=2e-13)
        inferred = ref.inference(rows)
        self.assertEqual(inferred['count'], 32*ref.BATCH)
        self.assertEqual(len(inferred['names']), 25)
        covariance = np.asarray(inferred['covariance_of_estimates_delta'])
        np.testing.assert_allclose(covariance, covariance.T, atol=1e-14)
        g = np.zeros((25, 23))
        g[0, 0] = g[1, 1] = 1
        factor = len(xy)/(len(xy)-1)
        g[2, [0, 2]] = [-2*point[0]*factor, factor]
        g[3, [1, 3]] = [-2*point[1]*factor, factor]
        g[4, [0, 1, 4]] = [-point[1]*factor, -point[0]*factor, factor]
        g[5, 2] = g[6, 3] = 1
        g[7:, 5:] = np.eye(18)
        np.testing.assert_allclose(g @ np.asarray(inferred['covariance_of_mean_W']) @ g.T,
                                   covariance, rtol=1e-10, atol=1e-11)
        direct_leave_out = [ref.estimates(rows[:i]+rows[i+1:]) for i in range(len(rows))]
        direct_jackknife = np.std(direct_leave_out, axis=0, ddof=1)*(len(rows)-1)/math.sqrt(len(rows))
        np.testing.assert_allclose(inferred['jackknife_se'], direct_jackknife, rtol=1e-10, atol=1e-11)
        # Translation tests stability of variance/covariance without altering
        # the analytic physical law or sampling reference coordinates.
        shifted = [ref.batch_summary(a+1e6, [[1e6]*9, [1e6]*9]) for a in arrays]
        np.testing.assert_allclose(ref.estimates(shifted)[2:5], point[2:5], rtol=2e-9)

    def test_seed_ledger_namespaces(self):
        identities = set()
        for kappa in (0, 10):
            for phase, count in ((1, ref.CALIBRATION), (2, ref.PILOT), (3, ref.GRID[-1])):
                for index in range(count//ref.BATCH):
                    entropy = [721610000, kappa, phase, index]
                    identity = tuple(np.random.SeedSequence(entropy).generate_state(4))
                    self.assertNotIn(identity, identities)
                    identities.add(identity)
        self.assertEqual(len(identities), 2*598016//ref.BATCH)

    def test_frozen_selection_no_extension(self):
        point = np.ones(25)
        small = {'estimate': point.tolist(), 'delta_se': [1e-6]*25}
        self.assertEqual(ref.select_size(small)['selected_count'], ref.GRID[0])
        huge = dict(small, delta_se=[10.]*25)
        self.assertIsNone(ref.select_size(huge)['selected_count'])
        zero = dict(small, delta_se=[0.]*25)
        with self.assertRaises(ValueError):
            ref.select_size(zero)

    def test_binomial_endpoints_and_cuts(self):
        zero, full = ref.binomial_interval(0, 100), ref.binomial_interval(100, 100)
        self.assertEqual(zero[0], 0)
        self.assertGreater(zero[1], 0)
        self.assertEqual(full[1], 1)
        self.assertLess(full[0], 1)
        array = np.column_stack((np.arange(ref.CALIBRATION), np.arange(ref.CALIBRATION)[::-1])).astype(float)
        ordered, cuts = ref.freeze_quantiles(array)
        self.assertEqual(cuts['cuts'][0][4], ref.CALIBRATION/2-1)
        self.assertEqual(cuts['cuts'][0], cuts['cuts'][1])
        self.assertTrue(np.all(np.diff(ordered, axis=0) >= 0))

    def test_incomplete_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            ref.batch_summary(np.ones((511, 2)), [[1]*9, [1]*9])
        with self.assertRaises(ValueError):
            ref.batch_summary(np.full((512, 2), np.nan), [[1]*9, [1]*9])


if __name__ == '__main__':
    unittest.main()
