import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain
import timestep_preselector as selector


class PreselectorTest(unittest.TestCase):
    def test_hessian_against_force_differences(self):
        models = [Chain.homogeneous(3, kappa=k) for k in (0., 10.)]
        models.append(Chain([.7, 1., 1.2], [12., 30., 18.], [0., 3., 8., 0.]))
        for model in models:
            for positions in model.sample(2, np.random.default_rng(91)):
                analytic = selector.hessian(model, positions)
                finite = np.empty_like(analytic)
                for i in range(positions.size):
                    offset = np.zeros_like(positions)
                    offset.flat[i] = 2e-6
                    plus = model.energy_forces(positions+offset)[1]
                    minus = model.energy_forces(positions-offset)[1]
                    finite[:, i] = -(plus-minus).ravel()/4e-6
                np.testing.assert_allclose(analytic, finite, rtol=2e-7, atol=2e-7)
                np.testing.assert_allclose(analytic, analytic.T, atol=1e-12)

    def test_translation_and_rotation_at_nonstationary_configuration(self):
        model = Chain.homogeneous(4, kappa=10.)
        r = model.sample(1, np.random.default_rng(28))[0]
        h = selector.hessian(model, r)
        translations = np.tile(np.eye(3), (5, 1))
        np.testing.assert_allclose(h@translations, 0., atol=2e-13)
        np.testing.assert_allclose(h, selector.hessian(model, r+[3., -2., 1.]), atol=2e-12)
        rotation, _ = np.linalg.qr(np.random.default_rng(17).normal(size=(3, 3)))
        transform = np.kron(np.eye(5), rotation)
        np.testing.assert_allclose(selector.hessian(model, r@rotation.T), transform@h@transform.T, atol=2e-12)
        gradient = -model.energy_forces(r)[1]
        for axis in np.eye(3):
            displacement = np.cross(axis, r)
            np.testing.assert_allclose(h@displacement.ravel(), np.cross(axis, gradient).ravel(), atol=2e-12)
        self.assertGreater(np.linalg.norm(h@displacement.ravel()), 1.)
        basis = selector.internal_basis(4)
        np.testing.assert_allclose(basis.T@basis, np.eye(12), atol=1e-14)
        np.testing.assert_allclose(basis.T@translations, 0., atol=1e-14)
        bad = h.copy(); bad[0, 0] += .01
        with self.assertRaisesRegex(ValueError, 'translation/symmetry'): selector.spectrum(bad, basis)

    def test_stationary_rotations_and_free_end_modes(self):
        n = 4
        r = np.zeros((n+1, 3)); r[:, 0] = np.arange(n+1)
        expected_longitudinal = 4*30*np.sin(np.arange(1, n+1)*np.pi/(2*(n+1)))**2
        for kappa in (0., 10.):
            h = selector.hessian(Chain.homogeneous(n, kappa=kappa), r)
            np.testing.assert_allclose(np.linalg.eigvalsh(h[::3, ::3])[1:], expected_longitudinal, atol=1e-12)
            for axis in np.eye(3):
                np.testing.assert_allclose(h@np.cross(axis, r).ravel(), 0., atol=1e-12)
            report = selector.spectrum(h, selector.internal_basis(n))
            self.assertEqual(report['numerical_zero_modes'], 2*n if kappa == 0 else 2)
            self.assertEqual(report['negative_eigenvalues'], [])
        gaussian = selector.hessian(Chain.homogeneous(n, b0=0.), r)
        np.testing.assert_allclose(np.linalg.eigvalsh(gaussian)[3:], np.repeat(expected_longitudinal, 3), atol=1e-12)

    def test_negative_curvature_and_single_bond_boundary(self):
        r = np.array([[0., 0., 0.], [.5, 0., 0.]])
        h = selector.hessian(Chain.homogeneous(1), r)
        result = selector.spectrum(h, selector.internal_basis(1))
        np.testing.assert_allclose(result['negative_eigenvalues'], [-60., -60.], atol=1e-12)
        self.assertAlmostEqual(result['lambda_max'], 60.)
        self.assertEqual(result['numerical_zero_modes'], 0)

    def test_report_quantiles_scaling_and_reproducibility(self):
        a = selector.preselect(n=3, configurations=8, seed=6)
        b = selector.preselect(n=3, configurations=8, seed=6, zeta=2., c=.1)
        self.assertEqual(a['configurations'], b['configurations'])
        expected = np.quantile([r['lambda_max'] for r in a['configurations']], [.5, .95, .99, 1.])
        np.testing.assert_allclose(list(a['lambda_max_distribution'].values()), expected)
        self.assertAlmostEqual(a['harmonic_approximation']['tau_est'], 1/280)
        self.assertAlmostEqual(a['harmonic_approximation']['dt_est'], .05/280)
        self.assertAlmostEqual(a['dt_suggested'], .05/expected[2])
        self.assertAlmostEqual(b['dt_suggested'], 4*a['dt_suggested'])
        self.assertEqual(a['numerical_modes']['rotations_removed'], 0)
        json.dumps(a, allow_nan=False)

    def test_geometry_and_condition_diagnostics(self):
        samples = np.array([[[0., 0., 0.], [.01, 0., 0.]], [[0., 0., 0.], [1.-1e-10, 0., 0.]]])
        with patch.object(Chain, 'sample', return_value=samples):
            result = selector.preselect(n=1, kappa=0., configurations=2)
        self.assertEqual(result['diagnostics']['very_short_bond_indices'], [0])
        self.assertEqual(result['diagnostics']['poorly_conditioned_indices'], [1])
        self.assertEqual(result['diagnostics']['configurations_with_negative_curvature'], 2)
        with self.assertRaises(ValueError): selector.hessian(Chain.homogeneous(1), np.zeros((2, 3)))

    def test_cli_and_invalid_inputs(self):
        script = Path(selector.__file__)
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp)/'result.json'
            argv = [sys.executable, str(script), '--N', '2', '--kappa', '0', '--configurations', '3', '--report', str(report)]
            subprocess.run(argv, check=True, timeout=20)
            result = json.loads(report.read_text())
            self.assertEqual(result['parameters']['N'], 2)
            self.assertEqual(result['parameters']['c'], .05)
            previous = report.read_bytes()
            self.assertNotEqual(subprocess.run(argv, capture_output=True, timeout=20).returncode, 0)
            self.assertEqual(report.read_bytes(), previous)
        for kwargs in ({'b0': 0.}, {'kb': -1.}, {'kappa': -1.}, {'zeta': float('nan')},
                       {'c': 0.}, {'n': 0}, {'configurations': 0}, {'seed': -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): selector.preselect(**kwargs)


if __name__ == '__main__': unittest.main()
