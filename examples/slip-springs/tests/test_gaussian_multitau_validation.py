import unittest
import numpy as np

from gaussian_multitau_validation import block_reference, modes, observations, summarize


class GaussianMultiTauValidationTest(unittest.TestCase):
    def test_paired_hierarchies_and_block_reference(self):
        channels, lam, a, variance = observations(frames=512, chains=4, seed=433201)
        self.assertEqual(channels.shape, (4, 512, 6))
        rows = summarize(channels, lam, a, variance, ((16, 10), (32, 9), (64, 8), (16, 40)))
        self.assertEqual([r['bins'] for r in rows], [56, 96, 160, 56])
        for result in rows:
            self.assertLess(result['max_abs_block'], 1e-10)
            self.assertTrue(np.isfinite(result['terminal']['chain_se']))

    def test_exact_stationary_zero_lag_reference(self):
        lam = modes(8)
        a = 1 - lam * 2.5e-5
        variance = 1 / (lam * (1 - lam * 2.5e-5 / 2))
        self.assertAlmostEqual(block_reference(lam, a, variance, 0, 1),
                               float(np.sum(lam * lam * variance * variance)), places=12)


if __name__ == '__main__':
    unittest.main()
