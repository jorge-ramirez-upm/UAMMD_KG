"""Bounded independent enumeration/statistics, not terminal E1 validation."""
import math
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slip_hopping_reference import Hopping


class Reference(unittest.TestCase):
    def model(self, sites=(0, 2)):
        return Hopping([[0,0,0],[.8,.1,0],[1.7,0,.2],[2.8,0,0]],
                       [[.1,0,0],[2.5,0,0]][:len(sites)], sites, 4, 1.25, 1.7)

    def test_enumeration_detailed_balance_and_stationary_distribution(self):
        for sites in ((0,), (0,2)):
            model = self.model(sites)
            states, pi = model.equilibrium()
            self.assertEqual(len(states), math.comb(4, len(sites)))
            for rate in (.3, 3.):
                q = model.generator(rate)
                flux = pi[:,None]*q
                np.testing.assert_allclose(flux, flux.T, atol=2e-15)
                np.testing.assert_allclose(pi@q, 0, atol=2e-15)
                for i in range(len(states)):
                    for j in range(i+1,len(states)):
                        if q[i,j]:
                            self.assertAlmostEqual(q[i,j]/q[j,i], math.exp(
                                -(model.energy(states[j])-model.energy(states[i]))/model.kbt), places=13)
                t = model.transition(rate, .7)
                np.testing.assert_allclose(pi@t, pi, atol=2e-15)
                np.testing.assert_allclose(t.sum(axis=1), 1, atol=3e-15)
            np.testing.assert_allclose(model.generator(3),10*model.generator(.3),atol=2e-15)

    def test_conditional_is_not_uniform_but_annealed_integrals_are(self):
        model = self.model((0,))
        _, pi = model.equilibrium()
        self.assertGreater(np.ptp(pi), .15)
        # Integrate the unnormalized Gaussian anchor weight for each site;
        # each Cartesian factor is translation independent. Do not integrate
        # conditional probabilities with an artificial uniform anchor measure.
        x = np.linspace(-12, 15, 40001)
        def integral(center):
            weight = np.exp(-model.k*(x-center)**2/(2*model.kbt))
            return np.dot(np.diff(x), .5*(weight[:-1]+weight[1:]))
        integrals = [integral(r[0]) for r in model.r]
        np.testing.assert_allclose(integrals, math.sqrt(2*math.pi*model.kbt/model.k), atol=2e-14)

    def test_sequential_exclusion_boundaries_and_multiple_chains(self):
        model = self.model()
        state = (0,2)
        for j,d,u,result,expected in [(0,-1,.5,1,(0,2)),(0,1,1e-8,0,(1,2)),
                                       (0,1,.5,2,(1,2)),(1,1,1e-8,0,(1,3)),
                                       (0,1,1e-8,0,(2,3))]:
            state, actual = model.attempt(state,j,d,u)
            self.assertEqual((actual,state),(result,expected))
        with self.assertRaises(ValueError):model.check((2,0))
        multi = Hopping(np.tile(model.r,(2,1)),np.tile(model.a,(2,1)),(0,2,4,6),4,1.25)
        self.assertEqual(len(multi.states()),36)
        with self.assertRaises(ValueError):multi.check((0,2,3,6))

    def test_poisson_and_cpu_stationarity_with_independent_replicas(self):
        rng = np.random.default_rng(31237)
        model = self.model()
        states, pi = model.equilibrium()
        for rate in (.5, 3):
            n = 6000
            initial = rng.choice(len(states),size=n,p=pi)
            final = []
            counts = []
            for i in initial:
                state, k, _ = model.batch(states[i],rate,.4,rng)
                final.append(states.index(state));counts.append(k)
            observed = np.bincount(final,minlength=len(states))/n
            self.assertTrue(np.all(np.abs(observed-pi)<6*np.sqrt(pi*(1-pi)/n)))
            mean = len(model.initial)*rate*.4
            self.assertLess(abs(np.mean(counts)-mean),6*math.sqrt(mean/n))
            self.assertLess(abs(np.var(counts)-mean),6*math.sqrt((mean+2*mean*mean)/n))

if __name__ == '__main__':unittest.main(verbosity=2)
