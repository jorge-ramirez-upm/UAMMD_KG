"""D1.6E standalone deterministic verification — PREPARED, UNEXECUTED.

Review before user execution. Explicit actions: --quadrature, --tests, --symbolic.
No default action, RNG, trajectories, production imports, or evidence inputs.
Standard library except the optional --symbolic action, which requires SymPy.
Not named test_*.py and not integrated into any build/test target.
"""

import argparse
import json
import math
import unittest


def simpson(function, left, right, panels):
    if panels <= 0 or panels % 2:
        raise ValueError('Simpson panels must be positive and even')
    step = (right - left) / panels
    terms = (function(left + j * step) * (4 if j % 2 else 2)
             for j in range(1, panels))
    return step / 3 * math.fsum((function(left), function(right), math.fsum(terms)))


def radial_closed(kb, b0, thermal):
    a = kb / (2 * thermal)
    i0 = math.sqrt(math.pi) / (2 * math.sqrt(a)) * math.erfc(-math.sqrt(a) * b0)
    i1 = b0 * i0 + math.exp(-a * b0 * b0) / (2 * a)
    i2 = b0 * i1 + i0 / (2 * a)
    return {'I0': i0, 'I1': i1, 'I2': i2, 'A': i1 / i2, 'B': i0 / i2}


def radial_quadrature(kb, b0, thermal, panels, cutoff=12):
    # Cancel l^-1/l^-2 against the radial Jacobian BEFORE evaluating at l=0.
    a = kb / (2 * thermal)
    upper = b0 + cutoff * math.sqrt(thermal / kb)
    weight = lambda length: math.exp(-a * (length - b0) ** 2)
    integrals = [simpson(lambda length, n=n: length ** n * weight(length),
                         0, upper, panels) for n in range(3)]
    variance = simpson(lambda length: (length - b0) ** 2 * length ** 2 * weight(length),
                       0, upper, panels) / integrals[2]
    # Positive Gaussian-tail upper bounds, independent of grid refinement.
    t0 = math.sqrt(a) * (upper - b0)
    exponential = math.exp(-t0 * t0)
    j0 = exponential / (2 * t0)  # upper bound, not erfc subtraction
    j1 = exponential / 2
    j2 = (t0 * exponential + j0) / 2
    tails = [j0 / math.sqrt(a),
             b0 * j0 / math.sqrt(a) + j1 / a,
             b0 * b0 * j0 / math.sqrt(a) + 2 * b0 * j1 / a + j2 / a ** 1.5]
    return {'I0': integrals[0], 'I1': integrals[1], 'I2': integrals[2],
            'A': integrals[1] / integrals[2], 'B': integrals[0] / integrals[2],
            'stretch_variance': variance, 'upper': upper, 'tail_bounds': tails}


def angular_closed(x):
    if x < 0:
        raise ValueError('This preparation covers nonnegative stiffness')
    if x == 0:
        return {'normalizer': 2.0, 'C': 0.0, 'D': 1 / 3}
    normalizer = -math.expm1(-2 * x) / x
    if x < 0.001:
        cosine = x / 3 - x ** 3 / 45 + 2 * x ** 5 / 945
        squared = 1 / 3 + 2 * x * x / 45 - 4 * x ** 4 / 945
    else:
        cosine = 1 + 2 * math.exp(-2 * x) / (-math.expm1(-2 * x)) - 1 / x
        squared = 1 - 2 * cosine / x
    return {'normalizer': normalizer, 'C': cosine, 'D': squared}


def angular_quadrature(x, panels):
    # exp[x(c-1)] has maximum 1; avoids unnecessary exp(+x) scaling.
    values = [simpson(lambda c, n=n: c ** n * math.exp(x * (c - 1)),
                      -1, 1, panels) for n in range(3)]
    return {'normalizer': values[0], 'C': values[1] / values[0],
            'D': values[2] / values[0]}


def backbone_square(n, kb, b0, thermal, kappa, radial, angular):
    stretch = 2 * n * kb * (3 - 2 * b0 * radial['A'])
    bend = (n - 1) * (8 * kappa * angular['C'] * radial['B']
                       + 2 * kappa * (1 + angular['D']) * radial['A'] ** 2)
    return thermal * (stretch + bend) / (n + 1)


def em_coefficient(backbone, mobility, spring_k, ms2):
    # spring_k=0 is only an algebraic removal check, not a normalized E1 target.
    return mobility * mobility * (backbone + spring_k * spring_k * ms2)


def close(actual, target, tolerance, label):
    if not math.isfinite(actual) or abs(actual - target) > tolerance:
        raise AssertionError(f'{label}: {actual!r} versus {target!r}, atol={tolerance}')


