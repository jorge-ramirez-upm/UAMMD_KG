"""D1.6D mathematical specifications — PREPARED, UNEXECUTED.

Independent review and separate authorization must precede execution.
Future explicit command (from repository root), NOT run in D1.6D:
    python3 examples/slip-springs/tests/d16d_math_regression.py

Standard library only. No RNG, sampling, quadrature, simulation, source imports,
CUDA, reference recalculation, or scientific evidence inputs. These finite
algebra/reciprocity fixtures cannot verify compiled production kernels.
The filename deliberately keeps this out of ordinary test_*.py discovery.
"""

from fractions import Fraction as Q
from itertools import combinations, permutations
from math import comb, exp, log, pi, sqrt
import unittest


def energy(r, anchor, k):
    return k * sum((x - a) ** 2 for x, a in zip(r, anchor)) / 2


def log_gaussian(r, anchor, k, thermal):
    return 1.5 * log(k / (2 * pi * thermal)) - float(energy(r, anchor, k) / thermal)


def links(sites, m):
    """Independent contour-sort specification; ID is tuple position."""
    result = {}
    for chain in sorted({site // m for site in sites}):
        ids = sorted((j for j, s in enumerate(sites) if s // m == chain),
                     key=lambda j: sites[j])
        for rank, j in enumerate(ids):
            result[j] = (ids[rank - 1] if rank else -1,
                         ids[rank + 1] if rank + 1 < len(ids) else -1)
    return result


def hop(sites, j, delta, m):
    """Ideal allowed-edge specification; rejected attempts retain state."""
    x, y = sites[j], sites[j] + delta
    if not 0 <= x % m + delta < m or y in sites:
        return sites
    previous, following = links(sites, m)[j]
    if previous != -1 and sites[previous] >= y:
        return sites
    if following != -1 and sites[following] <= y:
        return sites
    moved = list(sites)
    moved[j] = y
    return tuple(moved)


def transfer(sites, old_links, j, destination, m):
    """Small transcription of transactional link edits, checked against sorting.

    This is a mathematical fixture, not an invocation of production transfer().
    """
    assert sites[j] % m in (0, m - 1)
    assert destination % m in (0, m - 1)
    if destination in sites:  # source is occupied until this check
        return sites, old_links.copy()
    left = destination % m == 0
    others = sorted((i for i, s in enumerate(sites)
                     if i != j and s // m == destination // m),
                    key=lambda i: sites[i])
    neighbor = (others[0] if left else others[-1]) if others else -1
    updated = {i: list(pair) for i, pair in old_links.items()}
    previous, following = old_links[j]
    if previous != -1:
        updated[previous][1] = following
    if following != -1:
        updated[following][0] = previous
    updated[j] = [-1, neighbor] if left else [neighbor, -1]
    if neighbor != -1:
        updated[neighbor][0 if left else 1] = j
    moved = list(sites)
    moved[j] = destination
    return tuple(moved), {i: tuple(pair) for i, pair in updated.items()}


class D16DMathematicalSpecifications(unittest.TestCase):
    def test_spring_force_is_negative_exact_energy_derivative(self):
        r, anchor, k = (Q(2), Q(-1), Q(3)), (Q(-2), Q(1), Q(0)), Q(3, 5)
        # Centered difference is the exact derivative for a quadratic, no limit fit.
        epsilon = Q(1, 7)
        for d in range(3):
            plus, minus = list(r), list(r)
            plus[d] += epsilon
            minus[d] -= epsilon
            gradient = (energy(plus, anchor, k) - energy(minus, anchor, k)) / (2 * epsilon)
            self.assertEqual(-gradient, -k * (r[d] - anchor[d]))

    def test_metropolis_rate_ratio_and_energy_precision_formula(self):
        k, thermal, nu = Q(3, 5), Q(1), Q(100)
        anchor = (Q(1), Q(-2), Q(0))
        x, y = (Q(0), Q(1), Q(2)), (Q(3), Q(-1), Q(1))
        delta = (energy(y, anchor, k) - energy(x, anchor, k)) / thermal
        difference_of_squares = k / (2 * thermal) * sum(
            (v - u) * ((v - a) + (u - a)) for u, v, a in zip(x, y, anchor))
        self.assertEqual(delta, difference_of_squares)
        for change in (float(delta), -float(delta), 0.0):
            forward = float(nu / 2) * exp(min(0.0, -change))
            reverse = float(nu / 2) * exp(min(0.0, change))
            self.assertAlmostEqual(log(forward / reverse), -change, places=12)
        # Rounding/finite-bit acceptance symmetry is deliberately not asserted.

    def test_interior_exclusion_boundary_and_order_reciprocity(self):
        m = 4
        for occupied in combinations(range(m), 2):
            for sites in permutations(occupied):
                for j in range(2):
                    for delta in (-1, 1):
                        moved = hop(sites, j, delta, m)
                        if moved != sites:
                            self.assertEqual(hop(moved, j, -delta, m), sites)
                            self.assertEqual(links(moved, m), links(sites, m))
        self.assertEqual(hop((0, 1), 0, 1, m), (0, 1))
        self.assertEqual(hop((0, 2), 0, -1, m), (0, 2))

    def test_renewal_density_reciprocity_includes_gaussian(self):
        k, thermal, nu, chains = Q(3, 5), Q(1), Q(100), 2
        r_x, r_y = (Q(0), Q(0), Q(0)), (Q(3), Q(1), Q(-2))
        old, new = (Q(1), Q(2), Q(0)), (Q(5), Q(-1), Q(3))
        gx = log_gaussian(r_x, old, k, thermal)
        gy = log_gaussian(r_y, new, k, thermal)
        log_channel = log(float(nu / (4 * chains)))
        self.assertAlmostEqual(gx + log_channel + gy, gy + log_channel + gx)
        # MH target ratio (gy-gx) cancels reverse/forward proposal ratio.
        self.assertAlmostEqual((gy - gx) + (gx - gy), 0.0)
        # An extra ordinary energy acceptance factor would spoil this fixture.
        delta = float((energy(r_y, new, k) - energy(r_x, old, k)) / thermal)
        self.assertNotAlmostEqual(gx + gy + min(0, -delta),
                                  gy + gx + min(0, delta))

    def test_terminal_transfers_and_same_chain_inverse_links(self):
        m, chains = 4, 2
        # Singleton, two/multiple on same chain, occupied ends, cross-chain.
        for sites in ((0,), (3,), (0, 1), (0, 1, 2), (0, 3), (0, 5, 6)):
            before = links(sites, m)
            for j, source in enumerate(sites):
                if source % m not in (0, m - 1):
                    continue
                for dest in (c * m + b for c in range(chains) for b in (0, m - 1)):
                    moved, after = transfer(sites, before, j, dest, m)
                    self.assertEqual(after, links(moved, m))
                    if moved == sites:
                        self.assertIn(dest, sites)
                        self.assertEqual(after, before)
                    else:
                        restored, restored_links = transfer(moved, after, j, source, m)
                        self.assertEqual((restored, restored_links), (sites, before))

    def test_canonical_occupancy_and_constant_label_factor(self):
        m, chains, z = 3, 2, 2
        length = m * chains
        states = list(combinations(range(length), z))
        probability = Q(1, comb(length, z))
        self.assertEqual(sum(probability for _ in states), 1)
        for site in range(length):
            self.assertEqual(sum(probability for s in states if site in s), Q(z, length))
        for count in range(z + 1):
            mass = sum(probability for s in states if sum(x < m for x in s) == count)
            self.assertEqual(mass, Q(comb(m, count) * comb(length - m, z - count),
                                     comb(length, z)))
        labelled = [p for s in states for p in permutations(s)]
        self.assertEqual(len(labelled), length * (length - 1))
        self.assertEqual(Q(len(labelled), len(states)), 2)  # Z!, no Z_c! weights

    def test_anchor_normalization_and_gaussian_moments_analytically(self):
        # Gaussian integral theorem: integral exp(-x²/(2v)) dx = sqrt(2*pi*v).
        # Check the specified 3D density against a product of 1D analytic integrals.
        for thermal, k in ((Q(1), Q(3, 5)), (Q(7, 3), Q(2))):
            prefactor = (float(k / thermal) / (2 * pi)) ** 1.5
            one_dimensional_integral = sqrt(2 * pi * float(thermal / k))
            self.assertAlmostEqual(prefactor * one_dimensional_integral ** 3, 1.0)
        # Integration-by-parts recursion m_(2n)=(2n-1)*v*m_(2n-2).
        v = Q(5, 3)
        m2, m4 = v, 3 * v * v
        self.assertEqual(3 * m2, 5)
        self.assertEqual(3 * m4 + 6 * m2 * m2, Q(125, 3))
        # Each normalized anchor integrates to 1, irrespective of R or S.
        self.assertEqual(Q(1) ** 2 / comb(6, 2) * comb(6, 2), 1)

    def test_exact_quadratic_em_drift_and_equilibrium_cancellation(self):
        dimension, thermal, mu, k, h = 3, Q(1), Q(2), Q(3, 5), Q(1, 10)
        diffusion, rate, v = mu * thermal, mu * k, thermal / k
        old = dimension * v
        updated = (1 - rate * h) ** 2 * old + 2 * dimension * diffusion * h
        first_order = -2 * rate * old + 2 * dimension * diffusion
        self.assertEqual(first_order, 0)
        self.assertEqual(updated - old, dimension * rate ** 2 * h ** 2 * v)

    def test_harmonic_toy_transient_and_stationary_bias_are_distinct(self):
        # TOY ONLY: fixed harmonic anchor, no backbone, hopping or renewal.
        dimension, rate, diffusion, h = 3, Q(2), Q(1), Q(1, 10)
        v = diffusion / rate
        stationary = v / (1 - rate * h / 2)
        contraction = (1 - rate * h) ** 2
        self.assertTrue(0 < rate * h < 2)
        self.assertEqual(stationary, contraction * stationary + 2 * diffusion * h)
        initial, moment = dimension * v, dimension * v
        for n in range(1, 5):  # exact moment recurrence, not a trajectory
            moment = contraction * moment + 2 * dimension * diffusion * h
            closed = dimension * stationary + contraction ** n * (initial - dimension * stationary)
            self.assertEqual(moment, closed)
        one_step = dimension * rate ** 2 * h ** 2 * v
        asymptotic = dimension * (stationary - v)
        self.assertNotEqual(one_step, asymptotic)
        self.assertEqual(asymptotic / h, dimension * v * rate / (2 - rate * h))
        # Sum propagated defects, rather than multiplying the first defect by n.
        self.assertEqual(moment - initial, sum(one_step * contraction ** j for j in range(4)))


if __name__ == '__main__':
    unittest.main()
