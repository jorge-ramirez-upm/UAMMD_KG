"""Deterministic window/pairing fixtures, no stochastic convergence claims or GPU."""
import copy
import unittest
import analyze_e2_window_sensitivity as sensitivity


class SensitivityTests(unittest.TestCase):
    def setUp(self):
        self.summary = dict(windows_steps=10, records=[dict(replica=r, windows=[dict(
            start_step_exclusive=i*10, end_step_inclusive=(i+1)*10, segment='continuous',
            metrics={'L2': dict(mean=i*r)}, activity={'creations': dict(mean=1)})
            for i in range(6)]) for r in (1, 2, 3)])

    def test_pairing_and_overlap_remain_three_units_and_leave_inputs_unchanged(self):
        original = copy.deepcopy(self.summary)
        result = sensitivity.summarize(self.summary, [((20, 40), (40, 60)), ((30, 50), (40, 60))])
        self.assertEqual(self.summary, original)
        self.assertFalse(result['automatic_acceptance'])
        c = result['comparisons'][0]
        self.assertEqual(c['per_replica_changes'], [2, 4, 6])
        self.assertEqual(c['replicas'], 3)
        self.assertEqual(result['comparisons'][2]['overlapping_steps'], 10)

    def test_gaps_boundary_crossing_partial_windows_transient_and_replica_mismatch_fail(self):
        for change in ('gap', 'boundary', 'replica'):
            summary = copy.deepcopy(self.summary)
            if change == 'gap':
                summary['records'][0]['windows'].pop(2)
            elif change == 'boundary':
                summary['records'][0]['windows'][3]['segment'] = 'restart'
            else:
                summary['records'][2]['replica'] = 2
            with self.subTest(change=change), self.assertRaises(ValueError):
                sensitivity.summarize(summary, [((20, 40), (40, 60))])
        for pair in (((0, 20), (40, 60)), ((15, 35), (40, 60))):
            with self.assertRaises(ValueError):
                sensitivity.summarize(self.summary, [pair])

    def test_duration_weighted_mean_does_not_average_sem_or_iat(self):
        record = dict(windows=[dict(start_step_exclusive=0, end_step_inclusive=10,
            segment='one', metrics={'L2': dict(mean=2)}),
            dict(start_step_exclusive=10, end_step_inclusive=30,
            segment='one', metrics={'L2': dict(mean=5)})])
        self.assertEqual(sensitivity.mean(record, 'metrics', 'L2', 0, 30), 4)


    def test_degree_histograms_reuse_graph_replay_and_keep_rows_unchanged(self):
        from pathlib import Path
        import tempfile
        from test_e2_g1 import fixture
        import kg_assoc_e2 as e2
        with tempfile.TemporaryDirectory() as temp:
            entry = fixture(Path(temp), f=3)
            rows, _, _ = e2.validation.validate(entry)
            original = copy.deepcopy(rows)
            analysis = sensitivity.joint.segment.review.analysis
            graph_function = analysis.topology.frame_observables
            system = analysis.topology.read_system(entry['output_prefix'] + '.restart.lammpsdat', 2)
            _, events = analysis.dynamics.read_events(entry['output_prefix'] + '.events', system)
            frames = sensitivity.degree_histograms(rows, events, system)
            self.assertEqual(rows, original)
            self.assertIs(analysis.topology.frame_observables, graph_function)
            self.assertEqual(frames[0]['counts'], {0: 16})
            self.assertEqual(frames[-1]['counts'], {0: 14, 1: 2})
            rows[0]['bonds'] = 1
            with self.assertRaises(ValueError):
                sensitivity.degree_histograms(rows, events, system)


if __name__ == '__main__':
    unittest.main()
