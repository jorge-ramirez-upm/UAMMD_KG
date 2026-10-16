"""Bounded Stage 4A.1 checks; fixed seeds, independent chains as sample units."""
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain, langevin, radial_moments


def simpson(y, dx):
    return dx/3 * (y[0] + y[-1] + 4*y[1:-1:2].sum() + 2*y[2:-1:2].sum())


def radial_grid(b, k, kbt=1):
    # Independent uniform-grid Simpson integration, rather than Gauss nodes.
    sigma = math.sqrt(kbt/k)
    r = np.linspace(max(0, b-14*sigma), b+14*sigma, 40001)
    w = r*r*np.exp(-0.5*((r-b)/sigma)**2)
    return r, w, simpson(w, r[1]-r[0])


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.r = np.array([[0.2, -0.4, 0.1], [1.1, 0.2, -0.1],
                           [1.5, 1.3, 0.4], [0.9, 1.6, 1.1], [1.3, 2.2, 1.4]])
        self.chain = Chain([0.7, 1, 0, 1.2], [3, 7, 2, 11], [0, 0.1, 0, 8, 0])

    def assert_sample_mean(self, values, target):
        values = np.asarray(values)
        se = values.std(axis=0, ddof=1)/math.sqrt(len(values))
        # Six standard errors across independent chains; absolute floor handles
        # near deterministic observables. No overlapping origins are counted.
        self.assertTrue(np.all(np.abs(values.mean(axis=0)-target) <= 6*se + 5e-4),
                        (values.mean(axis=0), target, se))

    def test_finite_difference_each_term(self):
        homogeneous = Chain.homogeneous(4, kb=4, kappa=2)
        nearly = np.array([[0, 0, 0], [1, 0, 0], [2, 1e-7, 0],
                           [1, 2e-7, 0], [0, 1e-7, 1e-8]], dtype=float)
        for chain in (self.chain, homogeneous, Chain.homogeneous(4, kb=4, kappa=1e-9),
                      Chain.homogeneous(4, kb=4, kappa=1000)):
            for r in (self.r, nearly):
                for method in (chain.stretch_energy_forces, chain.bend_energy_forces, chain.energy_forces):
                    _, forces = method(r)
                    numerical = np.empty_like(r)
                    for index in np.ndindex(r.shape):
                        plus, minus = r.copy(), r.copy()
                        plus[index] += 2e-6
                        minus[index] -= 2e-6
                        numerical[index] = -(method(plus)[0]-method(minus)[0])/4e-6
                    # The absolute cancellation floor scales with the energy coefficient.
                    floor = max(2e-8, 2e-10*chain.kappa.max())
                    np.testing.assert_allclose(forces, numerical, atol=floor, rtol=2e-7)

    def test_symmetries_force_torque(self):
        rotation, _ = np.linalg.qr(np.random.default_rng(11).normal(size=(3, 3)))
        for method in (self.chain.stretch_energy_forces, self.chain.bend_energy_forces,
                       self.chain.energy_forces):
            e, f = method(self.r)
            et, ft = method(self.r + [2, -3, 4])
            er, fr = method(self.r @ rotation)
            self.assertAlmostEqual(e, et, delta=2e-13)
            self.assertAlmostEqual(e, er, delta=2e-13)
            np.testing.assert_allclose(ft, f, atol=2e-13, rtol=2e-13)
            np.testing.assert_allclose(fr, f @ rotation, atol=2e-13, rtol=2e-13)
            np.testing.assert_allclose(f.sum(axis=0), 0, atol=2e-14)
            np.testing.assert_allclose(np.cross(self.r-self.r.mean(axis=0), f).sum(axis=0), 0, atol=3e-14)

    def test_endpoint_signs_and_straight_folded(self):
        chain = Chain.homogeneous(1, b0=1, kb=3)
        e, f = chain.energy_forces([[0, 0, 0], [2, 0, 0]])
        self.assertEqual(e, 1.5)
        np.testing.assert_array_equal(f, [[3, 0, 0], [-3, 0, 0]])
        chain = Chain.homogeneous(2, kb=3, kappa=4)
        for r, expected in (([[0, 0, 0], [1, 0, 0], [2, 0, 0]], 0),
                            ([[0, 0, 0], [1, 0, 0], [0, 0, 0]], 8)):
            e, f = chain.bend_energy_forces(r)
            self.assertEqual(e, expected)
            np.testing.assert_array_equal(f, np.zeros((3, 3)))

    def test_zero_bending_is_exact_fast_path(self):
        chain = Chain.homogeneous(4, kappa=0)
        self.assertIsNone(chain.active_angles)
        e, f = chain.stretch_energy_forces(self.r)
        # Proves no angular call or angular allocation is reachable in total.
        with patch.object(chain, '_bend', side_effect=AssertionError('angular work')):
            with patch.object(chain, '_stretch', return_value=(e, f)):
                et, ft = chain.energy_forces(self.r)
                self.assertIs(ft, f)
            et, ft = chain.energy_forces(self.r)
        self.assertEqual(et, e)
        np.testing.assert_array_equal(ft, f)

    def test_inactive_angles_skip_collapsed_bonds(self):
        chain = Chain([0, 1, 1], [2, 3, 4], [0, 0, 2, 0])
        r = np.array([[0, 0, 0], [0, 0, 0], [1, 0, 0], [1, 1, 0]])
        self.assertEqual(chain.active_angles, ((2, 2.0),))
        chain.energy_forces(r)  # Zero bond belongs only to an inactive angle.
        np.testing.assert_array_equal(chain.stretch_energy_forces(r)[1][0], [0, 0, 0])

    def test_invalid_parameters_and_geometry(self):
        for args in (([], [], [0]), ([1], [0], [0, 0]), ([1], [-1], [0, 0]),
                     ([-1], [2], [0, 0]), ([1], [2], [1, 0]), ([1], [2], [0]),
                     ([np.nan], [2], [0, 0]), ([1, 1], [2, 2], [0, -1, 0]),
                     ([[1]], [2], [0, 0])):
            with self.assertRaises(ValueError):
                Chain(*args)
        for r in (np.zeros((4, 3)), np.full((5, 3), np.nan)):
            with self.assertRaises(ValueError):
                self.chain.energy_forces(r)
        with self.assertRaises(ValueError):
            Chain.homogeneous(1).energy_forces(np.zeros((2, 3)))
        with self.assertRaises(ValueError):
            Chain.homogeneous(2, b0=0, kappa=1).energy_forces(np.zeros((3, 3)))
        self.assertEqual(Chain.homogeneous(1, b0=0).energy_forces(np.zeros((2, 3)))[0], 0)
        for x in (-1, np.inf, np.nan):
            with self.assertRaises(ValueError):
                langevin(x)
        for t in (0, -1, np.inf, np.nan):
            with self.assertRaises(ValueError):
                self.chain.sample(1, np.random.default_rng(1), t)
            with self.assertRaises(ValueError):
                radial_moments(1, 3, t)
        with self.assertRaises(ValueError):
            self.chain.sample(0, np.random.default_rng(1))
        with self.assertRaises(ValueError):
            Chain.homogeneous(1, kappa=-1)
        with self.assertRaises(ValueError):
            radial_moments(1, 0)

    def test_langevin_independent_quadrature(self):
        c = np.linspace(-1, 1, 200001)
        for x in (0, 1e-9, 0.01, 0.049999, 0.05, 0.050001, 0.3, 3, 30, 350, 351, 1000):
            w = np.exp(x*(c-1))
            expected = simpson(c*w, 1e-5)/simpson(w, 1e-5)
            self.assertAlmostEqual(langevin(x), expected, delta=3e-12)
        self.assertEqual(langevin(0), 0)
        self.assertAlmostEqual(langevin(1e-12), 1e-12/3, delta=1e-28)
        self.assertEqual(langevin(1e12), 1-1e-12)

    def test_radial_moments_independent_quadrature_and_maxwell(self):
        for b, k, t in ((0, 3, 1), (0.01, 0.2, 2), (1, 30, 1), (2, 200, 0.7)):
            r, w, z = radial_grid(b, k, t)
            expected = [simpson(w*r**p, r[1]-r[0])/z for p in (1, 2)]
            np.testing.assert_allclose(radial_moments(b, k, t), expected, rtol=3e-12, atol=3e-13)
        np.testing.assert_allclose(radial_moments(0, 3, 2),
                                   [2*math.sqrt(2/3)*math.sqrt(2/math.pi), 2], rtol=3e-13)
        # Far from the radial boundary, Gaussian polynomial integrals are exact.
        np.testing.assert_allclose(radial_moments(10, 1), [1030/101, 10603/101], rtol=3e-13)

    def test_sample_radial_cdf_and_orientation_cdf(self):
        count = 16000
        for b, k, x in ((0, 2, 0), (1, 30, 1e-6), (2, 2, 3), (1, 100, 1000)):
            chain = Chain.homogeneous(2, b0=b, kb=k, kappa=x)
            q = np.diff(chain.sample(count, np.random.default_rng(4100+int(x))), axis=1)
            lengths = np.linalg.norm(q, axis=2)
            r, w, _ = radial_grid(b, k)
            cdf = np.r_[0, np.cumsum((w[1:]+w[:-1])*(r[1]-r[0])/2)]
            cdf /= cdf[-1]
            u = np.sort(np.interp(lengths[:, 0], r, cdf))
            grid = np.arange(1, count+1)/count
            self.assertLess(max(np.max(grid-u), np.max(u-grid+1/count)), 0.025)
            c = np.sum(q[:, 0]*q[:, 1], axis=1)/np.prod(lengths, axis=1)
            if x == 0:
                u = (np.sort(c)+1)/2
            else:
                u = (np.exp(x*(np.sort(c)-1))-np.exp(-2*x))/(-np.expm1(-2*x))
            self.assertLess(max(np.max(grid-u), np.max(u-grid+1/count)), 0.025)
            self.assert_sample_mean(lengths, chain.equilibrium_predictions()['mean_r'])
            self.assert_sample_mean(lengths**2, chain.equilibrium_predictions()['mean_r2'])
            self.assert_sample_mean(c, langevin(x))
            self.assert_sample_mean(q[:, 0]/lengths[:, 0, None], np.zeros(3))

    def test_homogeneous_and_heterogeneous_end_to_end_correlations(self):
        for chain in (Chain.homogeneous(5, kappa=0), Chain.homogeneous(5, kappa=2),
                      Chain([0, 0.7, 1.3, 1, 2], [2, 5, 10, 20, 50], [0, 0.01, 3, 0, 10, 0])):
            r = chain.sample(16000, np.random.default_rng(4811), kbt=1.7)
            q = np.diff(r, axis=1)
            lengths = np.linalg.norm(q, axis=2)
            u = q/lengths[:, :, None]
            pred = chain.equilibrium_predictions(1.7)
            self.assert_sample_mean(lengths, pred['mean_r'])
            self.assert_sample_mean(lengths**2, pred['mean_r2'])
            self.assert_sample_mean(np.sum(r[:, -1]**2, axis=1), pred['re2'])
            for i in range(chain.n):
                for j in range(i+1, chain.n):
                    expected = math.prod(langevin(k/1.7) for k in chain.kappa[i+1:j+1])
                    self.assert_sample_mean(np.sum(u[:, i]*u[:, j], axis=1), expected)
            # Different radial bonds are independent even with bending.
            self.assert_sample_mean((lengths[:, 0]-pred['mean_r'][0])
                                    * (lengths[:, 1]-pred['mean_r'][1]), 0)

    def test_radial_independence_of_bending(self):
        lengths = []
        for k in (0, 2, 1000):
            chain = Chain.homogeneous(4, kappa=k)
            r = chain.sample(8000, np.random.default_rng(724))
            lengths.append(np.linalg.norm(np.diff(r, axis=1), axis=2))
        for r in lengths[1:]:
            # Identical radial draws under a common RNG seed; only Cartesian
            # accumulation/rotation roundoff differs. Stronger than mean tests.
            np.testing.assert_allclose(r, lengths[0], rtol=4e-15, atol=4e-15)

    def test_end_to_end_prediction_independent_transfer_integration(self):
        chain = Chain([0.4, 1, 2], [3, 10, 5], [0, 0.3, 4, 0])
        means, seconds = [], []
        for b, k in zip(chain.b0, chain.kb):
            r, w, z = radial_grid(b, k)
            means.append(simpson(w*r, r[1]-r[0])/z)
            seconds.append(simpson(w*r*r, r[1]-r[0])/z)
        # Integrate conditional polar cosines AND relative azimuth explicitly;
        # evaluate Cartesian Re^2 rather than duplicating the product formula.
        c = np.linspace(-1, 1, 401)
        phi = (np.arange(32)+0.5)*2*np.pi/32
        c1, c2 = c[:, None], c[None, :]
        s1, s2 = np.sqrt(1-c1*c1), np.sqrt(1-c2*c2)
        observable = np.zeros((len(c), len(c)))
        for azimuth in phi:
            u2x = c2*s1 + s2*np.cos(azimuth)*c1
            u2y = s2*np.sin(azimuth)
            u2z = c2*c1 - s2*np.cos(azimuth)*s1
            rx = means[1]*s1 + means[2]*u2x
            ry = means[2]*u2y
            rz = means[0] + means[1]*c1 + means[2]*u2z
            observable += (rx*rx + ry*ry + rz*rz)/len(phi)
        observable += np.sum(np.array(seconds)-np.array(means)**2)
        w1, w2 = np.exp(0.3*(c-1)), np.exp(4*(c-1))
        weighted = observable*w1[:, None]*w2[None, :]
        inner = np.array([simpson(row, 0.005) for row in weighted])
        expected = simpson(inner, 0.005)/(simpson(w1, 0.005)*simpson(w2, 0.005))
        self.assertAlmostEqual(chain.equilibrium_predictions()['re2'], expected, delta=2e-8)


if __name__ == '__main__':
    unittest.main(verbosity=2)
