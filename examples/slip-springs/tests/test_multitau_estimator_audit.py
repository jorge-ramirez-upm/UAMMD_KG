import unittest
import numpy as np
from multitau_estimator_audit import block_expected, direct, multi_tau, sequence

class MultiTauAuditTests(unittest.TestCase):
    def test_exact_pair_counts_and_exported_deepest_omission(self):
        x=np.arange(1024,dtype=float)
        out=multi_tau(x,16,8)
        self.assertEqual(out[0][0:3],(0,float(np.mean(x*x)),1024))
        self.assertLess(max(row[0] for row in out),15*2**7)  # final populated level is omitted
        for lag,value,pairs,width,level in out:
            expected,raw=block_expected(x,width,lag)
            self.assertAlmostEqual(value,expected,places=10)
            self.assertEqual(pairs,raw)
    def test_block_averaging_is_not_instantaneous_correlation(self):
        x=sequence('exp',433701,65536);out=multi_tau(x,16,16)
        coarse=next(row for row in out if row[3]>=8)
        lag,value,pairs,width,level=coarse
        instantaneous,_=direct(x,lag);block,_=block_expected(x,width,lag)
        self.assertGreater(abs(value-instantaneous),1e-5)
        self.assertLess(abs(value-block),1e-12)
    def test_all_fixture_families_are_finite(self):
        for kind in ('white','exp','fast-slow','tail','deterministic'):
            self.assertTrue(np.isfinite(sequence(kind,433700,4096)).all())

if __name__=='__main__':unittest.main()