def quadrature_report():
    n, kb, b0, thermal, zeta, ms2 = 32, 30.0, 1.0, 1.0, 1.0, 5.0
    exact_radial = radial_closed(kb, b0, thermal)
    rows = []
    for panels in (256, 512, 1024, 2048, 4096, 8192):
        radial = radial_quadrature(kb, b0, thermal, panels)
        row = {'panels': panels, 'radial': radial,
               'radial_probability_mass': radial['I2'] / exact_radial['I2'], 'cases': {}}
        for kappa in (0.0, 10.0):
            angular = angular_quadrature(kappa / thermal, panels)
            analytic = angular_closed(kappa / thermal)
            backbone = backbone_square(n, kb, b0, thermal, kappa, radial, angular)
            row['cases'][str(int(kappa))] = {
                'angular': angular,
                'angular_probability_mass': angular['normalizer'] / analytic['normalizer'],
                'backbone_force_square_site': backbone,
                'em_h2_coefficient': em_coefficient(backbone, 1 / zeta, 3 * thermal / ms2, ms2)}
        rows.append(row)
    final, previous = rows[-1], rows[-2]
    for key in ('A', 'B'):
        close(final['radial'][key], previous['radial'][key], 1e-10, key + ' refinement')
        close(final['radial'][key], exact_radial[key], 1e-10, key + ' half-line identity')
    for key in ('I0', 'I1', 'I2'):
        close(final['radial'][key], exact_radial[key], 1e-10, key + ' absolute normalization')
    if max(final['radial']['tail_bounds']) > 1e-20:
        raise AssertionError('Radial tail bound exceeds preparation budget')
    close(final['radial_probability_mass'], 1, 1e-10, 'radial normalization')
    coefficients = {}
    for kappa in (0.0, 10.0):
        key = str(int(kappa))
        case = final['cases'][key]
        analytic = angular_closed(kappa / thermal)
        for moment in ('C', 'D'):
            close(case['angular'][moment], analytic[moment], 1e-10, key + moment + ' identity')
            close(case['angular'][moment], previous['cases'][key]['angular'][moment],
                  1e-10, key + moment + ' refinement')
        close(case['angular_probability_mass'], 1, 1e-10, key + ' angular normalization')
        independent = em_coefficient(
            backbone_square(n, kb, b0, thermal, kappa, exact_radial, analytic),
            1 / zeta, 3 * thermal / ms2, ms2)
        close(case['em_h2_coefficient'], independent, 2e-8, key + ' coefficient identity')
        close(case['em_h2_coefficient'], previous['cases'][key]['em_h2_coefficient'],
              2e-8, key + ' coefficient refinement')
        coefficients[key] = independent
    # Independent kappa=0 force-square route: direct radial stretch-force square.
    direct = 2 * n * kb * kb * final['radial']['stretch_variance'] / (n + 1)
    close(final['cases']['0']['backbone_force_square_site'], direct, 2e-8,
          'flexible direct force-square identity')
    # Check farther cutoff independently; do not use cutoff agreement as a tail proof.
    farther = radial_quadrature(kb, b0, thermal, 8192, cutoff=14)
    for key in ('A', 'B'):
        close(final['radial'][key], farther[key], 1e-10, key + ' cutoff sensitivity')
    # External supplied decimals are comparisons AFTER the independent calculations.
    external = {'A': 0.967741936179418, 'B': 0.967741914617288,
                'coefficient_0': 63.73548379003136, 'coefficient_10': 161.21348857512433}
    for key in ('A', 'B'):
        close(final['radial'][key], external[key], 1e-10, key + ' supplied comparison')
    for key in ('0', '10'):
        close(final['cases'][key]['em_h2_coefficient'], external['coefficient_' + key],
              2e-8, key + ' supplied coefficient comparison')
    return {'status': 'DETERMINISTIC_CHECKS_COMPLETED_BY_EXPLICIT_INVOCATION',
            'parameters': {'N': n, 'kb': kb, 'b0': b0, 'kBT': thermal, 'zeta': zeta, 'ms2': ms2},
            'radial_half_line_identities': exact_radial, 'closed_coefficients': coefficients,
            'grids': rows, 'farther_cutoff': farther, 'external_comparisons': external,
            'qualification': 'Floating-point engineering checks, not certified interval bounds or simulator validation.'}


