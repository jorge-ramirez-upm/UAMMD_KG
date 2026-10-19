import unittest

from analytical_multitau_resolution import analyze, block_average, instantaneous, spectrum


class AnalyticalMultiTauResolutionTest(unittest.TestCase):
    def test_exact_limit_and_finite_support(self):
        lam, a, v = spectrum(8)
        self.assertAlmostEqual(block_average(lam, a, v, 0, 1), instantaneous(lam, a, v, 0), places=12)
        result = analyze(8, duration_multiple=4)
        self.assertAlmostEqual(result['tau'], 1 / (2 * lam[0]), places=12)
        self.assertTrue(all(x['bins_4tau'] > 0 for x in result['configurations']))
        self.assertTrue(all(x['supported_lag'] <= 4 * result['tau'] + 1e-9 for x in result['configurations']))

    def test_more_slots_reduce_terminal_width(self):
        result = analyze(8, duration_multiple=10)
        widths = {x['slots']: x['max_width'] for x in result['configurations'][:3]}
        self.assertEqual(widths, {16: 32768, 32: 16384, 64: 16384})

    def test_per_bin_complete_pair_counts(self):
        result = analyze(8, duration_multiple=4)
        for cfg in result['configurations'][:3]:
            terminal = cfg['terminal']
            self.assertEqual(terminal['origins'], cfg['frames'] // terminal['width'] - terminal['offset'])
            self.assertGreaterEqual(terminal['origins'], 1)
            counts = {(r['level'], r['offset']): r['origins'] for r in cfg['origin_counts']}
            self.assertEqual(counts[(0, 0)], cfg['frames'])
            self.assertEqual(counts[(0, cfg['slots'] - 1)], cfg['frames'] - cfg['slots'] + 1)
            coarse = next(r for r in cfg['origin_counts'] if r['level'] == 1)
            self.assertEqual(coarse['origins'], cfg['frames'] // coarse['width'] - coarse['offset'])
            self.assertNotEqual(cfg['frames'] % coarse['width'], 0)


if __name__ == '__main__':
    unittest.main()
