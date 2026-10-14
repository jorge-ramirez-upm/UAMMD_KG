"""CPU guards for this dossier's fixed scope and read-only reproduction."""
import copy
import csv
import json
import math
from pathlib import Path
import sys
import statistics
import tempfile
import unittest
from unittest import mock

import reproduce as review
import multiplicity


class ReviewGuards(unittest.TestCase):
    def test_parallel_bonds_and_intra_loops_keep_permanent_star_ids(self):
        system = dict(stars=list(range(1, 6)), stickers=set(range(1, 21)))
        pairs = [(1, 5, 1, 2), (2, 6, 1, 2), (9, 13, 3, 4),
                 (10, 14, 3, 4), (11, 15, 3, 4), (17, 18, 5, 5), (19, 20, 5, 5)]
        graph = multiplicity.analysis.topology.frame_observables(0, 0, 0, pairs, system)
        original = copy.deepcopy(graph)
        result = multiplicity.distributions(graph, 5, 4)
        self.assertEqual(graph, original)
        self.assertEqual([result[f'edges_m{k}'] for k in range(1, 5)], [0, 1, 1, 0])
        self.assertEqual(result['stars_intra_loops_2'], 1)
        self.assertEqual(result['stars_intra_loops_0'], 4)
        self.assertEqual(result['mean_edge_multiplicity'], 2.5)
        self.assertEqual(result['max_edge_multiplicity'], 3)

    def test_four_parallel_bonds_and_invalid_valence(self):
        system = dict(stars=[1, 2], stickers=set(range(1, 9)))
        pairs = [(i, i + 4, 1, 2) for i in range(1, 5)]
        graph = multiplicity.analysis.topology.frame_observables(0, 0, 0, pairs, system)
        self.assertEqual(multiplicity.distributions(graph, 2, 4)['edges_m4'], 1)
        graph['edge_multiplicity'][(1, 2)] = 5
        with self.assertRaisesRegex(ValueError, 'valence'):
            multiplicity.distributions(graph, 2, 4)

    def test_exported_histories_and_window_means_preserve_graph_identities(self):
        directory = Path(review.__file__).parent / 'evidence'
        summary = json.loads((directory / 'summary.json').read_text())
        self.assertEqual(summary['windows_steps'], 500000)
        self.assertEqual([h['replica'] for h in summary['records']], [1, 2, 3])
        for record in summary['records']:
            with (directory / ('r%03d_frames.csv' % record['replica'])).open() as stream:
                rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(stream)]
            self.assertEqual([int(r['step']) for r in rows], list(range(0, 6000001, 1000)))
            self.assertEqual(rows[0]['bonds'], 0)
            for row in rows[1:]:
                self.assertEqual(row['bonds'], row['intra'] + row['inter'])
                self.assertAlmostEqual(sum(row[f'degree_{k}_fraction'] for k in range(5)), 1)
                self.assertAlmostEqual(sum(k * row[f'degree_{k}_fraction'] for k in range(5)),
                                       row['mean_degree'])
                self.assertAlmostEqual(sum(k * k * row[f'degree_{k}_fraction'] for k in range(5)),
                                       row['second_degree_moment'])
                self.assertAlmostEqual(row['components'],
                    1 + row['isolated_stars'] + row['satellite_components'])
                self.assertAlmostEqual(1000 * (1 - row['largest_cluster_fraction']),
                    row['isolated_stars'] + row['satellite_stars'])
            for window in record['windows']:
                selected = [r for r in rows if window['start_step_exclusive'] < r['step'] <=
                            window['end_step_inclusive']]
                self.assertEqual(len(selected), 500)
                for name, value in window['metrics'].items():
                    self.assertEqual(statistics.mean(r[name] for r in selected), value['mean'])

    def test_cached_mean_executes_identical_iat_arithmetic(self):
        cases = ([3] * 30, list(range(40)), [(-1) ** i for i in range(30)],
                 [math.sin(i / 3) + i / 100 for i in range(50)], [])
        for values in cases:
            times = [10 * i for i in range(len(values))]
            expected = review.BASE_IAT(values, times)
            actual = review.memoized_iat(values, times)
            for a, b in zip(actual, expected):
                self.assertTrue((math.isnan(a) and math.isnan(b)) or a == b)
        times = [0, 1, 3]
        self.assertTrue(all(math.isnan(v) for v in review.memoized_iat([1, 2, 3], times)))

    def test_iat_is_restored_after_success_or_failure(self):
        stationarity = review.joint.segment.review.analysis.stationarity
        original = stationarity.iat
        with mock.patch.object(review.graph, 'make_window', return_value={'checked': True}):
            self.assertEqual(review.fresh_window(None, None, 0, 1000), {'checked': True})
        self.assertIs(stationarity.iat, original)
        with mock.patch.object(review.graph, 'make_window', side_effect=ValueError('failure')):
            with self.assertRaisesRegex(ValueError, 'failure'):
                review.fresh_window(None, None, 0, 1000)
        self.assertIs(stationarity.iat, original)

    def test_wrong_endpoint_or_system_creates_no_output(self):
        source = dict(plan=dict(smoke=False, system=dict(system_id='F04_N010_RP040_EE08_EA04')),
                      histories=[dict(entry=dict(replica=r, start_step=0, end_step=6000000))
                                 for r in (1, 2, 3)])
        for end, system in ((4000000, 'F04_N010_RP040_EE08_EA04'),
                            (6000000, 'F04_N010_RP080_EE08_EA04')):
            candidate = copy.deepcopy(source)
            candidate['plan']['system']['system_id'] = system
            candidate['histories'][0]['entry']['end_step'] = end
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / 'new'
                with self.assertRaisesRegex(ValueError, 'exact RP040'):
                    review.write_evidence(candidate, output)
                self.assertFalse(output.exists())

    def test_existing_output_and_wrong_plan_never_authenticate(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'old'
            output.write_text('immutable')
            with mock.patch.object(review.graph, 'authenticate_with_graphs') as auth:
                with mock.patch.object(sys, 'argv', ['review', '--output', str(output)]):
                    with self.assertRaisesRegex(ValueError, 'immutable'):
                        review.main()
                output = Path(temp) / 'new'
                with mock.patch.object(sys, 'argv', ['review', '--output', str(output)]), \
                     mock.patch.object(review.joint.campaign, 'sha256', return_value='wrong'):
                    with self.assertRaisesRegex(ValueError, 'plan hash'):
                        review.main()
                auth.assert_not_called()
                self.assertFalse(output.exists())

    def test_paired_windows_keep_transient_as_context(self):
        for early, late in review.PAIRS:
            for start, end in (early, late):
                self.assertGreaterEqual(start, 1000000)
                self.assertLessEqual(end, 6000000)
                self.assertEqual(start % 500000, 0)
                self.assertEqual(end % 500000, 0)
        self.assertIn(((5000000, 5500000), (5500000, 6000000)), review.PAIRS)
        self.assertTrue(any(a[1] > b[0] for a, b in review.PAIRS))


if __name__ == '__main__':
    unittest.main()