class MathematicalChecks(unittest.TestCase):
    def test_bead_incidence_metric_includes_both_endpoints(self):
        for n in (1, 2, 5):
            incidence = [[int(bead == bond + 1) - int(bead == bond)
                          for bond in range(n)] for bead in range(n + 1)]
            for i in range(n):
                self.assertEqual(sum(row[i] for row in incidence), 0)
                for j in range(n):
                    metric = sum(row[i] * row[j] for row in incidence)
                    self.assertEqual(metric, 2 if i == j else (-1 if abs(i - j) == 1 else 0))

    def test_gaussian_bond_limit_and_endpoint_count(self):
        kb, thermal = 3.0, 2.0
        radial = radial_closed(kb, 0, thermal)
        close(radial['A'], 2 * math.sqrt(kb / (2 * thermal * math.pi)), 1e-14, 'Maxwell A')
        close(radial['B'], kb / thermal, 1e-14, 'Maxwell B')
        for n in (1, 2, 32):
            actual = backbone_square(n, kb, 0, thermal, 0, radial, angular_closed(0))
            close(actual, 6 * n * kb * thermal / (n + 1), 1e-12, 'Gaussian backbone')

    def test_no_angle_for_one_bond(self):
        radial = radial_closed(30, 1, 1)
        close(backbone_square(1, 30, 1, 1, 10, radial, angular_closed(10)),
              backbone_square(1, 30, 1, 1, 0, radial, angular_closed(0)), 1e-14, 'N=1')

    def test_small_angular_stiffness_is_regular(self):
        for x in (0.0, 1e-5, 10.0):
            numerical, analytic = angular_quadrature(x, 8192), angular_closed(x)
            for key in ('C', 'D'):
                close(numerical[key], analytic[key], 1e-10, 'angular limit ' + key)

    def test_zero_virtual_force_is_only_an_algebraic_limit(self):
        backbone = 7.0  # toy coefficient, not an evaluated nonlinear reference
        self.assertEqual(em_coefficient(backbone, 2, 0, 5), 4 * backbone)
        # For the normalized family, ms2=3*T/k; its added coefficient is 3*mu²*T*k.
        for k in (1.0, 0.1, 0.01):
            close(em_coefficient(backbone, 2, k, 3 / k) - 4 * backbone,
                  12 * k, 1e-12, 'normalized one-sided k limit')

    def test_quadratic_em_identity_has_no_extra_half(self):
        # Harmonic toy ONLY: exact equilibrium scalar second moment v=T/k.
        thermal, mobility, k, h = 2.0, 0.5, 3.0, 0.01
        v = thermal / k
        next_second = (1 - mobility * k * h) ** 2 * v + 2 * mobility * thermal * h
        close(next_second - v, h * h * mobility * mobility * k * thermal,
              1e-14, 'exact scalar EM defect')


def symbolic_checks():
    # Differentiate the Cartesian Hamiltonian BEFORE selecting a convenient frame.
    import sympy as s
    q = s.Matrix(s.symbols('q0:3', real=True))
    p = s.Matrix(s.symbols('p0:3', real=True))
    length, other = s.sqrt(q.dot(q)), s.sqrt(p.dot(p))
    kb, b0, kappa, ell, m = s.symbols('kb b0 kappa ell m', positive=True)
    c = s.symbols('c', real=True)
    frame = {q[0]: ell, q[1]: 0, q[2]: 0,
             p[0]: m * c, p[1]: m * s.sqrt(1 - c * c), p[2]: 0}
    stretch = kb * (length - b0) ** 2 / 2
    angle = kappa * (1 - q.dot(p) / (length * other))
    lap_stretch = sum(s.diff(stretch, variable, 2) for variable in q)
    lap_q = sum(s.diff(angle, variable, 2) for variable in q)
    lap_p = sum(s.diff(angle, variable, 2) for variable in p)
    mixed = sum(s.diff(angle, q[j], p[j]) for j in range(3))
    identities = (
        (lap_stretch, kb * (3 - 2 * b0 / ell)),
        (lap_q, 2 * kappa * c / ell ** 2),
        (lap_p, 2 * kappa * c / m ** 2),
        (mixed, -kappa * (1 + c * c) / (ell * m)),
        (2 * lap_q + 2 * lap_p - 2 * mixed,
         4 * kappa * c * (1 / ell ** 2 + 1 / m ** 2) + 2 * kappa * (1 + c * c) / (ell * m)))
    for derived, proposed in identities:
        remainder = s.simplify(derived.subs(frame, simultaneous=True) - proposed)
        if remainder != 0:
            raise AssertionError(f'Symbolic identity unresolved: {remainder}')
    print('Five Cartesian symbolic identities checked; no sampling or dynamics.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--quadrature', action='store_true')
    action.add_argument('--tests', action='store_true')
    action.add_argument('--symbolic', action='store_true')
    options = parser.parse_args()
    if options.quadrature:
        print(json.dumps(quadrature_report(), indent=2, allow_nan=False))
    elif options.tests:
        unittest.main(argv=[__file__])
    else:
        symbolic_checks()
