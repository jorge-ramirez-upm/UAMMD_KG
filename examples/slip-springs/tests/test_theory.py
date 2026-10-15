"""Independent matrix references for the scalar mode formulas and estimators."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile
import numpy as np

spec = importlib.util.spec_from_file_location('validation', Path(__file__).resolve().parents[1]/'validate.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class TheoryTests(unittest.TestCase):
    def test_modes_against_matrix(self):
        for n in (1, 2, 8, 32, 100):
            m = n+1
            incidence = np.zeros((n, m))
            for j in range(n):
                incidence[j, j:j+2] = [-1, 1]
            stiffness = 3*incidence.T@incidence
            eigenvalues = np.linalg.eigvalsh(stiffness)[1:]
            np.testing.assert_allclose(v.modes(n)[0], eigenvalues, rtol=1e-11)
            exact = [1, n, n*(n+2)/(6*m)]
            np.testing.assert_allclose(v.dimensions(n, .01, 0), exact, rtol=1e-12)
            # Iterate the full COM-free covariance independently, including additive noise.
            projector = np.eye(m)-np.ones((m, m))/m
            covariance = np.linalg.pinv(stiffness, hermitian=True)
            transition = np.eye(m)-.01*stiffness
            for step in range(12):
                expected = [np.trace(incidence@covariance@incidence.T)*3/n,
                            3*(covariance[0, 0]+covariance[-1, -1]-2*covariance[0, -1]),
                            3*np.trace(projector@covariance)/m]
                np.testing.assert_allclose(v.dimensions(n, .01, step), expected, rtol=2e-11)
                covariance = transition@covariance@transition.T+.02*projector
            end = np.zeros(m); end[0] = -1; end[-1] = 1
            covariance = np.linalg.pinv(stiffness, hermitian=True)
            propagator = np.linalg.matrix_power(transition, 7)
            expected = (end@propagator@covariance@end)/(end@covariance@end)
            self.assertAlmostEqual(v.correlation(n, .01, np.array([0]), 7), expected, places=11)
            self.assertAlmostEqual(v.correlation(n, .01, [0], 0, continuous=True), 1)

    def test_decimal_timestep_log_names(self):
        with tempfile.TemporaryDirectory(prefix='rouse-lognames-') as tmp:
            with patch.object(v.subprocess, 'run') as execute, patch.object(v, 'analyze', return_value={}):
                for name in ('N8_dt0.01', 'N8_dt0.005'):
                    output = Path(tmp)/name
                    output.mkdir()
                    # run() must refuse existing directories; the fake child creates it below.
                    output.rmdir()
                    execute.side_effect = lambda *args, **kwargs: output.mkdir()
                    v.run(Path('/unused'), output, [])
                self.assertEqual(len(list(Path(tmp).glob('*.log'))), 2)

    def test_validation_duration(self):
        for n in (8, 32, 100):
            for dt in (.01, .005, .0025):
                interval, steps = v.schedule(n, dt)
                self.assertEqual(steps, 40*interval)
                self.assertGreaterEqual(steps*dt, 1.25/v.modes(n)[0][0])

    def test_ratio_uncertainty(self):
        x = np.array([1., 3., 2., 6.])
        d = np.ones(4)*2
        value, se = v.ratio(x, d)
        self.assertEqual(value, 1.5)
        self.assertAlmostEqual(se, np.std(x/2, ddof=1)/2)
        self.assertFalse(v.record('bad', 3, .1, 0)['passed'])

if __name__ == '__main__':
    unittest.main()
