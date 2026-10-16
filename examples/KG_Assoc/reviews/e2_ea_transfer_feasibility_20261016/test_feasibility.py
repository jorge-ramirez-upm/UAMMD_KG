"""Deterministic CPU checks of frozen host kinetics and the feasibility claims."""
import itertools
import math
from pathlib import Path
import subprocess
import tempfile
import unittest

import reproduce as review


def hashed(seed, step, first, second, stream):
    mask = 2**64 - 1
    value = (seed ^ step ^ (first << 1) ^ (second << 17) ^ stream) + 0x9e3779b97f4a7c15
    value &= mask
    value = ((value ^ (value >> 30)) * 0xbf58476d1ce4e5b9) & mask
    value = ((value ^ (value >> 27)) * 0x94d049bb133111eb) & mask
    return value ^ (value >> 31)


class FeasibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        exe = Path(cls.temp.name) / 'host_check'
        subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-I', str(review.REPO),
                        str(review.HERE / 'kinetics_host_check.cpp'), '-o', str(exe)], check=True)
        cls.output = subprocess.check_output([str(exe)], text=True).splitlines()
        cls.probabilities = [list(map(float, line.split()[1:]))
                             for line in cls.output if line.startswith('P ')]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_header_probabilities_and_pair_ratio(self):
        self.assertEqual(len(self.probabilities), 36)
        for ea, temperature, _, du, q, formation, breaking in self.probabilities:
            self.assertAlmostEqual(q, review.attempt(ea, temperature), places=15)
            self.assertAlmostEqual(formation / breaking, math.exp(-du / temperature), places=10)
            self.assertAlmostEqual(formation, q * min(1, math.exp(-du / temperature)), places=15)
            self.assertAlmostEqual(breaking, q * min(1, math.exp(du / temperature)), places=15)

    def test_actual_sequential_sweep_order_hash_and_availability(self):
        energies = {round(row[2], 2): row[3] for row in self.probabilities}
        edges = [(0, 1, .93), (1, 2, 1.02), (2, 3, 1.20)]
        count = 0
        for line in self.output:
            if not line.startswith('S '):
                continue
            ea, seed, initial, final = map(int, line.split()[1:])
            active = {i for i in range(3) if initial & (1 << i)}
            order = sorted(range(3), key=lambda i: (
                hashed(seed, 100, *edges[i][:2], 0x4f52444552), *edges[i][:2]))
            for i in order:
                a, b, r = edges[i]
                occupied = {v for j in active for v in edges[j][:2]}
                creation = i not in active
                if creation and occupied & {a, b}:
                    continue
                p = review.attempt(ea) * min(1, math.exp((-1 if creation else 1) * energies[r]))
                u = (hashed(seed, 100, a, b, 0x414343455054) >> 11) * 2**-53
                if u < p:
                    active ^= {i}
            self.assertEqual(sum(1 << i for i in active), final)
            count += 1
        self.assertEqual(count, 340)

    def test_matching_gibbs_invariance_with_competing_reactions(self):
        for ea in (4, 6, 8, 10):
            for order in itertools.permutations(range(3)):
                states, target, matrix = review.matching_kernel(review.attempt(ea), order=order)
                for j in range(len(states)):
                    self.assertAlmostEqual(sum(target[i] * matrix[i][j]
                                               for i in range(len(states))), target[j], places=14)
                for row in matrix:
                    self.assertAlmostEqual(sum(row), 1, places=14)

    def test_invariance_does_not_require_sweep_reversibility(self):
        states, target, matrix = review.matching_kernel(review.attempt(4))
        residual = max(abs(target[i] * matrix[i][j] - target[j] * matrix[j][i])
                       for i in range(len(states)) for j in range(len(states)))
        self.assertGreater(residual, 1e-5)

    def test_full_sweep_is_not_a_uniform_clock_rescaling(self):
        states, _, a = review.matching_kernel(review.attempt(4))
        _, _, b = review.matching_kernel(review.attempt(8))
        empty, both = states.index(frozenset()), states.index(frozenset((0, 2)))
        ratio = review.attempt(8) / review.attempt(4)
        self.assertAlmostEqual(b[empty][both] / a[empty][both], ratio**2, places=14)
        self.assertGreater(abs(b[empty][both] / a[empty][both] - ratio), .01)
        self.assertGreater(abs(ratio / math.exp(-4) - 1), .1)

    def test_existing_restart_ea_guards(self):
        self.assertIn('RESTART_GUARDS_PASS', self.output)

    def test_fresh_chemical_seed_rejected_by_current_parent_reader(self):
        history = review.e2.campaign.load_json(review.RECORD)['histories'][0]
        system = review.e2.system_by_id('F04_N010_RP080_EE08_EA08')
        entry = dict(parent=dict(kind='e2', prefix=history['prefix'],
                                snapshot=history['prefix'] + '.restart.lammpsdat'),
                     system=system, physics=review.e2.validation.physics(system, 8),
                     parent_Ea=4, start_step=8000000, chemistry_seed=620801)
        with self.assertRaisesRegex(ValueError, 'parent step/chemistry seed mismatch'):
            review.e2.validation.read_parent(entry)
        entry['chemistry_seed'] = history['chemistry_seed']
        _, initial = review.e2.validation.read_parent(entry)
        self.assertGreater(len(initial['pairs']), 1700)

    def test_current_planner_refuses_higher_ea_ordinary_preparation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'banks/e2_attempts/F04_N010_RP080_EE08/new'
            with self.assertRaisesRegex(ValueError, 'fresh preparation requires Ea=4'):
                review.e2.prepare(root, output, 'F04_N010_RP080_EE08_EA08', 10000,
                                  review.HERE / 'ASSESSMENT.md', ea=8)
            self.assertFalse(output.exists())

    def test_reference_acceptance_does_not_permit_higher_ea(self):
        record = review.e2.campaign.load_json(review.RECORD)
        for ea in (6, 8, 10):
            with self.assertRaises(ValueError):
                review.registry.permitted(record, review.e2.system_by_id(
                    f'F04_N010_RP080_EE08_EA{ea:02d}'))

    def test_illustrative_seed_triplets_have_no_known_plan_collisions(self):
        chemical = [base + replica for base in (620600, 620800, 621000)
                    for replica in (1, 2, 3)]
        md = [base + replica for base in (630600, 630800, 631000)
              for replica in (1, 2, 3)]
        known = {22001, 22002, 22003, 32001, 32002, 32003}
        policy = review.e2.campaign.load_json(review.e2.HERE / 'e2_seed_map.json')
        known.update(policy['reserved_md_system_seeds'])
        for values in policy['chemical_seeds'].values():
            known.update(values)
        existing_effective = {review.e2.validation.effective_md_seed(seed) for seed in known}
        for path in (review.ROOT / 'banks').rglob('plan.json'):
            plan = review.e2.campaign.load_json(path)
            for history in plan.get('histories', []):
                known.update(history[key] for key in ('chemistry_seed', 'md_seed') if key in history)
                if 'effective_md_seed' in history:
                    existing_effective.add(history['effective_md_seed'])
        proposed = {review.e2.validation.effective_md_seed(seed) for seed in md}
        self.assertEqual(len(set(chemical + md)), 18)
        self.assertFalse(set(chemical + md) & known)
        self.assertEqual(len(proposed), 9)
        self.assertFalse(proposed & existing_effective)

    def test_preserved_sources_and_twelve_immutable_acceptances(self):
        self.assertEqual(len(review.verify_inputs()), 12)


if __name__ == '__main__':
    unittest.main()
