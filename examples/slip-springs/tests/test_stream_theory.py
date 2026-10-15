import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import stream_analysis as stream
import validate as rouse

class BlockTheory(unittest.TestCase):
    def test_explicit_wick_sum(self):
        for n in (1,8,32,100):
            for dt in (.01,.005,.0025):
                for equil in (0,17):
                    meta=dict(springs=n,dt=dt,sample=3,stress_frames=43,equil=equil)
                    lam,_=rouse.modes(n)
                    for block,lag in ((1,0),(1,5),(2,8),(3,12),(4,16)):
                        origins=43//block-lag//block
                        for continuous in (False,True):
                            total=0
                            for r in range(origins):
                                for u in range(block):
                                    for v in range(block):
                                        start=equil+(r*block+u)*3
                                        gap=(lag+v-u)*3
                                        if continuous: value=np.exp(-2*lam*dt*gap).sum()
                                        else:
                                            cov=rouse.variance(n,dt,np.array([start]))[0]*(1-lam*dt)**gap
                                            value=np.sum((lam*cov)**2)
                                        total+=value
                            expected=total/origins/block**2
                            self.assertAlmostEqual(stream.reference(meta,lag,block,continuous),expected,places=10)
    def test_zero_and_large_bins(self):
        meta=dict(springs=8,dt=.005,sample=10,stress_frames=1,equil=0)
        self.assertAlmostEqual(stream.reference(meta,0,1),8,places=12)
        meta['stress_frames']=10**10
        self.assertTrue(np.isfinite(stream.reference(meta,2**20,2**16)))
        self.assertAlmostEqual(float(stream.geometric_mean(np.array([0.]),100000)[0]),1)

if __name__=='__main__': unittest.main()
