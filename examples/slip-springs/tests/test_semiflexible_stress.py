"""Bounded independent CPU stress checks; no GPU or dynamics invocation."""
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain
import semiflexible_stress_reference as stress


def metric_angle_tensor(a, b, k):
    # Independently differentiate the cosine with respect to F^T F, eliminating
    # bond lengths before tensor construction. No forces or A/B gradients.
    u, v = a/np.linalg.norm(a), b/np.linalg.norm(b)
    c = np.dot(u, v)
    return k*(c*(np.outer(u, u)+np.outer(v, v))-np.outer(u, v)-np.outer(v, u))


class StressTests(unittest.TestCase):
    def setUp(self):
        self.r = np.array([[0.2, -0.4, 0.1], [1.1, 0.2, -0.1],
                           [1.5, 1.3, 0.4], [0.9, 1.6, 1.1], [1.3, 2.2, 1.4]])
        self.hetero = Chain([0.7, 1, 0, 1.2], [3, 7, 2, 11], [0, 0.1, 0, 8, 0])
        self.nearly = np.array([[0, 0, 0], [1, 0, 0], [2, 1e-7, 0],
                                [1, 2e-7, 0], [0, 1e-7, 1e-8]])

    def test_affine_derivatives_all_entries_and_deformation_types(self):
        basis = []
        for index in np.ndindex((3, 3)):
            e = np.zeros((3, 3));e[index] = 1
            basis.append(e)
        basis += [np.eye(3), np.diag([1, -2, 0.5]),
                  np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]]),
                  np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 0]]),
                  np.random.default_rng(43101).normal(size=(3, 3))]
        for model in (self.hetero, Chain.homogeneous(4, kb=4, kappa=2),
                      Chain.homogeneous(4, kb=4, kappa=1000)):
            for r in (self.r, self.nearly):
                tensors = stress.virials(model, r)
                methods = (model.stretch_energy_forces, model.bend_energy_forces, model.energy_forces)
                for name, energy in zip(('stretch', 'bend', 'total'), methods):
                    scale = max(1, abs(energy(r)[0]), model.kappa.max(), model.kb.max())
                    for e in basis:
                        h = 2e-6
                        plus = r @ (np.eye(3)+h*e).T
                        minus = r @ (np.eye(3)-h*e).T
                        derivative = (energy(plus)[0]-energy(minus)[0])/(2*h)
                        predicted = np.sum(tensors[name]*e)
                        self.assertLessEqual(abs(predicted-derivative),
                                             2e-9*scale*max(1, np.linalg.norm(e))+3e-7*abs(predicted))

    def test_individual_bending_metric_symmetry_trace_and_dilation(self):
        rng = np.random.default_rng(43102)
        pairs = [(rng.normal(size=3), rng.normal(size=3)) for _ in range(12)]
        pairs += [(np.array([1., 0, 0]), np.array([1., 1e-8, 0])),
                  (np.array([1., 0, 0]), np.array([-1., 1e-8, 0])),
                  (np.array([1., 0, 0]), np.array([1., 0, 0])),
                  (np.array([1., 0, 0]), np.array([-1., 0, 0]))]
        for a, b in pairs:
            for k in (1e-9, 2, 1000):
                w = stress.bending_angle_virial(a, b, k)
                floor = 1e-14*max(1, k)
                np.testing.assert_allclose(w, metric_angle_tensor(a, b, k), atol=floor, rtol=2e-13)
                np.testing.assert_allclose(w, w.T, atol=floor, rtol=0)
                self.assertAlmostEqual(np.trace(w), 0, delta=3*floor)
                np.testing.assert_allclose(stress.bending_angle_virial(3*a, 0.7*b, k), w,
                                           atol=3*floor, rtol=2e-13)
        for r in (self.r, self.nearly):
            e = self.hetero.bend_energy_forces(r)[0]
            self.assertAlmostEqual(self.hetero.bend_energy_forces(r*1.031)[0], e, delta=2e-13)
            self.assertAlmostEqual(np.trace(stress.virials(self.hetero, r)['bend']), 0, delta=3e-13)

    def test_force_virial_equivalence_arbitrary_reference(self):
        for model in (self.hetero, Chain.homogeneous(4, kb=4, kappa=0),
                      Chain.homogeneous(4, kb=4, kappa=1000)):
            for r in (self.r, self.nearly):
                tensors = stress.virials(model, r)
                for name, method in zip(('stretch', 'bend', 'total'),
                                        (model.stretch_energy_forces, model.bend_energy_forces, model.energy_forces)):
                    _, forces = method(r)
                    for origin in (np.zeros(3), r[2], np.array([31., -17, 9])):
                        independent = -forces.T @ (r-origin)
                        np.testing.assert_allclose(tensors[name], independent, rtol=2e-12,
                                                   atol=3e-13*max(1, model.kappa.max(), model.kb.max()))

    def test_rotations_translations_and_total_symmetry(self):
        rotation, _ = np.linalg.qr(np.random.default_rng(43103).normal(size=(3, 3)))
        if np.linalg.det(rotation) < 0:
            rotation[:, 0] *= -1
        for r in (self.r, self.nearly):
            original = stress.virials(self.hetero, r)
            shifted = stress.virials(self.hetero, r+[2, -3, 4])
            rotated = stress.virials(self.hetero, r @ rotation.T)
            self.assertAlmostEqual(self.hetero.energy_forces(r @ rotation.T)[0],
                                   self.hetero.energy_forces(r)[0], delta=2e-13)
            for name in ('stretch', 'bend', 'total'):
                np.testing.assert_allclose(shifted[name], original[name], atol=3e-13, rtol=2e-13)
                np.testing.assert_allclose(rotated[name], rotation @ original[name] @ rotation.T,
                                           atol=3e-13, rtol=2e-13)
                np.testing.assert_allclose(original[name], original[name].T, atol=3e-13, rtol=0)

    def test_components_and_rouse_limit(self):
        w = np.array([[1., 2, 3], [2, 5, 7], [3, 7, 11]])
        result = stress.components(w)
        np.testing.assert_array_equal(result['symmetric'], [1, 5, 11, 2, 3, 7])
        np.testing.assert_array_equal(result['shears'], [2, 3, 7])
        np.testing.assert_array_equal(result['normal_differences'], [-4, -10, -6])
        self.assertEqual(stress.DEVIATORIC_ORDER, ('xy', 'xz', 'yz', 'xx-yy', 'xx-zz', 'yy-zz'))
        model = Chain.homogeneous(4, b0=0, kb=3, kappa=0)
        result = stress.virials(model, self.r)
        q = np.diff(self.r, axis=0)
        np.testing.assert_allclose(result['total'], 3*q.T @ q, atol=2e-15)
        np.testing.assert_array_equal(result['bend'], np.zeros((3, 3)))
        self.assertEqual(result['total'].dtype, np.float64)
        # Component extraction does not silently repair a nonsymmetric input.
        raw = w.copy();raw[1, 0] = -99
        self.assertEqual(stress.components(raw)['symmetric'][3], 2)

    def test_one_and_two_bond_closed_form(self):
        model = Chain.homogeneous(1, b0=1, kb=3)
        result = stress.virials(model, [[0, 0, 0], [2, 0, 0]])
        np.testing.assert_array_equal(result['total'], np.diag([6, 0, 0]))
        model = Chain.homogeneous(2, kb=3, kappa=4)
        result = stress.virials(model, [[0, 0, 0], [1, 0, 0], [1, 1, 0]])
        np.testing.assert_array_equal(result['stretch'], np.zeros((3, 3)))
        np.testing.assert_array_equal(result['bend'], [[0, -4, 0], [-4, 0, 0], [0, 0, 0]])
        for end in (2, 0):
            np.testing.assert_array_equal(stress.virials(model, [[0, 0, 0], [1, 0, 0], [end, 0, 0]])['bend'], np.zeros((3, 3)))

    def test_flexible_path_has_no_angular_operations(self):
        model = Chain.homogeneous(4, kappa=0)
        with patch.object(stress, '_bending', side_effect=AssertionError('angular call')):
            with patch.object(stress, 'bending_angle_virial', side_effect=AssertionError('angular geometry')):
                result = stress.virials(model, self.r)
        np.testing.assert_array_equal(result['total'], result['stretch'])
        np.testing.assert_array_equal(result['bend'], np.zeros((3, 3)))
        # A collapsed bond is incident only to inactive angles and is smooth.
        model = Chain([0, 1, 1], [2, 3, 4], [0, 0, 2, 0])
        with patch.object(stress, 'bending_angle_virial', wraps=stress.bending_angle_virial) as calls:
            stress.virials(model, [[0, 0, 0], [0, 0, 0], [1, 0, 0], [1, 1, 0]])
            self.assertEqual(calls.call_count, 1)
            self.assertEqual(calls.call_args.args[-1], 2)

    def test_invalid_parameters_geometry_and_numerics(self):
        for args in (([], [], [0]), ([1], [0], [0, 0]), ([-1], [3], [0, 0]),
                     ([1], [3], [1, 0]), ([1, 1], [3, 3], [0, -1, 0]),
                     ([np.nan], [3], [0, 0])):
            with self.assertRaises(ValueError):
                stress.virials(Chain(*args), [[0, 0, 0], [1, 0, 0]])
        for r in (np.zeros((4, 3)), np.full((5, 3), np.nan), np.full((5, 3), np.inf)):
            with self.assertRaises(ValueError):
                stress.virials(self.hetero, r)
        with self.assertRaises(ValueError):
            stress.virials(Chain.homogeneous(1), [[0, 0, 0], [0, 0, 0]])
        with self.assertRaises(ValueError):
            stress.virials(Chain.homogeneous(2, b0=0, kappa=2), np.zeros((3, 3)))
        np.testing.assert_array_equal(stress.virials(Chain.homogeneous(1, b0=0), np.zeros((2, 3)))['total'], np.zeros((3, 3)))
        for a, b, k in (([0, 0, 0], [1, 0, 0], 1), ([1, 0, 0], [1, 0, 0], -1),
                        ([np.nan, 0, 0], [1, 0, 0], 1), ([1, 0], [1, 0, 0], 1)):
            with self.assertRaises(ValueError):
                stress.bending_angle_virial(a, b, k)
        for w in (np.zeros((2, 2)), np.full((3, 3), np.inf)):
            with self.assertRaises(ValueError):
                stress.components(w)
        with np.errstate(over='ignore', invalid='ignore'):
            with self.assertRaises(ValueError):
                stress.virials(Chain.homogeneous(1, b0=0), [[0, 0, 0], [1e200, 0, 0]])
            with self.assertRaises(ValueError):
                stress.virials(Chain.homogeneous(1, b0=1e200, kb=1), [[0, 0, 0], [1, 0, 0]])
            with self.assertRaises(ValueError):
                stress.bending_angle_virial([1, 0, 0], [-1, 0, 0], 1e308)

    def test_radial_integration_by_parts_identity(self):
        # Independent uniform-grid quadrature; no Cartesian force or virial call.
        def simpson(values, dx):
            return dx/3*(values[0]+values[-1]+4*values[1:-1:2].sum()+2*values[2:-1:2].sum())
        for b0, kb, kbt in ((0, 2, 1.7), (1, 30, 1), (1.2, 11, 0.7), (0.1, 0.3, 2)):
            sigma = math.sqrt(kbt/kb)
            r = np.linspace(0, b0+14*sigma, 40001)
            w = r*r*np.exp(-0.5*((r-b0)/sigma)**2)
            value = simpson(w*kb*(r-b0)*r, r[1])/simpson(w, r[1])
            self.assertAlmostEqual(value, 3*kbt, delta=1e-10*kbt)

    def test_six_channel_isotropic_projection_identity(self):
        rng = np.random.default_rng(43104)
        for _ in range(16):
            a, b = rng.normal(size=(2, 3, 3))
            a, b = a+a.T, b+b.T
            ca, cb = stress.components(a), stress.components(b)
            raw = np.dot(ca['shears'], cb['shears'])/5 + np.dot(ca['normal_differences'], cb['normal_differences'])/30
            da, db = a-np.trace(a)/3*np.eye(3), b-np.trace(b)/3*np.eye(3)
            # Exact projector identity for symmetric tensors, no angular averaging
            # or correlation implementation shared with the existing pipeline.
            self.assertAlmostEqual(raw, np.sum(da*db)/10, delta=3e-15)
            shifted = stress.components(a+7*np.eye(3))
            np.testing.assert_allclose(shifted['normal_differences'], ca['normal_differences'], atol=2e-15)
            np.testing.assert_array_equal(shifted['shears'], ca['shears'])

    def test_isotropic_equilibrium_hydrostatic_and_deviatoric_identity(self):
        examples = [(Chain.homogeneous(1, kb=4), 1.7),
                    (Chain.homogeneous(3, kappa=0), 1),
                    (Chain.homogeneous(3, kappa=2), 1),
                    (Chain.homogeneous(3, kappa=10), 1.7), (self.hetero, 0.7)]
        for case, (model, kbt) in enumerate(examples):
            count = 8192
            samples = model.sample(count, np.random.default_rng(43110+case), kbt)
            ws, wb = np.empty((count, 3, 3)), np.empty((count, 3, 3))
            for i, r in enumerate(samples):
                result = stress.virials(model, r)
                ws[i], wb[i] = result['stretch'], result['bend']
            max_z = 0
            for values, target in ((ws, model.n*kbt*np.eye(3)), (wb, np.zeros((3, 3))),
                                   (ws+wb, model.n*kbt*np.eye(3))):
                mean, se = values.mean(axis=0), values.std(axis=0, ddof=1)/math.sqrt(count)
                self.assertTrue(np.all(np.abs(mean-target) <= 6*se+2e-12), (case, mean, target, se))
                max_z = max(max_z, float(np.max(np.abs(mean-target)/(se+2e-12))))
                deviatoric = np.array([np.r_[stress.components(w)['shears'], stress.components(w)['normal_differences']] for w in values])
                mean, se = deviatoric.mean(axis=0), deviatoric.std(axis=0, ddof=1)/math.sqrt(count)
                self.assertTrue(np.all(np.abs(mean) <= 6*se+2e-12), (case, mean, se))
                max_z = max(max_z, float(np.max(np.abs(mean)/(se+2e-12))))
            # The bending trace vanishes configuration by configuration.
            np.testing.assert_allclose(np.trace(wb, axis1=1, axis2=2), 0,
                                       atol=2e-13*max(1, model.kappa.max()))
            print(f'equilibrium case={case} N={model.n} kbt={kbt} mean_diag_stretch={np.diag(ws.mean(axis=0))} '
                  f'mean_diag_bend={np.diag(wb.mean(axis=0))} max_abs_z={max_z:.4f}', flush=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
