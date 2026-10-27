"""D1.6F exact-algebra specifications — PREPARED, UNEXECUTED.

Future explicit user command after independent review, NOT run in preparation:
python3 examples/slip-springs/tests/d16f_math_regression.py --tests

Standard-library rational algebra only. No RNG, sampling, quadrature, dynamics,
production imports, or evidence reads. Not discovered by test_*.py patterns.
The matrices are analytical toys; these tests cannot verify full E1 kernels.
"""

import argparse
from fractions import Fraction as Q
import unittest


def transpose(a):
    return [list(row) for row in zip(*a)]


def multiply(a, b):
    return [[sum(x * y for x, y in zip(row, column)) for column in zip(*b)] for row in a]


def scale(c, a):
    return [[c * x for x in row] for row in a]


def add(*matrices):
    return [[sum(items) for items in zip(*rows)] for rows in zip(*matrices)]


def identity(n):
    return [[Q(int(i == j)) for j in range(n)] for i in range(n)]


def inverse2(a):
    determinant = a[0][0] * a[1][1] - a[0][1] * a[1][0]
    return scale(1 / determinant, [[a[1][1], -a[0][1]], [-a[1][0], a[0][0]]])


class D16FExactAlgebra(unittest.TestCase):
    def test_reversible_counterexample_local_and_stationary_signs(self):
        generator = scale(Q(1, 3), [[-5, 4, 1], [4, -8, 4], [1, 4, -5]])
        self.assertEqual(generator, transpose(generator))
        source = [-1, -2, 3]
        defect = scale(Q(1, 3), [source] * 3)
        observable = [[4], [0], [2]]
        equilibrium = [[Q(1, 3)] * 3]
        density_response = [Q(-3, 4), Q(-1, 2), Q(5, 4)]
        self.assertEqual(multiply([density_response], generator), [[-x for x in source]])
        local = multiply(multiply(equilibrium, defect), observable)[0][0]
        response = multiply(scale(Q(1, 3), [density_response]), observable)[0][0]
        self.assertEqual(local, Q(2, 3))
        self.assertEqual(response, Q(-1, 6))
        for h in (Q(1, 4), Q(1, 10), Q(1, 100)):
            kernel = add(identity(3), scale(h, generator), scale(h * h, defect))
            self.assertTrue(all(x >= 0 for row in kernel for x in row))
            self.assertTrue(all(sum(row) == 1 for row in kernel))
            invariant = [[(1 + h * x) / 3 for x in density_response]]
            self.assertEqual(multiply(invariant, kernel), invariant)
            self.assertEqual(multiply(invariant, observable)[0][0], 2 - h / 6)
            self.assertEqual(multiply(multiply(equilibrium, kernel), observable)[0][0] - 2,
                             Q(2, 3) * h * h)

    def test_counterexample_spectral_and_correlation_integrals(self):
        # The two cross-correlation weights are -4/3 and 2, with decay rates 2,4.
        self.assertEqual(-Q(4, 3) + 2, Q(2, 3))
        self.assertEqual(-Q(4, 3) / 2 + Q(2) / 4, Q(-1, 6))

    def test_backward_order_and_modified_generator_have_same_source(self):
        # Algebra toy: B,J reversible for uniform pi, C a row-sum-zero defect.
        b = [[-1, 1, 0], [1, -1, 0], [0, 0, 0]]
        j = [[0, 0, 0], [0, -1, 1], [0, 1, -1]]
        c = scale(Q(1, 3), [[-1, -2, 3]] * 3)
        equilibrium = [[Q(1, 3)] * 3]
        l = add(b, j)
        a2 = add(c, multiply(b, j), scale(Q(1, 2), multiply(j, j)))
        modified = add(a2, scale(Q(-1, 2), multiply(l, l)))
        self.assertNotEqual(multiply(b, j), multiply(j, b))
        self.assertEqual(multiply(equilibrium, a2), multiply(equilibrium, c))
        self.assertEqual(multiply(equilibrium, modified), multiply(equilibrium, c))
        self.assertNotEqual(a2, modified)

    def test_harmonic_scalar_stationary_response(self):
        thermal, mobility, k, h = Q(2), Q(1, 2), Q(3), Q(1, 10)
        rate, variance = mobility * k, thermal / k
        stationary = variance / (1 - rate * h / 2)
        self.assertEqual(stationary, (1 - rate * h) ** 2 * stationary + 2 * mobility * thermal * h)
        local_coefficient = rate * rate * variance
        self.assertEqual(local_coefficient / (2 * rate), mobility * thermal / 2)

    def test_coupled_harmonic_lyapunov_and_response(self):
        gamma, k, thermal, mobility, h = Q(2), Q(3), Q(1), Q(1, 2), Q(1, 10)
        stiffness = [[gamma + k, -gamma], [-gamma, gamma]]
        # Gershgorin supplies a sufficient stable step without numerical eigenvalues.
        self.assertLess(mobility * h * max(sum(abs(x) for x in row) for row in stiffness), 2)
        sigma0 = scale(thermal, inverse2(stiffness))
        factor = inverse2(add(identity(2), scale(-mobility * h / 2, stiffness)))
        sigma = multiply(sigma0, factor)
        update = add(identity(2), scale(-mobility * h, stiffness))
        self.assertEqual(sigma, add(multiply(multiply(update, sigma), transpose(update)),
                                    scale(2 * mobility * thermal * h, identity(2))))
        self.assertEqual(sigma0[0][0], thermal / k)
        response = scale(mobility * thermal / 2, identity(2))
        source = scale(mobility * mobility * thermal, stiffness)
        self.assertEqual(scale(mobility, add(multiply(stiffness, response), multiply(response, stiffness))), source)
        difference = add(sigma, scale(-1, sigma0))
        self.assertGreater(difference[0][0], 0)
        self.assertGreater(difference[0][0] * difference[1][1] - difference[0][1] ** 2, 0)
        a = mobility * h / 2
        formula = mobility * thermal * h / 2 * (1 - a * gamma) / (1 - a * (2 * gamma + k) + a * a * gamma * k)
        self.assertEqual(difference[0][0], formula)

    def test_gaussian_refresh_stationary_identity(self):
        # q denotes exp(-rho*h), kept rational for an exact fixed-step identity.
        rate, variance, h, q = Q(2), Q(3, 2), Q(1, 10), Q(4, 5)
        diffusion = rate * variance
        stationary = (q * 2 * diffusion * h + (1 - q) * variance) / (1 - q * (1 - rate * h) ** 2)
        defect = q * rate * rate * h * h * variance / (1 - q * (1 - rate * h) ** 2)
        self.assertEqual(stationary - variance, defect)
        self.assertGreater(defect, 0)
        # Leading-response algebra: known eigenvalue, not an inferred E1 timescale.
        rho = Q(3)
        response = rate * rate * variance / (2 * rate + rho)
        self.assertEqual(response * (2 * rate + rho), rate * rate * variance)

    def test_hop_reflection_geometry_and_static_gaussian_pairing(self):
        e, d = (Q(1), Q(-2), Q(3)), (Q(2), Q(1), Q(-1))
        reflected = tuple(-x - y for x, y in zip(e, d))
        square = lambda vector: sum(x * x for x in vector)
        shifted = tuple(x + y for x, y in zip(e, d))
        shifted_reflected = tuple(x + y for x, y in zip(reflected, d))
        self.assertEqual(square(reflected), square(shifted))
        self.assertEqual(square(shifted_reflected), square(e))
        self.assertEqual(square(shifted_reflected) - square(reflected), -(square(shifted) - square(e)))
        thermal, mobility, k, z = Q(1), Q(2), Q(3, 5), 4
        variance = thermal / k
        radial_sum_variance = 6 * z * variance * variance
        pairing = mobility * k * k / (4 * thermal) * radial_sum_variance / z
        self.assertEqual(pairing, 3 * mobility * thermal / 2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tests', action='store_true', required=True)
    parser.parse_args()
    unittest.main(argv=[__file__])
