"""D1.6A.2 deterministic constructed-data tests; no reference sampling.

Prepared for local Stage A. Importing this file executes no checks.
"""
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
from scipy.stats import beta, t

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import e1_d16a2_reference as ref


class ReferenceTests(unittest.TestCase):
    def rows(self):
        x = np.linspace(1, 20, ref.BATCH)
        cuts = [list(np.linspace(2, 18, 9)), list(np.linspace(2, 10, 9))]
        arrays = [np.column_stack((x+i/8, .3*x+(x % 3)+i/32)) for i in range(32)]
        return arrays, [ref.batch_summary(xy, cuts) for xy in arrays]

    def test_reproducible_batch_inference(self):
        arrays, rows = self.rows()
        xy = np.concatenate(arrays)
        inferred = ref.inference(rows)
        self.assertEqual(ref.inference(rows), inferred)
        cov = np.cov(xy, rowvar=False, ddof=1)
        np.testing.assert_allclose(inferred['estimate'][:7],
            [*xy.mean(axis=0), cov[0, 0], cov[1, 1], cov[0, 1], *np.mean(xy**2, axis=0)], rtol=2e-13)
        leave = [ref.estimates(rows[:i]+rows[i+1:]) for i in range(len(rows))]
        np.testing.assert_allclose(inferred['jackknife_se'],
            np.std(leave, axis=0, ddof=1)*(len(rows)-1)/math.sqrt(len(rows)), rtol=1e-10, atol=1e-11)
        point = np.asarray(inferred['estimate'])
        g = np.zeros((25, 23))
        g[0, 0] = g[1, 1] = 1
        factor = len(xy)/(len(xy)-1)
        g[2, [0, 2]] = [-2*point[0]*factor, factor]
        g[3, [1, 3]] = [-2*point[1]*factor, factor]
        g[4, [0, 1, 4]] = [-point[1]*factor, -point[0]*factor, factor]
        g[5, 2] = g[6, 3] = 1
        g[7:, 5:] = np.eye(18)
        np.testing.assert_allclose(g @ np.asarray(inferred['covariance_of_mean_W']) @ g.T,
            inferred['covariance_of_estimates_delta'], rtol=1e-10, atol=1e-11)

    def test_simultaneous_allocation_across_families_and_kappas(self):
        self.assertEqual(ref.M_ALPHA+ref.C_ALPHA, .05)
        self.assertEqual(ref.M_FAMILY, 2*7)
        self.assertEqual(ref.C_FAMILY, 2*18)
        _, rows = self.rows()
        inferred = ref.inference(rows)
        self.assertEqual(inferred['critical_t'], float(t.ppf(1-.025/(2*14), 31)))
        interval = ref.binomial_interval(50, 100)
        self.assertEqual(interval, [float(beta.ppf(.025/(2*36), 50, 51)),
                                    float(beta.ppf(1-.025/(2*36), 51, 50))])
        self.assertEqual(ref.binomial_interval(0, 100)[0], 0)
        self.assertEqual(ref.binomial_interval(100, 100)[1], 1)

    def test_moment_only_selection_invariant_to_cdf_uncertainty(self):
        pilot = {'estimate': [1.]*25, 'delta_se': [1e-6]*25}
        baseline = ref.select_size(pilot)
        pilot['delta_se'][7:] = [float('nan')]*18
        pilot['estimate'][7:] = [float('nan')]*18
        self.assertEqual(ref.select_size(pilot), baseline)
        self.assertEqual(baseline['selected_count'], 16384)
        self.assertEqual([p['count'] for p in baseline['predictions']], list(ref.GRID))
        self.assertEqual(baseline['pilot_SE_multiplier'], 2)
        pilot['delta_se'][2:7] = [10.]*5
        self.assertIsNone(ref.select_size(pilot)['selected_count'])
        pilot['delta_se'][2:7] = [0.]*5
        with self.assertRaises(ValueError):
            ref.select_size(pilot)

    def fixture(self):
        point = [10., 2., 4., 1., .5, 104., 5.]+[.5]*18
        half = [.1, .1, .1, .025, .025, 1., .1]+[.01]*18
        final = {'estimate': point, 'half_width': half, 'delta_se': [.001]*25,
                 'jackknife_se': [.0011]*25,
                 'interval': [[v-h, v+h] for v, h in zip(point, half)]}
        exact = dict(zip(ref.NAMES[:7], point[:7]))
        numerical = {'flexible': exact,
            'flexible_absolute_error_estimates': {name: 0. for name in exact},
            'size_means': {str(k): dict(zip(ref.NAMES[:2], point[:2])) for k in (0, 10)},
            'size_mean_absolute_error_estimates': {str(k): dict.fromkeys(ref.NAMES[:2], 0.) for k in (0, 10)}}
        return final, numerical

    def test_m_pass_c_unresolved_both_kappas_and_all_observables_retained(self):
        for kappa in (0, 10):
            final, numerical = self.fixture()
            assessed = ref.assess(final, numerical, kappa)
            self.assertEqual(assessed['status'], 'MOMENTS_PRECISION_RESOLVED_NOMINAL')
            self.assertEqual(assessed['cdf_status'], 'CDF_PRECISION_UNRESOLVED')
            self.assertTrue(assessed['moments_accepted'])
            self.assertEqual(len(assessed['observables']), 25)
            self.assertEqual(assessed['primary_moment_reference'],
                             'ANALYTICAL_EXACT' if kappa == 0 else 'INDEPENDENT_FINAL_SAMPLE')
            self.assertEqual(assessed['observables'][4]['required_precision_threshold'], .1)
            self.assertTrue(all(o['required_precision_threshold'] == .005 for o in assessed['observables'][7:]))

    def test_m_unresolved_c_resolved_and_consistency_failure_are_visible(self):
        final, numerical = self.fixture()
        final['half_width'][2] = .21
        final['half_width'][7:] = [.004]*18
        assessed = ref.assess(final, numerical, 10)
        self.assertEqual(assessed['status'], 'MOMENTS_PRECISION_UNRESOLVED')
        self.assertEqual(assessed['cdf_status'], 'CDF_PRECISION_RESOLVED_NOMINAL')
        self.assertFalse(assessed['moments_accepted'])
        final, numerical = self.fixture()
        numerical['size_means']['10']['mean_X'] = 999.
        assessed = ref.assess(final, numerical, 10)
        self.assertEqual(assessed['status'], 'NUMERICAL_CONSISTENCY_FAILED')
        self.assertFalse(assessed['moments_accepted'])
        # All exact kappa=0 variances/covariance/fourth moments remain checked.
        final, numerical = self.fixture()
        for name in ref.NAMES[2:7]:
            modified = dict(numerical, flexible=dict(numerical['flexible'], **{name: 999.}))
            self.assertEqual(ref.assess(final, modified, 0)['status'], 'NUMERICAL_CONSISTENCY_FAILED')

    def test_full_seed_collision_audit_and_forced_collision(self):
        audit = ref.seed_audit()
        self.assertEqual(audit['namespaces'], {'721610000': 2336, '721612000': 2336})
        self.assertEqual(audit['total_identities'], 4672)
        self.assertEqual(audit['new_equilibrium_draws'], 0)
        seed = np.random.SeedSequence([123])
        with patch.object(ref.np.random, 'SeedSequence', return_value=seed):
            with self.assertRaises(ValueError):
                ref.seed_audit()

    def test_incomplete_batch_rejected(self):
        with self.assertRaises(ValueError):
            ref.batch_summary(np.ones((511, 2)), [[1]*9, [1]*9])
        with self.assertRaises(ValueError):
            ref.batch_summary(np.full((512, 2), np.nan), [[1]*9, [1]*9])


if __name__ == '__main__':
    unittest.main()
