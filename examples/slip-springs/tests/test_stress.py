"""Independent full-matrix/Wick and direct-sum tests for Stage 2A."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
import tempfile
import json
import numpy as np
import stress
import validate

class StressTheoryTests(unittest.TestCase):
    def test_wick_matrix_reference(self):
        for n in (1, 4, 8):
            m = n+1
            b = np.zeros((n,m))
            for j in range(n):
                b[j,j:j+2] = [-1,1]
            stiffness = 3*b.T@b
            projector = np.eye(m)-np.ones((m,m))/m
            initial = np.linalg.pinv(stiffness, hermitian=True)
            for dt in (.01,.005,.0025,.05):
                a = np.eye(m)-dt*stiffness
                covariances = [initial]
                for _ in range(110):
                    covariances.append(a@covariances[-1]@a.T+2*dt*projector)
                for origins in ([0], [0,3,80]):
                    for lag in (0,1,7,16):
                        shear, diagonal = [], []
                        for origin in origins:
                            old,new = covariances[origin],covariances[origin+lag]
                            cross = np.linalg.matrix_power(a,lag)@old
                            wick = np.trace(stiffness@cross@stiffness@cross.T)
                            shear.append(wick)
                            diagonal.append(np.trace(stiffness@old)*np.trace(stiffness@new)+2*wick)
                        expected = [np.mean(shear),np.mean(diagonal)]
                        np.testing.assert_allclose(stress.reference(n,dt,origins,lag), expected, rtol=2e-12, atol=1e-12)
                np.testing.assert_allclose(stress.reference(n,dt,[0],0), [n,n*n+2*n], rtol=2e-12)
                lam = validate.modes(n)[0]
                for lag in (0,1,7):
                    expected = np.exp(-2*lam*lag*dt).sum()
                    self.assertAlmostEqual(stress.reference(n,dt,[0],lag,True)[0],expected)
            # Rotation: (x^2-y^2)/2 has the same two-time covariance as x*y.
            self.assertAlmostEqual((2*n+2*n)/4, n)

    def test_square_before_origin_average(self):
        n, dt, origins, lag = 8, .05, np.array([0,1,80]), 3
        lam = validate.modes(n)[0]
        cov = lam*validate.variance(n,dt,origins)*(1-lam*dt)**lag
        correct = (cov**2).sum(axis=-1).mean()
        wrong = (cov.mean(axis=0)**2).sum()
        self.assertGreater(correct-wrong, 1e-7)
        self.assertAlmostEqual(stress.reference(n,dt,origins,lag)[0], correct)

    def test_saved_chain_contributions(self):
        with tempfile.TemporaryDirectory(prefix='stress-fixture-') as tmp:
            root = Path(tmp)
            meta = dict(chains=4, springs=1, dt=.01, equil=0,
                        sampled_zero_bonds=0, max_spacing_over_noise=0)
            (root/'metadata.json').write_text(json.dumps(meta))
            tensor = np.arange(5*4*6,dtype=float).reshape(5,4,6)/10
            header = ('step,chain,'+','.join(stress.TENSOR))
            rows = [[t,c,*tensor[t,c]] for t in range(5) for c in range(4)]
            np.savetxt(root/'samples.csv', rows, delimiter=',', header=header, comments='')
            result = stress.analyze(root)
            expected = np.stack((tensor[...,3],tensor[...,4],tensor[...,5],
                                 (tensor[...,0]-tensor[...,1])/2,
                                 (tensor[...,0]-tensor[...,2])/2,
                                 (tensor[...,1]-tensor[...,2])/2),axis=-1)
            with np.load(root/'stress_chain_contributions.npz') as saved:
                np.testing.assert_array_equal(saved['chain_ids'], np.arange(4))
                self.assertEqual(saved['contributions'].shape, (3,4,6))
                for j,lag in enumerate((0,1,4)):
                    np.testing.assert_allclose(saved['contributions'][j],stress.direct_products(expected,lag))
            d = result['correlations'][3]
            self.assertEqual(d['raw_value'],4*d['value'])
            # This arbitrary deterministic fixture tests the estimator, not Gaussian physics.
            self.assertFalse(result['passed'])

    def test_direct_products_and_paired_uncertainty(self):
        values = np.arange(5*4*6,dtype=float).reshape(5,4,6)/10
        for lag in (0,1,4):
            actual = stress.direct_products(values,lag)
            oracle = np.zeros((4,6))
            for c in range(4):
                for ch in range(6):
                    oracle[c,ch] = sum(values[t,c,ch]*values[t+lag,c,ch] for t in range(5-lag))/(5-lag)
            np.testing.assert_allclose(actual,oracle,rtol=1e-14)
            mean,se = validate.estimate(actual[:,1]-actual[:,0])
            self.assertAlmostEqual(mean, np.mean(oracle[:,1]-oracle[:,0]))
            self.assertAlmostEqual(se, np.std(oracle[:,1]-oracle[:,0],ddof=1)/2)
        for bad in (-1,5):
            with self.assertRaises(ValueError):
                stress.direct_products(values,bad)

if __name__ == '__main__':
    unittest.main()
