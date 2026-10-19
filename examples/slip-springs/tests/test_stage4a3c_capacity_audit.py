import unittest
from stage4a3c_capacity_audit import bank_bytes, bins_through, hierarchy, maximum

class CapacityAuditTests(unittest.TestCase):
    def test_frozen_linux64_bank_accounting(self):
        self.assertAlmostEqual(bank_bytes(64, 21)/2**20, 490.15625)
        self.assertGreater(bank_bytes(64, 22), 512*2**20)
        self.assertAlmostEqual(bank_bytes(32, 24)/2**20, 284.09375)
    def test_support_never_exceeds_nominal_and_requires_sixteen_origins(self):
        rows=hierarchy(64, 21, 8_000_001)
        for row in rows:
            if row['supported_lag_samples'] is not None:
                self.assertLessEqual(row['supported_lag_samples'], row['nominal_lag_samples'])
        self.assertGreater(maximum(rows, 'supported_lag_time'), 4*1.382)
    def test_short_fixture_cannot_claim_long_support(self):
        rows=hierarchy(64, 12, 10_001)
        self.assertLess(maximum(rows, 'supported_lag_time'), 1)
    def test_minimum_planning_levels_and_bins(self):
        n8=4*1.382; n32=4*565
        self.assertEqual(bins_through(hierarchy(16,15,8_000_001),n8),140)
        self.assertEqual(bins_through(hierarchy(32,14,8_000_001),n8),248)
        self.assertEqual(bins_through(hierarchy(64,13,8_000_001),n8),450)
        self.assertEqual(bins_through(hierarchy(32,23,160_000_001),n32),396)

if __name__ == '__main__': unittest.main()
