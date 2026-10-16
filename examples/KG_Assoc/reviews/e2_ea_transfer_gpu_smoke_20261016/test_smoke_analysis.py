"""Deterministic CPU tests of event exposure integration and topology summaries."""
import math
import unittest
from reproduce import exposures, graph_summary, poisson_interval


class SmokeAnalysisTests(unittest.TestCase):
    def test_zero_event_exposure(self):
        result = exposures([], 1783, 8000000, 8010000)
        self.assertEqual(result['active_bond_time'], 178300)
        self.assertEqual(result['free_sticker_time'], 43400)
        self.assertEqual(result['final_bonds'], 1783)

    def test_ordered_same_step_events_and_end_boundary(self):
        # B=2 for 3 units, B=1 for 4 units, B=2 for 3 units.
        events = [(3, 'B', (1, 2)), (7, 'C', (1, 3)),
                  (7, 'C', (2, 4)), (7, 'B', (1, 3)), (10, 'B', (2, 4))]
        result = exposures(events, 2, 0, 10, dt=1, stickers=10)
        self.assertEqual(result['active_bond_time'], 16)
        self.assertEqual(result['free_sticker_time'], 68)
        self.assertEqual(result['final_bonds'], 1)

    def test_bad_event_chronology_or_population_rejected(self):
        for events, initial in [([(0, 'C', (1, 2))], 0),
                                ([(11, 'C', (1, 2))], 0),
                                ([(1, 'B', (1, 2))], 0),
                                ([(1, 'X', (1, 2))], 0),
                                ([(5, 'C', (1, 2)), (4, 'B', (1, 2))], 0)]:
            with self.assertRaises(AssertionError):
                exposures(events, initial, 0, 10, stickers=4)

    def test_full_multiplicity_degree_loop_distributions(self):
        system = dict(stars=[1, 2, 3, 4], stickers=set(range(1, 17)),
                      atom_to_star={i: (i-1)//4+1 for i in range(1, 17)})
        graph = graph_summary([(1, 5), (2, 6), (7, 9), (3, 10), (13, 14)], system)
        self.assertEqual(graph['multiplicity'], {'0': 3, '1': 2, '2': 1, '3': 0, '4': 0})
        self.assertEqual(graph['distinct_degree'], {0: 1, 2: 3})
        self.assertEqual(graph['intra_loops'], {0: 3, 1: 1})
        self.assertEqual(graph['isolated_stars'], [4])
        self.assertEqual(graph['component_sizes'], [3, 1])

    def test_sparse_count_interval_is_not_zero_width(self):
        interval = poisson_interval(0, 100)
        self.assertEqual(interval[0], 0)
        self.assertAlmostEqual(interval[1], -math.log(.025)/100)


if __name__ == '__main__':
    unittest.main()
